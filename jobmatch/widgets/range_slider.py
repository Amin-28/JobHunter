"""Interactive dual-handle range slider (used for the salary filter)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from ..theme import C


class DualRangeSlider(QWidget):
    changed = pyqtSignal(int, int)   # lo, hi (emitted continuously)
    committed = pyqtSignal(int, int)  # on release (good for debounced queries)

    def __init__(self, minimum: int, maximum: int, step: int = 5000, parent=None):
        super().__init__(parent)
        self._min = minimum
        self._max = maximum
        self._step = step
        self._lo = minimum
        self._hi = maximum
        self._r = 8            # handle radius
        self._drag: str | None = None   # 'lo' | 'hi'
        self.setFixedHeight(22)
        self.setMinimumWidth(120)
        self.setMouseTracking(True)

    # ---- values ----
    def values(self) -> tuple[int, int]:
        return self._lo, self._hi

    def set_values(self, lo: int, hi: int) -> None:
        self._lo = max(self._min, min(lo, self._max))
        self._hi = max(self._min, min(hi, self._max))
        if self._lo > self._hi:
            self._lo, self._hi = self._hi, self._lo
        self.update()

    # ---- geometry ----
    def _x(self, value: int) -> float:
        span = max(1, self._max - self._min)
        usable = self.width() - 2 * self._r
        return self._r + (value - self._min) / span * usable

    def _value(self, x: float) -> int:
        usable = max(1, self.width() - 2 * self._r)
        frac = min(1.0, max(0.0, (x - self._r) / usable))
        raw = self._min + frac * (self._max - self._min)
        return int(round(raw / self._step) * self._step)

    # ---- painting ----
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cy = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(C.border_input))
        p.drawRoundedRect(int(self._r), int(cy - 2), int(self.width() - 2 * self._r), 4, 2, 2)
        x_lo, x_hi = self._x(self._lo), self._x(self._hi)
        p.setBrush(QColor(C.accent))
        p.drawRect(int(x_lo), int(cy - 2), int(x_hi - x_lo), 4)
        for x in (x_lo, x_hi):
            p.setBrush(QColor("#FFFFFF"))
            p.setPen(QColor(C.accent))
            p.drawEllipse(int(x - self._r), int(cy - self._r), 2 * self._r, 2 * self._r)
            p.setPen(Qt.PenStyle.NoPen)
        p.end()

    # ---- interaction ----
    def mousePressEvent(self, event):  # noqa: N802
        x = event.position().x()
        self._drag = "lo" if abs(x - self._x(self._lo)) <= abs(x - self._x(self._hi)) else "hi"
        self._apply(x)

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._drag:
            self._apply(event.position().x())
        else:
            near = (abs(event.position().x() - self._x(self._lo)) < self._r + 3 or
                    abs(event.position().x() - self._x(self._hi)) < self._r + 3)
            self.setCursor(Qt.CursorShape.SizeHorCursor if near
                           else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self._drag:
            self._drag = None
            self.committed.emit(self._lo, self._hi)

    def _apply(self, x: float) -> None:
        v = self._value(x)
        if self._drag == "lo":
            self._lo = min(v, self._hi)
        else:
            self._hi = max(v, self._lo)
        self.update()
        self.changed.emit(self._lo, self._hi)
