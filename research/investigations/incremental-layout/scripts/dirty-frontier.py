"""Generate retained-input/frontier discriminators and compare every edit to full layout.

Usage: dirty-frontier.py DRIVER OUTPUT_DIR [--case NAME]
The hosted workflow supplies the compiled driver. Node identities come from its
nodes mode, and inctime validates the existing edit protocol without extensions.
The workflow reuses its semantic mutation checker and unmutated negative control.
Generated pages are isolated from the established case fixtures. The sparse case additionally requires the
three dirty paragraphs to be prepared/broken without a whole-context event walk.
Legacy-driver runs exercise marking with already validated stable style tables;
they do not test old/new construction-compatibility rejection.
"""
import argparse
import re
import subprocess
from pathlib import Path

import inctime
from edits import Tree

BASE = ('html,body{margin:0;padding:0}html{font-size:16px}'
        'body{font:32px/40px monospace}section{display:flow-root;width:600px}'
        'p{margin:0;font:32px/40px monospace}.leaf{font-size:1rem}')


def page(body, css=''):
    return '<!doctype html><html><head><style>' + BASE + css + '</style></head><body>' + body + '</body></html>'


def root_pairs(tree):
    root = tree.elements[0]['node']
    return [f'C {root} small', f'K {root} small', f'C {root} large', f'K {root} large']


def first(tree, tag):
    return next(e['node'] for e in tree.elements if e['name'] == tag)


def text(tree, marker):
    found = [t for t in tree.texts if t['data'] == marker.encode()]
    if len(found) != 1:
        raise ValueError((marker, found))
    return found[0]


def toggle(tree, tag='section'):
    node = first(tree, tag)
    return [f'C {node} changed', f'K {node} changed']


def fixtures():
    paragraphs = ''.join('<p><span class="leaf">Sparse %02d.</span></p>' % i
                         if i in (0, 32, 64) else '<p>Fixed %02d.</p>' % i
                         for i in range(65))
    yield 'sparse-root', page('<section>' + paragraphs + '</section>',
                              '.small{font-size:12px}.large{font-size:24px}'), root_pairs
    simple = '<section><p><span class="leaf">First.</span></p><p class="middle">Middle.</p><p><span class="leaf">Last.</span></p></section>'
    for name, rule in [('frame-width', 'width:90px'),
                       ('frame-left', 'padding-left:29px'),
                       ('frame-top', 'padding-top:31px'),
                       ('frame-definite', 'height:170px'),
                       ('frame-flow-width', 'padding-right:480px'),
                       ('own-minimum', 'min-height:230px'),
                       ('own-overflow', 'overflow:hidden'),
                       ('inactive-columns', 'column-gap:37px')]:
        css = '.changed{' + rule + '}.changed .leaf{font-size:24px}'
        if name == 'frame-definite':
            css += '.middle{height:50%}'
        if name == 'frame-flow-width':
            css += 'section{box-sizing:border-box}.middle{background:#def}'
        yield name, page(simple, css), toggle
    yield 'interior-block', page(simple, '.changed .middle{padding-top:27px;padding-left:25px}.changed .leaf{font-size:24px}'), toggle
    multiline = '<section><p><span class="leaf">First baseline.</span><br>Fixed final baseline.</p><p><span class="leaf">Second first.</span><br>Second final.</p></section>'
    yield 'stationary-first-line', page(multiline, 'p{font-size:16px}.changed .leaf{font-size:24px}'), toggle
    baseline = '<article><section>Hg</section><aside>Hg</aside></article>'
    baseline_css = ('article{display:flex;flex-direction:row;align-items:baseline;width:600px;font:16px/40px sans-serif}'
                    'section,aside{display:flow-root;box-sizing:border-box;flex:0 0 300px;width:300px;min-width:0;margin:0;padding:0;border:0}'
                    'section{overflow:visible}section.changed{overflow:hidden}')
    yield 'overflow-baseline', page(baseline, baseline_css), toggle
    wrap = '<section><p><span class="leaf">Several words cross the narrow measure.</span></p><p><span class="leaf">Other words also cross that measure.</span></p><p>Following reader.</p></section>'
    yield 'changed-placement', page(wrap, 'section{width:180px}.changed .leaf{font-size:32px}'), toggle
    flex = '<article><section><p><span class="leaf">Several words fill a flex item.</span></p><p><span class="leaf">A later line shares its width.</span></p></section><aside>Peer.</aside></article>'
    css = 'article{display:flex;width:500px}section{flex:1 1 300px;min-width:0;width:auto}aside{flex:1 1 200px}.changed section{flex-basis:100px}.changed .leaf{font-size:24px}'
    yield 'transient-flex-space', page(flex, css), lambda tree: toggle(tree, 'article')
    parent_space = '<article>' + simple + '</article>'
    yield 'parent-space', page(parent_space, 'article{width:600px}section{width:100%}.changed{width:120px}.changed .leaf{font-size:24px}'), lambda tree: toggle(tree, 'article')
    for name, extra in [('float-dependent', '<aside style="float:left;width:80px;height:90px">Float.</aside>'),
                        ('atomic-child', '<span style="display:inline-block;width:30px;height:20px">A</span>')]:
        body = '<section>' + extra + '<p><span class="leaf">First.</span></p><p><span class="leaf">Last.</span></p></section>'
        if name == 'atomic-child':
            body = body.replace('<section>' + extra + '<p>', '<section><p>' + extra)
        yield name, page(body, '.changed .leaf{font-size:24px}'), toggle
    yield 'positioned-containing-box', page(simple.replace('</section>', '<aside style="position:absolute;bottom:0;height:50%;width:20px">Out.</aside></section>'),
        'section{position:relative;border-top:10px solid;padding-top:10px}.changed{border-top-width:0;padding-top:20px;min-height:230px}.changed .leaf{font-size:24px}'), toggle
    def empty_edits(tree):
        node = text(tree, '\t\t')['node']
        return [f'T {node} 0 \\n', f'D {node} 0 1'] + toggle(tree) + [f'T {node} 0 \\n', f'D {node} 0 1']
    yield 'lineless', page('<section><span style="white-space:pre-line">\t\t</span><p><span class="leaf">First.</span></p><p><span class="leaf">Last.</span></p></section>', '.changed .leaf{font-size:24px}'), empty_edits
    def source_edits(tree):
        section = first(tree, 'section')
        marker = text(tree, 'Retained marker.')['parent']
        created = tree.arena
        node = text(tree, 'Retained marker.')['node']
        return [f'B {section} {marker} New source.'] + toggle(tree) + [f'T {node} 0 X', f'D {node} 0 1', f'X {created}'] + toggle(tree)
    yield 'source-splice', page('<section><p><span class="leaf">First.</span></p><p>Retained marker.</p><p><span class="leaf">Last.</span></p></section>', '.changed .leaf{font-size:24px}'), source_edits
    def reconstruct_edits(tree):
        holder = text(tree, 'Removed split.')['parent']
        while tree.by_node[holder]['name'] != 'div':
            holder = tree.by_node[holder]['parent']
        return [f'X {holder}'] + toggle(tree)
    yield 'source-reconstruction', page('<section><div><span>Removed split.<div>Split head.</div>Trailing source.</span></div><p><span class="leaf">First.</span></p><p><span class="leaf">Last.</span></p></section>', '.changed .leaf{font-size:24px}'), reconstruct_edits


