# JobMatch AI — web version (machine-free)

Same engine as the desktop app, exposed over HTTP so it runs on **any device
with a browser** — laptop, another PC, your phone. **API keys live on the server
(once)**, so no client machine needs them, and performance is identical
everywhere (the heavy work is the cloud job APIs + AI, not your machine).

```
web/
  backend/app.py   FastAPI — thin layer over jobmatch.services (parse/search/explain/keywords)
  frontend/        the browser UI (index.html + style.css + app.js), stateless
```

The browser holds your profile + saved jobs (localStorage); nothing personal is
stored on the server. Fonts load from Google Fonts, so no bundling needed.

## Run locally

```bash
pip install -r web/backend/requirements.txt
python -m uvicorn web.backend.app:app --port 8000
```
Open **http://localhost:8000**.  (Use `python -m uvicorn` — the bare `uvicorn`
command may not be on your PATH.)

## Add API keys (server-side)
Set them as environment variables before starting (or in the same
`settings.json` the desktop app uses — env wins):

| Variable | Enables |
|---|---|
| `GROQ_API_KEY` | free AI: résumé parsing, keyword research, explanations |
| `GEMINI_API_KEY` | free AI + semantic matching (embeddings) |
| `JOOBLE_KEY` | real Pakistan / local jobs |
| `RAPIDAPI_KEY` | JSearch — LinkedIn/Indeed/Glassdoor jobs via Google for Jobs (free tier) |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Adzuna listings |

PowerShell example:
```powershell
$env:GROQ_API_KEY="gsk_..."; $env:JOOBLE_KEY="..."; uvicorn web.backend.app:app --port 8000
```

## Deploy so it's reachable anywhere (free)

**Render (render.com):**
1. Push this repo to GitHub.
2. Render → New → Blueprint → pick the repo (it reads `render.yaml`).
3. Add your API keys under the service's **Environment** tab.
4. Deploy → you get a public `https://…onrender.com` URL that works on any device.

Any host that runs a `Procfile` works too (Railway, Fly.io): build with
`pip install -r web/backend/requirements.txt`, start with the `Procfile` command.

## API
`POST /api/parse` (multipart file) · `POST /api/search` · `POST /api/explain` ·
`POST /api/keywords` · `GET /api/status`. All take/return JSON; the profile is
passed from the browser each call (stateless server).
