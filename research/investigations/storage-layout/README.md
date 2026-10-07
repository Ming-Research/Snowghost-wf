# Compiler checks for the storage proposals

## Question and prior rejection criteria

Compare the alpha and beta source-reading claims against the released compiler
`wf-f949e676acfa`, manifest commit
`f949e676acfa811f96b21afd07f02c06dcd14b51`. This is an acceptance experiment,
not a performance comparison or an adopted storage design. Base: Snowghost
`1fdb4050806ba08ca1ecd09c1e23b7cb77729ce9` (`origin/main` at branch creation).
The original design exercises used Snowghost
`49c138aa666c3c8e474267fe4d24ae1ae92c2419`; both W1 excerpts require that layout
module, absent from this base. Test their exact source with extracted original
dependencies and an entry point; do not substitute fake library implementations.

- C1: grow an outer directory of owned fixed-capacity pages, then read and write
  selected fields. Inspect emitted growth code for payload movement. Compare a
  single quotient/remainder slot loop with a page loop and its offset loop.
  A denied target loop refutes a blanket parallel-certification claim; preserved
  output alone does not prove that no payload bytes moved.
- C2: fixed stride 16 passed to a writing helper, plus the cited runtime-stride
  conformance case. A denied target loop refutes the P10 correction.
- C3: compile the original alpha/beta W3 bundles and W1 fragments in context.
  Both scatter consumers must be certified, their producer checked once, and
  the supplied independent literal expectations satisfied. A source rejection
  refutes validity of that supplied program; any repair is a separate probe.
- C4: require a field-backed inverse and expect RANGE-1 at that field access.
  An unrelated earlier rejection does not settle the claim.
- C5: instantiate a callback descent helper over native pages. An acyclic helper
  must compile and update its chosen field; a callback cycle changing the function
  argument must reject with FN-6, not an earlier syntax or ownership error.

All compilation and execution run on GitHub-hosted CI. The initial fixed-stride
probe is the smallest timed sample before scaling to the remaining probes.
The temporary workflow is limited to `research/storage-mocks`, retained while
this research branch is active and removed before any readiness proposal.
No renderer code, approved decision, pin, or submodule is changed.

## Inputs and authority

The exercise inputs are `inputs/brief.md` and each agent's `design.md`, `today.md`,
`friction.md`, and eight workload mocks supplied with the task. Whitefoot's
`spec/kernel-spec.md` and named conformance cases were read with `gh api` at
exactly the manifest commit above. Relevant rules: OP-10, REF-1 through REF-4,
FN-5/FN-6, RANGE-1 through RANGE-5, PAR-2, and STOR-7/STOR-8.

Snowghost's maintained TODO at this base still describes stride-window denial.
The investigation records its disposition after observing the compiler.

## Initial sample (CI 37562135575)

Revision `608010ac6cebc9401350a19e876e8fe4aadc51be`: fixed-stride compiled in
4.37 seconds sequential and 2.46 seconds with `--par`; both executions passed
every literal check. This measures setup-scale only, not speed or parallelism.
The outer loop was **denied**, despite the inner fill loop being permitted.
Next compare the exact upstream runtime-stride case and fixed-stride variants
with the length hoisted and the guard omitted; do not conflate a green exit
with a permitted loop. At this observed scale, run each remaining small probe
once per compiler mode with a two-minute per-command bound, reporting any
timeout as unknown rather than as a rejection.

## First complete batch (CI 37562468051)

Revision `fba0c4f0cfef71764952932ec6abd4c7025580f5` established:

- C2's original borrowed-length guard denies the outer loop; hoisting the same
  length read before the loop permits it. The unchanged cited runtime-stride
  conformance case also permits its outer loop. Omitting the bounds guard without
  replacing the proof rejects under REF-4; retain that as a separate negative.
- Alpha W1 compiles/runs with its original dependencies. Beta W1 rejects at
  `remaining - left.total_count` under OP-2. Test a separate variant that snapshots
  that field before comparing/subtracting it, preserving exact arithmetic.
- Both supplied W3 programs reject under FORM-3 because `checked` is reserved.
  Keep those originals unchanged as negative evidence; separately rename that
  identifier to `verified` to test the actual inverse-producer claim.
- C4 rejects under RANGE-1 at `.back`, the intended reason. C5's ordinary callback
  compiles/runs; its changing-function callback cycle rejects under FN-6.
- C1's first harness rejected a conditional move under LIV-1. Move page creation
  inside the guarded append branch, with an explicit error on insufficient room;
  this is a harness repair and says nothing about the claimed storage behavior.

The runner now expects the observed rejections of the **unmodified** source
artifacts. This is a recorded falsification of their validity claim, not a
changed language expectation. Each repair is separately named and compiled.
