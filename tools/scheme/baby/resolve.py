"""Statically resolve gruvbox-baby into baby.json, the only baby input the generators read.

Upstream: https://github.com/luisiacc/gruvbox-baby, commit bd52e62, MIT licence.
The Lua sources are parsed as text, never executed.

Usage: python3 -I resolve.py [<gruvbox-baby clone>] [<summary dir>]
The clone defaults to $GRUVBOX_BABY. baby.json is written next to this script; baby-summary.md only when a
summary dir is given.
"""
import json
import math
import os
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ["GRUVBOX_BABY"])
SUMMARY = Path(sys.argv[2]) if len(sys.argv) > 2 else None
LUA = SRC / "lua" / "gruvbox-baby"
HERE = Path(__file__).resolve().parent

# ---- util.lua port (blend / darken / lighten; tokyonight-derived) ----
UTIL_BG, UTIL_FG = "#000000", "#ffffff"


def hex_to_rgb(h):
    h = h.lower()
    assert re.fullmatch(r"#[0-9a-f]{6}", h), h
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def blend(fg, bg, alpha):
    bg, fg = hex_to_rgb(bg), hex_to_rgb(fg)

    def ch(i):
        ret = alpha * fg[i] + ((1 - alpha) * bg[i])
        return math.floor(min(max(0, ret), 255) + 0.5)

    return "#%02X%02X%02X" % (ch(0), ch(1), ch(2))


def darken(h, amount, bg=None):
    return blend(h, bg or UTIL_BG, abs(amount))


def lighten(h, amount, fg=None):
    return blend(h, fg or UTIL_FG, abs(amount))


# ---- parsing helpers ----
def block(text, start_pat, end_pat):
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if re.search(start_pat, l):
            for j in range(i + 1, len(lines)):
                if re.fullmatch(end_pat, lines[j]):
                    return lines[i + 1:j]
    raise ValueError(start_pat)


def lua_str_map(lines):
    out = {}
    for l in lines:
        m = re.match(r'\s*(\w+)\s*=\s*"([^"]*)"', l)
        if m:
            out[m.group(1)] = m.group(2)
    return out


colors_src = (LUA / "colors.lua").read_text()
base_palette = lua_str_map(block(colors_src, r"^local the_palette = \{", r"\}"))
term = re.findall(r'"(#[0-9A-Fa-f]{6})"', "\n".join(block(colors_src, r"^the_palette.term = \{", r"\}")))
diff = lua_str_map(block(colors_src, r"^the_palette.diff = \{", r"\}"))
orig_over = lua_str_map(block(colors_src, r'^local original_palette = vim.tbl_extend', r"\}\)"))

# intensity_map: parse each background's entries as expressions
imap_lines = block(colors_src, r"local intensity_map = \{", r"  \}")
intensity = {}
cur = None
for l in imap_lines:
    m = re.match(r'\s*\["(\w+)"\] = \{', l)
    if m:
        cur = m.group(1)
        intensity[cur] = {}
        continue
    m = re.match(r"\s*(\w+) = (.+?),?\s*$", l)
    if m and cur:
        intensity[cur][m.group(1)] = m.group(2)


def eval_imap(expr, colors):
    m = re.fullmatch(r"colors\.(\w+)", expr)
    if m:
        return colors[m.group(1)], None
    m = re.fullmatch(r"util\.(darken|lighten)\(colors\.(\w+), ([\d.]+)\)", expr)
    if m:
        fn = darken if m.group(1) == "darken" else lighten
        return fn(colors[m.group(2)], float(m.group(3))), f"{m.group(1)}({m.group(2)}, {m.group(3)})"
    raise ValueError(expr)


# ---- config.lua defaults ----
cfg_src = (LUA / "config.lua").read_text()
config = {}
for k, v in re.findall(r'(\w+) = opt\("\w+", ([^)]*)\)', cfg_src):
    v = v.strip()
    config[k] = {"false": False, "true": True, "{}": {}}.get(v, v.strip('"'))


