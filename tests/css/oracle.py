"""The CSS syntax oracle: runs the Whitefoot driver over css-parsing-tests.

    python3 tests/css/oracle.py TESTS.json DRIVER

Writes each test input as UTF-8 to a case file beside TESTS.json, runs
DRIVER on it from the repository root, and compares each output line with
the expected result. The case file holds, per case, the byte length in
decimal, a newline, the bytes and a newline. The driver prints one line per
case: the components as JSON in css-parsing-tests' representation, except
that a number's value is the string "f64:" followed by the 16 hexadecimal
digits of its IEEE 754 bits. Values match within the relative tolerance
rust-cssparser's test harness uses.
"""

import json
import os
import struct
import subprocess
import sys


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
    tests_path, driver = sys.argv[1], sys.argv[2]
    with open(tests_path, encoding="utf-8") as tests_file:
        tests = json.load(tests_file)
    inputs, expected = tests[0::2], tests[1::2]
    cases_path = os.path.join(os.path.dirname(tests_path), "cases.bin")
    with open(cases_path, "wb") as cases:
        for text in inputs:
            data = text.encode("utf-8")
            cases.write(b"%d\n%s\n" % (len(data), data))
    run = subprocess.run([driver, os.path.relpath(cases_path)],
                         capture_output=True)
    lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = []
    for index, (text, want) in enumerate(zip(inputs, expected)):
        line = lines[index] if index < len(lines) else None
        try:
            got = decode_numbers(json.loads(line)) if line is not None else None
        except ValueError:
            got = line
        if not matches(got, want):
            failed.append((index, text, want, got))
    for index, text, want, got in failed[:10]:
        print(f"case {index}: {text!r}")
        print(f"  expected {json.dumps(want, ensure_ascii=False)}")
        print(f"  actual   {json.dumps(got, ensure_ascii=False)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(inputs) - len(failed)
    print(f"css_syntax: {len(inputs)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
