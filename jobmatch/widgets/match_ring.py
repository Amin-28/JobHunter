"""Circular match-score ring, painted with QPainter.

Spec (README 1e): track circle stroke, progress arc rounded-cap rotated -90°,
centered mono score label. Color thresholds:
  >=75 -> accent, 50-74 -> warn, <50 -> muted grey.
"""
from __future__ import annotations

from PyQt6.QtCore import (QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt,
                          pyqtProperty)
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..theme import C, F


def ring_colors(score: int) -> tuple[str, str]:
    """Return (arc_color, text_color) for a score."""
    if score >= 75:
        return C.accent, C.accent_ink
    if score >= 50:
        return C.warn, C.warn_ink
    return C.text_disabled, C.text_2   # muted arc, but a legible number


def _lighten(hex_color: str, amount: float = 0.28) -> str:
    """Blend a hex color toward white for the gradient's bright stop."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02X}{g:02X}{b:02X}"


class MatchRing(QWidget):
    def __init__(self, score: int = 0, diameter: int = 46, stroke: float = 4.5,
                 label_px: float = 12.0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._score = max(0, min(100, score))
        self._d = diameter
        self._stroke = stroke
        self._label_px = label_px
        self.setFixedSize(diameter, diameter)

    def set_score(self, score: int) -> None:
        self._score = max(0, min(100, score))
        self.update()

    # animatable float property (drives the sweep + count-up)
    def _get_score(self) -> float:
        return self._score

    def _set_score(self, v: float) -> None:
        self._score = max(0, min(100, int(round(v))))
        self.update()

    scoreValue = pyqtProperty(float, _get_score, _set_score)

    def animate_to(self, target: int, ms: int = 750) -> None:
        target = max(0, min(100, target))
        self._anim = QPropertyAnimation(self, b"scoreValue", self)
        self._anim.setDuration(ms)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(float(target))
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pad = self._stroke / 2 + 1
        rect = QRectF(pad, pad, self._d - 2 * pad, self._d - 2 * pad)

        # Track
        track = QPen(QColor("#E6EAEE"), self._stroke)
        track.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(track)
        p.drawArc(rect, 0, 360 * 16)

        # Progress arc (start at top = 90°, sweep clockwise = negative) with
        # a subtle gradient so the ring feels alive rather than flat.
        arc_hex, text_hex = ring_colors(self._score)
        grad = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
        grad.setColorAt(0.0, QColor(_lighten(arc_hex)))
        grad.setColorAt(1.0, QColor(arc_hex))
        arc = QPen(QBrush(grad), self._stroke)
        arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc)
        span = int(-360 * 16 * (self._score / 100))
        p.drawArc(rect, 90 * 16, span)

        # Centered label
        f = QFont(F.mono)
        f.setPixelSize(round(self._label_px))
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor(text_hex))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self._score))
        p.end()
