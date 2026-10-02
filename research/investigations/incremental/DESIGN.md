# End-to-end incremental concurrent rendering: a research tree

## Question

How should a renderer be built so that one change to a page costs work in
proportion to what the change actually affects, from the document through
style, layout and paint to the screen, with the stages running concurrently
across their boundaries rather than as whole-document passes?

The owner's framing, after the layout stage (mbbill/Snowghost#27), restated
in English: Chrome's pipeline supports incrementality poorly. Each stage is
hand-tuned for what may be reused, and its layering and tiling are hacks
around that, so changing one pixel repaints a tile. Incrementality is a
question of data coupling. What is not coupled to a change need not be
computed, and in Whitefoot uncoupled work is also provably parallel.
End-to-end parallelism therefore does not mean running Chrome's stages
concurrently. It means one local change flows through style, layout, paint
and presentation as far as its dependencies reach and no further, while a
change that affects the whole page still recomputes the whole page.

This record is a research tree, not a plan. It maps the approaches, what
each needs, what is established, what was measured here, what looks
promising, what is hard, and the experiments that would decide between
them. `design/pipeline.md` already decides that every stage is incremental
and parallel end to end, and that each stage is a pure function memoized by
its inputs. This tree is what that decision needs before it can be built.

## How to read the tree

Each node carries one status:

- **measured:** observed on the three real pages or in this repository's
  code, with the record named;
- **established:** shipped or published practice, with the system named;
- **promising:** consistent with the measurements and with Whitefoot's
  rules, but not yet built or measured here;
- **uncertain:** plausible, with an open question that decides it;
- **hard:** possible, at a cost or with an obstacle stated;
- **dead end:** excluded by an argument or a measurement given in the node.

The five branch notes under `notes/` hold the detail and their own sources:

- `notes/theory.md`: incremental computation families and Whitefoot's
  language rules;
- `notes/architecture.md`: units, couplings, execution models and the
  evolution of the current code;
- `notes/engines.md`: what Blink, Gecko, WebRender, Servo and UI toolkits
  do, mechanism by mechanism;
- `notes/fanout.md`: the census of how far edits propagate in Chromium on
  the three pages;
- `notes/raster.md`: from changed content to pixels without tiles.

Each note marks what its author fetched, measured or recalled from memory.
A recalled claim is a lead, not evidence. The census scripts and their
aggregates are in `census/`.

## The budget

These are the numbers every branch below has to meet.

- **Full recompute is about 50 frames.** html5's style stage takes 0.18 s
  and its layout stage 0.59 s at four workers
  (`research/investigations/layout/DESIGN.md`, Layout results;
  `research/investigations/concurrency/DESIGN.md`, Shape D). That is about
  0.8 s, against 16.7 ms for a 60 Hz frame and 4.2 ms at 240 Hz. Parallelism
  alone cannot make full recomputation an interactive path. (measured)
- **A frame where nothing changed must cost almost nothing.** Checking
  120,000 memoized units at 100 ns each costs 12 ms. One scan of a dense
  version array costs about 1 ms. Anything else must be push-based: the
  write marks what it dirties (`notes/theory.md` §0; arithmetic, with the
  per-unit constants an estimate).
- **Dynamic dependency tracing is affordable per formatting context or
  paragraph, not per box.** At about 100 ns to 1 µs per recorded edge, per
  box tracing costs as much as the work it saves (`notes/theory.md` §0;
  order of magnitude from memory). How many contexts and paragraphs the
  pages have is the first number experiment X1 records.

## What the census measured

`notes/fanout.md` applied 14 kinds of edit to the three pages in Chromium:

- 375 edits on apollo11, and 16 and 12 per kind on html5 and ecma262;
- a cheaper census of ancestor heights with 300 edits per kind per page.

For each edit it diffed every element's computed style and rectangles.
(measured; the limits are in its §0)

- **Style stays in the edited subtree.** In 405 of 406 samples the style
  change stayed inside the edited element's subtree. A leaf color or font
  size change restyles 1 to 2 elements; a container-level one restyles 64
  to 137 at the median.
- **A word edit almost never changes an ancestor's height.** 88 to 94
  percent of single-word insertions change no ancestor's height (12 percent
  on apollo11, 6 percent on ecma262 and html5).
