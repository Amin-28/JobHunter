"""Shared types + helpers + the source registry."""
from __future__ import annotations

import datetime as _dt
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

UA = "Mozilla/5.0 (JobMatchAI research desktop app)"


@dataclass
class RawJob:
    title: str
    company: str
    location: str
    mode: str                       # Remote / Hybrid / On-site
    type: str                       # Full-time / Contract / ...
    salary_min: int | None
    salary_max: int | None
    posted: str
    posted_days: int
    url: str
    description: str
    tags: list[str] = field(default_factory=list)
    source: str = ""
    currency: str = "USD"           # ISO code for the salary amounts
    apply_type: str = "website"     # website | email | form | none
    apply_value: str = ""           # defaults to url when empty


# name -> fetch(keywords, location, limit) -> list[RawJob]
Fetcher = Callable[[list[str], str, int], "list[RawJob]"]
SOURCES: dict[str, Fetcher] = {}


def register(name: str) -> Callable[[Fetcher], Fetcher]:
    def deco(fn: Fetcher) -> Fetcher:
        SOURCES[name] = fn
        return fn
    return deco


def source_names() -> list[str]:
    # ensure adapters are imported/registered
    from . import (remotive, arbeitnow, jobicy, remoteok, adzuna, jooble,  # noqa: F401
                   jsearch)
    return list(SOURCES.keys())


# ----------------------------------------------------------------- http
def get_json(url: str, params: dict | None = None, timeout: int = 12):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def post_json(url: str, body: dict, timeout: int = 12):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"User-Agent": UA, "Accept": "application/json",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


# ----------------------------------------------------------------- text
TYPE_MAP = {
    "full_time": "Full-time", "full-time": "Full-time", "fulltime": "Full-time",
    "part_time": "Part-time", "part-time": "Part-time",
    "contract": "Contract", "freelance": "Contract", "temporary": "Contract",
    "internship": "Internship", "intern": "Internship", "other": "Full-time",
}


def map_type(raw) -> str:
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    return TYPE_MAP.get(str(raw).strip().lower(), "Full-time")


def html_to_text(s: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", s)
    s = re.sub(r"(?i)</(p|div|li|h[1-6]|br)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def shorten(s: str, n: int) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def parse_salary_text(s: str) -> tuple[int | None, int | None]:
    if not s or re.search(r"hour|/hr|per hour|hourly|/h\b", s, re.I):
        return None, None
    vals: list[int] = []
    for tok in re.findall(r"\d[\d,]*", s):
        n = int(tok.replace(",", ""))
        if n < 1000:
            n *= 1000
        if 20000 <= n <= 10_000_000:   # wide enough for PKR/JPY annual figures
            vals.append(n)
    vals = sorted(set(vals))
    if not vals:
        return None, None
    if len(vals) == 1:
        return vals[0], vals[0]
    lo, hi = vals[0], vals[-1]
    if hi > lo * 4:
        return None, None
    return lo, hi


def days_since(iso: str | None) -> int:
    if not iso:
        return 999
    for parse in (_iso, _epoch):
        d = parse(iso)
        if d is not None:
            return max(0, (_dt.date.today() - d).days)
    return 999


def relative_date(iso_or_days) -> str:
    days = iso_or_days if isinstance(iso_or_days, int) else days_since(iso_or_days)
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 30:
        return f"{days // 7} week{'s' if days // 7 != 1 else ''} ago"
    return f"{days // 30} month{'s' if days // 30 != 1 else ''} ago"


def _iso(s):
    try:
        return _dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def _epoch(s):
    try:
        return _dt.datetime.fromtimestamp(int(s)).date()
    except (ValueError, TypeError, OSError):
        return None


def detect_mode(text: str, remote_flag: bool | None = None) -> str:
    low = (text or "").lower()
    if remote_flag or "remote" in low or "anywhere" in low or "worldwide" in low:
        return "Remote"
    if "hybrid" in low:
        return "Hybrid"
    return "On-site"
