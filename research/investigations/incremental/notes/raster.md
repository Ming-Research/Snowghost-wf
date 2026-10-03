# Branch "raster": from changed display content to pixels at 120-240 Hz, without tiles/layers as the invalidation unit

Author's note on evidence marks used throughout:
- **[cited]** = taken from a page I fetched/searched in this session (URL given).
- **[memory]** = established practice I know from training; not re-verified here. Treat as a lead.
- **[measured]** = I ran it in this container (`census/raster-bench.c`, gcc -O3, Xeon 2.1 GHz, 4 vCPU, no GPU).
- **[derived]** = arithmetic from stated assumptions; the assumptions are listed.
- **[speculation]** = my hypothesis, needs an experiment.

Status vocabulary: established / promising / uncertain / hard / likely dead end.

**Corrections after the GPU survey and the owner's discussion.** This note
was the first pass. Where the sections below disagree with these, these
win; `DESIGN.md` §7 holds the current tree.
- §3.1, Metal: Mozilla stated in 2019 that `CAMetalLayer` has no partial
  update and that smaller layers are the way around it; that has not been
  rechecked since (X18). Presentation tiles are then needed on macOS as a
  presentation unit (`webrender.md` I4; `DESIGN.md` 7.4).
- §3.2 P1: wgpu 30's surface appears to expose no buffer age or swapchain
  image index (an open question), and its DX12 and Metal backends have no
  damage path, so P1 is planned on buffers the shell owns, presented
  through each platform's own interface (`gpu2d.md` §4.3; `DESIGN.md`
  7.3).
- §3.2 P2: a dead end rather than the default fallback. Copying a full
  target to the swapchain every frame moves more bytes than a plain full
  redraw writes (`DESIGN.md` 7.3).
- §3.2 P5: OS layers are revived for scrolling where the OS takes several
  surfaces: prepainted strips moved by one container transform remove the
  shell's drawing from a scroll frame (`DESIGN.md` 7.5, method C).
- §5.1: the rule for caching an animated subtree, and where its texture
  goes, is in `DESIGN.md` 7.6.

---------------------------------------------------------------------------
## 0. What this container can and cannot measure (read first)

Checked: no `/dev/dri`, no `libEGL`, no Vulkan ICD (`/usr/share/vulkan/icd.d` absent; `libvulkan.so.1` loader only), Mesa gallium library present but no software Vulkan (lavapipe) or EGL front end, no X/Wayland. `node` 22 is present, no browser. So:

- **Measurable here:** everything on the CPU side of the shell: scene index query cost, reflow-shift cost, delta sizes, glyph/pixel blit throughput of a CPU rasterizer as a *proxy*, and correctness oracles (damage redraw == full redraw, pixel-exact) using a software rasterizer.
- **Needs real hardware:** GPU time per frame, power, present-to-photon latency, driver behaviour of buffer age / partial present / PSR, tile-based-GPU behaviour. Nothing in section 4 about GPU speed is measured; it is arithmetic plus cited behaviour. Do not take a GPU number from this file as a result.

Frame budgets [derived]: 120 Hz = 8.33 ms, 144 Hz = 6.94, 165 Hz = 6.06, 240 Hz = 4.17 ms. Everything after the renderer produced new data (delta transport, shell scene update, GPU, present) shares that budget with the next frame's work.

Scale facts about our pages [measured by others, `build/research/concurrency/layout-results.txt`]: ecma262 has 179,471 elements, 9,931 formatting contexts, 37,485 paragraphs, 2,025,062 scalars. Line count and paint-item count are **not** measured; my benchmark assumes 250,000 paint chunks (one per line fragment plus decorations), which is a guess consistent with 37k paragraphs and 2.0M scalars. One block formatting context holds 85-95% of the text on all three pages (layout DESIGN / pipeline.md "Rejected"), so a single context has on the order of 10^5 children. This shapes everything in sections 2-3: any structure that is "a flat list per context" is a 10^5-element list.

---------------------------------------------------------------------------
## 1. Framing: what a frame must cost, and the one claim worth testing

Claim C1 [speculation, derived below]: **for text- and rectangle-dominated pages, redrawing vectors/glyph-quads from a retained scene is cheaper per pixel than sampling a cached texture of the same region**, because ink coverage is low. If true, "cache pixels" only pays for subtrees that are expensive to draw (overdraw depth > ~2, blur/shadow/filter/backdrop, large path fills, video), and the right policy is a per-subtree cost decision, not a geometric tiling.

Derivation [derived; assumptions: 1920x1080 viewport, 16 px body text, ~22 px line pitch, ~240 chars/line over full width (an upper bound for readable pages), 8 px average advance]:
- ~49 lines x ~240 = ~12k glyph quads per full viewport. At ~32 B/instance (pos, atlas rect, color, clip index) = ~0.4 MB of instance data per frame; the pixel buffer is 8.3 MB (1080p) / 33 MB (4K).
- Glyph fill ~10x14 px each => 12k x 140 = 1.7 Mpx, which is less than the 2.07 Mpx of the screen itself. So drawing *all* the text costs less fill than a single full-screen blit, plus the background fill (one more screen-sized pass). A texture-cache blit of the same viewport is >= one screen-sized pass. The vector path is therefore at most ~2x the cache path in fill and may be less (the background is shared), and it has no cache to invalidate.
- Memory traffic is the energy cost, not ALU: full-frame write at 240 Hz = 1080p: 2.0 GB/s; 4K: 8.0 GB/s, before reads for blending/composition. [derived]. That is why damage matters for power and thermals even when the GPU has time to spare.

