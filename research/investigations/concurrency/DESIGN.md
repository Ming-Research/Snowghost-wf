# Concurrency of the style and layout shapes

Status: criteria recorded before any prototype runs. The style prototype is
built and checked. The layout prototype is designed below and not built. The
measurement waits for the precondition recorded under Results. Nothing here
is decided; the results feed the vocabulary proposal
(`research/investigations/vocabulary/DESIGN.md`) and, where they contradict
it, an amendment beside the design tree.

## Question

Whitefoot runs work in parallel only where it proves the work independent from
the data's shape: an owned tree split into halves, a counted loop whose
iteration writes only its own slot, disjoint subranges of one array. The
vocabulary proposal picks shapes for the stages' data (level-order style
arrays, an owned tree of formatting contexts). Does that choice decide how
much of style and layout runs in parallel on real pages, and which shape
parallelizes best under `whitefootc --par` on four cores?

The design tree fixes the independent formatting context as the unit of
parallel work (`design/pipeline.md`). Real pages often hold most of their
content in one block formatting context, so the measurement also asks how
much parallelism that unit leaves on them.

## Prototypes

Two prototype drivers under `renderer/proto/`, registered in
`renderer/modules.wfg` with their own entries. They exist only for this
investigation and are deleted when its decisions land, with the numbers kept
here. They reuse the finished modules: `pkg::html::tree_builder` builds the
document, `pkg::css::syntax`, `pkg::css::rules` and `pkg::css::selectors`
parse and match the page's style sheets, and `pkg::text::line_break` finds
break opportunities.

### Style (`pkg::proto::style`)

Per element, the prototype does the work a style stage does before computing
values:

- it tests every style rule of the page's sheets and of a small UA sheet in
  this directory (no rule hashing). The UA sheet holds the `display` rules of
  the HTML Standard's rendering section §15.3.1 hidden elements, §15.3.2 the
  page, §15.3.3 flow content, §15.3.6 sections and headings, §15.3.7 lists
  and §15.3.8 tables;
- it takes the rules inside `@media` and `@supports` blocks as if their
  condition held, and skips every other at-rule;
- it skips inline `style` attributes;
- it cascades `display`, `float`, `position` and `overflow` by source order
  (no specificity, which `pkg::css::selectors` does not expose);
- it fills four groups of eight `u64` from its matched rules. Two groups are
  inherited from the parent when no matched rule sets them; the groups stand
  in for the computed-value groups the vocabulary proposes interning.

Three traversal shapes compute the same result, which the driver checks:

- **A, level order** (the vocabulary proposal): the elements of each tree
  level sit contiguously; one counted loop per level, iteration k writing
  slot k and reading its parent's slot in the previous level.
- **B, preorder halving:** results in preorder, so a subtree is a contiguous
  range. A call styles a subtree's root, then splits the children's run into
  two halves by preorder offset. The halves are disjoint subranges of the
  results. The parent's values travel by reference, so a half's call fits a
  lane.
- **C, flat match then cascade:** one counted loop over all elements in
  preorder matches rules and writes each element's matched-rule summary to
  its own slot, since matching reads only the document. A sequential
  preorder pass then cascades and inherits.

After the style pass, a sequential **intern post-pass** interns each group
into a per-group hash table and replaces it by the table's index. It is
timed separately.

### Layout (`pkg::proto::layout`, not built)

From the style prototype's computed `display`, `float`, `position` and
`overflow`, the driver builds an owned tree:

- A node is an independent formatting context: the root, a float, an
  absolutely positioned box, a table cell, a flex or grid container's item,
  or a block with `overflow` other than `visible`. It owns its child
  contexts in `Box<Slots<Context>>`.
- Inside one context, its block boxes and paragraphs sit in flow order.
- A paragraph holds the collapsed text of one inline formatting context.

Line breaking uses `pkg::text::line_break` with a fixed advance per scalar
value (8 px; 0 for combining marks), since the font engine is not written
yet. Block layout stacks boxes with fixed margins by tag and collapses
adjacent sibling margins. Floats are recognized but do not shorten lines.

Two modes:

