"""Temporary hosted experiment, called by paged-mechanism.yml's memory job.

The unchanged instruction profiler owns driver invocation/process records.
This script adds named cache/branch counters and original-prefix U scopes;
native U is the driver's timestamp interval, whereas markers omit its initial
and final clock/argument bookkeeping. Cache simulation is a fixed model, not
measured CPU misses or cycles. Remove with the workflow after archiving evidence.

Callgrind format: https://valgrind.org/docs/manual/cl-format.html
Trailing omitted counters are zero; call-edge costs are inclusive and must
not enter exclusive conservation totals.
"""
from collections import Counter, defaultdict
import csv
import json
import os
from pathlib import Path
import re
import shutil
import statistics

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path.cwd()
OUT = ROOT / 'build/paged-memory'
ARCHIVE = ROOT / 'build/m2-paged-time'
GEOMETRY = {'I1': (32768, 8, 64), 'D1': (32768, 8, 64), 'LL': (33554432, 16, 64)}
EVENTS = {'Ir', 'I1mr', 'ILmr', 'Dr', 'D1mr', 'DLmr', 'Dw', 'D1mw', 'DLmw', 'Bc', 'Bcm', 'Bi', 'Bim'}
COMBINED = {'D1_read_write_misses': ('D1mr', 'D1mw'), 'LL_read_write_misses': ('DLmr', 'DLmw')}
CACHE_ROWS = []
U_BOUNDARIES = [('before', 'wf_layout.styles_restyled'), ('after', 'wf_layout.styles_restyled'),
                ('before', 'wf_layout.update'), ('after', 'wf_layout.update')]
LAYOUT_BOUNDARIES = [('before', 'wf_layout.build_boxes'), ('after', 'wf_layout.build_boxes'),
                     ('after', 'wf_oracle.layout.pick_all'), ('after', 'wf_layout.lay_out')]


