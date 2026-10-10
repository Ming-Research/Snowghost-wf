"""Temporary hosted fallback phase experiment; fallback-cost.yml is its caller.

Only private CI worktrees receive clock instrumentation. Canonical native
acceptance uses the unmodified drivers. Remove with the temporary workflow.
"""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('cost', HERE / 'fallback-cost.py')
cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cost)


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(('instrumentation anchor is not unique', old))
    return text.replace(old, new, 1)


def patch(tree):
    path = tree / 'renderer/oracle/layout/edit.wf'
    source = path.read_text()
    start = source.index('fn apply_structure_edit(')
    stop = source.index('\nfn full_structure_edit(', start)
    body = source[start:stop]
    body = once(body, '  let started = now(clock: clock);',
                '  let reconstruction_ns = 0_u64;\n  let started = now(clock: clock);')
    pattern = r'(?m)^( +)let (rebuilt|marked) = structure_changed\(([^\n]+)\);$'
    matches = list(re.finditer(pattern, body))
    if len(matches) != 1:
        raise ValueError('expected one reconstruction call in structural edit')
    match = matches[0]
    indent, name, arguments = match.groups()
    replacement = (f'{indent}let rebuild_started = fallback_stamp_flags(clock: clock, witness: &changed);\n'
        f'{indent}let {name} = fallback_rebuild_after(started: rebuild_started, {arguments});\n'
        f'{indent}let rebuild_finished = stamp(clock: clock, witness: &kept^.layout);\n'
        f'{indent}set reconstruction_ns = nanoseconds_from(earlier: rebuild_started, later: rebuild_finished);')
    body = body[:match.start()] + replacement + body[match.end():]
    body = once(body, '  return Ok<StyleUpdate, u8>(value: updated);',
        '  put_fallback_phase(buffer: report, kind: 0_u64, number: number, value: reconstruction_ns);\n'
        '  return Ok<StyleUpdate, u8>(value: updated);')
    source = source[:start] + body + source[stop:]
    start = source.index('fn finish_style_edit(')
    stop = source.index('\nfn ', start + 3)
    body = source[start:stop]
    body = once(body, '  match update(layout:',
                '  match fallback_update_after(started: after_picks, layout:')
    anchor = '  let elapsed = nanoseconds_from(earlier: started, later: finished);'
    body = once(body, anchor, anchor + '\n'
        '  let phase_layout_ns = nanoseconds_from(earlier: after_picks, later: finished);\n'
        '  let phase_total_ns = elapsed +sat style_ns;\n'
        '  put_fallback_phase(buffer: report, kind: 1_u64, number: number, value: phase_layout_ns);\n'
        '  put_fallback_phase(buffer: report, kind: 2_u64, number: number, value: phase_total_ns);')
    source = source[:start] + body + source[stop:]
    source += '''
const fallback_phase_label: Array<u8, 11> = "q141_phase ";

fn put_fallback_phase(buffer: &Box<Slots<u8>>, kind: u64, number: u64, value: u64) -> result: unit writes(buffer) {
  put_text(buffer: buffer, text: &fallback_phase_label[0_u64..fallback_phase_label.len]);
  put_decimal(buffer: buffer, value: kind);
  put_byte(buffer: buffer, value: 32_u8);
  put_decimal(buffer: buffer, value: number);
  put_byte(buffer: buffer, value: 32_u8);
  put_decimal(buffer: buffer, value: value);
  put_byte(buffer: buffer, value: 10_u8);
  return unit;
}

fn fallback_rebuild_after(started: Instant, layout: &Layout, document: &Document, old: &Styles, new: &Styles, traversal: &Traversal, atoms: &AtomTable, changed: &[Bool], parent: NodeId) -> result: Result<unit, LayoutError> reads(document), reads(old), reads(new), reads(traversal), reads(atoms), reads(changed), writes(layout) {
  doc "Anchors reconstruction after its clock argument, following the existing oracle timer dependency pattern.";
  let rebuilt = structure_changed(layout: layout, document: document, old: old, new: new, traversal: traversal, atoms: atoms, changed: changed, parent: parent);
  return rebuilt;
}

fn fallback_stamp_flags(clock: &Clock, witness: &Box<Array<Bool>>) -> result: Instant reads(witness), writes(clock) {
  doc "Reads the reconstruction start only after dense flag construction has returned its owning box.";
  let held = witness^.inner.len;
  let made = now(clock: clock);
  return made;
}

fn fallback_update_after(started: Instant, layout: &Layout, document: &Document, styles: &Styles, fonts: &FontSet, picks: &FontPicks) -> result: Result<unit, LayoutError> reads(document), reads(styles), reads(fonts), reads(picks), writes(layout) {
  doc "Anchors layout after its starting clock reading without changing the layout implementation.";
  let updated = update(layout: layout, document: document, styles: styles, fonts: fonts, picks: picks);
  return updated;
}
'''
    path.write_text(source)


