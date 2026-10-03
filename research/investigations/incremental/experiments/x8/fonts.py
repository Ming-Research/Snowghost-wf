#!/usr/bin/env python3
"""Aggregate the driver's fonts-mode output: per CSS family, the share of scalars and paragraphs.
usage: fonts.py FONTS.tsv [--sets OUT.json]"""
import sys, json, collections
G = {}; C = {}; N = 0
for line in open(sys.argv[1], encoding='utf-8'):
    f = line.rstrip('\n').split('\t')
    if f[0] == 'G': G[int(f[1])] = dict(size=f[2], weight=f[3], style=f[4], fams=[x for x in f[5].split('|') if x])
    elif f[0] == 'C': C[int(f[1])] = tuple(int(x) for x in f[2:5])
    elif f[0] == 'N': N = int(f[1])
tot = sum(c[0] for c in C.values())
first = collections.defaultdict(lambda: [0, 0, 0, set()]); anyl = collections.defaultdict(lambda: [0, 0, 0, set()])
for g, (sc, pa, pf) in C.items():
    if sc == 0 and pa == 0: continue
    fams = G[g]['fams']
    if fams:
        r = first[fams[0]]; r[0] += sc; r[1] += pa; r[2] += pf; r[3].add(g)
    for fam in set(fams):
        r = anyl[fam]; r[0] += sc; r[1] += pa; r[2] += pf; r[3].add(g)
print(f'paragraphs {N}, scalars {tot}, font groups used {sum(1 for c in C.values() if c[0])} of {len(G)}')
print('family\tfirst-listed: scalars%\tparas with a run%\tany-listed: scalars%\tparas with a run (sum over groups)%')
sets = {}
rows = sorted(anyl.items(), key=lambda kv: -kv[1][0])
for fam, r in rows:
    fr = first.get(fam, [0, 0, 0, set()])
    print(f'{fam}\t{100*fr[0]/tot:.2f}\t{100*fr[1]/N:.2f}\t{100*r[0]/tot:.2f}\t{100*r[1]/N:.2f}\t(groups first {len(fr[3])}, any {len(r[3])})')
    sets[fam] = dict(first=sorted(fr[3]), any=sorted(r[3]), first_scalars=fr[0], any_scalars=r[0])
if len(sys.argv) > 3: json.dump(dict(paragraphs=N, scalars=tot, sets=sets), open(sys.argv[3], 'w'))
