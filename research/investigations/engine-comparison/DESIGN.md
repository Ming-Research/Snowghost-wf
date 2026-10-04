# Per-edit cost against Chromium (E1)

## Question

On the same pages, the same edits and the same machine, how does one edit's
cost in Snowghost, from the edited document to laid-out boxes, compare with
Chromium's, edit kind by edit kind? This is the first measurement against a
current engine (AGENTS.md, Project goal) and decides what comes next among
an incremental style stage and paint.

## Proposal under test

After X5 (`research/investigations/incremental-layout/`), Snowghost is
ahead of Chromium on text edits, where no style is recomputed and only the
edited paragraph and what it moves are laid out again, and behind on class
and structural edits, where Snowghost still runs the whole style stage.

Rejected if, at four workers on any of the three pages, the median text
edit (word or sentence) costs Snowghost as much as Chromium or more; or if
a class or block edit costs Snowghost less than Chromium on a page, which
would mean the style stage is not what decides those kinds.

## What is compared

- **Workloads.** The X5 pages (`ecma262`, `html5` at their pinned bytes,
  `apollo11` the supplementary capture of `runs/step3c.txt`) and X5's
  edit scripts (`run.sh prepare`), unchanged: word, sentence, colour,
  fontsize, rootfont and block, each edit followed by its inverse.
- **Chromium.** The Playwright build Chromium 141.0.7390.37, headless, a
  1280 by 720 viewport at device scale 1, page scripts disabled, driven
  through the DevTools protocol; the page and its sheets are served from
  the same bytes by request interception, as the layout oracle reads them.
  Each edit is applied in the page by DOM calls (insertData, deleteData,
  classList, insertBefore, remove; an `S` line adds its sheet as a style
  element before the first edit), then `documentElement.offsetHeight`
  forces style recalculation and layout; the cost is `performance.now`
  around the call and the forced layout, so paint and compositing are out.
  A node of an edit script is found by its position among text nodes or
  elements in tree order, which both parsers follow, and its text is
  checked against the script's node listing before the run.
- **Snowghost.** The layout oracle's incremental mode on the driver of
  `runs/step4b.txt` section 5, whose clock readings follow the work: for a
  text edit text_changed and update; for a class edit the style stage in
  full, the delta, font picks, styles_changed and update; for a block edit
  the traversal, the style stage, the delta, structure_changed and update.
  The style stage's time is now reported with each class or block edit
  (`style_us`), so a class or block edit's cost is `style_us` plus the
  layout update's. Sequential and four workers.
- **Not comparable, and recorded as such.** Chromium lays text out in the
  fonts macOS resolves for the pages' families, Snowghost in its 47 Debian
  files; the boxes differ in places, the work is of one kind. Chromium's
  style recalculation for a text edit is part of its cost, Snowghost has
  none to do there. Chromium's main thread is one thread; it shapes and
  rasterizes off it, which neither number includes.

## Measurement

Every run under the host lock. Probe one script per page first; then one
process run per script and kind, repeated only where the spread of
per-edit times is too wide to read a median. Report per page, kind and
build the median and maximum, Chromium's and Snowghost's, and their ratio.

## Results

First pass (`runs/e1.txt`, one run per script): Snowghost leads on text
edits on html5 (12 to 40 times) and ecma262 (1.1 to 3.5 times), is level on
apollo11 (behind on word edits at four workers, 1.34), which rejects the
proposal as written there; it is 150 to 7,000 times slower on class and
block edits, the full style stage (0.18 to 0.62 s at four workers) being
nearly all of it. Next: Chromium's durations from trace events, below its
timer's 100 us resolution.
