"""Temporary hosted-CI diagnosis; no renderer fix or timing measurements."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request

from fontTools.ttLib import TTFont, TTCollection

results = Path('results')
text = Path('Makefile').read_text()
section = text.split('SYSTEM_FONTS := ', 1)[1].split('\n# FONT_ROOT', 1)[0]
paths = re.findall(r'/usr/share/fonts/[^\s\\]+', section)
assert len(paths) == 47
changed = []
for index, name in enumerate(paths):
    digests = []
    for version in ('24.04', '26.04'):
        source = Path('build/fontsets') / version / 'root' / name.lstrip('/')
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        digests.append(digest)
        kind = subprocess.check_output(['file', '-b', str(source)], text=True).strip()
        line = f'FILE {version} face={index} path={name} size={len(data)} sha256={digest} symlink={source.is_symlink()} type={kind}'
        print(line, flush=True)
        with (results / 'inventory.txt').open('a') as out:
            out.write(line + '\n')
    if digests[0] != digests[1]:
        changed.append({'index': index, 'path': name})
(results / 'changed.json').write_text(json.dumps(changed, indent=2))

page = Path('build/research/concurrency/html5.html')
page.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve('https://raw.githubusercontent.com/WebKit/WebKit/e9f2cf896959ec35ce49b0458b2b1bcfbd301e86/PerformanceTests/Parser/resources/html5.html', page)
assert hashlib.sha256(page.read_bytes()).hexdigest() == 'f0466f5a8c8099935a9394607abcd4bbbb3b41384a14b3f906eea80a521fe06e'

def fonts(version):
    subprocess.run(['make', '-s', 'oracle-fonts', f'FONT_ROOT={Path("build/fontsets") / version / "root"}'], check=True)

def run(label, command):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (results / f'{label}.stdout').write_text(result.stdout)
    (results / f'{label}.stderr').write_text(result.stderr)
    print(f'RESULT {label} exit={result.returncode}', flush=True)
    for line in result.stderr.splitlines():
        print(f'STDERR {label} {line}', flush=True)
    return result

for version in ('26.04', '24.04'):
    fonts(version)
    result = run(f'prepare-{version}', ['sh', 'research/investigations/incremental-layout/run.sh', 'prepare', 'html5'])
    if version == '26.04':
        assert result.returncode == 2 and 'failed: fonts' in result.stderr
    else:
        assert result.returncode == 0

# Diagnostic only: preserve Refused/Unreadable and the face number at the
# driver's existing failure report; no acceptance path changes.
driver = Path('renderer/oracle/layout/layout.wf')
source = driver.read_text()
old = '''    Err(..) => {
      let code = fail(err: err, files: files, what: &fonts_word[0_u64..fonts_word.len]);
      return code;
    }
  };
  let viewport'''
new = '''    Err(error: problem) => {
      let diagnostic = box_slots_new::<u8>(capacity: 128_u64);
      put_text(buffer: &diagnostic, text: &fonts_word[0_u64..fonts_word.len]);
      match problem {
        Refused(face: face) => {
          let label: Array<u8, 14> = " Refused face=";
          put_text(buffer: &diagnostic, text: &label[0_u64..label.len]);
          put_decimal(buffer: &diagnostic, value: face);
        }
        Unreadable(face: face) => {
          let label: Array<u8, 17> = " Unreadable face=";
          put_text(buffer: &diagnostic, text: &label[0_u64..label.len]);
          put_decimal(buffer: &diagnostic, value: face);
        }
      }
      let size = diagnostic.inner.len;
      let code = fail(err: err, files: files, what: &diagnostic.inner[0_u64..size]);
      return code;
    }
  };
  let viewport'''
assert source.count(old) == 1
driver.write_text(source.replace(old, new))
(results / 'diagnostic.patch').write_text(subprocess.check_output(['git', 'diff', '--', str(driver)], text=True))
wfc = next(Path('build/whitefoot').glob('*/whitefootc')).resolve()
subprocess.run([str(wfc), '--cache', str(Path('build/wf-cache').resolve()), '--fragments', 'function', '--graph', 'modules.wfg', '--entry', 'layout_oracle', '-o', '../build/layout_oracle_seq'], cwd='renderer', check=True)
fonts('26.04')
run('diagnostic-26.04', ['sh', 'research/investigations/incremental-layout/run.sh', 'prepare', 'html5'])

# One small page is enough to load every face without repeating full layout.
probe = Path('build/font-probe.html')
probe.write_text('<!doctype html><p>Font probe ABC 123</p>')
command = ['build/layout_oracle_seq', 'dump', '1', str(probe), 'renderer/style/ua.css']
fonts('24.04')
assert run('probe-control', command).returncode == 0
offenders = []
for face in changed:
    name = face['path']
    basename = Path(name).name
    target = Path('build/fonts') / basename
    shutil.copyfile(Path('build/fontsets/26.04/root') / name.lstrip('/'), target)
    result = run(f'swap-{face["index"]}-{basename}', command)
    if result.returncode:
        offenders.append(face)
    shutil.copyfile(Path('build/fontsets/24.04/root') / name.lstrip('/'), target)
(results / 'offenders.json').write_text(json.dumps(offenders, indent=2))
print(f'OFFENDERS {json.dumps(offenders)}', flush=True)

for face in changed:
    for version in ('24.04', '26.04'):
        source = Path('build/fontsets') / version / 'root' / face['path'].lstrip('/')
        font = TTFont(source, checkChecksums=2) if source.read_bytes()[:4] != b'ttcf' else TTCollection(source).fonts[0]
        font.ensureDecompiled()
        print(f'FONTTOOLS {version} {source.name} decompiled=all tables={sorted(font.keys())}', flush=True)
        for tag in ('head', 'maxp', 'hhea', 'OS/2', 'cmap', 'fvar', 'CFF2'):
            if tag in font:
                table = font[tag]
                detail = {key: getattr(table, key) for key in ('tableVersion', 'version', 'unitsPerEm', 'numGlyphs', 'numberOfHMetrics') if hasattr(table, key)}
                if tag == 'cmap':
                    detail['subtables'] = [(t.platformID, t.platEncID, t.format, len(getattr(t, 'cmap', {}))) for t in table.tables]
                print(f'TABLE {version} {source.name} {tag} {detail}', flush=True)
        font.saveXML(results / f'{version}-{source.name}.ttx', tables=['head', 'maxp', 'hhea', 'OS/2', 'cmap'])
