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
