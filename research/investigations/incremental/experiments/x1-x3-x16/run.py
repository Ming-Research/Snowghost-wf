"""Generates and runs the edits of X1/X3 for one page.
usage: python3 run.py PAGE [N_PER_KIND] [WORKERS]"""
import sys, os, re, json, random, time, traceback
from concurrent.futures import ThreadPoolExecutor
import lib
from lib import *

page = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 30
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
SEED = 20261002
rng = random.Random(SEED + sum(map(ord, page)))

html_path = D + '/' + page + '.html'
sheets = SHEETS[page]
os.makedirs(OUT + '/dumps', exist_ok=True)
os.makedirs(OUT + '/results', exist_ok=True)
os.makedirs(OUT + '/tmp', exist_ok=True)
os.makedirs(ROOT + '/build/x1', exist_ok=True)

text = open(ROOT + '/' + html_path, 'r', encoding='utf-8', errors='surrogateescape').read()
sheet_text = {k: open(ROOT + '/' + v, 'r', encoding='utf-8', errors='surrogateescape').read() for k, v in sheets.items()}

bl, bs_ = OUT + '/dumps/%s.base.l.tsv' % page, OUT + '/dumps/%s.base.s.tsv' % page
if not os.path.exists(bl):
    run_dump('layout_oracle', html_path, sheets, bl)
    run_dump('style_oracle', html_path, sheets, bs_)
BL = parse_layout(bl)
BS = parse_style(bs_)
BC = derive(BL, BS)
SRC = map_source(text, BL)
nel = len(BL.name)
print('%s: %d elements, %d source tags mapped, %d unmatched, %d text spans' %
      (page, nel, len(SRC.tags), SRC.unmatched, len(SRC.texts)), flush=True)

boxed = [i for i in range(nel) if BL.level[i] != 'n' and i in SRC.by_idx]
nchild = {}
for i in range(nel):
    nchild[BL.parent[i]] = nchild.get(BL.parent[i], 0) + 1

edits = []


def add(kind, ops, ins=None, target=None, sheet=None, meta=None):
    edits.append({'id': '%s-%03d' % (kind, sum(1 for e in edits if e['kind'] == kind)), 'kind': kind,
                  'ops': ops, 'ins': ins, 'target': target, 'sheet': sheet, 'meta': meta or {}})


# K1 / K2 text edits
sites = text_sites(text, SRC, BL, rng, N * 2)
for k, s in enumerate(sites[:N]):
    add('word', [(s['offset'], 0, rng.choice(WORDS) + ' ')], target={'parent': s['parent']})
for k, s in enumerate(sites[N:N * 2]):
    add('sentence', [(s['offset'], 0, SENTENCE[1:] + ' ')], target={'parent': s['parent']})

# K3 class edits: classes named by rules whose last compound is [tag].cls
css = '\n'.join(sheet_text.values())
for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I):
    css += '\n' + m.group(1)
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
LAYOUTISH = re.compile(r'(display|margin|padding|width|height|font-size|float|line-height|position|border|overflow|content)\s*:')
pool_all, pool_layout = [], []
for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
    sel, body = m.group(1), m.group(2)
    if '@' in sel or not body.strip():
        continue
    for one in sel.split(','):
        one = one.strip()
        mm = re.fullmatch(r'([A-Za-z][\w-]*)?((?:\.[\w-]+)+)', one)
        if not mm:
            continue
        tag = mm.group(1)
        for cls in mm.group(2).split('.')[1:]:
            pool_all.append((tag, cls))
            if LAYOUTISH.search(body):
                pool_layout.append((tag, cls))
by_tag = {}
for i in boxed:
    by_tag.setdefault(BL.name[i], []).append(i)
