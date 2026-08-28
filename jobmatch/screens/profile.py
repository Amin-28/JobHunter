"""Screen 1c — Profile Summary (editable)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .. import icons
from ..models import Skill
from ..theme import C, F
from ..widgets.chips import SkillChip
from ..widgets.common import rule, section_label
from ..widgets.flow_layout import FlowLayout


class InitialsTile(QWidget):
    def __init__(self, text: str, size: int = 52) -> None:
        super().__init__()
        self._text = text
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(C.accent_bg))
        p.drawRoundedRect(0, 0, self._size, self._size, 6, 6)
        f = QFont(F.sans); f.setPixelSize(18); f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f); p.setPen(QColor(C.accent))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)
        p.end()


class ProfileScreen(QWidget):
    search_requested = pyqtSignal()

    def __init__(self, store) -> None:
        super().__init__()
        self.store = store
        self.store.profile_changed.connect(self._rebuild)

        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        self._host = QWidget()
        scroll.setWidget(self._host)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._built = False

    def on_enter(self) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
        p = self.store.profile
        if p is None:
            return
        # clear
        old = self._host.layout()
        if old is not None:
            QWidget().setLayout(old)
        lay = QVBoxLayout(self._host)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(0)

        # header row
        head = QHBoxLayout()
        htext = QVBoxLayout(); htext.setSpacing(4)
        title = QLabel("Here's what we read")
        title.setStyleSheet(f"color:{C.text};font-size:21px;font-weight:600;background:transparent;")
        sub = QLabel("Fix anything that looks off — matching quality depends on it.")
        sub.setStyleSheet(f"color:{C.text_3};font-size:12.5px;background:transparent;")
        htext.addWidget(title); htext.addWidget(sub)
        head.addLayout(htext); head.addStretch()
        head.addWidget(self._confidence_pill(p.confidence),
                       alignment=Qt.AlignmentFlag.AlignTop)
        lay.addLayout(head)

        # card
        card = QWidget(); card.setObjectName("Card"); card.setMaximumWidth(860)
        cl = QVBoxLayout(card); cl.setContentsMargins(26, 24, 26, 24); cl.setSpacing(0)

        # identity
        idrow = QHBoxLayout(); idrow.setSpacing(14)
        idrow.addWidget(InitialsTile(_initials(p.name)))
        idcol = QVBoxLayout(); idcol.setSpacing(2)
        name = QLabel(p.name)
        name.setStyleSheet(f"color:{C.text};font-size:19px;font-weight:600;background:transparent;")
        role = QLabel(f"{p.current_title} · {p.location.split(' · ')[0]}")
        role.setStyleSheet(f"color:{C.text_3};font-size:13px;background:transparent;")
        idcol.addWidget(name); idcol.addWidget(role)
        idrow.addLayout(idcol); idrow.addStretch()
        edit_all = QPushButton("  Edit all"); edit_all.setProperty("kind", "secondary")
        edit_all.setIcon(icons.icon("pencil", 13, C.text_2))
        edit_all.setCursor(Qt.CursorShape.PointingHandCursor)
        idrow.addWidget(edit_all, alignment=Qt.AlignmentFlag.AlignTop)
        cl.addLayout(idrow)

        # AI-derived awareness (shown only when an AI key enriched the parse)
        if p.summary:
            summ = QLabel("“" + p.summary + "”"); summ.setWordWrap(True)
            summ.setStyleSheet(f"color:{C.text_2};font-size:12.5px;background:transparent;")
            cl.addSpacing(14); cl.addWidget(summ)
        if p.domains:
            dhost = QWidget(); dflow = FlowLayout(dhost, 7, 7)
            for d in p.domains[:6]:
                chip = QLabel(d)
                chip.setStyleSheet(
                    f"color:{C.accent_ink};background:{C.accent_bg};border:1px solid "
                    f"{C.accent_border};border-radius:3px;padding:3px 9px;font-size:11.5px;")
                dflow.addWidget(chip)
            cl.addSpacing(11); cl.addWidget(dhost)

        cl.addSpacing(22); cl.addWidget(rule()); cl.addSpacing(22)

        # field grid
        grid = QGridLayout(); grid.setHorizontalSpacing(34); grid.setVerticalSpacing(20)
        grid.addLayout(self._field("CURRENT TITLE", p.current_title), 0, 0)
        grid.addLayout(self._target_field("TARGET TITLE", p.target_title), 0, 1)
        grid.addLayout(self._field("YEARS OF EXPERIENCE", p.years,
                                   suffix=f"({p.years_span})"), 1, 0)
        grid.addLayout(self._field("LOCATION", p.location), 1, 1)
        cl.addLayout(grid)

        cl.addSpacing(22); cl.addWidget(rule()); cl.addSpacing(20)

        # skills
        srow = QHBoxLayout()
        srow.addWidget(section_label("KEY SKILLS"))
        detected = QLabel(f"{len(p.skills)} detected · click a chip to remove")
        detected.setStyleSheet(f"color:{C.text_disabled};font-size:11.5px;background:transparent;")
        srow.addSpacing(8); srow.addWidget(detected); srow.addStretch()
        cl.addLayout(srow)

        cl.addSpacing(12)
        chip_host = QWidget()
        self._chip_flow = FlowLayout(chip_host, hspacing=8, vspacing=8)
        self._render_chips()
        cl.addWidget(chip_host)

        lay.addSpacing(20); lay.addWidget(card)

        # footer
        foot = QHBoxLayout(); foot.setSpacing(14)
        search = QPushButton("  Search Jobs"); search.setProperty("kind", "primary")
        search.setIcon(icons.icon("search", 15, "#FFFFFF"))
        search.setStyleSheet(search.styleSheet())  # keep kind styling
        search.setCursor(Qt.CursorShape.PointingHandCursor)
        search.clicked.connect(self.search_requested.emit)
        helper = QLabel("Will search 6 boards using 9 keywords from your profile.")
        helper.setStyleSheet(f"color:{C.text_4};font-size:12px;background:transparent;")
        foot.addWidget(search); foot.addWidget(helper); foot.addStretch()
        lay.addSpacing(22); lay.addLayout(foot); lay.addStretch()

        self._sync_status()

    def _sync_status(self) -> None:
        if self.store.profile_dirty_fields:
            f = next(iter(self.store.profile_dirty_fields))
            self.store.set_status(f'Profile ready · Unsaved edit in "{f}"')
        else:
            self.store.set_status("Profile ready · 12 skills detected")

    # ---- pieces ----
    def _confidence_pill(self, level: str) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w); l.setContentsMargins(11, 6, 11, 6); l.setSpacing(7)
        dot_color = C.status_ok_dot if level == "high" else C.warn
        text = ("Extraction confidence: high" if level == "high"
                else "Extraction confidence: review the fields below")
        dot = QLabel("●"); dot.setStyleSheet(f"color:{dot_color};font-size:8px;background:transparent;")
        lbl = QLabel(text); lbl.setStyleSheet(f"color:{C.text_2};font-size:11.5px;background:transparent;")
        l.addWidget(dot); l.addWidget(lbl)
        w.setStyleSheet(f"background:{C.bg_panel};border:1px solid {C.border};border-radius:5px;")
        return w

    def _field(self, label: str, value: str, suffix: str = "") -> QVBoxLayout:
        col = QVBoxLayout(); col.setSpacing(7)
        col.addWidget(section_label(label))
        row = QHBoxLayout(); row.setSpacing(6)
        val = QLabel(value)
        val.setStyleSheet(f"color:{C.text};font-size:14px;background:transparent;")
        row.addWidget(val)
        if suffix:
            sfx = QLabel(suffix)
            sfx.setStyleSheet(f"color:{C.text_5};font-size:12px;background:transparent;")
            row.addWidget(sfx)
        row.addStretch()
        col.addLayout(row)
        return col

    def _target_field(self, label: str, value: str) -> QVBoxLayout:
        col = QVBoxLayout(); col.setSpacing(7)
        head = QHBoxLayout(); head.setSpacing(6)
        head.addWidget(section_label(label))
        self._edit_hint = QLabel("· editing")
        self._edit_hint.setStyleSheet(f"color:{C.warn};font-size:10px;font-weight:500;background:transparent;")
        self._edit_hint.setVisible(False)
        head.addWidget(self._edit_hint); head.addStretch()
        col.addLayout(head)

        self._target_row = QHBoxLayout(); self._target_row.setSpacing(8)
        self._target_value = QLabel(value or "—")
        self._target_value.setStyleSheet(f"color:{C.text};font-size:14px;background:transparent;")
        self._target_value.setCursor(Qt.CursorShape.PointingHandCursor)
        self._target_value.mousePressEvent = lambda e: self._begin_edit()
        self._target_edit = QLineEdit(value)
        self._target_edit.setVisible(False)
        self._target_edit.setFixedWidth(180)
        self._target_edit.returnPressed.connect(self._commit_edit)
        self._save_btn = QPushButton("Save")
        self._save_btn.setVisible(False)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setStyleSheet(
            f"QPushButton{{background:{C.accent};color:#fff;border-radius:5px;"
            f"padding:0 13px;font-size:12px;}}QPushButton:hover{{background:{C.accent_hover};}}")
        self._save_btn.clicked.connect(self._commit_edit)
        self._target_row.addWidget(self._target_value)
        self._target_row.addWidget(self._target_edit)
        self._target_row.addWidget(self._save_btn)
        self._target_row.addStretch()
        col.addLayout(self._target_row)
        return col

    def _begin_edit(self) -> None:
        self._target_value.setVisible(False)
        self._target_edit.setVisible(True); self._save_btn.setVisible(True)
        self._edit_hint.setVisible(True)
        self._target_edit.setFocus(); self._target_edit.selectAll()
        self.store.profile_dirty_fields.add("Target title")
        self._sync_status()

    def _commit_edit(self) -> None:
        val = self._target_edit.text().strip() or "—"
        self.store.profile.target_title = val
        self._target_value.setText(val)
        self._target_value.setVisible(True)
        self._target_edit.setVisible(False); self._save_btn.setVisible(False)
        self._edit_hint.setVisible(False)
        self.store.profile_dirty_fields.discard("Target title")
        self._sync_status()

    def _render_chips(self) -> None:
        self._chip_flow.clear()
        for sk in self.store.profile.skills:
            chip = SkillChip(sk.name, low=(sk.confidence == "low"))
            chip.removed.connect(self._remove_skill)
            self._chip_flow.addWidget(chip)
        add = QPushButton("+ Add skill")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.setStyleSheet(
            f"QPushButton{{color:{C.text_4};border:1px dashed {C.border_input};"
            f"border-radius:14px;padding:5px 12px;font-size:12.5px;background:transparent;}}"
            f"QPushButton:hover{{border-color:{C.accent};color:{C.accent};}}")
        add.clicked.connect(self._add_skill)
        self._chip_flow.addWidget(add)

    def _remove_skill(self, name: str) -> None:
        self.store.profile.skills = [s for s in self.store.profile.skills if s.name != name]
        self._render_chips()

    def _add_skill(self) -> None:
        self.store.profile.skills.append(Skill("New skill"))
        self._render_chips()


def _initials(name: str) -> str:
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()
