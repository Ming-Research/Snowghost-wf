#!/usr/bin/env python3
"""Cut a page's HTML before the start tag of the k-th child of its spine element.
usage: cut.py PAGE.html CHROMIUM_LAYOUT.tsv PERCENT[,PERCENT...] OUTPREFIX
Spine: from <body>, repeatedly descend into the child with the largest subtree
until the element has >= 20 element children. Cut points: before the spine child whose
element index is nearest p*(number of elements). Writes OUTPREFIX.<p>.html and prints the cut table."""
import sys, re
from html.parser import HTMLParser
page, dump, pcts, outp = sys.argv[1:5]
spine_marker = sys.argv[5] if len(sys.argv) > 5 else None
pcts = [float(x) for x in pcts.split(',')]
els = []  # (name, parent)
for line in open(dump, encoding='utf-8'):
    if line.startswith('E\t'):
        f = line.rstrip('\n').split('\t')
        els.append((f[2], int(f[3])))
n = len(els)
kids = [[] for _ in range(n)]
for i, (nm, p) in enumerate(els):
    if p >= 0: kids[p].append(i)
size = [1]*n
for i in range(n-1, -1, -1):
    p = els[i][1]
    if p >= 0: size[p] += size[i]
body = next(i for i, (nm, p) in enumerate(els) if nm == 'body')
spine = body
while len(kids[spine]) < 20 and kids[spine]:
    spine = max(kids[spine], key=lambda c: size[c])
src = open(page, encoding='utf-8', errors='surrogateescape').read()
# start-tag offsets in source order, skipping comments and the contents of
# script, style, template, textarea and title
pat = re.compile(r'<!--.*?-->|<(script|style|template|textarea|title)\b[^>]*>.*?</\1\s*>|<([a-zA-Z][a-zA-Z0-9:._-]*)', re.S | re.I)
tags = []
for m in pat.finditer(src):
    if m.group(1):
        tags.append((m.group(1).lower(), m.start()))
    elif m.group(2):
        tags.append((m.group(2).lower(), m.start()))
off = [None]*n
j = 0
pending = []
miss = 0
for i, (nm, par) in enumerate(els):
    ln = nm.lower()
    if j < len(tags) and tags[j][0] == ln:
        off[i] = tags[j][1]; j += 1; continue
    hit = None
    for q in pending[-8:]:
        if tags[q][0] == ln: hit = q; break
    if hit is not None:
        off[i] = tags[hit][1]; pending.remove(hit); continue
    for d in range(1, 9):
        if j + d < len(tags) and tags[j + d][0] == ln:
            pending.extend(range(j, j + d)); off[i] = tags[j + d][1]; j += d + 1; break
    else:
        miss += 1
print('unmatched elements (implied or dropped):', miss, 'tags', len(tags), 'elements', n, file=sys.stderr)
if spine_marker:
    at = src.index(spine_marker)
    at = src.rfind('<', 0, at)
    spine = off.index(at)
sk = kids[spine]
print('spine element', spine, els[spine][0], 'children', len(sk), 'elements', n, file=sys.stderr)
for pc in pcts:
    k = min(range(1, len(sk)), key=lambda c: abs(sk[c] / n - pc))
    e = sk[k]
    # the first element from e on that has a matched offset
    q = e
    while off[q] is None: q += 1
    cut = off[q]
    out = f'{outp}.{int(pc*100)}.html'
    with open(out, 'w', encoding='utf-8', errors='surrogateescape') as f:
        f.write(src[:cut])
    print(f'{pc}\tchild {k}/{len(sk)}\telement {e} {els[e][0]}\tcut byte {cut}/{len(src)} ({cut/len(src):.3f})\telements before {e} ({e/n:.3f})\t{out}')
