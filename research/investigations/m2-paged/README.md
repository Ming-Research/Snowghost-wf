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

In the starting v0.121 specification, RANGE-2 explicitly forgets whole-window facts at non-tail operations,
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

### Storage-only continuation

The owner authorized storage adoption without adding the inverse invariant or
parallelizing owner-motion writes. This narrows this round's completion scope;
the prior performance rejection thresholds, output identity requirements and
all existing gates remain unchanged. The prior inverse-maintenance and emitted
owner-motion task requirements remain open under sg-paged-grow-inverse; a
successful storage comparison cannot satisfy that broader adoption criterion.
The owner-motion Decision in layout.md is unchanged.

Each Context root and each Block retains its own separate `Box<Paged<Flow>>`
and `Box<Paged<SequenceNode>>`. Stable slots, tombstones, AVL links, summaries,
range actions, existing slot ceilings and pending-list construction remain.
Built-in prefix initialization follows append order; topology construction
still splits independent runs and joins child summaries before the parent.
Growth moves no initialized element. Owner-motion publication is unchanged.
No inverse invariant, proof-only data or parallel owner-motion form is added.

Sparse route storage still represents absent prefixes without initializing
those cells. Its former shared slot accessors now live with routes.wf; changing
that representation is not required for the owner sequences and remains the
proposed sg-paged-sparse-routes decision. No status board is changed in this run.
The implementation, hosted evidence and failed performance criterion are
recorded in the result section below; final record-head gates are tracked in
the Draft pull request.

Empty sequences start with zero-capacity built-in stores, so they allocate no
payload pages before first insertion or sealing. The first insertion reserves
four logical slots and subsequent growth preserves the existing doubling rule.
The mutation inventory addresses semantic helpers rather than the removed
recursive leaf bodies; its existing range/transfer mutations retain their
faults and exact-match assertions. No mutation is removed or weakened.

#### Pending sparse-route representation decision

**Should sparse high-water route domains also move to built-in Paged?**

**Background.** `sparse_routes(length, missing)` owns a Vacant directory with
`len = length`, and materializes only touched paths. A later route at a high
identity can exist while all earlier identities are absent. Paged instead
requires every index below its length initialized. The owner-sequence port
preserves append-only dense stable identities and does not require this change.

**Options.** A (recommended): retain sparse routes for this storage-only round,
under proposed deferral `sg-paged-sparse-routes` (P2). This preserves their
construction work and keeps the owner-sequence comparison attributable; some
hand-written page storage remains. B: authorize dense Paged routes and measure
high-water sparse construction and peak RSS. This removes the directory but
adds work and initialized storage proportional to the absent prefix, risking
splice and fallback regressions. C: ask the owning language session for a
sparse built-in representation. This preserves absent-prefix semantics but
requires a separate language design and postpones route adoption.

**Confidence 4/5.** The two storage domains differ structurally; source
inspection establishes the added initialization under B, but its workload
cost is unmeasured. Measured small high-water gaps could make B acceptable.
No route representation change is selected; A is the continuation recommendation.

Before the first timing sample, the hosted reporter fixes an edit-kind cell as
the arithmetic mean over every timed ordinal of that script, with `style_us`
reported separately from layout/update microseconds. Full-stage cells subtract
T(0) from T(repetitions), divided by repetitions. Per-round values are retained;
paired-ratio medians and both independent twins determine the original noise
rule. A cell whose round classifications disagree is unverified. RSS is the
maximum process high-water mark across rounds, never a subtraction of peaks.

The full hosted comparison uses one job per page/mode. Each job keeps base,
base twin, candidate and candidate twin on the same runner for all three
interleaved rounds; no ratios cross machines. The independent sample builds
are reused only when the measured ancestor's renderer, compiler pin and kit
are unchanged. The artifact records the measured source revision separately
from the workflow revision. This partitions elapsed work without changing
the comparison or the prior criterion.

#### Hosted pilot and full-matrix scale

The [sample run 38096036798](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096036798)
built all four cohorts independently at base
`030e4dd4081c9c15699363bdfa0e57c53a7f761d` and measured candidate
`2c2c171911933aef499e0fb96a288643803eacd5`, using compiler
`wf-78223721f77d`. Its GitHub-hosted Ubuntu 24.04 runner exposed four CPUs
on an AMD EPYC 7763, Linux 6.17.0-1022-azure. The two smallest Apollo11
sequential samples were:

