# Snowghost-wf — agent instructions

Snowghost-wf, Snowghost for short, is a cross-platform renderer for user
interfaces built with web technology: a chosen subset of the web platform
rendered in Whitefoot by a pipeline that is parallel and incremental end to
end, hosted on each operating system by a shell written in Rust (the
`processes` decision in `design/`). The owner-wide agent instructions
(mbbill/agents_config) apply with this file.

## Goal and priorities

Snowghost serves Whitefoot: it is the large real program that shows what
Whitefoot gives a renderer and exposes what Whitefoot still lacks. Reach, as
early as possible, renderings and measurements that show whether an
end-to-end parallel and incremental pipeline written in Whitefoot beats the
engines in use today, then grow to the subset of the web that mainstream
sites and generated applications need.

When priorities conflict:

1. reach the next end-to-end rendering milestone or performance comparison;
2. render correctly for the subset Snowghost claims, with every safety check
   Whitefoot requires;
3. keep the implementation understandable and easy to change;
4. add only the evidence needed to trust the current result;
5. defer robustness, infrastructure and polish that no current milestone
   needs.

**Parallelism is maximal, not chosen** (the `pipeline` decision): every stage
keeps only its algorithm's true data dependencies and writes all other work
in forms Whitefoot proves independent, leaving which work runs in parallel,
and at what grain, to the compiler and runtime. A sequential step names the
dependency that forces it.

**Design for parallelism first.** Every choice between alternatives, of a
stage, an algorithm, a data structure or an interface, starts by writing out
each candidate's dependencies. The shortest chain of true dependencies is
preferred, and extra or duplicated work that shortens it is a valid trade. A
recommendation that adds an order the algorithm does not need, such as a
cache or table shared across elements, a sequential pass or a global
counter, names the dependency that forces it or is not recommended. Measured
speed decides only between candidates of equal dependencies.

## References and evidence

- `design/` holds the decisions Snowghost is built on. A design decision is a
  choice between viable alternatives that changes rendered behavior, a safety
  or trust condition, a shared interface or representation, a significant
  performance commitment or a standing project rule. Read the nodes a change
  touches and their ancestors before changing code.
- Work is not planned in a document up front: a selected direction gets
  `research/investigations/<name>/`, which writes, before measuring, the
  question, the comparison that could answer it either way and the result
  that would reject the proposal; its surviving decision goes to the tree.
  An agent writer trial records the model, prompt, context, turns and time of
  each run, and keeps apart expressibility, the agent's success with the
  supplied help, composition and cost.
- The pinned Whitefoot commit defines the language; read it as
  [whitefoot-kit/downstream.md](whitefoot-kit/downstream.md#reading-the-language)
  describes. Whitefoot's `docs/patterns.md` lags the language; Snowghost is
  where current source patterns are tried. Cite the language from the pinned
  revision, never from Snowghost's code.
- A claim cites a design-tree decision, an investigation, a measurement with
  its workload, environment and comparison, or an oracle independent of
  Snowghost: a test suite, a format's conformance files, a specification's
  example or a reference renderer's output, never Snowghost's earlier output.
  Research and PRs may cite a decision as rationale, not as proof of an
  empirical claim.
- A performance comparison names its workload, machine, engine versions and
  settings, and measures every engine under the same conditions; a
  performance change is attributed with a same-source before-and-after
  comparison and a falsifier.
- No site, page, test or benchmark selects a special path in the renderer.
- Process wording in older artifacts, such as early investigations, is
  superseded by this file and the owner-wide instructions.

## Design tree

Live trees: the root node files under `design/` other than `log.md`, each
with its subdirectory, found by the Makefile. Change log: `design/log.md`.
Research record: `research/investigations/`. Maintained TODO: `docs/todo.md`,
which also holds Whitefoot requirements. Form and readiness checks:
`make design-lint` and `make design-ready`, running `lint.py` from the
`design/skill/` submodule of Design-skill.

## Agent roles

- The owner and the primary agent own the architecture: the design tree, the
  module graph, the Whitefoot module interfaces (`.wfm`) with their contracts
  and effect rows, and the format the renderer and the shell exchange.
- Implementer agents write module bodies (`.wf`) against those interfaces,
  and the shell's Rust components against that format. An implementer that
  finds an interface or the format insufficient reports the gap to the
  primary agent with a minimal example instead of editing it.

## Merge rules

1. Work-branch changes need no approval. A PR becomes ready only after the
   owner has approved every decision it needs, recorded in `design/log.md`
   and checked by `make design-ready`.
2. Every merge into `main` requires owner approval of the exact revision.
3. The exact revision merged into `main` passes `make check` first.
4. A change that moves `whitefoot.pin` or the `whitefoot-kit/` or
   `design/skill/` submodule names the revisions it adopts and why; a
   revision merged into `main` pins commits on those repositories' `main`,
   for Whitefoot a release `wf-<12 hex>`, never an experiment release.

The exact revision is the complete tree that will enter `main`, the pin and
submodules included; if it changes after approval or after its check, rules 2
and 3 apply again. No other step is a merge precondition. Dependent PRs are
stacked, each on the branch of the one before it.

## Checks

- `make check`, the gate, in CI on every push: downloads the compiler release
  `whitefoot.pin` names (Whitefoot-kit's `whitefoot.mk`), builds the renderer,
  runs the document arena's self-test and lints the design tree. It needs
  git, Python 3, curl, `/usr/bin/clang`, LLD on Linux and the `design/skill`
  and `whitefoot-kit` submodules; `make check WHITEFOOTC=<path>` uses another
  compiler.
- `make design-ready` and `make pin-ready`, in CI on ready PRs and `main`:
  every tree change is approved in the log, and the pin names no experiment
  release.
- The oracles are the `make oracle-*` targets, outside `make check`.

## Review

A change that edits `design/` or the renderer-shell format, adds or changes a
module interface, or changes more code than a small fix gets the owner-wide
completion review, by a separate read-only agent with the prompt and groups
in [docs/review-checklist.md](docs/review-checklist.md#how-to-review); other
changes need only the checks. The review's scope and fixed findings go in the
PR's review section.

## Whitefoot

Snowghost follows [whitefoot-kit/downstream.md](whitefoot-kit/downstream.md):
the pin, experiment pins for an unmerged Whitefoot change, Whitefoot gaps
recorded under *Whitefoot requirements* in `docs/todo.md`, and upgrades.
When an upgrade changes the compiler's code generation, its PR compares the
renderer's full-build and per-edit costs before and after on the same source
and machine. A change to the shared rules is made in Whitefoot-kit and adopted
by moving the submodule.

## Reports

A completion report also names any Whitefoot pin or submodule moved and any
Whitefoot gap filed.

## Documents

`README.md` introduces and navigates; this file holds the goal and project
rules; `design/` the decisions and their log; `docs/review-checklist.md` the
review items; `docs/todo.md` open defects and Whitefoot requirements until
resolved; `research/investigations/` questions, experiments and results; the
PR description the current change. None narrates editing history.
