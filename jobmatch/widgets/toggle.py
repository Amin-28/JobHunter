"""Sliding toggle switch (34x19), animated knob — README 1d 'Remote only'."""
from __future__ import annotations

from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, Qt, pyqtProperty,
                          pyqtSignal)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QAbstractButton

from ..theme import C


class ToggleSwitch(QAbstractButton):
    toggled_on = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(34, 19)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._offset = 17.0 if checked else 2.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.clicked.connect(self._on_click)

    def _on_click(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(17.0 if self.isChecked() else 2.0)
        self._anim.start()
        self.toggled_on.emit(self.isChecked())

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, v: float) -> None:
        self._offset = v
        self.update()

    offset = pyqtProperty(float, fget=get_offset, fset=set_offset)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track = QColor(C.accent if self.isChecked() else C.border_input)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, 34, 19, 10, 10)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(int(self._offset), 2, 15, 15)
        p.end()
