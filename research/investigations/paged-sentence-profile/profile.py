"""Temporary hosted Callgrind attribution of the html5 sentence slowdown.

Candidate: layout entry sequences stored in Whitefoot's Paged<T>; base: the
hand-written page tables; one compiler release for both. Remove this file and
.github/workflows/sentence-profile.yml after archiving the artifact.

Three measurements, each on the unchanged E1 html5-sentence edit script and
the unchanged edittime driver mode:

- seq-scoped: the sequential driver under --toggle-collect on one marker per
  process (the edit's text_changed+update boundary), so only the timed edit
  work is collected. A second base run (base-twin) is the noise control.
- seq-whole and par-whole: the whole process with collection from the start,
  for the full script and for a zero-edit script of the same S lines; the
  difference is the edits' cost plus their per-edit driver bookkeeping. Only
  these runs give valid call counts (under toggling, calls= is whole-process).
  The --par driver runs at WF_WORKERS=4; Callgrind serializes its threads, and
  toggling is per thread, which is why par uses the whole-process difference.

Function names are normalized: LLVM .llvm.<digits> suffixes and Callgrind's
'N recursion suffixes are dropped, and same-named local copies are summed.
"""
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

OUT = Path('build/sentence-profile')
COHORTS = ('base', 'candidate')
ACCESSORS = ('computed_of', 'font_of', 'box_of', 'text_of')
PAGED = re.compile(r'(?i)paged|place_back|slot_(read|write|links|output|store_output|cursor)|sequence_|page_|_page\b|window')
DATA = 'build/research/concurrency'


def norm(name):
    return re.sub(r"'\d+$", '', re.sub(r'\.llvm\.\d+', '', name))


def parse_callgrind(text):
    """Self Ir, inclusive call-edge Ir and calls; exclusive rows must sum to totals."""
    identifiers, own, edges, calls = {}, Counter(), Counter(), Counter()
    caller = callee = None
    pending = None
    positions = events = totals = None

    def symbol(value):
        match = re.fullmatch(r'\((\d+)\)(?: (.+))?', value)
        if not match:
            return value
        index, name = match.groups()
        if name is not None:
            identifiers[index] = name
        return identifiers[index]

    def vector(value):
        fields = value.split()
        return (list(map(int, fields)) + [0] * len(events))[events.index('Ir')]

    for line in text.splitlines():
        if line.startswith('positions: '):
            positions = len(line.split()) - 1
        elif line.startswith('events: '):
            events = line.split()[1:]
        elif line.startswith('totals: '):
            totals = vector(line[8:])
        elif line.startswith('fn='):
            caller, callee = norm(symbol(line[3:])), None
        elif line.startswith('cfn='):
            callee = norm(symbol(line[4:]))
        elif line.startswith('calls='):
            pending = int(line[6:].split()[0])
        elif line and line[0] in '*+-0123456789':
            fields = line.split()
            cost = vector(' '.join(fields[positions:]))
            if pending is None:
                own[caller] += cost
            else:
                edges[caller, callee] += cost
                calls[caller, callee] += pending
                pending = None
    if totals is None or sum(own.values()) != totals:
        raise ValueError('exclusive rows do not reconcile with the totals footer')
    return dict(total=totals, own=own, edges=edges, calls=calls)


def dry_run():
    sample = ('positions: line\nevents: Ir Dr\nfn=(1) a.llvm.123\n1 12 0\ncfn=(2) b\'2\n'
              'calls=3 2\n* 9\nfn=(2)\n2 9\ntotals: 21 0\n')
    parsed = parse_callgrind(sample)
    if parsed['total'] != 21 or parsed['own']['a'] != 12 or parsed['own']['b'] != 9 or parsed['calls']['a', 'b'] != 3:
        raise ValueError('valid sample lost self, normalization or calls')
    try:
        parse_callgrind(sample.replace('totals: 21', 'totals: 22'))
    except ValueError:
        pass
    else:
        raise ValueError('unreconciled totals accepted')


def deadline_left():
    return float(os.environ['PROFILE_DEADLINE']) - time.time()


