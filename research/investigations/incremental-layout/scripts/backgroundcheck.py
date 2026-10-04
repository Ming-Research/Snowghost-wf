#!/usr/bin/env python3
"""Independent Q77 background dependency checks, called by stylecheck.py and run.sh.

Run from repository root. Three tiny declared fixtures cover ordinary elements,
::before and ::after with 16 fixed class edits each. Expectations come from the
specified currentColor-or-positive-alpha fragment predicate, never a style dump.
Dumps resolve currentColor and round alpha, so they cannot recover that predicate.
These fixtures do not isolate current=True/raw-alpha=0: CSS stores currentColor
with a positive-alpha placeholder. Keep that internal coverage limit explicit.

All file/binary arguments are root-relative. Full streams, exits and digests are
saved in a new output directory; existing output is never overwritten. --self-test
runs synthetic parser controls and tiny subprocess stubs only. No timing is used
as performance evidence.
This script belongs to the existing investigation scripts directory and is removed
when Q77 is revoked or replaced by a maintained check covering the same dependency.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

STYLE_HEADER = (
    'index name display position float clear overflow-x overflow-y '
    'box-sizing visibility z-index width height min-width min-height max-width '
    'max-height top right bottom left margin-top margin-right margin-bottom '
    'margin-left padding-top padding-right padding-bottom padding-left border-top-width border-right-width border-bottom-width '
    'border-left-width border-top-style border-right-style border-bottom-style border-left-style border-top-color border-right-color border-bottom-color '
    'border-left-color font-family font-size font-weight font-style line-height color text-align '
    'text-indent text-transform white-space letter-spacing word-spacing vertical-align text-decoration-line list-style-type '
    'background-color flex-direction flex-wrap justify-content align-items align-content justify-items row-gap '
    'column-gap grid-template-columns grid-template-rows grid-template-areas grid-auto-flow grid-auto-columns grid-auto-rows order '
    'flex-grow flex-shrink flex-basis align-self justify-self grid-row-start grid-row-end grid-column-start '
    'grid-column-end aspect-ratio border-collapse border-spacing table-layout caption-side content counter-reset '
    'counter-increment counter-set quotes list-style-position overflow-wrap word-break column-count column-width '
    'column-fill break-inside unicode-bidi'
).split()
DECIMAL = r'(?:0|[1-9][0-9]*)'
STYLE = re.compile(r'edit (' + DECIMAL + r') changed (' + DECIMAL + r') time_us (' + DECIMAL + r')$')
FLAGS = re.compile(r'flags (' + DECIMAL + r')((?: ' + DECIMAL + r')*)$')
COUNTS = re.compile(r'style edit (' + DECIMAL + r') prepared (' + DECIMAL + r') contexts (' + DECIMAL + r') paragraphs (' + DECIMAL + r') held_entries (' + DECIMAL + r') entries (' + DECIMAL + r')$')
BASE = re.compile(r'base hash ([0-9a-f]{16}) bytes (' + DECIMAL + r')$')
LAYOUT = re.compile(r'edit (' + DECIMAL + r') hash ([0-9a-f]{16}) bytes (' + DECIMAL + r') inc same$')
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def relative(value):
    path = Path(value)
    require(not path.is_absolute() and '..' not in path.parts, 'file argument must be root-relative: ' + value)
    require(str(path) not in ('', '.'), 'file argument cannot be empty')
    return str(path)


class Reader:
    def __init__(self, output):
        require(bool(output) and output.endswith(b'\n'), 'empty or truncated stream')
        self.lines = output.decode('utf-8', errors='strict').splitlines(keepends=True)
        require(all(line.endswith('\n') and '\r' not in line for line in self.lines), 'invalid line endings')
        self.at = 0

    def take(self):
        require(self.at < len(self.lines), 'truncated output')
        line = self.lines[self.at][:-1]
        self.at += 1
        return line

    def match(self, pattern, reason):
        matched = pattern.fullmatch(self.take())
        require(matched is not None, reason)
        return matched

    def done(self):
        require(self.at == len(self.lines), 'extra/unexpected output')


def style_dump(reader, case, number):
    require(reader.take() == 'dump ' + str(number), 'missing, duplicated or unordered style dump')
    header = reader.take().split('\t')
    require(header == STYLE_HEADER, 'malformed style dump header')
    expected_rows = list(enumerate(case['elements']))
    if case['name'] != 'element':
        expected_rows.append((case['target_index'], '::' + case['name']))
    for index, name in expected_rows:
        row = reader.take().split('\t')
        require(len(row) == len(header) and row[0] == str(index) and row[1] == name,
                'missing, duplicated, unordered or malformed style dump row')
        require(all(field for field in row[:2]), 'empty style dump identity')


def validate_style(case, output):
    reader = Reader(output)
    style_dump(reader, case, 0)
    for wanted in case['edits']:
        number = wanted['number']
        edit = reader.match(STYLE, 'missing, duplicated, reordered or malformed style edit')
        require(int(edit[1]) == number and int(edit[2]) == wanted['changed_count'], 'wrong style ID or changed count')
        flags = reader.match(FLAGS, 'missing or malformed flags')
        indices = [int(value) for value in flags[2].split()]
        require(int(flags[1]) == number and indices == wanted['flags'], 'wrong/duplicate/unordered flags')
        style_dump(reader, case, number)
    reader.done()
    return re.sub(rb'(?m)^(edit [0-9]+ changed [0-9]+ time_us )\d+$', rb'\1IGNORED', output)


def fnv(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & ((1 << 64) - 1)
    return '%016x' % value


def rectangles(text):
    if text == '':
        return
    for rect in text.split(' '):
        fields = rect.split(',')
        require(len(fields) == 4 and all(NUMBER.fullmatch(value) for value in fields), 'malformed rectangle')


def layout_dump(reader, case, digest, size):
    first = reader.at
    for index, name in enumerate(case['elements']):
        row = reader.take().split('\t')
        require(len(row) == 6 and row[:3] == ['E', str(index), name], 'missing/duplicated/unordered layout element')
        require(row[3] == str(case['parents'][index]) and row[4] in ('n', 'i', 'b'), 'malformed layout element parent/display')
        require((row[4] == 'n') == (row[5] == ''), 'layout display/rectangle presence disagrees')
        rectangles(row[5])
    last_text = -1
    texts = []
    while reader.at < len(reader.lines) and reader.lines[reader.at].startswith('T\t'):
        row = reader.take().split('\t')
        require(len(row) == 4 and re.fullmatch(DECIMAL, row[1]) is not None and int(row[1]) > last_text,
                'malformed/duplicate/unordered layout text')
        require(re.fullmatch(r'-1|' + DECIMAL, row[2]) is not None, 'malformed layout text parent')
        last_text = int(row[1])
        texts.append((last_text, int(row[2])))
        require(row[3] != '', 'rendered text lacks rectangles')
        rectangles(row[3])
    require(texts == case['rendered_texts'], 'missing/unexpected body text identities')
    reader.match(re.compile(r'H\t' + DECIMAL + '$'), 'missing/malformed layout height')
    data = ''.join(reader.lines[first:reader.at]).encode('utf-8')
    require(len(data) == int(size) and fnv(data) == digest, 'dump bytes/hash mismatch')


def validate_layout(case, output):
    reader = Reader(output)
    base = reader.match(BASE, 'missing, duplicate or malformed base')
    layout_dump(reader, case, base[1], base[2])
    for wanted in case['edits']:
        number = wanted['number']
        counts = reader.match(COUNTS, 'missing/duplicate/unordered/malformed style work')
        require(int(counts[1]) == number, 'wrong work ID')
        values = [int(value) for value in counts.groups()[1:]]
        if wanted['layout_all_work_zero']:
            require(values == [0] * 5, 'presence-preserving edit performed layout work')
        else:
            require(values[2] > 0, 'presence-changing edit did not recompute a paragraph')
        edit = reader.match(LAYOUT, 'layout edit missing, malformed, full, refused or DIFF')
        require(int(edit[1]) == number, 'wrong/duplicate/unordered layout edit ID')
        layout_dump(reader, case, edit[2], edit[3])
    reader.done()
    return output


def validate_process(kind, case, output, stderr, status):
    require(status == 0, 'driver exited ' + str(status))
    require(stderr == b'', 'driver wrote stderr')
    return (validate_style if kind == 'style' else validate_layout)(case, output)


def compare(first, second):
    require(first == second, 'seq/par complete output differs')



EDIT_TOKENS = [('C', 'red'), ('K', 'red'), ('C', 'half'), ('C', 'blue'),
               ('K', 'blue'), ('K', 'half'), ('C', 'zero'), ('K', 'zero'),
               ('C', 'current'), ('C', 'textred'), ('K', 'textred'), ('C', 'blue'),
               ('K', 'blue'), ('K', 'current'), ('C', 'textred'), ('K', 'textred')]
PRESENCE_CHANGES = {1, 2, 3, 6, 9, 14}
CRITERIA = '''Q77 background predicate check criteria, recorded before driver runs.
Three fixed declared fixtures: ordinary element, generated ::before, generated
::after; generated content stays present and size/font inputs stay unchanged.
The fragment predicate is currentColor OR raw alpha > 0. Fixed expected flagged
edit numbers are 1,2,3,6,9,14, each flagging only the edited span's traversal
position. All other edits flag zero elements. Every presence change recomputes
at least one paragraph; every presence-preserving edit reports all five work
counts zero. Every retained edit must report inc same against a fresh rebuild.
All 16 edits/flags/counts/requested dumps must appear exactly once, in order.
Check complete seq/par outputs, ignoring only style time_us. Verify full layout
bytes/FNV and dump identities. Preserve all raw streams/exits/binary digests.
A nonzero exit, stderr, refusal, DIFF, missing/duplicate/bad record or seq/par
mismatch fails. Timings are not performance evidence.
The dump cannot recover currentColor or raw alpha; the fixed declarations,
not resolved dump colours, define this check's expected flags. CSS stores a
positive-alpha placeholder for currentColor, so these fixtures do not isolate
current=True/raw-alpha=0 against removal of only the current flag test.
--self-test results exercise parser failure paths, not renderer correctness.
'''


def sheet(name):
    suffix = '' if name == 'element' else '::' + name
    result = 'body{width:260px;font-family:serif;font-size:16px;line-height:20px}p{margin:0}.q77-base{color:rgba(0,0,0,0)}'
    content = '' if name == 'element' else 'content:"Prefix words ";'
    result += '.q77-base' + suffix + '{' + content + 'background-color:transparent}'
    colors = [('red', '#ff0000'), ('half', 'rgba(255,0,0,0.5)'),
              ('current', 'currentColor'), ('blue', '#0000ff'), ('zero', 'rgba(0,255,0,0)')]
    for token, color in colors:
        result += '.q77-' + token + suffix + '{background-color:' + color + '}'
    return result + '.q77-textred{color:#ff0000}'


def expected(name, elements, parents, target_node, target_index, texts):
    edits = []
    for number in range(1, 17):
        change = number in PRESENCE_CHANGES
        edits.append(dict(number=number, flags=[target_index] if change else [],
                          changed_count=int(change), layout_all_work_zero=not change))
    return dict(name=name, elements=elements, parents=parents, target_node=target_node,
                target_index=target_index, rendered_texts=texts, edits=edits)


def capture(binary, arguments, workers, prefix):
    command = [relative(binary)] + [relative(value) if at >= 2 else value for at, value in enumerate(arguments)]
    env = os.environ.copy()
    env['WF_WORKERS'] = str(workers)
    metadata = dict(command=command, workers=workers, exit=None)
    output, errors = b'', b''
    try:
        metadata['binary_sha256'] = hashlib.sha256(Path(binary).read_bytes()).hexdigest()
        process = subprocess.run(command, capture_output=True, env=env)
        output, errors = process.stdout, process.stderr
        metadata['exit'] = process.returncode
    except OSError as failure:
        metadata['start_error'] = str(failure)
    metadata['stdout_sha256'] = hashlib.sha256(output).hexdigest()
    metadata['stderr_sha256'] = hashlib.sha256(errors).hexdigest()
    Path(str(prefix) + '.stdout').write_bytes(output)
    Path(str(prefix) + '.stderr').write_bytes(errors)
    Path(str(prefix) + '.json').write_text(json.dumps(metadata, indent=2) + '\n')
    require(metadata['exit'] == 0, 'driver failed; see ' + str(prefix) + '.json')
    require(errors == b'', 'driver wrote stderr; see ' + str(prefix) + '.stderr')
    return output


def node_identities(name, output):
    reader = Reader(output)
    elements, parents, depths, node_positions, texts = [], [], [], {}, []
    target = None
    node_ids = set()
    arena = None
    while reader.at < len(reader.lines):
        line = reader.take()
        fields = line.split(' ', 4)
        if line.startswith('E '):
            fields = line.split(' ')
            require(len(fields) == 6 and all(re.fullmatch(DECIMAL, fields[at]) for at in (1, 2, 4, 5)), 'malformed node element')
            node, depth, tag, position = int(fields[1]), int(fields[2]), fields[3], int(fields[5])
            require(position == len(elements) and node not in node_positions, 'duplicate/unordered node element')
            while depths and depths[-1][0] >= depth:
                depths.pop()
            parents.append(depths[-1][1] if depths else -1)
            depths.append((depth, position))
            require(node not in node_ids, 'duplicate node identity')
            node_ids.add(node)
            node_positions[node] = position
            elements.append(tag)
            if tag == 'span':
                require(target is None, 'multiple target spans')
                target = (node, position)
        elif line.startswith('T '):
            require(len(fields) == 5 and all(re.fullmatch(DECIMAL, fields[at]) for at in (1, 2, 3)), 'malformed node text')
            require(int(fields[1]) not in node_ids, 'duplicate node text identity')
            node_ids.add(int(fields[1]))
            texts.append((int(fields[2]), fields[4]))
        elif line.startswith('N '):
            require(arena is None and len(fields) == 2 and re.fullmatch(DECIMAL, fields[1]), 'malformed/duplicate arena')
            arena = int(fields[1])
            reader.done()
        else:
            raise ValueError('unexpected node listing')
    require(arena is not None and target is not None and elements == ['html', 'head', 'meta', 'title', 'body', 'p', 'span', 'b'], 'incomplete fixture identities')
    require(all(node < arena for node in node_ids) and all(parent in node_positions for parent, text in texts), 'node outside arena or unknown text parent')
    visible = {'Leading words ', 'nested bold words', ' trailing words.'}
    rendered = [(ordinal, node_positions[parent]) for ordinal, (parent, text) in enumerate(texts) if text in visible]
    require(len(rendered) == 3, 'missing body text identities')
    return expected(name, elements, parents, *target, rendered)


def prepare(output, layout):
    cases = []
    for name in ('element', 'before', 'after'):
        page = output / (name + '.html')
        page.write_text('<!doctype html><html><head><meta charset="utf-8"><title>Background presence ' + name + '</title></head><body><p><span class="q77-base">Leading words <b>nested bold words</b> trailing words.</span></p></body></html>\n')
        listing = capture(layout, ['nodes', '0', str(page), 'renderer/style/ua.css'], 1, output / (name + '.nodes'))
        case = node_identities(name, listing)
        script = output / (name + '.edits')
        lines = ['S ' + sheet(name)] + ['P ' + str(number) for number in range(17)]
        lines += ['%s %d q77-%s' % (kind, case['target_node'], token) for kind, token in EDIT_TOKENS]
        script.write_text('\n'.join(lines) + '\n')
        case.update(page=str(page), script=str(script))
        cases.append(case)
    (output / 'expected.json').write_text(json.dumps(cases, indent=2) + '\n')
    return cases


def create_output(value):
    path = Path(relative(value))
    require(len(path.parts) > 1 and path.parts[0] == 'build', 'output must be a new directory under build/')
    path.mkdir(parents=True, exist_ok=False)
    return path


def execute(args, output):
    cases = prepare(output, args.layout_seq)
    failed = False
    for case in cases:
        for kind in ('style', 'layout'):
            normalized = []
            for label, workers in (('seq', 1), ('par', 4)):
                prefix = output / (case['name'] + '.' + kind + '.' + label)
                try:
                    raw = capture(getattr(args, kind + '_' + label),
                                  ['delta' if kind == 'style' else 'edit', case['script'], case['page'], 'renderer/style/ua.css'],
                                  workers, prefix)
                    normalized.append(validate_process(kind, case, raw, b'', 0))
                    print(case['name'] + ' ' + kind + ' ' + label + ': PASS (runtime)')
                except (ValueError, OSError, UnicodeError) as error:
                    print(str(prefix) + ': FAIL: ' + str(error), file=sys.stderr)
                    failed = True
            if len(normalized) == 2:
                try:
                    compare(*normalized)
                except ValueError as error:
                    print(case['name'] + ' ' + kind + ': FAIL: ' + str(error), file=sys.stderr)
                    failed = True
    require(not failed, 'Q77 checks failed; complete available evidence is in ' + str(output))
    print('PASS: Q77 3 fixtures x 16 edits x style/layout x seq/par; output ' + str(output))


def synthetic_style(case, micros=7):
    def dump(number):
        rows = list(enumerate(case['elements']))
        if case['name'] != 'element':
            rows.append((case['target_index'], '::' + case['name']))
        lines = ['dump ' + str(number), '\t'.join(STYLE_HEADER)]
        lines += ['\t'.join([str(index), name] + ['synthetic'] * (len(STYLE_HEADER) - 2)) for index, name in rows]
        return '\n'.join(lines) + '\n'
    result = dump(0)
    for edit in case['edits']:
        number = edit['number']
        result += 'edit %d changed %d time_us %d\n' % (number, edit['changed_count'], micros)
        result += 'flags ' + str(number) + ''.join(' ' + str(value) for value in edit['flags']) + '\n' + dump(number)
    return result.encode()


def synthetic_layout(case):
    dump = ''.join('E\t%d\t%s\t%d\tn\t\n' % (index, name, case['parents'][index]) for index, name in enumerate(case['elements']))
    dump += ''.join('T\t%d\t%d\t0,0,1,1\n' % (index, parent) for index, parent in case['rendered_texts']) + 'H\t720\n'
    raw = dump.encode()
    result = 'base hash %s bytes %d\n' % (fnv(raw), len(raw)) + dump
    for edit in case['edits']:
        counts = [0] * 5 if edit['layout_all_work_zero'] else [1] * 5
        result += 'style edit %d prepared %d contexts %d paragraphs %d held_entries %d entries %d\n' % (edit['number'], *counts)
        result += 'edit %d hash %s bytes %d inc same\n' % (edit['number'], fnv(raw), len(raw)) + dump
    return result.encode()


def self_test(output):
    rows = []
    def test(name, callback, reject=False):
        try:
            callback()
            failed = False
        except (ValueError, OSError, UnicodeError):
            failed = True
        require(failed == reject, 'control did not ' + ('reject ' if reject else 'accept ') + name)
        rows.append((name, 'REJECTED' if failed else 'ACCEPTED'))
    case = expected('element', ['html', 'head', 'meta', 'title', 'body', 'p', 'span', 'b'], [-1, 0, 1, 1, 0, 4, 5, 6], 9, 6, [(1, 6), (2, 7), (3, 6)])
    style, layout = synthetic_style(case), synthetic_layout(case)
    for kind, raw in [('style', style), ('layout', layout)]:
        check = validate_style if kind == 'style' else validate_layout
        test(kind + '-valid', lambda check=check, raw=raw: check(case, raw))
        for name, bad in [('empty', b''), ('truncated', raw[:-1]), ('extra', raw + b'garbage\n'), ('bad-utf8', raw + b'\xff\n')]:
            test(kind + '-' + name, lambda check=check, bad=bad: check(case, bad), True)
        test(kind + '-driver-exit', lambda kind=kind, raw=raw: validate_process(kind, case, raw, b'', 2), True)
        test(kind + '-driver-stderr', lambda kind=kind, raw=raw: validate_process(kind, case, raw, b'failed\n', 0), True)
    style_bad = {
        'wrong-count': style.replace(b'edit 1 changed 1', b'edit 1 changed 0', 1),
        'missing-edit': style.replace(b'edit 1 changed 1 time_us 7\n', b'', 1),
        'duplicate-edit': style.replace(b'edit 1 changed 1 time_us 7\n', b'edit 1 changed 1 time_us 7\n' * 2, 1),
        'unordered-edit': style.replace(b'edit 1 changed', b'edit 2 changed', 1),
        'bad-flags': style.replace(b'flags 1 6\n', b'flags 1 7\n', 1),
        'duplicate-flags': style.replace(b'flags 1 6\n', b'flags 1 6 6\n', 1),
        'missing-dump': style.replace(b'dump 1\n', b'', 1),
        'missing-row': re.sub(rb'(?m)^0\thtml[^\n]*\n', b'', style, count=1),
    }
    for name, bad in style_bad.items():
        test('style-' + name, lambda bad=bad: validate_style(case, bad), True)
    counts = b'style edit 1 prepared 1 contexts 1 paragraphs 1 held_entries 1 entries 1\n'
    layout_bad = {
        'missing-work': layout.replace(counts, b'', 1),
        'duplicate-work': layout.replace(counts, counts * 2, 1),
        'unordered-work': layout.replace(counts, counts.replace(b'edit 1', b'edit 2'), 1),
        'zero-paragraph': layout.replace(counts, counts.replace(b'paragraphs 1', b'paragraphs 0'), 1),
        'nonzero-on-zero-work': layout.replace(b'style edit 4 prepared 0', b'style edit 4 prepared 1', 1),
        'DIFF': layout.replace(b'inc same', b'inc DIFF', 1),
        'refused': layout.replace(b'inc same', b'inc refused', 1),
        'full': re.sub(rb'(?m)^edit 1[^\n]+', b'edit 1 full', layout, count=1),
        'wrong-hash': re.sub(rb'^base hash [0-9a-f]+', b'base hash 0000000000000000', layout, count=1),
        'wrong-bytes': re.sub(rb'^(base hash [0-9a-f]+ bytes )\d+', rb'\g<1>1', layout, count=1),
        'missing-height': layout.replace(b'H\t720\n', b'', 1),
        'duplicate-element': layout.replace(b'E\t0\thtml\t-1\tn\t\n', b'E\t0\thtml\t-1\tn\t\n' * 2, 1),
    }
    for name, bad in layout_bad.items():
        test('layout-' + name, lambda bad=bad: validate_layout(case, bad), True)
    for name in ('before', 'after'):
        pseudo = dict(case, name=name)
        raw = synthetic_style(pseudo)
        test(name + '-valid', lambda pseudo=pseudo, raw=raw: validate_style(pseudo, raw))
        bad = re.sub(rb'(?m)^6\t::[^\n]*\n', b'', raw, count=1)
        test(name + '-missing-generated-row', lambda pseudo=pseudo, bad=bad: validate_style(pseudo, bad), True)
    test('seq-par-timing-only', lambda: compare(validate_style(case, style), validate_style(case, synthetic_style(case, 19))))
    test('seq-par-style-dump-difference', lambda: compare(validate_style(case, style), validate_style(case, style.replace(b'synthetic', b'different', 1))), True)
    test('seq-par-count-difference', lambda: compare(validate_layout(case, layout), validate_layout(case, layout.replace(counts, counts.replace(b'prepared 1', b'prepared 2'), 1))), True)
    nodes = ("E 2 0 html 7 0\nE 3 1 head 2 1\nE 4 2 meta 0 2\nE 5 2 title 0 3\n"
             "T 6 5 26 Background presence element\nE 7 1 body 3 4\nE 8 2 p 2 5\nE 9 3 span 1 6\n"
             "T 10 9 14 Leading words \nE 11 4 b 0 7\nT 12 11 17 nested bold words\n"
             "T 13 9 16  trailing words.\nT 14 7 1 \\n\nN 15\n").encode()
    test('node-listing-valid', lambda: node_identities('element', nodes))
    for name, bad in {
        'missing-arena': nodes.replace(b'N 15\n', b''),
        'bad-element': nodes.replace(b'E 2 0 html', b'E bad 0 html', 1),
        'unordered-position': nodes.replace(b'E 3 1 head 2 1', b'E 3 1 head 2 2', 1),
        'duplicate-identity': nodes.replace(b'T 10 9 14', b'T 9 9 14', 1),
        'unknown-text-parent': nodes.replace(b'T 10 9 14', b'T 10 99 14', 1),
        'out-of-arena': nodes.replace(b'N 15', b'N 9'),
        'missing-target': nodes.replace(b'E 9 3 span', b'E 9 3 i', 1),
        'missing-body-text': nodes.replace(b'Leading words ', b'Other wording '),
    }.items():
        test('nodes-' + name, lambda bad=bad: node_identities('element', bad), True)
    test('refuse-existing-output', lambda: create_output(str(output)), True)
    test('absolute-binary-path', lambda: relative('/tmp/driver'), True)
    test('parent-path', lambda: relative('../driver'), True)
    stub = output / 'process-stub.sh'
    stub.write_text('#!/bin/sh\nprintf "sentinel\\n"\nprintf "failure\\n" >&2\nexit 2\n')
    stub.chmod(0o755)
    prefix = output / 'failed-process'
    test('preserve-failed-process', lambda: capture(str(stub), ['nodes', '0', 'page.html', 'renderer/style/ua.css'], 1, prefix), True)
    metadata = json.loads(Path(str(prefix) + '.json').read_text())
    require(metadata['exit'] == 2 and Path(str(prefix) + '.stdout').read_bytes() == b'sentinel\n' and Path(str(prefix) + '.stderr').read_bytes() == b'failure\n', 'failed process evidence was not preserved')
    missing = output / 'missing-process'
    test('preserve-process-start-failure', lambda: capture(str(output / 'missing-binary'), ['nodes', '0', 'page.html', 'renderer/style/ua.css'], 1, missing), True)
    require(json.loads(Path(str(missing) + '.json').read_text())['exit'] is None, 'failed start claimed an exit status')
    (output / 'controls.tsv').write_text('name\tresult\tscope\n' + ''.join(name + '\t' + result + '\tsynthetic only\n' for name, result in rows))
    print('PASS: %d synthetic controls; NO renderer executed; output %s' % (len(rows), output))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style-seq', default='build/style_oracle')
    parser.add_argument('--style-par', default='build/style_oracle_par')
    parser.add_argument('--layout-seq', default='build/layout_oracle_seq')
    parser.add_argument('--layout-par', default='build/layout_oracle_par')
    parser.add_argument('--output', default='build/x5/background-check')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    for kind in ('style', 'layout'):
        for label in ('seq', 'par'):
            relative(getattr(args, kind + '_' + label))
    output = create_output(args.output)
    (output / 'criteria.txt').write_text(CRITERIA)
    (output / 'run.json').write_text(json.dumps(dict(mode='synthetic' if args.self_test else 'runtime',
        command=sys.argv, checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
    if args.self_test:
        self_test(output)
    else:
        execute(args, output)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        sys.exit(1)
