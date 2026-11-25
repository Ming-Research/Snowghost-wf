# Pipeline

The renderer's stages from the document to the screen: how each runs in parallel, and how a stage kept across edits learns what changed.

### decision every-stage-incremental-and-parallel
Style and layout, the stages built so far, are each parallel and are kept across edits, so that an edit reruns only what it affects; later stages are to follow the same rule.
- rejected: an agent proposed a lifecycle of whole-document passes guarded by dirty flags, as current engines run; the owner rejected it, because there a change to a layout property reruns most of the pipeline, and only changes the compositor handles alone stay fast.

### decision stages-keep-only-true-dependencies
Each stage keeps only its algorithm's data dependencies and writes all other work in forms Whitefoot proves independent, leaving what runs in parallel, and at what grain, to the compiler.
- replaced: The formatting context as the unit of parallel work was on main; the owner changed it, because one context holds 85 to 95 percent of each measured page's text, so layout split between contexts ran at 0.84 to 0.96 times sequential (data: `research/investigations/concurrency/DESIGN.md`).

### decision kept-stages-learn-changes-from-marks
A stage kept across edits learns what changed from marks the edit pushes, and the oracles check its result byte for byte against a full build.
- replaced: Memoizing each stage by its inputs, with a key the compiler proves complete, was on main; the owner changed it, because the compiler proves which places a function reads but not their versions, and names the document arena only as a whole.
- rejected: an agent proposed invalidation rules kept by hand, as current engines keep them; the owner rejected it, because nothing checks them, and a missed dependency renders stale output.
