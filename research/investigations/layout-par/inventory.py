#!/usr/bin/env python3
"""Join source loops, the pinned compiler ledger, and layout-only Ir profiles.

This investigation caller is wired by par-inventory.yml. It deliberately reads
raw artifacts without rewriting them. --dry-run uses only handmade fixtures.
"""

import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
import tempfile


PAGES = ("ecma262", "html5", "apollo11")
LOOP_ROW = re.compile(r"^PAR loop\s+(.+):(\d+)\s+loop\s+(permitted|denied)\s+(.+)$")
RAW_ROW = re.compile(r"layout elements (\d+) contexts (\d+) paragraphs (\d+) reps (\d+)\s*")


class Invalid(ValueError):
    """An artifact is missing, malformed, or insufficient to support a report."""


def parse_callgrind(path):
    """Return (Ir total, exclusive {symbol: Ir}, {(caller, callee): Ir}).

    Symbol compression has a shared fn/cfn namespace, distinct from file and
    object namespaces. A calls= directive marks its next *cost* row as an edge;
    its numeric call count is never interpreted. Every exclusive event is
    reconciled against the required totals footer (summary is not that footer).
    """
    path = Path(path)
    own, edges = defaultdict(int), defaultdict(int)
    names = {"fn": {}, "fl": {}, "ob": {}}
    function = callee = None
    positions, events = ["line"], None
    explicit_positions = False
    previous = [None]
    edge_pending = False
    totals = None
    exclusive = None
    ir = None
    cost_seen = False

    def fail(number, message):
        raise Invalid(f"{path}:{number}: {message}")

    def symbol(value, namespace, number):
        match = re.fullmatch(r"\((\d+)\)(?: (.+))?", value)
        if not match:
            if not value:
                fail(number, "empty symbol")
            return value
        key, definition = match.groups()
        table = names[namespace]
        if definition is not None:
            if key in table and table[key] != definition:
                fail(number, "compressed symbol redefined")
            table[key] = definition
        if key not in table:
            fail(number, f"unknown compressed {namespace} symbol ({key})")
        return table[key]

    def position(value, prior, number):
        if value == "*":
            if prior is None:
                fail(number, "position * without predecessor")
            return prior
        if re.fullmatch(r"[+-](?:\d+|0x[0-9a-fA-F]+)", value):
            if prior is None:
                fail(number, "relative position without predecessor")
            magnitude = value[1:]
            offset = int(magnitude, 16 if magnitude.startswith("0x") else 10)
            return prior + (offset if value[0] == "+" else -offset)
        if re.fullmatch(r"(?:\d+|0x[0-9a-fA-F]+)", value):
            return int(value, 16 if value.startswith("0x") else 10)
        fail(number, f"invalid position {value!r}")

    for number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("event:"):
            # Descriptive or derived event headers may contain '='; they do
            # not change the concrete events order used by cost rows.
            continue
        header = re.match(r"^([A-Za-z]+):", line)
        if header and header[1] not in {"events", "positions", "totals"}:
            key = header[1]
            if key not in {"version", "creator", "pid", "cmd", "part", "desc", "summary", "thread"}:
                fail(number, f"unsupported header {key}")
            if key in {"part", "thread"} and cost_seen:
                fail(number, "multiple profile parts/threads require separate artifacts")
            continue
        if line.startswith("positions:"):
            if explicit_positions or cost_seen:
                fail(number, "duplicate or late positions declaration")
            positions = line.partition(":")[2].split()
            if not positions or len(set(positions)) != len(positions):
                fail(number, "invalid positions declaration")
            previous = [None] * len(positions)
            explicit_positions = True
            continue
        if line.startswith("events:"):
            if events is not None or cost_seen:
                fail(number, "duplicate or late events declaration")
            events = line.partition(":")[2].split()
            if events.count("Ir") != 1 or len(set(events)) != len(events):
                fail(number, "events must contain exactly one Ir")
            ir = events.index("Ir")
            exclusive = [0] * len(events)
            continue
        if line.startswith("totals:"):
            values = line.partition(":")[2].split()
            if events is None or len(values) != len(events) or not all(v.isdecimal() for v in values):
                fail(number, "totals width must equal events width with integer costs")
            if totals is not None or edge_pending:
                fail(number, "duplicate totals or unfinished edge")
            totals = list(map(int, values))
            continue
        if re.match(r"^[*+\-0-9]", line):
            if totals is not None:
                fail(number, "cost after totals footer")
            if function is None or positions is None or events is None:
                fail(number, "cost before function/positions/events")
            fields = line.split()
            if not len(positions) <= len(fields) <= len(positions) + len(events):
                fail(number, "cost row exceeds positions + events width or lacks positions")
            offsets, values = fields[:len(positions)], fields[len(positions):]
            previous = [position(v, p, number) for v, p in zip(offsets, previous)]
            if not all(value.isdecimal() for value in values):
                fail(number, "costs must be nonnegative integers")
            # The format explicitly gives omitted trailing events zero cost.
            counts = list(map(int, values)) + [0] * (len(events) - len(values))
            if edge_pending:
                edges[(function, callee)] += counts[ir]
                edge_pending = False
            else:
                own[function] += counts[ir]
                exclusive = [left + right for left, right in zip(exclusive, counts)]
            cost_seen = True
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            if key == "calls":
                if function is None or callee is None or edge_pending or positions is None:
                    fail(number, "calls requires caller, callee and one following edge row")
                # Validate structure only; do not read or report the calls count.
                fields = value.split()
                if len(fields) != 1 + len(positions) or not fields[0].isdecimal():
                    fail(number, "malformed calls directive")
                for field in fields[1:]:
                    if not re.fullmatch(r"(?:\*|[+-]?(?:\d+|0x[0-9a-fA-F]+))", field):
                        fail(number, "invalid calls target position")
                edge_pending = True
            elif key in ("fn", "cfn", "fl", "fi", "fe", "cfl", "cfi", "ob", "cob"):
                if edge_pending:
                    fail(number, "edge row missing before next symbol")
                namespace = "fn" if key in ("fn", "cfn") else "ob" if key in ("ob", "cob") else "fl"
                resolved = symbol(value, namespace, number)
                if key == "fn":
                    function, callee = resolved, None
                elif key == "cfn":
                    callee = resolved
            else:
                fail(number, f"unsupported association directive {key}")
            continue
        fail(number, "unrecognized Callgrind record")
    if totals is None or exclusive is None or edge_pending:
        raise Invalid(f"{path}: missing totals/events or unfinished edge")
    if exclusive != totals:
        raise Invalid(f"{path}: exclusive costs {exclusive} do not equal totals {totals}")
    return totals[ir], dict(own), dict(edges)


