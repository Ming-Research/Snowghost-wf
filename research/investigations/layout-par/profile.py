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
SECTIONS = ('.text', '.rodata', '.data')
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


def load_accounting():
    if 'layout_inventory' not in sys.modules:
        spec = importlib.util.spec_from_file_location('layout_inventory',
                                                    Path(__file__).with_name('inventory.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    return sys.modules['layout_inventory']


def parse_direct_calls(text, entry=ENTRY, symbol_address=None):
    """Require a real x86 direct call to the exported entry's exact address.

    Input is objdump -d --no-show-raw-insn, not a symbol listing. Header,
    comment, indirect-call, offset-target and non-call text cannot pass.
    """
    normalize = load_accounting().normalize_llvm_symbol
    entry = normalize(entry)
    header = re.compile(r'^\s*([0-9a-fA-F]+) <([^<>]+)>:\s*$')
    instruction = re.compile(r'^\s*([0-9a-fA-F]+):\s+(callq?)\s+([0-9a-fA-F]+) <([^<>]+)>\s*$')
    definitions = [int(match[1], 16) for line in text.splitlines()
                   if (match := header.fullmatch(line)) and normalize(match[2]) == entry]
    if len(definitions) != 1:
        raise ValueError(('objdump must contain exactly one exported entry definition', entry, definitions))
    address = definitions[0]
    if symbol_address is not None and address != symbol_address:
        raise ValueError(('objdump entry address differs from nm', entry, address, symbol_address))
    caller = None
    caller_raw = None
    header_raw = None
    callsites = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if match := header.fullmatch(line):
            caller_raw = match[2]
            caller = normalize(caller_raw)
            header_raw = line
            continue
        match = instruction.fullmatch(line)
        if not match or normalize(match[4]) != entry or int(match[3], 16) != address:
            continue
        if caller is None or caller == entry or caller.startswith(entry + '.body'):
            continue
        callsites.append(dict(caller=caller, caller_raw=caller_raw, header_raw=header_raw,
                              line=line_number,
                              instruction_address=match[1], mnemonic=match[2],
                              target_address=match[3], target=entry, target_raw=match[4], raw=line))
    if not callsites:
        raise ValueError(('no direct call instruction to the exported layout entry', entry))
    return callsites


def validate_join(left, right, revision, run_id, include_inputs=False, expected_page=None):
    """Reject artifacts that disagree about the source or pinned compiler."""
    keys = ('workflow_revision', 'source_revision', 'workflow_run_id', 'whitefoot_pin',
            'compiler_sha256', 'compiler_release_manifest', 'source_sha256', 'methodology_sha256')
    if include_inputs:
        keys += ('inputs', 'fonts')
    for key in keys:
        if key not in left or key not in right or left[key] != right[key]:
            raise ValueError(('artifact provenance differs or is missing', key))
    if left['workflow_revision'] != revision or left['source_revision'] != revision or left['workflow_run_id'] != run_id:
        raise ValueError('artifacts do not belong to this checked-out workflow run')
    if expected_page is not None and left.get('page') != expected_page:
        raise ValueError(('artifact page differs or is missing', expected_page, left.get('page')))


def parse_section_sizes(text):
    row = re.compile(r'^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+2\*\*\d+\s*$')
    sizes = {}
    for line in text.splitlines():
        match = row.fullmatch(line)
        if match and match[1] in SECTIONS:
            if match[1] in sizes:
                raise ValueError(('duplicate required section header', match[1]))
            sizes[match[1]] = int(match[2], 16)
    if set(sizes) != set(SECTIONS):
        raise ValueError(('missing required section headers', sorted(sizes)))
    return sizes


def parse_function_symbols(text):
    """Read every explicit ELF F entry, preserving duplicates and raw names."""
    normalize = load_accounting().normalize_llvm_symbol
    prefix = re.compile(r'^\s*([0-9a-fA-F]+)\s(.{7})\s+(.*)$')
    functions = []
    for line in text.splitlines():
        match = prefix.fullmatch(line)
        if not match:
            if re.match(r'^\s*[0-9a-fA-F]+\s+.*\bF\b', line):
                raise ValueError(('malformed function symbol flags', line))
            continue
        if match[2][6] != 'F':
            continue
        fields = match[3].split()
        if len(fields) == 4 and fields[2] in {'.hidden', '.protected', '.internal'}:
            fields.pop(2)
        if len(fields) != 3 or re.fullmatch(r'[0-9a-fA-F]+', fields[1]) is None:
            raise ValueError(('malformed function symbol size/name', line))
        raw = fields[2]
        functions.append(dict(raw=raw, normalized=normalize(raw), size=int(fields[1], 16), type='F'))
    if not functions:
        raise ValueError('function symbol table is empty or absent')
    return functions


def normalized_function_table(functions):
    return sorted((dict(name=entry['normalized'], size=entry['size']) for entry in functions),
                  key=lambda entry: (entry['name'], entry['size']))


def llvm_variants(functions):
    return [dict(raw=raw, normalized=normalized) for raw, normalized in
            sorted({(entry['raw'], entry['normalized']) for entry in functions
                    if entry['raw'] != entry['normalized']})]


def validate_page_drivers(identities):
    """Join equal selected sections and normalized function tables, not files."""
    if set(identities) != set(PAGES):
        raise ValueError(('page driver inventory must contain exactly the three pages', sorted(identities)))
    normalize = load_accounting().normalize_llvm_symbol
    reference = identities[PAGES[0]]
    for page, identity in identities.items():
        if re.fullmatch(r'[0-9a-f]{64}', identity.get('file_sha256', '')) is None:
            raise ValueError(('invalid whole-file integrity hash', page))
        sections = identity.get('sections', {})
        if set(sections) != set(SECTIONS):
            raise ValueError(('incomplete section inventory', page))
        for section, data in sections.items():
            if re.fullmatch(r'[0-9a-f]{64}', data.get('sha256', '')) is None or type(data.get('size')) is not int or data['size'] < 0:
                raise ValueError(('invalid section hash or size', page, section))
        functions = identity.get('functions', [])
        if not functions:
            raise ValueError(('missing function table', page))
        for function in functions:
            if not function.get('raw') or function.get('normalized') != normalize(function['raw']) or function.get('type') != 'F' or type(function.get('size')) is not int or function['size'] < 0:
                raise ValueError(('invalid raw/normalized function record', page))
        table = normalized_function_table(functions)
        variants = llvm_variants(functions)
        if identity.get('normalized_function_table') != table or identity.get('llvm_suffix_variants') != variants:
            raise ValueError(('function identity or LLVM audit does not match raw symbols', page))
        if sections != reference['sections'] or table != reference['normalized_function_table']:
            raise ValueError(('selected driver sections or normalized functions differ', page))
    return dict(common_sections=reference['sections'],
                common_function_table=reference['normalized_function_table'],
                whole_file_hash_variation=len({entry['file_sha256'] for entry in identities.values()}) > 1,
                llvm_symbol_variations={page: entry['llvm_suffix_variants'] for page, entry in identities.items()})


def identity_tool(folder, label, command):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('driver extraction runs only in CI')
    started = time.monotonic()
    status, expired, problem = None, False, None
    with (folder / (label + '.raw')).open('w') as stdout, (folder / (label + '.stderr')).open('w') as stderr:
        try:
            status = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=30).returncode
        except subprocess.TimeoutExpired:
            expired = True
        except OSError as error:
            problem = str(error)
    record = dict(label=label, command=list(map(str, command)), exit=status,
                  timeout=expired, spawn_error=problem, elapsed_seconds=time.monotonic() - started)
    with (folder / 'driver-identity-processes.jsonl').open('a') as output:
        output.write(json.dumps(record) + '\n')
    if expired or problem is not None or status != 0:
        raise RuntimeError(('driver identity tool failed', record))


def extract_driver_identity(driver, folder):
    """Inspect copied artifact bytes with an explicit disposable objcopy output."""
    before = digest(driver)
    try:
        identity_tool(folder, 'driver-section-headers', ['objdump', '-h', str(driver)])
        sizes = parse_section_sizes((folder / 'driver-section-headers.raw').read_text())
        identity_tool(folder, 'driver-function-symbols', ['objdump', '-t', str(driver)])
        functions = parse_function_symbols((folder / 'driver-function-symbols.raw').read_text())
        dumps = {section: folder / ('driver' + section + '.bin') for section in SECTIONS}
        if any(path.exists() for path in dumps.values()):
            raise ValueError('section dumps from a prior extraction are not valid new evidence')
        command = ['objcopy', *['--dump-section=' + section + '=' + str(path)
                               for section, path in dumps.items()], str(driver), '/dev/null']
        identity_tool(folder, 'driver-section-bytes', command)
        sections = {}
        for section, path in dumps.items():
            if not path.is_file() or path.stat().st_size != sizes[section]:
                raise ValueError(('section dump missing or size differs from header', section))
            sections[section] = dict(sha256=digest(path), size=sizes[section])
        identity = dict(file_sha256=before, sections=sections, functions=functions,
                        normalized_function_table=normalized_function_table(functions),
                        llvm_suffix_variants=llvm_variants(functions))
        write_json(folder / 'driver-identity.json', identity)
        return identity
    finally:
        after = digest(driver)
        write_json(folder / 'driver-extraction-integrity.json', dict(before_sha256=before, after_sha256=after))
        if after != before:
            raise ValueError('driver bytes changed during read-only identity extraction')


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
    suffixed = good.replace('wf_layout.lay_out', 'wf_layout.lay_out.llvm.14052526461537462625').replace(
        'wf_oracle.layout.drive.resume', 'wf_oracle.layout.drive.llvm.22.resume')
    normalized_calls = parse_direct_calls(suffixed, symbol_address=0x401000)
    if normalized_calls[0]['caller'] != observed[0]['caller'] or normalized_calls[0]['target'] != ENTRY or normalized_calls[0]['target_raw'] == ENTRY:
        raise AssertionError('LLVM-only direct-call spelling was not joined with raw evidence')
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
    page_provenance = {**provenance, 'page': 'ecma262',
                       'inputs': {'page': 'input-hash'}, 'fonts': {'font': 'font-hash'}}
    validate_join(page_provenance, dict(page_provenance), 'revision', 'run',
                  include_inputs=True, expected_page='ecma262')
    for key in ('inputs', 'fonts'):
        for wrong in ({**page_provenance, key: {'other': 'hash'}},
                      {name: value for name, value in page_provenance.items() if name != key}):
            try:
                validate_join(page_provenance, wrong, 'revision', 'run', include_inputs=True)
            except ValueError:
                rejected += 1
            else:
                raise AssertionError(('accepted differing or missing page inputs/fonts', key))
    for wrong in ({**page_provenance, 'page': 'html5'},
                  {name: value for name, value in page_provenance.items() if name != 'page'}):
        try:
            validate_join(wrong, provenance, 'revision', 'run', expected_page='ecma262')
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('accepted a mislabeled or missing artifact page')
    headers = ('  1 .text 00000003 00000100 00000100 00000100 2**4\n'
               '  2 .rodata 00000002 00000200 00000200 00000200 2**3\n'
               '  3 .data 00000001 00000300 00000300 00000300 2**3\n')
    if parse_section_sizes(headers) != {'.text': 3, '.rodata': 2, '.data': 1}:
        raise AssertionError('valid section header sizes were not read')
    symbols = ('00000100 l     F .text 00000010 wf__floor_stack_low.llvm.11\n'
               '00000110  w    F .text 00000010 wf__floor_stack_low.llvm.12\n'
               '00000120 g     F .text 00000008 .hidden wf_layout.lay_out\n'
               '00000300  w    O .data 00000001 weak_object\n'
               '00000130 g       .text 00000000 code_label\n')
    functions = parse_function_symbols(symbols)
    if len(functions) != 3 or functions[0]['normalized'] != 'wf__floor_stack_low' or functions[0]['size'] != 16 or functions[2]['raw'] != ENTRY:
        raise AssertionError('function flags, size or LLVM normalization were not read')
    for wrong in (headers.replace('  3 .data 00000001 00000300 00000300 00000300 2**3\n', ''),
                  headers + headers.splitlines(keepends=True)[0]):
        try:
            parse_section_sizes(wrong)
        except ValueError:
            pass
        else:
            raise AssertionError('accepted missing or duplicate required section header')
    for wrong in ('', symbols.replace('F .text', 'O .text'), symbols.replace('00000010', 'not-a-size')):
        try:
            parse_function_symbols(wrong)
        except ValueError:
            pass
        else:
            raise AssertionError('accepted absent or malformed function symbols')
    sections = {name: dict(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
                for name, data in (('.text', b'tex'), ('.rodata', b'ro'), ('.data', b'd'))}
    drivers = {}
    for index, page in enumerate(PAGES):
        rows = parse_function_symbols(symbols.replace('.llvm.11', f'.llvm.{100 + index}').replace('.llvm.12', f'.llvm.{200 + index}'))
        drivers[page] = dict(file_sha256='abc'[index] * 64, sections=sections,
                             functions=rows, normalized_function_table=normalized_function_table(rows),
                             llvm_suffix_variants=llvm_variants(rows))
    joined = validate_page_drivers(drivers)
    if not joined['whole_file_hash_variation'] or len(joined['common_function_table']) != 3:
        raise AssertionError('LLVM-only names and different file hashes did not join with multiplicity')
    wrong_drivers = [{page: value for page, value in drivers.items() if page != 'html5'},
                     {**drivers, 'extra': drivers['html5']}]
    def broken():
        return json.loads(json.dumps(drivers))
    for name in SECTIONS:
        wrong = broken()
        wrong['html5']['sections'][name]['sha256'] = 'f' * 64
        wrong_drivers.append(wrong)
    for field in ('functions', 'normalized_function_table'):
        wrong = broken()
        del wrong['html5'][field]
        wrong_drivers.append(wrong)
    wrong = broken()
    del wrong['html5']['sections']['.data']
    wrong_drivers.append(wrong)
    wrong = broken()
    wrong['html5']['file_sha256'] = ''
    wrong_drivers.append(wrong)
    for change in ('real-name', 'size', 'multiplicity', 'nonnumeric-llvm'):
        wrong = broken()
        rows = wrong['html5']['functions']
        if change == 'real-name':
            rows[0]['raw'] = rows[0]['normalized'] = 'different_function'
        elif change == 'size':
            rows[0]['size'] += 1
        elif change == 'multiplicity':
            rows.pop(0)
        else:
            rows[0]['raw'] = rows[0]['normalized'] = 'wf__floor_stack_low.llvm.notnumeric'
        wrong['html5']['normalized_function_table'] = normalized_function_table(rows)
        wrong['html5']['llvm_suffix_variants'] = llvm_variants(rows)
        wrong_drivers.append(wrong)
    for wrong in wrong_drivers:
        try:
            validate_page_drivers(wrong)
        except ValueError:
            pass
        else:
            raise AssertionError(('accepted incomplete or differing page driver inventory', wrong))
    print(f'handmade dry-run passed; {len(variants) + 1} corrupt callsite artifacts, '
          f'{rejected} corrupt joins and {len(wrong_drivers)} corrupt page-driver inventories rejected')


class Investigation:
    def __init__(self, mode, page=None):
        self.mode = mode
        self.page = page
        self.collection_entry = ENTRY
        self.started = time.monotonic()
        self.budget = min(BUDGET_SECONDS[mode], float(os.environ['LAYOUT_PAR_DEADLINE']) - time.time())
        if self.budget <= RESERVE_SECONDS:
            raise ValueError(f'{mode} job deadline leaves no harness budget')
        self.accounting = load_accounting()

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
        record = dict(label=label, mode=self.mode, page=self.page, command=list(map(str, command)),
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
            page=self.page,
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
                   if line.split() and self.accounting.normalize_llvm_symbol(line.split()[-1]) == ENTRY]
        if len(symbols) != 1 or len(symbols[0]) != 3 or symbols[0][1] not in {'t', 'T'}:
            raise ValueError(('exact layout entry missing or ambiguous; do not change compiler or source',
                              ENTRY, symbols))
        address = int(symbols[0][0], 16)
        self.collection_entry = symbols[0][-1]
        self.run('disassembly-seq', ['objdump', '-d', '--no-show-raw-insn', str(OUT / 'layout-seq')], 60)
        callsites = parse_direct_calls((OUT / 'disassembly-seq.raw').read_text(), symbol_address=address)
        write_json(OUT / 'direct-calls.json', dict(entry=ENTRY, entry_raw=self.collection_entry,
                                                nm_raw=symbols[0], symbol_address=hex(address), callsites=callsites))
        provenance = json.loads((OUT / 'provenance.json').read_text())
        provenance['collection_entry'] = self.collection_entry
        provenance['collection_entry_normalized'] = ENTRY
        write_json(OUT / 'provenance.json', provenance)

    def profile(self, page, count, cap, label=None):
        label = label or page
        driver = str((OUT / 'layout-seq').relative_to(ROOT))
        command = ['valgrind', '--tool=callgrind', '--collect-atstart=no',
                   '--toggle-collect=' + self.collection_entry,
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
        self.profile(self.page, 0, 240, label=self.page + '-zero')
        pilot = self.profile(self.page, 1, 300)
        # This one bounded pass is also this page's retained profile. There is
        # no larger repetition batch or extrapolation to another page.
        selection = dict(page=self.page, pilot=pilot, repetitions=1,
                         profile_reused=True, timeout_seconds=300,
                         remaining_budget_seconds=self.remaining(),
                         scale_rule='one bounded pass for this page; no extrapolation or larger batch',
                         evidence_scope='administrative wall-time budget, no performance conclusion')
        write_json(OUT / 'scale-selection.json', selection)


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=('ledger', 'profile'))
    parser.add_argument('--page', choices=PAGES)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.dry_run:
        if args.mode is not None or args.page is not None:
            parser.error('--dry-run accepts no job mode or page')
        dry_run()
        return
    if args.mode is None:
        parser.error('expected ledger or profile')
    if (args.mode == 'profile') != (args.page is not None):
        parser.error('profile requires --page; ledger accepts no --page')
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('this investigation runs only in CI')
    OUT = ROOT / ('build/layout-par-ledger' if args.mode == 'ledger' else 'build/layout-par-pages/' + args.page)
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'processes.jsonl').exists():
        raise ValueError('output directory must not contain a prior invocation')
    started = time.monotonic()
    investigation = None
    status = dict(status='incomplete', mode=args.mode, page=args.page,
                  started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    try:
        investigation = Investigation(args.mode, args.page)
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
