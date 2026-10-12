#!/usr/bin/env python3
"""Reads the callgrind profiles of the scan-cost experiment (DESIGN.md in this
directory, "Where the scanning entry's extra time goes") and prints where two
builds' instruction counts differ.

    scan-cost.py compare BASE BASE_ZERO OTHER OTHER_ZERO --chain REGEX [--top N] [--result FILE]
        Each argument is a callgrind output written with --compress-strings=no
        and --compress-pos=no. A build's stage cost is its `A 1` run minus its
        `A 0` run, per function and in total. Prints the totals of every
        event and their ratio OTHER/BASE, then a per-function table (calls,
        exclusive and inclusive Ir of both builds, the exclusive difference
        and that difference per call) sorted by base's inclusive Ir and again
        by the absolute exclusive difference, and the share of the total
        difference the matcher chain's functions carry (REGEX, which
        scan-param.sh owns). With --result naming the
        driver's output line of the BASE run, the difference is also given
        per selector_matches call of shape A (elements times rules).

    scan-cost.py annotate PROFILE DISASSEMBLY
        DISASSEMBLY is `objdump -d` text of some functions of the profiled
        binary. Prints each instruction with the exclusive events callgrind
        recorded at its address (the profile needs --dump-instr=yes). The
        profile's addresses are the loaded ones; the offset to the file's is
        the least executed address of each function minus its symbol address,
        and must be the same for every function annotated.

callgrind_annotate prints per-function exclusive and inclusive costs of one
profile but no call counts and no difference between two profiles, which is
why this reads the files itself. ThinLTO's `.llvm.<digits>` suffix of a
promoted local function is dropped, so a function keeps its name across
builds, and callgrind's `'<depth>` suffix of a recursive call is dropped,
so every depth counts toward one function (its inclusive cost then counts
the recursion more than once).
"""

import re
import sys
from collections import defaultdict

SUFFIX = re.compile(r"\.llvm\.\d+$")
RECURSION = re.compile(r"'\d+$")


def normal(name):
    return SUFFIX.sub("", RECURSION.sub("", name.strip()))


class Profile:
    def __init__(self, path):
        self.events = []
        self.positions = 1
        self.exclusive = defaultdict(lambda: None)
        self.inclusive_calls = defaultdict(lambda: None)
        self.calls = defaultdict(int)
        self.by_address = defaultdict(lambda: None)
        self.totals = None
        self.read(path)

    def zero(self):
        return [0] * len(self.events)

    def add(self, table, key, values):
        row = table[key]
        if row is None:
            row = self.zero()
            table[key] = row
        for index, value in enumerate(values):
            row[index] += value

    def read(self, path):
        function = None
        callee = None
        pending_call = False
        with open(path, encoding="utf-8", errors="replace") as source:
            for line in source:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                if line.startswith("events:"):
                    self.events = line.split()[1:]
                    continue
                if line.startswith("positions:"):
                    self.positions = len(line.split()[1:])
                    continue
                if line.startswith("totals:") or line.startswith("summary:"):
                    values = [int(v) for v in line.split()[1:]]
                    values += [0] * (len(self.events) - len(values))
                    if line.startswith("totals:") or self.totals is None:
                        self.totals = values
                    continue
                if line.startswith("fn="):
                    function = normal(line[3:])
                    continue
                if line.startswith("cfn="):
                    callee = normal(line[4:])
                    continue
                if line.startswith("calls="):
                    count = int(line[6:].split()[0])
                    self.calls[callee] += count
                    pending_call = True
                    continue
                if "=" in line.split()[0] or ":" in line.split()[0]:
                    # ob=, fl=, fi=, fe=, cob=, cfi=, cfl=, jump=, jcnd= and headers.
                    continue
                fields = line.split()
                if fields[0] in ("+", "-", "*") or fields[0][0] in "+-*":
                    raise SystemExit(f"{path}: compressed position {fields[0]!r}; profile with --compress-pos=no")
                values = [int(v) for v in fields[self.positions:]]
                values += [0] * (len(self.events) - len(values))
                if pending_call:
                    self.add(self.inclusive_calls, function, values)
                    pending_call = False
                else:
                    self.add(self.exclusive, function, values)
                    if self.positions >= 2 or fields[0].startswith("0x"):
                        address = int(fields[0], 16) if fields[0].startswith("0x") else int(fields[0])
                        self.add(self.by_address, (function, address), values)
        if self.totals is None:
            total = self.zero()
            for row in self.exclusive.values():
                for index, value in enumerate(row):
                    total[index] += value
            self.totals = total

    def functions(self):
        return set(k for k, v in self.exclusive.items() if v is not None) | set(self.calls)

    def excl(self, name, event=0):
        row = self.exclusive.get(name)
        return row[event] if row else 0

    def incl(self, name, event=0):
        row = self.inclusive_calls.get(name)
        return self.excl(name, event) + (row[event] if row else 0)


