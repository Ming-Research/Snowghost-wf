"""The font face oracle: runs the Whitefoot driver over the pinned fonts and
corrupted variants of them, comparing with fontTools.

    python3 tests/font/face_oracle.py FONT_DIR PY_DIR DRIVER

FONT_DIR holds the fonts in FONTS; PY_DIR holds the pinned fontTools
(tests/oracle-data.sh installs it). For each font the script runs DRIVER,
from the repository root, as `DRIVER FONT`, which loads the font with
pkg::font::load_face and prints, one item per line:

    metrics UPEM GLYPHS HHEA_ASC HHEA_DESC HHEA_GAP TYPO_ASC TYPO_DESC
            TYPO_GAP USE_TYPO WIN_ASC WIN_DESC      (on one line)
    cmap SCALAR GLYPH     for every scalar value, ascending, whose glyph
                          nominal_glyph returns is not 0 (SCALAR in hex)
    advance GLYPH ADVANCE for every glyph, ascending
    class GLYPH CLASS     for every glyph, CLASS 0 to 4 as GlyphClass
                          orders them
    end

or, when load_face refuses the font, the one line `refused Invalid`,
`refused Unsupported` or `refused TooLarge`. Numbers are decimal except
SCALAR; USE_TYPO is 0 or 1. The script computes the same lines with
fontTools and compares them. It also writes corrupted copies of the first
font (corruptions()) beside the fonts. A corrupted core table must be
refused as listed; a corrupted GDEF, GSUB or GPOS table must be ignored, so
the copy dumps as the intact font does, with every class 0 when GDEF is the
one ignored.
"""

import os
import struct
import subprocess
import sys

FONTS = ["NotoSans-Regular.ttf", "NotoSerif-Regular.ttf"]
INTACT = "intact"
NO_GDEF = "no GDEF"


def expected_dump(path):
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    head, hhea, maxp = font["head"], font["hhea"], font["maxp"]
    os2 = font["OS/2"] if "OS/2" in font else None
    lines = ["metrics %d %d %d %d %d %d %d %d %d %d %d" % (
        head.unitsPerEm, maxp.numGlyphs, hhea.ascent, hhea.descent, hhea.lineGap,
        os2.sTypoAscender if os2 else 0, os2.sTypoDescender if os2 else 0,
        os2.sTypoLineGap if os2 else 0, 1 if os2 and os2.fsSelection & 0x80 else 0,
        os2.usWinAscent if os2 else 0, os2.usWinDescent if os2 else 0)]
    order = font.getGlyphOrder()
    ids = {name: index for index, name in enumerate(order)}
    cmap = best_cmap(font)
    for scalar in sorted(cmap):
        glyph = ids[cmap[scalar]]
        if glyph != 0 and not 0xD800 <= scalar <= 0xDFFF:
            lines.append("cmap %x %d" % (scalar, glyph))
    metrics = font["hmtx"].metrics
    for index, name in enumerate(order):
        lines.append("advance %d %d" % (index, metrics[name][0]))
    classes = {}
    if "GDEF" in font and font["GDEF"].table.GlyphClassDef is not None:
        classes = font["GDEF"].table.GlyphClassDef.classDefs
    for index, name in enumerate(order):
        lines.append("class %d %d" % (index, classes.get(name, 0)))
    lines.append("end")
    return lines


def best_cmap(font):
    """The subtable load_face's doc names: the first present of these
    platform and encoding pairs whose format is 4 or 12."""
    for platform, encoding in ((3, 10), (0, 6), (0, 4), (3, 1), (0, 3), (0, 2), (0, 1), (0, 0)):
        for table in font["cmap"].tables:
            if (table.platformID, table.platEncID) == (platform, encoding) and table.format in (4, 12):
                return table.cmap
    return {}


def table_records(data):
    count = struct.unpack(">H", data[4:6])[0]
    records = {}
    for index in range(count):
        at = 12 + 16 * index
        tag = data[at:at + 4].decode("latin-1")
        offset, length = struct.unpack(">II", data[at + 8:at + 16])
        records[tag] = (at, offset, length)
    return records