def sparse_counts(raw):
    records = re.findall(r'^style edit (\d+) prepared (\d+) contexts (\d+) paragraphs (\d+) held_entries (\d+) entries (\d+)(?: .*)?$', raw, re.M)
    if len(records) != 4:
        raise ValueError('sparse frontier lacks four style-count records')
    for edit, prepared, contexts, paragraphs, held, entries in records:
        if (int(prepared), int(paragraphs), int(held)) != (3, 3, 0) or int(entries) >= 32:
            raise ValueError(('sparse frontier did not consume exactly three leaves without context replay', edit, prepared, contexts, paragraphs, held, entries))
    print('sparse frontier: all four edits prepare/break three leaves, held entries zero, total entries below 32', flush=True)


def run(args):
    directory = Path(args.output)
    directory.mkdir(parents=True, exist_ok=True)
    selected = 0
    for name, source, edits in fixtures():
        if args.case and name not in args.case:
            continue
        selected += 1
        html = directory / (name + '.html')
        html.write_text(source)
        nodes = directory / (name + '.nodes')
        nodes.write_text(subprocess.check_output([args.driver, 'nodes', '0', str(html), 'renderer/style/ua.css'], text=True))
        script = directory / (name + '.edits')
        script.write_text('\n'.join(edits(Tree(nodes))) + '\n')
        raw = subprocess.check_output([args.driver, 'edit', str(script), str(html), 'renderer/style/ua.css'], text=True)
        (directory / (name + '.raw')).write_text(raw)
        different = re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc DIFF$', raw, re.M)
        protocol = directory / (name + '.raw')
        operations = inctime.script_operations(str(script))
        inctime.read(str(protocol), operations, checking=True, require_paths=True)
        if name == 'sparse-root':
            sparse_counts(raw)
        print(name, 'edits', len(operations), 'differences', different, flush=True)
    if not selected:
        raise ValueError('no frontier cases selected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('output')
    parser.add_argument('--case', action='append')
    run(parser.parse_args())