def palette_for(original, background):
    colors = dict(base_palette)
    if original:
        colors.update(orig_over)
    computed = {}
    if background in intensity:
        src = dict(colors)  # tbl_extend: the map is built from the pre-override table
        for k, expr in intensity[background].items():
            val, how = eval_imap(expr, src)
            colors[k] = val
            if how:
                computed[k] = how
            elif expr != f"colors.{k}":
                computed[k] = f"= {expr.split('.')[1]}"
    return colors, computed


# ---- theme.lua ----
theme_src = (LUA / "theme.lua").read_text()
ENTRY = re.compile(r'^\s*(?:\["([^"]+)"\]|([A-Za-z_]\w*))\s*=\s*\{(.*)\},?\s*(?:--.*)?$')


def parse_entries(lines):
    entries, n_candidates = {}, 0
    for l in lines:
        if re.search(r"=\s*\{", l):
            n_candidates += 1
        m = ENTRY.match(l)
        if not m:
            continue
        name = m.group(1) or m.group(2)
        assert name not in entries, f"duplicate {name}"
        fields, positional = {}, []
        for part in [p.strip() for p in m.group(3).split(",") if p.strip()]:
            kv = re.fullmatch(r"(\w+)\s*=\s*(.+)", part)
            if kv:
                fields[kv.group(1)] = kv.group(2)
            else:
                positional.append(part)
        entries[name] = (fields, positional)
    assert n_candidates == len(entries), (n_candidates, len(entries))
    return entries


base_entries = parse_entries(block(theme_src, r"^  theme.base = \{", r"  \}"))
tele_entries = parse_entries(block(theme_src, r"if config.telescope_theme then", r"    \}\)"))
transp_entries = parse_entries(block(theme_src, r"if config.transparent_mode then", r"    \}\)"))


def eval_expr(expr, c):
    """-> (value or None, role, config_dep)"""
    m = re.fullmatch(r"c\.diff\.(\w+)", expr)
    if m:
        return c["diff"].get(m.group(1)), f"diff.{m.group(1)}", None
    m = re.fullmatch(r"c\.(\w+)", expr)
    if m:
        return c.get(m.group(1)), m.group(1), None
    m = re.fullmatch(r"config\.(\w+)", expr)
    if m:
        return config[m.group(1)], None, m.group(1)
    m = re.fullmatch(r'"([^"]*)"', expr)
    if m:
        return m.group(1), None, None
    raise ValueError(expr)


def norm(v):
    if isinstance(v, str) and v.startswith("#"):
        return v.lower()
    return v


def resolve_group(fields, positional, c):
    g, roles, deps, notes = {}, {}, [], []
    for key in ("fg", "bg", "sp", "style", "link"):
        if key not in fields:
            continue
        val, role, dep = eval_expr(fields[key], c)
        if role:
            roles[key] = role
        if dep:
            deps.append(dep)
        if val is None:
            notes.append(f"{key} = {fields[key]} is nil (undefined palette key) -> attribute not set")
            continue
        if key == "style" and val == "NONE":
            notes.append("style NONE is dropped by util.highlight")
            continue
        g[key] = norm(val)
    for p in positional:
        notes.append(f"positional value {p} ignored by util.highlight")
    for key in ("fg", "bg", "sp", "style", "link"):
        g.setdefault(key, None)
    if roles:
        g["roles"] = roles
    if deps:
        g["config_dep"] = deps
    if notes:
        g["notes"] = notes
    return g


BACKGROUNDS = ["dark", "medium", "soft"]
PALETTES = {"default": False, "original": True}

