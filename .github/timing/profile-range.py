"""Temporary hosted-only range reader profile; called by range-profile.yml."""
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import time

root = Path('build/range-profile')
source = Path('build/x5/scripts/html5-sentence.edits')
lines = source.read_text().splitlines(True)
setup = [line for line in lines if line.startswith('S ')]
edits = [line for line in lines if line.startswith(('T ', 'D ', 'C ', 'K '))]
assert len(edits) >= 2, lines[:5]
sample = root / 'sample.edits'
sample.write_text(''.join(setup + edits[:2]))
env = dict(os.environ, WF_WORKERS='4')


def command(name, mode, script):
    return [f'build/drivers/driver-{name}/layout_oracle_{mode}', 'edittime',
            str(script), 'build/research/concurrency/html5.html', 'renderer/style/ua.css']


def run(name, mode, script, label, profiled=False):
    out = root / f'{name}-{mode}-{label}'
    args = command(name, mode, script)
    if profiled:
        args = ['valgrind', '--tool=callgrind', '--collect-atstart=no',
                '--toggle-collect=wf_layout.update', '--separate-threads=no',
                f'--callgrind-out-file={out}.callgrind'] + args
    begin = time.monotonic()
    with Path(f'{out}.raw').open('wb') as stdout, Path(f'{out}.err').open('wb') as stderr:
        subprocess.run(args, stdout=stdout, stderr=stderr, env=env, check=True, timeout=900)
    elapsed = time.monotonic() - begin
    raw = Path(f'{out}.raw').read_text()
    costs = [int(v) for v in re.findall(r'^edit \d+ us (\d+)', raw, re.M)]
    assert len(costs) == (2 if script == sample else len(edits)), (out, costs)
    data = dict(seconds=elapsed, edits=len(costs), upper_median_us=sorted(costs)[len(costs)//2])
    Path(f'{out}.time.json').write_text(json.dumps(data) + '\n')
    print(out, data, flush=True)
    if profiled:
        path = Path(f'{out}.callgrind')
        for inclusive in ('yes', 'no'):
            with Path(f'{out}.inclusive-{inclusive}.txt').open('wb') as stdout:
                subprocess.run(['callgrind_annotate', f'--inclusive={inclusive}',
                                '--threshold=100', str(path)], stdout=stdout, check=True)
        counters = parse_counts(path)
        Path(f'{out}.counts.json').write_text(json.dumps(counters, indent=2) + '\n')
        assert counters['summary'] > 0, 'collection did not include layout.update'
        if name == 'ranges':
            assert counters['inherited_calls'] > 0, 'inherited reader calls were not visible'
        with gzip.open(str(path) + '.gz', 'wb') as packed:
            packed.write(path.read_bytes())
        path.unlink()
    return elapsed


def parse_counts(path):
    names, edges, selfs = {}, {}, {}
    caller = callee = ''
    edge_calls = None
    summary = 0
    positions = 1
    def name(value):
        match = re.fullmatch(r'\((\d+)\)(?: (.*))?', value)
        if match:
            key, value = match.groups()
            if value is not None:
                names[key] = value
            return names[key]
        return value
    for line in path.read_text().splitlines():
        if line.startswith('summary: '):
            summary = int(line.split()[1])
        elif line.startswith('positions: '):
            positions = len(line.split()) - 1
        elif line.startswith('fn='):
            caller = name(line[3:])
            edge_calls = None
        elif line.startswith('cfn='):
            callee = name(line[4:])
        elif line.startswith('calls='):
            edge_calls = int(line[6:].split()[0])
        elif line and line[0] in '*+-0123456789':
            parts = line.split()
            cost = int(parts[positions])
            if edge_calls is not None:
                key = (caller, callee)
                old = edges.get(key, [0, 0])
                edges[key] = [old[0] + edge_calls, old[1] + cost]
                edge_calls = None
            else:
                selfs[caller] = selfs.get(caller, 0) + cost
    relevant = [dict(caller=a, callee=b, calls=n, instructions=ir)
                for (a, b), (n, ir) in edges.items()
                if any(term in a or term in b for term in
                       ('range_inherited', 'slot_view', 'owner_inherited', 'range_expose'))]
    inherited_calls = sum(n for (a, b), (n, ir) in edges.items() if 'range_inherited' in b)
    return dict(summary=summary, inherited_calls=inherited_calls,
                inherited_node_reads=sum(n for (a, b), (n, ir) in edges.items()
                                         if 'range_inherited' in a and 'slot_view' in b),
                directory_recursions=sum(n for (a, b), (n, ir) in edges.items()
                                         if 'slot_view' in a and 'slot_view' in b),
                edges=relevant, self_instructions=sorted(selfs.items(), key=lambda x: -x[1]))


# Native samples establish the workload and observed spread before profiling it.
for name in ('frontier', 'ranges'):
    symbols = subprocess.check_output(['nm', '-an', command(name, 'seq', sample)[0]], text=True)
    assert 'wf_layout.update' in symbols, 'missing collection boundary'
    (root / f'{name}.symbols.txt').write_text('\n'.join(
        line for line in symbols.splitlines() if any(x in line for x in ('layout.update', 'range_inherited', 'slot_view'))))
    for mode in ('seq', 'par'):
        for index in (1, 2):
            assert run(name, mode, sample, f'sample-{index}') < 60

pilot = [run(name, 'seq', sample, 'pilot', True) for name in ('frontier', 'ranges')]
assert max(pilot) < 600, ('profile sample too slow for full batch', pilot)
for name in ('frontier', 'ranges'):
    for mode in ('seq', 'par'):
        run(name, mode, source, 'native')
        run(name, mode, source, 'profile', True)