def stage(full, empty):
    """Per-function stage costs: the A 1 profile minus the A 0 profile."""
    names = full.functions() | empty.functions()
    table = {}
    for name in names:
        table[name] = (
            full.calls.get(name, 0) - empty.calls.get(name, 0),
            full.excl(name) - empty.excl(name),
            full.incl(name) - empty.incl(name),
        )
    totals = [a - b for a, b in zip(full.totals, empty.totals)]
    return table, totals


def ratio(a, b):
    return f"{a / b:.4f}" if b else "-"


def compare(arguments):
    top = 40
    chain = None
    result = None
    rest = []
    index = 0
    while index < len(arguments):
        if arguments[index] == "--top":
            top = int(arguments[index + 1])
            index += 2
        elif arguments[index] == "--chain":
            chain = arguments[index + 1]
            index += 2
        elif arguments[index] == "--result":
            result = arguments[index + 1]
            index += 2
        else:
            rest.append(arguments[index])
            index += 1
    if len(rest) != 4 or chain is None:
        raise SystemExit("usage: scan-cost.py compare BASE BASE_ZERO OTHER OTHER_ZERO --chain REGEX [--top N] [--result FILE]")
    base_full, base_empty, other_full, other_empty = (Profile(p) for p in rest)
    if base_full.events != other_full.events:
        raise SystemExit("the two builds were profiled with different events")
    events = base_full.events
    base, base_totals = stage(base_full, base_empty)
    other, other_totals = stage(other_full, other_empty)

    print("== Stage totals (A 1 minus A 0), every event")
    print(f"{'event':<8} {'base':>16} {'other':>16} {'other-base':>16} {'other/base':>10}")
    for index, event in enumerate(events):
        b, o = base_totals[index], other_totals[index]
        print(f"{event:<8} {b:>16,} {o:>16,} {o - b:>16,} {ratio(o, b):>10}")
    print(f"whole runs, Ir: base A1 {base_full.totals[0]:,} A0 {base_empty.totals[0]:,}; other A1 {other_full.totals[0]:,} A0 {other_empty.totals[0]:,}")
    delta_total = other_totals[0] - base_totals[0]

    if result:
        with open(result, encoding="utf-8") as source:
            text = source.read()
        found = re.search(r"elements (\d+) rules (\d+) reps (\d+)", text)
        if found:
            elements, rules, reps = (int(g) for g in found.groups())
            pairs = elements * rules
            print(f"shape A: {elements} elements x {rules} rules = {pairs:,} selector_matches calls per repetition")
            print(f"Ir per call: base {base_totals[0] / pairs:.2f}, other {other_totals[0] / pairs:.2f}, difference {delta_total / pairs:.2f}")
        else:
            print(f"(no element and rule count in {result})")

    names = set(base) | set(other)

    def row(name):
        bc, be, bi = base.get(name, (0, 0, 0))
        oc, oe, oi = other.get(name, (0, 0, 0))
        per_call = f"{(oe - be) / bc:.2f}" if bc else "-"
        return f"{bc:>13,} {oc:>13,} {be:>15,} {oe:>15,} {oe - be:>14,} {per_call:>9} {bi:>15,} {oi:>15,}  {name}"

    header = f"{'calls base':>13} {'calls other':>13} {'excl Ir base':>15} {'excl Ir other':>15} {'excl diff':>14} {'diff/call':>9} {'incl Ir base':>15} {'incl Ir other':>15}  function"
    print()
    print(f"== Top {top} functions by base inclusive Ir (stage only; inclusive double-counts recursion)")
    print(header)
    for name in sorted(names, key=lambda n: -max(base.get(n, (0, 0, 0))[2], other.get(n, (0, 0, 0))[2]))[:top]:
        print(row(name))
    print()
    print(f"== Top {top} functions by |exclusive Ir difference| (other minus base; total difference {delta_total:,})")
    print(header)
    for name in sorted(names, key=lambda n: -abs(other.get(n, (0, 0, 0))[1] - base.get(n, (0, 0, 0))[1]))[:top]:
        print(row(name))
    print()
    pattern = re.compile(chain)
    members = sorted(n for n in names if pattern.search(n))
    chain_delta = sum(other.get(n, (0, 0, 0))[1] - base.get(n, (0, 0, 0))[1] for n in members)
    only_base = [n for n in members if n in base and base[n][1] and (n not in other or not other[n][1])]
    only_other = [n for n in members if n in other and other[n][1] and (n not in base or not base[n][1])]
    print("== The matcher chain")
    print(f"functions: {len(members)}; exclusive difference {chain_delta:,} = {ratio(chain_delta, delta_total)} of the stage's")
    print("executed only in base: " + (", ".join(only_base) or "none"))
    print("executed only in other: " + (", ".join(only_other) or "none"))
    for name in members:
        print(row(name))


