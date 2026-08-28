"""Multi-source job aggregator.

Each submodule exposes ``fetch(keywords, location, limit) -> list[RawJob]`` for
one job board. :func:`aggregate` runs the enabled sources concurrently, merges
and de-duplicates their results, and hands back normalized :class:`RawJob`s for
the caller to score against a profile.
"""
from __future__ import annotations

import concurrent.futures as _cf

from .base import RawJob, SOURCES, source_names
# import adapters so they register in SOURCES regardless of entry point
from . import (remotive, arbeitnow, jobicy, remoteok, adzuna, jooble,  # noqa: E402,F401
               jsearch)


def aggregate(keywords: list[str], location: str, limit_per_source: int = 25,
              enabled: list[str] | None = None) -> tuple[list[RawJob], list[str], list[str]]:
    """Fetch from every enabled source in parallel.

    Returns ``(jobs, ok_sources, failed_sources)``. Never raises for a single
    source failure — only surfaces which ones worked.
    """
    names = enabled or source_names()
    ok: list[str] = []
    failed: list[str] = []
    collected: list[RawJob] = []

    def run(name: str) -> tuple[str, list[RawJob] | None]:
        try:
            return name, SOURCES[name](keywords, location, limit_per_source)
        except Exception:
            return name, None

    with _cf.ThreadPoolExecutor(max_workers=max(1, len(names))) as ex:
        for name, jobs in ex.map(run, names):
            if jobs is None:
                failed.append(name)
            else:
                ok.append(name)
                collected.extend(jobs)

    return _dedupe(collected), ok, failed


def _dedupe(jobs: list[RawJob]) -> list[RawJob]:
    seen: set[tuple[str, str]] = set()
    out: list[RawJob] = []
    for j in jobs:
        key = (j.title.strip().lower(), j.company.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out
