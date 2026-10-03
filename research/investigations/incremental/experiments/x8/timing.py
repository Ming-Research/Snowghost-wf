#!/usr/bin/env python3
"""Time the layout driver's stages by the slope of process wall time over REPS.
usage: timing.py PAGE OUT.jsonl [SETS.json]
Per page: modes boxes, text, layout (cumulative stages), and, per font-family set from SETS.json
(fonts.py --sets), mode restricted (box tree + text preparation of only the paragraphs that use the
set) and mode relaid (the same followed by lay_out).  Per-rep seconds = (T(R) - T(1)) / (R - 1),
min of TRIALS trials of each.  Run under the host lock, from /home/user/sg-text."""
import sys, subprocess, time, json, os
page, outp = sys.argv[1], sys.argv[2]
sets = json.load(open(sys.argv[3]))['sets'] if len(sys.argv) > 3 else {}
ROOT = '/home/user/sg-text'
data = 'build/research/concurrency'
sheets = {'ecma262': [f'assets/css/ecmarkup.css={data}/ecma262-ecmarkup.css', f'assets/css/print.css={data}/ecma262-print.css'],
          'html5': [],
          'apollo11': [f'wikibase.client.init&only=styles&skin=vector-2022={data}/apollo11-modules.css', f'modules=site.styles&only=styles&skin=vector-2022={data}/apollo11-site.css']}[page]
R = int(os.environ.get('REPS', '4')); TRIALS = int(os.environ.get('TRIALS', '3'))
BIN = 'build/layout_oracle_x8'
def once(args, reps):
    t = time.perf_counter()
    r = subprocess.run([BIN, args[0], str(reps)] + args[1:] + [f'{data}/{page}.html', 'renderer/style/ua.css'] + sheets, cwd=ROOT, capture_output=True, text=True)
    dt = time.perf_counter() - t
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return dt, r.stdout.strip()
def slope(args):
    t1 = []; tr = []; out = ''
    for _ in range(TRIALS):
        t1.append(once(args, 1)[0]); d, out = once(args, R); tr.append(d)
    return (min(tr) - min(t1)) / (R - 1), min(t1), out
res = open(outp, 'w')
def emit(name, args):
    per, t1, out = slope(args)
    rec = dict(page=page, name=name, per_rep_s=per, one_rep_total_s=t1, reps=R, trials=TRIALS, out=out)
    res.write(json.dumps(rec) + '\n'); res.flush()
    print(f'{page} {name}: per rep {per*1000:.1f} ms (process with 1 rep {t1*1000:.0f} ms) {out}', flush=True)
ONLY = os.environ.get('ONLY')   # comma list of family names: time only the empty baselines and those sets (rare-font refinement with more reps)
ONLY = ONLY.split(',') if ONLY else None
for m in ['boxes', 'text', 'layout']:
    if ONLY is None: emit(m, [m])
emit('restricted-empty', ['restricted', '99999999'])
emit('relaid-empty', ['relaid', '99999999'])
seen = {}
for fam, s in sets.items():
    if ONLY is not None and fam not in ONLY: continue
    for kind in ['first', 'any']:
        groups = s[kind]
        if not groups: continue
        keep = ','.join(map(str, groups))
        if keep in seen:
            print(f'{page} {fam} {kind}: same groups as {seen[keep]}', flush=True); continue
        seen[keep] = f'{fam} {kind}'
        emit(f'restricted {fam} {kind}', ['restricted', keep])
        emit(f'relaid {fam} {kind}', ['relaid', keep])
