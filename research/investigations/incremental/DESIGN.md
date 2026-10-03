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
question of data coupling: what is not coupled to a change need not be
computed, and in Whitefoot uncoupled work is also provably parallel.
End-to-end parallelism therefore does not mean running Chrome's stages
concurrently. It means one local change flows through style, layout, paint
and presentation as far as its dependencies reach and no further, while a
change that affects the whole page still recomputes the whole page.

This record is a research tree, not a plan. It maps the approaches, what
each needs, what is established, what was measured here, what looks
promising, what is hard, and the experiments that would decide between
them. `design/pipeline.md` decides that every stage is incremental and
parallel end to end and that each stage is a pure function memoized by its
inputs. This tree is what that decision needs before it can be built, and
it finds one place where the decision claims more than the language gives
(5.1).

## The owner's direction

The owner ruled on the tree's first draft in conversation, in Chinese. In
English:

- **Priorities.**
  1. The main line is the minimal end-to-end update: each change updates
     only what it affects, through every stage to the screen.
  2. Concurrency inside one frame is auxiliary: use the cores to finish a
     frame's work within the frame. It constrains the main line's design
     rather than following it as a later phase.
  3. Next comes priority by viewport: work the viewport needs first,
     the rest later (X16).
- **Frame pipelining is a fallback, not the main line** (4.7). In the
  owner's words: where the quickest response to an action matters it
  adds latency, which is worse at 60 Hz; scrolling is not purely
  compositing; and script animations and other frame callbacks run every
  frame, while most animations on the web are written badly.
- **Pixels.** Layers and tiles are not the unit of invalidation. The shell
  keeps a retained scene and redraws the damaged region from vectors;
  beyond the buffers it presents, pixels are cached only where cost and
  stability call for it (7). The owner rejected a full-page target copied
  to the swapchain every frame as certainly slow on high-resolution
  screens (7.3).
- **The boundary (Q65).** The renderer gives the shell facts about the
  page, and the shell owns every policy that turns them into pixels for
  its platform. A policy changes cost, not the picture (6.3; the exact
  invariant is Q66).

## How to read the tree

Every node carries exactly one of these statuses, so the tree can be
filtered by them:

| Status | Meaning |
|---|---|
| **measured** | observed on the three real pages or in this repository, with the record named |
| **established** | shipped or published practice, with the system named |
| **promising** | consistent with the measurements and with Whitefoot's rules, not yet built or measured here |
| **uncertain** | plausible, with an open question or a measurement that decides it |
| **hard** | possible, at a cost or past an obstacle stated in the node |
| **unlikely** | argued against, but the argument rests on an unmeasured constant or a recalled source |
| **dead end** | excluded by an argument or a measurement given in the node |

A node that holds for some cases and not others is split into the cases.

**Where the detail lives.** The tree is drawn from seven explorations under
`notes/`:

- `theory.md`: incremental computation families and Whitefoot's language
  rules;
- `architecture.md`: units, couplings, execution models and the current
  code's evolution;
- `engines.md`: what Blink, Gecko, WebRender, Servo and UI toolkits do;
- `fanout.md`: the census in Chromium of how far edits propagate on the
  three pages;
- `raster.md`: from changed content to pixels without tiles, the first
  pass, corrected at its top by the next two;
- `gpu2d.md`: a survey of GPU 2D backends, text and the operating
  systems' presentation interfaces, with an experiment plan for a GPU
  machine;
- `webrender.md`: why WebRender added picture caching and operating-system
  compositor surfaces, and which of its reasons apply here.

`notes/critique.md` is a separate critique of this tree's first draft,
which this version answers.

**How to treat the notes' claims.** Each note marks what its author
fetched, measured or recalled. A recalled claim is a lead, not evidence;
nodes below that rest on one say "recalled". The notes refer to a shared
brief, `context.md`, whose content is the Question above; it is not kept.

**The census material.** `census/` holds the census's scripts and
aggregated results, and a CPU micro-benchmark. The census's raw per-edit
JSON is not kept, since its aggregates are.

## The budget

These are the numbers every branch has to meet.

- **A full recompute costs about 50 frames.** status: measured.
  - html5's layout stage takes 0.59 s at four workers
    (`research/investigations/layout/runs/time-parts.txt`).
  - Its style stage takes 0.18 s in the prototype's shape C
    (`research/investigations/concurrency/DESIGN.md`, Shape D); the real
    style stage is of the same order.
  - That is about 0.8 s, against 16.7 ms for a 60 Hz frame and 4.2 ms at
    240 Hz.
  - Parallelism alone cannot make full recomputation an interactive path.
- **The unit counts.** status: measured. The real layout stage
  (`research/investigations/layout/runs/time-parts.txt`):

  | Page | Formatting contexts | Paragraphs |
  |---|---:|---:|
  | ecma262 | 10,217 | 57,514 |
  | html5 | 13,843 | 60,868 |
  | apollo11 | 1,113 | 2,569 |

  One block formatting context holds most of each page's text
  (`research/investigations/concurrency/DESIGN.md`). html5's dominant one
  holds 20,919 paragraphs (`notes/architecture.md` §0).
- **A frame in which nothing changed must cost almost nothing.** status:
  arithmetic, with recalled constants.
  - Checking 120,000 memoized units at 100 ns each costs 12 ms.
  - One scan of a dense version array costs about 1 ms.
  - Anything else must be push-based: the write marks what it dirties, or
    the change arrives as an edit list (3.9). See `notes/theory.md` §0.
- **Dynamic dependency tracing.** status: uncertain, one measurement
  away.
  - The arithmetic: at a recalled 100 ns to 1 µs per recorded edge and
    about ten edges per unit, tracing a full build of html5 would cost
    14 to 140 ms per context and 61 to 610 ms per paragraph.
  - Against the 0.8 s full build, that is 2 to 17 percent at context grain
    and 8 to 76 percent at paragraph grain. `notes/theory.md` takes 5
    percent as the acceptable bookkeeping share.
  - Which end of the constant is true decides whether recorded reads (3.3)
    are affordable at context grain. Experiment X12 measures it.

## What the census measured

`notes/fanout.md` applied 14 kinds of edit to the three pages in Chromium:

- 375 edits on apollo11, and 16 and 12 per kind on html5 and ecma262;
- a census of ancestor heights with 300 edits per kind per page;
- per edit, a diff of 26 of the 50 compared longhands and of every
  element's rectangles.

