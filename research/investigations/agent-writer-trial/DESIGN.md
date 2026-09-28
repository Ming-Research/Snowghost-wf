# Agent writer trial

Status: planned. The criterion below is fixed before any run.

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

None yet.
