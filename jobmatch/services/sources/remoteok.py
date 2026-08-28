"""RemoteOK — remote jobs with salary + tags, no key.

The first array element is a legal/notice object; skip anything without a
``position``. No server-side search, so filter by keyword locally.
"""
from __future__ import annotations

from .base import (RawJob, get_json, html_to_text, register, relative_date,
                   days_since, shorten)

URL = "https://remoteok.com/api"


def _matches(kws: list[str], title: str, tags: list[str]) -> bool:
    if not kws:
        return True
    hay = f"{title} {' '.join(tags)}".lower()
    return any(k.lower() in hay for k in kws)


@register("RemoteOK")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    data = get_json(URL)
    out: list[RawJob] = []
    for r in data:
        if not isinstance(r, dict) or not r.get("position"):
            continue
        title = r["position"].strip()
        tags = [t for t in (r.get("tags") or []) if isinstance(t, str)]
        if not _matches(keywords, title, tags):
            continue
        smin = r.get("salary_min") or None
        smax = r.get("salary_max") or None
        if smin and smin < 20000:
            smin = smax = None
        out.append(RawJob(
            title=title,
            company=(r.get("company") or "Company").strip(),
            location=(r.get("location") or "Remote").strip() or "Remote",
            mode="Remote",
            type="Full-time",
            salary_min=smin, salary_max=smax,
            posted=relative_date(r.get("epoch") or r.get("date")),
            posted_days=days_since(r.get("epoch") or r.get("date")),
            url=r.get("url") or r.get("apply_url") or "",
            description=shorten(html_to_text(r.get("description") or ""), 700),
            tags=tags,
            source="RemoteOK",
        ))
        if len(out) >= limit:
            break
    return out
