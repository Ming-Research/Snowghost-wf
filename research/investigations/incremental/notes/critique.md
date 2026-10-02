# Critique of `research/investigations/incremental/DESIGN.md` and its five notes

Repository `/home/user/snowghost`, branch `research/incremental`, head `3ed7078`.
Read: `DESIGN.md`, `notes/{theory,architecture,engines,fanout,raster}.md`,
`design/pipeline.md`, `design/pipeline/layout.md`, the census aggregates under
`census/`, `research/investigations/concurrency/DESIGN.md` (open question,
Shape D) and `build/research/concurrency/layout-results.txt`. No file was
edited. Line numbers are of the files at this head. Where I recall a system
from memory I say so; such a recollection is a lead to verify, not evidence.

The owner asked for a complete tree of approaches, each marked, not a plan.
Judged against that, the synthesis is a good map of one approach family
(keys + ticks + owned-tree recursion + chunk deltas) with the alternatives
compressed to one-line "dead end" or "hard" verdicts, several of them on
evidence the notes themselves do not support. The most consequential
findings are in sections 2 and 3; section 1 lists what no note explored.

---

## 1. Branches missing entirely, or present in a note and dropped

### 1a. Missing from every note

**M1. Monoid summary trees as a general family for every document-order
chain.** `DESIGN.md:154-160` lists "a balanced tree of offsets, as Zed's
SumTree" for block offsets only, and `1.6` (`DESIGN.md:174-191`) treats
counters, `:nth-*`, inherited values, the margin strut and the running
height as chains to *checkpoint*. A checkpoint is a prefix fold evaluated
sequentially; a summary tree is the same fold with O(log n) update and
query, and it is also the structure `fanout.md:298-300` asks for counters
("storing them as a prefix-sum structure over the list") and
`engines.md:7.2(6)` ranks promising. Nothing in the tree states the family
once: *every* document-order coupling (heights, counters, quotes, sibling
positions, `:nth-last-*` by a reversed summary, scroll extent per
`fanout.md:303-306`) is a fold over a sequence with an associative summary,
and the open question is which folds are associative. Why it matters: it
unifies 1.3, 1.6 and the scroll-extent problem under one structure with a
proved cost, and it is the structure a parallel scan ([PAR-2] `imax`-style
accumulators) already needs. Provisional status: **promising** for heights,
counters, `:nth-child`, scroll extent; **hard** where the fold is not
associative (margin collapsing, `clear`, floats, `:nth-last-*` with
insertions), which `architecture.md:283-285` and `engines.md:159` already
note but only for offsets.

**M2. Delta-typed stage interfaces end to end.** The owner's phrase is
"one local change flows through style, layout, paint and presentation"
(`DESIGN.md:17-18`). In the tree a change flows as *dirtiness* (ticks)
until paint, where it becomes a *delta* (6.2). The alternative is that each
stage's input and output are edit lists: style emits "these nodes' group
ids changed", the box tree emits "these pieces were replaced", layout emits
"these fragments moved by δ", paint emits chunk ops. `engines.md:285`
describes Zed's display map doing exactly this ("an edit is propagated by
applying an `Edit` list through each layer, O(edits × log N)"), and
`theory.md:1.3-1.4` has the theory (differential dataflow, change
structures) but applies it only to selector matching and line breaking.
Why it matters: an edit-list interface is what makes the no-change frame
free (an empty list) without any tick scan, and it is what a spawned
pipeline of stage contexts (D2) would carry. Provisional status:
**promising** for the sequence-shaped stages (text, box tree, paint
order), **hard** for layout, where the output delta must be computed and
is not a function of the input delta alone.

**M3. Edit classes the census never applied, and no experiment covers.**
The census (`fanout.md:58-67`) applies single random edits to a loaded,
static page. The incremental cases a browser actually meets are:
- *parser appends during load*: the document grows at the end while
  earlier content is already laid out; the most common incremental case
  and the one where "the change affects only what follows" is literally
  true; also the natural first-pixel path;
- *font and image arrival*: a web font loading re-shapes every paragraph
  using it (full text preparation, 60-67 percent of layout); an image's
  size arriving resizes one box and pushes everything after it. These are
  listed as "hidden inputs" (`DESIGN.md:250-256`) but never as edit kinds;
