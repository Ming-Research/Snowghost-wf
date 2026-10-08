#!/usr/bin/env python3
"""CI-only Q138 frame/frontier diagnostic injection; remove after evidence.

Run from a disposable Snowghost checkout before its hosted oracle build.
This adds no retained renderer state and changes no layout admission.
Instrumented elapsed times are not performance evidence.
"""

from pathlib import Path


def function_text(source, name):
    start = source.index("fn " + name + "(")
    end = source.find("\nfn ", start + 1)
    return source[start:] if end < 0 else source[start:end]


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise SystemExit("Injection anchor absent or ambiguous: " + old[:100])
    return source.replace(old, new, 1)


root = Path.cwd()
module_path = root / "renderer/layout/module.wfm"
edit_path = root / "renderer/oracle/layout/edit.wf"
probe_path = root / "renderer/layout/root_probe.wf"
support = (root / "renderer/oracle/support/support.wf").read_text()
oracle = (root / "renderer/oracle/layout/layout.wf").read_text()
module = module_path.read_text()
edit = edit_path.read_text()
if probe_path.exists() or "public fn flow_probe(" in module:
    raise SystemExit("Probe already injected")

# Reuse project formatters without making layout depend on oracle modules.
formatters = "\n".join([
    function_text(support, "put_text"),
    function_text(support, "put_decimal"),
    function_text(oracle, "put_signed"),
])
for old, new in [
    ("put_text", "root_probe_text"),
    ("put_decimal", "root_probe_decimal"),
    ("put_signed", "root_probe_signed"),
    ("put_byte", "root_probe_byte"),
    ("decimal_glyphs", "root_probe_digits"),
]:
    formatters = formatters.replace(old, new)

helpers = '''const root_probe_digits: Array<u8, 10> = "0123456789";

fn root_probe_byte(buffer: &Box<Slots<u8>>, value: u8) -> result: unit writes(buffer) {
  doc "Appends one diagnostic byte using layout's existing bounded owned buffer growth.";
  let appended = push_item::<u8>(cell: buffer, value: value, ceiling: item_ceiling);
  return unit;
}

fn root_probe_u64(buffer: &Box<Slots<u8>>, value: u64) -> result: unit writes(buffer) {
  doc "Appends a space and one unsigned diagnostic field.";
  root_probe_byte(buffer: buffer, value: 32_u8);
  root_probe_decimal(buffer: buffer, value: value);
  return unit;
}

fn root_probe_u32(buffer: &Box<Slots<u8>>, value: u32) -> result: unit writes(buffer) {
  doc "Widens and appends one unsigned diagnostic field.";
  let wide = cvt::<u32, u64>(value);
  root_probe_u64(buffer: buffer, value: wide);
  return unit;
}

fn root_probe_u8(buffer: &Box<Slots<u8>>, value: u8) -> result: unit writes(buffer) {
  doc "Widens and appends one byte diagnostic field.";
  let wide = cvt::<u8, u64>(value);
  root_probe_u64(buffer: buffer, value: wide);
  return unit;
}

fn root_probe_i32(buffer: &Box<Slots<u8>>, value: i32) -> result: unit writes(buffer) {
  doc "Widens and appends one signed layout-unit field.";
  let wide = cvt::<i32, i64>(value);
  root_probe_byte(buffer: buffer, value: 32_u8);
  root_probe_signed(buffer: buffer, value: wide);
  return unit;
}

fn root_probe_bool(buffer: &Box<Slots<u8>>, value: Bool) -> result: unit writes(buffer) {
  doc "Appends a Boolean diagnostic field as zero or one.";
  let number = if value {
    give 1_u64;
  } else {
    give 0_u64;
  }
  root_probe_u64(buffer: buffer, value: number);
  return unit;
}
'''

fields = [
    ("edit", "u64", "edit"),
    ("phase", "u8", "phase"),
    ("parent", "u32", "parent"),
    ("slot", "u32", "context^.slot"),
    ("kind", "u8", "context^.kind"),
    ("element", "u32", "context^.style.element"),
    ("pseudo", "u32", "context^.style.pseudo"),
    ("anonymous", "bool", "context^.style.anonymous"),
    ("events", "u64", "events"),
]
for name in ["width", "height", "baseline", "content_raw", "flow_end"]:
    fields.append((name, "i32", "context^." + name))
fields.append(("has_baseline", "bool", "context^.has_baseline"))
for name in ["margin_top", "margin_right", "margin_bottom", "margin_left"]:
    fields.append((name, "i32", "context^." + name))
for space in ["space", "laid"]:
    for name in ["available", "basis_width", "basis_height", "forced_width", "forced_height"]:
        fields.append((space + "_" + name, "i32", "context^." + space + "." + name))
    fields.append((space + "_shrink", "bool", "context^." + space + ".shrink"))
fields.append(("frame_valid", "bool", "frame_valid"))
for name in ["content_left", "content_top", "flow_width", "definite"]:
    fields.append(("frame_" + name, "i32", "frame." + name))
