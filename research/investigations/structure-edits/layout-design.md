# M2 layout: parent-relative blocks and a flow splice

## Scope and measurement criterion

This is the layout design and sizing investigation for M2, based on
`7ee44119358d7b08dc90555ebe7b9275be478bed`, with Whitefoot pinned at
`f949e676acfa811f96b21afd07f02c06dcd14b51`. It proposes no rendering change.
Q109 already approves nested flow entries per block; Q104 reopens Q70's
context-relative suffix move. The implementation is staged below; Q114 A and the neutral complete-block seam Q115 A are owner-approved.

Recommend nested blocks with stable local entry slots, an owner-local
order/summary index, and a counter-neutral block splice. ecma262's tested
parent paths contain at most 208 direct entries inside a context of
112,817 entries; html5 still has a 6,648-entry sibling run. Parent-relative
origins remove descendant translations, while the index avoids copying
earlier entries. Whole-layout edit speed and full-build cost remain to be
measured in the implementation.

Before collecting the measurements: count each context's flow entries,
each block's direct entries and block children, and block depth. Compare
flat suffix size with the sum of direct sibling runs along an edit's
ancestor path. Reject the claim that nesting alone meets E1 if those runs
still approach the context's full flow, or if crossing float/margin state
requires replaying that flow. Prefer the shortest true dependency chain;
counts only size work, not prove speed. E1's whole-edit ceilings are 295 us
(apollo11), 3060 us (html5), and 115 us (ecma262), from
`../engine-comparison/runs/e1.txt`; M2 rounds these to 0.30/3.06/0.12 ms.

Time the existing `stack_flow(full_stack())` in isolation, after restoring
its normal pre-pass, child-layout and speculative line-break inputs outside
the interval. This is a warm replay of the current full-plan stacking pass,
not a splice implementation and not the whole layout stage. Empty its
`naturals` storage before timing so the first-pass allocation/initialization
is included. Include float fix-up within the pass; exclude column
fragmentation, positioned layout and split-fragment generation. Record the
timer granularity and spread. Compare the pass's height, baseline and flow
end with a preceding full layout; restore the context after probing and
check that the placed dump is unchanged. Sample a focused page first, then
one repetition per real page, then three only if affordable.
No estimate derived from these timings is a measured M2 edit latency.

## Inventory: identity, order, geometry and consumers

References below are to `renderer/layout/` unless prefixed otherwise. This
is an inventory of the compiled step-1/2 input, before the step-3 sequence
replacement described below, not additional CSS promises. A block
here is a non-BFC block in `Context.blocks`; a paragraph is an anonymous
inline formatting unit, which need not correspond one-to-one to a DOM `p`.
A child formatting context is a separate object with its own coordinate
space. DOM child count is therefore not the flow sibling count.

| Invariant today | Producer and consumers (`file:function` or interface type) | What a splice / parent-relative representation must replace |
|---|---|---|
| Block slots identify payloads; ancestry follows parent links and affected subtrees follow Open/Close entries. | `build.wf:place_element`; `style_update.wf:block_depth`, `common_restyled_block`; `flow.wf:block_at_entry`, `block_entry`; `update.wf:restack_block`, `local_ancestor_width`, `prepare_local_widths`. | Keep ancestry independent of slot values when introducing stable slots. The temporary width snapshot resolves parent links to Open entries within the affected flow range; it is not the eventual owned subtree. |
| A flat balanced Open/Close stream gives each block its parent, containing width and close. | `flow.wf:prepare_spaces`, `stack_flow`; `update.wf:restack_block`; `columns.wf:collect_units`; `module.wfm:Flow`. | A block owns a direct-entry sequence; entering/leaving it replaces Open/Close. An iterator may expose virtual Open/Close for the reference walker, without materializing a full flat array on edits. |
| Paragraph slots identify payloads; their order comes from Text entries in Context.flow. | `build.wf:end_paragraph`; `flow.wf:paragraph_at_entry`, `previous_stacked_paragraph`; `update.wf:first_float_entry`, `paragraph_after_entry`, `translate_after`. | The predecessor-with-lines query walks backward from the known flow entry. Translation visits only the following flow range; float influence compares flow entries, never paragraph slots. Stable entry handles remain to be introduced. |
| Each paragraph owns its pieces in inline source order; text routes use paragraph-local piece ranges. | `build.wf:add_piece`, `end_paragraph`; `prep.wf:prepare_paragraph`, `prepare_context`; `update.wf:patch_pieces`; `structure.wf:take_prepared`, `reuse_prepared`, `first_text_node`. | Keep pieces contiguous **within the paragraph**, owned by it. Inserting pieces must not shift every later paragraph's range. Whitespace collapse and shaping still run across the whole paragraph. |
| An open inline is closed and reopened across a block interruption; inserting a block can divide or join adjacent paragraphs. | `build.wf:stash_inlines`, `restore_inlines`, `emit_begins`, `end_paragraph`, `place_element`. | The splice boundary includes the two adjacent inline runs and open inline stack, not just the inserted DOM subtree. Plain block-between-blocks has empty boundary state; mixed inline/block content needs boundary repair or the existing rebuild fallback. |
| Splits are ordered by `open`, and `open`/`close` are flat flow indices. | `build.wf:open_splits`, `close_splits`; `flow.wf:place_splits`, `line_splits`, `split_closings`, `sibling_above`, `gap_lineless`, `split_fragments_with_empty`. | Stable entry endpoints and a local owning scope; order comparisons use that scope's sequence. A closing bit array sized to the context flow is not a retained edit structure. |
| Split/empty-inline fragments are derived from flow ranges and context-space extents, although `Fragment` itself has **no flow-index key**. | `flow.wf:entry_extent`, `shows_owner`, `empty_inline_fragments`, `split_fragments_with_empty`; `update.wf:range_start`, `translatable_fragments`, `translate_fragments`, `shift_split_lines`. | Anchor fragments to the narrowest owning block/paragraph and retain endpoint references for spanning fragments. Recompute a changed spanning fragment; do not translate every fragment of a context. |
| `Block.x/y` and `Paragraph.x/top` are owner-relative normal i64 origins; effective visual displacement is separate. The compatibility walker retains explicitly named context-coordinate scratch; paragraph line/fragment offsets remain paragraph-local. | `module.wfm:Block`, `Paragraph`, `Line`; `flow.wf:resolve_open`, `stack_flow`, `place_paragraph`; `inline.wf:break_lines`, `finish_lines`; `update.wf:range_start` and position readers and translation functions. | Distinguish normal-flow origin, CSS relative displacement and final visual origin. Store block/paragraph origins relative to their owning block; preserve paragraph-local lines. A mechanical `y -= parent.y` is insufficient. |
| Pre-pass `inner_x`, `avail_left`, `content_left`, paragraph `left` and `broken_left` are context-content coordinates. | `flow.wf:prepare_spaces`, `block_relative_offset`; `update.wf:local_width`, `write_local_block`, `write_local_paragraph`, `block_keeps_width`; `inline.wf:exclusion_room`, `break_lines`. | Keep width/percentage inputs separate from coordinate origins. Convert to context-content coordinates only where exclusion tests need them; a rigid subtree translation must not appear to change its line-breaking key. |
| `flow_at` names a flat entry for blocks, paragraphs and children; an atomic child uses its paragraph's entry. | `flow.wf:prepare_spaces`; `module.wfm:Context`, `Block`, `Paragraph`; `update.wf:entry_kind`, `restack_entry`, `shift_child`, `update_atomics_in`. | Stable `(owner block, entry slot)` handles, with explicit atomic/paragraph ownership. Ranks are ephemeral iterator positions, never persistent handles. |
| `naturals` has one position per flow entry; `baseline_entry`, restack ranges and `held_y` share its index/coordinate system. | `flow.wf:prepare_naturals`, `set_natural`, `later_floors`, `previous_stacked_paragraph`, `resume_open_frames`, `restack_settles`; `update.wf:restack_flow`, `shift_naturals`. | Attach natural state to local entries and baseline to a stable descendant handle. Parent motion must not rewrite descendant natural positions. Preserve the distinction between no-line/sentinel state and a valid coordinate. |
| Pending margin struts and unresolved ancestor tops can cross block edges. | `flow.wf:Stack`, `Frame`, `add_margin`, `resolve_open`, `open_unresolved`, `mark_lines`, `stack_flow` Open/Close branches. | Carry positive and negative components, through-collapse state, line/marker presence, border/padding barriers and height constraints. Equal height alone is not a cutoff. An empty block can transmit margin state without consuming height. |
| Floats belong to the formatting context, not the lexical block; earlier floats affect later descendants and siblings. Recovery orders child candidates by their Float entries, without scanning the unchanged flow prefix. | `flow.wf:place_float`, `float_bottom`, `narrow_beside`, `preceding_float_entries`, `resume_float_state`, `later_floors`, `restack_settles`; `inline.wf:exclusion_room`, `break_lines`; `module.wfm:Exclusion`. | Keep the BFC exclusion order and test its input/output at block boundaries. The temporary query scans child metadata and sorts selected float entry positions; it is not locality evidence. A nested block is not a new float containment boundary. Clearance, float floor, reach and horizontal room are observable inputs. |
| Child indices identify owned contexts across flow, inline marks, prepared atomics and table metadata. | `build.wf:add_child_flow`, `add_object`, `place_cell`; `module.wfm:Mark.Atomic`, `Piece.Object`, `Atomic`, `TableCell`, captions; `inline.wf:measure`, `atomic_metrics`, `finish_lines`; `flow.wf:place_atomics`. | Stable local child slots with holes or owned handles; update every cross-reference when ownership is migrated. No shifting live child identities on a splice. |
| Context identities are append-only directory slots, with tombstones and checked parent/child steps. A context rebuild publishes only its new subtree and retains outside identities. | `build.wf:record_tree`, `record_units`, `record_skipped`; `structure.wf:retire_at`, `retire_tree`, `retain_routes`, `relative_steps`, `structure_changed`; `update.wf:path_steps`, `mark_path`, `text_changed`; `module.wfm:TextUnit`, `ContextPath`, `ContextStep`. | Replace migration-time dense directory and NodeId-array copies with paged, targeted publication; replace append-only tombstones with checked-generation slot reuse when needed. Counts already use removed/added subtree deltas. Preserve skipped whitespace routing. |
| Each element has an explicit linked list of paragraph, block and context style uses, including uses in several contexts. Paragraph storage intervals and shared-use whole-tree fallback are absent. | `build.wf:note_use`, `record_uses`; `structure.wf:retain_routes`; `style_update.wf:styles_restyled`, `mark_use`; `module.wfm:StyleUse`, `StyleRoute`. | Replace copying retained route records during a context rebuild with targeted splice publication; preserve exact consumer membership. |
| A structural rebuild restores its context's entry walk state and must leave the same counter/quote state; retained generated spans and pseudo indices must still mean the same thing. | `build.wf:apply_counters`, `leave_scope`, `add_content`, `build_box`; `structure.wf:same_point`, `retained_outside`, `changed_outside`, `structure_changed`; `module.wfm:WalkPoint`, `StyleRef`. | Local building must prove a state-neutral seam, or replay dependent counter/quote readers, or refuse before publication. Reusing a context checkpoint at an arbitrary block insertion is wrong. Q111 stable element slots do not automatically stabilize pseudo/generated references. |
| Width/height/baseline/margins/intrinsic outputs and dirty counts govern propagation and no-change cutoffs. | `update.wf:before_of`, `same_outputs`, `update_held`, `update_flow`, `clear_marks`; `flow.wf:flow_frame`, `prepare_spaces`; `module.wfm:Context`. | Extend equivalent cutoffs to blocks, with margin/float output state. Preserve `definite_free`, intrinsic demand and positioned dependencies. Dirty ancestor flags alone do not justify scanning every sibling's payload. |
| Positioned descendants use the nearest positioned block's final dimensions; fixed boxes can use viewport origin. | `flow.wf:positioned_block`, `chain_anchor`, `position_child`, `position_out_children`; `flow.wf:place_context`. | Separate geometric owner from containing block. Mark dependent out-of-flow descendants when their containing block changes, and keep viewport-relative origins from accumulating block offsets. |
| A table cell's content can be shifted for borders/alignment, and its first baseline is read in flow order. | `table.wf:table_first_baseline`, `shift_cell`, `lay_out_table`; `tablegrid.wf` and `tableborders.wf` supply the table's dimensions. | First-baseline traversal descends nested flow in order. Apply a content-origin offset once, not to every nested block plus its descendants. Table rows/cells remain context-local; table-wide sizing remains a legitimate fallback. |
| Flex/grid sequences preserve document order among equal `order` values, while child storage is indexed independently; flex natural height reads every descendant extent in context coordinates. | `flex.wf:intrinsic_flex`, `flex_collect`, `flex_content_height`, `flex_position`, `lay_out_flex`; `grid.wf:grid_collect`, `grid_first_baseline`, `grid_finish_child`, `lay_out_grid`. | Keep a direct item sequence and stable child handles; convert extent reads or expose an equivalent subtree extent. Do not treat nesting as a reason to change item ordering, track algorithms or baseline rules. |
| Column units are in one-column context coordinates; avoid regions skip their descendants, and table children expose rows. | `columns.wf:collect_units`, `balanced_height`, `fragment_columns`; `flow.wf:place_rect`, `place_fragment`. | Accumulate block origins while collecting units, apply the column map only after coordinate accumulation. Rebalancing may reach the whole multicol context; it is not a plain sibling-translation edit. |
| Placement turns retained geometry into viewport rectangles; the dump groups them while preserving each owner's fragment order. | `flow.wf:place_context`, `place_boxes`; `renderer/oracle/layout/layout.wf:write_dump`, `put_rects`, `lay_out_page`; `renderer/oracle/layout/edit.wf:run_edits`, `finish_style_edit`. | One traversal carries accumulated origins, O(output), instead of an O(depth) ancestor sum for each rectangle. Keep fragment order, fixed origin and column ownership. Placement/dump are excluded from E1's layout timing and must be measured separately before paint. |
| Work counters currently mix restacked entries with translated suffix entries, and are not a complete count of everything visited. | `module.wfm:UpdateCounts`, `StructureCounts`; `update.wf:restack_flow`, `update_in_place`, `update_counts`; `structure.wf:structure_counts`; `renderer/oracle/layout/edit.wf` reporting and `research/investigations/incremental-layout/scripts/inctime.py`. | Preserve existing report meaning during migration; add separate physical visits, subtree skips, translated direct entries, rebuilt units, routing patches and fallback reason. `restack_flow` currently computes a suffix length even when no delta moves it; it also reports one paragraph for a block range. These are not valid locality proofs. |
| Saturating i32 layout arithmetic and f32 publication have a specific evaluation order. | `flow.wf:stack_flow`, `place_context`, `place_rect`; `inline.wf:px_of`; `module.wfm:lay_out` (Q54). | Reassociating parent sums can change saturated results. Relative differences need a wider temporary; preserve existing rounding and saturations, or use a checked full-context compatibility path for overflow cases. Never weaken byte identity to a tolerance. |

The pre-investigation `Fragment` comment called every fragment context-relative,
although `Paragraph` and `place_context` use paragraph-relative fragments.
The comment is corrected in this change; no coordinates or rendering change.

## Candidates and dependency chains

Let `E` be the inserted/removed subtree's layout units, `T` the scalars and
inline items in affected paragraphs, `D` the number of enclosing blocks
and contexts, and `s_i` the number of direct entries in ancestor `i`'s
sequence. Let `S = sum(s_i)` along the propagation path, `W` the subtree
whose widths or inherited layout styles actually change, and `F` the extra
entries reached by changed exclusions/clearance or an unsettled margin
boundary. `F` can be the rest of the BFC. `R` counts affected routing/style
uses and `G` affected split-fragment endpoints. Let `A <= S` count direct
entries actually reached: the later sibling ranges plus entries in the
explicit style/semantic frontier. Let `L = sum(log(s_i + 1))` count local
sequence-index paths. These are work counts, not nanoseconds. A wide parent can make `S` page-sized; nesting is not a bound
on sibling count. Removing `E` includes O(E) destruction and route removal.

For all candidates, shaping one paragraph depends on that paragraph's
source and styles; shaping different paragraphs is independent. Widths
propagate from ancestors to descendants. Intrinsic widths required by a
parent produce the reverse subtree dependency; flex/grid/table sizing can
then require another downward pass. None of these edges is removed by a
coordinate change. A font-size change may affect an entire inherited
subtree, not just the one block's border box.

### A. Owned nested flow per block (Q109), with stable local identities

A formatting context owns a synthetic root block. Each block owns its direct
block children, paragraphs (including their pieces), and child contexts,
and a sequence of handles specifying their interleaving. Payload slots are
stable for their lifetime; sequence position is not identity. A child block
appears once, rather than Open + all descendants + Close. Normal origins
and visual displacements are relative to the owning block. The BFC still
owns the exclusion domain; nesting does not establish a new BFC.

For the final splice, use an owner-local balanced sequence whose stable
leaves name entries and whose internal nodes cache subtree counts and
ordinary boundary-transfer summaries. Insertion allocates new leaves and
changes only O(log s_parent) index ancestors; no earlier entry leaf or
payload is read or copied. Prefix state is queried from cached internal
summaries. Growing payload storage uses stable pages and a bounded-depth
page directory, not a replacement array containing every old child. The
sequence's rank is queried when needed, never stored on every entry.
Sibling calculations remain independent; expose disjoint owned children
or a compiler-proved distinct-slot traversal, not a serial handle scatter.
A block's path is its parent link plus its parent's stable child slot.
Paragraphs and contexts use the same ownership rule. Full construction
assigns slots from known local counts, without a context-wide next-ID
counter; edit publication reserves only its owner's new slots.

A local `Slots<EntryId>` rebuilt on insertion is a simpler migration
reference, costing O(s_parent) handle copies even with no geometry work.
It **cannot pass M2 locality** because it copies earlier entries. The
balanced local sequence is therefore required for the final splice,
independently of whether html5 needs lazy range origins for speed.

- **Full build:** structural classification + inherited width inputs ->
  independent descendant construction/preparation -> subtree boundary
  outputs -> sibling placement -> parent output. Independent children are
  counted-loop iterations, recursing through their owned payloads. Line
  breaking is speculative at full width as today. Only counter/quote state
  that changes and is read later orders construction; identical incoming
  state can be read independently. After counter dependencies are settled,
  allocate local slots and gather child results by their input sibling
  positions, not by a shared append. Float placement and paragraphs beside
  floats follow the exclusion chain. For float-free runs, boundary
  transfers compose in a prefix scan; a uniform translation is an
  independent map. Work is O(all layout units + text work); geometric span
  is width depth + the longest text computation + per-level prefix depth
  + actual float influence chains. The existing serial builder may remain
  temporarily as a migration reference, not as a new parallelism choice.
- **Insert a block paragraph:** locate parent/seam -> build E with P's width
  and applicable walk state -> prepare/break its paragraphs -> replace P's
  direct sequence -> recompute P's affected boundary outputs -> propagate
  changed outputs up D ancestors. Other marked siblings' preparation is
  independent of E. At each ancestor, unchanged subtrees retain their
  contents; equal boundary inputs modulo translation permit one origin
  update each. Work O(E + T + A + L + F + R + G), with possible whole-container
  work for the named fallbacks. Ordinary span is E's dependency depth +
  text work + sum(log(s_i + 1)) + D; an exclusion chain adds its actual
  dependent work. This is **not** O(D) total work.
- **One block's font size:** changed style uses -> independent preparation
  of the affected paragraphs, and width propagation through W -> affected
  boundary outputs -> the same ancestor propagation and sibling maps.
  Work O(W + T + A + L + F + R + G). Font-unit advances may be rescaled where
  the current reshape key allows it. No new global shaping cache.
- **Text edit:** stable text route -> patch that paragraph's owned piece ->
  prepare/shape/break that paragraph -> compare its output -> propagate
  only if boundary outputs change. Work O(T + D) when outputs hold,
  otherwise O(T + A + L + D + F + G). Text/whitespace changes that create or
  destroy a paragraph enter boundary repair; they are not assumed to keep
  the box tree. The chain is the paragraph's text work followed by the
  ancestors; unrelated paragraphs have no dependency on it.

Sequence publication waits for new leaves and changed index ancestors,
not for a walk over the old prefix. Count index-node visits separately and
require an instrumented earlier-entry sentinel to stay untouched; calling
an earlier handle copy "metadata" is not a locality exemption. Prefix
placement is a data dependency, but a left-to-right loop through a whole
float-free sequence is not its shortest implementation.

### B. Flat flow in chunks, parent-relative block origins, subtree skips

Retain a flattened Open/Close/Text/Child stream, but store entries and
payloads in stable chunks. Blocks keep parent, matching-close and next-sibling
handles. Paragraph pieces move to per-paragraph storage just as in A;
leaving them in one shifting array would invalidate the claimed edit cost.
A global rank tree with stable entry leaves supports insertion without
context-wide memmove; chunks own payloads, not shifting order ranks.
Each block also needs a direct-child directory or equivalent skip index:
walking a singly linked sibling list merely to translate siblings would
add a serial O(s_i) chain that the translation does not need.

- **Full build:** classify/build local results -> compute chunk sizes by
  prefix -> fill disjoint ranges -> prepare paragraphs independently ->
  compute block boundary outputs and place siblings as in A. The rank/chunk
  directory adds a gather/index phase; it is a representation dependency,
  not a CSS dependency. Work O(all units + text), span of A plus the chunk
  index construction. A single shared append cursor is not recommended.
- **Insertion:** build E -> add stable entry leaves to the global order
  index, O(E + log(flow entries)) -> repair matching-boundary and direct-child
  handles on the D path -> A's boundary propagation. Work O(E + T + A + L +
  F + R + G + log(flow entries)); unchanged sibling subtrees skip in O(1)
  each. The global rank update is an additional dependent path. Copying an
  old chunk's earlier entry handles is ineligible under the same locality
  rule as A's migration vector.
- **Font-size change:** W's affected entries/payloads -> prepare/break ->
  the same boundary propagation as A, skipping unchanged subtrees by their
  matching-close handles. Work O(W + T + A + L + F + R + G); no index splice
  unless generated box topology changes.
- **Text edit:** direct stable paragraph/piece handle -> text work -> the
  same cutoff/propagation as A. O(T + D) for an unchanged output, otherwise
  O(T + A + L + D + F + G). Paragraph order must come from the chunk sequence,
  not the stable payload arena's slot order.

B is viable, and with a direct-child directory it can have the same
geometric dependency graph as A. It retains a second order representation
and needs disjoint-scatter proofs when a loop writes payloads reached
through flat handles. A's local owners narrow that proof to sibling-owned storage; its new
page/index traversal must still be proved at the pin. No measurement here
claims the proposed traversal already compiles. If B drops that directory or uses flat-array splicing, it adds a
pointer-chasing chain or O(context entries) copying and is rejected for
M2. The compiler's inability to carry a distinct-index fact between passes
is already recorded in `docs/todo.md`; do not hide that cost in a new
sequential scatter.

### C. Context-relative chunks (control, not recommended)

Chunks avoid the insertion memmove, but every changed height still moves
all later blocks, paragraphs, naturals and some fragments. Full-build
layout dependencies are unchanged; insert/font-size/text propagation does
O(context suffix) writes, even when the semantic influence ends at one
block. Those writes are independent and could run in parallel, but they
are unnecessary work required by the representation. This is Q70's cost
that Q104 reopens. A flat parent-relative array without stable splicing
removes the translation cost but still has the same page-sized insertion
copy and renumbering cost.

## Sizing observations (2026-10-05, Apple M1 Pro)

The preregistered criterion above was committed as `c0846b3` before the
measurements. The diagnostic source is
`e468312e7c53f826a2d2ea85e0c257c9d42736fe`, compiled sequentially with the
specified Whitefoot `f949e676acfa811f96b21afd07f02c06dcd14b51` compiler,
function fragments and the shared cache. The preserved confirmation driver SHA-256 is
`bc51558e163d7d95fa37cdc2865c6359893424973ef5a2632c696916e0524c05`.
It was rebuilt from the same source after the fault-injection checks; the
confirmation measurements below use that preserved binary.
Host: Apple M1 Pro, 8 CPU cores, 32 GiB, macOS 26.6.2 (25G83); viewport
1280 × 720, repository UA stylesheet, local fonts, no scripts. The
shared host build lock and 12,000 MB / 900 s guard covered each run. Other
worktrees also used that lock; these are short sizing observations, not a
controlled end-to-end engine comparison.

