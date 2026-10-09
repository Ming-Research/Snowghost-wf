"""One-use hosted reader diagnosis, called by reader-native-profile.yml.

Python supplies startup-marker capture and sample-based batch sizing that perf
alone cannot enforce. Retire this file with the workflow after its evidence.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time

root = Path('build/reader-native')
root.mkdir(parents=True, exist_ok=True)
names = ('frontier', 'frontiertwin', 'a', 'atwin')
settings = (('seq', 1), ('par', 1), ('par', 4))
source = Path('build/x5/scripts/html5-sentence.edits').read_text().splitlines(True)
setup = [line for line in source if line.startswith('S ')]
edits = [line for line in source if line.startswith(('T ', 'D '))]
pair = edits[34:36]
assert len(pair) == 2 and pair[0].startswith('T ') and pair[1].startswith('D '), pair
sample = root / 'sample.edits'
sample.write_text(''.join(setup + pair))


def command(name, mode, script):
    return [f'build/drivers/driver-{name}/layout_oracle_{mode}', 'edittime',
            str(script), 'build/research/concurrency/html5.html', 'renderer/style/ua.css']


def run(name, mode, workers, script, label, profiled=False):
    output = root / f'{name}-{mode}-{workers}-{label}'
    args = command(name, mode, script)
    if profiled:
        args = ['perf', 'record', '-e', 'cpu-clock:u', '--delay', '5000',
                '-m', '4096', '-F', '99', '--strict-freq', '--call-graph', 'dwarf,4096',
                '-o', str(output) + '.data', '--'] + args
    start = time.monotonic()
    base = first = last = None
    with Path(str(output) + '.raw').open('wb') as destination, Path(str(output) + '.err').open('wb') as err:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=err,
                                   env=dict(os.environ, WF_WORKERS=str(workers)),
                                   start_new_session=True)
        timer = threading.Timer(120, lambda: os.killpg(process.pid, signal.SIGKILL))
        timer.start()
        try:
            for line in process.stdout:
                elapsed = time.monotonic() - start
                if line.startswith(b'base hash '):
                    base = elapsed
                if line.startswith(b'edit 1 us '):
                    first = elapsed
                if re.match(rb'edit \d+ us ', line):
                    last = elapsed
                destination.write(line)
            status = process.wait()
        finally:
            timer.cancel()
    wall = time.monotonic() - start
    text = Path(str(output) + '.raw').read_text()
    values = [(int(a), int(b)) for a, b in re.findall(r'^edit (\d+) us (\d+)', text, re.M)]
    expected = 2 if script == sample else repeats * 2
    assert status == 0, (output, status)
    assert [a for a, _ in values] == list(range(1, expected + 1)), (output, len(values), expected)
    costs = sorted(b for _, b in values)
    info = dict(status=status, base_seconds=base, first_edit_seconds=first,
                last_edit_seconds=last,
                total_seconds=wall, count=len(costs), upper_median_us=costs[len(costs)//2],
                summed_edit_us=sum(costs), sample_delay_seconds=5 if profiled else 0)
    Path(str(output) + '.phase.json').write_text(json.dumps(info, indent=2) + '\n')
    print(output, info, flush=True)
    if profiled:
        def admitted(row):
            return (row['status'] == 0 and row['base_seconds'] is not None and
                    row['first_edit_seconds'] is not None and
                    0 <= row['base_seconds'] <= row['first_edit_seconds'] < 5 and
                    row['summed_edit_us'] > 10000000)
        assert admitted(info), info
        assert not admitted(dict(info, first_edit_seconds=6)), 'late startup admitted'
        assert not admitted(dict(info, base_seconds=None)), 'missing startup admitted'
        assert not admitted(dict(info, summed_edit_us=10000000)), 'short edit batch admitted'
        data = str(output) + '.data'
        for children in (False, True):
            suffix = 'callers' if children else 'self'
            with Path(str(output) + f'.{suffix}.txt').open('wb') as out, Path(str(output) + f'.{suffix}.err').open('wb') as err:
                subprocess.run(['perf', 'report', '-i', data, '--stdio', '--header',
                                '--children' if children else '--no-children',
                                '--show-nr-samples', '--show-total-period', '--percent-limit', '0.1'],
                               stdout=out, stderr=err, check=True, timeout=60)
        with Path(str(output) + '.samples.txt').open('wb') as out, Path(str(output) + '.samples.err').open('wb') as err:
            subprocess.run(['perf', 'script', '-i', data, '--show-lost-events',
                            '-F', 'comm,pid,tid,time,event,ip,sym,dso'],
                           stdout=out, stderr=err, check=True, timeout=60)
        records = Path(str(output) + '.samples.txt').read_text()
        loss_records = [line for line in records.splitlines() if re.search(r'\bPERF_RECORD_LOST(?:_SAMPLES)?\b', line)]
        warnings = Path(str(output) + '.err').read_text()
        loss_warnings = [line for line in warnings.splitlines() if 'lost' in line.lower()]
        # Preserve any reported loss; a successful collection is not an attribution verdict.
        Path(str(output) + '.loss.json').write_text(json.dumps(dict(records=loss_records, warnings=loss_warnings), indent=2) + '\n')
    return info


samples = []
for name in ('frontier', 'a'):
    for mode, workers in settings:
        for trial in (1, 2):
            samples.append(run(name, mode, workers, sample, f'sample-{trial}'))
assert max(x['total_seconds'] for x in samples) < 60, samples
costs = [x['summed_edit_us'] for x in samples]
assert min(costs) > 0, costs
repeats = min(30000, max(2, math.floor(45000000 / max(costs))))
script = root / 'repeated.edits'
script.write_text(''.join(setup + pair * repeats))
(root / 'scale.json').write_text(json.dumps(dict(pair_edit_us=costs, repeats=repeats), indent=2) + '\n')
paths = [Path('build/research/concurrency/html5.html'), Path('renderer/style/ua.css'), script]
paths += [Path(f'build/drivers/driver-{name}/layout_oracle_{mode}') for name in names for mode in ('seq', 'par')]
(root / 'inputs.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in paths))
for mode, workers in settings:
    for name in names:
        run(name, mode, workers, script, 'profile', profiled=True)
