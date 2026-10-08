"""Temporary input-only diagnosis, called by apollo11-diag; remove with that workflow."""
from pathlib import Path
import hashlib
import re
import subprocess
import time

work = Path('build/apollo11-ablation')
work.mkdir(exist_ok=True)
original = Path('build/x5/scripts/apollo11-block.edits').read_text()
sample = '\n'.join(original.splitlines()[:2]) + '\n'
args = ['build/research/concurrency/apollo11.html', 'renderer/style/ua.css',
        'wikibase.client.init&only=styles&skin=vector-2022=build/research/concurrency/apollo11-modules.css',
        'modules=site.styles&only=styles&skin=vector-2022=build/research/concurrency/apollo11-site.css']
failed = False


def run(label, css, edits=sample):
    global failed
    path = work / (label + '.edits')
    raw = work / (label + '.raw')
    path.write_text(('S ' + css + '\n' if css else '') + edits)
    started = time.monotonic()
    with raw.open('w') as out:
        driver = subprocess.run(['build/layout_oracle_seq', 'edit', str(path), *args], stdout=out)
    checked = subprocess.run(['python3', 'research/investigations/incremental-layout/scripts/inctime.py', '--check', str(path), str(raw)])
    failed |= driver.returncode != 0 or checked.returncode != 0
    paths = re.findall(r'^structure path (\d+) splice ([01]) reason (\d+)$', raw.read_text(), re.M)
    print(label, 'elapsed_s', round(time.monotonic() - started, 3),
          'driver_exit', driver.returncode, 'identity_exit', checked.returncode,
          'sha256', hashlib.sha256(path.read_bytes()).hexdigest(), paths, flush=True)
    return paths


# Follow-up controls address simultaneous dependencies left by one-at-a-time overrides.
run('baseline', '')
both = 'html,body{height:auto!important}'
grid = 'main#content,.mw-page-container-inner{display:block!important}'
run('both-auto', both)
run('both-auto-html-restore', both + 'html{height:100%!important}')
run('both-auto-body-restore', both + 'body{height:100%!important}')
run('both-auto-grids-block', both + grid)
all_heights = '*{height:auto!important;min-height:0!important;max-height:none!important}'
run('all-heights-auto', all_heights)
run('all-heights-auto-grids-block', all_heights + grid)
run('both-auto-all', both, original)

# Preserve full and incremental dumps of the newly observed sentence failure.
# This is a diagnostic capture of a known failing original workload, not a
# replacement expectation for the unchanged inc-same gate.
sentence = Path('build/x5/scripts/apollo11-sentence.edits').read_text().splitlines()
debug = work / 'sentence-debug.edits'
debug.write_text('P 31\nP 32\n' + '\n'.join(sentence[:32]) + '\n')
with (work / 'sentence-debug.raw').open('w') as out:
    result = subprocess.run(['build/layout_oracle_seq', 'edit', str(debug), *args], stdout=out)
failed |= result.returncode != 0
raise SystemExit(1 if failed else 0)
