"""The CSS color oracle: runs the Whitefoot driver over css-parsing-tests'
color suites.

    python3 tests/css/color_oracle.py TESTS_DIR DRIVER

Reads every suite in SUITES from TESTS_DIR, writes the inputs as UTF-8 to a
case file there, runs DRIVER on it from the repository root and compares
each output line with the expected serialization. Per case the case file
holds a line with the input's byte length, the bytes and a newline. The
driver tokenizes the input with pkg::css::syntax, parses the whole
component list with pkg::css::color::parse_color, and prints one line:
null for an error, "currentcolor", or [SPACE, FIRST, SECOND, THIRD, ALPHA]
with SPACE a name in SPACES and each channel a number as in
tests/css/oracle.py ("f64:" and 16 hexadecimal digits), or null when it is
missing. The suites serialize with at most six significant digits, so
channels compare within that precision rather than exactly.

CSS Color Module Level 5 (color_functions_5.json) is not in SUITES:
pkg::css::color does not implement it at this revision.
"""

import json
import os
import re
import struct
import subprocess
import sys

SUITES = ["color_keywords_3", "color_keywords_4", "color_hexadecimal_3",
          "color_hexadecimal_4", "color_hsl_3", "color_hsl_4", "color_hwb_4",
          "color_lab_4", "color_lch_4", "color_oklab_4", "color_oklch_4",
          "color_function_4"]

SPACES = ["rgb", "lab", "lch", "oklab", "oklch", "srgb", "srgb-linear",
          "display-p3", "a98-rgb", "prophoto-rgb", "rec2020", "xyz-d50",
          "xyz-d65"]


def channel(text):
    return None if text == "none" else float(text)


def expected_value(text):
    """The suite's serialization as [SPACE, FIRST, SECOND, THIRD, ALPHA]."""
    if text is None or text == "currentcolor":
        return text
    legacy = re.fullmatch(r"(rgba?)\((.*)\)", text)
    if legacy:
        values = [channel(part.strip()) for part in legacy.group(2).split(",")]
        return ["rgb"] + values + ([1.0] if len(values) == 3 else [])
    modern = re.fullmatch(r"([a-z]+)\((.*)\)", text)
    parts = modern.group(2).split(" / ")
    words = parts[0].split()
    space = words.pop(0) if modern.group(1) == "color" else modern.group(1)
    alpha = channel(parts[1]) if len(parts) == 2 else 1.0
    return [space] + [channel(word) for word in words] + [alpha]


def decode(value):
    if isinstance(value, str) and value.startswith("f64:") and len(value) == 20:
        return struct.unpack(">d", bytes.fromhex(value[4:]))[0]
    return value


def matches(actual, expected):
    if not isinstance(expected, list):
        return actual == expected
    if not isinstance(actual, list) or len(actual) != len(expected) or actual[0] != expected[0]:
        return False
    for got, want in zip(map(decode, actual[1:]), expected[1:]):
        if want is None or got is None or isinstance(got, str):
            if got != want:
                return False
        elif abs(got - want) > 1e-5 * max(abs(want), 1.0):
            return False
    return True


def main():
    tests_dir, driver = sys.argv[1], sys.argv[2]
    cases = []
    for suite in SUITES:
        with open(os.path.join(tests_dir, suite + ".json"), encoding="utf-8") as file:
            tests = json.load(file)
        for text, want in zip(tests[0::2], tests[1::2]):
            cases.append((suite, text, want))
    cases_path = os.path.join(tests_dir, "color-cases.bin")
    with open(cases_path, "wb") as file:
        for _, text, _ in cases:
            data = text.encode("utf-8")
            file.write(b"%d\n%s\n" % (len(data), data))
    run = subprocess.run([driver, os.path.relpath(cases_path)], capture_output=True)
    lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = []
    for position, (suite, text, want) in enumerate(cases):
        line = lines[position] if position < len(lines) else None
        try:
            got = json.loads(line) if line is not None else None
        except ValueError:
            got = line
        if line is None or not matches(got, expected_value(want)):
            failed.append((suite, text, want, got))
    for suite, text, want, got in failed[:10]:
        print(f"{suite}: {text!r}")
        print(f"  expected {json.dumps(want, ensure_ascii=False)}")
        shown = [decode(item) for item in got] if isinstance(got, list) else got
        print(f"  actual   {json.dumps(shown, ensure_ascii=False)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"css_color: {len(cases)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
