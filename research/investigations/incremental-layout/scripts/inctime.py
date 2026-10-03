"""Summarizes `layout_oracle incremental` runs (research/investigations/incremental-layout/run.sh time).

usage: python3 inctime.py RUN...

Each RUN file holds one process run's output of the driver's incremental
mode: per edit `edit I us U prepared R contexts C paragraphs P held_entries H
entries E`, or `edit I inc refused` or `edit I full` for an edit the layout
was rebuilt for. Every run must list the same edits. The time of an edit is
its least U over the runs (best of the runs); the counts must agree between
runs. Prints the edits timed and refused, the least, median, 90th percentile
and largest time in microseconds, how many edits stay under 1 ms, and the
least, median and largest of each count. Python 3 standard library only."""
import re
import sys

TIMED = re.compile(r'edit (\d+) us (\d+) prepared (\d+) contexts (\d+) paragraphs (\d+) held_entries (\d+) entries (\d+)$')
OTHER = re.compile(r'edit (\d+) (inc refused|full)$')


def read(path):
    timed = {}
    other = {}
    for line in open(path):
        line = line.rstrip('\n')
        m = TIMED.match(line)
        if m:
            values = [int(v) for v in m.groups()]
            timed[values[0]] = values[1:]
            continue
        m = OTHER.match(line)
        if m:
            other[int(m.group(1))] = m.group(2)
    return timed, other


def rank(values, fraction):
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
    return ordered[index]


def main():
    runs = [read(path) for path in sys.argv[1:]]
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
        return 0
    print('us min %d median %d p90 %d max %d; under 1000 us: %d of %d'
          % (min(times), rank(times, 0.5), rank(times, 0.9), max(times),
             sum(1 for t in times if t < 1000), len(times)))
    names = ['prepared', 'contexts', 'paragraphs', 'held_entries', 'entries']
    for k, name in enumerate(names):
        values = [first_timed[edit][k + 1] for edit in first_timed]
        print('%s min %d median %d max %d' % (name, min(values), rank(values, 0.5), max(values)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
