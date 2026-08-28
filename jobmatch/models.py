"""Dataclass models for the app store (mirrors README "State Management")."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

ApplyType = Literal["website", "email", "form", "none"]
Confidence = Literal["high", "low"]


@dataclass
class Skill:
    name: str
    confidence: Confidence = "high"


@dataclass
class Profile:
    name: str = ""
    current_title: str = ""
    target_title: str = ""
    years: str = ""
    years_span: str = ""
    location: str = ""
    remote_ok: bool = True
    skills: list[Skill] = field(default_factory=list)
    confidence: Confidence = "high"
    # richer awareness (populated by AI parsing when available)
    seniority: str = ""              # Junior / Mid / Senior / Lead
    domains: list[str] = field(default_factory=list)   # e.g. fintech, analytics
    education: str = ""
    summary: str = ""                # one-line professional summary
    raw_text: str = ""               # full résumé text (for semantic matching)


@dataclass
class Factors:
    skills: tuple[str, int] = ("", 0)       # (label, pct)
    seniority: tuple[str, int] = ("", 0)
    location: tuple[str, int] = ("", 0)
    tooling: tuple[str, int] = ("", 0)


@dataclass
class Apply:
    type: ApplyType = "none"
    value: str = ""


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    mode: str                # Remote / Hybrid / On-site
    type: str                # Full-time / Contract / ...
    salary_min: Optional[int]
    salary_max: Optional[int]
    score: int               # 0-100
    factors: Factors
    posted: str              # human string, e.g. "2 days ago"
    posted_days: int = 999   # age in days, for the "date posted" filter
    apply: Apply = None
    description: str = ""
    requirements: list[tuple[bool, str]] = field(default_factory=list)  # (met, text)
    benefits: str = ""
    matched_skills: list[str] = field(default_factory=list)
    extra_skill_count: int = 0
    source: str = ""
    currency: str = "USD"

    @property
    def salary_label(self) -> str:
        from .services.currency import format_range
        return format_range(self.salary_min, self.salary_max, self.currency)


@dataclass
class SavedJob:
    job: Job
    saved_at: str
    applied_at: Optional[str] = None
    deadline: Optional[str] = None
    expired: bool = False
    channel_note: str = ""
