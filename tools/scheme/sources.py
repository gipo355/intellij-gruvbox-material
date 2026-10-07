"""Collects the editor color keys a Darcula- or Default-parented scheme inherits or receives.

Sources, read straight from the installed IDE (nothing is extracted to disk):
  - the Darcula and Default schemes in DefaultColorSchemesManager.xml. Darcula has no parent scheme, so a
    Darcula-parented scheme does not inherit Default-only keys; they are still collected, as extra coverage
  - every file plugins attach via <additionalTextAttributes scheme="Darcula"|"Default" file="..."/>
  - files supplied in code by an <additionalTextAttributesProvider implementation="..."/> extension.
    The provider class is not run; instead every *Darcula*.xml and *Default*.xml resource in the declaring
    plugin's jars that parses as a text-attributes file (a <list> of options, or a <scheme>-like root with
    <attributes>/<colors>) is taken as a Darcula or Default file. intellij-rust, for example, ships
    org/rust/ide/colors/RustDarcula.xml this way. This may over-collect (e.g. a *_legacy variant), which only
    adds required keys.
  - the Islands Dark editor scheme, and "Light" (expUI_lightScheme.xml), the editor scheme Islands Light names
  - keys that exist only in code, with a code default or a fallback key (codekeys.py), from every jar above
"""

import glob
import os
import re
import xml.etree.ElementTree as ET
import zipfile

import codekeys


PLATFORM_JAR = "lib/intellij.platform.ide.impl.jar"
DEFAULT_SCHEMES = "DefaultColorSchemesManager.xml"
ISLANDS_SCHEME = "themes/islands/IslandSchemeDark.xml"
LIGHT_SCHEME = "themes/expUI/expUI_lightScheme.xml"

DECL_RE = re.compile(rb"<additionalTextAttributes\b[^>]*>")
PROVIDER_RE = re.compile(rb"<additionalTextAttributesProvider\b")
CHAIN_SCHEMES = ("Darcula", "Default")
ATTR_RE = re.compile(rb'(\w+)\s*=\s*"([^"]*)"')

# java.awt.Color names some plugins write instead of hex (Jupyter: "gray").
NAMED_COLORS = {"gray": "808080", "grey": "808080", "black": "000000", "white": "ffffff"}


class Plugin:
    def __init__(self, pid, root, jars, user):
        self.pid = pid
        self.root = root
        self.jars = jars
        self.user = user


def _jars_under(path):
    return sorted(glob.glob(os.path.join(path, "**", "*.jar"), recursive=True))


def _platform_jars(ide_home):
    return sorted(glob.glob(os.path.join(ide_home, "lib", "*.jar")))


def discover_plugins(ide_home, user_plugins):
    plugins = [Plugin("platform", os.path.join(ide_home, "lib"), _platform_jars(ide_home), False)]
    for d in sorted(glob.glob(os.path.join(ide_home, "plugins", "*"))):
        if os.path.isdir(d):
            plugins.append(Plugin(os.path.basename(d), d, _jars_under(d), False))
    if user_plugins and os.path.isdir(user_plugins):
        for d in sorted(glob.glob(os.path.join(user_plugins, "*"))):
            name = os.path.basename(d)
            if os.path.isdir(d):
                jars = _jars_under(os.path.join(d, "lib"))
            elif name.endswith(".jar"):
                jars = [d]
                name = name[: -len(".jar")]
            else:
                continue
            if jars:
                plugins.append(Plugin(name, d, jars, True))
    return plugins


def _is_descriptor(entry):
    if not entry.endswith(".xml"):
        return False
    return entry.startswith("META-INF/") or "/" not in entry


def _open(jar):
    try:
        return zipfile.ZipFile(jar)
    except (zipfile.BadZipFile, OSError):
        return None


def find_declarations(plugin):
    """-> (sorted unique (scheme, resource path) the plugin attaches to Darcula or Default, has a provider EP?)"""
    files = set()
    provider = False
    for jar in plugin.jars:
        z = _open(jar)
        if z is None:
            continue
        with z:
            for entry in z.namelist():
                if not _is_descriptor(entry):
                    continue
                data = z.read(entry)
                if b"additionalTextAttributes" not in data:
                    continue
                provider = provider or bool(PROVIDER_RE.search(data))
                for tag in DECL_RE.findall(data):
                    attrs = {k.decode(): v.decode() for k, v in ATTR_RE.findall(tag)}
                    if attrs.get("scheme") in CHAIN_SCHEMES and attrs.get("file"):
                        files.add((attrs["scheme"], attrs["file"].lstrip("/")))
    return sorted(files), provider


