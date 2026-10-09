#!/usr/bin/env python3
"""Temporary CI-only Q140 ablations/owned traces; removed before readiness.

The workflow compiles ordinary profiles before adding the trace, so diagnostic
storage never enters instruction counts. No native compiler option emits these
semantic layout inputs. Each trace stays on its child; collection is untimed.
"""
from pathlib import Path
import sys


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise SystemExit(f'{path}: expected one target: {old[:100]}')
    p.write_text(text.replace(old, new))


variant = sys.argv[1]
grid = 'renderer/layout/grid.wf'
if variant == 'equivalent':
    replace(grid, 'let same = same_space(first: child^.laid, second: space);',
            'let same = equivalent_space(styles: styles, style: style, first: child^.laid, second: space);')
elif variant == 'legacy':
    replace(grid, '    let same = same_space(first: child^.laid, second: space);', '''    let held = grid_read_row(record: &child^.grid_row);
    let forced = space.forced_height >= 0_i32;
    let matches = space.forced_height == child^.height;
    let unforced = bnot(forced);
    let fits = bor(unforced, matches);
    let percent = height_relative(styles: styles, style: style);
    let plain = bnot(percent);
    let depends = band(held.valid, plain);
    let same = band(depends, fits);''')
elif variant != 'trace':
    raise SystemExit('expected equivalent, legacy or trace')

if variant != 'trace':
    raise SystemExit(0)

module = 'renderer/layout/module.wfm'
replace(module, '  height_input: HeightInput;', '  q140_trace: Box<Slots<i64>>;\n  height_input: HeightInput;')
replace('renderer/layout/build.wf', '  return Context(height_input:',
        '  let q140_trace = box_slots_new::<i64>(capacity: 0_u64);\n  return Context(q140_trace: move q140_trace, height_input:')
with open(module, 'a') as f:
    f.write('\npublic fn q140_trace(layout: &Layout) -> values: Box<Slots<i64>> reads(layout) doc "Temporary owned grid-call diagnostic, collected after layout.";\n')

fields = [('phase', 'i32'), ('child^.slot', 'u32'), ('child^.style.element', 'u32'), ('child^.kind', 'u8'),
          ('child^.height', 'i32'), ('child^.width', 'i32')]
for prefix in ('child^.laid', 'space'):
    fields += [(prefix + '.' + field, 'i32') for field in ('available', 'basis_width', 'basis_height', 'forced_width', 'forced_height')]
    fields += [(prefix + '.shrink', 'Bool')]
fields += [(name, 'Bool') for name in ('child^.dirty', 'child^.restyled', 'child^.definite_free', 'child^.has_out', 'relative', 'ready')]
body = ['fn q140_trace_item(child: &Context, styles: &Styles, space: Space, phase: i32, ready: Bool) -> result: unit reads(styles), writes(child) {',
        '  let relative = height_relative(styles: styles, style: child^.style);']
for i, (value, kind) in enumerate(fields):
    if kind == 'Bool':
        body += [f'  let value{i} = if {value} {{', '    give 1_i64;', '  } else {', '    give 0_i64;', '  }']
    else:
        body += [f'  let value{i} = cvt::<{kind}, i64>({value});']
    body += [f'  let pushed{i} = push_item::<i64>(cell: &child^.q140_trace, value: value{i}, ceiling: item_ceiling);']
body += ['  return unit;', '}', '', '''fn q140_collect(context: &Context, values: &Box<Slots<i64>>) -> result: unit reads(context), writes(values) {
  let length = context^.q140_trace.inner.len;
  for (i in 0_u64..length) {
    let pushed = push_item::<i64>(cell: values, value: context^.q140_trace.inner[i], ceiling: item_ceiling);
  }
  let count = context^.children.inner.len;
  for (i in 0_u64..count) {
    q140_collect(context: &context^.children.inner[i], values: values);
  }
  return unit;
}

fn q140_trace(layout: &Layout) -> values: Box<Slots<i64>> reads(layout) {
  let values = box_slots_new::<i64>(capacity: 0_u64);
  q140_collect(context: &layout^.root, values: &values);
  return move values;
}''']
with open('renderer/layout/grid_retained.wf', 'a') as f:
    f.write('\n' + '\n'.join(body) + '\n')
replace(grid, '  if reuse {\n    grid_row_contribution',
        '  q140_trace_item(child: child, styles: styles, space: space, phase: 1_i32, ready: reuse);\n  if reuse {\n    grid_row_contribution')
replace(grid, '    if ready {\n      resolve_margins',
        '    q140_trace_item(child: child, styles: styles, space: space, phase: 2_i32, ready: ready);\n    if ready {\n      resolve_margins')
# Scalar record width is published with the trace's schema, not guessed by readers.
Path('build/attribute/trace-fields.txt').write_text('\n'.join(f'{i}: {value}' for i, (value, _) in enumerate(fields)) + '\n')
replace('renderer/oracle/layout/layout.wf',
        '        lay_out(layout: &layout, document: &page.document, styles: &styles, fonts: &fonts, picks: &picks);',
        '''        lay_out(layout: &layout, document: &page.document, styles: &styles, fonts: &fonts, picks: &picks);
        let values = pkg::layout::q140_trace(layout: &layout);
        let trace_buffer = box_slots_new::<u8>(capacity: 0_u64);
        let trace_length = values.inner.len;
        for (i in 0_u64..trace_length) {
          put_signed(buffer: &trace_buffer, value: values.inner[i]);
          let remainder = i % ''' + str(len(fields)) + '''_u64;
          if remainder == ''' + str(len(fields) - 1) + '''_u64 {
            put_byte(buffer: &trace_buffer, value: 10_u8);
          } else {
            put_byte(buffer: &trace_buffer, value: 32_u8);
          }
        }
        let trace_written = flush(factory: files, output: out, buffer: &trace_buffer);''')
