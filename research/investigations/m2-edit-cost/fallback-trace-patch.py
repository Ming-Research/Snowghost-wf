"""Apply increment-0 observations to a private CI source tree only.

fallback-trace.yml and fallback-source.yml are the callers. The ordinary tree has no diagnostic
fields, branches, allocations or helper calls. Delete with that workflow.
All anchors are checked before writing a patched file; a source change must
be reconciled explicitly rather than silently tracing a different guard.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).parent


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(('trace anchor is not unique', old))
    return text.replace(old, new, 1)


def functions(source):
    starts = list(re.finditer(r'^fn ([a-z_]+)\(', source, re.M))
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(source)
        yield start.group(1), start.start(), end, source[start.start():end]


class Guards:
    def __init__(self):
        self.rows = []

    def make(self, file, function, source, offset, guard, anchor):
        number = len(self.rows) + 1
        self.rows.append(dict(id=number, file=file, function=function,
                             line=source[:offset].count('\n') + 1,
                             guard=guard, anchor=anchor, kind='guard'))
        return number

    def note(self, file, name, source, offset, guard, anchor, indent):
        number = self.make(file, name, source, offset, guard, anchor)
        actual = '&visits' if name in ('structure_splice', 'splice_move') else 'visits'
        return f'{indent}trace_note(visits: {actual}, guard: {number}_u32);\n'


CLONES = {
    'motion_above', 'motion_range_ready', 'splice_edges_equal',
    'splice_container_ready', 'splice_grid_ready', 'splice_grid_flex_width',
    'splice_width_stable',
}

FAILURE_FUNCTIONS = {
    'splice_boundary', 'splice_context_ready', 'splice_inputs',
    'splice_sibling_ready', 'splice_sequence_plan', 'splice_plan_at',
    'splice_block_path', 'splice_path_ready', 'splice_move',
    'actual_flow_ready', 'changed_entry_ready', 'splice_child_entry',
    'owner_motion_ready', 'outward_motion_ready', 'structure_splice',
}


def predicate(body, offset):
    """Retain the real branch and local definitions, never infer from reason."""
    before = body[:offset]
    lines = before.splitlines()
    # A line's brace depth, rather than the last textual if, distinguishes
    # a live refusal edge from an already completed earlier branch.
    stack = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('}') and stack:
            closed = stack.pop()
        else:
            closed = None
        condition = re.search(r'\bif (.+) \{$', stripped)
        if condition:
            stack.append(('if', condition.group(1)))
        elif stripped.endswith('{'):
            if stripped == '} else {' and closed and closed[0] == 'if':
                stack.append(('else', closed[1]))
            else:
                stack.append(('scope', stripped))
    nearest = next((('False() == ' if kind == 'else' else 'True() == ') + condition
                    for kind, condition in reversed(stack) if kind in ('if', 'else')),
                   'function fallthrough; preceding alternatives did not return')
    definitions = []
    for line in lines:
        match = re.match(r'\s*let ([a-z_]+) = ([^;]+);$', line)
        if match and re.search(r'\b' + match.group(1) + r'\b', nearest):
            definitions.append(line.strip())
    return ' | '.join([nearest] + definitions)


def instrument_body(file, name, original, source, original_offset, guards):
    body = original
    def note_at(anchor, guard, indent):
        site = source.find(anchor, original_offset)
        if site < 0:
            raise ValueError(('missing original predicate', name, anchor))
        return guards.note(file, name.removeprefix('trace_'), source, site,
                           guard, anchor, indent)
    if name == 'splice_boundary':
        anchor = '          return 0_u32;\n        }\n      }\n    }\n    Close(..)'
        replacement = '          return 0_u32;\n        } else {\n'
        for field in ('no_lines', 'no_fragments'):
            replacement += f'          if {field} {{\n          }} else {{\n'
            replacement += note_at(anchor, field + ' == False()', '            ')
            replacement += '          }\n'
        replacement += '        }\n      }\n    }\n    Close(..)'
        body = once(body, anchor, replacement)
        for variant in ('Close', 'Out'):
            anchor = f'    {variant}(..) => {{\n    }}'
            body = once(body, anchor, f'    {variant}(..) => {{\n' +
                        note_at(anchor, 'item variant is ' + variant, '      ') + '    }')
        # Each failed payload lookup is a distinct leaf, including a stale
        # Text route. Observe in its bounded branch before falling through.
        for field, ending in (('blocks', '        return 0_u32;\n      }\n    }\n    Child'),
                              ('children', '        return 0_u32;\n      }\n    }\n    Text')):
            replacement = ending.replace('\n      }\n    }', '\n      } else {\n' +
                note_at(ending, f'at >= context^.{field}.inner.len', '        ') + '      }\n    }', 1)
            body = once(body, ending, replacement)
    if name in ('splice_sibling_ready', 'splice_plan_at', 'splice_inputs'):
        anchor = {'splice_sibling_ready': '    }\n    return False();\n  }\n  let at',
                  'splice_plan_at': '    }\n    return Err<SplicePlan, u32>(error: 1_u32);\n  }\n  if input.owner',
                  'splice_inputs': '    }\n    return Err<SpliceInput, u32>(error: 1_u32);\n  }\n  let frame'}[name]
        # inputs has a preflight with explicit leaves already; only its
        # repeated route descent needs this diagnostic expansion.
        if body.count(anchor) != 1:
            raise ValueError(('missing route fallthrough', name))
        position = body.index(anchor) + len('    }\n')
        observations = '    if child < context^.children.inner.len {\n'
        observations += '      if context^.slot != route.parent {\n'
        observations += note_at(anchor, 'context^.slot != route.parent', '        ') + '      }\n'
        observations += '      if context^.children.inner[child].slot != route.slot {\n'
        observations += note_at(anchor, 'context^.children.inner[child].slot != route.slot', '        ') + '      }\n'
        observations += '    } else {\n' + note_at(anchor, 'child >= context^.children.inner.len', '      ') + '    }\n'
        body = body[:position] + observations + body[position:]
    # bor failures report which already-read operand is true, rather than
    # merely naming the aggregated dirty flag.
    for function, variable, leaves in (
            ('splice_context_ready', 'unavailable', ['context^.dirty', 'context^.restyled']),
            ('trace_splice_grid_ready', 'changed', ['context^.dirty', 'context^.restyled']),
            ('trace_splice_container_ready', 'marked', ['context^.dirty', 'context^.restyled'])):
        if name == function:
            anchor = f'  if {variable} {{'
            observations = ''
            for leaf in leaves:
                observations += f'\n    if {leaf} {{\n' + note_at(anchor, leaf + ' == True()', '      ') + '    }'
            body = once(body, anchor, anchor + observations)
    # Decompose these conjunctions at their existing refusal edge. Each
    # observation is a constituent already computed by the ordinary code.
    splits = {
        ('splice_sequence_plan', 'supported'): ['same_edges', 'old.free_transfer', 'output.free_transfer'],
        ('splice_sequence_plan', 'movements_supported'): [],
        ('splice_block_path', 'ready'): ['grows', 'width_kept'],
        ('structure_splice', 'fits'): ['new_blocks', 'new_paragraphs', 'new_children'],
        ('trace_motion_range_ready', 'known'): ['suffix.motion_known', 'proposed.motion_known'],
        ('trace_splice_grid_flex_width', 'height_stable'): ['height', 'min_height', 'max_height'],
        ('trace_splice_grid_flex_width', 'limits'): ['min_width', 'max_width'],
    }
    for (function, variable), leaves in splits.items():
        if name != function or not leaves:
            continue
        anchor = f'  if {variable} {{\n  }} else {{'
        # splice_block_path is inside a loop.
        if body.count(anchor) != 1:
            anchor = f'    if {variable} {{\n    }} else {{'
        if body.count(anchor) != 1:
            raise ValueError(('missing composite edge', name, variable))
        indent = anchor.split('if', 1)[0] + '  '
        observations = ''
        for leaf in leaves:
            canonical_site = source.find(anchor, original_offset)
            note = guards.note(file, name.removeprefix('trace_'), source,
                               canonical_site if canonical_site >= 0 else original_offset,
                               f'{leaf} == False()', anchor, indent + '  ')
            observations += f'\n{indent}if {leaf} {{\n{indent}}} else {{\n{note}{indent}}}'
        body = once(body, anchor, anchor + observations)
    # Direct false return expressions need observations as well as explicit
    # return False branches. Their local scalar inputs are already settled.
    if name in ('trace_motion_above', 'trace_splice_width_stable',
                'trace_splice_container_ready', 'trace_splice_grid_ready',
                'trace_splice_grid_flex_width', 'splice_child_entry'):
        expressions = {'trace_motion_above': ['safe'],
                       'trace_splice_width_stable': ['fills'],
                       'trace_splice_container_ready': ['same'],
                       'trace_splice_grid_ready': ['band(same, width)'],
                       'trace_splice_grid_flex_width': ['band(grid, child^.grid_intrinsic_invariant)'],
                       'splice_child_entry': ['same']}[name]
        for expression in expressions:
            match = re.search(r'(?m)^( +)return ' + re.escape(expression) + r';$', body)
            if not match:
                raise ValueError(('missing scalar return', name, expression))
            indent = match.group(1)
            leaves = {'band(same, width)': ['same', 'width'],
                      'band(grid, child^.grid_intrinsic_invariant)': ['grid', 'child^.grid_intrinsic_invariant']}.get(expression, [expression])
            notes = ''
            for leaf in leaves:
                notes += f'{indent}if {leaf} {{\n{indent}}} else {{\n'
                description = f'{leaf} == False()'
                if name == 'trace_motion_above' and leaf == 'safe':
                    description = 'reach > proposed; proposed = floor +sat delta'
                notes += guards.note(file, name.removeprefix('trace_'), source,
                                     source.index('return ' + expression + ';', original_offset),
                                     description, match.group(0), indent + '  ')
                notes += f'{indent}}}\n'
            body = body[:match.start()] + notes + body[match.start():]
    failure = re.compile(r'(?m)^( +)return (?:False\(\)(?:, [^;]+)?|no, [^;]+|[1-9][0-9]*_u32|Err<Splice(?:Input|Plan), u32>\(error: [^;]+|Ok<u32, LayoutError>\(value: (?!0_u32)[^;]+);$')
    additions = []
    canonical_name = name.removeprefix('trace_')
    canonical = next(part for fn_name, start, stop, part in functions(source)
                     if fn_name == canonical_name)
    original_failures = list(failure.finditer(canonical))
    changed_failures = list(failure.finditer(body))
    if len(original_failures) != len(changed_failures):
        raise ValueError(('refusal edges changed while tracing', name))
    for ordinal, match in enumerate(changed_failures):
        indent = match.group(1)
        anchor = match.group(0).strip()
        original_match = original_failures[ordinal]
        description = predicate(canonical, original_match.start())
        if ordinal == len(changed_failures) - 1:
            fallthrough = {
                'splice_boundary': 'item is Text and paragraph index is outside context^.paragraphs.inner.len',
                'splice_child_entry': 'item variant is not Child',
                'owner_motion_ready': 'owner != no_index and at >= context^.blocks.inner.len',
                'splice_plan_at': 'input.owner != no_index and owner >= context^.blocks.inner.len',
                'splice_block_path': 'ancestor chain exceeds context^.blocks.inner.len + 1',
                'outward_motion_ready': 'ancestor chain exceeds context^.blocks.inner.len + 1',
            }
            if canonical_name in fallthrough:
                description = fallthrough[canonical_name]
        note = guards.note(file, canonical_name, source,
                           original_offset + original_match.start(),
                           description, anchor, indent)
        if 'context: &Context' in body.split('\n', 1)[0]:
            note += f'{indent}if visits^.trace_guard == {len(guards.rows)}_u32 {{\n{indent}  set visits^.trace_serial = context^.slot;\n{indent}}}\n'
        if name == 'structure_splice':
            note += f'{indent}set layout^.trace_guard = visits.trace_guard;\n{indent}set layout^.trace_visits = visits;\n'
        additions.append((match.start(), note))
    for offset, note in reversed(additions):
        body = body[:offset] + note + body[offset:]
    # The diagnostic identity read is additional to a narrowly stated
    # ordinary helper row. Keep broad rows as written and add only the
    # actual previously absent leaf read to narrow rows.
    header, rest = body.split('\n', 1)
    if 'context: &Context' in header and 'context^.slot' in body:
        covered = any(effect in header for effect in
                      ('reads(context)', 'writes(context)',
                       'reads(context.slot)', 'writes(context.slot)'))
        if not covered:
            if not header.endswith(' {'):
                raise ValueError(('unexpected effect row', name))
            row = re.search(r' (?:reads|writes)\(', header)
            if row is None:
                raise ValueError(('missing diagnostic effect row', name))
            header = header[:row.start()] + ' reads(context.slot),' + header[row.start():]
            body = header + '\n' + rest
    return body


def patch_guards(tree, guards):
    original_boundary = (tree / 'renderer/layout/splice_boundary.wf').read_text()
    module = tree / 'renderer/layout/module.wfm'
    source = module.read_text()
    source = once(source, '  frontier_reasons: u32;\n}', '''  frontier_reasons: u32;
  trace_guard: u32;
  trace_serial: u32;
  trace_owner: u32;
  trace_selected: u32;
  trace_reach: i64;
  trace_old_floor: i64;
  trace_new_floor: i64;
  trace_delta: i64;
  trace_added_floor: i64;
}''')
    layout_start = source.index('struct Layout {')
    field_start = source.index('\n', layout_start) + 1
    if source.startswith('  doc ', field_start):
        field_start = source.index('\n', field_start) + 1
    source = source[:field_start] + '  trace_guard: u32;\n  trace_visits: BoundaryVisits;\n' + source[field_start:]
    module.write_text(source)
    boundary = tree / 'renderer/layout/boundary.wf'
    source = boundary.read_text()
    empty = ', trace_guard: 0_u32, trace_serial: no_index, trace_owner: no_index, trace_selected: no_index, trace_reach: -9223372036854775807_i64, trace_old_floor: 9223372036854775807_i64, trace_new_floor: 9223372036854775807_i64, trace_delta: 0_i64, trace_added_floor: 9223372036854775807_i64'
    source = once(source, 'frontier_reasons: 0_u32);', 'frontier_reasons: 0_u32' + empty + ');')
    source = once(source, '  let total = BoundaryVisits(', '''  let selected = if first.trace_guard != 0_u32 {
    give first;
  } else {
    give second;
  }
  let total = BoundaryVisits(''')
    fields = ', '.join(f'trace_{field}: selected.trace_{field}' for field in ('guard', 'serial', 'owner', 'selected', 'reach', 'old_floor', 'new_floor', 'delta', 'added_floor'))
    source = once(source, 'frontier_reasons: frontier_reasons);', 'frontier_reasons: frontier_reasons, ' + fields + ');')
    boundary.write_text(source)
    build = tree / 'renderer/layout/build.wf'
    source = build.read_text()
    source = once(source, '  let made = Layout(root:', '  let trace_visits = no_boundary_visits();\n  let made = Layout(trace_guard: 0_u32, trace_visits: trace_visits, root:')
    build.write_text(source)
    for path in sorted((tree / 'renderer/layout').glob('splice*.wf')):
        source = path.read_text()
        replacements = []
        clones = []
        for name, start, stop, original in functions(source):
            if name in CLONES:
                clone = original.replace('fn ' + name + '(', 'fn trace_' + name + '(', 1)
                clone = clone.replace(') -> ', ', visits: &BoundaryVisits) -> ', 1)
                header, rest = clone.split('\n', 1)
                if ' pure {' in header:
                    header = header.replace(' pure {', ' writes(visits) {')
                else:
                    header = header[:-2] + ', writes(visits) {'
                clone = header + '\n' + rest
                clones.append(instrument_body(str(path.relative_to(tree)), 'trace_' + name, clone, source, start, guards))
            if name in FAILURE_FUNCTIONS:
                body = original
                if name == 'structure_splice':
                    body = once(body, '  let visits = no_boundary_visits();\n', '')
                    doc_end = body.index('\n', body.index('  doc ')) + 1
                    body = body[:doc_end] + '  let visits = no_boundary_visits();\n  set layout^.trace_guard = 0_u32;\n  set layout^.trace_visits = visits;\n' + body[doc_end:]
                replacements.append((start, stop, instrument_body(str(path.relative_to(tree)), name, body, source, start, guards)))
        for start, stop, body in reversed(replacements):
            source = source[:start] + body + source[stop:]
        if clones:
            source = source.rstrip('\n') + '\n\n' + '\n\n'.join(
                clone.strip('\n') for clone in clones) + '\n'
        # Redirect only already instrumented functions. Ordinary layout
        # callers retain the unchanged read-only predicates.
        replacements = []
        for name, start, stop, body in functions(source):
            if name not in FAILURE_FUNCTIONS and not name.startswith('trace_') and name != 'sequence_motion_ready':
                continue
            for target in CLONES:
                pattern = r'(?<![a-z_])' + target + r'\(([^\n]+)\);'
                body = re.sub(pattern, lambda m: 'trace_' + target + '(' + m.group(1) + ', visits: visits);', body)
            if name == 'sequence_motion_ready':
                # The traced callee now reads the context identity. This
                # forwarding helper has no refusal edge of its own, so
                # instrument_body's direct-read augmentation does not visit it.
                body = once(body, 'reads(context.blocks.inner)',
                            'reads(context.slot), reads(context.blocks.inner)')
            replacements.append((start, stop, body))
        for start, stop, body in reversed(replacements):
            source = source[:start] + body + source[stop:]
        path.write_text(source)
    motion = tree / 'renderer/layout/splice_motion.wf'
    source = motion.read_text()
    start = source.index('fn trace_motion_range_ready(')
    stop = source.index('\nfn ', start + 3) if '\nfn ' in source[start + 3:] else len(source)
    body = source[start:stop]
    anchor = '  let ready = trace_motion_above(reach: fixed_reach, floor: floor, delta: 0_i64, visits: visits);'
    body = once(body, anchor, anchor + '''
  if ready {
  } else {
    set visits^.trace_serial = context^.slot;
    set visits^.trace_owner = owner;
    set visits^.trace_reach = fixed_reach;
    set visits^.trace_old_floor = old.natural_floor;
    set visits^.trace_new_floor = fresh.natural_floor;
  }''')
    source = source[:start] + body + source[stop:]
    motion.write_text(source)
    boundary = tree / 'renderer/layout/splice_boundary.wf'
    source = boundary.read_text()
    anchor = '  let motion_ready = trace_motion_range_ready(context: context, owner: input.owner, fixed_reach: fixed_reach, suffix: suffix, proposed: affected_new, visits: visits);'
    source = once(source, anchor, '  set visits^.trace_selected = selected;\n  set visits^.trace_delta = wide_delta;\n' + anchor)
    anchor = '  let placed_added = shift_motion(output: added, delta: inserted_y);'
    source = once(source, anchor, anchor + '''
  if placed_added.natural_floor != 9223372036854775807_i64 {
    let trace_owner_origin = block_origin(context: context, block: input.owner);
    set visits^.trace_added_floor = placed_added.natural_floor +sat trace_owner_origin.y;
  }''')
    # Independent moves retain their own diagnostic leaf; balanced reduction
    # already combines visits, so no shared writer orders sibling work.
    anchor = '    set supported = text;'
    note = guards.note('renderer/layout/splice_boundary.wf', 'splice_move', original_boundary, original_boundary.index(anchor), 'own.through && item is neither Text nor Float nor Out', anchor, '      ')
    source = once(source, anchor, anchor + '\n    if text {\n    } else {\n' + note + '    }')
    anchor = '    set supported = band(supported, uniform);'
    note = guards.note('renderer/layout/splice_boundary.wf', 'splice_move', original_boundary, original_boundary.index(anchor), 'uniform_required && move_y != expected_delta', anchor, '      ')
    source = once(source, anchor, anchor + '\n    if uniform {\n    } else {\n' + note + '    }')
    anchor = '          lay_out_context(context: context, styles: styles, document: document, fonts: fonts, picks: picks, viewport: viewport);'
    fields = ('guard', 'serial', 'owner', 'selected', 'reach', 'old_floor', 'new_floor', 'delta', 'added_floor')
    restore = '\n'.join(f'          set context^.boundary_visits.trace_{field} = held_trace.trace_{field};' for field in fields)
    source = once(source, anchor, '          let held_trace = context^.boundary_visits;\n' + anchor + '\n' + restore)
    boundary.write_text(source)
    splice = tree / 'renderer/layout/splice.wf'
    source = splice.read_text()
    # Flex computes a possible later grid eligibility input even when the
    # eventual target is ordinary flow. Preserve normal visit counts, but
    # do not mistake a failed optional input probe for an actual refusal.
    anchor = '            let active = splice_child_entry(context: context, child: child, visits: visits);'
    source = once(source, anchor, '            let trace_optional_previous = visits^;\n' + anchor)
    anchor = '            give band(grid_inline_stable, edge);'
    fields = ('guard', 'serial', 'owner', 'selected', 'reach', 'old_floor',
              'new_floor', 'delta', 'added_floor')
    restored = '\n'.join(
        f'            set visits^.trace_{field} = trace_optional_previous.trace_{field};'
        for field in fields)
    source = once(source, anchor, restored + '\n' + anchor)
    anchor = '  let work = add_boundary_visits(first: visits, second: published_work);'
    source = once(source, anchor, anchor + '\n  set visits = work;')
    splice.write_text(source)
    helper = tree / 'renderer/layout/fallback-trace-guard.wf'
    helper.write_text('''fn trace_note(visits: &BoundaryVisits, guard: u32) -> result: unit writes(visits.trace_guard) {
  doc "Keeps the first actual failed leaf in the attempted certificate; independent suffix leaves combine through the existing balanced visits reduction.";
  if visits^.trace_guard == 0_u32 {
    set visits^.trace_guard = guard;
  }
  return unit;
}
''')
    # The oracle historically maps any LayoutError from the splice attempt
    # to path reason 9. Observe that mapping separately from a float refusal.
    edit = tree / 'renderer/oracle/layout/edit.wf'
    source = edit.read_text()
    start = source.index('fn apply_structure_edit(')
    stop = source.index('\nfn ', start + 3)
    body = source[start:stop]
    anchor = '    Err(..) => {\n      give 9_u32;\n    }'
    site = source.index(anchor, start)
    clauses = ''
    for variant in ('TooLarge', 'Inconsistent', 'Text'):
        guard = guards.make('renderer/oracle/layout/edit.wf', 'apply_structure_edit', source,
                            site, 'structure_splice returned LayoutError::' + variant,
                            anchor)
        guards.rows[-1]['kind'] = 'layout_error'
        clauses += f'    {variant}() => {{\n      set layout^.trace_guard = {guard}_u32;\n    }}\n'
    body = once(body, anchor, '    Err(error: failed) => {\n      trace_layout_error(layout: &kept^.layout, error: failed);\n      give 9_u32;\n    }')
    source = source[:start] + body + source[stop:]
    source = 'alias trace_layout_error = pkg::layout::trace_layout_error;\n' + source
    edit.write_text(source)
    module = tree / 'renderer/layout/module.wfm'
    source = module.read_text()
    source = source.rstrip('\n') + '\n\npublic fn trace_layout_error(layout: &Layout, error: LayoutError) -> result: unit writes(layout) doc "Private observation of the existing splice-error path.";\n'
    module.write_text(source)
    source = helper.read_text().rstrip('\n') + '\n'
    source += '''
fn trace_layout_error(layout: &Layout, error: LayoutError) -> result: unit writes(layout) {
  doc "Separately observes the driver's existing reason-nine mapping for actual layout errors.";
  match error {
''' + clauses + '''  }
  return unit;
}
'''
    helper.write_text(source)


def patch(tree):
    guards = Guards()
    patch_guards(tree, guards)
    spec = importlib.util.spec_from_file_location('trace_scope_patch', HERE / 'fallback-trace-scope.py')
    scope = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scope)
    scope.patch(tree, once)
    return guards.rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['patch'])
    parser.add_argument('tree', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    rows = patch(args.tree)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
    main()
