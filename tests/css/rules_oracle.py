"""The CSS rules oracle: runs the Whitefoot driver over css-parsing-tests'
rule and declaration suites.

    python3 tests/css/rules_oracle.py TESTS_DIR DRIVER

For each suite in SUITES, writes its inputs as UTF-8 to a case file in
TESTS_DIR, runs DRIVER on it from the repository root and compares each
output line with the expected result. Per case the case file holds a line
with the suite's index in SUITES and the input's byte length, the bytes and
a newline. The driver tokenizes the input with pkg::css::syntax, parses
the whole component list with the suite's pkg::css::rules function, and
prints one line: the result as JSON in css-parsing-tests' representation,
numbers as in tests/css/oracle.py ("f64:" and 16 hexadecimal digits).
"""

import json
import os
import struct
import subprocess
import sys

SUITES = ["stylesheet", "rule_list", "declaration_list", "blocks_contents",
          "one_rule", "one_declaration"]


def decode_numbers(value):
    if isinstance(value, list):
        return [decode_numbers(item) for item in value]
    if isinstance(value, str) and value.startswith("f64:") and len(value) == 20:
        return struct.unpack(">d", bytes.fromhex(value[4:]))[0]
    return value


def matches(actual, expected):
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(matches(a, e) for a, e in zip(actual, expected)))
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return (isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and abs(actual - expected) <= abs(expected) * 1e-6)
    return actual == expected


def main():
    tests_dir, driver = sys.argv[1], sys.argv[2]
    cases = []
    for index, suite in enumerate(SUITES):
        with open(os.path.join(tests_dir, suite + ".json"), encoding="utf-8") as file:
            tests = json.load(file)
        for text, want in zip(tests[0::2], tests[1::2]):
            cases.append((suite, index, text, want))
    cases_path = os.path.join(tests_dir, "rules-cases.bin")
    with open(cases_path, "wb") as file:
        for _, index, text, _ in cases:
            data = text.encode("utf-8")
            file.write(b"%d %d\n%s\n" % (index, len(data), data))
    run = subprocess.run([driver, os.path.relpath(cases_path)], capture_output=True)
    lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = []
    for position, (suite, _, text, want) in enumerate(cases):
        line = lines[position] if position < len(lines) else None
        try:
            got = decode_numbers(json.loads(line)) if line is not None else None
        except ValueError:
            got = line
        if not matches(got, want):
            failed.append((suite, text, want, got))
    for suite, text, want, got in failed[:10]:
        print(f"{suite}: {text!r}")
        print(f"  expected {json.dumps(want, ensure_ascii=False)}")
        print(f"  actual   {json.dumps(got, ensure_ascii=False)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"css_rules: {len(cases)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
