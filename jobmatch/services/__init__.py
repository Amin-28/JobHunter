"""Real backend services: résumé parsing, job search, and match scoring.

These replace the timed stubs that used to live in ``workers.py``. Each is a
plain, testable function; the ``QRunnable`` workers call them off the GUI thread
and re-emit their results through the same Qt signal contract the screens
already listen to.
"""
