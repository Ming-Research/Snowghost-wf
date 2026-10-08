"""Apply one Q139 semantic mutation and require its focused observation in CI.

Wired to the temporary falsify-m2 workflow. Source edits require one exact
match in the named function. Compiler failures and unrelated driver errors
are never detection. Certificate rows isolate one premise when integration
has another conservative guard; policy rows require loss of reason 7 itself.
"""
import argparse
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent

# file, function, old, new, fixture, observation
MUTATIONS = {
    'omit-minimum-reader': ('height_basis', 'height_read_mask', 'set mask = mask + 2_u8;', 'set mask = mask + 0_u8;', 'auto-minimum', 'path'),
    'omit-maximum-reader': ('height_basis', 'height_read_mask', 'set mask = mask + 4_u8;', 'set mask = mask + 0_u8;', 'auto-maximum', 'path'),
    'omit-nested-reader': ('height_basis', 'context_height_summary', 'set inside = total.heights;', 'set inside = empty_height_summary();', 'nested-context-reader', 'path'),
    'omit-float-reader': ('splice_motion', 'entry_motion', 'set output.heights = context_height_summary(context: &context^.children.inner[at], styles: styles);', 'set output.heights = empty_height_summary();', 'float-reader', 'path'),
    'context-height-basis': ('flow', 'prepare_spaces', 'set height = definite_block_height(styles: styles, style: style, basis_width: saved.width, basis_height: saved.basis_height);', 'set height = content_height;', 'nested', 'chromium'),
    'flatten-auto-basis': ('flow', 'prepare_spaces', 'set height = definite_block_height(styles: styles, style: style, basis_width: saved.width, basis_height: saved.basis_height);', 'let resolved_height = definite_block_height(styles: styles, style: style, basis_width: saved.width, basis_height: saved.basis_height);\n          if resolved_height >= 0_i32 {\n            set height = resolved_height;\n          }', 'auto-intermediate', 'chromium'),
    'indefinite-numeric-basis': ('height_basis', 'height_proof_summary', 'if proof.basis_state != 2_u8 {\n    return HeightSummary(consumers: readers, unproved: readers);\n  }', '', 'auto-later-reader', 'certificate'),
    'immutable-stretch': ('height_basis', 'height_dependency_state', 'return 3_u8;\n  }\n  if content', 'return 2_u8;\n  }\n  if content', 'layout-stretch', 'certificate'),
    'omit-growing-basis': ('height_basis', 'height_dependency_state', 'if basis_state != 2_u8 {\n      return 3_u8;\n    }', '', 'auto-intermediate', 'certificate'),
    'equal-number-growing': ('height_basis', 'height_dependency_state', 'if content < 0_i32 {\n    return 1_u8;\n  }', 'if content < 0_i32 {\n    return 2_u8;\n  }', 'layout-stretch', 'certificate'),
    'stale-definiteness': ('height_basis', 'same_height_input', 'if first.state != second.state {\n    return False();\n  }', '', 'equal-state', 'certificate'),
    'stale-source-handle': ('height_basis', 'same_height_input', 'if first.owner != second.owner {\n    return False();\n  }', '', 'private-chain', 'certificate'),
    'stale-source-context': ('height_basis', 'same_height_input', 'if first.context != second.context {\n    return False();\n  }', '', 'private-chain', 'certificate'),
    'stale-source-element': ('height_basis', 'same_height_input', 'if first.element != second.element {\n    return False();\n  }', '', 'equal-state', 'certificate'),
    'stale-resolution-mode': ('height_basis', 'same_height_input', 'if first.kind != second.kind {\n    return False();\n  }', '', 'layout-stretch', 'certificate'),
    'stale-viewport': ('height_basis', 'height_resolution_current', 'if proof.basis_height != height {\n    return False();\n  }', '', 'root', 'certificate'),
    'stale-width': ('height_basis', 'height_resolution_current', 'if proof.basis_width != width {\n    return False();\n  }', '', 'framed', 'certificate'),
    'missing-record': ('height_basis', 'height_resolution_current', 'if proof.valid {\n  } else {\n    return False();\n  }', '', 'nested', 'certificate'),
    'grow-fixed-height': ('boundary', 'propagate_boundary', 'let outgoing_delta = if measured.fixed_height {\n      give 0_i32;', 'let outgoing_delta = if measured.fixed_height {\n      give geometry_narrow(value: wide_delta);', 'root', 'identity'),
    'grow-auto-clamp': ('update', 'snapshot_grows', 'if maximum >= 0_i32 {\n    return False();\n  }\n  if minimum > frame {\n    return False();\n  }', '', 'cross-minimum', 'identity'),
    'private-context-basis': ('splice', 'splice_inputs', 'set input.basis_height = owner_height;', 'set input.basis_height = frame.definite;', 'private-reader', 'identity'),
    'omit-private-publication': ('splice', 'structure_splice', 'set added = normalized;', 'set normalized.heights = empty_height_summary();\n    set added = normalized;', 'private-reader', 'identity'),
    'omit-metadata-equality': ('boundary', 'same_transfer', 'if first.heights.consumers != second.heights.consumers {\n    return False();\n  }\n  if first.heights.unproved != second.heights.unproved {\n    return False();\n  }', '', 'private-reader', 'certificate'),
    'fixed-float-common-motion': ('splice_motion', 'outward_motion_ready', 'set obstacle = imax(obstacle, reach);', 'set obstacle = obstacle;', 'fixed-float-reentry', 'path'),
    'constrained-strut': ('boundary', 'lift_block_output', 'if measured.bottom_separates {', 'if measured.constrained_height {', 'inactive-maximum-margin', 'certificate'),
    'skip-viewport-refresh': ('oracle', 'run_edits', 'set kept = move resized;', 'let ignored = move resized;', 'root', 'identity'),
}


