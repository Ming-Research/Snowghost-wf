"""Edit-script generator of experiment X5 (research/investigations/incremental-layout/DESIGN.md).

usage: python3 edits.py PAGE NODES OUTDIR [--dump DUMP] [--count N]

PAGE     ecma262, html5 or apollo11; the seed is 20261002 plus the sum of the
         character codes of its name, as experiment X1 seeds its generator.
NODES    the output of `layout_oracle nodes 0 PAGE UA ...` on that page.
OUTDIR   receives PAGE-KIND.edits for the kinds word, sentence, colour,
         fontsize, rootfont and block, and PAGE-session-typing.edits and
         PAGE-session-scattered.edits.
--dump   the output of `layout_oracle dump 1 PAGE UA ...`; when given, edits
         are drawn only from the text nodes and elements that have boxes, as
         X1 draws its edits from the boxed ones.
--count  edits per kind, 30 by default and 10 for ecma262 (the typing and
         scattered sessions always hold 100).

A kind's script holds one S line (for the kinds that need a style sheet) and
then COUNT edits of that kind, each followed by its inverse (D, K or X), so
that the document returns to its initial state between edits. The language is the one `layout_oracle edit`
reads (renderer/oracle/layout/module.wfm). Python 3 standard library only."""
import argparse
import os
import random
import sys

SEED = 20261002

# X1's text (experiments/x1-x3-x16/lib.py), so that the edits are the same kinds.
WORDS = ['alpha', 'quickly', 'brown', 'sentinel', 'harbor', 'lantern', 'mosaic', 'notable',
         'orchard', 'pebble', 'quartz', 'ripple', 'summit', 'timber', 'velvet', 'whisper']
SENTENCE = b'This extra sentence was added by the edit script to test how local the change stays. '
BLOCK = (b'A new paragraph inserted at this point of the page by the edit script, long enough '
         b'to wrap onto a second line of text in a typical content column of the page.')

# X1's text_sites() skips the text of these elements.
NO_TEXT_EDIT = {'pre', 'textarea', 'script', 'style', 'title', 'code', 'option'}

SHEET_COLOUR = b'S .x5c{color:#123456}'
SHEET_FONTSIZE = b'S .x5f{font-size:130%}'
ROOT_FONTS = [(b'x5r12', b'12px'), (b'x5r20', b'20px'), (b'x5r24', b'24px')]


def unescape(data):
    out = bytearray()
    i = 0
    while i < len(data):
        c = data[i]
        if c == 0x5c and i + 1 < len(data) and data[i + 1] == 0x5c:
            out.append(0x5c)
            i += 2
        elif c == 0x5c and i + 1 < len(data) and data[i + 1] == 0x6e:
            out.append(0x0a)
            i += 2
        else:
            out.append(c)
            i += 1
    return bytes(out)


class Tree:
    """The nodes listing: elements with their parent, and text nodes."""

    def __init__(self, path):
        self.elements = []  # dict(node, depth, name, below, index, parent)
        self.texts = []     # dict(node, parent, size, data)
        self.arena = None
        self.first_text = {}  # element node -> data of its first child, when a Text node
        opened = None         # the element whose line came last
        stack = []          # (depth, node id) of the open elements
        with open(path, 'rb') as f:
            for raw in f:
                line = raw.rstrip(b'\n')
                if line.startswith(b'E '):
                    _, node, depth, name, below, index = line.split(b' ')
                    depth = int(depth)
                    while stack and stack[-1][0] >= depth:
                        stack.pop()
                    parent = stack[-1][1] if stack else None
                    stack.append((depth, int(node)))
                    opened = int(node)
                    self.elements.append({'node': int(node), 'depth': depth, 'name': name.decode(),
                                          'below': int(below), 'index': int(index), 'parent': parent})
                elif line.startswith(b'T '):
                    _, node, parent, size, data = line.split(b' ', 4)
                    data = unescape(data)
                    if len(data) != int(size):
                        raise SystemExit('nodes: text %s has %d bytes, the line says %s' %
                                         (node.decode(), len(data), size.decode()))
                    self.texts.append({'node': int(node), 'parent': int(parent), 'data': data})
                    if opened == int(parent):
                        self.first_text[int(parent)] = data
                    opened = None
                elif line.startswith(b'N '):
                    self.arena = int(line.split(b' ')[1])
        if self.arena is None:
            raise SystemExit('nodes: no N line; build the driver from the same revision as this script')
        self.by_node = {e['node']: e for e in self.elements}


def boxed_sets(path):
    """The traversal indices of the elements with boxes and the ordinals of
    the text nodes with rectangles, from a dump (E lines: index, name, parent,
    level, rectangles; T lines: ordinal, parent, rectangles)."""
    elements, texts = set(), set()
    with open(path, 'rb') as f:
        for raw in f:
            line = raw.rstrip(b'\n').split(b'\t')
            if line[0] == b'E' and line[4] != b'n':
                elements.add(int(line[1]))
            elif line[0] == b'T':
                texts.add(int(line[1]))
    return elements, texts


