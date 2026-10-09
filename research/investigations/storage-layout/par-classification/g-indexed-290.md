# G-indexed loop permission at wf-64c0f956df63

## Question and criterion

Does Whitefoot's indexed-reduction extension admit at least 16 of the same
32 complete loops, as written or with local helper effect/signature narrowing?
This recount reuses the function-and-purpose mapping and hosted report method
in [the #274 measurement](g-indexed-274.md), whose result was 0/32 both
as written and after allowed narrowing. All 32 rows remain applicable.

The pre-registered criterion is unchanged: **at least 16/32 complete loops
permitted with no source change beyond local helper narrowing**. Its prior
wording is in [Whitefoot's indexed-reduction investigation at the previous
release](https://github.com/Ming-Research/Whitefoot/blob/691ea81069202c88f17df9ce0005d17a6d47ada7/research/investigations/indexed-reductions/DESIGN.md#criterion).
Algorithms, passes and storage stay fixed; direct-store rewrites and folding
copied-cell chains do not count as helper narrowing. The owner separately
authorized the FN-1 source compatibility adaptation below: it removes only
unreachable statements, without changing the counted bodies or their inputs.
Fewer than 16 permissions after allowed narrowing rejects the criterion on
this source; a hard source refusal leaves unreported sites unmeasured.

The language oracle is [PAR-2 at Whitefoot
64c0f956df63cb42322fd1c1207c77bf69689818](https://github.com/Ming-Research/Whitefoot/blob/64c0f956df63cb42322fd1c1207c77bf69689818/spec/kernel-spec.md#13-execution-overlap),
kernel specification v0.107. This branch pins `wf-64c0f956df63` instead of
#274's `wf-691ea8106920` (v0.102); neither pin nor submodule moves in this
adaptation/recount task. PAR-2 now admits measure reads of the exact indexed
storage, exactly one fresh immutable single-use operation temporary,
unsigned `+sat`, fixed integer/Bool constant marks, and integer/Bool
record-field families. A copied cell followed by an operation temporary is
two steps and remains outside the rule. Calls retain projected effect
footprints; a whole-root helper write is not a visible indexed-cell update.

## FN-1 source compatibility adaptation

The earlier [report run 37884003424](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37884003424)
and [gate run 37884003441](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37884003441)
stopped at the first unreachable tail, before the PAR listing:

```text
./text/normalization/decompose.wf:88:3: error[FN-1]: UnreachableStatement
  source:   return at;
  marker:   ^^^^^^^^^^
```

[FN-1](https://github.com/Ming-Research/Whitefoot/blob/64c0f956df63cb42322fd1c1207c77bf69689818/spec/kernel-spec.md#8-functions-generics-contracts)
gives an ordinary loop a normal successor exactly when some break resolves
to it. The approved [v0.106 rule change](https://github.com/Ming-Research/Whitefoot/blob/64c0f956df63cb42322fd1c1207c77bf69689818/spec/log.md#2026-10-09-v0106-a-break-free-loop-has-no-normal-successor)
therefore makes the old required fallback statements unreachable. This
illustrative statement fragment shows the source shape; it is not a compiled
fixture:

```whitefoot
loop @scan {
  return at;
}
return at;
```

The final return is deleted. No break or replacement return is introduced.
For multi-statement tails, the first FN-1 diagnostic establishes that the
remaining sibling statements are unreachable too, so the entire tail is
removed together.

The [source-only adaptation commit
3c7a80d](https://github.com/Ming-Research/Snowghost-wf/commit/3c7a80df4da78ba65975a9c9a21111f07bccf82e)
removes **71 FN-1 sites: 93 unreachable statements in 70 functions across
45 files**. One function, `consume_attribute_value`, has two sites, after
its quoted and unquoted scanning loops. The sites comprise 9 in text, 1 in
URL, 5 in CSS, 14 in HTML, 1 in PNG, 9 in oracle drivers and 32 in tools.
**The FN-1 adaptation removed only unreachable statements and does not
change any loop's body or permission inputs.** Reachable statements,
interfaces, contracts, effect rows and imports are unchanged. The compiler
required no unused binding, helper or import cleanup. The initial renderer
tree was `da84aa05704ddb876d21541aebcc6e6dfc2cb166`; the adapted tree is
`9a4217b3ff2bdd4bf975636ac245de3f22b33dac`.

A temporary hosted diagnostic pass checked each module, repeated its check
only after a reported FN-1 deletion, and preserved every diagnostic and the
resulting source patch. Its first normalization sample took less than a
second, establishing the scale before checking the remaining modules.
[Run 37886136934](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37886136934),
on `47b9159cc439db476822125e12f7689b8ef26bbf`, records the 71 first FN-1
diagnostics and acceptance of all 52 gate modules after the deletions. Its
artifact `fn1-diagnostics-47b9159cc439db476822125e12f7689b8ef26bbf` contains
`deletions.json`, `results.json`, each compiler log and `adaptation.patch`.
The committed source patch matches that artifact exactly. This diagnostic
pass is module acceptance evidence, not the complete `make check` gate.
The temporary probe is removed in [9be190c](https://github.com/Ming-Research/Snowghost-wf/commit/9be190cc28e5c57282e8f9d9cbe8fe407ce40536).

## Hosted measurement

The existing [temporary report workflow](../../../../.github/workflows/par-count.yml)
builds `layout_oracle` with `--cache`, `--fragments function`, `--par` and
`--par-ledger`. Its capture preserves the source revision, pin, release
manifest, compiler stdout/stderr, compiler exit and complete `PAR loop`
listing. The independent existing `check` workflow runs `make check`.
Both use GitHub-hosted Ubuntu 24.04, never the self-hosted runner. No build,
test, check or performance measurement runs locally; CI status is polled
at most once every five minutes.

**Result: 11/32 permitted as written and 11/32 after allowed local helper
narrowing. The ≥16/32 criterion fails, five admissions short.** Compared with
#274's 0/32 before and after narrowing, #290 adds eleven complete-loop
permissions. No qualifying helper narrowing is applied, so the second count
uses the same measured bodies and is not a hypothetical rewrite or a second
compiler run. All 32 sites are measured; none is not applicable or unmeasured.
There is **no other new source refusal** after the FN-1 adaptation.

Both workflows ran on `9be190cc28e5c57282e8f9d9cbe8fe407ce40536`, with the
adapted renderer tree above. The report compiler exited **0**, stderr is
empty, and the captured release manifest confirms `wf-64c0f956df63`,
Whitefoot `64c0f956df63cb42322fd1c1207c77bf69689818` and v0.107. The ledger
contains **1,122 PAR loop entries**, with exactly one for each of the
32 mapped sites. Its SHA-256 is
`17734febca8c6ddea6e9951b83030f0ac2b9af3254aa292098aaef35ba3c48b1`.
`make check` passes the renderer module checks, document arena self-test,
21 design-checker tests and design lint on the same revision.

| CI run | Revision | Result and evidence |
|---|---|---|
| [37887019421 — parallel permission report](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37887019421) | `9be190cc28e5c57282e8f9d9cbe8fe407ce40536` | Success; compiler exit 0, empty stderr, complete 1,122-entry ledger and release manifest in artifact `par-count-9be190cc28e5c57282e8f9d9cbe8fe407ce40536`. |
| [37887019378 — make check](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37887019378) | `9be190cc28e5c57282e8f9d9cbe8fe407ce40536` | Success; the complete project gate with the adopted release. |

| Measurement | As written | After allowed narrowing | First condition-1 denials | First condition-2 denials |
|---|---|---|---|---|
| #274, `wf-691ea8106920`, v0.102 | 0/32 | 0/32 | 17 | 15 |
| #290, `wf-64c0f956df63`, v0.107 | 11/32 | 11/32 | 7 | 14 |

The eleven newly permitted sites are `split_closings`, `grid_build_tracks`,
`grid_shim_baselines`, `finish_lines`, `structure_flags`, `bucket`,
`root_font_readers`, the three `restyle` mark-cleanup loops, and
`order_reaches`. The counted bodies are identical to #274 despite the FN-1
compatibility deletions elsewhere in their functions or modules. Permission
is for complete source bodies; it does not establish actual runtime overlap,
performance or invocation hotness.

## The 32 loop sites

Locations are relative to `renderer/`. The classified old coordinate is
retained beside the current function and purpose. `split_closings` is at
line 1220 rather than its classified line 1189; `sort_run` is now at line 100
rather than 101 because `run_end`'s dead return was removed. Each row applies
to the complete counted body, including its nested work and other writes.
The #274 column gives that measurement's identical before/after status.
The diagnostic column quotes the new ledger's complete detail field.

| Old location | Current location and function | Loop purpose | As written, #290 | After allowed narrowing, #290 | #274 before / after | Diagnostic / first PAR condition | Change / helper assessment |
|---|---|---|---|---|---|---|---|
| `font/lookup_filters.wf:95` | `font/lookup_filters.wf:95` — `set_coverage_bits` | Coverage-word OR over coverage ranges; nested glyph updates use `old`/`marked` temporaries. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set filters^.inner[slot] = marked;` | None; copied cell plus operation temporary, including nested glyph work. |
| `font/lookup_filters.wf:103` | `font/lookup_filters.wf:103` — `set_coverage_bits` | Coverage-word OR over glyphs; destination words may collide. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set filters^.inner[slot] = marked;` | None; copied cell plus operation temporary. |
| `font/lookup_filters.wf:139` | `font/lookup_filters.wf:139` — `build_filters` | Union subtable coverage through `set_coverage_bits`, whose effect writes the whole filters root. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &filters` | None; whole-root helper call and two-step helper update. |
| `font/shape_plan.wf:211` | `font/shape_plan.wf:211` — `mark_lookups` | Lookup-mask OR through `old`/`combined` temporaries. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set flags^.inner[index] = combined;` | None; copied cell plus operation temporary. |
| `font/shape_plan.wf:267` | `font/shape_plan.wf:267` — `collect_stage` | Default-feature lookup-mask OR through whole-root `mark_lookups` calls. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at flags` | None; whole-root helper call and two-step helper update. |
| `layout/flow.wf:1189` | `layout/flow.wf:1220` — `split_closings` | Closing-event marks are direct constant `1_u8` stores. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its constant-mark form; admitted as written. |
| `layout/grid.wf:1070` | `layout/grid.wf:1070` — `grid_place` | Definite-item occupancy through `grid_mark`, plus stored-child item updates through `grid_put`. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &occupied` | None qualifies; occupancy call plus sequence-selected whole-record get/put. |
| `layout/grid.wf:1239` | `layout/grid.wf:1239` — `grid_build_tracks` | Overlapping item spans mark `GridTrack.used`, a Bool field of a record element. | Permitted | Same; no narrowing | Denied, condition 2 / same | `eligible; indexed constant marks` | None applied for its Bool record-field mark form; admitted as written. |
| `layout/grid.wf:2273` | `layout/grid.wf:2273` — `grid_shim_baselines` | Row-bucket ascent maximum through the `larger` temporary. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed reductions under imax` | None applied for its one-step imax temporary; admitted as written. |
| `layout/inline.wf:1087` | `layout/inline.wf:1087` — `finish_lines` | Text endpoint marks are direct constant `1_u8` stores. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its fixed 1_u8 marks; admitted as written. |
| `layout/table.wf:532` | `layout/table.wf:532` — `measure_rows` | Shared row `TableTrack` fields are updated through record get/put, beside scalar `longest` and per-cell outputs. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at natural` | None qualifies; narrowing per-cell outputs leaves shared TableTrack get/put. |
| `layout/tableborders.wf:127` | `layout/tableborders.wf:127` — `collapse_borders` | Column border conflicts use hidden-dominates-maximum through `merge_vertical`/`merge_horizontal`. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &vedge` | None qualifies; hidden-dominates-maximum selection is not a fixed admitted operator. |
| `layout/tableborders.wf:143` | `layout/tableborders.wf:143` — `collapse_borders` | Row/group border conflicts use hidden-dominates-maximum through the same helpers. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &vedge` | None qualifies; same border selection through whole-root helpers. |
| `layout/tableborders.wf:185` | `layout/tableborders.wf:185` — `collapse_borders` | Cell border conflicts use hidden-dominates-maximum through the same helpers. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &vedge` | None qualifies; same border selection through whole-root helpers. |
| `layout/tablegrid.wf:526` | `layout/tablegrid.wf:526` — `measure_columns` | Column record fixed/percent/originates/constrained updates include floating `fmax`. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | None qualifies; whole-Col get/put and floating fmax remain. |
| `layout/tablegrid.wf:543` | `layout/tablegrid.wf:543` — `measure_columns` | Column record min/max updates also read `constrained` to select the contribution. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | None qualifies; whole-Col get/put and constrained-dependent contribution remain. |
| `layout/tablegrid.wf:600` | `layout/tablegrid.wf:600` — `measure_fixed` | Column record `originates` is set to the constant `True()` through get/put. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | None qualifies; exposing originates needs a direct-field-store rewrite. |
| `oracle/layout/edit.wf:1196` | `oracle/layout/edit.wf:1196` — `structure_flags` | Remapped changed-node flags are direct constant `True()` stores. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its True mark form; admitted as written. |
| `oracle/layout/layout.wf:286` | `oracle/layout/layout.wf:286` — `bucket` | Rectangle histogram uses indexed `+sat`, outside the fixed #274 operator set. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed reductions under +sat` | None applied for its unsigned +sat and root len forms; admitted as written. |
| `style/cascade.wf:184` | `style/cascade.wf:184` — `test_bucket` | Bucket rule testing calls `test_rule`/`offer` for cascade key plus winning declaration, beside scalar `fits`. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at keys` | None qualifies; key-dependent winner payload through test_rule/offer remains. |
| `style/cascade.wf:270` | `style/cascade.wf:270` — `match_indexed` | Unkeyed rule testing calls the same richer cascade update, beside scalar `fits`. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at keys` | None qualifies; same key-dependent winner payload remains. |
| `style/cascade.wf:419` | `style/cascade.wf:419` — `offer` | Per-longhand winner compares the existing key and conditionally stores key plus declaration payload. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at set keys^[longhand] = key;` | None qualifies; old-key observation and winner payload stores remain. |
| `style/incremental.wf:77` | `style/incremental.wf:77` — `map_pseudos` | Pseudo flags use `ior`, but first-pseudo selection reads the existing cell before overwriting it. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set first^.inner[element] = cvt.wrap::<u64, u32>(p);` | None qualifies; first-pseudo check and nonconstant replacement remain. |
| `style/incremental.wf:996` | `style/incremental.wf:996` — `root_font_readers` | Root-font declaration scan uses direct-map `reading` writes and constant indexed `columns=True()` stores. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its True marks beside direct-map output; admitted as written. |
| `style/incremental.wf:1162` | `style/incremental.wf:1162` — `restyle_level` | Owner flags are constant marks; `structural` is a constant scalar mark; `place_style` and an error exit add obligations. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set structural = True();` | None qualifies; scalar structural=True, failure return and place_style remain. |
| `style/incremental.wf:1387` | `style/incremental.wf:1387` — `restyle` | Touched-first cleanup stores constant zero through the state marks root. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its fixed zero-mark form; admitted as written. |
| `style/incremental.wf:1418` | `style/incremental.wf:1418` — `restyle` | Touched cleanup stores constant zero through the state marks root. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its fixed zero-mark form; admitted as written. |
| `style/incremental.wf:1424` | `style/incremental.wf:1424` — `restyle` | Wanted-element cleanup stores constant zero through the state marks root. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed constant marks` | None applied for its fixed zero-mark form; admitted as written. |
| `style/levels.wf:30` | `style/levels.wf:30` — `level_index` | Depth histogram reads its partial count to guard an exact `+`, with parent validation and error returns. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: PAR-2 indexed accumulator: the indexed operation must belong to the scalar accumulator's admitted set, at set sizes.inner[depth] = seen + 1_u64;` | None qualifies; exact +, partial-count guard and failure exits remain. |
| `style/restyle.wf:97` | `style/restyle.wf:97` — `order_reaches` | Reach-bucket histogram already spells indexed `+wrap` directly. | Permitted | Same; no narrowing | Denied, condition 1 / same | `eligible; indexed reductions under +wrap` | None applied for its direct +wrap and root len forms; admitted as written. |
| `style/structure.wf:369` | `style/structure.wf:369` — `structure_restyle` | Pseudo holes are struct `NodeId` overwrites, outside integer/Bool indexed cells. | Denied, condition 2 | Same; no narrowing | Denied, condition 2 / same | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at set state^.cascade.nodes.inner[pseudo] = hole;` | None qualifies; NodeId record replacement and wider state accesses remain. |
| `text/normalization/decompose.wf:101` | `text/normalization/decompose.wf:100` — `sort_run` | Canonical-class histogram uses `current`/`next` temporaries before its indexed `+wrap` store. | Denied, condition 1 | Same; no narrowing | Denied, condition 1 / same | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set counts[class64] = next;` | None; copied cell plus operation temporary. |

## Helper narrowing boundary

No qualifying effect/signature-only helper narrowing admits another complete
loop. The after-narrowing column repeats the same measured verdict because
no helper source changes qualify; it is not a separate after-change run.

`set_coverage_bits` and `mark_lookups` already take separate mutable primitive
array roots, but copy the cell before the operation temporary. Narrowing
their effects leaves that two-step form unchanged, and their callers still
write through whole-root helpers. `grid_place` retains stored-sequence-selected
`GridItem` get/put beside its occupancy helper. Narrowing the independent
per-cell outputs in `measure_rows` leaves shared whole-`TableTrack` get/put.
The three `measure_columns`/`measure_fixed` rows retain whole-`Col` get/put;
the first two also retain floating maximum or existing-field-dependent
contributions. Returning a modified record and storing it through a helper
does not expose a record-field reduction under PAR-2. Border and cascade
winner helpers retain richer selection operations. Replacing these paths
with direct stores, changing their carriers or rewriting their update
operations exceeds the experiment's narrowing limit.

## Rule boundaries and disposition

The operation-temporary boundary remains exactly one step. These are
illustrative statement fragments, with an independent typed index `e`,
contribution `x` and already-bounded indexed cell; they are not separately
compiled fixtures. PAR-2 admits:

```whitefoot
let next = counts[e] +wrap x;
set counts[e] = next;
```

It excludes the copied-cell chain:

```whitefoot
let current = counts[e];
let next = current +wrap x;
set counts[e] = next;
```

The coverage loops and `mark_lookups` use the second structure with `ior`;
`sort_run` uses it with `+wrap`. The compiler's first denial now says that
an update requires an admitted operation directly or through one fresh,
unchanged, single-use temporary; it no longer mislabels those nonconstant
values as constant marks. `grid_shim_baselines` uses the first structure
with `imax` and is measured permitted. These four copied-cell rows
remain denied, whereas the one-step row is permitted.

The root measure distinction is similarly concrete. For an owned Box array
`counts`, this illustrative fragment keeps the bound check inside the loop:

```whitefoot
if e < counts.inner.len {
  set counts.inner[e] = counts.inner[e] +wrap 1_u64;
}
```

`order_reaches` is measured permitted with its in-body `starts.inner.len`
guard unchanged; #274 denied it at that root occurrence. `bucket` is also
permitted with its unsigned `+sat` update and in-body length guard. The
histogram's first pass is independent of partial element values: `.len`
reads descriptor storage that the cell updates leave unchanged. A prefix
read, a check of the existing cell value, or a contribution that reads the
indexed root remains outside the family. This is a measure-read permission,
not permission for arbitrary root reads or replacement of bounds checking.

Constant indexed marks and scalar writes are also distinct. Fixed
`set flags[e] = True();` is an indexed mark family; a whole-binding
`set structural = True();` is still outside the scalar accumulator's
operation-form requirement. The complete `restyle_level` loop retains that
scalar write, its failure exit and `place_style`, so permitting its indexed
owner marks alone cannot permit the whole loop.

These observed form boundaries are the result to send to Whitefoot, rather
than a renderer rewrite hidden inside helper narrowing. No compiler issue,
TODO gap, design decision, pull request or board update is created by this
task. The Whitefoot pin stays `wf-64c0f956df63`; `whitefoot-kit` stays
`1a0bf6b7b560341a1e9510c1a2a5ebb1d9a98ab6` and `design/skill` stays
`57f13a2b9e0f795a376335334d34b2237197b700`. The migration probe is removed;
the pre-existing temporary recount workflow stays on this work branch for
reproduction until the indexed-loop investigation closes. No runtime,
output-correctness or performance conclusion follows from permission alone.

## Completion review

A separate read-only reviewer examined
`010136b718d8dd835e2ad29741cdc8458d0747fd..9be190cc28e5c57282e8f9d9cbe8fe407ce40536`
plus the completed research record, applying checklist groups A, D, C, T,
R, M and V and applicable G1–G3/DC1–DC4 design checks. It inspected the
complete renderer diff and original contexts, all 71 first FN-1 diagnostics,
the matching hosted patch, all 32 source bodies and relevant helpers,
#274's result, exact pinned PAR-2/FN-1, scoped design nodes, raw ledger,
release manifest and actual hosted gate logs. It independently confirmed
source-body identity, all counts and diagnostics, the lack of qualifying
helper narrowing, the unchanged pin/submodules/workflow and the complete
gate's success. It ran no build, test, compiler, lint or CI polling.

**Findings: none within scope.** Design lint passed: seven nodes, depth one,
59 decisions and 24 rejected alternatives; the six decisions above the
CI review base's 53 are inherited branch changes, with no design diff in
this task. PR delivery checks are not applicable because the task prohibits
a PR. Runtime behavior and performance remain outside this recount's scope.
The final research-record commit changes only this document; the paired
successful runs above validate the same renderer, pin and workflow.
