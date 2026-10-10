# M2 block fallback: dependency-driven relayout (proposal)

## Question, scope and prior rejection criterion

Can an inserted or deleted block that fails the local splice reuse unaffected
box results, so that **every fallback costs at most main's whole-context rebuild
and every X5 page/kind/mode costs at most 2x main**? These are rejection criteria,
written before implementation or new measurement, not predicted achievements.
The owner selected this direction in `sg-fallback-next`, option C. The choices
below remain proposed; this design implements nothing and adds no approval log.

Source baseline: `030e4dd4081c9c15699363bdfa0e57c53a7f761d` on
`research/m2-layout`. [PR 58, counted fallback construction](https://github.com/Ming-Research/Snowghost-wf/pull/58)
left the 22 Apollo11 fallbacks at 1.2631–1.3963x paired main despite local
construction savings. The [final tighter verdict](SPLIT-CONTRACT.md#final-tighter-construction-replicated-memory-and-verdict)
owns that historical measurement. It used `wf-41f46e60030c`; the inspected
baseline pins `wf-78223721f77d`. Its timing is not a measurement of this baseline
or of this proposal. Nothing here relaxes the [M2 structural contract](../structure-edits/DESIGN.md#criterion)
or the existing correctness, locality and full-build conditions.

The design replaces automatic reconstruction on splice refusal with the same
layout algorithms called over a retained dependency frontier. It must repair
**source construction as well as geometry**: `structure.wf:structure_changed`
currently rebuilds the nearest exact context checkpoint, copies directories,
then transfers prepared paragraphs. `reuse_prepared` does not retain the old
box layout. Merely caching the subsequent `update` leaves reconstruction cost.

Paths below are relative to `renderer/layout/` unless linked otherwise. The
[layout node](../../../design/pipeline/layout.md) and its
[pipeline ancestor](../../../design/pipeline.md) own maximal parallelism,
explicit inputs, pushed marks, parent-relative placement and the reference
arithmetic. This proposal narrows no supported CSS behavior. A `Block` is an
ordinary flow box inside a `Context`, not necessarily a formatting-context
root; a `Paragraph` is an inline unit, not necessarily one DOM element.

## Reference design and its limits

Sources read on 2026-10-10; source links below pin Chromium revision
`9f504d5ba1a3c7fd982cca80cc641fbdfc57930f`. No source code is copied.

- [LayoutNG overview and fragment caching](https://chromium.googlesource.com/chromium/src/+/9f504d5ba1a3c7fd982cca80cc641fbdfc57930f/third_party/blink/renderer/core/layout/layout_ng.md): the algorithm's inputs include node/style/children and constraint space; accessing unrepresented inputs breaks caching. The caching subsection describes an early, unfragmented implementation, not today's complete cache policy.
- [LayoutNG architecture explanation](https://developer.chrome.com/docs/chromium/layoutng?hl=en): explicit retained constraints and immutable output fragments support subtree reuse; separate measurement and final-layout results avoid repeated alternating passes. This motivates phase separation, not a claim that this design inherits Chromium's complexity bounds.
- [LayoutBox::CachedLayoutResult](https://chromium.googlesource.com/chromium/src/+/9f504d5ba1a3c7fd982cca80cc641fbdfc57930f/third_party/blink/renderer/core/layout/layout_box_hot.cc#72): checks dirty state, cache phase, size constraints and BFC inputs including margins, offsets, exclusion space and clearance, with additional fragmentation refusals. A hit is stronger than equal width/height.
- [Size and BFC cache eligibility](https://chromium.googlesource.com/chromium/src/+/9f504d5ba1a3c7fd982cca80cc641fbdfc57930f/third_party/blink/renderer/core/layout/layout_utils.cc#409): `CalculateSizeBasedLayoutCacheStatus` and `MaySkipLayoutWithinBlockFormattingContext` distinguish changed constraints from changed consumed inputs, including self-collapse and floats. Snowghost must prove its own rules, rather than import these predicates.
- [ConstraintSpace](https://chromium.googlesource.com/chromium/src/+/9f504d5ba1a3c7fd982cca80cc641fbdfc57930f/third_party/blink/renderer/core/layout/constraint_space.h#815): `MaySkipLayout` alone explicitly leaves size and BFC checks to its caller. A partial comparison is not a reuse certificate.
- [MeasureCache](https://chromium.googlesource.com/chromium/src/+/9f504d5ba1a3c7fd982cca80cc641fbdfc57930f/third_party/blink/renderer/core/layout/measure_cache.cc#13) keeps multiple measured results and checks requested constraints. Snowghost's proposed first step retains its existing item-owned measurement values and one materialized final result, not this cache implementation.
- [BlockNode::Layout](https://chromium.googlesource.com/chromium/src/+/9f504d5ba1a3c7fd982cca80cc641fbdfc57930f/third_party/blink/renderer/core/layout/block_node.cc#407) repairs a fragment spine when descendants changed even if a cached parent result remains usable. Snowghost likewise must publish changed descendant output when ancestor sizing stops; it does not need a copied immutable fragment tree to do so.
- [Block fragmentation](https://developer.chrome.com/docs/chromium/renderingng-fragmentation) describes fragmentation-aware layout and break-token continuation. Snowghost instead retains its current one-column layout followed by balancing. Adopting caching does not silently adopt a different fragmentation algorithm.

## Dependency model: keys, values and retained state

A key is the actual input tuple of a particular phase, not a DOM address,
a previous output size, or a hash accepted without equality. A reuse value
includes that phase's result and its validity/lifetime. Equality permits an
explicitly proved projection of an unread input; otherwise compare the complete
input. Marks identify which results to inspect; they do not replace equality.
A dirty ancestor can assemble a new result using clean descendants. It cannot
return its old subtree merely because its own style and incoming `Space` match.

### Common contract

Every phase reads its live source domain and kind, applicable style values,
ordered direct source membership, and referenced child results. Style group IDs
are sufficient only while they denote immutable values in the same interning
domain; rebuilding that domain invalidates their identity proof. DOM bytes,
generated content and replaced-element attributes are inputs when read, even
when their `StyleRef` is unchanged. Source versions mean owner-local validity
invalidated by every writer; they require neither a shared global epoch nor
per-frame version scans. No completeness proof is attributed to Whitefoot's
effect rows: they describe places read, not complete value-version keys.

The retained style inputs cover box, size, spacing, border, font, text,
container, item, table and content groups, plus background visibility where it
controls inline fragment emission; a colour-only change need not change that
visibility input. Font resource/pick changes invalidate affected preparation
even if a style group stays equal.

Size inputs are the six `Space` fields (`available`, `basis_width`,
`basis_height`, `forced_width`, `forced_height`, `shrink`), viewport values where
read, and height-source identity/definiteness, not just numeric height.
`HeightInput`, `HeightProof`, `HeightSummary` and `definite_free` already carry
part of this proof. A phase discriminator separates intrinsic query, natural
measurement, final layout, normal-flow placement and final column/positioned
placement. Preparation/geometry validity cannot be substituted for one another.

Published outputs include border/content dimensions and margins; intrinsic
min/max contributions when demanded; **both** first and existing last baseline
with availability; local lines/fragments and live topology references; height
read summaries; and the outgoing boundary state read by the enclosing flow.
Placement anchors and visual displacement are separate from reusable interior
geometry. Equal parent-facing measurements may stop sizing propagation while
changed interior fragments still must reach dump/paint and later edits.

| Box or phase | Inputs read: reuse key, in addition to the common contract | Outputs published: reuse value | Existing summaries and required additions |
| --- | --- | --- | --- |
| Ordinary block and flow context | Box/size/spacing/border/font/marker/relative-position/clear values; containing width and height source; ordered child transfers; incoming cursor, positive/negative pending margin strut, unresolved open-frame state, line presence, float floor/exclusions and coordinate basis. Context preparation also reads `FlowFrame` and child constraints. | `BlockOutput`, `SequenceOutput`, used dimensions, through/solid state, outgoing strut, first/last baseline selectors, intrinsic contributions, exported floats/reach, local origins and fragment dependencies; context publishes `flow_end` and final height. | `entries` reductions, `BlockOutput`, height proofs, range actions and `FlowInputs` exist. Add per-block phase input/output validity and exact incoming-state equality/resume certificates. `FlowInputs` certifies completed context flow only and structural splice invalidates it; it is not a general box cache. `flow.wf:prepare_spaces,stack_flow`; `boundary.wf`; `module.wfm`. |
| Inline / paragraph preparation | Piece order and boundaries; text bytes/scalars/generated bytes; open inline styles, whitespace collapse, text transform; fonts, matching picks and shaping inputs; atomic object identities. | Collapsed text, runs, shaped text, break opportunities, inline marks and intrinsic contributions. | Owned pieces/runs/marks/shaped data and text/style routes exist; `structure.wf:take_prepared` already checks reuse. Add source-domain validity covering seam split/join and generated-reference changes. No shared word-shaping cache. `prep.wf`; `text/`; `build.wf`. |
| Paragraph line layout | Prepared result, strut/font/line-height, indent, wrap/alignment, width and left; atomic child margin-box metrics and baseline availability; actual paragraph BFC origin and entering exclusions where floats are read. | Lines, fragment/atomic offsets, height, line-presence, first/last baselines and outgoing transfer; empty-inline and split dependencies. | `broken_width`, `broken_left`, `beside`, lines/fragments and frontier exist. Add a complete line-input certificate, including atomic-result freshness and float geometry at queried positions. `beside` is not an exclusion key. `flow.wf:break_paragraph`; `inline.wf:measure,break_lines,finish_lines`. |
| Flex container and item | Ordered active item membership; direction/reverse/wrap, gaps, align/justify and definite sizes (`FlexBox`); item order, basis, factors, auto min/max, margins, frame, ratio and overflow; intrinsic/natural child contributions and baselines; each actual measuring/final/stretch `Space`. | Line membership, resolved targets and cross sizes, placements, used container size, first/last baselines, intrinsics and child results. | Child-owned `FlexCache` retains setup/prepared item plus final-space cross/baseline values. Its `final_baseline` already stores the effective first baseline; add complete source/phase validity and preserve baseline availability in outward equality; do not treat retained stretched geometry as natural measurement. Changed membership can affect all lines even if width is equal. `flex.wf`; `splice_flex.wf`. |
| Grid container and item | Track/template/area/auto-flow definitions, gaps, stable item order/placement/spans; available and definite dimensions; intrinsic/auto-min contributions, baseline groups, alignment and current measuring/final area constraints. | Resolved columns/rows, natural contributions, final child results and placements, size and both baselines. | `GridRowResult` already retains natural height, margins and first-baseline availability under complete measuring `Space`; Q140 column/intrinsic certificates are limited proofs, not a general track cache. Add explicit track/placement input validity and child-output dependencies; final geometry remains separate. `grid.wf`; `grid_retained.wf`; `splice_grid.wf`; [Q140](../structure-edits/layout-design.md#q140-grid-row-sizing-under-invariant-columns). |
| Multi-column flow | `FlowFrame` column count/width/gap and normal-flow constraints; complete settled break-unit order/sizes, break-inside decisions and table-row geometry. | Balanced height, `ColumnPiece` map and mapped/split output rectangles; normal-flow child geometry remains reusable separately. | Existing `column_map` and `columns.wf:collect_units` exist; add validity linking the map to the current unit stream and shape. Float/Out entries are not independent column units in this algorithm. No break-token key exists because layout is not fragmentainer-driven. |
| Positioned child (absolute/fixed) | Nearest positioned containing block's identity, padding box and resolved dimensions, or viewport for fixed; inset values/auto flags, margins, static anchor for auto axes, intrinsic/natural child size and resulting forced `Space`. | Child interior result and separately its final anchor/viewport-origin flag; descendant positioned outputs after any final sizing. | `Context.anchor`, `block`, `placement_paragraph`, `has_out`, `viewport_origin` and height provenance exist. Add containing-block/static-input dependency links and separate placement validity. Equal child size does not prove equal anchor. `flow.wf:position_out_events,position_one`; table final sizing reruns positioned settlement. |
| Floated child and exclusion production | Interior: shrink-to-fit/intrinsic inputs and actual child `Space`. Placement: side, margins, containing left/width, prior exclusions, cursor/clearance/floor and BFC basis, including floats outside lexical owner. | Local child result; positioned float rectangle and outgoing `Exclusion`/floor/reach used by subsequent lines, floats and blocks. | `Exclusion` and transfer float handles/count/reach exist. Add exact entering/exiting exclusion-state validity and negative dependency on previously absent intersection. A count or maximum reach is insufficient to establish equal geometry. `flow.wf:place_float,narrow_beside,resume_float_state`; `inline.wf:exclusion_room`. |
| Table context, cells and captions | Table topology/spans; table/row/column/group/caption styles; fixed/auto mode, spacing and collapsed-border winners; cell/caption intrinsics; resolved column widths, row spans/heights and baseline groups; final child spaces. | Track/row geometry, cell/caption results, borders/fragments, content adjustment, size and baselines. | Context rows/columns/cells/captions and outputs exist; add contribution/phase validity before selective reuse. Structural grid repair may rebuild the table's topology while clean child interiors remain reusable under matching constraints. `table.wf`, `tablegrid.wf`, `tableborders.wf`. |
| Replaced/control context | Natural kind, alt/generated text where applicable, ratio attributes, font metrics for text input/marker, style min/max and used-size constraints. | Used size, natural/intrinsic contribution, baseline and own fragments. | `natural`, ratio fields and context geometry exist; add explicit attribute/natural-input validity. Reuse cannot rely solely on style-delta marks. `build.wf`; `flow.wf:lay_out_replaced`; `module.wfm:Context`. |

A certificate enumerates all reader inputs, the producer that invalidates each,
and consumers of every exported field before its implementation. This table
specifies that obligation; there is no existing universal result record to
switch on. `lay_out_child` currently reuses a clean result under
`equivalent_space` and `keep_height_proof`; the proposal extends that discipline
to the ordinary boxes and source domains that presently disappear on fallback.
Existing [consumed-input equality](../structure-edits/layout-design.md#full-layout-consumed-input-equality)
remains the only permission to omit differing flow height inputs: its inline,
height-reader, provenance and equal-used-height conditions remain conjunctive.
Other context kinds retain complete constraints until separately proved.

## Algorithm and propagation

### 1. Mark the complete edit closure

Record old parent/seam and retained routes before removal retires the node;
insertion records its new owner and adjacent inline sources. Consume the style
stage's actual structural delta, including affected siblings and descendants,
not just the inserted subtree. Use existing text/style routes and context paths
to mark source-construction, preparation, intrinsic, layout or placement work
separately. Mark owning blocks and context ancestors with descendant-work flags;
invalidate natural flex/grid measurements before any dirty bit can be cleared.
A second changed subtree is independent pending work, not something an earlier
ancestor cutoff may erase. No dense whole-document layout flag conversion is
required by this proposed interface.

Changing source membership marks the old and new dependency edges: adjacent
paragraphs, split runs, empty inline sources, float intersections, counter/quote
readers, containing-block users and grid/flex/table membership. A dependency on
an absent float, line or adjacency must be invalidated when it becomes present.
Existing reverse routes and interval summaries provide part of this discovery;
new seam/checkpoint and incoming-float certificates are required.

### 2. Repair source topology before asking to reuse layout

Use the existing neutral complete-block seam when it proves sufficient. On a
mixed-inline refusal, reconstruct the enclosing inline source domain: include
both affected adjacent paragraphs, their open-inline stack, generated pieces,
atomic ownership, split-run roles and negative adjacency dependencies. Find an
exact builder input checkpoint and continue until source/output state converges;
a DOM parent alone is not such a checkpoint. Add owner-local construction
checkpoints only where the builder's state is completely represented (style,
open-inline stack, pending paragraph pieces, counters/quote scope and depth).
The unchanged prefix is read-only. Counter/quote effects propagate in source
order to actual later readers and stop only at equal state at a valid boundary.

Retain source handles only when membership and meaning survive; newly split or
joined paragraphs receive fresh identities and routes. Retire every handle into
a replaced source domain, including split endpoints and cached phase values;
keep untouched context slots and payload handles. No DOM preorder, slot rank,
page address or equal rectangle identifies a reusable source. Source-domain
replacement may be wider than the visible inserted block.

Prepare replacement records and allocation/ceiling checks privately. Publish
route additions and retirements only for affected suppliers and text nodes;
preserve supplier predecessor and text last-writer semantics. Surviving route
records must not require copying the whole directory. Independent supplier
records can be prepared independently; precedence within one supplier's logical
source order is real. Allocating checked disjoint output ranges can use balanced
counts and prefix allocation, not a shared per-record append counter. The
earlier balanced supplier constructor was rejected for increased instructions
and missing parallel permission. This proposal concerns changed suppliers only,
not reinstating that complete reconstruction. Any new allocation reduction must
be justified independently; the existing multiple-result permission witness
remains an upstream requirement;
an alternate spelling to hide that compiler gap is not authorized.

If no exact construction checkpoint exists before a topology effect escapes,
widen to the nearest exact context checkpoint, possibly the root. This is an
explicit reconstruction limitation, counted separately from a geometric cache
miss, not a promise of locality. Retain child results only with independently
proved source correspondence; a fresh context slot does not inherit an old
certificate automatically.

### 3. Evaluate the dirty dependency graph

The upward dirty chain discovers affected ancestors; actual evaluation is
**parent constraints down, demanded child outputs up**. It is not a bottom-up
loop that reuses yesterday's containing width. At each marked ancestor rerun
its layout orchestration, requesting only the child phases it consumes. A clean
child returns its completed value when its source and phase certificate are
valid and its new consumed inputs equal the stored inputs. Otherwise run that
phase using the ordinary full-layout algorithm; publish the new certificate
only after all outputs settle. A changed intrinsic contribution may require
parent sizing first and then another child layout under its final space.

Compute independent text preparation, intrinsic queries and speculative
no-float line breaking concurrently wherever their inputs are available. The
flow walk composes exact owner transfers over unchanged runs. At the first
changed margin/float/width input, replay the affected entries and reuse each
interior whose key still matches. Resume from settled predecessor geometry and
live float exports, extending existing resume mechanisms; do not add a second
sparse snapshot scheme rejected by the layout node. Keep reference i32
saturation order. Exact i64 differences support admitted translations only;
outside the arithmetic proof, replay reference operations instead of inverting
clamped outputs.

| Changed output | Required propagation and stopping condition |
| --- | --- |
| Margins / empty-through state | Carry positive maximum and negative minimum separately, unresolved top and line/barrier state through following siblings and ancestor close. Equal total margin or equal used height alone cannot stop it. Stop when every downstream consumed boundary field matches. |
| Float placement / exclusions | Recompute intersecting line rooms and later float placement, including negative-margin re-entry. Child interior reuse is separate from float placement reuse. Continue through the BFC until outgoing exclusion/floor state and subsequent inputs converge; worst case reaches its end. Unchanged float count is no certificate. |
| First/last baseline or availability | Recompute consuming flex line, grid row group, table row or inline atomic metrics even if size is equal. Rebreak the paragraph if atomic line metrics change. Stop separately for each baseline consumer only at equality. |
| Height, intrinsic size or definiteness | Update containing-block proofs, auto minima, flex targets, grid tracks/rows and table rows as demanded. A definite/indefinite transition or changed source identity invalidates a read even at equal numeric size. Changed final space must reach child layout before outward equality is tested. |
| Normal origin only | Keep interior coordinates and use existing exact owner/range displacement. Resolve positioned static anchors explicitly; they are not ordinary range members. No descendant-wide absolute-coordinate writes. |
| Line presence / inline fragmentation | Repair split/empty role topology and all intersecting dependency intervals, even if old endpoints were unchanged. Preserve source order of outputs and the distinction between old-frame scratch and settled placement. |
| Column unit or shape | Rebalance the complete current column-unit stream and republish the map, even when normal-flow replay was local. Reuse unaffected interiors; remap affected final output. Equality of column count or container height is insufficient. |
| Interior fragments with unchanged outward metrics | Stop ancestor sizing where appropriate, but retain the newly published descendants and repair any enclosing fragment expressions. Sizing cutoff never authorizes dropping descendant output or clearing unrelated marks. |

Flex item measurements precede line formation/flexing and final child spaces;
per-line cross/baseline reductions precede stretch. Grid intrinsic/placement
work precedes column resolution, which precedes independent row measurements,
row/baseline reductions and final area layouts. Preserve Q140's independent
item proposals and balanced per-track reductions, including required phase,
span-group and water-filling order. Tables follow their existing column, cell,
row/span and final-alignment phases. Each parent recomputes its own aggregate;
it cannot replace a changed child's height by simply adding a delta.

### 4. Publish a complete current result

Keep retained owned geometry as the authoritative settled result; proposed
cache values refer to its live logical domain, not to scratch from an in-flight
pass. Commit changed payloads, phase values, anchors, boundary reductions,
fragment roles, columns and exact later-edit routes as one completed update.
Keep old values available until each old-frame consumer has finished; existing
`reference_phase`, touched-payload lists and range normalization rules remain.
Legacy full-scratch readers require the existing bridge. A bridge that still
scans the whole context is counted work and a performance liability, not free
cache lookup. Do not mark a failed/incomplete result reusable.

Parent summary reduction follows child publication. Disjoint child publication
is independent; publication of one owner must not read partially written child
summaries. Failure before commit leaves the old retained result intact; a
post-publication splice refusal (reason 10) starts from the complete current
state and **must not apply the edit again**. The new fallback completes its
remaining dependency work. Exhausted storage or an inconsistent input returns
the existing error rather than publishing a truncated result.

### Splice fast cases and remaining wide work

The existing splice is a sufficient proof that source repair is neutral,
constraints survive, and transfer/fragment/height/float changes can be published
locally. Keep every conjunct: stable routes/references, complete seam,
counter/quote neutrality, supported container, retained style frontier,
height/width proof, fragment validity, storage ceilings, numeric/through
conditions, float-motion and ancestor settlement. Failure means run the more
general evaluator, not weaken the splice predicate.

`splice.wf` and `splice_boundary.wf` distinguish reasons: 1 owner/route,
2 container, 3 inline/fragment seam, 4 generated references, 5 counters/quotes,
6 style frontier, 7 boundary dependency, 8 ceiling, 9 float dependency,
10 post-publication settlement, and 11 grid/enclosing input proof. One numeric
reason can represent several guards. Record the old reason plus the new
source-repair scope, phases run and reuse hits; a new successful fallback is
still part of the fixed old fallback cost cohort. Keep the historical path
fixture as a baseline classification; add new path observations without changing
its oracle expectations to conceal a regression in the original 38 splices.

The existing bulk copying and tighter route reservation decisions continue to
apply when an explicit whole-context reconstruction is required; the new local
source repair must not call those whole-directory constructors by default.

Whole-context **layout** remains possible when changed constraints affect all
its children, float influence never converges, or no safe arithmetic/boundary
resume exists. Whole-context **source reconstruction** remains when no exact
checkpoint bounds changed construction state or a context's representation/kind
is replaced. Counters/quotes can reach the root. Tables may rebuild topology;
columns retain a full unit/map pass. These are distinct costs. None excuses an
Apollo11 fallback above main: if such a path misses the target, the proposal is
rejected for M2 until the missing dependency certificate or algorithm is resolved.
No ordinary reason-3/7/9 refusal automatically demands whole-context rebuilding.

## True dependency chain and parallelism

The graph is: edit and structural style delta -> exact source repair ->
independent preparation/intrinsic results -> parent sizing constraints ->
independent child layout -> required margin/float/track/baseline settlement ->
parent output -> consumers at the next ancestor and final placement. Some
algorithms alternate measurement and constraint phases; retain both results
so final stretching does not destroy the natural value. Ancestors form a
partial order over demanded outputs, not a global scheduling queue.

Independent work includes separate changed subtrees with settled incoming
spaces, all paragraph preparation, speculative line breaking, child contexts
behind settled boundaries, flex items in one measurement/final phase, grid
item proposals at one sizing phase, cells after columns settle, positioned
siblings after their containing blocks/static anchors settle, and fragment
endpoint evaluation after publication. Represent these as disjoint owned
writes and read-only inputs at every available grain. Storage/compiler proof
limitations are recorded as gaps, never reasons to invent semantic ordering.

The remaining orders are forced: source adjacency and counters/quotes;
margin collapse and float placement through the same BFC; flex freeze rounds
and line membership; grid/table phase and span dependencies; column balancing
after its unit stream; and parent reductions after child results. Exact
transfer composition may shorten the flow chain only where its existing
numeric proof applies. A global cache, shared append cursor or broad
context-wide mutable borrow adds order that these algorithms do not require.
Worst-case affected work is still the whole context/document. The bounded-work
claim is proportional to repaired source, changed/read dependencies, required
algorithm reductions, lookup paths and actual publication—not merely dirty
ancestor depth, and not unconditional O(log n).

## Correctness and falsification before implementation

Use a fresh full style/build/layout on the edited document as the independent
incremental oracle after **each** operation, comparing the complete serialized
placed output byte for byte. It must not use the retained candidate's caches.
Require sequential and parallel output equality, all X5 kinds/pages, original
block sequences and insert/delete inverses, plus the existing 104-edit Apollo11
followup sequence and 20-edit retained-state fixture. Internal identity/route
lifetime observations supplement geometry; a following text, class and splice
edit must consume repaired state. Full and incremental equality alone cannot
validate a shared algorithm error: use `tests/layout/layout_oracle.mjs` and the
existing Chromium Q139/Q140 cases for observable margins, floats, percentage
heights, baselines, flex/grid/table and column/positioned geometry in the claimed
subset. Browser tolerance is its existing contract; byte equality is between
Snowghost runs, not between unlike browser serialization formats.

| Deliberate mutation / distinguishing fixture | Required failure observation |
| --- | --- |
| Suppress dirty marking for one outside sibling whose structural selector changes. | Full comparison differs after insertion; proves closure is not just the inserted subtree. |
| Reuse a paragraph with changed font/bytes or atomic first baseline while width and outer height stay equal. | Glyph/fragment or baseline geometry differs; preparation, line and atomic keys are independently exercised. |
| Omit height basis identity/definiteness or an actual percentage reader. | Equal-numeric-basis and stretch-transition fixtures disagree; retains Q139/Q140 falsifiers. |
| Replace natural grid/flex measurement with stretched final geometry. | Nested measure/final/measure sequence differs; same-size case alone is insufficient. |
| Compare only summed margins; omit through/line/barrier state. | Positive/negative empty-block chain changes following placement. |
| Reuse with a moved float or treat no old intersection as no dependency. | New intersection or negative-margin re-entry changes line breaks/clearance; full output differs. |
| Keep only first or only last baseline, or omit availability. | Multiline nested flex/grid/table/atomic cases shift alignment despite equal height. |
| Preserve a retired seam handle or omit paragraph join/split/empty role repair. | Mixed-inline insert/delete differs, or a following edit follows a stale route and differs. |
| Stop publication when parent size is equal. | Fixed-height parent with changed interior text/fragment differs in full dump. |
| Ignore new containing-block identity/static anchor, or move positioned items as ordinary range members. | Absolute/fixed and table-final-size fixtures differ on placement while interior size can agree. |
| Reuse old column map after one unit changes; omit its downstream fragment update. | Break near a balancing boundary differs even if total height is unchanged. |
| Reassociate saturating arithmetic or translate a sentinel as a coordinate. | Existing saturation fixtures differ from exact reference operation order. |
| Omit one text/style/context route or duplicate a reason-10 edit. | Following text/class/splice consumes wrong state; original edit plus inverse fails identity. |

Each new detector must fail for its intended omitted dependency, not an earlier
unrelated error, and pass unmutated. No new tests or renderer code belong to
this design-only change. Its hosted `make check` validates document form and
unchanged project integration, not the proposed algorithm. The matrix above
is a required implementation experiment, currently unexecuted.

## Cost predictions from existing evidence

The [final-trim attribution](q141-final-attribution.csv) identifies dense
retained-state work such as `record_units`, `publish_boundaries`, `fill_flow`,
route construction and origin readers. It predates the tighter construction;
its counts must not be presented as the latest source. The
[tighter phase CSV](q141-bulk-tight-phases.csv) gives the following totals over
the fixed historical IDs, in millions of instructions rounded to three decimals.
These are instruction sums, **not time ratios or measured reuse savings**.

| Old reason and operations | Main: reconstruction / layout / other | Tighter: reconstruction / layout / other | Prediction and what could reject it |
| --- | ---: | ---: | --- |
| 9: 1–6, 9–10, 17–20, 23–24, 39–40, 51–52 (18) | 761.266 / 3646.007 / 25.375 | 1181.585 / 3912.261 / 31.598 | Largest opportunity: retain prefix and unaffected interiors, settle changed exclusion consumers until convergence. Predict lower reconstruction and layout instructions; no guaranteed small frontier if floats keep affecting later content. |
| 7: 29–30 (2) | 5.928 / 3.662 / 0.642 | 16.263 / 5.406 / 1.241 | Small main rebuild makes overhead decisive. Predict elimination of unrelated directory reconstruction, then actual input/ancestor settlement. Even deleting all current layout work leaves excessive reconstruction: source retention is essential. |
| 3: 35–36 (2) | 84.725 / 405.323 / 0.703 | 130.067 / 434.902 / 0.730 | Rebuild the inline seam domain and preserve unrelated paragraphs/contexts. Predict removal of most repeated interior layout only if exact seam correspondence can be proved; a context-wide source domain would limit savings. |

The path inventory records only a broad refusal code, not the exact failing
subguard or affected-unit cardinality. Do not claim these edits all fail a
particular margin, width or float condition without a trace. Existing profiles
contain neither new-key hit rates nor construction-frontier sizes; assigning
numerical latency or a particular sub-1x result now would invent evidence.
The historical elapsed-cost deficit requires a 20.8–28.4% reduction from that
tighter source to reach paired main; this is a required saving, not a forecast.
The falsifiable prediction is that avoiding unaffected construction **and**
layout supplies enough saving to offset key/frontier/publication work. Measure
those terms separately and reject the cost claim if it does not.

The historical final tighter controls already pass 2x. For all six X5 kinds:

| Kind | Prediction relative to the current design; risk to measure |
| --- | --- |
| Block | Preserve the 38 admitted Apollo11 splices and existing small ECMA262/HTML5 splices; reduce the fixed 22 fallbacks by reuse. New dispatch/key overhead must not slow admitted edits beyond the X5 bound. |
| Word | Same paragraph preparation and equal-output cutoff remain; no page-wide key scan. Expect similar cost, with any added lookup work charged. |
| Sentence | Same changed paragraph plus actual flow/float/split closure; expect similar or lower layout work. HTML5's current sequential worst paired ratio is 1.4130x, not a new prediction. |
| Colour | Paint-only changes must bypass layout keys/preparation; expect unchanged layout work. Small baseline edit times make added fixed bookkeeping visible. |
| Font size | Reuse settled sibling constraints and scoped column replay, preserving height/baseline proofs. Expect similar or lower layout work; HTML5 four-worker 1.7696x is the closest historical control to 2x. |
| Root font | May invalidate most text and lengths; no small-frontier promise. Preserve existing sparse frontier advantages on ECMA262; HTML5's dense changed work remains. Expect no improvement solely from block fallback caching and measure additional metadata cost. |

Implementation measurement protocol: GitHub-hosted CI only; first time two small
forward/inverse samples and inspect spread, then choose a finite interleaved
batch. Freeze main, same-source before, candidate, independent twins, compiler,
fonts, captures, complete edit scripts, machine/settings and seq/four-worker
modes in one runner. Compare per-edit total latency without full oracle work
inside the timed edit; identity runs are separate. Preserve all preceding edits.
Keep native phase timing, exclusive instruction attribution, actual key hits,
replayed units, route publications, source/geometry reconstruction counts and
memory/full-build observations. Zero-edit and attribution negative controls
remain required. Do not sum inclusive profile costs or medians of phases.

Reject if any paired 22-ID fallback median exceeds 1x main, **or any individual
historical fallback ID's repeated paired median exceeds 1x**; report reason
families too, so the small reason-7 pair is not hidden by the aggregate. Reject
if any X5 page/kind/mode paired median exceeds 2x. Evaluate each ordinary/twin
pair and round without pooling away failures. Twins diagnose noise, not waive
the threshold; inconclusive spread calls for a justified repeat, not acceptance.
Reject any correctness/lifetime/parallelism contract violation irrespective of
time. Keep the prior M2 full-build bound; measure retained memory and report
any regression separately. No benchmark/page identity may select code paths.
This task performs no new measurement, local check or self-hosted execution;
CI may be polled at most once per five minutes and never with a watch command.

## Interaction with Paged adoption

`research/m2-paged` was inspected at
`ee58302d1f9efcf50fa9832acdb729794f868c46`, an independent historical prototype
with `wf-exp-496186df5346`, not a pin or implementation to copy into this branch.
The layout node's `sg-pooled-store` decision assigns current storage adoption
to that work. This design neither moves its pin nor edits its implementation.

The semantic interface is live stable handles, owner-local ordered iteration,
read-only phase input views and disjoint result destinations. Keys exclude
page size, address, capacity, tree balancing, physical slot rank and borrow
identity. Deletion retires handles; it cannot silently reuse a slot for a new
source. Geometry remains owner-relative and source-domain lifetimes remain
explicit, whichever backing store supplies these operations.

Concrete coupling: Paged's context-wide pools need the `(owner, slot)` inverse
relation to prove independent owner writes; a slot alone is insufficient across
owners. Growth requires reacquiring views/facts before their use. Source repair
allocates private/disjoint ranges before exposing outputs, retaining the same
ceiling/exhaustion semantics. New per-box keys/phase values should be owned by
those same logical payloads, not a parallel directory keyed by page address.
The prototype's dense route prefix initializes gaps on a high-index write;
that cost can defeat sparse publication and must be measured, not assumed O(1).
Its proof and performance state is not evidence for current compiler support.

Retained equality and full-oracle fixtures can be specified now. Implementation
of disjoint publication must use the delivered storage invariant and compiler
proof; if the natural form is refused, keep a minimal witness and request the
owning language/compiler work rather than add runtime uniqueness checks.
Compare storage-only and storage-plus-fallback cohorts with the same compiler
and sources when measuring integration, so Paged allocation gains or regressions
are not attributed to fallback reuse. Both efforts touch Context/Block/Paragraph,
route publication and source retirement; settle their ownership interface before
implementation, and retain both old/current geometry reader contracts.

## Owner decision cards

All cards below are proposed under `sg-fallback-next`; no board is changed by
this task. The selected high-level relayout direction already stands. These
cards choose its implementation contracts, in dependency order.

### Source reconstruction boundary

**How should a failed splice repair source topology?**

**Background.** A layout-only cache still pays `structure_changed`'s complete
context construction and routing. Mixed inline edits can split/join paragraphs;
an arbitrary DOM parent does not carry an exact builder checkpoint.

**Options, dependencies first.**

- **A — Recommended:** retain unchanged source domains and repair from exact
  owner-local checkpoints through state convergence. Dependencies: changed
  source/order and incoming builder state -> seam repair -> independent prepared
  units -> route publication. Cost: new checkpoint/seam and route-lifetime proof.
  Risk: a valid boundary can be large, and missing checkpoints still require
  explicit context reconstruction; the cost gate may reject the result.
- **B:** rebuild the enclosing source context on every refusal, then match old
  and new child results. Dependencies: complete context walk -> correspondence
  and full route reconstruction -> reusable layout. Cost: simpler source
  transaction, but retains broad work before otherwise independent descendants.
  Risk: reason-7 reconstruction alone already exceeds main's entire budget in
  instruction evidence. Not recommended as M2's final mechanism.

**Confidence 4/5.** Code and profiles establish why source retention is needed;
exact local builder boundaries for all 22 cases remain untraced.

### Reuse equality

**How should input equality be established?**

**Background.** Equal outer size misses float, height-provenance, baseline and
fragment changes. Current height projections are proved only for specific flow
cases; effect rows do not prove a memoization key complete.

**Options, dependencies first.**

- **A — Recommended:** phase-specific explicit keys, complete comparisons by
  default, and only existing or separately proved consumed-input projections.
  Dependencies: local source validity + settled inputs -> local comparison;
  no shared cache/epoch. Cost: audit every phase's reads and retain its inputs.
  Risk: conservative misses until further equality proofs are justified.
- **B:** record exact dynamic read sets/values for each phase and compare them
  on reuse. Dependencies: old control reads -> validate their values -> replay
  if any differ; local records can remain independent. Cost: instrument every
  relevant read, including control/topology/negative reads, and maintain
  conditional-read lifetimes. Risk: incomplete tracking silently reuses stale
  output; no such recording mechanism exists here. Not recommended now.

**Confidence 4/5.** A extends inspected contracts without a new tracking runtime;
a demonstrated complete low-cost dynamic reader model could reopen it.

### Phase retention

**What should be cached across measure and final layout?**

**Background.** Flex/grid may ask the same child for natural and stretched
results. Current `FlexCache`/`GridRowResult` retain measurements separately;
using final geometry as a natural contribution is wrong.

**Options, dependencies first.**

- **A — Recommended:** retain the demanded intrinsic/natural values and one
  materialized final result per logical owner, with explicit phase validity.
  Dependencies: same real parent sizing phases; item caches are independent.
  Cost: bounded records and possible repeated materialization under alternating
  final constraints. Risk: scalar measurements may not avoid every repeated
  deep layout, which the visit/cost evidence must detect.
- **B:** retain multiple complete phase result trees per owner. Dependencies:
  the same sizing phases, with additional local lookup/allocation/publication;
  no shared eviction policy is required. Cost: more memory and fragment/route
  lifetime machinery. Risk: retained variants increase invalidation surface;
  they may reduce deep repeated work if A misses the target. Not recommended
  without evidence of repeated distinct materialized constraints.

**Confidence 3/5.** Existing item measurements make A concrete, but the affected
frontier and alternating-pass costs have not been measured.

### Publication ownership

**Should reuse require a new immutable fragment tree?**

**Background.** Snowghost already has owned payloads, anchored fragments, range
actions and explicit old/current scratch states. Equal ancestor measurements
must not discard a changed descendant's result.

**Options, dependencies first.**

- **A — Recommended:** keep owned retained results, prepare replacements before
  commit, and repair changed ancestor summaries/fragment dependencies. Dependencies:
  settled child outputs -> each consuming summary; disjoint outputs need no
  shared order. Cost: audit all readers and transactional validity. Risk: a
  legacy whole-context bridge can dominate despite local layout.
- **B:** introduce immutable result trees with structural sharing and rebuild
  each changed ancestor spine. Dependencies: child results -> parent tree node;
  independent branches remain independent. Cost: new allocation/lifetime model
  and adaptation of every placement/dump reader. Risk: duplicate representation
  and reference-bridge cost during migration. Not recommended without evidence
  that current ownership cannot expose the required independent publication.

**Confidence 4/5.** Existing anchors and consumers support A; an unresolvable
ownership/proof limitation would require returning to the owner, not a workaround.

### Fragmentation scope

**Should fallback reuse replace the column algorithm?**

**Background.** Current columns balance a settled single-column unit stream;
Chromium fragments during layout. Changing one unit can change the full map
without requiring all child interiors to be laid out again.

**Options, dependencies first.**

- **A — Recommended:** cache normal-flow results and retain complete balancing
  and map publication when units or shape change. Dependencies: settled units
  -> balance -> mapped placement. Cost: potentially whole-column-unit pass.
  Risk: it may remain a measured cost limit; it does not promise local balancing.
- **B:** adopt fragmentation-aware per-box results and break continuations now.
  Dependencies: fragmentainer constraints and predecessor continuation -> next
  fragment, plus balancing feedback. Cost: new behavior and contracts across
  all layout kinds. Risk: much broader correctness scope, with no profile
  showing it is necessary for these 22 fallback IDs. Not recommended in M2's
  fallback design; the existing column design's reopening conditions still apply.

**Confidence 4/5.** A preserves the recorded column semantics; a required page
or measured cost failure under those semantics could reopen B.
