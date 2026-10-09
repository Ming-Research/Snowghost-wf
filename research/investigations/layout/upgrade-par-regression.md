# Parallelism after the Whitefoot v0.108 upgrade

## Finding

**No loss of loop permission or outlined splitting was found on the requested
text-preparation and layout paths. The cause of the supplied runtime speedup
regression is not established by these ledgers.** All 109 previously permitted
source loops remain permitted; 21 more layout loops become permitted. The
paragraph and child-context preparation loops, child-layout loop and
paragraph line-breaking loop still have task publications in emitted LLVM,
with unchanged or nearly unchanged work budgets and the same runtime span
expressions.

The call-grain change does remove two call offers in the full driver:
CSS track-piece lookup and style value application. Neither is an offer on
text preparation's shaping, font matching or line-break path. Calls inside
one table-border loop move into its newly outlined chunk; their offers remain.
No old split in the requested modules becomes sequential in the lowering
ledger. This rejects attributing the text regression to a new PAR-2 refusal,
a lost outlined loop, or the new recursion-grain exemption alone. Permission
and emitted publication are not evidence that four workers executed the
measured workload.

A concrete additional-work candidate is the upgrade's displaced-struct
cleanup fix, Whitefoot #294: paragraph preparation gains five required
releases at shaped-text replacement. This change is visible in emitted code
and reproduced independently below; its contribution to the runtime
regression remains a hypothesis.

## Comparison and prior evidence

| Side | Snowghost revision | Compiler release | Whitefoot revision / specification |
|---|---|---|---|
| Old | `9d720c49daf4de746d507f5b1400ea407e3dfc09` | `wf-0b7f5c5b9854` | `0b7f5c5b98547dd27deb9691aed36281e350576b`, v0.94 |
| New | `c3ea1c84ca3a2eca1e4048555d8a7298bd620d00` | `wf-f887e82c4611` | `f887e82c46119dedf20e364c73461cb14fb2dfb3`, v0.108 |

The task supplies [14900K run 37894690211](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37894690211),
`research/investigations/layout/run.sh time`, one round:

| Measurement | Old compiler | New compiler |
|---|---:|---:|
| ecma262 text minus boxes, four workers | 0.167 s | 0.353 s |
| ecma262 text minus boxes, sequential | 0.380 s | 0.353 s |
| ecma262 whole layout, four workers | 0.24 s | 0.53 s |
| html5 whole layout, four workers | 0.26 s | 0.44 s |

The task also reports that later layout passes lost speedup, style retained
it, and the base's noise twin agreed within about 3%. These are supplied
measurements, not measurements of this diagnosis. The renderer source diff
removes unreachable tails after break-free loops (FN-1); it changes no layout
source and no loop body. Some font/text source lines consequently move.

Every compilation below ran on GitHub-hosted `ubuntu-24.04`, using each
revision's `make toolchain` release download. Both release manifests name
Linux LLVM major 22. No program was executed, no timing was taken, and no
build, test or check was run on the local machine. Local work consisted of
reading sources and captured artifacts and comparing their text.

The full driver command was:

```sh
cd renderer
"$wfc" --cache ../build/par-diag-cache --fragments function \
  --par --par-ledger --graph modules.wfg --entry layout_oracle \
  -o ../build/layout_oracle_par > compiler.stdout 2> compiler.stderr
```

A separate `--par --par-ledger --emit-llvm` compilation retained the full
module for static inspection. This second build omits `--fragments`: the
CLI disallows that combination. It therefore checks lowering and emission,
not the final fragment link. The PAR loop/split/actualization rows are
identical between driver and LLVM emission within each side (2448 old,
2472 new). Linked-code inspection is recorded separately
below. Compiler exit status was read directly from the command in each job,
and full stdout and stderr were uploaded even on failure.

Before the minimal examples were compiled, the investigation recorded the
criterion: a claimed reproduction must show old offered/permitted versus
new unoffered/denied, and an unchanged verdict rejects it. The recursion
example meets that criterion for call grain; the split-loop control shows
that ordinary splitting remains available. Neither is a reproduction of
the observed runtime speedup loss.

## Complete ledger comparison

Sites were matched by source path, function and counted-loop ordinal in that
function, rather than by line number or the compiler's AST path. There are
586 rows and 586 distinct sites on each side, with no unmatched or duplicate
sites in these modules. The complete ledgers are retained in the CI
artifacts; the tables list every changed semantic verdict or first refusal,
and the critical unchanged sites. The blanket wording change for condition
2, from “storage ... neither introduced by the iteration nor the accumulator”
to “shared storage without an admitted element or range family, or reads ...
outside ... permitted accesses”, is normalized when comparing refusals.

| Module group | Old permitted / denied | New permitted / denied | Old permission lost |
|---|---:|---:|---:|
| `pkg::font` | 2 / 97 | 2 / 97 | 0 |
| `pkg::layout::text` | 5 / 26 | 5 / 26 | 0 |
| `pkg::text::line_break` | 1 / 3 | 1 / 3 | 0 |
| `pkg::text::normalization` | 0 / 8 | 0 / 8 | 0 |
| Other `pkg::layout` functions | 101 / 343 | 122 / 322 | 0 |
| Total | 109 / 477 | 130 / 456 | 0 |

### Text preparation and later layout passes

The outer loops provide the coarse independent work; most font/shaping
inner loops were already denied by their carried state or early exits.

