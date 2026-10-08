"""Disable Q139 record collection for the hosted full-build cost control.

Called only in the temporary q139-full-cost workflow's detached copy. The
normal numerical height resolver is retained. This control is never used
for edits or admission; exact full dumps must match the unmodified source.
Record fields remain allocated, so this isolates collection/checking work,
not the record representation's empty-state memory cost.
"""
from pathlib import Path


def replace_body(source, name, body):
    start = source.index('fn ' + name + '(')
    brace = source.index(' {\n', start)
    next_function = source.find('\nfn ', brace)
    end = len(source) if next_function < 0 else next_function
    suffix = '\n' if next_function < 0 else '\n'
    return source[:brace + 3] + body.rstrip() + '\n}' + suffix + source[end:]


path = Path('renderer/layout/height_basis.wf')
source = path.read_text()
source = replace_body(source, 'resolve_height_proof', '''  let content = definite_block_height(styles: styles, style: style, basis_width: width, basis_height: height);
  if forced >= 0_i32 {
    let border = border_edges(styles: styles, style: style);
    let padding = padding_edges(styles: styles, style: style, basis: width);
    let borders = vertical(edges: border);
    let paddings = vertical(edges: padding);
    let frame = borders +sat paddings;
    let inner = forced -sat frame;
    set content = imax(inner, 0_i32);
  }
  let made = absent_height_proof();
  set made.content_height = content;
  return made;''')
source = replace_body(source, 'containing_height_proof', '  return absent_height_proof();')
source = replace_body(source, 'fresh_containing_proof', '  return absent_height_proof();')
source = replace_body(source, 'keep_height_proof', '  return True();')
for name in ('height_proof_summary', 'context_height_summary', 'retained_height_summary', 'child_height_summaries'):
    source = replace_body(source, name, '  return empty_height_summary();')
for name in ('context_height_current', 'height_proof_current'):
    source = replace_body(source, name, '  return True();')
for name in ('set_height_input', 'layout_height_inputs', 'refresh_context_height_proof', 'refresh_height_summary'):
    source = replace_body(source, name, '  return unit;')
path.write_text(source)
print('Full-build-only control: numerical height resolution retained; collection disabled; record storage retained')