- **When a height changes, absolute positions move but little else
  changes.**
  - A 12-word insertion moves a median of 4,415 boxes on apollo11 and
    54,842 on ecma262.
  - Measured as translation roots relative to the containing block, the same
    edits leave 40 and 33 boxes to change.
  - Across the kinds that move many boxes, 96 to 100 percent of the movement
    is an ancestor's translation.
- **Offsets relative to the parent are not enough on flat pages.**
  html5's `body` has 3,545 block children. Removing one `dd` moves 117,137
  boxes. It needs 3,560 offset rewrites with offsets relative to the parent,
  and 1 with each box anchored to the end of the preceding sibling.
- **Some edits are not local at all.**
  - Changing a container's inline size resizes 2,205 elements at p90 on
    apollo11's article body and leaves 86 percent of the nodes dirty.
  - An inherited font change on a container restyles 89 to 137 elements and
    resizes 91 to 151 at the median.
- **Couplings that reach siblings rather than only ancestors or
  descendants:**
  - table column widths;
  - flex and grid stretch;
  - shrink-to-fit up through inline ancestors: one word edit changes some
    ancestor's width in 49 to 73 percent of edits, along a median run of 1
    to 2 ancestors;
  - counters: an item inserted into apollo11's reference list renumbers a
    median of 147 following items.

## The tree

### 1. Where incrementality comes from: the couplings

The census and `notes/architecture.md` §2 separate couplings CSS imposes
from couplings the representation adds. Only the first kind is
unavoidable.

1.1 **Inheritance and selectors.** Status: measured local, established
mechanisms.
- **Scope.** A style change stays in the edited subtree, as the census
  shows.
- **Finding what to restyle.** This is a static analysis of the sheet:
  Blink's invalidation sets and Stylo's invalidation map. Both are
  established and over-approximate; `:has()`, sibling combinators and
  `:nth-*` widen them (`notes/engines.md` §1.1–1.2).
- **What replaces the hand-written bridge.** The bridge between "which
  style changed" and "which stage reruns" is Blink's style diff or Gecko's
  change hints. It can become each stage keyed by its own value groups,
  which Snowghost's interned groups already are. Status: promising.

1.2 **Line breaking inside a paragraph.** Status: measured local. Most word
edits end at the paragraph, since its height, line count and widths stay the
same. The paragraph's line-breaking output is the first boundary at which a
rerun can stop (`notes/fanout.md` §5). Text preparation is 60 to 67 percent
of the layout stage on the large pages, and it runs per paragraph.

1.3 **Heights pushing the content after them.** Status: measured; the
coupling that dominates in absolute terms, and representational in
almost all of its extent.
- **Context-relative positions.** These are Snowghost's Q55. They confine
  the coupling to the formatting context.
- **Flat contexts.** On flat contexts the cost is O(siblings) unless the
  offsets themselves become incremental. Three candidates, none measured:
  - each box anchored to its preceding sibling's end, a chain;
  - a balanced tree of offsets, as Zed's SumTree keeps sums over a
    sequence;
  - sending flow sizes and letting the consumer take prefix sums
    (`notes/raster.md` §6).
- **Decided by:** experiment X3.

1.4 **Inline size down, and inherited fonts.** Status: measured
non-local.
- **What happens.** A container's width change re-wraps every paragraph
  inside it, and an inherited font change reaches every descendant.
- **What is left.** Width-keyed reuse can help only where a paragraph's
  breaks are the same over a range of widths. Experiment X4 measures how
  often that holds.
- **Otherwise.** These edits are full-subtree work. Their speed has to come
  from parallelism over independent subtrees, which the stages already have.

1.5 **Siblings coupled through their container: tables, flex, grid.**
Status: measured, bounded. A cell or item change can resize its siblings
through column widths or stretch. Treat the container as one work item,
with the container's line or track sizes as its internal key.

1.6 **Chains in document order.** Status: promising for checkpoints;
speculation for counters.
- **The chains:**
  - inherited values;
  - counters and quotes, which the box tree builder now resolves in its
    walk (Q63);
  - sibling positions for `:nth-*`;
  - the block pass's running height and margin strut.
- **The idea.** Checkpoint the chain's state at unit boundaries, so that a
  rerun starts from the entry state and stops where the exit state equals
  the stored one (`notes/architecture.md` §5, invariant 5).
- **What breaks it.**
  - Counters read far ahead: 147 renumbered items is paint-sized fan-out.
  - `:nth-last-*`, which counts from the end.

1.7 **Floats, percentages, multi-column, absolute positioning.** Status:
uncertain.
- **Floats and percentages.** These were present on the pages but the
  census did not isolate them.
