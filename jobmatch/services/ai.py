"""Optional AI layer with a local fallback — prefers FREE providers.

Provider priority (first one with a key wins):
  1. Groq        GROQ_API_KEY        free, fast (Llama 3.3 70B)   console.groq.com
  2. Gemini      GEMINI_API_KEY      free tier                   aistudio.google.com
  3. OpenRouter  OPENROUTER_API_KEY  free models (`:free`)       openrouter.ai
  4. Anthropic   ANTHROPIC_API_KEY   paid (Claude)               console.anthropic.com

With no key at all, every call degrades to a clear rule-based explanation, so
the app is fully functional for free either way.
"""
from __future__ import annotations

import json
import math
import re
import urllib.request

from . import config

# default model per provider (override via settings 'ai_model')
_MODELS = {
    "Groq": "llama-3.3-70b-versatile",
    "Gemini": "gemini-2.0-flash",
    "OpenRouter": "meta-llama/llama-3.3-70b-instruct:free",
    "Claude": "claude-haiku-4-5-20251001",
}


def _provider() -> str | None:
    if config.groq_key():
        return "Groq"
    if config.gemini_key():
        return "Gemini"
    if config.openrouter_key():
        return "OpenRouter"
    if config.anthropic_key():
        return "Claude"
    return None


def available() -> bool:
    return _provider() is not None


def active_provider() -> str:
    return _provider() or "local"


def _model(provider: str) -> str:
    return config.get("ai_model") or _MODELS[provider]


# ------------------------------------------------------------ provider calls
def _post(url: str, body: dict, headers: dict, timeout: int = 30):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _chat(prompt: str, max_tokens: int = 320) -> str | None:
    provider = _provider()
    try:
        if provider == "Groq":
            data = _post(
                "https://api.groq.com/openai/v1/chat/completions",
                {"model": _model(provider), "max_tokens": max_tokens,
                 "messages": [{"role": "user", "content": prompt}]},
                {"Authorization": f"Bearer {config.groq_key()}"})
            return data["choices"][0]["message"]["content"].strip()

        if provider == "OpenRouter":
            data = _post(
                "https://openrouter.ai/api/v1/chat/completions",
                {"model": _model(provider), "max_tokens": max_tokens,
                 "messages": [{"role": "user", "content": prompt}]},
                {"Authorization": f"Bearer {config.openrouter_key()}"})
            return data["choices"][0]["message"]["content"].strip()

        if provider == "Gemini":
            model = _model(provider)
            data = _post(
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={config.gemini_key()}",
                {"contents": [{"parts": [{"text": prompt}]}],
                 "generationConfig": {"maxOutputTokens": max_tokens}},
                {})
            return "".join(
                p.get("text", "")
                for p in data["candidates"][0]["content"]["parts"]).strip()

        if provider == "Claude":
            data = _post(
                "https://api.anthropic.com/v1/messages",
                {"model": _model(provider), "max_tokens": max_tokens,
                 "messages": [{"role": "user", "content": prompt}]},
                {"x-api-key": config.anthropic_key(),
                 "anthropic-version": "2023-06-01"})
            return "".join(b.get("text", "") for b in data.get("content", [])).strip()
    except Exception:
        return None
    return None


# ------------------------------------------------------------ JSON helper
def _extract_json(text: str):
    """Pull the first JSON object/array out of an LLM reply (handles ``` fences)."""
    if not text:
        return None
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


# ------------------------------------------------------------ résumé parsing
def parse_profile(resume_text: str) -> dict | None:
    """Extract a structured profile from résumé text via the LLM (or None)."""
    if not available() or not resume_text.strip():
        return None
    prompt = (
        "Extract a structured candidate profile from this résumé. Return ONLY "
        "valid JSON (no markdown) with exactly these keys:\n"
        '{"name": str, "current_title": str, "target_title": str (the natural '
        'next role to aim for), "years_experience": number, "location": '
        '"City, Country", "remote_ok": bool, "seniority": one of '
        '["Junior","Mid","Senior","Lead"], "domains": [str] (industries/areas), '
        '"education": str, "summary": str (one line), "skills": '
        '[{"name": str, "confidence": "high"|"low"}] }\n'
        "Infer sensibly; use empty string/array if unknown.\n\n"
        f"RÉSUMÉ:\n{resume_text[:6000]}")
    data = _extract_json(_chat(prompt, max_tokens=900))
    return data if isinstance(data, dict) else None


