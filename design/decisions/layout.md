# Layout

The layout stage: the tree of formatting contexts it keeps, where each context's geometry is written, and when intrinsic sizes are computed.

### decision an-owned-tree-of-formatting-contexts
Layout keeps an owned tree of formatting contexts, and breaks every paragraph into lines in one counted loop before the block pass places floats and breaks again only the paragraphs a float narrows.
- rejected: an agent proposed breaking lines in parallel only in contexts with no float; the owner rejected it, because the main context holds a float on two of the three pages, and lines need no float placed until those beside one (data: `research/investigations/concurrency/DESIGN.md`).

### decision geometry-relative-to-the-context
Each formatting context writes its boxes, line boxes and fragments as offsets from its own border box, and only the walk that dumps or paints computes absolute positions.
- rejected: an agent proposed absolute positions written during layout; the owner rejected it, because a context could then not be laid out before all its ancestors were placed, while relative offsets let sibling contexts lay out on their own.

### decision intrinsic-sizes-on-demand
A context computes its min-content and max-content sizes only when a parent's algorithm needs them, its child contexts' in one counted loop, and keeps them.
- rejected: an agent proposed one bottom-up pass over every context; the owner rejected it, because it computes sizes that most block-level contexts never read.
- rejected: an agent proposed recursion that halves runs of sibling contexts; the owner rejected it, because the runtime's fixed recursion budget runs out under wide sibling runs.
