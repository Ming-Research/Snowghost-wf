"""Aggregates results/PAGE.jsonl (+ results/timing.json) into the numbers of report.md.
usage: python3 agg.py PAGE...   (prints markdown)"""
import json, sys, os, statistics as st
from bisect import bisect_left, bisect_right
FRAME = 16.667e-3
V = 720

def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p
    lo = int(k); hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)

def f(x, d=1):
    if x is None:
        return '-'
    if isinstance(x, float) and abs(x) < 10:
        return ('%.' + str(max(d, 2)) + 'g') % x
    return '%d' % round(x)

def dist(v):
    return 'med %s / p90 %s / max %s' % (f(q(v, .5)), f(q(v, .9)), f(max(v)) if v else '-')

timing = json.load(open('results/timing.json')) if os.path.exists('results/timing.json') else {}

def load(page):
    rows = [json.loads(l) for l in open('results/%s.jsonl' % page)]
    return rows

def prep(flat):
    return (sorted(flat[0::2]), sorted(flat[1::2]))

def share(pp, lo, hi):
    """Share of the units (prepped by prep) whose vertical extent meets [lo, hi]."""
    tops, bots = pp
    n = len(tops)
    if not n:
        return None
    return (n - (n - bisect_right(tops, hi)) - bisect_left(bots, lo)) / n

def consts(page, r):
    t = timing.get(page)
    if not t:
        return None
    ne = r['elements']
    ts = t['style_oracle:all'] / ne
    tp = (t['layout_oracle:text'] - t['layout_oracle:boxes']) / r['paras_total']
    tc = (t['layout_oracle:layout'] - t['layout_oracle:text']) / r['contexts_total']
    tb = (t['layout_oracle:layout'] - t['layout_oracle:text']) / r['boxes_total']
    return ts, tp, tc, tb

