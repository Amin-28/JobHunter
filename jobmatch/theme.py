"""Design tokens and QSS theme for JobMatch AI.

All colors, typography and geometry come straight from the design handoff
(README.md, "Design Tokens"). Import ``C`` for colors, ``F`` for font families,
build the global stylesheet with :func:`stylesheet`, and register bundled fonts
with :func:`load_fonts`.
"""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase


# token name -> (light, dark). Everything routes through here so a theme switch
# is a single reassignment. Widgets that paint in code read C.* at paint time;
# widgets with baked inline stylesheets are rebuilt on switch (main_window).
_TOKENS: dict[str, tuple[str, str]] = {
    # Accent / teal system
    "accent":               ("#0F6E6A", "#17A99D"),
    "accent_2":             ("#149B8F", "#25C6B7"),
    "accent_hover":         ("#0A5350", "#0F847B"),
    "accent_ink":           ("#0B5B58", "#8FDACF"),
    "accent_bg":            ("#E2EFEE", "#173430"),
    "accent_bg_soft":       ("#F7FAFA", "#14211F"),
    "accent_border":        ("#CFE0DF", "#274B45"),
    "accent_border_strong": ("#B9CDCB", "#34605A"),
    # gradient stops
    "sidebar_top":          ("#EEF3F3", "#191D22"),
    "sidebar_bottom":       ("#F4F6F8", "#15181C"),
    "hero_glow":            ("#EAF3F2", "#182422"),
    # Text ramp
    "text":                 ("#1B2027", "#E7EAEE"),
    "text_2":               ("#4C545E", "#B7BEC7"),
    "text_3":               ("#6B7481", "#949BA4"),
    "text_4":               ("#8B939D", "#6E767F"),
    "text_5":               ("#98A0AA", "#6E767F"),
    "text_disabled":        ("#AAB1BA", "#565E67"),
    # Surfaces
    "bg_app":               ("#FBFBFC", "#131619"),
    "bg_panel":             ("#FFFFFF", "#1B1F24"),
    "bg_chrome":            ("#E9EBEE", "#101316"),
    "bg_sidebar":           ("#F5F6F8", "#16191D"),
    "bg_fill":              ("#F2F4F6", "#252A30"),
    "bg_skeleton":          ("#EFF1F4", "#22262B"),
    "bg_skeleton_2":        ("#F4F6F8", "#2A2F35"),
    # Borders / rules
    "border":               ("#E2E6EA", "#2A2F36"),
    "border_input":         ("#CFD5DB", "#3A414A"),
    "border_button":        ("#D3D8DE", "#3A414A"),
    "border_window":        ("#CFD4DA", "#000000"),
    "border_chrome":        ("#D3D8DE", "#0A0C0E"),
    "rule":                 ("#ECEEF1", "#252A30"),
    # Semantic — warn
    "warn":                 ("#C07F2C", "#E0A24A"),
    "warn_ink":             ("#8A6320", "#E8BB6E"),
    "warn_bg":              ("#FDF6EA", "#2A2214"),
    "warn_border":          ("#F0E0C4", "#4A3B20"),
    "warn_border_dashed":   ("#E3CFA4", "#4A3B20"),
    # Semantic — danger
    "danger":               ("#C0503C", "#E17059"),
    "danger_bg":            ("#FDF1EF", "#2A1915"),
    "danger_border":        ("#F3D3CD", "#4A2C25"),
    # Semantic — ok
    "ok":                   ("#3F7A51", "#5CA872"),
    "ok_ink":               ("#31633F", "#84C596"),
    "ok_bg":                ("#F5F9F6", "#16241A"),
    "ok_border":            ("#CFE3D4", "#274A2F"),
    # Semantic — mail
    "mail":                 ("#33587F", "#6E9BCB"),
    "mail_icon":            ("#3A5F8A", "#6E9BCB"),
    "mail_bg":              ("#F6F8FB", "#171F28"),
    "mail_border":          ("#D3DDE8", "#2B3A49"),
    # Misc
    "status_ok_dot":        ("#3F9C58", "#4FB06A"),
}


class C:
    """Active color tokens — populated by :func:`apply_theme`."""


_current_theme = "light"


def apply_theme(name: str) -> None:
    global _current_theme
    _current_theme = "dark" if name == "dark" else "light"
    idx = 1 if _current_theme == "dark" else 0
    for token, pair in _TOKENS.items():
        setattr(C, token, pair[idx])


def current_theme() -> str:
    return _current_theme


apply_theme("light")   # ensure C has attributes at import time


# Company logo tile fills (fixed muted palette). White initials on top.
COMPANY_TILE_PALETTE = [
    "#1B2027",  # Paystack
    "#3A4B6D",  # Flutterwave
    "#7A5230",  # Kobo360
    "#5B6A5B",  # Andela
    "#6B4B6B",  # Moniepoint
]


def company_color(name: str) -> str:
    """Deterministically map a company name to one of the five tile tones."""
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return COMPANY_TILE_PALETTE[h % len(COMPANY_TILE_PALETTE)]


def initials(name: str) -> str:
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


class F:
    """Font family names (resolved after :func:`load_fonts`)."""

    sans = "IBM Plex Sans"
    mono = "IBM Plex Mono"


