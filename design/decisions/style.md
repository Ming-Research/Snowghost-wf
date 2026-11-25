# Style

The style stage: how it matches rules, cascades and computes each element's values, in which order, and what it hands layout.

### decision style-runs-in-three-parts
Style matches and picks each element's winning declarations in one counted loop, cascades what the parent decides level by level, then computes the other values in a second counted loop.
- replaced: One pass in document order that cascades, computes and inherits everything was on main; the owner changed it, because only the font size, the custom properties and the inherited values depend on the parent, and the rest of that pass lengthens the one sequential chain.
- replaced: One pass in document order for what the parent decides was on main; the owner changed it, because it orders siblings that depend only on their parent, a chain as long as the page, where levels make it the depth (data: `research/investigations/style/runs/level-cascade-time-after.txt`).
- rejected: an agent proposed one loop over a level's nodes with the shared stores behind a lock or merged after each level; the owner rejected it, because it orders the few nodes that write those stores against all others, and Whitefoot has no lock a counted loop may take.
- rejected: an agent proposed a cache of `var()` substitutions shared across elements; the owner rejected it, because every element would read and write it, which orders elements that do not depend on each other.
- rejected: an agent proposed storing styles in level order, one counted loop per level; the owner rejected it, because every reader in document order would need a second order map, while it came within 5 percent of document order (data: `research/investigations/concurrency/DESIGN.md`).
- rejected: an agent proposed recursion that halves each run of siblings; the owner rejected it, because the runtime's fixed recursion budget runs out under the wide sibling runs of real pages: 1.11 times on apollo11 against 3.62 (data: `research/investigations/concurrency/DESIGN.md`).
- rejected: an agent proposed cascading per formatting context; the owner rejected it, because the pipeline keeps no unit of parallel work, and an element's cascade depends on its parent, not on its formatting context.

### decision pseudo-elements-in-a-sparse-list
The first loop also matches rules for `::before` and `::after`, and each generated box's style goes into a sparse list in document order beside the elements' styles.
- rejected: an agent proposed a pseudo-element slot for every element, or generated boxes mixed into the element index; the owner rejected it, because most elements generate none, and every consumer and the oracle read the element index.