- **Floats specifically.**
  - The layout prototype's speculative line breaking re-broke 0 of
    32,684 and 4 of 770 paragraphs.
  - That bounds the cost of speculation, not of an incremental
    re-fill.
  - Source: `research/investigations/concurrency/DESIGN.md`.
- **Multi-column.** This is coupled across the whole container.
- **Absolute positioning.** This couples a box to a distant containing
  block.

1.8 **Representational couplings in the current code.** Status: measured
in the code. Each has a replacement (`notes/architecture.md` §2.12,
§4):
- style arrays indexed by preorder position, which an insertion renumbers;
- `Fragment.owner`, a preorder index for elements but a `NodeId` for text;
- placement by one global walk;
- the box tree built by one walk that carries counters, so one context
  cannot be rebuilt alone;
- append-only shared stores, such as custom properties and the resolved
  list.

### 2. Units and identity

2.1 **The unit differs by stage.** Status: promising.

| Stage | Unit |
|---|---|
| style | the styled node |
| layout | the formatting context, and inside it the paragraph |
| paint | a chunk per context and paint phase |

- **Why not the context alone.** One block formatting context holds 85 to
  95 percent of each page's text (concurrency investigation). So reuse
  inside a context, at paragraph or block grain, decides most of the gain.
- **Derived identities.** Fragments, lines and chunks take their identity
  from their unit; only nodes and contexts need identities of their own
  (`notes/architecture.md` §1.1).

2.2 **Stable identity.** Status: promising. There are three schemes
(`notes/architecture.md` §1.2):
- renumbering preorder after each change;
- `NodeId` plus a generation;
- content keys, which can recognize a moved subtree.

The recommended combination is `NodeId` with a generation for nodes and the
owned tree's path for contexts. Experiment X2 decides how per-node style
storage is laid out under it.

2.3 **Complete, value-shaped keys with equality cutoff.** Status:
established in Salsa and LayoutNG's constraint-space cache.
- **The idea.** Every unit stores its inputs as values and reruns only when
  one differs. A rerun whose output equals the old one stops the
  propagation, which is early cutoff.
- **Hidden inputs to keep out of the dark:**
  - the viewport, `rem` and loaded fonts;
  - image sizes;
  - counter and quote state;
  - sibling positions.

  Each must be in the key or versioned (`notes/architecture.md` §5,
  invariant 2).

### 3. How results are reused: the families of incremental computation

From `notes/theory.md` §1:

3.1 **Explicit keys and versions as data.** Status: promising; the family
that fits Whitefoot.
- **The mechanism.** Salsa-style memoization with arenas, generations and
  change ticks: indices into arenas, versions stored as integers, interned
  ids as cheap equality.
- **Push-based dirtying.** Done with ticks, it keeps no-change frames
  cheap.

3.2 **Traced dependency graphs (self-adjusting computation, Adapton).**
Status: dead end at box grain.
- **Cost:** the budget's arithmetic excludes per-box traces.
- **Representation:** Whitefoot stores no references, which excludes the
  thunk graphs they rely on.
- **What survives:** demand-driven evaluation (3.6, 4.4).

3.3 **Differential and timely dataflow.** Status: uncertain.
- **For selector matching:** promising as a model, where a sheet change is
  a delta over (rule, element) pairs.
- **Elsewhere:** hard.

3.4 **Derivatives of functions (incremental λ-calculus).** Status:
uncertain in general. Its useful special case is a delta API for one
function, such as re-breaking a paragraph from the changed line onward,
which LayoutNG's line reuse does (`notes/engines.md` §2.1, from memory).

3.5 **Signals and reactive frameworks.** Status: dead end at renderer
scale. Subscriber lists per value cost the per-box bookkeeping 3.2 excludes.
They remain a fine mental model for the graph of stages.

3.6 **Reconciliation at the output boundary.** Status: established in
React and WebRender's interning. Compare the new chunk list with the old by
identity and hash, and send only the difference.

3.7 **Pointer-based persistent structures.** Status: dead end in
Whitefoot. The language has single-owner boxes and no stored references, so
hash-consed DAGs, HAMTs and ropes with shared nodes cannot be represented.
Arenas with generations (3.1) take their place; Whitefoot's spec names
generations as data ([OP-13]).

### 4. Execution models: concurrency across stage boundaries

From `notes/architecture.md` §3 and `notes/theory.md` §2.4–2.5:

