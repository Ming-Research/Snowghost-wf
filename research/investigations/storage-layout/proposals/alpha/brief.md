# Storage and layout capabilities for Whitefoot: a brief from Snowghost

Snowghost-wf is a web renderer written in Whitefoot (repository root: your working
directory). Its pipeline (style, layout) is meant to be parallel and incremental end
to end: every stage keeps only its algorithm's true data dependencies and writes all
other work in forms Whitefoot proves independent (AGENTS.md, "Design for parallelism
first"). Most of the optimization work of the last months has been a fight with the
current storage shapes: performance limits and proof limits. The owner wants to add
to Whitefoot a small number of general, low-level storage/layout capabilities that
solve these problems as a class, and keep paying off for future problems. Not one
feature per problem.

The method is code, not speculation: assume a capability, then rewrite Snowghost's
hard cases against it. Where the rewrite gets awkward, needs a second new feature or
an escape hatch, that is the finding.

## What Whitefoot is today (pinned release wf-f949e676acfa, commit
f949e676acfa811f96b21afd07f02c06dcd14b51 of github.com/Ming-Research/Whitefoot)

Read the specification `spec/kernel-spec.md` at that commit through
`gh api 'repos/Ming-Research/Whitefoot/contents/spec/kernel-spec.md?ref=f949e676acfa811f96b21afd07f02c06dcd14b51' --jq .content | base64 -d`.
Also look at `lib/std` there (for example lib/std/collections/hash_map) and
`tests/programs`. Facts that matter here:
- Owned values; `Box<T>`, `Box<Slots<T>>` (a growable vector: growth relocates its
  elements), `Array<T, N>`; references are call-local borrows: no stored references,
  and a function cannot return a reference (REF-3). Within one function a
  loop-carried cursor may descend an owned path of runtime length and write through
  it (REF-1's `R.**` cover; conformance cases ref1-pos-iterative-owned-link-descent,
  ref1-pos-wildcard-primitive-write).
- No closures or function values, but a generic parameter may be a raw function-kind
  parameter (`fn_sig` in generics, FN-5), instantiated explicitly; FN-6 refuses a
  recursive cycle that changes the function argument.
- Effect rows: `reads(path)`, `writes(path)`, exact and narrowable to fields; two
  arguments of one call may not overlap where one writes (EFF-5).
