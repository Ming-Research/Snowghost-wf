"""The HTML tokenizer oracle: runs the Whitefoot driver over html5lib-tests.

    python3 tests/html/oracle.py TESTS_DIR DRIVER

Reads every tokenizer test file in TESTS_DIR (as tests/oracle-data.sh
fetches them), expands each test into one case per initial state, writes
the cases to a case file beside them and runs DRIVER on it from the
repository root. Per case the case file holds a header line
"STATE LAST_START_TAG_LENGTH INPUT_LENGTH", the last start tag's bytes, the
input's bytes and a newline; STATE is the index of the initial state in
STATES and the input is WTF-8. The driver prints one line per case: the
token list as JSON in html5lib's representation, strings as WTF-8.
Parse errors are not compared.
"""

import json
import os
import re
import subprocess
import sys

STATES = ["Data state", "RCDATA state", "RAWTEXT state", "Script data state",
          "PLAINTEXT state", "CDATA section state"]


def unescape(text):
    return re.sub(r"\\u([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), text)


def unescape_all(value):
    if isinstance(value, str):
        return unescape(value)
    if isinstance(value, list):
        return [unescape_all(item) for item in value]
    if isinstance(value, dict):
        return {unescape(k): unescape_all(v) for k, v in value.items()}
    return value


def wtf8(text):
    return text.encode("utf-8", "surrogatepass")


def merged(tokens):
    out = []
    for token in tokens:
        if (out and isinstance(token, list) and token and token[0] == "Character"
                and out[-1][0] == "Character"):
            out[-1] = ["Character", out[-1][1] + token[1]]
        else:
            out.append(list(token) if isinstance(token, list) else token)
    return out


def load_cases(tests_dir):
    cases = []
    for name in sorted(os.listdir(tests_dir)):
        if not name.endswith(".test"):
            continue
        with open(os.path.join(tests_dir, name), encoding="utf-8") as file:
            tests = json.load(file).get("tests", [])
        for test in tests:
            text, output = test["input"], test["output"]
            if test.get("doubleEscaped"):
                text, output = unescape(text), unescape_all(output)
            for state in test.get("initialStates", ["Data state"]):
                cases.append((f"{name}: {test['description']} ({state})",
                              STATES.index(state), test.get("lastStartTag", ""),
                              text, merged(output)))
    return cases


def main():
    tests_dir, driver = sys.argv[1], sys.argv[2]
    cases = load_cases(tests_dir)
    cases_path = os.path.join(tests_dir, "cases.bin")
    with open(cases_path, "wb") as file:
        for _, state, last, text, _ in cases:
            last_bytes, data = wtf8(last), wtf8(text)
            file.write(b"%d %d %d\n%s%s\n" % (state, len(last_bytes), len(data),
                                                last_bytes, data))
    run = subprocess.run([driver, os.path.relpath(cases_path)], capture_output=True)
    lines = run.stdout.split(b"\n")
    failed = []
    for index, (label, _, _, text, want) in enumerate(cases):
        line = lines[index] if index < len(lines) else None
        try:
            got = json.loads(line.decode("utf-8", "surrogatepass"))
            if isinstance(got, list):
                got = merged(got)
        except (AttributeError, ValueError):
            got = line
        if got != want:
            failed.append((label, text, want, got))
    for label, text, want, got in failed[:10]:
        print(f"{label}: {text!r}")
        print(f"  expected {json.dumps(want, ensure_ascii=False)}")
        print(f"  actual   {got if isinstance(got, bytes) else json.dumps(got, ensure_ascii=False)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"html_tokenizer: {len(cases)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
