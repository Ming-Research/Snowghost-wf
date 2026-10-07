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
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PROBES = Path(__file__).parent / 'probes'
OUT = ROOT / 'build/storage-probes'
COMPILER = ROOT / 'build/whitefoot/wf-f949e676acfa/whitefootc'
NEGATIVE = {
    'c2-missing-bound-negative': 'REF-4',
    'c3-alpha-w3': 'FORM-3',
    'c3-beta-w1': 'OP-2',
    'c3-beta-w3': 'FORM-3',
    'c4-field-inverse-negative': 'RANGE-1',
    'c5-changing-callback-negative': 'FN-6',
}


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
    results = []
    failed = False
    for source in sorted(PROBES.glob('*.wf')):
        for mode in ('seq', 'par'):
            name = source.stem
            executable = OUT / (name + '-' + mode)
            command = [str(COMPILER)]
            if mode == 'par':
                command += ['--par', '--par-ledger']
            command += [str(source.relative_to(ROOT)), '-o', str(executable)]
            code, stdout, stderr, elapsed = invoke(command, executable)
            text = (stdout + stderr).decode(errors='replace')
            expected = NEGATIVE.get(name)
            record = {'probe': name, 'mode': mode, 'compile_exit': code, 'seconds': elapsed}
            print(f'PROBE {name} {mode}: compile exit={code}, seconds={elapsed}', flush=True)
            for line in text.splitlines():
                if 'PAR loop' in line or 'PAR split' in line or code != 0:
                    print(line, flush=True)
            if expected:
                ok = code not in (0, 124) and f'error[{expected}]' in text
                record['expected_rule'] = expected
            else:
                ok = code == 0
                if ok:
                    env = os.environ.copy()
                    env['WF_WORKERS'] = '4'
                    run_code, run_out, run_err, run_seconds = invoke([str(executable)], str(executable) + '.run', env)
                    ok = run_code == 0 and run_out == b'' and run_err == b''
                    record.update(run_exit=run_code, run_seconds=run_seconds, output_ok=ok)
                    print(f'OUTPUT {name} {mode}: exit={run_code}, stdout={run_out!r}, stderr={run_err!r}; literal checks {"PASS" if ok else "FAIL"}', flush=True)
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
    sys.exit(main())
