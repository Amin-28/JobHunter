"""Screen 1h — Saved Jobs."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QMenu, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget)

from .. import icons
from ..models import SavedJob
from ..theme import C, F
from ..widgets.common import LogoTile
from ..widgets.match_ring import ring_colors


class SavedScreen(QWidget):
    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.store.saved_changed.connect(self._rebuild)

        col = QVBoxLayout(self); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(0)

        # header
        self._header = QWidget()
        self._header.setStyleSheet(f"background:{C.bg_app};border-bottom:1px solid {C.border};")
        hv = QHBoxLayout(self._header); hv.setContentsMargins(30, 24, 30, 16); hv.setSpacing(0)
        htext = QVBoxLayout(); htext.setSpacing(4)
        title = QLabel("Saved jobs")
        title.setStyleSheet(f"color:{C.text};font-size:21px;font-weight:600;background:transparent;")
        self._subtitle = QLabel("")
        self._subtitle.setStyleSheet(f"color:{C.text_3};font-size:12.5px;background:transparent;")
        htext.addWidget(title); htext.addWidget(self._subtitle)
        hv.addLayout(htext); hv.addStretch()
        sort = QComboBox(); sort.addItems(["Sort: date saved", "Sort: match score", "Sort: deadline"])
        hv.addWidget(sort)
        export = QPushButton("Export CSV"); export.setProperty("kind", "secondary")
        export.setCursor(Qt.CursorShape.PointingHandCursor)
        hv.addSpacing(10); hv.addWidget(export)
        col.addWidget(self._header)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self._host = QWidget(); self._list = QVBoxLayout(self._host)
        self._list.setContentsMargins(30, 8, 30, 20); self._list.setSpacing(0)
        self._list.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._host)
        col.addWidget(scroll, 1)

    def on_enter(self) -> None:
        self._rebuild()

    def _clear(self) -> None:
        while self._list.count():
            item = self._list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebuild(self) -> None:
        self._clear()
        saved = self.store.saved
        deadlines = sum(1 for s in saved if s.deadline)
        self._subtitle.setText(f"{len(saved)} saved · {deadlines} with deadlines this week")

        if not saved:
            empty = QLabel("Nothing saved yet.\nBookmark a job from the results list.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{C.text_3};font-size:13px;background:transparent;padding:60px;")
            self._list.addWidget(empty)
            self.store.set_status("0 saved")
            return

        for s in saved:
            self._list.addWidget(self._row(s))

        footer = QLabel("Saved jobs are re-checked each time you open the app.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color:{C.text_5};font-size:12px;background:transparent;margin-top:18px;")
        self._list.addWidget(footer)
        expired = sum(1 for s in saved if s.expired)
        self.store.set_status(f"{len(saved)} saved · {expired} expired listing")

    def _row(self, s: SavedJob) -> QWidget:
        job = s.job
        w = QWidget()
        w.setStyleSheet(f"border-bottom:1px solid {C.rule};")
        row = QHBoxLayout(w); row.setContentsMargins(4, 13, 4, 13); row.setSpacing(14)
        dim = s.expired

        bm = QLabel(); bm.setPixmap(icons.pixmap("bookmark_filled", 14, C.accent, 2.0))
        row.addWidget(bm)
        row.addWidget(LogoTile(job.company, 34, 5, 12))

        info = QVBoxLayout(); info.setSpacing(2)
        t = QLabel(job.title)
        deco = "text-decoration:line-through;" if dim else ""
        t.setStyleSheet(f"color:{C.text};font-size:13.5px;font-weight:600;background:transparent;{deco}")
        sub = QLabel(f"{job.company} · {job.location} · {job.salary_label}")
        sub.setStyleSheet(f"color:{C.text_4};font-size:11.5px;background:transparent;")
        info.addWidget(t); info.addWidget(sub)
        row.addLayout(info, 1)

        chip = self._status_chip(s)
        if chip:
            row.addWidget(chip)

        arc, txt = ring_colors(job.score)
        sc = QLabel(str(job.score)); sc.setFixedWidth(36)
        sc.setStyleSheet(f"color:{txt};font-family:'{F.mono}';font-size:11.5px;font-weight:600;background:transparent;")
        row.addWidget(sc)

        age = QLabel(s.saved_at); age.setFixedWidth(80)
        age.setStyleSheet(f"color:{C.text_4};font-size:11.5px;background:transparent;")
        row.addWidget(age)

        kebab = QPushButton(); kebab.setIcon(icons.icon("kebab", 15, C.text_disabled))
        kebab.setCursor(Qt.CursorShape.PointingHandCursor)
        kebab.setStyleSheet("border:none;background:transparent;")
        kebab.clicked.connect(lambda: self._kebab_menu(s, kebab))
        row.addWidget(kebab)

        if dim:
            w.setStyleSheet(w.styleSheet() + "")
            w.setWindowOpacity(0.6)
            for i in range(row.count()):
                item = row.itemAt(i).widget()
                if item:
                    item.setStyleSheet(item.styleSheet())
        return w

    def _status_chip(self, s: SavedJob) -> QLabel | None:
        if s.expired:
            return self._chip("Expired", C.danger, C.danger_bg, C.danger_border)
        if s.applied_at:
            return self._chip(s.applied_at, C.ok_ink, C.ok_bg, C.ok_border)
        if s.deadline:
            return self._chip(s.deadline, C.warn_ink, C.warn_bg, C.warn_border)
        if s.channel_note:
            lbl = QLabel(s.channel_note)
            lbl.setStyleSheet(f"color:{C.text_4};font-size:11.5px;background:transparent;")
            return lbl
        return None

    def _chip(self, text: str, fg: str, bg: str, border: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{fg};background:{bg};border:1px solid {border};border-radius:3px;"
            f"padding:3px 8px;font-size:11.5px;")
        return lbl

    def _kebab_menu(self, s: SavedJob, anchor: QWidget) -> None:
        menu = QMenu(self)
        menu.addAction("Open detail")
        menu.addAction("Mark as applied", lambda: self.store.mark_applied(s.job.id))
        menu.addAction("Copy apply link")
        menu.addSeparator()
        menu.addAction("Remove from saved", lambda: self.store.toggle_saved(s.job))
        menu.exec(anchor.mapToGlobal(anchor.rect().bottomLeft()))
