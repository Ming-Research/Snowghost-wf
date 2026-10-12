"""Focused increment-1 omission mutations, built and executed only in CI.

Each mutant must compile, reach source retention, finish the script, and fail
through its intended consumer. A crash, partial output or an earlier refusal
never counts as semantic evidence. Remove with fallback-source.yml once this
increment's evidence is archived.
"""
import argparse
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('retained_source', Path(__file__).with_name('retained-source.py'))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

MUTATIONS = {
    'omit-sibling-closure': ('closure-sibling', 1),
    'omit-branch-closure': ('closure-branch', 1),
    'equal-size-publication-cutoff': ('publication', 1),
    'omit-source-text-route': ('routes-text', 2),
    'omit-source-style-route': ('routes-style', 4),
    'omit-source-context-route': ('routes-context', 12),
    'reason-10-rank-replay': ('flex-outward-reentry', None),
}


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('mutation anchor absent or repeated: ' + old)
    return source.replace(old, new)


def apply(name):
    if name == 'reason-10-rank-replay':
        path = Path('renderer/oracle/layout/edit.wf')
        source = path.read_text()
        call = ('structure_retain_source(layout: &kept^.layout, document: &page^.document, '
                'styles: &kept^.state.styles, traversal: &page^.traversal, atoms: &page^.atoms, '
                'changed: &done.changed.inner[0_u64..changed_count], parent: parent, before: next, '
                'inserted: inserted, removed: next, references_stable: stable, fonts: fonts, picks: &kept^.picks)')
        replacement = ('  } else if splice_reason == 10_u32 {\n'
                       '    match removed {\n'
                       '      Some(..) => {\n'
                       '        match ' + call + ' {\n'
                       '          Ok(value: source_kept) => {\n'
                       '            give source_kept;\n'
                       '          }\n'
                       '          Err(..) => {\n'
                       '            return Err<StyleUpdate, u8>(error: 9_u8);\n'
                       '          }\n'
                       '        }\n'
                       '      }\n'
                       '      None() => {\n'
                       '        give False();\n'
                       '      }\n'
                       '    }\n')
        source = replace_once(source,
            '  } else if splice_reason == 10_u32 {\n    give False();\n', replacement)
    elif name.startswith('omit-') and name.endswith('-closure'):
        path = Path('renderer/layout/retain_source.wf')
        source = replace_once(path.read_text(),
            '  let closure_marked = propagate styles_restyled(layout: layout, traversal: traversal, changed: changed);\n', '')
    elif name == 'equal-size-publication-cutoff':
        path = Path('renderer/layout/retain_source.wf')
        call = '  lay_out(layout: layout, document: document, styles: styles, fonts: fonts, picks: picks);'
        source = replace_once(path.read_text(), call,
            '  if input.basis_height == unknown {\n' + '  ' + call + '\n  }')
    else:
        path = Path('renderer/layout/splice_publish.wf')
        source = path.read_text()
        if name == 'omit-source-text-route':
            source = replace_once(source,
                '    route_write::<TextUnit>(table: &layout^.text_units, at: at, value: text);\n', '')
        elif name == 'omit-source-style-route':
            source = replace_once(source,
                '    route_write::<StyleUse>(table: &layout^.uses, at: at, value: uses);\n', '')
            source = replace_once(source,
                '    route_write::<StyleUse>(table: &layout^.uses, at: at, value: supplier_use);\n', '')
        else:
            source = replace_once(source,
                '    route_write::<u32>(table: &layout^.context_of, at: at, value: context_slot);\n', '')
    path.write_text(source)