def provider_files(plugin):
    """-> sorted (scheme, path, data) for the plugin's *Darcula*.xml / *Default*.xml text-attributes resources."""
    found = {}
    for jar in plugin.jars:
        z = _open(jar)
        if z is None:
            continue
        with z:
            for entry in z.namelist():
                base = entry.rsplit("/", 1)[-1]
                scheme = next((s for s in CHAIN_SCHEMES if s in base), None)
                if scheme is None or not base.endswith(".xml") or entry in found:
                    continue
                data = z.read(entry)
                if _is_text_attributes(data):
                    found[entry] = (scheme, entry, data)
    return [found[e] for e in sorted(found)]


def _is_text_attributes(data):
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return False
    if root.tag == "list":
        return any(o.tag == "option" and o.find("value") is not None for o in root)
    return root.find("attributes") is not None or root.find("colors") is not None


def read_resource(jars, path):
    for jar in jars:
        z = _open(jar)
        if z is None:
            continue
        with z:
            if path in z.namelist():
                return z.read(path)
    return None


def _norm_color(raw):
    """IntelliJ writes ints in hex without padding ('0', 'ff', '8000'); 8 digits carry alpha."""
    if raw is None or raw == "":
        return ""
    raw = raw.strip().lower().lstrip("#")
    raw = NAMED_COLORS.get(raw, raw)
    if not re.fullmatch(r"[0-9a-f]{1,8}", raw):
        raise ValueError(f"unknown color value {raw!r}")
    if len(raw) <= 6:
        return raw.rjust(6, "0")
    return raw.rjust(8, "0")


def _parse_value(value_el):
    fields = {}
    for o in value_el.findall("option"):
        name, val = o.get("name"), o.get("value")
        if val is None:
            continue
        if name in ("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR"):
            fields[name] = _norm_color(val)
        else:
            fields[name] = val
    return fields


def parse_attribute_options(options):
    """<option name=K [baseAttributes=B]>[<value>...</value>]</option> -> {K: {"base": B|None, "value": dict|None}}"""
    out = {}
    for o in options:
        if o.tag != "option":
            continue
        v = o.find("value")
        out[o.get("name")] = {
            "base": o.get("baseAttributes"),
            "value": None if v is None else _parse_value(v),
        }
    return out


def parse_colors(colors_el):
    return {o.get("name"): _norm_color(o.get("value")) for o in colors_el.findall("option")}


def parse_scheme(scheme_el):
    colors = scheme_el.find("colors")
    attrs = scheme_el.find("attributes")
    return {
        "colors": parse_colors(colors) if colors is not None else {},
        "attributes": parse_attribute_options(list(attrs)) if attrs is not None else {},
    }


def parse_plugin_file(data):
    """Plugin files are either a flat <list> of attribute options or a <scheme>-like root."""
    root = ET.fromstring(data)
    if root.find("attributes") is not None or root.find("colors") is not None:
        return parse_scheme(root)
    return {"colors": {}, "attributes": parse_attribute_options(list(root))}


def collect(ide_home, user_plugins):
    platform_jar = os.path.join(ide_home, PLATFORM_JAR)
    schemes = ET.fromstring(read_resource([platform_jar], DEFAULT_SCHEMES))
    by_name = {s.get("name"): parse_scheme(s) for s in schemes.iter("scheme")}
    islands = parse_scheme(ET.fromstring(read_resource([platform_jar], ISLANDS_SCHEME)))
    light = parse_scheme(ET.fromstring(read_resource([platform_jar], LIGHT_SCHEME)))

    plugins = discover_plugins(ide_home, user_plugins)
    platform = plugins[0]
    contributions = []  # (plugin id, user?, scheme, file, parsed)
    unresolved = []
    for p in plugins:
        declared, provider = find_declarations(p)
        seen = set()
        for scheme, f in declared:
            data = read_resource(p.jars, f)
            if data is None and p is not platform:
                data = read_resource(platform.jars, f)
            if data is None:
                unresolved.append((p.pid, f))
                continue
            seen.add(f)
            contributions.append((p.pid, p.user, scheme, f, parse_plugin_file(data)))
        if provider:
            for scheme, f, data in provider_files(p):
                if f not in seen:
                    contributions.append((p.pid, p.user, scheme, f, parse_plugin_file(data)))
    return {
        "darcula": by_name["Darcula"],
        "default": by_name["Default"],
        "islands": islands,
        "light": light,
        "contributions": contributions,
        "unresolved": unresolved,
        "plugins": [(p.pid, p.user) for p in plugins],
        "code": codekeys.scan(jar for p in plugins for jar in p.jars),
    }
