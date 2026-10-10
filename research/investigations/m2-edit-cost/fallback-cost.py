"""Temporary Q141 experiment, called by fallback-cost.yml; remove before ready.

Native X5 timings retain every row. Callgrind dumps isolate each structural
edit, including style, and exclude startup and the full-layout comparator.
The existing X5 parser owns the timing protocol; no private timing driver.
"""
import argparse
import csv
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import time

ROOT = Path.cwd()
OUT = ROOT / 'build/fallback-cost'
SCRIPTS = ROOT / 'build/x5/scripts'
spec = importlib.util.spec_from_file_location('inctime', ROOT / 'research/investigations/incremental-layout/scripts/inctime.py')
inctime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inctime)


def args_for(page):
    base = 'build/research/concurrency/'
    result = [base + page + '.html', 'renderer/style/ua.css']
    if page == 'ecma262':
        result += ['assets/css/ecmarkup.css=' + base + 'ecma262-ecmarkup.css', 'assets/css/print.css=' + base + 'ecma262-print.css']
    if page == 'apollo11':
        result += ['wikibase.client.init&only=styles&skin=vector-2022=' + base + 'apollo11-modules.css', 'modules=site.styles&only=styles&skin=vector-2022=' + base + 'apollo11-site.css']
    return result


def driver(name, mode):
    return str(ROOT / f'build/drivers/driver-{name}/layout_oracle_{mode}')


def run(command, destination, timeout=180):
    started = time.monotonic()
    with destination.open('w') as stdout, destination.with_suffix('.stderr').open('w') as stderr:
        subprocess.run(command, stdout=stdout, stderr=stderr, check=True, timeout=timeout,
                       env=dict(os.environ, WF_WORKERS='4'))
    elapsed = time.monotonic() - started
    destination.with_suffix('.seconds').write_text(f'{elapsed:.6f}\n')
    return elapsed


def native(names, controls, rounds):
    rows = []
    pages = ('ecma262', 'html5', 'apollo11') if controls else ('apollo11',)
    kinds = ('word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block') if controls else ('block',)
    # Two smallest useful forward/inverse samples before selecting the batch.
    for page in pages:
        for kind in kinds:
            source = SCRIPTS / f'{page}-{kind}.edits'
            lines = source.read_text().splitlines(keepends=True)
            header = [line for line in lines if line.startswith('S ')]
            edits = [line for line in lines if line[:2] not in ('S ', 'P ', 'V ') and line.strip()]
            sample = OUT / f'{page}-{kind}-sample.edits'
            sample.write_text(''.join(header + edits[:2]))
            for mode in ('seq', 'par'):
                for name in (names[0], names[-1]):
                    wall = []
                    for repeat in range(2):
                        dest = OUT / f'pilot-{name}-{page}-{kind}-{mode}-{repeat}.raw'
                        wall.append(run([driver(name, mode), 'edittime', str(sample.relative_to(ROOT)), *args_for(page)], dest))
                        inctime.read(dest, inctime.script_operations(sample))
                    print('pilot', name, page, kind, mode, wall, 'wall spread', max(wall) / min(wall), flush=True)
                    if max(wall) > 30:
                        raise ValueError('pilot exceeds the bounded batch budget')
    for round_number in range(1, rounds + 1):
        ordered = names if round_number % 2 else list(reversed(names))
        for page in pages:
            for kind in kinds:
                source = SCRIPTS / f'{page}-{kind}.edits'
                operations = inctime.script_operations(source)
                for mode in ('seq', 'par'):
                    for name in ordered:
                        dest = OUT / f'{name}-{page}-{kind}-{mode}-r{round_number}.raw'
                        seconds = run([driver(name, mode), 'edittime', str(source.relative_to(ROOT)), *args_for(page)], dest)
                        timed, other, styled, built = inctime.read(dest, operations)
                        if other:
                            raise ValueError('nonincremental result')
                        values = []
                        for edit, data in timed.items():
                            style = styled.get(edit, [0, 0, 0, 0])
                            total = data[0] + style[3]
                            values.append(total)
                            path = built.get(edit, [])
                            local, reason = path[-2:] if len(path) == 5 else ('', '')
                            rows.append(dict(cohort=name, page=page, kind=kind, mode=mode,
                                round=round_number, edit=edit, total_us=total,
                                update_us=data[0] - style[0] - style[1],
                                delta_us=style[0], picks_us=style[1], style_us=style[3],
                                splice=local, reason=reason))
                        print('native', name, page, kind, mode, round_number, statistics.median(values), seconds, flush=True)
                        with (OUT / 'native.csv').open('w') as f:
                            writer = csv.DictWriter(f, fieldnames=rows[0])
                            writer.writeheader()
                            writer.writerows(rows)


