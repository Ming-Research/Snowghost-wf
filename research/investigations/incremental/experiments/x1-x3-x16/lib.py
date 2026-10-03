"""Shared code of the X1/X3/X15 experiments: dump parsing, HTML source mapping,
edit generation, and the per-edit analysis.  Python 3 standard library only."""
import re, math, random, os, subprocess

ROOT = '/home/user/sg-apollo'
OUT = '/tmp/claude-0/-home-user-Whitefoot/c1798ad6-8464-510f-9e4e-0b06f37af459/scratchpad/incr/exp/x1x3'
D = 'build/research/concurrency'
UA = 'renderer/style/ua.css'

SHEETS = {
    'ecma262': {'assets/css/ecmarkup.css': D + '/ecma262-ecmarkup.css',
                'assets/css/print.css': D + '/ecma262-print.css'},
    'html5': {},
    'apollo11': {'wikibase.client.init&only=styles&skin=vector-2022': D + '/apollo11-modules.css',
                 'modules=site.styles&only=styles&skin=vector-2022': D + '/apollo11-site.css'},
}

PAINT_ONLY = {'color', 'background-color', 'border-top-color', 'border-right-color',
              'border-bottom-color', 'border-left-color', 'visibility', 'text-decoration-line', 'z-index'}

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param',
        'source', 'track', 'wbr', 'basefont', 'bgsound', 'frame', 'keygen'}
RAW = {'script', 'style', 'textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes'}
IMPLIED = {'html', 'head', 'body', 'tbody', 'thead', 'tfoot', 'colgroup', 'tr'}
INLINE_DISP = {'inline', 'contents', 'ruby', 'ruby-text', 'ruby-base', 'ruby-text-container',
               'ruby-base-container'}
FLEXGRID = {'flex', 'inline-flex', 'grid', 'inline-grid'}
ROOT_DISP = {'inline-block', 'inline-flex', 'inline-grid', 'inline-table', 'table', 'flow-root',
             'table-cell', 'table-caption', 'flex', 'grid', 'table-row', 'table-row-group',
             'table-header-group', 'table-footer-group'}


# ---------------------------------------------------------------- dumps

def parse_rects(s):
    if not s:
        return []
    out = []
    for r in s.split(' '):
        x, y, w, h = r.split(',')
        out.append((float(x), float(y), float(w), float(h)))
    return out


class Layout:
    pass


def parse_layout(path):
    L = Layout()
    L.name, L.parent, L.level, L.rects = [], [], [], []
    L.T = []  # (ordinal, parent, rects)
    L.H = None
    with open(path, 'r', encoding='utf-8', errors='surrogateescape') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('E\t'):
                p = line.split('\t')
                L.name.append(p[2].lower())
                L.parent.append(int(p[3]))
                L.level.append(p[4])
                L.rects.append(parse_rects(p[5]) if len(p) > 5 else [])
            elif line.startswith('T\t'):
                p = line.split('\t')
                L.T.append((int(p[1]), int(p[2]), parse_rects(p[3]) if len(p) > 3 else []))
            elif line.startswith('H\t'):
                L.H = float(line.split('\t')[1])
    return L


class Style:
    pass


def parse_style(path):
    S = Style()
    with open(path, 'r', encoding='utf-8', errors='surrogateescape') as f:
        lines = f.read().split('\n')
    S.cols = lines[0].split('\t')
    S.rows = []  # line without the leading index
    S.disp, S.pos, S.flt, S.ovx, S.ovy, S.ccount, S.cwidth = [], [], [], [], [], [], []
    for line in lines[1:]:
        if not line:
            continue
        i = line.index('\t')
        rest = line[i + 1:]
        S.rows.append(rest)
        p = rest.split('\t', 8)  # name display position float clear ovx ovy ...
        S.disp.append(p[1]); S.pos.append(p[2]); S.flt.append(p[3]); S.ovx.append(p[5]); S.ovy.append(p[6])
        q = rest.rsplit('\t', 5)
        S.ccount.append(q[1]); S.cwidth.append(q[2])
    return S