def source_tokens(text):
    """Lex only identifiers and punctuation, ignoring strings and comments."""
    pattern = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z_0-9]*|\S', re.S)
    tokens = []
    consumed = 0
    line = 1
    for match in pattern.finditer(text):
        line += text[consumed:match.start()].count("\n")
        token = match.group()
        if not token.startswith(('"', '//', '/*')):
            tokens.append((token, line, match.start(), match.end()))
        line += token.count("\n")
        consumed = match.end()
    return tokens


def scan_source(text, path, module):
    tokens = source_tokens(text)
    stack, braces = [], {}
    for index, token in enumerate(tokens):
        if token[0] == "{":
            stack.append(index)
        elif token[0] == "}":
            if not stack:
                raise Invalid(f"{path}:{token[1]}: unmatched closing brace")
            braces[stack.pop()] = index
    if stack:
        raise Invalid(f"{path}: unclosed brace")
    functions, loops = [], []
    index = 0
    while index < len(tokens):
        token, line, _, _ = tokens[index]
        if token == "fn":
            if index + 1 >= len(tokens) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", tokens[index + 1][0]):
                raise Invalid(f"{path}:{line}: unknown function declaration")
            name = f"{module}.{tokens[index + 1][0]}"
            opening = index + 2
            while opening < len(tokens) and tokens[opening][0] not in ("{", ";"):
                opening += 1
            if opening >= len(tokens) or tokens[opening][0] != "{":
                raise Invalid(f"{path}:{line}: function has no body")
            if tokens[opening - 1][0] == "contract":
                opening = braces[opening] + 1
                if opening >= len(tokens) or tokens[opening][0] != "{":
                    raise Invalid(f"{path}:{line}: contract has no following function body")
            closing = braces[opening]
            functions.append({"file": path, "line": line, "function": name})
            for cursor in range(opening + 1, closing):
                kind, at, start, end = tokens[cursor]
                if kind not in ("for", "loop"):
                    continue
                label = ""
                if cursor + 2 < closing and tokens[cursor + 1][0] == "@":
                    label = tokens[cursor + 2][0]
                loops.append({"file": path, "line": at, "column": start - text.rfind("\n", 0, start),
                              "function": name, "kind": "counted" if kind == "for" else "ordinary",
                              "label": label})
            index = closing + 1
        elif token == "{":
            index = braces[index] + 1
        else:
            index += 1
    return functions, loops


def scan_tree(root):
    functions, loops = [], []
    layout = root / "renderer/layout"
    for path in sorted(layout.rglob("*.wf")):
        module_dir = path.parent
        while not (module_dir / "module.wfm").is_file():
            if module_dir == layout or module_dir == root:
                raise Invalid(f"{path}: no owning module interface")
            module_dir = module_dir.parent
        module = ".".join(module_dir.relative_to(root / "renderer").parts)
        more_functions, more_loops = scan_source(path.read_text(), path.relative_to(root).as_posix(), module)
        functions.extend(more_functions)
        loops.extend(more_loops)
    names = [function["function"] for function in functions]
    if len(set(names)) != len(names) or not functions:
        raise Invalid("source functions absent or duplicate qualified source function")
    return functions, loops


def ledger_rows(text, root):
    rows = defaultdict(list)
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.startswith("PAR loop"):
            continue
        match = LOOP_ROW.fullmatch(raw)
        if match is None:
            raise Invalid(f"ledger:{number}: malformed loop row")
        name, line, verdict, reason = match.groups()
        path = Path(name)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(root.resolve())
            except ValueError:
                # Standard-library or other package sources are outside scope.
                continue
        elif not name.startswith("renderer/"):
            path = Path("renderer") / path
        name = path.as_posix()
        if not name.startswith("renderer/layout/"):
            continue
        rule = "PAR-2"
        condition = re.match(r"condition (\d+):", reason)
        if verdict == "denied":
            if condition is None or condition[1] not in {"1", "2", "3", "4", "5"}:
                raise Invalid(f"ledger:{number}: denial lacks a PAR-2 condition")
            rule += f" condition {condition[1]}"
        elif not reason.startswith("eligible;"):
            raise Invalid(f"ledger:{number}: permission lacks eligibility reason")
        rows[(name, int(line))].append({"verdict": verdict, "reason": reason, "rule": rule, "raw": raw})
    return rows


