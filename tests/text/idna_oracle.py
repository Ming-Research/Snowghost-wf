"""The IDNA oracle: runs the Whitefoot driver over Unicode's IdnaTestV2.txt.

    python3 tests/text/idna_oracle.py IdnaTestV2.txt DRIVER

Reads every test line, writes each source string to a case file beside the
test file and runs DRIVER on it from the repository root. Per case the case
file holds one line: the source's code points as lowercase hexadecimal
numbers separated by single spaces (an empty line for the empty string).
The driver runs pkg::text::idna::domain_to_ascii on each and prints one
line: the result as a JSON string, or null when it is refused.

A case expects the toAsciiN column (Transitional_Processing false) when
its toAsciiN status, after removing the codes that the URL Standard's flags
ignore, is empty, and null otherwise. The ignored codes are those WPT's
url/tools/IdnaTestV2-parser.py removes: A4_1 and A4_2 (VerifyDnsLength
false), U1 (UseSTD3ASCIIRules false), V2 and V3 (CheckHyphens false).
Unlike that script, no case is excluded: the Bidi checks are required.
"""

import json
import os
import re
import subprocess
import sys

IGNORED = {"A4_1", "A4_2", "U1", "V2", "V3"}


def value(column, default):
    if column == "":
        return default
    if column == '""':
        return ""
    column = re.sub(r"\\x\{([0-9A-Fa-f]+)\}", lambda m: chr(int(m.group(1), 16)), column)
    return re.sub(r"\\u([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), column)


def statuses(column):
    return {code.strip() for code in column[1:-1].split(",") if code.strip()}


def load_cases(path):
    cases = []
    with open(path, encoding="utf-8") as file:
        for number, line in enumerate(file, 1):
            line = line.split("#", 1)[0].rstrip("\n")
            if not line.strip():
                continue
            columns = [column.strip() for column in line.split(";")]
            source = value(columns[0], "")
            to_unicode = value(columns[1], source)
            to_ascii = value(columns[3], to_unicode)
            status = columns[4] if columns[4] != "" else columns[2]
            errors = statuses(status) - IGNORED if status else set()
            cases.append((number, source, None if errors else to_ascii, sorted(errors)))
    return cases


def main():
    tests_path, driver = sys.argv[1], sys.argv[2]
    cases = load_cases(tests_path)
    cases_path = os.path.join(os.path.dirname(tests_path), "idna-cases.txt")
    with open(cases_path, "w", encoding="ascii") as file:
        for _, source, _, _ in cases:
            file.write(" ".join("%x" % ord(char) for char in source) + "\n")
    run = subprocess.run([driver, os.path.relpath(cases_path)], capture_output=True)
    lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = []
    for index, (number, source, want, errors) in enumerate(cases):
        line = lines[index] if index < len(lines) else None
        try:
            got = json.loads(line) if line is not None else "(no output)"
        except ValueError:
            got = line
        if got != want:
            failed.append((number, source, want, errors, got))
    for number, source, want, errors, got in failed[:10]:
        shown = source.encode("ascii", "backslashreplace").decode("ascii")
        print(f"line {number}: {shown}")
        print(f"  expected {json.dumps(want)}" + (f" ({', '.join(errors)})" if errors else ""))
        print(f"  actual   {json.dumps(got)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"idna: {len(cases)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