def run_dump(tool, page_file, sheets, outfile):
    args = ['build/%s' % tool, 'dump', '1', page_file, UA] + ['%s=%s' % kv for kv in sheets.items()]
    with open(outfile, 'wb') as f:
        r = subprocess.run(args, cwd=ROOT, stdout=f, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError('%s failed: %s' % (tool, r.stderr[:300]))


# ---------------------------------------------------------------- source map

TAG_RE = re.compile(r'<([A-Za-z][^\s/>]*)((?:"[^"]*"|\'[^\']*\'|[^>"\'])*)>')
END_RE = re.compile(r'</([A-Za-z][^\s/>]*)[^>]*>')


class Src:
    pass


def tokenize(text):
    """Returns tags: list of (name, start, end_after_gt, attr_start) and texts:
    list of (start, end, tag_index_of_last_start_or_-1, seq) with enough info to
    rebuild the open-element stack later in map_source()."""
    toks = []  # ('s', name, start, end, attrstart) | ('e', name) | ('t', start, end)
    i = 0
    n = len(text)
    while i < n:
        j = text.find('<', i)
        if j < 0:
            if i < n:
                toks.append(('t', i, n))
            break
        if j > i:
            toks.append(('t', i, j))
        if text.startswith('<!--', j):
            k = text.find('-->', j + 4)
            i = n if k < 0 else k + 3
            continue
        if text.startswith('<![CDATA[', j):
            k = text.find(']]>', j)
            i = n if k < 0 else k + 3
            continue
        if text.startswith('<!', j) or text.startswith('<?', j):
            k = text.find('>', j)
            i = n if k < 0 else k + 1
            continue
        m = TAG_RE.match(text, j)
        if m:
            name = m.group(1).lower()
            toks.append(('s', name, j, m.end(), m.start(2)))
            i = m.end()
            if name in RAW and not m.group(2).rstrip().endswith('/'):
                k = text.lower().find('</' + name, i)
                if k < 0:
                    k = n
                if k > i:
                    toks.append(('raw', i, k))
                i = k
            continue
        m = END_RE.match(text, j)
        if m:
            toks.append(('e', m.group(1).lower()))
            i = m.end()
            continue
        toks.append(('t', j, j + 1))
        i = j + 1
    return toks


def map_source(text, L):
    """Aligns source start tags with the dump's elements.  Returns Src with
    tags[k] = dict(idx, name, start, end, attrstart) for tags mapped to elements,
    and texts = list of dict(start, end, parent) for text spans with a mapped parent."""
    toks = tokenize(text)
    S = Src()
    S.tags = []
    S.texts = []
    names = L.name
    ne = len(names)
    ei = 0
    stack = []  # element indices
    unmatched = 0
    tmpl = 0
    for t in toks:
        kind = t[0]
        if kind == 's':
            name = t[1]
            if tmpl:
                if name == 'template':
                    tmpl += 1
                continue
            if name == 'template':
                pass
            # find ei
            idx = None
            for look in range(0, 6):
                if ei + look < ne and names[ei + look] == name:
                    idx = ei + look
                    break
            if idx is None:
                unmatched += 1
                continue
            ei = idx + 1
            S.tags.append({'idx': idx, 'name': name, 'start': t[2], 'end': t[3], 'attrstart': t[4]})
            par = L.parent[idx]
            while stack and stack[-1] != par:
                stack.pop()
            if name not in VOID and not text[t[3] - 2:t[3]] == '/>':
                stack.append(idx)
            if name == 'template':
                tmpl = 1
        elif kind == 'e':
            name = t[1]
            if tmpl:
                if name == 'template':
                    tmpl -= 1
                continue
            for k in range(len(stack) - 1, -1, -1):
                if names[stack[k]] == name:
                    del stack[k:]
                    break
        elif kind == 't' or kind == 'raw':
            if tmpl or kind == 'raw':
                continue
            if stack:
                S.texts.append({'start': t[1], 'end': t[2], 'parent': stack[-1]})
    S.unmatched = unmatched
    S.by_idx = {t['idx']: t for t in S.tags}
    return S


# ---------------------------------------------------------------- edit ops

WORDS = ['alpha', 'quickly', 'brown', 'sentinel', 'harbor', 'lantern', 'mosaic', 'notable',
         'orchard', 'pebble', 'quartz', 'ripple', 'summit', 'timber', 'velvet', 'whisper']
SENTENCE = ' This extra sentence was added by the edit script to test how local the change stays.'
BLOCK = ('<p>A new paragraph inserted at this point of the page by the edit script, long enough '
         'to wrap onto a second line of text in a typical content column of the page.</p>')


def attr_insert(text, tag, attr, addition_value, new_attr_prefix):
    """Returns (offset, insert_text) that appends `addition_value` to attribute `attr` of the
    start tag, or adds the attribute after the tag name."""
    seg = text[tag['start']:tag['end']]
    m = re.search(r'\s%s\s*=\s*("([^"]*)"|\'([^\']*)\')' % attr, seg, re.I)
    if m:
        q = seg[m.start(1)]
        off = tag['start'] + m.end(1) - 1  # before closing quote
        return off, addition_value
    m2 = re.search(r'\s%s\s*=' % attr, seg, re.I)
    if m2:
        return None  # unquoted attribute value: skip
    return tag['start'] + 1 + len(tag['name']), ' %s="%s"' % (attr, new_attr_prefix + addition_value)


def text_sites(text, S, L, rng, want, kind_filter=None):
    cand = []
    for t in S.texts:
        if L.level[t['parent']] == 'n':
            continue
        if L.name[t['parent']] in ('pre', 'textarea', 'script', 'style', 'title', 'code', 'option'):
            continue
        s = text[t['start']:t['end']]
        if len(s.strip()) < 90:
            continue
        cand.append(t)
    rng.shuffle(cand)
    out = []
    for t in cand:
        s = text[t['start']:t['end']]
        spaces = [m.start() for m in re.finditer(r' ', s) if 20 < m.start() < len(s) - 20]
        spaces = [p for p in spaces if '&' not in s[max(0, p - 12):p + 12]]
        if not spaces:
            continue
        p = rng.choice(spaces)
        out.append({'offset': t['start'] + p + 1, 'parent': t['parent'], 'tstart': t['start']})
        if len(out) >= want:
            break
    return out


class Ctx:
    """Per-side derived structure of a layout+style dump pair."""
    pass


def derive(L, S):
    c = Ctx()
    n = len(L.name)
    c.n = n
    c.isroot = [False] * n
    c.croot = [-1] * n
    c.pbox = [-1] * n
    c.container = [-1] * n
    c.pc = [-1] * n
    par = L.parent
    lev = L.level
    disp, pos, flt, ovx, ovy = S.disp, S.pos, S.flt, S.ovx, S.ovy
    for i in range(n):
        p = par[i]
        if lev[i] != 'n':
            r = (i == 0 or flt[i] != 'none' or pos[i] in ('absolute', 'fixed') or disp[i] in ROOT_DISP
                 or ovx[i] not in ('visible', 'clip') or ovy[i] not in ('visible', 'clip')
                 or S.ccount[i] != 'auto' or S.cwidth[i] != 'auto'
                 or (p >= 0 and disp[p] in FLEXGRID))
            c.isroot[i] = r
        if p >= 0:
            c.croot[i] = p if c.isroot[p] else c.croot[p]
            # nearest boxed ancestor
            q = p
            while q >= 0 and lev[q] == 'n':
                q = par[q]
            c.pbox[i] = q
            c.container[i] = c.container[p] if disp[p] in INLINE_DISP else p
    for i in range(n):
        c.pc[i] = c.container[i] if disp[i] in INLINE_DISP else i
    # prev in-flow block sibling per parent box
    c.prev = [-1] * n
    c.inflow = [False] * n
    c.nsib = {}
    last = {}
    for i in range(n):
        if lev[i] == 'b' and flt[i] == 'none' and pos[i] in ('static', 'relative', 'sticky'):
            c.inflow[i] = True
            pb = c.pbox[i]
            c.prev[i] = last.get(pb, -1)
            last[pb] = i
            c.nsib[pb] = c.nsib.get(pb, 0) + 1
    # bbox
    c.bb = [None] * n
    for i in range(n):
        rs = L.rects[i]
        if rs:
            x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
            x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
            c.bb[i] = (x0, y0, x1 - x0, y1 - y0)
    # T keys
    c.Tkey = {}
    cnt = {}
    for k, (o, p, rs) in enumerate(L.T):
        r = cnt.get(p, 0)
        cnt[p] = r + 1
        c.Tkey[(p, r)] = k
    # paragraph keys: container*1000 + run (runs split by in-flow block children above the text)
    from bisect import bisect_right
    kids = {}
    for i in range(n):
        if c.inflow[i] and c.bb[i]:
            kids.setdefault(par[i], []).append(c.bb[i][1] + c.bb[i][3])
    for v in kids.values():
        v.sort()
    c.tpara = []
    c.elem_pk = {}
    c.cont_pks = {}
    for k, (o, p, rs) in enumerate(L.T):
        cont = c.pc[p]
        run = 0
        if rs and cont in kids:
            run = bisect_right(kids[cont], rs[0][1] + EPS)
        pk = cont * 1000 + min(run, 999)
        c.tpara.append(pk)
        e = p
        while e >= 0:
            c.elem_pk.setdefault(e, set()).add(pk)
            if e == cont:
                break
            e = par[e]
        c.cont_pks.setdefault(cont, set()).add(pk)
    return c


EPS = 1e-3
EPSP = 0.1  # position tolerance: absolute positions are quantized to 1/64 and differences of them carry up to two quanta
DBG = None


def same(a, b):
    return abs(a - b) < EPSP


def sames(a, b):
    return abs(a - b) < EPS


def rects_same_size(a, b):
    if len(a) != len(b):
        return False
    for u, v in zip(a, b):
        if not sames(u[2], v[2]) or not sames(u[3], v[3]):
            return False
    return True


def rects_same_pos(a, b):
    for u, v in zip(a, b):
        if not same(u[0], v[0]) or not same(u[1], v[1]):
            return False
    return True


def analyze(BL, BS, AL, AS, ins=None, target=None, kind='', B=None):
    """BL/AL: Layout; BS/AS: Style; ins: (p, k): k elements inserted at element index p;
    target: dict(parent=idx) for text edits, dict(elem=idx) for element edits."""
    res = {}
    global EPSP
    # absolute positions are float32 in the dump: past 2**19 their spacing exceeds the quantum, and a
    # difference of two of them carries up to two spacings of noise, so the position tolerance scales with the page height
    hmax = max(BL.H or 1.0, AL.H or 1.0, 1.0)
    EPSP = max(0.1, 4.0 * 2.0 ** (math.floor(math.log2(hmax)) - 23))
    nb, na = len(BL.name), len(AL.name)
    p_ins, k_ins = ins if ins else (nb + 1000000, 0)
    if na != nb + k_ins:
        return {'valid': False, 'why': 'element count %d -> %d (expected +%d)' % (nb, na, k_ins)}

    def b2a(i):
        return i if i < p_ins else i + k_ins

    def a2b(j):
        if j < p_ins:
            return j
        if j < p_ins + k_ins:
            return None
        return j - k_ins

    for i in range(nb):
        if BL.name[i] != AL.name[b2a(i)]:
            return {'valid': False, 'why': 'name mismatch at %d: %s vs %s' % (i, BL.name[i], AL.name[b2a(i)])}
    B = B or derive(BL, BS)
    A = derive(AL, AS)
    cols = BS.cols[1:]
    paint_cols = [k for k, cname in enumerate(cols) if cname in PAINT_ONLY]
    # ---- style diff
    S_set = set()
    S_layout = set()
    for i in range(nb):
        j = b2a(i)
        if BS.rows[i] != AS.rows[j]:
            S_set.add(i)
            a = BS.rows[i].split('\t'); b = AS.rows[j].split('\t')
            lay = False
            for k in range(len(a)):
                if a[k] != b[k] and cols[k] not in PAINT_ONLY and cols[k] != 'name':
                    lay = True
                    break
            if lay:
                S_layout.add(i)
    from collections import Counter
    pb = Counter(BS.rows[nb:]); pa_ = Counter(AS.rows[na:])
    res['pseudo_changed'] = sum((pa_ - pb).values())
    new_el = [j for j in range(na) if a2b(j) is None]
    res['elements'] = nb
    res['style_changed'] = len(S_set)
    res['style_changed_layout'] = len(S_layout)
    res['new_elements'] = len(new_el)
    # ---- element boxes
    size_changed = set(); moved_only = set(); height_changed = set(); width_changed = set()
    for i in range(nb):
        j = b2a(i)
        lb, la = BL.level[i], AL.level[j]
        if lb == 'n' and la == 'n':
            continue
        if lb != la:
            size_changed.add(i)
            continue
        rb, ra = BL.rects[i], AL.rects[j]
        if not rects_same_size(rb, ra):
            size_changed.add(i)
            if lb == 'b' and rb and ra:
                if not sames(rb[0][3], ra[0][3]):
                    height_changed.add(i)
                if not sames(rb[0][2], ra[0][2]):
                    width_changed.add(i)
        elif not rects_same_pos(rb, ra):
            moved_only.add(i)
    res['boxes_total'] = sum(1 for l in BL.level if l != 'n')
    res['size_changed'] = len(size_changed)
    res['moved_only'] = len(moved_only)
    res['height_changed'] = len(height_changed)
    # ---- text nodes and paragraphs
    Tre = set()
    Tnew = 0
    edit_para = None
    if target and 'parent' in target:
        k0 = B.Tkey.get((target['parent'], 0))
        if k0 is not None:
            edit_para = B.tpara[k0]
    P_changed = set()
    P_count = set()
    para_all = set(B.tpara)
    for (p, r), k in B.Tkey.items():
        pa = b2a(p)
        k2 = A.Tkey.get((pa, r))
        pk = B.tpara[k]
        if k2 is None:
            P_changed.add(pk); P_count.add(pk)
            continue
        rb, ra = BL.T[k][2], AL.T[k2][2]
        if len(rb) != len(ra):
            Tre.add(k); P_changed.add(pk); P_count.add(pk)
        else:
            diff = False
            for u, v in zip(rb, ra):
                if not sames(u[2], v[2]):
                    diff = True
                    break
            if diff:
                Tre.add(k); P_changed.add(pk)
    newP = set()
    for (p, r), k2 in A.Tkey.items():
        if a2b(p) is None:
            Tnew += 1
            newP.add(A.tpara[k2])
    res['texts_total'] = len(BL.T)
    res['texts_rebroken'] = len(Tre)
    res['texts_new'] = Tnew
    res['paras_total'] = len(para_all)
    P_min = set(P_changed)
    if edit_para is not None:
        P_min.add(edit_para)
    for q in newP:
        P_min.add(('n', q))
    res['paras_changed'] = len(P_changed)
    res['paras_count_changed'] = len(P_count)
    res['paras_min'] = len(P_min)
    res['paras_changed_other'] = len([q for q in P_changed if q != edit_para])
    P_coarse = set()
    P_fine = set()
    ATOM = {'inline-block', 'inline-flex', 'inline-grid', 'inline-table'}
    for i in S_set:
        if BL.level[i] == 'n':
            continue
        pks = B.elem_pk.get(i)
        if pks:
            P_coarse |= pks
            if i in S_layout:
                P_fine |= pks
        if BS.disp[i] in ATOM:
            pks = B.cont_pks.get(B.container[i])
            if pks:
                P_coarse |= pks
                if i in S_layout:
                    P_fine |= pks
    for i in width_changed:
        if i in B.cont_pks:
            P_coarse |= B.cont_pks[i]; P_fine |= B.cont_pks[i]
    for i in size_changed:
        if BS.disp[i] in ATOM:
            pks = B.cont_pks.get(B.container[i])
            if pks:
                P_coarse |= pks; P_fine |= pks
    for q in P_min:
        P_coarse.add(q); P_fine.add(q)
    res['paras_coarse'] = len(P_coarse)
    res['paras_fine'] = len(P_fine)
    # ---- contexts (before-side ids; block members use B.croot, own content uses own())
    def own(Cx, i):
        return i if Cx.isroot[i] else Cx.croot[i]

    n_ctx = sum(1 for i in range(nb) if B.isroot[i])
    res['contexts_total'] = n_ctx
    C_min = set(); C_coarse = set()
    for i in range(nb):
        j = b2a(i)
        if BL.level[i] == 'n':
            continue
        cm = B.croot[i]
        in_size = i in size_changed
        # context-relative offset change
        offchg = False
        if BL.level[i] == 'b' and AL.level[j] == 'b' and B.bb[i] and A.bb[j] and cm >= 0:
            cj = A.croot[j]
            if B.bb[cm] and cj >= 0 and A.bb[cj]:
                ob = (B.bb[i][0] - B.bb[cm][0], B.bb[i][1] - B.bb[cm][1])
                oa = (A.bb[j][0] - A.bb[cj][0], A.bb[j][1] - A.bb[cj][1])
                offchg = not (same(ob[0], oa[0]) and same(ob[1], oa[1]))
        if (in_size or offchg) and cm >= 0:
            C_min.add(cm)
        if i in width_changed and B.isroot[i]:
            C_min.add(i)
        if i in S_set:
            if cm >= 0:
                C_coarse.add(cm)
            C_coarse.add(own(B, i))
            if i in S_layout:
                if cm >= 0:
                    C_min.add(cm)
                C_min.add(own(B, i))
    for q in P_min:
        if isinstance(q, tuple):
            C_min.add(('n', own(A, q[1] // 1000)))
        else:
            C_min.add(own(B, q // 1000))
    for j in new_el:
        cj = A.croot[j]
        if cj >= 0:
            m = a2b(cj)
            C_min.add(m if m is not None else ('n', cj))
    C_coarse |= C_min
    # contexts with inputs changed but only paint: counted in coarse; edit target for text counts in min via P_min
    res['ctx_min'] = len(C_min)
    res['ctx_coarse'] = len(C_coarse)
    # ---- X3: coordinate rewrites
    qualifies = bool(height_changed) or k_ins > 0
    res['x3_qualifies'] = qualifies
    ra_ = rb_ = rc_ = rd_ = re_ = 0
    common = 0
    for i in range(nb):
        j = b2a(i)
        lb, la = BL.level[i], AL.level[j]
        if lb == 'n' or la == 'n':
            continue
        bbb, bba = B.bb[i], A.bb[j]
        if not bbb or not bba:
            continue
        abs_moved = not (same(bbb[0], bba[0]) and same(bbb[1], bba[1]))
        if abs_moved:
            ra_ += 1
        if lb == 'b' and la == 'b':
            # (b) parent relative
            pb, pa_ = B.pbox[i], A.pbox[j]
            if pb >= 0 and pa_ >= 0 and B.bb[pb] and A.bb[pa_]:
                ob = (bbb[0] - B.bb[pb][0], bbb[1] - B.bb[pb][1])
                oa = (bba[0] - A.bb[pa_][0], bba[1] - A.bb[pa_][1])
            else:
                ob = (bbb[0], bbb[1]); oa = (bba[0], bba[1])
            pchg = not (same(ob[0], oa[0]) and same(ob[1], oa[1]))
            xchg = not same(ob[0], oa[0])
            if pchg:
                rb_ += 1
            # (c) context relative
            cm, cj = B.croot[i], A.croot[j]
            if cm >= 0 and cj >= 0 and B.bb[cm] and A.bb[cj]:
                cb = (bbb[0] - B.bb[cm][0], bbb[1] - B.bb[cm][1])
                ca = (bba[0] - A.bb[cj][0], bba[1] - A.bb[cj][1])
            else:
                cb = (bbb[0], bbb[1]); ca = (bba[0], bba[1])
            if not (same(cb[0], ca[0]) and same(cb[1], ca[1])):
                rc_ += 1
            # (d) sibling anchored
            def anchor(Cx, LL, e, bbs):
                pv = Cx.prev[e] if Cx.inflow[e] else -1
                pbx = Cx.pbox[e]
                if pv >= 0 and bbs[pv]:
                    return ('s', pv), (bbs[e][0] - bbs[pv][0], bbs[e][1] - (bbs[pv][1] + bbs[pv][3]))
                if pbx >= 0 and bbs[pbx]:
                    return ('p', pbx), (bbs[e][0] - bbs[pbx][0], bbs[e][1] - bbs[pbx][1])
                return ('p', -1), (bbs[e][0], bbs[e][1])
            ida, va = anchor(A, AL, j, A.bb)
            idb, vb = anchor(B, BL, i, B.bb)
            # identity of the anchor in before space
            ida_b = (ida[0], a2b(ida[1]) if ida[1] >= 0 else -1)
            ida_b = (ida[0], ida_b[1] if ida_b[1] is not None else ('new', ida[1]))
            idchg = ida_b != idb
            dchg = idchg or not (same(va[0], vb[0]) and same(va[1], vb[1]))
            if dchg:
                rd_ += 1
                if DBG is not None and len(DBG) < 40:
                    DBG.append((i, BL.name[i], B.pbox[i], idb, ida_b, vb, va, BS.disp[i], BS.flt[i], BS.pos[i]))
            # (e) summary tree: y via tree for in-flow boxes
            yrel_chg = not same(vb[1], va[1]) or idchg
            if B.inflow[i] and A.inflow[j]:
                if (i in height_changed) or yrel_chg:
                    ns = max(2, A.nsib.get(A.pbox[j], 2))
                    re_ += math.ceil(math.log2(ns))
                if not same(ob[0], oa[0]):
                    re_ += 1
            else:
                if pchg:
                    re_ += 1
        else:
            # inline-level boxes: paragraph relative in every scheme
            cb_, ca_ = B.container[i], A.container[j]
            if cb_ >= 0 and ca_ >= 0 and B.bb[cb_] and A.bb[ca_]:
                ob = [(r[0] - B.bb[cb_][0], r[1] - B.bb[cb_][1], r[2], r[3]) for r in BL.rects[i]]
                oa = [(r[0] - A.bb[ca_][0], r[1] - A.bb[ca_][1], r[2], r[3]) for r in AL.rects[j]]
                if len(ob) != len(oa) or not all(same(u[0], v[0]) and same(u[1], v[1]) for u, v in zip(ob, oa)):
                    common += 1
    # new boxes: one write each in every scheme (not counted); text nodes
    for (p, r), k in B.Tkey.items():
        pa = b2a(p)
        k2 = A.Tkey.get((pa, r))
        if k2 is None:
            ra_ += 1; common += 1
            continue
        rbt, rat = BL.T[k][2], AL.T[k2][2]
        cb_, ca_ = B.pc[p], A.pc[pa]
        moved_abs = len(rbt) != len(rat) or not rects_same_pos(rbt, rat)
        if moved_abs:
            ra_ += 1
        if cb_ >= 0 and ca_ >= 0 and B.bb[cb_] and A.bb[ca_]:
            ob = [(r_[0] - B.bb[cb_][0], r_[1] - B.bb[cb_][1]) for r_ in rbt]
            oa = [(r_[0] - A.bb[ca_][0], r_[1] - A.bb[ca_][1]) for r_ in rat]
            if len(ob) != len(oa) or not all(same(u[0], v[0]) and same(u[1], v[1]) for u, v in zip(ob, oa)):
                common += 1
        elif moved_abs:
            common += 1
    rf_ = sum(1 for i in size_changed if BL.level[i] == 'b' and AL.level[b2a(i)] == 'b' and B.inflow[i] and A.inflow[b2a(i)])
    res.update({'rw_a': ra_, 'rw_b': rb_, 'rw_c': rc_, 'rw_d': rd_, 'rw_e': re_, 'rw_f': rf_, 'rw_common': common})
    # ---- X16: after-side vertical extent [top, bottom] of every dirty unit, flat [t0, b0, t1, b1, ...], and the edit point
    def yspan(j):
        while j >= 0:
            if A.bb[j]:
                return (int(round(A.bb[j][1])), int(round(A.bb[j][1] + A.bb[j][3])))
            j = AL.parent[j]
        return (0, 0)
    def flat(spans):
        o = []
        for t, b in spans:
            o.append(t); o.append(b)
        return o
    para_y = {}
    for (p, r), k2 in A.Tkey.items():
        rs = AL.T[k2][2]
        if rs:
            pk = A.tpara[k2]
            t = int(round(min(x[1] for x in rs))); b = int(round(max(x[1] + x[3] for x in rs)))
            if pk in para_y:
                t = min(t, para_y[pk][0]); b = max(b, para_y[pk][1])
            para_y[pk] = (t, b)
    para_yb = {}
    for (p, r), k in B.Tkey.items():
        pa = b2a(p)
        k2 = A.Tkey.get((pa, r))
        rs = AL.T[k2][2] if k2 is not None else BL.T[k][2]
        if not rs:
            continue
        t = int(round(min(x[1] for x in rs))); b = int(round(max(x[1] + x[3] for x in rs)))
        pk = B.tpara[k]
        if pk in para_yb:
            t = min(t, para_yb[pk][0]); b = max(b, para_yb[pk][1])
        para_yb[pk] = (t, b)
    yS = [yspan(b2a(i)) for i in sorted(S_set)]
    yP = []
    for q in P_min:
        if isinstance(q, tuple):
            yP.append(para_y.get(q[1], (0, 0)))
        else:
            yP.append(para_yb.get(q, (0, 0)))
    yC = []
    for c in C_min:
        if isinstance(c, tuple):
            yC.append(yspan(c[1]))
        else:
            yC.append(yspan(b2a(c)))
    yB = []
    for i in sorted(size_changed | moved_only):
        if BL.level[i] != 'n' and AL.level[b2a(i)] != 'n':
            yB.append(yspan(b2a(i)))
    ey = None
    if target and 'parent' in target:
        if edit_para is not None and edit_para in para_yb:
            ey = para_yb[edit_para][0]
        else:
            ey = yspan(b2a(target['parent']))[0]
    elif target and 'elem' in target and target['elem'] != 0:
        e = target['elem']
        ey = yspan(p_ins if k_ins else b2a(e))[0]
    res['x16'] = {'ey': ey, 'H': AL.H, 'yS': flat(yS), 'yP': flat(yP), 'yC': flat(yC), 'yB': flat(yB)}
    # subtree over-approximation for the style stage
    if target and 'elem' in target:
        e = target['elem']
        sub = 1
        i = e + 1
        while i < nb and BL.parent[i] >= e:
            sub += 1
            i += 1
        res['subtree_size'] = sub
    res['valid'] = True
    res['sets'] = {
        'S': sorted(S_set),
        'P': sorted(x for x in P_min if not isinstance(x, tuple)),
        'C': sorted(x for x in C_min if not isinstance(x, tuple)),
        'nP': sum(1 for x in P_min if isinstance(x, tuple)),
        'nC': sum(1 for x in C_min if isinstance(x, tuple)),
    }
    return res