out = {
    "source": {
        "repo": "gruvbox-baby (luisiacc/gruvbox-baby)",
        "commit": (SRC / ".git" / "HEAD").exists() and None,
        "files": ["lua/gruvbox-baby/colors.lua", "config.lua", "theme.lua", "util.lua"],
    },
    "config_defaults": config,
    "helpers": {
        "blend(fg,bg,a)": "per channel floor(clamp(a*fg+(1-a)*bg,0,255)+0.5)",
        "darken(hex,a)": "blend(hex, #000000, a)",
        "lighten(hex,a)": "blend(hex, #ffffff, a)",
        "hsluv": "only used by util.brighten/invertColor/randomColor, which nothing calls; not needed",
    },
    "hex_case": "all hex normalised to lowercase (Lua emits uppercase from blend; palette mixes case)",
    "term": [t.lower() for t in term],
    "palettes": {},
    "computed": {},
    "groups": {},
    "conditional": {"telescope_theme": {}, "transparent_mode": {}},
}

for pname, orig in PALETTES.items():
    out["palettes"][pname], out["computed"][pname], out["groups"][pname] = {}, {}, {}
    out["conditional"]["telescope_theme"][pname] = {}
    out["conditional"]["transparent_mode"][pname] = {}
    for bgname in BACKGROUNDS:
        colors, computed = palette_for(orig, bgname)
        flat = {k: norm(v) for k, v in colors.items()}
        flat["diff"] = {k: v.lower() for k, v in diff.items()}
        out["palettes"][pname][bgname] = {k: v for k, v in flat.items()}
        out["computed"][pname][bgname] = computed
        c = dict(colors)
        c["diff"] = diff
        out["groups"][pname][bgname] = {n: resolve_group(f, p, c) for n, (f, p) in base_entries.items()}
        out["conditional"]["telescope_theme"][pname][bgname] = {
            n: resolve_group(f, p, c) for n, (f, p) in tele_entries.items()}
        ct = dict(c, background="NONE", background_dark="NONE")
        groups_t = {n: resolve_group(f, p, ct) for n, (f, p) in base_entries.items()}
        groups_t.update({n: resolve_group(f, p, ct) for n, (f, p) in transp_entries.items()})
        out["conditional"]["transparent_mode"][pname][bgname] = {
            n: g for n, g in groups_t.items()
            if g != out["groups"][pname][bgname][n] or n in transp_entries}

# soft_flat check
sf, _ = palette_for(False, "soft_flat")
so, _ = palette_for(False, "soft")
out["soft_flat"] = {"skipped": True, "differs_from_soft": {k: [so[k].lower(), sf[k].lower()] for k in sf if sf[k] != so[k]}}

# nvim 0.12 built-in defaults (read from the local nvim binary's strings)
links = dict(l.split() for l in (HERE / "nvim-default-links.txt").read_text().splitlines() if l.strip())
defs = {}
for l in (HERE / "nvim-default-defs.txt").read_text().splitlines():
    name, rest = l.split(None, 1)
    defs[name] = " ".join(t for t in rest.split() if t.startswith("gui"))


def effective(name, groups, seen=()):
    """Resolution as nvim would show it: theme group, else nvim default link/def, else TS parent."""
    if name in groups:
        return {"via": list(seen) + [name], "group": groups[name]}
    if name in links:
        return effective(links[name], groups, seen + (name,))
    if name in defs:
        return {"via": list(seen) + [name], "nvim_default": defs[name]}
    if name.startswith("@") and "." in name:
        return effective(name.rsplit(".", 1)[0], groups, seen + (name,))
    return {"via": list(seen) + [name], "undefined": True}


ref = out["groups"]["default"]["medium"]
NOT_SET = ["WinSeparator", "Delimiter", "SpecialChar", "Tag", "PmenuKind", "PmenuExtra", "StatusLineNC",
           "DiagnosticWarn", "DiagnosticInfo", "DiagnosticOk", "DiagnosticUnderlineError",
           "DiagnosticUnderlineWarn", "DiagnosticUnderlineInfo", "DiagnosticUnderlineHint",
           "DiagnosticVirtualTextError", "DiagnosticVirtualTextWarn", "DiagnosticVirtualTextInfo",
           "DiagnosticVirtualTextHint", "DiagnosticSignError", "DiagnosticSignWarn",
           "GitSignsAdd", "GitSignsChange", "GitSignsDelete", "Added", "Changed", "Removed",
           "FloatTitle", "WinBar", "@attribute", "@string.escape", "@string.regexp", "@string.special",
           "@type.definition", "@keyword.import", "@keyword.type", "@keyword.modifier", "@function.macro",
           "@constant.macro", "@variable.parameter.builtin", "@module.builtin", "@punctuation",
           "@comment.todo", "@comment.error", "@comment.warning", "@comment.note", "@comment.documentation",
           "@tag.builtin", "@markup.link", "@markup.italic", "@number.float", "@character.special",
           "@lsp.type.keyword", "@lsp.type.comment", "@lsp.type.string", "@lsp.type.number",
           "@lsp.type.operator", "@lsp.mod.deprecated"]
