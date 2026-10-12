# html5 sentence edits on per-block Paged storage: attribution

## Question

The 2026-10-11 14900K retest of per-block `Paged` layout storage (Snowghost-wf#61)
left one cell undecided: html5 sentence edits at 4 workers had a median about
4.8% slower than main (about 124 µs per edit, so 5–6 µs), with the candidate's
own twin 3.3% slower and the cell's noise at 5%. The question is where the
extra time goes, and whether it comes from Whitefoot's generated code for
`Paged` access.

## Method

Hosted runner (`ubuntu-24.04`, x86-64), Callgrind, both builds from one
compiler release (wf-26355924f942). Base is the hand-written page tables at
c10c909; candidate is per-block `Paged` at 644263d. The E1 html5 sentence
script has 60 operations. The sequential driver is collected only inside
`wf_oracle.layout.incremental_after`, so only the timed edit work is counted.
`profile.py` builds and runs both, and the temporary workflow
`.github/workflows/sentence-profile.yml` drives it.

- Pass 1, run 38208449670: instruction counts, with a second base build as
  the noise control.
- Pass 2, run 38213637879: the same scoped runs with `--cache-sim=yes
  --branch-sim=yes`, using Valgrind's cache model for the hosted CPU.

## Results

Both builds do identical edit work (the same per-edit counts). The base twin
differs from base by 0 instructions in total and 0 in every function.

| Event (60 edits) | Base | Candidate | Δ |
|---|---|---|---|
| Instructions | 146,891,267 | 138,755,294 | −5.5% |
| Data reads | 38,815,952 | 36,250,636 | −6.6% |
| Data writes | 23,876,545 | 21,696,009 | −9.1% |
| L1 data read misses | 1,007,788 | 1,025,432 | +1.8% |
| Last-level data read misses | 6,538 | 13,199 | +101.9% |
| Last-level data write misses | 3,450 | 5,620 | +62.9% |
| Conditional branch mispredictions | 434,794 | 420,242 | −3.3% |

The candidate executes fewer instructions. The hand-written table's slot
lookup (`slot_geometry`, `slot_cursor`, `slot_output`) disappears, worth
−8.1 M, against +1.0 M in `effective_output`. Its one cost is about 8,800
extra last-level misses, about 147 per edit. At 40–80 ns per miss that is
6–12 µs per edit, the same size as the 5–6 µs measured on the 14900K.

Extra last-level read misses by function (self, candidate − base):
`range_geometry` +1,889, `range_positioned` +1,585, `splice_position_frame`
+1,061, `splice_position` +630, `effective_output` +577. These are the
functions that walk each block's entry sequence during the splice. Write
misses: `splice_position` +1,170, `memset` +898, `line_break.build_runs` +484.

## Conclusion

The slowdown is memory locality, not Whitefoot code generation. With one
`Paged` per block, the entries the splice path walks are spread over many
separate allocations, where the hand-written tables kept them close. The
instruction count of the `Paged` access path is lower than the hand-written
one, so there is no generated-code defect to report to Whitefoot.

Not verified:
- The cache model is Valgrind's simulation of the hosted CPU, not the 14900K.
- The runs are sequential, while the undecided cell was 4 workers.
- The 147-misses-per-edit to 5–6 µs link is an estimate from memory latency,
  not a measurement.

Measuring last-level misses on the 14900K with hardware counters, for both
builds at 4 workers, would confirm or reject the conclusion.