def join_loops(loops, ledger):
    counts = defaultdict(int)
    for loop in loops:
        if loop["kind"] == "counted":
            counts[(loop["file"], loop["line"])] += 1
    missing = [f"{loop['file']}:{loop['line']} ({loop['function']})" for loop in loops
               if loop["kind"] == "counted" and (loop["file"], loop["line"]) not in ledger]
    ambiguous = [f"{path}:{line} ({count} loops)" for (path, line), count in counts.items() if count > 1]
    extra = [f"{path}:{line}" for path, line in ledger if (path, line) not in counts]
    if missing or ambiguous or extra:
        raise Invalid("loop coverage gap: " + "; ".join(
            message for message in (
                "missing counted verdicts: " + ", ".join(missing) if missing else "",
                "same-line loops cannot be distinguished by pinned ledger: " + ", ".join(ambiguous) if ambiguous else "",
                "ledger sites absent from scanned source: " + ", ".join(extra) if extra else "") if message))
    joined = []
    for loop in loops:
        verdicts = ledger.get((loop["file"], loop["line"]), []) if loop["kind"] == "counted" else []
        if not verdicts:
            verdicts = [{"verdict": "uncovered", "reason": "PAR-2 judges counted for only; ordinary loop has no loop verdict",
                         "rule": "PAR-2 outside counted-loop scope", "raw": ""}]
        status = "mixed" if len({row["verdict"] for row in verdicts}) > 1 else verdicts[0]["verdict"]
        for variant, row in enumerate(verdicts, 1):
            joined.append({**loop, "variant": variant, "site_verdict": status, **row})
    return joined


def normalize_llvm_symbol(symbol):
    """Remove numeric LLVM promotion segments; retain all other spelling."""
    return re.sub(r"\.llvm\.[0-9]+(?=\.|\$|'|$)", "", symbol)


def normalize_symbol(symbol):
    """Pinned source symbols: wf_NAME, $instance$..., .body[.llvm.N]."""
    symbol = normalize_llvm_symbol(symbol)
    if not symbol.startswith("wf_"):
        return None
    name = symbol[3:]
    if name.startswith("_par_seq_"):
        name = name[len("_par_seq_"):]
    name = re.sub(r"(?:'\d+)+$", "", name)
    name = re.sub(r"\.body$", "", name)
    return name.split("$instance$", 1)[0]


def symbol_audit(page, profile, own, edges, source_names):
    rows = []
    for raw in sorted(set(own) | {symbol for pair in edges for symbol in pair}):
        source = normalize_symbol(raw)
        rows.append({"page": page, "profile": profile, "raw_symbol": raw,
                     "llvm_normalized_symbol": normalize_llvm_symbol(raw),
                     "source_function": source if source in source_names else ""})
    return rows


def ledger_symbol_audit(text, source_names):
    rows = []
    pattern = re.compile(r"^PAR split\s+(\S+)\s+loop at (\d+(?:\.\d+)*)\s+(.+)$")
    for number, raw_line in enumerate(text.splitlines(), 1):
        if not raw_line.startswith("PAR split"):
            continue
        match = pattern.fullmatch(raw_line)
        if match is None:
            raise Invalid(f"ledger:{number}: malformed split actualization row")
        raw, node_path, _ = match.groups()
        normalized = normalize_llvm_symbol(raw)
        source = normalize_symbol(normalized if normalized.startswith("wf_") else "wf_" + normalized)
        rows.append({"raw_symbol": raw, "llvm_normalized_symbol": normalized,
                     "source_function": source if source in source_names else "",
                     "node_path": node_path, "raw_line": raw_line})
    return rows


