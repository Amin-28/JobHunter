"""In-app Settings — paste API keys without touching the hidden settings file.

Keys are stored via :mod:`config` (settings.json) and picked up immediately, no
restart needed. Fields use password echo so keys stay masked on screen.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget)

from .. import icons
from ..services import config
from ..theme import C, F

# (settings key, label, hint)  — grouped by section
_SECTIONS = [
    ("AI  ·  free", [
        ("groq_key", "Groq API key", "console.groq.com — free, fast"),
        ("gemini_key", "Google Gemini key", "aistudio.google.com — free"),
    ]),
    ("Jobs", [
        ("jooble_key", "Jooble key", "jooble.org/api/about — real Pakistan jobs, free"),
        ("rapidapi_key", "RapidAPI key (JSearch)", "rapidapi.com/…/jsearch — LinkedIn/Indeed jobs via Google, free tier"),
    ]),
    ("Advanced  ·  optional", [
        ("anthropic_api_key", "Anthropic (Claude) key", "console.anthropic.com — paid"),
        ("adzuna_app_id", "Adzuna App ID", "developer.adzuna.com — free"),
        ("adzuna_app_key", "Adzuna App Key", ""),
    ]),
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings — API keys")
        self.setMinimumWidth(460)
        self.setStyleSheet(f"QDialog{{background:{C.bg_app};}}")
        self._fields: dict[str, QLineEdit] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 20)
        root.setSpacing(0)

        head = QHBoxLayout(); head.setSpacing(9)
        icon = QLabel(); icon.setPixmap(icons.pixmap("key", 18, C.accent, 2.0))
        head.addWidget(icon)
        title = QLabel("API keys")
        title.setStyleSheet(f"color:{C.text};font-size:16px;font-weight:600;background:transparent;")
        head.addWidget(title); head.addStretch()
        root.addLayout(head)
        sub = QLabel("Paste any keys you have — everything works without them too. "
                     "Free options are marked.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{C.text_3};font-size:12px;background:transparent;")
        root.addSpacing(6); root.addWidget(sub); root.addSpacing(14)

        for section, rows in _SECTIONS:
            lbl = QLabel(section.upper())
            lbl.setStyleSheet(
                f"color:{C.text_5};font-size:10px;font-weight:600;letter-spacing:1px;"
                f"background:transparent;")
            root.addWidget(lbl); root.addSpacing(8)
            for key, label, hint in rows:
                root.addWidget(self._field(key, label, hint))
                root.addSpacing(10)
            root.addSpacing(6)

        # buttons
        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.setProperty("kind", "secondary")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save"); save.setProperty("kind", "primary")
        save.setStyleSheet(
            f"QPushButton{{background:{C.accent};color:#fff;border:none;border-radius:6px;"
            f"padding:9px 22px;font-size:13px;font-weight:600;}}"
            f"QPushButton:hover{{background:{C.accent_hover};}}")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addSpacing(8); btns.addWidget(save)
        root.addSpacing(8); root.addLayout(btns)

    def _field(self, key: str, label: str, hint: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(4)
        row = QHBoxLayout(); row.setSpacing(6)
        lab = QLabel(label)
        lab.setStyleSheet(f"color:{C.text_2};font-size:12.5px;font-weight:500;background:transparent;")
        row.addWidget(lab)
        if hint:
            h = QLabel("· " + hint)
            h.setStyleSheet(f"color:{C.text_4};font-size:11px;background:transparent;")
            row.addWidget(h)
        row.addStretch()
        v.addLayout(row)
        edit = QLineEdit(config.get(key, "") or "")
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.setPlaceholderText("paste key…")
        edit.setStyleSheet(f"font-family:'{F.mono}';font-size:12px;")
        self._fields[key] = edit
        v.addWidget(edit)
        return w

    def _save(self) -> None:
        for key, edit in self._fields.items():
            config.set(key, edit.text().strip())
        self.accept()
