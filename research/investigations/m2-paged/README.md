# Built-in pages and the owner-motion inverse

## Question and prior criterion

Recorded before implementation or measurement. Starting revision:
`030e4dd4081c9c15699363bdfa0e57c53a7f761d`, compiler
`wf-78223721f77d`, specification v0.121. Can the existing layout storage
use built-in `Paged`, preserve its owner/entry inverse at every writer,
and expose the independent owner-motion writes as parallel tasks without
increasing full-build or edit cost beyond the criteria below?

The oracle is [the pinned specification](https://github.com/Ming-Research/Whitefoot/blob/78223721f/spec/kernel-spec.md),
especially TYPE-11, OP-10, PRE-1 and RANGE-1 through RANGE-5. The
[owner ruling](../../../design/pipeline/layout.md) selects a Context range
type invariant over built-in order storage. The earlier
[released inverse proof](../m2-edit-cost/SPLIT-CONTRACT.md#released-inverse-proof-and-recursive-order-storage)
does not establish the renderer's writer obligations.

The [C3 attribution](https://github.com/Ming-Research/Snowghost-wf/blob/2d9fdf032992610986668f550ccb52f066d61143/research/investigations/storage-layout/c3-attribution/README.md)
compared one built-in store per existing owner/store, rather than pooling
owners. Whole HTML5 layout was within its 2% noise band (1.015 sequential,
1.008 at four workers), but sequential box construction was 1.093. These
historical observations motivate a same-structure port, not acceptance of
this revision or a prediction for every workload.

## Storage shape and dependencies

Replace `EntrySequence.payloads: SlotPages<Flow>` with an owned
`Box<Paged<Flow>>`, and its `SlotPages<SequenceNode>` metadata with an
independent `Box<Paged<SequenceNode>>`. Keep a sequence on each Block and
the root sequence on Context. Preserve stable append-only slot identities,
AVL order, event weights, liveness, tombstones, range actions and limits.
Slot number is a stable payload index, not the changing AVL rank. A splice
appends a payload slot and links it at its order position; it must not use
`insert_at` to shift stable identities. Bulk construction still has its
pending list followed by sealing; retain the same dependencies between
child summaries and parent summaries. No context-wide pool of owner order
stores is introduced.

The other `SlotPages` use is `RouteTable<T>` in routes.wf and the private
splice route patch. Its sparse constructor represents a high-water domain
without materializing the prefix, unlike Paged's initialized window. A
dense replacement would change that representation and its construction
cost. This requires a separate direction decision if the port reaches it;
the owner-order prerequisite is investigated first. Existing block,
paragraph and child `Slots` pools are not hand-written page directories.

## Invariant and writer inventory

For root order and each block owner's order, every live Open entry at
stable slot k names a block whose `entry_slot == k` and whose `parent`
names that owner (the root uses `no_index`). Text similarly uses the
paragraph's `entry_slot` and `block`; Child, Float and Out use the child's
`entry_slot` and `block`, with all three variants sharing the same child
target pool. Their facts must exclude cross-variant collisions together.
Retired entries require a liveness guard or clearing their payload when
removed; synthetic Close events are not stored live order entries.
The type invariant belongs to Context, which owns both ends, and is
received implicitly by callers. No runtime uniqueness test or proof-only
index is allowed. The independent motion loop uses the natural indirect
target write and `apart(i, j)` of the existing natural.wf probe.

Writer families to discharge, including propagated error exits:

| Writer | Obligation |
| --- | --- |
| build.wf `new_context`, block/paragraph/child construction and `finish_tree_sequences`; sequence.wf `new_sequence`, `pending_append`, `append_flow`, `record_child_entry`, `finish_sequence` | Empty domains establish the invariant; publish pending entries and their matching owner/slot fields together; sealing transfers the established relation. |
| sequence.wf `sequence_reserve`, `insert_before`, `remove`, rotations and balance | Growth preserves all initialized payloads; append establishes the new inverse; removal excludes retired entries; AVL rewiring preserves slot identities and inverse fields. |
| build.wf `push_item`/`push_or_fail` and every target-pool append | Growth preserves old targets and their fields; appending a new target must not activate a previously out-of-bounds order entry with a wrong inverse. |
| splice_publish.wf `relocate_splice`, `publish_splice_payloads`, `retire_splice_payloads`, `retire_splice_child`, `retire_splice_atomics` and their splice.wf/splice_boundary.wf callers | Private relocation rebases identities; publication transfers order and targets between owners; retirement removes the corresponding live relation before clearing inverse fields. Both source and destination must remain valid. |
| structure.wf context replacement/retirement and route publication | Kept outside identities remain unchanged; replacing a Context preserves its parent-owned inverse while establishing its internal one. |
| boundary.wf/reference.wf geometry and summary writers, range.wf action writers, prep/flow/update child and paragraph writers | Preserve inverse fields and order; narrow effect rows and checked contracts must carry that preservation through helpers. Geometry-only writes cannot introduce an order dependency. |
| boundary_checks.wf, frontier.wf and range.wf synthetic constructors | Establish the same relation as ordinary construction; no special test-only path. |

RANGE-2 explicitly forgets whole-window facts at non-tail operations,
including `grow_paged`. Before a broad port, a minimal Context witness
tests preservation through growth; a separate natural motion control carries
the inverse through its counted-loop invariant. OP-10 promises that growth moves no existing
element, but the published growth contract states only capacity and length.
If that sound writer cannot establish the exit invariant, stop this step
and retain its exact hosted diagnostic; do not repair it by redundant
stores, a runtime validation loop, a fixed capacity, or a compiler change.

## Comparison fixed before measurement

All execution uses GitHub-hosted Ubuntu AMD/Intel runners; no local
builds/checks/timing and no self-hosted runner. One pinned compiler and
toolchain for all cohorts. Build base, independently built base twin,
candidate and independently built candidate twin from recorded revisions.
Capture CPU, exposed CPUs, OS/kernel, compiler manifest/checksum, toolchain,
driver checksums, input hashes, worker count and command lines.

Start with two smallest useful build/runtime samples and their elapsed
times to choose batch size. Use at least three interleaved rounds, reversing
cohort order in alternate rounds, on one machine per comparison. Warm each
driver. Record every round and use paired candidate/base ratios; do not
compare absolute times between machines. Extend only ambiguous cells.

Measure full style and full layout for ecma262, html5 and apollo11 in
sequential and four-worker modes, plus every X5 edit kind (`word`,
`sentence`, `colour`, `fontsize`, `rootfont`, `block`, from run.sh),
preserving full script ordinals and separating style
from layout edit time. Report full-build costs including box construction,
not just the layout kernel. For each workload/mode define noise as the
maximum absolute deviation from 1 of both twin/original ratios across
rounds, with a 2% floor. Use the median of paired round ratios for the
candidate comparison; if round variation prevents classification, repeat
that cell and report it unverified until resolved.

Reject if any full-layout cell is more than 3% slower than base outside
measured noise, or if any full-style or edit-kind cell regresses beyond its
noise band. A full-layout cell above 3% with noise too large to decide is
unverified, not a pass. Reject completion for any changed output, weakened
check, failed gate, missing invariant-maintenance detection, denied natural
owner-motion loop or missing emitted task offer. Historical C3 evidence
cannot substitute for these measurements.

## Validation and evidence required for completion

On the final code revision: `check`, `layout-check`, `q139`, `q140`, every
`oracles-m2` job including Apollo11 fallback follow-ups, and the complete
`falsify-m2` matrix. Add successful-compilation mutations that corrupt
owner/slot maintenance and observe their semantic failure; rejection by
the compiler is proof evidence, never mutation detection. Capture
`--par-ledger` and reachable emitted task offers for each owner-motion
writer. A minimal proof witness is not renderer emission evidence.

No design log entry is added. Any new design choice stays proposed in
layout.md, and its implemented-status wording must match what actually
lands. The fallback-design branch's files remain outside this task.

## Progress and branch disposition

2026-10-10 22:52 UTC: The investigation and two proof programs are written;
no renderer code has changed. Their compiler outcomes, ledger, emission and
runtime results are unverified. The temporary hosted workflow records raw
statuses; its job succeeding means evidence collection, not proof acceptance.
No local build, check, test or measurement has run.

The first SSH push was rejected as non-fast-forward. The requested remote
branch already names `ee58302d1f9efcf50fa9832acdb729794f868c46`, an older
Paged experiment, rather than a branch from the requested base. No force
push or merge was attempted. Hosted compilation, the Draft PR and subsequent
integration await the branch disposition below. The potential growth proof
limitation is a specification-based hypothesis until the pinned release
has compiled the witness; it is not yet a reported compiler refusal.

### Replace the older experiment branch?

**Background.** `research/m2-paged` already contains an October 7 experiment
pinned to an older experimental compiler. Git rejects the new branch's
ordinary push. Merging that history into the requested 030e4dd-based task
would entangle unrelated earlier work; pushing another branch is outside
the task's explicit restriction.

**Options.** A (recommended): authorize replacement with an exact
`--force-with-lease=refs/heads/research/m2-paged:ee58302d1f9efcf50fa9832acdb729794f868c46`.
This preserves the requested base and branch name, but moves the published
reference away from the old experiment; its old tip is recorded here and
remains in the local clone. The lease refuses intervening changes.
B: authorize a different work-branch name, preserving the old reference
at the cost of changing the requested branch. C: preserve both local work
and the existing remote branch and stop; hosted validation and delivery
remain blocked.

**Confidence 5/5.** Git's non-fast-forward rejection and the fetched tip
establish the collision. Whether the old branch should be replaced belongs
to the owner; evidence of an active consumer would favor B.

### Read-only review and stopping status

2026-10-10 22:53 UTC: A separate reviewer inspected the complete four-file
diff from `030e4dd4081c9c15699363bdfa0e57c53a7f761d` to
`a9edebcf1a6d6cc4ce4e45d6aca703c734dcf24a`, plus the investigation's working
changes. Scope included the owner and project instructions, relevant
pipeline/layout decisions, C3 source, released inverse probes, affected
storage definitions, pinned specification and hosted workflow. No execution
was performed and there were no findings within this limited scope.
G2/G3, DC1/DC2, R3, T4 and repository/workflow hygiene passed within scope;
G1/DC3/C4 were not applicable. DC4 and validation remain unverified.
The implementing pass separately corrected two source names in the writer
inventory and the description of which probe contains the loop.

Stopping reason: the owner must authorize a disposition of the existing
remote branch before the task can reach hosted CI. Nothing has moved to
Paged in the renderer. The target inverse, its writer inventory, criteria
and hosted probe workflow are prepared, but neither probe has compiled.
There is no established Whitefoot refusal to file, no renderer ledger or
emission evidence, no semantic mutation detection, no gate run ID, no
timing table and no performance verdict. No pin, submodule, design tree or
fallback-design file changed; no Draft PR was opened from the old remote
branch. The remaining adoption and validation work retains its full scope.
