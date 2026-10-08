"""Generate sequence-range displacement discriminators and compare every edit to full layout.

Usage: range-displacement.py DRIVER OUTPUT_DIR [--case NAME]
The hosted workflow supplies the compiled driver. Each generated page and edit
script exercises one premise of the range contract in
research/investigations/m2-edit-cost/SPLIT-CONTRACT.md#sequence-range-displacement-contract:
rotations in both directions and insertion after prior motion, successor
transplantation, point replacement between opposite shifts, atomic point
encoding without sibling movement, viewport versus block-owned positioned
entries, zero absolute displacement with owner rebasing, natural floors read by
a later edit, the latest basis assignment consumed by splice reuse, and the full
bridge after wide structural relocation. Font-size class edits take the hybrid
reference path; wrapping text edits take the ordinary boundary path; B/X edits
take the structural splice. The independent oracle is full layout of the same
edited document: every incremental edit must report `inc same`.
"""
import argparse
import re
import subprocess
from pathlib import Path

import inctime
from edits import Tree

BASE = ('html,body{margin:0;padding:0}body{font:16px/20px monospace}'
        'section{display:flow-root;width:400px}p{margin:4px 0}.big{font-size:28px;line-height:36px}')
LONG = ' growing words wrap onto further lines of this narrow measure'


def page(body, css=''):
    return '<!doctype html><html><head><style>' + BASE + css + '</style></head><body>' + body + '</body></html>'


def text(tree, marker):
    found = [t for t in tree.texts if t['data'].startswith(marker.encode())]
    if len(found) != 1:
        raise ValueError((marker, len(found)))
    return found[0]


def element_of(tree, marker):
    return text(tree, marker)['parent']


def first(tree, tag):
    return next(e['node'] for e in tree.elements if e['name'] == tag)


def paragraphs(count, prefix='P'):
    return ''.join('<p>%s%02d.</p>' % (prefix, i) for i in range(count))


def grow(tree, marker):
    node = element_of(tree, marker)
    return [f'C {node} big'], [f'K {node} big']


def wrap(tree, marker):
    node = text(tree, marker)
    offset = len(node['data'])
    escaped = LONG.replace('\\', '\\\\')
    return [f'T {node["node"]} {offset} {escaped}'], [f'D {node["node"]} {offset} {len(LONG)}']