out["not_set_by_theme"] = {
    "note": "Groups the theme never sets. nvim_set_hl replaces only the groups it names; everything else "
            "keeps the nvim built-in default (links/defs read from the nvim 0.12.5 binary). Resolved "
            "against the default/medium theme groups.",
    "groups": {n: effective(n, ref) for n in NOT_SET if n not in ref},
}
out["config_dependent_groups"] = sorted(
    {n: g["config_dep"] for n, g in ref.items() if "config_dep" in g}.items())
out["config_dependent_groups"] = {n: d for n, d in out["config_dependent_groups"]}
out["after_queries"] = {
    "typescript/tsx/javascript/jsx": "(shorthand_property_identifier_pattern) @variable; jsx attribute property_identifier @attribute (theme has no @attribute -> nvim default Macro)",
    "typescript": "(module) @keyword",
    "python": "(decorator (identifier) @decorator)",
}
out["counts"] = {"base_groups": len(base_entries), "telescope_groups": len(tele_entries),
                 "transparent_overrides": len(transp_entries)}
out["source"]["commit"] = (SRC / ".git" / "HEAD").read_text().strip()
head = out["source"]["commit"]
if head.startswith("ref:"):
    ref_file = SRC / ".git" / head.split()[1]
    out["source"]["commit"] = ref_file.read_text().strip() if ref_file.exists() else head

(HERE / "baby.json").write_text(json.dumps(out, indent=1) + "\n")


# ---- summary ----
def lum(h):
    def lin(x):
        x /= 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(h)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


P = out["palettes"]
G = out["groups"]
L = []
w = L.append
w("# gruvbox-baby, statically resolved")
w("")
w(f"Source commit `{out['source']['commit'][:7]}`. Parsed from colors/config/theme.lua, colours computed with a Python port")
w("of `util.blend/darken/lighten` (`darken(x,a)` = blend toward #000000 with weight `a` on x; `lighten` toward #ffffff).")
w("hsluv is not involved: only `brighten/invertColor/randomColor` use it and nothing calls them.")
w(f"Groups: {len(base_entries)} base, +{len(tele_entries)} telescope_theme, {len(transp_entries)} transparent_mode overrides.")
w("All hex lowercased. Full data: `baby.json`.")
w("")
w("Config defaults: " + ", ".join(f"`{k}={json.dumps(v)}`" for k, v in config.items()))
w("")
w("## Palette")
w("")
w("`*` = computed or overridden by `intensity_map[background]`. `original` = `use_original_palette`.")
w("")
w("| role | default dark | default medium | default soft | original dark | original medium | original soft |")
w("|---|---|---|---|---|---|---|")
for k in base_palette:
    if k == "none":
        continue
    cells = []
    for pn in PALETTES:
        for bn in BACKGROUNDS:
            v = P[pn][bn][k]
            star = "*" if k in intensity.get(bn, {}) else ""
            cells.append(f"`{v}`{star}")
    w(f"| {k} | " + " | ".join(cells) + " |")
for k, v in diff.items():
    w(f"| diff.{k} | " + " | ".join([f"`{v.lower()}`"] * 6) + " |")
w("")
w("Computed values: " + "; ".join(
    f"{bn}: " + ", ".join(f"{k} = {how}" for k, how in out["computed"]["default"][bn].items())
    for bn in BACKGROUNDS))
