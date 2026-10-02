# The layout stage for headless static rendering

Status: the owner approved the scope, the oracle and the criteria below on
2026-10-01, with the four choices as recommended ("Owner rulings"). The
interface choices Q51 to Q58 were approved as recommended the same day
("Interface choices"), and the tree records them.

## Question

What does the layout stage of the first milestone, headless static
rendering, compute for every box, from which inputs, and how is it judged
correct and fast? Its input is decided: every element's computed values from
`pkg::style` (`research/investigations/style/DESIGN.md`), with percentages
and `calc()` with percentages left for layout (Q49) and lengths rounded to
`LayoutUnit` when layout reads them (`design/vocabulary.md`). Its shape is
decided provisionally (`design/pipeline/layout.md`): an owned tree of
formatting contexts, each paragraph broken into lines in one counted loop
before the context's block pass places floats and breaks again only the
paragraphs a float narrows, and a box tree built by one walk followed by one
decoding loop. What remains is which CSS layout the stage implements first,
what the style stage must add for it, and the oracle and criteria that judge
it.

## What exists

- **Text and fonts.** `pkg::font` parses TrueType and OpenType faces and
  shapes a run with GSUB and GPOS, checked glyph by glyph against HarfBuzz
  (`tests/font/shape_oracle.py`); `pkg::text::line_break` finds UAX #14
  break opportunities; `pkg::text::properties` and
  `pkg::text::normalization` give the Unicode data shaping and
  segmentation need. Font family matching, per-character fallback and the
  joining of shaped runs into lines do not exist.