def fixtures():
    # Insertions at the front force right rotations, at the end left
    # rotations, after a hybrid and an ordinary range already moved the suffix.
    def rotations(tree):
        section = first(tree, 'section')
        lead = element_of(tree, 'P00.')
        tail = None
        hybrid_on, hybrid_off = grow(tree, 'P01.')
        ordinary_on, ordinary_off = wrap(tree, 'P02.')
        made = hybrid_on + ordinary_on
        created = tree.arena
        inserted = []
        for k in range(6):
            made.append(f'B {section} {lead} Front {k}.')
            inserted.append(created)
            created += 2
        for k in range(6):
            made.append(f'B {section} - Back {k}.')
            inserted.append(created)
            created += 2
        made += hybrid_off + ordinary_off + hybrid_on
        made += [f'X {node}' for node in inserted]
        made += hybrid_off
        return made
    yield 'rotations', page('<section>' + paragraphs(24) + '</section>'), rotations

    # Removing a middle entry transplants its successor after motion.
    def transplant(tree):
        hybrid_on, hybrid_off = grow(tree, 'P00.')
        made = list(hybrid_on)
        for marker in ('P12.', 'P07.', 'P16.'):
            made.append(f'X {element_of(tree, marker)}')
        made += hybrid_off
        ordinary_on, ordinary_off = wrap(tree, 'P01.')
        return made + ordinary_on + ordinary_off
    yield 'transplant', page('<section>' + paragraphs(24) + '</section>'), transplant

    # A point replacement inside a moved suffix, then the opposite shift.
    def opposite(tree):
        on, off = grow(tree, 'P00.')
        point_on, point_off = wrap(tree, 'P09.')
        same = text(tree, 'P05.')
        return on + point_on + [f'T {same["node"]} 0 Q', f'D {same["node"]} 0 1'] + off + point_off + on + off
    yield 'opposite-shifts', page('<section>' + paragraphs(16) + '</section>'), opposite

    # Atomic inlines follow their paragraph; a text edit before one re-encodes
    # it without moving siblings, between two opposite paragraph moves.
    # A later splice dirties the boundary, so the next edit restores every
    # payload through the full raw bridge, atomic inlines from the immutable
    # paragraph-frame snapshot.
    def atomic(tree):
        on, off = grow(tree, 'P00.')
        before = text(tree, 'Before ')
        section = first(tree, 'section')
        lead = element_of(tree, 'P01.')
        created = tree.arena
        return (on + [f'T {before["node"]} 0 x', f'D {before["node"]} 0 1'] + off + [f'T {before["node"]} 0 y'] + on + off +
                [f'B {section} {lead} Spliced before.'] + on + off + [f'X {created}'] + on + off)
    body = ('<section>' + paragraphs(3) + '<p>Before <span style="display:inline-block;width:30px;height:24px;'
            'border:1px solid">A</span> after.</p>' + paragraphs(6, 'Q') + '</section>')
    yield 'atomic-point', page(body), atomic

    # A table cell's content adjustment applies once to an atomic inline
    # restored from its paragraph frame; reading restored paragraph scratch
    # would apply it twice.
    def cell(tree):
        on, off = grow(tree, 'P00.')
        holder = first(tree, 'td')
        lead = element_of(tree, 'P01.')
        created = tree.arena
        return on + off + [f'B {holder} {lead} Cell splice.'] + on + off + [f'X {created}'] + on + off
    cell_body = ('<table><tr><td style="height:300px;vertical-align:middle;width:300px">' + paragraphs(3) +
                 '<p>Before <span style="display:inline-block;width:30px;height:24px;border:1px solid">A</span> after.</p>' +
                 paragraphs(2, 'Q') + '</td></tr></table>')
    yield 'atomic-cell', page(cell_body), cell

    # Block-owned absolute and viewport-owned fixed entries in a moved suffix.
    def positioned(tree):
        on, off = grow(tree, 'P00.')
        wrap_on, wrap_off = wrap(tree, 'P01.')
        return on + wrap_on + off + wrap_off + on + off
    body = ('<section style="position:relative">' + paragraphs(4) +
            '<span style="position:absolute;width:10px;height:10px">Abs.</span>' +
            '<span style="position:fixed;width:12px;height:12px">Fixed.</span>' +
            '<div style="position:relative;top:3px;left:2px">' + paragraphs(3, 'R') +
            '<span style="position:absolute;bottom:0;width:8px;height:8px">Inner.</span></div>' +
            paragraphs(3, 'S') + '</section>')
    yield 'positioned-ownership', page(body), positioned

    # A replayed parent moves while its untouched children keep their
    # absolute position: the suffix range needs a nonidentity rebase with a
    # zero displacement.
    def rebase(tree):
        holder = element_of(tree, 'Inner00.')
        while tree.by_node[holder]['name'] != 'div':
            holder = tree.by_node[holder]['parent']
        on, off = grow(tree, 'Inner00.')
        return [f'C {holder} lift'] + on + off + [f'K {holder} lift'] + on + off
    body = ('<section>' + paragraphs(2) + '<div>' + paragraphs(1, 'Inner') + paragraphs(2, 'Kept') +
            '<span style="position:fixed;width:5px;height:5px">Fixed.</span>' +
            '<span style="position:absolute;width:6px;height:6px">Abs.</span>' + paragraphs(3, 'Late') +
            '</div>' + paragraphs(4) + '</section>')
    yield 'zero-rebase', page(body, '.lift{margin-top:-12px;padding-top:12px}'), rebase

    # A float in the suffix keeps a natural floor that a later edit reads.
    def floors(tree):
        on, off = grow(tree, 'P00.')
        later_on, later_off = grow(tree, 'M00.')
        wrap_on, wrap_off = wrap(tree, 'M01.')
        return on + later_on + wrap_on + off + wrap_off + later_off
    body = ('<section>' + paragraphs(3) + '<div style="float:left;width:60px;height:30px">F.</div>' +
            paragraphs(3, 'M') + '<div style="clear:both">' + paragraphs(2, 'C') + '</div>' + paragraphs(3, 'T') + '</section>')
    yield 'natural-floor', page(body), floors

    # Percentage heights read the latest basis assignment when a splice
    # later reuses the moved suffix's boundary.
    def basis(tree):
        section = first(tree, 'section')
        on, off = grow(tree, 'P00.')
        later = element_of(tree, 'H01.')
        while tree.by_node[later]['name'] != 'div':
            later = tree.by_node[later]['parent']
        created = tree.arena
        return on + [f'B {section} {later} Spliced.', f'X {created}'] + off + [f'B {section} {later} Again.', f'X {created + 2}']
    body = '<section style="height:600px">' + paragraphs(2) + ''.join('<div style="height:10%%">H%02d.</div>' % i for i in range(4)) + '</section>'
    yield 'basis-splice', page(body), basis

    # A splice whose following sibling changes its top margin publishes that
    # frontier transfer; later ordinary edits before it join through the
    # stored frontier transfer rather than its range-shifted old one.
    def frontier(tree):
        quote = first(tree, 'blockquote')
        retained = element_of(tree, 'Retained')
        created = tree.arena
        text_node = created + 1
        escaped = LONG.replace('\\', '\\\\')
        return ([f'B {quote} {retained} Inserted head.', f'T {text_node} 14 {escaped}', f'D {text_node} 14 {len(LONG)}'] +
                [f'T {text_node} 14 {escaped}', f'X {created}'])
    body = ('<blockquote><p>Retained paragraph.</p><p>Following paragraph.</p>' + paragraphs(4) + '</blockquote>')
    yield 'frontier-reuse', page(body, 'blockquote{display:block;margin:0;overflow:hidden;width:400px}blockquote>p:first-child{margin-top:0}p{margin:8px 0}'), frontier

    # A wide private relocation forces the full bridge before hybrid replay.
    def wide(tree):
        owner = element_of(tree, 'W00.')
        while tree.by_node[owner]['name'] != 'article':
            owner = tree.by_node[owner]['parent']
        created = tree.arena
        on, off = grow(tree, 'W00.')
        return on + [f'B {owner} - Relocated wide.'] + off + on + [f'X {created}'] + off
    body = '<section>' + paragraphs(2) + '<article style="display:block;padding-left:300px;margin-left:-280px">' + paragraphs(4, 'W') + '</article>' + paragraphs(3) + '</section>'
    yield 'wide-relocation', page(body), wide