| Function | Loop or call | Old verdict | New verdict | First condition |
|---|---|---|---|---|
| `layout.prepare_context` | `prep.wf:719`, paragraphs | Permitted; split under `band`, 9 captures | Same | None; eligible |
| `layout.prepare_context` | `prep.wf:726`, child contexts | Permitted; split under `band`, 10 captures | Same | None; eligible |
| `layout.prepare_paragraph` | `prep.wf:634`, pieces | Denied | Denied | Condition 2: shared write lacks an admitted family, at `&emit`; unchanged |
| `layout.text.itemize_faces` | Split loop at AST path `3701.0.13.0.4.0.4.0` | Split independent map, 3 captures | Same | None |
| `layout.text.rescale_segment` | Split loop at `3709.0.13.0` | Split independent map, 9 captures | Same | None |
| `layout.text.apply_spacing` | Split loop at `3712.0.12.0` | Split independent map, 4 captures | Same | None |
| `layout.text.find_breaks` | Split loop at `3719.0.13.0` | Split independent map, 7 captures | Same | None |
| `layout.text.shape_with` | Split loop at `3722.0.17.0.19.0` | Split independent map, 2 captures | Same | None |
| `layout.text.shape_with` | Call offer of `itemize_faces` beside `itemize_scripts` | Published in LLVM | Published in LLVM | None |
| `text.line_break.write_run_span` | Split loop at `571.0.5.0` | Split independent map, 4 captures | Same | None |
| `font.class_array` | Split loop at `842.0.10.0.8.0` | Split independent map, 2 captures | Same | None |
| `font.compile_advances` | Split loop at `882.0.18.0` | Split independent map, 13 captures | Same | None |
| `layout.lay_out_children` | `flow.wf:405`, child contexts | Split independent map, 7 captures | Same | None |
| `layout.break_all` | `flow.wf:428`, paragraphs | Split independent map, 7 captures | Split independent map, 6 captures | None; capture pruning, not a lost split |
| `layout.measure` | Nested independent map at `4376.0.15.0.2.0.3.0.3.0` | Split, 3 captures | Split, 4 captures; its outer loop also splits | None; added outer indexed family |

There is no split-to-decline transition among the requested modules.
`PAR actualization` chiefly prints negative decisions, so absence of an
omission line is not sufficient proof of an offer: the LLVM publication
sites were also inspected.

### Call offers whose ledger or emitted location changes

| Function | Loop or call | Old verdict | New verdict | First condition |
|---|---|---|---|---|
| `css.values.track_at` | `piece_breadth` call | Offered; LLVM publication present | Offer omitted; publication absent | Call grain: static work 3138 below 150000; reaches only recursion that offers none of its own calls |
| `style.reset_element` | `applied_value` call | Offered; LLVM publication present | Offer omitted; publication absent | Same call-grain condition, static work 60901 |
| `layout.grid_place` | Two `grid_mark` offers | Omitted | Publications present | Old grain: static work 3396 below 150000, no recursion; new splitters make recursion that offers calls reachable |
| `layout.intrinsic_table` | `grid_spacing` offer | Omitted | Publication present in `.body` | Old grain: static work 387 below 150000, no recursion; now reaches offered splitters |
| `layout.lay_out_grid` | `grid_build_tracks` offer | Omitted | Publication present | Old grain: static work 11967 below 150000, no recursion; now reaches offered splitters |
| `_par_chunk_layout.grid_build_tracks.3` | `grid_index` call in a new chunk | No such chunk | Offer omitted | Static work 3 below 150000, no recursion; newly introduced site, not a loss |
| `layout.collapse_borders` | Per-cell `widest_vertical` / `widest_horizontal` offers | In original function | In new `_par_chunk_layout.collapse_borders.1` | None; moved with the newly split loop |
| `layout.place_element` | `close_splits` offer | Omitted by grain (212) | Publication present in `wf__par_budget_layout.place_element.body` | Old grain: static work 212 below 150000, no recursion; now reaches offered splitters |
| `layout.take_prepared` | Four `swap` omission rows | Omitted by grain (5 each) | No grain rows; no publications in either module | No new condition reported; storage-lifetime actualization can cut groups before grain examines them |

The inventory includes generated budget bodies as well as ordinary functions
and outlined chunks. The `take_prepared` row concerns four generic `swap` instances, not four
lost tasks. Source inspection makes the new storage-lifetime cut a candidate
explanation for these missing negative rows; no ledger line identifies that
cut, so attributing these rows to it is an inference rather than a reported
condition. The two actual offer losses above are the only new
“reaches only recursion ...” rows in the full driver.

### All loop verdict gains

A loop ordinal includes counted loops nested in that function. Locations
refer to the new Snowghost revision; old/new locations are the same for these
layout sources. “C1” and “C2” name the ledger's numbered conditions, not new
rules: C1 is inadmissible carried state, C2 is shared storage lacking an
admitted family. The new first condition is none for every gain.

