"""Temporary independent CI ledger/profile jobs for par-inventory.yml.

Keep the untouched production driver and pinned compiler. Remove this harness
and the workflow once the evidence is archived. inventory.py owns accounting.
"""

import argparse
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
BUDGET_SECONDS = {'profile': 25 * 60, 'ledger': 42 * 60}
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


def parse_direct_calls(text, entry=ENTRY, symbol_address=None):
    """Require a real x86 direct call to the exported entry's exact address.

    Input is objdump -d --no-show-raw-insn, not a symbol listing. Header,
    comment, indirect-call, offset-target and non-call text cannot pass.
    """
    header = re.compile(r'^\s*([0-9a-fA-F]+) <([^<>]+)>:\s*$')
    instruction = re.compile(r'^\s*([0-9a-fA-F]+):\s+(callq?)\s+([0-9a-fA-F]+) <([^<>]+)>\s*$')
    definitions = [int(match[1], 16) for line in text.splitlines()
                   if (match := header.fullmatch(line)) and match[2] == entry]
    if len(definitions) != 1:
        raise ValueError(('objdump must contain exactly one exported entry definition', entry, definitions))
    address = definitions[0]
    if symbol_address is not None and address != symbol_address:
        raise ValueError(('objdump entry address differs from nm', entry, address, symbol_address))
    caller = None
    callsites = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if match := header.fullmatch(line):
            caller = match[2]
            continue
        match = instruction.fullmatch(line)
        if not match or match[4] != entry or int(match[3], 16) != address:
            continue
        if caller is None or caller == entry or caller.startswith(entry + '.body'):
            continue
        callsites.append(dict(caller=caller, line=line_number,
                              instruction_address=match[1], mnemonic=match[2],
                              target_address=match[3], target=entry, raw=line))
    if not callsites:
        raise ValueError(('no direct call instruction to the exported layout entry', entry))
    return callsites


def validate_join(left, right, revision, run_id):
    """Reject artifacts that disagree about the source or pinned compiler."""
    keys = ('workflow_revision', 'source_revision', 'workflow_run_id', 'whitefoot_pin',
            'compiler_sha256', 'compiler_release_manifest', 'source_sha256', 'methodology_sha256')
    for key in keys:
        if key not in left or key not in right or left[key] != right[key]:
            raise ValueError(('profile/ledger provenance differs or is missing', key))
    if left['workflow_revision'] != revision or left['source_revision'] != revision or left['workflow_run_id'] != run_id:
        raise ValueError('artifacts do not belong to this checked-out workflow run')


