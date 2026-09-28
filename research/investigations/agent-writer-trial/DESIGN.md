# Agent writer trial

Status: running. The criterion below was fixed before any run; the results
so far are recorded at the end.

## Question

Which model should implement each class of Snowghost's leaf modules? The
owner expects Opus to meet the bar and is unsure about Sonnet, and judges
Haiku likely too weak. Each task therefore runs once, starting on Sonnet,
and the supervisor moves it to Opus when Sonnet's code falls short.

The trial also shows how agents learn current Whitefoot and which source
patterns work for this code. `whitefoot/docs/patterns.md` lags the language,
so the trial does not supply it. Snowghost is where current patterns are
tried, and the patterns the runs establish are recorded here.

## Tasks

Each task is one leaf module behind an interface the architect writes before
any run, and each is judged by an oracle independent of Snowghost. The three
tasks stand for three classes of implementer work.

1. **Line breaking**, a table-driven algorithm: the break opportunities of
   Unicode UAX #14 for a sequence of code points, Unicode 17.0.0. The oracle
   is `LineBreakTest.txt`; the property tables come from `LineBreak.txt` and
   the other data files the algorithm names, `EastAsianWidth.txt`,
   `DerivedGeneralCategory.txt` and `emoji-data.txt`. The implementer also
   writes the program that generates the tables.
2. **CSS syntax**, a specification-driven parser: tokenizing and parsing
   component values under CSS Syntax Module Level 3. The oracle is the 50
   cases of `component_value_list.json` in css-parsing-tests at revision
   203ce36b, which also fixes that suite's error reports and legacy
   tokens.
3. **PNG decoding**, a performance-sensitive decoder: decoding to 8-bit RGBA.
   The oracle is PngSuite 2017jul19: its 162 valid images decoded by libpng,
   and its 14 corrupted images, which must be rejected. Speed is measured
   against libpng on a fixed set of large images.

## Setup

- **The package.** Snowghost's renderer is a Whitefoot module program rooted
  at `renderer/`. Each task's interface is a module (`pkg::text::line_break`,
  `pkg::css::syntax`, `pkg::image::png`) whose `module.wfm` is written
  before the runs. A driver module per task (`pkg::oracle::line_break`,
  `pkg::oracle::css_syntax`, `pkg::oracle::png`) has a graph entry that runs
  the oracle through the interface and prints the number of cases that pass
  and fail.
- **Oracle data.** `make oracle-data` (`tests/oracle-data.sh`) downloads
  each file at its pinned version, checks its SHA-256 and places it under
  `build/oracle/`, which git ignores. `make oracle-line-break`, `oracle-css`,
  `oracle-png` and `oracle-png-speed` build each driver entry and run it; the
  CSS driver prints its results as JSON, which `tests/css/oracle.py` compares
  with the suite.
- **PNG reference.** `tests/png/reference.c` decodes each image with
  libpng into raw RGBA for the driver to compare. It also generates the
  speed set: twelve 2048 by 2048 images of gradients, noise, synthetic text
  and an interface mock-up across the color types, 16-bit samples and Adam7,
  generated deterministically and encoded by libpng with default settings.
  On the trial container libpng 1.6.43 decodes the set in about 33 ms per
  image.
- **Supplied context.** Every run gets the same prompt: the task, the
  interface path, the relevant specification sections, and the commands to
  check the module and run its oracle. As references it gets the pinned
  Whitefoot specification, which is normative, the compiler's diagnostics
  and repairs, and the maintained programs under `whitefoot/tests/programs`
  and `whitefoot/lib/std`, which Whitefoot's gate compiles on every change.
  A run may not edit the interface, the driver or the data. An interface it
  finds insufficient is reported to the supervisor with a minimal example.
- **Isolation.** Each run works on its own branch from the same harness
  commit.

## Runs

- Each task runs once and starts on Sonnet. Haiku is not used for now.
- The supervisor reads the code as the run produces it. It moves the task to
  Opus when the code falls short: structure a reviewer would score below 3,
  misuse of the interface, or no progress toward acceptance over repeated
  repair cycles. Opus continues from the run's branch or starts afresh, as
  the supervisor judges.
- A run ends when the agent reports done or the supervisor stops it. Each
  run records the models used, the prompt, elapsed time, tool calls, tokens
  where reported, the supervisor's interventions and escalations with their
  reasons, and the final revision.

## Observations

These are kept apart, as the investigation skill requires:

1. **Expression**: whether the module and its proofs can be expressed in
   Whitefoot at all.
2. **Writing**: whether the model reached a module Whitefoot accepts, and
   how many rejections it repaired on the way.
3. **Composition**: whether the module passes its oracle through the
   architect's driver with the interface unchanged.
4. **Runtime cost**: PNG decoding speed against libpng. Throughput is also
   recorded for the other two tasks, without a goal.

