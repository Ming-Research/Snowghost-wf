"""Q140 grid fixtures, consumed by the hosted q140-baseline workflow.

The ordinary run requires the proposed splice/refusal paths. --baseline is
only a pre-implementation characterization: it separately requires existing
reason 2 and never supplies evidence of Q140 admission or mutation detection.
Both modes require full-rebuild identity and independent Chromium geometry.
"""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys
import time

from edits import Tree


HERE = Path(__file__).resolve().parent
RETAINED = 'Q140 retained.'
TAIL = 'Q140 tail.'
INSERTED = 'Q140insertedunbreakablecontentthatwidensanintrinsiccolumn.'
FLOW = '<p>' + RETAINED + '</p>{insert}<p>' + TAIL + '</p>'
ITEM = '<section>' + FLOW + '</section>'
PEER = '<aside><p>Short peer.</p></aside>'
LAST = '<footer><p>Following row.</p></footer>'
GRID = '<main>' + ITEM + PEER + LAST + '</main><div>Outer tail.</div>'
WRAPPER = ('<!doctype html><html><head><meta charset="utf-8">'
           '<title>Grid splice</title><style>'
           'body{{margin:8px;font:16px/20px serif}}'
           'p{{margin:0;height:40px}}'
           'main{{display:grid;width:400px;grid-template-columns:200px 200px}}'
           'section,aside,footer,div{{margin:0;padding:0;border:0}}'
           'footer{{grid-column:1 / -1}}{css}'
           '</style></head><body>{body}</body></html>\n')

# css, body, proposed reason. Each negative owns its document so the new
# column-dependency guard cannot be hidden behind another fixture's state.
# Nested baseline-only flex/grid fixtures change direct item membership;
# the inline-block fixture crosses an atomic route. Their geometry is kept,
# while path expectations follow those seams rather than an inside-item seam.
# Required flex-consumer positives stay reason 0; unknown inputs require 11.
CASES = {
    'fixed': ('', GRID, 0),
    'percentage': ('main{width:80%;grid-template-columns:25% 75%}', GRID, 0),
    'fractional-zero-minimum': ('main{grid-template-columns:minmax(0,1fr) minmax(0,2fr)}', GRID, 0),
    'gaps-and-frame': ('main{box-sizing:border-box;border:3px solid;padding:7px;gap:9px;grid-template-columns:minmax(0,1fr) 100px}', GRID, 0),
    'nested': ('main main{width:auto;grid-template-columns:minmax(0,1fr) 60px}main>div{min-width:0}', '<main><div><main>' + ITEM + PEER + LAST + '</main></div>' + PEER + LAST + '</main><div>Outer tail.</div>', 0),
    'stretch-shrink': ('aside p{height:20px}', GRID, 0),
    'baseline': ('main{align-items:baseline}aside{font-size:30px;line-height:35px}', GRID, 0),
    'baseline-auto-margin': ('main{align-items:baseline;grid-template-rows:100px auto}section{margin-top:auto}aside{font-size:30px;line-height:35px}', GRID, 0),
    'flex-percentage-intrinsic': ('.consumer{display:flex;width:500px}main{width:auto;flex:0 1 auto;grid-template-columns:50% 50%}', '<div class="consumer">' + GRID + PEER + '</div>', 11),
    'flex-fixed-intrinsic': ('.consumer{display:flex;width:600px}main{width:auto;flex:0 1 auto}', '<div class="consumer">' + GRID + PEER + '</div>', 0),
    'flex-percentage-explicit-min': ('.consumer{display:flex;width:300px}main{flex:0 1 auto;min-width:0;grid-template-columns:50% 50%}', '<div class="consumer">' + GRID + PEER + '</div>', 0),
    'flex-percentage-auto-min': ('.consumer{display:flex;width:300px}main{flex:0 1 auto;grid-template-columns:50% 50%}', '<div class="consumer">' + GRID + PEER + '</div>', 11),
    'flex-fractional-intrinsic': ('.consumer{display:flex;width:500px}main{width:auto;flex:0 1 auto;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}', '<div class="consumer">' + GRID + PEER + '</div>', 11),
    'flex-nested-fixed': ('.outer{display:flex;align-items:flex-start;width:600px}.consumer{display:flex;width:500px;min-width:0}', '<div class="outer"><div class="consumer">' + GRID + PEER + '</div>' + PEER + '</div>', 0),
    'flex-nested-unproved': ('.outer{display:flex;align-items:flex-start;width:600px}.consumer{display:flex}', '<div class="outer"><div class="consumer">' + GRID + PEER + '</div>' + PEER + '</div>', 11),
    'flex-column-unproved': ('.consumer{display:flex;flex-direction:column;height:250px;flex-wrap:wrap}main{width:auto}', '<div class="consumer">' + GRID + PEER + '</div>', 11),
    'baseline-consumer': ('main{align-items:baseline}.consumer{display:flex;align-items:baseline}.consumer>aside{font:30px/35px serif}.raised{font:30px/35px serif}', '<div class="consumer"><main>' + ITEM.replace('<p>', '<p class="raised">', 1) + PEER + LAST + '</main>' + PEER + '</div><div>Outer tail.</div>', 0),
    'baseline-nested-flow': ('main{align-items:baseline}aside{font-size:30px;line-height:35px}article{display:flow-root}', GRID.replace('<section>', '<section><article>').replace('</section>', '</article></section>'), 0),
    'baseline-nested-flex': ('main{align-items:baseline}aside{font-size:30px;line-height:35px}section{display:flex;flex-direction:column}', GRID, 2),
    'baseline-nested-grid': ('main{align-items:baseline}aside{font-size:30px;line-height:35px}section{display:grid;grid-template-columns:200px}', GRID, 11),
    'baseline-scroller': ('main{align-items:baseline}aside{font-size:30px;line-height:35px}section{overflow:auto}', GRID, 0),
    'baseline-sharing-priority': ('.consumer{display:flex;align-items:baseline}.consumer>aside{font:30px/35px serif}main>aside{align-self:baseline;font:30px/35px serif}section{align-self:start}', '<div class="consumer">' + GRID + PEER + '</div>', 0),
    'baseline-equal-height': ('main{align-items:baseline;height:180px}section{height:120px}aside{font-size:30px;line-height:35px}', GRID, 0),
    'baseline-flex-sharing': ('main{align-items:baseline}section{display:flex}section p{width:70px}section p:first-child{align-self:start}section p:last-child{align-self:baseline;font:30px/35px serif}', GRID, 2),
    'baseline-flex-reverse': ('main{align-items:baseline}section{display:flex;flex-direction:row-reverse}section p{width:70px}section p:last-child{font:30px/35px serif}', GRID, 2),
    'baseline-inline-block-last': ('main{align-items:baseline}.last{display:inline-block}.last p:first-child{font:30px/35px serif}aside{font-size:30px;line-height:35px}', GRID.replace('<section>', '<section><span class="last">').replace('</section>', '</span>last-line</section>'), 2),
    'baseline-row-span': ('main{align-items:baseline}section{grid-row:1 / 3}footer{grid-column:2}aside{font-size:30px;line-height:35px}', GRID, 0),
    'row-span': ('section{grid-row:1 / 3}footer{grid-column:2}aside p{height:20px}', GRID, 0),
    'fixed-container-height': ('main{height:240px;align-content:space-between}', GRID, 0),
    'clamped-container-height': ('main{min-height:100px;max-height:130px}', GRID, 0),
    'column-span-fixed': ('section{grid-column:1 / 3}', GRID, 0),
    'auto-fixed-contribution': ('main{grid-template-columns:auto 100px}section{width:200px}footer{grid-column:2}', GRID, 0),
    'auto-maximum': ('main{grid-template-columns:auto 100px}', GRID, 11),
    'fractional-intrinsic-minimum': ('main{grid-template-columns:1fr 100px}', GRID, 11),
    'column-span-intrinsic': ('main{grid-template-columns:100px auto}section{grid-column:1 / 3}', GRID, 11),
    'auto-placement-moves': ('main{grid-template-columns:200px 200px}', '<main>' + FLOW + '<p>Last item.</p></main><div>Outer tail.</div>', 11),
}


