"""Summarize the hosted Q140 paired edit-cost experiment.

Called by q140-cost.yml after every requested sample; remove with that
workflow. Raw protocol validation comes from the existing X5 reader. The
comparison pairs the same edit and round, including the full style-stage
charge for style/structure edits, before reporting medians and spread.
"""
import argparse
import json
from pathlib import Path
import statistics

import inctime

PAGES = ('ecma262', 'html5', 'apollo11')
KINDS = ('word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block')
NAMES = ('main', 'm2', 'twin', 'head')


def costs(path, operations):
    timed, other, styled, _ = inctime.read(str(path), operations)
    if other or set(timed) != set(range(1, len(operations) + 1)):
        raise ValueError('incomplete timed sample: ' + str(path))
    result = {}
    for number, values in timed.items():
        charge = values[0]
        if operations[number - 1] in inctime.RESTYLED:
            if number not in styled or len(styled[number]) != 4:
                raise ValueError('missing full style-stage charge: ' + str(path))
            charge += styled[number][3]
        result[number] = charge
    return result


def paired(first, second):
    if not first or first.keys() != second.keys() or min(second.values()) <= 0:
        raise ValueError('missing, mismatched or zero paired sample')
    return [first[key] / second[key] for key in first]


def controls():
    assert paired({(1, 1): 20}, {(1, 1): 10}) == [2]
    for first, second in (({}, {}), ({1: 1}, {2: 1}), ({1: 1}, {1: 0})):
        try:
            paired(first, second)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid paired input accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('scripts', type=Path)
    parser.add_argument('--rounds', type=int, required=True)
    args = parser.parse_args()
    controls()
    rows = []
    for page in PAGES:
        for kind in KINDS:
            operations = inctime.script_operations(str(args.scripts / (page + '-' + kind + '.edits')))
            for mode in ('seq', 'par'):
                samples = {name: {} for name in NAMES}
                for round_number in range(1, args.rounds + 1):
                    for name in NAMES:
                        path = args.directory / f'{page}-{kind}-{mode}-r{round_number}-{name}.raw'
                        values = costs(path, operations)
                        samples[name].update({(round_number, edit): value for edit, value in values.items()})
                head = paired(samples['head'], samples['m2'])
                twin = paired(samples['twin'], samples['m2'])
                record = dict(page=page, kind=kind, mode=mode, edits=len(operations), rounds=args.rounds)
                record.update({name + '_us': statistics.median(values.values()) for name, values in samples.items()})
                record.update(head_m2=statistics.median(head), head_m2_min=min(head), head_m2_max=max(head), twin_m2=statistics.median(twin), twin_m2_min=min(twin), twin_m2_max=max(twin))
                rows.append(record)
    (args.directory / 'table.json').write_text(json.dumps(rows, indent=2) + '\n')
    columns = list(rows[0])
    table = '\t'.join(columns) + '\n'
    for row in rows:
        table += '\t'.join(str(row[column]) for column in columns) + '\n'
    (args.directory / 'table.tsv').write_text(table)
    print(table, end='')


if __name__ == '__main__':
    main()