Also recorded: a separate reviewer's score, the supervisor's interventions,
the Whitefoot rejections that took more than one attempt to repair, and the
source patterns that worked.

## Criterion

A task is done when all of these hold:

1. `whitefootc --check-module` accepts the module against its unchanged
   interface, and the graph builds;
2. its oracle driver reports every case passing;
3. a separate reviewer scores it at least 3 of 5 for readability, interface
   fidelity and use of Whitefoot;
4. the supervisor gave it at most two interventions with information the
   prompt did not contain;
5. for PNG decoding, it decodes the speed set in at most three times
   libpng's single-thread time on the same machine.

The model that finishes a task sets the default model for its class. A task
Sonnet finishes alone makes Sonnet the default; a task moved to Opus makes
Opus the default, and Sonnet is tried again on that class only when the
supervisor sees reason to. A default holds until a later task of the class
contradicts it. A failure caused by a missing Whitefoot feature, a
documentation gap or an insufficient interface is fixed at its source before
the task continues.

## Results

Runs started 2026-09-28 at 09:41 UTC from harness commit 5290d73, each on
its own branch (`trial/run-css`, `trial/run-line-break`, `trial/run-png`).
One harness defect showed during the runs: the run worktrees had an empty
`whitefoot/` submodule, so the reference paths in the prompt did not exist.
The supervisor sent the corrected paths to the line-break and PNG runs; this
corrected the harness and gave no information about the code, so it is not
counted as an intervention. The CSS run found the files on its own.

### CSS syntax: Sonnet, done

- **Criterion:** met. The module checks against the unchanged interface; all
  50 cases pass (rerun independently); the reviewer scored it 4 of 5; no
  interventions.
- **Run:** about 31 minutes, 106 tool calls, about 405,000 tokens; six files,
  1,964 lines; the module checks in 0.3 s.
- **Reviewer:** readability 4, interface fidelity 4, use of Whitefoot 3,
  performance 4. Defects: output buffers grow by hand-written doubling whose
  full branch silently drops the byte instead of proving room; block kinds
  are `u8` codes rather than an enum; nesting recurses once per block, so a
  16 MiB input of `(` recurses millions of levels.
- **Default for the specification-driven class: Sonnet.**

### Line breaking: Sonnet, done

- **Criterion:** met. The module checks; all 19,338 cases pass (rerun
  independently); the generator reproduces the checked-in tables byte for
  byte from the Unicode 17.0.0 files; the reviewer scored it 3 of 5; no
  interventions.
- **Run:** about 60 minutes, 354 tool calls, about 657,000 tokens; 2,620
  lines plus 50 KB of generated tables (2,637 class ranges searched by
  bisection). The oracle's 19,338 cases run in 25 ms.
- **Reviewer:** readability 3, interface fidelity 4, use of Whitefoot 3,
  performance 3. Defects: one 437-line function holds LB4 to LB31; classes
  are `u8` codes; guards that should be proved instead silently skip; the
  generator depends on the oracle drivers' support module; two bisections
  per code point where a two-stage table would take one or two loads; a
  fallback past 100 million code points marks every position Allowed, which
  the interface does not state. That last one is the interface's fault: it
  set no length bound, so the writer invented one.
- **Default for the table-driven class: Sonnet**, at the bar.

### PNG decoding: Sonnet, then Opus

- Sonnet reached a correct decoder (all 176 cases) in about 88 minutes, 418
  tool calls and about 657,000 tokens, but decoded the speed set at 2.9 to
  3.3 times libpng's time, over the bar. Under the escalation rule the task
  moved to Opus, continuing from its branch at 8ac3741.

### Whitefoot findings

- **No text literals** made every message a byte array and every character
  a number (card #18): Whitefoot PR #166 adds them.
- **Range lengths:** two ranges formed at a call could not be related by
  `==`, and the repair for a range-length goal misled the writer (card #19):
  Whitefoot PR #167.
- **An allocation count without a target-sized bound** passes the module
  check and fails the build with no source location: being fixed in
  Whitefoot.
- Friction the language keeps by design (card #20): flat three-address form,
  exhaustive matches without a wildcard, explicit `move`, exact effect rows.
  Each run named the flat form as its largest source of length.

### Patterns the runs establish

- **Prove capacity or refuse; never skip silently.** Every run wrote guards
  of the form `if room { place_back(...) }` whose false branch does nothing,
  where the capacity was sufficient by construction. Size storage up front
  and carry the bound in a contract (the standard library's `GrowVector`
  requires `len < ceiling`), or return the module's error variant when the
  bound can fail.
- **State size limits in the interface.** A `requires` bound on every input
  length keeps the implementer from inventing a fallback.
- **Enums for internal classifications**, so a match checks every case.
- **Explicit stacks for input-driven nesting.** Stack exhaustion is outside
  Whitefoot's outcome model, so recursion depth must not follow the input.
- **Tools depend on the standard library,** not on test support modules.
