# Storage substrate first

This is a source-level proposal, not an adopted Snowghost decision or a claim
of compiler acceptance. The baseline is Snowghost
`49c138aa666c3c8e474267fe4d24ae1ae92c2419` and Whitefoot
`f949e676acfa811f96b21afd07f02c06dcd14b51` (`wf-f949e676acfa`). No compiler,
build, benchmark, or CI run was made for this exercise.

## Recommendation

Add **two separable capabilities**:

1. **S1: an owned, paged logical sequence**, with constant-depth indexing,
   append without moving existing elements, and consuming whole-page transfer.
2. **S2: field projections and declared physical field groups**, making a
   scalar field a logical integer column without copying or maintaining an
   additional array.

Keep typed handles, generations, ordered indexes, inverse-index contracts and
pass scratch in libraries. Do not add returned references, persistent proof
objects, a new scatter rule, or a stride-window primitive. A general allocation
region does not survive the minimality test: W8 needs a single owned pass
buffer, not a new lifetime system. This leaves part of P6 unresolved, explicitly.

The result is a small **semantic** substrate, not a claim that every proposed
backend optimization is free. In particular, page-directory growth still moves
directory words; page transfer costs proportional to transferred pages; and
many tiny owners still need allocator work. [Friction](friction.md) records
these limits rather than concealing them behind an arena API.

## What the pinned language already supplies

The normative source is the [pinned kernel specification](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/spec/kernel-spec.md).
The following distinctions change the design:

* RANGE-1 admits integer elements of arrays, slots and segments, not
  `records[k].inverse` or a value below an enum payload. S2 exposes the former
  as a column; it does not teach RANGE to reason about arbitrary records.
* RANGE-1–3 already admit range requirements and postconditions. A producer
  can establish an inverse relation once and two consumers can require it.
  MOD-6 and the restricted TYPE-11 invariant grammar prevent packaging that
  as an arbitrary private, quantified container invariant. P4 is an abstraction
  limit, not a blanket inability to pass facts between functions.
* PAR-2 already permits writes below an affine-indexed element, including its
  owned boxes, and fixed/runtime-stride range arguments. P10's historical
  denial is not a missing rule at this pin. See the maintained
  [stride case](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/par2-pos-runtime-stride-range-helper.wf)
  and [owned-element case](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/par2-pos-element-subtree-writes.wf).
* A lookup can invoke a raw function-kind generic on a call-local reference
  today. The [hash-map interface](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/lib/std/collections/hash_map/module.wfm)
  and [implementation](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/lib/std/collections/hash_map/hash-map.wf)
  demonstrate this. Thus P2's inlining is not required by REF-3; the remaining
  costs are dependent loads, callback instances and coarse effect paths.
* The maintained [range scatter example](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/range5-pos-scatter-through-left-inverse.wf)
  is the proof oracle for W3. The [recursive range program](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/programs/compute/range_split.wf)
  and [radix-scatter program](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/programs/compute/radix_scatter.wf)
  supply the slice-recursion and owned temporary shapes used in W5/W8.

No statement here says that these source inspections constitute a fresh
compiler test. The stale P10 wording in `docs/todo.md` is left untouched under
the task's output-directory restriction.

## S1: paged logical sequences

### Semantics and spelling

**HYPOTHETICAL:** `Paged<T>` admits only `T: drop` and is a noncopy affine
owner with a logical `rows` sequence. Linear (`nodrop`) elements are excluded
from this minimum proposal; a future linear container would need explicit
consuming removal/drain operations, not an implicit drop exception.
`rows.len` counts initialized logical slots, including initialized tombstones;
`rows.cap` is reserved capacity. `&p.rows[i]` and `&p.rows[a..b]` are call-local
places, never values stored in a handle. Each live logical slot owns exactly
one T. Growth adds pages and never moves an initialized T or its field groups.

Operations used in the mocks have these contracts. They are primitive
specifications, not undeclared language magic inside library routines:

| Operation | Semantics and source effects |
| --- | --- |
| `paged_new::<T>()` | Empty owner; no payload allocation. |
| `paged_filled::<T>(count, value)` | Exactly count initialized copies; only for copy T. |
| `paged_push::<T>(store, value)` | Consumes value; writes store; returns old len, new len = old len + 1, returned index < new len. Caller proves old len below the logical ceiling. |
| `paged_reserve::<T>(store, capacity)` | Writes store's allocation metadata; len unchanged; no payload copying. Invalidates outstanding borrows conservatively. |
| `paged_page_rows::<T>(store)` | Reads allocation metadata; returns the positive row granule fixed by this store's layout. |
| `paged_adopt::<T, fn empty>(target, source)` | Consumes source, writes target. Calls the ordinary raw function-kind `empty() -> T pure` to initialize each padding tombstone, then transfers source pages. Returns exactly the smallest B-aligned base >= old target len; new len = base + old source len; old target elements unchanged; source slot i becomes base+i. Requires enough logical address space. |
| Ordinary scope drop | Visits live initialized values in logical order and frees backing pages and directory. Spare slots are never read or dropped. |

Allocation follows STOR-8's total-in-source behavior. Logical overflow is a
normal explicit error before mutation; it is never disguised as allocation
failure. Mocks bound row counts by `1073741824_u64`; address/layout arithmetic
still needs STOR-6's target check. `paged_adopt` is a consuming storage operation,
not a reference-returning lookup and not a concurrent publication primitive.

Ranges can cross page boundaries. This is a genuine storage/ABI extension:
a paged range has an origin, start, length and layout descriptor, rather than
pretending to be a contiguous pointer. Kernel range operations resolve logical
indices; a host interface requiring contiguous bytes must explicitly
materialize them. There is no implicit flattening fallback. Ordinary flat
Array ranges retain their current representation.

S2 also affects a whole-row `&T`: fields may reside in different groups.
Such a call-local reference retains the row and layout descriptor (or the
callee is specialized for that layout); it cannot masquerade as an ordinary
contiguous record pointer. Whole-value copies explicitly gather all fields,
and whole-row drops visit each owned field exactly once. Descriptor arguments,
layout dispatch or extra specialized bodies are costs to measure. The
two-load model below describes direct scalar access, not a promise that every
general whole-row helper has no descriptor overhead.

### Representation and cost

Use a flat directory of uniquely owned page allocations, not a page tree, a
hash map, or a linked chain. For page capacity B, slot i selects directory
entry `i / B` and offset `i % B`. B and the group layout are fixed uniquely
for each concrete T on the selected target; they never vary between two
instances of `Paged<T>`. Changing a page policy requires another declared
layout/type or another backend experiment, not a hidden instance setting.
Thus W6's private and retained `Paged<Parcel>` necessarily match. B is a layout constant;
power-of-two B avoids a general divide. A logical page can be a suballocation
of a heap slab, but an implementation must not put a shared mutable allocation
cursor in a paragraph's source effect row.

With the store descriptor cached, a random scalar read needs **one directory
pointer load plus one payload load**; crossing a nested store adds that store's
descriptor and directory access. A flat array needs just the payload load.
These are an address-dependency model, not measured instructions or cache
misses. Bounds, liveness and generation validation add their own loads. A page
walk can hoist the directory load across many sequential accesses.

Append costs amortized O(1), one payload-page allocation per B rows, and
geometric directory growth. A growth event copies O(number of pages)
directory words; it copies **zero old payload bytes**. It is neither worst-case
O(1) append nor zero movement of all metadata. If that is unacceptable, a
bounded reserved virtual directory is an alternative, with address-space and
platform costs; it is not silently assumed by this recommendation.

`paged_adopt` copies/relinks O(source pages) descriptors and moves zero payload
bytes. Same-type source and destination have identical page/layout parameters. A
partial final destination page is sealed with tombstones; a partial source
page remains partial until a later append fills it. Repeated tiny adoptions
can therefore waste nearly one page per splice. No forwarding table is added
to every subsequent access to avoid that cost.

