# Friction, costs, and removal results

These are findings from source inspection and writing the eight mocks, not
compiler diagnostics or hardware measurements. The proposal is deliberately
conditional: two primitives cover the storage/access shapes, but they do not
by themselves eliminate every proof-construction or scheduling cost.

## F1 — small allocations and initialization remain

**Where:** W4, W5, W6 and W8; P6.

One paged sequence per paragraph still has at least one allocation unit when
nonempty. Several field groups can share a page allocation, but separate
owners cannot simply share one mutable source-level bump pointer without
ordering their preparation. W8 still initializes its fixed-size event array
and then overwrites it. Filling the final size in parallel is different from
appending an initialized prefix without clearing unused capacity.

**Disposition:** do not claim that S1 solves all of P6. Remove the region
candidate from the minimum kernel: these workloads still work without it.
Measure page/slab allocations and clearing first. A later region proposal
must show independent allocation lanes, non-escaping ownership and destruction
of nontrivial values; “one arena” is not an answer to those questions. The
source neither adds unsafe uninitialized reads nor hides a global allocator
cursor in every paragraph call.

## F2 — O(1) lookup still has an extra load, and zero relocation has a scope

**Where:** W1, W2, W6 and W7; P1/P2/P5/P9.

A flat page directory gives one pointer load before the requested field,
assuming the descriptor is already held. Flat arrays need no such dependent
load. A nested owner's local store adds another descriptor lookup. Generational
validation additionally reads metadata; a hot frozen pass can use already
validated slots. Directory doubling copies pointer words, though it copies
no existing payload. Whole-page adoption costs O(pages), not O(1).

**Disposition:** retain S1 as the nonmoving candidate, not as a measured win.
Compare a reserved virtual-address range on equal source and workload too;
it has a shorter address chain. If “zero relocation” includes directory
metadata, the proposed dynamic flat directory fails that stronger requirement.
Changing to a bounded reserved directory is a material representation choice,
not something to imply in a footnote.

## F3 — a storage primitive cannot manufacture an inverse or preserve a private proof

**Where:** W2, W3 and W6; P3/P4.

S2 lets RANGE read an existing integer field as a column. It does not make a
tree traversal injective. W3 shows an honest once-only validator and two
consumers. It adds a serial validation pass with early failure, and requires
the traversal's inverse to exist. W2's per-owner snapshots/validation can cost
O(direct entries), so it does not demonstrate the original logarithmic repair
plus suffix-only read locality. W6 similarly needs a validated removal list.

Public slice contracts carry the relation today; private quantified container
invariants and proof-parameter erasure do not. TYPE-11's restricted invariants
cannot be stretched into an `Injective<T>` fiction. A function's arbitrary
return value does not retain the proof without a postcondition. Mutating or
rebuilding either array invalidates the relation. Distinct generations of one
slot do not certify distinct writes.

**Disposition:** keep explicit contracts and count their data/ABI costs. Derive
the inverse in a producer that already needs a traversal, with a verified
postcondition, before claiming a production local-update win. That derivation
for the general edited AVL is **unverified here**. If a reusable private
invariant is mandatory, add it as a separately justified proof-system change;
the requirement that existing proof machinery apply unchanged would then need
revision. Do not silently award that power to a stable handle type.

## F4 — row/column aliases and a noncontiguous range ABI

**Where:** every S1/S2 mock, especially W3/W6/W7; P3/P5.

`rows[i].f` and `columns.f[i]` are the same place. Treating them as independent
array roots would unsoundly permit overlapping writes, drops or reads. A
paged/strided range cannot be passed as a contiguous pointer to a host call.
Logical projections require a coherent alias normalization and descriptor
lowering, not just accessor function names. A projected enum payload also
needs a refinement that a plain integer column does not supply.

A grouped whole-row `&T` likewise needs a layout/row descriptor or callee
specialization; ordinary helpers must not assume contiguous fields. Gathering
a whole-row value copies every field intentionally, and descriptor dispatch
or layout-specialized code can increase call overhead or code size.

