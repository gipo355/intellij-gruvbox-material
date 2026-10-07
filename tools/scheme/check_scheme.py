"""Self-check for the generated editor scheme. Exits non-zero on any failure.

    python3 -I tools/scheme/check_scheme.py
"""

import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import colors as C  # noqa: E402
from generate import OUTPUT, REQUIRED  # noqa: E402

COLOR_FIELDS = ("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR")
LEVEL_SET = re.compile(r"^(.*?(?:RAINBOW_COLOR|COLUMN_COLORING_ATTRIBUTE_|^RAINBOW_COLOR))(\d+)$")
ACCENTS = 7  # distinct accents available for a level set (blue is reserved)


def main():
    failures = []
    fail = failures.append
    by_hex = {v: k for k, v in C.PALETTE.items()}
    max_lum = C.luminance(C.PALETTE["fg0"])

    root = ET.parse(OUTPUT).getroot()
    if (root.tag, root.get("name"), root.get("version"), root.get("parent_scheme")) != (
        "scheme", "Gruvbox Material Islands", "142", "Darcula"):
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
    if "FONT_TYPE" in open(OUTPUT).read():
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
        if C.luminance(val) > max_lum + 1e-9:
            fail(f"{where}: {name} brighter than fg0")

    required = [l.strip() for l in open(REQUIRED) if l.strip() and not l.startswith("#")]
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

    print(f"scheme: {len(colors)} colors, {len(attrs)} attributes; required {len(required)}, missing {len(missing)}")
    print(f"colors used: {len(used) - empty} values, all checked against {len(C.PALETTE)} palette entries; "
          f"{empty} intentionally empty color values")
    print(f"effective attributes: {dict(sorted(terminal.items()))}")
    print(f"level sets checked: {len(sets)}")
    if failures:
        print(f"FAIL ({len(failures)}):")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
