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
this generator never builds it. The intrinsic-margin case re-queries the
edited item's intrinsic contributions while its used width stays fixed,
then edits the paragraph beside a retained atomic inline with percentage
margins; flow-root and floated children cover the other intrinsic margin
readers without letting a query replace their used margins. The inline,
floated and positioned flex-owner cases insert inside a flex item but cross
a Text/atomic, Float or Out entry in the enclosing flow. Each structural
edit is expected to refuse before publication with reason 2 and still match
its full rebuild; later text edits verify retained route correctness.

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

The edit-cost kind reuses the transfer page unchanged. It combines one-character
round trips with height-changing sentence round trips across relative, expired
float, negative-margin re-entry, constrained sibling and marker barriers.

The edit-cascade kind shares the unchanged transfer page in one flow, grows
several paragraphs before undoing them in reverse order, and makes later
reference restarts consume geometry translated by earlier edits. It targets
stale global reference scratch that an immediate edit/undo pair can hide.

The positioned-isolated kind retains the original positioned edits and isolates
the percentage-height fixture in its own flow root, so unrelated seams can
reach anchor publication; the original positioned kind remains unchanged.

The edit-height and edit-baseline kinds reuse style-case.html. The height
fixture uses flex baseline alignment; downward inline vertical alignment
changes its line height. The baseline fixture fixes line height while changing
font size inside a flow root within an inline-block body. The existing real
head/title element is made visible as its baseline peer, so a stale baseline
moves geometry that the DOM dump observes. Independent mutations suppress the
height or last-baseline equality guard, and each must be detected.

Python's standard library has no native parser for the driver's node listing,
so it reuses edits.Tree.
"""
import argparse
from pathlib import Path
import subprocess

from edits import Tree


CASES = {
    'edit-cascade': ('reference-suffix-reader',),
    'edit-baseline': ('baseline-only',),
    'edit-height': ('height-only',),
    'edit-cost': ('transfer-relative-sibling', 'transfer-clear-expired',
                  'transfer-clear-reentry', 'transfer-maximum-sibling',
                  'transfer-marker-lined'),
    'positioned': ('positioned-auto', 'positioned-growing', 'positioned-fixed',
                   'positioned-nested', 'positioned-atomic'),
    'transfer': ('transfer-clear-reentry', 'transfer-clear-expired',
                 'transfer-float-expired', 'transfer-marker-lined',
                 'transfer-fixed-sibling', 'transfer-minimum-sibling',
                 'transfer-maximum-sibling', 'transfer-relative-sibling'),
    'flex': ('flex-row-stretch', 'flex-row-start', 'flex-column-start',
             'flex-column-stretch', 'flex-grow', 'flex-shrink', 'flex-wrap',
             'flex-percentage', 'flex-intrinsic-margin', 'flex-inline-owner',
             'flex-float-owner', 'flex-positioned-owner'),
}

CASES['positioned-isolated'] = CASES['positioned']


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
    if kind == 'positioned-isolated':
        lines.append('S .growing{display:flow-root}')
    if kind in ('edit-baseline', 'edit-height'):
        inline = [element for element in tree.elements if element['name'] == 'em']
        if len(inline) != 1:
            raise ValueError('expected one inline em in the unchanged style fixture')
        node = inline[0]['node']
        lines.append('S head{display:inline-block;width:200px} title{display:block;font-size:16px;line-height:20px} head>style{display:none} body{display:inline-block;width:300px} body>div,body>p{display:none} body>p:nth-of-type(1){display:flow-root;width:300px;font-size:0;line-height:0} em{font-size:16px;line-height:40px} .costbaseline{font-size:24px} .costdescent{vertical-align:-30px}')
        token = 'costbaseline'
        if kind == 'edit-height':
            lines = ['S body{display:flex;align-items:baseline;width:2000px} p{width:2000px;min-width:0;flex-shrink:0;line-height:40px} p::before{content:"barrier";display:block;position:relative} .costdescent{vertical-align:-30px}']
            token = 'costdescent'
        lines.extend(('C %d %s' % (node, token), 'K %d %s' % (node, token)))
        lines.extend(('P 0', 'P 1', 'P 2'))
        return '\n'.join(lines) + '\n'
    if kind == 'edit-cascade':
        lines.append('S section{display:block}')
        prefix = 'A longer sentence moves the following retained paragraphs. ' * 5
        nodes = [marker(tree, case, role)['node'] for case in
                 ('transfer-clear-expired', 'transfer-float-expired',
                  'transfer-marker-lined', 'transfer-relative-sibling')
                 for role in ('retained', 'probe')]
        for node in nodes:
            lines.append('T %d 0 %s' % (node, prefix))
        for node in reversed(nodes):
            lines.append('D %d 0 %d' % (node, len(prefix.encode())))
        return '\n'.join(lines) + '\n'
    if kind == 'edit-cost':
        prefix = 'A longer sentence changes the paragraph height and following origins. ' * 5
        for case in CASES[kind]:
            node = marker(tree, case, 'retained')['node']
            text_pair(lines, node)
            lines.extend(('T %d 0 %s' % (node, prefix),
                          'D %d 0 %d' % (node, len(prefix.encode()))))
        return '\n'.join(lines) + '\n'
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
    fixture_kind = {'edit-cascade': 'transfer', 'positioned-isolated': 'positioned', 'edit-cost': 'transfer', 'edit-baseline': 'style', 'edit-height': 'style'}.get(args.kind, args.kind)
    fixture = Path(__file__).resolve().with_name(fixture_kind + '-case.html')
    fixture = fixture.relative_to(Path.cwd())
    nodes = args.output.with_suffix(args.output.suffix + '.nodes')
    with nodes.open('w') as output:
        subprocess.run([args.driver, 'nodes', '0', str(fixture),
                        'renderer/style/ua.css'], stdout=output, check=True)
    edits = generate(Tree(nodes), args.kind)
    args.output.write_text(edits)
    print('%s: %d cases, %d edits' %
          (args.output, len(CASES[args.kind]), sum(line.split()[0] in ('T', 'D', 'C', 'K', 'B', 'X') for line in edits.splitlines() if line.split())))


if __name__ == '__main__':
    main()