def load(name, path):
    spec = spec_from_file_location(name, ROOT / path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harness = load('instruction_harness', 'research/investigations/m2-paged/profile-mechanism.py')
harness.OUT = OUT
allocation = load('allocation', 'research/investigations/m2-paged/allocation-summary.py')


def counters(text, events):
    values = [int(value) for value in text.split()]
    if not values or len(values) > len(events) or any(value < 0 for value in values):
        raise ValueError('invalid counter vector')
    return dict(zip(events, values + [0] * (len(events) - len(values))))


def cache_profile(path):
    """Conserve every requested event, using exclusive rows only."""
    identifiers, own, calls, edges = {}, defaultdict(Counter), Counter(), defaultdict(Counter)
    events, summary, caller, callee, pending = None, None, None, None, False
    positions = 1
    def symbol(text):
        match = re.fullmatch(r'\((\d+)\)(?: (.*))?', text)
        if not match:
            return text
        index, name = match.groups()
        if name is not None:
            identifiers[index] = name
        if index not in identifiers:
            raise ValueError(('undefined function identifier', index))
        return identifiers[index]
    for line in Path(path).read_text().splitlines():
        if line.startswith('positions: '):
            positions = len(line.split()) - 1
        elif line.startswith('events: '):
            events = line.split()[1:]
            if len(events) != len(EVENTS) or set(events) != EVENTS:
                raise ValueError(('missing, repeated or unexpected cache/branch event', events))
        elif line.startswith('summary: '):
            if summary is not None or events is None:
                raise ValueError('duplicate summary or absent event header')
            summary = counters(line[9:], events)
        elif line.startswith('fn='):
            caller, pending = symbol(line[3:]), False
        elif line.startswith('cfn='):
            callee = symbol(line[4:])
        elif line.startswith('calls='):
            if caller is None or callee is None or pending:
                raise ValueError('incomplete call association')
            calls[callee] += int(line[6:].split()[0])
            pending = True
        elif line and line[0] in '*+-0123456789':
            fields = line.split()
            if events is None or caller is None or len(fields) <= positions:
                raise ValueError(('incomplete cost row', line))
            cost = counters(' '.join(fields[positions:]), events)
            if pending:
                edges[caller, callee].update(cost)
                pending = False
            else:
                own[caller].update(cost)
    total = Counter(dict.fromkeys(EVENTS, 0))
    for cost in own.values():
        total.update(cost)
    if summary is None or pending or dict(total) != summary:
        raise ValueError(('exclusive cache/branch costs do not reconcile', str(path), dict(total), summary))
    return summary, own, calls, edges


def controls():
    events = ' '.join(sorted(EVENTS))
    vector = ' '.join('21' if event == 'Ir' else '3' for event in sorted(EVENTS))
    left = ' '.join('12' if event == 'Ir' else '1' for event in sorted(EVENTS))
    right = ' '.join('9' if event == 'Ir' else '2' for event in sorted(EVENTS))
    fixture = f'positions: line\nevents: {events}\nsummary: {vector}\nfn=(1) outer\n1 {left}\ncfn=(2) child\ncalls=1 0\n* {right}\nfn=(2)\n1 {right}\n'
    directory = OUT / 'cache-controls'
    directory.mkdir(exist_ok=True)
    path = directory / 'good.callgrind'
    path.write_text(fixture)
    summary, own, calls, edges = cache_profile(path)
    if summary['Ir'] != 21 or own['outer']['Ir'] != 12 or calls['child'] != 1 or edges['outer', 'child']['Ir'] != 9:
        raise ValueError('valid fixture did not retain exclusive versus inclusive costs')
    # Missing input/event, wrong total, and missing self rows must fail.
    for label, wrong in [('event', fixture.replace('events: Bc ', 'events: ')),
                         ('total', fixture.replace('summary: ' + vector, 'summary: ' + vector.replace('21', '22'))),
                         ('row', fixture.replace('fn=(2)\n1 ' + right + '\n', 'fn=(2)\n')),
                         ('header', fixture.replace('summary: ' + vector + '\n', ''))]:
        bad = directory / (label + '.callgrind')
        bad.write_text(wrong)
        try:
            cache_profile(bad)
        except ValueError:
            continue
        raise ValueError(('accepted invalid cache evidence', label))
    # The format permits omitted trailing zero counters.
    omitted = directory / 'omitted-zero.callgrind'
    omitted.write_text(f'events: Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw Bc Bcm Bi Bim\nsummary: 1\nfn=one\n1 1\n')
    cache_profile(omitted)
    empty = directory / 'empty-zero.callgrind'
    empty.write_text(f'events: {events}\nsummary: 0\ntotals: 0\n')
    if any(cache_profile(empty)[0].values()):
        raise ValueError('empty zero-work dump acquired costs')
    left, right = Counter(dict.fromkeys(EVENTS, 0)), Counter(dict.fromkeys(EVENTS, 0))
    left.update(Ir=10, D1mr=2, D1mw=3, DLmr=4, DLmw=5)
    right.update(Ir=12, D1mr=3, D1mw=1, DLmr=6, DLmw=2)
    delta = paired_values(left, right)
    if delta['delta_Ir'] != 2 or delta['delta_D1_read_write_misses'] != -1 or delta['delta_LL_read_write_misses'] != -1:
        raise ValueError('paired named-event/combined-miss arithmetic witness failed')
    wrong = dict(delta, delta_D1_read_write_misses=0)
    try:
        conserve_pair(delta, wrong, 'synthetic corrupted combined delta')
    except ValueError:
        pass
    else:
        raise ValueError('paired conservation accepted corrupted combined misses')
    for operation in ('boxes', 'layout'):
        label = 'control-zero-' + operation
        raw = OUT / (label + '.raw')
        raw.write_text(f'{operation} elements 7 contexts 0 paragraphs 0 reps 0\n')
        validate_native(label, operation, 0)
        for contexts, paragraphs in ((1, 0), (0, 1)):
            raw.write_text(f'{operation} elements 7 contexts {contexts} paragraphs {paragraphs} reps 0\n')
            try:
                validate_native(label, operation, 0)
            except ValueError:
                continue
            raise ValueError(('zero stage control accepted work', operation))
    allocation.controls(OUT / 'allocation-controls')
    (directory / 'result.json').write_text(json.dumps({'status': 'passed', 'cases': 15}) + '\n')


def metadata():
    archived = json.loads((ARCHIVE / 'sample/machine.json').read_text())
    inventory = {str(Path('build/m2-paged-time') / folder / path.name): path
                 for folder in ('drivers', 'inputs', 'scripts')
                 for path in (ARCHIVE / folder).iterdir() if path.is_file()}
    if inventory.keys() != archived['hashes'].keys():
        raise ValueError('frozen archive inventory differs')
    for name, path in inventory.items():
        if harness.digest(path) != archived['hashes'][name]:
            raise ValueError(('frozen checksum differs', name))
    fonts = {str(p): harness.digest(p) for p in Path('build/fonts').rglob('*') if p.is_file()}
    if fonts != archived['font_hashes']:
        raise ValueError('fonts differ from the original experiment')
    result = dict(workflow_revision=os.environ['GITHUB_SHA'], archive=archived,
                  fonts=fonts, geometry=GEOMETRY, scope='sequential ecma262; fixed cache model',
                  timed_scope='original native U',
                  marker_scope='before styles_restyled through return from update; excludes edge clock/argument bookkeeping')
    (OUT / 'metadata.json').write_text(json.dumps(result, indent=2) + '\n')


def prefix(source, ordinal, name):
    selected, operations = [], 0
    for line in source.read_bytes().splitlines(keepends=True):
        selected.append(line)
        if line[:1] in (b'T', b'D', b'C', b'K', b'B', b'J', b'X'):
            operations += 1
            if operations == ordinal:
                break
    if operations != ordinal:
        raise ValueError(('missing original ordinal', ordinal))
    path = OUT / name
    path.write_bytes(b''.join(selected))
    if len(harness.inctime.script_operations(path)) != ordinal:
        raise ValueError('prefix changed the original operation count')
    return path


def select_pair(source):
    files = list((ROOT / 'build/paged-time-original').rglob('edits.jsonl'))
    if len(files) != 1:
        raise ValueError('expected one original matrix edit record')
    records = [json.loads(line) for line in files[0].read_text().splitlines()]
    base = [r for r in records if r['cohort'] == 'base' and r['page'] == 'ecma262'
            and r['mode'] == 'seq' and r['kind'] == 'fontsize']
    if len(base) != 3 or {r['round'] for r in base} != {1, 2, 3}:
        raise ValueError('missing original three-round base fontsize evidence')
    operations = harness.inctime.script_operations(source)
    if harness.digest(source) != '4def8240288a01f51276e2f68d5c2ae2e135721ac03952ad8e8d2533fbd324bb':
        raise ValueError('fontsize script differs from the original measured script')
    if len(operations) != 20 or operations != ['C', 'K'] * 10:
        raise ValueError('original script is not the recorded twenty class edits')
    for row in base:
        if set(map(int, row['edits'])) != set(range(1, 21)):
            raise ValueError('original timing evidence lacks an ordinal')
    rounds = {odd: {r['round']: r['edits'][str(odd)][0] + r['edits'][str(odd + 1)][0] for r in base}
              for odd in range(1, 21, 2)}
    scores = {odd: statistics.median(values.values()) for odd, values in rounds.items()}
    requested = os.environ.get('ORDINALS', '').strip()
    if requested:
        pair = [int(value) for value in requested.split(',')]
        if len(pair) != 2 or pair[0] not in scores or pair[1] != pair[0] + 1:
            raise ValueError('ordinals must select one original forward/inverse pair')
    else:
        odd = max(scores, key=scores.get)
        pair = [odd, odd + 1]
    selected = dict(ordinals=pair, source='original hosted matrix run 38101523274',
                    criterion='largest baseline median pair U across three original rounds',
                    override=bool(requested), pair_median_U_us=scores, pair_round_U_us=rounds,
                    original_operations=[line.decode().rstrip('\n') for line in source.read_bytes().splitlines(keepends=True) if line[:1] in (b'C', b'K')],
                    full_script_sha256=harness.digest(source), records_sha256=harness.digest(files[0]))
    selected['coverage'] = dict(
        selected_median_pair_U_us=scores[pair[0]], all_pair_medians_U_us=sum(scores.values()),
        fraction_of_summed_pair_medians=scores[pair[0]] / sum(scores.values()),
        per_round={r['round']: dict(selected_pair_U_us=rounds[pair[0]][r['round']],
            all_pairs_U_us=sum(values[r['round']] for values in rounds.values()),
            fraction=rounds[pair[0]][r['round']] / sum(values[r['round']] for values in rounds.values())) for r in base})
    (OUT / 'selection.json').write_text(json.dumps(selected, indent=2) + '\n')
    return pair


def geometry_header(path):
    text = path.read_text()
    for cache, (size, ways, line) in GEOMETRY.items():
        descriptions = re.findall(rf'^desc: {cache} cache: (.+)$', text, re.M)
        if len(descriptions) != 1 or list(map(int, re.findall(r'\d+', descriptions[0]))) != [size, line, ways]:
            raise ValueError(('cache geometry header differs from requested model', str(path), cache, descriptions))


def validate_native(label, operation, count):
    raw = OUT / (label + '.raw')
    if operation == 'edittime':
        timed, other, styled, built = harness.inctime.read(raw, harness.inctime.script_operations(count))
        if other:
            raise ValueError('original prefix refused an edit')
        (OUT / (label + '.timed.json')).write_text(json.dumps(dict(timed=timed, style=styled, structure=built), indent=2) + '\n')
        return {n: values[1:] for n, values in timed.items()}
    match = re.fullmatch(rf'{operation} elements (\d+) contexts (\d+) paragraphs (\d+) reps (\d+)\s*', raw.read_text())
    if not match or int(match[4]) != count:
        raise ValueError(('invalid stage output', label))
    if count == 0 and (int(match[2]) != 0 or int(match[3]) != 0):
        raise ValueError(('zero repetitions reported stage work', label, match.groups()))
    return match.groups()[:3]


def cache_row(label, ordinal, scope, total, own, calls, dump=None):
    functions, incoming = defaultdict(Counter), Counter()
    for symbol, cost in own.items():
        functions[harness.normalize(symbol)].update(cost)
    for symbol, count in calls.items():
        incoming[harness.normalize(symbol)] += count
    if any(sum(cost[event] for cost in functions.values()) != total[event] for event in EVENTS):
        raise ValueError('normalized exclusive functions do not conserve phase events')
    filename = f'{label}-ordinal-{ordinal}-{scope}.functions.csv'
    with (OUT / filename).open('w') as output:
        writer = csv.DictWriter(output, fieldnames=['function', 'incoming_calls', *sorted(EVENTS)])
        writer.writeheader()
        for symbol in sorted(functions):
            writer.writerow(dict(function=symbol, incoming_calls=incoming[symbol],
                                 **{event: functions[symbol][event] for event in EVENTS}))
    row = dict(label=label, original_ordinal=ordinal, scope=scope, counters=dict(total),
               dump=dump, functions=filename, geometry=GEOMETRY)
    with (OUT / 'cache-phases.jsonl').open('a') as output:
        output.write(json.dumps(row) + '\n')
    CACHE_ROWS.append((row, functions))


def extended_events(values):
    return {**{event: values[event] for event in EVENTS},
            **{name: sum(values[event] for event in parts) for name, parts in COMBINED.items()}}


def paired_values(left, right):
    left, right = extended_events(left), extended_events(right)
    return {f'{side}_{event}': value for event in left
            for side, value in [('base', left[event]), ('candidate', right[event]), ('delta', right[event] - left[event])]}


def conserve_pair(expected, observed, context):
    if dict(observed) != expected:
        raise ValueError(('paired function/phase conservation failed', context))


def cache_deltas(selected):
    """Pair only completed production phases; preserve unavailable cells."""
    groups = defaultdict(dict)
    for scope in ('box_construction', 'font_picks_and_bookkeeping', 'preparation_and_layout'):
        groups['layout', 1, scope] = {}
    for ordinal in selected:
        for scope in ('marking', 'font_picks_and_bookkeeping', 'update', 'substantive_U_sum_of_three_disjoint_parts'):
            groups['edittime', ordinal, scope] = {}
    for row, functions in CACHE_ROWS:
        match = re.fullmatch(r'cache-(base|candidate)-(layout|edittime)', row['label'])
        if match:
            cohort, operation = match.groups()
            groups[operation, row['original_ordinal'], row['scope']][cohort] = (row, functions)
    events = sorted(EVENTS | COMBINED.keys())
    columns = ['operation', 'original_ordinal', 'scope']
    metrics = [f'{side}_{event}' for event in events for side in ('base', 'candidate', 'delta')]
    statuses = []
    with (OUT / 'cache-phase-deltas.csv').open('w') as phases, (OUT / 'cache-function-deltas.csv').open('w') as functions:
        phase_writer = csv.DictWriter(phases, fieldnames=columns + metrics)
        function_writer = csv.DictWriter(functions, fieldnames=columns + ['function'] + metrics)
        phase_writer.writeheader()
        function_writer.writeheader()
        for key, cohorts in sorted(groups.items()):
            context = dict(zip(columns, key))
            if cohorts.keys() != {'base', 'candidate'}:
                statuses.append(dict(**context, status='unavailable: incomplete paired production profiles'))
                continue
            base, base_functions = cohorts['base']
            candidate, candidate_functions = cohorts['candidate']
            expected = paired_values(base['counters'], candidate['counters'])
            observed = Counter(dict.fromkeys(metrics, 0))
            for symbol in sorted(base_functions.keys() | candidate_functions.keys()):
                cost = paired_values(base_functions.get(symbol, Counter()), candidate_functions.get(symbol, Counter()))
                observed.update(cost)
                function_writer.writerow(dict(**context, function=symbol, **cost))
            conserve_pair(expected, observed, context)
            phase_writer.writerow(dict(**context, **expected))
            statuses.append(dict(**context, status='paired; every named event conserved'))
    (OUT / 'cache-deltas-status.json').write_text(json.dumps(dict(cells=statuses,
        warning='aggregate U overlaps its component rows; semantic function renames remain separate; dynamic deltas are not causal timing shares'), indent=2) + '\n')


def cache_run(label, cohort, operation, count, selected=None, zero=False):
    boundaries = U_BOUNDARIES if operation == 'edittime' else LAYOUT_BOUNDARIES
    options = ['--cache-sim=yes', '--branch-sim=yes'] + [f'--{cache}={",".join(map(str, shape))}' for cache, shape in GEOMETRY.items()]
    if zero:
        options += ['--collect-atstart=no', '--toggle-collect=wf_layout.styles_restyled']
    else:
        options += ['--collect-atstart=yes'] + [f'--dump-{direction}={marker}' for direction, marker in boundaries]
    result = harness.run(label, ['valgrind', '--tool=callgrind', *options,
        '--callgrind-out-file=' + str(OUT / (label + '.callgrind')),
        *harness.command(cohort, operation, count)], timeout=900, required=False)
    if result['exit'] != 0 or result['timeout'] or result['spawn_error']:
        return result, None
    if zero:
        harness.inctime.read(OUT / (label + '.raw'), [], checking=True)
        geometry_header(OUT / (label + '.callgrind'))
        total, _, _, _ = cache_profile(OUT / (label + '.callgrind'))
        if any(total.values()):
            raise ValueError('zero-edit cache control collected work')
        return result, {}
    counts = validate_native(label, operation, count)
    repetitions = len(counts) if operation == 'edittime' else int(count)
    parts = list(OUT.glob(label + '.callgrind.*'))
    if len(parts) != repetitions * len(boundaries):
        raise ValueError(('missing or extra cache boundary', label, len(parts)))
    regions = [(1, 'marking', ('wf_layout.styles_restyled',)),
               (2, 'font_picks_and_bookkeeping', ('wf_layout.text.extend_picks',)),
               (3, 'update', ('wf_layout.update',))] if operation == 'edittime' else [
        (1, 'box_construction', ('wf_layout.build_boxes',)),
        (2, 'font_picks_and_bookkeeping', ('wf_oracle.layout.pick_all',)),
        (3, 'preparation_and_layout', ('wf_layout.prepare_context', 'wf_layout.lay_out'))]
    for ordinal in range(1, repetitions + 1):
        subtotal = Counter(dict.fromkeys(EVENTS, 0))
        combined_own, combined_calls = defaultdict(Counter), Counter()
        for offset, boundary in enumerate(boundaries):
            path = OUT / f'{label}.callgrind.{(ordinal - 1) * len(boundaries) + offset + 1}'
            trigger = re.findall(r'^desc: Trigger: --dump-(before|after)=(.+)$', path.read_text(), re.M)
            if trigger != [boundary]:
                raise ValueError(('unexpected cache boundary', label, ordinal, trigger))
            geometry_header(path)
            cache_profile(path)  # Every part, including setup/inter-edit parts, reconciles.
        for offset, scope, required in regions:
            path = OUT / f'{label}.callgrind.{(ordinal - 1) * len(boundaries) + offset + 1}'
            total, own, calls, edges = cache_profile(path)
            symbols = {harness.normalize(symbol) for symbol in own.keys() | calls.keys()}
            if not set(required) <= symbols or total['Ir'] <= 0:
                raise ValueError(('cache scope lacks a required component', label, ordinal, required))
            if operation == 'edittime' and selected is not None and ordinal not in selected:
                continue
            subtotal.update(total)
            for symbol, cost in own.items():
                combined_own[symbol].update(cost)
            combined_calls.update(calls)
            cache_row(label, ordinal, scope, total, own, calls, path.name)
        if operation == 'edittime' and (selected is None or ordinal in selected):
            cache_row(label, ordinal, 'substantive_U_sum_of_three_disjoint_parts',
                      subtotal, combined_own, combined_calls)
    cache_profile(OUT / (label + '.callgrind'))  # Retain/reconcile the final residual too.
    return result, counts


def perf_counts(path, requested):
    observed = {}
    for line in path.read_text().splitlines() if path.exists() else []:
        fields = line.split(';')
        if len(fields) < 3 or fields[2] not in requested:
            continue
        event, value = fields[2], fields[0].strip()
        if event in observed:
            raise ValueError('duplicate perf counter')
        numeric = re.fullmatch(r'\d+(?:\.\d+)?', value)
        observed[event] = dict(status='available' if numeric else 'unavailable',
                               value=float(value) if numeric else None, raw=value)
    return {event: observed.get(event, dict(status='unavailable', value=None, raw='missing')) for event in requested}


def perf_run(prefix_script, expected_counts):
    candidates = [shutil.which('perf')] + sorted(map(str, Path('/usr/lib/linux-tools').glob('*/perf')), reverse=True)
    chosen = None
    for number, path in enumerate(dict.fromkeys(p for p in candidates if p)):
        result = harness.run(f'perf-version-{number}', [path, '--version'], timeout=30, required=False)
        if result['exit'] == 0 and not result['timeout'] and (OUT / f'perf-version-{number}.raw').read_text().strip():
            chosen = path
            break
    if chosen is None:
        (OUT / 'perf-status.json').write_text(json.dumps(dict(status='unavailable', reason='no runnable perf executable')) + '\n')
        return
    for cohort in ('base', 'candidate'):
        for operation, count in [('boxes', 1), ('layout', 1), ('edittime', prefix_script)]:
            for group, events in [('hardware', ['cycles', 'instructions', 'cache-misses', 'dTLB-load-misses', 'page-faults']),
                                  ('software', ['page-faults'])]:
                label = f'perf-{cohort}-{operation}-{group}'
                path = OUT / (label + '.perf.txt')
                result = harness.run(label, [chosen, 'stat', '--no-big-num', '-x', ';', '-o', str(path),
                    '-e', ','.join(events), '--', *harness.command(cohort, operation, count)], timeout=60, required=False)
                values = perf_counts(path, events)
                counts = None
                if result['exit'] == 0 and not result['timeout'] and not result['spawn_error']:
                    counts = validate_native(label, operation, count)
                    if counts != expected_counts[operation]:
                        raise ValueError('successful perf process work differs from native replay')
                available = result['exit'] == 0 and not result['timeout'] and all(v['status'] == 'available' for v in values.values())
                (OUT / (label + '.status.json')).write_text(json.dumps(dict(status='available' if available else 'unavailable-or-partial',
                    tool=chosen, scope='whole process including startup and prefix', events=values,
                    driver_counts=counts, process=result), indent=2) + '\n')


def dhat(label, cohort, script):
    path = OUT / (label + '.dhat.json')
    result = harness.run(label, ['valgrind', '--tool=dhat', '--mode=heap', '--num-callers=12',
        '--dhat-out-file=' + str(path), *harness.command(cohort, 'edittime', script)], timeout=900, required=False)
    if result['exit'] != 0 or result['timeout'] or result['spawn_error']:
        (OUT / (label + '.status.json')).write_text(json.dumps(dict(status='unavailable', process=result), indent=2) + '\n')
        return result, None
    counts = validate_native(label, 'edittime', script)
    summary = allocation.summarize(path, OUT / (label + '.stderr'))
    summary['scope'] = 'whole process: startup, initial layout, every original-prefix edit, and cleanup'
    (OUT / (label + '.summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
    return result, counts


def allocation_deltas():
    paths = [OUT / f'dhat-{cohort}.summary.json' for cohort in ('base', 'candidate')]
    if not all(path.exists() for path in paths):
        (OUT / 'allocation-deltas.json').write_text(json.dumps(dict(status='unavailable: incomplete paired production profiles',
            independent_peak_live_blocks=None)) + '\n')
        return
    base, candidate = [json.loads(path.read_text()) for path in paths]
    rows = []
    for scope in ('whole_process', 'whitefoot_heap_origin', 'other_or_unresolved_origin'):
        for metric in allocation.NAMES:
            rows.append(dict(scope=scope, metric=metric, base=base[scope][metric],
                candidate=candidate[scope][metric], delta=candidate[scope][metric] - base[scope][metric]))
    (OUT / 'allocation-deltas.json').write_text(json.dumps(dict(status='paired completed whole-process profiles',
        rows=rows, independent_peak_live_blocks=None,
        warning='live blocks measured at each process byte peak; no phase totals or independent block peak'), indent=2) + '\n')
    with (OUT / 'allocation-deltas.csv').open('w') as output:
        writer = csv.DictWriter(output, fieldnames=['scope', 'metric', 'base', 'candidate', 'delta'])
        writer.writeheader()
        writer.writerows(rows)


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('memory experiments run only in CI')
    OUT.mkdir(parents=True, exist_ok=True)
    controls()
    metadata()
    source = ARCHIVE / 'scripts/ecma262-fontsize.edits'
    pair = select_pair(source)  # Selection is recorded before any new measurement.
    small = prefix(source, 2, 'original-prefix-2.edits')
    selected = prefix(source, pair[-1], f'original-prefix-{pair[-1]}.edits')
    zero = OUT / 'zero.edits'
    zero.write_bytes(b''.join(line for line in source.read_bytes().splitlines(keepends=True) if line.startswith(b'S ')))
    (OUT / 'scripts.sha256').write_text('\n'.join(f'{harness.digest(path)}  {harness.file_argument(path)}' for path in (source, small, selected, zero)) + '\n')
    # Two native smallest samples before increasing native replay length.
    expected_counts = {}
    native_pilots = []
    for repeat in range(2):
        for cohort in ('base', 'candidate') if repeat == 0 else ('candidate', 'base'):
            label = f'native-pilot-{repeat}-{cohort}'
            result = harness.run(label, harness.command(cohort, 'edittime', small), timeout=30)
            native_pilots.append(dict(cohort=cohort, repeat=repeat, seconds=result['seconds']))
            counts = validate_native(label, 'edittime', small)
            previous = expected_counts.setdefault('small', counts)
            if previous != counts:
                raise ValueError('native pilot work counts differ')
    native_spreads = {cohort: max(r['seconds'] for r in native_pilots if r['cohort'] == cohort) /
                      min(r['seconds'] for r in native_pilots if r['cohort'] == cohort) for cohort in ('base', 'candidate')}
    (OUT / 'native-duration-plan.json').write_text(json.dumps(dict(pilots=native_pilots,
        spread_by_cohort=native_spreads, production_duration='unestimated; separate process cap 30s'), indent=2) + '\n')
    if max(native_spreads.values()) > 2:
        raise ValueError('native pilot spread is too large to choose the next bounded batch')
    native_samples = []
    for repeat in range(3):
        order = harness.COHORTS if repeat % 2 == 0 else harness.COHORTS[::-1]
        for operation, count in [('boxes', 0), ('boxes', 1), ('layout', 0), ('layout', 1), ('edittime', selected)]:
            for cohort in order:
                suffix = 'selected' if operation == 'edittime' else str(count)
                label = f'native-round-{repeat + 1}-{cohort}-{operation}-{suffix}'
                result = harness.run(label, harness.command(cohort, operation, count), timeout=30)
                counts = validate_native(label, operation, count)
                key = operation if count != 0 else operation + '-zero'
                previous = expected_counts.setdefault(key, counts)
                if previous != counts:
                    raise ValueError(('native work counts differ', operation, suffix))
                row = dict(round=repeat + 1, cohort=cohort, operation=operation,
                           repetitions=suffix, seconds=result['seconds'], counts=counts, process=result)
                if operation == 'edittime':
                    timed = json.loads((OUT / (label + '.timed.json')).read_text())['timed']
                    row['selected_original_U_us'] = {ordinal: timed[str(ordinal)][0] for ordinal in pair}
                    row['selected_pair_original_U_us'] = sum(row['selected_original_U_us'].values())
                native_samples.append(row)
                with (OUT / 'native-samples.jsonl').open('a') as output:
                    output.write(json.dumps(row) + '\n')
    differences = []
    for repeat in range(1, 4):
        for cohort in harness.COHORTS:
            for operation in ('boxes', 'layout'):
                rows = {r['repetitions']: r for r in native_samples
                        if r['round'] == repeat and r['cohort'] == cohort and r['operation'] == operation}
                differences.append(dict(round=repeat, cohort=cohort, operation=operation,
                    full_seconds=rows['1']['seconds'], zero_seconds=rows['0']['seconds'],
                    full_minus_zero_seconds=rows['1']['seconds'] - rows['0']['seconds']))
    (OUT / 'native-stage-differences.json').write_text(json.dumps(dict(rows=differences,
        scope='separate-process wall time difference; startup noise remains; original U is retained separately'), indent=2) + '\n')
    control, _ = cache_run('cache-zero', 'base', 'edittime', zero, zero=True)
    if control['exit'] != 0 or control['timeout']:
        raise ValueError('cache control could not complete within its budget')
    pilots = []
    for repeat in range(2):
        result, counts = cache_run(f'cache-pilot-{repeat}', 'base', 'edittime', small)
        pilots.append(result)
        if counts != expected_counts['small']:
            raise ValueError('cache pilot incomplete or work counts differ')
    duration = dict(pilot_seconds=[p['seconds'] for p in pilots],
                    spread=max(p['seconds'] for p in pilots) / min(p['seconds'] for p in pilots),
                    process_cap_seconds=900, selected_prefix_edits=pair[-1],
                    production_duration='unestimated; four separate production processes each have a 900s cap',
                    warning='startup dominates pilots; costly-prefix duration is not inferred from isolated U timings')
    (OUT / 'duration-plan.json').write_text(json.dumps(duration, indent=2) + '\n')
    if duration['spread'] > 2:
        raise ValueError('cache pilot spread is too large to choose the next bounded batch')
    for cohort in ('base', 'candidate'):
        for operation, count in [('layout', 1), ('edittime', selected)]:
            label = f'cache-{cohort}-{operation}'
            result, counts = cache_run(label, cohort, operation, count, selected=pair)
            if counts is not None and counts != expected_counts[operation]:
                raise ValueError('cache replay work differs from native replay')
    cache_deltas(pair)
    if os.environ.get('TRY_PERF', 'true') == 'true':
        perf_run(selected, expected_counts)
    else:
        (OUT / 'perf-status.json').write_text(json.dumps(dict(status='not requested')) + '\n')
    dhat_pilots = []
    for repeat in range(2):
        result, counts = dhat(f'dhat-pilot-{repeat}', 'base', small)
        dhat_pilots.append(result)
        if counts is not None and counts != expected_counts['small']:
            raise ValueError('allocation pilot work differs from native replay')
    completed = all(p['exit'] == 0 and not p['timeout'] and not p['spawn_error'] for p in dhat_pilots)
    spread = max(p['seconds'] for p in dhat_pilots) / min(p['seconds'] for p in dhat_pilots) if completed else None
    (OUT / 'dhat-duration-plan.json').write_text(json.dumps(dict(pilots=dhat_pilots, spread=spread,
        process_cap_seconds=900, production_duration='unestimated; two separate production processes each cap at 900s',
        production_status='permitted bounded batch' if completed and spread <= 2 else 'deferred: incomplete or unstable pilots'), indent=2) + '\n')
    if completed and spread <= 2:
        for cohort in ('base', 'candidate'):
            result, counts = dhat('dhat-' + cohort, cohort, selected)
            if counts is not None and counts != expected_counts['edittime']:
                raise ValueError('allocation replay work differs from native replay')
    allocation_deltas()


if __name__ == '__main__':
    main()
