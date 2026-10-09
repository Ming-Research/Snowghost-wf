"""Hosted Q140 full-layout and peak-RSS experiment, called by q140-cost.

Uses the established zero/repetition subtraction to exclude driver setup.
Candidate dumps are captured as evidence, not compared with other cohorts:
the first-baseline repair intentionally changes geometry. Peak RSS is the
whole process, not a measurement of retained record allocation alone.
Remove this finite-experiment helper with its workflow before readiness.
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
NAMES = ('main', 'm2', 'twin', 'head')


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
            stem = args.directory / (page + '-' + mode + '-head-dump')
            invoke([driver('head'), 'dump', '1'] + arguments(page), stem)
            dump_hash = hashlib.sha256(stem.with_suffix('.stdout').read_bytes()).hexdigest()
            pilot = []
            for trial in range(2):
                samples = []
                for reps in (0, 1):
                    seconds, _ = invoke([driver('head'), 'layout', str(reps)] + arguments(page), args.directory / f'{page}-{mode}-pilot-{trial}-{reps}')
                    samples.append(seconds)
                pilot.append(samples[1] - samples[0])
            # At least a half second of layout, bounded to ten repetitions;
            # retain both pilot differences so noisy subtraction is visible.
            per_build = max(min(pilot), 0.05)
            reps = max(1, min(10, math.ceil(0.5 / per_build)))
            print(page, mode, 'pilot layout seconds', pilot, 'selected repetitions', reps, flush=True)
            for round_number in range(1, args.rounds + 1):
                order = NAMES if round_number % 2 else tuple(reversed(NAMES))
                for name in order:
                    values = []
                    for count in (0, reps):
                        stem = args.directory / f'{page}-{mode}-{name}-r{round_number}-n{count}'
                        elapsed, rss = invoke([driver(name), 'layout', str(count)] + arguments(page), stem)
                        values.append(elapsed)
                    cost = (values[1] - values[0]) / reps
                    results.append(dict(page=page, mode=mode, build=name, round=round_number, reps=reps, seconds=cost, raw_seconds=values, peak_rss_kib=rss, candidate_dump_sha256=dump_hash))
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
