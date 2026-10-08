# Split fragment dependency experiment (Q134; Q135 A)

## Question and prior rejection criterion

The owner selected Q134 A on 2026-10-07: retain stable split-run and endpoint
identities with owner-relative anchors, repair affected fragments, and let
following fragments resolve through translated endpoints. Q135 A requires the
dependency and validity contract first. Q132 A retains counted post-publication
flex recovery. Option B is no longer an adoption candidate and its branch stays
unchanged. This document owns A's contract and its acceptance evidence beside
[the cost investigation](DESIGN.md).

Acceptance is byte-identical full dumps, incremental/full identity for all six
X5 kinds in sequential and parallel modes, unchanged case/fixture pages, every
page block edit splice 1 reason 0, and all existing falsifiers plus omissions
of affected-fragment repair and following-fragment translation. Two hosted
rounds compare A with main, cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 and an
independently built same-source base twin, using identical scripts, compiler,
host and settings. Sentence and font-size medians must be at most twice main
in each page/mode/round; word and block must be no worse than the base. Only a
passing result authorizes a merge commit into research/m2-layout followed by
layout-check and check. Failure is reported to the owner without merging.

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

### Edit closure and publication

| Edit | Invalidated inputs | Required repair | Retained work |
|---|---|---|---|
| Word or sentence text | Shaping, breaks, line-presence, paragraph size and outgoing flow state | Prepare/break the changed paragraph; settle affected flow; repair intersecting run intervals. A line-presence transition rebuilds topology, including negative adjacency inputs. | Unchanged pieces retain owner marks; runs outside replay keep selectors, offsets and geometry certificates. Following endpoints consume the exact admitted motion. |
| Local font-size or root font | All actual inherited font/length uses, intrinsic size, available width, line-presence and resolved margins | Follow recorded style uses, recompute affected widths, breaks, margins and flow; repair the run's first width and last margin even when height is unchanged. | A uniform exact vertical move preserves local offsets and role slots. Root font has no promised small frontier. |
| Class / colour | The actual style delta, including fragment visibility and generated content | Paint-only colour changes no layout input; layout deltas follow their recorded uses. Changed box/inline ownership or generated pieces replaces topology. | Style identity alone is neither an invalidator nor a proof of unchanged layout. |
| Block insertion/removal | Source order, endpoint lifetime, adjacency, owner marks and boundary state | The existing complete-block splice certificate permits retention only when no split or empty source is retired and the seam preserves topology/selectors. Otherwise rebuild the affected context through its recorded checkpoint. | Certified kept payload slots and relative anchors survive rank shifts; reference entry rebuild restores raw ranks before binary split lookup. |

There are three authority states. Full construction/reconstruction publishes raw
reference rectangles, dirty pending lines and uncached topology. Encoding then
publishes exact line offsets, checks every raw/anchor field, and constructs the
interval index. A stable-topology replay starts with these certificates, dirties
only stacked split lines, publishes their offsets after endpoints settle, and
repairs/certifies intersecting leaf slots before the balanced validity join.
Only then is `fragments_anchored` published. Raw suffix y fields are deliberately
stale in this last state: every output reader must use `placed_context_fragment`.
A compatibility bridge materializes anchored values before making raw scratch
authoritative again. Clearing fragments drops the index, aligned anchors and
repair/authority flags together. A failed certificate forbids local reuse;
it is not evidence that stale suffix scratch is reference output.

The index stores split-slot extrema, not coordinates: an enclosing run intersects
a replay of its interior even when neither endpoint is replayed. Payload slots,
not shifted event ranks, identify the endpoint. Flow order determines interval
selection and output order; it must never be inferred from y because relative
positioning and negative margins can reverse it. Empty-inline rectangles keep
their source paragraph's last lineless scratch semantics and are not suffix
rectangles. They can be retained only under the explicit empty-source stability
condition.

### Targeted certificate invariant

`repair_anchored_fragments` returns whether the targeted path executed, while
`fragments_valid` records the comparison result. Its admitted unmutated path
must produce true: `geometry_update_reference` first materializes nonzero
context adjustments and clears them; topology validity supplies live first/last
payloads and split slots; dirty line offsets are published before leaf repair.
For each mode, repair and evaluation then read the same immutable endpoints
and apply the same ordered i32 operations. The mode-2 i64 difference reconstructs
the freshly stacked i32 line exactly; mode 1 uses first top, mode 3 uses last
bottom minus first top, and mode 4 uses last bottom plus the repaired margin.
Untouched roles retain their prior certificates under the topology and exact
motion conditions above. Thus a failed targeted field comparison is an internal
invariant failure, exposed by the full/incremental oracle, rather than a supported
route to valid raw suffix rectangles. The omission falsifiers intentionally
break this invariant; there is no recovery that hides their missing work.
The normal full publisher differs: all its raw rectangles are freshly generated,
so a non-representable anchor may legitimately leave raw output authoritative.

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