def verify(name, baseline, mutant, out):
    if name == 'reason-10-rank-replay':
        verify_rank_replay(baseline, mutant, out)
        return
    case, consumer = MUTATIONS[name]
    baseline_folder, mutant_folder = out / 'baseline', out / 'mutant'
    page, script, metadata = fixture.prepare(baseline, baseline_folder, case)
    raw = baseline_folder / 'retained.raw'
    fixture.execute(baseline, 'edit', script, page, raw)
    fixture.validate(raw, script, metadata)
    permit_path_change = name == 'omit-source-context-route'
    try:
        fixture.detect(raw, script, metadata, consumer, permit_path_change, baseline_raw=raw)
    except ValueError as error:
        if str(error) != 'intended omission was not detected':
            raise
    else:
        raise ValueError('detector accepted the unmutated negative control')
    page, script, metadata = fixture.prepare(mutant, mutant_folder, case)
    mutant_raw = mutant_folder / 'retained.raw'
    fixture.execute(mutant, 'edit', script, page, mutant_raw)
    fixture.detect(mutant_raw, script, metadata, consumer, permit_path_change, baseline_raw=raw)
    if name == 'equal-size-publication-cutoff':
        require_equal_size_stale_interiors(mutant_raw)
    print(name + ': detected only after complete source retention at its intended consumer')


def require_equal_size_stale_interiors(raw):
    full, kept = [], []
    active, incremental = False, False
    for line in raw.read_text().splitlines():
        if line.startswith('edit 1 hash '):
            active = True
        elif active and line.startswith('edit 2 hash '):
            break
        elif active and line == 'inc dump':
            incremental = True
        elif active and line.startswith('E\t'):
            (kept if incremental else full).append(line.split('\t'))
    full_parent = [row for row in full if row[2] == 'section']
    kept_parent = [row for row in kept if row[2] == 'section']
    full_children = [row for row in full if row[2] == 'span']
    kept_children = [row for row in kept if row[2] == 'span']
    if len(full_parent) != 1 or full_parent != kept_parent:
        raise ValueError('publication mutant did not retain an equal-size enclosing parent')
    if len(full_children) != 2 or len(kept_children) != 2 or any(a == b for a, b in zip(full_children, kept_children)):
        raise ValueError('publication cutoff did not leave both retained branch interiors stale')


def verify_rank_replay(baseline, mutant, out):
    splice_spec = importlib.util.spec_from_file_location('splice_cases', fixture.SCRIPTS / 'splice-cases.py')
    splice = importlib.util.module_from_spec(splice_spec)
    splice_spec.loader.exec_module(splice)
    page = fixture.SCRIPTS / 'flex-case.html'
    baseline_folder = out / 'baseline'
    baseline_folder.mkdir(parents=True, exist_ok=True)
    listing = baseline_folder / 'nodes.txt'
    fixture.execute(baseline, 'nodes', 0, page, listing)
    # Select the existing fixture by its textual markers. This changes no
    # renderer path: the mutant models replay at the same logical rank, which
    # consumes the successor; replaying a tombstoned stable handle is inert.
    splice.CASES['flex'] = ('flex-outward-reentry',)
    edits, expected_paths = splice.generate(fixture.Tree(listing), 'flex')
    script = baseline_folder / 'rank-replay.edits'
    script.write_text(edits + 'P 1\n')
    paths = baseline_folder / 'rank-replay.paths'
    paths.write_text(expected_paths)
    raw = baseline_folder / 'rank-replay.raw'
    fixture.execute(baseline, 'edit', script, page, raw)
    fixture.inctime.read(raw, fixture.inctime.script_operations(script), checking=True, require_paths=True)
    splice.check_paths(paths, raw)
    records = fixture.records(raw.read_text())
    if records[1].get(1) != (0, 10) or not edits.startswith('X '):
        raise ValueError('existing reason-10 removal fixture was not reached')
    mutant_folder = out / 'mutant'
    mutant_folder.mkdir(parents=True, exist_ok=True)
    mutated = mutant_folder / 'rank-replay.raw'
    fixture.execute(mutant, 'edit', script, page, mutated)
    text = mutated.read_text()
    normalized = mutated.with_suffix('.protocol')
    normalized.write_text(fixture.re.sub(r' inc (DIFF|refused)$', ' inc same', text, flags=fixture.re.M))
    fixture.inctime.read(normalized, fixture.inctime.script_operations(script), checking=True, require_paths=True)
    statuses, observed, counts, hashes, base = fixture.records(text)
    if len(statuses) != len(fixture.inctime.script_operations(script)) or observed.get(1) != (0, 10) or statuses[1] != 'DIFF':
        raise ValueError('rank replay did not complete and differ at the already-published reason-10 removal')
    print('reason-10-rank-replay: positional double removal detected at reason 10, complete script')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
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
