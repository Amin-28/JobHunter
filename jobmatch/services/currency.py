"""Per-country currency: pick the right code for a job, format amounts nicely."""
from __future__ import annotations

import re

# country (lowercase substring) -> ISO currency code
COUNTRY_CURRENCY = {
    "pakistan": "PKR", "india": "INR", "bangladesh": "BDT", "sri lanka": "LKR",
    "united states": "USD", "usa": "USD", "u.s.": "USD", "canada": "CAD",
    "united kingdom": "GBP", "uk": "GBP", "england": "GBP", "ireland": "EUR",
    "germany": "EUR", "france": "EUR", "spain": "EUR", "portugal": "EUR",
    "italy": "EUR", "netherlands": "EUR", "belgium": "EUR", "austria": "EUR",
    "greece": "EUR", "finland": "EUR", "poland": "PLN", "switzerland": "CHF",
    "sweden": "SEK", "norway": "NOK", "denmark": "DKK",
    "australia": "AUD", "new zealand": "NZD", "singapore": "SGD",
    "malaysia": "MYR", "indonesia": "IDR", "philippines": "PHP",
    "united arab emirates": "AED", "uae": "AED", "saudi arabia": "SAR",
    "qatar": "QAR", "nigeria": "NGN", "kenya": "KES", "south africa": "ZAR",
    "egypt": "EGP", "brazil": "BRL", "mexico": "MXN", "argentina": "ARS",
    "turkey": "TRY", "japan": "JPY", "china": "CNY",
}

# ISO code -> display prefix
SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "PKR": "₨", "INR": "₹", "JPY": "¥",
    "CNY": "¥", "AUD": "A$", "CAD": "C$", "NZD": "NZ$", "SGD": "S$",
    "AED": "AED ", "SAR": "SAR ", "QAR": "QAR ", "ZAR": "R", "NGN": "₦",
    "KES": "KSh ", "BRL": "R$", "MXN": "MX$", "TRY": "₺", "CHF": "CHF ",
    "SEK": "kr ", "NOK": "kr ", "DKK": "kr ", "PLN": "zł ", "BDT": "৳",
    "LKR": "Rs ", "IDR": "Rp ", "MYR": "RM ", "PHP": "₱", "EGP": "E£",
    "ARS": "AR$",
}

# symbols/words that appear inside free-text salary strings
_TEXT_HINTS = [
    ("₨", "PKR"), ("rs.", "PKR"), ("rs ", "PKR"), ("pkr", "PKR"),
    ("₹", "INR"), ("inr", "INR"), ("€", "EUR"), ("eur", "EUR"),
    ("£", "GBP"), ("gbp", "GBP"), ("$", "USD"), ("usd", "USD"),
    ("aed", "AED"), ("sar", "SAR"), ("₦", "NGN"), ("ngn", "NGN"),
    ("zar", "ZAR"), ("aud", "AUD"), ("cad", "CAD"), ("₱", "PHP"),
]


def currency_for_location(location: str, default: str = "USD") -> str:
    low = (location or "").lower()
    for name, code in COUNTRY_CURRENCY.items():
        if name in low:
            return code
    return default


def detect_currency(text: str) -> str | None:
    low = (text or "").lower()
    for hint, code in _TEXT_HINTS:
        if hint in low:
            return code
    return None


def _amount(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1000:
        return f"{n // 1000}k"
    return str(n)


def format_range(lo: int | None, hi: int | None, code: str = "USD") -> str:
    if lo is None or hi is None:
        return "Salary not listed"
    sym = SYMBOLS.get(code, code + " ")
    if lo == hi:
        return f"{sym}{_amount(lo)}"
    return f"{sym}{_amount(lo)} – {sym}{_amount(hi)}"
