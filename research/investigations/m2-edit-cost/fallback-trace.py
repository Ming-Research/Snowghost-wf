"""Temporary increment-0 trace reconciliation, called by fallback-trace.yml.

The native oracle has no machine-readable CSV writer. This helper validates
its private diagnostic records, reuses the existing X5 correctness/path
checkers, and writes the evidence CSV and grouped Markdown. Remove with the
workflow after the trace evidence is archived. No performance is measured.
"""
import argparse
from collections import Counter, defaultdict
import csv
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / 'research/investigations/incremental-layout/scripts'
KINDS = ('blocks', 'paragraphs', 'contexts', 'routes')
SCOPE_FIELDS = ('context_slot', 'context_node',
    *(f'existing_{kind}' for kind in KINDS),
    *(f'outside_existing_{kind}' for kind in KINDS),
    *(f'built_{kind}' for kind in KINDS),
    *(f'outside_built_{kind}' for kind in KINDS),
    'mixed_existing_paragraphs', 'mixed_built_paragraphs')
NEUTRAL_FAILURES = {1: 'no unique complete named payload',
    2: 'counter/quote walk effects', 4: 'split head or open inline state',
    8: 'box source topology or outside construction correspondence unproved',
    16: 'unstable generated references', 32: 'source seam is not complete'}
FLOAT_FIELDS = ('float_node', 'consumer_kind', 'consumer_node',
    'stationary_reach', 'old_floor', 'new_floor', 'dependency_kind', 'guard_id')
CONSUMER_KINDS = {0: 'float export membership has no queried consumer',
    1: 'open block', 2: 'paragraph text source', 3: 'child context',
    4: 'float child', 5: 'positioned child', 6: 'inserted complete block'}
DEPENDENCY_KINDS = {1: 'old natural-floor minimum', 2: 'new natural-floor minimum',
                    3: 'changed float-export membership'}
NO_INDEX = 4294967295
I64_MIN = -9223372036854775808
I64_MAX = 9223372036854775807
U64_MAX = 18446744073709551615
PREFIX = 'fallback_trace '


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory(path, canonical=False):
    document = json.loads(path.read_text())
    paths = document['paths']
    result = {}
    for row in paths:
        if (not isinstance(row, list) or len(row) != 3 or
                any(type(value) is not int for value in row)):
            raise ValueError('malformed path inventory')
        edit, admitted, reason = row
        if edit in result or edit <= 0 or admitted not in (0, 1):
            raise ValueError('duplicate or invalid inventory operation')
        if not 0 <= reason <= 11 or (admitted == 1) != (reason == 0):
            raise ValueError('inconsistent inventory admission/reason')
        result[edit] = (admitted, reason)
    if sorted(result) != list(range(1, len(result) + 1)) or not result:
        raise ValueError('path inventory must contain every operation in order')
    if canonical and (len(result) != 60 or Counter(result.values()) !=
            Counter({(1, 0): 38, (0, 9): 18, (0, 7): 2, (0, 3): 2})):
        raise ValueError('canonical frozen 60-operation path inventory changed')
    return result


def guards(path):
    manifest = json.loads(path.read_text())
    rows = manifest['guards'] if isinstance(manifest, dict) else manifest
    found = {}
    for row in rows:
        identifier = row['id']
        if type(identifier) is not int or identifier <= 0 or identifier in found:
            raise ValueError('duplicate or invalid exact guard ID')
        for key in ('file', 'function', 'guard'):
            if not isinstance(row[key], str) or not row[key]:
                raise ValueError('incomplete exact guard manifest')
        if type(row['line']) is not int or row['line'] <= 0:
            raise ValueError('invalid exact guard source line')
        found[identifier] = row
    if not found:
        raise ValueError('empty exact guard manifest')
    return found


def operations(path):
    found = []
    for line in path.read_text().splitlines():
        if not line:
            continue
        fields = line.split(' ')
        if fields[0] in ('S', 'P', 'V'):
            continue
        if fields[0] == 'B' and len(fields) >= 4:
            if not fields[1].isdigit() or not (fields[2] == '-' or fields[2].isdigit()):
                raise ValueError('malformed block insertion')
        elif fields[0] == 'X' and len(fields) == 2 and fields[1].isdigit():
            pass
        else:
            raise ValueError('trace script must contain only block insertion/removal')
        found.append(fields)
    if not found:
        raise ValueError('empty trace edit script')
    return found


