"""Temporary hosted callgrind experiment; remove after archiving its artifact.

The ordinary sequential E1 driver and unchanged script generator own the work.
No renderer instrumentation or compiler flags change generated code. One marker
per process avoids Valgrind 3.22's option-trie shadowing. A common surviving
text-update wrapper is preferred; otherwise sum separately gated text_changed
and update replays of the same script. These scopes exclude timestamp calls.
Call-edge Ir is inclusive: conserve only exclusive rows against totals:, never
summary:. Inclusive rows overlap and do not describe causal cycle costs.
"""
from collections import Counter, defaultdict
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

TARGETS = ('set_links', 'next_glyphs', 'set_glyph_class', 'add_scalar_piece')
COHORTS = ('base', 'candidate')
OUT = Path('build/inline-profile')


class ProfileTimeout(RuntimeError):
    pass


class BudgetExhausted(RuntimeError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target(symbol):
    return next((name for name in TARGETS if re.search(r'(?:^|[.:])' + name, symbol)), None)


def parse_callgrind(text):
    """Parse Ir, position vectors, compressed fn/cfn IDs and inclusive edges."""
    identifiers, own, edges, calls = {}, Counter(), Counter(), Counter()
    caller = callee = None
    pending = None
    positions = events = summary = totals = None

    def symbol(value):
        match = re.fullmatch(r'\((\d+)\)(?: (.+))?', value)
        if not match:
            if not value:
                raise ValueError('empty function name')
            return value
        index, name = match.groups()
        if name is not None:
            if index in identifiers and identifiers[index] != name:
                raise ValueError('function ID redefined')
            identifiers[index] = name
        if index not in identifiers:
            raise ValueError('undefined function ID')
        return identifiers[index]

    def vector(value):
        fields = value.split()
        if events is None or len(fields) > len(events) or any(not f.isdigit() for f in fields):
            raise ValueError('invalid event vector')
        return (list(map(int, fields)) + [0] * len(events))[events.index('Ir')]

    for line in text.splitlines():
        if line.startswith('positions: '):
            if positions is not None or not line.split()[1:]:
                raise ValueError('invalid or duplicate positions')
            positions = len(line.split()) - 1
        elif line.startswith('events: '):
            if events is not None:
                raise ValueError('duplicate events')
            events = line.split()[1:]
            if len(set(events)) != len(events) or 'Ir' not in events:
                raise ValueError('missing or repeated Ir event')
        elif line.startswith('summary: '):
            if summary is not None:
                raise ValueError('duplicate summary')
            summary = vector(line[9:])
        elif line.startswith('totals: '):
            if totals is not None:
                raise ValueError('duplicate totals')
            totals = vector(line[8:])
        elif line.startswith(('fn=', 'cfn=')):
            if pending is not None:
                raise ValueError('call has no associated cost row')
            if line.startswith('fn='):
                caller, callee = symbol(line[3:]), None
            else:
                callee = symbol(line[4:])
        elif line.startswith('calls='):
            fields = line[6:].split()
            if caller is None or callee is None or pending is not None or not fields or not fields[0].isdigit():
                raise ValueError('invalid call association')
            if positions is None or len(fields) != positions + 1:
                raise ValueError('invalid call position vector')
            pending = int(fields[0])
        elif line and line[0] in '*+-0123456789':
            fields = line.split()
            if positions is None or caller is None or len(fields) < positions:
                raise ValueError('incomplete cost row')
            if any(not re.fullmatch(r'\*|[+-]?\d+|0x[0-9a-fA-F]+', f) for f in fields[:positions]):
                raise ValueError('invalid position')
            cost = vector(' '.join(fields[positions:]))
            if pending is None:
                own[caller] += cost
            else:
                edges[caller, callee] += cost
                calls[caller, callee] += pending
                pending = None
    if pending is not None or positions is None or summary is None or totals is None or sum(own.values()) != totals:
        raise ValueError('exclusive rows do not reconcile with totals footer')
    return dict(total=totals, summary=summary, own=own, edges=edges, calls=calls)


def parse_objdump(text):
    blocks, current = {}, None
    for line in text.splitlines(keepends=True):
        match = re.fullmatch(r'([0-9a-fA-F]+) <(.+)>:\s*', line.strip())
        if match:
            # Local symbols such as coroutine resume/destroy pieces repeat
            # across modules; later copies are keyed by their address.
            current = match[2]
            if current in blocks:
                current = f'{current}@{match[1]}'
                if current in blocks:
                    raise ValueError('duplicate disassembly address')
            blocks[current] = line
        elif current:
            blocks[current] += line
    if not blocks:
        raise ValueError('no disassembly functions')
    return blocks


def dry_run():
    # Hand-made, deliberately different summary: footer conservation is decisive.
    sample = ('positions: instr line\nevents: Ir Dr\nsummary: 999 0\n'
              'fn=(1) wf_caller\n0x10 1 12 0\ncfn=(2) wf_dom.set_links.body\n'
              'calls=3 0x20 2\n* +1 9\nfn=(2)\n0x20 2 9\ntotals: 21 0\n')
    parsed = parse_callgrind(sample)
    if parsed['total'] != 21 or parsed['own']['wf_caller'] != 12 or parsed['edges']['wf_caller', 'wf_dom.set_links.body'] != 9 or parsed['calls']['wf_caller', 'wf_dom.set_links.body'] != 3:
        raise ValueError('valid sample lost self/inclusive/calls')
    corrupt = [sample.replace('totals: 21', 'totals: 22'), sample.replace('totals: 21 0\n', ''),
               sample.replace('fn=(2)\n0x20 2 9\n', 'fn=(2)\n'),
               sample.replace('calls=3 0x20 2', 'calls=3 0x20'),
               sample.replace('cfn=(2) wf_dom.set_links.body', 'cfn=(2)')]
    for wrong in corrupt:
        try:
            parse_callgrind(wrong)
        except ValueError:
            pass
        else:
            raise ValueError('corrupted callgrind accepted')
    disassembly = ('0000000000000010 <wf_caller>:\n  10: 48 89 04 24 mov %rax,(%rsp)\n'
                   '  14: e8 07 00 00 00 call 20 <wf_dom.set_links>\n'
                   '0000000000000020 <wf_dom.set_links>:\n  20: c3 ret\n')
    if '(%rsp)' not in parse_objdump(disassembly)['wf_caller']:
        raise ValueError('valid objdump lost pre-call argument store')
    repeated = parse_objdump(disassembly + '0000000000000030 <wf_caller>:\n  30: c3 ret\n')
    if '(%rsp)' not in repeated['wf_caller'] or '30: c3' not in repeated['wf_caller@0000000000000030']:
        raise ValueError('repeated local label replaced the first function')
    for wrong in ('no functions\n', disassembly + '0000000000000030 <wf_caller>:\n' * 2):
        try:
            parse_objdump(wrong)
        except ValueError:
            pass
        else:
            raise ValueError('corrupted objdump accepted')
    print('hand-made controls: valid callgrind/objdump accepted; five callgrind and two objdump corruptions rejected')


def run(label, command, timeout):
    remaining = float(os.environ['INLINE_DEADLINE']) - time.time() - 15
    if remaining <= 0:
        raise BudgetExhausted('profiling deadline reached before ' + label)
    timeout = min(timeout, remaining)
    started = time.monotonic()
    with (OUT / (label + '.stdout')).open('w') as stdout, (OUT / (label + '.stderr')).open('w') as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr,
                                    env=dict(os.environ, WF_WORKERS='1'), timeout=timeout)
            status, expired = result.returncode, False
        except subprocess.TimeoutExpired:
            status, expired = None, True
    record = dict(label=label, command=command, seconds=time.monotonic() - started,
                  exit=status, timeout=expired, cwd=str(Path.cwd()), workers=1)
    with (OUT / 'processes.jsonl').open('a') as output:
        output.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    if expired:
        raise ProfileTimeout('timed out process: ' + label)
    if status != 0:
        raise RuntimeError('failed or timed out process: ' + label)
    return record


