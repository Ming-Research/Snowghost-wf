"""Render the fixed twin-noise criterion from hosted raw measurements.

Called by m2-paged-time.yml; retained alongside the investigation so each
reported table can be regenerated from its artifact without timing again.
"""
import json
from pathlib import Path
from statistics import mean, median
import sys

COHORTS = ('base', 'base-twin', 'candidate', 'candidate-twin')


def classify(ratios, noise, layout=False):
    def verdict(value):
        if layout:
            if value <= 1.03:
                return 'pass'
            return 'reject' if value > 1 + noise else 'unverified'
        return 'reject' if value > 1 + noise else 'pass'
    center = verdict(median(ratios))
    return center if all(verdict(r) == center for r in ratios) else 'unverified'


def cell(values, layout=False):
    if any(v <= 0 for rounds in values.values() for v in rounds):
        return float('nan'), float('nan'), 'unverified'
    noise = max(.02, *(abs(t / b - 1) for a, twin in [('base', 'base-twin'), ('candidate', 'candidate-twin')] for b, t in zip(values[a], values[twin])))
    ratios = [c / b for b, c in zip(values['base'], values['candidate'])]
    return median(ratios), noise, classify(ratios, noise, layout)


def grouped_rounds(rows, rounds, repeats):
    ordered = sorted(rows, key=lambda e: (e['round'], e.get('repeat', 1)))
    if [(e['round'], e.get('repeat', 1)) for e in ordered] != [(r, k) for r in range(1, rounds + 1) for k in range(1, repeats + 1)]:
        raise ValueError('missing/duplicate edit round or repetition')
    return [[e for e in ordered if e['round'] == r] for r in range(1, rounds + 1)]


def controls():
    # Wrong results must change the classification; large noise never passes a
    # layout regression above 3%, and inconsistent rounds remain unverified.
    examples = [([1., 1., 1.], .02, True, 'pass'),
                ([1.05] * 3, .02, True, 'reject'),
                ([1.05] * 3, .10, True, 'unverified'),
                ([1.04] * 3, .02, False, 'reject'),
                ([1., 1.05, 1.05], .02, True, 'unverified')]
    for ratios, noise, layout, expected in examples:
        if classify(ratios, noise, layout) != expected:
            raise ValueError('criterion control failed')

    complete = [dict(round=r, repeat=k) for r in (1, 2) for k in (1, 2)]
    if [len(g) for g in grouped_rounds(complete, 2, 2)] != [2, 2]:
        raise ValueError('repetition grouping control failed')
    for invalid in (complete[:-1], complete + [complete[0]]):
        try:
            grouped_rounds(invalid, 2, 2)
        except ValueError:
            pass
        else:
            raise ValueError('missing/duplicate repetition was accepted')


