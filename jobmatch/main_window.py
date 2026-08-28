"""Frameless window shell: title bar, left-nav, content stack, status bar.

Supports a runtime light/dark theme switch: because many widgets bake colors
into inline stylesheets, a switch re-applies the global QSS and rebuilds the
frame's content from the (persistent) store.
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QApplication, QGraphicsDropShadowEffect,
                             QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                             QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from . import icons
from .store import AppStore
from .theme import C, apply_theme, current_theme, stylesheet

P_UPLOAD, P_PROFILE, P_SEARCH, P_SAVED = 0, 1, 2, 3


class TitleBar(QWidget):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__()
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        self._win = window
        self._drag_pos: QPoint | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        mark = QLabel()
        mark.setFixedSize(15, 15)
        mark.setStyleSheet(
            f"border-radius:4px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {C.accent_2}, stop:1 {C.accent});")
        lay.addWidget(mark)
        title = QLabel("JobMatch AI")
        title.setObjectName("TitleLabel")
        title.setStyleSheet(
            f"color:{C.text};font-size:11.5px;font-weight:600;letter-spacing:0.3px;background:transparent;")
        lay.addWidget(title)
        lay.addStretch()

        # theme toggle (sun in dark → go light, moon in light → go dark)
        dark = current_theme() == "dark"
        theme_btn = QPushButton()
        theme_btn.setIcon(icons.icon("sun" if dark else "moon", 14, C.text_3, 1.9))
        theme_btn.setFixedSize(24, 22)
        theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_btn.setToolTip("Switch to light theme" if dark else "Switch to dark theme")
        theme_btn.setStyleSheet(
            "QPushButton{border:none;background:transparent;}"
            f"QPushButton:hover{{background:{C.bg_fill};border-radius:5px;}}")
        theme_btn.clicked.connect(window.toggle_theme)
        lay.addWidget(theme_btn)

        gear_btn = QPushButton()
        gear_btn.setIcon(icons.icon("gear", 14, C.text_3, 1.8))
        gear_btn.setFixedSize(24, 22)
        gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gear_btn.setToolTip("Settings — API keys")
        gear_btn.setStyleSheet(
            "QPushButton{border:none;background:transparent;}"
            f"QPushButton:hover{{background:{C.bg_fill};border-radius:5px;}}")
        gear_btn.clicked.connect(window.open_settings)
        lay.addWidget(gear_btn)
        lay.addSpacing(4)

        for glyph, name, obj in (("—", "min", "WinBtn"), ("▢", "max", "WinBtn"),
                                 ("✕", "close", "WinClose")):
            btn = QPushButton(glyph)
            btn.setObjectName(obj)
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if name == "min":
                btn.clicked.connect(window.showMinimized)
            elif name == "max":
                btn.clicked.connect(window.toggle_max)
            else:
                btn.clicked.connect(window.close)
            btn.setStyleSheet(
                f"QPushButton{{color:{C.text_4};border:none;background:transparent;font-size:12px;}}"
                f"QPushButton:hover{{color:{C.danger if name=='close' else C.text};}}")
            lay.addWidget(btn)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._win.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self._win.isMaximized():
                self._win.toggle_max()
            self._win.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        self._win.toggle_max()


class MainWindow(QWidget):
    def __init__(self, store: AppStore) -> None:
        super().__init__()
        self.store = store
        self._current_index = 0
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1240 + 24, 780 + 24)
        self.setMinimumSize(1040 + 24, 680 + 24)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(12, 12, 12, 12)   # room for window shadow

        self._build_frame()
        self._shortcuts()

        # restore straight into the workflow if a profile was persisted
        start = P_SEARCH if self.store.search_ready else P_UPLOAD
        self.goto(start)

    # ---- frame (rebuildable for theme switch) ----
    def _build_frame(self) -> None:
        self.frame = QWidget()
        self.frame.setObjectName("Window")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(34); shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 70 if current_theme() == "dark" else 33))
        self.frame.setGraphicsEffect(shadow)
        self._outer.addWidget(self.frame)

        col = QVBoxLayout(self.frame)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        self.titlebar = TitleBar(self)
        col.addWidget(self.titlebar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        from .widgets.nav import NavStepper
        self.nav = NavStepper()
        self.nav.navigate.connect(self.goto)
        body.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.setObjectName("Content")
        body.addWidget(self.stack, 1)
        col.addLayout(body, 1)

        self.status = QLabel("Ready · No resume loaded")
        self.status.setObjectName("StatusBar")
        self.status.setFixedHeight(26)
        self.status.setStyleSheet(
            f"#StatusBar{{background:{C.bg_sidebar};border-top:1px solid {C.border};"
            f"color:{C.text_4};font-size:10.5px;padding-left:12px;"
            f"border-bottom-left-radius:7px;border-bottom-right-radius:7px;}}")
        col.addWidget(self.status)

        self._build_screens()
        self._wire()

    def toggle_theme(self) -> None:
        from .services import config
        new = "light" if current_theme() == "dark" else "dark"
        apply_theme(new)
        config.set_theme(new)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet())
        idx = self._current_index
        old = self.frame
        self._outer.removeWidget(old)
        old.setParent(None)
        old.deleteLater()
        self._build_frame()
        self.goto(idx)

    # ---- screens ----
    def _build_screens(self) -> None:
        from .screens.upload import UploadScreen
        from .screens.profile import ProfileScreen
        from .screens.search import SearchScreen
        from .screens.saved import SavedScreen

        self.upload = UploadScreen(self.store)
        self.profile = ProfileScreen(self.store)
        self.search = SearchScreen(self.store)
        self.saved = SavedScreen(self.store)
        for w in (self.upload, self.profile, self.search, self.saved):
            self.stack.addWidget(w)

        self.upload.done.connect(lambda: self.goto(P_PROFILE))
        self.profile.search_requested.connect(lambda: self.goto(P_SEARCH))

    def _wire(self) -> None:
        self.store.status_changed.connect(self.status.setText)
        self.store.nav_gate_changed.connect(self._refresh_nav)
        self.store.saved_changed.connect(
            lambda: self.nav.set_saved_count(len(self.store.saved)))
        self.nav.set_saved_count(len(self.store.saved))
        self.status.setText(self.store.last_status)   # survive theme rebuilds

    def _shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+O"), self, lambda: self.goto(P_UPLOAD))
        QShortcut(QKeySequence("Ctrl+2"), self,
                  lambda: self.goto(P_PROFILE) if self.store.profile_ready else None)
        QShortcut(QKeySequence("Ctrl+3"), self,
                  lambda: self.goto(P_SEARCH) if self.store.search_ready else None)
        QShortcut(QKeySequence("Ctrl+4"), self,
                  lambda: self.goto(P_SAVED) if self.store.saved_ready else None)
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_theme)
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    def _on_escape(self) -> None:
        if self.stack.currentWidget() is self.search:
            self.search._close_detail()

    def _focus_search(self) -> None:
        if self.store.search_ready:
            self.goto(P_SEARCH)
            if hasattr(self.search, "focus_search"):
                self.search.focus_search()

    # ---- navigation ----
    def goto(self, index: int) -> None:
        gates = self._gates()
        if not gates.get(index, True):
            return
        self.stack.setCurrentIndex(index)
        self._current_index = index
        self.nav.update_states(index, gates)
        w = self.stack.widget(index)
        if hasattr(w, "on_enter"):
            w.on_enter()
        self._fade_in(w)

    def _fade_in(self, w: QWidget) -> None:
        eff = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(160)
        anim.setStartValue(0.0); anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: w.setGraphicsEffect(None))
        anim.start()
        self._page_anim = anim

    def _gates(self) -> dict[int, bool]:
        return {
            P_UPLOAD: True,
            P_PROFILE: self.store.profile_ready,
            P_SEARCH: self.store.search_ready,
            P_SAVED: self.store.saved_ready,
        }

    def _refresh_nav(self) -> None:
        self.nav.update_states(self._current_index, self._gates())
        self.nav.set_saved_count(len(self.store.saved))

    def toggle_max(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def open_settings(self) -> None:
        from .screens.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        if dlg.exec():
            # keys picked up immediately (config cache updated) — refresh status
            from .services import config
            n = len(config.enabled_sources())
            ai_on = bool(config.groq_key() or config.gemini_key()
                         or config.openrouter_key() or config.anthropic_key())
            self.store.set_status(
                f"Settings saved · {n} job sources"
                + (" · AI enabled" if ai_on else ""))
