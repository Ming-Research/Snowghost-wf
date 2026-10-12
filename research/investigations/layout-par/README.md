# Layout parallelism instruction inventory

The question is which source functions and loops own the sequential layout
pass's instruction work, and which of that work the pinned Whitefoot compiler
reports as permitted to run independently. For each costly refused loop, the
source audit distinguishes an algorithm's true dependency, a Snowghost writing
form that can expose independent work, and a Whitefoot proof gap requiring an
upstream semantic witness. The comparison joins a fresh
`--par --par-ledger` build with exclusive instruction costs from the same
source's sequential build, on the three E1 benchmark pages. It inventories
the existing implementation; it selects no new renderer algorithm or interface.

The proposal fails if the isolated profiles do not conserve exclusive `Ir`
against each dump's `totals:` footer, if a zero-repetition control collects
instructions, if the layout entry does not account for the complete collected
region, or if generated names and the ledger cannot be mapped to source without
guessing. Unmapped symbols and unsupported ledger evidence must remain visible.
If cost concentrates in admitted or unobserved functions rather than refused
ones, the investigation shifts toward actualization and inlining rather than
loop rewrites. A costly refusal with a true dependency motivates an algorithm
comparison; provably independent source forms motivate a downstream rewrite;
an unsupported natural form motivates a Whitefoot witness. These are provisional
investigation branches, not proposed renderer decisions.
Compiler permission is eligibility, not proof of actual parallel execution,
grain, critical-path improvement or speedup. `Ir` counts simulated instructions,
not cycles or elapsed time; inclusive costs overlap and are never added into
the exclusive work total.

## Inputs and scope

The page names and driver protocol follow the E1 concurrency and layout
investigations. ECMA262 and HTML5 use the revision-pinned URLs and hashes in
[`concurrency/run.sh`](../concurrency/run.sh). Apollo11 uses the separately
hashed, permanent [original-page fixture](../../../tests/layout/fixtures/apollo11/README.md),
extracted before the other pages are fetched. That fixture's hashes differ from
the later Apollo capture pinned by `concurrency/run.sh`, so its fetch mode is
not invoked for Apollo. Every download must match its authoritative hash.

Historical E1 byte identity is unverified: its supplementary Apollo capture
and recorded fonts are not supplied by this harness. The current run uses
the repository fixture and `make oracle-fonts` on Ubuntu 24.04, preserving the
font loader's established files and fallback order. The artifact records
each HTML, loaded sheet, UA sheet and font hash; it makes no claim that these
bytes reproduce a historical E1 measurement. The inventory's scope is the
actual recorded inputs, compiler and source revision.

Only `pkg::layout::lay_out` and its descendants are collected. Page loading,
parsing, style computation, font loading, box construction, font selection,
text preparation, output counting and dumping are outside that region. The
production `layout_oracle layout 1 ...` mode prepares these inputs and calls
the layout entry once; `layout 0 ...` prepares startup without entering it.
No renderer source, compiler flags that affect inlining, Whitefoot pin or
submodule is changed to expose a profile boundary. A missing exported entry
blocks profiling and requires investigation.

## Procedure

The temporary [`par-inventory.yml`](../../../.github/workflows/par-inventory.yml)
workflow runs on GitHub-hosted Ubuntu 24.04. The [`profile.py`](profile.py)
harness has independent `ledger` and `profile` job modes and refuses local
execution except the handmade `--dry-run` controls. The jobs start in parallel:
neither build or budget depends on the other. They create independent empty
caches and record the exact commands, exits, timeout budgets, elapsed durations, compiler
release manifest, compiler and driver hashes, source revision, submodules,
tool versions in their separate output roots. The ledger job writes
`build/layout-par-ledger/`; the profiling job writes `build/layout-par/` and
also records input/font hashes and preserves the actual input and font bytes.
Each job always uploads its own raw artifact, including partial failures and
its driver when built. Compiler cache directories stay outside the archive.

The historical 49 of 340 admitted count in board item `sg-bl-02-82`
is background, not the current inventory or a performance result. This run
must regenerate its counts from the complete fresh ledger and associate
instruction costs before deciding which refusal matters.