def main():
    controls()
    root = Path(sys.argv[1])
    processes = [json.loads(line) for line in (root / 'processes.jsonl').read_text().splitlines()]
    indexed = {row['label']: row for row in processes}
    if len(indexed) != len(processes) or any(row['exit'] for row in processes):
        raise ValueError('duplicate process or failed command')
    machine = json.loads((root / 'machine.json').read_text())
    rounds, repetitions = machine['rounds'], machine['repetitions']
    if rounds < 3:
        raise ValueError('incomplete round count')
    repeats = machine.get('edit_repetitions', 1)
    cells = machine.get('cells', ('style', 'layout', 'word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block'))
    edits = [json.loads(line) for line in (root / 'edits.jsonl').read_text().splitlines()] if any(k in cells for k in ('word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block')) else []
    output = ['# Hosted Paged storage comparison', '',
              f"Revision: {machine['revision']}; compiler: {machine['compiler']}; rounds: {rounds}; repetitions: {repetitions}; complete edit-script repetitions per round: {repeats}.", '',
              'Full-stage milliseconds subtract T(0) from T(repetitions). Edits use the mean microseconds over the complete ordered script, separately for layout update and style_us. Tables show medians across rounds. Noise is the largest twin/original deviation across both pairs and all rounds, at least 2%. Different round classifications are unverified.', '',
              '| Page | Mode | Stage | Base ms | Candidate ms | Ratio | Noise | Verdict |',
              '|---|---|---|---:|---:|---:|---:|---|']
    results, rss = [], []
    for page in machine['pages']:
        for mode in machine['modes']:
            for stage in ('style', 'layout'):
                if stage not in cells:
                    continue
                values, peaks = {}, {}
                for cohort in COHORTS:
                    values[cohort], peaks[cohort] = [], []
                    for r in range(1, rounds + 1):
                        prefix = f'r{r}-{cohort}-{page}-{mode}-{stage}'
                        zero, full = indexed[prefix + '-zero'], indexed[prefix + '-full']
                        values[cohort].append((full['seconds'] - zero['seconds']) / repetitions * 1000)
                        peaks[cohort].append(full['peak_rss_kib'])
                ratio, noise, verdict = cell(values, stage == 'layout')
                results.append(dict(page=page, mode=mode, stage=stage, values=values, ratio=ratio, noise=noise, verdict=verdict))
                output.append(f'| {page} | {mode} | {stage} | {median(values["base"]):.3f} | {median(values["candidate"]):.3f} | {ratio:.4f} | {noise:.1%} | {verdict} |')
                rss.append((page, mode, stage, peaks))
    output += ['', '| Page | Mode | Kind | Component | Base us | Candidate us | Ratio | Noise | Verdict |', '|---|---|---|---|---:|---:|---:|---:|---|']
    for page in machine['pages']:
        for mode in machine['modes']:
            for kind in ('word', 'sentence', 'colour', 'fontsize', 'rootfont', 'block'):
                if kind not in cells:
                    continue
                selected = [e for e in edits if (e['page'], e['mode'], e['kind']) == (page, mode, kind)]
                if len(selected) != rounds * 4 * repeats:
                    raise ValueError('missing edit cell')
                controls_row = selected[0]
                for e in selected:
                    if {k: v[1:] for k, v in e['edits'].items()} != {k: v[1:] for k, v in controls_row['edits'].items()} or e['structure'] != controls_row['structure']:
                        raise ValueError('edit counts differ between cohorts or rounds')
                for component in ('layout', 'style'):
                    if component == 'style' and not controls_row['style']:
                        continue
                    values, peaks = {}, {}
                    for cohort in COHORTS:
                        rows = [e for e in selected if e['cohort'] == cohort]
                        groups = grouped_rounds(rows, rounds, repeats)
                        values[cohort] = [mean(v[0] for e in group for v in e['edits'].values()) if component == 'layout' else mean(v[3] for e in group for v in e['style'].values()) for group in groups]
                        peaks[cohort] = [e['peak_rss_kib'] for e in rows]
                    ratio, noise, verdict = cell(values)
                    results.append(dict(page=page, mode=mode, kind=kind, stage=component, values=values, ratio=ratio, noise=noise, verdict=verdict))
                    output.append(f'| {page} | {mode} | {kind} | {component} | {median(values["base"]):.2f} | {median(values["candidate"]):.2f} | {ratio:.4f} | {noise:.1%} | {verdict} |')
                    if component == 'layout':
                        rss.append((page, mode, kind, peaks))
    output += ['', '| Page | Mode | Stage/script | Base peak MiB | Base twin | Candidate peak MiB | Candidate twin |', '|---|---|---|---:|---:|---:|---:|']
    for page, mode, stage, peaks in rss:
        output.append(f'| {page} | {mode} | {stage} | ' + ' | '.join(f'{max(peaks[c])/1024:.2f}' for c in COHORTS) + ' |')
    verdicts = {r['verdict'] for r in results}
    verdict = 'reject' if 'reject' in verdicts else 'unverified' if 'unverified' in verdicts else 'pass'
    output += ['', f'Performance verdict: **{verdict}**. Gate/output results and the deferred owner-motion invariant remain separate completion conditions.', '']
    (root / 'tables.md').write_text('\n'.join(output))
    (root / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
    print('\n'.join(output))


if __name__ == '__main__':
    main()
