# A review map generated from the source (the atlas)

Status: exploration in progress, handed over mid-way. Nothing here is a
decision; the open questions at the end are for the owner.

## Question

Whitefoot programs have a shape other languages lack: a struct holds no
reference, so every program is an owned tree of data plus integer indices
between tables, and every function states in its effect row what it reads
and writes. Can a tool draw a Whitefoot program's architecture from that
shape alone, so that a person reviewing code an agent wrote understands it
top-down, from the whole pipeline to one field, without reading the source
first? And where the drawing needs information the source cannot carry,
what does that say the language should add?

The second part is the point. The language's position is "AI writes, a
person reviews"; a review tool that the source cannot feed shows where the
language must let the writer state more, and the ease of reviewing becomes
a criterion for language design. Snowghost is the first large program to
try it on, but the tool is meant for any Whitefoot project.

## Proposal under test

A static map built only from declarations, docs, effect rows and the order
of calls, plus one hand-written layer for what the source does not state,
lets a reviewer answer architectural questions about Snowghost. Every item
in the hand-written layer is a candidate language requirement.

Rejected if, on the agent trial below, the map-only condition answers worse
than the source-only condition by more than ten points of incorrect claims,
or if the hand-written layer has to carry most of what a top-down reading
needs even after the language's existing doc entries are used in full.

## What was built

`prototype/` holds the apparatus, about 540 lines:

- `extract.py` reads every `.wf` and `.wfm` under a renderer tree and
  returns its declarations: structs with fields, enums with variants,
  functions with parameters, result, effect row, contract, docs and the
  calls in their body in first-appearance order, consts and aliases. It
  relies on the canonical form (top-level items at column 0, one header
  per line) and needs no compiler. Checked against `grep` on the renderer:
  both count 9621 top-level items.
- `build.py` resolves aliases to module paths, resolves the types each
  parameter, result and field names and the function each call names, adds
  reverse references, merges `annotations.json` and writes `atlas.html`.
  On the renderer at `29f89af`: 52 modules, 443 types, 3322 functions, 7877
  resolved calls, in 0.1 s.
- `atlas.template.html` is the page. `annotations.json` is the hand-written
  layer: index targets, which modules are drivers, and the top-level tour.

Run `python3 prototype/build.py renderer <out>` and open `<out>/atlas.html`.
The published prototype is a private Claude artifact; the owner has its
link.

## What the source gives and what it does not

Counts from the renderer at `29f89af`, driver modules (oracle, tools, proto)
excluded:

- Every function has a doc and an effect row: 389 of 389 in `dom` and
  `style`, and the pattern holds across the tree.
- 248 of 355 structs and enums have no doc. `dom`, the pipeline's input,
  documents none of its 11 types; `css::selectors` none of 30; `layout`
  58 of 62 and `font` 45 of 53.
- 431 fields of type `u32`, `u64` or an array of them name no target in
  their type. This count is an upper bound: it includes counts and sizes,
  which no simple rule tells from positions. For 31 of them a doc sentence
  names the target table, and `annotations.json` records each with the
  sentence it was taken from; for a few (`Flow::Child.context`,
  `PseudoStyle.element`) the doc names no table and the target is
  inferred.
- Nothing above a function can carry a doc. The grammar admits `doc` only
  on struct, enum, fn, interface and binding
  (`whitefoot/spec/kernel-spec-v0.90.md`, `struct_decl` to `doc`), not on a
  field, a variant, a module or a row of `modules.wfg`. There are no
  comments (`[FORM-4]`).
- The renderer has no top-level function that states its pipeline. The
  stages are called in order only by the test drivers (`oracle::layout`,
  `oracle::page`), so the map's first screen cannot be derived from
  renderer code.
- A doc has no short form. Its first sentence is often 60 words; a one-line
  summary for a row has to truncate it.

## The first design, and why it failed

The first page showed everything it had: a module dependency graph, a flow
graph of every call from an entry (35 functions and their data in one
drawing), module pages listing public functions with their docs, and a gap
dashboard. The owner's review: too much on screen, no focus, so many arrows
that they carried no information, and no stated reason for any element
being on the page. The cause was the order of design: it started from what
could be extracted instead of from what a reader asks.

A second observation from the same review: an agent does not suffer from
information overload, so a tool that an agent uses well can still be
unusable by a person. The agent trial therefore measures only whether the
information is present; whether a person can take it in is a separate
question that a person answers.

## The second design: derived from the reader's questions

The page is one map that expands in place. Each interaction is a question
the reader asks, and a screen shows only the answer to the question that
opened it; what can be clicked on that screen is the next question. A
newcomer reads the first screen; a returning reader goes through it by
position, the way one finds a book on a shelf, so every item has one place
and opening an item never moves the others.