### Checker boundary

The new storage recognizer exposes logical rows/ranges as existing sequence
places. Existing bounds, OWN-7, PAR-2's affine element and range premises,
RANGE and `apart` then operate on those logical places. The new obligation is
on the primitive implementation: distinct logical slots have disjoint owned
representations, and page adoption cannot leave two live owners of a page.

“Unchanged proof machinery” means unchanged inference rules and no new trusted
injectivity certificate. The admitted storage shapes, place elaboration,
layout/ABI lowering, initialization and release rules must be extended. A
literal claim of zero checker changes would be false.

Address stability grants **no additional reference survival**. A write of the
owning store, reserve, adopt, move or retirement still invalidates borrows by
REF-2. Callers resolve indices again after mutation. It also grants no
parallel append to one shared len: reserve/append operations on one owner
are ordered. Independent owners can allocate concurrently under STOR-8.

S1 addresses P1, P2, P6 partly, P7's backing, P8's backing and P9; it is used in
W1, W2, W4, W5, W6, W7 and optionally W8. It rules out arbitrary compaction,
hidden forwarding chains, contiguous-host-ABI assumptions and borrowing
through a growing owner.

## S2: projected fields with explicit layout groups

**HYPOTHETICAL:** `p.columns.f` is a non-owning *place spelling*, not a stored
reference and not a function result. Its elements are exactly `p.rows[i].f`.
Nested struct projections such as `columns.links.left` are allowed; enum
payload projections are not. A payload-dependent field must be explicitly
represented by a tag column and an initialized data column, or handled in an
ordinary matched row. An arbitrary gather of handles is not a projection.

The surface extension's declaration form is:

```text
layout SequenceNode {
  group topology(links);
  group semantic_own(own);
  group semantic_total(total);
}
```

W1 uses one combined `EntryCell` store: its physical groups are `links` with
`generation`, `payload`, `own`, and `total`. These groups share one page
allocation/directory; stable identity does not require three parallel stores.

This declaration is intentionally not presented as existing Whitefoot syntax.
Each field appears once. Each page has fixed, aligned group offsets; fields
within one group use the ordinary record layout. A column descriptor carries
the group offset and stride. One slab allocation can contain all groups of a
page, so grouping does not require one allocation per scalar column.

Rows and columns have one storage identity. `rows[i].f` aliases
`columns.f[i]`; two different fields of a row are disjoint under the existing
field separation rule. Before EFF-5, the resolver accounts for both spellings;
it must reject a whole-row writing argument alongside a read of its projected
field. There is no permission to treat two aliases as independent arrays.

For RANGE, a scalar projection is an ordinary logical integer sequence.
For `apart`, a projected scalar write is a single element. For dense PAR-2,
an indexed row continues to own all its fields and nested storage. These are
the same existing proof shapes. Normalizing the two spellings consistently is
the principal new compiler proof obligation, not an optimization assumption.

Read costs are S1's directory load plus only the selected group's loads. A
scalar in a record-strided group still consumes cache lines containing adjacent
fields; projection alone is not physical SoA. Split cold groups to reduce
traffic. Reads through `&row.links` copy neither `own` nor `total`; copy types
still copy exactly the selected returned group. No promise depends on the
optimizer eliminating a whole-record temporary.

S2 addresses P3, P4's representable public inverse, P5, and P8's hot topology;
it serves W1, W2, W3, W5, W6 and W7. It rules out overlapping layout groups,
implicit enum refinement, stored view objects and opaque quantified invariants.
Projection visibility follows the source field's visibility; it never exposes
a private field through a public alias.

## Libraries and deliberate non-capabilities

