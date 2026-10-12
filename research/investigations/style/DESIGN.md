# The style stage for headless static rendering

Status: the owner approved the scope, the oracle and the criteria below on
2026-10-01, with flex, grid and generated content left for the second batch,
and the interfaces' choices Q46 to Q50 the same day. The stage is written
(`pkg::css::values`, `pkg::style`, the `style_oracle` driver) and measured
below; criterion 1 holds on ecma262 and fails on html5 and apollo11 on the
border colors alone, which trace to one rule of Chromium's user-agent sheet
that the HTML Standard does not have. The owner ruled the three choices the
results raised on 2026-10-01 ("Choices after the results" below): the stage
keeps the Standard's sheet, so that failure stays recorded (superseded on
2026-10-02 by the ruling Q61, which follows Chromium: "Owner rulings"); `ex` and `ch`
come from the default fonts' metrics; and lengths become `LayoutUnit` when
layout reads them.

The second batch of the layout stage's scope
(`research/investigations/layout/DESIGN.md`, "The style stage's second
batch") is written and measured in "The second batch" below: the 37
longhands of flex, grid, tables and generated content, `::before` and
`::after` (Q51), the four groups of Q58 and the presentational hints of
`width`, `height` and the table attributes. The owner then ruled (Q61,
2026-10-02) that where the HTML Standard and Chromium differ the stage follows
Chromium, so the user-agent sheet gives Chromium's computed values and
criterion 1 holds on every page for every property, border colors and
`counter-reset` included ("The multi-column properties and Chromium's sheet"
below).

## Question

What does the style stage of the first milestone, headless static rendering,
compute for every element, from which inputs, and how is it judged correct?
The stage's shape is decided (`design/pipeline/style.md`: matching in one
parallel loop in document order with a rule index and sibling positions,
then a cascade pass in document order, which "The level cascade" below
later replaced), and so are its value types
(`design/vocabulary.md`: `LayoutUnit` lengths rounded once at computed-value
time, atoms for names, interned groups of computed values). What remains is
which CSS the stage implements first and the oracle that judges it.

## What the measured pages use

The three real pages of the concurrency investigation, counted over their
style sheets and `<style>` elements (`build/research/concurrency/`):

| Page | Declarations | Distinct properties | Custom property declarations | `::before`, `::after`, `::marker` | `style` attributes |
|---|---:|---:|---:|---:|---:|
| ecma262 | 736 | 142 | 94 | 20 | 0 |
| html5 | 761 | 88 | 0 | 32 | 2 |
| apollo11 | 4,007 | 364 | 421 | 211 | 409 |

- apollo11's module sheet holds 757 `var()` and 213 `calc()` uses, 74
  `@media` and 118 `@supports` rules; ecma262's sheets hold 89 `var()`.
- No sheet uses `@layer` or `@container`; ecma262 declares 12 `@font-face`
  rules, and two `@import` rules of highlight.js themes from a `<style>`
  element, which the oracle refuses to load and the stage skips.
- ecma262's `print.css` applies only to `media=print`, which the prototype
  applied as if it held.
- Flex layout appears on ecma262 (its sidebar) and apollo11 (menus and
  headers).

## Proposed scope

**Inputs.**

- Author style from `<link rel=stylesheet>` (with its `media`), `<style>`
  elements and `style` attributes, in document order.
- A user-agent sheet: the HTML Standard's rendering section, extended from
  the prototype's display rules to every property in scope.
- No user origin. One fixed viewport, 1280 by 720 CSS pixels, media type
  `screen`, `prefers-color-scheme: light`.

**Cascade.** Origin and importance, specificity, order of appearance and
the `style` attribute's place; `@media` with the Media Queries Level 4
features the viewport answers; `@supports` answered by the properties and
values the stage implements; custom properties with `var()` substitution,
fallbacks and cycle detection; `calc()` over lengths and percentages;
`initial`, `inherit` and `unset`, with `revert` and `revert-layer` taken as
`unset` since there is no user origin and no layer; shorthands expanded to
longhands.
Pseudo-classes that depend on interaction (`:hover`, `:focus`) never match.

**Properties.** The longhands block and inline layout and the painting of
text, backgrounds and borders read, 55 of them:

- box: `display`, `position`, `float`, `clear`, `overflow-x`, `overflow-y`,
  `box-sizing`, `visibility`, `z-index`;
- size: `width`, `height`, `min-width`, `min-height`, `max-width`,
  `max-height`;
- offsets: `top`, `right`, `bottom`, `left`;
- margin, padding: the four sides of each;
- border: width, style and color of each side;
- font: `font-family`, `font-size`, `font-weight`, `font-style`,
  `line-height`;
- text: `color`, `text-align`, `text-indent`, `text-transform`,
  `white-space`, `letter-spacing`, `word-spacing`, `vertical-align`,
  `text-decoration-line`, `list-style-type`;
- background: `background-color`;

with the shorthands `margin`, `padding`, `border` and its side, width,
style and color forms, `font`, `background` (its color only), `overflow`,
`list-style` (its type only) and `text-decoration` (its line only).

**Out of the first cut, each a later addition:** flex and grid properties,
`::before` and `::after` with `content`, `::marker`, web fonts from
`@font-face`, background images, border radius, shadows, transforms,
filters, masks, opacity, transitions and animations.

## Oracle

Chromium 141 (`/opt/pw-browsers/chromium-1194`), headless, with scripts
disabled, the same viewport, and every request answered from the pinned
page copies or refused. For each element in document order it reports
`computedStyleMap()` for every longhand in scope; the stage's computed
values are written in the same serialization and compared property by
property. `getComputedStyle` is not used: for sizes, margins, paddings and
offsets it reports values resolved by layout, so `width: 50%` reads
`632px` there and `50%` in `computedStyleMap()`, the computed value this
stage produces (checked with a one-element page).
A first run on ecma262 loaded the page and its two sheets this way and
counted 179,471 elements, the same count Snowghost's tree builder gives,
so the two documents can be compared element by element.

Chromium's own user-agent sheet differs from the HTML Standard's in places;
a difference that traces to it is recorded, not fixed by copying Chromium.

## Criteria

Recorded before any code:

1. **Correctness.** On each real page, every property in scope matches
   Chromium on at least 99 percent of the elements, and each class of
   mismatch is listed with its cause.
2. **Speed.** The style stage at four workers on each real page is
   recorded against the prototype's shape C (0.224, 0.180 and 0.202 s on
   ecma262, html5 and apollo11), with its parts: matching, the cascade pass
   and computing values, and interning. The cascade pass's share reopens
   Whitefoot's unique-keys investigation if it is large
   (`docs/todo.md`, Whitefoot requirements), and the interning pass is
   measured against the bound of `design/vocabulary.md`.
3. **Equality across builds.** The sequential and `--par` builds give the
   same computed values.

## Interfaces

The modules' interfaces are their `module.wfm` files; in short:

- **`pkg::css::selectors`** adds `Specificity` and `matching_specificity`
  (Q46).
- **`pkg::css::values`** holds the 55 longhands as `lh_*` numbers, the
  `Declared` value of a declaration, a `DeclarationStore` of declarations and
  family names, and the seven value groups of `design/vocabulary.md`; the
  eighth, the custom properties, is `pkg::style`'s set of each element.
  `parse_declaration` expands a longhand or one of the shorthands in scope,
  `inset` added for the user-agent sheet's `[popover]` rule, and records a
  value holding `var()` as `Pending`, its sheet and component range.
  `parse_pending` parses a substituted value and reads nothing shared;
  `parse_pending_named` also interns the names of `font-family` and
  `list-style-type`. `compute_length` resolves a length against the font
  size, the element's `ex` and `ch`, the root font size and the viewport of
  an `Environment`.
- **`pkg::style`** holds a `RuleStore` (sheets kept as component lists,
  rules, declarations, custom-property declarations, style attributes),
  `sheet_sources` for the driver, `add_sheet`, `add_style_element` and
  `add_style_attributes`, `media_holds`, and the four steps
  `match_elements`, `inherited_pass`, `reset_pass` and `intern_styles`, which
  `compute_styles` runs in turn and the driver can stop after any one.
- **`pkg::oracle::style`**, the `style_oracle` entry, loads a page and its
  sheets as the browser would and writes the oracle's TSV, or times the
  steps (`run.sh` in this directory).

The second batch extends these interfaces ("The second batch" below): the
37 longhands, `Stored` and `Ratio` values with the store's side tables and
`declaration_store_side_copy`; `alternative_pseudo_element`,
`pseudo_subject_key` and `pseudo_matching_specificity`; `Styles`' four new
groups, their lists and `pseudos`; and `add_presentational_hints`, which the
driver calls after `add_style_attributes`.

## How the three parts keep only true dependencies

Each follows from Q47 and Q50 and
the parallelism rule of `AGENTS.md`, and none changes them.

- **Fixed output per element in the parallel loops.** An iteration of a
  parallel loop writes only its own slot, so the first loop writes, per
  element, the winning declaration of each of the 55 longhands (55 `u32`)
  and one bit per rule that sets custom properties. Matched rules are not
  sorted: each declaration carries a key of origin and importance,
  specificity and declaration order, and the larger key wins, so the order
  in which the rule index offers candidates does not matter.
- **The first loop computes no value.** A longhand that is not inherited
  still needs the element's own font size for `em`, `ex` and `ch`, and its
  custom properties for `var()`, which the pass in document order decides,
  so every value is computed in the second loop; the chain of dependencies
  is the same, as both loops are parallel.
- **Custom properties are chosen in the pass in document order.** They are
  inherited and their number per element is not bounded, so the first loop
  records, per element, the specificity with which each rule that sets
  custom properties matched, one word per such rule, so its memory grows with
  elements times those rules; the pass in document
  order matches nothing again, picks the winning value per name, substitutes `var()` in it against
  the parent's set and the element's own, and shares the parent's set when
  the element declares none.
- **A custom property on a cycle of references is invalid**, fallback or
  not, and one that only refers to the cycle takes its fallback: when a
  round of substitution resolves nothing, the properties that reach
  themselves through the references substitution follows are dropped and
  the rounds go on. A reference counts only where substitution reads it: a
  `var()` whose name has a value is not followed into its fallback, as the
  reference does (both checked by the cases page).
- **The custom-property sets are interned by their entries** as the eighth
  task beside the seven value groups, so equal sets declared apart get one
  identifier.
- **`var()` in a value is substituted on text.** The value's components are
  written back as CSS text with the custom property's text in place of each
  `var()`, an empty comment on either side so no two tokens merge, and the
  result is tokenized again by `pkg::css::syntax`. The parallel loop does
  this in a buffer of its own iteration and reads the custom-property sets
  only.
- **`parse_pending` reads nothing shared.** Only `font-family` and
  `list-style-type` give names that must be interned, and both are
  inherited, so they are parsed by `parse_pending_named` in the pass in
  document order; every other longhand is parsed by `parse_pending`, whose
  effects are reads of its own value only.