def decode(raw, expected, exact_guards, script):
    rows = {edit: {'edit': edit, 'operation': script[edit - 1][0],
                  'floats': []} for edit in expected}
    seen = set()
    ordinary = []
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.startswith(PREFIX):
            if line.startswith('fallback_trace'):
                raise ValueError(f'line {line_number}: malformed diagnostic prefix')
            ordinary.append(line)
            continue
        match = re.fullmatch(r'fallback_trace ([a-z]+) (\d+)((?: -?\d+)+)\n', line)
        if not match:
            raise ValueError(f'line {line_number}: malformed diagnostic record')
        kind, identifier, payload = match.groups()
        edit = int(identifier)
        if edit not in rows:
            raise ValueError('diagnostic names unexpected operation')
        values = [int(value) for value in payload.split()]
        if any(value < I64_MIN or value > U64_MAX for value in values):
            raise ValueError('diagnostic integer exceeds its storage type')
        if kind != 'float':
            if (edit, kind) in seen:
                raise ValueError('duplicate diagnostic record')
            seen.add((edit, kind))
        row = rows[edit]
        if kind == 'edit' and len(values) == 4:
            admitted, reason, parent, edited = values
            if any(value < 0 for value in values) or (admitted, reason) != expected[edit]:
                raise ValueError('diagnostic admission differs from fixed path inventory')
            if parent >= NO_INDEX or edited >= NO_INDEX:
                raise ValueError('diagnostic edit names an absent source identity')
            operation = script[edit - 1]
            if (operation[0] == 'B' and parent != int(operation[1]) or
                    operation[0] == 'X' and edited != int(operation[1])):
                raise ValueError('diagnostic source identity differs from edit script')
            row.update(admitted=admitted, reason=reason, parent_node=parent, edited_node=edited)
        elif kind == 'guard' and len(values) == 1:
            guard, = values
            if guard < 0 or guard and guard not in exact_guards:
                raise ValueError('unknown exact guard')
            row['guard_id'] = guard
        elif kind == 'scope' and len(values) == len(SCOPE_FIELDS):
            if any(value < 0 for value in values):
                raise ValueError('negative source-scope cardinality')
            if values[0] >= NO_INDEX or values[1] >= NO_INDEX:
                raise ValueError('scope names an absent checkpoint identity')
            row.update(zip(SCOPE_FIELDS, values))
        elif kind == 'neutral' and len(values) == 2:
            neutral, failures = values
            if neutral not in (0, 1) or failures < 0 or failures & ~63 or (neutral == 1) != (failures == 0):
                raise ValueError('inconsistent source-neutral certificate')
            row.update(source_neutral=neutral, source_failures=failures)
        elif kind == 'retained' and len(values) == 3:
            retained, identity_ok, identity_count = values
            if retained not in (0, 1) or identity_ok not in (0, 1) or identity_count < 0:
                raise ValueError('invalid source-retention outcome')
            if not retained and (identity_ok or identity_count):
                raise ValueError('identity audit attached to a non-retaining outcome')
            row.update(retained_source=retained, retained_identity_ok=identity_ok,
                       retained_identity_count=identity_count)
        elif kind == 'float' and len(values) == len(FLOAT_FIELDS):
            float_node, consumer_kind, consumer_node = values[:3]
            dependency_kind = values[-2]
            absent_consumer = (consumer_kind == 0 and dependency_kind == 3 and consumer_node == NO_INDEX)
            if (not 0 <= float_node < NO_INDEX or consumer_kind not in CONSUMER_KINDS or
                    not (0 <= consumer_node < NO_INDEX or absent_consumer) or
                    dependency_kind not in DEPENDENCY_KINDS or values[-1] not in exact_guards or
                    (consumer_kind == 0) != (dependency_kind == 3)):
                raise ValueError('invalid float/consumer dependency')
            reach, old_floor, new_floor = values[3:6]
            if any(not I64_MIN <= value <= I64_MAX for value in (reach, old_floor, new_floor)):
                raise ValueError('float extrema exceed signed 64-bit coordinates')
            if dependency_kind in (1, 2):
                selected_floor = old_floor if dependency_kind == 1 else new_floor
                if (reach in (-I64_MAX, I64_MAX) or selected_floor == I64_MAX or
                        selected_floor != min(old_floor, new_floor) or reach <= selected_floor):
                    raise ValueError('recorded float extrema do not refuse the motion certificate')
            if values in row['floats']:
                raise ValueError('duplicate float/consumer dependency')
            row['floats'].append(values)
        else:
            raise ValueError('unknown diagnostic record or wrong field count')
    created = [int(value) for value in re.findall(r'^created (\d+)$', ''.join(ordinary), re.M)]
    construction_rows = re.findall(r'^structure edit (\d+) contexts (\d+) paragraphs (\d+) reused (\d+)$',
                                   ''.join(ordinary), re.M)
    construction = {int(edit): (int(contexts), int(paragraphs))
                    for edit, contexts, paragraphs, reused in construction_rows}
    if len(construction) != len(construction_rows):
        raise ValueError('duplicate ordinary structural construction counts')
    insertions = [edit for edit in rows if script[edit - 1][0] == 'B']
    if len(created) != len(insertions):
        raise ValueError('created identities do not cover every insertion')
    for edit, node in zip(insertions, created):
        if rows[edit].get('edited_node') != node:
            raise ValueError('diagnostic insertion identity differs from created record')
    for edit, row in rows.items():
        required = {(edit, kind) for kind in ('edit', 'guard', 'neutral', 'retained')}
        if not required <= seen:
            raise ValueError(f'edit {edit}: missing diagnostic record')
        if (row['admitted'] == 1) != (row['guard_id'] == 0):
            raise ValueError('exact guard disagrees with splice admission')
        if row['admitted']:
            if (edit, 'scope') in seen or row['floats'] or row['retained_source']:
                raise ValueError('admitted splice reports fallback-only source/dependencies')
            continue
        if (edit, 'scope') not in seen or row['existing_contexts'] == 0:
            raise ValueError('refusal lacks original checkpoint scope')
        if row['retained_source']:
            if row['retained_identity_ok'] != 1 or row['retained_identity_count'] == 0:
                raise ValueError('source-retaining fallback lacks a complete surviving identity audit')
            if not row['source_neutral']:
                raise ValueError('source-retaining fallback lacks complete-block certificate')
            if any(row[f'outside_built_{kind}'] for kind in KINDS) or row['mixed_built_paragraphs']:
                raise ValueError('source-retaining fallback constructed outside the edited subtree')
        elif row['built_contexts'] == 0:
            raise ValueError('reconstruction refusal lacks complete rebuilt checkpoint scope')
        if construction.get(edit) != (row['built_contexts'], row['built_paragraphs']):
            raise ValueError('checkpoint construction counts differ from ordinary structural observation')
        for phase in ('existing', 'built'):
            for kind in KINDS:
                if row[f'outside_{phase}_{kind}'] > row[f'{phase}_{kind}']:
                    raise ValueError('outside-subtree count exceeds checkpoint scope')
            if row[f'mixed_{phase}_paragraphs'] > row[f'{phase}_paragraphs']:
                raise ValueError('mixed paragraph count exceeds checkpoint paragraphs')
        entry = exact_guards[row['guard_id']]
        if 'reason' in entry and entry['reason'] != row['reason']:
            raise ValueError('exact guard belongs to another refusal reason')
        layout_error = entry.get('kind') == 'layout_error'
        if row['reason'] == 9 and not row['floats'] and not layout_error:
            raise ValueError('reason-9 refusal lacks float/consumer evidence')
        if layout_error and row['floats']:
            raise ValueError('layout error reports a float refusal')
        if any(record[-1] != row['guard_id'] for record in row['floats']):
            raise ValueError('float operand record names another rejecting predicate')
        for record in row['floats']:
            function = exact_guards[record[-1]]['function']
            if (record[-2] in (1, 2) and function not in ('motion_above', 'motion_range_ready') or
                    record[-2] == 3 and function != 'splice_sequence_plan'):
                raise ValueError('float dependency kind does not match the exact guard function')
        if row['reason'] != 9 and row['floats']:
            raise ValueError('float dependencies attached to another refusal reason')
    return ''.join(ordinary), [rows[edit] for edit in sorted(rows)]


