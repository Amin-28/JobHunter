"""Screen 1a (resume upload / empty state) + 1b (processing)."""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QVBoxLayout, QWidget, QStackedLayout)

from .. import icons
from ..theme import C, F
from ..workers import ParseWorker


class DropZone(QWidget):
    file_ready = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedSize(600, 216)
        self._state = "idle"     # idle | drag | rejected
        self._msg = ""

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(14)

        self._glyph = QLabel()
        self._glyph.setPixmap(icons.pixmap("upload", 30, "#9AA3AD", 1.7))
        self._glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._glyph, alignment=Qt.AlignmentFlag.AlignCenter)

        self._headline = QLabel("Drag & drop your resume here")
        self._headline.setStyleSheet(
            f"color:{C.text_2};font-size:14px;background:transparent;")
        self._headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._headline)

        # or-divider
        divider = QHBoxLayout()
        divider.setSpacing(12)
        divider.addStretch()
        for _ in range(1):
            l1 = QWidget(); l1.setFixedSize(60, 1); l1.setStyleSheet(f"background:{C.border};")
            divider.addWidget(l1)
            orl = QLabel("or"); orl.setStyleSheet(f"color:#A6ADB6;font-size:11.5px;background:transparent;")
            divider.addWidget(orl)
            l2 = QWidget(); l2.setFixedSize(60, 1); l2.setStyleSheet(f"background:{C.border};")
            divider.addWidget(l2)
        divider.addStretch()
        lay.addLayout(divider)

        self._browse = QPushButton("Browse Files…")
        self._browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse.setProperty("kind", "primary")
        self._browse.clicked.connect(self._browse_files)
        lay.addWidget(self._browse, alignment=Qt.AlignmentFlag.AlignCenter)

        self._hint = QLabel("PDF or DOCX · up to 10 MB")
        self._hint.setStyleSheet(f"color:{C.text_5};font-size:11px;background:transparent;")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._hint)

    # ---- painting the dashed border ----
    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self._state == "drag":
            border, fill = C.accent, C.accent_bg_soft
        elif self._state == "rejected":
            border, fill = C.danger, C.danger_bg
        else:
            border, fill = "#C3CAD2", C.bg_panel
        p.setBrush(QColor(fill))
        pen = p.pen(); pen.setColor(QColor(border)); pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        r = self.rect().adjusted(1, 1, -2, -2)
        p.drawRoundedRect(r, 8, 8)
        p.end()

    def _set_state(self, state: str) -> None:
        self._state = state
        accent = state == "drag"
        self._glyph.setPixmap(icons.pixmap("upload", 30, C.accent if accent else "#9AA3AD", 1.7))
        self._headline.setStyleSheet(
            f"color:{C.accent if accent else C.text_2};font-size:14px;background:transparent;")
        self.update()

    # ---- drag & drop ----
    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_state("drag")

    def dragLeaveEvent(self, event):  # noqa: N802
        self._set_state("idle")

    def dropEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        self._validate(path)

    def _browse_files(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose your resume", "", "Resumes (*.pdf *.docx)")
        if path:
            self._validate(path)

    def _validate(self, path: str) -> None:
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".pdf", ".docx"):
            self._reject("Only PDF or DOCX files, please.")
            return
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        if size > 10 * 1024 * 1024:
            self._reject("That file is over 10 MB.")
            return
        self._set_state("idle")
        self.file_ready.emit(path)

    def _reject(self, message: str) -> None:
        self._set_state("rejected")
        self._headline.setText(message)
        self._headline.setStyleSheet(
            f"color:{C.danger};font-size:13px;background:transparent;")

        def clear():
            self._headline.setText("Drag & drop your resume here")
            self._set_state("idle")
        QTimer.singleShot(4000, clear)