def driver_observations(path):
    """Check the producer's driver join evidence before rendering observations."""
    try:
        provenance = json.loads(path.read_text())
        identities = provenance["driver_identities"]
        common_sections = provenance["common_sections"]
        common_table = provenance["common_function_table"]
        if set(identities) != set(PAGES) or set(common_sections) != {".text", ".rodata", ".data"}:
            raise Invalid(f"{path}: driver identities or section inventory is incomplete")
        for section in common_sections.values():
            if not re.fullmatch(r"[0-9a-f]{64}", section["sha256"]) or type(section["size"]) is not int or section["size"] < 0:
                raise Invalid(f"{path}: invalid section hash or size")
        hashes, variants = {}, {}
        for page in PAGES:
            identity = identities[page]
            hashes[page] = identity["file_sha256"]
            if not re.fullmatch(r"[0-9a-f]{64}", hashes[page]):
                raise Invalid(f"{path}: invalid {page} whole-file hash")
            if identity["sections"] != common_sections:
                raise Invalid(f"{path}: {page} driver sections differ")
            functions = identity["functions"]
            for function in functions:
                if function["normalized"] != normalize_llvm_symbol(function["raw"]) or type(function["size"]) is not int or function["size"] < 0:
                    raise Invalid(f"{path}: {page} function normalization or size is invalid")
            table = sorted(({"name": function["normalized"], "size": function["size"]} for function in functions),
                           key=lambda entry: (entry["name"], entry["size"]))
            if identity["normalized_function_table"] != table or common_table != table:
                raise Invalid(f"{path}: {page} normalized function names or sizes differ")
            variants[page] = [{"raw": raw, "normalized": normalized} for raw, normalized in sorted({
                (function["raw"], function["normalized"]) for function in functions
                if function["raw"] != function["normalized"]})]
            if identity["llvm_suffix_variants"] != variants[page]:
                raise Invalid(f"{path}: {page} LLVM suffix audit differs from raw symbols")
        varied = len(set(hashes.values())) > 1
        if provenance["whole_file_hash_variation"] is not varied or provenance["llvm_symbol_variations"] != variants:
            raise Invalid(f"{path}: driver variation observation differs from evidence")
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise Invalid(f"{path}: incomplete or malformed driver join provenance") from error
    examples = sorted({(entry["raw"], entry["normalized"]) for entries in variants.values() for entry in entries})
    lines = ["## Driver join observations", "",
             f"The three page drivers have {len(set(hashes.values()))} distinct whole-file SHA-256 hashes "
             f"({'variation observed' if varied else 'all equal'}). The recorded .text, .rodata and .data hashes and sizes match, "
             "and their normalized function names and sizes match with duplicates preserved.", "",
             f"Observed numeric LLVM suffix variants: {sum(len(entries) for entries in variants.values())} page-symbol records "
             f"({len(examples)} distinct raw-to-normalized pairs). Raw driver evidence remains in join-provenance.json; "
             "matching measured sections and function tables does not establish whole-file identity or prove these suffixes are the only difference.", ""]
    lines.extend(f"- `{raw}` → `{normalized}`" for raw, normalized in examples[:10])
    lines.append("")
    return lines


def aggregate_profile(own, edges, source_names):
    self_cost, outgoing, symbols = defaultdict(int), defaultdict(int), defaultdict(set)
    unmatched = {}
    mapped = {}
    for symbol in set(own) | {symbol for pair in edges for symbol in pair}:
        name = normalize_symbol(symbol)
        mapped[symbol] = name if name in source_names else None
        if mapped[symbol]:
            symbols[name].add(symbol)
        else:
            unmatched[symbol] = own.get(symbol)
    for symbol, cost in own.items():
        if mapped[symbol]:
            self_cost[mapped[symbol]] += cost
    for (caller, callee), cost in edges.items():
        name = mapped[caller]
        if name and name != mapped[callee]:
            outgoing[name] += cost
    inclusive = {name: self_cost[name] + outgoing[name] for name in symbols}
    return dict(self_cost), inclusive, symbols, dict(unmatched)


def read_raw(path, repetitions):
    match = RAW_ROW.fullmatch(path.read_text())
    if match is None:
        raise Invalid(f"{path}: expected one complete layout elements/contexts/paragraphs/reps record")
    elements, contexts, paragraphs, reps = map(int, match.groups())
    if reps != repetitions or (repetitions and (elements == 0 or contexts == 0)):
        raise Invalid(f"{path}: invalid layout profile repetition or empty layout")
    if not repetitions and (contexts or paragraphs):
        raise Invalid(f"{path}: zero control produced contexts or paragraphs")
    return elements, contexts, paragraphs, reps


def write_csv(path, rows, fields):
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        writer.writerows(rows)


LOOP_FIELDS = ["file", "line", "column", "function", "kind", "label", "variant", "site_verdict", "verdict", "rule", "reason", "raw"]


def inventory(root, ledger_path, out):
    functions, loops = scan_tree(root)
    joined = join_loops(loops, ledger_rows(ledger_path.read_text(), root))
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "loops.csv", joined, LOOP_FIELDS)
    print(f"counted-loop coverage complete: {sum(loop['kind'] == 'counted' for loop in loops)} source loops; "
          f"{sum(loop['kind'] == 'ordinary' for loop in loops)} ordinary loops outside PAR-2")
    return functions, loops, joined