def load_fonts() -> None:
    """Register bundled TTFs if present; otherwise fall back gracefully.

    The handoff ships IBM Plex Sans/Mono as bundled TTFs. We look for them under
    ``jobmatch/assets/fonts``; if none are found we fall back to the platform
    UI font and a monospace family so the app still runs.
    """
    import os

    font_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
    loaded_families: set[str] = set()
    if os.path.isdir(font_dir):
        for fn in os.listdir(font_dir):
            if fn.lower().endswith((".ttf", ".otf")):
                fid = QFontDatabase.addApplicationFont(os.path.join(font_dir, fn))
                for fam in QFontDatabase.applicationFontFamilies(fid):
                    loaded_families.add(fam)

    available = set(QFontDatabase.families())
    if "IBM Plex Sans" not in available and "IBM Plex Sans" not in loaded_families:
        # Fall back to a clean platform UI sans.
        for cand in ("Segoe UI", "Inter", "Helvetica Neue", "Arial"):
            if cand in available:
                F.sans = cand
                break
    if "IBM Plex Mono" not in available and "IBM Plex Mono" not in loaded_families:
        for cand in ("Cascadia Mono", "Consolas", "Courier New", "monospace"):
            if cand in available:
                F.mono = cand
                break


def font(size: float, weight: int = 400, mono: bool = False,
         letter_spacing: float = 0.0) -> QFont:
    """Build a QFont from the design scale.

    ``size`` is in px (the design unit); ``letter_spacing`` is in em.
    """
    f = QFont(F.mono if mono else F.sans)
    f.setPixelSize(round(size))
    qt_weight = {
        400: QFont.Weight.Normal,
        500: QFont.Weight.Medium,
        600: QFont.Weight.DemiBold,
        700: QFont.Weight.Bold,
    }.get(weight, QFont.Weight.Normal)
    f.setWeight(qt_weight)
    if letter_spacing:
        # Qt uses percentage for PercentageSpacing; em -> percent.
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing,
                            100 + letter_spacing * 100)
    return f


def stylesheet() -> str:
    """Global application QSS built from the tokens above."""
    return f"""
    * {{
        font-family: "{F.sans}";
        color: {C.text};
        outline: none;
    }}
    QWidget {{ background: transparent; }}

    /* ---- Window shell ---- */
    #Window {{
        background: {C.bg_app};
        border: 1px solid {C.border_window};
        border-radius: 7px;
    }}
    #TitleBar {{
        background: {C.bg_chrome};
        border-bottom: 1px solid {C.border_chrome};
    }}
    #TitleLabel {{ color: {C.text}; }}
    #WinBtn {{
        color: #7A828C;
        background: transparent;
        border: none;
        font-size: 15px;
    }}
    #WinBtn:hover {{ color: {C.text}; }}
    #WinClose:hover {{ color: {C.danger}; }}

    #Sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {C.sidebar_top}, stop:1 {C.sidebar_bottom});
        border-right: 1px solid {C.border};
    }}
    #Content {{ background: {C.bg_app}; }}
    #StatusBar {{
        background: {C.bg_sidebar};
        border-top: 1px solid {C.border};
    }}
    #StatusLabel {{ color: {C.text_4}; }}

    /* ---- Nav rows (icon-based, see widgets/nav.py) ---- */
    #NavGroupLabel {{ color: {C.text_5}; }}
    #NavRow {{ border-radius: 9px; background: transparent; }}
    #NavRow[state="idle"]:hover {{ background: rgba(15,110,106,0.07); }}
    #NavRow[state="current"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {C.accent_bg}, stop:1 rgba(226,239,238,0.35));
    }}

    /* ---- Cards / panels ---- */
    #Card, #Panel {{
        background: {C.bg_panel};
        border: 1px solid {C.border};
        border-radius: 8px;
    }}
    #Toolbar {{
        background: {C.bg_panel};
        border-bottom: 1px solid {C.border};
    }}
    #FilterSidebar {{
        background: {C.bg_sidebar};
        border-right: 1px solid {C.border};
    }}

    /* ---- Buttons ---- */
    QPushButton[kind="primary"] {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {C.accent_2}, stop:1 {C.accent});
        color: #FFFFFF;
        border: 1px solid {C.accent};
        border-radius: 6px;
        padding: 9px 20px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton[kind="primary"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {C.accent}, stop:1 {C.accent_hover});
        border-color: {C.accent_hover};
    }}
    QPushButton[kind="primary"]:disabled {{
        background: #B7C7C6; border-color: #B7C7C6;
    }}
    QPushButton[kind="secondary"] {{
        background: {C.bg_panel};
        color: {C.text_2};
        border: 1px solid {C.border_button};
        border-radius: 5px;
        padding: 7px 15px;
        font-size: 12.5px;
    }}
    QPushButton[kind="secondary"]:hover {{ border-color: {C.text_disabled}; }}
    QPushButton[kind="ghost"] {{
        background: transparent; border: none; color: {C.accent};
        font-size: 12px;
    }}
    QPushButton[kind="ghost"]:hover {{ color: {C.accent_hover}; }}

    /* ---- Inputs ---- */
    QLineEdit {{
        background: {C.bg_panel};
        border: 1px solid {C.border_input};
        border-radius: 5px;
        padding: 7px 9px;
        selection-background-color: {C.accent_bg};
        selection-color: {C.accent_ink};
    }}
    QLineEdit:focus {{ border: 1.5px solid {C.accent}; }}

    QComboBox {{
        background: {C.bg_panel};
        border: 1px solid {C.border_input};
        border-radius: 4px;
        padding: 5px 10px;
        font-size: 12px;
        color: {C.text_2};
    }}
    QComboBox:hover {{ border-color: {C.text_disabled}; }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background: {C.bg_panel};
        border: 1px solid {C.border};
        selection-background-color: {C.accent_bg};
        selection-color: {C.accent_ink};
        outline: none;
    }}

    /* ---- Scrollbars ---- */
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #D3D8DE; border-radius: 4px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #BFC6CE; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