| Function | Loop / source location | Old verdict | New verdict | First condition |
|---|---|---|---|---|
| `close_splits` | Loop 1, `layout/build.wf:426` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `sort_keys` | Loop 2, `layout/flow.wf:1085` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `split_closings` | Loop 1, `layout/flow.wf:1170` | Denied: C2: shared write lacks an admitted family | Permitted: indexed constant marks | None |
| `grid_build_tracks` | Loop 2, `layout/grid.wf:1238` | Denied: C2: shared write lacks an admitted family | Permitted: indexed constant marks | None |
| `grid_build_tracks` | Loop 3, `layout/grid.wf:1245` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `grid_build_tracks` | Loop 4, `layout/grid.wf:1260` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `grid_mark` | Loop 1, `layout/grid.wf:981` | Denied: C2: shared write lacks an admitted family | Permitted: indexed constant marks | None |
| `grid_mark` | Loop 2, `layout/grid.wf:982` | Denied: C2: shared write lacks an admitted family | Permitted: indexed constant marks | None |
| `grid_shim_baselines` | Loop 1, `layout/grid.wf:2272` | Denied: C2: shared write lacks an admitted family | Permitted: indexed reductions under imax | None |
| `finish_lines` | Loop 3, `layout/inline.wf:1087` | Denied: C2: shared write lacks an admitted family | Permitted: indexed constant marks | None |
| `measure` | Loop 2, `layout/inline.wf:189` | Denied: C2: shared write lacks an admitted family | Permitted: indexed constant marks | None |
| `structure_changed` | Loop 3, `layout/structure.wf:801` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `grow_tracks` | Loop 1, `layout/table.wf:500` | Denied: C1: inadmissible carried state | Permitted: one accumulator under +sat | None |
| `shift_cell` | Loop 1, `layout/table.wf:387` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `shift_cell` | Loop 2, `layout/table.wf:396` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `shift_cell` | Loop 3, `layout/table.wf:405` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `shift_cell` | Loop 4, `layout/table.wf:417` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `collapse_borders` | Loop 4, `layout/tableborders.wf:206` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `separate_borders` | Loop 1, `layout/tableborders.wf:97` | Denied: C2: shared write lacks an admitted family | Permitted: no accumulator | None |
| `visible_columns` | Loop 1, `layout/tablegrid.wf:158` | Denied: C1: inadmissible carried state | Permitted: one accumulator under +sat | None |
| `prepare_local_widths` | Loop 3, `layout/update.wf:2079` | Denied: C2: shared write lacks an admitted family | Permitted: one accumulator under band | None |

### All changed first refusals without a verdict change

These 60 sites are denied on both sides. A different first condition means
that an earlier obstacle was removed or a newly considered indexed shape
was rejected; it does not mean that a formerly parallel loop was made
sequential. Source spellings after “at” are quoted from the new ledger.

