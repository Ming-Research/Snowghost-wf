# Friction and attempted falsifiers

The result is two capability **families**, not two tiny compiler patches. C1
contains four explicit proof/effect/ABI changes; C2 contains a new sparse storage
shape. No compiler, build, benchmark, repository change outside storage-mock,
commit or CI run was made for this task. Proposed certifications below are
source-level derivations, not an implementation's parallel ledger.

## F1 — W6 is the mutation stress case: identities are embedded

A private paragraph may contain many `Piece::Object(context: child)` records,
marks and atomic-inline records naming child contexts; entries and summaries
also hold handles. Publishing into another local key domain must rewrite all of
these, not just the root. If a private subtree has `n` records and `e` embedded
references, it costs `Omega(n + e)` work to move/rewrite it in this representation,
plus `O(r)` retirement work for `r` removed records and ordered-index seam work.
The bytes moved are fresh payloads; retained earlier payloads are not copied.

A packed private builder permits affine maps after checked reservation. A sparse
source needs a map keyed by `(slot, generation)`; building that map costs at
least one visit per live source key and its storage. Source extraction invalidates
liveness, so a Rebase is deliberately a relation over the **old identity domain**
and the fresh reservation, not a claim that source keys remain live. Reciprocal
entry/payload links must be rewritten consistently on both sides.

Counterexample to cheap maintenance: insert a subtree containing `m` paragraphs,
each with `q` object pieces, whose objects name private child contexts. Moving
only pages and changing one root leaves `m*q` references in the wrong domain.
A process-wide identity table could avoid that rewrite, but introduces permanent
lookup/ownership-domain costs; global sequential ID allocation is not justified
by any dependency between independent private builds. A page/domain namespace
scheme is another candidate, but makes reclamation and cross-domain references
part of the design. **Disposition: retain explicit rebasing and its cost; do not
claim constant-time publication or smuggle in global handles.**

## F2 — the persistent proof is the largest new mechanism

A field projection in RANGE is necessary but not sufficient. W5 needs recursive
partition facts and exact set effects; W6 needs preservation while a representation
is temporarily open. Today's TYPE-11 is limited to nongeneric scalar relations,
RANGE-2 cannot feed ordinary access bounds, and MOD-6 cannot export a predicate
mentioning private fields. Renaming a vector `Unique` solves none of these.

The W3 public-interface/client excerpts identify the cross-module proof and ABI
boundary, and the mocks identify producers and local preservation arguments, but
do not supply
an implementation of the C1 checker or a complete verified AVL library. In
particular, the tree-split/rotation/forest-membership induction and the verifier's
finite support calculus remain engineering and verification work. They must not
be treated as trusted library assertions. **Disposition: keep this limitation
visible. The first language trial should implement field inverses, framed
preservation and module exports on the small W3 case before committing to the
recursive effect-set part.** If the latter needs an unrestricted theorem prover
or whole-store validation, revise C1; the all-workload proposal has failed its
minimality test. No claim here is “every workload was compiler-certified.”

## F3 — page stores do not solve all scratch or small allocations

W4 still has pages/directories for many short paragraph-owned piece stores. A
fixed page size can waste almost a page per tiny paragraph; C2 does not establish
that it reduces their allocator cost. W8 still initializes a contiguous Array
with Gap values before overwriting it, and each ancillary array allocates and
releases separately. A store used as scratch would avoid initializing vacant
payload bytes but would add directory loads to every event read. That is a real
representation trade, not a free arena.

Existing Slots already forbids reading unused cells; removing unnecessary
clearing is a lowering improvement. Eliminating W8's Array initialization needs
a split-and-seal initializedness proof, or a verified compiler transformation
that proves complete overwrite before use. General region allocation additionally
needs containment, escape, element-drop and reclamation semantics. **Disposition:
defer both new facilities; retain the actual Array cost in W8 and measure C2's
small-store case before adding a third capability.** P6 is only partly addressed.

## F4 — independence does not remove ancestor-width dependencies

`prepare_local_widths` snapshots block inputs before independent calculations.
A sparse inverse proves distinct writes, but does not justify reading a parent's
width while another iteration overwrites it. W3 instead reads immutable source
inputs and recomputes each target's ancestor chain. That costs `O(sum depth)`
work. If immutable inputs are absent, materializing a snapshot costs `O(affected
inputs)` bytes/work; alternatively a parent-before-child calculation keeps the
true dependency edges but must avoid unnecessary level-wide barriers.
**Disposition: explicitly retain one of these costs, never label a mutable
ancestor read independent.** This is algorithmic work, not proof re-derivation.

## F5 — stable identity and current order are different facts