**Handles.** A nominal `EntryId` or `OwnerId` contains a slot and generation;
an entry also carries its owner's identity where it crosses owners. A slot
lookup checks owner/store identity, bounds, live state and generation. A raw
slot is enough within a frozen pass after validation. Two handles with
different generations can name the *same physical slot*, so handle inequality
is never an injectivity proof. Retirement clears live and increments generation;
at the maximum generation the slot is quarantined permanently. Reuse and
publication occur between passes. No process-wide unique counter is needed:
owner directory slots plus their generations supply the namespace. W1 shows
per-owner handles; W6 shows rebasing and retirement.

**Ordered index.** Retain an AVL of integer slots, cached subtree counts and
event weights, and separate semantic summaries. Insert/remove touch their
search/repair paths; payloads remain in their slots. Bulk build uses median
halves over the initial document-order run. This is library code, not a new
kernel tree or trusted acyclicity property. W1 keeps the actual Snowghost AVL
body as its library boundary and rewrites the storage-facing operations;
its dependency inventory is explicit.

**Facts.** Public slice parameters and RANGE contracts carry an inverse
relation across calls. A producer verifies or derives it once; writes to the
order/inverse invalidate it. Proof-only parameters still cross the ABI today.
The proposal deliberately pays that cost instead of hiding it in a new
certified-container kernel feature. W3 demonstrates two consumers and a real
establishment loop, including duplicate rejection.

**Pass storage.** W8's event array is allocated once in the pass caller and
borrowed by several walkers. Scope exit releases it. Unknown-size pending
lists can use S1 and allocate only initialized prefixes. No reference escapes,
no uninitialized element is read, and there is no unsafe “assume initialized”
operation. Known-size parallel fill still pays the existing filled-array
initialization; removing that cost is deferred. General regions, heterogeneous
bulk destruction and cross-owner slab leasing are not quietly bundled into S1.

**Stride.** W7 uses the existing range-reference form for sixteen-element
windows. A physical field stride belongs to S2's layout descriptor; an
iteration's logical window partition belongs to existing PAR-2. They are
different concerns.

## Workload and problem coverage

The eight files are individually simplified module excerpts, with dependencies
and hypotheses named in each. They are not one concatenated renderer program;
for example W2 substitutes a small boundary type for W1's full transfer. Only
today.md's W3 fence is offered as a complete source bundle. Code fences use
canonical source form; hypothetical storage types, places and operations are
marked in the surrounding prose rather than using nonexistent source comments.

| Workload | Shape and primitive use | Independence argument / remaining cost |
| --- | --- | --- |
| [W1](mocks/w1.md) | S1 nodes; S2 topology/summary projections | Ordered AVL ancestor repairs; no old payload relocation; index algorithms remain library code. |
| [W2](mocks/w2.md) | Flat S1 owner lookup; S2 direct-entry origins | Parent needs child's new boundary; direct suffix scatter uses W3's inverse, no descendant translation. |
| [W3](mocks/w3.md) | S2 semantic inverse/geometry columns; flat or paged backing | RANGE left inverse, established once, required by two later passes; no new proof token. |
| [W4](mocks/w4.md) | S1 paragraph rows with independently owned growing pieces | Dense affine index owns the whole paragraph subtree; allocator must avoid contention in practice. |
| [W5](mocks/w5.md) | S1 document-order construction; S2 index fields | Close fixes each owner's run; disjoint median halves and event slices, child totals before parent. |
| [W6](mocks/w6.md) | S1 private pages/adoption; S2 identity columns | Parallel private rebasing, publication barrier, dense tombstoning; page padding and reference rewrite remain. |
| [W7](mocks/w7.md) | S2 narrow field groups over S1 | Dense column reads; existing fixed-stride windows; no whole SequenceNode copies. |
| [W8](mocks/w8.md) | Lexically owned pass buffer, optionally S1 | Disjoint recursive fill, readers after fill, release after last reader; initialization and page release remain. |

