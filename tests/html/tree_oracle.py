"""The HTML tree construction oracle: runs the Whitefoot driver over the
html5lib tree-construction tests that WPT now hosts.

    python3 tests/html/tree_oracle.py TESTS_DIR DRIVER

Reads every `.dat` file in TESTS_DIR, writes the cases to a case file
beside them and runs DRIVER on it from the repository root. Per case the
case file holds a header line "SCRIPTING CONTEXT_LENGTH INPUT_LENGTH", the
fragment context's bytes (empty for a document; otherwise "td" or
"svg path", a namespace prefix and local name as the tests write them),
the input's bytes and a newline. SCRIPTING is 1 for a test marked
#script-on and 0 otherwise; a test marked neither runs once with scripting
off. The driver prints each case's tree in the tests' `#document` format,
one line per node or attribute, then a line holding only `#end`. Parse
errors are not compared.
"""

import os
import sys


def parse_file(path):
    with open(path, "rb") as file:
        lines = file.read().split(b"\n")
    tests, current, section = [], None, None
    for line in lines:
        if line == b"#data":
            if current is not None:
                tests.append(current)
            current = {"data": [], "document": [], "fragment": None, "scripting": 0}
            section = "data"
        elif current is None:
            continue
        elif line in (b"#errors", b"#new-errors"):
            section = "errors"
        elif line == b"#document":
            section = "document"
        elif line == b"#document-fragment":
            section = "fragment"
        elif line == b"#script-on":
            current["scripting"] = 1
        elif line == b"#script-off":
            current["scripting"] = 0
        elif section == "data":
            current["data"].append(line)
        elif section == "fragment":
            current["fragment"] = line.strip()
            section = None
        elif section == "document":
            current["document"].append(line)
    if current is not None:
        tests.append(current)
    cases = []
    for index, test in enumerate(tests):
        document = test["document"]
        while document and document[-1] == b"":
            document.pop()
        cases.append((f"{os.path.basename(path)} #{index}", test["scripting"],
                      test["fragment"] or b"", b"\n".join(test["data"]), document))
    return cases


def main():
    tests_dir, driver = sys.argv[1], sys.argv[2]
    cases = []
    for name in sorted(os.listdir(tests_dir)):
        if name.endswith(".dat"):
            cases.extend(parse_file(os.path.join(tests_dir, name)))
    cases_path = os.path.join(tests_dir, "cases.bin")
    with open(cases_path, "wb") as file:
        for _, scripting, context, data, _ in cases:
            file.write(b"%d %d %d\n%s%s\n" % (scripting, len(context), len(data), context, data))
    import subprocess
    run = subprocess.run([driver, os.path.relpath(cases_path)], capture_output=True)
    outputs, current = [], []
    for line in run.stdout.split(b"\n"):
        if line == b"#end":
            outputs.append(current)
            current = []
        else:
            current.append(line)
    failed = []
    for index, (label, _, context, data, want) in enumerate(cases):
        got = outputs[index] if index < len(outputs) else None
        if got != want:
            failed.append((label, context, data, want, got))
    for label, context, data, want, got in failed[:10]:
        print(f"{label}: {data[:120]!r}" + (f" (fragment {context.decode()})" if context else ""))
        print("  expected:")
        for line in want:
            print("    " + line.decode("utf-8", "replace"))
        print("  actual:")
        for line in (got or [b"(no output)"]):
            print("    " + line.decode("utf-8", "replace"))
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"html_tree: {len(cases)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
