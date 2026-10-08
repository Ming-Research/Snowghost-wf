"""Generate Q139 fixtures and their required structural paths for hosted CI.

The driver supplies stable DOM identities through edits.Tree. Each complete
edit prefix is checked by inctime.py and the existing splice path checker;
Chromium supplies independent rectangles for the initial and inserted pages.
No renderer is built by this generator.
"""
import argparse
from pathlib import Path
import re
import subprocess

from edits import Tree


BASE = '<p>Q139 retained.</p>{insert}<p>Q139 tail.</p>'
WRAPPER = '<!doctype html><html><head><meta charset="utf-8"><title>Percentage splice</title><style>html,body{{height:100%}} body{{margin:8px;font:16px/20px serif}} p{{margin:0;height:40px}} section,aside,div{{margin:0;padding:0;border:0}} {css}</style></head><body>{body}</body></html>\n'

# Each negative owns a document: an unrelated unresolved reader must not mask
# the selected predicate. The required path is independent of dump equality.
CASES = {
    'root': ('p{height:300px}', '<section>' + BASE + '</section><aside>Outside.</aside>', 0),
    'root-zero-margin': ('body{margin:0} p{height:300px}', '<section>' + BASE + '</section><aside>Outside.</aside>', 0),
    'nested': ('section{height:200px}.half,.quarter{height:50%}', '<section><div class="half"><div class="quarter">' + BASE + '</div><aside>Half tail.</aside></div><aside>Outer tail.</aside></section><aside>Outside.</aside>', 0),
    'framed': ('section{height:200px;width:300px}.half{height:50%;box-sizing:border-box;border:3px solid;padding:5px}.quarter{height:50%}', '<section><div class="half"><div class="quarter">' + BASE + '</div></div></section><aside>Outside.</aside>', 0),
    'rounding': ('section{height:101px}.half{height:33.33%}.quarter{height:20000%}', '<section><div class="half"><div class="quarter">' + BASE + '</div></div></section><aside>Outside.</aside>', 0),
    'fixed-limits': ('section{height:200px}.half{height:80%;min-height:25%;max-height:50%}', '<section><div class="half">' + BASE + '</div><aside>Outer tail.</aside></section><aside>Outside.</aside>', 0),
    'sibling-limits': ('section{height:200px}.minimum{min-height:50%}.maximum{max-height:25%}.maximum p{height:100px}', '<section><div>' + BASE + '</div><aside class="minimum">Minimum.</aside><aside class="maximum"><p>Maximum.</p></aside></section>', 0),
    'inactive-maximum-margin': ('section{height:200px}.maximum{max-height:1000px}.maximum p{height:20px;margin:0 0 30px}', '<section><div>' + BASE + '</div><div class="maximum"><p>Margin.</p></div><aside>Outside.</aside></section>', 0),
    'sibling-width-percent': ('section{height:200px;width:300px}.sibling{height:50%;padding:3% 2%;margin:4% 1%;box-sizing:border-box}', '<section><div>' + BASE + '</div><aside class="sibling">Width based.</aside></section>', 0),
    'private-reader': ('section{height:200px}p{height:50%}', '<section>' + BASE + '</section><aside>Outside.</aside>', 0),
    'private-chain': ('section{height:200px}p{height:50%}p::before{display:block;height:50%;content:"New child."}p.old{height:40px}p.old::before{content:none}', '<section>' + BASE.replace('<p>', '<p class="old">') + '</section><aside>Outside.</aside>', 0),
    'partial-restyle': ('html,body{height:auto}section{height:200px}.holder{height:100px}', '<section><div class="holder">' + BASE + '</div></section><aside>Outside.</aside>', 0),
    'equal-state': ('section{height:200px}.holder{height:50%}p{height:50px}.remainder{height:100px}', '<section><div class="holder">' + BASE + '</div><aside class="remainder">Remainder.</aside></section><aside>Outside.</aside>', 0),
    'quirks': ('', '<section>' + BASE + '</section><aside>Outside.</aside>', 7),
    'layout-stretch': ('.flex{display:flex;align-items:stretch}.flex>section,.flex>aside{width:300px}.reader{height:50%}', '<div class="flex"><section>' + BASE + '</section><aside><div class="reader">Stretch.</div></aside></div>', 7),
    'auto-owner': ('section{height:50%}', '<div><section>' + BASE + '</section></div>', 7),
    'auto-earlier-reader': ('.reader{height:50%}', '<div><aside class="reader">Earlier.</aside><section>' + BASE + '</section></div>', 7),
    'auto-later-reader': ('.reader{height:50%}', '<div><section>' + BASE + '</section><aside class="reader">Later.</aside></div>', 7),
    'auto-minimum': ('.reader{min-height:50%}', '<div><section>' + BASE + '</section><aside class="reader">Minimum.</aside></div>', 7),
    'auto-maximum': ('.reader{max-height:50%}', '<div><section>' + BASE + '</section><aside class="reader">Maximum.</aside></div>', 7),
    'nested-context-reader': ('.nested{display:flow-root}.reader{height:50%}', '<div><section>' + BASE + '</section><aside class="nested"><div class="reader">Nested.</div></aside></div>', 7),
    'float-reader': ('.reader{float:left;height:50%;width:30px}', '<div><section>' + BASE + '</section><aside class="reader">Float.</aside></div>', 7),
    'auto-intermediate': ('.outer{height:200px}section{height:50%}', '<div class="outer"><div><section>' + BASE + '</section></div></div>', 7),
    'cross-minimum': ('.outer{height:200px}section{min-height:50%}', '<div class="outer"><section>' + BASE + '</section><aside>Outside.</aside></div>', 7),
    'cross-maximum': ('.outer{height:200px}section{max-height:50%}', '<div class="outer"><section>' + BASE + '</section><aside>Outside.</aside></div>', 7),
    'new-indefinite-reader': ('p{height:50%}p.old{height:40px}', '<section>' + BASE.replace('<p>', '<p class="old">') + '</section>', 7),
}


