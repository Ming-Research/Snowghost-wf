"""The shaping oracle: runs the Whitefoot driver's shape_run over a corpus
and compares every glyph with HarfBuzz.

    python3 tests/font/shape_oracle.py FONT_DIR UDHR_DIR PY_DIR DRIVER

FONT_DIR holds the fonts in FONTS, UDHR_DIR the Universal Declaration of
Human Rights texts in UDHR, and PY_DIR the pinned uharfbuzz (HarfBuzz
14.5.0), which tests/oracle-data.sh installs. The script builds the corpus
in cases(), writes it to a case file in FONT_DIR and runs DRIVER, from the
repository root, as `DRIVER FONT... CASES` with the fonts in FONTS order.
Per case the case file holds a line "FONT SCRIPT COUNT", FONT an index into
FONTS and SCRIPT into SCRIPTS, then a line of COUNT values in lowercase
hexadecimal separated by single spaces (empty for none). The driver loads
each font once with pkg::font::load_face, shapes each case with shape_run,
and prints one line per case: a JSON array of [glyph, cluster, x_advance,
y_advance, x_offset, y_offset] arrays, or a JSON string naming a fault.
HarfBuzz shapes the same values added with add_codepoints into a buffer
whose direction is left to right and whose script is set and language not,
with its default features, font scale equal to units per em, and default
cluster level; each glyph must match exactly.
"""

import json
import os
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ElementTree

FONTS = ["NotoSans-Regular.ttf", "NotoSerif-Regular.ttf"]
SCRIPTS = ["Zyyy", "Latn", "Grek", "Cyrl"]
UDHR = [("udhr_eng.xml", "Latn"), ("udhr_rus.xml", "Cyrl"),
        ("udhr_ell_monotonic.xml", "Grek"), ("udhr_ell_polytonic.xml", "Grek")]
LETTERS = [chr(c) for c in range(0x41, 0x5B)] + [chr(c) for c in range(0x61, 0x7B)]
MARKS = [0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307, 0x308, 0x30A,
         0x30B, 0x30C, 0x323, 0x327, 0x328]


def assigned(value):
    return unicodedata.category(chr(value)) != "Cn"


def cases(udhr_dir):
    """(label, script, values) for every case, shaped with every font."""
    out = []
    for a in LETTERS:
        for b in LETTERS:
            out.append(("pair " + a + b, "Latn", [ord(a), ord(b)]))
    punctuation = "0123456789.,:;!?'\"-()[]/&"
    for a in punctuation:
        for b in punctuation:
            out.append(("punctuation " + a + b, "Latn", [ord(a), ord(b)]))
    for word in ["fi", "fl", "ff", "ffi", "ffl", "fj", "office", "affluent", "fjord",
                 "shuffle", "ﬁ", "Th", "AVATAR", "Wave", "To.", "L'Y"]:
        out.append(("word " + word, "Latn", [ord(c) for c in word]))
    for base in "aeiouyAEIOUYcnszgCNSZG":
        for mark in MARKS:
            out.append(("mark %s+%04X" % (base, mark), "Latn", [ord(base), mark]))
    for base in "aeoAEO":
        for first in MARKS[:4] + [0x308, 0x323]:
            for second in MARKS[:4] + [0x308, 0x323]:
                out.append(("marks %s+%04X+%04X" % (base, first, second), "Latn",
                            [ord(base), first, second]))
    greek = [c for c in range(0x391, 0x3CA) if assigned(c)]
    for c in greek:
        out.append(("greek %04X" % c, "Grek", [c]))
    lower = [c for c in range(0x3B1, 0x3CA) if assigned(c)]
    for a in lower:
        for b in lower:
            out.append(("greek pair %04X %04X" % (a, b), "Grek", [a, b]))
    for c in range(0x1F00, 0x2000):
        if assigned(c):
            out.append(("polytonic %04X" % c, "Grek", [c]))
    cyrillic = list(range(0x410, 0x450))
    for c in cyrillic:
        out.append(("cyrillic %04X" % c, "Cyrl", [c]))
    for a in cyrillic[32:]:
        for b in cyrillic[32:]:
            out.append(("cyrillic pair %04X %04X" % (a, b), "Cyrl", [a, b]))
    for text in ["0123456789", "1+1=2", "(12.5%)", "…", "a — b", ""]:
        out.append(("common %r" % text, "Zyyy", [ord(c) for c in text]))
    for ignorable in [0x200D, 0x200C, 0x00AD, 0x200B, 0x2060, 0xFEFF, 0x034F]:
        out.append(("ignorable %04X" % ignorable, "Latn", [0x61, ignorable, 0x62]))
    for space in range(0x2000, 0x200B):
        out.append(("space %04X" % space, "Latn", [0x61, space, 0x62]))
    out.append(("surrogate", "Latn", [0x61, 0xD800, 0x62]))
    out.append(("beyond", "Latn", [0x61, 0x110000, 0x62]))
    for name, script in UDHR:
        root = ElementTree.parse(os.path.join(udhr_dir, name)).getroot()
        paragraphs = ["".join(node.itertext()).strip() for node in root.iter()
                      if node.tag.endswith("para")]
        for index, text in enumerate(paragraphs):
            out.append(("%s para %d" % (name, index), script, [ord(c) for c in text]))
            decomposed = unicodedata.normalize("NFD", text)
            if decomposed != text:
                out.append(("%s para %d NFD" % (name, index), script,
                            [ord(c) for c in decomposed]))
    return out


