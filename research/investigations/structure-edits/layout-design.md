# M2 layout: parent-relative blocks and a flow splice

## Scope and measurement criterion

This is the layout design and sizing investigation for M2, based on
`7ee44119358d7b08dc90555ebe7b9275be478bed`, with Whitefoot pinned at
`f949e676acfa811f96b21afd07f02c06dcd14b51`. It proposes no rendering change.
Q109 already approves nested flow entries per block; Q104 reopens Q70's
context-relative suffix move. The implementation remains future work.

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
| Block indices are preorder, ancestors precede descendants, and a subtree is a contiguous index interval. | `build.wf:place_element`; `style_update.wf:common_restyled_block`; `update.wf:first_block_after`, `restack_block`, `local_ancestor_width`, `prepare_local_widths`. | Stable identity cannot be compared numerically for ancestry. Use parent/depth ancestry and an owned subtree; never binary-search append order. |
| A flat balanced Open/Close stream gives each block its parent, containing width and close. | `flow.wf:prepare_spaces`, `stack_flow`; `update.wf:restack_block`; `columns.wf:collect_units`; `module.wfm:Flow`. | A block owns a direct-entry sequence; entering/leaving it replaces Open/Close. An iterator may expose virtual Open/Close for the reference walker, without materializing a full flat array on edits. |
| Paragraph indices increase in flow order. | `build.wf:end_paragraph`; `update.wf:first_paragraph_after`, `first_float_paragraph`; `flow.wf:previous_stacked_paragraph`. | Separate paragraph identity from order. The predecessor-with-lines query follows sequence/tree order; a numeric paragraph slot is never a rank. |
| A paragraph's pieces occupy `Context.pieces[first..first+count]`, in inline source order. | `build.wf:add_piece`, `end_paragraph`; `prep.wf:prepare_paragraph`, `prepare_context`; `update.wf:patch_pieces`; `structure.wf:take_prepared`, `reuse_prepared`, `first_text_node`. | Keep pieces contiguous **within the paragraph**, owned by it. Inserting pieces must not shift every later paragraph's range. Whitespace collapse and shaping still run across the whole paragraph. |
| An open inline is closed and reopened across a block interruption; inserting a block can divide or join adjacent paragraphs. | `build.wf:stash_inlines`, `restore_inlines`, `emit_begins`, `end_paragraph`, `place_element`. | The splice boundary includes the two adjacent inline runs and open inline stack, not just the inserted DOM subtree. Plain block-between-blocks has empty boundary state; mixed inline/block content needs boundary repair or the existing rebuild fallback. |
| Splits are ordered by `open`, and `open`/`close` are flat flow indices. | `build.wf:open_splits`, `close_splits`; `flow.wf:place_splits`, `line_splits`, `split_closings`, `sibling_above`, `gap_lineless`, `split_fragments_with_empty`. | Stable entry endpoints and a local owning scope; order comparisons use that scope's sequence. A closing bit array sized to the context flow is not a retained edit structure. |
| Split/empty-inline fragments are derived from flow ranges and context-space extents, although `Fragment` itself has **no flow-index key**. | `flow.wf:entry_extent`, `shows_owner`, `empty_inline_fragments`, `split_fragments_with_empty`; `update.wf:range_start`, `translatable_fragments`, `translate_fragments`, `shift_split_lines`. | Anchor fragments to the narrowest owning block/paragraph and retain endpoint references for spanning fragments. Recompute a changed spanning fragment; do not translate every fragment of a context. |
| `Block.x/y` and `Paragraph.x/top` are in the context border box; paragraph line/fragment offsets are already paragraph-local. | `module.wfm:Block`, `Paragraph`, `Line`; `flow.wf:resolve_open`, `stack_flow`, `place_paragraph`; `inline.wf:break_lines`, `finish_lines`; `update.wf:range_start` and position readers and translation functions. | Distinguish normal-flow origin, CSS relative displacement and final visual origin. Store block/paragraph origins relative to their owning block; preserve paragraph-local lines. A mechanical `y -= parent.y` is insufficient. |
| Pre-pass `inner_x`, `avail_left`, `content_left`, paragraph `left` and `broken_left` are context-content coordinates. | `flow.wf:prepare_spaces`, `block_relative_offset`; `update.wf:local_width`, `write_local_block`, `write_local_paragraph`, `block_keeps_width`; `inline.wf:exclusion_room`, `break_lines`. | Keep width/percentage inputs separate from coordinate origins. Convert to context-content coordinates only where exclusion tests need them; a rigid subtree translation must not appear to change its line-breaking key. |
| `flow_at` names a flat entry for blocks, paragraphs and children; an atomic child uses its paragraph's entry. | `flow.wf:prepare_spaces`; `module.wfm:Context`, `Block`, `Paragraph`; `update.wf:entry_kind`, `restack_entry`, `shift_child`, `update_atomics_in`. | Stable `(owner block, entry slot)` handles, with explicit atomic/paragraph ownership. Ranks are ephemeral iterator positions, never persistent handles. |
| `naturals` has one position per flow entry; `baseline_entry`, restack ranges and `held_y` share its index/coordinate system. | `flow.wf:prepare_naturals`, `set_natural`, `later_floors`, `previous_stacked_paragraph`, `resume_open_frames`, `restack_settles`; `update.wf:restack_flow`, `shift_naturals`. | Attach natural state to local entries and baseline to a stable descendant handle. Parent motion must not rewrite descendant natural positions. Preserve the distinction between no-line/sentinel state and a valid coordinate. |
| Pending margin struts and unresolved ancestor tops can cross block edges. | `flow.wf:Stack`, `Frame`, `add_margin`, `resolve_open`, `open_unresolved`, `mark_lines`, `stack_flow` Open/Close branches. | Carry positive and negative components, through-collapse state, line/marker presence, border/padding barriers and height constraints. Equal height alone is not a cutoff. An empty block can transmit margin state without consuming height. |
| Floats belong to the formatting context, not the lexical block; earlier floats affect later descendants and siblings. | `flow.wf:place_float`, `float_bottom`, `narrow_beside`, `resume_float_state`, `later_floors`, `restack_settles`; `inline.wf:exclusion_room`, `break_lines`; `module.wfm:Exclusion`. | Keep the BFC exclusion order and test its input/output at block boundaries. A nested block is not a new float containment boundary. Clearance, float floor, reach and horizontal room are observable inputs. |
| Child indices identify owned contexts across flow, inline marks, prepared atomics and table metadata. | `build.wf:add_child_flow`, `add_object`, `place_cell`; `module.wfm:Mark.Atomic`, `Piece.Object`, `Atomic`, `TableCell`, captions; `inline.wf:measure`, `atomic_metrics`, `finish_lines`; `flow.wf:place_atomics`. | Stable local child slots with holes or owned handles; update every cross-reference when ownership is migrated. No shifting live child identities on a splice. |
| Text routing and context serials are rebuilt in preorder, and child positions form paths. | `build.wf:record_tree`, `record_units`, `record_skipped`; `structure.wf:fill_serials`, `relative_steps`, `structure_changed`; `update.wf:path_steps`, `mark_path`, `text_changed`; `module.wfm:TextUnit`, `ContextPath`. | Stable routes through owner/slot links, patch only created/deleted/boundary units and ancestor links. Preserve skipped whitespace nodes' routing. Delete the full-tree recount, NodeId-array initialization and order-map copy from a successful local splice. |
| A style use summarizes a contiguous paragraph index range; `shared` can force broad marking. | `build.wf:note_use`, `record_uses`; `style_update.wf:styles_restyled`; `module.wfm:StyleUse`. | Use a local owner/subtree plus explicit stable paragraph uses when discontiguous; update only the splice's uses. An over-approximation is allowed for correctness but its visited work must be counted. |
| A structural rebuild restores its context's entry walk state and must leave the same counter/quote state; retained generated spans and pseudo indices must still mean the same thing. | `build.wf:apply_counters`, `leave_scope`, `add_content`, `build_box`; `structure.wf:same_point`, `retained_outside`, `changed_outside`, `structure_changed`; `module.wfm:WalkPoint`, `StyleRef`. | Local building must prove a state-neutral seam, or replay dependent counter/quote readers, or refuse before publication. Reusing a context checkpoint at an arbitrary block insertion is wrong. Q111 stable element slots do not automatically stabilize pseudo/generated references. |
| Width/height/baseline/margins/intrinsic outputs and dirty counts govern propagation and no-change cutoffs. | `update.wf:before_of`, `same_outputs`, `update_held`, `update_flow`, `clear_marks`; `flow.wf:flow_frame`, `prepare_spaces`; `module.wfm:Context`. | Extend equivalent cutoffs to blocks, with margin/float output state. Preserve `definite_free`, intrinsic demand and positioned dependencies. Dirty ancestor flags alone do not justify scanning every sibling's payload. |
| Positioned descendants use the nearest positioned block's final dimensions; fixed boxes can use viewport origin. | `flow.wf:positioned_block`, `chain_anchor`, `position_child`, `position_out_children`; `flow.wf:place_context`. | Separate geometric owner from containing block. Mark dependent out-of-flow descendants when their containing block changes, and keep viewport-relative origins from accumulating block offsets. |
| A table cell's content can be shifted for borders/alignment, and its first baseline is read in flow order. | `table.wf:table_first_baseline`, `shift_cell`, `lay_out_table`; `tablegrid.wf` and `tableborders.wf` supply the table's dimensions. | First-baseline traversal descends nested flow in order. Apply a content-origin offset once, not to every nested block plus its descendants. Table rows/cells remain context-local; table-wide sizing remains a legitimate fallback. |
| Flex/grid sequences preserve document order among equal `order` values, while child storage is indexed independently; flex natural height reads every descendant extent in context coordinates. | `flex.wf:intrinsic_flex`, `flex_collect`, `flex_content_height`, `flex_position`, `lay_out_flex`; `grid.wf:grid_collect`, `grid_first_baseline`, `grid_finish_child`, `lay_out_grid`. | Keep a direct item sequence and stable child handles; convert extent reads or expose an equivalent subtree extent. Do not treat nesting as a reason to change item ordering, track algorithms or baseline rules. |
| Column units are in one-column context coordinates; avoid regions skip their descendants, and table children expose rows. | `columns.wf:collect_units`, `balanced_height`, `fragment_columns`; `flow.wf:place_rect`, `place_fragment`. | Accumulate block origins while collecting units, apply the column map only after coordinate accumulation. Rebalancing may reach the whole multicol context; it is not a plain sibling-translation edit. |
| Placement turns retained geometry into viewport rectangles; the dump groups them while preserving each owner's fragment order. | `flow.wf:place_context`, `place_boxes`; `renderer/oracle/layout/layout.wf:write_dump`, `put_rects`, `lay_out_page`; `renderer/oracle/layout/edit.wf:run_edits`, `finish_style_edit`. | One traversal carries accumulated origins, O(output), instead of an O(depth) ancestor sum for each rectangle. Keep fragment order, fixed origin and column ownership. Placement/dump are excluded from E1's layout timing and must be measured separately before paint. |
| Work counters currently mix restacked entries with translated suffix entries, and are not a complete count of everything visited. | `module.wfm:UpdateCounts`, `StructureCounts`; `update.wf:restack_flow`, `update_in_place`, `update_counts`; `structure.wf:structure_counts`; `renderer/oracle/layout/edit.wf` reporting and `incremental-layout/scripts/inctime.py`. | Preserve existing report meaning during migration; add separate physical visits, subtree skips, translated direct entries, rebuilt units, routing patches and fallback reason. `restack_flow` currently computes a suffix length even when no delta moves it; it also reports one paragraph for a block range. These are not valid locality proofs. |
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
uses and `G` affected split-fragment endpoints. These are work counts, not
nanoseconds. A wide parent can make `S` page-sized; nesting is not a bound
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

