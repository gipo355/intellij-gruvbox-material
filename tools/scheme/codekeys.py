"""Editor color keys that exist only in code, read from the bytecode of the installed IDE and plugins.

A key created as TextAttributesKey.createTextAttributesKey(name, TextAttributes), ColorKey.createColorKey(name, Color)
or FileStatusFactory.createFileStatus(id, ..., Color) carries its default in code: no scheme XML mentions it, so
sources.py never sees it and the IDE paints the code default under any theme that does not set it. Keys created
with a fallback key (createTextAttributesKey(name, KEY), createColorKeyWithFallback) are recorded with that link,
so a chain ending on a restricted key (CONSOLE_BLUE_OUTPUT) can be caught.

The scan is static. Within one statement (since the previous field store, pop or return): a fallback call's key name is
the last string constant pushed before its fallback, a static field or Kotlin getter; a default call's is the last
string pushed (the default is built from numbers); a file status id is the first string, ahead of its description.
Enum constructors push the constant's own name first, hence not simply "the first string". Names built at runtime
are skipped.
"""

import struct
import zipfile

TAK = "com/intellij/openapi/editor/colors/TextAttributesKey"
CK = "com/intellij/openapi/editor/colors/ColorKey"
FSF = "com/intellij/openapi/vcs/FileStatusFactory"
MARKERS = (TAK.encode(), CK.encode(), FSF.encode())

# Opcodes after which the operand stack holds no pending call arguments: pop, aastore, return, putstatic/putfield.
# Local stores are not boundaries: Kotlin's apply { } parks the half-built default in a local.
BOUNDARIES = {0x57, 0x58, 0x53, 0xb0, 0xb1, 0xb3, 0xb5}
INVOKES = {0xb6, 0xb7, 0xb8, 0xb9}


def _op_length(code, pc):
    op = code[pc]
    if op in (0xaa, 0xab):
        pad = (4 - (pc + 1) % 4) % 4
        base = pc + 1 + pad
        if op == 0xaa:
            low, high = struct.unpack_from(">ii", code, base + 4)
            return 1 + pad + 12 + 4 * (high - low + 1)
        pairs = struct.unpack_from(">i", code, base + 4)[0]
        return 1 + pad + 8 + 8 * pairs
    if op == 0xc4:
        return 6 if code[pc + 1] == 0x84 else 4
    if op in (0x10, 0x12, 0xbc, 0xa9) or 0x15 <= op <= 0x19 or 0x36 <= op <= 0x3a:
        return 2
    if op in (0x11, 0x13, 0x14, 0x84, 0xbb, 0xbd, 0xc0, 0xc1, 0xc6, 0xc7) or 0x99 <= op <= 0xa8 or 0xb2 <= op <= 0xb8:
        return 3
    if op == 0xc5:
        return 4
    if op in (0xb9, 0xba, 0xc8, 0xc9):
        return 5
    return 1


def _constant_pool(data):
    count = struct.unpack_from(">H", data, 8)[0]
    pool = [None] * count
    pos, i = 10, 1
    while i < count:
        tag = data[pos]
        if tag == 1:
            n = struct.unpack_from(">H", data, pos + 1)[0]
            pool[i] = (1, data[pos + 3: pos + 3 + n].decode("utf-8", "replace"))
            pos += 3 + n
        elif tag in (3, 4):
            pos += 5
        elif tag in (5, 6):
            pos += 9
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            pool[i] = (tag, struct.unpack_from(">H", data, pos + 1)[0])
            pos += 3
        elif tag == 15:
            pos += 4
        elif tag in (9, 10, 11, 12, 17, 18):
            pool[i] = (tag, *struct.unpack_from(">HH", data, pos + 1))
            pos += 5
        else:
            raise ValueError(f"constant tag {tag}")
        i += 1
    return pool, pos


def _member(pool, index):
    """-> (owner, name, descriptor) of a field or method ref."""
    _tag, cls, nat = pool[index]
    _t, name, desc = pool[nat]
    return pool[pool[cls][1]][1], pool[name][1], pool[desc][1]


def _bootstrap_name(pool, index):
    return pool[pool[pool[index][2]][1]][1]


def _string(pool, index):
    entry = pool[index]
    return pool[entry[1]][1] if entry and entry[0] == 8 else None


def _code_attributes(data, pos, pool):
    pos += 6  # access, this, super
    interfaces = struct.unpack_from(">H", data, pos)[0]
    pos += 2 + 2 * interfaces
    for _section in range(2):  # fields, then methods
        members = struct.unpack_from(">H", data, pos)[0]
        pos += 2
        for _ in range(members):
            attrs = struct.unpack_from(">H", data, pos + 6)[0]
            pos += 8
            for _ in range(attrs):
                name, length = struct.unpack_from(">HI", data, pos)
                if _section == 1 and pool[name][1] == "Code":
                    code_length = struct.unpack_from(">I", data, pos + 10)[0]
                    yield data[pos + 14: pos + 14 + code_length]
                pos += 6 + length


