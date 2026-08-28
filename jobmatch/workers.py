"""Off-GUI-thread workers wrapping the real backend services.

Same Qt signal contract the screens already listen to — only the bodies changed
from timed stubs to real work:

* :class:`ParseWorker` runs the local résumé parser (:mod:`services.resume_parser`)
  and emits staged progress as it extracts text, finds sections and skills.
* :class:`SearchWorker` runs the live job search (:mod:`services.job_search`),
  falling back to cached sample jobs (scored against the profile) when offline —
  it reports which happened via ``finished(jobs, offline)``.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from .models import Profile
from .services import job_search
from .services.job_search import Offline
from .services.resume_parser import ParseError, parse_resume


class ParseSignals(QObject):
    progress = pyqtSignal(int, str)     # pct, step
    finished = pyqtSignal(object)       # Profile
    failed = pyqtSignal(str)


class ParseWorker(QRunnable):
    def __init__(self, path) -> None:
        super().__init__()
        self.path = path
        self.signals = ParseSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        def progress(pct: int, msg: str) -> None:
            if not self._cancelled:
                self.signals.progress.emit(pct, msg)
        try:
            profile: Profile = parse_resume(self.path, progress)
        except ParseError as e:
            if not self._cancelled:
                self.signals.failed.emit(str(e))
            return
        except Exception as e:  # pragma: no cover - unexpected
            if not self._cancelled:
                self.signals.failed.emit("We couldn't read that file.")
            return
        if not self._cancelled:
            self.signals.finished.emit(profile)


class SearchSignals(QObject):
    finished = pyqtSignal(object, bool, object)   # list[Job], offline, source_info
    failed = pyqtSignal(str)


class SearchWorker(QRunnable):
    def __init__(self, profile: Profile, keywords: list[str] | None = None,
                 location: str = "") -> None:
        super().__init__()
        self.profile = profile
        self.keywords = keywords
        self.location = location
        self.signals = SearchSignals()

    def run(self) -> None:
        try:
            jobs, ok, failed = job_search.search(
                self.profile, self.keywords, self.location)
            info = {"ok": ok, "failed": failed}
            if not jobs:
                self.signals.finished.emit(self._cached(), True, info)
            else:
                self.signals.finished.emit(jobs, False, info)
        except Offline:
            self.signals.finished.emit(self._cached(), True, {"ok": [], "failed": []})

    def _cached(self) -> list:
        """Sample jobs, re-scored against the live profile, as an offline cache."""
        return _rescore_sample(self.profile)


class ExplainSignals(QObject):
    finished = pyqtSignal(str, str)   # explanation, provider ('local' if offline)


class ExplainWorker(QRunnable):
    """Fetch a 'why this score' explanation off the GUI thread."""

    def __init__(self, profile, job) -> None:
        super().__init__()
        self.profile = profile
        self.job = job
        self.signals = ExplainSignals()

    def run(self) -> None:
        from .services import ai
        provider = ai.active_provider()
        try:
            text = ai.explain_match(self.profile, self.job)
        except Exception:
            text, provider = ai.explain_local(self.profile, self.job), "local"
        self.signals.finished.emit(text, provider)


class KeywordsSignals(QObject):
    finished = pyqtSignal(object, str)   # list[str], provider ('local' if none)


class KeywordsWorker(QRunnable):
    """AI-assisted (or heuristic) search-keyword research off the GUI thread."""

    def __init__(self, profile) -> None:
        super().__init__()
        self.profile = profile
        self.signals = KeywordsSignals()

    def run(self) -> None:
        from .services import ai
        provider = ai.active_provider()
        try:
            kws = ai.suggest_keywords(self.profile)
        except Exception:
            from .services.job_search import build_keywords
            kws, provider = build_keywords(self.profile), "local"
        self.signals.finished.emit(kws, provider)


def _rescore_sample(profile):
    from .sample_data import sample_jobs
    from .services import scoring
    jobs = sample_jobs()
    for j in jobs:
        text = f"{j.description} {j.benefits} {' '.join(j.matched_skills)}"
        j.score, j.factors, matched = scoring.score_job(
            profile, title=j.title, text=text, tags=j.matched_skills)
        if matched:
            j.matched_skills = matched
            j.extra_skill_count = max(0, len(matched) - 3)
    jobs.sort(key=lambda j: -j.score)
    return jobs
