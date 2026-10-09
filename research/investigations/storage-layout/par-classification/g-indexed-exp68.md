# G-indexed loop permission at wf-exp-68fe93be539c

## Question and criterion

Does the copied-cell and call-form extension admit at least 16 of the same
32 complete G-indexed loops, as written or after local helper effect/signature
narrowing? The function-and-purpose mapping, complete-body counting method and
hosted report command are those of [the #290 recount](g-indexed-290.md),
which measured 11/32 before and after narrowing, and [the #274 recount](g-indexed-274.md),
which measured 0/32 in both columns. All 32 rows remain applicable.

The criterion is unchanged: **at least 16/32 complete loops permitted with
no source change beyond local helper narrowing**. Algorithms, passes and
storage stay fixed. A direct-store rewrite is not helper narrowing. The
pre-registered [criterion and prediction of 17](https://github.com/Ming-Research/Whitefoot/blob/68fe93be539c844f31d68ee98c2455c960a3379b/research/investigations/indexed-reductions/DESIGN.md#criterion-1)
reject the extension as insufficient if fewer than 16 are admitted; a hard
source refusal leaves any unreported sites unmeasured.

The oracle is [PAR-2 at Whitefoot
68fe93be539c844f31d68ee98c2455c960a3379b](https://github.com/Ming-Research/Whitefoot/blob/68fe93be539c844f31d68ee98c2455c960a3379b/spec/kernel-spec.md#13-execution-overlap),
kernel specification v0.109 draft on `claude/indexed-reduction-calls`.
`whitefoot.pin` moves from `wf-64c0f956df63` (v0.107) to
`wf-exp-68fe93be539c` only on `research/par-count-exp68`. This experiment
pin is not eligible for main. The inherited FN-1 adaptation is unchanged.

PAR-2 now permits an accumulator operand copied from the same cell earlier
in the same block, with at most one copy and one operation temporary. Both
are fresh, unwritten and used exactly once for their specified roles.
Intervening statements must have read/write footprints disjoint from the
indexed root and writes disjoint from the subscript/contribution inputs.
Subscripts and contributions still read nothing of the indexed binding.

A call can supply indexed updates when its reference argument resolves to
a prefix of the family's storage path and its callee has an indexed summary
for that parameter. The callee's whole body must use the parameter only for
measure reads or admitted operation, constant-mark or acyclic call-form
updates, preserving the storage path and length and one fixed kind per
disjoint family. Other arguments and their row accesses must be disjoint
from the root binding. All other complete-loop conditions still apply.

This release's call-form permission retains sequential lowering. The
recount measures source-loop permission only, with no timing or speed claim.
The implementation boundary is visible in
[`split_counted_range`](https://github.com/Ming-Research/Whitefoot/blob/68fe93be539c844f31d68ee98c2455c960a3379b/compiler/src/lowering/builder/split.rs#L280),
which retains the sequential path when an indexed family contains calls.

## Hosted method

The existing [par-count workflow](../../../../.github/workflows/par-count.yml)
builds `layout_oracle` with `--cache`, `--fragments function`, `--par` and
`--par-ledger`, preserving the revision, pin, release manifest, compiler
stdout/stderr, compiler exit code and full loop ledger in its artifact.
Only its branch selector and release/artifact paths change. The independent
existing `check` workflow runs the unchanged `make check` gate.

Both workflows use GitHub-hosted Ubuntu 24.04. No local or self-hosted build,
test, check or performance measurement is part of this recount. CI status
is polled at most once every five minutes.

## Result and CI evidence

**17/32 permitted as written and 17/32 after allowed narrowing. The ≥16/32
criterion passes, one admission above the threshold, and matches the prior
prediction of 17.** No qualifying narrowing is applied: the second column
uses the same measured bodies, not a hypothetical rewrite or a separate
post-change run. All 32 sites have exactly one ledger entry; none is
inapplicable or unmeasured. There is **no new renderer source refusal**.

Both workflows ran on `28f6ae7839cca4740ec8d957fa7fb8166eb67ec6`.
The renderer tree remains `9a4217b3ff2bdd4bf975636ac245de3f22b33dac`,
identical to #290's adapted source. The report compiler exited **0** and
stderr is empty. Its manifest identifies `wf-exp-68fe93be539c`, Whitefoot
`68fe93be539c844f31d68ee98c2455c960a3379b` and v0.109. The complete ledger
has **1,122 entries**; its SHA-256 is
`87b31cdca05b290be94636b9d725a07cdc0fa8e70d3cc501af3d7fe845b82862`.
Hosted `make check` accepts all 52 renderer modules, passes the document
arena self-test and all 21 design-checker tests, and passes design lint.

| CI run | Revision | Result and preserved evidence |
|---|---|---|
| [37904741267 — parallel permission report](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37904741267) | `28f6ae7839cca4740ec8d957fa7fb8166eb67ec6` | Success; compiler exit 0, empty stderr, full ledger and release manifest in artifact `par-count-28f6ae7839cca4740ec8d957fa7fb8166eb67ec6`. |
| [37904741220 — make check](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37904741220) | `28f6ae7839cca4740ec8d957fa7fb8166eb67ec6` | Success; complete existing gate with the experiment pin. |

| Measurement | As written | After allowed narrowing | First condition-1 denials | First condition-2 denials |
|---|---|---|---|---|
| #274, `wf-691ea8106920`, v0.102 | 0/32 | 0/32 | 17 | 15 |
| #290, `wf-64c0f956df63`, v0.107 | 11/32 | 11/32 | 7 | 14 |
| This recount, `wf-exp-68fe93be539c`, v0.109 draft | 17/32 | 17/32 | 7 | 8 |

## The 32 loop sites

Locations are relative to `renderer/`. The old classified coordinate is
retained beside the current function and purpose, reusing #290's mapping.
`split_closings` remains at line 1220, and `sort_run` remains at line 100
following the inherited FN-1 adaptation. Every verdict is for the complete
loop, including nested work, calls and other writes. C1 and C2 mean first
PAR condition 1 and 2; the diagnostic column preserves the complete detail
field verbatim. Each baseline column gives that recount's identical
before/after status. No source narrowing is applied to any row.

| Old location | Current location and function | Complete-loop purpose | #274 before / after | #290 before / after | As written, exp68 | After allowed narrowing, exp68 | Diagnostic / first condition | Change / narrowing assessment |
|---|---|---|---|---|---|---|---|---|
| `font/lookup_filters.wf:95` | `font/lookup_filters.wf:95` — `set_coverage_bits` | Coverage-word OR over coverage ranges; nested glyph updates use `old`/`marked` temporaries. | Denied C1 | Denied C1 | Permitted | Permitted | `eligible; indexed reductions under ior` | New permission: fresh single-use copied cell plus ior temporary; no narrowing. |
| `font/lookup_filters.wf:103` | `font/lookup_filters.wf:103` — `set_coverage_bits` | Coverage-word OR over glyphs; destination words may collide. | Denied C1 | Denied C1 | Permitted | Permitted | `eligible; indexed reductions under ior` | New permission: same copied-cell ior form in the nested glyph loop; no narrowing. |
| `font/lookup_filters.wf:139` | `font/lookup_filters.wf:139` — `build_filters` | Union subtable coverage through `set_coverage_bits`, whose effect writes the whole filters root. | Denied C2 | Denied C2 | Permitted | Permitted | `eligible; indexed reductions under ior` | New permission: set_coverage_bits supplies an ior indexed summary; no narrowing. |
| `font/shape_plan.wf:211` | `font/shape_plan.wf:211` — `mark_lookups` | Lookup-mask OR through `old`/`combined` temporaries. | Denied C1 | Denied C1 | Permitted | Permitted | `eligible; indexed reductions under ior` | New permission: fresh single-use old/combined ior chain; no narrowing. |
| `font/shape_plan.wf:267` | `font/shape_plan.wf:267` — `collect_stage` | Default-feature lookup-mask OR through whole-root `mark_lookups` calls. | Denied C2 | Denied C2 | Permitted | Permitted | `eligible; indexed reductions under ior` | New permission: mark_lookups supplies an ior indexed summary; no narrowing. |
| `layout/flow.wf:1189` | `layout/flow.wf:1220` — `split_closings` | Closing-event marks are direct constant `1_u8` stores. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `layout/grid.wf:1070` | `layout/grid.wf:1070` — `grid_place` | Definite-item occupancy through `grid_mark`, plus stored-child item updates through `grid_put`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &model^.items` | Still denied: grid_mark now supplies occupancy marks, exposing unpartitioned model item get/put; narrowing cannot establish sequence-selected item independence. |
| `layout/grid.wf:1239` | `layout/grid.wf:1239` — `grid_build_tracks` | Overlapping item spans mark `GridTrack.used`, a Bool field of a record element. | Denied C2 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `layout/grid.wf:2273` | `layout/grid.wf:2273` — `grid_shim_baselines` | Row-bucket ascent maximum through the `larger` temporary. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under imax` | Same permission; admitted as written, with no narrowing. |
| `layout/inline.wf:1087` | `layout/inline.wf:1087` — `finish_lines` | Text endpoint marks are direct constant `1_u8` stores. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `layout/table.wf:532` | `layout/table.wf:532` — `measure_rows` | Shared row `TableTrack` fields are updated through record get/put, beside scalar `longest` and per-cell outputs. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at put_i32(list: natural, at: i, value: natural_height)` | Still denied, now C1 at put_i32: its nonconstant replacement is not an indexed update. Narrowing per-cell outputs still leaves shared whole-TableTrack get/put. |
| `layout/tableborders.wf:127` | `layout/tableborders.wf:127` — `collapse_borders` | Column border conflicts use hidden-dominates-maximum through `merge_vertical`/`merge_horizontal`. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: a copied cell or single-use temporary requires no intervening root access or write to index/contribution support, at merge_vertical(vedge: &vedge, stride: stride, column: c, first: 0_u64, end: rows, value: sides.left)` | Still denied, now C1 inside the helper summary: merge_edge tests the copied cell and conditionally writes the root before its imax write-back. Hidden-dominates-maximum is not one fixed admitted kind. |
| `layout/tableborders.wf:143` | `layout/tableborders.wf:143` — `collapse_borders` | Row/group border conflicts use hidden-dominates-maximum through the same helpers. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: a copied cell or single-use temporary requires no intervening root access or write to index/contribution support, at merge_vertical(vedge: &vedge, stride: stride, column: 0_u64, first: r, end: below, value: sides.left)` | Still denied, now C1: the same merge_edge summary boundary; no qualifying narrowing. |
| `layout/tableborders.wf:185` | `layout/tableborders.wf:185` — `collapse_borders` | Cell border conflicts use hidden-dominates-maximum through the same helpers. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: a copied cell or single-use temporary requires no intervening root access or write to index/contribution support, at merge_vertical(vedge: &vedge, stride: stride, column: column_first, first: row_first, end: row_end, value: sides.left)` | Still denied, now C1: the same merge_edge summary boundary; no qualifying narrowing. |
| `layout/tablegrid.wf:526` | `layout/tablegrid.wf:526` — `measure_columns` | Column record fixed/percent/originates/constrained updates include floating `fmax`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | Still denied: whole-Col get/put and floating fmax; effect/signature narrowing leaves these operations. |
| `layout/tablegrid.wf:543` | `layout/tablegrid.wf:543` — `measure_columns` | Column record min/max updates also read `constrained` to select the contribution. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | Still denied: whole-Col get/put and a contribution chosen by existing constrained; no qualifying narrowing. |
| `layout/tablegrid.wf:600` | `layout/tablegrid.wf:600` — `measure_fixed` | Column record `originates` is set to the constant `True()` through get/put. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | Still denied: exposing originates needs a direct-field-store rewrite of whole-Col get/put, outside narrowing. |
| `oracle/layout/edit.wf:1196` | `oracle/layout/edit.wf:1196` — `structure_flags` | Remapped changed-node flags are direct constant `True()` stores. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `oracle/layout/layout.wf:286` | `oracle/layout/layout.wf:286` — `bucket` | Rectangle histogram uses indexed `+sat`, outside the fixed #274 operator set. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under +sat` | Same permission; admitted as written, with no narrowing. |
| `style/cascade.wf:184` | `style/cascade.wf:184` — `test_bucket` | Bucket rule testing calls `test_rule`/`offer` for cascade key plus winning declaration, beside scalar `fits`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at keys` | Still denied: test_rule/offer select a key and its winner payload; no qualifying narrowing. |
| `style/cascade.wf:270` | `style/cascade.wf:270` — `match_indexed` | Unkeyed rule testing calls the same richer cascade update, beside scalar `fits`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at keys` | Still denied: the same key-dependent winner payload through test_rule/offer; no qualifying narrowing. |
| `style/cascade.wf:419` | `style/cascade.wf:419` — `offer` | Per-longhand winner compares the existing key and conditionally stores key plus declaration payload. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at set keys^[longhand] = key;` | Still denied: old-key observation and nonconstant key/payload stores; no helper narrowing applies. |
| `style/incremental.wf:77` | `style/incremental.wf:77` — `map_pseudos` | Pseudo flags use `ior`, but first-pseudo selection reads the existing cell before overwriting it. | Denied C1 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set first^.inner[element] = cvt.wrap::<u64, u32>(p);` | Still denied: first-pseudo selection reads the old cell before nonconstant replacement; no helper narrowing applies. |
| `style/incremental.wf:996` | `style/incremental.wf:996` — `root_font_readers` | Root-font declaration scan uses direct-map `reading` writes and constant indexed `columns=True()` stores. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/incremental.wf:1162` | `style/incremental.wf:1162` — `restyle_level` | Owner flags are constant marks; `structural` is a constant scalar mark; `place_style` and an error exit add obligations. | Denied C1 | Denied C1 | Denied C1 | Denied C1 | `condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set structural = True();` | Still denied: structural=True is a scalar mark; failure return and place_style add obligations. Narrowing does not admit the complete body. |
| `style/incremental.wf:1387` | `style/incremental.wf:1387` — `restyle` | Touched-first cleanup stores constant zero through the state marks root. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/incremental.wf:1418` | `style/incremental.wf:1418` — `restyle` | Touched cleanup stores constant zero through the state marks root. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/incremental.wf:1424` | `style/incremental.wf:1424` — `restyle` | Wanted-element cleanup stores constant zero through the state marks root. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/levels.wf:30` | `style/levels.wf:30` — `level_index` | Depth histogram reads its partial count to guard an exact `+`, with parent validation and error returns. | Denied C1 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: the indexed operation must belong to the scalar accumulator's admitted set, at set sizes.inner[depth] = seen + 1_u64;` | Still denied: exact + is outside the operation set, with a partial-count guard and failure returns; no helper narrowing applies. |
| `style/restyle.wf:97` | `style/restyle.wf:97` — `order_reaches` | Reach-bucket histogram already spells indexed `+wrap` directly. | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under +wrap` | Same permission; admitted as written, with no narrowing. |
| `style/structure.wf:369` | `style/structure.wf:369` — `structure_restyle` | Pseudo holes are struct `NodeId` overwrites, outside integer/Bool indexed cells. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at set state^.cascade.nodes.inner[pseudo] = hole;` | Still denied: NodeId record overwrite, outside integer/Bool cells; no helper narrowing applies. |
| `text/normalization/decompose.wf:101` | `text/normalization/decompose.wf:100` — `sort_run` | Canonical-class histogram uses `current`/`next` temporaries before its indexed `+wrap` store. | Denied C1 | Denied C1 | Permitted | Permitted | `eligible; indexed reductions under +wrap` | New permission: fresh single-use current/next +wrap chain; no narrowing. |

## Changes since #290 and narrowing boundary

Six rows gain permission on identical bodies:

- `set_coverage_bits`, `font/lookup_filters.wf:95` and `:103`: the nested
  coverage-range and glyph loops now admit the fresh `old`/`marked` copied-cell
  `ior` chain.
- `build_filters`, `font/lookup_filters.wf:139`: its `set_coverage_bits` call
  now supplies a valid indexed `ior` summary for the separate filters root.
- `mark_lookups`, `font/shape_plan.wf:211`: the fresh `old`/`combined` copied-cell
  `ior` chain is now admitted.
- `collect_stage`, `font/shape_plan.wf:267`: its `mark_lookups` call now supplies
  a valid indexed `ior` summary for the separate flags root.
- `sort_run`, `text/normalization/decompose.wf:100` (classified line 101): its
  fresh `current`/`next` copied-cell `+wrap` chain is now admitted.

All eleven #290 permissions remain permitted. The other fifteen rows remain
denied, but five have a changed first diagnostic. `grid_place` still reports
condition 2, now at `&model^.items` rather than `&occupied`: the occupancy
helper is summarized, leaving sequence-selected whole-record item get/put.
`measure_rows` now reports condition 1 at `put_i32`, whose arbitrary
replacement value is not a fixed indexed operation or constant mark.
The three `collapse_borders` loops now report condition 1 through
`merge_vertical`, exposing `merge_edge`'s intervening root access/write
boundary instead of the former whole-root condition-2 footprint. These are
changed denial explanations, not complete-loop admissions.

**Applied narrowing diffs: none.** The two newly summarized font helpers
already take their mutable primitive array roots separately from layout.
For the remaining rows, an effect/signature-only change cannot remove all
complete-body blockers. Narrowing `measure_rows`' per-cell output helpers
would leave shared whole-`TableTrack` get/put. The grid and column loops
retain whole-record reads/replacements; the column cases also retain
floating maximum or old-field-dependent contributions. Turning a get/put
sequence into field updates is a direct-store rewrite, not narrowing.
Border helpers retain hidden-dominates-maximum selection, and cascade
helpers retain key-dependent winner payloads. The direct first-pseudo,
scalar-mark, guarded exact-add and `NodeId` replacement bodies have no
helper narrowing that removes their blockers. No algorithm, pass, storage,
operator, cell-update spelling or renderer interface changes are counted.

## Rule boundaries for Whitefoot

The copied-cell form is now observed permitted in the four direct-update
rows. This is the exact statement shape in the counted `sort_run` loop,
with an already-bounded `class64` and an independent contribution; it is a
source fragment, not a separately compiled fixture:

```whitefoot
let current = counts[class64];
let next = current +wrap 1_u64;
set counts[class64] = next;
```

The font bit updates use the same shape with `ior`. Their callers also now
have complete-loop permission without any narrowing. Call-form permission
is a permission result only: this release retains those call-form loops'
sequential lowering, so this recount establishes neither overlap nor speed.

The fifteen denials stay outside the rule. A useful minimal boundary is the
actual statement shape in `merge_edge` (inside its bounds guard):

```whitefoot
let current = list^.inner[at];
if current < 0_i32 {
  return unit;
}
if value < 0_i32 {
  set list^.inner[at] = -1_i32;
  return unit;
}
let wider = imax(current, value);
set list^.inner[at] = wider;
```

This fragment is not a new compiled fixture. `current` is observed by a
branch as well as used by `imax`; an intervening statement can write the
root, and the family mixes a constant mark with an operation update.
PAR-2 requires a single-use copied operand, disjoint intervening footprints
and one fixed family kind. The three complete border loops are observed
denied with the exact condition-1 diagnostics in the table. Supporting
hidden-dominates-maximum needs a broader selection/operator rule; narrowing
a helper's effect or signature cannot supply it.

A second compact boundary is `put_i32`'s store:

```whitefoot
if at < list^.inner.len {
  set list^.inner[at] = value;
}
```

This is an arbitrary replacement, so it supplies neither an operation
update nor a constant-mark summary. The observed `measure_rows` denial now
points to that call. Narrowing this helper to an iteration's output element
would still leave the complete loop's shared row-record get/put; it cannot
be counted as an extra admission. These boundaries explain the remaining
result without a renderer workaround or a claim that every shared update
now qualifies. No new hard source diagnostic or compiler issue is filed.

## Disposition and limits

The experiment passes its source-permission criterion on the unchanged
renderer. Runtime values, output correctness, actual overlap, invocation
hotness and performance are outside this measurement. No local build,
test, check or timing, self-hosted run, pull request, main-line change,
status-board update, renderer workaround or separate backlog item is part
of this task. The observations above are the record to send to Whitefoot.

`whitefoot-kit` stays `1a0bf6b7b560341a1e9510c1a2a5ebb1d9a98ab6` and
`design/skill` stays `57f13a2b9e0f795a376335334d34b2237197b700`.
There is no design-tree change. The inherited temporary report workflow
stays on this experiment branch for reproduction until the indexed-loop
investigation closes. The final report-only change leaves the measured
renderer, pin, submodules and workflow identical to the paired CI runs.

## Completion review

A separate read-only reviewer examined
`5b8e7281905eeba9207a4fc5b6c0b8d642be0e2e..28f6ae7839cca4740ec8d957fa7fb8166eb67ec6`
plus this completed research record, checking groups A, D, T, R, M and V
and applicable G1–G3/DC1–DC4 design checks. It read the complete diff,
all 32 loop bodies and relevant helpers, prior recounts, exact PAR-2,
the call-form lowering boundary, applicable design nodes, raw report
artifact, hosted gate logs and gate metadata. It independently confirmed
the mapping, every verbatim diagnostic, counts, source identity, comparison,
narrowing boundary and both minimal denied fragments.

**Findings: none within scope.** A1–A4, D1–D4, T1, T3–T4, R1–R2, R4,
M1 and V1–V2 pass. Group C, T2, R3 and PR-delivery items V3–V4 are not
applicable: no source or interface change, new capture machinery,
architectural choice or PR is part of this task. G1 and DC3 are not
applicable without node or implementing-code changes; G2, G3, DC1, DC2
and DC4 pass within the measurement scope.

Hosted design lint reports seven nodes, depth one, 59 decisions and
24 rejected alternatives. The six decisions above the CI review base's
53 are inherited; this task has no design diff. The reviewer ran no
compiler, build, test, lint or CI polling. Negative-path execution of the
inherited capture remains unverified because no hard source refusal occurred.
Runtime behavior, overlap and performance remain outside the review scope.
