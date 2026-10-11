#!/usr/bin/env python3
"""Temporary sg-paged-elem-dir-alias object reader; called by paged-alias-check.yml.

Keep until its CI evidence is archived. No compiler/objdump subprocesses here.
Only recognized x86-64 AT&T page lookups are classified; unknown lowering fails
closed for inspection rather than becoming a pass. LLVM isolation changes only
witness linkage/inlining, preserving function bodies and compiler alias metadata.
"""
import json
import re
import sys
import tempfile
from pathlib import Path

RELEASES = ('wf-78223721f77d', 'wf-exp-e9d765cd6067')


def prepare(source, destination):
    text = Path(source).read_text()
    for name in ('touch', 'touch_grow'):
        pattern = re.compile(r'^define ([^\n]*@wf_' + name + r'\([^\n]*\{)$', re.M)
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise ValueError(('missing/ambiguous witness definition', name, len(matches)))
        def retain(match):
            header = re.sub(r'\b(?:internal|private|alwaysinline)\s*', '', match.group(0))
            if 'noinline' not in header:
                header = header[:-1] + 'noinline {'
            return header
        text = pattern.sub(retain, text)
    Path(destination).write_text(text)


def operands(text):
    # Commas inside AT&T memory addressing are not operand separators.
    return re.split(r',\s*(?![^()]*\))', text.strip())


def registers(text):
    return set(re.findall(r'%[a-z][a-z0-9]*', text))


def memory(text):
    m = re.fullmatch(r'(?P<disp>-?(?:0x[0-9a-f]+|\d+))?\((?P<base>%\w+)(?:,(?P<index>%\w+),(?P<scale>[1248]))?\)', text)
    if not m:
        return None
    return int(m['disp'] or '0', 0), m['base'], m['index'], int(m['scale'] or '1')


def full_register(name):
    aliases = {'eax': 'rax', 'ax': 'rax', 'al': 'rax', 'ah': 'rax',
               'ebx': 'rbx', 'bx': 'rbx', 'bl': 'rbx', 'bh': 'rbx',
               'ecx': 'rcx', 'cx': 'rcx', 'cl': 'rcx', 'ch': 'rcx',
               'edx': 'rdx', 'dx': 'rdx', 'dl': 'rdx', 'dh': 'rdx',
               'edi': 'rdi', 'di': 'rdi', 'dil': 'rdi',
               'esi': 'rsi', 'si': 'rsi', 'sil': 'rsi',
               'ebp': 'rbp', 'bp': 'rbp', 'bpl': 'rbp',
               'esp': 'rsp', 'sp': 'rsp', 'spl': 'rsp'}
    numbered = re.fullmatch(r'%r(\d+)[dwb]', name)
    return '%r' + numbered[1] if numbered else '%' + aliases.get(name[1:], name[1:])


