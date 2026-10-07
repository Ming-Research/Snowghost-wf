# Split fragment dependency experiment (Q134; Q135 A)

## Question and prior rejection criterion

From cf12c609e1c00f86bb431fab4e92f5dca2bf94f2, compare stable anchored
run records (A) with flat rectangles reached through a dependency index (B).
The owner authorized both experiments, not adoption of either. Reject a
performance acceptance claim unless both sentence and font-size edits are
within twice concurrent main in each mode and both hosted rounds. Measure
all six X5 kinds on ecma262 and html5, with the merged base and its independent
same-source twin, using identical scripts, compiler, host and settings.
Correctness remains byte-identical full dumps, incremental/full identity in
both modes, unchanged cases, every page block edit splice 1 reason 0, and all
existing falsifiers plus one omission of each option's targeted repair.

This document owns the experiment's contract and results. It lives beside
[the cost investigation](DESIGN.md); fold its surviving conclusions into that
record when the experiment branches are retired. No experiment is merged into
research/m2-layout and no pull request is opened.

## Contract before implementation

The reference is the existing full fragment generator, checked against the
project's external rendering oracles; cached output is never a correctness
oracle. The relevant owners are `design/pipeline.md`,
`design/pipeline/layout.md`, and the stable-split section of
`../structure-edits/layout-design.md`. The merged anchors already identify
endpoints. Q134 therefore concerns retaining run correspondence and complete
invalidation, rather than inventing an endpoint identity absent from the base.

A split is one open inline owner interrupted by an Open(block) or
Child(context) payload. A run is a maximal sequence of that owner's splits
whose intervening flow events are all lineless paragraphs. Multiple runs of
one owner remain distinct even when their rectangles coincide. Fragment
identity is run identity plus role (leading, spanning, trailing), never owner
plus rectangle. Paragraph text/inline fragments retain paragraph ownership.
Empty-inline identity is source paragraph plus inline mark, separate from
run-plus-role identity. Context-owned empty-inline fragments retain their source paragraph's reference
scratch semantics: a lineless paragraph does not acquire a translated origin.

| Output | Inputs, including negative dependencies |
|---|---|
| Run membership/order | Split source order and owner; first/last live payload identities; every intervening event's kind and paragraph line-presence bit. An absent separating line is an input. |
| Leading fragment existence | The event immediately preceding the first opening; whether it is lined; its closing inline-owner marks. |
| Leading y selector | `sibling_above` backwards through lineless paragraphs, floats and positioned events to the first discriminating event; whether a closed block is itself a split head; Split.line sentinel. |
| Leading y | First visual top, or pending line position from the first normal origin and exact offset; preserve the selector and saturation order. |
| Spanning rectangle | First split's containing left/width; context content left; first visual top; last visual top and height. Height is `(last_top +sat last_height) -sat first_top`. |
| Trailing existence | Event immediately after the last close; its line presence and opening inline-owner marks. |
| Trailing y | Last visual top, height, and resolved bottom margin: a block resolves its style with the first split width as percentage basis; an independent Child supplies its already resolved margin_bottom. |
| Empty-inline rectangle | Source paragraph's line-presence bit, marks and styles, absence of that owner from the split-owner set, paragraph left and its retained lineless resolved position. |

Text can change shaping, line count, height, intrinsic contributions and
line-presence, hence run joining and adjacent-fragment existence. Unchanged
line presence is insufficient when owner marks change. Font-size can also
change inherited lengths, widths, margins, pending lines, and the containing
block's geometry. Class changes use actual style deltas: paint-only changes
leave these inputs unchanged; layout or generated-content changes follow all
style uses, including visibility of an inline's own fragment. Block insertion
or removal changes order, source ownership, adjacency and lifetimes. A kept
split head's interior edit changes its extent without necessarily changing
its external run. The existing structural certificate proves which complete
block seams preserve run topology and selectors; it must not be weakened.

