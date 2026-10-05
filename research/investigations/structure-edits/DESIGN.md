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
and layout. ecma262 has about 96,000 elements and 118,000 flow entries in
one context. Any step that touches every element or every entry, at even
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
positions relative to the parent block, it is O(1) per ancestor.

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
- **Q107**, the style state's key: NodeId, approved. Reopened as Q111 when
  step 1 found that the full stage's parallel loops would then write through
  NodeIds whose distinctness Whitefoot cannot state (docs/todo.md, Whitefoot
  requirements). The recommendation is now a stable slot: an element's
  preorder position at the last full build, with inserted elements appended.
- **Q108**, no traversal per edit: approved. An edit takes depths from
  parents; the preorder list is rebuilt by the next full build.
- **Q109**, nested flow entries with offsets relative to the parent block:
  approved.
- **Q110**, a structural reverse index for `:nth-*`, `+` and `~`, with P's
  positions recomputed: approved.
