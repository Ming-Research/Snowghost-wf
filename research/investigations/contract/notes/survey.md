# The renderer-to-shell contract: a survey and three candidate designs

Research note for Snowghost, 2026-10-03. Scope: what the Whitefoot renderer
publishes to the Rust shell, how a frame's change crosses shared memory, and
how one format serves both a first frame and a one-word edit. It surveys
Chromium (Blink paint chunks, cc property trees, viz frames, the newer
`LayerContext` path), WebRender with Gecko and Servo, Flutter, Fuchsia's
Flatland and Android's hwui, then proposes three contract designs, a
recommendation, and the experiments that would decide the open points.

Evidence marks used on every claim:
- **[E]** established: I read the primary source this session (URL given).
- **[R]** recalled: from memory, not re-read this session; treat as a lead.
- **[I]** inferred: my reading or arithmetic; the assumptions are stated.
- **[SG]** a fact about Snowghost or Whitefoot read from its repository at
  `origin/main` acd7a80 (Snowghost) or the active Whitefoot spec.

Source-URL notes. Chromium files were read from
`https://chromium.googlesource.com/chromium/src/+/main/<path>`; WebRender
from `https://raw.githubusercontent.com/mozilla-firefox/firefox/main/gfx/wr/<path>`,
which mirrors mozilla-central (`hg.mozilla.org/.../raw-file/tip/...` serves
the same files behind a redirect); Flutter from
`raw.githubusercontent.com/flutter/flutter/master/engine/src/flutter/<path>`;
Android from `android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/hwui/<path>`;
Fuchsia from `fuchsia.googlesource.com/fuchsia/+/refs/heads/main/<path>`.

---------------------------------------------------------------------------

## Summary (one page)

**What the precedents send.** Every system splits the same three things
apart: *content* in local coordinates (Blink paint chunks, WebRender display
items, Flutter display lists, hwui display lists), *properties* in a tree
(Blink and cc's transform, clip, effect and scroll trees, WebRender's spatial
tree, Flatland's transforms, hwui's per-node `RenderProperties`), and
*resources* by key (WebRender's image and font keys, viz transferable
resources, Flatland images). They differ in what crosses a process boundary
and whether the receiver is told what changed:
- Chromium's renderer sends viz a **complete frame of quads per frame**
  (`CompositorFrame` "contains the complete output meant for display") [E];
  the newer, flag-gated `LayerContext` sends **only layers and property
  nodes added or modified**, the layer order only when it changed, and
  animation keyframe models [E]. Raster stays on the renderer's side: viz
  receives tiles.
- Gecko sends WebRender a **whole display list per change** and WebRender
  diffs it; a content-side interner that makes unchanged items cross as
  stable handles landed on 2026-09-21 with nothing interned yet [E].
- Flatland is a **feed-forward op stream** on client-chosen ids, applied
  atomically at `Present`, with present credits for backpressure and release
  fences for buffer reuse; an invalid op closes the channel [E].
- Flutter and hwui hand a whole tree to a raster thread in one process;
  Flutter diffs layers by instance identity and then by deep compare capped
  at a byte limit [E]; hwui blocks the UI thread during a sync step [E].