def _call(owner, name, desc):
    if owner == TAK and name == "createTextAttributesKey":
        if "TextAttributesKey;)" in desc:
            return "attr", "fallback"
        return "attr", "default" if "TextAttributes;)" in desc else "plain"
    if owner == CK and name == "createColorKey":
        return "color", "default" if "Color;)" in desc else "plain"
    if owner == CK and name == "createColorKeyWithFallback":
        return "color", "fallback"
    if owner == FSF and name == "createFileStatus":
        return ("status", "default") if "java/awt/Color" in desc else None
    return None


def scan_class(data):
    """-> [(kind, how, key name, fallback ref or None, static field the key is stored in or None)]."""
    pool, pos = _constant_pool(data)
    calls = []
    for code in _code_attributes(data, pos, pool):
        strings, refs = [], []
        pc = last = 0
        while pc < len(code):
            op = code[pc]
            step = _op_length(code, pc)
            if op in (0x12, 0x13):
                s = _string(pool, code[pc + 1] if op == 0x12 else struct.unpack_from(">H", code, pc + 1)[0])
                if s is not None:
                    strings.append((pc, s))
            elif op == 0xb2:
                owner, name, _d = _member(pool, struct.unpack_from(">H", code, pc + 1)[0])
                refs.append((pc, f"{owner}.{name}"))
            elif op in INVOKES:
                owner, name, desc = _member(pool, struct.unpack_from(">H", code, pc + 1)[0])
                found = _call(owner, name, desc)
                if found and found[1] == "default" and code[last] == 0x01:
                    found = (found[0], "plain")  # aconst_null: no default after all
                if owner == "kotlin/jvm/internal/Intrinsics" and strings:
                    strings.pop()  # the null-check message, e.g. "createTextAttributesKey(...)"
                elif found:
                    nxt = pc + step
                    # dup, checkcast, and Kotlin's null check (ldc message; invokestatic Intrinsics.*) before the store
                    while nxt < len(code) and (code[nxt] in (0x59, 0xc0, 0x12, 0x13) or code[nxt] == 0xb8 and _member(
                            pool, struct.unpack_from(">H", code, nxt + 1)[0])[0] == "kotlin/jvm/internal/Intrinsics"):
                        nxt += _op_length(code, nxt)
                    stored = None
                    if nxt < len(code) and code[nxt] == 0xb3:
                        o, n, _d = _member(pool, struct.unpack_from(">H", code, nxt + 1)[0])
                        stored = f"{o}.{n}"
                    key = None
                    if found[0] == "status":
                        key = strings[0][1] if strings else None
                    elif found[1] == "fallback" and refs:
                        key = next((s for at, s in reversed(strings) if at < refs[-1][0]), None)
                    elif strings:
                        key = strings[-1][1]
                    if key is not None:
                        calls.append((*found, key, refs[-1][1] if found[1] == "fallback" and refs else None, stored))
                    strings, refs = [], []
                elif (owner, name) in (("java/lang/String", "concat"), ("java/lang/StringBuilder", "toString")):
                    strings = []  # a name built at runtime
                elif name.startswith("get") and desc.startswith("()L") and op in (0xb6, 0xb8):
                    refs.append((pc, f"{owner}.{name[3:]}"))
            elif op == 0xba and _bootstrap_name(pool, struct.unpack_from(">H", code, pc + 1)[0]) == "makeConcatWithConstants":
                strings = []  # a name built at runtime
            if op == 0x57 and refs and refs[-1][0] == last:
                refs.pop()  # Kotlin object access: getstatic INSTANCE; pop
            elif op in BOUNDARIES:
                strings, refs = [], []
            last = pc
            pc += step
    return calls


def scan(jars):
    """-> {key name: {"kind", "how": default|fallback|plain, "fallback": key name or None, "jars": {basename}}}."""
    raw, fields = [], {}
    for jar in jars:
        try:
            zf = zipfile.ZipFile(jar)
        except (zipfile.BadZipFile, OSError):
            continue
        with zf:
            for entry in zf.namelist():
                if not entry.endswith(".class"):
                    continue
                data = zf.read(entry)
                if not any(m in data for m in MARKERS):
                    continue
                try:
                    calls = scan_class(data)
                except (ValueError, IndexError, struct.error, TypeError):
                    continue
                for kind, how, name, ref, stored in calls:
                    raw.append((kind, how, name, ref, jar))
                    if stored:
                        fields[stored] = name
    keys = {}
    for kind, how, name, ref, jar in raw:
        if kind == "status":
            kind, name = "color", "FILESTATUS_" + name
        entry = keys.setdefault(name, {"kind": kind, "how": how, "fallback": None, "jars": set()})
        entry["jars"].add(jar.replace("\\", "/").rsplit("/", 1)[-1])
        if how == "default" or entry["how"] == "plain":
            entry["how"] = how
        if ref:
            entry["fallback"] = entry["fallback"] or fields.get(ref)
    return keys
