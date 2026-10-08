"""Exercise retained run splitting/joining and empty-role lifetimes in hosted CI.

Usage: fragment-topology.py DRIVER OUTPUT_DIR [--detect-omission]
Generated pages leave established fixtures unchanged. Each text operation must
match a fresh full layout. Omission mode requires a semantic difference and
still validates every driver record; an unmutated driver is a negative control.
The native driver supplies node identities, parsed by the established Tree.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

import inctime
from edits import Tree

PAGE = """<!doctype html><style>
html,body{margin:0;padding:0}body{font:16px/20px monospace}
section{display:flow-root;width:180px}div{margin:0}span{background:#def}
.head{HEAD}.offset{OFFSET}p{margin:0}
</style><section><p>Before.</p><span>\t <div class="head">First head.</div> \t <div class="head offset">Second head.</div> \t\t</span><p>After.</p><span>\t\t</span><p>Last.</p></section>
"""


def run(driver, directory, detect):
    directory.mkdir(parents=True, exist_ok=True)
    differences = []
    for head, rule in [('open', ''), ('child', 'display:flow-root'),
                       ('nested-open', ''), ('nested-child', 'display:flow-root')]:
        for offset, displacement in [('plain', ''), ('negative', 'margin-top:-20px'),
                                     ('coincident', 'position:relative;top:-20px')]:
            name = head + '-' + offset
            page = directory / (name + '.html')
            source = PAGE.replace('HEAD', rule).replace('OFFSET', displacement)
            if head.startswith('nested-'):
                source = source.replace('<span>\t ', '<span><em>\t ')
                source = source.replace(' \t\t</span><p>After.', ' \t\t</em></span><p>After.')
            page.write_text(source)
            nodes = directory / (name + '.nodes')
            nodes.write_text(subprocess.check_output(
                [driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], text=True))
            tree = Tree(nodes)
            selected = []
            for marker in (b'\t ', b' \t ', b' \t\t', b'\t\t'):
                found = [text['node'] for text in tree.texts if text['data'] == marker]
                if len(found) != 1:
                    raise ValueError((name, marker, found))
                selected.append(found[0])
            edits = []
            # Each transition changes a different negative or empty dependency.
            for node in selected:
                edits.extend((f'T {node} 0 Visible ', f'D {node} 0 8'))
            # Retain several replacements at once, then consume them in another order.
            for node in selected:
                edits.append(f'T {node} 0 Visible ')
            for node in reversed(selected):
                edits.append(f'D {node} 0 8')
            script = directory / (name + '.edits')
            script.write_text('\n'.join(edits) + '\n')
            rawfile = directory / (name + '.raw')
            started = time.monotonic()
            raw = subprocess.check_output(
                [driver, 'edit', str(script), str(page), 'renderer/style/ua.css'], text=True)
            rawfile.write_text(raw)
            operations = inctime.script_operations(str(script))
            different = re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc DIFF$', raw, re.M)
            protocol = directory / (name + '.protocol')
            protocol.write_text(raw.replace(' inc DIFF\n', ' inc same\n') if detect else raw)
            inctime.read(str(protocol), operations, checking=True)
            if different:
                differences.append((name, different))
            print(name, 'edits', len(operations), 'differences', different,
                  'wall seconds', round(time.monotonic() - started, 3), flush=True)
    if detect and not differences:
        raise ValueError('topology omission produced no rebuild difference')
    if detect:
        print('detected topology omission:', differences)


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != '--detect-omission'):
        raise SystemExit(__doc__)
    run(sys.argv[1], Path(sys.argv[2]), len(sys.argv) == 4)
