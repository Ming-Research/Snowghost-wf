# M2 block fallback implementation plan

## 1. Scope, ownership and concrete changes

This is an implementation plan, not an implementation or new performance
result. The owner approved option A of all five cards in
[FALLBACK-DESIGN.md](FALLBACK-DESIGN.md#owner-decision-cards), and directed
implementation on the existing hand-written storage before Paged. Those
instructions supersede the design document's historical proposal wording.
The acceptance conditions remain every historical fallback at most 1x paired
main, every X5 page/kind/mode at most 2x main, and the existing correctness,
locality and full-build conditions. The design tree and design document are
unchanged by this round.

The code baseline is the layout architecture described by
[the layout decision](../../../design/pipeline/layout.md), its
[pipeline ancestor](../../../design/pipeline.md), and the
[structural criterion](../structure-edits/DESIGN.md#criterion). The inspected
pin is `wf-78223721f77d`, resolving in the local Whitefoot repository to
`78223721f77db615c950b6df1bcc690629f9fe4b`. Language obligations below refer to
that revision, not to what existing Snowghost source happens to compile.

Names introduced below are proposed internal records/functions. They are not
claims that these APIs exist. Paths without a directory prefix are in
`renderer/layout/`. No retained cache directory is added to `Layout`.

### Design steps mapped to code

| Design step | Existing owners and operations | Planned change |
| --- | --- | --- |
| Complete closure | `structure.wf:structure_changed`, `splice.wf:structure_splice`, `update.wf:mark_path,path_steps,prepare_marked`, `style_update.wf:mark_use,styles_restyled`; `TextUnit`, `StyleRoute`, `ContextPath`, `ParagraphFrontier` | Add a structural edit envelope containing the old and new seam identities, changed source suppliers, the actual sparse structural style delta and whether source publication has already happened. Add payload-owned phase marks and descendant-work summaries. Route marks to every old/new consumer before retiring sources; invalidate natural measurements before any dirty mark clears. |
| Exact source repair | `build.wf:Walk,Open,walk_element,end_paragraph,build_box,finish_tree_sequences`; `structure.wf:WalkPoint` helpers, `exact_walk_at,rebuild_of,reuse_prepared`; `splice.wf:build_splice` | Add `SourceCheckpoint` and `SourceRepair` logic in `build.wf`/`structure.wf`, owned by the affected Block/Paragraph/Context. Separate complete-block source neutrality from the splice's stronger geometry certificate. Repair only the invalid source domain; use exact checkpoints and equality of outgoing construction state. Existing whole-context reconstruction stays the explicit path when no exact boundary exists. |
| Dirty evaluation | `update.wf:update,update_child,update_flow_inner,update_flow_reference,restack_flow`; `flow.wf:prepare_spaces,lay_out_child,break_paragraph,stack_flow,resume_float_state,resume_open_frames`; `frontier.wf`; `box.wf:intrinsic_sizes,lay_out_context` | Add phase requests, complete input comparison and a per-owner evaluator. Parent orchestration supplies current constraints before child final layout; children publish demanded results before the consuming reduction. Extend ordinary-flow resume and equality rather than add a second snapshot scheduler. |
| Complete publication | `splice_publish.wf:splice_routes,publish_splice_routes,publish_splice_payloads,retire_splice_payloads`; `reference.wf`, `geometry.wf`, `range.wf`, `boundary.wf`, `fragment_repair.wf`, `fragment_topology.wf` | Prepare replacement payloads and route patches privately; preserve old-frame readers until finished; publish each completed payload, its validity and its dependent summaries. New `FallbackTransaction` is transient owned scratch, not a second retained tree. Publication is part of every increment that admits edits, starting with increment 1. |
| Splice fast case | `splice.wf:structure_splice,splice_inputs,splice_boundary`; `splice_boundary.wf:splice_sequence_plan,splice_path_ready,publish_splice_at,splice_finish` and `splice_motion.wf` | Preserve every existing admission conjunct and old reason classification. A successful splice is a certified source/phase/publication transaction in the same model. A refusal enters general repair/evaluation; reason 10 is already published and continues settlement exactly once. |

Update the affected `.wfm` contracts and
`renderer/oracle/layout/edit.wf:apply_structure_edit` and its edit producers
together when implementing the envelope. Capture removal identities before DOM
detachment and route
retirement, not by recovering yesterday's parent from today's DOM. The actual
driver call sites must pass that envelope through their insertion/removal path;
do not convert the sparse style delta into a dense document-wide array for the
new path. Keep the existing public reconstruction entry point usable for its
current callers while they migrate within the same increment.

`apply_structure_edit` currently maps a `structure_splice` error to numeric
reason 9. New observations must distinguish an actual float guard refusal
from that error path, preserving the underlying `LayoutError`; the historical
numeric cohort is retained for comparison. `changed_outside` currently refuses
an outside style delta, so it cannot serve as the new complete closure engine:
plan and mark each independently affected source domain before evaluating any
ancestor cutoff.

### Retained records live on their payloads

One materialized final result remains the existing geometry on each owner.
Optional, demanded measurement records are separate from that geometry. A
record's `valid` says its completed result belongs to a live source and phase;
it is not, by itself, an input key. Complete equality applies to the tuples
below. No key contains page address, capacity, AVL rank, allocator identity or
a shared global epoch. A source revision is owner-local invalidation evidence;
it cannot excuse omitting a producer or a consumed input.

| Owner and proposed fields | Key contents | Result and current storage |
| --- | --- | --- |
| `Block.source`, `Block.checkpoints`, `Block.phase_marks` | Live logical source, kind, direct ordered membership; checkpoint's exact builder state | Surviving `entries`, style and topology; entry/exit construction certificates. Checkpoints are indexed only within this owner's affected source boundaries. |
| `Block.flow_result: BlockFlowResult` | Source/style inputs, containing width, full height provenance, ordered child transfers; entering cursor, positive and negative margin extrema, open-frame/line/barrier state, float exclusions/floor and coordinate basis | Existing `output: BlockOutput`, `boundary: SequenceOutput`, width/height, parent-relative origin and fragment dependencies. The new record retains the input tuple and completed outgoing state; it does not duplicate a subtree. |
| `Paragraph.source`, `Paragraph.preparation: ParagraphPrepResult` | Exact pieces/order/boundaries, bytes/scalars/generated content, inline style stack, whitespace/transform values, font/pick resource validity and atomic identities | Existing `text,runs,run_styles,marks,shaped,min_content,max_content`. `take_prepared`'s piece equality remains useful but is not sufficient when referenced bytes or fonts changed. |
| `Paragraph.line_result: ParagraphLineResult`, `Paragraph.phase_marks` | Completed preparation identity; font/strut/line-height/indent/wrap/alignment and background visibility; width/left; each atomic's current margin-box metrics and both baseline availabilities; actual BFC origin and exact entering exclusion input | Existing `lines,fragments,atomics,height`; line presence, first/last baseline and transfer. `broken_width`, `broken_left` and `beside` alone do not authorize reuse. Speculative no-float and actual-float requests have distinct phase inputs; only the final materialized lines are retained. |
| `Context.source`, `Context.phase_marks`, `Context.descendant_work` | Live source/kind, actual direct membership, exact construction entry/exit validity | Existing child tree and source records; `walk_exact,entered,left` remain valid only for genuine checkpoints. A context created by neutral `build_splice` does not become exact merely by keeping its geometry. |
| `Context.intrinsic_result: IntrinsicResult` | Intrinsic phase, source/style inputs, actual basis and child contributions, replaced inputs where read | Existing `min_content,max_content,intrinsic_known,intrinsic_basis` plus validity and complete key; allocate/compute only when demanded. |
| `Context.final_result: ContextFinalResult` | Final phase, source/style and demanded child output inputs, all six `Space` fields, viewport where read, `HeightInput`/`HeightProof` identity and definiteness | Existing width/height, margins, first and last baseline plus availability, `height_summary`, local fragments and final child geometry. Keep `laid`, Q139/Q140 proofs and `definite_free` conjunctively; `FlowInputs` remains a completed-flow certificate, not a universal key. |
| Child `Context.flex_cache` and `Context.grid_row` | Extend `FlexCache`/`GridRowResult` with source/phase validity, complete measuring constraints, consumed style and child contributions, baseline availability | Retained prepared flex item/natural cross measurement and grid natural row values; final/stretch geometry remains in the one materialized result. Add first/last information only where a consumer requests it, without changing existing last-baseline meaning. |
| Container `Context.flex_inputs`, `Context.grid_inputs`, `Context.table_inputs` | Ordered active membership, relevant style groups, sizing/placement definitions and consumed intrinsic/natural child outputs | Validity of flex line orchestration, grid tracks/areas and table topology/contributions; their ordinary algorithms still own reductions. No shared per-item cache and no second cell or track ownership directory. |
| Floated child `Context.float_result: FloatPlacementResult` | Interior result, side/margins, containing left/width, exact prior exclusions, cursor/clearance/floor and BFC basis | Existing anchor plus exact exported `Exclusion` and floor/reach; this placement result is separate from interior final validity. |
| Positioned child `Context.position_result: PositionedResult` | Containing-block identity and padding geometry or fixed viewport, insets/auto flags, margins, static anchor, intrinsic/natural inputs and forced `Space` | Existing `anchor,block,placement_paragraph,viewport_origin`; dependencies link to their actual producers. Parent-size equality cannot retain an obsolete anchor. |
| Column `Context.column_result: ColumnResult` | Settled normal-flow unit stream/order/sizes, break-inside and table-row inputs, count/width/gap | Existing `column_map` and mapped/split fragments. Rebalance the complete stream when any key component changes. |
| Replaced/control `Context.natural_result: ReplacedNaturalResult` | Natural kind, ratio attributes, alt/generated text, control/font metrics and applicable size constraints | Existing `natural,ratio_width,ratio_height`, intrinsic/natural contribution and own baseline/fragments. Attribute changes enter source invalidation even when style IDs match. |

Common style input records name the consumed box, size, spacing, border, font,
text, container, item, table and content groups and background visibility when
it controls fragment emission. Group IDs are compared only inside an unchanged
immutable interning domain. A full style-domain replacement invalidates those
records or compares the actual values; an old mutable `Styles` reference is
not a snapshot. Font/pick replacement invalidates affected preparation.

Before enabling each key, write its reader/producer/consumer audit beside its
implementation: each field read by the ordinary phase, which mutation changes
it, which mark/validity it invalidates, and which exported value its consumers
compare. The initial producer checklist is:

- `patch_pieces`/text updates invalidate the paragraph's preparation,
  intrinsic, lines and consuming ancestors; source split/join retires its old
  identity and all those records.
- `mark_use`/`styles_restyled` and the structural delta invalidate construction
  when display/generated/counter/quote membership changes, otherwise the
  consuming prep, sizing, placement and fragment phases. Every changed
  outside sibling and descendant remains pending independently.
- Source repair invalidates membership, adjacent paragraphs, empty/split roles,
  atomic ownership, affected route suppliers and negative adjacency inputs;
  counter/quote changes invalidate downstream construction readers.
- `prepare_spaces`/parent sizing writes invalidate actual `Space` and height
  provenance consumers; intrinsic/natural result changes invalidate flex/grid/
  table orchestration. Clear `flex_cache` and `grid_row` validity before clearing
  marks, as their existing `*_forget` discipline requires.
- `place_float` changes both present and previously absent intersection inputs;
  width/origin/clearance changes revalidate those inputs even if a paragraph
  used to be full-width. `BlockOutput.reads_floats`, a count or maximum reach
  alone is insufficient.
- Changed local fragments invalidate consuming fragment expressions even when
  both baselines and dimensions match. Changed anchors/containing blocks
  invalidate positioned placement; changed units invalidate complete balancing.

Exact exclusion equality initially compares all fields of the live entering
exclusion stream and its BFC basis, including the empty stream. Derive that
stream from stable float exports and settled predecessor state, using existing
resume machinery. Concretely, the incoming certificate names its BFC, stable
entry boundary and source/order validity. Each floated child owns its completed
`FloatPlacementResult` export (identity, side, top, bottom, edge and coordinate
basis). Before changing that export, retain its old value in that child's
transactional replacement record until old-input comparisons finish. Deleted
float exports and removed source spans move into `FallbackTransaction` scratch;
the affected owner's old seam membership stays available there until commit.
Reconstruct the old incoming stream from unchanged exports plus those retained
old exports and the old source seam; reconstruct the new stream from current
settled exports and current membership. Compare length, ordered identities,
every exclusion field, floor/reach and basis. An unchanged handle read through
mutated current geometry is never an old input. The old seam also distinguishes
an empty old stream from a newly present float. This is old-value retention for
the current transaction, not a persistent second snapshot/resume scheme. Do not
copy the entire BFC exclusion prefix into every box. A later narrowed query projection requires
its own proof of positive and negative reads; until then charge complete
comparisons and conservative misses. Source membership and ordered child-result
comparison likewise follow actual logical entries, with unchanged-run
certificates only where every relevant writer invalidates the owner summary.

During an alternating measure/final request, a materialization that has been
overwritten is not reusable under its pre-edit input certificate. Keep interim
line/final validity false until that phase completes, then replace its input
certificate with the exact inputs that produced the current materialization.
Comparisons target that materialization, not always the transaction-start
stream; demanded scalar measurements retain their separate phase keys.

## 2. Dependencies and publication contract

The overall graph is edit/style delta -> exact source repair -> preparation
and demanded intrinsic/natural results -> parent constraints -> child final
results -> flow/container settlement -> parent outputs and final placement.
This is a request graph with alternating phases, not a bottom-up dirty loop.

| New work | True predecessor dependencies | Work that remains independent; forbidden extra ordering |
| --- | --- | --- |
| Closure proposals and marks | Old routes/seams and the actual edited style delta; marks at a shared ancestor are a union | Each changed supplier produces a private mark proposal. Reduce common ancestor summaries; process disjoint descendants separately. Do not scatter all work through one mutable `Context` or append to one global queue. |
| Checkpoint capture and source repair | Source order, open inline/pending paragraph state, counter/quote scope and depth; outgoing state equality is needed before stopping | Exact independent source domains with settled incoming state build privately. Piece decoding and paragraph preparation need only their own pieces. No shared builder cursor between unrelated domains. |
| Route patch preparation | Completed replacement source identities and affected supplier order | Different suppliers and text nodes produce records independently. Within one supplier preserve predecessor ordering and text last-writer semantics. Counts and disjoint ranges precede writes; no per-record shared append cursor. |
| Intrinsic/preparation/line requests | Own source/style/font input; child intrinsic or atomic metrics when actually consumed | Counted disjoint owner writes; speculative full-width paragraph breaking is independent before float settlement. Demand does not imply preparing every paragraph. |
| Ordinary block spaces | Parent's resolved containing width and height provenance | Once parent inputs settle, each child derives its own space. Recurse over nested owners instead of using a shared pre-pass stack to order unrelated siblings. Existing compatibility pre-pass is explicitly counted when still required. |
| Flow replay and float placement | Preceding unresolved margins, lines/open frames and exclusions in the same BFC | Reuse/interior work with already settled inputs is independent. Certified exact transfer composition and read-only prefix queries can shorten the chain. Float and margin effects cross lexical block ownership; the BFC is the dependency domain. |
| Flex | Item measurements -> line formation/freeze rounds -> cross/baseline reduction -> stretch/final spaces | Items within a measurement/final phase and distinct settled lines are independent. A changed membership can require every line; no scalar height-delta shortcut. |
| Grid | Placement/intrinsics -> columns -> natural row measurements -> row/baseline reductions -> final areas | Preserve independent item proposals and balanced per-track reductions, with genuine span-group/water-filling order. No shared track accumulator during item proposals. |
| Table | Topology/border winners -> columns -> cells -> row/span/baseline reduction -> final alignment/positioning | Independent cell/caption contribution and final layouts once constraints settle. Table topology may rebuild without destroying clean cell interiors whose source correspondence survives. |
| Column and positioned output | Complete current normal units before balancing; settled containing block and static anchor before positioned placement | Column units' interior layout and positioned siblings with settled inputs remain independent. Complete balancing is intentionally retained. |
| Publication and counters | Prepared replacements and all old-frame reads complete -> payload publication -> consuming summary | Disjoint payload writes and fragment endpoint evaluations are independent. Counters are per-operation results reduced after work, never a shared mutable diagnostic accumulator inside parallel loops. |

`SourceCheckpoint` must represent more than today's `WalkPoint`: `Walk`
counters/quote depth/element depth and list-counter interpretation, plus
`Open.style`, open inline stack, pending pieces/size/emission state, owning flow
boundary and split/atomic construction state. A complete-block boundary may
certify empty pending inline state and neutral counter/quote effects instead
of retaining nonempty state. General inline checkpoints must represent it
exactly. Store semantic identities and owned state, never borrowed storage
addresses; compare both source correspondence and exit state before reusing a
later domain. An arbitrary DOM parent is not an exact checkpoint.

The checkpoint also accounts for `Walk.effects`, `list_item` interpretation
and skipped-text producer bookkeeping. Their representation need not retain
irrelevant diagnostics, but resumption must reproduce neutrality and route
emissions, including text that previously produced no piece.

Every admitted edit uses this transaction contract from the first increment:

1. Snapshot only required old boundary inputs, routes and old-frame geometry.
   Prepare replacement source, all fallible phase results, allocation bounds and route
   patches privately. Complete fallible text preparation and all recoverable
   consistency/ceiling checks before retained publication. Allocation failure
   follows the existing error contract; it never publishes a truncated result.
2. Run any remaining old-frame consumers before replacing their inputs.
   Existing `reference_phase`, touched payload lists and normalization remain
   authoritative. A compatibility bridge can materialize complete scratch, but
   its full scan is charged; it is not a key hit.
3. Enter an internal commit phase after every recoverable failure is excluded.
   Install prepared source replacements through the existing mutation functions;
   then run the ordinary nonfallible geometry core on that current source,
   retaining old values needed by comparisons until their consumers finish.
   No dump, paint, next edit or successful return may observe this intermediate
   state, and no validity bit licenses it as a completed result. Only after
   geometry settles publish completed payload replacements, their source lifetimes,
   anchors and phase certificates. Retire replaced handles, split endpoints
   and routes. Repair consuming boundaries/fragment roles only after their
   child results exist. The update becomes externally complete only when all
   geometry and later-edit routes agree; preparation success alone is not
   completion.
4. Clear only the completed pending phase/descendant marks. Equal outward
   measurements stop that consumer's sizing work, not descendant publication
   or a second dirty branch. Failed/incomplete results are never reusable.
5. Distinguish `Unpublished` and `PublishedNeedsSettlement` in the transient edit
   state. Reason 10 begins from a complete already-published source edit; the
   fallback settles remaining dependencies without detaching/inserting again.

The plan does not use private preparation as a pretext to copy the complete
old context. Private scratch owns replacements and the old values needed by
their consumers; unaffected payloads stay in place. If the current ownership
or accessor contracts cannot express independent preparation/publication,
section 4's witness blocks that operation rather than introducing a serial
whole-context mutation or a replacement storage implementation.

`update.wf:prepare_marked`/`reset_paragraph` currently mutate retained paragraphs
before fallible preparation completes; the new transaction cannot call that
path unmodified. Add a paragraph-local private preparation helper using
`prep.wf:prepare_paragraph` with immutable previous input and a distinct owned
output, then install it only in the internal commit. `lay_out_context` and the
ordinary flow geometry core currently return `unit`; this plan uses that
nonfallible settlement contract after preflight, not a claim that their outputs
were all computed privately. Any new recoverable error found in that core must
move before commit or prepare its own replacement privately. It may not return
with partially changed retained state. Source-seam mutations within one owner
have their real topology order; disjoint geometry and supplier work remain
subject to the independent-write proof gate.

## 3. Ordered, individually testable increments

Each increment preserves all existing behavior through the ordinary algorithm
when its new semantic certificate is unavailable. This is staged implementation
of the approved reconstruction policy, not a new permission to conceal a
Whitefoot refusal. An unsupported optimization reports its source scope and
ordinary phase work; the final M2 gate still rejects any historical fallback
above 1x. Every increment has complete publication for the edits it admits.

The first three increments attack the measured opportunity directly: the
18 reason-9 operations dominate construction/layout work; reason 7's two
operations require source retention even if layout became free. Reasons are
diagnostics, never runtime dispatch keys for benchmark-specific behavior.
The exact failing subguards and local checkpoint sizes must be traced before
claiming coverage of a historical ID.

### Increment 0 trace

Before implementing increment 1, trace the 60 original Apollo11 X5 block
operations against the preserved page capture and unchanged path inventory.
The question is whether the 18 historical reason-9 refusals have a neutral
complete-block source seam despite their geometry refusal, and how much source
the exact fallback checkpoint rebuilds outside the edited subtree. The trace
records actual failing guard locations and predicates, checkpoint identities,
existing and constructed payload/route counts, source-neutral evidence, and
the specific floats and consumers behind each reason-9 dependency.

These criteria precede the run. If more than half of the 18 reason-9 operations
require mixed-inline or stateful source repair, move the corresponding work
from increment 4 or 9 ahead of neutral-source retention. Any source-neutral
classification that lacks a complete seam/state proof leaves that operation
unsettled; missing data does not count as neutrality. If reason 7's two edits
require a different construction boundary, bring that required checkpoint work
forward as well, since their reconstruction budget remains decisive. If the
reason-9 cohort is predominantly neutral and rebuilds substantial unrelated
source, keep increments 1 and 2 first. An error mapped to numeric reason 9 is
reported separately and requires diagnosis before selecting float work.

Diagnostic instrumentation follows `fallback-phase.py`: it is applied only to
a private CI source tree, with exact guard anchors and an archived source diff.
The ordinary renderer and oracle contain no switch, trace field or branch when
this patch is absent. The diagnostic applies to structural edits generally;
the workflow's Apollo script selects the observation cohort, not renderer
behavior. Read-only source/geometry inspection adds trace work in that build
without admitting a splice or altering reconstruction. Both ordinary and
instrumented oracles must pass the unchanged path/correctness fixture and have
equal ordinary checking output after diagnostic records are removed.

The temporary `fallback-trace.yml` hosted workflow produces
`fallback-trace.csv` and a summary grouped by exact guard and source scope.
Its results are diagnostic evidence, not latency or instruction measurements.
The workflow and its temporary helpers are removed before readiness after the
evidence is archived. Hosted runners provide correctness, instruction counts
and traces; later precise timing runs on the 14900K through the coordinator's queue.

An unproved outside construction correspondence is reported separately from a
demonstrated mixed-inline or counter/quote seam; it cannot by itself establish
that wider reconstruction is necessary. Missing float-proof contributors fail
the trace instead of supplying an inferred consumer.

[Hosted run 38186480413](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38186480413)
at `aaec00a` verified all 60 operations against fresh full layout with unchanged
paths and ordinary output: 38 admitted, 22 refused. All 18 reason-9 edits and
reason-7 IDs 29/30 are complete-block source-neutral and fail
`splice_motion.wf:171 motion_above` at `reach > floor`; together their
checkpoints reconstruct 16,356 blocks / 34,122 paragraphs / 13,322 contexts /
218,124 routes, including 16,346 / 34,112 / 13,322 / 218,104 outside the edited
subtree. IDs 35/36 fail the `splice_inputs` owner mismatch with an incomplete
source seam and reconstruct 1,817 blocks / 3,791 paragraphs / 1,480 contexts /
24,234 routes together. Increments 1 and 2 remain first: neutral source
retention addresses 20 of the 22 refusals and avoids reconstructing nearly all
of their unchanged source; the remaining mixed seam requires later checkpoint
work. These source counts establish the selected order, not a performance gain.

### Increment 1 — Retain complete-block source on a geometry refusal

**Change.** Separate `structure_splice`'s source-neutral complete-block proof
from its boundary/float settlement proof. Add the structural envelope and
phase closure described above; wire its old seam capture into the existing
driver path. Factor the private builder/route patch and publication operations
already in `build_splice`, `splice_routes`, `publish_splice_payloads` and
`retire_splice_payloads` so a source-neutral seam can retain unchanged
Block/Paragraph/Context identities even when geometry fails the splice.
The factorization must not relax the original splice predicate. It admits
source retention by semantic seam/state evidence, regardless of numeric reason.

For this first path, keep exact neutral source checkpoints, source/preparation
validity and complete affected route patches. Do not add an incomplete geometry
key: run the ordinary required layout orchestration over the retained source
and count any whole-context pre-pass/stack/bridge. Reuse existing independently
valid prepared paragraphs and child results only under their current complete
contracts. A general inline/counter seam continues through the existing exact
context reconstruction. Include full closure for an outside retained style
consumer; a construction-changing outside delta chooses the wider source
repair rather than silently treating it as a geometry change.

Concretely, extend `splice_publish.wf:RoutePatch` preparation into a supplier-
local chain patch. `publish_splice_routes` currently installs the touched
supplier's new head; that is insufficient when the same style supplier feeds
both replaced and retained paragraphs. Preserve surviving predecessor links
and each text node's logical last writer, with removals/additions prepared
together. Do not invoke `retain_routes` or `copy_retained_*` for this local path.

**Dependency and publication boundary.** Old/new seam and style delta precede
source repair; fresh inserted domains prepare independently; supplier-local
route precedence is the only route order. Ordinary geometry runs with current
parent constraints, then payload/route publication and parent summaries finish
as in section 2. No fallible operation may leave a half-repaired source tree.
Increment 1 lands with the same natural publication form as the existing
splice: independent per-destination writes, with no hand-added serialization,
runtime uniqueness check or additional directory. Each affected loop's owning
`doc` names `sg-inverse-proof-gap`, which currently withholds parallel
permission. Private preparation/preflight must succeed before commit, and
ordinary geometry plus route publication must complete without a recoverable
exit. New `SourceRepair` planning is read-only on retained state; the internal
commit uses factored `commit_splice_sequence`/payload publication, followed by
ordinary current-source geometry and completed validity/routes. A broad
`writes(context)` convenience wrapper must not order independently writable
destinations.

**Deferred parallel proof.** The existing
[inverse witness](inverse-proof/README.md) and
[storage ruling](SPLIT-CONTRACT.md#released-inverse-proof-and-recursive-order-storage)
own the known RANGE-1 limitation (`sg-inverse-proof-gap`). The owner/entry
type invariant and parallel publication proof follow
[PR #61, Paged adoption](https://github.com/Ming-Research/Snowghost-wf/pull/61)
and Whitefoot's small-owner, Bool-guard, `take_back` image and helper-frame
fixes; they do not gate increment 1. Separately, `route_write` writes shared
high-water metadata and `slot_write` declares whole-page-tree effects. A later
route-publication change should allocate/reserve privately, reduce the final
high-water mark once, and expose writes to already existing disjoint cells
through precise accessor contracts. That Snowghost effect-shape limitation is
deferred; this increment changes neither those internals nor their truthful
effects.

**Implementation state.** Source retention is implemented in the active
renderer sources; the temporary workflow builds those sources and applies
only diagnostic instrumentation or individual mutations to private trees.
The [bounded union arithmetic](source-union-range.md) uses exact `+`, since
the existing type bounds and ceiling preflights exclude saturation. The
remaining front-end refusal is [result contract transport](source-result-contract.md):
explicit success bounds establish the nested result invariant, but a forwarded
generic error helper cannot communicate its always-failure outcome to the
success-routed obligation. This is separate from `sg-inverse-proof-gap`.
The ordinary-layout, supplier-chain, retained-identity and F1/F9/F13 checks
remain wired but have not executed for this implementation. No runtime bounds
substitute, serial union or changed error-production form is used.

**Evidence.** Add a small retained-source fixture with an unchanged earlier
paragraph/context, a complete inserted/deleted block beside an earlier float,
and a later structural-selector consumer. After each insertion, text edit,
class edit, second structural edit and inverse deletion, fresh full layout must
be byte equal, in seq and par. Observe unchanged stable payload/route identities
and zero reconstruction for unrelated domains. Activate F1, F9 and F13 below,
including reason-10 exactly-once and missing-route subcases. Mutation failure
must be the intended stale sibling/output/route or duplicate edit, not refusal
before the new source path is reached. Preserve the original path fixture and
its 38 successful Apollo splices; record new fallback observations separately.

**Cost observation.** Trace every old fallback's precise guard, source scope,
constructed/retained payload counts and route records published. Compare
reconstruction, preparation, layout and bridge costs separately for all
18 historical reason-9 IDs and IDs 29–30. The falsifiable initial claim is
reduced source/directory work, not reduced float replay or attainment of 1x.
Reject source-retention benefit if unrelated directory copying remains the
dominant path or source construction does not shrink. Two small forward/inverse
pilots precede any larger batch; CI alone runs them.

### Increment 2 — Reuse ordinary interiors through changed float dependencies

**Change.** Introduce complete `BlockFlowResult`, `ParagraphLineResult` and
`FloatPlacementResult` for retained ordinary flow. Extend
`prepare_spaces`, `break_paragraph`, `stack_flow`, `resume_float_state`,
`resume_open_frames`, `restack_flow` and the boundary/frontier consumers to
request each phase under current inputs. Reuse an unchanged interior while
recomputing its float/normal placement. Resume from actual predecessor geometry
and live float exports; continue to equal outgoing margin/open-frame/exclusion
state, or the BFC end. Never substitute `beside`, float count or reach for the
key, and never assume an old nonintersection survives a new origin.

**Dependencies.** Preparation and speculative line requests are independent;
the actual exclusion chain orders only consumers whose input changes. Exact
transfer composition can bypass unchanged runs within its arithmetic proof.
All other saturation cases replay reference operations.

**Evidence.** Activate F2 (bytes/font and atomic inputs), F6, F7's inline
baseline case and F12. Exercise float insertion/removal, same-count moved
floats, clearance, a float outside lexical owner, negative-margin re-entry,
and a new intersection after an initially full-width paragraph. Keep F9/F13
active. Each operation compares with fresh full layout; the complete 18-ID
cohort is a coverage target only after tracing proves its source admission.

F12 needs a wired reassociation detector: `falsify-m2.yml` currently leaves
`reassociate-saturation` awaiting `sg-fraga-reassociation`. Existing saturation
fixtures alone do not establish that the intended mutation has been detected.

**Cost.** Record input comparisons, hits/misses, exclusion entries read,
rebroken paragraphs, replayed flow entries, convergence boundary, bridge work
and memory. Compare reason-9 construction and layout separately. A long true
float chain is reported as such; it does not relax the total cost gate.

### Increment 3 — Settle boundary, margin and percentage-height dependencies

**Change.** Extend ordinary owner/ancestor evaluation in `boundary.wf`,
`height_basis.wf`, `update.wf` and `flow.wf`; compare both margin extrema,
through/line/barrier state, both baselines and complete height provenance.
Recompute used sizes from child outputs through ordinary parent algorithms.
Keep existing Q139/Q140 consumed-input proofs conjunctive; no generalization
of the ordinary-flow height projection to flex/grid/table/replaced contexts.

**Dependencies.** Parent constraints go down before child layout; child
summaries go up before ancestor equality. Shared margin edges force settlement
order; independent children with settled inputs remain disjoint work.

**Evidence.** Activate F3 and F5; exercise equal numeric basis with changed
identity/definiteness, actual percentage min/max/height readers, positive and
negative empty chains and marker/line barriers. Retain F9's fixed-height
changed-interior case. Trace reason-7 IDs 29–30 instead of assuming which
boundary guard they exercise.

**Cost.** Charge proof/key checks, ancestor reductions and source retention
overhead per ID. Compare both reason-7 edits individually: their small main
budget makes a dense route/metadata pass a likely rejection, even with zero
layout misses.

### Increment 4 — Repair mixed inline source seams exactly

**Change.** Extend `SourceCheckpoint` beyond neutral boundaries in `build.wf`
and `structure.wf`, including `Open` pending state and open inline frames.
Repair both adjacent paragraphs, split/join roles, atomic ownership and empty
inline sources through exact state convergence. Update `fragment_topology.wf`,
`fragment_repair.wf`, `splice_fragments.wf` and source route patches together.
Joined/split paragraphs get fresh identities; untouched paragraphs keep theirs.

**Dependencies.** Piece/source order and open-frame state constrain seam
construction; independently closed paragraphs prepare in disjoint iterations.
Settled endpoint inputs precede independent fragment expression evaluation.

**Evidence.** Activate all F8 subcases and F2's generated/changed-source
preparation case. Use insertion/deletion inside open inline boxes, styled empty
inlines and atomic seams, followed by text/class/splice edits. Target old
reason-3 IDs 35–36 only after recording their exact source domains.

**Cost.** Count checkpoint lookup, reconstructed pieces/paragraphs, retained
domains, retired/new route records and fragment dependency work. A domain
reaching the whole context is an observed limitation, not a local repair claim.

### Increment 5 — Keep flex natural measurements across final layout

**Change.** Extend child-owned `FlexCache` and container input validity in
`flex.wf`, `splice_flex.wf`, `update.wf` and `module.wfm`. Audit preparation,
natural measurement, line/freeze/cross/baseline and final/stretch phases;
request intrinsic results through `box.wf`'s ordinary demand path. Preserve one
materialized final result, never use stretched geometry as natural input.

**Dependencies.** Item measurements are independent; line membership/freeze
rounds and cross/baseline reductions precede independent final/stretch layouts.

**Evidence.** Activate F4's flex measure/final/measure case and all flex
subcases of F7, plus F3 stretch transitions. Include equal size with changed
baseline availability, item order/membership and two independently dirty items.

**Cost.** Count natural hits/misses, deep rematerializations, complete line
reformation and child phases. Check block and font-size/root-font X5 controls;
do not claim phase caching eliminates every alternating layout.

### Increment 6 — Retain grid phase results with current tracks and areas

**Change.** Extend `grid_retained.wf:GridRowResult` helpers and
`grid.wf:grid_measure_column,grid_measure_item,grid_columns_pass,grid_rows_pass,
grid_final_pass` together with `splice_grid.wf`. Keep Q140's invariant-column
proof as a sufficient specialization; changed placement/tracks run their
ordinary sizing phases with independently retained child inputs/results.

**Dependencies.** Placement/intrinsic proposals precede columns, columns
precede independent row measurements, row/baseline reductions precede final
areas. Preserve per-item proposals, balanced reductions and true span phases.

**Evidence.** Activate F4's grid case, grid F7 and F3/Q140 variants, including
changed spans/order, unchanged outer width with different tracks, and
natural/final/natural constraints. All previous full-oracle checks remain.

**Cost.** Separate item contributions, track reductions, natural hits and final
layouts; observe reason-11/enclosing paths without changing their historical
classification and measure the closest X5 controls to the 2x ceiling.

### Increment 7 — Retain table and replaced/control contributions

**Change.** Add table input/contribution validity to `table.wf`, `tablegrid.wf`
and `tableborders.wf`, using child Context results for cells/captions. Add
replaced natural input validity at `build.wf`'s attribute/natural producers and
`flow.wf:replaced_size,intrinsic_replaced,lay_out_replaced`. Rebuild changed table
topology when necessary and retain child interiors only with actual source
correspondence and current spaces.

**Dependencies.** Topology and border winners constrain columns; settled
columns release independent cell work; row spans/baselines and final alignment
then settle. Independent replaced contexts read only their own attributes,
fonts/styles and containing constraints.

**Evidence.** Activate table F7 and table-final-size F10; extend F2/F3 coverage
to atomic replaced/control changes. Exercise row/column spans, captions,
collapsed borders and unchanged styles with changed ratio/alt/control inputs.

**Cost.** Count rebuilt topology separately from reused cell/caption interiors,
intrinsic queries and final sizing. Report any whole-table aggregate work
honestly; no claim of local track sizing is introduced.

### Increment 8 — Publish columns and positioned placement from current inputs

**Change.** Add `ColumnResult` validity in `columns.wf:collect_units,
fragment_columns,reflow_column_height` and complete `PositionedResult`
dependencies in `flow.wf:position_out_events,position_one,chain_anchor` and
`splice_position.wf`. Reuse normal-flow interiors; always rebalance the complete
current unit stream on change. Position out-of-flow children after their
actual containing block and static anchor settle, including table final sizing.

**Dependencies.** Units precede balancing/map publication; containing-block and
static-position outputs precede each positioned child's placement. Positioned
siblings are independent once those inputs exist.

**Evidence.** Activate F11 and all remaining F10 subcases: fixed viewport,
new containing-block identity at equal size, auto-axis static anchor and
positioned nodes excluded from ordinary range moves. F9 verifies changed
descendants still reach complete column/fragment output.

**Cost.** Separate normal-flow reuse from full unit collection/balance/map and
positioned phases. Columns retain a complete pass by approval, but its measured
cost remains inside the 1x/2x limits.

### Increment 9 — Complete stateful source repair and wider closure

**Change.** Extend exact checkpoint propagation for counters, quotes, generated
references, construction-changing outside style deltas and context-kind
replacement in `build.wf`, `structure.wf`, `style_update.wf` and
`splice_publish.wf`. Continue source order to equal outgoing state at a valid
boundary; widen explicitly to an exact context/root checkpoint when needed.
Keep ordinary tables/columns/positioned and all phase keys from earlier steps.

**Dependencies.** Counter/quote readers genuinely depend on preceding scope
state. Domains after convergence and independently affected suppliers do not.
Do not clear a second dirty branch when the first ancestor's dimensions agree.

**Evidence.** Extend F1/F8/F13 to counters/quotes and generated references,
multiple changed subtrees and a neutral splice followed by stateful rebuild.
Observe source lifetime/route identity as well as byte output after each
followup operation. Explicit reconstruction scope must match the trace.

**Cost.** Count each widened source domain and all later readers visited;
distinguish source reconstruction from ordinary geometry misses. Measure
full-build/checkpoint storage and retained memory, without presenting
worst-case root propagation as a bounded local algorithm.

### Increment 10 — Unify fast-case certificates and run the complete gates

**Change.** Finish common dispatch/accounting so `structure_splice` supplies a
sufficient certificate to the same evaluator/publication model; remove only
superseded duplicate orchestration, keeping each original conjunct and path
fixture. Audit all marks, old/current readers, result lifetimes, exact output
fields and effects against the complete read/producer/consumer ledger. This
increment completes integration; it does not defer correctness of publication
from earlier increments.

**Dependencies.** Fast-case proof and general evaluation use the same true
dependencies. Diagnostic aggregation is a reduction of local results.

**Evidence.** All F1–F13 subcases, all X5 page/kind/modes, original block
sequences/inverses, 104-edit Apollo followups and the 20-edit retained-state
fixture, existing Chromium oracles and Q139/Q140 checks. Existing permitted
refusals and original splice expectations stay explicit. Run the project gate
and one fresh read-only completion review against actual CI evidence, including
R3, C4, T4 and applicable design correspondence checks. No green suite is rerun
without a new change or unresolved issue.

**Cost.** Apply the complete paired acceptance protocol below; keep all 22 IDs
in the fixed cohort even when the new path succeeds. If any individual
historical ID or required aggregate/mode fails, report that M2 is incomplete
and resolve the measured dependency/algorithm limit; do not rename the cohort.

### Mutation activation ledger

These F labels identify rows of the design's falsification table in order;
they are local experiment labels, not new status-board items. Each composite
row has separate submutations so that one omitted input cannot hide another.
Every baseline passes; the mutant demonstrably reaches the changed path and
fails the intended byte/output/lifetime observation. A compiler failure,
unrelated earlier refusal, missing fixture or generic nonzero exit is not the
required detection.

| Row | Activated by | Required distinguishing omission and observation |
| --- | --- | --- |
| F1 outside style closure | 1; expanded 9 | Omit one changed retained sibling, then one changed descendant in another branch: insertion output differs while inserted content itself remains correct. |
| F2 preparation/atomic line input | 2, 4, 7 | Separately omit changed bytes, font/pick input, generated bytes and atomic first-baseline freshness while width/outer height agree: glyph/fragment or alignment differs. |
| F3 height input | 3; flex/grid 5–6 | Separately omit basis identity, definiteness and one percentage reader: equal numeric basis and stretch-transition outputs differ; retain existing Q139/Q140 mutants. |
| F4 natural versus final | 5–6 | Independently substitute stretched final geometry into flex and grid natural records: measure/final/measure sequences differ, not merely a changed-size single pass. |
| F5 margin state | 3 | Separately sum extrema, drop through state, line presence or barrier: positive/negative empty chains place the following box differently. |
| F6 exclusion dependency | 2 | Separately retain a moved float's input and omit a previously absent intersection: new intersection, clearance or negative-margin re-entry differs. |
| F7 baselines | 2, 5–7 | Separately omit first, last and availability; multiline nested flex/grid/table/atomic fixtures change alignment at equal height. |
| F8 source lifetime | 4; expanded 9 | Separately preserve retired handle, omit join, split or empty role: immediate seam output or following text/class/splice differs. |
| F9 publication cutoff | 1 onward | Stop publication at equal parent size: fixed-height parent retains stale interior text/fragment in the complete dump; a second dirty branch remains observable. |
| F10 positioned inputs | 7–8 | Separately ignore containing-block identity, static anchor, fixed viewport or apply ordinary range move: absolute/fixed and table-final-size placement differs at possibly equal interior size. |
| F11 columns | 8 | Independently retain old map and omit downstream fragment update: unit change near balance boundary differs even when total height agrees. |
| F12 arithmetic | 2 onward | Separately reassociate saturating operations and translate absent sentinel: existing saturation fixtures differ from reference operation order. |
| F13 routes/exactly once | 1; expanded 4, 9 | Independently omit text, style or context route, and apply a reason-10 edit twice: following consumer or original-plus-inverse differs. |

### Shared validation and cost protocol

CI performs every build, compiler witness, renderer run, test and
measurement; this planning round runs none. Reuse `.github/workflows/check.yml`,
`oracles-m2.yml`, `falsify-m2.yml`, Q139/Q140 workflows and the existing
`fallback-cost.py`/`fallback-phase.py` machinery where applicable. Amend harness
machinery only with representative wrong-result/missing-input detectors.
`make check` and the project's eventual readiness checks remain wired.

`fallback-cost.yml` currently pins historical comparison sources; update and
record the intended frozen cohorts before using it for these increments.
An unchanged workflow's old `main`/`before` labels are not current revisions.

After every operation, a fresh full style/build/layout on the edited document
is the incremental oracle. It uses no retained candidate cache and compares
complete serialized placed output byte for byte; seq and par outputs also
agree. Existing Chromium layout cases independently check shared algorithm
correctness for margins, floats, heights, baselines, containers and positioning.
Browser tolerances retain their current meaning. Identity runs and internal
lifetime observations are separate from timed edits.

Freeze main, same-source before/candidate and independent twins, compiler,
fonts, captured page bytes, complete edit scripts and machine/settings. Start
with two small forward/inverse pilots and inspect spread before choosing finite
interleaved batches. Preserve all preceding edits. Record per-edit total native
latency, exclusive instruction attribution, phase/key/source/replay/publication
counts and full-build/retained memory; include zero-edit and attribution
negative controls. Count comparisons, lookup paths, preparation attempts,
failed fast-case work, full bridges, publication and key memory. Never add
inclusive profile costs or medians of separately measured phases.

For fixed old IDs 1–6, 9–10, 17–20, 23–24, 39–40, 51–52 (reason 9), 29–30
(reason 7), and 35–36 (reason 3), reject if any individual repeated paired
median or required cohort median exceeds 1x main. Report each reason family.
Reject any X5 page/kind/mode paired median above 2x; do not pool twins or rounds
to erase failures. Preserve the prior M2 full-build bound and report memory
regressions. Spread that cannot decide calls for a justified repeat. No
numerical savings or reuse hit rates are predicted before observing the new
path, and no page/fixture identity chooses renderer behavior.

The retained full-build condition is style and layout stages within 5 percent
of M1 (`8b8612f`), on every page, as the structural criterion states; compare
the same-source before/candidate as well to attribute this implementation's
effect. Resolve the full M1 revision in the measurement manifest before use.

## 4. Whitefoot questions and minimal witnesses

These are expected proof pressure points, not a claim that the pinned compiler
has rejected code not yet written. The language already specifies disjoint
slice writes, indexed/field effect footprints, ownership replacement and range
facts. Use those natural forms; do not label ordinary specified support a gap.
The known historical recursive-storage/multiple-result probes below must be
checked against the actual pinned release in CI, with diagnostic status and
parallel offer evidence. No compiler invocation occurs in this round.

Distinguish source rejection from accepted source lowered without the required
independence. The pinned specification's effect/range rules and PAR-2 permission
conditions, not acceptance alone, govern these witnesses. Report each outcome
separately. Phase equality with variable owned vectors is a complete explicit
length/element comparison; OP-16 structural equality is not available for
arbitrary `Box`/`Slots` records or floating-point fields.

The sketches are semantic fragments, not complete runnable Whitefoot programs;
their names denote the planned records. Implementation witnesses must use the
pinned syntax: `doc` fields, `else if`, and all constructor fields named.

| Pressure point and code site | Smallest natural form to test | What refusal would mean; required acceptance |
| --- | --- | --- |
| Logical disjoint writes through recursive pages: `sequence.wf:slot_write,slot_store_output`, route publication | Two known distinct live logical slots in one `SlotPages` tree; independent calls `slot_write(pages: pages, slot: a, ...)` and `slot_write(pages: pages, slot: b, ...)`, with `a != b` established by construction | Existing accessor effects write the recursive page prefix. Increment 1 retains the approved natural loop form without a parallel certificate, naming `sg-inverse-proof-gap` in its owning `doc`. Paged and the pending range fixes supply later parallel permission; shared high-water metadata is a separate deferred Snowghost effect-shape change. No runtime uniqueness check or extra inverse directory is added. |
| Owner/slot inverse through accessors: retained entry -> payload publication and marking | For independent logical entries, `target = sequence_payload(sequence: owner_entries, slot: k)`; write `blocks[target.Open.block].flow_result`, using the construction-maintained inverse `(owner, entry_slot)` | `RANGE` terms may not express the recursive logical lookup; the existing `inverse-proof/recursive-fact.wf` records that historical limitation. Witness both construction of the relation and the forwarded writer call, then loop permission/emission. Do not add a parallel inverse directory, sort targets or runtime uniqueness pass to conceal it. |
| Indexed/field effect precision through helpers: `prepare_spaces`, `place_float`, payload publication | A helper reads immutable parent inputs plus a child result and writes only `paragraphs[k].line_result` or `children[k].anchor`; two different `k` calls are independent | Existing broad `writes(context)` implementations are refactoring targets, not proof of a language gap. First state truthful narrow effects on existing owned destinations. If the compiler widens them through calls/descendant boxes despite the specified contracts, file that smaller case. Never weaken the declared reads. |
| Independent recursive calls returning several results: route counts, validity and summaries | `let (left_count, left_ok) = count(left_slice); let (right_count, right_ok) = count(right_slice);` followed by count/validity reduction | Preserve `bulk-parallel-results.wf` as the minimal historical lead. Expect independent calls before the reduction; compile and inspect permission/emission at the pin. Do not replace the result shape solely to hide denied parallel permission. |
| Affine replacement and old/new lifetime: `Paragraph` shaped data, source checkpoints, final payload transaction | Prepare an owned replacement while read-only old fields are live; finish old-frame reads; `swap`/move into a disjoint destination; return the still-complete old state on precommit error | OP-12 ownership replacement is specified. A refusal with nonoverlapping lifetimes is a compiler witness; a real overlap means the transaction has a design bug. Do not clone every retained subtree or introduce shared mutable ownership to evade it. |
| Range facts after reservation/growth: payload/route capacity, prepared disjoint output ranges | Construct checked counts/prefix ranges, reserve through the existing operation, reacquire views, then write each certified range; constructor establishes the owner inverse through the actual `Slots` append path | Invalidation of stale views by growth is correct. Test the natural reacquired facts and construction-maintained bounds. A failure to transport required facts through a specified contract becomes a witness; repeated dynamic bounds/uniqueness tests or redundant field stores are not planned repairs. |
| Disjoint descendant ownership and sparse frontier: `ParagraphFrontier`, child Context evaluation | A fork partitions two payload slices; each recursive call mutates its own descendant-owned preparation/result and returns local counts | PAR-2 already describes owner-descendant independence. Require the natural nested-owned form to be admitted and emit offers where eligible; no context-wide mutable borrow, serial tree walk or shared diagnostic counter is a workaround. |
| Fallible independent preparation: new private paragraph/source preparation | Independent item calls produce their own owned `Result<Prepared, LayoutError>`; only a subsequent reduction decides whether to commit. Contrast the natural loop body containing `propagate prepare(...)` | PAR-2 excludes a body-level failure exit. Private per-item results are the actual transaction's independent outputs, followed by a necessary all-success decision, not a serial workaround. If that natural owned-result form still lacks permission, file the minimal case; do not silently serialize preparation. |

A witness lives in this project's investigation only while it demonstrates the
downstream need. If CI shows an actual language/compiler gap, the primary
session writes the smallest semantic witness under this investigation and tells
the owner, who files it into Whitefoot. Include the pinned revision, direct
compiler status, expected proof/permission and an acceptance test (including
emitted parallel opportunity when relevant). Continue other independent lines.
This round makes no board writes and files no request. Whitefoot's own session changes its
repository; Snowghost verifies the delivered fix with its witness and pinned
compiler through CI. No storage migration or experiment pin is preauthorized
by a refusal. Continue independent planning/implementation lines, and stop the
blocked operation without hiding the gap.

## 5. Departures, narrowing and direction-changing uncertainties

**No behavioral design departure is proposed.** All five approved choices
stand: exact source retention, explicit complete phase keys, demanded scalar
measurements plus one final result, owned transactional publication and complete
column balancing. Unsupported semantic certificates use the approved explicit
ordinary algorithm/reconstruction scope; they do not lower the final cost gate.
The first increment intentionally narrows local source repair to provably
neutral complete-block boundaries, with all publication obligations active;
later increments widen source and phase coverage. This is delivery order,
not a permanent exclusion of mixed inline, stateful, flex/grid/table or columns.

**Storage interpretation.** The existing `EntrySequence` pages are accessed
through `sequence.wf`/boundary/range functions (`sequence_payload`,
`sequence_node`, `sequence_output`, `flow_event`, `insert_before`, `remove` and
their current callers); route directories use `route_read`/`route_write` and
the existing publication functions. Keep `SlotPages`, `EntrySequence` and
`RouteTable` backing internals unchanged. Block/Paragraph/Context payloads
currently live in `Box<Slots<...>>` and are accessed through their existing
typed owned slices; `sequence.wf` does not expose a borrowed generic payload
accessor. The owner confirmed these existing access paths are allowed. Changing
backing internals or adding a parallel storage layer is excluded. Paged remains
later stacked work.

**CI and measurement protocol.** Hosted runners provide correctness,
instruction counts and traces; precise timing runs on the 14900K
through the coordinator's queue. Each comparison stays on one machine under
matched conditions. Historical hosted timings are not current 14900K evidence.

The following uncertainties must remain visible in implementation reports:

1. **Exact source domains for the 22 edits.** The old reason is not an exact
   failing guard. Increment 0 traces subguards and checkpoint boundaries. If
   dominant reason-9 edits require stateful/mixed source reconstruction, move
   the necessary checkpoint increment forward before claiming early coverage;
   do not broaden neutrality by assumption. Missing exact checkpoints may
   leave reason 7 above budget and reject the implementation's M2 claim.
2. **Parallel permission after storage adoption.** `sg-inverse-proof-gap` is
   the known owner/slot inverse limitation, with the existing natural
   publication loops approved until Paged and the pending range fixes supply
   their parallel proof. It does not block increment 1. Later evidence must
   distinguish source acceptance from parallel permission/emission, and
   Snowghost's shared route high-water effects remain a separate deferred
   limitation. No semantic serial order, runtime uniqueness check or second
   directory is introduced for either limitation.
3. **Complete comparisons at acceptable cost.** Exact float state and
   membership/child-output comparisons may cost more than the saved work.
   Count them from increment 2. A new projection requires an explicit proof;
   hashes alone or untracked revisions are not substitutes. Adding multiple
   materialized result trees to cure repeated phase work would reopen an
   approved choice rather than being an implementation detail.
4. **Publication bridge and failure semantics.** A full old/current scratch
   bridge or a private clone of an entire BFC could erase retention savings.
   Audit its real readers and charge it from increment 1. If bounded owned
   preparation cannot preserve the error/old-frame contract, stop for the
   ownership/design decision instead of publishing partially current results.
5. **Later-edit routes and construction state.** Supplier predecessor and text
   last-writer rules, synthetic checkpoints, generated references and two
   simultaneous changed branches can invalidate otherwise equal geometry.
   The followup sequences and independent mutation subcases are required
   evidence, not optional hardening after timing passes.

This plan changes no compiler pin or submodule and files no Whitefoot gap.
No tests, compiler runs, renderer runs or performance measurements have been
performed for it; implementation acceptance remains unverified until the
CI experiments and completion review above.