The diagnostic lives in `renderer/layout/probe.wf`, called only by
`renderer/oracle/layout/probe.wf` through the `probe` oracle mode, at
commit `b7ec605` of branch `research/flow-design-astra`. It was not merged
into the M2 branch, because it adds an oracle-only function and a
`std::time` dependency to `pkg::layout`'s interface; build that commit to
reproduce the tables. Step 6's physical counters replace it. No ordinary layout path calls the probe. `probe REPS PAGE UA
[sheet mappings...]` uses the same parsing, styles, fonts and viewport as
`dump`. Each repetition builds a fresh layout. It emits one row for every
context and every block, including a synthetic root sequence per context.
The first field is the repetition, followed by:

- Context: `0 serial owner kind context_depth flow_entries blocks paragraphs
  child_contexts stack_ns`.
- Block: `1 context_serial block_index owner local_depth direct_blocks
  direct_entries flow_open subtree_flow_span parent_block`.
- Clock calibration: `2 sample 0 0 0 0 0 0 0 empty_pair_ns`.

`4294967295` is the synthetic root/no-parent sentinel. Serials are census
identities only. A direct entry counts one Open for an immediate block,
one Text/Child/Float/Out, and no Close; it never includes that child's
descendants. Local block depth starts at 1 under its context; context
depth starts at 0. These two distributions are separate, not an assertion
that their quantiles can be added. All quantiles below are nearest-rank.

### Counts and the actual edit parents

| Census | apollo11 | html5 | ecma262 |
|---|---:|---:|---:|
| Contexts, including empty/non-flow | 1,113 | 13,843 | 10,217 |
| Contexts with flow entries | 980 | 13,408 | 10,036 |
| All flow entries | 5,675 | 117,924 | 128,718 |
| Non-BFC blocks | 1,262 | 28,044 | 34,302 |
| Paragraphs | 2,569 | 60,868 | 57,514 |
| Flow/context, nonempty: p50 / p90 / p99 / max | 1 / 7 / 16 / 1,190 | 1 / 1 / 1 / 104,321 | 1 / 2 / 12 / 112,817 |
| Direct entries/block: p50 / p90 / p99 / max | 1 / 3 / 17 / 594 | 1 / 4 / 26 / 6,648 | 1 / 5 / 19 / 219 |
| Direct block children/block: p50 / p90 / p99 / max | 0 / 1 / 8 / 297 | 0 / 2 / 13 / 3,432 | 0 / 3 / 11 / 108 |
| Sibling entries seen by each block: p50 / p90 / p99 / max | 10 / 593 / 593 / 593 | 17 / 6,647 / 6,647 / 6,647 | 6 / 38 / 172 / 218 |
| Local block depth: p50 / p90 / p99 / max | 2 / 7 / 9 / 11 | 4 / 7 / 11 / 26 | 5 / 9 / 13 / 23 |
| Context depth: p50 / p90 / p99 / max | 8 / 9 / 13 / 14 | 3 / 4 / 4 / 4 | 4 / 6 / 7 / 8 |

The sibling row samples **blocks**, so a wide parent's many children each
see the same large sibling count. The direct-entry row samples **parents**.
Confusing them would hide the broad parents that dominate edit work.
The largest contexts have census `(serial, owner)` `(815,10244)`, `(1,2)`
and `(91,21173)`. Apollo's edit-dominant context is instead `(349,2044)`:
1,014 entries, 243 blocks and 420 paragraphs. The observed ecma262 maximum
is 112,817, not the approximate 118,000 in the task; this report uses the
count actually produced by the pinned source and captured inputs.

| Local block depth histogram | apollo11 | html5 | ecma262 |
|---|---:|---:|---:|
| 1 | 218 | 58 | 1,075 |
| 2 | 443 | 3,432 | 612 |
| 3–4 | 223 | 14,854 | 8,141 |
| 5–8 | 338 | 8,265 | 20,861 |
| 9–16 | 40 | 1,415 | 3,539 |
| 17–26 | 0 | 20 | 74 |

Resolve the existing E1/X5 block-script B parents through the independently
regenerated node listing to their owning block or context root. Count all
direct entries along that block's ancestor path **inside its owning
context**, including the context root sequence. Call this `S_C`. It is a
conservative scan/copy ceiling for that path: it includes entries before
the edit; it excludes outer contexts, additional float influence and style
frontier changes. It sizes a conservative direct-run scan, not the
recommended index's actual leaf visits; earlier leaves remain untouched.
It is not measured replay work. All script parents
resolved exactly to their own block/context owner, without an ancestor
substitution. B/X pairs return to the original structural shape.

| Existing forward B edits | apollo11 | html5 | ecma262 |
|---|---:|---:|---:|
| Insertions sampled (inverse removals use the same seams) | 30 | 30 | 10 |
| Direct entries at insertion parent: median / max | 14 / 41 | 7 / 6,648 | 7 / 15 |
| `S_C`: p50 / p90 / max | 49 / 74 / 74 | 6,716 / 6,898 / 7,080 | 149 / 200 / 208 |
| Owning-context flow sizes reached | 3; 1,014 | 104,321 | 9; 17; 112,817 |

For the main contexts, the maximum `S_C` is about 7.3%, 6.8% and 0.18% of
its flat flow size, respectively. These ratios compare conservative work
counts, not a speedup prediction. They support nesting strongly for
ecma262. html5 retains a 6,648-entry run at the body, even for many deeply
nested edits. The local sequence already needs a prefix-summary index for locality;
first retain independent origin writes over the affected later run. If
that measured cost breaks the budget, add lazy range offsets to the index. That tree buys O(log s) path updates for an
ordinary range translation, with additional retained summaries and lazy
origin reads. It must not introduce a single shared writer for otherwise
independent subtrees. Adding lazy origins globally now has no measured cost basis; the order
and summary index itself is mandatory to avoid touching earlier leaves.

A binary local sequence index would have 4,413 / 89,880 / 94,416 entry
leaves and 2,214 / 48,429 / 50,078 internal nodes respectively, computed
as `sum(max(direct_entries - 1, 0))` over blocks plus context roots. These
are representation counts, not allocated bytes or timings: a packed
multiway index may use fewer nodes. They make the memory/full-build risk
concrete; the index should not allocate a separate heavyweight object for
every single-entry sequence. Its fanout is an implementation measurement
within the same dependency graph, not permission to scan preceding leaves.

### Isolated full-plan stacking time

The initial six-block fixture took 0.50 s wall, and `flow-cases.html` 0.07 s;
the real-page one-repetition pilot took 0.45 / 2.31 / 3.40 s wall. This sized
a three-repetition run (0.96 / 5.72 / 8.25 s wall). After fault injections
rebuilt the driver, a confirmation run retained and hashed that binary
and repeated three times (1.30 / 5.57 / 7.75 s wall). The table reports all
three confirmation samples, without warm-up removal or best-run choice.
Counts were identical in all six repetitions.

| Timed interval, milliseconds | apollo11 | html5 | ecma262 |
|---|---|---|---|
| Sum of one stack pass per nonempty flow context | 1.753 / 1.735 / 1.751 | 5.201 / 6.276 / 6.343 | 5.602 / 6.348 / 6.470 |
| Largest flow context only | .032 / .031 / .032 | 3.371 / 4.473 / 4.345 | 4.189 / 4.912 / 5.027 |
| Apollo's edit-dominant context only | 1.409 / 1.406 / 1.413 | — | — |
| Number of timed flow contexts | 810 | 13,408 | 9,212 |

The preceding run's summed samples were 1.815 / 1.869 / 1.851 ms,
5.417 / 6.426 / 6.762 ms and 5.769 / 6.649 / 6.801 ms respectively.
They support the same sizing conclusion; the confirmation was to preserve
measurement-binary identity, not to select a faster run.

These are **one full-plan stacking pass at each context's final space**,
not the accumulated stacking time inside an integrated full build, which
may visit a child again during sizing. Inputs are prepared and the
context fully laid out before the interval; `naturals` is then emptied so
its allocation/initialization is included. The interval includes whatever
float fix-up `stack_flow` invokes, including dependent child/paragraph
work; it excludes the preceding width preparation, child layout and
speculative line breaking, and subsequent splits, columns, positioned
layout and placement. Apollo's timing is therefore not proportional to
its flow count. The probe checks the pass's resulting height, baseline and
flow end, then restores full layout and compares every placed rectangle.

`std::time` reaches `clock_gettime(CLOCK_MONOTONIC)` through pinned
`compiler/src/backend/completion/file_posix.c:wf_file_monotonic_ns_host`.
Observed values are quantized in 1,000 ns increments; the empty-pair
samples have median 0 ns and maximum 1,000 ns. Zero does not mean zero
work. Summing thousands of sub-microsecond context intervals is coarse;
the large-context intervals are the more useful evidence. The repeated
large-context passes vary by roughly 20–35%; no conclusion here depends on a
small timing difference, so a longer run would not choose between the
unimplemented candidates. The result is sufficient to reject a full
stacking pass as ecma262's 115 us edit path.

Dividing the **entire** historical E1 budget by max `S_C` gives generous
ceilings of 3.99 us, 0.432 us and 0.553 us per visited direct entry. These
are arithmetic limits, not estimated processing times: construction,
styles, text preparation, ancestor contexts, floats and publication also
consume the same budget. In particular, do not extrapolate 208 entries
from the 112,817-entry stack time and call it an achieved M2 latency.
The 16/239/259 ms layout-stage figures in
[`DESIGN.md`, Where the cost is now](DESIGN.md#where-the-cost-is-now)
include much more work than this interval; this experiment does not attribute their difference to stacking.

### Reproduction and input identity

From the worktree root, after the task's locked/guarded compiler command:

```sh
build/layout_oracle_seq probe 3 build/research/concurrency/apollo11.html renderer/style/ua.css \
  'wikibase.client.init&only=styles&skin=vector-2022=build/research/concurrency/apollo11-modules.css' \
  'modules=site.styles&only=styles&skin=vector-2022=build/research/concurrency/apollo11-site.css'
build/layout_oracle_seq probe 3 build/research/concurrency/html5.html renderer/style/ua.css
build/layout_oracle_seq probe 3 build/research/concurrency/ecma262.html renderer/style/ua.css \
  assets/css/ecmarkup.css=build/research/concurrency/ecma262-ecmarkup.css \
  assets/css/print.css=build/research/concurrency/ecma262-print.css
```

Run measurements under the host lock/guard, as for compilation. These
commands emit all per-context/per-block counts rather than only the table.
For each repetition, sum tag-0 column `stack_ns`; select the same census
serial for a context interval. For counts use one repetition, ignore tag 2,
and include the synthetic root when summing direct entries. The following
independent identities held for every context on all three pages:
`sum(direct_entries) + blocks == flow_entries`,
`sum(direct_blocks) == blocks`, and globally
`sum(child_contexts) == contexts - 1`.

Inputs were copied as regular files, not symlinked. Apollo uses the E1
step-4b supplementary capture (`engine-comparison`'s `apollo-supplement`),
not an assertion that the unavailable original capture was recovered.
All three freshly generated node listings exactly matched the listings
used by the existing scripts. SHA-256 identities:

| Input under `build/` | SHA-256 |
|---|---|
| `research/concurrency/apollo11.html` | `26ad3f9e6f81d685e848ceb43dec17b3b5fcc81c2896a8182599662decd65169` |
| `research/concurrency/apollo11-modules.css` | `cc2e64f8f1706af7f505ec69b6c9807cb05a743f7887ccbf8c7e104e1f41a9f8` |
| `research/concurrency/apollo11-site.css` | `3f439934c51c220c4b92072d4dec2219920cef1bbafb58eda32a7161df7b9d0c` |
| `research/concurrency/html5.html` | `f0466f5a8c8099935a9394607abcd4bbbb3b41384a14b3f906eea80a521fe06e` |
| `research/concurrency/ecma262.html` | `e2b29c85f37b8ded51873ce385b6573a35cbc26b467c21c14f8184f3bab5aa26` |
| `research/concurrency/ecma262-ecmarkup.css` | `8bef2688107197ac28abe81b62a61100904cec548e223d03a10ac7ea7b6b2fc7` |
| `research/concurrency/ecma262-print.css` | `e80f1880ab96cb3418cddbcd7a529aa6e474113f4a87c2555d079f84fc09c53f` |
| `x5/scripts/apollo11-block.edits` | `1c2503a8240268b3172121e64dfdbffce25cd0939c488f069a11e107088e4573` |
| `x5/scripts/html5-block.edits` | `b7d1e894ce50aa6e20eec702ff987137c476b61ea2b8b2b9593b7c17f09b771c` |
| `x5/scripts/ecma262-block.edits` | `e401d4b06cd9ecc7aec00096220f2f91130aac1cdde3303572786cf535f55b1f` |

The historical Chromium comparator is 141.0.7390.37 / Playwright build
1194, viewport 1280 × 720, scripts disabled, as recorded in E1. Chromium
was not rerun here. This is a source/representation sizing study, not new
evidence that Snowghost beats Chromium.

## Recommended contract

Choose A, as Q109 directs. Expose a virtual flat iterator for comparison
with the current walker during migration; do not retain B's additional
global order representation on every edit. The owner approved local stable slots, an order/summary index and boundary
outputs (Q114 A). The owner also approved the initial neutral complete-block seam with explicit
fallbacks (Q115 A). Approval does not establish implementation or
measured locality.

### Ownership and lookup

Conceptually, the types are the following; this is a contract sketch, not
Whitefoot source to compile:

```
FlowBlock = style, parent_route, local_depth,
            normal_origin, own_relative_shift, used_size, width_inputs,
            paged_slots<Block | Paragraph | Context>, indexed_sequence<EntryId>,
            boundary_output, dirty_children, local_split_fragments
