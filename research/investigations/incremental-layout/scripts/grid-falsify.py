"""Grid admission, row reuse and baseline mutations for the hosted Q140 workflow.

Reuses the established Q139 source-site and identity detector. A compiler
error, incomplete output or unrelated driver error never counts as detection.
Remove the temporary baseline-path option when Q140 admission is implemented.
"""
import argparse
import math
from pathlib import Path
import re
import subprocess
import tempfile

from importlib.util import module_from_spec, spec_from_file_location

HERE = Path(__file__).resolve().parent


def module(name):
    spec = spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    loaded = module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


MUTATIONS = {
    'omit-final-height-dependency': (
        'grid_retained', 'grid_same_layout',
        '  let same_height = bor(same_definite, child^.definite_free);',
        '  let same_height = True();', 'final-space', 'final-chromium'),
    'omit-final-used-height': (
        'grid_retained', 'grid_same_layout',
        '  return height == child^.height;',
        '  return True();', 'final-space', 'final-chromium'),
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
    'skip-grid-rerun': (
        'splice_boundary', 'publish_splice_at',
        'let replayed = splice_recompute_grid(context: context, styles: styles, document: document, fonts: fonts, picks: picks, viewport: viewport);',
        'let replayed = no_updates();', 'fixed', 'identity'),
    'reuse-stretched-row': (
        'grid', 'grid_measure_item',
        '    grid_row_contribution(item: item, measured: held);',
        '    set held.height = child^.height;\n    grid_row_contribution(item: item, measured: held);',
        'stretch-shrink', 'identity'),
    'omit-final-grid-space': (
        'grid', 'grid_finish_child', '    let ready = band(same, clean);',
        '    let ready = clean;', 'stretch-shrink', 'chromium'),
    'admit-intrinsic-columns': (
        'splice_grid', 'splice_grid_ready',
        '  if context^.grid_columns_invariant {\n  } else {\n    return False();\n  }',
        '', 'auto-maximum', 'path'),
    'admit-intrinsic-minimum': (
        'grid_retained', 'grid_independent_columns',
        '    let minimum = track.min_kind == track_length;',
        '    let minimum = True();', 'fractional-intrinsic-minimum', 'path'),
    'inspect-first-column-only': (
        'grid_retained', 'grid_column_item_ready',
        '  let span = grid_index(value: item.columns);',
        '  let span = 1_u64;', 'column-span-intrinsic', 'path'),
    'refuse-fixed-intrinsic-contribution': (
        'grid_retained', 'grid_column_item_ready',
        '      return grid_fixed_contribution(child: child, styles: styles);',
        '      return False();', 'auto-fixed-contribution', 'positive-path'),
    'omit-flex-automatic-minimum': (
        'splice_grid', 'splice_grid_flex_width',
        '  let needs_content = bor(content_base, content_minimum);',
        '  let needs_content = content_base;', 'flex-percentage-auto-min', 'path'),
    'trust-definite-grid-for-flex': (
        'splice_grid', 'splice_grid_flex_width',
        '    return band(grid, child^.grid_intrinsic_invariant);',
        '    return band(grid, child^.grid_columns_invariant);',
        'flex-percentage-intrinsic', 'path'),
    'admit-intrinsic-flexible-maximum': (
        'grid_retained', 'grid_independent_columns',
        '    let definite_flex = band(definite, flexible);',
        '    let definite_flex = flexible;', 'flex-fractional-intrinsic', 'path'),
    'forget-enclosing-flex-edge': (
        'splice', 'splice_inputs',
        '            give band(grid_inline_stable, edge);',
        '            give edge;', 'flex-nested-unproved', 'path'),
    'refuse-proved-flex-width': (
        'splice_grid', 'splice_grid_flex_width',
        '    return band(grid, child^.grid_intrinsic_invariant);',
        '    return False();', 'flex-fixed-intrinsic', 'positive-path'),
    'share-auto-margin-baseline': (
        'grid', 'grid_mark_baselines',
        '        let participates = band(aligned, manual);',
        '        let participates = aligned;', 'baseline-auto-margin', 'chromium'),
    'suppress-grid-refusal': (
        'oracle', 'put_structure_path',
        '  put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);',
        '  if reason == 11_u32 {\n    return unit;\n  }\n  put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);',
        'auto-maximum', 'protocol'),
    'count-grid-refusal-as-splice': (
        'oracle', 'put_structure_path',
        '  put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);',
        '  if reason == 11_u32 {\n    set reason = 0_u32;\n  }\n  put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);',
        'auto-maximum', 'path'),
}


