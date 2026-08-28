"""Application bootstrap: build QApplication, load fonts/theme, show window."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow
from .services import config
from .store import AppStore
from .theme import apply_theme, load_fonts, stylesheet


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("JobMatch AI")
    load_fonts()
    apply_theme(config.theme())      # restore the last light/dark choice
    app.setStyleSheet(stylesheet())

    store = AppStore()
    window = MainWindow(store)
    window.show()
    return app.exec()
