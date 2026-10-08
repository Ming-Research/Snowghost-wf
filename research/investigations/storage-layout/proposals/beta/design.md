# Storage from proof obligations

This is a proposal and a set of source-inspected mocks, not an implemented
Whitefoot extension or a renderer patch. The two proposed capabilities are **C1,
sealed relational containers**, and **C2, an indexable store of stable cells**.
C1 is the primary proposal; C2 is a conditional storage candidate whose kernel
necessity is not established by these mocks (see the native-page alternative
below). They deliberately do not include returned references, stored references, an
unchecked constructor, a new parallel scheduling construct, or a general region
lifetime system. The unresolved costs are part of the result; see
[friction.md](friction.md).

The source baseline is Snowghost `49c138aa666c3c8e474267fe4d24ae1ae92c2419` and
[Whitefoot `f949e676acfa811f96b21afd07f02c06dcd14b51`](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/spec/kernel-spec.md).
The brief's pin is the language authority. Sources were read, not compiled.
The mocks are proposals inside Markdown fences: ordinary statements follow
Whitefoot's canonical form; every departure is identified below. Library
algorithms remain library algorithms, and their verification obligations are
listed rather than attributed to a nonexistent compiler run.

## Obligations before representations

Let `P` be a payload store, `E` an entry store, `O` one owner's ordered index,
and `S` a selection of entries. A key includes its slot and generation. Its
meaning is local to one particular store, not to all stores of its type.

| Obligation | Fact that must belong to the data | Consumers |
| --- | --- | --- |
| A selected place exists | key belongs to this store, slot is allocated, cell is live, generation matches | All workloads |
| Two sparse writes differ | `S[i] != S[j]` for `i != j`; entry target's **stored** back-link is the corresponding stable entry key | W2, W3, W6 |
| A tag-dependent projection exists | a selected `Item::Block`, `Text`, or `Child` refers to the corresponding payload variant | W2–W7 |
| Independent recursive calls do not interfere | left, own, and right entry subtrees have disjoint entry sets; nested owner subtrees have disjoint payload sets | W1, W5, W8 |
| Reads do not race with writes | every read/write pair is compared through its complete field path, including helper rows | W2–W7 |
| A parent's output is available | recursive child results precede their parent's composition; no global depth barrier | W2, W5 |
| A bulk destination is safe | exact lengths, checked total weights, disjoint half-open output ranges | W5, W6, W8, P10 |
| Proof survives a call | the callee exports the same relation and its support; facts do not depend on private source inspection | W1–W8 |
| Proof survives a mutation | the mutator reestablishes the container invariant on its changed support, and frames the rest | W1, W2, W6 |
| A proof-only argument is free | its declaration identifies an erased proof parameter; no executable read, release or address use | W3, W7 |

Injectivity of entry keys alone is insufficient: two different entries might
name the same paragraph. Conversely, an inverse alone is insufficient if a
selection repeats an entry. Both premises are needed. A distinct selection also
does not prohibit an iteration from reading another iteration's output.

## C1 — sealed relational containers

### Semantics

Extend TYPE-11 beyond its current nongeneric scalar relations. A library type
may publish a **checked predicate** over its owned representation, including
bounded quantified projections through array elements, record fields and
refined enum payloads. Structural predicates may recurse over an owned finite
partition, with an explicit decreasing natural measure. This is an extension
to proof expressiveness, not permission to assert arbitrary propositions.

An invariant is established by constructors and preserved by **every** mutator,
on successful and error exits. A module may temporarily open its own invariant
inside an exclusive operation, but cannot expose that open representation to
clients or use the suspended invariant to justify accesses. Its unchecked
construction route does not exist. A public logical predicate may describe
private fields; its public signature exports the observations, proof obligations
and effect support clients need. The implementation must prove that export.
This is the proposed alternative to making all representation fields public
readonly just to satisfy MOD-6.

A fact attaches to the values and versions it actually concerns. For example,
`selection_for(s, scene)` depends on `s.keys`, the relevant live headers, entry
targets and payload back-links. It does **not** depend on origins or widths.
`current_order(s, owner)` additionally depends on that owner's topology version.
Writing geometry preserves the former by framing. Rotation preserves both by
its verified postcondition. Removal of a selected entry invalidates liveness;
insertion may preserve liveness and uniqueness while invalidating completeness
and current order. There is no one global epoch whose increment discards all
proofs, and no exemption from invalidation because an object is named “sealed.”

