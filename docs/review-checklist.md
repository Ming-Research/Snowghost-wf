# Task completion review

The items an independent reviewer checks when a task completes.
[AGENTS.md](../AGENTS.md#review) says when the review runs, who runs it, how
findings are handled and where the report goes; merge conditions remain in
its [branch and main boundary](../AGENTS.md#branch-and-main-boundary).

## How to review

Read the task's requested outcome and constraints, the complete diff from the
base to the reviewed revision (including uncommitted and new files), and the
actual validation results. Read changed sections in context and the directly
affected definitions, interfaces, callers or cases. Do not load the whole
repository or require a separate review packet.

Judge the artifacts against the task and their current owners, not just the
author's summary. Mechanical checks cover their encoded properties; this
review checks meaning, placement and omitted dependent updates. It does not
reconstruct an unrecorded reason or certify a design argument: mark such a
question `unverified` for the implementing agent.

Check every group whose trigger applies. Mark items
`pass`, `finding`, `unverified` or `not applicable`; missing evidence is not a
pass. A finding names its item ID, file and line, the offending text or
missing evidence, and a short reason; quote both sides of a contradiction.

## A. Scope and repository layout — every change

Source: [repository hygiene](../AGENTS.md#repository-structure-and-hygiene).

- [ ] **A1 — Task fit.** Each changed artifact serves the requested outcome or
  a necessary dependency. The completion claim does not silently drop a
  requirement or leave an advertised fix as a stub or unconnected code.
- [ ] **A2 — New paths.** Each added file or directory has a consumer, an
  existing home and a removal condition. No unapproved root entry, parallel
  document, copied implementation, per-task report or unused helper.
- [ ] **A3 — Connections.** Added scripts and tests have a real caller or
  collection path; documented commands name existing targets. Moves and
  deletions update affected links and wiring.
- [ ] **A4 — Artifact hygiene.** No scratch output, personal path, credential
  or machine-local setup in the diff. Artifacts use English. No edit to a
  file under `whitefoot/`; the only permitted change there is the pin.

## D. Documentation — changed Markdown, comments or examples

- [ ] **D1 — Purpose.** Each changed passage serves its document's reader
  under the [document roles](../AGENTS.md#document-roles); no editorial
  history or process instructions inside substantive documents.
- [ ] **D2 — References.** Changed references resolve to the intended file,
  heading or symbol, obey the
  [citation boundaries](../AGENTS.md#citation-boundaries), and support their
  claim.
- [ ] **D3 — Current meaning.** Changed claims agree with their owning source
  and affected guidance. A goal, a proposal, a decision, an implemented
  capability and a dated measurement are kept distinct.
- [ ] **D4 — Usability.** Instructions name real commands and prerequisites;
  changed runnable examples were run.

## C. Code and cases — changes to Whitefoot sources or tests

Source: [code and tests](../AGENTS.md#code-and-tests).

- [ ] **C1 — Observable case.** A fix has a case that distinguishes the faulty
  behavior from the intended result; new behavior has coverage for its normal
  use and relevant boundaries.
- [ ] **C2 — Independent expectation.** Expected results come from an oracle
  independent of Snowghost, never from its current output. A regression case
  fails before the fix and passes after.
- [ ] **C3 — General path.** The change implements a general rule of the
  subset Snowghost claims. No site, page, test or benchmark selects a special
  path, and no fallback conceals an unsupported feature.
- [ ] **C4 — Interface fidelity.** Module bodies implement their `.wfm`
  interfaces as written. An interface, contract or effect row changed only
  with the architecture's approval, and none was weakened to let a body pass.
- [ ] **C5 — Architectural fit.** Apply the design skill's
  [G3](../design/skill/SKILL.md#design-checks) to structural choices, and
  check that the assessment happened when the choice was made.

## T. Checks and the pin — changes to tests, the Makefile, `.github/` or `whitefoot/`

- [ ] **T1 — Preserved checks.** Every removed, skipped, narrowed or weakened
  test or check has a technical reason consistent with the requested change.
- [ ] **T2 — Effective checks.** New cases actually run; new check machinery
  shows that a representative wrong result is detected.
- [ ] **T3 — Local and CI correspondence.** CI runs the same Makefile targets
  as local `make check`; changed selection adds no omission or extra check.
- [ ] **T4 — The pin.** A moved `whitefoot/` pin names the adopted Whitefoot
  revisions and why; a revision bound for `main` pins a commit on
  Whitefoot's `main`, and Snowghost's checks pass with it.

## R. Decisions — changed choices, premises or evidence

Source: [How work proceeds](../AGENTS.md#how-work-proceeds) and the
[design-tree skill](../design/skill/SKILL.md#what-is-a-decision). Applies to
changes under `design/` or `research/investigations/`, and to any task that
made a material choice elsewhere.

- [ ] **R1 — Stated ground.** A material choice has a retrievable explanation
  of its purpose, alternatives considered, selection reason and remaining
  uncertainty. Unresolved proposals have not become settled decisions through
  wording alone.
- [ ] **R2 — Discriminating evidence.** An experiment used to select a design
  states the comparison that could distinguish it, its conditions and its
  actual outcome; a criterion claimed as prior is inspectable.
- [ ] **R3 — Maintained tree.** Added, changed or retired decisions have
  corresponding design records under the design skill, and cited sources
  resolve and support their scope.

## M. Design review — every change

- [ ] **M1 — Design procedure.** Apply the design-tree skill
  (`design/skill/SKILL.md`) to the reviewed scope: its design checks G1–G3,
  correspondence checks DC1–DC4 and structural validation, and include the
  actual results.

## V. Validation and handoff — every change

- [ ] **V1 — Actual checks.** Applicable checks ran on the delivered content;
  commands, results and limitations are available. Focused success is not
  described as a complete gate.
- [ ] **V2 — Supported claims.** Counts, paths, revisions and quoted results
  were checked. A performance claim names workload, machine, engine versions
  and comparison; a causal claim has isolating evidence.
- [ ] **V3 — Delivery.** The PR describes the current result and remaining
  limitations. Its *Found along the way* section gives every defect or
  opportunity the work exposed a disposition: fixed, recorded in
  `docs/todo.md`, or declined with a reason. A PR marked ready has the
  owner's approval of every design-tree change it carries, recorded in
  `design/log.md`.
- [ ] **V4 — Existing PR updated.** The reviewed changes are pushed to the PR
  branch; its remote head is the delivered revision and its description
  reflects the current diff.
