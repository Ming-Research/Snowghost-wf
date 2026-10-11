"""CI fixtures for sg-bl-02-02's bounded structural + reaches.

Run from the repository root:
  python3 plus-reach.py LAYOUT STYLE OUTDIR [--pilot|--before|--mutant]

Each edit starts with a fresh page. Node identifiers come from LAYOUT's
nodes mode, never from assumed parser allocation. Removal cases detach
original elements, independently of insertion cases. Text and comments
separate every sibling; insertion points alternate between an element and
the preceding Text node. Reach counts below follow selector dependencies,
not outputs captured from either renderer. Structure mode independently
compares retained computed styles and membership with a full recomputation.

The runner is wired to the temporary oracles-m2 plus-reach job, and leaves
all generated pages, scripts and raw results in OUTDIR for its artifact.
"""

import argparse
import json
import re
import subprocess
import time
from pathlib import Path


UA = "renderer/style/ua.css"
TAIL = 64
REACH = re.compile(r"^reach 1 set (\d+) changed (\d+) missing (\d+)(?: first \d+)?$")
STRUCTURE = re.compile(r"^structure 1 visited (\d+) changed (\d+) differ (\d+)(?: first \d+)?$")
SUMMARY = re.compile(r"^structure edits 1 differ (\d+) fallbacks 0$")


def cases():
    # n is the number of + links in the matching original chain. The final
    # structural compound has suffix 0, the preceding one suffix 1, etc.
    groups = [
        ("one", 1, "h1 + p", "p", False, False),
        ("two", 2, "h1 + p + h2", "h2", False, False),
        ("three", 3, "h1 + p + p + h2", "h2", False, False),
        ("first", 2, "h1:first-child + p + h2", "h2", False, True),
        ("nested", 2, "h2:is(h1 + p + h2)", "h2", False, False),
        ("anything", 2, "h1 + p + *", "h2", False, False),
        ("general", 1, "h1 ~ p", "p", True, False),
        ("plus-general", 2, "h1 + p ~ h2", "h2", True, False),
        ("general-plus", 2, "h1 ~ p + h2", "h2", True, False),
    ]
    for name, n, selector, subject, wide, position in groups:
        for operation in ("insert", "remove"):
            for distance in range(4):
                # distance counts *remaining element* siblings between the
                # insertion/removal and the surviving target.
                padding = max(0, distance - n + (operation == "remove"))
                tags = ["span"] * padding + ["h1"] + ["p"] * (n - 1)
                target = len(tags)
                tags += [subject] * (TAIL + 1)
                edit = target - distance - (operation == "remove")
                changed = int(distance < n)
                if position:
                    # A :first-child change at h1 can reach one more hop.
                    changed = int(distance <= n)
                if name == "general":
                    changed = TAIL + 1 if operation == "remove" and distance == 0 else 0
                elif name == "plus-general":
                    changed = TAIL + 1 if operation == "remove" and distance < n else 0
                elif name == "general-plus":
                    changed = int(operation == "remove" and distance < n)
                elif name == "anything" and operation == "insert" and distance == 1:
                    # h1,p becomes h1,new-p,old-p: old-p now matches the
                    # universal subject, while the original h2 stops matching.
                    changed = 2
                if wide:
                    wanted = TAIL + 1
                elif name == "anything":
                    wanted = n
                else:
                    wanted = max(0, n + int(position) - distance)
                # Before the repair, any nonzero suffix widened side_next
                # to every following sibling. Single + already was bounded.
                old_wide = wide or n > 1
                old_wanted = wanted
                if old_wide:
                    old_wanted = TAIL + 1
                    if name == "anything":
                        old_wanted += distance
                yield dict(name=f"{name}-{operation}-d{distance}", tags=tags,
                           edit=edit, operation=operation, distance=distance,
                           css=f"{selector} {{ color: #123456; }}",
                           wanted=wanted, old_wanted=old_wanted, changed=changed)
    # The bounded key must expire even when another key keeps the shared
    # sibling walk going. A single union-wide flag would wrongly include all
    # 33 h2 elements rather than the one at the final + hop.
    for operation in ("insert", "remove"):
        yield dict(name=f"coexist-{operation}",
                   tags=["h1", "p", "h2"] + [tag for _ in range(32) for tag in ("h2", "em")],
                   edit=1 if operation == "insert" else 0, operation=operation,
                   distance=1, css="h1 + p + h2 { color: #123456; } h1 ~ em { color: #654321; }",
                   wanted=33, old_wanted=65, changed=1 if operation == "insert" else 33)
    # Two finite keys with different suffix lengths: h2 at distance 2 must
    # expire at its own bound 1 while em keeps the walk alive to distance 2.
    yield dict(name="different-bounds", tags=["h1", "p", "p", "h2", "em"] + ["h2", "em"] * 32,
               edit=0, operation="remove", distance=2,
               css="h1 + p + h2 { color: #123456; } h1 + p + p + em { color: #654321; }",
               wanted=0, old_wanted=66, changed=0)


