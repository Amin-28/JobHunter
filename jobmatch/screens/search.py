"""Screens 1d (search + filters), 1e (result cards), 1f/1g (job detail)."""
from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, Qt, QThreadPool,
                          QTimer, pyqtSignal)
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFrame, QGraphicsOpacityEffect,
                             QHBoxLayout, QLabel, QLineEdit, QProgressBar,
                             QPushButton, QScrollArea, QStackedWidget,
                             QVBoxLayout, QWidget)

from .. import icons
from ..theme import C, F
from ..widgets.chips import KeywordToken, keyword_token
from ..widgets.common import LogoTile, rule, section_label
from ..widgets.flow_layout import FlowLayout
from ..widgets.job_card import JobCard
from ..widgets.match_ring import MatchRing, ring_colors
from ..widgets.range_slider import DualRangeSlider
from ..widgets.toggle import ToggleSwitch
from ..services.job_search import build_keywords
from ..workers import ExplainWorker, KeywordsWorker, SearchWorker
from .apply_bar import ApplyBar


class SalaryTrack(QWidget):
    """Static dual-range salary track (visual)."""
    def __init__(self):
        super().__init__(); self.setFixedHeight(18)
    def paintEvent(self, e):  # noqa: N802
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        y = 9; w = self.width()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#DFE3E8"))
        p.drawRoundedRect(0, y - 2, w, 4, 2, 2)
        x1, x2 = int(w * 0.15), int(w * 0.75)
        p.setBrush(QColor(C.accent)); p.drawRect(x1, y - 2, x2 - x1, 4)
        for hx in (x1, x2):
            p.setBrush(QColor("#FFFFFF"))
            p.setPen(QColor(C.accent))
            p.drawEllipse(hx - 7, y - 7, 14, 14)
            p.setPen(Qt.PenStyle.NoPen)
        p.end()