def symbols(cohort):
    names = set()
    for line in (OUT / 'drivers' / (cohort + '.nm')).read_text().splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[-2] in ('t', 'T'):
            names.add(fields[-1])
    return names


def choose_markers(emitted):
    common = emitted['base'] & emitted['candidate']
    for stem in ('incremental_after', 'apply_incremental'):
        matches = sorted(s for s in common if re.search(r'\.' + stem + r'$', s))
        if len(matches) == 1:
            return matches
    matches = []
    for stem in ('text_changed', 'update'):
        candidates = sorted(s for s in common if s == 'wf_layout.' + stem)
        if len(candidates) != 1:
            raise ValueError('no common unambiguous boundary for ' + stem)
        matches.extend(candidates)
    return matches


def prefix(source, count, destination):
    written, lines = 0, []
    for line in source.read_bytes().splitlines(keepends=True):
        if line[:2] in (b'T ', b'D ', b'C ', b'K ', b'B ', b'X '):
            if written == count:
                break
            written += 1
        lines.append(line)
    if written != count:
        raise ValueError('prefix shorter than requested operations')
    destination.write_bytes(b''.join(lines))


def merge(profiles):
    merged = dict(total=0, own=Counter(), edges=Counter(), calls=Counter())
    for parsed in profiles:
        merged['total'] += parsed['total']
        for key in ('own', 'edges', 'calls'):
            merged[key].update(parsed[key])
    return merged