def run(command, prefix):
    stdout = Path(str(prefix) + ".raw")
    stderr = Path(str(prefix) + ".err")
    with stdout.open("w") as out, stderr.open("w") as err:
        result = subprocess.run(command, stdout=out, stderr=err, check=False)
    return result.returncode, stdout.read_text()


def node_ids(raw, expected):
    stack = []
    section = None
    children = []
    preceding_text = None
    for line in raw.splitlines():
        if line.startswith("E "):
            _, node, depth, tag, _, _ = line.split()
            node, depth = int(node), int(depth)
            while stack and stack[-1][0] >= depth:
                stack.pop()
            parent = stack[-1][1] if stack else None
            stack.append((depth, node))
            if tag == "section":
                if section is not None:
                    raise ValueError("fixture has more than one section")
                section = node
            elif parent == section:
                children.append((tag, node, preceding_text))
                preceding_text = None
        elif line.startswith("T "):
            _, node, parent, _, _ = line.split(" ", 4)
            if int(parent) == section:
                preceding_text = int(node)
    if section is None or [tag for tag, _, _ in children] != expected:
        raise ValueError("nodes listing does not match the independently generated sibling list")
    return section, children


def fixture(layout, style, outdir, case, before=False, mutant=False):
    name = case["name"]
    page = outdir / f"{name}.html"
    script = outdir / f"{name}.edits"
    siblings = [f"<{tag}>child{i}</{tag}>" for i, tag in enumerate(case["tags"])]
    page.write_text("<!doctype html><html><head></head><body><section>\n<!-- gap -->\n" +
                    "\n<!-- gap -->\n".join(siblings) + "\n<!-- gap -->\n</section></body></html>\n")
    status, raw = run([layout, "nodes", "0", str(page), UA], outdir / f"{name}.nodes")
    if status:
        raise ValueError(f"{name}: nodes exited {status}")
    parent, children = node_ids(raw, case["tags"])
    _, element, text = children[case["edit"]]
    if case["operation"] == "insert":
        # Insertion before text exposes the same element-neighbour relation
        # as insertion before the element, with a different raw node anchor.
        before_node = text if case["distance"] % 2 else element
        if before_node is None:
            raise ValueError(f"{name}: no separator text before insertion")
        operation = f"B {parent} {before_node} inserted"
    else:
        operation = f"X {element}"
    script.write_text(f"S {case['css']}\n{operation}\n")
    reach_status, reach_raw = run([style, "reach", str(script), str(page), UA], outdir / f"{name}.reach")
    structure_status, structure_raw = run([style, "structure", str(script), str(page), UA], outdir / f"{name}.structure")
    reach_lines = reach_raw.splitlines()
    reach = REACH.fullmatch(reach_lines[0]) if len(reach_lines) == 1 else None
    structure_lines = structure_raw.splitlines()
    structure = STRUCTURE.fullmatch(structure_lines[0]) if len(structure_lines) == 2 else None
    summary = SUMMARY.fullmatch(structure_lines[1]) if len(structure_lines) == 2 else None
    if not (reach and structure and summary):
        raise ValueError(f"{name}: incomplete, rebuilt or unexpected oracle protocol; see raw files")
    reached, changed, missing = map(int, reach.groups())
    differ = int(structure.group(3))
    expected = case["old_wanted"] if before else case["wanted"]
    if mutant:
        if not (reach_status == 1 and structure_status == 1 and missing > 0 and differ > 0):
            raise ValueError(f"{name}: mutation must produce missing elements and computed-style differences")
    elif reach_status or structure_status or missing or differ or reached != expected:
        raise ValueError(f"{name}: reach set {reached} expected {expected}, missing {missing}, differ {differ}, "
                         f"exit statuses {reach_status}/{structure_status}")
    if changed != case["changed"] or int(summary.group(1)) != differ:
        raise ValueError(f"{name}: changed {changed} expected {case['changed']}, or inconsistent difference summary")
    result = dict(name=name, expected_set=expected, set=reached, changed=changed, missing=missing, differ=differ,
                  reach_status=reach_status, structure_status=structure_status)
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout")
    parser.add_argument("style")
    parser.add_argument("outdir", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pilot", action="store_true")
    mode.add_argument("--before", action="store_true")
    mode.add_argument("--mutant", action="store_true")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    selected = list(cases())
    if args.pilot or args.mutant:
        selected = [case for case in selected if case["name"] == "two-remove-d1"]
    started = time.monotonic()
    results = []
    try:
        for case in selected:
            results.append(fixture(args.layout, args.style, args.outdir, case, args.before, args.mutant))
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    report = dict(cases=len(results), elapsed_seconds=time.monotonic() - started, before=args.before,
                  mutant=args.mutant, results=results)
    (args.outdir / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{len(results)} focused cases passed; sample/batch wall time {report['elapsed_seconds']:.3f}s")


if __name__ == "__main__":
    main()