Recompute topology when any membership, adjacency, source or selector input
changes. Recompute geometry only for changed geometric inputs. A uniform
translation with unchanged local geometry and exact arithmetic changes no
run topology or dimensions; A changes the owning origin, whereas B writes
each affected flat rectangle. A spanning run whose endpoints move differently
recomputes its extent. A changed pending margin repairs Split.line's offset;
translation alone preserves it only under the same exact-arithmetic and
sentinel conditions as the existing motion certificate. A changed width or
margin always refreshes the corresponding run fields, even if height agrees.

Validity has separate topology, geometry and scratch obligations. An anchor
certificate is carried only across edits whose dependency closure preserves
it; changed expressions must be checked against freshly computed reference
rectangles. Raw scratch is authoritative after reference replay until repaired
anchors are certified. A stale raw rectangle cannot be compared as if it were
fresh, nor can a fresh anchor override a legitimate reference result. The full
bridge remains necessary when a legacy reader requires all resolved scratch.
Missing metadata, retired endpoints or failed numeric conditions retain the
existing reference behavior; no new source limitation is introduced.

## Candidate data, invariants and true order

A retains a run slot within a retained topology, its first/last split endpoints, explicit
fragment roles, horizontal inputs, trailing margin, leading selector and
owner-relative line offset. A reverse dependency index maps changed sources
and adjacency intervals to runs. Distinct runs never alias through coordinates.
Run slots remain stable while topology survives; replacement retires the old
topology's slot domain together with every index that can name it. Internal
references do not escape that domain, so reused storage cannot be observed
through an old reference. Identity is context plus topology lifetime plus local
slot; the lifetime needs no stored or wrapping global generation counter.
Logical publication order is separate from storage identity: the context own
rectangle comes first, runs follow first-split source order, each emits leading,
spanning and trailing roles in that order when present, then empty-inline
sources follow event and mark order. Replacement updates this logical order
without appending an early replacement behind a kept suffix. Source adjacency
is the true ordering dependency; independent rectangle evaluation is unordered.
Context replacement retires its entire identity domain. The prototypes add no
identity allocator: split indices use the existing guarded `flow_index`
conversion and role slots use existing array storage. No generation counter is
incremented or saturated; `no_index` remains missing metadata, never a fresh
identity. Any later handle that escapes topology ownership would require an
explicit non-wrapping generation and exhaustion policy before publication.

B retains the same semantic dependencies and lifetime distinction, but its
published outputs are flat rectangles. An index maps source identities and
flow intervals to disjoint rectangle slots. Source or topology replacement
updates that mapping before reuse. Geometry repair writes the actual affected
rectangles, including every translated suffix rectangle. Coincident rectangles
are separate destinations. Lookup cannot use rectangle intersection, because
negative margins and coincident geometry are valid.

Both candidates start with independent text/style preparation and speculative
paragraph breaking. Flow placement follows only margin/float/available-space
dependencies. Changed line-presence and marks select topology repair; stable
run membership permits independent endpoint, width and margin evaluation.
Each run's outputs depend on its endpoints and selectors, not on another run's
rectangle. Dependency lookup is read-only; disjoint repair destinations run
independently. Publication follows preparation of complete replacement records;
ancestor summary reduction follows the existing tree. Read-only snapshots or
function-kind parameters may expose these independent writes without shared
append cursors. A shared mutable work queue, serial run scan or global
allocation counter would add an unjustified order.

A's order ends at changed local inputs and ancestor origins; absolute
resolution belongs to dump/paint. B adds the necessary flat-output writes after
a movement is known, but those writes are mutually independent. Topology
joining has an order dependency on source adjacency, not on geometric repair
of preceding runs. Balanced summaries can discover independent runs without
serial reconstruction of the whole context. Full rebuilding of unchanged runs
is an experiment limitation, not fulfillment of bounded repair.

The i32 reference operation order is normative for both candidates. Widened
owner differences are exact i64 differences; narrowing happens at the same
observable boundary as the reference. In particular, translating a previously
clamped height is not equivalent to re-evaluating two endpoints. `no_line` and
`no_index` remain sentinels and cannot be reused as finite coordinates or live
identities. Existing saturation and structural falsifiers remain enabled.

## Status