def profile(names):
    source = SCRIPTS / 'apollo11-block.edits'
    lines = source.read_text().splitlines(keepends=True)
    header = [line for line in lines if line.startswith('S ')]
    edits = [line for line in lines if line[:2] not in ('S ', 'P ', 'V ') and line.strip()]
    # Initial layout never enters apply_structure_edit. Zero edits is the
    # negative control for toggle collection; before/after dumps reset costs
    # and call counters for every edit in the full unchanged script.
    for name in names:
        for size, selected in (('zero', []), ('sample', edits[:2]), ('full', edits)):
            script = OUT / f'profile-{size}.edits'
            script.write_text(''.join(header + selected))
            prefix = OUT / f'profile-{name}-{size}'
            options = ['--collect-atstart=no', '--toggle-collect=wf_oracle.layout.apply_structure_edit']
            if size == 'full':
                options = ['--collect-atstart=yes', '--dump-before=wf_oracle.layout.apply_structure_edit', '--dump-after=wf_oracle.layout.apply_structure_edit']
            seconds = run(['valgrind', '--tool=callgrind', *options,
                           '--callgrind-out-file=' + str(prefix) + '.callgrind',
                           driver(name, 'seq'), 'edittime', str(script.relative_to(ROOT)), *args_for('apollo11')],
                          Path(str(prefix) + '.raw'), timeout=300)
            print('profile', name, size, seconds, flush=True)
            if size != 'full':
                import re
                summary = int(re.search(r'^summary: (\d+)', Path(str(prefix) + '.callgrind').read_text(), re.M)[1])
                if (summary == 0) != (size == 'zero'):
                    raise ValueError(('wrong collection boundary', name, size, summary))
                if seconds > 90:
                    raise ValueError('profile pilot too long for full script')
            else:
                parts = list(OUT.glob(prefix.name + '.callgrind.*'))
                if len(parts) != 2 * len(edits):
                    raise ValueError(('missing edit dumps', len(parts), len(edits)))


