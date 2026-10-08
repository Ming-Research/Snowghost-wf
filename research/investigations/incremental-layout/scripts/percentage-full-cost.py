"""Hosted full-build collection-cost experiment, called by q139-full-cost.

One zero/one-repetition pilot per page/build mode determines a bounded batch
size before alternating all candidates on the same runner. Collection-off
and collection-off twin use the same source and differ only in process order.
Full dumps must be byte identical before any timings are accepted. RSS is a
whole-process observation, not an asserted count of retained record bytes.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import time

PAGES = ('ecma262', 'html5', 'apollo11')
NAMES = tuple(name for name in ('main', 'm2', 'twin', 'control', 'controltwin', 'head') if Path('build/drivers/driver-' + name).is_dir())


def arguments(page):
    directory = 'build/research/concurrency/'
    args = [directory + page + '.html', 'renderer/style/ua.css']
    if page == 'ecma262':
        args += ['assets/css/ecmarkup.css=' + directory + 'ecma262-ecmarkup.css', 'assets/css/print.css=' + directory + 'ecma262-print.css']
    if page == 'apollo11':
        args += ['wikibase.client.init&only=styles&skin=vector-2022=' + directory + 'apollo11-modules.css', 'modules=site.styles&only=styles&skin=vector-2022=' + directory + 'apollo11-site.css']
    return args


def invoke(command, stem):
    with stem.with_suffix('.stdout').open('wb') as output:
        started = time.monotonic_ns()
        done = subprocess.run(['/usr/bin/time', '-f', '%e\t%M', '-o', str(stem.with_suffix('.resources'))] + command, stdout=output, stderr=subprocess.PIPE)
        elapsed = (time.monotonic_ns() - started) / 1e9
    stem.with_suffix('.stderr').write_bytes(done.stderr)
    stem.with_suffix('.status').write_text(str(done.returncode) + '\n')
    if done.returncode or done.stderr:
        raise RuntimeError('full-build command failed: ' + str(stem))
    rss = int(stem.with_suffix('.resources').read_text().split()[1])
    return elapsed, rss


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--rounds', type=int, default=3)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    os.environ['WF_WORKERS'] = '4'
    results = []
    for page in PAGES:
        for mode in ('seq', 'par'):
            def driver(name):
                return 'build/drivers/driver-' + name + '/layout_oracle_' + mode
            hashes = []
            for name in ('head', 'control', 'controltwin') if 'control' in NAMES else ('head',):
                stem = args.directory / (page + '-' + mode + '-' + name + '-dump')
                invoke([driver(name), 'dump', '1'] + arguments(page), stem)
                hashes.append(hashlib.sha256(stem.with_suffix('.stdout').read_bytes()).hexdigest())
            if len(set(hashes)) != 1:
                raise RuntimeError('collection-off control changed full geometry: ' + page + '/' + mode)
            pilot = []
            for reps in (0, 1):
                seconds, _ = invoke([driver('head'), 'layout', str(reps)] + arguments(page), args.directory / f'{page}-{mode}-pilot-{reps}')
                pilot.append(seconds)
            per_build = max(pilot[1] - pilot[0], 0.05)
            reps = max(1, min(10, math.ceil(0.5 / per_build)))
            print(page, mode, 'pilot seconds', pilot, 'selected repetitions', reps, flush=True)
            for round_number in range(1, args.rounds + 1):
                order = NAMES if round_number % 2 else tuple(reversed(NAMES))
                for name in order:
                    values = []
                    for count in (0, reps):
                        stem = args.directory / f'{page}-{mode}-{name}-r{round_number}-n{count}'
                        elapsed, rss = invoke([driver(name), 'layout', str(count)] + arguments(page), stem)
                        values.append(elapsed)
                    cost = (values[1] - values[0]) / reps
                    results.append(dict(page=page, mode=mode, build=name, round=round_number, reps=reps, seconds=cost, raw_seconds=values, peak_rss_kib=rss, control_reference_dump_sha256=hashes[0]))
                    print(results[-1], flush=True)
                    (args.directory / 'samples.json').write_text(json.dumps(results, indent=2) + '\n')
    table = []
    for page in PAGES:
        for mode in ('seq', 'par'):
            row = dict(page=page, mode=mode)
            for name in NAMES:
                samples = [r['seconds'] * 1000 for r in results if r['page'] == page and r['mode'] == mode and r['build'] == name]
                row[name + '_ms'] = statistics.median(samples)
                row[name + '_range_ms'] = [min(samples), max(samples)]
            table.append(row)
    (args.directory / 'table.json').write_text(json.dumps(table, indent=2) + '\n')
    print(json.dumps(table, indent=2))


if __name__ == '__main__':
    main()
