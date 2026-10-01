# The style stage for headless static rendering

Status: the owner approved the scope, the oracle and the criteria below on
2026-10-01, with flex, grid and generated content left for the second batch,
and the interfaces' choices Q46 to Q50 the same day. The stage is written
(`pkg::css::values`, `pkg::style`, the `style_oracle` driver) and measured
below; criterion 1 holds on ecma262 and fails on html5 and apollo11 on the
border colors alone, which trace to one rule of Chromium's user-agent sheet
that the HTML Standard does not have. Two choices wait for the owner: that
rule, and how `ex` and `ch` are resolved.

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
`initial`, `inherit` and `unset`; shorthands expanded to longhands.
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
  family names, and the seven computed groups of `design/vocabulary.md`.
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

Written while implementing Q47 and Q50; each follows from those rulings and
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
  records only which custom-property rules matched; the pass in document
  order picks the winning value per name, substitutes `var()` in it against
  the parent's set and the element's own, and shares the parent's set when
  the element declares none.
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

Measured at Snowghost commit of this change with the pinned compiler, against
the Chromium dumps of `make oracle-style-dump`; `run.sh check` reproduces
criteria 1 and 3, `run.sh time` criterion 2.

### Criterion 1: matching Chromium

The lowest share of elements matching per page, with the HTML Standard's
user-agent sheet (`renderer/style/ua.css`):

| Page | Elements | Properties below 99% | Lowest others |
|---|---:|---|---|
| ecma262 | 179,471 | none | border colors 99.37%, line-height 99.44% |
| html5 | 117,179 | border-top, -right and -left-color 96.71% | line-height 99.81% |
| apollo11 | 11,845 | the four border colors 98.17% | font-family 99.24%, color 99.31% |

Every page has the same element count in both. With Chromium's rule
`table { border-color: gray }` added to a copy of the sheet, and nothing else
changed, every property matches on at least 99 percent of the elements of
every page (html5's border colors 100%, apollo11's 99.31%), so that rule
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
- **Not explained:** 4 images of apollo11 whose width differs (`auto`
  against `250px`, `330px` against `325px`).

### Criterion 2: speed

Per-run times in seconds, the best of three runs, on a 4-processor Linux
host (`runs/time-parts.txt`, written by `run.sh time`). Each part is the
difference between the mode that ends with it and the one before, so a part
of a few hundredths is within the runs' noise; some come out negative.

| Page | Build | Matching | Pass in document order | Third part | Interning | Stage |
|---|---|---:|---:|---:|---:|---:|
| ecma262 | 4 workers | 0.320 | 0.158 | 0.052 | 0.146 | 0.676 |
| ecma262 | sequential | 1.118 | 0.116 | 0.128 | 0.136 | 1.498 |
| html5 | 4 workers | 0.394 | 0.042 | 0.010 | 0.114 | 0.560 |
| html5 | sequential | 1.302 | 0.106 | 0.028 | 0.086 | 1.522 |
| apollo11 | 4 workers | 0.195 | 0.016 | 0.007 | 0.003 | 0.221 |
| apollo11 | sequential | 0.732 | 0.004 | 0.014 | -0.025 | 0.725 |

- **Against the prototype's shape C** (0.224, 0.180 and 0.202 s at four
  workers), the stage takes 3.0, 3.1 and 1.1 times as long. The prototype
  parsed four keywords and stored the rest as hashes, without specificity,
  `!important`, `var()` or computed values; its matching was the same
  shape and index. Matching alone now takes 0.320, 0.394 and 0.195 s. It
  scales 3.5, 3.4 and 3.8 times from one worker to four.
- **Static specificity.** Matching a rule whose alternatives share one
  specificity with the boolean matcher, and reading that specificity from
  the rule, left every dump unchanged and made matching at four workers
  4, 13 and 5 percent faster (0.306, 0.344 and 0.185 s,
  `runs/time-uniform-specificity.txt`), so the rest of matching's cost
  over the prototype's is not the specificity; it is not attributed yet.
- **The pass in document order** is 23 percent of the four-worker stage on
  ecma262 and 7 percent on the other two. On ecma262 that is the large share
  criterion 2 names, so the cascade pass's case for Whitefoot's
  unique-keys investigation is made (`docs/todo.md`).
- **Interning** is 22 and 20 percent of the four-worker stage on ecma262 and
  html5, above the 15 percent bound of `design/vocabulary.md`, though only
  4 and 5 percent at one worker; why it grows with workers is not known.
  The bound's next step, interning split by hash into per-partition tables,
  is recorded in `docs/todo.md`.

### Criterion 3: equal builds

The sequential and `--par` builds wrote byte-identical dumps of all three
pages. The compiler's parallelism ledger splits the first part's loop and the
third part's loop into independent maps and runs the seven interning calls
as parallel pairs.

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
  `design/vocabulary.md`; their log entry is written with the stage's
  completion. The owner also asked that `AGENTS.md` require every design
  choice to start from its candidates' dependencies (mbbill/Snowghost#25).
