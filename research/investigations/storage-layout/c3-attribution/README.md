# Attributing the C3 loss of built-in Paged on the 14900K

Whitefoot#263 proposes a built-in `Paged<T>`. Its acceptance criterion C3 asks
that Snowghost's layout stores built on it cost no more than the hand-written
two-level pages. The confirming run on the owner's i9-14900K
([../c3-14900k/](../c3-14900k/README.txt), run 37725144848) failed C3. This
investigation separates the causes before any verdict on #263, as the owner
directed on 2026-10-08. Whitefoot implements `Paged`; Snowghost measures it.

## The gap to attribute

The like-for-like build, `nodeshf` (3abffd8: one `Paged` per existing store,
header-first cell, wf-exp-f1971c00269a), differs from `pages` (8d5fab0) only
in `renderer/layout/{pages.wf,boundary.wf,module.wfm}` and the compiler. Best
of three interleaved rounds on html5, per run, relative to `pages`:

| stage | lane | twin | nodeshf |
|---|---|---:|---:|
| boxes | seq | 1.10 | 1.27 |
| boxes | par-4 | 0.97 | 1.06 |
| layout | seq | 1.00 | 1.02 |
| layout | par-4 | 1.01 | 1.03 |

The box build is the only stage clearly outside the twin's spread. Page faults
of one 20-repetition box run: pages 123,490, nodeshf 243,062. That run timed
3 repetitions at 10 ms resolution, so the box cells carry about 3% of
quantization alone.

The pooled builds `paged` and `hf` differ from `pages` in their store design as
well (context-wide pools, 33 files), so a gap there cannot be attributed to the
`Paged` type alone; they are outside this question.

## Hypotheses and builds

Branch research/c3-attr, each build one commit:

- **E1, compiler** (483ef80): `nodeshf`'s tree with the three files restored
  from `pages`. Against `pages` only the compiler differs (wf-0b7f5c5b9854 vs
  wf-exp-f1971c00269a, plus kit and workflows); against `nodeshf` only the
  storage source.
- **E2, page geometry and growth** (0f2d9e1): E1 with the hand-written pages
  given `Paged`'s geometry and growth: every native page holds
  `paged_page_len::<T>()` slots, with no small first page; growth allocates
  every page through the logical capacity, intervening ones included; cells
  are initialized only through the logical length. The pointer directory and
  the access path stay hand-written. Against E1 only geometry and growth
  differ; against `nodeshf` only the access path and `Paged`'s own directory.
- **E3, where the time goes**: a perf stat (task clock, page faults) and a
  perf profile of the box and layout stages of every build except the twin.

## Comparison and decision rule, fixed before measuring

One run of `time-14900k` on research/timing-c3attr (07fd14f): builds `pages`,
`twin` (the same drivers), `e1`, `e2`, `nodeshf`; html5 only; the box, text
and layout modes at 10 repetitions, seq and par-4; three interleaved rounds;
no style stage, no edit timing. A cell is the best round's per-run time.

- **Noise band** b, per stage and lane: |twin/pages − 1|, at least 2%.
- **Gap present**: nodeshf/pages − 1 > b on the box stage. If not, the
  like-for-like gap is within noise at this scale, and the C3 failure rests on
  the pooled builds; stop and report that.
- **Compiler**: e1/pages outside 1 ± b means the compiler accounts for that
  part of the gap.
- **Geometry and growth confirmed** when, on the box stage, (e2 − e1) is at
  least half of (nodeshf − e1), outside the band in both lanes, and e2's page
  faults are within 20% of nodeshf's. Whitefoot then changes `Paged`'s
  geometry or growth (a smaller first page, lazy pages), and Snowghost
  re-measures with its experiment releases.
- **Geometry and growth rejected** when e2 stays within 1 ± b of e1 while
  nodeshf is outside it. The remaining cause is `Paged`'s directory or access
  lowering, and E3's profiles of e2 and nodeshf locate it.
- Anything between is reported as partial, with each share and the profiles.

This is a probe: if the band is too wide to apply the rule, the next run
raises the repetitions on the deciding stage only.

## Results

Not yet measured.