def function_span(source, function):
    start = source.index('fn ' + function + '(')
    end = source.find('\nfn ', start + 1)
    return start, len(source) if end < 0 else end


def apply(name):
    file, function, old, new, _, _ = MUTATIONS[name]
    path = Path('renderer/oracle/layout/edit.wf') if file == 'oracle' else Path('renderer/layout/' + file + '.wf')
    source = path.read_text()
    start, end = function_span(source, function)
    body = source[start:end]
    if body.count(old) != 1:
        raise ValueError('%s: expected one mutation site, got %d' % (name, body.count(old)))
    path.write_text(source[:start] + body.replace(old, new) + source[end:])
    print('applied', name, path, function)


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    made = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(made)
    return made


def classify(status, output, error, script, mode, baseline_paths):
    if mode == 'certificate':
        return status == 2 and error.strip() == 'boundary transfer check failed' and not output
    if status != 0 or error:
        raise ValueError('unrelated driver failure: %d %s' % (status, error))
    normalized, differences = re.subn(r'^(edit \d+ hash [0-9a-f]{16} bytes \d+ inc )DIFF$', r'\1same', output, flags=re.M)
    normalized_path = script.parent / 'normalized.raw'
    normalized_path.write_text(normalized)
    checker = module('inctime')
    checker.read(str(normalized_path), checker.script_operations(str(script)), checking=True, require_paths=True)
    if differences:
        return True
    if mode == 'path':
        actual = {int(n): (int(local), int(reason)) for n, local, reason in re.findall(r'^structure path (\d+) splice ([01]) reason (\d+)$', output, re.M)}
        # Only loss of this premise's required refusal counts; an unrelated
        # earlier refusal must not count as a policy mutation detection.
        return any(expected == (0, 7) and actual[number] == (1, 0)
                   for number, expected in baseline_paths.items())
    return False


def run_driver(driver, args, stem):
    completed = subprocess.run([driver] + args, capture_output=True, text=True)
    stem.with_suffix('.raw').write_text(completed.stdout)
    stem.with_suffix('.err').write_text(completed.stderr)
    stem.with_suffix('.status').write_text(str(completed.returncode) + '\n')
    return completed