def run(label, command, workers):
    left = deadline_left() - 30
    if left <= 0:
        raise TimeoutError('deadline reached before ' + label)
    started = time.monotonic()
    with (OUT / 'runs' / (label + '.stdout')).open('w') as stdout, (OUT / 'runs' / (label + '.stderr')).open('w') as stderr:
        try:
            status = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=left,
                                    env=dict(os.environ, WF_WORKERS=str(workers))).returncode
        except subprocess.TimeoutExpired:
            status = None
    record = dict(label=label, command=command, workers=workers, seconds=round(time.monotonic() - started, 1), exit=status)
    with (OUT / 'processes.jsonl').open('a') as output:
        output.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    if status != 0:
        raise RuntimeError('failed or timed out: ' + label)
    return record


def driver_command(cohort, mode, script):
    return [str(OUT / 'drivers' / (cohort + '-' + mode)), 'edittime', str(script), DATA + '/html5.html', 'renderer/style/ua.css']


def called_symbols(cohort, mode):
    text = (OUT / 'drivers' / (cohort + '-' + mode + '.objdump')).read_text()
    calls = Counter(norm(s) for s in re.findall(r'\bcallq?\s+[0-9a-f]+ <([^>+]+)>', text))
    jumps = Counter(norm(s) for s in re.findall(r'\bjmpq?\s+[0-9a-f]+ <([^>+]+)>', text))
    return calls, jumps


def emitted(cohort, mode):
    names = Counter()
    for line in (OUT / 'drivers' / (cohort + '-' + mode + '.nm')).read_text().splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[-2] in ('t', 'T'):
            names[norm(fields[-1])] += 1
    return names


def choose_markers():
    common = None
    for cohort in COHORTS:
        calls, _ = called_symbols(cohort, 'seq')
        names = set(emitted(cohort, 'seq')) & set(calls)
        common = names if common is None else common & names
    for stem in ('incremental_after', 'apply_incremental'):
        matches = sorted(s for s in common if re.search(r'\.' + stem + r'$', s))
        if len(matches) == 1:
            return matches
    markers = []
    for stem in ('text_changed', 'update'):
        matches = sorted(s for s in common if s == 'wf_layout.' + stem)
        if len(matches) != 1:
            raise ValueError('no common unambiguous boundary for ' + stem)
        markers.extend(matches)
    return markers


def verify(inctime, label, script, operations):
    stdout = str(OUT / 'runs' / (label + '.stdout'))
    if not operations:
        inctime.read(stdout, [], checking=True)
        return None
    timed, other, styled, built = inctime.read(stdout, operations)
    if other or styled or built or len(timed) != len(operations):
        raise ValueError(label + ': incomplete, refused or non-text edit protocol')
    return {str(k): v[1:] for k, v in sorted(timed.items())}


def callgrind(label, cohort, mode, script, operations, inctime, marker=None):
    output = OUT / 'runs' / (label + '.callgrind')
    options = ['--collect-atstart=no', '--toggle-collect=' + marker[:-1] + '?'] if marker else []
    workers = 4 if mode == 'par' else 1
    record = run(label, ['valgrind', '--tool=callgrind', *options, '--callgrind-out-file=' + str(output),
                         *driver_command(cohort, mode, script)], workers)
    counts = verify(inctime, label, script, operations)
    parsed = parse_callgrind(output.read_text())
    if marker and operations and (parsed['total'] <= 0 or marker not in parsed['own']):
        raise ValueError(label + ': scoped output lacks marker work')
    if marker and not operations and parsed['total'] != 0:
        raise ValueError(label + ': zero-edit control collected work')
    record.update(total=parsed['total'])
    return parsed, counts, record


def merge(profiles):
    merged = dict(total=0, own=Counter(), edges=Counter(), calls=Counter())
    for p in profiles:
        merged['total'] += p['total']
        for key in ('own', 'edges', 'calls'):
            merged[key].update(p[key])
    return merged


