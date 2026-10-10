# Structural edits that cost what they insert (M2)

## Question

Can inserting or removing an element restyle and lay out only what the
insertion reaches, so that E1's block edit costs less than Chromium's
(`research/investigations/engine-comparison/runs/e1.txt`)? The block edit
inserts a two-line paragraph and removes it again. Chromium's costs are:

- apollo11: 0.30 ms;
- html5: 3.06 ms;
- ecma262: 0.12 ms.

This is M2 of the plan in `research/investigations/incremental-style/DESIGN.md`.
The owner chose it as the next milestone (Q106), with Q90 (NodeId-indexed
style state), Q94 (per-parent sibling positions) and Q104 (block offsets
relative to their parent, reopening the layout tree's Q70) in its scope.

## Where the cost is now

Measured at 8b8612f with the layout driver's edittime mode
(`incremental-style/runs/step5.txt`): `run.sh time seq PAGE block 1` with
ALONE=1, Apple M1 Pro, sequential build. The figures are the medians of a B
edit (insert a paragraph), in ms.

| page     | full style | full delta | structure + update | total seq | Chromium |
|----------|------------|------------|--------------------|-----------|----------|
| apollo11 | 114        | 4.3        | 16                 | 129       | 0.30     |
| html5    | 476        | 77         | 239                | 715       | 3.06     |
| ecma262  | 937        | 86         | 259                | 1180      | 0.12     |

`apply_structure_edit` (`renderer/oracle/layout/edit.wf`):

1. Builds the traversal again: every element's preorder position, parent
   and depth. O(elements).
2. Builds a whole new style state. The kept state is indexed by preorder
   position, which the insertion shifts for every later element (Q90).
3. Compares the two states element by element (`layout_changes`).
4. Builds again the context that holds the inserted block
   (`structure_changed`). On html5 that context has 13,842 child contexts
   and 60,869 paragraphs, 59,243 of them reused. On ecma262 the update then
   walks about 118,000 flow entries.

## What the target implies

ecma262's 0.12 ms is about 120 us for the whole edit: DOM insertion, style
and layout. ecma262 has 179,471 elements (419,309 nodes with its text nodes) and about
118,000 flow entries in one context. Any step that touches every element or every entry, at even
1 ns each, spends most of that budget. So the edit's path may not hold:

- a traversal built again (step 1);
- style state shifted or rebuilt by position (step 2);
- a whole-page delta (step 3);
- a flow entry array shifted by an insertion: half of 118,000 entries of
  tens of bytes is megabytes of memmove;
- positions of every later entry moved one by one (the suffix move that also
  keeps ecma262's font-size edit at 1.8 to 2.1 times Chromium, Q104).

Each structure an edit touches must allow insertion and lookup in time that
follows the edit, not the page.

## Dependencies of an insertion

What the insertion of an element E under parent P before sibling S truly
depends on:

- **Matching E's subtree.** It reads E's ancestors, which are unchanged,
  and E's siblings. Independent per element of the subtree.
- **Siblings whose matching reads positions or neighbours.** `:nth-*`,
  `:first-child`, `:last-child`, `+` and `~`. Only P's children and their
  descendants, through the rules' structural features: the same kind of
  reverse index as Q91's class reaches.
- **Inherited values.** E's subtree reads P's computed values, which are
  unchanged. Independent of everything after S.
- **Counters and quotes.** They run in document order (layout tree Q86).
  An insertion that changes a counter must reach every later reader; Q86
  refuses that case today.
- **Layout.** E's boxes and paragraphs depend on E's styles and the width
  of P's content box.
  - P's stacking depends on E's height, through E's margins and the floats
    that reach E.
  - P's height depends on its children.
  - P's ancestors depend on P's height.
  - Blocks after P move only by P's height change, unless a float or a
    margin collapsing through P's edge carries more.

So the true chain is: E's subtree, P's later children, then P's ancestors
up to the context. Every later block of the context only moves. In a flat
flow with positions relative to the context, that move is O(suffix). With
positions relative to the parent block, each unaffected sibling subtree
moves in O(1), but the update still visits the affected direct sibling
ranges along the ancestor path, plus any margin/float influence. It is not
O(1) per ancestor. The concrete representation, dependency bounds, census
and stack-pass measurements are in [the layout design](layout-design.md).

## Candidates

Each candidate is listed with its dependency chain; measured speed decides
only between candidates with equal chains (AGENTS.md).

### Style state keyed by something an insertion does not move (Q90's scope)

- *NodeId*. The DOM arena only appends, so no slot moves. Arrays are sized
  by the node count, text nodes included: ecma262 has about twice as many
  nodes as elements. Chain: none added.
- *A stable element slot.* Each element gets the next slot when first
  styled, and a removed element's slot is left empty. Arrays are sized by
  elements ever styled. It needs a NodeId-to-slot map, one per document.
  Chain: none added; one more indirection than NodeId.
- *Preorder with shifting.* Every insertion shifts every array after the
  point. Chain: O(elements) per edit. Rejected by the target.

### Iteration order without a traversal per edit

The full stage iterates elements in preorder by levels (style tree,
"level cascade"). A restyle of a set iterates the set's elements by depth.
An insertion needs only:

- the new elements' depths, which are their parent's plus one;
- the restyle set by depth.

Candidates:

- *Keep the traversal for full builds only.* An edit computes depths from
  parents, never preorder positions. The kept preorder list goes stale
  after an edit and is rebuilt lazily, off the edit's path.
- *An order-maintenance structure.* It gives O(1) or O(log n) before/after
  comparisons with insertion, for consumers that need document order
  (counters, layout's preorder serials).

### Flow entries an insertion splices into

- *Flat per context, as now, in chunks.* Insertion touches one chunk.
  Offsets stay relative to the context, so the suffix move remains.
- *Nested per block, with offsets relative to the parent block.* Each
  block holds its own entries and its children's offsets.
  - An insertion changes P's entries.
  - A height change reaches P's ancestors, one offset each.
  - Readers of an absolute position add offsets up the chain.
  - Chain for an edit: P's later children and P's ancestors.
  - A full build stacks each block's children in order. Different blocks'
    children are independent except where floats or collapsing margins
    cross their edges. Those are true dependencies, which the flat flow also
    has.
  - This is Q104's direction. Its cost on readers (paint, the dump, hit
    tests) is to be measured.

### The restyle set of an insertion (Q94 and the structural reverse index)

- *The inserted subtree only.* Wrong when a later sibling matches
  `:nth-child`, `+` or `~` against the new position.
- *The inserted subtree, plus the siblings and sibling descendants that
  structural reaches name.* This is recorded as Q91's class reaches are,
  per structural pseudo-class and sibling combinator. Sibling positions are
  recomputed for P alone.

## Criterion

Written before implementation and kept as written, as M1's was.

1. **Identity.** Every edit of X5's block scripts on the three pages, of
   `incremental-layout/scripts/block-case`, and of new focused cases is
   `inc same` or an explained `inc refused`, seq and par, with seq and par
   outputs equal. The focused cases are:
   - a counter after the insertion;
   - `:nth-child` and `+`/`~` siblings;
   - a float beside the insertion;
   - margins collapsing through the parent.
   Falsifiers, each required to fail:
   - the structural reverse index disabled;
   - P's later siblings not re-stacked;
   - an ancestor's offset not updated.
2. **Cost.** Each page's block edit at or below Chromium's, sequentially
   and at four workers, reported with the elements and entries the edit
   visited.
3. **Locality.** An insertion visits only the elements of its subtree, the
   siblings the structural reaches name, P's later children and P's
   ancestors. This is counted by the oracle.
4. **Full build.** The style and layout stages of a full build within 5
   percent of M1's (8b8612f). The nested flow is measured on every page.
5. **No regression.** Every other E1 kind at or below step 5's figures.

## Steps

1. Style state keyed by a stable key (Q90), with the full build unchanged
   in output. Check: dumps byte-identical, criterion 4.
2. Restyle of an insertion or removal without a traversal or a new style
   state: the structural reverse index, P's positions (Q94) and the new
   subtree's levels. Check: style identity against a full run after every
   block edit.
3. Nested flow entries with offsets relative to the parent block (Q104).
   Full build first. Check: layout dumps byte-identical, criterion 4.
4. The flow-range splice: build E's boxes and paragraphs alone, insert their
   entries into P, re-stack P's later children and update the ancestors'
   offsets. Check: criteria 1 and 3.
5. E2: every E1 kind against Chromium, seq and par-4. Results here; the
   rulings into the design tree.

## Decisions

These open questions go to the owner before step 1 starts, because they
set the direction of the work (design-tree skill, "Before starting").
- **Q107**, the style state's key: NodeId, approved, then reopened as Q111.
- **Q111**: a stable slot, approved. An element's slot is its preorder
  position at the last full build. An inserted element is appended and a
  removed one leaves a hole.
  - The full build keeps its code and layout, and the NodeId-to-slot map is
    the traversal's existing order map.
  - NodeId arrays would also stay parallel: the level cascade's inverse-map
    precondition and `apart` certificate prove writes through NodeIds
    distinct, at one O(n) check per pass. But they would hold every text
    node's slot (2.3 times the elements on ecma262), spread each pass's
    accesses over that many cache lines, and grow with the DOM arena, which
    only appends and cannot be compacted alone.
  - Slots grow only with inserted elements, and a compaction can renumber
    them alone. It is part of the TODO that the approval of Q89 required.
  - Not measured; the comparison follows from what each pass reads and
    writes.
- **Q108**, no traversal per edit: approved. An edit takes depths from
  parents; the preorder list is rebuilt by the next full build.
- **Q109**, nested flow entries with offsets relative to the parent block:
  approved.
- **Q110**, a structural reverse index for `:nth-*`, `+` and `~`, with P's
  positions recomputed: approved.
- **Q113**, the structural set's precision: approved (A). Astra's completeness check
  (`runs/structure-check.txt`) found the set complete but html5 naming
  58,230 elements for an insertion that changed none: `p + * > li` reached
  the `li` of every child of body, and `.status p:first-child + p > a`
  every later `a`. Recommended and implemented on that recommendation:
  - each structural reach records the side of the edit point whose
    children it reaches (previous, next, earlier, later), and
    `structural_restyle` takes the point's two neighbours and walks only
    those places;
  - each reach records the ancestor features of its left compounds, and a
    reach the parent's chain does not admit is skipped.
  Largest html5 set 58,230 → 548; the remainder is `hN + div + hM`, whose
  `div` compound reaches every later heading. Alternative: keep the
  coarse set and accept the cost (rejected by the target). Bounding a
  reach by its count of `+` hops (C) waits for step 2's measured cost
  (`docs/todo.md`).
- **Q114**, approved (A) on 2026-10-06: the nested flow's identity and order (steps 3 and 4). See
  [the layout design](layout-design.md#recommended-contract). Recommended:
  each block owns its entries in stable local slots with a block-local
  balanced order and summary index, stores its boundary outputs (size,
  baselines, margin struts, float exports) and an insertion translates only
  the direct later siblings, instead of a plain local array, whose insertion
  copies the earlier entries too, or a flat flow with a second subtree index.
- **Q115**, approved (A) on 2026-10-06: the first splice's scope. Recommended: a complete
  block-level seam with no counter, quote or inline run crossing it first,
  every other seam keeping today's rebuild as a counted fallback, and no
  fallback allowed on a timed E1 block edit, instead of supporting every
  builder state before the first local splice.

The completion review of steps 1 and 2 (a separate read-only agent, at
8e69668) found three things, each fixed before the steps merged:
- **An :nth-child of-clause hid its structural features.** The clause's
  alternatives were never queued for nested_reaches, so with
  `#ofempty > div:nth-child(1 of :empty)` an insertion into the first div
  changed which div matched and neither was rematched. They are now queued
  with reach_around; `:empty` inside a clause becomes a parent reach beyond
  the edit's parent, which `structural_restyle` answers with a full restyle.
  `incremental-style/scripts/ofclause-case` holds the case, apart from
  `structure-case`, whose bounded sets a full restyle would otherwise hide;
  the reach check fails on it at 8e69668.
- **Slot initialization ordered siblings.** Each new element appended to
  every shared row store before the next, an order the insertion does not
  need. Rows now grow once by the subtree's size, the order maps are written
  by the one sequential scatter (distinct NodeIds Whitefoot cannot yet prove
  distinct; docs/todo.md), and each new element fills its own rows, its
  depth taken from its steps up to the subtree's root.
- **Criterion 4 was measured against the wrong base.** The full-build
  comparison in runs/slots.txt used the 7ee4411 binaries rather than M1, did
  not time the parallel style stage, and its html5 par-4 layout change is
  1.95 percent, not within 1.5. The full build is measured again against M1
  on the 14900K runner (runs/full-14900k.txt).

## Step 1 and 2 in detail: stable slots and the insertion restyle

**Index spaces today.** The style state has two kinds of arrays.

- Per element, indexed by preorder position 0..E: the traversal's
  elements, parents, depths, `Styles.elements`, the pseudo flags and marks.
- Per styled node, 0..N: the cascade's winners and kinds, and the inherited
  and reset arrays. There the E elements come first and the N - E
  pseudo-elements after them (13,368 on ecma262). Code tests `n <
  element_count` for "is an element".

**Slots (Q111).** The full build keeps both spaces exactly as they are. An
insertion of a subtree with m elements and q pseudo-elements appends:

- m element slots E, E+1, ... to every per-element array: the traversal's
  elements, parents (parent slot) and depths (parent depth + 1), and the
  order map entries for the new NodeIds;
- m + q node slots N, N+1, ... to every per-node array;
- an element-to-node map for appended elements only. An element below E is
  its own node; above, the map gives its node. A kind test replaces
  `n < element_count`.

A removal marks the subtree's element slots empty: the order map entry and
the traversal's element entry name none, and they are skipped wherever a
pass lists elements. The layout reaches styles through the order map, as it
does today.

**Pseudo-element order.** `Styles.pseudos` is sorted by element and found by
binary search (`rank_in`). Appended elements' pseudo-elements go to a second
sparse list searched the same way, until the next full build merges them.

**The insertion restyle (step 2).**

1. Insert into the DOM and append the new subtree's slots (above).
2. Find the restyle set: every new element, plus
   `structural_restyle(parent)` mapped from NodeIds to slots. Use Astra's
   `structure` oracle to check that the set is complete.
3. Rematch the set; run the levels from the shallowest depth, children
   queued as Q91's frontier does; intern into the kept tables.
4. Hand layout the changed list. Its structural path stays as it is until
   step 4.

Expected effect: the style part of a block edit drops from the full stage
(114, 476 and 937 ms) to the set's size, while layout's structure + update
(16, 239 and 259 ms) remains for steps 3 and 4.

## Apollo sentence identity and sibling-margin repair

The repair compares main `8fbc160` with the current M2 line using the exact
Apollo HTML and X5 scripts preserved by hosted diagnosis run 37727037303.
Both revisions build with their own compiler pins. Sentence edits 31 and 32
must equal full rebuilds; equality on main would reject an inherited-defect
account. A reduced HTML/edit fixture must fail before the renderer repair
and pass after it. The sibling-frontier repair admits supported retained
margin changes and must be falsified by removing its settlement. The
percentage-height and grid refusals retain their existing scope. All builds
and checks run in GitHub-hosted CI, with no local validation.

The defect was in `finish_reference_scope`: it published a converged suffix
only when `scope.delta != 0`. In the captured edit, paragraph
1646 moves from y=2951.84375 to 2977.84375 and shrinks from 130 to 104 px;
following paragraph 1653 therefore stays at y=3097.84375 in the full rebuild.
Its enclosing section moves down 26 px. Skipping suffix encoding retains
paragraph 1653's old owner-relative origin, producing y=3123.84375 instead.
The repair publishes the suffix of every nonempty reference scope, including
zero displacement, through the existing direct-owner traversal. It preserves
unchanged descendant interiors and the reference arithmetic order. Restoring
the old guard reproduces both reduced-case mismatches, while the repair
restores full-build identity on the reduced and original inputs.

The reason-6 completion certifies the retained direct ordinary sibling
immediately following the seam, with unchanged horizontal geometry,
top/bottom frames, bottom margin, static positioning and height constraints.
The style delta must be boxes-only, and the current display, float, overflow
and column state must still construct a neutral plain flow block. The
sibling-context edit script requires reason 6 when first-child membership
changes the retained paragraph from a block to a flow context. The sibling's
observed natural edge must coincide with its normal origin, and an unframed
interior must expose no leading margin, preserving that equality after the change.
Its changed top margin joins the private suffix transfer before seam and
ancestor validation, so removal compares the combined structural and margin
change with the old exposed strut. Each independent suffix calculation uses
that replacement in its cached prefix, and publication writes the measured margin, transfer and
direct origin together. No retained text needs preparation or style replay.
A mutation omitting that sibling's direct move must expose stale geometry.
Other changed retained styles keep reason 6; percentage-height and grid
ancestor preflights retain their existing scope. This completes the existing
sibling-frontier contract without adding a new dependency class.

### Main comparison

Hosted run [37732411321](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37732411321)
built main `8fbc1601785cee70265da1eac4d99589fc6fb67c` with its own
`wf-0b7f5c5b9854` pin and Ubuntu Clang 22.1.8. Every sentence and block edit
matched its full rebuild in seq and par, including sentence edits 31–32.
The HTML SHA-256 was checked against the diagnosis capture and the original
scripts and stylesheets came from its preserved artifact. Main does not have
this sentence defect. The preceding attempt with default Clang 18 could not
compile that pin's LLVM syntax and supplied no rendering result.

The unchanged M2 renderer at `cf12c609`, built by run
[37731326544](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37731326544)
on diagnostic-only revision `5642361`, reproduced exactly sentence edits
31–32 as `inc DIFF` and the six original reason-6 structural edits in both
modes. That run remains intentionally failed; its main job was the Clang
prerequisite failure superseded by run 37732411321.

### Repair evidence

Hosted run [37736036220](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37736036220)
at `b86c2e90883455e46b13ff8913daeb1331653afb` passed the exact captured Apollo
sentence and block scripts, 60 edits each in seq and par. Sentence edits
31–32 now report `inc same`. The six block edits 7–8, 29–30 and 43–44 now
reach `splice 0 reason 7`: retained sibling style no longer refuses them,
but the unchanged html/body percentage-height preflight still does. This
matches the prior diagnosis's margin-control result; no percentage-height
or grid guard was relaxed.

The same run built a comparator restoring only `reference.wf` from
`cf12c609`. Both edits of
[`sentence-convergence-case.edits`](../incremental-layout/scripts/sentence-convergence-case.edits)
on its [HTML fixture](../incremental-layout/scripts/sentence-convergence-case.html)
report `inc DIFF` in the sequential pre-fix comparator and `inc same` in
both repaired seq/par drivers.
The case isolates an edited paragraph before a moved section whose inner
paragraph crosses a stationary float; suffix positions converge while the
section origin changes.

Both insertion and removal in
[`sibling-margin-case.edits`](../incremental-layout/scripts/sibling-margin-case.edits)
on its [HTML fixture](../incremental-layout/scripts/sibling-margin-case.html)
report `inc same`, `splice 1 reason 0` in seq and par. The separate
[`sibling-context-case.edits`](../incremental-layout/scripts/sibling-context-case.edits)
uses that HTML to test a first-child change that creates a formatting context;
both required reason-6 paths and full-build identity pass in seq and par.

### Final validation and review

At `b86c2e90883455e46b13ff8913daeb1331653afb`, hosted
[`make check`](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37736036284)
passed, including the DOM self-test, 21 design-checker tests and design lint.
The complete hosted
[`[oracles]` run](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37736036234)
passed all 14 jobs. Every X5 kind (word, sentence, block, colour, fontsize and
rootfont) matched full rebuilds on ecma262 and html5, with seq/par equality.
The pages' 20 and 60 block edits respectively all reported `splice 1 reason 0`
in both modes. Full-build page and layout-case dumps stayed identical to the
base, and existing case/fixture checks plus the three new edit scripts passed.
The oracle expectations and existing permitted refusals were not weakened.

The complete hosted
[`[falsify]` run](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37736036323)
passed all 46 mutation jobs and its check-machinery job on the same revision.
The new `zero-suffix` mutation restores the old reference guard; the new
`sibling-frontier` mutation suppresses the retained sibling's direct move.
Each produces `inc DIFF` on both edits of its corresponding new fixture,
while the unmutated baselines pass. Existing mutations remain detected.

One separate read-only review inspected the complete
`cf12c609..e8594aa` diff, the local counter repair through `b86c2e9`, and the
final evidence-only investigation changes. It checked groups A/D/C/T/R/M/V
and applicable G1–G3/DC1–DC4 against the pipeline, layout and relevant style
decisions, including actual CI logs and mutation evidence. All applicable
items passed within scope; node-edit and approach-retirement obligations
were inapplicable because this task changes neither. The PR clauses were
inapplicable under the owner's explicit no-PR instruction. The CI lint
reports seven nodes, depth one, 59 decisions and 24 rejections against its
main-relative base; this task changes no tree nodes. No local validation or
green-suite rerun was performed by the reviewer. General certificate
soundness beyond inspected arguments and tested cases remains unverified;
the review is not a formal proof.

The review's two findings were fixed: R1, an uncounted retained-block opening
in `splice_sibling_ready`, now charges the existing boundary counter once
per opening; R2, ambiguous pre-fix mode wording, now states explicitly that
the reduced pre-fix comparator was sequential and the repaired drivers ran
both modes. No finding remains open. The construction-state guard and its
negative fixture also keep a changed formatting context outside this margin
certificate. The sentence defect and covered sibling-frontier gap are fixed;
percentage-height and grid locality remain outside this repair as directed,
and other retained-style frontiers remain in the existing TODO.

The latest M2 head was fetched and merged before final validation; it remained
`cf12c609`, already included. Only `research/m2-apollo11-fix` was pushed and no
PR was opened. All builds and checks ran on GitHub-hosted runners. No
Whitefoot gap was encountered, and the compiler pin and submodules were
unchanged. The temporary diagnosis workflow, `apollo11-diag.yml`, last ran in
full as run 37736036220 at `b86c2e9`; it was removed when this repair was
integrated into research/m2-layout.
