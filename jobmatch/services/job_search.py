"""Job search orchestrator — aggregates many sources, scores against the profile.

Sources live in :mod:`jobmatch.services.sources` (Remotive, Arbeitnow, Jobicy,
RemoteOK, and — with a key — Adzuna). This module builds search keywords from
the résumé, runs the aggregator, and turns each normalized ``RawJob`` into a
scored :class:`Job`.
"""
from __future__ import annotations

import hashlib
import re

from ..models import Apply, Job
from . import config, scoring
from .sources import aggregate
from .sources.base import shorten
from .vocab import SKILLS


class Offline(Exception):
    """Raised only when every source failed to respond."""


# ------------------------------------------------------------- keywords
def build_keywords(profile) -> list[str]:
    """Keep job titles as whole phrases (not split into words) + top skills."""
    kws: list[str] = []
    for title in (profile.target_title, profile.current_title):
        t = _clean_title(title)
        if t and t not in kws:
            kws.append(t)
    for s in profile.skills[:3]:
        if s.name not in kws:
            kws.append(s.name)
    return kws[:5]


def _clean_title(title: str) -> str:
    """Normalise a title phrase: drop seniority words, trim punctuation."""
    t = re.sub(r"\b(senior|junior|lead|principal|staff|sr\.?|jr\.?)\b", "",
               title or "", flags=re.I)
    t = re.sub(r"[^A-Za-z0-9+#./ -]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ------------------------------------------------------------- search
def search(profile, keywords: list[str] | None = None, location: str = "",
           limit_per_source: int = 25):
    """Return (jobs, ok_sources, failed_sources), scored + sorted by match.

    Smart path (with an AI key): expands the search into several adjacent role
    titles, aggregates them in parallel, then re-ranks every result by semantic
    similarity to the résumé (Gemini embeddings). Without a key it's a single
    keyword aggregate scored by the rule engine — same as before.
    """
    from . import ai
    query_sets = _query_sets(profile, keywords, ai)
    raws, ok, failed = _run_queries(query_sets, location, limit_per_source)
    if not raws and failed and not ok:
        raise Offline("all sources failed")
    jobs = [_raw_to_job(profile, r) for r in raws]
    jobs = _semantic_rerank(profile, jobs, ai)
    jobs.sort(key=lambda j: -j.score)
    return jobs, ok, failed


def _query_sets(profile, keywords, ai) -> list[list[str]]:
    """The keyword lists to search: the user's/base set + AI role expansions."""
    base = keywords or build_keywords(profile)
    sets: list[list[str]] = [base]
    if ai.available():
        top_skills = [s.name for s in profile.skills[:2]]
        for role in ai.expand_queries(profile):
            cand = [role] + top_skills
            if cand not in sets:
                sets.append(cand)
    return sets[:4]


def _run_queries(query_sets, location, limit_per_source):
    """Run each query's aggregate in parallel, merge + de-duplicate."""
    import concurrent.futures as cf
    ok: set[str] = set()
    failed: set[str] = set()
    raws: list = []
    seen: set[tuple[str, str]] = set()

    def one(kws):
        return aggregate(kws, location, limit_per_source, config.enabled_sources())

    with cf.ThreadPoolExecutor(max_workers=max(1, len(query_sets))) as ex:
        for r, o, f in ex.map(one, query_sets):
            ok.update(o); failed.update(f)
            for job in r:
                key = (job.title.strip().lower(), job.company.strip().lower())
                if key not in seen:
                    seen.add(key)
                    raws.append(job)
    return raws, sorted(ok), sorted(failed - ok)


def _semantic_rerank(profile, jobs, ai):
    """Blend embedding similarity (résumé vs job) into the match score."""
    if not ai.embeddings_available() or not jobs:
        return jobs
    jobs = jobs[:60]   # keep the embedding payload reasonable
    resume_text = (
        f"{profile.current_title}. {profile.summary} "
        f"Skills: {', '.join(s.name for s in profile.skills)}. "
        f"{profile.raw_text}")[:2000]
    vecs = ai.embed([resume_text] + [f"{j.title}. {j.description}" for j in jobs])
    if not vecs or len(vecs) != len(jobs) + 1:
        return jobs
    rv = vecs[0]
    for j, v in zip(jobs, vecs[1:]):
        sem = int(max(0.0, min(1.0, ai.cosine(rv, v))) * 100)
        j.score = max(0, min(100, round(0.55 * j.score + 0.45 * sem)))
    return jobs


def search_jobs(profile, keywords=None, location="", limit=25) -> list[Job]:
    jobs, _ok, _failed = search(profile, keywords, location, limit)
    return jobs


# ------------------------------------------------------------- mapping
def _raw_to_job(profile, r) -> Job:
    score, factors, matched = scoring.score_job(
        profile, title=r.title, text=r.description, tags=r.tags)
    jid = "j" + hashlib.md5(f"{r.source}|{r.url}|{r.title}".encode()).hexdigest()[:12]
    return Job(
        id=jid,
        title=r.title, company=r.company, location=r.location,
        mode=r.mode, type=r.type,
        salary_min=r.salary_min, salary_max=r.salary_max,
        score=score, factors=factors,
        posted=r.posted, posted_days=r.posted_days,
        apply=Apply(r.apply_type, r.apply_value or r.url),
        description=r.description,
        requirements=_requirements(profile, r.tags),
        benefits=_benefits(r.description),
        matched_skills=matched,
        extra_skill_count=max(0, len(matched) - 3),
        source=r.source,
        currency=getattr(r, "currency", "USD"),
    )


def _requirements(profile, tags) -> list[tuple[bool, str]]:
    have = {s.name.lower() for s in profile.skills}
    seen: set[str] = set()
    rows: list[tuple[bool, bool, str]] = []
    for tag in tags:
        canon = _canonical(tag)
        key = canon.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append((key in have, canon in SKILLS, canon))
    rows.sort(key=lambda r: (not r[0], not r[1]))
    return [(met, name) for met, _known, name in rows[:6]]


def _canonical(tag: str) -> str:
    t = tag.strip().lower()
    for name, aliases in SKILLS.items():
        if t == name.lower() or t in aliases:
            return name
    return tag.strip().title()


def _benefits(text: str) -> str:
    m = re.search(r"(?i)(benefits|what we offer|perks)[:\s](.{0,240})", text or "")
    if m:
        return shorten(m.group(2), 220)
    return "See the original listing for full benefits."
