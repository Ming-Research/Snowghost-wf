# Architecture of an end-to-end incremental, concurrent renderer

Branch of the shared exploration (`context.md`): what unit flows from the
document to the screen, what CSS truly couples versus what the current
representation couples, which execution model carries updates across stage
boundaries, how the current full-recompute code evolves, and which
invariants make "a local change stays local" true.

Every node carries a status (**established** / **promising** /
**uncertain** / **hard** / **likely dead end**), reasoning, evidence, costs,
what it needs from Whitefoot, and the experiment that would settle it, with
its criterion written before the measurement. "Measured" means a number in
`research/investigations/*/DESIGN.md` at the revision it names; "named
system" means established practice with a citation; "from memory" is my
recollection without a fetched source; everything else is speculation and
says so.

Grounding read for this branch: `design/pipeline.md`, `design/processes.md`,
`design/vocabulary.md`, `design/pipeline/style.md`, `design/pipeline/layout.md`
(all nodes, with `design/log.md`), `research/investigations/layout/DESIGN.md`
(Q51–Q63, results), `research/investigations/style/DESIGN.md` (three parts,
results), `research/investigations/concurrency/DESIGN.md` (layout
measurement, floats, shape D, the open question on the unit of
invalidation), `research/investigations/architecture/DESIGN.md`,
`renderer/layout/module.wfm`, `renderer/style/module.wfm`, and Whitefoot
`spec/kernel-spec.md` §9 (effects), §13 (PAR-1, PAR-2, WAIT-2/3, SHARE-1..3)
and [RANGE-5] (`apart` certificates).

---

## 0. Where the code stands, read for incrementality

Facts I rely on below (all measured or read from the sources named):

- **Style** is three parts over arrays indexed by *preorder position*
  (`Traversal.elements`, `Cascade.winners` 55 × n, `Inherited.*`,
  `Resets.*`, `Styles.elements`), then interning into append-only tables
  whose identifiers are the computed style (`ComputedStyle` = 12 `u32`
  group ids). At four workers: matching 0.30 s, document-order pass 0.164 s,
  third part 0.08 s, interning 0.088 s on ecma262 (179,471 elements);
  sequential 1.5 s (style/DESIGN.md, criterion 2).
- **Layout** is an owned tree `Context { children: Box<Slots<Context>>, … }`;
  each context writes its boxes, lines and `Fragment`s relative to its own
  border box (Q55) and stores the `Space` it was given and `intrinsic_known`
  (module.wfm). Text preparation (itemize, shape, break opportunities) is a
  counted loop per paragraph and is 60–67 % of the sequential stage; the
  layout passes are 0.14–0.18 s at four workers on the two large pages
  (layout/DESIGN.md, criterion 2). In the prototype, stacking the block
  pass was 0.2 % of layout's instructions (concurrency/DESIGN.md, floats).
- One block formatting context holds 85–95 % of each real page's text
  (ecma262: 27,979 paragraphs in one context; html5: 20,919), so "the
  context" is not a useful grain of *work*, which the pipeline tree already
  records; whether it is the unit of *storage, invalidation and caching* is
  the recorded open question (concurrency/DESIGN.md).
- The box tree is one global walk in tree order that also resolves counters
  and quotes (Q63) and records each paragraph's pieces as byte spans into
  the document's text arena and into `generated_text`, which is rebuilt per
  style run.
- `Fragment.owner` is an element's *preorder index* for `placed_element` and
  a text node's *`NodeId`* for `placed_text`: one identity survives an
  unrelated insertion, the other does not.
- Whitefoot: an iteration may write `slots[a*i+b]` (PAR-2 affine element), a
  proved range `&r[s*i+b..]`, or an element an `apart` certificate places
  (RANGE-5, Whitefoot #203; proved in about 1 s for the owner loop,
  re-derived each run in `level_index`). A spawn takes value parameters only
  (WAIT-3); an atomic statement on a `Shared<T>` is a waiting call, so no
  PAR-1/PAR-2 overlap contains one. An effect path can name `x`, `x.f`,
  `x[i]`, `x[lo..hi]`, never "the nodes reachable from this id".
- Paint, display lists, the scene and the shell do not exist; the processes
  tree fixes the boundary as data (display lists, layer trees) in shared
  memory.

---

## 1. Units and identity

### 1.1 The unit is not one thing: each stage has its own memo unit, and the identities map (status: promising)

**Claim.** Nothing flows "end to end" unchanged. The quantity that flows is
a *change*, and each stage has a natural unit at which a change is absorbed
or passed on:

| Stage | Memo / rerun unit | Why that unit | Maps to the next stage as |
|---|---|---|---|
| Document | node (`NodeId`) | script and the parser address nodes | a styled node (element, or `::before`/`::after` box) |
| Style | styled node, with the *restyle root* (a subtree) as the rerun extent | inputs are own winners + parent's inherited ids (true chain parent→child) | zero or one context root, a `Block`, inline `Mark`s inside a paragraph, or a generated box |
| Box tree | formatting context (rebuild of one context's `flow`/`pieces`) | anonymous boxes and block-in-inline splits are decided per context; a `display` change on an inline reshapes its context's flow | paragraphs, blocks, child contexts |
| Text preparation | paragraph | depends on its own pieces and run styles alone (Q53); the heaviest work (60–67 %) | lines |
| Layout | context (size, position of children) and paragraph (lines) | a context's inside depends on its `Space` alone (Q55); a paragraph's fill on its width, exclusions and atomics | fragments relative to the context |
| Paint | display chunk per context, with paint phases | coordinates relative to the context; order fixed within a stacking context | chunk references in a scene tree |
| Scene / compositing (shell) | chunk, spatial node | the shell retains chunks; damage = union of changed chunks' bounds | pixels |

The relations are one-to-many downward (element → fragments; context →
chunks when multicol splits a box per column) and the identities are
*derived*, never shared: a fragment is addressed as (context identity,
ordinal), a line as (paragraph identity, ordinal), a chunk as (context
identity, phase). Only the context and the styled node need an identity that
survives unrelated edits; everything below them is re-derived with its
owner and need not be stable.

**Evidence.** Blink's LayoutNG keys its cached layout result on the box by
the constraint space that produced it, and its fragments are immutable with
offsets from the parent fragment
([LayoutNG README](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/blink/renderer/core/layout/layout_ng.md),
[RenderingNG deep dive](https://developer.chrome.com/docs/chromium/layoutng));
Q55 and the stored `Context.space` are that design. Flutter's relayout
boundary is the same cutoff stated as a rule on the child–parent protocol
([RenderObject.layout](https://api.flutter.dev/flutter/rendering/RenderObject/layout.html)).
Blink's subsequence cache reuses the display items of an unchanged paint
layer ([core/paint README](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/third_party/blink/renderer/core/paint/README.md)).

**Costs.** Each unit must store its key (§1.3) and a dirty flag; the mapping
element → context needs an index (§1.2).

**Whitefoot.** Nothing new for the layout tree: recursion over
`children[i]` in a counted loop is a PAR-2 affine element, so a per-child
update is provably disjoint without facts. The style unit is where the
proof model bites (§1.2, option B).

**Experiment that settles whether these are the right units (E5 below):
run the current full pipeline twice with a scripted mutation in between
and diff.** It needs no incremental code and measures CSS's own locality on
the three pages per mutation class: how many styled nodes' ids change, how
many contexts' fragments change, how many paragraphs' lines change.
Criterion: if for a text edit inside one paragraph of the dominant context
fewer than 1 % of paragraphs change their lines and fewer than 1 % of
contexts their fragments, the paragraph+context pair is the right layout
unit; if a class toggle on a mid-page element changes the ids of more than
10 % of its descendants on average, the style cutoff (§2.1) needs the
finer custom-property dependency record.

### 1.2 Keeping identities stable across updates

Three ways to make "the same unit" findable after an edit; they differ in
where the cost of stability is paid.

**A. Preorder-contiguous arrays, renumbered on structural change**
(status: established for full passes, uncertain as an incremental store).
What style does today. A subtree is a contiguous range `[lo, hi)`, which is
the one representation in which a Whitefoot effect row can say "this call
reads only this subtree" (`reads(styles[lo..hi])`, EFF-1 `erange`) and a
proved range reference partitions parallel work over subtrees for free.
Insertion or removal shifts every later index: every per-element array must
be moved (ecma262: 12 group ids + 55 winners per element ≈ 270 bytes × 180 k
≈ 48 MB to move in the worst position; a memmove of that size is on the
order of 5–10 ms on this class of host — an estimate, not measured), and
every consumer that stored an index (`Fragment.owner`, `StyleRef.element`,
`PseudoStyle.element`) is invalidated. **Likely dead end as the primary
store** for a document script mutates; fine for a static page. Rescue
variants: order-maintenance labels (Dietz–Sleator, from memory) give O(1)
amortized order comparison with stable ids and local relabeling, and
Whitefoot's `Segments<T>` is a natural chunked store (insert splits a
segment, indices inside a segment stay contiguous) — but a segment index
read from storage reintroduces the scatter proof (B).

**B. Stable arena ids (`NodeId` + generation) for every per-node result**
(status: promising for style, established as a DOM shape). Style results
live at the node's slot (in the DOM arena or a parallel `Box<Slots<…>>`
indexed by `NodeId`); the spec itself says a stale index "names the current
occupant" and a program "keeps a generation number as data" (§7, OP-4
commentary). Routing a mutation to its unit is O(1). The cost moves to the
proofs: "for each `k` in the dirty list, write `results[dirty[k]]`" is a
write through an index read from storage, denied by PAR-2 unless an `apart`
certificate places it (RANGE-5), which needs a fact that the dirty list is
duplicate-free, derived where the list is built (as `level_index` derives
`listed`). Whitefoot #203/#204 made that provable in about 1 s for the owner
loop; `docs/todo.md` records that every pass re-derives its facts
(measured cost of `level_index` is inside `cascade-d`'s 0.034 s on ecma262
at four workers, not separated). **Needs from Whitefoot:** range facts kept
with the structure that owns the list, so the dirty list's distinctness is
stated once at insertion (a `Slots` with an invariant "no two equal
entries") and not re-derived per loop; the ordered-result-list loop binding
(todo); contract-only parameters erased.

**C. Content keys (hash of inputs) with no identity at all** (status:
uncertain). The build-system view ("constructive traces", Mokhov et al.
*Build systems à la carte*, from memory): a unit is found in a table by the
hash of its inputs, so insertion needs no renumbering and a moved subtree is
a cache hit. Costs: hashing every input per frame is a full pass over the
inputs (defeats the purpose unless hashes are maintained incrementally
bottom-up, which is again a dirty-flag walk), collisions need a full-key
compare, and the table is a shared store written by every unit (the same
ordering problem Q47 refused for a `var()` cache). Useful for one thing:
*move detection* (a subtree reparented by script or by the adoption agency
keeps its results), which A and B lose. Keep as a secondary mechanism for
moves, not the primary identity.

**Recommended combination.** Style: B (per-`NodeId` slots, with the
document-order sequence kept as a separate derived list per restyle root).
Layout: the owned tree, where identity is the path (parent slot, child
index) and the element → context map is a per-node `u32` box address
refreshed when a context is rebuilt (local, since a rebuild rewrites the
addresses of exactly the nodes in that context). Paint: chunk identity =
context identity.

### 1.3 What a unit's key must contain (status: established principle; the list is this codebase's)

A stored result is reusable only if every input is in its key or is
guaranteed unchanged by a version stamp in the key. From the current
`Context`, `Paragraph` and `Styles` shapes:

- styled node: own winners (55 ids + custom keys), parent's inherited group
  ids, `Positions` entry (for `:nth-*`), environment version (viewport,
  fonts loaded, `rem`); explicit `inherit` and blockification read the
  parent's *winners*, so the parent's winners are in the key too;
- context: `Space` (already stored), style ids of the establishing element,
  the keys of its children, the text keys of its paragraphs, the exclusion
  list reaching it from outside (none for a BFC root: that is what makes it a
  unit), the counter and quote state at its entry (§2.8), its column-map
  inputs;
- paragraph: its pieces (node ids + spans, generated text by *content*, not
  by span into a rebuilt buffer), run styles, available width, exclusions
  intersecting it, atomic inlines' sizes, font set version;
- chunk: the context's fragments and the style ids they paint with.

**Whitefoot's "complete key" decision holds only for owned or contiguous
inputs.** The pipeline tree's third decision (a pure function memoized by its
inputs, key completeness proved by the compiler) is true for a function
`lay_out_context(ctx: &Context, space: Space, …) reads(ctx)` — the effect
row *is* the key — and for `inherited_pass_range(&styles[lo..hi])`. It is
not true for a function that takes `document: &Document` and follows links
from a `NodeId`: its row says `reads(document)`, i.e. the key is the whole
document. For the DOM arena (needed by script and tree construction,
`design/vocabulary.md`), style memoization is therefore by *explicit
invalidation* — dirty flags from mutations plus selector invalidation sets
(§2.9) — not by a proved key. This is a limit of the decision's reach, not
a defect of the stage, and should be recorded when the tree is revised.

---

## 2. Couplings: what CSS truly ties together, and what the representation ties

For each true coupling: direction and extent; the representation that
confines it; what remains. Representational couplings follow in §2.12.

### 2.1 Inheritance and custom properties (true; parent → child chain) — confinement status: established (interned ids, Stylo/Blink cutoffs); the per-name custom record is uncertain
Extent: the subtree. Confinement: interned group ids make the cutoff a
comparison of a few `u32`: a child whose own winners did not change and
whose parent's inherited ids (font, text, visibility, table, custom set)
are unchanged has an unchanged style, and its subtree stops. **Threat:**
the custom-property *set* is one id; adding `--x` on `html` changes every
descendant's `custom` id and so every `ComputedStyle`, although only the
elements that substitute `var(--x)` compute anything different. Confining
that needs a per-element record of the names it substituted (a dynamic
dependency, written into the element's own slot, so PAR-2 admits it) and a
cutoff "set changed but none of my names changed". Second threat: `em`,
`ex`, `lh` chains (a font-size change invalidates lengths down the subtree
until a descendant sets an absolute size — unavoidable, bounded by the
subtree). `rem`, `vw/vh` and `@media` are global by definition: a viewport
resize restyles every element that uses them (Stylo keeps a
viewport-dependent flag per element, from memory); keep a per-element bit
"uses viewport units" so a resize touches only those.

### 2.2 Selector couplings: descendant, sibling, `:nth-*`, `:has()` (true; across the tree) — confinement status: established (Blink invalidation sets)
A class change on `e` can change the matched rules of `e`, its descendants
(descendant/child combinators with `e`'s compound on the left), its later
siblings (`+`, `~`) and, with `:has()`, its ancestors. Confinement: compute
from the sheet, once, which compounds appear left of a combinator and with
which combinator — Blink's descendant and sibling invalidation sets
([style-invalidation.md](https://chromium.googlesource.com/chromium/src/+/master/third_party/blink/renderer/core/css/style-invalidation.md),
with `:has()` handling described by
[Igalia](https://blogs.igalia.com/blee/posts/2023/05/31/how-blink-invalidates-styles-when-has-in-use.html));
the existing rule index keyed by rightmost compound is the matching half of
the same idea. `:nth-child` reads the sibling-position table, built today by
one global walk; incrementally it is a per-parent recount, which
`design/pipeline/style.md` already reopens. What remains: a rule such as
`body.dark *` is a true whole-page coupling and must rerun the page; the
invalidation set tells us so without walking it.

### 2.3 Margin collapsing (true; along one BFC's flow, including through empty blocks and into a child's first/last margins) — confinement status: established (LayoutNG margin strut); translation variant uncertain
Extent: the flow of one block formatting context; stops at a BFC root. The
block pass is the only chain and the prototype measured it at 0.2 % of
layout's instructions (stacking, flat page). Confinement by representation:
positions relative to the context (done) so re-stacking rewrites `Block.y`
and `Paragraph.top` inside one context and nothing inside its children;
LayoutNG passes the pending margins as a "margin strut" in the constraint
space, so a child BFC's result can be cached under the same key regardless
of what collapsed above it (from memory of the LayoutNG design). A cheaper
rerun than re-stacking the whole dominant context (20–28 k entries) is to
*translate* everything after the changed block by the delta while no
collapse rule changes; whether that is worth its bookkeeping depends on the
measured cost of the plain re-stack (E4). Deferring even the in-context `y`
to the paint walk as a prefix sum is possible but margin collapsing, `clear`
and floats make the "sum" a small state machine; I would not do it before
E4 shows the re-stack is costly.

### 2.4 Floats and `clear` (true; one BFC, forward in flow, and into non-BFC descendants) — confinement status: promising (measured speculation; incremental re-fill unmeasured)
A float's position depends on the flow height before it, and it narrows the
lines of every later paragraph whose vertical range it meets, including
paragraphs inside nested blocks that are not BFC roots. The decided
speculation (break every paragraph at full width, re-break the ones a float
narrows) measured 0 of 32,684 paragraphs re-broken on html5 and 4 of 770 on
apollo11. Incrementally the same structure holds: a context stores its
`Exclusion`s; after a change, the paragraphs whose stored `least_top`/width
inputs differ from the new exclusions are re-filled. What remains:
`shape-outside` and floats that push each other extend the exclusion
geometry but not the dependency shape.

### 2.5 Line breaking and inline layout (true; inside one paragraph; upward from atomic inlines) — confinement status: established (paragraph-local)
A paragraph's lines depend on its text, run styles, width, exclusions and
the sizes of its atomic inlines (child contexts: images, inline-blocks),
which is a *child → parent* edge inside layout. Confinement: paragraph key
(§1.3); atomics' sizes are values (width, height, baseline) crossing one
boundary. Threats: `::first-line` and `::first-letter` make style depend on
the break result (style ← layout, paragraph-local, needs an iterate-once
path); `text-wrap: balance/pretty` and hyphenation stay paragraph-local but
re-break the whole paragraph; bidi reordering is per line.

### 2.6 Intrinsic sizes up, available sizes down (true; the parent–child protocol) — confinement status: established (LayoutNG constraint space, Flutter relayout boundary)
Down: `Space` (available width, percentage bases, forced sizes, shrink) —
already a value, already stored, so equality of `Space` is the cutoff
LayoutNG uses and Flutter states as "tight constraints" (relayout
boundary). Up: min/max-content, size, baseline — values. What remains is
the *extent* of upward propagation: a change inside a context whose parent
read its intrinsic sizes (flex, grid, table cell, float, shrink-to-fit,
multicol balancing) propagates until an ancestor whose sizes come out equal
or whose parent did not read them (`intrinsic_known` already records
whether a parent asked). Threats: tables (every cell couples to its column
and the table is the unit), flex/grid with `auto` tracks and baseline
alignment (every item), percentage heights with an indefinite basis
(`basis_height = -1` then resolved later), `aspect-ratio`, form controls.
Flutter's rule, that a child whose parent ignores its size is a boundary,
is the invariant to state (§5, I4).

### 2.7 Percentages and `calc()` (true, but already deferred) — confinement status: established (Q49)
Resolved in layout against the `Space` basis (Q49): confined by the same
key as 2.6. Nothing else to do.

### 2.8 Counters and quotes (true; a chain in document order across contexts) — confinement status: promising (checkpointing is speculation here)
`counter-increment` on one element shifts the value every later reader in
scope sees; readers are generated content (pieces of paragraphs), so a
change re-prepares those paragraphs. Pages: 4–10 `counter()` uses per
sheet, 124 rendered references on apollo11. Q63 resolves counters in the
global box-tree walk, which is a chain across every context. Confinement:
checkpoint the walk's carried state (counter stacks, quote depth, and
anything else the walk carries: sibling counts, pending margins if any) at
each context's entry and store the state at its exit; a local rebuild of a
context restarts from its stored entry state, and later contexts are
re-walked only while an exit state differs from the stored one (cutoff when
a renumbering ends at an element that `counter-reset`s). This keeps Q63 and
makes the global walk re-enterable per context. Threat: a counter read in
every list item (`li::marker` with `counter(list-item)` as text) makes a
single insertion re-prepare every later item in that list — bounded by the
list, and inherent.

### 2.9 Stacking order (true; across contexts, within a stacking context) — confinement status: established (Blink paint chunks, WebRender stacking contexts)
CSS 2.2 Appendix E orders a stacking context's painting by phase
(background, negative z-index children, in-flow block backgrounds, floats,
inline content, z=0 positioned, positive z-index), interleaving descendants
from many formatting contexts. One context's drawing therefore cannot be
one contiguous run of the final order. Confinement: a chunk per context
holds its drawing *split by phase*; the stacking context's node in the scene
holds an *order list of (chunk, phase) references*; a `z-index`/`position`
change rewrites one order list, not the chunks. Blink's paint chunks and
subsequence cache, and WebRender's stacking contexts over a spatial tree,
are the same separation of content from order and position
([core/paint README](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/third_party/blink/renderer/core/paint/README.md),
[WebRender clipping and positioning](https://fossies.org/linux/firefox/gfx/wr/webrender/doc/CLIPPING_AND_POSITIONING.md)).

### 2.10 Containing blocks for absolute and fixed positioning (true; a distant ancestor) — confinement status: promising
An absolutely positioned box is sized against its containing block (nearest
positioned ancestor; transforms also establish one) and, with `auto`
insets, placed at its static position, which lies inside some other
context's flow (`Flow::Out`). Confinement: own the out-of-flow context under
its containing block's context; resolve its static position in the walk
that computes absolute positions anyway (the paint/placement walk, Q55), so
a change in the anchor's flow moves the box without re-laying it out.
apollo11 has two such boxes whose static position lies inside a line (a
known mismatch); the placement walk has the line positions, so this also
fixes that case. Fixed positioning and `sticky` are scene properties
(spatial nodes), not layout couplings, once the chunk is relative.

### 2.11 Multi-column (true; the whole container) — confinement status: established as a bound; cutoff unmeasured
Balancing reads the one-column content height, so any change inside a
multicol container re-balances it; the column map is a post-pass over
units no break may cross (Q59). Extent: the container (20.7 % of html5's
block boxes lie in two such tables). Confinement: the container is a
context; cutoff when its one-column content height is unchanged;
`column-span: all` (out of scope) would split the container into pieces,
each balanced alone.

### 2.12 Representational couplings in the current code (status: identified; each has a cheap replacement)

| Field or pass | Coupling it creates | Replacement |
|---|---|---|
| `Traversal`, `Styles.elements`, `Inherited.*`, `Resets.*`, `Cascade.winners`, `custom_keys` by preorder index | every structural edit renumbers every element's results | per-`NodeId` slots (§1.2 B); a document-order list per restyle root, derived locally |
| `Fragment.owner` = preorder index for elements, `NodeId` for text | the layout output's identity for elements changes on unrelated insertions | `NodeId` (+ generation) for both; the oracle driver maps to preorder for dumps |
| `Positions` built by one global walk | `:nth-*` of every element depends on a whole-document pass | per-parent sibling counts, recounted for the parent of a mutation |
| `build_boxes` as one global walk carrying counters | a context cannot be rebuilt alone | per-context rebuild from checkpointed walk state (§2.8) |
| `generated_text` rebuilt per style run; pieces as spans into it | paragraph keys change although content did not | per-pseudo stable storage or content hash in the piece key |
| interning tables append-only across runs | ids stable (good), memory grows per frame | keep; add reclamation only when measured (a generation sweep when a table exceeds a bound) |
| `place_boxes` → one flat array of absolute rectangles | the only consumer walks the whole tree and produces absolute coordinates | an oracle-only path; paint emits per-context chunks (§3.6) |
| `Layout.paragraphs/contexts` counts, `Context.space`, `intrinsic_known`, owned `children` | none; these are the right shape | keep |
| text arena per document, pieces as byte spans | none if edits append (old bytes become garbage) | keep; reclaim with the document's own policy |

---

## 3. Execution models

Common vocabulary: a *frame* = one batch of document mutations made visible;
*latency to first pixel* = the critical path from the last mutation to the
shell receiving the changed chunks for a single local edit (text inside one
paragraph of the dominant context, no style change); *worst case* = a
change on `html` that alters every element's style (font-size, a custom
property every rule reads).

### 3.a Per-subtree fused pipeline (status: promising; the natural fit for Whitefoot's proofs)

**Shape.** One recursive update over the owned layout tree:
`update_context(ctx, space, dirty)` → if nothing in `ctx` is dirty and
`space == ctx.space`, return the stored size; else restyle the context's
dirty styled nodes (inherited pass over the restyle roots inside it, parallel
loops for match and resets), rebuild its flow if a `display`/box-generating
change occurred, re-prepare dirty paragraphs (counted loop), re-stack, recurse
into children in a counted loop, and re-paint its chunk into the context's
own chunk slot. Style → layout → paint for one unit are three statements
with a true dependency; two sibling subtrees are two iterations of a counted
loop over `children[i]`.

**Concurrency across stages.** Emergent: while child 1 is painting, child 2
may be restyling, because PAR-2 proves the iterations disjoint and PAR-1
overlaps independent statements within an iteration. No stage barrier
exists between style, layout and paint. This is what "DOM → style → layout
→ paint concurrently across stage boundaries" means in this language
without spawning contexts. **One barrier remains: shipping.** If writing a
chunk into the shell's shared memory is a waiting host call (W8 is not
designed yet, so this is open), it cannot sit inside the recursion: PAR-1
denies overlap to a statement containing a waiting call and PAR-2 to a loop
whose body contains one. So chunks are per-iteration outputs in their
context's slot, and the changed chunks are shipped after the recursion
returns — one batch per frame — or moved into a spawned shell-facing context
that waits on the shell while the next frame's update begins. Shipping is
therefore batched at frame end, which bounds the latency gain of (a) over
(c) to the style/layout/paint overlap across siblings, not to streaming
chunks to the screen mid-update. If W8's write turns out not to wait (a
plain write into shared memory with a later signal), the send can stay in
the iteration and streaming returns.

**Scheduling.** The compiler's and runtime's (pipeline tree, second
decision): work splits at the counted loops and the recursion; the critical
path is the chain root → dirty context → its block pass → chunk. There is
no scheduler to write.

**Latency to first pixel (estimate, not measured).** For a text edit in one
paragraph: restyle nothing; re-prepare one paragraph (one paragraph of
average size is roughly 0.78 s / 28 k ≈ 30 µs sequential on ecma262); re-fill
its lines; re-stack the dominant context (0.2 % of prototype layout → likely
sub-millisecond, E4); re-emit one chunk; translate later chunks in the scene
(shell). Plus the walk from the root to the dirty context (depth × a
comparison). Order of a millisecond total, dominated by the re-stack and
the shell round trip if the chunk is large.

**Worst case.** Everything is dirty: the same work as today's full pipeline
at its measured parallel speed (style 0.63 s + layout 0.59 s at four workers
on ecma262), plus one key comparison per unit. No regression over today
beyond the comparisons.

**Bookkeeping.** A dirty flag per styled node and per context, propagated
to the root at mutation time (O(depth) per mutation, Flutter/Blink practice);
stored keys (§1.3); the element → context address. Nothing dynamic.

**Expression in Whitefoot.** Recursion over `children[i]` (affine element,
PAR-2) — already how `lay_out` runs; counted loops over paragraphs writing
their own slots; `writes(ctx)` rows per context. The restyle inside a
context writes per-`NodeId` style slots — the one place needing a certified
scatter (§1.2 B) or, alternatively, the context's styled nodes listed as a
range of a per-context document-order list owned by the context (then the
write is to the context's own storage and needs no certificate, at the cost
of a copy of ids). Style's parent→child chain crosses context boundaries
(an inline child context's root inherits from an element inside the parent's
paragraph), so the restyle of a context's root is an input value (its
parent's inherited ids), exactly like `Space`.

**What it needs from Whitefoot.** Nothing beyond main at the pin for the
layout tree. For style scatter: the range-fact items in `docs/todo.md`.
For *script concurrency* (script mutating the next frame while this runs):
W4 (§3.e2).

**Experiment (E1 + E3).** Build the dirty-flag/`Space`-cutoff update on the
current layout stage, with per-paragraph reuse, and time four edit classes
on html5 and ecma262. Criteria: a one-paragraph text edit costs < 1 ms at
four workers and < 1/100 of the full stage; a mid-page class toggle that
changes one block's height costs < 5 ms; the `html` font-size change costs
≤ 1.2 × the full stage. E3 compares it with model (c) on a scattered-edit
workload (100 table cells changed): (a) earns its structure if it is > 20 %
faster; otherwise (c)'s simpler driver wins and (a) is a later step.

### 3.b Dataflow graph of keyed nodes with change propagation (status: established in compilers and editors; hard here, in the general form)

**Shape.** Every unit is a node keyed by identity; each computation records
the nodes it read; a change marks dependents; propagation reruns nodes in
dependency order with early cutoff when a node's new value equals its old
(Salsa's red-green algorithm and backdating,
[salsa reference](https://salsa-rs.github.io/salsa/reference/algorithm.html);
Acar's self-adjusting computation,
[experimental analysis](https://www.researchgate.net/publication/220404776_An_Experimental_Analysis_of_Self-Adjusting_Computation)).

**Concurrency across stages.** Natural: nodes of different stages run
whenever their inputs are ready; a wave of ready nodes is a parallel loop.
**Scheduling.** Topological by recorded edges; needs a worklist and a
height or revision per node. **Latency.** Optimal in the number of nodes
recomputed (the affected set), plus verification walks: Salsa's
"deep verify" visits dependencies of a node to decide whether it is still
green, a cost proportional to the dependency closure touched, not the
change. **Worst case.** Full recompute at a constant-factor overhead: the
self-adjusting literature reports 2–30× for building the dependence graph
(constant factors from the cited analysis; GC-heavy), Salsa's overhead is
smaller because edges are per query not per instruction (from memory, not
measured here). **Bookkeeping.** Edge lists per node (writable into the
node's own slot, so PAR-2 admits them), revisions, a worklist with
distinctness.

**Why the general form is hard in Whitefoot.** (1) Dynamic edges are data:
a wave "for k in dirty: recompute node[k]" is the certified scatter, and
every stage's loop needs a certificate with a distinctness fact; (2) a
worklist is written by many iterations (append from parallel iterations is
not a PAR-2 accumulator); it must be built per wave as per-iteration output
lists then concatenated — fine, but it is the kind of bookkeeping the owner
calls "manual"; (3) the key-completeness argument is lost once reads are
recorded dynamically rather than stated in rows.

**The useful specialization: the edges are the tree.** In CSS the dependency
structure is almost entirely static per stage: style(e) ← style(parent(e)),
own winners; layout(ctx) ← Space, styles in ctx, children; chunk(ctx) ←
layout(ctx). Only the couplings of §2.2, §2.6-up, §2.8 and §2.10 are
"long" edges, and each has a static over-approximation (invalidation sets,
`intrinsic_known`, counter checkpoints, containing-block ownership). A
dataflow with static tree edges and a handful of dynamic ones is model (a)
with recorded reads for the long edges, which is where I would land, not at
a general graph.

**Experiment.** Not first. If E5 shows affected sets that (a)'s static
cutoffs over-approximate badly (e.g. root custom-property changes where < 5 %
of elements substitute the name but all are rerun), add the per-element
"names substituted" record (one dynamic edge kind) and measure the gain;
criterion: the rerun set shrinks to within 2× of the true affected set.

### 3.c Staged full passes over a dirty frontier (status: established — this is Blink's lifecycle; the baseline to beat)

**Shape.** Per frame: style recalc over dirty subtrees; layout over
`needs-layout` boxes up to relayout boundaries; pre-paint/property update;
paint invalidation; composite. Each stage walks from the root to its dirty
frontier and the stages run in order. **Concurrency.** Within a stage only
(Stylo parallel restyle); stage barriers between. **Latency.** Each stage
pays its root-to-frontier walk and its barrier, even when one paragraph
changed; on a large tree this fixed cost is real (Blink's lifecycle update
on a big page is hundreds of microseconds with nothing dirty — from memory,
not measured here). **Worst case.** Same as (a). **Bookkeeping.** Dirty bits
per stage, the same stored keys. **Whitefoot.** The simplest: today's four
functions with a `dirty` parameter and range-restricted loops; no cross-stage
overlap needed, so no scatter proofs beyond style's.

**Role.** Build it as the *control* for E3; it is what (a) must beat, and it
is also (a) with barriers inserted, so the two share every unit, key and
invariant. The owner's critique of Chrome is not that it has stages but that
each stage's incrementality is hand-tuned and the stages cannot overlap; (c)
keeps the first defect out (keys are values, cutoffs are equality) and
keeps the second in. The difference is measurable.

### 3.d Demand-driven: pull from the frame (status: uncertain; strong for paint and for huge documents, weak for layout)

**Shape.** The frame asks: which chunks intersect the viewport? For each,
is its context's layout valid? If not, lay it out, which asks its parent for
`Space`, which asks the styles. Nothing offscreen is computed unless
something visible depends on it.

**Where it works.** Paint and chunk emission: never paint what the viewport
does not show (every engine culls). `content-visibility: auto` is this model
shipped for layout, by letting the author declare that offscreen subtrees
contribute only an estimated size
([web.dev](https://web.dev/articles/content-visibility)). **Where it fails
by itself.** The position of the visible content depends on the heights of
everything above it in the dominant BFC, and the document's scroll height
on everything; heights come from line breaking, the heaviest work. Pull
therefore cannot skip the text preparation of the content above the fold
without an estimate. **With speculation it becomes interesting:** lay out
the viewport's contexts first with estimated heights for what precedes
them (an average line height × an estimated line count from text length and
width), show the first pixel, then lay out the rest and correct; the pipeline
tree already admits speculative work with fix-up. This is how virtualized
lists behave (RecyclerView, UITableView, from memory) and nobody does it for
plain CSS content because of the jump when estimates are corrected.

**Latency.** First pixel for a *load* of ecma262 could drop from the full
stage to the viewport's share (the viewport shows about 0.1 % of 180 k
elements); for a local edit it is no better than (a). **Worst case.**
Estimation error forces a second layout of everything laid out so far.
**Bookkeeping.** Estimates and their correction; scroll anchoring.
**Whitefoot.** Pull is recursion with results, which is fine; the
speculation is two adjacent statements (estimate-based layout of the
viewport contexts, full layout of the rest) with disjoint writes, then a
comparison.

**Experiment (E7).** On ecma262, lay out only the contexts whose estimated
vertical range intersects the viewport, with the rest estimated, and
measure time to the first complete viewport against the full stage; and
measure the estimate's error (how far the first viewport's content moves
after full layout). Criteria: first viewport in < 1/10 of the full stage;
content shift < 1 line in 90 % of viewports sampled along the page.
Not first: it needs paint and the shell, and it serves loading, not editing.

### 3.e Others

**3.e1 Attribute-grammar scheduling (status: established theory; a design
tool, not a runtime).** CSS layout has been written as an attribute grammar
with inherited (down) and synthesized (up) attributes and a parallel
schedule derived from the grammar (Meyerovich and Bodík,
[Fast and parallel webpage layout](https://archives.iw3c2.org/www2010/_lmeyerov/projects/pbrowser/pubfiles/playout.pdf)),
and incremental attribute evaluation re-evaluates exactly the affected
attributes after a subtree replacement (Demers, Reps, Teitelbaum,
[POPL '81](https://www.semanticscholar.org/paper/Incremental-evaluation-for-attribute-grammars-with-Demers-Reps/105e17f5a7404597c8182371822e5494945dae01);
a recent layout-specific treatment is
[Spineless Traversal for Layout Invalidation](https://arxiv.org/html/2411.10659v5)).
The value for this project is the *discipline*: write each stage's
parent→child and child→parent values explicitly (`Space` down, size and
intrinsic sizes up, inherited ids down, counter state along) and refuse any
other cross-unit read. Then (a)'s cutoffs are exactly the attribute
grammar's affected set, and the "long" couplings of §2 are the places the
grammar would need non-local attributes, which is where to keep an explicit
record. **Whitefoot:** the effect rows are the attribute declarations; a
function whose row names only its unit and the crossing values is the proof
that the discipline held. No experiment needed; adopt as the rule for
writing (a).

**3.e2 Frame pipelining with snapshots (status: hard; needs W4).** Script
mutates frame N+1 while the renderer works on frame N (Blink's compositor
commit; React Fiber's double buffer). In Whitefoot a renderer context must
*own* what it reads (WAIT-3: value parameters), so the document would have
to be moved to the renderer, which stops script, or copied, which is a full
pass, or made persistent (copy-on-write arena with versioned slots, where
script's writes allocate new slots and old versions stay readable). The
persistent arena is the only variant that keeps both the identity stability
script needs and a read-only snapshot without copying; it is speculation
here and interacts with reclamation. **Alternative that avoids it:** do not
pipeline; a frame is: script runs (owns the document) → mutations marked →
one update pass (owns everything) → chunks sent; the shell pipelines
compositing and scrolling, which is where frame rate is actually won
(compositor-only animations, processes tree). Latency of a local edit is
then (a)'s; throughput of script-heavy pages loses the overlap of script
with rendering. **Experiment:** none until script exists; record W4 as the
blocker.

**3.e3 Optimistic cross-stage speculation (status: promising; cheap in
Whitefoot).** For a mutation that *might* change style (a class toggle),
start the layout work that is likely unaffected (re-prepare the paragraph
whose text changed, using the old style ids) as a statement adjacent to the
restyle, with disjoint writes; when the restyle finishes, compare the new
ids with the ones the speculation used and redo the paragraph only on a
mismatch. The pipeline tree already blesses speculation that shortens the
critical path. It shortens the chain restyle → text preparation to
max(restyle, prep) for the common case. Measure with E1's class-toggle edit:
criterion, latency falls by at least the smaller of the two parts.

**3.e4 The shell's side: damage instead of tiles (status: uncertain; a
tradeoff to measure, not a hack to remove).** The owner calls layering and
tiling hacks. With a retained scene of chunks in relative coordinates, the
shell can rasterize only the union of changed chunks' old and new bounds
(damage rectangles) into a persistent surface. WebRender's picture caching
is tiles because GPU rasterization of unchanged content per frame was its
cost, and tiles amortize it under scrolling
([WebRender picture caching](https://mozillagfx.wordpress.com/2018/11/02/webrender-picture-caching/)).
Whether damage rectangles alone suffice depends on scroll behaviour (a
scroll moves everything: with a persistent surface larger than the viewport
it is a blit; with tiles it is a reuse) and on raster cost (CPU vs GPU). This
is the shell's decision and comes after paint exists; the renderer's
contribution is to make damage precise (chunks with bounds) so the shell can
choose either. **Experiment (E6):** with Skia, time raster of a 1-paragraph
damage rect vs a 256×256 tile vs the full viewport, CPU and GPU, on the
real pages' chunks; criterion: if damage-rect raster is < 1/5 of tile raster
for the single-edit case and scrolling stays at the display's rate with a
persistent surface, tiles are not needed in the first shell.

---

## 4. How the current code evolves

Descriptive: what is reused and what changes under each model. (Not an
argument for or against any model; AGENTS.md rules out the amount of change
as a reason.)

### Under (a) and (c) alike (they share units and keys)

- **`match_elements`** → `match_nodes(roots)` over the styled nodes of the
  restyle roots given by the invalidation sets (§2.2), writing per-`NodeId`
  slots; the rule index and `pseudo_subject_key` are reused as is; the
  presentational hints and style attributes become per-node records updated
  on attribute mutation; a new `invalidation_sets(store)` is computed once
  per `RuleStore` change.
- **`inherited_pass`** → `inherited_pass_from(root, parent_values)`: the same
  code over a document-order list of one subtree, started from the parent's
  stored inherited values; cutoff when a node's inherited ids and custom set
  id equal its stored ones and its own winners are unchanged (needs the
  interning of inherited groups to happen inside this pass, or a provisional
  id compare after interning — the current order interns last).
- **`reset_pass`** → same loop over the subtree's list.
- **`intern_styles`** → tables persist across frames; interning becomes
  "intern these changed nodes"; the eleven tasks stay independent.
- **`Positions`** → per-parent counts; `build_traversal` → per-root
  document-order lists.
- **`build_boxes`** → `build_context(element, entry_state)` with the walk's
  state checkpointed (§2.8); the `Piece` recording and anonymous-box rules
  are reused per context; `Fragment.owner` and `StyleRef.element` become
  `NodeId`s.
- **`prepare_text`** → unchanged per paragraph, called for dirty paragraphs
  only; paragraph keys added to `Paragraph`.
- **`lay_out`** → `lay_out_context` gains the `space == ctx.space && !dirty`
  cutoff and the intrinsic-size cutoff; exclusions compared per paragraph
  before re-filling; the multicol map re-run on changed content height.
- **`place_boxes`** stays as the oracle path; a new `paint_context` emits a
  chunk per context with phases; a new `scene` module describes stacking
  contexts' order lists and spatial nodes; the shell holds them.
- **New:** a mutation interface on `Document` that marks styled nodes and
  their contexts dirty and records attribute/child-list changes for the
  invalidation sets; the frame driver.

**Under (a) additionally:** the stage calls are moved inside the per-context
recursion so that a context's restyle, rebuild, text, layout and paint are
one function; the driver is `update_context(root)`.

**Under (b):** every function above also records what it read into its
unit's record, and the driver is a wave scheduler over a worklist; the
layout recursion is replaced by node-level recomputation ordered by height.
Everything in §2.12 must change first, as with (a).

**Under (d):** `lay_out_context` becomes a function that returns a size on
request and lays out lazily; the scene asks for chunks in viewport order;
estimation and correction are new. The style stage is unchanged.

### What is already right and should not move
The owned `Context` tree, relative fragments (Q55), stored `Space`, on-demand
intrinsic sizes with `intrinsic_known` (Q56), text preparation per paragraph
with no shared cache (Q53), counters in the walk (Q63, with checkpoints),
interned group ids as the computed style (the cheap equality that every
cutoff needs), percentages deferred (Q49), the document as an arena.

---

## 5. Invariants for "a local change stays local", and what threatens each

1. **Stable identity** (established). Every stored result is addressed by an identity that
   unrelated insertions, removals and moves do not change (`NodeId` +
   generation; tree path for owned contexts). *Threatened by:* preorder
   indexing (current style arrays, `Fragment.owner`); the adoption agency
   and `innerHTML` (replacing subtrees is a real change; moving one is a
   move, which only content keys (§1.2 C) can recognize).
2. **Complete, value-shaped keys with equality cutoff** (established: Salsa, LayoutNG). Every unit stores
   its inputs as values and reruns only when they differ; interned ids make
   the comparison cheap. *Threatened by:* hidden inputs (viewport, loaded
   fonts, `rem`, sibling positions, counter state, quotes depth, loaded
   image sizes) unless each is in the key or versioned; the one-id custom
   set (§2.1).
3. **Relative coordinates everywhere until the consumer** (established: LayoutNG fragments, WebRender spatial tree; decided here as Q55). Positions are
   relative to the unit; absolute positions exist in the placement walk,
   the scene and script's answers only. *Threatened by:* `getBoundingClientRect`
   and friends (answer by walking up, O(depth)); abs-pos static positions
   (resolve in the placement walk); multicol column maps (keep as maps);
   `transform`, `fixed`, `sticky` (scene properties).
4. **Thin boundaries** (established: Flutter's relayout boundary, LayoutNG constraint space). What crosses a unit boundary is a small value each
   way (`Space` and inherited ids down; size, baseline, intrinsic sizes up;
   exclusions sideways inside one BFC) and never a reference into the other
   unit's storage. *Threatened by:* margin collapsing into a child's first
   and last margins (pass a strut), floats crossing non-BFC blocks (they
   are not units — consistent with `Block` not being a context), baseline
   alignment in flex, tables and inline-blocks (a value, but one that makes
   siblings depend on each other inside the parent), `::first-line`.
5. **Re-enterable chains** (promising; speculation for counters). Every state carried along document order
   (inherited style, counters, quotes, sibling counts, exclusions, the
   block pass's running height and margin strut) is checkpointed at unit
   boundaries, so a rerun starts at the unit's entry state and stops where
   its exit state equals the stored one. *Threatened by:* counters read by
   many later elements (§2.8), `quotes` nesting, `:nth-last-*` (counts from
   the end: a later insertion changes earlier elements' positions).
6. **Outputs partitioned like the work** (promising; follows from PAR-1/PAR-2, unmeasured). Each stage writes per-unit
   storage, so stage S on unit A and stage S+1 on unit B are disjoint under
   PAR-1/PAR-2; no stage appends to one shared array during the update.
   *Threatened by:* global interning tables (intern in a short sequential
   step after the parallel loops, as today, or per-unit then merge), one
   display list (use per-context chunks), a global worklist (per-iteration
   lists concatenated).
7. **Order separated from content** (established: Blink paint chunks and property trees). Paint order lives in the stacking
   context's order list; drawing lives in chunks; the shell retains both and
   computes damage from chunk bounds. *Threatened by:* `z-index`/`position`
   changes (rewrite one list), `opacity`/`transform` groups (scene effect
   nodes), `mix-blend-mode` and `backdrop-filter` (an effect that reads what
   is below it couples chunks in the shell — bounded to the group).
8. **Invalidation extents known from the sheet, not the walk** (established: Blink invalidation sets). Which
   elements a DOM mutation can restyle is computed from the selectors once
   (invalidation sets), so a mutation with no matching set touches nothing.
   *Threatened by:* `:has()`, `*` on the left of a combinator, attribute
   selectors on frequently changed attributes, `:nth-child` (sibling sets).
9. **Script's synchronous queries flush only the path** (uncertain; no engine does less than a stage flush, from memory). `offsetWidth`
   after a mutation forces the update of the dirty ancestors on the path to
   the queried box, not the frontier of the whole document. *Threatened by:*
   anything in 5 whose exit state changed, which forces the later chain.
10. **Speculation only where fix-up is local and detectable** (promising; measured for floats). (Floats;
    optimistic layout under old style ids; viewport-first estimates.)
    *Threatened by:* speculation whose mismatch is detected late (estimates
    whose correction moves what is already on screen).

---

## 6. What this asks of Whitefoot (collected)

- Range facts as a property of a container (a `Slots` whose invariant says
  its entries are distinct), usable by every loop over it without
  re-derivation; the ordered-result-list loop binding; contract-only
  parameters erased — all recorded in Snowghost's `docs/todo.md` already,
  and the mechanism (#203/#204) is at the pin. Needed by: per-`NodeId`
  style scatter (any model), (b)'s waves.
- A statement of the limit in §1.3: proved key completeness holds for owned
  values and contiguous ranges; the tree decision should say so.
- W4 (snapshots or a persistent arena) for frame pipelining with script;
  not needed for (a) without pipelining.
- `swap` (OP-11) for double-buffered chunks and for replacing a child
  context's `Box` without copying — exists.
- W8's shape decides whether chunk shipping waits: a waiting write forces
  the frame-end batch of §3.a; a non-waiting write into shared memory with
  a separate signal lets chunks stream from inside the recursion.
- Nothing for cross-stage overlap itself: PAR-1 over adjacent statements
  with disjoint rows and PAR-2 over `children[i]` are the mechanism.

---

## 7. Experiments, in the order I would run them

| Id | Question | Needs | Criterion (written here, before measuring) |
|---|---|---|---|
| E5 | How local is CSS on these pages per mutation class? | two full runs + a diff tool; a scripted mutation set (text edit in one paragraph; class toggle mid-page; insert a block at the top; `html` font-size; `--x` on `:root`). Two pitfalls the tool must handle: interned ids are assigned in first-occurrence order per run, so the diff dereferences each id to its group *value*, never compares ids; and a structural mutation shifts preorder indices and context paths, so elements, contexts and paragraphs are aligned across runs by a stable marker (an attribute the driver emits, or the source position) | reports the affected set per class; decides the unit (§1.1) and whether §2.1's custom-property record is needed |
| E4 | Cost of re-stacking the dominant BFC alone | a timer around the block pass of html5's largest context | < 0.5 ms sequential → no translation bookkeeping; else design the translate path |
| E2 | Per-element style store: renumber vs certified scatter vs `Segments` | three small drivers over ecma262's element count | per single insertion at the top: time and, for the certificate, compile time; the faster at < 1 ms wins; a certificate that costs > 2 s of proof per loop is reported to Whitefoot |
| E1 | Incremental layout on the owned tree (model a core) | dirty flags, `Space` cutoff, paragraph keys on the current stage | one-paragraph edit < 1 ms at four workers and < 1/100 of the full stage; `html` font-size ≤ 1.2 × full; byte-identical dumps against a full run |
| E3 | Does cross-stage overlap (a) beat barriers (c)? | E1 plus a staged driver; a 100-cell scattered edit | (a) > 20 % faster, else (c) first |
| E6 | Damage vs tiles in the shell | paint and a Skia shell | damage-rect raster < 1/5 of tile raster for a single edit; scrolling at display rate with a persistent surface |
| E7 | Viewport-first speculative layout for loading | paint, estimates | first viewport < 1/10 of full stage; shift < 1 line in 90 % of sampled viewports |

---

## 8. Top three recommendations

1. **Run E5 now, before any incremental code.** Two full runs and a diff
   tell us the true affected set of each mutation class on the real pages:
   whether paragraph+context is the layout unit, how far style cutoffs
   reach, and whether custom properties need a finer record. It answers the
   recorded open question with measurement and costs a diff tool, not an
   architecture — a tool that compares group values rather than interned
   ids and aligns units across runs by a stable marker (§7, E5), since ids
   and preorder positions both move between runs.

2. **Build model (a) on the owned context tree, with (c)'s staged driver
   as its control (E1, E4, E3).** It is the model whose independence
   Whitefoot proves without new facts (recursion over `children[i]`,
   per-paragraph loops, `writes(ctx)` rows), its cutoffs are value
   comparisons on data the code already stores (`Space`, interned ids,
   `intrinsic_known`), and cross-stage concurrency is emergent rather than
   scheduled. Replace the preorder-indexed style storage with per-`NodeId`
   slots first (E2 decides how), checkpoint the box walk's state at context
   boundaries so Q63 survives per-context rebuilds, and write every stage as
   the attribute-grammar discipline of §3.e1: only `Space`/inherited ids
   down and sizes up cross a boundary.

3. **Fix the paint boundary before paint is written:** a chunk per context
   with paint phases, coordinates relative to the context, a stacking
   context's order list of (chunk, phase) references, and spatial nodes for
   transforms, fixed and sticky — the scene the shell retains and damages by
   chunk bounds. Absolute positions, static positions of absolutely
   positioned boxes and multicol column offsets are resolved in that one
   walk. This makes paint incremental from its first version and leaves the
   tiles-or-damage question (E6) to the shell, where it belongs.

Open questions I could not settle from the sources: the real cost of the
inherited pass restricted to a subtree when interning stays last (cutoff
needs ids during the pass); whether `Segments` can carry a per-segment
distinctness fact; how reclamation of interning tables and the text arena
interacts with stable ids over many frames; and what W4 looks like once
script exists.