w(f"`soft_flat` skipped: differs from `soft` only in {out['soft_flat']['differs_from_soft']}.")
w("`original` overrides (all backgrounds): " + ", ".join(f"{k}={v.lower()}" for k, v in orig_over.items()) + ".")
w("")
w("Terminal colours 0-15: " + " ".join(f"`{t}`" for t in out["term"]))
w("")


def fmt_attr(g, key):
    v = g[key]
    if v is None:
        return ""
    role = g.get("roles", {}).get(key)
    return f"{role} `{v}`" if role else f"`{v}`"


def row(name, pn="default", bn="medium", extra=""):
    groups = G[pn][bn]
    if name in groups:
        g = groups[name]
        orig = G["original"][bn][name]
        ofg = orig["fg"] if orig["fg"] != g["fg"] else "same"
        dep = ", ".join(g.get("config_dep", []))
        note = "; ".join(g.get("notes", []))
        return f"| {name} | {fmt_attr(g, 'fg')} | {fmt_attr(g, 'bg')} | {g['style'] or ''} | `{ofg}` | {dep} | {note}{extra} |"
    e = effective(name, groups)
    via = " -> ".join(e["via"])
    if "group" in e:
        g = e["group"]
        res = f"{fmt_attr(g, 'fg')} {g['style'] or ''}".strip()
        return f"| {name} | *not set*, resolves {via}: {res} | | | | | nvim fallback{extra} |"
    if "nvim_default" in e:
        return f"| {name} | *not set*, {via}: nvim default `{e['nvim_default']}` | | | | | not themed{extra} |"
    return f"| {name} | *not set, undefined* | | | | | |"


HDR = ["| group | fg | bg | style | original fg | config dep | notes |", "|---|---|---|---|---|---|---|"]
w("## Core syntax (default palette, any background)")
w("")
w("Syntax foregrounds do not depend on background. `original fg` shows the use_original_palette value.")
w("")
L.extend(HDR)
for n in ["Normal", "Comment", "Constant", "String", "Character", "Number", "Boolean", "Float", "Identifier",
          "Function", "Statement", "Conditional", "Repeat", "Label", "Operator", "Keyword", "Exception",
          "PreProc", "Include", "Define", "Macro", "PreCondit", "Type", "StorageClass", "Structure", "Typedef",
          "Special", "Delimiter", "SpecialChar", "SpecialComment", "Todo", "Error", "Title", "Underlined"]:
    w(row(n))
w("")
w("Normal bg: dark `" + P['default']['dark']['background'] + "`, medium `" + P['default']['medium']['background']
  + "`, soft `" + P['default']['soft']['background'] + "`.")
w("")
w("## Treesitter captures")
w("")
w("Unset captures resolve like nvim does: built-in default link first, else strip the last `.part`.")
w("")
L.extend(HDR)
ts = ["@variable", "@variable.builtin", "@variable.parameter", "@parameter", "@parameter.reference",
      "@variable.member", "@field", "@property", "@function", "@function.call", "@function.builtin",
      "@function.method", "@function.method.call", "@method", "@method.call", "@function.macro",
      "@constructor", "@keyword", "@keyword.function", "@keyword.return", "@keyword.operator",
      "@keyword.conditional", "@keyword.repeat", "@keyword.exception", "@keyword.directive",
      "@keyword.import", "@keyword.type", "@keyword.modifier", "@keyword.storage.lifetime", "@conditional",
      "@repeat", "@exception", "@label", "@operator", "@type", "@type.builtin", "@type.qualifier",
      "@type.definition", "@structure", "@string", "@string.escape", "@string.regexp", "@string.special",
      "@character", "@number", "@number.float", "@boolean", "@constant", "@constant.builtin",
      "@constant.macro", "@definition.constant", "@namespace", "@module", "@module.builtin", "@tag",
      "@tag.delimiter", "@tag.attribute", "@tag.builtin", "@attribute", "@attribute.python", "@decorator",
      "@punctuation", "@punctuation.delimiter", "@punctuation.bracket", "@punctuation.special",
      "@comment", "@comment.documentation", "@comment.todo", "@comment.error", "@comment.warning",
      "@comment.note", "@markup", "@markup.heading", "@markup.strong", "@markup.emphasis",
      "@markup.italic", "@markup.underline", "@markup.strike", "@markup.raw", "@markup.list",
      "@markup.link", "@uri", "@error",
      "@variable.python", "@variable.rust", "@variable.cpp", "@variable.javascript"]