- **Explicit `inherit` on a longhand that is not inherited** (such as
  `border-color: inherit`) needs the parent's computed value, which the
  second parallel loop computes at the same time. The element computes it
  again by walking up its ancestors' winning declarations instead: duplicated
  work that adds no order between elements.
- **Blockification** of a flex or grid container's children reads the
  parent's `display` the same way, from the parent's winning declaration.

## Results

Criteria 1 and 3 as `run.sh check` reports them at commit 29fbdd8 and after,
with the pinned compiler, against the Chromium dumps of
`make oracle-style-dump`; criterion 2 from `run.sh time` at the commits
named there.

### Criterion 1: matching Chromium

The lowest share of elements matching per page, with the HTML Standard's
user-agent sheet (`renderer/style/ua.css`):

| Page | Elements | Properties below 99% | Lowest others |
|---|---:|---|---|
| ecma262 | 179,471 | none | border colors 99.37%, line-height 99.44% |
| html5 | 117,179 | border-top, -right and -left-color 96.71% | line-height 99.81% |
| apollo11 | 11,845 | the four border colors 98.17% | font-family 99.24%, color 99.31% |

Every page has the same element count in both. `tests/css/style-cases.html`,
67 elements that exercise what the pages use little (`var()` fallbacks and
cycles and their dependents, `calc()`, media query ranges, `oblique`, `@supports`, explicit `inherit`,
keyword font sizes with and without monospace), matches on every property
but the border colors of its tables and their rows, the same rule's. With Chromium's rule
`table { border-color: gray }` added to a copy of the sheet, and nothing else
changed (`runs/ua-table-gray.txt`, `UA=... run.sh check`), every property
matches on at least 99 percent of the elements of every page and of the
cases page (html5's border colors 100%, apollo11's 99.31%), so that rule
accounts for the failures.

The classes of mismatch, with their causes:

- **Chromium's user-agent sheet where the HTML Standard has no rule**
  (the sheet follows Chromium since the owner's ruling Q61 of 2026-10-02, so
  these classes are gone; "The multi-column properties and Chromium's
  sheet"):
  `table { border-color: gray }` (1,123, 3,849 and 135 elements on
  ecma262, html5 and apollo11, tables and the cells that inherit it);
  `overflow: clip` on `img`, `video` and `canvas` (7, 30 and 65);
  `-webkit-center` for `caption` (17 and 4); the form controls' fonts,
  colors, borders and padding, which the Standard leaves to prose (5 buttons
  and a fieldset on ecma262, 81 inputs on apollo11); `svg:not(:root) { overflow: hidden }` from its SVG
  sheet (1).
- **The HTML Standard's sheet where Chromium has no rule** (also
  followed to Chromium's since Q61): `sub, sup { line-height: normal }` (990
  and 214 elements on ecma262 and html5).
- **Chromium's own behaviour:** the `source` and `track` children of a
  `video` take initial values instead of inherited ones (71 on apollo11);
  two `td` elements of html5 whose font size computes to 4.8px read 6px,
  probably a minimum font size; not confirmed.
- **`@supports` answered by Snowghost's support** (DESIGN, scope): apollo11's
  icons test `mask-image`, which the stage does not implement, so their
  fallback backgrounds apply (19 elements).
- **Not implemented:** the `width` and `height` attributes of `img`,
  `object` and `video` as presentational hints, which the Standard maps to
  the dimension properties (6, 10 and about 25 elements); an SVG `title`
  taken for an HTML one by the sheet's `title { display: none }` (1 on
  ecma262).
- **Serialization, not computation:** the stage keeps `oblique` apart from
  `italic`, and the driver writes both as `italic`, as the reference does,
  so the comparison cannot tell them apart.
- **Not explained:** 4 images of apollo11 whose width differs (`auto`
  against `250px`, `330px` against `325px`).

### Criterion 2: speed

Per-run times in seconds, the best of three runs (`RUNS=3`), on a 4-processor
Linux host, measured at commit d0e70c6 (`runs/time-parts.txt`, written by
`run.sh time`); the code after it changed only the order of the interning
calls and the handling of custom-property cycles. Each part is the
difference between the mode that ends with it and the one before, so a part
of a few hundredths is within the runs' noise.

| Page | Build | Matching | Pass in document order | Third part | Interning | Stage |
|---|---|---:|---:|---:|---:|---:|
| ecma262 | 4 workers | 0.300 | 0.164 | 0.080 | 0.088 | 0.632 |
| ecma262 | sequential | 1.102 | 0.170 | 0.140 | 0.104 | 1.516 |
| html5 | 4 workers | 0.366 | 0.040 | 0.038 | 0.060 | 0.504 |
| html5 | sequential | 1.328 | 0.048 | 0.088 | 0.012 | 1.476 |
| apollo11 | 4 workers | 0.179 | 0.007 | 0.014 | 0.005 | 0.205 |
| apollo11 | sequential | 0.712 | 0.014 | 0.004 | 0.015 | 0.745 |

- **Against the prototype's shape C** (0.224, 0.180 and 0.202 s at four
  workers), the stage takes 2.8, 2.8 and 1.0 times as long. The prototype
  parsed four keywords and stored the rest as hashes, without specificity,
  `!important`, `var()` or computed values; its matching was the same
  shape and index. Matching scales 3.7, 3.6 and 3.9 times from one worker
  to four.
- **Static specificity.** A first run, before the last changes
  (`runs/time-parts-first.txt`), took 0.320, 0.394 and 0.195 s to match at
  four workers. Matching a rule whose alternatives share one specificity
  with the boolean matcher, and reading that specificity from the rule, left
  every dump unchanged and gave 0.306, 0.344 and 0.185 s
  (`runs/time-uniform-specificity.txt`), so specificity is not most of
  matching's cost over the prototype's; the rest is not attributed yet.
- **The pass in document order** is 26 percent of the four-worker stage on
  ecma262 and 8 and 3 percent on html5 and apollo11. On ecma262 that is the
  large share criterion 2 names, so the cascade pass's case for Whitefoot's
  unique-keys investigation is made (`docs/todo.md`).
- **Interning**, the eight tasks, is 14, 12 and 2 percent of the four-worker
  stage in that run; with the eight calls made adjacent so the compiler
  pairs all of them (commit 29fbdd8), a run of the last two modes gave 10, 17 and 7 percent
  (0.062, 0.090 and 0.016 s, `runs/time-interning-final.txt`), and the first
  run, with seven tasks, 22 and 20 percent on ecma262 and html5. The bound
  of `design/vocabulary.md` is 15 percent, so the runs fall on both sides of
  it; from one worker to four it speeds up only 1.1 to 2.1 times on ecma262
  and html5 in the two later runs, and the first run measured it slower at
  four workers. Every run measures it as a difference of whole runs, so it
  is timed alone next (`docs/todo.md`).
- **At the final code** (commit fd6338d, best of five runs,
  `runs/time-parts-fd6338d.txt`), matching and the whole stage ran 8 to 15
  percent slower in both builds than at d0e70c6, though matching's code
  differs only in one bound and its start-up time T(0) rose too (0.27 to
  0.31 s on ecma262 against 0.25 to 0.29 s); the difference is not
  attributed. The stage's speedup from the sequential build to
  four workers is unchanged: 2.4, 2.9 and 3.6 times on ecma262, html5 and
  apollo11 (1.688 to 0.700, 1.650 to 0.568 and 0.823 to 0.230 s), against
  2.4, 2.9 and 3.6 at d0e70c6. On ecma262 the pass in document order
  (0.172 s sequential) bounds four workers at about 3.1 times; matching
  scales 3.5 times, the third part 2.0 and interning 1.3.

### Criterion 3: equal builds

The sequential and `--par` builds wrote byte-identical dumps of all three
pages and of the cases page. The compiler's parallelism ledger, which
`run.sh check` writes to `build/research/style/ledger.txt` and summarizes,
splits the first part's loop (under a `band` of its results) and the third
part's loop (an independent map) and admits the eight interning calls as
parallel pairs; interning speeds up only 1.1 to 2.1 times from one worker to
four on ecma262 and html5 (criterion 2), so how much of that parallelism the runtime uses is not
known.

## Choices after the results