Edit targets were uniform over elements, so mostly leaves. Pseudo-elements
and markers were invisible, class edits were no-ops in 42 to 88 percent of
samples, and every edit was a single edit on a loaded page. Its §0 lists
these limits. The findings:

- **Style stays in the edited subtree.** In 405 of 406 samples the style
  change did not leave the edited element's subtree. A leaf color or font
  size change restyles 1 to 2 elements, a container-level one 64 to 137 at
  the median. Selector couplings across the tree (siblings, `:has()`)
  occurred once and are not characterized.
- **A word edit almost never changes an ancestor's height.** 88 to 94
  percent of single-word insertions change no ancestor's height (12
  percent on apollo11, 6 percent on ecma262 and html5).
- **Absolute positions move in bulk, but it is almost all translation.**
  A 12-word insertion moves a median of 4,415 boxes on apollo11 and 54,842
  on ecma262, almost all as a translation of whole subtrees. Relative to
  the nearest block ancestor, the edits have a median of 40 and 33
  translation roots. Across the kinds that move many boxes, 96 to 100
  percent of the movement is an ancestor's translation.
- **Offsets relative to the parent do not suffice on flat pages.** html5's
  `body` has 3,545 block children, and removing one `dd` moves 117,137
  boxes.
  - Offsets relative to the nearest block ancestor need 3,560 rewrites.
  - Offsets anchored to the preceding sibling's end need 1.
  - Offsets relative to the formatting context, Snowghost's Q55, would
    need more than the parent-relative count. A block is not a context, and
    html5's dominant context holds 20,919 paragraphs. The census did not
    measure that scheme.
- **Some edits are not local at all.**
  - Changing a container's inline size resizes 2,205 elements at p90 on
    apollo11's article body and leaves 86 percent of the nodes dirty.
  - An inherited font change on a container restyles 89 to 137 elements
    and resizes 91 to 151 at the median.
- **Couplings that reach siblings, not only ancestors or descendants:**
  - table column widths;
  - flex and grid stretch;
  - shrink-to-fit up through inline ancestors: one word edit changes some
    ancestor's width in 49 to 73 percent of edits, along a median run of 1
    to 2 ancestors;
  - counters: an item inserted into apollo11's reference list renumbers a
    median of 147 following items.
- **Edits the census did not apply:**
  - the parser appending during load;
  - a font or an image arriving;
  - animations of layout properties;
  - `:hover`, focus, selection and the caret.

  Experiment X8 covers the first two; the others are open (1.11).

## The tree

### 1. Where incrementality comes from: the couplings

The census and `notes/architecture.md` §2 separate couplings CSS imposes
from couplings the representation adds. Only the first kind is
unavoidable.

1.1 **Inheritance and selectors.**
- **Locality.** status: measured, within the census's limits above. A
  style change stays in the edited subtree for leaf-weighted single edits
  over 26 longhands.
- **Finding what to restyle.** status: established. This is a static
  analysis of the sheet: Blink's invalidation sets, and Stylo's
  invalidation map (recalled). Both over-approximate, more so with
  `:has()`, sibling combinators and `:nth-*` (`notes/engines.md`
  §1.1–1.2).
- **Deriving those tables from the compiler.** status: uncertain. The
  invalidation set of a rule is what the matcher reads for it
  (`notes/engines.md` §1.1). If Whitefoot could reflect a function's effect
  row, or a finer read set, into data, the reverse index from element
  features to rules would come from the compiler instead of a second
  hand-written table.
  - The same holds between stages. "Which style changes affect layout" is
    the union of the layout functions' read sets, where Blink keeps a
    hand-written style diff and Gecko change hints.
  - The open question is whether the spec lets a row be reflected; it names
    rows as checked, not as values.
- **Stage keys from value groups.** status: promising. Each stage keyed
  by the interned value groups it reads, which Snowghost's computed styles
  already are, replaces the hand-written bridge.

1.2 **Line breaking inside a paragraph.** status: measured local.
- **Why it matters.** Most word edits end at the paragraph, since its
  height, line count and widths stay the same. Text preparation is 60 to 67
  percent of the layout stage and runs per paragraph.
- **Consequence.** The paragraph's line-breaking output is the first
  boundary at which a rerun can stop (`notes/fanout.md` §5).

1.3 **Heights pushing the content after them.** status: measured; the
coupling that dominates in absolute terms, and representational in almost
all of its extent.
- **Context-relative positions (Q55).** These confine the coupling to the
  formatting context, but a rewrite inside a context is O(siblings in the
  context), which is large in flat contexts.
- **Making offsets themselves incremental.** Three candidates, none
  measured:
  - **Sibling anchoring:** each box anchored to its preceding sibling's
    end. It reduces html5's removal to 1 rewrite, but turns a position
    query into a walk.
  - **Summary tree:** a balanced tree of offsets (3.8).
  - **Prefix sums at the consumer:** flow sizes sent instead, with the
    consumer taking prefix sums (`notes/raster.md` §6).
- **Decided by:** experiment X3, on Snowghost's own output.

1.4 **Inline size down, and inherited fonts.** status: measured
non-local.
- **What happens.** A container's width change re-wraps every paragraph
  inside it, and an inherited font change reaches every descendant.
- **What might be saved.** Width-keyed reuse saves work only where a
  paragraph's breaks hold over a range of widths. Experiment X4 measures
  how often.
- **Otherwise.** These are full-subtree work: their speed comes from
  parallelism, or from progressive delivery (4.6), not from
  incrementality.

1.5 **Siblings coupled through their container: tables, flex, grid.**
status: measured, bounded. A cell or item change can resize its siblings
through column widths or stretch. The container is one work item, with its
track or line sizes as its internal key.

1.6 **Chains in document order.**
- **The chains:**
  - inherited values;
  - counters and quotes, which the box tree builder resolves in its walk
    (Q63);
  - sibling positions for `:nth-*`;
  - the block pass's running height and margin strut;
  - the document's scroll extent.
- **Checkpoints.** status: promising. A rerun starts from the chain's
  stored state at a unit's entry and stops where the exit state equals the
  stored one (`notes/architecture.md` §5, invariant 5).
- **Summary trees.** status: promising for associative folds, hard for
  the rest. A checkpointed chain is a prefix fold; keeping it as a summary
  tree gives O(log n) updates (3.8). That holds for heights, counters,
  `:nth-child` and scroll extent. Margin collapsing, `clear`, floats and
  `:nth-last-*` under insertion are not plainly associative.