fields.append(("frame_columned", "bool", "frame.columned"))
for name in ["column_count", "column_width", "column_gap"]:
    fields.append(("frame_" + name, "i32", "frame." + name))
for name in ["dirty", "restyled"]:
    fields.append((name, "bool", "context^." + name))
for name in ["restyled_blocks", "restyled_block", "marked_paragraphs", "marked_paragraph", "marked_children", "marked_child"]:
    fields.append((name, "u32", "context^." + name))
for name in ["intrinsic_known", "intrinsic_held"]:
    fields.append((name, "bool", "context^." + name))
for name in ["intrinsic_basis", "min_content", "max_content", "held_min", "held_max"]:
    fields.append((name, "i32", "context^." + name))
for name in ["definite_free", "flow_definite_free", "has_out", "boundary_dirty", "reference_dense"]:
    fields.append((name, "bool", "context^." + name))

schema = "flow_probe_schema " + " ".join(name for name, _, _ in fields) + "\n"
schema_literal = schema.replace("\n", "\\n")
constants = (
    'alias Styles = pkg::style::Styles;\n\n'
    f'const root_probe_schema: Array<u8, {len(schema)}> = "{schema_literal}";\n\n'
    'const root_probe_record: Array<u8, 10> = "flow_probe";\n\n'
)

body = '''fn root_probe_context(context: &Context, styles: &Styles, buffer: &Box<Slots<u8>>, parent: u32, phase: u8, edit: u64) -> result: unit reads(context), reads(styles), writes(buffer) {
  doc "Emits a generic live context snapshot; frames are effective flow inputs only when frame_valid is one. Phase zero precedes restyle, one follows marking at retained dimensions, and two follows completed update. No layout field is changed.";
  if context^.retired {
    return unit;
  }
  let events = flow_length(context: context);
  let frame_valid = context^.kind == ctx_flow;
  let frame = flow_frame(styles: styles, style: context^.style, space: context^.space, width: context^.width);
  root_probe_text(buffer: buffer, text: &root_probe_record[0_u64..root_probe_record.len]);
'''
for _, kind, expression in fields:
    body += f"  root_probe_{kind}(buffer: buffer, value: {expression});\n"
body += '''  root_probe_byte(buffer: buffer, value: 10_u8);
  let count = context^.children.inner.len;
  for (at in 0_u64..count) {
    root_probe_context(context: &context^.children.inner[at], styles: styles, buffer: buffer, parent: context^.slot, phase: phase, edit: edit);
  }
  return unit;
}

fn flow_probe(layout: &Layout, styles: &Styles, buffer: &Box<Slots<u8>>, phase: u8, edit: u64) -> result: unit reads(layout), reads(styles), writes(buffer) {
  doc "Appends a schema and all live context frame/frontier records for the temporary hosted diagnostic. Diagnostic elapsed times are not performance evidence.";
  root_probe_text(buffer: buffer, text: &root_probe_schema[0_u64..root_probe_schema.len]);
  root_probe_context(context: &layout^.root, styles: styles, buffer: buffer, parent: no_index, phase: phase, edit: edit);
  return unit;
}
'''

declaration = '\npublic fn flow_probe(layout: &Layout, styles: &Styles, buffer: &Box<Slots<u8>>, phase: u8, edit: u64) -> result: unit reads(layout), reads(styles), writes(buffer) doc "Temporary hosted-only read-only frame/frontier diagnostic: phase zero before restyle, one after marks at retained dimensions, two after update; appends a schema and all live contexts. No persistence or layout admission is changed.";\n'
module += declaration
edit = 'alias flow_probe = pkg::layout::flow_probe;\n' + edit
apply_source = function_text(edit, "apply_style_incremental")
apply_new = replace_once(
    apply_source,
    "  let style_started = now(clock: clock);",
    "  flow_probe(layout: &kept^.layout, styles: &kept^.state.styles, buffer: report, phase: 0_u8, edit: number);\n  let style_started = now(clock: clock);",
)
apply_new = replace_once(
    apply_new,
    "  let finished_update = propagate finish_style_edit(",
    "  flow_probe(layout: &kept^.layout, styles: &kept^.state.styles, buffer: report, phase: 1_u8, edit: number);\n  let finished_update = propagate finish_style_edit(",
)
edit = replace_once(edit, apply_source, apply_new)
finish_source = function_text(edit, "finish_style_edit")
finish_new = replace_once(
    finish_source,
    "  let finished = stamp(clock: clock, witness: &kept^.layout);",
    "  let finished = stamp(clock: clock, witness: &kept^.layout);\n  flow_probe(layout: &kept^.layout, styles: &kept^.state.styles, buffer: report, phase: 2_u8, edit: number);",
)
edit = replace_once(edit, finish_source, finish_new)

probe_path.write_text(constants + helpers + "\n" + formatters + "\n" + body)
module_path.write_text(module)
edit_path.write_text(edit)
print("Injected temporary all-context flow_probe; no module graph or retained layout state changed")