For the first implementation, direct sequence storage may be a local
`Slots<EntryId>` rebuilt on insertion, O(s_parent), with payload ownership
moved only when that local storage grows. Store order rank on the local
entry; only P's ranks change. Sibling loops write each owned payload
independently. Stable holes need a local free list or generation check;
never use a context-wide next-ID counter in parallel construction. A
block's path is its parent link plus its parent's stable child slot.
Paragraphs and contexts use the same ownership rule. Array growth outside
this local scope is addressed under the splice contract below.

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
  update each. Work O(E + T + S + F + R + G), with possible whole-container
  work for the named fallbacks. Ordinary span is E's dependency depth +
  text work + sum(log(s_i + 1)) + D; an exclusion chain adds its actual
  dependent work. This is **not** O(D) total work.
- **One block's font size:** changed style uses -> independent preparation
  of the affected paragraphs, and width propagation through W -> affected
  boundary outputs -> the same ancestor propagation and sibling maps.
  Work O(W + T + S + F + R + G). Font-unit advances may be rescaled where
  the current reshape key allows it. No new global shaping cache.
- **Text edit:** stable text route -> patch that paragraph's owned piece ->
  prepare/shape/break that paragraph -> compare its output -> propagate
  only if boundary outputs change. Work O(T + D) when outputs hold,
  otherwise O(T + S + D + F + G). Text/whitespace changes that create or
  destroy a paragraph enter boundary repair; they are not assumed to keep
  the box tree. The chain is the paragraph's text work followed by the
  ancestors; unrelated paragraphs have no dependency on it.