| Operation | First process ms | Second process ms |
| --- | ---: | ---: |
| Full style, one repetition | 214.290 | 218.915 |
| Full layout, one repetition | 308.411 | 302.452 |
| First two word edits | 329.581 | 326.703 |
| First two sentence edits | 331.300 | 335.554 |
| First two colour edits | 332.962 | 331.518 |
| First two fontsize edits | 328.994 | 328.817 |
| First two rootfont edits | 515.201 | 519.049 |
| First two block edits | 404.224 | 406.203 |

These are pilot process durations including startup, not acceptance-stage
measurements or candidate/base ratios. Full-stage pilot spread is about 2%;
the full matrix therefore uses 20 repetitions per full-stage process to
reduce startup-subtraction sensitivity, three interleaved rounds, and each
complete edit script. One job per page/mode bounds elapsed job duration;
twins and candidate/base comparisons remain on that job's one machine.
The sample's independent style builds took 156.03–173.40 seconds and layout
builds 497.06–564.51 seconds. Binary and input hashes, every build log, raw
samples and machine metadata are retained in the run's sample artifact.

#### Focused extension fixed before rerunning

The first three-round comparison has unresolved Apollo11 cells in both modes
and four-worker ecma262 cells. In particular, four-worker ecma262 full layout
has a median paired ratio of 1.0456 with 2% twin noise, but round classifications
disagree; this is unverified rather than a confirmed rejection. Apollo11 colour
layout updates include zero-microsecond observations, so their ratios cannot
be resolved from the first three rounds.

Following the prior instruction to extend only ambiguous cells, the next
comparison selects each unresolved full stage or edit kind. It uses 100
full-stage repetitions and five complete script executions per cohort per
round, still with three reversing interleaved rounds and all four cohorts
on one runner per page/mode. The edit-kind cell is the mean over every timed
ordinal of all five complete scripts in that round. Every repetition retains
the existing ordinal, refusal and non-timing-count checks; the reporter also
rejects missing or duplicated repetitions. Selecting an edit kind necessarily
observes both its layout and style components. No original result or threshold
is removed; all initial tables remain evidence. If the longer observation
still cannot classify a cell, it remains unverified; a zero-resolution value
is never converted to a pass.

#### Storage-only result and continuation decision

The same-structure candidate **fails the pre-written performance criterion**.
The [complete timing and peak-RSS tables](RESULTS.md) retain the initial
comparison and the focused extensions separately. The initial comparison
rejects sequential ecma262 full layout and fontsize updates, and four-worker
HTML5 full layout; longer selected observations also reject ecma262 four-worker full layout,
Apollo11 sequential block updates and HTML5 fontsize updates in both modes. Remaining noisy cells
cannot make these criterion failures pass. No storage redesign or threshold
change is made in response.

All requested correctness gates passed at measured renderer revision
`2c2c171911933aef499e0fb96a288643803eacd5`:

| Gate | Hosted run | Evidence |
| --- | --- | --- |
| check | [38096036768](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096036768) | Graph acceptance, ordinary checks and design lint passed. |
| layout-check | [38096036750](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096036750) | The compiler accepted pkg::layout with --check-module. |
| q139 | [38096070873](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096070873) | Independent reference and retained-identity checks passed in both modes. |
| q140 | [38096072343](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096072343) | Complete fixture gate passed; its semantic mutations also ran in the complete matrix below. |
| Complete oracles-m2 | [38096044985](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096044985) | All 20 jobs passed, including Apollo11's original 60 edits and 44 splice follow-ups matching full rebuilds in both modes. |
| Complete falsify-m2 | [38096043567](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096043567) | All 168 jobs passed, including Q139/Q140 mutations, range/transfer faults and detector controls. |

