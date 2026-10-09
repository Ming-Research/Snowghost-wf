"""First-baseline propagation mutations for the hosted Q140 fixture workflow.

Reuses the established Q139 source-site and identity detector. A compiler
error, incomplete output or unrelated driver error never counts as detection.
Remove the temporary baseline-path option when Q140 admission is implemented.
"""
import argparse
import math
from pathlib import Path
import subprocess

from importlib.util import module_from_spec, spec_from_file_location

HERE = Path(__file__).resolve().parent


def module(name):
    spec = spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    loaded = module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


MUTATIONS = {
    'omit-first-flow-update': (
        'update', 'update_flow',
        '  let first_visits = publish_flow_first_baseline(context: context);',
        '  let first_visits = no_boundary_visits();',
        'baseline-equal-height', 'identity'),
    'omit-first-output-equality': (
        'update', 'same_outputs',
        '  if before.first_baseline != context^.first_baseline {\n    return False();\n  }', '',
        'baseline-equal-height', 'identity'),
    'omit-first-child-publication': (
        'boundary', 'context_size_output', '  if has_first_baseline {',
        '  let publish_first = False();\n  if publish_first {',
        'baseline-nested-flow', 'chromium'),

}


def require_complete_dump(output):
    rows = output.splitlines()
    if not output.endswith('\n') or not rows or not rows[-1].startswith('H\t'):
        raise ValueError('incomplete dump: missing terminal height row')
    if sum(row.startswith('H\t') for row in rows) != 1:
        raise ValueError('malformed dump: duplicate height row')
    fields = rows[-1].split('\t')
    if len(fields) != 2 or not math.isfinite(float(fields[1])):
        raise ValueError('malformed dump: invalid terminal height')


def self_test():
    complete = 'E\t0\thtml\t-1\tb\t0,0,10,10\nT\t0\t0\t0,0,5,5\nH\t10\n'
    require_complete_dump(complete)
    incomplete = [
        '', complete.split('T\t')[0], complete.rsplit('H\t', 1)[0],
        complete.rstrip('\n'), complete + 'H\t10\n',
        complete.replace('H\t10', 'H\tnan'),
    ]
    for output in incomplete:
        try:
            require_complete_dump(output)
        except ValueError:
            continue
        raise AssertionError('incomplete or malformed dump accepted')
    print('complete dump accepted; truncated and malformed dumps rejected')


def verify(name, baseline, mutant, directory, baseline_paths):
    directory.mkdir(parents=True, exist_ok=True)
    _, _, _, _, case, mode = MUTATIONS[name]
    grid = module('grid-splice')
    detector = module('percentage-falsify')
    grid.run(baseline, directory, case, baseline_paths)
    script = directory / 'case.edits'
    if mode == 'chromium':
        arguments = ['dump', '1', str(directory / 'case.html'), 'renderer/style/ua.css']
        wrong = detector.run_driver(mutant, arguments, directory / 'mutated')
        if wrong.returncode or wrong.stderr:
            raise ValueError('mutated driver failed: ' + wrong.stderr)
        require_complete_dump(wrong.stdout)
        compared = subprocess.run([
            'node', 'tests/layout/layout_oracle.mjs', 'compare',
            str(directory / 'case.chromium.tsv'), str(directory / 'mutated.raw'),
        ], capture_output=True, text=True)
        (directory / 'mutated-comparison.txt').write_text(compared.stdout + compared.stderr)
        detected = compared.returncode == 1 and 'block-level boxes:' in compared.stdout
    else:
        arguments = ['edit', str(script), str(directory / 'case.html'), 'renderer/style/ua.css']
        base = detector.run_driver(baseline, arguments, directory / 'control')
        if detector.classify(base.returncode, base.stdout, base.stderr, script, 'identity', {}):
            raise ValueError('unmutated control was accepted as detection')
        wrong = detector.run_driver(mutant, arguments, directory / 'mutated')
        detected = detector.classify(wrong.returncode, wrong.stdout, wrong.stderr, script, 'identity', {})
    print(('detected: ' if detected else 'NOT DETECTED: ') + name)
    if not detected:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('self-test')
    apply = sub.add_parser('apply')
    apply.add_argument('name', choices=MUTATIONS)
    check = sub.add_parser('verify')
    check.add_argument('name', choices=MUTATIONS)
    check.add_argument('baseline')
    check.add_argument('mutant')
    check.add_argument('directory', type=Path)
    check.add_argument('--baseline-paths', action='store_true')
    args = parser.parse_args()
    if args.command == 'self-test':
        self_test()
    elif args.command == 'apply':
        module('percentage-falsify').apply_site(args.name, *MUTATIONS[args.name][:4])
    else:
        verify(args.name, args.baseline, args.mutant, args.directory, args.baseline_paths)


if __name__ == '__main__':
    main()
