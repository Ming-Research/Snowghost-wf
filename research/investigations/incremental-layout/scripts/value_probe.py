#!/usr/bin/env python3
"""Reproduce Q78 diagnostic value comparisons and strict runtime falsifiers.

Home: research/investigations/incremental-layout/scripts; caller: run.sh
value-falsify. Sources and binaries are disposable copies under build/x5;
production files and interfaces are never modified. The copied probe declaration
is exactly the primary-owned diagnostic declaration. Probe timings are ignored,
never performance evidence. Retire this caller when the same independent raw
value checks and five falsifiers run in the regular style gate; keep the
investigation's criteria, source revisions and archived results.

An explicit --revision supplies every mother renderer file through git blobs.
Preparation resolves fixture NodeIds/element positions with --nodes-driver;
forward and inverse are separate invocations. --execute builds control seq/par
before five seq mutants. Compilation failure never counts as a killed mutant.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SCRIPT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parents[3]
TASK_ROOT = REPO_ROOT / 'build/x5/value-falsifiers'
SOURCES = ['control', 'same-id', 'identity-ranges', 'omit-tail', 'float-tolerance', 'signed-zero']
VARIANTS = ['control', 'control-par', *SOURCES[1:]]
PAGE = '<!doctype html><html><head><meta charset="utf-8"></head><body><div id="a">A probe</div><div id="b">B probe</div></body></html>\n'
SCENARIOS = [
    (1, 'width', 'width-move', '#a,#b{width:17px}#a.move{width:19px}', 'a'),
    (2, 'tracks', 'tracks-range', '#a{display:grid;grid-template-columns:[a]11px}#b{display:grid;grid-template-columns:[x]17px[y]19px}#a.move{grid-template-columns:[a]11px[b]13px}', 'a'),
    (3, 'tracks', 'tracks-last', '#a{display:grid;grid-template-columns:[a]11px}#b{display:grid;grid-template-columns:[x]17px[y]19px}#b.move{grid-template-columns:[x]17px[y]23px}', 'b'),
    (4, 'families', 'families-range', "#a{--f:'A';font-family:var(--f)}#b{--f:'B','C';font-family:var(--f)}#a.move{--f:'A','Extra'}", 'a'),
    (5, 'families', 'families-last', "#a{--f:'A';font-family:var(--f)}#b{--f:'B','C';font-family:var(--f)}#b.move{--f:'B','D'}", 'b'),
    (6, 'content', 'content-range', "#a::before{content:'a'}#b::before{content:'uv'}#a.move::before{content:'long' counter(n)}", 'a'),
    (7, 'content', 'content-last', "#a::before{content:'a'}#b::before{content:'uv'}#b.move::before{content:'uw'}", 'b'),
]

PROBE_DECLARATION = 'public fn x5_value_probe(old: &Styles, new: &Styles, scenario: u32, first_element: u32, second_element: u32) -> failure: u32 reads(old), reads(new) doc "Disposable X5 value-comparison probe: zero only when this scenario\'s raw identity/range preconditions and its hand-written expected layout flags all hold. Reads raw table values independently of the delta helpers used to compute flags. Never ships as a production interface.";'

BRIDGE_PATCHES = [
    ('alias compute_styles = pkg::style::compute_styles;\nalias flush = pkg::oracle::support::flush;\nalias layout_changes = pkg::style::layout_changes;\nalias line_end = pkg::oracle::support::line_end;\nalias nanoseconds_from = std::time::nanoseconds_from;\nalias now = std::time::now;\n',
     'alias compute_styles = pkg::style::compute_styles;\nalias flush = pkg::oracle::support::flush;\nalias layout_changes = pkg::style::layout_changes;\nalias x5_value_probe = pkg::style::x5_value_probe;\nalias line_end = pkg::oracle::support::line_end;\nalias nanoseconds_from = std::time::nanoseconds_from;\nalias now = std::time::now;\n'),
    ('const operation_reason: Array<u8, 28> = "the operation does not apply";\n\nconst syntax_reason: Array<u8, 20> = "unreadable operation";\n\nconst sheet_late_reason: Array<u8, 34> = "a style sheet line follows an edit";\n\n',
     'const operation_reason: Array<u8, 28> = "the operation does not apply";\n\nconst syntax_reason: Array<u8, 20> = "unreadable operation";\n\nconst probe_failed_label: Array<u8, 24> = "value probe failed code ";\n\nstruct ValueProbeSpec {\n  scenario: u32;\n  first_element: u32;\n  second_element: u32;\n}\n\nconst sheet_late_reason: Array<u8, 34> = "a style sheet line follows an edit";\n\n'),
    ('  }\n}\n\nfn add_script_sheets(store: &RuleStore, script: &[u8], environment: Environment, atoms: &AtomTable, notes: &Box<Slots<u8>>) -> ok: Bool reads(script), writes(store), writes(atoms), writes(notes) {\n  doc "Adds the text of each S line of the script as an author style sheet, and checks that every other line is empty, an edit (C, K or N) or a request (P), and that no S line follows an edit.";\n  let length = script^.len;\n',
     '  }\n}\n\nfn read_value_probe(script: &[u8]) -> found: Option<ValueProbeSpec> reads(script) {\n  doc "Reads the unique first-line V SCENARIO A_ELEMENT B_ELEMENT header; None on any invalid field.";\n  let length = script^.len;\n  if length < 8_u64 {\n    return None<ValueProbeSpec>();\n  }\n  if script^[0_u64] != 86_u8 {\n    return None<ValueProbeSpec>();\n  }\n  if script^[1_u64] != 32_u8 {\n    return None<ValueProbeSpec>();\n  }\n  let end = line_end(text: script, start: 0_u64);\n  if end > length {\n    return None<ValueProbeSpec>();\n  }\n  let (scenario_found, scenario, after_scenario) = read_number(line: &script^[0_u64..end], start: 2_u64);\n  let (a_found, a, after_a) = read_number(line: &script^[0_u64..end], start: after_scenario);\n  let (b_found, b, after_b) = read_number(line: &script^[0_u64..end], start: after_a);\n  let pair = band(scenario_found, a_found);\n  let fields = band(pair, b_found);\n  if fields {\n  } else {\n    return None<ValueProbeSpec>();\n  }\n  let expected_end = end +sat 1_u64;\n  if after_b != expected_end {\n    return None<ValueProbeSpec>();\n  }\n  if scenario < 1_u64 {\n    return None<ValueProbeSpec>();\n  }\n  if scenario > 7_u64 {\n    return None<ValueProbeSpec>();\n  }\n  if a >= 4294967295_u64 {\n    return None<ValueProbeSpec>();\n  }\n  if b >= 4294967295_u64 {\n    return None<ValueProbeSpec>();\n  }\n  let scenario_id = cvt::<u64, u32>(scenario);\n  let first = cvt::<u64, u32>(a);\n  let second = cvt::<u64, u32>(b);\n  let made = ValueProbeSpec(scenario: scenario_id, first_element: first, second_element: second);\n  return Some<ValueProbeSpec>(value: made);\n}\n\nfn add_script_sheets(store: &RuleStore, script: &[u8], environment: Environment, atoms: &AtomTable, notes: &Box<Slots<u8>>) -> ok: Bool reads(script), writes(store), writes(atoms), writes(notes) {\n  doc "Adds the text of each S line of the script as an author style sheet, and checks that every other line is empty, an edit (C, K or N) or a request (P), and that no S line follows an edit.";\n  let length = script^.len;\n'),
    ('    if start < end {\n      let kind = script^[start];\n      let body = start +sat 2_u64;\n      if kind == 83_u8 {\n        if edited {\n          put_failure(notes: notes, number: number, reason: &sheet_late_reason[0_u64..sheet_late_reason.len]);\n          return False();\n',
     '    if start < end {\n      let kind = script^[start];\n      let body = start +sat 2_u64;\n      if kind == 86_u8 {\n        if start != 0_u64 {\n          put_failure(notes: notes, number: number, reason: &syntax_reason[0_u64..syntax_reason.len]);\n          return False();\n        }\n        match read_value_probe(script: script) {\n          Some(..) => {\n          }\n          None() => {\n            put_failure(notes: notes, number: number, reason: &syntax_reason[0_u64..syntax_reason.len]);\n            return False();\n          }\n        }\n      } else if kind == 83_u8 {\n        if edited {\n          put_failure(notes: notes, number: number, reason: &sheet_late_reason[0_u64..sheet_late_reason.len]);\n          return False();\n'),
    ('fn run_delta(store: &RuleStore, document: &Document, atoms: &AtomTable, traversal: &Traversal, environment: Environment, script: &[u8], clock: &Clock, out: &OutputStream, err: &OutputStream, files: &HandleFactory) -> code: u8 reads(store), reads(traversal), reads(script), writes(document), writes(atoms), writes(clock), writes(out), writes(err), writes(files) waits {\n  doc "Computes the styles of the document, then applies each edit line of the script (C and K add and remove a class token, N changes nothing), recomputes the styles after it, and reports `edit I changed COUNT time_us US`, I counting the edits from 1, COUNT the elements pkg::style::layout_changes flags between the styles before and after the edit and US the microseconds that call took; the new styles become the old ones. For an edit number a P line names, the line `flags I` and the flagged indices, then the line `dump I` and the style dump of the styles after the edit, follow (P 0 names the unedited document and prints the dump alone). Returns 0, or 2 after naming the failure on err.";\n  let notes = box_slots_new::<u8>(capacity: 4096_u64);\n  let dumps = box_slots_new::<u64>(capacity: 16_u64);\n  collect_requests(script: script, dumps: &dumps);\n  let class_atom = class_index(atoms: atoms);\n',
     'fn run_delta(store: &RuleStore, document: &Document, atoms: &AtomTable, traversal: &Traversal, environment: Environment, script: &[u8], clock: &Clock, out: &OutputStream, err: &OutputStream, files: &HandleFactory) -> code: u8 reads(store), reads(traversal), reads(script), writes(document), writes(atoms), writes(clock), writes(out), writes(err), writes(files) waits {\n  doc "Computes the styles of the document, then applies each edit line of the script (C and K add and remove a class token, N changes nothing), recomputes the styles after it, and reports `edit I changed COUNT time_us US`, I counting the edits from 1, COUNT the elements pkg::style::layout_changes flags between the styles before and after the edit and US the microseconds that call took; the new styles become the old ones. For an edit number a P line names, the line `flags I` and the flagged indices, then the line `dump I` and the style dump of the styles after the edit, follow (P 0 names the unedited document and prints the dump alone). Returns 0, or 2 after naming the failure on err.";\n  let notes = box_slots_new::<u8>(capacity: 4096_u64);\n  let probe = match read_value_probe(script: script) {\n    Some(value: found) => {\n      give found;\n    }\n    None() => {\n      put_failure(notes: &notes, number: 1_u64, reason: &syntax_reason[0_u64..syntax_reason.len]);\n      let reported = flush(factory: files, output: err, buffer: &notes);\n      return 2_u8;\n    }\n  }\n  let dumps = box_slots_new::<u64>(capacity: 16_u64);\n  collect_requests(script: script, dumps: &dumps);\n  let class_atom = class_index(atoms: atoms);\n'),
    ('      let kind = script^[start];\n      let skipped_s = kind == 83_u8;\n      let skipped_p = kind == 80_u8;\n      let skipped = bor(skipped_s, skipped_p);\n      if skipped {\n      } else {\n        set edits = edits +sat 1_u64;\n',
     '      let kind = script^[start];\n      let skipped_s = kind == 83_u8;\n      let skipped_p = kind == 80_u8;\n      let skipped_v = kind == 86_u8;\n      let ordinary_skipped = bor(skipped_s, skipped_p);\n      let skipped = bor(ordinary_skipped, skipped_v);\n      if skipped {\n      } else {\n        set edits = edits +sat 1_u64;\n'),
    ('            report_style(err: err, files: files, failure: failure);\n            return 2_u8;\n          }\n        }\n        let started = now(clock: clock);\n        let changed = layout_changes(old: &old, new: &new);\n',
     '            report_style(err: err, files: files, failure: failure);\n            return 2_u8;\n          }\n        }\n        let probe_failure = x5_value_probe(old: &old, new: &new, scenario: probe.scenario, first_element: probe.first_element, second_element: probe.second_element);\n        if probe_failure != 0_u32 {\n          put_text(buffer: &notes, text: &probe_failed_label[0_u64..probe_failed_label.len]);\n          let wide_failure = cvt::<u32, u64>(probe_failure);\n          put_decimal(buffer: &notes, value: wide_failure);\n          put_byte(buffer: &notes, value: 32_u8);\n          put_text(buffer: &notes, text: &edit_label[0_u64..edit_label.len]);\n          put_decimal(buffer: &notes, value: edits);\n          put_byte(buffer: &notes, value: 10_u8);\n          let reported = flush(factory: files, output: err, buffer: &notes);\n          return 2_u8;\n        }\n        let started = now(clock: clock);\n        let changed = layout_changes(old: &old, new: &new);\n'),
]

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('patch must match exactly once: ' + repr(old))
    return text.replace(old, new, 1)


def function(text, name, transform):
    match = re.search(r'^fn ' + re.escape(name) + r'\(', text, re.M)
    if match is None:
        raise ValueError('missing function ' + name)
    following = re.search(r'^fn ', text[match.end():], re.M)
    end = match.end() + following.start() if following else len(text)
    before = text[match.start():end]
    after = transform(before)
    if before == after:
        raise ValueError('unchanged function ' + name)
    return text[:match.start()] + after + text[end:]


def range_guard(text, start_a, start_b, end_a, end_b):
    guard = ('  let endpoints_start = %s == %s;\n'
             '  let endpoints_end = %s == %s;\n'
             '  let endpoints_same = band(endpoints_start, endpoints_end);\n'
             '  if endpoints_same {\n  } else {\n    return False();\n  }\n') % (start_a, start_b, end_a, end_b)
    if '  let first = old^.' in text:
        marker = next(line + '\n' for line in text.splitlines() if line.startswith('  let second = new^.'))
        return once(text, marker, marker + guard)
    marker = next(line + '\n' for line in text.splitlines() if line.startswith('  doc '))
    return once(text, marker, marker + guard)


def mutants(source):
    marker = '  let first = old^.sizes.inner[old_at];\n'
    m1 = function(source, 'delta_size', lambda text: once(text, marker,
        '  let identity_same = old_id == new_id;\n  if identity_same {\n    return True();\n  }\n' + marker))
    m2 = function(source, 'delta_size', lambda text: once(text, marker,
        '  let identity_same = old_id == new_id;\n  if identity_same {\n  } else {\n    return False();\n  }\n' + marker))
    for name, arguments in [
        ('delta_families', ('first.families_start', 'second.families_start', 'first.families_end', 'second.families_end')),
        ('delta_track_list', ('first.first', 'second.first', 'first.end', 'second.end')),
        ('delta_content_list', ('first.first', 'second.first', 'first.end', 'second.end')),
        ('delta_generated', ('old_first', 'new_first', 'old_end', 'new_end')),
    ]:
        m2 = function(m2, name, lambda text, args=arguments: range_guard(text, *args))
    m3 = source
    for name in ('delta_track_list', 'delta_families', 'delta_generated'):
        m3 = function(m3, name, lambda text: once(text,
            '  for (offset in 0_u64..old_count) {\n',
            '  let compared_count = old_count -sat 1_u64;\n  for (offset in 0_u64..compared_count) {\n'))
    m4 = function(source, 'delta_float_value', lambda text: once(text,
        '  let first_word = exact_word(value: first);\n  let second_word = exact_word(value: second);\n  let same = first_word == second_word;\n',
        '  let distance = fsub.strict(first, second);\n  let magnitude = fabs(distance);\n  let same = fle(magnitude, 1.0e-6_f32);\n'))
    m5 = function(source, 'delta_float_value', lambda text: once(text,
        '  let first_word = exact_word(value: first);\n  let second_word = exact_word(value: second);\n',
        '  let first_word = reinterpret::<f32, u32>(first);\n  let second_word = reinterpret::<f32, u32>(second);\n'))
    return {'same-id': m1, 'identity-ranges': m2, 'omit-tail': m3,
            'float-tolerance': m4, 'signed-zero': m5}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(manifest):
    for name in SOURCES:
        folder = TASK_ROOT / 'sources' / name / 'renderer'
        actual = {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
        expected = dict(manifest['baseline_source_sha256'])
        if name != 'control':
            expected['style/delta.wf'] = manifest['variant_delta_sha256'][name]
        if actual != expected:
            raise ValueError('source-copy mismatch: ' + name)
    for relative, expected in manifest['input_sha256'].items():
        if sha(TASK_ROOT / relative) != expected:
            raise ValueError('input-copy mismatch: ' + relative)
    cases = manifest['cases']
    expected = {(scenario, direction) for scenario in range(1, 8) for direction in ('forward', 'inverse')}
    if {(case['scenario'], case['direction']) for case in cases} != expected or len(cases) != 14:
        raise ValueError('incomplete or duplicate scenario matrix')


def validate(process, wanted_element, expected_failure):
    if expected_failure is None:
        if process.returncode != 0 or process.stderr:
            raise ValueError('valid comparison/premise control failed: status=%d stderr=%r' % (process.returncode, process.stderr))
        edits, flags = [], []
        for line in process.stdout.decode('utf-8', errors='strict').splitlines():
            if line.startswith('edit '):
                match = re.fullmatch(r'edit (\d+) changed (\d+) time_us (\d+)', line)
                if not match:
                    raise ValueError('malformed edit record')
                edits.append((int(match[1]), int(match[2])))
            if line.startswith('flags '):
                match = re.fullmatch(r'flags (\d+)(.*)', line)
                if not match:
                    raise ValueError('malformed flags record')
                flags.append((int(match[1]), [int(value) for value in match[2].split()]))
        if edits != [(1, 1)] or flags != [(1, [wanted_element])]:
            raise ValueError('missing, duplicate or incorrect exact flags: %r %r' % (edits, flags))
    else:
        diagnostic = ('value probe failed code %d edit 1\n' % expected_failure).encode()
        if process.returncode != 2 or process.stderr != diagnostic or process.stdout:
            raise ValueError('falsifier did not reach its exact comparator assertion: status=%d stderr=%r stdout=%r' %
                             (process.returncode, process.stderr, process.stdout[:200]))



def certify_outer(source, ledger):
    start = source.index('fn layout_changes(')
    body = source[start:]
    loop = '  for (i in 0_u64..shorter) {'
    if body.count(loop) != 1:
        raise ValueError('outer element loop is not uniquely identified')
    line = source[:start + body.index(loop)].count('\n') + 1
    records = re.findall(r'^PAR loop\s+\./style/delta\.wf:' + str(line) + r'\s+loop\s+(.*)$', ledger, re.M)
    if len(records) != 1 or not records[0].startswith('permitted   eligible;'):
        raise ValueError('outer element loop lacks unique permitted ledger evidence: ' + repr(records))


def build(compiler, cache, name):
    source_name = 'control' if name == 'control-par' else name
    folder = TASK_ROOT / 'sources' / source_name / 'renderer'
    binary = TASK_ROOT / 'bin' / name
    if binary.exists():
        raise ValueError('refusing pre-existing binary: ' + str(binary))
    log = TASK_ROOT / 'evidence' / (name + '.build.txt')
    commands = [[str(compiler), '--graph', 'modules.wfg', '--check-module', module]
                for module in ('pkg::style', 'pkg::oracle::style')]
    command = [str(compiler)]
    if name == 'control-par':
        command += ['--par', '--par-ledger']
    if cache:
        command += ['--cache', str(cache), '--fragments', 'function']
    commands.append(command + ['--graph', 'modules.wfg', '--entry', 'style_oracle', '-o', str(binary)])
    with log.open('wb') as output:
        for command in commands:
            output.write((json.dumps(command) + '\n').encode())
            output.flush()
            process = subprocess.run(command, cwd=folder, stdout=output, stderr=subprocess.STDOUT)
            if process.returncode:
                raise ValueError(name + ': compilation failed; this is not a killed mutant; see ' + str(log))
    if name == 'control-par':
        certify_outer((folder / 'style/delta.wf').read_text(), log.read_text())
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError('successful command produced no executable: ' + name)
    return sha(binary)


def run_variant(name, cases):
    binary = TASK_ROOT / 'bin' / name
    observations, failures = [], []
    for case in cases:
        label = '%s-s%d-%s' % (name, case['scenario'], case['direction'])
        try:
            process = subprocess.run([str(binary), 'delta', case['script'], case['page'],
                                      'sources/control/renderer/style/ua.css'], cwd=TASK_ROOT,
                                     capture_output=True, env={**os.environ, 'WF_WORKERS': '4'})
        except OSError as error:
            failures.append(label + ': process invocation failed: ' + str(error))
            observations.append({'scenario': case['scenario'], 'direction': case['direction'], 'invocation_error': str(error)})
            continue
        (TASK_ROOT / 'evidence' / (label + '.stdout')).write_bytes(process.stdout)
        (TASK_ROOT / 'evidence' / (label + '.stderr')).write_bytes(process.stderr)
        expected = case['failures'].get(name)
        normalized = re.sub(rb'time_us \d+', b'time_us IGNORED', process.stdout)
        try:
            validate(process, case['expected_element'], expected)
            if name == 'control-par':
                seq_label = 'control-s%d-%s' % (case['scenario'], case['direction'])
                sequential = (TASK_ROOT / 'evidence' / (seq_label + '.stdout')).read_bytes()
                sequential = re.sub(rb'time_us \d+', b'time_us IGNORED', sequential)
                if normalized != sequential:
                    raise ValueError('complete seq/par outputs differ after removing time_us')
        except (ValueError, UnicodeError) as error:
            failures.append(label + ': ' + str(error))
        observations.append({'scenario': case['scenario'], 'direction': case['direction'],
                             'status': process.returncode, 'expected_failure': expected,
                             'expected_element': case['expected_element'],
                             'edited_node': case['edited_node'],
                             'diagnostic': process.stderr.decode(errors='replace'),
                             'normalized_stdout_sha256': hashlib.sha256(normalized).hexdigest()})
        print(label + ': recorded status %d' % process.returncode, flush=True)
    (TASK_ROOT / 'evidence' / (name + '.runtime.json')).write_text(json.dumps(observations, indent=2) + '\n')
    if failures:
        raise ValueError('\n'.join(failures))
    return observations


def mother_sources(revision):
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', revision + '^{commit}'], cwd=REPO_ROOT, text=True).strip()
    listing = subprocess.check_output(['git', 'ls-tree', '-rz', revision, 'renderer'], cwd=REPO_ROOT)
    entries = []
    for record in listing.split(b'\0'):
        if not record:
            continue
        metadata, path = record.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        relative = str(Path(path.decode()).relative_to('renderer'))
        if kind != 'blob' or mode not in ('100644', '100755') or '..' in Path(relative).parts:
            raise ValueError('unsupported mother source: ' + relative)
        entries.append((relative, mode, blob))
    raw = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=REPO_ROOT,
                                  input=('\n'.join(blob for _, _, blob in entries) + '\n').encode())
    position, sources, receipt = 0, {}, {}
    for relative, mode, blob in entries:
        end = raw.index(b'\n', position)
        actual_blob, kind, count = raw[position:end].decode().split()
        count = int(count)
        body = raw[end + 1:end + 1 + count]
        position = end + 2 + count
        if actual_blob != blob or kind != 'blob' or len(body) != count or raw[position - 1] != 10:
            raise ValueError('invalid git blob response: ' + relative)
        sources[relative] = body
        receipt[relative] = {'blob': blob, 'mode': mode, 'bytes': count,
                             'sha256': hashlib.sha256(body).hexdigest()}
    if position != len(raw) or not sources:
        raise ValueError('incomplete mother renderer')
    return revision, sources, receipt


def diagnostic_sources(mother):
    sources = dict(mother)
    sources['style/x5_value_probe.wf'] = (SCRIPT_ROOT / 'value_probe.wf').read_bytes()
    interface = sources['style/module.wfm'].decode()
    if 'public fn x5_value_probe(' in interface:
        raise ValueError('mother already has a probe declaration')
    sources['style/module.wfm'] = (interface.rstrip() + '\n\n' + PROBE_DECLARATION + '\n').encode()
    bridge = sources['oracle/style/delta.wf'].decode()
    for before, after in BRIDGE_PATCHES:
        bridge = once(bridge, before, after)
    sources['oracle/style/delta.wf'] = bridge.encode()
    return sources


def parse_nodes(output):
    elements, markers, arena = {}, {}, None
    for line in output.decode().splitlines():
        if line.startswith('E '):
            _, node, depth, name, descendants, position = line.split(' ')
            if int(node) in elements:
                raise ValueError('duplicate element node')
            elements[int(node)] = (name, int(position))
        elif line.startswith('T '):
            _, node, parent, size, data = line.split(' ', 4)
            if data in ('A probe', 'B probe'):
                if data in markers:
                    raise ValueError('duplicate marker')
                markers[data] = int(parent)
        elif line.startswith('N '):
            if arena is not None:
                raise ValueError('duplicate arena record')
            arena = int(line.split(' ')[1])
        else:
            raise ValueError('unexpected node record: ' + line)
    if arena is None or set(markers) != {'A probe', 'B probe'}:
        raise ValueError('missing node identities')
    a, b = markers['A probe'], markers['B probe']
    if a == b or elements[a][0] != 'div' or elements[b][0] != 'div':
        raise ValueError('markers are not distinct divs')
    return a, elements[a][1], b, elements[b][1]


def fixtures(mapping):
    a, ai, b, bi = mapping
    inputs, cases = {}, []
    requirements = {'same-id': {1: 'a'}, 'identity-ranges': {1: 'b', 2: 'b', 4: 'b', 6: 'b'},
                    'omit-tail': {3: 'b', 5: 'b', 7: 'b'},
                    'float-tolerance': {i: 901 for i in range(1, 8)},
                    'signed-zero': {i: 902 for i in range(1, 8)}}
    for scenario, group, name, sheet, edited in SCENARIOS:
        node = a if edited == 'a' else b
        for direction, operation in [('forward', 'C'), ('inverse', 'K')]:
            page = PAGE if direction == 'forward' else once(PAGE, 'id="' + edited + '"', 'id="' + edited + '" class="move"')
            page_path = 'inputs/' + name + '-' + direction + '.html'
            script_path = 'inputs/' + name + '-' + direction + '.edits'
            inputs[page_path] = page.encode()
            inputs[script_path] = ('V %d %d %d\nS %s\nP 1\n%s %d move\n' % (scenario, ai, bi, sheet, operation, node)).encode()
            failures = {}
            for mutant, wanted in requirements.items():
                code = wanted.get(scenario)
                if code is not None:
                    failures[mutant] = 1000 + (ai if code == 'a' else bi) if isinstance(code, str) else code
            cases.append({'scenario': scenario, 'direction': direction, 'page': page_path,
                          'script': script_path, 'a': ai, 'b': bi, 'edited_node': node,
                          'expected_element': ai if edited == 'a' else bi, 'failures': failures})
    return inputs, cases


def prepare(revision, nodes_driver):
    if TASK_ROOT.exists():
        raise ValueError('refusing to overwrite diagnostic directory: ' + str(TASK_ROOT))
    revision, mother, receipt = mother_sources(revision)
    baseline = diagnostic_sources(mother)
    delta = baseline['style/delta.wf'].decode()
    variants = mutants(delta)
    TASK_ROOT.mkdir(parents=True)
    for name in SOURCES:
        folder = TASK_ROOT / 'sources' / name / 'renderer'
        for relative, body in baseline.items():
            path = folder / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(variants[name].encode() if name != 'control' and relative == 'style/delta.wf' else body)
            path.chmod(int(receipt.get(relative, {'mode': '100644'})['mode'], 8) & 0o777)
    (TASK_ROOT / 'inputs').mkdir()
    (TASK_ROOT / 'inputs/nodes.html').write_text(PAGE)
    process = subprocess.run([str(nodes_driver), 'nodes', '0', 'inputs/nodes.html',
                              'sources/control/renderer/style/ua.css'], cwd=TASK_ROOT, capture_output=True)
    (TASK_ROOT / 'inputs/nodes.stdout').write_bytes(process.stdout)
    (TASK_ROOT / 'inputs/nodes.stderr').write_bytes(process.stderr)
    if process.returncode or process.stderr:
        raise ValueError('node listing failed: status=%d stderr=%r' % (process.returncode, process.stderr))
    inputs, cases = fixtures(parse_nodes(process.stdout))
    for relative, body in inputs.items():
        (TASK_ROOT / relative).write_bytes(body)
    manifest = {'source_revision': revision, 'mother_git_blobs': receipt,
                'baseline_source_sha256': {path: hashlib.sha256(body).hexdigest() for path, body in baseline.items()},
                'variant_delta_sha256': {name: hashlib.sha256(body.encode()).hexdigest() for name, body in variants.items()},
                'input_sha256': {str(path.relative_to(TASK_ROOT)): sha(path) for path in sorted((TASK_ROOT / 'inputs').iterdir())},
                'cases': cases, 'nodes_driver': str(nodes_driver), 'nodes_driver_sha256': sha(nodes_driver),
                'probe_sha256': sha(SCRIPT_ROOT / 'value_probe.wf'), 'runner_sha256': sha(Path(__file__))}
    (TASK_ROOT / 'patches').mkdir()
    for name, body in variants.items():
        patch = difflib.unified_diff(delta.splitlines(True), body.splitlines(True), fromfile='control/style/delta.wf', tofile=name + '/style/delta.wf')
        (TASK_ROOT / 'patches' / (name + '.patch')).write_text(''.join(patch))
    (TASK_ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared diagnostic copies from ' + revision + '; no compilation run.')
    return manifest


def verify_provenance(manifest, revision):
    if manifest['runner_sha256'] != sha(Path(__file__)) or manifest['probe_sha256'] != sha(SCRIPT_ROOT / 'value_probe.wf'):
        raise ValueError('runner or probe changed since preparation; use a new output directory')
    resolved, mother, receipt = mother_sources(revision)
    if resolved != manifest['source_revision'] or receipt != manifest['mother_git_blobs']:
        raise ValueError('mother revision or git blob provenance mismatch')
    baseline = diagnostic_sources(mother)
    expected = {path: hashlib.sha256(body).hexdigest() for path, body in baseline.items()}
    if expected != manifest['baseline_source_sha256']:
        raise ValueError('diagnostic changes differ from recorded mother + probe')
    variants = mutants(mother['style/delta.wf'].decode())
    if {name: hashlib.sha256(body.encode()).hexdigest() for name, body in variants.items()} != manifest['variant_delta_sha256']:
        raise ValueError('mutants differ from the exact declared patches')
    inputs, cases = fixtures(parse_nodes((TASK_ROOT / 'inputs/nodes.stdout').read_bytes()))
    if cases != manifest['cases']:
        raise ValueError('scenario expectations differ from declared fixtures')
    for relative, body in inputs.items():
        if (TASK_ROOT / relative).read_bytes() != body:
            raise ValueError('fixture changed: ' + relative)
    if (TASK_ROOT / 'inputs/nodes.html').read_text() != PAGE or (TASK_ROOT / 'inputs/nodes.stderr').read_bytes():
        raise ValueError('invalid node-listing control input or stderr')
    verify_sources(manifest)


def main():
    global TASK_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', help='explicit mother renderer commit')
    parser.add_argument('--output', type=Path, default=TASK_ROOT)
    parser.add_argument('--nodes-driver', type=Path)
    parser.add_argument('--compiler', type=Path, default=REPO_ROOT / 'whitefoot/compiler/target/gate/whitefootc')
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--controls', action='store_true', help='run process/parser stub controls only')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only', action='store_true')
    mode.add_argument('--verify-only', action='store_true', help='no compiler or renderer execution')
    mode.add_argument('--execute', action='store_true', help='requires host lock; builds diagnostic copies only')
    args = parser.parse_args()
    if args.controls:
        subprocess.run([sys.executable, str(SCRIPT_ROOT / 'value_probe_controls.py')], check=True)
        return
    if not args.revision:
        parser.error('--revision is required except for --controls')
    TASK_ROOT = args.output.resolve()
    if not TASK_ROOT.is_relative_to((REPO_ROOT / 'build/x5').resolve()) or TASK_ROOT == (REPO_ROOT / 'build/x5').resolve():
        raise ValueError('diagnostic output must be a child of this worktree build/x5')
    manifest_path = TASK_ROOT / 'manifest.json'
    if not manifest_path.exists():
        if args.verify_only or not args.nodes_driver:
            raise ValueError('unprepared directory; supply --nodes-driver for safe preparation')
        manifest = prepare(args.revision, args.nodes_driver.resolve())
    else:
        if args.prepare_only:
            raise ValueError('already prepared; use --verify-only or a new output directory')
        manifest = json.loads(manifest_path.read_text())
    verify_provenance(manifest, args.revision)
    print('PASS source verification: mother git blobs, exact diagnostic patches, fixtures and all source copies.')
    print('Plan: 7 binaries (6 seq, 1 par), 14 module checks, 98 isolated runtime calls; timings ignored.')
    if not args.execute:
        return
    if not os.environ.get('WHITEFOOT_CHECK_OWNER'):
        raise ValueError('--execute requires the host lock; use run.sh value-falsify --execute')
    compiler = args.compiler.resolve()
    compiler_hash = sha(compiler)
    (TASK_ROOT / 'bin').mkdir(exist_ok=True)
    (TASK_ROOT / 'evidence').mkdir(exist_ok=True)
    results = {'compiler_sha256': compiler_hash, 'source_revision': manifest['source_revision'], 'variants': {}}
    for name in VARIANTS:
        binary_hash = build(compiler, args.cache.resolve() if args.cache else None, name)
        if sha(compiler) != compiler_hash:
            raise ValueError('compiler changed during execution')
        observations = run_variant(name, manifest['cases'])
        results['variants'][name] = {'binary_sha256': binary_hash, 'observations': observations}
        (TASK_ROOT / 'evidence/results.json').write_text(json.dumps(results, indent=2) + '\n')
    verify_provenance(manifest, args.revision)
    print('PASS: updated seq/par controls agree completely after removing time_us; all five mutants built and failed at their declared exact runtime assertions.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, KeyError, subprocess.CalledProcessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        sys.exit(1)
