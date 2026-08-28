"""Remotive — remote jobs, keyword search, no key. Region eligibility in loc."""
from __future__ import annotations

from .base import (RawJob, get_json, html_to_text, map_type, parse_salary_text,
                   register, relative_date, days_since, shorten)

URL = "https://remotive.com/api/remote-jobs"


@register("Remotive")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    query = " ".join(keywords[:3]) if keywords else "analyst"
    data = get_json(URL, {"search": query, "limit": limit})
    out: list[RawJob] = []
    for r in data.get("jobs", [])[:limit]:
        title = (r.get("title") or "").strip()
        if not title:
            continue
        text = html_to_text(r.get("description") or "")
        smin, smax = parse_salary_text(r.get("salary") or "")
        out.append(RawJob(
            title=title,
            company=(r.get("company_name") or "Company").strip(),
            location=(r.get("candidate_required_location") or "Remote").strip() or "Remote",
            mode="Remote",
            type=map_type(r.get("job_type")),
            salary_min=smin, salary_max=smax,
            posted=relative_date(r.get("publication_date")),
            posted_days=days_since(r.get("publication_date")),
            url=r.get("url") or "",
            description=shorten(text, 700),
            tags=[t for t in (r.get("tags") or []) if isinstance(t, str)],
            source="Remotive",
        ))
    return out
