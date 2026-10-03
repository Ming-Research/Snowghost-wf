#!/usr/bin/env python3
"""Compare the prefix elements of a truncated page's layout and style dumps with the full page's.
usage: prefix.py FULL_LAYOUT TRUNC_LAYOUT FULL_STYLE TRUNC_STYLE CUT_ELEMENT  -> JSON-ish summary on stdout"""
import sys, collections, json

def load_layout(path):
    E = []; T = {}; H = None
    for line in open(path, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if f[0] == 'E':
            rects = [tuple(float(v) for v in r.split(',')) for r in f[5].split(' ')] if len(f) > 5 and f[5] else []
            E.append((f[2], int(f[3]), f[4], rects))
        elif f[0] == 'T':
            rects = [tuple(float(v) for v in r.split(',')) for r in f[3].split(' ')] if len(f) > 3 and f[3] else []
            T[int(f[1])] = (int(f[2]), rects)
        elif f[0] == 'H':
            H = float(f[1])
    return E, T, H

def load_style(path):
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8')]
    return rows[0], rows[1:]

def box(rects):
    if not rects: return None
    x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects); y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)

def near(a, b, eps=1e-6):
    return abs(a - b) <= eps

fullL, trL, fullS, trS, cut = sys.argv[1:6]
cut = int(cut)
FE, FT, FH = load_layout(fullL)
TE, TT, TH = load_layout(trL)
m = len(TE)
res = collections.OrderedDict()
res['elements_full'] = len(FE); res['elements_trunc'] = m; res['cut_element'] = cut
bad = sum(1 for i in range(m) if (FE[i][0], FE[i][1]) != (TE[i][0], TE[i][1]))
res['structure_mismatches'] = bad
res['height_full'] = FH; res['height_trunc'] = TH
# ancestors of the cut element in the full tree (open at the cut)
anc = set(); p = FE[cut][1]
while p >= 0: anc.add(p); p = FE[p][1]
res['open_ancestors'] = len(anc)
def nearest_box(E, i):
    p = E[i][1]
    while p >= 0:
        if E[p][3]: return box(E[p][3])
        p = E[p][1]
    return (0, 0, 0, 0)
cls = collections.Counter()
changed = []
for i in range(min(m, cut)):
    fn, fp, fl, fr = FE[i]; tn, tp, tl, tr = TE[i]
    if fl != tl:
        k = 'level'
    elif not fr and not tr:
        k = 'nobox'
    elif len(fr) != len(tr):
        k = 'rect_count'
    else:
        same_size = all(near(a[2], b[2]) and near(a[3], b[3]) for a, b in zip(fr, tr))
        same_pos = all(near(a[0], b[0]) and near(a[1], b[1]) for a, b in zip(fr, tr))
        if same_size and same_pos: k = 'same'
        elif same_size:
            # position relative to the nearest ancestor with a box
            fb = box(fr); tb = box(tr); fpb = nearest_box(FE, i); tpb = nearest_box(TE, i)
            rel_same = near(fb[0] - fpb[0], tb[0] - tpb[0]) and near(fb[1] - fpb[1], tb[1] - tpb[1])
            k = 'moved_rel_same' if rel_same else 'moved_rel_changed'
        else:
            fb = box(fr); tb = box(tr)
            k = 'resized_w' if not near(fb[2], tb[2]) else 'resized_h'
            if not near(fb[2], tb[2]) and not near(fb[3], tb[3]): k = 'resized_wh'
    if i in anc: k = 'open_' + k
    cls[k] += 1
    if k not in ('same', 'nobox', 'moved_rel_same') and not k.startswith('open_'):
        changed.append((i, FE[i][0], k))
res['classes'] = dict(cls)
res['prefix_boxes'] = sum(v for k, v in cls.items() if k != 'nobox' and k != 'open_nobox')
res['changed_nonopen'] = len(changed)
json.dump(res, sys.stdout, indent=1); print()
# text nodes
tcls = collections.Counter(); para_changed = set(); paras = set()
tn = 0
for o, (par, fr) in FT.items():
    if o not in TT:
        # not in truncated: only fine if beyond prefix
        if par < cut: tcls['missing_in_trunc'] += 1
        continue
    if par >= cut: continue
    tp_, tr = TT[o]
    # paragraph key: nearest block-level ancestor
    q = par
    while q >= 0 and FE[q][2] != 'b': q = FE[q][1]
    paras.add(q)
    if len(fr) != len(tr): k = 'frag_count'
    elif all(near(a[2], b[2]) and near(a[3], b[3]) for a, b in zip(fr, tr)):
        k = 'same' if all(near(a[0], b[0]) and near(a[1], b[1]) for a, b in zip(fr, tr)) else 'moved'
    else: k = 'frag_resized'
    tcls[k] += 1
    if k in ('frag_count', 'frag_resized'): para_changed.add(q)
res_t = dict(text_nodes=sum(tcls.values()), classes=dict(tcls), paragraphs=len(paras), paragraphs_relaid=len(para_changed))
print(json.dumps(res_t))
# changed element dump for classification
with open(sys.argv[6] if len(sys.argv) > 6 else '/dev/null', 'w') as f:
    for i, n, k in changed: f.write(f'{i}\t{n}\t{k}\n')
# style compare
import os
if not (os.path.isfile(trS) and os.path.getsize(trS) > 0): sys.exit(0)
hdr, FS = load_style(fullS); hdr2, TS = load_style(trS)
sd = collections.Counter(); srows = 0; sopen = collections.Counter(); sother = []
for i in range(min(len(TS), cut)):
    a = FS[i]; b = TS[i]
    diff = [hdr[c] for c in range(len(hdr)) if a[c] != b[c]]
    if diff:
        srows += 1
        for c in diff: (sopen if i in anc else sd)[c] += 1
        if i not in anc: sother.append((i, a[1], diff))
print(json.dumps(dict(style_rows_trunc=len(TS), style_rows_changed=srows, changed_columns_nonopen=dict(sd), changed_columns_open=dict(sopen), examples=sother[:8])))
