"""Renders the tray icon: a small ring gauge colored by severity.

AppIndicator hosts generally cache an icon by file path and only redraw when
the path changes, not when its mtime changes. So instead of overwriting one
file, we alternate between two paths on every refresh to force a reload.
"""

import math
import os

import cairo

CACHE_DIR = os.path.expanduser("~/.cache/claude-usage-monitor")
SIZE = 32

COLORS = {
    "normal": (0.20, 0.70, 0.35),
    "warning": (0.90, 0.60, 0.10),
    "critical": (0.85, 0.20, 0.20),
    "error": (0.55, 0.55, 0.55),
}

_toggle = False


def _color_for(percent, severity):
    if severity in ("rejected", "critical"):
        return COLORS["critical"]
    if severity in ("warning", "allowed_warning"):
        return COLORS["warning"]
    if percent is None:
        return COLORS["error"]
    if percent >= 90:
        return COLORS["critical"]
    if percent >= 70:
        return COLORS["warning"]
    return COLORS["normal"]


def render(percent, severity="normal"):
    """Draws a ring gauge PNG and returns its path. `percent` may be None (error state)."""
    global _toggle
    os.makedirs(CACHE_DIR, exist_ok=True)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, SIZE, SIZE)
    ctx = cairo.Context(surface)

    cx, cy, radius = SIZE / 2, SIZE / 2, SIZE / 2 - 3
    line_width = 4.5

    ctx.set_line_width(line_width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    ctx.set_source_rgba(1, 1, 1, 0.25)
    ctx.arc(cx, cy, radius, 0, 2 * math.pi)
    ctx.stroke()

    r, g, b = _color_for(percent, severity)
    frac = 0 if percent is None else max(0.0, min(1.0, percent / 100.0))
    start = -math.pi / 2
    end = start + frac * 2 * math.pi

    ctx.set_source_rgb(r, g, b)
    if frac > 0:
        ctx.arc(cx, cy, radius, start, end)
        ctx.stroke()
    else:
        # Draw a small dot so an empty/error gauge is still visible
        ctx.arc(cx, cy, 1.5, 0, 2 * math.pi)
        ctx.set_source_rgb(r, g, b)
        ctx.fill()

    _toggle = not _toggle
    path = os.path.join(CACHE_DIR, f"icon_{'a' if _toggle else 'b'}.png")
    surface.write_to_png(path)
    return path