def check_fixture(args, directory, name, source, edits):
    """Writes one generated case and requires incremental/full identity for every edit."""
    html = directory / (name + '.html')
    html.write_text(source)
    nodes = directory / (name + '.nodes')
    nodes.write_text(subprocess.check_output([args.driver, 'nodes', '0', str(html), 'renderer/style/ua.css'], text=True))
    script = directory / (name + '.edits')
    script.write_text('\n'.join(edits(Tree(nodes))) + '\n')
    raw = subprocess.check_output([args.driver, 'edit', str(script), str(html), 'renderer/style/ua.css'], text=True)
    (directory / (name + '.raw')).write_text(raw)
    different = re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc DIFF$', raw, re.M)
    refused = re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc refused$', raw, re.M)
    operations = inctime.script_operations(str(script))
    print(name, 'edits', len(operations), 'differences', different, 'refused', refused, flush=True)
    inctime.read(str(directory / (name + '.raw')), operations, checking=True)


def run(args):
    directory = Path(args.output)
    directory.mkdir(parents=True, exist_ok=True)
    selected = 0
    failures = []
    for name, source, edits in fixtures():
        if args.case and name not in args.case:
            continue
        selected += 1
        try:
            check_fixture(args, directory, name, source, edits)
        except (ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as failure:
            print('FAILED:', name, repr(failure), flush=True)
            failures.append(name)
    if not selected:
        raise ValueError('no range cases selected')
    if failures:
        raise SystemExit('failed range fixtures: ' + ' '.join(failures))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('output')
    parser.add_argument('--case', action='append')
    run(parser.parse_args())