The contract preceded the prototype. Q134 A and Q135 A are owner-approved;
implementation completeness and acceptance are separate from that selection.
The owner instructed that the design log entry wait until
[pull request #49](https://github.com/Ming-Research/Snowghost-wf/pull/49) is approved;
this work opens no pull request.
The following dated prototype evidence predates the completion validation. Independent contract
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
publishes those offsets. The existing arithmetic travel certificate is required before suffix reuse,
including convergence at a computed zero delta because saturated old positions
cannot recover the true old cursor. Exact motion preserves suffix offsets;
unsafe arithmetic replays the suffix through the original operations. Both options
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

`split-limit.py` generates low/high-origin Open and Child heads with an empty
leading fragment and plain/atomic paragraphs, followed by growth and exact
undo. Ordinary oracles require identity in seq/par. The numeric falsifier
requires unmutated identity and a detector negative control before omitting
each `reference_motion_fits` admission call separately; low-origin controls must stay identical
and a high-origin semantic difference must be observed. No expected result or
page block-splice requirement is relaxed.

The source review also found an unnecessary global repair-to-certificate
barrier. Both prototypes now evaluate the unchanged full field comparison
immediately after each leaf repair, using a shared value evaluator with narrow
immutable reads. Independent subtrees return booleans to a balanced conjunction;
only validity publication waits for the whole reduction. The separate second
index traversal is removed. Full publication uses the same evaluator and exact
comparison, including raw/missing-anchor behavior and saturating operation order.
Final timing and affected validation must use this fused revision.

The initial plain boundary probes passed, but did not exercise the exceptional
line repair: paragraph pre-breaking followed by numeric refusal forced full
stacking. Adding an unchanged atomic inline reached reference reuse and exposed
an undo mismatch in both prototypes (A run 37691741191, B run 37696134276).
The B debug dump shows the head at 33554412 px instead of the full build's
33554420 px after undo; the full hash returns to the initial hash. Saturating
`old_y + 20px`, then subtracting 20px, loses the original coordinate. The old
publication-time numeric check was too late to repair that information.

Both prototypes now require the origin/travel certificate before in-place
suffix translation and before accepting partial-stack convergence. Failed
admission continues reference replay through the suffix. The old root travel
is read once before partial stacking. A's exceptional fragment-only line repair
is retired: it cannot repair saturated endpoint geometry, and both former
call sites now require its exact-motion certificate before translation.
The numeric admission omission replaces that unreachable repair omission;
all existing fragment and targeted-cell falsifiers remain wired. [The historical-base probe](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37696128952)
also fails both growth and undo at cf12c609; its undo dump has the same lost
head coordinate. Corrected runtime validation is pending.

The numeric argument uses the existing conservative travel metadata: margins,
frames, baseline components, constrained heights, relative displacement and
atomic/float/positioned excursions are charged by absolute magnitude and
summed without wrapping. Unchanged suffix placement therefore needs the old
travel plus the proposed displacement and content-origin magnitude to remain
strictly below the i32 sentinel. Changed prefix operations retain their
reference order. The travel argument was audited in source; it is not a
machine-checked arithmetic proof. Independent omissions are configured to exercise both new
admission sites separately.

## Remaining-cost diagnostic question, before profiling

The fused hosted comparison 37684940686 still fails HTML5 font-size acceptance
for both representations. Selected pairs 23/24 and 43/44 were near A's earlier
sequential median, with reason-5 and reason-6 boundary fallbacks and thousands
of boundary visits despite few held entries. Profile those unchanged C/K pairs
on main, cf12c609, A and B using the measured drivers and verified page digest.
Two small samples select a bounded repetition count before the profiler runs.
If split-fragment work still dominates, reject the claim that the targeted
representation removes the observed cost. If boundary publication/lookup
instead dominates, the remaining bottleneck is broader reference maintenance.
This repeated-pair profile is exploratory diagnosis, includes process startup
and style preparation, and does not replace the two-round acceptance workload.

## Remaining-cost profile result

[Hosted profile 37696133904](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37696133904)
used the measured fused drivers A 3b239df449c136a2f690f5f8d16636c527a5e73f,
B 6d0286f6257a19d1375e5a4501ec3169193949c2 (renderer 1d7db04),
main 1fdb4050806ba08ca1ecd09c1e23b7cb77729ce9 and cf12c609,
with wf-0b7f5c5b9854/clang 22.1.8 on one hosted Intel Xeon Platinum 8370C
(4 vCPU, Linux 6.17.0-1022-azure). This precedes the numeric correction.
Four ten-pair samples took 2.55–2.63 seconds including startup; the bounded
rule selected 228 repetitions, or 456 measured edits, per profile.

For A, pairs 23/24 and 43/44 retained only 7 and 10 entries but accounted for
84,675 and 54,285 entries, respectively. Their boundary visits were
2,940/18,042/28,623 and 1,654/8,624/13,634 (entries/blocks/indexes), with one
reason-5 or reason-6 fallback per edit. `translate_dense_reference_suffix`
was the largest layout self-time symbol at 12.47% and 7.28%; B showed 12.62%
and 6.26%, and cf12c609 10.23% and 5.87%. No fragment repair/reconstruction
symbol reached the report's 0.5% self threshold in A's two profiles.
The profile includes startup and style work, so these percentages are not
isolated per-edit shares and do not establish a complete cost decomposition.

Source inspection agrees: the legacy reference path still translates dense
suffix scratch, then encodes/publishes boundary outputs through retained
owner indexes. Both representations optimize split fragments, not that wider
compatibility suffix. This is the remaining measured mechanism for these two
HTML font edit pairs; it does not prove every HTML font edit has the same cost.
The ordinary two-round workload remains the acceptance test. A bounded
reference-suffix representation/consumer contract is deferred in the TODO;
neither prototype claims to have solved it.

## Completion validation setup

The first completion timing attempt, [37710841463](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37710841463),
failed all four driver builds before measurement: the pinned f949 compiler's
`llvm.coro.end` return type was rejected by Clang 22. The workflow had retained
the newer compiler's toolchain while selecting the branch pin for all drivers.
The corrected workflow uses Ubuntu 24.04's native clang/lld, as this branch's
correctness workflows do, with the same f949 compiler for main, base, twin and A.
No renderer source or expected output is changed for this toolchain correction.
