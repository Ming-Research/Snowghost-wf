"""Needed-record omission controls for fallback-followup.py and falsify-m2."""
import argparse
import importlib.util
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('followup', HERE / 'fallback-followup.py')
followup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(followup)

MUTATIONS = ('omit-fallback-style-routes', 'omit-fallback-text-routes',
             'omit-bulk-retained-heads', 'omit-bulk-retained-units',
             'omit-bulk-retained-contexts', 'omit-bulk-path-copy')


def apply(name):
    path = Path('renderer/layout/structure.wf')
    source = path.read_text()
    replacements = {
        'omit-bulk-retained-heads': ('  set uses^[middle] = StyleUse(head: head);',
                                     '  set uses^[middle] = StyleUse(head: no_index);'),
        'omit-bulk-retained-units': ('  let listing = copy_retained_units(source: &layout^.text_units, paths: &paths, count: nodes);', '  let listing = route_table::<TextUnit>(count: nodes, missing: unreached);'),
        'omit-bulk-retained-contexts': ('  let context_of = copy_retained_contexts(source: &layout^.context_of, paths: &paths, count: nodes);', '  let context_of = route_table::<u32>(count: nodes, missing: no_index);'),
        'omit-bulk-path-copy': ('  copy_route_table::<ContextPath>(source: source, destination: destination);\n', ''),
    }
    if name in replacements:
        needle, fault = replacements[name]
        if source.count(needle) != 1:
            raise ValueError('bulk publication site changed')
        path.write_text(source.replace(needle, fault))
        return
    needle = '  record_skipped(walk: &walk, listing: &listing);'
    if source.count(needle) != 1:
        raise ValueError('fallback publication site changed')
    if name == MUTATIONS[0]:
        fault = '  let forgotten_uses = route_table::<StyleUse>(count: nodes, missing: unused);\n  set uses = move forgotten_uses;'
    else:
        fault = '  let forgotten_text = route_table::<TextUnit>(count: nodes, missing: unreached);\n  set listing = move forgotten_text;'
    source = source.replace(needle, fault + '\n' + needle)
    path.write_text(source)


def bulk_sequence(driver, out, mutation, permit_difference=False):
    out.mkdir(parents=True, exist_ok=True)
    page = out / 'retained.html'
    page.write_text('<!doctype html><html><head><style>\nbody{width:500px;margin:0;font-size:16px;line-height:20px}\nsection{display:flow-root}p{margin:8px 0}\n</style></head><body><section><div>Mixed <span>Inside inline.</span> tail.</div></section><section><div>Other mixed <span>Outside inline.</span> tail.</div><div><p>Outside first.</p><p>Outside last.</p></div></section></body></html>')
    listing = out / 'nodes.txt'
    followup.execute(driver, 'nodes', 0, page, listing)
    tree = followup.edits.Tree(listing)
    def marker(text):
        found = [row for row in tree.texts if row['data'] == text.encode()]
        if len(found) != 1:
            raise ValueError('missing retained-state marker')
        return found[0]
    inside = marker('Inside inline.')
    outside = marker('Outside last.')
    mixed = marker('Outside inline.')
    parent = tree.by_node[inside['parent']]['parent']
    first = f'B {parent} {inside["parent"]} Force inside reconstruction.'
    if mutation == 'omit-bulk-retained-units':
        second = f'T {outside["node"]} 0 A longer outside text change. '
        expected = {1: (0, 3)}
    elif mutation == 'omit-bulk-retained-contexts':
        outer = tree.by_node[mixed['parent']]['parent']
        second = f'B {outer} {mixed["parent"]} Force outside reconstruction.'
        expected = {1: (0, 3), 2: (0, 3)}
    else:
        outer = tree.by_node[outside['parent']]['parent']
        second = f'B {outer} {outside["parent"]} Consume outside routes.'
        expected = {1: (0, 3), 2: (1, 0)}
    script = out / 'retained.edits'
    script.write_text(first + '\n' + second + '\n')
    raw = out / 'retained.raw'
    followup.execute(driver, 'edit', script, page, raw)
    text = raw.read_text()
    statuses = dict((int(n), status) for n, status in re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc (same|DIFF|refused)$', text, re.M))
    if sorted(statuses) != [1, 2] or statuses[1] != 'same' or followup.paths(text).get(1) != (0, 3):
        raise ValueError('bulk mutation failed before its intended later consumer')
    if not permit_difference:
        followup.inctime.read(raw, followup.inctime.script_operations(script), checking=True, require_paths=True)
        followup.require_paths(text, expected)
    return text, statuses


def verify(name, baseline, mutant, out):
    if name.startswith('omit-bulk-'):
        bulk_sequence(baseline, out / 'baseline', name)
        raw, statuses = bulk_sequence(mutant, out / 'mutant', name, permit_difference=True)
        observed = followup.paths(raw)
        if name == 'omit-bulk-retained-heads':
            detected = statuses[2] == 'same' and observed.get(2) == (0, 1)
        elif name == 'omit-bulk-retained-units':
            detected = statuses[2] == 'DIFF'
        elif name == 'omit-bulk-retained-contexts':
            detected = statuses[2] == 'refused' and observed.get(2) == (0, 3)
        else:
            detected = statuses[2] == 'refused' and observed.get(2) == (0, 1)
        if not detected:
            raise ValueError(('bulk omission did not fail through its intended consumer', name, statuses, observed))
        print(name, 'detected by its intended retained-state consumer')
        return
    followup.focused(baseline, out / 'baseline')
    raw, expected = followup.focused(mutant, out / 'mutant', permit_difference=True)
    actual = followup.paths(raw)
    statuses = dict((int(n), s) for n, s in re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc (same|DIFF|refused)$', raw, re.M))
    if name == MUTATIONS[0]:
        if actual.get(2) != (0, 1) or statuses[2] != 'same':
            raise ValueError('missing fallback owner route was not detected by the next splice')
    else:
        # text_changed treats an absent route as a node with no paragraph
        # consumer. Erasing a real route therefore leaves stale geometry;
        # it does not return a topology refusal. Require the full comparator
        # to catch that fault after both fallback insertion and removal.
        if any(statuses[i] != 'same' for i in (1, 2, 3, 14, 15, 16)) or any(statuses[i] != 'DIFF' for i in (4, 17)):
            raise ValueError('missing fallback text route did not leave stale geometry on the retained text edits')
        if any(actual.get(i) != expected[i] for i in (1, 2, 3, 14, 15, 16)):
            raise ValueError('text-route omission failed an earlier unrelated path')
    print(name, 'detected by its intended post-fallback consumer')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('apply', 'verify'))
    parser.add_argument('mutation', choices=MUTATIONS)
    parser.add_argument('baseline', nargs='?')
    parser.add_argument('mutant', nargs='?')
    parser.add_argument('output', nargs='?', type=Path)
    args = parser.parse_args()
    if args.action == 'apply':
        apply(args.mutation)
    else:
        verify(args.mutation, args.baseline, args.mutant, args.output)