def expected(font_path, script, values):
    import uharfbuzz as hb
    with open(font_path, "rb") as file:
        face = hb.Face(file.read())
    font = hb.Font(face)
    buffer = hb.Buffer()
    buffer.add_codepoints(values)
    buffer.direction = "ltr"
    buffer.script = script
    hb.shape(font, buffer)
    return [[info.codepoint, info.cluster, pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset]
            for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)]


def main():
    font_dir, udhr_dir, py_dir, driver = sys.argv[1:5]
    sys.path.insert(0, py_dir)
    import uharfbuzz as hb
    fonts = []
    for name in FONTS:
        with open(os.path.join(font_dir, name), "rb") as file:
            fonts.append(hb.Font(hb.Face(file.read())))
    corpus = cases(udhr_dir)
    runs = []
    for font_index in range(len(FONTS)):
        for label, script, values in corpus:
            runs.append((font_index, label, script, values))
    cases_path = os.path.join(font_dir, "shape-cases.txt")
    wanted = []
    with open(cases_path, "w", encoding="ascii") as file:
        for font_index, label, script, values in runs:
            file.write("%d %d %d\n%s\n" % (font_index, SCRIPTS.index(script), len(values),
                                           " ".join("%x" % v for v in values)))
            buffer = hb.Buffer()
            buffer.add_codepoints(values)
            buffer.direction = "ltr"
            buffer.script = script
            hb.shape(fonts[font_index], buffer)
            wanted.append([[i.codepoint, i.cluster, p.x_advance, p.y_advance, p.x_offset, p.y_offset]
                           for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)])
    arguments = [driver] + [os.path.relpath(os.path.join(font_dir, name)) for name in FONTS]
    run = subprocess.run(arguments + [os.path.relpath(cases_path)], capture_output=True)
    lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = []
    for index, (font_index, label, script, values) in enumerate(runs):
        line = lines[index] if index < len(lines) else None
        try:
            got = json.loads(line) if line is not None else "(no output)"
        except ValueError:
            got = line
        if got != wanted[index]:
            failed.append((FONTS[font_index], label, script, wanted[index], got))
    for font, label, script, want, got in failed[:10]:
        print(f"{font} {script} {label}")
        print(f"  expected {json.dumps(want)[:400]}")
        print(f"  actual   {json.dumps(got)[:400]}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(runs) - len(failed)
    print(f"font_shape: {len(runs)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
