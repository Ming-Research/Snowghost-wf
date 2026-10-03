#!/usr/bin/env python3
"""Random and stratified append points. usage: sample.py PAGE NUNIFORM NSTRATUM SEED  -> samples-PAGE.jsonl
For each chosen element c the page's HTML is cut before c's start tag, dumped (layout and style) and
the prefix elements (index < c) are compared with the full page's dumps."""
import sys, re, json, random, subprocess, collections, os
page, nuni, nstr, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
OUTSUF = sys.argv[5] if len(sys.argv) > 5 else ''   # resumed run: output suffix
ONLY = sys.argv[6].split(',') if len(sys.argv) > 6 else None   # resumed run: only these strata
ROOT = '/home/user/sg-text'
X = os.path.dirname(os.path.abspath(__file__))
data = 'build/research/concurrency'
sheets = {'ecma262': [f'assets/css/ecmarkup.css={data}/ecma262-ecmarkup.css', f'assets/css/print.css={data}/ecma262-print.css'],
          'html5': [],
          'apollo11': [f'wikibase.client.init&only=styles&skin=vector-2022={data}/apollo11-modules.css', f'modules=site.styles&only=styles&skin=vector-2022={data}/apollo11-site.css']}[page]
srcpath = f'{ROOT}/{data}/{page}.html'

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
        elif f[0] == 'H': H = float(f[1])
    return E, T, H
def load_style(path):
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8')]
    el = [r for r in rows[1:] if not r[1].startswith('::')]
    ps = {(int(r[0]), r[1]): r for r in rows[1:] if r[1].startswith('::')}
    return rows[0], el, ps
def box(rects):
    x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects); y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)
def near(a, b): return abs(a - b) <= 1e-6

FE, FT, FH = load_layout(f'{X}/dumps/{page}.full.layout.tsv')
hdr, FS, FP = load_style(f'{X}/dumps/{page}.full.style.tsv')
col = {h: i for i, h in enumerate(hdr)}
n = len(FE)
assert len(FS) == n, (len(FS), n)
src = open(srcpath, encoding='utf-8', errors='surrogateescape').read()
pat = re.compile(r'<!--.*?-->|<(script|style|template|textarea|title)\b[^>]*>.*?</\1\s*>|<([a-zA-Z][a-zA-Z0-9:._-]*)', re.S | re.I)
tags = []
for m in pat.finditer(src):
    if m.group(1): tags.append((m.group(1).lower(), m.start()))
    elif m.group(2): tags.append((m.group(2).lower(), m.start()))
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
    """The kind of the deepest shrink-to-fit-like or table/flex/grid ancestor: table, float, flexgrid, inline-block, abspos."""
    for a in anc_of(c):
        d = disp(a); r = FS[a]
        if d.startswith('table') or d == 'inline-table': return {'table'}
        if r[col['float']] != 'none': return {'float'}
        if d in ('flex', 'inline-flex', 'grid', 'inline-grid'): return {'flexgrid'}
        if d == 'inline-block': return {'inline-block'}
        if r[col['position']] in ('absolute', 'fixed'): return {'abspos'}
    return {'plain'}
rnd = random.Random(seed)
cands = [c for c in range(200, n - 50) if off[c] is not None and FE[c][2] != 'n' or False]
cands = [c for c in range(200, n - 50) if off[c] is not None]
chosen = [('uniform', c) for c in rnd.sample(cands, nuni)]
strata = collections.defaultdict(list)
for c in cands:
    for s in strata_of(c): strata[s].append(c)
for s, lst in sorted(strata.items()):
    if ONLY is not None and s not in ONLY: continue
    for c in rnd.sample(lst, min(nstr, len(lst))): chosen.append((s, c))
print(page, 'strata sizes', {k: len(v) for k, v in strata.items()}, file=sys.stderr)

def run(cmd, outp):
    with open(outp, 'w') as f:
        r = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.PIPE)
    return r.returncode