1.7 **Containment declared by the page.** status: established. CSS
`contain` and `content-visibility` declare the boundaries this tree looks
for (`notes/engines.md` §2.1.2).
- **Why implement it.** The renderer must implement them for their
  semantics anyway. Each such box is then a cutoff and a parallel boundary
  at no extra design cost.
- **Their limit.** They are declared by authors, so they cannot be the
  mechanism on pages without them, such as the three measured here.

1.8 **Floats, percentages, multi-column, absolute positioning.** status:
uncertain.
- **Floats and percentages.** They were present on the pages, but the
  census could not isolate them.
- **Floats specifically.** The prototype's speculative line breaking
  re-broke 0 of 32,684 and 4 of 770 paragraphs
  (`research/investigations/concurrency/DESIGN.md`). That bounds the cost of
  speculation, not of an incremental re-fill.
- **Multi-column.** It couples the whole container.
- **Absolute positioning.** It couples a box to a distant containing block.

1.9 **Cycles in the dependency graph.**
- **Stratification.** status: promising as the stated rule. Container
  queries and `:has()` would make the graph cyclic, but CSS stratifies them
  itself: a container query requires containment, which cuts the edge from
  the container's layout to its descendants' style. Evaluating strata in
  order, with any fixpoint only inside one, is the database discipline for
  the same problem.
- **A fixpoint inside a stratum.** status: hard, for termination and
  cost.

1.10 **Representational couplings in the current code.** status:
measured in the code. Each has a replacement (`notes/architecture.md`
§2.12, §4):
- style arrays indexed by preorder position, which an insertion renumbers;
- `Fragment.owner`, a preorder index for elements but a `NodeId` for text;
- placement by one global walk;
- the box tree built by one walk that carries counters, so one context
  cannot be rebuilt alone;
- append-only shared stores, such as custom properties and the resolved
  list.

1.11 **Edits of time rather than of content.** Animations of layout
properties change the same key every frame, so both the bookkeeping floor
and 1.4's full-subtree cost are paid per frame.
- **Animated layout properties.** status: hard, by 1.4.
- **`:hover`, focus and the caret.** status: uncertain. These are mostly
  paint-only and are the most frequent edits of all.

### 2. Units and identity

2.1 **The unit differs by stage.** status: promising.

| Stage | Unit | Cheapest cutoff |
|---|---|---|
| style | the styled node | interned group ids unchanged |
| box tree | the styled node's box | only the structure-affecting groups are read (Servo's box damage) |
| text preparation | the paragraph | text and font groups unchanged |
| layout | the formatting context, and the paragraph inside it | the available space and inputs unchanged; the output size unchanged |
| paint | a chunk per context and paint phase | content hash unchanged |
| scene | the chunk's node in the shell | identity and hash unchanged |

`notes/architecture.md` §1.1 has the full mapping. Fragments, lines and
chunks take their identity from their unit; only nodes and contexts need
identities of their own.

2.2 **Stable identity.** Four schemes, each status: uncertain until
experiment X2:
- **Renumbering preorder after each change.** Cheap to read, but O(n) per
  structural edit.
- **`NodeId` plus a generation.** Stable, but needs per-node storage that
  is not in preorder.
- **Content keys.** These can recognize a moved subtree.
- **Order-maintenance labels.** Labels with gaps keep document order
  comparable under insertion (Dietz and Sleator; recalled;
  `notes/architecture.md` §1.2, `notes/raster.md` §6).

2.3 **Complete, value-shaped keys with equality cutoff.** status:
established in Salsa and LayoutNG's constraint-space cache (both recalled
in part).
- **The idea.** Every unit stores its inputs as values and reruns only
  when one differs. A rerun whose output equals the old one stops the
  propagation.
- **Hidden inputs to keep out of the dark:**
  - the viewport, `rem` and loaded fonts;
  - image sizes;
  - counter and quote state;
  - sibling positions.

  Each must be in the key or versioned (`notes/architecture.md` §5,
  invariant 2).

### 3. How results are reused: families of incremental computation

From `notes/theory.md` §1, `notes/architecture.md` §3.e and the critique:

3.1 **Explicit keys with versions as data.** status: promising; the
family that fits Whitefoot.
- **The mechanism.** Memoization in Salsa's style over arenas with
  generations and change ticks: indices into arenas, versions as integers,
  interned ids as cheap equality.
- **Push-based dirtying.** Done with ticks, it keeps a no-change frame
  near free.

3.2 **Attribute grammars.** status: established as theory, promising as
the frame for this tree.
- **The theory.** A tree of nodes whose attributes flow down (inherited
  style, available space) and up (sizes, intrinsic sizes).
- **What it gives.** Optimal incremental re-evaluation follows from the
  dependencies (Demers, Reps and Teitelbaum, 1981), and the parallel
  schedule can be derived (Meyerovich and Bodík, 2010).
- **Why it is the frame.** It is the formal statement of the owner's
  "incrementality falls out of data dependencies"
  (`notes/architecture.md` §3.e1).

3.3 **Recorded reads for the long edges, at context grain.** status:
uncertain, decided by X12.
- **The idea.** Static edges follow the owned tree. Only the few couplings
  that leave it record their reads dynamically, per context: floats
  crossing blocks, counters read far ahead, an absolute box's containing
  block.
- **Who lands here.** Two notes do:
  - `notes/architecture.md` §3.b: "where I would land";
  - `notes/theory.md` §4.2.
- **Related idea.** LayoutNG-style validity predicates are related
  (`notes/engines.md` §2.1.3, recalled).

3.4 **Traced dependency graphs per box (self-adjusting computation,
Adapton).** status: unlikely.
- **Cost.** At box grain the budget's arithmetic excludes them, but that
  arithmetic rests on a recalled per-edge constant.
- **Representation.** Whitefoot stores no references, which excludes the
  thunk graphs they rely on.
- **What survives.** Demand-driven evaluation (4.4) and recorded reads at
  coarse grain (3.3).

3.5 **Differential and timely dataflow.**
- **Selector matching.** status: uncertain. A sheet change becomes a delta
  over (rule, element) pairs.
- **Elsewhere.** status: hard.

3.6 **Derivatives of functions (incremental λ-calculus).**
- **In general.** status: uncertain.
- **One function's delta API.** status: promising. Re-breaking a
  paragraph from the changed line onward, as LayoutNG's line reuse does
  (recalled), is the useful special case.

