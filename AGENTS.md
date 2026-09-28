# Snowghost — agent instructions

Snowghost is a cross-platform renderer for user interfaces built with web
technology. Its renderer implements a chosen subset of the web platform in
Whitefoot, with a pipeline meant to be parallel and incremental from end to
end, and a shell written in Rust hosts it on each operating system (the
`processes` decision in `design/`). Whitefoot, the language and its compiler,
is pinned as the `whitefoot/` submodule.

## Project goal

Reach, as early as possible, renderings and measurements that show whether an
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

## Authority and reading

`design/` holds the decisions Snowghost is built on, each with its reason and
refused alternatives. Work is not planned in a document up front: a selected
direction gets `research/investigations/<name>/` for its design, measurements
and rejected alternatives, and its surviving decision goes to the design
tree. Read only the material relevant to the task, and do not turn research
into an implied implementation requirement.

The pinned `whitefoot/` revision defines the language: its specification
`whitefoot/spec/kernel-spec.md` and `whitefoot/docs/patterns.md` are the
references for writing Whitefoot. Snowghost never edits files under
`whitefoot/`; see [The Whitefoot boundary](#the-whitefoot-boundary).

A finished task is not evidence: a claim cites a design-tree decision, an
investigation, a measurement with its workload, environment and comparison,
or an oracle independent of Snowghost such as a test suite, a format's
conformance files or a reference renderer's output.

## How work proceeds

Follow the four occasions below. A *material choice* changes rendered
behavior, a safety or trust condition, a shared interface or representation,
a significant performance commitment or a standing project rule. Restoring
decided behavior or editing prose without changing its meaning is routine;
task size and file count do not decide which a change is.

1. **Start or resume:** read the affected design-tree nodes and their
   ancestors. On resumption, verify the actual worktree and PR state.
2. **Choose:** state why a material choice fits its requirements and evidence;
   record a discriminating experiment's criterion before using it to choose,
   and load the `investigation` skill when a choice needs a new measurement,
   benchmark or trial.
3. **Update:** when a conclusion or its grounds change, update current guidance
   and material dependents in the same work. A design revision is an
   owner-ruled tree change or a pending amendment: load the `design-tree`
   skill whenever a task makes, proposes or applies a design decision or edits
   `design/`.
4. **Finish:** load the `completion-review` skill before marking a PR ready or
   reporting completion (checks, one independent review, finding routing,
   publication), and the `owner-handoff` skill whenever you stop for the
   owner.

Routine fixes under unchanged design need no decision record. Record reasons
when choices settle, not by reconstructing them at task completion.

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

Use a PR as the owner's review surface from the start, as a Draft until the
design-tree workflow makes it ready. Push coherent progress to the same
branch and keep its description and actual validation results current. A
series of dependent PRs is stacked, each on the branch of the one before it.
Updating a work-branch PR never authorizes a merge into `main`.

Recurring procedures are skills: `design-tree` (body in `design/skill/`),
and `investigation`, `completion-review` and `owner-handoff` (bodies in
`docs/skills/`). `.claude/skills/` and `.agents/skills/` hold only links to
them.

## Agent roles

- The owner and the primary agent own the architecture: the design tree, the
  module graph and the Whitefoot module interfaces (`.wfm`), with their
  contracts and effect rows.
- Implementer agents write module bodies (`.wf`) against those interfaces, in
  parallel. An implementer that finds an interface insufficient reports the
  gap to the primary agent with a minimal example instead of editing the
  interface.
- A separate reviewer agent that did not implement a change reviews it under
  the completion-review skill.
- The primary agent dispatches and supervises implementer and reviewer agents
  and chooses the model for each kind of task from measured agent writer
  trials (investigation skill).

## Branch and main boundary

These are the complete approval and merge rules:

1. Work-branch changes need no approval, except that new repository-root
   entries require owner approval, changes to the live design tree require
   the owner's ruling under the design-tree skill, and a review finding whose
   resolution would change a design decision or amendment or the agreed scope
   requires the owner's direction.
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

`make check` is the gate. It needs git, Rust stable at least at the
`rust-version` in `whitefoot/compiler/Cargo.toml`, Python 3, and a clone
with its submodule: `git clone --recurse-submodules`, or
`git submodule update --init` in an existing clone. It builds the pinned
compiler with Whitefoot's own build target, leaving it at
`whitefoot/compiler/target/gate/whitefootc`, and runs the design lint; CI runs
the same targets on every push.

## The Whitefoot boundary

- Snowghost builds with exactly the pinned `whitefoot/` revision, and moving
  the pin is a deliberate change under rule 4.
- A change Snowghost needs in Whitefoot is made in Whitefoot, under
  Whitefoot's own AGENTS.md, as a branch and PR in its repository, never as
  an edit to the submodule's files. While that PR is open, a Snowghost work
  branch may pin its head.
- State a Whitefoot gap as its minimal semantic example, apart from the
  renderer code that exposed it, and record it under *Whitefoot requirements*
  in `docs/todo.md` until Whitefoot resolves it. A renderer problem is fixed
  in Snowghost, not by generalizing the language.

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

## Communication

Describe renderer and language work with precise, neutral technical wording:
name the concrete rule, failure and expected behavior, and report material
risks accurately.

## Data safety

Preserve unrelated user changes in a dirty worktree. Never discard, overwrite
or rewrite work outside the requested change boundary.