def command(args, output=None):
    if output is None:
        subprocess.run(args, check=True)
    else:
        with output.open('w') as stream:
            subprocess.run(args, stdout=stream, check=True)


def prepare(driver, directory, name):
    directory.mkdir(parents=True, exist_ok=True)
    css, body, reason = CASES[name]
    # Preserve all previously authored baseline style/viewport lifetimes even
    # when their direct-item or atomic seam requires fallback.
    lifetime = reason == 0 or name.startswith('baseline-')
    source = WRAPPER.format(css=css, body=body)
    page = directory / 'case.html'
    page.write_text(source.replace('{insert}', ''))
    (directory / 'inserted.html').write_text(source.replace('{insert}', '<p>' + INSERTED + '</p>'))
    nodes = directory / 'case.nodes'
    command([driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], nodes)
    tree = Tree(nodes)
    tail_text = next(text for text in tree.texts if text['data'] == TAIL.encode())
    retained = next(text for text in tree.texts if text['data'] == RETAINED.encode())
    tail = tree.by_node[tail_text['parent']]
    commands = []
    paths = []
    next_node = tree.arena
    operation = 0

    def append(text, structural=False):
        nonlocal operation
        commands.append(text)
        if not text.startswith('V '):
            operation += 1
        if structural:
            paths.append((operation, int(reason == 0), reason))

    def pair():
        nonlocal next_node
        append('B %d %d %s' % (tail['parent'], tail['node'], INSERTED), True)
        append('X %d' % next_node, True)
        next_node += 2

    pair()
    # Required identity after text/style changes and after original-slot
    # retirement, without adopting rebuilt geometry between edits.
    append('T %d 0 extra ' % retained['node'])
    append('D %d 0 6' % retained['node'])
    pair()
    if lifetime:
        append('C %d q140-large' % retained['parent'])
        pair()
        append('K %d q140-large' % retained['parent'])
        pair()
    if name == 'baseline-inline-block-last':
        # Removing the first paragraph makes the retained tail match
        # .last p:first-child. Later pairs toggle that match, so the existing
        # retained-restyle refusal precedes the atomic-route refusal.
        reason = 6
    append('X %d' % retained['parent'], True)
    append('T %d 0 retained ' % tail_text['node'])
    append('D %d 0 9' % tail_text['node'])
    pair()
    if lifetime:
        for width, height in ((1000, 800), (1280, 720)):
            append('V %d %d' % (width, height))
            pair()
    changed_rule = '.q140-large{font-size:24px;line-height:30px;height:70px}'
    if name == 'baseline-equal-height':
        changed_rule = '.q140-large{font-size:24px;line-height:30px}'
    script = ('S ' + changed_rule + '\n'
              'P 0\nP 1\nP 2\n' + '\n'.join(commands) + '\n')
    (directory / 'case.edits').write_text(script)
    (directory / 'case.edits.paths').write_text(''.join(
        'structure path %d splice %d reason %d\n' % row for row in paths))
    (directory / 'baseline.paths').write_text(''.join(
        'structure path %d splice 0 reason 2\n' % row[0] for row in paths))