def construction_variant(tree, name):
    """Private same-source ablations; archived source.diff records each one."""
    path = tree / 'renderer/layout/structure.wf'
    source = path.read_text()
    before = subprocess.run(['git', 'show', '941e51d478f13ae38e5d714e45c01903356a04ba:renderer/layout/structure.wf'],
                            check=True, capture_output=True, text=True).stdout
    def replace(needle, replacement):
        nonlocal source
        if source.count(needle) != 1:
            raise ValueError(('construction site changed', name, needle))
        source = source.replace(needle, replacement)
    if name == 'noreserve':
        replace('let fresh_routes = reconstruction_route_bound(context: &built);', 'let fresh_routes = 0_u64;')
        replace('let route_bound = layout^.routes.len +sat fresh_routes;', 'let route_bound = fresh_routes;')
    elif name == 'serialroutes':
        start = source.index('fn retain_routes(')
        end = source.index('\nfn reconstruction_route_bound(', start)
        old_start = before.index('fn retain_routes(')
        old_end = before.index('\nfn reconstruction_route_bound(', old_start)
        restored = before[old_start:old_end].replace('routes: &RouteTable<StyleRoute>)', 'routes: &RouteTable<StyleRoute>, reserve: u64)')
        marker = '  let nodes = uses^.len;'
        allocation = ('  if reserve > item_ceiling {\n    return too_large::<unit>();\n  }\n'
                      '  let missing = absent_style_route();\n'
                      '  let allocated = route_table::<StyleRoute>(count: reserve, missing: missing);\n'
                      '  set routes^ = move allocated;\n  set routes^.len = 0_u64;\n')
        restored = restored.replace(marker, allocation + marker)
        source = source[:start] + restored + source[end:]
    elif name == 'oldpaths':
        old_start = before.index('  set paths.len = 0_u64;', before.index('fn structure_changed('))
        old_end = before.index('  let retired =', old_start)
        body = before[old_start:old_end].replace('too_large::<unit>()', 'too_large::<RouteTable<ContextPath>>()').replace('layout^.paths.len', 'source^.len').replace('&layout^.paths', 'source').replace('paths.len', 'destination^.len').replace('&paths', 'destination')
        start = source.index('  if source^.len > item_ceiling {', source.index('fn copy_retained_paths('))
        end = source.index('  return Ok<RouteTable<ContextPath>, LayoutError>(value: move made);', start)
        source = source[:start] + body + source[end:]
    elif name in ('oldunits', 'oldcontexts'):
        old_start = before.index('  for (k in 0_u64..nodes) {', before.index('  let context_of =', before.index('fn structure_changed(')))
        old_end = before.index('  let unused = unused_style();', old_start)
        loop = before[old_start:old_end]
        split = loop.index('    if k < layout^.context_of.len')
        if name == 'oldunits':
            body = loop[:split] + '  }\n'
            body = body.replace('layout^.text_units.len', 'source^.len').replace('&layout^.text_units', 'source').replace('&paths', 'paths').replace('&listing', 'destination')
            function = 'copy_retained_units'
            next_function = 'copy_retained_contexts'
        else:
            body = '  for (k in 0_u64..nodes) {\n' + loop[split:]
            body = body.replace('layout^.context_of.len', 'source^.len').replace('&layout^.context_of', 'source').replace('&paths', 'paths').replace('&context_of', 'destination')
            function = 'copy_retained_contexts'
            next_function = 'structure_changed'
        start = source.index('fn ' + function + '(')
        end = source.index('\nfn ' + next_function + '(', start)
        body_start = source.index('  copy_route_table', start)
        prefix = source[start:body_start]
        replacement = prefix + '  let nodes = count;\n' + body + '  return move made;\n}\n'
        source = source[:start] + replacement + source[end:]
    else:
        raise ValueError(('unknown construction variant', name))
    path.write_text(source)


def memory_record(text):
    import re
    rss = re.findall(r'^\s*Maximum resident set size \(kbytes\): (\d+)$', text, re.M)
    status = re.findall(r'^\s*Exit status: (\d+)$', text, re.M)
    if len(rss) != 1 or status != ['0'] or int(rss[0]) <= 0:
        raise ValueError('missing, failed or invalid maximum RSS observation')
    return int(rss[0])