def dry_run():
    # Handmade disassembly only: no subprocess, filesystem fixture or build.
    good = ('0000000000400100 <wf_oracle.layout.drive.resume>:\n'
            '  400110: call 401000 <wf_layout.lay_out>\n'
            '  400115: callq 401000 <wf_layout.lay_out>\n'
            '0000000000401000 <wf_layout.lay_out>:\n'
            '  401010: ret\n')
    observed = parse_direct_calls(good, symbol_address=0x401000)
    if len(observed) != 2 or observed[0]['caller'] != 'wf_oracle.layout.drive.resume':
        raise AssertionError('valid direct call instructions were not recognized')
    variants = [
        good.replace('  400110: call 401000 <wf_layout.lay_out>\n', '').replace('  400115: callq 401000 <wf_layout.lay_out>\n', ''),
        good.replace('call ', 'jmp ').replace('callq ', 'jmp '),
        good.replace('<wf_layout.lay_out>\n', '<wf_layout.other>\n'),
        good.replace('<wf_layout.lay_out>\n', '<wf_layout.lay_out+0x1>\n'),
        good.replace('call 401000', 'call *%rax # 401000').replace('callq 401000', 'callq *%rax # 401000'),
        good.replace('  400110:', '# 400110:').replace('  400115:', '# 400115:'),
        good.replace('call 401000', '.quad 401000').replace('callq 401000', '.quad 401000'),
        good.replace('call 401000', 'call 402000').replace('callq 401000', 'callq 402000'),
        good.replace('0000000000400100 <wf_oracle.layout.drive.resume>:\n', ''),
        good.replace('<wf_oracle.layout.drive.resume>:', '<wf_layout.lay_out.body.llvm.1>:'),
        good + '0000000000401000 <wf_layout.lay_out>:\n',
    ]
    for wrong in variants:
        try:
            parse_direct_calls(wrong, symbol_address=0x401000)
        except ValueError:
            pass
        else:
            raise AssertionError(('accepted invalid direct-call evidence', wrong))
    try:
        parse_direct_calls(good, symbol_address=0x402000)
    except ValueError:
        pass
    else:
        raise AssertionError('accepted nm/objdump address mismatch')
    provenance = dict(workflow_revision='revision', source_revision='revision', workflow_run_id='run',
                      whitefoot_pin='pin', compiler_sha256='compiler', compiler_release_manifest={'commit': 'compiler-source'},
                      source_sha256={'source': 'hash'}, methodology_sha256={'parser': 'hash'})
    validate_join(provenance, dict(provenance), 'revision', 'run')
    rejected = 0
    for key in provenance:
        for wrong in ({**provenance, key: 'mismatch'}, {name: value for name, value in provenance.items() if name != key}):
            try:
                validate_join(provenance, wrong, 'revision', 'run')
            except ValueError:
                rejected += 1
            else:
                raise AssertionError(('accepted mismatched or missing join provenance', key))
    for revision, run_id in (('other-revision', 'run'), ('revision', 'other-run')):
        try:
            validate_join(provenance, dict(provenance), revision, run_id)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('accepted artifacts from another workflow run')
    print(f'handmade dry-run passed; {len(variants) + 1} corrupt callsite artifacts and {rejected} corrupt joins rejected')