for n in ts:
    w(row(n))
w("")
w("## LSP semantic tokens")
w("")
L.extend(HDR)
for n in [k for k in base_entries if k.startswith("@lsp")] + ["@lsp.type.keyword", "@lsp.type.comment",
                                                                   "@lsp.type.string", "@lsp.type.number",
                                                                   "@lsp.mod.deprecated"]:
    w(row(n))
w("")
w("## UI groups (default palette, per background)")
w("")
w("Cells are fg / bg. Background roles change per variant; with `original`, swap fg roles per the palette table.")
w("")
w("| group | roles (fg / bg) | style | dark | medium | soft |")
w("|---|---|---|---|---|---|")
ui = ["Normal", "NormalFloat", "FloatBorder", "CursorLine", "CursorColumn", "ColorColumn", "Visual", "VisualNOS",
      "Search", "IncSearch", "MatchParen", "LineNr", "CursorLineNr", "SignColumn", "FoldColumn", "Folded",
      "Pmenu", "PmenuSel", "PmenuSbar", "PmenuThumb", "StatusLine", "StatusLineNC", "StatusLineTerm",
      "StatusLineTermNC", "TabLine", "TabLineFill", "TabLineSel", "VertSplit", "WinSeparator", "EndOfBuffer",
      "NonText", "Whitespace", "Conceal", "Cursor", "MultiCursor", "Directory", "Question", "QuickFixLine",
      "WildMenu", "ErrorMsg", "WarningMsg", "MoreMsg", "SpellBad", "SpellCap", "DiffAdd", "DiffChange",
      "DiffDelete", "DiffText", "diffAdded", "diffRemoved", "DiagnosticError", "DiagnosticWarn",
      "DiagnosticWarning", "DiagnosticInfo", "DiagnosticInformation", "DiagnosticHint",
      "DiagnosticUnderlineError", "DiagnosticUnderlineWarn", "DiagnosticUnderlineInfo",
      "DiagnosticUnderlineHint", "DiagnosticVirtualTextError", "DiagnosticVirtualTextWarn",
      "DiagnosticVirtualTextInfo", "DiagnosticVirtualTextHint", "GitSignsAdd", "GitSignsChange",
      "GitSignsDelete", "GitSignsCurrentLineBlame", "GitGutterAdd", "GitGutterChange", "GitGutterDelete",
      "IlluminatedWordText", "NvimTreeNormal", "NeoTreeNormal", "CmpDocumentation", "IndentBlanklineChar",
      "IndentBlanklineContextChar"]


def cell(g):
    return f"{g['fg'] or '-'} / {g['bg'] or '-'}"


for n in ui:
    gs = [G["default"][b] for b in BACKGROUNDS]
    if n in gs[0]:
        g = gs[0][n]
        r = g.get("roles", {})
        roles = f"{r.get('fg', g['fg'] or '-')} / {r.get('bg', g['bg'] or '-')}"
        st = (g["style"] or "") + (" (" + "; ".join(g["notes"]) + ")" if "notes" in g else "")
        w(f"| {n} | {roles} | {st} | " + " | ".join(cell(x[n]) for x in gs) + " |")
    else:
        e = effective(n, gs[0])
        via = " -> ".join(e["via"][1:])
        if "group" in e:
            res = [cell(effective(n, x)["group"]) for x in gs]
            w(f"| {n} | *not set*, -> {via} | | " + " | ".join(res) + " |")
        elif "nvim_default" in e:
            w(f"| {n} | *not set*, {('-> ' + via + ' ') if via else ''}nvim default `{e['nvim_default']}` | | | | |")
        else:
            w(f"| {n} | *not set, undefined* | | | | |")
