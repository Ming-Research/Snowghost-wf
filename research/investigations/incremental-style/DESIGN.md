# An incremental style stage (M1)

## Question

Can a class, style or structural edit restyle only the elements it affects,
and hand layout only those, so that the edit's cost from the edited document
to laid-out boxes follows the size of its effect instead of the page? E1
(`research/investigations/engine-comparison/runs/e1.txt`) found the style
boundary, not layout, losing on four of six edit kinds; this milestone is
the owner's choice after E1 and an architecture review (2026-10-04): M1, an
incremental style stage end to end, then M2, a flow-range splice for
structural edits with a second comparison (E2), then paint.

## Where the cost is now

- **The stage reruns in full.** `compute_styles` (`renderer/style`) runs
  matching, the level cascade, the reset pass and interning over every
  element: 0.18 to 0.62 s at four workers on the three pages, while
  Chromium's colour edit costs 25 to 35 us (E1).
- **The delta compares every element.** Each run interns into its own
  tables (Q83), so `layout_changes` maps both runs' tables by value and
  compares every element's groups: 0.8 to 3.2 ms per edit
  (`incremental-layout/runs/step4b.txt`).
- **The marking validates and walks everything.** `styles_changed`
  checks every element's and pseudo-element's construction inputs
  (`retained_styles`) and recurses over every context
  (`mark_style_context`): 3.8 ms sequentially and 27 ms at four workers on
  html5 for a colour edit that changes no layout.
- **Shared stores are global.** Custom-property sets, the resolved-value
  list, the side tables of list values and the generated text are appended
  in node order for the whole document (`Inherited`, `Styles.generated_text`),
  so a partial run has no place to put its values without the whole run's.

A colour edit's true dependency chain is one element's restyle and, at
most, one paragraph's mark. Every step above that visits the page is a step
the algorithm does not need.

## Proposal

Keep the style stage's three parts and their parallel shapes, and make
each run over a restyle set instead of the document, on state that
persists across edits:

1. The stage's per-element state (matched winners, inherited and reset
   values, computed group identifiers) is kept between edits, indexed by
   NodeId (Q90), with value tables that keep their identifiers (Q89, which
   revises Q83).
2. An edit yields a restyle set from a reverse index of the rules' features
   (Q91) and per-parent sibling positions (Q94).
3. Matching, the level cascade and the reset pass run over the restyle set,
   the cascade continuing to a child only while what it inherits changed;
   interning looks up and appends into the kept tables.
4. The stage emits a sparse list of changed elements with what changed for
   layout, which marks layout through each element's unit (Q93), replacing
   `layout_changes` and `styles_changed`'s walks.

## Decisions

Each is taken on its recommendation while the work proceeds and goes to the
owner at handoff; the dependency chains of the candidates come first, as
AGENTS.md requires.

**Q89, identifiers that survive an edit (Q83 revisited).** Candidates:
- *Per-run tables mapped by value* (Q83, now): every edit interns all
  elements, classifies both runs' tables and compares every element. The
  chain is the whole page, by construction.
- *Kept tables with stable identifiers*: an edit looks each restyled
  element's groups up in the kept tables (independent reads), then appends
  the values not found, in one sequential pass over the misses, which
  assigns their identifiers. The chain is the restyle set's misses; the
  tables grow with the distinct values a session meets.
- *Identifiers by content hash*: no shared table on any path, the shortest
  chain; but two values with one hash would compare equal, which no proof
  rules out, and a wrong cutoff renders stale output silently.
Recommended: kept tables, compacted rarely (an epoch that renumbers every
table and every holder of an identifier, with a full key check), because
layout's keys (Q69) hold group identifiers and stay valid across a restyle
without any mapping, so the whole-page delta disappears. Q83's grounds
(tables grow; each run waits on the last) held for a full rerun; for a
restyle set the wait is over the misses only. The same kept-table treatment
covers the custom-property sets, the side tables of list values and the
generated text, each interned by content instead of appended per run.

**Q90, where per-element style state lives.** Candidates:
- *Arrays in preorder with an order map* (Q67's map, now): an insertion
  shifts every later element's slot in every array, O(elements) writes per
  structural edit, or rebuilds them.
- *Arrays indexed by NodeId*: the DOM arena only appends, so no slot ever
  moves; a full build writes slot `elements[i]` for each preorder position,
  and a restyle writes the slots of its own list. Both are writes through
  indices the program knows distinct, which the level cascade already
  proves with Whitefoot's range facts and `apart` (style investigation,
  The level cascade); arrays are sized by the node count, text nodes
  included.
Recommended: NodeId, keeping preorder only for the lists a pass iterates
(levels, the restyle set), because no structural edit then moves any
state; the memory for non-element slots is measured.

**Q91, the restyle set.** Candidates:
- *The edited element's subtree rematched*: every element of the subtree
  independent, then the cascade level by level inside it. A class toggled
  on `body` or `html`, the commonest site-wide style edit, rematches the
  page.
- *A reverse index of rule features* (Blink's invalidation sets, Stylo's
  invalidation map): built once with the rules, from each feature (class,
  id, attribute, type) in a compound that is not the subject to the rules
  and the combinator that names it; an edit looks up its changed features
  and finds the elements the named rules could now match or stop matching
  (descendants for descendant and child combinators, later siblings for
  sibling combinators), each test independent. Over-approximates with
  `:has()` and `:nth-*`, which the census met once in 406 samples.
