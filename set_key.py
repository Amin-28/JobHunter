"""Save an API key to settings.json and test the matching job source live.

Usage (from F:\\Job Hunter):
    python set_key.py jooble   <JOOBLE_KEY>   ["Karachi, Pakistan"]
    python set_key.py rapidapi <RAPIDAPI_KEY> ["Karachi, Pakistan"]
    python set_key.py groq     <GROQ_KEY>
    python set_key.py gemini   <GEMINI_KEY>

It merges the key into settings.json (so the app uses it too), confirms it
persisted, then — for a job source — makes a real request and prints the jobs
it got back, or the exact error.
"""
import json
import sys

from jobmatch.services import config

# arg name -> (settings field, source-registry name or None for AI keys)
FIELDS = {
    "jooble": ("jooble_key", "Jooble"),
    "rapidapi": ("rapidapi_key", "LinkedIn"),   # LinkedIn Job Search API
    "groq": ("groq_key", None),
    "gemini": ("gemini_key", None),
}

if len(sys.argv) < 3 or sys.argv[1] not in FIELDS:
    print("Usage: python set_key.py <jooble|rapidapi|groq|gemini> <KEY> [location]")
    print('Example: python set_key.py jooble your-jooble-key "Karachi, Pakistan"')
    sys.exit(1)

which = sys.argv[1]
key = sys.argv[2].strip()
location = sys.argv[3] if len(sys.argv) > 3 else "Karachi, Pakistan"
field, source = FIELDS[which]

config.set(field, key)
disk = json.loads(config._SETTINGS_FILE.read_text("utf-8"))
ok = bool(disk.get(field, "").strip())
print(f"[1] Saved {field} to {config._SETTINGS_FILE}: {'YES' if ok else 'FAILED TO WRITE'}")
print(f"[2] Enabled job sources now: {config.enabled_sources()}")

if source is None:
    print(f"[3] {which} is an AI key — saved. (No job-search test.)")
    sys.exit(0)

from jobmatch.services.sources.base import SOURCES, source_names  # noqa: E402
source_names()
print(f"[3] Calling {source} live for '{location}' ...")
try:
    jobs = SOURCES[source](["data analyst", "developer"], location, 10)
    print(f"[4] {source} returned {len(jobs)} jobs:")
    for j in jobs:
        print(f"      [{j.source}] {j.title}  |  {j.location}  |  {j.salary_label}")
    if jobs:
        print(f"\nSUCCESS — {source} works and the key is saved. The app will use it now.")
    else:
        print("    0 jobs — try a bigger city (e.g. just \"Pakistan\") or simpler keywords.")
except Exception as e:  # noqa: BLE001
    print(f"[4] {source} FAILED: {type(e).__name__}: {e}")
    print("    Paste this whole output to me and I'll tell you the exact next step.")
