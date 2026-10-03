# Why WebRender added picture caching and OS-compositor surfaces, and which of those reasons apply to a damage-scissored retained-scene renderer

Research note for Snowghost `research/investigations/incremental/DESIGN.md` §6–7 and
`notes/raster.md` §2.2, §3, §5. Written 2026-10-02 from web sources fetched in
this session plus the current WebRender sources at `hg.mozilla.org` tip.

Status vocabulary used on every finding:

- **established** — stated in a primary source (Mozilla gfx blog, Bugzilla, the
  WebRender source) and quoted here.
- **measured-by-them** — a number published by the people who measured it.
- **inferred** — my reading of the sources; the sources do not say it in these words.
- **from memory** — not re-verified in this session; treat as a lead.
- **secondary** — only found in a non-primary source.

URL conventions: BZ n = https://bugzilla.mozilla.org/show_bug.cgi?id=n.
"tip" means the file fetched this session from
https://hg.mozilla.org/mozilla-central/raw-file/tip/gfx/wr/webrender/src/.

---------------------------------------------------------------------------
## 0. The one-paragraph answer

WebRender did not abandon "redraw from a retained scene". It still redraws
every dirty tile from primitives every frame, and the content-side still
sends it whole display lists. What it added was (a) a pixel cache (picture
cache tiles) whose main job is to make *scrolling and static content* cost
nothing on the GPU, (b) a dependency diff per frame to find out what changed
because the display list does not tell it, (c) dirty-rect scissoring inside a
tile plus partial present to the OS, and (d) hand-off of tiles and video to
the OS compositor so the window manager stops copying the whole window. The
*documented* reasons are, in order of evidence weight: memory-bandwidth-bound
power on integrated GPUs at high resolution (strongest, with numbers); the
OS compositor re-copying the whole window on every present (strong, with
numbers); pathological pages where redrawing everything each scroll frame
exceeded the GPU (stated, no numbers); CPU-side scene/frame rebuilding per
frame (stated, with CPU numbers for video). Of these, only the first is
inherent to any per-frame GPU redraw, and even it is answered by *not
touching unchanged pixels*, which damage scissoring and partial present do
without tiles. The others came from WebRender's position inside Gecko
(whole display lists, no deltas) and inside an OS (a compositor it cannot
bypass). The owner's design must still supply: a pixel cache for scrolling
on weak/high-DPI targets *if* X3/X4 say redraw costs too much there, an OS
compositor surface for video and (on macOS) for partial update at all, and a
way to keep its CPU work proportional to the change.

---------------------------------------------------------------------------
## 1. Tree of findings

### 1. What the original WebRender design was

1.1 **Paint every pixel every frame, no painting/compositing split.** established.
- Lin Clark, 2017-10: "What if we stopped trying to guess what layers we need?
  What if we removed this boundary between painting and compositing and just
  went back to painting every pixel on every frame?" Layers are described as a
  trade-off with cliffs: too many layers cost memory and transfer, too few
  mean "you've doubled the amount of drawing you have to do, touching each
  pixel twice". https://hacks.mozilla.org/2017/10/the-whole-web-at-maximum-fps-how-webrender-gets-rid-of-jank/
- Nical, 2018-11-02: "WebRender's original strategy for rendering web pages was
  'We re-render everything each frame'... Most other things were initially
  redrawn each frame"; "the cost of changing a single thing is about the same
  as the cost of changing everything."
  https://mozillagfx.wordpress.com/2018/11/02/webrender-picture-caching/
- servo/webrender wiki overview: "Redraw each frame (when there is something to
  be updated - not a constant fps like games!)", "Cache results (such as
  vertex buffers, rasterized glyphs) where possible between frames", "Group
  items into small number of draw calls. Necessary for good performance with
  OpenGL." https://github.com/servo/webrender/wiki

1.2 **Glyphs were always cached; the per-frame work was quads.** established.
- "as you scroll with WebRender today, we re-draw a rectangle for each glyph
  on screen each frame, but the rasterization of the glyphs has always been
  cached in a traditional text rendering fashion." (picture-caching post, above)
- Lin Clark: "We still render the characters (called glyphs) that are used in
  blocks of text on the CPU" (same article as 1.1).

1.3 **Opaque/alpha passes with a depth buffer to kill overdraw.** established.
- "WebRender: Culling": "memory bandwidth is a very common bottleneck, even on
  high end hardware"; z-buffer front-to-back opaque pass, back-to-front alpha
  pass. https://mozillagfx.wordpress.com/2018/11/08/webrender-culling/
- "WebRender: Batching": blended primitives look back over "the last 10 blended
  primitives" for a batch; opaque ones batch freely.
  https://mozillagfx.wordpress.com/2018/11/21/webrender-batching/
- Primitive segmentation moves pixels from the alpha pass into the opaque pass
  ("memory bandwidth savings and better batching").
  https://mozillagfx.wordpress.com/2019/01/03/webrender-primitive-segmentation/

### 2. The problems full redraw caused (Q1)

2.1 **Scrolling pathological pages exceeded the GPU.** established, no numbers.
- "WebRender on the other hand re-draws everything each frame as you scroll,
  and on most GPUs this is too much." (example: a CSS reproduction of an oil
  painting; other browsers paint it once into a layer and move the layer).
  https://mozillagfx.wordpress.com/2018/11/02/webrender-picture-caching/
- Newsletter #31: picture caching "should solve a lot of the remaining issues
  with pages that generate too much GPU work."
  https://mozillagfx.wordpress.com/2018/11/21/webrender-newsletter-31/

2.2 **Power, even when fast enough.** established; measured-by-them for the
numbers.
- Motivation sentence: "even if WebRender is fast enough to render complex
  content every frame at 60fps, there are valuable power optimizations we could
  get from not redrawing some things continuously." (picture-caching post)
- March 2018, newsletter #15: "We are aware that WebRender currently consumes
  more battery than it should and we decided to postpone power saving
  optimizations to after we make our first release to a limited set of user
  (which have desktop computers)."
  https://mozillagfx.wordpress.com/2018/03/05/webrender-newsletter-15/
