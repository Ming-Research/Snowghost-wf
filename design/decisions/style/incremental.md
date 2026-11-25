# Incremental style

How the style stage keeps its state across edits, which elements an edit restyles, and what it tells layout.

### decision style-state-kept-across-edits
Each group's table keeps its identifiers across edits, and an edit's restyled nodes look their values up and append the ones not found, so layout's keys stay valid without a whole-page delta.
- replaced: Tables made for each run and mapped by value between runs was on main; the owner changed it, because once a restyle covers only the elements an edit reaches, interning and comparing the whole page on every edit is the main cost and an order the restyle does not need.
- rejected: an agent proposed identifiers made from a hash of the content; the owner rejected it, because two values with one hash would compare equal, and no proof rules that out.
- rejected: an agent proposed comparing every element's style values deeply, with no table; the owner rejected it, because it failed the root-font criterion at four workers on ecma262, 217 against 3 ms per colour edit (data: `research/investigations/incremental-layout/DESIGN.md`).

### decision style-rows-are-stable-slots
An element's row is its preorder place at the last full build; an insertion appends rows, a removal leaves holes the passes skip, and new elements take their depth from their parents.
- replaced: Rows in preorder that every insertion shifts was on main; the owner changed it, because with slots no row moves, the full build keeps its order and parallel loops, and a block edit's style work follows the set it restyles (data: `research/investigations/structure-edits/runs/slots.txt`).
- rejected: an agent proposed rows indexed by `NodeId`; the owner rejected it, because they hold a row for every text node, 2.3 times the elements on ecma262, and grow with the document's node array, which cannot be compacted alone.

### decision class-edits-restyle-through-a-reverse-index
A class edit restyles the elements a reverse index of the rules' class features names, and the level cascade goes on to a child only while what it inherits, or its own style, changed.
- rejected: an agent proposed rematching the edited element's subtree; the owner rejected it, because for a class on `body` that rematches the page, while the index names just the elements whose winners or inputs can change (data: `research/investigations/incremental-style/runs/step3.txt`).

### decision insertions-restyle-through-a-structural-index
An insertion or removal rematches, beside the inserted subtree, only the siblings that a structural reverse index of position pseudo-classes, sibling combinators and `:empty` can reach.
- rejected: an agent proposed rematching the parent's children and their subtrees; the owner rejected it, because on html5 it named 58,230 elements for an insertion that changed none, against 548 with sides and context (data: `research/investigations/structure-edits/runs/structure-check.txt`).

### decision style-tells-layout-a-sparse-list
The style stage hands layout a sparse list of the elements whose computed style changed in what layout reads, and says apart whether an input of box construction changed.
- replaced: A flag per element, with whole-tree checking and marking, was on main; the owner changed it, because that is two page-sized walks per edit, while a sparse list costs only the changed elements and their context paths.

### decision style-attributes-found-by-node-id
Style attribute and presentational hint declarations are parsed once at load and found by the element's `NodeId` through a dense index.
- rejected: an agent proposed parsing them again after every edit; the owner rejected it, because that parses every style attribute on every frame, while an insertion leaves each element's `NodeId`, and so its declarations, in place.

### decision root-font-edits-restyle-their-readers
A root font-size change restyles through the level cascade only the elements whose winning declarations can read the root's size, and rebuilds without matching past a sixty-fourth of the elements.
- replaced: Rebuilding every node on every root font-size change was on main; the owner changed it, because only those elements and the inherited font chain read the root's size, and ecma262's edit went from 989 to 14 ms (data: `research/investigations/incremental-style/runs/rootfont.txt`).
