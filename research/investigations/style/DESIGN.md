# The style stage for headless static rendering

Status: the owner approved the scope, the oracle and the criteria below on
2026-10-01, with flex, grid and generated content left for the second batch.
The interfaces at the end are proposed for the owner's review before any
module body is written.

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

## Interfaces this needs

- `pkg::css::selectors` returns the highest specificity among an
  element's matching alternatives, which the cascade orders by; today it
  returns only whether the element matches.
- A new module parses and computes property values (`pkg::css::values`),
  and the style stage itself becomes `pkg::style`, grown from
  `renderer/proto/style` shape C. Their interfaces go to the owner before
  their bodies are written.

## Proposed interfaces

Three modules, with their main types and functions; property-by-property
enums are elided.

**`pkg::css::selectors`, one addition.**

```
public struct Specificity { public ids: u32; public classes: u32; public types: u32; }

public fn matching_specificity(list: &SelectorList, document: &Document,
    atoms: &AtomTable, element: NodeId, context: MatchContext,
    positions: &Positions) -> result: Option<Specificity> ...
```

The highest specificity among the alternatives of `list` that `element`
matches, under Selectors Level 4's rules for `:is()`, `:not()`, `:has()`
and `:where()`; `None` when none matches. It replaces the boolean entry in
the style stage, so matching and ordering take one pass over each rule.

**`pkg::css::values`, new: declarations and computed values.**

- `Longhand`, one variant per longhand in scope (55), and `CssWide`
  (`Initial`, `Inherit`, `Unset`).
- `parse_declaration(values, name, range, important, atoms, store)`: expands
  one declaration, a shorthand into its longhands, into the store's
  declared values, or records it invalid. A value holding `var()` is kept
  as its component range, to be substituted and parsed per element.
- `DeclarationStore`: the declared values of every rule, with side tables
  for what has no fixed size (font-family lists, `calc()` trees, unresolved
  ranges), each declaration naming its longhand, origin, importance and
  position in the cascade.
- Computed groups, the provisional groups of `design/vocabulary.md`:
  `BoxGroup` (display, position, float, clear, overflow, box-sizing,
  visibility, z-index), `SizeGroup` (the six sizes and four offsets),
  `SpacingGroup` (margins and paddings), `BorderGroup` (widths, styles,
  colors), `FontGroup` (family list, size, weight, style, line-height),
  `TextGroup` (color and the text longhands), `BackgroundGroup` (color), and
  `CustomGroup` (the custom properties an element inherits and sets).
  Absolute lengths are `LayoutUnit`; a percentage, or a `calc()` mixing
  one with a length, stays unresolved until layout knows its basis; colors
  are resolved to sRGB with alpha.
- `compute(declared, parent, root_font_size, environment)` for one element:
  substitutes `var()`, resolves `em`, `rem`, viewport units and keywords, and
  returns the element's groups.

**`pkg::style`, new: the stage, grown from the prototype's shape C.**

```
public struct Environment { public width: LayoutUnit; public height: LayoutUnit; }
public struct StyleSheetText { public origin: Origin; public text: TextSpan; public media: Option<TextSpan>; }
public struct RuleStore { ... }       // selectors, declarations, rule index
public struct Styles {
  public readonly elements: Box<Array<ComputedStyle>>;   // document order
  public readonly box: Box<Slots<BoxGroup>>; ...          // one table per group
}

public fn collect_sheets(document: &Document) -> sheets: ...   // <style> text, <link> hrefs, style attributes
public fn build_rules(sheets, ua_sheet, environment, atoms) -> Result<RuleStore, StyleError>
public fn compute_styles(store: &RuleStore, document: &Document, atoms: &AtomTable,
    environment: Environment) -> Result<Styles, StyleError>
```

- `collect_sheets` reports the `href` of each `<link rel=stylesheet>`; the
  driver reads the files, since the renderer has no network
  (`design/processes.md`), and the shell will supply them later.
- `build_rules` evaluates `@media` and `@supports` against `Environment`
  and the supported longhands, once per sheet, so matching never sees a
  rule whose condition fails.
- `compute_styles` runs in three parts (Q50): a parallel loop matches,
  orders and selects each element's cascaded values and computes what needs
  nothing from the parent; one pass in document order computes the font
  size, the custom properties and the inherited values; a second parallel
  loop computes the rest. The eight group tables are then interned as eight
  independent tasks (Q48).
- `var()` is substituted where its result is needed (Q47): in the pass in
  document order for the font size and inherited longhands, which children
  read, and per element in the second loop for every other longhand, with
  no cache shared across elements.

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
