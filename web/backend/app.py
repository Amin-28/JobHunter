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

from fastapi import Body, FastAPI, File, UploadFile          # noqa: E402
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
