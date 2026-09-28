"""The text properties oracle: runs the Whitefoot driver over every code
point and a set of composition pairs, comparing with the Unicode Character
Database.

    python3 tests/text/properties_oracle.py UCD_DIR DRIVER

UCD_DIR holds Unicode 17.0.0's UnicodeData.txt, DerivedGeneralCategory.txt,
DerivedNormalizationProps.txt and emoji-data.txt (tests/oracle-data.sh
fetches them). The script writes a pair file in UCD_DIR and runs DRIVER,
from the repository root, as `DRIVER PAIRS`. The driver prints one line
`CODE GC CCC EP DECOMPOSITION` per code point from 0 to 10FFFF and then one
line `C FIRST SECOND RESULT` per pair, as
renderer/oracle/text_properties/module.wfm describes; this script computes
the same lines from the files and compares them. The pairs are every
two-character canonical decomposition in UnicodeData.txt, each expected to
compose to its primary composite unless Full_Composition_Exclusion holds,
every arithmetic Hangul composition, and pairs that compose to nothing.
"""

import os
import subprocess
import sys

S_BASE, L_BASE, V_BASE, T_BASE = 0xAC00, 0x1100, 0x1161, 0x11A7
L_COUNT, V_COUNT, T_COUNT = 19, 21, 28
N_COUNT = V_COUNT * T_COUNT
S_COUNT = L_COUNT * N_COUNT


def ranges(path, wanted=None):
    """(first, last, value) for each data line of a UCD property file,
    keeping only lines whose value is in wanted when it is given."""
    out = []
    with open(path, encoding="utf-8") as file:
        for line in file:
            data = line.split("#", 1)[0].strip()
            if not data:
                continue
            fields = [field.strip() for field in data.split(";")]
            span, value = fields[0], fields[1]
            if wanted is not None and value not in wanted:
                continue
            first, _, last = span.partition("..")
            out.append((int(first, 16), int(last or first, 16), value))
    return out


def unicode_data(path):
    """Canonical combining classes and canonical decompositions by code
    point, from UnicodeData.txt; range entries carry neither."""
    ccc, decomposition = {}, {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            fields = line.rstrip("\n").split(";")
            code = int(fields[0], 16)
            if fields[1].endswith(", Last>"):
                continue
            if fields[3] != "0":
                ccc[code] = int(fields[3])
            mapping = fields[5]
            if mapping and not mapping.startswith("<"):
                parts = [int(part, 16) for part in mapping.split()]
                decomposition[code] = (parts[0], parts[1] if len(parts) == 2 else 0)
    return ccc, decomposition


def hangul_decomposition(code):
    index = code - S_BASE
    if not 0 <= index < S_COUNT:
        return None
    trailing = index % T_COUNT
    if trailing == 0:
        return (L_BASE + index // N_COUNT, V_BASE + (index % N_COUNT) // T_COUNT)
    return (code - trailing, T_BASE + trailing)


def expected(ucd_dir):
    categories = ["Cn"] * 0x110000
    for first, last, value in ranges(os.path.join(ucd_dir, "DerivedGeneralCategory.txt")):
        for code in range(first, last + 1):
            categories[code] = value
    pictographic = bytearray(0x110000)
    for first, last, _ in ranges(os.path.join(ucd_dir, "emoji-data.txt"), {"Extended_Pictographic"}):
        for code in range(first, last + 1):
            pictographic[code] = 1
    ccc, decomposition = unicode_data(os.path.join(ucd_dir, "UnicodeData.txt"))
    excluded = set()
    for first, last, _ in ranges(os.path.join(ucd_dir, "DerivedNormalizationProps.txt"),
                                 {"Full_Composition_Exclusion"}):
        excluded.update(range(first, last + 1))
    lines = []
    for code in range(0x110000):
        split = hangul_decomposition(code) or decomposition.get(code)
        shown = "-" if split is None else "%x,%x" % split
        lines.append("%x %s %d %d %s" % (code, categories[code], ccc.get(code, 0),
                                        pictographic[code], shown))
    composites = {}
    for code, (first, second) in decomposition.items():
        if second != 0:
            composites.setdefault((first, second), []).append(code)
    pairs = []
    for pair in sorted(composites):
        primary = [code for code in composites[pair] if code not in excluded]
        assert len(primary) <= 1, pair
        pairs.append((pair, primary[0] if primary else None))
    for leading in range(L_COUNT):
        for vowel in range(V_COUNT):
            syllable = S_BASE + (leading * V_COUNT + vowel) * T_COUNT
            pairs.append(((L_BASE + leading, V_BASE + vowel), syllable))
            for trailing in range(1, T_COUNT):
                pairs.append(((syllable, T_BASE + trailing), syllable + trailing))
            pairs.append(((syllable, T_BASE), None))
            pairs.append(((syllable + 1, T_BASE + 1), None))
    for pair in [(0x61, 0x62), (0x110000, 0x301), (0x41, 0x110000), (0xD800, 0x301),
                 (0x41, 0xD800), (0xFFFFFFFF, 0x301), (L_BASE - 1, V_BASE), (L_BASE, V_BASE - 1),
                 (S_BASE + S_COUNT, T_BASE + 1), (0x301, 0x41)]:
        pairs.append((pair, None))
    return lines, pairs


def main():
    ucd_dir, driver = sys.argv[1], sys.argv[2]
    want_lines, pairs = expected(ucd_dir)
    pairs_path = os.path.join(ucd_dir, "composition-pairs.txt")
    with open(pairs_path, "w", encoding="ascii") as file:
        for (first, second), _ in pairs:
            file.write("%x %x\n" % (first, second))
    for (first, second), result in pairs:
        want_lines.append("C %x %x %s" % (first, second, "-" if result is None else "%x" % result))
    run = subprocess.run([driver, os.path.relpath(pairs_path)], capture_output=True)
    got_lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = 0
    shown = 0
    for index, want in enumerate(want_lines):
        got = got_lines[index] if index < len(got_lines) else "(missing)"
        if got != want:
            failed += 1
            if shown < 20:
                print(f"line {index + 1}: expected {want!r}, actual {got!r}")
                shown += 1
    if len(got_lines) > len(want_lines):
        print(f"{len(got_lines) - len(want_lines)} extra lines, first {got_lines[len(want_lines)]!r}")
        failed += 1
    if run.returncode != 0:
        print(f"driver exited with {run.returncode}: "
              + run.stderr.decode("utf-8", "replace")[-500:])
    cases = len(want_lines)
    print(f"text_properties: {cases} cases, {cases - failed} passed, {failed} failed")
    return 0 if failed == 0 and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