The pinned Whitefoot revision's [P13 implementation-permission pattern](https://github.com/Ming-Research/Whitefoot/blob/78223721f77db615c950b6df1bcc690629f9fe4b/docs/patterns.md#p13-keep-parallelism-a-proved-implementation-permission)
and [kernel specification's PAR-2 rule](https://github.com/Ming-Research/Whitefoot/blob/78223721f77db615c950b6df1bcc690629f9fe4b/spec/kernel-spec.md)
define the interpretation of permission. Its [permission-ledger implementation](https://github.com/Ming-Research/Whitefoot/blob/78223721f77db615c950b6df1bcc690629f9fe4b/compiler/src/semantic/permission_ledger.rs)
defines emitted verdicts and generic-site deduplication; mixed verdicts at a
source site remain visible. Its [compiler command implementation](https://github.com/Ming-Research/Whitefoot/blob/78223721f77db615c950b6df1bcc690629f9fe4b/compiler/src/bin/whitefootc.rs)
defines graph-build ledger output on standard output and the ledger cache
bypass. The run's release manifest records the full compiler commit rather
than inferring it from a shortened release tag.

The source inventory lexes identifiers and braces, excluding strings and
comments, and finds functions with their nested loops under `renderer/layout`.
The nearest owning `module.wfm` supplies the qualified source module name;
the lexical function body supplies each loop's owner. Generated symbol variants
are normalized to those source names. Ledger sites join by source path and
line because the pinned format supplies no function name. Missing counted-loop
verdicts, ledger sites absent from source, or multiple source loops on one
ledger line block a complete inventory. Ordinary `loop` forms remain
explicitly uncovered by the counted-loop rule, never labeled compiler refused.
The compiler checks every nongeneric function in the entry module's dependency
composition, even when the selected entry never calls it. A generic template
needs a concrete instantiation to appear in the permission ledger, so an unused
generic counted loop can block coverage ([pinned signature discovery](https://github.com/Ming-Research/Whitefoot/blob/78223721f77db615c950b6df1bcc690629f9fe4b/compiler/src/semantic/check/generics.rs#L324-L367)).

The sequential build command, from `renderer/`, is:

```sh
"$WFC" --cache "$GITHUB_WORKSPACE/build/layout-par-cache-seq" \
  --fragments function --graph modules.wfg --entry layout_oracle \
  -o "$GITHUB_WORKSPACE/build/layout-par/layout-seq"
```

The ledger job's independently cached build adds `--par --par-ledger`, writes
`build/layout-par-ledger/layout-par` and retains complete standard output as
`build/layout-par-ledger/par-ledger.log`, with diagnostics separately. It runs
the complete source-to-ledger coverage check before publishing its successful
artifact. The profiling job can proceed without waiting for that compilation.

Before any profile, `nm --defined-only` must find exactly the exported text
symbol `wf_layout.lay_out` in the sequential binary. Symbol presence alone
does not show that the driver still calls it after optimization, so
`objdump -d --no-show-raw-insn` must also show a direct x86 `call` or `callq`
instruction to `<wf_layout.lay_out>` at the same address. Function headers,
comments, data, indirect calls, target offsets, other callees and tail jumps
cannot satisfy this check. Calls from the entry itself or its body variants
are excluded. The artifact retains full disassembly and structured callsite
records with caller, disassembly line, instruction and target addresses and
the raw instruction. If no such callsite exists, profiling stops before the
zero control; no source or compiler change is made to invent one. Static
callsite presence still does not prove dynamic execution; the positive pilot
and its exact root accounting remain required.

The pilot profiles ECMA262 once, with the same options later used for HTML5
and Apollo11:

```sh
WF_WORKERS=1 valgrind --tool=callgrind --collect-atstart=no \
  --toggle-collect=wf_layout.lay_out \
  --callgrind-out-file=build/layout-par/ecma262.callgrind \
  build/layout-par/layout-seq layout 1 \
  build/research/concurrency/ecma262.html renderer/style/ua.css \
  assets/css/ecmarkup.css=build/research/concurrency/ecma262-ecmarkup.css \
  assets/css/print.css=build/research/concurrency/ecma262-print.css
```

Run from the repository root and use relative page and stylesheet paths:
the driver's filesystem capability rejects absolute inputs and symbolic links.
The same command with repetitions zero creates `zero.callgrind`; its exclusive
total must be zero. The pilot must be positive, contain the exact entry and
give that entry's normalized wrapper/body family an inclusive cost equal to
the reconciled exclusive total, excluding internal family edges.
Collection uses only this entry toggle; there are no before/after dumps and
no call-count measurements or conclusions.

The ledger job starts its own 52-minute deadline in its first step and has a
55-minute job cap. Its harness budget is the lesser of 42 minutes and the time
left before that deadline, with the ledger build alone capped at 40 minutes;
setup is capped at 9 minutes. Its recorded command allowance and duration show
any clipping by its own deadline. Neither the sequential build nor a profile
consumes this ledger budget.

The profiling job starts its own 40-minute deadline and retains a 45-minute
job cap. Its harness budget is the lesser of 25 minutes and the time left
before its deadline, including input preparation, metadata, the sequential
build, boundary checks and four profiler processes. Its sequential build is
capped at 10 minutes, the zero control at 4 minutes and the pilot at 5 minutes.
The pilot's measured process duration is reused to choose remaining profile caps:
four times its duration, scaled upward by HTML plus loaded-sheet byte size,
with a two-minute minimum. This conservative scheduling rule is not a
performance model. If those caps do not fit the remaining budget, the job
stops with retained evidence and a request for a separately bounded batch.
Timeout, incomplete dumps and missing controls never count as completed pages.

A third job needs both jobs to succeed and downloads their separate artifacts.
Before joining, it requires equal actual source and workflow revisions, run
identity, Whitefoot pin, compiler executable hash, release manifest, renderer
source hashes and methodology hashes. It verifies the downloaded drivers
against their recorded hashes. It then summarizes the profiles against the
downloaded ledger and uploads a summary artifact containing both evidence
directories. A failed build or mismatched artifact cannot produce a completed
inventory.

The accounting CLI is:

```sh
python3 -I research/investigations/layout-par/inventory.py --dry-run
python3 -I research/investigations/layout-par/profile.py --dry-run
python3 -I research/investigations/layout-par/profile.py ledger
python3 -I research/investigations/layout-par/profile.py profile
python3 -I research/investigations/layout-par/inventory.py inventory \
  --root . --ledger build/layout-par-ledger/par-ledger.log --out build/layout-par-ledger
python3 -I research/investigations/layout-par/inventory.py summarize \
  --root . --ledger build/layout-par-ledger/par-ledger.log --out build/layout-par
```

The dry runs supply handmade parser and provenance rejection controls, without
building or running the renderer. The two job modes run only in CI. The ledger
mode invokes the `inventory` command after its build to validate counted-loop
coverage. The dependent summary job's `summarize` command reads all three page
dumps and raw protocols plus the zero control, then writes the source and ledger
inventory. Its Callgrind parser resolves compressed function identifiers and
uses the `Ir` event column. Regular cost rows are exclusive; the cost row
following a `calls=` marker is an inclusive edge and is excluded from the
exclusive reconciliation. The marker is used only to distinguish row kinds;
its numeric count is neither read as evidence nor reported. Reconciliation
uses the `totals:` footer; `summary:` is retained only as metadata.
These meanings follow the [Callgrind format specification](https://valgrind.org/docs/manual/cl-format.html)
and [Callgrind manual](https://valgrind.org/docs/manual/cl-manual.html).

## Preparation checks

Initial preparation, before the budget repair: the allowed local
`python3 -I research/investigations/layout-par/inventory.py --dry-run`
used handmade source, ledger and profile fixtures; it ran no compiler, build,
renderer or test suite. The final repeat after preparation edits passed with
exit 0 and rejected 15 corrupt artifacts.

A fresh `gpt-6.1-sol` agent at high effort reviewed all four new files read-only
against base `1e0228e`, the project checklist and applicable pipeline/layout
decisions. It found two defects: valid Callgrind rows with omitted trailing
event costs were rejected, and an invented permission condition `12` was
accepted. Both are fixed and covered by handmade fixtures, and the reviewer
reported no unresolved static findings within scope. CI gates, actual compiler
ledger coverage and real profile accounting remain unverified. This initial
review does not cover the later job split or direct-call validation.

After the budget repair, the primary agent ran the allowed local
`python3 -I research/investigations/layout-par/profile.py --dry-run` on handmade
disassembly and provenance samples. It exited 0 and rejected 12 corrupt
callsite artifacts and 18 corrupt joins, without running a compiler, build,
renderer or test suite.

A separate fresh `gpt-6.1-sol` agent at high effort reviewed the three changed
files read-only against base `af9eb26`, the project checklist and applicable
pipeline/layout decisions, and reported no static findings within scope.
Runtime CI, actual direct-call presence, compiler ledger coverage and real
profile accounting remain unverified.

## Results

On 2026-10-11 the owner reported that [the first inventory CI run](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38192419000)
completed the sequential build in about 6.4 minutes and timed out the ledger
build at its 600-second cap. The run logs could not be retrieved in this
session, so these are owner-reported observations, not independently verified
measurements. They motivate separate build jobs and a 40-minute ledger build
cap; they establish no renderer performance result or instruction inventory.

Pending CI: no instruction costs, regenerated ledger counts or dependency
classifications are claimed yet. Archive the complete Actions
artifact, the run link, checked-out revision, reconciled page totals, unmapped
functions and review scope here when they exist. Retain failed pilots and
their process records so later runs can justify a changed batch. The
`profile-status.json` file describes collection only; `ledger-status.json`
describes compilation and coverage. Matched `join-provenance.json`, successful
inventory generation and the dependent job's result establish whether
accounting completed.

The workflow and `profile.py` are temporary experiment machinery. Remove them
after their raw evidence is archived and before this investigation is marked
ready; keep the accounting tool only if it has an established caller or
documented analysis use. Any language or compiler proof gap exposed by the
inventory goes to Whitefoot with a semantic witness, rather than changing
the renderer to hide it.
