"""Results job card (README 1e) with default / hover / selected / saved states."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                             QLabel, QPushButton, QVBoxLayout, QWidget)

from .. import icons
from ..models import Job
from ..theme import C, F
from .chips import matched_skill_chip, overflow_chip, salary_chip
from .common import LogoTile
from .flow_layout import FlowLayout
from .match_ring import MatchRing


class JobCard(QFrame):
    clicked = pyqtSignal(str)          # job id (open detail)
    save_toggled = pyqtSignal(str)     # job id

    def __init__(self, job: Job, saved: bool = False, selected: bool = False,
                 viewed: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.job = job
        self._saved = saved
        self._selected = selected
        self.setObjectName("JobCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMaximumWidth(900)

        root = QHBoxLayout(self)
        root.setContentsMargins(17, 15, 17, 15)
        root.setSpacing(14)

        root.addWidget(LogoTile(job.company, size=40, radius=5, font_px=14),
                       alignment=Qt.AlignmentFlag.AlignTop)

        # ---- center column ----
        center = QVBoxLayout()
        center.setSpacing(0)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title = QLabel(job.title)
        title.setStyleSheet(
            f"color:{C.text};font-size:14.5px;font-weight:600;background:transparent;")
        title_row.addWidget(title)
        self._bookmark = QLabel()
        self._bookmark.setPixmap(
            icons.pixmap("bookmark_filled", 13, C.accent, 2.0))
        self._bookmark.setVisible(saved)
        title_row.addWidget(self._bookmark)
        title_row.addStretch()
        center.addLayout(title_row)

        meta_tail = " · viewed yesterday" if viewed else ""
        meta = QLabel(f"{job.company} · {job.location} ({job.mode}) · {job.type}{meta_tail}")
        meta.setStyleSheet(
            f"color:{C.text_3};font-size:12.5px;background:transparent;margin-top:4px;")
        center.addWidget(meta)

        # tag row
        tag_host = QWidget()
        tags = FlowLayout(tag_host, hspacing=7, vspacing=7)
        tags.addWidget(salary_chip(job.salary_label, listed=job.salary_min is not None))
        for sk in job.matched_skills[:3]:
            tags.addWidget(matched_skill_chip(sk))
        if job.extra_skill_count:
            tags.addWidget(overflow_chip(job.extra_skill_count))
        tag_host.setStyleSheet("margin-top:9px;")
        center.addWidget(tag_host)

        # hover-only action row
        self._actions = QWidget()
        act = QHBoxLayout(self._actions)
        act.setContentsMargins(0, 11, 0, 0)
        act.setSpacing(8)
        view_btn = QPushButton("View details")
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.setStyleSheet(
            f"QPushButton{{color:{C.accent};border:1px solid {C.accent};"
            f"border-radius:4px;padding:5px 12px;font-size:12px;font-weight:600;"
            f"background:transparent;}}"
            f"QPushButton:hover{{background:{C.accent_bg};}}")
        view_btn.clicked.connect(lambda: self.clicked.emit(job.id))
        self._save_btn = QPushButton()
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setStyleSheet(
            f"QPushButton{{color:{C.text_2};border:1px solid {C.border_button};"
            f"border-radius:4px;padding:5px 12px;font-size:12px;background:transparent;}}"
            f"QPushButton:hover{{border-color:{C.text_disabled};}}")
        self._save_btn.clicked.connect(lambda: self.save_toggled.emit(job.id))
        act.addWidget(view_btn)
        act.addWidget(self._save_btn)
        act.addStretch()
        self._actions.setVisible(False)
        center.addWidget(self._actions)

        root.addLayout(center, 1)

        # ---- right column ----
        right = QVBoxLayout()
        right.setSpacing(10)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        ring = MatchRing(job.score, diameter=46, stroke=4.5, label_px=12)
        right.addWidget(ring, alignment=Qt.AlignmentFlag.AlignRight)
        posted = QLabel(job.posted)
        posted.setStyleSheet(f"color:{C.text_4};font-size:11px;background:transparent;")
        right.addWidget(posted, alignment=Qt.AlignmentFlag.AlignRight)
        right.addStretch()
        root.addLayout(right)

        self._update_save_label()
        self._apply_style()

    # ---- state ----
    def set_saved(self, saved: bool) -> None:
        self._saved = saved
        self._bookmark.setVisible(saved)
        self._update_save_label()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def _update_save_label(self) -> None:
        self._save_btn.setText("Saved" if self._saved else "Save")

    def _apply_style(self) -> None:
        if self._selected:
            self.setStyleSheet(
                f"#JobCard{{background:{C.accent_bg_soft};"
                f"border:1px solid {C.accent};border-left:3px solid {C.accent};"
                f"border-radius:6px;}}")
        else:
            self.setStyleSheet(
                f"#JobCard{{background:{C.bg_panel};border:1px solid {C.border};"
                f"border-radius:6px;}}"
                f"#JobCard:hover{{border-color:{C.accent_border_strong};}}")

    # ---- hover reveals action row + shadow ----
    def enterEvent(self, event) -> None:  # noqa: N802
        self._actions.setVisible(True)
        eff = QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(18)
        eff.setOffset(0, 3)
        eff.setColor(QColor(20, 28, 38, 24))
        self.setGraphicsEffect(eff)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._actions.setVisible(False)
        self.setGraphicsEffect(None)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.job.id)
        super().mouseReleaseEvent(event)
