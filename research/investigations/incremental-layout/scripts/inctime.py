"""Validates X5 outputs and summarizes incremental timings.

usage: python3 inctime.py SCRIPT RUN...
       python3 inctime.py --check SCRIPT OUTPUT
       python3 inctime.py --reparse SCRIPT EDIT_OUTPUT REPARSE_OUTPUT COUNT

The script defines the exact, nonempty edit sequence. Each run must report
one base and every edit once in order: T/D/C/K/B/X must succeed incrementally.
Checking validates raw driver stdout before run.sh extracts comparable
lines, so malformed, duplicate and incomplete records cannot disappear in
a filter. Raw dumps and the separate style and child diagnostics are accepted only
in their documented forms. Timing takes the best microseconds per edit over
the runs and requires identical counts across runs. No timed edits is an
error. The 1 ms reporting threshold is unchanged. Python 3 standard library.
"""
import re
import sys

TIMED = re.compile(r'edit (\d+) us (\d+) prepared (\d+) contexts (\d+) paragraphs (\d+) held_entries (\d+) entries (\d+)$')
OTHER = re.compile(r'edit (\d+) (inc refused|full)$')
HASH = re.compile(r'edit (\d+) hash [0-9a-f]{16} bytes \d+(?: inc (same|DIFF|refused))?$')
BASE = re.compile(r'base hash [0-9a-f]{16} bytes \d+$')
STYLE_COUNTS = re.compile(r'style edit (\d+) prepared \d+ contexts \d+ paragraphs \d+ held_entries \d+ entries \d+$')
STYLE_TIME = re.compile(r'style edit (\d+) delta_us \d+ picks_us \d+ full_us \d+$')
CHILD_COUNTS = re.compile(r'child edit (\d+) prepared \d+ contexts \d+ paragraphs \d+ held_entries \d+ entries \d+$')
CHILD_TIME = re.compile(r'child edit (\d+) delta_us \d+ picks_us \d+ full_us \d+$')
CREATED = re.compile(r'created \d+$')


def script_operations(path):
    operations = []
    for number, raw in enumerate(open(path, 'rb'), 1):
        line = raw.rstrip(b'\n')
        if not line:
            continue
        kind = line[:1]
        if kind not in (b'S', b'P', b'T', b'D', b'C', b'K', b'B', b'X') or line[1:2] != b' ':
            raise ValueError('%s:%d: unreadable operation' % (path, number))
        if kind not in (b'S', b'P'):
            operations.append(kind.decode('ascii'))
    if not operations:
        raise ValueError(path + ': no edits')
    return operations


def read(path, operations, checking=False):
    timed, other = {}, {}
    seen, auxiliary = set(), set()
    base_count = 0
    created_count = 0
    for line_number, raw in enumerate(open(path), 1):
        line = raw.rstrip('\n')
        if BASE.fullmatch(line):
            base_count += 1
            if base_count != 1 or seen:
                raise ValueError('%s:%d: duplicate or late base' % (path, line_number))
            continue
        style = (STYLE_COUNTS if checking else STYLE_TIME).fullmatch(line)
        if style:
            edit = int(style.group(1))
            if edit in auxiliary or not 1 <= edit <= len(operations) or operations[edit - 1] not in ('C', 'K'):
                raise ValueError('%s:%d: unexpected style edit' % (path, line_number))
            auxiliary.add(edit)
            continue
        child = (CHILD_COUNTS if checking else CHILD_TIME).fullmatch(line)
        if child:
            edit = int(child.group(1))
            if edit in auxiliary or not 1 <= edit <= len(operations) or operations[edit - 1] not in ('B', 'X'):
                raise ValueError('%s:%d: unexpected child edit' % (path, line_number))
            auxiliary.add(edit)
            continue
        if CREATED.fullmatch(line):
            created_count += 1
            continue
        if checking and (line.startswith(('E\t', 'T\t', 'H\t')) or line == 'inc dump'):
            continue
        match = HASH.fullmatch(line) if checking else TIMED.fullmatch(line)
        fallback = None if checking else OTHER.fullmatch(line)
        if not match and not fallback:
            raise ValueError('%s:%d: unexpected output: %s' % (path, line_number, line))
        record = match or fallback
        edit = int(record.group(1))
        if base_count != 1 or edit in seen or edit != len(seen) + 1 or edit > len(operations):
            raise ValueError('%s:%d: duplicate, missing or unordered edit ID %d' % (path, line_number, edit))
        seen.add(edit)
        incremental = operations[edit - 1] in ('T', 'D', 'C', 'K', 'B', 'X')
        if checking:
            status = match.group(2)
            if incremental and status != 'same':
                raise ValueError('%s: edit %d: expected inc same, got %s' % (path, edit, status or 'full'))
            if not incremental and status is not None:
                raise ValueError('%s: edit %d: structural edit did not use full path' % (path, edit))
        elif match:
            if not incremental:
                raise ValueError('%s: edit %d: unexpected timed structural edit' % (path, edit))
            timed[edit] = [int(value) for value in match.groups()[1:]]
        else:
            status = fallback.group(2)
            if incremental or status != 'full':
                raise ValueError('%s: edit %d: unexpected %s' % (path, edit, status))
            other[edit] = status
    if base_count != 1 or len(seen) != len(operations):
        raise ValueError('%s: %d edits for %d operations, %d bases' % (path, len(seen), len(operations), base_count))
    if created_count != operations.count('B'):
        raise ValueError('%s: %d created records for %d insertions' % (path, created_count, operations.count('B')))
    if not checking and not timed:
        raise ValueError(path + ': no edits were timed')
    return timed, other


