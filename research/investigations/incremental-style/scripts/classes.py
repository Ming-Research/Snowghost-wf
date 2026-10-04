"""Writes the class edit scripts of M1 for one page (run.sh scripts).

    classes.py PAGE NODES OUTDIR [SHEET ...]

NODES is the page's node listing (layout_oracle nodes mode, as X5's run.sh
prepare writes it), SHEET the page's linked style sheets. It writes:

PAGE-classes.edits  40 toggles (C then K) of a class word that the page's
                    own style sheets name, on a random element, so the
                    page's own selectors and combinators decide what each
                    edit restyles;
PAGE-body.edits     a sheet whose rules name class x5b only in compounds
                    left of a descendant, child or sibling combinator,
                    toggled three times on body and once on ten random
                    elements.

The choices are seeded by the page name, so the scripts are reproducible.
"""
import random
import re
import sys


def main():
    page, nodes, out, sheets = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    elements, body, css, style_nodes = [], None, [], set()
    for line in open(nodes, encoding='utf-8', errors='replace'):
        fields = line.rstrip('\n').split(' ', 4)
        if fields[0] == 'E':
            node, name = int(fields[1]), fields[3]
            elements.append(node)
            if name == 'body':
                body = node
            if name == 'style':
                style_nodes.add(node)
        elif fields[0] == 'T' and int(fields[2]) in style_nodes:
            css.append(fields[4].replace('\\n', '\n'))
    for sheet in sheets:
        css.append(open(sheet, encoding='utf-8', errors='replace').read())
    text = re.sub(r'/\*.*?\*/', '', '\n'.join(css), flags=re.S)
    words = sorted(set(re.findall(r'\.(-?[A-Za-z_][\w-]*)', text)) - {'x5b'})
    if body is None or not words:
        sys.exit('classes.py: %s has no body element or no class word' % page)
    rng = random.Random('restyle-' + page)
    lines = []
    for _ in range(40):
        element, word = rng.choice(elements), rng.choice(words)
        lines += ['C %d %s' % (element, word), 'K %d %s' % (element, word)]
    with open('%s/%s-classes.edits' % (out, page), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    lines = ['S .x5b p{color:#123456}.x5b>div{padding-left:1px}.x5b~*{color:red}']
    for _ in range(3):
        lines += ['C %d x5b' % body, 'K %d x5b' % body]
    for element in rng.sample(elements, 10):
        lines += ['C %d x5b' % element, 'K %d x5b' % element]
    with open('%s/%s-body.edits' % (out, page), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('%s: %d elements, %d class words, body %d' % (page, len(elements), len(words), body))


main()
