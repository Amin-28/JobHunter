"""Adzuna — legal aggregator of Indeed-style listings across many boards.

Requires a free API key (app_id + app_key from developer.adzuna.com), set via
env (ADZUNA_APP_ID / ADZUNA_APP_KEY) or the settings file. Without keys this
source raises and the aggregator simply skips it. Adzuna is real *location-based*
search (actual city listings), which the free remote-only APIs can't provide.
"""
from __future__ import annotations

from .. import config
from .base import (RawJob, get_json, html_to_text, register, relative_date,
                   days_since, shorten)

# Adzuna country coverage -> code. Pakistan isn't covered; fall back sensibly.
_COUNTRY_CODE = {
    "united kingdom": "gb", "uk": "gb", "united states": "us", "usa": "us",
    "canada": "ca", "australia": "au", "germany": "de", "france": "fr",
    "india": "in", "italy": "it", "spain": "es", "netherlands": "nl",
    "new zealand": "nz", "poland": "pl", "singapore": "sg", "brazil": "br",
    "south africa": "za", "austria": "at", "mexico": "mx",
}


_CODE_CURRENCY = {
    "gb": "GBP", "us": "USD", "ca": "CAD", "au": "AUD", "de": "EUR",
    "fr": "EUR", "in": "INR", "it": "EUR", "es": "EUR", "nl": "EUR",
    "nz": "NZD", "pl": "PLN", "sg": "SGD", "br": "BRL", "za": "ZAR",
    "at": "EUR", "mx": "MXN",
}


def _country(location: str) -> str:
    low = (location or "").lower()
    for name, code in _COUNTRY_CODE.items():
        if name in low:
            return code
    # Pakistan/Asia not covered by Adzuna → default to a large market
    return "gb"


@register("Adzuna")
def fetch(keywords: list[str], location: str, limit: int) -> list[RawJob]:
    keys = config.adzuna_keys()
    if not keys:
        raise RuntimeError("Adzuna keys not configured")
    app_id, app_key = keys
    country = _country(location)
    params = {
        "app_id": app_id, "app_key": app_key,
        "results_per_page": min(50, limit),
        "what": " ".join(keywords[:4]) or "analyst",
        "content-type": "application/json",
    }
    where = (location or "").split(",")[0].split("·")[0].strip()
    if where:
        params["where"] = where
    data = get_json(f"https://api.adzuna.com/v1/api/jobs/{country}/search/1", params)
    out: list[RawJob] = []
    for r in data.get("results", [])[:limit]:
        title = (r.get("title") or "").strip()
        if not title:
            continue
        loc = (r.get("location", {}) or {}).get("display_name", "") or where or "—"
        smin = int(r["salary_min"]) if r.get("salary_min") else None
        smax = int(r["salary_max"]) if r.get("salary_max") else None
        out.append(RawJob(
            title=title,
            company=((r.get("company", {}) or {}).get("display_name") or "Company").strip(),
            location=loc,
            mode="On-site" if where else "Remote",
            type=r.get("contract_time", "").replace("_", "-").title() or "Full-time",
            salary_min=smin, salary_max=smax,
            posted=relative_date(r.get("created")),
            posted_days=days_since(r.get("created")),
            url=r.get("redirect_url") or "",
            description=shorten(html_to_text(r.get("description") or ""), 700),
            tags=[r.get("category", {}).get("label", "")] if r.get("category") else [],
            source="Adzuna",
            currency=_CODE_CURRENCY.get(country, "USD"),
        ))
    return out