4.1 **One task per subtree, running style, layout and paint together.**
Status: promising; the natural fit.
- **The model.** An independent context runs style, intrinsic sizes,
  layout and paint for its subtree as one recursion over the owned context
  tree.
- **Concurrency.** Sibling subtrees run concurrently, so stages overlap
  across contexts without a scheduler.
- **Why Whitefoot proves it without new facts.**
  - recursion over `children[i]` is an affine element write (PAR-2);
  - the rows are per context.
- **Cutoffs.** These are value comparisons on data the code already
  stores: `Space`, interned ids, `intrinsic_known`.
- **The constraint.** Only the available space and inherited ids may go
  down, and only sizes may come up: the attribute-grammar discipline of
  `notes/architecture.md` §3.e1.

4.2 **A dataflow graph of keyed nodes with change propagation.** Status:
hard in its general form.
- **Proof cost.** Writing results at dirty indices needs a distinctness
  fact derived each frame and an `apart` certificate. Shape D showed both
  can be done, at a proof cost.
- **What 4.1 avoids.** The flat loop over a dirty list is exactly the step
  4.1's recursion makes unnecessary.

4.3 **Staged passes over a dirty frontier.** Status: established; this is
Blink's lifecycle. It is the control that 4.1 must beat (experiment X6).

4.4 **Demand-driven: pull from the frame.** Status: uncertain.
- **Strong for:** paint, and very long documents, where only the viewport
  and a margin around it need painting.
- **Weak for:** layout, whose positions depend on everything before them.
- **Open question.** Whole-page paint with culling in the shell, or
  viewport-dependent paint on request (`notes/raster.md` §6, D4b), decides
  whether the shell needs a channel back to the renderer.

4.5 **Pipelining frames over snapshots, and optimistic speculation across
stages.** Status: uncertain.
- **Script.** Frame pipelining needs snapshots of the document while script
  runs, which Whitefoot does not yet offer.
- **Speculation.** It pays only where a misprediction is found early and
  fixed locally, as floats were (`notes/architecture.md` §3.e2–e3).

### 5. Whitefoot: what it gives, and what it would need

From `notes/theory.md` §2 and `notes/architecture.md` §6:

5.1 **The effect row as a memoization key.** Status: established in part.
- **Complete in places.** Rows are checked both ways ([EFF-2]); there are
  no globals or function values ([FN-5]); host outcomes come only through
  waiting calls. So the places a function can read are exactly its row and
  its by-value arguments.
- **Not complete in values.** Nothing records whether a read place changed,
  so the pipeline decision's "the compiler proves the memoization key
  complete" holds for places, not for versions.
- **The deduplication licence.** [EFF-3]'s licence to deduplicate calls
  needs a pure function that allocates nothing, which no stage result is.
- **Practice that follows: pass the inputs, not the world.** Pass
  `&styles^.groups[k]` rather than `&styles`, so the row names the element's
  path.

5.2 **Equality for cutoff.** Status: gap with a route. Whitefoot has no
aggregate equality. The routes are:
- the integer and interned-id comparisons the cheap cutoffs need;
- an interface-supplied `eq`;
- a derived structural equality as a future language decision.

5.3 **Versions the compiler maintains.** Status: proposal, gated on
experiment X2.
- **The mechanism.** A `tracked` storage root whose version the compiler
  bumps at every write its rows already know, and a `memo fn` that reruns
  when the version of a path it reads moved.
- **First step.** Ticks written as library code come first; the language
  mechanism needs measured grounds and a decision card.

5.4 **Parallel work over a dirty set.** Status: feasible today in two
shapes.
- **Recursion from the root.** Pull from the root over the owned tree,
  descending only where a subtree's maximum tick moved. It needs no
  certificate, and the frontier is an antichain by construction.
- **Flat loop.** A loop over a dirty list needs the per-frame distinctness
  fact.

5.5 **Concurrency across stages.** Status: hard as scheduled concurrency,
promising as emergent concurrency.
- **Spawns.** These take values only ([WAIT-3]), so stages cannot share a
  reference.
- **What works.** Stages overlap through PAR-1 and PAR-2 when each stage's
  outputs are partitioned like its work.
- **Waiting writes.** If writing to the shell's shared memory waits, chunks
  must be batched at the end of the frame.

5.6 **Range facts as a property of a container.** Status: wanted; already
in `docs/todo.md`. A `Slots` whose invariant says its entries are distinct,
usable by every loop over it without deriving the fact again.

