"""Generate the positioned/flex/transfer splice fixtures' edits from driver node IDs.

Run from the repository root with the CI-built driver and fonts available:
    s=research/investigations/incremental-layout/scripts
    python3 "$s/splice-cases.py" build/layout_oracle_seq positioned build/positioned-case.edits
    build/layout_oracle_seq edit build/positioned-case.edits "$s/positioned-case.html" renderer/style/ua.css > build/positioned-case.raw
    python3 "$s/inctime.py" --check build/positioned-case.edits build/positioned-case.raw
    python3 "$s/splice-cases.py" --check-paths build/positioned-case.edits.paths build/positioned-case.raw
Use flex or transfer in place of positioned for the other fixtures. The existing
inctime.py requires every operation to match a full rebuild; unsupported
semantic cases may use their counted structural fallback.

Each ordinary case inserts a paragraph before its retained marker, edits retained,
new and dependent text, removes the paragraph, then edits the retained and
dependent text again. Insert/delete text pairs restore the original text.
The document is restored before the next case, so cases do not depend on
one another's geometry. Within a case the edits are ordered because each
operation consumes the preceding retained layout and its published routes.

The fixed-height positioned cases isolate static-anchor displacement from
containing-block resizing. The growing case changes both percentage height
and top/bottom stretch; nested anchors expose translating descendants twice;
the atomic cases move inline-blocks with their paragraphs, including opposing
vertical margins whose offsets must not be hidden by anchor cancellation. The row stretch
case changes the sibling's height and its child's percentage height. Column
grow/shrink change free space through the edited item's auto flex basis.
Column wrap crosses the fixed main extent after insertion, changing which
items share a line. Percentage items exercise counted fallback when their
dependencies are outside the splice argument. CI supplies the renderer;
this generator never builds it. The intrinsic-margin case re-queries the
edited item's intrinsic contributions while its used width stays fixed,
then edits the paragraph beside a retained atomic inline with percentage
margins; flow-root and floated children cover the other intrinsic margin
readers without letting a query replace their used margins. The intrinsic-position
case instead edits only the sibling probe between insertion and removal:
editing the owner would resolve its children's margins again. Its fixed-size
absolute child has a percentage left margin and explicit left inset, so the
removal's positioned settlement reads the retained margin after the first
splice's intrinsic query. A mutation that overwrites that margin with its
zero-basis intrinsic value must change the positioned child's dumped x.
The inline, floated and positioned flex-owner cases insert inside a flex item but cross
a Text/atomic, Float or Out entry in the enclosing flow. Each structural
edit is expected to refuse before publication with reason 2 and still match
its full rebuild; later text edits verify retained route correctness. The
<output>.paths sidecar records these three cases' required structural
fallbacks and the intrinsic-position case's required successful splices,
using the generated commands' operation numbers. --check-paths
checks each required row exactly once; inctime.py separately validates the
complete protocol and identity. Other fixture kinds have empty sidecars.

The transfer fixture isolates eight cases behind separate flow roots:
transfer-clear-reentry has an earlier float ending at 100px, an owner at
200px whose first line puts the seam at 220px, and a later -170px margin
before clear:left. The later natural position is 70px before insertion and
90px after it. The float is expired
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
import re
import sys
from pathlib import Path
import subprocess

from edits import Tree


CASES = {
    'positioned': ('positioned-auto', 'positioned-growing', 'positioned-fixed',
                   'positioned-nested', 'positioned-atomic',
                   'positioned-atomic-cancel'),
    'transfer': ('transfer-clear-reentry', 'transfer-clear-expired',
                 'transfer-float-expired', 'transfer-marker-lined',
                 'transfer-fixed-sibling', 'transfer-minimum-sibling',
                 'transfer-maximum-sibling', 'transfer-relative-sibling'),
    'flex': ('flex-row-stretch', 'flex-row-start', 'flex-column-start',
             'flex-column-stretch', 'flex-grow', 'flex-shrink', 'flex-wrap',
             'flex-percentage', 'flex-intrinsic-margin', 'flex-inline-owner',
             'flex-float-owner', 'flex-positioned-owner',
             'flex-intrinsic-position'),
}


OWNER_FALLBACK_CASES = frozenset(('flex-inline-owner', 'flex-float-owner',
                                  'flex-positioned-owner'))


def check_paths(expected_path, raw_path):
    """Require each selected structural path exactly once without parsing edits."""
    expected = {}
    for line in expected_path.read_text().splitlines():
        match = re.fullmatch(r'structure path (\d+) splice ([01]) reason (\d+)', line)
        if match is None or match[1] in expected:
            raise ValueError('%s: malformed or duplicate expectation: %s' %
                             (expected_path, line))
        expected[match[1]] = line
    found = {number: [] for number in expected}
    for line in raw_path.read_text().splitlines():
        match = re.match(r'structure path (\d+)(?: |$)', line)
        if match and match[1] in found:
            found[match[1]].append(line)
    for number, wanted in expected.items():
        if found[number] != [wanted]:
            raise ValueError('%s: expected exactly one %r, found %r' %
                             (raw_path, wanted, found[number]))
    print('%s: %d required structural paths matched' % (raw_path, len(expected)))


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
    paths = []
    for number, case in enumerate(CASES[kind]):
        retained = marker(tree, case, 'retained')
        probe = marker(tree, case, 'probe')
        paragraph = tree.by_node[retained['parent']]
        if paragraph['name'] != 'p' or paragraph['parent'] is None:
            raise ValueError(case + ': retained marker must be a paragraph child')
        created = tree.arena + 2 * number
        lines.append('B %d %d Inserted block.' %
                     (paragraph['parent'], paragraph['node']))
        if case in OWNER_FALLBACK_CASES:
            paths.append('structure path %d splice 0 reason 2' % len(lines))
        if case == 'flex-intrinsic-position':
            paths.append('structure path %d splice 1 reason 0' % len(lines))
            after_insert = (probe['node'],)
        else:
            after_insert = (retained['node'], created + 1, probe['node'])
        for node in after_insert:
            text_pair(lines, node)
        lines.append('X %d' % created)
        if case in OWNER_FALLBACK_CASES:
            paths.append('structure path %d splice 0 reason 2' % len(lines))
        if case == 'flex-intrinsic-position':
            paths.append('structure path %d splice 1 reason 0' % len(lines))
        for node in (retained['node'], probe['node']):
            text_pair(lines, node)
    return '\n'.join(lines) + '\n', ''.join(line + '\n' for line in paths)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--check-paths':
        parser = argparse.ArgumentParser(description=check_paths.__doc__)
        parser.add_argument('--check-paths', nargs=2, type=Path, required=True,
                            metavar=('EXPECTED', 'RAW'))
        args = parser.parse_args()
        check_paths(*args.check_paths)
        return
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
    edits, paths = generate(Tree(nodes), args.kind)
    args.output.write_text(edits)
    args.output.with_suffix(args.output.suffix + ".paths").write_text(paths)
    print('%s: %d cases, %d edits' %
          (args.output, len(CASES[args.kind]), len(edits.splitlines())))


if __name__ == '__main__':
    main()