- The first release qualification literally excluded machines with a battery:
  BZ 1475355 ("we could probably use GetSystemPowerStatus() to just ensure that
  there's no battery"); BZ 1490942 "WebRender not qualified for desktops with
  UPS ('Has battery')".
- The model they settled on, April 2019, newsletter #43: "energy consumption in
  WebRender (as well as Firefox's painting and compositing architecture) is
  strongly correlated with the amount of pixels that are manipulated. In other
  word, it is dominated by memory bandwidth which is stressed by high screen
  resolutions... it gives us a very simple metric to measure and build
  optimizations and heuristics around." Remedies named there: document
  splitting and OS compositor integration ("No need to tell the window manager
  to redraw the whole window when only the upper part changed").
  https://mozillagfx.wordpress.com/2019/04/10/webrender-newsletter-43/
- Mac meta BZ 1422090 (non-WebRender Firefox 59 but the same full-window
  compositor): scrolling mozilla.org at 1440x900, Firefox 14 W GPU vs Chrome
  ~3 W; scaled retina 1024x640 → 3 W, 1680x1050 → 20 W; and "Turning WebRender
  ON roughly doubles GPU power consumption." measured-by-them.
- Mac BZ 1452489 (WebRender, 2018): scrolling near the top of arstechnica.com
  16–20 W GPU vs ~3 W elsewhere, GPU time 12 ms vs 3.8 ms; cause (Glenn
  Watson): images with `mix-blend-mode: multiply` "we don't cache them between
  frames... Each image gets drawn to an off-screen target... The expensive
  mix-blend-mode shader is run". measured-by-them. This is the clearest case
  of "redraw of an *expensive effect* each frame" rather than of plain content.

2.3 **The OS compositor re-copying the whole window every present.** established,
measured-by-them (macOS, non-WebRender compositor, Firefox 70).
- pcwalton, servo/webrender#3115 (2018-09): "every frame, we render the entire
  window, present it, and then the OS compositor blits the entire window again.
  This primarily causes needless energy usage." Proposed: bindings to
  DirectComposition / CoreAnimation / Wayland / SurfaceFlinger, tile the scene
  into non-overlapping OS layers, give scroll roots their own tiles, "only
  create layers for real scroll roots with rectilinear transforms" to avoid
  Gecko's FrameLayerBuilder prediction pitfalls.
  https://github.com/servo/webrender/issues/3115
- Markus Stange, Firefox 70 on macOS: scrolling 16.4 W → 9.4 W, spinning
  square 12.8 → 2.9 W, YouTube 28.4 → 16.4 W, Google Docs idle 7.4 → 1.6 W,
  loading animation high 19.4 → 1.8 W. Mechanism: "we were always redrawing
  the whole window on every change, and the window manager was always copying
  our entire window to the screen on every change", because `flushBuffer`
  "gives you no way to indicate which parts of the OpenGL context have
  changed"; "This is a limitation which does not exist on Windows". Fix: own
  swap chain of IOSurfaces, partial redraw ("This change on its own is
  responsible for most of the power savings"), window tiled into square
  CALayers, opaque vs transparent layers. Cost model: "A screen worth of pixels
  takes up around 28MB at the default scaled retina resolution (1680×1050@2x)...
  each screenful of one layer of compositing takes up 3 * 28MB of memory
  bandwidth. My machine has a memory bandwidth of ~28GB/s, so each screenful of
  compositing takes about 3 milliseconds. We believe that the GPU runs at full
  frequency while it waits for memory." And on WebRender: "Wasn't the point of
  WebRender to redraw the entire window every frame?... WebRender is now adding
  support for native layers and caching, so that unnecessary redraws can be
  avoided. WebRender still aims to be able to redraw the entire window at full
  frame rate, but it now takes advantage of caching in order to reduce power
  usage." "This will allow us to ship WebRender on macOS without a power
  regression."
  https://mozillagfx.wordpress.com/2019/10/22/dramatically-reduced-power-usage-in-firefox-70-on-macos-with-core-animation/

2.4 **Video: drawn into the cache, then to the screen, then composited by the
OS.** established, measured-by-them.
- BZ 1579235 "YouTube is drawn into the picture cache and then onto the
  screen": "During video playback we end wastefully drawing into the picture
  cache and then drawing to the screen. This wastes our precious bandwidth."
  Fix: compositor surfaces for YUV primitives; "allows video playback to be
  composited directly into the framebuffer, without invalidation of content
  tiles, which can save a significant amount of battery power".
- BZ 1569767 (Intel): WebRender 52% vs 15% GPU on one laptop, 70–75% vs 25–30%
  on UHD 620; after DirectComposition + compositor surfaces: Surface Go 10%
  GPU / 1.8–2 W with WR vs 30% / 3.3 W without; "The bulk of the problem has
  been fixed by DC and bug 1579235."
- Newsletter #52: "On an Intel HD 530 1080p60 video playback has 65% usage with
  WebRender on in 75, 40% with Webrender off, and 32% usage with WebRender on
  in 76." https://mozillagfx.wordpress.com/2020/04/30/moz-gfx-newsletter-52/
- 2026, Firefox 149 "layer compositor" on Windows (BZ 2000149): fullscreen video
  "around 10% power savings" by power meter on Intel and AMD; WebGL/WebGPU as
  RGB overlay "improved Talos' glterrain score about 12%". measured-by-them.

2.5 **CPU-side: scene and frame rebuilt per frame.** established, measured-by-them
for video.
- Newsletter #10 (2017-11): "Glenn removed the need to re-build scenes every
  frame during scrolling (this is a big CPU win)."
  https://mozillagfx.wordpress.com/2017/11/27/webrender-newsletter-10/
- Newsletter #12 (2018-01): "Glenn removed the need to re-build the scene when a
  dynamic property changes. This saves a lot of CPU time during scrolling and
  animations." https://mozillagfx.wordpress.com/2018/01/16/webrender-newsletter-12/
- BZ 1474583 (YouTube, Windows): CPU ~14% avg without WR vs ~30% with; cause:
  "The DL is not changing, just the contents of an external texture. Thus, we
  should be able to detect this case and redraw the same built Frame as the
  previous frame"; the transaction "unconditionally triggers a frame build";
  fix: "we skip frame building altogether when the only thing that change is a
  video frame that is already on the GPU." BZ 1430451 reports 100% vs 40–45%
  total CPU for the same scenario. BZ 1420430: scene rebuilds came from
  `SetDisplayList` messages (Gecko resending display lists) and
  `UpdateDynamicProperties`.
- Newsletter #46: display list build time (Gecko side) "mean... has gone down
  by 40%, from ~1.8ms to ~1.1ms". https://mozillagfx.wordpress.com/2019/07/05/moz-gfx-newsletter-46/
- BZ 1642629 (2020): frame building allocations; "On a 4k screen for most sites
  the element counts are low enough that we can get away with preallocation...
  but high enough that reallocation happens a few times per frame".
- inferred: the per-frame dependency diff that picture caching requires (3.3
  below) is itself CPU work proportional to the visible primitive count every
  frame, because Gecko never sends deltas.

2.6 **Fill rate on integrated GPUs and HiDPI.** measured-by-them (the team's
own baseline table).
- servo/webrender wiki "GPU fill rate baseline": one full-screen pass with a
  trivial shader costs 0.05 ms on a GTX 1070 at 1920x1080, 0.07 ms on an RX
  480, 1.60 ms on Intel Ivybridge mobile (Linux) at 1920x1080, 1.96 ms on
  Haswell at 3200x1800. https://github.com/servo/webrender/wiki/GPU-fill-rate-baseline
- inferred: a 16.7 ms budget allows ~10 such passes on that Ivybridge at 1080p
  (16.7/1.60) and ~8 on the Haswell at 3200x1800 (16.7/1.96); a page with a
  background, text, a few alpha layers and one blurred or blended surface is
  already most of that, and at 120 Hz (8.3 ms: ~5 and ~4 passes) it is over. This is the
  numeric form of "on most GPUs this is too much".

2.7 **Text subpixel AA pushed tile-cache structure.** established.
- Subpixel AA needs an opaque backdrop. `tile_cache/mod.rs` (tip): "The picture
  space rectangle that is known to be opaque. This is used to determine where
  subpixel AA can be used, and where alpha blending can be disabled";
  "only the primary sub-slice may be opaque and support subpixel AA".
- BZ 1635610: to keep subpixel AA "we avoid creating a separate picture cache
  slice for different scroll roots, so that we can guarantee the subpixel AA
  rendering will all occur in the same slice", at the cost of "more tile
  invalidations and rasterizations"; fixing it (per-scroll-root slices by
  default + better opaque-backdrop detection) took YouTube scrolling from 35
  draw calls / 4.6 ms renderer thread to ~10 / ~2 ms. measured-by-them.

2.8 **Tiles bring their own failure modes.** established.
- BZ 1559284: a fast path that updated a native texture without running frame
  building left "stale tiles" (choppy YouTube unless the mouse moved).
- BZ 1602803 (Surface Go, Hacker News): with the OS compositor, GPU 50% vs
  25%; Iris 550 20 W vs 15.5 W package; part of the GPU work "moved from the
  Firefox process to the DWM"; scrolling caused "clip_chain.pic_clip_rect
  changes" invalidating tiles needlessly; closed after remeasurement showed
  "better or the same". measured-by-them. Lesson: a tile cache is only as good
  as its invalidation keys; a clip rect that moves with scroll invalidates
  everything.
- BZ 1694707: "Constant picture cache invalidation when scrolling" a GDPR
  overlay page (title only; not read in detail).
- BZ 1556163 (draw.io): "Picture caching isn't helping scrolling at all"; the
  cost was blob (SVG) rasterization and display-list building on the content
  thread, fixed by splitting blobs, not by the cache.
- Native surfaces have an allocation cost; `tile_cache/mod.rs`: "There is an
  assumption that creating a native surface is cheap, and only when a tile is
  added to a surface is there a significant cost. This assumption holds true
  for the current native compositor implementations on Windows and Mac."

### 3. What picture caching, compositor surfaces and partial present are (Q2)

All from the WebRender sources at tip unless noted; the module doc of
`picture.rs` is quoted, and the constants are read from `tile_cache/mod.rs`.

3.1 **Slices.** established.
- "the scene is cut into a small number of slices, typically: content slice,
  UI slice, background UI slice". "Each time a new scroll root is encountered,
  a new picture cache slice will be created." The doc says more than 8 slices
  squashes to one; the code says `MAX_CACHE_SLICES: usize = 16` (`slice_builder.rs`,
  with the comment "it's assumed the GPU memory + compositing overhead would be
  too high"). Also "WR will first look for an iframe item in the root stacking
  context to apply picture caching to."
- Scroll bars get their own slices (`SliceFlags::IS_SCROLLBAR`).

3.2 **Tiles.** established.
- `TILE_SIZE_DEFAULT` = 1024x512 device pixels (`tile_cache/mod.rs`; the module
  doc in `picture.rs` still says "2048x512 (or 128x128 for the UI slice)", which
  is stale). Gecko overrides through `gfx.webrender.picture-tile-width`
  (512 on Windows, 1024 elsewhere) and `gfx.webrender.picture-tile-height`
  (512) (`modules/libpref/init/StaticPrefList.yaml` at tip); the renderer
  clamps to 128..4096 (`renderer/init.rs`). Scrollbar slices use 1024x32 /
  32x1024. Tile size is re-evaluated only every 120 frames "so that we don't
  end up constantly invalidating and reallocating tiles if the picture rect
  size is changing near a threshold value."
- A tile is either a texture ("cached rasterized content") or a "clear tile"
  that "contain[s] only a solid color rectangle rendered directly during the
  composite pass" (so solid-colour areas cost no texture).
- Tiles are tracked in an opaque surface and an alpha surface per slice; a
  tile moves between them when its opacity changes.

3.3 **Invalidation.** established.
- "Each tile keeps track of the elements that affect it, which can be:
  primitives, clips, image keys, opacity bindings, transforms. These dependency
  lists are built each frame and compared to the previous frame to see if the
  tile changed." The comparison uses interned primitive keys
  (`compare_cache: FastHashMap<PrimitiveComparisonKey, PrimitiveCompareResult>`,
  `invalidation/compare.rs`).
- Why interning exists: newsletter #33, "In order for picture caching to work
  across displaylists we must be able to detect what did not change after a
  new displaylist arrives. The interning mechanism introduced by Glenn in #3075
  gives us this ability in addition to other goodies such as de-duplication of
  interned resources and less CPU-GPU data transfer."
  https://mozillagfx.wordpress.com/2018/12/13/webrender-newsletter-33/
- "The tile's primitive dependency information is organized in a quadtree...
  The union of the invalidated leaves of each quadtree produces a per-tile
  dirty rect which defines the scissor rect used when replaying the tile's
  drawing commands and can be used for partial present." The `Tile` struct
  carries one `dirty_rect` and notes "We have multiple dirty rects available
  due to the quadtree above. In future, expose these as multiple dirty rects".
- Known over-invalidation sources recorded in the code: clips in local space
  (newsletter #33), clip-rect changes under scroll (BZ 1602803), new slice
  inserted (`slice_index` comment: "we invalidate tiles if a new layer gets
  inserted / removed between display lists"), surface opacity change
  invalidates the whole surface, raster-scale change invalidates all tiles.

3.4 **What is cached and what is not.** established.
- Cached: the rasterized pixels of each tile of each slice (content, UI,
  scrollbars), in the texture cache or in OS-compositor surfaces.
- Not cached by the picture cache: glyph rasterization (separate glyph cache),
  render tasks for effects (blur, mix-blend, clip masks — bug 1452489 shows
  the cost when these are not cached), and compositor surfaces (video,
  WebGL), which are updated every frame outside the tiles.
- Picture caching did not make the renderer incremental: the content side
  still sends a full display list on every change, and each frame rebuilds
  dependency lists for every visible primitive of every slice. The cache
  reduces GPU rasterization, not CPU scene work.

3.5 **Compositor surfaces.** established.
- `picture.rs` doc: "Sometimes, a primitive would prefer to exist as a native
  compositor surface. This allows a large and/or regularly changing primitive
  (such as a video, or webgl canvas) to be updated each frame without
  invalidating the content of tiles, and can provide a significant performance
  win and battery saving." Overlapping content makes the tile an "overlay
  tile" drawn in alpha mode above the surface; only opaque primitives are
  promoted; at most `MAX_COMPOSITOR_SURFACES = 4` per cache, and a YUV
  primitive must stay at the same rect for `YUV_SURFACE_STABLE_FRAMES = 15`
  frames before promotion.
- The `Compositor` trait (`composite.rs`): `create_surface(id, tile_size,
  is_opaque)`, `create_external_surface`, `create_tile`, `bind(tile, dirty_rect,
  valid_rect)`, `add_surface(transform, clip, rounded clip)` every frame,
  `start_compositing(clear_color, dirty_rects, opaque_rects)`. Doc: "picture
  cache slices will be composited by the OS compositor, rather than drawn via
  WR batches"; `CompositorConfig::Native` "can be significantly more power
  efficient on operating systems that support it." Gecko enables it on
  Windows, macOS and GTK (`gfx.webrender.compositor`).
- 2025–2026: a third mode, `CompositorConfig::Layer` with a `LayerCompositor`
  trait ("swapchain based compositing": `bind_layer(index, dirty_rects)`,
  `present_layer`, `add_surface`), enabled on Windows and GTK
  (`gfx.webrender.layer-compositor`), shipped in Firefox 149 (BZ 2000149, meta
  BZ 1959009). Its stated wins are video power and WebGL/WebGPU overlays, i.e.
  the *external surface* path, not the tile path.

3.6 **Partial present.** established.
- `CompositorConfig::Draw { max_partial_present_rects,
  draw_previous_partial_present_regions, partial_present }`: "If this is
  non-zero, then the operating system supports a form of 'partial present'
  where only dirty regions of the framebuffer need to be updated";
  `draw_previous_partial_present_regions` "is used for EGL which requires the
  front buffer to always be fully consistent"; `PartialPresentCompositor::
  set_buffer_damage_region(rects)` provides "the frame's dirty region and some
  previous frames' dirty regions, if applicable (calculated using the buffer
  age)".
- Gecko: `gfx.webrender.max-partial-present-rects` = 1 on Windows, Android and
  GTK, 0 elsewhere; `gfx.webrender.allow-partial-present-buffer-age` = true.
  So the Draw path presents **one** damage rect; the OS-compositor paths use
  per-tile dirty rects (`gfx.webrender.compositor.max_update_rects` = 1 per
  tile bind).
- Android: BZ 1575765 (Firefox 83) "KHR_partial_update allows us to avoid
  rerendering the entire backbuffer every frame, and instead only render what
  has changed on the current frame, as well as the difference between the
  current backbuffer and the current frontbuffer". A search summary (not the
  fetched bug page) adds that Mali and Adreno devices reported buffer ages of 3
  and that BZ 1656533 was needed for the feature to help — search-summary-only,
  unverified.
- Wayland: BZ 1617498 meta; Robert Mader measured ~30% lower GPU utilization
  during scrolling on Skylake with RC6 +10% but "power consumption remained
  neutral initially"; results depended on the compositor (KDE better, Mutter
  blending penalties). measured-by-them.

3.7 **Rollout order, as evidence of which hardware was the problem.** established.
- FF67 (2019-05): "Windows 10 desktops with NVIDIA graphics cards" — "the
  platform where we currently have the best performance", ~4% of desktop users
  (https://mozillagfx.wordpress.com/2019/05/21/graphics-team-ships-webrender-mvp/,
  https://www.firefox.com/en-US/firefox/67.0/releasenotes/).
- FF68: Windows 10 AMD. FF73: "laptops with Nvidia graphics cards with drivers
  newer than 432.00, and screen sizes smaller than 1920x1200" (Wikipedia
  version history). FF75: "Direct Composition is being integrated for our
  users on Windows to help improve performance and enable our ongoing work to
  ship WebRender on Windows 10 laptops with Intel graphics cards"
  (https://www.firefox.com/en-US/firefox/75.0/releasenotes/). BZ 1630629
  (FF76/77): "DirectComposition gives performance and battery life improvements
  so we want to limit the risk... by only shipping to user with it";
  "DirectComposition is important for battery usage on Intel." FF83/84: macOS,
  Intel Gen 6, Linux GNOME X11 (https://www.firefox.com/en-US/firefox/84.0/releasenotes/).
  FF92: everyone, with SWGL software fallback; FF93 pref removed
  (https://wiki.mozilla.org/Platform/GFX/WebRender_Where). Reading: batteries,
  integrated GPUs and large/HiDPI screens were the last to qualify, and
  qualified only once the OS compositor path existed.

### 4. Inherent vs WebRender-specific (Q3)

The discriminating test: would the problem exist in a renderer that (a)
receives deltas with stable ids instead of whole display lists, and (b)
redraws only the damage region from a retained GPU scene?

Rows are inferred verdicts over the cited evidence in §2–3; the "Evidence"
column points at the established/measured findings they rest on.

| # | Problem | Evidence | Inherent to any retained-scene GPU redraw? | Verdict |
|---|---|---|---|---|
| I1 | Memory-bandwidth-bound power at high resolution: every touched pixel costs ~3 reads/writes; integrated GPUs share DRAM with the CPU | 2.2, 2.3 (28 MB/screen, 3 ms/screenful at 28 GB/s; 3 W → 20 W with scaled resolution) | **Yes** for pixels you touch. **No** for pixels you do not touch. | Applies to us. It argues for *damage-limited* pixel traffic, not for tiles. Tiles are one way to not touch pixels; a scissor is another. |
| I2 | Per-frame redraw of *expensive effects* (blur, mix-blend, filters, large paths) is too slow and hot | 2.2 (BZ 1452489: 12 ms vs 3.8 ms; 16–20 W vs 3 W) | **Yes** whenever the effect's input is unchanged and it is redrawn | Applies. Needs a pixel cache for *effect outputs*, promoted by cost — exactly `raster.md` §5.1. WebRender's answer (cache the render task) is the same mechanism at a different grain. |
| I3 | Scrolling a heavy page redraws everything every frame | 2.1 (no numbers), 2.6 (fill-rate table) | **Partly.** Scroll damage is the whole viewport, so damage scissoring does nothing; what remains is the per-frame cost of drawing the viewport's instances. Inherent on GPUs where that cost exceeds a frame or the power budget; not inherent on GPUs where it is sub-millisecond. | Open for us; X3/X4 decide. The data point is "most GPUs" in 2018 for a pathological page. For text/rect pages, raster.md's C1 claims the viewport redraw is cheap; that is unmeasured. The fallback if it fails is scroll-by-copy (P3) or cost-promoted subtree caches, not a fixed tile grid. |
| I4 | The OS compositor copies the whole window every present unless told otherwise; on macOS there was no API to tell it | 2.3 (all the Firefox 70 numbers) | **Yes** on every OS with a compositor. Not a renderer design question at all. | Applies regardless of our scene design. Needs: partial present with damage rects where the API exists (DXGI dirty rects, EGL damage, Wayland damage), and on macOS *multiple CALayers* (the only partial-update mechanism Apple exposes: "there are no APIs for partial updates of CAMetalLayers either, so you'd need to implement a solution with smaller layers"). |
| I5 | Video / WebGL: content already in a GPU texture is drawn into a cache, then into the frame, then copied by the OS | 2.4 | **Yes** for any design that composites video through its own frame | Applies. OS compositor surface (overlay/underlay) for video and canvases only — the one place WebRender and the owner's design already agree. |
| W1 | Gecko sends whole display lists per change; WebRender rebuilds scene/frame and must *diff* to find what changed | 2.5, 3.3 (interning exists to detect "what did not change after a new displaylist arrives") | **No.** A delta protocol with stable ids makes the diff unnecessary. | WebRender-specific. The owner's D1/D4 remove it. Caveat: the shell's per-frame work must then be O(changed + visible), which is a design obligation, not a free consequence. |
| W2 | Frame building each frame rebuilds batches, render-task graph, clip masks over all visible primitives | 2.5 (BZ 1474583, 1642629), 1.3 | **No**, but every GPU renderer must keep *some* per-frame CPU work proportional to the visible set unless the GPU-side scene is persistent (indirect/instanced draws from stable slots, D8). | WebRender-specific in degree. The owner's D8 (stable GPU slots, node table, culled instanced draws) is the answer; its cost must be measured at 10^5 chunks. |
| W3 | Picture caching's own dependency diff and tile bookkeeping is CPU work every frame | 3.3; BZ 1602803, 1694707 (over-invalidation) | **No.** It exists because of W1. | Not needed with deltas. Keep the *idea* of a per-item dependency list (what reads the backdrop, what spreads) as explicit fields (raster.md §2.5 condition 2). |
| W4 | Subpixel AA requires an opaque backdrop, which shaped slice/tile policy | 2.7 | **Yes** for LCD subpixel text; **no** for grayscale AA. | Applies if we want subpixel AA: an item needs to know whether its backdrop is opaque (a property-tree/backdrop query), which is independent of tiles. Chromium on most platforms and macOS since 10.14 have dropped subpixel AA (from memory, not verified this session); a design choice for us. |
| W5 | Tile grain over-invalidates (one changed pixel redraws a 1024x512 tile unless the dirty rect is sub-tile) | 3.3 | **No.** WebRender itself scissors to the sub-tile dirty rect. | Not inherent; the tile is the *cache* grain, not the *redraw* grain, even in WebRender. |
| W6 | OpenGL draw-call cost drove heavy batching; OpenGL drivers drove blocklists | 1.1 (wiki: "Necessary for good performance with OpenGL"), rollout 3.7 | **No** on Metal/Vulkan/D3D12 with instancing and indirect draws; driver variance remains. | WebRender-specific in degree. Our shell can design for bindless/instanced draws from the start. |
| W7 | Glyphs rasterized on the CPU and uploaded to an atlas; quads redrawn per frame | 1.2 | **No** per se; both WebRender and Zed show atlas quads redraw at 120 Hz. | Same as the owner's plan; the cost is fill (raster.md §1), not an inherent problem. |

What survives the test, i.e. what the owner's design must still provide
(Q4), is I1, I2, I4, I5 and conditionally I3 and W4.

### 5. What a damage-scissored retained-scene design must do (Q4)

5.1 **Make the damage region the unit of pixel traffic on every path.** inferred
from I1 and I4.
- Redraw: scissor to the damage rects and load (not clear) the previous
  contents; on tile-based GPUs the hardware tile is the floor (raster.md P7).
- Present: hand the same rects to the OS. Windows: DXGI `Present1` dirty rects
  or a DirectComposition/`IDCompositionTexture` layer; EGL: buffer age +
  `KHR_partial_update` / swap-with-damage, remembering Android buffer ages of 3
  (3.6); Wayland: `damage_buffer`; macOS: no partial update of a single
  `CAMetalLayer` as of Mozilla's 2019 statement ("there are no APIs for partial
  updates of CAMetalLayers either, so you'd need to implement a solution with
  smaller layers", Markus Stange, 2019-10, URL in 2.3) — the only route Apple
  gives is several layers with their own IOSurface swap chains, which is why
  both Firefox 70's compositor and WebRender's native path tile the window into
  CALayers. On macOS this is a presentation-side tiling the owner cannot avoid;
  it does not have to be the renderer's cache or invalidation unit. **This
  resolves `notes/raster.md` §3.1's open item** ("Metal / CoreAnimation:
  CAMetalLayer has no public dirty-rect present as far as I know [memory, low
  confidence, not searched; verify before relying on it]"): confirmed by a
  primary source for 2019; whether Apple added one since 2019 was not checked.
- A present with no damage must not present at all (Zed issue 32588: 1–1.3 ms
  GPU per frame at 120 Hz for an unchanged empty window, 2.2–2.7 ms with code;
  https://github.com/zed-industries/zed/issues/32588).

5.2 **Keep CPU work proportional to the change.** inferred from W1–W3.
- The delta protocol removes WebRender's display-list diff. What remains per
  frame: property-tree evaluation for animated nodes, damage computation over
  changed chunks, culling of the visible set, and command generation for the
  damaged region. D8's stable GPU slots plus indirect draws are what make the
  last two O(visible) rather than O(scene); the measured 1 µs index query is
  the easy part, the instance/command path is the part to measure.
- A video frame or canvas update must not trigger scene or command rebuild at
  all (BZ 1474583's fix, generalised): external surfaces update by handle.

5.3 **Cache pixels where cost says so, at the grain of the thing that is
expensive.** inferred from I2 and I3.
- Effects with unchanged inputs (blur, backdrop, mix-blend, filters, large
  paths, shadows) are the measured hot spots (BZ 1452489). Cache their output
  as a render-graph node with a content key; this is WebRender's render-task
  cache in a different coat and the owner's §5.1 rule.
- Scrolling is the open case. If X3/X4 show viewport redraw within budget on
  the weakest target, no scroll cache is needed; if not, the first fallback is
  scroll-by-copy of the previous frame's overlap (DXGI scroll rect / blit),
  which needs no invalidation machinery, then cost-promoted subtree caches.
  WebRender's slice-per-scroll-root is the heavy version of the same idea; its
  costs (16-slice cap, GPU memory, sub-slice interleaving for video) are the
  reasons not to start there.

5.4 **Use OS compositor surfaces only for pixels that already exist as a
buffer.** established via I5 and WebRender's own limits.
- Video and WebGL/WebGPU canvases as overlay/underlay surfaces; WebRender's
  numbers (BZ 1569767, BZ 2000149) are the expected win: 1/3 to 1/2 of GPU
  time and ~10–20% of system power on video.
- Do not use OS surfaces for page scrolling: it needs the pixels in a buffer,
  so it degenerates into tiling (raster.md P5), which is exactly the WebRender
  native path with its 4-surface and 16-slice caps and its "clip rect moved
  with scroll" invalidation bugs.

5.5 **Say what each item reads and spreads.** inferred from 3.3 and raster.md
§2.5.
- Keep WebRender's dependency *categories* (primitives, clips, image keys,
  opacity and colour bindings, transforms) as declared fields on chunks and
  property nodes, so damage can be computed from the delta without a diff:
  `old ∪ new` bounds, inflated by `spread`, plus the full bounds of anything
  that `reads_backdrop`.

5.6 **Decide subpixel AA explicitly.** established via W4.
- Subpixel text requires knowing the backdrop is opaque at draw time; that is
  a per-item query against the property tree and the opaque-region summary,
  which the shell can answer without tiles. If grayscale AA is acceptable
  (Chromium on most platforms; macOS since 10.14 — both from memory, not
  verified this session), the question disappears.

### 6. Other systems that redraw from vectors each frame (Q5)

6.1 **Zed GPUI.** established / measured-by-them.
- Design: "Zed is rendered like a videogame"; elements push primitives into a
  `Scene` of "shadows, rectangles, glyphs, icons, and image elements organized
  in layers"; "the performance of composing text using the glyph atlas
  approximates the bandwidth of the GPU". https://zed.dev/blog/videogame
- 120 Hz: frame times "consistently... under 4ms"; "we now render repeated
  frames for 1 second after the last input event". https://zed.dev/blog/120fps
- Costs reported by users: overdraw "5-6 times" per pixel measured in RenderDoc,
  "burning GPU power... draining the battery", with WebRender's opaque
  front-to-back pass cited as the fix (https://github.com/zed-industries/zed/issues/8043);
  unchanged-window presents cost 1–1.3 ms GPU/frame at 120 Hz on an empty
  buffer, 2.2–2.7 ms with code (issue 32588 above); 2026 PRs add journaling of
  skipped frames (https://github.com/zed-industries/zed/pull/64958). A
  community fork ("gpui-fast") retains layout between frames
  (https://github.com/longbridge/gpui-fast) — secondary.
- Reading: existence proof that an atlas-quad scene redraws at 120 Hz on
  Apple GPUs; the recorded pain is power from overdraw and from presenting
  unchanged frames, not from the redraw of changed ones. No damage region.

6.2 **Vello / Linebender (2025–2026).** established.
- Three renderers: Vello CPU, Vello GPU (sparse strips: "preprocesses paths on
  the CPU and uses the GPU for rasterization and compositing"), and the
  compute-centric renderer now "experimental". https://github.com/linebender/vello
  The 2025 blog posts call the sparse-strips GPU renderer "Vello Hybrid" and
  the 2026 README calls it "Vello GPU"; I infer a rename, not verified.
- Sparse strips were motivated partly by caching: "Exploring the performance
  benefits of glyph caching is a major motivation for moving to sparse strips"
  (https://github.com/linebender/vello/issues/670); 2025-08 "support for
  caching sparse strips" in Vello Hybrid (https://linebender.org/blog/tmil-20/);
  2026-Q1 "First cut at glyph caching – more work is needed", Vello Hybrid
  "roughly beta quality" (https://linebender.org/blog/tmil-25/). On an M1 Pro
  Vello CPU "takes second place in many of the benchmarks, often beating...
  Skia and Cairo" in a Blend2D-harness comparison (https://linebender.org/blog/tmil-19/).
- Damage: a `RenderRegion::Rects` mode for `vello_gpu` is an **open** PR as of
  2026-09: draws the scene under a scissor per rect, "pixels inside the region
  match an unconfined render exactly", drops root strips outside the region on
  the CPU; "The WebGL renderer is unchanged; it always redraws its whole
  drawing buffer"; "vello_cpu has no equivalent yet"
  (https://github.com/linebender/vello/pull/1737). Masonry/Xilem: "Damage
  regions aren't currently implemented"; they plan "a single damage region"
  per frame from widget paint rects, and note "As of August 2025, Winit doesn't
  support damage regions" (https://github.com/linebender/xilem/issues/789).
  A third-party fork claims partial redraw "3.7-4.9x less per frame than
  full" (https://github.com/mindderivative/tre/pull/17) — secondary, unverified.
- No power measurements published by Linebender were found.

6.3 **Flutter (Skia and Impeller).** established / measured-by-them.
- Motivation: "Flutter redraws every pixel even if there's a very tiny part of
  the screen that's animating (e.g., CircularProgressIndicator, caret in
  TextField)" (https://github.com/flutter/flutter/issues/33939).
- Skia-era partial repaint, iOS/Metal (2021): damage from layer-tree diffing,
  "Accumulated damage for each framebuffer; Key is address of underlying
  MTLTexture for each drawable", filter bounds inflated
  (https://github.com/flutter-team-archive/engine/pull/28801). Android/OpenGL
  was enabled then restricted: "We currently disable it on Android API levels
  < 29. We have continued to bump up this level and its entirely arbitrary...
  If we cannot rely on this being well supported and cannot detect when it
  isn't, we should consider backing out the feature entirely"
  (https://github.com/flutter/flutter/issues/123353).
- Impeller (2023): the MSAA resolve "will unconditionally clear that texture",
  so partial repaint renders to a separate texture and blits; "The blit seems
  to take about 500ns for a full screen on an iPhone 13"; above a 70% dirty
  fraction "we just render as normal"; empty damage short-circuits to an
  immediate present (https://github.com/flutter-team-archive/engine/pull/40959).
  2025 follow-up moves to a full-size offscreen with a transients cache
  (https://github.com/flutter/flutter/pull/161626). No power numbers published.
- Reading: the damage path is worth keeping even where a full-screen copy is
  cheap, because the win is in *not drawing*; its risk is driver/age
  correctness on Android, which Firefox also hit (buffer age 3, flicker).

6.4 **Skia Graphite (Chrome).** established / measured-by-them.
- Shipped on Apple Silicon Chrome 2025-07; "Ganesh always had a GL-centric
  design with too many specialized code paths"; Graphite "is multithreaded by
  default", targets Metal/Vulkan/D3D12, "increased our Motionmark 1.3 scores by
  almost 15% on a Macbook Pro M3". Chrome still rasterizes into tiles; a stated
  future is re-issuing "Graphite recordings... with certain dynamic changes
  such as translation" to avoid tile allocation for simple content.
  https://blog.google/chromium/introducing-skia-graphite-chromes/
- Chromium viz partial swap uses a single union damage rect ("the minimum one
  rectangle that covers whole damaged area instead of holding the list of
  rectangles") (https://hackmd.io/@elkurin/r1Ux087ST). No power numbers found
  in accessible sources this session.

6.5 **Rive.** established for the landing page; secondary for the per-frame
text claim.
- "You can fill the screen with animated text that looks perfectly sharp, all
  without making a dent in framerate"; triangle-patch reduction of antialiased
  paths on the 3D raster pipeline (https://rive.app/renderer,
  https://rive.app/blog/rive-renderer-now-open-source-and-available-on-all-platforms).
  The claim that "every glyph [is] redrawn from raw bezier curves... every
  frame" was found only in a secondary source
  (https://alphapixeldev.com/sdf-vs-msdf-vs-slug-vs-rive-gpu-text-rendering/).
  No damage model; no power numbers.

6.6 **Cross-system reading.** inferred.
- Every system that started as "redraw the whole frame" and then met laptops
  added the same two things in the same order: skip presenting unchanged
  frames, then confine redraw to damage (Firefox 70 compositor, WebRender,
  Flutter, Zed's 2026 frame journaling, Vello's open PR). None of them went
  back to hand-placed layers as the *invalidation* unit; WebRender's tiles are
  a cache and a presentation unit whose redraw grain is the dirty rect.
- The published power wins come from not touching pixels (Firefox 70:
  3x; WebRender video surfaces: 1/3–1/2 of GPU time), and the published
  failures come from invalidation keys that move with scroll (BZ 1602803) and
  from presentation-side age bugs (Android, Flutter). A delta-driven design
  avoids the first class by construction and inherits the second.

---------------------------------------------------------------------------
## 7. Direct answers

**Q1.** Published causes and numbers: GPU power dominated by memory
bandwidth at high resolution on integrated GPUs (3 W → 20 W by scaling the
retina resolution; 28 MB per screenful, ~3 ms per full-screen composite at
28 GB/s; WebRender "roughly doubles" GPU power on a 2013 Iris Mac); the OS
compositor re-copying the window (Firefox 70's 3x power wins came from
fixing this alone, before WebRender); expensive effects redrawn per frame
(12 ms / 16–20 W vs 3.8 ms / 3 W on one scroll); video drawn three times
(52% vs 15% GPU on Intel, fixed to 10% vs 30% with surfaces; 65% → 32%);
CPU scene/frame rebuilds per frame (30% vs 14% CPU on YouTube); fill rate
on integrated GPUs (1.6–2 ms per full-screen pass on Ivybridge/Haswell
HiDPI). "On most GPUs this is too much" for scrolling a pathological page
is stated without numbers. No published number isolates "redrawing plain
text/rect content each frame" as a problem.

**Q2.** Picture caching = per-scroll-root slices (max 16) of 1024x512
(Gecko: 512x512 on Windows) cached tiles, each with a dependency list
(primitives, clips, image keys, opacity/colour bindings, transforms)
rebuilt each frame and diffed against the previous frame through interned
keys, a quadtree producing a per-tile dirty rect used as the scissor when
re-rasterizing the tile and as the partial-present rect; solid tiles become
"clear tiles". Compositor surfaces = opaque video/WebGL primitives (≤4,
stable for 15 frames) given their own OS surface so they update without
invalidating tiles; the OS composites the tiles and surfaces (Windows
DirectComposition, macOS CoreAnimation, Wayland subsurfaces), and since
Firefox 149 a "layer compositor" mode handles video/WebGL overlays on
Windows and GTK. Partial present = buffer age plus one damage rect to the
OS on Windows/Android/GTK, none on macOS (where the CALayer tiles are the
partial-update mechanism). Problems solved: GPU time and power for
scrolling and static content, OS window copies, video bandwidth; problems
created: per-frame dependency diffing, over-invalidation from moving clips,
stale tiles when frame building is skipped, GPU memory for tiles and
surfaces, subpixel-AA constraints.

**Q3.** Inherent: pixel traffic costs power (I1), unchanged expensive
effects must not be recomputed (I2), the OS compositor must be told what
changed and on macOS only multiple layers can say it (I4), video must
bypass the frame (I5), and, conditionally on hardware, whole-viewport
redraw on scroll may exceed the budget (I3). WebRender-specific: the
display-list diff and interning (W1, W3), per-frame batch/render-task
rebuilding over the full visible set (W2), tile-grain cache (W5), OpenGL
draw-call and driver constraints (W6), CPU glyph rasterization (W7, shared
with the owner's plan and not a problem). Subpixel AA (W4) is inherent
only if wanted.

**Q4.** Damage-scissored redraw into a persistent or age-tracked target;
present the same rects (DXGI dirty rects / EGL damage with age / Wayland
damage); on macOS a small set of CALayers as the presentation unit only;
never present an unchanged frame; a delta protocol with stable ids and
declared `spread`/`reads_backdrop` so damage comes from the delta, not a
diff; stable GPU slots and indirect draws so per-frame CPU is O(changed +
visible); effect outputs cached by content key and cost; OS surfaces for
video/canvas only; scroll served by viewport redraw if X3/X4 allow, else
scroll-copy, else cost-promoted subtree caches; an explicit decision on
subpixel AA.

**Q5.** Zed: 120 Hz full redraw works on Apple GPUs; reported costs are
5–6x overdraw and 1–2.7 ms GPU per unchanged frame; mitigation in 2026 is
frame skipping, not damage. Vello: caching of sparse strips and glyphs
added 2025–2026; damage-region rendering is an open PR (byte-exact,
scissor per rect); Masonry has no damage regions and winit no damage API;
no power numbers. Flutter: damage from layer-tree diffs since 2021 on
iOS/Metal, flaky on Android (API-level gates, considered backing out);
Impeller needs a separate resolve texture and a ~500 ns blit, skips damage
above 70% dirty; no power numbers. Skia Graphite: 15% MotionMark on M3,
still tile-based in Chrome; Chrome presents one union damage rect. Rive:
full redraw per frame, no damage, no power numbers.

---------------------------------------------------------------------------
## 8. Gaps and what was not found

- No Mozilla measurement isolating the GPU cost of redrawing *plain* text/rect
  content per frame on an integrated GPU; the fill-rate table and the memory
  bandwidth model are the closest.
- No published picture-caching before/after power or GPU-time numbers other
  than the video and OS-compositor cases above; the "most GPUs" claim for
  scroll remains unquantified.
- Chromium's partial-swap power design doc (referenced from
  https://issues.chromium.org/issues/40412661) was behind a sign-in; the
  wezterm issue that quotes a "blinking cursor power halved" result did not
  contain the number when fetched.
- The `Q2 2020 WR Perf Notes` wiki page could not be fetched.
- Rive's per-frame glyph claim is secondary only.
- No retrospective, talk or blog post by Jeff Muizelaar, Dzmitry Malyshau
  (kvark) or Glenn Watson on these design changes was found; kvark's posts
  found were on capture/debug infrastructure, and Glenn Watson's reasoning
  exists only in newsletters, Bugzilla comments and source comments.
- Nothing here was measured in this session; every number is the source's.
