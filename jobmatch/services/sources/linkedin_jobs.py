"""LinkedIn Job Search API (RapidAPI, by fantastic-jobs / Active Jobs DB).

ToS-compliant, location-aware LinkedIn job search — the working way to get real
Karachi/Pakistan + LinkedIn listings. Uses the RAPIDAPI_KEY; Subscribe to *this*
API's free plan on RapidAPI. Endpoint: GET /active-jb with title/location/
time_frame; returns a JSON array of jobs (with AI-extracted salary/skills).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from .. import config
from ..currency import currency_for_location
from .base import RawJob, UA, map_type, register, relative_date, days_since, shorten

HOST = "linkedin-job-search-api.p.rapidapi.com"


@register("LinkedIn")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    key = config.rapidapi_key()
    if not key:
        raise RuntimeError("RapidAPI key not configured")
    where = (location or "").split("·")[0].strip() or "Pakistan"
    title = keywords[0] if keywords else "developer"
    params = {"title": title, "location": where, "time_frame": "7d"}
    url = f"https://{HOST}/active-jb?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "x-rapidapi-key": key, "x-rapidapi-host": HOST, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:220]
        raise RuntimeError(f"LinkedIn API HTTP {e.code} — {body}") from e

    rows = data if isinstance(data, list) else (data.get("data") or [])
    out: list[RawJob] = []
    for r in rows[:limit]:
        if not isinstance(r, dict):
            continue
        title_v = (r.get("title") or "").strip()
        if not title_v:
            continue
        loc = _first(r.get("locations_derived")) or _first(r.get("countries_derived")) or where
        arrangement = (r.get("ai_work_arrangement") or "").lower()
        remote = "remote" in arrangement or "remote" in title_v.lower()
        smin = _num(r.get("ai_salary_min_value"))
        smax = _num(r.get("ai_salary_max_value"))
        cur = (r.get("ai_salary_currency") or "").strip() or currency_for_location(loc)
        skills = r.get("ai_key_skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]
        desc = (r.get("ai_requirements_summary") or r.get("ai_core_responsibilities")
                or "") or ""
        if isinstance(desc, list):
            desc = " ".join(str(x) for x in desc)
        out.append(RawJob(
            title=title_v,
            company=(r.get("organization") or "Company").strip() or "Company",
            location=loc,
            mode="Remote" if remote else "On-site",
            type=map_type(_first(r.get("employment_type"))),
            salary_min=smin, salary_max=smax,
            posted=relative_date(r.get("date_posted")),
            posted_days=days_since(r.get("date_posted")),
            url=r.get("url") or "",
            description=shorten(desc, 700),
            tags=[str(s) for s in skills if s][:5] or [w for w in title_v.split() if len(w) > 2][:4],
            source="LinkedIn",
            currency=cur,
        ))
    return out


def _first(v):
    if isinstance(v, list):
        return str(v[0]).strip() if v else ""
    return str(v).strip() if v else ""


def _num(v):
    try:
        n = int(float(v))
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None
