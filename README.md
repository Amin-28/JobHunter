# JobMatch AI

A native desktop application (Python 3.11+ / **PyQt6**) that matches jobs to your
résumé. Drop in a PDF/DOCX, it parses an editable profile, searches job sources,
and ranks results with a **match score**. Built to the design handoff in
[`design_handoff_jobmatch_ai/`](design_handoff_jobmatch_ai).

## Run

```bash
pip install -r requirements.txt
python main.py
```

> Tested on Python 3.14 + PyQt6 6.11. Requires **PyQt6-Qt6** (the Qt runtime,
> which ships the SVG module used for icons).

## The flow

`Resume upload → parse → Profile → Search + filters → Job detail → Saved`

| Screen | Module | Handoff |
|---|---|---|
| Résumé upload (empty + processing) | `jobmatch/screens/upload.py` | 1a · 1b |
| Profile summary (editable) | `jobmatch/screens/profile.py` | 1c |
| Search, filters, result cards | `jobmatch/screens/search.py` | 1d · 1e |
| Job detail + apply channel | `jobmatch/screens/search.py`, `apply_bar.py` | 1f · 1g |
| Saved jobs | `jobmatch/screens/saved.py` | 1h |

## Architecture

```
main.py                 entry point
jobmatch/
  app.py                QApplication bootstrap (fonts + theme)
  theme.py              design tokens (colors/type/geometry) + QSS
  icons.py              inline SVG line-icon set → QPixmap/QIcon
  models.py             Profile, Job, SavedJob, ... dataclasses
  store.py              AppStore(QObject) — single state store, signal-driven
  workers.py            off-GUI-thread parse + search workers (QRunnable)
  services/
    resume_parser.py    real PDF/DOCX text extraction + profile heuristics
    job_search.py       aggregator orchestrator (scores each RawJob)
    sources/            one adapter per job board (parallel, deduped)
      remotive / arbeitnow / jobicy / remoteok / adzuna
    scoring.py          match score + factor breakdown (profile vs job)
    filtering.py        client-side filters incl. region-eligibility
    ai.py               optional Claude layer (why-score, keyword research)
    store_db.py         SQLite persistence (saved jobs, profile, query)
    config.py           settings file + API keys + source toggles + theme
    vocab.py            skills / tooling / seniority / gazetteer
  sample_data.py        cached demo jobs (offline fallback only)
  main_window.py        frameless shell: title bar, nav stepper, status bar
  widgets/
    nav.py              left-nav workflow stepper (future/done/current)
    match_ring.py       QPainter circular score ring
    toggle.py           animated switch
    job_card.py         results card (hover/selected/saved states)
    chips.py, common.py, flow_layout.py
  screens/              the five workflow pages
```

**State** lives in one `AppStore`; every screen reads it and reacts to its
signals, so bookmarking a job anywhere updates the results list, the detail
view, and the nav count at once. **Parsing and searching run off the GUI
thread** via `QThreadPool` workers that emit progress/finished signals.

## What's real

- **Résumé parsing** (`services/resume_parser.py`): reads real **PDF** (`pypdf`)
  and **DOCX** (stdlib `zipfile` + XML) on-device. Extracts name, title, years +
  span, location (gazetteer-backed) and skills with a per-skill confidence flag.
- **Multi-source job search** (`services/sources/`): aggregates **Remotive,
  Arbeitnow, Jobicy and RemoteOK** (all free, no key) in parallel, de-duplicates,
  and **scores every job against your résumé** (Skills / Seniority / Location /
  Tooling + overall 0–100). Add a free **Adzuna** key for real location-based
  (Indeed-style) listings. All sources failing → cached sample jobs, status
  *"Offline — showing cached results."*
- **Filters that work** (`services/filtering.py`): location (by *region
  eligibility* — a Karachi candidate keeps APAC/Worldwide roles, drops US-only),
  remote-only, job type, experience level, date; debounced, with empty state +
  Reset.
- **Persistence** (`services/store_db.py`): saved jobs, the parsed profile, the
  last query and the theme persist to SQLite and restore on launch.
- **Dark mode**: light/dark toggle in the title bar (`Ctrl+D`), remembered.
- **AI layer** (`services/ai.py`, optional): "Why this score?" in the detail
  pane and "AI research" in the toolbar. Both work locally with no key; with an
  `ANTHROPIC_API_KEY` they upgrade to **Claude** for richer explanations and
  smarter keyword research.
- Plus nav gating, drop validation, error states, keyboard shortcuts, match-ring
  math, apply-channel restyling, optimistic save/bookmark.

### Smart features (with a free AI key)
- **AI résumé parsing** — a Groq/Gemini pass extracts a richer profile (target
  role, seniority, industry domains, one-line summary, curated skills); shown on
  the Profile screen. Falls back to the on-device heuristic parser with no key.
- **AI query expansion** — searches your role *plus* adjacent/step-up titles in
  parallel and merges them, for much better recall.
- **Semantic matching** *(needs a Gemini key)* — embeds your résumé and each job
  (Gemini's free `text-embedding-004`) and blends similarity into the match score
  (55% rule engine + 45% semantic), so ranking reflects meaning, not keywords.

## Configuration (optional keys)

Set as environment variables, or in the settings file at
`%APPDATA%/JobMatchAI/settings.json` (created on first run):

| Key | Enables |
|---|---|
| `GROQ_API_KEY` | **AI explanations + keyword research — FREE**, fast (Llama 3.3). Free key at console.groq.com |
| `GEMINI_API_KEY` | Same, via Google Gemini — **FREE** tier. Key at aistudio.google.com |
| `OPENROUTER_API_KEY` | Same, via OpenRouter free models. Key at openrouter.ai |
| `ANTHROPIC_API_KEY` | Same, via Claude — **paid** (pay-as-you-go) |
| `JOOBLE_KEY` | **Jooble source — real Pakistan (and ~70-country) local listings.** Free at jooble.org/api/about |
| `RAPIDAPI_KEY` | **JSearch — LinkedIn / Indeed / Glassdoor jobs via Google for Jobs** (ToS-compliant, real location search). Free tier at rapidapi.com |
| `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | Adzuna source (Indeed-style listings, no PK) — free at developer.adzuna.com |

The AI layer picks the first provider it finds a key for, in the order above
(free providers first). No key → clear rule-based explanations, fully working.

**Easiest way to add keys:** click the **⚙ gear** in the title bar → paste into
the **Settings** dialog → Save. Keys apply immediately (no restart, no editing
the hidden settings file). Salaries display in each job's **local currency**
(PKR, USD, EUR, GBP, INR…), inferred from the listing's country.

Env vars win over the settings file, so nothing sensitive has to be written to disk.
Your résumé location drives these location-aware sources — e.g. a Karachi résumé +
`JOOBLE_KEY` returns Karachi/Lahore/Islamabad jobs.

## Not built (by design)

- **LinkedIn / Indeed direct scraping** — LinkedIn has no public jobs API and
  Indeed retired theirs; scraping either violates their ToS and is quickly
  blocked. Broad coverage comes from the aggregator; **Adzuna** (global) and
  **Jooble** (incl. Pakistan) are the legitimate keyed routes to local listings.

## Fonts

**IBM Plex Sans / IBM Plex Mono** ship bundled in `jobmatch/assets/fonts/`
(OFL, from Google Fonts — `OFL.txt` included) and load automatically via
`theme.load_fonts()`. Sans is the variable font (all weights in one file);
Mono ships Regular/Medium/SemiBold. If the folder is ever removed, the app
falls back to the platform UI font (Segoe UI on Windows) and a monospace family.
