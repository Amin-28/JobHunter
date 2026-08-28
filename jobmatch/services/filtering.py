"""Client-side result filtering — makes the filter sidebar actually work.

The search fetches a batch of jobs once (by keyword); every other control
(location, remote-only, job type, experience level, salary, date) narrows that
batch here, instantly. The headline is *location eligibility*: remote listings
declare which regions they accept, so a Karachi-based candidate keeps
"Worldwide / APAC / Asia / Anywhere" roles and drops "US-only" ones.
"""
from __future__ import annotations

import re

from ..models import Job
from . import vocab

# country (lowercase) -> coarse region bucket
_COUNTRY_REGION = {
    **{c: "asia" for c in ("pakistan", "india", "bangladesh", "china", "japan",
        "south korea", "singapore", "malaysia", "indonesia", "philippines",
        "vietnam", "thailand", "sri lanka", "nepal")},
    **{c: "africa" for c in ("nigeria", "ghana", "kenya", "south africa",
        "egypt", "morocco", "ethiopia", "tanzania", "uganda")},
    **{c: "north america" for c in ("united states", "usa", "u.s.", "u.s.a.",
        "canada", "mexico")},
    **{c: "europe" for c in ("united kingdom", "uk", "u.k.", "ireland",
        "germany", "france", "spain", "portugal", "italy", "netherlands",
        "belgium", "switzerland", "austria", "sweden", "norway", "denmark",
        "finland", "poland", "ukraine", "romania", "greece", "estonia",
        "lithuania", "latvia", "czechia", "hungary", "bulgaria")},
    **{c: "latam" for c in ("brazil", "argentina", "chile", "colombia", "peru")},
    **{c: "oceania" for c in ("australia", "new zealand")},
    **{c: "middle east" for c in ("united arab emirates", "uae", "saudi arabia",
        "qatar", "israel", "turkey")},
}

_REGION_SYNONYMS = {
    "asia": {"asia", "apac", "asia pacific", "asia-pacific", "south asia", "sea"},
    "africa": {"africa", "emea"},
    "north america": {"north america", "usa", "us", "u.s.", "united states",
                      "canada", "namer", "americas"},
    "europe": {"europe", "emea", "eu", "uk", "united kingdom"},
    "latam": {"latam", "latin america", "south america", "americas"},
    "oceania": {"oceania", "apac", "australia", "anz"},
    "middle east": {"middle east", "emea", "mena", "gcc"},
}

_UNIVERSAL = {"worldwide", "anywhere", "global", "remote", "any", "everywhere",
              "international", "-"}

_LEVELS = {"junior": 1, "mid": 2, "senior": 3, "lead": 4}


def location_keywords(user_location: str) -> set[str]:
    """Region/keywords a candidate in ``user_location`` is eligible for."""
    if not user_location:
        return set()
    low = user_location.lower()
    kws: set[str] = set(_UNIVERSAL)
    # the city token (before a comma) and any country/city word
    city = low.split(",")[0].split("·")[0].strip()
    if city:
        kws.add(city)
    for country, region in _COUNTRY_REGION.items():
        if re.search(rf"(?<![\w]){re.escape(country)}(?![\w])", low):
            kws.add(country)
            kws |= _REGION_SYNONYMS.get(region, {region})
    # also match a bare region name typed directly
    for region, syns in _REGION_SYNONYMS.items():
        if region in low:
            kws |= syns
    return kws


def location_matches(job: Job, user_location: str) -> bool:
    if not user_location.strip():
        return True
    jl = (job.location or "").lower()
    if not jl or job.mode.lower() == "remote" and not jl:
        return True
    kws = location_keywords(user_location)
    # direct city/country substring, or an eligible region keyword
    if city := user_location.lower().split(",")[0].strip():
        if city and city in jl:
            return True
    return any(kw and kw in jl for kw in kws)


def job_level(title: str) -> int | None:
    low = title.lower()
    for word, rank in vocab.SENIORITY.items():
        if re.search(rf"(?<![\w]){re.escape(word)}(?![\w])", low):
            return {0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4}.get(rank)
    return None


_POSTED_MAX = {"24h": 1, "7d": 7, "30d": 30, "any": 10_000}


def filter_jobs(jobs: list[Job], q: dict) -> list[Job]:
    out: list[Job] = []
    types = q.get("job_types") or set()
    levels = {l.lower() for l in (q.get("levels") or set())}
    level_ranks = {_LEVELS[l] for l in levels if l in _LEVELS}
    smin = q.get("salary_min", 0)
    smax = q.get("salary_max", 10_000_000)
    max_days = _POSTED_MAX.get(q.get("posted_within", "any"), 10_000)
    loc = q.get("location", "")
    remote_only = q.get("remote_only", False)

    for j in jobs:
        if remote_only and j.mode.lower() != "remote":
            continue
        if not location_matches(j, loc):
            continue
        if types and j.type not in types:
            continue
        if level_ranks:
            lv = job_level(j.title)
            if lv is not None and lv not in level_ranks:
                continue
        # salary: the slider is a USD scale, so only filter USD-denominated jobs
        # (comparing a PKR/EUR figure against a USD range would be meaningless).
        if (getattr(j, "currency", "USD") == "USD"
                and j.salary_min is not None and j.salary_max is not None):
            if j.salary_max < smin or j.salary_min > smax:
                continue
        if j.posted_days > max_days:
            continue
        out.append(j)
    return out