# Removing the fixed-contribution read also removes its transitive effect.
# Keep the intentionally wrong program's effect rows exact; compilation is
# only a prerequisite for observing the excessive grid refusal.
EXTRA_SITES = {
    'refuse-fixed-intrinsic-contribution': [
        ('grid_retained', 'grid_column_item_ready',
         'reads(child), reads(tracks), reads(styles)', 'reads(tracks)'),
        ('grid_retained', 'grid_column_items_ready',
         'reads(children), reads(items), reads(tracks), reads(styles)',
         'reads(children), reads(items), reads(tracks)'),
    ],
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
    detector = module('percentage-falsify')
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / 'case.edits'
        script.write_text('B 1 - Text\n')
        def result(path):
            output = ('base hash 0000000000000000 bytes 1\ncreated 10\n' + path +
                      'edit 1 hash 0000000000000001 bytes 2 inc same\n')
            return subprocess.CompletedProcess([], 0, output, '')
        refused = result('structure path 1 splice 0 reason 11\n')
        spliced = result('structure path 1 splice 1 reason 0\n')
        unrelated = result('structure path 1 splice 0 reason 2\n')
        negative = {1: (0, 11)}
        positive = {1: (1, 0)}
        assert not classify(detector, refused, script, 'path', negative)
        assert classify(detector, spliced, script, 'path', negative)
        assert not classify(detector, unrelated, script, 'path', negative)
        assert not classify(detector, spliced, script, 'positive-path', positive)
        assert classify(detector, refused, script, 'positive-path', positive)
        assert not classify(detector, unrelated, script, 'positive-path', positive)
        assert classify(detector, result(''), script, 'protocol', negative)
    print('grid refusal loss and over-refusal detected; controls and unrelated refusals rejected')


def verify(name, baseline, mutant, directory, baseline_paths):
    directory.mkdir(parents=True, exist_ok=True)
    _, _, _, _, case, mode = MUTATIONS[name]
    grid = module('grid-splice')
    detector = module('percentage-falsify')
    if mode == 'final-chromium':
        page = Path('tests/layout/grid-final-space-cases.html')
        grid.command(['node', 'tests/layout/layout_oracle.mjs', 'dump', str(page)], directory / 'case.chromium.tsv')
        arguments = ['dump', '1', str(page), 'renderer/style/ua.css']
        base = detector.run_driver(baseline, arguments, directory / 'control')
        if base.returncode or base.stderr:
            raise ValueError('unmutated driver failed: ' + base.stderr)
        require_complete_dump(base.stdout)
        grid.command(['node', 'tests/layout/layout_oracle.mjs', 'compare', str(directory / 'case.chromium.tsv'), str(directory / 'control.raw')])
    else:
        grid.run(baseline, directory, case, baseline_paths)
        script = directory / 'case.edits'
        required = path_rows(script.with_suffix('.edits.paths').read_text())
        arguments = ['dump', '1', str(directory / 'case.html'), 'renderer/style/ua.css']
    if mode in ('chromium', 'final-chromium'):
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
        if classify(detector, base, script, mode, required):
            raise ValueError('unmutated control was accepted as detection')
        wrong = detector.run_driver(mutant, arguments, directory / 'mutated')
        detected = classify(detector, wrong, script, mode, required)
    print(('detected: ' if detected else 'NOT DETECTED: ') + name)
    if not detected:
        raise SystemExit(1)


def path_rows(output):
    return {int(n): (int(local), int(reason)) for n, local, reason in re.findall(
        r'^structure path (\d+) splice ([01]) reason (\d+)$', output, re.M)}


def classify(detector, result, script, mode, required):
    # Established validation rejects incomplete output, driver/compiler errors
    # and unrelated refusal reasons before the grid-specific path observation.
    shared_mode = 'protocol' if mode == 'protocol' else 'identity'
    if detector.classify(result.returncode, result.stdout, result.stderr, script, shared_mode, {}):
        return True
    actual = path_rows(result.stdout)
    if mode == 'path':
        return any(expected == (0, 11) and actual[number] == (1, 0)
                   for number, expected in required.items())
    if mode == 'positive-path':
        return any(expected == (1, 0) and actual[number] == (0, 11)
                   for number, expected in required.items())
    return False


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
        apply_site = module('percentage-falsify').apply_site
        apply_site(args.name, *MUTATIONS[args.name][:4])
        for site in EXTRA_SITES.get(args.name, ()):
            apply_site(args.name, *site)
    else:
        verify(args.name, args.baseline, args.mutant, args.directory, args.baseline_paths)


if __name__ == '__main__':
    main()
