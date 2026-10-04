"""Independent reference for pkg::style::layout_changes (experiment X5, step 4).

usage: python3 stylecheck.py empty PAGE
       python3 stylecheck.py ref PAGE KIND [--count N] [--verbose]
       python3 stylecheck.py case HTMLFILE CLASS,CLASS,... [--verbose]

Run from the repository root with build/style_oracle (built from the entry
style_oracle) and build/layout_oracle (for the `nodes` listing the edit
scripts are drawn from), with the pages and sheets that
research/investigations/layout/run.sh sheets_of names in
build/research/concurrency/. Scratch files go to build/x5/.

empty   runs the script `S .x5c{color:#123456}` and `N` (a recompute with no
        change) in `style_oracle delta` and requires 0 flagged elements.
ref     generates PAGE-KIND.edits with edits.py (KIND colour, fontsize or
        rootfont), appends a P line for every edit and for the unedited
        document, runs `style_oracle delta`, and for every edit compares the
        driver's flagged elements with a brute-force comparison of the style
        dump before and after it. An element is changed by the reference when
        any column of its row differs except color, border-*-color and
        background-color (the colours pkg::layout does not read), when its
        row is missing or new, or when a ::before or ::after row of it
        differs, appears or disappears. The reference reads only the dump
        (computed values as the driver serializes them), not layout_changes.
        case    runs the edits of make_case_script on a small page (a path ending in
        .html, such as lists-case.html) and compares as ref does.
        Exit status 1 when any edit disagrees. A line is printed for a disagreeing
        edit (with --verbose for every edit) and a summary last; the summary
        also counts the rows whose colour columns alone changed, which shows
        that a colour edit changes the dump.

The dump prints a pseudo-element only when its content is not none and
serializes floats rounded, so the reference can differ from layout_changes
(which compares the pseudo-elements the cascade matched and floats exactly)
for a pseudo-element with content none or a float that prints equally; the
report counts both directions per edit."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = 'build/research/concurrency'
UA = 'renderer/style/ua.css'
OUT = 'build/x5'
STYLE = os.environ.get('STYLE_ORACLE', 'build/style_oracle')
LAYOUT = 'build/layout_oracle'

NOT_LAYOUT = {b'color', b'border-top-color', b'border-right-color', b'border-bottom-color',
              b'border-left-color', b'background-color'}


def sheets_of(page):
    if page == 'ecma262':
        return ['assets/css/ecmarkup.css=%s/ecma262-ecmarkup.css' % DATA,
                'assets/css/print.css=%s/ecma262-print.css' % DATA]
    if page == 'html5':
        return []
    if page == 'apollo11':
        return ['wikibase.client.init&only=styles&skin=vector-2022=%s/apollo11-modules.css' % DATA,
                'modules=site.styles&only=styles&skin=vector-2022=%s/apollo11-site.css' % DATA]
    raise SystemExit('stylecheck: unknown page %s' % page)


def driver_args(page):
    if page.endswith('.html'):
        return [page, UA]
    return ['%s/%s.html' % (DATA, page), UA] + sheets_of(page)


def run_delta(page, script_path):
    return subprocess.Popen([STYLE, 'delta', script_path] + driver_args(page), stdout=subprocess.PIPE)


def empty(page):
    path = '%s/%s-empty.edits' % (OUT, page)
    with open(path, 'wb') as f:
        f.write(b'S .x5c{color:#123456}\nN\n')
    proc = run_delta(page, path)
    lines = proc.stdout.read().decode().splitlines()
    status = proc.wait()
    print('%s empty edit: exit %d, driver says: %s' % (page, status, ' | '.join(lines)))
    flagged = [int(l.split()[3]) for l in lines if l.startswith('edit ')]
    return status == 0 and flagged == [0]


def make_script(page, kind, count):
    os.makedirs(OUT, exist_ok=True)
    nodes = '%s/%s.nodes' % (OUT, page)
    with open(nodes, 'wb') as f:
        subprocess.check_call([LAYOUT, 'nodes', '0'] + driver_args(page), stdout=f)
    cmd = [sys.executable, os.path.join(HERE, 'edits.py'), page, nodes, OUT]
    if count:
        cmd += ['--count', str(count)]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    path = '%s/%s-%s.edits' % (OUT, page, kind)
    with open(path, 'rb') as f:
        lines = f.read().splitlines()
    edits = [l for l in lines if l[:1] in (b'C', b'K')]
    with open(path, 'wb') as f:
        f.write(b'\n'.join(lines) + b'\n')
        f.write(b''.join(b'P %d\n' % i for i in range(len(edits) + 1)))
    return path, len(edits)


def layout_rows(dump, columns):
    """The rows of one dump: {(index, name): (layout-relevant columns, hash of the whole row)}."""
    rows = {}
    for line in dump:
        parts = line.rstrip(b'\n').split(b'\t')
        rows[(parts[0], parts[1])] = (b'\t'.join(parts[i] for i in columns), hash(line))
    return rows


def read_blocks(stream):
    """Yields ('edit', n, changed, micros), ('flags', n, set of indices) and
    ('dump', n, lines) from the driver's output in order."""
    pending = None
    for raw in stream:
        if raw.startswith(b'edit '):
            if pending:
                yield pending
                pending = None
            fields = raw.split()
            yield ('edit', int(fields[1]), int(fields[3]), int(fields[5]))
        elif raw.startswith(b'flags '):
            fields = raw.split()
            yield ('flags', int(fields[1]), {int(x) for x in fields[2:]})
        elif raw.startswith(b'dump '):
            if pending:
                yield pending
            pending = ('dump', int(raw.split()[1]), [])
        elif pending:
            pending[2].append(raw)
    if pending:
        yield pending