- **The prototype** (`renderer/proto/layout`) measured the stage's shape
  with a fixed advance per character, no `clear`, floats that do not push
  each other, and fixed fractions of the enclosing width for floats, table
  cells, flex and grid items and inline-blocks: at four workers it ran 3.31
  and 2.94 times faster than the sequential build on html5 and apollo11
  (0.029 and 0.0017 s), breaking again 4 of apollo11's 770 paragraphs
  (`research/investigations/concurrency/DESIGN.md`, "Floats, speculative
  line breaking and fix-up").
- **The style stage** computes 55 longhands. It has none of the flex, grid,
  table or generated-content properties, which its scope left for a second
  batch, and no `width` and `height` attributes as presentational hints.

## What the measured pages use

Measured in Chromium 141 under the style oracle's setup, with
`scope_probe.mjs` in this directory (`runs/scope-probe.txt`).

Each rendered text node's characters, by the nearest layout feature above
it:

| Page | Characters | Block and inline only | Flex item | Grid item | Table | Other |
|---|---:|---:|---:|---:|---:|---:|
| ecma262 | 1,924,693 | | 95.4% | | 4.0% | inline-block 0.6% |
| html5 | 2,577,586 | 95.4% | | | 4.6% | |
| apollo11 | 140,878 | | 1.2% | 85.8% | 12.1% | float 0.5%, inline-block 0.3%, positioned 0.1% |

- **Flex and grid hold the main column.** ecma262's `body` is a one-line
  flex row of a fixed menu, a 33% spacer and `#spec-container` (`flex: 1
  1 66%`, 858 px wide), which holds 96 percent of the body's text;
  apollo11's page is a grid with named areas and fixed columns (`196px
  972px`) whose content cell is itself a grid (`752px 196px`). Inside them
  the text is ordinary block and inline flow, so the containers decide the
  widths everything else is laid out in.
- **Tables** hold 4 to 12 percent of the text; 13 percent of html5's
  117,179 elements are table boxes, among them 11,792 cells and 3,651 rows
  of its index and reference tables.
- **Generated content** is common: ecma262 has 13,368 `::before` boxes
  (grammar markers and word joiners), html5 2,512 (`Note: `, `↪`), and
  apollo11 1,416, among them reference numbers made with `counter()`. Each
  takes inline space and moves line breaks.
- **List markers** are all outside the list item (15,782, 4,235 and 468).
- **Fonts.** Of about 1,500 sampled text nodes per page, Liberation Serif,
  Liberation Sans and DejaVu Sans Mono draw all but 0.07 to 0.11 percent of
  the glyphs; the rest fall back per character to DejaVu Sans, FreeSerif,
  FreeSans and WenQuanYi Zen Hei. The oracle refuses font requests, so
  ecma262's twelve `@font-face` rules load nothing.
- **Family names.** Chromium on the oracle's host draws `serif`,
  `sans-serif` and `monospace` with Liberation Serif, Liberation Sans and
  DejaVu Sans Mono, and `system-ui` with DejaVu Sans; it accepts the
  metric-compatible aliases Arial and Helvetica for Liberation Sans, Times
  New Roman and Times for Liberation Serif, and Courier New and Courier for
  Liberation Mono, but not fontconfig's other substitutes: Georgia,
  Verdana, Segoe UI, IBM Plex Serif and Linux Libertine fall through to
  the default, Liberation Serif, where `fc-match` names DejaVu Serif or
  DejaVu Sans (`runs/families.txt`). The pages ask for IBM Plex, Linux
  Libertine and Georgia among others, none installed.
- **White space and alignment.** `white-space` is `nowrap` on 47,166,
  13,633 and 3,349 elements and `pre` or `pre-wrap` on 1,946, 3,354 and 0;
  `text-align` is `center`, `left` or `right` on 1,227, 11,399 and 3,378
  elements and `justify` on none (the style oracle's Chromium dumps).
- **Replaced elements and form controls** are few: 13, 28 and 96 images,
  SVG and video elements, inputs and buttons, most images sized by `width` and `height`
  attributes (the oracle refuses image requests).
- **Text advances** are not rounded per glyph: ten `i`s of 16px serif are
  44.453125 px wide and one is 4.453125 px, so Chromium sums unrounded
  advances, and rounds the sum up to 1/64 px: one `i` of 17px serif,
  4.7231 px unrounded, is 4.734375 px, and three, 14.1694 px, are
  14.171875 px. A CSS length is truncated instead: a block of `width:
  100.01px` is 100 px wide and one of `100.02px` 100.015625 px. 99.8 to 99.97 percent of
  element boxes have a fractional edge.

## Proposed scope

**Inputs.** The document, its computed styles from `pkg::style`, the fonts
installed on the oracle's host (the same files Snowghost reads), and one
viewport of 1280 by 720 CSS pixels at scroll position zero. Scrollbars take
no space, as in the oracle: Playwright launches headless Chromium with
`--hide-scrollbars`, and ecma262's `body`, 1.27 million px tall, is 1280 px
wide.

**Boxes.** Box generation for `display` `block`, `inline`, `inline-block`,
`flow-root`, `list-item`, `contents` and `none`, the table values, `flex`,
`inline-flex`, `grid` and `inline-grid`, with CSS 2.2's and CSS Display 3's
anonymous boxes; `::before` and `::after` with string, `counter()`,
`counters()`, `attr()` and quote content; outside list markers, which take
no inline space.

**Block layout.** CSS 2.2 chapters 9 and 10: widths and heights with `auto`,
percentages, `min-*`, `max-*` and `box-sizing`; auto horizontal margins;
margin collapsing; block formatting context roots; floats and `clear`;
relative, absolute and fixed positioning with static positions; `sticky`
laid out in flow, where it stays at scroll position zero.

**Inline layout.** CSS Text 3 white-space processing and `text-transform`;
font matching and per-character fallback; shaping with `pkg::font`; line
breaking with `pkg::text::line_break` under `word-break: normal` and
`overflow-wrap`, where Blink's ASCII break table overrides UAX #14 (Text
preparation results, Break opportunities); `letter-spacing`,
`word-spacing`, `text-indent` and `text-align` (start, end, left, right,
center, and justify, which no page uses and the stage aligns as start,
`docs/todo.md`); line boxes from
`line-height` and `vertical-align` (CSS 2.2 10.8); inline boxes' horizontal
margins, borders and padding; atomic inlines (`inline-block`, replaced
elements, `inline-flex`, `inline-grid`, `inline-table`); `br`.

**Fonts.** A `font-family` list is matched against the installed faces by
name, with the metric-compatible aliases and generic families Chromium
resolves on the oracle's host (What the measured pages use, Family names),
an unmatched list ending at the default, Liberation Serif; weight and style
are chosen by CSS Fonts 4's matching, synthesizing what no face provides;
a character no face of the list maps falls back to the installed faces in a
fixed order. This was to revise the style stage's provisional `ex` and
`ch` rule (`design/pipeline/style.md`) to the metrics of the installed font
each element uses; the stage did not do it, and the style stage still takes
them from the generic families' faces (`docs/todo.md`). Web fonts stay out
of scope, so the rule stays provisional on them.

**Replaced elements.** `img`, `video`, `svg` and `canvas` sized by CSS, by
their `width` and `height` attributes as presentational hints, and by
`aspect-ratio`; no image data is read, as the oracle reads none.

**Flex.** CSS Flexbox 1: both directions, single and multiple lines,
`order`, `flex-grow`, `flex-shrink` and `flex-basis` with intrinsic sizes,
automatic minimum sizes, auto margins, `justify-content`, `align-items`,
`align-self`, `align-content` and gaps.

**Grid.** CSS Grid 1 without subgrid: explicit tracks of lengths,
percentages, `fr`, `auto`, `min-content`, `max-content`, `minmax()` and
`repeat()`, including `auto-fill` and `auto-fit`; implicit tracks; named
areas and lines; line-based placement and auto-placement in both flows,
dense included; gaps; the alignment properties.

**Tables.** CSS 2.2 chapter 17 with the automatic and fixed table layout as
CSS Tables 3 describes them: anonymous table objects, captions, `rowspan`
and `colspan`, `border-collapse` (both values), `border-spacing`,
`vertical-align` in cells, and the HTML `width`, `cellpadding`,
`cellspacing` and `border` attributes the HTML Standard maps to CSS.

**The style stage's second batch,** checked by the style oracle with new
columns: the flex and grid properties above, `border-collapse`,
`border-spacing`, `table-layout`, `caption-side`, `content`,
`counter-reset`, `counter-increment`, `counter-set`, `quotes`,
`list-style-position`, `overflow-wrap`, `word-break`, `unicode-bidi` (whose
only effect here is that no soft wrap opportunity precedes an inline box with
a bidi control, `runs/bidi-isolate-breaks.txt`), `aspect-ratio`, and the
presentational hints of `width`, `height` and the table attributes.

**Out of scope,** each counted where the pages use it: writing modes,
`direction: rtl` and bidirectional reordering; multi-column layout
beyond the limited form Q59 brought in (no `column-span`, orphans, widows
or `column-fill: balance-all`); `transform` (which moves
`getBoundingClientRect`); form controls' inner layout, and the intrinsic
sizes of controls other than single-line text inputs, checkboxes and radio
buttons; SVG's inner layout (the `svg` element is a
replaced box); iframes; ruby; hyphenation; fragmentation; `contain` and
container queries; `zoom`; quirks mode.

## The stage's shape, before the interface choices

Following AGENTS.md's "Design for parallelism first" and the decided
tree, the work keeps only these dependencies, which the interface choices,
brought to the owner as decision cards after the scope is approved, refine:

1. Box tree construction: the decided walk and decoding loop, extended with
   generated content and anonymous boxes.
2. Per paragraph and in parallel: itemizing by font, shaping and finding
   break opportunities, which depend on the paragraph's text and styles
   alone.
3. Per formatting context and bottom up: intrinsic sizes, which flex, grid,
   tables, floats and shrink-to-fit widths need and which depend only on
   the context's contents; sibling contexts are independent.
4. Per formatting context and top down: layout at the width the parent
   gives, with the decided speculative line breaking; child contexts at
   known widths are independent.

## Oracle

A new `tests/layout/layout_oracle.mjs` loads each page in Chromium 141
under the style oracle's setup and writes, in the style oracle's TSV
conventions:

- for each element in document order: its index and local name, `none`
  when it generates no box, otherwise its border box from
  `getBoundingClientRect` (x, y, width, height) and its number of fragments
  from `getClientRects`;
- for each text node with a rendered fragment, in document order: its
  number of line fragments and each fragment's box from a `Range`'s
  `getClientRects`;
- the document's scroll height.

A Snowghost driver writes the same format. The comparison judges a
block-level box by its size and its position relative to its parent
element's box, so one wrong height moves the boxes after it in their parent
and no further. Inline-level boxes and text fragments are judged by their
number of fragments and each fragment's width: their positions inside a
paragraph move with every earlier line break, which the fragment counts
already judge, so they are reported, not judged, as absolute positions
are. Inline elements are most elements: 128,809 of ecma262's 179,471,
73,054 of html5's 117,179 and 8,342 of apollo11's 11,845. It reports, per page and per measure,
the share of exact matches (1/64 px) and of matches within 1 px, and the
most frequent mismatches with an example element.

## Criteria

Recorded before any code; the owner ruled on them on 2026-10-01 (Owner
rulings):

1. **Correctness.** On each real page, at least 99 percent of the
   block-level boxes match Chromium within 1 px in width, height and
   position relative to their parent's box; at least 99 percent of the
   inline elements and rendered text nodes have Chromium's number of
   fragments, each fragment's width within 1 px; and each class of mismatch
   is listed with its cause. Elements in out-of-scope features
   count in the denominators.
2. **Speed.** The layout stage, from computed styles to the dumped boxes,
   runs at least 2 times faster at four workers than in the sequential build
   on ecma262 and html5, the pages with enough work to measure, and is
   recorded on all three with its parts: box tree, text (font matching,
   shaping, break opportunities), intrinsic sizes, and the layout passes,
   with the prototype's 0.029 and 0.0017 s on html5 and apollo11 for
   reference.
3. **Equality across builds.** The sequential and `--par` builds give
   byte-identical dumps.

## Choices the owner ruled

1. **One batch or two.** Recommended: one batch with flex, grid, tables
   and generated content, since flex and grid decide the main column's
   width on ecma262 and apollo11, table boxes are 13 percent of
   html5's elements and move what follows them, and generated content moves line
   breaks on every page. The alternative, block and inline first with
   flex, grid and tables in a second batch, reaches a rendered page sooner
   but cannot meet criterion 1 on any page until the second batch lands.
2. **Fonts.** Recommended: match families as the oracle's host does, with
   its aliases and generic defaults written as Snowghost's own table for
   the installed fonts, rather than reading fontconfig's configuration,
   which would tie the renderer to one platform's font service.
3. **Scrollbars.** Recommended: scrollbars that take no space, as the
   oracle's browser has them and as overlay scrollbars behave; the
   alternative reserves 15 px beside every scroll container, as desktop
   Chromium does by default.
4. **The criteria's bounds and measures:** 99 percent, 1 px and a speedup
   of 2, with inline-level positions reported rather than judged. Judging
   them relative to their parent as well would make criterion 1 require
   every line break before them in the paragraph to match too, for most of
   the elements.

## Interface choices

Brought to the owner as decision cards Q51 to Q58 and approved as
recommended; each starts from the dependencies of its candidates.

- **Q51, pseudo-element styles.** The first part of the style stage also
  matches the rules whose subject ends in `::before` or `::after`, and the
  stage computes each generated box's style with its element as parent, in
  a sparse list in document order beside the elements' styles, instead of
  pseudo-element slots for every element or interleaving the generated
  boxes into the element index the oracle and every consumer use: a
  generated box depends only on its element's matched rules and computed
  style, so it joins the same loops, and most elements have none. The
  style oracle dumps a row for each generated box whose `content` is not
  `none`, from `getComputedStyle(element, pseudo)`.
- **Q52, counters and quotes.** One pass in document order over only the
  elements that reset, set or increment a counter, or whose generated
  content reads one or a quote depth, instead of a parallel scan of counter
  scopes: a counter's value is a true chain over those elements in document
  order, and few elements take part: the pages' sheets write `counter()`
  5, 4 and 10 times, and apollo11 renders 124 reference numbers with it.
  List items, which increment the implicit `list-item` counter, join the
  pass only when generated content reads that counter, since outside
  markers take no space; ecma262 has 15,782 of them.
  Q63 (Choices after the results) records where the stage resolves them
  instead: in the box tree builder's walk.
- **Q53, text preparation.** One counted loop over paragraphs, each
  iteration itemizing its own text by font, script and style, shaping each
  item once with `pkg::font` and finding its break opportunities and its
  min-content and max-content contributions, instead of a shaping cache
  shared across paragraphs, which would order paragraphs that do not depend
  on each other, as Q47 refused for `var()`; font lists are matched once
  per interned font group, not per element. A line that ends inside a
  shaped item keeps the item's advances without reshaping its edge, since
  `pkg::font` reports no unsafe-to-break positions; a mismatch class it
  causes reopens it.
- **Q54, rounding to `LayoutUnit`.** A text fragment's width is the sum of
  its glyphs' unrounded advances in logical order, rounded up once to
  `LayoutUnit`, and a computed length is truncated toward zero when layout
  reads it, as the reference does both (What the measured pages use, Text
  advances), instead of rounding each glyph's advance, which drifts by up
  to 1/128 px a glyph and moves line breaks, or rounding both to nearest,
  which misses the exact-match tier by 1/64 px wherever the reference
  rounds otherwise (Q62, below, gives line heights the reference's own
  conversion, `runs/line-height-rounding.txt`); the fixed summation order
  keeps the result independent of the worker count.
- **Q55, fragments relative to their context.** Each formatting context
  writes its boxes, line boxes and text fragments with offsets from its
  own border box, and its parent places it by one offset; absolute
  positions exist only in the walk that dumps or paints, instead of
  absolute positions written during layout, because a context's inside then
  depends on its available size alone, so sibling contexts lay out
  independently and moving a context touches none of its contents.
- **Q56, intrinsic sizes on demand.** A context computes its min-content
  and max-content sizes when a parent's algorithm needs them (flex, grid,
  tables, floats, shrink-to-fit widths), its child contexts' in one counted
  loop, and keeps them, instead of one bottom-up pass over every context,
  which computes sizes that most block-level contexts never read; both keep
  only the subtree dependency. The recursion goes one level per nested
  context, with each context's children in a counted loop, not the halving
  of sibling runs that `design/pipeline/style.md` refused for the runtime's
  recursion budget.
- **Q57, tables.** The automatic and fixed table layout of CSS Tables 3's
  editor's draft, and where the draft leaves a step undefined, the
  reference's behavior with each such step recorded, instead of CSS 2.2's
  informative automatic layout, which leaves column widths to the
  implementation.
- **Q58, the style stage's new groups.** Four new interned groups: flex and
  grid container, flex and grid item, table, and generated content, with
  variable-length values (track lists, area names, content lists) as spans
  into side stores like the family lists, instead of adding the properties
  to the box group, which would make every element's box group differ by
  values most elements leave initial and lose sharing. The table and
  generated-content groups hold inherited and non-inherited properties
  together, as the box group already holds `visibility`.

## Owner rulings

- **2026-10-01, scope, oracle and criteria,** written in Chinese after the
  handoff of mbbill/Snowghost#27: one batch with flex, grid, tables and
  generated content; font matching as Snowghost's own table equal to the
  reference's resolution on its host; scrollbars that take no space; the
  criteria's bounds and measures as proposed.
- **2026-10-01, Q51 to Q58,** written in Chinese: all as recommended, and
  start the implementation.
- **2026-10-02, Q59, multi-column layout,** written in Chinese: agreed
  with the recommendation, a limited multi-column layout. The scope had
  left multi-column out while counting its boxes, without measuring how
  many there are: 9,125 of html5's 44,111 block boxes (20.7 percent) and
  332 of apollo11's 2,365 (14 percent) lie in multi-column containers
  (html5's `#base64-table` and `#named-character-references-table`,
  apollo11's two reference lists), so criterion 1 could not hold on those
  pages without it. Chromium breaks those containers only between table
  rows, between list items that `break-inside: avoid-column` keeps whole,
  and between the lines of a paragraph, without applying orphans or widows,
  splits a broken box into one rectangle per column that reaches the
  column's bottom, and repeats no table header; the stage does the same:
  `column-count`, `column-width`, `column-gap` and balanced columns, no
  `column-span` and no break inside a line.
- **2026-10-02, Q60 and Q61, Chromium over the HTML Standard,** written in
  Chinese: the HTML Standard's `sub, sup { line-height: normal }`, which
  Chromium does not apply, made every line with a `sup` or `sub` 2 to 5 px
  shorter than the reference; with it removed from the user-agent sheet
  ecma262's block boxes rose from 85.98 to 90.53 percent within 1 px and
  html5's from 87.29 to 88.14. The owner first ruled to follow the
  Standard, then reversed it for every difference: Chromium is the engine
  readers compare with, so where the Standard and Chromium differ the
  stage follows Chromium, which also reverses the style stage's ruling on
  `table { border-color: gray }`.
- **2026-10-02, Q62 and Q63** (Choices after the results), written in
  Chinese: both approved as recommended: line heights take the reference's
  conversion to layout units, and the box tree builder's walk resolves
  counters and quotes.

## Text preparation results

`pkg::layout::text` (Q53, Q54) against Chromium 141 on this host, with the
text oracle: `make oracle-text` draws 1,000 rendered text nodes at even
steps from each page with their parents' computed font-family, size,
weight, style, spacing and wrapping (one line of text after white-space
processing and text-transform, at most 120 scalars), adds 24 spacing cases,
10 cases of synthetic styles and sizes, 204 break cases and 648 extents
cases, measures them in Chromium with
`tests/layout/text_oracle.mjs` and compares the `text_oracle` driver's
results (`runs/text-compare.txt`).

| Cases | Count | Width exact at 1/64 px | Breaks equal |
|---|---:|---:|---:|
| ecma262 text | 1,000 | 1,000 | 1,000 |
| html5 text | 1,000 | 999 | 1,000 |
| apollo11 text | 1,000 | 998 | 1,000 |
| spacing | 24 | 24 | 24 |
| synthetic styles and sizes | 10 | 10 | 10 |
| breaks | 204 | 198 | 183 |

2,997 of the 3,000 page cases (99.9 percent) have Chromium's width
exactly, against the 99 percent sought, and the ascent plus descent, the
line height and the baseline of all 648 extents cases (Liberation Serif,
Sans and Mono, DejaVu Sans Mono, Sans and Serif, FreeSerif, FreeSans,
FreeMono, IPAGothic, Unifont and Loma at 18 sizes from 8 to 48 px, regular,
bold and italic) match. What the reference does, as measured:

- **Advances.** A glyph's advance is FreeType's linear advance for the
  size truncated to 26.6, handed to HarfBuzz in 16.16, plus HarfBuzz's
  scaling of its positioning; the size is first quantized by Blink's font
  cache, `trunc(size * 100) / 100` in f32 (18.72 px draws at 18.71, 1197/64
  in 26.6, not 1198/64; the synthetic cases at 18.72, 18.63 and 18.8 px,
  whose 26.6 sizes the quantization lowers by 1/64, match). Within one page Chromium shares a face's platform
  data between nearby sizes, so the oracle measures each size in a page of
  its own. Synthetic bold and synthetic oblique change no advance (the
  synthetic cases of Unifont, IPAGothic and DejaVu Sans at 700 and italic,
  and of WenQuanYi Zen Hei drawn bold by fallback).
- **Vertical metrics.** Ascent, descent and line gap scaled by the
  quantized size in f32 and each rounded half up; no pixel moves from the
  ascent to a descent rounded down. The baseline of a line with
  line-height normal is the ascent plus half the line gap rounded down.
- **Family names and fallback.** As `runs/families.txt` records, and
  `ui-serif`, `ui-sans-serif`, `ui-monospace`, `ui-rounded`, `math`,
  `emoji` and `fangsong` resolve to nothing; named faces match ASCII
  case-insensitively, but Noto Color Emoji and OpenSymbol are never
  matched by name. A character no listed face maps falls back through
  fontconfig's sort of `:lang=en-us:scalable=true` (DejaVu Sans, DejaVu
  Sans Bold, WenQuanYi Zen Hei, Loma, IPAGothic, FreeSans, FreeSerif,
  FreeMono, OpenSymbol, DejaVu Serif, Liberation Serif, the Unifont faces,
  Noto Color Emoji), the regular face drawn with synthetic bold for bold
  text (`runs/text-fallback.txt`); `pkg::oracle::fonts` adds the faces in
  that order. For bold or italic text whose first family is a generic name,
  Chromium first tries fontconfig's face for that name (`serif` is DejaVu
  Serif there), which the fixed order does not model.
