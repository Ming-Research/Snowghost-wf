"""Generate percentage-basis restyles from the existing full-layout oracle fixture.

The hosted q139 workflow supplies a compiled driver and checks each prefix with
inctime.py. Chromium owns the fixture's initial rectangle expectations; these
edits separately test refresh after height, definiteness and width changes.
The generator reuses edits.Tree because the node protocol has no native parser.
"""
import argparse
from pathlib import Path
import subprocess

from edits import Tree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    fixture = 'tests/layout/percentage-height-cases.html'
    nodes = args.output.with_suffix('.nodes')
    with nodes.open('w') as output:
        subprocess.run([args.driver, 'nodes', '0', fixture,
                        'renderer/style/ua.css'], stdout=output, check=True)
    tree = Tree(nodes)
    by_index = {element['index']: element for element in tree.elements}
    lines = ['S .basis-tall{height:300px!important} .basis-auto{height:auto!important} .basis-frame{width:300px!important;padding-top:10%;box-sizing:border-box} .basis-atomic{display:inline-block} .basis-float{float:left}']
    for mode in ('', 'basis-atomic', 'basis-float'):
        child = by_index[7]
        assert child['name'] == 'div', child
        if mode:
            lines.append('C %d %s' % (child['node'], mode))
        for index in (6, 7, 9, 10, 13, 15, 16):
            element = by_index[index]
            assert element['name'] == 'div', element
            for token in ('basis-tall', 'basis-auto', 'basis-frame'):
                lines.extend(('C %d %s' % (element['node'], token),
                              'K %d %s' % (element['node'], token)))
        if mode:
            lines.append('K %d %s' % (child['node'], mode))
    args.output.write_text('\n'.join(lines) + '\n')
    print('%s: %d restyles' % (args.output, len(lines) - 1))


if __name__ == '__main__':
    main()
