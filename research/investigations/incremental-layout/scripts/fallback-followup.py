"""Fallback lifetimes: a rebuilt context must support the next local edit.

Called by the hosted oracles and fallback mutation jobs. Full rebuilds supply
geometry expectations; fixed path expectations distinguish lost routes from
correct rendering obtained through a second reconstruction. No production
path or admission predicate is changed for these fixtures.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


inctime = module('inctime')
edits = module('edits')


def execute(driver, mode, script, page, output, sheets=()):
    command = [str(Path(driver).resolve()), mode, str(script), str(page), 'renderer/style/ua.css', *sheets]
    with output.open('w') as out, output.with_suffix('.stderr').open('w') as err:
        subprocess.run(command, stdout=out, stderr=err, check=True, timeout=180)


def paths(raw):
    found = {}
    for number, splice, reason in re.findall(r'^structure path (\d+) splice ([01]) reason (\d+)$', raw, re.M):
        number = int(number)
        if number in found:
            raise ValueError('duplicate structural path')
        found[number] = (int(splice), int(reason))
    return found


def require_paths(raw, expected):
    actual = paths(raw)
    if actual != expected:
        raise ValueError(f'fallback followup paths: expected {expected}, got {actual}')


def controls():
    good = 'structure path 1 splice 0 reason 3\nstructure path 2 splice 1 reason 0\n'
    expected = {1: (0, 3), 2: (1, 0)}
    require_paths(good, expected)
    for wrong in ('', good.splitlines()[0], good + good, good.replace('splice 1 reason 0', 'splice 0 reason 1')):
        try:
            require_paths(wrong, expected)
        except ValueError:
            pass
        else:
            raise AssertionError('accepted missing, duplicate or changed path')


def focused(driver, out, permit_difference=False):
    out.mkdir(parents=True, exist_ok=True)
    page = out / 'fallback.html'
    page.write_text('''<!doctype html><html><head><style>
body{width:500px;margin:0;font-size:16px;line-height:20px}
section{display:flow-root}p{margin:8px 0}.probe{font-size:27px}
</style></head><body><section><div>Mixed prefix <span>Fallback inline reader.</span> mixed tail.</div><div><p>Fallback stable first.</p><p>Fallback stable last.</p></div></section><section><div><p>Outside first.</p><p>Outside last.</p></div></section></body></html>''')
    listing = out / 'nodes.txt'
    execute(driver, 'nodes', 0, page, listing)
    tree = edits.Tree(listing)
    def marker(value):
        selected = [t for t in tree.texts if t['data'] == value.encode()]
        if len(selected) != 1:
            raise ValueError('missing fixture marker: ' + value)
        return selected[0]
    inline = marker('Fallback inline reader.')
    stable = marker('Fallback stable last.')
    outside = marker('Outside last.')
    inline_parent = tree.by_node[inline['parent']]['parent']
    stable_parent = tree.by_node[stable['parent']]['parent']
    outside_parent = tree.by_node[outside['parent']]['parent']
    new = tree.arena
    lines = [
        f'B {inline_parent} {inline["parent"]} Force the mixed inline seam to rebuild.',
        f'B {stable_parent} {stable["parent"]} The next block must splice in the rebuilt context.',
        f'X {new + 2}',
        f'T {inline["node"]} 0 Changed ', f'D {inline["node"]} 0 8',
        f'C {inline["parent"]} probe', f'K {inline["parent"]} probe',
        f'T {new + 1} 0 New ', f'D {new + 1} 0 4',
        f'C {new} probe', f'K {new} probe',
        f'B {outside_parent} {outside["parent"]} Outside routes also survive.',
        f'X {new + 4}',
        f'X {new}',
        f'B {stable_parent} {stable["parent"]} Splice after fallback removal.',
        f'X {new + 6}',
        f'T {inline["node"]} 0 Again ', f'D {inline["node"]} 0 6',
        f'C {inline["parent"]} probe', f'K {inline["parent"]} probe',
    ]
    script = out / 'followup.edits'
    script.write_text('\n'.join(lines) + '\n')
    raw = out / 'followup.raw'
    execute(driver, 'edit', script, page, raw)
    expected = {1: (0, 3), 2: (1, 0), 3: (1, 0), 12: (1, 0), 13: (1, 0),
                14: (0, 3), 15: (1, 0), 16: (1, 0)}
    # Mutations must leave the first fallback correct and be observed by a
    # later consumer, not by a compiler error or an incomplete/crashed run.
    text = raw.read_text()
    if permit_difference:
        statuses = re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc (same|DIFF|refused)$', text, re.M)
        if [int(n) for n, _ in statuses] != list(range(1, len(lines) + 1)):
            raise ValueError('incomplete mutated sequence')
        if statuses[0][1] != 'same' or paths(text).get(1) != (0, 3):
            raise ValueError('mutation did not reach the next-edit lifetime')
        return text, expected
    inctime.read(raw, inctime.script_operations(script), checking=True, require_paths=True)
    require_paths(text, expected)
    print('focused fallback insertion/removal, fresh/retained text and style, and following splices: pass')
    return text, expected


def apollo(driver, out, baseline_raw):
    """Replay all original edits; put a proved splice after each fallback.

    Insertions allocate two DOM nodes, as the existing X5 generator specifies.
    Remap only generated removal IDs when adding followup insertions. Keep
    original sites, order, page, and CSS unchanged. Select followup sites from
    the frozen before-source paths, never from the candidate being tested.
    """
    out.mkdir(parents=True, exist_ok=True)
    source = Path('build/x5/scripts/apollo11-block.edits')
    original = source.read_text().splitlines()
    baseline = paths(Path(baseline_raw).read_text())
    wanted = Counter({(1, 0): 38, (0, 9): 18, (0, 7): 2, (0, 3): 2})
    if Counter(baseline.values()) != wanted or sorted(baseline) != list(range(1, 61)):
        raise ValueError('frozen before-source fallback inventory differs')
    first_splice = next(i for i in range(1, 61, 2) if baseline[i] == (1, 0))
    followup = original[first_splice - 1]
    if not followup.startswith('B '):
        raise ValueError('followup site is not an original insertion')
    next_node = int(original[1].split()[1])
    remap, lines, expected, mapping = {}, [], {}, []
    for edit, line in enumerate(original, 1):
        if line.startswith('B '):
            old_node = int(original[edit].split()[1])
            remap[old_node] = next_node
            next_node += 2
        elif line.startswith('X '):
            line = f'X {remap[int(line.split()[1])]}'
        else:
            raise ValueError('unexpected original block operation')
        lines.append(line)
        expected[len(lines)] = baseline[edit]
        mapping.append(dict(original=edit, expanded=len(lines), path=baseline[edit]))
        if baseline[edit][0] == 0:
            lines.append(followup)
            expected[len(lines)] = (1, 0)
            lines.append(f'X {next_node}')
            expected[len(lines)] = (1, 0)
            next_node += 2
    script = out / 'apollo-followup.edits'
    script.write_text('\n'.join(lines) + '\n')
    (out / 'mapping.json').write_text(json.dumps(mapping, indent=2) + '\n')
    sheets = ('wikibase.client.init&only=styles&skin=vector-2022=build/research/concurrency/apollo11-modules.css', 'modules=site.styles&only=styles&skin=vector-2022=build/research/concurrency/apollo11-site.css')
    raw = out / 'apollo-followup.raw'
    execute(driver, 'edit', script, 'build/research/concurrency/apollo11.html', raw, sheets)
    inctime.read(raw, inctime.script_operations(script), checking=True, require_paths=True)
    require_paths(raw.read_text(), expected)
    print('Apollo11: all original 60 edits and 44 splice followups match full rebuilds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', nargs='?')
    parser.add_argument('output', nargs='?', type=Path)
    parser.add_argument('--apollo-before')
    parser.add_argument('--self-test', action='store_true')
    options = parser.parse_args()
    if options.self_test:
        controls()
    elif options.apollo_before:
        apollo(options.driver, options.output, options.apollo_before)
    else:
        focused(options.driver, options.output)
