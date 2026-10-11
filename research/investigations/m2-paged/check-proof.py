"""Check proof artifacts with the same verifier used by altered-evidence controls.

Status checks alone cannot establish the intended refusal and emitted split;
this callable verifier checks those records and lets CI falsify each condition.
Remove together with the temporary m2-paged-proof.yml before branch readiness.
"""

import re
import shutil
import sys
import tempfile
from pathlib import Path


POSITIVE = ('natural-paged', 'grow-inverse', 'emission', 'build', 'runtime')
NEGATIVE = 'grow-inverse-corrupt'
REQUIRED = tuple(f'{name}.status' for name in (*POSITIVE, NEGATIVE)) + (
    f'{NEGATIVE}.log', 'natural-paged.log', 'emission.log',
    'runtime.log', 'natural-paged.ll',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    for name in REQUIRED:
        require((root / name).is_file(), f'missing evidence: {name}')
    for name in POSITIVE:
        require(int((root / f'{name}.status').read_text()) == 0, f'{name} failed')
    require(int((root / f'{NEGATIVE}.status').read_text()) != 0,
            'corrupt inverse accepted')
    diagnostic = (root / f'{NEGATIVE}.log').read_text()
    rules = re.findall(r'error\[([^]]+)\]', diagnostic)
    require(bool(rules) and set(rules) == {'RANGE-3'}, 'unrelated refusal')
    require('UndischargedRangeFact' in diagnostic, 'missing range diagnostic')
    require('entry_slot' in diagnostic, 'missing inverse diagnostic')
    ledger = (root / 'natural-paged.log').read_text()
    require(re.search(r'^PAR loop\s+.*natural-paged\.wf:\d+\s+loop\s+permitted\s+eligible;',
                      ledger, re.M), 'owner motion not eligible')
    emission = (root / 'emission.log').read_text()
    require(re.search(r'^PAR split\s+translate_owner_suffix\s+loop at \S+\s+split independent map over',
                      emission, re.M), 'owner motion not split')
    require((root / 'natural-paged.ll').stat().st_size > 0, 'empty LLVM')


def controls(root):
    alterations = [(f'failed {name}', f'{name}.status', '1\n') for name in POSITIVE]
    alterations += [('accepted inverse', f'{NEGATIVE}.status', '0\n'),
                    ('unrelated refusal', f'{NEGATIVE}.log',
                     'error[OP-4]: UndischargedRangeFact entry_slot\n'),
                    ('missing range diagnostic', f'{NEGATIVE}.log',
                     'error[RANGE-3]: entry_slot\n'),
                    ('missing inverse diagnostic', f'{NEGATIVE}.log',
                     'error[RANGE-3]: UndischargedRangeFact\n'),
                    ('denied loop', 'natural-paged.log',
                     'PAR loop natural-paged.wf:21 loop denied condition 1\n'),
                    ('missing eligible loop', 'natural-paged.log', ''),
                    ('missing split', 'emission.log', ''),
                    ('empty LLVM', 'natural-paged.ll', '')]
    alterations += [(f'missing {name}', name, None) for name in REQUIRED]
    for label, name, content in alterations:
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory)
            for evidence in REQUIRED:
                shutil.copyfile(root / evidence, sample / evidence)
            if content is None:
                (sample / name).unlink()
            else:
                (sample / name).write_text(content)
            try:
                verify(sample)
            except (ValueError, OSError) as error:
                print(f'detected {label}: {error}')
            else:
                raise ValueError(f'gate accepted altered evidence: {label}')


if __name__ == '__main__':
    evidence_root = Path(sys.argv[1])
    verify(evidence_root)
    print('growth accepted; corrupt inverse refused by RANGE-3; natural owner motion eligible, emitted and executed')
    controls(evidence_root)
