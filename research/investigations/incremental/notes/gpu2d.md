# GPU 2D backends, text, OS damage presentation and an experiment plan for Snowghost's retained-scene shell

Prepared 2026-10-02 for the Snowghost "raster" branch question. It updates `research/investigations/incremental/notes/raster.md` on branch `research/incremental` (prior note, called "raster.md" below).
No GPU in this container; **no number here was measured by me**. Every figure is someone else's, or arithmetic that I mark as such.

**Where `DESIGN.md` departs from this note.** `DESIGN.md` §7 holds the
current tree; where they disagree it wins.
- §6.3 and arm (b) of §7.1 treat a persistent target copied to the
  swapchain (P2) as a working model. `DESIGN.md` 7.3 makes it a dead end:
  the copy moves a full frame every frame. Experiments follow `DESIGN.md`'s
  X10 rather than §7.1's arms where they differ.

## 0. How to read the evidence marks

Each claim carries a status and an evidence-quality tag.

Status (the four requested):
- **ESTABLISHED**: a specification, source file or registry record I read as raw text.
- **THEIRS**: a number or behaviour measured/reported by the project that published it; I did not reproduce it.
- **INFERRED**: my reasoning from established facts; the premises are listed.
- **MEMORY**: from training, not re-verified in this session. Treat as a lead.

Evidence quality (added because the fetch tool returns small-model summaries, and two of them were visibly wrong: a releases page summary said "October 2, 2024" for vello 0.11.0 / glifo 0.4.0, while the crates.io JSON says 2026-10-02; the Linebender blog index fetch returned a list ending January 2025):
- **[raw]**: I read the actual text (spec .adoc/.txt, source files in the crate tarball or on trunk, crates.io JSON, the Microsoft page).
- **[fetch]**: seen only through a WebFetch summary; wording and figures could be distorted. The URL is given so the reader can check.
- **[snippet]**: seen only in a search-result snippet; weakest.
- Where dates conflict, crates.io dates win.

## 1. What changed since raster.md (the deltas are the value)

| Prior note said | Now (2026-10-02) | Status / evidence |
|---|---|---|
| Vello fork (`mindderivative/tre`) does damage redraw; "unverified third-party" | The mechanism it relies on is in **upstream** `vello_gpu` 0.3.0: `TargetInit::SrcOver` (maps to `wgpu::LoadOp::Load`) and `TargetInit::Clear(ClearSettings::Rects{color, rects})` (a scissored clear pass, then `LoadOp::Load`). | ESTABLISHED [raw] crate tarball `vello_gpu-0.3.0/src/render/wgpu/mod.rs:2593-2603`, `src/render/common.rs:29-53` |
| P1 (age-tracked) and P2 (persistent target + copy) both "established" | wgpu has **no** damage-present API on trunk; issue #682 was closed "not planned"; **PR #10152 `Queue::present_with_damage` is open** (Vulkan via `VK_KHR_incremental_present`, EGL via `eglSwapBuffersWithDamage`; DX12 and Metal ignore the rects). wgpu also does not expose buffer age. | ESTABLISHED for the DX12/Metal source facts [raw]; PR content [fetch]. See section 4.3 for why this blocks P1 through wgpu (INFERRED). |
| Vello hybrid "beta" | `vello_hybrid` was renamed `vello_gpu`; `vello_gpu` 0.3.0, `vello_cpu` 0.3.0, `vello_common` 0.3.0, `glifo` 0.4.0, `vello` (compute, "research") 0.11.0 all published 2026-10-02. `vello_gpu` docs still say glyph caching is "experimental and not recommended", yet 0.3.0 contains a `GlyphAtlas`/`GlyphCacheConfig` implementation. | ESTABLISHED [raw] crates.io JSON; `vello_gpu-0.3.0/src/lib.rs:65`, `src/text.rs:16-62` |
| Slug is patent-encumbered | Slug patent dedicated to the public domain effective 2026-03-17; reference HLSL shaders under MIT/Apache; "This algorithm ignores font hinting". | THEIRS [fetch] https://hackaday.com/2026/03/20/slug-algorithm-for-on-gpu-rendering-of-fonts-with-bezier-curves-now-in-public-domain/ , https://mathewsachin.github.io/blog/2026/03/18/decade-of-slug.html , https://github.com/EricLengyel/Slug |
| WebRender is a Mozilla-internal thing | `webrender` 0.68 (2026-01), 0.69, 0.70 (2026-07-10) are on crates.io after a gap since 0.61 (2020-01); the GitHub repo says it is a downstream mirror of mozilla-central `gfx/wr`. It is still OpenGL (`gleam`, `glslopt`, `mozangle`). | ESTABLISHED [raw] crates.io JSON and dependency list; mirror statement [fetch] https://github.com/servo/webrender |
| Skia via skia-safe: Ganesh | `skia-safe` 0.153.3 (2026-09-04) has separate `ganesh` and `graphite` features; Graphite for Metal and Vulkan, no Dawn/WebGPU bindings yet. Chrome ships Graphite on Apple Silicon Macs (announced 2025-07-08). | skia-safe version [raw]; feature split [snippet]/[fetch] https://crates.io/crates/skia-safe , https://github.com/rust-skia/rust-skia/discussions/1243 ; Chrome [fetch] https://blog.google/chromium/introducing-skia-graphite-chromes/ |
| Zed: GPUI "retained scene" implies damage tracking | Zed's own tracker is open: "Excessive display server repaints from missing damage/present regions" (#15166, 2024-07-25, open). The only GPUI damage-rect work I found (PR #63936) is **software-renderer only**; "the existing GPU paths ... remain unchanged". The wgpu PR #10152 says it was validated in production on Linux/Vulkan through Zed. | THEIRS [fetch] https://github.com/zed-industries/zed/issues/15166 , https://github.com/zed-industries/zed/pull/63936 , https://github.com/gfx-rs/wgpu/pull/10152 |