- *Read sets reflected from effect rows*: needs a Whitefoot facility that
  does not exist (incremental research tree, 1.1).
Recommended: the reverse index for whose matching can change, and the
level cascade restricted to a frontier for whose inherited values change:
a child joins the frontier only when its parent's inherited values (font,
text, custom set, the inherited table and content longhands) got different
identifiers. One more fact per element, recorded by the reset pass,
says whether a value it does not inherit depends on font size (em, rem,
ex, ch, lh), so that a root or parent font change re-resets only those.

**Q92, the stage's shared stores.** The custom-property sets, the
resolved-value list and the side tables are written in node order by the
nodes outside the level loops. Candidates: keep them global and rebuild
them per edit (a whole-page chain again); give each node its own slots
(no sharing, more memory); intern them as kept tables (Q89). Recommended:
per-node slots for what a node alone reads (its resolved pending values),
kept tables for what nodes share by value (custom sets, list values,
generated text), so equal content keeps one identifier across edits.

**Q93, from style to layout.** Candidates:
- *A dense flag per element and whole-tree validation and marking* (now):
  O(page) twice per edit.
- *A sparse list of changed elements* `(NodeId, layout groups changed,
  box construction affected)`, each marking layout through a map from the
  element to the unit that holds its boxes, as `text_changed` marks through
  a text node's `TextUnit`. Marking from several elements writes shared
  ancestors, so that loop is sequential over the list (tens of entries,
  microseconds); the update's recursion over marked subtrees is unchanged
  (Q71).
Recommended: the sparse list. An element whose box construction inputs
changed (display, position, float, generated content, list markers) routes
to the structural path instead of being refused after a whole-tree check,
and the producer guarantees what `retained_styles` checks today. The
element-to-unit map is recorded by the box tree's walk and kept by
NodeId, like the text units.

**Q94, sibling positions.** `sibling_positions` walks the whole document
once per run for `:nth-*`. Recommended: positions recomputed for the
children of a parent whose children changed, since an insertion or removal
changes them for that parent alone; the table is already indexed by
NodeId.

## Criterion

Written before any implementation run. On the X5 pages and the E1 harness,
same host and Chromium build:

1. **Identity.** Every edit of X5's scripts (word, sentence, colour,
   fontsize, rootfont, block), of `style-case` and `block-case`, and of a
   new `body` class toggle script, `inc same` in seq and par, outputs equal;
   the style oracle's dump after every edit equal to a full style run's.
   Falsifiers, each required to fail: the reverse index disabled (a rule
   whose non-subject compound names the toggled class); the inherited
   cutoff taken on an unchanged font group while the custom set changed;
   one element of the changed list not marked in layout.
2. **Cost.** Colour and fontsize class edits within 2 times Chromium's
   sequentially on all three pages; a root font-size edit at or below
   Chromium's at four workers; reported at seq, par-1 and par-4 with the
   restyle set's size.
3. **Locality.** A colour edit visits, in style and layout together, no
   element or context outside its restyle set and their ancestors (counted
   by the oracle); toggling a class that no rule names restyles nothing.
4. **Full build.** The style and layout stages of a full build within 5
   percent of main's.

## Steps

1. Kept, NodeId-indexed style state and kept tables (Q89, Q90, Q92) in the
   full build. Check: the style and layout dumps unchanged; criterion 4.
2. The reverse rule index, per-parent positions and the restyle set (Q91,
   Q94), checked against a full run: the set must contain every element
   whose computed style a full run changes.
3. The partial passes and the inherited cutoff. Check: criterion 1's style
   part.
4. The sparse interface and the element-to-unit map (Q93), retiring
   `layout_changes`, `retained_styles` and `mark_style_context`. Check:
   criterion 1 and 3.
5. E1's kinds and the `body` toggle against Chromium; criterion 2;
   results here and the rulings into `design/pipeline/style.md` and
   `layout.md`.

## Risks

- Proving the restyle passes' writes disjoint over a list the pass builds
  needs the same facts the level cascade derives, now for a list; if
  Whitefoot cannot state them for a sparse list, that is a Whitefoot
  requirement, not a reason to serialize.
- `:has()` is out of the style stage's scope today; the reverse index must
  stay correct by refusing (a full restyle) any edit whose features it
  cannot bound.
- The four-worker runtime's fixed cost on sub-millisecond work (a Whitefoot
  requirement in `docs/todo.md`) may hide the gain at par-4; par-1 and seq
  separate it.

## Results

- **Step 1** (`runs/step1.txt`). The value tables of the eleven groups and
  the list tables they name are kept in `Styles` and a full build fills
  them from empty: every style and layout dump and every table size equals
  main's on the three pages and four case pages, seq and par; a variant that
  forces the tables to grow agrees, and one that loses entries on growth
  fails the table sizes while the dumps cannot see it. The full build is
  within 5 percent (at most +3.3%, ecma262 at four workers). Two parts of
  step 1 moved: the custom-property sets name sets of the inherited pass's
  per-run store, so their kept table comes with that store in step 3; and
  Q90's NodeId-indexed state only matters once an edit moves preorder
  positions, which no edit of M1 does before structural edits, so it is
  proposed for M2.
