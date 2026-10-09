"""Validates X5 outputs and summarizes incremental timings.

usage: python3 inctime.py SCRIPT RUN...
       python3 inctime.py --check SCRIPT OUTPUT
       python3 inctime.py --reparse SCRIPT EDIT_OUTPUT REPARSE_OUTPUT COUNT

The script defines the exact, nonempty edit sequence. Each run must report
one base and every edit once in order: T/D/C/K/B/J/X must succeed
incrementally. C/K/B/J/X carry a style edit line, and B/J/X a structure edit
line with the contexts and paragraphs built again and those that kept their
preparation.
Checking validates raw driver stdout before run.sh extracts comparable
lines, so malformed, duplicate and incomplete records cannot disappear in
a filter. Raw dumps and the separate style diagnostics are accepted only
in their documented forms. Timing takes the best microseconds per edit over
the runs and requires identical counts across runs. No timed edits is an
error. The 1 ms reporting threshold is unchanged. Python 3 standard library.
Structural path records distinguish local splices from reason-coded fallbacks.
J PARENT BEFORE DEPTH TEXT inserts nested divs around a paragraph through
the same structural path as B; DEPTH is between 1 and 32.
V WIDTH HEIGHT is a full viewport refresh between edits, not a timed edit;
the next edit compares against a fresh build at that viewport.
--check requires them for every structural edit. Historical timing and
filtered reparse logs may omit the entire set; a partial set is invalid.
Historical logs may omit the entire boundary-count suffix. Current logs
must supply all five fields together; timings retain and compare those
counts, and reject mixed old/new timing records within one run.
"""
import re
import sys

BOUNDARY = (r'(?: boundary_entries (\d+) boundary_blocks (\d+) boundary_indexes (\d+)'
            r' boundary_fallbacks (\d+) boundary_reason (\d+))?')
TIMED = re.compile(r'edit (\d+) us (\d+) prepared (\d+) contexts (\d+) paragraphs (\d+) held_entries (\d+) entries (\d+)' + BOUNDARY + '$')
OTHER = re.compile(r'edit (\d+) (inc refused|full)$')
HASH = re.compile(r'edit (\d+) hash [0-9a-f]{16} bytes \d+(?: inc (same|DIFF|refused))?$')
BASE = re.compile(r'base hash [0-9a-f]{16} bytes \d+$')
STYLE_COUNTS = re.compile(r'style edit (\d+) prepared \d+ contexts \d+ paragraphs \d+ held_entries \d+ entries \d+' + BOUNDARY + '$')
STYLE_TIME = re.compile(r'style edit (\d+) delta_us (\d+) picks_us (\d+) full_us (\d+)(?: style_us (\d+))?$')
STRUCTURE = re.compile(r'structure edit (\d+) contexts (\d+) paragraphs (\d+) reused (\d+)$')
CREATED = re.compile(r'created \d+$')
STRUCTURE_FALLBACK = re.compile(r'structure fallback (\d+)$')
STRUCTURE_PATH = re.compile(r'structure path (\d+) splice ([01]) reason (\d+)$')
INCREMENTAL = ('T', 'D', 'C', 'K', 'B', 'J', 'X')
RESTYLED = ('C', 'K', 'B', 'J', 'X')


def script_operations(path):
    operations = []
    for number, raw in enumerate(open(path, 'rb'), 1):
        line = raw.rstrip(b'\n')
        if not line:
            continue
        kind = line[:1]
        if kind not in (b'S', b'P', b'V', b'T', b'D', b'C', b'K', b'B', b'J', b'X') or line[1:2] != b' ':
            raise ValueError('%s:%d: unreadable operation' % (path, number))
        if kind not in (b'S', b'P', b'V'):
            operations.append(kind.decode('ascii'))
    if not operations:
        raise ValueError(path + ': no edits')
    return operations


