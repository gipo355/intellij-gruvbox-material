"""Generates the Gruvbox Material Islands editor schemes (one per palette variant), their required-keys checklists
and the runtime key groups (src/main/resources/gruvbox/groups.json).

    IDEA_HOME=<IDE install dir> IDEA_PLUGINS_DIR=<user plugins dir> python3 -I tools/scheme/generate.py
    NVIM_CONFIG=<nvim config dir> ... generate.py --refresh-nvim

Each directory can also be passed as --ide, --user-plugins, --nvim-config. Jars are read in memory. Run
tools/ui/build_theme.py first: the accent ui keys in groups.json come from the generated theme.json files.

Dark variants: every key a Darcula-parented scheme would otherwise inherit (Darcula, Islands Dark and every plugin's
additionalTextAttributes for Darcula) is written explicitly, so nothing falls back to Darcula's colors or font
styles. Keys of Default and of plugin files for Default are written too: Darcula has no parent scheme, so they would
otherwise fall back to their code defaults. Precedence per key: curated tables > Islands > Darcula > plugin files
for Darcula > Default > plugin files for Default. Light variant (parent Default): every key of Default, of "Light"
(the expUI editor scheme Islands Light names) and of every plugin file for Default; precedence curated > Light >
Default > plugin files for Default.

Both families also define the keys no scheme file mentions but code creates with a default color, and the keys
whose visible code fallback chain ends on a blue-allowed key (CONSOLE_BLUE_OUTPUT) outside the blue-allowed set.
Those have no value to map, so they must be curated.

Keys are resolved to palette role names once per family, against dark soft or light soft; each variant of the
family renders the same roles with its own hex, so medium and hard cannot drift from soft.

Every attribute gets its own <value>: IntelliJ does not follow baseAttributes="X" to X (it falls back to the
key's coded fallback, then the parent scheme), so links (curated L() or a source's baseAttributes) are resolved
here to the target's final value.
"""

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import tempfile
from xml.sax.saxutils import quoteattr

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import colors as C  # noqa: E402
import curated  # noqa: E402
import sources  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = C.REPO
THEMES = os.path.join(REPO, "src", "main", "resources", "themes")
REQUIRED = {True: os.path.join(REPO, "src", "test", "resources", "scheme-required-keys.txt"),
            False: os.path.join(REPO, "src", "test", "resources", "scheme-required-keys-light.txt")}
GROUPS = os.path.join(REPO, "src", "main", "resources", "gruvbox", "groups.json")
# Family -> the variant whose palette the source colors are mapped against.
MAPPING_VARIANT = {True: "dark-soft", False: "light-soft"}
NVIM_JSON = os.path.join(HERE, "nvim-highlights.json")
NVIM_LUA = os.path.join(HERE, "nvim_dump.lua")

