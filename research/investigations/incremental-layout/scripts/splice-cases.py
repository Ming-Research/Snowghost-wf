"""Generate the positioned/flex/transfer splice fixtures' edits from driver node IDs.

Run from the repository root with the CI-built driver and fonts available:
    s=research/investigations/incremental-layout/scripts
    python3 "$s/splice-cases.py" build/layout_oracle_seq positioned build/positioned-case.edits
    build/layout_oracle_seq edit build/positioned-case.edits "$s/positioned-case.html" renderer/style/ua.css > build/positioned-case.raw
    python3 "$s/inctime.py" --check build/positioned-case.edits build/positioned-case.raw
Use flex or transfer in place of positioned for the other fixtures. The existing
inctime.py requires every operation to match a full rebuild; unsupported
semantic cases may use their counted structural fallback.

Each case inserts a paragraph before its retained marker, edits retained,
new and dependent text, removes the paragraph, then edits the retained and
dependent text again. Insert/delete text pairs restore the original text.
The document is restored before the next case, so cases do not depend on
one another's geometry. Within a case the edits are ordered because each
operation consumes the preceding retained layout and its published routes.

The fixed-height positioned cases isolate static-anchor displacement from
containing-block resizing. The growing case changes both percentage height
and top/bottom stretch; nested anchors expose translating descendants twice;
the atomic case moves an inline-block with its paragraph. The row stretch
case changes the sibling's height and its child's percentage height. Column
grow/shrink change free space through the edited item's auto flex basis.
Column wrap crosses the fixed main extent after insertion, changing which
items share a line. Percentage items exercise counted fallback when their
dependencies are outside the splice argument. CI supplies the renderer;
this generator never builds it.

The transfer fixture isolates eight cases behind separate flow roots:
transfer-clear-reentry has an earlier float ending at 100px, a seam at
200px and a later -170px margin before clear:left, so the later natural
position is 50px before insertion and 70px after it. The float is expired
at the seam but clearance still holds the probe at 100px. This case must
reject uniform suffix translation or replay its float-dependent region.
transfer-clear-expired and transfer-float-expired keep every later natural
position below the earlier float; transfer-marker-lined keeps real content
lines in an outside-marker owner. transfer-fixed-sibling,
transfer-minimum-sibling and transfer-maximum-sibling retain separate
specified/minimum/maximum height constraints in later siblings, whose
interiors stay unchanged while their anchors move. transfer-relative-sibling
moves a later sibling with a nonzero visual offset. These seven cases are
candidates for certified translation; the governing argument owns their
final splice/fallback classification. Identity is required for all eight.

Python's standard library has no native
parser for the driver's node listing, so it reuses edits.Tree.
"""
import argparse
from pathlib import Path
import subprocess

from edits import Tree


CASES = {
    'positioned': ('positioned-auto', 'positioned-growing', 'positioned-fixed',
                   'positioned-nested', 'positioned-atomic'),
    'transfer': ('transfer-clear-reentry', 'transfer-clear-expired',
                 'transfer-float-expired', 'transfer-marker-lined',
                 'transfer-fixed-sibling', 'transfer-minimum-sibling',
                 'transfer-maximum-sibling', 'transfer-relative-sibling'),
    'flex': ('flex-row-stretch', 'flex-row-start', 'flex-column-start',
             'flex-column-stretch', 'flex-grow', 'flex-shrink', 'flex-wrap',
             'flex-percentage'),
}


def marker(tree, case, role):
    """Resolve one exact marker, refusing fixtures with missing/duplicate text."""
    wanted = ('M2 %s %s.' % (role, case)).encode()
    found = [text for text in tree.texts if text['data'] == wanted]
    if len(found) != 1:
        raise ValueError('%s: expected one %s marker, found %d' %
                         (case, role, len(found)))
    return found[0]


def text_pair(lines, node):
    """Insert and remove one byte without changing a following operation's text."""
    lines.extend(('T %d 0 R' % node, 'D %d 0 1' % node))


def generate(tree, kind):
    """Exercise each independent fixture and its text routes after both edits."""
    lines = []
    for number, case in enumerate(CASES[kind]):
        retained = marker(tree, case, 'retained')
        probe = marker(tree, case, 'probe')
        paragraph = tree.by_node[retained['parent']]
        if paragraph['name'] != 'p' or paragraph['parent'] is None:
            raise ValueError(case + ': retained marker must be a paragraph child')
        created = tree.arena + 2 * number
        lines.append('B %d %d Inserted block.' %
                     (paragraph['parent'], paragraph['node']))
        for node in (retained['node'], created + 1, probe['node']):
            text_pair(lines, node)
        lines.append('X %d' % created)
        for node in (retained['node'], probe['node']):
            text_pair(lines, node)
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('driver')
    parser.add_argument('kind', choices=CASES)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    fixture = Path(__file__).resolve().with_name(args.kind + '-case.html')
    fixture = fixture.relative_to(Path.cwd())
    nodes = args.output.with_suffix(args.output.suffix + '.nodes')
    with nodes.open('w') as output:
        subprocess.run([args.driver, 'nodes', '0', str(fixture),
                        'renderer/style/ua.css'], stdout=output, check=True)
    edits = generate(Tree(nodes), args.kind)
    args.output.write_text(edits)
    print('%s: %d cases, %d edits' %
          (args.output, len(CASES[args.kind]), len(edits.splitlines())))


if __name__ == '__main__':
    main()
