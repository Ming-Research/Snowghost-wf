# Structural edits that cost what they insert (M2)

## Question

Can inserting or removing an element restyle and lay out only what the
insertion reaches, so that E1's block edit costs no more than Chromium's
(0.30, 3.06 and 0.12 ms on apollo11, html5 and ecma262,
`research/investigations/engine-comparison/runs/e1.txt`)? This is M2 of the
plan in `research/investigations/incremental-style/DESIGN.md`: a flow-range
splice for structural edits. The owner's goal of leading Chromium on every E1
edit kind before paint makes it the next milestone.

## Where the cost is now

Measured with the layout driver's edittime mode. The setup:

- `run.sh time seq PAGE block 1` with ALONE=1;
- the result of `research/investigations/incremental-style/runs/rootfont.txt`;
- Apple M1 Pro, sequential build.

Medians of the first two edits, in ms, for each part of a B edit (insert a
paragraph):

| page     | full style | full delta | structure + update | Chromium |
|----------|------------|------------|--------------------|----------|
| apollo11 | 114        | 4.3        | 16                 | 0.30     |
| html5    | 476        | 77         | 239                | 3.06     |
| ecma262  | 937        | 86         | 259                | 0.12     |

`apply_structure_edit` (`renderer/oracle/layout/edit.wf`) makes the cost
grow with the page in three places:

- **A new style state for the page.** It builds the traversal again and
  runs the whole style stage, because every per-element array is indexed by
  preorder position (Q90 of M1). An insertion moves the position of every
  later element.
- **A full delta.** `layout_changes` compares every element's groups
  across the two runs.
- **The nearest context built again.** `structure_changed` rebuilds the
  context that holds the inserted block's parent. On html5 that is the
  body's flow: 13,842 contexts and 60,869 paragraphs, 59,243 of them
  reused. The update then walks its 106,000 flow entries.

What an insertion actually depends on:

- the new element's own matching and computation, which read its parent's
  inherited values;
- the siblings whose matching reads their position or their neighbours:
  `:nth-*`, `:first-child`, `:last-child`, `+` and `~`;
- one flow-range splice:
  - new boxes and paragraphs for the new subtree;
  - stacking from the insertion point until the following blocks have only
    moved.

Every other step above visits the page.

## Candidates (to be written out with their dependencies before choosing)

1. **Style state that an insertion does not move.**
   - Arrays indexed by NodeId (M1's Q90 recommendation): the DOM arena only
     appends, so no slot moves.
   - Alternatively, preorder arrays with an insertion that shifts every
     later slot, O(elements) per edit.
2. **The restyle set of an insertion.** The new subtree, plus the siblings
   and sibling descendants that the reverse index's structural reaches
   name (position pseudo-classes and sibling combinators). Sibling
   positions are recomputed for the one parent whose children changed
   (Q94).
3. **The traversal.**
   - Patched for the inserted subtree: its preorder range and depths, and
     the parent's child list.
   - Alternatively, built again, which is O(elements) but parallel.
4. **The flow-range splice.**
   - Build the new subtree's boxes and paragraphs alone and splice their
     entries into the parent flow.
   - Then re-stack from the insertion point with the re-stack machinery of
     M1 (`restack_block` and resume after the preceding paragraph), which
     stops once later blocks only move.
   - The remaining O(suffix) move of later entries is the same cost that
     keeps ecma262's font-size edit above Chromium
     (`incremental-style/runs/fontsize-fable.txt`). It is a shared
     candidate: block positions relative to their parent block, so a moved
     block carries its subtree.

## Criterion

Not yet written. It will be written before any implementation run, as M1's
was: identity of every incremental dump against a full rebuild on X5's
block scripts and the block case pages, and E1 timings against Chromium.
