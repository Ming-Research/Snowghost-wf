#!/usr/bin/env python3
"""Chunk appends. usage: chunk.py PAGE NUNIFORM NSTRATUM SEED OUT.jsonl [K,K,...]
For cut elements c chosen as in sample.py (uniform and by stratum), the page's HTML cut before c's start tag
(prefix P_c) is laid out, and so is the page cut before the first element at or after c+K (prefix P_c'), for
each chunk size K in elements (default 20,200,2000).  The elements of P_c (index < c) are compared between the two
dumps: what an append of K elements changes in what was already laid out."""
import sys, re, json, random, subprocess, collections, os
page, nuni, nstr, seed, outfn = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
KS = [int(k) for k in sys.argv[6].split(',')] if len(sys.argv) > 6 else [20, 200, 2000]
ROOT = '/home/user/sg-text'
X = os.path.dirname(os.path.abspath(__file__))
data = 'build/research/concurrency'
sheets = {'ecma262': [f'assets/css/ecmarkup.css={data}/ecma262-ecmarkup.css', f'assets/css/print.css={data}/ecma262-print.css'],
          'html5': [],
          'apollo11': [f'wikibase.client.init&only=styles&skin=vector-2022={data}/apollo11-modules.css', f'modules=site.styles&only=styles&skin=vector-2022={data}/apollo11-site.css']}[page]
src = open(f'{ROOT}/{data}/{page}.html', encoding='utf-8', errors='surrogateescape').read()
def load_layout(path):
    E = []; T = {}
    for line in open(path, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if f[0] == 'E':
            rects = [tuple(float(v) for v in r.split(',')) for r in f[5].split(' ')] if len(f) > 5 and f[5] else []
            E.append((f[2], int(f[3]), f[4], rects))
        elif f[0] == 'T':
            rects = [tuple(float(v) for v in r.split(',')) for r in f[3].split(' ')] if len(f) > 3 and f[3] else []
            T[int(f[1])] = (int(f[2]), rects)
    return E, T
def load_style(path):
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8')]
    return rows[0], [r for r in rows[1:] if not r[1].startswith('::')]
def box(rects):
    x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects); y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)
def near(a, b): return abs(a - b) <= 1e-6
FE, FT = load_layout(f'{X}/dumps/{page}.full.layout.tsv')
hdr, FS = load_style(f'{X}/dumps/{page}.full.style.tsv')
col = {h: i for i, h in enumerate(hdr)}
n = len(FE)
pat = re.compile(r'<!--.*?-->|<(script|style|template|textarea|title)\b[^>]*>.*?</\1\s*>|<([a-zA-Z][a-zA-Z0-9:._-]*)', re.S | re.I)
tags = [((m.group(1) or m.group(2)).lower(), m.start()) for m in pat.finditer(src) if m.group(1) or m.group(2)]
off = [None]*n; j = 0; pending = []
for i, (nm, par, lv, rc) in enumerate(FE):
    ln = nm.lower()
    if j < len(tags) and tags[j][0] == ln: off[i] = tags[j][1]; j += 1; continue
    hit = None
    for q in pending[-8:]:
        if tags[q][0] == ln: hit = q; break
    if hit is not None: off[i] = tags[hit][1]; pending.remove(hit); continue
    for d in range(1, 9):
        if j + d < len(tags) and tags[j + d][0] == ln:
            pending.extend(range(j, j + d)); off[i] = tags[j + d][1]; j += d + 1; break
def anc_of(i):
    out = []; p = FE[i][1]
    while p >= 0: out.append(p); p = FE[p][1]
    return out
def disp(i): return FS[i][col['display']]
def strata_of(c):
    for a in anc_of(c):
        d = disp(a); r = FS[a]
        if d.startswith('table') or d == 'inline-table': return 'table'
        if r[col['float']] != 'none': return 'float'
        if d in ('flex', 'inline-flex', 'grid', 'inline-grid'): return 'flexgrid'
        if d == 'inline-block': return 'inline-block'
        if r[col['position']] in ('absolute', 'fixed'): return 'abspos'
    return 'plain'
rnd = random.Random(seed)
maxk = max(KS)
cands = [c for c in range(200, n - maxk - 100) if off[c] is not None]
chosen = [('uniform', c) for c in rnd.sample(cands, nuni)]
strata = collections.defaultdict(list)
for c in cands: strata[strata_of(c)].append(c)
for s, lst in sorted(strata.items()):
    if s == 'plain': continue
    for c in rnd.sample(lst, min(nstr, len(lst))): chosen.append((s, c))
