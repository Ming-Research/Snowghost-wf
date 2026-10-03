# The renderer-to-shell contract census, and X17

Two runs of the same scripts (`measure.mjs`, `inpage.js`, aggregated by
`agg.py`):
- the three local pages, in this container's headless Chromium 141 (chromium-1194), JavaScript off, 2026-10-03; output `res/`, `agg-local.txt`;
- 30 real sites, run by the owner on a Mac with Google Chrome and visible windows, JavaScript on, 2026-10-03; output `real/results.json`, `real/agg.txt`. This container's Chromium rejects the egress proxy's certificate authority, so real sites could not load here.

Viewport 1280×720, device pixel ratio 1, a fresh profile per page, nothing
logged in. The site list was fixed before any run: six each of news, docs,
shops, social and web apps (`sites.txt` in the owner's kit).

## Method

**Census**, in the page after load, network idle and 2.5 s, at scroll 0, over
all rendered elements including open shadow roots:
- stacking contexts by CSS reason (fixed or sticky, z-index, opacity below 1, transforms, filter, backdrop-filter, mix-blend-mode, perspective, clip-path, mask, isolation, contain, container-type, will-change, view-transition-name);
- users of transform, opacity, filter, backdrop-filter and blending; fixed, sticky and will-change elements; video, canvas, iframe, svg and img;
- nested scroll roots: `overflow: auto | scroll` with scrollable overflow, body excluded;
- running animations from `document.getAnimations()`, classified by keyframe properties as compositor-only (transform, opacity, translate, rotate, scale, filter, backdrop-filter), paint or layout;
- Chromium's own layers and compositing reasons from the DevTools LayerTree domain.

**X17 frames.** The main viewport scrolls to k×720 px, k = 1..K, K = min(30,
the page's steps); a first pass loads lazy content. A frame is the step from
k−1 to k. Non-scrolling roots are the outermost fixed or sticky boxes whose
document position changed since the previous frame.
- *Detector A (paint order).* One DOM snapshot with paint order at scroll 0. Paintables are non-empty text, media and form elements, and boxes with a background or border. A frame is interleaved if a paintable of a non-scrolling root and a paintable of scrolling content overlap and the scrolling one is painted later. It ignores clipping, so it can over-report.
- *Detector B (sampling).* A 16×9 grid per frame through `elementsFromPoint`, counting only elements that paint at the point; interleaved if scrolling content sits above non-scrolling content. It respects clipping and can miss thin overlaps.
- *Controls.* Six synthetic pages (`test/`): a fixed or sticky header with `z-index: auto` under later positioned blocks (interleaved), the same with `z-index: 10` (not), no fixed content, a horizontally disjoint header, and a mixed case. A and B agree on all six (16 frames each).

## Results: census

**Real sites** (30 pages; median / p90 / max; full table in `real/agg.txt`):

| measure | median / p90 / max |
|---|---|
| elements | 1,756 / 5,493 / 9,606 |
| stacking contexts | 78 / 330 / 343 |
| transform users | 6.5 / 47 / 264 |
| opacity below 1 | 8.5 / 64 / 195 |
| filter | 0 / 1 / 12 |
| backdrop-filter | 0 / 3 / 13 |
| mix-blend-mode | 0 / 0 / 60 |
| fixed | 1.5 / 5 / 16 |
| sticky | 1 / 3 / 4 |
| nested scroll roots | 1 / 4 / 11 |
| will-change | 0 / 0 / 43 |
| video | 0 / 6 / 25 |
| canvas | 0 / 0 / 2 |
| running animations | 0 / 40 / 162 |
| of which compositor-only | 0 / 1 / 144 |
| of which paint | 0 / 5 / 81 |
| of which layout | 0 / 0 / 0 |
| Chromium layers | 13.5 / 82 / 228 |
| Chromium layers that draw | 10 / 67 / 174 |

- No running animation on any page animates a layout property. The largest counts are ikea (162, 144 compositor-only), walmart (81, all paint) and ebay (75, all compositor-only).
- Chromium's layer counts run from 5 (Hacker News) to 228 (CodePen); amazon 90, ebay 84, ikea 82.

**Local pages** (JavaScript off): 11,845, 179,471 and 117,179 elements; 0 to
2 fixed or sticky elements each; no running animations; Chromium 4 to 10
layers, none promoted for overlap in the main flow. ecma262 has 33,422
`mix-blend-mode` users, all from one rule (`var { mix-blend-mode: multiply }`),
so "reads its backdrop" can arrive as one style fact on tens of thousands of
chunks.

## Results: X17

**Criterion** (written before the run): the one-rule strip placement of
`DESIGN.md` 7.5 stands if the interleaved part needs drawing in under 5
percent of viewport frames over the sample; otherwise strips need splitting
by paint order.

| sample | pages with frames | frames | frames with a non-scrolling root | A interleaved | B interleaved |
|---|---:|---:|---:|---:|---:|
| real sites | 22 | 300 | 295 | 2 (0.7 %) | 0 (0 %) |
| local pages | 3 | 90 | 60 | 0 | 0 |

- The two detector-A frames are the first frame of npr and of wikipedia; B finds none.
- 8 real sites give no frames: youtube, gmaps and excalidraw scroll an inner element, not the main viewport; reddit, old-reddit, quora, medium and google-search were blocked or showed little content.

**Verdict: the criterion holds**, at 0.7 % by the over-reporting detector and
0 % by the sampling one. Non-scrolling content is present in 295 of 300
frames, nearly always painted above the scrolled content, so drawing it each
frame above the strips is the common case and must be cheap.

## Limits

- Main viewport only; interleaving inside nested scrollers is not measured, and pages that scroll an inner element give no frames.
- Steps of one viewport, capped at 30; continuous flings are not sampled.
- Non-scrolling means fixed or sticky roots only; sticky descendants are assumed to move with their root.
- The census counts rendered elements, not pseudo-elements, at one instant after load; scroll-driven or later animations are missed.
- The real sites ran in one region on one machine; consent banners and bot walls depend on both.