class UploadScreen(QWidget):
    done = pyqtSignal()

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.pool = QThreadPool.globalInstance()
        self._worker: ParseWorker | None = None

        self._layout = QStackedLayout(self)
        self._empty = self._build_empty()
        self._processing = self._build_processing()
        self._layout.addWidget(self._empty)
        self._layout.addWidget(self._processing)

    def on_enter(self) -> None:
        if self.store.parse_state in ("idle", "error"):
            self._layout.setCurrentWidget(self._empty)
            self.store.set_status("Ready · No resume loaded")

    # ---- 1a empty ----
    def _build_empty(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        illo = QLabel()
        illo.setPixmap(icons.pixmap("file", 72, "#C3CAD2", 1.6))
        illo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(illo, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Find jobs that fit your resume")
        title.setStyleSheet(
            f"color:{C.text};font-size:26px;font-weight:600;background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setContentsMargins(0, 22, 0, 8)
        outer.addWidget(title)

        sub = QLabel("Drop in your resume and JobMatch reads your skills, titles and "
                     "experience to score every job it finds.")
        sub.setWordWrap(True)
        sub.setFixedWidth(430)
        sub.setStyleSheet(
            f"color:{C.text_3};font-size:13.5px;background:transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(sub, alignment=Qt.AlignmentFlag.AlignCenter)

        dz = DropZone()
        dz.file_ready.connect(self._start_parse)
        dz_wrap = QWidget()
        dzl = QVBoxLayout(dz_wrap); dzl.setContentsMargins(0, 30, 0, 0)
        dzl.addWidget(dz, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(dz_wrap, alignment=Qt.AlignmentFlag.AlignCenter)

        footer = QLabel("Last used: <b>amara_okafor_cv.pdf</b>")
        footer.setStyleSheet(
            f"color:{C.text_4};font-size:11.5px;background:transparent;margin-top:26px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(footer)
        return w

    # ---- 1b processing ----
    def _build_processing(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Reading your resume…")
        title.setStyleSheet(
            f"color:{C.text};font-size:22px;font-weight:600;background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        sub = QLabel("This takes a few seconds. Everything happens on your machine.")
        sub.setStyleSheet(f"color:{C.text_3};font-size:13px;background:transparent;margin-top:7px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(sub)

        card = QWidget(); card.setObjectName("Card"); card.setFixedWidth(600)
        cl = QVBoxLayout(card); cl.setContentsMargins(24, 22, 24, 22); cl.setSpacing(0)

        # file row
        frow = QHBoxLayout(); frow.setSpacing(12)
        badge = QLabel("PDF"); badge.setFixedSize(34, 40)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{C.danger_bg};border:1px solid {C.danger_border};"
            f"border-radius:4px;color:{C.danger};font-family:'{F.mono}';"
            f"font-size:9px;font-weight:600;")
        frow.addWidget(badge)
        finfo = QVBoxLayout(); finfo.setSpacing(2)
        self._fname = QLabel("amara_okafor_cv.pdf")
        self._fname.setStyleSheet(f"color:{C.text};font-size:13px;font-weight:600;background:transparent;")
        fsub = QLabel("248 KB · 2 pages")
        fsub.setStyleSheet(f"color:{C.text_4};font-size:11.5px;background:transparent;")
        finfo.addWidget(self._fname); finfo.addWidget(fsub)
        frow.addLayout(finfo); frow.addStretch()
        self._pct = QLabel("0%")
        self._pct.setStyleSheet(
            f"color:{C.accent};font-family:'{F.mono}';font-size:12px;font-weight:600;background:transparent;")
        frow.addWidget(self._pct)
        cl.addLayout(frow)

        self._bar = QProgressBar(); self._bar.setTextVisible(False)
        self._bar.setFixedHeight(5); self._bar.setRange(0, 100); self._bar.setValue(0)
        self._bar.setStyleSheet(
            f"QProgressBar{{background:{C.rule};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{background:{C.accent};border-radius:3px;}}")
        cl.addSpacing(16); cl.addWidget(self._bar)

        self._error = QLabel("")
        self._error.setWordWrap(True)
        self._error.setVisible(False)
        self._error.setStyleSheet(
            f"color:{C.danger};font-size:12.5px;background:transparent;margin-top:12px;")
        cl.addWidget(self._error)

        # step list
        self._steps_box = QVBoxLayout(); self._steps_box.setSpacing(11)
        self._step_labels: list[QLabel] = []
        steps = ["Extracted text from 2 pages",
                 "Found sections: Experience, Skills, Education",
                 "Identifying skills and seniority…",
                 "Building search keywords"]
        for text in steps:
            row = QHBoxLayout(); row.setSpacing(9)
            dot = QLabel("○"); dot.setStyleSheet(f"color:{C.text_disabled};font-size:14px;background:transparent;")
            lbl = QLabel(text); lbl.setStyleSheet(f"color:{C.text_disabled};font-size:12.5px;background:transparent;")
            row.addWidget(dot); row.addWidget(lbl); row.addStretch()
            self._step_labels.append(lbl)
            lbl.setProperty("dot", dot)
            self._steps_box.addLayout(row)
        cl.addSpacing(20); cl.addLayout(self._steps_box)

        # footer cancel
        cl.addSpacing(16)
        sep = QWidget(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{C.rule};")
        cl.addWidget(sep)
        frow2 = QHBoxLayout(); frow2.addStretch()
        cancel = QPushButton("Cancel"); cancel.setProperty("kind", "secondary")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self._cancel)
        frow2.addWidget(cancel)
        cl.addSpacing(16); cl.addLayout(frow2)

        outer.addSpacing(28)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        return w

    # ---- parse lifecycle ----
    def _start_parse(self, path: str) -> None:
        self.store.resume_file = path
        self.store.set_parse_state("parsing")
        self._fname.setText(os.path.basename(path))
        self._bar.setValue(0); self._pct.setText("0%")
        self._error.setVisible(False)
        self._bar.setStyleSheet(
            f"QProgressBar{{background:{C.rule};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{background:{C.accent};border-radius:3px;}}")
        for lbl in self._step_labels:
            lbl.setStyleSheet(f"color:{C.text_disabled};font-size:12.5px;background:transparent;")
            lbl.property("dot").setText("○")
            lbl.property("dot").setStyleSheet(f"color:{C.text_disabled};font-size:14px;background:transparent;")
        self._layout.setCurrentWidget(self._processing)
        self.store.set_status(f"Parsing… · {os.path.basename(path)}")

        self._worker = ParseWorker(path)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.failed.connect(self._on_failed)
        self.pool.start(self._worker)

    def _on_progress(self, pct: int, step: str) -> None:
        self._bar.setValue(pct); self._pct.setText(f"{pct}%")
        # mark steps done up to this one
        try:
            idx = [l.text() for l in self._step_labels].index(step)
        except ValueError:
            idx = -1
        for i, lbl in enumerate(self._step_labels):
            dot = lbl.property("dot")
            if i <= idx:
                lbl.setStyleSheet(f"color:{C.text_2};font-size:12.5px;background:transparent;")
                dot.setText("✓"); dot.setStyleSheet(f"color:{C.accent};font-size:13px;background:transparent;")
            elif i == idx + 1:
                lbl.setStyleSheet(f"color:{C.text};font-size:12.5px;font-weight:600;background:transparent;")
                dot.setText("◍"); dot.setStyleSheet(f"color:{C.accent};font-size:13px;background:transparent;")

    def _on_finished(self, profile) -> None:
        self.store.set_profile(profile)
        self.store.set_parse_state("done")
        self.done.emit()

    def _on_failed(self, message: str) -> None:
        self.store.set_parse_state("error")
        self._bar.setStyleSheet(
            f"QProgressBar{{background:{C.rule};border:none;border-radius:3px;}}"
            f"QProgressBar::chunk{{background:{C.danger};border-radius:3px;}}")
        self._error.setText(f"{message}  Try another file, or check the résumé isn't a scanned image.")
        self._error.setVisible(True)
        self.store.set_status("Couldn't read that file")

    def _cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
        self.store.set_parse_state("idle")
        self._layout.setCurrentWidget(self._empty)
        self.store.set_status("Ready · No resume loaded")
