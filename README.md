# Snowghost-wf

Snowghost-wf, Snowghost for short, is a cross-platform renderer for user
interfaces built with web technology. It implements a chosen subset of the
web platform: the part that mainstream sites and the applications AI coding
tools generate actually use. Its renderer is written in
[Whitefoot](https://github.com/Ming-Research/Whitefoot), a systems language
whose compiler proves memory safety, the absence of data races and silent
overflow, and the independence it uses to run code in parallel; a shell
written in Rust hosts it on each operating system.

The aim is a light platform for web-built applications, with a rendering
pipeline that is parallel and incremental from end to end: a change to one
element reruns only the stages and the parts of the page it affects, and
every part of every stage that does not depend on another runs in parallel.
The renderer keeps only each algorithm's true dependencies and leaves the
grain of parallel work to the Whitefoot compiler.

## Why

In today's engines a change to a layout property reruns most of the
rendering pipeline, and only what the compositor handles alone, such as
transform and opacity animations, stays fast. Their stages are tuned one by
one for what may be reused. Snowghost treats incrementality as a question of
data coupling instead. Work that a change does not reach is not computed
again, and in Whitefoot that independent work is also provably parallel.

Snowghost is also Whitefoot's large real program. It shows what Whitefoot's
proofs give a renderer, and it exposes what the language still lacks. The
first question it answers is whether a pipeline built this way beats the
engines in use today, measured on the same pages and the same edits.

## Status

Snowghost is a research renderer. It renders headless, to laid-out boxes, and
does not yet paint.

- **Built:**
  - HTML tokenizing and tree construction;
  - CSS parsing, selector matching and a level-parallel cascade;
  - layout of block and inline flow, floats, flex, grid, tables and a subset
    of multi-column;
  - font loading and HarfBuzz-compatible shaping for simple scripts, and line
    breaking;
  - PNG decoding, URL parsing and Unicode normalization.
- **Incremental:**
  - layout is kept across edits and updated from marks that each edit pushes;
  - the style stage restyles only the elements an edit can reach;
  - every incremental result is checked byte for byte against a full build.
- **Measured against Chromium:**
  - **Pages and edits:** the ECMAScript specification, the HTML
    specification and a Wikipedia article, with word, sentence, colour,
    font-size, root font-size and block edits.
  - **Results:** at the end of the incremental style stage, Snowghost costs
    less than Chromium 141 per edit on 15 of 18 page and edit pairs,
    sequentially. It trails on one font-size edit and on the three block
    edits ([E1](research/investigations/engine-comparison/DESIGN.md),
    [M1 results](research/investigations/incremental-style/DESIGN.md#results)).
- **In progress:**
  - **M2:** an inserted or removed element costs in proportion to what it
    reaches ([structural edits](research/investigations/structure-edits/DESIGN.md)).
- **Not started:**
  - paint;
  - the Rust shell, with rasterization, compositing, windows and input;
  - the JavaScript interpreter.

[`docs/todo.md`](docs/todo.md) lists the known defects and the Whitefoot
features Snowghost is waiting for.

## How it is built

- **Two processes**
  ([`design/processes.md`](design/processes.md)). The renderer, in
  Whitefoot, owns the document, style, layout, text, paint, script and image
  decoding. The shell, in Rust, owns windows, input, accessibility,
  rasterization, compositing, networking and storage. They exchange data,
  not calls: the renderer sends facts about the page, and the shell decides
  how to draw them.
- **Every stage keeps only its true dependencies**
  ([`design/pipeline.md`](design/pipeline.md)). Any other ordering is
  written in forms the compiler proves independent, and the compiler and
  runtime decide what runs in parallel and at what grain.
- **A stage kept across edits learns what changed from marks the edit
  pushes.** It is checked against a full build, because the compiler proves
  which places a function reads but not their versions.
- **Chromium is the reference.** Where a specification and Chromium differ,
  the renderer follows Chromium and records the difference.
- **The subset is chosen feature by feature**
  ([`design/scope.md`](design/scope.md)), weighing how much sites use a
  feature against what it costs in performance.

Correctness is judged by oracles independent of Snowghost:
- html5lib's and web-platform-tests' (WPT) parsing cases;
- WPT's selector and URL cases;
- the CSS parsing tests, the Unicode data files and PngSuite;
- Chromium's computed styles and box rectangles, driven headless through
  Playwright.

## Repository layout

| Path | Contents |
|---|---|
| `renderer/` | The renderer's Whitefoot modules, one directory per package; `modules.wfg` is the module graph |
| `renderer/oracle/` | Drivers that run a stage and print its output for the oracles |
| `tests/` | The oracles' scripts and focused case pages |
| `design/` | The decisions the project is built on, each with its reason and refused alternatives, and the log of the owner's approvals |
| `design/skill/` | [Design-skill](https://github.com/Ming-Research/Design-skill), as a submodule: the design tree's lint and CI base script |
| `research/investigations/` | One directory per question: its design, experiments, measurements and rejected alternatives |
| `docs/` | The review checklist, and the TODO of known defects and Whitefoot requirements |
| `whitefoot.pin` | The Whitefoot compiler release the renderer builds with, `release = wf-<12 hex digits of its commit>` |
| `whitefoot-kit/` | [Whitefoot-kit](https://github.com/Ming-Research/Whitefoot-kit), as a submodule: the build rules and downstream rules shared by projects written in Whitefoot |

## Building and checking

```sh
git clone --recurse-submodules https://github.com/Ming-Research/Snowghost-wf.git
cd Snowghost-wf
make check
```

`make check` downloads the Whitefoot compiler release that `whitefoot.pin`
names, builds the renderer, runs the
document arena's self-test and lints the design tree. It runs on Linux
x86-64 and macOS arm64, and needs Git, Python 3, curl, clang at
`/usr/bin/clang` and, on Linux, LLD. CI runs it on every push.

The oracles are separate `make oracle-*` targets. They need network access
for their test suites and, for the Chromium oracles, Node.js and Playwright.

## How the work is organized

Most of the code is written by coding agents and reviewed by the project's
owner.
- [`AGENTS.md`](AGENTS.md) holds the goal, the priorities and the
  project's own rules.
- Every design decision lands in the design tree and is approved by the
  owner before it reaches `main`.
- An investigation under `research/investigations/` writes its question and
  the result that would reject it before it measures.

## License

MIT; see [LICENSE](LICENSE).
