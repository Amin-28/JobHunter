"""LinkedIn Job Search API (RapidAPI, by fantastic-jobs / Active Jobs DB).

A ToS-compliant, location-aware job search that indexes LinkedIn (and other)
postings — the practical way to get real Karachi/Pakistan + LinkedIn jobs. Uses
the same RAPIDAPI_KEY as JSearch; you must Subscribe to *this* API's free plan on
RapidAPI (rapidapi.com/fantastic-jobs-fantastic-jobs-default/api/linkedin-job-
search-api). Without a key/subscription it's skipped or errors clearly.
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
    where = (location or "").split("·")[0].strip()
    title = " ".join(keywords[:3]) or "developer"
    params = {"title_filter": title, "limit": str(min(limit, 20))}
    if where:
        params["location_filter"] = where
    url = f"https://{HOST}/active-jb-7d?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "x-rapidapi-key": key, "x-rapidapi-host": HOST, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:220]
        raise RuntimeError(f"LinkedIn API HTTP {e.code} — {body}") from e

    rows = data if isinstance(data, list) else data.get("data") or data.get("jobs") or []
    out: list[RawJob] = []
    for r in rows[:limit]:
        if not isinstance(r, dict):
            continue
        title_v = (r.get("title") or "").strip()
        if not title_v:
            continue
        loc = _first(r.get("locations_derived")) or _first(r.get("cities_derived")) \
            or _first(r.get("countries_derived")) or where or "—"
        out.append(RawJob(
            title=title_v,
            company=(r.get("organization") or r.get("organization_name")
                     or "Company").strip() or "Company",
            location=loc,
            mode="Remote" if r.get("remote_derived") else "On-site",
            type=map_type(_first(r.get("employment_type"))),
            salary_min=None, salary_max=None,     # salary_raw is inconsistent; skip
            posted=relative_date(r.get("date_posted")),
            posted_days=days_since(r.get("date_posted")),
            url=r.get("url") or "",
            description=shorten(r.get("description_text") or r.get("description") or "", 700),
            tags=[w for w in title_v.split() if len(w) > 2][:4],
            source="LinkedIn",
            currency=currency_for_location(loc),
        ))
    return out


def _first(v):
    if isinstance(v, list):
        return str(v[0]).strip() if v else ""
    return str(v).strip() if v else ""