- *layout-property animations and transitions* (height, width, margin,
  font-size at 60-240 Hz): the same key changes every frame, so the
  bookkeeping floor and the 1.4 "full-subtree" cost are paid per frame;
- *`:hover`, focus, selection and caret*: the most frequent style edits,
  mostly paint-only.
Why it matters: X1-X6 and the census all answer "how local is a random
single edit"; none answers "how does the pipeline behave under the edits a
page actually receives". Provisional status: **measurable now** (append
and font classes can be scripted against the existing drivers);
animations **hard** by 1.4's own argument.

**M4. Progressive, anytime and frame-miss behaviour for the whole-page
case.** The budget (`DESIGN.md:61-66`) says a whole-page change costs about
50 frames; the question says such a change "still recomputes the whole
page". Nothing in the tree says what the user sees during those 50 frames.
`architecture.md:3.d` (viewport-first estimated layout, E7) and
`raster.md:127` ("Frame-miss policy ... Status: uncertain, needs a design")
both raise it; DESIGN 4.4 keeps only the demand-driven paint half and
drops E7 from the experiment table. Priority-driven and interruptible work
(React Fiber lanes, `engines.md:271`) is the toolkit-side version. Why it
matters: this is where a container-width or root font-size change meets
the frame budget, and 1.4's "speed has to come from parallelism" cannot
reach 16 ms from 0.8 s at four workers. Provisional status: **promising**
for loading and whole-page edits; needs a design before an experiment.

**M5. Stratification instead of "cycles no engine solves".**
`DESIGN.md:487-488` lists container queries and `:has()` under "what no
engine solves". CSS itself stratifies: a container query requires
containment, which cuts the edge from the container's own layout to its
descendants' style; `:has()` is bounded by Blink's ancestor flags. The
database analogue is stratified evaluation: compute strata in order, with
a fixpoint only inside a stratum. Why it matters: a stratified dependency
graph is still "incrementality from data dependencies"; a cyclic one is
not, and the tree should say which the renderer assumes. Provisional
status: **promising** as the stated rule; **hard** if a fixpoint is ever
needed (termination and cost).

**M6. Compiler-derived invalidation tables from effect rows.** The
Whitefoot-specific idea nowhere stated: Blink's invalidation sets
(`DESIGN.md:134-137`) are hand-derived from the selector grammar;
`engines.md:57` observes "the invalidation set is exactly the 'reads' row
of `match`, computed per rule rather than declared per function". If the
matcher's row names, per rule, which element features it reads, the
reverse index (feature → rules → relation) is derivable from the compiler's
own effect analysis, with no second hand-written table. The same applies
to layout's "which group changes affect layout" (`theory.md:3.1`): it is the
union of the layout functions' rows, not a table. Why it matters: this is
the one place where "the compiler proves the key" turns into "the compiler
*generates* the invalidation data", which is the owner's non-Chrome ideal
in a concrete form. Provisional status: **promising**; needs a spec reading
to decide whether a row can be reflected into data (the spec names rows as
checked, not as values).

**M7. GPU-driven layout.** The owner's list names it; no note covers it
beyond `raster.md:198` (D8, GPU-side scene layout) and
`architecture.md:608` (Meyerovich and Bodík's parallel attribute-grammar
schedule, CPU). Meyerovich's later GPU layout work (from memory:
"Superconductor"; verify) ran attribute-grammar schedules on the GPU. For
CSS the obstacles are shaping (variable-length, table-driven, no GPU
form), floats and tables (data-dependent control flow). The narrow case
that may pay is placement in flat contexts: block-axis positions are a
prefix sum over 3,545 (html5 `body`) to 10^5 sizes, and glyph positioning
within a line is a prefix sum over advances; both are GPU scans, and D8's
node table already puts the offsets on the GPU. Provisional status:
**likely dead end** for the general stage; **uncertain, narrow promise**
for placement and glyph positioning, decided by whether the CPU prefix
scan (M1) is ever the bottleneck.