Selectors are owned key arrays or small tree descriptors, not stored borrows.
Their data may outlive a mutation, but their use requires the current matching
relation. A certificate supplies no dereference, extends no storage lifetime,
and grants nothing for a second store with numerically identical keys. For
storage across calls, a `Scene` owns both its tables and its retained indexes;
its type invariant relates them. Temporary selections receive relations by
verified postconditions. Moving a complete owner transports its relations;
moving or destroying one component without a preserving operation suspends them.
Raw external keys use an explicit checked lookup before receiving a relation.

### Checker rules, not an automatic theorem prover

The small proof kernel needs these explicit extensions:

1. Bounded RANGE terms may project fields and matched enum payloads below an
   element, including keys represented by integer tuples. Existence, tag and
   generation premises must be established before a projection contributes a
   fact. Such established existence facts can discharge ordinary access bounds;
   today's RANGE-2 deliberately cannot do this.
2. A sealed predicate has a finite list of support paths and verified
   introduction, elimination and preservation rules. The checker checks local
   store updates by same-index/different-index cases, and structural recursion
   by a decreasing measure and disjoint partition. It does not discover AVL
   invariants or accept a user-written axiom.
3. An effect may select a proved set of cells and a field below them. Two calls
   using one store are separable if their selected sets are disjoint, or their
   selected fields are disjoint. An untouched scalar field on that same owning
   record is consequently an ordinary read-only input. There is no broad
   `writes(scene)` row in an operation advertised as independent.
4. A contract-only reference parameter may be declared `proof`. It is checked
   at the source call and erased in the declared ABI of both caller and callee.
   Body reads, writes, address formation, ownership transfer and destructor
   obligations through it are forbidden. This is not speculative dead-argument
   elimination that would depend on reading a foreign module's body.

`apart(i, j) { }` still requests a checked two-iteration proof. It can instantiate
the container's exported predicates without a runtime scan or a producer's
loop invariant being in lexical scope. Ordinary arithmetic still obeys OP-2;
no saturation is used for counts, keys, generations or range endpoints.

### Operations and cost

A `Selection` constructor consumes a completed, proved traversal result or
checks an arbitrary input list. The latter has a real cost: a maintained
membership map gives linear work, or sorting and duplicate checking gives
`O(k log k)` work. Merely wrapping an arbitrary list in `Selection` is rejected.
The mocks take the former route: their indexes already prove tree membership,
and collection emits each member once into a disjoint destination interval.
Materializing keys is `O(k)` data work, performed once for two W3 consumers;
it is not a pass that reconstructs facts from scratch.

The inverse is `payload.back == entry_key`, **not** `payload.back == rank`.
Given targets equal, their back-links are equal, hence the entry keys are equal,
contradicting selection distinctness. This proof uses the field the application
already needs to find an entry from a payload. No proof-only inverse array is
needed. A permutation, filtered subsequence, or subtree of a proved distinct
selection stays distinct; concatenation additionally needs a disjointness proof.

Library types include `Ordered`, `Selection`, `Census`, `TreePart`, `IndexPart`, `Rebase`, and
`Reservation`. Their representation rules are below. They are not new kernel
container types. AVL repair, routing, free lists and summary algebra stay in the
library. C1 adds no runtime loads by itself; runtime headers, backlinks and
selection arrays have their explicitly listed costs. Verified evidence is erased.

C1 rules out duplicate scatter destinations, forging proofs by deserializing a
selector, using a stale selector after retirement, hiding writes behind a broad
helper row, and using an invariant while its supporting fields are open for edit.
It addresses P2, P3, P4, P7, P8 and the proof side of P9/P10; W1–W8 exercise it.

## C2 — indexable stable cells

### Semantics and operations

`Store<T>` is an owned sparse table of cells. `Key` is ordinary owned data
`(slot, generation)`, interpreted relative to a specific store. A store cell
contains a liveness header and, only while live, an owned `T`.

- `reserve(store, count)` checks address/count limits and reserves vacant cells;
  it returns an owned `Reservation` for distinct keys. It writes directory and
  allocation metadata. Failure occurs before any live value changes.
- `emplace(store, key, value)` consumes a reserved vacancy and initializes exactly
  that cell. Batch emplacement writes no shared length or live-count counter.
- `store[key].field` is a **place**, after current membership/liveness is proved;
  `&store[key].field` is an ordinary call-local borrow. A field read copies only
  that field. There is no helper returning `&T`.
