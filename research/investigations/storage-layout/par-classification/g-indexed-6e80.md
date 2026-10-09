# G-indexed loop permission and emission at wf-6e800e9160f7

## Question and criterion

Does Whitefoot main 6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58,
specification v0.115, admit at least 16 of the same 32 complete G-indexed
loops, as written or after local helper effect/signature narrowing?
The mapping and method are those of [exp68](g-indexed-exp68.md),
[#290](g-indexed-290.md) and [#274](g-indexed-274.md).
Algorithms, passes and storage remain fixed; a direct-store rewrite is
not helper narrowing. Fewer than 16 permissions rejects the criterion;
a hard source refusal leaves unreported sites unmeasured. The release
owner's prediction is 17, compared with exp68's 17, #290's 11 and #274's 0.

The oracle is [PAR-2 at the adopted Whitefoot revision](https://github.com/Ming-Research/Whitefoot/blob/6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58/spec/kernel-spec.md#13-execution-overlap).
Permission is measured independently from emission: every permitted
call-form and copied-cell row must also be traced in `--emit-llvm` output
to its generated splitter's lane acquire, publish and join calls.
A permitted row that retains sequential lowering rejects that emission
claim without changing its source-permission verdict. No runtime overlap,
output-correctness or performance claim follows from these measurements.

## Result and comparison

**17/32 permitted as written and 17/32 after allowed narrowing. The ≥16/32
criterion passes, one admission above the threshold, matching the release
owner's prediction of 17.** No narrowing is applied, so the second count
uses the same measured bodies; there is no qualifying narrowing diff or
separate post-narrowing run. All 32 sites are applicable and each has exactly
one ledger entry. None is unmeasured after the cancellation adaptations.

| Measurement | As written | After allowed narrowing | First C1 denials | First C2 denials |
|---|---|---|---|---|
| #274, `wf-691ea8106920`, v0.102 | 0/32 | 0/32 | 17 | 15 |
| #290, `wf-64c0f956df63`, v0.107 | 11/32 | 11/32 | 7 | 14 |
| exp68, `wf-exp-68fe93be539c`, v0.109 draft | 17/32 | 17/32 | 7 | 8 |
| This recount, `wf-6e800e9160f7`, v0.115 | 17/32 | 17/32 | 7 | 8 |

**No permission row or first diagnostic changes since exp68.** Relative to
#290, the same six rows gain permission: the copied-cell loops in
`set_coverage_bits` (two), `mark_lookups` and `sort_run`, and the call-form
loops in `build_filters` and `collect_stage`. All eleven #290 permissions
remain admitted. The other fifteen rows remain denied for the same first
conditions as exp68. #316's proved-separation grouping produces no change
to this set's permission results. The release's material change for the
call-form rows is in emission, independently audited below.

The renderer tree is `74da0b3e237d9fd36fed5f1422066b86da7f2d71` after
compatibility adaptations, versus exp68's
`9a4217b3ff2bdd4bf975636ac245de3f22b33dac`. The only renderer changes are
the nine matching upgrade files described below; every directory containing
the counted bodies is unchanged. `whitefoot-kit` remains
`1a0bf6b7b560341a1e9510c1a2a5ebb1d9a98ab6`, and `design/skill` remains
`57f13a2b9e0f795a376335334d34b2237197b700`. There is no design-tree change.

## Hosted method and source compatibility

The inherited [par-count workflow](../../../../.github/workflows/par-count.yml)
builds `layout_oracle` with `--cache`, `--fragments function`, `--par` and
`--par-ledger`, preserving the revision, pin, release manifest, compiler
streams, exit code and full loop ledger. Its branch selector, release paths
and ledger artifact name now select this recount. A second compiler
invocation uses `--emit-llvm --par --par-ledger` on the same entry and cache,
without `--fragments`, which the CLI forbids with `--emit-llvm`. It preserves
the whole LLVM module, emission streams/exit and per-definition counts and
extracts for `set_coverage_bits`, `build_filters`, `mark_lookups`,
`collect_stage` and `sort_run`, including their generated helpers. Because
the layout entry uses normalization queries rather than full normalization,
`sort_run` is outside its emitted closure; a targeted invocation uses
`--function pkg::text::normalization::sort_run --emit-llvm --par --par-ledger`
on the same graph, source, pin and cache. Counts refer to call instructions,
never runtime declarations. The all-module permission ledger and this
targeted function's permission/actualization ledger remain separate evidence.

The independent existing `check` workflow runs unchanged `make check`.
Both workflows use GitHub-hosted Ubuntu 24.04. No local or self-hosted
build, test, check or timing is part of this measurement; CI status is
polled at most once every five minutes.

The [v0.110–v0.115 specification log](https://github.com/Ming-Research/Whitefoot/blob/6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58/spec/log.md)
was read before the upgrade. v0.110 adds fieldless `IoError::Cancelled`
and cancellation parameters on host waits; v0.113 adds read-only shared
cancellation-state handles and makes cancellation firing a waiting call.
v0.111 adds map-reserve release, v0.112 extends range facts, v0.114 admits
the copied-cell and call-form indexed updates, and v0.115 changes canonical
scientific float spelling. Compiler overlap grouping also consumes proved
separations (#316); the ledger determines whether that changes these rows.

The renderer adaptations reuse [the matching cancellation classifier
fix](https://github.com/Ming-Research/Snowghost-wf/commit/551c21b0291656abf55014d62cb85d44f246aa54)
in `oracle/font_face/font_face.wf`:

```diff
     DeadlinePassed() => {
       return False();
     }
+    Cancelled() => {
+      return False();
+    }
```

`file_too_large` answers whether an `IoError` is `FileTooLarge`; cancellation
is a distinct host outcome, so `False()` is the specified classification.
Adding its explicit arm preserves exhaustive matching rather than hiding
an unhandled outcome. The file before this patch matches that fix's parent.
The other cancellation adaptations reuse [the upgrade's host-I/O patch](https://github.com/Ming-Research/Snowghost-wf/commit/d0cfd313ebacf1bac1010cfa248f68dfafbd87a9)
on matching files: `io_error_code` returns `0_u32` for fieldless `Cancelled`,
and its body/interface documentation now says that errors without a host
code return zero. Seven `write_once` sites and one `read_next` site in
oracle support and the six table-generator tool files pass a fresh
`cancel_never()` watch and close it after the host wait, before handling
the outcome. This satisfies the new argument/linear-handle obligations
and preserves the command-line tools' unbounded waits. It adds no polling,
deadline, cancellation source or renderer fallback.

These compatibility adaptations are separate from helper narrowing: none of
the 32 counted loop bodies or their permission inputs changes. The inherited
FN-1 unreachable-tail adaptation from #290 stays unchanged.

The initial runs on `7e1eaa3e8034894a9688a516e00266297f677ef9`, with only
the font-classifier arm applied, record the remaining compatibility refusals:

```text
./oracle/support/support.wf:327:3: error[ERR-2]: NonExhaustiveMatch
  source:   match error {
  marker:   ^^^^^^^^^^^^^
  missing_variants: [Cancelled]
```

The [initial par-count run 38001496505](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38001496505)
exited 1 before producing a loop ledger. The [initial gate run
38001496520](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38001496520)
stopped at the corresponding host-call signature change:

```text
./tools/static_atoms/static_atoms.wf:213:11: error[GRAM-11]: InvalidNamedArguments
  callee: read_next
  declared_parameters: [factory, input, destination, start, end, deadline, cancel]
```

These are the new exhaustive-match and required-argument obligations, not
a refusal of a sound natural form. The reused patches supply the correct
classification and the explicit noncancellable wait policy. The upgrade's
[hosted classifier controls, run 38000758589](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38000758589),
at `bb98d4371d0e148775e232e4d2938ddb9aec3be6` with `wf-f887e82c4611`,
exercise these identical classifier bodies: the correct mappings pass,
both missing-arm forms fail with ERR-2, and returning a nonzero code or
`True()` for cancellation is detected. This is reused classifier evidence
at v0.113, not a new runtime test of the v0.115 renderer.

## CI evidence

Both final workflows run on
`5c140fa63a346bdc0245fb402cac76ca163418f6`. The complete ledger contains
**1,122 entries** with SHA-256
`9d1c645ec40a064286cfb80d47909804dfcbf144c4c26204dafe3a1d04031fe8`.
It is byte-identical to the earlier adapted capture. The ledger build,
layout LLVM emission and targeted `sort_run` LLVM emission all exit **0**
with empty stderr.
The manifest identifies `wf-6e800e9160f7`, Whitefoot
`6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58` and v0.115.

| CI run | Revision | Result and evidence |
|---|---|---|
| [38002421307 — permission ledger and LLVM emission](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38002421307) | `5c140fa63a346bdc0245fb402cac76ca163418f6` | Success; artifact `par-count-5c140fa63a346bdc0245fb402cac76ca163418f6` preserves the full ledger, both LLVM modules, compiler streams/exits, release manifest, `emission-counts.json` and `emission-functions.ll`. |
| [38002421299 — make check](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38002421299) | `5c140fa63a346bdc0245fb402cac76ca163418f6` | Success; complete existing gate with the adopted release. |

Hosted [make check, run 38002421299](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38002421299)
passes on `5c140fa63a346bdc0245fb402cac76ca163418f6`: all 52 renderer
modules are accepted, the document arena self-test passes, all 21
design-checker tests pass and design lint passes. Lint reports seven nodes,
depth one, 59 decisions and 24 rejected alternatives. Its six decisions
above the CI review base's 53 are inherited; this recount has no design diff.
The measured renderer, pin and submodules are identical to the adapted
capture run; the later workflow adds only the missing normalization emission.

## The 32 loop sites

Locations are relative to `renderer/`. Function and purpose identify each
complete body, including nested work, calls and other writes. The old
classified coordinates are retained; `split_closings` remains at 1220 and
`sort_run` at 100. C1/C2 are the first PAR-2 condition reported, and each
detail is copied verbatim from the hosted ledger. Baseline columns give
those recounts' identical before/after statuses. No row receives narrowing.

| Old location | Current location and function | Complete-loop purpose | #274 before / after | #290 before / after | exp68 before / after | As written, 6e80 | After allowed narrowing, 6e80 | Diagnostic / first condition | Narrowing assessment |
|---|---|---|---|---|---|---|---|---|---|
| `font/lookup_filters.wf:95` | `font/lookup_filters.wf:95` — `set_coverage_bits` | Coverage-word OR over coverage ranges; nested glyph updates use `old`/`marked` temporaries. | Denied C1 | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under ior` | Same permission: fresh single-use copied cell plus ior temporary; no narrowing. |
| `font/lookup_filters.wf:103` | `font/lookup_filters.wf:103` — `set_coverage_bits` | Coverage-word OR over glyphs; destination words may collide. | Denied C1 | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under ior` | Same permission: same copied-cell ior form in the nested glyph loop; no narrowing. |
| `font/lookup_filters.wf:139` | `font/lookup_filters.wf:139` — `build_filters` | Union subtable coverage through `set_coverage_bits`, whose effect writes the whole filters root. | Denied C2 | Denied C2 | Permitted | Permitted | Permitted | `eligible; indexed reductions under ior` | Same permission: set_coverage_bits supplies an ior indexed summary; no narrowing. |
| `font/shape_plan.wf:211` | `font/shape_plan.wf:211` — `mark_lookups` | Lookup-mask OR through `old`/`combined` temporaries. | Denied C1 | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under ior` | Same permission: fresh single-use old/combined ior chain; no narrowing. |
| `font/shape_plan.wf:267` | `font/shape_plan.wf:267` — `collect_stage` | Default-feature lookup-mask OR through whole-root `mark_lookups` calls. | Denied C2 | Denied C2 | Permitted | Permitted | Permitted | `eligible; indexed reductions under ior` | Same permission: mark_lookups supplies an ior indexed summary; no narrowing. |
| `layout/flow.wf:1189` | `layout/flow.wf:1220` — `split_closings` | Closing-event marks are direct constant `1_u8` stores. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `layout/grid.wf:1070` | `layout/grid.wf:1070` — `grid_place` | Definite-item occupancy through `grid_mark`, plus stored-child item updates through `grid_put`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &model^.items` | Still denied: grid_mark now supplies occupancy marks, exposing unpartitioned model item get/put; narrowing cannot establish sequence-selected item independence. |
| `layout/grid.wf:1239` | `layout/grid.wf:1239` — `grid_build_tracks` | Overlapping item spans mark `GridTrack.used`, a Bool field of a record element. | Denied C2 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `layout/grid.wf:2273` | `layout/grid.wf:2273` — `grid_shim_baselines` | Row-bucket ascent maximum through the `larger` temporary. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed reductions under imax` | Same permission; admitted as written, with no narrowing. |
| `layout/inline.wf:1087` | `layout/inline.wf:1087` — `finish_lines` | Text endpoint marks are direct constant `1_u8` stores. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `layout/table.wf:532` | `layout/table.wf:532` — `measure_rows` | Shared row `TableTrack` fields are updated through record get/put, beside scalar `longest` and per-cell outputs. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at put_i32(list: natural, at: i, value: natural_height)` | Still denied C1 at put_i32: its nonconstant replacement is not an indexed update. Narrowing per-cell outputs still leaves shared whole-TableTrack get/put. |
| `layout/tableborders.wf:127` | `layout/tableborders.wf:127` — `collapse_borders` | Column border conflicts use hidden-dominates-maximum through `merge_vertical`/`merge_horizontal`. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: a copied cell or single-use temporary requires no intervening root access or write to index/contribution support, at merge_vertical(vedge: &vedge, stride: stride, column: c, first: 0_u64, end: rows, value: sides.left)` | Still denied C1 inside the helper summary: merge_edge tests the copied cell and conditionally writes the root before its imax write-back. Hidden-dominates-maximum is not one fixed admitted kind. |
| `layout/tableborders.wf:143` | `layout/tableborders.wf:143` — `collapse_borders` | Row/group border conflicts use hidden-dominates-maximum through the same helpers. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: a copied cell or single-use temporary requires no intervening root access or write to index/contribution support, at merge_vertical(vedge: &vedge, stride: stride, column: 0_u64, first: r, end: below, value: sides.left)` | Still denied C1: the same merge_edge summary boundary; no qualifying narrowing. |
| `layout/tableborders.wf:185` | `layout/tableborders.wf:185` — `collapse_borders` | Cell border conflicts use hidden-dominates-maximum through the same helpers. | Denied C2 | Denied C2 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: a copied cell or single-use temporary requires no intervening root access or write to index/contribution support, at merge_vertical(vedge: &vedge, stride: stride, column: column_first, first: row_first, end: row_end, value: sides.left)` | Still denied C1: the same merge_edge summary boundary; no qualifying narrowing. |
| `layout/tablegrid.wf:526` | `layout/tablegrid.wf:526` — `measure_columns` | Column record fixed/percent/originates/constrained updates include floating `fmax`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | Still denied: whole-Col get/put and floating fmax; effect/signature narrowing leaves these operations. |
| `layout/tablegrid.wf:543` | `layout/tablegrid.wf:543` — `measure_columns` | Column record min/max updates also read `constrained` to select the contribution. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | Still denied: whole-Col get/put and a contribution chosen by existing constrained; no qualifying narrowing. |
| `layout/tablegrid.wf:600` | `layout/tablegrid.wf:600` — `measure_fixed` | Column record `originates` is set to the constant `True()` through get/put. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at cols` | Still denied: exposing originates needs a direct-field-store rewrite of whole-Col get/put, outside narrowing. |
| `oracle/layout/edit.wf:1196` | `oracle/layout/edit.wf:1196` — `structure_flags` | Remapped changed-node flags are direct constant `True()` stores. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `oracle/layout/layout.wf:286` | `oracle/layout/layout.wf:286` — `bucket` | Rectangle histogram uses indexed `+sat`, outside the fixed #274 operator set. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed reductions under +sat` | Same permission; admitted as written, with no narrowing. |
| `style/cascade.wf:184` | `style/cascade.wf:184` — `test_bucket` | Bucket rule testing calls `test_rule`/`offer` for cascade key plus winning declaration, beside scalar `fits`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at keys` | Still denied: test_rule/offer select a key and its winner payload; no qualifying narrowing. |
| `style/cascade.wf:270` | `style/cascade.wf:270` — `match_indexed` | Unkeyed rule testing calls the same richer cascade update, beside scalar `fits`. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at keys` | Still denied: the same key-dependent winner payload through test_rule/offer; no qualifying narrowing. |
| `style/cascade.wf:419` | `style/cascade.wf:419` — `offer` | Per-longhand winner compares the existing key and conditionally stores key plus declaration payload. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at set keys^[longhand] = key;` | Still denied: old-key observation and nonconstant key/payload stores; no helper narrowing applies. |
| `style/incremental.wf:77` | `style/incremental.wf:77` — `map_pseudos` | Pseudo flags use `ior`, but first-pseudo selection reads the existing cell before overwriting it. | Denied C1 | Denied C1 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set first^.inner[element] = cvt.wrap::<u64, u32>(p);` | Still denied: first-pseudo selection reads the old cell before nonconstant replacement; no helper narrowing applies. |
| `style/incremental.wf:996` | `style/incremental.wf:996` — `root_font_readers` | Root-font declaration scan uses direct-map `reading` writes and constant indexed `columns=True()` stores. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/incremental.wf:1162` | `style/incremental.wf:1162` — `restyle_level` | Owner flags are constant marks; `structural` is a constant scalar mark; `place_style` and an error exit add obligations. | Denied C1 | Denied C1 | Denied C1 | Denied C1 | Denied C1 | `condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set structural = True();` | Still denied: structural=True is a scalar mark; failure return and place_style add obligations. Narrowing does not admit the complete body. |
| `style/incremental.wf:1387` | `style/incremental.wf:1387` — `restyle` | Touched-first cleanup stores constant zero through the state marks root. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/incremental.wf:1418` | `style/incremental.wf:1418` — `restyle` | Touched cleanup stores constant zero through the state marks root. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/incremental.wf:1424` | `style/incremental.wf:1424` — `restyle` | Wanted-element cleanup stores constant zero through the state marks root. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed constant marks` | Same permission; admitted as written, with no narrowing. |
| `style/levels.wf:30` | `style/levels.wf:30` — `level_index` | Depth histogram reads its partial count to guard an exact `+`, with parent validation and error returns. | Denied C1 | Denied C1 | Denied C1 | Denied C1 | Denied C1 | `condition 1: PAR-2 indexed accumulator: the indexed operation must belong to the scalar accumulator's admitted set, at set sizes.inner[depth] = seen + 1_u64;` | Still denied: exact + is outside the operation set, with a partial-count guard and failure returns; no helper narrowing applies. |
| `style/restyle.wf:97` | `style/restyle.wf:97` — `order_reaches` | Reach-bucket histogram already spells indexed `+wrap` directly. | Denied C1 | Permitted | Permitted | Permitted | Permitted | `eligible; indexed reductions under +wrap` | Same permission; admitted as written, with no narrowing. |
| `style/structure.wf:369` | `style/structure.wf:369` — `structure_restyle` | Pseudo holes are struct `NodeId` overwrites, outside integer/Bool indexed cells. | Denied C2 | Denied C2 | Denied C2 | Denied C2 | Denied C2 | `condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at set state^.cascade.nodes.inner[pseudo] = hole;` | Still denied: NodeId record overwrite, outside integer/Bool cells; no helper narrowing applies. |
| `text/normalization/decompose.wf:101` | `text/normalization/decompose.wf:100` — `sort_run` | Canonical-class histogram uses `current`/`next` temporaries before its indexed `+wrap` store. | Denied C1 | Denied C1 | Permitted | Permitted | Permitted | `eligible; indexed reductions under +wrap` | Same permission: fresh single-use current/next +wrap chain; no narrowing. |

## LLVM emission

**All six required rows emit parallel lane code:** both permitted call-form
rows and all four copied-cell rows. Their source-to-splitter traces in the
layout and targeted normalization LLVM are below.
The `wf__par_split_` prefix is omitted only in the splitter column.
Counts are call instructions inside that exact definition, in the order
`@wf__par_acquire_lane` / `@wf__par_publish` / `@wf__par_join`.

| Counted row | Form | Splitter | Acquire / publish / join | Source-to-splitter trace |
|---|---|---|---|---|
| `set_coverage_bits`, `lookup_filters.wf:95` | Copied cell, `ior` | `font.set_coverage_bits.2` | 1 / 1 / 1 | The original function calls `.2`; its outer chunk `.3` contains the nested glyph split. |
| `set_coverage_bits`, `lookup_filters.wf:103` | Copied cell, `ior` | `font.set_coverage_bits.0` | 1 / 1 / 1 | Outer chunk `.3` calls `.0` for `first..bounded`. |
| `build_filters`, `lookup_filters.wf:139` | Call-form `ior` | `font.build_filters.0` | 1 / 1 / 1 | The original function calls `.0`; outer chunk `.1` calls inner-step splitter `.2`, whose chunk `.3` calls `set_coverage_bits`. |
| `mark_lookups`, `shape_plan.wf:211` | Copied cell, `ior` | `font.mark_lookups.0` | 1 / 1 / 1 | The original function calls `.0` for its lookup-step loop. |
| `collect_stage`, `shape_plan.wf:267` | Call-form `ior` | `font.collect_stage.0` | 1 / 1 / 1 | The original function's `.body` calls `.0`; chunk `.1` calls `mark_lookups`. |
| `sort_run`, `decompose.wf:100` (classified line 101) | Copied cell, `+wrap` | `text.normalization.sort_run.0` | 1 / 1 / 1 | The targeted original function calls `.0` for `run_start..run_stop`; its chunk `.1` performs the histogram update. |

| Function, including its generated helper definitions | Acquire | Publish | Join | Attribution |
|---|---|---|---|---|
| `set_coverage_bits` | 2 | 2 | 2 | Two counted loops, one call of each runtime operation per splitter. |
| `build_filters` | 2 | 2 | 2 | Counted outer row loop plus the additional inner-step splitter; the counted row itself has 1 / 1 / 1. |
| `mark_lookups` | 1 | 1 | 1 | One counted copied-cell loop. |
| `collect_stage` | 1 | 1 | 1 | One counted call-form loop. |
| `sort_run` | 1 | 1 | 1 | One counted copied-cell loop in the targeted module. |

`build_filters` and `collect_stage` prepare per-leaf root-shaped private
blocks and combine them after the split; their chunks pass the private
root to the update helper. The direct copied-cell loops prepare private
slabs and combine their cells. The corresponding actualization ledgers report
splits, rather than a decline or retention of the sequential-only body.
The targeted normalization ledger reports
`text.normalization.sort_run`, `loop at 16.0.9.0`,
`split independent map over 9 captured bindings`; the source-level ledger
still identifies the counted loop at `decompose.wf:100`.
The emitted sequential clones and the runtime's no-lane branch are ordinary
fallbacks for scheduling with no allowance; their presence does not erase
the acquire/publish/join paths. Counts are per definition and per function
family, not executed lane counts or simultaneous-worker observations.

The earlier [capture run 38002012357](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38002012357),
on `c816f3c3dbb0f39d6ec8c191ac96e3122008846d`, successfully built the ledger
and emitted layout LLVM (both compiler exits 0), then failed the extraction
with **`missing emitted function: sort_run`**. This is an observed
missing-input control: the collection does not silently accept an omitted
target. The targeted normalization invocation repairs the coverage while
preserving the same counting logic. It changes no measured source body.

At exp68 the [call-form lowering boundary](https://github.com/Ming-Research/Whitefoot/blob/68fe93be539c844f31d68ee98c2455c960a3379b/compiler/src/lowering/builder/split.rs#L283)
returned before building any split when an indexed family contained calls.
That refusal is absent from [the release's lowering](https://github.com/Ming-Research/Whitefoot/blob/6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58/compiler/src/lowering/builder/split.rs#L289).
The new font call-form splitters above directly observe the resulting
emission change on the counted bodies, without claiming runtime overlap or
speed. The copied-cell font rows retain permission and emit their parallel
lane paths; `sort_run`'s targeted module verifies the remaining copied-cell
row outside the layout entry closure.

## Narrowing boundary and observations for Whitefoot

No qualifying helper narrowing was found. The two font helpers already
receive their mutable primitive-array roots separately from the read-only
layout. For the remaining bodies, narrowing an effect or signature does
not remove the complete-loop blockers: sequence-selected item get/put in
the grid; shared `TableTrack` get/put after narrowing per-cell output
helpers; whole-`Col` get/put, floating maximum or old-field-dependent
contributions in columns; hidden-dominates-maximum in borders; and
key-dependent winner payloads in cascade. The direct first-pseudo,
scalar-mark, guarded exact-add and `NodeId` replacement forms have no
helper narrowing that removes their blockers. Replacing whole-record
get/put with field stores would be a direct-store rewrite, outside the
criterion. **Applied narrowing diffs: none.** The after-narrowing column
therefore uses the same measured bodies, not a hypothetical rewrite.

The copied-cell positive form in `sort_run` is this source fragment,
inside the counted loop with a bounded `class64` and independent contribution:

```whitefoot
let current = counts[class64];
let next = current +wrap 1_u64;
set counts[class64] = next;
```

A useful remaining rule boundary is `merge_edge`'s actual statement shape,
inside its bounds guard:

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

This observes `current` in a branch as well as in `imax`, permits an
intervening write to the root, and mixes a constant mark with an operation
update. PAR-2 requires a single-use copied operand, disjoint intervening
footprints and one fixed family kind. Supporting hidden-dominates-maximum
requires a broader operator/selection rule, not helper narrowing. These
are illustrative source fragments, not separately compiled fixtures.
No renderer workaround or Whitefoot source change is made here.

## Disposition and limits

The source-permission criterion and the requested emission audit both pass.
After the correct cancellation compatibility adaptations there is no further
hard source refusal. The remaining fifteen complete-loop denials and the
minimal border-selection boundary above are the observations to send to
Whitefoot; no new compiler issue or separate gap is filed. No algorithm,
pass, storage or counted update spelling changes, and no qualifying helper
narrowing is applied.

This is source permission and static emitted-code evidence. Runtime values,
output correctness, actual overlapping execution, invocation hotness and
performance remain unverified and outside this measurement. The temporary
workflow stays on this work branch for reproduction until the indexed-loop
investigation closes. The final research-record-only commit leaves the
measured renderer, pin, submodules and workflow identical to the paired
successful CI runs. No pull request or status-board update is part of this
task.

## Completion review

A separate read-only reviewer inspected
`4a9258bd7dac3d557318bc8872fd05d88ff240fd..5c140fa63a346bdc0245fb402cac76ca163418f6`
plus the completed research record. Scope included the complete diff, all
32 counted bodies and relevant helpers, PAR-2 and the specification log,
prior recounts, relevant design nodes, workflows, raw artifacts and hosted
logs. The reviewer independently compared every table entry and diagnostic,
recomputed emission counts from both raw LLVM modules, and inspected each
audited row's splitter, private storage and combine path. No local build,
compiler invocation, test, check, lint or CI polling was run by the reviewer.

Against [the project checklist](../../../../docs/review-checklist.md),
A1–A4, D1–D4, C1–C5, T1–T4, R1–R2/R4, M1 and V1–V2 pass;
R3 and V3–V4 are not applicable. The applicable design checks G2/G3 and
DC1/DC2/DC4 pass; G1 and DC3 are not applicable because no tree edit or
retired implementation is part of this task. Runtime correctness, actual
overlap, invocation hotness and performance remain outside scope and
unverified. **Findings: none within scope; no review fixes were required.**
The final commit adds only this completed research record to the measured
revision.
