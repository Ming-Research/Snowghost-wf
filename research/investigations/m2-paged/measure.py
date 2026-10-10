"""Hosted-only paired measurement, called by m2-paged-time.yml until adoption.

The existing stage scripts select best-of-rounds and reuse build caches; this
comparison needs independent twins, reversed interleaving, per-process RSS and
retained full-script ordinal evidence. Driver protocols remain unchanged.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path('build/m2-paged-time')
COHORTS = ('base', 'base-twin', 'candidate', 'candidate-twin')
PAGES = ('ecma262', 'html5', 'apollo11')
KINDS = ('word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sheets(page):
    pairs = {
        'ecma262': [('assets/css/ecmarkup.css', 'ecma262-ecmarkup.css'),
                    ('assets/css/print.css', 'ecma262-print.css')],
        'html5': [],
        'apollo11': [('wikibase.client.init&only=styles&skin=vector-2022', 'apollo11-modules.css'),
                     ('modules=site.styles&only=styles&skin=vector-2022', 'apollo11-site.css')],
    }
    return ['renderer/style/ua.css'] + [f'{name}={ROOT / "inputs" / filename}' for name, filename in pairs[page]]


def run(label, cohort, stage, mode, page, operation, count):
    driver = ROOT / 'drivers' / f'{cohort}-{stage}-{mode}'
    args = [str(driver), operation, str(count), str(ROOT / 'inputs' / f'{page}.html'), *sheets(page)]
    target = ROOT / os.environ['PHASE'] / label
    target.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, WF_WORKERS='4' if mode == 'par4' else '1')
    started = time.perf_counter_ns()
    with target.with_suffix('.raw').open('w') as out, target.with_suffix('.err').open('w') as err:
        completed = subprocess.run(['/usr/bin/time', '-f', '%M', '-o', str(target.with_suffix('.rss')), *args], stdout=out, stderr=err, env=env)
    elapsed = (time.perf_counter_ns() - started) / 1e9
    record = dict(label=label, cohort=cohort, stage=stage, mode=mode, page=page,
                  operation=operation, count=str(count), seconds=elapsed,
                  exit=completed.returncode, command=args,
                  peak_rss_kib=int(target.with_suffix('.rss').read_text().splitlines()[-1]))
    with (ROOT / os.environ['PHASE'] / 'processes.jsonl').open('a') as output:
        output.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    completed.check_returncode()
    return target.with_suffix('.raw'), record


def main():
    phase, repetitions = sys.argv[1], int(sys.argv[2])
    if os.environ.get('GITHUB_ACTIONS') != 'true' or phase not in ('sample', 'matrix') or repetitions < 1:
        raise ValueError('requires hosted CI, a known phase and positive repetitions')
    os.environ['PHASE'] = phase
    output = ROOT / phase
    output.mkdir(parents=True, exist_ok=True)
    machine = dict(platform=platform.platform(), cpu=subprocess.check_output(['lscpu'], text=True),
                   compiler=Path('whitefoot.pin').read_text().strip(), revision=os.environ['GITHUB_SHA'],
                   rounds=0 if phase == 'sample' else 3, repetitions=repetitions,
                   hashes={str(p): digest(p) for folder in ('drivers', 'inputs', 'scripts') for p in (ROOT / folder).glob('*') if p.is_file()})
    machine['font_hashes'] = {str(p): digest(p) for p in Path('build/fonts').rglob('*') if p.is_file()}
    for tool in ('/usr/bin/clang', 'ld.lld'):
        machine[tool] = subprocess.check_output([tool, '--version'], text=True)
    compiler_dir = Path('build/whitefoot/wf-78223721f77d')
    machine['compiler_sha256'] = digest(compiler_dir / 'whitefootc')
    machine['compiler_manifest'] = json.loads((compiler_dir / 'whitefoot-release.json').read_text())
    (output / 'machine.json').write_text(json.dumps(machine, indent=2) + '\n')
    # Existing parser validates full ordinals, successful edits and count shape.
    spec = importlib.util.spec_from_file_location('inctime', 'research/investigations/incremental-layout/scripts/inctime.py')
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    if phase == 'sample':
        for sample in range(2):
            for stage, operation in [('style', 'all'), ('layout', 'layout')]:
                run(f'small-{sample}-{stage}', 'base', stage, 'seq', 'apollo11', operation, 1)
        for kind in KINDS:
            source = ROOT / 'scripts' / f'apollo11-{kind}.edits'
            sample_script = output / f'apollo11-{kind}.edits'
            selected, edits = [], 0
            for line in source.read_bytes().splitlines(keepends=True):
                selected.append(line)
                if line[:1] in (b'T', b'D', b'C', b'K', b'B', b'J', b'X'):
                    edits += 1
                    if edits == 2:
                        break
            sample_script.write_bytes(b''.join(selected))
            for sample in range(2):
                raw, _ = run(f'small-{sample}-edit-{kind}', 'base', 'layout', 'seq', 'apollo11', 'edittime', sample_script)
                parser.read(raw, parser.script_operations(sample_script))
        return
    for page in PAGES:
        for mode in ('seq', 'par4'):
            for cohort in COHORTS:
                for stage, operation in [('style', 'all'), ('layout', 'layout')]:
                    run(f'warm-{cohort}-{page}-{mode}-{stage}', cohort, stage, mode, page, operation, 1)
            for round_id in range(1, 4):
                order = COHORTS if round_id % 2 else COHORTS[::-1]
                for stage, operation in [('style', 'all'), ('layout', 'layout')]:
                    for cohort in order:
                        prefix = f'r{round_id}-{cohort}-{page}-{mode}-{stage}'
                        run(prefix + '-zero', cohort, stage, mode, page, operation, 0)
                        run(prefix + '-full', cohort, stage, mode, page, operation, repetitions)
                for kind in KINDS:
                    script = ROOT / 'scripts' / f'{page}-{kind}.edits'
                    operations = parser.script_operations(script)
                    for cohort in order:
                        prefix = f'r{round_id}-{cohort}-{page}-{mode}-edit-{kind}'
                        raw, record = run(prefix, cohort, 'layout', mode, page, 'edittime', script)
                        timed, other, styled, built = parser.read(raw, operations)
                        if other or len(timed) != len(operations):
                            raise ValueError(f'{prefix}: missing or refused timed edits')
                        record.update(kind=kind, round=round_id, edits=timed, style=styled, structure=built)
                        with (output / 'edits.jsonl').open('a') as out:
                            out.write(json.dumps(record) + '\n')


if __name__ == '__main__':
    main()
