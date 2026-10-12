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
harness has independent `ledger` and `profile --page PAGE` job modes and refuses
local execution except the handmade `--dry-run` controls. The ledger job and
three profiling matrix jobs start independently. Each page has its own build,
zero control, one-pass profile and budget; `fail-fast: false` lets every page
attempt its work even if another fails. They create independent empty
caches and record the exact commands, exits, timeout budgets, elapsed durations, compiler
release manifest, compiler and driver hashes, source revision, submodules,
tool versions in their separate output roots. The ledger job writes
`build/layout-par-ledger/`; each page writes `build/layout-par-pages/PAGE/` and
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

The sequential build command for a page job, from `renderer/`, is:

```sh
"$WFC" --cache "$GITHUB_WORKSPACE/build/layout-par-cache-seq" \
  --fragments function --graph modules.wfg --entry layout_oracle \
  -o "$GITHUB_WORKSPACE/build/layout-par-pages/$PAGE/layout-seq"
```

The ledger job's independently cached build adds `--par --par-ledger`, writes
`build/layout-par-ledger/layout-par` and retains complete standard output as
`build/layout-par-ledger/par-ledger.log`, with diagnostics separately. It runs
the complete source-to-ledger coverage check before publishing its successful
artifact. Every profiling page can proceed without waiting for that compilation.

Before any profile, `nm --defined-only` must find exactly the exported text
symbol `wf_layout.lay_out` in the sequential binary. Symbol presence alone
does not show that the driver still calls it after optimization, so
`objdump -d --no-show-raw-insn` must also show a direct x86 `call` or `callq`
instruction to `<wf_layout.lay_out>` at the same address. Function headers,
comments, data, indirect calls, target offsets, other callees and tail jumps
cannot satisfy this check. Calls from the entry itself or its body variants
are excluded. The artifact retains full disassembly and structured callsite
records with caller, disassembly line, instruction and target addresses and
the raw instruction. Numeric `.llvm.<digits>` segments are normalized in the
entry's `nm` name and the disassembly's caller, header and call target; raw
spellings remain in the evidence and collection uses the actual emitted entry
name. Nonnumeric LLVM spellings remain distinct. If no such callsite exists, profiling stops before the
zero control; no source or compiler change is made to invent one. Static
callsite presence still does not prove dynamic execution; the positive pilot
and its exact root accounting remain required.

Each page's pilot is its only single-pass profile and is retained directly.
For example, the ECMA262 job runs:

```sh
WF_WORKERS=1 valgrind --tool=callgrind --collect-atstart=no \
  --toggle-collect=wf_layout.lay_out \
  --callgrind-out-file=build/layout-par-pages/ecma262/ecma262.callgrind \
  build/layout-par-pages/ecma262/layout-seq layout 1 \
  build/research/concurrency/ecma262.html renderer/style/ua.css \
  assets/css/ecmarkup.css=build/research/concurrency/ecma262-ecmarkup.css \
  assets/css/print.css=build/research/concurrency/ecma262-print.css
```

Run from the repository root and use relative page and stylesheet paths:
the driver's filesystem capability rejects absolute inputs and symbolic links.
Each job first runs its own page with repetitions zero, producing
`PAGE-zero.callgrind` and `PAGE-zero.raw`; its exclusive total and raw context
and paragraph counts must be zero. The pilot must be positive, contain the exact entry and
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

Each profiling job starts its own 40-minute deadline and retains a 45-minute
job cap. Its harness budget is the lesser of 25 minutes and the time left
before its deadline, including input fetching and verification, provenance, one
sequential build, boundary checks, its own zero control and one single-pass
profile. Its sequential build is capped at 10 minutes, the zero control at
4 minutes and the single pass at 5 minutes. `scale-selection.json` records
that measured pass and the remaining budget; the pass is reused as the actual
result. There is no extrapolation to another page, repetition increase or
sum-of-remaining-page-caps gate. The recorded process durations justify only
administrative budgets, never renderer performance conclusions.
Timeout, incomplete dumps and missing controls never count as completed pages.

