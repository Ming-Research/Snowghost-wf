# Shared vocabulary

Status: draft for the owner. Nothing here is decided; the probes are
evidence, and the proposals become design-tree amendments only after the
owner's ruling.

## Question

How does the renderer store its document, styles, boxes and fragments, and
what types do all its stages share, so that every stage is incremental and
parallel by formatting context (the `pipeline` tree) and Whitefoot can prove
the parallel work independent? This vocabulary is the part of the renderer
that is most expensive to change later (architecture study, "Division of
work"), and the first milestone, headless static rendering, needs it before
any stage can be written.

## Constraints from Whitefoot

- References are never stored (`design/language/ownership/no-stored-references`
  in Whitefoot): a tree is either owned (`Box`, `Box<Slots<T>>`) or an arena
  whose links are indices.
- Parallel work is proved from effects: two calls overlap when their writes
  are disjoint places, and a counted loop runs as an independent map when
  each iteration writes only its own slot (PAR-1, EFF-5, OWN-7).
- A value is released at its owner's scope exit, so an owned tree kept
  across frames keeps its results with no collector.

## Probes

Both compile with the pinned compiler (`whitefootc --par --par-ledger`):

- `owned-tree-probe.wf`: an n-ary tree whose node owns its children in a
  `Box<Slots<Unit>>`, laid out by recursion that splits a sibling run into
  halves. The ledger reports `PAR permitted pair(lay_out_run, lay_out_run)`:
  the two halves run in parallel with no annotation, under a runtime-derived
  recursion budget.
- `level-loop-probe.wf`: one tree level of a cascade as a counted loop whose
  iteration k reads the level's inputs and writes only slot k. The ledger
  reports `PAR loop permitted` and splits it as an independent map.

The probe also found a checker gap: two range references written directly as
call arguments do not get their REF-4 lengths related (`&a[0..n]` and
`&b[0..n]` are not proved equal), while named ranges are. Whitefoot PR #167
fixes it; until it merges, bind each range with `let` first.

## Proposal

1. **Two storage regimes.**
   - **The document is an arena.** Nodes live in a `Box<Slots<Node>>` indexed
     by `NodeId`, a `u32` index, with parent, first child, last child and
     sibling links as indices. Script and the parser need random access by
     identity and mutation anywhere, which an owned tree cannot give.
   - **Layout data is an owned tree of formatting contexts.** Each formatting
     context owns its boxes, its fragments and its child formatting contexts
     (`Box<Slots<FormattingContext>>`). The tree persists across frames. Each
     node keeps the inputs of its last layout (its constraints and its style
     and content versions) next to its result, which is the memoization the
     `pipeline` tree requires. A node whose inputs are unchanged returns its
     result without descending. Siblings are laid out in parallel by halving
     the run, as the owned-tree probe shows.
2. **Stage outputs are dense arrays in traversal order.** Style is computed
   level by level: the elements of one tree level sit contiguously in a level
   array, and one counted loop computes the level with each iteration writing
   its own slot, as the level-loop probe shows. Writing through an index
   array (`styles[order[k]]`) would need a proof that `order` is a
   permutation, which Whitefoot does not derive, so outputs are written in
   traversal order and read back through the order map.
3. **Layout units are fixed point.** `LayoutUnit` is an `i32` in 1/64 of a
   CSS pixel, as in Blink: about 33 million pixels of range, exact addition
   and comparison, and layouts that do not depend on floating-point rounding.
   Geometry (`Point`, `Size`, `Rect`, `Sides`) is built on it; conversion
   from CSS lengths rounds once, at computed-value time.
4. **Computed styles are interned.** Computed values are grouped (box, text,
   font, background, border, margin and padding, position), each group
   interned in a style store and named by a `u32` identifier. An element's
   computed style is a small struct of group identifiers, so equal styles
   share storage and a style comparison is a comparison of identifiers.
   Inheritance copies an identifier.
5. **Text is WTF-8 and names are atoms.** Text content lives in byte arenas
   addressed by spans, encoded as WTF-8: UTF-8 that also encodes lone
   surrogates, as Servo stores DOM strings. Script's strings are UTF-16 and
   may hold a lone surrogate that the document must keep, while every other
   stage reads UTF-8; consumers that follow the CSS or HTML preprocessing
   rules already turn a surrogate into U+FFFD. Tag, attribute and property names are atoms:
   `u32` indices into an atom table, with the names the renderer knows given
   fixed indices by a generated table, so comparing a name is comparing an
   integer.
6. **The display list is flat per stacking context.** Paint emits, per
   stacking context, an array of items (rectangles, borders, text runs,
   images) that refer to clip and transform nodes by index, and to fonts and
   images by resource identifier. The renderer-shell format is these arrays
   serialized with a version header into shared memory; the incremental
   pipeline sends only the stacking contexts that changed.

## Open questions

- **Tree levels versus formatting contexts for style.** Level-order style is
  simple and parallel, but a mutation deep in a large page recomputes one
  element per level down its subtree; cascading per formatting context would
  make style follow the same unit as layout. The first style prototype
  measures both.
- **Fragment storage.** Whether fragments live inside each formatting
  context's node (simple, local) or in per-frame arrays handed to paint
  (easier to send to the shell) is decided by the first paint prototype.
- **Floats and margin collapsing** couple the boxes inside one block
  formatting context; the owned tree keeps that sequential work inside one
  node. The first block layout prototype confirms the node boundary.

## First steps

- Write `pkg::base::geometry` (`LayoutUnit` and the geometry types) and
  `pkg::base::atom` as the first vocabulary modules, with their interfaces
  reviewed by the owner.
- Write the document arena `pkg::dom` with the interface the HTML tree
  builder needs, so the HTML tokenizer and tree builder can be implemented
  against html5lib-tests as implementer leaves.
- Build a prototype of the owned formatting-context tree with block layout
  only, measure parallel speedup on a large synthetic page, and record it
  here.
