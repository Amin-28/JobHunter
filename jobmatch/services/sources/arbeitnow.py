"""Arbeitnow — real on-site + remote jobs (Europe-heavy), no key.

The free board API returns a recent feed with no server-side search, so we
filter by keyword locally. It carries genuine city locations.
"""
from __future__ import annotations

from .base import (RawJob, detect_mode, get_json, html_to_text, map_type,
                   register, relative_date, days_since, shorten)

URL = "https://www.arbeitnow.com/api/job-board-api"


def _matches(kws: list[str], title: str, tags: list[str], desc: str) -> bool:
    if not kws:
        return True
    hay = f"{title} {' '.join(tags)} {desc[:400]}".lower()
    return any(k.lower() in hay for k in kws)


@register("Arbeitnow")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    data = get_json(URL)
    out: list[RawJob] = []
    for r in data.get("data", []):
        title = (r.get("title") or "").strip()
        if not title:
            continue
        tags = [t for t in (r.get("tags") or []) if isinstance(t, str)]
        text = html_to_text(r.get("description") or "")
        if not _matches(keywords, title, tags, text):
            continue
        loc = (r.get("location") or "").strip() or "Europe"
        out.append(RawJob(
            title=title,
            company=(r.get("company_name") or "Company").strip(),
            location=loc,
            mode=detect_mode(loc, r.get("remote")),
            type=map_type(r.get("job_types")),
            salary_min=None, salary_max=None,
            posted=relative_date(r.get("created_at")),
            posted_days=days_since(r.get("created_at")),
            url=r.get("url") or "",
            description=shorten(text, 700),
            tags=tags,
            source="Arbeitnow",
            currency="EUR",
        ))
        if len(out) >= limit:
            break
    return out