def memory(names, rounds):
    source = SCRIPTS / 'apollo11-block.edits'
    lines = source.read_text().splitlines(keepends=True)
    header = [line for line in lines if line.startswith('S ')]
    edits = [line for line in lines if line[:2] not in ('S ', 'P ', 'V ') and line.strip()]
    rows = []
    for mode in ('seq', 'par'):
        for size, selected in (('zero', []), ('sample', edits[:2]), ('full', edits)):
            script = OUT / f'memory-{size}.edits'
            script.write_text(''.join(header + selected))
            repetitions = rounds if size == 'full' else 2
            for repeat in range(1, repetitions + 1):
                ordered = names if repeat % 2 else list(reversed(names))
                for name in ordered:
                    dest = OUT / f'memory-{name}-{mode}-{size}-{repeat}.raw'
                    measured = dest.with_suffix('.time')
                    seconds = run(['/usr/bin/time', '-v', '-o', str(measured),
                                   driver(name, mode), 'edittime', str(script.relative_to(ROOT)),
                                   *args_for('apollo11')], dest)
                    if size == 'zero':
                        inctime.read(str(dest), [], checking=True)
                    else:
                        inctime.read(dest, inctime.script_operations(script))
                    rss = memory_record(measured.read_text())
                    rows.append(dict(cohort=name, mode=mode, size=size, round=repeat,
                                     maximum_rss_kib=rss, wall_seconds=seconds))
                    print('memory', rows[-1], flush=True)
                    if size != 'full' and seconds > 30:
                        raise ValueError('RSS pilot exceeds bounded batch budget')
    with (OUT / 'memory.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def callgrind(path):
    """Read Ir self costs and call edges from one independent dump part."""
    import re
    from collections import Counter
    identifiers, own, calls, edges = {}, Counter(), Counter(), Counter()
    caller, callee, pending = None, None, False
    summary = None
    positions, events = 1, 1
    def symbol(text):
        match = re.fullmatch(r'\((\d+)\)(?: (.*))?', text)
        if not match:
            return text
        index, name = match.groups()
        if name is not None:
            identifiers[index] = name
        return identifiers[index]
    for line in Path(path).read_text().splitlines():
        if line.startswith('positions: '):
            positions = len(line.split()) - 1
        elif line.startswith('events: '):
            names = line.split()[1:]
            if names[0] != 'Ir':
                raise ValueError('unexpected callgrind events')
            events = len(names)
        elif line.startswith('summary: '):
            summary = int(line.split()[1])
        elif line.startswith('fn='):
            caller = symbol(line[3:])
            pending = False
        elif line.startswith('cfn='):
            callee = symbol(line[4:])
        elif line.startswith('calls='):
            calls[callee] += int(line[6:].split()[0])
            pending = True
        elif line and line[0] in '*+-0123456789':
            parts = line.split()
            if len(parts) != positions + events:
                raise ValueError(('unexpected cost row', line))
            cost = int(parts[positions])
            if pending:
                edges[caller, callee] += cost
                pending = False
            else:
                own[caller] += cost
    if summary is None or sum(own.values()) != summary:
        raise ValueError(('instruction accounting does not reconcile', path, summary, sum(own.values())))
    return summary, own, calls, edges


def summarize():
    from collections import Counter
    import re
    rows = list(csv.DictReader((OUT / 'native.csv').open()))
    inventory_path = ROOT / 'tests/layout/fixtures/apollo11/block-paths.json'
    expected_paths = {n: (splice, reason) for n, splice, reason in json.loads(inventory_path.read_text())['paths']}
    for row in rows:
        if row['page'] == 'apollo11' and row['kind'] == 'block' and row['cohort'] not in ('main', 'maintwin'):
            path = int(row['splice']), int(row['reason'])
            if path != expected_paths[int(row['edit'])]:
                raise ValueError(('changed original admission', row))
    selected = {}
    for mode in ('seq', 'par'):
        inventory = [r for r in rows if r['cohort'] == 'candidate' and r['page'] == 'apollo11' and r['kind'] == 'block' and r['mode'] == mode and r['round'] == '1']
        distribution = Counter((int(r['splice']), int(r['reason'])) for r in inventory)
        expected = Counter({(1, 0): 38, (0, 9): 18, (0, 7): 2, (0, 3): 2})
        if distribution != expected:
            raise ValueError(('changed block admission', mode, distribution))
        selected[mode] = {int(r['edit']) for r in inventory if r['splice'] == '0'}
    if selected['seq'] != selected['par']:
        raise ValueError('sequential and parallel fallback IDs differ')
    ids = selected['seq']
    (OUT / 'fallback-ids.json').write_text(json.dumps(sorted(ids)) + '\n')
    grouped = {}
    for row in rows:
        scopes = ['all-edits']
        if row['page'] == 'apollo11' and row['kind'] == 'block' and int(row['edit']) in ids:
            scopes.append('fallbacks')
        for scope in scopes:
            key = (row['cohort'], row['page'], row['kind'], row['mode'], row['round'], scope)
            grouped.setdefault(key, []).append(int(row['total_us']))
    summary_rows = [dict(cohort=k[0], page=k[1], kind=k[2], mode=k[3], round=k[4], scope=k[5], edits=len(v), median_us=statistics.median(v)) for k, v in grouped.items()]
    with (OUT / 'native-summary.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=summary_rows[0]); writer.writeheader(); writer.writerows(summary_rows)
    medians = {k: statistics.median(v) for k, v in grouped.items()}
    comparisons = []
    for key, value in medians.items():
        name, page, kind, mode, round_number, scope = key
        if name not in ('candidate', 'candidatetwin', 'before', 'beforetwin'):
            continue
        control = 'maintwin' if name.endswith('twin') else 'main'
        reference = medians[(control, *key[1:])]
        limit = 1 if scope == 'fallbacks' else 2
        comparisons.append(dict(cohort=name, control=control, page=page,
            kind=kind, mode=mode, round=round_number, scope=scope,
            median_us=value, main_us=reference, ratio=value / reference,
            limit=limit, accepted=value <= limit * reference))
    with (OUT / 'acceptance.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=comparisons[0]); writer.writeheader(); writer.writerows(comparisons)
    totals, counts, functions, breakdown = {}, {}, {}, []
    cohorts = ['main', 'candidate']
    if (OUT / 'profile-before-full.callgrind.2').exists():
        cohorts.insert(1, 'before')
    for name in cohorts:
        total, own, calls = 0, Counter(), Counter()
        for edit in sorted(ids):
            path = OUT / f'profile-{name}-full.callgrind.{2 * edit}'
            cost, self_cost, incoming, edges = callgrind(path)
            rebuild = sum(v for (caller, callee), v in edges.items() if callee.split('.body.llvm.')[0] == 'wf_layout.structure_changed')
            layout = sum(v for (caller, callee), v in edges.items() if callee.split('.body.llvm.')[0] == 'wf_layout.update')
            if not rebuild or not layout or cost < rebuild + layout:
                raise ValueError(('invalid phase decomposition', name, edit, cost, rebuild, layout))
            breakdown.append(dict(cohort=name, edit=edit, instructions=cost, structural_rebuild=rebuild, layout=layout, bookkeeping=cost-rebuild-layout))
            total += cost
            for symbol, amount in self_cost.items():
                own[re.sub(r"(?:\.body\.llvm\.[0-9]+|'[0-9]+)$", '', re.sub(r'\$instance\$[0-9a-f]+', '<all>', symbol))] += amount
            for symbol, amount in incoming.items():
                calls[re.sub(r"(?:\.body\.llvm\.[0-9]+|'[0-9]+)$", '', re.sub(r'\$instance\$[0-9a-f]+', '<all>', symbol))] += amount
        totals[name], counts[name], functions[name] = total, calls, own
    with (OUT / 'instruction-breakdown.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=breakdown[0]); writer.writeheader(); writer.writerows(breakdown)
    symbols = set().union(*(set(functions[n]) for n in cohorts))
    attribution = []
    for symbol in symbols:
        row = dict(function=symbol)
        for name in cohorts:
            row[name + '_calls'] = counts[name][symbol]
            row[name + '_self'] = functions[name][symbol]
        row['difference'] = functions['candidate'][symbol] - functions['main'][symbol]
        if 'before' in cohorts:
            row['repair_difference'] = functions['candidate'][symbol] - functions['before'][symbol]
        attribution.append(row)
    attribution.sort(key=lambda row: row['difference'], reverse=True)
    with (OUT / 'attribution.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=attribution[0]); writer.writeheader(); writer.writerows(attribution)
    construction_summary(ids)
    print('fallback instruction totals', totals)
    for row in attribution[:25]:
        print(row)


def constructor_cost(edges, function):
    import re
    def normalized(symbol):
        return re.sub(r"(?:\.body\.llvm\.[0-9]+|'[0-9]+)+$", '', symbol)
    costs = [value for (caller, callee), value in edges.items()
             if normalized(callee) == 'wf_layout.' + function
             and normalized(caller) == 'wf_layout.structure_changed']
    return sum(costs) if costs else None


def construction_summary(ids):
    import re
    names = ('candidate', 'serialroutes', 'oldpaths', 'oldunits', 'oldcontexts', 'noreserve')
    functions = ('retain_routes', 'copy_retained_paths', 'copy_retained_units', 'copy_retained_contexts', 'record_tree', 'reconstruction_route_bound')
    rows = []
    for name in names:
        if not (OUT / f'profile-{name}-full.callgrind.2').exists():
            continue
        for edit in sorted(ids):
            total, own, calls, edges = callgrind(OUT / f'profile-{name}-full.callgrind.{2 * edit}')
            for function in functions:
                # Only the constructor's outer call belongs here, not its
                # recursive or outlined internal calls a second time.
                cost = constructor_cost(edges, function)
                rows.append(dict(cohort=name, edit=edit, constructor=function,
                                 status='observed' if cost is not None else 'unverified-boundary',
                                 inclusive_instructions=cost if cost is not None else ''))
    if rows:
        with (OUT / 'constructions.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)


def controls():
    # Instruction conservation is required evidence: neither a missing event
    # nor an inclusive call cost may silently become exclusive work.
    import tempfile
    content = """positions: line
events: Ir
summary: 21
fn=(1) outer
1 3
cfn=(2) wf_layout.structure_changed
calls=1 0
* 4
cfn=(3) wf_layout.update
calls=1 0
* 5
fn=(2)
1 4
fn=(3)
1 5
fn=(4) bookkeeping
1 9
"""
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / 'part'
        path.write_text(content)
        total, own, calls, edges = callgrind(path)
        assert total == 21 and own['outer'] == 3
        assert calls['wf_layout.structure_changed'] == 1
        assert edges['outer', 'wf_layout.update'] == 5
        for wrong in (content.replace('summary: 21', 'summary: 22'),
                      content.replace('events: Ir', 'events: Dr'),
                      content.replace('1 9\n', '')):
            path.write_text(wrong)
            try:
                callgrind(path)
            except ValueError:
                pass
            else:
                raise AssertionError('accepted incorrect instruction evidence')
    good = 'Maximum resident set size (kbytes): 123\nExit status: 0\n'
    assert memory_record(good) == 123
    for bad in ('', good + good, good.replace('123', '0'), good.replace('status: 0', 'status: 1')):
        try:
            memory_record(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('accepted incorrect RSS evidence')
    edges = {('wf_layout.structure_changed.body.llvm.3', 'wf_layout.retain_routes'): 100,
             ('wf_layout.retain_routes', "wf_layout.retain_routes'2"): 90}
    assert constructor_cost(edges, 'retain_routes') == 100
    assert constructor_cost(edges, 'copy_retained_paths') is None
    assert constructor_cost({}, 'retain_routes') is None
    assert constructor_cost({('wf_layout.structure_changed', 'wf_layout.retain_routes'): 0}, 'retain_routes') == 0
    print('instruction-accounting, constructor-boundary and RSS controls: pass')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('native', 'profile', 'memory', 'variant', 'summarize', 'self-test'))
    parser.add_argument('--names', nargs='+')
    parser.add_argument('--tree', type=Path)
    parser.add_argument('--variant')
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--rounds', type=int, default=3)
    opts = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if opts.action == 'variant':
        construction_variant(opts.tree, opts.variant)
    elif opts.action == 'native':
        native(opts.names, opts.controls, opts.rounds)
    elif opts.action == 'memory':
        memory(opts.names, opts.rounds)
    elif opts.action == 'profile':
        profile(opts.names)
    elif opts.action == 'summarize':
        summarize()
    else:
        controls()
