"""Read native record byte sizes from the compiler's LLVM types in hosted CI.

The temporary full-cost workflow supplies emitted LLVM. Native clang computes
sizeof through LLVM getelementptr, avoiding a guessed layout from field sums.
The generated inspection executable never links or executes renderer code.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('ir', type=Path)
parser.add_argument('directory', type=Path)
args = parser.parse_args()
args.directory.mkdir(parents=True, exist_ok=True)
source = args.ir.read_text()
headers = [line for line in source.splitlines() if line.startswith(('target datalayout', 'target triple'))]
types = [line for line in source.splitlines() if re.match(r'^%.* = type ', line)]
(args.directory / 'available-types.txt').write_text('\n'.join(types) + '\n')
bodies = dict(line.split(' = type ', 1) for line in types)


def fields(body):
    """Top-level members of an LLVM struct body."""
    body = body.strip()
    body = body[2:-2] if body.startswith('<{') else body[1:-1]
    members, depth, current = [], 0, ''
    for character in body:
        depth += character in '[{<'
        depth -= character in ']}>'
        if character == ',' and depth == 0:
            members.append(current.strip())
            current = ''
        else:
            current += character
    return members + ([current.strip()] if current.strip() else [])


# The compiler names types by hash, so the records are found by their exact
# member sequence from renderer/layout/module.wfm, and their holders (Block,
# Context, SpliceInput) by containing them; an ambiguous match is refused.
style_refs = {name for name, body in bodies.items() if fields(body) == ['i32', 'i32', 'i1']}
proof_tail = ['i32', 'i32', 'i32', 'i8', 'i8', 'i32', 'i32', 'i32', 'i32', 'i8', 'i8', 'i32', 'i32', 'i32', 'i32', 'i32', 'i1']
inputs = [name for name, body in bodies.items() if fields(body) == ['i32', 'i32', 'i32', 'i8', 'i8']]
proofs = [name for name, body in bodies.items() if fields(body)[:1] and fields(body)[0] in style_refs and fields(body)[1:] == proof_tail]
if len(inputs) != 1 or len(proofs) != 1:
    raise SystemExit('expected one HeightInput and one HeightProof layout, found %r and %r' % (inputs, proofs))
labels = {inputs[0]: 'HeightInput', proofs[0]: 'HeightProof'}
for name, body in bodies.items():
    if proofs[0] in fields(body):
        labels[name] = 'holder of HeightProof (%d members)' % len(fields(body))
selected = list(labels)
ir = '\n'.join(headers + types) + '\n'
c = '#include <stdio.h>\n'
for number, name in enumerate(selected):
    ir += f'define i64 @q139_size_{number}() {{\n  %end = getelementptr {name}, ptr null, i64 1\n  %bytes = ptrtoint ptr %end to i64\n  ret i64 %bytes\n}}\n'
    c += f'extern unsigned long long q139_size_{number}(void);\n'
c += 'int main(void) {\n'
for number, name in enumerate(selected):
    c += '  printf("%s\\t%s\\t%llu\\n", ' + json.dumps(labels[name]) + ', ' + json.dumps(name) + f', q139_size_{number}());\n'
c += '  return 0;\n}\n'
(args.directory / 'sizes.ll').write_text(ir)
(args.directory / 'sizes.c').write_text(c)
program = args.directory / 'sizes'
subprocess.run(['clang', '-O2', str(args.directory / 'sizes.ll'), str(args.directory / 'sizes.c'), '-o', str(program)], check=True)
result = subprocess.run([str(program)], check=True, capture_output=True, text=True)
(args.directory / 'sizes.tsv').write_text(result.stdout)
print(result.stdout, end='')