**Disposition:** retain these obligations in the kernel boundary. Test negative
row/column alias cases, same-slot/different-generation scatter, whole-root
helper effects and ranges crossing page boundaries before benchmarking. Keep
enum payloads explicit or split tags/data deliberately. REF-3 remains intact:
all views are call-site places, no reference-returning API is added. REF-2
continues to invalidate borrows on owner mutation despite address stability.

## F5 — page adoption trades copying for slack and graph work

**Where:** W6; P7/P9.

Adopting at an aligned destination seals a partially filled final page. Many
single-node splices can waste almost one page each. Reclaiming tombstone pages
without preserving generations can resurrect stale identities. Adoption
transfers ownership, but cannot find or rebase arbitrary handles hidden in
renderer payloads; visitors must name every identity-bearing field. A
generation mismatch detects a stale link but does not make a splice's graph
correct.

**Disposition:** retain explicit relocation visitors and a preflighted seam.
Keep generation state for the live namespace and quarantine exhausted slots.
Measure tiny-splice occupancy. A library may instead move **new** payloads
once into retained spare slots, keeping all old payloads fixed; that sacrifices
zero movement of private payloads but may beat adoption for small inserts.
Do not select that alternative for these mocks without reporting the changed
guarantee. A two-level forwarding map avoids rebasing at the price of another
load on every later access; it is not the chosen default.

## F6 — bulk scratch and projections are not free by type spelling

**Where:** W5/W7/W8; P5/P6/P8.

S2's scalar projection over a hot group is still strided and can fetch nearby
cold fields. Actual physical group separation, and no whole-record temporary,
are both needed for the promised traffic/copy reduction. Splitting every field
into a separate allocation would worsen P6, hence the grouped page slab.
W8 already has one shared event array in current Snowghost; this proposal
cannot honestly claim to remove repeated event materialization there.

**Disposition:** keep grouping a separate ablation from paging. Inspect code
size and loads before attributing a speed change. Keep the existing flat
pass buffer when it has a known size; use paged scratch only when growth or
publication needs it. A general region and an uninitialized-fill builder are
not hidden inside the minimal proposal.

## F7 — close-time sealing exposes an extra scheduling boundary

**Where:** W5; P6/P8.

The document walk has true counter/stack/order dependencies. A completed
owner's median index construction does not depend on the next unrelated
document event. The straightforward source calls `seal` inside that walk;
Whitefoot may finish it before continuing the loop, imposing avoidable order.
S1 makes the data reachable and stable, but does not grant asynchronous
execution of a loop iteration or change its effects.

**Disposition:** the mock shows the requested close-time shape and records
this limitation. A bulk-only library can freeze at Close and seal all owners
in a later dense counted loop (the original `finish_tree_sequences` shape),
then reduce bottom-up. That keeps O(n) work and exposes sibling independence,
but moves actual sealing away from Close and adds a phase boundary. A claim
that exact close-time sealing also overlaps all unrelated later work remains
unverified; do not introduce an async primitive solely to conceal it.

## F8 — ordered-index and semantic-boundary correctness remain library obligations

**Where:** W1/W2/W5; P8.

Stable storage does not prove the AVL balanced, a cached event weight exact,
or a boundary composition safe to reassociate. W1 retains the actual existing
AVL library rather than pretending a one-line `insert` is a primitive. W2
models fixed-strut ordinary blocks and checks height, baseline and intrinsic
width; W5 models zero-strut wrapper blocks while using the existing transfer
library. Neither is a new proof of CSS margin/float behavior. The full source
still needs its travel/domain preflight before ordered summary regrouping.

**Disposition:** preserve those library checks and use an independent list
oracle plus reference layout on implementation. The original AVL is a code
dependency, not the correctness oracle. Do not change the semantic monoid,
introduce saturating identity rebasing, or hide unsupported CSS behind a
successful storage result. The bounded traversals fail on invalid paths;
tree invariants are not bestowed by S1.

## F9 — generations and retained namespaces have costs

**Where:** W1/W6; P7.