def subtract(full, zero):
    out = dict(total=full['total'] - zero['total'], own=Counter(), calls=Counter(), edges=Counter())
    for key in ('own', 'calls', 'edges'):
        for k in full[key].keys() | zero[key].keys():
            out[key][k] = full[key][k] - zero[key][k]
    return out


def incoming(profile, name):
    return sum(v for (a, b), v in profile['calls'].items() if b == name)


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers),
                      *['| ' + ' | '.join(map(str, r)) + ' |' for r in rows]]) + '\n'


def diff_rows(base, cand, top=45, with_calls=False):
    names = base['own'].keys() | cand['own'].keys()
    delta = sorted(names, key=lambda n: -abs(cand['own'][n] - base['own'][n]))[:top]
    total = cand['total'] - base['total']
    rows = []
    for n in delta:
        d = cand['own'][n] - base['own'][n]
        row = [n, 'yes' if PAGED.search(n) else '', base['own'][n], cand['own'][n], d,
               '%.1f%%' % (100 * d / total) if total else '-']
        if with_calls:
            row += [incoming(base, n), incoming(cand, n)]
        rows.append(row)
    headers = ['Function', 'Paged path?', 'Base self Ir', 'Candidate self Ir', 'Δ self Ir', 'Share of Δ total']
    if with_calls:
        headers += ['Base calls', 'Candidate calls']
    return table(headers, rows)


def serialize(profile):
    return dict(total=profile['total'], own=dict(profile['own'].most_common()),
                calls={a + ' -> ' + b: v for (a, b), v in profile['calls'].items() if v})


def accessor_rows(results):
    rows = []
    for name in ACCESSORS:
        pattern = re.compile(r'(?:^|[.:])' + name + r'(?:$|[.])')
        for cohort in COHORTS:
            for mode in ('seq', 'par'):
                symbols = sorted(s for s in emitted(cohort, mode) if pattern.search(s))
                calls, jumps = called_symbols(cohort, mode)
                static = sum(calls[s] for s in symbols)
                tails = sum(jumps[s] for s in symbols)
                scoped = results.get('seq-scoped', {}).get(cohort) if mode == 'seq' else None
                whole = results.get(mode + '-whole', {}).get(cohort)
                rows.append([name, cohort, mode, ', '.join(symbols) or 'not emitted', static, tails,
                             sum(scoped['own'][s] for s in symbols) if scoped else '-',
                             sum(whole['own'][s] for s in symbols) if whole else '-',
                             sum(incoming(whole, s) for s in symbols) if whole else '-'])
    return table(['Accessor', 'Build', 'Driver', 'Emitted symbols', 'Direct call sites', 'Tail-jump sites',
                  'Scoped self Ir (seq)', 'Edits self Ir (whole full−zero)', 'Edits calls (whole full−zero)'], rows)


def report(state):
    lines = ['# html5 sentence Callgrind attribution', '', 'Status: ' + state['status'], '',
             'Instruction counts (Ir) on a hosted runner, not 14900K time. Δ = candidate − base.', '',
             *state['notes'], '']
    results = state['results']
    if 'seq-scoped' in results:
        r = results['seq-scoped']
        lines += ['## Sequential driver, scoped to the edits (markers ' + ', '.join(state['markers']) + ')', '',
                  table(['Build', 'Total Ir'], [[c, r[c]['total']] for c in r]) , '',
                  'Base-twin noise: total Δ %d, largest per-function |Δ| %d.' % (
                      r['base-twin']['total'] - r['base']['total'],
                      max([abs(r['base-twin']['own'][n] - r['base']['own'][n]) for n in r['base']['own'].keys() | r['base-twin']['own'].keys()] or [0]))
                  if 'base-twin' in r else '', '',
                  'Edit work counts identical between builds: ' + str(state.get('counts_equal')), '',
                  diff_rows(r['base'], r['candidate']), '']
    for key, title in (('seq-whole', 'Sequential driver, whole process: full script − zero-edit script'),
                       ('par-whole', '--par driver at WF_WORKERS=4, whole process: full script − zero-edit script')):
        if key in results and all(c in results[key] for c in COHORTS):
            r = results[key]
            raw = state['raw'][key]
            lines += ['## ' + title, '',
                      table(['Run', 'Total Ir'], [[k, v] for k, v in sorted(raw.items())]), '',
                      table(['Build', 'Edits Ir (full − zero)'], [[c, r[c]['total']] for c in COHORTS]), '',
                      diff_rows(r['base'], r['candidate'], with_calls=True), '']
    if state.get('accessors'):
        lines += ['## Accessors', '', state['accessors'], '']
    (OUT / 'summary.md').write_text('\n'.join(lines))


