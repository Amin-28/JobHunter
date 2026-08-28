"""Left-nav — icon-based workflow rows with live states and a Saved badge."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget)

from .. import icons
from ..theme import C, F

# index -> (icon name, label)
_ITEMS = [
    ("file", "Resume"),
    ("user", "Profile"),
    ("search", "Search"),
    ("bookmark", "Saved"),
]


class NavRow(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, index: int, icon_name: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("NavRow")
        self.index = index
        self._icon = icon_name
        self._enabled = False
        self.setFixedHeight(40)
        self.setProperty("state", "locked")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(0)

        # active indicator bar (left)
        self._bar = QFrame()
        self._bar.setFixedWidth(3)
        self._bar.setStyleSheet("background:transparent;border-radius:2px;")
        lay.addWidget(self._bar)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedWidth(30)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._icon_lbl)

        self._label = QLabel(label)
        self._label.setStyleSheet(
            f"color:{C.text_2};font-size:13px;background:transparent;")
        lay.addWidget(self._label)
        lay.addStretch()

        self._trailing = QLabel()
        self._trailing.setStyleSheet("background:transparent;")
        lay.addWidget(self._trailing)

        self.set_state("locked")

    def set_state(self, state: str) -> None:
        """state: current | done | idle | locked."""
        self._enabled = state != "locked"
        self.setProperty("state", "current" if state == "current"
                         else ("idle" if state in ("idle", "done") else "locked"))
        self.setCursor(Qt.CursorShape.PointingHandCursor if self._enabled
                       else Qt.CursorShape.ArrowCursor)

        if state == "current":
            icon_color, label_color, weight = C.accent, C.accent, "600"
            self._bar.setStyleSheet(
                f"background:{C.accent};border-radius:2px;")
        elif state == "done":
            icon_color, label_color, weight = C.text_2, C.text_2, "500"
            self._bar.setStyleSheet("background:transparent;border-radius:2px;")
        elif state == "idle":
            icon_color, label_color, weight = C.text_3, C.text_2, "500"
            self._bar.setStyleSheet("background:transparent;border-radius:2px;")
        else:  # locked
            icon_color, label_color, weight = C.text_disabled, C.text_disabled, "500"
            self._bar.setStyleSheet("background:transparent;border-radius:2px;")

        self._icon_lbl.setPixmap(icons.pixmap(self._icon, 18, icon_color, 2.0))
        self._label.setStyleSheet(
            f"color:{label_color};font-size:13px;font-weight:{weight};background:transparent;")

        # trailing: done -> check; others cleared (Saved badge set separately)
        if state == "done" and self.index != 3:
            self._trailing.setPixmap(icons.pixmap("check_circle", 15, C.accent, 2.0))
        elif self.index != 3:
            self._trailing.clear()

        self.style().unpolish(self); self.style().polish(self)

    def set_badge(self, count: int) -> None:
        if self.index != 3:
            return
        if count > 0:
            self._trailing.setText(str(count))
            self._trailing.setStyleSheet(
                f"color:{C.accent_ink};background:{C.accent_bg};border-radius:9px;"
                f"padding:1px 8px;font-family:'{F.mono}';font-size:11px;font-weight:600;")
        else:
            self._trailing.setText("0")
            self._trailing.setStyleSheet(
                f"color:{C.text_4};background:{C.bg_fill};border-radius:9px;"
                f"padding:1px 8px;font-family:'{F.mono}';font-size:11px;")

    def mousePressEvent(self, event):  # noqa: N802
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)


class NavStepper(QWidget):
    navigate = pyqtSignal(int)

    LABELS = [lbl for _, lbl in _ITEMS]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(200)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 14)
        lay.setSpacing(4)

        group = QLabel("WORKFLOW")
        group.setObjectName("NavGroupLabel")
        group.setStyleSheet(
            f"color:{C.text_5};font-size:9.5px;font-weight:700;letter-spacing:1.4px;"
            f"padding:2px 8px 10px 8px;background:transparent;")
        lay.addWidget(group)

        self.rows: list[NavRow] = []
        for i, (icon_name, label) in enumerate(_ITEMS):
            row = NavRow(i, icon_name, label)
            row.clicked.connect(self.navigate.emit)
            lay.addWidget(row)
            self.rows.append(row)
        self.rows[3].set_badge(0)

        lay.addStretch()

        # footer — a soft "offline" pill
        footer = QFrame()
        footer.setStyleSheet(
            f"background:{C.bg_panel};border:1px solid {C.border};border-radius:9px;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(10, 8, 10, 8)
        fl.setSpacing(7)
        lock = QLabel()
        lock.setPixmap(icons.pixmap("lock", 13, C.accent, 1.9))
        note = QLabel("Runs offline")
        note.setStyleSheet(
            f"color:{C.text_3};font-size:11px;font-weight:500;background:transparent;")
        fl.addWidget(lock); fl.addWidget(note); fl.addStretch()
        lay.addWidget(footer)
        self._badge_count = 0

    def update_states(self, current_index: int, gates: dict[int, bool]) -> None:
        for i, row in enumerate(self.rows):
            enabled = gates.get(i, True)
            if i == current_index:
                row.set_state("current")
            elif enabled and i < current_index:
                row.set_state("done")
            elif enabled:
                row.set_state("idle")
            else:
                row.set_state("locked")
        # keep the badge count intact after state changes
        self.rows[3].set_badge(self._badge_count)

    def set_saved_count(self, n: int) -> None:
        self._badge_count = n
        self.rows[3].set_badge(n)
