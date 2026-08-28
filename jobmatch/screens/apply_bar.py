"""Apply-channel bar (README 1g) — restyles from the parsed apply target."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)

from .. import icons
from ..models import Apply
from ..theme import C, F

# type -> visual config
_VARIANTS = {
    "website": dict(bg=C.accent_bg_soft, border=C.accent_border, icon="globe",
                    icon_color=C.accent, label="APPLY ON COMPANY SITE",
                    label_color=C.accent_ink, btn="Visit Website", btn_color=C.accent,
                    dashed=False),
    "email":   dict(bg=C.mail_bg, border=C.mail_border, icon="envelope",
                    icon_color=C.mail_icon, label="APPLY BY EMAIL",
                    label_color=C.mail, btn="Send Email", btn_color=C.mail, dashed=False),
    "form":    dict(bg=C.ok_bg, border=C.ok_border, icon="form",
                    icon_color=C.ok, label="APPLICATION FORM",
                    label_color=C.ok_ink, btn="Open Application Form", btn_color=C.ok,
                    dashed=False),
    "none":    dict(bg="#FAFAFA", border=C.border_button, icon="info",
                    icon_color=C.text_5, label="NO APPLY LINK DETECTED",
                    label_color=C.text_4, btn="Open source listing",
                    btn_color=None, dashed=True),
}


class ApplyBar(QWidget):
    def __init__(self, apply: Apply, job_title: str = "", parent=None) -> None:
        super().__init__(parent)
        self.apply = apply
        cfg = _VARIANTS[apply.type]
        dash = "dashed" if cfg["dashed"] else "solid"
        self.setStyleSheet(
            f"ApplyBar{{background:{cfg['bg']};border:1px {dash} {cfg['border']};"
            f"border-radius:6px;}}")

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(16)

        ic = QLabel(); ic.setPixmap(icons.pixmap(cfg["icon"], 19, cfg["icon_color"], 2.0))
        row.addWidget(ic, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout(); col.setSpacing(5)
        label = QLabel(cfg["label"])
        label.setStyleSheet(
            f"color:{cfg['label_color']};font-size:10px;font-weight:600;"
            f"letter-spacing:0.8px;background:transparent;")
        col.addWidget(label)
        if apply.type == "none":
            value = QLabel("Open the original listing to find how to apply.")
            value.setStyleSheet(f"color:{C.text_3};font-size:12.5px;background:transparent;")
        else:
            value = QLabel(apply.value)
            value.setStyleSheet(
                f"color:{C.text_2};font-family:'{F.mono}';font-size:12.5px;background:transparent;")
        col.addWidget(value)
        row.addLayout(col)
        row.addStretch()

        # secondary buttons per variant
        if apply.type == "email":
            copy = QPushButton("Copy"); copy.setProperty("kind", "secondary")
            copy.setCursor(Qt.CursorShape.PointingHandCursor)
            copy.clicked.connect(lambda: QApplication.clipboard().setText(apply.value))
            row.addWidget(copy)

        # primary action
        if apply.type == "none":
            btn = QPushButton("Open source listing")
            btn.setProperty("kind", "secondary")
        else:
            btn = QPushButton(cfg["btn"])
            btn.setStyleSheet(
                f"QPushButton{{background:{cfg['btn_color']};color:#fff;border:none;"
                f"border-radius:5px;padding:9px 17px;font-size:13px;font-weight:600;}}"
                f"QPushButton:hover{{background:{cfg['btn_color']};}}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._activate(job_title))
        row.addWidget(btn)

    def _activate(self, job_title: str) -> None:
        a = self.apply
        if a.type == "website" or a.type == "form":
            QDesktopServices.openUrl(QUrl(a.value))
        elif a.type == "email":
            subject = f"Application — {job_title}".replace(" ", "%20")
            QDesktopServices.openUrl(QUrl(f"mailto:{a.value}?subject={subject}"))
