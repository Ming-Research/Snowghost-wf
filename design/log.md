# Design tree change log

Newest first. One entry per ruling on the tree, an approved change or a
refused amendment: a dated title, `Nodes:` naming every node changed or ruled
on, `Owner-approved:` for an approved live-tree change, and `Summary:`;
`skill/SKILL.md` owns the form.

## 2026-09-28 Adopt the scope, pipeline, script and processes decisions

Nodes: scope, pipeline, script, processes

Owner-approved: The owner approved decision cards #10 and #11 in conversation, writing in Chinese that both were agreed, for the pipeline and script amendments exactly as shown in PR #2, adding for pipeline that many details remain to be refined later and for script that the tail-call lowering can certainly be done. The owner then approved decision card #14 with its follow-up, writing that the split is reasonable and decided: a renderer process written in Whitefoot, like a browser's renderer process, and a Rust shell that owns windows, input, accessibility, rasterization and compositing on existing libraries such as Skia, networking and storage, connected by a display-list and layer-tree format, with the pipeline's purity decision narrowed to the renderer's stages. The owner approved decision card #9 with a further selection criterion, then confirmed decision card #12, writing in Chinese that all was agreed, for the revised scope amendment as shown in PR #2: the subset chosen feature by feature, weighing use against performance cost with performance winning over strict conformance, and the renderer written in Whitefoot. After the completion review, the owner approved decision cards #16 and #17 on 2026-09-28, writing in Chinese that both were agreed: the script tree's reason names a renderer that relies on memory safety instead of per-site processes, and the pipeline tree's unit applies in every renderer stage.

Summary: The scope tree records that Snowghost implements a subset of the web platform chosen feature by feature, weighing use against performance cost, and that its renderer is written in Whitefoot. The pipeline tree records that every stage is incremental and parallel end to end, that the independent formatting context is the unit of storage, parallel work, invalidation and caching, and that each renderer stage up to display lists and layer trees is a pure Whitefoot function memoized by its inputs. The script tree records an interpreter written in Whitefoot with no just-in-time compiler, dispatching through a match lowered to a tail-call chain, provisional until Whitefoot provides that lowering. The processes tree records the split into a Whitefoot renderer and a Rust shell, the data boundary between them, and what each owns. The reasons are in research/investigations/architecture/DESIGN.md.