- **Chromium's `table { border-color: gray }`.** With the HTML Standard's
  sheet, html5 and apollo11 fail criterion 1 on the border colors alone,
  and with this one rule added both pass (criterion 1 above). Keeping the
  Standard's sheet records the difference, as the scope says; adding the
  rule makes the stage match the reference on every page.
  The owner ruled for the Standard's sheet (superseded on 2026-10-02 by Q61,
  which follows Chromium). The rendering section of the
  HTML Standard (checked again on 2026-10-01 at
  https://html.spec.whatwg.org/multipage/rendering.html) sets table border
  colors only as `inherit` on row groups and rows, `black` on the cells of a
  table with a `rules` attribute and, as a presentational hint, from the
  `bordercolor` attribute, so criterion 1 stays unmet on html5 and apollo11
  by this one recorded difference.
- **`ex` and `ch`.** Taken as half an em, as CSS allows without font
  metrics, they put 13,306 of ecma262's 179,471 elements (7.4 percent) off
  in `margin-right`, by up to 15 percent (`runs/ex-half-em.txt`). The
  reference resolves them from the x-height and the zero's advance of the
  first available font: for ecma262's `emu-nt` at 18px, Liberation Serif's
  OS/2 x-height of 940 of 2,048 units gives 0.5ex = 4.13086px, the value it
  reports. The stage now takes them from the first generic family of each
  element's list as the environment's default fonts measure it (Liberation
  Serif 940 and 1,024 units, Liberation Sans 1,082 and 1,139, DejaVu Sans
  Mono 1,120, its x glyph's height as it has no OS/2 x-height, rounded up to
  whole pixels as the reference does, and 1,233, read from the fonts'
  `OS/2`, `glyf` and `hmtx` tables), which gives 100 percent on those
  margins; the owner agreed, and the decision is in
  `design/pipeline/style.md`, provisional until the font stage matches
  families. The metrics are those of the reference's
  host, so this criterion's result for `ex` and `ch` is tuned to it.
- **Where lengths become `LayoutUnit`.** `design/vocabulary.md` rounds a CSS
  length to 1/64 of a pixel once, at computed-value time. The stage keeps
  computed lengths as `f32` pixels: the reference's `computedStyleMap`
  reports them unrounded (4.13086px), and percentages and `calc()` with
  them already wait for layout (Q49), so layout reads every length anyway.
  The proposal was to round when layout reads a computed length, the one
  rounding the decision asks for, moved to layout's input; the owner agreed,
  and `design/vocabulary.md` records it.

## The second batch

The longhands, pseudo-elements and hints the layout stage's scope adds
(`research/investigations/layout/DESIGN.md`, "The style stage's second
batch"), on the interfaces of Q51 and Q58.

### What it adds

- **`pkg::css::values`** parses the 37 longhands `flex-direction` to
  `word-break` and the shorthands `flex`, `flex-flow`, `gap` (and the aliases
  `grid-gap`, `grid-row-gap`, `grid-column-gap`, `word-wrap`),
  `place-items`, `place-content`, `place-self`, `grid-template`, `grid`,
  `grid-area`, `grid-row` and `grid-column`; `list-style` now sets
  `list-style-position`. A value of variable length is a `Stored` value
  naming an entry of the `DeclarationStore`'s side stores (track lists with
  their declared tracks and line names, area maps, grid lines, content,
  counter and quote lists, and the two `border-spacing` lengths); an integer
  `repeat()` is expanded at parse time and one `auto-fill` or `auto-fit`
  repeat is kept as the list's repeated range; `aspect-ratio` is a `Ratio`.
  An explicit `0%` keeps its percentage as negative zero, so a computed
  `flex-basis: 0%` (and `width: 0%`) reads as a percentage.
- **`pkg::css::selectors`** keeps which pseudo-element each alternative ends
  in and adds `pseudo_subject_key` and `pseudo_matching_specificity`, which
  match an alternative ending in `::before` or `::after` (or `:before`,
  `:after`) against its originating element with the pseudo-element counted
  as one type selector.
- **`pkg::style`** cascades, inherits and computes the new longhands in the
  three parts, computes a style for each `::before` and `::after` some rule
  with a longhand declaration matches into `Styles.pseudos`, interns the
  four groups of Q58 as four more tasks beside the eight, and offers the
  presentational hints of `add_presentational_hints`. The user-agent sheet
  gains the Standard's rules for the new longhands.

### How the second batch keeps only true dependencies

- **Pseudo-elements are styled nodes after the elements.** A counted loop
  over the elements finds, per element, whether a rule of a second rule
  index, keyed by the compound before the pseudo-element, matches its
  `::before` and its `::after`; a sequential count numbers them after the
  elements, in document order of their elements, since each one's number
  depends on how many come before it; then the first part's loop runs over
  elements and pseudo-elements alike, and the second part's pass reaches a
  pseudo-element after its element, its parent. The winners arrays hold one
  run per styled node, so no element carries pseudo-element slots, and the
  element index space, which the oracle and every consumer read, is
  unchanged. Matching the pseudo-element rules twice, once to find which
  pseudo-elements exist and once to cascade them, is extra work that adds no
  order.
- **Pending values that fill shared tables are parsed in the pass in
  document order.** A `var()` in a track list, an area map, a grid line,
  `content` or a counter list must intern names and append side entries
  after substitution, which writes the shared atom table and store, so the
  pass resolves such values of every node, though the longhands are not
  inherited, and the third part reads the result; the pass does this only
  when the sheets hold such a value, and it is the shared tables that order
  it, not the values' parents.
- **The third part is two counted loops.** The new values not inherited are
  computed in a loop of their own beside the first batch's, because one
  loop writing all twelve outputs captured 520 bytes, more than the
  runtime's 256-byte lane frame, and the compiler declined to run it in
  parallel (the ledger of the first run); the two loops read the same inputs
  and neither waits for the other.
- **Lists are computed where they are interned.** A track list's lengths
  depend on the font of the node whose value applies, and a list cannot be
  written to a shared table from a parallel loop, so the third part keeps a
  reference to the declared list and that node, and the container task
  computes and interns the list beside its group, the one task that writes
  its tables; equal lists share an identifier, and the content task does
  the same for content, counter and quote lists, remembering each declared
  list's identifier.
- **Presentational hints are added in one walk, as style attributes are.**
  Each element's hints are written as a declaration list and parsed into the
  shared store in preorder, before matching; a cell reads its table's
  `cellpadding` and `border` by walking two or three parents up.

### Oracle additions

`tests/css/style_oracle.mjs` dumps the 37 new longhands from
`computedStyleMap()`, whose `get()` gives a list-valued property's first
item, so `grid-auto-columns` and `grid-auto-rows` hold their first track,
and one row per `::before` and `::after` whose content is not `none`, from
`getComputedStyle(element, pseudo)`. For those rows the properties whose
resolved value is not the computed value are dumped empty and not compared:
the sizes, offsets, margins and paddings, `line-height` (a number reads as
px: `line-height: 1.5` on a 16px `::before` reads `24px`), `min-width` and
`min-height` (`auto` reads `0px` on a box that is no flex or grid item), and
the grid templates of a grid container, each checked with a one-element page
in Chromium 141. Chromium keeps a computed counter list in a hash map, so it
serializes `counter-reset: mw-ref-details-parent mw-references list-item`
as `mw-references 0 list-item 0 mw-ref-details-parent 0`; compare sorts the
name and value pairs of the three counter longhands on both sides. A
mismatch in a compared pseudo-element cell is reported, an empty Chromium
cell is skipped, and a row whose index or name differs stops the
comparison, each checked by editing a copy of the cases page's dump.

### The multi-column properties and Chromium's sheet

The layout stage's multi-column layout reads four more longhands, none of them
inherited, which the style stage now parses, cascades and interns, and the
owner's ruling Q61 of 2026-10-02 moved the user-agent sheet to Chromium's
computed values.

- **Longhands 92 to 95.** `column-count` (`auto` or a positive integer,
  `ContainerGroup.column_count`, 0 for `auto`, clamped to 65535 as Chromium
  computes it), `column-width` (`auto` or a non-negative length with no
  percentage, a `Sizing`; `0` is a width, not `auto`), `column-fill`
  (`balance`, `auto`, `balance-all`) and `break-inside` (`auto`, `avoid`,
  `avoid-page`, `avoid-column`, `ItemGroup.break_inside`). They are grammars of
  the second batch's tables (`pkg::css::values`, `columns.wf`), cascaded in
  `reset_second` beside the flex and grid values, and `longhand_count`,
  the cascade's winner tables and the oracle's columns grew from 92 to 96.
  The layout stage then added `unicode-bidi` (`lh_unicode_bidi`, 97
  longhands), which the oracle dumps as a column, and the `lh` unit in
  lengths (`Lengths.lh`), resolved against the element's computed line
  height; with `line-height: normal` the stage takes 1.15 times the font
  size, since it holds no font metrics beyond the x-height and the zero's
  advance (`docs/todo.md`).
- **Shorthands and aliases, as probed in Chromium 141.** `columns` takes a
  width, a count or both in either order, `auto` standing for either and each
  omitted one `auto`; two counts, two widths and three values are invalid and
  `columns: 0 3` reads 0 as the width. `page-break-inside` and
  `-webkit-column-break-inside` accept only `auto` and `avoid`
  (`avoid-page`, `avoid-column` and `always` are invalid there), so they are
  one-longhand shorthands, not aliases; `-webkit-column-count`,
  `-webkit-column-width` and `-webkit-column-gap` are aliases and
  `-webkit-columns` a shorthand alias. `-moz-column-width` and the other
  `-moz-` spellings stay unknown names, as in Chromium (apollo11 and html5
  write them beside the standard ones). Chromium 141 rejects
  `column-fill: balance-all`; the stage parses it as CSS Multicol Level 2
  defines it, since the interface declares it, and the cases page leaves it
  out so that one difference does not enter the criterion.
- **Interning.** The container and item groups are interned by a key of their
  fields, which the new fields had to join: before they did, the cases page
  showed `column-count` 95.81%, `column-width` 95.81%, `column-fill` 98.74%
  and `break-inside` 96.23%, every element taking the first group with the
  same other values.
- **Parallelism.** The four values are read by the loops that already read
  the flex and grid values, so no loop is added and none gains an order; the
  ledger still splits `pseudo_flags`, `match_all`, `reset_all` and
  `reset_second_all` (10 captured bindings, as before) and admits the eleven
  adjacent interning pairs, and every page's sequential and `--par` dumps are
  byte-identical.
- **The user-agent sheet follows Chromium.** `ua.css` adds
  `table { border-color: gray }`, drops `line-height: normal` from `sub` and
  `sup`, sets `overflow: clip` on `img`, `video`, `canvas`, `iframe`, `embed`
  and `object` (not on `input[type=image]`), `-webkit-center` for `caption` and
  `center`, the SVG sheet's `overflow: hidden`, and the fonts, colors, borders,
  padding and disabled colors of `input`, `button`, `select`, `textarea` and
  `fieldset`; it leaves out `ol, ul, menu { counter-reset: list-item }` and the
  `align-content` rules of inputs, buttons and selects. Every rule from
  Chromium's sheet is marked in the file. The control rules were written
  against Chromium's computed values for each input type, `button`, `select`
  (drop-down and list box), `textarea`, `fieldset` and the disabled variants,
  on probe pages dumped by `style_oracle.mjs` and diffed cell by cell with the
  driver; the cases page keeps one of each input type, the disabled variants,
  `button`, drop-down and list-box `select`, `textarea` and `fieldset`, and
  the controls still differing (`option`, `meter`, `progress`, `audio`,
  `marquee`, `rt`, the controls of a disabled `fieldset`: `docs/todo.md`) are
  left off it.
  The stage has no system colors, so `Canvas`, `CanvasText` and `ThreeDFace`
  (whose declarations the sheet dropped as invalid, leaving the dialog's
  background and the fieldset's border unset) are written as the rgb values
  Chromium resolves them to, and the hint that gives the cells of a bordered
  table their width and `inset` style now gives `border-color: inherit` too,
  as Chromium does, so the cell shows the table's gray.

Results of `run.sh check`, against Chromium dumps made by the same tree's
`make oracle-style-dump`, before the sheet's change (commit 356d6ee, with
`UA` set to the previous `ua.css`) and after it (commit 59a946b; the cases page at commit 4df6612, which adds the controls), per page: the
properties below 99 percent and the lowest property, whose causes are the
classes above.

| Page | Elements | Before: below 99% | After: below 99% | After: lowest property |
|---|---:|---|---|---|
| ecma262 | 179,471 | counter-reset 97.29% | none | display, width, height 99.99% |
| html5 | 117,179 | border-top, -right, -bottom, -left-color 96.78% | none | width, height, aspect-ratio 99.98% |
| apollo11 | 11,845 | border colors 98.36% | none | line-height 99.40% |
| cases | 179, then 230 | border colors 85.77% | none | align-content, grid-template-rows, content 99.65% |

The four new columns match on every element and pseudo-element of every page
(100.00%; the cases page has 291 compared cells each, including a `::before`
with its own `column-count`, `column-width` and `break-inside`). The remaining
lowest values are the classes recorded above that Q61 does not touch: images
the oracle refuses, `source` and `track` under `video`, `lh` and `round()`,
the repeat, `safe` and `url()` forms on the cases page.

### Results

`run.sh check` with `PAGES` set to a copy of the pages outside the
worktree's link, at commit 4d4fe0f, against the Chromium dumps of the same commit's
`make oracle-style-dump`:

| Page | Elements | Pseudo-elements | Properties below 99% | Lowest new longhand |
|---|---:|---:|---|---|
| ecma262 | 179,471 | 13,368 | counter-reset 97.29% | align-content 99.99% |
| html5 | 117,179 | 2,512 | border-top, -right and -left-color 96.78% | counter-reset 99.16% |
| apollo11 | 11,845 | 1,416 | border colors 98.36%, counter-reset 98.40% | border-collapse 99.73% |
| cases | 161 | 44 | border colors 83.41%, counter-reset 98.53% | align-content 99.02% |

Every page's sequential and `--par` dumps are byte-identical (criterion 3).
The ledger splits `pseudo_flags`, `match_all`, `reset_all` and
`reset_second_all` and admits the twelve interning calls as eleven adjacent
pairs. The border colors were then the owner-ruled difference (Chromium's
`table { border-color: gray }`, a ruling Q61 later superseded, below). With
the user-agent sheet's
`ol, ul, menu { counter-reset: list-item }` left out and nothing else
changed (`runs/ua-no-list-reset.txt`), counter-reset matches on
every element of every page, and every other property is unchanged, so that one rule accounts for its failures.

The classes of mismatch the second batch adds, with their causes:

- **The Standard's user-agent rules where Chromium's computed values
  differ** (left out since Q61; the layout stage is to reset `list-item` for these
  lists implicitly, as Chromium does):
  `ol, ul, menu { counter-reset: list-item }` (5,223, 995 and 211
  lists on ecma262, html5 and apollo11; Chromium resets the `list-item`
  counter without showing it in the computed value); `align-content: unsafe
  center` on inputs and `center` on buttons and selects (5 on ecma262, 23 on
  apollo11), which Chromium leaves `normal`.
- **Chromium's behaviour with images the oracle refuses:** an `img` with
  alt text whose load failed loses its `width` and `height` presentational
  hints and their `aspect-ratio` in Chromium (1 on ecma262, 5 on html5, 9 on
  apollo11): the DevTools protocol shows the hints among the element's
  attribute styles while its computed values are `auto`.
- **Chromium's own behaviour:** as in the first batch, the `source` and
  `track` children of a `video` take initial values, here
  `border-collapse: separate` under a collapsing table (35 on apollo11).
- **Not implemented:** the `lh` unit (`height: 2lh`, 9 `th` on ecma262) and
  CSS `round()`, whose `@supports` block apollo11 uses for image widths (2
  `img`, 325px against 330px; the first batch's unexplained image widths);
  a `url()` in `content` is kept as written where Chromium resolves it
  against the base URL (1 on the cases page).
- **Parsed as the interface declares, differently from Chromium:** an
  integer `repeat()` is expanded (`16px [m] 16px [m]` against
  `repeat(2, 16px [m])`), `safe` and `unsafe` are dropped (`end` against
  `safe end`), and `legacy` with a direction computes to `normal`; each is
  on the cases page only (`docs/todo.md`).

### Choices the second batch raises

- **`ol, ul, menu { counter-reset: list-item }`.** Settled by the owner's
  ruling Q61 (2026-10-02), which follows Chromium and leaves the rule out;
  the question as it stood: the HTML Standard's
  rendering section has the rule, and the tree's decision keeps the
  Standard's sheet and records where the reference differs; with it,
  `counter-reset` misses criterion 1 on ecma262 and apollo11, and without it
  every page passes. Layout needs the `list-item` reset either way, to
  number list markers; it can come from this rule or be implied for lists as
  Chromium does.
- **Interface changes beyond the declared ones,** each needed to reproduce a
  value: `SizeGroup` keeps `aspect_width` and `aspect_height` instead of one
  ratio, since the computed value is the pair (`auto 100 / 50`);
  `TrackList.repeat_names_before` holds the names between the track before an
  automatic repeat and the repeat; `item_url` and `item_alt` keep `url()`
  images and the alternative text after `/` (apollo11's `']' / ''`), without
  which those `::after` rows would lose their content; `track_lists[1]` is
  one `auto` track, the implicit tracks' initial value.
- **Shapes the decisions do not settle,** each taken as the one with the
  fewest true dependencies and described in "How the second batch keeps
  only true dependencies": pending values of stored longhands resolved in
  the pass in document order (as it then was), ordered by the shared atom
  table and store; the
  third part as two loops, for the runtime's lane frame; hints written in one
  walk before matching, as style attributes are; lists computed where they
  are interned; and a pseudo-element whose matched rules set only custom
  properties getting no style, since its content is `none` and it generates
  no box.

## The level cascade

The stage's second part, the pass in document order that computes what the
parent decides (font size, custom properties and inherited values), is
sequential: about a quarter of the four-worker stage on ecma262 at its
first measurement (Criterion 2). Shape D of the concurrency investigation
cascaded level by level in the prototype, its level loop proved parallel
by Whitefoot's range facts and `apart` certificate
(`research/investigations/concurrency/DESIGN.md`, Shape D). The owner
agreed, after the layout stage's handoff (mbbill/Snowghost#27), to port it
to the real stage.

**What the pass shares.** Most nodes compute their values from their
parent's and the store's alone and write only their own slots. A node that
declares custom properties, or whose winning value of an inherited or a
stored longhand holds `var()`, appends to stores the pass shares (the
custom-property sets, entries and text, and the list of resolved values,
kept, before the port, in node order for the third part) and may intern
atoms. The port
keeps that work, and only that, out of the parallel loop.

**Criteria**, recorded before the code:

1. **Equal results.** The style oracle's dumps of the three pages and the
   case page are byte-identical to those of the stage before the port, in
   the sequential and the `--par` build.
2. **Speed.** At four workers the pass is at least 1.5 times faster than
   before the port on ecma262 and html5, and the whole stage is not slower
   on any of the three pages, each the best of five runs of `run.sh time`
   on the same host with no other job running.
3. **Record.** The pass's time before and after, at one, two and four
   workers and in the sequential build, and the share of nodes the
   parallel loop handles on each page.

### The port

The dependencies first. A styled node depends on its parent's values, and
on nothing else of the pass, unless it writes a store the pass shares; a
level's elements are therefore independent of one another, and a
pseudo-element depends only on its element. The candidates were:

- **The pass in document order** (before the port): every node waits for
  the one before it, a chain as long as the document.
- **Every node of a level in one loop, the shared stores behind a lock or a
  per-level merge**: it adds an order between nodes that need none, and
  Whitefoot has no lock a counted loop may take.
- **The level's nodes that write no shared store in one counted loop, the
  others after it in document order** (chosen): the chain is the tree's
  depth, plus, per level, the nodes that do write a shared store, whose
  appends keep the order of the pass before the port within the level.

The port, in `renderer/style/levels.wf` and `inherited.wf`:

- `node_plain` flags, in one counted loop over the styled nodes, each node
  that declares a custom property (it gets a set of its own) or has a
  pending winning value of a stored longhand (it appends to the resolved
  list). `inherit_level` then leaves to the sequential path a node without
  a parent element, whose font size every `rem` reads.
- `level_index` groups the elements by the depths the traversal's walk
  already records (`Traversal` keeps them), so the walk is not repeated:
  a counted pass checks that each element's parent precedes it, or is the
  document, and lies one level above it, and counts each depth; a second
  groups the elements by depth in preorder. Its loop invariants (`above`,
  and `fresh` and `grouped`) give its postconditions `up` and `listed`,
  shape D's facts.
- For each level from the root, `inherit_level` computes the level's
  unflagged elements in one counted loop with `apart(i, j) { }`, whose
  requirements are `level_index`'s postconditions: iteration k reads its
  parent's slots and writes its own in each per-node array of the state,
  and its custom-property set is its parent's. `fast_node` gathers the
  declared values by `gather_plain` and computes them by `compute_node`,
  which `inherit_element` shares, so the two paths cannot drift apart. A
  node whose pending value only `parse_pending_named` can parse (a family
  list, a `list-style-type` name, a `border-spacing` or `quotes` value of a
  side table) is flagged in its own slot. `inherit_element` then computes
  the level's flagged nodes in preorder, as before.
- `inherit_pseudos` computes the pseudo-elements in one counted loop after
  the last level, each from its element at an index below the first
  pseudo-element's, which the certificate uses; the flagged ones follow
  in order.
- The resolved list is indexed by node (`resolved_first`, `resolved_end`)
  instead of searched in node order, since the slow nodes now append to it
  in level order. Custom-property sets, the pass's named store and atoms
  are numbered in that order too; nothing the dump or the layout stage
  reads depends on those numbers, only on their contents and equalities.

Two choices depart from the recommendation the work started from, each for
a shorter chain:

- **A pending value of an inherited longhand stays in the loop** when it
  needs no shared store. A node that declares no custom property reads
  only its parent's set, which no iteration of a level writes, so the loop
  substitutes `var()` against it and parses the result with
  `parse_pending`, which interns nothing and appends nothing
  (`plain_resolved`, which the third part's `pending_value` now uses too).
  `parse_pending_named` gives the same value for every value
  `parse_pending` parses, since `merge_side` and `shift_stored` change only
  names and side-table values; only at a resource ceiling do they differ,
  where `merge_side` cannot intern a name of the expansion or append its
  side tables (the atom table or the store full) and stops the stage with
  TooLarge, which the loop, appending nothing, does not. Without it, 65,100 of ecma262's 179,471
  elements and 8,500 of its 13,368 pseudo-elements, each with a pending
  winning value of an inherited longhand, took the sequential path.
- **The facts stay inside the stage's second part.** `todo.md` asks for
  `level_index`'s postconditions where the traversal builds its levels.
  `build_traversal` and `inherited_pass` are public, and a public
  function's contract may name only public fields (Whitefoot's MOD-6), so
  the facts would have to become public fields' postconditions and every
  client (the page and layout oracles, which keep the traversal in their
  own structs) would have to carry them to the call. The pass instead
  checks the walk's recorded depths in one counted loop, which costs what
  deriving them did, and the walk runs once.

**Whitefoot finding.** A counted loop whose certified elements are fields
of a struct behind a reference is denied permission when its body reads a
scalar field of the same struct, though no iteration writes it: in the
minimal case, `set state^.one.inner[at] = v` under `apart` with
`let s = state^.shared.scale;` in the body is denied at the write, while an
element read `state^.shared.table.inner[0]` or a range reference to it is
permitted. The loops read the scalars they need once before the loop.

### Results

With Whitefoot 3629be15, the style oracle's check at commit 881eede
(`runs/level-cascade-check-881eede.txt`), the controls of the facts at the
same commit and the rest at e6fad78, which changes only a function's
description in the renderer:

- **Criterion 1.** Every page's sequential and `--par` dumps are
  byte-identical to the stage's before the port (f4028dc): ecma262
  c2317cfc58d7dafd, html5 55b66818fc3b7e6d, apollo11 6b2c50185e8c4442,
  cases 43af18e0ddfcb6b6. The layout oracle's html5 dumps, sequential and
  `--par`, are byte-identical to the one the layout driver built at
  f4028dc gives (58deb6d805fce800), and `run.sh check html5` of the layout
  investigation passes. A level loop that writes the parent's font instead
  of the computed one changes ecma262's dump and drops `font-size` to 4.41
  percent against Chromium, so the dumps see the loop's results.
- **Permission.** `--par-ledger` permits and splits `inherit_level`'s and
  `inherit_pseudos`' loops (14 and 13 captured bindings) and `node_plain`'s;
  `level_index`'s two passes, the loop over levels and the sequential loops
  stay denied, each depending on what earlier iterations wrote. Without
  `apart`, the level loop is denied at its first write (a `--function`
  build's ledger). Before the loops
  wrote through the state, with each per-node array a parameter, they were
  permitted but declined to split: 26 captured bindings, 1,112 bytes, did
  not fit the runtime's 256-byte lane frame.
- **The facts.** Each is needed: without `inherit_level`'s `up` or
  `listed` requirement, or with the pseudo-element's guard weakened to
  `raw < count`, the certificate is rejected (RANGE-5); without
  `level_index`'s `up` or `listed` postcondition the call of
  `inherit_level` is; without the `above` invariant or the `grouped`
  invariant `level_index`'s return is, and without `fresh` its grouping
  loop (RANGE-3).
- **Criterion 3, the share of nodes the loops compute:**

| Page | Elements | In the level loops | Pseudo-elements | In their loop |
|---|---:|---:|---:|---:|
| ecma262 | 179,471 | 179,470 | 13,368 | 13,368 |
| html5 | 117,179 | 117,178 | 3,129 | 3,129 |
| apollo11 | 11,845 | 11,795 | 1,596 | 1,596 |
| cases | 249 | 242 | 63 | 62 |

  The pseudo-elements counted are the styled ones the first part numbers,
  more than the dump lists. The rest are the root and, on apollo11 and the
  cases page, nodes that declare custom properties or have a pending value
  of a stored longhand.
- **The fallback path.** None of the three pages sends a node of the level
  loop to the sequential path for a pending value only
  `parse_pending_named` parses. `tests/css/style-cases.html` now does: a
  `font-family`, `list-style-type`, `quotes` and `border-spacing` taken
  from `var()`, with and without a custom property in scope. Its dumps
  with the case added, sequential and `--par` (b25828cfabd613e5,
  `runs/level-cascade-check-final.txt`),
  equal the dump the stage before the port gives of the same page, and a
  level loop that leaves such a node unflagged, so that neither path
  computes it, changes the dump from the first added element on.
- **Criterion 2.** `run.sh time` before the port (f4028dc) and after it
  (5936e0f, whose renderer is 7e54cc1's), one after the other on the same
  host's four processors with no other job
  (`runs/level-cascade-time-before.txt`,
  `runs/level-cascade-time-after.txt`), the best of five runs, per run of
  the stage. The pass is the inherited mode less the match mode, a
  difference of two timed modes, so its smaller values carry the noise of
  both (apollo11's two-worker 0.0015 s is below the timer's resolution
  over twenty repetitions):

| Page | Build | Pass before | Pass after | Ratio | Stage before | Stage after |
|---|---|---:|---:|---:|---:|---:|
| ecma262 | sequential | 0.262 s | 0.346 s | 0.76 | 2.410 s | 2.436 s |
| ecma262 | 1 worker | 0.274 s | 0.344 s | 0.80 | 2.394 s | 2.462 s |
| ecma262 | 2 workers | 0.288 s | 0.184 s | 1.57 | 1.530 s | 1.434 s |
| ecma262 | 4 workers | 0.284 s | 0.114 s | 2.49 | 1.094 s | 0.926 s |
| html5 | sequential | 0.058 s | 0.132 s | 0.44 | 1.850 s | 2.024 s |
| html5 | 1 worker | 0.024 s | 0.128 s | 0.19 | 1.842 s | 1.876 s |
| html5 | 2 workers | 0.078 s | 0.048 s | 1.63 | 1.100 s | 1.112 s |
| html5 | 4 workers | 0.074 s | 0.036 s | 2.06 | 0.722 s | 0.718 s |
| apollo11 | sequential | 0.0205 s | 0.0265 s | 0.77 | 1.009 s | 1.014 s |
| apollo11 | 1 worker | 0.0175 s | 0.0085 s | 2.06 | 0.997 s | 0.988 s |
| apollo11 | 2 workers | 0.0160 s | 0.0015 s | 10.67 | 0.543 s | 0.524 s |
| apollo11 | 4 workers | 0.0170 s | 0.0040 s | 4.25 | 0.2945 s | 0.2815 s |

  Criterion 2 holds: at four workers the pass is 2.49 and 2.06 times
  faster on ecma262 and html5, and the whole stage is 15 percent faster on
  ecma262, 4 percent on apollo11 and level on html5 (0.718 against 0.722
  s). At one worker and in the sequential build the port costs: the pass
  runs `node_plain`'s loop, `level_index`'s check and grouping, and a loop
  per level, so on ecma262 it is 20 to 24 percent slower and on html5 two
  to five times slower, its stage 9 percent slower sequentially, more
  than the pass's 0.07 s explains, so part of it is the run's noise. The
  criterion judges four workers, the build the renderer runs; the cost at
  one worker is the price of the levels and is recorded, not hidden.

**What these results rest on.** The equality, the hashes and the
Chromium comparison at the final revision are in
`runs/level-cascade-check-final.txt`, written by `run.sh check`, with
the ledger's verdict on each loop of `levels.wf`. The shares of nodes the
loops compute, the count of nodes the recommendation's rule would have
sent to the sequential path (65,100 and 8,500 on ecma262), the denial of
the level loop without `apart`, the declined split at 26 captured
bindings, and
the controls of the facts were observed by the agent that implemented
the port, with temporary counters and edited copies, and are not in a run
file; repeating them needs the same edits.

## Step timing

The sections above time the stage's parts as differences between whole
modes. This one times each step of the full style build inside one run, so
that four things stop being estimates. The questions, the comparisons and the
results that would answer them were fixed before any run; the results follow
the limits.

**Questions and what decides them.**

1. *Does interning stay within 15 percent of the four-worker stage?* (the
   provisional bound in `design/vocabulary.md`). `intern` is the time of
   `intern_styles` alone, against `total`, the four parts' sum, from
   `run.sh profile` in the `par4` mode. The bound holds on a page when
   `intern` is at most 15 percent of `total` there; it fails on a page above
   it. A page whose three process results straddle 15 percent is undecided.
2. *Why is matching 47, 73 and 87 percent of the stage?* The matcher counts,
   per styled node, the rule items the index offers, those the feature
   filter admits so that their selectors are tested, and those that match.
   Matching's time is the sum of the sequential steps before its loop and
   `match.loop`; `match.loop` divided by the admitted items, in the `seq`
   mode, is the cost of one selector test, filter and index walk included.
   The breakdown is sound only if offered >= admitted >= matched on every
   page and the counters are equal between builds and runs; the page whose
   share is largest is explained when its admitted items per node and its
   cost per test, multiplied, reproduce `match.loop` (they do by
   construction), and the admitted share of the offered items says whether
   the filter or the index is what could cut the tests.
3. *How much of the stage runs before its parallel loops, and how much of
   it is sequential?* `match.rule_index`, `match.positions`,
   `match.pseudo_flags`, `match.numbering` and `match.allocation` precede
   the matching loop, and `alone.depth_check` is the second part's
   sequential check. The `par4` shares of these steps, against the same
   steps in `seq`, say which scale with workers (the ledger says which of
   their loops are split). `alone.positions` and `alone.depth_check` are
   `sibling_positions` and the depth check run alone on the same input after
   the stage; `alone.positions` is checked against `match.positions`, the
   same pass inside the stage, and a difference above 25 percent in `seq`
   means a standalone time cannot stand for the step inside the stage.
4. *Does the positions parameter make `selector_matches` slower?* Shape A of
   the prototype driver calls it for every rule and element. `scan-param.sh`
   times it, interleaved, with this source (base), with
   `scan-without-positions.patch` applied (noparam: the parameter removed
   from the eight matcher functions between `selector_matches` and the leaf
   tests) and with base's binary again (twin). The parameter is a cause when
   noparam's least stage time is at most 0.93 of base's (half the 14 percent
   recorded in `concurrency/DESIGN.md`) and the twin's is within 0.97 and
   1.03 of base's; it is not when noparam is within the twin's spread. A
   spread of twin and base wider than 3 percent leaves it undecided.

**What the measurement changes.** The counters are written by
`match_all`'s iteration into its own three words of a `counts` table, as it
writes its winners; the stage passes an empty table, so its matching counts
nothing. `overhead` times `match` with origin/main's driver and this one in
turn to bound what the empty table costs; the ledger line for `match_all`
must still say split. `match_elements_profiled` repeats `match_with`'s steps
with a clock reading between them and is not called by the stage; the dump
of the path through it (`profdump`) must equal `dump`'s and origin/main's
byte for byte, with a changed user-agent sheet as the control that the
comparison can fail.

**Limits.** The workflow `style-build-timing` runs on a hosted runner, so its
times attribute time to steps and are not precise timings; the 14900K runs
the precise ones. A step run alone (`alone.*`) is timed after the stage, on
the same input, as a check on whether a standalone time can stand for the
step inside the stage (question 3).

### Results

**Run.** Workflow `style-build-timing`, run 38306217375 at df11876, pin
`wf-d837678c6905`, on GitHub-hosted `ubuntu-24.04`, 4 vCPUs (2 physical
cores with two threads each). The `profile` job ran on an Intel Xeon
Platinum 8370C and the `scan-param` job on an AMD EPYC 7763; each job
compares only its own builds. Hosted timings are coarse: a step's time is
the least of three process results (`spread` is the largest over the least
of those three; at most 1.03 for most steps above 1 percent of the total,
at most 1.10 for all of them, and up to 1.15 for steps below 1 percent), `time -p` has a resolution
of 10 ms, and four workers on two cores scale a loop by about 2x, not 4x.
`par4` is four workers, `seq` the sequential build; times are best
milliseconds of the full style build of one page (`total` includes the
clock readings between steps, so the four parts sum to it within 1.5
percent).

**Identity.** For ecma262, html5 and apollo11 the dump of the profiled path
(`profdump`) equals MODE `dump`'s, sequential and with four workers, and
equals the dump of origin/main's driver, byte for byte (SHA-256 prefixes
c2317cfc58d7dafd, 55b66818fc3b7e6d and f7af20a5ec49c511). The control now
differs: a user-agent sheet with `body { display: none !important; }`
changes the profiled dump of ecma262. The first control, without
`!important`, did not change it (CI run 38240732150), because a user-agent
declaration loses to the page's own sheets; the important layer beats every
origin [`layer_of`]. The counters are in order on every page: offered >=
admitted >= matched > 0. The ledger still says `style.match_all` is split
(under `band`, 13 captured bindings, against 23 for origin/main's build).

**Time per step, ecma262 / html5 / apollo11** (ms, share of `total`; `x` is
seq over par4):

| step | ecma262 seq | ecma262 par4 | x | html5 seq | html5 par4 | x | apollo11 seq | apollo11 par4 | x |
|---|---|---|---|---|---|---|---|---|---|
| match.rule_index | 0.13 (0.0%) | 0.13 (0.0%) | 1.0 | 0.15 (0.0%) | 0.13 (0.0%) | 1.2 | 0.51 (0.4%) | 0.51 (0.7%) | 1.0 |
| match.positions | 16.5 (1.6%) | 15.5 (2.7%) | 1.06 | 9.9 (1.7%) | 8.9 (2.7%) | 1.1 | 0.91 (0.7%) | 0.90 (1.3%) | 1.0 |
| match.pseudo_flags | 99.6 (9.7%) | 53.6 (9.3%) | 1.9 | 33.8 (5.9%) | 21.8 (6.6%) | 1.6 | 23.2 (18.7%) | 12.4 (17.8%) | 1.9 |
| match.numbering | 0.78 (0.1%) | 0.81 (0.1%) | 1.0 | 0.39 (0.1%) | 0.46 (0.1%) | 0.9 | 0.05 (0.0%) | 0.07 (0.1%) | 0.8 |
| match.allocation | 12.3 (1.2%) | 12.2 (2.1%) | 1.0 | 3.6 (0.6%) | 3.5 (1.1%) | 1.0 | 0.40 (0.3%) | 0.41 (0.6%) | 1.0 |
| match.loop | 352.9 (34.3%) | 163.7 (28.4%) | 2.2 | 292.5 (50.9%) | 137.7 (41.6%) | 2.1 | 67.5 (54.5%) | 33.3 (47.7%) | 2.0 |
| **match** | 484.7 (47.1%) | 248.0 (43.1%) | 1.95 | 340.8 (59.3%) | 172.6 (52.2%) | 2.0 | 93.0 (75.1%) | 48.0 (68.8%) | 1.9 |
| inherited | 158.0 (15.3%) | 73.8 (12.8%) | 2.1 | 66.3 (11.5%) | 31.8 (9.6%) | 2.1 | 9.1 (7.4%) | 5.5 (7.8%) | 1.7 |
| reset | 250.4 (24.3%) | 134.4 (23.3%) | 1.9 | 82.3 (14.3%) | 52.4 (15.8%) | 1.6 | 11.2 (9.1%) | 6.4 (9.2%) | 1.75 |
| **intern** | 135.4 (13.2%) | 114.9 (20.0%) | 1.18 | 84.7 (14.7%) | 69.8 (21.1%) | 1.2 | 10.0 (8.1%) | 9.0 (12.9%) | 1.1 |
| **total** | 1029.6 | 576.0 | 1.79 | 574.5 | 330.8 | 1.74 | 123.8 | 69.8 | 1.77 |

Run alone after the stage (seq): `alone.positions` 19.1, 12.9 and 0.90 ms,
against `match.positions` 16.5, 9.9 and 0.91 ms; `alone.depth_check` 0.80,
0.51 and 0.044 ms (0.1 percent of the total or less on every page).
`par1` times equal `seq` within 2 percent for every step.

**Counters** (the profiled path counts; the stage itself passes an empty
table). Per styled node: offered 31.7 / 77.9 / 76.8, admitted 27.7 / 43.9 /
46.1, matched 2.21 / 3.60 / 3.21 (ecma262 / html5 / apollo11). The filter
admits 87.6, 56.4 and 60.1 percent of the offered items, and 8.0, 8.2 and
7.0 percent of the admitted tests match. A selector test costs
`match.loop` over admitted: 66.0, 55.4 and 108.8 ns (seq); the cost per
offered item is 57.8, 31.2 and 65.4 ns. The most any node is offered is 84,
137 and 347 items, and admitted 82, 98 and 181. The empty-table cost
(`overhead`, least of five rounds of `match`, new over origin/main's
driver, with a second copy of origin/main's as twin) is 1.004 and 1.000 on
ecma262, 1.030 and 1.023 on html5, 1.022 and 1.011 on apollo11 (seq and
four workers); the twin differs from origin/main's by at most 1.1 percent.

**Question 1: interning against 15 percent of the four-worker stage.**
`intern` is 20.0 percent (ecma262, spread 1.03), 21.1 percent (html5, 1.07)
and 12.9 percent (apollo11, 1.03) of `total` at `par4`. The bound fails on
ecma262 and html5 and holds on apollo11 by this rule. The failures are 5 and
6 points above the bound against a spread of at most 7 percent of the
value, so they hold on hosted noise. Interning is also the one part that
does not scale: 1.1 to 1.2x from `seq` to `par4`, against 1.6 to 2.2x for
the others, although the ledger shows its loops (`intern_styles`,
`intern_values`) split; what stays sequential inside it is not measured
here.

**Question 2: why matching is the largest part.** Matching is 47.1, 59.3
and 75.1 percent of `seq` (43.1, 52.2 and 68.8 at `par4`), and
`match.loop` is 73, 86 and 73 percent of it. The pseudo-element flags are the
second step inside it (9.7, 5.9 and 18.7 percent of `seq`). The earlier
estimates from whole-mode differences were 47, 73 and 87 percent (read in
the order ecma262, html5, apollo11); only the ecma262 share reproduces
here, and the other two are lower by 14 and 12 points; I did not reconcile
them. What the counters add: ecma262 offers
few items (31.7 per node) and the filter keeps nearly all of them, so
the index, not the filter, bounds its tests; html5 and apollo11 offer 2.5
times as many items per node and the filter drops 40 to 44 percent of them
before any test, so the filter already does much of the cutting there. A
test costs twice as much on apollo11 (108.8 ns) as on html5 (55.4 ns) with
about the same number of tests per node, so apollo11's selectors, not its
count, make its matching expensive; why was not measured. The
profiled path counts, so `match.loop` and the cost per test include the
counters' own cost, which the empty-table figures above bound at 3 percent
of `match` at most.

**Question 3: what runs before the parallel loops.** In `par4` the steps
that do not scale are `match.rule_index`, `match.positions`,
`match.numbering` and `match.allocation` (1.0x, 1.06x on ecma262), 28.7 ms
or 5.0 percent of the ecma262 total, 13.0 ms or 3.9 percent on html5 and 1.9
ms or 2.7 percent on apollo11; `match.positions` (2.7 percent on the two
large pages) and `match.allocation` (2.1 percent on ecma262) are the two
that matter. `alone.depth_check` is the second part's sequential check and
costs at most 0.1 percent. `alone.positions` stands for `match.positions`
on ecma262 (+16 percent) and apollo11 (-0.4 percent) but not on html5 (+30
percent, above the 25 percent bound), so for html5 use `match.positions`;
the earlier premise that a standalone pass is a lower bound was wrong here.
The remaining scaling losses are in `reset` (1.6x on html5) and `intern`.

**Question 4: does the positions parameter make the scanning entry slower?**
Yes, by the criterion. Shape A of the prototype driver, stage time over five
interleaved rounds, noparam over base: ecma262 0.845 (least) and 0.860
(median), with the twin at 1.014; apollo11 0.924 and 0.925, twin 1.000. Both
are at most 0.93 and the twin is within 0.97 to 1.03 on both. On ecma262
every noparam round (1.86 to 1.96 s) is below every base round (2.20 to
2.24 s). Removing the parameter makes shape A's scan 18 percent faster on
ecma262 (more than the 14 percent recorded in `concurrency/DESIGN.md`) and 8
percent faster on apollo11. The positioned entries in the real stage keep
the parameter in use, and this measurement says nothing about their cost or
about how much of the stage the scanning entry accounts for; the mechanism
(argument passing through the eight functions, or what the compiler does
with them) is not determined.

**Findings** (not implemented):

1. Interning is the largest part that does not scale (20 to 21 percent of
   the four-worker stage on the two large pages, 1.1 to 1.2x scaling). If
   it scaled as the other parts do (2.1x), the four-worker stage would
   shrink by about 9 percent on ecma262 and html5 (an estimate from that
   assumption, not a measurement). Find which of its steps is sequential
   and partition it (sg-bl-02-29).
2. `sibling_positions` (`match.positions`) and the pseudo-element
   allocation (`match.allocation`) are sequential and together are 4.8
   percent of the ecma262 four-worker stage; whether the positions
   pass can be split was not examined. Neither is worth doing before
   interning.
3. Matching is 43 to 69 percent of the four-worker stage; a test costs 55
   to 109 ns. On ecma262 the filter keeps 88
   percent of the offered items, so there only the index (offering fewer
   items) or a cheaper test cuts the work; on html5 and apollo11 the filter
   already drops 40 to 44 percent (sg-bl-02-30 below).
4. Remove the positions parameter from the scanning chain, or find which
   part of it costs 8 to 18 percent, and measure the stage again
   (sg-bl-02-28).
5. The counters cost up to 3 percent of `match` when they count nothing
   (html5, sequential). They should stay out of the stage: keep a counting
   copy of `match_all` for the profiled path, or drop the counters once
   the investigation is done.

**Per board item.**

- sg-bl-02-28 (the 14 percent slower scan entry on ecma262): the positions
  parameter is a cause; removing it recovers more than the recorded 14
  percent in shape A on ecma262 and 8 percent on apollo11. Decided on
  hosted noise for ecma262 (0.845 against a twin at 1.014); apollo11's
  0.924 is 0.6 points inside the 0.93 bound and is not decided by this run.
  Not shown: the effect on the real stage, and the mechanism.
- sg-bl-02-29 (partition interning above 15 percent of the four-worker
  time): the rule fires on ecma262 (20.0 percent) and html5 (21.1 percent)
  and does not on apollo11 (12.9 percent). The failures hold on hosted
  noise. The hosted machine scales loops about 2x with four workers, so it
  understates the share a machine that scales them 4x would give; apollo11's
  pass is therefore not settled for the 14900K.
- sg-bl-02-30 (per-element candidate counts on apollo11): 76.8 offered per
  styled node on average (1,484 rules, so the index passes 5.2 percent of
  them), 46.1 admitted, 3.2 matched; the distribution of offered items per
  node (binary-digit buckets) is 49 nodes with 2 to 3, 31 with 4 to 7, 980
  with 8 to 15, 511 with 16 to 31, 6,246 with 32 to 63, 2,272 with 64 to
  127, 3,349 with 128 to 255 and 12 with 256 to 347. The most expensive node
  (347 offered) costs about 23 microseconds at 65 ns per offered item, 0.03
  percent of the 67.5 ms loop, so no node limits the loop's balance.
  Offered items per node are about those of html5 (77.9) despite
  3 times as many rules.

**What needs the 14900K, and what does not.** Each decision above was
made by the plan's prior criterion (a threshold and a spread rule) and holds
on hosted noise: question 1 on ecma262 and html5, question 4 on ecma262, and
the identity and counter checks, which are exact. No decision waits on the
14900K. Three conclusions are not settled by this run and need it only if
they must be stated precisely: apollo11 on question 1 (a machine that scales
four workers by 4x changes the shares), apollo11 on question 4 (0.924
against 0.93), and the empty-table cost of the counters (1 to 3 percent is
near this run's resolution). One 14900K run would settle all three:
`run.sh profile ecma262 html5 apollo11`, `RUNS_OVERHEAD=15 run.sh overhead`
and `ROUNDS=15 scan-param.sh time ecma262 apollo11` from this workflow with
`runs-on: [self-hosted, 14900k]` on the work branch (the 14900K is idle-checked
and announced to the other sessions first). The temporary workflow
`style-build-timing` can be removed when the owner does not want those
three; it must be removed before the branch is ready either way.

## Interning in parallel

Board item sg-bl-02-29. Interning was 20.0 and 21.1 percent of the
four-worker stage on ecma262 and html5 (above the item's 15 percent rule)
and scaled 1.1 to 1.2x from `seq` to `par4` ("Step timing" above). This
section was written before any code changed.

**What stays sequential, and why.** Both the full build (`intern_styles`)
and a restyle (`intern_nodes`) intern through `intern_values`, which makes
twelve calls, one per table: the seven value groups (box, size, spacing,
border, font, text, background), the custom-property sets (`canon_sets`) and
the container, item, table and content groups. The full ledger of run
38306217375 (artifact `style-step-timing-38306217375`, `ledger.txt`, pin
`wf-d837678c6905`) shows two things:

- Every adjacent pair of the twelve calls is permitted to overlap
  (`PAR permitted ./style/intern.wf:1627 pair(intern_box_group,
  intern_size_group) eligible`, and so on through `pair(intern_table_group,
  intern_content_group)`). The per-table parallelism the vocabulary tree
  decided (Q48, "each is interned as its own task in parallel") is written
  and admitted by the language.
- The compiler then drops the offer of each of the seven value groups:
  `PAR actualization style.intern_values call grain: omitted offer of
  style.intern_box_group (static work 35791 below 150000, no recursion)`,
  and likewise size 108,847, spacing 75,599, border 76,175, font 37,055,
  text 77,311 and background 33,183. The call grain prices a call by a
  static instruction count that charges each loop 16 times its body, not by
  the loop's runtime extent; each of these calls runs one loop over every
  styled node (179,471 elements on ecma262), so its runtime work is far
  above its static price. The seven therefore run one after another as
  ordinary calls. The other five have no such line and are offered.
  Whitefoot's call-offer grain investigation records this as the rule's
  known limit (a non-recursive helper whose work is large only through its
  runtime extents loses its offer), not exercised by any program it
  measured; this is such a program.

Inside one table the loop is denied (`PAR loop ./style/intern.wf:756 loop
denied condition 1: PAR-2 indexed accumulator ... at set index^.inner[at] =
narrowed;`). That order is a true dependency of the written algorithm: a
value's identifier is the position of the first equal value, so whether a
value is new depends on every value interned before it. The kept-state
decision (`design/pipeline/style.md`: each group's table keeps its
identifiers across edits and an edit appends the values not found) requires
only that existing identifiers do not move; the first-seen order among the
values one run adds is required by no decision, but it is what makes the
identifiers, and every output that exposes them, the same in every build, so
each candidate below keeps it.

Also sequential, outside the tables: the loop that copies each node's
identifiers into `styles.elements` and the pseudo-elements
(`intern.wf:1449`, denied because a `propagate` leaves it) and
`copy_families`; both copy, they do not hash or compare.

**Candidates and their dependency chains.** N is the number of nodes
interned, c_t the cost per value of table t, split into h_t (hashing, which
reads only the value) and p_t (probing, comparing with the table's entries
and appending, which reads the table as earlier values left it), W the
workers, S the preparation and assembly loops (split, N/W) plus the copy
loop above.

| candidate | chain |
|---|---|
| current, as compiled at the pin | S + sum over the seven value groups of N c_t, then the other five overlapped |
| A, per-table tasks (Q48, the code as written) | S + max over all tables of N c_t |
| B, A with each table's hashes computed first in a split loop | S + sum of N h_t / W + max of N p_t |
| C, A with each table cut into P hash partitions, first-seen identifiers restored by a prefix count | S + max of N c_t / P + N / W + a prefix count of N |

A changes no code; only the compiler's call grain stands between the source
and its chain. B keeps the tables' formats and kept state and adds one array
of N hashes per table. C needs each table's kept index cut into P indexes
kept across edits, a mark per node saying whether it was the first of its
value, a prefix count of those marks to give first-seen identifiers, and
writes from each partition to its own row of N slots (a range reference per
partition) gathered afterwards; it adds work of order N P.

**What each predicts for the four-worker share.** The step timing does not
split interning by table, so the per-table costs are not measured. The
static weights above (size 24.5 percent of the seven value groups' sum;
text, border and spacing 17 percent each) are a proxy for their relative
cost per value. To reach 15 percent, interning at `par4` must fall from
114.9 to at most 81.4 ms on ecma262 (0.15/0.85 of the other parts' 461.1 ms)
and from 69.8 to at most 46.1 ms on html5 (of 261.0 ms). Assuming the seven
value groups run at their sequential speed today, A shrinks them to the
larger of their largest table and their sum over the effective cores: about
half their time on the hosted runner (two physical cores), about a quarter
on a machine that scales four workers 4x, since the size group is about a
quarter of them. A therefore passes the rule on the hosted runner only if
the seven value groups take at least 67 of ecma262's 135.4 ms of sequential
interning (49 percent) and 47 of html5's 84.7 ms (56 percent); on a machine
that scales four workers 4x, at least 45 and 32 ms (33 and 37 percent). B
further removes the hashing from each table's chain; C divides the largest
table's chain by P. Which is needed depends on that breakdown, which the
profiled path does not yet record.

**The falsifier.** A change is rejected, by the item's rule, when interning
at `par4` stays above 15 percent of `total` on ecma262 or html5 (least of
three processes, the same spread rule as question 1 above), or when, in a
same-compiler, interleaved before-and-after comparison with a second copy of
the base build as twin (as `scan-param.sh` does), the change's `par4`
interning time is within the twin's spread of the base's, or its `seq`
interning time is slower than the base's by more than the twin's spread. A
build whose ledger still shows an `omitted offer of style.intern_*_group`
line does not test A, whatever its times. Every change keeps the profiled
dump equal to MODE `dump`'s and to the base's, byte for byte, on the three
pages.

**Result.** Not implemented. The natural parallel form, A, is the code as
written and is permitted; the compiler's call grain does not hand it out.
Writing the twelve calls in another shape to cross the grain, or building
with `--par-call-grain off` (which offers every small call too), would route
around a Whitefoot gap, so the gap goes to Whitefoot with this witness (a
fragment, not a standalone program):

```text
fn intern_words(table: &Box<Slots<u64>>, index: &Box<Array<u32>>, values: &[u64], ids: &[u32]) -> result: unit reads(values), writes(table), writes(index), writes(ids) {
  doc "One counted loop over values^.len: hash, probe index, append to table when new, write the identifier.";
  ...
}

intern_words(table: &first_table, index: &first_index, values: &first_values.inner[0_u64..count], ids: &first_ids.inner[0_u64..count]);
intern_words(table: &second_table, index: &second_index, values: &second_values.inner[0_u64..count], ids: &second_ids.inner[0_u64..count]);
```

The two calls write disjoint places, so [PAR-1] admits their overlap, as
the ledger shows for the twelve calls of `intern_values`; the call grain
then omits the offer whenever the static work of the loop is below 150,000
units, which does not depend on `count`, so the pair runs sequentially at
every worker count. The fragment has not been compiled alone; the observed
case is `intern_values` at the pin. Acceptance: with `count` at 10^6 the pair is offered (no
omitted-offer line for it) and its four-worker time on the 14900K is at
most 0.6 of its sequential time, while with `count` at 3 it costs no more
than the sequential build within the noise floor. Whitefoot's planned
on-demand phase keeps the static call grain (owner's ruling of 2026-10-10,
with runtime feedback per call site to follow if a static estimate
misjudges a call); this is such a misjudged call.

### Per-table breakdown

The predictions above need each table's cost, which the step timing does not
record. `pkg::style::intern_styles_profiled` repeats `intern_styles` and
`intern_values` step by step, with a reading of the clock between steps and
each table's call between two readings, so the twelve calls run one after
another. MODE profile runs it after the stage, on the same second and third
parts, and prints its 24 steps: `intern.prepare` (completing the text, table
and content groups), `intern.setup` (the empty result, identifier arrays and
side stores), one step per table (`intern.box` through `intern.content`,
`intern.custom` being the custom-property sets), `intern.ids` (assembling
each node's identifiers), `intern.place` (placing them by element and
pseudo-element, and the families), `intern.whole`, and then `hash.box`
through `hash.background`: each of the seven hashed groups' values hashed
alone in a loop whose iterations are independent, which is B's first step.
The stage's own `intern` step is unchanged. MODE profdump now interns
through this copy, so its byte-for-byte equality with MODE dump checks that
the copy builds the stage's styles. `run.sh profile` adds a summary per page
and mode: `intern.whole`, the seven value groups' sum, the other five's,
the largest table, the rest (S), the seven hashes' sum and the stage's
`intern`.

**Rules, fixed before the run.**

- The breakdown stands for the stage when `intern.whole` in `seq` is within
  25 percent of `intern` in `seq` on each page (the bound question 3 used
  for steps run alone); otherwise its shares are not used.
- A's prediction is the one above: on the hosted runner the seven value
  groups (`groups7_ms`, `seq`) must reach 67 ms on ecma262 and 47 ms on
  html5 for A to bring interning to 15 percent.
- B is worth doing when the seven groups' hashing (`hash7_ms`, `seq`) is at
  least 20 percent of `intern.whole` (`seq`) on both ecma262 and html5:
  hashing then leaves the sequential chain and cuts at least 10 percent of
  interning on the hosted runner (half of it, at two physical cores), above
  the 7 percent spread of the step timing, and 15 percent at a true 4x. Below
  20 percent on either page, B is not done.
- C is what A would need when the largest table is more than half of the
  twelve tables' sum (`largest_ms` against `groups7_ms` plus `others5_ms`),
  since per-table tasks then leave that table as the chain.

**Results.** Workflow `style-build-timing`, hosted run 38314107962 at
b96ca9b, pin `wf-d837678c6905`, on GitHub-hosted `ubuntu-24.04` (the
limits of "Step timing" apply: four workers on two physical cores, least of
three processes). Milliseconds; `seq` is the sequential build, `par4` four
workers:

| page | intern.whole seq | stage intern seq | groups7 seq | others5 seq | largest table | hash7 seq | hash7 par4 |
|---|---|---|---|---|---|---|---|
| ecma262 | 146.9 | 133.5 | 73.1 | 55.4 | container 24.9 | 40.9 (27.8%) | 16.9 |
| html5 | 83.9 | 82.2 | 44.1 | 34.3 | container 15.5 | 25.4 (30.3%) | 10.6 |
| apollo11 | 10.2 | 9.8 | 5.2 | 4.1 | container 1.7 | 2.8 (27.6%) | 1.2 |

`hash7`'s percentage is its share of `intern.whole` in `seq`.

- *The breakdown stands.* `intern.whole` is within 25 percent of the
  stage's `intern` on every page (1.10, 1.02 and 1.04 times it).
- *A's prediction fails on html5 and holds on ecma262.* The seven value
  groups take 44.1 ms on html5, under the 47 ms A needs there, and 73.1 ms
  on ecma262, above the 67 ms it needs. A is blocked anyway on Whitefoot's
  call grain (board request sg-req-call-grain-runtime-extent); it is not
  reached by reshaping the calls or building with `--par-call-grain off`.
- *B is worth doing.* The seven groups' hashing is 27.8 percent of
  `intern.whole` on ecma262 and 30.3 percent on html5, above the 20
  percent rule on both, and alone it scales 2.4x from `seq` to `par4` on
  both pages.
- *C is not needed.* The largest table, container (one of the five tables
  that are not hashed here), is 19.4, 19.8 and 18.3 percent of the twelve
  tables' sum on the three pages, under half of it.

### Hashing outside the chain (B)

Written before the code changed.

**The chain today.** Each of the seven value groups' interning functions
(`intern_box_group` through `intern_background_group`) runs one counted
loop over the N nodes it is given. Iteration i hashes value i, probes the
table's open-addressing index with that hash, compares with the entries it
finds and, when none is equal, appends the value and gives it the next
identifier. The loop is denied (an indexed accumulator: the index and the
table), so hashing and probing alternate in one sequential chain of N
steps, and the seven calls run one after another (the call grain omits
their offers). Per table the chain is N (h_t + p_t); for the seven,
S + sum over t of N (h_t + p_t).

**The chain with B.** Each of the seven functions first fills an array of
N hashes in a counted loop whose iteration i reads only value i and writes
only slot i (`hash_box_values` through `hash_background_values`), then runs
the probe loop as before, reading hash i from that array instead of
computing it.

- *Stays sequential:* the probe and append loop, in first-occurrence order.
  Whether value i is new depends on every value interned before it, and the
  identifiers are the positions of the first equal values; that order is
  what makes them the same in every build and keeps an edit's identifiers
  stable (the kept-state decision). The index's growth (`index_*_group`,
  which places the table's earlier values again, and on a full build has
  none to place), the five other tables and the assembly loop are
  unchanged.
- *Leaves the chain:* the hashing. Each table's chain becomes
  N h_t / W + N p_t, and the seven together S + sum over t of
  (N h_t / W + N p_t) while the call grain keeps them sequential, or
  S + max over t of (N h_t / W + N p_t) once Whitefoot offers them (A).
- *Costs:* one array of N 64-bit hashes per table call (1.4 MB on ecma262),
  one store and one load per value, and a fork and join per table at
  `par4`.

**What B predicts.** On the hosted runner the seven groups' hashing took
40.9 ms in `seq` and 16.9 ms at `par4` on ecma262 (25.4 and 10.6 on html5),
so B should take about 24 ms off ecma262's `par4` interning and about 15 ms
off html5's, if the probe loops keep their speed. Against the `par4`
interning of "Step timing" (114.9 and 69.8 ms) that is about 91 and 55 ms,
still above the 81.4 and 46.1 ms the 15 percent rule needs: B alone is not
predicted to bring interning within 15 percent on the hosted runner, and the
rest stays with A. In `seq`, B does the same hashing plus a store and a load
per value, so it should be within the noise of the base.

*Tested by the results below; it is partly wrong there.*

**The comparison and the falsifier.** `run.sh compare` times the base
build (b96ca9b), the change and a copy of the base's binary (the twin), all
built by the same compiler, in interleaved rounds whose order rotates, and
reads the stage's own `intern` step and `total` from MODE profile, `seq` and
`par4`, on ecma262, html5 and apollo11; each build's time is its least over
the rounds. The twin's spread is how far its time lies from the base's. By
the rules of "The falsifier" above, B is rejected when its `par4` interning
is not below the base's by more than the twin's spread, or when its `seq`
interning is slower than the base's by more than the twin's spread, on
ecma262 or html5; the 15 percent clause is reported as well and, as
predicted above, is not expected to pass with B alone. The ledger must
permit each of the seven hashing loops, and the per-table calls' call-grain
lines are compared between base and change so that a change in which calls
are offered, which would mix A into the measurement, is seen. The profiled
dump must equal MODE `dump`'s and the base's byte for byte on the three
pages (`run.sh profile`, the `profile` job).

**Results.** Hosted run 38316806349 at 945d0b1, job "interning before and
after hashing leaves the chain", on a GitHub-hosted runner with two physical
cores, not the 14900K. Five interleaved rounds; base b96ca9b, change
945d0b1, twin a second copy of the base. Times are the stage's `intern` step,
least of five, in milliseconds; "twin spread" is how far the twin lies from
the base:

| page | mode | base | change | twin | change vs base | twin spread | interning share of `total` |
|---|---|---|---|---|---|---|---|
| ecma262 | seq | 73.348 | 68.306 | 72.472 | -6.9% | 1.2% | |
| ecma262 | par4 | 66.848 | 40.290 | 66.075 | -39.7% | 1.2% | 13.9% (base 21.1%) |
| html5 | seq | 48.196 | 45.152 | 47.695 | -6.3% | 1.0% | |
| html5 | par4 | 40.774 | 27.000 | 39.755 | -33.8% | 2.5% | 15.4% (base 21.4%) |
| apollo11 | seq | 5.363 | 5.027 | 5.326 | -6.3% | 0.7% | |
| apollo11 | par4 | 4.968 | 3.286 | 5.002 | -33.9% | 0.7% | 9.5% (base 14.2%) |

The identity checks passed: MODE `dump`, `profdump` in `seq` and `profdump` in
`par4` equal the base's byte for byte on all three pages, and the ledger
permits the seven hashing loops. The call-grain lines of the seven
`intern_*_group` calls are unchanged (the offers stay omitted), so A is not
mixed into the measurement.

Verdicts, by the falsifier fixed above:

- *B is kept.* On ecma262 and html5, `par4` interning is below the base's
  by 39.7 and 33.8 percent, far beyond the twin's spread (1.2 and 2.5
  percent), and `seq` interning is not slower than the base's but 6.9 and
  6.3 percent faster, beyond the spread as well. This run does not explain
  the `seq` gain; the prediction expected no change.
- *The 15 percent rule is met on ecma262 and not on html5.* Interning is
  13.9 percent of ecma262's four-worker `total` (base 21.1 percent) and 15.4
  percent of html5's (base 21.4 percent). On html5 it is short by under 1
  ms of its 27.0 ms (derived from the shares, with the other parts unchanged).
- *The prediction written before the run is partly wrong.* It said B alone
  fails the 15 percent rule on both pages, with `par4` interning about 91 ms
  on ecma262 and about 55 ms on html5. The rule fails on html5 as predicted
  and holds on ecma262, and the measured `par4` interning is 40.3 and 27.0
  ms. The two sets of milliseconds are not on one basis: the prediction
  subtracted the hashing's saving from the 114.9 and 69.8 ms of "Step timing",
  measured in another run, while this run's base takes 66.8 and 40.8 ms; the
  base's shares of `total` (21.1 and 21.4 percent) agree with that earlier
  run's (20.0 and 21.1 percent). Compared by saving, the prediction expected
  about 24 and 15 ms off `par4` interning, and the run shows 26.6 and 13.8
  ms off, from a smaller base.
- *What remains.* Reaching 15 percent on html5 is A, which waits on
  Whitefoot's call grain (board request sg-req-call-grain-runtime-extent).
- *Not yet done.* The board item's completion condition measures on the
  14900K; this run was the hosted runner, with two physical cores, where
  four workers cannot scale 4x. The 14900K run is still to do.

## Owner rulings

- **2026-10-02, Q64, the level cascade,** written in Chinese after the
  handoff of mbbill/Snowghost#28: approved as recommended; the stage's
  second part computes the inherited values level by level.
- **2026-10-02, Q61.** Where the HTML Standard and Chromium differ, Snowghost
  follows Chromium: the user-agent sheet gives Chromium's computed values.
  This supersedes the 2026-10-01 choice to keep the Standard's sheet for
  `table { border-color: gray }` and the second batch's choice for
  `ol, ul, menu { counter-reset: list-item }`.

- **2026-10-01, scope.** The scope, oracle and criteria above, with flex,
  grid and generated content in the second batch.
- **2026-10-01, Q46 to Q50**, after the owner asked whether the
  recommendations were right for parallelism and the first `var()`
  recommendation, a cache shared across elements, was withdrawn for adding
  an order the cascade does not need:
  - Q46: `matching_specificity` in `pkg::css::selectors`;
  - Q47: `var()` substituted where its result is needed, with no shared
    cache;
  - Q48: eight computed-value groups, interned in parallel;
  - Q49: percentages and `calc()` with percentages stay unresolved until
    layout;
  - Q50: the stage in three parts, the pass in document order holding only
    what depends on the parent.
  The tree records Q47, Q48, Q49 and Q50 in `design/pipeline/style.md` and
  `design/vocabulary.md`. The owner also asked that `AGENTS.md` require every design
  choice to start from its candidates' dependencies (mbbill/Snowghost#25).
- **2026-10-01, the three choices after the results**, written in Chinese
  after the handoff of mbbill/Snowghost#24: keep the HTML Standard's
  user-agent sheet without Chromium's `table { border-color: gray }`;
  resolve `ex` and `ch` from the default fonts' metrics, provisionally;
  round a computed length to `LayoutUnit` when layout reads it. The owner
  also approved the tree changes of `design/pipeline/style.md` and
  `design/vocabulary.md`.
