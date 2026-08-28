"""Real résumé parsing: PDF/DOCX text extraction + heuristic profile building.

`parse_resume(path, progress)` returns a populated ``Profile``. It runs entirely
locally (no network) — honouring the handoff's "everything happens on your
machine" promise. Heuristics are intentionally transparent and easy to tune;
swap in an LLM or a dedicated résumé parser behind the same signature later.
"""
from __future__ import annotations

import datetime as _dt
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Callable, Optional

from ..models import Profile, Skill
from . import vocab

Progress = Optional[Callable[[int, str], None]]


class ParseError(Exception):
    pass


# ---------------------------------------------------------------- extraction
def extract_text(path: str | Path) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(p)
    if ext == ".docx":
        return _extract_docx(p)
    raise ParseError(f"Unsupported file type: {ext}")


def _extract_pdf(p: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:  # pragma: no cover
        raise ParseError("pypdf is required to read PDF files") from e
    try:
        reader = PdfReader(str(p))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as e:  # pragma: no cover - malformed file
        raise ParseError("We couldn't read that file.") from e


def _extract_docx(p: Path) -> str:
    """Extract text from a .docx without third-party deps (it's a zip of XML)."""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        with zipfile.ZipFile(p) as zf:
            xml = zf.read("word/document.xml")
    except Exception as e:
        raise ParseError("We couldn't read that file.") from e
    root = ET.fromstring(xml)
    lines: list[str] = []
    for para in root.iter(f"{ns}p"):
        text = "".join(node.text or "" for node in para.iter(f"{ns}t"))
        lines.append(text)
    return "\n".join(lines)


# ---------------------------------------------------------------- parsing
def parse_resume(path: str | Path, progress: Progress = None) -> Profile:
    def emit(pct: int, msg: str) -> None:
        if progress:
            progress(pct, msg)

    text = extract_text(path)
    if not text.strip():
        raise ParseError("We couldn't read that file.")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    pages = max(1, text.count("\f") + 1)
    emit(25, f"Extracted text from {pages} page{'s' if pages != 1 else ''}")

    sections = _split_sections(lines)
    found = [k for k in ("experience", "skills", "education") if k in sections]
    emit(50, "Found sections: " + (", ".join(s.title() for s in found) or "none"))

    name = _guess_name(lines)
    current_title = _guess_title(lines, sections)
    years, span = _estimate_experience(text, sections)
    location, remote_ok = _guess_location(text, lines)
    emit(75, "Identifying skills and seniority…")

    skills = _extract_skills(text, sections)

    confidence: str = "high" if (found and skills and name) else "low"
    profile = Profile(
        name=name or "Your Name",
        current_title=current_title or "—",
        target_title=current_title or "",
        years=years,
        years_span=span,
        location=location,
        remote_ok=remote_ok,
        confidence=confidence,
        skills=skills,
        raw_text=text,
    )

    # AI enhancement: a richer, more accurate profile when a key is configured
    from . import ai
    if ai.available():
        emit(85, f"Reading your résumé with {ai.active_provider()}…")
        enriched = _ai_enhance(profile, text)
        emit(100, "Profile ready")
        return enriched
    emit(100, "Building search keywords")
    return profile


def _ai_enhance(heuristic: Profile, text: str) -> Profile:
    """Overlay an LLM-extracted profile on the heuristic one (heuristic fills gaps)."""
    from . import ai
    data = ai.parse_profile(text)
    if not data:
        return heuristic

    def pick(key: str, fallback):
        v = data.get(key)
        return v if isinstance(v, str) and v.strip() else fallback

    ai_skills: list[Skill] = []
    for s in data.get("skills", []) or []:
        if isinstance(s, dict) and s.get("name"):
            conf = "low" if str(s.get("confidence")).lower() == "low" else "high"
            ai_skills.append(Skill(str(s["name"]).strip(), conf))
    skills = ai_skills or heuristic.skills

    years_num = data.get("years_experience")
    if isinstance(years_num, (int, float)) and years_num > 0:
        years = f"{int(years_num)} year{'s' if int(years_num) != 1 else ''}"
    else:
        years = heuristic.years

    domains = [str(d).strip() for d in (data.get("domains") or []) if str(d).strip()]
    remote = data.get("remote_ok")
    return Profile(
        name=pick("name", heuristic.name),
        current_title=pick("current_title", heuristic.current_title),
        target_title=pick("target_title", heuristic.target_title or heuristic.current_title),
        years=years,
        years_span=heuristic.years_span,
        location=pick("location", heuristic.location),
        remote_ok=bool(remote) if isinstance(remote, bool) else heuristic.remote_ok,
        confidence="high",
        skills=skills,
        seniority=pick("seniority", heuristic.seniority),
        domains=domains,
        education=pick("education", ""),
        summary=pick("summary", ""),
        raw_text=text,
    )


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    """Bucket lines under recognised section headers."""
    header_lookup: dict[str, str] = {}
    for canon, aliases in vocab.SECTION_HEADERS.items():
        for a in aliases:
            header_lookup[a] = canon

    sections: dict[str, list[str]] = {"_head": []}
    current = "_head"
    for ln in lines:
        key = ln.lower().strip(" :·-").strip()
        if key in header_lookup and len(ln) < 40:
            current = header_lookup[key]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(ln)
    return sections


def _guess_name(lines: list[str]) -> str:
    for ln in lines[:6]:
        if "@" in ln or any(c.isdigit() for c in ln):
            continue
        words = ln.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            if not any(tw in ln.lower() for tw in vocab.TITLE_WORDS):
                return ln.strip()
    return ""


def _guess_title(lines: list[str], sections: dict) -> str:
    # prefer a title-looking line near the top
    for ln in lines[:8]:
        low = ln.lower()
        if any(tw in low for tw in vocab.TITLE_WORDS) and len(ln) < 60:
            return re.sub(r"\s*[|·].*$", "", ln).strip()
    # else scan the experience section's first title-ish line
    for ln in sections.get("experience", [])[:6]:
        if any(tw in ln.lower() for tw in vocab.TITLE_WORDS):
            return ln.split("  ")[0].strip()
    return ""


def _estimate_experience(text: str, sections: dict | None = None) -> tuple[str, str]:
    # 1) an explicit "N years" phrase wins (e.g. a summary line)
    explicit = [int(m) for m in re.findall(r"\b(\d{1,2})\+?\s*years?\b", text.lower())]
    explicit = [n for n in explicit if 1 <= n <= 50]

    # 2) otherwise infer from date ranges — prefer the experience section so
    #    an education year doesn't inflate the span
    scope = " ".join(sections.get("experience", [])) if sections else ""
    nums = sorted({int(y) for y in re.findall(r"(?:19|20)\d{2}", scope)})
    if not nums:
        nums = sorted({int(y) for y in re.findall(r"(?:19|20)\d{2}", text)})
    now = _dt.date.today().year
    has_present = bool(re.search(r"present|current", scope or text, re.I))

    span = ""
    if nums:
        end_year = now if has_present else nums[-1]
        span = f"{nums[0]} – {'present' if has_present else nums[-1]}"

    if explicit:
        n = max(explicit)
        return f"{n} year{'s' if n != 1 else ''}", span
    if nums:
        total = max(0, (now if has_present else nums[-1]) - nums[0])
        return (f"{total} year{'s' if total != 1 else ''}" if total > 0 else ""), span
    return "", ""


_PLACE = re.compile(r"^[A-Z][A-Za-z.\-']+(?: [A-Z][A-Za-z.\-']+){0,2}$")
_LABEL = re.compile(
    r"^(?:location|address|city|residence)\s*[:\-]\s*(.+)$"
    r"|^(?:based in|located in|living in|based out of)\s+(.+)$", re.I)


def _guess_location(text: str, lines: list[str]) -> tuple[str, bool]:
    """Find the candidate's home location using a gazetteer + shape heuristics.

    Tries, in order: an explicit "Location: …" label, a "City, Region" pair
    where either side is a known place, a bare known city/country line, and a
    full-text "City, Country" fallback. Returns ("", remote_ok) if nothing is
    confident enough — never a job title or company by mistake.
    """
    remote_ok = bool(re.search(r"\bremote\b|open to remote|work from home|anywhere",
                               text, re.I))

    def is_place(token: str) -> bool:
        t = token.strip().lower()
        return (t in vocab.CITIES or t in vocab.COUNTRIES
                or t in vocab.US_STATES or t.replace(".", "") in vocab.COUNTRIES)

    def looks_like_noise(seg: str) -> bool:
        low = seg.lower()
        return ("@" in seg or "http" in low or any(ch.isdigit() for ch in seg)
                or any(tw in low for tw in vocab.TITLE_WORDS) or len(seg) > 42)

    candidates: list[tuple[int, str]] = []  # (priority, text) — higher = better

    def consider(seg: str, base_priority: int) -> None:
        seg = seg.strip(" \t.,|•·–-")
        if not seg or looks_like_noise(seg):
            return
        if "," in seg:
            left, right = (p.strip() for p in seg.split(",", 1))
            if (is_place(left) or is_place(right)) and _PLACE.match(left):
                candidates.append((base_priority + 3, f"{left}, {right}"))
                return
        if is_place(seg) and _PLACE.match(seg):
            candidates.append((base_priority + 1, seg))

    # 1) explicit label anywhere near the top
    for ln in lines[:18]:
        m = _LABEL.match(ln.strip())
        if m:
            consider(m.group(1) or m.group(2), base_priority=10)

    # 2) contact-style header lines, split on common separators
    for ln in lines[:12]:
        for seg in re.split(r"[|•·]|\t|\s{2,}", ln):
            consider(seg, base_priority=5)

    # 3) whole-text "City, Country/State" fallback
    if not candidates:
        for m in re.finditer(r"([A-Z][A-Za-z.\-']+(?: [A-Z][A-Za-z.\-']+)?),\s*"
                             r"([A-Z][A-Za-z.\-' ]+)", text):
            left, right = m.group(1).strip(), m.group(2).strip()
            if is_place(left) or is_place(right):
                consider(f"{left}, {right}", base_priority=2)
                break

    if candidates:
        candidates.sort(key=lambda c: -c[0])
        best = candidates[0][1]
        return (best + (" · open to remote" if remote_ok else ""), remote_ok)

    # infer country from an international dialing code in a phone number
    m = re.search(r"\+(\d{1,3})[\s.\-()]*\d", text)
    if m and (country := _PHONE_CC.get(m.group(1))):
        return (country + (" · open to remote" if remote_ok else ""), remote_ok)

    if remote_ok:
        return ("Remote", True)
    return ("", remote_ok)


_PHONE_CC = {
    "92": "Pakistan", "91": "India", "880": "Bangladesh", "94": "Sri Lanka",
    "234": "Nigeria", "254": "Kenya", "233": "Ghana", "27": "South Africa",
    "20": "Egypt", "44": "United Kingdom", "353": "Ireland", "49": "Germany",
    "33": "France", "34": "Spain", "39": "Italy", "31": "Netherlands",
    "61": "Australia", "64": "New Zealand", "65": "Singapore", "60": "Malaysia",
    "63": "Philippines", "62": "Indonesia", "84": "Vietnam", "66": "Thailand",
    "971": "United Arab Emirates", "966": "Saudi Arabia", "974": "Qatar",
    "55": "Brazil", "52": "Mexico", "54": "Argentina", "57": "Colombia",
}


def _extract_skills(text: str, sections: dict) -> list[Skill]:
    low = text.lower()
    skills_blob = " ".join(sections.get("skills", [])).lower()
    result: list[Skill] = []
    seen: set[str] = set()
    for canon, aliases in vocab.SKILLS.items():
        matched = False
        in_skills_section = False
        occurrences = 0
        for a in aliases:
            pat = a if a.startswith("\\b") or "\\b" in a else re.escape(a)
            hits = re.findall(rf"(?<![\w]){pat}(?![\w])", low)
            if hits:
                matched = True
                occurrences += len(hits)
            if re.search(rf"(?<![\w]){pat}(?![\w])", skills_blob):
                in_skills_section = True
        if matched and canon not in seen:
            seen.add(canon)
            # high confidence if it's in the skills section or mentioned >1x
            conf = "high" if (in_skills_section or occurrences > 1) else "low"
            result.append(Skill(canon, conf))
    # stable order: high-confidence first, then by appearance
    result.sort(key=lambda s: (s.confidence != "high",))
    return result
