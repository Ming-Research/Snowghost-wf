# Agent writer trial

Status: planned. The criterion below is fixed before any run.

## Question

Which model should implement each class of Snowghost's leaf modules? Sonnet
is the expected implementer. Haiku runs the same tasks as a comparison, and
Opus runs a task only where Sonnet fails it.

The trial also shows how agents learn current Whitefoot and which source
patterns work for this code. `whitefoot/docs/patterns.md` lags the language,
so the trial does not supply it. Snowghost is where current patterns are
tried, and the patterns the runs establish are recorded here.

## Tasks

Each task is one leaf module behind an interface the architect writes before
any run, and each is judged by an oracle independent of Snowghost. The three
tasks stand for three classes of implementer work.

1. **Line breaking**, a table-driven algorithm: the break opportunities of
   Unicode UAX #14 for a sequence of code points. The oracle is
   `LineBreakTest.txt`; the property tables come from `LineBreak.txt` and
   the other data files the algorithm names, all from one pinned Unicode
   version.
2. **CSS syntax**, a specification-driven parser: tokenizing and parsing
   component values under CSS Syntax Module Level 3. The oracle is the
   tokenization and component-value tests of css-parsing-tests at a pinned
   revision.
3. **PNG decoding**, a performance-sensitive decoder: decoding to 8-bit RGBA.
   The oracle is the valid images of PngSuite decoded by libpng. Speed is
   measured against libpng on a fixed set of large images.

## Setup

- **The package.** Snowghost's renderer is a Whitefoot module program rooted
  at `renderer/`. Each task's interface is a module (`pkg::text::line_break`,
  `pkg::css::syntax`, `pkg::image::png`) whose `module.wfm` is written
  before the runs. A driver module per task (`pkg::oracle::line_break`,
  `pkg::oracle::css_syntax`, `pkg::oracle::png`) has a graph entry that runs
  the oracle through the interface and prints the number of cases that pass
  and fail.
- **Oracle data.** `make oracle-data` downloads each file at its pinned
  version, checks its SHA-256 and places it under `build/oracle/`, which git
  ignores.
- **PNG reference.** A C program under `tests/` decodes each image with
  libpng into raw RGBA for the driver to compare. It also generates the
  speed set: twelve 2048 by 2048 images of gradients, noise and synthetic
  text, generated deterministically and encoded by libpng with default
  settings.
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

- Sonnet and Haiku each attempt all three tasks.
- Opus attempts a task only if Sonnet's run fails the criterion.
- A run ends when the agent reports done or the supervisor stops it. Each
  run records the model, the prompt, elapsed time, tool calls, tokens where
  reported, supervisor interventions and the final revision.

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

A run meets the bar when all of these hold:

1. `whitefootc --check-module` accepts the module against its unchanged
   interface, and the graph builds;
2. its oracle driver reports every case passing;
3. a separate reviewer scores it at least 3 of 5 for readability, interface
   fidelity and use of Whitefoot;
4. the supervisor gave it at most two interventions with information the
   prompt did not contain;
5. for PNG decoding, it decodes the speed set in at most three times
   libpng's single-thread time on the same machine.

For each class, the cheapest model whose run meets the bar is assigned the
class, in the order Haiku, Sonnet, Opus. A class no model meets is analyzed
before anything reruns: the failure is filed as a Whitefoot requirement, a
documentation gap or an interface change, and the task reruns after that
fix. An assignment holds until a later task of the class contradicts it.

## Results

None yet.
