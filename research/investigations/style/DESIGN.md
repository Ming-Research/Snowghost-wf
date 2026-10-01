# The style stage for headless static rendering

Status: the owner approved the scope, the oracle and the criteria below on
2026-10-01, with flex, grid and generated content left for the second batch,
and the interfaces' choices Q46 to Q50 the same day. The stage is written
(`pkg::css::values`, `pkg::style`, the `style_oracle` driver) and measured
below; criterion 1 holds on ecma262 and fails on html5 and apollo11 on the
border colors alone, which trace to one rule of Chromium's user-agent sheet
that the HTML Standard does not have. The owner ruled the three choices the
results raised on 2026-10-01 ("Choices after the results" below): the stage
keeps the Standard's sheet, so that failure stays recorded; `ex` and `ch`
come from the default fonts' metrics; and lengths become `LayoutUnit` when
layout reads them.

## Question

What does the style stage of the first milestone, headless static rendering,
compute for every element, from which inputs, and how is it judged correct?
The stage's shape is decided (`design/pipeline/style.md`: matching in one
parallel loop in document order with a rule index and sibling positions,
then a cascade pass in document order), and so are its value types
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

- **Chromium's user-agent sheet where the HTML Standard has no rule:**
  `table { border-color: gray }` (1,123, 3,849 and 135 elements on
  ecma262, html5 and apollo11, tables and the cells that inherit it);
  `overflow: clip` on `img`, `video` and `canvas` (7, 30 and 65);
  `-webkit-center` for `caption` (17 and 4); the form controls' fonts,
  colors, borders and padding, which the Standard leaves to prose (5 buttons
  and a fieldset on ecma262, 81 inputs on apollo11); `svg:not(:root) { overflow: hidden }` from its SVG
  sheet (1).
- **The HTML Standard's sheet where Chromium has no rule:**
  `sub, sup { line-height: normal }` (990 and 214 elements on ecma262 and
  html5).
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
  The owner ruled for the Standard's sheet. The rendering section of the
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

## Owner rulings

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