def rank(values, fraction):
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
    return ordered[index]


def check_reparse(script, edited, reparsed, count):
    operations = script_operations(script)
    read(edited, operations, checking=True)
    count = int(count)
    forward = [i for i, kind in enumerate(operations, 1) if kind in ('T', 'B')][:count]
    if count <= 0 or len(forward) != count:
        raise ValueError('reparse count must name available forward edits')
    hashes = {}
    for raw in open(edited):
        match = re.fullmatch(r'edit (\d+) hash ([0-9a-f]{16}) bytes (\d+)(?: inc same)?\n?', raw)
        if match:
            hashes[int(match.group(1))] = match.groups()[1:]
    found = []
    failed = False
    for raw in open(reparsed):
        match = re.fullmatch(r'reparse (\d+) hash ([0-9a-f]{16}) bytes (\d+)\n?', raw)
        if not match:
            raise ValueError('unreadable reparse result: ' + raw.rstrip('\n'))
        edit = int(match.group(1))
        if len(found) >= count or edit != forward[len(found)]:
            raise ValueError('duplicate, missing or unexpected reparse edit ID')
        found.append(edit)
        same = hashes[edit] == match.groups()[1:]
        print('reparse edit %d: %s' % (edit, 'same' if same else 'DIFFERS'))
        failed |= not same
    if found != forward:
        raise ValueError('incomplete reparse output')
    return 1 if failed else 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == '--reparse':
        if len(sys.argv) != 6:
            raise ValueError('usage: inctime.py --reparse SCRIPT EDIT_OUTPUT REPARSE_OUTPUT COUNT')
        return check_reparse(*sys.argv[2:])
    if len(sys.argv) >= 2 and sys.argv[1] == '--check':
        if len(sys.argv) != 4:
            raise ValueError('usage: inctime.py --check SCRIPT OUTPUT')
        operations = script_operations(sys.argv[2])
        read(sys.argv[3], operations, checking=True)
        return 0
    if len(sys.argv) < 3:
        raise ValueError('usage: inctime.py SCRIPT RUN...')
    operations = script_operations(sys.argv[1])
    runs = [read(path, operations) for path in sys.argv[2:]]
    if not runs:
        print('no runs')
        return 1
    first_timed, first_other = runs[0]
    for timed, other in runs[1:]:
        if set(timed) != set(first_timed) or other != first_other:
            print('the runs list different edits')
            return 1
        for edit, values in timed.items():
            if values[1:] != first_timed[edit][1:]:
                print('edit %d: the runs disagree on the counts' % edit)
                return 1
    best = {edit: min(timed[edit][0] for timed, _ in runs) for edit in first_timed}
    times = list(best.values())
    refused = sum(1 for kind in first_other.values() if kind == 'inc refused')
    full = sum(1 for kind in first_other.values() if kind == 'full')
    print('edits timed %d, refused %d, rebuilt %d, runs %d' % (len(times), refused, full, len(runs)))
    if not times:
        raise ValueError('no edits were timed')
    print('us min %d median %d p90 %d max %d; under 1000 us: %d of %d'
          % (min(times), rank(times, 0.5), rank(times, 0.9), max(times),
             sum(1 for t in times if t < 1000), len(times)))
    names = ['prepared', 'contexts', 'paragraphs', 'held_entries', 'entries']
    for k, name in enumerate(names):
        values = [first_timed[edit][k + 1] for edit in first_timed]
        print('%s min %d median %d max %d' % (name, min(values), rank(values, 0.5), max(values)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, UnicodeError) as error:
        print('inctime.py: ' + str(error), file=sys.stderr)
        sys.exit(1)
