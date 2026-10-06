# Known defects and follow-up work

Items the work has found and not yet done. Remove an item in the change that
resolves it.

## Whitefoot requirements

Gaps Snowghost needs Whitefoot to close, each stated as its minimal semantic
example apart from the renderer code that exposed it
([Whitefoot-kit](../whitefoot-kit/downstream.md#trying-an-unmerged-whitefoot-change)).

- **A write through indices the program knows are distinct needs its
  facts derived again in each pass.** Minimal example: a tree in an arena,
  each node's children's indices kept in its own list; a counted loop over
  one level's nodes writes `results[child]` for each child. Range facts and
  `apart` (mbbill/Whitefoot#203, #204) now prove such a loop parallel, and
  the style stage's inherited pass is written that way
  (`research/investigations/style/DESIGN.md`, "The level cascade"), but the
  facts are loop invariants of the pass that derives them, not properties
  of the arrays: a public function's contract may name only public fields
  (MOD-6), so the traversal cannot hand its levels to the pass with the
  facts attached, and the pass checks the walk's depths again in a counted
  loop of its own. The layout builder's map from node to style index is
  the remaining scatter written sequentially. Change: a container whose
  invariant states its entries distinct, usable by every loop over it.
  Reopen when Whitefoot offers one, or when the builder's map is rewritten.

- **Reading an unwritten scalar field denies a certified loop.** Minimal
  example: `state: &State` with fields `one: Box<Array<u64>>` and
  `shared: Common`, where `Common` holds `scale: f32`; a counted loop with
  `apart(i, j) { }` writes `state^.one.inner[at]` for distinct `at`.
  Adding `let s = state^.shared.scale;` to its body, even unused, makes the
  ledger deny the loop at the write ("the body writes storage that is
  neither introduced by the iteration nor the accumulator"), while reading
  `state^.shared.table.inner.len` keeps it permitted; no iteration writes
  `state^.shared`. The style stage's level loops
  (`renderer/style/levels.wf`) therefore read the environment and the
  state's scalars once before each loop. Change: the permission survey
  separates a read of a field no iteration writes from the certified
  writes. Reopen when Whitefoot changes the survey, or when a loop needs a
  scalar that changes per level.

- **A function receives every value its requirements name.** Minimal
  example: a function whose requirement states `positions[slots[k]] == k`
  for every `k` must take `positions` as a parameter though its body never
  reads it, and every call passes it. `cascade_level` in
  `renderer/proto/style/shapes.wf` takes `positions`, `depths` and `level`
  only so its requirements can name them. Whitefoot records it in its
  `docs/todo.md`, "Parameters a contract names but the body does not use
  are passed at run time" (mbbill/Whitefoot#203). Change: a parameter that
  only contracts read, erased by lowering. Reopen when that lands or the
  calls' cost shows in a profile.

- **A file named by bytes cannot be opened through a symbolic link.**
  `std::fs::open_directory` and `std::fs::open_file` open one component with
  `O_NOFOLLOW`, and `std::fs::open_read`, which follows links, takes a
  `RelativePath` that only `relative_path` of an argument's `HostString`
  forms. A program given a directory `d` that must open `d/n.png` for names
  `n` read from a file therefore fails when a component of `d` is a link:
  `open_directory(root: cwd, name: "build")` fails with host error 20
  (`ENOTDIR`) and no std call reaches the file. Impact: `png_oracle check`
  refuses its `DIR` in a worktree whose `build` is a link to another
  checkout's build directory, so `make oracle-png` fails there; a `DIR`
  spelling that reaches the same directory without a link works. The
  `style_oracle` driver fails the same way on the real pages in such a
  worktree (`build/research/concurrency` is a link), so
  `research/investigations/style/run.sh` takes `PAGES`, a copy of the pages
  outside the link. Change: a std function that forms a `RelativePath` from
  a byte range, or a component open that follows links. Reopen when oracle
  runs from such worktrees are needed.

- **A local `slots_new::<T, N>()` clears all N slots when created.** The
  code compiled at the pin clears the whole window before any value is
  placed, though no slot past `len` is readable ([WIN-1], [OP-13]); in
  `pkg::css::selectors`'s `match_complex`, a 64-frame window per call, it
  was 21 percent of the style stage's instructions on ecma262 before the
  rule index (`research/investigations/concurrency/DESIGN.md`, "Style's
  work per element"). Whitefoot records it in its `docs/todo.md`
  (mbbill/Whitefoot#196). Change: a window created without clearing.
  Reopen when that lands, to move the pin and measure again.

- **A counted loop that writes a fixed-stride window per iteration is not
  split.** Minimal example: `for (u in 0_u64..n)` takes
  `&ids^[u * 16_u64 .. u * 16_u64 + 16_u64]` and hands it to a function
  that writes it; the windows of distinct `u` are disjoint, but `--par`
  denies the loop as overlapping, so it runs serially
  (`research/investigations/incremental/experiments/x12/program/x12/x12.wf`,
  `record_all`). Impact: a per-unit log of recorded reads, the shape 3.3 of
  the incremental research tree needs, cannot be written in parallel; at
  ten edges per unit that costs well under 1 percent of the build today.
  Change: admit a range write whose bounds are an affine function of the
  loop index with a stride no smaller than its length. Reopen when a stage
  records its reads per unit.

- **No host module shares memory between processes.** Whitefoot's host
  modules are a closed list of six (`std::time`, `std::io`, `std::text`,
  `std::fs`, `std::net`, `std::process`), none of which maps a region two
  processes see; a byte stream through `std::io` is what exists. Minimal
  example: a renderer that writes a frame's records into a region the shell
  reads, then publishes an epoch the shell may read only after every record
  is visible. Impact: `design/processes.md`'s "through shared memory" cannot
  be built; the contract investigation stages a byte stream first
  (`research/investigations/contract/DESIGN.md`, Q75). Change: a host module
  for a shared region with a release-ordered publish. Reopen when the shell
  exists and the copy over a byte stream is measured (C4 there).

- **A split loop called with a few iterations pays its dispatch on every
  call.** Minimal example: `fn mark(frames: &Box<Slots<Frame>>)` whose
  counted loop sets one field of each element (a certified independent
  map), called once per entry of a sequential walk over 100,000 entries
  with two or three frames open each time. At `WF_WORKERS=4` the --par
  build runs the walk slower than the sequential build; at one worker it
  costs the same. Measured on X5's html5 text edits, whose update re-stacks
  a 104,321-entry flow (`research/investigations/incremental-layout/runs/step3b.txt`):
  the step 3 --par driver takes 55.2 ms per edit at the median at four
  workers and 22.7 ms at one; the same sources with the stacking pass's
  three small split loops (`mark_lines`, `float_bottom`,
  `lowest_bottom_above` in `renderer/layout/flow.wf`) made sequential take
  28.1 ms at four workers and 22.8 ms at one, so those loops' parallel
  dispatch costs about 27 ms over the walk's calls. A full layout hides it
  behind its parallel work. Change: run a split loop whose trip count (or
  static work) is below a grain inline in the caller, as the call grain
  already does for calls. Reopen when the runtime offers a loop grain; the
  layout code needs no change.

## Snowghost

- **Structural reaches through `+` chains reach every later sibling.** In
  `h1 + div + h2`, the `div` compound reaches its later siblings, which
  `structural_restyle` widens to every element child after the edit point
  (`renderer/style/restyle.wf`, `widen_side`), while only the element two
  after the point can change. Impact: html5's largest block-edit set is 548
  elements, every later heading, against a handful
  (`research/investigations/structure-edits/runs/structure-check.txt`).
  Change: record in `FeatureReach` the number of `+` hops when only `+`
  follows the compound, and walk that many elements past the point. Reopen
  when M2 step 2's measured insertion cost on html5 shows the set's rematch
  matters against Chromium's 3.06 ms (Q113 option C).

- **Stable-slot structural style still has nonlocal boundaries.**
  `structure_restyle` keeps the style rows, but contiguous `Slots` storage
  can copy its allocation on growth; the 4096-entry reserve postpones rather
  than removes that cost. The selector position cache updates original
  children of the edited parent, while new NodeIds scan siblings. Also,
  `class_restyle` uses preorder ranges and requests a full build after a
  structure edit. Change: bound allocation growth, extend the position
  cache and replace the class reach's preorder ranges with DOM links before
  claiming strict locality across mixed editing sessions. Validate with
  growth-boundary, wide-sibling and interleaved B/X/C/K scripts against a
  fresh style computation. Reopen in M2's follow-up before E2; see
  `research/investigations/structure-edits/runs/slots.txt`.

- **Inserted declarations need a RuleStore update.** `structure_restyle`
  reads the store, whose NodeId-indexed inline declarations and hints were
  parsed at load. Inserting `<p style="color:red">` cannot register its
  declaration through that interface; B's plain paragraph has no such
  declarations. Change: add an insertion preparation operation for style
  attributes and hints, with a minimal inserted styled-element oracle.
  Reopen before accepting general element insertion beyond B/X.

- **Layout update entry counts are not physical visits.** In
  `renderer/layout/update.wf:restack_flow`, `entries` includes the suffix
  length after convergence even for a zero translation, excludes prefix
  recovery and auxiliary scans, and `paragraphs` is one for an entire
  block range. These counters cannot establish M2's locality criterion.
  Change: retain the old report columns for comparison and add physical
  replay, translated-direct-entry, subtree-skip, routing and fragment-work
  counts at their operations. Reopen when implementing M2's nested flow;
  require tiny hand-counted cases and mutations that hide a suffix walk
  to fail the locality check. See
  `research/investigations/structure-edits/layout-design.md`, Inventory.

- **The DOM's node array only grows.** `pkg::dom` appends every created
  node and keeps detached ones (`detach` leaves the node and its subtree in
  the document without a parent), so an editing session's DOM grows with
  every insertion and never shrinks. Every NodeId-indexed table follows it:
  layout's uses and order maps, the class records and the sibling
  positions. Change: reclaim detached subtrees, by a free list for new nodes
  or by an epoch that renumbers NodeIds together with every holder. Reopen
  with the stable-slot compaction above, or before the shell runs editing
  sessions.

- **The incremental restyle runs its loops sequentially.** `restyle`,
  `restyle_level`, `root_font_readers` and `class_restyle`
  (`renderer/style`) are plain loops that push into shared lists (the
  level's batch, the next level, the touched list). The level cascade of a
  full build proves the same per-node work parallel, and nothing but the
  appends orders one restyled node after another. Impact: no par-4 gain on
  restyles of many elements (body and custom-property edits, the root
  font-size levels); par-4 E1 colour edits are slower than seq because of
  the runtime's fixed cost, not this. Change: write each level's
  computation as the full cascade's counted loop over the level's distinct
  positions and gather the appends after it. Reopen when an incremental
  edit's restyle set grows past a few hundred elements on a measured page,
  or with the parallel incremental timing that M1's criterion 2 asks for
  (par-1 and par-4 with the set's size).

- **Kept style state only grows (a condition of Q89).** The owner approved
  Q89, value tables kept across edits, with this item required.
  - What grows: `class_attribute_changed` appends an element's class records
    on every class edit and leaves the old ones unread. The kept value
    tables, custom-property sets and generated text only append, so every
    distinct value a session meets stays.
  - Impact: memory grows with a session's edits, not with the page. A table
    that reaches its ceiling refuses, and the edit falls back to a full
    rebuild.
  - Change: the compaction Q89 recommended. It is an epoch that renumbers
    every table and every holder of an identifier: the styles, layout's keys
    and the class-record heads. It runs when a table has doubled since the
    last full build. Measure first how a long editing session grows.
  - M2's stable element slots (Q111) grow the same way. Inserted elements
    are appended and removed ones leave holes. The same epoch packs the live
    slots and renumbers the NodeId-to-slot map and every holder of a slot.
  - Reopen before the shell runs editing sessions, or when an editing
    session's measured memory grows past the full build's by half.

- **No incremental regression runs in the gate.** `make check` builds and
  checks modules; the identity checks of incremental style and layout
  (`research/investigations/incremental-style/run.sh incremental`,
  `incremental-layout/run.sh inc`) need the fetched pages under build/ and
  run by hand, and the restack boundary page the restack investigation built
  was not kept. A matcher defect (a sibling combinator's left compound
  required as an ancestor by the feature filter) passed every page check
  because the pages hold no matching selector of that shape. Change: keep
  focused case pages and edit scripts in the repository (as
  `incremental-layout/scripts/style-case.*` are) for the shapes found, and a
  gate target that runs them against a full rebuild. Reopen when the next
  incremental defect is found by review rather than a check.

- **The Chromium style oracle cannot run on the development Mac.**
  `tests/css/style_oracle.mjs` needs the Playwright module, which is not
  installed there; only the Chromium binary is. `tests/css/style-cases.html`
  gained the sibling-combinator selector cases the feature-filter defect
  showed, unchecked against Chromium so far. Change: install Playwright, or
  drive Chromium over the DevTools protocol as
  `research/investigations/engine-comparison/chromium.mjs` does. Reopen
  before the next style change claims Chromium agreement.

- **Matching still costs more per element on apollo11.** After the
  per-alternative index and the feature filter, the sequential style stage
  takes 0.39 s for three runs of apollo11's 11,845 elements, about 11 us per
  element, against about 4 on html5 (1.54 s, about 120,000 styled nodes)
  and 10 on ecma262 (2.95 s, about 96,000); the gap to html5 that the old
  item reported (83 against 13 to 16 us) narrowed but remains. Candidate
  rules per element were not counted.
  Change: count candidates and admitted rules per element and profile the
  admitted ones. Reopen with the next style performance work.

- **The restack prototype increases some edits' font-pick interval.** Paired
  sequential Apollo runs report colour/body/custom medians 3-4 us above
  the base, concentrated in `picks_us`, although font-pick source did not
  change; reversed-order ecma262 custom-property runs also regress 2-3 us. The combined candidate therefore fails its nonregression
  criterion. Change: isolate the executable or retained-state difference
  with the same source and workload before attributing or fixing it.
  Reopen before adopting the restack prototype; the paired median must
  cease to increase, and all identity checks must still pass
  ([evidence](../research/investigations/incremental-style/runs/restack-astra.txt)).

- **An ecma262 font-size edit on emu-alg still prepares the whole flow
  context.** With child counts propagated, ecma262 sfontsize edits 7-8
  (an emu-alg with ol/li blocks) take #spec-container's full pre-pass
  path (112,819 entries, about 10 ms) although the context is not
  restyled, has two restyled blocks with a valid common block and no
  marked child: `restack_block` refuses, and which check refuses (a
  marked paragraph outside the common block, a changed block width in
  a subtree that is not block-and-text-only, or no close found) is not
  isolated. Change: report the refusal in a diagnostic run, then widen
  that check. Reopen with the next ecma262 incremental layout target
  ([evidence](../research/investigations/incremental-style/runs/fontsize-fable.txt)).

- **A re-stack makes the context's inline-box fragments again.** After
  every re-stack of a context with block-in-inline splits,
  `restack_flow` runs `split_fragments_with_empty`: a sort of the
  splits, a flag per flow entry, the per-split loop and a copy of the
  kept empty fragments with a binary search each. On #spec-container
  that is about 0.8 ms of each 1.1-1.5 ms sfontsize edit (timing-only
  probe). A converged re-stack now keeps and translates the list when
  no split opens or closes in the re-stacked range and no lineless
  paragraph there opens an inline box; a range holding such a split or
  paragraph still regenerates everything. Change: keep the sorted keys
  and closing flags, which depend only on the flow's structure, and
  regenerate only the runs that intersect the range. Reopen with the
  next ecma262 incremental layout target
  ([evidence](../research/investigations/incremental-style/runs/fontsize-fable.txt)).

- **A context's cached intrinsic sizes depend on when they are first
  asked for.** `intrinsic_sizes` (`renderer/layout/box.wf`) resolves a
  percentage padding against `space.basis_width` when first asked and keeps
  the result (`intrinsic_known`): a parent computing its own intrinsic
  sizes asks before it has written its children's spaces (the fresh space,
  basis 0), a child's own layout asks after (its real basis), so the same
  box's min- and max-content widths differ with the order of requests.
  `intrinsic_flow` also writes every child's margins resolved against no
  width, which `lay_out_child` overwrites. The incremental update
  (`renderer/layout/update.wf`) reproduces both by returning marked
  children to the fresh space, resolving kept children's margins again
  (also on its in-place path, when the context's own intrinsic sizes were
  computed in the update), forgetting a relaid child's sizes only where a
  full layout would compute them against another basis
  (`intrinsic_basis`), and recomputing a container item's sizes against
  the basis they were last computed against.
  Impact: percentage paddings on shrink-to-fit boxes size them by request
  order, and every incremental path must mirror that order. Change: resolve
  intrinsic contributions against one fixed basis (CSS Sizing 3 resolves
  cyclic percentages against zero for them) and leave the children's
  margins to their own layout. Reopen with the next layout correctness
  work or when the update's resets cost measurably.

- **An incremental re-stack lays out again every child a float narrowed.**
  `narrow_beside` lays an in-flow child out again in the room floats leave
  and writes that room into its space; when the update re-stacks the
  parent from an entry before the child, the re-stack gives the child its
  full-width space again, which differs from the narrowed one it was last
  laid out in, so the child is updated at full width (its pre-pass, its
  children and its paragraphs again) and narrowed again even when no edit
  reaches it. (Absolutely positioned children, which `position_out_with`
  lays out again in a forced space, are kept since X5 step 3b; entries
  before the edited one are replayed without layout since step 3c.)
  Impact: since X5 step 3c the cause of the apollo11 sentence edits 31
  and 32, 0.8 ms each sequentially against the page's 0.44 ms bound
  (`research/investigations/incremental-layout/runs/step3c.txt`). Change:
  record the pre-pass space and the width the child needed beside the
  narrowed layout, and keep the child when the pre-pass space and the room
  are unchanged. Reopen with X5's next step on edits beside floats.

- **An update breaks a paragraph at full width before breaking it beside
  floats.** The stacking pass decides whether floats narrow a paragraph
  from its full-width height, so the update's paths break a marked
  paragraph, and X5 step 3c's re-stack every later paragraph a float had
  narrowed, at full width first and again beside the floats. Impact: in
  the re-stack of apollo11 sentence edit 45 the full-width break of the
  edited paragraph is 1.0 of 6.9 million instructions (the paragraph's
  text preparation, 4.3 million, is the largest part)
  (`research/investigations/incremental-layout/runs/step3c.txt`). Change:
  keep each paragraph's full-width height from its last full-width break
  and break a later paragraph once, beside the floats, when that height
  shows they narrow it. Reopen when apollo11's edits beside floats are
  measured again against its bound.

- **The update's translation walks every child of a large context.**
  `translate_after` (`renderer/layout/update.wf`) tests the flow entry of
  every child context, not only those after the changed entry, and
  `shift_naturals` moves each later entry's natural position in a further
  pass; both run on every height change of an in-place update. Impact:
  on ecma262's specification container they are 0.9 and 0.9 million
  instructions of the 2.8 million of sentence edit 3, one of the three
  ecma262 sentence edits above 1 ms
  (`research/investigations/incremental-layout/runs/step3c.txt`). Change:
  find the first later child by binary search where children are in flow
  order, and keep the naturals relative to their entry's placed position
  so a translation leaves them; or reopen Q70's summary tree. Reopen with
  the next update performance work on ecma262.

- **A root font-size update on apollo11 misses criterion 2 at four
  workers.** The update takes 46 ms against about 30 ms for the full layout
  (median ratio 1.55, 1 of 60 edits within 1.2), while sequentially it is
  0.97, and on html5 and ecma262 it passes at four workers
  (`research/investigations/incremental-layout/runs/step4b.txt`). Impact:
  X5's criterion 2 on the smallest page. Change: time the update's parts on
  one edit with clock readings ordered after the work (the delta, the
  marking walk, preparation, layout); if the fixed per-update walks dominate
  a 30 ms page, scale them with the marked work. Reopen with the incremental
  style stage, which replaces the delta.

- **A style update that changes no layout costs 5 to 9 times more at four
  workers.** Colour edits do no layout work but take 27.6 ms at four
  workers against 3.8 ms sequentially on html5 (45 against 6 ms on
  ecma262): styles_changed's validation of every element and its marking
  walk over every context (`runs/step4b.txt`). Impact: the latency of every
  style edit at four workers. Change: measure that walk alone; if the cost
  is the split loops' dispatch on small trees, it is the Whitefoot item on
  split loops with few iterations above. Reopen with the item before it.

- **X5's far-read counter was not built.** Step 6 planned to count, per
  unit, the reads of another element's style, to price Q69's refused
  alternative of recorded reads per unit. Q69 chose keys of the
  layout-relevant groups, and every X5 edit on three pages matched a full
  build, so the count decides nothing now. Change: count calls of
  `computed_of` whose element is outside the reading unit. Reopen if an
  edit kind shows a missed dependency or recorded reads are reconsidered.

- **A changed background predicate prepares and breaks its paragraph
  again.** `layout_changes` reports an element whose background turns
  transparent or visible (Q84 in
  `research/investigations/incremental-layout/DESIGN.md`), and
  `styles_changed` marks every paragraph reading it, although `culled_box`
  only selects which fragments the paragraph's lines report. Impact:
  unmeasured; no X5 edit kind changes a background. Change: a separate
  per-element flag that regenerates the paragraph's fragments from its
  kept lines. Reopen when an edit kind or a page measures background edits.

- **`Paragraph.min_content` and `max_content` are never written.** Every
  paragraph keeps the zeros `new_paragraph` gives them; intrinsic sizes
  are computed per request by `paragraph_intrinsic`. Impact: two dead
  fields in `renderer/layout/module.wfm` that read as a cache. Change:
  remove them, or cache there if a measurement shows paragraph intrinsic
  sizes repeated. Reopen with the next change to the layout interface.

- **The style stage checks the walk's depths again to group levels.**
  `level_index` in `renderer/style/levels.wf` runs a counted pass over the
  depths `walk_elements` records, to state the facts the level loops need,
  then groups the elements by depth; the prototype's shape D
  (`renderer/proto/style/shapes.wf`) walks the tree again for the same
  purpose. Impact: one sequential counted pass and one grouping per stage,
  inside the measured inherited pass. Change: produce the facts where the
  walk records the depths, once a public interface may carry them (see
  Whitefoot requirements, distinct indices). Reopen with that requirement.

- **The level cascade's fast path repeats the sequential path's code.**
  `inherit_level` and `inherit_pseudos` (`renderer/style/levels.wf`) each
  write the twelve per-node arrays inline, as `store_node` does;
  `gather_plain`, `plain_declared` and `plain_resolved` repeat
  `gather_declared`, `inherited_declared` and `resolve_named` without the
  writes to shared stores. They share `compute_node`, but only the style
  oracle's dumps keep the gathering paths equal. The loops are inlined
  because passing the arrays as parameters made 26 captured bindings,
  more than the runtime's lane frame takes, and `store_node` takes the
  whole state. Impact: a change to how a node is gathered or stored has to
  be made twice. Change: one gathering function generic over whether it
  may write shared stores, and a store of a node's values the loop may
  call. Reopen with the next change to either path, or when the
  permission survey admits a call that writes one element of each array.

- **More than one parentless element takes the last one's root font
  size.** The style stage's second and third parts set `root_font_size`
  from each element without a parent element, so with several the last
  wins; the pass before the level cascade gave its children the first.
  The HTML tree builder makes exactly one, so no page shows it. Change:
  take the document element's size, and refuse or ignore others. Reopen
  when another document source (XML, script) can make several.

- **Shapes C and D and the cascade timing repeat one match.**
  `style_shape_c`, `style_shape_d` and `match_all` in
  `renderer/proto/style/shapes.wf` each check the element and rule counts,
  build the rule index and the sibling positions and run the flat match;
  C and D then differ only in their cascade, which `cascade_only` already
  chooses between. Impact: a change to the match has to be made three
  times, and `check` compares C's and D's results but not `match_all`'s, so
  a drift there would show only in the cascade timings. Change: C and D
  call `match_all` and `cascade_only`. Reopen with the next change to the
  match or when shape D replaces C in the pipeline, and time C again then,
  since its code changes.
- **The selector oracle does not exercise the rule index, sibling
  positions or specificity.** `tests/css/selectors_oracle.py` drives
  `selector_matches`, which scans; `subject_key`, `name_hash`,
  `sibling_positions`, `selector_matches_positioned` and
  `matching_specificity` are checked only end to end, by the style stage's
  comparison with Chromium on three real pages
  (`research/investigations/style/run.sh check`), where a wrong match or
  specificity shows only as a wrong computed value. Drive
  `matching_specificity` with `sibling_positions` in the oracle, with the
  specificities Selectors Level 4's examples give, and add cases that pin
  `subject_key` against `selector_matches` (ids and classes in quirks mode,
  SVG and MathML names, duplicate attributes). Reopen now that
  `pkg::style` uses them; it is the next selector change's first step.
- **Passing sibling positions costs the scanning matcher about 13
  percent.** With the positions slice threaded through `list_matches`,
  `match_complex`, `compound_matches` and `instr_matches`, the style
  prototype's shape A, which calls `selector_matches` for every rule and
  element, takes 6.57 s against 5.77 s for two repetitions on ecma262 (wall
  time with setup included, best of three, sequential build; the run is in
  the concurrency investigation's `runs/21-shape-a-95b9073.txt`); the cause
  is not attributed. Measure where
  the time goes, and if it is the extra parameter, give the positions to
  the nth helpers another way; reopen when `selector_matches` is on a hot
  path outside the prototype.
- **Interning is timed only as a difference of whole runs.** Three runs on
  the real style stage put the interning tasks at 10 to 22 percent of the
  four-worker stage on ecma262 and html5 and under 8 percent on apollo11,
  on both sides of the 15 percent bound of `design/vocabulary.md`, and
  interning speeds up only 1.1 to 2.1 times with four workers on those two
  (`research/investigations/style/DESIGN.md`, criterion 2). Change: time
  interning alone with its own mode, and if it passes the bound, split each
  table by hash into partitions interned in parallel, as criterion 2
  prescribes. Reopen before the style stage is measured against another
  engine.
- **Matching costs more than the prototype's.** Matching takes 0.300,
  0.366 and 0.179 s at four workers on ecma262, html5 and apollo11, against
  0.224, 0.180 and 0.202 s for the prototype's whole shape C, with the same
  index and shape; specificity accounts for at most 13 percent of it. The
  user-agent sheet now holds 147 rules, against the prototype's display
  rules, and the cost per rule offered is not measured. Change: count the
  rules the index offers per element and the time per test, then decide.
  Reopen with the interning item.
- **Sibling positions are counted by one sequential walk of the whole
  document.** The table matching reads (`renderer/css/selectors/positions.wf`)
  shares its type counters across parents, an order the counts do not need:
  one parent's children depend only on that parent's child list. Counting
  each parent's children in a counted loop would run in parallel and, after
  a change, recount only the parents whose children changed. The walk's own
  time is not measured. Reopen when it is, or when style runs incrementally
  (`design/pipeline/style.md`).
- **Building the box tree as a walk then a decoding loop is measured on two
  pages only.** On ecma262 and html5 it made the builder and layout together
  1.08 and 1.24 times faster at four workers, short of the 1.5 sought, and
  the sequential build 34 and 21 percent slower; the owner kept it because
  what remains is under 1 percent of the four-worker pipeline
  (`design/pipeline/layout.md`), and asked that it be measured again on
  more real cases. Measure the real builder against decoding during the
  walk, sequentially and at four workers, on every real page the first
  milestone renders. Reopen when the real box tree builder exists.
- **The tokenizer copies text one code point at a time.** `bytes_push` and
  `push_codepoint` take 13 and 10 percent of html5's parse, and UTF-8
  decoding 7 (the concurrency investigation's HTML parsing section): a text
  token's bytes are decoded and pushed back singly where a run of plain
  bytes could be copied whole, which shortens parsing's chain without
  parallelism. The owner placed it after style. Reopen when parsing is the
  next sequential cost studied.

- **The user-agent sheet's rules match every namespace, and only HTML
  style elements are read.** `pkg::style::add_sheet` skips `@namespace`, so
  `ua.css`'s `@namespace` for HTML does not restrict its rules: an SVG
  `title` takes `title { display: none }` (one element of ecma262), and
  `sheet_sources` lists only `style` elements in the HTML namespace, not
  SVG's. Change: give a sheet's default namespace to the selector parser
  and read SVG style elements. Reopen when an SVG-heavy page joins the
  corpus.

- **Second-batch values the style stage parses differently from the
  reference.** Each is a recorded class of the style investigation's second
  batch (`research/investigations/style/DESIGN.md`): an integer `repeat()` in
  a track list is expanded at parse time, as the interface declares, where
  Chromium keeps `repeat(2, ...)`; `safe` and `unsafe` are dropped from
  alignment values, which Chromium keeps; `justify-items: legacy` with a
  direction is kept as `legacy`, which computes to `normal`, where Chromium
  keeps `legacy center`. No real page uses any of them. Change: give
  `TrackList` a list of repeated ranges with counts and the alignment values
  an overflow-position bit and a legacy bit, if layout needs them; reopen
  when a page uses one.
- **Multi-column values the style stage does not give.** `column-span`,
  `column-rule-width`, `column-rule-style` and `column-rule-color` (the rule's
  width takes part in the column box's width), `break-before`, `break-after`,
  `orphans` and `widows` are not parsed; `column-count: calc(...)` is not
  parsed as an integer (Chromium accepts `calc(1 + 2)`), and a `calc()` that
  is no length is not a `column-width` either; `column-fill: balance-all` is
  parsed as CSS Multicol Level 2 defines it, where Chromium 141 rejects it,
  and `-webkit-column-fill` is not an alias, as in Chromium. Change: add the
  longhands to `pkg::css::values` as the second batch did for flex and grid,
  and an integer `calc()` grammar. Reopen when the layout stage's multi-column
  layout or a page needs one.
- **The user-agent sheet's Chromium rules cover what the pages and a probe of
  every control showed.** Chromium's computed values still differ for
  `option` and `optgroup` (`min-height`, padding, `align-items`, gaps), the
  `meter` and `progress` boxes, `audio`'s `display: none` without controls
  and its size, `marquee`, `rt`'s font size, and the `width` and `height`
  attributes of `svg`; `:disabled` does not match the controls of a disabled
  `fieldset`, which the selector matcher does not implement; a `select`
  shown as a list box is recognised by the `multiple` and `size` attributes
  read as text, so `size="02"` is not; and a table's `frame` and `rules`
  attributes give `outset` and `inset` where Chromium gives `solid` (the hints'
  place in the cascade, below). The form-control font is the probed Linux
  host's. Change: probe and add each with the same method as the form
  controls (`tests/css/style_oracle.mjs` on a page of the elements against the
  `style_oracle` driver). Reopen when layout draws one of them.
- **`url()` in `content` is kept as written.** Chromium resolves it against
  the document's base URL (`url("http://snowghost.test/page/x.png")`); the
  stage keeps the specified URL, since it resolves no URL and loads no
  image. Change: resolve it with `pkg::url` when images are loaded.
- **`rlh` and most stepped-value functions are not parsed.** The `lh` unit
  (ecma262's `.corner-cell { height: 2lh }`) and `round()` of two px
  lengths (apollo11's image widths) are; `rlh`, `round()` with another
  strategy or other units, `mod()` and `rem()` are not. Change: `rlh` as a
  length of the root's computed line-height and the remaining stepped-value
  functions in `calc()`. Reopen when a page uses one.
- **Some presentational hints are not implemented.** The `li` `value` and
  `ol` `start` and `reversed` hints for `counter-set` and `counter-reset`
  (Chromium exposes neither in computed values), the dimension attributes of
  a `source` in a `picture` that an `img` takes from it, `body`'s margin
  attributes, `bgcolor`, `bordercolor`, `background`, and the `table[border]`
  rules' place in the user-agent cascade: they are offered with the hints,
  above every user-agent selector, so on a table with both `border` and
  `frame` or `rules` they win where the Standard's later rules would.
  Change: per-record specificity and order for the hint records. Reopen when
  a page uses one.
- **Component walking helpers are written twice.** `pkg::css::values`
  (`tokens.wf`, `components.wf`, and `shapes.wf`, whose `shape_of` the second
  batch's grammars use) and `pkg::style` (`components.wf`) each
  classify components, skip whitespace, find a sibling and compare an
  identifier with a word list, because neither module can reach the
  other's private functions. Change: make one set public in
  `pkg::css::syntax`, next to the component list they read, and use it from
  both. Reopen at the next change to either module's component handling.
- **`pkg::proto::style` duplicates the rule index and traversal that
  `pkg::style` now holds.** The prototype stays because the concurrency
  investigation's measurements are reproduced with it and
  `pkg::proto::layout` builds on it; `pkg::style`'s `cascade.wf` and
  `traversal.wf` started as copies of its `index.wf` and `traversal.wf`.
  Change: retire both prototypes, or point them at `pkg::style`, when the
  layout stage is built on `pkg::style` and the concurrency investigation's
  runs no longer need reproducing.

- **No mechanical check for documents and artifacts.** `make check` does not
  refuse non-English text, personal filesystem paths or broken Markdown links
  and anchors; reviewers check them by hand (checklist A4 and D2).
  Whitefoot's `make static` stages `repository-invariants` and `guidance` are
  the models. Add the equivalent when the documents grow enough that a missed
  link or leaked path costs review time, or when one first reaches a pull
  request.
- **`bytes_push` (`html/tokenizer/buffers.wf`) leaves cell unchanged, rather
  than proving it, when a push would cross `ceiling`.** `text_ceiling` (3 *
  2^30) and `attribute_ceiling` (2^30) are sized from `next_token`'s own
  `source^.len <= 2^30` requirement and this module's worst-case per-source-byte
  expansion (a NUL becoming three-byte U+FFFD; no attribute without consuming
  a source byte), so no legitimate caller reaches ceiling and the guard is
  dead on every input the module accepts. Proving that mechanically needs a
  loop-position invariant (current output length vs. source position
  consumed) in every `scan_*` state that pushes text or attributes
  (`data_state.wf`, `text_states.wf`, `script_data.wf`, `comments.wf`,
  `doctype.wf`, `tags.wf`), tying each state's own advancement to the
  3x/1x bound above; `bytes_push` and its `push_byte`/`push_codepoint`/
  `push_attribute` callers already carry the exact `requires`/`ensures`
  pair such a proof would need (drafted and reverted; the reachable half,
  within `bytes_push` itself, checks). Add it if a stress input, fuzz run or
  future state addition raises real doubt that the sizing argument still
  holds, or when another finding forces the same loop-invariant work anyway.
- **Processing instructions are not parsed.** The HTML standard now parses
  `<?target data?>` into processing instruction nodes (WPT's
  `processing-instructions.dat`, 124 cases), while the tokenizer's oracle,
  html5lib-tests' frozen tokenizer suite, still reads `<?` as a bogus
  comment. The tree oracle excludes that file and four `<?` cases in other
  files. Support needs a token and a
  node variant in `pkg::html::tokenizer` and `pkg::dom`, the serializer's
  `<?target data?>` form, and the tokenizer cases that expect a comment
  marked as superseded. Reopen when a target site uses processing
  instructions or the tokenizer oracle moves to a suite that has them.
- **An option's contents are not cloned into `selectedcontent`.** The
  standard clones the selected option into a customizable select's
  `selectedcontent` element from the option element's insertion and
  selectedness steps, not from tree construction, so
  `pkg::html::tree_builder` does not do it; the tree oracle excludes the
  four `webkit02.dat` cases that observe it. Change: implement the element
  behaviour where DOM insertion steps live. Reopen when form controls are
  rendered.
- **pkg::css::color covers CSS Color Module Level 4 only.** System colors,
  `color-mix()`, `light-dark()`, relative color syntax, `calc()` in
  channels and the Level 5 spaces (`device-cmyk()`, `@color-profile`
  spaces) parse as Invalid, and `color_functions_5.json` is not in the
  oracle. Impact: pages using them lose the declaration; the style stage now
  resolves colors, and the HTML Standard's user-agent sheet uses `Canvas`,
  `CanvasText` and `ThreeDFace`, whose declarations are dropped, which no
  element of the three real pages shows in its computed values. Change:
  extend `ParsedColor` and the parser, and add the suite. Reopen when a
  page in the corpus shows a system color or a Level 5 form in a mismatch.
- **`narrow_f32` predates `cvt.nearest`.** `pkg::css::color` narrows its
  channels from f64 to f32 by computing round-to-nearest-even from the
  bits, because the pin it was written against had no rounding conversion;
  the pin now has `cvt.nearest` ([OP-6]), which `pkg::css::values` uses.
  Change: replace `narrow_f32` with `cvt.nearest::<f64, f32>` and rerun
  `make oracle-css-color`. Reopen at the next change to `pkg::css::color`.
- **pkg::text::normalization has NFC and NFD only.** NFKC and NFKD, and
  their NormalizationTest.txt invariants, are not implemented: IDNA needs
  NFC only. Change: add the compatibility decompositions to the generated
  tables and two NormalizationForm variants. Reopen when a consumer needs a
  compatibility form.
- **pkg::url computes no origin or search parameters and encodes queries
  as UTF-8 only.** The record has no origin (blob: URLs and opaque origins
  need modelling) and no application/x-www-form-urlencoded parsing, and a
  document's non-UTF-8 encoding does not reach the query's
  percent-encoding; WPT's origin and searchParams fields are not compared.
  Change: add an origin function and a search-parameter parser, and an
  encoding argument once text decoding exists. Reopen when fetch or
  same-origin checks need an origin, or a legacy-encoded page is loaded.
- **Punycode encoding is quadratic in the worst case.**
  `pkg::text::idna`'s encoder follows RFC 3492's reference structure: it
  scans the whole label once per distinct non-ASCII code point, so a label
  of n strictly ascending distinct code points costs O(n^2). With
  VerifyDnsLength false a label has no length limit, so a hostile URL can
  reach it. Change: sort the label's non-ASCII code points once and walk
  them in order. Reopen when URL parsing runs on untrusted input at scale,
  or a profile shows it.
- **pkg::oracle::support has no signed decimal writer.** The font drivers
  print negative metrics, advances and offsets, so `pkg::oracle::font_face`
  (`put_signed_field`) and `pkg::oracle::font_shape` (`put_signed_item`)
  each carry the same sign-and-magnitude step beside support's unsigned
  `put_decimal`. Change: add a signed writer to support's interface and use
  it in both drivers. Reopen when a third driver prints signed numbers or
  support's interface next changes.
- **pkg::font reads only raw sfnt fonts for simple scripts.** WOFF and
  WOFF2 (which needs a Brotli decoder), font collections, variable fonts
  and CFF2 are refused as Unsupported; shaping covers horizontal
  left-to-right Latin, Greek and Cyrillic with HarfBuzz's default
  features, not the complex-script shapers (Arabic, Indic, Khmer,
  Myanmar, Hangul, Thai), vertical text, cmap format 14 variation
  selectors or the GSUB and GPOS lookup types outside the listed ones;
  and load_face validates only the tables shaping reads, not the outline
  tables (glyf, loca, CFF) the shell's rasterizer will read. Impact: web
  fonts, which are mostly WOFF2, and pages in other scripts cannot use
  their fonts yet. Change: a WOFF2 and Brotli leaf, outline validation
  before any font reaches the shell, and one shaper leaf per script
  family. Reopen when the first page needs a web font, a non-Latin script
  beyond Greek and Cyrillic, or the shell rasterizes.
- **load_face ignores a whole malformed GDEF, GSUB or GPOS table.** Chrome
  passes these tables to HarfBuzz unsanitized, and HarfBuzz's sanitizer
  neuters each offset it cannot follow, so the lookups that parse still
  apply. pkg::font drops the whole table instead. The two agree when the
  table is unreadable as a whole or when the neutered offset is the only
  structure a feature uses; otherwise a font with one broken lookup loses
  its other lookups here. Change: validate per lookup and ignore only the
  failing lookup, matching HarfBuzz's neutering. Reopen when a real web
  font with a partly broken layout table renders differently from Chrome.

- **Emoji presentation is not given to a color emoji face.** Chromium draws
  a character whose Emoji_Presentation is Yes (U+231B, U+1F600) with Noto
  Color Emoji ahead of the font-family list; `pkg::layout::text` draws it
  with the first face of the chain that maps it (DejaVu Sans for U+1F600,
  FreeSerif for U+231B), so the advance differs. Impact: 1 of the 3,000
  text cases drawn from the three pages (html5's U+231B) and the synthetic
  emoji cases (research/investigations/layout/DESIGN.md, "Text preparation
  results"). Change: Emoji_Presentation in `pkg::text::properties` from
  emoji-data.txt, a mark on color faces (CBDT, sbix or COLR) in `FontSet`,
  and itemizing emoji-presentation sequences, and characters followed by
  U+FE0F, to the first color face. Reopen when a page that renders emoji
  joins the corpus.
- **Indic and other complex scripts are shaped as Common.** `pkg::font`
  shapes Latin, Greek, Cyrillic and Common only, so Devanagari's reordering
  and conjuncts and Tamil's are missing: two of apollo11's language links
  (हिन्दी and தமிழ், in FreeSans) are 0.33 and 0.08 px wider than in
  Chromium. Change: HarfBuzz's Indic shaper in `pkg::font` and the script
  in `pkg::layout::text`'s itemizer. Reopen when such text is in scope.
- **Fallback for bold or italic text skips the generic's own family.** For
  a bold or italic group whose first family is `serif` (or `monospace`),
  Chromium tries fontconfig's face for that generic name at normal style
  (DejaVu Serif, DejaVu Sans Mono) before its global fallback order
  (`research/investigations/layout/runs/text-fallback.txt`: bold `serif`
  draws U+2200 with DejaVu Serif, regular `serif` with DejaVu Sans);
  `pick_fonts` follows the fixed order of the set, as its interface says.
  Chromium also picks a run's fallback face by the run's first unmapped
  character and keeps it for later characters it maps, where
  `pkg::layout::text` decides per character. Impact: none of the sampled
  page text (its first families are IBM Plex Serif and sans-serif). Change:
  a per-group fallback prefix in `pick_fonts`, with the interface's doc.
  Reopen when bold or italic serif text with symbols outside Liberation is
  measured.
- **`word-break: break-all` is not Chromium's.** Blink also breaks before
  and after dash punctuation in break-all and does not break after a
  hyphen-minus before a non-ASCII letter; `pkg::layout::text` allows a break
  between two letters or numbers only. Impact: 21 of the synthetic break
  cases; no sampled page text uses break-all or keep-all. Change: measure
  Blink's break-all classes as the normal ASCII table was measured and
  encode them. Reopen when a page uses break-all.
- **The x-height of a face without OS/2 sxHeight is approximated.** Skia
  measures the hinted x glyph for DejaVu and WenQuanYi (OS/2 version 1),
  giving whole pixels; `face_extents` returns 0.56 times the rounded
  ascent, Blink's own fallback, so `ex` lengths and `vertical-align:
  middle` on DejaVu text differ by up to about 1 px. Change: the x glyph's
  bounding box from glyf with the autohinter's rounding, or a measured
  table. Reopen when ex units on DejaVu text move a measured box.
- **Letter-spacing does not turn ligatures off.** Chromium disables
  liga, clig, dlig, hlig and calt when letter-spacing is not 0;
  `pkg::font::shape_run` takes no feature settings. The installed Liberation
  faces have no such ligatures, so no measured case differs. Change: a
  feature parameter in `shape_run`. Reopen when a face with ligatures is
  drawn with letter-spacing.
- **A tab gets no advance from text preparation.** `shape_paragraph` treats
  U+0009 as a control of advance 0; its width depends on its position and
  `tab-size`, which only line layout knows. The layout stage must give each
  preserved tab its tab stop. Reopen with `white-space: pre` text that holds
  tabs.
- **`text-align: justify` aligns as start.** `finish_lines` offsets a line
  for right, end, center and their -webkit- forms and leaves every other
  value at the start, so justified lines keep their natural spacing.
  Impact: no element of the three pages computes `justify` (the style
  oracle's text-align column). Change: distribute a line's free space over
  its justification opportunities, except on the last line and lines a
  forced break ends, as CSS Text 3, 7.3 describes. Reopen when a page
  justifies text.
- **`text-overflow: ellipsis` draws no ellipsis.** Chromium reports an
  extra fragment for the ellipsis of an overflowing line in a box with
  `overflow` other than visible; the stage leaves the line whole. Change:
  truncate the line's runs at the content edge less the ellipsis's advance
  and add the ellipsis fragment. Reopen when a measured page sets it on
  overflowing text.
- **A text input's baseline is 3 px above Chromium's.** The stage puts the
  baseline of a single-line text input at its border, padding, centred
  line and the font's ascent (`lay_out_replaced`); in `tests/layout/flow-cases.html`
  Chromium's baseline lies 13 px below the input's top where the stage's
  lies 10 px below, which moves the line and the boxes after it. Change:
  probe the inner editor's position with borders, padding and heights
  varied, and take its baseline. Reopen when a page puts a text input on a
  line with text.
- **Most form controls do not have the reference's size.** Only
  single-line text inputs, checkboxes and radio buttons get Chromium's
  natural sizes (`natural_text_input`, `natural_toggle`); the other
  `input` types, `select` and `textarea` are replaced boxes of the default
  300 by 150 px (`is_replaced`, `natural_object`), and `button` is laid out
  as an ordinary inline-block. Change: their natural sizes and baselines
  from probes of Chromium. Reopen when a page lays one out.
- **Multi-column layout is limited to Q59's form.** `column-span`,
  orphans and widows, `column-fill: balance-all` and a break inside a box
  that is neither a paragraph, a table nor a `break-inside: avoid` box
  (a fixed-height block is kept whole) are not implemented
  (`renderer/layout/columns.wf`). Impact: none on the three pages, whose
  multi-column containers hold tables, lists and paragraphs. Change: the
  fragmentation units and the spanner's own pass. Reopen when a page uses
  one.
- **Right-to-left text is shaped and ordered as left-to-right.** Eleven of
  apollo11's language names in Arabic script (span 506 is 60.66 px wide
  here, 38.27 in Chromium) and about a dozen of its text nodes differ:
  `pkg::font` applies no Arabic joining forms and the stage does no
  bidirectional reordering, both out of scope. Change: Arabic shaping in
  `pkg::font` and UAX #9 reordering of a line's runs. Reopen when
  right-to-left text is in scope.
- **`font-variant: small-caps` is not applied.** The style stage does not
  compute it and text preparation draws lowercase letters at full size:
  apollo11's twelve `abbr` navigation links (t, e, v) and their `li` are
  1 to 2 px off. Change: the longhand in `pkg::css::values` and synthetic
  small capitals in `pkg::layout::text`, as Chromium scales lowercase
  letters to 70 percent. Reopen with any further page that sets it.
- **`transform` does not move boxes.** `getClientRects` reports transformed
  boxes; apollo11's search icon (`span` 110, `translateY(-50%)`) is 9 px
  lower here. Transforms are out of scope. Change: apply translations to
  the dumped rectangles of a box and its descendants after layout. Reopen
  when transforms are in scope.
- **An absolute box's static position inside an inline formatting context
  is the block's start.** apollo11's `span` 3660 (`.sr-only` inside a line)
  starts at x 263 here and at the inline position 395.5 in Chromium.
  Change: record the inline position the box would have had on its line
  as its static position. Reopen when such a box is visible on a page.
- **A float's max-content contribution is added to the widest line.** The
  stage adds a float's width to the widest line of the text beside it;
  Chromium adds it to the lines it sits beside only
  (`research/investigations/layout/runs/float-intrinsic.txt`: float, aaa,
  br, bbb gives 54 px here, 51.3125 in Chromium). Change: track the lines a
  float shortens during the max-content pass. Reopen when a page's
  shrink-to-fit box holds a float beside lines of different widths.
- **A block-level box in normal flow ignores `width: min-content`,
  `max-content` and `fit-content`.** The keywords size shrink-to-fit
  boxes, tables and absolute boxes only. Change: resolve them in the
  block's used width from its intrinsic sizes. Reopen when a page sets one
  on a block in flow.
- **Preserved spaces that hang at a `pre-wrap` line's end are not in the
  text's width.** `tests/layout/flow-cases.html`'s pre-wrap text reports a
  first line 200 px wide in Chromium and 157.75 here. Change: include the
  hanging spaces up to the line's end in the fragment, as Chromium's
  `getClientRects` does. Reopen when a page wraps pre-wrap text with
  runs of spaces.
- **Some apollo11 links lose the kerning across their end.** About 21 of
  apollo11's links are 1.0 to 1.2 px wider than in Chromium: the text
  "Kennedy" in `a` 1223 is 55.58 px wide here and 54.55 in Chromium, which
  shapes it together with the comma after the link, so the y-comma kerning
  pair applies. The stage gives the same 54.55 on a probe with the same
  markup inside the page's own head and stylesheets, so something else on
  the full page splits the shaping run there;
  the cause is not yet found. Change: find which property or boundary
  `pkg::layout::text` splits runs at on the page, and probe whether
  Chromium splits there. Reopen before apollo11's inline measure needs
  these boxes.
- **About 70 of ecma262's block boxes follow line wraps that differ by
  less than 0.2 px.** A line that fits here by about 0.01 px does not fit
  in Chromium (`emu-rhs` 83416); varying `text-indent` puts Chromium's
  threshold between -25 and -25.2 px and the stage's between -24.5 and
  -25 px, and an inline box's width here is 1/64 px less than Chromium's
  for the same run (138.0 against 137.984). Each such wrap moves the boxes
  after it by up to 3.5 px. Cause not yet isolated: Chromium appears to
  test the fit against an unrounded sum of item widths. Change: probe the
  fit test with runs whose widths sum to just under and over the available
  width, and compare with `break_lines`. Reopen when ecma262's block
  measure needs these boxes or a page shows the same wrap differences.
- **`lh` for `line-height: normal` is 1.15 times the font size.** The style
  stage resolves the `lh` unit against the element's computed line height,
  and for `normal` it takes 1.15 times the font size, since it holds no
  font ascent, descent or line gap; layout computes `normal` from the
  face's metrics. Impact: none measured; ecma262 uses `lh` only with a
  numeric line-height. Change: give the style stage the first available
  face's metrics, as it already has its x-height and zero advance. Reopen
  when a page uses `lh` under `line-height: normal`.
- **The initial line height 18.4 px is written in five places.**
  `renderer/style/inherited.wf`, `reset.wf` (twice), `lists.wf` and
  `media.wf` each spell 16 px times 1.15. Change: one named constant in
  `pkg::css::values`. Reopen with the next change to any of them.
- **A table cell's absolute children are positioned twice.** The cell's
  flow positions them, then `lay_out_table` positions them again with
  `position_out_with` once the rows have their heights; the first result
  is discarded. Change: skip the first pass for a context laid out as a
  cell. Reopen when profiling shows it, or with the next change to table
  cell layout.
- **A float before a block inside an inline box sits 10 px too high.** In
  `tests/layout/flow-cases.html`'s probe e1 the float is at y 427 where
  Chromium puts it at 437. Change: probe how the block's collapsed margin
  moves the float's position and apply it. Reopen when a page floats a box
  there.
- **`ex` and `ch` still come from the generic families' faces.** The layout
  scope was to revise the style stage's provisional rule
  (`design/pipeline/style.md`) to the metrics of the installed face each
  element's `font-family` matches, now that `pkg::layout::text` matches
  families; the style stage still takes the x-height and zero advance of
  the serif, sans-serif and monospace defaults. Impact: not measured
  separately; criterion 1 holds on the three pages with it. Change: run family matching before the
  style stage's compute part and pass each font group's first face metrics.
  Reopen when a page sizes boxes in `ex` or `ch` under a named family.
- **Multi-column layout ignores `column-fill: auto` and the container's
  height.** `fragment_columns` always balances and never reads
  `column_fill` or a definite container height, where Chromium fills
  columns in turn up to that height and balances only up to it. Impact:
  none on the three pages, whose multi-column containers have auto heights
  and balance. Change: take the definite height as the column height for
  `auto`, and as the bound of the balanced height, with overflow columns.
  Reopen when a page sets either.
- **Most of the layout passes' loops run sequentially.** Of the 340 loops in
  `renderer/layout/` the `--par` ledger lists, it permits 49; it refuses
  127 that write storage neither the iteration introduces nor an
  accumulator holds, 119 that write storage outliving the iteration
  without an exactly associative reduction, 39 that leave early and 6
  that carry several accumulators. The layout passes reach 2.30 and 2.47
  times their sequential speed at four workers on ecma262 and html5, and
  1.53 on apollo11 (research/investigations/layout/DESIGN.md, Layout
  results). Which refused loops hold the passes' time is not measured.
  Change: profile the passes' sequential time by function, then rewrite the
  costly loops so each iteration writes only its own element, or state the
  minimal semantic gap for Whitefoot under Whitefoot requirements when a
  loop cannot be so written. Reopen before the next performance target for
  layout, or when the passes exceed half the stage's time at four workers.
