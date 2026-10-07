"""Collect every ui key that any *.theme.json shipped with the IDE or a user-installed plugin sets.
This theme's own installed copy is skipped, so the list never learns keys from it.

Usage: IDEA_HOME=<IDE install dir> IDEA_PLUGINS_DIR=<user plugins dir> \
       python3 -I tools/ui/known_ui_keys.py > src/test/resources/known-ui-keys.txt
"""
import glob
import json
import os
import re
import sys
import zipfile

OWN_PLUGIN_ID = b"<id>dev.gipo.gruvboxmaterial</id>"
OWN_PLUGIN_DIR = "gruvbox-material-islands"


def flatten(node, prefix=""):
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten(value, path)
        else:
            yield path


def merge_pairs(pairs):
    # Duplicate object keys (e.g. "ComboBox" twice in ManyIslandsDarcula) are all applied by the IDE.
    out = {}
    for key, value in pairs:
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_pairs([*out[key].items(), *value.items()])
        else:
            out[key] = value
    return out


def loads(text):
    # A few bundled themes carry // comments or trailing commas.
    try:
        return json.loads(text, object_pairs_hook=merge_pairs)
    except json.JSONDecodeError:
        text = re.sub(r'^\s*//.*$', "", text, flags=re.M)
        text = re.sub(r",(\s*[}\]])", r"\1", text)
        return json.loads(text, object_pairs_hook=merge_pairs)


def is_own(path, config_home):
    return os.path.relpath(path, config_home).split(os.sep)[0] == OWN_PLUGIN_DIR


def themes(ide_home, config_home):
    jars = glob.glob(os.path.join(ide_home, "lib", "*.jar"))
    jars += glob.glob(os.path.join(ide_home, "plugins", "**", "*.jar"), recursive=True)
    jars += [j for j in glob.glob(os.path.join(config_home, "**", "*.jar"), recursive=True) if not is_own(j, config_home)]
    for jar in sorted(set(jars)):
        try:
            with zipfile.ZipFile(jar) as zf:
                names = zf.namelist()
                if "META-INF/plugin.xml" in names and OWN_PLUGIN_ID in zf.read("META-INF/plugin.xml"):
                    continue
                for name in names:
                    if name.endswith(".theme.json"):
                        yield f"{jar}!{name}", zf.read(name).decode("utf-8-sig")
        except (zipfile.BadZipFile, OSError):
            continue
    for path in glob.glob(os.path.join(config_home, "**", "*.theme.json"), recursive=True):
        if is_own(path, config_home):
            continue
        with open(path, encoding="utf-8-sig") as fh:
            yield path, fh.read()

def env_dir(name):
    path = os.environ.get(name)
    if not path:
        sys.exit(f"{name} is not set (see the usage line at the top of this script)")
    if not os.path.isdir(path):
        sys.exit(f"{name}={path} is not a directory")
    return path


def main():
    ide_home = env_dir("IDEA_HOME")
    config_home = env_dir("IDEA_PLUGINS_DIR")
    keys = set()
    count = 0
    for origin, text in themes(ide_home, config_home):
        try:
            ui = loads(text).get("ui", {})
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"skip {origin}: {e}", file=sys.stderr)
            continue
        count += 1
        keys.update(flatten(ui))
    print(f"{count} themes, {len(keys)} keys", file=sys.stderr)
    sys.stdout.write("".join(k + "\n" for k in sorted(keys)))


if __name__ == "__main__":
    main()
