#!/usr/bin/env python3
"""Reproduce strict-runner controls without executing a compiler or renderer.

Home: research/investigations/incremental-layout/scripts; called by
value_probe.py --controls and run.sh value-falsify. It imports the actual
runner, supplies process outcomes and uses only temporary evidence. Retire
with value_probe.py when these checks enter the regular style gate.
"""
import hashlib
import importlib.util
from pathlib import Path
from subprocess import CompletedProcess
import tempfile
from unittest.mock import patch

TASK_ROOT = Path(__file__).resolve().parent


def main():
    specification = importlib.util.spec_from_file_location('strict_falsifier_runner', TASK_ROOT / 'value_probe.py')
    runner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(runner)
    good = b'edit 1 changed 1 time_us 0\nflags 1 4\ndump 1\n'
    incorrect = [
        ('positive_process_failure', good, b'', 2, None),
        ('positive_stderr', good, b'error', 0, None),
        ('positive_no_records', b'', b'', 0, None),
        ('positive_missing_flags', good.split(b'flags')[0], b'', 0, None),
        ('positive_duplicate_edits', good + good.split(b'flags')[0], b'', 0, None),
        ('positive_duplicate_flags', good + b'flags 1 4\n', b'', 0, None),
        ('positive_wrong_edit_id', good.replace(b'edit 1', b'edit 2'), b'', 0, None),
        ('positive_wrong_count', good.replace(b'changed 1', b'changed 2'), b'', 0, None),
        ('positive_wrong_position', good.replace(b'flags 1 4', b'flags 1 5'), b'', 0, None),
        ('positive_malformed_edit', b'edit 1\nflags 1 4\n', b'', 0, None),
        ('positive_noninteger_flag', good.replace(b'flags 1 4', b'flags 1 nope'), b'', 0, None),
        ('negative_unexpected_success', b'', b'', 0, 1004),
        ('negative_signal_or_other_status', b'', b'value probe failed code 1004 edit 1\n', -9, 1004),
        ('negative_premise_failure', b'', b'value probe failed code 101 edit 1\n', 2, 1004),
        ('negative_wrong_element', b'', b'value probe failed code 1005 edit 1\n', 2, 1004),
        ('negative_wrong_edit', b'', b'value probe failed code 1004 edit 2\n', 2, 1004),
        ('negative_missing_diagnostic', b'', b'', 2, 1004),
        ('negative_extra_diagnostic', b'', b'value probe failed code 1004 edit 1\nextra\n', 2, 1004),
        ('negative_unexpected_stdout', b'bad', b'value probe failed code 1004 edit 1\n', 2, 1004),
        ('negative_truncated_diagnostic', b'', b'value probe failed code 1004 edit 1', 2, 1004),
    ]
    report = ['No real compiler, renderer, benchmark or production-file mutation.',
              'Process controls are harness tests, never comparison-falsifier evidence.']
    for name, stdout, stderr, status, expected in incorrect:
        try:
            runner.validate(CompletedProcess([], status, stdout, stderr), 4, expected)
        except ValueError:
            report.append(name + ': rejected')
        else:
            raise AssertionError('incorrect outcome accepted: ' + name)
    runner.validate(CompletedProcess([], 0, good, b''), 4, None)
    runner.validate(CompletedProcess([], 2, b'', b'value probe failed code 1004 edit 1\n'), 4, 1004)
    report.append('Two exact valid process controls: accepted')
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        (temporary_root / 'bin').mkdir()
        (temporary_root / 'evidence').mkdir()
        (temporary_root / 'sources/control/renderer').mkdir(parents=True)
        with patch.object(runner, 'TASK_ROOT', temporary_root), patch.object(
                runner.subprocess, 'run', return_value=CompletedProcess([], 1)):
            try:
                runner.build(Path('/not-invoked'), None, 'control')
            except ValueError as error:
                if 'compilation failed; this is not a killed mutant' not in str(error):
                    raise
                report.append('compile_failure_never_kills_mutant: rejected')
            else:
                raise AssertionError('compilation failure accepted')
        case = {'scenario': 1, 'direction': 'forward', 'script': 'input.edits', 'page': 'input.html',
                'expected_element': 4, 'edited_node': 6, 'failures': {}}
        sequential = good + b'original dump\n'
        parallel = sequential.replace(b'time_us 0', b'time_us 7')
        (temporary_root / 'evidence/control-s1-forward.stdout').write_bytes(sequential)
        with patch.object(runner, 'TASK_ROOT', temporary_root), patch.object(
                runner.subprocess, 'run', return_value=CompletedProcess([], 0, parallel, b'')):
            runner.run_variant('control-par', [case])
        report.append('seq/par timing-only difference: accepted')
        with patch.object(runner, 'TASK_ROOT', temporary_root), patch.object(
                runner.subprocess, 'run', return_value=CompletedProcess(
                    [], 0, parallel.replace(b'original dump', b'wrong dump'), b'')):
            try:
                runner.run_variant('control-par', [case])
            except ValueError as error:
                if 'complete seq/par outputs differ' not in str(error):
                    raise
                report.append('seq/par same flags but changed complete dump: rejected')
            else:
                raise AssertionError('different complete dump accepted')
        inverse = {**case, 'direction': 'inverse'}
        with patch.object(runner, 'TASK_ROOT', temporary_root), patch.object(
                runner.subprocess, 'run', side_effect=[CompletedProcess([], 1, b'', b'failed'),
                                                       CompletedProcess([], 0, good, b'')]) as calls:
            try:
                runner.run_variant('control', [case, inverse])
            except ValueError:
                if calls.call_count != 2 or not (temporary_root / 'evidence/control-s1-inverse.stdout').is_file():
                    raise AssertionError('forward failure hid the inverse run')
            else:
                raise AssertionError('forward failure accepted')
        report.append('inverse executes independently after a failed forward: verified')
        with patch.object(runner, 'TASK_ROOT', temporary_root), patch.object(
                runner.subprocess, 'run', side_effect=[OSError('stub execution failure'),
                                                       CompletedProcess([], 0, good, b'')]) as calls:
            try:
                runner.run_variant('control', [case, inverse])
            except ValueError:
                if calls.call_count != 2:
                    raise AssertionError('forward invocation error hid the inverse run')
            else:
                raise AssertionError('invocation failure accepted')
        report.append('inverse executes after a forward invocation error: verified')
        commands = []
        sample = 'fn layout_changes(old: &Styles) {\n  for (i in 0_u64..shorter) {\n}\n'
        ledger = 'PAR loop        ./style/delta.wf:2  loop  permitted   eligible; no accumulator\n'
        (temporary_root / 'sources/control/renderer/style').mkdir()
        (temporary_root / 'sources/control/renderer/style/delta.wf').write_text(sample)
        runner.certify_outer(sample, ledger)
        for bad in ('', ledger.replace('permitted   eligible;', 'denied      condition 2:'), ledger + ledger, ledger.replace(':2 ', ':3 ')):
            try:
                runner.certify_outer(sample, bad)
            except ValueError:
                pass
            else:
                raise AssertionError('missing/denied/duplicate/wrong-line ledger accepted')
        report.append('outer-loop ledger permitted accepted; missing/denied/duplicate/wrong-line rejected')

        def stub_compiler(command, **unused):
            commands.append(command)
            if '-o' in command:
                binary = Path(command[command.index('-o') + 1])
                binary.write_bytes(b'not executed compiler control')
                binary.chmod(0o755)
                unused['stdout'].write(ledger.encode())
            return CompletedProcess(command, 0)

        with patch.object(runner, 'TASK_ROOT', temporary_root), patch.object(
                runner.subprocess, 'run', side_effect=stub_compiler):
            runner.build(Path('/not-invoked'), None, 'control-par')
        if len(commands) != 3 or '--par' not in commands[-1] or '--par-ledger' not in commands[-1]:
            raise AssertionError('parallel control build omitted parallel flags')
        report.append('control-par build has --par --par-ledger: verified with stub only')
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        original = b'valid source'
        digest = hashlib.sha256(original).hexdigest()
        for name in runner.SOURCES:
            path = temporary_root / 'sources' / name / 'renderer/style/delta.wf'
            path.parent.mkdir(parents=True)
            path.write_bytes(original)
        input_path = temporary_root / 'input.edits'
        input_path.write_bytes(original)
        manifest = {'baseline_source_sha256': {'style/delta.wf': digest},
                    'variant_delta_sha256': {name: digest for name in runner.SOURCES[1:]},
                    'input_sha256': {'input.edits': digest},
                    'cases': [{'scenario': scenario, 'direction': direction}
                              for scenario in range(1, 8) for direction in ('forward', 'inverse')]}
        with patch.object(runner, 'TASK_ROOT', temporary_root):
            runner.verify_sources(manifest)
            report.append('valid source-copy/hash/matrix control: accepted')
            target = temporary_root / 'sources/control/renderer/style/delta.wf'
            extra = target.parent / 'unexpected.wf'
            for name, mutate, restore in [
                ('corrupted source', lambda: target.write_bytes(b'wrong'), lambda: target.write_bytes(original)),
                ('missing source', target.unlink, lambda: target.write_bytes(original)),
                ('extra source', lambda: extra.write_bytes(original), extra.unlink),
                ('corrupted input', lambda: input_path.write_bytes(b'wrong'), lambda: input_path.write_bytes(original)),
                ('incomplete matrix', lambda: manifest['cases'].pop(),
                 lambda: manifest['cases'].append({'scenario': 7, 'direction': 'inverse'})),
            ]:
                mutate()
                try:
                    runner.verify_sources(manifest)
                except (ValueError, OSError):
                    report.append(name + ': rejected')
                else:
                    raise AssertionError(name + ' accepted')
                finally:
                    restore()
            runner.verify_sources(manifest)
    try:
        runner.once('absent anchor', 'required anchor', 'mutated')
    except ValueError:
        report.append('missing patch anchor: rejected')
    else:
        raise AssertionError('missing patch anchor accepted')
    try:
        runner.once('anchor anchor', 'anchor', 'mutated')
    except ValueError:
        report.append('duplicate patch anchor: rejected')
    else:
        raise AssertionError('duplicate patch anchor accepted')
    report.append('PASS: 21 incorrect original controls rejected, 2 exact process controls accepted, normalized-output controls passed.')
    print('\n'.join(report))


if __name__ == '__main__':
    main()
