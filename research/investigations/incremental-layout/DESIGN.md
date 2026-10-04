# Incremental layout on the owned context tree (X5)

## Question

Can one edit to a page re-lay out only what it affects, on the layout stage
as it stands, fast enough to be the interactive path? This is experiment X5
of the incremental research tree
(`research/investigations/incremental/DESIGN.md`, Experiments), the first
build on the owner's main line: the minimal end-to-end update, with
concurrency inside a frame as its constraint.

## Criterion

Written before any run, in the research tree's Experiments table:

1. a one-paragraph edit under 1 ms at four workers and under 1/100 of the
   full stage;
2. an `html` font-size change no worse than 1.2 times a full run;
3. a full build with the bookkeeping within 5 percent of today's;
4. after every edit, dumps byte-identical to a full run on the edited
   document (the research tree, §8).

"The full stage" is the layout stage from computed styles to laid-out
boxes: 0.590 s on html5, 0.587 s on ecma262 and 0.044 s on apollo11 at four
workers (`research/investigations/layout/runs/time-parts.txt`). So part 1's
1/100 is 5.9, 5.9 and 0.44 ms; on apollo11 it is stricter than 1 ms and
binds.

## Scope

Grounded in the research tree's Results (X1, X3, X4, X8, X12, X16).

**Edits, in order.**
1. `word` and `sentence`: X1 shows one paragraph changed in 68 of 70 edits,
   no style change, and 1 to 6 contexts changed (shrink-to-fit ancestors;
   18 at most on ecma262). They carry part 1.
2. `colour`, `fontsize` and `rootfont`: they enter layout from the style
   stage and test keys split by consumer (X1: a whole-style key recomputes
   a paragraph on 27 of 30 apollo11 colour edits, a key of the
   layout-relevant groups none) and part 2.
