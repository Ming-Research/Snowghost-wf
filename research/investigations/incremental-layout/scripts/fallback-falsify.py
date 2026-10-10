"""Needed-record omission controls for fallback-followup.py and falsify-m2."""
import argparse
import importlib.util
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('followup', HERE / 'fallback-followup.py')
followup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(followup)

MUTATIONS = ('omit-fallback-style-routes', 'omit-fallback-text-routes')


def apply(name):
    path = Path('renderer/layout/structure.wf')
    source = path.read_text()
    needle = '  record_skipped(walk: &walk, listing: &listing);'
    if source.count(needle) != 1:
        raise ValueError('fallback publication site changed')
    if name == MUTATIONS[0]:
        fault = '  let forgotten_uses = route_table::<StyleUse>(count: nodes, missing: unused);\n  set uses = move forgotten_uses;'
    else:
        fault = '  let forgotten_text = route_table::<TextUnit>(count: nodes, missing: unreached);\n  set listing = move forgotten_text;'
    source = source.replace(needle, fault + '\n' + needle)
    path.write_text(source)


def verify(name, baseline, mutant, out):
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