A local sequence rebuild copies handles, not subtree payloads. It introduces
no dependency between sibling calculations: fill each destination slot by
its known old/new rank, then publish the completed sequence once. Prefix
placement is a data dependency, but a left-to-right loop through an entire
float-free sequence is not the shortest implementation of that dependency.

### B. Flat flow in chunks, parent-relative block origins, subtree skips

Retain a flattened Open/Close/Text/Child stream, but store entries and
payloads in stable chunks. Blocks keep parent, matching-close and next-sibling
handles. Paragraph pieces move to per-paragraph storage just as in A;
leaving them in one shifting array would invalidate the claimed edit cost.
A rank tree over chunks supports insertion without context-wide memmove.
Each block also needs a direct-child directory or equivalent skip index:
walking a singly linked sibling list merely to translate siblings would
add a serial O(s_i) chain that the translation does not need.

- **Full build:** classify/build local results -> compute chunk sizes by
  prefix -> fill disjoint ranges -> prepare paragraphs independently ->
  compute block boundary outputs and place siblings as in A. The rank/chunk
  directory adds a gather/index phase; it is a representation dependency,
  not a CSS dependency. Work O(all units + text), span of A plus the chunk
  index construction. A single shared append cursor is not recommended.
- **Insertion:** build E -> splice the containing chunk(s), O(E + chunk
  size + log(number of chunks)) -> repair matching-boundary and direct-child
  handles on the D path -> A's boundary propagation. Work O(E + T + S + F +
  R + G + chunk size + log(chunks)); unchanged sibling subtrees skip in
  O(1) each. The chunk rank update is an additional dependent path.
