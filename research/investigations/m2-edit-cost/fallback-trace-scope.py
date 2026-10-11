"""Install read-only diagnostic helpers in the workflow's private source tree.

This is imported only by fallback-trace-patch.py. Its observations never enter
canonical renderer source; remove it with the temporary trace workflow.
"""
from pathlib import Path

HERE = Path(__file__).parent


def patch(tree, once):
    template = (HERE / 'fallback-trace-layout.wf').read_text()
    split = template.index('fn empty_trace_scope')
    interface = tree / 'renderer/layout/module.wfm'
    source = interface.read_text()
    fields = '  trace_old_scope: TraceScope;\n  trace_built_scope: TraceScope;\n  trace_source: TraceSource;\n  trace_edit: u32;\n  trace_parent: u32;\n  trace_root: u32;\n  trace_context: u32;\n  trace_context_node: u32;\n  trace_removing: Bool;\n  trace_floats: Box<Slots<i64>>;\n'
    source = once(source, 'public struct Layout {\n', template[:split].rstrip() + '\n\npublic struct Layout {\n' + fields)
    source = source.rstrip() + '\n\npublic fn fallback_trace_scope(layout: &Layout) -> made: Box<Array<u64>> reads(layout) doc "Private diagnostic live checkpoint census.";\n\npublic fn fallback_trace_data(layout: &Layout) -> (parent: u32, edit: u32, neutral: u32, failure: u32, guard: u32) reads(layout) doc "Private source-only seam certificate and actual guard.";\n\npublic fn fallback_trace_floats(layout: &Layout) -> made: Box<Slots<i64>> reads(layout) doc "Private copied proof-contributor rows.";\n'
    interface.write_text(source)
    build = tree / 'renderer/layout/build.wf'
    source = build.read_text()
    init = """  let trace_old_scope = empty_trace_scope();
  let trace_built_scope = empty_trace_scope();
  let trace_source = empty_trace_source();
  let trace_removing = False();
  let trace_floats = box_slots_new::<i64>(capacity: 0_u64);
"""
    constructor = 'Layout(trace_old_scope: trace_old_scope, trace_built_scope: trace_built_scope, trace_source: trace_source, trace_edit: no_index, trace_parent: no_index, trace_root: no_index, trace_context: no_index, trace_context_node: no_index, trace_removing: trace_removing, trace_floats: move trace_floats, '
    source = once(source, '  let made = Layout(', init + '  let made = ' + constructor)
    build.write_text(source)
    helper = tree / 'renderer/layout/fallback-trace-layout.wf'
    helper.write_text('alias Document = pkg::dom::Document;\nalias Styles = pkg::style::Styles;\nalias Traversal = pkg::style::Traversal;\nalias changed_boxes_only = pkg::style::changed_boxes_only;\n\n' + template[split:].rstrip() + '\n' + GETTERS)
    splice = tree / 'renderer/layout/splice.wf'
    source = splice.read_text()
    anchor = '  if references_stable {\n  } else {'
    source = once(source, anchor, INITIAL + anchor)
    # Source seam must be checked even if a stronger early context check refuses.
    anchor = '  let frontier_block = no_index;'
    early = '''  let trace_before_item = splice_source(layout: layout, node: before, serial: owner.serial);
  let trace_removed_item = splice_source(layout: layout, node: removed, serial: owner.serial);
  let trace_ending = match before {
    Some(..) => {
      give False();
    }
    None() => {
      give True();
    }
  }
  let trace_seam = trace_source_seam_at(context: &layout^.root, steps: &steps.inner[0_u64..depth], depth: 0_u64, owner: owner.block, before: trace_before_item, removed: trace_removed_item, removing: removing, ending: trace_ending);
  if trace_seam {
    set layout^.trace_source.failure = iand(layout^.trace_source.failure, 4294967263_u32);
  }
'''
    source = once(source, anchor, early + anchor)
    anchor = '  let plan = match splice_plan_at('
    source = once(source, anchor, '''  if inserting {
    set layout^.trace_floats = trace_float_exports(context: &fresh, styles: styles, document: document, root: layout^.trace_root, edit: layout^.trace_edit);
  }
''' + anchor)
    anchor = '  return Ok<u32, LayoutError>(value: 0_u32);'
    source = once(source, anchor, '''  if inserting {
    let found = trace_source_tree(context: &layout^.root, styles: styles, edit: layout^.trace_edit);
    set layout^.trace_source.matches = found.matches;
    set layout^.trace_source.failure = ior(layout^.trace_source.failure, found.failure);
  }
''' + anchor)
    splice.write_text(source)
    structure = tree / 'renderer/layout/structure.wf'
    source = structure.read_text()
    anchor = '  let rebuild = propagate rebuild_of(context: &layout^.root, steps: &base.inner[0_u64..base_count], depth: 0_u64);'
    source = once(source, anchor, anchor + OLD_SCOPE)
    anchor = '  finish_tree_sequences(context: &built);'
    source = once(source, anchor, anchor + '''
  set layout^.trace_built_scope = trace_scope_tree(context: &built, document: document, edit: layout^.trace_edit, root: layout^.trace_root);
  if layout^.trace_removing {
  } else {
    let found = trace_source_tree(context: &built, styles: new, edit: layout^.trace_edit);
    set layout^.trace_source.matches = found.matches;
    set layout^.trace_source.failure = ior(layout^.trace_source.failure, found.failure);
  }''')
    anchor = '  let recorded = propagate record_tree(context: &built, parent: old_path.parent, child: old_path.child, paths: &paths, listing: &listing, uses: &uses, routes: &routes, context_of: &context_of, root: root);'
    source = once(source, anchor, '  let trace_routes_before = routes.len;\n' + anchor + '''
  let (trace_new_routes, trace_outside_new_routes) = trace_scope_routes(context: &built, paths: &paths, routes: &routes, scope: built.slot, from: trace_routes_before, until: routes.len, document: document, edit: layout^.trace_edit, root: root);
  set layout^.trace_built_scope.routes = trace_new_routes;
  set layout^.trace_built_scope.outside_routes = trace_outside_new_routes;''')
    structure.write_text(source)
    oracle = tree / 'renderer/oracle/layout/edit.wf'
    source = oracle.read_text()
    source = once(source, 'alias structure_splice = pkg::layout::structure_splice;', 'alias structure_splice = pkg::layout::structure_splice;\nalias fallback_trace_scope = pkg::layout::fallback_trace_scope;\nalias fallback_trace_data = pkg::layout::fallback_trace_data;\nalias fallback_trace_floats = pkg::layout::fallback_trace_floats;')
    anchor = '  let after_delta = stamp(clock: clock, witness: &kept^.layout);'
    # This anchor occurs in several paths; limit to the structural function.
    start = source.index('fn apply_structure_edit(')
    stop = source.index('fn full_structure_edit(', start)
    body = source[start:stop]
    body = once(body, anchor, '  put_fallback_trace(buffer: report, number: number, reason: splice_reason, layout: &kept^.layout);\n' + anchor)
    source = (source[:start] + body + source[stop:]).rstrip() + '\n' + ORACLE
    oracle.write_text(source)


