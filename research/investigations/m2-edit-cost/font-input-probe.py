"""Temporary hosted-only input trace; remove after its workflow evidence is recorded.

The trace writes only diagnostic buffers owned by each context. It changes no
layout input, dirty mark, admission or result. Its timings are not cost evidence.
"""
from pathlib import Path


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise SystemExit('Missing or ambiguous trace anchor: ' + old[:100])
    return source.replace(old, new, 1)


def function(source, name):
    start = source.index('fn ' + name + '(')
    end = source.find('\nfn ', start + 1)
    return source[start:] if end < 0 else source[start:end]


module = Path('renderer/layout/module.wfm')
build = Path('renderer/layout/build.wf')
edit = Path('renderer/oracle/layout/edit.wf')
module.write_text(replace_once(module.read_text(), '\n  height_input: HeightInput;', '\n  font_probe: Box<Slots<u8>>;\n  height_input: HeightInput;'))
s = build.read_text()
s = replace_once(s, '  return Context(height_input:', '  let font_probe = box_slots_new::<u8>(capacity: 0_u64);\n  return Context(font_probe: move font_probe, height_input:')
build.write_text(s)

support = Path('renderer/oracle/support/support.wf').read_text()
oracle = Path('renderer/oracle/layout/layout.wf').read_text()
formatters = '\n'.join([function(support, 'put_text'), function(support, 'put_decimal'), function(oracle, 'put_signed')])
for old,new in [('put_text','font_probe_text'),('put_decimal','font_probe_decimal'),('put_signed','font_probe_signed'),('put_byte','font_probe_byte'),('decimal_glyphs','font_probe_digits')]:
    formatters = formatters.replace(old,new)
fields = [('stage','u32','stage'),('slot','u32','context^.slot'),('element','u32','context^.style.element'),('kind','u8','context^.kind'),('events','u64','events')]
for name in ['dirty','restyled','boundary_dirty','intrinsic_known','intrinsic_held','definite_free','has_out','local_geometry','reference_dense']:
    fields.append((name,'bool','context^.'+name))
for name in ['marked_paragraphs','marked_children','restyled_blocks','restyled_block']:
    fields.append((name,'u32','context^.'+name))
for name in ['width','height','content_raw']:
    fields.append((name,'i32','context^.'+name))
fields.append(('saved_valid','bool','context^.flow_inputs.valid'))
fields.append(('saved_width','i32','context^.flow_inputs.width'))
for label,base in [('space','context^.space'),('laid','context^.laid'),('saved_space','context^.flow_inputs.space')]:
    for name in ['available','basis_width','basis_height','forced_width','forced_height']:
        fields.append((label+'_'+name,'i32',base+'.'+name))
    fields.append((label+'_shrink','bool',base+'.shrink'))
for label,base in [('frame','frame'),('saved_frame','context^.flow_inputs.frame')]:
    for name in ['content_left','content_top','flow_width','definite','column_count','column_width','column_gap']:
        fields.append((label+'_'+name,'i32',base+'.'+name))
    fields.append((label+'_columned','bool',base+'.columned'))
schema = 'font_probe_schema '+' '.join(n for n,_,_ in fields)+'\n'
Path('build/font-input-probe/schema.txt').write_text(schema)
body = 'alias Styles = pkg::style::Styles;\n\nconst font_probe_digits: Array<u8, 10> = "0123456789";\n\n'
body += 'const font_probe_label: Array<u8, 10> = "font_probe";\n\n'
body += 'fn font_probe_byte(buffer: &Box<Slots<u8>>, value: u8) -> result: unit writes(buffer) {\n  let appended = push_item::<u8>(cell: buffer, value: value, ceiling: item_ceiling);\n  return unit;\n}\n\n'
for kind in ['u8','u32','u64','i32','bool']:
    typ = 'Bool' if kind == 'bool' else kind
    if kind == 'bool': expr='let wide = if value {\n    give 1_u64;\n  } else {\n    give 0_u64;\n  }'
    elif kind == 'u64': expr='let wide = value;'
    else: expr=f'let wide = cvt::<{kind}, {"i64" if kind == "i32" else "u64"}>(value);'
    formatter = 'signed' if kind == 'i32' else 'decimal'
    body += f'fn font_probe_{kind}(buffer: &Box<Slots<u8>>, value: {typ}) -> result: unit writes(buffer) {{\n  {expr}\n  font_probe_byte(buffer: buffer, value: 32_u8);\n  font_probe_{formatter}(buffer: buffer, value: wide);\n  return unit;\n}}\n\n'