def analyze(text, name):
    headers = list(re.finditer(r'^\s*[0-9a-f]+ <([^>]+)>:\s*$', text, re.M))
    selected = [i for i, h in enumerate(headers) if h[1] == 'wf_' + name]
    if len(selected) != 1:
        raise ValueError(('missing/ambiguous disassembly symbol', name))
    i = selected[0]
    body = text[headers[i].end():headers[i + 1].start() if i + 1 < len(headers) else len(text)]
    pages, directories = {}, set()
    loads, stores, calls, order = [], [], [], []
    for line in body.splitlines():
        match = re.match(r'^\s*([0-9a-f]+):\s+([a-z][a-z0-9]*)\s*(.*?)\s*$', line)
        if not match:
            if re.match(r'^\s*[0-9a-f]+:\s+R_X86_64_\w+\s+', line):
                continue
            if line.strip():
                raise ValueError(('unparsed instruction', name, line))
            continue
        address, op, args = match.groups()
        args = args.split('#', 1)[0].strip()
        parts = operands(args)
        if op.startswith('call'):
            calls.append(line.strip())
            order.append('call')
            # SysV caller-saved pointer values do not survive an opaque call.
            clobbered = {'%rax', '%rcx', '%rdx', '%rsi', '%rdi', '%r8', '%r9', '%r10', '%r11'}
            pages = {register: origin for register, origin in pages.items() if register not in clobbered}
            directories -= clobbered
        if len(parts) != 2:
            # Unknown operations may also mutate implicit registers (mul/div).
            if not (op.startswith(('j', 'call', 'ret', 'nop')) or op in ('push', 'pushq')):
                pages.clear()
                directories.clear()
            continue
        src, dst = parts
        srcmem, dstmem = memory(src), memory(dst)
        lookup = (op in ('mov', 'movq') and srcmem is not None and
                  srcmem[2] is not None and srcmem[3] == 8 and
                  (srcmem[0] == 24 or (srcmem[0] == 0 and srcmem[1] in directories)) and
                  re.fullmatch(r'%r(?:[a-z]+|\d+)', dst) is not None)
        if lookup:
            loads.append(line.strip())
            order.append('load')
        if dstmem is not None and registers(dst) & pages.keys():
            width = None
            if op in ('movups', 'movaps', 'movdqu', 'movdqa', 'vmovups', 'vmovaps', 'vmovdqu', 'vmovdqa') and src.startswith('%xmm'):
                width = 16
            elif op == 'movq' or (op == 'mov' and re.fullmatch(r'%r(?:[a-z]+|\d+)', src)):
                width = 8
            if width is None:
                raise ValueError(('unrecognized page-derived store', name, line))
            stores.append({'instruction': line.strip(), 'bytes': width,
                           'page_load_ids': sorted(set().union(*(pages[r] for r in registers(dst) if r in pages)))})
            order.append('store')
        ordinary_moves = ('mov', 'movq', 'movl', 'movw', 'movb', 'movabs', 'movabsq',
                          'movzbl', 'movzwl', 'movslq', 'movsbl', 'movswl', 'movzbq',
                          'movzwq', 'movsbq', 'movswq', 'movd', 'movaps', 'movups',
                          'movdqa', 'movdqu', 'vmovaps', 'vmovups', 'vmovdqa', 'vmovdqu')
        vector_only = op in ('punpcklqdq', 'punpckhqdq', 'movlhps', 'pshufd') and all(
            r.startswith('%xmm') for r in registers(args))
        known = op in ordinary_moves or op in ('lea', 'leaq', 'leal', 'add', 'addq',
                     'sub', 'subq', 'cmp', 'cmpq', 'test', 'testq') or vector_only
        if not known:
            # xchg with a memory destination still overwrites its source GPR.
            pages.clear()
            directories.clear()
        if re.fullmatch(r'%\w+', dst):
            if lookup:
                pages[dst] = {len(loads) - 1}
                directories.discard(dst)
            elif op in ordinary_moves:
                page, directory = pages.get(src, set()).copy(), src in directories
                pages.pop(dst, None)
                directories.discard(dst)
                if page:
                    pages[dst] = page
                if directory:
                    directories.add(dst)
            elif op in ('lea', 'leaq', 'leal'):
                page = set().union(*(pages[r] for r in registers(src) if r in pages))
                directory = srcmem is not None and srcmem[0] == 24 and srcmem[2] is None
                pages.pop(dst, None)
                directories.discard(dst)
                if page:
                    pages[dst] = page
                if directory:
                    directories.add(dst)
            elif op in ('xor', 'xorq', 'xorl') and src == dst:
                pages.pop(dst, None)
                directories.discard(dst)
            # add/sub keep destination provenance; cmp/test do not write it.
        # A write to a subregister destroys the corresponding full pointer.
        if re.fullmatch(r'%[a-z0-9]+', dst) and op not in ('cmp', 'cmpq', 'test', 'testq'):
            full = full_register(dst)
            if full != dst:
                pages.pop(full, None)
                directories.discard(full)
    # Growth may also read entries while copying the directory. Count only
    # load origins that supply an element-store address, not directory copies.
    used = set().union(*(set(store['page_load_ids']) for store in stores))
    load_number = -1
    filtered_order = []
    for event in order:
        if event == 'load':
            load_number += 1
            if load_number not in used:
                continue
        filtered_order.append(event)
    loads = [line for number, line in enumerate(loads) if number in used]
    order = filtered_order
    if not loads or sum(s['bytes'] for s in stores) != 16 or len(stores) not in (1, 2):
        raise ValueError(('unrecognized two-field witness lowering', name, loads, stores))
    return {'symbol': 'wf_' + name, 'page_pointer_loads': loads, 'element_stores': stores,
            'calls': calls, 'access_order': order, 'merged_16_byte_store': len(stores) == 1 and stores[0]['bytes'] == 16}


