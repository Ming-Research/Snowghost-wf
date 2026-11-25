# Boxes

How layout builds its box tree from the document and styles, and where counters and quotes get their values.

### decision the-box-tree-walk-records-text-pieces
The box tree is built by one walk of the document in tree order that records each paragraph's text as pieces, which each paragraph decodes and collapses later in a counted loop.
- replaced: Decoding and collapsing text during the walk was on main; the owner changed it, because it kept four fifths of the builder's work in the walk's chain, and what is left to gain is under 1 percent of the pipeline (data: `research/investigations/concurrency/DESIGN.md`).

### decision counters-resolved-in-the-box-tree-walk
Counter and quote values are resolved by the box tree builder's walk as it visits each element in tree order, every list item adding one to `list-item`.
- replaced: A separate pass in document order in the style stage, over only the elements that change or read a counter, was on main; the owner changed it, because the box tree's walk already visits every element in that order, so the pass would be a second chain over them.
- rejected: an agent proposed a parallel scan over counter scopes; the owner rejected it, because a counter's value is a true chain in document order, and the pages' sheets read counters in 4 to 10 places, too few to pay for the scan's bookkeeping.
