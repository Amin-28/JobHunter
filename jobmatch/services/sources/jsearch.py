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

import urllib.error
import urllib.parse
import urllib.request
import json

from .. import config
from ..currency import currency_for_location
from .base import (RawJob, UA, html_to_text, map_type, register,
                   relative_date, days_since, shorten)

HOST = "jsearch.p.rapidapi.com"

# location country -> ISO 3166-1 alpha-2 (JSearch's `country` param)
_ISO = {
    "pakistan": "pk", "india": "in", "bangladesh": "bd", "sri lanka": "lk",
    "united states": "us", "usa": "us", "u.s.": "us", "canada": "ca",
    "united kingdom": "gb", "uk": "gb", "england": "gb", "ireland": "ie",
    "germany": "de", "france": "fr", "spain": "es", "italy": "it",
    "netherlands": "nl", "poland": "pl", "australia": "au", "new zealand": "nz",
    "singapore": "sg", "malaysia": "my", "indonesia": "id", "philippines": "ph",
    "united arab emirates": "ae", "uae": "ae", "saudi arabia": "sa", "qatar": "qa",
    "nigeria": "ng", "kenya": "ke", "south africa": "za", "egypt": "eg",
    "brazil": "br", "mexico": "mx", "turkey": "tr", "japan": "jp", "china": "cn",
}


def _iso_and_city(location: str) -> tuple[str | None, str]:
    low = (location or "").lower()
    iso = None
    for name, code in _ISO.items():
        if name in low:
            iso = code
            break
    city = (location or "").split(",")[0].split("·")[0].strip()
    # don't treat a country name as a "city"
    if city.lower() in _ISO:
        city = ""
    return iso, city


@register("JSearch")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    key = config.rapidapi_key()
    if not key:
        raise RuntimeError("RapidAPI key not configured")
    iso, city = _iso_and_city(location)
    terms = " ".join(keywords[:3]) or "developer"
    query = f"{terms} {city}".strip() if city else terms
    params = {"query": query, "page": "1", "num_pages": "1"}
    if iso:                       # proper country filter (pk, us, gb …)
        params["country"] = iso
    url = f"https://{HOST}/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "X-RapidAPI-Key": key, "X-RapidAPI-Host": HOST, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:220]
        raise RuntimeError(f"JSearch HTTP {e.code} — {body}") from e

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
