"""Self-check for every variant's theme.json against tools/palette.json and known-ui-keys.txt.

Usage: python3 -I tools/ui/check_theme.py   (exit 1 on any failure)
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THEMES = os.path.join(ROOT, "src/main/resources/themes")
KNOWN = os.path.join(ROOT, "src/test/resources/known-ui-keys.txt")
palette_file = json.load(open(os.path.join(ROOT, "tools/palette.json")))
PALETTE = {}
BLUE_PATHS = [re.compile(p) for p in palette_file["restricted"]["blue"]["themePaths"]]

HEX = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
NON_COLOR = re.compile(r"^(-?\d+(\.\d+)?(,-?\d+)*|com\.[\w.$]+)$")
errors = []


def no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    for k in {k for k in keys if keys.count(k) > 1}:
        errors.append(f"duplicate key: {k}")
    return dict(pairs)


def flatten(node, prefix=""):
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten(value, path)
        else:
            yield path, value


def luminance(hex_color):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(x, y):
    hi, lo = sorted((luminance(x), luminance(y)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check_color(path, value, colors):
    """Resolve a value; returns the #rrggbb it paints with, or None for non-colors/transparent."""
    if isinstance(value, (bool, int, float)):
        return None
    if value in colors:
        value = colors[value]
    elif not HEX.match(value):
        if not NON_COLOR.match(value):
            errors.append(f"{path}: '{value}' is neither a palette color, a palette name nor a known non-color")
        return None
    rgb, alpha = value[:7].lower(), value[7:].lower()
    if alpha == "00":
        return None
    if rgb not in PALETTE.values():
        errors.append(f"{path}: {value} is not a palette color")
        return None
    if rgb == PALETTE["blue"] and not any(p.search(path) for p in BLUE_PATHS):
        errors.append(f"{path}: blue outside icons")
    bg = PALETTE["bg0"]
    if contrast(rgb, bg) > contrast(PALETTE[palette_file["rules"]["maxContrastColor"]], bg) + 1e-9:
        errors.append(f"{path}: {value} contrasts more with bg0 than fg0")
    return rgb


def check(meta):
    PALETTE.clear()
    PALETTE.update({k: v.lower() for k, v in meta["colors"].items()})
    try:
        theme = json.load(open(os.path.join(THEMES, meta["stem"] + ".theme.json")), object_pairs_hook=no_duplicates)
    except json.JSONDecodeError as e:
        errors.append(f"invalid JSON: {e}")
        return

    colors = theme.get("colors", {})
    for name, value in colors.items():
        if PALETTE.get(name) != str(value).lower():
            errors.append(f"colors.{name}: {value} does not match palette.json")

    for key, expected in (("name", meta["name"]), ("dark", meta["dark"]), ("author", "gipo355"),
                          ("parentTheme", meta["parentTheme"]),
                          ("editorScheme", f"/themes/{meta['stem']}.xml")):
        if theme.get(key) != expected:
            errors.append(f"{key}: {theme.get(key)!r}, expected {expected!r}")

    known = set(open(KNOWN).read().split())
    ui = list(flatten(theme["ui"]))
    used = set()
    for key, value in ui:
        if key not in known:
            errors.append(f"ui.{key}: not in known-ui-keys.txt")
        rgb = check_color(f"ui.{key}", value, colors)
        if rgb:
            used.add(rgb)

    icons = list(flatten({"icons": theme.get("icons", {}),
                          "iconColorsOnSelection": theme.get("iconColorsOnSelection", {})}))
    for key, value in icons:
        check_color(key, value, colors)

    print(f"{meta['name']}: ui keys: {len(ui)}, icon keys: {len(icons)}, distinct ui colors: {len(used)}")


def main():
    for key, meta in palette_file["variants"].items():
        before = len(errors)
        check(meta)
        errors[before:] = [f"{key}: {e}" for e in errors[before:]]
    if errors:
        for e in errors:
            print("FAIL", e)
        sys.exit(1)
    print("OK: JSON valid, palette-only colors, blue only under icons, nothing contrasts more with bg0 than fg0, "
          "all ui keys known")


if __name__ == "__main__":
    main()
