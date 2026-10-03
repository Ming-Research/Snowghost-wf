#!/usr/bin/env python3
"""X4 analysis: do a paragraph's line breaks hold when the viewport width changes?
usage: analyze.py PAGE DIR   (DIR holds PAGE.W.tsv, the driver's dump at viewport width W px; base 1280)

A paragraph is a block-level box (nearest non-inline ancestor of its text nodes).  Its signature at a width is the
fragment rectangles of its text nodes (keyed by text-node ordinal; a node with no fragment is absent) and of the
inline elements inside it.  Two signatures are the same when they have the same keys and the same number of
fragments/rects with widths within TOL px (a different break gives a different fragment count or width).  So
'holds' means: every text node and inline box of the paragraph is cut into the same pieces.
Container-changed: the paragraph's own block box changed width between the two viewport widths (it has an
available inline size that differs); the others are unaffected by construction (fixed-width or centred containers).
Weights: paragraphs counted once, or by their number of text fragments at the base width (a proxy for text work)."""
import sys, os, re
page, d = sys.argv[1], sys.argv[2]
TOL = 0.02
BASE = 1280
def load(path):
    E, T = {}, {}
    for line in open(path):
        f = line.rstrip('\n').split('\t')
        if f[0] == 'E':
            rects = [tuple(map(float, r.split(','))) for r in f[5].split()] if len(f) > 5 and f[5] else []
            E[int(f[1])] = (int(f[3]), f[4], rects)
        elif f[0] == 'T':
            rects = [tuple(map(float, r.split(','))) for r in f[3].split()] if len(f) > 3 and f[3] else []
            T[int(f[1])] = (int(f[2]), rects)
    return E, T
widths = sorted(int(m.group(1)) for fn in os.listdir(d) if (m := re.fullmatch(re.escape(page) + r'\.(\d+)\.tsv', fn)))
data = {w: load(f'{d}/{page}.{w}.tsv') for w in widths}
E0, T0 = data[BASE]
def block_of(p, E):
    while p >= 0 and E[p][1] == 'i': p = E[p][0]
    return p
para_t = {}; para_i = {}
for o, (p, r) in T0.items(): para_t.setdefault(block_of(p, E0), []).append(o)
for i, (par, lvl, rects) in E0.items():
    if lvl == 'i': 
        b = block_of(par, E0)
        if b in para_t: para_i.setdefault(b, []).append(i)
# text nodes that exist only at other widths (whitespace that collapses at a line end at base but not elsewhere)
extra = {}
for w, (E, T) in data.items():
    for o, (p, r) in T.items():
        if o not in T0: extra.setdefault(block_of(p, E0), set()).add(o)
def eqr(a, b): return len(a) == len(b) and all(abs(x[2] - y[2]) <= TOL for x, y in zip(a, b))
def holds(w, b):
    E, T = data[w]
    for o in para_t[b]:
        if o not in T or not eqr(T[o][1], T0[o][1]): return False
    for o in extra.get(b, ()):
        if o in T: return False
    for i in para_i.get(b, ()):
        if not eqr(E[i][2], E0[i][2]): return False
    return True
def bw(E, b):
    r = E[b][2]
    return max(x[0] + x[2] for x in r) - min(x[0] for x in r) if r else None
blocks = list(para_t)
frag = {b: sum(len(T0[o][1]) for o in para_t[b]) for b in blocks}
multi = {b: any(len(T0[o][1]) > 1 for o in para_t[b]) or any(len(E0[i][2]) > 1 for i in para_i.get(b, ())) for b in blocks}
ntext = len(T0); nmulti = sum(multi.values())
print(f'# {page}: {len(E0)} elements, {ntext} text nodes with fragments, {len(blocks)} paragraphs ({nmulti} multi-line), {sum(frag.values())} fragments; widths {widths}')
def pct(a, b): return f'{a}/{b} ({100*a/b:.1f}%)' if b else f'{a}/0'
print('delta | all paragraphs hold | multi-line hold | container-changed hold | container-changed multi-line hold | fragment-weighted: all, container-changed')
summary = {}
for w in widths:
    if w == BASE: continue
    E, T = data[w]
    ch = [b for b in blocks if bw(E0, b) is not None and bw(E, b) is not None and abs(bw(E0, b) - bw(E, b)) > TOL]
    chs = set(ch)
    H = {b: holds(w, b) for b in blocks}
    a = sum(H.values()); am = sum(H[b] for b in blocks if multi[b])
    c = sum(H[b] for b in ch); cm = sum(H[b] for b in ch if multi[b])
    nm_ch = sum(1 for b in ch if multi[b])
    fw_all = sum(frag[b] for b in blocks if H[b]); fw_ch = sum(frag[b] for b in ch if H[b])
    print(f'{w-BASE:+5d} | {pct(a,len(blocks))} | {pct(am,nmulti)} | {pct(c,len(ch))} | {pct(cm,nm_ch)} | {pct(fw_all,sum(frag.values()))}, {pct(fw_ch,sum(frag[b] for b in ch))}')
    summary[w - BASE] = (a, len(blocks), c, len(ch), cm, nm_ch)
# hold interval: for each paragraph, the widest contiguous (from base outward) run of sampled viewport widths at which it holds
print('\nhold interval in viewport px, over paragraphs whose container changes at the extreme samples (first failing sample bounds it):')
for name, ws in (('shrink', sorted((w for w in widths if w < BASE), reverse=True)), ('grow', sorted(w for w in widths if w > BASE))):
    ext = ws[-1]; E, _ = data[ext]
    chb = [b for b in blocks if bw(E0, b) is not None and bw(E, b) is not None and abs(bw(E0, b) - bw(E, b)) > TOL]
    lim = []
    for b in chb:
        last = 0
        for w in ws:
            if holds(w, b): last = abs(w - BASE)
            else: break
        else: last = None   # held at every sampled width
        lim.append(last)
    n = len(lim)
    srt = sorted(x for x in lim if x is not None)
    print(f'  {name}: {n} container-changed paragraphs at {ext-BASE:+d}; held through all samples: {sum(1 for x in lim if x is None)}; '
          f'failed within samples: {len(srt)}; of those, largest held delta median {srt[len(srt)//2] if srt else "-"} px, p25 {srt[len(srt)//4] if srt else "-"}, p75 {srt[3*len(srt)//4] if srt else "-"}')
    for lo in (1, 5, 10, 20, 50):
        k = sum(1 for x in lim if x is None or x >= lo)
        print(f'     holds at least {lo} px: {pct(k, n)}')

# the criterion is about a 10 px resize of the container: show by how much the paragraph blocks really change at viewport +-10
import collections
print('\nviewport +-10 px: the most common block width changes (container-changed paragraphs), with how many of them hold:')
for w in (BASE - 10, BASE + 10):
    if w not in data: continue
    E, _ = data[w]
    by = collections.defaultdict(list)
    for b in blocks:
        a, c = bw(E0, b), bw(E, b)
        if a is None or c is None or abs(a - c) <= TOL: continue
        by[round(abs(a - c), 1)].append(b)
    for dl, bs in sorted(by.items(), key=lambda kv: -len(kv[1]))[:3]:
        h = sum(holds(w, b) for b in bs); m = [b for b in bs if multi[b]]; hm = sum(holds(w, b) for b in m)
        print(f'  viewport {w-BASE:+d}: block width changes by {dl} px for {len(bs)} paragraphs: hold {pct(h, len(bs))}; multi-line {pct(hm, len(m))}')