def reconcile(ordinary, diagnostic, expected, script, out):
    checker = load_module('inctime')
    path_checker = load_module('fallback-followup')
    kinds = [operation[0] for operation in script]
    for path in (ordinary, diagnostic):
        checker.read(str(path), kinds, checking=True, require_paths=True)
        path_checker.require_paths(path.read_text(), expected)
    if ordinary.read_bytes() != diagnostic.read_bytes():
        raise ValueError('diagnostic changed ordinary byte output')
    (out / 'expected.paths').write_text(''.join(
        f'structure path {edit} splice {local} reason {reason}\n'
        for edit, (local, reason) in expected.items()))


def summarize(args, canonical=False):
    args.out.mkdir(parents=True, exist_ok=True)
    expected = inventory(args.inventory, canonical=canonical)
    script = operations(args.script)
    if len(script) != len(expected):
        raise ValueError('script length differs from fixed path inventory')
    exact_guards = guards(args.manifest)
    clean, rows = decode(args.diagnostic.read_text(), expected, exact_guards, script)
    if canonical:
        retained = {row['edit'] for row in rows if row['retained_source']}
        required_retention = {1, 2, 3, 4, 5, 6, 9, 10, 17, 18, 19, 20,
                              23, 24, 29, 30, 39, 40, 51, 52}
        if retained != required_retention:
            raise ValueError('canonical motion refusals did not retain their source scope')
    filtered = args.out / 'diagnostic.ordinary'
    filtered.write_text(clean)
    reconcile(args.ordinary, filtered, expected, script, args.out)
    fields = ('edit', 'operation', 'admitted', 'reason', 'parent_node', 'edited_node',
              'guard_id', 'guard_file', 'guard_function', 'guard_line', 'guard', 'guard_kind',
              'source_neutral', 'source_failures', 'source_failure_names', 'retained_source',
              'retained_identity_ok', 'retained_identity_count',
              *SCOPE_FIELDS, 'float_dependencies')
    (args.out / 'trace-schema.json').write_text(json.dumps(dict(
        scope_fields=SCOPE_FIELDS, float_fields=FLOAT_FIELDS,
        consumer_kinds=CONSUMER_KINDS, dependency_kinds=DEPENDENCY_KINDS,
        source_neutral_failures=NEUTRAL_FAILURES), indent=2) + '\n')
    with (args.out / 'fallback-trace.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            entry = exact_guards[row['guard_id']] if row['guard_id'] else {}
            output = {key: value for key, value in row.items() if key in fields}
            output.update(guard_file=entry.get('file', ''), guard_function=entry.get('function', ''),
                guard_line=entry.get('line', ''), guard=entry.get('guard', ''),
                guard_kind=entry.get('kind', 'predicate') if entry else '',
                source_failure_names='; '.join(name for bit, name in NEUTRAL_FAILURES.items()
                    if row['source_failures'] & bit),
                float_dependencies=json.dumps([dict(zip(FLOAT_FIELDS, record),
                    consumer_kind_name=CONSUMER_KINDS[record[1]],
                    dependency_kind_name=DEPENDENCY_KINDS[record[-2]])
                    for record in sorted(row['floats'])], separators=(',', ':')))
            writer.writerow(output)
    refused = [row for row in rows if not row['admitted']]
    groups = defaultdict(list)
    for row in refused:
        scope = 'complete block neutral' if row['source_neutral'] else 'source-only criterion not certified'
        outcome = 'source retained' if row['retained_source'] else 'checkpoint rebuilt'
        groups[row['guard_id'], scope, row['source_failures'], outcome].append(row)
    text = ['# Increment 0 fallback trace', '',
        f'{len(rows)} structural operations: {len(rows) - len(refused)} admitted, {len(refused)} refused. '
        'Every operation matches fresh full layout; fixed paths and ordinary output are unchanged.', '',
        'Existing counts describe the original exact checkpoint; built counts describe actual '
        'constructed payloads and route records. Source retention excludes its private synthetic context. '
        'Outside counts are relative to the edited subtree; mixed paragraphs are reported separately. '
        'Float records identify the operands of the refusing proof, not a measured physical intersection.', '',
        '| Exact failing guard | Source scope | Fallback outcome | IDs | Existing / built payloads | Outside existing / built |',
        '| --- | --- | --- | --- | --- | --- |']
    for (guard_id, scope, failures, outcome), group in sorted(groups.items()):
        entry = exact_guards[guard_id]
        guard = entry['guard'].replace('|', '\\|').replace('\n', ' ')
        source = f"{entry['file']}:{entry['line']} `{entry['function']}`"
        if failures:
            scope += ': ' + '; '.join(name for bit, name in NEUTRAL_FAILURES.items() if failures & bit)
        def counts(prefix):
            return ', '.join(f'{sum(row[prefix + kind] for row in group)} {kind}' for kind in KINDS)
        text.append(f'| {source}: `{guard}` | {scope} | {outcome} | '
                    f'{", ".join(str(row["edit"]) for row in group)} | '
                    f'{counts("existing_")} / {counts("built_")} | '
                    f'{counts("outside_existing_")} / {counts("outside_built_")} |')
    reason_nine = [row for row in refused if row['reason'] == 9]
    neutral_nine = sum(row['source_neutral'] for row in reason_nine)
    text.extend(['', f'Reason 9: {neutral_nine}/{len(reason_nine)} source-neutral complete-block edits. '
        'Use the plan’s pre-run reorder criterion; these counts alone are no performance result.', '',
        'The CSV contains one row per operation, exact checkpoint cardinalities and all recorded '
        'float/consumer operands. Raw logs, guard manifest and private source diff accompany it.'])
    (args.out / 'fallback-trace.md').write_text('\n'.join(text) + '\n')
    print(f'trace: {len(rows)} operations, {len(refused)} refusals; full-layout, paths and byte equality pass')


def execute(driver, script, destination):
    sheets = ('wikibase.client.init&only=styles&skin=vector-2022=build/research/concurrency/apollo11-modules.css',
              'modules=site.styles&only=styles&skin=vector-2022=build/research/concurrency/apollo11-site.css')
    command = [str(driver.resolve()), 'edit', str(script),
               'build/research/concurrency/apollo11.html', 'renderer/style/ua.css', *sheets]
    started = time.monotonic()
    with destination.open('w') as stdout, destination.with_suffix('.stderr').open('w') as stderr:
        completed = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=240)
    destination.with_suffix('.status').write_text(str(completed.returncode) + '\n')
    elapsed = time.monotonic() - started
    if completed.returncode:
        raise ValueError(f'oracle failed with status {completed.returncode}: {destination}')
    return elapsed