3.7 **Signals and reactive frameworks.** status: unlikely at renderer
scale. A subscriber list per value costs the per-box bookkeeping that 3.4's
arithmetic weighs against. It stays a mental model for the graph of stages.

3.8 **Monoid summary trees.** status: promising for associative folds.
- **The idea.** A sequence kept as a balanced tree whose nodes store an
  associative summary of their range, as Zed's SumTree does for text
  (recalled). Updates and prefix queries cost O(log n), and a parallel scan
  computes the same fold.
- **What it would unify.** Every chain in document order whose fold is
  associative (1.6), and the flat-context offsets of 1.3.
- **Where it is hard.** Folds that are not plainly associative: margin
  collapsing, `clear`, floats.

3.9 **Edit lists as stage interfaces.** Each stage's input and output is
a list of edits:
- style emits "these nodes' groups changed";
- the box tree emits "these pieces were replaced";
- layout emits "these fragments moved by δ";
- paint emits chunk operations.

Zed's display map propagates edits through its layers this way (recalled,
`notes/engines.md` §5.5). An empty list makes the no-change frame free
without scanning versions.
- **Sequence-shaped stages (text, box tree, paint order).** status:
  promising.
- **Layout.** status: hard. Its output delta is not a function of its
  input delta alone.

3.10 **Reconciliation at the output boundary.** status: established, in
React and in WebRender's interning (recalled). Compare the new chunk list
with the old by identity and hash, and send only the difference.

3.11 **Persistence.**
- **Pointer sharing:** hash-consed DAGs, HAMTs, ropes with shared nodes.
  status: dead end in Whitefoot. Single-owner boxes and no stored
  references cannot represent shared nodes.
- **Versioned slots:** fat-node persistence, like MVCC. status:
  promising, unmeasured.
  - **The idea.** A `Slots` whose element holds (version, value) pairs. A
    reader at version v takes the last pair at or below v, so no reference
    is stored (`notes/architecture.md` §3.e2).
  - **What it would provide:** the document snapshot frame pipelining needs
    (4.5), the old state style invalidation compares against, and the old
    bounds damage needs (7.2).
  - **Its cost:** a version list per slot and a reclamation sweep.

### 4. Execution models: concurrency across stage boundaries

From `notes/architecture.md` §3 and `notes/theory.md` §2.4–2.5:

4.1 **One task per subtree, running style, layout and paint together.**
- **Scattered edits.** status: promising.
  - Sibling subtrees run concurrently, so stages overlap across contexts
    without a scheduler.
  - Whitefoot proves this without new facts: recursion over `children[i]`
    is an affine element write (PAR-2), and the rows are per context.
- **One local edit.** status: no gain from cross-stage overlap.
  - With one dirty context, style, layout and paint form a sequential
    chain, so latency is the chain's length.
  - If writing to the shell waits, chunks ship at the frame's end
    (`notes/architecture.md` §3.a).
  - The gain over staged passes is overlap across siblings.
- **Cutoffs.** These compare data the code already stores (`Space`,
  interned ids, `intrinsic_known`), under the attribute-grammar discipline
  of 3.2.

4.2 **A dataflow graph of keyed nodes.** status: hard in its general form.
- **The proof cost.** Writing results at dirty indices needs a
  distinctness fact derived each frame and an `apart` certificate. Shape D
  showed both are possible, at a proof cost.
- **The hybrid.** 4.1 plus recorded reads for the long edges (3.3) sits
  between 4.1 and this model.

4.3 **Staged passes over a dirty frontier.** status: established; this is
Blink's lifecycle. It is the control the others must beat (X6).

4.4 **Demand-driven: pull from the frame.** status: uncertain.
- **Where it is strong.** For paint, and for very long documents, where
  only the viewport and a margin around it need painting.
- **Where it is weak.** For layout, whose positions depend on everything
  before them.
- **What it decides.** Whole-page paint with culling in the shell, or
  viewport-dependent paint on request (`notes/raster.md` §6, D4b), decides
  whether the shell needs a channel back to the renderer (X9).

4.5 **Spawned stage contexts passing owned deltas.** status: uncertain.
- **The model.** Stages run as spawned contexts and pass owned edit
  lists (3.9) through shared queues. This is the cross-stage form
  Whitefoot's rules admit: a spawn takes values only ([WAIT-3])
  (`notes/theory.md` §2.5).
- **What decides it.** It overlaps stages for a stream of edits, not for
  one. Experiment X7 decides whether that beats the sequential chain.

4.6 **Progressive and anytime delivery for whole-page changes.** status:
promising for loading and for whole-page edits; needs a design.
- **The problem.** A container-width or root font-size change costs about
  50 frames, and parallelism cannot reach 16 ms from 0.8 s.
- **The options.**
  - viewport-first layout with estimates (`notes/architecture.md` §3.d,
    E7);
  - priority lanes and interruptible work, as React's Fiber does
    (recalled);
  - a frame-miss policy (`notes/raster.md` §3.4).