# ------------------------------------------------------------ query expansion
def expand_queries(profile) -> list[str]:
    """Adjacent role titles to broaden the search (falls back to the profile title)."""
    base = [t for t in (profile.target_title, profile.current_title) if t]
    if not available():
        return base[:1] or ["analyst"]
    skills = ", ".join(s.name for s in profile.skills[:8])
    prompt = (
        "List 4 job TITLES this candidate should search for (their current level "
        "plus close adjacent/step-up roles). Return ONLY the titles, one per "
        "line, no numbering.\n"
        f"Current: {profile.current_title}. Target: {profile.target_title}. "
        f"Seniority: {profile.seniority}. Skills: {skills}.")
    out = _chat(prompt, max_tokens=120)
    titles = [ln.strip("-•* \t") for ln in (out or "").splitlines() if ln.strip()]
    titles = [t for t in titles if 2 < len(t) < 48]
    return (titles or base)[:4]


# ------------------------------------------------------------ embeddings
def embeddings_available() -> bool:
    return bool(config.gemini_key())


def embed(texts: list[str]) -> list[list[float]] | None:
    """Batch-embed texts with Gemini's free embedding model (or None)."""
    key = config.gemini_key()
    if not key or not texts:
        return None
    try:
        data = _post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"text-embedding-004:batchEmbedContents?key={key}",
            {"requests": [
                {"model": "models/text-embedding-004",
                 "content": {"parts": [{"text": t[:2000]}]}} for t in texts]},
            {})
        return [e["values"] for e in data.get("embeddings", [])] or None
    except Exception:
        return None


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ------------------------------------------------------------ explanations
def explain_match(profile, job) -> str:
    ai = _chat(_match_prompt(profile, job), max_tokens=260) if available() else None
    return ai or explain_local(profile, job)


def explain_local(profile, job) -> str:
    f = job.factors
    matched = job.matched_skills
    missing = [t for met, t in job.requirements if not met][:4]
    parts: list[str] = [f"Overall match {job.score}/100."]
    if matched:
        parts.append(f"You match {f.skills[0]} of the skills it looks for"
                     f" ({', '.join(matched[:4])}).")
    parts.append(f"Seniority: {f.seniority[0].lower()}"
                 f" ({profile.current_title or 'your title'} vs “{job.title}”).")
    parts.append(f"Location: {f.location[0].lower()} for {job.location}.")
    if f.tooling[1] < 60:
        parts.append(f"Weakest factor is tooling ({f.tooling[0]})"
                     + (f" — the posting wants {', '.join(missing)}." if missing else "."))
    if missing:
        parts.append("To rank higher, add these to your résumé if you have them: "
                     + ", ".join(missing) + ".")
    return " ".join(parts)


def _match_prompt(profile, job) -> str:
    skills = ", ".join(s.name for s in profile.skills[:12])
    missing = [t for met, t in job.requirements if not met]
    f = job.factors
    return (
        "You are a concise career coach. In 2-3 short sentences, explain to the "
        "candidate why this job scored the way it did and one concrete way to "
        "improve their fit. Be specific and encouraging, no preamble.\n\n"
        f"Candidate: {profile.current_title}, {profile.years} experience, "
        f"based {profile.location}. Skills: {skills}.\n"
        f"Job: {job.title} at {job.company} ({job.location}, {job.type}).\n"
        f"Computed match {job.score}/100 — skills {f.skills[0]}, seniority "
        f"{f.seniority[0]}, location {f.location[0]}, tooling {f.tooling[0]}.\n"
        f"Skills the posting lists that the candidate lacks: "
        f"{', '.join(missing) or 'none'}."
    )


# ------------------------------------------------------------ keyword research
def suggest_keywords(profile) -> list[str]:
    from .job_search import build_keywords
    if not available():
        return build_keywords(profile)
    skills = ", ".join(s.name for s in profile.skills[:12])
    loc = (profile.location or "").split(" · ")[0].strip()
    prompt = (
        "Suggest 6 concise job-search keywords/phrases (each 1-3 words) to find "
        "roles for this person across job boards"
        + (f", suitable for the {loc} job market" if loc else "") + ". Return "
        "ONLY the keywords, one per line, no numbering.\n"
        f"Title: {profile.current_title} / target {profile.target_title}. "
        f"Skills: {skills}."
        + (f" Location: {loc}." if loc else ""))
    out = _chat(prompt, max_tokens=120)
    if not out:
        return build_keywords(profile)
    kws = [ln.strip("-•* \t") for ln in out.splitlines() if ln.strip()]
    return [k for k in kws if k][:6] or build_keywords(profile)
