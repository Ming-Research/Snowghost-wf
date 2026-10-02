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