def run(args):
    args.out.mkdir(parents=True, exist_ok=True)
    expected = inventory(args.inventory, canonical=True)
    script = operations(args.script)
    if len(script) != 60 or script[0][0] != 'B' or script[1][0] != 'X':
        raise ValueError('canonical script must begin with its insertion/removal inverse')
    lines = args.script.read_text().splitlines(keepends=True)
    pilot = args.out / 'pilot.edits'
    edit_lines = [line for line in lines if line[:2] in ('B ', 'X ')]
    pilot.write_text(''.join(line for line in lines if line.startswith('S ')) + ''.join(edit_lines[:2]))
    pilot_inventory = args.out / 'pilot-paths.json'
    pilot_inventory.write_text(json.dumps({'paths': [[edit, *expected[edit]] for edit in (1, 2)]}) + '\n')
    pilot_runs = []
    for repeat in (1, 2):
        sample = args.out / f'pilot-{repeat}'
        sample.mkdir()
        ordinary = sample / 'ordinary.raw'
        diagnostic = sample / 'diagnostic.raw'
        durations = [execute(args.ordinary, pilot, ordinary), execute(args.diagnostic, pilot, diagnostic)]
        sample_args = argparse.Namespace(ordinary=ordinary, diagnostic=diagnostic,
            script=pilot, inventory=pilot_inventory, manifest=args.manifest, out=sample)
        summarize(sample_args)
        for checked in (ordinary, sample / 'diagnostic.ordinary'):
            subprocess.run(['python3', str(SCRIPTS / 'roundtrip.py'), str(checked), str(pilot)], check=True)
        pilot_runs.append(durations)
    (args.out / 'pilot-wall-seconds.json').write_text(json.dumps(pilot_runs) + '\n')
    spreads = [max(row[cohort] for row in pilot_runs) / min(row[cohort] for row in pilot_runs)
               for cohort in (0, 1)]
    print(f'bounded pilot wall seconds (budget only, not renderer timing): {pilot_runs}; '
          f'ordinary/diagnostic spread ratios: {spreads}', flush=True)
    if max(value for row in pilot_runs for value in row) > 30:
        raise ValueError('pilot exceeds the bounded hosted full-script budget')
    baseline = args.out / 'ordinary.raw'
    traced = args.out / 'diagnostic.raw'
    execute(args.ordinary, args.script, baseline)
    execute(args.diagnostic, args.script, traced)
    final_args = argparse.Namespace(ordinary=baseline, diagnostic=traced,
        script=args.script, inventory=args.inventory, manifest=args.manifest, out=args.out)
    summarize(final_args, canonical=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('action', choices=('run', 'summarize'))
    parser.add_argument('--ordinary', type=Path, required=True)
    parser.add_argument('--diagnostic', type=Path, required=True)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'run':
        run(arguments)
    else:
        summarize(arguments)
