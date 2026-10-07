"""One-use CI instrumentation of cutoff returns; remove after attribution.

The ordinary driver exposes aggregate visits, not each context's cutoff
guard. Native commands cannot add those observations. This script changes
only the diagnostic checkout, tags counter fields and adds a read-only dump.
Its timings and tagged counters are not acceptance measurements.
"""
from pathlib import Path
import re

target = Path('renderer/layout/boundary.wf')
source = target.read_text()
for name, field in [('stationary_child', 'blocks'),
                    ('stationary_paragraph', 'indexes')]:
    start = source.index('fn ' + name + '(')
    end = source.index('\nfn ', start + 1)
    body = source[start:end]
    code = 0

    def tag(match):
        global code
        code += 1
        print(name, code, body[max(0, match.start() - 110):match.end()].strip())
        return (match[1] + 'set context^.boundary_visits.' + field +
                ' = ' + str(code * 1000000) + '_u64;\n' + match[0])

    body = re.sub(r'^( +)return [^\n]+;', tag, body, flags=re.M)
    source = source[:start] + body + source[end:]
target.write_text(source)

Path('renderer/layout/probe_trace.wf').write_text('''fn probe_value(values: &Box<Slots<u64>>, value: u64) -> result: unit writes(values) {
  doc "Appends one diagnostic scalar.";
  let pushed = push_item::<u64>(cell: values, value: value, ceiling: item_ceiling);
  return unit;
}

fn probe_context(context: &Context, values: &Box<Slots<u64>>) -> result: unit reads(context), writes(values) {
  doc "Collects per-context cutoff tags without changing layout.";
  let child_code = context^.boundary_visits.blocks / 1000000_u64;
  let paragraph_code = context^.boundary_visits.indexes / 1000000_u64;
  let child_seen = child_code > 0_u64;
  let paragraph_seen = paragraph_code > 0_u64;
  let seen = bor(child_seen, paragraph_seen);
  if seen {
    let serial = cvt::<u32, u64>(context^.slot);
    let element = cvt::<u32, u64>(context^.style.element);
    let held = if context^.intrinsic_held {
      give 1_u64;
    } else {
      give 0_u64;
    }
    let known = if context^.intrinsic_known {
      give 1_u64;
    } else {
      give 0_u64;
    }
    probe_value(values: values, value: serial);
    probe_value(values: values, value: element);
    probe_value(values: values, value: context^.blocks.inner.len);
    probe_value(values: values, value: context^.paragraphs.inner.len);
    probe_value(values: values, value: child_code);
    probe_value(values: values, value: paragraph_code);
    probe_value(values: values, value: held);
    probe_value(values: values, value: known);
  }
  let children = context^.children.inner.len;
  for (at in 0_u64..children) {
    probe_context(context: &context^.children.inner[at], values: values);
  }
  return unit;
}

fn probe_trace(layout: &Layout) -> made: Box<Slots<u64>> reads(layout) {
  doc "One-use cutoff observations for the diagnostic driver.";
  let values = box_slots_new::<u64>(capacity: 64_u64);
  probe_context(context: &layout^.root, values: &values);
  return move values;
}
''')
module = Path('renderer/layout/module.wfm')
module.write_text(module.read_text() + '\npublic fn probe_trace(layout: &Layout) -> made: Box<Slots<u64>> reads(layout) doc "One-use cutoff diagnostic records.";\n')
oracle = Path('renderer/oracle/layout/edit.wf')
body = oracle.read_text()
start = body.index('fn put_counts(')
end = body.index('\nfn ', start + 1)
counts = body[start:end]
extra = '''  let diagnostics = pkg::layout::probe_trace(layout: layout);
  let rows = diagnostics.inner.len / 8_u64;
  for (row in 0_u64..rows) {
    put_byte(buffer: buffer, value: 10_u8);
    put_text(buffer: buffer, text: &probe_label[0_u64..6_u64]);
    for (field in 0_u64..8_u64) {
      let offset = row *sat 8_u64;
      let at = offset +sat field;
      if at < diagnostics.inner.len {
        put_decimal(buffer: buffer, value: diagnostics.inner[at]);
        put_byte(buffer: buffer, value: 32_u8);
      }
    }
  }
'''
assert counts.count('  return unit;') == 1
counts = counts.replace('  return unit;', extra + '  return unit;')
body = body[:start] + counts + body[end:]
first_function = body.index('fn ')
body = body[:first_function] + 'const probe_label: Array<u8, 6> = "probe ";\n\n' + body[first_function:]
oracle.write_text(body)
