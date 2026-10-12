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

## Where the scanning entry's extra time goes

Question 4 of the step timing found shape A 15.5 percent faster on ecma262
without the positions parameter (noparam over base 0.845 least, 0.860
median, twin 1.014) and left the mechanism open. One slice parameter passed
down eight functions should cost a few instructions per call. This
experiment finds where the difference lies before anything is removed,
because the answer decides who acts: a form Whitefoot compiles poorly is a
Whitefoot gap, reported with a minimal witness and not routed around; a cost
in Snowghost's own code is Snowghost's to fix.

**What the patch changes besides the parameter.** In base, the scanning
entry `selector_matches` passes an empty slice of a local one-word array
down the chain, and every leaf that reads the table tests at run time
whether the table covers the node: the class test calls `class_records` (a
length test; the indexed loop's code stays in the function), and the edge
and `:nth-*` tests call `positioned_scan` through `count_siblings`. In
noparam those leaves build their own empty slice, so the compiler sees a
length of zero and can delete the lookups and the class test's indexed
branch. The timed comparison therefore mixes passing the parameter with
compiling the lookups in; the per-function and per-instruction counts below
separate the two.

**Measurement.** The temporary workflow `style-scan-cost` on a hosted
`ubuntu-24.04` runner with the pin's compiler runs `scan-param.sh build`,
`check ecma262`, `build-par`, `disasm`, `emit` and `callgrind ecma262`.
Callgrind counts executed instructions (Ir) exactly, per function and per
instruction address, and simulates a cache and a branch predictor. Shape A's
stage is the `A 1` run minus the `A 0` run of the same binary, function by
function. Base's binary profiled a second time (twin) is the control: its
stage Ir must equal base's within 0.1 percent, or the counts are not
deterministic enough to attribute a difference to functions. Below, r_time
is 0.845, the hosted time ratio noparam over base (question 4); r_Ir is the
stage's Ir ratio noparam over base; ΔIr is base's stage Ir minus noparam's
(`scan-cost.py` prints noparam minus base, negative when noparam executes
fewer); and the chain is the functions `scan-param.sh` names, from `selector_matches`
down to the leaf tests and the lookups `class_records` and
`positioned_scan`.

**Hypotheses and what decides each**, fixed before the run:

1. *Not instructions.* The time goes to code placement, alignment, memory
   or branch prediction, not to executed instructions. It holds when r_Ir is
   at least 0.97 (instructions explain at most a fifth of the 15.5 percent)
   and is rejected when r_Ir is at most 0.90 (they explain at least two
   thirds); between the two, both contribute. Where instructions do not
   explain the time, the simulated data-cache misses (D1mr, D1mw, DLmr,
   DLmw) and mispredicted branches (Bcm, Bim) of the stage say whether
   memory or prediction carries the rest; if they too agree within the
   twin's spread, the rest is placement, which callgrind cannot see and the
   14900K's hardware counters would, in a later run.
2. *Argument passing through calls that stay calls.* The chain's functions
   are separate machine functions in both builds, and each call carries the
   slice's two words, moved, spilled and reloaded around inner calls. It
   predicts the same executed chain symbols in both binaries, call counts
   equal within 0.1 percent, and the chain carrying at least 80 percent of
   ΔIr spread over several functions, each at most 12 instructions per call
   more in base; the annotated disassembly shows the difference at argument
   moves, spills and reloads. It is rejected when one function carries more
   than half of ΔIr at more than 12 instructions per call, or the chain
   carries less than half of ΔIr.
3. *Different inlining.* The parameter changes what the ThinLTO link
   inlines. It predicts a chain function that is an executed machine
   function in one build and not in the other, or whose call count differs
   by more than 1 percent, with ΔIr concentrated at that boundary (calls,
   prologues, epilogues). It is rejected when both binaries execute the same
   chain symbols with call counts within 0.1 percent.
4. *A check per iteration or per call.* Whitefoot emits, for the slice
   parameter, a bounds, alias or overlap test that runs on every call or in
   a loop: `compound_matches`' loop over simple selectors, `list_matches`'
   loop over alternatives, `match_complex`'s walk, `nth_scan`'s loop over
   siblings. It predicts that the emitted IR of a chain function in base
   (before LLVM optimizes it) compares or branches on the positions pointer
   or length outside `class_records` and `positioned_scan`, that the
   optimized code keeps the test in a loop, and that the function's
   difference per call grows with its loop's trip count. It is rejected when
   the emitted IR of each chain function differs between the builds only in
   the parameter list, the arguments passed on and the lines the patch
   changes in the source.
5. *The lookups the patch folds.* Snowghost's own code: the scanning entry
   passes a table that is empty only at run time, and the lookups run on
   every class and structural test. It predicts `class_records` and
   `positioned_scan`, or their inlined instructions (the slice's length test
   and the class test's indexed branch), executed in base and absent from
   noparam, and those instructions in base's annotated disassembly summing to
   at least a quarter of ΔIr. It is rejected when they carry less than a
   quarter of ΔIr.
6. *Parallel captures.* The sequential build has no parallel loop, so
   captures cannot explain its difference. The `--par` ledgers of base and
   noparam (`build-par`) and the `--par` profiles say whether the parameter
   changes what a `--par` build's loops capture or execute; equal ledgers
   reject it for `--par` builds.

Hypotheses 2 to 5 can hold together; the attribution gives each its share
of ΔIr. What each outcome means for who acts: 3 or 4 is a Whitefoot gap
(inlining, or a check emitted for the natural form), filed with a minimal
witness; 5 is Snowghost's code, or an artifact of the patch rather than of
the parameter, and is answered in Snowghost or by timing a patch that keeps
the lookups; 2 alone is the ordinary cost of an argument through calls that
are not inlined, and whether Whitefoot should inline or specialize those
calls is a question for the owner; 1 needs the 14900K.

**Limits.** Callgrind counts instructions and simulates a generic two-level
cache and branch predictor, not the hosted CPU, and measures no time, which
is why r_Ir is compared with an r_time measured separately. The optimized IR
in `emit` is the emitted module after a whole-module `clang -O2`, not after
the build's ThinLTO link; the disassembly of the linked binaries is what
runs. The `--par` profiles run four workers serialized by valgrind, so
their totals include scheduling, while their chain's per-function counts do
not depend on it.

### Results

**Run.** Workflow `style-scan-cost`, run 38312337441 at 97eeaf7, pin
`wf-d837678c6905`, hosted `ubuntu-24.04` on an AMD EPYC 7763, clang 22.1.8,
valgrind 3.22.0. The three sequential builds print the same check on ecma262
(179,471 elements, 336 rules, checksum fae8a9b77c6b818a), and the twin is
base's binary byte for byte. Shape A calls `selector_matches` 179,471 x 336 =
60,302,256 times per repetition.

**A defect in the first run.** `profile_run` assigned its fifth argument to
the caller's variable, so after the first `--par` run the sequential `A 1`
runs were recorded without the cache and branch simulators (Ir only) while
the `A 0` runs had them. Instruction counts are unaffected; the simulated
misses that hypothesis 1 reads are missing. The script now keeps the
options in its own variable, and `scan-cost.py compare` refuses four
profiles whose events differ.

**Twin.** Base and twin have the same stage Ir, 17,117,359,662, and every
function's count is equal (`compare-twin.txt`). Counts are deterministic,
so a difference between base and noparam is the builds'.

**r_Ir.** Base 17,117,359,662, noparam 15,486,307,786: r_Ir = 0.9047 and ΔIr
= 1,631,051,876, 27.05 instructions per `selector_matches` call out of
283.86 (9.5 percent). The `--par` builds give the same ratio, 0.9047, and the
same per-function differences.

**Where ΔIr lies** (base minus noparam, stage only; calls are equal in both
builds unless named):

| function | ΔIr | share | per call |
|---|---:|---:|---:|
| `match_complex` (106,853,532 calls) | 784,372,654 | 48.1% | 7.34 |
| `style_element` (holds the inlined `selector_matches` and `list_matches`) | 698,789,055 | 42.8% | 6 per `match_complex` call + 1 per `selector_matches` call |
| `instr_matches` (115,247,629 calls) | 140,339,980 | 8.6% | 1.22 |
| `class_records` (966,416 calls in base, none in noparam) | 5,798,496 | 0.4% | 6 |
| `nth_scan` (91,763 calls) | 1,379,499 | 0.1% | 15.0 |
| `nth_of_type_matches` (7,596 calls in base, inlined in noparam) | 372,204 | 0.0% | 49 |

These six sum to ΔIr exactly. `selector_matches`, `list_matches` and
`compound_matches` are inlined in both builds, so `compare-seq.txt`'s
"chain share" (0.5716) leaves out `style_element`, which holds the first two;
the annotated disassembly below accounts for all of `style_element`'s
difference.

**What the extra instructions are** (annotated disassembly of the linked
binaries):

- `style_element`, per call of `match_complex` (106,310,750 calls), 19
  instructions in base against 13 in noparam. Base passes the empty table in
  `rcx` (`lea 0x60(%rsp),%rcx`) and `r8` (`xor %r8d,%r8d`), which moves
  `comp_end`, the target's address and the context's address onto the stack
  (`sub $0x8,%rsp`, three `push`es, `add $0x20,%rsp`). Noparam passes
  `comp_end` in `r8`, the target's address in `r9` and only the context's
  address on the stack (`lea 0x30(%rsp),%rax; mov %rax,(%rsp)`). The
  remaining instruction per `selector_matches` call is
  `movq $0x0,0x58(%rsp)`: the scanning entry's one-word empty array,
  written on every call (60,302,256 instructions, 3.7 percent of ΔIr).
- `match_complex`, on its common path (the subject's first simple selector
  fails), 66 instructions in base against 59. Base receives nine argument
  words, so it loads `comp_end` and the target's address from the stack
  (`mov 0x370(%rsp),%r14d`, `mov 0x378(%rsp),%rax`), keeps `atoms` and the
  table's two words in stack slots (`mov %rdx,0x18(%rsp)`,
  `mov %rcx,0x20(%rsp)`, `mov %r8,0x28(%rsp)`), and before each call of
  `instr_matches` reloads all three and pushes two stack arguments
  (`push 0x380(%rsp)`, `push %rax`, then `add $0x10,%rsp`): 24 instructions
  per call of `instr_matches` against 19.
- `instr_matches` receives eight argument words in base, six in noparam, and
  loads the two from the stack in its prologue (`mov 0x88(%rsp),%r12`,
  `mov 0x80(%rsp),%rbx` against `mov %r9,%rbx`): one more instruction on all
  115,247,629 calls; the remaining 25,092,351 lie in its class and
  structural arms.

**The hypotheses by their rules.**

1. *Not instructions*: neither holds nor is rejected. r_Ir = 0.9047 lies
   between 0.90 and 0.97. Executed instructions explain 61 percent of the
   hosted time difference by the least times (1 - 0.9047 = 0.095 against
   1 - 0.845 = 0.155) and 68 percent by the medians (against 1 - 0.860). The
   rest is not decided: the simulated misses were not recorded (the defect
   above). The added instructions are stack stores, loads, pushes and stack
   adjustments on the call path, which may cost more than the average
   instruction; that is a guess, not a result.
2. *Argument passing through calls that stay calls*: holds. The chain,
   counting the inlined `selector_matches` and `list_matches` in
   `style_element`, carries all of ΔIr; the largest single function carries
   48.1 percent, under half; the per-call differences are 1.22 to 7.34 in
   the functions called on every test (15 and 49 in two rare leaves with
   91,763 and 7,596 calls, together 0.1 percent of ΔIr); and the
   disassembly shows the difference at argument moves, stack arguments,
   spills and reloads. The two table words push the argument count of
   `match_complex` from seven words to nine and of `instr_matches` from six
   to eight, past the six integer argument registers of the x86-64 C calling
   convention that Whitefoot's calls use.
3. *Different inlining*: not rejected by its rule, but it carries at most 2
   percent. `class_records` (966,416 calls) and `nth_of_type_matches` (7,596
   calls) are calls in base only. In noparam `class_records` is gone because
   its argument is a constant empty table, and `nth_of_type_matches` is
   inlined because it shrank: both are consequences of hypothesis 5's
   folding. The main chain's boundaries are the same in both builds:
   `match_complex`, `instr_matches`, `nth_scan` and `backtrack` are calls
   with equal counts, and `selector_matches`, `list_matches` and
   `compound_matches` are inlined in both.
4. *A check per iteration or per call*: rejected. In base's emitted IR the
   table's two words are used outside calls only to pack them into a pair at
   each function's entry, in phis that carry the pair through loops
   (`compound_matches`, `list_matches`, `match_complex`, `nth_scan`,
   `nth_qualifies`, `count_siblings`), and in the reads of its length in
   `class_records`, `positioned_scan` and the class test
   (`%v136 = extractvalue { ptr, i64 } %v3, 1` in `instr_matches`, the line
   `let length = positions^.len;` the patch changes). `match_complex`'s loop
   in the binary compares nothing on the table; it only reloads its words
   for the next call.
5. *The lookups the patch folds*: rejected. `class_records` (5,798,496),
   `nth_of_type_matches` (372,204), `nth_scan` (1,379,499) and all of
   `instr_matches` beyond its one prologue instruction per call (25,092,351)
   together are at most 32,642,550 instructions, 2.0 percent of ΔIr, against
   the quarter the rule requires.
6. *Parallel captures*: rejected for `--par` builds. With line numbers
   removed, the two `--par` ledgers differ only in the statement pairs and
   chains of the lines the patch adds or edits (the `array_filled` lets, the
   positioned entry's `length` let and `list_matches` calls); no loop's
   verdict or captures differ, and the `--par` profiles repeat the
   sequential ratio.

**Who acts.** The cost is not in Snowghost's own code (hypothesis 5 is 2.0
percent; the scanning entry's empty-array store another 3.7 percent) and not
a check Whitefoot emits (4) or a change of inlining (3). It is the cost of
two more argument words on every call of a matcher chain that is not inlined
(2). Whitefoot compiles this signature as a C compiler would compile the
same nine-word signature. What makes the cost Whitefoot's question is that a
Whitefoot writer cannot write the form that avoids it: a record of the
chain's borrowed inputs (list, document, atoms, table) passed as one
reference is refused, because no stored position may hold a reference kind
[TYPE-8, GRAM-3], so every borrowed input of a recursive read-only chain is
its own argument, a range reference two of them, and the calls use the C
convention's six integer argument registers. Small copy records also cross
calls as pointers to stack copies: `NodeId` (one `u32`) and `MatchContext`
are `ptr %wf.arg.vN` parameters with no `readonly`, `dereferenceable` or
`noalias` facts, which the compiler's parameter ABI gives every stored
aggregate, while a small aggregate result already returns in registers.
Removing the parameter from the chain, or a scan-only copy of the chain,
would route around this and is not done; the gap goes to Whitefoot with a
minimal witness, and the owner decides the direction (a record of borrowed
references, a calling convention with more argument registers for
Whitefoot's own calls, or accepting the cost). Snowghost's one local item is
the scanning entry's per-call empty array (3.7 percent of ΔIr), which goes
away with whatever form the table takes and is not worth a change alone.

**What kinds the extra instructions are.** Sorting the annotated
disassembly's differences above by what each instruction does, per
`match_complex` call on the common path (about 14.7 instructions: 6 in
`style_element`, 7.34 in `match_complex` and 1.22 on each of 1.08
`instr_matches` calls; 1.77 `match_complex` calls per `selector_matches`
call and the empty-array store give the 27.05): about 9 are
stack-argument traffic, the arguments past
the sixth word (`style_element`'s `sub`, pushes and `add` against
noparam's one store, 4; `match_complex`'s two incoming loads and its two
pushes and stack adjustment at the `instr_matches` call against noparam's
register moves, 4; `instr_matches`' incoming load, 1); 2 set up the
table's own two words at the `match_complex` call (`lea`, `xor`); and
about 3 carry those two words across the `instr_matches` call
(`match_complex` spills them on entry and reloads both before every call,
since its six callee-saved registers already hold other inputs). This is
read from the instructions, not measured by removing each part: a calling
convention with more argument registers would by this reading remove the
first kind and leave the other two, about 5 per call, and one record of
borrowed references would remove all three.

**Witness.** The first `witness-argument-words.wf` in this directory
reduced the chain to two mutually recursive read-only functions, `step` (a
loop over a range of items, as `match_complex` and `compound_matches`) and
`test` (one item, recursing into `step` for a nested range, as
`instr_matches` does for `:not()`), that thread three borrowed records, an
`Id` (one word), a `Context` (two `Option<Id>`) and, in the `with` copy
only, an empty table of a local one-word array they forward and read in one
rare arm. The two copies give `step` nine argument words against seven and
`test` eight against six, as in the renderer. `scan-param.sh witness` builds
it as the renderer is built (function fragments, ThinLTO), requires both
copies to count the same matches, and prints each copy's calls and
instructions per call under callgrind with their disassembly. Its
prediction, written before it was built and tested by the run below: the
`with` copy's `step` and `test` execute more instructions per call than the
`without` copy's, by about the renderer's 7 and 1, at the argument moves,
stack arguments and reloads. Acceptance depends on the direction chosen:
with a record of borrowed references, the witness rewritten to pass one
such record keeps its per-call instructions when the table joins the
record (within 1 per call); with a different calling convention for
Whitefoot's own calls, the `with` copy costs at most 2 more instructions
per `step` call and 1 per `test` call than the `without` copy; and either way
shape A on ecma262 then gives r_Ir of at least 0.98 under this experiment.

**The first witness's result.** Run 38314756318 at 83bf352 (the same
workflow, runner and pin) built it; both copies count the same matches.
The prediction failed: `step_with` executes 52.62 instructions per call and
`step_without` 55.32 (1,114,112 calls each), so the `with` copy is 2.7
cheaper, and neither `test` copy has a callgrind row. The reason is the
witness's shape, not the argument words:

- *`test` is inlined into `step`.* `step_with`'s only call is to itself
  (the inlined `:not()` arm, 65,536 calls) and the same holds for
  `step_without`; `wf_test_with` and `wf_test_without` stay in the binary
  with `step` inlined into them and are never called. So the call that
  carries most of the renderer's cost, a nine-word function calling an
  eight-word one on every loop iteration, never runs. `test` is small
  enough for LLVM to inline; the renderer's `instr_matches` has 36 arms
  (1,181 instructions) and two call sites (the subject and the ancestor walk of
  `match_complex`) and stays a call.
- *The callee's side can come out cheaper.* What remains per call is
  `step`'s entry and one inlined test. `step_with` loads three stack
  arguments, `step_without` one, but `step_with` keeps `words` and `keys`
  in the registers they arrive in and reloads `id` and `context` from the
  caller's argument area only after the rare recursive call, while
  `step_without`, with `id` arriving in a register, spills `words` and
  `keys` to its own frame (frame 0x28 against 0x18) and reloads both on
  every test: 20 instructions per failing class test against 23 (the two
  reloads and a jump), and 23 instructions of entry against 24. Arguments read but never written can be reloaded from
  the slots the caller wrote, so on the callee's side words past the sixth
  cost nothing fixed; the difference follows each function's register
  allocation.
- *The caller's side is where the cost is, and the first witness did not
  report it.* `main`'s loop around the call (read from the profile's
  per-instruction counts against `main`'s disassembly) runs 20 instructions
  per call of `step_with` against 18 per call of `step_without`: the table's
  two words and two more pushes, less two register moves. Net per
  top-level call the `with` copy is about 0.7 instructions cheaper.

**Hypothesis 2 after the first witness.** It still stands for the renderer:
its grounds are the renderer's own annotated disassembly and exact counts,
which the witness does not touch, and the witness failed because it lacked
the renderer's call of `test` from `step`, not because its argument words
cost nothing. What the evidence shows is where the renderer's extra
instructions are and what kinds they are (above). What it is only
consistent with: that these instructions cause the 61 to 68 percent of the
time difference that their share would predict, and how much each remedy
would remove (the reading above, not a measurement). The first witness adds
one constraint: the cost is not a fixed price per argument word past the
sixth, but the caller's re-passing of every word on every call in a loop
and the callee's carrying of the words across its own calls.

**The second witness.** `witness-argument-words.wf` now reduces the chain
with the renderer's call graph: `main` (as `style_element`) loops over
256 rules for each of 4096 elements and calls `step` (as `match_complex`,
nine words against seven), which tests the subject compound and then walks
ancestors for the earlier compounds through `compound` (as
`compound_matches`), from two places, and `compound` calls `test` (as
`instr_matches`, eight words against six) for each simple selector. `test`
matches a six-variant enum passed as the renderer passes `Instr`: a tag,
the element's two classes, its index, the context's first id, first child
(the `with` copy reads the empty table first, as the positioned lookups
do) and a negation that recurses into `step`. Most rules fail at the
subject's first class test, as shape A's do. Its six arms are the
renderer's common ones, which is also what keeps `test` a call; the
script now fails when `test` is never called, since such a witness lacks
the renderer's shape, and prints `main`'s instructions at each copy's call.
Prediction, before it is built: both `test` copies are called, with equal
call counts in the two copies; `step_with` executes at least 4 more
instructions per call than `step_without` (renderer 7.34) and `main` at
least 2 more per call of `step_with` than of `step_without` (renderer 6;
the first witness's `main` gave 2),
the extra instructions in the annotated disassembly being stack-argument
pushes and loads and reloads of the table's words. `test`'s difference is
reported without a threshold (renderer 1.22), since the first witness
showed a callee's side moving by 3 with its register allocation. A
difference of `step` between 2 and 4 reproduces part, and the annotated
difference names the kinds missing. If `test` is called and `step`'s
difference is under 2, the renderer's cost depends
on more than the arity and the call graph, most likely `match_complex`'s
other state live across the call (its backtracking stack and walk
variables), and that is the next reduction. The acceptance by direction
above then applies to this witness.

**Not settled.** What the 32 to 39 percent of the time difference that
instructions do not explain is: the rerun with the simulators, and the
14900K's hardware counters if the simulators show no difference. The share
of the real stage's time that this cost takes: the stage's positioned entries
carry the table, and its index and filter call the chain on 28 to 46 tests
per element instead of shape A's 336.

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