- `extract(store, key)` consumes that live cell, returning its owned `T` and
  leaving a tombstone. Independent extractions write only their own cells.
- `retire(store, key)` drops the live value and leaves a tombstone. It does not
  push a shared free-list head inside a parallel loop.
- `probe(store, raw_key)` or `key_at(store, slot)` checks header bounds,
  generation and liveness and returns `Option<Key>` with a current relation.
  An external invalid key is reported, not silently substituted with a default.

Reuse is a library policy. A collected tombstone batch can be reserved again by
an exclusive allocator operation, incrementing each generation with checked
arithmetic; a generation at its maximum is permanently retired. No generation
wrap, and no resurrection of an old selection. Tombstoning and deferred reuse
are sufficient for all the mocks. Reclamation must account for any separately
retained external route: its old key remains an invalid key, never a new object.

### Native-page alternative: nonrelocation alone needs no new kernel

Today's types can already represent
`Box<Slots<Box<Slots<Cell<T>, page_size>>>>>`, where `Cell<T>` contains a
generation and an `Option<T>` or equivalent live/vacant enum. Outer growth moves
Box descriptors; the inner page allocations and their payloads do not move.
A caller can guard page/offset bounds and form
`&pages^.inner[page].inner[offset]` locally. A field-narrow helper takes that
reference and returns an owned field value. FN-5 callbacks can encapsulate a
lookup without returning references. This gives constant-depth lookup and
payload nonrelocation in today's language; the binary SlotPages tree is not the
only possible baseline. The same quotient/remainder address path can be used in
C2, and a `(page, offset, generation)` key avoids having to recover that pair from
a flat slot just to form the native place.

The remaining potential reasons for C2 are specific:

- Sparse **affine** payload initialization at reserved independent cells without
  first sequentially constructing a full Slots prefix of vacant enum values.
  A `T: copy` page can use filled Arrays; a general owned `T` cannot use
  `array_filled` to replicate `Option<T>`, even when its value is None.
- A checked logical indexed-place mapping, with precise fields and footprints,
  hidden behind a public Store interface. Otherwise each caller exposes native
  page paths, or uses callbacks whose projected effects need C1 anyway.
- Strong borrow preservation across descriptor growth, if a real consumer needs
  it. None of these mocks does, so this cannot presently justify a kernel change.

Native pages share C2's descriptor-copy, fragmentation and page-allocation
costs. Page construction and directory append may add chains from Slots length
updates, while C2 can reserve and initialize distinct headers/cells as a batch;
that internal independence must be demonstrated, not assumed from an opaque
operation name. C1 might be sufficient to describe an equally good native-page
library, leaving only ordinary lowering improvements. **If that library closes
the same proofs and initialization dependencies, omit C2 from the kernel.**
The proposed Store syntax is the mock's experimental interface, not a conclusion
that a new storage primitive is uniquely necessary. The first storage trial
must include this native baseline, not only today's recursive directory.

### Minimal shape and cost model

Use fixed-size payload pages behind an array of owning page descriptors. A key's
slot selects a page by division and a cell by remainder. A direct access needs
one directory-element load, a header load for a dynamic probe, and the requested
field load; a proved live key need not repeat the probe. An additional directory
base load may be required depending on register allocation. These are semantic
load paths, not measured instruction counts. There is no runtime-depth tree
walk. The page size is an implementation parameter to measure, not a semantic
constant or a per-workload special path.

Growing the descriptor array can copy `O(number_of_pages)` **descriptors**, with
amortized constant descriptor work under geometric growth. Existing `T` payloads
never relocate. Worst-case growth is therefore not constant latency. Allocation
is one block per newly needed page plus occasional directory growth, not one box
per cell. Pages initialize headers only; vacant payload bytes cannot be read.
Reservation returns an error for representational exhaustion; heap exhaustion
retains the language's STOR-8 behavior. A reservation of `k` cells is `O(k)`
header work and `O(ceil(k/page_size))` payload-page allocations in the worst case.

A field projection is supported on the original record, so W7 needs no column
layout feature. Physical AoS still fetches cache lines containing other fields;
this avoids whole-record value copies, not all cache pollution. The library may
choose parallel field-group stores when measurements justify them, with C1
keeping their domains aligned. That is a separate representation choice, not
an unmentioned automatic transpose.