def text_sites(tree, rng, boxed_texts, want, after_period=False):
    """Insertion points as X1's text_sites() finds them: a text node whose
    stripped data has at least 90 bytes, under an element that is not in
    NO_TEXT_EDIT, at a space with 20 bytes of the data on each side (after a
    period and a space when after_period)."""
    candidates = []
    for ordinal, text in enumerate(tree.texts):
        if boxed_texts is not None and ordinal not in boxed_texts:
            continue
        parent = tree.by_node.get(text['parent'])
        if parent is None or parent['name'] in NO_TEXT_EDIT:
            continue
        if len(text['data'].strip()) < 90:
            continue
        candidates.append(text)
    rng.shuffle(candidates)
    sites = []
    for text in candidates:
        data = text['data']
        spaces = [p for p in range(21, len(data) - 20) if data[p] == 0x20]
        if after_period:
            spaces = [p for p in spaces if data[p - 1] == 0x2e]
        if not spaces:
            continue
        sites.append((text['node'], rng.choice(spaces) + 1))
        if len(sites) >= want:
            break
    return sites


def script(sheet, pairs):
    lines = [sheet] if sheet else []
    for forward, inverse in pairs:
        lines.append(forward)
        if inverse is not None:
            lines.append(inverse)
    return b'\n'.join(lines) + b'\n'


def insertion(node, offset, text):
    return (b'T %d %d ' % (node, offset) + text,
            b'D %d %d %d' % (node, offset, len(text)))


def generate(page, tree, boxed, count):
    boxed_elements = boxed[0] if boxed else None
    boxed_texts = boxed[1] if boxed else None
    scripts = {}

    def rng_of(kind):
        return random.Random('%d-%s-%s' % (SEED + sum(map(ord, page)), page, kind))

    # word: X1's word edit, a word and a space inserted at a space
    rng = rng_of('word')
    sites = text_sites(tree, rng, boxed_texts, count)
    scripts['word'] = script(None, [
        insertion(node, offset, rng.choice(WORDS).encode() + b' ') for node, offset in sites])

    # sentence: a sentence inserted after a period and a space
    rng = rng_of('sentence')
    sites = text_sites(tree, rng, boxed_texts, count, after_period=True)
    scripts['sentence'] = script(None, [insertion(node, offset, SENTENCE) for node, offset in sites])

    # colour: class x5c on a random boxed element
    rng = rng_of('colour')
    pool = [e for e in tree.elements if boxed_elements is None or e['index'] in boxed_elements]
    chosen = rng.sample(pool, min(count, len(pool)))
    scripts['colour'] = script(SHEET_COLOUR, [
        (b'C %d x5c' % e['node'], b'K %d x5c' % e['node']) for e in chosen])

    # fontsize: class x5f on an element with at least 5 element descendants
    rng = rng_of('fontsize')
    pool = [e for e in pool if e['below'] >= 5]
    chosen = rng.sample(pool, min(count, len(pool)))
    scripts['fontsize'] = script(SHEET_FONTSIZE, [
        (b'C %d x5f' % e['node'], b'K %d x5f' % e['node']) for e in chosen])

    # rootfont: the three font sizes on the html element in turn
    html = tree.elements[0]
    if html['name'] != 'html':
        raise SystemExit('nodes: the first element is %s, not html' % html['name'])
    sheet = b'S ' + b''.join(b'.%s{font-size:%s}' % entry for entry in ROOT_FONTS)
    scripts['rootfont'] = script(sheet, [
        (b'C %d %s' % (html['node'], ROOT_FONTS[k % 3][0]), b'K %d %s' % (html['node'], ROOT_FONTS[k % 3][0]))
        for k in range(count)])

    # block: a paragraph before a random p element, under its parent. A B edit
    # creates two nodes, the p and its text, at the end of the arena, so the
    # k-th created p has the identifier arena + 2k (the N line of the listing).
    rng = rng_of('block')
    pool = [e for e in tree.elements if e['name'] == 'p' and e['parent'] is not None
            and (boxed_elements is None or e['index'] in boxed_elements)]
    chosen = rng.sample(pool, min(count, len(pool)))
    pairs = []
    for k, e in enumerate(chosen):
        pairs.append((b'B %d %d ' % (e['parent'], e['node']) + BLOCK, b'X %d' % (tree.arena + 2 * k)))
    scripts['block'] = script(None, pairs)

    # sessions: 100 word edits, no inverses. Typing continues after the
    # previous word at one point; scattered edits go to 100 different nodes.
    rng = rng_of('session-typing')
    site = text_sites(tree, rng, boxed_texts, 1)[0]
    pairs = []
    offset = site[1]
    for _ in range(100):
        word = rng.choice(WORDS).encode() + b' '
        pairs.append((b'T %d %d ' % (site[0], offset) + word, None))
        offset += len(word)
    scripts['session-typing'] = script(None, pairs)

    rng = rng_of('session-scattered')
    sites = text_sites(tree, rng, boxed_texts, 100)
    pairs = [(b'T %d %d ' % (node, offset) + rng.choice(WORDS).encode() + b' ', None) for node, offset in sites]
    scripts['session-scattered'] = script(None, pairs)
    return scripts


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('page')
    parser.add_argument('nodes')
    parser.add_argument('outdir')
    parser.add_argument('--dump')
    parser.add_argument('--count', type=int)
    args = parser.parse_args()
    count = args.count or (10 if args.page == 'ecma262' else 30)
    tree = Tree(args.nodes)
    boxed = boxed_sets(args.dump) if args.dump else None
    os.makedirs(args.outdir, exist_ok=True)
    for kind, body in generate(args.page, tree, boxed, count).items():
        path = os.path.join(args.outdir, '%s-%s.edits' % (args.page, kind))
        with open(path, 'wb') as f:
            f.write(body)
        edits = sum(1 for line in body.split(b'\n') if line[:1] in (b'T', b'D', b'C', b'K', b'B', b'X'))
        print('%s: %d edit lines' % (path, edits), file=sys.stderr)


if __name__ == '__main__':
    main()
