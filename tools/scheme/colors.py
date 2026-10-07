"""Palette access, color math and the deterministic Darcula -> palette mapping."""

import colorsys
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PALETTE_FILE = os.path.join(REPO, "tools", "palette.json")

# What a translucent Darcula color sits on when it is painted.
DARCULA_BG = "2b2b2b"

FG_GREYS = ["grey0", "grey1", "grey2", "fg0"]
BG_GREYS = ["bg0", "bg1", "bg_current_word", "bg3", "bg5"]

# Hue (degrees) -> accent. 345-15 wraps through 0.
HUE_BANDS = [
    (15, "red"),
    (40, "orange"),
    (65, "yellow"),
    (100, "green"),
    (200, "aqua"),
    (260, "tan"),
    (345, "purple"),
    (360, "red"),
]

# A hued fill becomes the dim tint of its accent, never the accent itself.
TINT = {
    "red": "bg_visual_red",
    "orange": "bg_visual_yellow",
    "yellow": "bg_visual_yellow",
    "green": "bg_visual_green",
    "aqua": "bg_visual_blue",
    "tan": "bg_visual_blue",
    "blue": "bg_visual_blue",
    "purple": "bg_visual_purple",
}

GREY_SATURATION = 0.15


def load_palette():
    with open(PALETTE_FILE) as f:
        data = json.load(f)
    colors = {k: v.lstrip("#").lower() for k, v in data["colors"].items()}
    blue_keys = [re.compile(p) for p in data["restricted"]["blue"]["schemeKeys"]]
    return colors, blue_keys


PALETTE, BLUE_KEYS = load_palette()


def blue_allowed(key):
    return any(p.search(key) for p in BLUE_KEYS)


def rgb(hex6):
    return tuple(int(hex6[i : i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(hex6):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in rgb(hex6))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def flatten(raw, under=DARCULA_BG):
    """Composites an 8-digit (alpha) color over the background it is painted on."""
    if len(raw) != 8:
        return raw
    alpha = int(raw[6:8], 16) / 255
    fg, bg = rgb(raw[:6]), rgb(under)
    return "".join(f"{round((a * alpha + b * (1 - alpha)) * 255):02x}" for a, b in zip(fg, bg))


def _nearest(hex6, names):
    lum = luminance(hex6)
    return min(names, key=lambda n: (abs(luminance(PALETTE[n]) - lum), names.index(n)))


def accent(hex6, key):
    h, _, s = colorsys.rgb_to_hls(*rgb(hex6))
    if s < GREY_SATURATION:
        return None
    deg = h * 360
    name = next(n for limit, n in HUE_BANDS if deg < limit)
    if name == "tan" and blue_allowed(key):
        return "blue"
    return name


def map_fg(raw, key):
    hex6 = flatten(raw)
    name = accent(hex6, key)
    return name if name else _nearest(hex6, FG_GREYS)


def map_bg(raw, key, greys=None):
    hex6 = flatten(raw)
    if greys and hex6 in greys:
        return greys[hex6]
    name = accent(hex6, key)
    return TINT[name] if name else _nearest(hex6, BG_GREYS)


BG_HINT = re.compile(r"(?i)background|ROW|hover|pressed|track|thumb|SELECTION|STRIPE|NOTIFICATION")
DARK = 0.1


def map_color_key(raw, key, greys=None):
    """<colors> entries carry no field name, so the role comes from the key name, then from lightness."""
    if BG_HINT.search(key):
        return map_bg(raw, key, greys)
    if luminance(flatten(raw)) < DARK:
        return map_bg(raw, key, greys)
    return map_fg(raw, key)