Growth preserves already formed borrows into existing cells because only the
page directory moves. Retiring, replacing or extracting their cell invalidates
them. Moving/dropping the store invalidates all its borrows. A call that grows a
store and also takes an overlapping reference remains subject to EFF-5: address
stability does not authorize an overlapping call. The mock creates fresh borrows
at each use and requires no special surviving-borrow spelling.

Reservation/growth conflicts with fresh indexed accesses to that store until
the directory update completes; a relocating descriptor array must not race a
lookup. Element filling/retirement after reservation touches only its own cell
header and value. Headers must have independent writable storage (no shared
non-atomic bitmap word). Stable addresses do not remove these obligations.

The kernel owns the place mapping, sparse-cell initializedness, allocation,
nonrelocation and reference invalidation rules. The library owns keys, policies,
index balancing and selection predicates. This is one additional storage shape,
not a pointer API. It rules out compaction that moves live payloads, interpreting
a vacant payload, observable addresses and reference-returning accessors.
It addresses P1, P2, P5, P6 in part, P7 and P9; all workloads can use it, with W8
intentionally retaining today's contiguous Array scratch where that is cheaper.

## Library model used by every mock

The fences are implementation-record fragments against this proposed library,
not eight standalone runnable programs. All called operations are specified here
or in the workload that uses them. Routine renderer arithmetic is reduced to an
explicit model: nonnegative, bounded exact vertical extents, a baseline (including
absence), and an intrinsic width. `Summary` equality compares all these fields.
`join` adds extents exactly, takes the last present baseline translated by the
left extent, and takes the maximum intrinsic width. Counts/event weights are
checked separately. The valid-domain predicate bounds total extent and counts
before construction; mutation preflight reports overflow before publication.
This ordered composition is associative in that exact domain, not commutative.
No mock reassociates signed saturating geometry, floats, or CSS margin transfers.
A production port must retain Snowghost's richer `SequenceOutput`, ordinary-flow
preflight and full equality; the simplification does not establish CSS fidelity.

The logical representation is:

| Type | Runtime data and owned storage | Checked property |
| --- | --- | --- |
| `Scene` | `Store<Entry> entries`, `Store<Payload> payloads`, synthetic root `Ordered`, paragraph `Census`, immutable `Inputs`, scalar `Common` | All live entries target live payloads of the right tag; target back-link is that entry; every payload has one entry; owner's parent links form a forest |
| `Entry` | owner key, `Item` enum target, `Links` group, leaf and aggregate `Summary` | Belongs to exactly one owner's index |
| `Payload` | back-link, parent owner, census position/temporary retirement mark, `Geometry`, `Body` enum (`Block`, `Paragraph`, `Child`), semantic summary | Its back-link's target is this payload; paragraph body owns its growable `Store<Piece>` |
| `Ordered` | root key, count, total events; index links live in `entries` | AVL balance; subtree membership is disjoint; parent/child links agree; sizes/weights exact; inorder is the owner's order |
| `Selection` | ordered array of entry keys | Distinct live entries; optional current-order/completeness relation to one owner; no Close events |
| `Census` | initialized backing key Array, logical live-prefix count, inverse dense position in paragraph metadata | Lists each live paragraph once within that prefix; single deletion swaps one key, batches use disjoint hole/tail repair; unused key-buffer cells confer no liveness |
| `IndexPart` | root plus a direct-index count | One owner's direct-entry subtree, excluding nested owners; split halves are disjoint and strictly smaller |
| `TreePart` | root and finite membership descriptor, no enumerated copy of descendants | Descendant partition of the index/owner forest; children disjoint, strict size decrease |
| `Rebase` | source/destination reservation descriptors, one map per store domain | Total and injective on private live keys; maps never use saturating addition; image disjoint from retained live cells |
| `Reservation` | fresh cell interval(s), generations | Distinct vacant destinations; affine split/concatenate does not duplicate a vacancy |

`Inputs` is a read-only table keyed in the payload domain during a pass; the
builder/insertion/splice operations install or remap the corresponding input
record together with each payload. Its field effects are disjoint from geometry.
`BoundaryChange` contains owner, `entry_key`, output and shift; `EventPosition`
contains `entry_key` and within-entry offset.

The synthetic root uses an `Owner::Root()` tag; real blocks use
`Owner::Block(key: ...)`. Root is not an integer sentinel that can accidentally
index a store. `Item::Block`, `Text` and `Child` each carry a payload key.
A stored entry occurs once; Close is synthesized only in an event stream and is
never part of a scatter selection. The reduced model omits Float/Out: their
mutable placement depends on BFC state, so treating them as ordinary independent
geometry would be false.