print(page, 'strata sizes', {k: len(v) for k, v in strata.items()}, file=sys.stderr, flush=True)
def dump_prefix(e, tag):
    path = f'{ROOT}/build/x8c-{page}-{tag}.html'
    open(path, 'w', encoding='utf-8', errors='surrogateescape').write(src[:off[e]])
    lt = f'{X}/dumps/c-{page}-{tag}.layout.tsv'
    with open(lt, 'w') as f:
        r = subprocess.run(['build/layout_oracle', 'dump', '1', f'build/x8c-{page}-{tag}.html', 'renderer/style/ua.css'] + sheets, cwd=ROOT, stdout=f, stderr=subprocess.PIPE)
    if r.returncode: return None
    return load_layout(lt)
out = open(outfn, 'w')
for stratum, c in chosen:
    base = dump_prefix(c, 'a')
    if base is None or len(base[0]) != c: out.write(json.dumps(dict(page=page, stratum=stratum, cut=c, skipped='base')) + '\n'); continue
    BE, BT = base
    for K in KS:
        e = c + K
        while e < n and off[e] is None: e += 1
        if e >= n: continue
        aft = dump_prefix(e, 'b')
        rec = dict(page=page, stratum=stratum, cut=c, cut_name=FE[c][0], K=e - c)
        if aft is None or len(aft[0]) != e or any((BE[i][0], BE[i][1]) != (aft[0][i][0], aft[0][i][1]) for i in range(c)):
            rec['skipped'] = 'structure'; out.write(json.dumps(rec) + '\n'); out.flush(); continue
        AE, AT = aft
        # open ancestors of element c in the later tree: the elements still being filled when the first chunk ended
        anc = set(); p = AE[c][1] if c < len(AE) else -1
        while p >= 0: anc.add(p); p = AE[p][1]
        cls = collections.Counter()
        def nearest_box(E, i):
            p = E[i][1]
            while p >= 0:
                if E[p][3]: return box(E[p][3])
                p = E[p][1]
            return (0, 0, 0, 0)
        for i in range(c):
            fr = AE[i][3]; tr = BE[i][3]
            if AE[i][2] != BE[i][2]: k_ = 'level'
            elif not fr and not tr: k_ = 'nobox'
            elif len(fr) != len(tr): k_ = 'rect_count'
            else:
                ss = all(near(a[2], b[2]) and near(a[3], b[3]) for a, b in zip(fr, tr))
                sp = all(near(a[0], b[0]) and near(a[1], b[1]) for a, b in zip(fr, tr))
                if ss and sp: k_ = 'same'
                elif ss:
                    fb = box(fr); tb = box(tr); fpb = nearest_box(AE, i); tpb = nearest_box(BE, i)
                    k_ = 'moved_rel_same' if near(fb[0] - fpb[0], tb[0] - tpb[0]) and near(fb[1] - fpb[1], tb[1] - tpb[1]) else 'moved_rel_changed'
                else:
                    fb = box(fr); tb = box(tr)
                    k_ = 'resized_w' if not near(fb[2], tb[2]) else 'resized_h'
                    if not near(fb[2], tb[2]) and not near(fb[3], tb[3]): k_ = 'resized_wh'
            cls[('open_' if i in anc else '') + k_] += 1
        redo = sum(v for k, v in cls.items() if not k.startswith('open_') and k not in ('same', 'nobox', 'moved_rel_same'))
        tcls = collections.Counter(); relaid = set()
        for o, (par, fr) in AT.items():
            if par >= c or o not in BT: continue
            tr = BT[o][1]
            if len(fr) != len(tr): k_ = 'frag_count'
            elif all(near(a[2], b[2]) and near(a[3], b[3]) for a, b in zip(fr, tr)):
                k_ = 'same' if all(near(a[0], b[0]) and near(a[1], b[1]) for a, b in zip(fr, tr)) else 'moved'
            else: k_ = 'frag_resized'
            tcls[k_] += 1
            if k_ in ('frag_count', 'frag_resized'):
                q = par
                while q >= 0 and AE[q][2] != 'b': q = AE[q][1]
                if q not in anc: relaid.add(q)
        rec.update(open_ancestors=len(anc), classes=dict(cls), redo=redo, rigid=cls.get('moved_rel_same', 0),
                   text=dict(tcls), paragraphs_relaid_nonopen=len(relaid))
        out.write(json.dumps(rec) + '\n'); out.flush()