A dense rank inverse `payload.position == rank` makes a front insertion repair
every later position: `Omega(owner size)` metadata writes, even with stable pages.
The design uses `payload.back == stable entry key`. AVL rotations and insertion
change `O(log n)` index metadata and preserve existing back-links.

However, a materialized ordered Selection does not magically insert the new key.
Its distinctness and liveness can survive an insertion; its completeness and
current-order relation cannot. Removal invalidates liveness for selections
containing that key. Under the proposed support rules an intersecting selection
must be consumed, rebuilt, filtered with a checked operation, or explicitly
revalidated; there is no automatic invalidation subscriber list hidden in a type.
Repeated edits alternating with whole-owner traversals can therefore cost
`Theta(owner size)` materialization per edit. **Disposition: keep retained order
in the AVL; retain lists only when their actual workload reuses them (W3 twice).
Charge list materialization and its invalidation scope, not a global proof scan.**

## F6 — allocation metadata and reclamation can reintroduce order

Calling `reserve` on one store in every iteration would contend on its directory
and reservation boundary. W6 reserves known domains once before filling distinct
cells. Retirement leaves tombstones without updating a shared freelist or live
counter in each iteration. W4 grows distinct paragraph-owned stores.
A batch of independent unknown-sized builders needs private stores first, then
a parallel count/prefix allocation or a descriptor-domain design before merging;
no constant-time shared bump pointer is assumed to be proof-independent.
**Disposition: preserve explicit reservation/publication boundaries.** Reuse,
page reclamation and generation exhaustion need their own measured policy;
permanently retiring an exhausted generation prevents ABA without wrapping.

### Dense census updates also need a batch

A claim that distinct owners can operate independently after reservation would
ignore shared Census tail/count updates. W1's complete single-edit calls remain
exclusive. The proposed multi-owner/W6 batch
marks distinct removed payloads, compacts removal holes and tail survivors using
a parallel prefix, fills proved distinct holes/new positions, then publishes one
count. It costs `O(r+a)` work plus occasional `O(n)` key-buffer growth and
`O(log(r+a+1))` compaction span. It also needs temporary key arrays and the zip's
disjointness proof. **Disposition: fixed in the proposed batch algorithm; measure
it against owner-local census partitions if frequent structural batches make
this join dominate.** A loop of independent layout work never calls the shared
single-removal operation.

## F7 — whole-value moves, reads and helper rows matter

A helper taking `Entry` by value still copies it; one taking `&Scene` with
`writes(scene)` prevents separation even when its implementation touches one
field. W7 uses `&store[key].links`, returning a small Links value. W5's recursive
helpers publish selected field effects, and W6's key constructors read only
immutable packed-domain metadata. If the latter read the entire mutable private
store, its extraction loop would fail certification. **Disposition: require
these exact rows in the hypothetical module interface and test their substitution
across a real module boundary.** No address-stability argument excuses overlap.

## F8 — constant directory depth has memory costs

C2 replaces directory-tree descent with indexed descriptors; those descriptors
can relocate and an unlucky growth copies their entire array. Live payload pages
cannot compact. Fragmentation may retain many tombstones/pages, and generational
keys are larger than today's u32 slots. A direct field load avoids a 280-byte
value copy but can still fetch cold neighboring fields in AoS cache lines.
**Disposition: report amortized and worst-case costs separately; benchmark direct
AoS projection against the existing split representation before promising a
column-layout improvement.** No numerical speedup is claimed.

### Native page composition may eliminate the second kernel feature

A directory of owning Boxes already gives stable payload pages and constant-depth
access at this pin. C2 must earn its kernel status on independently initialized
affine cells and public indexed-place/effect abstraction, not on nonrelocation
alone. The mocks never require a borrow to survive growth. **Disposition: C2 is
conditional; compare with the native-page shape in design.md and omit it if C1
plus a checked library closes the same obligations without additional chains.**
This comparison is unverified, and is a more discriminating next step than only
comparing a new store to the recursive SlotPages implementation.

## F9 — exact arithmetic is part of the summary contract

A tree reduction does not make signed saturating addition associative. The mocks
use an exact bounded transfer model and compare extent, baseline and intrinsic
width on convergence. Production `SequenceOutput` also carries struts, through
state, handles, float exports and barriers; these cannot be omitted from its
semantic equality or replaced with the mock algebra. **Disposition: the model
is a storage/proof experiment, not a CSS behavior replacement.** Structural count
and range arithmetic must reject overflow, never saturate two distinct keys or
ranges onto the same address. A zero height delta with a changed baseline is a
required propagation case.

## F10 — two catalog limits need precise qualification at this pin

PAR-2 already admits a proved strided **range argument**, including fixed stride
16. The TODO's cited “not split” result is older source evidence; whether the
pinned implementation fulfills that rule was not tested. This is not a basis for
adding another storage feature. Direct writes via different affine element maps
and an arbitrary list of intervals remain different obligations.