def check(directory):
    root = Path(directory)
    verdict = {'request': 'sg-paged-elem-dir-alias', 'method': 'optimized x86-64 AT&T object disassembly; static lookup sites', 'functions': {}}
    try:
        for release in RELEASES:
            text = (root / release / 'disassembly.txt').read_text()
            verdict['functions'][release] = {name: analyze(text, name) for name in ('touch', 'touch_grow')}
        old, new = (verdict['functions'][r] for r in RELEASES)
        checks = {
            'old_touch_reload_control': len(old['touch']['page_pointer_loads']) == 2,
            'new_touch_single_page_load': len(new['touch']['page_pointer_loads']) == 1,
            'old_growth_reload_control': len(old['touch_grow']['page_pointer_loads']) == 2,
            'new_growth_reload_control': len(new['touch_grow']['page_pointer_loads']) == 2,
            'growth_reload_after_mutation_both_compilers': all(
                re.search(r'load,store,(?:call,)+load,store', ','.join(
                    event for event in side['touch_grow']['access_order'] if event in ('load', 'store', 'call')))
                is not None for side in (old, new)),
            'touch_order_both_compilers': all(
                side['touch']['access_order'] == order for side, order in
                ((old, ['load', 'store', 'load', 'store']),
                 (new, ['load', 'store'] if new['touch']['merged_16_byte_store'] else ['load', 'store', 'store']))),
        }
        verdict['checks'] = checks
        verdict['accepted'] = all(checks.values())
    except (OSError, ValueError) as error:
        verdict['accepted'] = False
        verdict['unclassified_error'] = str(error)
    (root / 'verdict.json').write_text(json.dumps(verdict, indent=2) + '\n')
    print(json.dumps(verdict, indent=2))
    if not verdict['accepted']:
        raise SystemExit('alias acceptance failed or lowering requires manual inspection; see verdict.json')



