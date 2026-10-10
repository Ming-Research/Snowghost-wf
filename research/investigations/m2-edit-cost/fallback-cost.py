"""Temporary Q141 experiment, called by fallback-cost.yml; remove before ready.

Native X5 timings retain every row. Callgrind dumps isolate each structural
edit, including style, and exclude startup and the full-layout comparator.
The existing X5 parser owns the timing protocol; no private timing driver.
"""
import argparse
import csv
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import time

ROOT = Path.cwd()
OUT = ROOT / 'build/fallback-cost'
SCRIPTS = ROOT / 'build/x5/scripts'
spec = importlib.util.spec_from_file_location('inctime', ROOT / 'research/investigations/incremental-layout/scripts/inctime.py')
inctime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inctime)


def args_for(page):
    base = 'build/research/concurrency/'
    result = [base + page + '.html', 'renderer/style/ua.css']
    if page == 'ecma262':
        result += ['assets/css/ecmarkup.css=' + base + 'ecma262-ecmarkup.css', 'assets/css/print.css=' + base + 'ecma262-print.css']
    if page == 'apollo11':
        result += ['wikibase.client.init&only=styles&skin=vector-2022=' + base + 'apollo11-modules.css', 'modules=site.styles&only=styles&skin=vector-2022=' + base + 'apollo11-site.css']
    return result


def driver(name, mode):
    return str(ROOT / f'build/drivers/driver-{name}/layout_oracle_{mode}')


def run(command, destination, timeout=180):
    started = time.monotonic()
    with destination.open('w') as stdout, destination.with_suffix('.stderr').open('w') as stderr:
        subprocess.run(command, stdout=stdout, stderr=stderr, check=True, timeout=timeout,
                       env=dict(os.environ, WF_WORKERS='4'))
    elapsed = time.monotonic() - started
    destination.with_suffix('.seconds').write_text(f'{elapsed:.6f}\n')
    return elapsed


def native(names, controls, rounds):
    rows = []
    pages = ('ecma262', 'html5', 'apollo11') if controls else ('apollo11',)
    kinds = ('word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block') if controls else ('block',)
    # Two smallest useful forward/inverse samples before selecting the batch.
    for page in pages:
        for kind in kinds:
            source = SCRIPTS / f'{page}-{kind}.edits'
            lines = source.read_text().splitlines(keepends=True)
            header = [line for line in lines if line.startswith('S ')]
            edits = [line for line in lines if line[:2] not in ('S ', 'P ', 'V ') and line.strip()]
            sample = OUT / f'{page}-{kind}-sample.edits'
            sample.write_text(''.join(header + edits[:2]))
            for mode in ('seq', 'par'):
                for name in (names[0], names[-1]):
                    wall = []
                    for repeat in range(2):
                        dest = OUT / f'pilot-{name}-{page}-{kind}-{mode}-{repeat}.raw'
                        wall.append(run([driver(name, mode), 'edittime', str(sample), *args_for(page)], dest))
                        inctime.read(dest, inctime.script_operations(sample))
                    print('pilot', name, page, kind, mode, wall, 'wall spread', max(wall) / min(wall), flush=True)
                    if max(wall) > 30:
                        raise ValueError('pilot exceeds the bounded batch budget')
    for round_number in range(1, rounds + 1):
        ordered = names if round_number % 2 else list(reversed(names))
        for page in pages:
            for kind in kinds:
                source = SCRIPTS / f'{page}-{kind}.edits'
                operations = inctime.script_operations(source)
                for mode in ('seq', 'par'):
                    for name in ordered:
                        dest = OUT / f'{name}-{page}-{kind}-{mode}-r{round_number}.raw'
                        seconds = run([driver(name, mode), 'edittime', str(source), *args_for(page)], dest)
                        timed, other, styled, built = inctime.read(dest, operations)
                        if other:
                            raise ValueError('nonincremental result')
                        values = []
                        for edit, data in timed.items():
                            style = styled.get(edit, [0, 0, 0, 0])
                            total = data[0] + style[3]
                            values.append(total)
                            path = built.get(edit, [])
                            local, reason = path[-2:] if len(path) == 5 else ('', '')
                            rows.append(dict(cohort=name, page=page, kind=kind, mode=mode,
                                round=round_number, edit=edit, total_us=total,
                                update_us=data[0] - style[0] - style[1],
                                delta_us=style[0], picks_us=style[1], style_us=style[3],
                                splice=local, reason=reason))
                        print('native', name, page, kind, mode, round_number, statistics.median(values), seconds, flush=True)
                        with (OUT / 'native.csv').open('w') as f:
                            writer = csv.DictWriter(f, fieldnames=rows[0])
                            writer.writeheader()
                            writer.writerows(rows)


def profile(names):
    source = SCRIPTS / 'apollo11-block.edits'
    lines = source.read_text().splitlines(keepends=True)
    header = [line for line in lines if line.startswith('S ')]
    edits = [line for line in lines if line[:2] not in ('S ', 'P ', 'V ') and line.strip()]
    # Initial layout never enters apply_structure_edit. Zero edits is the
    # negative control for toggle collection; before/after dumps reset costs
    # and call counters for every edit in the full unchanged script.
    for name in names:
        for size, selected in (('zero', []), ('sample', edits[:2]), ('full', edits)):
            script = OUT / f'profile-{size}.edits'
            script.write_text(''.join(header + selected))
            prefix = OUT / f'profile-{name}-{size}'
            options = ['--collect-atstart=no', '--toggle-collect=wf_oracle.layout.apply_structure_edit']
            if size == 'full':
                options = ['--collect-atstart=yes', '--dump-before=wf_oracle.layout.apply_structure_edit', '--dump-after=wf_oracle.layout.apply_structure_edit']
            seconds = run(['valgrind', '--tool=callgrind', *options,
                           '--callgrind-out-file=' + str(prefix) + '.callgrind',
                           driver(name, 'seq'), 'edittime', str(script), *args_for('apollo11')],
                          Path(str(prefix) + '.raw'), timeout=300)
            print('profile', name, size, seconds, flush=True)
            if size != 'full':
                import re
                summary = int(re.search(r'^summary: (\d+)', Path(str(prefix) + '.callgrind').read_text(), re.M)[1])
                if (summary == 0) != (size == 'zero'):
                    raise ValueError(('wrong collection boundary', name, size, summary))
                if seconds > 90:
                    raise ValueError('profile pilot too long for full script')
            else:
                parts = list(OUT.glob(prefix.name + '.callgrind.*'))
                if len(parts) != 2 * len(edits):
                    raise ValueError(('missing edit dumps', len(parts), len(edits)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('native', 'profile'))
    parser.add_argument('--names', nargs='+', required=True)
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--rounds', type=int, default=3)
    opts = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if opts.action == 'native':
        native(opts.names, opts.controls, opts.rounds)
    else:
        profile(opts.names)