**Three findings that bear directly on Snowghost's contract.**
1. **Chunk grain.** `DESIGN.md` 2.1 makes a paint chunk "per context and
   paint phase", but one block formatting context holds 85 to 95 percent of
   the text [SG]. On html5 (2,645,960 scalars, 11,794 contexts, 32,684
   paragraphs [SG]) a one-word edit would then republish about 19 MB of glyph
   data [I]. The frame walkthrough already makes each paragraph its own chunk.
   The contract needs a chunk per paragraph (X1's unit) or finer, which is
   about 0.7 KB for a one-word edit [I].
2. **Whitefoot has no shared-memory host module.** The six host modules are
   a closed list [SG, PRE-2]; a byte stream (`std::io::write_once`) exists
   today. Shared memory needs a new host module. HOST-1 orders two host
   writes only through state both reach. So "payload before epoch" has to go
   through one region owner, and parallel paint output is best built as
   Whitefoot values and copied once [I].
3. **Two facts are missing from the Q65 table.** Shell-side scrolling needs
   (a) hit-test and scroll-routing facts: pointer-events, touch-action, and
   regions whose input handlers block scrolling. Chromium sends a
   `HitTestRegionList` and per-chunk hit-test data [E]; Servo sends a scroll
   tree with touch-action [E]. It also needs (b) a protocol for a scroll
   offset that has **two writers**: the shell scrolls, and script sets
   `scrollTop`. WebRender carries an external scroll offset with a
   generation [E].

**Candidates.**
- **A. Retained arena plus epoch journal:** immutable records read in place,
  freed after an acknowledgement.
- **B. Transactions copied into a shell-owned scene:** the Flatland and
  `LayerContext` shape, where the ring is reclaimed as it is consumed.
- **C. Versioned snapshot with structural sharing:** the shell diffs roots
  by offset equality.

In all three, ids are renderer-allocated with generations; chunks are
immutable and carry no position; placement and order sit in tables of their
own; resources are separate long-lived blobs. A one-word edit is about
0.7 to 1 KB. A complete first frame of html5 is about 13 to 27 MB depending
on the glyph encoding, against about 25 to 45 KB for three viewports [I]. That
gap is X9's question, and the contract should carry a "painted region" fact
so progressive publication stays possible.

**Recommendation: B.** Its semantics are independent of the transport, so it
runs over a pipe today and over a shared-memory ring once Whitefoot has one.
The shell copies data before validating it, so a renderer bug cannot change
bytes after validation. Reclamation is a read index, not an epoch-tracked
heap. Its weakness is a shell restart, which needs a full republish. The
renderer can produce one from its memoized paint results.

**Q65 checks, three layers.**
- **Contract replay:** after any history of edits, the scene built from the
  deltas equals the scene from one full publish (`DESIGN.md` §8, extended).
- **Pixels at rest:** every shell policy's frame at rest equals a reference
  full redraw (X14), with Q66's resampling exception.
- **Fact soundness:** the reference rasterizer verifies every declared
  claim (bounds, opaque rect, backdrop reads) against the chunk's own
  pixels. A wrong fact breaks the invariant even when every policy is right.

The contract rule that makes this checkable: every field is either drawn by
the reference redraw or is a claim about what it draws. Facts the shell can
derive (glyph counts, blur cost, "content or geometry changed") are not sent.

---------------------------------------------------------------------------

## 1. What Snowghost already fixes [SG]

- **Processes and ownership** (`design/processes.md`).
  - Two processes "connected by data rather than calls". The renderer sends
    "display lists, property trees and animation descriptions in a
    versioned format through shared memory", and receives input and loaded
    resources over a channel.
  - The renderer owns image decoding and font validation. The shell owns
    rasterization, compositing, presentation, scrolling, compositor-only
    animations and system fonts.
  - Q65: "The renderer sends the shell facts about the page and never
    decides how it is drawn ... no policy changes the picture at rest, only
    its cost".
  - Q66: the one exception is a texture cached under a transform animation
    that scales, rotates or moves it by a fraction of a pixel; it is
    resampled until the animation ends.
- **Layout output** (`design/pipeline/layout.md`, Q55). Each context writes
  offsets from its own border box, and its parent places it by one offset.
  Absolute positions are computed "only by the walk that dumps or paints".
- **Paint boundary** (`DESIGN.md` 6.1–6.3).
  - Chunks are in context coordinates, with stable ids and content hashes.
  - Order lists hold chunk references per stacking context; properties live
    in trees.
  - Deltas go "through shared memory with epoch acknowledgement".
  - 6.3 tabulates the facts the shell needs.
- **Sizes** (`experiments/contract/report.md`).
  - Over 30 real sites, median and p90: fixed 1.5 and 5, sticky 1 and 3,
    nested scroll roots 1 and 4, backdrop-filter 0 and 3, video 0 and 6,
    running animations 0 and 40. No animation animates a layout property.
  - ecma262 has 33,422 `mix-blend-mode` users from one rule.
- **Page scale** (`research/investigations/concurrency/runs/0-check-base-e45ccb7.txt`):

  | page | elements | contexts | paragraphs | scalars | height (px) |
  |---|---:|---:|---:|---:|---:|
  | html5 | 117,179 | 11,794 | 32,684 | 2,645,960 | 1,283,308 |
  | ecma262 | 179,471 | 9,931 | 37,485 | 2,025,062 | 1,222,660 |
  | apollo11 | 11,844 | 235 | 770 | 128,790 | 409,588 |

- **Edit locality** (X1, X3).
  - A word edit changes one paragraph in 68 of 70 edits.
  - Context-relative offsets rewrite few roots for word edits. html5
    `text+word` moved context roots are 1/4/34 (median/p90/max).
  - Sentence edits rewrite many: html5 `text+sentence` is 228/1,287/2,092.
  - A summary tree needs 5 to 819 times fewer rewrites at p90
    (`census/html5.agg.txt`, `DESIGN.md` Results).
- **Whitefoot** (Whitefoot's `spec/kernel-spec.md`).
  - [PRE-2]: "The host modules are the six standard library modules
    `std::time`, `std::io`, `std::text`, `std::fs`, `std::net` and
    `std::process`". `std::io` has `write_once(factory, output: &OutputStream, source: &[u8], ...)`.
  - [HOST-1]: "Host effects are ordered through shared state and in no other
    way ... an order between two host operations exists only through state
    both reach."
  - No shared-memory or atomic cross-process primitive exists. `atomic` and
    `Shared` [SHARE-1..3] are in-process.

---------------------------------------------------------------------------

## 2. Survey

### 2.1 Chromium: Blink paint chunks and property trees

**What paint produces.** "Paint artifact consists of a list of display items
in paint order ... partitioned into *paint chunks* which define certain
*paint properties*" [E, Blink paint README]. A chunk is "a contiguous
sequence of drawings with common paint properties" [E, `paint_chunk.h`].
Its fields, read from the header [E]:
- `id`: "should be stable across document cycles". A display item's id is
  the pair (client pointer, type), and a chunk whose client is "just
  created" must not match an old chunk with an equal id, "which may happen
  if this chunk's client is just created at the same address of the old
  chunk's deleted client". Pointer identity needed this explicit guard
  against address reuse: a revision worth copying as a generation number.
- `properties`: the chunk's `PropertyTreeState`, one node in each of the
  transform, clip and effect trees.
- `bounds` and `drawable_bounds`, "in the coordinate space of the containing
  transform node".
- `rect_known_to_be_opaque`; `raster_effect_outset` ("Some raster effects can
  exceed |bounds| in the rasterization space");
  `text_known_to_be_on_opaque_background`; `has_text`;
  `background_color` ("Color to use for checkerboarding");
  `hit_test_data`; `effectively_invisible`.

So Blink's chunk already carries Snowghost's 6.3 facts: identity, bounds,
opaque area, effect outset, and the text-on-opaque fact that decides
subpixel text. It carries no content hash, because it never leaves the
process: the `RasterInvalidator` matches chunks by id and compares display
items [E, README].

**Property trees** [E, README]. Four trees.
- A transform node has a 4×4 matrix, an origin, a flattening flag and a
  rendering context id.
- A clip node is "a float rect with (optionally) rounded corner radius", an
  optional clip path, and its transform node.
- An effect node has opacity, blend mode, filter and mask, an output clip
  and a transform node. "One can imagine each effect node as corresponding
  roughly to a bitmap that is drawn before being composited into another
  bitmap".
- A scroll node gives the scrollable directions, the transform node holding
  the offset, and the extent: "the scroll offset is stored as a 2d transform
  in the transform tree".

cc's nodes add the animation facts the compositor needs [E,
`cc/trees/transform_node.h`, `effect_node.h`]:
- `has_potential_animation`, `is_currently_animating`,
  `to_screen_is_potentially_animated`;
- on effects, `has_potential_opacity_animation` and the filter and
  backdrop-filter variants;
- `backdrop_filters`, `blend_mode`, `may_have_backdrop_effect`,
  `lcd_text_disallowed_by_backdrop_filter`;
- and `will_change_transform`, a hint.

**What changed over time** [E, chromium.org/blink/slimming-paint]:
- display items (M45);
- property trees in Blink (M58);
- paint chunks used for raster invalidation (M67);
- "sends a layer list instead of a tree, and generates final property trees
  in blink instead of re-generating them in cc" (M75);
- "compositing decisions made after paint" (CompositeAfterPaint, M94).

The direction is Snowghost's: move layer decisions after paint, and make
paint output plus property trees the interface. Layerization stayed a
heuristic. `PaintArtifactCompositor` "has to make tradeoffs between GPU
memory and reducing the costs when things change", merging chunks unless
"a direct compositing reason", overlap ("overlap testing") or "sparsity"
forbids it [E, README]. That is the policy Q65 moves into the shell.

**Cost on a no-op frame.** The new artifact is built by copying cached
items into a new vector, and raster invalidation walks all chunks [E,
README: "UseCachedSubsequenceIfPossible", chunk-by-chunk matching]. This
O(items) floor exists because paint output is a flat list rebuilt each
cycle. A delta contract avoids it by construction.

### 2.2 Chromium: renderer to viz

**Today's path: whole frames.** `CompositorFrameSink.SubmitCompositorFrame(local_surface_id, CompositorFrame, HitTestRegionList?, submit_time)` [E, `compositor_frame_sink.mojom`].
- A `CompositorFrame` has `metadata`, `resource_list` and
  `render_pass_list`, "in the order that each CompositorRenderPass will be
  drawn. The last one is the root" [E, `compositor_frame.h`].
- A pass has `output_rect`, `damage_rect`, `transform_to_root_target`,
  `has_transparent_background`, `cache_render_pass` ("we might reuse the
  texture if there is no damage") and `filters` and `backdrop_filters`
  [E, `render_pass_internal.h`, `compositor_render_pass.h`].
- Its quads are stored "front-to-back", each with a `SharedQuadState` [E].
- Damage is a rectangle per pass, with `has_per_quad_damage` as a later
  refinement [E].

Viz's acknowledgement protocol [E, mojom]:
- "For successful swaps, the implementation must call
  DidReceiveCompositorFrameAck() asynchronously ... in order to unthrottle
  the next frame". That ack returns `array<ReturnedResource>`, and
  `ReclaimResources` returns more later.
- Resource ids are therefore freed by an explicit return message, not by
  the sender's timeout: the pattern Snowghost's id freeing needs.

Message size is a known problem. The submit method carries
`[EstimateSize, UnlimitedSize]` with "TODO(crbug.com/40154480): Investigate
whether it's possible to alter the CompositorFrame structure to be less
likely to exceed soft message size limits" [E]. No byte figures were found;
the precedent is qualitative.

**The newer path: deltas.** `LayerContext.UpdateDisplayTree(LayerTreeUpdate)`
[E, `layer_context.mojom`]. Binding a `LayerContext` puts the sink in a
mode where "frames will automatically be submitted by Viz based on the
state of a GPU-side layer tree" [E, frame sink mojom]. The update carries:
- `layers`: "Properties of layers added or modified since the last update.
  Note that the ordering of this array is arbitrary";
- `layer_order`: "The full list of layer IDs in the tree, in layer-list
  order. If null, the layer list has not changed";
- `transform_nodes`, `clip_nodes`, `effect_nodes`, `scroll_nodes`: "Nodes
  added or modified on any property tree since the last update", with
  `num_*_nodes` giving "The total number of nodes in each property tree"
  [E]. That removal works by truncating to that count is my reading [I];
- `tilings` (rastered tile resources), `animation_timelines` and
  `removed_animation_timelines`, `ui_resource_requests` (create or delete);
- `frame_has_damage`: "Viz should make sure its damage calculations
  matches it. This is used to enforce checks in Viz to make sure it is in
  sync with Renderer's behavior".

Layer ids are client-chosen: "guaranteed to be (a) unique across all layers
currently in the tree and (b) consistent for the lifetime of each layer.
When a LayerTreeUpdate contains a Layer with a previously unseen ID, the
Layer is being added" [E, `layer.mojom`]. Layers also carry an optional
stable `element_id` that identifies "a client-side object which can be
represented by multiple layers over time".

Animations cross as data [E, `animation.mojom`]. An
`AnimationKeyframeModel` has an id, a group id, a target property, an
element id, a timing function (cubic Bézier, steps or a linear point list),
keyframes (a value plus a start time plus optional easing), a duration,
direction, fill mode, playback rate, iterations, start delay and hold time.
"Models for paint worklets and custom CSS properties are not pushed to
Viz."

Status: `cc/base/features.cc` declares
`BASE_FEATURE(kTreesInViz, base::FEATURE_DISABLED_BY_DEFAULT)` [E]. The
tracking bug is "JellyMander Phase 1a (TreesInViz)"
(https://issues.chromium.org/issues/369883417, seen as a search result).
That it ships to users is not claimed.

**What this teaches.**
- The delta form: changed records by id, the order list only when it
  changed, tree sizes for removal.
- A self-check flag that lets the receiver verify the sender
  (`frame_has_damage`).
- Animations as keyframe data.

Raster is still the renderer's, through out-of-process raster in the GPU
process [R], so viz receives pixels (tiles), not display lists. Snowghost
inverts this: the shell rasterizes, so the contract must carry drawable
content.

**Text across Chromium's boundary.** Skia's `SkStrikeServer` and
`SkStrikeClient` [E, `include/private/chromium/SkChromeRemoteGlyphCache.h`
in skia.googlesource.com]:
- "Serializes the strike data captured using a canvas returned by
  ::makeAnalysisCanvas";
- the client "Deserializes the strike data from a SkStrikeServer. All
  messages generated from a server when serializing the ops must be
  deserialized before the op is rasterized";
- "re-write the Rec mapping the typefaceID from the renderer to the
  corresponding typefaceID on the GPU";
- discardable handles pin and free entries across the boundary.

That the strike data holds glyph images, paths and metrics, so the GPU
process never parses the font, is [R]. The trust direction is the same as
Snowghost's: fonts are parsed where page content is parsed.

### 2.3 WebRender with Gecko and Servo

**Transactions** [E, `webrender/src/render_api.rs`]. "A Transaction is a
group of commands to apply atomically to a document", so that "no other
message can be interleaved between two commands that need to be applied
together".
- It holds `scene_ops` ("applied before scene building"), `frame_ops`
  ("applied after scene building"), `resource_updates` and notifications.
- `skip_scene_builder()` is "useful to avoid jank in transaction associated
  with animated property updates, panning and zooming", with the warning
  that such transactions "can race ahead of transactions that don't skip
  it".
- `set_display_list(epoch, namespace, (pipeline_id, BuiltDisplayList))`:
  the epoch is "The unique Frame ID, monotonically increasing"; "Scrolling
  doesn't require an own Frame".
- `update_epoch` pushes the epoch into both queues, because "We track
  epochs before and after scene building".
- The renderer reports back which epoch of each pipeline is on screen:
  `Renderer::flush_pipeline_info() -> PipelineInfo { epochs, removed_pipelines }`
  [E, `webrender/src/renderer/mod.rs`].

Gecko's display-list throttling on unacknowledged transactions is [R].

**Resources** [E, `render_api.rs`].
- `ResourceUpdate` covers `AddImage`, `UpdateImage`, `DeleteImage`, blob
  images (Gecko-recorded drawing that WebRender rasterizes),
  `AddFont(Raw(FontKey, bytes, index) | Native(handle))`, `DeleteFont`,
  `AddFontInstance { key, font_key, glyph_size, options, platform_options, variations }`
  and `DeleteFontInstance`.
- Fonts cross as whole font files, and the receiving process parses them.
- `ImageData` is `Raw(Arc<Vec<u8>>)` or `External(ExternalImageData)`,
  where the embedder owns the buffer or texture [E, `image.rs`].
- Over Gecko's IPC, bytes go through `ShmSegmentsWriter`, which "pushes
  bytes in a sequence of fixed size shmems for small allocations and
  creates dedicated shmems for large allocations". The chunk size
  "64k - 2 * 4k - 16 = 57328 bytes" is chosen because "Each shmem has two
  guard pages, and the minimum shmem size (at least one Windows) is 64k"
  [E, `gfx/layers/wr/IpcResourceUpdateQueue.h`].

**The display list** [E, `webrender_api/src/display_list.rs`, `display_item.rs`].
- A `BuiltDisplayList` has a `DisplayListPayload { items_data, spatial_tree, interner_delta }`;
  the first two are peek-poke-serialized byte buffers.
- Items share `CommonItemProperties { clip_rect, clip_chain_id, spatial_id, flags }`.
- Spatial tree items are `ScrollFrame`, `ReferenceFrame` and `StickyFrame`.
  - `ScrollFrameDescriptor` carries `content_rect`, `frame_rect`,
    `external_id`, `external_scroll_offset` ("The amount this scrollframe
    has already been scrolled by, in the caller"), a
    `scroll_offset_generation` and `has_scroll_linked_effect`.
  - `StickyFrameDescriptor` carries margins and vertical and horizontal
    offset bounds, so the compositor computes sticky offsets itself.
- Text is `TextDisplayItem { common, bounds, font_key: FontInstanceKey, color, glyph_options, shadow }`
  followed by `Vec<GlyphInstance { index: u32, point: LayoutPoint }>` [E,
  `font.rs`]: absolute glyph positions, 12 bytes per glyph before
  serialization overhead.
- Animated values are `PropertyBinding<T> = Value(T) | Binding(key, T)`
  [E, `lib.rs`]; frame ops `AppendDynamicProperties` and
  `SetScrollOffsets` update them without a new display list [E].
  Rectangles take `PropertyBinding<ColorF>`, so colour can animate without
  repaint.

**What failed or was revised.**
- **Whole display lists.** Gecko resends whole lists, so WebRender interns
  primitives on its side and diffs per frame to learn what changed
  (`notes/webrender.md` §3.3 [E there]).
- **Interning moving to the sender**, 2026-09-21, bug 2073976 [E,
  `webrender_api/src/interning.rs`, Bugzilla, hg log]:
  - "An item that survives into the next display list ... keeps the same
    handle and its data is not re-transmitted at all".
  - A handle is "a slot index plus the build in which the item was first
    interned".
  - "The receiver is a pure follower and never talks back. Because it only
    ever follows, the deltas form a strict sequence - every one has to be
    delivered, in order, or the two sides are out of step for good."
  - An entry is collected after `RETAIN_BUILDS` (10) builds absent "so that
    content flickering an item in and out does not re-send it". The
    receiver applies a remove "only together with the scene built from the
    list that no longer references the entry".
  - A builder id exists so that "a second builder silently collides with the
    first" becomes "a detectable error rather than corruption".
  - Status: "Nothing is interned yet: the machinery lands first", so this
    is in progress, not shipped behaviour.
  - This is the closest precedent for Snowghost's design: stable handles,
    an ordered delta stream, a build stamp to detect desynchronization.
- **The display item cache is gone.** `webrender_api/src/display_item_cache.rs`
  is absent at mozilla-central tip ("not found in manifest"); its last
  recorded change is dated 2024-11-18, and an earlier one in 2021 is
  "Bug 1724344 - Split DL cache data into separate payload vec" [E, hg
  json-log]. It was a cache keyed by item key that let Gecko reuse display
  items across lists without resending them [R]. The removal commit was not
  found. Together with the 2026 interner, this says reuse across lists was
  tried once, removed, and is being rebuilt as stable handles [I].
- **Picture caching** was added because full redraw cost power and
  bandwidth; it is a shell policy in Snowghost's terms (`notes/webrender.md`).
- **Scroll offsets baked into item coordinates** (Gecko's
  `external_scroll_offset`) made coordinates drift unless they lie on the
  grid: "a non-zero value here means some of this list's positions will
  drift with the scroll offset ... See bug 2059570" [E, `display_list.rs`
  descriptor]. Lesson: content must not encode the scroll offset; the
  offset lives only in a node.

**Servo** [E, `components/shared/paint/lib.rs` and `display_list.rs` in
servo/servo].
- Layout builds a WebRender display list, and `send_display_list` sends
  the descriptor on the control channel and the payload (`items_data`,
  `spatial_tree`) plus a `PaintDisplayListInfo` on separate channels.
- That info is a scroll tree with `external_id`, `content_rect`,
  `clip_rect`, `scroll_sensitivity`, `touch_action` and `offset`, used by
  the compositor for scrolling and hit testing.
- The split exists because the info, "a large data structure that scales
  with the size of the display list", was serialized on the compositor's
  IPC channel and filled the socket buffer. That caused a three-thread
  deadlock: compositor waiting on a hit test, render backend blocked on
  the full socket, script blocked sending [E, servo/servo PR 36484,
  read through a page summary].
- Lesson: bulk data and control messages must not share a bounded channel
  that either side blocks on.

### 2.4 Flutter

- **`DisplayList`** is "a persistent sequence of rendering operations". It
  exposes `bytes()`, `op_count()`, `unique_id()`, `GetBounds()`, an
  optional `rtree()` and `Equals()`. It also reports facts the compositor
  uses to pick surfaces: `can_apply_group_opacity`,
  `root_has_backdrop_filter`, `root_is_unbounded`, the maximum blend mode,
  and `modifies_transparent_black` [E, `display_list/display_list.h`].
  These are facts derived from content, computed once by the producer.
- **Identity and change.** `Layer::IsReplacing` matches an old layer by
  `original_layer_id_` [E, `flow/layers/layer.h`].
  `DisplayListLayer::Compare` tries pointer equality first, then `op_count`,
  `bytes` and bounds. It gives up above `kMaxBytesToCompare`
  ("PictureTooComplexToCompare") and only then deep-compares [E,
  `flow/layers/display_list_layer.cc`]. Without a stable id plus a content
  hash, large pictures are assumed changed.
- **Damage.** `DiffContext` computes frame damage and buffer damage,
  mirroring `EGL_KHR_partial_update`'s surface and buffer damage. A
  *readback region* rule says "if any part of the readback region needs to
  be repainted, then the whole readback region must be repainted"; that is
  the backdrop-reader widening, done at diff time [E, `flow/diff_context.h`].
- **Raster cache**, revised. Flutter #88832 says opacity layers are always
  cached, other items are cached only after being seen for some frames,
  and it uses "an acknowledged bad measure for whether a picture is complex
  enough" [E, issue page summary]. Under Impeller the cache is compiled
  out: `raster_cache.h` is wrapped in `#if !SLIMPELLER` [E]. An issue
  author states that "Impeller does not currently support raster cache,
  meaning every frame is fully redrawn" [E secondary, flutter#166184].
  Lesson: cache heuristics placed in the producer's layer structure were
  revisited. Snowghost keeps them out of the contract.
- The layer tree goes from UI thread to raster thread in one process
  through a bounded pipeline [R].

### 2.5 Fuchsia Scenic: Gfx to Flatland

- **The revision.** Gfx was a 3D scene graph in which "Drawing order is
  handled by Z depth and opacity is handled via alpha blending based on
  depth (features like group opacity are impossible)". It frustrated
  display-controller planes [E, fuchsia.dev 2021 roadmap "Flatland"].
  Flatland lets clients "only submit 2D layers that are scaled and offset
  in X/Y" [E]. The clients (Flutter, Chromium) rasterize their own content
  into images.
- **Protocol** [E, `sdk/fidl/fuchsia.ui.composition/flatland.fidl`]:
  - `TransformId` and `ContentId` are client-chosen `uint64`; zero is
    invalid.
  - Ops are feed-forward and `Present` executes them all. "If executing an
    operation produces an error ... Operations that produce errors are
    ignored and the channel is closed."
  - "The client may only call Present when they have a non-zero number of
    present credits"; `OnNextFrameBegin` returns credits and
    `OnFramePresented` reports display.
  - `release_fences` are signalled "when it is safe to reuse resources
    which no longer appear in the local scene graph at the time of the
    current Present".
  - "Once released, the id immediately goes out of scope for future
    function calls and can be reused", while the object lives "as long as
    they are children of either an unreleased Transform, or the Root".
  - Children render "back-to-front ... in the order the children were
    added".
- **Lessons.**
  - Atomic commit at an explicit boundary.
  - Credit-based backpressure.
  - Id release separate from object lifetime.
  - Fail closed on a protocol violation.
  - Flatland carries no vector content at all, so it is a precedent for the
    protocol, not for the content format.

### 2.6 Android hwui

- Each `RenderNode` holds `mStagingProperties` and `mStagingDisplayList`
  written by the UI thread, pushed by `pushStagingPropertiesChanges` and
  `pushStagingDisplayListChanges` during sync [E, `RenderNode.h`].
- `DrawFrameTask` is "the sync-state task": the UI thread calls
  `postAndWait()` and is unblocked after `syncFrameState`, or after the
  draw when the sync cannot unblock it early [E, `DrawFrameTask.h/.cpp`].
- Properties include `LayerType` and `hasOverlappingRendering`, the latter
  an app-declared fact that lets the renderer skip an offscreen for alpha
  [E, `RenderProperties.h`].
- `RenderNodeAnimator` runs property animations on the render thread [R].
- Lesson: double-buffered per-node staging gives atomic frames at the cost
  of a blocking sync. Snowghost's processes cannot block on each other, so
  the staging is the delta itself.

### 2.7 Text and resources across the precedents

| system | text crosses as | font data goes to | images |
|---|---|---|---|
| Chromium (viz) | already rastered tiles; glyph strikes from renderer to GPU process (Skia remote glyph cache) | stays with the renderer; strikes cross [E header; contents R] | transferable resources (GPU-backed) [E] |
| WebRender | glyph runs: font instance key + `(u32 index, point)` per glyph [E] | whole font file (`AddFont::Raw`) or native handle; the receiver parses it [E] | raw bytes or external buffer, by key [E] |
| Flutter | glyph runs inside display lists [R] | same process | same process |
| Flatland | client-rastered images | n/a | sysmem buffers through an allocator [E docs] |
| Snowghost (fixed) | the renderer shapes; the shell rasterizes [SG] | the renderer validates fonts; the shell owns system fonts [SG] | the renderer decodes [SG] |

Snowghost's position is new among these. The renderer has the parsed font
and the shell rasterizes. WebRender's answer (send the font file) would hand
untrusted font bytes to the shell's rasterizer, which
`design/processes.md` refuses ("instead of handing page content such as
images and fonts to the shell's libraries"). Skia's answer (send derived
glyph data) keeps parsing in the trusted-parse process, matching Snowghost's
direction [I].

---------------------------------------------------------------------------

## 3. What the contract has to settle

Each item states the fact, why the shell needs it, and the decision left
open. All of it is facts in Q65's sense.

### 3.1 Chunks: grain, identity, content

- **Grain.** `DESIGN.md` 2.1 says "a chunk per context and paint phase".
  With 85 to 95 percent of text in one context [SG], that chunk holds about
  1.9 to 2.1 million glyphs on html5 [I, assumption below], so a one-word
  edit republishes it whole. The memoized paint unit and the chunk must
  therefore be the paragraph for text, as the frame walkthrough already
  does (#103 is one paragraph). X1 measured the paragraph as the unit a word
  edit touches. Decorations (backgrounds, borders, shadows) can be per box
  or per context. **Open:** split one paragraph's chunk by line when a
  paragraph is very large? The run file's `largest` field is 8,983 on
  html5 [SG]. That it counts the scalars of the largest paragraph is my
  reading, supported by the synthetic one-paragraph page whose `largest`
  equals its 1,074,999 scalars [I].
- **Identity.**
  - A `ChunkId` is (stable unit key, generation).
  - The key comes from the paint unit's identity: element or paragraph
    identity plus phase. Its scheme is X2's question.
  - The generation guards slot reuse, as Blink's `client_is_just_created`
    and WebRender's "build first interned" stamp do [E].
  - Equal key means the same unit; a new generation means a new object
    under a reused slot.
- **Immutability.** A chunk record is never edited. A change publishes a
  new record under the same id ("put"), which replaces the old one at that
  epoch.
- **Hash.** With deltas, a put is the change signal, so the hash is not
  needed to find changes (Blink and WebRender need theirs because they
  resend or diff). It still serves:
  - the shell's cache key for 7.6's "content unchanged";
  - de-duplication if equal content recurs (WebRender's interner);
  - the replay oracle (§6).

  Keep it as 64 bits of a specified hash over the record's bytes, so the
  shell can recompute it in a debug mode.
- **Content.**
  - Items in the chunk's local coordinates, with no position of the chunk
    itself (Q55).
  - The item kinds the walkthrough lists: Rect, RoundedRect, Border,
    BoxShadow, Image, GlyphRun, plus gradients, lines and decorations, and
    an external-surface reference.
  - Items reference interned style values (colours and gradients) by value,
    not by id, unless X-sizes say otherwise.
- **Per-chunk facts**, each a claim the reference rasterizer can verify:
  - `ink_bounds`: local rect including shadow blur and outline outsets;
  - `opaque_rect`: a subset of the chunk's pixels proven fully opaque, or
    empty. Blink keeps one rect [E];
  - `hit`: pointer-events, cursor class and touch-action (§3.6).

### 3.2 Placement apart from content

- A chunk's position is (property-tree node, offset within that node's
  space) and lives in a **placement table**, so a shift of later content
  rewrites placements (about 12 to 16 bytes each), never chunk records.
- X3 decides the structure:
  - context-relative offsets, as Q55: a context is a transform-like node
    and chunks are placed in it;
  - or a summary tree or prefix sums, where the contract carries flow
    sizes and the shell sums (`notes/raster.md` D2).
- X3's p90 numbers for sentence edits on html5 (1,287 context roots,
  against 5 to 819 times fewer for a summary tree) are the evidence. The
  contract can carry either form; the choice changes the placement table's
  shape, not the chunk format.

### 3.3 Property trees

Nodes carry renderer-allocated ids and a parent id.
- **Transform**: a 2D affine matrix, a 4×4 only when 3D is present,
  origin, and a flattening flag where 3D exists. Context offsets (Q55) are
  translations here or in the placement table (3.2).
- **Scroll**: container clip rect, content size, scrollable axes, the
  scroll-linked-effect fact, and the transform node that holds the offset.
  The offset is in the node, never baked into content (WebRender bug
  2059570 [E]).
- **Sticky**: constraints as in WebRender's `StickyFrameDescriptor`
  (margins plus offset bounds) [E], so the shell computes sticky offsets
  per scroll frame without the renderer.
- **Clip**: a rect with radii, or a path or mask reference, plus its
  transform node.
- **Effect**: opacity, blend mode, filter list, backdrop filter,
  mask or clip-path, output clip, and transform node.
  - Effect *values* are interned descriptors referenced by id, so
    ecma262's 33,422 `mix-blend-mode: multiply` users are 33,422 small
    nodes pointing at one descriptor, not 33,422 copies of a filter list
    [SG census; I].
  - Whether a node reads its backdrop follows from its descriptor (blend
    mode not normal, or a backdrop filter), so it is derived, not sent.

### 3.4 Order

- One order list per stacking context: a sequence of entries, each a chunk
  id or a child stacking context (an effect or isolation group).
- **Send form.** Chromium's `LayerContext` resends the whole order list
  when it changes [E]. That is fine at Chromium's 13 to 228 layers [SG]
  and not at Snowghost's chunk counts: the dominant context's list has
  tens of thousands of entries [I].
- So the op is a splice:
  `Splice { list, after: ChunkId | Head, remove: n, insert: [ChunkId] }`.
- Order across stacking contexts follows CSS 2.2 Appendix E; the
  renderer computes it, and the shell never reorders.

### 3.5 Scroll roots and what moves with them

- The 6.3 row "per scroll root, the content that moves rigidly with it" is
  **derivable**: a chunk moves rigidly with scroll node S when the
  transform chain from its node to S contains no other scroll, sticky or
  animated node.
- Fixed content hangs from the viewport root; sticky content from a sticky
  node. The shell derives the strip membership of 7.5 from the trees, so
  the contract need not send it.

### 3.6 Facts missing from the Q65 table

- **Scroll offset with two writers.** The shell scrolls (compositor
  scrolling); script also writes `scrollTop` and reads it back.
  - Precedents: WebRender's `external_scroll_offset` plus
    `scroll_offset_generation` [E], and cc's split of base and active
    offsets [R].
  - Proposal: the shell owns the current offset and reports
    `(node, offset, applied_generation)` back over the channel. A script
    write is a transaction op `ScrollTo { node, offset, generation }`.
  - The shell applies a write only if its generation is newer than the last
    it applied, and the renderer's layout reads the reported offset as an
    input.
- **Hit testing and scroll routing.** To route a wheel or touch scroll
  without a round trip, the shell needs per chunk or per node:
  pointer-events, touch-action, and "an input handler here may cancel
  scrolling" (passive or blocking listeners).
  - Precedents: Chromium's `HitTestRegionList` on every submit [E],
    `PaintChunk::hit_test_data` [E], and Servo's scroll tree with
    `touch_action` and `scroll_sensitivity` [E].
- **Accessibility.** The shell owns accessibility [SG], so an
  accessibility tree must cross too. It is not part of the paint contract,
  but it shares the transport and the id scheme. Flag only.

### 3.7 Animations

- A description per running animation, shaped like viz's
  `AnimationKeyframeModel` [E]: id, target node, property, keyframes
  (offset, value, easing), default easing (cubic Bézier, steps, linear
  points), duration, delay, iterations, iteration start, direction, fill,
  playback rate, and hold time when paused.
- **Start time.** It must be a fact both sides agree on. The shell reports
  the actual start instant back, because script reads `currentTime` [R
  for cc's round trip; I for Snowghost].
- **Colour animations.** The census's paint animations (walmart 81) can stay
  renderer-driven at first. WebRender's `PropertyBinding<ColorF>` [E] shows
  how a colour can animate in the shell later without changing chunk
  content: an item's colour bound to an animation id is a fact.
- **Caret blink** is a steps animation on an opacity node, so a blinking
  caret costs the renderer nothing [I].

### 3.8 Resources

- **Images.** `ImageId -> { width, height, format, alpha: premultiplied | straight, color space, bytes }`,
  decoded by the renderer [SG].
  - Large decoded images are big: 4000×3000 RGBA8 is 48 MB [I].
  - **Open:** decode at intrinsic size, or at a size bounded by its
    largest use? Choosing a decode size from the display is closer to
    policy; a size from the page's own use is a fact.
  - Animated images: frames as image updates driven by the renderer at
    first.
- **Fonts** are the hard one (2.7). Three forms:
  - **(f1) Validated font bytes.** The shell's rasterizer parses them.
    This matches Chromium's FreeType hinting most easily, but it hands
    page fonts to an unproved parser, which `processes.md` refuses.
  - **(f2) Glyph outlines per (face, glyph id).** Contours in font units
    plus advance, sent on first use in a run. These are plain values and
    resolution-independent, so the shell rasterizes at any scale. TrueType
    bytecode hinting is lost, but Chromium on Linux uses slight hinting
    [R], which only adjusts vertical positions.
  - **(f3) Glyph masks per (face, glyph, size, subpixel bucket).**
    Skia's remote-strike approach. It needs the device scale and the
    shell's antialiasing mode, which edges into shell rasterization.

  System fonts are the shell's own files [SG]. The renderer still needs
  their tables to shape, so their bytes come to the renderer over the
  channel, and the shell can rasterize them from its own copy.
  **Open:** (f2) with or without the renderer applying slight hinting. Its
  criterion is in §7.
- **Lifetimes.** Resources are separate from chunks: put, retain while
  referenced, release with an epoch, freed after acknowledgement. This
  follows viz's returned resources and Flatland's release fences [E].

### 3.9 External surfaces

- A `SurfaceRef { surface id, rect, opaque }` item. The frames come from a
  producer outside the scene contract.
- **Open:** video decoding is not placed by `processes.md`. A video frame
  stream needs its own buffer and fence protocol, not the delta stream
  (WebRender's video-in-tiles waste, `notes/webrender.md` 2.4).

### 3.10 Completeness and progress

- A transaction may carry
  `Painted { region: rect in the root scroll space, complete: bool }`: the
  part of the page whose chunks are all published.
- The shell never shows a frame claiming content outside that region is
  final. Whether it shows a background there or waits is its policy.
- This keeps whole-page and viewport-first paint inside one contract (X9).

### 3.11 What is not sent

- Glyph counts, blur radii and path complexity are in the chunk.
- "Content or geometry changed": a put versus a placement or node op.
- Strip membership: 3.5.
- Backdrop reads: from the effect descriptor.

Sending them would create a second source of truth that can disagree with
the first, which the contract would then need a rule for. This follows
`AGENTS.md`'s "state each normative fact once" applied to data [I]. The
exception is a fact that is expensive or impossible for the shell to derive
and cheap for the renderer: `opaque_rect` and `ink_bounds` (both verified,
§6).

---------------------------------------------------------------------------

## 4. Sizes [I]

**Assumptions.**
- One scalar in six is a space; spaces emit no glyph, as the walkthrough
  states for its runs. So html5's 2,645,960 scalars give about 2.2 million
  glyphs.
- Chunks are per paragraph plus one decoration chunk per context: 32,684 +
  11,794, about 44,500.
- Chunk header 48 bytes (walkthrough); placement record 16 bytes; order
  entry 8 bytes; property node 32 bytes per context.

**Glyph encodings.**

| encoding | bytes per glyph | html5 text |
|---|---:|---:|
| (id u16, x f32, y f32): walkthrough | 10 | 22 MB |
| per-line run, y once; (id u16, x f32) | 6 | 13 MB |
| per-line run; (id u16, advance i16 in 1/64 px) | 4 | 9 MB |
| WebRender `GlyphInstance` (u32, f32, f32) | 12 | 26 MB |

The 4-byte form is exact only if layout's glyph positions are fixed-point at
1/64 px, which is a layout representation choice (open).

**First frame, html5 (117,179 elements).**
- Chunk headers: 44,500 × 48 B = 2.1 MB.
- Decoration items: about 1 to 2 MB, assuming a fifth of the 117,165 boxes
  draw a background or border at 40 to 80 B.
- Placement: 0.7 MB. Order entries: 0.4 MB. Property nodes: 0.4 MB.
- Text: 9 to 22 MB.
- **Total: about 13 to 27 MB**, plus fonts (outlines for a few hundred
  glyphs per face: tens of KB) and images.
- Three viewports of 720 px are 2,160 / 1,283,308 = 0.17 percent of the
  page: **about 25 to 45 KB**.
- X9's criterion ("viewport-dependent paint is adopted only if the
  whole-page list exceeds the shared-memory budget or delays the first frame
  by more than one frame on ecma262") is about this gap. Moving 20 MB costs
  about 2 ms at 10 GB/s; producing it is the real cost, and X9 measures
  that.

**One-word edit**, inside one paragraph whose height stays the same:
- one chunk put of about 68 glyphs × 10 B + 48 B = **about 0.7 KB**, as the
  walkthrough found 700 B for a 55-glyph paragraph;
- plus a transaction header (tens of bytes).

**One-word edit that adds a line**, with context-relative placement:
- the chunk plus the moved roots (html5 `text+word` p90 4, max 34;
  apollo11 p90 34, max 59 [SG]): **under 2 KB**.

**Sentence insert** (html5 `text+sentence`, context-relative): p90 1,287
moved roots × 16 B, about 20 KB. With a summary tree, X3's ratios make it a
few hundred bytes.

**Under 2.1's grain** (chunk per context and phase), the same one-word edit
republishes 85 to 95 percent of the text: **about 8 to 21 MB**. This is the
reason for 3.1.

**Precedent sizes.** No primary byte counts for viz frames, WebRender lists
or Flatland updates were found. Chromium's `[UnlimitedSize]` TODO and
Servo's deadlock are qualitative evidence that bulk paint data strains IPC
channels [E].

---------------------------------------------------------------------------

## 5. Three candidate contracts

All three share §3's records and the id scheme:
- Ids are allocated by the renderer: chunk, node, order list, resource,
  animation and surface, each (slot u32, generation u32).
- A freed slot is reusable only after the shell acknowledges the epoch that
  retired it (Flatland releases ids immediately but keeps objects alive
  [E]; Snowghost keeps both until acknowledged, which is simpler to check).

They differ in where bytes live, how the shell learns of changes, and what
an acknowledgement frees.

### A. Retained arena plus epoch journal

**Shape.**
- The renderer appends immutable records (chunks, resources, node tables)
  to a shared **arena** it alone writes. It also appends a **journal**
  entry per epoch: ops that point at arena offsets (`Put chunk id @off`,
  `Retire id`, `SetNode`, `SetPlacement`, `Splice`, `Painted`,
  `Animation`).
- Commit: write the records and journal entry, then a header word
  `{epoch, journal end}` with a release store.
- The shell keeps tables id → arena offset and reads payloads in place.
- The shell acknowledges the applied epoch over the channel, and the
  renderer frees records retired at or before it.

**The renderer must** keep an arena allocator with per-epoch retire lists,
compact a fragmented arena by re-putting live records, and hold at most K
unacknowledged epochs, coalescing later changes into one pending delta.

**The shell per frame** reads new journal entries, applies them to its id
tables in O(ops), uploads changed payloads to the GPU, and acknowledges.

**Sizes.** One-word edit: about 0.7 KB of payload plus about 40 B of journal.
First frame: 13 to 27 MB of arena plus about 1 MB of journal.

**Strengths.**
- Zero copy of payloads.
- After a shell restart or GPU loss, the shell rebuilds from the arena
  without the renderer, if the renderer also keeps a live directory record.

**Failure modes.**
- **Reuse before acknowledgement**: torn reads in the shell.
- **Time-of-check to time-of-use**: the shell validates bytes that stay in
  writable shared memory. A renderer bug can change them after validation,
  so every read must be safe on garbage.
- **Arena exhaustion** stalls the renderer, and compaction costs a large
  republish.
- **Lost journal entries**: the shell must detect them by epoch gaps,
  WebRender's "out of step for good" [E].

**Whitefoot.**
- Needs a shared-memory host module, with release-store publication of the
  header word.
- By HOST-1, the payload writes and the publication must reach one region
  owner to be ordered [I]. Overlapped paint iterations writing straight into
  the region would each touch that owner and lose their independence.
  So paint builds records as Whitefoot values, and one host call copies
  them into the arena.
- "Never written after publication" is a disjoint-write property on index
  ranges past the watermark, which Whitefoot can prove inside the renderer.
  The shell's concurrent read is outside Whitefoot's model.

### B. Transactions copied into a shell-owned scene (recommended)

**Shape.**
- A single-producer, single-consumer **ring of transactions**. Each
  transaction is `{ epoch, flags (urgent, painted), ops[] }` with payloads
  inline: chunk records, node records, splices, animation descriptions.
- The shell copies each transaction into its own scene on apply, at a
  transaction boundary, never mid-transaction (WebRender's and Flatland's
  atomicity [E]).
- Ring space is reclaimed when the shell advances its read index; that
  index is the acknowledgement.
- **Large, long-lived resources** (image pixels, font outlines and surface
  buffers) go in **separate blobs**:
  - a transaction references them by id;
  - the shell returns `Released(id)` once it holds its own copy or the
    reference is gone, as viz's `ReturnedResource` and Flatland's release
    fences do [E].
- Credits: at most K transactions in flight. Beyond that, the renderer
  coalesces: a later put supersedes an earlier one of the same id, and
  node sets and splices merge.

**The renderer must** keep its id allocator and the set of live ids (to know
what to retire), not encoded payloads. On request it republishes everything
from its memoized paint results (a reset transaction followed by puts).

**The shell per frame** copies and validates each transaction in
O(transaction bytes), applies it to its scene and spatial index, and uploads
changed instances.

**Sizes.** The same as A on the wire. Memory: the shell holds its own copy
of the scene, about 13 to 27 MB for html5, plus GPU buffers [I].

**Strengths.**
- **Transport-independent semantics.** The same transactions run over a
  pipe (`std::io::write_once` exists today [SG]), a socket or a
  shared-memory ring.
- Copying before validation removes A's time-of-check problem.
- Reclamation is a read index plus resource releases.
- Atomic apply is natural: decode the whole transaction, then swap.

**Failure modes.**
- **Shell restart** loses the scene, and the renderer must republish in
  full: about a first frame's cost.
- **A large first frame through a ring** needs either a ring as large as
  the frame or several transactions with `Painted.complete = false` until
  the last, which is the progressive path anyway.
- **One stream for control and bulk** can deadlock, as Servo's did [E].
  - Acknowledgements and input go on the separate channel.
  - Neither side blocks on a full buffer while the other waits for it: the
    renderer blocks only on credits, and the shell never blocks on the
    renderer.

**Whitefoot.**
- Over a pipe it works today; over a ring it needs the same host module as
  A, but only for a byte ring with head and tail words.
- Payloads are built as values, and one host call per transaction writes
  them (a single owner, so ordered by HOST-1 [I]).

### C. Versioned snapshot with structural sharing

**Shape.**
- Each epoch the renderer publishes a **root**: persistent trees (fan-out
  about 16) for the chunk table, the placement table, each order list and
  the node tables, in a renderer-written region.
- Unchanged subtrees are shared by offset with the previous root (path
  copying).
- The shell walks the new root against the old, skipping any subtree whose
  offset is unchanged. Flutter's first test is pointer equality [E]; here
  it is offset equality.
- Old roots are reclaimed when the shell acknowledges it no longer holds
  them.

**The renderer must**
- path-copy: with 44,500 chunks and fan-out 16, depth is 4, so about four
  256-byte nodes per changed chunk;
- reclaim nodes no root reaches, which needs reference counts or a tracing
  pass over the regions.

**The shell per frame** runs the diff in O(changed × depth), reads payloads
in place, and acknowledges roots.

**Sizes.** One-word edit: 0.7 KB plus about 1 KB of path copies. First
frame: as A plus about 3 to 6 percent for interior nodes [I].

**Strengths.**
- Every epoch is a complete value. A shell restart, the replay oracle and a
  scene dump are reads of a root.
- No journal can be lost, since the shell may skip roots (it can jump from
  epoch 5 to 9).

**Failure modes.**
- The reclamation of a shared persistent structure is the hardest part,
  and the same in-place time-of-check exposure as A.
- Order lists of tens of thousands of entries need a persistent sequence
  (a rope or B-tree), as 3.4's splice does in A and B.

**Whitefoot.** Persistent values are natural in Whitefoot. Offsets in
shared memory are plain data. Reclaiming across processes needs either a
tracing pass the renderer runs over its regions, or counts; the cost of
proving it is unknown [I]. It needs the shared-memory host module.

### Comparison

| | A arena + journal | B transactions (recommended) | C snapshots |
|---|---|---|---|
| renderer computes | records, journal, retire lists, compaction | records, live-id set, coalescing | records, path copies, reclamation |
| shell per frame | apply ops, read in place | copy, validate, apply | diff roots, read in place |
| one-word edit | ≈0.7 KB + 40 B | ≈0.7 KB + header | ≈0.7 KB + ≈1 KB |
| first frame (html5) | 13–27 MB in arena | 13–27 MB streamed; shell copy | 13–27 MB + ≈6 % |
| shell restart | rebuild from arena | full republish | read latest root |
| validation exposure | in place, time-of-check risk | copy then validate | in place, time-of-check risk |
| runs on today's Whitefoot | no (needs shared memory) | yes, over a pipe | no |
| Q65 replay oracle | replay the journal | replay the transactions | compare roots |

---------------------------------------------------------------------------

## 6. Checking "policy never changes the picture" (Q65, Q66)

1. **Contract replay.** After any history of edits, the scene the shell
   builds from the deltas equals the scene of one full publish of the final
   document. The comparison is by values in paint order, not ids, as
   `DESIGN.md` §8 requires of dumps. This catches lost or misordered
   deltas, stale placements and splices applied at the wrong anchor.
   Chromium's `frame_has_damage` self-check is a small precedent:
   "This is used to enforce checks in Viz to make sure it is in sync with
   Renderer's behavior" [E].
2. **Pixels at rest** (X14). A CPU reference rasterizer draws the full
   scene at epoch E. Every combination of the shell's policies must produce
   the same bytes at rest: damage-scissored redraw, age-tracked buffers,
   strips, cached subtrees, culling by opaque areas. Q66's exception is a
   cached texture during a scaling, rotating or fractional transform
   animation; the first frame after it ends must match. Each deliberate
   breakage must fail once.
3. **Fact soundness.** A policy that trusts a wrong fact changes pixels with
   no policy at fault. So the reference rasterizer checks each declared
   claim against the chunk drawn alone:
   - nothing drawn outside `ink_bounds`;
   - alpha 255 everywhere in `opaque_rect`;
   - an effect whose descriptor says it reads no backdrop passes this test:
     render the group alone onto transparent, then composite that result
     source-over onto backdrops A and B. Rendering the group directly over
     A and over B must give the same bytes as those two composites;
   - a `Painted` region contains every published chunk's placed bounds.

The contract rule that makes (3) possible: **every field is either drawn by
the reference redraw, or a claim about what that redraw draws, or a timing
fact the reference evaluates at time t (animations). No field is read only
by a policy.** A field that fails this test is a hint, and Q65 excludes
hints.

---------------------------------------------------------------------------

## 7. Recommendation and open questions

**Recommendation.** Contract B, with §3's records.
- Paragraph-grain chunks, immutable, without positions.
- Placement and order in their own tables, with splices for order.
- Interned effect descriptors.
- Renderer-allocated ids with generations, freed on acknowledgement.
- Resources as separately released blobs.
- Animations as keyframe data.
- The two missing facts (scroll-offset generation, hit-test and
  scroll-routing flags).
- A `Painted` region.

Begin over a pipe, which runs on today's Whitefoot. Move to a shared-memory
ring when Whitefoot gains a host module for it, without changing the
records. A is the fallback if the copy proves costly (Q-B below). C is
worth reopening only if shell restarts matter.

**Implications for recorded decisions (for the owner).**
- `design/processes.md` says the renderer sends its data "through shared
  memory". Starting over a pipe is a staging choice, not a change to the
  contract's records. It is still a material choice against that wording
  and needs the owner's ruling.
- The shared-memory transport depends on Whitefoot: [PRE-2]'s host modules
  are a closed list of six, so a shared-memory host module, with a
  release-ordered publish, is a Whitefoot specification change.
- `DESIGN.md` 2.1's "a chunk per context and paint phase" conflicts with
  the grain this contract needs (3.1). The paint stage's memo unit would
  follow the paragraph.
- 6.3's fact table gains two rows (3.6) and loses several sent rows to
  derivation (3.11).

**Open questions, each with the criterion an experiment would decide.**

| # | Question | Experiment | Criterion (fixed before running) |
|---|---|---|---|
| Q-grain | Paragraph chunks, or line chunks for large paragraphs? | Snowghost paint over X1's edit script on the three pages; record bytes per edit at both grains | Lines are added where the p99 one-word-edit transaction exceeds 4 KB at paragraph grain |
| Q-glyph | Glyph encoding: 10, 6 or 4 bytes per glyph | Encode html5 and ecma262 paint output in each form; decode in the shell | The smallest form whose shell decode costs under 1 ms per MB, and whose positions round-trip exactly through layout's representation |
| Q-place | Context-relative placement or summary tree in the contract | X3's data mapped to placement bytes per edit | Adopt the summary form if sentence-edit p90 bytes exceed 16 KB under context-relative placement (html5 is about 20 KB by §4, so this likely passes, to be checked on real output) |
| Q-B | Is copying into the shell (B) a measurable cost? | Time the shell's copy and validate against apply plus GPU upload, for the first frame and for edit streams | Keep B unless the copy exceeds 10 percent of apply-and-upload time for the first frame or 0.1 ms per edit transaction |
| Q-first | Whole page or progressive first frame (X9) | Paint html5 and ecma262 whole and viewport-first under B | X9's criterion as written: progressive is used if the whole list exceeds the transport budget or delays the first frame by more than one frame on ecma262 |
| Q-font | Glyph outlines (f2), with or without renderer-applied slight hinting, against font bytes (f1) | Rasterize the measured pages' text both ways and diff against the reference browser's pixels | f2 is adopted if its text pixels differ from the reference in no more glyphs than f1's; otherwise f2 plus renderer slight hinting is measured; f1 is out unless both fail |
| Q-order | Splice ops or whole-list replacement | Count order-list bytes on X1's insert-block and remove-block edits | Splices are needed if whole-list replacement exceeds 64 KB at p90 |
| Q-dedupe | Interning repeated chunk content (WebRender's interner) | Hash all chunks on the three pages and count duplicates | Intern only if duplicates exceed 10 percent of first-frame bytes |
| Q-scroll | Two-writer scroll protocol | A script that sets `scrollTop` during a shell-driven fling, run under the replay oracle | The offset after the fling equals the generation-ordered result, and no frame shows a script offset older than one already applied |
| Q-sound | Does the soundness check catch wrong facts? | Inject a shrunken `ink_bounds`, a too-large `opaque_rect` and a missing backdrop read | Each injected error fails §6's check (3) once, and X14 fails on the matching policy |

**Not decided here.**
- Video's producer and frame protocol (3.9), and image decode size (3.8).
- The accessibility tree's place on the same transport (3.6).
- Whether colour animations move to the shell, which the census bounds at
  81 paint animations on one page.

---------------------------------------------------------------------------

## 8. Sources

Chromium (all `https://chromium.googlesource.com/chromium/src/+/main/` unless noted):
- `third_party/blink/renderer/platform/graphics/paint/README.md` [E]
- `third_party/blink/renderer/platform/graphics/paint/paint_chunk.h`, `paint_artifact.h`, `property_tree_state.h` [E]
- `cc/trees/property_tree.h`, `cc/trees/effect_node.h`, `cc/trees/transform_node.h` [E]
- `components/viz/common/quads/compositor_frame.h`, `compositor_render_pass.h`, `render_pass_internal.h` [E]
- `services/viz/public/mojom/compositing/compositor_frame_sink.mojom`, `layer_context.mojom`, `layer.mojom`, `animation.mojom`, `tiling.mojom` [E]
- https://www.chromium.org/blink/slimming-paint/ [E]
- https://issues.chromium.org/issues/369883417 (TreesInViz tracking bug; search result) [E]
- https://developer.chrome.com/docs/chromium/renderingng-data-structures (cited through `notes/engines.md`)
- Skia: https://skia.googlesource.com/skia/+/refs/heads/main/include/private/chromium/SkChromeRemoteGlyphCache.h [E]

WebRender and Gecko (mirror of mozilla-central, `https://raw.githubusercontent.com/mozilla-firefox/firefox/main/`):
- `gfx/wr/webrender/src/render_api.rs` (Transaction, ResourceUpdate, epochs) [E]
- `gfx/wr/webrender_api/src/display_list.rs`, `display_item.rs`, `font.rs`, `image.rs`, `lib.rs`, `interning.rs` [E]
- `gfx/wr/webrender/src/renderer/mod.rs` (`PipelineInfo`, `flush_pipeline_info`) [E]
- `gfx/layers/wr/IpcResourceUpdateQueue.h` [E]
- https://bugzilla.mozilla.org/show_bug.cgi?id=2073976 and `https://hg.mozilla.org/mozilla-central/json-log/tip/gfx/wr/webrender_api/src/interning.rs` (landed 2026-09-21) [E]

Servo:
- https://raw.githubusercontent.com/servo/servo/main/components/shared/paint/lib.rs, `.../display_list.rs` [E]
- https://github.com/servo/servo/pull/36484 [E, via page summary]

Flutter (`https://raw.githubusercontent.com/flutter/flutter/master/engine/src/flutter/`):
- `display_list/display_list.h`, `flow/raster_cache.h`, `flow/diff_context.h`, `flow/layers/layer.h`, `flow/layers/display_list_layer.cc` [E]
- https://github.com/flutter/flutter/issues/88832 [E, via page summary]; https://github.com/flutter/flutter/issues/166184 [E secondary]

Fuchsia:
- https://fuchsia.googlesource.com/fuchsia/+/refs/heads/main/sdk/fidl/fuchsia.ui.composition/flatland.fidl [E]
- https://fuchsia.dev/fuchsia-src/contribute/roadmap/2021/flatland [E]; https://fuchsia.dev/fuchsia-src/concepts/ui/scenic/flatland [E]

Android (`https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/libs/hwui/`):
- `RenderNode.h`, `RenderProperties.h`, `renderthread/DrawFrameTask.h`, `renderthread/DrawFrameTask.cpp` [E]

Snowghost (`git show origin/main:<path>` at acd7a80):
- `design/processes.md`, `design/pipeline.md`, `design/pipeline/layout.md`
- `research/investigations/incremental/DESIGN.md` §2, §6, §7, §8, Experiments, Results
- `research/investigations/incremental/notes/raster.md` §1, §2.5, §3, §6; `notes/engines.md` §3, §4.2, §7; `notes/webrender.md`; `notes/gpu2d.md`
- `research/investigations/incremental/experiments/contract/report.md`, `local/agg-local.txt`
- `research/investigations/incremental/census/{html5,ecma262,apollo11}.agg.txt`, `census/shape.out`
- `research/investigations/concurrency/runs/0-check-base-e45ccb7.txt`
- the frame walkthrough (scratchpad `frame-walkthrough.html`, sections 2 and 3)

Whitefoot: `spec/kernel-spec.md` [PRE-2], [HOST-1], [WAIT-2], [SHARE-1..3], `std::io` record.
