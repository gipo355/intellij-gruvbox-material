"""Derives tools/palette.json (every variant's role -> hex) and the runtime copy src/main/resources/gruvbox/palette.json.

    python3 -I tools/palette.py

Base: sainnhe/gruvbox-material autoload/gruvbox_material.vim (commit 11d779b), get_palette(background, 'material')
for dark soft/medium/hard and light soft. On top of it, every number below is computed, not picked:
  - dark accents: red and purple lowered in chroma at the same hue (one OKLCH lightness band), blue -> tan in syntax;
  - light accents: each upstream accent moved to the same contrast against bg0, chroma capped, so none stands out;
  - tints (search, visual, usages, nvim diff tints): the OKLCH offset each has from dark-soft bg0, applied to the
    variant's bg0 (lightness offset mirrored on light: tints darker than the background);
  - diff tints: bg0 moved by one lightness offset and shifted towards each hue in a/b, so every tint sits the same
    OKLab distance from bg0; the largest offset (least chroma) that still keeps the four hues apart and the text readable wins;
  - keyword choices (runtime only): an OKLCH grid per family on dark; on light the same hue and chroma, each entry's
    lightness solved so its contrast share of fg0's matches its dark-soft counterpart.
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "palette.json")
RUNTIME = os.path.join(ROOT, "src", "main", "resources", "gruvbox", "palette.json")

# get_palette(background, 'material'): palette1 (backgrounds) per background, palette2/3 (foregrounds) per &background.
UPSTREAM_BG = {
    "dark-soft": {
        "bg_dim": "#252423", "bg0": "#32302f", "bg1": "#3c3836", "bg_current_word": "#45403d",
        "bg_statusline2": "#46413e", "bg3": "#504945", "bg_statusline3": "#5b534d", "bg5": "#665c54",
    },
    "dark-medium": {
        "bg_dim": "#1b1b1b", "bg0": "#282828", "bg1": "#32302f", "bg_current_word": "#3c3836",
        "bg_statusline2": "#3a3735", "bg3": "#45403d", "bg_statusline3": "#504945", "bg5": "#5a524c",
    },
    "dark-hard": {
        "bg_dim": "#141617", "bg0": "#1d2021", "bg1": "#282828", "bg_current_word": "#32302f",
        "bg_statusline2": "#32302f", "bg3": "#3c3836", "bg_statusline3": "#504945", "bg5": "#504945",
    },
    "light-soft": {
        "bg_dim": "#ebdbb2", "bg0": "#f2e5bc", "bg1": "#eddeb5", "bg_current_word": "#ebdbb2",
        "bg_statusline2": "#ebdbb2", "bg3": "#e6d5ae", "bg_statusline3": "#dac9a5", "bg5": "#d5c4a1",
    },
}
UPSTREAM_FG = {
    True: {
        "fg0": "#d4be98", "grey0": "#7c6f64", "grey1": "#928374", "grey2": "#a89984",
        "red": "#ea6962", "orange": "#e78a4e", "yellow": "#d8a657", "green": "#a9b665",
        "aqua": "#89b482", "purple": "#d3869b", "blue": "#7daea3",
    },
    False: {
        "fg0": "#654735", "grey0": "#a89984", "grey1": "#928374", "grey2": "#7c6f64",
        "red": "#c14a4a", "orange": "#c35e0a", "yellow": "#b47109", "green": "#6c782e",
        "aqua": "#4c7a5d", "purple": "#945e80", "blue": "#45707a",
    },
}

# User-approved dark tuning: same hues, lower chroma (red was the chroma outlier); tan replaces blue in syntax.
DARK_ACCENTS = {"red": "#e67d76", "purple": "#d48da0", "tan": "#c4a67e"}
ACCENTS = ["red", "orange", "yellow", "green", "aqua", "tan", "purple", "blue"]

# Tints as the user's nvim paints them on dark-soft bg0 (bg_visual_*/bg_diff_* are upstream dark soft).
REFERENCE_TINTS = {
    "bg_visual_red": "#543937", "bg_visual_yellow": "#574833", "bg_visual_green": "#424a3e",
    "bg_visual_blue": "#404946", "bg_visual_purple": "#4b3e45", "bg_diff_red": "#472322", "bg_diff_green": "#3d4220",
    "diff_add": "#343a24", "diff_delete": "#442a27", "diff_change": "#3b3420", "diff_text": "#4d4024",
    "search": "#4a5229", "search_current": "#7a3d35", "substitute": "#6b5428", "write_usage": "#4a3a2a",
}

# Light: accents at one contrast against bg0 (dark accents span 4.7-6.0 under fg0's 7.3), chroma capped.
LIGHT_ACCENT_CONTRAST = 5.0
LIGHT_CHROMA_CAP = 0.11
LIGHT_COMMENT_CONTRAST = 4.0

DIFF = {
    "hues": {"ins": 125, "del": 25, "mod": 72, "conf": 335},
    # Lint bounds (asserted by ThemeLintTest) and the solver's aim inside them. contrastRatio: fg0's contrast on the
    # tint over fg0's contrast on bg0, so the floor follows each variant's text contrast.
    "block": {"deltaE": [0.06, 0.09], "pairwise": 0.038, "contrastRatio": 0.74,
              "aim": {"deltaE": 0.08, "pairwise": 0.042, "contrastRatio": 0.75}},
    "line": {"deltaE": [0.035, 0.05], "pairwise": 0.025, "contrastRatio": 0.87,
             "aim": {"deltaE": 0.036, "pairwise": 0.028, "contrastRatio": 0.88}},
    # Minimum OKLab distance between each hue's block tint (changed words) and its line tint.
    "wordVsLine": 0.035,
}
DIFF_KINDS = ("block", "line")

VARIANTS = {
    "dark-soft": {"id": "f869fff9-c7e3-4656-b344-d228bf76a6c3", "name": "Gruvbox Material Islands",
                  "stem": "GruvboxMaterialIslands", "dark": True},
    "dark-medium": {"id": "275611fd-a504-467e-9c31-f0470ba50762", "name": "Gruvbox Material Islands Medium",
                    "stem": "GruvboxMaterialIslandsMedium", "dark": True},
    "dark-hard": {"id": "117eb1e1-e632-4fba-b735-691361c815df", "name": "Gruvbox Material Islands Hard",
                  "stem": "GruvboxMaterialIslandsHard", "dark": True},
    "light-soft": {"id": "653f45a7-3ec3-431d-a49e-dfba1290c9bf", "name": "Gruvbox Material Islands Light",
                   "stem": "GruvboxMaterialIslandsLight", "dark": False},
}
# Runtime keyword-colour choices: rows bright -> ghost (most to least visible), columns by strength.
KEYWORDS = {
    "brightness": ["Bright", "Mid", "Mid-dark", "Dark", "Darker", "Faint", "Ghost"],
    "strength": ["Vivid", "Muted", "Soft"],
    "lightness": [0.74, 0.71, 0.68, 0.65, 0.62, 0.57, 0.52],
    "families": {
        "red": ("Red", 25, [0.12, 0.09, 0.065]),
        "orange": ("Orange", 56, [0.12, 0.09, 0.065]),
        "clay": ("Clay", 44.5, [0.09, 0.065, 0.045]),
        "stone": ("Stone", 90, [0.05, 0.035, 0.022]),
        "slate": ("Slate", 240, [0.045, 0.03, 0.018]),
    },
}

PARENTS = {True: ("ExperimentalDark", "Darcula"), False: ("ExperimentalLightWithLightHeader", "Default")}

ROLE_ORDER = (["fg0", "grey0", "grey1", "grey2"] + ACCENTS + list(UPSTREAM_BG["dark-soft"]) + list(REFERENCE_TINTS)
              + [f"diff_{k}" for k in DIFF["hues"]] + [f"diff_{k}_line" for k in DIFF["hues"]])


# ---------------------------------------------------------------- color math (OKLab, WCAG contrast)


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def to_hex(channels):
    return "#" + "".join(f"{round(min(1.0, max(0.0, c)) * 255):02x}" for c in channels)


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gamma(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklab(hex_color):
    r, g, b = (_lin(c) for c in rgb(hex_color))
    l = math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _oklab_to_linear(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def lch(hex_color):
    L, a, b = oklab(hex_color)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def from_oklab(L, a, b):
    """-> hex, or None when the color is outside sRGB."""
    lin = _oklab_to_linear(L, a, b)
    if not all(-1e-6 <= c <= 1 + 1e-6 for c in lin):
        return None
    return to_hex(_gamma(min(1.0, max(0.0, c))) for c in lin)


def from_lch(L, C, h):
    """-> hex; chroma is lowered until the color fits sRGB."""
    for _ in range(200):
        out = from_oklab(L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h)))
        if out:
            return out
        C *= 0.98
    raise SystemExit(f"cannot fit L={L} C={C} h={h} into sRGB")


def delta_e(x, y):
    return math.dist(oklab(x), oklab(y))


def luminance(hex_color):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(x, y):
    hi, lo = sorted((luminance(x), luminance(y)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------- derivation


def at_contrast(hex_color, bg, target, chroma_cap=None):
    """Same hue (chroma capped), lightness moved until the contrast against bg is target."""
    _, C, h = lch(hex_color)
    if chroma_cap is not None:
        C = min(C, chroma_cap)
    return lch_at_contrast(C, h, bg, target)


def lch_at_contrast(C, h, bg, target):
    bg_l = lch(bg)[0]
    lo, hi = (0.0, bg_l) if bg_l > 0.5 else (bg_l, 1.0)
    for _ in range(60):
        mid = (lo + hi) / 2
        darker_than_bg = bg_l > 0.5
        if (contrast(from_lch(mid, C, h), bg) > target) == darker_than_bg:
            lo = mid
        else:
            hi = mid
    return from_lch((lo + hi) / 2, C, h)


def tint(reference, ref_bg, bg, dark):
    L, C, h = lch(reference)
    dl = L - lch(ref_bg)[0]
    return from_lch(lch(bg)[0] + (dl if dark else -dl), C, h)


def diff_tint(bg, dl, target, hue):
    """bg0 moved by dl in lightness and towards hue in a/b, target OKLab distance in all (None outside sRGB)."""
    L0, a0, b0 = oklab(bg)
    shift = math.sqrt(target * target - dl * dl)
    return from_oklab(L0 + dl, a0 + shift * math.cos(math.radians(hue)), b0 + shift * math.sin(math.radians(hue)))


def diff_set(bg, fg, dark, spec):
    """-> {suffix: hex}: the largest lightness offset whose tints meet every aim on the rounded hex. Where bg0 sits
    near the sRGB edge (light), the distance from bg0 may grow towards its bound and the pairwise aim relax halfway
    to its bound to keep the hues apart."""
    aim = spec["aim"]
    floor = aim["contrastRatio"] * contrast(fg, bg)
    top = round(spec["deltaE"][1] * 1000) - 4
    for pairwise, target in [(p, t) for p in (aim["pairwise"], (aim["pairwise"] + spec["pairwise"]) / 2)
                             for t in range(round(aim["deltaE"] * 1000), top + 1, 2)]:
        for step in range(target, -1, -1):
            dl = step / 1000 * (1 if dark else -1)
            tints = {k: diff_tint(bg, dl, target / 1000, h) for k, h in DIFF["hues"].items()}
            if None in tints.values():
                continue
            ok = all(spec["deltaE"][0] <= delta_e(t, bg) <= spec["deltaE"][1]
                     and contrast(fg, t) >= floor for t in tints.values())
            values = list(tints.values())
            pairs = [delta_e(x, y) for i, x in enumerate(values) for y in values[i + 1:]]
            if ok and min(pairs) >= pairwise:
                return tints
    raise SystemExit(f"no diff tint set on {bg} meets {aim}")


def variant_colors(key, meta):
    dark = meta["dark"]
    bgs = UPSTREAM_BG[key]
    bg0 = bgs["bg0"]
    fg = dict(UPSTREAM_FG[dark])
    colors = {"fg0": fg["fg0"], "grey0": fg["grey0"], "grey1": fg["grey1"], "grey2": fg["grey2"]}
    if dark:
        accents = {k: fg[k] for k in ACCENTS if k != "tan"}
        accents.update(DARK_ACCENTS)
    else:
        upstream = {**{k: fg[k] for k in ACCENTS if k != "tan"},
                    "tan": from_lch(lch(fg["yellow"])[0], lch(DARK_ACCENTS["tan"])[1], lch(DARK_ACCENTS["tan"])[2])}
        accents = {k: at_contrast(v, bg0, LIGHT_ACCENT_CONTRAST, LIGHT_CHROMA_CAP) for k, v in upstream.items()}
        colors["grey2"] = at_contrast(fg["grey2"], bg0, LIGHT_COMMENT_CONTRAST)
    colors.update({k: accents[k] for k in ACCENTS})
    colors.update(bgs)
    ref_bg = UPSTREAM_BG["dark-soft"]["bg0"]
    colors.update({k: tint(v, ref_bg, bg0, dark) for k, v in REFERENCE_TINTS.items()})
    for kind, suffix in (("block", ""), ("line", "_line")):
        for k, v in diff_set(bg0, colors["fg0"], dark, DIFF[kind]).items():
            colors[f"diff_{k}{suffix}"] = v
    return {k: colors[k] for k in ROLE_ORDER}


def keyword_table(dark, bg, fg):
    """{brightness, strength, families: {key: {label, colors: rows x strengths}}} for one variant."""
    soft = UPSTREAM_BG["dark-soft"]["bg0"]
    reference = contrast(UPSTREAM_FG[True]["fg0"], soft)
    families = {}
    for key, (label, h, chromas) in KEYWORDS["families"].items():
        rows = []
        for L in KEYWORDS["lightness"]:
            row = [from_lch(L, C, h) for C in chromas]
            if not dark:
                row = [lch_at_contrast(C, h, bg, contrast(d, soft) / reference * contrast(fg, bg))
                       for C, d in zip(chromas, row)]
            rows.append(row)
        families[key] = {"label": label, "colors": rows}
    return {"brightness": KEYWORDS["brightness"], "strength": KEYWORDS["strength"], "families": families}


def build():
    variants = {}
    for key, meta in VARIANTS.items():
        theme_parent, scheme_parent = PARENTS[meta["dark"]]
        variants[key] = {**meta, "parentTheme": theme_parent, "parentScheme": scheme_parent,
                         "colors": variant_colors(key, meta)}
    soft = variants["dark-soft"]["colors"]
    drift = {k: (v, soft[k]) for k, v in REFERENCE_TINTS.items() if soft[k] != v}
    if drift:
        raise SystemExit(f"dark-soft tints do not round-trip: {drift}")
    return {
        "$comment": "Generated by tools/palette.py: every color the theme may use, per variant. Generators map into "
                    "role names; ThemeLintTest rejects anything outside the variant's roles. Base: "
                    "sainnhe/gruvbox-material, foreground=material. Blue is remapped to tan everywhere except the "
                    "keys listed in restricted.",
        "variants": variants,
        "restricted": {
            "$comment": "blue is allowed only here: ANSI blue keeps terminal output legible, and blue icons keep "
                        "class/interface glyphs distinct. Patterns are regexes on the scheme attribute/color key, "
                        "or on the theme.json path.",
            "blue": {"schemeKeys": ["^CONSOLE_BLUE.*", "^CONSOLE_CYAN.*"], "themePaths": ["^icons\\."]},
        },
        "rules": {
            "$comment": "No color anywhere may contrast more with the variant's bg0 than fg0 does: bright glyphs and "
                        "blocks are what bloom. No bold or italic in the editor scheme. diff: bounds for the diff "
                        "tints (OKLab distance from bg0 and between the four, fg0 contrast on each, as a ratio "
                        "of fg0's contrast on bg0; wordVsLine: distance between each hue's block and line tint).",
            "maxContrastColor": "fg0",
            "fontTypes": "none",
            "diff": {k: {f: x for f, x in v.items() if f != "aim"} if k in DIFF_KINDS else v for k, v in DIFF.items()},
        },
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def report(data):
    for key, v in data["variants"].items():
        c = v["colors"]
        bg = c["bg0"]
        accents = [c[k] for k in ACCENTS if k != "blue"]
        crs = [contrast(a, bg) for a in accents]
        print(f"{key:12s} TEXT {contrast(c['fg0'], bg):.2f}  comment {contrast(c['grey2'], bg):.2f}  "
              f"accents {min(crs):.2f}-{max(crs):.2f}  L {min(lch(a)[0] for a in accents):.3f}-"
              f"{max(lch(a)[0] for a in accents):.3f}  max chroma {max(lch(a)[1] for a in accents):.3f}")
        for suffix in ("", "_line"):
            tints = {k: c[f"diff_{k}{suffix}"] for k in DIFF["hues"]}
            vals = list(tints.values())
            pairs = min(delta_e(x, y) for i, x in enumerate(vals) for y in vals[i + 1:])
            cells = "  ".join(f"{k} {t} dE {delta_e(t, bg):.3f} cr {contrast(c['fg0'], t):.2f}" for k, t in tints.items())
            print(f"  diff{suffix or '_block':6s} {cells}  min pair {pairs:.3f}")


def main():
    data = build()
    write_json(OUT, data)
    write_json(RUNTIME, {"variants": {
        v["id"]: {"name": v["name"], "dark": v["dark"], "editorScheme": v["name"], "roles": v["colors"],
                  "keywords": keyword_table(v["dark"], v["colors"]["bg0"], v["colors"]["fg0"])}
        for v in data["variants"].values()}})
    report(data)


if __name__ == "__main__":
    main()
