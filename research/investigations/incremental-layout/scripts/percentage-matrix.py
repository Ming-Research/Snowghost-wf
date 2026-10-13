"""Run Q139's focused fixtures with hosted drivers and the existing oracles.

The root pair must already have passed as the workflow's timed small sample.
Each fixture has independent Chromium expectations before/after insertion;
all retained edit prefixes and required paths use the established X5 checkers.
This script is wired to the permanent q139 workflow.
"""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def command(args, output=None):
    if output is None:
        subprocess.run(args, check=True)
    else:
        with output.open('w') as stream:
            subprocess.run(args, stdout=stream, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('directory', type=Path)
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('percentage_splice', HERE / 'percentage-splice.py')
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    selected = args.case or fixtures.CASES
    totals = []
    failed = []
    for name in selected:
        directory = args.directory / name
        directory.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        try:
            generate = [sys.executable, str(HERE / 'percentage-splice.py'), args.driver, str(directory), '--case', name]
            # Negative cases isolate one unchanged refusal premise. Positive
            # cases additionally exercise source restyle and record lifetime.
            if fixtures.CASES[name][2] == 0 and name != 'fixed-floats':
                generate.append('--lifetime')
            command(generate)
            raw = directory / 'edits.raw'
            command([args.driver, 'edit', str(directory / 'case.edits'), str(directory / 'case.html'), 'renderer/style/ua.css'], raw)
            command([sys.executable, str(HERE / 'inctime.py'), '--check', str(directory / 'case.edits'), str(raw)])
            command([sys.executable, str(HERE / 'splice-cases.py'), '--check-paths', str(directory / 'case.edits.paths'), str(raw)])
            command([sys.executable, str(HERE / 'percentage-splice.py'), args.driver, str(directory), '--extract', str(raw)])
            # Quirks and overflowing arithmetic probe conservative refusal;
            # their retained/fresh equality is required without claiming the
            # ordinary exact-size domain covers those resolution modes.
            if name not in ('quirks', 'near-limit'):
                for page in ('case', 'inserted'):
                    command(['node', 'tests/layout/layout_oracle.mjs', 'dump', str(directory / (page + '.html'))], directory / (page + '.chromium.tsv'))
                for prefix, page in ((0, 'case'), (1, 'inserted'), (2, 'case')):
                    command(['node', 'tests/layout/layout_oracle.mjs', 'compare', str(directory / (page + '.chromium.tsv')), str(directory / ('prefix-%d.tsv' % prefix))])
        except subprocess.CalledProcessError as error:
            failed.append(name)
            print('FAILED', name, error, flush=True)
        elapsed = time.monotonic() - started
        totals.append('%s\t%.3f\t%s' % (name, elapsed, 'FAIL' if name in failed else 'PASS'))
        print(totals[-1], flush=True)
    (args.directory / 'summary.tsv').write_text('\n'.join(totals) + '\n')
    if failed:
        raise SystemExit('failed Q139 fixtures: ' + ', '.join(failed))


if __name__ == '__main__':
    main()
