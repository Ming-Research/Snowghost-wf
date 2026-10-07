"""Run the origin/travel fixture through the ordinary oracle driver in CI.

Usage: near-limit.py DRIVER OUTPUT_DIR [--unsafe]
The unsafe mode requires an actual incremental/rebuild difference, not merely
an altered path, and is used only by falsify-m2's unsafe-admission mutation.
Generated HTML, node IDs, edit scripts and raw logs stay under OUTPUT_DIR.
"""
import re
import subprocess
import sys
from pathlib import Path

import inctime
from edits import Tree

HERE = Path(__file__).resolve().parent


def require_paths(raw, local):
    paths = [tuple(map(int, match)) for match in
             re.findall(r'^structure path (\d+) splice ([01]) reason (\d+)$', raw, re.M)]
    expected = [(1, 1, 0), (2, 1, 0)] if local else [(1, 0, 7), (2, 0, 7)]
    if paths != expected:
        raise AssertionError(f'expected paths {expected}, got {paths}')


def require_refusal(raw):
    rows = [inctime.TIMED.fullmatch(line) for line in raw.splitlines()]
    text = [row for row in rows if row and int(row.group(1)) in (3, 4)]
    if len(text) != 2 or any(row.group(11) is None or int(row.group(11)) == 0 for row in text):
        raise AssertionError('near-limit text edits must have counted boundary fallbacks')


def check_machinery(raw, timed, local):
    require_paths(raw, local)
    for wrong in (re.sub(r'^structure path 1 .*\n', '', raw, flags=re.M),
                  raw.replace('splice 1 reason 0', 'splice 0 reason 7') if local else
                  raw.replace('splice 0 reason 7', 'splice 1 reason 0'),
                  raw.replace('reason 7', 'reason 6') if not local else
                  raw.replace('reason 0', 'reason 7')):
        try:
            require_paths(wrong, local)
        except AssertionError:
            pass
        else:
            raise AssertionError('path assertion accepted a deliberate fault')
    if not local:
        require_refusal(timed)
        for wrong in (re.sub(r'boundary_fallbacks \d+', 'boundary_fallbacks 0', timed),
                      re.sub(r'^edit [34] us .*\n', '', timed, flags=re.M)):
            try:
                require_refusal(wrong)
            except AssertionError:
                pass
            else:
                raise AssertionError('fallback assertion accepted a deliberate fault')
    print('detected missing, wrong-mode and wrong-reason paths' +
          (', zero and missing text fallback counts' if not local else ''))


def run(driver, directory, unsafe):
    directory.mkdir(parents=True, exist_ok=True)
    template = (HERE / 'near-limit-case.html').read_text()
    cases = {
        'admitted': template.replace('33554000px', '12000000px').replace('-33552000px', '-1000000px'),
        'signed': template,
        'baseline': template.replace('overflow: hidden; height: 33554000px', 'overflow: visible; height: 16px')
            .replace('<div class="tower"></div>', '<div class="tower"><div style="display:flow-root;overflow:hidden;height:33553000px"></div><p>High baseline.</p></div>')
            .replace('<p class="return">Return text.</p>', ''),
        'origin': template.replace('display: flow-root; }', 'display: flow-root; padding-top: 33553000px; }', 1)
            .replace('<div class="tower"></div>', '<div class="tower" style="height:16px"></div>')
            .replace('margin-top: -33552000px', 'margin-top: 0px'),
    }
    differences = []
    for name, html in cases.items():
        page = directory / f'{name}.html'
        page.write_text(html)
        nodes = directory / f'{name}.nodes'
        nodes.write_text(subprocess.check_output([driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], text=True))
        tree = Tree(nodes)
        parent = next(e['node'] for e in tree.elements if e['name'] == 'section')
        tower = next(e['node'] for e in tree.elements if e['name'] == 'div' and e['parent'] == parent)
        text = next(t['node'] for t in tree.texts if t['data'] in (b'Return text.', b'High baseline.'))
        prefix = 'Additional words to make this paragraph wrap onto several more lines. '
        script = directory / f'{name}.edits'
        script.write_text(f'B {parent} {tower} Inserted block.\nX {tree.arena}\nT {text} 0 {prefix}\nD {text} 0 {len(prefix)}\n')
        rawfile = directory / f'{name}.raw'
        raw = subprocess.check_output([driver, 'edit', str(script), str(page), 'renderer/style/ua.css'], text=True)
        rawfile.write_text(raw)
        for line in raw.splitlines():
            if line.startswith('structure path') or ' inc ' in line:
                print(name, line)
        if unsafe:
            if ' inc DIFF\n' in raw:
                differences.append(name)
            continue
        operations = inctime.script_operations(script)
        inctime.read(rawfile, operations, checking=True, require_paths=True)
        timedfile = directory / f'{name}.timed'
        timed = subprocess.check_output([driver, 'incremental', str(script), str(page), 'renderer/style/ua.css'], text=True)
        timedfile.write_text(timed)
        inctime.read(timedfile, operations, require_paths=True)
        check_machinery(raw, timed, name == 'admitted')
        print(name, 'all 4 edits inc same; paths and counted refusals verified')
    if unsafe:
        if not differences:
            raise AssertionError('unsafe arithmetic admission produced no rebuild difference')
        print('detected unsafe arithmetic admission by rebuild differences:', ', '.join(differences))


if __name__ == '__main__':
    run(sys.argv[1], Path(sys.argv[2]), '--unsafe' in sys.argv[3:])