body += 'fn font_probe_record(context: &Context, styles: &Styles, stage: u32) -> result: unit reads(styles), writes(context) {\n  let events = flow_length(context: context);\n  let frame = flow_frame(styles: styles, style: context^.style, space: context^.space, width: context^.width);\n'
# Capture every input before borrowing the separate diagnostic destination.
for name,_,expr in fields: body += f'  let saved_{name} = {expr};\n'
body += '  font_probe_text(buffer: &context^.font_probe, text: &font_probe_label[0_u64..font_probe_label.len]);\n'
for name,kind,_ in fields: body += f'  font_probe_{kind}(buffer: &context^.font_probe, value: saved_{name});\n'
body += '  font_probe_byte(buffer: &context^.font_probe, value: 10_u8);\n  return unit;\n}\n\n'
body += '''fn font_probe_drain_context(context: &Context, buffer: &Box<Slots<u8>>) -> result: unit writes(context), writes(buffer) {
  let count = context^.font_probe.inner.len;
  font_probe_text(buffer: buffer, text: &context^.font_probe.inner[0_u64..count]);
  truncate(cell: &context^.font_probe, length: 0_u64);
  let children = context^.children.inner.len;
  for (at in 0_u64..children) {
    font_probe_drain_context(context: &context^.children.inner[at], buffer: buffer);
  }
  return unit;
}

fn font_probe_drain(layout: &Layout, buffer: &Box<Slots<u8>>) -> result: unit writes(layout), writes(buffer) {
  font_probe_drain_context(context: &layout^.root, buffer: buffer);
  return unit;
}
'''
# Layout uses pop-back for bounded owned scratch retirement.
body=body.replace('  truncate(cell: &context^.font_probe, length: 0_u64);','  for (\n    step in 0_u64..count,\n    invariant remaining: context^.font_probe.inner.len == count - step\n  ) {\n    let dropped = take_back(window: &context^.font_probe.inner);\n  }')
Path('renderer/layout/font_probe.wf').write_text(body+'\n'+formatters)
module.write_text(module.read_text()+'\npublic fn font_probe_drain(layout: &Layout, buffer: &Box<Slots<u8>>) -> result: unit writes(layout), writes(buffer) doc "Drains temporary hosted diagnostic buffers without changing any layout field.";\n')
for path,name,stage in [('renderer/layout/update.wf','update_flow_inner',1),('renderer/layout/update.wf','update_flow_reference_full',2),('renderer/layout/reference.wf','full_reference_publication',3)]:
    p=Path(path); s=p.read_text(); old=function(s,name); lines=old.splitlines(keepends=True)
    lines.insert(2,f'  font_probe_record(context: context, styles: styles, stage: {stage}_u32);\n')
    p.write_text(replace_once(s,old,''.join(lines)))
# Observe admission after earlier probes, separately from update entry.
p = Path('renderer/layout/update.wf'); s = p.read_text()
anchor = '    let column_ready = column_replay_ready(context: context, styles: styles, frame: frame, unasked: unasked);'
s = replace_once(s, anchor, '    font_probe_record(context: context, styles: styles, stage: 4_u32);\n' + anchor + '\n    if column_ready {\n      font_probe_record(context: context, styles: styles, stage: 5_u32);\n    }')
p.write_text(s)
# Refusal reasons do not need style inputs, and survive in each context's buffer.
p=Path('renderer/layout/boundary.wf'); s=p.read_text(); old=function(s,'boundary_refusal'); lines=old.splitlines(keepends=True)
lines.insert(2,'  font_probe_text(buffer: &context^.font_probe, text: &font_probe_label[0_u64..font_probe_label.len]);\n  font_probe_u32(buffer: &context^.font_probe, value: reason);\n  font_probe_byte(buffer: &context^.font_probe, value: 10_u8);\n')
# Extend only the diagnostic effect row; existing result and counters stay exact.
new=''.join(lines).replace('writes(context.boundary_visits)', 'writes(context.boundary_visits), writes(context.font_probe)')
p.write_text(replace_once(s,old,new))
s=edit.read_text()
s=replace_once(s,'  let finished = stamp(clock: clock, witness: &kept^.layout);','  let finished = stamp(clock: clock, witness: &kept^.layout);\n  pkg::layout::font_probe_drain(layout: &kept^.layout, buffer: report);')
edit.write_text(s)