out = open(f'{X}/samples-{page}{OUTSUF}.jsonl', 'w')
tmp = f'{ROOT}/build/x8s-{page}{OUTSUF}.html'
for k, (stratum, c) in enumerate(chosen):
    open(tmp, 'w', encoding='utf-8', errors='surrogateescape').write(src[:off[c]])
    lt = f'{X}/dumps/s-{page}{OUTSUF}.layout.tsv'; st = f'{X}/dumps/s-{page}{OUTSUF}.style.tsv'
    rc1 = run(['build/layout_oracle', 'dump', '1', f'build/x8s-{page}{OUTSUF}.html', 'renderer/style/ua.css'] + sheets, lt)
    rc2 = run(['build/style_oracle', 'dump', '1', f'build/x8s-{page}{OUTSUF}.html', 'renderer/style/ua.css'] + sheets, st)
    TE, TT, TH = load_layout(lt); thdr, TS, TP = load_style(st)
    m = len(TE)
    rec = dict(page=page, stratum=stratum, cut=c, cut_name=FE[c][0], frac=c / n, rc=[rc1, rc2], trunc_elements=m, trunc_style_rows=len(TS))
    if m != c or len(TS) != c or any((FE[i][0], FE[i][1]) != (TE[i][0], TE[i][1]) for i in range(m)):
        rec['skipped'] = 'structure'; out.write(json.dumps(rec) + '\n'); out.flush(); continue
    anc = set(anc_of(c))
    rec['open_ancestors'] = len(anc)
    rec['anc_displays'] = [disp(a) for a in anc_of(c)][:6]
    # nearest open ancestor of each element: the deepest ancestor-or-self in anc, computed by walking up
    def lca(i):
        p = i
        while p >= 0 and p not in anc: p = FE[p][1]
        return p
    def nearest_box(E, i):
        p = E[i][1]
        while p >= 0:
            if E[p][3]: return box(E[p][3])
            p = E[p][1]
        return (0, 0, 0, 0)
    cls = collections.Counter(); causes = collections.Counter(); changed = []
    boxes = 0
    for i in range(c):
        fn, fp, fl, fr = FE[i]; tn, tp, tl, tr = TE[i]
        if fr: boxes += 1
        if fl != tl: k_ = 'level'
        elif not fr and not tr: k_ = 'nobox'
        elif len(fr) != len(tr): k_ = 'rect_count'
        else:
            ss = all(near(a[2], b[2]) and near(a[3], b[3]) for a, b in zip(fr, tr))
            sp = all(near(a[0], b[0]) and near(a[1], b[1]) for a, b in zip(fr, tr))
            if ss and sp: k_ = 'same'
            elif ss:
                fb = box(fr); tb = box(tr); fpb = nearest_box(FE, i); tpb = nearest_box(TE, i)
                k_ = 'moved_rel_same' if near(fb[0] - fpb[0], tb[0] - tpb[0]) and near(fb[1] - fpb[1], tb[1] - tpb[1]) else 'moved_rel_changed'
            else:
                fb = box(fr); tb = box(tr)
                k_ = 'resized_w' if not near(fb[2], tb[2]) else 'resized_h'
                if not near(fb[2], tb[2]) and not near(fb[3], tb[3]): k_ = 'resized_wh'
        if i in anc: cls['open_' + k_] += 1; continue
        cls[k_] += 1
        if k_ not in ('same', 'nobox', 'moved_rel_same'):
            a = lca(i)
            ad = disp(a) if a >= 0 else 'none'
            ar = FS[a] if a >= 0 else None
            cause = 'lca:' + ad
            if ar is not None:
                if ar[col['float']] != 'none': cause += '+float'
                if ar[col['position']] in ('absolute', 'fixed'): cause += '+abs'
            changed.append((i, FE[i][0], k_, disp(i), a, ad))
            causes[(k_, cause, disp(i))] += 1
    rec['boxes'] = boxes
    rec['classes'] = dict(cls)
    rec['changed_nonopen'] = len(changed)
    rec['causes'] = [[list(k_), v] for k_, v in causes.most_common(12)]
    rec['changed_first'] = changed[:3]
    # text and paragraphs
    tcls = collections.Counter(); paras = set(); relaid = set()
    for o, (par, fr) in FT.items():
        if par >= c: continue
        if o not in TT: tcls['missing'] += 1; continue
        q = par
        while q >= 0 and FE[q][2] != 'b': q = FE[q][1]
        tr = TT[o][1]
        if len(fr) != len(tr): k_ = 'frag_count'
        elif all(near(a[2], b[2]) and near(a[3], b[3]) for a, b in zip(fr, tr)):
            k_ = 'same' if all(near(a[0], b[0]) and near(a[1], b[1]) for a, b in zip(fr, tr)) else 'moved'
        else: k_ = 'frag_resized'
        tcls[k_] += 1
        paras.add(q)
        if k_ in ('frag_count', 'frag_resized') and q not in anc: relaid.add(q)
    rec['text'] = dict(tcls); rec['paragraphs'] = len(paras); rec['paragraphs_relaid_nonopen'] = len(relaid)
    # style
    sd = collections.Counter(); srows = 0; sex = []
    for i in range(c):
        a = FS[i]; b = TS[i]
        diff = [hdr[x] for x in range(len(hdr)) if a[x] != b[x]]
        if diff:
            if i in anc: sd['open'] += 1; continue
            srows += 1
            for d in diff: sd[d] += 1
            sex.append((i, FE[i][0], diff))
    pseudo_changed = 0; pseudo_total = 0
    for key, a in FP.items():
        if key[0] >= c: continue
        pseudo_total += 1
        b = TP.get(key)
        if key[0] in anc: continue
        if b is None or a != b: pseudo_changed += 1
    rec['pseudo_rows'] = pseudo_total; rec['pseudo_changed_nonopen'] = pseudo_changed
    rec['style_changed_nonopen_rows'] = srows; rec['style_cols'] = dict(sd); rec['style_examples'] = sex[:3]
    rec['height_full'] = FH; rec['height_trunc'] = TH
    out.write(json.dumps(rec) + '\n'); out.flush()
