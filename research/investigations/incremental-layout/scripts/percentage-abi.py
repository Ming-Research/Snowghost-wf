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
wanted = ('HeightProof', 'HeightInput', 'HeightSummary', 'SequenceOutput', 'BlockOutput', 'Block', 'Context', 'Before')
selected = [line.split(' = type ')[0] for line in types if any(name in line.split(' = type ')[0] for name in wanted)]
if not selected:
    (args.directory / 'available-types.txt').write_text('\n'.join(types) + '\n')
    raise SystemExit('No named layout types found; inspect available-types.txt instead of guessing sizes')
ir = '\n'.join(headers + types) + '\n'
c = '#include <stdio.h>\n'
for number, name in enumerate(selected):
    ir += f'define i64 @q139_size_{number}() {{\n  %end = getelementptr {name}, ptr null, i64 1\n  %bytes = ptrtoint ptr %end to i64\n  ret i64 %bytes\n}}\n'
    c += f'extern unsigned long long q139_size_{number}(void);\n'
c += 'int main(void) {\n'
for number, name in enumerate(selected):
    c += '  printf("%s\\t%llu\\n", ' + json.dumps(name) + f', q139_size_{number}());\n'
c += '  return 0;\n}\n'
(args.directory / 'sizes.ll').write_text(ir)
(args.directory / 'sizes.c').write_text(c)
program = args.directory / 'sizes'
subprocess.run(['clang', '-O2', str(args.directory / 'sizes.ll'), str(args.directory / 'sizes.c'), '-o', str(program)], check=True)
result = subprocess.run([str(program)], check=True, capture_output=True, text=True)
(args.directory / 'sizes.tsv').write_text(result.stdout)
print(result.stdout, end='')
