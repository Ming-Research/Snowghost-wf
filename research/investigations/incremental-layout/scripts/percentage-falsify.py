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
    'omit-minimum-reader': ('height_basis', 'sizing_read_mask', 'set mask = mask + 2_u8;', 'set mask = mask + 0_u8;', 'auto-minimum', 'path'),
    'omit-maximum-reader': ('height_basis', 'sizing_read_mask', 'set mask = mask + 4_u8;', 'set mask = mask + 0_u8;', 'auto-maximum', 'path'),
    'omit-nested-reader': ('height_basis', 'context_height_summary', 'set inside = total.heights;', 'set inside = empty_height_summary();', 'nested-context-reader', 'path'),
    'omit-float-reader': ('splice_motion', 'entry_motion', 'set output.heights = context_height_summary(context: &context^.children.inner[at], styles: styles);', 'set output.heights = empty_height_summary();', 'float-reader', 'path'),
    'context-height-basis': ('flow', 'prepare_spaces', 'set height = proof.content_height;', 'set height = content_height;', 'nested', 'chromium'),
    'flatten-auto-basis': ('flow', 'prepare_spaces', 'set height = proof.content_height;', 'if proof.content_height >= 0_i32 {\n            set height = proof.content_height;\n          }', 'auto-intermediate', 'chromium'),
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
    'skip-definiteness-refresh': ('flow', 'prepare_spaces', 'set context^.blocks.inner[at].height_proof = proof;', 'let old = context^.blocks.inner[at].height_proof;\n          let was_fixed = old.state == 2_u8;\n          let now_auto = proof.state == 1_u8;\n          let changed = band(was_fixed, now_auto);\n          if changed {\n          } else {\n            set context^.blocks.inner[at].height_proof = proof;\n          }', 'equal-state', 'identity'),
    'skip-width-refresh': ('height_basis', 'refresh_local_height_proofs', 'set context^.blocks.inner[at].height_proof = proof;', 'let old = context^.blocks.inner[at].height_proof;\n          let width_changed = old.basis_width != context^.blocks.inner[at].avail_width;\n          let stale = band(old.valid, width_changed);\n          if stale {\n          } else {\n            set context^.blocks.inner[at].height_proof = proof;\n          }', 'partial-restyle', 'positive-path'),
    'skip-private-context-rebase': ('build', 'record_tree', 'set context^.height_proof.source_context = parent;', '', 'private-context-chain', 'positive-path'),
    'skip-private-owner-rebase': ('splice_publish', 'relocate_splice', 'set block^.height_proof.source_owner = block^.height_proof.source_owner +sat input.blocks;', 'set block^.height_proof.source_owner = block^.height_proof.source_owner +sat 0_u32;', 'private-chain', 'positive-path'),
    'missing-record': ('height_basis', 'height_resolution_current', 'if proof.valid {\n  } else {\n    return False();\n  }', '', 'nested', 'certificate'),
    'grow-fixed-height': ('boundary', 'propagate_boundary', 'let outgoing_delta = if measured.fixed_height {\n      give 0_i32;', 'let outgoing_delta = if measured.fixed_height {\n      give geometry_narrow(value: wide_delta);', 'root', 'identity'),
    'grow-auto-clamp': ('update', 'snapshot_grows', 'if maximum >= 0_i32 {\n    return False();\n  }\n  if minimum > frame {\n    return False();\n  }', '', 'cross-minimum', 'identity'),
    'private-context-basis': ('splice', 'splice_inputs', 'set input.basis_height = owner_height;', 'set input.basis_height = frame.definite;', 'private-reader', 'identity'),
    'omit-private-publication': ('splice', 'structure_splice', 'set added = normalized;', 'set normalized.heights = empty_height_summary();\n    set added = normalized;', 'private-reader', 'identity'),
    'omit-metadata-equality': ('boundary', 'same_transfer', 'if first.heights.consumers != second.heights.consumers {\n    return False();\n  }\n  if first.heights.unproved != second.heights.unproved {\n    return False();\n  }', '', 'private-reader', 'certificate'),
    'fixed-float-common-motion': ('splice_motion', 'outward_motion_ready', 'set obstacle = imax(obstacle, reach);', 'set obstacle = obstacle;', 'fixed-float-reentry', 'path'),
    'constrained-strut': ('boundary', 'lift_block_output', 'if measured.bottom_separates {', 'if measured.constrained_height {', 'inactive-maximum-margin', 'certificate'),
    'skip-viewport-refresh': ('oracle', 'run_edits', 'let resized = match build_page(page: page, fonts: fonts, environment: environment, viewport: viewport, preserve: preserve)', 'let stale_viewport = Viewport(width: 1.28e3_f32, height: 7.2e2_f32);\n        let resized = match build_page(page: page, fonts: fonts, environment: environment, viewport: stale_viewport, preserve: preserve)', 'root', 'identity'),
    'retired-dependency': ('splice_boundary', 'splice_sequence_plan', 'set output.motion_known = motion_total.motion_known;', 'set output.motion_known = motion_total.motion_known;\n  if removing {\n    set output.heights = old.heights;\n  }', 'private-reader', 'identity'),
    'stop-fixed-output-equality': ('boundary', 'propagate_boundary', 'let stable = band(same, size_same);', 'let stable = size_same;', 'private-reader', 'identity'),
    'height-based-padding': ('flow', 'prepare_spaces', 'let padding = padding_edges(styles: styles, style: style, basis: width);', 'let padding = padding_edges(styles: styles, style: style, basis: height);', 'sibling-width-percent', 'full'),
    'height-based-margins': ('flow', 'stack_flow', 'let margins = margin_edges(styles: styles, style: style, basis: outer_width);', 'let margins = margin_edges(styles: styles, style: style, basis: frame.basis_height);', 'sibling-width-percent', 'full'),
    'suppress-refusal-row': ('oracle', 'put_structure_path', 'put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);', 'if reason == 7_u32 {\n    return unit;\n  }\n  put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);', 'auto-later-reader', 'protocol'),
    'count-refusal-as-splice': ('oracle', 'put_structure_path', 'put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);', 'if reason == 7_u32 {\n    set reason = 0_u32;\n  }\n  put_text(buffer: buffer, text: &structure_path_label[0_u64..15_u64]);', 'auto-later-reader', 'path'),
    'collapse-percentage-chain': ('flow', 'stack_flow', 'let specified = specified_height(styles: styles, style: style, basis: block_basis, frame: vertical_frame);', 'let specified = specified_height(styles: styles, style: style, basis: block_basis, frame: vertical_frame);\n          let fused = fused_percentage_height(context: context, styles: styles, at: at);\n          if fused >= 0_i32 {\n            set specified = fused;\n          }', 'rounding', 'full'),
}

