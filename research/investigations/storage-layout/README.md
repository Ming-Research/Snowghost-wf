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
The two proposals, as written against that commit, are in
[proposals/alpha](proposals/alpha/design.md) and
[proposals/beta](proposals/beta/design.md); each holds its brief, design,
friction log, today's-Whitefoot assessment and W1-W8 mocks.

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
The entry is qualified using the observed guarded/hoisted comparison below;
its production experiment remains unchanged.

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

## Repaired controls (CI 37562645431)

Revision `940889c631021220516e0d9e958a79c35f5edfce`: renaming `checked` alone
lets both original W3 algorithms compile and pass their supplied output checks
in both modes. Both consumers in each program are certified. Beta W1 likewise
compiles/runs after snapshotting `left.total_count` before its comparisons and
exact subtractions. None of these repairs is applied to the original probes.
C1's output-check harness needed its directory-length guard after the two writing
calls, whose broad effect rows invalidate the previous length fact.

All four original fences were compared byte-for-byte with the supplied inputs.
The 81 extracted W1 dependency records were independently compared and hashed
against their recorded Snowghost commit. Only the module-only `public` prefix
on LayoutError is omitted in the standalone source bundles. Their larger file
sizes are the cost of retaining the genuine AVL/library dependencies.

The CI driver checks a nonempty explicit inventory, exact selected loop verdicts,
expected rule plus diagnostic detail, and runtime exit/stdout/stderr. Its static
self-check deliberately substitutes a missing input/ledger, a denied loop, a
wrong rule, a timeout, an accepted negative, and wrong runtime output. All must
be detected; no Whitefoot compilation is part of that self-check.

## Settled claims

All fifteen probes have known outcomes in both sequential and `--par` builds in
[CI 37563028392](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37563028392),
revision `0e7c36441860219ceae95bc29aa2548d0ed81f83`. Nine programs compile and pass
literal result checks; six are expected source rejections. The
[retained transcript](runs/37563028392.txt) carries the exact diagnostic and
selected ledger lines, compiler/run statuses, and generated growth functions.
These results concern this Linux x86-64 release and these programs, not throughput
or a promise that every admitted loop actually overlaps at this small runtime size.

| Claim | Verdict | Evidence and qualification |
| --- | --- | --- |
| C1 | Partly | [Native pages](probes/c1-native-pages.wf) grow their directory from capacity 1 to 16 with fixed-capacity four-slot pages. The emitted grow instance copies only `len * sizeof(ptr)` bytes between pointer directories, then frees the old directory; it never dereferences a payload page. Twelve fields receive the expected changes and every cold field remains 99. The flat slot loop at line 35 is denied; `one_page` at line 49 and `by_page` at line 58 are permitted and split. |
| C2 | Partly | [Fixed stride with in-loop length read](probes/c2-fixed-stride.wf), line 13, is denied. [The otherwise identical hoisted-length version](probes/c2-fixed-stride-hoisted.wf), line 14, is permitted. [The unchanged cited runtime-stride test](probes/c2-runtime-stride-reference.wf), line 19, is permitted. All three run correctly. [Removing the bounds proof](probes/c2-missing-bound-negative.wf) rejects with REF-4, which is separate from parallel eligibility. |
| C3 | Partly | [Alpha W1](probes/c3-alpha-w1.wf) compiles/runs in its extracted original context. [Beta W1](probes/c3-beta-w1.wf) rejects with OP-2 at line 31. [Alpha W3](probes/c3-alpha-w3.wf) and [beta W3](probes/c3-beta-w3.wf) reject with FORM-3 because `checked` is reserved. The [alpha rename-only control](probes/c3-alpha-w3-renamed.wf) permits both consumers at lines 28/46; the [beta rename-only control](probes/c3-beta-w3-renamed.wf) permits both at 44/64. Both producers establish the fact once per two-pass call; neither consumer re-derives it. The [beta W1 scalar-snapshot control](probes/c3-beta-w1-snapshot.wf) also compiles/runs. W1 has dependent AVL walks, not scatter loops. |
| C4 | Holds (expected rejection) | [Field inverse](probes/c4-field-inverse-negative.wf), line 7, rejects with `error[RANGE-1]: InvalidRangeClause`, `reason: a range term selects below an element`. |
| C5 | Holds | [The callback helper](probes/c5-callback-pages.wf) compiles and changes its selected field from 41 to 42, also checking an absent page. [The changing callback](probes/c5-changing-callback-negative.wf), line 9, rejects with `error[FN-6]: PolymorphicRecursion`, `cycle: with_slot -> reenter -> with_slot`. |

### What the results contradict or qualify

- Alpha and beta's original `today.md` W3 validity assessments are false at the
  supplied pin; so is beta's W1 assessment. The rename/snapshot controls establish
  the intended behavior without concealing those original failures. Alpha's W1
  assessment holds in its explicitly stated module context.
- Alpha W7's `sixteen_per_row` reads the output length in its loop like the denied
  C2 probe. Its claimed eligibility does not follow for that spelling in this
  compiler. Both designs correctly identify the available stride rule and the
  cited upstream positive case; neither supports dismissing the TODO's current
  denial without the length-read qualification. The TODO now records this exact
  distinction; its original `record_all` experiment is left unchanged.
- Beta's native-page nonrelocation and direct-access alternative is confirmed.
  Alpha's proposed S1 cannot be justified by nonrelocation and constant-depth
  scalar access alone. This does not implement S1's cross-page range ABI or page
  adoption, or beta's proposed sparse-cell and encapsulated proof interfaces.
- Both agents correctly describe the field-inverse restriction and availability
  of ordinary FN-5 callbacks. FN-6 limits their generalization: the finite callback
  re-entry tested here is still refused. No result establishes that callbacks
  remove every production descent duplication or that paging is faster.

### Disposition and reproduction

The maintained P10 TODO is qualified, not closed: the in-loop length-read denial
is reproducible. The flat quotient/remainder page loop remains a documented proof
limit, with a certified page-wise alternative. Rejected input programs remain
untouched alongside separately named positive repairs. No production renderer
change or new storage design is adopted. No Whitefoot issue was filed remotely;
no pin or submodule revision moved.

`make compiler` and then `python3 -B research/investigations/storage-layout/run.py`
are invoked by the temporary workflow on this branch's pushes. The adjacent
`--self-check` invocation compiles nothing and exercises the driver's failure
recognition. The final expectation inventory additionally asserts all three
C1 loop verdicts; it was checked against the retained thirty compiler outcomes.

`w1-provenance.json` identifies every original dependency beside the probes' MIT
notice. W1's supplied code is unchanged at the front of its file, followed by
an independent literal-result entry point and original dependency definitions.
The known rejection expectations document experimentally refuted source claims;
no test requirement was weakened to call a rejected program valid.