### Notation used in fences (all hypothetical)

- `Store<T>`, indexing a store by `Key`, and the operations above are C2.
- Predicate calls in contracts, `proof x: &T`, named support sets in effect
  paths, and their use by an empty `apart` clause are C1. For example
  `writes(scene.payloads[selection.targets].geometry)` denotes the exact
  payload-key image of that selection in this scene, not its own backing array.
- A `.members`, `.targets`, `.subtree`, `.entry_cells`, `.payload_cells`, or
  `.reserved` suffix in an effect row is a logical selector, not executable
  traversal or a copied list. Public operation signatures export these selectors
  and their support. A caller cannot invent one from an arbitrary integer.
- The public logical effect views in W3 (`index_links`, `index_root`,
  `item_targets`, `line_state`, `origins`, `widths`, `width_inputs`, `constants`)
  are checked aliases for private support paths. Provider signatures and bodies
  use the same exported view names; consumers do not gain private field access.
- `tree_split` returns three owned descriptors for disjoint parts; it loads
  constant-size root metadata. It does not enumerate a subtree. Recursive
  library proofs establish its partition relation.
- `select_key`, `part_key` and `reservation_key` return owned keys with verified
  membership and injectivity postconditions. `select_key` reads a selection
  element; it does not perform a search.
- `same_summary`, `join`, `leaf_summary`, `lift_summary`, `width_rule`, and
  `piece_width` are ordinary library functions implementing the bounded model
  just described. Their rows read only their arguments; they cannot access a
  store secretly. `empty_summary` is its identity; `empty_geometry` has zero
  origin/width; `make_*` constructors set all record fields.

This notation deliberately exposes new proof and effect semantics. Ordinary
function-looking names do not imply that these contracts can be expressed by
the current FN-8/FN-9 fragment.

### Dense membership under a batch mutation

One dense context-wide Census is useful for W4, but repeated `census_detach`
operations contend on its last key/count and can update another owner's inverse.
Those operations are **not** independent just because their removed owners are.
A batch uses this checked library algorithm instead:

1. Reserve key-buffer capacity for the final size before exposing destinations.
   Mark the `r` removed paragraph keys in their own transient retirement fields,
   in parallel; marks are not live-cell retirement and do not break back-links.
2. Let the old count be `n` and `m = n - r`. Independently collect removal holes
   below `m` and surviving keys in the old tail `[m, n)`. There are equally many
   of each. A parallel prefix compaction produces dense `holes` and `survivors`
   arrays. The tail test reads those retirement marks; there is no shared hash
   insertion or repeated tail-pop. Both source lists are snapshotted before writes.
3. Zip the arrays: iteration `i` fills unique key-buffer position `holes[i]`
   from unique `survivors[i]`, and repairs that surviving payload's census inverse.
   Then fill distinct positions `[m, m+a)` for the `a` new paragraph keys and
   their inverses. New payloads are disjoint from retained survivors.
4. Publish logical count `m+a` once after the fills. Key-buffer positions beyond
   that prefix remain initialized raw keys but carry no membership authority;
   removed payload marks disappear when their cells are retired.

Work is `O(r+a)`, span `O(log(r+a+1))` for marking/compaction/filling, plus an
occasional `O(n)` **key-buffer** growth copy and the publication boundary. The
parallel prefix operation is an ordinary divide-and-conquer library algorithm
over disjoint slices with checked bounded counts; it needs no new storage shape
or generalized reduction opcode. C1 exports distinct holes, distinct survivors,
equal lengths and their disjointness from new keys. Without these proofs the zip
is not certified. Individual W1 edits can use constant-work single removal, but
their full API includes this shared metadata and is not claimed independent.

The alternative of scanning stable payload high-water slots has independent
mutation but costs tombstone/other-kind visits in every W4 pass. Partitioned
owner-local census lists are another alternative with an extra traversal/index
for context-wide dense enumeration. The proposed batch represents the unavoidable
final complete-census dependency by one count publication, instead of imposing a
per-removal chain. Its extra scratch/compaction and proof costs must be measured.

## What the checked library must establish

These are induction arguments to implement and check, not additional trusted
primitives. Failure to verify one is a failure of the proposal.

