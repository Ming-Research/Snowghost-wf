"""Increment-1 source lifetime fixture, called only by fallback-source CI.

The existing oracle compares the complete serialized layout against a fresh
full layout after every edit. This fixture adds source-work observations and
later consumers of each retained route; it never selects a renderer path.
Python reuses the established node-listing and output protocol parsers because
there is no native renderer command for locating textual fixture markers.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time

SCRIPTS = Path(__file__).resolve().parents[1] / 'incremental-layout' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from edits import Tree
import inctime


PAGE = '''<!doctype html><html><head><style>
body{width:640px;margin:0;font:16px/20px serif}p{margin:0}
section{display:flow-root;width:400px;height:500px;padding:4px;border:1px solid}
.stable,.retained,.branch{display:flow-root}.float{float:left;width:60px;height:100px}
.spacer{padding-top:200px}.probe{clear:left;margin-top:-190px}
.inside{display:block;position:relative}.changed{position:relative;top:13px}
.owner>div{display:flow-root}.fresh{position:relative;left:9px}
</style></head><body><section><div class="stable"><p>Stable earlier paragraph.</p></div>
<div class="float"></div><div class="spacer"></div><div class="owner">
<p>First edited owner line.</p><p class="retained"><span class="inside">Retained sibling interior.</span></p>
<div class="branch"><p><span class="inside">Retained branch interior.</span></p></div>
</div><div class="probe"><p>Later float consumer.</p></div></section>
<div class="stable"><p>Outside stable paragraph.</p></div></body></html>'''

CASES = ('plain', 'closure-sibling', 'closure-branch', 'publication',
         'routes-text', 'routes-style', 'routes-context')
SELECTORS = {
    'closure-sibling': '.retained{float:left;width:auto}.retained .inside{width:40px}.owner>p:nth-child(3) .inside{width:120px}',
    'closure-branch': '.branch{float:left;width:auto}.branch .inside{width:40px}.owner>p:nth-child(3)~.branch .inside{width:120px}',
    'publication': '.owner{height:100px}.owner>p:nth-child(3) .inside{top:17px}.owner>p:nth-child(3)~.branch .inside{top:19px}',
}


def execute(driver, mode, script, page, raw):
    with raw.open('w') as out, raw.with_suffix('.stderr').open('w') as err:
        completed = subprocess.run([str(Path(driver).resolve()), mode, str(script), str(page),
                                    'renderer/style/ua.css'], stdout=out, stderr=err, timeout=180)
    if completed.returncode:
        raise ValueError(f'oracle failed ({completed.returncode}): {raw.with_suffix(".stderr")}')
    if raw.with_suffix('.stderr').read_text():
        raise ValueError('unexpected oracle stderr: ' + str(raw))


def marker(tree, value):
    matches = [row for row in tree.texts if row['data'] == value.encode()]
    if len(matches) != 1:
        raise ValueError('expected one fixture marker: ' + value)
    return matches[0]


def prepare(driver, out, case):
    out.mkdir(parents=True, exist_ok=True)
    page = out / 'retained.html'
    page.write_text(PAGE)
    listing = out / 'nodes.txt'
    execute(driver, 'nodes', 0, page, listing)
    tree = Tree(listing)
    sibling = marker(tree, 'Retained sibling interior.')
    paragraph = tree.by_node[sibling['parent']]['parent']
    owner = tree.by_node[paragraph]['parent']
    branch = marker(tree, 'Retained branch interior.')
    stable = marker(tree, 'Stable earlier paragraph.')
    outside = marker(tree, 'Outside stable paragraph.')
    created = tree.arena
    nested = case == 'routes-context'
    fresh_paragraph = created + 1 if nested else created
    fresh_text = fresh_paragraph + 1
    lines = []
    if case in SELECTORS:
        lines.append('S ' + SELECTORS[case])
    lines.append(f'{"J" if nested else "B"} {owner} {paragraph} ' +
                 ('1 ' if nested else '') + 'Inserted complete source block.')
    text = 'A longer route consumer changes this paragraph and its line breaking. ' * 4
    lines.extend((f'T {fresh_text} 0 {text}', f'D {fresh_text} 0 {len(text)}',
                  f'C {fresh_paragraph} fresh', f'K {fresh_paragraph} fresh',
                  f'T {stable["node"]} 0 {text}', f'D {stable["node"]} 0 {len(text)}',
                  f'C {sibling["parent"]} changed', f'K {sibling["parent"]} changed',
                  f'C {branch["parent"]} changed', f'K {branch["parent"]} changed'))
    next_created = created + (3 if nested else 2)
    if nested:
        # Establishing-element routes are consumed by a structural edit inside
        # the freshly retained child context, not merely by its geometry.
        lines.extend((f'B {created} {fresh_paragraph} Second complete source block.',
                      f'X {next_created}'))
    else:
        lines.extend((f'B {owner} {paragraph} Second complete source block.',
                      f'X {next_created}'))
    lines.extend((f'X {created}', f'T {outside["node"]} 0 {text}',
                  f'D {outside["node"]} 0 {len(text)}',
                  f'C {sibling["parent"]} changed', f'K {sibling["parent"]} changed'))
    count = sum(line[:1] in 'TDCKBJX' for line in lines)
    lines.extend(f'P {number}' for number in (0, 1, count))
    script = out / 'retained.edits'
    script.write_text('\n'.join(lines) + '\n')
    metadata = dict(case=case, edits=count, nested=nested, first_contexts=int(nested),
                    restored=count, fixture='motion-above-complete-block')
    (out / 'fixture.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return page, script, metadata


def records(text):
    statuses, paths, counts, hashes = {}, {}, {}, {}
    base = None
    for line in text.splitlines():
        found = re.fullmatch(r'edit (\d+) hash ([0-9a-f]{16}) bytes (\d+) inc (same|DIFF|refused)', line)
        if found:
            number = int(found[1])
            if number in statuses:
                raise ValueError('duplicate edit status')
            statuses[number] = found[4]
            hashes[number] = (found[2], found[3])
        found = re.fullmatch(r'base hash ([0-9a-f]{16}) bytes (\d+)', line)
        if found:
            if base is not None:
                raise ValueError('duplicate base')
            base = (found[1], found[2])
        found = re.fullmatch(r'structure path (\d+) splice ([01]) reason (\d+)', line)
        if found:
            number = int(found[1])
            if number in paths:
                raise ValueError('duplicate structural path')
            paths[number] = (int(found[2]), int(found[3]))
        found = re.fullmatch(r'structure edit (\d+) contexts (\d+) paragraphs (\d+) reused (\d+)', line)
        if found:
            number = int(found[1])
            if number in counts:
                raise ValueError('duplicate construction record')
            counts[number] = (int(found[2]), int(found[3]), int(found[4]))
    if base is None or sorted(statuses) != list(range(1, len(statuses) + 1)):
        raise ValueError('missing base or incomplete edit sequence')
    return statuses, paths, counts, hashes, base


def validate(raw, script, metadata, retained=True):
    inctime.read(raw, inctime.script_operations(script), checking=True, require_paths=True)
    statuses, paths, counts, hashes, base = records(raw.read_text())
    if len(statuses) != metadata['edits']:
        raise ValueError('fixture did not complete every operation')
    if hashes[metadata['restored']] != base:
        raise ValueError('original-plus-inverse did not restore complete output')
    if paths.get(1, (1, 0))[0] != 0:
        raise ValueError('fixture did not refuse the unchanged splice predicate')
    if retained and counts.get(1, ())[:2] != (metadata['first_contexts'], 1):
        raise ValueError('first refusal reconstructed outside the inserted source subtree')
    if retained and counts.get(14, ())[:2] != (0, 0):
        raise ValueError('inverse removal reconstructed retained source')
    return dict(paths=paths, constructed=counts)


def run(driver, out, retained=True):
    summary = {}
    # One forward/inverse pilot precedes the larger lifetime scripts in CI.
    page, script, metadata = prepare(driver, out / 'pilot', 'plain')
    pilot = out / 'pilot' / 'pilot.edits'
    original = script.read_text().splitlines()
    insertion = next(line for line in original if line.startswith('B '))
    removal = next(line for line in original if line.startswith('X ') and line.endswith(str(Tree(out / 'pilot' / 'nodes.txt').arena)))
    pilot.write_text(insertion + '\n' + removal + '\n')
    pilot_raw = out / 'pilot' / 'pilot.raw'
    pilot_started = time.monotonic()
    execute(driver, 'edit', pilot, page, pilot_raw)
    inctime.read(pilot_raw, ['B', 'X'], checking=True, require_paths=True)
    pilot_seconds = time.monotonic() - pilot_started
    print(f'forward/inverse pilot: {pilot_seconds:.3f} s', flush=True)
    if pilot_seconds > 60:
        raise ValueError('pilot exceeds 60 seconds; select the lifetime batch scale from its CI evidence')
    for case in CASES:
        folder = out / case
        page, script, metadata = prepare(driver, folder, case)
        raw = folder / 'retained.raw'
        execute(driver, 'edit', script, page, raw)
        summary[case] = validate(raw, script, metadata, retained=retained)
        work = 'retained source work' if retained else 'reconstruction baseline'
        print(case + ': complete output, ' + work + ' and route lifetime accepted')
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


def compare(first, second):
    for case in CASES:
        old_path, new_path = first / case / 'retained.raw', second / case / 'retained.raw'
        old, new = old_path.read_text(), new_path.read_text()
        old_records, new_records = records(old), records(new)
        if old_records[3:] != new_records[3:]:
            raise ValueError('baseline/candidate full output differs: ' + case)
        # P requests materialize the serialized dump, beyond its hash/length.
        dumps = lambda raw: b''.join(line for line in raw.splitlines(keepends=True) if line.startswith((b'E\t', b'T\t', b'H\t')))
        old_dump, new_dump = dumps(old_path.read_bytes()), dumps(new_path.read_bytes())
        if not old_dump or old_dump != new_dump:
            raise ValueError('baseline/candidate serialized dump differs: ' + case)
        print(case + ': baseline/candidate output byte equal')


def controls(folder):
    raw = folder / 'plain' / 'retained.raw'
    script = folder / 'plain' / 'retained.edits'
    metadata = json.loads((folder / 'plain' / 'fixture.json').read_text())
    validate(raw, script, metadata)
    source = raw.read_text()
    bad_count = re.sub(r'^structure edit 1 contexts \d+ paragraphs \d+ reused \d+$',
                       'structure edit 1 contexts 99 paragraphs 99 reused 0', source, count=1, flags=re.M)
    bad_restore = re.sub(r'^(edit ' + str(metadata['restored']) + r' hash )[0-9a-f]{16}',
                         r'\g<1>ffffffffffffffff', source, count=1, flags=re.M)
    missing = re.sub(r'^structure path 1 .*\n', '', source, count=1, flags=re.M)
    for name, text, intended in (
        ('missing-path', missing, 'partial structural path records'),
        ('unrelated-output', source + 'unknown protocol\n', 'unexpected output'),
        ('outside-reconstruction', bad_count, 'reconstructed outside'),
        ('inverse-output', bad_restore, 'did not restore complete output'),
    ):
        wrong = folder / ('negative-' + name + '.raw')
        wrong.write_text(text)
        try:
            validate(wrong, script, metadata)
        except ValueError as error:
            if intended not in str(error):
                raise ValueError('detector rejected corruption for an unrelated condition') from error
        else:
            raise ValueError('detector accepted corrupted ' + name)
        print('detected corrupted ' + name + ': ' + intended)


def detect(raw, script, metadata, expected_edit, permit_path_change=False, baseline_raw=None):
    text = raw.read_text()
    # Check the entire ordinary output protocol before accepting any difference.
    # Only status values are normalized in this temporary protocol-check copy.
    normalized = raw.with_suffix('.protocol')
    normalized.write_text(re.sub(r' inc (DIFF|refused)$', ' inc same', text, flags=re.M))
    inctime.read(normalized, inctime.script_operations(script), checking=True, require_paths=True)
    statuses, paths, counts, hashes, base = records(text)
    if len(statuses) != metadata['edits'] or counts.get(1, ())[:2] != (metadata['first_contexts'], 1):
        raise ValueError('mutant did not complete the retained source path')
    if paths.get(1, (1, 0))[0] != 0:
        raise ValueError('mutant bypassed splice refusal')
    if any(statuses[number] != 'same' for number in range(1, expected_edit)):
        raise ValueError('mutation failed before its intended consumer')
    detected = statuses[expected_edit] == 'DIFF'
    if permit_path_change:
        if baseline_raw is None:
            raise ValueError('missing baseline route evidence')
        wanted = records(baseline_raw.read_text())[1].get(expected_edit)
        observed = paths.get(expected_edit)
        detected = detected or (wanted is not None and observed is not None and observed != wanted)
    if not detected:
        raise ValueError('intended omission was not detected')
    return statuses, paths


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver')
    parser.add_argument('output', type=Path)
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--compare', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        controls(args.output)
    elif args.compare:
        compare(args.output, args.compare)
    else:
        run(args.driver, args.output, retained=not args.baseline)