def serialize(profile):
    return dict(total=profile['total'], own=dict(profile['own']),
                edges=[dict(caller=a, callee=b, inclusive_ir=v, calls=profile['calls'][a, b])
                       for (a, b), v in sorted(profile['edges'].items())])


def command(cohort, page, script):
    data = 'build/research/concurrency'
    sheets = [] if page == 'html5' else [
        'wikibase.client.init&only=styles&skin=vector-2022=' + data + '/apollo11-modules.css',
        'modules=site.styles&only=styles&skin=vector-2022=' + data + '/apollo11-site.css']
    return [str(OUT / 'drivers' / (cohort + '-layout_oracle')), 'edittime', str(script),
            data + '/' + page + '.html', 'renderer/style/ua.css', *sheets]


def profile(label, cohort, page, script, markers, count, cap, inctime):
    results, profiles, work_counts = [], [], None
    for index, marker in enumerate(markers):
        part = label + '-scope' + str(index + 1)
        output = OUT / (part + '.callgrind')
        # '?' preserves exact length: wrappers and their .body clones cannot
        # both toggle one process. Register only one marker in each command.
        pattern = marker[:-1] + '?'
        result = run(part, ['valgrind', '--tool=callgrind', '--collect-atstart=no',
                           '--toggle-collect=' + pattern, '--dump-before=' + pattern,
                           '--dump-after=' + pattern, '--callgrind-out-file=' + str(output),
                           *command(cohort, page, script)], cap)
        timed, other, styled, built = inctime.read(str(OUT / (part + '.stdout')), inctime.script_operations(str(script)))
        counts = {ordinal: row[1:] for ordinal, row in timed.items()}
        if other or styled or built or len(timed) != count:
            raise ValueError('incomplete/refused/non-text edit protocol')
        if work_counts is not None and counts != work_counts:
            raise ValueError('scope replays differ in update work counts')
        work_counts = counts
        expected = [Path(str(output) + '.' + str(n)) for n in range(1, 2 * count + 1)]
        if set(OUT.glob(part + '.callgrind.*')) != set(expected):
            raise ValueError('missing/extra dump boundaries: ' + part)
        for offset, path in enumerate(expected):
            triggers = re.findall(r'^desc: Trigger: --dump-(before|after)=(.+)$', path.read_text(), re.M)
            direction = 'before' if offset % 2 == 0 else 'after'
            if len(triggers) != 1 or triggers[0][0] != direction or triggers[0][1] not in (pattern, marker):
                raise ValueError('wrong dump boundary: ' + str(path))
            parsed = parse_callgrind(path.read_text())
            if offset % 2:
                if parsed['total'] <= 0 or marker not in (parsed['own'].keys() | {b for a, b in parsed['edges']}):
                    raise ValueError('collected scope lacks marker work')
                profiles.append(parsed)
            elif parsed['total'] != 0:
                raise ValueError('work escaped selected interval')
        if parse_callgrind(output.read_text())['total'] != 0:
            raise ValueError('final residual contains outside-interval work')
        results.append(result)
    return merge(profiles), results, work_counts


