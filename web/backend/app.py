"""JobMatch AI — web backend (FastAPI).

Thin HTTP layer over the exact same engine the desktop app uses
(``jobmatch.services``). It is stateless: the browser holds the profile and
saved jobs (localStorage) and sends the profile with each request. API keys live
here on the server (environment variables), so no client machine needs them —
that is what makes the app "machine-free".

Run locally:   uvicorn web.backend.app:app --reload --port 8000
Then open:     http://localhost:8000
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# make the `jobmatch` package importable no matter where uvicorn is launched
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import Body, FastAPI, File, Request, UploadFile  # noqa: E402
from fastapi.responses import JSONResponse                    # noqa: E402
from fastapi.staticfiles import StaticFiles                   # noqa: E402

from jobmatch.services import ai, config, job_search          # noqa: E402
from jobmatch.services.job_search import build_keywords       # noqa: E402
from jobmatch.services.resume_parser import ParseError, parse_resume  # noqa: E402
from jobmatch.services.store_db import (_profile_from_dict,   # noqa: E402
                                        _profile_to_dict, job_from_dict,
                                        job_to_dict)

app = FastAPI(title="JobMatch AI")
_FRONTEND = _ROOT / "web" / "frontend"


@app.get("/api/status")
def status() -> dict:
    return {"sources": config.enabled_sources(), "ai": ai.active_provider()}


# fields the in-app Settings panel may set (matches the desktop dialog)
_SETTING_KEYS = ["groq_key", "gemini_key", "jooble_key", "rapidapi_key",
                 "anthropic_api_key", "adzuna_app_id", "adzuna_app_key"]


def _is_local(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    return host in ("127.0.0.1", "::1", "localhost", "testclient")


@app.get("/api/settings")
def get_settings(request: Request) -> dict:
    # never return key VALUES — only whether each is set, plus live status
    return {
        "local": _is_local(request),
        "configured": {k: bool(config.get(k, "")) for k in _SETTING_KEYS},
        "sources": config.enabled_sources(),
        "ai": ai.active_provider(),
    }


@app.post("/api/settings")
def save_settings(request: Request, payload: dict = Body(...)) -> JSONResponse:
    if not _is_local(request):
        return JSONResponse(
            {"error": "Settings can only be changed from the local machine. "
                      "On a hosted server, set keys as environment variables."},
            status_code=403)
    for k in _SETTING_KEYS:
        if k in payload and isinstance(payload[k], str):
            config.set(k, payload[k].strip())
    return JSONResponse({
        "ok": True, "sources": config.enabled_sources(), "ai": ai.active_provider(),
        "configured": {k: bool(config.get(k, "")) for k in _SETTING_KEYS},
    })


@app.post("/api/parse")
def parse(file: UploadFile = File(...)) -> JSONResponse:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".pdf", ".docx"):
        return JSONResponse({"error": "Only PDF or DOCX files, please."}, status_code=400)
    data = file.file.read()
    if len(data) > 10 * 1024 * 1024:
        return JSONResponse({"error": "That file is over 10 MB."}, status_code=400)
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        tmp.write(data)
        tmp.close()
        profile = parse_resume(tmp.name)
    except ParseError as e:
        return JSONResponse({"error": str(e)}, status_code=422)
    except Exception:
        return JSONResponse({"error": "We couldn't read that file."}, status_code=422)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return JSONResponse({
        "profile": _profile_to_dict(profile),
        "keywords": build_keywords(profile),
        "ai": ai.active_provider(),
    })


@app.post("/api/test-sources")
def test_sources(payload: dict = Body(default={})) -> JSONResponse:
    """Ping every registered source and report jobs / no-key / error, per source."""
    import time
    from jobmatch.services.sources.base import SOURCES, source_names
    source_names()   # ensure adapters registered
    loc = (payload or {}).get("location") or "Karachi, Pakistan"
    kws = (payload or {}).get("keywords") or ["data analyst", "developer"]
    enabled = set(config.enabled_sources())
    results = []
    for name, fn in SOURCES.items():
        t = time.time()
        try:
            jobs = fn(kws, loc, 5)
            results.append({"name": name, "status": "ok", "count": len(jobs),
                            "ms": int((time.time() - t) * 1000),
                            "enabled": name in enabled})
        except Exception as e:
            msg = f"{type(e).__name__}: {str(e)[:140]}"
            no_key = "not configured" in str(e).lower() or "key" in str(e).lower()
            results.append({"name": name, "status": "no_key" if no_key else "error",
                            "error": None if no_key else msg, "enabled": name in enabled})
    return JSONResponse({"results": results, "ai": ai.active_provider()})


@app.post("/api/search")
def search(payload: dict = Body(...)) -> JSONResponse:
    profile = _profile_from_dict(payload.get("profile") or {})
    keywords = payload.get("keywords") or None
    location = payload.get("location", "")
    try:
        jobs, ok, failed = job_search.search(profile, keywords, location)
        offline = False
    except job_search.Offline:
        jobs, ok, failed, offline = [], [], [], True
    return JSONResponse({
        "jobs": [job_to_dict(j) for j in jobs],
        "ok": ok, "failed": failed, "offline": offline,
        "ai": ai.active_provider(),
    })


@app.post("/api/explain")
def explain(payload: dict = Body(...)) -> JSONResponse:
    profile = _profile_from_dict(payload.get("profile") or {})
    job = job_from_dict(payload.get("job") or {})
    return JSONResponse({
        "text": ai.explain_match(profile, job),
        "provider": ai.active_provider(),
    })


@app.post("/api/keywords")
def keywords(payload: dict = Body(...)) -> JSONResponse:
    profile = _profile_from_dict(payload.get("profile") or {})
    return JSONResponse({
        "keywords": ai.suggest_keywords(profile),
        "provider": ai.active_provider(),
    })


# serve the frontend (must be mounted last so /api/* wins)
if _FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")