made = 0
tries = 0
used_tags = set()
while made < N and tries < N * 50:
    tries += 1
    pool = pool_layout if (made % 2 == 0 and pool_layout) else pool_all
    if not pool:
        break
    tag, cls = rng.choice(pool)
    cands = by_tag.get(tag.lower()) if tag else boxed
    if not cands:
        continue
    i = rng.choice(cands)
    if i in used_tags:
        continue
    t = SRC.by_idx[i]
    seg = text[t['start']:t['end']]
    if re.search(r'class\s*=\s*[^"\'\s]', seg):
        continue
    if re.search(r'[\s"\']%s[\s"\']' % re.escape(cls), seg):
        continue
    r = attr_insert(text, t, 'class', ' ' + cls, '')
    if r is None:
        continue
    off, ins_text = r
    if ins_text.startswith(' class="'):
        ins_text = ' class="%s"' % cls
    used_tags.add(i)
    add('class', [(off, 0, ins_text)], target={'elem': i}, meta={'cls': cls, 'tag': BL.name[i]})
    made += 1

# K4 inline color
for i in rng.sample(boxed, min(N, len(boxed))):
    t = SRC.by_idx[i]
    r = attr_insert(text, t, 'style', ';color:#c00', 'color:#c00')
    if r is None:
        continue
    add('color', [(r[0], 0, r[1])], target={'elem': i}, meta={'tag': BL.name[i]})

# K5 block insertion before a <p>
ps = [i for i in boxed if BL.name[i] == 'p' and BL.level[i] == 'b']
for i in rng.sample(ps, min(N, len(ps))):
    t = SRC.by_idx[i]
    add('block', [(t['start'], 0, BLOCK)], ins=(i, 1), target={'elem': i})

# K6 container font-size
desc = [0] * nel
for i in range(nel - 1, 0, -1):
    desc[BL.parent[i]] += 1 + desc[i]
conts = [i for i in boxed if BL.level[i] == 'b' and desc[i] >= 5 and nchild.get(i, 0) >= 3]
for i in rng.sample(conts, min(N, len(conts))):
    t = SRC.by_idx[i]
    r = attr_insert(text, t, 'style', ';font-size:130%', 'font-size:130%')
    if r is None:
        continue
    add('fontsize', [(r[0], 0, r[1])], target={'elem': i}, meta={'tag': BL.name[i], 'desc': desc[i]})

# K7 html font-size
html_tag = SRC.by_idx[0]
for v in ('12px', '20px', '24px'):
    r = attr_insert(text, html_tag, 'style', ';font-size:' + v, 'font-size:' + v)
    if r:
        add('rootfont', [(r[0], 0, r[1])], target={'elem': 0}, meta={'value': v})

# K8 custom properties
used = {}
for m in re.finditer(r'var\(\s*(--[\w-]+)\s*(?:,([^()]*(?:\([^()]*\)[^()]*)*))?\)', css + text):
    used.setdefault(m.group(1), m.group(2))
defs = []
for sk, st in sheet_text.items():
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', st):
        sel = m.group(1).strip()
        if ':root' in sel or sel.split(',')[-1].strip() == 'html' or sel.strip() == 'html':
            base = m.start(2)
            for d in re.finditer(r'(--[\w-]+)\s*:\s*([^;}]+)', m.group(2)):
                defs.append((sk, d.group(1), base + d.start(2), d.group(2)))


def newval(v):
    v = v.strip()
    m = re.fullmatch(r'(-?[\d.]+)(px|em|rem|%)', v)
    if m:
        return ('len', '%g%s' % (float(m.group(1)) * 1.5 + (1 if m.group(2) == 'px' else 0), m.group(2)))
    if re.fullmatch(r'#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|[a-z]+', v) and not v in ('none', 'auto', 'normal', 'inherit', 'initial'):
        return ('color', '#7a3b91')
    return None


cand_len, cand_other = [], []
seen = set()
for sk, name, off, val in defs:
    if name not in used or name in seen:
        continue
    nv = newval(val)
    if not nv:
        continue
    seen.add(name)
    (cand_len if nv[0] == 'len' else cand_other).append(('sheet', sk, name, off, len(val), nv[1], val.strip()))
for name, fb in used.items():
    if name in seen or fb is None:
        continue
    nv = newval(fb)
    if not nv:
        continue
    seen.add(name)
    (cand_len if nv[0] == 'len' else cand_other).append(('inline', None, name, None, None, nv[1], fb.strip()))
