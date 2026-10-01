# The layout stage for headless static rendering

Status: a proposal of scope, oracle and criteria for the owner's approval;
nothing below is decided and no layout code is written.

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
- **Replaced elements and form controls** are few: 13, 28 and 96 images,
  SVG and video elements, inputs and buttons, most images sized by `width` and `height`
  attributes (the oracle refuses image requests).
- **Text advances** are not rounded per glyph: ten `i`s of 16px serif are
  44.453125 px wide and one is 4.453125 px, so Chromium sums unrounded
  advances and snaps the result to 1/64 px. 99.8 to 99.97 percent of
  element boxes have a fractional edge.

## Proposed scope

**Inputs.** The document, its computed styles from `pkg::style`, the fonts
installed on the oracle's host (the same files Snowghost reads), and one
viewport of 1280 by 720 CSS pixels at scroll position zero. Scrollbars take
no space, as in the oracle, whose browser runs with hidden scrollbars.

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
`overflow-wrap`; `letter-spacing`, `word-spacing`, `text-indent` and
`text-align` (start, end, left, right, center, justify); line boxes from
`line-height` and `vertical-align` (CSS 2.2 10.8); inline boxes' horizontal
margins, borders and padding; atomic inlines (`inline-block`, replaced
elements, `inline-flex`, `inline-grid`, `inline-table`); `br`.

**Fonts.** A `font-family` list is matched against the installed faces,
with the metric-compatible aliases the oracle's host resolves (Arial,
Helvetica and the like to Liberation Sans, Times New Roman to Liberation
Serif, Courier New to Liberation Mono) and the generic families mapped to
the host's defaults (serif to Liberation Serif, sans-serif to Liberation
Sans, monospace to DejaVu Sans Mono), choosing weight and style by CSS
Fonts 4's matching and synthesizing what no face provides; a character no
face of the list maps falls back to the installed faces in a fixed order.
This replaces the style stage's provisional `ex` and `ch` rule
(`design/pipeline/style.md`) with the metrics of the font each element
uses.

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
`list-style-position`, `overflow-wrap`, `word-break`, `aspect-ratio`, and
the presentational hints of `width`, `height` and the table attributes.

**Out of scope,** each counted where the pages use it: writing modes,
`direction: rtl` and bidirectional reordering; multi-column layout;
`transform` (which moves `getBoundingClientRect`); form controls'
intrinsic sizes and inner layout; SVG's inner layout (the `svg` element is a
replaced box); iframes; ruby; hyphenation; fragmentation; `contain` and
container queries; `zoom`; quirks mode.

## The stage's shape, before the interface choices

Following `docs/constitution.md`'s parallelism-first aim and the decided
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

A Snowghost driver writes the same format. The comparison judges sizes and
each box's position relative to its parent element's box, so one wrong
height moves the boxes after it in their parent and no further; absolute
positions are reported, not judged. It reports, per page and per measure,
the share of exact matches (1/64 px) and of matches within 1 px, and the
most frequent mismatches with an example element.

## Criteria

Proposed, to be recorded before any code:

1. **Correctness.** On each real page, at least 99 percent of the elements
   with a box match Chromium within 1 px in width, height and position
   relative to their parent's box, at least 99 percent of the rendered text
   nodes have Chromium's number of line fragments, and each class of
   mismatch is listed with its cause. Elements in out-of-scope features
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

## Choices for the owner

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
4. **The criteria's bounds:** 99 percent, 1 px and a speedup of 2.