- Parallelism: `--par` splits counted loops the compiler proves independent
  (PAR-1/PAR-2): each iteration writes only storage indexed by the loop variable, or
  through index facts: RANGE rules and `apart(i, j)` certificates prove that a list
  of integer indices is injective (style's renderer/style/levels.wf uses this). The
  facts are loop invariants of the pass that derives them.
- Every integer operation is proved in range or saturating (OP-2); every index guarded.

## The problem catalog (all measured or observed in Snowghost)

Each item names where it hurts in the source. Read those functions; they are the
ground truth for the mocks.

P1. Growth relocates. `Box<Slots<T>>` copies its elements when it grows, and the
owner decided (Q114 A, design/pipeline/layout.md) that inserting an entry must not
copy earlier payloads. So the per-block entry nodes moved into a recursive page tree
`SlotPages<T>` (renderer/layout/module.wfm, renderer/layout/sequence.wf `slot_read`,
`slot_write`), where every access is an O(log n) descent through `Fork` arms.
Measured on an i9-14900K, html5 full layout: step 2 (flat arrays) 0.633 s; with the
entry sequences 3.407 s; after three repair rounds still 0.693 s seq (+10%) and
0.370 vs 0.293 s at four workers (+26%)
(research/investigations/structure-edits/runs/full-14900k.txt).

P2. Nested access of runtime depth. Blocks nest to data-dependent depth (up to ~30).
Update and splice code reaches a block from a changed entry by parent slots and
works on it and its ancestors (renderer/layout/boundary.wf `propagate_boundary`,
`boundary_owner_update`; renderer/layout/splice_boundary.wf). Moving the payloads into
their owners (branch research/m2-step3b-owned) inlined every descent: +13,766 lines,
update.wf alone +6,421. Today the payloads stay in context-wide pools
(`context.blocks.inner[slot]`), O(1) at any depth.

P3. Indirect writes cannot be proved independent. A flow-ordered list of slots
selects payloads, and independent iterations write `payloads[slot].field`
(renderer/layout/update.wf `translate_after`, `prepare_local_widths`). RANGE covers
integer-array elements, not a field below an element or an enum payload, so these
loops are not certified (docs/todo.md, "Flow-selected payload writes need a proof
over stored fields").

P4. Index facts do not travel. A traversal knows its level lists are injective, but
the facts are loop invariants of that pass; a public contract may name only public
fields (MOD-6), so the next pass re-derives them in its own counted loop
(docs/todo.md, "A write through indices the program knows are distinct...";
research/investigations/style/DESIGN.md, "The level cascade"). Related: a parameter
that only contracts read is still passed (docs/todo.md, "A function receives every
value its requirements name"), and reading an unwritten scalar field in a certified
loop denies it (docs/todo.md, "Reading an unwritten scalar field...").

P5. Whole-value copies. Reading one field through a helper copies the whole value
(a SequenceNode was about 280 bytes with two 130-byte SequenceOutput); memmove was
29.7% of full-layout samples until the node was split by hand into separately paged
field groups with field-narrow helpers (module.wfm `SequenceNode.links`,
sequence.wf). That is a hand-written column layout.

P6. Allocation granularity and scratch. Many small boxes: each paragraph owns a
`Box<Slots<Piece>>`, each block an entry sequence with its pages; malloc/free about
15% of samples; four-worker scaling worse than step 2. Per-pass scratch (the
materialized event array of `materialize_flow`/`fill_flow`, reduction snapshots,
pending lists) is allocated and freed per pass with no region to put it in. A local
`slots_new::<T, N>()` clears all N slots on creation (docs/todo.md).

P7. Stable identity reimplemented. Stable slots with tombstones, generations and
route tables are written again for each structure: `SlotPages`, `RouteTable`
(renderer/layout/routes.wf), context directories, style's stable slots
(renderer/style/structure.wf). Removal leaves tombstones; reuse needs generations.

P8. Ordered index with summaries. Per-owner AVL with subtree summaries, select by
event weight, bottom-up reduction, bulk build from sorted input
(renderer/layout/sequence.wf, boundary.wf). Probably library material, but it must
sit efficiently on whatever storage exists.

P9. Publication across trees. A splice builds a subtree privately, then moves its
payloads into the retained pools and rebases slots (renderer/layout/splice_publish.wf
`publish_splice_payloads`, `relocate_*`); removal retires a subtree.

P10. Strided windows. A counted loop writing `ids[u*16 .. u*16+16]` per iteration is
denied as overlapping (docs/todo.md, "A counted loop that writes a fixed-stride
window...").

## Workloads every mock must cover

Write each as Whitefoot source in the spec's canonical form, using the hypothetical
capability where you need it, clearly marked (for example a `// HYPOTHETICAL:` line
in a separate notes file, since Whitefoot has no comments; or keep the
hypothetical syntax in a fenced block of a .md file). Keep the algorithm's real
dependencies; take the shapes from the cited functions, simplified to their essence
but not to triviality.

W1. Per-owner ordered entries with stable slots: insert before an entry, remove,
select by rank, without copying earlier payloads (sequence.wf `insert_before`,
`remove`, `sequence_select`).
W2. From one changed entry, walk the ancestor chain of owners, recompute each
owner's summary and translate only its direct later siblings, stopping when the
output holds (boundary.wf `propagate_boundary`).
W3. Sparse independent scatter by a slot list, in parallel, proved (update.wf
`translate_after`, `prepare_local_widths`), with the injectivity fact established
once and reused by two later passes.
W4. Dense parallel pass over all paragraphs of a context, each writing only its own
paragraph and its own growable pieces (renderer/layout/prep.wf `prepare_context`).
W5. Full build in document order: nested blocks, each owner's entries collected and
its index bulk-built at close; then a bottom-up reduction over all owners, siblings
independent (build.wf, sequence.wf `finish_sequence`, boundary.wf reductions).
W6. Splice: build a subtree privately, publish its payloads into the retained
store, rebase identities, retire a removed subtree with tombstones
(splice_publish.wf).
W7. Field-narrow access to large records: read one field group of many nodes
without copying the others (the SequenceNode split).
W8. Per-pass scratch: a walk materializes an event array once, several walkers of
that pass read it, then it is dropped (sequence.wf `materialize_flow`, flow.wf
`place_context`).

## What to deliver (in your output directory)

1. `design.md`: the capabilities you propose, as few as possible. For each: its
   semantics, operations, cost model (loads per access, allocation, relocation),
   the facts it gives the checker (independence, injectivity, disjointness,
   reference survival), what stays kernel and what goes to a library, and which
   problems P1-P10 it addresses. State what each rules out.
2. `mocks/`: one file per workload W1-W8, written against your capabilities, with a
   line count and a note on the original's size.
3. `friction.md`: every point where a mock got awkward, needed an extra feature,
   an escape hatch, an unproved step, or a cost you could not avoid; for each, the
   problem it exposes and whether your design should change.
4. `today.md`: for W1 and W3, the same workload in today's Whitefoot (it must be
   valid at the pinned release; you may check syntax only by reading the spec, do
   not compile), to show the difference concretely.

Constraints: general low-level capabilities (each must serve at least two problems
and at least two workloads); no stored references, and no returned references
unless you show with a mock why that is the only way; parallel-first: name the
dependency behind every order a mock keeps. Do not edit repository files outside
your output directory, do not commit, do not compile or build anything (CI-only
project; source reading and `gh api` reads are fine).

Final message: a summary (English) of your capabilities, the problems/workloads each
covers, the three worst frictions, and what you would test first on hardware.
