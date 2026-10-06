# Design tree change log

Newest first. One entry per approved change of the tree: a dated title,
`Nodes:` naming every node changed, `Owner-approved:` and `Summary:`;
`skill/SKILL.md` owns the form.

## 2026-10-06 Keep style slots stable across structural edits and bound the insertion restyle

Nodes: pipeline/style

Owner-approved: The owner approved Q108, Q110, Q111 and Q113 during M2's work on 2026-10-05 and 2026-10-06, as research/investigations/structure-edits/DESIGN.md records under Decisions; on 2026-10-06, before the night's work, the owner wrote in Chinese that all the cards were agreed, among them the card asking leave to write this entry and merge M2's style steps once the completion review's findings were fixed and CI passed (Q119).

Summary: The style tree records two decisions of M2 steps 1 and 2. The kept style state's rows are stable slots: an insertion appends its elements' rows, a removal leaves holes the passes skip, and an edit takes depths from parents instead of building the traversal again (Q108, Q111), so no existing row moves and the full build keeps its order and parallel loops. An insertion or removal rematches, besides the inserted subtree, only the elements a structural reverse index names by their place around the edit point and the ancestor features their rules need (Q110, Q113), which on html5 brought one insertion's set from 58,230 elements to 548. The grounds are research/investigations/structure-edits/DESIGN.md, runs/structure-check.txt and runs/slots.txt.

## 2026-10-05 Keep the style stage across edits

Nodes: pipeline/style, pipeline/layout

Owner-approved: 2026-10-05, the owner wrote in Chinese that Q89 was approved provided the kept state's memory growth went into the TODO, then, after reading the detailed cards of Q90 to Q106, that all of them were approved.

Summary: The style tree now keeps the stage's state across edits. Its groups' identifiers and shared stores live in tables kept between edits, replacing per-run interning (Q83 retired; Q89, Q92); their growth is a TODO item the approval requires. A class edit's restyle set comes from a reverse index of the rules' class features, with a level frontier for inherited changes (Q91). Layout receives a sparse list of changed elements and marks only the paragraphs that read each one (Q93). Rules are indexed per selector alternative (Q99) and filtered by a feature filter of each element and its ancestors (Q100). A root font-size change restyles the elements that read the root's size (Q101). The layout tree records the re-stack decisions of the agent runs: the smallest common block, resuming after a paragraph with lines, marked child contexts settled at their entry, and translated fragments (Q95 to Q98). It also records glyphs kept in font units so that a size change rescales instead of reshaping (Q102), and Q70 reopened for M2 (Q104). NodeId-indexed state and per-parent positions are deferred to M2 (Q90, Q94). E1 is compared with Chromium in the edittime mode (Q103). Astra's colour branch stays unmerged (Q105). M2 comes next (Q106). The grounds and measurements are in research/investigations/incremental-style/DESIGN.md and its runs, step 5 above all.

## 2026-10-04 Keep layout across edits by marks pushed from each edit

Nodes: pipeline, pipeline/layout, pipeline/style

Owner-approved: 2026-10-04, the owner had agreed in Chinese to Q67 to Q73 as recommended; during the resumed work on mbbill/Snowghost#30 the owner chose Q83's option A, then wrote in Chinese that Q84 to Q86 were approved as recommended, that Q87 was approved, and, shown the card Q88 and the tree edits, that Q88 was approved and the close of X5 could proceed.

