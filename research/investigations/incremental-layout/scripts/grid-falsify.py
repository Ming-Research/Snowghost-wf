"""First-baseline propagation mutations for the hosted Q140 fixture workflow.

Reuses the established Q139 source-site and identity detector. A compiler
error, incomplete output or unrelated driver error never counts as detection.
Remove the temporary baseline-path option when Q140 admission is implemented.
"""
import argparse
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
        'update', 'update_flow', '  publish_flow_first_baseline(context: context);', '',
        'baseline-equal-height', 'identity'),
    'omit-first-output-equality': (
        'update', 'same_outputs',
        '  if before.first_baseline != context^.first_baseline {\n    return False();\n  }', '',
        'baseline-equal-height', 'identity'),
    'omit-first-child-publication': (
        'boundary', 'context_size_output', '  if has_first_baseline {',
        '  let publish_first = False();\n  if publish_first {',
        'baseline-nested-flow', 'chromium'),
    'omit-first-splice-publication': (
        'splice_boundary', 'splice_finish', '  publish_flow_first_baseline(context: context);', '',
        'baseline-consumer', 'identity'),
}


def verify(name, baseline, mutant, directory, baseline_paths):
    if baseline_paths and name == 'omit-first-splice-publication':
        raise ValueError('splice publication requires Q140 admission; baseline refusals cannot detect it')
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
    apply = sub.add_parser('apply')
    apply.add_argument('name', choices=MUTATIONS)
    check = sub.add_parser('verify')
    check.add_argument('name', choices=MUTATIONS)
    check.add_argument('baseline')
    check.add_argument('mutant')
    check.add_argument('directory', type=Path)
    check.add_argument('--baseline-paths', action='store_true')
    args = parser.parse_args()
    if args.command == 'apply':
        module('percentage-falsify').apply_site(args.name, *MUTATIONS[args.name][:4])
    else:
        verify(args.name, args.baseline, args.mutant, args.directory, args.baseline_paths)


if __name__ == '__main__':
    main()