Paragraph = existing shaped/line data + owned contiguous Piece storage
EntryId   = owner-local stable slot + checked generation
Route     = owning block/context route + stable slot
TextUse   = paragraph route + local piece range
StyleUse  = owning block/subtree route and explicit paragraph uses
```

The sketch can use separate typed slot pages and a tagged sequence, to
keep existing counted-loop preparation and child-context layout forms;
it need not force all payloads into one large enum. Nothing persists a
preorder integer as identity. Ancestor intersection aligns depths and
walks parent links, O(D), replacing `common_restyled_block`'s numeric test.
A preceding paragraph with lines is found through last-line/first-line
subtree outputs and predecessor entry links; there is no binary search of
append order. Full dump iteration follows sequence order and emits the
same fragments per owner as before.

A route directory is routing data, not an alternate owner of geometry.
Context serials may initially stay numerically identical to a full build,
but appended serials must remain valid without reindexing old paths. New
routes are allocated within their new subtree and published in disjoint
slots. Use chunked growth for NodeId-indexed `text_units`/`uses` and route
pages so one added node does not allocate and initialize an array as large
as the DOM. Use a fixed-fanout shallow radix directory so growth touches
only new pages and their directory paths, and include that allocation
inside the measured edit. Do not depend on an untimed reservation to hide
a whole-directory copy. A table
shared by all elements is not a shared **mutation chain**: independently
known NodeIds write disjoint slots. If that independence cannot be proved
at the pin, resolve the minimal Whitefoot proof gap before replacing it by
a serialized global writer. Do not import Q111's style-slot identity as a
layout order.

After deletion, clear only removed routes and uses. Reuse a local slot
only after incrementing its checked generation, so an old route cannot
alias a new entry; exhaustion refuses before publication. Reserve a batch
of free/new slots in one owner operation, then initialize them independently.
Use pages so that growth copies no earlier live payload. Compaction is an
explicit full rebuild, off this edit path; it updates every holder atomically.
Existing `docs/todo.md` session-growth work owns its policy.

The sequence interface needs `insert_before(stable_entry, new_range)`,
`remove(range)`, `prefix_output(before_entry)` and `visit_later(range)`.
Its internal-node summaries include count, first/last line handles and the
ordinary margin transfer, or an explicit unsupported-state flag. Insertion
updates aggregates on the index path without opening a preceding leaf;
rotation/rebalancing moves index links, not payloads or all stored ranks.
Boundary-state changes update the same path. `visit_later` descends only
intersecting subtrees and exposes independent owned child regions. Validate
that traversal's proof at the pin before changing all payload types; a
missing distinct-slot proof is a Whitefoot gap, not license to serialize
unrelated writes. Local index nodes and payload pages are block-owned, so
there is no context-wide order index shared by unrelated blocks.

### Geometry and boundary outputs

Use the parent's **normal-flow border origin** for layout offsets; retain
CSS relative displacement separately. At placement, accumulate normal
origins and visual displacements separately, exactly once. A child context's
own internals remain context-local; its anchoring position becomes local
to the nearest owning block. A fixed context keeps the viewport-origin
exception. Absolute positioning reads its containing block's origin/size,
which is not necessarily its geometric owner.

Do not turn `Stack` into persistent snapshots at arbitrary entry numbers.
Store each block's semantic output, invalidated with that block:

- resolved size, content advance, ink/content extent, first/last baseline
  handles and positions, and line/marker presence;
- leading/trailing margin struts as `(largest positive, most negative)`,
  whether they collapse through an empty block, and barriers caused by
  border, padding, clearance or constrained height;
- whether the block reads/exports floats, its exclusion input dependency,
  and any outgoing active exclusions/float floor/reach needed by later flow;
- width/percentage bases, intrinsic demand/results and positioned/column
  dependencies needed for the same-output test.

For a float-free run with stable widths and already measured child
outputs, margin struts combine with `max(positive)` and `min(negative)`
until a separator settles them; advances then add. Through-collapsing
empty entries preserve the pending strut rather than advancing the cursor.
Represent each such entry as a boundary-state transfer, composed in tree
order, and use an order-preserving parallel prefix over the direct run.
The summary must retain both ends and the through flag: a single collapsed
margin value loses information (`max(10, 5) + min(-4, 0)` cannot be recovered
from the sum 6 alone). A resolved child's internal origins are independent
of the absolute origin at which that prefix places it.

A concrete ordinary transfer can be represented as either `Through(a)` or
`Solid(l, h, t)`, where a strut is a positive/negative pair, `join` takes
componentwise max/min, and `value` adds the pair. For entering state
`(y, m)`, Through returns `(y, join(m,a))`; Solid returns
`(y + value(join(m,l)) + h, t)`. Here `h` is the advance between the first
and last resolved edges, not a border height with external margins added.
Composition in document order is:

| Left then right | Composed transfer |
|---|---|
| `Through(a); Through(b)` | `Through(join(a,b))` |
| `Through(a); Solid(l,h,t)` | `Solid(join(a,l),h,t)` |
| `Solid(l,h,t); Through(a)` | `Solid(l,h,join(t,a))` |
| `Solid(l1,h1,t1); Solid(l2,h2,t2)` | `Solid(l1,h1 + value(join(t1,l2)) + h2,t2)` |

This is a fixed-size associative representation of those transfers when
arithmetic does not saturate. Use a balanced reduction and down-sweep to
obtain the entering state at each direct entry; independent entry origins
then follow. Cache the first resolved-edge handle plus internal min/max
extents and first/last line handles relative to that edge, so negative
margins and baselines do not make final cursor equal final content extent.
Through-only blocks defer their unresolved origin to the eventual resolved
edge instead of forcing that edge early. The old Open/Close rules determine
which edges can be represented this way; a border, padding, marker or
height constraint must not be silently classified as Through. This gives
the implementer an explicit algebra to test, not permission to change
those classifications. Step 4's varied-entering-state comparison is the
acceptance test for lifting nested block outputs into these transfers.

This bounded summary is only for the translation-invariant ordinary case.
A changed height clamp, unresolved ancestor edge, clear against floats,
positioned dependency or non-equivalent exclusion input expands the replay
region until the full state is equivalent, or selects the full-context
path. Do not assert that every arbitrary float-dependent block has a
constant-sized composable summary. Prove the ordinary summary against the
existing entry machine with varied entering positive/negative struts,
empty blocks, first/last borders, explicit/min/max heights and outside
markers before it becomes the implementation. A missed case rejects the
summary or narrows the *new fast path* while preserving full rendering.

After recomputation, a clean sibling with the same width and boundary
input modulo translation consumes its summary and changes only its local
origin. The sibling-origin writes are independent once their prefixes are
known. Where all outputs converge except a common delta, map that delta
over the remaining **direct** siblings; do not descend them. Recompute the
parent output, then repeat at the next ancestor. Stop when size, baseline,
margin transfer, intrinsic output and exclusion output all hold. Thus a
paragraph inserted in a section moves the next sections once each, not
every paragraph in those sections.

Floats remain an ordered list in their BFC. Their placement reads preceding
float geometry, clearance and the natural cursor; paragraph fix-up reads
the exclusions that overlap it. Reuse requires the same normalized
exclusion geometry, not merely the same maximum bottom. A float from a
preceding sibling may reach a changed descendant and a float inside that
descendant may reach following siblings. Replay that influence chain;
resume ordinary summary composition only after it ends. Independent
full-width preparation/line breaking still occurs before this chain.

For saturation: compute differences between resolved i32 origins in i64,
and add through i64 before the legacy conversion point. That protects
subtraction but does not make saturating addition associative. Any block
for which the legacy operation order could saturate leaves the summary
path; replay the existing context-coordinate machine, then encode its
resolved outputs as exact wider parent differences. Keep this compatibility
path until saturation cases prove a replacement byte-identical. It is a
numeric condition applying to every page, not a workload special case.

### Origin-aware ordinary arithmetic certificate

Question: can the fixed 2^26/2^27/2^28 admission limits be replaced by
an origin-dependent certificate without changing the reference result?
The comparison is incremental versus full sequential rebuild, plus seq/par
identity, on every X5 edit and on near-limit signed-margin/baseline cases.
A mismatch, a missed counted refusal when an intermediate would saturate,
or an undetected unsafe-admission mutation rejects this proposal. This is
an arithmetic correctness change, not a performance claim.

Let M = 2147483647 layout units. For a context, O is its actual
`flow_frame.content_top`, and T is the sum of absolute elementary vertical
terms in its ordinary root transfer. A margin contributes its absolute
value; a solid contributes its absolute height; a paragraph also contributes
the absolute top and baseline components of its first and last lines,
separately (the absolute value of their sum would hide cancellation).
A child context contributes its measured border height, external margins,
and both exposed baseline excursions. Its contents have their own coordinate
space and are certified separately when changed. Joins add T; block lifting
adds margins and top/bottom frames. Max/min collapsing struts select existing
terms and cannot enlarge this sum.

Admission for an update requires **|O| + T_old + T_new <= M**. This certifies
both reference runs and leaves the necessary room for differences between
them, not just each final cursor. All certificate arithmetic is i64 with
saturating positive sums: overflow rejects rather than wrapping. Index
summaries have no placement origin; each nonempty join clears `ordinary`
when T > M (the necessary zero-origin condition). An identity join preserves
its input, and publication always performs the stronger check with the real O. Semantic barriers remain independent of this numeric
condition. For a splice, privately compose the candidate owner sequence,
lift through its block ancestors, and then preview enclosing context sizes
and baselines bottom-up. Check each context's old and proposed root, rather
than assuming a safe old root makes a growing ancestor safe. A text update
uses the same block-ancestor preview. The dependency chain is exactly the
existing ancestor propagation; sibling prefixes remain independent cached
reductions, with no descendant geometry walk.

The reference audit (`renderer/layout/flow.wf:stack_flow`, `boundary.wf`,
`geometry.wf`, `box.wf:used_height`, `update.wf:finish_in_place`) is:

| Ordinary position step | Coverage or retained exclusion |
|---|---|
| `pending_margin`: positive + negative; `add_margin`: max/min; cursor + pending margin, including preliminary line positions and final flow end | Each selected margin is charged once per settled edge by its source term. The extrema have opposite signs, so adding the pair cannot overflow. Prefix absolute sums bound every cursor. |
| Open: border.top + padding.top, cursor + collapsed margin, then y + top_frame; `resolve_open` copies y into pending ancestors | Nonnegative frame components are charged by their sum; a saturated frame itself cannot pass the combined bound. No operation on y other than addition/copy. |
| Close: optional cursor + trailing strut, top + top_frame + marker, max(flow_end, marker_end), content_end - top, + bottom_frame, top + height | Markers and constrained block heights remain excluded. For an ordinary auto block, the difference cancels its common prefix and is bounded by the terms inside it. `snapshot_grows` retains the lower-frame clamp check on changed ancestors; already ordinary sibling interiors are unchanged. Nonnegative top/bottom frames are charged by lifting. |
| Text: cursor + pending strut; y + paragraph.height; line.top + line.baseline; y + line_base; content_top + that value | Travel charges absolute height and the individual first/last baseline components, so cancellation cannot hide a saturated intermediate. Line breaking, glyph placement and its rounding run unchanged on the paragraph before this certificate. Atomic inlines and float-dependent paragraphs stay excluded. |
| Child: max(cursor + strut, clear_floor), y + child.height, y + child.baseline; content_top + y or baseline | Clearance and parent floats remain excluded. The no-clear floor is -M: T <= M makes it inert. Child height and baseline are measured atoms. Its anchor is this very content_top + y, not an additional uncounted displacement. |
| Block/paragraph/child normal versus visual positions: y + dy (+ own_dy), then content_top + y | Nonstatic blocks and child entries remain excluded, so all those relative offsets are zero. The context's own external placement is applied separately by the existing placement walk. |
| Horizontal widths, percentage resolution, specified heights, line shaping, division/rounding | These are not reassociated functions of the vertical cursor. They are evaluated by the same helpers with unchanged width/percentage inputs; changed child/paragraph results are measured before composition. Width changes, intrinsic dependencies, columns, splits, positioned entries, clearance, floats and unsupported height constraints keep their existing refusal paths. |
| `content_raw`/`flow_end`, context baseline, ancestor block heights, and direct sibling origin updates | Old and new reference values are bounded as above. Their i32 differences are bounded by T_old + T_new; the common O cancels. Adding the exact difference gives the certified new value. `used_height` then performs the same frame additions and clamps in the same order as full layout; it is not reassociated, even if that final size clamps. Its resulting child height is certified as an atom in the enclosing context. |
| `origin_from_resolved`, `origin_relative`, `origin_accumulate`, `geometry_narrow`, dump/paint | Parent differences and reconstruction use i64. Telescoping reconstructs the certified reference i32 context-local origins exactly; the legacy narrowing and subsequent placement/float conversion order are unchanged. Child internals and fragment offsets are neither translated individually nor reassociated with the external anchor. Table content offsets (`content_dy`) remain a separate addition after origin narrowing; a table ancestor still excludes structural splicing, and marked tables rebuild. |

Thus every reassociated ordinary reference position is O plus a prefix
of counted terms, or a difference of two prefixes whose common part
cancels. All intermediate additions/subtractions lie in [-M, M]; max/min
only select such values. In this domain saturating i32 operations equal
integer operations, the transfer algebra is associative, and index-order
composition equals the sequential reference. The symmetric bound deliberately
leaves i32's extra negative endpoint unused. It is sufficient, not necessary:
some safe large/cancelling pages may still replay. Cases outside the audit
continue through the reference walker; no claim is made about reassociating
arbitrary saturation, clearance, relative displacement or percentage layout.

A numeric refusal must force a complete reference stack, not fall through
to the legacy delta or partial-stack shortcuts. The positive-margin fixture
at `9dff281` (CI job 112607339534 in run 37563963179) exposed why: expanding
text clamps the content total at M, and shrinking it cannot recover the
reference total by subtracting the text delta from that clamped value.
`boundary_update` now marks a failed old-origin/travel certificate for full
stacking, as it already did after a failed post-recompute certificate. The
fixture's fourth edit failed before this repair; the requirement remains
exact rebuild identity, including when the retained path refuses.

The CI fixture is `incremental-layout/scripts/near-limit-case.html`, driven
by `near-limit.py DRIVER OUTPUT_DIR`. The script derives live node IDs and
keeps generated variants, edits and raw logs under the output directory.
Its admitted variant uses a 4,000,000 px independent block and a -1,000,000 px
margin, exceeding the old limit while leaving room for both the owning and
enclosing contexts' exposed baselines. Refusal variants use a 33,554,000 px
block followed by a -33,552,000 px margin and a positive bottom margin,
a 33,553,000 px positive margin, a small fixed-height child exposing a baseline near M, and a context content
origin near M. Each inserts/removes a block and grows/restores text; all
edits must equal a full rebuild, structural refusal must report reason 7,
and text refusals must be counted. The unsafe-admission mutation replaces
M in the shared certificate with 68719476735 and must produce an actual
incremental/rebuild difference, not merely a changed path. Assertion probes
independently remove path/count rows, change mode/reason and zero refusal
counts, requiring each broken condition to fail.

Focused CI evidence at `66fdec5`, run
[37565331129](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37565331129):
all five near-limit variants' four edits equal their full rebuilds; the
admitted variant's two structural edits splice locally, the other variants'
structural edits refuse with reason 7, and their text refusals are counted.
This includes the positive-margin inverse text edit that failed at `9dff281`.
The page block edits also all equal their rebuilds, but none splices locally:
ecma262 edits 1–20 now report reason 2, traced to the flex context guard;
html5 edits 1–60 report reason 7, traced to the nonordinary root transfer's
positioned/atomic barrier 5. These are semantic exclusions outside this
argument, retained in `docs/todo.md`; changing the arithmetic certificate
alone does not establish the pages' zero-fallback acceptance. This focused
run does not establish full seq/par or unsafe-mutation validation.

### The splice transaction

1. Receive the changed DOM parent, before-sibling or end marker, inserted /
   removed subtree, and the style frontier from M2 steps 1–2. Resolve them
   through stable uses to the owning block and direct entry seam. A parent
   with `display:contents`, anonymous wrappers or split inlines may map to
   a containing scope rather than to one block.
2. Validate the seam **before mutating retained state**. For the first
   supported path it is between complete block-level entries, with no
   inline run crossing it, stable generated/pseudo references, and a
   counter/quote-neutral inserted/removed range. Style changes to siblings
   are not ignored: their uses join the same dirty frontier.
3. Build the inserted subtree in private owned storage from P's width and
   applicable style/walk inputs. For a neutral range, no arbitrary cached
   counter value is needed; if it reads a counter/quote, find its exact
   input from the nearest recorded scope boundary or refuse. Lay out child
   contexts and prepare paragraphs independently where their inputs permit.
   A failed allocation or unsupported state leaves the old layout intact.
4. Allocate new entry leaves, the changed local sequence-index path and
   changed route/use pages; stitch E in (or remove it). Publish only after all construction and
   validation succeeds. Unchanged paragraphs keep their existing shaped
   payload by ownership; there is no `reuse_prepared` search/swap over C.
5. Recompute from the earliest changed boundary (including a preceding
   collapsing edge if necessary), settle P, and propagate as described
   above. Split repair includes both endpoints and adjacent inline runs;
   a split's owner can lie outside E. Report every fallback and every
   physical visit. Update total live counts by added-minus-removed subtree
   counts, not `count_tree(root)`.
6. Removal uses the same seam contract and boundary recomputation. An
   insert/remove roundtrip preserves rendering, not arena slot numbers.
   Repeated insertions before the same old sibling and removal of both a
   newly inserted and a pre-existing block must work without rank aliasing.

Counter writes/readers are a true document-order dependency. Keep Q86's
refusal when an outgoing counter or quote state changes; leave dependent
reader propagation as a separate owner choice, not a hidden requirement
for this block-paragraph path. A content declaration or list item may
change that state even when its visible text is unchanged. Neutrality must
follow style/box-construction effects, not the tag name `p`.

Flex/grid/table/multicol reconstruction, mixed-inline boundary repair,
changed generated references and non-neutral counters retain a correct
full-build route while the fast path is introduced. They must be counted
as fallbacks, never successful local splices. Do not declare E1 complete
if any timed block edit takes that route. Once the representation is in
place, supporting more seams changes the locality achieved, not the
rendered subset.

## Implementation sequence and falsifiers

Step 1 has paragraph-owned pieces, explicit flow-order/parent queries,
append-only context identities with checked routes, and explicit paragraph
style uses. Context rebuilding retires only its subtree and publishes its
replacement without renumbering retained contexts; dense routing metadata
copies remain migration support. Stable entry handles arrived in step 3; paged route growth and the neutral
splice now have the step-5 source described below. Step 1 is the compiled input to step 2; its validation evidence remains
with the primary agent, and is not a step-2 validation result.
The step-3 source removes `Context.flow`: each block and the context root
own an `EntrySequence`. Its stable direct-entry slots and AVL metadata use
separate lazy pages. The virtual walker synthesizes Open/Close events by
weighted descent for isolated lookups; compatibility walks materialize one
transient event array, filled through disjoint cached rank ranges. Recorded
compatibility positions, split endpoints and baseline entries are still ranks;
the block, paragraph and child-context records also carry local entry slots.
The indirect payload writes still need a Whitefoot disjointness proof;
child-context publication still follows child slots. Both limitations are
recorded in [the TODO](../../../docs/todo.md) and must be resolved before
claiming the full step's independence and storage-permutation checks.
Step 2's source encodes reference-walker outputs through `geometry.wf`.
The walker still performs every potentially saturating layout operation in
its original order, then stores exact wider parent differences. Placement
accumulates block origins once in flow order, keeping normal and effective
visual displacement separate, and applies column maps after accumulation.
Table alignment uses a content offset; a later compatibility positioning
pass materializes it before writing positioned children. A suffix move
changes only root entries in owner-relative storage when the numeric guard
proves the corresponding i32 additions exact, otherwise it keeps the
reference per-entry translation.

Steps 1 and 2 are the committed, compiled input supplied by the primary
agent. This implementation session supplies no additional dump, edit-prefix,
mutation or timing results; the primary agent runs validation in CI. Context-wide conversion
snapshots and the legacy fragment, split-line, natural and baseline state
remain compatibility work, not evidence of bounded edits; their replacement
with owner-local boundary outputs is recorded in the TODO. A lineless
paragraph retains the reference walker's unplaced scratch-origin behavior.
Step 3 now has the nested order representation and small virtual-event
adapters in flex, grid, table and columns. Its node summaries carry direct
counts, virtual event spans and first/last line-bearing entry handles;
nonempty margin transfers are populated by the step-4 source described below.
The builder collects direct entries in per-owner pending lists, then seals
each closed block and context into a balanced sequence in bulk. Typed block, paragraph and
child-context payload pools remain context-owned migration storage: the
paged entries contain handles into those pools, not the heavy payloads.
Physical typed-payload ownership remains open; step 5 supplies local route publication;
this source does not claim the complete step-3 ownership contract or M2
locality. Step 4 has an unvalidated ordinary-path implementation; its wider
dirty frontier and parallel scatter remain incomplete. Step 5 now has the source-only neutral splice described below; compilation,
identity, mutations and performance remain for CI. Step 6 remains unimplemented. Each step lands with
the full-build and incremental paths producing exactly the same dump,
including fragment order; a partial performance improvement never permits
a rendering difference. Line ranges are estimates of changed/added source
and focused checks, overlap between steps, and are not measured velocity.
No Whitefoot implementation change is included in the estimates.

| Step | Change and estimated lines touched | Check | Required falsifier |
|---|---|---|---|
| 1. Decouple identity from order | 700–1,100: `module.wfm`, `build`, `prep`, `structure`, `style_update`, `update`. Paragraph-owned pieces; stable owner/entry/context slots and routes; explicit order queries. Keep the current flat walker through an adapter; temporary vectors are not locality evidence. | Full dumps on all three pages and five focused layout pages; every prefix of existing text, font-size and block scripts compared with a fresh full build; repeated insert/delete before one sibling, plus a style edit and a text edit after each splice. | Retain numeric-slot ancestry, omit one text/use route repair, or let a newly appended paragraph use numeric predecessor order. Each must fail its focused case. Mutation of the last piece's range must fail a multi-piece paragraph case. |
| 2. Make geometry owner-relative | 900–1,500: `flow`, `update`, `columns`, `table`, `flex`, `grid`, `inline`, `module.wfm`, dump checks. Centralize normal/visual/context coordinate conversions; table content origin; anchored fragments/naturals/baselines. Initially stack through the full reference walker and convert resolved outputs. | Byte-identical full dumps, seq and par, including negative margins, relative ancestors, positioned/fixed children, table alignment, split inlines and columns. Add extreme/saturated coordinate cases. Measure placement separately. | Omit one ancestor origin, apply relative displacement twice, shift every nested table descendant, apply a column map before accumulation, or reassociate a saturating sum. Each case must produce a dump difference. |
| 3. Replace flat ownership with nested indexed sequences | 1,250–2,050: `build`, `flow`, `prep`, `structure`, `style_update`, `update`, `module.wfm`; small item-iterator adapters in `flex`, `grid`, `table`, `columns`. Owner-local balanced order/summary indexes and paged payload slots; stop retaining or rebuilding the flat stream on successful edits. | Same full-build outputs and edit-prefix checks; assert live unit totals against an independent walk; inspect the compiler's certified loops for sibling preparation and child layout. Full-build time is compared with the frozen M1/base source under the same pin, not just with step 2. | Reverse equal-order siblings, treat a float as block-contained, or leave a retained flat-stream rebuild on the edit path. Rendering catches the first two; physical-work counts and a wide/deep synthetic scaling case catch the last. |
| 4. Block outputs and bounded propagation | 800–1,400: `flow`, `update`, `columns` consumers and focused cases. Ordinary margin transfer composition/prefix; float influence replay; dirty-child frontier; translate only direct clean siblings. Font-size and text edits use this path before a structural splice does. | Generate small margin/empty/marker configurations with varied entering struts and compare the transfer composition with the original entry machine; independently retain Chromium rectangle cases. Every edit remains byte-identical to a fresh build. Report W, A, L, D, F and actual visits, including cached index nodes used to recover prefix state; no earlier entry leaf may be consumed. | Collapse a strut to one scalar, clear an incoming float at a block boundary, stop on equal height with a changed baseline, omit an ancestor-height update, or scan an unchanged descendant. Geometry cases catch state mistakes; instrumented earlier-leaf and unchanged-descendant sentinels catch extra work. |
| 5. Publish a flow-range splice | Source-only implementation (the original 650–1,100-line estimate was exceeded): `structure`, `build`, routing/marking helpers, `oracle/layout/edit`, focused scripts. Private subtree build, local sequence swap, seam validation, targeted routing and count deltas, insert and removal. | Three pages' block scripts, `research/investigations/incremental-layout/scripts/block-case.html` and its `.edits` script, focused counter / `:nth-*` / `+` / `~` / float / collapsing-margin / split-inline cases. Compare every prefix with full build and serialized-source reparse, seq and par. Assert an explained refusal leaves the retained tree untouched. After each removal edit, issue another text/font-size edit to catch stale routes. | Disable the structural style frontier, fail to restack P's later siblings, skip a route tombstone/generation check after slot reuse, ignore outgoing counter state, or publish before seam validation. Each mutation must fail; an unexplained `inc refused` is not success. |
| 6. End-to-end sizing and deletion of migration support | 150–300: oracle counts, harness/reporting, research/tree record; remove the temporary flat adapter and this probe when replaced. | E2's whole-edit costs at seq and par-4 on the same E1 captures/scripts; no fallback in a claimed local block edit, all current edit kinds no worse than M1, final full style/layout within M2's 5% envelope. Pair before/after same-source toggles for the specific optimization being attributed, and record the pin and driver hashes. | Force one whole-context route rebuild, disable subtree skipping, or omit placement when claiming paint cost. The locality/performance checks must reject these. If the measured distributions cannot distinguish a change, collect a longer paired sample rather than claim a win. |

At every step, the fresh-build comparator bypasses retained state. Also
keep the pre-migration driver as an output comparator until the full build
has migrated, and use existing Chromium/WPT-derived layout cases to avoid
a bug shared by the new full and incremental paths. A reparse comparison
must map live NodeIds to the dump's document-order owners, as the current
oracle does; node allocation identities themselves need not match.

A sequential implementation of the float-free prefix is useful only as a
reference, not the recommended final algorithm. Greedy line breaking does
have a prior-line-end dependency inside each paragraph. Counters/quotes
carry scope state in tree order. Floats carry exclusions and floor state.
Unresolved margin edges carry struts until a separator; combining their
transfer summaries is order-sensitive but associative, so that order does
not require a linear span. Parent height and intrinsic size depend on
child outputs. Sequence publication depends on completing its replacement.
No allocator counter, shared shape cache, whole-context scan or serial
scatter is justified by those semantic dependencies.

### Step-4 source and remaining acceptance work

`renderer/layout/boundary.wf` is the maintained home of boundary publication
and update helpers; `boundary_checks.wf` is its oracle check implementation,
removed when the algebra coverage moves to a dedicated layout test entry.
The edit script is test data consumed by the existing incremental driver,
removed when equivalent generated edit cases replace it.

The boundary module publishes block sizes, width inputs, baseline
handles and offsets, separate positive/negative margin extrema, through
state and barriers. Float exports retain first/last stable entry handles
and a count in the enclosing BFC; `reads_floats` is conservative and never
cleared at a lexical block close. They are routing metadata for reference
replay, not a claimed constant-sized exclusion transfer. The full-build
stacking algorithm is unchanged; a post-pass seeds the semantic summaries.

The new update attempt precedes `geometry_reference`. It handles one
marked paragraph or one marked child context per context, recursively, and
at most one restyled block on that entry's ancestor chain. Thus text edits
and single-paragraph font-size edits can propagate across block and context
boundaries. Each ancestor uses the same width/growth checks as the old path,
through a shared snapshot. AVL summary repair and a suffix down-sweep consume
metadata before the changed entry without opening its payload. Sibling
translation changes direct origins only. Size, baseline handles/offsets,
margin transfer, intrinsic contributions and float metadata all participate
in convergence. A baseline change does not stop merely because height agrees.

The ordinary path requires stable widths and struts, existing solid content,
no incoming/exported floats in that BFC, no clearance, marker-created line,
height clamp, positioned dependency, intrinsic demand, column map or spanning
context fragments. Arithmetic uses a conservative absolute-travel bound,
including exposed baselines. Unsupported state takes the reference path,
without changing rendering requirements. After a successful ordinary edit,
`boundary_dirty` records that legacy naturals are stale: the next refusal
forces full reference stacking before republishing them. A refusal after
rebreaking also forces full stacking, so the newly computed paragraph height
cannot be mistaken for the old height by a partial replay.

The existing incremental oracle calls `boundary_transfer_check` before edit
scripts. It compares both association orders with sequential calls to the
reference margin operations for four transfer shapes, triples in document
order, and nine entering struts; it also checks that equal height does not
hide a changed baseline. This is algebra coverage, not proof of all nested
Open/Close classifications. `boundary-case.edits`, applied to the existing
`incremental-layout/scripts/block-case.html`, adds a same-line-height font
change and text wrapping changes before and after it. Its inline-block
containers expose the last paragraph's baseline to a parent line; that parent
still takes the atomic-inline fallback, so this is a geometry test rather
than a zero-fallback locality case. The script's NodeIds
must be confirmed with the driver's `nodes` mode in CI; they have not been
executed in this source-edit session. The temporary `oracles-m2` workflow
selects this script against `block-case.html` in both builds and validates
every edit with `inctime.py --check`; it has not been dispatched here.
The timing parser accepts the complete new counter suffix, retains it in
count comparisons and reports its ranges. Entirely legacy logs remain
readable; a partial suffix is invalid.

`put_counts` appends `boundary_entries`, `boundary_blocks`,
`boundary_indexes`, `boundary_fallbacks` and `boundary_reason` to the existing
update counts. These count boundary-path payload-opening operations and AVL
metadata lookups, including repeated opens. They do not count each scalar
load, slot-page directory step, preparation work or the reference replay.
Any fallback therefore disqualifies a whole-edit locality claim. The counters
are aggregated only through contexts actually updated, not by scanning
unchanged contexts or summing stale counters.

Remaining work is recorded in `docs/todo.md`: multiple dirty entries per
context, compiler-proved independent suffix output/scatter, complete physical
visit sentinels and reference-path counters, full nested margin/empty/marker
classification cases, and exact seq/par edit-prefix validation. No build,
test, lint, measurement or mutation was run in this implementation session.
The algebra source is wired, but no acceptance result or performance result
is claimed. No pin or design decision changed.

A separate read-only review inspected the working diff from
`8069a471c473c7e44b687c1a2d04035016862394`, the boundary decision and directly
affected consumers. It found repeated uncounted helper reads (replaced by
shared block snapshots), missing child propagation (added for flow children),
non-flow child updates bypassing reset/fallback setup (now refused before
calling `update_child`), and the timing parser's rejection of appended
counters (updated). It also identified the remaining multi-entry,
parallel-scatter, nested-case and sentinel gaps recorded above. The review
ran no compiler or checks and did not establish byte identity. The final
non-flow guard, parser and workflow wiring are local repairs inspected by the
implementer, not a new validation run.

#### Step-4 mutations for CI

Apply each separately and restore it before the next run:

1. **Collapse a strut to one scalar.** In `sequence.wf:join_output`, after
   composing the leading pair, assign their sum to `leading_positive` and
   assign zero to `leading_negative`. `boundary_transfer_check` must reject
   the mixed-sign entering-state cases; a zero net strut must not erase its
   extrema before a later join.
2. **Clear an incoming float at a block boundary.** In `flow.wf:stack_flow`'s
   `Close` arm, replace `stack.floats` with an empty `Slots<Exclusion>` and
   reset `stack.reach`. Use a float inside a zero-height unframed block whose
   float extends beside the following paragraph, with a later `clear: both`.
   The independent Chromium case must change; resetting only
   `BlockOutput.reads_floats` is masked by the additional BFC-wide refusal and
   is not a sufficient falsifier of float preservation.
3. **Stop on equal height with a changed baseline.** In
   `propagate_boundary`, replace `band(same, size_same)` with `size_same`.
   Apply the font-size class from `boundary-case.edits` under its fixed
   line-height: a containing context that reads the descendant baseline must
   differ from a fresh build. Separately, remove the baseline comparisons
   from `same_transfer`; the wired algebra check must reject that mutation.
4. **Omit an ancestor-height update.** Remove the assignment to
   `context^.blocks.inner[at].height` in `propagate_boundary`, keeping the
   cached output update. The wrapping text insertion must differ from the
   fresh-build ancestor rectangle even when the sibling origins agree.
5. **Scan an unchanged descendant.** In `apply_boundary_move`'s `Open` arm,
   descend the moved block's `entries` and read a descendant through the
   counted payload-opening path. On otherwise identical wide/deep fixtures,
   the visit assertion must reject growth with the unchanged subtree size.
   A new uninstrumented read is outside the present counters; the required
   earlier-leaf/descendant sentinels remain an explicit acceptance gap.

For mutation 5, widen that function's counter effect from
`writes(context.boundary_visits.blocks)` to `writes(context.boundary_visits)`
and insert this inside its existing guarded block branch before the origin
write. This intentionally scans direct contents of an unchanged sibling:

```text
let extra_handles = box_slots_new::<EntryHandle>(capacity: 0_u64);
let extra_root = context^.blocks.inner[at].entries.root;
later_handles(sequence: &context^.blocks.inner[at].entries, root: extra_root, skip: 0_u64, owner: b, handles: &extra_handles, visits: &context^.boundary_visits);
let extra_count = extra_handles.inner.len;
for (extra_at in 0_u64..extra_count) {
  let extra_slot = extra_handles.inner[extra_at].slot;
  let extra_payload = sequence_payload(sequence: &context^.blocks.inner[at].entries, slot: extra_slot);
  set context^.boundary_visits.entries = context^.boundary_visits.entries +sat 1_u64;
}
```

### Step-5 source and CI falsifiers

The source adds `structure_splice` before Q86's `structure_changed`. The
private builder consumes the owning block's content width, style and
containing-height input. Its synthetic counter checkpoint is explicitly
inexact: a later non-neutral edit rebuilds from the nearest exact enclosing
checkpoint, retaining Q86's outgoing-state refusal. Neutrality records
counter writes/readers, implicit list increments and quote operations during
normal construction; it is not inferred from the inserted tag name.

`splice_inputs` resolves stable owner and seam routes without retained
mutation. `splice_sequence_plan` composes cached prefix/suffix transfers,
including both extrema of the preceding margin edge. It validates the
step-4 ordinary path and privately computes each direct later sibling's
translation. `splice_routes` constructs the inserted subtree's text/use
and context-directory records; removal collects only the removed subtree.
Publication appends private payloads to the unchanged context-wide stable
pools, calls the existing AVL `insert_before`/`remove`, publishes/tombstones
only affected routes, settles the owner and propagates step-4 boundaries.
Live context/paragraph totals use added-minus-removed counts. Removed
paragraph/context slots remain tombstones and are excluded from preparation,
placement and independent live-count comparisons.

All recoverable construction and capacity failures precede publication.
The mutable AVL and route helpers allocate their pages during the commit
phase after validation; this is not a persistent tree prepared and swapped
in one pointer write. Whitefoot allocation exhaustion is not a recoverable
layout result. CI must establish the proof obligations before this source
is described as an executable transaction.

The oracle emits `structure path N splice S reason R` in addition to its
existing structural and physical boundary counters. `inctime.py --check`
requires one row for every structural operation, with `S=1` exactly when
`R=0`. Historical timing and filtered reparse logs may omit the entire set;
a partial set is always invalid. Timing compares these fields across runs.
The page harness checks raw logs before comparing filtered hashes, and its
path summary reads those raw logs. The reason namespace is separate from
step 4's `boundary_reason`:

| R | Meaning and disposition |
|---|---|
| 0 | Published local splice. |
| 1 | Missing/ambiguous stable owner or route, including a `display:contents` parent. |
| 2 | Non-flow or multi-column context on the owner path. |
| 3 | Mixed inline seam, non-block inserted range, split inline state or mismatched direct owner. |
| 4 | Generated/pseudo references were not retained by the style delta. |
| 5 | Counter/quote read or write dependency, including implicit list state. |
| 6 | The structural style frontier also changes retained content; Q86 consumes the whole frontier. |
| 7 | Unsupported step-4 boundary: float/intrinsic/definite-height dependency, through block, changed exposed strut, numeric bound or unavailable cached geometry. |
| 8 | Preflighted entry, payload or DOM storage ceiling. |
| 9 | Private construction returned a layout error, including route/path construction ceilings; emitted by the oracle. |

Every nonzero result takes the existing reconstruction route and is not
local-splice evidence. The fast path currently requires unchanged exposed
leading/trailing margin pairs and solid old/new owner outputs; accepting a
complete-block seam alone does not establish these further conditions.
An ordinary inserted block may contain independently laid-out child
contexts, but a container-specific algorithm on the propagation path falls
back. No E1 or whole-M2 completion is claimed.

Dependencies: private paragraph preparation and child layout retain their
independent counted loops. Each later sibling computes its origin from
cached prefixes independently (duplicated logarithmic metadata reads),
and its diagnostic totals use a balanced reduction. The builder's source
walk retains its existing document-order dependency for paragraph assembly
and state validation. Stable-slot allocation, route installation and direct
payload writes belong to ordered publication; enclosing boundary propagation
follows the ancestor chain. Context-wide pool growth and indirect publication
scatter remain Q122/CI limitations, not a claim of certified parallel writes.

`block-case.html` is unchanged. The script preserves its original operations
and adds repeated insertion before old sibling 17 (new blocks 53 and 55),
removal of new block 53 and pre-existing block 15, then insertions 57 and 59
and removals 57 and 55. Each new structural operation is followed by text
insert/delete and font-size class add/remove on retained block 17/text 18
and a surviving new block/text. Before inserting 57, block 55 gets a 37px
bottom margin: the new paragraph's top margin must collapse with that edge.
These appended ordinary `.box` operations are expected to report reason 0;
every prefix must match fresh full layout, including live totals. Earlier
mixed-inline, counter and constrained-owner operations retain explained
fallbacks; Q86 may still refuse a changed outgoing counter state. CI must
check those reasons explicitly rather than require every old negative case
to be a local splice. The script's source NodeIds include all original
whitespace nodes and the doctype; no original NodeId is renumbered. A final
negative case adds a zero-margin paragraph 61/text 62 after mixed box 20's
inline run, then removes it, with the same retained/new probes. Both
structural operations must report reason 3; zero margins prevent the
exposed-strut guard from masking the seam-validation mutation.

Apply each mutation separately and restore the source afterwards. These are
specified falsifiers, **not run results**; all compilation and mutation runs
belong to the primary agent's CI:

1. **Skip seam validation.** In `splice_sequence_plan`, replace both exact
   calls `let reason = splice_boundary(context: context, item: preceding_item, removing: no, visits: visits);`
   and `let reason = splice_boundary(context: context, item: following_item, removing: no, visits: visits);`
   with `let reason = 0_u32;`. In a mixed-inline flow with an existing
   line-bearing paragraph on either side, insertion must remain a reason-3
   fallback, never reason 0. Use the final `.mixed-seam` append case as well as the existing
   before-span case: the latter can refuse earlier at route resolution and
   by itself does not falsify this guard. Compare every
   prefix with fresh layout; assert the path independently of dump equality.
2. **Omit the preceding collapsing edge.** In `splice_sequence.wf:splice_edge`,
   replace `let gap = wide_positive +sat wide_negative;` with
   `let gap = 0_i64;`. The insertion after block 55's 37px bottom margin
   must differ from fresh layout. Include a mixed-sign margin fixture so
   preserving only a net scalar cannot pass accidentally.
3. **Do not translate later siblings.** In `splice_boundary.wf:splice_move`,
   replace `let move_y = new_y -sat old_y;` with `let move_y = 0_i64;`.
   Both repeated insertions before old sibling 17 must differ from fresh
   layout at that sibling, without translating its descendants individually.
4. **Do not update live counts.** In `structure_splice`, replace
   `set layout^.paragraphs = kept_paragraphs +sat added_paragraphs;` with
   `set layout^.paragraphs = kept_paragraphs;`. Insertions must fail the
   oracle's incremental-versus-full live-count comparison even if hashes
   agree. Separately replace
   `let kept_paragraphs = layout^.paragraphs -sat lost_paragraphs;` with
   `let kept_paragraphs = layout^.paragraphs;`; removals must fail it.
5. **Lose new text routes.** In `publish_splice_routes`, replace
   `route_write::<TextUnit>(table: &layout^.text_units, at: at, value: text);`
   with `route_write::<TextUnit>(table: &layout^.text_units, at: at, value: absent_text);`.
   The first new-text edit after insertion must refuse or differ. Keep
   `absent_text` as the already declared tombstone value in this function.
6. **Treat a synthetic checkpoint as exact.** In `forget_splice_points`,
   replace `set context^.walk_exact = False();` with
   `set context^.walk_exact = True();`. Insert a neutral context after an
   earlier counter setter, then introduce a counter reader inside it;
   comparison with a full rebuild must catch the invented counter input.
7. **Drop a path record.** Remove one `structure path` row from an otherwise
   complete new-format log, or change a reason-0 row to `splice 0 reason 0`.
   `inctime.py --check` must reject the malformed/incomplete log.

The temporary `falsify-m2` workflow also runs each oracle shell assertion
group inside a non-final loop iteration with one violated condition at a
time (difference, excess refusals, or no successful edits), requiring the
shell to exit with failure. Its path-log fixtures test one missing row, all
missing rows, and both contradictory splice/reason combinations, with an
otherwise complete two-edit insertion/removal log and a passing restored log.

`splice-route-case.edits` uses `block-case.html` and probes text 44 immediately
after inserting block 43 before old sibling 17, before any retained-text or
style edit can cause resynchronization. `checkpoint-case.html` puts a counter
reset of `list-item` to 777 on the section and makes its direct paragraph children
independent contexts. `checkpoint-case.sh` resolves the section and new-node
IDs from the driver's node listing, then inserts a neutral context and a
list-item paragraph with an inside decimal marker inside it. This introduces
a counter reader without changing pseudo membership or generated-text
references, which the style/Q86 fallback currently refuses independently.
A genuine enclosing checkpoint produces marker 778 and leaves the root
context's outgoing state unchanged: the section's counter goes out of scope
when the body closes. The synthetic empty checkpoint instead constructs 1
and cannot reproduce the genuine incoming/outgoing state. Three digits also
distinguish their geometry even with tabular digits. Both fixtures
are consumed by the step-5 oracle job and the mutation matrix. These are
validation fixtures, not measured results.

The refusal audit at `63bc857` found two expected Q86 refusals, edits 5 and 6:
inserting/removing paragraph 47 inside counter box 27 changes the outgoing
`c` value consumed by the following box. The other ten refusals were edits
14, 23, 32, 41, 51, 60, 69, 78, 88 and 97, all `C 17 splice-font`. They
were class-frontier defects: `class_restyle` promoted every stale traversal
to a full request, and `rebuild_all` returned a structural refusal instead
of computing on stable slots. The resulting full resynchronization restored
new text routes before the original script probed texts 54, 56, 58, 60 and
62. No second route publisher runs on a successful local splice.

The original new-text probes belong to inserted blocks 53/text 54,
55/text 56, 57/text 58 and 59/text 60, all locally spliced. Block 61/text 62
instead comes from the mixed-inline reason-3 reconstruction. Removals probe
whichever of those new blocks survives. The immediate text fixture detects
`lose-text-route` at edit 2 with `inc DIFF` in the first mutation run
[37554096137](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37554096137).
That run did not pass overall: its first counter fixture added a pseudo,
which the unmutated Q86 path independently refused. The list-marker fixture
replaces that setup without relaxing its required incremental success.

The focused job in
[37553901105](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37553901105)
fails at the repaired refusal assertion (12 versus 2). Its raw page logs
show that ecma262 block edits 1–20 and html5 block edits 1–60 all reach
`structure_splice` and take reason-7 reconstruction, with no refused edit
or dump mismatch. Their missing summaries were a harness defect: `inc`
read filtered hash output after `edit` had removed diagnostic rows.
These are fallback results, not E2 local-splice evidence. A diagnostic CI
copy assigns distinct nonzero codes to the existing context guard exits
without changing which route executes. Run
[37556900282](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37556900282)
at `0fe4965` reports diagnostic reason 77 for every ecma262 edit 1–20 and
every html5 edit 1–60. That exit is exactly
`output.travel >= 67108864_i64` in `splice_context_ready`; earlier guards
for context kind, columns, geometry, definite height, intrinsic/dirty state,
splits/fragments and nonordinary/through output have passed at the rejecting
context. Both insertions and removals therefore attempt the splice and take
the Q86 reconstruction path under public reason 7. None is an incremental
refusal or dump mismatch.

At `0fe4965` the fixed bound was the admission condition for unsaturated
ordinary transfer arithmetic, including baseline excursions. Crossing its conservative
sum does not demonstrate actual coordinate overflow, nor does this trace
show that all subsequent checks would pass if it were relaxed. Removing or
raising it without a replacement exactness argument would weaken a safety
condition. That revision retained these 80 fallbacks. The
[origin-aware certificate](#origin-aware-ordinary-arithmetic-certificate)
replaces that numeric condition; its page runs must independently establish
the unchanged E2 zero-fallback criterion. No claim of local
page block edits or step-6 acceptance follows from identity alone.

The repair reuses `visit_child` and the same class reach subject keys for
stable-slot traversals, resolving only selected NodeIds through the existing
order map. DOM links supply enumeration dependencies; inherited computation
keeps the existing depth frontier. The public `RestyleSet` already permits
stable slots in any order, so no interface or representation changes.
The stable-slot destination is initialized to its known size before mapping,
so each selected NodeId writes a distinct output index; window construction
alone requires sequential length updates. The completion review caught and
removed an unnecessary shared append from that mapping. It also caught a
mutation-harness early exit that rejected the expected boundary assertion;
the handler now accepts that specific diagnostic, keeps unrelated driver
failures fatal, and exercises both outcomes plus successful execution in CI.
The existing preorder path remains valid until the first structural edit.
`splice-style-case.edits` checks descendant, following-sibling and
following-sibling-descendant reaches across insertion and removal. The
`stale-class-frontier` mutation restores the stale-traversal promotion and
must make these probes refuse. The focused oracle at `c3b29cd` in
[37557227954](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37557227954)
passes all three added fixtures and leaves only block-case edits 5 and 6
refused. The counter fixture's first edit is a local splice; its second
correctly reconstructs from an exact enclosing checkpoint (reason 5) and
matches the full rebuild. The gate at `5b2298b` passes in
[37557293310](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37557293310).
The check-machinery job in
[37557293309](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37557293309)
detects all eight oracle-assertion violations, four malformed path logs, and
both expected and unrelated driver failures, with passing restored inputs.
The synthetic-checkpoint job in that mutation run detects edit 2 as
`inc refused` instead of the baseline's `inc same`: the invented empty
incoming counter state fails Q86's outgoing-state equality. This is the
counter-sensitive failure the fixture requires, before any wrong layout can
publish. The temporary `style refusal` diagnostic used to locate the ten class
failures is removed after that audit: it was not part of the raw-log grammar
and made the class mutation stop before checking its actual refused edit.
The restored diagnostic-free oracle makes the class fixture fail on
`edit 2: expected inc same, got refused`. Final mutation run
[37558813498](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37558813498)
at `b13fac3` passes all 17 mutations and the check-machinery job. Its direct
new-text probe fails at edit 2 with `inc DIFF`; the original block-case now
also detects the missing text route with four differences, because class
resynchronization no longer repairs it. Its synthetic checkpoint reader
fails at edit 2 with `inc refused`; both fixtures pass unmutated in the same
jobs. The gate also passes at that revision in
[37558813441](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37558813441).
Full oracle run
[37557227954](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37557227954)
at `c3b29cd` passes full-build dumps against the base, all six edit kinds on
both pages in seq/par, all three added fixtures in both builds, and the
existing case checks. Block-case has 100 matching edits, zero differences
and exactly two refusals in each build. Page block edits have 20/20 and
60/60 matching results and zero refusals in both builds, while still taking
the reason-7 fallback described above. Changes from that runtime revision
to `b13fac3` only repair the workflow's handler-probe extraction, retire
temporary class-refusal output and record evidence; renderer/style and
layout behavior are unchanged. Final mutation and gate runs validate that
retirement without repeating the full oracle.

The separate read-only GPT-6 completion review covered `49c138a..20521be`
and the then-dirty fixtures, checklist groups A/D/C/T/R/M/V and design checks
G1–G3/DC1–DC4, with limited follow-ups through `b13fac3` and the page audit.
It read changed artifacts, direct consumers and pipeline/layout/style nodes,
and inspected actual CI logs without compiling or rerunning suites. Its
findings are fixed: expected boundary-assertion exits count as mutation
detection while unrelated errors remain fatal; stable-slot mapping writes
disjoint indices; the handler probe extracts complete physical lines; and
temporary class diagnostics no longer mask the actual refused-edit check.
That review deferred the arithmetic fallback limit; the later
[origin-aware certificate](#origin-aware-ordinary-arithmetic-certificate)
addresses it without changing the earlier audit results.
No design decision, module interface, Whitefoot pin or submodule changed, and
no new Whitefoot gap was demonstrated. The task prohibits PR edits, so this
research record and the completion report carry its review/evidence record.

CI must additionally exercise `:nth-*`, `+` and `~` retained style changes
(reason 6), exact-checkpoint counter/quote refusals, removal of a pre-existing
child context, saturation/float/fragment fallbacks, and independent seq/par
identity. Source review cannot certify effect rows, OP-4 bounds after pool
mutation, AVL slot invariants, loop parallelism or mutation effectiveness.
Boundary visits cover checked splice index reads and AVL repair but remain
step-4 counters, not an allocation or whole-builder census; fallback attempts
and route-page visits require fuller instrumentation before locality claims.
The maintained TODO carries those limits and the full-build route-cost risk.

### Full-build regression repair

The question is whether removing repeated nested rank descent, incremental
AVL construction and per-entry ancestor summary repair restores the full-build
envelope without changing event order, stable payload identities, AVL validity
or boundary behavior. The owner selected transient walk materialization, bulk
construction, field-narrow index access and one bottom-up semantic reduction
after each reference walk. Reject the repair if html5 or ecma262 full layout
exceeds step 2 by more than 5% in either sequential or four-worker mode, or if
dumps or incremental identity differ. Compare the same source/pin/settings
before and after with interleaved runs and a twin of the baseline as the noise
control; the supplied best-of-three results motivate the repair but do not
establish acceptance.

The owner's i9-14900K measurements, `layout/run.sh time html5`, best of three,
seconds per run, isolate the remaining summary cost:

| Source | Boxes, sequential | Layout, sequential | Layout, four workers |
| --- | ---: | ---: | ---: |
| Step 2, `0e2a0931f630f156bf99bcc9596d37acea787ca8` | 0.070 | 0.630 | 0.297 |
| First repair, `2084e34be7cbf57318c4228312dbcf5a6ba9cd3e` | 0.110 | 1.370 | 1.060 |
| First repair without full-build `publish_boundaries` | — | 1.270 | 0.970 |
| Also without both `stack_flow` calls to `record_event_lines` | — | 0.700 | 0.373 |

The same supplied sequential profile attributes 29.7% self time to
`__memmove_avx_unaligned_erms`, versus 0.9% at step 2; `boundary_set` is 4.8%,
`slot_read` 3.0%, `fill_flow` 1.7%, `join_output` 1.5%, `slot_write` 1.0%,
and allocation/free about 8%. Compiler version and other settings were not
included with these observations. Source inspection confirms repeated whole
node copies through page directories and ancestor repair in the line-summary
writer and semantic publisher; it does not independently attribute machine
instructions. These ablations remove required behavior and are diagnostic
variants, not acceptable implementations.

The second repair (`a0d2a05`, run 37515789411 in
[runs/full-14900k.txt](runs/full-14900k.txt))
reduced html5 layout to 0.7267 s sequential / 0.4033 s with four workers,
against step 2's 0.6333 / 0.2967 s; ecma262 was 0.7100 / 0.4067 s against
0.5833 / 0.2733 s. Boxes remained 0.1133 and 0.1167 s sequential, against
0.0667 and 0.0767 s. The supplied next profile puts memmove at 1.5%,
`fill_flow` at 2.6%, `store_reduction` at 0.7%, and allocation/free/unlink/
consolidation at about 15% versus step 2's 12%. These are supplied observations,
not new measurements or proof that any individual allocation causes the gap.

The next source repair starts from `2a630a0`. Its comparison and rejection
criterion remain those above. The dependency choices are:

- Re-materializing at each walker and borrowing one immutable pass slice
  have the same topology dependencies. The latter removes repeated work
  without ordering independent contexts or retaining a cache. `lay_out_context`
  owns the array for a flow/flex/grid layout, `update_flow` creates it only
  after the bounded boundary path refuses, and `place_context` owns a separate
  dump-publication pass. The space, stacking, positioning, split-fragment,
  intrinsic, flex/grid and column walkers borrow slices. `materialize_flow`
  now uses a filled Array rather than incrementing a Slots length for each
  event. Cached weights still partition left, nested and right event ranges.
- A query from a parent has no child pass to borrow. `intrinsic_content`
  materializes for such a query after its skip and table/replaced dispatches;
  `intrinsic_sizes` reaches it only after cache and specified-width checks.
  Queries made by `used_width` instead reuse the active pass. Children keep
  their own independent queries. `table_first_baseline` queries a cell after
  its layout has returned and therefore owns its buffer; `position_out_with`
  similarly starts a cell positioning pass after the table finalizes its
  dimensions. These, plus the three pass owners above, are the remaining
  materialization sites. The bounded boundary path allocates none: an ordinary
  root transfer excludes Out entries, so its `finish_in_place` call can pass
  an empty stack slice without dropping positioning work.
- Initial four-slot leaves plus boxed binary directory nodes and one
  owner-sized leaf have the same stable-slot identity and no sibling data
  dependency. An initial owner-sized leaf removes directory allocation and
  makes its payload copy and transfer publication single counted loops.
  `finish_sequence` allocates two final pages at the smallest power of two
  covering the owner's count (minimum four), and `bulk_nodes` writes links
  directly into the final node page. There is no topology scratch array.
  This trades fewer allocations/descent steps for padding: up to nearly
  twice the live slots instead of rounding only to four. Initialization
  bytes and peak memory must be measured alongside allocation count.
  Incremental growth wraps the existing leaf, then adds small directory
  leaves; it never copies or enlarges an existing page.
- `pending` is now an optional builder list, allocated at first append and
  released to None at sealing. Empty owners and sealed owners allocate no
  pending box. Close publishes only its completed pending event span to its
  parent. That source-order dependency remains; sealing has none and moves
  after the document walk into `finish_tree_sequences`, with counted disjoint
  block-owner and child-context loops. Both full build and replacement-tree
  publication call it. All closed pending lists now survive until this phase,
  so peak construction scratch lifetime grows; no retained scratch survives
  publication.
- Owner-sized pages let `reduce_sequence` read topology/payload slots directly,
  eliminating `SequenceInput`, `sequence_inputs` and `reduce_owner` snapshots,
  including allocations inside nested reductions. After later directory
  growth these reads follow the directory; that full reference fallback may
  do more lookup work than a dense snapshot, while the bounded edit path is
  unchanged. `prepare_boundary_entry` computes paragraph/child/float/Out
  transfers in a counted event loop before reduction. Each iteration reads
  completed geometry and writes only its own result; no iteration allocates.
  The remaining reduction preserves left-own-right association and block
  lifting after nested results, then publishes pages and blocks independently.

For a nonempty owner with n direct entries, let P = ceil(n/4), F be the
number of allocated binary forks in the old bulk directory, and G be the
number of positive-capacity pending buffers (initial four plus doublings).
The source-level Box allocation estimate for construction is:

| Storage | Before | After |
| --- | ---: | ---: |
| Initial empty pending and replacement empty pending | 2 | 0 |
| Positive-capacity pending buffers | G | G |
| Topology scratch | 1 | 0 |
| Payload and metadata leaves | 2P | 2 |
| Boxed directory children | 4F | 0 |
| Total per direct entry | (3 + G + 2P + 4F) / n | (G + 2) / n |

Examples: n=1 is 6 -> 3 allocations per entry; n=4 is 1.5 -> 0.75;
n=8 is 13/8 -> 4/8; n=16 is 26/16 -> 5/16. An empty owner falls from
one pending allocation to zero. Counts include replaced buffers, not just
live allocations, and exclude payload construction common to both versions.
Step 2 had no owner sequence allocations. Full reference reduction additionally
removes one snapshot allocation per owner, even for empty owners; the one
context-wide reduction array and three rank arrays remain. These are source
estimates under Whitefoot STOR-1's one-allocation Box rule, not allocator
measurements. The language source inspected is
[the specified Whitefoot revision](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/spec/kernel-spec.md).

Changed loop dependencies and remaining limits:

| Operation | Dependency / compiler-facing form |
| --- | --- |
| `finish_sequence` capacity selection | Scalar doubling recurrence, bounded by the slot ceiling; no layout ordering is introduced. |
| `finish_sequence` payload publication | Counted index at writes only final payload[at], reading pending[at]. |
| `finish_tree_sequences` block and child loops | Each iteration mutates one owned block sequence or one child subtree; parents' pending weights are already complete. |
| `publish_boundaries` leaf preparation | Counted event index at reads geometry and writes only reduced[at]. |
| `store_reduction` page publication | Existing counted cell loop now spans the initial owner-sized leaf; every cell writes only its own/total fields. Block publication remains a counted owner loop. |
| `bulk_nodes` | Disjoint recursive median halves; parent height/event totals wait on both. |
| `fill_flow` | Disjoint recursive event slices, with no semantic sibling dependency; Array construction removes the former append-length chain. |
| `reduce_sequence` | Disjoint recursive left/nested/right slices; only ordered transfer joins and enclosing block lifting wait on child outputs. |
| Slice-threaded reference walkers | Existing order and arithmetic are unchanged: margin/float/stack state, positioned ancestor stacks, stable flex/grid collection, column units and fragment output order supply the dependencies. |

The last three recursive kernels have **not** been converted to counted
branch scheduling. Their disjoint source effects do not establish that the
current --par backend overlaps recursive calls. The counted leaf preparation,
owner sealing and wider page loops expose additional independent work, but
full four-worker recovery remains unverified and this part of the requested
repair is incomplete. A counted branch representation must avoid allocating
one result box per tree node or imposing global depth barriers; neither is
introduced just to obtain a parallel loop. No compiler limitation is claimed
without a compile/lowering result.

In the profile's terms, sharing a common four-walker flow pass can remove
three of its four fills, but intrinsic queries, table queries and dump passes
remain separate. Even eliminating all reported `fill_flow` self time would
save only about 19 ms of the supplied 0.727 s html5 run; 75% of that is about
14 ms, an upper-bound illustration, not a predicted measured gain. The
allocation changes target the much larger construction gap and the 15%
allocator bucket, with no supported per-allocation time estimate. Direct page
indexing also removes directory traversal from the initial materialization
and reduction; its effect is not separately identified by the flat profile.
Larger-page initialization can offset those savings. No source-only result
establishes the acceptance envelope.

Boundary transfers, Close's preceding-float flag, geometry arithmetic,
identity and oracle counter meanings remain unchanged. Metadata-opening
counters still count repeated physical reads; page-directory steps and
reference work remain excluded. The semantic publication continues to keep
outputs in payloads during stacking, with one later reduction; narrower
reads do not change the step-4 boundary contract.

No compilation, gate, dump comparison, edit validation, falsifier execution
or measurement accompanies this source edit. The primary agent owns CI.
All exact-string falsifier anchors remain in place. Proof-sensitive changes
are slice/effect threading, the borrowed optional pending list while disjoint
sequence fields are published, bounds after recursive reduction writes,
initial large leaves followed by wrapped directory growth, and the empty
slice on the ordinary boundary-only finish path. Review found and repaired
unnecessary materialization for skipped intrinsic/table/replaced paths and an
unsupported tuple-if initializer. No pin, submodule or Whitefoot gap changed.
The proposed layout decision is updated; no approval-log or readiness claim
is made.

### Step-3 source falsifiers for CI

These are mutations to apply separately and revert, not executed results.
The primary agent compiles and runs the ordinary layout/edit checks.

1. In `flex.wf:flex_collect`, replace the materialized event read at `k` with a guarded read
   at `flow_count -sat 1_u64 -sat k` (split the two arithmetic operations
   into separate let initializers).
   Give several siblings the same nonzero `order` so stable sorting is
   exercised. Their per-owner fragment positions must differ from the
   unchanged source. Apply the equivalent mutation to `grid_collect` for
   the grid adapter. Entry order, not payload slot order, is the input to
   the existing stable sorts.
2. In `flow.wf:stack_flow`'s `Close(block: b)` arm, insert
   `set stack.floats = box_slots_new::<Exclusion>(capacity: 0_u64);`,
   `set stack.float_floor = 0_i32;` and `set stack.reach = 0_i32;`.
   A float inside one non-BFC block extending beside a paragraph in the
   next block must lose its exclusion under the mutation. Compare with the
   independent float fixture/reference rectangles, including clearance.
3. Replace a walk's borrowed `events^[k]` read with a call to
   `flow_event(context: context, at: k)`, keeping the ordinary rank guard.
   This restores a nested root descent per rank. Correctness comparisons
   need not reject it; the same-source full-build timing comparison must
   distinguish its cost. Separately, moving `materialize_flow` into the
   rank loop must be rejected by allocation/index-visit growth. Temporary
   arrays on the reference path do not demonstrate bounded edit locality.

The current compatibility geometry and routing paths already contain
whole-context work. The third falsifier therefore needs counters at the
sequence operations, not the historical aggregate restack counters. The
typed-payload migration and step-4/5 work remain necessary before a complete
edit can satisfy the final locality criterion.

## Risks and owner questions

Q104, Q109, Q114 A and Q115 A are approved directions.
The descriptions below distinguish the approved contract from implementation
and measurement still needed.

- **Q114 A — stable local slots and block boundary outputs (approved).**
  This gives owned, independently writable siblings and removes every
  insertion-sensitive rank from retained identity. A local array costs
  O(s_parent) copies, including earlier handles, and cannot pass the existing
  M2 locality criterion. Recommend a balanced local order/summary index
  with stable leaves and paged payload slots; its extra allocations and
  lookup cost must meet the full-build envelope. A flat global order index
  needs a second local-child index for the same dependency graph. Lazy
  range origins remain conditional on measured wide-suffix cost.
  Retain the ordinary margin transfer/prefix contract so a convenience
  left-to-right loop does not become the architectural dependency chain.
  Boundary outputs differ from the refused arbitrary stacking snapshots:
  they are the block's output contract, needed to decide whether its
  descendants may be skipped at all. Their exact minimal fields and
  compiler proof must be established in step 4, not assumed from this
  sizing run.
- **Q115 A — a neutral complete-block seam first (approved).** Counter
  changes, split-inline boundary changes and container-wide algorithms
  keep the existing correct rebuild route. The alternative is to implement
  every builder state transition before the first local block splice,
  delaying the E1 milestone. Require zero such fallbacks on the timed E1
  block scripts before claiming M2; extend a seam actually required by
  those scripts in the same milestone. Do not label a font-size/text
  regression as an acceptable consequence of this structural fast path.
- **Wide siblings.** Parent-relative offsets remove descendant writes,
  not direct sibling writes. Recommendation: measure sums on the actual
  edit paths, not only the median block fanout; if they dominate 115 us,
  add a block-local range-translation/prefix tree with lazy origins. It
  must preserve independent sibling work and publish a range offset
  without touching each descendant. This is a reopening condition, not a
  claim that a summary tree is already needed on every block.
- **Float reach and collapsed edges.** Recommendation: equal normalized
  full boundary state, not equal box height, is the skip condition. Count
  F explicitly. A float that changes line breaks across thousands of
  entries can legitimately defeat locality; report that separately from
  a suffix that merely translates.
- **Construction and routing can dominate after stacking is fixed.**
  Recommendation: no page-sized `count_tree`, `record_tree`, order copy,
  `retained_outside`, `changed_outside` scan, or growing dense array on a
  successful splice. Validate the style frontier from steps 1–2 and only
  the changed builder references. Stable state alone does not achieve
  this; the call sites must consume the frontier.
- **Proof and allocation costs.** Recommendation: prototype one owned
  nested preparation loop and one local splice against the pinned
  specification before spreading types through all consumers. Use
  `Box<Slots<...>>` ownership and local slot contracts from the maintained
  programs, not an unproved scatter or a language workaround. Record an
  actual compiler limitation as a minimal Whitefoot gap if found. This
  investigation compiles only the diagnostic, not the proposed types.
- **Coordinate overflow and placement cost.** Recommendation: checked
  wide differences with the compatibility fallback, and one accumulating
  traversal for placement. Random hit tests may pay O(D); paint/hit testing
  are not benchmarked here. Do not treat them as free because E1 excludes
  placement.
- **Full-build regression and memory.** Recommendation: separately
  measure allocation count, peak live bytes, paragraph preparation, stack,
  and placement before accepting the nested representation. Per-block
  indexes/pages/outputs may cost more than today's packed arrays. A's dependency
  advantage does not establish its sequential speed or M2's 5% condition.
- **Reported work.** Recommendation: implement the physical counters in
  step 4 and retain historical columns only for comparison. The existing
  discrepancy is recorded in `docs/todo.md`; it must not be used to pass a
  locality gate.

## Validation and remaining uncertainty

Renderer validation used the source at
`e468312e7c53f826a2d2ea85e0c257c9d42736fe`; subsequent changes only refine
this research record and its governing design prose. The provided compiler
and checked-out/pinned Whitefoot revision agreed, and the compiler's
SHA-256 remained
`a589b9ad3adf7e6508f03ada519e5d5565399e0e420472d2e4d05bd405fdda7f`.
No Whitefoot source or pin changed.

- The task's exact compiler invocation, from `renderer/` under its supplied
  lock/guard with the shared cache and `--fragments function`, compiled the
  new `layout_oracle` entry successfully. The only executable additions
  are the removable census/timing probe, its declared interface/dependency,
  and the oracle mode dispatch; ordinary layout functions are unchanged.
- A hand-derived fixture with body containing `div(p(A),p(B))` and
  `div(p(C))`, plus the normal html/head/title structure, has 2 contexts,
  16 flow entries, 6 non-BFC blocks and 3 paragraphs. Every reported owner,
  parent, direct count, depth, open index and subtree span matched the
  hand enumeration. Its checker rejected 111 individually changed fields,
  missing/extra rows and changed row order. This expectation comes from
  the fixture structure, not the census algorithm's own output.
- The probe passed its stack-height, baseline, flow-end and every-rectangle
  comparison on the fixture, `flow-cases.html` and every real-page
  repetition. Ten temporary source faults each compiled and made the
  fixture exit 2: a wrong stack height, baseline or flow end; wrong placed
  count, kind, owner, x, y, width or height. The source was restored and
  rebuilt. A failed temporary float-operator spelling was corrected before
  counting the four coordinate mutations as tested.
- Ordinary `dump 1` output is byte-identical to the supplied pre-probe
  driver on the five existing flow/table/flex/grid/column case pages and
  all three real pages: 1,249,058 / 12,538,869 / 19,024,863 bytes for
  apollo11/html5/ecma262. This is preservation evidence, not an independent
  claim of CSS correctness or a reconstruction of that supplied driver's
  exact build provenance.
- From the worktree root,
  `sh research/investigations/incremental-layout/run.sh inc seq PAGE block`
  passed 60/60 apollo11 edits, 60/60 html5 and 20/20 ecma262, with zero
  differences or refusals. The sampled apollo11 run took 19.06 s wall;
  html5/ecma262 then took 121.22 / 59.07 s. These runs validate unchanged
  existing edit behavior; they do not exercise the proposed splice.
- `make -o compiler check WHITEFOOTC=<provided pinned compiler>
  CACHE=<shared cache>` passed renderer module checks, the DOM self-test
  and design lint in 9.51 s. The compiler prerequisite was deliberately
  satisfied by the supplied, hash-verified pinned binary; this is not a
  claim that the compiler was rebuilt or that an unmodified `make check`
  ran. Design lint's 21 tests passed. The exact final prose is also checked
  separately with `make design-lint` and `git diff --check`.

The separate read-only reviewer (GPT-6.1-sol; A, D, C, R, M and V, including
G1–G3 and DC1–DC4; T not applicable) checked the diff from `7ee4411`, source
callers, tree ancestors and actual logs without rerunning green suites.
The review exposed stale whole-context/whole-walk/preorder clauses and the
old O(1)-per-ancestor claim; the governing prose now distinguishes the
reference path from M2 and uses the direct-sibling bound. It also exposed
that copying a whole local sequence still touches earlier entries. The
recommendation now requires the stable local order/summary index before a
splice can pass the unchanged locality criterion. Initial vectors are
explicitly migration-only. The reviewer confirmed that resolution of the
locality finding. The original measurement binary had not been preserved;
a confirmation run now has the preserved, directly verified hash above.
Final block-script and gate results completed after the review and are
reported directly here.

The design-tree rewording this research proposed for
`design/pipeline/layout.md` was not merged: it described the unimplemented
M2 representation as decided, and the tree changes with the implementation
it governs. Found along the way: the misleading all-context-relative `Fragment`
comment is corrected; misleading `UpdateCounts` physical-work semantics
are recorded in `docs/todo.md` with impact, proposed counters and reopening
condition. No language gap was demonstrated or filed. The proposed nested
types, distinct-slot traversal, summary coverage, full-build allocation
cost, parallel speed and actual E1 splice latency remain unverified.
Q114 A, Q104, Q109 and Q115 A are approved inputs. Step-3 source has not been compiled or executed in this
implementation session; the primary agent owns CI validation. No approval log entry or readiness claim is made. Delivery is a
local branch commit only, as requested; there is no push or PR update.

### Q128 semantic extension: constituent inventory and proof boundary

Q128 B (owner direction, 2026-10-07) selects positioned/atomic propagation,
then flex-item propagation, keeping the unchanged X5 scripts and the
zero-fallback gate. At the initial inventory, the question was whether these two
extensions covered the actual page owners. The discriminating observation is
an inventory of the individual retained transfers in the first edited
owner's context, rather than its maximum refusal reason. A contributor
outside those two extensions rejects the premise that removing just their
guards can establish the page acceptance claim. This is a scope
investigation, not a timing comparison.

A temporary read-only inventory at `4154340` ran in hosted CI
[37578072578](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37578072578),
using the unchanged pin and pinned page bytes. Its `step5-diagnostics`
artifact contains `html5.semantic.raw`, `ecma262.semantic.raw` and the node
listings. Each `semantic` row is five integers: record kind, context slot,
payload slot, style NodeId, detail. Kinds are 1 context kind, 2 nonordinary
block's maximum barrier, 3 paragraph atomic count, 4 positioned child's
position, and 5 nonordinary block's position. These diagnostic rows are not
part of the oracle protocol. The normal near-limit check correctly rejected
them; the inventory step passed, but the run as a whole failed. The temporary
API and printing were subsequently removed, without weakening the parser.

The first html5 splice owner is `dd` NodeId 217487, block slot 25203 in flow
context slot 1 (the `html` element). Its own transfer has **barrier 1**, not
5. Its ancestor `dl` NodeId 217457 has barrier 5; body NodeId 47 also has
barrier 5. The context inventory reports:

| Contributor | Observed records |
| --- | ---: |
| Nonordinary block transfers with maximum barrier 1 | 17,631 |
| Maximum barrier 2 | 2,642 |
| Maximum barrier 3 | 5,088 |
| Maximum barrier 5 | 2,626 |
| Relative-positioned blocks among those records | 698 |
| Paragraphs with atomic inlines | 1,053 |
| Absolute-positioned children | 531 |
| Fixed-positioned children | 0 |

These are retained payload records, including ancestors whose summaries
inherit a descendant's barrier, not counts of independent layout defects.
The absolute children belong to `pre` (217), `li` (202), `dl` (102), `p` (6)
and `span` (4) styles; the relative blocks are `h4` (394), `li` (202) and
`dl` (102). Atomic paragraphs predominantly belong to `dt` (1,029), with
23 `p` and one `div`. Thus stage 1 also has to account for relative block
origins; “positioned” is not solely an out-of-flow classification.

`join_output` takes the maximum barrier, so 5 conceals 1–3. In
`stack_flow`, `boundary_floats` becomes true after the first float and never
expires; each later block stores it as `output.reads_floats`. This explains
why the distant `dd` is marked even when the earlier float may no longer
reach it. It is not evidence that a float actually changes that edit's
geometry. The stylesheet also has `dt { clear:left }`, and eight edited
parent sites are list items. The existing blanket marker check rejects
those with retained outside markers independently of whether the marker
creates a line; their individual marker predicates were not inventoried.

The first ecma262 target is in flow context slot 91, element NodeId 21173.
Its inventory has 20,146 nonordinary block records with maximum barrier 3,
7,689 with barrier 5, 2,447 relative heading blocks, and 2,149 atomic
paragraphs. Therefore crossing body's flex context alone does not make
that target ordinary. The first edit on each page still matched its full
rebuild: html5 reported `splice 0 reason 7`, ecma262 `splice 0 reason 2`.
These are one-edit diagnostic observations, not the required final all-edit
acceptance run.

#### Positioned and atomic argument, with its missing premise

If the in-flow transfer is valid and its old/new arithmetic is certified,
the owner and its direct later siblings settle first. An unchanged
paragraph's atomic child uses the same laid-out local offset and therefore
moves once with the paragraph. A moved enclosing block already moves all
its local descendants; their anchors must not also receive that delta.

For an out-of-flow child, compare its containing-block position and size,
percentage bases and inset resolution inputs. With those inputs unchanged,
an auto axis follows its changed static position, while a definite inset
axis keeps the coordinate that the existing positioning algorithm computes.
Fixed explicit offsets use the viewport, not the moved ancestor. A changed
containing-block size goes through the existing incremental child-layout
path, followed by positioning. Nested contexts keep their internal local
origins and move through one anchor. Relative positioning also needs its
visual excursion in the arithmetic certificate: translating an already
saturated visual coordinate is not equivalent to recomputing it.

Independent anchor translations have no inter-anchor dependency. Their
inputs wait for owner geometry and containing-block sizes, and publication
waits for those independent results. Re-laying out a resized child precedes
positioning that reads its new dimensions. These are the necessary orders;
there is no justified descendant-by-descendant translation or sibling order.

The initial inventory lacked a valid transfer premise through the earlier-
float, clearance and barrier-3 contributors. Barrier 3 conflates height
constraints and marker state; that inventory did not record their individual
predicates. The later constituent inventory and Q129 arguments below resolve
those dependencies. Accepting `barriers == 5` alone cannot establish them,
and positioned propagation alone cannot remove the owner's barrier 1.

#### Flex argument and the actual nested page paths

An unchanged flex setup fixes the axes, ordering, available main/cross
space and percentage bases. Each item's hypothetical main size depends on
its flex basis, intrinsic contribution or natural layout, limits, margins
and frame. The container's line breaking and free-space distribution read
all those hypothetical sizes and flex factors. Final main sizes determine
which item interiors need layout; natural cross sizes and baselines then
determine line cross sizes and alignment; stretch can change an item's used
cross size and require its interior to be laid out again. Placement and the
container's baseline/size follow those results. Running the existing
`flex.wf` arithmetic in that order avoids changing its rounding or
saturation behavior.

Unchanged siblings can reuse retained preparation results when their styles,
content and setup inputs are unchanged. Their interiors can be retained
when their final used space is unchanged, even if their anchor moves. A
changed final main or cross size uses the existing incremental layout path.
Sibling layouts, including stretch layouts, are independent once their
sizes are known. Line membership and the freeze loop retain their algorithmic
dependencies; enclosing contexts wait on the container's new outputs.

The pinned ecmarkup CSS uses definite-width body flex with 33% and 66%
flex bases. Those percentages do not prohibit reuse when their width basis
is unchanged. Two script sites also cross an `emu-note` row flex container:
insertions before nodes 98185 and 123590, edit pairs 7–8 and 19–20.
Their result must propagate through the spec-container flow and then body
flex. A one-flex-ancestor cap or blanket percentage rejection would therefore
fail the required page workload. This bottom-up argument composes when each
container satisfies its input conditions. The implementation below reruns
line breaking and rejects reuse when a percentage basis changes; a context
outside the propagated input/output certificates retains explicit fallback.

The initial implementation obligations were to retain preparation and
pre-stretch results, invalidate intrinsic caches along the changed path,
and publish actual flex outputs while preserving the old output needed for
comparison. A stretched item's retained height is not its natural height.
The retained-input and actual-output sections below own the implemented
mechanisms and their validation requirements.

#### Q129: additional transfer scope

The two selected boundaries are necessary but insufficient. A local proof
for the masked float/clearance state needs to show that unchanged earlier
floats cannot reach any later natural position or flow end, in either the
old or proposed layout, and that later floats preserve their relative
geometry. Existing `restack_settles` states this condition, but its suffix
floor comes from flat `naturals` scratch; the local splice invalidates that
scratch. Before this extension, `SequenceOutput` did not retain that
minimum; the implemented summary certificate is argued below.

A seam-only test is unsound. If an unchanged left float ends at y=100 and
the seam is y=200, a later negative margin can put a `clear:left` block's
natural position at y=70. Inserting height 10 changes that natural position
to 80, but clearance still places it at 100. Uniform translation would put
it at 110. Both layouts have no active float at the seam.

The recommended additional stage would retain the required local float
reach and suffix-minimum evidence, preserve other barrier kinds separately,
and certify lined marker blocks only when the old/new line presence proves
that no synthetic marker line appears. Its additional falsifier must make
the negative-margin/clearance example fail when the cutoff is bypassed.
Independent summary preparation/reduction should retain the existing tree's
dependencies; prefix/suffix composition is ordered because float exclusions
and collapsing margins depend on preceding flow. The continuation authorizes this expansion of Q128 B and directs work to
proceed on Q129 A unless vetoed. The float/clearance certificate and its
later uniform-float extension below implement that direction.
The alternative is to retain counted reference replay for these contributors,
which preserves correctness but leaves the unchanged page zero-fallback gate
blocked. No gate or expected result has been relaxed.

The positioned and flex fixture pages and `splice-cases.py` are wired to
`oracles-m2` for full-rebuild identity, sequentially in step5 and in both
builds in the full job. Each case inserts/removes a block and edits retained,
inserted and dependent text around those operations. These establish fixture
coverage only; until the extensions and their mutations run, identity through
a counted fallback does not establish splice coverage or falsifier detection.


#### Flex retained-input argument (implementation contract)

The comparison is unchanged full flex layout versus an update that repeats
its container algorithm while retaining item preparation and pre-stretch
results. A difference in a fixture edit prefix or a page prefix rejects the
reuse contract. Mutations omit stretch layout, free-space recomputation and
line rebreaking independently; each must produce an observable difference.

Each child owns a preparation record keyed by the complete `FlexBox` setup
except the updating flag. The record contains the `FlexItem` before line
construction, including hypothetical size, natural size, factors, limits,
margins and baseline inputs. It is invalidated when content or a
layout-relevant style changes, before an update can clear that child's dirty
mark. A local splice invalidates the same record on its changed path.
Unchanged percentage bases are part of this setup equality; changed bases
cannot reuse preparation. This local ownership adds no order among siblings.

A second record retains the cross size and baseline from the final-main-size
layout *before stretch*, keyed by the complete requested Space. An unchanged
item may supply those numbers while its interior still holds a previous
stretched layout. Once the line cross size is known, the stretch pass
materializes exactly the Space that full layout would select, including
removing an old stretch when the new line no longer requests one. Interior
reuse requires equivalent used space and unchanged content/style. Keeping
only current stretched height would conflate two different algorithm inputs
and is rejected; replaying every item's interior introduces unnecessary work
without shortening a dependency.

The container still orders items, breaks wrapping lines, runs the free-space
freeze algorithm and resolves cross alignment on every update. Consequently
wrapping and nested flex containers need no distinct approximate algorithm.
Independent item preparations precede line construction; final item layouts
wait on targets; cross-line reduction waits on natural cross outputs;
independent stretch layouts wait on cross targets; container outputs follow
placement. An outer container waits on its changed child's outputs. These
are the existing algorithm's dependencies, with no new sibling chain.


#### Float and clearance transfer argument (first certificate)

Question: can the edited owner and each outward suffix be transferred while
all earlier float exclusions remain unchanged? Compare each insert/remove
prefix with a fresh layout, and bypass the cutoff on the negative-margin
clearance fixture. Identity failure rejects the certificate; a mutation
that remains undetected rejects the fixture. A seam-only height comparison
is expressly not the criterion.

Retain the minimum pre-clearance natural position and maximum float margin
bottom of each entry subtree, expressed relative to its sequence owner.
Independent leaves read the completed reference walk's natural positions;
a block lifts its interior minimum by its own normal offset and includes
its Open natural position. The balanced index reduces minima and maxima
without imposing sibling order. A translated direct entry shifts its two
bounds by the same delta, repairs the index, and leaves descendant-local
bounds unchanged. Empty minima/maxima keep explicit sentinel values.

This initial scope is extended by Uniform later-float translation below.
For the initial certificate, an affected suffix containing floats is refused.
All preceding floats therefore remain fixed. Before publication, accumulate
the preceding float maximum across the owner's ancestors, and require it
not to exceed the affected suffix minimum in either the retained or the
proposed position. Apply this at each outward boundary and to the flow end.
The suffix minimum includes every nested Open, paragraph and child natural
position, so a later negative margin that returns above the seam is covered.
If clearance currently raises an affected entry, its pre-clearance natural
position is less than the prefix reach and this certificate refuses it.
Inactive clearance leaves exactly the ordinary collapsing-margin transfer.

The owner seam must still have exact free-flow transfer arithmetic and
unchanged exposed struts. Growing ancestors must retain automatic height,
unchanged width inputs and line presence, and must pass the existing
height-growth predicate. An outside marker with a retained line creates no
synthetic line before or after the change; a marker-only owner is refused.
Unchanged constrained sibling interiors may translate, but an active size
constraint on the growing path is outside this first certificate. Prefix
geometry is retained; no claim that a maximum barrier code describes its
constituents is used. Later floats or an active constraint needed by the
pages would require extending this argument before admission.

The orders introduced are owner settlement before ancestor output, and a
changed entry's metadata before the index ancestors that read it. Prefix
queries, suffix queries and direct sibling motion calculations are
independent. Publication continues the existing distinct-slot scatter;
there is no descendant geometry walk. The arithmetic certificate includes
old and proposed travel and visual excursions before translation. Relative
block displacement is charged at its owning block. Positioned, atomic and
float anchors charge their owner-local normal and visual excursions plus
height. A constrained or otherwise non-free block additionally charges its
measured height, since its content transfer alone need not bound its used
size. Those per-block semantic exclusions and extra charges remain in
BlockOutput when a changed interior is lifted during later edits.


Intrinsic measurement must also preserve retained inputs: `intrinsic_flow`
previously wrote zero-basis horizontal margins into its live child contexts.
A reused item interior need not run layout to restore those fields. The
measurement now computes those same zero-basis contributions locally for
flow children, floats and atomic inlines. The added `flex-intrinsic-margin`
fixture holds final width constant while an edit forces an intrinsic query
and then edits text beside a percentage-margin atomic child. This repair
preserves the full intrinsic calculation and removes its unintended write;
the dedicated `flex-intrinsic-position` case below supplies behavioral
mutation detection, which remains a CI obligation.

#### Settling a flex ancestor after publication

The flex boundary cannot predict its final height and baseline from only the
edited flow's height delta: line membership, free space, natural cross sizes
and stretch jointly determine them. After publishing the already certified
local flow splice, recompute the clean flex ancestor with the existing flex
algorithm in update mode. Invalidate its own intrinsic contribution and
parent-item cache; each child's retained preparation and interior remain
subject to the input checks above. Stable child slots and routes are kept,
and no box-tree construction occurs.

Only this flex context crosses the reference-coordinate bridge. Its child
contexts retain their owned geometry and are laid out again only when the
algorithm requests another space or their contents changed. Preparation,
final-size and stretch passes return per-child work counts in independent
array slots; the reduction adds those counts, positioned-child work and the
container's own pass. It must not describe enclosing-flow replay as a local
splice: outward flow propagation consumes the actual flex output and must
pass its own transfer certificate. A failed post-flex certificate remains
an explicit counted refusal; the primary publication path owns recovery.
A nested flex chain repeats this argument one ancestor at a time.


#### Actual flex outputs and explicit post-publication refusal

A flex container's new size is known only after its algorithm has resolved
new item sizes and any changed interiors. Predicting it from the edited
item's height alone is unsound for wrapping and stretch. The local owner is
published first, then the flex container is recomputed, then enclosing flow
certificates consume its actual outputs. An enclosing flow whose certificate
passes translates only its direct suffix and ancestor boundary path.

Proposed operational contract Q130: if that actual-output certificate fails,
finish the affected container by its existing reference layout and report
structural refusal reason 10. The existing reconstruction caller then starts
from a complete, self-consistent layout of the current document; neutral
insertion preserves the exact enclosing walk checkpoint. Reasons 1–9 still
refuse before publication. This explicit refusal is excluded by the pages'
zero-fallback gate. It avoids either pretending a whole enclosing flow replay
is local or deep-copying retained subtrees solely to predict flex outputs.
Every reference completion is counted; no performance claim includes it.
The implementation recommendation proceeds within the approved stage-2
scope, and remains proposed until owner review of the branch.


#### Classifying the flex ancestor's enclosing entry

The actual-output transfer requires an in-flow child-context entry. A routed
flex context can instead be an atomic inline within a paragraph, a float,
or an absolutely positioned child. Applying the ordinary child boundary
update to those entries skips their owning paragraph, float placement or
positioning dependency. Admission therefore checks that every routed child
of a flow parent is the same live `Flow::Child` before private construction
or publication. The other classes explicitly refuse with reason 2.

The `flex-inline-owner`, `flex-float-owner` and `flex-positioned-owner`
fixtures each edit a paragraph inside a flex item, so the route first
crosses the flex container and then the enclosing non-Child entry. Each
fixture inserts and removes a block and follows both with text edits.
The expected structural path is `splice 0 reason 2`, with full-rebuild
identity throughout; this extends coverage beyond ordinary block flex
ancestors without claiming support for those additional dependencies.


Completion review repairs: equal-height transfer equality now includes all
certificate fields (`travel`, natural floor, float reach, known motion and
free-transfer eligibility), so a changed certificate propagates even when
geometry does not. The boundary self-check varies each field independently.
Post-flex flow propagation additionally requires unchanged child width and
horizontal margins; otherwise horizontal placement needs reference layout
and the explicit reason-10 path is used. The float fixtures put the edited
flow owner between the earlier float and later clearance, so the float-floor
mutation reaches the outward certificate rather than an unrelated refusal
of a float inside the edited sequence.


The completion review also found that a positioned child's arithmetic charge
must follow its settled height and anchor: percentage height in the growing
containing-block fixture changes that charge. After independent anchor
settlement, the splice refreshes each direct `Out` entry's charge and joins
its owner ancestry with zero geometric delta. Leaf certificate writes depend on settled anchors, and ancestor reductions
depend on their leaves. The current sequential AVL repairs retain the
existing deferred scatter limitation; they neither move siblings nor reopen
positioned descendants. This preserves the current-state certificate
for a subsequent edit.


An atomic inline's arithmetic charge uses its paragraph-relative normal and
visual offsets, plus its height, rather than its current owner-relative
anchor. Opposing vertical margins can leave a short line with a large atomic
offset; a preceding tall block can initially cancel that offset. Removing
the block destroys the cancellation, so retaining the old absolute anchor
charge is unsound. The paragraph-relative offsets do not change when the
paragraph translates. The ordinary flow certificate bounds the paragraph
origin, and the triangle inequality adds the absolute normal offset, the
absolute visual-minus-normal offset and absolute height to bound the atomic
normal, visual and bottom coordinates. Rebreaking the paragraph rebuilds
these offsets through the existing reference path; a direct paragraph move
changes its anchor only. No ordering among atomic anchor writes is added.


The old context-wide `definite_free` flag also includes out-of-flow
percentage heights. Stage 1 settles those boxes again after the containing
block grows, so that blanket refusal prevents its own supported case.
Retain a separate `flow_definite_free` pre-pass fact for blocks, in-flow
children and floats only. Those retained flow inputs must remain independent
of the context's definite-height basis; atomic inline spaces already use an
indefinite basis. Positioned inputs are excluded from this fact because
`position_one` recomputes them from the settled containing block. Structural
publication combines the old and inserted facts; local style updates that
introduce any height dependency conservatively invalidate it until the
reference pre-pass recomputes the fact. This changes admission, not the
meaning of the existing update cutoff's `definite_free` flag.


Publication also preserves `has_out` by combining retained and inserted
payloads with logical OR. Insertion can introduce the first positioned child
in a context, and final settlement must visit it against the retained
containing block. Retaining true after removal is conservative: the child
loop skips retired entries.


The retained-margin falsifier has a dedicated `flex-intrinsic-position`
case. A fixed-width item's automatic minimum invokes intrinsic measurement;
an absolute descendant has an explicit left inset and percentage left
margin. Text edits in the sibling item leave the first item's retained
margin state untouched before block removal. The rejected intrinsic side
effect would make the positioned descendant read a zero-basis margin at
removal (predicted x=7px instead of x=25px). Both structural operations must
use the local path, so a fallback cannot make this detection claim.
`positioned-generated-removal` first removes a pre-existing paragraph whose
class creates an absolute generated `::before`; `positioned-atomic-removal`
uses an inline-block generated child instead. Each then runs the ordinary
block insertion/removal and subsequent text edits. Only the removed paragraph
has the generating class, so inserted paragraphs remain reference-neutral.
Every structural operation requires a local splice, and every edit requires
full-rebuild identity including retained context/paragraph counts.
These cases do not runtime-verify publication of the first `has_out` state;
that logical-OR repair is source-reviewed only until a neutral insertion
exercises it.

CI [37598631869](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37598631869)
at `8918b891312a8e79e9e4709da8206839e3649049` exposed the original fixture's
incorrect insertion expectation: edit 73 took reason 4 and reported `inc refused`.
Removal 80 took the local path but reported `inc DIFF` despite byte-identical
printed geometry. The oracle also compares live context and paragraph counts;
source inspection found `retire_splice_payloads` omitted `Out` retirement.
The analogous atomic removal covers child contexts referenced by removed
paragraph marks. The replacement fixture removes a pre-existing generated child instead of
introducing unsupported pseudo membership. It preserves local-splice and
identity requirements and leaves the pages' zero-fallback gate unchanged.
The repaired baseline passed both removals in focused CI
[37602480329](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37602480329)
at `41085b1377803b9d62275b1f7e4278e055cd30bc`; mutation detection remains separate.
`no-positioned-retirement` omits only the `Out` retirement branch, while
`no-atomic-retirement` omits atomic-child retirement and count accumulation
before a removed paragraph is vacated. Each uses the strict semantic detector
and the local-path baseline assertions of these fixtures: only a valid
incremental identity/count difference detects the fault, never a path change
or unrelated failure. The original positioned fault has the run above;
the atomic fault has no original CI run, so its mutation supplies the required
before-repair observation. Both detections are required by the mutation acceptance gate below.

#### Uniform later-float translation

The successful constituent inventory at `5738c2d` in CI
[37597267424](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37597267424)
finds a later float in html5's outward body suffix. The earlier certificate
refuses it even though the old suffix minimum lies below neither earlier
float. The comparison is a local splice against the unchanged full walker;
any changed exclusion interaction or later negative-margin reentry rejects
the proposed extension.

Partition the context's float state at the structural seam. Floats in the
seam prefix and prefixes of its owner ancestors are stationary. Floats in
the affected suffixes translate by the same delta as the corresponding
flow. Compute the stationary reach once from those prefixes, excluding the
changed ancestor entry itself; passing its aggregate reach upward would
mistakenly classify its already moved later floats as stationary. Require
all direct in-flow suffix movements in the edited owner to share the final
delta. Every outward suffix already receives that same delta.

Certify both old and new suffix natural minima against the stationary reach,
including inserted content and all negative margins. The reach includes
both each float's margin bottom and margin top: the latter also bounds the
reference float-placement floor when negative margins invert an exclusion.
Stationary floats can then influence neither clearance, line width nor the
placement floor in the moved region. Interactions among moved floats and
moved flow preserve all relative coordinates and unchanged widths, so the
reference exclusion queries and placements produce exactly their old result
plus delta. The existing conservative root flow-end check still requires
old and new flow ends to lie beyond every old float reach; cases failing it
keep a counted refusal. This avoids claiming a new root-height clamp rule.

A Float entry contributes no cursor or margin change; it retains its float
exports and natural-position bound. Its anchor moves once, directly or by
its containing block. Arithmetic charges its normal offset from the
reference natural position, visual displacement, height and both vertical
margins. This offset is invariant under the certified common translation;
the flow certificate bounds the natural cursor separately. Independent
suffix movements need no ordering. The owner-chain certificates and the
existing shared AVL repairs keep their previously stated dependencies and
scatter limitation. Falsifiers omit a moved float anchor and ignore the
stationary suffix minimum; negative-margin fixtures must detect the latter.

The edited block itself must neither introduce nor remove float exports.
New or deleted exclusions change interactions rather than translating existing
ones, so a positive float count in the inserted or removed transfer retains
reason 9 until a separate argument covers it. The `transfer-later-float`
fixture keeps an earlier expired float stationary, then moves a later float
with opposing vertical margins and a following negatively margined clearance
block. Its insertion and removal must both take the local path and equal the
reference layout; omitting the direct float anchor movement must differ.


#### Q129 constituent inventory at 5738c2d

The temporary diagnostic driver at
`5738c2df6a9071555de2fad184b5b5893eaffd86` completed its first-edit inventory
in hosted CI [37597267424](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37597267424).
The `step5-diagnostics` artifact owns the evidence: `ecma262.semantic.raw`,
`html5.semantic.raw`, `inventory.semantic.legend`, `refusals.semantic.map`
and `x5/{ecma262,html5}.nodes`. Semantic records name their context, payload
slot, style NodeId and individual predicate; a maximum inherited barrier is
not counted as an independent constraint. Signed values below are decoded
layout units, not pixels.

| Inventoried owner context | Blocks | Own outside markers | Markers with first and last line handles | Own specified/minimum/maximum-height predicates |
| --- | ---: | ---: | ---: | ---: |
| ecma262 context 91, element 21173 | 33,032 | 15,577 | 15,577 | 0 / 0 / 0 |
| html5 context 1, element 2 | 27,987 | 4,235 | 4,235 | 0 / 0 / 0 |

The corresponding ancestor contexts contain no additional block payloads.
Of ecma262's 20,146 maximum-barrier-3 blocks, 15,485 have their own marker
and 4,661 inherit the barrier; another 92 own markers are masked by barrier
5. Of html5's 5,088 maximum-barrier-3 blocks, 4,168 have their own marker
and 920 inherit it; another 67 own markers are masked by barrier 5. These
observations resolve the constraint-versus-marker question for the retained
contexts inventoried, not for every nested context or future edit. The
unchanged first edit on each page matched its full rebuild.

The source-site diagnostic reports ecma262 refusal 1015 at
`splice.wf:243`, the `context.splits` guard in `splice_context_ready`.
Its selected owner is block 30832, list-item NodeId 390174, in context 91.
This run did not emit split contents or context fragments; their count,
open/close ranks and geometric relation to the edit remain unverified.
A follow-up inventory records those fields before any proposed admission.

Html5 reports refusal 1056 at `splice_boundary.wf:239`, the false result of
`outward_motion_ready`. Its owner chain is dd NodeId 217487 (block 25203),
dl NodeId 217457 (25196), div NodeId 208450 (23942), then body NodeId 47
(0). In body's direct suffix after that div, sibling div NodeId 264809
(block 26493) exports the later float img NodeId 264840 (child 1910,
flow rank 98475, margin bottom 68,752,020). The stationary earlier floats
are NodeId 51 (rank 4, bottom 7,488) and NodeId 199934 (rank 84007, bottom
58,990,350). The first edited seam before NodeId 217489 is rank 93746;
its old natural position and the minimum of all later retained naturals are
both 64,361,442. Neither earlier float reaches that old suffix, while the
context flow end 73,738,639 lies beyond all three old float bottoms.

The source at this revision refuses any suffix exporting a float, so that
body suffix necessarily violates its certificate if reached. The Boolean
trace does not distinguish an earlier unknown-motion rejection inside
`outward_motion_ready`; the observations establish the later-float dependency
and the old cutoff facts, not the complete proposed-layout certificate.
Uniform later-float movement remains subject to the separate argument and
falsifiers above. No expected result was weakened to obtain this inventory.


#### Private fragment publication boundary

The private subtree's root is an anonymous flow context whose blocks and
paragraphs are relocated into the retained owner. Its context-level split
records and empty-inline fragments have no publication mapping in this
splice. A complete outer block alone does not prove that its interior has no
such records. Refuse a private root with splits (reason 3) or context-level
fragments (reason 7) before publication; child contexts retain their own
fragment lists and remain covered by their whole-context ownership. This
closes an admission hole independently of admitting retained split groups.
The paragraph-and-text `B` driver cannot construct nested block-in-inline
content, so this boundary currently has source inspection rather than a
driver regression. Future fragment insertion support must publish the
corresponding ownership records before removing these guards.


#### Retained split-fragment admission investigation

Question: do the required structural seams occur after every dependency of
their contexts' split and empty-inline fragments, or must the splice update
spanning or later fragment endpoints? Compare the complete page edit sites
with split open/close ranks and fragment-source ownership from the reference
layout. A seam before any required dependency rejects an unchanged-prefix
admission argument for that seam; it does not justify omitting the fragment.

The unchanged-prefix candidate needs more than `split.close < seam`: the
reference fragment builder reads the event immediately after each run's last
close to decide whether to emit an empty trailing rectangle. Require that
event too to remain before the seam. Every split endpoint, predecessor
selector, inter-run gap and first-line state is then unchanged. Empty-inline
fragments also need their source paragraphs retained in that prefix. A
cached exclusive bound over these dependencies would admit suffix edits
without scanning unaffected fragment geometry; their raw compatibility ranks
would remain valid because the event insertion/removal occurs after them.
An edit inside an enclosing independent Child changes no parent event count
but still needs the same dependency test against that Child's rank.

If a required seam fails this comparison, stable endpoint ownership and
local dependency queries are needed: an edit may change inter-run joining,
the `sibling_above` selector, adjacent inline marks, or the pending margin
that determines `Split.line`. Translating a cached rectangle or line offset
without proving those inputs unchanged is insufficient. Removing an ancestor
of an endpoint must count as endpoint removal. The inventory, not a page
name or benchmark path, determines which general argument must be built.

The unchanged-prefix candidate was implemented and checked at `d981f914`.
Its bound preserved all dependencies before a seam, but the inventory below
rejects it as sufficient page coverage. It is superseded by stable endpoint
anchors and seam dependency summaries, argued below; its fixtures remain.

#### Ecma262 split-owner inventory at ebc9be94

CI [37601205755](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37601205755)
at `ebc9be94aa2929f5889f4a63e1abcf583b626a0e` records 4,196 splits and
11,694 context fragments in ecma262 context 91. The first insertion before
NodeId 390176 is at event rank 104306; 94 splits begin later. Eight of the
ten insertion sites have block ranks in this context's inventory, and every
one precedes later splits (94–1,406 records). The two nested-context sites
need their inner ranks separately. This rejects unchanged-prefix admission
as sufficient page coverage; it does not reject the prefix argument itself.

The splits belong to 3,708 inline owners: 2,298 `emu-alg`, 1,309
`emu-grammar` and 101 `emu-table`. There are 3,607 single-record owners and
101 owners with 2–28 records; all multiple-record owners are `emu-grammar`.
The 2,298 algorithm records open at `ol` block ranks, and the 1,797 grammar
records open at `emu-production` block ranks. For all 4,095 mapped ranges,
the close is after every descendant block's open, and no unrelated block
opens inside the range. The builder records the matching block Close;
the inventory lacks a complete event-kind list, so nesting checks alone do
not independently recover each exact closing rank. The 101 table records
have equal open/close ranks absent from the block map. The builder's
independent Child path creates this shape, and every such owner has one
DOM `figure` child; the inventory lacks that child's flow rank for a direct
payload-identity check.

Every split owner has exactly three context rectangles: a zero-height
leading rectangle, a positive-height main rectangle and a zero-height
trailing rectangle. This is measured output, not a proof that every owner's
records always join one run. All 101 multiple-record owners have a common
block parent for their production blocks; each adjacent record has
`next.open - previous.close == 2`. The intervening event's kind, line count,
inline marks and the `gap_lineless` predicate were not recorded. The first
seam's affected suffix includes 69 owners: 44 algorithms, 24 grammars and
one table. Two grammars have 14 and 13 records, so anchoring every affected
owner to one enclosed `ol` would omit required cases.

The first later algorithm owner 390330 wraps `ol` NodeId 390331 (block
30844), open 104356 and close 104396. Its leading and main y are 75994187,
main height 24192, and trailing y 76019531, in the renderer's 1/64px units.
The first later multiple-record grammar owner 409907 has leading/main y
79328603, main height 96058 and trailing y 79425813. Later table owner
413047 has leading/main y 79921257, main height 10056 and trailing y
79933041. Across all owners, the leading rectangle equals main top for
2,623 owners, lies 18px above it for 1,081, and 9px above for four. Trailing
rectangles lie 18px beyond main bottom for 2,419 owners, exactly at bottom
for 1,188, and 27px beyond for 101. Independent block top/bottom measurements
were not emitted; these values establish the observed rectangle relationships,
not a replacement argument for first-line and margin dependencies.

The other 570 context fragments are the context's own `div` NodeId 21173
box (y 0, height 81602022) and one zero-size rectangle at y 0 for each of
569 `span` owners, disjoint from split owners. Of those spans, 568 are
direct children of `emu-clause` and one of `emu-annex`; their nearest block
open ranks range from 289 to 110570. Paragraph source ranks were not emitted.
Only insertion owner 211274 contains such a span (211275), before its `h1`
and before the edited paragraph 211291. The other nine insertion owners
contain none. All are pre-existing nodes, so none belongs to the freshly
inserted plain paragraph removed by an X5 inverse edit. Their zero y must
not be assumed to translate with the containing block: `paragraph_position`
uses a lineless paragraph's retained resolved position, and
`empty_inline_fragments` reads that position. General endpoint ownership
must preserve the reference's distinction.

#### Stable split endpoints and anchored fragment extents

The next comparison replaces the insufficient prefix-only implementation.
It must admit an ordinary complete-block edit before retained split runs,
and inside a retained split head, while matching full layout after the edit
and subsequent text edits. A changed run count, rectangle, or later replay
rank rejects the proposal. Page inventory motivates the scope but never
selects renderer behavior.

A Split retains its stable Open(block) or Child(context) identity. Its raw
open/close ranks are reference-walker scratch. Before a reference replay,
weighted sequence prefixes and lexical ancestor Open events restore the
opening rank; a block's cached interior event count determines its closing
rank. This bridge is already a whole-context operation, and is never called
by the accepted local splice. Split.line retains an exact offset from its
head's normal origin, republished after each reference pass; no_line stays
a sentinel. Thus a later text edit cannot reuse a pre-insertion raw rank.

Context fragments have aligned anchor metadata; paragraph fragments keep
their existing representation. A split run's main fragment reads its first
head's visual top and last head's visual bottom, using the reference i32
saturating subtraction for height. Its leading empty fragment either reads
the first visual top, or the first normal origin plus the saved Split.line
offset, according to the selector the reference generator chose. Its
trailing empty fragment reads the last visual bottom plus the reference
resolved bottom margin. Each endpoint is a stable payload identity, not an
event rank. The existing placement walk resolves anchors from its block
origin snapshot. Independent endpoints and fragments require no ordering.
The reference bridge materializes these rectangles before replay, and the
reference generator republishes their anchors or line offsets afterwards.

The splice preserves the generator's topology and selectors with two local
certificates. Each entry summary counts split heads and empty-inline source
paragraphs in its owned flow; independent child interiors are excluded,
because their fragments belong to that child. Removing an entry with a
nonzero count is refused, including removal of an ancestor of a source.
Fresh root splits and context fragments remain refused. Secondly, summaries
retain the first and last non-transparent direct entry kind: ordinary solid
or split head. A Through ordinary entry, lineless paragraph, Float or Out is
transparent for this conservative query; a split head is never transparent.
The suffix's first kind must not be a split head. A prefix ending in a
split head requires a retained ordinary solid separator in that suffix.
This covers intervening whitespace without scanning earlier entries.
The existing neutral complete-block and immediate-boundary checks remain.

These guards preserve the split list, its order, and every gap that could
join two runs. A removed or inserted complete block cannot change a gap between joined
split heads: a following split head is refused, and a preceding split head
requires a retained ordinary separator after the seam. The same guards preserve the immediate inline-mark selectors and
sibling_above at affected heads. The first retained ordinary solid entry
absorbs the changed incoming margin strut; its unchanged trailing strut
makes each later split's pending-margin line translate with its normal
origin. A splice inside a split head leaves that head's entering edge and
external adjacency unchanged, and changes its anchored bottom by the new
height. Ancestor propagation preserves exposed struts, so the argument also
holds for an enclosing split head or independent Child. Float/clearance and
exact-arithmetic certificates still apply; anchors do not license a new
layout transfer. Lineless empty-inline fragments remain raw: the reference
reads their retained scratch position, not the translated owner origin.

The only new orders are existing source order for fragment publication and
lexical ancestry for weighted rank lookup. Summary reduction follows the
existing index dependency tree. Split/fragment bridge calculations write
independent temporary cells before independent publication, so metadata
reads do not create a sibling write chain. No local splice scans splits,
fragments, previous payloads or unchanged descendant geometry.

The earlier prefix/later fixtures remain identity checks; the later-split
path now requires local success because anchored extents implement it.
Additional fixtures cover multiple joined heads, editing inside a head,
independent Child heads, negative margins, and refused adjacent-head or
source-removal seams. Mutations suppress anchor resolution and split-rank
restoration separately; each must produce a valid identity difference.

The reference bridge lifetime is explicit: before legacy readers, anchored
rectangles and split rank/line scratch are materialized. On return to owned
geometry, every Split.line offset is republished from the actual reference
scratch. Independent fragment checks then require each anchor to reproduce
the actual raw rectangle exactly. Their balanced conjunction certifies the
context representation; a mismatch keeps raw fragments authoritative and
refuses structural anchor reuse with reason 3 until a later replay restores
agreement. This covers legacy translate/keep paths as well as regeneration,
without overriding a legitimate reference update. It is a representation
certificate, not an oracle or evidence of CSS correctness. A page mismatch
here must be investigated, never admitted by dropping the certificate.

A Through block does not reset the pending margin strut, so the conservative
neighbor summary skips it; a retained split head is never skipped. A solid
ordinary block's Close preserves sibling_above=true for the next head; a
lined paragraph resets the strut for the stored-line branch. Ancestor-head
incoming edges remain unchanged. Thus the argument does not assume that an
empty block absorbs margins.

The origin-only bridge inside `translate_after` deliberately does not
synchronize fragments or split lines. It runs during a legacy reference
pass, whose caller still owns `shift_split_lines` and `translate_fragments`.
Synchronizing there would apply delta twice. The shared conversion helpers
therefore take an explicit synchronization mode: external replay entry and
exit synchronize dependencies, while the internal suffix-origin conversion
preserves raw fragment/line state for its caller. A line-growing text edit
before a later split is the regression and must match the full rebuild.

The implemented fixtures are `transfer-multi-before`,
`transfer-multi-after`, `transfer-inside-head`, `transfer-child-head`,
`transfer-negative-head`, `transfer-adjacent-head` and
`transfer-source-removal`, plus `transfer-float-width-reentry` for a clear:none
paragraph whose width changes when its later negative margin crosses an
earlier float's bottom. Supported split cases include line-growing text
pairs before later fragment dependencies. The initial source-removal X
requires reason 3; subsequent neutral B/X pairs still require local success.
The temporary CI semantic inventory injection is removed after its evidence
was retained in the research record and CI artifacts.

`no-split-anchor` replaces the retired prefix-bound mutation because the
prefix representation has been superseded, not because its identity check
was relaxed. It disables only anchored placement. `stale-split-ranks` omits
only reference-bridge rank publication and must fail a following text edit.
Three additional equality mutations omit fragment_sources, fragment_first
or fragment_last from same_transfer; the oracle's independent changed-field
checks must reject each before edits. The fixture expectation machinery now
checks each initial-removal target kind and ownership and every required
path row, including the refused source removal. Its local Python smoke test
passed every deliberately wrong condition; renderer acceptance is recorded below.

Completion review R9 identified a missing `shift_split_lines` in the legacy
`update_in_place` translation path. The restack path already updates this
scratch, but the direct text path only moves payloads and raw rectangles.
`transfer-line-lifetime` grows a paragraph before a later split whose
leading empty rectangle reads Split.line, keeps that growth through the
next structural removal, and requires the removal to remain local. Paired
text restoration before the removal would conceal the stale offset. This
first attempt was submitted without the repair at `baad9efe`; it did not
fail, so that shape was not discriminating. A later attempt put the split
first inside an ordinary wrapper, but CI
[37611691658](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37611691658)
at `39de64c2b9556069b8baf6fc9d3e712ce787a95f` did not detect the mutation.
Adding 1px of top padding to resolve that wrapper before its split also
failed to detect it in CI
[37618315798](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37618315798)
at `9aba0456a8ac85cc6be89fd7fe14c175ada832d3`. The source explanation that
the original wrapper necessarily leaves `Split.line=no_line` omitted a
premise: the inline's own border and padding can create a line before the
head. That line both resolves the wrapper and can make `shows_owner` suppress
the leading split fragment, so resolving the wrapper alone does not establish
mode 2.

The discriminating CI inventory
[37624438479](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37624438479)
at `5dc92f9cf749cf00fe1e42fabd3e97358f43f60d` compared that framed inline
with a plain span inside the padded wrapper, each with and without exactly
the line-refresh call. Its `line-lifetime-inventory` artifact records modes,
raw lines and offsets, `update_in_place` calls and nonzero translations, and
certificate validity around the held text growth. The prior rejection
criterion was no mode-2 anchor, no nonzero-delta update, or no subsequent path
change when the refresh was omitted.

In context 29 (section NodeId 275), the framed span NodeId 284 emitted modes
3 and 4 only; its stale line offset therefore did not invalidate an anchor.
The plain span emitted modes 2, 3 and 4. At edit 251 both drivers increased
`update_in_place` calls from three to four and performed one translation of
15,360 layout units. The baseline line moved from 5,504 to 20,864 while its
normal-relative offset remained -768. The mutant retained line 5,504 and
published offset -16,128, despite raw leading-fragment y moving to 20,864.
Its representation certificate became false. Removal 252 stayed
`splice 1 reason 0` in the baseline and became `splice 0 reason 3` in the
mutant; both kept full-rebuild identity. These observations distinguish a
missing line refresh from an unexercised anchor or update path.

The maintained fixture uses that plain span and retains the padded wrapper,
held text growth and required local removal. Other split fixtures retain
framed inline coverage. Removing decoration here supplies the previously
missing line-based anchor; it does not relax identity or path expectations.
The temporary diagnostic job and its injected counters are removed after
this evidence. Normal oracle and mutation jobs run the uninstrumented source.
The implementation repair uses the existing split-line shift after
origin-only translation, excluding equal and ancestor opening ranks.
`no-split-line-refresh` removes exactly that call. Its detector validates
complete incremental identity/protocol first, then accepts a changed required
local path, because the representation certificate deliberately preserves
correct raw output when line metadata is stale. This mutation checks the
required optimization contract; the other semantic mutations still require
an actual identity difference (or their exact boundary assertion). The new
path mode has unchanged-output, missing/invalid expectation, duplicate and
malformed-protocol negative controls.

The focused page run at `b384564a01526c40dc808c758d178e0fad93003c`
[37608958517](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37608958517)
matched every block edit: html5 had 60 local splices, ecma262 had 16 local
splices and four reason-3 refusals (operations 3/4 and 9/10). Both remaining
seams follow a completed algorithm split, parent whitespace and a retained
ordinary paragraph. The preceding split closes at rank 91958 or 62345;
the corresponding seam is 91960 or 62347. This narrows the needed extension
to one-sided adjacency after a split, not a gap between joined heads.

The retained-separator condition above admits this shape. The retained
ordinary entry remains a non-lineless event separating runs, so adding or
removing the neutral block cannot change grouping. The preceding head's
immediate following event either survives (a lineless paragraph or another
transparent event), or changes between complete-block Open/Child events;
none reports the inline owner's following line. Exposing a lined paragraph
immediately is already refused by the existing boundary check. Its endpoint
and bottom margin survive, while later head inputs are protected by the
retained separator. The source-removal and following-head guards remain.
`transfer-adjacent-head` therefore strengthens its expectation to local
success; `transfer-before-head` removes a pre-existing separator before a
head and still requires reason 3, then checks local neutral edits after it.

Completion review R10 found that `inctime.py` still accepted only reasons
0–9 even though the implemented post-flex contract uses reason 10. A local
protocol sample demonstrated rejection before repair. The parser now accepts
`splice 0 reason 10`, and its machinery checks that reason 11 and
`splice 1 reason 10` remain invalid. The page gate still requires exactly
`splice 1 reason 0`; recognizing the documented fallback does not relax it.

`flex-outward-reentry` exercises reason 10 at runtime. An earlier float ends
at 100px, a 100px spacer precedes an auto-height column flex container, and
its two-line item initially has height 40px. A later paragraph's -30px
margin puts its natural top at 110px. Removing one pre-existing item
paragraph leaves 20px, so the actual flex output would put that later
paragraph at 90px, beside the float. Flex preflight cannot know its actual
output; the subsequent outward motion certificate must decline with reason
10, finish the reference layout and let the caller reconstruct correctly.
The initial removal requires that exact reason and every edit requires full
identity. The following ordinary B/X pair is identity coverage without a
forced path. Generator machinery includes initial-only path assertions,
independently of cases that assert both ordinary B/X paths.


#### Semantic extension acceptance

The focused `step5` job of CI
[37611691695](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37611691695)
at `39de64c2b9556069b8baf6fc9d3e712ce787a95f` passed. Its unchanged page
scripts produced 20 ecma262 and 60 html5 structural operations, all
`splice 1 reason 0` and all `inc same`. The positioned, flex and transfer
fixtures produced respectively 106, 169 and 274 edits, all `inc same`.
All 18 positioned structural operations spliced locally. The flex fixtures
include 18 local operations, two reason-7 arithmetic/transfer refusals, six
reason-2 ownership refusals and three reason-10 completed-reference results.
The transfer fixtures include 40 local operations, four reason-7 refusals and
two reason-3 fragment-source/topology refusals. These are sequential focused
observations, not a substitute for the complete acceptance matrix.

The full `[oracles]` gate requires all six X5 edit kinds on both pinned pages,
sequentially and in parallel, to match full rebuilds, together with the case
pages, full-build dumps, near-limit checks and the page zero-fallback gate.
The `[falsify]` gate requires every enabled mutation to be detected, including
positioned anchors, stretch, free-space recomputation, wrapping, float-floor
reentry and split-fragment lifetime. A correct baseline and a changed path
alone do not detect semantic mutations; the split-line-refresh optimization
contract is the explicitly argued exception above. CI run records and their
raw artifacts are the evidence for these gates. No renderer was compiled or
executed locally, and no timing or complete-M2 claim follows from this work.

## Q139: percentage heights whose basis the edit cannot change

Q139 A and Q145 C authorize this argument first: retain each percentage
height's basis, prove that no basis belongs to the edit's growing ancestor
chain, and otherwise refuse and count it. This section specifies that
certificate; it does not implement it or claim fixture, mutation or timing
results. The existing `flow_definite_free` refusal remains in the source.
The [layout decision](../../../design/pipeline/layout.md) owns the splice;
this argument extends its percentage-input premise without relaxing the
other Q128/Q129 certificates. Implementation and its corresponding live-tree
update belong to the later task.

The motivation is the [apollo11 diagnosis at its recorded branch revision](https://github.com/Ming-Research/Snowghost-wf/blob/2b122a48d5a1798cbe58232db44df56a4072ea40/research/investigations/structure-edits/apollo11-blocks.md#control-results-and-causal-limit):
54 of 60 block edits refused with structural reason 7; removing both
`html` and `body` percentage heights exposed reason 2 at grid ancestors.
Restoring either height restored reason 7. This establishes a masked
dependency, not a successful splice on the original page. Q140's grid scope
is independent; accepting this certificate must not report that grid work
as local. The other six edits had a retained-style refusal.

### Percentage inputs and the precise admission condition

For ordinary in-flow blocks, a percentage `height` uses the containing
block's content height; an indefinite content-dependent basis makes it
behave as `auto`. The root uses the initial containing block, whose size
comes from the viewport in this continuous-media scope. Percentage
`min-height` and `max-height` also use the containing height; CSS 2.1 treats
them as zero and no maximum respectively when that basis is indefinite.
These are different properties, not three spellings of `height:auto`.
See [CSS 2.1 containing blocks](https://www.w3.org/TR/CSS21/visudet.html#containing-block-details),
[height](https://www.w3.org/TR/CSS21/visudet.html#the-height-property), and
[minimum/maximum height](https://www.w3.org/TR/CSS21/visudet.html#min-max-heights).

[CSS Sizing 3's definition of definite size](https://www.w3.org/TR/css-sizing-3/#definite)
includes a percentage resolved solely from definite sizes; its
[nested-percentage example](https://www.w3.org/TR/css-sizing-3/#percentage-sizing)
therefore supplies the induction used below. Definite does not universally
mean independent of this edit: layout modes can provide a definite size
after layout, and the containing block of an absolutely positioned box is
definite for that box. The [cyclic-percentage rules](https://www.w3.org/TR/css-sizing-3/#cyclic-percentage-contribution)
also have layout-mode exceptions. This certificate covers ordinary block
resolution, not quirks-mode ancestor skipping, orthogonal writing modes,
table rules, or a flex/grid size merely because its last numeric value is
known. Unsupported provenance is a refusal, not an invented fixed basis.

Use these sets and records, based on layout identities rather than DOM
preorder numbers or the nearest formatting-context root:

- `A` is the complete enclosing block/context path from the changed owner
  through every boundary whose outputs must be settled. It includes fixed
  height ancestors: their content extent, baseline or float export may
  change even when their used height cannot.
- `G` is the conservative **growing chain** within `A`: every ancestor
  whose used content height may change, including shrinkage on removal and
  sizes not knowable before flex settlement. Remove an ancestor from `G`
  only after proving its used height content-independent from unchanged
  inputs. Do not remove it because its old and guessed new numbers match,
  because the current delta is zero, or because a clamp is active today.
  Thus `html` and `body` with a proven viewport-based `height:100%` belong
  to `A` but not `G`. A lexical ancestor test alone would reject the very
  case this extension is intended to admit.
- `R` is the retained in-flow geometry whose percentage inputs the splice
  proposes to reuse, including blocks, child contexts, floats, and their
  retained descendant dependency summaries in every affected scope.
  Earlier siblings count too. It is not just the edited parent's style.
  Out-of-flow boxes that Q128 actually settles again are excluded from
  this reuse claim; their inputs and arithmetic charges still follow Q128.
- For every percentage-bearing `height`, `min-height` and `max-height`
  read in `R`, retain the consumer identity and property, its actual
  containing-block identity (or explicit initial-containing-block token),
  axis and box edge, definite/indefinite/unknown resolution state, resolved
  basis value, and **provenance**. Provenance names the source of that value:
  viewport, content-independent specified size with its limits and box
  conversion, another resolved percentage with a link to its basis, or
  content/layout-dependent or unsupported. Record every intermediate
  containing block; flattening a chain to "viewport" would lose an
  intervening clamp or restyle. Percentage-bearing expressions, including
  supported length-plus-percentage expressions, count as reads.

Admission requires all the following premises before retained publication:

1. **Complete, current inputs.** The seam, style frontier and stable routes
   pass the existing checks. Every reused percentage read has a live basis
   record and unchanged resolution inputs: containing-block identity,
   property/expression, style and font inputs, width/box-sizing inputs,
   viewport and layout mode. Relevant invalidation or missing metadata is
   failure, not absence of a dependency. Retained nested contexts contribute
   summaries even when their entry itself has no percentage style.
2. **Definite, edit-independent provenance.** Every such read has a definite
   basis, and every height-producing link in its provenance terminates in
   an unchanged external size or content-independent specified size.
   No link's basis belongs to `G`; no link depends on changed content,
   unresolved intrinsic sizing, a changed clamp, or a flex/grid result
   still to be computed. Both numeric value and definiteness must be
   preserved. An indefinite basis is conservatively refused by this first
   certificate even if ordinary CSS would make its percentage ineffective;
   proving stable auto behavior is not needed to admit the approved case.
3. **Correct ancestor transfer.** Each ancestor in `A` has either the
   existing exact auto-growth transfer or a content-independent used-height
   transfer. In the latter case settle its changed content summary but keep
   its resolved used height; its outgoing size delta is zero. A percentage
   min/max constraint with a fixed basis is a fixed *limit*, not proof that
   an auto height stays fixed or grows by the child's delta. Such auto-height
   ancestors still need the existing growth certificate; an active or
   crossed clamp remains refused. No new general clamp transfer is implied.
4. **Private construction and all other certificates.** Resolve percentages
   inside the inserted subtree using the same containing-block inputs and
   rules as a fresh build. Record its new dependencies before publication,
   and apply premises 1–3 to external basis links and the proposed enclosing
   outputs. Internal definite chains can be resolved wholly in private
   storage. An indefinite/unsupported link or dependence on `G` refuses
   here too. Preserve the existing arithmetic, width, margin, marker,
   float/clearance, flex, positioned and split-fragment conditions.

The test is sufficient, not necessary. Unknown classification goes into
`G` or fails provenance; no speculative reuse is admitted on equal old
numbers. Removed consumers need no new layout, but their metadata must be
removed and surviving readers must still pass. A percentage-free edit uses
the old certificate. Every failed Q139 premise produces a counted
pre-publication structural refusal with reason 7 when that check is reached;
an earlier independent reason keeps its existing precedence. Do not relabel
Q129 float refusals or Q130's post-flex reason 10 as percentage failures.

### Correctness argument and its boundary

Fix a successful preflight and compare the proposed result with fresh layout
of the edited document at the same viewport. First prove basis invariance,
top down in the provenance graph. External leaves are unchanged by premise 1.
A content-independent specified-size link has identical style, limits,
width-dependent frame and input bases, so its used content height is
identical. A percentage link then applies the same expression, rounding,
box conversion and constraints to the same input; its result and
definiteness are identical. Premise 2 excludes a back edge through changed
content, so induction covers nested percentages without a circular
assumption that the ancestor is unchanged because its child is unchanged.
No multiplication of percentages into a shortcut is allowed: preserving
each resolution step also preserves rounding and saturation behavior.

Consequently each reused percentage height is constant. Each reused
percentage minimum/maximum resolves to the same limit. Outside `A` the
consumer's content, width and all other size inputs are unchanged, so
applying that same limit leaves its used height unchanged as well. On `A`
the content can change: premise 3, not the basis test, establishes the
ancestor's exact output. For example `height:auto; min-height:50%` can leave
its minimum when a child is inserted, although its minimum's basis never
changes. It is unsound to add the child's delta to that ancestor or to
declare it fixed solely from a retained clamp result.

Percentage padding and margins, including top and bottom, read containing
**width** in this horizontal ordinary-flow scope, as specified by
[CSS 2.1 margins](https://www.w3.org/TR/CSS21/box.html#margin-properties) and
[padding](https://www.w3.org/TR/CSS21/box.html#padding-properties).
Width equality therefore keeps their values and the frame conversion fixed.
It does not by itself prove unchanged collapsing-margin state: the existing
strut and through/solid certificates still do that. In particular the
current `snapshot_grows` rejects percentage vertical padding outright;
Q139 does not silently delete that additional refusal. A retained sibling
with fixed width can nevertheless retain percentage padding/margins under
its existing translation certificate. A width change requires its existing
fallback, regardless of the height basis.

Inside the inserted subtree there is no cached geometry to preserve. Its
private layout consumes proven enclosing bases, resolves any internal
definite chain in dependency order, and supplies the same size and boundary
outputs as fresh layout. Its new reads are part of the published metadata,
not hidden by combining only old boolean flags. Removal subtracts them.
The next insert, removal, text edit or restyle must see the current records;
an insert/remove roundtrip proves nothing about stale identities by itself.

For the root example, let the viewport content height be `V`. With default
content-box sizing and zero frame, `html {height:100%}` resolves against the
initial containing block to `V`; `body {height:100%}` resolves against html
to `V`. Additional nested `height:50%` containers successively resolve
against their immediate containing blocks. Inserting content changes
neither `V` nor those containing heights. Content can overflow them; that
overflow is not a new percentage basis. Normal html/body margins and frames
must still be resolved normally, not removed as an admission workaround.
A fixed-height ancestor absorbs the *used-height* delta, while its changed
content extent, baseline, anchored fragments and exclusions remain subject
to normal propagation. It is not a stop-on-height-equality rule.

For positions, apply the existing boundary-transfer induction from the seam
outward. At each ancestor, its recomputed changed child output and unchanged
prefix state determine the direct suffix's new origins. An unchanged
suffix entry has unchanged width, used height and normalized boundary input,
so it needs exactly its certified translation; its descendants retain local
origins. Beyond a fixed-height ancestor the size delta can be zero, but all
other outputs must still settle. No new percentage-driven relayout of a
retained off-path subtree is needed.

The precise preservation claim distinguishes the splice's existing update
sets. Let `T` be the existing direct suffix translations and boxes moved by
those anchors, and `U` its changed subtree, ancestor settlement, flex/positioned
recomputation and anchored-fragment updates. Every retained box outside
`T union U` keeps its used height and position; boxes in `T` that are only
translated keep used heights and local geometry. The literal claim that
*every* box outside `T` is unchanged would already be false for an auto-height
ancestor or a Q128 positioned child. Q139 adds no new off-path update set;
it proves that percentage inputs cannot add one. Split rectangles spanning
changed endpoints likewise belong to the existing anchor-update set.

The conjunction with the existing certificates is essential:

- **Floats and clearance.** Invariant percentage heights keep each retained
  float's height and exclusion shape fixed. Q129 still compares old and
  proposed suffix natural minima with stationary reach, including negative
  margins, clearance and float floor, and still forbids new/deleted float
  exports. All mutually interacting moved floats and flow must share its
  certified delta. A fixed-height ancestor may change an inner suffix by a
  nonzero delta while its outer suffix stays put; if those regions share
  float influence and no existing certificate separates them, refuse under
  Q129. Do not infer common motion from the newly constant height, or stop
  exporting float reach at a fixed-height block that is not a BFC.
- **Flex.** Q128 still recomputes the container algorithm and checks complete
  preparation/space keys, stretch, wrapping, free space and actual outputs.
  A size supplied by the changed flex result cannot be certified unchanged
  before that result exists: a reused percentage consumer of that size fails
  premise 2. Recomputed item interiors remain the flex algorithm's work,
  not reuse authorized here. Q130 still owns an outward failure after flex
  publication. Grid/table/multicol scope does not expand.
- **Positioned and atomic content.** Q128 settles the relevant anchors,
  recomputes positioned percentage sizes against the settled containing
  block, and refreshes their arithmetic charges. A changing positioned
  basis is not evidence against this proof about *reused in-flow* geometry.
  Atomic reuse must still satisfy its actual Space, baseline and paragraph
  rules; Q139 cannot invent a definite atomic basis where that path supplies
  an indefinite one.
- **Split fragments, arithmetic and margins.** Retain source-removal,
  seam-topology and endpoint-selector certificates and update the same
  stable anchors and line offsets. A fixed used height does not freeze a
  spanning fragment's endpoints. Content extent, measured constrained height,
  old/new travel and visual excursions all remain charged. Percentage
  resolution uses the full builder's numeric order and fails the existing
  bounds when necessary; equal basis values cannot justify reassociation.

For comparison only, Chromium's
[`layout_utils.cc` at the inspected revision](https://chromium.googlesource.com/chromium/src/+/4b47de55fa514cf90042b65c634b6ac10502d42b/third_party/blink/renderer/core/layout/layout_utils.cc#101)
reads `DependsOnPercentageBlockSize()` from the `LayoutResult`'s physical
fragment and compares old/new `PercentageResolutionBlockSize()` when that
flag is set. Its surrounding cache logic also checks sizing mode,
definiteness and other constraints. Q139 proves **before splice publication**
that the relevant old/new bases must be equal, using retained provenance and
the growing chain, rather than computing a new layout merely to compare
them. Both distinguish having a percentage dependency from changing its
basis; neither flag alone proves cache reuse. This is an analogy, not an
independent correctness oracle for Snowghost's transfer implementation.

### Refusals and minimal negative examples

These are HTML fragments for later fixture construction, not executed
fixtures. Unless a row says otherwise, place the fragment in a standards-mode
document with `body {margin:0}` and `p {margin:0}`, insert a line-bearing
`<p>new</p>` at the indicated comment, and also remove a pre-existing block.
Retain line-bearing content and a separator so a mixed-inline or through
seam does not accidentally supply the refusal being tested. Each Q139
failure is reason 7 if reached; variants exercising other guards must assert
their own reason rather than manufacturing a reason-7 result.

| Failure | Minimal fragment / edit | Why refusal remains necessary |
| --- | --- | --- |
| Indefinite basis on the growing chain | `<section id="a"><p>old</p><!-- insert --><div style="height:50%"><p>tail</p></div></section>` | `a` has content-driven auto height and is in `G`. The percentage behaves as auto here; reusing a numeric old height as a definite basis is invalid. This conservative refusal does not claim CSS requires a cycle or a changed percentage result. |
| Indefinite basis even off the growing chain | `<section><p>old</p><!-- insert --></section><aside><div style="height:50%"><p>tail</p></div></aside>` | The retained aside subtree contains an unresolved basis, although aside is not edited. A proposed summary that says only "basis not in G" would miss the definiteness premise. No stable-indefinite certificate is added here. |
| A broken intermediate percentage chain | `<div style="height:200px"><section style="height:50%"><div id="a"><p>old</p><!-- insert --><div style="height:50%"><p>tail</p></div></div></section></div>` | The inner percentage's immediate basis is auto-height `a`, not the outer 200px box. Retaining only the terminal definite ancestor would incorrectly admit it. |
| Percentage minimum on an auto-height ancestor | `<div style="height:200px"><section style="min-height:50%"><p style="height:80px">old</p><!-- insert 40px block --></section></div>` | The minimum stays 100px, but the section changes from 100px to 120px, not by the inserted 40px. An active clamp on the growing path is outside the existing transfer. Removal crosses the boundary in reverse. |
| Percentage maximum on an auto-height ancestor | `<div style="height:200px"><section style="max-height:50%"><p style="height:80px">old</p><!-- insert 40px block --></section></div>` | The maximum stays 100px, but the section grows by 20px and then overflows. Same-basis equality is insufficient; an active/crossed clamp remains reason 7. |
| Layout-supplied definite basis may change | `<div style="display:flex;align-items:stretch"><section><p>old</p><!-- insert tall block --></section><aside><div style="height:50%"><p>tail</p></div></aside></div>` | The changed flex line can stretch aside to a different height and re-resolve its child. A reused interior cannot treat the old stretch target as an external constant. Q128 may instead recompute that interior; Q139 cannot certify it before settlement. Where an enclosing unsupported entry refuses earlier, that earlier reason remains. |
| New percentage read with no admissible external basis | `<section><p>old</p><!-- insert <div style="height:50%"><p>new</p></div> --><p>tail</p></section>` | Looking only at retained reads would miss the inserted box's auto/content-driven basis. Private construction must fail this certificate before publishing any routes or geometry. |
| Changed source, resolution mode, or stale provenance | `<div id="basis" style="height:200px"><section style="height:50%"><p>old</p><!-- insert --></section></div>`; first change `basis` to `height:auto` or `height:300px`, then insert, without an intervening retained-record refresh in the fault injection | The old identity/value/definiteness record is not current. The legitimate style path must invalidate or republish it; missing records after a reference rebuild or slot replacement are equally unknown. A combined retained restyle may correctly refuse earlier with reason 6. |
| Changed viewport input | `html,body {height:100%}` with `<section><p>old</p><!-- insert --></section>`; resize the viewport before attempting reuse | The terminal external value is no longer equal. Normal resize layout must refresh it, or this preflight refuses. HTML alone cannot express stale retained viewport state. |
| Width/box-conversion input not preserved | `<div id="basis" style="width:200px;height:200px"><section style="height:50%;box-sizing:border-box;padding-top:10%"><p>old</p><!-- insert --></section></div>`; change `basis` width to 300px before reuse | Equal height basis does not keep the section's content height or padding fixed. Width/style invalidation must run; a stale record cannot pass premise 1. Existing width or style guards can refuse first. |
| Uncertified resolution mode or numeric transfer | `<section style="height:calc(50% + 2147483647px)"><p>old</p><!-- insert --></section>` under a definite viewport-based body; separately put the first row in a document without a standards-mode doctype | A percentage expression does not waive travel/overflow limits. The quirks variant cannot borrow the ordinary containing-block proof. These are conservative refusal probes, not assertions that their CSS has no full-layout result. |

Indefinite percentage min/max cases use the first row with `min-height:50%`
or `max-height:50%` in place of `height:50%` and retain reason 7 for this
certificate. A dangling basis handle, omitted descendant record, unsupported
provenance link, or cycle without a definite external derivation also fails
premise 1 or 2. Such metadata faults require injection into a real fixture;
there is no HTML declaration that directly creates a dangling layout handle.
The nonzero percentage in these negative probes must not be erased from
the record merely because its current used result happens to be zero.

### Required fixtures and falsifiers for the implementation task

The comparison is every incremental edit prefix against a fresh full build,
plus independent CSS/Chromium rectangle expectations for basis resolution.
Either a geometry difference on an admitted prefix or admission outside
these premises rejects the implementation. If full and incremental agree
but disagree with the independent expected containing block, both are wrong;
do not bless that output as a fixture. Begin in hosted CI with one reduced
insertion/removal pair before expanding the matrix. These are obligations,
not new files or completed validation in this argument-only task.

Positive fixtures must include:

- **Reduced apollo11 root chain:** standards mode, `html,body {height:100%}`,
  an ordinary auto-height section with old/inserted/later paragraphs and a
  later sibling; no grids. Assert successful local insertion and removal,
  constant html/body used heights, inner suffix motion and content overflow.
  Use enough content to cross the viewport height in both directions.
  Repeat with normal body margins, and a viewport change followed by a
  proper full refresh. The unchanged real apollo11 input still exposes Q140.
- **Nested definite chain:** a 200px containing block, a 50% child and a 50%
  grandchild, with complete block seams inside the grandchild and later
  siblings at each level. Expect 100px then 50px content heights with zero
  frame. Include a parallel sibling chain with a different percentage,
  nonzero border/padding and border-box variants; use a nonintegral
  percentage/basis combination to catch changed rounding order.
- **Limits on unchanged geometry:** retained sibling boxes with percentage
  min-height and max-height against a fixed basis, including active limits;
  and a content-independent percentage-height ancestor with fixed resolved
  limits. Their used heights stay constant. Do not use an auto ancestor
  crossing a clamp as a positive case.
- **Width percentages and private readers:** percentage top/bottom margins
  and padding on retained translated siblings at fixed width; an inserted
  definite percentage chain with a valid external basis. Repeat insertion
  before one old sibling, remove both new and old blocks, then edit retained
  and inserted text and restyle a basis. Confirm records are renewed after
  full fallback, with no stale slots or basis shortcuts.
- **Certificate combinations:** place the root/nested chain around each
  supported Q129 stationary-expired-float/later-float/clearance case, Q128
  positioned/atomic and flex cases, and the anchored split cases. Claim a
  positive splice only where all their old conditions still hold. Fixed
  height with a moving internal float and stationary interacting outer flow
  needs a negative companion, not a widened float certificate.

Negative fixtures cover every row above, both min/max indefinite variants,
unchanged-numeric-value but changed-definiteness state, a missing or retired
basis handle, and a percentage reader in a nested retained context whose own
entry is percentage-free. Retain the existing float-floor negative-margin,
flex changed-space, split-topology and near-limit negatives. Attribute the
first refusal to the guard actually reached; preserve full rendering on all
fallbacks and assert unchanged retained state at a reason-7 preflight exit.

Extend the existing temporary `falsify-m2` workflow on the implementation
branch. Apply each mutation separately to a restored baseline, require that
the intended fixture reaches that predicate, and retain raw path and dump
logs. Do not accept a compile error, unrelated earlier refusal or a crashed
driver as detection. The workflow's branch trigger must include that branch;
adding a mutation name without execution is no evidence. The premise-to-
mutation obligations are:

| Premise | Mutation, and observation required to detect it |
| --- | --- |
| Complete consumer inventory (1) | Omit one percentage reader in a retained nested context or a float, and independently ignore min-height and max-height reads. The focused negative must lose its required reason-7 path or produce wrong geometry. Instrument the selected predicate so an earlier guard cannot masquerade as detection. |
| Correct immediate basis and full provenance (1–2) | Replace the immediate containing block with the context root, or flatten a nested chain past the auto-height intermediate. The independent 200/100/50 rectangle expectations or the broken-chain refusal must fail. |
| Definite, content-independent basis (2) | Treat an indefinite old numeric height as definite; separately accept an old flex stretch target as immutable. The auto-height/flex negative must either violate its reuse/refusal assertion or differ after the growing edit. A fully recomputed flex interior is not a detection of this reuse mutation. |
| Growing-chain exclusion (2) | Ignore one basis membership in `G`, or remove an unresolved layout-sized ancestor from `G` on equal old numbers. Use a certificate-level fixture for this predicate with other premises supplied, plus a flex-growth integration probe; demand an explicit assertion failure if another preflight conservatively masks the mutation. |
| Freshness, identity and external inputs (1–2) | Skip invalidation after changing a basis from definite to auto, after replacing its stable handle, and after a viewport/width change, one at a time. A subsequent edit must fail the freshness assertion or produce a dump/independent-rectangle difference. Compare state as well as the numeric basis. |
| Exact constrained ancestor transfer (3) | Propagate content delta into a fixed percentage height; independently treat an auto-height percentage clamp as exact growth. Root overflow and the 80px + 40px limit probes must differ at an ancestor or its later sibling. Also mutate the output-equality cutoff to ignore changed extent/baseline with equal used height. |
| Private subtree and metadata lifetime (4) | Resolve a fresh reader using the context basis instead of its containing block; separately omit its dependency publication or fail to remove a retired dependency. Nested private rectangles, a subsequent basis edit, and a removal followed by another local insertion must detect these respectively. Missing publication must not be hidden by an intervening full rebuild. |
| Width-dependent frame and unchanged margin transfer (1,4) | Use height instead of width for percentage padding/margins, or reuse their old resolved value after a width change; separately ignore an exposed-strut change. Non-square geometry and the existing margin probes must differ or violate refusal. |
| All existing certificates remain conjunctive (4) | Independently bypass stationary-float reach, common-motion equality across a fixed-height boundary, flex Space equality/stretch layout, split-topology protection, positioned charge refresh and numeric travel checks. Their focused combination cases must detect each bypass; run the existing mutation rows as well. |
| Numeric resolution and counted refusal (2,4) | Collapse nested percentage arithmetic into one multiplication, then independently suppress a reason-7 path row or count it as a successful splice. The rounding fixture and existing malformed-path assertions must detect the respective changes. |

These include semantic mutations and conservative admission-policy
mutations. The latter may leave rendering correct; their detection is an
explicit basis/certificate or required-path assertion, as in the existing
seam and path-log falsifiers, not a claim of a rendering defect. A guard
with no reachable integration counterexample still needs an isolated
certificate assertion varying that premise while keeping the others fixed.
Positive-path assertions also prevent replacing the whole extension by
unconditional fallback. Full-build cost is a separate empirical gate.

### Retained data, dependencies and criterion 4

The current boolean `flow_definite_free` says only that some percentage read
exists; it cannot identify the basis or distinguish html from an edited
auto-height ancestor. The later implementation needs the per-read records
above, live provenance links and invalidation ownership, plus a summary that
can answer whether any reused read has unknown/indefinite provenance or
reaches `G`, without scanning unrelated descendants on every edit. Width
inputs and fixed-used-height versus content-output fields must stay distinct.
The record describes actual resolution, not a second CSS resolver maintained
only for splice admission.

Let `N` be live layout boxes, `P` percentage-property reads, `D` enclosing
depth, and `K` the dependency-summary/index records visited by an edit.
There are at most three direct height-property reads per box here; repeated
copies of each read at every ancestor would nevertheless cost `O(P D)`.
Retain shared provenance edges, not expanded ancestor lists. Missing metadata
must safely fall back, but must not become the way the positive fixtures
quietly evade the intended admission.

| Candidate | Actual dependencies and costs | Disposition |
| --- | --- | --- |
| Per-box records with an edit-time scan of every retained consumer | Full-build record writes depend on that box's existing style/containing-block resolution; independent children write disjoint records. Once ancestor inputs are known, all edit-time membership queries can run independently and reduce with a balanced OR. Storage and build work are `O(N + P)`; each edit reads `O(P)` consumers even when it changes one paragraph. | A correctness reference for CI, not the final local splice. Parallel scanning removes no page-wide work and fails the existing locality criterion. |
| Locally owned records and composable dependency summaries over the existing owner/index tree | Style and containing-block identity precede each record; a definite percentage depends on its basis value, giving true top-down edges through nested percentage chains. Sibling records are independent once those inputs exist. Parent summaries depend on child summaries and combine by balanced reductions, not a document-order fold. Edit queries read immutable summaries after `A/G` classification; disjoint query results reduce independently, and publication joins only changed index ancestors. | Recommended direction: retain direct provenance once and use queryable summaries to avoid unrelated consumer leaves. Exact set/range representation, `K` bound and byte cost remain implementation obligations, not a claim that one bit or a constant-sized exact basis set suffices. Summaries may conservatively refuse; they must still admit the required definite chains. |
| Per-basis reverse reader lists, filled by shared append | Each reader must first resolve its basis. Shared mutation then orders otherwise independent readers of the same viewport/root basis; repairs can fan out to all its readers. A dense page-sized reverse table also charges percentage-free full builds. | Not recommended: the append order is not a layout dependency. If exact reverse grouping proves necessary, disjoint emission followed by balanced grouping is the parallel alternative; its extra storage/work and reader traversal still need comparison with owner summaries. |

Constructing `G` requires proving independence, not first recomputing the
whole page: follow already recorded basis links from unchanged terminals.
Then read the changed owner's outward path and conservatively classify
content/layout-dependent sizes. Private subtree resolution can overlap
independent retained-summary queries once enclosing inputs are known.
Boundary output propagation waits for the changed child and its containing
algorithm, as before. Shared cache insertion, a global allocation counter
on the dependency path, and sibling-by-sibling record validation add no
necessary dependency and are not the recommendation.

The records charge the full build for provenance writes, summary construction,
storage initialization and retained memory, even on a frame with no edits.
Percentage-free boxes should incur only the representation's empty-state
cost, not allocated reader lists or a second traversal. Reuse the existing
resolution pass where possible; doing so is not proof that the added cost is
negligible. Report actual fields/bytes, allocations, record and index visits,
and any full-build pass added in the implementation task.

[M2 criterion 4](DESIGN.md#criterion) still requires full style and layout
within 5 percent of M1's `8b8612f` on every page; this extension receives no
extra allowance. Before measuring, record the comparison of the same source
with/without record collection, interleaved runs and a twin base noise
control, on the 14900K through CI with identical compiler, captures and
settings. Compare sequential and four-worker full builds and per-edit costs;
begin with the smallest useful sample and expand only if its spread cannot
settle the question. Exceeding criterion 4, scanning unchanged descendants,
or introducing an unnecessary sibling dependency rejects the implementation
choice even when its geometry is correct. No cost has been measured here.

### Remaining uncertainty and rejection conditions

The argument is conditional on exact containing-block provenance and the
existing transfer certificates; it does not establish that today's full
builder already supplies those facts. Source inspection finds
`prepare_spaces` passing a context-wide `content_height` into nested child
spaces, and `stack_flow` passing its single `basis_height` to ordinary block
height resolution. Its open-block frames track widths but not a nested
height basis. That is a concrete risk for the nested 200/100/50 fixture,
recorded in [the TODO](../../../docs/todo.md); no local run establishes the
actual mismatch. Before implementing admission, CI must compare nested and
auto-intermediate full builds with independent expected rectangles. If they
disagree, repair full resolution and its consumers; do not encode the wrong
context-wide basis as an invariant or narrow the required nested fixture.

Other open evidence is whether the supported numeric/box-sizing paths,
fixed-height ancestor output summaries and cross-boundary float certificates
can implement these premises without extra descendant work, and which
summary representation meets criterion 4. Those are later implementation
and measurement obligations, not owner decisions made by this prose. No
new choice is requested beyond Q139 A and Q145 C. A need to admit changing
bases, stable indefinite percentages, general clamp transitions or a wider
float/flex scope would require another argument and an owner ruling.

An admitted edit that changes a supposedly invariant basis, off-path used
height or position overturns the proof's premises or its transfer argument.
A specification/reference-browser exception in the claimed ordinary scope,
an overlooked provenance edge, or a full-layout result that depends on
content despite the asserted definite derivation has the same consequence.
Keep the counted fallback until the discrepancy is resolved. A surviving
mutation overturns the claimed evidence; a slow full build overturns the
representation choice, not the CSS induction. This task changes no renderer,
pin or submodule, files no Whitefoot gap, and supplies no execution results.


### Q139 implementation: independent full-layout probe

The implementation first compares `tests/layout/percentage-height-cases.html`
with Chromium through `tests/layout/layout_oracle.mjs` on hosted CI. The
probe covers a 200px block with nested 50% blocks, the same outer block with
an auto-height intermediate, the html/body viewport chain, and a nested
formatting-context boundary. A mismatch rejects the existing resolver;
full/incremental identity cannot establish this premise. The Chromium dump,
comparison and renderer dump are retained as CI artifacts. The focused case
has fourteen block boxes and no visible inline/text boxes; its ordinary
oracle floor requires all fourteen to match.

The candidate repair propagates the immediate containing block's definite
content height in the existing top-down pre-pass and retains the input in
`BlockOutput.basis_height`. Every intermediate percentage is resolved in
order; an auto-height block supplies an indefinite basis. The stacking pass,
child spaces and boundary/growth consumers use that same input. A restyled
block with percentage-dependent descendants requires the pre-pass before
child layout; width equality alone cannot establish height-key equality.
The baseline [hosted run 37761041831](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37761041831)
at `480b7d5180be244ed8844ea876cb4cea908e9fb7` confirms the defect:
Chromium 141.0.7390.37 resolves 200/100/50px, while the renderer produces
200/360/360px. The auto intermediate and its percentage child are both
30px in Chromium and 360px in the renderer. The viewport chain gives
html/body 720px, then 360/180px; the last renderer box is 360px. Across the
formatting-context boundary, Chromium gives 200/100/50px and the renderer
200/360/180px. Seven of fourteen block boxes match; the comparison exits 1.
The committed `.chromium.tsv` is the downloaded reference artifact and the
workflow requires a fresh Chromium dump to agree before judging the fix.

The baseline driver build took 6m59s and the focused dump 0.227s on the
hosted runner; these observations size the next sequential/parallel fixture
run, not a renderer performance comparison. The repaired revision
`ed2d4114d6b4db98d2025b1278bf1d330261a3f4` passes in
[hosted run 37764019799](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37764019799):
all fourteen block boxes match Chromium exactly, sequential and four-worker
dumps agree byte for byte, and every existing layout case floor passes
unchanged. The [gate at the same revision](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37764019903)
also passes. This closes the nested-height TODO before splice admission.
The earlier source-format and effect-row failures produced no rendering
results and are not regression evidence. Revision `03f8e43` additionally
probes restyles of height, definiteness and width with ordinary, atomic and
floated children. Its first 42 ordinary restyles pass, but
[run 37765149668](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37765149668)
then refuses the probe's display-changing class edit, as the style-only API
requires topology reconstruction. Each display/float mode is therefore set
by the initial stylesheet before its retained baseline; all height/width
edits remain required, with no allowance for refused edits. Validation of
those separate mode runs passes at `c0ffc6979d9090dcaa2f55de12d54610f32c2c41`
in [run 37767223590](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37767223590):
42 edits per mode, each in sequential and four-worker builds.

Per the implementation task's machine constraint, all evidence and all
performance comparisons use GitHub-hosted CI, including the comparison of
every X5 edit kind against main and `95ea4a1` with a twin. No local build,
check, test or timing is part of this experiment. This overrides the earlier
argument's proposed 14900K measurement host for this task.


### Q139 implementation: records and local summaries

The candidate retains one `HeightProof` per block/context, naming its actual
immediate basis and the height/minimum/maximum read mask, state, numeric input,
content result and style keys. The ordinary containing-block links share
provenance; a percentage-free specified size starts an independent terminal,
and an auto intermediate or a flex/grid/table supplied size cannot be promoted
from its last number. Existing full-layout pre-passes establish the top-down
inputs; sibling record writes have no added shared cache or reader append.

Live `HeightSummary` counts compose in the existing balanced ordinary-flow
index. Non-flow owners combine cached direct-item summaries with a balanced
reduction after their algorithm settles. The intended admission query reads
those summaries plus the enclosing path, not consumer leaves elsewhere in the
page. Publication, removal and reference refresh must preserve those counts;
missing records count as unproved. The live-tree decision is proposed, with
admission, fixed-height transfer and the required mutation matrix still being
implemented. No positive splice or locality result is claimed yet.

The cost comparison rejects a Q139 regression beyond the paired twin spread
for any X5 kind. The hosted workflow uses the same compiler release and
settings for main `8fbc1601785cee70265da1eac4d99589fc6fb67c`, M2
`95ea4a10832257d0563d2410565900e5d2981118`, its independently built twin and
the candidate, sharing exact page captures, fonts and edit scripts. Start with
one forward/inverse pair per kind in two interleaved rounds, then select scale
from its observed duration and spread. The full-build and storage comparison
remains an additional obligation; this small sample cannot establish it.


The draft provenance implementation separates the parent's incoming edge from
the child's last certified input. Geometry reuse compares both, so a changed
identity or definiteness state triggers fresh layout even when dimensions
are equal. Ordinary block records are resolved top down; live-source checks
include the stable context, owner, consumer style and nonretired entry slot.
Their cached summaries are published bottom up through the existing owner
index. A splice checks its enclosing sources and preserves unrelated
certificates only under invariant source inputs; retirement removes owned
consumers through the same index. No edit-time descendant scan is intended.
This is implementation reasoning, pending the lifetime fixtures and review.

The draft review found two issues before successful admission validation:
constrained siblings lost a collapsed bottom strut, and recorded source
identities were not checked. The former now retains the full resolver's
bottom-separation state; the latter is being addressed with live-link checks
and separate incoming/certified inputs. Neither is claimed verified yet.


The fixed-height float conjunction uses the existing no-new/no-deleted-export
premise. At an absorber, an existing export moves either by the incoming
displacement or by zero (a lower absorber can stop part of the displacement).
Thus old global reach plus the positive part of the displacement bounds both
old and proposed exports. Carry that bound outward after used-height delta
becomes zero; every outer direct suffix's old/new natural minimum and the
context flow end must remain beyond it. Existing known-motion and exact
arithmetic checks still apply. This admits expired internal floats while
refusing stationary outer flow that could newly intersect a moved float;
no descendant traversal or active-float relayout is introduced. The focused
`fixed-floats` and `fixed-float-reentry` fixtures discriminate these cases;
execution and a bound-bypass mutation remain required.


The initial full-layout repair used a context-wide percentage guard on local
block restyles. The candidate narrows that guard to the affected subtree:
every old and new ordinary-block read and every immediate Child/Float/Atomic
read is checked, including unmarked entries. A percentage-free child keeps
its own fixed or indefinite outgoing basis when its incoming containing
height changes; its independently marked style/content update still settles
normally. Readers outside the affected subtree cannot read a changed inner
source. This avoids forcing unrelated edits through a full pre-pass solely
because html/body uses a viewport percentage. The height/width restyle probes
and all-kind paired costs must validate the narrowed path before adoption.

The fixed-height transfer preserves the existing vertical-percentage-padding
refusal, as required by the argument; `ancestor-width-padding` isolates it.
Retained siblings with unchanged width still use their translation certificate.
The narrow read-only review of the float bound and subtree restyle refinement
found no concrete defect within those changes; execution and mutation coverage
remain pending. The hosted draft gate passed at `96cf59e178e0040bf478226c9d186eec3769f8ac`
([run 37773447136](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37773447136));
this is compilation/static evidence, not completion of Q139's admission probes.

The first compiled provenance draft kept the independent full-layout boxes
but failed the floated-container restyle inventory on restoring its percentage
style ([run 37772936762](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37772936762),
`5edd410d4830c34e2cd7c301f1978eee650eda9a`, edits 8, 10 and 12).
The parent equality cutoff predates retained height inventories. Its `Before`
record now snapshots the published inventory and equality compares both
consumer and unproved counts, so unchanged geometry cannot suppress metadata
publication. A read-only inspection confirmed the missing equality input;
the hosted rerun must establish whether this repairs the observed failures.
Every restyle prefix now requests dumps to preserve both sides of a mismatch.
The edit oracle also supports a full viewport refresh between edits; root
and nested lifetime probes resize, rebuild normally, then require another
local insert/remove pair at the new viewport and after restoration.

The mutation harness is being extended on the Q139 branch itself. Initial
rows target reader inventory, immediate/auto-intermediate basis resolution,
indefinite and layout-sized inputs, growing-set classification, individual
freshness fields, fixed/clamped transfer, private publication, float common
motion and constrained struts. Pure classification and input-equality helpers
are shared with the implementation so isolated assertions exercise the real
predicates; their extraction changes no admission rule. No mutation is counted
as detected before a hosted run compiles and executes its driver. Remaining
rows include retired dependencies, arithmetic reassociation, width-frame
resolution, output-equality and path-report mutations, plus the original
conjunctive-certificate matrix. The complete fixture runner is prepared but
will not replace the required first successful timed root splice pair.

The next evidence pass keeps the original positioned, flex, float, clearance,
split and edit-cost fixture path assertions, and repeats them under the
html/body viewport chain. This exposes any interaction between the new
conservative inventory and the old successful paths without silently changing
an expectation. The mutation inventory now also covers retired dependencies,
fixed-height output cutoffs, height substituted for width in spacing,
collapsed nested-percentage arithmetic, suppressed refusal rows and false
successful-splice reporting. These remain prepared obligations until executed.
The full pre-pass consumes the content height already returned by its proof's
normal resolver instead of resolving the identical height a second time.

The first reduced root splice passes at
`2dde3c0b276aa95ab0422e64a1a6f23ac2aecc02`
([run 37774886038](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37774886038)):
both builds splice insertion and removal with reason 0, every prefix matches
a fresh build, and Chromium matches every requested block exactly (6/7/6
boxes before/inserted/removed). The driver pairs took 0.226s sequential and
0.227s with four workers; the focused matrix can now expand on hosted CI.
Existing Chromium layout floors also pass. The run remains failing because
float restore edits 8/10/12 retain stale geometry. Requested dumps establish
300/150px retained versus 100/50px fresh on edit 8, so the inventory-equality
repair did not settle this failure. The new provenance-mismatch full-layout
branch cleared descendant marks but left the updated context itself dirty;
the next restyle therefore could not count it as newly marked. It now clears
the whole settled subtree, matching the ordinary update's mark lifecycle.
The next CI run must verify that repair; no expectation was changed.

Mutation jobs share immutable sequential/four-worker baseline drivers built
once from their workflow revision, while every mutant starts from a separate
fresh checkout and changes one named predicate. This removes repeated baseline
compilation, not an oracle or negative control. Each row still validates its
unmutated focused fixture before accepting its intended failure. The detector
has hosted machinery controls for identity differences, intended reason-7
admission loss, missing rows, exact certificate assertions and unrelated errors.
