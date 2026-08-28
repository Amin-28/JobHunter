"""Jobicy — remote jobs with geo + level, no key."""
from __future__ import annotations

from .base import (RawJob, get_json, html_to_text, map_type, register,
                   relative_date, days_since, shorten)

URL = "https://jobicy.com/api/v2/remote-jobs"


@register("Jobicy")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    params = {"count": min(50, max(10, limit))}
    if keywords:
        params["tag"] = keywords[0]
    data = get_json(URL, params)
    out: list[RawJob] = []
    for r in data.get("jobs", [])[:limit]:
        title = (r.get("jobTitle") or "").strip()
        if not title:
            continue
        text = html_to_text(r.get("jobDescription") or r.get("jobExcerpt") or "")
        geo = (r.get("jobGeo") or "Remote").strip() or "Remote"
        out.append(RawJob(
            title=title,
            company=(r.get("companyName") or "Company").strip(),
            location=geo,
            mode="Remote",
            type=map_type(r.get("jobType")),
            salary_min=r.get("annualSalaryMin") or None,
            salary_max=r.get("annualSalaryMax") or None,
            posted=relative_date(r.get("pubDate")),
            posted_days=days_since(r.get("pubDate")),
            url=r.get("url") or "",
            description=shorten(text, 700),
            tags=([r["jobIndustry"]] if isinstance(r.get("jobIndustry"), str)
                  else list(r.get("jobIndustry") or [])),
            source="Jobicy",
        ))
    return out