Final record-head validation is tracked in [Draft PR 61's validation table](https://github.com/Ming-Research/Snowghost-wf/pull/61).
The complete mutation inventory still applies: every relevant anchor remains in
a semantic helper, so no moved-storage mutation required respelling or removal.
The range-context-basis and range-splice-geometry mutants produce their intended
semantic failures; the legacy block detector observes two rebuild differences
in its intended interior-block case. Compilation failure never substitutes
for semantic detection.

The existing growth witness remains refused in
[hosted proof collection 38096036801](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096036801):
`grow-inverse.wf:20:3: error[RANGE-3]: UndischargedRangeFact`, at `return unit`,
missing `c^.targets.inner[c^.order.inner[k].Open.block].entry_slot == k`.
The collection job's success is not proof acceptance. No production inverse
or new parallel owner-motion form is added, and no new sound natural-form
refusal was encountered in the storage-only port.

Proposed deferrals, not filed on a status board in this run:

- `sg-paged-storage-cost` (P1): the candidate exceeds the unchanged full-layout
  and edit-cost thresholds. The cause within allocation, prefix initialization, access or emitted
  code is unverified; this is a performance lead, not a newly established
  compiler defect. Reopen after the direction decision below: isolate a
  minimal per-owner payload/metadata witness with the owning Paged session,
  preserve ownership and workload semantics, and require the same full-page
  criterion and correctness gates when verifying any fix.
- `sg-paged-sparse-routes` (P2): absent high-water prefixes still use sparse
  directories. Reopen only after the earlier representation card is ruled;
  validate high-water construction cost, peak RSS and splice/fallback identity.
- `sg-paged-small-edit-timing` (P2): some selected timing cells remain limited
  by noise or integer-microsecond resolution. Keep their unresolved status;
  further work is unnecessary to establish this candidate's rejection.
  Reopen if the owner selects another adoption trial and these cells could
  affect its verdict; improve the observation without omitting script
  ordinals or changing the threshold, and demonstrate missing/wrong-record
  detection before relying on the new observation.

The existing `sg-paged-grow-inverse` (P1) is already filed with the owning
Whitefoot session. Its minimal witness and acceptance condition remain the
natural growth form preserving the element-content inverse under the pinned
proof rules, followed by verification in the renderer's real writer families.
It is independent of the new performance lead.

**What should follow the failed Paged performance criterion?**

**Background.** The per-owner Paged port preserves outputs and passes the
required correctness gates, but fails the recorded full-layout and edit-cost
thresholds. Its precise cost mechanism has not been isolated. Changing owner
pooling, storage semantics or the acceptance threshold would start a different
experiment and would not resolve this same-structure comparison's failed criterion.

**Options.** A (recommended): keep this candidate Draft and ask the owning
Whitefoot session to investigate the built-in storage cost using a minimal
same-ownership witness before another adoption attempt, under proposed item
`sg-paged-storage-cost`. This costs a focused hosted investigation and possibly
a language/compiler change; the risk is that the measured overhead cannot be
removed under the present representation. B: end this adoption attempt and
retain the current baseline's hand-written owner stores. This avoids the
measured regression but retains their maintenance and the blocked inverse
proof; it yields no fix for the built-in representation's observed cost.

**Confidence 4/5.** The measurements settle rejection under the agreed rule.
The next investigation is recommended because the project exists to expose
language/compiler limitations, but the cause and fixability of this overhead
remain unknown. No new direction is selected in this run.

A separate read-only review covered the complete diff from `030e4dd` through
`d7e0a8c`, these completion records, relevant design ancestors and direct
consumers, and the retained hosted gate and measurement evidence. It applied
G1–G3, DC1–DC4, project checks R3/C4/T4 and the engineering evidence, experiment,
design and hygiene rules. One finding (R1), the stale recursive-directory growth
decision, was fixed by replacing that clause in place; focused follow-up review
confirmed the correction. No findings remain within scope. Raw evidence
inspection confirmed the independent cohorts, all twelve machine rows, rejection
and unresolved cells, peak RSS, complete mutation inventory and Apollo11
follow-ups. The review ran no builds, tests, checks or new measurements.
Final record-head gates remain pending here and are recorded in the linked PR
validation table when complete. Performance acceptance failed; eight timing
cells remain unresolved. The owner-motion Decision is unchanged; no approval or
design-log ruling is fabricated.

### Experiment compiler: inverse continuation

The owner's ruling on card sg-inverse-storage (choice A) places the inverse
on Paged elements; `research/m2-paged-inverse` resumes that work on the
existing per-owner Paged representation now that an experiment compiler
keeps element facts across growth. The branch starts from the
storage-only adoption and pins `wf-exp-174c2cd36590`: its release manifest
names Whitefoot commit `174c2cd365902d5256848a65e2bcf5ee84becc3b`, specification
v0.127. The earlier compiler was `wf-78223721f77d`, commit
`78223721f77db615c950b6df1bcc690629f9fe4b`, specification v0.121. No submodule
or design-tree decision changes in this continuation.

The experiment's ENT-5 relocation rule preserves the initialized elements
and length across `grow` and `grow_paged`; capacity facts and facts reached
through invalidated references still die. The first CI round must accept
the unchanged `grow-inverse.wf`, reject `grow-inverse-corrupt.wf` at its
inverse obligation, and retain the natural control's permitted loop, split
ledger, emitted LLVM and successful execution. Refusal of the corrupt proof
sample is static proof evidence, separate from the existing semantic mutation
matrix, which must still compile its mutants before detecting their faults.
The temporary workflow calls `check-proof.py` to enforce these outcomes and
reject altered copies of the evidence through the same verifier: failed or
missing statuses, an accepted negative sample, an unrelated or incomplete
diagnostic, missing eligibility or split evidence, and absent or empty LLVM.
CI retains the verifier and detector-control output in `gate.log`; these
controls run only in CI and do not rerun the compiler.

Static comparison of the specifications, maintained language examples and
standard-library interfaces found no necessary renderer compatibility edit.
The added swap placement restriction does not affect the renderer's owning
Box, aggregate or element exchanges. The first hosted round accepts the
unchanged renderer. The production Context invariant,
writer maintenance, owner-motion split evidence and production inverse-write
mutation follow only after this compatibility/proof baseline passes.

The writer audit identifies a real transient-state boundary to resolve before
adding that invariant. With one live root entry `Open(block: 0)` at slot 0,
`relocate_splice` can change the sole block's `entry_slot` to destination
slot 1 while `fresh.entries` still holds the original entry at slot 0. Its
`&Context` exit would therefore violate the proposed source inverse. A
publication transaction that consumes the prepared source is a candidate to
examine; no interface change or new design decision is made here. Narrowing
the borrow merely to avoid the Context obligation would not repair that state.
The hosted writer-boundary round below now establishes formation refusals
for the existing Boolean liveness guard and old-element frame contracts,
and an inverse refusal across ordinary `sequence_reserve`. The append helper
has not yet reached that proof question because its reduced witness had an
ownership-spelling mistake. These results block dependent implementation.
The renderer's retained reference writer is `translate_reference_owner_suffix`,
a sparse recursive AVL traversal; `translate_owner_suffix` names the small
proof control, not a current renderer function. Its eventual parallel form
must preserve that traversal's work bound and account for descendant and
atomic-child writes. The control's root scatter alone does not prove those
additional accesses independent.

The proof and timing workflows resolve the compiler from `whitefoot.pin`.
The existing correctness workflows are wired to the inverse branch, retaining
their full-matrix commit-message controls. The timing comparison still requires
identical cohort pins: its historical base has the old pin, so it cannot
measure this experiment without a separately prepared comparable baseline.
No new timing result or change to the earlier rejection criterion is claimed.

The owner committed and pushed the first step as
`ff7933bfc0f870fdf55bcfa981dfc1e2ae6f9cbf` and supplied these CI results:

| Gate | Hosted run | Result supplied by owner |
| --- | --- | --- |
| Proof samples and evidence controls | [38143114752](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114752) | Growth accepted; corrupt inverse refused at its inverse obligation; natural control eligible/split; verifier controls passed. |
| check | [38143114758](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114758) | Passed on the experiment compiler. |
| layout-check | [38143114774](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114774) | Passed. |
| oracles-m2 | [38143114771](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114771) | Passed. |
| q139 percentage and retained identity | [38143114747](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114747) | Passed. |
| q140 | [38143114763](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114763) | Passed. |
| falsify-m2 | [38143114812](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38143114812) | Still running when the owner sent the continuation; completed mutants had passed. |

The current session could not independently retrieve these runs because its
GitHub API connection is unavailable. No local compiler, build, test or
measurement ran, and no status board or approval log is written.

A separate read-only review (requested model: `gpt-6.1-sol`, high effort)
covered this first-step working diff
against `a9f3a69`, including the untracked negative proof sample and evidence
checker, relevant design ancestors, pinned proof rules and workflow consumers.
It found missing wrong/missing-input controls for the new evidence gate;
the shared verifier and hosted controls above address that finding, and a
focused rereview found no further actionable findings. The owner-supplied
hosted results above settle the baseline acceptance and control execution;
the production inverse remains unverified.

### Natural writer-boundary witnesses, before renderer implementation

The next hosted sample asks whether the existing liveness and helper
boundaries admit the owner's invariant, and whether consuming publication
fixes the source Context's invalid transient state. These sources are minimal
semantic reductions, not alternate renderer implementations. All keep actual
owner/order fields and runtime-capacity stores; no redundant inverse writes,
new truth fields, substituted integer liveness or runtime uniqueness checks
are introduced. No renderer interface or design-tree decision changes here.

The owner pushed the witnesses as `0d2be1757c0d168520bfd143d34b398fde69eecb`.
The downloaded artifact from [proof run 38148527940](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38148527940)
identifies that revision and experiment commit
`174c2cd365902d5256848a65e2bcf5ee84becc3b`, specification v0.127.
All nine samples returned 1. Workflow success means collection succeeded;
it does not mean any of these nine sources was accepted.

Classification: **1** is a witness mistake corrected here; **2** is a natural
language limitation retained unchanged; **3** is an intended sound refusal.

| Witness | Classification and consequence |
| --- | --- |
| [live-inverse-bare.wf](live-inverse-bare.wf) | **2 — proof / checker-range facts:** range guards require comparisons, excluding the ordinary bare Bool guard. Keep unchanged. |
| [live-inverse-equality.wf](live-inverse-equality.wf) | **2 — proof / checker-range facts:** the natural comparison with `True()` is excluded as a call. Keep unchanged. |
| [reserve-helper-boundary.wf](reserve-helper-boundary.wf) | **2 — proof / checker-range facts:** an ordinary helper's write forgets payload facts; its unchanged-length contract does not preserve the inverse. Keep unchanged, paired with its natural frame below. |
| [reserve-helper-frame.wf](reserve-helper-frame.wf) | **2 — proof / checker-range facts:** the old-element equality needed for the helper contract cannot read entry storage. Keep unchanged. |
| [append-primitive.wf](append-primitive.wf) | **1 — witness contract omission after the copy fix:** round three reaches a sound inverse refusal because the combined bounds/inverse clause is vacuous for out-of-range targets. Add the separate natural bounds requirement below. Primitive preservation remains unverified. |
| [append-helper-boundary.wf](append-helper-boundary.wf) | Round three reaches **RANGE-3 at a propagated error exit**. Correct the same **1 — bounds contract omission** with a separate requirement. The ordinary-call frame limitation remains independently established by the frame witnesses; whether this corrected helper reaches that refusal awaits CI. |
| [append-helper-frame.wf](append-helper-frame.wf) | **2 — proof / checker-range facts:** generic old-prefix equality cannot read entry storage. Keep unchanged. |
| [publish-borrowed-invalid.wf](publish-borrowed-invalid.wf) | **3 — intended sound refusal:** the source root inverse is false at its borrowed return after rebasing `entry_slot`. It fails precisely at that inverse obligation. Keep unchanged. |
| [publish-consume.wf](publish-consume.wf) | **2 — proof / checker-range facts, storage-operation result transport:** the destination exit cannot recover the transferred Block's inherited parent fact. Keep unchanged; no redundant parent store. |

The two copy-argument fixes change neither the inverse, storage shape,
contracts nor effects. OWN-1 requires bare use of copy values, but explicitly
allows generic `move` at concrete copy instances when the symbolic parameter
is bounded `drop`. The actual renderer Block owns Paged entries and is affine;
its real ownership spelling is not changed by fixing this scalar reduction.
See [OWN-1 at the experiment commit](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L652-L658).

#### Exact hosted diagnostic excerpts

Locations below are relative to `research/investigations/m2-paged/`;
the artifact retains the full source lines, markers and mechanical repairs.
These are observations of the pushed sources, including the two mistakes
before correction, not predictions about the next revision.

`live-inverse-bare`:

```text
live-inverse-bare.wf:25:138: error[GRAM-5]: UnexpectedToken
  expected: ["<", ">", "==", "!=", "<=", ">="]
  found: ","
```

`live-inverse-equality`:

```text
live-inverse-equality.wf:25:142: error[RANGE-1]: InvalidRangeClause
  reason: a range term calls a function
```

`reserve-helper-boundary`:

```text
reserve-helper-boundary.wf:31:3: error[RANGE-3]: UndischargedRangeFact
  fact: inverse
  site: a return
  missing: `c^.targets.inner[c^.sequence.payloads.inner[k].Open.block].entry_slot == k` (line 16)
```

`reserve-helper-frame`:

```text
reserve-helper-frame.wf:12:102: error[RANGE-1]: InvalidRangeClause
  reason: a range term reads an entry image
```

`append-primitive`:

```text
append-primitive.wf:21:48: error[OWN-1]: MoveOfCopy
```

`append-helper-boundary`:

```text
append-helper-boundary.wf:61:74: error[OWN-1]: MoveOfCopy
```

`append-helper-frame`:

```text
append-helper-frame.wf:9:40: error[RANGE-1]: InvalidRangeClause
  reason: a range term reads an entry image
```

`publish-borrowed-invalid`:

```text
publish-borrowed-invalid.wf:28:3: error[RANGE-3]: UndischargedRangeFact
  fact: root_inverse
  site: a return
  missing: `c^.blocks.inner[c^.order.inner[k].Open.block].entry_slot == k` (line 18)
```

`publish-consume`:

```text
publish-consume.wf:52:3: error[RANGE-3]: UndischargedRangeFact
  fact: root_inverse
  site: a return
  missing: `c^.blocks.inner[c^.order.inner[k].Open.block].parent == no_index` (line 20)
```

#### Rule ownership and next observation

The liveness pair isolates a missing Boolean guard in the range language:
[GRAM-5](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L318-L321)
requires a comparison, and
[RANGE-1](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L4089-L4102)
admits noninteger equality only between element projections or live own
bindings and excludes calls. `True()` is the correct Bool constructor under
[PRE-1](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L2393-L2396).
[FORM-5](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L117)
provides no Boolean literal and
[CONST-2](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L635-L650)
excludes enum constants. A Context invariant has no ordinary local truth
binding. Neither sample has a misspelled constructor to repair; changing
liveness storage or adding a truth field would conceal the limitation.

For helper preservation,
[RANGE-2](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L4107-L4115)
forgets locations written through an ordinary call and imports only declared
postconditions. The reserve length contract is insufficient for contents;
the two natural frame contracts state the missing old-element relation,
but RANGE-1 excludes their entry-image reads. Ordinary
[FN-9 relations](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L1443-L1449)
also exclude subscript datums, so scalar postconditions cannot express that
old-element frame. This is a contract/range-fact
expressibility gap, not evidence that primitive Paged growth loses facts.
[ENT-5](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L3608-L3618)
and RANGE-2 preserve the primitive growth facts already observed in the
accepted growth control. Corrected append-primitive should separate primitive
append preservation from the ordinary helper boundary. Corrected
append-helper-boundary may reach a RANGE-3 inverse refusal at a normal or
propagated-error exit; the round-two OWN-1 refusal proved nothing about that.

For consuming publication, the one-element source bounds and inverse are
already requirements under
[TYPE-11](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L423-L427).
They imply the sole source Block's `parent == no_index`. The consumed own
source has no exit-state obligation; only the written destination Context
owes the exit inverse. RANGE-2 treats an aggregate returned by a call as new
storage. Its special `take_back` definition preserves the remaining prefix
and length but supplies no relation from the returned aggregate to the old
last element; [PRE-1's take_back contract](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L2481-L2484)
publishes only length. The destination parent refusal matches this missing
returned-element transport. This attribution follows the specified proof
surface; the exit log does not trace intermediate compiler states. No extra
parent precondition is semantically needed, and a parent store would be
redundant. Ownership transfer itself was not refused. The responsible area is
proof/checker-range facts for storage-operation results, not paged/storage
or Paged growth. These limitations are identified here; no request was filed
into Whitefoot or the status board in this round.

The borrowed control is a different, sound refusal: a still-live source
order slot zero names a Block whose new slot is nonzero. TYPE-11 owes the
source exit inverse and
[RANGE-3](https://github.com/Ming-Research/Whitefoot/blob/174c2cd365902d5256848a65e2bcf5ee84becc3b/spec/kernel-spec.md#L4118-L4127)
refuses exactly its `entry_slot == k` conclusion at return.

#### Append proof result after correcting ownership spelling

The downloaded [proof run 38149272888](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38149272888)
identifies `8bf0196c66264247699b2df542ba7f495fd5fbd6`. All nine exit statuses
are still 1. The seven other diagnostic bodies are byte-for-byte unchanged
from the previous round, excluding timing lines. The corrected append cases
now report:

```text
append-primitive.wf:22:3: error[RANGE-3]: UndischargedRangeFact
  fact: inverse
  site: a return
  missing: `c^.targets.inner[c^.order.inner[k].Open.block].entry_slot == k` (line 12)

append-helper-boundary.wf:61:3: error[RANGE-3]: UndischargedRangeFact
  fact: inverse
  site: a propagated error exit
  missing: `c^.targets.inner[c^.order.inner[k].Open.block].entry_slot == k` (line 16)
```

The primitive refusal is sound for the written contract. RANGE-1 conditions
an entire clause on every read it forms being defined; the bounds conclusion
in the same clause as `targets[order[k]]` is therefore not an independent
bounds guarantee. Counterexample: `order[0] = Open(0)` with `targets.len == 0`
satisfies that clause vacuously. Appending `Block(entry_slot: 1)` activates the
inverse at order slot zero and makes it false. The earlier prediction that
the combined clause excluded this case was incorrect.

Both append writers now state exactly this separate ordinary requirement:

```wf
requires forall existing(k in 0_u64..c^.order.inner.len): c^.order.inner[k].Open.block < c^.targets.inner.len;
```

It reads only order elements and target length, so no missing target makes
it vacuous. A real writer can satisfy it because all live entries name
already-published targets before a new target is appended. In the production
inverse it will need its own bounds clause with the existing liveness guard;
the current Boolean formation gap still blocks that production expression.
No restriction on the appended Block's fields, runtime check, write or
representation is added.

The same entry requirement does not eliminate helper error exits. Even with
valid existing indices, RANGE-2 forgets the targets written through the
ordinary helper and its scalar length contracts cannot recover their fields.
The generic prefix-frame witnesses independently establish the missing
natural contract expressibility. The latest helper diagnostic alone does
not separate that limitation from the bounds omission; the next hosted round
must do so. Do not remove propagation or require away the error case.

Next CI should accept append-primitive with this added prerequisite and
record the corrected helper's first unconfounded result, expected to remain
RANGE-3 at the propagated error exit. These are predictions, not observations.
The seven unchanged cases and existing growth/corrupt-inverse/natural-split
assertions and recorder controls remain wired. No renderer writer, interface,
pin, submodule or design-tree decision changes. The confirmed gaps remain
Boolean guard formation, modular old-element frame contracts and removed
aggregate fact transport; request drafts are supplied to the owner in chat,
not maintained as repository artifacts. Production maintenance and publication
remain blocked on those gaps and the owner's interface choice.

`m2-paged-proof.yml` records each sample's raw status and complete diagnostic
log, with acceptance/refusal summarized in `writer-boundaries.tsv`. An exit
without the expected compiler diagnostic is an unclassified collection
failure. Successful collection does not establish acceptance of these new
samples; the earlier positive, negative and natural-split assertions remain
mandatory. The same recorder's classification/rejection path also receives
CI-only controls for a missing diagnostic, a crash status with diagnostic
text, and missing status or log files. Their detection output is retained in
`writer-boundary-controls.log`. In the downloaded round, all four recorder
controls detected their wrong or missing evidence. `gate.log` also confirms
growth acceptance, corrupt-inverse refusal, natural control eligibility,
emission and execution, and the established verifier controls. If consuming
publication is accepted, CI also builds and executes
its retained-prefix, transferred-geometry, stable-slot, target and owned-page
observations. Its one-leaf scope does not prove nested relocation or parallel
subtree publication. The observed consume refusal means its build and runtime
were not attempted in this round; no runtime publication result is claimed.

The production invariant is blocked: the rejected Boolean guard affects
every live/tombstone writer, and the rejected natural frame contracts affect
reserve and target append callers independently of splice relocation. The
natural witnesses and diagnostics remain unchanged; no different
representation or spelling is adopted.

The pre-push read-only review, requested with `gpt-6.1-sol` at high effort,
covered the complete witness-round diff against `ff7933b`, relevant
design ancestors, the pinned proof rules and affected renderer boundaries.
It found that the new refusal-classification gate lacked wrong/missing-input
controls. Those controls now share the actual recorder's functions; focused
rereview found no further findings within scope. Static G2/G3, DC1/DC2, R3,
draft-pin T4 and repository hygiene passed; G1/DC3/C4 were not applicable.
It missed the two concrete copy-value moves now exposed by CI and corrected
above. The downloaded diagnostics settle this round's nine refusals and
detector execution; corrected append results, publication runtime and
production inverse support remain unverified.

A separate read-only diagnostic review, requested with `gpt-6.1-sol` at high
effort, covered the ownership-spelling diff from
`0d2be1757c0d168520bfd143d34b398fde69eecb` subsequently pushed as
`8bf0196c66264247699b2df542ba7f495fd5fbd6`, all nine sources and logs,
manifest, controls, pinned rules,
relevant design ancestors and affected renderer boundaries. It found no
findings within scope. G2/G3, DC1/DC2, R3, draft-pin T4 and evidence/hygiene
passed; G1/DC3/C4 were not applicable. DC4 remains unverified for corrected
append acceptance and production/publication proof support. The reviewer
ran `git diff --check` locally; no local compiler, build, test suite or
measurement ran. Work stops for the owner's push of the separate append bounds requirements and classification before dependent
renderer changes.

A focused read-only rereview against `8bf0196c66264247699b2df542ba7f495fd5fbd6`
plus the separate bounds requirements and result-record update found two
wording findings, both corrected: the new requirement restricts the Context
domain, not the appended Block's fields, and OWN-1 describes round two rather
than the latest proof result. Rereview found no remaining findings within
scope. The bounds counterexample, unchanged error obligation and pending CI
predictions were checked by inspection; no local checks or execution ran in
this round.

#### Where should the prepared splice's ownership be consumed?

**Question.** Should relocation and publication consume the prepared source
within the destination publication transaction, or consume it at the earlier
private relocation boundary and return its existing owned fields?

**Background.** The current `relocate_splice(fresh: &Context, ...)` changes a
prepared root's `entry_slot` from private slot zero to the destination slot,
while its source root order still names that root at slot zero. Returning a
reusable `Context` at that point violates the proposed inverse. Preparation,
route construction and preflight planning still need the valid private
Context before it is consumed. The new borrowed witness represents this
invalid exit and is refused for that intended reason. The consuming witness
represents only one prepared leaf; its destination exit is refused for the
inherited parent fact, exposing the returned-element proof gap above.

**Options.**

- **A (recommended): consume at destination publication.** The dependency
  chain is preparation → route/preflight planning → consume/destructure →
  independent payload rebasing → existing target-pool prefix appends →
  matching owner-order linking → valid destination exit. Separate payloads
  have no rebasing dependency on each other; their completed contents and
  prefix publication determine when their order entries can be linked.
  Source-invalid values remain local to one ownership transaction, and its
  destination Context exit states the restored inverse. This requires
  changing the publication interfaces and carrying the source ownership
  through the checked target path. Nested targets and propagated exits still
  need proof; the leaf witness cannot settle them.
- **B: consume at private relocation and return the detached existing
  fields.** The chain is preparation → route/preflight planning →
  consume/destructure → independent payload rebasing → return those same
  owned fields → existing target-pool prefix appends → matching order
  linking → valid destination exit. This keeps relocation and publication
  as separate helpers and adds no retained storage representation. It adds
  a contract boundary that must describe the relation between multiple
  returned stores and their scalar bases; contracts cannot refer back to
  consumed source storage. Its interface and proof expressibility remain
  unverified, and the owner must confirm that this transient interface
  packaging fits the task's representation constraint before adoption. It
  cannot serve as a workaround if Whitefoot refuses A's sound natural
  transfer. Both candidates retain the same true prefix-append dependency;
  no measured speed advantage is claimed. A is recommended because its
  ownership and cross-field invariant are contained in the final publishing
  boundary rather than transported across another interface.

**Confidence 3/5.** The source mismatch and the preparation dependencies are
visible in the existing writers. The recommendation's proof transport
is blocked by the hosted leaf refusal; nested-subtree coverage also remains
unverified. This changes the proof evidence, not either candidate's true
data dependencies.
Neither alternative is adopted; the owner must choose before renderer
publication interfaces change. Clearing the soon-dropped source solely to
satisfy a borrowed exit is excluded by the task's redundant-write rule.

#### Range fixes in release wf-5b8bccb2d9be

Whitefoot#366, released as `wf-5b8bccb2d9be` (Whitefoot main `5b8bccb2d`,
specification v0.131), admits a bare Bool field or binding as a range guard
and makes `take_back` return the window's last element before the call, so
facts proved for that element while stored carry over. The table above
records the earlier experiment compiler; these are the front-end results
(`whitefootc --check`) of every witness here at the new pin, with
`wf-78223721f77d` as the old control.

- `live-inverse-bare.wf` is accepted; the old control still refuses the bare
  guard (GRAM-5). Reaching the declaration exposed a witness mistake, fixed
  here: `preserve` read nothing, so its exact effect row is `pure`, not
  `reads(c)` (EFF-2).
- `publish-consume-orphan.wf` is new: `publish-consume` plus the range
  requirement that every source Block has `parent == no_index`. It is
  accepted, and the old control refuses it, so the destination exit now
  receives the returned element's stored fact.
- `publish-consume.wf` is still refused for the same parent fact. Its source
  states that fact only through the order-indexed inverse; reaching the sole
  Block needs the deduction that `order[0].block < blocks.len == 1` names
  slot zero. That is a one-element case analysis, not the returned-element
  transport #366 fixed, and a real prepared splice with several Blocks would
  need a fact stated per Block regardless.
- `live-inverse-equality.wf` (a call in a range term) and both helper-frame
  witnesses (entry-image reads in range clauses) are refused as before; the
  frame pair waits on Whitefoot's helper-frame work.
- `append-primitive.wf`, `grow-inverse.wf` and `natural-paged.wf` are
  accepted; `append-helper-boundary.wf`, `reserve-helper-boundary.wf`,
  `grow-inverse-corrupt.wf` and `publish-borrowed-invalid.wf` reach their
  inverse refusals as before.