def make_case_script(page, classes):
    """For a small case page: every element below body gets each class of CLASSES
    added and removed in turn, then all of them added one after the other and
    removed in reverse; a P line follows for every edit and for the unedited
    document."""
    os.makedirs(OUT, exist_ok=True)
    nodes = '%s/%s.nodes' % (OUT, os.path.basename(page))
    with open(nodes, 'wb') as f:
        subprocess.check_call([LAYOUT, 'nodes', '0'] + driver_args(page), stdout=f)
    elements = []
    seen_body = False
    for line in open(nodes, 'rb'):
        fields = line.split()
        if fields and fields[0] == b'E':
            seen_body = seen_body or fields[3] == b'body'
            if seen_body:
                elements.append(int(fields[1]))
    lines = []
    for node in elements:
        for name in classes:
            lines.append(b'C %d %s' % (node, name.encode()))
            lines.append(b'K %d %s' % (node, name.encode()))
        for name in classes:
            lines.append(b'C %d %s' % (node, name.encode()))
        for name in reversed(classes):
            lines.append(b'K %d %s' % (node, name.encode()))
    path = '%s/%s.edits' % (OUT, os.path.basename(page))
    with open(path, 'wb') as f:
        f.write(b'\n'.join(lines) + b'\n')
        f.write(b''.join(b'P %d\n' % i for i in range(len(lines) + 1)))
    return path, len(lines)


def reference(page, kind, count, verbose, classes=None):
    if classes:
        path, edits = make_case_script(page, classes)
        kind = 'case'
    else:
        path, edits = make_script(page, kind, count)
    proc = run_delta(page, path)
    columns = None
    previous = None
    flagged = {}
    counts = {}
    disagree = 0
    totals = []
    for block in read_blocks(proc.stdout):
        if block[0] == 'edit':
            counts[block[1]] = block[2]
        elif block[0] == 'flags':
            flagged[block[1]] = block[2]
        else:
            number, dump = block[1], block[2]
            if columns is None:
                names = dump[0].rstrip(b'\n').split(b'\t')
                columns = [i for i, n in enumerate(names) if n not in NOT_LAYOUT]
            rows = layout_rows(dump[1:], columns)
            if previous is not None:
                keys = set(previous) | set(rows)
                changed = set()
                paint = 0
                for key in keys:
                    before, after = previous.get(key), rows.get(key)
                    if before is None or after is None or before[0] != after[0]:
                        changed.add(int(key[0]))
                    elif before[1] != after[1]:
                        paint += 1
                got = flagged.get(number, set())
                extra = got - changed
                missing = changed - got
                agree = not extra and not missing
                if not agree:
                    disagree += 1
                if verbose or not agree:
                    print('%s %s edit %d: layout_changes %d (count line %d), reference %d, only layout_changes %d, '
                          'only reference %d, rows changed in colour only %d: %s' % (
                              page, kind, number, len(got), counts.get(number, -1), len(changed), len(extra),
                              len(missing), paint, 'agree' if agree else 'DISAGREE'))
                totals.append((len(got), len(changed), paint))
                if not agree:
                    print('    only layout_changes: %s' % sorted(extra)[:20])
                    print('    only reference: %s' % sorted(missing)[:20])
            previous = rows
    status = proc.wait()
    flags = sorted(t[0] for t in totals)
    reference_counts = sorted(t[1] for t in totals)
    paints = sorted(t[2] for t in totals)
    middle = len(totals) // 2
    print('%s %s: %d edits, %d disagree, driver exit %d; flagged min/median/max %d/%d/%d, reference '
          '%d/%d/%d, rows changed in colour only %d/%d/%d' % (
              page, kind, edits, disagree, status, flags[0], flags[middle], flags[-1],
              reference_counts[0], reference_counts[middle], reference_counts[-1],
              paints[0], paints[middle], paints[-1]))
    return status == 0 and disagree == 0 and len(counts) == edits


def main():
    args = sys.argv[1:]
    count = None
    verbose = '--verbose' in args
    if verbose:
        args.remove('--verbose')
    if '--count' in args:
        at = args.index('--count')
        count = int(args[at + 1])
        del args[at:at + 2]
    if len(args) == 2 and args[0] == 'empty':
        ok = empty(args[1])
    elif len(args) == 3 and args[0] == 'ref':
        ok = reference(args[1], args[2], count, verbose)
    elif len(args) == 3 and args[0] == 'case':
        ok = reference(args[1], None, count, verbose, args[2].split(','))
    else:
        raise SystemExit(__doc__)
    sys.exit(0 if ok else 1)


main()