class Investigation:
    def __init__(self, mode):
        self.mode = mode
        self.started = time.monotonic()
        self.budget = min(BUDGET_SECONDS[mode], float(os.environ['LAYOUT_PAR_DEADLINE']) - time.time())
        if self.budget <= RESERVE_SECONDS:
            raise ValueError(f'{mode} job deadline leaves no harness budget')
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
        record = dict(label=label, mode=self.mode, command=list(map(str, command)),
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
        commands = [
            ('revision', ['git', 'rev-parse', 'HEAD']),
            ('submodules', ['git', 'submodule', 'status']),
            ('worktree', ['git', 'status', '--porcelain']),
            ('clang-version', ['/usr/bin/clang', '--version']),
            ('linker-version', ['ld.lld', '--version']),
            ('machine', ['lscpu']),
        ]
        if self.mode == 'profile':
            commands += [('profiler-version', ['valgrind', '--version']),
                         ('font-packages', ['dpkg-query', '-W', 'fonts-*'])]
        for label, command in commands:
            self.run(label, command, 10)
        files, fonts = [], []
        if self.mode == 'profile':
            files = [ROOT / DATA / (page + '.html') for page in PAGES]
            files += [ROOT / mapping.rsplit('=', 1)[1]
                      for page in PAGES for mapping in sheets(page)]
            files += [ROOT / 'renderer/style/ua.css']
            fonts = sorted((ROOT / 'build/fonts').glob('*'))
            if not fonts or any(not path.is_file() or path.is_symlink() for path in fonts):
                raise ValueError('oracle fonts must be a nonempty set of copied files')
        sources = sorted(path for path in (ROOT / 'renderer').rglob('*')
                         if path.is_file() and (path.suffix in {'.wf', '.wfm'} or path.name == 'modules.wfg'))
        metadata = dict(
            mode=self.mode,
            workflow_revision=os.environ['GITHUB_SHA'],
            source_revision=(OUT / 'revision.raw').read_text().strip(),
            workflow_run_id=os.environ['GITHUB_RUN_ID'],
            system=platform.uname()._asdict(),
            compiler_release_manifest=json.loads(compiler.with_name('whitefoot-release.json').read_text()),
            whitefoot_pin=(ROOT / 'whitefoot.pin').read_text(),
            compiler_sha256=digest(compiler),
            source_sha256={str(path.relative_to(ROOT)): digest(path) for path in sources},
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
            if not sources:
                continue
            destination = OUT / folder
            destination.mkdir()
            for source in sources:
                shutil.copyfile(source, destination / source.name)

    def build(self, compiler):
        name = 'par' if self.mode == 'ledger' else 'seq'
        flags = ['--par', '--par-ledger'] if self.mode == 'ledger' else []
        cache = ROOT / 'build' / ('layout-par-cache-' + name)
        if cache.exists():
            raise ValueError(('fresh build cache required', str(cache)))
        output = OUT / ('layout-' + name)
        command = [str(compiler), '--cache', str(cache), '--fragments', 'function',
                   *flags, '--graph', 'modules.wfg', '--entry', 'layout_oracle',
                   '-o', str(output)]
        self.run('build-' + name, command, 40 * 60 if self.mode == 'ledger' else 600,
                 cwd=ROOT / 'renderer',
                 stdout_name='par-ledger.log' if name == 'par' else 'build-seq.log')
        write_json(OUT / 'drivers.json', {
            name: dict(sha256=digest(output), path=str(output.relative_to(ROOT)))})
        if self.mode == 'ledger':
            self.run('source-ledger-coverage', [sys.executable, '-I',
                     'research/investigations/layout-par/inventory.py', 'inventory',
                     '--root', '.', '--ledger', str((OUT / 'par-ledger.log').relative_to(ROOT)),
                     '--out', str(OUT.relative_to(ROOT))], 60)

    def entry_check(self):
        self.run('symbols-seq', ['nm', '--defined-only', str(OUT / 'layout-seq')], 15)
        symbols = [line.split() for line in (OUT / 'symbols-seq.raw').read_text().splitlines()
                   if line.split() and line.split()[-1] == ENTRY]
        if len(symbols) != 1 or len(symbols[0]) != 3 or symbols[0][1] not in {'t', 'T'}:
            raise ValueError(('exact layout entry missing or ambiguous; do not change compiler or source',
                              ENTRY, symbols))
        address = int(symbols[0][0], 16)
        self.run('disassembly-seq', ['objdump', '-d', '--no-show-raw-insn', str(OUT / 'layout-seq')], 60)
        callsites = parse_direct_calls((OUT / 'disassembly-seq.raw').read_text(), symbol_address=address)
        write_json(OUT / 'direct-calls.json', dict(entry=ENTRY, symbol_address=hex(address), callsites=callsites))

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
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=('ledger', 'profile'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.dry_run:
        if args.mode is not None:
            parser.error('--dry-run accepts no job mode')
        dry_run()
        return
    if args.mode is None:
        parser.error('expected ledger or profile')
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('this investigation runs only in CI')
    OUT = ROOT / ('build/layout-par-ledger' if args.mode == 'ledger' else 'build/layout-par')
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'processes.jsonl').exists():
        raise ValueError('output directory must not contain a prior invocation')
    started = time.monotonic()
    investigation = None
    status = dict(status='incomplete', mode=args.mode,
                  started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    try:
        investigation = Investigation(args.mode)
        pin = (ROOT / 'whitefoot.pin').read_text().strip()
        match = re.fullmatch(r'release = (wf-(?:exp-)?[0-9a-f]{12})', pin)
        if not match:
            raise ValueError('unexpected Whitefoot pin')
        compiler = ROOT / 'build/whitefoot' / match[1] / 'whitefootc'
        if args.mode == 'profile':
            investigation.inputs()
        investigation.provenance(compiler)
        investigation.build(compiler)
        if args.mode == 'profile':
            investigation.entry_check()
            investigation.collect()
            status['status'] = 'profiles-complete-accounting-pending'
        else:
            status['status'] = 'ledger-complete-coverage-checked'
    except Exception as error:
        status['reason'] = repr(error)
        raise
    finally:
        status['elapsed_seconds'] = time.monotonic() - started
        status['remaining_budget_seconds'] = investigation.remaining() if investigation else None
        write_json(OUT / ('ledger-status.json' if args.mode == 'ledger' else 'profile-status.json'), status)


if __name__ == '__main__':
    main()