CPU proxy [measured, this box, 1 core, scalar-ish C auto-vectorized, -O3 -march=native]:
- Blending 20,000 atlas glyph masks (10x14, 8-bit coverage) into a 1080p BGRA buffer: **4.0 ms, ~200 ns/glyph, 0.70 Gpx/s**. A *CPU* rasterizer with an atlas would redraw a whole text-heavy 1080p viewport (~12k glyphs) in ~2.4 ms on one core, ~0.6 ms on four if rows are partitioned. Say this carefully: it shows the glyph-blit workload is small, not that a CPU should do it.
- Full 1080p frame `memcpy` (8.3 MB): **~0.9 ms** (~9.5 GB/s, single core). Scroll-by-`memmove` of 22 rows: **~0.35 ms**.
- Interpretation: on this CPU a full-viewport text redraw and a full-viewport pixel copy are the same order of magnitude (2.4 ms vs 0.9 ms single-core). A GPU changes both by roughly 1-2 orders of magnitude but probably *not their ratio*, since both are bandwidth-bound; this ratio is exactly what experiment X3/X4 must measure on a GPU.

Frame-time conclusion [speculation]: on any current dGPU/iGPU, redrawing the whole viewport of glyph quads is very probably <1 ms; the real arguments for damage-limited rendering are (a) power and memory bandwidth at 4K/240 Hz, (b) weak GPUs/phones, (c) shorter GPU latency for the changed frame, (d) letting the compositor and panel skip work (section 3). Do not justify damage tracking by "the GPU cannot keep up" before X3 says so.

---------------------------------------------------------------------------
## 2. Renderer: what GPU 2D systems do on a small change