def disassembly(emitted):
    blocks = {cohort: parse_objdump((OUT / 'drivers' / (cohort + '.objdump')).read_text()) for cohort in COHORTS}
    status, static_callers = {}, {}
    for cohort in COHORTS:
        selected = {s: text for s, text in blocks[cohort].items() if target(s) == 'set_links'}
        callers = {}
        static_callers[cohort] = []
        for symbol, text in blocks[cohort].items():
            for callee in (s for s in blocks[cohort] if target(s)):
                if re.search(r'\bcallq?\s+[^\n]*<' + re.escape(callee) + r'(?:\+0x[0-9a-f]+)?>', text):
                    static_callers[cohort].append([symbol, callee])
            if any(re.search(r'\bcallq?\s+[^\n]*<' + re.escape(callee) + r'(?:\+0x[0-9a-f]+)?>', text) for callee in selected):
                callers[symbol] = text
        status[cohort] = dict(set_links=list(selected), callsite_callers=list(callers),
                              note='no emitted set_links symbol; may have been inlined or eliminated' if not selected else 'emitted functions saved')
        (OUT / (cohort + '-set_links.disassembly.txt')).write_text('\n'.join(selected.values()) or status[cohort]['note'] + '\n')
        (OUT / (cohort + '-set_links-callers.disassembly.txt')).write_text('\n'.join(callers.values()) or 'No direct callsite found in objdump.\n')
    # Preserve the candidate caller functions on base as well, including when
    # set_links itself disappeared there. Complete bodies retain argument stores.
    candidate_callers = status['candidate']['callsite_callers']
    (OUT / 'base-candidate-callsite-functions.disassembly.txt').write_text('\n'.join(
        blocks['base'].get(s, 'No base function named ' + s + '\n') for s in candidate_callers))
    if status['candidate']['set_links'] and not candidate_callers:
        raise ValueError('candidate set_links emitted but no direct caller disassembled')
    (OUT / 'disassembly-status.json').write_text(json.dumps(status, indent=2) + '\n')
    (OUT / 'static-callers.json').write_text(json.dumps(static_callers, indent=2) + '\n')
    return status


def metric(profile, symbol):
    return (profile['own'][symbol] + sum(v for (a, b), v in profile['edges'].items() if a == symbol),
            profile['own'][symbol], sum(v for (a, b), v in profile['calls'].items() if b == symbol))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |',
                      *['| ' + ' | '.join(map(str, row)) + ' |' for row in rows]]) + '\n'