COLOR_FIELDS = ("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR")
FIELD_ORDER = ("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "EFFECT_TYPE", "ERROR_STRIPE_COLOR")


def refresh_nvim(config_dir):
    # An empty state dir keeps runtime choices saved there (e.g. a keyword colour) out of the dump.
    with tempfile.TemporaryDirectory() as state:
        out = subprocess.run(
            ["nvim", "--headless", "-c", f"luafile {NVIM_LUA}", "-c", "qa!"],
            cwd=config_dir, capture_output=True, text=True, timeout=120, check=True,
            env={**os.environ, "XDG_STATE_HOME": state},
        ).stdout
    data = json.loads(out)
    groups = {k: (v if isinstance(v, dict) else {}) for k, v in data["groups"].items()}
    with open(NVIM_JSON, "w") as f:
        json.dump({"colors_name": data["colors_name"], "groups": groups}, f, indent=2, sort_keys=True)
        f.write("\n")


def scheme_path(variant):
    return os.path.join(THEMES, C.VARIANTS[variant]["stem"] + ".xml")


def family(dark):
    return [k for k, v in C.VARIANTS.items() if v["dark"] == dark]


def palette_name(hex_value):
    hex_value = hex_value.lstrip("#").lower()
    for name, value in C.PALETTE.items():
        if value == hex_value:
            return name
    return None


# ---------------------------------------------------------------- checklist


def build_checklist(src, dark=True):
    """-> (color keys, attribute keys, key -> sorted source labels, value providers in precedence order)"""
    if not dark:
        return build_light_checklist(src)
    color_src = collections.defaultdict(set)
    attr_src = collections.defaultdict(set)
    darcula, default, islands = src["darcula"], src["default"], src["islands"]

    for k in darcula["colors"]:
        color_src[k].add("Darcula")
    for k in darcula["attributes"]:
        attr_src[k].add("Darcula")
    for k in default["colors"]:
        if k not in darcula["colors"]:
            color_src[k].add("Default")
    for k in default["attributes"]:
        if k not in darcula["attributes"]:
            attr_src[k].add("Default")
    for k in islands["colors"]:
        color_src[k].add("Islands")
    for k in islands["attributes"]:
        attr_src[k].add("Islands")
    for pid, _user, scheme, _f, d in src["contributions"]:
        label = plugin_label(pid, scheme)
        for k in d["colors"]:
            color_src[k].add(label)
        for k in d["attributes"]:
            attr_src[k].add(label)

    # Value providers: user-installed plugins shadow bundled ones at runtime.
    plugin_defs = sorted(src["contributions"], key=lambda c: (not c[1], c[0], c[3]))
    def plugin_providers(scheme):
        return [(plugin_label(pid, s), d) for pid, _u, s, _f, d in plugin_defs if s == scheme]
    providers = [("Islands", islands), ("Darcula", darcula)] + plugin_providers("Darcula")
    providers += [("Default", default)] + plugin_providers("Default")
    code_sources(src["code"], color_src, attr_src)
    return color_src, attr_src, providers


def build_light_checklist(src):
    color_src = collections.defaultdict(set)
    attr_src = collections.defaultdict(set)
    default, light = src["default"], src["light"]
    for label, scheme in (("Default", default), ("Light", light)):
        for k in scheme["colors"]:
            color_src[k].add(label)
        for k in scheme["attributes"]:
            attr_src[k].add(label)
    plugin_defs = sorted((c for c in src["contributions"] if c[2] == "Default"), key=lambda c: (not c[1], c[0], c[3]))
    for pid, _user, scheme, _f, d in plugin_defs:
        for k in d["colors"]:
            color_src[k].add(plugin_label(pid, scheme))
        for k in d["attributes"]:
            attr_src[k].add(plugin_label(pid, scheme))
    providers = [("Light", light), ("Default", default)]
    providers += [(plugin_label(pid, s), d) for pid, _u, s, _f, d in plugin_defs]
    code_sources(src["code"], color_src, attr_src)
    return color_src, attr_src, providers


def code_sources(code, color_src, attr_src):
    """Adds the code keys no source defines: those with a code default, and those whose fallback chain first reaches
    a defined key that may be blue while they may not."""
    defined = set(color_src) | set(attr_src)
    for name, entry in sorted(code.items()):
        if name in defined:
            continue
        table = color_src if entry["kind"] == "color" else attr_src
        if entry["how"] == "default":
            table[name].add("code")
            continue
        seen, k = {name}, entry["fallback"]
        while k and k not in defined and k not in seen and code.get(k, {}).get("how") != "default":
            seen.add(k)
            k = code.get(k, {}).get("fallback")
        if k in defined and C.blue_allowed(k) and not C.blue_allowed(name):
            table[name].add(f"code fallback to {k}")


def plugin_label(pid, scheme):
    return f"plugin:{pid}" if scheme == "Darcula" else f"plugin:{pid} ({scheme})"


def default_only(labels):
    return labels and all(l == "Default" or l.endswith(" (Default)") for l in labels)


# ---------------------------------------------------------------- resolution


def map_value(value, key, greys):
    out = {}
    for field, raw in value.items():
        if field == "FONT_TYPE" or raw == "":
            continue
        if field == "BACKGROUND":
            bg = C.map_bg(raw, key, greys)
            # A bg0 fill only hides the caret row and selection under it.
            if bg != "bg0":
                out[field] = bg
        elif field in COLOR_FIELDS:
            out[field] = C.map_fg(raw, key)
        else:
            out[field] = raw
    if "EFFECT_TYPE" in out and "EFFECT_COLOR" not in out:
        del out["EFFECT_TYPE"]
    return out


def cycle_entry(key):
    for pattern, cycle in curated.CYCLES:
        m = re.match(pattern, key)
        if m:
            return curated.A(fg=cycle[int(m.group(2)) % len(cycle)])
    return None


def resolve_attribute(key, providers):
    """-> (definition, how) with how in curated | linked | auto"""
    if key in curated.CORE:
        return curated.CORE[key], "curated"
    if key in curated.LANGUAGES:
        return curated.LANGUAGES[key], "curated"
    entry = cycle_entry(key)
    if entry:
        return entry, "curated"
    for label, scheme in providers:
        d = scheme["attributes"].get(key)
        if d is None:
            continue
        if d["value"] is None:
            if d["base"]:
                return curated.L(d["base"]), "linked"
            return curated.NONE, "auto"
        greys = curated.ISLANDS_GREYS if label == "Islands" else None
        return {"base": None, "value": map_value(d["value"], key, greys)}, "auto"
    return None, None


def resolve_color(key, providers, dark=True):
    table = curated.COLORS if dark else {**curated.COLORS, **curated.LIGHT_COLORS}
    if key in table:
        return table[key], "curated"
    for label, scheme in providers:
        if key in scheme["colors"]:
            raw = scheme["colors"][key]
            if raw == "":
                return "", "auto"
            greys = curated.ISLANDS_GREYS if label == "Islands" else None
            return C.map_color_key(raw, key, greys), "auto"
    return None, None


def resolve(src, dark=True):
    color_src, attr_src, providers = build_checklist(src, dark)
    out_colors, out_attrs, how = {}, {}, {}
    code_only = sorted(k for table in (attr_src, color_src) for k, s in table.items()
                       if all(l.startswith("code") for l in s))
    uncurated = [k for k in code_only if not (k in curated.COLORS or k in curated.CORE or k in curated.LANGUAGES
                                              or cycle_entry(k))]
    if uncurated:
        raise SystemExit(f"keys only code defines must be curated: {uncurated}")

    for k in sorted(color_src):
        v, h = resolve_color(k, providers, dark)
        out_colors[k], how[k] = v, h

    pending = sorted(attr_src)
    curated_extra = sorted((set(curated.CORE) | set(curated.LANGUAGES)) - set(attr_src) - set(color_src))
    for k in curated_extra:
        attr_src[k]  # creates an empty source set: defined, not required
    pending += curated_extra
    while pending:
        k = pending.pop(0)
        if k in out_attrs:
            continue
        d, h = resolve_attribute(k, providers)
        if d is None:
            raise SystemExit(f"link target {k} has no definition anywhere")
        out_attrs[k], how[k] = d, h
        if d["base"] and d["base"] not in out_attrs:
            if not attr_src[d["base"]]:
                attr_src[d["base"]].add("link target")
            pending.append(d["base"])

    misplaced = sorted(k for k in curated.COLORS if k in attr_src and attr_src[k])
    if misplaced:
        raise SystemExit(f"curated as colors but are attributes: {misplaced}")
    light_only = {k for table in (attr_src, color_src) for k, s in table.items() if default_only(s)} if dark else set()
    uncurated = sorted(k for k in light_only if how[k] != "curated")
    if uncurated:
        raise SystemExit(f"Default-only keys must be curated (their values are light-scheme colors): {uncurated}")
    extra = {k for k in out_attrs if not attr_src[k]}
    links = resolve_links(out_attrs)
    return out_colors, out_attrs, how, color_src, attr_src, extra, links


def resolve_links(out_attrs):
    """Replaces every link with a copy of its target's final value. -> {key: link chain after the key}"""
    finals = {}
    for k in sorted(out_attrs):
        chain = [k]
        while out_attrs[chain[-1]]["value"] is None:
            nxt = out_attrs[chain[-1]]["base"]
            if nxt in chain:
                raise SystemExit(f"link cycle: {' -> '.join(chain + [nxt])}")
            chain.append(nxt)
        if len(chain) > 1:
            finals[k] = (chain[1:], out_attrs[chain[-1]]["value"])
    for k, (_chain, value) in finals.items():
        out_attrs[k] = {"base": None, "value": dict(value)}
    return {k: chain for k, (chain, _v) in finals.items()}


# ---------------------------------------------------------------- output


def render(out_colors, out_attrs, variant):
    meta = C.VARIANTS[variant]
    palette = meta["colors"]

    def hexof(name):
        return palette[name] if name else ""

    header = f'<scheme name={quoteattr(meta["name"])} version="142" parent_scheme={quoteattr(meta["parentScheme"])}>'
    lines = [header, "  <colors>"]
    for k in sorted(out_colors):
        lines.append(f"    <option name={quoteattr(k)} value=\"{hexof(out_colors[k])}\"/>")
    lines += ["  </colors>", "  <attributes>"]
    for k in sorted(out_attrs):
        d = out_attrs[k]
        if not d["value"]:
            lines.append(f"    <option name={quoteattr(k)}>")
            lines.append("      <value/>")
            lines.append("    </option>")
            continue
        lines.append(f"    <option name={quoteattr(k)}>")
        lines.append("      <value>")
        for field in FIELD_ORDER:
            if field in d["value"]:
                v = d["value"][field]
                v = hexof(v) if field in COLOR_FIELDS else v
                lines.append(f"        <option name=\"{field}\" value={quoteattr(v)}/>")
        lines.append("      </value>")
        lines.append("    </option>")
    lines += ["  </attributes>", "</scheme>", ""]
    return "\n".join(lines)


def render_required(color_src, attr_src, src, dark=True):
    keys = {k for k, s in color_src.items() if s} | {k for k, s in attr_src.items() if s}
    files = sorted({f"{pid}: {f} ({scheme})" for pid, _u, scheme, f, _d in src["contributions"]
                    if dark or scheme == "Default"})
    if dark:
        head = [
            "# Keys the dark Gruvbox Material Islands schemes must define explicitly (generated by tools/scheme/generate.py).",
            "# Sources: Darcula and Default (DefaultColorSchemesManager.xml; Darcula has no parent, Default keys are",
            "# written so they skip their code defaults), Islands Dark (themes/islands/IslandSchemeDark.xml), link",
            "# targets, keys only code defines (a code default, or a code fallback chain onto a blue-allowed key),",
            "# and every installed plugin file for Darcula or Default (additionalTextAttributes, or",
            "# *Darcula*/*Default*.xml of a provider plugin):",
        ]
    else:
        head = [
            "# Keys the light Gruvbox Material Islands scheme must define explicitly (generated by tools/scheme/generate.py).",
            "# Sources: the Default scheme (DefaultColorSchemesManager.xml), Light (themes/expUI/expUI_lightScheme.xml,",
            "# the editor scheme Islands Light names), link targets, keys only code defines (a code default, or a",
            "# code fallback chain onto a blue-allowed key), and every installed plugin file for Default",
            "# (additionalTextAttributes, or *Default*.xml of a provider plugin):",
        ]
    head += [f"#   {f}" for f in files]
    return "\n".join(head + sorted(keys)) + "\n"


def report(src, out_colors, out_attrs, how, color_src, attr_src, extra, links, dark):
    required = {k for k, s in color_src.items() if s} | {k for k, s in attr_src.items() if s}
    by_source = collections.Counter()
    for table in (color_src, attr_src):
        for k, s in table.items():
            for label in s:
                by_source[label] += 1
    print(f"{'dark' if dark else 'light'} checklist: {len(required)} keys "
          f"({sum(1 for s in color_src.values() if s)} colors, "
          f"{sum(1 for s in attr_src.values() if s)} attributes); +{len(extra)} curated keys beyond it")
    for label, n in sorted(by_source.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:4d}  {label}")
    def treatment(k):
        if k in out_colors:
            return f"{how[k]} color"
        kind = "link" if k in links else "empty" if not out_attrs[k]["value"] else "explicit"
        return f"{how[k]} {kind}"

    counts = collections.Counter(treatment(k) for k in required)
    print("required keys by treatment:", ", ".join(f"{h} {n}" for h, n in sorted(counts.items())))
    providers = build_checklist(src, dark)[2]
    hidden = sorted(
        k for k, d in out_attrs.items()
        if d["value"] == {} and any(
            any(f in COLOR_FIELDS and v for f, v in (p["attributes"].get(k, {}).get("value") or {}).items())
            for _label, p in providers))
    print(f"emitted <value/> although a source colors the key ({len(hidden)}): {', '.join(hidden)}")
    if dark:
        contributing = {pid for pid, _u, _s, _f, _d in src["contributions"]}
        silent = sorted({pid for pid, user in src["plugins"] if user} - contributing)
        print(f"user-installed plugins contributing nothing to Darcula: {len(silent)}"
              f" (e.g. {', '.join(p for p in silent if p in ('Indent Rainbow', 'atlashcl', 'dotenv', 'terraform'))})")
    if src["unresolved"]:
        print("UNRESOLVED additionalTextAttributes files:", src["unresolved"])

    if dark:
        with open(NVIM_JSON) as f:
            nvim = json.load(f)["groups"]
        print("\nnvim -> IntelliJ core (dark soft):")
        for group, nf, key, field in curated.NVIM_ALIGN:
            want = palette_name(nvim.get(group, {}).get(nf, "")) or nvim.get(group, {}).get(nf, "-")
            if field is None:
                got = out_colors.get(key)
            else:
                got = out_attrs[key]["value"].get(field)
            note = ""
            if want != got:
                note = curated.NVIM_DEVIATIONS.get((group, key), "MISMATCH")
            print(f"  {group:24s} {nf:2s} {str(want):16s} -> {key}{'.' + field if field else ''} = {got}"
                  + (f"   [{note}]" if note else ""))

    syntax = {d["value"].get("FOREGROUND") for d in out_attrs.values()}
    syntax -= {None, "fg0"}
    print()
    for variant in family(dark):
        palette = C.VARIANTS[variant]["colors"]
        bg = palette["bg0"]
        top = max(syntax, key=lambda n: C.contrast(palette[n], bg))
        print(f"{variant}: TEXT fg0 on bg0 {C.contrast(palette['fg0'], bg):.2f}:1; comments grey2 "
              f"{C.contrast(palette['grey2'], bg):.2f}:1; highest-contrast foreground other than fg0: {top} "
              f"{C.contrast(palette[top], bg):.2f}:1")


# ---------------------------------------------------------------- runtime groups


GROUP_ROOTS = {
    "operators": {"DEFAULT_OPERATION_SIGN"},
    "comments": {"DEFAULT_LINE_COMMENT", "DEFAULT_BLOCK_COMMENT"},
    "docs": {"DEFAULT_DOC_COMMENT", "DEFAULT_DOC_MARKUP", "DEFAULT_DOC_COMMENT_TAG", "DEFAULT_DOC_COMMENT_TAG_VALUE"},
    "calls": {"DEFAULT_FUNCTION_CALL"},
    "keywords": {"DEFAULT_KEYWORD"},
    "parameters": {"DEFAULT_PARAMETER", "DEFAULT_REASSIGNED_PARAMETER"},
    "reassigned": {"DEFAULT_REASSIGNED_LOCAL_VARIABLE", "DEFAULT_REASSIGNED_PARAMETER"},
    "annotations": {"DEFAULT_METADATA"},
}
# Method keys are shared by declarations and calls; a link to one counts as a call only when the key says so.
METHOD_ROOTS = {"DEFAULT_INSTANCE_METHOD", "DEFAULT_STATIC_METHOD"}
# Names that link to DEFAULT_PARAMETER only for its color: annotation attributes and named arguments are not parameters.
NOT_PARAMETERS = {"ANNOTATION_ATTRIBUTE_NAME_ATTRIBUTES", "KOTLIN_NAMED_ARGUMENT"}


def key_groups(out_attrs, chains):
    """Membership by link chain (curated L() targets and the sources' baseAttributes), never by color."""
    groups = {}
    for name, roots in GROUP_ROOTS.items():
        groups[name] = {k for k in out_attrs if k in roots or roots & set(chains.get(k, ()))}
    groups["calls"] |= {k for k in out_attrs if "CALL" in k.upper() and METHOD_ROOTS & set(chains.get(k, ()))}
    groups["parameters"] -= NOT_PARAMETERS
    return groups


def accent_ui_keys():
    """ui keys whose value is the accent role (aqua) in any generated theme.json."""
    keys = set()
    for meta in C.VARIANTS.values():
        path = os.path.join(THEMES, meta["stem"] + ".theme.json")
        if not os.path.isfile(path):
            raise SystemExit(f"{os.path.relpath(path, REPO)} missing: run tools/ui/build_theme.py first")
        with open(path) as f:
            ui = json.load(f)["ui"]
        stack = [("", ui)]
        while stack:
            prefix, node = stack.pop()
            for k, v in node.items():
                path_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    stack.append((path_key, v))
                elif v == "aqua":
                    keys.add(path_key)
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ide", default=os.environ.get("IDEA_HOME"), help="IDE install dir (env IDEA_HOME)")
    ap.add_argument("--user-plugins", default=os.environ.get("IDEA_PLUGINS_DIR"),
                    help="user-installed plugins dir (env IDEA_PLUGINS_DIR)")
    ap.add_argument("--refresh-nvim", action="store_true", help="re-dump nvim highlights into nvim-highlights.json")
    ap.add_argument("--nvim-config", default=os.environ.get("NVIM_CONFIG"), help="nvim config dir (env NVIM_CONFIG)")
    args = ap.parse_args()
    if not args.ide or not os.path.isdir(os.path.join(args.ide, "lib")):
        ap.error("set IDEA_HOME (or --ide) to the IntelliJ IDEA install dir, the one containing lib/")
    if not args.user_plugins or not os.path.isdir(args.user_plugins):
        ap.error("set IDEA_PLUGINS_DIR (or --user-plugins) to the user plugins dir, e.g. the IDE's config/plugins dir")
    if args.refresh_nvim and (not args.nvim_config or not os.path.isdir(args.nvim_config)):
        ap.error("--refresh-nvim needs NVIM_CONFIG (or --nvim-config) set to the nvim config dir")

    if args.refresh_nvim:
        refresh_nvim(args.nvim_config)
    src = sources.collect(args.ide, args.user_plugins)
    groups = collections.defaultdict(set)
    os.makedirs(THEMES, exist_ok=True)
    for dark in (True, False):
        C.use(MAPPING_VARIANT[dark])
        out_colors, out_attrs, how, color_src, attr_src, extra, chains = resolve(src, dark)
        for variant in family(dark):
            with open(scheme_path(variant), "w") as f:
                f.write(render(out_colors, out_attrs, variant))
        os.makedirs(os.path.dirname(REQUIRED[dark]), exist_ok=True)
        with open(REQUIRED[dark], "w") as f:
            f.write(render_required(color_src, attr_src, src, dark))
        for name, keys in key_groups(out_attrs, chains).items():
            groups[name] |= keys
        report(src, out_colors, out_attrs, how, color_src, attr_src, extra, chains, dark)
        print()
    C.use(MAPPING_VARIANT[True])
    groups["accentUiKeys"] = accent_ui_keys()
    os.makedirs(os.path.dirname(GROUPS), exist_ok=True)
    with open(GROUPS, "w") as f:
        json.dump({k: sorted(groups[k]) for k in ("operators", "comments", "docs", "calls", "keywords", "parameters", "reassigned", "annotations", "accentUiKeys")}, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
