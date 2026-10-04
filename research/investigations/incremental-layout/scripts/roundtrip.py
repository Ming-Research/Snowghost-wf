"""Checks the output of `layout_oracle edit` on a script of edits that each
have an inverse (research/investigations/incremental-layout/run.sh roundtrip).

usage: python3 roundtrip.py OUTPUT SCRIPT

OUTPUT holds the `base hash` line and the `edit I hash` lines, one for each
edit line of SCRIPT. Edit 1, 3, ...
are forward edits and 2, 4, ... their inverses: every inverse must return the
base hash, and every forward edit should change it. Prints the counts, and
exits with 1 when an inverse does not return the base hash; a forward edit
that leaves the hash unchanged is reported, not failed, since a kind may
change nothing the dump holds."""
import re
import sys

expected = sum(1 for line in open(sys.argv[2], 'rb') if line[:1] in (b'T', b'D', b'C', b'K', b'B', b'X'))
base = None
hashes = {}
for line in open(sys.argv[1]):
    m = re.match(r'base hash ([0-9a-f]{16}) bytes (\d+)$', line)
    if m:
        base = m.group(1)
    m = re.match(r'edit (\d+) hash ([0-9a-f]{16}) bytes (\d+)( inc (same|DIFF|refused))?$', line)
    if m:
        hashes[int(m.group(1))] = m.group(2)
if base is None or len(hashes) != expected:
    print('%d edit hash lines for %d edits' % (len(hashes), expected))
    sys.exit(1)
forward = [i for i in sorted(hashes) if i % 2 == 1]
inverse = [i for i in sorted(hashes) if i % 2 == 0]
changed = sum(1 for i in forward if hashes[i] != base)
restored = sum(1 for i in inverse if hashes[i] == base)
print('%d forward edits, %d change the hash; %d inverse edits, %d restore the base hash'
      % (len(forward), changed, len(inverse), restored))
sys.exit(0 if restored == len(inverse) and len(forward) == len(inverse) else 1)