The first screen answers three questions: what the program does (one
sentence), what its main steps are and what data passes between them (four
rows for rendering a page, four for updating after an edit), and where to
go next (the rows and the data themselves). Each row reads left to right:
what the step needs, the step, what it makes or changes in place. Long
arrows are not drawn; a datum's flow is shown by hovering it, which lights
every place it appears. Opening a step shows the steps inside it in the
same form; opening a datum shows its fields under that row, with each field
of a named type openable in turn, down the ownership tree; the signature,
contract and full doc appear only at the bottom.

Two rules in the page are heuristics, not derived from anything:

- A callee counts as a step when it calls something itself and has at most
  four callers; the rest fold into "n small helpers". The threshold was set
  after looking at `compute_styles`, `inherited_pass`, `lay_out_flow` and
  `update`.
- The "needs" column shows only parameters taken by reference; small values
  (`NodeId`, `Viewport`, `Environment`) are left out.

The first screen is almost entirely hand-written: the sentence, the two
paths, the eight stage names and their summaries, and which functions form a
stage (`annotations.json`, `tour`). From the second level down the page is
read from the source. That is the finding in concrete form: the level a
reader needs first is the level the language gives no place to write.

Walked through once in a browser: Style, then Compute the styles, shows the
four passes with the chain Cascade, Inherited, Resets, Styles read off the
rows; opening Styles lists its 28 fields flat, with no doc and no grouping.
The Layout rows and the recursion notice (`lay_out_context` calling itself
through `lay_out_flow`) were not exercised.

## Agent trial

`trial/PLAN.md`, written before any run, defines three conditions for one
question ("describe the layout engine"): A, the map alone through a
Playwright-driven browser; B, the renderer source alone; C, both. Agent:
codex-cli 0.160.0, model gpt-6.1-sol, reasoning effort low, chosen by the
owner.

Only B has run (`trial/B.answer.md`): 95 s wall, 6 shell commands, 202,716
input tokens of which 150,528 cached, 1,909 output tokens, 819 words; its
command log shows it read nothing outside the copied `renderer/` tree. It
answered mainly from `layout/module.wfm` and `rg 'doc "'` over the module's
files, that is from docs, and names index targets that the docs state only
in prose. It is not graded; grading waits for A so one grader scores both.

A has not run: it needs `@playwright/mcp` (about 13.6 MB from npm), which
the owner had not approved at handover, and should run against the second
design, not the first.

## Candidate language requirements

Not filed in `docs/todo.md`: none is yet a requirement of renderer code,
and the owner has not ruled. Each would be stated as a minimal example when
filed.

1. A doc on a module and on `modules.wfg` rows, and a required one-line
   summary form of every doc, so the top of the map can be read from the
   source.
2. A way to state, in a field's type, the index space it belongs to and the
   table it points into, so "which table does this u32 index" is read from
   the type rather than from prose, and the compiler can check it. The
   language today refuses brands and typed handles on memory-safety grounds
   (`whitefoot/design/language/data-model.md`,
   `ownership/pools-and-arenas.md`); this asks for them on semantic grounds,
   as a feature for review, which is a different argument and would need
   its own design: index arithmetic, the sentinels (`no_index`,
   `root_element`) as `Option` with a niche, and maps between spaces. The
   owner's view at handover: worth doing, as a feature of the language for
   its review tool.
3. A doc on a field and on an enum variant, so a struct's long doc
   (`layout::Context`, one paragraph for 54 fields) can attach to the
   fields it describes.
4. A place in the program, not in a test driver, that states the pipeline.
   This one is Snowghost's, not the language's, and will come with the
   shell integration.

## Open questions for the owner

- Q1. Is the second design, rows that read "needs, step, makes" and expand
  in place with no long arrows, the expandable architecture diagram the
  owner asked for? The owner had not seen it at handover.
- Q2. Should the unbuilt stages (paint, compositing, the shell) appear on
  the first screen, dashed? Their source is `design/`, not code.
- Q3. Run trial A against the second design, with the Playwright download?
- Q4. Where the tool should live. It is meant for every Whitefoot project,
  so its home is the Whitefoot repository, with Snowghost as its first user;
  the compiler's own `--render-interface` and `--par-ledger` outputs may
  replace `extract.py` once the data it needs is exported.

## Next steps, in order

1. Owner reviews the second design (Q1, Q2) against the derivation above,
   element by element: why each thing is on the screen and what would be
   better.
2. Finish the derivation one level further: what opening Layout should
   show, given 577 private functions in one module and only file names
   (`flow.wf`, `flex.wf`, `grid.wf`, `table.wf`) as an intermediate
   grouping.
3. Run trial A and C on the second design, grade all three with one
   grader, classify every incorrect claim of A as information missing from
   the map, present but not found, or asserted without support.
4. Turn the candidate requirements the trial confirms into minimal examples
   and file them under Whitefoot requirements in `docs/todo.md`; propose
   the first two in the Whitefoot repository.
5. Check the whole approach on a second Whitefoot program (a `lib/std`
   module) so the requirements are not shaped by Snowghost alone.
