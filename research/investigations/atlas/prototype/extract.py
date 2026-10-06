"""Prototype: extract the declarations of Whitefoot modules from canonical source (used by build.py)."""
import json, re, sys
from pathlib import Path

ITEM = re.compile(r'^(public\s+)?(opaque\s+)?((?:nocopy|nodrop)\s+)?(struct|enum|fn|const|alias|interface|binding)\b')
DOC = re.compile(r'doc "((?:[^"\\]|\\.)*)"')
EFFECT = re.compile(r'\b(reads|writes)\(([^)]*)\)|\b(pure)\b|\b(waits)\b')
CALL = re.compile(r'\b([a-z_][a-z0-9_]*(?:::[a-z_][a-z0-9_]*)*)\s*(?:::<[^>]*>)?\(')
KEYWORDS = {'if', 'match', 'return', 'cvt', 'move', 'while', 'for', 'requires', 'ensures', 'reads', 'writes', 'contract', 'define'}

def split_items(text):
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        m = ITEM.match(lines[i])
        if not m:
            i += 1
            continue
        start = i
        if lines[i].rstrip().endswith('{') or (m.group(4) == 'fn' and 'contract {' in lines[i]):
            depth = 0
            while True:
                depth += lines[i].count('{') - lines[i].count('}')
                if depth <= 0 and i > start or (depth == 0 and lines[i].rstrip().endswith('}')):
                    break
                i += 1
        yield m, '\n'.join(lines[start:i + 1]), start + 1
        i += 1

def parse_fields(body, variant=False):
    out = []
    for line in body.split('\n')[1:-1]:
        s = line.strip()
        if s.startswith('doc ') or s.startswith('invariant'):
            continue
        if variant:
            m = re.match(r'([A-Z]\w*)\((.*)\);', s)
            if m:
                out.append({'name': m.group(1), 'fields': [f.strip() for f in m.group(2).split(',') if f.strip()]})
        else:
            m = re.match(r'(public\s+)?(readonly\s+)?(\w+):\s*(.+);$', s)
            if m:
                out.append({'name': m.group(3), 'type': m.group(4), 'public': bool(m.group(1))})
    return out

def parse_fn(header, body):
    name = re.match(r'(?:public\s+)?fn\s+(\w+)', header).group(1)
    params = re.search(r'\((.*?)\)\s*->', header)
    result = re.search(r'->\s*(.*?)\s+(?:reads|writes|pure|contract|waits|\{|;|doc)', header + ' ;')
    effects = []
    tail = header.split('->', 1)[1] if '->' in header else ''
    tail = tail.split(' doc "')[0]
    for m in EFFECT.finditer(tail):
        if m.group(1):
            effects.append({'kind': m.group(1), 'places': [p.strip() for p in m.group(2).split(',')]})
        elif m.group(3):
            effects.append({'kind': 'pure'})
        elif m.group(4):
            effects.append({'kind': 'waits'})
    contract = re.findall(r'^\s*((?:requires|ensures)\b.*);$', body, re.M)
    calls = list(dict.fromkeys(c for c in CALL.findall(body.split('\n', 1)[1] if '\n' in body else '') if c.split('::')[-1] not in KEYWORDS))
    return {'name': name, 'params': params.group(1) if params else '', 'result': result.group(1) if result else '',
            'effects': effects, 'contract': contract, 'calls': calls}

def extract(path, module):
    items = []
    for m, body, line in split_items(path.read_text()):
        kind = m.group(4)
        docm = DOC.search(body)
        item = {'module': module, 'file': str(path), 'line': line, 'kind': kind, 'public': bool(m.group(1)),
                'doc': docm.group(1) if docm else None}
        first = body.split('\n')[0]
        if kind == 'struct':
            item['name'] = re.search(r'struct\s+(\w+)', first).group(1)
            item['fields'] = parse_fields(body)
        elif kind == 'enum':
            item['name'] = re.search(r'enum\s+(\w+)', first).group(1)
            item['variants'] = parse_fields(body, variant=True)
        elif kind == 'fn':
            item.update(parse_fn(first, body))
        elif kind in ('const', 'alias'):
            item['name'] = re.search(r'(?:const|alias)\s+(\w+)', first).group(1)
            item['text'] = first.strip()
        else:
            item['name'] = re.search(r'(?:interface|binding)\s+(\w+)', first).group(1)
        items.append(item)
    return items

if __name__ == '__main__':
    root = Path(sys.argv[1])
    model = []
    for d in sys.argv[2:]:
        mod = 'pkg::' + d.replace('/', '::')
        for f in sorted((root / d).glob('*.wf*')):
            model += extract(f, mod)
    json.dump(model, sys.stdout, indent=1)
