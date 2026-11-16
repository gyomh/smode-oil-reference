# -*- coding: utf-8 -*-
"""CLASSES.md from a catalogue of SMODE classes: python gen_classes.py <catalog.json> [CLASSES.md]

catalog.json is a list of {"cls": "<Oil class>", "vars": [{"path", "type", "cls", "value", "options"?}], "presets": ["<lib>|<name>"]}
as the Node Editor's agent writes it ("catalog" task: Oil.createObject(cls) on a throwaway object, variables walked two
levels deep; angles converted to degrees, colours to hex)."""
import io, json, os, re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "catalog.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "CLASSES.md")
cat = json.load(open(SRC, encoding="utf-8"))

FAMILIES = [
    ("Texture modifiers (`layer.generator.modifiers`, `compo.modifiers`, `renderer.effects`)", lambda c: c.endswith("TextureModifier")),
    ("Texture masks (`MaskTextureModifier.masks`, `modifier.masks`)", lambda c: c.endswith("TextureMask")),
    ("Texture generators (`TextureLayer.generator`, a material map, a mask image)", lambda c: c.endswith("TextureGenerator")),
    ("3D colour sources of a PBR channel (no UV)", lambda c: c in ("Gradient3dColorizer", "CheckerBoard3dTexture", "UVW3dTexture")),
    ("Geometry generators (`GeometryLayer.generator`)", lambda c: c.endswith("GeometryGenerator")),
    ("Shapes and layers", lambda c: True),
]
ANGLE_NOTE = "angles are listed in degrees (Oil stores radians: `set(math.radians(x))`)"


def fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        s = ("%.4f" % v).rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    return str(v)


def esc(s):
    return str(s).replace("|", "\\|")


lines = []
lines.append("# SMODE R15 classes and their settings (read by script)")
lines.append("")
lines.append("Generated from the catalogue of the Node Editor (16/11/2026): each class was created with `Oil.createObject(cls)` on a")
lines.append("throwaway object and its variables walked (`getNumVariables` / `getVariableName` / `getVariable`), two levels deep")
lines.append("inside composite values. Columns: the path to write (`obj.<path>.set(...)`), the Oil class of the variable, the default")
lines.append("value of a fresh object, the choices of an enumeration (index order: `set(i)` or `set(\"name\")`). Colours are shown as")
lines.append("hex; " + ANGLE_NOTE + ". `Percentage` takes 0..1 in `set()` and")
lines.append("prints x100 in `toString()`. Variables that hold objects, pointers, vectors, strings and transports are left out: see the README")
lines.append("for those (masks, maps, players, references). Presets: the libraries of `packs/Standard Pack/Presets` that have a file for the")
lines.append("class (`Default`, `Advanced Presets`); setting `preset.presetName` does not apply one (see the README).")
lines.append("")
lines.append("Classes: %d. Settings: %d." % (len(cat), sum(len(e.get("vars") or []) for e in cat)))
lines.append("")

done = set()
toc = []
sections = []
for title, test in FAMILIES:
    items = [e for e in cat if e["cls"] not in done and test(e["cls"])]
    if not items:
        continue
    items.sort(key=lambda e: e["cls"])
    anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    toc.append("- [%s](#%s): %s" % (title.split(" (")[0], anchor, ", ".join("`%s`" % e["cls"] for e in items)))
    sec = ["## " + title, ""]
    for e in items:
        done.add(e["cls"])
        sec.append("### `%s`" % e["cls"])
        sec.append("")
        if e.get("error"):
            sec.append("Could not be read: `%s`" % e["error"])
            sec.append("")
            continue
        pres = e.get("presets") or []
        if pres:
            libs = {}
            for p in pres:
                lib, _, name = p.partition("|")
                libs.setdefault(lib, []).append(name)
            sec.append("Presets: " + " ; ".join("**%s** (%s)" % (lib, ", ".join(names)) for lib, names in libs.items()))
            sec.append("")
        vs = e.get("vars") or []
        if not vs:
            sec.append("No plain setting (objects, pointers or vectors only).")
            sec.append("")
            continue
        sec.append("| path | Oil class | default | choices |")
        sec.append("|---|---|---|---|")
        for v in vs:
            opts = ", ".join(v.get("options") or [])
            val = v.get("value")
            if v.get("type") == "enum" and v.get("options") and isinstance(val, int) and 0 <= val < len(v["options"]):
                val = "%d (%s)" % (val, v["options"][val])
            sec.append("| `%s` | `%s` | %s | %s |" % (v["path"], v.get("cls", ""), esc(fmt(val)), esc(opts)))
        sec.append("")
    sections.append("\n".join(sec))

lines.append("## Contents")
lines.append("")
lines += toc
lines.append("")
lines += sections
text = "\n".join(lines).rstrip() + "\n"
io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print("written", OUT, len(text), "chars,", len(done), "classes")
