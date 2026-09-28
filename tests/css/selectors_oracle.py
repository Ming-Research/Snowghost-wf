"""The CSS selectors oracle: runs the Whitefoot driver over WPT's Selectors
API data and css-parsing-tests' An+B suite.

    python3 tests/css/selectors_oracle.py WPT_NODES CSS_TESTS DRIVER

WPT_NODES holds WPT's dom/nodes/selectors.js and
ParentNode-querySelector-All-content.html; CSS_TESTS holds An+B.json. The
script reads the JavaScript literals of selectors.js, keeps the valid
selectors meant for querySelectorAll (testType has TEST_QSA) that run in
the document context of an HTML document (exclude names neither
"document" nor "html"), and all the invalid selectors. It writes the cases
to a case file in WPT_NODES and runs DRIVER, from the repository root, as
`DRIVER CONTENT CASES`, with CONTENT the content document. Per case the
case file holds a line "KIND LENGTH", the input's LENGTH bytes (UTF-8) and
a newline: KIND 0 is an <an+b> input, KIND 1 a selector. The driver prints
one line per case: for an <an+b>, [A, B] or null; for a selector, null
when it is invalid, otherwise a JSON array of the id attribute values of
the document's elements that match it, in tree order, as querySelectorAll
on the document returns them. The document is the content file parsed as
HTML, with the elements that WPT's setupSpecialElements adds under #root
that pkg::dom can represent, and with :target matching #target, as the
test loads it with the fragment #target.

EXCLUDED names the cases that need what pkg::dom does not represent: an
element in no namespace or in a namespace other than HTML, SVG and MathML,
and an attribute in such a namespace.
"""

import json
import os
import re
import subprocess
import sys

TEST_FLAGS = {"TEST_QSA": 0x01, "TEST_FIND": 0x04, "TEST_MATCH": 0x10}

EXCLUDED = {
    "Namespace selector, matching element with any namespace":
        "needs elements in no namespace and in http://www.example.org/ns",
    "Namespace selector, matching div elements in no namespace only":
        "needs an element in no namespace",
    "Namespace selector, matching any elements in no namespace only":
        "needs an element in no namespace",
    "Attribute presence selector, matching title attribute, case insensitivity":
        "needs an attribute in http://www.example.org/ns",
}


class Literal:
    """A reader for the JavaScript literals selectors.js uses: arrays, objects
    with bare keys, strings, numbers, the TEST_ flags joined by |, and
    comments."""

    def __init__(self, text):
        self.text, self.at = text, 0

    def skip(self):
        while self.at < len(self.text):
            if self.text[self.at].isspace():
                self.at += 1
            elif self.text.startswith("//", self.at):
                self.at = self.text.index("\n", self.at)
            elif self.text.startswith("/*", self.at):
                self.at = self.text.index("*/", self.at) + 2
            else:
                return

    def peek(self):
        self.skip()
        return self.text[self.at]

    def expect(self, char):
        if self.peek() != char:
            raise ValueError(f"expected {char!r} at {self.at}")
        self.at += 1

    def value(self):
        char = self.peek()
        if char == "[":
            self.at += 1
            items = []
            while self.peek() != "]":
                items.append(self.value())
                if self.peek() == ",":
                    self.at += 1
            self.at += 1
            return items
        if char == "{":
            self.at += 1
            fields = {}
            while self.peek() != "}":
                key = re.match(r"[A-Za-z_]\w*", self.text[self.at:]).group(0)
                self.at += len(key)
                self.expect(":")
                fields[key] = self.value()
                if self.peek() == ",":
                    self.at += 1
            self.at += 1
            return fields
        if char in "\"'":
            return self.string(char)
        word = re.match(r"-?\w+", self.text[self.at:]).group(0)
        self.at += len(word)
        result = TEST_FLAGS[word] if word in TEST_FLAGS else int(word)
        while self.peek() == "|":
            self.at += 1
            result |= self.value()
        return result

    def string(self, quote):
        self.at += 1
        out = []
        while self.text[self.at] != quote:
            char = self.text[self.at]
            if char == "\\":
                self.at += 1
                char = self.text[self.at]
                if char == "u":
                    out.append(chr(int(self.text[self.at + 1:self.at + 5], 16)))
                    self.at += 5
                    continue
                if char == "x":
                    out.append(chr(int(self.text[self.at + 1:self.at + 3], 16)))
                    self.at += 3
                    continue
                if char == "\n":
                    self.at += 1
                    continue
                char = {"n": "\n", "t": "\t", "r": "\r", "f": "\f", "v": "\v",
                        "b": "\b", "0": "\0"}.get(char, char)
            out.append(char)
            self.at += 1
        self.at += 1
        return "".join(out)


def read_array(source, name):
    reader = Literal(source)
    reader.at = source.index(f"var {name}") + len(f"var {name}")
    reader.expect("=")
    return reader.value()


def load_cases(wpt_nodes, css_tests):
    cases = []
    with open(os.path.join(css_tests, "An+B.json"), encoding="utf-8") as file:
        tests = json.load(file)
    for text, want in zip(tests[0::2], tests[1::2]):
        cases.append((f"An+B {text!r}", 0, text, want))
    with open(os.path.join(wpt_nodes, "selectors.js"), encoding="utf-8") as file:
        source = file.read()
    for test in read_array(source, "invalidSelectors"):
        cases.append((f"invalid {test['name']}: {test['selector']!r}", 1, test["selector"], None))
    excluded = 0
    for test in read_array(source, "validSelectors"):
        contexts = test.get("exclude", [])
        if not test["testType"] & TEST_FLAGS["TEST_QSA"] or "document" in contexts or "html" in contexts:
            continue
        if test["name"] in EXCLUDED:
            excluded += 1
            continue
        cases.append((f"valid {test['name']}: {test['selector']!r}", 1, test["selector"], test["expect"]))
    return cases, excluded


def main():
    wpt_nodes, css_tests, driver = sys.argv[1], sys.argv[2], sys.argv[3]
    cases, excluded = load_cases(wpt_nodes, css_tests)
    cases_path = os.path.join(wpt_nodes, "selector-cases.bin")
    with open(cases_path, "wb") as file:
        for _, kind, text, _ in cases:
            data = text.encode("utf-8")
            file.write(b"%d %d\n%s\n" % (kind, len(data), data))
    content = os.path.join(wpt_nodes, "ParentNode-querySelector-All-content.html")
    run = subprocess.run([driver, os.path.relpath(content), os.path.relpath(cases_path)],
                         capture_output=True)
    lines = run.stdout.decode("utf-8", "replace").splitlines()
    failed = []
    for index, (label, _, _, want) in enumerate(cases):
        line = lines[index] if index < len(lines) else None
        try:
            got = json.loads(line) if line is not None else "(no output)"
        except ValueError:
            got = line
        if got != want:
            failed.append((label, want, got))
    for label, want, got in failed[:10]:
        print(label)
        print(f"  expected {json.dumps(want, ensure_ascii=False)}")
        print(f"  actual   {json.dumps(got, ensure_ascii=False)}")
    if run.returncode != 0:
        print(f"driver exited with status {run.returncode}")
        print(run.stderr.decode("utf-8", "replace")[-2000:])
    passed = len(cases) - len(failed)
    print(f"css_selectors: {len(cases)} cases, {passed} passed, {len(failed)} failed, {excluded} excluded")
    return 0 if not failed and run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
