"""Jooble — global aggregator that DOES cover Pakistan (and ~70 countries).

Needs a free API key (jooble.org/api/about), set via env ``JOOBLE_KEY`` or the
settings file. This is the practical way to get real *local* Pakistan listings
(Karachi/Lahore/Islamabad on-site roles) that the remote-only free APIs and
Adzuna don't carry. Without a key this source raises and is skipped.
"""
from __future__ import annotations

import re

from .. import config
from ..currency import currency_for_location, detect_currency
from .base import (RawJob, detect_mode, html_to_text, map_type, post_json,
                   parse_salary_text, register, relative_date, days_since, shorten)


@register("Jooble")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    key = config.jooble_key()
    if not key:
        raise RuntimeError("Jooble key not configured")
    where = (location or "").split("·")[0].strip()
    body = {"keywords": " ".join(keywords[:4]) or "developer", "location": where}
    data = post_json(f"https://jooble.org/api/{key}", body)
    out: list[RawJob] = []
    for r in data.get("jobs", [])[:limit]:
        title = (r.get("title") or "").strip()
        if not title:
            continue
        text = html_to_text(r.get("snippet") or "")
        loc = (r.get("location") or where or "—").strip()
        salary_str = r.get("salary") or ""
        smin, smax = parse_salary_text(salary_str)
        cur = detect_currency(salary_str) or currency_for_location(loc or where)
        out.append(RawJob(
            title=title,
            company=(r.get("company") or "Company").strip() or "Company",
            location=loc,
            mode=detect_mode(f"{title} {loc} {text}"),
            type=map_type(r.get("type")),
            salary_min=smin, salary_max=smax,
            posted=relative_date(r.get("updated")),
            posted_days=days_since(r.get("updated")),
            url=r.get("link") or "",
            description=shorten(text, 700),
            tags=_tags(title),
            source="Jooble",
            currency=cur,
        ))
    return out


def _tags(title: str) -> list[str]:
    # Jooble has no tag field; derive a couple of coarse keywords from the title
    words = re.findall(r"[A-Za-z][A-Za-z+#.]{2,}", title)
    stop = {"senior", "junior", "the", "and", "for", "with", "remote"}
    return [w for w in words if w.lower() not in stop][:4]