- **Font-size change:** W's affected entries/payloads -> prepare/break ->
  the same boundary propagation as A, skipping unchanged subtrees by their
  matching-close handles. Work O(W + T + S + F + R + G); no index splice
  unless generated box topology changes.
- **Text edit:** direct stable paragraph/piece handle -> text work -> the
  same cutoff/propagation as A. O(T + D) for an unchanged output, otherwise
  O(T + S + D + F + G). Paragraph order must come from the chunk sequence,
  not the stable payload arena's slot order.

B is viable, and with a direct-child directory it can have the same
geometric dependency graph as A. It retains a second order representation
and needs disjoint-scatter proofs when a loop writes payloads reached
through flat handles. A's owned children expose those writes directly to
Whitefoot. If B drops that directory or uses flat-array splicing, it adds a
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

## Recommended contract

Choose A, as Q109 directs. Use B as a differential iterator during the
migration, not a second retained order updated on every edit. The new
material choices are proposed here, not already implemented or owner
approved: local stable slots and boundary outputs (Q112), and the initial
splice's safe scope with explicit fallbacks (Q113).

### Ownership and lookup

Conceptually, the types are the following; this is a contract sketch, not
Whitefoot source to compile:

```
FlowBlock = style, parent_route, local_depth,
            normal_origin, own_relative_shift, used_size, width_inputs,
            slots<Block | Paragraph | Context>, sequence<EntryId>,
            boundary_output, dirty_children, local_split_fragments
Paragraph = existing shaped/line data + owned contiguous Piece storage
EntryId   = owner-local stable slot + generation (if slots are reused)
Route     = owning block/context route + stable slot
TextUse   = paragraph route + local piece range
StyleUse  = owning block/subtree route and explicit paragraph uses
```

The sketch can use separate typed Slots arrays and a tagged sequence, to
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
as the DOM; page-directory growth must also be amortized/reserved outside
the measured edit, or represented by a shallow radix directory. A table
shared by all elements is not a shared **mutation chain**: independently
known NodeIds write disjoint slots. If that independence cannot be proved
at the pin, resolve the minimal Whitefoot proof gap before replacing it by
a serialized global writer. Do not import Q111's style-slot identity as a
layout order.

After deletion, clear only removed routes and uses. Reuse requires a
checked generation or never-reused slots until compaction. Compaction is
an explicit full rebuild, off this edit path; it updates every holder
atomically. Existing `docs/todo.md` session-growth work owns its policy.

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
4. Allocate the replacement local sequence and changed route/use pages;
   stitch E in (or remove it). Publish only after all construction and
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

These are future implementation steps, not completed work. Each lands with
the full-build and incremental paths producing exactly the same dump,
including fragment order; a partial performance improvement never permits
a rendering difference. Line ranges are estimates of changed/added source
and focused checks, overlap between steps, and are not measured velocity.
No Whitefoot implementation change is included in the estimates.