def read(path, operations, checking=False, require_paths=False):
    timed, other, styled, built = {}, {}, {}, {}
    seen, auxiliary, structural = set(), set(), set()
    fallbacks = set()
    paths = {}
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
            if edit in auxiliary or not 1 <= edit <= len(operations) or operations[edit - 1] not in RESTYLED:
                raise ValueError('%s:%d: unexpected style edit' % (path, line_number))
            auxiliary.add(edit)
            if not checking:
                styled[edit] = [int(value) for value in style.groups()[1:] if value is not None]
            continue
        structure = STRUCTURE.fullmatch(line)
        if structure:
            edit = int(structure.group(1))
            if edit in structural or not 1 <= edit <= len(operations) or operations[edit - 1] not in ('B', 'J', 'X'):
                raise ValueError('%s:%d: unexpected structure edit' % (path, line_number))
            structural.add(edit)
            built[edit] = [int(value) for value in structure.groups()[1:]]
            continue
        path_record = STRUCTURE_PATH.fullmatch(line)
        if path_record:
            edit, local, reason = map(int, path_record.groups())
            if (edit in paths or edit in seen or
                    not 1 <= edit <= len(operations) or
                    operations[edit - 1] not in ('B', 'J', 'X')):
                raise ValueError('%s:%d: unexpected structure path' % (path, line_number))
            if (local == 1) != (reason == 0) or not 0 <= reason <= 11:
                raise ValueError('%s:%d: inconsistent splice/fallback reason' % (path, line_number))
            paths[edit] = [local, reason]
            continue
        fallback_record = STRUCTURE_FALLBACK.fullmatch(line)
        if fallback_record:
            edit = int(fallback_record.group(1))
            if (edit in fallbacks or edit in seen or
                    not 1 <= edit <= len(operations) or
                    operations[edit - 1] not in ('B', 'J', 'X')):
                raise ValueError('%s:%d: unexpected structure fallback' % (path, line_number))
            fallbacks.add(edit)
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
        incremental = operations[edit - 1] in INCREMENTAL
        if checking:
            status = match.group(2)
            if incremental and status != 'same':
                raise ValueError('%s: edit %d: expected inc same, got %s' % (path, edit, status or 'full'))
            if not incremental and status is not None:
                raise ValueError('%s: edit %d: an edit of no incremental kind reported an incremental status' % (path, edit))
        elif match:
            if not incremental:
                raise ValueError('%s: edit %d: unexpected timed structural edit' % (path, edit))
            timed[edit] = [int(value) for value in match.groups()[1:] if value is not None]
        else:
            status = fallback.group(2)
            if incremental or status != 'full':
                raise ValueError('%s: edit %d: unexpected %s' % (path, edit, status))
            other[edit] = status
    if base_count != 1 or len(seen) != len(operations):
        raise ValueError('%s: %d edits for %d operations, %d bases' % (path, len(seen), len(operations), base_count))
    if created_count != (operations.count('B') + operations.count('J')):
        raise ValueError('%s: %d created records for %d insertions' % (path, created_count, (operations.count('B') + operations.count('J'))))
    if not checking and not timed:
        raise ValueError(path + ': no edits were timed')
    if not checking and set(styled) != {edit for edit in timed if operations[edit - 1] in RESTYLED}:
        raise ValueError(path + ': a timed style edit lacks its style edit line')
    if not checking and set(built) != {edit for edit in timed if operations[edit - 1] in ('B', 'J', 'X')}:
        raise ValueError(path + ': a timed structural edit lacks its structure edit line')
    if paths or require_paths:
        expected = {i for i, kind in enumerate(operations, 1) if kind in ('B', 'J', 'X')}
        if set(paths) != expected:
            raise ValueError(path + ': partial structural path records')
        for edit in built:
            built[edit] += paths[edit]
    return timed, other, styled, built


def rank(values, fraction):
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
    return ordered[index]


