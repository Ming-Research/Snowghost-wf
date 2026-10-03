#!/usr/bin/env python3
"""Aggregate samples-*.jsonl: what an append changes in the already laid-out prefix.
usage: agg.py FILE... ; the full element count of each page is read from dumps/PAGE.full.layout.tsv"""
import sys, json, collections, statistics, os
X = os.path.dirname(os.path.abspath(__file__))
N = {}
def nfull(p):
    if p not in N: N[p] = sum(1 for l in open(f'{X}/dumps/{p}.full.layout.tsv') if l.startswith('E\t'))
    return N[p]
q = lambda a, p: sorted(a)[int(p * (len(a) - 1))] if a else float('nan')
rows = []
for fn in sys.argv[1:]:
    for l in open(fn):
        r = json.loads(l)
        if 'skipped' in r: rows.append(dict(page=r['page'], stratum=r['stratum'], skipped=True)); continue
        cl = r['classes']
        # non-open boxes whose own size or relative position changed: need their layout redone
        redo = sum(v for k, v in cl.items() if not k.startswith('open_') and k not in ('same', 'nobox', 'moved_rel_same'))
        rigid = cl.get('moved_rel_same', 0)
        opn = r['open_ancestors']
        t = r['text']; tre = r['paragraphs_relaid_nonopen']
        suffix = nfull(r['page']) - r['cut']
        rows.append(dict(page=r['page'], stratum=r['stratum'], cut=r['cut'], suffix=suffix, redo=redo, rigid=rigid, open=opn,
                         para_relaid=tre, style=r['style_changed_nonopen_rows'], pseudo=r['pseudo_changed_nonopen'],
                         text_frag=t.get('frag_count', 0) + t.get('frag_resized', 0), text_moved=t.get('moved', 0),
                         boxes=r['boxes'], skipped=False))
good = [r for r in rows if not r['skipped']]
print('samples', len(rows), 'skipped (structure of truncated page differs)', len(rows) - len(good))
def block(name, rs):
    if not rs: return
    n = len(rs)
    redo = [r['redo'] for r in rs]; work = [r['redo'] + r['open'] for r in rs]
    print(f'\n## {name}: n={n}')
    print(f'  prefix boxes that are not open ancestors and changed size or relative position ("redo"): zero in {sum(1 for x in redo if x==0)}/{n}; median {q(redo,.5)}, p90 {q(redo,.9)}, max {max(redo)}')
    print(f'  open ancestors (their extent grows with the appended content): median {q([r["open"] for r in rs],.5)}, max {max(r["open"] for r in rs)}')
    print(f'  re-laid-out prefix boxes = redo + open: median {q(work,.5)}, p90 {q(work,.9)}, max {max(work)}')
    print(f'  rigidly translated boxes (position relative to parent unchanged): nonzero in {sum(1 for r in rs if r["rigid"])}/{n}, max {max(r["rigid"] for r in rs)}')
    print(f'  paragraphs of the prefix whose line breaks changed (excluding open ancestors): nonzero in {sum(1 for r in rs if r["para_relaid"])}/{n}, max {max(r["para_relaid"] for r in rs)}')
    print(f'  prefix text fragments with a changed count or size: median {q([r["text_frag"] for r in rs],.5)}, max {max(r["text_frag"] for r in rs)}; text moved only: max {max(r["text_moved"] for r in rs)}')
    print(f'  prefix style rows changed (non-open): nonzero in {sum(1 for r in rs if r["style"])}/{n}; pseudo rows: {sum(1 for r in rs if r["pseudo"])}/{n}')
    # cost proxy: elements. ratio = (suffix + re-laid prefix boxes)/suffix, per sample
    ratio = [(r['suffix'] + r['redo'] + r['open']) / r['suffix'] for r in rs if r['suffix'] > 0]
    print(f'  proxy ratio (suffix elements + re-laid prefix boxes)/suffix elements: median {q(ratio,.5):.4f}, p90 {q(ratio,.9):.4f}, max {max(ratio):.4f}; samples above 2: {sum(1 for x in ratio if x>2)}')
    # smallest appended chunk for which the worst sample's extra work is within one suffix cost
    print(f'  largest re-laid prefix boxes {max(work)} => suffix >= {max(work)} elements keeps the worst observed sample within 2x')
for p in ['html5', 'ecma262', 'apollo11']:
    ps = [r for r in good if r['page'] == p]
    block(p + ' all', ps)
    for s in sorted({r['stratum'] for r in ps}):
        block(f'{p} / {s}', [r for r in ps if r['stratum'] == s])
block('ALL', good)
