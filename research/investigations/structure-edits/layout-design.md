# M2 layout: parent-relative blocks and a flow splice

## Scope and measurement criterion

This is the layout design and sizing investigation for M2, based on
`7ee44119358d7b08dc90555ebe7b9275be478bed`, with Whitefoot pinned at
`f949e676acfa811f96b21afd07f02c06dcd14b51`. It proposes no rendering change.
Q109 already approves nested flow entries per block; Q104 reopens Q70's
context-relative suffix move. The implementation is staged below; Q114 and Q115 below are open
recommendations.

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
is an inventory of the current code, not additional CSS promises. A block
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
global order representation on every edit. The new
material choices are proposed here, not already implemented or owner
approved: local stable slots, order/summary index and boundary outputs (Q114), and the initial
splice's safe scope with explicit fallbacks (Q115).

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
copies remain migration support. Stable entry handles, paged route growth
and local splice publication remain unimplemented. Step 1 is the compiled input to step 2; its validation evidence remains
with the primary agent, and is not a step-2 validation result.
`Context.flow` is the temporary flat-walk adapter's single ordered sequence;
its recorded positions, split endpoints and baseline entry are still ranks.
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

This source has no step-2 compilation, dump, edit-prefix, mutation or timing
results yet. The primary agent runs those in CI. Context-wide conversion
snapshots and the legacy fragment, split-line, natural and baseline state
remain compatibility work, not evidence of bounded edits; their replacement
with owner-local boundary outputs is recorded in the TODO. A lineless
paragraph retains the reference walker's unplaced scratch-origin behavior.
Steps 3 onward below remain unimplemented. Each step lands with
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
| 5. Publish a flow-range splice | 650–1,100: `structure`, `build`, routing/marking helpers, `oracle/layout/edit`, focused scripts. Private subtree build, local sequence swap, seam validation, targeted routing and count deltas, insert and removal. | Three pages' block scripts, `research/investigations/incremental-layout/scripts/block-case.html` and its `.edits` script, focused counter / `:nth-*` / `+` / `~` / float / collapsing-margin / split-inline cases. Compare every prefix with full build and serialized-source reparse, seq and par. Assert an explained refusal leaves the retained tree untouched. After each removal edit, issue another text/font-size edit to catch stale routes. | Disable the structural style frontier, fail to restack P's later siblings, skip a route tombstone/generation check after slot reuse, ignore outgoing counter state, or publish before seam validation. Each mutation must fail; an unexplained `inc refused` is not success. |
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

## Risks and owner questions

Q104 and Q109 are approved directions. Q114 and Q115 below remain open;
this research does not claim implementation approval for them.

- **Q114 — stable local slots and block boundary outputs (recommended).**
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
- **Q115 — a neutral complete-block seam first (recommended).** Counter
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
Q114 and Q115 are open recommendations; Q104 and Q109 are approved
inputs. No approval log entry or readiness claim is made. Delivery is a
local branch commit only, as requested; there is no push or PR update.