def main():
    dry_run()
    (OUT / 'runs').mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('inctime', 'research/investigations/incremental-layout/scripts/inctime.py')
    inctime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inctime)
    script = OUT / 'scripts' / 'html5-sentence.edits'
    zero = OUT / 'scripts' / 'html5-sentence-zero.edits'
    zero.write_bytes(b''.join(l for l in script.read_bytes().splitlines(keepends=True) if l.startswith(b'S ')))
    operations = inctime.script_operations(str(script))
    state = dict(status='running', notes=['html5 sentence script: %d operations.' % len(operations)],
                 results={}, raw={}, markers=[])
    try:
        markers = choose_markers()
        state['markers'] = markers
        # Sequential, scoped to each marker; summed over disjoint marker scopes.
        scoped, counts = {}, {}
        for cohort, label in (('base', 'base'), ('candidate', 'candidate'), ('base', 'base-twin')):
            parts = []
            for index, marker in enumerate(markers):
                for z, s, ops in (('zero', zero, []), ('', script, operations)):
                    if z and label != 'base' and label != 'candidate':
                        continue
                    name = 'seq-scoped-' + label + ('-zero' if z else '') + '-m' + str(index + 1)
                    parsed, c, record = callgrind(name, cohort, 'seq', s, ops, inctime, marker)
                    if not z:
                        parts.append(parsed)
                        counts[label] = c
            scoped[label] = merge(parts)
            (OUT / ('seq-scoped-' + label + '.json')).write_text(json.dumps(serialize(scoped[label]), indent=1))
            state['results']['seq-scoped'] = scoped
            state['counts_equal'] = len({json.dumps(v) for v in counts.values()}) == 1
            report(state)
        state['notes'].append('Zero-edit scoped controls collected 0 Ir in both builds.')
        state['accessors'] = accessor_rows(state['results'])
        report(state)
        # Whole-process differences: sequential, then par at four workers.
        rounds = {'seq': 1, 'par': 2}
        for mode in ('seq', 'par'):
            key = mode + '-whole'
            raw, fulls, zeros = {}, {c: [] for c in COHORTS}, {c: [] for c in COHORTS}
            state['raw'][key] = raw
            for round_index in range(rounds[mode]):
                for cohort in COHORTS:
                    for z, s, ops in (('zero', zero, []), ('full', script, operations)):
                        name = '%s-%s-%s-r%d' % (key, cohort, z, round_index + 1)
                        parsed, c, record = callgrind(name, cohort, mode, s, ops, inctime)
                        raw[name] = parsed['total']
                        (fulls if z == 'full' else zeros)[cohort].append(parsed)
                        if c is not None and json.dumps(c) != json.dumps(counts.get('base')):
                            state['notes'].append(name + ': edit work counts differ from the sequential base run.')
                state['results'][key] = {c: subtract(fulls[c][0], zeros[c][0]) for c in COHORTS}
                for c in COHORTS:
                    (OUT / (key + '-' + c + '.json')).write_text(json.dumps(serialize(state['results'][key][c]), indent=1))
                state['accessors'] = accessor_rows(state['results'])
                report(state)
        state['status'] = 'completed'
    except Exception as problem:
        state['status'] = 'FAILED or incomplete: ' + repr(problem)
        raise
    finally:
        report(state)


if __name__ == '__main__':
    if sys.argv[1:] == ['--dry-run']:
        dry_run()
    else:
        main()
