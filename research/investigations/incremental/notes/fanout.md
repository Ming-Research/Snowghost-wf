# How far do local edits propagate? An empirical census on the three real pages

Branch: `fanout` of the end-to-end incremental rendering exploration. This is a measurement, not a design. Everything below
that says "measured" comes from Chromium 1194 (headless, Playwright, scripts disabled, 1280x720, the oracle's sheet mapping)
on `ecma262.html` (179,471 elements, 167,715 boxes, 189,758 rendered text nodes, page 1.27 Mpx tall), `html5.html`
(117,179 / 117,165 / 119,763, 1.15 Mpx tall) and `apollo11.html` (11,845 / 10,600 / 8,069, 55 kpx tall). Anything marked
*inferred* or *speculation* is not a measurement.

Scripts (all in `fanout/`, none touch the repository): `inpage.js` (in-page snapshot, edit and diff machinery), `run.mjs`
(full per-edit census), `chain.mjs` (cheap ancestor-chain census, 300 edits per kind), `counters.mjs`, `shape.mjs`,
`disp.mjs`, `stretch.mjs`, `scroll.mjs`, `dbg.mjs`/`dbg2.mjs`/`prof.mjs` (one-off debugging and timing), and the aggregators `agg.mjs`, `chainagg.mjs`, `summary.mjs`. Raw results:
`apollo11.json`, `html5.json`, `ecma262.json`, `chain-*.json`; aggregates `*.agg.txt`, `summary.md`, `chain.agg.txt`.

## Headline (read this first)

1. **Style is local, and so is most geometry once positions are not absolute.** A style change stays inside the edited
   element's subtree in every sample but one (one `class-` edit on apollo11 changed one element outside the subtree, a
   selector coupling); a leaf color/font-size edit changes the computed style of 1-2 elements, a container-level edit of
   64-137 (median). The *geometry* of a typical word-level text edit is also tiny (1-2 elements resized, 1-3 moved on all
   three pages), because 88-94% of single-word insertions change the height of no ancestor (chain census, n = 300 per page;
   12% on apollo11's narrower columns, 6% on ecma262 and html5).
2. **When a block's height changes, absolute positions of 30-100% of the page change at once, but almost all of that is
   one translation of whole subtrees.** Boxes moved with no size change: median 4,415 (apollo11), 54,842 (ecma262) for a
   12-word insertion; but only 40 / 33 of them are the *roots* of a translation if positions were relative to the
   containing block (the *dirty % rel* columns below: median 0.00-0.77% of boxes and text nodes for the leaf-level kinds, up
   to 2.05% for container-level kinds; p90 up to 5.4% for leaf-level kinds (apollo11 `insert-block`); container-level edits on apollo11 reach 34% (font-size) and
   86% (width) at p90). In aggregate over the edit kinds that move many
   boxes, the share of moved boxes explained by an ancestor's translation is 99-100% on ecma262, 96-99% on apollo11
   and 97-98% on html5; the exception is a width change on a container, 64% on apollo11. (For one-word edits that move
   only the few boxes after the edit on the same line, all moved boxes are roots, which is what one expects.)
3. **Parent-relative storage is not enough on flat documents.** `html5` has one `body` with 3,545 block children. Removing
   one `dd` moves 117,137 boxes; under parent-relative positions 3,560 offsets must still be rewritten (every following
   child of `body`), under sibling-end-anchored positions 1. Median roots under sibling anchoring: 1-2 (html5; 47 for container width), 1-7 (ecma262,
   apollo11; 27 for container font-size on ecma262). So Q55's "relative to the formatting context" needs a second mechanism (offset relative to the preceding
   sibling's end, or an offset tree) to be O(change) rather than O(siblings).
4. **What cannot be local, by the numbers:** an inline-size change of a container (every descendant re-wraps; apollo11
   `container-width` at p90: 2,205 resized elements, 6,633 move roots, 86% of nodes dirty) and font-size/line-height-like
   inherited changes on a container (89-137 style changes at the median, 91-151 resized elements, then the same push as above).
5. **Couplings that carry fan-out beyond ancestors/descendants:** block height pushing following content (by far the
   largest in absolute terms, section 2 node C); inline-size flowing down (container width);
   table column widths (`table-row>table-cell` residual width changes with no changed child: html5 1,180, apollo11 201,
   summed over all edits); sibling stretch in flex/grid (an `emu-note` label stretches to its content: 334 of 397 probes;
   apollo11's page grid: 272 residual height changes); shrink-to-fit upward through inline ancestors (a one-word text edit
   changes some ancestor's width in 49-73% of edits; the run of ancestors with changed width has median length 1-2, max 8).
   Floats and percentages were present (apollo11: 68 floats, 173 inline `%` widths;
   html5 3 floats; ecma262 none) but I could not isolate them; counters add a statically measured renumbering fan-out
   (section 2, node C).

## 0. Method and limits (status: measured; limits listed because they bound every number)

**Per edit** (page loaded once, every edit applied then reverted in place, so each edit starts from the same state):
1. baseline (once): rebuild the layout tree (`display:none` then restore on `<html>`), then snapshot, for every element,
   `getClientRects()`, for every text node the `Range.getClientRects()`, and the computed style (below);
2. apply the edit, snapshot again, diff, revert; for a sample (every edit on apollo11, every 5th on the big pages) snapshot
   again after the revert and check it equals the baseline (apollo11: 375 checked; html5: 50, 0 differ; ecma262: 39, 0
   differ; apollo11: 165 differ, all by exactly one element, see below).

**Edit kinds** (uniform random over candidates, seeded; counts per page: apollo11 30 per kind (15 for container kinds),
html5 16 (8), ecma262 12 (6) - the big pages are small samples, so p90 and max there are anecdotal; the 300-edit chain
census backs the height-change probabilities):
`text+word` (one lorem word at a random word boundary of a rendered text node), `text-word` (delete a word),
`text+sentence` (12 words), `class+` (add a class that occurs in some stylesheet selector, so often a no-op),
`class-` (remove one of an element's classes), `color` (inline `color:red` on a random box), `width` (inline width 80% of
its current width on a block-level box), `font-size` (`120%` on a random box), `display-none` (random box), `insert-block`
(clone a small block, <= 25 descendants, after itself), `remove-block` (remove one), and the container versions
(`container-color`, `container-font-size` 110%, `container-width` 80%) on block elements with >= 60 descendant elements.
Targets are uniform over elements/text nodes, so most targets are leaves; a user's distribution differs.

**Computed-style set** (26 longhands, cut from 50 for time; style "changed" only if one of these differs):
display float position color font-size font-weight font-family line-height text-align visibility background-color
white-space letter-spacing margin-top padding-top padding-left border-top-width min-width max-width flex-grow flex-basis
overflow-x vertical-align text-indent transform counter-increment, plus the *computed* (not used) `width` and `height`
through `computedStyleMap()`. Properties outside this set (for instance `margin-bottom`, `gap`, `grid-template-*`) that
change would show only as geometry.

**Classification of each element box (union of its `getClientRects()`) and each text node (its range rects):**
unchanged; *size* (any fragment's width or height differs, or the fragment count differs); *shift* (same sizes, fragments
displaced differently = line reflow without size change); *moved* (same sizes, one common translation); gone; appeared.
"Move roots" are moved boxes whose offset relative to a reference box changed: *parent-rel* / *ctx* = relative to the
nearest block-level ancestor's box (the formatting-context container; for text, its nearest block ancestor), *sibling-end* =
relative to the bottom-left corner of the previous block-level sibling when both are block-level and the sibling has a box in both
states; otherwise (first child, inline-level elements, no box in one state) it falls back to the test against the nearest
ancestor *with a box* (possibly an inline box), not the block ancestor. Text-node move roots are always tested against the
nearest block ancestor and are the same in both "dirty % rel" columns. A moved
box that is not a root is "explained by an ancestor translation" (or by the preceding sibling's). Dirty % = (elements +
text nodes in the class) / (boxes + rendered text nodes); *dirty % abs* counts everything whose absolute geometry or style
changed; *dirty % rel* counts style-changed + resized + shifted + gone/new + move roots + resized/shifted text + text
move roots, i.e. what a store of relative offsets would have to rewrite or recompute (an upper bound in that style and
size sets overlap).

**Limits that matter**
- *Tolerance.* Chromium reports rects as float32. At y = 0.5-1.3 Mpx a size is only resolved to 1/16-1/8 px, and a
  fractional shift of a whole subtree changed 5,000+ block heights by 1/32 px in a first pass of html5. Sizes and
  translations are therefore compared with eps = max(1/64, 3 ulp(page height)): 0.016 px (apollo11), 0.375 px (html5,
  ecma262). Real changes below that are invisible to the census.
- *Chromium fragments inline boxes differently on first layout and after incremental relayout* (a `sup.mw-ref` was 3
  abutting rects initially and 1 after any relayout). Abutting rects on one line are merged, and the baseline is taken after
  a forced full rebuild; one element on apollo11 (`span.mw-reference-text`, id `mw-reference-text-c...`, wrapped in the
  baseline, unwrapped after any incremental relayout) still differs permanently once the first edit ran, so every apollo11
  count after that carries +1 "size changed" (visible as `container-color` showing 1 resized element).
- *Invisible to the census:* pseudo-elements and `::marker` (counter renumbering shows no rect or style change),
  paint-only properties outside the set, scrolling and sticky/fixed effects (apollo11 has a sticky header), images and fonts (images are blocked; system fonts only).
- *Not the same as Snowghost's dependency graph.* Chromium's result is the ground truth for "what changed", not for what
  a differently structured engine would have to recompute (it can recompute more, or less if it memoizes better).
- Edits are single, and uniform over targets; no editing session, no hover/focus state, one 1280x720 viewport.
- Timing was not measured (three Chromiums shared four cores; the ecma262 run alone took about 25 minutes, over the "few
  minutes per page" budget, because of 180k elements x 26 properties per snapshot).
- `apollo11.json` was produced by an earlier version of `inpage.js` (no `eps` field): its tolerance is identical by the
  formula (1/64 at 55 kpx); only the abutting-rect merge tolerance was 0.001 px instead of about 0.012 px.

## 1. Distributions per page and edit kind

Each cell is median / p90 / max over the edits of that kind (the number in the second column is the edit count and, in
parentheses, how many were no-ops: no element or text box changed at all). "style changed" counts elements whose computed
style (set above) differs; "el size changed" includes shifted, gone and new boxes; "el moved" is the translation-only
count in absolute coordinates; "move roots" are the moved boxes whose offset to their reference box changed (parent-rel =
containing block; sibling-end = previous block sibling's bottom-left corner); "dirty %" as defined in section 0.
The big-page rows rest on 6-16 edits each, so p90/max are single observations.


#### apollo11: 11845 elements, 10600 boxes, 8069 rendered text nodes (eps 0.016 px)

| edit kind | edits (no-op) | style changed | el size changed | el moved (abs) | move roots, parent-rel | move roots, sibling-end | text nodes resized | text nodes moved | dirty % abs | dirty % rel (parent) | dirty % rel (sibling-end) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| text+word | 30 (0) | 0 / 0 / 0 | 2 / 12 / 15 | 3 / 37 / 6696 | 3 / 34 / 59 | 2 / 10 / 37 | 1 / 5 / 9 | 3 / 31 / 5055 | 0.06 / 0.43 / 63.03 | 0.06 / 0.42 / 0.65 | 0.05 / 0.28 / 0.53 |
| text-word | 30 (0) | 0 / 0 / 0 | 2 / 13 / 17 | 6 / 7082 / 9333 | 6 / 40 / 205 | 3 / 9 / 20 | 2 / 6 / 7 | 6 / 5448 / 7434 | 0.08 / 67.22 / 89.91 | 0.08 / 0.42 / 1.24 | 0.06 / 0.22 / 0.36 |
| text+sentence | 30 (0) | 0 / 0 / 0 | 16 / 20 / 179 | 4415 / 7105 / 9173 | 40 / 270 / 437 | 4 / 20 / 119 | 2 / 5 / 7 | 2985 / 5486 / 7277 | 39.74 / 67.57 / 88.19 | 0.44 / 1.59 / 4.82 | 0.14 / 0.43 / 3.12 |
| class+ | 30 (19) | 0 / 3 / 3 | 0 / 8 / 16 | 0 / 5 / 9125 | 0 / 5 / 33 | 0 / 2 / 8 | 0 / 2 / 4 | 0 / 5 / 7228 | 0.00 / 0.09 / 87.70 | 0.00 / 0.10 / 0.40 | 0.00 / 0.07 / 0.27 |
| class- | 30 (22) | 0 / 1 / 5 | 0 / 5 / 11 | 0 / 71 / 774 | 0 / 7 / 8 | 0 / 1 / 2 | 0 / 0 / 2 | 0 / 16 / 360 | 0.00 / 0.50 / 6.13 | 0.00 / 0.07 / 0.11 | 0.00 / 0.04 / 0.07 |
| color | 30 (0) | 2 / 7 / 9 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0.01 / 0.04 / 0.05 | 0.01 / 0.04 / 0.05 | 0.01 / 0.04 / 0.05 |
| width | 30 (0) | 1 / 1 / 1 | 2 / 34 / 156 | 0 / 6598 / 9536 | 0 / 81 / 250 | 0 / 22 / 29 | 0 / 5 / 22 | 0 / 4955 / 7648 | 0.01 / 61.99 / 93.00 | 0.02 / 0.82 / 3.62 | 0.02 / 0.50 / 2.44 |
| font-size | 30 (0) | 2 / 11 / 16 | 18 / 35 / 46 | 4130 / 8799 / 9815 | 27 / 190 / 307 | 7 / 17 / 114 | 1 / 8 / 20 | 2727 / 6973 / 7849 | 36.83 / 84.58 / 94.70 | 0.35 / 1.19 / 2.08 | 0.21 / 0.56 / 1.34 |
| display-none | 30 (0) | 1 / 1 / 1 | 5 / 23 / 28 | 6 / 5087 / 9429 | 6 / 72 / 208 | 3 / 8 / 18 | 0 / 4 / 10 | 5 / 3622 / 7496 | 0.09 / 46.76 / 90.79 | 0.09 / 0.50 / 1.23 | 0.07 / 0.19 / 0.42 |
| insert-block | 30 (0) | 0 / 0 / 0 | 14 / 233 / 235 | 7367 / 9582 / 9639 | 32 / 322 / 324 | 7 / 96 / 98 | 0 / 80 / 83 | 5745 / 7754 / 7775 | 70.30 / 94.54 / 94.54 | 0.35 / 5.36 / 5.38 | 0.12 / 4.15 / 4.17 |
| remove-block | 30 (0) | 3 / 14 / 26 | 22 / 159 / 161 | 4897 / 9585 / 10586 | 25 / 244 / 255 | 7 / 55 / 59 | 0 / 10 / 12 | 3444 / 7650 / 8068 | 44.80 / 92.89 / 99.98 | 0.43 / 3.03 / 3.51 | 0.20 / 2.02 / 2.27 |
| container-color | 15 (0) | 73 / 5369 / 5369 | 1 / 1 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0.40 / 28.76 / 28.76 | 0.40 / 28.76 / 28.76 | 0.40 / 28.76 / 28.76 |
| container-font-size | 15 (0) | 123 / 2587 / 3884 | 131 / 2538 / 3302 | 1680 / 8398 / 10263 | 15 / 18 / 543 | 4 / 12 / 43 | 84 / 1171 / 3166 | 848 / 6665 / 7999 | 16.86 / 81.81 / 97.89 | 2.05 / 33.80 / 55.48 | 1.99 / 33.76 / 55.46 |
| container-width | 15 (0) | 1 / 1 / 1 | 21 / 2205 / 2222 | 590 / 7642 / 8302 | 61 / 6633 / 6668 | 18 / 2253 / 2266 | 2 / 1309 / 1315 | 322 / 6546 / 6585 | 5.65 / 94.57 / 94.94 | 0.69 / 86.04 / 86.53 | 0.46 / 62.57 / 62.95 |

reverts checked 375, not restored 165

#### html5: 117179 elements, 117165 boxes, 119763 rendered text nodes (eps 0.375 px)

| edit kind | edits (no-op) | style changed | el size changed | el moved (abs) | move roots, parent-rel | move roots, sibling-end | text nodes resized | text nodes moved | dirty % abs | dirty % rel (parent) | dirty % rel (sibling-end) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| text+word | 16 (0) | 0 / 0 / 0 | 1 / 2 / 2 | 1 / 4 / 34 | 1 / 4 / 34 | 1 / 3 / 17 | 1 / 3 / 3 | 1 / 7 / 33 | 0.00 / 0.01 / 0.03 | 0.00 / 0.01 / 0.03 | 0.00 / 0.01 / 0.02 |
| text-word | 16 (0) | 0 / 0 / 0 | 0 / 1 / 1 | 1 / 4 / 4 | 1 / 4 / 4 | 1 / 4 / 4 | 2 / 2 / 2 | 2 / 8 / 8 | 0.00 / 0.01 / 0.01 | 0.00 / 0.01 / 0.01 | 0.00 / 0.01 / 0.01 |
| text+sentence | 16 (0) | 0 / 0 / 0 | 5 / 381 / 583 | 551 / 68223 / 94031 | 228 / 1287 / 2092 | 2 / 98 / 194 | 2 / 26 / 36 | 471 / 66027 / 95616 | 0.44 / 56.67 / 80.05 | 0.10 / 1.14 / 1.39 | 0.00 / 0.72 / 0.89 |
| class+ | 16 (12) | 0 / 1 / 1 | 0 / 2 / 2 | 0 / 1 / 4 | 0 / 1 / 4 | 0 / 1 / 2 | 0 / 0 / 1 | 0 / 2 / 4 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| class- | 16 (14) | 0 / 1 / 10 | 0 / 4 / 5 | 0 / 13089 / 40737 | 0 / 214 / 404 | 0 / 4 / 15 | 0 / 0 / 7 | 0 / 11585 / 34233 | 0.00 / 10.42 / 31.65 | 0.00 / 0.11 / 0.18 | 0.00 / 0.01 / 0.02 |
| color | 16 (0) | 1 / 2 / 3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| width | 16 (0) | 1 / 1 / 1 | 1 / 213 / 456 | 0 / 50260 / 52231 | 0 / 880 / 927 | 0 / 42 / 115 | 0 / 58 / 127 | 0 / 44905 / 47193 | 0.00 / 40.31 / 41.97 | 0.00 / 0.83 / 0.94 | 0.00 / 0.49 / 0.59 |
| font-size | 16 (0) | 1 / 3 / 4 | 6 / 13 / 14 | 80410 / 116122 / 116912 | 1799 / 3567 / 3581 | 1 / 6 / 12 | 1 / 3 / 7 | 79301 / 118976 / 119603 | 67.41 / 99.23 / 99.83 | 0.77 / 1.51 / 1.52 | 0.01 / 0.01 / 0.02 |
| display-none | 16 (0) | 1 / 1 / 1 | 2 / 10 / 10 | 2 / 115364 / 117081 | 2 / 3561 / 3566 | 1 / 5 / 8 | 0 / 2 / 2 | 3 / 118388 / 119709 | 0.00 / 98.66 / 99.95 | 0.00 / 1.51 / 1.51 | 0.00 / 0.01 / 0.01 |
| insert-block | 16 (0) | 0 / 0 / 0 | 4 / 105 / 489 | 48072 / 97230 / 98940 | 485 / 2395 / 2567 | 1 / 1 / 16 | 0 / 0 / 124 | 42186 / 98966 / 100719 | 38.10 / 82.81 / 84.27 | 0.21 / 1.01 / 1.09 | 0.00 / 0.05 / 0.37 |
| remove-block | 16 (0) | 3 / 17 / 20 | 6 / 20 / 28 | 48293 / 113857 / 117137 | 532 / 3523 / 3560 | 1 / 2 / 3 | 0 / 0 / 0 | 42278 / 117326 / 119751 | 38.23 / 97.58 / 99.99 | 0.23 / 1.49 / 1.51 | 0.00 / 0.02 / 0.02 |
| container-color | 8 (0) | 64 / 105 / 105 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0.03 / 0.04 / 0.04 | 0.03 / 0.04 / 0.04 | 0.03 / 0.04 / 0.04 |
| container-font-size | 8 (0) | 89 / 614 / 614 | 91 / 612 / 612 | 77692 / 112456 / 112456 | 1658 / 3346 / 3346 | 1 / 4 / 4 | 100 / 713 / 713 | 76355 / 115950 / 115950 | 65.11 / 96.44 / 96.44 | 0.88 / 1.48 / 1.48 | 0.11 / 0.82 / 0.82 |
| container-width | 8 (0) | 1 / 1 / 1 | 96 / 1083 / 1083 | 31806 / 115507 / 115507 | 1025 / 5103 / 5103 | 47 / 129 / 129 | 44 / 186 / 186 | 24132 / 119122 / 119122 | 23.66 / 99.49 / 99.49 | 1.08 / 3.33 / 3.33 | 0.25 / 1.17 / 1.17 |

reverts checked 50, not restored 0

#### ecma262: 179471 elements, 167715 boxes, 189758 rendered text nodes (eps 0.375 px)

| edit kind | edits (no-op) | style changed | el size changed | el moved (abs) | move roots, parent-rel | move roots, sibling-end | text nodes resized | text nodes moved | dirty % abs | dirty % rel (parent) | dirty % rel (sibling-end) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| text+word | 12 (0) | 0 / 0 / 0 | 1 / 2 / 2 | 2 / 3 / 11 | 2 / 3 / 11 | 1 / 2 / 7 | 1 / 2 / 3 | 2 / 5 / 13 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.01 |
| text-word | 12 (0) | 0 / 0 / 0 | 0 / 2 / 4 | 1 / 7 / 16 | 1 / 7 / 16 | 1 / 4 / 5 | 1 / 3 / 3 | 2 / 8 / 14 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.01 |
| text+sentence | 12 (0) | 0 / 0 / 0 | 14 / 15 / 18 | 54842 / 87754 / 109215 | 33 / 57 / 61 | 3 / 13 / 13 | 2 / 4 / 6 | 65425 / 104519 / 126553 | 33.65 / 53.79 / 65.96 | 0.01 / 0.02 / 0.03 | 0.01 / 0.01 / 0.02 |
| class+ | 12 (10) | 0 / 0 / 1 | 0 / 10 / 792 | 0 / 34656 / 121053 | 0 / 18 / 31 | 0 / 0 / 1 | 0 / 0 / 0 | 0 / 39202 / 138072 | 0.00 / 20.66 / 72.71 | 0.00 / 0.01 / 0.23 | 0.00 / 0.00 / 0.22 |
| class- | 12 (5) | 0 / 1 / 2 | 0 / 3 / 12 | 0 / 2 / 162456 | 0 / 2 / 39 | 0 / 2 / 2 | 0 / 0 / 2 | 1 / 5 / 183987 | 0.00 / 0.00 / 96.92 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.00 |
| color | 12 (2) | 1 / 6 / 26 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.01 | 0.00 / 0.00 / 0.01 |
| width | 12 (0) | 1 / 1 / 1 | 1 / 18 / 42 | 0 / 135519 / 151831 | 0 / 46 / 101 | 0 / 2 / 2 | 0 / 3 / 3 | 0 / 155482 / 171488 | 0.00 / 81.41 / 90.45 | 0.00 / 0.02 / 0.08 | 0.00 / 0.01 / 0.06 |
| font-size | 12 (4) | 1 / 2 / 19 | 11 / 18 / 28 | 78135 / 166227 / 167355 | 40 / 64 / 69 | 2 / 12 / 17 | 1 / 2 / 36 | 93684 / 188196 / 189376 | 48.07 / 99.15 / 99.79 | 0.02 / 0.03 / 0.04 | 0.01 / 0.01 / 0.03 |
| display-none | 12 (0) | 1 / 1 / 1 | 2 / 16 / 17 | 2 / 19614 / 165130 | 2 / 33 / 50 | 1 / 5 / 9 | 1 / 4 / 4 | 4 / 19796 / 187192 | 0.00 / 11.03 / 98.56 | 0.00 / 0.02 / 0.02 | 0.00 / 0.01 / 0.01 |
| insert-block | 12 (0) | 0 / 0 / 0 | 8 / 10 / 12 | 103877 / 143826 / 145149 | 36 / 65 / 97 | 2 / 17 / 32 | 0 / 0 / 0 | 121421 / 164108 / 165381 | 63.03 / 86.14 / 86.87 | 0.01 / 0.02 / 0.03 | 0.00 / 0.01 / 0.01 |
| remove-block | 12 (0) | 6 / 15 / 16 | 18 / 24 / 29 | 82050 / 139961 / 164378 | 39 / 49 / 60 | 1 / 3 / 7 | 0 / 0 / 0 | 97906 / 160431 / 186262 | 50.35 / 84.04 / 98.09 | 0.02 / 0.02 / 0.02 | 0.01 / 0.01 / 0.01 |
| container-color | 6 (0) | 85 / 132 / 132 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0.02 / 0.04 / 0.04 | 0.02 / 0.04 / 0.04 | 0.02 / 0.04 / 0.04 |
| container-font-size | 6 (0) | 137 / 385 / 385 | 151 / 391 / 391 | 104197 / 149504 / 149504 | 62 / 205 / 205 | 27 / 171 / 171 | 147 / 586 / 586 | 121733 / 169187 / 169187 | 63.24 / 89.28 / 89.28 | 0.15 / 0.49 / 0.49 | 0.14 / 0.48 / 0.48 |
| container-width | 6 (0) | 1 / 1 / 1 | 41 / 51 / 51 | 19356 / 101314 / 101314 | 84 / 145 / 145 | 5 / 25 / 25 | 13 / 14 / 14 | 19478 / 118458 / 118458 | 10.88 / 61.49 / 61.49 | 0.05 / 0.11 / 0.11 | 0.03 / 0.08 / 0.08 |

reverts checked 39, not restored 0

**Chain census** (`chain.mjs`; 300 edits per kind per page; rects of the target's ancestor chain only). The probability that the edit changes the height of *any* ancestor (so that the content below it is pushed), the length of the run of ancestors whose height changes (median / p90 / max), and the number of following siblings, summed over the height-changed ancestors, that sit in the push path (median / p90 / max; an upper bound of the offsets rewritten under parent-relative storage):

| edit kind | apollo11: P(height) / run / following siblings | html5 | ecma262 |
|---|---|---|---|
| text+word | 12% / 10/18/20 / 16/246/291 | 6% / 6/9/10 / 664/3165/3277 | 6% / 8/16/22 / 33/62/65 |
| text-word | 10% / 14/15/20 / 16/184/280 | 4% / 5/10/11 / 1423/2839/2902 | 6% / 8/13/14 / 39/69/105 |
| text+sentence | 88% / 13/16/21 / 19/176/302 | 53% / 5/8/11 / 591/2697/3551 | 83% / 10/14/22 / 35/55/114 |
| font-size 120% | 94% / 10/16/21 / 20/174/302 | 99% / 5/8/13 / 1154/2916/3590 | 79% / 9/13/20 / 41/63/148 |
| width 80% | 27% / 10/15/20 / 13/31/239 | 18% / 4/7/10 / 870/2856/3253 | 20% / 8/13/17 / 34/46/73 |
| insert-block | 87% / 10/16/19 / 9/29/93 | 82% / 4/6/12 / 454/2916/3571 | 98% / 8/12/20 / 35/53/103 |
| remove-block | 86% / 9/14/19 / 7/35/102 | 74% / 4/6/12 / 453/2916/3571 | 97% / 8/12/20 / 35/53/103 |
| display-none | 30% / 12/16/20 / 12/99/264 | 32% / 4/7/10 / 655/3279/3588 | 42% / 8/11/16 / 37/56/105 |

(Median page shape for the following-sibling column: `shape.out`: html5's `body` has 3,545 children, 99% of boxes' parents
have <= 9 children; ecma262's widest container has 122; apollo11's widest list has 297. Depth: median 15 (apollo11), 5
(html5), 9 (ecma262); max 27-28. The chain runs of 10-20 ancestors on apollo11/ecma262 are mostly depth, not fan-out.)

## 2. The tree of couplings

Each node: what carries the dirtiness, status, the evidence from this census, what it implies for the Whitefoot design
(Q55 fragments relative to their formatting context; Q56 intrinsic sizes on demand).

### A. Style inheritance and selectors (status: measured, bounded)
- Style dirtiness stayed in the edited element's subtree in 405 of 406 style-edit samples (class+, class-, color,
  font-size, width, display-none, container-color, container-font-size on the three pages); the exception is one apollo11
  `class-` that changed one element outside the subtree.
  Median changed elements for `color`: 2 / 1 / 1 (apollo11 / html5 / ecma262), for container color 73 / 64 / 85, for
  container font-size 123 / 89 / 137 (p90 apollo11 container-color 5,369 = a whole section).
- `class+`/`class-` are no-ops for 63% / 73% (apollo11), 75% / 88% (html5), 83% / 42% (ecma262) of random samples: most
  class names in the sheets match something only under other conditions. When they matter they behave like the
  inline-style edits (apollo11 `class+` p90 style changes 3, geometry 8).
- Implies: a dirty set "subtree of the target + rules whose selectors mention the changed attribute" is a tight bound
  here; selector-structural invalidation (siblings, `:has`) was rare (1 of 406 style-edit samples showed it) and is not
  characterized by this census.

### B. Line wrapping within a paragraph (status: measured)
- A one-word insertion changes the paragraph's line count (some ancestor's height changes) in 12% / 6% / 6% of
  edits (apollo11 / html5 / ecma262), a 12-word insertion in 88% / 53% / 83%, a word deletion in 10% / 4% / 6%.
- If the line count is unchanged the damage is the paragraph: the edited text node, `paragraphMate` text nodes sharing the
  nearest block ancestor (21 over the 30 apollo11 `text+word` edits, 9 over 16 on html5, 5 over 12 on ecma262), and the
  boxes after the edit on the same line (median 1-3 moved).
- Resized text nodes outside the paragraph for one-word edits: none on html5/ecma262, 6 over 30 edits on apollo11
  (tables). For the 12-word edit, html5 shows 60 resized text nodes (over 16 edits) in blocks whose width changed (table cells).
- Implies: line breaking is a per-paragraph computation whose output interface (height, line count, widths) is what the
  outside depends on; if unchanged, nothing else needs to run. This is the cheapest and most valuable memo boundary.

### C. Block height pushing following content (status: measured; the dominant coupling)
- Absolute positions change for 30-100% of the page whenever a height changes (see `dirty % abs`); relative to the
  containing block almost none do: `dirty % rel` 0.0-1.1% in the median edit.
- Roots per level scale with the fan-out of containers on the path: parent-relative move roots are 25-40 (median) for
  the height-changing kinds on apollo11/ecma262, 228-1,799 on html5 whose `body` has 3,545 children; sibling-end anchoring
  needs a median of 1-2 on html5 (p90 up to 98 for the 12-word edit), 1-3 on ecma262 (27 for container font-size) and 4-7
  on apollo11.
- Status of the node's design options: relative-to-context positions (Q55): *established practice* (Chromium LayoutNG's
  physical fragments carry offsets relative to the parent fragment; from memory, not checked here) and measured
  sufficient on nested pages; *insufficient on flat ones* (html5: median 228-1,799 parent-relative roots against 1-2
  sibling-anchored); an offset tree or
  sibling-chained offsets is needed for O(change). Speculation: cumulative offsets in a balanced tree over a container's
  children give O(log n) updates and O(log n) absolute lookup.
- Experiment that would settle it: store block-child offsets three ways (parent-relative array, sibling-end chain,
  tree-of-offsets) in Snowghost's layout output and replay these edits (the `moved` classes are already computed here).

### D. Inline-size flowing down: stretch, percentages, available width (status: measured)
- Container width (80%) is the one edit kind where the downstream set is not an ancestor translation. apollo11
  `container-width` (median / p90): 21 / 2,205 resized elements, 2 / 1,309 resized text nodes, 61 / 6,633 move roots (36%
  of moved boxes unexplained by an ancestor translation in aggregate); html5: 96 / 1,083 resized elements, 1,025 / 5,103
  move roots; ecma262: 41 / 51 resized elements, 84 / 145 move roots (the sampled containers were small).
- Width cause attribution (elements whose width changed, sum over container-width edits, apollo11): 2,358 `followsParent`
  (block child whose width change equals its parent's: stretch), 1,666 `childW`, 544 `parentOther` (their parent
  changed width by a different amount: percentages, table columns, intrinsic sizes). html5 1,982 / 225 / 305; ecma262
  178 / 7 / 0.
- Implies: availability of inline size is the input that makes whole subtrees dirty; Q56's on-demand intrinsic sizes do
  not help here, only a boundary where a subtree's layout depends on its width through a small summary (width-independent
  subtrees, `min-content`/`max-content` memo) could. Not measured: whether a width-keyed memo hits (the first experiment
  below).

### E. Shrink-to-fit and intrinsic sizes upward (status: measured, shallow)
- A one-word edit changes the width of some ancestor in 49-73% of edits on every page (the edited inline box and its
  inline ancestors; run length median 1-2, max 8). Cause tags over the `text+word` edits: html5 and ecma262 all `childW`
  (a child's width changed); apollo11 48 `childW`, 30 `followsParent`, 5 residual.
- Residual (no child changed, parent width not following): `table-row>table-cell` (html5 1,180 over all edits; apollo11
  201): auto table layout, column widths coupling the cells of a column (inferred from the display pair, not isolated).
  `list-item>inline` 159 (apollo11) was not investigated.
- Implies: intrinsic widths propagate through inline ancestors cheaply (a chain); the expensive upward coupling is tables,
  where a cell edit may change the column and so every cell in it. Q56 on-demand intrinsic sizes is where this is
  answered; the census says only that inline chains are short.

### F. Sibling stretch: flex and grid (status: measured, small count, confirmed by probe)
- `flex>block` height changes with no changed child: 63 over all ecma262 edits (emu-notes: label and content are flex
  items; a one-off probe grew the content of 397 ecma262 flex containers: the sibling's height changed too in 334).
  `grid>block` 272 on apollo11, about 2 per edit that changes the page height (plausibly the page-level grid's track
  sizing; not isolated).
- Implies: the dependency is container-local (siblings under the same flex/grid container), so it stays inside the
  container's output; it is a coupling *among siblings*, so siblings are not independent work items when the container is
  flex/grid/table.

### G. Floats (status: not isolated)
- apollo11 has 68 floats, html5 3, ecma262 0, so the corpus barely exercises them; the 254 apollo11 text nodes whose
  size changed with no tag above (cause `other`, `block/block`) are from table/infobox `insert-block` edits and are not
  evidently float effects. Treat floats as unmeasured; the experiment would be a float-heavy page (image-with-caption
  articles).

### H. Percentage and viewport-relative sizes (status: not isolated)
- apollo11: 173 inline `%` widths, ecma262 1, html5 0. A `width` edit on a block is the proxy: its descendants
  re-wrap exactly as in D. No viewport-unit edits were made (the viewport is fixed).

### I. Counters and list markers (status: static census, paint-sized)
- Ordered lists: marker renumbering after inserting/removing an item = following siblings in the list. ecma262
  (14,490 ordered markers) median 1, p90 7, max 37; html5 (3,229) 3 / 11 / 61; apollo11 (299 reference items in 2
  lists, via `counter-increment`) 147 / 267 / 296. (`counters.out`.)
- Counted on elements' own computed style only (pseudo-elements are invisible here): ecma262 has 1 element with
  `counter-reset` and none with `counter-increment`; html5 none; apollo11 348 and 299.
- Geometry effect: none observed in the census (outside markers do not change layout, and the census cannot see
  `::marker` or `::before` content); an item whose digit count changes (9 to 10) can resize an inside marker.
  Implies: counters are an ordered dependency along a sibling list: an edit dirties paint for the following siblings
  (apollo11: ~150 of 299 references) without dirtying layout, which argues for storing them as a prefix-sum structure over
  the list rather than recomputing per item; this is speculation, not measured.

### J. Document height, scrolling, fixed/sticky (status: partly measured)
- Insert/remove edits that change a block's height reach the root's height in 74-98% of cases on ecma262/html5 (chain
  census `reaches root`); on apollo11 the `html` and `body` rects stay 720 px tall (viewport-sized) while `scrollHeight` grows (measured with `scroll.mjs`:
  54,678 to 54,902 after inserting one 60-word paragraph). Scroll extent therefore needs a single aggregated height that is updated by every height-changing edit;
  per-edit cost one add, if heights are stored as deltas.

## 3. What the census says about how much incrementality exists in principle

- **Plenty, if positions are not stored absolutely:** in the median edit the set that must be recomputed (dirty % rel) is
  0.00-0.44% of nodes on apollo11, 0.00-0.77% on html5 and 0.00-0.02% on ecma262 for the leaf-level kinds, and up to
  2.05% (apollo11 container font-size) for the container-level kinds; the same edits change 30-70% of nodes in the median
  for the kinds that usually change a height (text+sentence, font-size, insert/remove) if absolute positions are the dirty unit (p90 up to
  99%). The unit of dirtiness must therefore be a fragment relative to its context, with an offset structure that is not
  O(siblings).
- **Typical edits stay local in style and in line wrapping** (A, B): the first bounded computations are the target's subtree style and its
  paragraph's line breaking. Whether the paragraph's *output* changed (height, line count, widths) decides everything after.
- **The big couplings are few and structurally identifiable:** C (heights down the document, handled by relative
  offsets), D (inline size down, handled only by width-keyed memoization or by recomputing the subtree), table columns and
  flex/grid stretch (siblings under one container are not independent), and counters (paint-only fan-out along a sibling
  list).
- **Where it would not help:** edits that change an inherited font property or the inline size of a large container
  (D, A): on apollo11, where the sampled container is the article body, p90 dirty % rel is 34% (container font-size) and
  86% (container width); on html5/ecma262 the sampled containers were small (p90 <= 3.3%). Those edits stay
  full-subtree recomputations; the win there has to come from parallelism over independent subtrees, not from
  incrementality.

## 4. Open questions and discriminating experiments

1. *Do width-keyed memos hit?* For each paragraph record its output (line count, height, widths) as a function of the
   available inline size; replay container-width edits and count how often a paragraph's output is unchanged (the edits that
   resize a paragraph's box but not its line count: not measurable from this census because box width follows the
   container; Snowghost's own layout would measure it).
2. *Offset structure:* the three-way comparison in C.
3. *Table columns:* for a cell edit, how often does the column width change (so every cell resizes)? The census shows only
   the cases where it did (`wOther`, html5 1,180 residuals).
4. *Corpora:* floats, percentage-heavy and viewport-unit pages; a real editing session (typing at one point) instead of
   uniform samples.
5. *Noise floor:* an engine-internal layout dump instead of rects would remove the float32 tolerance and the inline
   fragment merge; not available through Playwright, and probably not worth it for the conclusions above.

## 5. Top three recommendations

1. **Design the fragment/offset store for flat containers now.** Q55's relative-to-context offsets cut the 33-70% dirty set
   to 0.0-1.1%, but html5's 3,545-child `body` costs 485-3,560 offset rewrites per height change under parent-relative
   storage against 1 under sibling-end anchoring. Settle the offset structure (sibling chain or tree of offsets) before
   building layout memoization on top of it.
2. **Make a paragraph's line-breaking output the first incremental boundary** (B): 88-94% of word-level edits leave
   every ancestor's height unchanged, so recomputing only the paragraph and comparing its summary with the old one
   (line count, height, inline widths) ends most edits at the paragraph.
3. **Treat inline-size changes of containers and inherited font changes as full-subtree work and give them parallelism,
   not incrementality**, and track the sibling-coupled containers (table, flex, grid) as single work items; measure
   width-keyed paragraph memos (experiment 1) before investing in more.
