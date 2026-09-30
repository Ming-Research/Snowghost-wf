# Concurrency of the style and layout shapes

Status: criteria recorded before any prototype runs. The style prototype is
built, checked and measured: criteria 1 and 2 are answered and criterion 4
is answered for the style shapes. The layout prototype is built and measured;
its result retired the independent formatting context as the unit of
parallel work (the `pipeline` tree's principle, approved 2026-09-29), which
makes criterion 3's second branch moot. The rest here decides nothing; the
results feed the vocabulary proposal
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

### Layout (`pkg::proto::layout`)

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
adjacent sibling margins. A float sits where its element occurs in the
flow and narrows the lines beside it (see [Floats](#floats-speculative-line-breaking-and-fix-up)).

Two modes, and a third one added for floats:

- **L1, formatting contexts only** (the design tree's unit): child contexts
  are laid out in parallel by halving their run. Everything inside one
  context runs in sequence, including line breaking of all its paragraphs.
- **L2, contexts and paragraphs:** as L1. In addition, a context with no
  float among its boxes breaks all its paragraphs in one counted loop, each
  iteration writing its own paragraph's result. Its block pass then runs in
  sequence.
- **L3, speculative lines:** as L2, in every context, floats or not: each
  paragraph is broken at the context's full width in parallel, and the block
  pass breaks again, exactly, only the paragraphs a float narrows.

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

## Open question: the unit of storage, invalidation and caching

The layout result retired the formatting context as the unit of parallel
work, but not necessarily as the unit of storage, invalidation or caching.
The prototypes store an owned tree of contexts, and within it the parallel
work follows data dependencies (paragraphs of one context, sibling
contexts), not the nodes. The `pipeline` tree still commits to rerunning
only the stages and the parts of the page a change affects; what "part"
means there, a context, a paragraph or a stage's own record, is not decided
here. The first incremental prototype, which reruns layout after a change,
is the measurement that can decide it.

## Results

### Style measurement

`run.sh style` at Snowghost commit 5f9f994, whose Whitefoot pin 13556101
carries the call-offer grain and the recursion budget spent only at group
calls (mbbill/Whitefoot#177), on the development machine (four Intel Xeon
cores at 2.1 GHz, Linux 6.18) under the check lock. Each figure is the stage
time (T(REPS) - T(0)) / REPS from the best of seven runs; the repetition
counts are `run.sh`'s. T(0) no longer grows with workers: 0.27 to 0.29 s on
ecma262, 0.22 to 0.23 s on html5 and 0.05 to 0.06 s on apollo11 in every
build. `run.sh check` passes on all seven pages.

Style stage, seconds, with the speedup of four workers over the sequential
build:

| Page | Shape | seq | W1 | W2 | W4 | seq / W4 |
|---|---|---:|---:|---:|---:|---:|
| ecma262 | A | 2.850 | 2.877 | 1.757 | 0.810 | 3.52 |
| ecma262 | B | 3.063 | 2.983 | 1.700 | 0.887 | 3.45 |
| ecma262 | C | 2.840 | 2.953 | 1.507 | 0.790 | 3.59 |
| html5 | A | 3.707 | 3.737 | 2.073 | 1.040 | 3.56 |
| html5 | B | 3.947 | 3.950 | 2.007 | 1.107 | 3.57 |
| html5 | C | 3.800 | 3.893 | 1.973 | 1.023 | 3.71 |
| apollo11 | A | 1.683 | 1.723 | 0.955 | 0.483 | 3.49 |
| apollo11 | B | 1.775 | 1.723 | 1.613 | 1.600 | 1.11 |
| apollo11 | C | 1.685 | 1.773 | 0.900 | 0.465 | 3.62 |
| flat | A | 0.0309 | 0.0316 | 0.0191 | 0.0088 | 3.51 |
| flat | B | 0.0355 | 0.0338 | 0.0175 | 0.0084 | 4.23 |
| flat | C | 0.0299 | 0.0319 | 0.0165 | 0.0091 | 3.29 |
| unbalanced | A | 0.0150 | 0.0153 | 0.0097 | 0.0045 | 3.33 |
| unbalanced | B | 0.0187 | 0.0167 | 0.0083 | 0.0044 | 4.25 |
| unbalanced | C | 0.0149 | 0.0157 | 0.0081 | 0.0045 | 3.31 |

The deep page (405 elements) stays under a millisecond per repetition in
every build (C 0.3 ms at two workers and 0.2 ms at four, the others 0.6 to
0.8 ms), and the paragraph page (6 elements) under the timer's resolution;
neither separates the shapes.

Intern post-pass, seconds per repetition, against the four-worker style time
of C: 0.0365 on ecma262 (4.6 percent), 0.0296 on html5 (2.9 percent) and
0.0021 on apollo11 (0.5 percent), the same in every build.

- **Criterion 1: C.** The median four-worker time over the three real pages
  is 0.790 s for C, 0.810 s for A and 1.107 s for B. A is within 5 percent
  of C, and the simpler-storage order C, A, B then chooses C. A, the
  vocabulary's level order, is not rejected by the criterion, since C is
  2.5 percent faster, but it is not the adopted shape.
- **Criterion 2: the sequential post-pass.** It costs at most 4.6 percent of
  C's four-worker style time on every real page, under the 15 percent bound.
- **Criterion 4, style half: not met.** On the unbalanced page B's speedup,
  4.25, is above C's 3.31, and on the flat page 4.23 against 3.29; B does not
  fall below half of C. The unbalanced page's chain is five levels deep,
  within the budget. Apollo11, a real page, shows the case the criterion
  describes: B reaches 1.11 against C's 3.62, because its work sits under
  a few children of wide sibling runs whose halvings are real splits and
  spend the fixed-depth budget. That finding already went to Whitefoot
  (mbbill/Whitefoot#177, its todo item "A fixed recursion budget cannot
  follow an unbalanced tree"). The L1 half waits for the layout prototype.
- **Not recorded: the `--par-ledger` decisions.** `whitefootc` refuses
  `--par-ledger` with `--graph` ("reports a source bundle build"), and the
  prototype builds only from the module graph, so the Timing section's
  ledger record is not available; the gap goes to Whitefoot's todo.


### Layout measurement

`run.sh layout` at Snowghost commit 7d840e2 with the same pin, machine and
lock as the style measurement, before floats had an anchor in the flow: a
float then narrowed no line, so these figures describe that model, not the
current one. The float section below measures L1 again under the anchor
model on html5 (0.0960 s sequential, 0.1120 s at four workers) and apollo11
(0.0050 s and 0.0052 s), which keeps L1 below the sequential build there;
ecma262 and the synthetic pages hold no float, so their layout is the same
in both models. The layout stage
(T(REPS) - T(0)) / REPS from the best of seven runs, T(0) holding parsing,
styling (shape C) and building the context tree. `run.sh check` passes: L1
and L2 agree on all seven pages, and the root heights of flat (1,520,016 px)
and deep (15,216 px) equal the ones computed by hand from the pages' text,
width and margins.

The prototype as built, beyond the design above: a context's width is its
enclosing context's, a third for a float, a quarter for a table cell or a
flex or grid item and half for an inline-block; `br` adds U+2028 and an
inline-level context adds U+FFFC; whitespace always collapses, `pre`
included. The builder's rules are in `renderer/proto/layout/module.wfm`.
Each paragraph's line count is kept in an array beside the paragraphs,
because Whitefoot's loop permission [PAR-2] admits a whole-element write
(`set lines^[i] = n`) and denies a write to one field of element i
(`set paragraphs^[i].lines = n`); see the Whitefoot finding below.

Layout stage, seconds per repetition, with the speedup of four workers over
the sequential build:

| Page | Mode | seq | W1 | W2 | W4 | seq / W4 |
|---|---|---:|---:|---:|---:|---:|
| ecma262 | L1 | 0.0714 | 0.0739 | 0.0820 | 0.0774 | 0.92 |
| ecma262 | L2 | 0.0724 | 0.0739 | 0.0425 | 0.0228 | 3.18 |
| html5 | L1 | 0.0907 | 0.0950 | 0.1080 | 0.1080 | 0.84 |
| html5 | L2 | 0.0937 | 0.0930 | 0.1080 | 0.1077 | 0.87 |
| apollo11 | L1 | 0.0049 | 0.0046 | 0.0049 | 0.0051 | 0.96 |
| apollo11 | L2 | 0.0039 | 0.0043 | 0.0050 | 0.0051 | 0.76 |
| flat | L1 | 0.1330 | 0.1370 | 0.1700 | 0.1685 | 0.79 |
| flat | L2 | 0.1345 | 0.1390 | 0.0825 | 0.0415 | 3.24 |
| unbalanced | L1 | 0.0670 | 0.0690 | 0.0845 | 0.0845 | 0.79 |
| unbalanced | L2 | 0.0660 | 0.0685 | 0.0415 | 0.0200 | 3.30 |

Deep stays under 2 ms per repetition (L2 0.4 ms at four workers against
1.3 ms sequentially); the one-paragraph page takes 43 to 54 ms in every
build and mode, since one paragraph is one task.

**Where layout time sits.** `proto_layout profile` prints each context's own
scalar values. On every real page one context holds almost all of the text:

| Page | Contexts | Largest context's scalar values | Share | Its paragraphs | A float among its boxes |
|---|---:|---:|---:|---:|---|
| ecma262 | 9,931 | 1,724,203 of 2,025,062 | 85 % | 27,979 | no |
| html5 | 11,794 | 2,526,573 of 2,645,960 | 95 % | 20,919 | yes |
| apollo11 | 235 | 118,841 of 128,790 | 92 % | 559 | yes |

The next largest context holds 4,234 scalar values on ecma262 and under
1,300 on the other two. So L1, which splits only runs of contexts, has
nothing to split: every real page's layout is one context's sequential
work. L2 breaks that context's paragraphs in parallel on ecma262 (3.18),
but on html5 and apollo11 the largest context has a float among its boxes,
and L2 as designed then proceeds as L1.

**The four-worker L1 penalty.** L1 is 5 to 24 percent slower at two and
four workers than at one on every page. The call grain keeps no call offer
on its path; the one split loop on it is `pkg::text::line_break`'s
`write_run_span`, run once per run of a paragraph. With that loop made
unsplittable in a local build (not committed), flat's L1 took 1.52 s at
four workers against 1.57 s at one (ten repetitions, best of three), where
the committed build took 1.80 s against 1.53 s: a split loop whose runtime
work never reaches the work unit still costs its query once per call when
workers are idle. The finding goes to Whitefoot.

- **Criterion 3, first branch: not met.** L1 reaches 0.92 over the
  sequential build at four workers on the median real page (0.84, 0.92 and
  0.96 on the three), not 2. The design tree's unit does not stand for
  layout on these pages.
- **Criterion 3, second branch: moot.** The owner ruled on the first
  branch's finding instead: the `pipeline` tree now has no unit of parallel
  work, every stage keeping only its algorithm's true data dependencies, and
  refuses the float-free paragraph rule this branch would have proposed.
  For the record, L2 against L1 at four workers is 3.39 on ecma262, 1.00 on
  html5 and 1.00 on apollo11: 1.00 read as the ratio on the page whose ratio
  is the median, 3.39 read as the ratio of the median four-worker times
  (L1 0.0774 s, L2 0.0228 s, both ecma262's). The criterion did not say
  which.
- **Criterion 4, L1 half: not met, and uninformative.** On the unbalanced
  page L1 reaches 0.79 against L2's 3.30, below half, but L1 does not match
  L2 on the flat page (0.79 against 3.24) either. Both synthetic pages hold
  one formatting context, so L1 has nothing to split on them; the
  criterion's premise, sibling contexts of unequal size, is absent.

### Preview with the call grain

Superseded by the measurement above; kept for how shape B's two obstacles
were found. Best of three at one and four workers only, stage time
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

### Whitefoot: whole-element writes in a counted loop

L2's paragraph loop first wrote each paragraph's line count into the
paragraph, `set paragraphs^[i].lines = lines`, and `--par-ledger` reported
the loop denied: "the body writes storage that is neither introduced by the
iteration nor the accumulator". [PAR-2]'s element family is exactly a
direct `Array` or `Slots` subscript, so a write to one field of element i is
not one, although it writes inside element i's range. Writing the counts to
an array beside the paragraphs, `set lines^[i] = counted`, is permitted and
splits. The finding goes to Whitefoot as a language gap: a field of the
element an affine subscript selects.

`--par-ledger` refused a `--graph` build until mbbill/Whitefoot#186, so
these decisions were read with that branch's compiler. Whitefoot v0.81
admits the field write; see below.

### Field writes after Whitefoot v0.81

Whitefoot v0.81 (mbbill/Whitefoot#186, pinned at `290b575b`) admits a
counted loop's writes at or below one mapped element, so L2's paragraph loop
can write each paragraph's line count into the paragraph itself again,
`set paragraphs^[i].lines = counted`, instead of into the array kept beside
the paragraphs.

Criterion, written before measuring: with that pin, the field-write loop is
permitted and split (`--par-ledger`), and its L2 layout stage on ecma262 and
flat is within 5 percent of the array build, compiled with the same pin, at
one and four workers. A larger gap means the field form costs something the
array form does not, and the finding goes to Whitefoot.

`--par-ledger` reports `PAR split proto.layout.break_all loop ... split
independent map`, and both builds give the same checksums on ecma262 and
flat, where L1 and L2 agree. `run.sh layout "ecma262 flat"` with RUNS=3 and
WORKERS "1 4" (the array build first, then the field build, each best of
three), L2 stage in seconds:

| Page | Workers | Array | Field |
|---|---|---:|---:|
| ecma262 | 1 | 0.0718 | 0.0742 |
| ecma262 | 4 | 0.0222 | 0.0227 |
| flat | 1 | 0.1305 | 0.1390 |
| flat | 4 | 0.0390 | 0.0410 |

flat's 6.5 and 5.1 percent passed the bound, but its L1 rows, which do not
run the loop, moved 3 percent between the two runs too. An alternating
comparison separated drift from cost: both builds on flat in L2, 20
repetitions, five rounds alternating array and field. The best totals in
seconds: at four workers 0.93 and 0.93, the order varying by round; at one
worker 2.77 and 2.83, and sequential 2.73 and 2.83, the field build slower
in every round. The field form costs about 2 percent of the stage at one
worker and 4 percent sequentially, and nothing measurable at four: within
the criterion. The likely cause is the paragraph record growing from one
word to two; it is left as is.

### Floats: speculative line breaking and fix-up

The pipeline tree breaks every paragraph into lines before floats are placed
and breaks again only the paragraphs a float narrows. This section measures
that on html5 and apollo11, whose largest context holds a float.

**Where the layout stage's work sits.** Callgrind on flat's layout stage (L1,
sequential build) attributes 91 percent of the instructions to
`find_line_breaks` (building runs 20, deciding opportunities 63, writing them
9), 8.5 percent to the greedy fill and 0.2 percent to stacking and the
checksum. Breaking one paragraph depends on its text only; its greedy fill
depends on the widths of its lines, which a float narrows. A float's place
depends on the height of the flow before it, and so on the fill of every
earlier paragraph. So the only true sequential chain is the block pass, and
it is cheap unless many paragraphs sit beside floats.

**The float model.** A float's anchor is where its element occurs in the
flow; inside a paragraph that is before the paragraph, so the float narrows
it from its first line. Its top is the flow's height plus the pending
margin at the anchor, its width the float context's width (a third of the
enclosing one) and its height that context's laid-out height. Floats do not
push each other, and `clear` is not modelled. A line 20 px high whose
vertical range meets a float is the context's width minus the widths of the
floats it meets, at least 0, and a context's height reaches the lowest float
bottom. Every mode computes the same layout: L1 and L2 fill each paragraph
beside the floats already placed, and L3 re-breaks a paragraph whose top is
above the lowest float bottom so far. That test is exact: float tops and
paragraph tops only grow along the flow, so a float placed before a
paragraph meets its lines exactly when its bottom lies below the paragraph's
top.

Criteria, written before measuring:

1. **Equality.** L3's checksum equals L1's and L2's on all seven pages, and
   the sequential build's checksums equal the `--par` build's.
2. **Speedup.** At four workers, L3's layout stage on html5 and on apollo11
   is at least 2 times faster than the sequential build's L1.
3. **Fix-up share.** The share of paragraphs L3 re-breaks, by count and by
   scalar values, is recorded; above 10 percent on either page means the
   float approach is reconsidered.
4. **Largest paragraph.** The largest paragraph's share of each page's
   scalar values is recorded, to decide whether breaking inside a paragraph
   is worth building.

Each measurement runs in under ten minutes.

**Results.** At Snowghost commit 802eff0 with the `290b575b` pin, on the
same machine under the lock. `proto_layout check` passes on all seven pages
in both builds, the sequential build's checksums equal the `--par` build's,
and a sequential build whose L3 skips the fix-up fails the check on
apollo11; that build changes `stack_flow`'s `let beside = top < reach;` so
that `beside` also requires `known` to be False.
`--par-ledger` still splits `break_all` as an independent map.
`MODES="L1 L3" WORKERS=4 RUNS=3 run.sh layout "html5 apollo11"` took 6
minutes, including building both drivers. Layout stage in seconds per
repetition, best of three:

| Page | L1 seq | L1 W4 | L3 seq | L3 W4 | L1 seq / L3 W4 |
|---|---:|---:|---:|---:|---:|
| html5 | 0.0960 | 0.1120 | 0.0967 | 0.0290 | 3.31 |
| apollo11 | 0.0050 | 0.0052 | 0.0047 | 0.0017 | 2.94 |

apollo11's stage is 0.26 to 0.75 s of wall time over 150 repetitions, so the
0.01 s resolution of `time -p` bounds each of its figures to about 4
percent.

| Page | Floats | Paragraphs broken again | Their scalar values | Largest paragraph's share of the scalar values |
|---|---:|---:|---:|---:|
| html5 | 3 | 0 of 32,684 | 0 of 2,645,960 | 0.34 % (8,983) |
| apollo11 | 4 | 4 of 770 (0.52 %) | 2,751 (2.14 %) | 1.07 % (1,381) |

- **Criterion 1: met.**
- **Criterion 2: met,** 3.31 on html5 and 2.94 on apollo11.
- **Criterion 3: below the bound.** The fix-up breaks again at most 0.52
  percent of the paragraphs and 2.14 percent of the scalar values. On html5
  every paragraph starts at or below the lowest bottom of the floats placed
  before it, so its three floats narrow no paragraph, and what kept L2 at
  0.87 there was only its float-free rule. The driver does not print float
  heights, so whether html5's floats are empty or follow the last paragraph
  of their context is not known; either way html5 does not exercise the
  fix-up, and apollo11's four paragraphs are its only exercise.
- **Criterion 4.** The largest paragraph holds 0.34 percent of html5's
  scalar values and 1.07 percent of apollo11's (`check` also prints 1,277
  of 2,025,062 for ecma262, 0.06 percent). The criterion set no threshold
  in advance. At four workers the stage's time is about a quarter of its
  work plus its critical path, and the largest paragraph is the part the
  paragraph loop cannot split, so breaking inside a paragraph could gain
  at most about that share on these pages. It stays unbuilt; the synthetic
  one-paragraph page is the case it would serve.

### Box tree construction

With L3, layout's stage is a quarter of its sequential time on html5 and
apollo11, so building the context tree (`build_layout`), which every
layout run needs first and which runs in sequence, may now cost as much as
laying the tree out. `proto_layout build REPS` builds the tree REPS more
times after the first, so its stage time is measured like the others.

**Where its dependencies are.** The builder walks the document in tree
order. Within one context, text joins the open paragraph with whitespace
collapsed against the scalar before it, and flow items are appended in
order, so a context's own walk is a chain. A child context depends only on
its element and its width, which comes from the enclosing context's width
alone, so building it depends on nothing its siblings or the enclosing walk
produce: child contexts are independent work, as they are in layout. The
preorder map from node to style index is a scatter whose independence
needs a permutation proof Whitefoot does not derive.

Criterion, written before measuring: the build stage is timed in the
sequential build and at four workers on the three real pages. If its
sequential time exceeds L3's four-worker layout stage on any of them, the
builder is the next sequential cost of layout, and a design that builds
the tree along its true dependencies goes to the owner before any change;
otherwise it waits behind the larger stages. The measurement runs in under
ten minutes.

**Results.** At Snowghost commit 5c5bb1f with the `290b575b` pin, under the
lock: `MODES=build WORKERS=4 RUNS=3 run.sh layout "ecma262 html5 apollo11"`
took 6 minutes, including building both drivers. Build stage in seconds per
repetition, best of three, beside the four-worker layout stage measured
before (L3 on html5 and apollo11; L2 on ecma262, which holds no float, so
its L3 runs the same loop):

| Page | Build seq | Build W4 | Layout W4 |
|---|---:|---:|---:|
| ecma262 | 0.0275 | 0.0288 | 0.0228 (L2) |
| html5 | 0.0305 | 0.0309 | 0.0290 (L3) |
| apollo11 | 0.0012 | 0.0013 | 0.0017 (L3) |

Callgrind on html5's build stage (one build, sequential driver, collection
limited to `build_layout`): 376 million instructions, 60 percent in
`add_text`, which decodes UTF-8 and collapses whitespace, 20 percent in
appending each scalar value to the open paragraph (`push_item`), 8 percent
in the walk itself (`build_children` and `build_element`) and about 9
percent in allocation and copying (`malloc`, `calloc`, `free`, `memcpy`
and `memset`).

- **Criterion: met** on ecma262 and html5, where the sequential build takes
  longer than the four-worker layout stage; not on apollo11. The `--par`
  build gains nothing, since nothing in the builder is split.
- Four fifths of the builder is turning text into paragraphs' scalar
  values, and on html5 one context holds 95 percent of the text, so
  building child contexts in parallel would leave most of that work in one
  context's walk.
- For scale, at four workers the style stage takes 0.79 s on ecma262 and
  1.02 s on html5, and setup (parsing, the traversal arrays and the rule
  store) 0.29 and 0.23 s, so the builder is about 2 to 3 percent of those
  pages' four-worker pipeline.

**Decoding after the walk** (the owner's choice after this measurement).
The walk records each paragraph's text as pieces, a byte span of a text
node or one scalar value (U+2028 for `br`, U+FFFC for an inline-level
context), and a paragraph starts at its first piece holding a scalar value,
so a text node of whitespace alone before it adds none. After a context's
walk, one counted loop decodes each paragraph's pieces and collapses their
whitespace, each iteration writing its own paragraph's text. The pieces of
one paragraph depend only on each other, so the walk keeps only what orders
the flow, and decoding runs once per build, not once per layout, leaving
the paragraph as layout reads it unchanged.

Criteria, written before measuring:

1. **Equality.** Every page's `check` checksum and root height equal the
   ones before the change: ecma262 `b47f12e705ca8399`, html5
   `573435a08e88e874`, apollo11 `1b5748884b4ca817`, flat `2f23fed55397442f`,
   deep `9bf5169a445b9dd7`, unbalanced `94024e7779ea1cdd` and paragraph
   `c515c705c909bc8e`.
2. **Speedup.** At four workers the build and L3 layout stages together
   take at most two thirds of their time before (0.0516 s on ecma262,
   0.0599 s on html5), that is, they are at least 1.5 times faster.

**Setup** (the owner's choice after this measurement). Parsing, the
traversal arrays and the rule store run once before style, in sequence.
`proto_layout parse`, `traverse` and `rules` repeat one of them REPS more
times. Their sequential times on the three real pages and their shares of
the four-worker pipeline are recorded; no threshold selects among them,
and the largest names the next sequential cost to study.

**Results.** At Snowghost commit 7c9caf3 with the same pin, machine and
lock. Every page's paragraph and scalar value counts, root height and
checksum equal the ones above in both builds, and `--par-ledger` splits
`decode_all` as an independent map; `runs/0-check-base-e45ccb7.txt` holds
the base's `check` output and `runs/8-check-075f359.txt` the output and the
splits at 075f359. `MODES="build L3" WORKERS=4 RUNS=3 run.sh layout "ecma262
html5"` took 7 minutes, including building both drivers; seconds per
repetition, best of three:

| Page | Build seq | Build W4 | L3 W4 | Build and L3, W4 | Before | Speedup |
|---|---:|---:|---:|---:|---:|---:|
| ecma262 | 0.0369 | 0.0274 | 0.0206 | 0.0480 | 0.0516 | 1.08 |
| html5 | 0.0370 | 0.0224 | 0.0260 | 0.0484 | 0.0599 | 1.24 |

- **Criterion 1: met.**
- **Criterion 2: not met.** Both pages got faster at four workers, by
  1.08 and 1.24 times, not 1.5. The bound asked for the ideal on ecma262
  and more than it on html5: with the old builder's decoding share (80
  percent) divided by four and nothing else changed, the totals give 1.50
  and 1.45. The totals before add L2's layout time, measured in an earlier
  run, and after L3's; the layout code did not change.
- The sequential build became 34 percent slower on ecma262 and 21 percent
  on html5. Callgrind on html5's build counts 396 million instructions
  against 376 million before, 75 percent of them in `decode_pieces`, the
  split loop's body, and 25 percent in the walk. At four workers the build
  runs 1.35 (ecma262) and 1.65 (html5) times faster than sequentially,
  against about 2.3 if the decoding loop divided by four. What costs the
  difference is not measured: candidates are the second pass over the
  text, one allocation per paragraph inside the split loop, and on ecma262
  the 15 percent of the text outside the largest context, whose small
  contexts decode during the walk.

`KEEP_BUILD=1 MODES="parse traverse rules" WORKERS=4 RUNS=3 run.sh layout
"ecma262 html5 apollo11"` took 5 minutes; seconds per repetition, best of
three. A step's share is of the four-worker pipeline taken as the three
steps' four-worker times, style C from the style measurement, the build and
L3 layout from the runs above (apollo11's build from the first build
measurement):

| Page | Parse seq | Parse W4 | Traversal W4 | Rule store W4 | Shares at W4: parse, traversal, rule store |
|---|---:|---:|---:|---:|---|
| ecma262 | 0.1827 | 0.1907 | 0.0066 | 0.0043 | 18, 0.6, 0.4 % |
| html5 | 0.1443 | 0.1473 | 0.0040 | 0.0031 | 12, 0.3, 0.3 % |
| apollo11 | 0.0197 | 0.0200 | 0.0004 | 0.0185 | 4, 0.1, 3.6 % |

- The `--par` build is no faster within the spread between runs: apollo11's
  rule store and traversal took 7 and 10 percent less at four workers, the
  other steps within 5 percent.
- Parsing is the largest sequential cost on ecma262 and html5. On apollo11,
  whose style sheets are large, the rule store costs about as much as
  parsing; each repetition of `rules` also reads the sheet files again.
- The repeated steps run after the first, with the atom table already
  filled, and the three steps sum to about 0.20 s on ecma262 and 0.15 s on
  html5, against the 0.29 and 0.23 s of the style measurement's T(0); what
  the difference holds, such as reading the files, starting the process or
  the first run's cold atom table, is not measured.
- Traversal and the rule store are 14 to 34 percent of T(REPS), so their
  times carry about 10 to 15 percent of T(0)'s spread.

**Where the decoding loop loses its speedup.** The 1.5 of criterion 2 was
the ideal on ecma262 and above it on html5 (see above). An exploratory run,
one each before this criterion, put ecma262's build at 0.032 s at one
worker, 0.028 at two and 0.024 at four, so the split loop scales far less
than its 75 percent share allows. Each iteration allocates its paragraph's
text inside the split loop. The experiment allocates it instead during the
walk, at the capacity the pieces bound, and leaves the decoding work as it
is.

Criterion, written before measuring: the build stage at one, two and four
workers and sequentially, best of three, on ecma262 and html5, before and
after. If the four-worker time falls by at least a fifth on both pages,
allocation inside the split loop is the cost, and the change stays;
otherwise the cost lies elsewhere and the builder is left as it is.

Results, `KEEP_BUILD=1 MODES=build WORKERS="1 2 4" RUNS=3 run.sh layout
"ecma262 html5"` before (commit f8fbad0) and after (93c2aae), 4 minutes
each; every page's result is unchanged. Build stage in seconds per
repetition, best of three:

| Page | | W1 | W2 | W4 | seq |
|---|---|---:|---:|---:|---:|
| ecma262 | before | 0.0324 | 0.0275 | 0.0239 | 0.0327 |
| ecma262 | after | 0.0285 | 0.0262 | 0.0213 | 0.0318 |
| html5 | before | 0.0343 | 0.0267 | 0.0205 | 0.0355 |
| html5 | after | 0.0313 | 0.0229 | 0.0184 | 0.0310 |

- **Criterion: not met.** The four-worker time fell by 11 percent on
  ecma262 and 10 percent on html5, not a fifth.
- W1 over W4 is 1.34 on ecma262 and 1.70 on html5 after, and 1.36 and
  1.67 before. The gains at every worker count lie within the spread
  between runs found below, so whether the allocations weighed on the
  loop's scaling cannot be told from these runs. Read by Amdahl's law, the
  ratios leave about 66 and 45 percent of the one-worker time outside the
  split loop, far above the walk's 25 percent of the instructions.
- Each paragraph's reserved text holds one 4-byte slot per byte and
  inserted scalar value, and stays reserved after decoding; the memory this
  costs is not measured.

**The walk's own time.** `proto_layout walk REPS` builds the tree REPS more
times without decoding it. Criterion, written before measuring: the walk's
time at one and four workers and sequentially, best of three, on ecma262
and html5. If the walk takes at least half of the one-worker build on
either page, the walk, not the decoding loop, limits the build's speedup,
and the builder's next change would be to the walk; otherwise the decoding
loop itself scales poorly.

Results at commit 075f359, `KEEP_BUILD=1 MODES="walk build" WORKERS="1 4"
RUNS=3 run.sh layout "ecma262 html5"`, 6 minutes; every page's result is
unchanged. Seconds per repetition, best of three; the decoding is the build
less the walk:

| Page | Walk W1 | Walk W4 | Walk seq | Build W1 | Build W4 | Decoding W1 | Decoding W4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ecma262 | 0.0151 | 0.0152 | 0.0155 | 0.0311 | 0.0238 | 0.0160 | 0.0086 |
| html5 | 0.0118 | 0.0124 | 0.0122 | 0.0315 | 0.0193 | 0.0197 | 0.0069 |

- **Criterion: not met,** narrowly on ecma262: the walk is 49 percent of
  the one-worker build there and 37 percent on html5.
- Both halves limit the build. The walk gains nothing from workers, and
  since commit 93c2aae it also allocates every paragraph's text. All
  decoding, the split loops and the small contexts' loops that run during
  the walk, is 1.86 times faster at four workers on ecma262 and 2.86 on
  html5; with 85 and 95 percent of the text in the largest context, it
  could reach at most about 2.8 and 3.5. The walk's one-worker time plus
  all decoding divided by four would give 0.0191 and 0.0167 s at four
  workers.
- **The allocation experiment's gain is within the noise.** The same
  decoding code at commit 93c2aae (075f359 adds only the flag that skips
  it) took 0.0213 and 0.0285 s at four and one workers on
  ecma262 in the run before, against 0.0238 and 0.0311 here, and 0.0184
  against 0.0193 at four workers on html5: two runs differ by 5 to 12
  percent, as much as the 11 and 10 percent the experiment gained. Its
  verdict, less than a fifth, stands either way.
- Against the builder before decoding moved out of the walk (0.0288 and
  0.0309 s at four workers), the build at four workers now takes 0.0213 to
  0.0238 s on ecma262 and 0.0184 to 0.0193 s on html5.

The raw output of every run in this section and the callgrind summaries are
in `runs/`, with the checkout path removed. The runs with `KEEP_BUILD`
reused drivers built from commit 7c9caf3 (setup and the allocation
experiment's before), 93c2aae (after) and 075f359 (walk); `run.sh` now
prints each driver's hash.

**The owner's ruling.** Decoding after the walk stays, and the builder is
left here: what the walk and the decoding loop could still give is a few
milliseconds, under 1 percent of the four-worker pipeline. Parsing, the
largest sequential step, is the next one studied.

### HTML parsing

Parsing runs once, in sequence, before everything else, and takes 18 and 12
percent of ecma262's and html5's four-worker pipeline. Callgrind on html5's
parse (sequential driver built from commit 075f359, collection limited to
`parse_document`): 1,358 million instructions, 60 percent in the tokenizer
(`next_token`) and 39 percent in tree construction (`process_token`, with
atom interning 5 percent and DOM insertion 7). The largest single costs are
per-byte copies of text into the token's text buffer: `bytes_push` 13
percent, `push_codepoint` 10 and UTF-8 decoding 7.

**Where its dependencies are.**

- *Tokenizer.* A state machine over the bytes: each byte's meaning depends
  on the state the bytes before it left. Almost all of a page is in the data
  state, and a chunk of the page tokenized from an assumed state agrees with
  the true one from the first point where both states meet, typically at
  the next `<` in data. Tree construction feeds back into the tokenizer:
  after `script`, `style`, `title`, `textarea` and a few other start tags it
  switches the tokenizer to script data, raw text or RCDATA, and it allows
  CDATA sections only in foreign content. So a chunk's tokens can be
  computed speculatively in parallel and checked where each chunk starts.
- *Tree construction.* The insertion mode, the stack of open elements and
  the list of active formatting elements carry from each token to the next,
  and the adoption agency and foster parenting rewrite the tree on earlier
  decisions. It is one chain over the tokens; interning names and building
  a node's attributes depend only on the token.
- *Copying text.* A text token's bytes are decoded to code points and
  pushed back one at a time; a run of plain bytes could be copied whole.
  That shortens the chain without parallelism.

`proto_layout tokenize REPS` runs the tokenizer alone over the page REPS
times, from the data state and with no tree construction, so the contents
of `script`, `style`, `title` and `textarea` are tokenized as markup rather
than as text; it counts the tokens.

Criterion, written before measuring: the tokenizer alone and the whole
parse, sequentially, best of three, on the three real pages. If the
tokenizer takes at least half of the parse on both large pages (ecma262 and
html5), the first parallel design targets the tokenizer (speculative
chunks); otherwise it targets tree construction and the text copy.

**Results.** At Snowghost commit 58fa8ee, `KEEP_BUILD=1 MODES="tokenize
parse" RUNS=3 run.sh layout "ecma262 html5 apollo11"` took 8 minutes (an
empty `WORKERS` falls back to its default, so the `--par` build ran at one,
two and four workers too). Seconds per repetition, best of three, in the
sequential build:

| Page | Tokenizer alone | Whole parse | Tokenizer's share |
|---|---:|---:|---:|
| ecma262 | 0.0757 | 0.1773 | 43 % |
| html5 | 0.0627 | 0.1557 | 40 % |
| apollo11 | 0.0116 | 0.0209 | 56 % |

- **Criterion: tree construction and the text copy first.** The tokenizer
  takes 43 and 40 percent of the parse on ecma262 and html5, under half,
  though it runs 60 percent of html5's instructions.
- The `--par` build shows no trend with workers: at one, two and four
  workers it is 9 percent faster (html5's parse at four) to 8 percent
  slower (apollo11's tokenizer at one) than the sequential build.
- The tokenizer's share is an estimate: without tree construction it never
  switches to raw text, RCDATA or script data.

The raw output is in `runs/10-tokenize-58fa8ee.txt`, and the callgrind
summary in `runs/9-callgrind-parse-075f359.txt`.

**The owner's ruling.** Parsing is left for now: at four workers it is 12
to 18 percent of the pipeline, while style takes 70 to 80 percent. Copying
runs of plain text whole, the cheapest shortening of parsing's chain,
comes after style.

### Style's work per element

Style runs in parallel already (shape C, 3.6 times faster at four workers
than sequentially), yet takes 0.79 s on ecma262 and 1.02 s on html5 at four
workers, 70 to 80 percent of the pipeline. Callgrind on ecma262's style
computation (sequential driver built from commit 58fa8ee, collection
limited to `compute_styles`): 32,248 million instructions, about 180,000
per element.

- Selector matching takes 65 percent: `match_complex` 34, `instr_matches`
  23 and `backtrack` 8. `match_element` tests every rule of the store
  against every element, so `match_complex` runs 106 million times, about
  590 times per element; most of those rules cannot match the element,
  since their rightmost compound names another id, class or tag.
- `memset` takes 21 percent, 99 percent of it under `match_complex`: each call
  creates `slots_new::<Frame, 64>()` for its backtracking, and the compiled
  code clears the 64 frames, though a frame past the window's length is
  never read.
- `match_element`'s own loop takes 12 percent.

The raw summary is in `runs/11-callgrind-style-58fa8ee.txt`.

**A rule index** (the owner's choice). Each alternative of a rule's selector
list keys the rule by its subject compound, the rightmost one: by its id if
it has one, else its first class, else its type, each as a hash of the
name's ASCII-lowercased bytes; a rule with an alternative that has none of
them goes to a list tested against every element, and an alternative that
never matches keys nothing. An element tests only the rules under the
hashes of its own id, its class words and its local name, and that list,
with the same `selector_matches` as before. A rule it skips has no
alternative whose subject names the element's id, a class of it or its
type, even ignoring case and namespace, so it cannot match: the matched
rules, and so the cascade, are exactly those of matching every rule, and
hash collisions only add rules to test.

Criteria, written before measuring:

1. **Equality.** `proto_style check` passes on all seven pages (shapes A, B
   and C agree and the intern pass is sound), and every page's style
   checksum in shape C equals the one before the change.
2. **Speedup.** Shape C's style stage at four workers is at least 3 times
   faster on ecma262 and on html5 than before, measured in the same run
   against the previous driver.

**Results.** At Snowghost commit ec21b7c, `proto_style check` passes on all
seven pages, and every page's shape C checksum equals the one of the driver
built from 7e2ada4, before the index (`runs/12-style-check-ec21b7c.txt`). A
build whose index skips the class buckets fails the check on ecma262 ("A
differs from C at preorder element 59", `runs/17-negative-controls.txt`).
`--par-ledger` still splits `match_elements` (`runs/18-style-ledger-95b9073.txt`
records it at the end of this work). A one-shot script under the lock
(`runs/13-style-index-script.sh.txt`) timed shape C with five repetitions,
best of three, both drivers in the same run (`runs/13-style-index-ec21b7c.txt`),
seconds per repetition:

| Page | Rules | Before, W4 | After, W4 | Speedup | Before, seq | After, seq |
|---|---:|---:|---:|---:|---:|---:|
| ecma262 | 336 | 0.696 | 0.218 | 3.19 | 2.568 | 0.698 |
| html5 | 324 | 0.942 | 0.734 | 1.28 | 3.522 | 2.710 |
| apollo11 | 1,558 | 0.416 | 0.198 | 2.10 | 1.512 | 0.792 |

- **Criterion 1: met.**
- **Criterion 2: met on ecma262, not on html5.**
- **What html5 spends its time on.** Callgrind on html5's shape C with
  the index (`runs/14-callgrind-style-html5-ec21b7c.txt`): 24,587 million
  instructions, 61 percent in `nth_scan` and 18 in `nth_qualifies`, which
  evaluate `:nth-child` and `:nth-of-type` by counting the element's
  siblings each time, so a rule of that kind costs time in proportion to
  the element's position among its siblings, which points to long sibling
  runs on html5; their lengths are not measured. The index cannot remove
  those tests, since such a rule's subject is a common type or none, and
  the rest of matching is about 20 percent.

**Sibling positions** (the owner's choice). Every `:nth-child`,
`:nth-last-child`, `:first-child`, `:last-child`, `:only-child` and their
`-of-type` forms reads one result of a sibling count: the element's 1-based
position among its parent's element children, or among those with its
namespace and local name, and their total. One pass over the document,
before matching, records both pairs for every element, walking each
parent's children twice, first to number them and then to write their
totals, and counting each type with a table indexed by its atom; matching reads them instead of counting. `:nth-child(An+B of S)` and
`:nth-last-child(An+B of S)` depend on S and keep counting. The pass takes
time in proportion to the nodes, where counting took time in proportion to
the element's position for every test.

Criteria, written before measuring:

1. **Equality.** `proto_style check` passes on all seven pages and every
   page's shape C checksum equals the one before the change.
2. **Speedup.** Shape C's style stage at four workers on html5 is at least
   3 times faster than with the rule index alone (0.734 s), measured in the
   same run against that driver, and no slower on ecma262 and apollo11.

**Results.** Commit aacd878 walked each parent's children with a counted
loop that ran to the node count whatever the list's length, work in
proportion to the square of the nodes, and a first timing run stopped at
its ten-minute limit; 0c66df9 leaves the walk at the last sibling. At
0c66df9, `proto_style check` passes on all seven pages with every shape C
checksum unchanged (`runs/16-style-check-0c66df9.txt`), and a build whose
child positions are off by one fails the check on html5 and ecma262 ("A
differs from C", `runs/17-negative-controls.txt`). `--par-ledger` still
splits `match_elements`. The one-shot script (`runs/15-style-positions-script.sh.txt`) timed shape C
with the rule index alone (ec21b7c) and with positions too (0c66df9) in one
run, five repetitions, best of three (`runs/15-style-positions-0c66df9.txt`),
seconds per repetition:

| Page | Index, W4 | Positions, W4 | Speedup | Index, seq | Positions, seq |
|---|---:|---:|---:|---:|---:|
| ecma262 | 0.210 | 0.224 | 0.94 | 0.700 | 0.700 |
| html5 | 0.730 | 0.180 | 4.06 | 2.600 | 0.578 |
| apollo11 | 0.206 | 0.202 | 1.02 | 0.756 | 0.754 |

- **Criterion 1: met.**
- **Criterion 2: met on html5, not on ecma262,** which is 7 percent slower
  at four workers and as fast sequentially. A likely cause, not measured:
  the position pass runs in sequence before the parallel matching loop, so
  what it costs is not divided among the workers, and ecma262 may have
  little sibling counting for it to save; neither the pass's own time nor
  ecma262's sibling counting is measured.
- Against shape C before the rule index, style at four workers now takes
  0.224 s on ecma262 (0.696 s before), 0.180 s on html5 (0.942 s) and
  0.202 s on apollo11 (0.416 s), each from its own run.

**Keeping `selector_matches` free of allocation.** The review found that
0c66df9's `selector_matches`, the scanning entry the oracle and shapes A
and B call, created four empty position arrays on every call, against its
documented promise to allocate nothing, and that shape A took 6.13 s
against 3.08 s for one repetition on ecma262. At 95b9073 the positions are
one table of four words per node, the matcher's internal functions take it
as a slice, and `selector_matches` passes an empty slice of a local array.
Shape A still takes 6.63 s against 5.88 s for two repetitions (best of
three, sequential), 13 percent more, recorded in `docs/todo.md`. The same
script timed the final drivers again (`runs/19-style-positions-95b9073.txt`),
and every page's shape C checksum is unchanged at 95b9073
(`runs/20-style-check-95b9073.txt`):

| Page | Index, W4 | Positions, W4 | Speedup | Index, seq | Positions, seq |
|---|---:|---:|---:|---:|---:|
| ecma262 | 0.236 | 0.258 | 0.91 | 0.770 | 0.792 |
| html5 | 0.832 | 0.206 | 4.04 | 3.002 | 0.652 |
| apollo11 | 0.230 | 0.226 | 1.02 | 0.852 | 0.860 |

The rule index driver, the same in both runs, took 10 to 16 percent longer
in this one, and the verdicts hold: html5 met, ecma262 9 percent slower at
four workers.

**How the position pass fits the pipeline tree.** The `pipeline` tree asks
every stage to keep only its algorithm's data dependencies and to run
incrementally. The pass here is one sequential walk of the whole document
sharing its type counters across parents. Its data dependencies are
narrower: one parent's children depend only on that parent's child list, so
the pass could count per parent in parallel and, after a change, recount
only the parents whose children changed. That form is not built or
measured here; it is the candidate when the pass's cost or incremental
style needs it.


### Whitefoot: an equality requirement over range lengths

`range-length-probe.wf` in this directory passes two ranges with the same
non-constant bounds, `&a.inner[low..high]` and `&b.inner[low..high]`, to a
function that `requires first^.len == second^.len`. `whitefootc` rejects
the call with FN-8 UndischargedCallRequirement, disposition Unproved, also
after a proved `invariant equal: first^.len == second^.len;`. It accepts
the call when both ranges start at `0_u64`, and when the requirement is
written as `first^.len <= second^.len` and `first^.len >= second^.len`,
the form the style prototype's `style_level` uses.