A nominal type prevents mixing kinds at compile time, not mixing two stores
of the same kind. The owner slot/generation namespace must be checked at an
external entry point. Every reused row needs a retained generation and a
live marker. Free-slot discovery can be a library freelist, but a shared
freelist mutated by every iteration creates a dependency. These mocks append
new rows and quarantine retired identities; they do not demonstrate concurrent
reuse or compacting stable stores.

**Disposition:** no kernel handle primitive. Use nominal structs, explicit
lookup, per-owner free lists outside certified passes if reuse is implemented,
and dense/affine or validated physical-slot selection while a pass is frozen.
Generation exhaustion is a permanent no-reuse state, never modular arithmetic.

## F10 — cost and acceptance evidence are deliberately limited

**Where:** all mocks and today.md.

No source here was compiled; no check result is represented as a gate pass.
Today's W1 is an exact existing-module fragment and W3 a complete source
bundle checked against the specification by reading only. Hypothetical files
are source excerpts with named library dependencies, not ready-to-build
renderer replacements. Their line counts include the displayed source and
exclude cited unchanged library bodies; they cannot substantiate a code-size
percentage or the removal of all of the historical 13,766 added lines.

**Disposition:** first validate primitive ownership/path normalization and
the RANGE producer/consumer cases through CI if this proposal is selected;
then use the hardware comparison in design.md. A failed proof needs a design
change or a documented residual cost, not a new unchecked success path.

## Catalog corrections found during this exercise

* **P2:** the pinned FN-5 callback and REF-1 cursor are already a compact
  alternative to inlining every descent. The remaining depth/load/effect
  cost is real. Disposition: account for it in today's comparison.
* **P4:** RANGE postconditions already travel through calls; opaque packaging,
  field admission and runtime proof-only arguments are the narrower gaps.
  Disposition: demonstrate the existing route in W3 and today.md.
* **P10:** fixed and runtime-stride range writes are already in pinned PAR-2
  with a maintained conformance example. Disposition: use them in W7, add no
  storage capability for them.
* **Source location:** the brief names `update.wf` for `translate_after`; the
  definition at this revision is in `renderer/layout/geometry.wf`, called
  from `update.wf`. Disposition: follow the definition as well as its callers.

These observations are recorded here because the task forbids editing the
maintained TODO outside `storage-mock/`. No Whitefoot gap was filed remotely,
and no pin or submodule was changed.

## Validation scope

The inspected repository revision is
`49c138aa666c3c8e474267fe4d24ae1ae92c2419`; this delivery consists only of
uncommitted files under `storage-mock/`. The pinned language was retrieved by
read-only `gh api` calls at the exact commit in the brief. Original function
and file sizes were counted from that repository revision. Each mock footer
counts its Whitefoot fence including blank lines, excluding prose and cited
library bodies. Today's six W1 functions were compared byte-for-byte with
their owning source. Local Markdown file targets and trailing whitespace
were checked. These are artifact checks, not Whitefoot acceptance tests.

A separate read-only completion review inspected all eleven deliverables,
the brief, relevant design nodes, the pinned grammar/proof rules and directly
referenced source. Repairs made during review: flat constructor/call syntax
and distinct match binders; an integer validator success payload admissible
for FN-9 routes; non-shadowing range-fact names; Paged's explicit `T: drop`
bound; exact adoption base/new-length semantics and same-type layout identity;
the grouped whole-row reference ABI obligation; and W2's use of the actual
`sequence_rank` adapter. The W5 wrapper's direct
count/event weight was corrected and inspected again. These changes add no
unchecked proof path.

The review checked
groups A, D, C, R, M and V, and found no unresolved actionable finding after
those repairs. Execution/acceptance items, parallelism completeness (F3/F7)
and compiler realization remain unverified. Gate/pin and PR-delivery groups
were not applicable under this task's restrictions.

No compilation, execution, performance run, project gate, design-lint, commit,
push or PR change was performed. Checker acceptance, target lowering, private
AVL inverse derivation and hardware costs remain unverified. The proposal
changes no approved design-tree decision and requests no operational approval.
