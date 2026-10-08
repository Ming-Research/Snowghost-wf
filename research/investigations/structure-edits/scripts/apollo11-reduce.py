"""Temporary hosted fixture search; removed after retaining the minimal case."""
from pathlib import Path
import subprocess
import time

out = Path('build/apollo-fix')
out.mkdir(exist_ok=True)
html = out / 'sentence-convergence-case.html'
edits = out / 'sentence-convergence-case.edits'
# The first paragraph grows; the later nested paragraph crosses a stationary
# float bottom and loses the same line, restoring the previous cursor.
for height in (60, 80, 100, 120, 140, 160):
    for words in (6, 10, 14, 18, 22, 26, 30):
        html.write_text('<!doctype html><style>body{margin:0;width:400px;font:20px/20px monospace}p{margin:0}.float{float:right;width:200px;height:' + str(height) + 'px}</style><div class="float"></div><p>START words words</p><section><p>' + 'words ' * words + '</p><p>END</p></section>')
        nodes = subprocess.check_output(['build/layout_oracle_seq', 'nodes', str(html), 'renderer/style/ua.css'], text=True)
        target = next(line.split()[1] for line in nodes.splitlines() if line.startswith('T ') and 'START' in line)
        edits.write_text(f'T {target} 0 added words words words \nD {target} 0 24\n')
        started = time.monotonic()
        raw = subprocess.check_output(['build/layout_oracle_seq', 'edit', str(edits), str(html), 'renderer/style/ua.css'], text=True)
        print(height, words, round(time.monotonic()-started, 3), raw, flush=True)
        if 'inc DIFF' in raw:
            (out / 'reduced.raw').write_text(raw)
            raise SystemExit(0)
raise SystemExit('No failing candidate on this revision')
