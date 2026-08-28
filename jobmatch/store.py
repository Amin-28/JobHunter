"""App-level state store — a QObject that broadcasts changes via signals.

Every screen reads from and writes to this single store, and reacts to its
signals, so a save toggled anywhere updates every view and the nav count.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from .models import Job, Profile, SavedJob


class AppStore(QObject):
    # workflow / navigation
    parse_state_changed = pyqtSignal(str)          # idle|parsing|done|error
    parse_progress = pyqtSignal(int, str)          # pct, step text
    profile_changed = pyqtSignal()
    results_changed = pyqtSignal()
    results_state_changed = pyqtSignal(str)        # idle|loading|loaded|error
    selected_job_changed = pyqtSignal(str)         # job id
    saved_changed = pyqtSignal()
    status_changed = pyqtSignal(str)               # status-bar text
    nav_gate_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.resume_file: Optional[Path] = None
        self.parse_state: str = "idle"
        self.profile: Optional[Profile] = None
        self.profile_dirty_fields: set[str] = set()
        self.editing_field: Optional[str] = None

        self.raw_results: list[Job] = []   # unfiltered batch from the source
        self.results: list[Job] = []       # after filters (what the list shows)
        self.results_state: str = "idle"
        self.sort_by: str = "Match score"
        self.query: dict = {
            "keywords": [],
            "location": "",
            "remote_only": False,
            "salary_min": 0,
            "salary_max": 10_000_000,
            "posted_within": "any",
            "job_types": set(),   # empty = no filter
            "levels": set(),      # empty = no filter
        }
        self.selected_job_id: Optional[str] = None
        self.viewed_ids: set[str] = set()
        self.saved: list[SavedJob] = []
        self.last_status: str = "Ready · No resume loaded"
        self._load_persisted()

    def _load_persisted(self) -> None:
        """Restore saved jobs, profile and last query from SQLite."""
        try:
            from .services import store_db
        except Exception:
            return
        saved = store_db.load_saved()
        if saved:
            self.saved = saved
        profile = store_db.load_profile()
        if profile is not None:
            self.profile = profile
            self.parse_state = "done"       # profile restored → downstream unlocked
        q = store_db.load_query()
        if q:
            self.query.update(q)

    def _persist_saved(self) -> None:
        try:
            from .services import store_db
            store_db.save_saved(self.saved)
        except Exception:
            pass

    def _persist_profile(self) -> None:
        try:
            from .services import store_db
            store_db.save_profile(self.profile)
        except Exception:
            pass

    def _persist_query(self) -> None:
        try:
            from .services import store_db
            store_db.save_query(self.query)
        except Exception:
            pass

    # ---- gating -------------------------------------------------------
    @property
    def profile_ready(self) -> bool:
        return self.parse_state == "done" and self.profile is not None

    @property
    def search_ready(self) -> bool:
        return self.profile_ready

    @property
    def saved_ready(self) -> bool:
        return len(self.saved) > 0

    # ---- mutations ----------------------------------------------------
    def set_parse_state(self, state: str) -> None:
        self.parse_state = state
        self.parse_state_changed.emit(state)
        self.nav_gate_changed.emit()

    def set_profile(self, profile: Profile) -> None:
        self.profile = profile
        # seed the location filter from the résumé (drop the "· open to remote" tail)
        loc = (profile.location or "").split(" · ")[0].strip()
        self.query["location"] = loc
        self._persist_profile()
        self.profile_changed.emit()
        self.nav_gate_changed.emit()

    def set_raw_results(self, jobs: list[Job]) -> None:
        self.raw_results = jobs
        self.apply_filters()

    def apply_filters(self) -> None:
        from .services.filtering import filter_jobs
        jobs = filter_jobs(self.raw_results, self.query)
        jobs = self._sorted(jobs)
        self.results = jobs
        self._persist_query()
        self.results_changed.emit()

    def update_query(self, **kw) -> None:
        self.query.update(kw)
        self._persist_query()
        self.apply_filters()

    def _sorted(self, jobs: list[Job]) -> list[Job]:
        key = self.sort_by
        if key == "Date posted":
            return sorted(jobs, key=lambda j: j.posted_days)
        if key == "Salary":
            return sorted(jobs, key=lambda j: -(j.salary_max or 0))
        return sorted(jobs, key=lambda j: -j.score)

    def set_results(self, jobs: list[Job]) -> None:
        self.results = jobs
        self.results_changed.emit()

    def set_results_state(self, state: str) -> None:
        self.results_state = state
        self.results_state_changed.emit(state)

    def select_job(self, job_id: str) -> None:
        self.selected_job_id = job_id
        self.viewed_ids.add(job_id)
        self.selected_job_changed.emit(job_id)

    def job_by_id(self, job_id: str) -> Optional[Job]:
        for j in self.results:
            if j.id == job_id:
                return j
        return None

    def is_saved(self, job_id: str) -> bool:
        return any(s.job.id == job_id for s in self.saved)

    def toggle_saved(self, job: Job) -> None:
        if self.is_saved(job.id):
            self.saved = [s for s in self.saved if s.job.id != job.id]
        else:
            self.saved.insert(0, SavedJob(job, saved_at="just now"))
        self._persist_saved()
        self.saved_changed.emit()
        self.nav_gate_changed.emit()

    def mark_applied(self, job_id: str) -> None:
        for s in self.saved:
            if s.job.id == job_id:
                s.applied_at = "Applied today"
        self._persist_saved()
        self.saved_changed.emit()

    def set_status(self, text: str) -> None:
        self.last_status = text
        self.status_changed.emit(text)
