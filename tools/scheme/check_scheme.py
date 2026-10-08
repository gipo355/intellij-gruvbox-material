"""Self-check for the generated editor schemes, one per palette variant. Exits non-zero on any failure.

    python3 -I tools/scheme/check_scheme.py
"""

import collections
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import colors as C  # noqa: E402
import palette as P  # noqa: E402
from generate import REQUIRED, scheme_path  # noqa: E402

COLOR_FIELDS = ("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR")
LEVEL_SET = re.compile(r"^(.*?(?:RAINBOW_COLOR|COLUMN_COLORING_ATTRIBUTE_|^RAINBOW_COLOR))(\d+)$")
ACCENTS = 7  # distinct accents available for a level set (blue is reserved)
DIFF_KEYS = {"ins": "DIFF_INSERTED", "del": "DIFF_DELETED", "mod": "DIFF_MODIFIED", "conf": "DIFF_CONFLICT"}
DIFF_FIELDS = {"block": "BACKGROUND", "line": "FOREGROUND"}


def check_diff(attrs, palette, rules, fail):
    """The section-2 diff bounds, on the tints the scheme actually writes."""
    bg, fg = "#" + palette["bg0"], "#" + palette["fg0"]
    by_kind = {}
    for kind, field in DIFF_FIELDS.items():
        spec = rules[kind]
        floor = spec["contrastRatio"] * P.contrast(fg, bg)
        tints = by_kind[kind] = {}
        for hue, key in DIFF_KEYS.items():
            value = (attrs.get(key) or {}).get(field)
            if not value:
                fail(f"{key}.{field}: not set")
                continue
            tints[hue] = "#" + value
            de = P.delta_e(tints[hue], bg)
            if not spec["deltaE"][0] <= de <= spec["deltaE"][1]:
                fail(f"{key}.{field}: deltaE {de:.3f} vs bg0 outside {spec['deltaE']}")
            if P.contrast(fg, tints[hue]) < floor:
                fail(f"{key}.{field}: fg0 contrast {P.contrast(fg, tints[hue]):.2f} < {floor:.2f}")
        vals = list(tints.values())
        pair = min((P.delta_e(x, y) for i, x in enumerate(vals) for y in vals[i + 1:]), default=0)
        if pair < spec["pairwise"]:
            fail(f"diff {kind}: min pairwise deltaE {pair:.3f} < {spec['pairwise']}")
        lightness = [P.oklab(t)[0] for t in vals]
        if kind == "block" and lightness and max(lightness) - min(lightness) > 0.01:
            fail(f"diff block: lightness offsets differ by {max(lightness) - min(lightness):.3f} (> 0.01, rounding)")
    for hue, key in DIFF_KEYS.items():
        word, line = by_kind["block"].get(hue), by_kind["line"].get(hue)
        if word and line and P.delta_e(word, line) < rules["wordVsLine"]:
            fail(f"{key}: word {word} vs line {line} deltaE {P.delta_e(word, line):.3f} < {rules['wordVsLine']}")


def check(variant, rules):
    failures = []
    fail = failures.append
    meta = C.VARIANTS[variant]
    C.use(variant)
    by_hex = {}
    for k, v in C.PALETTE.items():
        by_hex.setdefault(v, k)
    bg0 = C.PALETTE["bg0"]
    max_contrast = C.contrast(C.PALETTE[rules["maxContrastColor"]], bg0)
    output = scheme_path(variant)

    root = ET.parse(output).getroot()
    if (root.tag, root.get("name"), root.get("version"), root.get("parent_scheme")) != (
        "scheme", meta["name"], "142", meta["parentScheme"]):
        fail(f"unexpected root {root.tag} {root.attrib}")

    colors, attrs = {}, {}
    used = []  # (key, field, value)
    for o in root.find("colors").findall("option"):
        k = o.get("name")
        if k in colors:
            fail(f"duplicate color {k}")
        colors[k] = o.get("value")
        used.append((k, None, o.get("value")))
    for o in root.find("attributes").findall("option"):
        k = o.get("name")
        if k in attrs:
            fail(f"duplicate attribute {k}")
        v = o.find("value")
        fields = None if v is None else {f.get("name"): f.get("value") for f in v.findall("option")}
        attrs[k] = fields
        if o.get("baseAttributes") is not None:
            fail(f"{k}: baseAttributes (IntelliJ ignores the link target; write the value)")
        if v is None:
            fail(f"{k}: no value")
        for f, val in (fields or {}).items():
            if f == "FONT_TYPE":
                fail(f"{k}: FONT_TYPE")
            elif f in COLOR_FIELDS:
                used.append((k, f, val))
            elif f != "EFFECT_TYPE":
                fail(f"{k}: unexpected field {f}")
    if "FONT_TYPE" in open(output).read():
        fail("FONT_TYPE appears in the file")

    empty = 0
    for k, f, val in used:
        where = f"{k}{'.' + f if f else ''}"
        if val == "":
            if f is not None:
                fail(f"{where}: empty attribute field")
            empty += 1
            continue
        if not re.fullmatch(r"[0-9a-f]{6}", val):
            fail(f"{where}: not 6-digit lowercase hex: {val}")
            continue
        name = by_hex.get(val)
        if name is None:
            fail(f"{where}: {val} not in palette")
            continue
        if name == "blue" and not C.blue_allowed(k):
            fail(f"{where}: blue outside restricted keys")
        if C.contrast(val, bg0) > max_contrast + 1e-9:
            fail(f"{where}: {name} contrasts more with bg0 than fg0")

    check_diff(attrs, C.PALETTE, rules["diff"], fail)

    required = [l.strip() for l in open(REQUIRED[meta["dark"]]) if l.strip() and not l.startswith("#")]
    missing = [k for k in required if k not in colors and k not in attrs]
    for k in missing:
        fail(f"required key not defined: {k}")

    terminal = collections.Counter(
        "colored" if any(f in COLOR_FIELDS for f in attrs[k]) else "explicitly empty"
        for k in required if attrs.get(k) is not None)

    # Level sets (rainbow brackets, CSV columns): neighbours differ, the first ACCENTS levels are distinct.
    sets = collections.defaultdict(dict)
    for k, fields in attrs.items():
        m = LEVEL_SET.match(k)
        if m and fields and "FOREGROUND" in fields and "BLACK_LIST" not in k:
            sets[m.group(1)][int(m.group(2))] = fields["FOREGROUND"]
    for name, levels in sorted(sets.items()):
        seq = [levels[i] for i in sorted(levels)]
        head = seq[:ACCENTS]
        if len(set(head)) != len(head) or any(a == b for a, b in zip(seq, seq[1:])):
            fail(f"level set {name} not distinguishable: {[by_hex.get(c) for c in seq]}")

    print(f"{variant}: {len(colors)} colors, {len(attrs)} attributes; required {len(required)}, missing {len(missing)}")
    print(f"colors used: {len(used) - empty} values, all checked against {len(C.PALETTE)} palette entries; "
          f"{empty} intentionally empty color values")
    print(f"effective attributes: {dict(sorted(terminal.items()))}")
    print(f"level sets checked: {len(sets)}")
    return failures


def main():
    with open(C.PALETTE_FILE) as f:
        rules = json.load(f)["rules"]
    failures = [f"{v}: {f}" for v in C.VARIANTS for f in check(v, rules)]
    if failures:
        print(f"FAIL ({len(failures)}):")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