def self_test():
    """Hand-made disassembly dry-run, including controls that must fail."""
    def function(name, mode):
        if mode == 'reload':
            lines = ['mov 0x18(%rax,%rsi,8),%rdi', 'mov %rdx,(%rdi)',
                     'mov 0x18(%rax,%rsi,8),%rdi', 'mov %rcx,0x8(%rdi)']
        elif mode == 'merged':
            lines = ['mov 0x18(%rax,%rsi,8),%rdi', 'movups %xmm0,(%rdi)']
        elif mode == 'reuse':
            lines = ['lea 0x18(%rax),%r10', 'mov (%r10,%rsi,8),%rdi',
                     'mov %rdx,(%rdi)', 'mov %rcx,0x8(%rdi)']
        elif mode == 'stale':
            lines = ['mov 0x18(%rax,%rsi,8),%rbx', 'mov %rdx,(%rbx)',
                     'call 24 <wf_touch_grow+0x24>', 'mov %rcx,0x8(%rbx)']
        elif mode == 'grow':
            lines = ['mov 0x18(%rax,%rsi,8),%rdi', 'mov %rdx,(%rdi)',
                     'call 24 <wf_touch_grow+0x24>',
                     'mov 0x18(%rax,%rsi,8),%rdi', 'mov %rcx,0x8(%rdi)']
        else:
            raise ValueError(mode)
        lines.append('ret')
        text = '0000000000000000 <wf_' + name + '>:\n'
        for i, line in enumerate(lines):
            text += f'  {i * 8:x}:  {line}\n'
            if line.startswith('call'):
                text += f'  {i * 8 + 1:x}: R_X86_64_PLT32 wf__heap_take-0x4\n'
        return text
    def run_case(old, new, accepted):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for tag, text in zip(RELEASES, (old, new)):
                (root / tag).mkdir()
                (root / tag / 'disassembly.txt').write_text(text)
            try:
                check(root)
            except SystemExit:
                if accepted:
                    raise
            else:
                if not accepted:
                    raise AssertionError('wrong disassembly accepted')
            assert json.loads((root / 'verdict.json').read_text())['accepted'] == accepted
    old = function('touch', 'reload') + function('touch_grow', 'grow')
    new = function('touch', 'merged') + function('touch_grow', 'grow')
    run_case(old, new, True)
    run_case(old, function('touch', 'reuse') + function('touch_grow', 'grow'), True)
    negatives = [
        ('new reload', old, old),
        ('missing old reload', new, new),
        ('missing function', old, function('touch', 'merged')),
        ('growth no call', old, function('touch', 'merged') + function('touch_grow', 'reload')),
        ('growth stale pointer', old, function('touch', 'merged') + function('touch_grow', 'stale')),
        ('wrong store width', old, new.replace('movups %xmm0', 'movb %dl')),
        ('missing page load', old, new.replace('mov 0x18(%rax,%rsi,8),%rdi', 'mov (%rax),%rdi', 1)),
        ('unparsed instruction', old, new.replace('  8:  movups', '  bad-encoding  movups', 1)),
        ('conditional overwrite', old, new.replace('  8:  movups', '  7: cmovne %rax,%rdi\n  8:  movups', 1)),
        ('single operand overwrite', old, new.replace('  8:  movups', '  7: pop %rdi\n  8:  movups', 1)),
        ('subregister overwrite', old, new.replace('  8:  movups', '  7: mov %eax,%edi\n  8:  movups', 1)),
        ('implicit destination overwrite', old, new.replace('%rdi', '%rax').replace('  8:  movups', '  7: mul %rbx\n  8:  movups', 1)),
        ('two destination overwrite', old, new.replace('  8:  movups', '  7: xchg %rdi,%rbx\n  8:  movups', 1)),
        ('memory exchange overwrite', old, new.replace('  8:  movups', '  7: xchg %rdi,(%rbx)\n  8:  movups', 1)),
    ]
    for label, before, after in negatives:
        run_case(before, after, False)
        print('detected:', label)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / 'raw.ll'
        destination = root / 'isolated.ll'
        raw = ('define internal void @wf_touch(ptr %p) #0 {\n  ret void\n}\n'
               'define void @wf_touch_grow(ptr %p) #0 {\n  ret void\n}\n'
               '!0 = !{!0}\n')
        source.write_text(raw)
        prepare(source, destination)
        isolated = destination.read_text()
        assert 'internal' not in isolated and isolated.count('noinline {') == 2
        assert isolated.split('!0 =')[1] == raw.split('!0 =')[1]
        source.write_text(raw.replace('wf_touch_grow', 'wf_wrong'))
        try:
            prepare(source, destination)
        except ValueError:
            print('detected: missing LLVM witness')
        else:
            raise AssertionError('missing LLVM witness accepted')
    print('PASS: two hand-made passing shapes and fifteen rejection controls; LLVM isolation checked')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'self-test':
        self_test()
    elif len(sys.argv) == 4 and sys.argv[1] == 'prepare':
        prepare(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == 'check':
        check(sys.argv[2])
    else:
        raise SystemExit('usage: check-element-directory.py prepare INPUT.ll OUTPUT.ll | check OUTPUT_DIR | self-test')