class SearchScreen(QWidget):
    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.pool = QThreadPool.globalInstance()
        self._cards: dict[str, JobCard] = {}
        self._filter_widgets: dict = {}

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(280)
        self._debounce.timeout.connect(self.store.apply_filters)

        self.stack = QStackedWidget()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.stack)

        self._results_view = self._build_results_view()
        self._detail_view = QWidget()   # filled per-job
        self.stack.addWidget(self._results_view)
        self.stack.addWidget(self._detail_view)

        self.store.results_changed.connect(self._render_results)
        self.store.results_state_changed.connect(self._render_results)
        self.store.saved_changed.connect(self._sync_saved)

    def on_enter(self) -> None:
        self.stack.setCurrentWidget(self._results_view)
        # seed location filter + keyword tokens from the résumé on first entry
        loc_widget = self._filter_widgets.get("location")
        if loc_widget is not None and not loc_widget.text() and self.store.query.get("location"):
            loc_widget.setText(self.store.query["location"])
        if not self.store.query["keywords"] and self.store.profile is not None:
            self.store.query["keywords"] = build_keywords(self.store.profile)[:3]
            self._render_tokens()
        if not self.store.raw_results and self.store.results_state != "loading":
            self._run_search()

    def focus_search(self) -> None:
        self._token_input.setFocus()

    def _render_tokens(self) -> None:
        # clear any existing token chips (keep the magnifier at 0 and input at end)
        for i in reversed(range(1, self._token_layout.count() - 1)):
            item = self._token_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
                self._token_layout.removeItem(item)
        for kw in self.store.query["keywords"]:
            tok = KeywordToken(kw)
            tok.removed.connect(self._remove_keyword)
            self._token_layout.insertWidget(self._token_layout.count() - 1, tok)

    def _remove_keyword(self, kw: str) -> None:
        self.store.query["keywords"] = [k for k in self.store.query["keywords"] if k != kw]
        self._render_tokens()
        self._run_search()

    def _add_keyword(self) -> None:
        text = self._token_input.text().strip()
        if not text:
            return
        self.store.query["keywords"].append(text)
        self._token_input.clear()
        self._render_tokens()
        self._run_search()

    def _ai_research(self) -> None:
        if self.store.profile is None:
            return
        self._ai_btn.setEnabled(False)
        self._ai_btn.setText("  Researching…")
        worker = KeywordsWorker(self.store.profile)
        worker.signals.finished.connect(self._on_ai_keywords)
        self.pool.start(worker)

    def _on_ai_keywords(self, keywords, provider: str) -> None:
        self._ai_btn.setEnabled(True)
        self._ai_btn.setText("  AI research")
        if keywords:
            self.store.query["keywords"] = keywords[:5]
            self._render_tokens()
            self._run_search()
            src = provider if provider != "local" else "your résumé"
            self.store.set_status(f"Keywords from {src}: {', '.join(keywords[:5])}")

    # ================= 1d results view =================
    def _build_results_view(self) -> QWidget:
        w = QWidget()
        col = QVBoxLayout(w); col.setContentsMargins(0, 0, 0, 0); col.setSpacing(0)

        # search toolbar
        toolbar = QWidget(); toolbar.setObjectName("Toolbar"); toolbar.setFixedHeight(52)
        tl = QHBoxLayout(toolbar); tl.setContentsMargins(16, 0, 16, 0); tl.setSpacing(12)
        field = QWidget()
        field.setStyleSheet(
            f"background:{C.bg_panel};border:1px solid {C.border_input};border-radius:5px;")
        fl = QHBoxLayout(field); fl.setContentsMargins(11, 6, 11, 6); fl.setSpacing(6)
        mag = QLabel(); mag.setPixmap(icons.pixmap("search", 15, C.text_4, 2.0))
        fl.addWidget(mag)
        self._token_layout = fl
        self._token_input = QLineEdit(); self._token_input.setPlaceholderText("add keyword…")
        self._token_input.setStyleSheet("border:none;background:transparent;font-size:13px;")
        self._token_input.returnPressed.connect(self._add_keyword)
        fl.addWidget(self._token_input, 1)
        field.setMaximumWidth(640)
        tl.addWidget(field, 1)

        # AI keyword research (uses Claude if a key is set, else résumé heuristics)
        self._ai_btn = QPushButton("  AI research")
        self._ai_btn.setIcon(icons.icon("sparkle", 14, C.accent))
        self._ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ai_btn.setToolTip("Suggest better search keywords from your résumé")
        self._ai_btn.setStyleSheet(
            f"QPushButton{{color:{C.accent};border:1px solid {C.accent_border};"
            f"border-radius:5px;padding:7px 12px;font-size:12px;font-weight:600;"
            f"background:{C.accent_bg_soft};}}"
            f"QPushButton:hover{{background:{C.accent_bg};}}")
        self._ai_btn.clicked.connect(self._ai_research)
        tl.addWidget(self._ai_btn)

        search_btn = QPushButton("Search"); search_btn.setProperty("kind", "primary")
        search_btn.setStyleSheet(
            f"QPushButton{{background:{C.accent};color:#fff;border:none;border-radius:5px;"
            f"padding:8px 18px;font-size:12.5px;font-weight:600;}}"
            f"QPushButton:hover{{background:{C.accent_hover};}}")
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.clicked.connect(self._run_search)
        tl.addWidget(search_btn)
        hint = QLabel("Suggested from resume")
        hint.setStyleSheet(f"color:{C.text_4};font-size:11.5px;background:transparent;")
        tl.addWidget(hint)
        col.addWidget(toolbar)

        # body: filter sidebar + results
        body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)
        body.addWidget(self._build_filters())

        results_col = QVBoxLayout(); results_col.setContentsMargins(0, 0, 0, 0); results_col.setSpacing(0)
        # results header
        header = QWidget(); header.setFixedHeight(42)
        header.setStyleSheet(f"border-bottom:1px solid {C.border};")
        hl = QHBoxLayout(header); hl.setContentsMargins(20, 0, 20, 0)
        self._count_label = QLabel("Searching…")
        self._count_label.setStyleSheet(f"color:{C.text};font-size:12.5px;font-weight:600;background:transparent;")
        hl.addWidget(self._count_label); hl.addStretch()
        sortlbl = QLabel("Sort by"); sortlbl.setStyleSheet(f"color:{C.text_3};font-size:12px;background:transparent;")
        hl.addWidget(sortlbl)
        self._sort = QComboBox(); self._sort.addItems(["Match score", "Date posted", "Salary"])
        self._sort.currentTextChanged.connect(self._on_sort)
        hl.addWidget(self._sort)
        results_col.addWidget(header)

        # scroll list
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self._list_host = QWidget()
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(20, 14, 20, 14)
        self._list_layout.setSpacing(11)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._list_host)
        results_col.addWidget(scroll, 1)

        rc = QWidget(); rc.setLayout(results_col); rc.setStyleSheet(f"background:{C.bg_app};")
        body.addWidget(rc, 1)
        col.addLayout(body, 1)
        return w

    def _build_filters(self) -> QWidget:
        panel = QWidget(); panel.setObjectName("FilterSidebar"); panel.setFixedWidth(252)
        scroll = QScrollArea(panel); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent;")
        inner = QWidget(); scroll.setWidget(inner)
        v = QVBoxLayout(inner); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(0)
        outer = QVBoxLayout(panel); outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(scroll)

        head = QHBoxLayout()
        htitle = QLabel("Filters"); htitle.setStyleSheet(f"color:{C.text};font-size:12.5px;font-weight:600;background:transparent;")
        head.addWidget(htitle); head.addStretch()
        reset = QPushButton("Reset")
        reset.setStyleSheet(f"color:{C.text_4};font-size:11px;border:none;background:transparent;")
        reset.setCursor(Qt.CursorShape.PointingHandCursor)
        reset.clicked.connect(self._reset_filters)
        head.addWidget(reset)
        v.addLayout(head); v.addSpacing(16)

        # Location  (seeded from the résumé in on_enter)
        v.addWidget(section_label("LOCATION")); v.addSpacing(8)
        loc = QLineEdit(); loc.setPlaceholderText("City, country or region")
        loc.setStyleSheet(loc.styleSheet() + "font-size:12.5px;")
        loc.textChanged.connect(self._on_location_changed)
        self._filter_widgets["location"] = loc
        v.addWidget(loc); v.addSpacing(10)
        remote_row = QHBoxLayout()
        rl = QLabel("Remote only"); rl.setStyleSheet(f"color:{C.text_2};font-size:12.5px;background:transparent;")
        remote_row.addWidget(rl); remote_row.addStretch()
        remote = ToggleSwitch(checked=False)
        remote.toggled_on.connect(lambda on: self._set_query(remote_only=on))
        self._filter_widgets["remote"] = remote
        remote_row.addWidget(remote)
        v.addLayout(remote_row)
        v.addSpacing(16); v.addWidget(rule(C.border)); v.addSpacing(16)

        # Salary — interactive dual-range filter
        v.addWidget(section_label("SALARY RANGE (ANNUAL)")); v.addSpacing(12)
        self._salary = DualRangeSlider(0, 250000, 5000)
        self._salary.changed.connect(self._on_salary_labels)
        self._salary.committed.connect(self._on_salary_commit)
        v.addWidget(self._salary); v.addSpacing(6)
        srow = QHBoxLayout()
        self._smin = QLabel("$0"); self._smax = QLabel("$250k+")
        for s in (self._smin, self._smax):
            s.setStyleSheet(f"color:{C.text_2};font-family:'{F.mono}';font-size:11.5px;background:transparent;")
        srow.addWidget(self._smin); srow.addStretch(); srow.addWidget(self._smax)
        v.addLayout(srow)
        v.addSpacing(16); v.addWidget(rule(C.border)); v.addSpacing(16)

        # Date posted segmented
        v.addWidget(section_label("DATE POSTED")); v.addSpacing(10)
        seg = QHBoxLayout(); seg.setSpacing(0)
        self._date_buttons = []
        for opt, val in (("24h", "24h"), ("7d", "7d"), ("30d", "30d"), ("Any", "any")):
            b = QPushButton(opt); b.setCheckable(True); b.setChecked(val == "any")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{border:1px solid {C.border_input};background:{C.bg_panel};"
                f"color:{C.text_2};font-size:11.5px;padding:5px 0;}}"
                f"QPushButton:checked{{background:{C.accent};color:#fff;font-weight:600;border-color:{C.accent};}}")
            b.clicked.connect(lambda _, v_=val, btn=b: self._on_date(v_, btn))
            self._date_buttons.append(b)
            seg.addWidget(b, 1)
        v.addLayout(seg)
        v.addSpacing(16); v.addWidget(rule(C.border)); v.addSpacing(16)

        # Job type
        v.addWidget(section_label("JOB TYPE")); v.addSpacing(10)
        self._type_boxes = []
        for name in ("Full-time", "Contract", "Internship", "Part-time"):
            cb = self._checkbox(name)
            self._type_boxes.append(cb)
            v.addWidget(cb); v.addSpacing(9)
        v.addSpacing(7); v.addWidget(rule(C.border)); v.addSpacing(16)

        # Experience pills
        v.addWidget(section_label("EXPERIENCE LEVEL")); v.addSpacing(10)
        pill_host = QWidget(); flow = FlowLayout(pill_host, 7, 7)
        self._level_pills = []
        for name in ("Junior", "Mid", "Senior", "Lead"):
            p = self._pill(name)
            self._level_pills.append(p)
            flow.addWidget(p)
        v.addWidget(pill_host)
        v.addStretch()
        return panel

    # ---- filter change handlers ----
    def _set_query(self, **kw) -> None:
        self.store.query.update(kw)
        self._debounce.start()

    def _on_location_changed(self, text: str) -> None:
        self._set_query(location=text.strip())

    @staticmethod
    def _fmt_salary(v: int, is_max: bool = False) -> str:
        if is_max and v >= 250000:
            return "$250k+"
        return f"${v // 1000}k"

    def _on_salary_labels(self, lo: int, hi: int) -> None:
        self._smin.setText(self._fmt_salary(lo))
        self._smax.setText(self._fmt_salary(hi, is_max=True))

    def _on_salary_commit(self, lo: int, hi: int) -> None:
        self._set_query(salary_min=lo,
                        salary_max=(10_000_000 if hi >= 250000 else hi))

    def _on_date(self, value: str, btn) -> None:
        for b in self._date_buttons:
            b.setChecked(b is btn)
        self._set_query(posted_within=value)

    def _on_types_changed(self) -> None:
        selected = {cb.text() for cb in self._type_boxes if cb.isChecked()}
        self._set_query(job_types=selected)

    def _on_levels_changed(self) -> None:
        selected = {p.text() for p in self._level_pills if p.isChecked()}
        self._set_query(levels=selected)

    def _reset_filters(self) -> None:
        self.store.query.update(location="", remote_only=False, posted_within="any",
                                job_types=set(), levels=set(),
                                salary_min=0, salary_max=10_000_000)
        if hasattr(self, "_salary"):
            self._salary.set_values(0, 250000)
            self._on_salary_labels(0, 250000)
        self._filter_widgets["location"].setText("")
        self._filter_widgets["remote"].setChecked(False)
        for cb in self._type_boxes:
            cb.setChecked(False)
        for p in self._level_pills:
            p.setChecked(False)
        for b in self._date_buttons:
            b.setChecked(b.text() == "Any")
        self.store.apply_filters()

    def _checkbox(self, name: str) -> QCheckBox:
        cb = QCheckBox(name)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.setStyleSheet(
            f"QCheckBox{{color:{C.text_2};font-size:12.5px;background:transparent;}}"
            f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;}}"
            f"QCheckBox::indicator:unchecked{{border:1px solid {C.border_input};background:{C.bg_panel};}}"
            f"QCheckBox::indicator:checked{{background:{C.accent};border:1px solid {C.accent};}}")
        cb.toggled.connect(self._on_types_changed)
        return cb

    def _pill(self, name: str) -> QPushButton:
        b = QPushButton(name); b.setCheckable(True)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(
            f"QPushButton{{border:1px solid {C.border_input};background:{C.bg_panel};"
            f"color:{C.text_3};font-size:12px;border-radius:14px;padding:5px 12px;}}"
            f"QPushButton:checked{{background:{C.accent_bg};border-color:{C.accent};"
            f"color:{C.accent_ink};font-weight:600;}}")
        b.toggled.connect(self._on_levels_changed)
        return b

    # ---- search + rendering ----
    def _run_search(self) -> None:
        self.store.set_results_state("loading")
        self._render_results()
        self.store.set_status("Searching live sources…")
        kws = self.store.query.get("keywords") or None
        loc = self.store.query.get("location", "")
        worker = SearchWorker(self.store.profile, kws, loc)
        worker.signals.finished.connect(self._on_results)
        self.pool.start(worker)

    def _on_results(self, jobs, offline: bool, info) -> None:
        self._offline = offline
        self.store.set_raw_results(jobs)     # applies filters + emits results_changed
        self.store.set_results_state("loaded")
        info = info or {}
        ok = info.get("ok", [])
        if offline:
            self.store.set_status("Offline — showing cached results")
        else:
            now = __import__("datetime").datetime.now().strftime("%H:%M")
            src = ", ".join(ok) if ok else "sources"
            self.store.set_status(
                f"{len(jobs)} jobs · refreshed {now} · {len(ok)} sources: {src}")

    def _on_sort(self, key: str) -> None:
        self.store.sort_by = key
        self.store.apply_filters()

    def _active_filter_count(self) -> int:
        q = self.store.query
        n = 0
        n += bool(q.get("location"))
        n += bool(q.get("remote_only"))
        n += bool(q.get("job_types"))
        n += bool(q.get("levels"))
        n += q.get("posted_within", "any") != "any"
        n += q.get("salary_min", 0) > 0 or q.get("salary_max", 10_000_000) < 10_000_000
        return n

    def _clear_list(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                # stop any in-flight pop animation/timer before freeing the card
                t = getattr(w, "_pop_timer", None)
                if t is not None:
                    t.stop()
                a = getattr(w, "_pop_anim", None)
                if a is not None:
                    a.stop()
                w.setMaximumHeight(16777215)
                w.deleteLater()
        self._cards.clear()

    def _render_results(self, *_) -> None:
        self._clear_list()
        if self.store.results_state == "loading":
            self._count_label.setText("Searching…")
            for _ in range(4):
                self._list_layout.addWidget(self._skeleton_card())
            return
        jobs = self.store.results
        total = len(self.store.raw_results)
        nf = self._active_filter_count()
        suffix = f"  ·  {nf} filter{'s' if nf != 1 else ''} applied" if nf else ""
        if getattr(self, "_offline", False):
            suffix += "  ·  cached"
        shown = f"{len(jobs)} of {total} jobs" if nf and total else f"{len(jobs)} jobs"
        self._count_label.setText(shown + suffix)

        if not jobs:
            self._list_layout.addWidget(self._empty_state(total > 0))
            return
        self._card_anims = []
        for i, job in enumerate(jobs):
            card = JobCard(job, saved=self.store.is_saved(job.id),
                           selected=(job.id == self.store.selected_job_id),
                           viewed=(job.id in self.store.viewed_ids))
            card.clicked.connect(self._open_detail)
            card.save_toggled.connect(self._toggle_save)
            self._cards[job.id] = card
            self._list_layout.addWidget(card)
            self._pop_in(card, delay=min(i, 12) * 32)

    def _pop_in(self, card: QWidget, delay: int) -> None:
        """Staggered grow-in so results pop into place.

        Uses a maximumHeight animation (no QGraphicsOpacityEffect — that churns
        badly during rapid re-renders). The delay timer and the animation are
        BOTH children of the card, so a fresh render that deletes the card also
        deletes them; they can never fire against a freed widget.
        """
        card.setMaximumHeight(0)

        def start() -> None:
            if sip.isdeleted(card):
                return
            h = max(96, card.sizeHint().height())
            grow = QPropertyAnimation(card, b"maximumHeight", card)
            grow.setDuration(300); grow.setStartValue(0); grow.setEndValue(h)
            grow.setEasingCurve(QEasingCurve.Type.OutCubic)
            grow.finished.connect(
                lambda: None if sip.isdeleted(card) else card.setMaximumHeight(16777215))
            grow.start()
            card._pop_anim = grow

        timer = QTimer(card)
        timer.setSingleShot(True)
        timer.timeout.connect(start)
        card._pop_timer = timer
        timer.start(delay)

    def _empty_state(self, filtered_out: bool) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box); v.setContentsMargins(0, 80, 0, 0)
        v.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        v.setSpacing(14)
        loc = self.store.query.get("location", "")
        if filtered_out:
            msg = (f"No roles open to “{loc}” in this batch."
                   if loc else "No jobs match these filters.")
            sub = ("Free sources list mostly global remote roles — widen the "
                   "location or clear filters to see everything you're eligible for.")
        else:
            msg = "No jobs found for these keywords."
            sub = "Try a different keyword in the search bar above."
        title = QLabel(msg)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color:{C.text};font-size:15px;font-weight:600;background:transparent;")
        subl = QLabel(sub); subl.setWordWrap(True); subl.setFixedWidth(360)
        subl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subl.setStyleSheet(f"color:{C.text_3};font-size:12.5px;background:transparent;")
        v.addWidget(title); v.addWidget(subl)
        if filtered_out:
            btn = QPushButton("Clear filters"); btn.setProperty("kind", "secondary")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self._reset_filters)
            v.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        return box

    def _skeleton_card(self) -> QWidget:
        card = QFrame(); card.setObjectName("SkelCard")
        card.setStyleSheet(f"#SkelCard{{background:{C.bg_panel};border:1px solid {C.border};border-radius:6px;}}")
        card.setMaximumWidth(900)
        row = QHBoxLayout(card); row.setContentsMargins(17, 15, 17, 15); row.setSpacing(14)
        tile = QWidget(); tile.setFixedSize(40, 40)
        tile.setStyleSheet(f"background:{C.bg_skeleton};border-radius:5px;")
        row.addWidget(tile, alignment=Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout(); col.setSpacing(8)
        for w_, h_ in ((180, 11), (260, 9)):
            bar = QWidget(); bar.setFixedSize(w_, h_)
            bar.setStyleSheet(f"background:{C.bg_skeleton};border-radius:3px;")
            col.addWidget(bar)
        col.addStretch(); row.addLayout(col, 1)
        ring = QWidget(); ring.setFixedSize(46, 46)
        ring.setStyleSheet(f"background:{C.bg_skeleton};border-radius:23px;")
        row.addWidget(ring, alignment=Qt.AlignmentFlag.AlignTop)
        return card

    def _toggle_save(self, job_id: str) -> None:
        job = self.store.job_by_id(job_id)
        if job:
            self.store.toggle_saved(job)

    def _sync_saved(self) -> None:
        for jid, card in self._cards.items():
            card.set_saved(self.store.is_saved(jid))

    # ================= 1f/1g detail view =================
    def _open_detail(self, job_id: str) -> None:
        self.store.select_job(job_id)
        job = self.store.job_by_id(job_id)
        if not job:
            return
        # rebuild detail view
        idx = self.stack.indexOf(self._detail_view)
        self.stack.removeWidget(self._detail_view)
        self._anim_ring = None
        self._anim_bars = []
        self._detail_view = self._build_detail(job)
        self.stack.insertWidget(idx, self._detail_view)
        self.stack.setCurrentWidget(self._detail_view)
        pos = [j.id for j in self.store.results].index(job_id) + 1
        self.store.set_status(f"Job {pos} of {len(self.store.results)} · Source: {job.source}")
        self._play_detail_intro()

    def _play_detail_intro(self) -> None:
        """Fade the pane in and animate the match ring + factor bars."""
        eff = QGraphicsOpacityEffect(self._detail_view)
        self._detail_view.setGraphicsEffect(eff)
        self._fade = QPropertyAnimation(eff, b"opacity", self)
        self._fade.setDuration(180)
        self._fade.setStartValue(0.0); self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.finished.connect(lambda: self._detail_view.setGraphicsEffect(None))
        self._fade.start()
        if getattr(self, "_anim_ring", None) is not None:
            QTimer.singleShot(60, lambda: self._anim_ring.animate_to(self._anim_ring._score))
        for bar, pct in getattr(self, "_anim_bars", []):
            anim = QPropertyAnimation(bar, b"value", bar)
            anim.setDuration(640); anim.setStartValue(0); anim.setEndValue(pct)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            bar._anim = anim  # keep a reference
            anim.start()

    def _close_detail(self) -> None:
        if self.stack.currentWidget() is self._detail_view:
            self.stack.setCurrentWidget(self._results_view)
            self.store.set_status(
                f"{len(self.store.results)} results · Remotive")
            self._render_results()
            return True
        return False

    def _build_detail(self, job) -> QWidget:
        w = QWidget()
        body = QHBoxLayout(w); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)

        # ---- results rail ----
        rail = QWidget(); rail.setFixedWidth(300)
        rail.setStyleSheet(f"background:{C.bg_sidebar};border-right:1px solid {C.border};")
        rv = QVBoxLayout(rail); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(0)
        back = QPushButton(f"  Back to {len(self.store.results)} results")
        back.setIcon(icons.icon("chevron_left", 13, C.text_3))
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(
            f"QPushButton{{text-align:left;color:{C.text_3};font-size:12px;background:transparent;"
            f"border:none;border-bottom:1px solid {C.border};padding:11px 14px;}}")
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self._results_view))
        rv.addWidget(back)
        rail_scroll = QScrollArea(); rail_scroll.setWidgetResizable(True)
        rail_inner = QWidget(); ril = QVBoxLayout(rail_inner)
        ril.setContentsMargins(8, 8, 8, 8); ril.setSpacing(6); ril.setAlignment(Qt.AlignmentFlag.AlignTop)
        for j in self.store.results:
            ril.addWidget(self._rail_card(j, current=(j.id == job.id)))
        rail_scroll.setWidget(rail_inner)
        rv.addWidget(rail_scroll, 1)
        body.addWidget(rail)

        # ---- detail pane ----
        pane = QVBoxLayout(); pane.setContentsMargins(0, 0, 0, 0); pane.setSpacing(0)

        # header
        header = QWidget(); header.setStyleSheet(f"background:{C.bg_panel};border-bottom:1px solid {C.border};")
        hv = QVBoxLayout(header); hv.setContentsMargins(30, 22, 30, 18); hv.setSpacing(0)
        hrow = QHBoxLayout(); hrow.setSpacing(14)
        hrow.addWidget(LogoTile(job.company, 46, 6, 16), alignment=Qt.AlignmentFlag.AlignTop)
        hcol = QVBoxLayout(); hcol.setSpacing(4)
        t = QLabel(job.title); t.setWordWrap(True)
        t.setStyleSheet(f"color:{C.text};font-size:21px;font-weight:600;background:transparent;")
        m = QLabel(f"{job.company} · {job.location} ({job.mode}) · {job.type} · Posted {job.posted}")
        m.setWordWrap(True)
        m.setStyleSheet(f"color:{C.text_3};font-size:13px;background:transparent;")
        hcol.addWidget(t); hcol.addWidget(m)
        hrow.addLayout(hcol, 1)
        self._save_job_btn = QPushButton()
        self._save_job_btn.setProperty("kind", "secondary")
        self._save_job_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_job_btn.clicked.connect(lambda: self._toggle_save_detail(job))
        self._refresh_save_btn(job)
        hrow.addWidget(self._save_job_btn, alignment=Qt.AlignmentFlag.AlignTop)
        close = QPushButton()
        close.setIcon(icons.icon("x", 15, C.text_3))
        close.setFixedSize(30, 30)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setToolTip("Close  (Esc)")
        close.setStyleSheet(
            f"QPushButton{{border:1px solid {C.border};border-radius:15px;"
            f"background:{C.bg_panel};}}"
            f"QPushButton:hover{{background:{C.bg_fill};border-color:{C.border_input};}}")
        close.clicked.connect(self._close_detail)
        hrow.addWidget(close, alignment=Qt.AlignmentFlag.AlignTop)
        hv.addLayout(hrow)
        hv.addSpacing(16)
        hv.addWidget(ApplyBar(job.apply, job.title))
        pane.addWidget(header)

        # content: main + meta
        content = QHBoxLayout(); content.setContentsMargins(0, 0, 0, 0); content.setSpacing(0)
        # main
        main_scroll = QScrollArea(); main_scroll.setWidgetResizable(True)
        main = QWidget(); mv = QVBoxLayout(main); mv.setContentsMargins(30, 22, 30, 22); mv.setSpacing(0)
        mv.addWidget(self._section_heading("About the role"))
        about = QLabel(job.description); about.setWordWrap(True)
        about.setStyleSheet(f"color:{C.text_2};font-size:13px;line-height:1.65;background:transparent;")
        mv.addSpacing(8); mv.addWidget(about)

        mv.addSpacing(22); mv.addWidget(self._section_heading("Requirements"))
        mv.addSpacing(8)
        for met, text in job.requirements:
            rr = QHBoxLayout(); rr.setSpacing(9)
            ic = QLabel()
            if met:
                ic.setPixmap(icons.pixmap("check", 14, C.accent, 2.2))
                lbl = QLabel(text); lbl.setStyleSheet(f"color:{C.text_2};font-size:12.5px;background:transparent;")
            else:
                ic.setPixmap(icons.pixmap("x", 14, C.danger, 2.2))
                lbl = QLabel(f"{text}  (not on your resume)")
                lbl.setStyleSheet(f"color:{C.text_4};font-size:12.5px;background:transparent;")
            lbl.setWordWrap(True)
            rr.addWidget(ic, alignment=Qt.AlignmentFlag.AlignTop); rr.addWidget(lbl, 1)
            mv.addSpacing(10); mv.addLayout(rr)

        mv.addSpacing(22); mv.addWidget(self._section_heading("Benefits"))
        ben = QLabel(job.benefits); ben.setWordWrap(True)
        ben.setStyleSheet(f"color:{C.text_2};font-size:12.5px;line-height:1.65;background:transparent;")
        mv.addSpacing(8); mv.addWidget(ben)
        mv.addStretch()
        main_scroll.setWidget(main)
        content.addWidget(main_scroll, 1)

        # meta column
        content.addWidget(self._meta_column(job))
        pane.addLayout(content, 1)

        pane_wrap = QWidget(); pane_wrap.setLayout(pane); pane_wrap.setStyleSheet(f"background:{C.bg_app};")
        body.addWidget(pane_wrap, 1)
        return w

    def _explain(self, job) -> None:
        from ..services import ai
        self._why_btn.setVisible(False)
        self._why_panel.setVisible(True)
        base = ai.explain_local(self.store.profile, job)
        if ai.available():
            self._why_panel.setText(base + f"\n\n✨ Asking {ai.active_provider()} for a sharper take…")
            worker = ExplainWorker(self.store.profile, job)
            worker.signals.finished.connect(self._on_explained)
            self.pool.start(worker)
        else:
            self._why_panel.setText(base)

    def _on_explained(self, text: str, provider: str) -> None:
        tag = f"\n\n✨ Explained by {provider}" if provider != "local" else ""
        self._why_panel.setText(text + tag)

    def _refresh_save_btn(self, job) -> None:
        saved = self.store.is_saved(job.id)
        self._save_job_btn.setText("  Saved" if saved else "  Save Job")
        self._save_job_btn.setIcon(icons.icon(
            "bookmark_filled" if saved else "bookmark", 14,
            C.accent if saved else C.text_2))

    def _toggle_save_detail(self, job) -> None:
        self.store.toggle_saved(job)
        self._refresh_save_btn(job)

    def _section_heading(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{C.text};font-size:13.5px;font-weight:600;background:transparent;")
        return lbl

    def _rail_card(self, job, current: bool) -> QWidget:
        card = QFrame(); card.setCursor(Qt.CursorShape.PointingHandCursor)
        border = C.accent if current else C.border
        hover = C.accent if current else C.accent_border_strong
        card.setStyleSheet(
            f"QFrame{{background:{C.bg_panel};border:1px solid {border};border-radius:5px;}}"
            f"QFrame:hover{{border-color:{hover};}}")
        row = QHBoxLayout(card); row.setContentsMargins(12, 11, 12, 11); row.setSpacing(11)
        row.addWidget(LogoTile(job.company, 30, 4, 11), alignment=Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout(); col.setSpacing(2)
        t = QLabel(job.title); t.setStyleSheet(f"color:{C.text};font-size:12.5px;font-weight:600;background:transparent;")
        s = QLabel(f"{job.company} · {job.location}")
        s.setStyleSheet(f"color:{C.text_4};font-size:11px;background:transparent;")
        col.addWidget(t); col.addWidget(s)
        row.addLayout(col, 1)
        arc, txt = ring_colors(job.score)
        sc = QLabel(str(job.score))
        sc.setStyleSheet(f"color:{txt};font-family:'{F.mono}';font-size:11px;font-weight:600;background:transparent;")
        row.addWidget(sc, alignment=Qt.AlignmentFlag.AlignTop)
        card.mouseReleaseEvent = lambda e, jid=job.id: self._open_detail(jid)
        return card

    def _meta_column(self, job) -> QWidget:
        col = QWidget()
        col.setStyleSheet(f"background:{C.bg_app};")
        v = QVBoxLayout(col); v.setContentsMargins(20, 22, 20, 22); v.setSpacing(0)

        v.addWidget(section_label("MATCH BREAKDOWN")); v.addSpacing(12)
        rr = QHBoxLayout(); rr.setSpacing(12)
        ring = MatchRing(0, 60, 6, 14)
        ring._score = job.score      # target; animate_to sweeps 0 -> here
        self._anim_ring = ring
        rr.addWidget(ring)
        verdict = QLabel("Strong on skills,\nlight on tooling")
        verdict.setStyleSheet(f"color:{C.text_3};font-size:11.5px;background:transparent;")
        rr.addWidget(verdict); rr.addStretch()
        v.addLayout(rr); v.addSpacing(16)

        f = job.factors
        for label, (val, pct) in (("Skills", f.skills), ("Seniority", f.seniority),
                                  ("Location", f.location), ("Tooling", f.tooling)):
            v.addLayout(self._factor_bar(label, val, pct)); v.addSpacing(12)

        # "Why this score?" — local explanation, AI-upgraded when a key is set
        self._why_btn = QPushButton("  Why this score?")
        self._why_btn.setIcon(icons.icon("sparkle", 13, C.accent))
        self._why_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._why_btn.setStyleSheet(
            f"QPushButton{{color:{C.accent};border:1px solid {C.accent_border};"
            f"border-radius:6px;padding:6px 10px;font-size:12px;font-weight:600;"
            f"background:{C.accent_bg_soft};text-align:left;}}"
            f"QPushButton:hover{{background:{C.accent_bg};}}")
        self._why_btn.clicked.connect(lambda: self._explain(job))
        v.addSpacing(2); v.addWidget(self._why_btn)
        self._why_panel = QLabel(""); self._why_panel.setWordWrap(True)
        self._why_panel.setVisible(False)
        self._why_panel.setStyleSheet(
            f"color:{C.text_2};font-size:12px;background:{C.accent_bg_soft};"
            f"border:1px solid {C.accent_border};border-radius:6px;padding:10px 11px;")
        v.addSpacing(8); v.addWidget(self._why_panel)

        v.addSpacing(8); v.addWidget(rule(C.border)); v.addSpacing(16)
        v.addWidget(section_label("COMPANY")); v.addSpacing(8)
        comp = QLabel(f"{job.company}\nFintech · 500–1000\nFounded 2016 · Lagos + remote")
        comp.setStyleSheet(f"color:{C.text_2};font-size:12.5px;background:transparent;")
        v.addWidget(comp); v.addSpacing(6)
        link = QLabel(f"{job.company.lower()}.com ↗")
        link.setStyleSheet(f"color:{C.accent};font-size:12px;background:transparent;")
        v.addWidget(link)

        v.addSpacing(16); v.addWidget(rule(C.border)); v.addSpacing(16)
        v.addWidget(section_label("SALARY")); v.addSpacing(8)
        if job.salary_min:
            sal = QLabel(job.salary_label)
            sal.setStyleSheet(f"color:{C.text};font-family:'{F.mono}';font-size:15px;font-weight:600;background:transparent;")
            note = QLabel(f"Listed by employer · {job.currency}")
        else:
            sal = QLabel("—")
            sal.setStyleSheet(f"color:{C.text};font-family:'{F.mono}';font-size:15px;font-weight:600;background:transparent;")
            note = QLabel("Not listed by employer")
        note.setStyleSheet(f"color:{C.text_4};font-size:11.5px;background:transparent;")
        v.addWidget(sal); v.addWidget(note)
        v.addStretch()

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFixedWidth(286)
        scroll.setWidget(col)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{C.bg_app};border-left:1px solid {C.border};}}")
        return scroll

    def _factor_bar(self, label: str, value: str, pct: int) -> QVBoxLayout:
        col = QVBoxLayout(); col.setSpacing(5)
        row = QHBoxLayout()
        l = QLabel(label); l.setStyleSheet(f"color:{C.text_2};font-size:11.5px;background:transparent;")
        val = QLabel(value); val.setStyleSheet(f"color:{C.text_2};font-family:'{F.mono}';font-size:11.5px;background:transparent;")
        row.addWidget(l); row.addStretch(); row.addWidget(val)
        col.addLayout(row)
        bar = QProgressBar(); bar.setTextVisible(False); bar.setFixedHeight(4)
        bar.setRange(0, 100); bar.setValue(0)
        fill = C.warn if pct < 50 else C.accent
        bar.setStyleSheet(
            f"QProgressBar{{background:{C.rule};border:none;border-radius:2px;}}"
            f"QProgressBar::chunk{{background:{fill};border-radius:2px;}}")
        col.addWidget(bar)
        self._anim_bars.append((bar, pct))
        return col
