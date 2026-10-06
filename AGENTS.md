# Snowghost-wf — agent instructions

Snowghost-wf, Snowghost for short, is a cross-platform renderer for user
interfaces built with web technology: a chosen subset of the web platform
rendered in Whitefoot by a pipeline that is parallel and incremental end to
end, hosted on each operating system by a shell written in Rust (the
`processes` decision in `design/`).

## Goal and first priorities

Snowghost serves Whitefoot: it is the large real program that shows what
Whitefoot gives a renderer and exposes what Whitefoot still lacks. Reach, as
early as possible, renderings and measurements that show whether an
end-to-end parallel and incremental pipeline written in Whitefoot beats the
engines in use today, then grow to the subset of the web that mainstream
sites and generated applications need.

1. Reach the next end-to-end rendering milestone or performance comparison.
2. Render correctly for the subset Snowghost claims, with every safety check
   Whitefoot requires.

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

## References

- Research record: `research/investigations/<name>/`. Maintained TODO:
  `docs/todo.md`, which also holds the Whitefoot requirements.
- The language: the Whitefoot commit `whitefoot.pin` names, read as
  [whitefoot-kit/downstream.md](whitefoot-kit/downstream.md#reading-the-language)
  describes and cited from that revision, never from Snowghost's code.
  Snowghost is where current Whitefoot source patterns are tried.
- Oracles: Chromium is the reference renderer (the `pipeline` decision),
  through `tests/css/style_oracle.mjs` and `tests/layout/layout_oracle.mjs`;
  html5lib's and WPT's parsing, selector and URL cases, the CSS parsing
  tests, the Unicode data files and PngSuite, all through the
  `make oracle-*` targets.
- Performance: E1 (`research/investigations/engine-comparison/`) compares
  Snowghost with Chromium on the ecma262, html5 and apollo11 pages of
  `research/investigations/concurrency/run.sh` with X5's edit scripts
  (`research/investigations/incremental-layout/run.sh`).

## Checks

- `make check`, the gate, in CI on every push: downloads the compiler release
  `whitefoot.pin` names (Whitefoot-kit's `whitefoot.mk`), builds the renderer,
  runs the document arena's self-test and `make design-lint`. It needs git,
  Python 3, curl, `/usr/bin/clang`, LLD on Linux and the `design/skill` and
  `whitefoot-kit` submodules; `make check WHITEFOOTC=<path>` uses another
  compiler.
- The readiness check adds `make pin-ready`: `whitefoot.pin` names no
  experiment release.
- Review checklist: [docs/review-checklist.md](docs/review-checklist.md).

## Whitefoot

Snowghost follows [whitefoot-kit/downstream.md](whitefoot-kit/downstream.md)
for the pin, experiment pins, Whitefoot gaps and upgrades. Its benchmarks
for an upgrade's comparison are the renderer's full-build and per-edit
costs: `.github/workflows/time-14900k.yml` with `BUILDS` naming the base
and the upgrade branch, `FULL=1` and every E1 edit kind.

## Reports

A completion report also names any Whitefoot pin or submodule moved and any
Whitefoot gap filed.

## Documents

`README.md` introduces and navigates; this file holds the goal and project
rules; `docs/review-checklist.md` the review items; `docs/todo.md` open
defects and Whitefoot requirements until resolved; `research/investigations/`
questions, experiments and results.