def verify(name, baseline, mutant, directory):
    directory.mkdir(parents=True, exist_ok=True)
    _, _, _, _, case, mode = MUTATIONS[name]
    args = [sys.executable, str(HERE / 'percentage-splice.py'), baseline, str(directory), '--case', case]
    if case in ('root', 'nested', 'framed', 'private-reader', 'private-chain', 'equal-state'):
        args.append('--lifetime')
    subprocess.run(args, check=True)
    script = directory / 'case.edits'
    required = {int(n): (int(local), int(reason)) for n, local, reason in re.findall(r'^structure path (\d+) splice ([01]) reason (\d+)$', script.with_suffix('.edits.paths').read_text(), re.M)}
    edit_args = ['edit', str(script), str(directory / 'case.html'), 'renderer/style/ua.css']
    base = run_driver(baseline, edit_args, directory / 'baseline')
    if base.returncode or base.stderr:
        raise ValueError('baseline driver failed: ' + base.stderr)
    checker = module('inctime')
    checker.read(str(directory / 'baseline.raw'), checker.script_operations(str(script)), checking=True, require_paths=True)
    subprocess.run([sys.executable, str(HERE / 'splice-cases.py'), '--check-paths', str(script) + '.paths', str(directory / 'baseline.raw')], check=True)
    if mode == 'chromium':
        args = ['dump', '1', 'tests/layout/percentage-height-cases.html', 'renderer/style/ua.css']
        wrong = run_driver(mutant, args, directory / 'mutated')
        if wrong.returncode or wrong.stderr:
            raise ValueError('mutant dump driver failed: ' + wrong.stderr)
        comparison = subprocess.run(['node', 'tests/layout/layout_oracle.mjs', 'compare', 'tests/layout/percentage-height-cases.chromium.tsv', str(directory / 'mutated.raw')], capture_output=True, text=True)
        (directory / 'chromium-comparison.txt').write_text(comparison.stdout + comparison.stderr)
        detected = comparison.returncode == 1 and 'block-level boxes:' in comparison.stdout
    else:
        wrong = run_driver(mutant, edit_args, directory / 'mutated')
        detected = classify(wrong.returncode, wrong.stdout, wrong.stderr, script, mode, required)
        if classify(base.returncode, base.stdout, base.stderr, script, mode, required):
            raise ValueError('unmutated negative control was accepted as detection')
    print(('detected: ' if detected else 'NOT DETECTED: ') + name)
    if not detected:
        raise SystemExit(1)


def self_test():
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / 'case.edits'
        script.write_text('B 1 - Text\nX 10\n')
        rows = ['base hash 0000000000000000 bytes 1', 'created 10',
                'structure path 1 splice 0 reason 7',
                'edit 1 hash 0000000000000001 bytes 2 inc same',
                'structure path 2 splice 0 reason 7',
                'edit 2 hash 0000000000000000 bytes 1 inc same']
        good = '\n'.join(rows) + '\n'
        paths = {1: (0, 7), 2: (0, 7)}
        assert not classify(0, good, '', script, 'path', paths)
        assert classify(0, good.replace('splice 0 reason 7', 'splice 1 reason 0'), '', script, 'path', paths)
        assert not classify(0, good.replace('reason 7', 'reason 9'), '', script, 'path', paths)
        assert classify(0, good.replace('inc same', 'inc DIFF'), '', script, 'identity', paths)
        assert classify(2, '', 'boundary transfer check failed\n', script, 'certificate', paths)
        assert not classify(2, '', 'unrelated error', script, 'certificate', paths)
        assert not classify(2, good, 'boundary transfer check failed\n', script, 'certificate', paths)
        for status, output, error in ((9, '', 'crash'), (0, good + 'bad protocol\n', ''),
                                      (0, good.replace(rows[2] + '\n', ''), '')):
            try:
                classify(status, output, error, script, 'identity', paths)
            except ValueError:
                pass
            else:
                raise AssertionError('invalid output accepted')
    print('Q139 detector distinguishes identity, intended policy, certificate and unrelated failures')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('apply', 'verify', 'list', 'self-test'))
    parser.add_argument('name', nargs='?', choices=MUTATIONS)
    parser.add_argument('baseline', nargs='?')
    parser.add_argument('mutant', nargs='?')
    parser.add_argument('directory', nargs='?', type=Path)
    args = parser.parse_args()
    if args.action == 'list':
        print(' '.join(MUTATIONS))
    elif args.action == 'self-test':
        self_test()
    elif args.action == 'apply':
        apply(args.name)
    else:
        verify(args.name, args.baseline, args.mutant, args.directory)


if __name__ == '__main__':
    main()
