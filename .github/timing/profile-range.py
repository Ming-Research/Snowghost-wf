"""Temporary hosted-only range reader profile; called by bisect-hosted.yml after native timing."""
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
assert len(edits) >= 36, len(edits)
sample = root / 'sample.edits'
sample.write_text(''.join(setup + edits[34:36]))
env = dict(os.environ, WF_WORKERS='4')
build_names = os.environ.get('PROFILE_BUILDS', 'frontier ranges').split()


def command(name, mode, script):
    return [f'build/drivers/driver-{name}/layout_oracle_{mode}', 'edittime',
            str(script), 'build/research/concurrency/html5.html', 'renderer/style/ua.css']


def run(name, mode, script, label, profiled=False):
    out = root / f'{name}-{mode}-{label}'
    args = command(name, mode, script)
    if profiled:
        args = ['valgrind', '--tool=callgrind', '--separate-threads=yes', '--skip-plt=no',
                '--skip-direct-rec=no', '--zero-before=wf_layout.update',
                '--dump-after=wf_layout.update',
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
        records = []
        for path in sorted(root.glob(out.name + '.callgrind*'), key=part_key):
            selected = 'Trigger: --dump-after=wf_layout.update' in path.read_text()
            if selected:
                counters = parse_counts(path)
                assert counters['summary'] > 0, path
                assert sum(value for _, value in counters['self_instructions']) == counters['summary'], path
                records.append(dict(part=path.name, **counters))
                for inclusive in ('yes', 'no'):
                    with Path(f'{path}.inclusive-{inclusive}.txt').open('wb') as stdout:
                        subprocess.run(['callgrind_annotate', f'--inclusive={inclusive}',
                                        '--threshold=100', str(path)], stdout=stdout, check=True)
            with gzip.open(str(path) + '.gz', 'wb') as packed:
                packed.write(path.read_bytes())
            path.unlink()
        assert len({row['thread'] for row in records}) == 1, ('mixed update threads', records)
        assert len(records) == len(costs), ('expected one update dump per edit', out, len(records), len(costs))
        assert sum(row['inherited_calls'] for row in records) > 0 if name != 'frontier' else True
        Path(f'{out}.counts.json').write_text(json.dumps(records, indent=2) + '\n')
    return elapsed


def part_key(path):
    content = path.read_text()
    return tuple(int(re.search(rf'^{field}: (\d+)', content, re.M)[1])
                 if re.search(rf'^{field}: (\d+)', content, re.M) else 0
                 for field in ('part', 'thread'))


def parse_counts(path):
    names, edges, selfs = {}, {}, {}
    caller = callee = ''
    edge_calls = None
    summary = 0
    thread = None
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
        elif line.startswith('thread: '):
            thread = int(line.split()[1])
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
    return dict(summary=summary, thread=thread, inherited_calls=inherited_calls,
                inherited_node_reads=sum(n for (a, b), (n, ir) in edges.items()
                                         if 'range_inherited' in a and 'slot_view' in b),
                directory_recursions=sum(n for (a, b), (n, ir) in edges.items()
                                         if 'slot_view' in a and 'slot_view' in b),
                edges=relevant, self_instructions=sorted(selfs.items(), key=lambda x: -x[1]))


# Exercise the counter decoder in CI against independent, hand-counted call edges.
probe = root / 'counter-probe.callgrind'
probe.write_text("""positions: line
events: Ir
summary: 17
fn=(1) wf_layout.range_inherited
1 7
cfn=(2) wf_layout.slot_view
calls=3 1
1 10
fn=(2)
1 10
cfn=(2)
calls=2 1
1 4
""")
expected = parse_counts(probe)
assert expected['inherited_node_reads'] == 3, expected
assert expected['directory_recursions'] == 2, expected
assert sum(value for _, value in expected['self_instructions']) == 17, expected
for source_call, missing in [('calls=3 1', 'inherited_node_reads'),
                             ('calls=2 1', 'directory_recursions')]:
    probe.write_text(probe.read_text().replace(source_call, 'calls=0 1'))
    assert parse_counts(probe)[missing] == 0, missing
probe.unlink()
print('counter decoder detects known and omitted call edges', flush=True)

# Validate the profiler boundary itself with known startup/inter-update/shutdown
# calls into the same readers, not only the decoder's input grammar.
probe_c = root / 'phase-probe.c'
probe_c.write_text(r"""
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
__attribute__((noinline)) int allocation(void) {
  unsigned char *bytes = malloc(1024);
  memset(bytes, 7, 1024);
  int value = bytes[511];
  free(bytes);
  return value;
}
__attribute__((noinline)) int slot_view(int depth) {
  return depth ? slot_view(depth - 1) + 1 : 1;
}
__attribute__((noinline)) int range_inherited(void) { return slot_view(2) + allocation() - 7; }
__attribute__((noinline)) int profile_update(int count) {
  int sum = 0;
  for (int i = 0; i < count; ++i) sum += range_inherited();
  return sum;
}
static void *worker(void *opaque) {
  volatile int sum = 0;
  for (int i = 0; i < 100; ++i) sum += range_inherited();
  sum += profile_update(2);
  for (int i = 0; i < 100; ++i) sum += range_inherited();
  sum += profile_update(5);
  for (int i = 0; i < 100; ++i) sum += range_inherited();
  *(int *)opaque = sum;
  return NULL;
}
int main(void) {
  volatile int outside = 0;
  for (int i = 0; i < 100; ++i) outside += range_inherited();
  pthread_t thread;
  int sum = 0;
  if (pthread_create(&thread, NULL, worker, &sum) != 0) return 2;
  if (pthread_join(thread, NULL) != 0) return 3;
  return sum == 921 && outside == 300 ? 0 : 1;
}
""")
probe_exe = root / 'phase-probe'
subprocess.run(['cc', '-O0', '-g', '-fno-builtin', '-pthread', str(probe_c), '-o', str(probe_exe)], check=True)
subprocess.run(['valgrind', '--tool=callgrind', '--separate-threads=yes', '--skip-plt=no', '--skip-direct-rec=no',
                '--zero-before=profile_update', '--dump-after=profile_update',
                f'--callgrind-out-file={root}/phase-probe.callgrind', str(probe_exe)], check=True)
phase_counts = []
for path in root.glob('phase-probe.callgrind*'):
    if 'Trigger: --dump-after=' in path.read_text():
        row = parse_counts(path)
        assert sum(value for _, value in row['self_instructions']) == row['summary'], (path, row)
        phase_counts.append((row['inherited_calls'], row['inherited_node_reads'], row['directory_recursions']))
assert sorted(phase_counts) == [(2, 2, 4), (5, 5, 10)], phase_counts
print('profiler excludes 400 reader calls outside the two selected updates:', phase_counts, flush=True)

# Native samples establish the workload and observed spread before profiling it.
for name in build_names:
    symbols = subprocess.check_output(['nm', '-an', command(name, 'seq', sample)[0]], text=True)
    assert any(line.split()[-1:] == ['wf_layout.update'] for line in symbols.splitlines()), 'missing exact collection boundary'
    (root / f'{name}.symbols.txt').write_text('\n'.join(
        line for line in symbols.splitlines() if any(x in line for x in ('layout.update', 'range_inherited', 'slot_view'))))
    for mode in ('seq', 'par'):
        for index in (1, 2):
            assert run(name, mode, sample, f'sample-{index}') < 60

pilot = [run(name, 'seq', sample, 'pilot', True) for name in build_names]
assert max(pilot) < 600, ('profile sample too slow for full batch', pilot)
for name in build_names:
    for mode in ('seq', 'par'):
        run(name, mode, source, 'native')
    run(name, 'seq', source, 'profile', True)
