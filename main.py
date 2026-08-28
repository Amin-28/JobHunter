"""JobMatch AI — entry point.

Run with:  python main.py
"""
from __future__ import annotations

import sys

from jobmatch.app import run

if __name__ == "__main__":
    sys.exit(run())
