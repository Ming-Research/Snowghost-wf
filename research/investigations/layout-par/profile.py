"""Temporary CI-only layout profiles, called by par-inventory.yml.

Keep the untouched production driver and pinned compiler. Remove this harness
and the workflow once the evidence is archived. inventory.py owns accounting.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path.cwd()
OUT = ROOT / 'build/layout-par'
DATA = Path('build/research/concurrency')
ENTRY = 'wf_layout.lay_out'
PAGES = ('ecma262', 'html5', 'apollo11')
BUDGET_SECONDS = 25 * 60
RESERVE_SECONDS = 60


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sheets(page):
    if page == 'ecma262':
        return [f'assets/css/ecmarkup.css={DATA}/ecma262-ecmarkup.css',
                f'assets/css/print.css={DATA}/ecma262-print.css']
    if page == 'apollo11':
        return [f'wikibase.client.init&only=styles&skin=vector-2022={DATA}/apollo11-modules.css',
                f'modules=site.styles&only=styles&skin=vector-2022={DATA}/apollo11-site.css']
    if page == 'html5':
        return []
    raise ValueError(('unknown page', page))


class Investigation:
    def __init__(self):
        self.started = time.monotonic()
        self.budget = min(BUDGET_SECONDS, float(os.environ['LAYOUT_PAR_DEADLINE']) - time.time())
        if self.budget <= RESERVE_SECONDS:
            raise ValueError('shared workflow deadline leaves no profiling budget')
        spec = importlib.util.spec_from_file_location('layout_inventory',
                                                    Path(__file__).with_name('inventory.py'))
        self.accounting = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.accounting
        spec.loader.exec_module(self.accounting)

    def remaining(self):
        return self.budget - (time.monotonic() - self.started)

    def run(self, label, command, cap, cwd=ROOT, stdout_name=None):
        allowance = min(cap, self.remaining() - RESERVE_SECONDS)
        if allowance <= 0:
            raise RuntimeError(('investigation budget exhausted before process', label))
        stdout_path = OUT / (stdout_name or label + '.raw')
        stderr_path = OUT / (label + '.stderr')
        started = time.monotonic()
        code, expired, problem = None, False, None
        with stdout_path.open('w') as stdout, stderr_path.open('w') as stderr:
            try:
                process = subprocess.Popen(command, cwd=cwd,
                                           env=dict(os.environ, WF_WORKERS='1'),
                                           stdout=stdout, stderr=stderr,
                                           start_new_session=True)
                try:
                    code = process.wait(timeout=allowance)
                except subprocess.TimeoutExpired:
                    expired = True
                    # The compiler and Valgrind can have descendants. Bound
                    # the whole group, not only the waiting parent process.
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        code = process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        code = process.wait()
            except OSError as error:
                problem = str(error)
        record = dict(label=label, command=list(map(str, command)),
                      cwd=str(cwd.relative_to(ROOT)) if cwd != ROOT else '.',
                      workers=1, allowance_seconds=allowance,
                      elapsed_seconds=time.monotonic() - started,
                      exit=code, timeout=expired, spawn_error=problem,
                      stdout=str(stdout_path.relative_to(ROOT)),
                      stderr=str(stderr_path.relative_to(ROOT)))
        with (OUT / 'processes.jsonl').open('a') as output:
            output.write(json.dumps(record) + '\n')
        print(json.dumps(record), flush=True)
        if expired or problem is not None or code != 0:
            raise RuntimeError(('process failed; partial output is not evidence', record))
        return record

    def inputs(self):
        # Apollo's permanent original-page fixture is independent of the
        # later capture that concurrency/run.sh pins. Never silently refetch
        # it or accept a failed fetch. The manifest is the fixture's oracle.
        (ROOT / DATA).mkdir(parents=True, exist_ok=True)
        self.run('apollo-extract', ['tar', '-xzf',
                 'tests/layout/fixtures/apollo11/inputs.tar.gz', '-C', str(DATA)], 20)
        self.run('apollo-hashes', ['sha256sum', '-c',
                 'tests/layout/fixtures/apollo11/inputs.sha256'], 20)
        source = ROOT / 'research/investigations/concurrency/run.sh'
        match = re.search(r"pins\(\) \{\s+cat <<'EOF'\n(.*?)\nEOF\n\}",
                          source.read_text(), re.S)
        if not match:
            raise ValueError('could not read the authoritative E1 input pins')
        selected = []
        for row in match.group(1).splitlines():
            name, url, expected = row.split()
            if not name.startswith(('ecma262', 'html5')):
                continue
            selected.append(name)
            destination = ROOT / DATA / name
            if not destination.is_file() or digest(destination) != expected:
                partial = destination.with_suffix(destination.suffix + '.part')
                self.run('fetch-' + name, ['curl', '-fsSL', '--retry', '2',
                         '--connect-timeout', '15', '--max-time', '60',
                         '-o', str(partial.relative_to(ROOT)), url], 200)
                if digest(partial) != expected:
                    raise ValueError(('pinned E1 input hash differs', name))
                partial.replace(destination)
        if set(selected) != {'ecma262.html', 'ecma262-ecmarkup.css',
                             'ecma262-print.css', 'html5.html'}:
            raise ValueError(('E1 input pin inventory differs', selected))

    def provenance(self, compiler):
        for label, command in (
            ('revision', ['git', 'rev-parse', 'HEAD']),
            ('submodules', ['git', 'submodule', 'status']),
            ('worktree', ['git', 'status', '--porcelain']),
            ('clang-version', ['/usr/bin/clang', '--version']),
            ('linker-version', ['ld.lld', '--version']),
            ('profiler-version', ['valgrind', '--version']),
            ('font-packages', ['dpkg-query', '-W', 'fonts-*']),
            ('machine', ['lscpu']),
        ):
            self.run(label, command, 10)
        files = [ROOT / DATA / (page + '.html') for page in PAGES]
        files += [ROOT / mapping.rsplit('=', 1)[1]
                  for page in PAGES for mapping in sheets(page)]
        files += [ROOT / 'renderer/style/ua.css']
        fonts = sorted((ROOT / 'build/fonts').glob('*'))
        if not fonts or any(not path.is_file() or path.is_symlink() for path in fonts):
            raise ValueError('oracle fonts must be a nonempty set of copied files')
        metadata = dict(
            workflow_revision=os.environ['GITHUB_SHA'],
            workflow_run_id=os.environ['GITHUB_RUN_ID'],
            system=platform.uname()._asdict(),
            compiler_release_manifest=json.loads(compiler.with_name('whitefoot-release.json').read_text()),
            whitefoot_pin=(ROOT / 'whitefoot.pin').read_text(),
            compiler_sha256=digest(compiler),
            inputs={str(path.relative_to(ROOT)): digest(path) for path in files},
            fonts={str(path.relative_to(ROOT)): digest(path) for path in fonts},
            methodology_sha256={str(path.relative_to(ROOT)): digest(path) for path in (
                Path(__file__).resolve(), Path(__file__).with_name('inventory.py').resolve(),
                ROOT / '.github/workflows/par-inventory.yml',
                ROOT / 'research/investigations/concurrency/run.sh',
                ROOT / 'tests/layout/fixtures/apollo11/inputs.sha256')},
            historical_e1_input_identity='unverified: repository Apollo fixture and current oracle fonts',
            collection_entry=ENTRY, instruction_event='Ir',
            budget_seconds=self.budget,
            shared_workflow_deadline_epoch=float(os.environ['LAYOUT_PAR_DEADLINE']))
        write_json(OUT / 'provenance.json', metadata)
        (OUT / 'whitefoot.pin').write_text(metadata['whitefoot_pin'])
        compiler_manifest = compiler.with_name('whitefoot-release.json')
        shutil.copyfile(compiler_manifest, OUT / compiler_manifest.name)
        # The fixture and pinned downloads remain recoverable independently of
        # Actions retention, but the actual run also keeps every input byte.
        for folder, sources in (('inputs', files), ('fonts', fonts)):
            destination = OUT / folder
            destination.mkdir()
            for source in sources:
                shutil.copyfile(source, destination / source.name)

    def builds(self, compiler):
        for name, flags in (('seq', []), ('par', ['--par', '--par-ledger'])):
            cache = ROOT / 'build' / ('layout-par-cache-' + name)
            if cache.exists():
                raise ValueError(('fresh build cache required', str(cache)))
            output = OUT / ('layout-' + name)
            command = [str(compiler), '--cache', str(cache), '--fragments', 'function',
                       *flags, '--graph', 'modules.wfg', '--entry', 'layout_oracle',
                       '-o', str(output)]
            self.run('build-' + name, command, 600, cwd=ROOT / 'renderer',
                     stdout_name='par-ledger.log' if name == 'par' else 'build-seq.log')
        self.run('symbols-seq', ['nm', '--defined-only', str(OUT / 'layout-seq')], 15)
        names = [line.split()[-1] for line in (OUT / 'symbols-seq.raw').read_text().splitlines()
                 if line.split()]
        if names.count(ENTRY) != 1:
            raise ValueError(('exact layout entry missing or ambiguous; do not change compiler or source',
                              ENTRY, names.count(ENTRY)))
        write_json(OUT / 'drivers.json', {
            name: dict(sha256=digest(OUT / ('layout-' + name)),
                       path=str((OUT / ('layout-' + name)).relative_to(ROOT)))
            for name in ('seq', 'par')})
        self.run('source-ledger-coverage', [sys.executable, '-I',
                 'research/investigations/layout-par/inventory.py', 'inventory',
                 '--root', '.', '--ledger', 'build/layout-par/par-ledger.log',
                 '--out', 'build/layout-par'], 60)

    def profile(self, page, count, cap, label=None):
        label = label or page
        driver = str((OUT / 'layout-seq').relative_to(ROOT))
        command = ['valgrind', '--tool=callgrind', '--collect-atstart=no',
                   '--toggle-collect=' + ENTRY,
                   '--callgrind-out-file=' + str((OUT / (label + '.callgrind')).relative_to(ROOT)),
                   driver, 'layout', str(count), str(DATA / (page + '.html')),
                   'renderer/style/ua.css', *sheets(page)]
        record = self.run(label, command, cap)
        raw = (OUT / (label + '.raw')).read_text()
        match = re.fullmatch(r'layout elements (\d+) contexts (\d+) paragraphs (\d+) reps (\d+)\s*', raw)
        if not match or int(match[4]) != count:
            raise ValueError(('unexpected layout protocol', label, raw))
        total, own, edges = self.accounting.parse_callgrind(OUT / (label + '.callgrind'))
        if count == 0:
            if total != 0 or int(match[2]) != 0 or int(match[3]) != 0:
                raise ValueError(('startup entered layout negative control', total, raw))
        else:
            observed = set(own) | {symbol for pair in edges for symbol in pair}
            # Wrapper and LLVM body are the same source entry. Their internal
            # edges would count body work twice if added beside body self cost.
            family = self.accounting.normalize_symbol
            entry_family = family(ENTRY)
            inclusive = sum(cost for symbol, cost in own.items() if family(symbol) == entry_family)
            inclusive += sum(cost for (caller, callee), cost in edges.items()
                             if family(caller) == entry_family and family(callee) != entry_family)
            entry_observed = any(family(symbol) == entry_family for symbol in observed)
            if total <= 0 or not entry_observed or inclusive != total:
                raise ValueError(('layout entry does not cover exactly collected Ir',
                                  label, total, inclusive, entry_observed))
        return record

    def collect(self):
        self.profile('ecma262', 0, 240, label='zero')
        pilot = self.profile('ecma262', 1, 300)
        # This elapsed time chooses a bounded process budget only. A single
        # hosted observation gives neither timing spread nor speed evidence.
        sizes = {page: sum((ROOT / path).stat().st_size for path in
                           [str(DATA / (page + '.html')),
                            *[item.rsplit('=', 1)[1] for item in sheets(page)]])
                 for page in PAGES}
        caps = {page: max(120, 4 * pilot['elapsed_seconds'] *
                         max(1, sizes[page] / sizes['ecma262']))
                for page in PAGES[1:]}
        selection = dict(pilot=pilot, input_bytes=sizes, timeout_seconds=caps,
                         remaining_budget_seconds=self.remaining(),
                         scale_rule='4x pilot elapsed, at least 120s, scaled by HTML+sheet bytes; never below pilot size',
                         evidence_scope='administrative wall-time budget, no performance conclusion')
        write_json(OUT / 'scale-selection.json', selection)
        if sum(caps.values()) + RESERVE_SECONDS > self.remaining():
            raise RuntimeError(('remaining one-pass profiles require a separately chosen bounded batch', selection))
        for page in PAGES[1:]:
            self.profile(page, 1, caps[page])


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('this investigation runs only in CI')
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'processes.jsonl').exists():
        raise ValueError('output directory must not contain a prior invocation')
    started = time.monotonic()
    investigation = None
    status = dict(status='incomplete', started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    try:
        investigation = Investigation()
        pin = (ROOT / 'whitefoot.pin').read_text().strip()
        match = re.fullmatch(r'release = (wf-(?:exp-)?[0-9a-f]{12})', pin)
        if not match:
            raise ValueError('unexpected Whitefoot pin')
        compiler = ROOT / 'build/whitefoot' / match[1] / 'whitefootc'
        investigation.inputs()
        investigation.provenance(compiler)
        investigation.builds(compiler)
        investigation.collect()
        status['status'] = 'profiles-complete-accounting-pending'
    except Exception as error:
        status['reason'] = repr(error)
        raise
    finally:
        status['elapsed_seconds'] = time.monotonic() - started
        status['remaining_budget_seconds'] = investigation.remaining() if investigation else None
        write_json(OUT / 'profile-status.json', status)


if __name__ == '__main__':
    main()