| Function | Loop / source location (old → new) | Old verdict | New verdict | First condition in new compiler |
|---|---|---|---|---|
| `class_array` | Loop 1, `font/gdef.wf:75 → 75` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set classes.inner[glyph] = value; |
| `compile_mark_glyph_sets` | Loop 1, `font/gdef.wf:124 → 124` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set memo.inner[coverage_at] = marker; |
| `set_coverage_bits` | Loop 1, `font/lookup_filters.wf:95 → 95` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set filters^.inner[slot] = marked; |
| `set_coverage_bits` | Loop 2, `font/lookup_filters.wf:103 → 103` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set filters^.inner[slot] = marked; |
| `mark_lookups` | Loop 1, `font/shape_plan.wf:211 → 211` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set flags^.inner[index] = combined; |
| `add_content` | Loop 2, `layout/build.wf:1024 → 1024` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 2 times in the body and a reduction reads it once, at set shown = shown +sat 1_u64; |
| `apply_counters` | Loop 2, `layout/build.wf:578 → 578` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set walk^.counters.inner[at].value = change.value; |
| `build_boxes` | Loop 1, `layout/build.wf:2898 → 2898` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set order.inner[at] = cvt::<u64, u32>(position); |
| `count_tree` | Loop 1, `layout/build.wf:2650 → 2650` | Denied: C1: inadmissible carried state | Denied | condition 1: the body carries 2 accumulators, and this rule recombines one |
| `place_cell` | Loop 1, `layout/build.wf:2097 → 2097` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 3 times in the body and a reduction reads it once, at set column_here = column_here +sat 1_u64; |
| `place_cell` | Loop 2, `layout/build.wf:2126 → 2126` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set busy^.inner[target] = free_from; |
| `record_skipped` | Loop 1, `layout/build.wf:2874 → 2874` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: every occurrence of the indexed root must be a root measure or belong to its cell update; prefix reads, checks of cells and root-dependent subscripts or contributions are not permitted, at set listing^.inner[at].serial = skipped_text; |
| `record_units` | Loop 1, `layout/build.wf:2663 → 2663` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: one operand must name exactly the target's subscripted place, at set listing^.inner[at].count = held.count +sat 1_u32; |
| `record_units` | Loop 2, `layout/build.wf:2671 → 2671` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: one operand must name exactly the target's subscripted place, at set listing^.inner[at].count = held.count +sat 1_u32; |
| `collect_units` | Loop 1, `layout/columns.wf:99 → 99` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set skip_depth = depth; |
| `flex_align_cross` | Loop 1, `layout/flex.wf:1114 → 1114` | Denied: C2: shared write lacks an admitted family | Denied | condition 4: a break leaves the loop |
| `flex_collect` | Loop 1, `layout/flex.wf:695 → 695` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set items^.inner[at].order = group.order; |
| `flex_load` | Loop 1, `layout/flex.wf:760 → 760` | Denied: C2: shared write lacks an admitted family | Denied | condition 4: a break leaves the loop |
| `flex_resolve` | Loop 4, `layout/flex.wf:861 → 861` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set lanes^.inner[k].target = wanted; |
| `flex_resolve` | Loop 7, `layout/flex.wf:956 → 956` | Denied: C2: shared write lacks an admitted family | Denied | condition 4: a break leaves the loop |
| `flex_sort` | Loop 1, `layout/flex.wf:656 → 656` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set sequence^.inner[hole] = previous; |
| `line_splits` | Loop 1, `layout/flow.wf:616 → 616` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 4 times in the body and a reduction reads it once, at set at = at +sat 1_u64; |
| `merge_pass` | Loop 2, `layout/flow.wf:1110 → 1110` | Denied: C1: inadmissible carried state | Denied | condition 1: the body carries 3 accumulators, and this rule recombines one |
| `place_atomics` | Loop 1, `layout/flow.wf:1326 → 1326` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: the indexed operation must belong to the scalar accumulator's admitted set, at set context^.children.inner[child].x = left +sat placed.x; |
| `place_splits` | Loop 1, `layout/flow.wf:634 → 634` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 5 times in the body and a reduction reads it once, at set at = at +sat 1_u64; |
| `prepare_spaces` | Loop 2, `layout/flow.wf:289 → 289` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: the target must be an integer or Bool cell of one outside Array or Slots root, at set context^.children.inner[child_at].space = child_space(available: width, basis_width: width, basis_height: unknown, shrink: yes); |
| `resolve_open` | Loop 1, `layout/flow.wf:541 → 541` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set context^.blocks.inner[block].y = y; |
| `resume_open_frames` | Loop 3, `layout/flow.wf:1680 → 1680` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set context^.blocks.inner[at].held_y = context^.blocks.inner[at].y; |
| `settle_open` | Loop 1, `layout/flow.wf:1466 → 1466` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: the indexed operation must belong to the scalar accumulator's admitted set, at set context^.blocks.inner[at].x = content_left +sat x_shifted; |
| `split_fragments_with_empty` | Loop 1, `layout/flow.wf:926 → 926` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set next_same.inner[from] = to; |
| `split_fragments_with_empty` | Loop 2, `layout/flow.wf:941 → 941` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: every occurrence of the indexed root must be a root measure or belong to its cell update; prefix reads, checks of cells and root-dependent subscripts or contributions are not permitted, at set used.inner[j] = 1_u8; |
| `stack_flow` | Loop 2, `layout/flow.wf:1764 → 1764` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set old_reach = stack.reach; |
| `grid_place` | Loop 4, `layout/grid.wf:1086 → 1086` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set cursors.inner[row] = past; |
| `grid_place` | Loop 8, `layout/grid.wf:1164 → 1164` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 2 times in the body and a reduction reads it once, at set cursor_row = cursor_row +sat 1_u64; |
| `grid_place` | Loop 9, `layout/grid.wf:1179 → 1179` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set cursor_column = 0_u64; |
| `grid_sort_sequence` | Loop 1, `layout/grid.wf:911 → 911` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set model^.sequence.inner[at] = previous; |
| `finish_lines` | Loop 1, `layout/inline.wf:1070 → 1070` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set segment_at.inner[k] = named; |
| `finish_lines` | Loop 6, `layout/inline.wf:1132 → 1132` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set top = top +sat height; |
| `finish_lines` | Loop 9, `layout/inline.wf:1201 → 1201` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set low = low_next; |
| `finish_lines` | Loop 10, `layout/inline.wf:1205 → 1205` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set low = low_next; |
| `framed_inside` | Loop 1, `layout/inline.wf:688 → 688` | Denied: C2: shared write lacks an admitted family | Denied | condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at &open_marks |
| `leading_cut` | Loop 2, `layout/inline.wf:966 → 966` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 3 times in the body and a reduction reads it once, at set cut = cut +sat 1_u64; |
| `next_line` | Loop 1, `layout/inline.wf:318 → 318` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 3 times in the body and a reduction reads it once, at set begin = begin +sat 1_u64; |
| `merge_runs` | Loop 1, `layout/prep.wf:560 → 560` | Denied: C1: inadmissible carried state | Denied | condition 1: the accumulator is read 5 times in the body and a reduction reads it once, at set pointer = pointer +sat 1_u64; |
| `merge_runs` | Loop 2, `layout/prep.wf:577 → 577` | Denied: C1: inadmissible carried state | Denied | condition 1: the body carries 2 accumulators, and this rule recombines one |
| `mark_fresh` | Loop 1, `layout/structure.wf:614 → 614` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set marked_paragraph = cvt.wrap::<u64, u32>(i); |
| `reuse_prepared` | Loop 1, `layout/structure.wf:551 → 551` | Denied: C1: inadmissible carried state | Denied | condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at old_root |
| `reuse_prepared` | Loop 4, `layout/structure.wf:602 → 602` | Denied: C1: inadmissible carried state | Denied | condition 2: the body writes shared storage without an admitted element or range family, or reads that storage outside the family's permitted accesses, at old_root |
| `styles_restyled` | Loop 2, `layout/style_update.wf:714 → 714` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set runs.inner[index] = reads_runs; |
| `lay_out_table` | Loop 7, `layout/table.wf:888 → 888` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set context^.children.inner[item.child].x = left; |
| `pick_fonts` | Loop 2, `layout/text/picks.wf:277 → 277` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set chain.inner[at] = face; |
| `pick_fonts` | Loop 3, `layout/text/picks.wf:288 → 288` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set chain.inner[at] = face; |
| `shape_segment` | Loop 1, `layout/text/shape.wf:340 → 340` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set glyphs^.inner[at] = pack_glyph(nominal: nominal, shaped: glyph.x_advance); |
| `first_float_paragraph` | Loop 1, `layout/update.wf:433 → 433` | Denied: C1: inadmissible carried state | Denied | condition 4: a return leaves the loop |
| `restack_block` | Loop 1, `layout/update.wf:2147 → 2147` | Denied: C1: inadmissible carried state | Denied | condition 1: the loop writes storage outliving the iteration that no exactly associative operation reduces, at set depth = depth -sat 1_u64; |
| `restack_block` | Loop 2, `layout/update.wf:2171 → 2171` | Denied: C1: inadmissible carried state | Denied | condition 1: the body carries 2 accumulators, and this rule recombines one |
| `sum_counts` | Loop 1, `layout/update.wf:723 → 723` | Denied: C1: inadmissible carried state | Denied | condition 1: the body carries 4 accumulators, and this rule recombines one |
| `sort_run` | Loop 1, `text/normalization/decompose.wf:101 → 100` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set counts[class64] = next; |
| `sort_run` | Loop 4, `text/normalization/decompose.wf:127 → 126` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set scratch.inner[slot] = value; |
| `sort_run` | Loop 5, `text/normalization/decompose.wf:142 → 141` | Denied: C2: shared write lacks an admitted family | Denied | condition 1: PAR-2 indexed accumulator: each indexed write requires an admitted operation directly or through one fresh, unchanged, single-use temporary, at set output^.inner[dest] = value; |

