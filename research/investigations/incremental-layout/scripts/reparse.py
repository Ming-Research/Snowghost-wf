"""Applies text edits of an edit script to the page's HTML source and dumps
the edited source with the plain `dump` mode: the re-parse oracle of X5's
edit application (research/investigations/incremental-layout/DESIGN.md,
Q73), independent of `layout_oracle edit`.

usage: python3 reparse.py HTML NODES SCRIPT OUTDIR DRIVER UA COUNT [SUFFIX=SHEET ...]

For the first COUNT forward T and B edits of SCRIPT that suit it, writes the page
with the same insertion made in its source to OUTDIR/reparse-I.html (I being
the edit's number, counting the script's edits from 1), runs
`DRIVER dump 1 FILE UA SUFFIX=SHEET ...` on it and prints `reparse I hash H
bytes N` in the format of `layout_oracle edit`, or `reparse I skipped` for a
forward edit that does not suit the source. An edit suits the source when
the data of its Text node, which NODES lists, occurs exactly once in the
source byte for byte, so the parser's character references and newline
rules did not touch it; the insertion is then made at the same byte offset
inside that occurrence. A B edit is made as `<p>TEXT</p>` before the start tag
that precedes the data of its BEFORE element's first child, a Text node
found once in the source, so BEFORE must be a p element with no attributes
holding such text first. The script's S lines are not applied here: pass the
sheets that only the edit mode adds as extra SUFFIX=SHEET arguments (the
kinds this is used for have none)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from edits import Tree, unescape  # noqa: E402


def fnv1a(data):
    state = 0xcbf29ce484222325
    for byte in data:
        state = ((state ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return state


def main():
    html, nodes, script, outdir, driver, ua, count = sys.argv[1:8]
    sheets = sys.argv[8:]
    count = int(count)
    tree = Tree(nodes)
    data_of = {t['node']: t['data'] for t in tree.texts}
    source = open(html, 'rb').read()
    os.makedirs(outdir, exist_ok=True)
    number = 0
    done = 0
    for line in open(script, 'rb'):
        line = line.rstrip(b'\n')
        if line[:1] not in (b'T', b'D', b'C', b'K', b'B', b'X'):
            continue
        number += 1
        if line[:1] == b'T':
            _, node, offset, text = line.split(b' ', 3)
            node, offset = int(node), int(offset)
            data = data_of[node]
            if source.count(data) != 1:
                print('edit %d: text node %d occurs %d times in the source, skipped' %
                      (number, node, source.count(data)), file=sys.stderr)
                print('reparse %d skipped' % number)
                continue
            at = source.index(data) + offset
            edited = source[:at] + unescape(text) + source[at:]
        elif line[:1] == b'B':
            _, parent, before, text = line.split(b' ', 3)
            data = tree.first_text.get(int(before))
            if data is None or source.count(data) != 1:
                print('edit %d: element %s has no Text first child found once in the source, skipped' %
                      (number, before.decode()), file=sys.stderr)
                print('reparse %d skipped' % number)
                continue
            # The start tag of the p element is the last `<p` before its text.
            at = source.rfind(b'<p', 0, source.index(data))
            if at < 0 or source[at + 2:at + 3] not in (b' ', b'>'):
                print('edit %d: no plain <p start tag before its text, skipped' % number, file=sys.stderr)
                print('reparse %d skipped' % number)
                continue
            edited = source[:at] + b'<p>' + unescape(text) + b'</p>' + source[at:]
        else:
            continue
        path = os.path.join(outdir, 'reparse-%d.html' % number)
        with open(path, 'wb') as f:
            f.write(edited)
        dump = subprocess.run([driver, 'dump', '1', path, ua] + sheets, capture_output=True, check=True).stdout
        print('reparse %d hash %016x bytes %d' % (number, fnv1a(dump), len(dump)))
        done += 1
        if done >= count:
            break


if __name__ == '__main__':
    main()