## 2. Candidate backends (Rust)

Update model column answers "what does a small edit cost and who owns the persistent pixels".

### 2.1 Summary table

| Backend | API / update model | Maturity (2026-10) | Text | Cost per frame (documented) |
|---|---|---|---|---|
| **vello_gpu** (sparse strips; CPU path preprocessing, GPU raster + composite; wgpu 30 or WebGL2; no compute shaders) | Immediate-mode `Scene` (CPU context) rebuilt per frame, `Renderer` renders to a user texture. Target init is load (`SrcOver`) or clear-viewport or clear-rects. No retained scene on the GPU. | Crates at 0.3.0. Docs: "slightly less mature" than vello_cpu; some features "panic" (mask layers, complex filter graphs); no API stability guarantee. Linebender called hybrid "roughly beta quality" in April 2026. | `glifo`: atlas-based glyph cache, hinting with LRU cache, variable fonts, COLR; glyph caching flagged experimental. | CPU: path flattening + strip generation for everything in the `Scene` you submit; GPU: strip raster. Cost is O(submitted content), so the shell must cull to the damage rect itself (INFERRED). Drawing is not scissored to the damage rects in the root pass; only the clear pass has `set_scissor_rect` (ESTABLISHED [raw] `mod.rs:643-656`); so wrap damage content in a clip (INFERRED). |
| **vello** (compute, "research") 0.11.0 | `Scene` encoded each frame; the whole pipeline (binning, coarse, fine) runs on every render. | Experimental per the repo README (compute renderer sits in the research directory). | Path-based glyphs; upstream cache described as experimental. | Fixed dispatch floor for the full pipeline; no documented damage mode. The tre fork reports partial redraw only on the **vello_gpu** path. |
| **vello_cpu** 0.3.0 | CPU rasterizer, SIMD + multithreaded; output Pixmap that you upload (or share memory on UMA). | "Most mature" Vello renderer per its README; Linebender's April 2026 note: "competitive performance". | glifo, same as above. | CPU cycles scale with damage area if you restrict the scene; upload of damage region only. Candidate as the correctness oracle and as a fallback for machines with no usable GPU. |
| **WebRender** 0.70 | Retained display lists in documents (`set_display_list`, `DisplayListBuilder`, spatial tree, clip chains, stacking contexts); scene builder + frame builder threads; **picture-cache tiles** hold cached pixels; dirty rects within tiles; OpenGL (gleam). | Production in Firefox and Servo; on crates.io; API churn historically high ("publishing on crates.io doesn't mean anything in terms of API stability" - WebRender newsletter #35 [snippet]); upstream is mozilla-central. | `wr_glyph_rasterizer` (FreeType / DirectWrite / CoreText), glyphs in a texture cache; `enable_subpixel_aa`, `dedicated_glyph_raster_thread` options (docs.rs). | Per-frame dependency comparison per tile and frame building; documented Windows case where tile compositor cost more power than the non-compositor path (section 6.2). Conflicts with the owner's "no tile as invalidation unit" requirement (INFERRED from design). |
| **Skia via skia-safe** 0.153.3 | Immediate-mode `SkCanvas` on `SkSurface`; the host owns persistent surfaces and damage. Graphite: record then replay recordings (Chrome: "re-issued ... with certain dynamic changes such as translation"). | Ganesh stable; Graphite maturest on Metal; rust-skia's Graphite binding was "early development" in January 2026 [fetch], and 0.153.x lists Graphite Metal/Vulkan. C++ dependency, large build. | Best-in-class text on every OS: FreeType/DirectWrite/CoreText scalers, LCD AA, gamma/contrast tables, atlas + SDF paths. | Draws what you submit. No damage logic in Skia itself. |
| **femtovg** 0.27.0 | Immediate mode (NanoVG port), OpenGL ES 3 or wgpu backend. | Used by Slint [fetch] https://github.com/femtovg/femtovg | Own shaping + font matching with atlas. | Draws what is submitted; no damage mechanism. |
| **lyon** 1.0.19 | Tessellator only (paths to triangles). | Stable. | None. | Not a renderer; useful only if the shell writes its own path pipeline. |
| **Blend2D** | CPU, JIT pipelines, optional multithreaded context (described as a prototype). | The C++ library is active (a snippet reports 1.6 on 2025-09-22 and 1.7 on 2025-11-05 [snippet]); Rust bindings `blend2d`/`blend2d-sys` 0.3.0 were last published **2019-07-16** and are marked incomplete. | TrueType/OpenType in-library. | Not a Rust-native option; a research comparison point only. |
| **tiny-skia** 0.12.0 (2026-02-02) | CPU, single-threaded, no text. | Maintained by Linebender. README: 20-100% slower than Skia on x86-64, 100-300% slower on ARM [fetch] https://github.com/linebender/tiny-skia | None. | Reference rasterizer for tests; not a performance candidate. |
| **wgpu 30.0.1** (2026-08-22) as platform layer | Safe API over Vulkan, Metal, DX12, GL. | Mainstream. | n/a | Present path facts in section 4.3. |

### 2.2 Constraints that decide the backend (not a pick)

1. **Persistent target with load + scissored clear** exists upstream in `vello_gpu` (ESTABLISHED [raw]). So "Vello as damage rasterizer" does **not** collapse to "render a small texture and blit" (the P2 variant I feared). It still needs the host to supply a scene limited to the damage rect and a clip, because the root pass has no scissor on drawing (INFERRED from `grep set_scissor_rect`: only the clear pass).
2. The tre fork measured 3.7-4.9x lower per-frame cost for one animating card among 576 on a 1920x1080 window (0.56-1.00 ms vs 2.16-4.78 ms), and equal cost when all cards animate; hardware not given in the summary I received (THEIRS [fetch] https://github.com/mindderivative/tre/pull/17). Interpretation: the CPU-side strip building dominates for small scenes, so Vello cost is dominated by what you resubmit, not by pixels.
3. **WebRender cannot take the owner's property tree and chunk ids without re-expressing them as display lists + spatial/clip trees; its damage unit is the cache tile.** It is the right reference implementation to compare against, not a drop-in backend (INFERRED).
4. **A hand-written wgpu pass** (instanced rect/border quads, glyph atlas quads, image quads, clip/transform from a property-tree buffer) is the only candidate whose per-frame cost is O(visible items) with no per-frame CPU path processing, and whose damage scissoring is a plain `set_scissor_rect` (INFERRED; this is what prior raster.md section 2.5/6 designed around). Zed (GPUI) and WebRender both use this shape for rects and text.

## 3. Text on the GPU

| Technique | Quality (hinting, subpixel, gamma) | Cost and fit | Status |
|---|---|---|---|
| **Glyph atlas + instanced quads** (glyphon: `cosmic-text` shaping, `swash` rasterization, `etagere` packing, wgpu pass; glyphon 0.12.0 2026-07-09, cosmic-text 0.19.0 2026-04-22, swash 0.2.10 2026-07-17) | swash can hint outlines (`ScalerBuilder::hint(bool)`, default false) and can emit alpha or LCD masks (`zeno::Format::{Alpha, Subpixel, CustomSubpixel}`) [fetch]. Cache keys bin fractional x/y (`CacheKey.x_bin/y_bin`, `font_size_bits`) so subpixel positions are cached. Whether glyphon's shader uses LCD masks or gamma/contrast correction is **not documented** in what I saw [fetch]: assume grayscale AA with no contrast tuning until checked. | Cheapest per frame once warm (one quad per glyph, one atlas); cold start pays rasterization. Cost grows with distinct (font, size, subpixel bin) count. | Atlas design ESTABLISHED (glyphon README [fetch]); quality of its shader INFERRED / unverified |
| **WebRender / Skia style** (platform scaler into atlas) | Matches OS text: FreeType / DirectWrite / CoreText hinting, LCD AA, Skia gamma and contrast "hacks" (pre-blend adjustment in the mask using the known text color; blending is not linearised) [fetch] https://skia.org/docs/dev/design/raster_tragedy/ | Best fidelity vs Chromium/Firefox; requires platform glyph rasterizers or FreeType. | THEIRS [fetch] |
| **vello_gpu + glifo** | Glyphs drawn as paths or from an atlas; hinting supported via LRU hint cache; glifo notes hinting is undesirable when the scene is animating or zooming [snippet] https://github.com/linebender/vello/issues/670 . A reported glifo bug: hint-cache lookups by raw run coordinates rebuilt the hinting instance each run (about 25 us vs 0.45 us per run, 7-10 ms encode per frame on a Pixel 9 Pro in text-heavy scenes) [snippet]: evidence that the encode side, not the GPU, is the risk on text-heavy pages. | Per-frame CPU encode scales with glyph runs submitted; atlas caching still flagged experimental in docs. | THEIRS [snippet]; docs status ESTABLISHED [raw] |
| **Slug** (curve evaluation in the fragment shader from band/curve textures) | Exact coverage at any scale, no atlas, no hinting ("ignores font hinting"), multi-color/gradient text needs extra passes [fetch]. | More ALU per pixel than an atlas sample; no atlas misses; good for zoom/rotate, large CJK sets. No published measured cost versus an atlas that I could verify (an alphapixeldev comparison is explicitly unmeasured [fetch] https://alphapixeldev.com/sdf-vs-msdf-vs-slug-vs-rive-gpu-text-rendering/). | Patent dedication THEIRS [fetch]; cost INFERRED/unknown |
| **SDF/MSDF** | Soft corners at small sizes; "at very small sizes you are still sampling too few texels" [fetch]. | Cheap, scale-flexible; poor fit for 12-16 px body text. | THEIRS [fetch] |

Take-aways for experiments (INFERRED): body text at 1x/2x DPR on a mostly static page should be the atlas path (hinted or unhinted per setting); path/curve techniques matter for zoom, rotation and very large glyph sets. A single 8 px-pitch, 12 k-glyph viewport (prior note's arithmetic, raster.md section 1) is about 0.4 MB of instance data per frame; the experiment must confirm that this is not the bottleneck.

## 4. OS presentation for damage

### 4.1 What the specs say

- **EGL buffer age and partial update** [raw]
  - `EGL_EXT_buffer_age`: back buffer age 0 = undefined contents, N = contents from N frames ago.
  - `EGL_KHR_partial_update`: `eglSetDamageRegionKHR` must be called after querying `EGL_BUFFER_AGE_KHR` and before any drawing; draws outside the region give undefined contents for the whole framebuffer. Intended as the efficient alternative to `EGL_BUFFER_PRESERVED` (which implies a full-frame copy).
  - Sources: https://raw.githubusercontent.com/KhronosGroup/EGL-Registry/main/extensions/KHR/EGL_KHR_partial_update.txt , https://raw.githubusercontent.com/KhronosGroup/EGL-Registry/main/extensions/EXT/EGL_EXT_buffer_age.txt
  - ESTABLISHED. Tile-based GPUs additionally use partial_update to avoid fetching/storing unchanged tiles [fetch] https://docs.imgtec.com/reference-manuals/open-gl-es-extensions/html/topics/EGL_KHR/partial-update.html . "surface damage" (for the consumer) and "buffer damage" (for the producer) are different sets; keep both (spec text).
- **Vulkan `VK_KHR_incremental_present`** [raw] https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/chapters/VK_KHR_surface/wsi.adoc (lines 7690-7760)
  - "an optimization hint that a presentation engine may use". The application "still must ensure that all pixels of a presented image contain the desired values, in case the presentation engine ignores this hint".
  - Rectangles are the region "that has changed since the last present to the swapchain": that is **surface damage**, not buffer damage.
  - Vulkan has no buffer-age query. Content of a presentable image after reacquire equals what you last wrote to that image (spec line 7429), so a Vulkan app tracks damage history per swapchain image index itself, and resets it on swapchain recreation (INFERRED).
  - ESTABLISHED.
- **DXGI `Present1`** [raw] https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-1-2-presentation-improvements
  - Dirty rects work in flip and bitblt models; the scroll rect only in flip model.
  - "you save on the usage of memory bandwidth and the related usage of system power".
  - The app must keep every pixel in dirty rects up to date and must copy forward or re-render overlaps between consecutive frames' dirty rects across the N buffers; the runtime copies the rest from the previous frame.
  - The Microsoft example uses `DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL` with `BufferCount >= 2`.
  - ESTABLISHED.
- **Wayland** [raw for Mesa source; fetch for the book]
  - `wl_surface.damage_buffer` is the preferred damage request; `damage` (surface coordinates) is "effectively deprecated". Damage is framed as an optimization: the compositor can copy only a fraction of the surface (https://wayland-book.com/surfaces-in-depth/damaging-surfaces.html [fetch]).
  - Mesa Vulkan WSI forwards `VkPresentRegionsKHR` rects as `wl_surface_damage_buffer` (and falls back to max damage if the compositor lacks `damage_buffer`): `src/vulkan/wsi/wsi_common_wayland.c:3375-3395` (ESTABLISHED [raw], fetched from the Mesa main branch on 2026-10-02).
  - `VK_KHR_incremental_present` is advertised in Mesa's `radv_physical_device.c`, `anv_physical_device.c` and `nvk_physical_device.c` (ESTABLISHED [raw]).
  - Firefox bug 1648872: partial present "never worked" in official builds because unversioned `wl_registry_bind` made Mesa fall back to full-window damage; fixed in Firefox 82 [fetch] https://bugzilla.mozilla.org/show_bug.cgi?id=1648872 . Lesson: verify with `WAYLAND_DEBUG=1` that damage reaches the compositor.
  - Frame pacing protocols `wp_fifo_v1` and `wp_commit_timing_v1` were added to wayland-protocols 1.38 (staging) [snippet] https://www.phoronix.com/news/Wayland-Protocols-1.38 . Compositor adoption varies (MEMORY).
- **macOS** CAMetalLayer / CoreAnimation
  - No partial-update API for `CAMetalLayer`; the Firefox team's answer (2019) was "smaller layers": split the window into many square CoreAnimation layers backed by IOSurface, update only the dirty layers [fetch] https://mozillagfx.wordpress.com/2019/10/22/dramatically-reduced-power-usage-in-firefox-70-on-macos-with-core-animation/ . I found no newer Apple API; absence of evidence, so treat as "THEIRS 2019, re-check".
  - wgpu's Metal backend only supports `Fifo` and `Immediate` present modes (`displaySyncEnabled`), sets `maximumDrawableCount = maximum_frame_latency + 1`, and calls no damage API (ESTABLISHED [raw] `wgpu-hal/src/metal/surface.rs:266-270,342`).
  - Apple GPUs are tile-based (MEMORY): partial render passes still pay per-tile load/store unless load actions say otherwise; this is why Impeller on iOS adds a separate resolve texture and a 70% damage threshold (THEIRS [fetch] https://github.com/flutter-team-archive/engine/pull/40959).
- **DirectComposition** (Windows) (MEMORY plus wgpu source): lets an app hand the OS compositor several swapchains/visuals. wgpu can create a DXGI swapchain from a visual (`Dx12SwapchainKind::DxgiFromVisual`, `wgpu-types/src/backend.rs`) (ESTABLISHED [raw]). Firefox enabled a WebRender "layer compositor" on Windows in Firefox 149 after a revert in 147 and measured about 10% power saving in full-screen video (29-30 W vs 32-35 W, 15-16 vs 17-18 W, 11-12 vs 12-13 W) (THEIRS [fetch] https://bugzilla.mozilla.org/show_bug.cgi?id=2000149).
- **KMS / panel self refresh** (MEMORY plus snippet): Intel PSR2 selective update and DRM `FB_DAMAGE_CLIPS` let the panel refresh partial regions; PSR enabling saved about 0.5 W on one laptop per a community post [snippet] https://hansdegoede.livejournal.com/18653.html . Applications rarely control this; the compositor does, from damage it receives (MEMORY).

### 4.2 What each mechanism saves, and constraints

| Mechanism | Saves | Does not save | Constraint |
|---|---|---|---|
| Scissored redraw into a persistent or age-valid target | GPU shading, ROP bandwidth, power | Scanout (the display scans the whole frame every refresh) | Needs valid old pixels: buffer age (EGL), own per-image tracking (Vulkan/DX12), or a persistent offscreen target |
| Present with damage (`swap_buffers_with_damage`, `VkPresentRegionsKHR`, `Present1` dirty rects) | Compositor copy/blend work, memory bandwidth, can enable PSR2/selective update | App-side shading | A hint; the full image must still be correct; DXGI additionally requires the intersection copy across buffers |
| Scroll rect (DXGI flip model only) | Re-render of scrolled area | | Windows only; not exposed by wgpu |
| OS compositor layers/tiles (CoreAnimation, DirectComposition, Wayland subsurfaces) | Whole-surface re-render and compositing for static layers | Cost of many layers (bug 1602803) | Brings back tile-like partitioning |

### 4.3 What this means for wgpu as the platform layer

- **Presentation modes** (ESTABLISHED [raw] https://docs.rs/wgpu/30.0.1/wgpu/enum.PresentMode.html [fetch] plus HAL source): `Fifo` (everywhere, about 3 frames deep), `FifoRelaxed` (AMD on Vulkan), `Immediate`, `Mailbox` (DX12 on Windows 10, NVIDIA on Vulkan, Wayland on Vulkan), `AutoVsync`, `AutoNoVsync`. Metal supports only Fifo and Immediate. `desired_maximum_frame_latency` maps to `min_image_count - 1` on Vulkan (`vulkan/swapchain/native.rs:228`), to drawable count minus one on Metal.
- **DX12**: `Present(interval, flags)`, not `Present1` (`wgpu-hal/src/dx12/mod.rs:1726-1745`), and the swap effect is `DXGI_SWAP_EFFECT_FLIP_DISCARD` (`wgpu-hal/src/dx12/mod.rs:1440` on trunk) (ESTABLISHED [raw]). Therefore dirty rects and scroll rects are unavailable through wgpu on Windows today; PR #10152's rationale that FLIP_DISCARD "prohibits partial presentation" is the PR author's claim [fetch]; Microsoft's example uses FLIP_SEQUENTIAL. Using damage on DX12 would need a wgpu patch or a native DXGI/DirectComposition path.
- **No buffer age and no swapchain-image index** is exposed by `wgpu::Surface::get_current_texture` as far as I know (MEMORY; INFERRED from the API: `SurfaceTexture` carries the texture and a `suboptimal` flag). Consequence (INFERRED): P1 from raster.md (age-tracked scissored redraw straight into the swapchain image) is **not expressible** through wgpu. The wgpu-expressible form is P2: persistent offscreen target + copy to the acquired image.
  - Because Vulkan treats damage as a hint and requires the whole image to be right, the copy must cover the whole frame unless the shell can tell which swapchain image it got.
  - Arithmetic (INFERRED, assumes 4 bytes/pixel, read + write): full-frame copy per frame is 16.6 MB at 1920x1080, 41.5 MB at 2880x1800, 66.4 MB at 3840x2160; at 120 Hz that is 2.0, 5.0 and 8.0 GB/s. A damage-limited redraw does not remove this cost, so P2 can erase part of the saving on integrated GPUs (shared LPDDR bandwidth). Experiment arm required (section 7).
  - The escape is wgpu-hal interop or a native swapchain for the platform, giving real buffer age on EGL, own image-history on Vulkan.
- **Known wgpu performance trap** (THEIRS [fetch] https://github.com/gfx-rs/wgpu/issues/9559): since wgpu-hal 26.0.6, `Surface::get_current_texture` latency on AMD RX 6800 XT, Windows 11, Vulkan, `Immediate` rose from 74 us mean to 4,833 us mean (p99 130 us to 20,254 us), 78 to 56 fps; still open through 29.0.x. Pin and test the exact wgpu version per GPU vendor.
- **Active upstream work**: PR #10152 open as of 2026-09-29 [fetch]. The older investigation issue #2869 proposed an extended presentation API (damage, scheduling, statistics) but is a tracking issue only [fetch].

## 5. Published measurements: full redraw vs damage-limited vs cached

Everything here is THEIRS and mostly [fetch]; no source gives a clean "same machine, full vs damage-limited, watts" laptop number at high DPI.

| Source | Setup | Result | Notes |
|---|---|---|---|
| Firefox 70 macOS (CoreAnimation, tiles in IOSurface layers) https://mozillagfx.wordpress.com/2019/10/22/dramatically-reduced-power-usage-in-firefox-70-on-macos-with-core-animation/ [fetch] | MacBook Pro early 2013 | Scrolling 16.4 W to 9.4 W (-43%); spinning square 12.8 to 2.9 W; Google Docs idle 7.4 to 1.6 W; loading animation 19.4 to 1.8 W | Bundles three changes (CA layers, partial update, opaque layers). Old Intel/NVIDIA hardware. Not a clean damage-only number. |
| Same project, bug 1429522 https://bugzilla.mozilla.org/show_bug.cgi?id=1429522 [fetch] | blank Google Doc, blinking cursor | 30 W total (15 W GPU) to 7 W total (0.2 W GPU) | The strongest evidence that idle-ish pages are dominated by "nothing drawn, nothing presented" vs "full-window redraw per cursor blink". |
| Chromium partial swap https://groups.google.com/a/chromium.org/g/graphics-dev/c/bprmj7GeyRA [fetch]; power claim from a search snippet | | "drops power consumption by a blinking cursor in Google Docs to about half" | The claim is a snippet, not located in a primary document; Chromium uses a **single** bounding damage rect (hackmd summary [fetch] https://hackmd.io/@elkurin/r1Ux087ST) and, on Mac/ChromeOS, manages back buffers and damage history itself (`SkiaOutputDeviceBufferQueue`). |
| Firefox Windows, bug 1602803 https://bugzilla.mozilla.org/show_bug.cgi?id=1602803 [fetch] | Surface Go, Iris 550, GTX 1050, HD530 | With the OS-compositor tile mode: 50% GPU vs 25% (Surface Go); Iris 550 20 W vs 15.5 W; GTX 1050 13.3 W vs 8.5 W; caused by DWM cost, clip-rect-driven tile invalidation | A counter-example: moving pixels into OS-composited tiles raised power on integrated GPUs. Resolved by fixing tile invalidation, not by abandoning tiles. |
| WebRender partial present, bug 1480172 https://bugzilla.mozilla.org/show_bug.cgi?id=1480172 [fetch] | | Glenn Watson: "unlikely to help with CPU usage - it would be more related to saving GPU memory bandwidth and thus power savings" | Predicts that damage wins appear in power and bandwidth, not CPU time. |
| WebRender on Android with `EGL_KHR_partial_update` (bug 1575765) [fetch] | Mali/Adreno | Mobile GPUs reported buffer age 3, not the assumed 2; flicker from rendering without swap | Driver behavior is a correctness risk, not just a perf matter. |
| kitty issue #3898 https://github.com/kovidgoyal/kitty/issues/3898 [fetch] | A commenter quoting a different project | RX 480: about 60 W to 50 W with `EGL_EXT_buffer_age` when "continually updating ~20% of a frame" | Anecdote relayed by an issue author, not a controlled measurement. |
| tre PR #17 (Vello fork) https://github.com/mindderivative/tre/pull/17 [fetch] | 1920x1080, 576 animated cards, one animating | 0.56-1.00 ms vs 2.16-4.78 ms per frame; no gain when all animate | Frame time of their pipeline; hardware not captured. |
| GPUI software renderer PR #63936 https://github.com/zed-industries/zed/pull/63936 [fetch] | Windows 11 (WARP baseline), Linux Wayland (llvmpipe baseline) | CPU ms per frame 181.9 to 7.8 (-95.7%, full-frame scenario), caret scenario 73.6 to 5.3 ms (-92.9%) | CPU raster baselines, not GPUs. GPU path unchanged. |
| Flutter Impeller iOS partial repaint PR #40959 [fetch]; issue #124526 [fetch] | iPhone 13 | Blit about 500 ns full-screen; partial repaint used only when damage is under 70% of width/height; issue open, priority P3 | No power numbers. Shows the threshold design: skip partial paths when damage is large. |
| Zed blog on 120 fps https://zed.dev/blog/120fps [fetch] | M1 | Render "under 4 ms"; frame times oscillating 8-16 ms with CVDisplayLink; has a dirty flag but the post does not describe damage tracking | Frame-pacing, not damage. |
| Chrome Graphite announcement [fetch] https://blog.google/chromium/introducing-skia-graphite-chromes/ | MacBook Pro M3 | Motionmark 1.3 up almost 15%; lower GPU process memory; "the performance difference between drawing a cached image and drawing its content can be worth skipping allocating a tile" | Direct statement of the owner's "cache pixels only where measured cost says so" policy by a production browser. |
| Android HWUI | | The partial-update extension "helps tile GPUs avoid loading unchanged tiles"; HWUI has properties to use buffer age with a `BUFFER_PRESERVED` fallback [snippet] | **Gap**: no published HWUI or Flutter damage-region power numbers found. |

**Gaps (not chased)**: no measured Flutter DRM or Android HWUI power numbers; the Alacritty partial-render issue (#5843) has none; Chromium's "Mac: investigate implementing partial swap" issue is behind a login; no published high-DPI integrated-GPU "full vs damage" watts measurement found. The experiment in section 7 therefore has no published prior to calibrate against; its thresholds must be stated in advance.

## 6. Interpretation for the shell design

6.1 (INFERRED) The published power swings come from **what the OS compositor and driver do per present** (full-window blend, tile counts, DWM work) as much as from shader work. So the experiment matrix must vary the draw knob and the present knob independently.

6.2 (THEIRS) Two independent teams found that moving to OS-composited tiles can reduce power (macOS Firefox 70) or increase it (Windows Firefox, bug 1602803), depending on tile invalidation and DWM behavior. Owner's choice to avoid tiles as the damage unit is supported; but "no layers at all" on macOS means CAMetalLayer without partial update, i.e. every present is a full-surface compositor update (INFERRED from the 2019 statement; verify).

6.3 (INFERRED) The persistent-target model (P2) is the only model that works through wgpu today on all three OSes, at the cost of a full-frame copy; the age-tracked model (P1) needs native swapchain control. The experiment's arm (b) vs (c) isolates the value of damage hints; arm (e) below measures the full-copy tax.

## 7. Experiment plan for the GPU machine

### 7.0 Prerequisites and scope

- **Question 0** (half a day): does any wgpu or wgpu-hal path give the acquired swapchain image index or an age on Vulkan/DX12/Metal? If not, record it as a constraint; P1 is out through wgpu.
- Build `wgpu` pinned at 30.0.1 plus a local patch that applies PR #10152 (Vulkan/EGL damage) for the Linux arms.
- **Scene dump**: JSON or binary of a real page after layout and paint (the Whitefoot/Snowghost renderer's chunk list): per chunk id, local rects, borders (widths, colors, radii), glyph runs (font id, size, glyph ids, positions), images, and the property tree (transform, clip, effect, scroll nodes) plus the viewport. Add an *edit script*: a list of (chunk id, change) steps for a one-line text change, a caret blink, a hover color change, and a 1-line reflow shift. Pages: at least one text-heavy (ecma262-like), one card/UI page, one with shadows/blur.
- **Backends under test** (same dump, same pixel oracle):
  - **A** hand-written wgpu pass (instanced quads for rects/borders, glyph atlas from swash/cosmic-text or glifo, image quads).
  - **B** `vello_gpu` 0.3.0 with `TargetInit::Clear(Rects)` plus damage clip, glifo atlas on and off.
  - **C** `vello_cpu` + upload of damage region only (CPU reference and fallback).
  - **D** optional: Skia Graphite via `skia-safe` 0.153.x on Metal/Vulkan.
  - **E** optional: WebRender 0.70 `wrench`-style harness with the page converted to display lists, as the tile-based baseline.
- **Correctness oracle first** (prior X1, rerun here): for every edit step, damage-scissored output must equal the full redraw bit-for-bit (A) or within a stated tolerance (B, text AA). A check must be seen to fail once for each failure mode: a missing chunk in the damage list, a stale per-image history, a swapchain recreate.

### 7.1 Arms (each at 1920x1080 and 3840x2160 or the machine's native HiDPI size; 60 and 120 Hz if available)

| Arm | Draw | Present |
|---|---|---|
| a | full redraw each frame | full present |
| b | damage-scissored redraw into persistent target, then full-frame copy to the swapchain | full present |
| c | as b | present with damage (PR #10152 on Vulkan/EGL; native `Present1` with FLIP_SEQUENTIAL on Windows; none on macOS) |
| d | scroll: (d1) redraw the visible chunks each frame at a new scroll offset; (d2) draw a cached texture of an overscan region at an offset and redraw only newly exposed strips; (d3) d2 + DXGI scroll rect on a native Windows path |
| e | the copy tax: copy only damage rects (where image history is known: EGL buffer age, or a Vulkan patch with per-image history) vs full-frame copy, same damage |
| f | idle: nothing changed; present suppressed vs a damage-empty present vs a full present |

Damage sweep for a, b, c, e: caret (about 2x20 px), one text line, 5% / 25% / 50% / 100% of the surface, plus two distant small rects (checks the multi-rect merge policy; Chromium collapses to one rect).

### 7.2 Frame-time metrics (GPU machine, per arm)

- GPU time per pass via `wgpu::Features::TIMESTAMP_QUERY`; CPU time for scene update, culling/encode, `get_current_texture`, `submit`, `present` (cite issue #9559's `get_current_texture` pathology as a reason to log it separately).
- Present-to-photon latency: PresentMon 2.x on Windows (GPU busy, frame time, display time) [snippet] https://github.com/GameTechDev/PresentMon ; `wp_presentation` feedback on Wayland; MetalPerformance HUD / `CAMetalDisplayLink` stats on macOS (MEMORY, verify).
- 1,000+ frames per arm after a 5 s warm-up; report median, p95, p99, and dropped frames against the budget (8.33 ms at 120 Hz; 6.94 ms at 144 Hz; 4.17 ms at 240 Hz).
- Atlas behavior: glyph atlas miss counts and cold-page first-visit cost for backends A and B.

### 7.3 Power measurement

Power must be measured over at least 30 s windows (5 repeats, median and spread), with an idle baseline subtracted, fixed brightness, display refresh and OS power plan, and the same compositor/session. Include system-level (wall or battery) power to catch compositor cost that process counters miss. Measuring only the app's GPU/CPU hides exactly the effect the Firefox bugs showed.

| OS / hardware | Package / CPU+iGPU energy | GPU | Whole system |
|---|---|---|---|
| Linux Intel | RAPL via `perf stat -a -e power/energy-pkg/` (needs `CAP_PERFMON` or `perf_event_paranoid <= 0`) or `/sys/class/powercap/intel-rapl*/energy_uj` (cumulative uJ; Intel RAPL gives energy, not instantaneous power) https://docs.kernel.org/power/powercap/powercap.html [fetch] | `intel_gpu_top -o` logs GPU and package power with engine busy and RC6 [snippet]; the package domain includes the iGPU | battery `power_now` or a wall meter |
| Linux AMD | `energy-pkg` supported from Linux 5.8, powercap Zen1-3 from 5.11 [snippet] https://www.phoronix.com/news/AMD-Zen-RAPL-Linux-5.8 ; per-core energy via perf in newer kernels | `amdgpu` hwmon `power1_average` (MEMORY) or `amd-smi` (MEMORY) | wall meter |
| NVIDIA (Linux or Windows) | CPU as above | `nvidia-smi --query-gpu=power.draw` (average over 1 s on Ampere+, +/-5 W spec) or NVML `nvmlDeviceGetTotalEnergyConsumption` (mJ, newer than Pascal) [snippet]; **caution**: a study found `nvidia-smi` samples only about 25% of runtime on A100/H100 and its error is closer to +/-5% than +/-5 W https://arxiv.org/abs/2312.02741 [fetch]. Use the NVML energy counter and a wall meter for the discrete card case. | wall meter |
| Windows | Intel Power Gadget is discontinued (MEMORY): use `pcm` (Intel PCM) / HWiNFO sensors (MEMORY) and Windows Performance Recorder/Energy Estimation Engine (MEMORY) | PresentMon 2.x GPU telemetry (power on supported Intel Arc; NVIDIA via NVML) [snippet] | wall meter; battery discharge rate (`powercfg /batteryreport` is too coarse; MEMORY) |
| macOS | `sudo powermetrics --samplers cpu_power,gpu_power -i 1000` (mW, estimated SoC subsystem power; run as root) [snippet] https://manp.gs/mac/1/powermetrics | same sampler, plus Xcode Instruments Energy/Metal System Trace (MEMORY) | wall meter or `pmset -g batt` (coarse) |

Controls: close other apps; lock the refresh rate; run the same window size; repeat in both compositor idle and with a competing window visible (to prevent direct-scanout special cases changing the result; MEMORY).

### 7.4 Decision criteria (fix them before running)

Inputs per page and per damage size: the frame budget `B` for the target refresh rate and the arm's measured cost.

1. **Redraw policy.** Adopt damage-limited redraw (b over a) if full redraw (a) costs more than 25% of the frame budget on the median page at the machine's native resolution, or if b saves more than 20% of whole-system energy in the "one text line" and "caret" arms, with the difference larger than the run-to-run spread (3 sigma of the repeated idle-baseline-subtracted measurements).
2. **Present policy.** Use damage presentation (c over b) only if the extra energy saved in c vs b exceeds noise **and** is at least 5% of the b-vs-a saving or 100 mW, whichever is larger (a threshold I propose; adjust before running); and only on platforms where it is expressible (Vulkan/EGL via patched wgpu; native DXGI on Windows; none on macOS).
3. **Copy tax.** If the full-frame copy in b costs more than the shading it saved at 4K (arm e vs b), do not choose P2; take the native-swapchain path with image-history, or draw directly to the swapchain with a scissor where age is known.
4. **Pixel caches.** Cache a subtree or scroll overscan texture (d2) only if redrawing it costs more than sampling its cached texture plus invalidation by a margin of 20% median frame time at the same quality, which is the prior raster.md claim C1 recast; use Chrome's own statement as a prior ("worth skipping allocating a tile" when content is simple) [fetch].
5. **Backend.** Prefer A if it meets (1) with B's cost no better by more than 20% on the text-heavy page; prefer B if it is within 20% of A and removes enough code (paths, shadows, gradients, filters) to justify Vello's CPU encode; keep C as the correctness reference. If B's CPU-side encode exceeds 25% of the budget on the text-heavy page with glifo caching on, treat B as unsuitable for text and consider hybrid text = A's atlas, everything else = B.
6. **Text.** Atlas stays default for 12-16 px body text if it beats Slug or glifo path text by more than 20% GPU time and matches the reference raster (SSIM against Chromium-rendered pixels) at least as well; Slug or glifo paths for zoom, rotation and large glyph sets.

### 7.5 Reported threats to validity

Driver age reporting and present-mode surprises (Firefox Android buffer age 3; AMD/wgpu latency regression); thermal throttling on laptops; compositor behavior differences (GNOME/KDE/Weston); VRR; HiDPI scaling fractional factors; wgpu version drift.

## 8. Not verified here

- All GPU speed, power and latency numbers for Snowghost. None were measured in this session.
- Compositor-side use of client damage in Mutter/KWin/wlroots (MEMORY).
- Whether `vello_gpu` text with glifo atlas is production-quality; docs say it is not recommended.
- Blend2D version claims (snippet only), `intel_gpu_top` and powermetrics specifics (snippet).
- Slug patent number: left out because it came only from a snippet. The dedication date (2026-03-17) is in two independent write-ups.

## 9. Sources (all fetched or searched 2026-10-02)

Specs / source read raw:
- https://raw.githubusercontent.com/KhronosGroup/EGL-Registry/main/extensions/KHR/EGL_KHR_partial_update.txt
- https://raw.githubusercontent.com/KhronosGroup/EGL-Registry/main/extensions/EXT/EGL_EXT_buffer_age.txt
- https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/chapters/VK_KHR_surface/wsi.adoc and https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/appendices/VK_KHR_incremental_present.adoc
- https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-1-2-presentation-improvements
- https://gitlab.freedesktop.org/mesa/mesa/-/raw/main/src/vulkan/wsi/wsi_common_wayland.c ; `radv_physical_device.c`, `anv_physical_device.c`, `nvk_physical_device.c` in the same tree
- https://raw.githubusercontent.com/gfx-rs/wgpu/trunk/wgpu-hal/src/dx12/mod.rs , `.../metal/surface.rs`, `.../vulkan/swapchain/native.rs`, `wgpu-types/src/backend.rs`
- crates.io API JSON for wgpu, vello, vello_cpu, vello_hybrid, vello_gpu, glifo, skia-safe, webrender, tiny-skia, femtovg, glyphon, cosmic-text, swash, blend2d, lyon
- https://static.crates.io/crates/vello_gpu/vello_gpu-0.3.0.crate (read `src/render/common.rs`, `src/render/wgpu/mod.rs`, `src/text.rs`, `src/lib.rs`)

Fetch-summarized or snippets: URLs inline above, plus https://linebender.org/blog/tmil-25/ (Linebender 2026 Q1, April 2026), https://github.com/linebender/vello , https://docs.rs/vello_gpu/latest/vello_gpu/ , https://docs.rs/glifo/latest/glifo/ , https://github.com/gfx-rs/wgpu/issues/682 , https://github.com/gfx-rs/wgpu/issues/2869 , https://github.com/gfx-rs/wgpu/pull/10152 , https://github.com/gfx-rs/wgpu/issues/9559 , https://skia.org/docs/dev/design/raster_tragedy/ , https://github.com/grovesNL/glyphon , https://github.com/pop-os/cosmic-text , https://docs.rs/swash/latest/swash/scale/struct.ScalerBuilder.html , https://docs.rs/zeno/latest/zeno/enum.Format.html , https://docs.rs/cosmic-text/latest/cosmic_text/struct.CacheKey.html , https://doc.servo.org/webrender/index.html , https://doc.servo.org/webrender/struct.WebRenderOptions.html , https://bugzilla.mozilla.org/show_bug.cgi?id=1575159 , https://bugzilla.mozilla.org/show_bug.cgi?id=1575765 , https://github.com/zed-industries/zed/issues/15166 , https://github.com/flutter/flutter/issues/124526 , https://github.com/alacritty/alacritty/issues/5843 , https://docs.kernel.org/power/powercap/powercap.html , https://arxiv.org/abs/2312.02741 .
