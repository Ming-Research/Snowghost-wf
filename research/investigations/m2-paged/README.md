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

### Earlier branch collision (resolved by owner)

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

Earlier stopping reason: the owner had to authorize a disposition of the existing
remote branch before the task can reach hosted CI. Nothing has moved to
Paged in the renderer. The target inverse, its writer inventory, criteria
and hosted probe workflow are prepared, but neither probe has compiled.
There is no established Whitefoot refusal to file, no renderer ledger or
emission evidence, no semantic mutation detection, no gate run ID, no
timing table and no performance verdict. No pin, submodule, design tree or
fallback-design file changed; no Draft PR was opened from the old remote
branch. The remaining adoption and validation work retains its full scope.

### Authorized continuation on the new branch

2026-10-10: The owner selected a new branch, `research/m2-paged-adopt`,
with plain SSH pushes and a Draft pull request into `research/m2-layout`.
The older `research/m2-paged` reference remains untouched. This settles the
earlier branch card in favor of option B. The proof workflow now names the
new branch. The existing read-only Whitefoot clone in `.git` supplies the
normative specification at `78223721f77db615c950b6df1bcc690629f9fe4b`; no
Whitefoot source enters the tracked tree. Step 2 starts with the prepared
growth-preservation witness before any broad storage rewrite.

### Hosted growth refusal

2026-10-10 23:15 UTC: Hosted proof collection
[38094056612](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38094056612)
at `2083610c8cc1e5477bed68fc90ad01a9999ddd30`, using
`wf-78223721f77d`, refuses the unchanged `grow-inverse.wf` with exit 1:

```text
research/investigations/m2-paged/grow-inverse.wf:20:3: error[RANGE-3]: UndischargedRangeFact
  source:   return unit;
  marker:   ^^^^^^^^^^^^
  fact: inv
  site: a return
  missing: `c^.targets.inner[c^.order.inner[k].Open.block].entry_slot == k` (line 13)
  mechanical_fix: establish the fact before this site: a range `requires`, a range invariant of the enclosing counted loop, or a guard that excludes the uncovered elements
```

This blocks step 2, including order storage, and therefore renderer owner-motion
parallelization and candidate acceptance. `sequence_reserve` in
`renderer/layout/sequence.wf` grows the owner sequence before insertion while
retaining earlier entries; the same-structure Paged replacement needs this
operation. OP-10 says `grow_paged` moves no existing element, but PRE-1
publishes only capacity and unchanged length, and RANGE-2 forgets the written
cell contents. This is a specified proof limitation, not evidence that the
compiler violates v0.121. A loop invariant must be proved on entry (RANGE-3);
simply restating the lost relation after growth cannot recover it. No runtime
check, redundant write, fixed capacity, proof-only data or alternate storage
representation is added. The minimal witness remains unchanged for the
owning language session. Proposed deferral key: `sg-paged-grow-inverse`, P1;
reopen when the pinned release can prove this exact writer and still rejects
a corrupted inverse, then resume the full renderer writer audit and gates.

The same run found a fixture syntax error in `natural-paged.wf`: GRAM-9 does
not admit a constructor in a call's atom argument. The control now binds
each Block and Flow value before passing it to `place_back`, as the ordinary
grammar requires; its values, inverse and writer are unchanged. Until its
rerun passes, it supplies no ledger, emission or runtime evidence.
Hosted [check 38094056543](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38094056543)
passed at `2083610c8cc1e5477bed68fc90ad01a9999ddd30`. This is prerequisite
validation only; no renderer storage has moved.

### Corrected control and blocked disposition

2026-10-10 23:21 UTC: Hosted
[proof collection 38094433125](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38094433125)
and [check 38094433121](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38094433121)
completed at `662ee4b311084148a5206e2494873a00b81a34e8`. The growth witness
again exits 1 with the exact RANGE-3 diagnostic above. The corrected natural
control checks, emits LLVM, builds and runs with `WF_WORKERS=4`, each with
exit 0; its runtime observes the expected origins 11 and 21 after the
permuted two-target update. The ledger reports:

```text
PAR loop        research/investigations/m2-paged/natural-paged.wf:20  loop  permitted   eligible; no accumulator
PAR split       translate_owner_suffix  loop at 3.0.5.0  split independent map over 3 captured bindings
```

In the artifact's `natural-paged.ll`, the reachable `wf_forward` calls
`wf_translate_owner_suffix`, which calls the split helper. That helper
contains `wf__par_acquire_lane(i64 64)` at line 833, publishes
`wf__par_thunk__par_split_translate_owner_suffix.0.0` at line 851, and joins
at line 861. This establishes a compiled task offer for the natural control;
it does not claim that the runtime schedules two tiny iterations on separate
workers, or that any renderer owner-motion writer has been parallelized.

The corrected run used hosted Ubuntu 24.04, AMD EPYC 9V45, four exposed
vCPUs. The first run used hosted Intel Xeon Platinum 8573C, four vCPUs. Both
artifacts identify compiler `wf-78223721f77d`, specification commit
`78223721f77db615c950b6df1bcc690629f9fe4b`, and compiler SHA-256
`5d3522d32388f5cc9596eedeea51fed8786df6b916b30103a550b0a1d5f9c99a`.
These are proof runs, not paired performance measurements.

| Acceptance comparison | Required workloads | Modes | Rounds completed | Verdict |
| --- | --- | --- | ---: | --- |
| Full style and full layout | ecma262, html5, apollo11 | Sequential and four workers | 0 | Unmeasured: adoption blocked |
| Every X5 edit | word, sentence, colour, fontsize, rootfont, block on all three pages | Sequential and four workers | 0 | Unmeasured: adoption blocked |

The pre-written baseline remains `030e4dd4081c9c15699363bdfa0e57c53a7f761d`
with the same pinned compiler for base, candidate and independent twins.
There is no adopted candidate revision or timing machine to compare. The
criterion is unchanged; performance is unverified and completion fails its
required proof condition. No renderer store moved to Paged, no invariant was
added to the renderer, and no semantic maintenance mutation was run. The
required layout-check, q139, q140, complete oracles-m2 (including Apollo11
fallback follow-ups) and complete falsify-m2 matrix remain unrun for an
adopted final head; passing the ordinary check on these prerequisite changes
does not replace them. Final report and Draft PR record the documentation
head's own CI results after publication.

A separate read-only completion review covers the full four-file diff from
030e4dd through 662ee4b and this result record, relevant layout/pipeline
decisions, affected growth and owner-motion consumers, C3, released inverse
probes, the pinned specification and raw hosted artifacts. Finding R1 was
the invalid constructor argument syntax, corrected without changing values
or proof obligations and now accepted by hosted execution. G2/G3, DC1/DC2,
R3 and unchanged-pin T4 pass within this prerequisite scope; G1/DC3/C4 are
not applicable. DC4, renderer-wide parallelism, remaining gates and acceptance
timing remain unverified. No local suite was run or green suite repeated by
the reviewer.

Stopping reason: step 2 needs the owning language session to resolve
`sg-paged-grow-inverse`; dependent implementation, semantic mutations and
acceptance cannot proceed under the pinned release. No new direction was
chosen, so the existing owner-approved inverse decision remains unchanged
and there is no new decision card or design log entry. A future sparse-route
port retains a separate proposed deferral, `sg-paged-sparse-routes` (P2):
its implicit absent high-water prefix must not be materialized without an
owner decision and construction-cost evidence. No files from the concurrent
fallback-design work, status board, pin or submodules changed. All execution
was hosted; the branch remains Draft in
[PR 61](https://github.com/Ming-Research/Snowghost-wf/pull/61).