Likewise, RANGE facts already cross function boundaries through explicit
postconditions and requirements, and FN-5 plus REF-1 already supports a shared
callback-based runtime-depth descent. The comparison in today.md uses the former;
the design does not misrepresent the latter as impossible. **Disposition: qualify
these findings here; leave docs/todo.md unchanged under the output-only constraint.**

## Loop and call audit

“Derived” below means under C1/C2's stated rules and the listed library contracts.
It does not upgrade the unimplemented producer proofs in F2 to machine evidence.
Serial loops are not certification failures when they carry a true dependency.

| Workload | Independent work and its derivation | Required order / remaining qualification |
| --- | --- | --- |
| W1 | Owner-local work after disjoint reservation and one batch census plan; bulk halves by partition | Rank/event descent and upward AVL repair depend on the previous node. AVL library verification remains F2. |
| W2 | Direct suffix scatter uses W3's inverse; collection writes disjoint ranges | Ancestor output depends on child output; stop compares the complete model summary. |
| W3 | Two `apart` loops use the same distinct-entry plus field-inverse relation; widths/common reads disjoint from outputs | Producer materializes once. Ancestor-input computation is real work, F4. |
| W4 | Dense Census is complete/injective; each matched paragraph owns all its pieces; Bool reduction is admitted | Per-paragraph streaming state is local. Existing paragraph-level parallelism is retained. |
| W5 | Recursive left/right/nested-owner sets and fields are disjoint; bulk build uses disjoint halves | Document walk state and each parent combine are dependent. No depth-wide barriers. |
| W6 | Source keys, mapped destinations and removed lists each distinct; header changes are cell-local; embedded piece loop maps its own slot | Reservation, publication and detach/retire boundaries; rebasing costs F1 and library verification F2. |
| W7 | Output index is the counted binder; all entry fields are read-only | Actual bytes loaded depend on physical layout; no whole record copy is required. |
| W8 | Structural weights partition left/own/right and Open/inside/Close; walkers only read one array | Walker stack state follows event order; Array double initialization remains F3. |

## Negative cases the language prototype must reject

These are inspectable falsifiers, **not tests run in this task**:

1. Construct Selection `[e, e]`; or distinct `[e1, e2]` whose items target the
   same payload. The first lacks distinctness; the second violates the back-link
   invariant. The two failures must be distinguished.
2. Change a target's `.back`, `.item`, live generation or owning store, then
   reuse an old relation. A geometry-only update must be the positive control.
3. Remove a selected entry and reuse its slot, including the maximum-generation
   boundary; an old key must never address the replacement.
4. Read another selected payload's mutable geometry in a scatter helper, or
   widen that helper's row to a whole overlapping object. Certification must fail;
   reading `common.scale` must continue to pass.
5. Name a proof parameter in executable code in a second module; reject that
   body rather than silently retaining an inconsistent ABI. Changing an exported
   predicate without rechecking its provider must not preserve old evidence.
6. Give two recursive parts overlapping membership; or make two supposedly
   disjoint output intervals overlap; or give a block weight smaller than two.
   Reject the claimed separation/access domain before lowering.
7. Rebase two fresh keys to one destination, omit a reciprocal edge rewrite, or
   overflow the reservation end. Do not accept a saturated mapping.
8. Stop W2 on unchanged height when baseline/intrinsic output changed. A later
   ancestor must still receive the changed model output.

## First hardware experiment

First establish semantic/checker evidence in Whitefoot CI: a minimal two-module
W3 fixture, both passes accepted in its parallel ledger, the negative variants
above rejected for the intended reasons, and byte-equal sequential/parallel
outputs. Then compare same-source stable-store accesses against both native boxed-page
composition and recursive pages
on the owner's idle `14900k` runner **through CI**, with the required notice to
other sessions before a long run. No hardware work was authorized or done by
this source-only brief.

Use one small warmup/sample first to measure duration/spread, then select run
scale. Interleave baseline, C2 variant, and a twin baseline as a noise control,
with identical compiler revision/settings, dataset, workers and machine. First
workloads: W3 sparse field writes reused twice, W1 insert-at-front plus rank
queries, and the W6 object-piece-heavy splice that stresses rebasing. Record
payload bytes moved, directory bytes copied, allocations, emitted copy sizes,
proof-construction work separately from consumer work, wall time and scaling
at one and four workers. A repeated traversal hidden in a consumer, copying old
payloads on growth, or the supposed independent loops denied by the ledger
rejects the proposal before a speed comparison. If W6's reference rewrite or
small-paragraph allocation dominates after directory descent disappears,
reopen the relevant representation, not the safety requirement.