Contract recorded before implementation. Q135 A is authorized and closed;
Q134 remains open pending validation and measurements. Independent contract
review found and fixed the empty-source line-presence/identity dependency,
publication order separate from storage identity, and the Child margin case.

Both prototypes use topology-local run-role slots aligned with the reference
fragment sequence and a balanced postorder interval index. Internal references
do not escape the topology; clearing it drops the entire index before slots
can be reused. This implements a lifetime domain rather than a wrapping global
generation counter. Kept topology retains stable split endpoints and role
slots. Topology-changing replays still reconstruct the context's split runs;
bounded topology replacement remains an explicit prototype limitation.
Text/style preparation rebuilds Open/Close marks from the unchanged Begin/End
pieces; changed text offsets do not change the owner predicates read by the
fragment builder. Box-tree reconstruction replaces the topology instead.

The first hosted layout-check sample at 7e38d03541fdf44ae6d3b383b0d8b634ac02524f
spent 10 seconds in its compiler/check step (run 37675824700), before expanding
to full correctness jobs. The first B compilation exposed a missing Styles
alias, fixed at 1c68bb5; it was a source error, not a Whitefoot gap. Obsolete
mutation run 37677062916 was cancelled after the source changed; it is no pass.

B repairs the changed range plus its translated suffix, then runs the existing
complete field comparison only over those dependency intervals. A repairs the
replayed range, retaining suffix expressions and their certificates because
their local inputs are unchanged. A's split lines are also owner-relative:
stacked openings mark raw line scratch dirty; binary source-range lookup
publishes those offsets. The existing arithmetic travel certificate permits
unchanged suffix offsets; exceptional numeric repair preserves the reference
saturating addition using the still-retained old owner origins. Both options
keep the original full construction and certification for replaced topology.

A's no-split-line-refresh mutant disables the published mode-2 anchor
resolution and reads stale raw line scratch. The reference-only
`split_reference_line` helper is not the reader of retained suffix fragments;
its superseded queued mutation is not validation evidence. The previous dirty-publication omission was
not detected (37679193027): ordinary suffix translation no longer needs that
publication. Dropping an eliminated suffix-coordinate write is also ineffective.
The original path requirement and unmutated identity remain unchanged. The additional option-specific mutant drops the
targeted fragment-cell repair and must fail a semantic identity check. No
fixture HTML, expected dump, or block success requirement is changed.

Independent review identified missing runtime coverage of A's exceptional
split-line saturation repair. `split-limit.py` now generates low/high-origin
Open and Child heads with an empty leading fragment, followed by paragraph
growth/shrink edits. The supplementary hosted oracle job reuses exact-source
correctness drivers and requires seq/par identity; A additionally omits only
the exceptional line repair and requires a high-origin semantic difference.
These are proposed boundary probes until CI demonstrates both observations.
The local assertion sample rejected missing detection, a low-control mismatch,
incomplete output and a refused edit; an actual high mismatch was recognized.

The source review also found an unnecessary global repair-to-certificate
barrier. Both prototypes now evaluate the unchanged full field comparison
immediately after each leaf repair, using a shared value evaluator with narrow
immutable reads. Independent subtrees return booleans to a balanced conjunction;
only validity publication waits for the whole reduction. The separate second
index traversal is removed. Full publication uses the same evaluator and exact
comparison, including raw/missing-anchor behavior and saturating operation order.
Final timing and affected validation must use this fused revision.

The first generated saturation probes passed normal seq/par identity and the
unmutated detector negative control, but did not detect omission of exceptional
repair (37683206470). They therefore establish boundary identity only, not
coverage of that repair path. Its reach and a distinguishing probe remain under
investigation; the omission expectation is unchanged.

Source inspection explains that first probe's non-discrimination: the plain
paragraph is pre-broken; the high-origin travel refusal then marks the context
restyled and forces full stacking. The additional atomic-inline variant makes
pre-breaking inapplicable, allowing the existing split-fragment refusal to
reach legacy reference updating instead. Ordinary incremental counters and
base dumps are now captured with both plain and atomic variants. No admission
guard or expected identity is changed; selective omission must still differ.