3. `block`: the structural case (identity, the box tree's walk, offsets).
   No criterion number yet; X5 records its first.

Deferred: `class` and `custom` (the path of `fontsize` and `rootfont` once
the style delta exists), parser appends and font arrival (X8), width-interval
keys for line breaks (X4: lay_out is 26 to 29 percent of the work), and
cutoffs inside tables, flex and grid (tree 1.5: a cell change reruns its
container).

**Stages.** Incremental: the box tree (per context, from a checkpoint of the
walk), text preparation (per paragraph, keyed) and layout (a context with a
`Space` cutoff, a paragraph with a key). A full rerun: parsing (edits go to
the live `Document` through `pkg::dom`'s operations, so node ids hold) and
the style stage, whose result enters layout as a delta (Q68). `place_boxes`
and the dump stay untimed, as in `run.sh time`.

## Decisions

Each is open for the owner and taken on its recommendation meanwhile. The
cards are in the PR's handoff; here are the choices and their grounds.

**Q67, identity across edits.** `StyleRef.element` and `Fragment.owner`
are preorder positions in `Styles.elements` (`renderer/layout/module.wfm`),
so a block insertion renumbers every later element. Options: renumber the
kept tree after a structural edit; `NodeId` in both fields with a dense
`order[node]` rebuilt with each style run; order-maintenance labels.
Recommended: `NodeId`, stable for the node's life, routed in O(1), and the
style stage's storage order stops being a layout dependency; part 3 measures
the indirection.

**Q68, how an edit enters.** At the document boundary, an edit list of DOM
operations resolves each changed node to its unit (`unit_of`, written by the
box tree's walk) and marks the path to the root with ticks (X12: 27 to 42 ns).
At the style boundary, after the full style rerun, the layout-relevant group
ids of old and new styles are compared densely, aligned by `NodeId` (X12:
44 to 82 µs), and each changed element marks its unit. Recommended over
dirty marks without a style delta (X1: every paragraph recomputes on a
colour edit) and over diffing inputs each frame (O(n) per frame). Two
interface consequences:
- interned group ids are the index of the first equal value in a run's
  table (`renderer/style/intern.wf`), so a value first seen earlier in a new
  run shifts every later id; the new run interns into the previous run's
  tables, keeping old ids;
- `pkg::dom` has no in-place text mutation; a word edit replaces the text
  node, which grows the arenas per keystroke, or `pkg::dom` gains
  `replace_text`.

**Q69, keys and cutoffs.** Whitefoot has no aggregate equality ([OP-8]), so
keys and outputs compare as integers and interned ids.
- A context's key: its `Space`, the layout-relevant group ids of its
  establishing element (box, size, spacing, border, font, text, container,
  item, table, content; not background or custom), the font set's tick, and
  for the box tree, the walk's state at its entry (counters, quotes, open
  inline styles).
- Its compared output: border-box width and height, baseline, margins, and
  intrinsic sizes when known, since X1's word edits dirty up to 18 ancestor
  contexts through shrink-to-fit, each cutting off at its parent when its
  size holds.
- A paragraph's key: its pieces (node, span, scalar, per-run layout groups)
  and the font picks' tick for preparation; width, left, exclusions and
  atomic children's sizes for breaking. Output: height and line count.

Recommended: the layout-relevant groups only, against the whole style (X1)
and recorded reads per unit (affordable per X12, but the edge count is
unmeasured; X5 counts the far reads).

**Q70, offsets (Q55 revisited).** X3: context-relative offsets rewrite
24,213 entries at p90 on html5 against 48 for a summary tree, but at 0.55 to
2.5 ns a write that is 13 to 61 µs, inside part 1. The deciding cost for X5
is the block pass's walk from the edited entry to the context's end, which a
moved height forces under context-relative offsets. Recommended for X5: keep
Q55, add a translate-by-δ path over later entries when the edited entry's
exit margin strut is unchanged and no float extends past it, and read
positions through one function, so a summary tree can replace it if the
measured walk fails part 1. Parent-relative offsets win only on nested
pages; prefix sums or a summary tree make every reader in the block pass and
`place_boxes` pay a sum on every full build, against part 3. Reopen at the
paint boundary, where under Q55 a δ changes every later chunk's offset.

**Q71, parallel loops over a dirty set.** Recommended: recursion from the
root over subtree ticks, each iteration testing its own unit's tick in an
`if`, so `lay_out_children`, `break_all` and `prepare_context` stay counted
loops over `children[i]` and `paragraphs[i]`, certified affine elements
([PAR-2]); no new fact, and the frontier is an antichain by construction.
Ticks and keys live inside `Context` and `Paragraph`, and the frame's epoch
is a by-value parameter, because reading an unwritten scalar of a shared
state denies a certified loop (`docs/todo.md`). Against a flat dirty list
with `apart` (needs the per-frame distinctness fact [MOD-6] keeps from
travelling with the list) and a flat arena with a certified scatter (changes
the storage decision of `design/pipeline/layout.md` for a gain only X6 could
show).

**Q72, the no-change frame.** Recommended: push-based ticks on the tree,
plus the dense style delta while style is a full rerun (X12: one tick load;
dense scan 44 to 82 µs), against a dense version scan every frame (68 µs on
html5) and a memo-key walk (2.3 to 2.6 ms at paragraph grain, failing X12).

**Q73, the oracle.** Recommended: after every prefix of an edit script, the
incremental dump byte-identical to a from-scratch build on the edited live
document and to a re-parse of the edited source; and the sequential build
identical to `--par`. Falsifiers, each run once and required to fail: one
tick bump deleted (X11), one key field omitted.

**Q83, the style delta's identifiers (Q68 revised).** Step 4a did not
implement Q68's interning into the previous run's tables: each style run
interns on its own, and `layout_changes` maps both runs' tables onto
classes by value, once per table, then compares each element's classes
(`renderer/style/delta.wf`). Interning into the previous tables makes them
grow over a session with every value ever seen, and makes each run's
interning wait on the last. The alternative tried after step 4a, comparing
every element's values deeply with no table, failed criterion 2 at four
workers on ecma262 (root-font update/full median 1.31; colour delta 217 ms
against 3 ms; `runs/step4b.txt` on the archive branch named in Results).
Marking follows from the delta by a recursion over the tree in which each
paragraph and context tests its own pieces' styles (Q71's loops), rather than
by each changed element marking its unit through `unit_of`; both are linear
while the style stage is a full rerun.

**Q84, background presence in the style delta.** Layout's `culled_box`
(`renderer/layout/inline.wf`) reads whether a background is currentColor or
has positive alpha, and a culled inline box reports its content's
rectangles instead of its own, so the dump depends on that predicate while
Q69 left backgrounds out of the keys. Recommended: compare the predicate in
`layout_changes` and keep ignoring exact colours, which no layout reader
reads; a changed predicate marks its paragraph, which is prepared and
broken again although only its fragments change (`docs/todo.md`).

**Q85, style attribute and hint records by NodeId.** `pkg::style` recorded
each element's style attribute and presentational hints once, at load, by
preorder position, and looked them up by binary search on that position, so
an inserted or removed element left every later record on the wrong element:
step 1's finding 6, where every apollo11 block edit differed from a re-parse
(`runs/step1.txt`, section 6). Recommended: a dense array from NodeId to the
record, filled by the recording loop at load, which is already sequential
because it appends to the store; each element then reads its own slot.
Rejected: keeping the records sorted by NodeId with a binary search, because
the tree builder creates some nodes out of tree order (foster parenting,
adoption), so load order is not NodeId order; and recording them again after
every edit, which parses every style attribute per frame.

**Q86, the structural update.** A `B` or `X` edit changes the children of one
element. Recommended: build again the context of the nearest element at or
above it that establishes one (C), from the walk's state as `build_box`
entered C, recorded in each context with the state as it left (Q69's walk
state at entry); keep every other context; give each new paragraph whose
pieces and styles equal an old paragraph's that paragraph's preparation
(Q69's paragraph key); record text units and paths again over the whole tree.
Refuse, before changing the layout, when the walk leaves C in another state
(counters or quotes a later context reads), when the delta flags an element
outside C or C's own element, or when the generated text or the
pseudo-element list changed, which retained pieces index. Dependencies: the
walk inside C is the builder's one chain in document order, as in a full
build; finding each paragraph's old counterpart reads only its own first text
node's unit; taking the preparation swaps into an old paragraph whose index
the compiler cannot prove apart from another iteration's, so that loop is
sequential (`docs/todo.md`, Whitefoot requirements); recording units and
paths again is one walk, linear in the tree, and is measured. Against copying
the preparation (no source constructor of `ShapedText` outside
`pkg::layout::text`), against keeping C's unchanged child contexts by their
entry state (deferred: on html5 C is the root element's context and most of
its paragraphs sit in its own flow, so paragraphs dominate), and against
stable per-source routing of every context (the stopped branch's Q81),
which renames nothing but adds a routing layer to every update.

## Measurement

- **Edit scripts.** `scripts/edits.py`, with X1's seed and rules
  (`research/investigations/incremental/experiments/x1-x3-x16/`), emitting
  the driver's edit language (`renderer/oracle/layout/module.wfm`) keyed by
  the node identifiers the driver's `nodes` mode lists, and by the base dump
  for the boxed elements and text: X1's single edits (30 per kind per page,
  10 on ecma262), and typing sessions of 100 to 1,000 word edits at one point
  and scattered (X13).
- **Driver.** A mode `edit` of `layout_oracle`: load, build, then per edit
  apply, update, and dump or time, excluding `place_boxes` and the dump.
  Per script: minimum, median, p90, maximum, best of 5 process runs, every
  build and run under `run-check.pl`, `WF_WORKERS` 1, 2 and 4 and the
  sequential build.
- **Parts.** Part 1 from `word` and `sentence` at four workers; part 2 from
  the `rootfont` edits against the same build's full `lay_out`; part 3 by
  `run.sh time`'s method against main, with the ledger's split layout loops
  not dropping; part 4 after every edit, both builds, and both falsifiers.

## Steps

1. The edit language, mode `edit` with a full rebuild after each edit, the
   emitter and the re-parse oracle. Check: script (a) byte-identical on three
   pages, sequential and `--par`.
2. Bookkeeping without incrementality: `NodeId` identity, `unit_of`, ticks
   and keys in `Context` and `Paragraph`, the walk's checkpoints. Check: dumps
   unchanged; part 3; the ledger's layout loops.
3. Text edits: patch the pieces, re-prepare and re-break the paragraph,
   re-stack with the δ path and the size cutoff, recursion over ticks. Check:
   parts 1 and 4 on `word` and `sentence`; the measured re-stack walk decides
   whether Q70's recommendation stands.
4. The style delta (Q83); `colour`, `fontsize` and `rootfont`. Check: part 2; colour edits recompute no
   paragraph.
5. `block`: rebuild a context from its checkpoint, reusing its paragraphs'
   preparation by key. Check: part 4; its cost and entries moved recorded.
6. Sessions, falsifiers and the far-read counter; results here; the rulings
   into `design/pipeline/layout.md`.

## Style update validation plan

Before step 4b's implementation and runs: retain the box tree only when the
same traversal, generated-content references and pseudo-element identities
still describe it. A style delta marks actual consumers in independent
context and paragraph loops, then gathers child marks up the owned tree.
Each paragraph depends on its pieces and styles; each context's local mark
is independent of its siblings. Only propagation to a parent needs a
child's mark. Repeated root-to-unit marking would impose an avoidable order
on changes to unrelated elements, so use Q71's recursion and counted loops.
No mark skips the tree, as Q72 requires, after validating retained references.

A local style change must not take a cutoff whose premise was an unchanged
style. Record each paragraph's actual line-breaking width and left edge;
the pre-pass may change these through a block's em-based spacing while its
context width stays constant. Keep preparation only for paragraphs whose
layout-relevant style consumers did not change, and keep lines only when
their actual inputs still match. The caller recomputes FontPicks for the
new style tables before using them.

Checks, required before claiming this step complete:
- Text colour changes prepare and lay out zero units; font-size and root
  font-size edits must succeed incrementally, without a full-rebuild fallback.
- Every edit and its inverse match the full build byte for byte, including
  a font-size edit followed by a text edit, em padding, empty inline boxes,
  and unchanged paragraphs whose font groups were renumbered.
- DOM class changes carry NodeId and attribute-name facts under Q68;
  computed style equality alone does not cover `content: attr(class)`.
  Refuse a changed attribute consumed by that element's generated content
  before marking, while accepting an unrelated element's class edit. The
  scope remains colour/font-size updates, not arbitrary attribute updates.
- A box topology or generated-reference change that cannot be retained is
  refused before marks are written; inserted non-generating pseudo-elements
  must not silently move retained references to the wrong pseudo-element.
- Compare a paragraph's saved width and left with the pre-pass results;
  omit that comparison once and require the em-padding case to fail.
- Omit one style mark once and require a font-size case to fail. Run both
  sequential and four-worker drivers and compare their checked outputs.
- Measure criterion 2 against the same build's full layout stage, excluding
  the full style computation from both. Report style-delta and font-picking
  costs explicitly; do not describe the still-full style stage as incremental.

`scripts/style-case.html` holds one element for each of these cases, and
`scripts/style-case.edits` edits them in order, each edit followed by its
inverse: em padding around a paragraph whose own style is fixed, a
background turning visible, another colour and transparent, an empty inline
box gaining padding, `attr(class)` and `attr(title)` read by `::before`, a
font size followed by a text edit, `display: none` removed, a pseudo-element
added, a colour and the root font size. The attribute, display and
pseudo-element edits must be refused; every other edit must be `inc same`.
Run from the repository root:

    build/layout_oracle_seq edit research/investigations/incremental-layout/scripts/style-case.edits research/investigations/incremental-layout/scripts/style-case.html renderer/style/ua.css

## Structural update plan (step 5)

Step 2 recorded text units and paths but not Q67's identity: `StyleRef.element`
and `Fragment.owner` were still preorder positions, so step 5 has two parts.

5a, identity. `Traversal.order` and its copy `Styles.order` map NodeId to
preorder; `StyleRef.element` and element owners hold NodeIds, resolved
through `element_position` (`root_element` names the root's style); the style
delta is one flag per NodeId; style attribute and hint records follow Q85.
Checks: every dump of the three pages and of `scripts/style-case.html`
byte-identical to main's; every step 3 and step 4 check still passing, seq
and par; the five apollo11 block edits of step 1's re-parse check now equal
to the re-parse; part 3 within 5 percent.

5b, structure (Q86). Checks, with the `block` scripts of the three pages,
seq and par:
- every edit `inc same` or `inc refused`, every refusal counted and
  explained, none differing; seq and par output lines identical;
- falsifiers, each required to fail on a script or case: the exit state not
  compared (a case where an inserted list item changes a later counter); the
  old context's outputs not carried into the new one; the piece comparison
  of the paragraph key dropped (a reused paragraph whose text differs);
- recorded per edit: the microseconds of structure_changed and update, the
  contexts and paragraphs built again, the paragraphs that kept their
  preparation, against the same build's full layout. No latency threshold is
  set before this first measurement.
- part 3 with the checkpoints of every context, within 5 percent.

`scripts/block-case.html` and `scripts/block-case.edits` hold the cases, each
insertion followed by its removal: at the end of a box, splitting an inline
paragraph, inside a counted box whose counter a later box shows (must be
refused), in the root element's context, and inside a box of fixed height.
Run as the style case is, with `block-case` for `style-case`.

## Risks

- A certified loop is denied when it reads an unwritten scalar of a shared
  state (`docs/todo.md`); step 2 shows whether adding a tick read to
  `lay_out_children` trips it, which would be the first place a Whitefoot
  change precedes the prototype.
- Distinct-index facts are derived again in each pass (`docs/todo.md`): not
  blocking under Q71's recommendation.
- `Slots` insertion shifts indices ([OP-10]): no paragraph is inserted in
  place, so a `block` edit rebuilds its context and costs its context's size
  (html5's `body` holds 3,545 children).

## Results

None yet.

## Owner rulings

2026-10-04: after a comparison of each card's performance and feasibility,
the owner wrote in Chinese that they agree to all, as recommended: Q67
(NodeId with a dense order array), Q68 (push-based marks and the style
delta), Q69 (keys of the layout-relevant groups), Q70 (keep Q55 with the δ
path; revisit at the paint boundary when the contract's C3 measures the
bytes per edit), Q71 (recursion over marked subtrees), Q72 (push-based
marks) and Q73 (the byte-identity oracle with falsifiers). They go into
`design/pipeline/layout.md` with step 6, and `design/log.md` records them
then.

2026-10-04: the owner chose Q83's option A, the per-run tables mapped by
value, over interning into the previous run's tables and over deep
comparison without tables. With the owner's agreement, Q77 to Q82, proposed
on the stopped branch `codex/x5-handoff-2026-10-03`, are withdrawn; Q84
takes up Q77's background predicate, which the byte-identity oracle needs.

2026-10-04: the owner approved Q84, Q85 and Q86 as recommended. They go
into `design/pipeline/layout.md` and `design/pipeline/style.md` with step 6,
with Q67 to Q73 and Q83.
