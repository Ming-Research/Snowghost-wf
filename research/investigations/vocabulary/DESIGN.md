# Shared vocabulary

Status: revised after the concurrency investigation and brought to the
owner. Proposals 1 to 5 are in the design tree as draft decisions
(`design/vocabulary.md`, `design/pipeline/style.md` and
`design/pipeline/layout.md`), each awaiting the owner's ruling; proposal 6
waits for the first paint prototype. Nothing here is decided until the log
records the ruling.

## Question

How does the renderer store its document, styles, boxes and fragments, and
what types do all its stages share, so that every stage is incremental and
parallel along its true data dependencies (the `pipeline` tree) and
Whitefoot can prove the parallel work independent? This vocabulary is the
part of the renderer that is most expensive to change later (architecture
study, "Division of work"), and the first milestone, headless static
rendering, needs it before any stage can be written.

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
`&b[0..n]` are not proved equal), while named ranges are. It is being fixed
in Whitefoot alongside the range-length diagnostic work.

## Proposal

Each item says what the concurrency investigation's measurements changed and
where its draft decision stands.

1. **Two storage regimes.**
   - **The document is an arena.** Nodes live in a `Box<Slots<Node>>` indexed
     by `NodeId`, a `u32` index, with parent, first child, last child and
     sibling links as indices. Script and the parser need random access by
     identity and mutation anywhere, which an owned tree cannot give.
     `pkg::dom` implements it, and the HTML tree builder, judged
     by the tree-construction tests (`make oracle-html-tree`), builds on it. Draft decision in `design/vocabulary.md`.
   - **Layout data is an owned tree of formatting contexts.** The layout
     measurement retired the context as the unit of parallel work: one block
     formatting context holds 85 to 95 percent of each real page's text, so
     the parallel work is the paragraphs inside it, broken in one counted
     loop before floats are placed. The prototype still stores the owned
     tree, and nothing measured argues against it as storage for static
     rendering; whether a context is also the unit of memoization and
     invalidation is the open question the first incremental prototype
     decides. Draft decision, provisional, in `design/pipeline/layout.md`.
2. **Stage outputs in document order.** Superseded. The style measurement
   compared the level order proposed here (A) with halving the preorder (B)
   and with matching every element in one counted loop in document order
   followed by a cascade pass in document order (C). Its criterion 1 adopted
   C: 0.790 s at four workers against 0.810 s for A and 1.107 s for B on the
   median real page, and C needs no second order map. A rule index then
   made the style stage at four workers 1.3 to 3.2 times faster on the three
   real pages, and a table of sibling positions a further 4.1 times on
   html5, each measured against its predecessor in one run. Draft decisions in `design/pipeline/style.md`. Writing through an
   index array (`styles[order[k]]`) still needs a permutation proof
   Whitefoot does not derive, so every stage writes its outputs in the order
   it computes them.
3. **Layout units are fixed point.** `LayoutUnit` is an `i32` in 1/64 of a
   CSS pixel, as in Blink: about 33 million pixels of range, exact addition
   and comparison, and layouts that do not depend on floating-point rounding.
   `pkg::base::geometry` implements it with `Point`, `Size`, `Rect` and
   `Sides`; conversion from CSS lengths rounds once, at computed-value time.
   Nothing measured bears on it. Draft decision in `design/vocabulary.md`.
4. **Computed styles are interned.** Computed values are grouped (box, text,
   font, background, border, margin and padding, position), each group
   interned in a style store and named by a `u32` identifier. An element's
   computed style is a small struct of group identifiers, so equal styles
   share storage and a style comparison is a comparison of identifiers.
   Inheritance copies an identifier. The style measurement's criterion 2
   adopted interning as one sequential pass after the style stage, which
   cost at most 4.6 percent of the four-worker style stage then. The rule
   index made that stage three times faster on ecma262 and html5 without
   changing the pass, which is now about 14 to 16 percent of it, at the
   criterion's 15 percent bound, so the pass is measured again on the real
   style stage. The groups themselves are the proposal's and are revisited
   when real computed values replace the prototype's four placeholder
   groups. Draft decision, provisional on both, in `design/vocabulary.md`.
5. **Text is UTF-8 and names are atoms.** Text content lives in one byte
   arena per document addressed by `u32` spans. `pkg::dom` stores UTF-8; the
   widening to WTF-8, UTF-8 that also encodes lone surrogates as Servo
   stores DOM strings, is needed only when script can store a lone
   surrogate, so it waits for script. Tag, attribute and property names are
   atoms: `u32` indices into an atom table, with the names the renderer
   knows given fixed indices by a generated table (`pkg::base::atom` and
   `pkg::base::static_atoms`). Draft decisions in `design/vocabulary.md`.
6. **The display list is flat per stacking context.** Paint emits, per
   stacking context, an array of items (rectangles, borders, text runs,
   images) that refer to clip and transform nodes by index, and to fonts and
   images by resource identifier. The renderer-shell format is these arrays
   serialized with a version header into shared memory; the incremental
   pipeline sends only the stacking contexts that changed. Unchanged and not
   in the tree: no measurement bears on it, and the first paint prototype
   decides it with fragment storage.

## Open questions

- **Tree levels versus formatting contexts for style.** Answered in the
  draft: neither.
  Style matches in document order (proposal 2), and an element's cascade
  depends on its parent, not on its formatting context.
- **Fragment storage.** Whether fragments live inside each formatting
  context's node (simple, local) or in per-frame arrays handed to paint
  (easier to send to the shell) is decided by the first paint prototype.
- **Floats and margin collapsing.** Answered in the draft for layout's
  parallel work:
  paragraphs are broken before floats are placed and broken again exactly
  where a float narrows them (the `pipeline` tree), and the block pass is
  the only sequential chain; the fix-up broke again at most 0.52 percent of
  the paragraphs on the measured pages. `clear` and floats pushing each
  other are not yet modelled.
- **The unit of memoization and invalidation.** Open; see the concurrency
  investigation's open question. The first incremental prototype decides
  it.
- **The cascade pass's order.** The cascade runs in document order, which
  orders siblings that depend only on their common parent. Its share of the
  style stage is not measured; when real computed values make it
  substantial, cascading each tree level, or each parent's children, in a
  counted loop is the alternative.

## Next steps

The first vocabulary modules are written: `pkg::base::geometry`,
`pkg::base::atom` and `pkg::dom`, with the HTML tokenizer and tree builder
built against them. After the owner's ruling on the draft decisions, the
first milestone, headless static rendering, needs the stages in order:

- the style stage with real computed values: specificity, importance and
  origin in the cascade, inheritance and the properties block and inline
  layout read, grown from the style prototype's shape C;
- box tree construction and block and inline layout with real text
  shaping from `pkg::font`, grown from the layout prototype;
- paint to the display list of proposal 6, with fragment storage decided
  there.
