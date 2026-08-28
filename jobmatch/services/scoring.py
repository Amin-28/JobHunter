"""Compute a job's match score and factor breakdown against a profile.

Produces the same shape the UI already renders (README 1f "Match breakdown"):
Skills `9/12`, Seniority `Match`, Location `Remote ok`, Tooling `2/5`, plus an
overall 0–100 score. Deterministic and dependency-free.
"""
from __future__ import annotations

import re

from ..models import Factors, Profile
from . import vocab

# overall score weighting
_W = {"skills": 0.45, "seniority": 0.20, "location": 0.20, "tooling": 0.15}


def _seniority_rank(text: str) -> int | None:
    low = text.lower()
    best = None
    for word, rank in vocab.SENIORITY.items():
        if re.search(rf"(?<![\w]){re.escape(word)}(?![\w])", low):
            best = rank if best is None else max(best, rank)
    return best


def score_job(profile: Profile, *, title: str, text: str, tags: list[str]
              ) -> tuple[int, Factors, list[str]]:
    """Return (score 0-100, Factors, matched_skill_names)."""
    haystack = f"{title}\n{text}\n{' '.join(tags)}".lower()

    # ---- skills ----
    profile_skills = [s.name for s in profile.skills] or []
    total = max(1, min(len(profile_skills), 12))
    considered = profile_skills[:12]
    matched = [name for name in considered if _mentions(name, haystack)]
    skills_pct = round(100 * len(matched) / total)

    # ---- tooling ----
    tools = [s for s in considered if s in vocab.TOOLING]
    tool_total = max(1, min(len(tools), 5)) if tools else 5
    tool_matched = [s for s in tools if _mentions(s, haystack)]
    tooling_pct = round(100 * len(tool_matched) / tool_total)

    # ---- seniority ----
    p_rank = _seniority_rank(profile.current_title) or _years_to_rank(profile.years)
    j_rank = _seniority_rank(title)
    if j_rank is None or p_rank is None:
        sen_label, sen_pct = "Unknown", 60
    else:
        diff = abs(p_rank - j_rank)
        if diff == 0:
            sen_label, sen_pct = "Match", 92
        elif diff == 1:
            sen_label, sen_pct = "Close", 74
        else:
            sen_label, sen_pct = "Below" if j_rank < p_rank else "Above", 55

    # ---- location ----
    loc_label, loc_pct = _location_factor(profile, haystack)

    factors = Factors(
        skills=(f"{len(matched)}/{total}", skills_pct),
        seniority=(sen_label, sen_pct),
        location=(loc_label, loc_pct),
        tooling=(f"{len(tool_matched)}/{tool_total}", tooling_pct),
    )
    overall = round(
        _W["skills"] * skills_pct + _W["seniority"] * sen_pct
        + _W["location"] * loc_pct + _W["tooling"] * tooling_pct
    )
    return max(0, min(100, overall)), factors, matched


def _mentions(skill: str, haystack: str) -> bool:
    aliases = vocab.SKILLS.get(skill, [skill.lower()])
    for a in aliases:
        pat = a if "\\b" in a else re.escape(a)
        if re.search(rf"(?<![\w]){pat}(?![\w])", haystack):
            return True
    return False


def _years_to_rank(years: str) -> int | None:
    m = re.search(r"\d+", years or "")
    if not m:
        return None
    n = int(m.group())
    if n < 2:
        return 1
    if n < 5:
        return 2
    if n < 9:
        return 3
    return 4


def _location_factor(profile: Profile, haystack: str) -> tuple[str, int]:
    is_remote = bool(re.search(r"\bremote\b|anywhere|worldwide", haystack))
    is_hybrid = "hybrid" in haystack
    if profile.remote_ok and is_remote:
        return "Remote ok", 100
    # same city?
    city = (profile.location.split(",")[0] or "").strip().lower()
    if city and len(city) > 2 and city in haystack:
        return "Same city", 100
    if is_hybrid:
        return "Hybrid", 70
    if is_remote:
        return "Remote", 90
    return "On-site", 35