### 6. The paint boundary

`notes/architecture.md` §8, `notes/engines.md` §3 and §7.4, and
`notes/raster.md` §6 converge here. The recommendation is to fix this
boundary before paint is written.

6.1 **Chunks per context and paint phase.** Status: promising.
- **Coordinates.** Each chunk is in its context's coordinates.
- **Identity.** Each chunk has a stable identity and a content hash.
- **Stacking.** A stacking context is an order list of references to
  chunks.
- **Properties.** Transform, clip, effect and scroll live in a property
  tree, so a change to one of them rewrites one node and no content.
- **Precedent.** Blink's paint chunks and property trees are the
  established precedent for separating order and properties from content;
  their layerization is the heuristic part not to copy.

6.2 **Deltas to the shell.** Status: promising.
- **What is sent.** Only changed chunks, plus order lists and property
  nodes, through shared memory with epoch acknowledgement.
- **What the cost is.** On the CPU side the cost of a reflow is the bytes
  crossing the boundary, not time. On a synthetic 250,000-chunk scene, a
  spatial index answers a viewport query in under 1 µs. Rewriting 245,000
  absolute positions takes 0.2 ms, against 0.04 µs on a tree of relative
  offsets (`notes/raster.md` §1; measured on the CPU, scene size assumed).

### 7. From changed content to pixels

From `notes/raster.md` and `notes/engines.md` §4 and §6. This container
has no GPU, so every GPU figure in this section is cited or derived, not
measured.

7.1 **Redrawing the whole scene on the GPU every frame.** Status:
established as a legitimate control.
- **Who does it.** Zed's GPUI, Vello-based Masonry and early WebRender.
- **Its limit.** Power, memory bandwidth, weak GPUs and 4K at 240 Hz, not
  frame time on a discrete GPU.

7.2 **Redrawing exactly the damaged region from a retained scene.**
Status: promising.
- **The mechanism.** The damage is the union of the old and new bounds of
  the changed chunks. Scissor to it, find the chunks that intersect it with
  a spatial index, and redraw only those.
- **Precedent.** WebRender already scissors to dirty rectangles smaller
  than a tile.

7.3 **Tiles and layers as the unit of invalidation.** Status: dead end for
this goal.
- **Why.** They are a hand-placed partition, as in Chrome's cc and viz
  union damage.
- **What they provided, and what replaces it.**
  - Memory bounds and raster threading must be provided some other way.
  - Pixel caches pay only for subtrees that are expensive to draw (filters,
    shadows, deep overdraw), promoted by measured cost with hysteresis.
  - Offscreen groups the semantics require (opacity, blend modes, filters)
    stay as nodes of a render graph, not persistent layers.

7.4 **Partial presentation.** Status: established with limits.
- **What exists.** Buffer age and partial update in EGL, Wayland damage,
  DXGI dirty and scroll rectangles, and damage clips in KMS.
- **The limits.** Vulkan has no buffer-age query. The Metal and
  CoreAnimation behavior is unverified.
- **What it saves.** Mostly power and memory traffic, not frame time.

7.5 **Text.** Status: uncertain. On text-heavy pages glyph drawing is the
dominant item. A glyph atlas, Slug-style curve rendering and Vello's
compute rasterization each need hardware to compare (experiment X10).

7.6 **A software damage rasterizer in Whitefoot.** Status: proposal for
the owner. Writes to disjoint rows are provable. It would serve as a
pixel-exact test oracle, a headless target and a fallback, and it does not
replace the shell's GPU path (`notes/raster.md` §7).

### 8. The oracle for every incremental step

Status: established here; extend it. Snowghost already requires the
sequential and `--par` builds to give byte-identical dumps. An incremental
run is held to the same rule: after a history of edits, its dumps must be
byte-identical to a full run on the final document. This gives an exact
oracle for every experiment below at no extra design cost
(`notes/theory.md` §2.7).

### 9. What no engine solves

From `notes/engines.md` §7.3:

- **Cycles in the dependency graph.** Container queries and `:has()` make
  it cyclic, and CSS restricts them with containment.
- **Inherent non-locality.** The non-local couplings of 1.4 to 1.6 stay
  non-local whatever the representation.
- **The cost of finding what to recheck.** It grows with depth times the
  width of a level unless sequences are kept as summary trees, which margin
  collapsing and floats complicate.
