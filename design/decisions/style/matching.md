# Matching

Which selectors the style stage tests against each element, and the tables it reads to test them.

### decision rules-indexed-per-alternative
An element is tested only against the selector alternatives that its id, class words or local name select through an index of each alternative's rightmost compound, plus those that name none.
- replaced: Testing every rule on each element was on main; the owner changed it, because an alternative whose rightmost compound names another id, class or type cannot match, and testing all cost 590 tests per element (data: `research/investigations/concurrency/DESIGN.md`).
- replaced: An index of whole rules was on main; the owner changed it, because it tested every alternative of a rule one alternative selected, and items per alternative made the sequential stage 1.4 to 2.0 times faster (data: `research/investigations/incremental-style/runs/matching.txt`).

### decision a-bloom-filter-of-ancestor-features
Before an alternative is matched, a 256-bit Bloom filter of the features of the element and its ancestors rejects a rule that needs a feature the filter lacks; each element builds its own.
- replaced: Walking the ancestors for every descendant combinator was on main; the owner changed it, because the filter halved a class edit's restyle on apollo11 and saves a third of the full stage, with the same rules matched (data: `research/investigations/incremental-style/runs/matching.txt`).
- rejected: an agent proposed a 1024-bit filter; the owner rejected it, because it measured slower (data: `research/investigations/incremental-style/runs/matching.txt`).

### decision sibling-positions-from-one-table
Matching reads each element's place among its siblings, and among its siblings of its type, and its class words, from one table built before matching.
- replaced: Counting siblings at each `:nth-child` or `:nth-of-type` test was on main; the owner changed it, because its cost grew with the element's place, and the table made html5's style stage 4.1 times faster (data: `research/investigations/concurrency/DESIGN.md`).