- **L1, formatting contexts only** (the design tree's unit): child contexts
  are laid out in parallel by halving their run. Everything inside one
  context runs in sequence, including line breaking of all its paragraphs.
- **L2, contexts and paragraphs:** as L1. In addition, a context with no
  float among its boxes breaks all its paragraphs in one counted loop, each
  iteration writing its own paragraph's result. Its block pass then runs in
  sequence.

### Pages

Real pages, each pinned by revision and SHA-256 in `run.sh`, with the style
sheets they load:

- the ECMAScript specification (tc39/ecma262 `gh-pages`);
- WebKit's parser benchmark copy of the HTML specification
  (`PerformanceTests/Parser/resources/html5.html`) with the WHATWG style
  sheet;
- one English Wikipedia article revision with its skin's style sheets.

The Wikipedia revision's `oldid` pins only the article's text. Wikimedia
serves no revision-stable bytes of the rendered page or of its skin's style
sheets, so their SHA-256 identifies the copies fetched on 2026-09-28, and a
re-fetch that fails the check means copying `build/research/concurrency/`
from a machine that has them.

Synthetic pages, generated by `run.sh`:

- **flat:** 20,000 paragraphs of 40 words in `body`;
- **deep:** 200 nested `div`s, each with a paragraph;
- **unbalanced:** two short siblings beside a chain five levels deep that
  holds 10,000 paragraphs;
- **one paragraph:** a single paragraph of 200,000 words.

### Timing

Whitefoot's standard library has no clock, so `run.sh` times whole runs.

- A driver takes the stage and a repetition count. The stage's time is
  (T(reps) − T(0)) / reps, where T(0) covers parsing and tree building.
- Each figure is the best of seven runs at `WF_WORKERS` = 1, 2 and 4, with
  the `--par` build.
- The sequential build (no `--par`) is the baseline.
- Runs take the Whitefoot check lock (`.github/run-check.pl` in the
  Whitefoot checkout), so no other heavy job shares the machine.
- The dossier records the machine, the compiler revision, each driver's
  `--par-ledger` decisions for the traversal functions, and each page's
  element, context and paragraph counts.

## Criteria

Recorded before any run; the results section may not change them.

1. **Style shape.** The style stage adopts the shape with the lowest median
   4-worker time over the three real pages. When two shapes are within 5%,
   the simpler storage wins, in the order C, A, B. The vocabulary's level
   order (A) is rejected if another shape is more than 5% faster.
2. **Interning.** Interning as a sequential post-pass is adopted if, on
   every real page, it costs at most 15% of the adopted shape's 4-worker
   style time. Otherwise the next measurement is interning split by hash
   into per-partition tables, one task per partition.
3. **Layout unit.**
   - If L1 reaches at least 2× over the sequential build at 4 workers on the
     median real page, the design tree's unit stands for layout.
   - If it does not, and L2 is at least 1.5× faster than L1 at 4 workers on
     the median real page, the dossier proposes an amendment to
     `design/pipeline.md`: paragraphs of a block formatting context with no
     float are laid out in parallel before its block pass.
   - If neither holds, the dossier records where layout time sits on the
     real pages (by context and paragraph size) and proposes nothing.
4. **Runtime fan-out.** If B or L1 reaches less than half of C's or L2's
   4-worker speedup on the unbalanced page while matching them on the flat
   page, the finding goes to Whitefoot. It shows that the runtime's
   worker-derived recursion depth under-serves unbalanced trees.

## Results

The measurement has not run. It waits for the precondition below, which
Whitefoot's call-offer grain (mbbill/Whitefoot#177) now meets, and for the pin
to move to a compiler that carries it.

### Preview with the call grain

Not the measurement: best of three at one and four workers only, stage time
(T(2) - T(0)) / 2, with the Whitefoot branch of #177 (call grain) building the
prototype, on the development machine under the check lock.

| Page | Shape | W1 (s) | W4 (s) | Speedup |
|---|---|---:|---:|---:|
| ecma262 | A | 2.877 | 0.814 | 3.53 |
| ecma262 | C | 2.931 | 0.790 | 3.71 |
| html5 | A | 3.727 | 1.034 | 3.60 |
| html5 | C | 3.855 | 1.035 | 3.73 |
| apollo11 | A | 1.713 | 0.486 | 3.53 |
| apollo11 | C | 1.776 | 0.463 | 3.84 |

Shape B first showed no speedup (0.96 to 1.00) for two reasons found in turn:

- **Its halving offer did not fit a lane.** `style_run` took `parent:
  Computed` by value, and `Computed` alone is 256 bytes, the lane slot's
  whole size, so the permitted pair of recursive calls was never handed out,
  with no ledger line (a Whitefoot diagnostic gap, now being fixed on #177).
  `style_subtree` and `style_run` now take `parent: &Computed`, reading it
  once per element; the check-mode checksums are unchanged.
- **The recursion budget runs out before the wide runs.** With the frame
  fixed, B reached 2.57 on html5 but 1.04 on ecma262 and apollo11. Built with
  `--par-recursive-frontier off` it reaches 3.76 on ecma262 and 3.81 on
  apollo11. The budget, about eight levels at four workers, is spent by
  every call in the recursive component, including the one-child descents of
  a deep document that offer nothing, so the wide sibling runs below are
  reached sequentially. This is criterion 4's case in a real page; the
  finding goes to Whitefoot (a budget spent only at hand-outs).

### Precondition: the grain of `--par` tasks

Under `--par` the compiler hands each overlap of two statements that it
permits to another lane as a task; it omits only overlaps with calls of
small straight-line scalar functions. The finished modules the prototypes
reuse hold many such overlaps whose work is a few instructions, so a
4-worker figure would mostly measure that task overhead in tree building
and selector matching rather than the traversal shapes, and criterion 1
could not tell the shapes apart. The measurement runs after a Whitefoot
investigation into `--par` task granularity.

T(0), the setup every run pays (reading and parsing the page, the traversal
arrays and the rule store; shape C with REPS 0), the best of three runs
with the scheduler's steal count of that run:

| Page | Sequential build | `--par`, 1 worker | 2 workers | 4 workers |
|---|---|---|---|---|
| ecma262 (179,471 elements) | 0.31 s | 0.30 s | 9.00 s (11.2 M steals) | 16.42 s (17.0 M steals) |
| html5 (117,179 elements) | 0.25 s | 0.26 s | 1.62 s (0.77 M steals) | 1.56 s (0.62 M steals) |
| apollo11 (11,844 elements) | 0.07 s | 0.10 s | 0.14 s (4,144 steals) | 0.11 s (29 steals) |

The overhead also varies from run to run: html5's three runs at two workers
took 1.62 to 4.06 s, and a single run at four workers in an earlier locked
session took 9.98 s with 9.6 million steals.

The runs held the check lock on the development machine (four Intel Xeon
cores at 2.1 GHz, Linux 6.18), which other agents' jobs share between
locked runs.

- Of the 420 sites where the `--par` build of `proto_style` publishes a
  task, 389 are in `pkg::html::tree_builder` (13 of them in its
  budget-carrying clones), 8 in `pkg::html::tokenizer`, 5 in
  `pkg::css::rules`, one each in `pkg::css::selectors` and `pkg::dom`, 4
  in the prototype's split loops and 12 in its driver, check and table
  setup, none of them per element. The 5,001st and the 25,001st task
  published during the flat page's setup came from the tree builder's
  per-token predicates `is_addr_block_end` and
  `is_html_or_svg_or_mathml_table_context`.
- One example inside selector matching: `byte_eq` in
  `renderer/css/selectors/text_cmp.wf` lowers both bytes with two
  independent calls of `ascii_lower_byte`, so the `--par` build publishes
  one task for each byte it compares case-insensitively. Matching compares
  that way attribute values under the `i` flag or on the HTML Standard's
  case-insensitive attributes, `:lang()` arguments, `input` types for
  `:checked`, and ids and classes in quirks mode.
- The prototype's own per-element helpers had the same pattern until commit
  e73f8c0: two independent statements in `inherit_from`, run once per
  element in every shape, and four in the checksum.

### Whitefoot: an equality requirement over range lengths

`range-length-probe.wf` in this directory passes two ranges with the same
non-constant bounds, `&a.inner[low..high]` and `&b.inner[low..high]`, to a
function that `requires first^.len == second^.len`. `whitefootc` rejects
the call with FN-8 UndischargedCallRequirement, disposition Unproved, also
after a proved `invariant equal: first^.len == second^.len;`. It accepts
the call when both ranges start at `0_u64`, and when the requirement is
written as `first^.len <= second^.len` and `first^.len >= second^.len`,
the form the style prototype's `style_level` uses.
