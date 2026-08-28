"""Inline line-icon set (Feather/Lucide style, 24x24 viewBox).

Icons are stored as SVG path bodies and rendered to a ``QPixmap``/``QIcon`` at
any size and stroke color via :func:`pixmap` / :func:`icon`. This mirrors the
handoff's guidance to render a small bundled SVG set with the color passed per
state.
"""
from __future__ import annotations

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

# Each value is the inner markup of a 0 0 24 24 SVG (stroke-based).
_PATHS: dict[str, str] = {
    "upload": '<path d="M12 15V3M12 3l-4 4M12 3l4 4"/><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "pencil": '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "bookmark": '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>',
    "bookmark_filled": '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" fill="CURRENT"/>',
    "chevron_left": '<path d="M15 18l-6-6 6-6"/>',
    "chevron_down": '<path d="M6 9l6 6 6-6"/>',
    "envelope": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18"/>',
    "form": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "external": '<path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><circle cx="12" cy="8" r="0.6" fill="CURRENT" stroke="none"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "x": '<path d="M18 6L6 18M6 6l12 12"/>',
    "kebab": '<circle cx="12" cy="5" r="1.4" fill="CURRENT" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="CURRENT" stroke="none"/><circle cx="12" cy="19" r="1.4" fill="CURRENT" stroke="none"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "copy": '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    "file": '<path d="M14 3v5h5"/><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3.5" cy="6" r="1" fill="CURRENT" stroke="none"/><circle cx="3.5" cy="12" r="1" fill="CURRENT" stroke="none"/><circle cx="3.5" cy="18" r="1" fill="CURRENT" stroke="none"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-3.5 3.6-6 8-6s8 2.5 8 6"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 12h18"/>',
    "sparkle": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    "filter": '<path d="M3 5h18l-7 8v6l-4-2v-4z"/>',
    "sliders": '<path d="M4 6h10M18 6h2M4 12h2M10 12h10M4 18h8M16 18h4"/><circle cx="16" cy="6" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="14" cy="18" r="2"/>',
    "check_circle": '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
    "map_pin": '<path d="M12 21s7-5.7 7-11a7 7 0 1 0-14 0c0 5.3 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "moon": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/>',
    "key": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.5 12.5L20 3M16 7l3 3M14 9l2 2"/>',
}


def svg_string(name: str, color: str, stroke: float = 2.0) -> str:
    body = _PATHS[name].replace("CURRENT", color)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


def pixmap(name: str, size: int, color: str, stroke: float = 2.0,
           dpr: float = 2.0) -> QPixmap:
    """Render an icon to a crisp pixmap at ``size`` px in ``color``."""
    renderer = QSvgRenderer(QByteArray(svg_string(name, color, stroke).encode()))
    phys = max(1, int(round(size * dpr)))
    pm = QPixmap(phys, phys)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(p, QRectF(0, 0, phys, phys))   # fill the full physical bitmap
    p.end()
    pm.setDevicePixelRatio(dpr)                    # then scale down for display
    return pm


def icon(name: str, size: int, color: str, stroke: float = 2.0) -> QIcon:
    ic = QIcon(pixmap(name, size, color, stroke))
    return ic