DIS_HEAD = re.compile(r"^([0-9a-f]+) <(.+)>:$")
DIS_LINE = re.compile(r"^\s+([0-9a-f]+):\t(.*)$")


def annotate(arguments):
    if len(arguments) != 2:
        raise SystemExit("usage: scan-cost.py annotate PROFILE DISASSEMBLY")
    profile = Profile(arguments[0])
    blocks = []
    with open(arguments[1], encoding="utf-8", errors="replace") as source:
        for line in source:
            line = line.rstrip("\n")
            head = DIS_HEAD.match(line)
            if head:
                blocks.append((int(head.group(1), 16), head.group(2), []))
                continue
            instr = DIS_LINE.match(line)
            if instr and blocks:
                blocks[-1][2].append((int(instr.group(1), 16), instr.group(2)))
    addresses = defaultdict(list)
    for (function, address), values in profile.by_address.items():
        addresses[function].append(address)
    offsets = set()
    for start, symbol, _ in blocks:
        executed = addresses.get(normal(symbol))
        if executed:
            offsets.add(min(executed) - start)
    if len(offsets) != 1:
        print(f"!! the functions give {len(offsets)} load offsets {sorted(hex(o) for o in offsets)}; using the most common one")
    offset = max(offsets, key=lambda o: sum(1 for s, n, _ in blocks if addresses.get(normal(n)) and min(addresses[normal(n)]) - s == o)) if offsets else 0
    print(f"load offset {offset:#x}; events {' '.join(profile.events)}")
    for start, symbol, lines in blocks:
        name = normal(symbol)
        total = profile.excl(name)
        print()
        print(f"== {symbol}: exclusive Ir {total:,}, calls {profile.calls.get(name, 0):,}")
        for address, text in lines:
            values = profile.by_address.get((name, address + offset))
            if values:
                shown = " ".join(f"{v:>12,}" for v in values[:1]) + (" " + " ".join(f"{e}={v:,}" for e, v in zip(profile.events[1:], values[1:]) if v) if len(values) > 1 else "")
            else:
                shown = f"{'.':>12}"
            print(f"{shown}  {address:x}: {text}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    command, arguments = sys.argv[1], sys.argv[2:]
    if command == "compare":
        compare(arguments)
    elif command == "annotate":
        annotate(arguments)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