def run(driver, directory, name, baseline):
    prepare(driver, directory, name)
    raw = directory / 'edits.raw'
    script = directory / 'case.edits'
    command([driver, 'edit', str(script), str(directory / 'case.html'), 'renderer/style/ua.css'], raw)
    command([sys.executable, str(HERE / 'inctime.py'), '--check', str(script), str(raw)])
    expected = directory / ('baseline.paths' if baseline else 'case.edits.paths')
    spec = importlib.util.spec_from_file_location('percentage_splice', HERE / 'percentage-splice.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    extractor.extract(raw, directory)
    for page in ('case', 'inserted'):
        command(['node', 'tests/layout/layout_oracle.mjs', 'dump', str(directory / (page + '.html'))], directory / (page + '.chromium.tsv'))
    for prefix, page in ((0, 'case'), (1, 'inserted'), (2, 'case')):
        command(['node', 'tests/layout/layout_oracle.mjs', 'compare', str(directory / (page + '.chromium.tsv')), str(directory / ('prefix-%d.tsv' % prefix))])
    command([sys.executable, str(HERE / 'splice-cases.py'), '--check-paths', str(expected), str(raw)])


def final_space(driver, directory, intrinsic=False):
    """Check final constraints and a later direct-context height reader."""
    directory.mkdir(parents=True, exist_ok=True)
    source = Path('tests/layout/grid-final-space-cases.html').read_text()
    if intrinsic:
        source = source.replace('</style>', '.restyle-grid { grid-template-columns: auto 80px; }\n.restyle-grid > article { width: 200px; }\n</style>')
    page = directory / 'case.html'
    page.write_text(source)
    (directory / 'changed.html').write_text(source.replace(
        'class="restyle-context"', 'class="restyle-context half"'))
    nodes = directory / 'case.nodes'
    command([driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], nodes)
    tree = Tree(nodes)
    marker = next(text for text in tree.texts
                  if text['data'] == b'Restyled direct context.')
    child = tree.by_node[marker['parent']]['parent']
    script = directory / 'case.edits'
    script.write_text('P 0\nP 1\nP 2\nC %d half\nK %d half\n' % (child, child))
    raw = directory / 'edits.raw'
    command([driver, 'edit', str(script), str(page), 'renderer/style/ua.css'], raw)
    command([sys.executable, str(HERE / 'inctime.py'), '--check', str(script), str(raw)])
    spec = importlib.util.spec_from_file_location('percentage_splice', HERE / 'percentage-splice.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    extractor.extract(raw, directory)
    for name in ('case', 'changed'):
        command(['node', 'tests/layout/layout_oracle.mjs', 'dump', str(directory / (name + '.html'))], directory / (name + '.chromium.tsv'))
    for prefix, name in ((0, 'case'), (1, 'changed'), (2, 'case')):
        command(['node', 'tests/layout/layout_oracle.mjs', 'compare', str(directory / (name + '.chromium.tsv')), str(directory / ('prefix-%d.tsv' % prefix))])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('directory', type=Path)
    parser.add_argument('--case', choices=CASES, action='append')
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--final-space', action='store_true')
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    if args.final_space:
        final_space(args.driver, args.directory / 'fixed')
        final_space(args.driver, args.directory / 'intrinsic', intrinsic=True)
        return
    failures = []
    summary = []
    for name in args.case or CASES:
        started = time.monotonic()
        try:
            run(args.driver, args.directory / name, name, args.baseline)
        except subprocess.CalledProcessError as error:
            failures.append(name)
            print('FAILED', name, error, flush=True)
        label = 'BASELINE' if args.baseline else 'Q140'
        row = '%s\t%s\t%.3f\t%s' % (label, name, time.monotonic() - started, 'FAIL' if name in failures else 'PASS')
        summary.append(row)
        print(row, flush=True)
    (args.directory / 'summary.tsv').write_text('\n'.join(summary) + '\n')
    if failures:
        raise SystemExit('failed grid fixtures: ' + ', '.join(failures))


if __name__ == '__main__':
    main()