- **Key comparison costs.** Comparing a key can cost more than recomputing
  a cheap node.

## Experiments

The experiments below are merged from the five notes, in the order they
build on each other. Each criterion is written before the experiment is
run.

| Id | Question | Needs | Criterion |
|---|---|---|---|
| X1 | How local are real edits in Snowghost's own stages, and how many contexts and paragraphs do the pages have? | two full runs around a scripted edit, and a diff tool that compares group values, not interned ids, and aligns units by a stable marker | records the affected set per edit kind at each unit; decides whether context plus paragraph is the layout unit (`notes/architecture.md` E5, `notes/engines.md` E1) |
| X2 | How is per-node style stored under stable identity: renumbering, a certified scatter, or `Segments`? | three small drivers at ecma262's element count | for one insertion at the top, the faster under 1 ms wins; a certificate proof over 2 s per loop is reported to Whitefoot |
| X3 | Which offset structure: context-relative, sibling-anchored, or offset tree / prefix sums? | the census's edit script run on Snowghost's layout output | prefix sums or a tree if the context-relative scheme rewrites more than 10^4 coordinates where they rewrite fewer than 10^3 (`notes/raster.md` X9) |
| X4 | Do width-keyed paragraph results hit, given that a paragraph's breaks hold over a range of widths? | paragraph output as a function of inline size, swept | decides whether container-width edits get memoization or only parallelism (`notes/fanout.md` §4, `notes/engines.md` E3) |
| X5 | Incremental layout on the owned context tree (4.1), with cutoffs on `Space` and paragraph keys | X1, X2; the current stage | a one-paragraph edit under 1 ms at four workers and under 1/100 of the full stage; an `html` font-size change no worse than 1.2 times a full run; byte-identical to a full run (8) |
| X6 | Does concurrency across stages (4.1) beat staged passes (4.3)? | X5 and a staged driver; a scattered 100-cell edit | 4.1 more than 20 percent faster, else 4.3 first |
| X7 | A CPU damage-redraw oracle | a software rasterizer of chunks | damage-scissored and age-tracked redraws byte-identical to a full redraw; each deliberate breakage (missing spread, omitted overlap, wrong buffer age) fails it once (`notes/raster.md` X1) |
| X8 | Damage redraw against full redraw and pixel caches on a real GPU | a GPU host and the paint stage | damage-limited rendering is justified if full redraw exceeds 25 percent of the frame budget or damage saves more than 20 percent of power; otherwise subtree caches promoted by cost, never tiles (`notes/raster.md` X3–X4) |
| X9 | Whole-page paint with culling in the shell, or viewport-dependent paint | paint, shell | first-frame and scroll latency, and the size of the full list |
| X10 | Text rendering: glyph atlas, Slug, or Vello | a GPU host | frame cost of a text-heavy page per approach (`notes/raster.md` X5) |

X1 to X4 and X7 run in this container with the existing stages. X5 and X6
need an incremental layout prototype. X8 to X10 need a paint stage and real
hardware.

## Where the branches agree

These are leads to discuss, not decisions:

- **Measure before building.** X1, X3 and X4 decide the unit, the offset
  structure and how far memoization reaches, at the cost of drivers and
  diffs rather than an architecture.
- **The candidate execution model is 4.1, with 4.3 as its control.**
  Whitefoot proves 4.1's independence without new facts, its cutoffs use
  data already stored, and its concurrency across stages falls out of the
  proofs instead of being scheduled.
- **Fix the paint boundary (6) before writing paint.** That boundary is
  chunks per context in local coordinates, with stable identities, a
  property tree and order lists. It is the hardest interface to change
  later. Tiles and layers then stay out of the design, and the shell decides
  damage by chunk bounds.
- **Ask Whitefoot for nothing yet beyond what is recorded.** Versions as
  data and passing inputs rather than the world come first. A compiler
  mechanism for versions (5.3) needs X2's measurements and a decision card.

## Open questions

- **Counters and quotes.** How are they kept incremental once the box tree
  builder resolves them in one walk? Checkpoints at context boundaries are
  speculation.
- **Snapshots.** What does a document snapshot look like once script
  exists? Frame pipelining needs one.
- **Stable identities over time.** How do the interning tables and the text
  arena reclaim space under stable identities over many frames?
- **`Segments`.** Can it carry a distinctness fact per segment?
- **Viewport-dependent paint.** Is it worth a channel from the shell back
  to the renderer?
