# Mechanism of the owner-store regression

Source investigation, 2026-10-11. **The regression is established; its time
shares are not.** The strongest edit-path candidates are the extra dependent
page lookup relative to the current single-leaf baseline, and optimization
facts lost across that lookup. Fixed page geometry and additional allocations
are strong construction/memory candidates. Source inspection does not yet
choose (a) a Whitefoot gap, (b) a Snowghost usage problem, or (c) both.

Recommendation: collect the isolated update profile and optimized address
paths below before changing either implementation. If ordinary element writes
lose header/page separation in optimized code, that is a Whitefoot code
generation gap; changing Snowghost's spelling to conceal it is not the remedy.
No renderer change, compiler run, build, test, or measurement was performed
locally. The only local calculation applied the specification's layout-ceiling
arithmetic to the declared fields; it is not a performance measurement.

## Scope and source coordinates

`B:` below means Snowghost base
`030e4dd4081c9c15699363bdfa0e57c53a7f761d`; `C:` means inspected adoption head
`9f7cc92a622fb9600cafae7c21ffdcbda1c15c7a`. The measured candidate is
`2c2c171911933aef499e0fb96a288643803eacd5`; its renderer, pin and kit have no
diff against C. All `W:` coordinates mean Whitefoot
`78223721f77db615c950b6df1bcc690629f9fe4b`, read with `git show` in the local
clone, never its working files. Historical coordinates explicitly name their
revision. Paths and line numbers refer to those revisions, not future heads.

Evidence read: this investigation's [README](README.md) and
[RESULTS](RESULTS.md), the complete seven-file renderer storage diff, both
storage implementations and their replay/publication consumers, the pinned
kernel specification, Paged/contiguous/window/cleanup emitters, target geometry
and heap runtime, all pinned `lib/std/**/module.wfm` interfaces, the historical
C3 records and port, the layout/pipeline design ancestors, AGENTS.md,
Whitefoot-kit's downstream rules, and the review checklist. The standard
library interfaces supply no Paged bulk-fill or reserve abstraction; Paged's
operations come from the specification's PRE-1 records.

