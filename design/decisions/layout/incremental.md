# Incremental layout

How a layout kept across edits names elements, learns what an edit changed, decides what to redo, and re-stacks a flow.

### decision layout-names-elements-by-node-id
Layout names an element by its `NodeId`, resolved to the style stage's preorder place through an order map each style run rebuilds.
- replaced: Preorder positions as layout's names for elements was on main; the owner changed it, because an insertion shifts the position of every later element, while a `NodeId` lasts the node's life, so an insertion renumbers nothing a kept layout holds.
- rejected: an agent proposed renumbering a kept tree's element positions after an insertion; the owner rejected it, because every later element's position changes, so an insertion would touch the whole tree.

### decision edits-reach-layout-as-pushed-marks
An edit reaches a kept layout as marks pushed from what it changed toward the root, and an update recurses only into marked subtrees, so a frame with no change costs one test.
- rejected: an agent proposed scanning versions densely every frame, or walking memo keys; the owner rejected it, because a frame with no change should cost one test, while walking memo keys cost 2.3 to 2.6 ms a frame (data: `research/investigations/incremental/experiments/x12/report.md`).

### decision redo-only-what-a-key-says-changed
A kept context or paragraph is redone only when its key of layout-relevant style groups, space and entry state changed, and propagation stops where a context's outer sizes come out the same.
- rejected: an agent proposed the whole style as the key; the owner rejected it, because then colour and custom properties change paragraphs too, and a paragraph was redone on 27 of 30 colour edits (data: `research/investigations/incremental/experiments/x1-x3-x16/agg-apollo11.md`).

### decision later-entries-move-by-one-delta
Offsets stay relative to the context's border box, and an update moves the entries after a changed one by one delta when its exit margins hold and no float reaches past it.
- rejected: an agent proposed offsets relative to the parent, or a summary tree of offsets; the owner rejected it, because every reader would pay for them on every full build, and the walk from the edit fits its budget (data: `research/investigations/incremental/experiments/x1-x3-x16/report.md`).

### decision structural-edits-rebuild-one-context
An insertion or removal builds again the nearest context at or above the changed parent from the walk's state recorded there, and falls back to a full build when that state would change.
- replaced: Building the whole layout again after every insertion or removal was on main; the owner changed it, because counters and quotes are the only state the walk carries from one context to the next, so one context can be built again from its recorded entry.
- rejected: an agent proposed routing every context through stable per-source paths; the owner rejected it, because that adds a routing layer to every update.

### decision restack-the-smallest-common-block
A style edit that changes blocks inside one flow re-stacks only the smallest block that holds them, keeping widths that did not change.
- replaced: Preparing and stacking the whole context on a style edit was on main; the owner changed it, because widths depend on ancestors, not siblings, and preparing the whole context made html5's font-size edit 10 ms (data: `research/investigations/incremental-style/runs/restack-astra.txt`).

### decision restack-resumes-after-a-paragraph-with-lines
A partial re-stack resumes after the preceding unchanged paragraph with lines, whose position, ancestors and preceding floats give the stacking state.
- replaced: Replaying the flow from its start was on main; the owner changed it, because pending margins are settled after a paragraph with lines, so its geometry gives the state (data: `research/investigations/incremental-style/runs/restack-astra.txt`).
- rejected: an agent proposed snapshots of the stacking state at sparse places in the flow; the owner rejected it, because resuming after a paragraph with lines recovers the same state from geometry already kept, with no state to invalidate.

### decision child-style-changes-mark-the-child
A child context's own style change marks the child for its parent flow to settle at the child's entry; flex, grid and table parents are marked restyled instead.
- replaced: Marking the parent flow restyled was on main; the owner changed it, because a flow reads a child's style only where it places it, and marking the flow prepared all of ecma262's main flow for one edit (data: `research/investigations/incremental-style/runs/fontsize-fable.txt`).

### decision restack-translates-inline-fragments
A re-stack whose later entries all moved by one delta translates the context's inline-box fragments, when no split inline box opens or closes in the range, instead of making them again.
- replaced: Making the inline-box fragments again after every re-stack was on main; the owner changed it, because each fragment lies wholly before, around or after the range, and remaking them cost 0.8 ms of an ecma262 edit (data: `research/investigations/incremental-style/runs/fontsize-fable.txt`).