- **Scripts.** A run with no letters is shaped as Latin, the script of the
  content language: Liberation Sans kerns only under `latn`, and "6.5.11.1"
  is 1.19 px narrower so.
- **Break opportunities.** Blink's line breaker allows a break after a
  space or tab before anything else, and between two ASCII scalars (or
  U+00A0) only where its ASCII table does (`runs/text-ascii-breaks.txt`:
  after `-` and `?` before most scalars, and before `(`, `<`, `[` and `{`
  after most other punctuation), so "ISO/IEC", "and/or" and "<!DOCTYPE" have no opportunity
  inside where UAX #14 has one; elsewhere UAX #14 applies. An emergency
  break of `overflow-wrap` is never before a space, and `word-break:
  break-word` is `normal` with `overflow-wrap: anywhere`.

Each mismatch class, with its cause (`docs/todo.md` holds the changes):

- **Emoji presentation** (html5's U+231B, and the 6 synthetic emoji cases):
  Chromium draws an Emoji_Presentation character with Noto Color Emoji
  ahead of the family list; `pkg::layout::text` takes the first face that
  maps it.
- **Indic shaping** (2 of apollo11's language links, in Devanagari and
  Tamil): `pkg::font` shapes these scripts as Common, without HarfBuzz's
  Indic shaper; 0.33 and 0.08 px.
- **`word-break: break-all`** (21 synthetic cases, no page text): Blink also
  breaks around dash punctuation and does not break after a hyphen-minus
  before a non-ASCII letter.
- **x-height**, reported but not judged: 481 of 648 extents cases match.
  DejaVu's faces have no OS/2 sxHeight, and Skia measures the hinted x
  glyph (whole pixels, the unhinted 4.375 px at 8 px under synthetic
  oblique), where `face_extents` returns 0.56 times the ascent; five
  FreeSerif and FreeSans cases differ by 1/64 px in ten x-heights.
## Layout results

At Snowghost commit a5fc2de with Whitefoot `3629be15`, against Chromium 141
on this host (`run.sh check`, `runs/check.txt`; Chromium's dumps from
`make oracle-layout-dump`):

| Page | Block-level boxes | Inline-level boxes | Text nodes |
|---|---:|---:|---:|
| ecma262 | 40,112 / 40,182 (99.82%) | 127,523 / 127,533 (99.99%) | 189,739 / 189,761 (99.98%) |
| html5 | 44,111 / 44,111 (100.00%) | 73,008 / 73,054 (99.93%) | 119,707 / 119,763 (99.95%) |
| apollo11 | 2,351 / 2,365 (99.40%) | 8,190 / 8,235 (99.45%) | 8,032 / 8,069 (99.54%) |

Criterion 1 holds on all three pages. The case pages, which hold probes of
the rules below and of known gaps, give flex 259/259, grid 286/286, table
694/718, flow 219/234 and columns 93/99 block-level boxes. What remains,
by class and cause (each deferred in `docs/todo.md`):

- **ecma262, 70 block-level boxes, 10 inline boxes and 22 text
  nodes:** line wraps that differ by less than 0.2 px of available width,
  each moving the boxes after it by up to 3.5 px; 37 `emu-clause`, 9
  `emu-annex` and the other `y` classes follow them. One `path` inside an
  `svg` has no box here, since the stage does not lay out an SVG's inside.
- **html5, 46 inline boxes and 56 text nodes:** right-to-left text, out of
  scope: Arabic in `span`, `kbd`, `samp`, `bdo` and the `pre` of the
  bidirectional examples, which the stage shapes without joining forms and
  does not reorder; and glyph sequences HarfBuzz composes differently (the
  named character references U+226F and U+2282 with U+20D2).
- **apollo11, 14 block-level boxes:** 11 language names in Arabic script
  (right-to-left text, as above); the search icon, which `transform`
  moves (out of scope); and two absolutely positioned boxes whose static
  position lies inside a line, which the stage puts at the block's start.
- **apollo11, 45 inline boxes and 37 text nodes:** the right-to-left
  language names; twelve `abbr` links in `font-variant: small-caps`,
  which the style stage does not compute; and about twenty links whose
  text Chromium kerns with the punctuation after them, which the stage
  does on a probe of the same markup but not on the page, cause not yet
  found.

The rules that brought the pages there, each from a probe of Chromium,
are in `runs/` with their cases in `tests/layout/*-cases.html`: the
culling of inline boxes and the rectangles of a block inside an inline box
(`ecma262-block-in-inline-lh-cell.txt`), line heights rounded to layout
units (`line-height-rounding.txt`), the faces a line's height takes from
fallback (`fallback-line-height.txt`), the `lh` unit, intrinsic width
keywords and floats in intrinsic widths (`float-intrinsic.txt`), the
column widths of spanning cells (`colspan-min-content.txt`), images'
ratios and broken-image fallbacks (`replaced-ratio.txt`,
`alt-icon-min-content.txt`), and balanced columns, whose height Chromium
starts at the one-column content height over the column count and grows
by the least overflow.

**Equality across builds (criterion 3).** At the same commit the
sequential and `--par` builds, the latter at four workers, give
byte-identical dumps of the three pages and the five case pages
(`runs/check.txt`).

**Speed (criterion 2).** `run.sh time` at commit a5fc2de, on this host's
four processors with no other job running, the best of five runs, per run
(`runs/time-parts.txt`). Each run times the stage from computed styles to
laid-out boxes: the box tree (the driver's boxes mode), the text
preparation with font matching, shaping and break opportunities (text mode
less boxes), and the layout passes (layout mode less text); placing the
boxes for the dump and writing it are not timed.

| Page | Part | Sequential | `--par`, 1 worker | 2 workers | 4 workers | Speed-up at 4 |
|---|---|---:|---:|---:|---:|---:|
| ecma262 | whole stage | 1.290 s | 1.357 s | 0.860 s | 0.587 s | 2.20 |
| ecma262 | box tree | 0.103 s | 0.113 s | 0.093 s | 0.100 s | 1.03 |
| ecma262 | text preparation | 0.780 s | 0.833 s | 0.480 s | 0.310 s | 2.52 |
| ecma262 | layout passes | 0.407 s | 0.410 s | 0.287 s | 0.177 s | 2.30 |
| html5 | whole stage | 1.390 s | 1.393 s | 0.880 s | 0.590 s | 2.36 |
| html5 | box tree | 0.100 s | 0.083 s | 0.090 s | 0.090 s | 1.11 |
| html5 | text preparation | 0.937 s | 0.990 s | 0.583 s | 0.357 s | 2.62 |
| html5 | layout passes | 0.353 s | 0.320 s | 0.207 s | 0.143 s | 2.47 |
| apollo11 | whole stage | 0.086 s | 0.086 s | 0.065 s | 0.044 s | 1.95 |
| apollo11 | box tree | 0.005 s | 0.006 s | 0.005 s | 0.005 s | 1.00 |
| apollo11 | text preparation | 0.052 s | 0.055 s | 0.041 s | 0.020 s | 2.60 |
| apollo11 | layout passes | 0.029 s | 0.025 s | 0.019 s | 0.019 s | 1.53 |

Criterion 2 holds on ecma262 and html5. Intrinsic sizes are computed on
demand inside the layout passes (Q56), so they are not a part of their own.
Text preparation is about 60 percent of the sequential stage on ecma262
and 67 percent on html5. The box tree's walk is the one chain in document
order the tree decides, so it does not speed up; at four workers it is 17
and 15 percent of the stage on ecma262 and html5. The layout passes on
html5 take 0.353 s sequentially against the prototype's 0.029 s, which used
a fixed advance per character, no `clear`, floats that do not push each
other, and fixed fractions of the enclosing width for floats, table
cells, flex and grid items and inline-blocks. Of the 340 loops in
`renderer/layout/` the `--par` ledger lists, it permits 49; of the 291 it
refuses, 127 write storage neither the iteration introduces nor an
accumulator holds, 119 write storage that outlives the iteration without
an exactly associative reduction, 39 leave early and 6 carry several
accumulators (`runs/ledger-loops.txt`). Which of them hold the passes'
sequential time is not measured.

**Table steps the draft leaves undefined (Q57).** Where CSS Tables 3's
editor's draft leaves a step to the implementation, the stage takes the
reference's behavior, each probed in Chromium and stated in the function
that implements it:

- columns that no cell starts in and no `col` gives a box collapse, and no
  spacing is counted beside them (`mark_collapsed`,
  `renderer/layout/tablegrid.wf`); the draft's grid keeps them;
- a spanning cell's min-content width grows the columns it spans in
  proportion to how far each column's max-content width exceeds its
  min-content width, then by the draft's excess rules
  (`runs/colspan-min-content.txt`, `tablegrid.wf`);
- the max-content sum leaves room for percentage columns: their
  max-content widths and the others' sum, each over the share of the table
  they leave, are lower bounds (`tablegrid.wf`);
- a row group's height is a least height for its rows, what it exceeds
  them by going to its rows (`renderer/layout/table.wf`); the draft ignores
  heights on row groups.

## Choices after the results

Two decisions the results changed, which the owner approved (Owner
rulings):

- **Q62, line heights in layout units.** Q54 had every computed length
  truncated toward zero when layout reads it. The reference rounds a
  line-height given as a length to the nearest layout unit, and makes a
  number line-height of the font size rounded to the nearest unit times the
  number, truncated (`runs/line-height-rounding.txt`: all 7 length cases
  and all 9 number cases); truncating every length made apollo11's
  infobox rows a unit short each, 1 px after 60 rows. The stage converts
  line heights so (`units_nearest`, `units_times` in
  `renderer/layout/styles.wf`), and `design/vocabulary.md` states it.
- **Q63, where counters are resolved.** Q52 put counter and quote values
  in one pass of the style stage over only the elements that change or
  read a counter. The stage resolves them in the box tree builder's walk,
  which already visits every element in document order, with every list
  item incrementing `list-item`; a separate pass would be a second chain
  in document order over the same elements. `design/pipeline/layout.md`
  states it, and `design/pipeline/style.md` no longer holds Q52's node.