# A semantic omission with more than one writer is applied at every writer:
# skipping width invalidation in only the partial-restyle refresh would be
# repaired by the reference publisher, which writes the same record.
EXTRA_SITES = {
    'skip-width-refresh': [
        ('flow', 'prepare_spaces', 'set context^.blocks.inner[at].height_proof = proof;', 'let old = context^.blocks.inner[at].height_proof;\n          let width_changed = old.basis_width != width;\n          let stale = band(old.valid, width_changed);\n          if stale {\n          } else {\n            set context^.blocks.inner[at].height_proof = proof;\n          }'),
        ('boundary', 'reference_item_output', 'set context^.blocks.inner[at].height_proof = proof;', 'let old = context^.blocks.inner[at].height_proof;\n        let width_changed = old.basis_width != context^.blocks.inner[at].avail_width;\n        let stale = band(old.valid, width_changed);\n        if stale {\n        } else {\n          set context^.blocks.inner[at].height_proof = proof;\n        }'),
    ],
}

FUSION = '''
fn fused_percentage_height(context: &Context, styles: &Styles, at: u64) -> made: i32 reads(context), reads(styles) {
  if at < context^.blocks.inner.len {
    let child = &context^.blocks.inner[at];
    let parent_at = cvt::<u32, u64>(child^.parent);
    if parent_at < context^.blocks.inner.len {
      let parent = &context^.blocks.inner[parent_at];
      let own = size_of(styles: styles, style: child^.style);
      let outer = size_of(styles: styles, style: parent^.style);
      if own.height.kind == sizing_value {
        if outer.height.kind == sizing_value {
          if own.height.value.has_percent {
            if outer.height.value.has_percent {
              let basis = parent^.output.basis_height;
              if basis >= 0_i32 {
                let grand = pixels(raw: basis);
                let combined = fmul.strict(own.height.value.percent, outer.height.value.percent);
                let ratio = fdiv.strict(combined, 1.0e4_f32);
                let resolved = fmul.strict(grand, ratio);
                let raw = units(px: resolved);
                return raw;
              }
            }
          }
        }
      }
    }
  }
  return unknown;
}
'''


