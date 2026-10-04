#!/usr/bin/env python3
"""Step 4b style identity and three-run timing harness (run.sh style-update).

Requires an existing outer host lock. All input paths passed to Whitefoot
resolve below ROOT and are relative to cwd. Default data: original ecma262/
html5; supplementary Apollo requires explicit inputs. No compilation or
previous-output reuse. The frozen method and build-record schema are in
../DESIGN.md, Maintained style-update measurement.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import io
import tarfile
import tempfile
import copy
import contextlib

CRITERIA = """Step 4b: exact complete identity, one style auxiliary per C/K,
matching seq/par hashes and counts, stable counts across timing runs, zero
colour work counts, and three complete process runs without removed failures.
Criterion 2: each rootfont edit must satisfy independent min(update_us) /
min(full_us) <= 1.2, with both minima selected from the three runs of the
same implementation and execution mode. Preserve every paired ratio and
both selected run IDs. Four workers is primary; sequential is separate.
compute_styles and placement are excluded from update/full timing. This
measurement alone does not certify X5 criteria 3 or 4, structural edits or
the unavailable original Apollo inputs. Supplementary Apollo stays separate.
"""

KINDS = ('colour', 'fontsize', 'rootfont')
COUNT_NAMES = ('prepared', 'contexts', 'paragraphs', 'held_entries', 'entries')
COUNTS = rb' prepared (\d+) contexts (\d+) paragraphs (\d+) held_entries (\d+) entries (\d+)'
BASE = re.compile(rb'base hash ([0-9a-f]{16}) bytes (\d+)')
IDENTITY = re.compile(rb'edit (\d+) hash ([0-9a-f]{16}) bytes (\d+) inc (same|DIFF|refused)')
STYLE_COUNTS = re.compile(rb'style edit (\d+)' + COUNTS)
TIMED = re.compile(rb'edit (\d+) us (\d+)' + COUNTS)
STYLE_TIME = re.compile(rb'style edit (\d+) delta_us (\d+) picks_us (\d+) full_us (\d+)')
ORIGINAL_HASHES = {
    'ecma262.html': 'e2b29c85f37b8ded51873ce385b6573a35cbc26b467c21c14f8184f3bab5aa26',
    'ecma262-ecmarkup.css': '8bef2688107197ac28abe81b62a61100904cec548e223d03a10ac7ea7b6b2fc7',
    'ecma262-print.css': 'e80f1880ab96cb3418cddbcd7a529aa6e474113f4a87c2555d079f84fc09c53f',
    'html5.html': 'f0466f5a8c8099935a9394607abcd4bbbb3b41384a14b3f906eea80a521fe06e',
}


def digest(path):
    hashed = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            hashed.update(chunk)
    return hashed.hexdigest()


def relative(path, root):
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        raise ValueError(f'input must resolve below ROOT: {path}') from None


def mappings(page, directory):
    if page == 'ecma262':
        return [f'assets/css/ecmarkup.css={directory}/ecma262-ecmarkup.css', f'assets/css/print.css={directory}/ecma262-print.css']
    if page == 'apollo11':
        return [f'wikibase.client.init&only=styles&skin=vector-2022={directory}/apollo11-modules.css', f'modules=site.styles&only=styles&skin=vector-2022={directory}/apollo11-site.css']
    return []


def script_errors(path, expected):
    lines = path.read_bytes().splitlines()
    errors = []
    if not lines or not lines[0].startswith(b'S '):
        errors.append('missing initial stylesheet')
    edits = lines[1:]
    if len(edits) != expected or any(not re.fullmatch(rb'[CK] \d+ [^\s]+', line) for line in edits):
        errors.append(f'expected exactly {expected} C/K lines after one initial S line')
    for index in range(0, len(edits) - 1, 2):
        if edits[index][:1] != b'C' or edits[index + 1] != b'K' + edits[index][1:]:
            errors.append(f'edit pair {index + 1}/{index + 2} is not C with its matching K inverse')
    return errors


def parse(raw, expected, phase, colour=False):
    lines, errors, records = raw.splitlines(), [], []
    base = BASE.fullmatch(lines[0]) if lines else None
    if not base or not raw.endswith(b'\n'):
        errors.append('missing/malformed base or final newline')
    if len(lines) != 1 + 2 * expected:
        errors.append(f'{len(lines)} output lines; expected {1 + 2 * expected}')
    for number in range(1, expected + 1):
        pair = lines[1 + 2 * (number - 1):1 + 2 * number]
        if len(pair) != 2:
            errors.append(f'edit {number}: missing primary/auxiliary output')
            continue
        style = (STYLE_COUNTS if phase == 'identity' else STYLE_TIME).fullmatch(pair[0])
        primary = (IDENTITY if phase == 'identity' else TIMED).fullmatch(pair[1])
        if not style or not primary:
            errors.append(f'edit {number}: malformed/refused/DIFF/missing output: {pair!r}')
            continue
        if int(style[1]) != number or int(primary[1]) != number:
            errors.append(f'edit {number}: auxiliary/primary IDs are {style[1]!r}/{primary[1]!r}')
        if phase == 'identity':
            counts = list(map(int, style.groups()[1:]))
            status = primary[4].decode()
            if status != 'same':
                errors.append(f'edit {number}: inc {status}')
            record = {'edit': number, 'hash': primary[2].decode(), 'bytes': int(primary[3]), 'status': status, 'counts': counts}
        else:
            counts = list(map(int, primary.groups()[2:]))
            update, delta, picks, full = int(primary[2]), int(style[2]), int(style[3]), int(style[4])
            if full == 0:
                errors.append(f'edit {number}: zero full_us cannot support a ratio')
            if delta + picks > update:
                errors.append(f'edit {number}: delta_us + picks_us exceeds update_us')
            record = {'edit': number, 'update_us': update, 'delta_us': delta, 'picks_us': picks, 'full_us': full, 'counts': counts,
                      'paired_ratio': update / full if full else None,
                      'paired_within_1_2': update * 5 <= full * 6 if full else False}
        if colour and any(counts):
            errors.append(f'edit {number}: colour work counts must all be zero, got {counts}')
        records.append(record)
    return {'base': {'hash': base[1].decode(), 'bytes': int(base[2])} if base else None, 'records': records, 'errors': errors}


def select_best(runs):
    result = []
    for index in range(len(runs[0])):
        values = [{'run': number + 1, **run[index]} for number, run in enumerate(runs)]
        update = min(values, key=lambda v: v['update_us'])
        full = min(values, key=lambda v: v['full_us'])
        paired = min(values, key=lambda v: v['paired_ratio'])
        result.append({'edit': index + 1, 'all_runs': values,
                       'best_update': update, 'best_full': full,
                       'independent_min_ratio': update['update_us'] / full['full_us'],
                       'independent_min_within_1_2': update['update_us'] * 5 <= full['full_us'] * 6,
                       'minimum_paired_ratio': paired['paired_ratio'], 'minimum_paired_run': paired['run'],
                       'minimum_paired_within_1_2': paired['paired_within_1_2']})
    return result


def git(root, *words):
    completed = subprocess.run(['git', *words], cwd=root, capture_output=True)
    if completed.returncode:
        raise ValueError('git %s: %s' % (' '.join(words), completed.stderr.decode(errors='replace')))
    return completed.stdout


def source_snapshot(root, revision):
    revision = git(root, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    listing = git(root, 'ls-tree', '-r', '-z', revision, '--', 'renderer')
    objects = {}
    for entry in listing.split(b'\0'):
        if entry:
            meta, name = entry.split(b'\t', 1)
            if Path(name.decode()).suffix in ('.wf', '.wfm', '.wfg'):
                mode, kind, object_id = meta.split()
                if kind != b'blob' or mode not in (b'100644', b'100755'):
                    raise ValueError('compile source is not a regular git blob: ' + name.decode())
                objects[name.decode()] = object_id.decode()
    archive = git(root, 'archive', revision, 'renderer')
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        files = {}
        for item in stream.getmembers():
            if item.isfile() and item.name in objects:
                data = stream.extractfile(item).read()
                git_hash = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                if git_hash != objects[item.name]:
                    raise ValueError('archive changed a source blob: ' + item.name)
                files[item.name] = hashlib.sha256(data).hexdigest()
    if set(files) != set(objects):
        raise ValueError('archive omitted compile source files')
    if 'renderer/modules.wfg' not in files:
        raise ValueError('source revision lacks renderer/modules.wfg: ' + revision)
    pin = git(root, 'ls-tree', revision, 'whitefoot').decode().split()
    if len(pin) < 3 or pin[0:2] != ['160000', 'commit']:
        raise ValueError('source revision lacks a Whitefoot gitlink')
    return {'revision': revision, 'files': files, 'whitefoot_revision': pin[2],
            'fingerprint': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def verify_build(record, binary, snapshot, mode, root):
    """Validate recorded association; hashes alone do not prove compilation."""
    if record['source_revision'] != snapshot['revision'] or record['source_files'] != snapshot['files']:
        raise ValueError('build source revision or complete source snapshot differs')
    if (root / record['binary']).resolve() != binary or record['binary_sha256'] != digest(binary):
        raise ValueError('build record binary path/hash differs')
    compiler = record['compiler']
    if compiler['revision'] != snapshot['whitefoot_revision']:
        raise ValueError('build compiler pin differs from source gitlink')
    compiler_path = Path(compiler['path'])
    if not compiler_path.is_absolute():
        compiler_path = root / compiler_path
    if digest(compiler_path) != compiler['sha256']:
        raise ValueError('recorded compiler binary hash differs')
    build = record['build']
    if build['returncode'] != 0 or not isinstance(build['argv'], list) or not build['argv'] or not build['cwd']:
        raise ValueError('missing successful build command/cwd/returncode')
    command = build['argv']
    if (Path(build['cwd']) / command[0]).resolve() != compiler_path.resolve():
        raise ValueError('build argv does not use the recorded compiler')
    if ('--par' in command) != (mode == 'par'):
        raise ValueError('build command parallel mode differs')
    if '--entry' not in command or command[command.index('--entry') + 1:command.index('--entry') + 2] != ['layout_oracle']:
        raise ValueError('build command does not name layout_oracle')
    if '--graph' not in command or not command[command.index('--graph') + 1:command.index('--graph') + 2]:
        raise ValueError('build command lacks its graph')
    graph = Path(build['cwd']) / command[command.index('--graph') + 1]
    if not str(graph).endswith('/renderer/modules.wfg'):
        raise ValueError('build graph is not renderer/modules.wfg')
    if '-o' not in command or not command[command.index('-o') + 1:command.index('-o') + 2]:
        raise ValueError('build command lacks its output')
    if build['output_sha256'] != record['binary_sha256']:
        raise ValueError('build output hash differs from retained driver')
    for stream in ('stdout', 'stderr'):
        evidence = build[stream]
        path = root / evidence['path']
        relative(path, root)
        if digest(path) != evidence['sha256']:
            raise ValueError('build raw evidence hash differs: ' + stream)
    return {'source_revision': snapshot['revision'], 'source_fingerprint': snapshot['fingerprint'],
            'whitefoot_revision': snapshot['whitefoot_revision'], 'record': record,
            'association': 'verified build record and git source snapshot; requires truthful build-time capture'}


def performance(summary, pages, kinds, phases):
    """A bad observation remains evidence; incomplete evidence is untested."""
    result = {'selection_rule': 'independent min(update_us)/min(full_us) <= 1.2 per rootfont edit',
              'primary_mode': 'par', 'scope': 'selected datasets only',
              'original_three_page_criterion2': 'untested', 'by_case': {}, 'by_role_mode': {}}
    for role in ('baseline', 'candidate'):
        for mode in ('par', 'seq'):
            verdicts = []
            for page in pages:
                key = f'{page}:rootfont:{role}:{mode}'
                values = summary['best'].get(key)
                valid = summary['integrity_passed'] and 'rootfont' in kinds and set(phases) == {'identity', 'timing'} and values
                failed = [item['edit'] for item in values if not item['independent_min_within_1_2']] if values else []
                verdict = ('fail' if failed else 'pass') if valid else 'untested'
                result['by_case'][key] = {'criterion2': verdict, 'failed_edits': failed,
                                        'dataset': summary.get('datasets', {}).get(page, {}).get('kind', 'synthetic')}
                verdicts.append(verdict)
            result['by_role_mode'][role + '-' + mode] = (
                'fail' if 'fail' in verdicts else 'pass' if all(v == 'pass' for v in verdicts) else 'untested')
    return result


def self_test():
    """Exercise falsifiers on synthetic metadata/output, never real pages."""
    base = b'base hash 0123456789abcdef bytes 100\n'
    counts = b' prepared 0 contexts 0 paragraphs 0 held_entries 0 entries 0\n'
    identity = base + b'style edit 1' + counts + b'edit 1 hash 0123456789abcdef bytes 100 inc same\n'
    timing = base + b'style edit 1 delta_us 2 picks_us 3 full_us 10\nedit 1 us 8' + counts
    assert not parse(identity, 1, 'identity', True)['errors']
    assert not parse(timing, 1, 'timing', True)['errors']
    bad = {
        'missing-style-identity': (base + identity.splitlines(keepends=True)[2], 'identity'),
        'missing-style-timing': (base + timing.splitlines(keepends=True)[2], 'timing'),
        'duplicate-style': (identity.replace(b'edit 1 hash', b'style edit 1' + counts + b'edit 1 hash'), 'identity'),
        'wrong-auxiliary-ID': (identity.replace(b'style edit 1', b'style edit 2'), 'identity'),
        'DIFF': (identity.replace(b'inc same', b'inc DIFF'), 'identity'),
        'refused': (identity.replace(b'inc same', b'inc refused'), 'identity'),
        'wrong-count': (identity.replace(b'prepared 0', b'prepared 1'), 'identity'),
        'zero-full': (timing.replace(b'full_us 10', b'full_us 0'), 'timing'),
        'truncated': (identity[:-1], 'identity'),
        'impossible-components': (timing.replace(b'us 8 prepared', b'us 4 prepared'), 'timing'),
        'missing-output': (b'', 'identity'),
    }
    report = {'synthetic_only': True, 'parser_falsifiers': {}}
    for label, (raw, phase) in bad.items():
        errors = parse(raw, 1, phase, True)['errors']
        assert errors, label
        report['parser_falsifiers'][label] = errors
    home = Path(__file__).resolve().parents[4] / 'build/x5'
    home.mkdir(parents=True, exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix='style-update-selftest-', dir=home))
    root = evidence / 'synthetic-root'
    root.mkdir()
    def write(name, data):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        return path
    write('renderer/modules.wfg', 'synthetic graph; not compiled\n')
    write('renderer/synthetic.wf', 'synthetic source; not compiled\n')
    write('renderer/style/ua.css', 'synthetic UA\n')
    git(root, 'init', '-q')
    git(root, 'add', 'renderer')
    git(root, 'update-index', '--add', '--cacheinfo', '160000,3629be153b8fdb792ffe146d21dfc3251e4f887a,whitefoot')
    git(root, '-c', 'user.name=Style measurement self-test', '-c', 'user.email=selftest@example.invalid', 'commit', '-qm', 'Synthetic measurement fixture')
    snapshot = source_snapshot(root, 'HEAD')
    write('build/fonts/synthetic.bin', 'synthetic font, not loaded\n')
    pins = {}
    for name in ORIGINAL_HASHES:
        path = write('build/research/concurrency/' + name, 'synthetic ' + name)
        pins[name] = digest(path)
    apollo = 'build/x5/supplement'
    items = []
    for name in ('apollo11.html', 'apollo11-modules.css', 'apollo11-site.css'):
        path = write(apollo + '/' + name, 'synthetic ' + name)
        items.append({'file': relative(path, root), 'sha256': digest(path), 'bytes': path.stat().st_size})
    write(apollo + '/manifest.json', json.dumps({'files': items}))
    for page in ('ecma262', 'html5', 'apollo11'):
        for kind in KINDS:
            count = 20 if page == 'ecma262' else 60
            write(f'build/x5/scripts/{page}-{kind}.edits', 'S .synthetic{}\n' + 'C 4 synthetic\nK 4 synthetic\n' * (count // 2))
    stub = '''#!{python}
import json, os, pathlib, sys
mode, script, page, ua, *sheets = sys.argv[1:]
assert all(not pathlib.Path(p).is_absolute() and '..' not in pathlib.Path(p).parts for p in (script,page,ua))
count = len(pathlib.Path(script).read_text().splitlines()) - 1
kind = pathlib.Path(script).stem.split('-')[-1]
fault = pathlib.Path('fault.txt').read_text().strip()
if fault == 'exit7':
    print('deliberate failed subprocess', file=sys.stderr); sys.exit(7)
key = pathlib.Path(sys.argv[0]).name + ':' + script
path = pathlib.Path('build/counters.json')
counters = json.loads(path.read_text()) if path.exists() else {{}}
run = counters.get(key, 0) + 1 if mode == 'incremental' else 0
if run:
    counters[key] = run; path.write_text(json.dumps(counters))
print('base hash 0123456789abcdef bytes 100')
for i in range(1,count+1):
    counts = [0]*5 if kind == 'colour' else [1,2,3,4,5]
    if fault == 'colour-work': counts[0] = 1
    if fault == 'count-mismatch' and mode == 'incremental': counts[0] += 1
    text = ' '.join(n+' '+str(v) for n,v in zip(('prepared','contexts','paragraphs','held_entries','entries'),counts))
    if fault != 'missing-style':
        print('style edit',i,text if mode == 'edit' else 'delta_us 100 picks_us 100 full_us '+str([1200,1000,1100][(run-1)%3]))
    if mode == 'edit': print('edit',i,'hash 0123456789abcdef bytes 100 inc','DIFF' if fault == 'DIFF' else 'same')
    else: print('edit',i,'us',1600 if fault == 'performance' else [1000,1400,1100][(run-1)%3],text)
'''.format(python=sys.executable)
    compiler = write('build/synthetic-compiler', 'synthetic compiler marker; no compilation\n')
    build_out = write('build/synthetic-build.stdout', 'synthetic association test; no compilation\n')
    build_err = write('build/synthetic-build.stderr', '')
    builds = {}
    for role, stem in [('baseline', 'style'), ('candidate', 'independent')]:
        for mode in ('seq', 'par'):
            binary = write(f'build/layout_oracle_{stem}_{mode}', stub)
            binary.chmod(0o755)
            builds[role + '-' + mode] = {
                'source_revision': snapshot['revision'], 'source_files': snapshot['files'],
                'binary': relative(binary, root), 'binary_sha256': digest(binary),
                'compiler': {'revision': snapshot['whitefoot_revision'], 'path': str(compiler), 'sha256': digest(compiler)},
                'build': {'argv': [str(compiler), '--graph', 'modules.wfg', '--entry', 'layout_oracle', '-o', str(binary), *(['--par'] if mode == 'par' else [])],
                          'cwd': str(root / 'renderer'), 'returncode': 0,
                          'output_sha256': digest(binary),
                          'stdout': {'path': relative(build_out, root), 'sha256': digest(build_out)},
                          'stderr': {'path': relative(build_err, root), 'sha256': digest(build_err)}}}
    manifest = write('build/manifest.json', json.dumps({'schema': 1, 'builds': builds}))
    valid = builds['baseline-seq']
    binary = root / valid['binary']
    verify_build(valid, binary, snapshot, 'seq', root)
    report['provenance_falsifiers'] = []
    for label in ('revision', 'missing-source', 'wrong-source', 'binary', 'compiler', 'compiler-pin', 'mode',
                  'build-exit', 'build-log', 'command-compiler', 'graph', 'output-hash', 'entry', 'output-flag'):
        wrong = copy.deepcopy(valid)
        if label == 'revision': wrong['source_revision'] = '0' * 40
        elif label == 'missing-source': wrong['source_files'].pop('renderer/synthetic.wf')
        elif label == 'wrong-source': wrong['source_files']['renderer/synthetic.wf'] = '0' * 64
        elif label == 'binary': wrong['binary_sha256'] = '0' * 64
        elif label == 'compiler': wrong['compiler']['sha256'] = '0' * 64
        elif label == 'compiler-pin': wrong['compiler']['revision'] = '0' * 40
        elif label == 'mode': wrong['build']['argv'].append('--par')
        elif label == 'build-exit': wrong['build']['returncode'] = 1
        elif label == 'build-log': wrong['build']['stdout']['sha256'] = '0' * 64
        elif label == 'command-compiler': wrong['build']['argv'][0] = '/nonexistent-compiler'
        elif label == 'graph': wrong['build']['argv'][2] = 'wrong.wfg'
        elif label == 'output-hash': wrong['build']['output_sha256'] = '0' * 64
        elif label == 'entry': wrong['build']['argv'][4] = 'wrong_entry'
        elif label == 'output-flag': wrong['build']['argv'][5] = '--wrong-output'
        try:
            verify_build(wrong, binary, snapshot, 'seq', root)
        except ValueError:
            report['provenance_falsifiers'].append(label)
        else:
            raise AssertionError('bad provenance passed: ' + label)
    common = ['--root', str(root), '--baseline-source', snapshot['revision'], '--candidate-source', snapshot['revision'],
              '--build-manifest', str(manifest), '--apollo-data-dir', apollo, '--apollo-manifest', apollo + '/manifest.json']
    owner = os.environ.get('WHITEFOOT_CHECK_OWNER')
    os.environ['WHITEFOOT_CHECK_OWNER'] = 'synthetic-self-test-only'
    report['matrix'] = {}
    try:
        for fault in ('normal', 'performance', 'missing-style', 'colour-work', 'count-mismatch', 'DIFF', 'exit7'):
            write('fault.txt', fault)
            (root / 'build/counters.json').unlink(missing_ok=True)
            output = root / ('build/x5/output-' + fault)
            selection = ['--pages', 'ecma262', 'html5', 'apollo11'] if fault == 'normal' else ['--pages', 'ecma262', '--kinds', 'colour' if fault == 'colour-work' else 'rootfont']
            with (evidence / (fault + '.report')).open('w') as log, contextlib.redirect_stdout(log):
                code = main(common + selection + ['--output', str(output)], prepare_test=lambda summary, args: pins)
            summary = json.loads((output / 'results.json').read_text())
            wanted = 0 if fault in ('normal', 'performance') else 1
            assert code == wanted, (fault, code)
            assert len(summary['runs']) == (144 if fault == 'normal' else 16)
            if fault == 'normal':
                assert summary['performance']['by_role_mode']['candidate-par'] == 'pass'
                assert any(summary['rootfont_observations'].values())
            if fault == 'performance':
                assert summary['execution_correctness'] == 'pass'
                assert summary['performance']['by_role_mode']['candidate-par'] == 'fail'
            assert all('stdout_sha256' in run and run['returncode'] is not None for run in summary['runs'])
            report['matrix'][fault] = {'exit': code, 'processes': len(summary['runs']),
                'execution_correctness': summary['execution_correctness'], 'performance': summary['performance']['by_role_mode']}
        write('fault.txt', 'normal')
        (root / apollo / 'apollo11-modules.css').unlink()
        output = root / 'build/x5/output-missing-apollo'
        with (evidence / 'missing-apollo.report').open('w') as log, contextlib.redirect_stdout(log):
            code = main(common + ['--pages', 'apollo11', '--kinds', 'rootfont', '--output', str(output)],
                        prepare_test=lambda summary, args: pins)
        summary = json.loads((output / 'results.json').read_text())
        assert code == 1 and not summary['runs'] and summary['incomplete_cases'] == 8
        report['matrix']['missing-apollo'] = {'exit': code, 'processes': 0, 'execution_correctness': summary['execution_correctness']}
        # Individually valid records can still confound the comparison with
        # a different compiler. Check those cross-build conditions as well.
        changed = copy.deepcopy(builds)
        second_compiler = write('build/other-compiler', 'different synthetic compiler bytes\n')
        changed['candidate-par']['compiler']['path'] = str(second_compiler)
        changed['candidate-par']['compiler']['sha256'] = digest(second_compiler)
        changed['candidate-par']['build']['argv'][0] = str(second_compiler)
        manifest.write_text(json.dumps({'schema': 1, 'builds': changed}))
        output = root / 'build/x5/output-compiler-mismatch'
        with (evidence / 'compiler-mismatch.report').open('w') as log, contextlib.redirect_stdout(log):
            code = main(common + ['--pages', 'ecma262', '--kinds', 'rootfont', '--output', str(output)],
                        prepare_test=lambda summary, args: pins)
        summary = json.loads((output / 'results.json').read_text())
        assert code == 1 and not summary['runs'] and any('same pinned compiler binary' in f for f in summary['failures'])
        report['matrix']['compiler-mismatch'] = {'exit': code, 'processes': 0}
        manifest.write_text(json.dumps({'schema': 1, 'builds': builds}))
        git(root, 'update-index', '--cacheinfo', '160000,0000000000000000000000000000000000000001,whitefoot')
        git(root, '-c', 'user.name=Style measurement self-test', '-c', 'user.email=selftest@example.invalid', 'commit', '-qm', 'Synthetic different compiler pin')
        different = git(root, 'rev-parse', 'HEAD').decode().strip()
        selection = common.copy()
        selection[selection.index('--candidate-source') + 1] = different
        output = root / 'build/x5/output-pin-mismatch'
        with (evidence / 'pin-mismatch.report').open('w') as log, contextlib.redirect_stdout(log):
            code = main(selection + ['--pages', 'ecma262', '--kinds', 'rootfont', '--output', str(output)],
                        prepare_test=lambda summary, args: pins)
        summary = json.loads((output / 'results.json').read_text())
        assert code == 1 and not summary['runs'] and any('pin different compilers' in f for f in summary['failures'])
        report['matrix']['pin-mismatch'] = {'exit': code, 'processes': 0}
    finally:
        if owner is None:
            del os.environ['WHITEFOOT_CHECK_OWNER']
        else:
            os.environ['WHITEFOOT_CHECK_OWNER'] = owner
    (evidence / 'self-test.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Synthetic self-test passed: 11 parser falsifiers, 14 provenance falsifiers, 10 stub matrices; evidence: ' + str(evidence))
    return 0


def main(argv=None, prepare_test=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument('--pages', nargs='+', choices=('ecma262', 'html5', 'apollo11'), default=['ecma262', 'html5'])
    parser.add_argument('--kinds', nargs='+', choices=KINDS, default=list(KINDS))
    parser.add_argument('--phases', nargs='+', choices=('identity', 'timing'), default=['identity', 'timing'])
    parser.add_argument('--scripts-dir', type=Path, default=Path('build/x5/scripts'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--apollo-data-dir', type=Path, help='explicit supplementary capture below ROOT')
    parser.add_argument('--apollo-manifest', type=Path, help='explicit three-input supplementary manifest below ROOT')
    parser.add_argument('--baseline-source', help='commit used to build both baseline drivers')
    parser.add_argument('--candidate-source', help='commit used to build both candidate drivers')
    parser.add_argument('--build-manifest', type=Path, help='build-time source/binary/compiler/log association records')
    parser.add_argument('--self-test', action='store_true', help='lightweight parser, provenance and stub checks; no renderer run')
    for role, stem in [('baseline', 'style'), ('candidate', 'independent')]:
        for mode in ('seq', 'par'):
            parser.add_argument(f'--{role}-{mode}', type=Path, help=f'default ROOT/build/layout_oracle_{stem}_{mode}')
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if prepare_test is None and not all((args.baseline_source, args.candidate_source, args.build_manifest)):
        parser.error('--baseline-source, --candidate-source and --build-manifest are required')
    if prepare_test is None and 'apollo11' in args.pages and not all((args.apollo_data_dir, args.apollo_manifest)):
        parser.error('apollo11 requires explicit --apollo-data-dir and --apollo-manifest for supplementary data')
    for name in ('pages', 'kinds', 'phases'):
        values = getattr(args, name)
        if len(set(values)) != len(values):
            parser.error(f'{name} must be unique')
    root = args.root.resolve()
    output = (root / (args.output or Path('build/x5/style-update'))).resolve()
    relative(output, root)
    output.mkdir(parents=True, exist_ok=False)
    raw_dir = output / 'raw'
    raw_dir.mkdir()
    summary = {'root': str(root), 'machine': platform.platform(), 'processors': os.cpu_count(),
               'lock_owner': os.environ.get('WHITEFOOT_CHECK_OWNER'), 'state': 'running',
               'pages': args.pages, 'kinds': args.kinds, 'phases': args.phases,
               'scope': 'selected step 4b style edits only; original Apollo and full X5 remain unverified',
               'roles': ['baseline', 'candidate'], 'workers': {'seq': 1, 'par': 4}, 'timing_runs': 3,
               'drivers': {}, 'inputs': {}, 'fonts': {}, 'runs': [], 'comparisons': [], 'cases': [], 'failures': [],
               'best': {}, 'rootfont_observations': {}, 'datasets': {}, 'integrity_passed': None,
               'synthetic_self_test': prepare_test is not None}
    identity, timed = {}, {}

    def checkpoint():
        path = output / 'results.json.tmp'
        path.write_text(json.dumps(summary, indent=2) + '\n')
        path.replace(output / 'results.json')

    def fail(label, errors):
        summary['failures'].extend(f'{label}: {error}' for error in errors)

    def metadata(paths):
        result = {}
        for path in paths:
            path = Path(path)
            name = relative(path, root)
            result[name] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
            summary['inputs'][name] = result[name]
        return result

    def compare(label, first, second):
        equal = first == second
        summary['comparisons'].append({'label': label, 'equal': equal})
        if not equal:
            fail(label, ['normalized hashes/counts differ'])

    checkpoint()
    try:
        if not summary['lock_owner']:
            raise ValueError('WHITEFOOT_CHECK_OWNER is required; use the existing outer host lock')
        summary['criteria'] = {'sha256': hashlib.sha256(CRITERIA.encode()).hexdigest(), 'text': CRITERIA}
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True)
        if revision.returncode:
            raise ValueError('git revision failed: ' + revision.stderr)
        summary['root_revision'] = revision.stdout.strip()
        for role, stem in [('baseline', 'style'), ('candidate', 'independent')]:
            for mode in ('seq', 'par'):
                binary = (root / (getattr(args, f'{role}_{mode}') or Path(f'build/layout_oracle_{stem}_{mode}'))).resolve()
                if not binary.is_file() or not os.access(binary, os.X_OK):
                    raise ValueError(f'missing executable: {binary}')
                summary['drivers'][f'{role}-{mode}'] = {'path': str(binary), 'sha256': digest(binary)}
        snapshots = {role: source_snapshot(root, getattr(args, role + '_source')) for role in ('baseline', 'candidate')}
        if snapshots['baseline']['whitefoot_revision'] != snapshots['candidate']['whitefoot_revision']:
            raise ValueError('baseline/candidate source revisions pin different compilers')
        summary['source_snapshots'] = snapshots
        before, after = snapshots['baseline']['files'], snapshots['candidate']['files']
        summary['source_differences'] = {name: {'baseline': before.get(name), 'candidate': after.get(name)}
                                         for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)}
        manifest_path = (root / args.build_manifest).resolve()
        metadata([manifest_path])
        manifest = json.loads(manifest_path.read_text())
        if manifest['schema'] != 1 or set(manifest['builds']) != set(summary['drivers']):
            raise ValueError('build manifest requires schema 1 and all four driver records')
        for key, driver in summary['drivers'].items():
            role, mode = key.split('-')
            driver['provenance'] = verify_build(manifest['builds'][key], Path(driver['path']), snapshots[role], mode, root)
        if len({item['compiler']['sha256'] for item in manifest['builds'].values()}) != 1:
            raise ValueError('all four drivers require the same pinned compiler binary')
        if prepare_test is not None:
            synthetic_pins = prepare_test(summary, args)
        fonts = sorted(path for path in (root / 'build/fonts').rglob('*') if path.is_file())
        summary['fonts'] = {relative(path, root): digest(path) for path in fonts}
        if not summary['fonts']:
            raise ValueError('no font files')
        summary['font_fingerprint'] = hashlib.sha256(json.dumps(summary['fonts'], sort_keys=True).encode()).hexdigest()
        scripts = root / args.scripts_dir
        relative(scripts, root)
        for page in args.pages:
            data = relative(root / args.apollo_data_dir, root) if page == 'apollo11' else 'build/research/concurrency'
            html = root / data / (page + '.html')
            sheets = mappings(page, data)
            paths = [html, root / 'renderer/style/ua.css', *[root / mapping.rsplit('=', 1)[1] for mapping in sheets]]
            base_inputs = metadata(paths)
            if page == 'apollo11':
                manifest_path = root / args.apollo_manifest
                metadata([manifest_path])
                manifest = json.loads(manifest_path.read_text())
                for item in manifest['files']:
                    path = root / item['file']
                    if relative(path, root) not in base_inputs or digest(path) != item['sha256'] or path.stat().st_size != item['bytes']:
                        raise ValueError('Apollo supplementary manifest differs from actual inputs')
                expected_manifest_paths = {relative(path, root) for path in paths if path.name != 'ua.css'}
                if len(manifest['files']) != 3 or {item['file'] for item in manifest['files']} != expected_manifest_paths:
                    raise ValueError('Apollo supplementary manifest requires all three distinct inputs')
                summary['datasets'][page] = {'kind': 'supplementary', 'directory': data,
                                            'manifest': relative(manifest_path, root), 'manifest_sha256': digest(manifest_path)}
            else:
                for path in [html, *[root / m.rsplit('=', 1)[1] for m in sheets]]:
                    expected_pin = ORIGINAL_HASHES[path.name] if prepare_test is None else synthetic_pins[path.name]
                    if digest(path) != expected_pin:
                        raise ValueError(f'original workload pin mismatch: {path}')
                summary['datasets'][page] = {'kind': 'original pinned inputs' if prepare_test is None else 'synthetic self-test inputs', 'directory': data}
            for kind in args.kinds:
                expected = 20 if page == 'ecma262' else 60
                script = scripts / f'{page}-{kind}.edits'
                inputs = {**base_inputs, **metadata([script])}
                errors = script_errors(script, expected)
                fail(f'{page}-{kind}-script', errors)
                if errors:
                    checkpoint()
                    continue
                for phase in args.phases:
                    for role in ('baseline', 'candidate'):
                        for mode in ('seq', 'par'):
                            key = f'{page}:{kind}:{role}:{mode}'
                            repetitions = 3 if phase == 'timing' else 1
                            case = {'case': key, 'phase': phase, 'state': 'running', 'expected_edits': expected}
                            start_errors = len(summary['failures'])
                            summary['cases'].append(case)
                            checkpoint()
                            parsed_runs = []
                            for repetition in range(1, repetitions + 1):
                                label = f'{page}-{kind}.{role}-{mode}.{phase}.r{repetition}'
                                stdout, stderr = raw_dir / (label + '.stdout'), raw_dir / (label + '.stderr')
                                driver = summary['drivers'][role + '-' + mode]
                                if digest(Path(driver['path'])) != driver['sha256']:
                                    raise ValueError('driver changed after provenance validation: ' + role + '-' + mode)
                                for path, info in inputs.items():
                                    if digest(root / path) != info['sha256']:
                                        raise ValueError('input changed during measurement: ' + path)
                                if {relative(path, root): digest(path) for path in (root / 'build/fonts').rglob('*') if path.is_file()} != summary['fonts']:
                                    raise ValueError('font dataset changed during measurement')
                                command = [relative(Path(driver['path']), root), 'edit' if phase == 'identity' else 'incremental', relative(script, root), relative(html, root), 'renderer/style/ua.css', *sheets]
                                record = {'label': label, 'case': key, 'phase': phase, 'run': repetition, 'command': command,
                                          'workers': 1 if mode == 'seq' else 4, 'driver': driver, 'inputs': inputs,
                                          'font_fingerprint': summary['font_fingerprint'], 'returncode': None,
                                          'stdout': str(stdout), 'stderr': str(stderr), 'state': 'running'}
                                summary['runs'].append(record)
                                checkpoint()
                                try:
                                    with stdout.open('wb') as out, stderr.open('wb') as err:
                                        completed = subprocess.run(command, cwd=root, env=dict(os.environ, WF_WORKERS=str(record['workers'])), stdout=out, stderr=err)
                                    record['returncode'] = completed.returncode
                                    if completed.returncode:
                                        fail(label, [f'subprocess exited {completed.returncode}'])
                                except OSError as error:
                                    record['spawn_error'] = str(error)
                                    fail(label, [str(error)])
                                finally:
                                    record['state'] = 'finished' if record['returncode'] is not None else 'incomplete'
                                    for stream, path in [('stdout', stdout), ('stderr', stderr)]:
                                        if path.is_file():
                                            record[stream + '_sha256'] = digest(path)
                                            record[stream + '_bytes'] = path.stat().st_size
                                    checkpoint()
                                record['parsed'] = parse(stdout.read_bytes() if stdout.is_file() else b'', expected, phase, kind == 'colour')
                                fail(label, record['parsed']['errors'])
                                checkpoint()
                                if record['returncode'] == 0 and not record['parsed']['errors']:
                                    parsed_runs.append(record['parsed'])
                            if len(parsed_runs) == repetitions:
                                if phase == 'identity':
                                    identity[key] = parsed_runs[0]
                                else:
                                    timed[key] = parsed_runs
                                    for repetition in range(1, 3):
                                        compare(key + f'-timing-counts-r1-r{repetition + 1}', [r['counts'] for r in parsed_runs[0]['records']], [r['counts'] for r in parsed_runs[repetition]['records']])
                                        compare(key + f'-timing-base-r1-r{repetition + 1}', parsed_runs[0]['base'], parsed_runs[repetition]['base'])
                                    summary['best'][key] = select_best([run['records'] for run in parsed_runs])
                                    if kind == 'rootfont':
                                        summary['rootfont_observations'][key] = {
                                            'paired_over_1_2': [{'edit': r['edit'], 'run': i + 1, 'update_us': r['update_us'], 'full_us': r['full_us'], 'ratio': r['paired_ratio']} for i, run in enumerate(parsed_runs) for r in run['records'] if not r['paired_within_1_2']],
                                            'minimum_paired_over_1_2': [r['edit'] for r in summary['best'][key] if not r['minimum_paired_within_1_2']]}
                            case.update(state='finished', integrity_passed=len(summary['failures']) == start_errors, valid_process_runs=len(parsed_runs))
                            checkpoint()
        for page in args.pages:
            for kind in args.kinds:
                for role in ('baseline', 'candidate'):
                    seq, par = f'{page}:{kind}:{role}:seq', f'{page}:{kind}:{role}:par'
                    if seq in identity and par in identity:
                        compare(seq + '-identity-seq-par', identity[seq], identity[par])
                    if seq in timed and par in timed:
                        for i in range(3):
                            compare(seq + f'-timing-seq-par-r{i + 1}', {'base': timed[seq][i]['base'], 'counts': [r['counts'] for r in timed[seq][i]['records']]}, {'base': timed[par][i]['base'], 'counts': [r['counts'] for r in timed[par][i]['records']]})
                    for key in [seq, par]:
                        if key in identity and key in timed:
                            for i in range(3):
                                compare(key + f'-identity-timing-r{i + 1}', {'base': identity[key]['base'], 'counts': [r['counts'] for r in identity[key]['records']]}, {'base': timed[key][i]['base'], 'counts': [r['counts'] for r in timed[key][i]['records']]})
                for mode in ('seq', 'par'):
                    a, b = f'{page}:{kind}:baseline:{mode}', f'{page}:{kind}:candidate:{mode}'
                    if a in identity and b in identity:
                        compare(a + '-baseline-candidate-hashes', {'base': identity[a]['base'], 'hashes': [(r['hash'], r['bytes']) for r in identity[a]['records']]}, {'base': identity[b]['base'], 'hashes': [(r['hash'], r['bytes']) for r in identity[b]['records']]})
    except (OSError, ValueError, KeyError, TypeError, IndexError, KeyboardInterrupt) as error:
        fail('execution', [type(error).__name__ + ': ' + str(error)])
    expected_cases = len(args.pages) * len(args.kinds) * len(args.phases) * 4
    summary['incomplete_cases'] = expected_cases - sum(c.get('state') == 'finished' for c in summary['cases'])
    summary['integrity_passed'] = not summary['failures'] and summary['incomplete_cases'] == 0
    summary['execution_correctness'] = 'pass' if summary['integrity_passed'] else 'fail'
    summary['performance'] = performance(summary, args.pages, args.kinds, args.phases)
    summary['full_comparisons'] = {}
    for page in args.pages:
        for kind in args.kinds:
            for mode in ('par', 'seq'):
                baseline, candidate = f'{page}:{kind}:baseline:{mode}', f'{page}:{kind}:candidate:{mode}'
                if baseline in timed and candidate in timed:
                    summary['full_comparisons'][f'{page}:{kind}:{mode}'] = [
                        {'edit': index + 1, 'runs': [
                            {'run': run + 1, 'baseline_full_us': timed[baseline][run]['records'][index]['full_us'],
                             'candidate_full_us': timed[candidate][run]['records'][index]['full_us']}
                            for run in range(3)]}
                        for index in range(len(timed[baseline][0]['records']))]
    summary['state'] = 'finished'
    checkpoint()
    observations = sum(len(v['paired_over_1_2']) for v in summary['rootfont_observations'].values())
    report = [summary['scope'], f"Selection: pages={args.pages}, kinds={args.kinds}, phases={args.phases}", f"Execution/correctness of selected phases: {summary['execution_correctness']}; incomplete cases: {summary['incomplete_cases']}",
              f"Criterion 2 on selected datasets (four workers, primary): {summary['performance']['by_role_mode'].get('candidate-par')}; baseline: {summary['performance']['by_role_mode'].get('baseline-par')}",
              f"Criterion 2 on selected datasets (sequential): {summary['performance']['by_role_mode'].get('candidate-seq')}; baseline: {summary['performance']['by_role_mode'].get('baseline-seq')}",
              f"Rootfont paired observations above 1.2: {observations}; none discarded",
              'Every paired observation and independent/minimum-paired selections remain in results.json.',
              'Original Apollo criterion is not certified by this supplementary capture.']
    report += ['FAILURE: ' + error for error in summary['failures']]
    report.append(f'Raw evidence: {output}')
    (output / 'report.txt').write_text('\n'.join(report) + '\n')
    print('\n'.join(report))
    # A valid measurement that misses its cost goal remains a valid execution.
    # results.json/report.txt expose the separate performance conclusion.
    return 0 if summary['integrity_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
