# Snowghost — agent instructions

Snowghost is a cross-platform renderer for user interfaces built with web
technology. Its renderer implements a chosen subset of the web platform in
Whitefoot, with a pipeline meant to be parallel and incremental from end to
end, and a shell written in Rust hosts it on each operating system (the
`processes` decision in `design/`). Whitefoot, the language and its compiler,
is pinned as the `whitefoot/` submodule.

## Project goal

Snowghost exists to serve Whitefoot: it is the large real program that shows
what Whitefoot gives a renderer and exposes what Whitefoot still lacks. Reach,
as early as possible, renderings and measurements that show whether an
end-to-end parallel and incremental pipeline written in Whitefoot beats the
engines in use today, then grow to the subset of the web that mainstream
sites and generated applications need.

When priorities conflict, use this order:

1. reach the next end-to-end rendering milestone or performance comparison;
2. render correctly for the subset Snowghost claims, with every safety check
   Whitefoot requires;
3. keep the implementation understandable and easy to change;
4. add only the evidence needed to trust the current result; and
5. defer robustness, infrastructure and polish that no current milestone
   needs.

Parallelism is maximal, not chosen: every stage keeps only its algorithm's
true data dependencies and writes all other work in forms Whitefoot proves
independent, leaving which work runs in parallel, and at what grain, to the
compiler and runtime (the `pipeline` decision in `design/`). Do not pick a
coarse unit of parallel work or add an order the computation does not need;
a sequential step names the dependency that forces it.

**Design for parallelism first.** Every choice between alternatives, of a
stage, an algorithm, a data structure or an interface, starts by writing
out each candidate's dependencies: which work depends on which result and
why, and which work is independent. The candidate with the shortest chain of
true dependencies is preferred, and taking extra or duplicated work to
shorten that chain is a valid trade. A recommendation that adds an order
the algorithm does not need, such as a cache or table shared across
elements, a sequential pass or a global counter, names the dependency that
forces it or is not recommended. Measured speed decides between candidates
of equal dependencies, not before.

## Authority and reading

`design/` holds the decisions Snowghost is built on, each with its reason and
refused alternatives. Work is not planned in a document up front: a selected
direction gets `research/investigations/<name>/` for its design, measurements
and rejected alternatives, and its surviving decision goes to the design
tree. Read only the material relevant to the task, and do not turn research
into an implied implementation requirement.