def check_reparse(script, edited, reparsed, count):
    operations = script_operations(script)
    read(edited, operations, checking=True)
    count = int(count)
    forward = [i for i, kind in enumerate(operations, 1) if kind in ('T', 'B', 'J')]
    if count <= 0 or len(forward) < count:
        raise ValueError('reparse count must name available forward edits')
    hashes = {}
    for raw in open(edited):
        match = re.fullmatch(r'edit (\d+) hash ([0-9a-f]{16}) bytes (\d+)(?: inc same)?\n?', raw)
        if match:
            hashes[int(match.group(1))] = match.groups()[1:]
    position = 0
    compared = 0
    failed = False
    for raw in open(reparsed):
        skipped = re.fullmatch(r'reparse (\d+) skipped\n?', raw)
        match = re.fullmatch(r'reparse (\d+) hash ([0-9a-f]{16}) bytes (\d+)\n?', raw)
        if not skipped and not match:
            raise ValueError('unreadable reparse result: ' + raw.rstrip('\n'))
        edit = int((skipped or match).group(1))
        if compared >= count or position >= len(forward) or edit != forward[position]:
            raise ValueError('duplicate, missing or unexpected reparse edit ID')
        position += 1
        if skipped:
            print('reparse edit %d: skipped' % edit)
            continue
        compared += 1
        same = hashes[edit] == match.groups()[1:]
        print('reparse edit %d: %s' % (edit, 'same' if same else 'DIFFERS'))
        failed |= not same
    if compared != count:
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
        read(sys.argv[3], operations, checking=True, require_paths=True)
        return 0
    if len(sys.argv) < 3:
        raise ValueError('usage: inctime.py SCRIPT RUN...')
    operations = script_operations(sys.argv[1])
    runs = [read(path, operations) for path in sys.argv[2:]]
    if not runs:
        print('no runs')
        return 1
    first_timed, first_other, first_styled, first_built = runs[0]
    for timed, other, _, built in runs[1:]:
        if set(timed) != set(first_timed) or other != first_other:
            print('the runs list different edits')
            return 1
        if built != first_built:
            print('the runs disagree on the structure counts')
            return 1
        for edit, values in timed.items():
            if values[1:] != first_timed[edit][1:]:
                print('edit %d: the runs disagree on the counts' % edit)
                return 1
    best = {edit: min(timed[edit][0] for timed, _, _, _ in runs) for edit in first_timed}
    times = list(best.values())
    refused = sum(1 for kind in first_other.values() if kind == 'inc refused')
    full = sum(1 for kind in first_other.values() if kind == 'full')
    print('edits timed %d, refused %d, rebuilt %d, runs %d' % (len(times), refused, full, len(runs)))
    style_fallbacks = sum(1 for path in sys.argv[2:] for line in open(path)
                          if STRUCTURE_FALLBACK.fullmatch(line.rstrip('\n')))
    print('structural style fallbacks %d across %d runs' % (style_fallbacks, len(runs)))
    if not times:
        raise ValueError('no edits were timed')
    print('us min %d median %d p90 %d max %d; under 1000 us: %d of %d'
          % (min(times), rank(times, 0.5), rank(times, 0.9), max(times),
             sum(1 for t in times if t < 1000), len(times)))
    names = ['prepared', 'contexts', 'paragraphs', 'held_entries', 'entries']
    widths = {len(values) for values in first_timed.values()}
    if len(widths) != 1:
        raise ValueError('mixed legacy and boundary count records')
    if widths == {11}:
        names += ['boundary_entries', 'boundary_blocks', 'boundary_indexes',
                  'boundary_fallbacks', 'boundary_reason']
    for k, name in enumerate(names):
        values = [first_timed[edit][k + 1] for edit in first_timed]
        print('%s min %d median %d max %d' % (name, min(values), rank(values, 0.5), max(values)))
    if first_styled:
        # Criterion 2: per style edit, the best update over the runs against
        # the best full layout over the runs, each chosen independently.
        # A driver run in edittime mode skips the comparator and reports
        # full_us 0 for every edit; it has no ratio to report.
        compared = any(styled[edit][2] > 0 for _, _, styled, _ in runs for edit in styled)
        ratios, deltas, picks = [], [], []
        for edit in sorted(first_styled):
            full = min(styled[edit][2] for _, _, styled, _ in runs)
            if compared and full <= 0:
                raise ValueError('edit %d: full layout timed at 0 us' % edit)
            if compared:
                ratios.append(best[edit] / full)
            deltas.append(min(styled[edit][0] for _, _, styled, _ in runs))
            picks.append(min(styled[edit][1] for _, _, styled, _ in runs))
        if ratios:
            print('update/full min %.3f median %.3f max %.3f; at most 1.2: %d of %d'
                  % (min(ratios), rank(ratios, 0.5), max(ratios),
                     sum(1 for r in ratios if r <= 1.2), len(ratios)))
        else:
            print('update/full not measured (edittime)')
        print('delta_us median %d max %d; picks_us median %d max %d'
              % (rank(deltas, 0.5), max(deltas), rank(picks, 0.5), max(picks)))
        if all(len(first_styled[edit]) == 4 for edit in first_styled):
            # The style stage, run in full before the update, and the edit's
            # whole cost from the edited document to laid-out boxes.
            styles = [min(styled[edit][3] for _, _, styled, _ in runs) for edit in sorted(first_styled)]
            whole = [best[edit] + styles[k] for k, edit in enumerate(sorted(first_styled))]
            print('style_us median %d max %d; style+update us median %d max %d'
                  % (rank(styles, 0.5), max(styles), rank(whole, 0.5), max(whole)))
    if first_built:
        if all(len(values) == 5 for values in first_built.values()):
            local = sum(values[3] for values in first_built.values())
            reasons = {}
            for values in first_built.values():
                if values[4]:
                    reasons[values[4]] = reasons.get(values[4], 0) + 1
            print('structural layout splices %d, fallbacks %d; reasons %s'
                  % (local, len(first_built) - local, sorted(reasons.items())))
        names = ['built contexts', 'built paragraphs', 'reused paragraphs']
        for k, name in enumerate(names):
            values = [first_built[edit][k] for edit in first_built]
            print('%s min %d median %d max %d' % (name, min(values), rank(values, 0.5), max(values)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, UnicodeError) as error:
        print('inctime.py: ' + str(error), file=sys.stderr)
        sys.exit(1)