def function_span(source, function):
    """The function through its closing brace at column 0, excluding the
    separator and any following struct, alias or function."""
    start = source.index('fn ' + function + '(')
    end = source.index('\n}\n', start) + 2
    return start, end


def apply_site(name, file, function, old, new):
    path = Path('renderer/oracle/layout/edit.wf') if file == 'oracle' else Path('renderer/layout/' + file + '.wf')
    source = path.read_text()
    start, end = function_span(source, function)
    body = source[start:end]
    if body.count(old) != 1:
        raise ValueError('%s: expected one mutation site in %s, got %d' % (name, function, body.count(old)))
    changed = body.replace(old, new)
    # Removing a clause must not leave a whitespace-only line inside a
    # function: the language requires canonical trivia even for mutants.
    changed = '\n'.join(line for line in changed.splitlines() if line.strip())
    # source[end:] keeps the newline after the closing brace and the blank
    # separator before whatever item follows.
    path.write_text(source[:start] + changed + source[end:])
    print('applied', name, path, function)


def apply(name):
    file, function, old, new, _, _ = MUTATIONS[name]
    apply_site(name, file, function, old, new)
    for site in EXTRA_SITES.get(name, ()):
        apply_site(name, *site)
    if name == 'collapse-percentage-chain':
        helper = Path('renderer/layout/height_basis.wf')
        helper.write_text(helper.read_text() + FUSION)


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
    try:
        checker.read(str(normalized_path), checker.script_operations(str(script)), checking=True, require_paths=True)
    except ValueError as error:
        if mode == 'protocol' and 'partial structural path records' in str(error):
            return True
        raise
    if mode == 'protocol':
        return False
    if differences:
        return True
    if mode in ('path', 'positive-path'):
        actual = {int(n): (int(local), int(reason)) for n, local, reason in re.findall(r'^structure path (\d+) splice ([01]) reason (\d+)$', output, re.M)}
        # Only loss of this premise's required refusal counts; an unrelated
        # earlier refusal must not count as a policy mutation detection.
        if mode == 'positive-path':
            return any(expected == (1, 0) and actual[number] == (0, 7)
                       for number, expected in baseline_paths.items())
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
    if case in ('root', 'nested', 'framed', 'private-reader', 'private-chain', 'private-context-chain', 'equal-state', 'partial-restyle'):
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
    if mode == 'full':
        args = ['dump', '1', str(directory / 'case.html'), 'renderer/style/ua.css']
        fresh = run_driver(baseline, args, directory / 'baseline-full')
        wrong = run_driver(mutant, args, directory / 'mutated-full')
        if fresh.returncode or fresh.stderr or wrong.returncode or wrong.stderr:
            raise ValueError('full dump failed')
        detected = fresh.stdout != wrong.stdout
    elif mode == 'chromium':
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
        positives = {1: (1, 0), 2: (1, 0)}
        assert classify(0, good, '', script, 'positive-path', positives)
        assert not classify(0, good.replace('reason 7', 'reason 9'), '', script, 'positive-path', positives)
        assert not classify(0, good.replace('splice 0 reason 7', 'splice 1 reason 0'), '', script, 'positive-path', positives)
        assert classify(0, good.replace('inc same', 'inc DIFF'), '', script, 'identity', paths)
        assert classify(2, '', 'boundary transfer check failed\n', script, 'certificate', paths)
        assert not classify(2, '', 'unrelated error', script, 'certificate', paths)
        assert not classify(2, good, 'boundary transfer check failed\n', script, 'certificate', paths)
        assert classify(0, good.replace(rows[2] + '\n', ''), '', script, 'protocol', paths)
        assert not classify(0, good, '', script, 'protocol', paths)
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