The pinned `whitefoot/` revision defines the language. Write Whitefoot from
its specification `whitefoot/spec/kernel-spec.md`, which is normative, the
compiler's diagnostics and repairs, and the maintained programs under
`whitefoot/tests/programs` and `whitefoot/lib/std`, which Whitefoot's gate
compiles on every change. `whitefoot/docs/patterns.md` lags the language and
is not a reference; Snowghost is where current source patterns are tried.
Snowghost never edits files under `whitefoot/`; see
[The Whitefoot boundary](#the-whitefoot-boundary).

A finished task is not evidence: a claim cites a design-tree decision, an
investigation, a measurement with its workload, environment and comparison,
or an oracle independent of Snowghost such as a test suite, a format's
conformance files or a reference renderer's output. Process wording in any
historical artifact, such as an older investigation, is superseded by the
rules below.

## How work proceeds

A *material choice* changes rendered behavior, a safety or trust condition, a
shared interface or representation, a significant performance commitment or a
standing project rule; only a material choice between viable alternatives is
a design decision. Restoring decided behavior or editing prose without
changing its meaning is routine.

1. **Before starting,** read the affected design-tree nodes and their
   ancestors, verify the worktree and PR state on resumption, and settle the
   direction with the owner as the `design-tree` skill describes.
2. **While working,** state why each material choice fits its evidence and
   record an experiment's criterion before using it to choose. Change the
   code and the design tree together on a Draft PR, and update what a changed
   conclusion affects in the same work.
3. **At completion,** run the [checks](#checks) and, when it applies, the
   [review](#review), then hand the work back as the skill describes, adding
   the validation run and its revision, what remains unverified, any
   `whitefoot/` pin moved or gap filed, and what the work found along the way.
4. **After the owner approves** every decision, write the log entry and mark
   the PR ready (rule 1 below).

**Fix or record what you notice.** When work exposes a defect elsewhere, such
as a bug, an awkward interface, duplicated logic or a stale document, fix it
in the same change if it is small and within the files you are changing;
otherwise add an item to `docs/todo.md` with its impact, the change you would
make and when to reopen it. List each in the PR's *Found along the way*
section with its disposition.

**Verify with observations that could have come out otherwise.** A passing
result is evidence only if a wrong result would have failed it. Make each new
check fail once for each way it can fail, and never check a transform against
its own output. Resolve every commit id, path, count and measurement with a
tool when you write it. Another agent's or a reviewer's report is a lead to
verify, not evidence. A green result reached by weakening a requirement does
not answer the original question.

Use a PR as the owner's review surface from the start, as a Draft until rule 1
below lets it become ready. Push coherent progress to the same branch and keep
its description and actual validation results current. A series of dependent
PRs is stacked, each on the branch of the one before it. Updating a
work-branch PR never authorizes a merge into `main`.

**The design tree.** The `design-tree` skill (`design/skill/`, linked from
`.claude/skills/` and `.agents/skills/`) is the one recurring procedure. Its
live trees are the root node files under `design/` other than `log.md`, each
with its subdirectory, which the Makefile finds and lints; its log is
`design/log.md`, its research record `research/investigations/`, its TODO
`docs/todo.md`, and its checks `make design-lint` and `make design-ready`.

**Investigations.** An investigation decides something. Before measuring,
write in `research/investigations/<name>/` the question, the comparison that
could answer it either way and the result that would reject the proposal;
the surviving decision goes to the tree. Attribute a performance change with
a same-source before-and-after comparison and a falsifier. An agent writer
trial keeps apart whether the program can be expressed in Whitefoot, whether
the tested agent writes it with the supplied help, whether separately written
modules compose, and whether it meets its cost goal, and records the model,
prompt, context, turns and time of each run.

## Agent roles

- The owner and the primary agent own the architecture: the design tree, the
  module graph and the Whitefoot module interfaces (`.wfm`), with their
  contracts and effect rows, and the format the renderer and the shell
  exchange.
- Implementer agents write module bodies (`.wf`) against those interfaces,
  and the shell's Rust components against that format, in parallel. An
  implementer that finds an interface or the format insufficient reports the
  gap to the primary agent with a minimal example instead of editing it.
- A separate reviewer agent that did not implement a change reviews it when
  the [review](#review) calls for one.
- The primary agent dispatches and supervises implementer and reviewer agents
  and chooses the model for each kind of task from measured agent writer
  trials.

## Branch and main boundary

These are the complete approval and merge rules:

1. Work-branch changes need no approval, including the design tree, code,
   tests, gate wiring and documentation, except that new repository-root
   entries require owner approval. A PR becomes ready only after the owner
   has approved every decision it needs, including every design-tree change;
   the approval is recorded in `design/log.md` only then, and
   `make design-ready` checks the record.
2. Every change merged into `main` requires owner approval of the exact
   revision to be merged.
3. The exact revision merged into `main` must pass `make check` before the
   merge.
4. A change that moves the `whitefoot/` pin names the Whitefoot revisions it
   adopts and why, and a revision merged into `main` pins a commit on
   Whitefoot's `main`.

**Exact revision** is the complete tree that will enter `main`, the
submodule pin included; if it changes after approval or after its successful
check, rules 2 and 3 apply to the new revision. No other workflow step is an
approval or merge precondition.

## Checks

- `make check`, the gate, in CI on every push and on the revision to merge.
  It needs git, Rust stable at least at the `rust-version` in
  `whitefoot/compiler/Cargo.toml`, Python 3 and the submodule
  (`git clone --recurse-submodules` or `git submodule update --init`). It
  builds the pinned compiler to `whitefoot/compiler/target/gate/whitefootc`,
  builds the renderer and runs the design lint.
- `make design-ready`, before marking ready and in CI on ready PRs and main:
  every design-tree change is approved in the log.

## Review

A substantial task gets one review at completion, and any task gets one when
the owner asks. A change is substantial when it edits `design/` or the
renderer-shell format, adds or changes a module interface, or changes more
code than a small fix; a small fix, a documentation change or a process
change needs only the checks. Start a separate, read-only agent that did not
implement the change, with the prompt in
[the review checklist](docs/review-checklist.md#how-to-review), then fix every
finding as the `design-tree` skill's workflow describes, push, verify that
the remote head is the reviewed revision, and fill the PR's review section.

## The Whitefoot boundary

- Snowghost builds with exactly the pinned `whitefoot/` revision, and moving
  the pin is a deliberate change under rule 4.
- A change Snowghost needs in Whitefoot is made in Whitefoot, under
  Whitefoot's own AGENTS.md, as a branch and PR in its repository, never as
  an edit to the submodule's files. While that PR is open, a Snowghost work
  branch may pin its head.
- When a missing Whitefoot feature would bend Snowghost's implementation or
  architecture, add the feature to Whitefoot instead of working around it.
  State the gap as its minimal semantic example, apart from the renderer code
  that exposed it, and record it under *Whitefoot requirements* in
  `docs/todo.md` until Whitefoot resolves it. A problem that belongs to the
  renderer alone is fixed in Snowghost, not by generalizing the language.

## Code and tests

- Snowghost's implementation rules are its design decisions in `design/`;
  read the nodes a change touches and their ancestors before changing code.
- Correctness is judged by an oracle independent of Snowghost: the relevant
  test suite, a format's conformance files, a specification's example or a
  reference renderer's output, never Snowghost's own earlier output.
- No site, page, test or benchmark selects a special path in the renderer.
- A performance comparison names its workload, machine, engine versions and
  settings, and measures every engine under the same conditions.
- Never delete, disable, narrow or unwire a test or check merely to make
  `make check` green. A deliberately retired test leaves an honest technical
  explanation in the same change.

## Repository structure and hygiene

The repository root and every established directory are a curated, closed
set. Follow this by judgment and keep moving.

- Do not add a repository-root entry without owner approval. Put new material
  in the existing directory that owns its kind; if none fits, ask.
- Every new file, directory, script or document earns its place before it is
  created: name what it serves, its home and the condition under which it is
  removed.
- No bulk dumps. A script ships wired to a caller; a document ships into an
  existing home and is kept current or deleted.
- Prefer native tooling; a new script must justify why the native path cannot
  do the job.
- Supersede in place: when new material replaces old, update, merge or delete
  the old in the same change.
- Repository artifacts, identifiers, comments, diagnostics, fixtures, test
  names and file names use English.
- Each document keeps its role: `README.md` introduces and navigates, this
  file holds the goal, authority, process and rules, `design/` the decisions
  and their log, `docs/review-checklist.md` the review items, `docs/todo.md`
  open defects and Whitefoot requirements until resolved,
  `research/investigations/` questions, experiments and results, and the PR
  description the current change. None narrates editing history.
- A claim cites the evidence [Authority and reading](#authority-and-reading)
  names; Whitefoot's language is cited from the pinned revision, never from
  Snowghost's code. Research and PRs may cite a decision as rationale, not as
  proof of an empirical claim.

## Communication

Describe renderer and language work with precise, neutral technical wording:
name the concrete rule, failure and expected behavior, and report material
risks accurately.

## Data safety

Preserve unrelated user changes in a dirty worktree. Never discard, overwrite
or rewrite work outside the requested change boundary.