The [measured comparison](RESULTS.md#complete-initial-comparison) rejects
ecma262 sequential full layout (1.0331), HTML5 four-worker full layout
(1.0341), and ecma262 sequential font-size update (1.0908, 3.2% noise).
Style does not show the same regression. The focused HTML5 font-size results
also reject (1.0583 sequential and 1.0408 four-worker). These are aggregate
observations, not attribution to any individual helper.

## What each storage operation actually costs

### Ordinary access and full publication

The base is not normally a long recursive descent. Sealing builds **one
power-of-two contiguous Array leaf per owner per store**
(`B:renderer/layout/sequence.wf:303–345`). A normal un-grown read tests `slot
< span`, matches the leaf, tests `at < leaf.len`, and addresses an inline
element after the Array header (`B:sequence.wf:175–203,466–492`). Only later
growth introduces Fork paths. The candidate retains the span and length
guards but uses Paged (`C:sequence.wf:175–189,441–449`). It removes variant
dispatch/possible recursive descent and adds native page address formation.

`W:compiler/src/backend/emitter/paged.rs:43–63` emits, for **each requested
address**, a shift, mask, directory GEP, page-pointer load, and element GEP.
There is no integer division, page-bound check or allocation in that path.
The header-first directory is inline at cell + 24, not a separately allocated
directory (`W:paged.rs:11–22`). Ordinary Box access also reaches the cell
through its owner pointer. The extra load is the page pointer relative to an
Array leaf, not an extra standalone directory object. LLVM may combine or
hoist repeated address calculations; emitter occurrence counts are not
optimized instruction counts.

Both versions already use field-narrow helpers. The candidate does not
introduce whole-SequenceNode copies in `slot_cursor`, `slot_view`,
`slot_geometry`, `slot_links`, or `slot_store_actions`:
`B:sequence.wf:175–203,543–568`, `B:range.wf:56–150` versus
`C:sequence.wf:175–189,476–485`, `C:range.wf:56–104`. Output access still
copies the selected SequenceOutput, and output publication still writes that
output plus its structural weights:
`B:sequence.wf:576–650` versus `C:sequence.wf:494–538`.

The particularly relevant dense publisher changes from a contiguous leaf loop
(`B:boundary.wf:513–556`) to a flat Paged loop
(`C:boundary.wf:513–530`). Each live slot reads node liveness, reads a payload,
then writes own and total outputs. The emitter can request multiple page
addresses for that slot. Metadata and payload page sizes differ, so there is
no single common physical-page loop for both. The true dependencies are
unchanged: each published slot depends on its completed reduction and rank;
slots are independent. A page reference could amortize node addressing, but
that is a proposed diagnostic comparison, not an established fix.

**No implicit runtime bounds-check regression is supported by source.** OP-4
(`W:spec/kernel-spec.md:1069–1076`) requires compile-time discharge and states
that accepted subscripts have no runtime check in every mode. The explicit
source `if` guards execute in both versions. Losing a source proof gives a
compiler refusal, not a synthesized safety check. Losing an LLVM optimization
fact can instead leave additional loads or source guards in the machine code.

### Possible lost optimization facts

The Paged element address loads a pointer from the directory with no access
alias metadata (`W:paged.rs:62`). The contiguous window path instead forms
an inbounds GEP into the same object and can emit a nonnegative-offset
`llvm.assume`; Paged returns before this path
(`W:compiler/src/backend/emitter/runs.rs:652–687`). Those facts are not
interchangeable: a nonnegative Paged index alone cannot establish which
allocation the loaded page pointer belongs to.

The backend explicitly emits no per-access alias scopes
(`W:compiler/src/backend/emitter.rs:1751–1753`). A `&Run<T>` carries a
directory pointer, origin and length, and deliberately lacks `noalias`, because
disjoint runs may share the directory (`W:emitter.rs:1771–1778,1810–1815`).
Sealing changes `bulk_nodes`' contiguous `&[SequenceNode]` argument to
`&Run<SequenceNode>` (`B:sequence.wf:271`, `C:sequence.wf:254,315`;
`W:paged.rs:81–95,318–328`). This is a real lowering difference, but simply
putting `noalias` on the shared directory would be unjustified.

Hypothesis: stores through an opaque loaded page pointer may make LLVM
conservatively reload the header's `len`, the Box's cell pointer, or directory
entries, and prevent commoning/vectorization across field writes. Element
storage and header/directory storage are actually disjoint; no growth happens
in the dense publisher. **Whether these reloads survive optimization is
unverified.** Read-only point helpers may optimize well even if write loops do
not. Inspect both kinds rather than inferring all costs from bulk construction.

### Geometry, allocation and initialization

The native page length is the largest power of two fitting 4096 bytes of
**language stride ceiling**, not actual target stride
(`W:spec/kernel-spec.md:1164–1177,1231`;
`W:compiler/src/target.rs:453–482`). Applying that rule to the declarations:

| Type | C3 language stride ceiling | Current ceiling | C3 native B | Current native B |
| --- | ---: | ---: | ---: | ---: |
| Flow | 28 | 28 | 128 | 128 |
| SequenceCursor | 48 | 48 | 64 | 64 |
| SequenceOutput | 128 | 192 | 32 | 16 |
| SequenceNode | 304 | 528 | 8 | 4 |

Sources: `3abffd8:renderer/layout/module.wfm:82–89,106–177` and
`C:module.wfm:82–89,107–110,144–182,222–239,257–267,301–307`. Flow's ceiling
includes the tag and **all six alternative payloads** under OP-9, even though
the actual union needs only one. B is source-derived; actual element stride,
page bytes and allocator size classes must be confirmed in CI's LLVM and
allocation evidence. A four-slot Flow owner still reserves one 128-slot
physical page; a 128-slot node owner allocates 32 four-slot pages instead of
the base's single 128-slot leaf. The fixed page policy therefore affects tiny
payload owners and large metadata owners differently.

Empty construction now allocates two zero-capacity Paged cells
(`C:sequence.wf:165–172`), versus two allocation-free Vacant values
(`B:sequence.wf:165–172`). The emitter reserves at least one directory entry,
so each empty cell requests 32 bytes, without any element page
(`W:paged.rs:143–167,239–267`). Nonempty sealing constructs replacement cells
and disposes of those initial cells (`C:sequence.wf:307–324`); this adds
allocate/free traffic even before physical pages are considered.

Paged construction and growth allocate every physical page through **capacity**,
including a partially used last page (`W:paged.rs:153–167,270–315`). Pages
come from `wf__heap_take`, which uses malloc, not calloc
(`W:paged.rs:132–138`, `W:compiler/src/backend/heap.c:16–21`). Only the
header and directory entries are written by construction: **no automatic
whole-page zeroing** appears in this emitter. Allocation accounting uses
thread-local counters and a relaxed atomic store, not a lock on every take
(`W:compiler/src/backend/completion/bridge.c:1360–1373`). More allocations
still incur that accounting and allocator work.

The source then initializes the full logical power-of-two span with dummy
values via `paged_fill`, and overwrites live payloads and node links
(`C:sequence.wf:305–319,452–460`). The base also initialized the full span
with dummy values (`B:sequence.wf:322–334`), so neither padding nor duplicate
initialization is wholly new. The difference is one Array-fill loop with a
single length publication (`W:compiler/src/backend/emitter/buffer.rs:281–309`)
versus per-element `place_back` through a page address and a changing length
word (`W:runs.rs:451–455,459–495`). Initialization has a serial boundary
dependency; topology and payload construction after initialization do not.
If this natural append loop fails to optimize into a page fill, the missing
bulk operation or lowering may belong in Whitefoot. Initializing only live
slots is a separate possible Snowghost policy improvement, not proof that the
current dummy-padding overhead explains the regression.

Release frees every allocated Paged page; copy-only Flow/SequenceNode need no
per-element destructor (`W:compiler/src/backend/emitter/cleanup.rs:1158–1208`).
Full-layout repetitions include layout construction and release
(`C:renderer/oracle/layout/layout.wf:862–897`), so extra frees belong to the
full-stage hypothesis too.

### Growth and splice paths

Base reserve wraps old roots and adds vacant right subtrees; a subsequent write
allocates only its missing path and four-slot leaf
(`B:sequence.wf:401–424,495–539`). Candidate reserve doubles logical span,
reserves both stores through that span, and slot writes initialize through
the new index (`C:sequence.wf:384–398,463–473`). Native growth allocates missing
pages and, only when directory capacity increases, copies **old page pointers
and the header**, never existing elements (`W:paged.rs:176–233`). Directory
capacity doubles. Within one existing physical page, logical capacity growth
allocates no new page. Repeated full payload copying on growth is ruled out
by this source; reservation of unused future pages remains plausible.

Splice relocation also changes contiguous leaf loops into flat Paged loops
(`B:splice_sequence.wf:179–218` versus `C:splice_sequence.wf:179–198`). Its
slot writes remain independent and only private replacement stores are
visited. Attribute this only if those callers occur in the selected timed
edit; the font-size script is a style edit, not a structural edit. The route
table remains sparse recursive storage: the old slot helpers were copied
and renamed to `route_slot_read/write`, not ported to dense Paged
(`B:sequence.wf:466–539`; `C:routes.wf:125–202`). Routes and target Slots
pools are not evidence of a new global Paged pool.

## Why font-size edits can regress more than full layout

The replay bridge uses sequence reads and publication repeatedly without
necessarily reconstructing the tree. `C:update.wf:1657–1674` materializes flow
for unscoped replay and finishes its reference scope;
`C:reference.wf:282–295` sends an incomplete scope to full publication;
`C:reference.wf:13–28` normalizes retained actions and calls
`publish_boundaries`. That publisher reduces the AVL and scatters results for
the context and its blocks (`C:boundary.wf:544–564`). Action normalization,
when active, also repeatedly reads/writes Paged slots
(`C:range.wf:721–788`). These algorithms already exist in the base; the diff
changes their leaf addresses, not their replay admission rules.

This supplies a mechanism for a larger percentage on replay than on a full
stage diluted by unchanged styling, text and other layout work. It does not
prove that every font-size ordinal takes this bridge. Existing update counts
and phase call edges must establish that. The timed style-edit U also includes
delta/font picks/marking outside `wf_layout.update`, while `style_us` is
separate (`C:renderer/oracle/layout/edit.wf:1629`). Isolated update profiles
must be compared with the enclosing totals before assigning the whole 9.1%.
Startup-only allocation counts cannot explain an update-only regression.

Peak RSS supports a geometry hypothesis but not a causal time share:
ecma262 sequential full layout is 536.69 versus 581.82 MiB; font-size process
peak is 814.66 versus 877.59 MiB ([initial RSS table](RESULTS.md#peak-rss)).
Those are whole-process high-water marks, including setup. Increased residency
may affect retained reads even if timed updates allocate nothing; conversely,
uninitialized reserved pages do not necessarily become resident in full.

## Reconciliation with C3

The [historical C3 attribution](https://github.com/Ming-Research/Snowghost-wf/blob/2d9fdf032992610986668f550ccb52f066d61143/research/investigations/storage-layout/c3-attribution/README.md)
compared `pages` at `8d5fab0f1586455ebc39aef1cd666d4e95dd5ae1` with
`nodeshf` at `3abffd812bb4c532657dc4853e06eb964b720e11`, using
`wf-exp-f1971c00269a` for the latter. “Same shape” meant **one store per
existing owner**, not identical geometry to today's base.

- C3's hand-written baseline was already a two-level pointer directory with
  a 4–64-slot first leaf and 64-slot subsequent leaves
  (`8d5fab0:renderer/layout/pages.wf:1–59`). Today's baseline begins with one
  contiguous power-of-two leaf, so Paged adds a directory-dependent address
  to a different starting point.
- C3's candidate retained an outer Vacant/Pages wrapper and allocated nothing
  for empty owners (`3abffd8:sequence.wf:135–140`, `pages.wf:29–43`). Today's
  candidate has eagerly created empty cells. C3 initialized a rounded first
  block plus 64-slot tail; today initializes a power-of-two span. Both
  candidates use the native type-dependent Paged geometry underneath.
- C3's node had two shorter outputs and no RangeActions
  (`3abffd8:module.wfm:112–165`); today's node has B=4 instead of B=8. C3 also
  ported RouteTables, which PR #61 leaves recursive (`3abffd8:module.wfm:92–103`
  versus `C:module.wfm:92–104,289–292`).
- The pinned Paged emitter uses heap-accounted take/give; C3 used plain
  malloc/free. The emitter diff otherwise preserves the address path, eager
  pages and directory floor of one. Both current cohorts use the same pin,
  so compiler-version drift is not a confound within today's comparison.
- C3 measured HTML5 only, no edits, ten repetitions and best of three rounds
  on the 14900K (historical README:53–56,79–102). Its twins reused executables
  (`07fd14f:.github/workflows/time-14900k.yml:135–154`; raw base/twin driver
  hashes agree). Today uses independent builds, median paired ratios,
  reversed interleaving, hosted machines, more repetitions and full scripts.

C3's 1.015 sequential / 1.008 four-worker whole-layout ratios are within its
noise band, not evidence of zero overhead. Its sequential box ratio 1.093
already exposed construction loss. Its “half geometry, half allocation”
account is limited to that historical box experiment (README:105–125), not a
share to apply to today's full layout or font-size edits. The two records do
not contradict each other.

## Ranked hypotheses and separating observations

The order prioritizes explaining the font-size rejection. No additive
percentage shares can be inferred yet; these causes interact.

| Rank | Hypothesis and plausible scope | Observation that separates it |
| --- | --- | --- |
| 1 | Extra dependent directory load and shift/mask in the now-paged owner leaf. Can explain both full and allocation-light replay; 9% is plausible if replay is concentrated in slot access, but not established. Evidence: base leaf `B:sequence.wf:185–189`, candidate `C:sequence.wf:182–185`, `W:paged.rs:43–63`, publisher comparison above. | Update-only excess instructions/cycles concentrate in `slot_cursor/output/view/geometry`, `reduce_sequence`, `store_reduction`, or their inlined callers, with comparable call/update counts and little allocator activity. Reject as dominant if those paths contribute little absolute excess. |
| 2 | LLVM cannot retain header/directory/element separation across writes; repeated loads, guards or scalarized stores amplify the basic address cost. This is a potential Whitefoot gap, not established from raw emission. Evidence: `W:paged.rs:62`, `W:runs.rs:652–687`, `W:emitter.rs:1751–1778`; base/candidate publisher and bulk-node paths above. | Optimized disassembly has post-store header/page-pointer reloads or lost loop optimization absent from base; a minimal same-source compiler fix removes them and the isolated instruction excess without changing page geometry or algorithm. Reject this subcause where optimized loads are already commoned/hoisted. |
| 3 | Fixed physical geometry, extra empty cells and many more allocations expand resident working set and allocator/free work. Strong for full construction and RSS; for replay only residency or actual timed construction can matter. Evidence: `B:sequence.wf:165–172,322–340`, `C:sequence.wf:165–172,307–324`, `W:paged.rs:143–167,270–315`. | Build/release call edges and allocation counts increase as predicted; retained update instruction counts stay close but cycles/load stalls/cache or dTLB misses increase. Separately count owner-size distribution and requested bytes. Reject startup allocator activity as explanation of an isolated update excess. |
| 4 | Serial append initialization and power-of-two logical reservation add avoidable source work or expose a missing bulk-fill lowering. Strong for sealing/reconstruction; weak for a retained style edit unless constructors appear inside update. Evidence: `B:sequence.wf:322–334`, `C:sequence.wf:305–319,452–460`, `W:buffer.rs:281–309`, `W:runs.rs:451–495`. | `paged_fill/finish_sequence` dominate build excess, per-slot length loads/stores survive optimization, and the same functions appear in update if claimed there. Reject for the edit if its timed call graph contains no sealing/fill. A live-length-only diagnostic must preserve identities/output and run the full checks before it is called a usage fix. |
| 5 | Eager reserve through doubled capacity and directory copying on growth. Valid construction/splice concern, probably small for this font-size path. Evidence: `B:sequence.wf:401–424,495–539`, `C:sequence.wf:384–398,463–473`, `W:paged.rs:193–233`. | Count growth calls, old/new page counts, pointer-copy bytes and newly allocated pages **inside** update. Zero calls reject it for that stage. Copies proportional to payload bytes would contradict the inspected lowering and require investigation; only directory-word copying is predicted. |

## CI profile and acceptance plan

The temporary [workflow](../../../.github/workflows/paged-mechanism.yml) and
its wired script collect evidence, not a pass/fail performance verdict. Remove
them when this mechanism round ends. Default push work is a bounded pilot;
full profiling is an explicit dispatch after reading its durations. The
frozen sample artifact comes from run 38096036798, the independent-build run
in RESULTS, and includes all four cohorts, exact pages, CSS and complete X5
scripts. Refuse reuse if renderer, pin or kit differ from its recorded
candidate. Record tools, CPU/kernel, font/input/script/binary/compiler hashes,
commands, exit status and profile availability. Retain emitted LLVM and
disassembly from the frozen source revisions; neither replaces optimized
machine-code inspection.

Start with **ecma262 sequential**, `WF_WORKERS=1`, because both its full layout
and font-size update reject. Use `layout_oracle layout REPS PAGE UA
SUFFIX=SHEET ...` and `layout_oracle edittime SCRIPT PAGE UA SUFFIX=SHEET ...`,
the argument construction of `measure.py:27–46`, from the repository root.
Every page, script, UA and mapped-sheet file path passed to the driver is
relative to that root; the driver accepts RelativePath inputs rather than
absolute filesystem paths (`renderer/oracle/support/support.wf:162–181`).
The profiler reuses `measure.py`'s sheet mapping and records cwd, worker count,
stderr text and its retained file beside each command and exit status. Run two one-layout
and two first-font-size-pair samples, time them, and cap the next scale from
those durations. Do not replace the acceptance script with a repeated pair:
the full profile uses the complete X5 font-size script and preserves ordinals
and counts. Verify base/candidate count equality, including refusals; otherwise
different work rather than storage overhead must be investigated first.

Use Callgrind instruction counts and call edges with collection toggled around
`wf_layout.update` for font-size edits and `wf_layout.lay_out` for the layout
kernel. A zero-edit/zero-repetition negative control must collect zero; a
positive sample must collect nonzero. For construction/full costs retain
whole-process profiles or before/after phase dumps covering `wf_layout.build_boxes`,
the kernel, and teardown. `lay_out` alone excludes the box builder and text
preparation; do not label it whole full layout. Full update dumps separate
each ordinal from setup/style; `finish_style_edit` is broader than update.
Callgrind instruction counts are not native time, cache stalls or four-worker
scheduling evidence. Inspect self cost and call edges, not summed overlapping
inclusive percentages.

The written workflow implements Callgrind phase profiles and optional
whole-process perf stat for common hardware counters and page faults/context
switches. The perf record, L1/dTLB events and native zero-work stat comparisons
below are follow-up commands for the primary agent, not implemented workflow
features. Workflow execution, marker survival, dump boundaries and control
rejections remain unverified until CI runs.

On a runner exposing PMU events, collect matched native `perf stat` groups:
`cycles,instructions,branches,branch-misses`;
`cache-references,cache-misses`; and supported L1 data-load / dTLB load-miss
events (`perf list` determines spelling). Also retain `task-clock,page-faults,
minor-faults,major-faults`. Use `perf record -F 99 -m 1024 --call-graph
dwarf,4096` with explicit sample-loss records, followed by symbol reports and
annotation/disassembly of the hot helpers. A whole-process stat includes
startup: match zero-work controls and use phase isolation before claiming an
edit-only share. Missing hardware access must be reported **unavailable**, not
zero misses. Hosted PMU denial leaves instruction attribution usable but memory
latency unverified; arrange any precise timing follow-up on the 14900K through
CI under the project's machine rules. Do not change event selection silently
between cohorts.

For hypotheses 1–2 annotate header/Box loads, page-pointer loads, shift/mask,
branches and transfer copies in the optimized helpers. Compare call counts and
absolute extra instructions per slot against the isolated update total. For
3–5 use allocation/free call edges and phase placement first; if they cannot
provide requested-byte/page counts, a Whitefoot-owned diagnostic runtime can
record size histograms and page/growth counts without modifying renderer
semantics. Any instrumentation's timing stays out of the acceptance table.
No shared cache, global allocator counter or serial renderer pass is proposed.

Once the sequential cause is visible, repeat **HTML5 four workers** full layout
with `--par` drivers and `WF_WORKERS=4` on one machine, to test whether the
same mechanism explains its 3.4%. Compare compiler task offers/joins for
`store_reduction`, block publication and relocation; changed worker scheduling
cannot explain the sequential rejection by itself. Use the independently
built twins and three reversed interleaved rounds for any subsequent native
performance claim, applying the original noise/rejection criterion. Percentage
shares require same-source interleaved before/after compiler or usage changes,
each with a twin control and independent correctness checks; profile fractions
alone cannot establish them.

## Candidate Whitefoot gaps and minimal witnesses

These are semantic witness **fragments**, not locally compiled programs or
filed requests. Only the growth-inverse witness already has a hosted refusal.

1. **Header/element separation missing from optimization (hypothesis).** A
   writer naturally expects an element field write not to mutate the window's
   header or its page directory:

   ```whitefoot
   struct Cell { x: u64; y: u64; }
   fn touch(p: &Box<Paged<Cell>>) -> result: unit writes(p) {
     let count = p^.inner.len;
     for (at in 0_u64..count) {
       if at < p^.inner.len {
         set p^.inner[at].x = at;
         set p^.inner[at].y = at;
       }
     }
     return unit;
   }
   ```

   Acceptance: initialize distinct values across at least two pages, check
   both written fields and unchanged len/cap, then inspect optimized code for
   retained directory/header invariance and reuse of each same-slot address.
   Use a write-through-`&Run<Cell>` subrange variant too; distinct subranges may
   share their directory. A blanket directory `noalias` is not acceptable.
   If the missed optimization explains the renderer excess, file the minimal
   witness with the instruction/assembly regression test and renderer criterion
   as the acceptance test, not a Snowghost local-pointer workaround.

2. **Natural bulk initialization lacks a suitable lowering/API (hypothesis).**

   ```whitefoot
   let p = box_paged_new::<Cell>(capacity: n);
   let zero = Cell(x: 0_u64, y: 0_u64);
   for (at in 0_u64..n) {
     if p.inner.len < p.inner.cap {
       place_back(window: &p.inner, value: zero);
     }
   }
   ```

   OP-10 permits this; its published len evolves at every append. Acceptance:
   normal and zero length, page-boundary lengths, final values/len/cap and later
   growth remain correct; optimized emitted work fills elements with no
   unnecessary repeated header traffic. Determine whether recognizing this
   source loop suffices before asking for a bulk constructor. A Snowghost
   live-prefix policy is viable only if it preserves the storage contracts and
   parallelism; no timing benefit or gap classification is established yet.

3. **Tiny/empty owner cost in intended Paged use (known policy, gap status open).**

   ```whitefoot
   let empty = box_paged_new::<u32>(capacity: 0_u64);
   let one = box_paged_new::<u32>(capacity: 1_u64);
   place_back(window: &one.inner, value: 7_u32);
   ```

   The first reserves a cell; the second reserves a full native page. This
   implements OP-13 faithfully, not a compiler correctness bug. Whitefoot's
   Paged research DESIGN explicitly deferred a smaller first page under “Not
   in this change.” If profiles establish unacceptable cost for natural
   per-owner stores, bring compact/lazy first storage to Whitefoot rather than
   silently restoring hand-written tables or pooling unrelated owners. Any
   policy change must preserve observable B, page-reference extents, no-element
   movement on growth, and checked allocation behavior. A lazy optional owner
   in Snowghost is another direction to evaluate, not a delivered remedy or
   justification to hide a demonstrated compiler gap.

4. **Growth forgets the owner inverse (already established, separate from time).**
   [grow-inverse.wf](grow-inverse.wf) owns a range invariant linking
   `targets[order[k].Open.block].entry_slot == k`; its writer only calls
   `grow_paged` at lines 16–20. The pinned release's hosted RANGE-3 refusal and
   exact diagnostic are retained in [README](README.md#hosted-growth-refusal).
   OP-10 moves no elements, but its whole-cell row discards content facts under
   RANGE-2. Acceptance is that unchanged minimal writer compiles and corrupted
   inverse writers still fail, without a validation loop, redundant stores or
   fixed capacity. This explains the deferred owner-motion proof; no invariant
   was adopted in the storage-only port, so it does **not** explain the measured
   runtime regression. Existing disposition: `sg-paged-grow-inverse`.

No new Whitefoot request, pin movement, submodule movement, or design/approval
log change was made in this round. The primary agent should file a performance
gap only after the profile separates compiler facts from source policy, with
the witness and falsifiable acceptance condition above.
