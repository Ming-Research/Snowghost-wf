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


ROOT = '''<!doctype html><html><head><meta charset="utf-8"><title>Definite percentage splice</title><style>
html,body{height:100%} body{margin:8px;font:16px/20px serif}
p{margin:0;height:300px} section,aside{margin:0;padding:0;border:0}
</style></head><body><section><p>Q139 retained.</p>{insert}<p>Q139 tail.</p></section><aside>Q139 outside.</aside></body></html>
'''


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
    args = parser.parse_args()
    directory = args.directory
    directory.mkdir(parents=True, exist_ok=True)
    if args.extract:
        extract(args.extract, directory)
        return
    page = directory / 'case.html'
    page.write_text(ROOT.replace('{insert}', ''))
    (directory / 'inserted.html').write_text(ROOT.replace('{insert}', '<p>Q139 inserted.</p>'))
    nodes = directory / 'case.nodes'
    with nodes.open('w') as output:
        subprocess.run([args.driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], stdout=output, check=True)
    tree = Tree(nodes)
    tails = [text for text in tree.texts if text['data'] == b'Q139 tail.']
    if len(tails) != 1:
        raise ValueError('fixture must have one tail marker')
    tail = tree.by_node[tails[0]['parent']]
    script = 'P 0\nP 1\nP 2\nB %d %d Q139 inserted.\nX %d\n' % (tail['parent'], tail['node'], tree.arena)
    (directory / 'case.edits').write_text(script)
    (directory / 'case.edits.paths').write_text('structure path 1 splice 1 reason 0\nstructure path 2 splice 1 reason 0\n')
    print('%s: one overflow insertion/removal pair with normal body margins' % directory)


if __name__ == '__main__':
    main()