def summarize(root, ledger_path, out):
    functions, loops, joined = inventory(root, ledger_path, out)
    names = {function["function"] for function in functions}
    profiles = {}
    audit = []
    for page in PAGES:
        path = out / f"{page}.callgrind"
        total, own, edges = parse_callgrind(path)
        audit.extend(symbol_audit(page, page, own, edges, names))
        self_cost, inclusive, symbols, unmatched = aggregate_profile(own, edges, names)
        if total <= 0 or inclusive.get("layout.lay_out", 0) <= 0:
            raise Invalid(f"{path}: layout.lay_out is unobserved/nonpositive or total is nonpositive")
        # The toggle covers lay_out's entire dynamic invocation. Its normalized
        # inclusive cost must close exactly over the exclusive profile footer.
        if inclusive["layout.lay_out"] != total:
            raise Invalid(f"{path}: lay_out inclusive {inclusive['layout.lay_out']} != profile total {total}")
        raw = read_raw(out / f"{page}.raw", 1)
        ranks = {name: rank for rank, name in enumerate(sorted(inclusive, key=lambda n: (-inclusive[n], n)), 1)}
        profiles[page] = (total, self_cost, inclusive, symbols, unmatched, raw, ranks)
    for page in PAGES:
        control = out / f"{page}-zero.callgrind"
        zero, own, edges = parse_callgrind(control)
        audit.extend(symbol_audit(page, f"{page}-zero", own, edges, names))
        if zero != 0:
            raise Invalid(f"{control}: zero control recorded {zero} Ir")
        read_raw(out / f"{page}-zero.raw", 0)
    observations = driver_observations(out / "join-provenance.json")
    ledger_symbols = ledger_symbol_audit(ledger_path.read_text(), names)

    by_function = defaultdict(list)
    for row in joined:
        by_function[row["function"]].append(row)
    refused_names = {row["function"] for row in joined if row["verdict"] == "denied"}
    refused_ranks = {page: {name: rank for rank, name in enumerate(
        sorted(refused_names & inclusive.keys(), key=lambda n: (-inclusive[n], n)), 1)}
        for page, (_, _, inclusive, _, _, _, _) in profiles.items()}
    rows = []
    for function in functions:
        name = function["function"]
        refused = [row for row in by_function[name] if row["verdict"] == "denied"]
        details = " | ".join(f"{row['file']}:{row['line']} variant {row['variant']}: {row['reason']}" for row in refused)
        row = {**function, "counted_loops": sum(loop["function"] == name and loop["kind"] == "counted" for loop in loops),
               "ordinary_loops": sum(loop["function"] == name and loop["kind"] == "ordinary" for loop in loops),
               "refused_sites": len({(loop['file'], loop['line']) for loop in refused}),
               "refused_verdicts": len(refused), "refused_loop_details": details}
        for page, (total, own, inclusive, symbols, _, _, ranks) in profiles.items():
            observed = name in inclusive
            row.update({f"{page}_status": "observed" if observed else "unobserved; possibly inlined or outside collected invocation",
                        f"{page}_self_Ir": own.get(name, 0) if observed else "",
                        f"{page}_self_share": f"{own.get(name, 0) / total:.9f}" if observed else "",
                        f"{page}_inclusive_Ir": inclusive[name] if observed else "",
                        f"{page}_inclusive_share": f"{inclusive[name] / total:.9f}" if observed else "",
                        f"{page}_rank": ranks.get(name, ""),
                        f"{page}_refused_rank": refused_ranks[page].get(name, ""),
                        f"{page}_symbols": " | ".join(sorted(symbols.get(name, ())))})
        rows.append(row)
    rows.sort(key=lambda row: (-max((float(row[f"{page}_inclusive_share"]) for page in PAGES if row[f"{page}_inclusive_share"] != ""), default=-1), row["function"]))
    function_fields = ["file", "line", "function", "counted_loops", "ordinary_loops", "refused_sites", "refused_verdicts", "refused_loop_details"]
    function_fields += [f"{page}_{field}" for page in PAGES for field in ("status", "self_Ir", "self_share", "inclusive_Ir", "inclusive_share", "rank", "refused_rank", "symbols")]
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "loops.csv", joined, LOOP_FIELDS)
    write_csv(out / "functions.csv", rows, function_fields)
    write_csv(out / "symbol-map.csv", audit, ["page", "profile", "raw_symbol", "llvm_normalized_symbol", "source_function"])
    write_csv(out / "ledger-symbols.csv", ledger_symbols, ["raw_symbol", "llvm_normalized_symbol", "source_function", "node_path", "raw_line"])
    summary = ["# Layout loop inventory", "", f"Source functions: {len(functions)}. Source loops: {len(loops)} "
               f"({sum(loop['kind'] == 'counted' for loop in loops)} counted; {sum(loop['kind'] == 'ordinary' for loop in loops)} ordinary).",
               f"Ledger verdict rows: {sum(row['verdict'] != 'uncovered' for row in joined)}. "
               f"Refused verdict rows: {sum(row['verdict'] == 'denied' for row in joined)}. "
               f"Mixed source sites: {len({(row['file'], row['line']) for row in joined if row['site_verdict'] == 'mixed'})}.", "",
               "Every counted source loop has a ledger verdict. Ordinary loops are explicitly outside PAR-2's counted-loop judgment. "
               "Distinct generic verdicts remain separate rows; same-line counted-loop multiplicity is rejected because the pinned ledger cannot distinguish it.", "",
               "Inclusive Ir is normalized-family self cost plus outgoing edge Ir to different normalized families. "
               "Wrapper/body and instance variants are joined; internal family edges are excluded to prevent double counting. "
               "Recursive and ancestor/descendant inclusive costs overlap; shares are not additive and can exceed 100%. "
               "Unobserved functions receive no invented zero. Ranks cover observed source functions only; refused ranks cover functions holding refused loop verdicts. "
               "A compiler permission is not proof of runtime parallel execution; raw PAR split rows remain in the ledger artifact.", "",
               "Totals reconcile every exclusive event against each Callgrind totals footer. The profile's layout.lay_out inclusive Ir "
               "also equals its total, and all three page-specific zero-repetition controls have zero Ir. Call counts are not read as costs or reported.", ""]
    summary += ["Numeric .llvm.N segments are removed only for symbol joins; all raw names remain in symbol-map.csv and ledger-symbols.csv. "
                "Loop permission rows join by file and line, independently of symbol suffixes. Split rows join only to source function families: "
                "their structural NodePaths cannot be joined to source loop file/line sites without further compiler evidence.", ""]
    summary += observations
    for page, (total, own, inclusive, _, unmatched, raw, _) in profiles.items():
        summary += [f"## {page}", "", f"Ir: {total}; layout elements {raw[0]}, contexts {raw[1]}, paragraphs {raw[2]}, reps {raw[3]}. "
                    f"Observed source functions: {len(inclusive)}; unmatched exclusive Ir: {sum(cost or 0 for cost in unmatched.values())}.", "",
                    "| Rank | Source function | Inclusive share |", "| --- | --- | --- |"]
        for rank, name in enumerate(sorted(inclusive, key=lambda n: (-inclusive[n], n))[:20], 1):
            summary.append(f"| {rank} | `{name}` | {inclusive[name] / total:.2%} |")
        summary += ["", "Functions holding refused counted loops (observed only; all functions and exact verdict rows remain in the CSVs):", "",
                    "| Refused rank | Source function | Inclusive share | Self share | Refused sites | Compiler reasons |",
                    "| --- | --- | --- | --- | --- | --- |"]
        for name in sorted(refused_ranks[page], key=refused_ranks[page].get)[:20]:
            refused = [row for row in by_function[name] if row["verdict"] == "denied"]
            reasons = "<br>".join(f"line {row['line']}, variant {row['variant']}: {row['reason']}" for row in refused)
            reasons = reasons.replace("|", "\\|").replace("\n", " ")
            sites = len({(row['file'], row['line']) for row in refused})
            summary.append(f"| {refused_ranks[page][name]} | `{name}` | {inclusive[name] / total:.2%} | {own.get(name, 0) / total:.2%} | {sites} | {reasons} |")
        summary += ["", "Unmatched symbols (includes external helpers and unsupported source-symbol variants):", ""]
        summary += [f"- `{symbol}`: {str(cost) + ' exclusive Ir' if cost is not None else 'edge observed; no exclusive row'}"
                    for symbol, cost in sorted(unmatched.items(), key=lambda item: (-(item[1] or 0), item[0]))]
        if not unmatched:
            summary.append("None.")
        summary.append("")
    (out / "summary.md").write_text("\n".join(summary) + "\n")
    print(f"wrote {out / 'loops.csv'}, {out / 'functions.csv'}, {out / 'summary.md'}")


