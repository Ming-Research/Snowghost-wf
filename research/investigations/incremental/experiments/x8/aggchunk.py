#!/usr/bin/env python3
"""Aggregate chunks-*.jsonl: what appending K elements changes in the already laid-out prefix.
usage: aggchunk.py FILE..."""
import sys, json, collections
q = lambda a, p: sorted(a)[int(p * (len(a) - 1))] if a else float('nan')
rows = [json.loads(l) for fn in sys.argv[1:] for l in open(fn)]
sk = [r for r in rows if 'skipped' in r]
rows = [r for r in rows if 'skipped' not in r]
print('records', len(rows), 'skipped', len(sk), collections.Counter(r['skipped'] for r in sk))
def kb(k): return 20 if k < 100 else (200 if k < 1000 else 2000)
def line(name, rs):
    if not rs: return
    redo = [r['redo'] for r in rs]; opn = [r['open_ancestors'] for r in rs]
    work = [r['redo'] + r['open_ancestors'] for r in rs]
    ratio = [(r['K'] + w) / r['K'] for r, w in zip(rs, work)]
    print(f'{name:34s} n={len(rs):3d} redo med {q(redo,.5):6.0f} p90 {q(redo,.9):6.0f} max {max(redo):5d} | open med {q(opn,.5):3.0f} | '
          f'rigid max {max(r["rigid"] for r in rs):5d} | para relaid max {max(r["paragraphs_relaid_nonopen"] for r in rs):3d} | '
          f'ratio med {q(ratio,.5):6.2f} p90 {q(ratio,.9):7.2f} max {max(ratio):8.2f} | >2: {sum(1 for x in ratio if x>2)}/{len(rs)} | redo==0: {sum(1 for x in redo if x==0)}')
for p in ['apollo11', 'html5', 'ecma262']:
    for K in (20, 200, 2000):
        line(f'{p} K~{K} all', [r for r in rows if r['page'] == p and kb(r['K']) == K])
    for s in sorted({r['stratum'] for r in rows if r['page'] == p}):
        for K in (20, 200, 2000):
            line(f'{p} {s} K~{K}', [r for r in rows if r['page'] == p and r['stratum'] == s and kb(r['K']) == K])