4.7 **Frame pipelining and optimistic speculation across stages.**
- **Frame pipelining.** status: a fallback only, by the owner's ruling
  (see The owner's direction). Overlapping frames needs a snapshot of the
  document while script runs, which versioned slots (3.11) could provide,
  and successive frames' edits overlap fully only where their dirty sets
  are disjoint (X15).
- **Speculation.** status: promising only where a misprediction is found
  early and fixed locally, as floats were (`notes/architecture.md`
  §3.e2–e3).

4.8 **Script's synchronous queries as path flushes.** status: uncertain.
- **The problem.** `offsetWidth` after a mutation forces layout.
  Flushing only the path from the queried box to the root is a pull, the
  reverse of 4.1's push.
- **The answer.** No engine is known to do less than a stage flush
  (recalled, `notes/architecture.md` §5, invariant 9). It needs script, so
  it is design-only today, but the execution model should not foreclose it.

4.9 **Layout on the GPU.**
- **The whole stage.** status: unlikely. Shaping, floats and tables are
  data-dependent control flow with no GPU form. Meyerovich's GPU layout
  work, recalled and unchecked, ran attribute-grammar schedules on the
  GPU.
- **Placement in flat contexts and glyph positioning.** status:
  uncertain. Both are prefix sums, which the GPU scans well. It is decided
  by whether the CPU prefix scan (3.8) is ever the bottleneck.

### 5. Whitefoot: what it gives, and what it would need

From `notes/theory.md` §2 and `notes/architecture.md` §6:

5.1 **The effect row as a memoization key.**
- **Complete in places.** status: established by the spec.
  - Rows are checked both ways ([EFF-2]), and there are no globals or
    function values ([FN-5]). Host outcomes come only through waiting
    calls.
  - So the places a function can read are exactly its row and its
    by-value arguments.
- **Complete in values.** status: dead end as stated. Nothing records
  whether a read place changed, so the claim in `design/pipeline.md` that
  "the compiler then proves the memoization key complete" holds for places,
  not for versions.
- **Where the claim also fails.** For the DOM arena, read through
  `&Document`, the row names the whole arena (`notes/architecture.md`
  §1.3).
- **Deduplication.** [EFF-3]'s licence to deduplicate calls needs a pure
  function that allocates nothing, which no stage result is.
- **Practice that follows: pass the inputs, not the world.** Pass
  `&styles^.groups[k]` rather than `&styles`, so the row names the
  element's path.
- **The design tree.** It should record the decision's actual reach. This
  is the one design-tree matter the research raises (Open questions).

5.2 **Equality for cutoff.** status: hard, with a route. Whitefoot has no
aggregate equality. The routes:
- the integer and interned-id comparisons the cheap cutoffs need;
- an interface-supplied `eq`;
- a derived structural equality, as a future language decision.

5.3 **Versions the compiler maintains.** status: uncertain, decided by
X11.
- **The mechanism.** A `tracked` storage root whose version the compiler
  bumps at every write its rows already know, and a `memo fn` that reruns
  when the version of a path it reads moved.
- **First step.** Ticks written as library code come first. X11 tests
  whether the byte-identity oracle catches a forgotten bump. The language
  mechanism needs that ground and a decision card.

5.4 **Parallel work over a dirty set.** Three shapes:
- **Recursion from the root.** status: promising.
  - It descends only where a subtree's maximum tick moved, needs no
    certificate, and its frontier is an antichain by construction.
  - Its cost is O(dirty × depth × width) for the tick checks. Widths are
    3,545 on html5's `body`, 297 on apollo11 and 122 on ecma262, so tens of
    microseconds.
- **A flat loop over a dirty list.** status: hard. It needs the per-frame
  distinctness fact (4.2).
- **Spineless traversal.** status: uncertain. A priority queue over dirty
  nodes with order maintenance, instead of walking the spine from the root
  ("Spineless Traversal for Layout Invalidation", arXiv 2411.10659; cited
  by `notes/architecture.md` §3.e, not re-read).

5.5 **Concurrency across stages.** status: hard as scheduled concurrency,
promising as emergent concurrency (4.1).
- **Spawns.** These take values only ([WAIT-3]), so stages cannot share a
  reference; 4.5 is the scheduled form.
- **Waiting writes.** If writing to the shell's shared memory waits,
  chunks are batched at the frame's end.

5.6 **Range facts as a property of a container.** status: promising;
already in `docs/todo.md`. A `Slots` whose invariant says its entries are
distinct, usable by every loop over it without deriving the fact again.

### 6. The paint boundary

`notes/architecture.md` §8, `notes/engines.md` §3 and §7.4 and
`notes/raster.md` §6 converge on these properties. Each holds under either
answer to 4.4.

6.1 **Order and properties apart from content.** status: established in
the separation, promising in this form.
- **Chunks.** Each chunk is in its context's coordinates, with a stable
  identity and a content hash.
- **Stacking.** A stacking context is an order list of chunk references.
- **Properties.** Transform, clip, effect and scroll live in a property
  tree, so a change to one rewrites one node and no content.
- **Precedent.** Blink's paint chunks and property trees establish the
  separation; their layerization is the heuristic part (`notes/engines.md`
  §3.2–3.3).

6.2 **Deltas to the shell.** status: promising.
- **What is sent.** Only changed chunks, order lists and property nodes,
  through shared memory with epoch acknowledgement.
- **What the CPU measured, on a synthetic scene of 250,000 chunks.** The
  scene size is an assumption (`notes/raster.md` §0).
  - The cost of a reflow is the bytes crossing the boundary.
  - A spatial index answers a viewport query in under 1 µs.
  - Rewriting 245,000 absolute positions takes 0.2 ms, against 0.04 µs on
    a tree of relative offsets.

6.3 **Facts in, policy out (Q65).** status: the owner's ruling; the
invariant's exception is open (Q66); the contents of the contract are
promising, not built.
- **The rule.** The renderer states facts about the page and never decides
  how to draw it. The shell decides, per platform and by measured cost,
  how to draw, which pixels to cache, how to scroll and how to present.
  Chrome decides layerization in paint from hints such as `will-change`
  and overlap; this rule keeps platform policy out of the renderer.
- **The invariant (Q66, open).** At rest, every combination of shell
  policies produces the pixels a full redraw of the scene produces, so a
  policy or a threshold can change without risking a wrong pixel. The one
  proposed exception: a subtree cached as a texture (7.6) while a
  transform animation scales it, rotates it or moves it by a fraction of a
  pixel is resampled, and the first frame after the animation ends is
  exact again. Choices such as subpixel antialiasing for text follow facts
  the renderer states (opaque areas), so a full redraw makes the same
  choice. X14, extended to CPU models of the policies, checks frames at
  rest.
- **Facts, not hints.** "This transform node is driven by a CSS
  animation" is a fact; "this element will change" is a hint. Stability
  and cost that the renderer cannot state, the shell observes across
  frames and measures.
- **What the shell needs, from the discussion of 7:**

  | Fact | What the shell does with it |
  |---|---|
  | each chunk's stable identity and content hash | finds what changed |
  | bounds including effect outsets | computes damage |
  | the transform, scroll, clip and effect nodes each chunk hangs from | scrolls and animates by rewriting nodes, not chunks |
  | paint order | redraws in order; tells whether anything above a subtree overlaps it, which decides whether that subtree can be an OS layer (7.6) |
  | each chunk's opaque area | skips what is fully covered; decides whether text may use subpixel antialiasing |
  | whether a chunk reads its backdrop (`backdrop-filter`, blend modes) | widens damage |
  | per scroll root, the content that moves rigidly with it; where fixed and sticky content hangs | prepaints strips and moves them (7.5) |
  | animation descriptions: node, property, values, duration, easing | runs the animation itself; knows only a property changes |
  | per delta, whether a chunk changed in content or only in geometry | decides whether a subtree may be cached as a texture (7.6) |
  | cost estimates: glyph count, blur radius, path complexity | chooses what to cache |
  | external surfaces: video, canvas | hands them to hardware planes (7.8) |
  | viewport priority, and which deltas are urgent | orders prepainting and background work (X16) |

### 7. From changed content to pixels

From `notes/raster.md`, `notes/gpu2d.md`, `notes/webrender.md` and
`notes/engines.md` §4 and §6. This container has no GPU, so every GPU
figure here is cited or derived. Derived byte counts are approximate.
They assume 4 bytes per pixel, a 3840×2160 screen (33 MB per full frame),
no framebuffer compression, and an OS compositor that reads and writes
each window pixel once. Compression and tile-based GPUs lower them;
Mozilla's own model counts three passes of a screenful per compositing
layer (`notes/webrender.md` §2.3), which raises the compositor's share.
Only hardware settles them (X10).

7.1 **Redrawing the whole scene on the GPU every frame.** status:
established as a control.
- **Who does it.** Zed's GPUI, Vello-based Masonry and early WebRender
  (`notes/webrender.md` §1 and §6).
- **Its limit.** Power and memory bandwidth on integrated GPUs at high
  resolution, rather than frame time on a discrete GPU. Mozilla found
  energy "strongly correlated with the amount of pixels that are
  manipulated" (`notes/webrender.md` §2.2). Zed spends 1 to 2.7 ms of GPU
  per frame at 120 Hz presenting frames in which nothing changed (Zed
  issue 32588, `notes/webrender.md` §6.1).

7.2 **Redrawing exactly the damaged region from a retained scene.**
status: promising; the main line.
- **The mechanism.** The damage is the union of the old and new bounds of
  the changed chunks. Scissor to it, find the intersecting chunks with a
  spatial index, and redraw only those, in paint order. A frame with no
  damage draws and presents nothing.
- **Precedent.** WebRender's redraw grain is the dirty rectangle inside a
  tile, not the tile (`notes/webrender.md` §0, W5).

7.3 **Knowing what the buffer holds.** Redrawing only the damage needs a
buffer whose contents are known.
- **wgpu's surface cannot provide it.**
  - status: established from wgpu 30's source. Its DX12 backend calls
    `Present` rather than `Present1`, its Metal backend has no damage path,
    and damage-aware presentation is an open pull request for Vulkan and
    EGL only (`notes/gpu2d.md` §4.3).
  - status: uncertain. That its public API exposes no buffer age or
    swapchain image index is the survey's reading of `SurfaceTexture`, not
    a search of every path; the open question on wgpu below decides it.
- **A persistent full-page target copied to the swapchain.** status: dead
  end, derived. The copy reads and writes a full frame every frame, 66 MB
  even for a caret blink, more than a plain full redraw writes (33 MB).
  The owner rejected it in conversation.
- **Buffers the shell owns, handed to the OS compositor.** status:
  promising; the main path. The shell knows which frame each buffer last
  held, so it redraws the damage of the frames that buffer missed plus
  this frame's, from vectors; copying those regions from another buffer
  is an option only for content expensive to redraw. wgpu may still
  record the drawing; the presentation is the shell's own:
  - macOS: IOSurfaces as the contents of CALayers;
  - Windows: DirectComposition surfaces, or a flip-model swap chain with
    `Present1`;
  - Wayland: the shell's own buffers with `damage_buffer`;
  - Android: EGL buffer age.

7.4 **Telling the OS compositor what changed.** Without it, the OS
recomposites the whole window at every present (`notes/webrender.md` I4).
- **Where a damage interface exists.** status: established from the
  specifications for DXGI dirty rectangles, Wayland `damage_buffer` (Mesa
  forwards Vulkan's incremental present to it) and EGL partial update
  (`notes/gpu2d.md` §4.1). DirectComposition surfaces taking an update
  rectangle when drawing begins is recalled, not read.
- **macOS.** status: established for 2019, not rechecked since; X18 checks
  it. In Mozilla's words, "there are no APIs for partial updates of
  CAMetalLayers either, so you'd need to implement a solution with smaller
  layers" (`notes/webrender.md` I4). Firefox ships that: the window split
  into tiles, each a CALayer with its own IOSurfaces (`notes/webrender.md`
  §2.3). That the OS then recomposites only the tiles whose contents
  changed is inferred from that design. These tiles are the presentation
  unit, not the invalidation unit: a change redraws its damage inside the
  tile.
- **Tile size.** status: uncertain, decided by X18. A small change costs
  the redraw of the damage plus the OS's recompositing of its tile, about
  twice the tile's bytes (derived):

  | Tile | Per small change |
  |---|---:|
  | 256×256 | 0.5 MB |
  | 512×512 | 2 MB |
  | 1024×512 | 4 MB |
  | one layer for the window | 66 MB |

  The table assumes the OS reads and writes a recomposited tile once.
  Smaller tiles mean more layers: a 4K viewport at 256×256 is 135 tiles
  before prepainting, and each needs at least two buffers so that the shell
  never draws into one the OS is reading (derived). WebRender uses
  1024×512 on macOS and 512×512 on Windows (`notes/webrender.md` §3.2).
- **What others measured.** status: measured by them, not reproduced.
  Firefox 70 on macOS, with its own IOSurfaces, partial redraw and CALayer
  tiles together, went from 16.4 W to 9.4 W scrolling and from 7.4 W to
  1.6 W on an idle Google Docs page; Mozilla credits partial redraw with
  "most of the power savings" (`notes/webrender.md` §2.3). A blinking
  caret in a blank Google document went from about 30 W to 7 W in
  BZ 1429522 (`notes/gpu2d.md` §5).
  Firefox's Windows tile compositor once raised power, 20 W against 15.5 W
  on an Iris 550, until tiles stopped being invalidated when clip
  rectangles moved under scrolling (BZ 1602803) (`notes/gpu2d.md` §5).

7.5 **Scrolling.** A scroll changes every pixel of the viewport, so every
method writes a full frame at least once; they differ in what else they
touch. Per frame, windowed, derived:

| Method | The shell | The OS compositor | Total |
|---|---|---|---:|
| A: redraw the viewport from vectors | write 33 MB | read and write 66 MB | about 100 MB |
| B: cached tiles composited by the shell | read and write 66 MB | read and write 66 MB | about 133 MB |
| C: prepainted strips as OS layers, moved by one container transform | prepainting, amortized | read and write 66 MB | about 66 MB plus prepainting |

- **A.** status: promising as the default. For text and rectangles its
  shading is near the floor. WebRender's team found redrawing everything
  per scroll frame "too much" on most GPUs for a pathological page, a CSS
  reproduction of an oil painting, with no numbers; no source isolates
  plain text and rectangles as a problem (`notes/webrender.md` §2.1, §8).
- **B.** status: dead end, derived: it is the most traffic of the three.
- **C.** status: promising where the OS takes several surfaces. Strips
  span the viewport's width and form a ring; one that scrolls out is
  reused at the other end. The prepainted margin is the fastest fling's
  speed times the time to paint a strip, and prepainting is low-priority
  work (the owner's third priority).
- **Fullscreen reverses the order.** With direct scanout the OS composites
  nothing, so A costs 33 MB and C stays near 66 MB, since many layers
  likely prevent direct scanout (recalled).
- **What may go into strips.** Only content that moves rigidly with that
  scroll root. Fixed and sticky content, and other scroll roots, are drawn
  above each frame or get their own strips. Where paint order interleaves
  them, as a fixed header between two scrolled boxes, the interleaved part
  is drawn each frame rather than split into more layers: this is the case
  from which Chrome's overlap testing and squashing grew. How often it
  occurs is X17.
- **Scroll offsets snap to device pixels**, so strip pixels are never
  resampled and text stays sharp.

7.6 **Animated subtrees.** status: promising.
- **The problem.** A large subtree that moves or rotates damages its old
  and new bounds every frame, across many tiles.
- **What a texture saves.** Drawing the subtree and what it uncovers, not
  the recompositing of the swept region, which changes every frame
  anyway. It pays where the subtree is expensive to draw; a plain
  rectangle redraws as fast as it composites.
- **The rule.** Cache the subtree as a texture while a property node above
  it animates, its content stays the same and its draw cost passes a
  threshold. The shell knows the first two: it runs CSS animations itself,
  and for script-driven changes a run of deltas that change geometry only
  shows it (WebRender waits 15 stable frames before promoting a video
  surface, `notes/webrender.md` §3.5). Release the texture when the
  animation ends or the content changes.
- **Where the texture goes.** To an OS layer if nothing above it in paint
  order overlaps it, so the shell draws nothing per frame; otherwise the
  shell composites it into the affected tiles itself, which is always
  correct. Overlap therefore never forces more layers.
- **Costs.** Rotation and scaling resample the texture and soften text;
  scaled content is redrawn at its final scale when the animation ends.
  This is the same mechanism as the offscreen target a group opacity
  needs.

7.7 **Tiles and layers as the unit of invalidation.** status: dead end
for this goal. They are a hand-placed partition, so a change repaints
whatever its tile holds; WebRender's over-invalidation under scrolling
(BZ 1602803) is this failure (`notes/webrender.md` W3).

7.8 **Video and canvas.** status: established. Content already in a GPU
buffer goes to an OS surface or hardware plane rather than through the
frame: with DirectComposition and compositor surfaces, WebRender on a
Surface Go played video at about 10 percent GPU and 1.8 to 2 W, against 30
percent and 3.3 W without WebRender (BZ 1569767, measured by them,
`notes/webrender.md` §2.4).

7.9 **Text.** status: uncertain. Glyph drawing is expected to dominate on
text-heavy pages; that is derived from an assumed scene, not measured. A
glyph atlas, Slug-style curve rendering (its patent was dedicated to the
public domain in 2026) and Vello's compute rasterization need hardware to
compare (X10, `notes/gpu2d.md` §3).

7.10 **A software damage rasterizer in Whitefoot.** status: promising, as
a proposal for the owner.
- **What it provides.** Writes to disjoint rows are provable, and it would
  serve as a pixel-exact test oracle (6.3's invariant), a headless target
  and a fallback.
- **What it does not do.** It does not replace the shell's GPU path
  (`notes/raster.md` §7).

7.11 **What WebRender's history adds.** status: established from Mozilla's
sources (`notes/webrender.md` §0, §7). WebRender kept redrawing from
primitives; it added a pixel cache for scrolling and static content, a
per-frame diff because Gecko sends whole display lists, sub-tile dirty
rectangles, and OS compositor surfaces. With deltas and stable identities
(6.2) the diff is unnecessary. The rest maps to 7.3 to 7.8: never touch
unchanged pixels, tell the OS what changed, cache only expensive effect
outputs, and hand video to the OS.

### 8. The oracle for every incremental step

status: established here, extended.
- **The rule.** Snowghost requires the sequential and `--par` builds to
  give byte-identical dumps. An incremental run is held to the same rule:
  after a history of edits, its dumps must be byte-identical to a full run
  on the final document.
- **What makes it cheap.** The existing dumps print values (computed
  values, rectangles), not interned ids or slot indices, so it costs no
  design. Any new dump must keep that property.

### 9. What remains hard everywhere

From `notes/engines.md` §7.3:

- **Real coupling stays real.** The couplings of 1.4 to 1.6 stay
  non-local whatever the representation.
- **Finding what to recheck.** Its cost grows with depth times level
  width unless sequences become summary trees (3.8) or traversal avoids the
  spine (5.4).
- **Comparing a key.** It can cost more than recomputing a cheap node.

## Experiments

Each criterion is written before the experiment runs, and each can fail.

| Id | Question | Needs | Criterion |
|---|---|---|---|
| X1 | How local are real edits in Snowghost's own stages, at each unit of 2.1? | two full runs around a scripted edit, and a diff tool that compares group values, not ids, and aligns units by a stable marker | context plus paragraph is the layout unit if fewer than 1 percent of paragraphs change lines for word edits; otherwise a finer unit is needed. Per key design, the recomputed set over the minimal set must stay under 3 (`notes/architecture.md` §1.1, `notes/engines.md` E1) |
| X2 | How is per-node style stored under stable identity: renumbering, a certified scatter, `Segments`, or order labels? | small drivers at ecma262's element count | for one insertion at the top, the fastest under 1 ms wins; a certificate proof over 2 s per loop is reported to Whitefoot |
| X3 | Which offset structure: context-relative, sibling-anchored, summary tree, or prefix sums? | the census's edit script on Snowghost's layout output | over the census's distribution of translation roots, adopt the tree or prefix sums where the context-relative scheme's p90 rewrite count exceeds theirs by more than the per-write cost ratio. It can pass on ecma262 and fail on html5 |
| X4 | Do a paragraph's line breaks hold over a range of widths? | paragraph output swept over inline size | width-keyed memoization pays if more than half of the paragraphs keep their breaks across a 10 px resize; otherwise container-width edits get parallelism only |
| X5 | Incremental layout on the owned context tree (4.1), with cutoffs on `Space` and paragraph keys | X1, X2; the current stage | a one-paragraph edit under 1 ms at four workers and under 1/100 of the full stage; an `html` font-size change no worse than 1.2 times a full run; a full build with bookkeeping within 5 percent of today's; byte-identical to a full run (8) |
| X6 | 4.1 against staged passes (4.3) | X5 and a staged driver | measured twice, on one local edit (latency to the first chunk) and on 100 scattered edits. 4.1 is the model if it wins the scattered case by more than 20 percent without losing the local one |
| X7 | A pipeline of spawned stages (4.5) against the sequential chain | X5 and edit lists | the pipeline is worth it if, for a stream of edits, latency per edit is at most 1/1.3 of the chain's (`notes/theory.md` E5) |
| X8 | Edits the census missed: parser appends and font arrival | the existing drivers | an append re-lays out only what follows, within 2 times the appended content's own cost; a font arrival costs no more than the text preparation of the paragraphs using it |
| X9 | Whole-page paint with culling in the shell, or viewport-dependent paint | paint, shell | viewport-dependent paint is adopted only if the whole-page list exceeds the shared-memory budget or delays the first frame by more than one frame on ecma262 |
| X10 | Pixels on a GPU machine, at 1080p and 4K, windowed and fullscreen: full redraw against damage redraw into shell-owned buffers with damage reported to the OS (7.3, 7.4); scrolling by A against C (7.5); a large animated subtree redrawn, cached and composited by the shell, and cached as an OS layer, in plain and text-and-image variants (7.6); text approaches (7.9) | a GPU host, a scene dump of the three pages, edit scripts (`notes/gpu2d.md` §7) | damage-limited rendering is justified if full redraw exceeds 25 percent of the frame budget or damage saves more than 20 percent of system energy; C replaces A where it saves more than 20 percent of energy or A misses the frame budget; an animated subtree is cached where caching saves more than 20 percent; a glyph atlas stays the default if it beats the others by more than 20 percent |
| X11 | Does the oracle catch a forgotten version bump? | ticks as library code, X5 | delete one bump deliberately and run the edit script. If the oracle misses it, 5.3's language mechanism has its first ground |
| X12 | The cost of recording reads and validating versions | X5 with recording | a no-change frame under 0.5 ms; recorded reads at context grain within 5 percent of the full build, or 3.3 is out |
| X13 | An editing session | X5 | 100 to 1,000 edits typed at one point and scattered, the oracle checked after every prefix; no growth of interning tables or arenas beyond the content added |
| X14 | A CPU oracle for the shell's policies | a software rasterizer of chunks (7.10) and CPU models of the policies | damage-scissored and age-tracked redraws, strips and cached subtrees at rest byte-identical to a full redraw (6.3); each deliberate breakage (missing spread, omitted overlap, wrong buffer age) fails once (`notes/raster.md` X1) |
| X15 | How often do successive frames' edits touch disjoint parts of the page? | X1's dirty sets over edit streams | frame pipelining (4.7) is worth reopening only if most successive edits in a typing or scattered-edit stream have disjoint dirty sets in every stage |
| X16 | What fraction of an edit's recomputation lies in or near the viewport? | X1's dirty sets and the layout rectangles | viewport-first scheduling pays if, for edits costing more than one frame, the median share of dirty units within one viewport height of the viewport is under one half |
| X17 | How often does paint order interleave a scroll root's content with content that does not scroll with it? | a sample of real pages in Chromium, scrolled | the one-rule strip placement of 7.5 stands if the interleaved part needs drawing in under 5 percent of viewport frames over the sample; otherwise strips need splitting by paint order |
| X18 | macOS presentation: does one `CAMetalLayer` recomposite the whole layer at every present, and which tile size costs least? | a Mac, Quartz Debug's update flashing, `powermetrics` | tiles are used on macOS if they save more than 20 percent of energy over one layer on a blinking caret and on typing; the tile size with the least energy over caret, typing and scrolling at the Mac's native resolution is chosen |

**Where each can run.**
- In this container with the existing stages: X1 to X4, X8, X14 to X16.
- In Chromium: X17.
- Needing an incremental layout prototype: X5 to X7 and X11 to X13.
- Needing paint and real hardware: X9, X10 and X18.

## Leads, and what each would foreclose

These are leads for discussion, not decisions. Each says what choosing it
early would close off.

- **Measure first: X1, X3, X4, X8, X12.** All five notes agree on this.
  It closes nothing.
- **4.1 as the execution model, with recorded reads (3.3) for the long
  edges.** This is `notes/architecture.md`'s landing. `notes/theory.md`
  proposes the spawned pipeline (4.5) instead, and the others are silent.
  Choosing it before X6 and X7 would foreclose 4.5, spineless traversal
  (5.4) and edit lists (3.9) as the main interface.
- **Fix the paint boundary's properties (6.1) and the contract of facts
  (6.3) before writing paint.** The owner ruled the boundary (Q65); the
  contract's contents hold under whole-page and viewport-dependent paint
  alike. Choosing a shell policy before X10 and X18 would foreclose them.
- **Correct the record in `design/pipeline.md`** about what the compiler
  proves (5.1). This is a design-tree change for the owner.

## Open questions

- **The memoization decision.** Should `design/pipeline.md`'s decision say
  that the compiler proves a key complete in places, not in versions, and
  not across the DOM arena (5.1)?
- **Counters and quotes.** How do they stay incremental once one walk
  resolves them (Q63)? By checkpoints, or by summary trees (3.8)?
- **Snapshots.** What does a document snapshot look like once script
  exists? Are versioned slots (3.11) enough?
- **Stable identities over time.** How do the interning tables and the text
  arena reclaim space under stable identities over many frames?
- **`Segments`.** Can it carry a distinctness fact per segment?
- **The shell channel.** Is viewport-dependent paint worth a channel from
  the shell back to the renderer (4.4, X9)?
- **wgpu's surface.** Does any wgpu or wgpu-hal path expose the swapchain
  image index or age (`notes/gpu2d.md` §7.0)? If not, the shell presents
  through each platform's own interface (7.3).
- **Display process.** `design/processes.md` builds the shell first on
  libraries such as Skia for rasterization and compositing. Which library
  draws into shell-owned buffers is for X10 to decide.
- **Reflecting rows.** Can an effect row, or a finer read set, be reflected
  into data to derive invalidation tables (1.1)?
