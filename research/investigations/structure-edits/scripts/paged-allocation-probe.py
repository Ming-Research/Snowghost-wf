"""Inject a CI-only census into a detached base tree and create allocation IR probes.

The layout-check workflow consumes this experiment's diagnostic; remove with the
Paged experiment. Production sources and helper callers are not instrumented.
"""
import re
import sys
from pathlib import Path

if sys.argv[1] == '--summarize':
    from collections import Counter
    evidence = Path(sys.argv[2])
    lines = (evidence / 'allocation-html5.txt').read_text().splitlines()
    assert lines[-1].startswith('layout elements '), 'missing completed-build row'
    rows = [tuple(map(int, line.split())) for line in lines[:-1]]
    assert all(len(row) == 4 and 0 <= row[0] < 7 for row in rows)
    names = ['SequenceNode', 'Flow', 'TextUnit', 'StyleUse', 'StyleRoute', 'u32', 'ContextPath']
    assert {row[0] for row in rows} == set(range(7)), 'missing store type'
    assert [(r[2], r[3]) for r in rows if r[0] == 0] == [(r[2], r[3]) for r in rows if r[0] == 1]
    print('Measured base stores (one proposed Paged per store):', len(rows))
    for kind, name in enumerate(names):
        ir = (evidence / 'allocation-base' / (name + '.wf.ll')).read_text()
        match = re.search(r'page.size:\n.*?@llvm.umul.with.overflow.i64\(i64 (\d+), i64 (\d+)\)', ir, re.S)
        assert match, name
        native, stride = map(int, match.groups())
        selected = [r for r in rows if r[0] == kind]
        assert all(r[1] == native for r in selected), (name, 'runtime/IR geometry mismatch')
        first_cells = sum(r[2] for r in selected)
        capacities = [r[2] + (r[3] - 1) * 64 for r in selected]
        native_pages = sum((c + native - 1) // native for c in capacities)
        print(name, 'stores', len(selected), 'B', native, 'stride', stride,
              'native_first_bytes', len(selected) * native * stride,
              'base_first_data_bytes', first_cells * stride,
              'native_all_page_bytes', native_pages * native * stride,
              'base_all_page_data_bytes', sum(capacities) * stride,
              'base_first_width_histogram', dict(sorted(Counter(r[2] for r in selected).items())))
    sys.exit(0)

root = Path(sys.argv[1])
layout = root / 'renderer/layout'
module = (layout / 'module.wfm').read_text()
types = ['SequenceNode', 'Flow', 'TextUnit', 'StyleUse', 'StyleRoute', 'u32', 'ContextPath']
source = '''fn allocation_store<T>(pages: &SlotPages<T>, kind: u64, output: &Box<Slots<u64>>) -> result: unit reads(pages), writes(output) {
  doc "Records each nonempty base store's type, native page length and old first width.";
  match pages^ {
    Vacant() => {
    }
    Pages(first: width, directory: pointers) => {
      let native = paged_page_len::<T>();
      let first = cvt::<u32, u64>(width^);
      let a = push_item::<u64>(cell: output, value: kind, ceiling: 1073741824_u64);
      let b = push_item::<u64>(cell: output, value: native, ceiling: 1073741824_u64);
      let c = push_item::<u64>(cell: output, value: first, ceiling: 1073741824_u64);
      let d = push_item::<u64>(cell: output, value: pointers^.inner.len, ceiling: 1073741824_u64);
    }
  }
  return unit;
}

fn allocation_sequence(sequence: &EntrySequence, output: &Box<Slots<u64>>) -> result: unit reads(sequence), writes(output) {
  doc "Records the two independent stores belonging to one owner.";
  allocation_store::<SequenceNode>(pages: &sequence^.nodes, kind: 0_u64, output: output);
  allocation_store::<Flow>(pages: &sequence^.payloads, kind: 1_u64, output: output);
  return unit;
}

fn allocation_context(context: &Context, output: &Box<Slots<u64>>) -> result: unit reads(context), writes(output) {
  doc "Visits the retained owned tree once for allocation accounting only.";
  allocation_sequence(sequence: &context^.entries, output: output);
  for (at in 0_u64..context^.blocks.inner.len) {
    allocation_sequence(sequence: &context^.blocks.inner[at].entries, output: output);
  }
  for (child in 0_u64..context^.children.inner.len) {
    allocation_context(context: &context^.children.inner[child], output: output);
  }
  return unit;
}

fn allocation_census(layout: &Layout) -> result: Box<Slots<u64>> reads(layout) {
  doc "Returns CI-only allocation rows after a complete build of the base tree.";
  let output = box_slots_new::<u64>(capacity: 0_u64);
  allocation_context(context: &layout^.root, output: &output);
'''
for kind, (typ, field) in enumerate(zip(types[2:], ['text_units', 'uses', 'routes', 'context_of', 'paths']), 2):
    source += f'  allocation_store::<{typ}>(pages: &layout^.{field}.pages, kind: {kind}_u64, output: &output);\n'
source += '  return move output;\n}\n'
(layout / 'allocation_probe.wf').write_text(source)
(layout / 'module.wfm').write_text(module + '\npublic fn allocation_census(layout: &Layout) -> result: Box<Slots<u64>> reads(layout) doc "Returns CI-only allocation rows.";\n')
p=root / 'renderer/oracle/layout/layout.wf'
s=p.read_text(); anchor='    let (counted_contexts, counted_paragraphs) = layout_counts(layout: &layout);'
assert s.count(anchor) == 1
s=s.replace(anchor, '''    let census = pkg::layout::allocation_census(layout: &layout);
    let census_buffer = box_slots_new::<u8>(capacity: 256_u64);
    for (cell in 0_u64..census.inner.len) {
      put_decimal(buffer: &census_buffer, value: census.inner[cell]);
      let column = cell % 4_u64;
      if column == 3_u64 {
        put_byte(buffer: &census_buffer, value: 10_u8);
      } else {
        put_byte(buffer: &census_buffer, value: 32_u8);
      }
    }
    let census_written = flush(factory: files, output: out, buffer: &census_buffer);
''' + anchor)
p.write_text(s)
# The exact declarations, not a handwritten ABI estimate, determine allocations.
declarations = []
for typ in ['EntryHandle', 'SequenceOutput', 'SequenceCursor'] + [t for t in types if t != 'u32']:
    match = re.search(r'^(?:struct|enum) ' + typ + r' \{.*?^\}', module, re.M | re.S)
    assert match, typ
    declarations.append(match.group())
def zero_value(typ, statements):
    if typ in ('u32', 'u64', 'i32', 'i64'):
        return '0_' + typ
    if typ == 'Bool':
        expression = 'False()'
    else:
        declaration = next(d for d in declarations if re.match(r'(struct|enum) ' + typ + r' \{', d))
        if declaration.startswith('enum '):
            variant = re.search(r'^  (\w+)\((.*?)\);', declaration, re.M)
            assert variant, typ
            fields = re.findall(r'(\w+): (\w+)', variant.group(2))
            constructor = typ + '::' + variant.group(1)
        else:
            fields = re.findall(r'^  (\w+): (\w+);', declaration, re.M)
            constructor = typ
        operands = [name + ': ' + zero_value(field_type, statements) for name, field_type in fields]
        expression = constructor + '(' + ', '.join(operands) + ')'
    name = 'zero_' + str(len(statements))
    statements.append('  let ' + name + ' = ' + expression + ';')
    return name

for typ in types:
    statements = []
    value = zero_value(typ, statements)
    initializers = ''.join(line + '\n' for line in statements)
    probe='\n\n'.join(declarations) + f'''

fn main() -> result: unit pure {{
  doc "Exposes this element type's actual native page allocation in compiler IR.";
  let storage = box_paged_new::<{typ}>(capacity: 1_u64);
{initializers}  let baseline = box_array_filled::<{typ}>(count: 4_u64, value: {value});
  return unit;
}}
'''
    (root / f'{typ}.wf').write_text(probe)
