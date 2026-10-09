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
Its prior wording is in [Whitefoot's indexed-reduction investigation at the
previous release](https://github.com/Ming-Research/Whitefoot/blob/691ea81069202c88f17df9ce0005d17a6d47ada7/research/investigations/indexed-reductions/DESIGN.md#criterion).
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

**Result: the recount is blocked by a hard source refusal before the PAR
listing. The as-written count is unknown/32, and the count with allowed
narrowing is unknown/32. All 32 sites are unmeasured; the ≥16/32 criterion
is not determined.** Zero emitted permissions is not a measured 0/32 result.
No PAR condition was reported for any of these sites, so none is labeled
permitted or denied by this release.

Both workflows ran on `a622deaf66fef50d077d7163f44a308c4e562788` with the
unchanged renderer tree above. The report compiler exited **1**;
`compiler.stdout` and `loops-64c0f956.txt` are both empty. The captured
release manifest confirms the requested tag, Whitefoot commit and v0.107.
The report artifact preserves the source revision, pin, manifest, compiler
streams and exit code despite the failed build. This also supplies observed
negative-path evidence for the existing capture's `if/else` repair.

| CI run | Revision | Result and evidence |
|---|---|---|
| [37884003424 — parallel permission report](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37884003424) | `a622deaf66fef50d077d7163f44a308c4e562788` | Failure; compiler exit 1 at D1 below, zero PAR rows. [Artifact 11596450048](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37884003424/artifacts/11596450048) is `par-count-a622deaf66fef50d077d7163f44a308c4e562788`. |
| [37884003441 — make check](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37884003441) | `a622deaf66fef50d077d7163f44a308c4e562788` | Failure; normalization module rejected at D1, renderer target stops and make exits 2. The document arena self-test and design lint were not reached. |

### Source refusal D1

The exact report compiler stderr is:

```text
./text/normalization/decompose.wf:88:3: error[FN-1]: UnreachableStatement
  source:   return at;
  marker:   ^^^^^^^^^^
```

The gate independently reports the same diagnostic while checking
`pkg::text::normalization`; its preceding base geometry, static atoms, atoms,
document arena and line-break module checks accepted. This is one observed
first source refusal, not evidence that no later refusal exists.

`run_end` at `renderer/text/normalization/decompose.wf:60` has an ordinary
`loop @scan` with no `break` targeting it: both stopping branches return from
the function, and otherwise the body advances `at` and repeats. The return
after the loop at line 88 is structurally unreachable. A minimal control-flow
fragment of this shape is:

```whitefoot
loop {
  return at;
}
return at;
```

This is an illustrative statement fragment, not a separately compiled fixture.
[FN-1 at the adopted revision](https://github.com/Ming-Research/Whitefoot/blob/64c0f956df63cb42322fd1c1207c77bf69689818/spec/kernel-spec.md#8-functions-generics-contracts)
gives an ordinary loop a normal successor exactly when some break resolves
to it, and rejects structurally unreachable statements. The
[v0.106 change log](https://github.com/Ming-Research/Whitefoot/blob/64c0f956df63cb42322fd1c1207c77bf69689818/spec/log.md#2026-10-09-v0106-a-break-free-loop-has-no-normal-successor)
records that change between the two releases. The observed refusal agrees
with this newer rule; it is not a PAR-2 denial or evidence of an indexed
reduction bug. The same renderer tree compiled under the previous release,
as documented in the prior measurement.

The task forbids working around a refusal. No return was removed, no module
was excluded, and no renderer spelling was changed to obtain a ledger.
Without source acceptance, the requested checks of temporary RHS permission
and the in-body histogram length read remain unmeasured.

## Helper narrowing boundary

Source inspection identifies no effect/signature-only narrowing that admits
an additional complete loop. `set_coverage_bits` and `mark_lookups` already
take separate mutable primitive-array roots, but copy the cell before the
operation temporary; changing their effects leaves that form unchanged.
Their callers also retain whole-root writes, rather than visible indexed
updates. `grid_place` retains stored-sequence-indexed `GridItem` get/put
beside its occupancy helper. Narrowing the independent per-cell outputs
in `measure_rows` leaves shared whole-`TableTrack` get/put.
The three `measure_columns`/`measure_fixed` rows retain whole-`Col` get/put;
the first two also retain floating maximum or existing-field-dependent
contributions. Returning a modified record and storing it through a helper
does not expose a record-field reduction under PAR-2. Replacing those paths
with direct field stores is outside this experiment's narrowing limit.
Border and cascade winner helpers retain their richer selection operations;
effect narrowing cannot turn them into an admitted fixed cell operation.

No helper change or direct-store rewrite is applied. There is consequently
no helper diff or after-change report. The after-narrowing column carries
the same lack of measurement as the as-written column, rather than treating
source inspection as a compiler permission verdict.

## The 32 loop sites

The old/current function-and-purpose mapping is unchanged. Locations are
relative to `renderer/`; only `split_closings` differs from its classified
coordinate. Each status applies to the complete counted body. The #274 column
reports both of that measurement's identical before/after statuses.

**D1** in every new status is the global source refusal above, not a PAR
denial for that loop. No first PAR condition or per-loop diagnostic exists in
the empty new ledger. The last column is static inspection against PAR-2,
not an observed acceptance or rejection under this release.

| Old location | Current location and function | Loop purpose | As written, #290 | After allowed narrowing, #290 | #274 before / after | Diagnostic / first PAR condition | Change / spec-only assessment |
|---|---|---|---|---|---|---|---|
| `font/lookup_filters.wf:95` | `font/lookup_filters.wf:95` — `set_coverage_bits` | Coverage-word OR over coverage ranges; nested glyph updates use `old`/`marked` temporaries. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None; copied cell plus operation temporary, including nested glyph work. |
| `font/lookup_filters.wf:103` | `font/lookup_filters.wf:103` — `set_coverage_bits` | Coverage-word OR over glyphs; destination words may collide. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None; copied cell plus operation temporary. |
| `font/lookup_filters.wf:139` | `font/lookup_filters.wf:139` — `build_filters` | Union subtable coverage through `set_coverage_bits`, whose effect writes the whole filters root. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None; whole-root helper call and two-step helper update. |
| `font/shape_plan.wf:211` | `font/shape_plan.wf:211` — `mark_lookups` | Lookup-mask OR through `old`/`combined` temporaries. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None; copied cell plus operation temporary. |
| `font/shape_plan.wf:267` | `font/shape_plan.wf:267` — `collect_stage` | Default-feature lookup-mask OR through whole-root `mark_lookups` calls. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None; whole-root helper call and two-step helper update. |
| `layout/flow.wf:1189` | `layout/flow.wf:1220` — `split_closings` | Closing-event marks are direct constant `1_u8` stores. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its constant-mark form; permission unmeasured. |
| `layout/grid.wf:1070` | `layout/grid.wf:1070` — `grid_place` | Definite-item occupancy through `grid_mark`, plus stored-child item updates through `grid_put`. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; occupancy call plus sequence-selected whole-record get/put. |
| `layout/grid.wf:1239` | `layout/grid.wf:1239` — `grid_build_tracks` | Overlapping item spans mark `GridTrack.used`, a Bool field of a record element. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None needed for its Bool record-field mark form; permission unmeasured. |
| `layout/grid.wf:2273` | `layout/grid.wf:2273` — `grid_shim_baselines` | Row-bucket ascent maximum through the `larger` temporary. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its one-step imax temporary; permission unmeasured. |
| `layout/inline.wf:1087` | `layout/inline.wf:1087` — `finish_lines` | Text endpoint marks are direct constant `1_u8` stores. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its fixed 1_u8 marks; permission unmeasured. |
| `layout/table.wf:532` | `layout/table.wf:532` — `measure_rows` | Shared row `TableTrack` fields are updated through record get/put, beside scalar `longest` and per-cell outputs. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; narrowing per-cell outputs leaves shared TableTrack get/put. |
| `layout/tableborders.wf:127` | `layout/tableborders.wf:127` — `collapse_borders` | Column border conflicts use hidden-dominates-maximum through `merge_vertical`/`merge_horizontal`. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; hidden-dominates-maximum selection is not a fixed admitted operator. |
| `layout/tableborders.wf:143` | `layout/tableborders.wf:143` — `collapse_borders` | Row/group border conflicts use hidden-dominates-maximum through the same helpers. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; same border selection through whole-root helpers. |
| `layout/tableborders.wf:185` | `layout/tableborders.wf:185` — `collapse_borders` | Cell border conflicts use hidden-dominates-maximum through the same helpers. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; same border selection through whole-root helpers. |
| `layout/tablegrid.wf:526` | `layout/tablegrid.wf:526` — `measure_columns` | Column record fixed/percent/originates/constrained updates include floating `fmax`. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; whole-Col get/put and floating fmax remain. |
| `layout/tablegrid.wf:543` | `layout/tablegrid.wf:543` — `measure_columns` | Column record min/max updates also read `constrained` to select the contribution. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; whole-Col get/put and constrained-dependent contribution remain. |
| `layout/tablegrid.wf:600` | `layout/tablegrid.wf:600` — `measure_fixed` | Column record `originates` is set to the constant `True()` through get/put. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; exposing originates needs a direct-field-store rewrite. |
| `oracle/layout/edit.wf:1196` | `oracle/layout/edit.wf:1196` — `structure_flags` | Remapped changed-node flags are direct constant `True()` stores. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its True mark form; permission unmeasured. |
| `oracle/layout/layout.wf:286` | `oracle/layout/layout.wf:286` — `bucket` | Rectangle histogram uses indexed `+sat`, outside the fixed #274 operator set. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its unsigned +sat and root len forms; permission unmeasured. |
| `style/cascade.wf:184` | `style/cascade.wf:184` — `test_bucket` | Bucket rule testing calls `test_rule`/`offer` for cascade key plus winning declaration, beside scalar `fits`. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; key-dependent winner payload through test_rule/offer remains. |
| `style/cascade.wf:270` | `style/cascade.wf:270` — `match_indexed` | Unkeyed rule testing calls the same richer cascade update, beside scalar `fits`. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; same key-dependent winner payload remains. |
| `style/cascade.wf:419` | `style/cascade.wf:419` — `offer` | Per-longhand winner compares the existing key and conditionally stores key plus declaration payload. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; old-key observation and winner payload stores remain. |
| `style/incremental.wf:77` | `style/incremental.wf:77` — `map_pseudos` | Pseudo flags use `ior`, but first-pseudo selection reads the existing cell before overwriting it. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None qualifies; first-pseudo check and nonconstant replacement remain. |
| `style/incremental.wf:996` | `style/incremental.wf:996` — `root_font_readers` | Root-font declaration scan uses direct-map `reading` writes and constant indexed `columns=True()` stores. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its True marks beside direct-map output; permission unmeasured. |
| `style/incremental.wf:1162` | `style/incremental.wf:1162` — `restyle_level` | Owner flags are constant marks; `structural` is a constant scalar mark; `place_style` and an error exit add obligations. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None qualifies; scalar structural=True, failure return and place_style remain. |
| `style/incremental.wf:1387` | `style/incremental.wf:1387` — `restyle` | Touched-first cleanup stores constant zero through the state marks root. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its fixed zero-mark form; permission unmeasured. |
| `style/incremental.wf:1418` | `style/incremental.wf:1418` — `restyle` | Touched cleanup stores constant zero through the state marks root. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its fixed zero-mark form; permission unmeasured. |
| `style/incremental.wf:1424` | `style/incremental.wf:1424` — `restyle` | Wanted-element cleanup stores constant zero through the state marks root. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its fixed zero-mark form; permission unmeasured. |
| `style/levels.wf:30` | `style/levels.wf:30` — `level_index` | Depth histogram reads its partial count to guard an exact `+`, with parent validation and error returns. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None qualifies; exact +, partial-count guard and failure exits remain. |
| `style/restyle.wf:97` | `style/restyle.wf:97` — `order_reaches` | Reach-bucket histogram already spells indexed `+wrap` directly. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None needed for its direct +wrap and root len forms; permission unmeasured. |
| `style/structure.wf:369` | `style/structure.wf:369` — `structure_restyle` | Pseudo holes are struct `NodeId` overwrites, outside integer/Bool indexed cells. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 2 / same | D1; no PAR condition emitted | None qualifies; NodeId record replacement and wider state accesses remain. |
| `text/normalization/decompose.wf:101` | `text/normalization/decompose.wf:101` — `sort_run` | Canonical-class histogram uses `current`/`next` temporaries before its indexed `+wrap` store. | Unmeasured (D1) | Unmeasured (D1) | Denied, condition 1 / same | D1; no PAR condition emitted | None; copied cell plus operation temporary. |

## Rule boundaries and disposition

The requested temporary and length-read questions cannot receive measured
verdicts from this run. The normative distinction is nevertheless concrete.
In statement fragments with an independent index `e` and contribution `x`,
PAR-2 admits the one-step form:

```whitefoot
let next = counts[e] +wrap x;
set counts[e] = next;
```

It does not admit this two-step cell-copy chain:

```whitefoot
let current = counts[e];
let next = current +wrap x;
set counts[e] = next;
```

The coverage and lookup-mask loops use that second structure with `ior`,
and `sort_run` uses it with `+wrap`. `grid_shim_baselines` uses the first
structure with `imax`. The previously denied `order_reaches` histogram
already has the direct `+wrap` cell update and in-body root `.len` read;
the amended measure rule covers that read without hoisting it. These are
specification assessments; the new compiler emitted no verdict or new
diagnostic for any of them. The old misleading constant-mark diagnostic
therefore was not retested on this renderer.

The source compatibility refusal D1 is recorded here for Whitefoot, with its
minimal shape and normative explanation. No renderer workaround, compiler
issue, TODO entry, design change, pull request or board update was made.
Only the requested Whitefoot pin and temporary report-workflow target moved;
`whitefoot-kit` remains at `1a0bf6b7b560341a1e9510c1a2a5ebb1d9a98ab6`
and `design/skill` at `57f13a2b9e0f795a376335334d34b2237197b700`.
No Whitefoot gap was separately filed. This is a compatibility refusal
matching a specified rule, not evidence of a missing indexed reduction.

Work stops because the unchanged source is refused and the task forbids
working around it. A recount on this exact release needs separate
authorization to address source compatibility. The temporary workflow stays
on this work branch for that recount and is removed when the investigation
closes. No runtime, output-correctness or performance conclusion follows
from the empty permission listing.

## Completion review

A separate read-only reviewer examined
`80345cb8138c63507f882285739839b610c686c9..a622deaf66fef50d077d7163f44a308c4e562788`
plus the completed report, covering checklist groups A, D, T, R, M and V;
code checks were not applicable because no renderer source changed, and PR
delivery checks were not applicable because this task forbids a PR. It read
all 32 mapped bodies and relevant helpers, the previous classification and
method, the exact PAR-2 and FN-1, specification log, scoped design nodes and
the hosted artifact/logs. It independently confirmed the mapping, the prior
17 condition-1/15 condition-2 comparison, the empty new listing, compiler
exit and exact refusal, and the lack of qualifying helper narrowing.

The review's one local documentation finding was fixed: the used-field
carrier is named `GridTrack`, rather than the abbreviated `Track` copied
from the old report. The correction was checked against the declaration and
verified by the reviewer; no behavior or decision changed. No findings remain
within scope. Release compatibility and overall lint-backed design validation
remain unverified because the gate stops at normalization before design lint.
The review ran no build, test, check, compiler, lint or CI polling, and no such
operation ran locally during this task. The report's final commit changes
only this research record; the paired CI attempts above share the unchanged
renderer, adopted pin and report workflow.