def dry_run():
    """Prove validators reject handmade wrong artifacts; no compiler/test run."""
    good = """version: 1
cmd: renderer assets=stylesheet
event: Sum = Ir + Dr
positions: line instr
events: Ir Dr
summary: 900 999
ob=(1) executable
fl=(1) source.wf
fn=(1) wf_layout.lay_out
1 0x10 2 1
cfn=(2) wf_layout.lay_out.body
calls=987654321 1 0x20
* +1 12 3
fn=(2)
1 0x20 3 1
cfn=(3) wf_layout.text.prepare$instance$7.body.llvm.1
calls=1 2 0x30
* +1 9 2
fn=(3)
2 0x30 9 2
totals: 14 4
"""
    checks = 0
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "handmade.callgrind"
        path.write_text(good)
        total, own, edges = parse_callgrind(path)
        assert total == 14 and sum(own.values()) == 14
        assert edges[("wf_layout.lay_out", "wf_layout.lay_out.body")] == 12
        _, inclusive, _, _ = aggregate_profile(own, edges, {"layout.lay_out", "layout.text.prepare"})
        assert inclusive == {"layout.lay_out": 14, "layout.text.prepare": 9}
        assert normalize_symbol("wf_layout.text.prepare$instance$7.body.llvm.1'2") == "layout.text.prepare"
        assert normalize_llvm_symbol("runtime_helper.llvm.12.llvm.34") == "runtime_helper"
        assert normalize_llvm_symbol("runtime_helper.llvm.56") == "runtime_helper"
        assert normalize_llvm_symbol("runtime_helper.llvm.foo") == "runtime_helper.llvm.foo"
        assert normalize_llvm_symbol("runtime_helper.llvm.123foo") == "runtime_helper.llvm.123foo"
        assert normalize_llvm_symbol("runtime_other.llvm.56") != normalize_llvm_symbol("runtime_helper.llvm.12")
        assert normalize_symbol("wf_layout.llvm.1.text.prepare$instance$7.llvm.2.body'2") == "layout.text.prepare"
        audited = symbol_audit("ecma262", "ecma262", {"runtime_helper.llvm.12": 3,
                              "wf_layout.llvm.1.lay_out.body.llvm.2": 5}, {}, {"layout.lay_out"})
        assert audited[0]["raw_symbol"] == "runtime_helper.llvm.12" and audited[0]["source_function"] == ""
        assert audited[0]["llvm_normalized_symbol"] == "runtime_helper"
        assert audited[1]["source_function"] == "layout.lay_out"
        split_line = "PAR split       layout.llvm.1.lay_out$instance$7.llvm.2  loop at 0.3.9  split independent map over 1 captured binding"
        split_audit = ledger_symbol_audit(split_line, {"layout.lay_out"})
        assert split_audit[0]["raw_line"] == split_line and split_audit[0]["node_path"] == "0.3.9"
        assert split_audit[0]["source_function"] == "layout.lay_out"
        default_positions = "events: Ir Dr\nfn=wf_layout.lay_out\n1 4\n+1\ntotals: 4 0\n"
        path.write_text(default_positions)
        assert parse_callgrind(path) == (4, {"wf_layout.lay_out": 4}, {})
        # Relative positions carry across function specifications and allow hex.
        path.write_text("positions: instr\nevents: Ir\nfn=first\n0x10 1\nfn=second\n+0x2 2\ntotals: 3\n")
        assert parse_callgrind(path)[0] == 3
        for corrupted in (good.replace("totals: 14 4", "totals: 13 4"), good.replace("totals: 14 4", ""),
                          good.replace("fn=(2)\n", "fn=(999)\n"), good.replace("1 0x10 2 1", "1 0x10 2 1 9"),
                          good.replace("* +1 12 3", ""), good.replace("1 0x10 2 1", "* 0x10 2 1"),
                          good.replace("events: Ir Dr", "events: Dr Dr"), good + "1 0x10 1 0\n"):
            path.write_text(corrupted)
            try:
                parse_callgrind(path)
            except Invalid:
                checks += 1
            else:
                raise AssertionError("accepted corrupted Callgrind fixture")
        zero = good.replace("2 1\n", "0 0\n").replace("12 3\n", "0 0\n").replace("3 1\n", "0 0\n").replace("9 2\n", "0 0\n").replace("14 4\n", "0 0\n")
        path.write_text(zero)
        assert parse_callgrind(path)[0] == 0
        source = '''struct S { doc "fn pretend() { for (i in 0_u64..n) { } }"; }
fn example() -> result: unit pure {
 doc "loop { } // for";
 // for (x in 0_u64..n) { }
 for (i in 0_u64..n) { loop @exit { break @exit; } }
 return unit;
}
'''
        functions, loops = scan_source(source, "renderer/layout/test.wf", "layout")
        assert len(functions) == 1 and [loop["kind"] for loop in loops] == ["counted", "ordinary"]
        contract = '''fn contracted<T: copy>() -> result: unit pure contract {
 requires True();
} {
 doc "for (not_a_loop) { loop { } }";
 for @items (i in 0_u64..count) { }
 return unit;
}
'''
        contract_functions, contract_loops = scan_source(contract, "renderer/layout/contract.wf", "layout")
        assert len(contract_functions) == len(contract_loops) == 1
        assert contract_loops[0]["line"] == 5 and contract_loops[0]["label"] == "items"
        ledger = ledger_rows("PAR loop        layout/test.wf:5  loop  permitted   eligible; no accumulator\n"
                             "PAR loop        layout/test.wf:5  loop  denied      condition 2: the body contains example\n", Path(directory))
        joined = join_loops(loops, ledger)
        assert len(joined) == 3 and joined[0]["site_verdict"] == "mixed" and joined[-1]["verdict"] == "uncovered"
        try:
            ledger_rows("PAR loop        layout/test.wf:5  loop  denied      condition 12: invalid\n", Path(directory))
        except Invalid:
            checks += 1
        else:
            raise AssertionError("accepted a nonexistent permission condition")
        for wrong_loops, wrong_ledger in ((loops, {}), (loops + [loops[0]], ledger), (loops, {**ledger, ("renderer/layout/test.wf", 90): ledger[("renderer/layout/test.wf", 5)]})):
            try:
                join_loops(wrong_loops, wrong_ledger)
            except Invalid:
                checks += 1
            else:
                raise AssertionError("accepted incomplete/ambiguous ledger coverage")
        raw_path = Path(directory) / "sample.raw"
        raw_path.write_text("layout elements 2 contexts 1 paragraphs 1 reps 1\n")
        assert read_raw(raw_path, 1) == (2, 1, 1, 1)
        for bad in ("layout elements 2 contexts 1 paragraphs 1 reps 0\n", "layout elements 2 contexts 1 paragraphs 1 reps 1\nextra\n", "layout elements 2 contexts 0 paragraphs 0 reps 1\n"):
            raw_path.write_text(bad)
            try:
                read_raw(raw_path, 1)
            except Invalid:
                checks += 1
            else:
                raise AssertionError("accepted corrupted raw protocol")
        # Full report generation against handmade source, ledger and profiles
        # checks CSV/report integration without reading project source or runs.
        root = Path(directory) / "fixture"
        layout = root / "renderer/layout"
        text_module = layout / "text"
        text_module.mkdir(parents=True)
        (layout / "module.wfm").write_text("")
        (text_module / "module.wfm").write_text("")
        (layout / "test.wf").write_text('fn lay_out() -> result: unit pure {\n for (i in 0_u64..count) { }\n}\nfn unobserved() -> result: unit pure { }\n')
        (text_module / "test.wf").write_text('fn prepare() -> result: unit pure contract { requires True(); } {\n for (i in 0_u64..count) { }\n}\n')
        out = root / "out"
        out.mkdir()
        ledger_path = out / "ledger.log"
        ledger_path.write_text("PAR loop        layout/test.wf:2  loop  denied      condition 1: fixture denial\n"
                               "PAR loop        layout/text/test.wf:2  loop  permitted   eligible; no accumulator\n" + split_line + "\n")
        for page in PAGES:
            (out / f"{page}.callgrind").write_text(good)
            (out / f"{page}.raw").write_text("layout elements 2 contexts 1 paragraphs 1 reps 1\n")
            (out / f"{page}-zero.callgrind").write_text(zero)
            (out / f"{page}-zero.raw").write_text("layout elements 2 contexts 0 paragraphs 0 reps 0\n")
        sections = {name: {"sha256": "a" * 64, "size": 20} for name in (".text", ".rodata", ".data")}
        identities = {}
        for number, page in enumerate(PAGES, 1):
            functions = [{"raw": f"wf_layout.llvm.{number}.lay_out.body.llvm.{number + 10}",
                          "normalized": "wf_layout.lay_out.body", "size": 42, "type": "F"},
                         {"raw": f"runtime_helper.llvm.{number}", "normalized": "runtime_helper", "size": 8, "type": "F"},
                         {"raw": f"runtime_helper.llvm.{number + 100}", "normalized": "runtime_helper", "size": 8, "type": "F"}]
            table = sorted(({"name": function["normalized"], "size": function["size"]} for function in functions),
                           key=lambda entry: (entry["name"], entry["size"]))
            variants = [{"raw": raw, "normalized": normalized} for raw, normalized in sorted({
                (function["raw"], function["normalized"]) for function in functions})]
            identities[page] = {"file_sha256": str(number) * 64, "sections": sections, "functions": functions,
                                "normalized_function_table": table, "llvm_suffix_variants": variants}
        provenance = {"driver_identities": identities, "common_sections": sections, "common_function_table": table,
                      "whole_file_hash_variation": True,
                      "llvm_symbol_variations": {page: identity["llvm_suffix_variants"] for page, identity in identities.items()}}
        provenance_path = out / "join-provenance.json"
        provenance_path.write_text(json.dumps(provenance))
        assert "variation observed" in "\n".join(driver_observations(provenance_path))
        changed = json.loads(json.dumps(provenance))
        changed["driver_identities"]["html5"]["functions"][0]["raw"] = "wf_layout.different.body.llvm.12"
        changed["driver_identities"]["html5"]["functions"][0]["normalized"] = "wf_layout.different.body"
        provenance_path.write_text(json.dumps(changed))
        try:
            driver_observations(provenance_path)
        except Invalid as error:
            assert "html5 normalized function names or sizes differ" in str(error)
            checks += 1
        else:
            raise AssertionError("accepted a real function-name difference after LLVM normalization")
        provenance_path.write_text(json.dumps(provenance))
        summarize(root, ledger_path, out)
        with (out / "functions.csv").open() as stream:
            reported = {row["function"]: row for row in csv.DictReader(stream)}
        assert reported["layout.lay_out"]["ecma262_refused_rank"] == "1"
        assert reported["layout.lay_out"]["ecma262_self_share"] == "0.357142857"
        assert reported["layout.unobserved"]["ecma262_inclusive_Ir"] == ""
        assert "fixture denial" in (out / "summary.md").read_text()
        assert "3 distinct whole-file SHA-256 hashes (variation observed)" in (out / "summary.md").read_text()
        assert "Observed numeric LLVM suffix variants: 9 page-symbol records" in (out / "summary.md").read_text()
        with (out / "symbol-map.csv").open() as stream:
            symbol_rows = list(csv.DictReader(stream))
        assert any(row["raw_symbol"] == "wf_layout.text.prepare$instance$7.body.llvm.1" and
                   row["llvm_normalized_symbol"] == "wf_layout.text.prepare$instance$7.body" and
                   row["source_function"] == "layout.text.prepare" for row in symbol_rows)
        with (out / "ledger-symbols.csv").open() as stream:
            assert list(csv.DictReader(stream))[0]["raw_line"] == split_line
        assert "all three page-specific zero-repetition controls have zero Ir" in (out / "summary.md").read_text()
        for missing in (out / "html5-zero.callgrind", out / "apollo11-zero.raw"):
            original = missing.read_text()
            missing.unlink()
            try:
                summarize(root, ledger_path, out)
            except FileNotFoundError as error:
                assert Path(error.filename) == missing
                checks += 1
            else:
                raise AssertionError("accepted a missing page-specific zero control")
            missing.write_text(original)
        nonzero = out / "apollo11-zero.callgrind"
        nonzero.write_text(good)
        try:
            summarize(root, ledger_path, out)
        except Invalid as error:
            assert str(error) == f"{nonzero}: zero control recorded 14 Ir"
            checks += 1
        else:
            raise AssertionError("accepted a nonzero page-specific control")
        nonzero.write_text(zero)
    print(f"handmade dry-run passed; {checks} corrupt artifacts rejected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("inventory", "summarize", "dry-run"), default="summarize")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--ledger", type=Path, default=Path("build/layout-par/par-ledger.log"))
    parser.add_argument("--out", type=Path, default=Path("build/layout-par"))
    args = parser.parse_args()
    try:
        if args.dry_run or args.command == "dry-run":
            dry_run()
        elif args.command == "inventory":
            inventory(args.root, args.ledger, args.out)
        else:
            summarize(args.root, args.ledger, args.out)
    except (Invalid, OSError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
