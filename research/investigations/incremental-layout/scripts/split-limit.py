"""Generate split-line saturation probes; run only with CI-built oracle drivers.

Usage: split-limit.py DRIVER OUTPUT_DIR [--detect-omission]
The optional mode requires an actual high-origin mismatch while checking the
complete driver protocol and unchanged low-origin controls. CI runs the same
inputs on unmodified sequential/parallel drivers before omitting the numeric
suffix admission. The generated pages and logs stay in OUTPUT_DIR; case pages stay
unchanged. The standard library has no driver-node parser, so this reuses Tree.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

import inctime
from edits import Tree

TEMPLATE = """<!doctype html><style>
html,body{margin:0;padding:0}body{font:16px/20px monospace}
section{display:flow-root;width:240px;padding-top:ORIGINpx}
p{margin:0;width:80px}.wrapper{padding-top:1px}
.head{margin-top:40px;margin-bottom:0;DISPLAY}
</style><section><p>Probe.ATOMIC</p><div class="wrapper"><span><div class="head">Head.</div></span></div></section>
"""


def run(driver, directory, detect):
    directory.mkdir(parents=True, exist_ok=True)
    differences = []
    heads = [('open', '', ''), ('child', 'display:flow-root', ''),
             ('open-atomic', '', '<i style="display:inline-block;width:1px;height:1px"></i>'),
             ('child-atomic', 'display:flow-root', '<i style="display:inline-block;width:1px;height:1px"></i>')]
    for origin_name, origin in [('low', '40'), ('high', '33554360')]:
        for head_name, display, atomic in heads:
            name = origin_name + '-' + head_name
            page = directory / (name + '.html')
            page.write_text(TEMPLATE.replace('ORIGIN', origin).replace('DISPLAY', display).replace('ATOMIC', atomic))
            nodes = directory / (name + '.nodes')
            nodes.write_text(subprocess.check_output([driver, 'nodes', '0', str(page), 'renderer/style/ua.css'], text=True))
            tree = Tree(nodes)
            node = next(text['node'] for text in tree.texts if text['data'] == b'Probe.')
            script = directory / (name + '.edits')
            script.write_text(f'T {node} 0 More \nD {node} 0 5\n')
            rawfile = directory / (name + '.raw')
            before = time.monotonic()
            raw = subprocess.check_output([driver, 'edit', str(script), str(page), 'renderer/style/ua.css'], text=True)
            elapsed = time.monotonic() - before
            rawfile.write_text(raw)
            operations = inctime.script_operations(str(script))
            if not detect:
                dump = subprocess.check_output([driver, 'dump', '1', str(page), 'renderer/style/ua.css'], text=True)
                (directory / (name + '.dump')).write_text(dump)
                timedfile = directory / (name + '.timed')
                timed = subprocess.check_output([driver, 'incremental', str(script), str(page), 'renderer/style/ua.css'], text=True)
                timedfile.write_text(timed)
                inctime.read(str(timedfile), operations)
                for row in timed.splitlines():
                    if row.startswith('edit '):
                        print(name, row, flush=True)
            different = re.findall(r'^edit (\d+) hash [0-9a-f]{16} bytes \d+ inc DIFF$', raw, re.M)
            if detect and different and origin_name == 'high':
                # This copy checks completeness and protocol, not identity.
                protocol = directory / (name + '.protocol')
                protocol.write_text(raw.replace(' inc DIFF\n', ' inc same\n'))
                inctime.read(str(protocol), operations, checking=True)
                differences.append(name)
            else:
                try:
                    inctime.read(str(rawfile), operations, checking=True)
                except ValueError:
                    debug = directory / (name + '.debug.edits')
                    debug.write_text('P 1\nP 2\n' + script.read_text())
                    with (directory / (name + '.debug.raw')).open('w') as output, (directory / (name + '.debug.err')).open('w') as error:
                        result = subprocess.run([driver, 'edit', str(debug), str(page), 'renderer/style/ua.css'], stdout=output, stderr=error)
                    (directory / (name + '.debug.status')).write_text(str(result.returncode) + '\n')
                    raise
            print(name, 'seconds', round(elapsed, 3), 'different edits', different, flush=True)
    if detect:
        if not differences:
            raise AssertionError('omitted numeric suffix admission produced no high-origin difference')
        print('detected numeric suffix-admission omission:', ', '.join(differences))


if __name__ == '__main__':
    run(sys.argv[1], Path(sys.argv[2]), '--detect-omission' in sys.argv[3:])