def report(pairs, emitted, notes, failure=None):
    lines = ['# Hosted v0.127 inline profile', '',
             'Status: ' + ('FAILED: ' + failure if failure else 'completed paired profiles'), '',
             'Instruction counts are hosted Callgrind Ir, not 14900K timings or measured cycle shares. '
             'Inclusive Ir = self Ir + outgoing call-edge Ir; inclusive rows overlap. Incoming calls come from call edges. '
             'Absent emitted symbols may have been inlined or eliminated; emitted symbols with no collected cost report zero.', '',
             'Apollo11 is a fresh hosted capture of the E1 oldid and sheet URLs, not the persistent 14900K capture. '
             'Both builds read identical captured bytes, fonts, UA, and generated scripts. SHA256SUMS records these inputs.', '',
             *notes, '']
    for label, pair in pairs.items():
        left, right = pair['base'], pair['candidate']
        lines += ['## ' + label, '', f"First {pair['count']} individual operations of {pair['available']} (forward and inverse each count as one). "
                  'A truncated odd prefix ends after a forward edit; no operations were filtered or reordered.', '',
                  table(['Build', 'Total interval Ir'], [('base', left['total']), ('candidate', right['total']), ('delta', right['total'] - left['total'])]), '']
        all_symbols = set().union(*(p['own'].keys() | {s for edge in p['edges'] for s in edge} for p in (left, right)))
        target_symbols = {s for s in emitted['base'] | emitted['candidate'] | all_symbols if target(s)}
        caller_symbols = {a for p in (left, right) for a, b in p['edges'] if b in target_symbols}
        if (OUT / 'static-callers.json').exists():
            static = json.loads((OUT / 'static-callers.json').read_text())
            caller_symbols.update(a for c in COHORTS for a, b in static[c] if b in target_symbols)
        rows = []
        for s in sorted(target_symbols | caller_symbols):
            l, r = metric(left, s), metric(right, s)
            role = ('target ' + target(s)) if target(s) else 'direct caller'
            states = ['emitted' if s in emitted[c] else 'not emitted' for c in COHORTS]
            rows.append([s, role, *states, *l, *r, *(r[i] - l[i] for i in range(3))])
        lines += [table(['Function', 'Role', 'Base symbol', 'Candidate symbol', 'Base inclusive Ir', 'Base self Ir', 'Base calls',
                         'Candidate inclusive Ir', 'Candidate self Ir', 'Candidate calls', 'Δ inclusive Ir', 'Δ self Ir', 'Δ calls'], rows), '']
        # Explicit prefix totals remain visible even when no symbol survives.
        rows = []
        for name in TARGETS:
            sums = [tuple(sum(metric(p, s)[i] for s in target_symbols if target(s) == name) for i in range(3)) for p in (left, right)]
            rows.append([name, *sums[0], *sums[1], *(sums[1][i] - sums[0][i] for i in range(3))])
        lines += [table(['Prefix family (variants overlap)', 'Base inclusive Ir', 'Base self Ir', 'Base calls', 'Candidate inclusive Ir',
                         'Candidate self Ir', 'Candidate calls', 'Δ inclusive Ir', 'Δ self Ir', 'Δ calls'], rows), '']
        edges = sorted({edge for p in (left, right) for edge in p['edges'] if edge[1] in target_symbols})
        lines += [table(['Caller → target', 'Base inclusive Ir', 'Base calls', 'Candidate inclusive Ir', 'Candidate calls', 'Δ Ir', 'Δ calls'],
                       [[a + ' → ' + b, left['edges'][a, b], left['calls'][a, b], right['edges'][a, b], right['calls'][a, b],
                         right['edges'][a, b] - left['edges'][a, b], right['calls'][a, b] - left['calls'][a, b]] for a, b in edges]), '']
    (OUT / 'summary.md').write_text('\n'.join(lines))


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('profiling runs only in GitHub Actions; local use is --dry-run')
    OUT.mkdir(parents=True, exist_ok=True)
    deadline = float(os.environ['INLINE_DEADLINE'])
    pairs, emitted, notes, failure = {}, {c: set() for c in COHORTS}, [], None
    try:
        dry_run()
        notes.append(table(['Build', 'Snowghost revision', 'Whitefoot pin', 'Clang'],
                           [[c, (OUT / 'drivers' / (c + '.source.txt')).read_text().splitlines()[0],
                             (OUT / 'drivers' / (c + '.whitefoot.pin')).read_text().strip(),
                             (OUT / 'drivers' / (c + '.toolchain.txt')).read_text().splitlines()[0]] for c in COHORTS]))
        emitted = {c: symbols(c) for c in COHORTS}
        status = disassembly(emitted)
        markers = choose_markers(emitted)
        notes += ['Collected boundaries: `' + '`, `'.join(markers) + '`. '
                  'Each marker toggles collection on entry/off return and dumps before/after; startup, input mutation, '
                  'initial layout, clocks and report/cleanup are excluded. '
                  + ('The common wrapper contains text_changed and update.' if len(markers) == 1 else
                     'Separate deterministic replays collect text_changed and update, then sum their disjoint scopes; inter-call wrapper bookkeeping is excluded.'),
                  'All dump exclusive rows reconcile with their totals footer; summary metadata is not used for conservation.',
                  'set_links disassembly status: `' + json.dumps(status) + '`. Full caller functions include pre-call stack argument stores.']
        (OUT / 'markers.json').write_text(json.dumps(dict(markers=markers, per_process_one_marker=True), indent=2) + '\n')
        spec = importlib.util.spec_from_file_location('inctime', 'research/investigations/incremental-layout/scripts/inctime.py')
        inctime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inctime)
        for page, kind in [('apollo11', 'word'), ('html5', 'sentence')]:
            label = page + '-' + kind
            source = OUT / 'scripts' / (label + '.edits')
            available = len(inctime.script_operations(str(source)))
            pilot = OUT / 'scripts' / (label + '-pilot-1.edits')
            prefix(source, 1, pilot)
            zero = OUT / 'scripts' / (label + '-zero.edits')
            zero.write_bytes(b''.join(line for line in source.read_bytes().splitlines(keepends=True) if line.startswith(b'S ')))
            # Preserve time for artifacts; sentence is optional, word is required.
            remaining = deadline - time.time()
            if remaining < 120 and page == 'html5':
                notes.append('html5 sentence deferred: less than 120 seconds remained before profiling deadline.')
                break
            if remaining < 120:
                raise RuntimeError('insufficient budget for word pilots')
            # A zero-operation negative control rejects startup or initial
            # layout in the collected interval. Real pilots below reject a
            # missing marker through their numbered boundaries.
            if page == 'apollo11':
                for c in COHORTS:
                    for index, marker in enumerate(markers):
                        control = label + '-zero-' + c + '-scope' + str(index + 1)
                        pattern = marker[:-1] + '?'
                        output = OUT / (control + '.callgrind')
                        run(control, ['valgrind', '--tool=callgrind', '--collect-atstart=no',
                                      '--toggle-collect=' + pattern, '--callgrind-out-file=' + str(output),
                                      *command(c, page, zero)], min(180, max(15, (deadline - time.time()) / (6 * len(markers)))))
                        inctime.read(str(OUT / (control + '.stdout')), [], checking=True)
                        if parse_callgrind(output.read_text())['total'] != 0:
                            raise ValueError('zero-edit control collected startup work')
                notes.append('Zero-operation controls for both builds and every selected scope collected 0 Ir; startup and initial layout remain outside the interval.')
            pilots, pilot_counts, deferred = [], None, False
            for c in COHORTS:
                try:
                    _, processes, counts = profile(label + '-pilot-' + c, c, page, pilot, markers, 1,
                                                   min(180, max(15, (deadline - time.time()) / (4 * len(markers)))), inctime)
                except (ProfileTimeout, BudgetExhausted) as problem:
                    if page != 'html5':
                        raise
                    notes.append('html5 sentence deferred during bounded pilot: ' + str(problem))
                    deferred = True
                    break
                if pilot_counts is not None and counts != pilot_counts:
                    raise ValueError('paired pilot work counts differ')
                pilot_counts = counts
                pilots.append(sum(p['seconds'] for p in processes))
            if deferred:
                break
            # Two complete 1-edit process pilots bound startup too. Treat the
            # slower whole process as per-operation cost (conservative), allow
            # 2x uncertainty and enforce separate subprocess/deadline caps.
            remaining = deadline - time.time()
            budget = min(720, max(0, remaining - 90))
            count = min(available, math.floor(budget / (4 * max(pilots))))
            plan = dict(page=page, kind=kind, pilot_seconds=dict(zip(COHORTS, pilots)),
                        paired_spread=max(pilots) / min(pilots), available_operations=available,
                        chosen_operations=count, pair_budget_seconds=budget,
                        criterion='N=floor(pair budget/(2 builds * 2 safety factor * slower 1-edit whole-process pilot)); cap full source count',
                        caveat='paired pilot difference is not repeat noise; edit costs may differ; hard process/deadline caps remain')
            (OUT / (label + '-duration-plan.json')).write_text(json.dumps(plan, indent=2) + '\n')
            if count < 1:
                if page == 'html5':
                    notes.append('html5 sentence deferred: pilots left no conservative paired production budget.')
                    break
                raise RuntimeError('word pilots left no paired production budget')
            selected = OUT / 'scripts' / (label + '-first-' + str(count) + '.edits')
            prefix(source, count, selected)
            paired, expected = {}, None
            for c in COHORTS:
                cap = min(budget / (2 * len(markers)), max(1, (deadline - time.time() - 30) / len(markers)))
                try:
                    data, _, counts = profile(label + '-production-' + c, c, page, selected, markers, count, cap, inctime)
                except (ProfileTimeout, BudgetExhausted) as problem:
                    if page != 'html5':
                        raise
                    notes.append('html5 sentence deferred during bounded production: ' + str(problem))
                    deferred = True
                    break
                if expected is not None and counts != expected:
                    raise ValueError('paired production work counts differ')
                expected = counts
                paired[c] = data
                (OUT / (label + '-' + c + '-profile.json')).write_text(json.dumps(serialize(data), indent=2) + '\n')
            if deferred:
                break
            pairs[label] = dict(**paired, count=count, available=available)
            notes.append(label + ' pilot/selection: `' + json.dumps(plan) + '`.')
            report(pairs, emitted, notes)
    except Exception as problem:
        failure = repr(problem)
        (OUT / 'failure.txt').write_text(failure + '\n')
        raise
    finally:
        report(pairs, emitted, notes, failure)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.dry_run:
        dry_run()
    else:
        main()