def extract(raw, directory):
    """Keep requested fresh-prefix dumps for the independent browser comparator."""
    current = None
    rows = {}
    for line in raw.read_text().splitlines():
        if line.startswith('base hash '):
            current = 0
        match = re.fullmatch(r'edit (\d+) hash [0-9a-f]{16} bytes \d+ inc same', line)
        if match:
            current = int(match[1])
        if line == 'inc dump':
            raise ValueError('incremental difference is not reference evidence')
        if line.startswith(('E\t', 'T\t', 'H\t')):
            if current is None:
                raise ValueError('dump before its identity row')
            rows.setdefault(current, []).append(line)
    if set(rows) != {0, 1, 2}:
        raise ValueError('expected every requested prefix dump, got %r' % sorted(rows))
    for number, lines in rows.items():
        (directory / ('prefix-%d.tsv' % number)).write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('directory', type=Path)
    parser.add_argument('--extract', type=Path)
    parser.add_argument('--case', choices=CASES, default='root')
    parser.add_argument('--lifetime', action='store_true')
    args = parser.parse_args()
    directory = args.directory
    directory.mkdir(parents=True, exist_ok=True)
    if args.extract:
        extract(args.extract, directory)
        return
    page = directory / 'case.html'
    css, body, reason = CASES[args.case]
    source = WRAPPER.format(css=css, body=body)
    if args.case == 'quirks':
        source = source.replace('<!doctype html>', '')
    page.write_text(source.replace('{insert}', ''))
    (directory / 'inserted.html').write_text(source.replace('{insert}', '<p>Q139 inserted.</p>'))
    nodes = directory / 'case.nodes'
    with nodes.open('w') as output:
        subprocess.run([args.driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], stdout=output, check=True)
    tree = Tree(nodes)
    tails = [text for text in tree.texts if text['data'] == b'Q139 tail.']
    if len(tails) != 1:
        raise ValueError('fixture must have one tail marker')
    tail = tree.by_node[tails[0]['parent']]
    script = 'P 0\nP 1\nP 2\nB %d %d Q139 inserted.\nX %d\n' % (tail['parent'], tail['node'], tree.arena)
    paths = [(1, int(reason == 0), reason), (2, int(reason == 0), reason)]
    if args.lifetime:
        retained = next(text for text in tree.texts if text['data'] == b'Q139 retained.')
        owner = tree.by_node[tail['parent']]
        basis = tree.by_node[owner['parent']] if args.case in ('partial-restyle', 'equal-state') else owner
        next_node = tree.arena + 2
        commands = [line for line in script.splitlines() if line.startswith(('B ', 'X '))]
        def block_pair(expected_reason):
            nonlocal next_node
            commands.append('B %d %d Q139 inserted.' % (tail['parent'], tail['node']))
            paths.append((len(commands), int(expected_reason == 0), expected_reason))
            # Exercise the new record and route before retirement; text is not
            # restored by a full layout between these commands.
            commands.extend(('T %d 0 fresh ' % (next_node + 1),
                             'D %d 0 6' % (next_node + 1),
                             'T %d 0 retained ' % retained['node'],
                             'D %d 0 9' % retained['node']))
            commands.append('X %d' % next_node)
            paths.append((len(commands), int(expected_reason == 0), expected_reason))
            next_node += 2
        block_pair(reason)
        # An explicit source change followed by another structural edit must
        # see renewed metadata. This targets the percentage-free partial
        # restyle path as well as the percentage-dependent full pre-pass.
        for token in ('basis-tall', 'basis-width'):
            commands.append('C %d %s' % (basis['node'], token))
            block_pair(reason)
            commands.append('K %d %s' % (basis['node'], token))
            block_pair(reason)
        if args.case == 'equal-state':
            commands.append('C %d basis-auto' % basis['node'])
            block_pair(7)
            commands.append('K %d basis-auto' % basis['node'])
            block_pair(0)
        sheet = 'S .basis-tall{height:300px!important}.basis-width{width:300px!important}.basis-auto{height:auto!important}\n'
        script = sheet + 'P 0\nP 1\nP 2\n' + '\n'.join(commands) + '\n'
    (directory / 'case.edits').write_text(script)
    (directory / 'case.edits.paths').write_text(''.join('structure path %d splice %d reason %d\n' % row for row in paths))
    print('%s: %s insertion/removal, required reason %d' % (directory, args.case, reason))


if __name__ == '__main__':
    main()