Summary: The layout tree records that a kept layout names elements by NodeId through an order map each style run rebuilds; that an edit reaches it as marks pushed toward the root (a text node's unit, a style delta of layout-relevant values, or one context built again), with updates recursing only into marked subtrees; the keys and cutoffs that decide what is redone, including whether a background is visible; offsets moved by one delta; and the structural update that builds again the nearest context from the walk's recorded state and refuses when the walk would leave it changed. The style tree records per-run interning with the delta mapping both runs' tables by value, and style attribute and hint records found by NodeId. The pipeline's memoization decision now states what the compiler proves (the places a function reads, not their versions) and that kept stages are checked against a full build byte for byte. The grounds, checks and measurements are in research/investigations/incremental-layout/DESIGN.md and its runs.

## 2026-10-03 Keep platform policy out of the renderer: facts in, policy out

Nodes: processes, pipeline

Owner-approved: 2026-10-03, after the discussion of retained-scene rendering and the shell's per-platform choices, the owner wrote in Chinese that they agreed to Q65 and to continue on that line; then wrote in Chinese that Q66 takes option A; then, shown the tree changes of mbbill/Snowghost#29 including the rename of layer trees to property trees, wrote in Chinese that #29 is confirmed.

Summary: The processes tree records that the renderer sends the shell facts about the page and never decides how they are drawn, while the shell owns every platform policy (how to draw, which pixels to cache, how to scroll and how to present), and that no policy changes the picture at rest, only its cost, because platforms differ in what their compositors and presentation interfaces allow, so these choices are measured and changed in the shell without touching the renderer; it refuses the renderer grouping content into compositing layers from hints. Its one exception (Q66) lets a cached subtree be resampled while a transform animation scales, rotates or moves it by a fraction of a pixel, the frame after the animation being exact again, and refuses holding animation frames to a full redraw's pixels. Since the renderer no longer builds layers, the processes and pipeline trees say property trees where they said layer trees. The grounds, the facts the shell needs and the measurements are in research/investigations/incremental/DESIGN.md, sections 6.3 and 7.

## 2026-10-02 Cascade the style stage's inherited values level by level

Nodes: pipeline/style

Owner-approved: 2026-10-02, after the handoff of mbbill/Snowghost#28's card Q64, the owner wrote in Chinese to rule Q64 as recommended: the inherited values are computed level by level.

Summary: The style stage's second part, which computes what the parent decides (font size, custom properties and inherited values), becomes a cascade level by level instead of one pass in document order: one counted loop per level of the element tree over the nodes that write nothing the levels share, proved parallel by Whitefoot's range facts and `apart` certificate, then the level's other nodes in document order, and the pseudo-elements after the last level, so the chain is the tree's depth. The pass in document order and a level loop with the shared stores behind a lock or a per-level merge are refused. The grounds, the byte-identical dumps and the measured times are in research/investigations/style/DESIGN.md, The level cascade.

## 2026-10-02 Record the layout stage's shape and follow Chromium where a specification differs

Nodes: pipeline, pipeline/layout, pipeline/style, vocabulary

Owner-approved: 2026-10-01, the owner approved the layout scope, oracle and criteria, including font matching through Snowghost's own table and scrollbars that take no space, and then wrote in Chinese that Q51 to Q58 were all approved as recommended and to start the implementation; 2026-10-02, the owner agreed in Chinese to Q59's recommended option A, first ruled Q60 to follow the Standard and then reversed it to follow Chromium for every difference (Q60 and Q61), and, shown the cards Q62 and Q63 with the tree edit that lifts the Q61 ruling to the pipeline, wrote in Chinese that they agreed to both.

Summary: The layout tree records font matching through Snowghost's own table of the reference's resolution on its host, scrollbars that take no space, text prepared per paragraph in one counted loop without a shared shaping cache, fragments written relative to their formatting context, intrinsic sizes computed on demand, tables per CSS Tables 3's draft with the reference's behavior for undefined steps, a limited multi-column layout laid out as one column and split by a column map, and counters and quotes resolved in the box tree builder's walk rather than a separate pass in the style stage. The style tree records generated boxes' styles in a sparse list beside the elements' and moves the user-agent sheet to the reference's computed values. The pipeline records the owner's rule that the renderer follows Chromium where a specification differs. The vocabulary tree adds the layout-only value groups and states each computed length's conversion to `LayoutUnit` as the reference's for its use, line heights included. The grounds and measurements are in research/investigations/layout/DESIGN.md.

## 2026-10-01 Record the real style stage's shape, value groups and units

Nodes: pipeline/style, vocabulary

Owner-approved: 2026-10-01, after the handoff of PR #24, the owner wrote in Chinese, item by item, to follow the Standard, agreed, agreed and approved: keep the HTML Standard's user-agent sheet without Chromium's table border color, agree to resolving `ex` and `ch` from the default fonts' metrics, agree to rounding lengths to `LayoutUnit` where layout reads them, and approve the tree changes; the stage's interface choices Q46 to Q50 had been approved earlier that day.

Summary: The style tree replaces matching followed by one cascade pass with three parts: a parallel loop that matches and selects each longhand's winning declaration by a key that needs no sorting, a pass in document order holding only what the parent decides (font size, custom properties and inherited values), and a second parallel loop for every other value, substituting `var()` per element with no shared cache, since a shared cache or one pass doing everything would order work that has no dependency. It records the user-agent sheet as the HTML Standard's rules with the reference browser's differences recorded, not copied, and `ex` and `ch` from the default fonts' metrics, provisional until the font stage matches families. The vocabulary tree names the eight computed-value groups and interns each as its own parallel task, still provisional on timing interning alone; keeps a percentage, alone or in `calc()`, unresolved until layout; and rounds a computed length to `LayoutUnit` once when layout reads it rather than at computed-value time. The grounds and measurements are in research/investigations/style/DESIGN.md.

## 2026-10-01 Record the shared vocabulary and the style and layout stages' shapes

Nodes: vocabulary, pipeline/style, pipeline/layout

Owner-approved: 2026-10-01, after the handoff of PR #23's decision cards Q36 to Q45, the owner wrote in Chinese that Q36, Q37, Q39, Q40, Q42, Q43 and Q44 were agreed, that Q45 must be recorded so that it is measured again when there are more real cases, that Q38 was fine once explained, and, after discussing a level-parallel cascade, chose C for Q41 and sent the Whitefoot capability to a separate investigation.

Summary: The vocabulary tree records the document as an index-linked arena, layout lengths as 1/64-pixel fixed point, names as atoms with generated indices, document text as one UTF-8 byte arena with script's lone surrogates decided when script lands, and computed styles as interned groups, provisional on the real groups and on remeasuring the sequential interning pass, which the rule index brought to 14 to 16 percent of the faster style stage. The style tree records matching every element in one parallel loop in document order followed by a cascade pass in document order, which is to cascade each level in parallel once Whitefoot can prove writes through distinct indices disjoint, plus the rule index and the sibling-position table. The layout tree records the owned formatting-context tree with speculative line breaking, provisional until the incremental prototype decides the unit of invalidation, and the box tree built by a walk followed by a decoding loop, provisional until more real pages measure it. The grounds are the concurrency investigation's measurements, research/investigations/concurrency/DESIGN.md, and the revised proposal in research/investigations/vocabulary/DESIGN.md.

## 2026-09-29 Parallelize every stage by its true data dependencies

Nodes: pipeline

Owner-approved: 2026-09-29, the owner approved the pipeline-parallel-principle amendment of PR #14 as shown, applied unchanged apart from its replacement note, writing in Chinese that it was acceptable, after agreeing that the pipeline's second decision must change and that the maximal-parallelism principle belongs in the design tree.

Summary: The pipeline tree replaces the independent formatting context as the unit of storage, parallel work, invalidation and caching with a principle: every renderer stage keeps only its algorithm's true data dependencies, writes all other work in forms the Whitefoot compiler proves independent, takes extra or speculative work where it shortens the critical path, and leaves which independent work runs in parallel, and at what grain, to the compiler and runtime, because a stage's time on P cores is about its work over P plus its critical path. Two alternatives are refused on the concurrency investigation's layout measurement: the context as the unit of parallel work, since one block formatting context holds 85 to 95 percent of the text on each measured real page and context-only layout ran at 0.84 to 0.96 times the sequential build at four workers, and paragraph parallelism only in float-free contexts, since the dominant context holds a float on two of the three pages. Whether the context remains the unit of storage, invalidation or caching is left open in research/investigations/concurrency/DESIGN.md, not decided. The owner also ruled that speculative computation is acceptable and that floats may be approximated where the deviation is small, which the scope tree's existing decision already covers.

## 2026-09-28 Adopt the scope, pipeline, script and processes decisions

Nodes: scope, pipeline, script, processes

Owner-approved: The owner approved decision cards #10 and #11 in conversation, writing in Chinese that both were agreed, for the pipeline and script amendments exactly as shown in PR #2, adding for pipeline that many details remain to be refined later and for script that the tail-call lowering can certainly be done. The owner then approved decision card #14 with its follow-up, writing that the split is reasonable and decided: a renderer process written in Whitefoot, like a browser's renderer process, and a Rust shell that owns windows, input, accessibility, rasterization and compositing on existing libraries such as Skia, networking and storage, connected by a display-list and layer-tree format, with the pipeline's purity decision narrowed to the renderer's stages. The owner approved decision card #9 with a further selection criterion, then confirmed decision card #12, writing in Chinese that all was agreed, for the revised scope amendment as shown in PR #2: the subset chosen feature by feature, weighing use against performance cost with performance winning over strict conformance, and the renderer written in Whitefoot. After the completion review, the owner approved decision cards #16 and #17 on 2026-09-28, writing in Chinese that both were agreed: the script tree's reason names a renderer that relies on memory safety instead of per-site processes, and the pipeline tree's unit applies in every renderer stage.

Summary: The scope tree records that Snowghost implements a subset of the web platform chosen feature by feature, weighing use against performance cost, and that its renderer is written in Whitefoot. The pipeline tree records that every stage is incremental and parallel end to end, that the independent formatting context is the unit of storage, parallel work, invalidation and caching, and that each renderer stage up to display lists and layer trees is a pure Whitefoot function memoized by its inputs. The script tree records an interpreter written in Whitefoot with no just-in-time compiler, dispatching through a match lowered to a tail-call chain, provisional until Whitefoot provides that lowering. The processes tree records the split into a Whitefoot renderer and a Rust shell, the data boundary between them, and what each owns. The reasons are in research/investigations/architecture/DESIGN.md.
