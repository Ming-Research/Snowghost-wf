"""Per-unit constants of the full stages: sequential drivers, T(REPS)-T(0) over REPS, best of RUNS.
Run under the host lock: perl run-check.pl x1-timing python3 timing.py"""
import subprocess, time, json, sys
sys.path.insert(0, '.')
from lib import ROOT, D, UA, SHEETS
RUNS = 3
REPS = {'apollo11': 10, 'html5': 3, 'ecma262': 3}
out = {}
def best(tool, mode, reps, page):
    args = ['build/' + tool, mode, str(reps), D + '/' + page + '.html', UA] + ['%s=%s' % kv for kv in SHEETS[page].items()]
    b = None
    for _ in range(RUNS):
        t = time.time()
        r = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        d = time.time() - t
        if r.returncode != 0:
            raise RuntimeError(r.stderr[:200])
        b = d if b is None else min(b, d)
    return b
for page in ['apollo11', 'html5', 'ecma262']:
    o = {}
    cnt = subprocess.run(['build/layout_oracle', 'layout', '1', D + '/' + page + '.html', UA] + ['%s=%s' % kv for kv in SHEETS[page].items()], cwd=ROOT, stdout=subprocess.PIPE).stdout.decode()
    o['counts'] = cnt.strip()
    for tool, modes in (('layout_oracle', ['boxes', 'text', 'layout']), ('style_oracle', ['all'])):
        for m in modes:
            z = best(tool, m, 0, page)
            f = best(tool, m, REPS[page], page)
            o[tool + ':' + m] = (f - z) / REPS[page]
            print(page, tool, m, 'T0=%.3f TR=%.3f per-run=%.4f' % (z, f, (f - z) / REPS[page]), flush=True)
    out[page] = o
json.dump(out, open('results/timing.json', 'w'), indent=1)