def decode(text, edits, required):
    phases, ordinary = {}, []
    for line in text.splitlines(keepends=True):
        if not line.startswith('q141_phase '):
            ordinary.append(line)
            continue
        match = re.fullmatch(r'q141_phase ([012]) (\d+) (\d+)\n', line)
        if not match:
            raise ValueError('malformed phase record')
        kind, edit, amount = map(int, match.groups())
        if not 1 <= edit <= edits or (edit, kind) in phases:
            raise ValueError('duplicate or unexpected phase record')
        phases[edit, kind] = amount
    if len(phases) != 3 * edits:
        raise ValueError('missing phase record')
    result = {}
    for edit in range(1, edits + 1):
        rebuild, layout, total = (phases[edit, kind] for kind in range(3))
        if layout <= 0 or total < rebuild + layout or (edit in required and rebuild <= 0):
            raise ValueError('invalid phase decomposition')
        result[edit] = dict(reconstruction_ns=rebuild, layout_ns=layout,
                            bookkeeping_ns=total-rebuild-layout, total_ns=total)
    return ''.join(ordinary), result


def reconcile(phases, timed, styled):
    for edit, row in phases.items():
        delta, picks, _, style = styled[edit]
        elapsed = timed[edit][0]
        # Independent microsecond truncation accounts for at most one unit
        # in a sum of two intervals, or two units in a three-way difference.
        if row['total_ns']//1000 - elapsed - style not in (0, 1):
            raise ValueError('phase total differs from ordinary edit timing')
        if elapsed - delta - picks - row['layout_ns']//1000 not in (0, 1, 2):
            raise ValueError('phase layout differs from ordinary edit timing')
        if row['reconstruction_ns']//1000 > delta:
            raise ValueError('reconstruction exceeds its containing delta interval')


def require_admissions(built, expected):
    for edit, path in expected.items():
        if tuple(built[edit][-2:]) != path:
            raise ValueError(('changed phase admission', edit))


