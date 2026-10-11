"""Summarize the temporary hosted DHAT pass wired by memory-mechanism.py.

DHAT's per-program-point gb/gbk values share the process byte-peak instant;
mb/mbk values do not. Never add mb/mbk to claim a process or subset peak.
See https://valgrind.org/docs/manual/dh-manual.html (including realloc).
Remove this helper with the temporary workflow after archiving its evidence.
"""
import argparse
import json
import os
from pathlib import Path
import re


FIELDS = ('tb', 'tbk', 'gb', 'gbk', 'eb', 'ebk')
NAMES = ('total_requested_bytes', 'total_allocation_events',
         'live_requested_bytes_at_process_byte_peak',
         'live_blocks_at_process_byte_peak',
         'live_requested_bytes_at_exit', 'live_blocks_at_exit')


def totals(points):
    return {name: sum(point[field] for point in points)
            for field, name in zip(FIELDS, NAMES)}


def summarize(profile_path, log_path):
    """Read a completed heap-mode DHAT profile and cross-check its log.

    The caller must separately require exit zero and no timeout. A truncated
    profile or a process killed early must never be used as a completed run.
    """
    profile = json.loads(Path(profile_path).read_text())
    if profile.get('dhatFileVersion') != 2 or profile.get('mode') != 'heap' or profile.get('bklt') is not True:
        raise ValueError('requires DHAT v2 heap profile with lifetime accounting')
    frames, points = profile['ftbl'], profile['pps']
    if not isinstance(frames, list) or not all(isinstance(frame, str) for frame in frames) or not isinstance(points, list):
        raise ValueError('invalid DHAT point/frame tables')
    for key in ('te', 'tg'):
        if type(profile[key]) is not int or profile[key] < 0:
            raise ValueError(('invalid DHAT instruction time', key))
    if profile['tg'] > profile['te']:
        raise ValueError('global peak occurs after exit')
    whitefoot, other = [], []
    for point in points:
        for key in FIELDS:
            if type(point[key]) is not int or point[key] < 0:
                raise ValueError(('invalid DHAT count', key))
        if point['gb'] > point['tb'] or point['eb'] > point['tb'] or point['gbk'] > point['tbk'] or point['ebk'] > point['tbk']:
            raise ValueError('live allocation exceeds cumulative allocation')
        if not isinstance(point['fs'], list) or any(type(i) is not int or not 0 <= i < len(frames) for i in point['fs']):
            raise ValueError('invalid DHAT stack frame index')
        stack = [frames[i] for i in point['fs']]
        # Disjoint stack-origin partition, not a phase partition. Realloc is
        # attributed by DHAT to the original allocation stack; deeper callers
        # can also be truncated by --num-callers. Retain the raw profile.
        bucket = whitefoot if any(re.search(r'\bwf__heap_(?:take|retake)\b', frame) for frame in stack) else other
        bucket.append(point)
    total = totals(points)
    log = Path(log_path).read_text(errors='replace')
    observed = []
    for label in ('Total', 'At t-gmax', 'At t-end'):
        matches = re.findall(r'==\d+==\s*' + re.escape(label) + r':\s*([\d,]+) bytes in ([\d,]+) blocks\s*', log)
        if len(matches) != 1:
            raise ValueError(('missing or ambiguous DHAT summary', label))
        observed.extend(int(value.replace(',', '')) for value in matches[0])
    if observed != [total[name] for name in NAMES]:
        raise ValueError(('DHAT point sums disagree with printed totals', observed, total))
    return dict(
        scope='whole process: intercepted allocator requests from startup through cleanup',
        units='successful allocation events and requested bytes; realloc adds one event and its new extent; DHAT normalizes zero-size allocations to one byte',
        exclusions='mmap-only storage, stack, allocator metadata/slack, profiler memory, and unintercepted bootstrap/linker allocations; not RSS',
        peak_definition='maximum simultaneously live requested bytes; block count is at that byte-peak instant',
        independent_peak_live_blocks=None,
        subset_definition='original allocation stack includes wf__heap_take/retake; subset live values are at the process peak, not subset peaks',
        phase_limitation='no phase totals: includes initial layout and every preceding edit; realloc retains its original allocation stack',
        command=profile['cmd'], pid=profile['pid'],
        instruction_times=dict(global_byte_peak=profile['tg'], exit=profile['te']),
        whole_process=total,
        whitefoot_heap_origin=totals(whitefoot),
        other_or_unresolved_origin=totals(other),
        program_points=len(points), whitefoot_program_points=len(whitefoot))


def controls(directory):
    """CI-only arithmetic and rejection witnesses for this new reader."""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('allocation summary controls require CI')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    profile_path, log_path = directory / 'fixture.dhat.json', directory / 'fixture.stderr'
    profile = dict(dhatFileVersion=2, mode='heap', bklt=True, te=50, tg=40,
                   cmd='synthetic summary fixture', pid=1,
                   ftbl=['[root]', '0x1: wf__heap_take (heap.c:16)', '0x2: library'],
                   pps=[dict(tb=100, tbk=2, gb=0, gbk=0, eb=0, ebk=0, mb=100, mbk=2, fs=[1]),
                        dict(tb=200, tbk=3, gb=200, gbk=3, eb=10, ebk=1, mb=200, mbk=3, fs=[2])])
    log = ('==1== Total: 300 bytes in 5 blocks\n'
           '==1== At t-gmax: 200 bytes in 3 blocks\n'
           '==1== At t-end: 10 bytes in 1 blocks\n')
    profile_path.write_text(json.dumps(profile))
    log_path.write_text(log)
    valid = summarize(profile_path, log_path)
    expected = dict(zip(NAMES, (300, 5, 200, 3, 10, 1)))
    if valid['whole_process'] != expected or valid['whitefoot_heap_origin']['total_requested_bytes'] != 100:
        raise ValueError('allocation summary arithmetic/partition witness failed')
    records = ['correct common-instant peak (200), not sum of individual maxima (300)']
    wrong = json.loads(json.dumps(profile))
    del wrong['pps'][0]['gbk']
    cases = [('missing global-peak blocks', wrong, log),
             ('printed total disagrees', profile, log.replace('300 bytes', '301 bytes')),
             ('individual maxima substituted for common peak', profile, log.replace('200 bytes in 3', '300 bytes in 5')),
             ('missing printed exit', profile, log.split('==1== At t-end')[0]),
             ('wrong mode', dict(profile, mode='copy'), log)]
    for label, data, text in cases:
        profile_path.write_text(json.dumps(data))
        log_path.write_text(text)
        try:
            summarize(profile_path, log_path)
        except (ValueError, KeyError):
            records.append('rejected: ' + label)
        else:
            raise ValueError(('allocation summary accepted invalid witness', label))
    (directory / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--metadata', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('CLI is for hosted CI only')
    record = dict(label=args.label, profile=str(args.profile), log=str(args.log),
                  **summarize(args.profile, args.log))
    if args.metadata is not None:
        record['workload_metadata'] = json.loads(args.metadata.read_text())
    args.output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
