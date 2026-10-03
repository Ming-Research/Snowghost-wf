#!/usr/bin/env python3
"""Summarise timing-PAGE.jsonl: the cost of a font arrival against the text preparation of the paragraphs that use the font.
P_F = restricted_F - restricted_empty (text preparation of F's paragraphs only)
R_F = relaid_F - relaid_empty - P_F (line breaking and placement of F's paragraphs, beyond the structural layout)
S   = relaid_empty - restricted_empty (lay_out with every paragraph emptied: the box-structure part)
full: boxes, text, layout per rep."""
import sys, json, re
import os
for page in sys.argv[1:]:
    rows = {}
    for l in open(os.environ.get('FILE', f'timing-{page}.jsonl')):
        r = json.loads(l); rows[r['name']] = r
    ms = lambda n: rows[n]['per_rep_s'] * 1000
    kept = lambda n: int(re.search(r'kept (\d+)', rows[n]['out']).group(1))
    npara = int(re.search(r'paragraphs (\d+)', rows['restricted-empty']['out']).group(1))
    full = json.load(open('fullref.json'))[page]
    box, txt, lay = full
    ms0 = ms
    re_, rl_ = ms('restricted-empty'), ms('relaid-empty')
    print(f'\n## {page}: per rep ms (R reps {rows["restricted-empty"]["reps"]}): boxes {box:.1f}, text {txt:.1f} (prep {txt-box:.1f}), layout {lay:.1f} (lay_out {lay-txt:.1f}); '
          f'restricted-empty {re_:.1f}, relaid-empty {rl_:.1f}; S = {rl_-re_:.1f}; paragraphs {npara}')
    print('set | paragraphs kept | P_F | R_F | (P_F+R_F)/P_F | P_F / full prep | (P_F+R_F+S)/P_F | arrival upper bound / full (lay-box)')
    for n in rows:
        if not n.startswith('restricted ') : continue
        k = n[len('restricted '):]
        if f'relaid {k}' not in rows: continue
        P = ms(n) - re_; R = ms(f'relaid {k}') - rl_ - P
        full_prep = txt - box
        ratio = (P + R) / P if P > 1 else float('nan')
        ratio2 = (P + R + (rl_ - re_)) / P if P > 1 else float('nan')
        print(f'{k} | {kept(n)} ({100*kept(n)/npara:.1f}%) | {P:.1f} | {R:.1f} | {ratio:.2f} | {100*P/full_prep:.1f}% | {ratio2:.2f} | {100*(P+R+rl_-re_)/(lay-box):.1f}%')