def native(names, rounds):
    source = cost.SCRIPTS / 'apollo11-block.edits'
    operations = cost.inctime.script_operations(source)
    inventory = json.loads((cost.ROOT / 'tests/layout/fixtures/apollo11/block-paths.json').read_text())['paths']
    paths = {n: (splice, reason) for n, splice, reason in inventory}
    ids = {n for n, splice, reason in inventory if not splice}
    lines = source.read_text().splitlines(keepends=True)
    sample = cost.OUT / 'phase-sample.edits'
    sample.write_text(''.join([line for line in lines if line.startswith('S ')] +
        [line for line in lines if line[:2] not in ('S ', 'P ', 'V ') and line.strip()][:2]))
    rows = []
    for mode in ('seq', 'par'):
        for name in (names[0], names[-1]):
            spread = []
            for repeat in range(2):
                destination = cost.OUT / f'phase-pilot-{name}-{mode}-{repeat}.raw'
                spread.append(cost.run([cost.driver(name, mode), 'edittime', str(sample.relative_to(cost.ROOT)), *cost.args_for('apollo11')], destination))
                clean, phases = decode(destination.read_text(), 2, {1, 2})
                filtered = destination.with_suffix('.ordinary')
                filtered.write_text(clean)
                timed, other, styled, built = cost.inctime.read(filtered, operations[:2])
                if other:
                    raise ValueError('nonincremental phase pilot')
                reconcile(phases, timed, styled)
                if name not in ('main', 'maintwin'):
                    require_admissions(built, {n: paths[n] for n in (1, 2)})
            print('phase pilot', name, mode, spread, 'spread', max(spread)/min(spread), flush=True)
            if max(spread) > 30:
                raise ValueError('phase pilot exceeds the bounded batch budget')
    for number in range(1, rounds + 1):
        ordered = names if number % 2 else list(reversed(names))
        for mode in ('seq', 'par'):
            for name in ordered:
                destination = cost.OUT / f'phase-{name}-{mode}-r{number}.raw'
                seconds = cost.run([cost.driver(name, mode), 'edittime', str(source.relative_to(cost.ROOT)), *cost.args_for('apollo11')], destination)
                clean, phases = decode(destination.read_text(), len(operations), ids)
                filtered = destination.with_suffix('.ordinary')
                filtered.write_text(clean)
                timed, other, styled, built = cost.inctime.read(filtered, operations)
                if other:
                    raise ValueError('nonincremental phase result')
                reconcile(phases, timed, styled)
                if name not in ('main', 'maintwin'):
                    require_admissions(built, paths)
                for edit in sorted(ids):
                    rows.append(dict(cohort=name, mode=mode, round=number, edit=edit, **phases[edit]))
                print('phase native', name, mode, number, seconds, flush=True)
    with (cost.OUT / 'native-phases.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def controls():
    good = 'q141_phase 0 1 4\nq141_phase 1 1 5\nq141_phase 2 1 12\n'
    _, values = decode(good, 1, {1})
    assert values[1]['bookkeeping_ns'] == 3
    for wrong in (good.split('\n', 1)[1], good + good.splitlines(keepends=True)[0],
                  good.replace('1 12', '1 8'), good.replace('0 1 4', '0 1 0'),
                  good.replace('1 1 5', '1 1 0'), good.replace('0 1 4', '0 2 4'),
                  good.replace('phase 1', 'phase 3')):
        try:
            decode(wrong, 1, {1})
        except ValueError:
            pass
        else:
            raise AssertionError('incorrect phase evidence accepted')
    for text in ('missing', 'anchor anchor'):
        try:
            once(text, 'anchor', 'replacement')
        except ValueError:
            pass
        else:
            raise AssertionError('ambiguous source patch accepted')
    phases = {1: dict(total_ns=12900, reconstruction_ns=4000, layout_ns=5500)}
    timed, styled = {1: [10]}, {1: [4, 1, 0, 2]}
    reconcile(phases, timed, styled)
    for field, wrong in (('total_ns', 20000), ('layout_ns', 7000), ('reconstruction_ns', 5000)):
        changed = {1: dict(phases[1], **{field: wrong})}
        try:
            reconcile(changed, timed, styled)
        except ValueError:
            pass
        else:
            raise AssertionError('phase timer mismatch accepted')
    require_admissions({1: [2, 3, 4, 0, 9]}, {1: (0, 9)})
    try:
        require_admissions({1: [2, 3, 4, 1, 0]}, {1: (0, 9)})
    except ValueError:
        pass
    else:
        raise AssertionError('changed admission accepted')
    print('phase instrumentation and accounting controls: pass')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('patch', 'native', 'self-test'))
    parser.add_argument('--tree', type=Path)
    parser.add_argument('--names', nargs='+')
    parser.add_argument('--rounds', type=int, default=3)
    args = parser.parse_args()
    cost.OUT.mkdir(parents=True, exist_ok=True)
    if args.action == 'patch':
        patch(args.tree)
    elif args.action == 'native':
        native(args.names, args.rounds)
    else:
        controls()
