"""The URL oracle: runs the Whitefoot driver over WPT's URL parsing data.

    python3 tests/url/oracle.py RESOURCES DRIVER

Reads urltestdata.json, IdnaTestV2.json and toascii.json from RESOURCES
(WPT's url/resources), writes the cases to a case file there and runs
DRIVER on it from the repository root. Per case the case file holds a
header line "HAS_BASE INPUT_LENGTH BASE_LENGTH", the input's bytes, the
base's bytes (none when HAS_BASE is 0) and a newline; strings are WTF-8.
The driver parses the base with pkg::url::parse_url, then the input with
parse_url_with_base (or parse_url without a base), and prints one line:
null when the input is refused, otherwise a JSON object with the URL API's
href, protocol, username, password, host, hostname, port, pathname, search
and hash, computed from the record as the URL Standard's getters define.

The host suites run as WPT's IdnaTestV2 and toascii tests do: the input is
"https://" + host + "/x" with no base, and a non-null output o expects href
"https://" + o + "/x", host and hostname o and pathname "/x". Origin and
searchParams are not compared: pkg::url does not compute them at this
revision.
"""

import json
import os
import subprocess
import sys

FIELDS = ["href", "protocol", "username", "password", "host", "hostname",
          "port", "pathname", "search", "hash"]


def load_cases(resources):
    cases = []
    with open(os.path.join(resources, "urltestdata.json"), encoding="utf-8") as file:
        for test in json.load(file):
            if isinstance(test, str):
                continue
            want = None if test.get("failure") else {field: test[field] for field in FIELDS}
            cases.append((f"urltestdata: {test['input']!r} base {test['base']!r}",
                          test["input"], test["base"], want))
    for name in ["IdnaTestV2.json", "toascii.json"]:
        with open(os.path.join(resources, name), encoding="utf-8") as file:
            tests = json.load(file)
        for test in tests:
            if isinstance(test, str):
                continue
            output = test["output"]
            want = None
            if output is not None:
                want = {"href": "https://" + output + "/x", "protocol": "https:",
                        "username": "", "password": "", "host": output,
                        "hostname": output, "port": "", "pathname": "/x",
                        "search": "", "hash": ""}
            cases.append((f"{name}: {test['input']!r}", "https://" + test["input"] + "/x",
                          None, want))
    return cases


def wtf8(text):
    return text.encode("utf-8", "surrogatepass")


def main():
    resources, driver = sys.argv[1], sys.argv[2]
    cases = load_cases(resources)
    cases_path = os.path.join(resources, "url-cases.bin")
    with open(cases_path, "wb") as file:
        for _, text, base, _ in cases:
            data = wtf8(text)
            base_data = wtf8(base) if base is not None else b""
            file.write(b"%d %d %d\n%s%s\n" % (0 if base is None else 1, len(data),
                                                len(base_data), data, base_data))
    run = subprocess.run([driver, os.path.relpath(cases_path)], capture_output=True)
    lines = run.stdout.split(b"\n")
    failed = []
    for index, (label, _, _, want) in enumerate(cases):
        line = lines[index] if index < len(lines) else None
        try:
            got = json.loads(line.decode("utf-8", "surrogatepass"))
        except (AttributeError, ValueError):
            got = line
        if got != want:
            failed.append((label, want, got))
    for label, want, got in failed[:10]:
        print(label)
        print(f"  expected {json.dumps(want, ensure_ascii=False)}")
        print(f"  actual   {got if isinstance(got, bytes) else json.dumps(got, ensure_ascii=False)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"url: {len(cases)} cases, {passed} passed, {len(failed)} failed")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
