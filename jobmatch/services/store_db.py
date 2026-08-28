"""SQLite persistence — saved jobs, the parsed profile, and the last query.

Everything lives in one local file under the app-data dir, so a saved list and
your profile survive between launches (README "State Management"). All reads are
defensive: a missing/corrupt DB just yields empty state.
"""
from __future__ import annotations

import contextlib
import json
import sqlite3
from typing import Optional

from ..models import (Apply, Factors, Job, Profile, SavedJob, Skill)
from . import config

_DB = config.data_dir() / "jobmatch.db"


@contextlib.contextmanager
def _conn():
    """Open a connection, ensure schema, commit on success, always close.

    (sqlite3's own context manager commits but never closes — leaking the file
    handle and locking the DB on Windows. This closes it explicitly.)
    """
    c = sqlite3.connect(_DB, timeout=5)
    try:
        c.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS saved ("
                  "id TEXT PRIMARY KEY, pos INTEGER, data TEXT)")
        yield c
        c.commit()
    finally:
        c.close()


# --------------------------------------------------------- (de)serialize
def job_to_dict(j: Job) -> dict:
    return {
        "id": j.id, "title": j.title, "company": j.company,
        "location": j.location, "mode": j.mode, "type": j.type,
        "salary_min": j.salary_min, "salary_max": j.salary_max,
        "score": j.score,
        "factors": {"skills": list(j.factors.skills), "seniority": list(j.factors.seniority),
                    "location": list(j.factors.location), "tooling": list(j.factors.tooling)},
        "posted": j.posted, "posted_days": j.posted_days,
        "apply": {"type": j.apply.type, "value": j.apply.value},
        "description": j.description,
        "requirements": [[bool(m), t] for m, t in j.requirements],
        "benefits": j.benefits, "matched_skills": list(j.matched_skills),
        "extra_skill_count": j.extra_skill_count, "source": j.source,
        "currency": j.currency,
    }


def job_from_dict(d: dict) -> Job:
    f = d.get("factors", {})
    return Job(
        id=d["id"], title=d["title"], company=d["company"], location=d["location"],
        mode=d["mode"], type=d["type"], salary_min=d.get("salary_min"),
        salary_max=d.get("salary_max"), score=d.get("score", 0),
        factors=Factors(tuple(f.get("skills", ("", 0))), tuple(f.get("seniority", ("", 0))),
                        tuple(f.get("location", ("", 0))), tuple(f.get("tooling", ("", 0)))),
        posted=d.get("posted", ""), posted_days=d.get("posted_days", 999),
        apply=Apply(d.get("apply", {}).get("type", "none"), d.get("apply", {}).get("value", "")),
        description=d.get("description", ""),
        requirements=[(bool(m), t) for m, t in d.get("requirements", [])],
        benefits=d.get("benefits", ""), matched_skills=d.get("matched_skills", []),
        extra_skill_count=d.get("extra_skill_count", 0), source=d.get("source", ""),
        currency=d.get("currency", "USD"),
    )


def _profile_to_dict(p: Profile) -> dict:
    return {**p.__dict__, "skills": [{"name": s.name, "confidence": s.confidence}
                                     for s in p.skills]}


def _profile_from_dict(d: dict) -> Profile:
    import dataclasses
    valid = {f.name for f in dataclasses.fields(Profile)}
    kw = {k: v for k, v in d.items() if k in valid}
    kw["skills"] = [Skill(s["name"], s.get("confidence", "high"))
                    for s in d.get("skills", [])]
    return Profile(**kw)


# --------------------------------------------------------------- kv
def _kv_get(key: str):
    try:
        with _conn() as c:
            row = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None
    except (sqlite3.Error, ValueError):
        return None


def _kv_set(key: str, value) -> None:
    try:
        with _conn() as c:
            c.execute("INSERT INTO kv(key,value) VALUES(?,?) "
                      "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (key, json.dumps(value)))
    except (sqlite3.Error, TypeError):
        pass


# --------------------------------------------------------- public API
def load_profile() -> Optional[Profile]:
    d = _kv_get("profile")
    try:
        return _profile_from_dict(d) if d else None
    except (TypeError, KeyError):
        return None


def save_profile(p: Profile | None) -> None:
    if p is not None:
        _kv_set("profile", _profile_to_dict(p))


def load_query() -> Optional[dict]:
    d = _kv_get("query")
    if not d:
        return None
    d["job_types"] = set(d.get("job_types", []))
    d["levels"] = set(d.get("levels", []))
    return d


def save_query(q: dict) -> None:
    out = dict(q)
    out["job_types"] = sorted(q.get("job_types", set()))
    out["levels"] = sorted(q.get("levels", set()))
    _kv_set("query", out)


def load_saved() -> list[SavedJob]:
    try:
        with _conn() as c:
            rows = c.execute("SELECT data FROM saved ORDER BY pos").fetchall()
    except sqlite3.Error:
        return []
    out: list[SavedJob] = []
    for (data,) in rows:
        try:
            d = json.loads(data)
            out.append(SavedJob(
                job=job_from_dict(d["job"]), saved_at=d.get("saved_at", ""),
                applied_at=d.get("applied_at"), deadline=d.get("deadline"),
                expired=d.get("expired", False), channel_note=d.get("channel_note", "")))
        except (ValueError, KeyError):
            continue
    return out


def save_saved(saved: list[SavedJob]) -> None:
    try:
        with _conn() as c:
            c.execute("DELETE FROM saved")
            for i, s in enumerate(saved):
                payload = {
                    "job": job_to_dict(s.job), "saved_at": s.saved_at,
                    "applied_at": s.applied_at, "deadline": s.deadline,
                    "expired": s.expired, "channel_note": s.channel_note,
                }
                c.execute("INSERT INTO saved(id,pos,data) VALUES(?,?,?)",
                          (s.job.id, i, json.dumps(payload)))
    except (sqlite3.Error, TypeError):
        pass
