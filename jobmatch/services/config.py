"""User configuration + data directory.

Settings live in a JSON file under the OS's per-user app-data dir. Secrets
(Adzuna, Anthropic keys) may also come from environment variables, which take
precedence so nothing sensitive has to be written to disk.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData/Roaming")
    elif "darwin" in os.sys.platform:
        base = str(Path.home() / "Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    d = Path(base) / "JobMatchAI"
    d.mkdir(parents=True, exist_ok=True)
    return d


_SETTINGS_FILE = data_dir() / "settings.json"
_cache: dict | None = None
_mtime: float = -1.0


def _load() -> dict:
    """Return settings, reloading if the file changed on disk (so a manual edit
    or another process's save is picked up without a restart)."""
    global _cache, _mtime
    try:
        m = _SETTINGS_FILE.stat().st_mtime
    except OSError:
        m = 0.0
    if _cache is None or m != _mtime:
        try:
            _cache = json.loads(_SETTINGS_FILE.read_text("utf-8"))
        except (OSError, ValueError):
            _cache = {}
        _mtime = m
    return _cache


def get(key: str, default=None):
    return _load().get(key, default)


def set(key: str, value) -> None:  # noqa: A001 - deliberate simple API
    """Merge one key onto the CURRENT on-disk settings and save.

    Always re-reads the file first (never trusts a possibly-stale cache), so a
    process that loaded an empty file can't clobber keys another process wrote.
    """
    global _cache, _mtime
    try:
        disk = json.loads(_SETTINGS_FILE.read_text("utf-8"))
    except (OSError, ValueError):
        disk = {}
    disk[key] = value
    try:
        _SETTINGS_FILE.write_text(json.dumps(disk, indent=2), "utf-8")
        _mtime = _SETTINGS_FILE.stat().st_mtime
    except OSError:
        pass
    _cache = disk


# ---- secrets (env var wins over settings file) ----
# NOTE: the settings.json field name (file_key) must match what the in-app
# Settings dialog writes — it is NOT always the lowercased env var name.
def secret(env_name: str, file_key: str) -> str | None:
    return os.environ.get(env_name) or get(file_key)


def adzuna_keys() -> tuple[str, str] | None:
    app_id = secret("ADZUNA_APP_ID", "adzuna_app_id")
    app_key = secret("ADZUNA_APP_KEY", "adzuna_app_key")
    return (app_id, app_key) if app_id and app_key else None


def anthropic_key() -> str | None:
    return secret("ANTHROPIC_API_KEY", "anthropic_api_key")


def groq_key() -> str | None:
    return secret("GROQ_API_KEY", "groq_key")


def gemini_key() -> str | None:
    return secret("GEMINI_API_KEY", "gemini_key")


def openrouter_key() -> str | None:
    return secret("OPENROUTER_API_KEY", "openrouter_key")


def jooble_key() -> str | None:
    return secret("JOOBLE_KEY", "jooble_key")


def rapidapi_key() -> str | None:
    return secret("RAPIDAPI_KEY", "rapidapi_key")


# ---- which sources are enabled ----
_FREE = ["Remotive", "Arbeitnow", "Jobicy", "RemoteOK"]


def enabled_sources() -> list[str]:
    saved = get("enabled_sources")
    names = saved if isinstance(saved, list) and saved else list(_FREE)
    if adzuna_keys() and "Adzuna" not in names:
        names = names + ["Adzuna"]
    if jooble_key() and "Jooble" not in names:
        names = names + ["Jooble"]     # covers Pakistan + most countries
    if rapidapi_key():                 # both use the RapidAPI key; whichever the
        for s in ("JSearch", "LinkedIn"):   # user is subscribed to will respond
            if s not in names:
                names = names + [s]
    return names


def theme() -> str:
    return get("theme", "light")


def set_theme(name: str) -> None:
    set("theme", name)