def main(pages):
    allx16 = []
    for page in pages:
        rows = load(page)
        bad = [r for r in rows if not r.get('valid')]
        R = [r for r in rows if r.get('valid')]
        print('\n## %s: %d edits, %d invalid\n' % (page, len(rows), len(bad)))
        for r in bad[:5]:
            print('invalid', r['id'], r.get('why', '')[:120])
        r0 = R[0]
        print('elements %d, boxes %d, contexts %d, paragraphs (dump-derived) %d, H %d' % (r0['elements'], r0['boxes_total'], r0['contexts_total'], r0['paras_total'], r0['H_before']))
        kinds = sorted(set(r['kind'] for r in R), key=lambda k: ['word', 'sentence', 'class', 'color', 'block', 'fontsize', 'custom', 'rootfont'].index(k))
        # ---------------- X1
        print('\n### X1 locality\n')
        print('| kind | n | style nodes changed | paragraphs changed | % of paragraphs (med / p90 / max) | edits with <1 % | contexts changed (min) |')
        print('|---|---:|---|---|---|---:|---|')
        for k in kinds:
            K = [r for r in R if r['kind'] == k]
            frac = [100.0 * r['paras_changed'] / r['paras_total'] for r in K]
            lt1 = sum(1 for x in frac if x < 1.0)
            print('| %s | %d | %s | %s | %.2f / %.2f / %.2f | %d/%d | %s |' % (k, len(K), dist([r['style_changed'] for r in K]), dist([r['paras_changed'] for r in K]), q(frac, .5), q(frac, .9), max(frac), lt1, len(K), dist([r['ctx_min'] for r in K])))
        W = [r for r in R if r['kind'] == 'word']
        if W:
            fr = [100.0 * r['paras_changed'] / r['paras_total'] for r in W]
            print('\nWord edits: mean %.3f %% of paragraphs change lines, max %.3f %%; paragraphs changed per edit: %s; other than the edited one: %s' % (st.mean(fr), max(fr), dist([r['paras_changed'] for r in W]), dist([r['paras_changed_other'] for r in W])))
        print('\nRecomputed over minimal (per edit with minimal > 0; "inf" = recomputed with empty minimal set):\n')
        print('| kind | unit | key | n with min>0 | ratio med / p90 / max | share of edits with ratio < 3 | recomputed with empty minimal |')
        print('|---|---|---|---:|---|---:|---:|')
        for k in kinds:
            K = [r for r in R if r['kind'] == k]
            def line(unit, key, rec, mn):
                pairs = [(rec(r), mn(r)) for r in K]
                pos = [(a, b) for a, b in pairs if b > 0]
                empty = sum(1 for a, b in pairs if b == 0 and a > 0)
                if not pos and not empty:
                    return
                ratios = [a / b for a, b in pos]
                lt3 = sum(1 for x in ratios if x < 3)
                print('| %s | %s | %s | %d | %s | %s | %d |' % (k, unit, key, len(pos), '%.2f / %.2f / %.2f' % (q(ratios, .5), q(ratios, .9), max(ratios)) if ratios else '-', '%d/%d' % (lt3, len(ratios)) if ratios else '-', empty))
            line('paragraph', 'layout-relevant groups', lambda r: r['paras_fine'], lambda r: r['paras_min'])
            line('paragraph', 'whole style', lambda r: r['paras_coarse'], lambda r: r['paras_min'])
            line('context', 'whole style', lambda r: r['ctx_coarse'], lambda r: r['ctx_min'])
            if k in ('class', 'color', 'fontsize', 'custom', 'rootfont'):
                line('styled node', 'restyle subtree', lambda r: r.get('subtree_size', r['elements']), lambda r: r['style_changed'])
        # ---------------- X3
        print('\n### X3 rewrites\n')
        print('a absolute positions moved; b parent-relative; c context-relative; d sibling-anchored; e summary-tree node writes; f prefix-sum size writes. Edits with a height change or insertion (translation roots exist).\n')
        print('| subset | n | stat | a | b | c (context-rel) | d (sibling) | e (tree) | f (prefix sums) |')
        print('|---|---:|---|---:|---:|---:|---:|---:|---:|')
        def x3rows(name, S):
            if not S:
                return
            for lab, p in (('med', .5), ('p90', .9), ('p99', .99), ('max', 1.0)):
                print('| %s | %d | %s | %s |' % (name, len(S), lab, ' | '.join(f(q([r['rw_' + c] for r in S], p)) for c in 'abcdef')))
        Q = [r for r in R if r['x3_qualifies']]
        x3rows('all qualifying', Q)
        for k in kinds:
            Kq = [r for r in Q if r['kind'] == k]
            if k in ('word', 'sentence', 'block') and Kq:
                x3rows(k, Kq)
        if Q:
            c90 = q([r['rw_c'] for r in Q], .9)
            print('\nBreak-even per-write cost ratio r* = p90(c) / p90(x): ' + ', '.join('%s %.2f' % (n, c90 / max(q([r["rw_" + n] for r in Q], .9), 1)) for n in 'def'))
            for k in ('word', 'sentence', 'block'):
                Kq = [r for r in Q if r['kind'] == k]
                if Kq:
                    c90 = q([r['rw_c'] for r in Kq], .9)
                    print('  %s: ' % k + ', '.join('%s %.2f' % (n, c90 / max(q([r["rw_" + n] for r in Kq], .9), 1)) for n in 'def'))
        # ---------------- X16
        X = [r for r in R if 'x16' in r]
        if not X:
            continue
        c = consts(page, r0)
        print('\n### X16 viewport share\n')
        if c:
            ts, tp, tc, tb = c
            print('unit costs from the full stages (sequential drivers): style %.2f us/node, text prep %.1f us/paragraph, layout passes %.1f us/context (%.2f us/box)' % (ts * 1e6, tp * 1e6, tc * 1e6, tb * 1e6))
        out = []
        for r in X:
            x = r['x16']
            H = x['H']
            if x['ey'] is not None:
                eys = [x['ey']]
            else:
                eys = [H * p for p in (.1, .3, .5, .7, .9)]
            cost = None
            if c:
                cost = (len(x['yS'])//2) * ts + (len(x['yP'])//2) * tp + (len(x['yC'])//2) * tc
                costB = cost + (len(x['yB'])//2) * tb
            else:
                costB = None
            PP = {a: prep(x[a]) for a in ('yS', 'yP', 'yC', 'yB')}
            PP['all'] = prep(x['yS'] + x['yP'] + x['yC'] + x['yB'])
            PP['work'] = prep(x['yS'] + x['yP'] + x['yC'])
            res = {'id': r['id'], 'kind': r['kind'], 'cost': cost, 'costB': costB, 'n': [len(x[a]) // 2 for a in ('yS', 'yP', 'yC', 'yB')]}
            for tag, w in (('in', V / 2), ('w720', V), ('w1080', V * 1.5)):
                allsh, wsh, typ = [], [], []
                for ey in eys:
                    allsh.append(share(PP['all'], ey - w, ey + w))
                    wsh.append(share(PP['work'], ey - w, ey + w))
                    typ.append([share(PP[a], ey - w, ey + w) for a in ('yS', 'yP', 'yC', 'yB')])
                def avg(v):
                    v = [a for a in v if a is not None]
                    return sum(v) / len(v) if v else None
                res[tag] = {'all': avg(allsh), 'work': avg(wsh), 'typ': [avg([t[i] for t in typ]) for i in range(4)]}
                if c:
                    cw = []
                    for ey in eys:
                        a = [(share(PP['yS'], ey - w, ey + w), (len(x['yS'])//2) * ts), (share(PP['yP'], ey - w, ey + w), (len(x['yP'])//2) * tp), (share(PP['yC'], ey - w, ey + w), (len(x['yC'])//2) * tc)]
                        tot = sum(b for s, b in a if s is not None)
                        cw.append(sum(s * b for s, b in a if s is not None) / tot if tot > 0 else None)
                    res[tag]['cost'] = avg(cw)
            out.append(res)
        allx16.extend([dict(o, page=page) for o in out])
        if c:
            print('\nCost per edit (sequential estimate, work units S,P,C), ms: ')
            for k in kinds:
                v = [o['cost'] * 1e3 for o in out if o['kind'] == k]
                vb = [o['costB'] * 1e3 for o in out if o['kind'] == k]
                print('- %s: med %.3f p90 %.3f max %.2f; with moved boxes at average cost: med %.3f p90 %.2f max %.1f; edits over one frame: %d/%d (A), %d/%d (B)' % (k, q(v, .5), q(v, .9), max(v), q(vb, .5), q(vb, .9), max(vb), sum(1 for o in out if o['kind'] == k and o['cost'] > FRAME), len(v), sum(1 for o in out if o['kind'] == k and o['costB'] > FRAME), len(v)))
        for lab, sel in (('all edits', lambda o: True),) + ((('edits costing > 1 frame (S,P,C units at the full stages\' per-unit times)', lambda o: o['cost'] > FRAME), ('edits costing > 1 frame on 4 ideal workers (cost / 4)', lambda o: o['cost'] / 4 > FRAME)) if c else ()):
            S = [o for o in out if sel(o)]
            print('\n%s: n=%d' % (lab, len(S)))
            if not S:
                continue
            print('\n| window | pooled S,P,C,B med (p25-p75) | S,P,C only med | cost-weighted S,P,C med | S med | P med | C med | B med |')
            print('|---|---|---|---|---|---|---|---|')
            for tag, name in (('in', 'in the viewport (+-360)'), ('w720', 'within 720 of the edit point'), ('w1080', 'viewport +-720 (+-1080 of the edit point)')):
                def med(g):
                    v = [g(o) for o in S]
                    v = [a for a in v if a is not None]
                    return q(v, .5), q(v, .25), q(v, .75)
                a = med(lambda o: o[tag]['all']); w = med(lambda o: o[tag]['work'])
                cw = med(lambda o: o[tag].get('cost')) if c else (None,) * 3
                t = [med(lambda o, i=i: o[tag]['typ'][i])[0] for i in range(4)]
                fm = lambda x: '-' if x is None else '%.3f' % x
                print('| %s | %s (%s-%s) | %s | %s | %s |' % (name, fm(a[0]), fm(a[1]), fm(a[2]), fm(w[0]), fm(cw[0]), ' | '.join(fm(x) for x in t)))
            bykind = {}
            for o in S:
                bykind.setdefault(o['kind'], []).append(o)
            print('\nper kind, median share within 720 (pooled / S,P,C only):', '; '.join('%s n=%d %.3f / %.3f' % (k, len(v), q([o['w720']['all'] for o in v if o['w720']['all'] is not None] or [0], .5), q([o['w720']['work'] for o in v if o['w720']['work'] is not None] or [0], .5)) for k, v in sorted(bykind.items())))
        if c:
            print('\nSensitivity to the cost threshold (window: within 720 of the edit point; median over edits):\n')
            print('| threshold | n edits | pooled S,P,C,B | S,P,C | cost-weighted S,P,C | p90 pooled |')
            print('|---|---:|---:|---:|---:|---:|')
            for name, th in (('all', -1), ('0.1 ms', 1e-4), ('1 ms', 1e-3), ('4.2 ms (240 Hz frame)', 1 / 240.0), ('16.7 ms (60 Hz frame)', FRAME)):
                S = [o for o in out if o['cost'] > th]
                if not S:
                    print('| %s | 0 | - | - | - | - |' % name)
                    continue
                g = lambda key: q([o['w720'][key] for o in S if o['w720'].get(key) is not None], .5)
                print('| %s | %d | %.3f | %.3f | %.3f | %.3f |' % (name, len(S), g('all'), g('work'), g('cost'), q([o['w720']['all'] for o in S if o['w720']['all'] is not None], .9)))
    json.dump(allx16, open('results/x16.%s.json' % '_'.join(pages), 'w'))

main(sys.argv[1:])