INITIAL = '''  set layout^.trace_old_scope = empty_trace_scope();
  set layout^.trace_built_scope = empty_trace_scope();
  set layout^.trace_context = no_index;
  set layout^.trace_context_node = no_index;
  set layout^.trace_parent = parent.index;
  set layout^.trace_root = no_index;
  if 0_u64 < traversal^.elements.inner.len {
    set layout^.trace_root = traversal^.elements.inner[0_u64].index;
  }
  set layout^.trace_edit = no_index;
  set layout^.trace_removing = False();
  match inserted {
    Some(value: node) => {
      set layout^.trace_edit = node.index;
    }
    None() => {
    }
  }
  match removed {
    Some(value: node) => {
      set layout^.trace_edit = node.index;
      set layout^.trace_removing = True();
    }
    None() => {
    }
  }
  let trace_source = empty_trace_source();
  set trace_source.failure = 32_u32;
  if layout^.trace_removing {
    let found = trace_source_tree(context: &layout^.root, styles: styles, edit: layout^.trace_edit);
    set trace_source.matches = found.matches;
    set trace_source.failure = ior(trace_source.failure, found.failure);
  }
  if references_stable {
  } else {
    set trace_source.failure = ior(trace_source.failure, 16_u32);
  }
  set layout^.trace_source = trace_source;
  let trace_frontier = trace_source_frontier(layout: layout, document: document, styles: styles, traversal: traversal, changed: changed, edit: layout^.trace_edit);
  if trace_frontier {
  } else {
    set layout^.trace_source.failure = ior(layout^.trace_source.failure, 8_u32);
  }
  set layout^.trace_floats = box_slots_new::<i64>(capacity: 0_u64);
  if layout^.trace_removing {
    set layout^.trace_floats = trace_float_exports(context: &layout^.root, styles: styles, document: document, root: layout^.trace_root, edit: layout^.trace_edit);
  }
'''
OLD_SCOPE = '''
  set layout^.trace_context = serial;
  set layout^.trace_context_node = index_for_trace(element: element);
  set layout^.trace_old_scope = trace_scope_at(context: &layout^.root, steps: &base.inner[0_u64..base_count], depth: 0_u64, document: document, edit: layout^.trace_edit, root: layout^.trace_root);
  let (trace_old_routes, trace_outside_old_routes) = trace_scope_existing_routes(layout: layout, scope: serial, document: document, edit: layout^.trace_edit, root: layout^.trace_root);
  set layout^.trace_old_scope.routes = trace_old_routes;
  set layout^.trace_old_scope.outside_routes = trace_outside_old_routes;
  let trace_visits = layout^.trace_visits;
  if trace_visits.trace_reach != -9223372036854775807_i64 {
    set layout^.trace_floats = trace_float_extrema(context: &layout^.root, serial: trace_visits.trace_serial, owner: trace_visits.trace_owner, selected: trace_visits.trace_selected, reach: trace_visits.trace_reach, old_floor: trace_visits.trace_old_floor, new_floor: trace_visits.trace_new_floor, added_floor: trace_visits.trace_added_floor, delta: trace_visits.trace_delta, removing: layout^.trace_removing, styles: old, root: layout^.trace_root, edit: layout^.trace_edit);
  }'''