## Whitefoot changes and attribution

### Call grain: an actual change, outside the text path

[Whitefoot #278, call grain: exempt only recursion that offers its own calls](https://github.com/Ming-Research/Whitefoot/pull/278),
merged as `db72af4347a44de7d389d97ca28efd661a7c59b3`, changes an implementation
policy, not PAR-1 permission. Previously, reaching any cyclic call-graph
component exempted an offered call from the 150000 static-work floor.
Now a cycle exempts calls only when one of its surviving overlap groups
calls into that cycle. Pruning repeats to a fixed point because removing a
small call can dissolve the group that supplied the exemption.

The rule is implemented by [call_grain.rs:80–112 and 123–172](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/lowering/builder/call_grain.rs#L80).
PAR-1/PAR-2 permit overlap but do not require it; [PAR-2's optionality](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/spec/kernel-spec.md#L2215)
therefore does not promise that every permitted call is published. The new
miniature below has linear recursion with no overlap group inside it and
reproduces this exact omission. The layout splitters recurse with their own
two-member overlap group, so this exemption remains available to them;
[source splitter construction](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/lowering/builder/split.rs#L1250) and their LLVM publications agree.
The two driver losses in CSS/style follow #278's new reported condition.
Neither supplies text preparation's coarse parallelism.

### Loop-permission expansions: gains and changed first refusals

[Whitefoot #268, permit measure reads of mapped roots](https://github.com/Ming-Research/Whitefoot/pull/268),
merged as `f7aca0277487596f16a7da20d54bad049d865ee8`, changes PAR-2 in v0.97:
reading a mapped root's unchanged length no longer defeats its element
family. The current [element-map coverage check](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/semantic/loop_permission.rs#L2255) admits those
measure reads while retaining the same affine map requirement for other
reads. This accounts for the newly admitted independent-map spellings that
read their written collection's length, including `close_splits`,
`sort_keys`, `shift_cell`, table-border edge filling and paragraph-width
preparation. Attribution to this rule is by source inspection; intermediate
releases were not compiled.

[Whitefoot #274, indexed reductions](https://github.com/Ming-Research/Whitefoot/pull/274)
(v0.102), followed by [#290, more indexed reduction forms](https://github.com/Ming-Research/Whitefoot/pull/290)
(v0.107, merge `64c0f956d`), admits indexed constant marks, the one fresh
single-use temporary, record-field families and unsigned `+sat`.
The [current PAR-2 forms](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/spec/kernel-spec.md#L2173) explain the new constant-mark loops,
`grid_shim_baselines`'s indexed `imax`, and the unsigned `+sat` gains in
`grow_tracks` and `visible_columns`. The [denial order](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/semantic/loop_permission.rs#L2174) checks
carried and indexed state before shared writes, so unsupported indexed
writes now report C1 instead of the old C2. A new C1 row at an already denied
site is not a permission regression. The additional Paged rule in v0.108
does not affect these sources, which contain no Paged storage.

### Checker soundness fixes: no observed permission loss here

[Whitefoot #281, range soundness](https://github.com/Ming-Research/Whitefoot/pull/281),
merge `4992bed27374773c483ae10d4c72030c7216ec40`, prevents entry-state range
facts from proving current-state contradictions and forgets exposed scalar
facts on unplaced writes. See [range-world havoc/exposure](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/semantic/range_judgment/world.rs#L566),
and RANGE-1's separation of entry and current images. This repairs the
checker without changing PAR-2's admitted loop form. No previously
permitted site in the compared modules loses permission.

[Whitefoot #282, end Bool origins at reaching writes](https://github.com/Ming-Research/Whitefoot/pull/282),
merge `0e953e67d3e93afa5a170388db3b17ad13ef2a7a`, changes ENT-3 in v0.104:
a binding no longer retains its initializer's comparison after a write
reaches it, including a write through a reference. [Flow kill handling](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/semantic/entailment/flow/events.rs#L845)
implements that lifetime. Again, this pair of driver ledgers shows no loop
permission loss attributable to it. The fix may affect proofs elsewhere;
this observation is limited to the compiled driver and requested modules.

### Storage lifetime and runtime changes

[Whitefoot #275, cut overlap at storage-release conflicts](https://github.com/Ming-Research/Whitefoot/pull/275),
merge `0bea2b796169deb0c192c3416c27f584282d418a`, adds a lowering boundary
between calls whose release and borrowed actual/argument-formation storage
may overlap. [CallStorageEffects::conflicts](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/semantic/permission.rs#L327) and
[group formation](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/lowering/builder.rs#L1047) implement it; PAR-1's data-footprint
permission itself is unchanged. These cuts have no dedicated ledger line.
LLVM shows no disappearing text/font publication, and the four old
`take_prepared` swaps were already grain-omitted, so they do not establish
a new text serialization mechanism.

[Whitefoot #277, memory statistics](https://github.com/Ming-Research/Whitefoot/pull/277),
merge `631d3ffbe9284ad032559b76343d8a5c5a0c56dc`, implements PRE-2's heap
meter. In the paragraph-preparation chunk, five former `free` calls now
load allocation extents and call `wf__heap_give`; `shape_with` similarly
gains counted release paths. [The wrappers](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/backend/heap.c#L7) and
[the per-thread counters](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/backend/completion/bridge.c#L1291) are visible source changes on the
hot path, but no cost was measured here. The counters have separate
64-byte-aligned slots and use one relaxed atomic store per change, with an
atomic fetch-add only on first registration. A hypothesis of a single
shared allocation-counter lock is contradicted by this implementation.
[#280, reallocating growth](https://github.com/Ming-Research/Whitefoot/pull/280)
also changes allocation paths. Whether those changes, native optimization,
or actual worker participation explain the runtime measurements remains
unverified; these are candidates, not established causes.

The scheduler's `core.c` and `entry.c`, including split-budget computation
and WF_WORKERS handling, are unchanged between the pins. Its host thread
start adds stop-signal masking in #273; no scheduler policy change was found
in that diff. This does not rule out a linking or runtime interaction.

### Required releases added on the text path: a concrete cost candidate

[Whitefoot #294, release displaced struct components](https://github.com/Ming-Research/Whitefoot/pull/294),
merged at the new pin `f887e82c46119dedf20e364c73461cb14fb2dfb3`, fixes a
pre-existing violation of SET-1/WIN-3/STOR-3. Assigning over a live struct
previously recorded one whole-struct drop, which the backend skipped instead
of releasing its owned fields. [The new displaced-release expansion](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/compiler/src/lowering/builder/targets.rs#L156)
records those components individually after the write, as
[the owned-place assignment rule requires](https://github.com/Ming-Research/Whitefoot/blob/f887e82c46119dedf20e364c73461cb14fb2dfb3/spec/kernel-spec.md#L834).

This reaches the exact text-preparation path: `prep.wf:703` assigns
`set paragraph^.shaped = move shaped;`. In `wf_layout.prepare_paragraph`,
the old emitted function contains zero `free` calls; the new function
contains five `wf__heap_give` calls capturing the displaced `ShapedText`'s
five owning fields before the write and releasing them afterward.
`wf_layout.reset_paragraph` likewise changes from four release calls to
nine. These counts are static call sites, not dynamic counts or timings.
`shaped_empty` (`layout/text/fonts.wf:85–93`) allocates all five owning
fields even for empty text, so replacing a fresh paragraph's initial
shaped value exercises the same added releases. The release obligation
already exists in [v0.94 WIN-3](https://github.com/Ming-Research/Whitefoot/blob/0b7f5c5b98547dd27deb9691aed36281e350576b/spec/kernel-spec.md#L823)
and [PROV-6](https://github.com/Ming-Research/Whitefoot/blob/0b7f5c5b98547dd27deb9691aed36281e350576b/spec/kernel-spec.md#L774): #294 corrects implementation
of an existing requirement, rather than adding a new language requirement.
The five added releases in paragraph preparation are distinct from #277's
counting wrappers around releases that already existed.

Established: the new compiler does additional required cleanup on this hot
path while preserving its loop/task parallelism. Hypothesis: that cleanup,
its allocator behavior across workers and the counting wrappers contribute
to the runtime regression. Its cost and the apparent loss of worker speedup
are not established without execution evidence or an intermediate comparison.
The old leak is a correctness defect, not an optimization to recover.

A small independent witness, `displaced-struct.wf`, replaces a one-field
struct through a reference. The pre-compilation criterion is: old
`wf_replace` has no displaced release, new `wf_replace` has one after its
store; a release in both functions would reject this witness. Hosted outputs
are recorded below. This is a cleanup-change witness, not an offer-loss
witness.

## Static task budgets and linked code

In the emitted module, `prepare_context` differs only in its two numeric
weight operands; the loaded paragraph/child counts and calls to splitters
are unchanged. Each splitter retains the acquire/publish/join path. The
splitter for `lay_out_children` is byte-for-byte identical in emitted LLVM.
`break_all` drops one unused capture, with a smaller task frame.

| Loop | Old weight | New weight | Runtime span |
|---|---:|---:|---|
| Paragraph preparation | 2782120 | 2782125 | Context paragraph count, unchanged |
| Child-context preparation | 19052 | 19132 | Context child count, unchanged |
| Child layout | 12080 | 12080 | Context child count, unchanged |
| Paragraph line breaking | 20605079 | 20601299 | Paragraph count, unchanged |

The LLVM module contains weak no-op runtime fallbacks; seeing a weak
`wf__par_split_budget` returning zero in `--emit-llvm` output does not show
that the native driver uses it. The native build supplies the ordinary C
runtime with strong definitions. The hosted fragment-build capture retains
the linked executable, symbol listing and disassembly to inspect that
resolution without executing the program.

Both linked fragment drivers retain the strong scheduler implementations,
not the LLVM fallbacks: `wf__par_split_budget` reads scheduler lanes,
queued work, the span and weight; `wf__par_publish` updates the queue and
wakes workers. In `wf_layout.prepare_context`, ThinLTO inlines the budget
queries and still calls both splitters. The four critical splitters in the
table above retain the corresponding thunk-address stores, queue publication
and join paths. Publication is largely inlined, so searching only for calls
to `wf__par_publish` would miss it.

The linked-old capture has the same four thunk publications and queue paths.
This rules out a new replacement of these task paths by no-op runtime
fallbacks in the hosted fragment builds; it does not establish what happened
in the earlier 14900K executions.

## Stand-alone examples and both outputs

All files are complete entry programs in [upgrade-par-examples](upgrade-par-examples/).
They are compiled and emitted, never executed. Each CI artifact retains
the source, full ledger/stdout, stderr, exit status, LLVM and linked-code
text. The exact command is:

```sh
"$wfc" --par --par-ledger source.wf -o build/example
"$wfc" --par --par-ledger --emit-llvm source.wf -o program.ll
"$wfc" --cache build/example-cache --fragments function \
  --par --par-ledger source.wf -o build/example-fragments
```

### Linear recursion: an offer removed by #278

[linear-call-grain.wf](upgrade-par-examples/linear-call-grain.wf):

```whitefoot
fn descend(depth: u64) -> result: u64 pure {
  if depth == 0_u64 {
    return 1_u64;
  }
  let next = depth -wrap 1_u64;
  let child = descend(depth: next);
  return child +wrap 1_u64;
}

fn main() -> status: std::process::ExitStatus pure {
  let left = descend(depth: 2_u64);
  let right = descend(depth: 3_u64);
  let sum = left +wrap right;
  let code = cvt.wrap::<u64, u8>(sum);
  return std::process::exit_status(code: code);
}
```

Both compilers permit the two adjacent calls in `main`:

```text
PAR permitted   ...:11  pair(descend, descend)  eligible
PAR chain       ...:11  run(descend, descend)  2 members through line 12
```

The old compiler adds no grain omission and emits a publication of the
first `descend` call. The new compiler reports:

```text
PAR actualization  main  call grain: omitted offer of descend (static work 32 below 150000, reaches only recursion that offers none of its own calls)
```

The new `wf_main` has no publication. Both still exclude `descend` from
recursion-budget cloning because it has no sequential clone. Thus the
changed behavior is actualization, not a permission rejection. Both native
compilation and LLVM emission succeeded with empty stderr in run
37898522362. Both fragment builds also succeeded with empty stderr in run
37900241732.
Its old linked `wf_main` retains the thunk and inlined queue publication;
its new `wf_main` has neither. The ordinary links likewise have one old
`wf__par_publish` call and none in the new `wf_main`.

### Scalar reduction: a split that survives

[split-reduction.wf](upgrade-par-examples/split-reduction.wf):

```whitefoot
fn sum(count: u64) -> result: u64 pure {
  let total = 0_u64;
  for (i in 0_u64..count) {
    set total = total +wrap i;
  }
  return total;
}

fn main() -> status: std::process::ExitStatus pure {
  let total = sum(count: 1000000_u64);
  let code = cvt.wrap::<u64, u8>(total);
  return std::process::exit_status(code: code);
}
```

Both compiler ledgers report:

```text
PAR loop        ...:3  loop  permitted   eligible; one accumulator under +wrap
PAR split       sum  loop at 0.0.4.0  split under +wrap over 1 captured binding
PAR frontier    component(_par_split_sum.0)  excluded: _par_split_sum.0 is a synthesized loop function
```

The exclusion concerns recursion-budget cloning, not loop splitting. Both
LLVM modules contain `wf__par_split_sum.0` and its publication path. Both
linked ordinary and fragment builds retain that path; the ordinary build
calls `wf__par_publish`, while ThinLTO inlines queue publication in the
fragment build. Both sides compiled and emitted with exit 0 and empty
stderr in the final capture below.

### Owned-struct replacement: added cleanup without an offer loss

[displaced-struct.wf](upgrade-par-examples/displaced-struct.wf):

```whitefoot
struct Text {
  bytes: Box<Array<u8>>;
}

fn replace(text: &Text) -> result: unit writes(text) {
  let bytes = box_array_filled::<u8>(count: 4_u64, value: 0_u8);
  let next = Text(bytes: move bytes);
  set text^ = move next;
  return unit;
}

fn main() -> status: std::process::ExitStatus pure {
  let bytes = box_array_filled::<u8>(count: 4_u64, value: 0_u8);
  let text = Text(bytes: move bytes);
  replace(text: &text);
  return std::process::exit_status(code: 0_u8);
}
```

Hosted run 37902078784 meets the cleanup criterion. The ledger is identical
on both sides: the adjacent allocation/construction and replacement/return
pairs are denied for the same conditions, and no cyclic component exists.
There is no permission or offer loss in this example.

The old emitted `wf_replace` ends after the replacement with:

```llvm
call void @llvm.memmove.p0.p0.i64(ptr %v0, ptr %wf.slot.0, ...)
; drop %v5
ret i8 %v6
```

The new function retains the displaced pointer before the write and then
releases it:

```llvm
%v6 = load ptr, ptr %t1
call void @llvm.memmove.p0.p0.i64(ptr %v0, ptr %wf.slot.0, ...)
; load the displaced array length and calculate its allocation extent
call void @wf__heap_give(ptr %v6, i64 %drop.5)
; drop %v6
ret i8 %v7
```

These are excerpts; the complete emitted modules are in the artifacts.
Old `wf_replace` has zero release calls, new has one after the write.
Both ordinary and fragment-linked disassemblies retain the distinction:
old replacement has no `free` call; new replacement stores the new pointer
and then reaches `free`. All three examples compiled in ordinary,
function-fragment and LLVM-emission modes on both sides with exit 0 and
empty stderr. No executable was run.

## CI evidence, scope and remaining uncertainty

| Run | Diagnosis revision | What it retains | Result |
|---|---|---|---|
| [37897751877](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37897751877) | `c2e33901a6c71a297d7666721ecb124242c6a1ed` | Both complete cached function-fragment driver ledgers, stderr, exit codes, revision/pin and release manifests | Success; both compiler exits 0, empty stderr |
| [37898522362](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37898522362) | `117c8504307fd37eebc5a882bc91afd598adcc80` | Both full emitted driver modules and ledgers; linear-recursion example source, native/LLVM outputs | Success; all compiler/emission exits 0, empty stderr |
| [37900241732](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37900241732) | `dde7110b7ea126caf03504466646508fb391cbb9` | Both linked fragment drivers, symbols/disassembly and full ledgers; both examples, native/LLVM/fragment outputs | Success; both driver exits and all example native/emission/fragment exits 0, empty stderr |
| [37902078784](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37902078784) | `0e9236f1f20bb5da36e32b3ea4bbf3a946686fdb` | All three stand-alone sources, full ledgers/stderr, LLVM and ordinary/fragment-linked disassemblies; displaced-struct witness | Success; all example native/emission/fragment exits 0, empty stderr |

Artifacts are named `upgrade-par-diag-old-RUN` and
`upgrade-par-diag-new-RUN`; `compiler.stdout` is the full driver ledger and
`compiler.stderr` its complete stderr. Example outputs are under
`examples/NAME/`. Existing hosted checks passed on the first two diagnosis
revisions ([37897751672](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37897751672),
[37898522201](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37898522201)).
Hosted checks also passed on the linked-driver capture revision
([37900242515](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37900242515))
and the final example-capture revision
([37902079199](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37902079199)).
The temporary diagnosis workflow remains confined to this work branch, for
repeat captures while the runtime cause is open; remove it when that
investigation closes. It runs only on hosted runners.
A duplicate LLVM capture triggered by the final workflow push
(37900242590) was cancelled; it supplies no claimed evidence.

Established: this driver retains all old loop permissions and all old
outlined splits in the requested modules; #278 is reproduced independently
and removes the two identified CSS/style offers; critical text/layout split
budgets do not collapse to zero in emitted lowering; #294 adds the missing
five releases at shaped-text replacement. That upstream correctness defect
is already fixed by the new pin; no new Whitefoot gap was filed. No compiler source,
renderer, interface, pin or submodule is changed by this diagnosis.

Unverified: four-worker participation in the supplied timed run; the runtime
cause and its cost; a compiler bisect or intermediate-build attribution;
whether the same conclusions hold for other entry points. A non-timing
participation capture (scheduler reports/task counts for the same binaries
and workloads) would distinguish failure to execute offers from a cost
regression while offers execute. It is outside this ledger/source-only
capture. No recovery workaround is proposed or implemented.

Independent read-only completion review covered the full change from
`c3ea1c84ca3a2eca1e4048555d8a7298bd620d00` through
`dde7110b7ea126caf03504466646508fb391cbb9` plus this report, followed by a
limited review of the added displaced-struct witness through
`0e9236f1f20bb5da36e32b3ea4bbf3a946686fdb`, its hosted artifacts and the
report additions. It inspected the relevant pipeline/layout decisions,
complete workflow/example diff, requested ledger scope, affected compiler
rules, emitted modules and linked code. It ran no suite or program.

The review found one evidence error: `place_element`'s new `close_splits`
publication had been missed in its generated budget body. The table and
inventory scope were corrected and independently verified. The late
cleanup section's assignment citation was corrected to `prep.wf:703`.
No findings remain within the reviewed scope.

| Review group | Result |
|---|---|
| G1, DC3 | Not applicable: no design-tree changes or retired implementation |
| G2, G3, DC1, DC2 | Pass within scope: existing design commitments preserved; no renderer architecture change or recovery workaround |
| DC4 and engineering evidence/hygiene | Pass for static ledger/code-generation claims; runtime causal attribution unverified |
| R3, parallelism first | Pass: permission, actualization and execution distinguished; no added renderer dependency |
| C4, interface fidelity | Not applicable: interfaces and effects unchanged |
| T4, compiler pin | Pass: exact pins retained; no vendored compiler or submodule change |

The reviewer independently confirmed the site counts, changed call inventory
including generated budget bodies, critical split paths, cleanup witness and
captured exit/stderr evidence. Hosted gate conclusions were verified by the
implementing session; the reviewer did not poll CI. Local work used source
and captured-text inspection only. Runtime participation and causal cost
remain unverified rather than receiving a review pass.