w("")
w("## Quirks found in the source")
w("")
w("- `DiagnosticWarn`/`DiagnosticInfo` are never set: the theme sets the lspsaga-era names `DiagnosticWarning`")
w("  (soft_yellow) and `DiagnosticInformation` (light_blue). Only `DiagnosticError` (red) and `DiagnosticHint`")
w("  (dark_gray) hit real nvim groups. Underline groups keep nvim defaults (sp NvimLight*); VirtualText/Sign")
w("  link to the base Diagnostic group by default. For a port, the intended colours are the lspsaga ones.")
w("- `WinSeparator` is not set; nvim 0.12 links it to `Normal` (and `VertSplit` -> `WinSeparator` by default, but")
w("  the theme overrides `VertSplit` to background_light). Splits therefore draw in Normal fg. Intended: background_light.")
w("- `c.bg_float` (CmpDocumentation, CmpDocumentationBorder) and `c.NONE` (Cursor fg, EasyMotionShade fg) are nil:")
w("  the palette has `none`, not `NONE`, and no `bg_float`. Those attributes are simply not set.")
w("- Transparent block `Cursor = { bg = c.soft_green, c.dark }`: the positional `c.dark` is ignored.")
w("- `@number` is magenta but `Number` is bright_yellow; `@character` is soft_green but `Character` is soft_yellow;")
w("  `@constant` is pink **bold** while `Constant` is plain pink; `@type` is clean_green while `Type` is soft_yellow;")
w("  `@conditional/@repeat` red while `Conditional` is foreground and `Repeat` magenta. With treesitter on, the @ values win.")
w("- No `GitSigns*` sign groups, `Delimiter`, `SpecialChar`, `Tag`, `@attribute`, `@string.*`, `@comment.*` subgroups;")
w("  see the tables above for what nvim falls back to. GitSigns defines its own default links to GitGutter*/diff")
w("  groups at runtime (plugin behaviour, unverified here), so in practice signs likely pick up GitGutterAdd etc.")
w("- nvim built-in defaults come from the local nvim 0.12.5 binary; NvimLight* hex values are not resolved (unverified).")
w("- `FoldColumn fg = \"NONE\"` is the literal string. `style = \"NONE\"` (variable_style default) is dropped.")
w("- `after/queries`: TS/JS capture `(module) @keyword`, shorthand property patterns as `@variable`,")
w("  JSX attribute names as `@attribute` (unset -> Macro -> magenta), Python decorator identifiers as `@decorator`.")
w("- Config-dependent groups: " + ", ".join(f"{n} ({'/'.join(d)})" for n, d in out["config_dependent_groups"].items()) + ".")
w("- `telescope_theme` (off by default) adds " + ", ".join(tele_entries) + "; `transparent_mode` sets background/")
w("  background_dark to NONE and overrides Visual, MultiCursor, Cursor. Both resolved under `conditional` in baby.json.")
w("")
w("## WCAG 2 contrast of each foreground vs Normal bg")
w("")
for pn in PALETTES:
    w(f"### {pn} palette")
    w("")
    w("| fg | roles | vs dark | vs medium | vs soft |")
    w("|---|---|---|---|---|")
    fgs = {}
    for bn in BACKGROUNDS:
        for n, g in G[pn][bn].items():
            v = g["fg"]
            if v and v.startswith("#"):
                fgs.setdefault(v, set()).add(g.get("roles", {}).get("fg", "literal"))
    for v in sorted(fgs, key=lambda x: -lum(x)):
        cs = []
        for bn in BACKGROUNDS:
            bgv = P[pn][bn]["background"]
            cs.append(f"{contrast(v, bgv):.2f}")
        w(f"| `{v}` | {', '.join(sorted(fgs[v]))} | " + " | ".join(cs) + " |")
    w("")
if SUMMARY:
    (SUMMARY / "baby-summary.md").write_text("\n".join(L) + "\n")
print(len(L), "summary lines;", out["counts"])
