"""Small chip/pill factory widgets built from the token palette."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ..theme import C, F


def _chip_label(text: str, *, fg: str, bg: str, border: str, radius: int,
                pad_v: int, pad_h: int, px: float, weight: int = 400,
                mono: bool = False, dashed: bool = False) -> QLabel:
    lbl = QLabel(text)
    fam = F.mono if mono else F.sans
    style = (
        f"color:{fg};background:{bg};"
        f"border:1px {'dashed' if dashed else 'solid'} {border};"
        f"border-radius:{radius}px;padding:{pad_v}px {pad_h}px;"
        f"font-family:'{fam}';font-size:{px}px;font-weight:{weight};"
    )
    lbl.setStyleSheet(style)
    return lbl


def salary_chip(text: str, listed: bool = True) -> QLabel:
    return _chip_label(
        text, fg=(C.text_2 if listed else C.text_4), bg=C.bg_fill,
        border=C.bg_fill, radius=3, pad_v=3, pad_h=7, px=11, weight=500, mono=True)


def matched_skill_chip(text: str) -> QLabel:
    return _chip_label(
        text, fg=C.accent_ink, bg=C.accent_bg, border=C.accent_bg,
        radius=3, pad_v=3, pad_h=7, px=11)


def overflow_chip(count: int) -> QLabel:
    return _chip_label(
        f"+{count}", fg=C.text_3, bg=C.bg_fill, border=C.bg_fill,
        radius=3, pad_v=3, pad_h=7, px=11)


def keyword_token(text: str) -> QLabel:
    return _chip_label(
        text, fg=C.accent_ink, bg=C.accent_bg, border=C.accent_bg,
        radius=3, pad_v=2, pad_h=7, px=12)


class KeywordToken(QWidget):
    """Removable keyword chip for the search bar."""

    removed = pyqtSignal(str)

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.text = text
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 4, 2)
        lay.setSpacing(4)
        self.setStyleSheet(
            f"KeywordToken{{background:{C.accent_bg};border:1px solid {C.accent_border};"
            f"border-radius:4px;}}")
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{C.accent_ink};font-size:12px;background:transparent;border:none;")
        lay.addWidget(lbl)
        x = QPushButton("✕")
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setFixedSize(14, 14)
        x.setStyleSheet(
            f"QPushButton{{color:{C.accent};border:none;background:transparent;font-size:9px;}}"
            f"QPushButton:hover{{color:{C.danger};}}")
        x.clicked.connect(lambda: self.removed.emit(self.text))
        lay.addWidget(x)


class SkillChip(QWidget):
    """Removable profile skill chip (normal or low-confidence variant)."""

    removed = pyqtSignal(str)

    def __init__(self, name: str, low: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.name = name
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 5, 9, 5)
        lay.setSpacing(7)

        if low:
            fg, bg, border = C.warn_ink, C.warn_bg, C.warn_border_dashed
        else:
            fg, bg, border = C.accent_ink, C.accent_bg, C.accent_border
        dash = "dashed" if low else "solid"
        self.setStyleSheet(
            f"SkillChip{{background:{bg};border:1px {dash} {border};"
            f"border-radius:14px;}}")

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"color:{fg};font-family:'{F.sans}';font-size:12.5px;background:transparent;border:none;")
        lay.addWidget(name_lbl)

        if low:
            tag = QLabel("low confidence")
            tag.setStyleSheet(
                f"color:#B08C4A;font-size:10.5px;background:transparent;border:none;")
            lay.addWidget(tag)

        x = QPushButton("✕")
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setFixedSize(14, 14)
        x.setStyleSheet(
            f"QPushButton{{color:#7FA8A6;border:none;background:transparent;font-size:10px;}}"
            f"QPushButton:hover{{color:{C.danger};}}")
        x.clicked.connect(lambda: self.removed.emit(self.name))
        lay.addWidget(x)
