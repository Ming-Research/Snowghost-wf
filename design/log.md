# Design tree change log

Newest first. One entry per ruling on the tree, an approved change or a
refused amendment: a dated title, `Nodes:` naming every node changed or ruled
on, `Owner-approved:` for an approved live-tree change, and `Summary:`;
`skill/SKILL.md` owns the form.

## 2026-09-28 Adopt the pipeline and script decisions

Nodes: pipeline, script

Owner-approved: The owner approved decision cards #10 and #11 in conversation, writing in Chinese that both were agreed, for the pipeline and script amendments exactly as shown in PR #2; for pipeline the owner added that many details remain to be refined later, and for script that the tail-call lowering can certainly be done.

Summary: The pipeline tree records three decisions: every stage from the document to the screen is incremental and parallel end to end; the independent formatting context is the unit of storage, parallel work, invalidation and caching; and each stage is a pure Whitefoot function memoized by its inputs, so the compiler proves the key complete. The script tree records an interpreter written in Whitefoot with no just-in-time compiler, dispatching through a match lowered to a tail-call chain, provisional until Whitefoot provides that lowering. The reasons are in research/investigations/architecture/DESIGN.md.
