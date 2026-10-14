"""Prototype: build the atlas page from a renderer tree.

    python3 build.py <renderer dir> <output dir>

Reads every .wf, .wfm and modules.wfg under the renderer directory with
extract.py, resolves types and calls, merges annotations.json and writes
<output dir>/atlas.html (the page) and <output dir>/atlas.json (its data).
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

import extract

root = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'atlas.json'
items = []
for d in sorted({str(p.parent.relative_to(root)) for p in root.rglob('*.wf*') if p.suffix in ('.wf', '.wfm')}):
    mod = 'pkg::' + d.replace('/', '::')
    for f in sorted((root / d).glob('*.wf*')):
        if f.suffix in ('.wf', '.wfm'):
            items += extract.extract(f, mod)

TYPEID = re.compile(r'\b([A-Z][A-Za-z0-9_]*)\b')
PRELUDE = {'Box', 'Slots', 'Array', 'Option', 'Result', 'Bool', 'Vec', 'Deque', 'Map'}

def mod_of_dir(d):
    return 'pkg::' + d.replace('/', '::')

# Module graph from the .wfg file.
graph = {}
for line in (root / 'modules.wfg').read_text().split('\n'):
    m = re.match(r'(pkg::[\w:]+):\s*\[(.*)\];', line)
    if m:
        graph[m.group(1)] = [d.strip() for d in m.group(2).split(',') if d.strip()]
entries = re.findall(r'entry (\w+) = ([\w:]+);', (root / 'modules.wfg').read_text())

# Per-file aliases.
aliases = defaultdict(dict)
for it in items:
    if it['kind'] == 'alias':
        m = re.match(r'alias\s+(\w+)\s*=\s*([\w:]+);', it['text'])
        if m:
            aliases[it['file']][m.group(1)] = m.group(2)

types = {}
for it in items:
    if it['kind'] in ('struct', 'enum'):
        types[f"{it['module']}::{it['name']}"] = it

def resolve_type(name, it):
    target = aliases[it['file']].get(name)
    if target:
        return target
    local = f"{it['module']}::{name}"
    return local if local in types else None

def type_refs(text, it):
    refs = []
    for name in TYPEID.findall(text or ''):
        if name in PRELUDE:
            continue
        r = resolve_type(name, it)
        if r and r not in refs:
            refs.append(r)
    return refs

fn_index = {}
for it in items:
    if it['kind'] == 'fn':
        fn_index.setdefault(f"{it['module']}::{it['name']}", []).append(it)

def resolve_call(name, it):
    if '::' in name:
        return name if name in fn_index else None
    target = aliases[it['file']].get(name)
    if target and target in fn_index:
        return target
    local = f"{it['module']}::{name}"
    return local if local in fn_index else None

def params_of(text):
    params, depth, cur = [], 0, ''
    for ch in text:
        depth += ch in '<(' ; depth -= ch in '>)'
        if ch == ',' and depth == 0:
            params.append(cur); cur = ''
        else:
            cur += ch
    if cur.strip():
        params.append(cur)
    out = []
    for p in params:
        if ':' in p:
            n, t = p.split(':', 1)
            out.append({'name': n.strip(), 'type': t.strip()})
    return out

data = {'modules': {}, 'types': {}, 'fns': {}, 'graph': graph, 'entries': entries}
for mod in sorted({it['module'] for it in items}):
    data['modules'][mod] = {'deps': graph.get(mod, []), 'files': sorted({it['file'] for it in items if it['module'] == mod}),
                            'consts': sum(1 for it in items if it['module'] == mod and it['kind'] == 'const')}

for key, it in types.items():
    t = {'id': key, 'module': it['module'], 'name': it['name'], 'kind': it['kind'], 'public': it['public'],
         'doc': it['doc'], 'file': it['file'], 'line': it['line']}
    if it['kind'] == 'struct':
        t['fields'] = [dict(f, refs=type_refs(f['type'], it)) for f in it['fields']]
    else:
        t['variants'] = [{'name': v['name'], 'fields': v['fields'], 'refs': type_refs(' '.join(v['fields']), it)} for v in it['variants']]
    data['types'][key] = t

for key, defs in fn_index.items():
    iface = next((d for d in defs if d['file'].endswith('.wfm')), None)
    impl = next((d for d in defs if d['file'].endswith('.wf')), None)
    base = impl or iface
    params = params_of(base['params'])
    for p in params:
        p['refs'] = type_refs(p['type'], base)
    calls = [c for c in (resolve_call(c, impl) for c in (impl['calls'] if impl else [])) if c and c != key]
    data['fns'][key] = {
        'id': key, 'module': base['module'], 'name': base['name'], 'public': bool(iface and iface['public']) or base['public'],
        'params': params, 'result': base['result'], 'result_refs': type_refs(base['result'], base),
        'effects': base['effects'], 'contract': base['contract'],
        'doc_interface': iface['doc'] if iface else None, 'doc_body': impl['doc'] if impl else None,
        'file': base['file'], 'line': base['line'], 'calls': list(dict.fromkeys(calls)),
    }

# Reverse references.
callers = defaultdict(set)
for k, f in data['fns'].items():
    for c in f['calls']:
        callers[c].add(k)
for k, f in data['fns'].items():
    f['callers'] = sorted(callers[k])

data['annotations'] = json.load(open(Path(__file__).parent / 'annotations.json'))
blob = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
json.dump(data, open(out_path, 'w'), separators=(',', ':'))
template = (Path(__file__).parent / 'atlas.template.html').read_text()
(out_dir / 'atlas.html').write_text(template.replace('/*ATLAS_DATA*/null', blob))
print('modules', len(data['modules']), 'types', len(data['types']), 'fns', len(data['fns']))
print('calls resolved', sum(len(f['calls']) for f in data['fns'].values()))
print('bytes', Path(out_path).stat().st_size)