def corruptions(data):
    """Copies of a font with what load_face must do with each: the one line
    of a refusal, or INTACT (dump as the intact font) or NO_GDEF (dump as
    the intact font with every class 0) for an ignored layout table."""
    records = table_records(data)
    out = []
    for cut in (0, 11, 12 + 16, len(data) // 2, len(data) - 1):
        out.append(("truncated-%d" % cut, data[:cut], "refused Invalid"))
    changed = bytearray(data)
    at = records["glyf"][0]
    struct.pack_into(">I", changed, at + 8, len(data) + 16)
    out.append(("record-past-end", bytes(changed), "refused Invalid"))
    changed = bytearray(data)
    struct.pack_into(">H", changed, 4, 0x7FFF)
    out.append(("too-many-tables", bytes(changed), "refused Invalid"))
    changed = bytearray(data)
    _, cmap, cmap_length = records["cmap"]
    subtables = struct.unpack(">H", data[cmap + 2:cmap + 4])[0]
    for index in range(subtables):
        struct.pack_into(">I", changed, cmap + 4 + 8 * index + 4, cmap_length + 64)
    out.append(("cmap-subtable-past-table", bytes(changed), "refused Invalid"))
    changed = bytearray(data)
    _, gsub, gsub_length = records["GSUB"]
    assert gsub_length < 0xFFF0
    struct.pack_into(">H", changed, gsub + 8, 0xFFF0)
    out.append(("gsub-lookup-list-past-table", bytes(changed), INTACT))
    changed = bytearray(data)
    _, gpos, gpos_length = records["GPOS"]
    lookups = gpos + struct.unpack(">H", data[gpos + 8:gpos + 10])[0]
    first = lookups + struct.unpack(">H", data[lookups + 2:lookups + 4])[0]
    assert first + 6 + 2 * 0xFFFF > gpos + gpos_length
    struct.pack_into(">H", changed, first + 4, 0xFFFF)
    out.append(("gpos-subtable-count-past-table", bytes(changed), INTACT))
    changed = bytearray(data)
    _, gdef, gdef_length = records["GDEF"]
    assert gdef_length < 0xFFF0
    struct.pack_into(">H", changed, gdef + 4, 0xFFF0)
    out.append(("gdef-class-definition-past-table", bytes(changed), NO_GDEF))
    changed = bytearray(data)
    _, hhea, _ = records["hhea"]
    struct.pack_into(">H", changed, hhea + 34, 0)
    out.append(("no-horizontal-metrics", bytes(changed), "refused Invalid"))
    out.append(("collection", b"ttcf" + data[4:], "refused Unsupported"))
    out.append(("woff2", b"wOF2" + data[4:], "refused Unsupported"))
    return out


def run(driver, path):
    result = subprocess.run([driver, os.path.relpath(path)], capture_output=True)
    return result.stdout.decode("utf-8", "replace").splitlines(), result


def main():
    font_dir, py_dir, driver = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.path.insert(0, py_dir)
    cases, failed = 0, 0
    for name in FONTS:
        path = os.path.join(font_dir, name)
        want = expected_dump(path)
        got, result = run(driver, path)
        cases += 1
        if got != want or result.returncode != 0:
            failed += 1
            print(f"{name}: dump differs (exit {result.returncode}, {len(got)} lines, expected {len(want)})")
            shown = 0
            for index in range(max(len(got), len(want))):
                a = got[index] if index < len(got) else "(missing)"
                b = want[index] if index < len(want) else "(missing)"
                if a != b:
                    print(f"  line {index + 1}: expected {b!r}, actual {a!r}")
                    shown += 1
                    if shown == 10:
                        break
            if result.stderr:
                print("  " + result.stderr.decode("utf-8", "replace")[-500:])
    with open(os.path.join(font_dir, FONTS[0]), "rb") as file:
        data = file.read()
    intact = expected_dump(os.path.join(font_dir, FONTS[0]))
    no_gdef = [line if not line.startswith("class ") else " ".join(line.split()[:2] + ["0"])
               for line in intact]
    for label, corrupted, want in corruptions(data):
        path = os.path.join(font_dir, "corrupt-%s.ttf" % label)
        with open(path, "wb") as file:
            file.write(corrupted)
        got, result = run(driver, path)
        cases += 1
        lines = intact if want == INTACT else no_gdef if want == NO_GDEF else [want]
        if got != lines or result.returncode != 0:
            failed += 1
            first = next((i for i in range(max(len(got), len(lines)))
                          if i >= len(got) or i >= len(lines) or got[i] != lines[i]), 0)
            expected = lines[first] if first < len(lines) else "(missing)"
            actual = got[first] if first < len(got) else "(missing)"
            print(f"{label}: expected {want!r}; line {first + 1}: expected {expected!r}, "
                  f"actual {actual!r} (exit {result.returncode})")
    print(f"font_face: {cases} cases, {cases - failed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