| Operation | Establishment/preservation argument | Work and necessary order |
| --- | --- | --- |
| AVL insert/remove/rotation | Fresh vacancy is outside old membership; insertion unions one key. Deletion transplants links, never copies a survivor's payload. Rotation partitions `A, x, B, y, C` identically before/after and repairs each affected backlink and count. | `O(log n)` changed index cells; parent repair consumes changed child metadata. Independent owners need disjoint reservations, not a shared append inside their loops. |
| Bulk index | Split sorted distinct keys at median; recursively build disjoint halves; root consumes their heights/counts. | `O(n)` work, `O(log n)` span for an owner; no insert-at-end loop. |
| Ordered collection | Cached left count partitions destination into left, root, right; disjoint tree memberships prove all emitted keys distinct. | `O(k + log n)` suffix work; balanced recursion, not a shared `push` chain. |
| Entry/payload attachment | Initialize reciprocal links while invariant is open; close only when both directions and tags agree. | Constant metadata work per attachment; unsupported alias attachment rejected. |
| Recursive owner reduction | Left/right index parts and a block entry's nested owner own disjoint entry and payload sets; read only fixed inputs, write only summaries. | Sibling computations independent; combine waits for its actual children. |
| Splice remap | Distinct source keys map through distinct reserved keys. Replace each private internal edge by its image; patch only the new roots' external parent/seam links. Reciprocal relations commute with the map. | `O(new payloads + internal references)` work; preparation independent, one reservation/publication boundary. |
| Retirement | Detach an owner subtree, then operate on its proved unique payload/entry census. Each retired header invalidates only its own live-key facts. | `O(removed records)` work; no scan of retained records. Dropping nested owned pieces costs their size/pages. |

No per-consumer derivation loop appears in the mocks. The price is a stronger
library verifier. These induction arguments have been inspected, not checked by
an implementation of C1. A source-only exercise cannot honestly report a
compiler-certified verdict for a language extension that does not exist.

## Coverage and rejected extra features

| Problem | Treatment |
| --- | --- |
| P1 | C2 stable pages; C1/library AVL leaves old payloads untouched. |
| P2 | C2 context-wide direct keys; C1 exact selected effects. Today's FN-5 callbacks remain usable for genuinely owned recursive structures. |
| P3 | C1 field/enum inverse plus exact effect comparison. |
| P4 | C1 persistent predicates, support-aware framing and declared proof-argument erasure. |
| P5 | C2 direct projected places; no whole-record helper return. Physical column layout is optional library work. |
| P6 | C2 page amortization and vacant-cell initialization; scratch is owned once per pass. General arena allocation/bulk release and Array no-fill remain **unsolved**, not hidden in C2. |
| P7 | One library generational-key/tombstone protocol over C2; no per-container reinvention. |
| P8 | Checked library AVL with disjoint structural induction under C1, direct cells under C2. |
| P9 | C1 injective remap and publication protocol; C2 reserved destination cells avoid copying retained payloads. Fresh payloads still move once. |
| P10 | At this pin PAR-2 already admits a proved range argument `&ids[s*i+b..s*i+b+s]`. No new kernel capability for that exact case. C1 additionally handles stored disjoint variable ranges. Direct writes through several affine element maps are a different case. |

The P10 entry in [docs/todo.md](../docs/todo.md) predates the pinned rule as far as
this source inspection can establish; compiler behavior was not tested. Likewise,
WIN-1 already makes unused Slots payload bytes unobservable: eliminating their
clearing is an implementation improvement, not permission to read uninitialized
memory. Neither issue justifies another language feature on this evidence.

A flat relocating payload vector loses P1. An owned pointer tree preserves
payloads but adds address-dependent descent and coarse effects. A global dense
rank inverse adds `O(n)` metadata updates on front insertion. An implicit shared
free-list push serializes otherwise independent retirements. A universal region
lifetime feature would add escape and ownership rules to solve costs not measured
by these mocks; defer it until page allocation and the remaining scratch cost
are separated on hardware.

## Reading and validation

[W1](mocks/W1.md), [W2](mocks/W2.md), [W3](mocks/W3.md),
[W4](mocks/W4.md), [W5](mocks/W5.md), [W6](mocks/W6.md),
[W7](mocks/W7.md), [W8](mocks/W8.md) give the source fragments and loop proofs.
[today.md](today.md) provides the pinned-language comparisons.
Counts refer to lines in the code fences, including internal blank lines, not
Markdown or shared library definitions. They are **not** a code-size improvement
measurement: the originals implement more behavior and the mocks use an
unimplemented common library.
