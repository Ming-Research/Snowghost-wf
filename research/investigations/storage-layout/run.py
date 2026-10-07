#!/usr/bin/env python3
"""CI caller for isolated acceptance probes; retain each verdict even on failure.

A Python driver is used because a shell loop cannot conveniently retain structured
per-probe results, both streams, exact statuses, and timeouts after failures.
Called only by storage-probes.yml; remove with that temporary workflow when this
research branch is retired. No compilation occurs during local static checks.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PROBES = Path(__file__).parent / 'probes'
OUT = ROOT / 'build/storage-probes'
COMPILER = ROOT / 'build/whitefoot/wf-f949e676acfa/whitefootc'
EXPECTATIONS = Path(__file__).with_name('expectations.json')


def inventory_ok(expected, present):
    return bool(expected) and set(expected) == set(present)


def compilation_ok(expected, code, text, source, mode):
    if 'rejection' in expected:
        rule, title, detail = expected['rejection']
        return (code == 1 and re.findall(r'error\[([^\]]+)\]', text) == [rule]
                and f'error[{rule}]: {title}' in text and detail in text)
    if code != 0:
        return False
    if mode == 'par':
        for line, verdict in expected['loops'].items():
            pattern = rf'^PAR loop\s+{re.escape(source)}:{line}  loop  {re.escape(verdict)}$'
            if not re.search(pattern, text, re.M):
                return False
    return True


def output_ok(code, stdout, stderr):
    return code == 0 and stdout == b'' and stderr == b''


def self_check():
    """Exercise missing-input and wrong-verdict failures without compiling."""
    positive = {'loops': {'3': 'permitted   eligible; no accumulator'}}
    ledger = 'PAR loop        probe.wf:3  loop  permitted   eligible; no accumulator'
    assert compilation_ok(positive, 0, ledger, 'probe.wf', 'par')
    assert not compilation_ok(positive, 0, '', 'probe.wf', 'par')
    assert not compilation_ok(positive, 0, ledger.replace('permitted', 'denied'), 'probe.wf', 'par')
    assert not compilation_ok(positive, 1, ledger, 'probe.wf', 'par')
    negative = {'rejection': ['RANGE-1', 'InvalidRangeClause', 'reason: a range term selects below an element']}
    diagnostic = 'error[RANGE-1]: InvalidRangeClause\nreason: a range term selects below an element'
    assert compilation_ok(negative, 1, diagnostic, 'probe.wf', 'seq')
    assert not compilation_ok(negative, 0, diagnostic, 'probe.wf', 'seq')
    assert not compilation_ok(negative, 1, diagnostic.replace('RANGE-1', 'FORM-3'), 'probe.wf', 'seq')
    assert not compilation_ok(negative, 124, diagnostic, 'probe.wf', 'seq')
    assert inventory_ok({'probe': positive}, ['probe'])
    assert not inventory_ok({'probe': positive}, [])
    assert not inventory_ok({}, [])
    assert output_ok(0, b'', b'')
    assert not output_ok(1, b'', b'')
    assert not output_ok(0, b'wrong', b'')
    assert not output_ok(0, b'', b'wrong')
    print('HARNESS self-check: missing input/ledger, denied loop, wrong rule, timeout, accepted negative, and wrong output all detected.')


def invoke(command, log, env=None):
    start = time.monotonic()
    try:
        done = subprocess.run(command, capture_output=True, timeout=120, env=env)
        code, stdout, stderr = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b'', error.stderr or b''
        stderr += b'\nPROBE TIMEOUT: no language verdict\n'
    elapsed = round(time.monotonic() - start, 3)
    Path(str(log) + '.stdout').write_bytes(stdout)
    Path(str(log) + '.stderr').write_bytes(stderr)
    return code, stdout, stderr, elapsed


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    expectations = json.loads(EXPECTATIONS.read_text())
    sources = sorted(PROBES.glob('*.wf'))
    if not inventory_ok(expectations, [source.stem for source in sources]):
        raise SystemExit('Probe files do not match the nonempty expectation inventory')
    results = []
    failed = False
    for source in sources:
        for mode in ('seq', 'par'):
            name = source.stem
            executable = OUT / (name + '-' + mode)
            command = [str(COMPILER)]
            if mode == 'par':
                command += ['--par', '--par-ledger']
            command += [str(source.relative_to(ROOT)), '-o', str(executable)]
            code, stdout, stderr, elapsed = invoke(command, executable)
            text = (stdout + stderr).decode(errors='replace')
            expected = expectations[name]
            ok = compilation_ok(expected, code, text, str(source.relative_to(ROOT)), mode)
            record = {'probe': name, 'mode': mode, 'compile_exit': code, 'seconds': elapsed}
            print(f'PROBE {name} {mode}: compile exit={code}, seconds={elapsed}', flush=True)
            for line in text.splitlines():
                if 'PAR loop' in line or 'PAR split' in line or code != 0:
                    print(line, flush=True)
            if 'rejection' in expected:
                record['expected_rule'] = expected['rejection'][0]
            else:
                if code == 0:
                    env = os.environ.copy()
                    env['WF_WORKERS'] = '4'
                    run_code, run_out, run_err, run_seconds = invoke([str(executable)], str(executable) + '.run', env)
                    correct = output_ok(run_code, run_out, run_err)
                    ok &= correct
                    record.update(run_exit=run_code, run_seconds=run_seconds, output_ok=correct)
                    print(f'OUTPUT {name} {mode}: exit={run_code}, stdout={run_out!r}, stderr={run_err!r}; literal checks {"PASS" if correct else "FAIL"}', flush=True)
            print(f'EXPECTATION {name} {mode}: {"PASS" if ok else "FAIL"}', flush=True)
            record['pass'] = ok
            failed |= not ok
            results.append(record)
    # The generated growth body is evidence for C1's nonrelocation subclaim.
    if not any(r['probe'] == 'c1-native-pages' and r['compile_exit'] != 0 for r in results):
        code, stdout, stderr, elapsed = invoke([str(COMPILER), '--emit-llvm', str(PROBES.relative_to(ROOT) / 'c1-native-pages.wf')], OUT / 'c1-native-pages-ir')
        (OUT / 'c1-native-pages.ll').write_bytes(stdout)
        print(f'IR c1-native-pages: exit={code}, seconds={elapsed}', flush=True)
        failed |= code != 0
    (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    return int(failed)


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-check']:
        self_check()
    elif sys.argv[1:]:
        raise SystemExit('usage: run.py [--self-check]')
    else:
        sys.exit(main())