**M8. Script-facing synchronous queries as path flushes.** `offsetWidth`
and `getBoundingClientRect` after a mutation force a layout. The tree has
no node; `architecture.md:791-794` (invariant 9, "uncertain; no engine does
less than a stage flush, from memory") and `engines.md:387` (Q-b) raise it.
Why it matters: it decides whether layout must be demand-driven along one
path (a pull from the queried box up to the root), which is a different
execution shape from 4.1's push from the root. Provisional status:
**uncertain**; it needs script, so it is design-only today, but the
execution model should not foreclose it.

**M9. Lower-weight vocabulary branches.** (a) Render and frame graphs
from games (Frostbite FrameGraph, from memory): declared per-pass
read/write sets from which the schedule, barriers and resource lifetimes
are derived; the game-industry twin of effect rows for the *stage* graph
of 3.5. (b) Spreadsheet calc chains and dynamic topological-order
maintenance (Pearce-Kelly, from memory) for 4.2's "topological by recorded
edges"; Excel is already in Build Systems à la Carte, which theory cites.
(c) Order-maintenance labels (Dietz-Sleator) as a fourth identity scheme:
present in `architecture.md:150-152` and `raster.md:189` ("order labels
with gaps"), absent from `DESIGN.md:235-239`, which lists three. Status for
all three: **established elsewhere, vocabulary here**.

### 1b. Endorsed by a note, dropped by the synthesis

**D1. Dynamic read-recording for the long edges at context grain.**
`theory.md:762-766`: "this is the one grain where a Salsa-like dependency
list *could* be kept". `architecture.md:522-530`: "A dataflow with static
tree edges and a handful of dynamic ones is model (a) with recorded reads
for the long edges, which is where I would land". `engines.md:124-130`
(validity predicates, "promising ... beyond what any shipped engine does").
`DESIGN.md:271-276` (3.2) reduces the survivors to "demand-driven
evaluation" and `DESIGN.md:163-169` (1.4) keeps width-keyed reuse as a
sub-bullet. Two of three branch authors land on recorded reads for the long
edges; the synthesis omits it.

**D1b. Versioned slots (fat-node persistence, MVCC) as the snapshot and
old-vs-new mechanism.** `DESIGN.md:296-300` (3.7) says persistent
structures are a "dead end in Whitefoot" because storage holds no
references, and `4.5` (`DESIGN.md:341-344`) says snapshots are something
"Whitefoot does not yet offer". Both conflate *pointer sharing* with
*persistence*. A persistent array by the fat-node method is a `Slots` whose
element holds (version, value) pairs; a reader at version v takes the last
pair with version ≤ v. No reference is stored. `architecture.md:630-634`
names exactly this ("copy-on-write arena with versioned slots ... the only
variant that keeps both the identity stability script needs and a read-only
snapshot without copying"), calls it speculation, and the synthesis drops
it as a branch. Why it matters: it supplies (i) the document snapshot frame
pipelining needs (4.5), (ii) the old state Stylo's `ElementSnapshot` needs
for invalidation (`engines.md:61,68(b)`: "in a persistent-data design ...
the snapshot is the previous version, free"), and (iii) old bounds for
damage (`raster.md:120`). Cost: version lists per slot and a reclamation
sweep. Provisional status: **promising; unmeasured**; it interacts with
the reclamation open question (`DESIGN.md:546-548`).

**D2. The pipeline of spawned stage contexts passing owned deltas.**
`theory.md:618-635` describes it as the attainable cross-stage form under
[WAIT-3] and gives it experiment E5 (pipeline vs sequential chain,
criterion 1.3× latency). DESIGN §4 has no such node; `DESIGN.md:389-396`
(5.5) mentions spawns only to say stages "cannot share a reference"; X6
(`DESIGN.md:510`) compares 4.1 with 4.3, a different pair.

**D3. The box tree and text preparation as units.** `architecture.md:83-91`
has seven rows (document, style, box tree, text preparation, layout,
paint, scene). `DESIGN.md:222-226` keeps three (style, layout, paint). Text
preparation is 60-67 percent of the layout stage (`DESIGN.md:145-147`), and
`engines.md:152` argues the box-tree key should be the structure-affecting
style group only so a colour or width change never rebuilds boxes (Servo's
box damage vs empty damage). Dropping these rows drops the two cheapest
cutoffs.

**D4. Spineless traversal.** `architecture.md:613` cites "Spineless
Traversal for Layout Invalidation" (arXiv 2411.10659). `DESIGN.md:490-493`
(§9) lists "the cost of finding what to recheck ... grows with depth times
the width of a level" as something no engine solves. The cited paper is
about exactly that cost (a priority queue over dirty nodes with
order-maintenance instead of a spine walk; I have not re-read it, so treat
the mechanism as a lead). It belongs in §5.4 as a third shape.

**D5. Containment and `content-visibility` as CSS-declared boundaries.**
`engines.md:115-122` covers them; `grep -i "contain:\|content-visibility"
DESIGN.md` finds nothing. The renderer must implement `contain` for its
semantics regardless, and each such box is a free cutoff and a free
parallel boundary. A node stating that is cheap and it answers part of M5.

**D6. The attribute-grammar family as a node of §3.** `DESIGN.md:318-320`
uses it only as "the constraint" on 4.1; `architecture.md:604-623` presents
it as the established theory in which "incrementality falls out of data
dependencies" is a theorem (Demers-Reps-Teitelbaum) and the parallel
schedule is derived (Meyerovich-Bodík). It is the family the owner's ideal
belongs to and deserves its own status line beside 3.1-3.7.

---

## 2. Statuses that look wrong or overconfident

**S1. "Dynamic dependency tracing is affordable per formatting context or
paragraph" (`DESIGN.md:72-76`, status measured/arithmetic).** The note's
own constants (`theory.md:53-61`: 100 ns to 1 µs per edge, ~10 edges per
unit) and the *known* counts (`build/research/concurrency/layout-results.txt:12,43`:
37,485 and 32,684 paragraphs; 9,931 and 11,794 contexts) give 37 ms to
0.37 s per full build at paragraph grain and 10 to 100 ms at context
grain. Theory's own acceptance threshold for bookkeeping is "under 5
percent" of the full build (`theory.md:802-804`), and the full build is
about 0.8 s: paragraph grain is 4.7 percent at the low constant and 47
percent at the high one; context grain 1.2 and 12 percent. So "affordable
per paragraph" holds only at the low end of a recalled constant range and
fails the note's own criterion at the high end; `theory.md:59` says "at a
few thousand units it is a few milliseconds", and the pages have ten
thousand contexts. The status rests on counts the note says are unknown
(see C1) and, once they are used, on which end of an unmeasured range is
true. It should be **uncertain, one measurement away**, not a settled
budget line.

**S2. 3.7 "dead end in Whitefoot" (`DESIGN.md:296-300`).** The argument
("single-owner boxes and no stored references, so hash-consed DAGs, HAMTs
and ropes with shared nodes cannot be represented") excludes pointer
*sharing*; it does not exclude persistence by versioned slots (D1b), nor
ropes over arena indices, which `theory.md:343-344` itself keeps ("Ropes
survive as chunked `Slots`"). Should be **hard / reduces to versioned
arenas**, not dead end.

**S3. 7.3 "Tiles and layers as the unit of invalidation: dead end for this
goal" (`DESIGN.md:447-456`).** `architecture.md:654`: "status: uncertain; a
tradeoff to measure, not a hack to remove". `raster.md:116` (P7): "on those
GPUs 'avoid tile-sized granularity' cannot be total: the hardware's tile
is the floor". `raster.md:165`: "If experiment X3/X4 shows (2) fails on the
weakest target, the minimum extension is cost-promoted subtree caches, not
tiles". `engines.md:207`: tiles exist because "scroll must be served from
already-rastered pixels without the main thread". Three notes say
"measure"; the synthesis says "dead end" before X8 and X4 run, and
`DESIGN.md:531-535` then states the outcome ("Tiles and layers then stay
out of the design"). As the *unit of invalidation* the rejection is
argued; as a *pixel cache for scrolling* it is open, and 7.3 does not
separate the two.

**S4. 4.1 "promising; the natural fit" and 5.5 "promising as emergent
concurrency" (`DESIGN.md:305-321, 389-396`).** For the owner's case, one
local edit, there is one dirty context, so style → layout → paint is a
sequential chain and 4.1 provides no cross-stage overlap at all; the
overlap it provides is between sibling subtrees, which the stages already
have. `architecture.md:425-437` says shipping is batched at frame end and
"bounds the latency gain of (a) over (c) to the style/layout/paint overlap
across siblings, not to streaming chunks to the screen mid-update".
`theory.md:604-617` shows PAR-1 denies overlap of two dynamic dirty sets
statically and rates cross-stage concurrency "hard". `DESIGN.md:311-312`
("stages overlap across contexts without a scheduler") is true and does
not say this. The honest status: promising for scattered edits, no gain
for a single local edit, whose latency is the chain's length.

**S5. 1.1 "measured local" (`DESIGN.md:131-141`).** `fanout.md:69-74`:
26 of 50 longhands were compared; `fanout.md:102`: pseudo-elements and
`::marker` invisible; `fanout.md:215-217`: "selector-structural
invalidation (siblings, `:has`) was rare (1 of 406 ...) and is not
characterized by this census"; `fanout.md:212-213`: class edits were no-ops
in 42-88 percent of samples; targets are uniform over elements, so mostly
leaves. "Measured local on these three sheets, for leaf-weighted single
edits, over 26 longhands" is what the evidence supports.

**S6. 5.4 "Recursion from the root ... frontier is an antichain by
construction" with cost O(|dirty| × depth) (`DESIGN.md:380-386`,
`theory.md:598-600`).** Descending "only where a subtree's maximum tick
moved" over an owned `Slots` of children costs a scan of the children at
each level: `shape.out` gives widths 3,545 (html5 `body`), 297 (apollo11),
122 (ecma262), so the real cost is O(|dirty| × depth × width), which §9
(`DESIGN.md:490-493`) admits and 5.4 does not. At ~10 ns per tick compare
that is tens of microseconds, so the conclusion survives; the stated cost
does not.

**S7. 3.2 and 3.5 "dead end" (`DESIGN.md:271-290`).** Both rest on the
unmeasured per-edge constant of S1 ("order of magnitude from memory",
`DESIGN.md:75`). A dead end by an unmeasured constant should be "hard;
excluded by arithmetic on recalled constants, confirmable by one
measurement". Adapton's and Salsa's actual overheads are one benchmark
away.

**S8. §8 "established here; ... at no extra design cost" (see C4).**

**S9. Status vocabulary.** `DESIGN.md:30-39` defines six statuses; nodes
use "measured local, established mechanisms" (1.1), "gap with a route"
(5.2), "proposal" (5.3), "feasible today" (5.4), "wanted" (5.6),
"established in part" (5.1), "established with limits" (7.4). 2.2 gives
one status to three schemes. The owner asked for each approach marked
feasible / hard / tried / promising; a reader cannot filter the tree by
status as written.

---

## 3. Contradictions

**C1. Context and paragraph counts: known vs "not measured".**
`theory.md:60-61`: "The number of formatting contexts on the three pages
is **not measured**; it is the first number experiment E1 should record."
`DESIGN.md:75-76`: "How many contexts and paragraphs the pages have is the
first number experiment X1 records."
`raster.md:22`: "ecma262 has 179,471 elements, 9,931 formatting contexts,
37,485 paragraphs, 2,025,062 scalars [measured by others,
`build/research/concurrency/layout-results.txt`]".
That file exists at this head and its lines 12, 43 and 69 give all three
pages. X1's "first number" is already on disk, and S1 follows.

**C2. design/pipeline.md's third decision vs theory and architecture.**
`design/pipeline.md:5`: "the compiler then proves the memoization key
complete and a result that read anything outside its key does not
compile".
`theory.md:421-427` (Claim B): "value-completeness: not given by the
language ... a program that forgets to bump a version has exactly the
'missed dependency renders stale output' failure the decision wants to
exclude, moved from the read side to the write side".
`architecture.md:217-227`: "It is not true for a function that takes
`document: &Document` and follows links from a `NodeId`: its row says
`reads(document)`, i.e. the key is the whole document ... This is a limit
of the decision's reach ... and should be recorded when the tree is
revised."
`DESIGN.md:351-364` (5.1) records the gap. `DESIGN.md:536-538` ("Ask
Whitefoot for nothing yet") carries no obligation to amend the pipeline
decision, so a live design-tree decision now rests on a claim the
research contradicts. This is the one finding that is a design-tree
matter, not only a research one.

**C3. The census's "parent-relative" count is presented as Q55's cost;
they are different schemes, and Q55's is worse.**
`DESIGN.md:103-106`: "Offsets relative to the parent are not enough on flat
pages. html5's `body` has 3,545 block children. Removing one `dd` moves
117,137 boxes. It needs 3,560 offset rewrites with offsets relative to the
parent"; `DESIGN.md:152-155` (1.3): "Context-relative positions. These are
Snowghost's Q55 ... On flat contexts the cost is O(siblings)".
`fanout.md:80-81`: the census's reference box is "the nearest block-level
ancestor's box"; `design/pipeline/layout.md:11` (Q55): offsets are "from
its own border box" of the *formatting context*, and a `Block` is not a
context (`architecture.md:762`). html5's dominant BFC holds 20,919
paragraphs (`architecture.md:51`), so under Q55 as decided a height change
near its top rewrites every block, paragraph and line offset after it in
that context, which `raster.md:176` states plainly: "for a 10^5-child flat
context is still an O(children) rewrite for a height change near the
top". So 3,560 is the census's nearest-block number, not Q55's; Q55's
number on html5 is unmeasured and plausibly above 10^4. The tree's budget
for 1.3 is therefore understated, X3's thresholds (`DESIGN.md:507`: more
than 10^4 against fewer than 10^3) may well be decidable, and X3 must
measure on Snowghost's own layout output, as its "Needs" column already
says, rather than reuse the census's column.

**C4. §8 oracle vs identity drift.**
`DESIGN.md:476-481`: "after a history of edits, its dumps must be
byte-identical to a full run on the final document. This gives an exact
oracle ... at no extra design cost."
`architecture.md:828` (E5 pitfalls): "interned ids are assigned in
first-occurrence order per run, so the diff dereferences each id to its
group *value*, never compares ids; and a structural mutation shifts
preorder indices and context paths".
`architecture.md:387`: "`Fragment.owner` = preorder index for elements ...
| `NodeId` (+ generation) for both; the oracle driver maps to preorder for
dumps".
An incremental run keeps its interning tables and node slots across
frames, so its ids and indices differ from a fresh full run's. Byte
identity then holds only if the dump already canonicalizes both:
architecture plans the preorder renumbering (second half of line 387);
whether the dump emits interned ids or dereferenced group values I did
not verify. "No extra design cost" is a check to make against the dump
format, not a settled fact, and the section should say which
canonicalization it relies on.

**C5. Experiment gating names the wrong experiment.**
`DESIGN.md:372-373` (5.3): "Status: proposal, gated on experiment X2."
`DESIGN.md:536-538`: "A compiler mechanism for versions (5.3) needs X2's
measurements."
`DESIGN.md:506` (X2): "How is per-node style stored under stable identity:
renumbering, a certified scatter, or `Segments`?"
The experiment 5.3 needs is `theory.md:828-835` (E2: library ticks first,
count bump sites, a deliberately omitted bump against the oracle,
bookkeeping share of the full build). It has no row in the table.

**C6. Intern-pass share inside theory.md.** `theory.md:342-344`: "measured
at 0.5 to 4.6 percent of the four-worker style stage"; `theory.md:739`:
"the intern pass costs 2.9 to 4.6 percent". I could not find either range
in `concurrency/DESIGN.md` by grep; both are unverified here.

**C7. 2.1's unit table vs architecture's (D3 above).** Seven units become
three without a reason given.

---

## 4. Claims in DESIGN.md lacking evidence or unflagged recall

- `DESIGN.md:62-66` (the budget): "html5's style stage takes 0.18 s". The
  source table (`theory.md:28-30`) labels that row "style stage (shape C,
  prototype)". The real style stage figures the notes give are for ecma262
  (`architecture.md:39-41`, about 0.63 s at four workers). The budget mixes
  a prototype style time with a real layout time and does not say so.
- `DESIGN.md:134-137`: Stylo's invalidation map "established" — engines
  has it [M] (`engines.md:61`, "from memory of source code"); Blink's doc
  was obtained as a search snippet only (`engines.md:409`).
- `DESIGN.md:157-158`: "as Zed's SumTree keeps sums" — `engines.md:285` is
  [M].
- `DESIGN.md:292-294` (3.6): "established in React and WebRender's
  interning" — `engines.md:228` marks WebRender interning [M].
- `DESIGN.md:435` (7.1): "Zed's GPUI, Vello-based Masonry and early
  WebRender" — GPUI cited (`raster.md:68`); Masonry and early WebRender
  [M] (`engines.md:278, 243`).
- `DESIGN.md:459-462` (7.4): Vulkan "has no buffer-age query" and the KMS
  damage clips are [memory] in `raster.md:104,106`; DESIGN flags only Metal.
- `DESIGN.md:465-466` (7.5): "On text-heavy pages glyph drawing is the
  dominant item" — derived from an assumed 250,000-chunk scene;
  `raster.md:22`: "Line count and paint-item count are **not** measured".
- `DESIGN.md:69-71`: "One scan of a dense version array costs about 1 ms"
  — `theory.md:51-52` marks the constants speculation; DESIGN says
  "arithmetic, with the per-unit constants an estimate", which is fair,
  but the three "dead end" verdicts built on it (S7) are not hedged.
- `DESIGN.md:82`: "375 edits on apollo11, and 16 and 12 per kind on html5
  and ecma262" mixes a total with per-kind counts (`fanout.md:58-60`:
  apollo11 is 30 per kind, 15 for container kinds).
- `DESIGN.md:54-55`: "The census scripts and their aggregates are in
  `census/`". The raw results fanout names (`fanout.md:11-12`:
  `apollo11.json`, `html5.json`, `ecma262.json`, `chain-*.json`) are not in
  the repository, and `fanout.md:9` says the scripts are in `fanout/`,
  which does not exist. The census is reproducible only by re-running
  Chromium under Playwright; its aggregates cannot be re-derived from
  what is committed.
- `theory.md:3` and `architecture.md:3` cite a shared `context.md`; no such
  file exists on this branch.
- `DESIGN.md:286` correctly flags LayoutNG line reuse as from memory; the
  same flag is missing on LayoutNG's "simplified layout" and consumed-
  dimension coarsening that 1.4 and X4 build on (`engines.md:126`: "[M,
  moderate confidence, names approximate]").

---

## 5. Experiments: criteria that cannot fail, and better discriminators

**Criteria that cannot fail as written (`DESIGN.md:503-514`):**
- X1: "records the affected set per edit kind at each unit; decides whether
  context plus paragraph is the layout unit" — a measurement with no
  threshold. The source criteria had thresholds: `architecture.md:126-131`
  (fewer than 1 percent of paragraphs change lines ... more than 10 percent
  of descendants change ids) and `engines.md:367` (recomputed/oracle ≤ ~3×,
  visited within an order of magnitude of recomputed).
- X4: "decides whether container-width edits get memoization or only
  parallelism" — no threshold; `engines.md:375` had "more than ~half of
  paragraphs keep breaks across a 10 px resize".
- X9: "first-frame and scroll latency, and the size of the full list" — no
  threshold at all.
- X10: "frame cost of a text-heavy page per approach" — `raster.md:221` had
  "atlas stays the default if it beats the others by > 20 percent and the
  others do not need > 2× work to match its crispness".
- X3: see C3; the census column it reuses measures a different scheme.

**Criteria dropped in the merge:** theory E1's "a no-op edit under 0.5 ms"
and "full build with bookkeeping within 5 percent of today's"
(`theory.md:823-825`) are gone from X5, although the no-change frame is the
tightest constraint in the budget (`DESIGN.md:67-71`) and the bookkeeping
share is the one number that decides 5.3.

**Experiments that would discriminate better:**
- **A no-change frame.** Time a frame after zero edits at one and four
  workers with each candidate (dense tick scan, subtree-max ticks, edit
  lists). Criterion: under 0.5 ms; any scheme above it is out whatever its
  edit-time numbers.
- **An editing session.** Run a history of 100-1,000 edits at one point
  (typing) and scattered, checking the §8 oracle after every prefix, and
  record memory growth of interning tables and arenas. Single edits
  cannot show drift, leaks or the cost of stale identities.
- **The omitted-bump mutation test** (`theory.md:830-833`): remove one tick
  bump deliberately and check that the oracle catches it on the edit
  script. If it does not, 5.3's language mechanism has its first ground;
  if it does, a test replaces the rule for now. This is the only
  experiment that bears on 5.3 and it is not in the table.
- **Over-approximation ratio per key design** (`engines.md:366-368`): for
  each edit class, recomputed set / oracle minimal set for whole-style
  keys vs group keys, exact vs coarsened `Space`. X1 records the oracle
  set only; the ratio is what decides key granularity (engines Q-a).
- **Single-edit latency to first chunk, 4.1 vs 4.3.** X6's "scattered
  100-cell edit" is throughput-shaped and favours 4.1 by construction;
  the owner's framing is one local edit. Measure both; if 4.1 wins only
  the scattered case, S4's honest status follows.
- **Parser-append and font-arrival edit classes** (M3) against the
  existing drivers: the append class tests the "only what follows" claim
  directly; the font class bounds the worst realistic re-preparation.
- **Scroll by redraw vs copy on real content** before fixing 7.3's status
  (raster X4): keep it as its own row rather than folded into X8.
- **X3 with the census's actual distribution** rather than fixed powers of
  ten: adopt the offset tree if, over the chain census's push-root
  distribution (`fanout.md:184-196`), the context-relative scheme's p90
  rewrite count exceeds the tree's by more than the measured per-write
  cost ratio. That criterion can fail on html5 and pass on ecma262, which
  is the discrimination wanted.

---

## 6. "Where the branches agree" narrows the exploration

`DESIGN.md:520-538` presents four agreements. Checked against the notes:

- **"The candidate execution model is 4.1, with 4.3 as its control."** Only
  `architecture.md` proposes (a). `theory.md:618-635` proposes the spawned
  pipeline and rates cross-stage overlap "hard"; `engines.md:398` recommends
  LayoutNG's keyed model at box/paragraph grain and is silent on execution
  model; `raster.md` does not address it; `architecture.md:528-530` itself
  says it would land on "(a) with recorded reads for the long edges", which
  is a 4.1/4.2 hybrid the synthesis does not offer. "Branches agree" is
  one branch's recommendation, and it forecloses D1, D2, D4 and M4 before
  X1 runs.
- **"Fix the paint boundary ... Tiles and layers then stay out of the
  design, and the shell decides damage by chunk bounds."** It decides X8's
  and X4's outcome (S3), and it presumes whole-page paint shipped to the
  shell while `DESIGN.md:337-339` (4.4) and `raster.md:186` (D4b) keep
  whole-page vs viewport-dependent paint open: the shell can only "decide
  damage by chunk bounds" if it holds the chunks.
- **"Ask Whitefoot for nothing yet beyond what is recorded."** Reasonable
  as sequencing, but it leaves C2 standing: the one thing the research has
  found about Whitefoot is that `design/pipeline.md:5` claims more than the
  language gives, and the agreement does not ask for that record to be
  corrected.
- **"Measure before building"** is the one agreement all five notes make,
  and the experiments it names (X1, X3, X4) are the ones whose criteria
  cannot fail (section 5).

Also narrowing by omission: the three-row unit table (D3), the absence of
containment (D5), and the statement in 2.2 of a "recommended combination"
of identity schemes before X2 runs (`DESIGN.md:241-243`).

---

## Summary of the most important points

1. The counts X1 is to "record first" are already measured
   (`layout-results.txt:12,43,69`); with them the budget's "affordable per
   paragraph" claim passes theory's own 5 percent criterion only at the
   low end of a recalled constant range and fails at the high end, so it
   is uncertain, not settled (C1, S1).
2. `design/pipeline.md:5` claims a compiler-proved complete key; theory
   and architecture show it is place-complete only and not for arena-linked
   reads. DESIGN records the gap but nothing proposes amending the
   decision (C2).
3. The census's nearest-block offset count (3,560) is presented as Q55's
   cost; Q55 is context-relative and on html5's 20,919-paragraph BFC its
   rewrite is O(children), unmeasured and plausibly above 10^4. 1.3's
   budget is understated and X3 must measure on Snowghost's own output
   (C3).
4. The §8 oracle's "no extra design cost" holds only if the dump already
   dereferences interned ids and renumbers; the second is planned, the
   first unverified (C4).
5. X1, X4, X9 and X10 have no failing condition; the no-op-frame and
   bookkeeping-share criteria and the omitted-bump test were lost in the
   merge; 5.3 is gated on the wrong experiment (C5, section 5).
6. "Dead end" on tiles, persistence, traces and signals is stronger than
   the notes support; 4.1 gives no cross-stage concurrency for the single
   local edit the owner describes (S2-S4, S7).
7. Branches absent from every note: summary trees as the general chain
   family, delta-typed stage interfaces, realistic edit classes (append,
   font/image arrival, animations), progressive rendering,
   stratification, compiler-derived invalidation tables, GPU placement,
   script path flushes. Branches a note named and the synthesis dropped:
   recorded reads for long edges, versioned-slot persistence, the spawned
   pipeline, box tree and text preparation as units, spineless traversal,
   containment, attribute grammars as a family.
