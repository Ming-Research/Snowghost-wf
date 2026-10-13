"""Generate retained-layout edits for length-math-cases.html.

The layout investigation's run.sh invokes this with an already built driver.
Reuse X5's nodes parser because the driver has no native edit-script generator.
Each prefix is checked byte for byte against a fresh build by the driver and
the existing inctime.py checker; no new comparison format is introduced.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/investigations/incremental-layout/scripts'))
from edits import Tree


class FixtureElements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names = []
        self.ids = {}

    def handle_starttag(self, name, attributes):
        index = len(self.names)
        self.names.append(name)
        element_id = dict(attributes).get('id')
        if element_id is not None:
            if element_id in self.ids:
                raise ValueError('duplicate fixture id: ' + element_id)
            self.ids[element_id] = index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    fixture = ROOT / 'tests/layout/length-math-cases.html'
    nodes = args.output.with_suffix('.nodes')
    with nodes.open('w') as output:
        subprocess.run([args.driver, 'nodes', '0', str(fixture),
                        'renderer/style/ua.css'], stdout=output, check=True)
    tree = Tree(nodes)
    html = FixtureElements()
    html.feed(fixture.read_text())
    elements = sorted(tree.elements, key=lambda element: element['index'])
    if [element['name'] for element in elements] != html.names:
        raise ValueError('fixture element order differs from driver nodes')
    by_id = {name: elements[index]['node'] for name, index in html.ids.items()}
    root_node = elements[0]['node']
    lines = [
        'S .math-wide{width:2000px!important} .math-small{width:300px!important}'
        ' .math-medium{width:800px!important} .math-large{width:1400px!important}'
        ' .math-auto{height:auto!important} .math-tall{height:120px!important}'
        ' .math-root-large{font-size:80px!important}'
        ' .math-root-small{font-size:8px!important}'
        ' .math-expression{width:calc(max(3px, min(20px, 10%)) + 4px)!important}'
    ]

    def roundtrip(node, token):
        lines.extend(('C %d %s' % (node, token), 'K %d %s' % (node, token)))

    # Basis changes select a different expression arm without reparsing children.
    for name, token in (('grid-narrow', 'math-wide'),
                        ('clamp-small', 'math-large'),
                        ('clamp-medium', 'math-small'),
                        ('clamp-large', 'math-medium'),
                        ('height-definite', 'math-auto'),
                        ('height-indefinite', 'math-tall'),
                        ('cancel-definite', 'math-auto'),
                        ('cancel-indefinite', 'math-tall'),
                        ('affine-cancel-definite', 'math-auto'),
                        ('affine-cancel-indefinite', 'math-tall'),
                        ('calc-min', 'math-wide'),
                        ('nested', 'math-small')):
        roundtrip(by_id[name], token)
    # All font/viewport arms remain dependencies even when currently unselected.
    for viewport in (1280, 200, 4000, 1280):
        lines.append('V %d 720' % viewport)
        roundtrip(root_node, 'math-root-large')
        roundtrip(root_node, 'math-root-small')
    # Different expressions must change interned style groups by content.
    roundtrip(by_id['min-three'], 'math-expression')
    roundtrip(by_id['max-three'], 'math-expression')
    # Request every prefix dump so the existing checker verifies retained output.
    count = sum(line.startswith(('C ', 'K ')) for line in lines)
    prefixes = ['P %d' % index for index in range(count + 1)]
    args.output.write_text('\n'.join(prefixes + lines) + '\n')
    print('%s: %d restyles and four viewport refreshes' % (args.output, count))


if __name__ == '__main__':
    main()