GETTERS = '''
fn index_for_trace(element: u64) -> index: u32 pure {
  return cvt.wrap::<u64, u32>(element);
}

fn fallback_trace_scope(layout: &Layout) -> made: Box<Array<u64>> reads(layout) {
  let made = box_array_filled::<u64>(count: 20_u64, value: 0_u64);
  let old = layout^.trace_old_scope;
  let fresh = layout^.trace_built_scope;
  set made.inner[0_u64] = cvt::<u32, u64>(layout^.trace_context);
  set made.inner[1_u64] = cvt::<u32, u64>(layout^.trace_context_node);
  set made.inner[2_u64] = old.blocks;
  set made.inner[3_u64] = old.paragraphs;
  set made.inner[4_u64] = old.contexts;
  set made.inner[5_u64] = old.routes;
  set made.inner[6_u64] = old.outside_blocks;
  set made.inner[7_u64] = old.outside_paragraphs;
  set made.inner[8_u64] = old.outside_contexts;
  set made.inner[9_u64] = old.outside_routes;
  set made.inner[10_u64] = fresh.blocks;
  set made.inner[11_u64] = fresh.paragraphs;
  set made.inner[12_u64] = fresh.contexts;
  set made.inner[13_u64] = fresh.routes;
  set made.inner[14_u64] = fresh.outside_blocks;
  set made.inner[15_u64] = fresh.outside_paragraphs;
  set made.inner[16_u64] = fresh.outside_contexts;
  set made.inner[17_u64] = fresh.outside_routes;
  set made.inner[18_u64] = old.mixed_paragraphs;
  set made.inner[19_u64] = fresh.mixed_paragraphs;
  return move made;
}

fn fallback_trace_data(layout: &Layout) -> (parent: u32, edit: u32, neutral: u32, failure: u32, guard: u32) reads(layout) {
  let failure = layout^.trace_source.failure;
  if layout^.trace_source.matches != 1_u64 {
    set failure = ior(failure, 1_u32);
  }
  let neutral = if failure == 0_u32 {
    give 1_u32;
  } else {
    give 0_u32;
  }
  return layout^.trace_parent, layout^.trace_edit, neutral, failure, layout^.trace_guard;
}

fn fallback_trace_floats(layout: &Layout) -> made: Box<Slots<i64>> reads(layout) {
  let made = box_slots_new::<i64>(capacity: 0_u64);
  let count = layout^.trace_floats.inner.len;
  for (at in 0_u64..count) {
    trace_push_signed(cell: &made, value: layout^.trace_floats.inner[at]);
  }
  return move made;
}
'''
ORACLE = '''
const trace_edit_label: Array<u8, 20> = "fallback_trace edit ";

const trace_guard_label: Array<u8, 21> = "fallback_trace guard ";

const trace_neutral_label: Array<u8, 23> = "fallback_trace neutral ";

const trace_scope_label: Array<u8, 21> = "fallback_trace scope ";

const trace_float_label: Array<u8, 21> = "fallback_trace float ";

fn put_trace_number(buffer: &Box<Slots<u8>>, value: u64) -> result: unit writes(buffer) {
  put_byte(buffer: buffer, value: 32_u8);
  put_decimal(buffer: buffer, value: value);
  return unit;
}

fn put_trace_signed(buffer: &Box<Slots<u8>>, value: i64) -> result: unit writes(buffer) {
  put_byte(buffer: buffer, value: 32_u8);
  if value < 0_i64 {
    put_byte(buffer: buffer, value: 45_u8);
    let bits = cvt.wrap::<i64, u64>(value);
    let wide = 0_u64 -wrap bits;
    put_decimal(buffer: buffer, value: wide);
  } else {
    let wide = cvt::<i64, u64>(value);
    put_decimal(buffer: buffer, value: wide);
  }
  return unit;
}

fn put_fallback_trace(buffer: &Box<Slots<u8>>, number: u64, reason: u32, layout: &Layout) -> result: unit reads(layout), writes(buffer) {
  let (parent, edit, neutral, failure, guard) = fallback_trace_data(layout: layout);
  put_text(buffer: buffer, text: &trace_edit_label[0_u64..trace_edit_label.len]);
  put_decimal(buffer: buffer, value: number);
  let admitted = if reason == 0_u32 {
    give 1_u64;
  } else {
    give 0_u64;
  }
  put_trace_number(buffer: buffer, value: admitted);
  let reason_value = cvt::<u32, u64>(reason);
  put_trace_number(buffer: buffer, value: reason_value);
  let parent_value = cvt::<u32, u64>(parent);
  let edit_value = cvt::<u32, u64>(edit);
  put_trace_number(buffer: buffer, value: parent_value);
  put_trace_number(buffer: buffer, value: edit_value);
  put_byte(buffer: buffer, value: 10_u8);
  put_text(buffer: buffer, text: &trace_guard_label[0_u64..trace_guard_label.len]);
  put_decimal(buffer: buffer, value: number);
  let guard_value = cvt::<u32, u64>(guard);
  put_trace_number(buffer: buffer, value: guard_value);
  put_byte(buffer: buffer, value: 10_u8);
  put_text(buffer: buffer, text: &trace_neutral_label[0_u64..trace_neutral_label.len]);
  put_decimal(buffer: buffer, value: number);
  let neutral_value = cvt::<u32, u64>(neutral);
  let failure_value = cvt::<u32, u64>(failure);
  put_trace_number(buffer: buffer, value: neutral_value);
  put_trace_number(buffer: buffer, value: failure_value);
  put_byte(buffer: buffer, value: 10_u8);
  if reason != 0_u32 {
    let scope = fallback_trace_scope(layout: layout);
    put_text(buffer: buffer, text: &trace_scope_label[0_u64..trace_scope_label.len]);
    put_decimal(buffer: buffer, value: number);
    let count = scope.inner.len;
    for (at in 0_u64..count) {
      put_trace_number(buffer: buffer, value: scope.inner[at]);
    }
    put_byte(buffer: buffer, value: 10_u8);
    if reason == 9_u32 {
      let floats = fallback_trace_floats(layout: layout);
      let rows = floats.inner.len / 7_u64;
      for (row in 0_u64..rows) {
        put_text(buffer: buffer, text: &trace_float_label[0_u64..trace_float_label.len]);
        put_decimal(buffer: buffer, value: number);
        for (field in 0_u64..7_u64) {
          let start = row *sat 7_u64;
          let at = start +sat field;
          if at < floats.inner.len {
            put_trace_signed(buffer: buffer, value: floats.inner[at]);
          }
        }
        put_trace_number(buffer: buffer, value: guard_value);
        put_byte(buffer: buffer, value: 10_u8);
      }
    }
  }
  return unit;
}
'''
