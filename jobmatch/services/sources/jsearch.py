"""JSearch (RapidAPI) — Google-for-Jobs aggregation.

Google for Jobs legally indexes LinkedIn, Indeed, Glassdoor, ZipRecruiter and
company sites; JSearch exposes that as a proper API. This is the ToS-compliant
way to surface LinkedIn-sourced listings (no scraping), and it supports real
location search — so a Karachi query returns Karachi jobs. Each job keeps its
original publisher (e.g. "LinkedIn") as the source label.

Needs a free RapidAPI key (rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch),
set via env ``RAPIDAPI_KEY`` or the in-app Settings. Without a key it's skipped.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
import json

from .. import config
from ..currency import currency_for_location
from .base import (RawJob, UA, html_to_text, map_type, register,
                   relative_date, days_since, shorten)

HOST = "jsearch.p.rapidapi.com"


@register("JSearch")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    key = config.rapidapi_key()
    if not key:
        raise RuntimeError("RapidAPI key not configured")
    where = (location or "").split("·")[0].strip()
    terms = " ".join(keywords[:3]) or "developer"
    query = f"{terms} in {where}" if where else terms
    params = {"query": query, "page": "1", "num_pages": "1"}
    url = f"https://{HOST}/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": key, "X-RapidAPI-Host": HOST, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))

    out: list[RawJob] = []
    for r in (data.get("data") or [])[:limit]:
        title = (r.get("job_title") or "").strip()
        if not title:
            continue
        city = (r.get("job_city") or "").strip()
        country = (r.get("job_country") or "").strip()
        loc = ", ".join(p for p in (city, country) if p) or (where or "—")
        remote = bool(r.get("job_is_remote"))
        smin = r.get("job_min_salary")
        smax = r.get("job_max_salary")
        cur = (r.get("job_salary_currency") or "").strip() or currency_for_location(loc)
        skills = r.get("job_required_skills") or []
        out.append(RawJob(
            title=title,
            company=(r.get("employer_name") or "Company").strip() or "Company",
            location=loc,
            mode="Remote" if remote else "On-site",
            type=map_type(r.get("job_employment_type")),
            salary_min=int(smin) if smin else None,
            salary_max=int(smax) if smax else None,
            posted=relative_date(r.get("job_posted_at_datetime_utc")),
            posted_days=days_since(r.get("job_posted_at_datetime_utc")),
            url=r.get("job_apply_link") or "",
            description=shorten(html_to_text(r.get("job_description") or ""), 700),
            tags=[s for s in skills if isinstance(s, str)][:5],
            # keep the real publisher (LinkedIn / Indeed / …) as the source label
            source=(r.get("job_publisher") or "JSearch").strip(),
            currency=cur,
        ))
    return out