| Step | Change and estimated lines touched | Check | Required falsifier |
|---|---|---|---|
| 1. Decouple identity from order | 700–1,100: `module.wfm`, `build`, `prep`, `structure`, `style_update`, `update`. Paragraph-owned pieces; stable owner/entry/context slots and routes; explicit order queries. Keep the current flat walker through an adapter. | Full dumps on all three pages and five focused layout pages; every prefix of existing text, font-size and block scripts compared with a fresh full build; repeated insert/delete before one sibling, plus a style edit and a text edit after each splice. | Retain numeric-slot ancestry, omit one text/use route repair, or let a newly appended paragraph use numeric predecessor order. Each must fail its focused case. Mutation of the last piece's range must fail a multi-piece paragraph case. |
| 2. Make geometry owner-relative | 900–1,500: `flow`, `update`, `columns`, `table`, `flex`, `grid`, `inline`, `module.wfm`, dump checks. Centralize normal/visual/context coordinate conversions; table content origin; anchored fragments/naturals/baselines. Initially stack through the full reference walker and convert resolved outputs. | Byte-identical full dumps, seq and par, including negative margins, relative ancestors, positioned/fixed children, table alignment, split inlines and columns. Add extreme/saturated coordinate cases. Measure placement separately. | Omit one ancestor origin, apply relative displacement twice, shift every nested table descendant, apply a column map before accumulation, or reassociate a saturating sum. Each case must produce a dump difference. |
| 3. Replace flat ownership with nested direct sequences | 1,000–1,700: `build`, `flow`, `prep`, `structure`, `style_update`, `update`, `module.wfm`; small item-iterator adapters in `flex`, `grid`, `table`, `columns`. Stop retaining or rebuilding the flat stream on successful edits. | Same full-build outputs and edit-prefix checks; assert live unit totals against an independent walk; inspect the compiler's certified loops for sibling preparation and child layout. Full-build time is compared with the frozen M1/base source under the same pin, not just with step 2. | Reverse equal-order siblings, treat a float as block-contained, or leave a retained flat-stream rebuild on the edit path. Rendering catches the first two; physical-work counts and a wide/deep synthetic scaling case catch the last. |
| 4. Block outputs and bounded propagation | 800–1,400: `flow`, `update`, `columns` consumers and focused cases. Ordinary margin transfer composition/prefix; float influence replay; dirty-child frontier; translate only direct clean siblings. Font-size and text edits use this path before a structural splice does. | Generate small margin/empty/marker configurations with varied entering struts and compare the transfer composition with the original entry machine; independently retain Chromium rectangle cases. Every edit remains byte-identical to a fresh build. Report W, S, D, F and actual visits, including the prefix used to recover state. | Collapse a strut to one scalar, clear an incoming float at a block boundary, stop on equal height with a changed baseline, omit an ancestor-height update, or scan an unchanged descendant. Geometry cases catch state mistakes; an instrumented sentinel counter catches extra work. |
| 5. Publish a flow-range splice | 650–1,100: `structure`, `build`, routing/marking helpers, `oracle/layout/edit`, focused scripts. Private subtree build, local sequence swap, seam validation, targeted routing and count deltas, insert and removal. | Three pages' block scripts, `incremental-layout/scripts/block-case`, focused counter / `:nth-*` / `+` / `~` / float / collapsing-margin / split-inline cases. Compare every prefix with full build and serialized-source reparse, seq and par. Assert an explained refusal leaves the retained tree untouched. After each removal edit, issue another text/font-size edit to catch stale routes. | Disable the structural style frontier, fail to restack P's later siblings, skip a route tombstone, ignore outgoing counter state, or publish before seam validation. Each mutation must fail; an unexplained `inc refused` is not success. |
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

Q104 and Q109 are approved directions. Q112 and Q113 below remain open;
this research does not claim implementation approval for them.

- **Q112 — stable local slots and block boundary outputs (recommended).**
  This gives owned, independently writable siblings and removes every
  insertion-sensitive rank from retained identity. Local sequence arrays
  cost O(s_parent) handle copying; alternative chunk/rank trees avoid that
  for very wide parents but add indexing to all readers. Start with the
  local representation only if the census/E1 path sizes support it; reopen
  before accepting an edit that still scales with a large sibling run.
  Retain the ordinary margin transfer/prefix contract so a convenience
  left-to-right loop does not become the architectural dependency chain.
  Boundary outputs differ from the refused arbitrary stacking snapshots:
  they are the block's output contract, needed to decide whether its
  descendants may be skipped at all. Their exact minimal fields and
  compiler proof must be established in step 4, not assumed from this
  sizing run.
- **Q113 — a neutral complete-block seam first (recommended).** Counter
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
  vectors/outputs may cost more than today's packed arrays. A's dependency
  advantage does not establish its sequential speed or M2's 5% condition.
- **Reported work.** Recommendation: implement the physical counters in
  step 4 and retain historical columns only for comparison. The existing
  discrepancy is recorded in `docs/todo.md`; it must not be used to pass a
  locality gate.