rng.shuffle(cand_len); rng.shuffle(cand_other)
pick = cand_len[:10] + cand_other[:max(0, 14 - min(10, len(cand_len)))]
for kindc, sk, name, off, ln, nv, old in pick:
    if kindc == 'sheet':
        add('custom', [(off, ln, nv)], sheet=sk, target={'elem': 0}, meta={'name': name, 'old': old, 'new': nv, 'where': 'root-def'})
    else:
        r = attr_insert(text, html_tag, 'style', ';%s:%s' % (name, nv), '%s:%s' % (name, nv))
        add('custom', [(r[0], 0, r[1])], target={'elem': 0}, meta={'name': name, 'old': old, 'new': nv, 'where': 'root-inline'})

print('%s: %d edits generated: %s' % (page, len(edits), {k: sum(1 for e in edits if e['kind'] == k) for k in sorted(set(e['kind'] for e in edits))}), flush=True)
print('custom candidates: len=%d other=%d used=%d defs=%d' % (len(cand_len), len(cand_other), len(used), len(defs)), flush=True)

resfile = os.environ.get('RESFILE') or OUT + '/results/%s.jsonl' % page
done = set()
if os.path.exists(resfile):
    for line in open(resfile):
        try:
            done.add(json.loads(line)['id'])
        except Exception:
            pass


def apply_ops(src, ops):
    for off, ln, t in sorted(ops, key=lambda o: -o[0]):
        src = src[:off] + t + src[off + ln:]
    return src


def do(e):
    tid = '%s-%s' % (page, e['id'])
    try:
        shs = dict(sheets)
        hp = html_path
        if e['sheet']:
            sp = 'build/x1/%s.css' % tid
            with open(ROOT + '/' + sp, 'w', encoding='utf-8', errors='surrogateescape') as f:
                f.write(apply_ops(sheet_text[e['sheet']], e['ops']))
            shs[e['sheet']] = sp
        else:
            hp = 'build/x1/%s.html' % tid
            with open(ROOT + '/' + hp, 'w', encoding='utf-8', errors='surrogateescape') as f:
                f.write(apply_ops(text, e['ops']))
        lp = OUT + '/tmp/%s.l.tsv' % tid
        sp_ = OUT + '/tmp/%s.s.tsv' % tid
        run_dump('layout_oracle', hp, shs, lp)
        run_dump('style_oracle', hp, shs, sp_)
        AL = parse_layout(lp)
        AS = parse_style(sp_)
        if os.environ.get('DBGID') == e['id']:
            lib.DBG = []
        res = analyze(BL, BS, AL, AS, ins=e['ins'], target=e['target'], kind=e['kind'], B=BC)
        if lib.DBG is not None:
            print('\n'.join(map(str, lib.DBG)))
        res['id'] = e['id']; res['kind'] = e['kind']; res['meta'] = e['meta']; res['page'] = page
        res['H_before'] = BL.H; res['H_after'] = AL.H
        for p in (lp, sp_, ROOT + '/' + hp if not e['sheet'] else ROOT + '/' + shs[e['sheet']]):
            try:
                os.remove(p)
            except OSError:
                pass
        return res
    except Exception as ex:
        return {'id': e['id'], 'kind': e['kind'], 'page': page, 'valid': False, 'why': 'exception ' + repr(ex) + traceback.format_exc()[-300:]}


todo = [e for e in edits if e['id'] not in done]
todo = todo[:int(os.environ.get('CHUNK', '100000'))]
if os.environ.get('ONLY'):
    todo = [e for e in edits if e['id'] == os.environ['ONLY']]
print('%d edits to run' % len(todo), flush=True)
t0 = time.time()
with open(resfile, 'a') as out, ThreadPoolExecutor(WORKERS) as ex:
    for k, res in enumerate(ex.map(do, todo)):
        out.write(json.dumps(res) + '\n')
        out.flush()
        if k % 10 == 0:
            print('  %d/%d done, %.0fs, last %s valid=%s %s' % (k + 1, len(todo), time.time() - t0, res['id'], res.get('valid'), res.get('why', '')), flush=True)
print('finished %s in %.0fs' % (page, time.time() - t0), flush=True)
