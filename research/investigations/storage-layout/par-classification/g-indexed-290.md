# G-indexed loop permission at wf-64c0f956df63

## Question and criterion

Does Whitefoot's indexed-reduction extension admit at least 16 of the same
32 complete loops, as written or with local helper effect/signature narrowing?
This recount reuses the function-and-purpose mapping and hosted report method
in [the previous measurement](g-indexed-274.md), whose result was 0/32 both
as written and after allowed narrowing. Every row remains applicable on this
branch, created from `80345cb8138c63507f882285739839b610c686c9`;
its renderer tree is `da84aa05704ddb876d21541aebcc6e6dfc2cb166`.

The pre-registered acceptance criterion is unchanged: **at least 16/32 complete
loops permitted with no source change beyond local helper narrowing**.
Algorithms, passes and storage stay fixed; direct-store rewrites do not count
as narrowing. The comparison is the hosted loop ledger at the unchanged
renderer tree under the old and new releases, followed by a new report if
qualifying helper narrowing is found. Fewer than 16 permissions after allowed
narrowing rejects the criterion on this source; a hard source refusal leaves
unreported sites unmeasured, rather than counting them as PAR denials.

The language oracle is [PAR-2 at Whitefoot
64c0f956df63cb42322fd1c1207c77bf69689818](https://github.com/Ming-Research/Whitefoot/blob/64c0f956df63cb42322fd1c1207c77bf69689818/spec/kernel-spec.md#13-execution-overlap),
kernel specification v0.107. This branch alone replaces `wf-691ea8106920`
with `wf-64c0f956df63` to measure that rule; neither submodule moves.
The rule admits measure reads of the selected indexed storage, exactly one
fresh immutable single-use temporary step for an operation update, unsigned
`+sat`, fixed integer/Bool constant marks, and integer/Bool record-field
families. A copied cell followed by an operation temporary is two steps;
the rule does not admit that spelling. Calls retain their projected effect
footprints; a whole-root helper write is not a visible indexed-cell update.

## Hosted measurement

The existing [temporary report workflow](../../../../.github/workflows/par-count.yml)
is retargeted to `research/par-count-290` and the requested compiler release;
its flags and exit/stream capture remain unchanged. The existing `check`
workflow runs `make check` on the same revision. Both use GitHub-hosted
Ubuntu 24.04, never the self-hosted runner. No build, test, check or performance
measurement runs locally; CI status is polled at most once every five minutes.

Results and the per-row ledger will be recorded after hosted CI completes.