### 2.1 Vello (compute-shader, full scene per frame)
Status: **promising for vector-heavy content, uncertain-to-unfit as the primary text path** (as of the sources below).
- Model [memory, plus cited README summary]: user code builds a `Scene` (a flat encoding: path tags, segments, draw tags/data, transforms) each frame, uploaded and processed by ~a dozen compute dispatches (flatten, binning into 16x16 tiles, coarse per-tile command lists, fine rasterization). Cost = CPU encode (O(scene)) + GPU stages (O(scene size + covered area)) + a fixed dispatch floor. Upstream `RenderParams` has no damage rect [memory]: a one-pixel change costs the same GPU pipeline unless the caller shrinks the scene.
- Partial updates: scene *fragments* can be built once and appended (cheaper CPU encode) but are still re-processed on the GPU each frame. A third-party fork reports a persistent render target + damage tracker (node painted rect + paint-state fingerprint), with partial redraw costing "3.7-4.9x less per frame than full" in a 1920x1080 window with a small animation [cited, unverified third-party claim: https://github.com/mindderivative/tre/pull/17 and issue https://github.com/mindderivative/tre/issues/4]. That is evidence that the technique ("persistent target + redraw only the damaged part of the scene + copy to swapchain") is workable; it is not evidence about text pages.
- Glyphs: upstream glyph caching is described as experimental/not recommended; the sparse-strip successor (`vello_hybrid`/`vello_cpu`) is described as potentially allowing retained rendered paths "essentially the same functionality as glyph caching" and as beta quality [cited: https://github.com/linebender/vello/issues/670 , https://docs.rs/ps-vello-hybrid/latest/vello_hybrid/ , https://linebender.org/blog/tmil-25/].
- Pattern worth keeping: **Vello as a damage rasterizer** [speculation]: the shell culls the retained scene to the damage rect, encodes only that subset translated to the rect origin, renders to a small texture, blits into the persistent target. Cost = fixed dispatch floor + O(damage). Good for SVG/canvas-like content, shadows/gradients/paths; probably worse than an atlas quad pass for plain text.
- Needs from Whitefoot: nothing special beyond the item stream in section 3. Experiment: X5.

### 2.2 WebRender (retained scene, picture caching)
Status: **established, and the closest relative of what we want, but its invalidation unit is a tile**.
- Facts [cited: https://doc.servo.org/webrender/picture/index.html , https://doc.servo.org/webrender/picture/struct.TileCacheInstance.html]: the scene is cut into few "slices"; each slice is a grid of tiles with cached textures; each tile records its dependencies (primitives, clips, image keys, opacity bindings, transforms), rebuilt each frame and compared to the previous frame; dependencies are in a quadtree per tile; the union of invalidated leaves gives a per-tile **dirty rect used as the scissor when replaying that tile's commands, and usable for partial present**. Tiles can be "clear tiles" (solid color, drawn in the composite pass, no texture). Large or often-changing primitives (video, WebGL) can be native compositor surfaces so they do not invalidate tiles; this is explicitly a power win.
- What it shows: (1) *the dirty region is not a tile*: WebRender already scissors to the union of invalidated quadtree leaves inside a tile, i.e. sub-tile damage is established practice; (2) dependency comparison per frame is O(items in slice) every frame unless the scene builder delivers deltas; (3) tiles exist to serve scrolling (cached pixels) and picture-level isolation, not to bound damage.
- Costs to us: the per-frame dependency diff is exactly the "hand-maintained invalidation" the owner wants to avoid; in our design the renderer emits a delta, so the diff is unnecessary.

### 2.3 Skia Ganesh / Graphite, Chrome's viz
Status: **established; Skia is an immediate 2D API, retention and damage live above it**.
- Graphite replaces Ganesh in Chrome (Dawn/WebGPU backend, multithreaded recording, fewer code paths, compute path rendering); shipped by default on Apple Silicon Macs with ~15% rendering gain [cited: https://www.osnews.com/story/142739/introducing-skia-graphite-chromes-rasterization-backend-for-the-future/].
- Chromium viz tracks damage per render pass (`DamageTracker`, accumulating the **union** into one rect: two distant small changes become one large rect), uses it as the draw scissor and swap rect, and for platforms without buffer-age support tracks per-buffer damage over `number_of_buffers` (`FrameBufferDamageTracker`) [cited: https://hackmd.io/@elkurin/r1Ux087ST and chromium.googlesource.com viz sources from the search]. Cost lesson: single-rect union is a real limitation; a damage *list* with a cost-based merge is better (section 3.3).
- Skia as our shell library (pipeline.md): fine for the first iteration, but the retained scene, spatial index and damage logic are ours regardless; Skia would be a "draw these items into this clip" executor. Its glyph path uses atlas/SDF/path by size [memory].

### 2.4 Pathfinder, Rive, Slug, immediate-mode GPU UI
- **Pathfinder** (Servo/Patrick Walton): GPU vector/text rasterizer; repository archived [memory]; dead end as a dependency; historical value only.
- **Rive renderer**: GPU vector animation renderer using pixel-local-storage or raster-ordered-view paths; redraws the artboard per frame [memory]; no retained damage model; not a text-page tool.
- **Slug** (Lengyel): resolution-independent text by evaluating Bezier coverage per pixel from curve data in a texture, no atlas; patent dedicated to the public domain on 2026-03-17 [cited: https://hackaday.com/2026/03/20/slug-algorithm-for-on-gpu-rendering-of-fonts-with-bezier-curves-now-in-public-domain/ , https://alphapixeldev.com/sdf-vs-msdf-vs-slug-vs-rive-gpu-text-rendering/]. Status: **promising for scaled/rotated/animated text and zoom; uncertain for 16 px static text** where a one-sample atlas quad needs less shader work per pixel and can use hinting/pixel-snapped coverage matching Chromium [speculation]. Removes atlas-miss stalls and the "re-raster on every zoom step" problem; costs a larger vertex/fragment workload (a loop over the glyph's curve bands) per pixel. Experiment X5.
- **Zed GPUI** [cited: https://zed.dev/blog/videogame , https://deepwiki.com/zed-industries/zed/2.2-ui-framework-(gpui)]: per-frame rebuild of a retained `Scene` of quads/glyph-atlas sprites/paths/underlines; OS APIs shape text, glyph atlas on GPU with a cache of shaped runs; batches per primitive type and blend; Metal/Vulkan/DX12; 120 fps target. Existence proof that *full* redraw of atlas-quad scenes at 120 Hz is routine for UI-sized scenes (thousands of primitives). Not proof for a 10^5-run document unless culled by an index (which GPUI's immediate-mode element tree does by not building off-screen elements; we must index instead).
- **Makepad / game engines / Unity UGUI** [memory, low confidence]: draw-list/canvas batching; the known pain is *rebatching* a whole canvas when any element changes (Unity UGUI "canvas rebuild"); i.e. batching granularity is the hidden invalidation unit. Lesson for us: instances must be independently addressable (stable slots) so a change rewrites its own slot and nothing else.

### 2.5 Question: can we redraw exactly the damaged region from a retained scene with a spatial index?
Status: **established technique, promising for us**, with four conditions.
1. **Complete overlap set**: redraw *every* item whose bounds intersect the damage rect in paint order, scissored to the rect. Pixel-identical to full redraw if blending is deterministic and every intersecting item is included. Occlusion culling is optional and must not change pixels.
2. **Damage inflation**: items that read the backdrop or spread beyond their bounds (blur, drop shadow, backdrop-filter, mix-blend, filters, LCD text sampling neighbours) must declare `reads_backdrop`/`spread`; shell expands damage by those. This is the data-coupling statement in explicit form; it should be a field, not an inference.
3. **Paint order is tree order**: the index must be the *paint tree itself* (stacking contexts, then flow), visited in paint order, so pruned DFS emits items in order without sorting. A purely geometric index (grid/R-tree) loses order and needs a sort by sequence number.
4. **Presentation agrees**: either age-tracked buffers or a persistent target (section 3).

Measured [bench.c, 250k chunks; after the shifts, the hit arrays (not only counts) of the tree, y-sorted and linear methods were compared for 500 viewport queries: identical]:

| operation | method | cost |
|---|---|---|
| index build (all 250k chunks) | 16-ary tree, depth 6 | 3.7 ms one-off |
| query 1920x1080 (~56 hits) | y-sorted array + binary search on prefix-max bottom | 0.55 us |
| query 1920x1080 | 16-ary tree with relative offsets | 0.87 us |
| query 300x40 (~3 hits) | y-sorted / tree | 0.33 / 0.44 us |
| query any | linear scan (baseline) | 200-260 us |
| reflow shift of ~245k later chunks | rewrite absolute coordinates | **~195-240 us measured** (the benchmark writes 8 B/chunk, ~2 MB; 4.9 MB is the **derived** transport size at an assumed 20 B/chunk) |
| same shift | relative-offset 16-ary tree | **0.04 us measured; at most 80 node writes** (computed as F x (depth-1), an upper bound, not a counter) |

Reading it honestly:
- Finding the visible/damaged items costs ~1 us: **the spatial index is irrelevant to the frame budget** at this scale; pick whichever is simplest. This removes "need a heavyweight R-tree/BVH" from the worry list. Caveat: my synthetic scene is flow-ordered (y-monotone) with 2% tall overlapping boxes; scenes with many large overlapping absolutely positioned layers, transforms and clips stress it more. Not measured.
- The *shift* is cheap on the CPU (0.2 ms measured) but **its cost is bytes** [derived]: ~4.9 MB of coordinate rewrite per paragraph height change if each chunk's position record is 20 B (assumed; the benchmark itself touches 8 B/chunk) if absolute positions cross the process boundary or must be re-uploaded as GPU instance data; the relative-offset tree turns that into at most ~80 node writes (upper bound, F x (depth-1)). Over shared memory at 10 GB/s, 4.9 MB is ~0.5 ms and pollutes caches; the GPU instance buffer would need a full re-upload unless the shader applies per-chunk offsets from a small buffer (section 3.2).
- Important: a reflow that moves everything below *also damages the whole viewport if the viewport is below the change*. The relative representation saves transport/CPU work, not pixels. Pixel damage is decided by what is on screen.

---------------------------------------------------------------------------
## 3. Presentation

### 3.1 What partial present buys and does not buy
Established facts [cited unless marked]:
- The display scans out the full frame every refresh regardless [memory]; "partial" saves GPU rendering, memory traffic and compositor work, and enables panel self-refresh, not scanout time. Claims of latency savings come from shorter GPU/compositor work for that frame.
- **EGL**: `EGL_EXT_buffer_age` reports how many frames old the back buffer is; `EGL_KHR_partial_update` / `EGL_EXT_swap_buffers_with_damage` / `EGL_KHR_swap_buffers_with_damage` take damage rects. Distinction: partial_update = damage relative to *this buffer's contents* (age-based); swap_buffers_with_damage = damage relative to the *last frame* for the compositor [cited: https://registry.khronos.org/EGL/extensions/KHR/EGL_KHR_swap_buffers_with_damage.txt , https://mesa-dev.freedesktop.narkive.com/rCRL1z1Z/question-about-egl-khr-partial-update-implementation , Weston gl-renderer partial update commit https://cgit.freedesktop.org/wayland/weston/commit/?id=df2095fa35fe84e4ebc30754dd9f25e50bd1aa47 ]. Mozilla's Android notes show partial compositing via these [cited: https://bugzilla.mozilla.org/show_bug.cgi?id=1484812, 1575765].
- **Wayland**: `wl_surface.damage_buffer` tells the compositor what changed so it skips recomposition; also `wp_viewporter` (source-rect crop/scale), `presentation-time` (actual present timestamps), frame callbacks [memory].
- **Windows**: DXGI flip model `Present1` with `pDirtyRects` and `pScrollRect/pScrollOffset`: the OS only copies/composes what changed, saving memory bandwidth and power; dirty rects must contain every changed pixel and the app may not assume contents persist in them; scroll rect = region of the previous frame the OS copies before the app draws; unsupported with discard/sequential effects and with multisampled swap chains [cited: https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-1-2-presentation-improvements]. Also DirectComposition and waitable swap chains for latency [memory].
- **Vulkan**: `VK_KHR_incremental_present` gives present regions; **no buffer-age query**, so the app tracks which swapchain image holds which frame and unions damage itself [memory]. Chromium does exactly this for platforms without age [cited above].
- **Metal / CoreAnimation**: `CAMetalLayer` has no public dirty-rect present as far as I know [memory, low confidence, not searched; verify before relying on it]; ProMotion variable refresh via display link; Apple GPUs are tile-based deferred (TBDR) so the cost model differs (below).
- **DRM/KMS**: atomic commit with plane properties; `FB_DAMAGE_CLIPS` per plane enables selective update on panels with PSR2/selective-update; overlay planes can carry video or a scrolled surface; compositors fall back to GPU composition when planes cannot be used [memory].
- **Variable refresh (VRR/adaptive sync)** decouples present time from the refresh grid; the biggest power win is *not presenting* when nothing changed, plus accurate frame pacing [memory].

### 3.2 Our options (tree)
- **P1. Age-tracked buffers + scissored redraw (EGL partial_update; Vulkan with app-side age)** — established; cheapest in memory; complexity = per-buffer damage history (we have to maintain it anyway for P2); correctness risk in resize, swapchain recreation, driver-dependent age reporting (some drivers report age 0 forever = full redraw). Status: **established, promising as the main path.**
- **P2. Persistent offscreen target + damage-scissored draw + copy-to-swapchain** (what the Vello fork does) — status: **established, simple, promising as the default fallback.** Cost: one extra pass of copy (can be restricted to the damage rects, or full frame: 8.3 MB at 1080p; measured CPU memcpy 0.9 ms, a GPU does it in a small fraction of that). Avoids age tracking and works on every API; costs memory (one more full-size texture) and one more full-frame bandwidth item if the copy is full-frame; pair with present-with-damage so only damaged rects are copied *and* reported.
- **P3. Scroll by copying previous pixels (DXGI scroll rect; Chromium/hwui style) + draw the exposed strip** — established. Cost: copy of the retained area; breaks for sticky/fixed overlays (they must be redrawn or composited above), for fractional scrolling with subpixel text positions, and when the scrolled area is simultaneously damaged. Alternative P4 below is simpler for a 10^5-item scene because the viewport redraw is cheap (Claim C1).
- **P4. Scroll = redraw viewport from the retained scene with a changed offset uniform** — promising as *default*; zero cached pixels, zero invalidation; cost = O(items in viewport + overscan), ~12k instances (section 1). Text positions are snapped to whole device pixels along the scroll axis (as Chromium does) so the atlas glyphs stay crisp and bit-identical frame to frame [memory]. Measurement X4 decides vs P3.
- **P5. Hardware planes / compositor subsurfaces (KMS planes, Wayland subsurfaces, CoreAnimation/DirectComposition visuals) for: video, canvases, the *overscan scroll surface*** — established for video/canvas (WebRender compositor surfaces); for scrolling text pages it **degenerates into tiling a big texture** (to scroll with `wp_viewporter` crop or a plane offset you need the pixels), so use it only for content whose pixels already exist as a buffer. Status: **established for media; likely dead end as the page-scroll mechanism**.
- **P6. Panel self-refresh / selective update through `FB_DAMAGE_CLIPS`** — promising for laptop battery; only reachable if the shell owns the DRM path (e.g. a kiosk/embedded mode) or the compositor forwards our damage. **Uncertain**; needs real hardware (X7).
- **P7. TBDR/mobile GPUs** [memory]: on Mali/Adreno/Apple the hardware itself bins into tiles; a render pass that loads the previous contents pays a full-tile load/store unless the driver knows the damage (partial_update) or a scissor limits binned tiles. So on those GPUs "avoid tile-sized granularity" cannot be total: the hardware's tile is the floor for the memory cost, and the savings of damage-limited rendering come from skipping tiles entirely. This favours P1/P2 with accurate damage on mobile. **Uncertain**; X3 on a phone.

### 3.3 Damage representation and merging
- Damage per frame is a **list of rects in device pixels** (not one union rect; Chromium's union is the cautionary example), bounded to K (4-8), merged by a cost rule: merge A,B if `area(A∪B) - area(A) - area(B) < overhead_px` where `overhead_px` ≈ per-rect pass cost / per-pixel cost on the device (measure it, X3). For scattered tiny changes (cursor + one text line + a button hover) this gives 3 small rects, not one half-screen rect.
- Computation: damage = ∪ over changed chunks of transform(old_bounds ∪ new_bounds) through the transform tree, inflated by `spread`/`reads_backdrop`. Old bounds must be kept by the shell (a field in its chunk table) or sent by the renderer. Cost ∝ number of changed chunks.
- Animation: a subtree whose transform is animated in the shell contributes `old ∪ new` bounds per frame; if its content is unchanged the shell redraws only that subtree plus whatever it uncovers: this is the "compositor-only animation" of pipeline.md, but with exact damage instead of a layer.

### 3.4 Latency path [derived + memory]
input event → (shell) → renderer (style/layout/paint delta) → shell scene update → damage → GPU → present → scanout. Rules that follow:
- Scroll/pinch/transform animations are decided *in the shell from the already-held scene* (as in compositor-thread scrolling) without waiting for the renderer; the renderer learns the new viewport asynchronously and may refine. This only works if the shell holds scene content beyond the viewport (overscan in scene space, *not* pixel space): free in this design because scene data is cheap to keep and rasterization is per frame.
- One frame of present queueing is the norm (double buffer); latency-critical updates use waitable/low-latency swapchains (DXGI), `VK_EXT_present_mode`/mailbox, Wayland `presentation-time` + commit-timing, tearing-control for opt-in tearing [memory]. These are policy, orthogonal to the scene design.
- Frame-miss policy (what tiles used to give via "checkerboarding"): when a frame's work would miss the deadline, redraw less (previous frame + damage-limited partial update of the most important region), never block on rasterizing content that has not been drawn yet. Since drawing is per frame and cheap, the only real stall sources are glyph-atlas misses, image decode/upload and expensive subtrees (below). Status: **uncertain, needs a design**.

---------------------------------------------------------------------------
## 4. Text rendering: the dominant item

Text dominates the paint workload on our three pages (ecma262: 2.0M scalars; html5, apollo11 similar). Frame cost on text = (number of visible glyph instances) x (cost per instance) + atlas misses.

- **T1. Glyph atlas + instanced quads** (GPUI, Skia, WebRender, most engines) — **established, promising as baseline**. Instance = (glyph id slot, position in item-local coordinates, color/paint index, clip/transform index). Atlas key = (font face id, glyph id, size, subpixel x-bucket, variation/hinting mode). Working set for Latin/mixed pages is a few hundred glyphs x few sizes = a few hundred KB; CJK-heavy pages tens of thousands of glyphs = low tens of MB if sized small [derived/speculation]. Atlas misses are the only data-dependent stall; rasterize outlines (FreeType-class) on a worker, draw missing glyphs the next frame or with a fallback (path draw/Slug) — never block the present on a miss.
  - Ownership question: pipeline.md says the renderer shapes text and validates fonts; the shell rasterizes. The data crossing the boundary is then (font id, glyph ids, positions) per run plus *validated font outlines* (or the font file the renderer already validated) so the shell does not parse untrusted fonts on its own: the font bytes' safety is a renderer-process property. Open question: send glyph *outlines* (validated, simple data) to the shell instead of the font binary, which removes the shell's need to parse font tables at all. [speculation, promising for the trust boundary].
  - Subpixel positioning: horizontal subpixel buckets (4 is typical [memory]); vertical snapped. LCD subpixel AA requires an opaque known backdrop and breaks under transforms/opacity groups; grayscale AA is the transform-safe default. Scroll-by-pixel keeps cache keys stable.
- **T2. Direct-curve text (Slug, now free to implement)** — promising for zoom, rotation, large/animated text, no atlas, no re-raster. Evaluate cost at 16 px static text vs T1 (X5).
- **T3. SDF/MSDF atlas** [memory]: scale-flexible, poor at small sizes (blurry corners, no hinting); likely dead end for body text, fine for large display text.
- **T4. Vello glyph path** — see 2.1; not recommended until glyph caching/sparse strips mature; **uncertain**.
- **T5. Text as vector paths in the generic path renderer** — likely dead end at 10^5 glyphs per page unless cached as atlas.
- Cost decision per text item [speculation]: use atlas for sizes <= ~64 px with no non-axis-aligned transform; use direct-curve or path for others; the *shell* chooses per frame from the transform and size, since the renderer's item says only "glyph run at local coordinates, nominal size".

---------------------------------------------------------------------------
## 5. Scrolling and animation without re-rasterization; when to cache pixels

### 5.1 Decision rule (replaces fixed tile/layer policy)
Status: **promising [speculation]**.
For a subtree S and a region/rate of change:
- `draw_cost(S)` = instances x instance cost + sum of covered pixels per layer of overdraw x per-pixel cost + expensive operators (blur, backdrop, big path, gradient stacks, shadows).
- `reuse_cost(S)` = sampling the cached texture over S's screen bounds + the amortized cost of re-raster whenever its content or scale changes + memory.
- Cache S as a texture iff `draw_cost(S) x P(S stays unchanged for the next frames) > reuse_cost(S)`, with hysteresis; demote when changed repeatedly. Measure `draw_cost` with GPU timestamp queries (EWMA per subtree), not estimates, after a cold start from the static estimate.
- By Claim C1 plain text/rect subtrees essentially never qualify; subtrees with deep overdraw, filters/shadows/backdrop blur, large SVG, offscreen groups with opacity < 1 containing many items (group needs an offscreen anyway: that *is* the layer, created by semantics not by policy) do.
- Mandatory offscreens by semantics, independent of the cost rule: `opacity < 1` on a group with overlapping children, `mix-blend-mode`, `filter`, `backdrop-filter`, `clip-path`/mask with antialiasing over a group. These need an intermediate target in every renderer; keep them as *render-graph nodes with bounds*, not as persistent layers; reuse the texture only if the cost rule says so.
- Fixed/sticky/overlays: they are scene items with a different transform parent; the scroll offset applies to a different node; no layer needed.
Existing practice that is similar [memory/cited]: WebRender picture caching also decides cache vs redraw per slice using dependency tracking; Android RenderNode "hardware layers" and Chrome `will-change` heuristics are hand rules; ours is cost-driven.

### 5.2 Transform tree
Status: **established**, required. Shell nodes: `{parent, local transform (static or animation descriptor), clip, effect}`; items reference a node id. Scroll offset is a transform node. Animations of transform/opacity are evaluated per frame in the shell; subtree bounds give damage. Because items are in local coordinates, animating a subtree changes one node, not its items (and the renderer's paint memo key excludes position, matching Q55).

### 5.3 What the retired tile/layer unit actually provided (to be replaced, not forgotten)
1. Bounded damage granularity -> replaced by exact rect lists (3.3).
2. Zero draw cost for scrolled-but-unchanged pixels -> replaced by cheap per-frame redraw of ~12k instances (C1) or, if X4 says copy wins, P3 for the scroll axis only.
3. Async raster off the frame path with checkerboard fallback -> replaced by "draw is per frame and cheap; only atlas/image/expensive-subtree misses can stall; use fallbacks per item".
4. Isolation of independent compositing effects -> replaced by render-graph nodes (5.1) created by semantics.
If experiment X3/X4 shows (2) fails on the weakest target, the minimum extension is *cost-promoted subtree caches*, not tiles.

---------------------------------------------------------------------------
## 6. Renderer-to-shell data (what it should look like)

Context: pipeline.md says renderer sends "display lists, layer trees and animation descriptions in a versioned format through shared memory"; Q55 makes fragments relative to their formatting context; Q56 makes intrinsic sizes on demand. The owner wants incrementality to fall out of decoupling. Design nodes:

### D1. Stable item identity
Status: **established need**. Every item and node has an id stable across frames and edits (derive from DOM node id + fragment index within the node, or an arena slot with generation). Without it the shell cannot map a changed item to its old bounds (for damage) or its GPU slot (for patching). Experiment: none; it is a prerequisite. Whitefoot need: ids must be a property of layout output (a persistent arena slot per fragment), not of list position.

### D2. Local coordinates + transform tree
Status: **promising, partly decided (Q55)**. Item geometry relative to its formatting-context/stacking-context node; node transform relative to its parent. Moving a context changes one node. For *in-flow* content, positions can be sent as sizes in flow order and let the shell derive positions as prefix sums ("position = previous sibling end + margin", the relative-offset tree measured in 2.5): the shift of 10^5 later siblings becomes at most ~80 writes. Cost/risk: margin collapsing, floats, and `position: relative` complicate "position = prefix sum"; only the plain block/inline flow needs it; other cases send explicit offsets. **Uncertain**; it is a layout-output-representation question that Q55 as written does not yet answer (Q55 gives offsets relative to the context, which for a 10^5-child flat context is still an O(children) rewrite for a height change near the top). Experiment X2 measured the data side only; the layout side (can layout produce the delta in O(F log n) rather than recomputing absolute offsets) is open.

### D3. Per-chunk bounds
Status: **established**. Each item carries local bounds (plus `spread`, `reads_backdrop`, `opaque` flags); each paint-tree node carries the union. Needed for culling, damage and index. The shell may build and own the index (measured cheap: 3.7 ms build, ~1 us query at 250k chunks), so the renderer sends bounds, not an index.

### D4. Deltas, not full lists
Status: **promising**. Delta = ops {add chunk, replace chunk content, remove chunk, set node transform/clip/effect, set order position, bump epoch}. A *chunk* = the output of the paint function for one memoized subtree (pipeline.md: each stage is a pure memoized function of explicit inputs); the memo key is the chunk id. A chunk is **immutable once published**; a change publishes a new chunk and a delta op replacing the reference. Bytes per delta ∝ changed chunks (typically a handful, 1-10 KB) rather than a list.
Full-list fallback must exist (first frame, resize reflowing everything). Size order [derived]: 250k chunks x ~20 B refs = 5 MB for a full re-send; deltas for a keystroke are ~KB. Experiment: Snowghost paint stage can produce the chunk stream and a harness can count delta bytes for scripted edits (class change, text insert, window resize) on the three pages.

### D4b. Open question handed upstream: whole-page paint or viewport-dependent paint?
Sections D4, D5 and 3.4 assume the renderer paints the whole page and the shell culls to the viewport (that is what makes the full list ~5 MB and shell-side scrolling free of renderer round-trips). The alternative is paint on demand with the viewport as an input dependency (Q56-style): the renderer sends chunks near the viewport and the shell requests more as it scrolls. That changes the data contract (D5 needs a request channel from shell to renderer), the scroll latency path (3.4: scrolling into unpainted area waits for the renderer, i.e. checkerboarding returns in a different form), and the size of the "full list". Not resolved here; it sits between this branch and layout/paint and should be decided with them. X9 measures how big the whole-page chunk set really is, which bears on it.

### D5. Shared memory protocol
Status: **promising, fits Whitefoot's constraints**. Because chunks are immutable after publication, the reader needs no seqlock: renderer appends chunks to a shared arena and publishes delta messages through a single-producer ring plus epoch counter; the shell reads only published regions and **acknowledges an epoch**; the renderer reclaims chunks superseded before the acked epoch. Order/identity: items are placed by *order labels* with gaps (order-maintenance labels or fractional keys) so inserting in the middle of the 10^5 sequence does not renumber. Whitefoot needs: a way to emit a typed, versioned byte layout into a region it exclusively writes (struct-of-arrays, no pointers, offsets), with the "never mutate after publish" property expressed as ownership transfer (the compiler can prove the writer does not touch published chunks, which is exactly a disjoint-writes statement). Experiment: X2-style measurement of delta byte rates; later a real ring.

### D6. Order and stacking
Status: **hard-ish, must be right**. Paint order within a stacking context is tree order plus z-index reordering; the shell scene is a paint tree (so DFS = paint order). Deltas that move an element between stacking contexts (z-index change) are tree moves, which are rarer than content edits; first implementation may resend the affected stacking subtree.

### D7. Text items
Status: **promising**. A text run item = (font id, glyph id array, glyph advances/positions in run-local coords, size, paint ref, flags). Glyph ids and positions are shaping output: stored once per run in the chunk; position updates for a moved paragraph are a node-offset change. Bounds computed by the renderer (it knows the metrics). Per-glyph instances are derived in the shell; the shell may keep a per-run GPU instance slice so a moved paragraph rewrites an offset/transform slot, not 100s of instances.

### D8. GPU-side layout of the scene (shell internal; our proposal for its design)
Status: **promising [speculation]**. Keep instance data in a big GPU buffer with stable slots per chunk (free-list allocator); per-instance a *node id*; a small "node table" buffer holds node transforms/clips/offsets, updated each frame from the transform tree. Then: moving or animating a subtree = update some node-table entries; scrolling = one uniform; reflow shift (D2) = O(F log n) node-table writes; content edit = rewrite the changed chunk's slots. Per-frame, draw calls are indirect/instanced over the culled visible slot ranges (CPU cull from the index, or GPU compute cull for 10^5 chunks, which at ~1 us CPU cost is unnecessary). This is the structure that makes "no layer, no tile" cheap: nothing is baked at a coordinate.

---------------------------------------------------------------------------
## 7. Software rasterization in Whitefoot as a branch (not in pipeline.md; flagged for the owner)

Status: **feasible, uncertain value** [speculation grounded in measurement].
- Whitefoot proves disjoint-write counted loops, so a software damage-rect rasterizer (rows or tiles of the damage region as disjoint outputs, items intersecting the rect in paint order) is expressible as proven-parallel code with no locks and no unsafe. The measured proxy: 12k glyph blits ~2.4 ms single core scalar and a 1080p copy ~0.9 ms; with 4 cores and damage-limited work a text edit would be well under 1 ms. At 4K/240 Hz the memory traffic is the limit (33 MB/frame full; ~8 GB/s at 240 Hz).
- Value: (a) a **correctness oracle** the GPU path must match pixel for pixel (damage redraw == full redraw; scrolled frames == fresh frames); (b) a portable fallback and a headless test target (this container has no GPU); (c) present via shared memory (`wl_shm`, DXGI/DirectComposition upload) keeps the whole renderer in the safe language; cost: upload of the damage rects each frame, no GPU effects acceleration.
- Conflict with decision in pipeline.md ("rasterization and compositing belong on the GPU ... Skia first"): this is not a reversal, it is a test oracle plus fallback; the owner decides if it is more than that.

---------------------------------------------------------------------------
## 8. Experiments (discriminating, with the criterion stated before the result)

Legend: [HERE] runnable in this container; [HW] needs real hardware.

**X1 [HERE] Damage-redraw correctness oracle.** Build a small CPU rasterizer (can be C/Rust, compiler-independent) for rect, glyph-mask and clip items from a synthetic paint tree; random edit sequences (insert/remove/move/resize/transform/opacity/filter-like spread) and scroll steps; for each step compare (a) full redraw, (b) damage-scissored redraw into a persistent target, (c) age-tracked double/triple buffered redraw. Criterion: byte-identical in all cases; each way of cheating the test must fail it once (drop `spread` inflation -> mismatch; omit one overlapping item -> mismatch; wrong buffer age -> mismatch). Settles whether the dependency data (`bounds`, `spread`, `reads_backdrop`, order) is sufficient before any GPU exists.

**X2 [HERE, done for the shell-side data structure] Scene index and reflow shift.** Result in 2.5: queries ~0.3-0.9 us at 250k chunks, shift 0.04 us (relative tree) vs ~200 us / 4.9 MB (absolute). Remaining: replace the synthetic scene by the paint-chunk stream of the real pages once Snowghost has a paint stage; count real chunk numbers; test scenes with deep overlap and transforms. Criterion to adopt the relative-offset flow tree: if real edits (insert a paragraph near the top of ecma262, change the font size of one section) rewrite > ~10^4 absolute coordinates under the per-context-relative scheme (Q55) while the prefix-sum scheme rewrites < 10^3, adopt D2's flow-size representation; otherwise keep Q55 as is.

**X3 [HW] Full viewport redraw vs damage-scissored redraw vs persistent-target copy.** Same scene (the real page paint chunks, instanced atlas glyph quads), GPU timestamp queries and a power measurement (RAPL/powermetrics on desktop/laptop; battery gauge on a phone) at 1080p/1440p/4K, on integrated Intel/AMD, a discrete GPU, Apple Silicon, and one TBDR phone. Scenarios: single-glyph change, one-line change, caret blink, hover on a button, full scroll. Criterion decided in advance: damage-limited rendering is justified for a platform if, at its refresh rate, full redraw exceeds 25% of the frame budget **or** damage-limited saves > 20% power on a sustained 10 s scroll/typing run; for platforms where neither holds, use the simpler full redraw and keep damage only for present.

**X4 [HW] Scroll mechanisms.** (a) redraw viewport with offset, (b) copy-previous-pixels + draw exposed strip (scroll rect), (c) retained big texture with crop, (d) tile-like cached pixels (control). Measure GPU ms, power, and frame-time variance on real pages at 120/240 Hz, with and without a sticky header and with fractional/inertial scrolling. Criterion: (a) is the default unless (b) saves > 30% power at equal visual output on the same hardware; (c) and (d) are only needed if (a) fails the budget on the weakest target.

**X5 [HW] Text path comparison.** Atlas quads vs Slug vs Vello (sparse-strip/hybrid or compute) for: 16 px static page, 16 px scrolling, continuous zoom 100%-400%, rotated text. Metrics: GPU ms, CPU encode ms, cold-cache ms (first visit of a page), visual diff vs Chromium text raster (SSIM or per-pixel). Criterion: atlas stays the default if it beats the others on 16 px static/scroll by > 20% and the others do not need > 2x work to match its crispness; Slug becomes the zoom/transform path if its zoom frames stay within the budget while the atlas path shows re-raster stalls.

**X6 [HERE+HW] Cost-promoted subtree cache.** On a page with a blur-shadow card or SVG, compare always-redraw, always-cache, and the cost rule of 5.1 (EWMA of GPU timestamp cost, hysteresis) across animation and static phases. Criterion: the rule must match the best of the two fixed policies in both phases within 10% frame time; otherwise the rule is too noisy to keep.

**X7 [HW] Present paths.** Wayland (damage_buffer, buffer_age, partial_update) on two compositors, Windows DXGI Present1 dirty rects/scroll rect, and (laptop with PSR2) KMS `FB_DAMAGE_CLIPS` if reachable. Measure compositor GPU time/power (intel_gpu_top, ETW, powermetrics), driver behaviour of buffer age (0? correct?), resize/recreate behaviour. Criterion: partial present is worth the complexity on a platform only if measured compositor/GPU power drops > 10% in a typing and a scroll workload; and age reporting is correct on > 90% of tested drivers (else P2).

**X8 [HW] End-to-end latency.** Input to photon with a high-speed camera or photodiode: shell-only scroll, renderer-involved edit (keystroke), and animation; compare 1-frame vs 2-frame queueing configurations. Criterion: median and 99th percentile at 240 Hz; target is renderer-involved edit <= 2 frames at the median.

**X9 [HERE] Delta size accounting.** Using Snowghost's layout output on the three pages, count how many chunks/bytes change for scripted edits under (a) absolute offsets, (b) Q55 context-relative, (c) flow-size prefix scheme. Complement of X2; needs only layout output, no paint stage (fragments are the chunks' geometry). This is the cheapest experiment that touches the real data and is runnable now with the existing drivers (use `perl .github/run-check.pl`).

---------------------------------------------------------------------------
## 9. Dead ends and traps (so nobody repeats them)

- **A fixed-size tile as the damage unit** (owner's rejection): confirmed by WebRender's own sub-tile dirty rect; the tile is for cached pixels, not for damage.
- **One union damage rect** (Chromium viz): scattered edits blow it up; use a cost-merged list.
- **Per-frame full dependency diff** (WebRender's tile dependency compare): O(items) every frame; unnecessary when the renderer emits deltas.
- **Putting absolute coordinates in items**: a reflow rewrites 10^5 items; ~4.9 MB at an assumed 20 B/chunk (derived; ~2 MB / 0.2 ms is what the benchmark actually wrote/took); use local/relative.
- **Vello as the text engine on 10^5-glyph pages today**: full per-frame pipeline floor, experimental glyph cache [cited].
- **Pathfinder**: archived [memory].
- **Using GPU speed to justify damage tracking before measuring**: C1/section 1 suggests the viewport redraw is cheap; the justification is power/latency, to be measured.
- **Buffer age assumed correct**: some drivers misreport; always have P2 as the fallback [memory, X7 to confirm].

---------------------------------------------------------------------------
## 10. Needs from Whitefoot / the project (summary)
1. Stable fragment/item identity as a first-class layout output (D1).
2. A representation of in-flow positions that makes a height change O(log n) in rewritten data (D2/X9), compatible with Q55.
3. Chunks as immutable memoized paint outputs with explicit `bounds`, `spread`, `reads_backdrop`, `opaque` (D3/D4); the paint-stage memo key excludes absolute position.
4. A way to write a versioned, pointer-free byte layout into an exclusively owned shared region with publish/ack, expressed so the compiler can prove published chunks are not mutated (D5).
5. Optional: software rasterizer in Whitefoot as oracle/fallback (section 7).

---------------------------------------------------------------------------
## 11. Top three recommendations (what to try first, and why)

1. **X9 + X2-real: measure delta size on real layout output, then choose the position representation (D2).** It is runnable now, touches the owner's actual coupling question (what must be rewritten when a paragraph's height changes in a 10^5-child formatting context), and my synthetic measurement says the cost is bytes (derived ~4.9 MB at 20 B/chunk) not CPU time (0.2 ms measured): the representation decides whether a small edit is a small message. Criterion in X2.

2. **X1: the software damage-redraw oracle, with the paint-chunk contract (bounds, spread, reads_backdrop, order) as the only inputs.** It is runnable in this container, it validates the dependency data before any GPU or Skia exists, and the same oracle later becomes the compiler-independent test the GPU shell must match pixel for pixel. A failure here changes the data format, which is the expensive thing to change later.

3. **X3/X4 on one real GPU box before committing to a pixel cache of any kind: instanced atlas-glyph redraw of the retained scene (full vs damage-scissored vs persistent copy), and scroll by redraw vs scroll-copy.** My derivation (C1) says the viewport redraw is cheaper than a cache blit for text pages and that damage matters for power more than frame time; if a measurement on even one integrated GPU at 4K/240 Hz confirms it, the whole "no tiles, no layers" design is justified and the cost-promotion rule (5.1) is only needed for filters/shadows/overdraw. If it fails, the minimal fallback is subtree caches promoted by measured cost, not tiles.

Evidence index (URLs from this session): Vello fork partial redraw https://github.com/mindderivative/tre/pull/17 ; Vello glyph/sparse-strip status https://github.com/linebender/vello/issues/670 , https://linebender.org/blog/tmil-25/ ; WebRender picture cache https://doc.servo.org/webrender/picture/index.html ; EGL damage extensions https://registry.khronos.org/EGL/extensions/KHR/EGL_KHR_swap_buffers_with_damage.txt ; Weston partial update https://cgit.freedesktop.org/wayland/weston/commit/?id=df2095fa35fe84e4ebc30754dd9f25e50bd1aa47 ; Mozilla partial composite https://bugzilla.mozilla.org/show_bug.cgi?id=1484812 ; Chromium viz partial swap https://hackmd.io/@elkurin/r1Ux087ST ; DXGI dirty/scroll rects https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-1-2-presentation-improvements ; Slug public domain https://hackaday.com/2026/03/20/slug-algorithm-for-on-gpu-rendering-of-fonts-with-bezier-curves-now-in-public-domain/ ; GPUI https://zed.dev/blog/videogame ; Skia Graphite https://www.osnews.com/story/142739/introducing-skia-graphite-chromes-rasterization-backend-for-the-future/ .
