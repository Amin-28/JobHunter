"""Small shared widgets: company logo tile and section labels."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QLabel, QWidget

from ..theme import C, F, company_color, initials


class LogoTile(QWidget):
    """Rounded square with company initials (design fallback for a real logo)."""

    def __init__(self, company: str, size: int = 40, radius: int = 5,
                 font_px: float = 14.0, parent=None) -> None:
        super().__init__(parent)
        self.company = company
        self._size = size
        self._radius = radius
        self._font_px = font_px
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(company_color(self.company)))
        p.drawRoundedRect(0, 0, self._size, self._size, self._radius, self._radius)
        f = QFont(F.sans)
        f.setPixelSize(round(self._font_px))
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, initials(self.company))
        p.end()


def section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        f"color:{C.text_5};font-size:10px;font-weight:600;"
        f"letter-spacing:1px;background:transparent;")
    return lbl


def rule(color: str = C.rule) -> QWidget:
    w = QWidget()
    w.setFixedHeight(1)
    w.setStyleSheet(f"background:{color};")
    return w