A summary job needs the ledger and all three matrix jobs to succeed. It
downloads each page artifact into its own directory without merging them.
Before joining, it requires equal actual source and workflow revisions, run
identity, Whitefoot pin, compiler executable hash, release manifest, renderer
source hashes and methodology hashes. Page identities must match their
artifact names, and all three pages must record identical input and font
hashes. It still verifies each downloaded whole file against that artifact's
recorded SHA-256; those integrity checks do not require hashes from different
page builds to match. Cross-page equivalence requires identical SHA-256 hashes
and sizes for all three `.text`, `.rodata` and `.data` sections, plus identical
normalized function names and sizes with duplicate entries preserved. The
normalization removes only numeric `.llvm.<digits>` segments at a segment
boundary, preserving every other spelling. Real name or size differences,
missing sections and changed section bytes stop the join; no page is skipped.

The summary job installs binutils explicitly and retains `objdump -h` section
headers, the complete `objdump -t` symbol table and extracted section bytes in
each page directory. Only explicit `F` function entries form the function
table; a code-section label or weak object is not a function. `objcopy
--dump-section` uses an explicit `/dev/null` output so it does not rewrite the
driver. Every dump must exist and match its section header's size, and the
whole-file hash is checked before and after extraction. These formats follow
the [GNU objdump documentation](https://sourceware.org/binutils/docs/binutils/objdump.html)
and [GNU objcopy documentation](https://sourceware.org/binutils/docs/binutils/objcopy.html).

`driver-identities.json` and `join-provenance.json` retain whole-file hashes,
section hashes and sizes, raw and normalized function records, the common
function table and observed LLVM suffix spellings. The summary reports
observed whole-file hash and suffix variation. Matching these selected sections
and tables does not establish complete ELF identity or prove that suffixes are
the only difference. Only after the integrity and equivalence
checks does it copy each page's `PAGE.callgrind`, `PAGE.raw`,
`PAGE-zero.callgrind` and `PAGE-zero.raw` into flat `build/layout-par/` for
accounting. The summary artifact retains those outputs, all three complete
page evidence directories and the complete ledger directory. A failed job,
missing control or mismatched artifact cannot produce a completed inventory.

The accounting CLI is:

```sh
python3 -I research/investigations/layout-par/inventory.py --dry-run
python3 -I research/investigations/layout-par/profile.py --dry-run
python3 -I research/investigations/layout-par/profile.py ledger
python3 -I research/investigations/layout-par/profile.py profile --page ecma262
python3 -I research/investigations/layout-par/inventory.py inventory \
  --root . --ledger build/layout-par-ledger/par-ledger.log --out build/layout-par-ledger
python3 -I research/investigations/layout-par/inventory.py summarize \
  --root . --ledger build/layout-par-ledger/par-ledger.log --out build/layout-par
```

The dry runs supply handmade parser and provenance rejection controls, without
building or running the renderer. The two job modes run only in CI. The ledger
mode invokes the `inventory` command after its build to validate counted-loop
coverage. Profile mode requires `--page` (ecma262, html5 or apollo11); ledger
mode accepts no page. The dependent summary job's `summarize` command reads
all three page dumps and raw protocols plus all three page-specific zero
controls, then writes the source and ledger
inventory. The shared numeric LLVM-segment normalizer is used by source,
Callgrind, ledger and disassembly symbol joins, with raw spellings retained in
the symbol audits. Its Callgrind parser resolves compressed function identifiers and
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

For the page-matrix repair, the primary agent reran both allowed local
handmade dry runs with Python `-I`. `profile.py --dry-run` exited 0 and
rejected 12 corrupt callsite artifacts, 24 corrupt joins and 5 corrupt driver
inventories. `inventory.py --dry-run` exited 0 and rejected 18 corrupt
artifacts, including missing and nonzero page-specific zero controls. Neither
command ran a compiler, build, renderer or test suite.

A separate fresh `gpt-6.1-sol` agent at high effort reviewed all four changed
files read-only against base `ecf972e`, the project checklist and applicable
pipeline/layout decisions, and reported no static findings within scope.
That review covered the original whole-file equality criterion, which the
driver-identity repair below supersedes. The new extraction and normalization
controls were checked by the primary agent's allowed local Python `-I -B`
handmade dry runs: `profile.py --dry-run` exited 0 and rejected 12 corrupt
callsite artifacts, 24 corrupt joins and 13 corrupt page-driver fixtures;
`inventory.py --dry-run` exited 0 and rejected 19 corrupt artifacts. Neither
command ran a compiler, build, renderer or binutils extraction.

A separate fresh `gpt-6.1-sol` agent at high effort reviewed all four changed
files read-only against base `30eb22b`, the project checklist and applicable
pipeline/layout decisions, and reported no static findings within scope.
Actual binutils extraction, the selected-section/normalized-function-table
join, observed raw suffix variation and the ranked CSV inventory remain
pending CI.

## Results

[Inventory run 38198149902](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38198149902)
at revision `fd5e248` (renderer as `research/m2-layout` 1e0228e, compiler
`wf-78223721f77d`) completed every job. Every Callgrind dump's exclusive rows
reconcile with its `totals:` footer, `lay_out`'s inclusive cost equals each
total, and the three zero-repetition controls collected 0 Ir. The layout pass
executed 2,891,988,739 Ir on ECMA262, 2,709,043,391 on HTML5 and 237,403,910 on
Apollo11. The ledger gave a verdict for all 601 counted loops in
`renderer/layout/`; 428 are refused. The three page drivers have identical
`.text`, `.rodata` and `.data` bytes and identical function tables once the
per-build `.llvm.<digits>` suffixes are removed; only those symbol names
differ. The artifact holds `loops.csv`, `functions.csv`, `symbol-map.csv`,
the ledger, the raw profiles and `summary.md`, whose per-page rankings the
classification below uses.

The workflow and `profile.py` are temporary experiment machinery. Remove them
after their raw evidence is archived and before this investigation is marked
ready; keep the accounting tool only if it has an established caller or
documented analysis use. Any language or compiler proof gap exposed by the
inventory goes to Whitefoot with a semantic witness, rather than changing
the renderer to hide it.

### Refused-loop classification

Source: [inventory run 38198149902](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38198149902)
at revision `fd5e248`, compiler release `wf-78223721f77d` (Whitefoot
`78223721f77d`, specification v0.121). Each refused counted loop of the
costliest functions was read in `renderer/layout` and judged against that
revision's PAR-2 and RANGE-5 text. Classes: **T** the algorithm needs the
order (the dependency is named); **S** the work is independent and a form
the pinned rules admit exists; **W** the work is independent, the natural
form is refused and no honest rewrite exists (witnesses W1 to W6 below);
**U** unsettled.

Costs are Callgrind `Ir` shares of the `lay_out` pass, ecma262 / html5 /
apollo11, per source function (`functions.csv`); the binary carries no line
information, so no cost is attributed to a single loop. Self shares add;
inclusive shares overlap and do not.

Context for every payoff below: the outer parallelism of layout is already
admitted. `lay_out_children` (flow.wf:485), `break_all` (flow.wf:508, every
paragraph of a context: 75.1 / 75.1 / 64.4% inclusive), the flex item loops
(flex.wf:1634, 1687, 1736, 1744) and the table part loop (table.wf:704) are
permitted. The 250–700% inclusive share of `lay_out_context` is that
admitted recursion, not its refused loop. The refused loops under
`break_paragraph` (`finish_lines`, `next_line`, `measure`, `break_lines`,
`framed_inside`, `add_box_rects`) run inside one iteration of `break_all`,
so rewriting them shortens the critical path of one paragraph, not the
total sequential work. The others run once per context, inside the admitted
recursion.

| Function (self / inclusive %) | Line | Refusal, short | Class | Justification |
| --- | --- | --- | --- | --- |
| `lay_out_context` box.wf (0.05 / 439, 0.06 / 246, 0.06 / 704) | 554 | `take_back` writes `fragments.inner` | W | Clears a window; each `take_back` moves `len`. The natural bulk clear has no prelude operation (W6). Cost negligible. |
| `finish_lines` inline.wf (19.0 / 54.1, 22.7 / 52.9, 21.8 / 55.6) | 1070 | value write at `segment_at[k]`, `k` not affine in `s` | S | Segments are disjoint; write per position, `for k: segment_at[k] = segment containing k` (binary search), or drop the table and search in `fallback_extents`. Cheap. |
| | 1117, 1125 | `take_back` on `fragments`, `atomics` | W | Window clear (W6). |
| | 1132 | `top = top +sat height` and the carried `stack`, `mark` | S | Line work depends on earlier lines only through the open-box chain at the line start (a function of mark nesting), the mark cursor (searchable), `top` and output order. Restructure below; residual sequential steps: the `top` scan and the ordered concatenation. |
| | 1145 | `parent_group` carried | T | Each open box's alignment group joins its parent's: a chain along the nesting. Bounded by nesting depth. |
| | 1167 | `visible_end` carried | T | Backward search for trailing collapsible spaces with early exit; usually 0–1 steps. |
| | 1201 | `low`, `x`, `p`, mark cursor carried | S | `x` is a `fadd.strict` prefix sum whose order fixes published bytes (T) and stays a cheap sequential walk; the independent per-position work (`fallback_extents`, shifts, text tops and heights, moves) moves to a per-position loop once the innermost open mark per position is known. |
| | 1205 | marks at position `p`, stack push/pop | T | Marks at one position are applied in source order; push/pop is the bracket structure. |
| | 1506 | prefix reads of `stack` | T | Iteration `k` sets `stack[k-1].emitted`, which the next iteration reads: a culled parent reports only when no child did. Bounded by depth. |
| | 1544 | two accumulators | T | `high` grows from `low` and `low` shrinks from `high`; top- and bottom-aligned groups interact in order. Few groups. |
| | 1578, 1594 | push into `paragraph^.fragments`, `atomics` | W | One unconditional append per iteration in index order (W5). Inside the line restructure these become iteration-own. |
| | 1628, 1645 | conditional pushes into `fragments` | W | Variable output per iteration in order (W2). Also: 1628 scans every mark of the paragraph for every line, O(lines × marks); a per-line mark range would remove that work. |
| | 1672 | `width_px = fadd.strict(...)` | T | Strict float sum; order fixes the bytes. Short (one text run). |
| `next_line` inline.wf (7.1 / 7.3, 9.4 / 9.7, 7.9 / 8.1) | 318 | `begin` read 3 times | T | Forward search for the first non-collapsible position with early exit; usually 0–1 steps. An `imin` reduction form is admitted but scans the whole remaining text per line. |
| | 337 | `candidate` and `width` carried | T | Greedy fill: the strict float running width and the first overflow decide the line end. Lines follow one another (break_lines:443). |
| `measure` inline.wf (2.8 / 10.6, 2.8 / 8.9, 3.2 / 13.7) | 208 | float read-modify-write at `opens[at]` | S | Per-mark work (`inline_frame` edges, `box_of`, `atomic_width`; about 6.2 / 4.3 / 8.8% in edge functions under `measure`) is independent: one per-mark loop writes per-mark arrays, then a sequential scatter keeps the true dependency, the `fadd.strict` order of marks sharing one position. Front-end accepted. |
| `break_lines` inline.wf (0.6 / 10.5, 0.7 / 13.3, 0.5 / 10.2) | 415 | `take_back` on `lines` | W | Window clear (W6). |
| | 443 | `top`, `start` carried | T | Greedy line breaking: each line starts at the previous end, and its top decides the room beside floats. |
| | 459 | `begin` carried across retries | T | Each retry moves the line below the float the previous retry found. |
| `framed_inside` inline.wf (0.7 / 7.0, 0.6 / 4.9, 0.6 / 6.7) | 688 | open-mark stack | S | Per-mark `box_metrics`, `margined_box`, `shifted_box` (5.3 / 3.4 / 5.4%) are independent; a per-mark loop computes them, the cheap bracket walk stays sequential (T: nesting). Front-end accepted. |
| `lay_out_table` table.wf (0.03 / 5.6, 0.17 / 20.2, 0.09 / 33.8) | 659 | column `edge` carried | T | Prefix sum of column widths. Few columns. |
| | 682, 801 | value write at `forced[item.child]` | W | Injective scatter through `item.child` (W3). Cheap. |
| | 711 | push of identical tracks | S | A fill: a `Box<Array<TableTrack>>` from `box_array_filled`. |
| | 723 | two signed `+sat` sums | T | Signed saturating sums are order-dependent (PAR-2's own example); trivial. |
| | 786, 879 | `y_cursor`, `bottom_cursor` | T | Prefix sums of row and caption heights. |
| | 864 | writes `children[cell]`, `cell = item.child` | S | Iterate children `k` (affine) and skip non-cells by `kinds`, with each cell's used border recorded per child; `position_out_with` then writes only element `k`. |
| `lay_out_flex` flex.wf (0.05 / 116, absent, 0.15 / 15.7) | 1626 | push of blank items | S | A fill with `item.child = i`: an array and an affine write. |
| | 1660 | `break` leaves the loop | S | The guard `if l < lines.inner.len` replaces the `break`; the `imax` accumulator is admitted. Front-end accepted. |
| | 1675, 1722 | call writes `&lanes` over `[first, end)` | W | Each line owns a disjoint, data-dependent range of lanes (W1). Cheap. |
| | 1695 | two writes of signed `natural_cross` | T | Signed `+sat`; trivial. |
| `stack_flow` flow.wf (1.7 / 4.4, 1.5 / 4.1, 1.0 / 14.3) | 1883 | `next_split` carried | T | First split past a position, early exit; a binary search would shorten but not parallelise it. |
| | 1901 | stacking state | T | The stacking pass, documented as the one walk that keeps the content's true order: margin collapsing, clearance and floats in document order. |
| | 2301 | `below` and `y` across attempts | T | Each float-avoidance attempt starts below the previous one. |
| `intrinsic_flow` flow.wf (0.07 / 3.8, 0.08 / 3.3, 0.16 / 11.5) | 3087 | `most`, `around`, frames carried | S | The walk (nesting frames, chunk segments) is cheap and sequential (T), but it calls `paragraph_intrinsic` twice per paragraph (3.6 / 3.1 / 6.9%); a per-paragraph loop before the walk, shaped like `break_all`, stores both widths in the unused `Paragraph.min_content` and `max_content`. Front-end accepted. |
| `paragraph_intrinsic` flow.wf (1.5 / 3.6, 0.8 / 3.1, 1.6 / 6.9) | 2978 | value write at `advances[at]` | W | Atomic marks sit at distinct positions: injective scatter (W3). Cheap. |
| | 3024 | `best = fmax(...)`, strict float run | T | Strict float sums within break segments, reset at each opportunity. |
| `prepare_spaces` flow.wf (0.6 / 2.7, 0.5 / 2.3, 0.4 / 1.6) | 273 | `next_split` and frames carried | T | Containing widths flow down the open-block nesting in document order. |
| | 345 | writes `children[child_at]` | W | Injective scatter over one paragraph's atomic marks (W3). |
| `prepare_table` table.wf (0.00 / 1.3, 0.02 / 4.3, 0.02 / 8.9) | 138 | value write at `kinds[child]` through `put_i32` | S | The value is the constant 1: a direct `set kinds.inner[child] = 1_i32` is PAR-2's constant-mark family, as `finish_lines:1087` (admitted) writes `edges[first]`. The costly cell intrinsic loop is already admitted. |
| `measure_rows` table.wf (0.02 / 0.04, 0.12 / 0.21, 0.05 / 0.09) | 470, 542 | `track_put` writes the whole window | S | Direct writes to `tracks^.inner[r]` are affine. |
| | 488 | `track_get`/`track_put` at `item.row` | U | The updates are `imax` on track fields and a `True` mark, which PAR-2's indexed families cover when written as direct field updates; settle with the ledger on that form. |
| | 552, 553 | `track`, `deltas` across spans and items | T | CSS Tables distributes spanning cells in span order over the sizes earlier ones produced. |
| `position_out_events` flow.wf (0.19 / 0.56, 0.23 / 0.41, 0.16 / 0.34) | 2573 | `counted = add_counts(...)` | W | After a cheap nesting pass for the anchor block, each positioned child is independent; refused by the record reduction (W4) and the scatter to `children[at]` (W3). |
| `entry_motion_at` splice_motion.wf (0.31 / 0.60, 0.30 / 0.58, 0.20 / 0.39) | 38 | field accumulator `output.travel` | W | Two accumulators (`travel`, `heights`) in one record (W4); `travel` is signed `+sat` and order-dependent by itself. |
| `intrinsic_flex` flex.wf (0.00 / 0.03, absent, 0.01 / 0.86) | 302 | several accumulators | S | Hoist `flex_contribution` into a per-child loop, as in `intrinsic_flow`; the sums stay sequential (signed `+sat`, T). |
| `place_atomics` flow.wf (≤0.05 / ≤0.35) | 1178 | writes `children[child]` | W | Injective scatter (W3). |
| `add_box_rects` inline.wf (0.23 / 0.24, 0.15 / 0.16, 0.40 / 0.70) | 630 | `child = parent` | T | Walks up culled ancestors to the first unculled one. |
| `measure_cells` table.wf (≤0.11 / ≤0.41) | 56 | conditional push into `items` | W | Ordered output with skips (W2). |
| `collapse_borders` tableborders.wf (≤0.18 / ≤0.33) | 127, 143, 185 | call-form accumulator through `merge_edge` | U | Adjacent columns and rows share edges; admitted only if `merge_edge` is an admitted operation update. Settle by reading `merge_edge` and the ledger. |
| `sort_keys` flow.wf (0.05) | 984 | `into_other` toggle | T | Merge-sort passes read the previous pass's output. |
| `filled_i32` tablegrid.wf (≤0.06) | 75 | push of copies | S | A fill: `box_array_filled`. |

#### Snowghost rewrites

Ranked by expected payoff; each moves work out of a sequential walk into a
loop whose iterations write only their own element.

1. `intrinsic_flow:3087` (3.6 / 3.1 / 6.9% under `paragraph_intrinsic`).
   Today every paragraph's min-content and max-content widths are computed
   one after another inside the walk over the context's events, while
   `break_all` already breaks the same paragraphs in parallel. Before the walk:

   ```
   for (q in 0_u64..paragraph_count) {
     let low_q = paragraph_intrinsic(paragraph: &context^.paragraphs.inner[q], children: &context^.children.inner[0_u64..children], styles: styles, minimum: yes_q);
     let high_q = paragraph_intrinsic(paragraph: &context^.paragraphs.inner[q], children: &context^.children.inner[0_u64..children], styles: styles, minimum: no_q);
     set context^.paragraphs.inner[q].min_content = low_q;
     set context^.paragraphs.inner[q].max_content = high_q;
   }
   ```

   and the walk's `Text` arm reads the two fields. It computes paragraphs
   inside fixed-width blocks the walk skips: extra work for a shorter chain.
   This is the only item here that adds parallelism across paragraphs; the
   others are within one paragraph.
2. `finish_lines` restructure (1132, 1201, with 1070), the largest work:
   finish_lines' self share plus `fallback_extents` (4.5 / 6.4 / 5.2%),
   `box_metrics` (6.2 / 5.0 / 5.7%), `culled_box` and edge functions.
   Phases: (a) a per-mark table, independent per mark: metrics, culled,
   vertical-align edge, relative offset, frame widths, shared with `measure`
   and `framed_inside`, which compute the same per-mark style values again;
   (b) a sequential bracket walk over the marks: parent mark, baseline shift
   (it depends on the parent's), and for each line the innermost open mark at
   its start and its first mark; (c) a per-position loop for
   `fallback_extents` and the text metrics; (d) a per-line loop writing only
   `lines[l]` and iteration-own fragment buffers, rebuilding its open-box
   chain from (b); (e) the `top` scan,
   `top_l = imax(top_{l-1} +sat height_{l-1}, least_top_l)`; (f) the ordered
   concatenation with `top_l` added. (e) and (f) are the named sequential
   dependencies. The per-position arrays (`xs`, `shifts`, `text_tops`, ...)
   are read only within one line, so they become line-local; otherwise each
   line writes a data-dependent range of them (W1). Expected payoff is the
   critical path of long paragraphs; correctness must be checked against
   the layout oracle.
3. `measure:208` (edge functions under `measure` 6.2 / 4.3 / 8.8%): a
   per-mark loop writes each mark's frame width or atomic width and glue
   flag into per-mark arrays; a second, sequential loop scatters them into
   `opens`, `closes`, `glued` and `advances`. The scatter stays sequential
   because marks sharing one position add `fadd.strict` contributions to one
   cell, whose order fixes the bytes.
4. `framed_inside:688` (5.3 / 3.4 / 5.4%): a per-mark loop computes
   `box_metrics`, `margined_box` and `shifted_box`; the bracket walk then
   compares stored values.
5. Small forms with no measurable payoff: `flex:1660` (guard instead of
   `break`), `measure_rows:470, 542` (direct element writes), `table:864`
   (iterate children), `table:711`, `flex:1626`, `filled_i32:75` (filled
   arrays), `prepare_table:138` (constant mark), `finish_lines:1070`,
   `intrinsic_flex:302`.

#### Whitefoot gaps

Each witness is a semantic sketch; the line numbers are its occurrences.

- **W1, disjoint data-dependent ranges to a callee** (flex 1675, 1722). With
  `starts` nondecreasing, `for (l in 0..n) { work(run: &data^.inner[starts[l]..starts[l+1]]); }`.
  PAR-2's proved range reference needs endpoint images `s*l+b`; RANGE-5
  states that a call through a reference argument naming a run leaves the
  certificate unproved. No form admits a partition given by an offset
  table.
- **W2, ordered output of a variable number of items per iteration**
  (finish_lines 1628, 1645, measure_cells 56, and the concatenation of the
  restructure). With `offsets` the prefix sums of `counts`,
  `for (l in 0..n) { for (j in 0..counts[l]) { set out[offsets[l]+j] = g(l, j); } }`.
  The subscript is not `a*l+b` with constant `b`. Whether an `apart`
  certificate over a monotonicity range fact proves the nested writes
  distinct is unsettled; a ledger run on this witness with that clause
  settles it.
- **W3, injective indirect scatter** (table 682, 801, prepare_spaces 345, place_atomics 1178, paragraph_intrinsic 2978,
  position_out_events 2573). `for (i in 0..n) { set out[idx[i]] = v(i); }`
  with `idx` injective. PAR-2 says an injectivity argument starts no proof
  search; RANGE-5 could certify it given an active fact
  `idx[i] != idx[j]` for `i != j`, which nothing in the renderer
  establishes where the indices are built.
- **W4, record or multiple scalar accumulators** (position_out_events 2573,
  entry_motion_at 38). `set total = add_counts(first: total, second: f(i));`
  where `add_counts` is field-wise unsigned `+sat`: associative, commutative,
  identity `no_updates()`. Smallest form: two unsigned accumulators,
  `set a = a +sat x; set b = b +sat y;`. PAR-2 admits at most one scalar
  accumulator, applied directly. Placing the fields in cells of a
  one-element array might match the indexed families, but that spelling
  exists only to obtain the permission.
- **W5, one unconditional append per iteration** (finish_lines 1578, 1594).
  `for (i in 0..n) { place_back(window: &out.inner, value: f(i)); }` with
  capacity reserved: iteration `i` fills slot `len0 + i`, but every
  iteration writes `out.next` and `out.len`, and `len0` is not a constant
  `b`. No filled window constructor or array-to-window append exists to
  write the slots as elements instead.
- **W6, no window truncate** (box 554, finish_lines 1117, 1125,
  break_lines 415). Clearing a window is a loop of `take_back`, sequential in
  `len`; `split_off` needs a destination with that much capacity. Low cost,
  but it is also why per-line scratch buffers are reallocated rather than
  reused.

#### Allocation

Call edges from layout functions into `malloc`, `free`, `realloc` and
`wf__heap_retake` carry 12.4 / 14.1 / 10.0% of the pass (inclusive edge `Ir`
from the Callgrind dumps). The largest callers: `finish_lines` 6.8 / 7.1 /
4.5% (plus 0.6 / 0.9 / 1.5% zero-filling in `memset`), `break_paragraph`
freeing the `Measure` 1.4 / 1.5 / 0.8%, `measure` 0.9 / 1.1 / 0.8%,
`framed_inside` 0.8 / 0.8 / 0.4%, `break_lines` window growth 0.6 / 0.7 /
0.3%, `paragraph_intrinsic` 0.4 / 0.4 / 0.5%, `add_fragment` growth 0.4 /
0.5 / 0.4%. Almost all of it is temporary storage per call or per iteration:
`finish_lines` allocates nine position-indexed arrays and an open-box stack
per paragraph and a `pending` window per line; `measure` allocates five
arrays per call and runs three times per paragraph that has intrinsic
sizes (min-content, max-content, breaking); `framed_inside` allocates three
per paragraph although marks and styles do not change during layout. Forms
that avoid it: one array of per-position records instead of nine arrays, one
`Measure` for both intrinsic widths, the per-mark table computed once per
paragraph, and reuse of per-line buffers, which W6 makes a loop.

#### Verified and inferred

Verified: loop text and refusal reasons (`loops.csv`), function shares
(`functions.csv`), allocation and callee edges (recomputed from the three
dumps), and the admission of `lay_out_children`, `break_all`, the flex item
loops and the table part loop (ledger rows). The pinned front-end module
check (`whitefootc --graph modules.wfg --check-module pkg::layout`, on a
scratch copy) accepts rewrite 1 alone, and rewrites 3 and 4 with `flex:1660`
together. A deliberate syntax error in an earlier draft was rejected, so the
check read the scratch sources. The module check reports no PAR verdicts and
`--par-ledger` requires a build, so PAR-2 admission of every S rewrite is
inferred from the rule text and from admitted loops of the same shape
(`break_all:508`, `measure:183`, `finish_lines:1087`), not observed. Not
verified: per-loop cost (no line information), every T claim beyond reading
the code, and the restructure of `finish_lines`, which was not written.
