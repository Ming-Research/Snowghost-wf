#!/usr/bin/env python3
"""Time the layout driver (mode layout: boxes, text preparation, lay_out) on the page cut at 10/25/50/75 percent and on the whole page.
usage: timing-cuts.py PAGE OUT.jsonl.  Per-rep seconds = (T(R) - T(1)) / (R - 1), min over TRIALS; run under the host lock from /home/user/sg-text."""
import sys, subprocess, time, json, os
page, outp = sys.argv[1], sys.argv[2]
ROOT = '/home/user/sg-text'
data = 'build/research/concurrency'
sheets = {'ecma262': [f'assets/css/ecmarkup.css={data}/ecma262-ecmarkup.css', f'assets/css/print.css={data}/ecma262-print.css'],
          'html5': [],
          'apollo11': [f'wikibase.client.init&only=styles&skin=vector-2022={data}/apollo11-modules.css', f'modules=site.styles&only=styles&skin=vector-2022={data}/apollo11-site.css']}[page]
R = int(os.environ.get('REPS', '3')); TRIALS = int(os.environ.get('TRIALS', '2'))
def once(mode, path, reps):
    t = time.perf_counter()
    r = subprocess.run(['build/layout_oracle_x8', mode, str(reps), path, 'renderer/style/ua.css'] + sheets, cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return time.perf_counter() - t, r.stdout.strip()
res = open(outp, 'w')
for label, path in [('10', f'build/x8cut-{page}.10.html'), ('25', f'build/x8cut-{page}.25.html'), ('50', f'build/x8cut-{page}.50.html'), ('75', f'build/x8cut-{page}.75.html'), ('full', f'{data}/{page}.html')]:
    for mode in ('text', 'layout'):
        t1 = min(once(mode, path, 1)[0] for _ in range(TRIALS)); outs = [once(mode, path, R) for _ in range(TRIALS)]
        tr = min(o[0] for o in outs)
        rec = dict(page=page, cut=label, mode=mode, per_rep_s=(tr - t1) / (R - 1), one_rep_total_s=t1, out=outs[0][1])
        res.write(json.dumps(rec) + '\n'); res.flush(); print(rec, flush=True)
