"""Temporary hosted-CI mechanism profile, wired to paged-mechanism.yml.

Reuse the frozen independent timing drivers and inputs. Retain every duration,
exit status, native timing row and Callgrind dump. Callgrind counts instructions,
not cycles; optional perf counts include process setup and comparators. Remove
with the workflow after evidence is archived, before the adoption is ready.
"""
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path.cwd()
ARCHIVE = ROOT / 'build/m2-paged-time'
OUT = ROOT / 'build/paged-mechanism'
COHORTS = ('base', 'base-twin', 'candidate', 'candidate-twin')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inctime = load('inctime', 'research/investigations/incremental-layout/scripts/inctime.py')
accounting = load('accounting', 'research/investigations/m2-edit-cost/fallback-cost.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def driver(cohort):
    return str(ARCHIVE / 'drivers' / f'{cohort}-layout-seq')


def command(cohort, operation, count):
    inputs = ARCHIVE / 'inputs'
    return [driver(cohort), operation, str(count), str(inputs / 'ecma262.html'),
            'renderer/style/ua.css',
            'assets/css/ecmarkup.css=' + str(inputs / 'ecma262-ecmarkup.css'),
            'assets/css/print.css=' + str(inputs / 'ecma262-print.css')]


def run(label, args, timeout=180, required=True):
    started = time.monotonic()
    status, expired = None, False
    with (OUT / (label + '.raw')).open('w') as stdout, (OUT / (label + '.stderr')).open('w') as stderr:
        try:
            status = subprocess.run(args, stdout=stdout, stderr=stderr,
                                    env=dict(os.environ, WF_WORKERS='1'), timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            expired = True
    seconds = time.monotonic() - started
    record = dict(label=label, command=args, seconds=seconds, exit=status, timeout=expired)
    with (OUT / 'processes.jsonl').open('a') as output:
        output.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    if required and (expired or status != 0):
        raise RuntimeError(('failed process', record))
    return record


def layout_counts(raw, count):
    match = re.fullmatch(r'layout elements (\d+) contexts (\d+) paragraphs (\d+) reps (\d+)\s*', raw.read_text())
    if not match or int(match[4]) != count:
        raise ValueError(('unexpected full-layout protocol', str(raw), raw.read_text()))
    if count == 0 and (int(match[2]) != 0 or int(match[3]) != 0):
        raise ValueError(('zero repetitions reported layout work', str(raw), match.groups()))
    return match.groups()[:3]


def native(label, cohort, operation, count):
    result = run(label, command(cohort, operation, count))
    raw = OUT / (label + '.raw')
    if operation == 'edittime':
        operations = inctime.script_operations(count)
        timed, other, styled, built = inctime.read(raw, operations)
        if other or len(timed) != len(operations):
            raise ValueError(('refused or missing edits', label))
        evidence = dict(label=label, timed=timed, style=styled, structure=built)
        with (OUT / 'native-edits.jsonl').open('a') as output:
            output.write(json.dumps(evidence) + '\n')
        # Counts must agree for each corresponding edit in both storage forms.
        return result, {i: data[1:] for i, data in timed.items()}
    return result, layout_counts(raw, count)


def normalize(symbol):
    return re.sub(r"(?:\.body\.llvm\.[0-9]+|'[0-9]+)+$", '',
                  re.sub(r'\$instance\$[0-9a-f]+', '<all>', symbol))


def profile(label, cohort, operation, count, expected, zero=False):
    markers = ['wf_layout.update'] if operation == 'edittime' else [
        'wf_layout.build_boxes', 'wf_oracle.layout.pick_all',
        'wf_layout.prepare_text', 'wf_layout.lay_out']
    if zero:
        options = ['--collect-atstart=no'] + ['--toggle-collect=' + marker for marker in markers]
    else:
        options = ['--collect-atstart=yes']
        for marker in markers:
            options += ['--dump-before=' + marker, '--dump-after=' + marker]
    prefix = OUT / label
    result = run(label, ['valgrind', '--tool=callgrind', *options,
                         '--callgrind-out-file=' + str(prefix) + '.callgrind',
                         *command(cohort, operation, count)], timeout=180 if expected <= 2 else 900)
    if operation == 'edittime' and not zero:
        timed, other, _, _ = inctime.read(OUT / (label + '.raw'), inctime.script_operations(count))
        if other or len(timed) != expected:
            raise ValueError(('profile edit protocol', label))
    if zero:
        if operation == 'layout':
            layout_counts(OUT / (label + '.raw'), count)
        else:
            inctime.read(OUT / (label + '.raw'), [], checking=True)
        total, _, _, _ = accounting.callgrind(str(prefix) + '.callgrind')
        if total != 0:
            raise ValueError(('startup entered negative control', label, total))
        return result
    parts = list(OUT.glob(label + '.callgrind.*'))
    if len(parts) != 2 * expected * len(markers):
        raise ValueError(('missing phase boundary, symbol may have been inlined', label, len(parts), expected, markers))
    rows, attribution = [], {}
    for ordinal in range(expected):
        for phase, marker in enumerate(markers):
            part = 2 * (ordinal * len(markers) + phase + 1)
            path = OUT / f'{label}.callgrind.{part}'
            total, own, calls, edges = accounting.callgrind(path)
            if total <= 0 or not any(normalize(symbol) == marker for symbol in own.keys() | calls.keys()):
                raise ValueError(('empty or unexpected measured phase', label, part, marker))
            rows.append(dict(label=label, ordinal=ordinal + 1, phase=marker,
                             instructions=total, dump=path.name))
            for symbol in own.keys() | calls.keys():
                key = marker, normalize(symbol)
                item = attribution.setdefault(key, dict(self_instructions=0, incoming_calls=0))
                item['self_instructions'] += own[symbol]
                item['incoming_calls'] += calls[symbol]
            annotation = str(path) + '.annotation.txt'
            with open(annotation, 'w') as output:
                subprocess.run(['callgrind_annotate', '--inclusive=no', '--auto=no', '--threshold=99', str(path)],
                               stdout=output, check=True)
    with (OUT / 'phases.jsonl').open('a') as output:
        for row in rows:
            output.write(json.dumps(row) + '\n')
    with (OUT / (label + '.functions.csv')).open('w') as output:
        fields = ['phase', 'function', 'self_instructions', 'incoming_calls']
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for (phase, function), costs in sorted(attribution.items()):
            writer.writerow(dict(phase=phase, function=function, **costs))
    return result


def perf(label, args, events):
    # Availability is recorded, never interpreted as a zero counter. Even a
    # successful stat counts the whole process, not the isolated layout phase.
    output = OUT / (label + '.perf.csv')
    result = run(label, ['perf', 'stat', '-x,', '-o', str(output), '-e', events, '--', *args], required=False)
    content = output.read_text() if output.exists() else ''
    unavailable = result['exit'] != 0 or result['timeout'] or '<not supported>' in content or '<not counted>' in content
    (OUT / (label + '.perf-status.json')).write_text(json.dumps(dict(
        status='unavailable-or-partial' if unavailable else 'available',
        scope='whole process, includes startup and full comparator', **result), indent=2) + '\n')


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('this investigation runs only in CI')
    OUT.mkdir(parents=True, exist_ok=True)
    machine = json.loads((ARCHIVE / 'sample/machine.json').read_text())
    # These are the inputs/checksums retained by the original frozen sample.
    inventory = {}
    for folder in ('drivers', 'inputs', 'scripts'):
        for path in (ARCHIVE / folder).iterdir():
            if path.is_file():
                key = str(Path('build/m2-paged-time') / folder / path.name)
                inventory[key] = path
    expected = machine['hashes']
    if inventory.keys() != expected.keys():
        raise ValueError(('archive inventory differs',
                          'missing', sorted(expected.keys() - inventory.keys()),
                          'unexpected', sorted(inventory.keys() - expected.keys())))
    for key, path in inventory.items():
        if expected[key] != digest(path):
            raise ValueError(('archive checksum differs', key))
    compiler = ROOT / 'build/whitefoot/wf-78223721f77d/whitefootc'
    if machine['compiler_sha256'] != digest(compiler):
        raise ValueError('compiler differs from frozen sample')
    fonts = {str(p): digest(p) for p in Path('build/fonts').rglob('*') if p.is_file()}
    if fonts != machine['font_hashes']:
        raise ValueError('fonts differ from frozen sample')
    (OUT / 'archive-machine.json').write_text(json.dumps(machine, indent=2) + '\n')
    (OUT / 'current-checksums.json').write_text(json.dumps(dict(fonts=fonts,
        workflow_revision=os.environ['GITHUB_SHA'], compiler_sha256=digest(compiler)), indent=2) + '\n')
    source = ARCHIVE / 'scripts/ecma262-fontsize.edits'
    lines = source.read_text().splitlines(keepends=True)
    header = [line for line in lines if line.startswith('S ')]
    edits = [line for line in lines if line.strip() and line[:2] not in ('S ', 'P ', 'V ')]
    sample = OUT / 'fontsize-two.edits'
    zero = OUT / 'fontsize-zero.edits'
    sample.write_text(''.join(header + edits[:2]))
    zero.write_text(''.join(header))
    if len(inctime.script_operations(sample)) != 2:
        raise ValueError('pilot does not contain the first forward/inverse pair')
    (OUT / 'scripts.sha256').write_text('\n'.join(f'{digest(p)}  {p}' for p in (source, sample, zero)) + '\n')
    counts = {}
    # Independent twins remain a native noise control; profiling twins adds
    # little attribution evidence, so only the two original binaries are profiled.
    for repeat in range(2):
        order = COHORTS if repeat == 0 else COHORTS[::-1]
        for cohort in order:
            for operation, count in [('layout', 1), ('edittime', sample)]:
                result, observed = native(f'pilot-{repeat}-{cohort}-{operation}', cohort, operation, count)
                if result['seconds'] > 30:
                    raise ValueError('native pilot exceeds bounded budget')
                previous = counts.setdefault(operation, observed)
                if previous != observed:
                    raise ValueError(('work counts differ', operation, cohort, previous, observed))
    for cohort in ('base', 'candidate'):
        profile('zero-' + cohort, cohort, 'edittime', zero, 0, zero=True)
        profile('zero-layout-' + cohort, cohort, 'layout', 0, 0, zero=True)
    pilots = []
    for repeat in range(2):
        for cohort in (('base', 'candidate') if repeat == 0 else ('candidate', 'base')):
            pilots.append(profile(f'profile-pilot-{repeat}-{cohort}-fontsize', cohort, 'edittime', sample, 2))
            profile(f'profile-pilot-{repeat}-{cohort}-layout', cohort, 'layout', 1, 1)
    spread = max(p['seconds'] for p in pilots) / min(p['seconds'] for p in pilots)
    # Deliberately conservative: initial setup is charged per two edits. A full
    # script exceeding this cap requires the primary agent to choose a CI batch.
    estimate = max(p['seconds'] for p in pilots) * len(edits) / 2
    selection = dict(edits=len(edits), pilot_spread=spread,
                     per_full_process_estimate_seconds=estimate, budget_seconds=900,
                     full_requested=os.environ.get('FULL_PROFILE') == 'true')
    (OUT / 'scale-selection.json').write_text(json.dumps(selection, indent=2) + '\n')
    if selection['full_requested']:
        if estimate > 900 or spread > 2:
            raise ValueError(('full profile needs a smaller chosen CI batch', selection))
        full_counts = None
        for cohort in ('base', 'candidate'):
            _, observed = native('full-native-' + cohort, cohort, 'edittime', source)
            if full_counts is not None and observed != full_counts:
                raise ValueError('complete script work counts differ')
            full_counts = observed
            profile('full-profile-' + cohort, cohort, 'edittime', source, len(edits))
    if os.environ.get('TRY_PERF') == 'true':
        for cohort in ('base', 'candidate'):
            for group, events in [('hardware', 'cycles,instructions,branches,branch-misses,cache-references,cache-misses'),
                                  ('software', 'page-faults,context-switches')]:
                perf(f'perf-{cohort}-layout-{group}', command(cohort, 'layout', 1), events)
                perf(f'perf-{cohort}-fontsize-{group}', command(cohort, 'edittime', source if selection['full_requested'] else sample), events)


if __name__ == '__main__':
    main()