| Problem | Disposition |
| --- | --- |
| P1 | S1 removes payload relocation and tree lookup; directory copies remain. |
| P2 | S1 makes owners directly indexed; today's FN-5 already avoids mandatory inlining. |
| P3 | S2 exposes integer inverse fields and scalar destinations; enum tagging needs an explicit representation. |
| P4 | Existing RANGE contracts + public projections; private persistent invariants and erased parameters remain gaps. |
| P5 | S2 avoids unwanted value copies and permits physically separate groups. |
| P6 | Fewer page-tree allocations, lazy prefixes and one pass buffer; tiny-owner allocation and clearing are unresolved. |
| P7 | One library handle protocol over S1; no new kernel generational type. |
| P8 | Existing AVL algorithm over constant-depth storage; balanced index itself is not free. |
| P9 | Consuming page adoption, explicit identity rebasing and tombstones; no payload relocation, O(pages + identity edges) work. |
| P10 | Already specified at the pin; source-level witness in W7, no new primitive. |

## Removal tests and alternatives, starting with dependencies

| Candidate / removal | Dependency chain | What breaks or gets worse |
| --- | --- | --- |
| Remove S1; use growable Slots | Same index proof, but growth copies the retained prefix | W1 violates the no-old-payload-copy requirement; W6 publication can relocate retained pools. |
| Replace S1 with recursive pages | One dependent branch/load per directory level | Semantics survive; W1/W2/W7 lose constant-depth access and helpers/code instances return. |
| Use one box per stable row | One pointer chase, independent allocation | Stable O(1) indexing survives, but allocation count and fragmentation make P6 worse; still needs a directory and transfer ownership. |
| Use virtual-address reservation | Direct base-plus-offset access, no directory-load chain | A credible equal-or-shorter dependency alternative; reserved address space, page commitment, platform support and whole-page adoption need experiments. Not rejected on implementation effort. |
| Remove S2; explicit public SoA | Same independent integer columns | All workloads can still be written, but representation/inverse/group plumbing is manual and whole-row ownership is harder to keep visible. S2 is a code-size/layout primitive, not required for mathematical expressibility. |
| Remove declared grouping but keep projection | Same source dependencies | Proofs survive; W7 may still fetch cold cache lines. Could ship projections first if hardware shows grouping adds no useful traffic reduction. |
| Add opaque certified selections | Producer-to-consumer dependency remains | Better abstraction for P4, but changes fact lifetime/invalidations and the kernel; not necessary for these mocks. |
| Add an allocation region | Same semantic parallelism, potentially fewer allocator operations | No workload fails without it; only P6's cost remains. Defer until allocation measurements justify an independent capability. |
| Add returned/stored references | Can save repeated lookup only if safe lifetime rules are added | No mock requires either. S1 lookup is already constant depth; REF-3 remains unchanged. |

The irreducible new *behavior* is S1. S2 is the smallest additional source
abstraction retained for this storage/layout task: removing it requires the
manual representation duplication the task is trying to eliminate. There is
no claim that two is a formal lower bound for every possible language design.

## First hardware experiment, not yet run

Start with the smallest useful indexed-read/append/publication sample, then
choose scale from its timing spread on the 14900K through CI. Use one source
algorithm and interchangeable flat-array, existing recursive-page, flat-page-
directory and reserved-virtual-range backends. Compare identical payload and
group layouts before changing layout as a second factor. Interleave before,
after and a same-source twin of the base as a noise control.

Count dependent loads, bytes copied at growth/publication, page/directory
allocations, slack, instructions and generated code size; measure sequential
and four-worker W3/W4/W5 and full html5 layout under the same compiler/settings.
Use the independent sequence/list oracle for W1 and seq/par byte equality for
scatter and reduction. Reject the paging recommendation if its extra directory
load erases the gain over the current owner-sized pages on full build, or if
small-owner/adoption slack or allocator contention dominates the target edit
mix. Reject grouping if it saves no traffic/copies with equivalent dependencies.
No performance value in this proposal is a new measurement.
