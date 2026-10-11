# Mechanism of the owner-store regression

Source and CI-artifact investigation, 2026-10-11. **The regression and a
Whitefoot optimization gap are established; their time shares are not.**
Optimized candidate output writes reload page-directory entries across element
writes where the base retains its array address. Point access adds a dependent
page load, but removal of leaf dispatch can offset its instruction count.
Fixed geometry and allocations remain construction/memory candidates. The profiles establish both a Whitefoot directory-separation gap and added
construction/release work from geometry and eager ownership. They do not
identify their shares of the native timing regression; the sampled updates
actually execute fewer instructions.

Recommendation: bring the verified element/directory separation gap to
Whitefoot with the witness below, and complete the matched isolated update
profiles before assigning its share of the regression. Changing Snowghost's
spelling to conceal it is not the remedy.
No renderer change, compiler run, build, renderer test or performance
measurement was performed locally. The file-reader checks below ran locally
with `python3 -I` under the user's explicit authorization. Local calculations use declared layout ceilings and text processing
of the downloaded CI artifact; they are not performance measurements.

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
in the dense publisher. **Page-entry reloads survive optimization in the frozen candidate output writer**,
as detailed in the CI evidence below. This does not establish every possible
header/cell/len reload or failed vectorization in every loop. Read-only point
helpers must be assessed separately from write paths.

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
the actual union needs only one. B is source-derived; the artifact confirms node stride 528 and Flow stride 8
in optimized address formation. Page bytes and allocator size classes still
need confirmation from CI allocation evidence. A four-slot Flow owner still reserves one 128-slot
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

## What CI run 38139461660 verifies

Evidence: [CI run 38139461660](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38139461660),
artifact `paged-mechanism`. Coordinates in this section refer to that artifact's
files, not repository files; the artifact is not copied into this repository.
Both optimized disassemblies are from the frozen measured sequential drivers.
`base.ll` and `candidate.ll` are **conservative source lowering**, not optimized
LLVM: the workflow requests `--emit-llvm`; `W:compiler/src/bin/whitefootc.rs:779–787`
writes the module directly and returns before linking/optimization. They show
where addresses originate, while the disassembly establishes which operations
survive optimization.

### Lookup cost depends on the access shape

In `wf_layout.slot_links`, the valid initial-leaf address path is **12 executed
non-padding instructions in base versus 11 in candidate**, through the element
stride multiply, before the field-transfer instructions. Base coordinates:
`base.disassembly.txt:337594–337595,337598–337600,337612–337618`; candidate:
`candidate.disassembly.txt:337272–337282`. Candidate's page-specific work is a
copy, `shr $2`, `and $3`, and directory-entry load at `13f796`; both then use
`imul $528`. This replaces base tag load/compare/branch and empty-variant
test/branch. Thus this representative point access has **net −1 instruction**,
not a uniform additive lookup tax. It still accesses a page through a loaded
directory entry rather than forming an inline Array address. Conditional
branches fall from four to two on that path. No integer division or implicit
bounds check appears. Lowering counterparts are `base.ll:425461–425549` and
`candidate.ll:427283–427333`; these are not optimized instruction counts.

The frequently sampled reads also remove dispatch work on valid initial-leaf
paths. All counts exclude padding and assume the corresponding successful
branch:

| Optimized path | Base instructions | Candidate | Delta | Artifact disassembly coordinates |
| --- | ---: | ---: | ---: | --- |
| `sequence_select`, current node through liveness | 17 | 14 | −3 | base 340709–340713,340716–340718,340731–340739; candidate 340078–340091 |
| `sequence_select`, left child through event count | 17 | 12 | −5 | base 340741–340745,340747–340749,340763–340771; candidate 340093–340104 |
| Flow `slot_read$instance$510b5e22e4c688b6`, complete successful call | 21 | 15 | −6 | base 475342–475352,475364–475369,475377–475380; candidate 473530–473544 |

`sequence_select` reuses cell and length between current-node and child
accesses in one descent, and reuses each selected element address for its
fields. Across descents, candidate still loads the invariant cell and len at
`142273`/`142277` (`candidate.disassembly.txt:340081–340082`) despite no stores
or calls in that loop. This is missed read-only hoisting, not evidence of
post-write invalidation; the selected page/index changes and cannot simply be
hoisted. Its conservative lowering is `candidate.ll:428476–428596` versus
`base.ll:426721–426841`. The Flow reader's stride-eight multiplication folds
into the memory operand. These hot reads weaken a blanket instruction-count
explanation; dependent-load latency and physical locality remain candidates.

The dense `wf_layout.store_reduction` loop is different. Base advances a
contiguous node pointer by 528 bytes each iteration
(`base.disassembly.txt:208669–208672`); candidate recomputes the metadata
page/offset and payload page/offset at each slot
(`candidate.disassembly.txt:208620–208643`). Through Flow dispatch, the base
prefix has 12 executed instructions versus candidate's 24: **+12**. Own/total
copy setup adds another three, the post-copy register restoration adds one,
and the loop increment removes one: **+15 caller instructions per successfully
published live slot**, along corresponding Flow branches, excluding identical
copy bodies and once-per-call setup. Supporting ranges:
`base.disassembly.txt:208703–208718` versus
`candidate.disassembly.txt:208662–208681`. This count includes the reload
below; hypotheses 1 and 2 must not double-count it. Lowering counterparts:
`base.ll:252727–252954`, `candidate.ll:252756–252932`.

### A narrow Whitefoot optimization gap survives

`wf_layout.slot_store_output` retains its cell/header address in `%rbx` and
its page index in `%r14`; it does **not** reload all headers, lengths or Box
pointers after each write. However, the total-output branch loads the same
page-directory entry after its output copy, writes `events`, reloads that
unchanged directory entry, and writes `count`:

- `candidate.disassembly.txt:337427–337435`: `13f9bc` copy call,
  `13f9c1` page load, `13f9cb` element-field store, `13f9d0` identical page
  load, `13f9d9` element-field store. There is no call, growth, index change
  or directory mutation between the two scalar stores.
- `base.disassembly.txt:337816–337822`: the base retains its contiguous leaf
  address and combines the two weights with `movdqu`, `pshufd`, `movdqu`.
- `candidate.ll:427626–427661` emits repeated Box/page addressing across
  the copy and scalar writes. Optimization removes Box-pointer repetition,
  but not the directory-entry repetition.

Own-output publication also reloads the page once after its copy
(`candidate.disassembly.txt:337416–337421` versus
`base.disassembly.txt:337808–337812`). In `wf_layout.store_reduction`, the
candidate similarly reloads the node page after the own copy before the total
copy (`candidate.disassembly.txt:208668–208673`, `c3f89` → `c3f8e`); base
retains `%rbp` across both (`base.disassembly.txt:208708–208714`). These are
verified failures to preserve the semantic separation of directory storage
and element storage. This is a Whitefoot optimization gap, with the minimal
same-slot two-field witness below; a renderer spelling change would conceal it.
The artifact does not prove that blanket directory `noalias` is safe, nor does
it identify the exact metadata/lowering change that should supply the fact.

### Dynamic scope and what remains unresolved

Invocation controls, both native pilot rounds, all zero-work Callgrind
controls and the base two-edit update profile passed. `phases.jsonl:1–2`
records **2,862,479 and 2,866,420 instructions** for the two base updates.
This run has no matched candidate update profile. The subsequent run below
supplies that comparison; neither run provides native time shares. In the base function attribution, `store_reduction` has only
212 self instructions over two calls and `publish_boundaries` only 432 over
two calls. The dense publisher example alone therefore cannot explain the
first-pair regression. `sequence_select` (547,348 self instructions, 5,046
calls) and `slot_read<all>` (131,796, 6,276 calls) merit priority in the matched
comparison; inlined storage work is charged to its caller.

The failed layout check confused requested markers with actual boundaries.
Its retained dumps have four triggers, at line 14 of each part:
`.1` before `build_boxes`, `.2` after `build_boxes`, `.3` after `pick_all`,
`.4` after `lay_out`. `prepare_text` is inlined: the driver calls
`prepare_context` directly. `.4:1844–1850` includes both preparation and layout,
so it cannot be called an isolated layout kernel. The corrected profiler
requires these four exact ordered triggers, nonzero measured intervals, and
the named functions, including both `prepare_context` and `lay_out` in the
combined interval. It still rejects missing/extra/wrong boundaries; the
corrected invocation subsequently passed in run 38141932250. Full matched profiles must establish dynamic
access counts, instruction excess outside these examples, allocation/growth
placement and whether memory latency explains excess time with modest
instruction differences. None of the +3%/+9% time shares is settled here.

## Matched profiles from CI run 38141932250

Evidence: [successful CI run 38141932250](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38141932250),
artifact `paged-mechanism`. The invocation, negative controls and phase mapping
now pass. Both pilot rounds have identical phase totals and identical function
self costs/calls. Exclusive costs reconcile exactly with the raw summaries;
function CSV sums reconcile with each selected phase. Counters are **Ir only**:
no cache, branch, cycle or perf observations were collected. Do not interpret
that absence as a PMU permission rejection. All four update-profile stderr
files contain a nonfatal `brk segment overflow` warning despite exit zero;
Valgrind's allocation environment is another reason not to treat its elapsed
process time as native performance.

### Phase totals and comparison with native time

The font-size profile covers only `C/K 303118 x5f`, the first forward/inverse
pair of the original 20-edit script. Each reports prepared 12, contexts 5,
paragraphs 1 (`native-edits.jsonl` and profile raws). These do not represent the full-script work behind the recorded +9.08%.
RESULTS averages all timed ordinals within a round and reports the median
paired-round ratio; it does not take a median over individual updates.
`scale-selection.json` records
`full_requested: false` and a conservative 1,344.52-second full-process estimate
above the 900-second cap. Successful CI did not run the complete edit script.

| Interval | Base Ir | Candidate Ir | Delta Ir | Change |
| --- | ---: | ---: | ---: | ---: |
| Font-size update 1 | 2,862,479 | 2,572,663 | −289,816 | −10.1247% |
| Font-size update 2 | 2,866,420 | 2,579,800 | −286,620 | −9.9992% |
| Both updates | 5,728,899 | 5,152,463 | −576,436 | −10.0619% |
| Box construction | 1,049,039,467 | 1,101,139,609 | +52,100,142 | +4.9665% |
| Font picks/bookkeeping | 523,346 | 523,334 | −12 | −0.0023% |
| Preparation + layout/bookkeeping | 8,760,622,178 | 8,756,355,120 | −4,267,058 | −0.0487% |
| Selected full-layout intervals | 9,810,184,991 | 9,858,018,063 | +47,833,072 | +0.4876% |
| After layout through termination | 359,464,599 | 384,260,759 | +24,796,160 | +6.8981% |

Coordinates: `phases.jsonl:1–20`; each layout's undotted `.callgrind` final
dump has the termination summary at line 18. Whole layout-process delta is
+72,629,212 Ir: selected intervals +47,833,072, final dump +24,796,160 and
startup −20. Construction through termination adds +72,629,232 Ir (about
+0.7142% over its base sum), but includes global cleanup. The original full
stage uses elapsed `T(repetitions)−T(0)`; this one-repetition artifact has no
collecting zero-layout baseline for subtracting its instruction cleanup.
Consequently +0.4876% is not a complete full-stage instruction comparison.
Even including the additional destruction, instruction growth is much smaller
than the native +3.31%. Memory/allocator latency, locality, branch behavior
and native cycles per instruction must account for the remaining timing
explanation, or a matched zero-subtracted native counter experiment must
show a scope difference. Instructions alone do not predict that timing ratio.

For the sampled two updates, instructions decline; they cannot explain the
original +9.08% by increased executed work. That does not contradict RESULTS:
the profile samples two small updates whereas RESULTS summarizes all 20.
Moreover, the `U` timing encloses marking and font-pick work as well as
`wf_layout.update`: `C:renderer/oracle/layout/edit.wf:1246–1259,1445–1478`.
The profile isolates only `update`, so even matching ordinals would not yet
match the entire timed interval. Profile both the enclosing interval and its
components. Profile the original full-script ordinals, especially updates
that do most work, with identical preceding edit state, before extrapolating. If those matched
updates also shed instructions while taking longer, collect native cycles,
cache/TLB and branch observations to distinguish latency from instruction
count. This artifact supplies none of those counters.

### Function accounting, with mixed mechanisms kept explicit

[INSTRUCTION-DELTAS.csv](INSTRUCTION-DELTAS.csv) is a derived, exclusive
self-cost table for every function with changed cost or call count in the
selected intervals (171 rows, pilot round 0; round 1 repeats the same values).
It includes exact base/candidate costs, calls and conservative hypothesis
correspondence. It is not a copy of the raw artifact. Each phase's rows sum
to the phase delta above. Unchanged functions are omitted. Anonymous address
symbols stay unresolved; their addresses cannot identify equivalent cleanup
routines between binaries.

**Construction:** the following disjoint locations sum to +52,100,142 Ir.
Percentages use the net construction delta; negative savings mean positive
locations can sum to more than 100%. These are locations of changed work,
not an experimentally isolated causal split.

| Exclusive self-cost location | Delta Ir | Net-delta share | Hypothesis correspondence |
| --- | ---: | ---: | --- |
| Allocator and heap-accounting family | +43,136,741 | 82.796% | H3, added cells/pages and allocator consequences |
| `finish_sequence` | +9,602,726 | 18.431% | H3/H4 allocation setup and append initialization, inseparable here |
| `bulk_nodes` | +849,744 | 1.631% | H1/H2 paged addressing / optimization facts, inseparable here |
| `new_block` + `new_context` | +740,040 | 1.420% | H3 eager empty-owner setup |
| All remaining locations | −2,229,109 | −4.279% | Other, including copy/cleanup improvements |

The allocator family's largest self deltas are `_int_malloc` +17,566,924,
`malloc` +11,017,008, `_int_free` +4,828,117, `free` +3,458,364,
`wf__heap_take` +2,274,048, `wf__heap_change` +1,947,260 and
`wf__heap_give` +975,436. Its remaining names and deltas are in the derived
CSV. Route-helper renames cancel exactly: `slot_read/write` become
`route_slot_read/write`, respectively 97,642,107 and 73,543,156 instructions
with identical calls. Counting those renames as added lookup work is wrong.

**Two updates:** disjoint locations sum to −576,436 Ir.

| Function family | Delta Ir | Correspondence |
| --- | ---: | --- |
| `sequence_select` + `nested_event` | −309,802 | H1/H2/inlining; selection is inlined into the candidate caller |
| `slot_read` + `reference_child_event` | −214,596 | H1/inlining; disappearing helper cost is not abolished access |
| `slot_view` + `owner_view` | −34,308 | H1/inlining |
| `owner_store_actions` | −7,198 | H1/inlining into callers |
| `store_reduction` + `publish_boundaries` | −26 | H1/H2/inlining |
| Allocator/heap family | +1,540 | H3/allocator state unresolved; allocation counts unchanged |
| Remaining functions | −12,046 | Other/mixed |

**Preparation + layout:** disjoint locations sum to −4,267,058 Ir.

| Function family | Delta Ir | Correspondence |
| --- | ---: | --- |
| `store_reduction` + `publish_boundaries` | +505,582 | H1/H2/inlining; normalize the +7,206,351/−6,700,769 symbol transfer |
| `slot_read` | −4,402,629 | H1/inlining; some cost moves into callers |
| `reduce_sequence` | −1,387,500 | H1/H2/consumer optimization, not isolated |
| `fill_flow` | −554,511 | Other/mixed consumer change |
| Allocator/heap family | +2,322,623 | H3/allocator state unresolved; allocation counts unchanged |
| Remaining functions | −750,623 | Other/mixed |

There is **no defensible separate percentage for H1 versus H2**, or H3
versus H4 in `finish_sequence`, from these self costs. Each changed function
contains multiple mechanisms, and optimization moves work across names.
H5 has no established positive contribution: construction allocates its final
capacity, and its extra allocations reconcile without any growth copies.
This is not a measurement proving all growth paths cost zero.

One H2 contribution can be counted directly: candidate publication executes
its redundant between-copy directory reload **93,888 times** in preparation
plus layout (12,587 root + 81,301 owner publications), and **twice** across
the two updates. Raw evidence: candidate layout part `.4:4825–4858`, paired
copy-site counts; candidate disassembly `209027–209036` and `209158–209167`,
reloads at `c457a` and `c47a9`. Update parts `.2:3412–3424` and `.4:5370–5382`
show one paired publication per update. These are 93,888 extra reload
instructions, 0.001072% of that candidate phase's Ir, not H2's total cost or
a wall-time bound. Other scalar-write reloads remain unquantified. This
identified edge plainly cannot explain the +9% update regression by its
instruction count; the compiler gap still needs closing.

### Allocation attribution and the decision

Construction's extra `wf__heap_take` calls reconcile completely:

| Caller edge | Base | Candidate | Added takes |
| --- | ---: | ---: | ---: |
| `new_block` | 0 | 68,604 | 68,604 |
| `new_context` | 234,991 | 255,425 | 20,434 |
| `finish_sequence` | 88,676 | 189,142 | 100,466 |
| All callers | 1,417,688 | 1,607,192 | 189,504 |

Two eager empty stores per 34,302 blocks and 10,217 contexts add **89,038
cell allocations** (46.985% of extra takes). Sealing adds **100,466 native
page allocations** (53.015%); node pages hold four nodes. Those shares count
allocation operations, not bytes, allocator instructions or time.
During sealing, frees rise by 88,676: the initial two empty cells for each
nonempty owner are discarded. At termination, extra frees are exactly
100,828 = 100,466 pages + 362 retained empty cells. The latter equals
89,038 initial empty cells minus 88,676 already freed at sealing. These
counts verify H3 much more directly than a function-cost percentage does.

The final dump's +24,796,160 Ir comprises allocator/heap +23,245,005,
generated cleanup +1,551,144 and driver +11. The generated routines must be
grouped across anonymous addresses. This broad termination region contains
font/document cleanup as well as layout release; it supports additional H3
release work, not a clean native time attribution.

**Conclusion: both at the mechanism level, not a quantified split of the
native regression.** (a) Whitefoot fails to preserve directory invariance
across element writes; this gap is verified and must be filed independently
of its small counted publication edge. (b) Snowghost eagerly constructs empty
stores and initializes its entire reserved logical span; these source policies
create avoidable construction work within ordinary Paged use. H3's physical
four-node-page policy belongs to Whitefoot, rather than being fixable by a
syntax change. The allocation-operation shares and exclusive function shares
above are the shares this artifact establishes. H1/H2/H3/H4 native time shares
and a full-script update instruction attribution remain unidentified.

Intended-language comparisons to evaluate, not delivered fixes:

- **Lazy owner-local presence**, `Option<Box<Paged<T>>>`, can remove the
  89,038 initial cell allocations, 88,676 sealing frees and 362 final frees.
  Construct final storage when that owner acquires elements. It adds an
  owner-local presence branch, no shared pool/counter, no dependency between
  independent owners. It changes representation and writer/proof interfaces;
  preserve the Context inverse and validate absent-owner behavior. This
  addresses eager Snowghost ownership, not the confirmed directory reload or
  small-page policy. Keep that gap visible in every nonempty store.
- **Initialize the live prefix** `count`, retaining capacity `page_width`,
  instead of appending missing elements through the reserved span. This can
  remove padding appends (H4), but not pages reserved by eager capacity (H3).
  Current `slot_write` already initializes future prefixes
  (`C:sequence.wf:452–470`). It retains owner-local append order required by
  stable identities and adds no cross-owner dependency. Prove absent-slot,
  tombstone and future-growth behavior before claiming the spelling fixes it;
  do not use it to conceal an inefficient lowering of natural append loops.
- **Compact/empty physical storage** requires a Whitefoot Paged policy
  decision and semantic tests for B/page extents and nonmoving growth. Do not
  restore a hand-written table or share a context-wide owner pool to hide it.
- **H5 reserve/growth changes** are not justified by this profile. A later
  comparison must show growth inside affected work and retain amortized cost
  and stable slot identities; no global serial growth coordinator is needed.

The directory witness is [element-directory.wf](element-directory.wf), kept
with this investigation until the gap is resolved. It is a semantic library
witness, not a claimed compiled reproducer. CI acceptance must (1) check it
with the pinned compiler, (2) initialize at least two pages and verify two
field writes at boundary/interior positions preserve all other values and
len/cap, and (3) retain an optimized `touch` body and require one page-entry
load for the same slot, not a reload between field stores. Inspect disassembly
rather than conservative `--emit-llvm` output; ensure the witness function is
retained instead of optimized away. Also test distinct Run subranges sharing
a directory so the fix cannot use unsound blanket directory `noalias`.
The separate growth-inverse witness and acceptance remain below. Bulk-fill
and compact-page gaps remain candidates, not demonstrated compiler defects.

The next attribution run must cover the original full-script font-size
ordinals in bounded batches, prioritizing updates that do most work and
retaining each ordinal's preceding edit state.
Keep the twin/interleaving controls for native timing; collect matched native
cycles/instructions and supported L1/LLC/dTLB/branch events, with a collecting
zero-layout baseline and release included. Isolate a same-source Whitefoot
metadata fix, then each owner-presence/live-prefix policy separately. Only
those comparisons can assign causal shares of the original regression.

## Ranked hypotheses and separating observations

The order prioritizes explaining the font-size rejection. No additive
percentage shares can be inferred yet; these causes interact.

| Rank | Hypothesis and plausible scope | Observation that separates it |
| --- | --- | --- |
| 1 | Extra dependent directory load and shift/mask in the now-paged owner leaf. Latency/locality can explain full and allocation-light replay; instruction-count dominance is weakened by the optimized hot read paths having fewer instructions. Dense publication adds 15 caller instructions/live slot, but is sparse in the retained base pilot. Evidence: base leaf `B:sequence.wf:185–189`, candidate `C:sequence.wf:182–185`, `W:paged.rs:43–63`, publisher comparison above. | Update-only excess instructions/cycles concentrate in `slot_cursor/output/view/geometry`, `reduce_sequence`, `store_reduction`, or their inlined callers, with comparable call/update counts and little allocator activity. Reject as dominant if those paths contribute little absolute excess. |
| 2 | LLVM cannot retain header/directory/element separation across writes; repeated loads, guards or scalarized stores amplify the basic address cost. The directory-entry subcause is verified in run 38139461660; broader header reloads and its time share remain open. Evidence: `W:paged.rs:62`, `W:runs.rs:652–687`, `W:emitter.rs:1751–1778`; base/candidate publisher and bulk-node paths above. | Optimized disassembly has post-store header/page-pointer reloads or lost loop optimization absent from base; a minimal same-source compiler fix removes them and the isolated instruction excess without changing page geometry or algorithm. Reject this subcause where optimized loads are already commoned/hoisted. |
| 3 | Fixed physical geometry, extra empty cells and many more allocations expand resident working set and allocator/free work. Strong for full construction and RSS; for replay only residency or actual timed construction can matter. Evidence: `B:sequence.wf:165–172,322–340`, `C:sequence.wf:165–172,307–324`, `W:paged.rs:143–167,270–315`. | Build/release call edges and allocation counts increase as predicted; retained update instruction counts stay close but cycles/load stalls/cache or dTLB misses increase. Separately count owner-size distribution and requested bytes. Reject startup allocator activity as explanation of an isolated update excess. |
| 4 | Serial append initialization and power-of-two logical reservation add avoidable source work or expose a missing bulk-fill lowering. Strong for sealing/reconstruction; weak for a retained style edit unless constructors appear inside update. Evidence: `B:sequence.wf:322–334`, `C:sequence.wf:305–319,452–460`, `W:buffer.rs:281–309`, `W:runs.rs:451–495`. | `paged_fill/finish_sequence` dominate build excess, per-slot length loads/stores survive optimization, and the same functions appear in update if claimed there. Reject for the edit if its timed call graph contains no sealing/fill. A live-length-only diagnostic must preserve identities/output and run the full checks before it is called a usage fix. |
| 5 | Eager reserve through doubled capacity and directory copying on growth. Valid construction/splice concern, probably small for this font-size path. Evidence: `B:sequence.wf:401–424,495–539`, `C:sequence.wf:384–398,463–473`, `W:paged.rs:193–233`. | Count growth calls, old/new page counts, pointer-copy bytes and newly allocated pages **inside** update. Zero calls reject it for that stage. Copies proportional to payload bytes would contradict the inspected lowering and require investigation; only directory-word copying is predicted. |

## Instruction profile and subsequent acceptance plan

The temporary [workflow](../../../.github/workflows/paged-mechanism.yml) and
its wired script collect evidence, not a pass/fail performance verdict. Remove
them when this mechanism round ends. The completed instruction experiment is available through the `instructions`
dispatch choice; its full profiling remains explicit. Pushes now select the
memory experiment below, and a path filter excludes documentation-only pushes. The
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

Use Callgrind instruction counts and call edges. Positive runs collect from
startup, with before/after dumps isolating each `wf_layout.update` for
font-size edits; zero-work controls start with collection disabled and toggle
at the selected markers, and must collect zero. A positive sample must collect
nonzero. For full-layout runs retain every startup and teardown dump. The
frozen binary's layout driver inlines `prepare_text` and calls
`prepare_context` directly, so the workflow uses four boundaries per
repetition: before box construction, after box construction, after font
picks, and after layout. Their three measured intervals are box construction,
font picks with caller bookkeeping, and text preparation plus layout with
caller bookkeeping. The last interval is not an isolated layout kernel.
The script verifies this exact trigger sequence and the named functions in
each interval; missing or extra boundaries fail. Full update dumps separate
each ordinal from setup/style; `finish_style_edit` is broader than update.
Callgrind instruction counts are not native time, cache stalls or four-worker
scheduling evidence. Inspect self cost and call edges, not summed overlapping
inclusive percentages.

Run 38141932250 verified the corrected instruction boundaries and matched
base/candidate pilot profiles. The next hosted memory experiment below owns
cache simulation, the effective optional perf input, and allocation evidence.
Complete-script instruction updates and same-source intervention comparisons
remain unverified. The additional sampling commands below describe possible
follow-up, not features delivered by the instruction profiler.

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
filed requests. The first gap has optimized renderer evidence from run 38139461660; its
minimal witness still needs compilation and optimization acceptance in CI.
Only the growth-inverse witness already has a hosted refusal.

1. **Directory/element separation missing from optimization (verified in renderer).** A
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
   File the verified gap with the minimal witness and instruction/assembly
   acceptance test; use the matched renderer profile to determine its time
   share. The witness is not yet compiled. Do not use a Snowghost local-pointer
   workaround to hide it.

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


## Hosted memory experiment: prior criterion, before results

This plan was written after instruction run
[38141932250](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38141932250)
and before any result from the new memory job. It tests explanations of the
native +3.3% full-layout and +9.1% font-size regressions; it does not convert
instruction, miss or allocation percentages directly into time shares.
The [workflow](../../../.github/workflows/paged-mechanism.yml) uses only
`ubuntu-24.04` hosted runners, defaults to this experiment on relevant pushes,
and skips documentation-only pushes. Its `memory` dispatch accepts an optional
original C/K pair override and a perf boolean. Frozen drivers, sheets, fonts,
script and one-worker invocation are reused without renderer changes.

### Selection and matched state

The instruction pilot's first two edits are insufficient for the original
20-edit timing statistic. CI downloads the original ecma262/seq matrix artifact
from [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274),
validates all 20 ordinals in each of three baseline rounds, and selects the
forward/inverse pair with the largest median summed baseline **U**. Ties favor
the earlier pair. This selects two ordinals using old evidence before measuring
new memory behavior, rather than choosing whichever new result looks worst.
`selection.json` records the chosen ordinal numbers, node operations, all pair
scores, source/script hashes and coverage of the original U total. An override
is identified explicitly and carries the same ranking for comparison.

The original complete script hash is
`4def8240288a01f51276e2f68d5c2ae2e135721ac03952ad8e8d2533fbd324bb`.
The possible pairs are 1–2 (node 303118), 3–4 (343539), 5–6 (217190), 7–8
(414119), 9–10 (288562), 11–12 (224717), 13–14 (79145), 15–16 (147937),
17–18 (221537), and 19–20 (217945). Their identities are verified from the
matching script. At plan-writing time their timing rank was **not verified locally**: the
retained matrix ZIP could not be extracted through the available network tools.
The workflow resolves and records the choice before profiling; the first memory
run below now verifies that selection. Thus no specific
pair is falsely declared dominant in this pre-run account. If it contributes
little to the full-script total, this bounded experiment has limited coverage.

Replay every original operation through the selected inverse ordinal. Do not
repeat a pair or skip earlier edits. Simulate caches from process startup,
including initial layout and the preceding edit prefix; dumps reset counters
without flushing the simulated caches. Native runs retain the driver's exact
U timestamps and work counts. Zero-repetition stage baselines must report zero
contexts and paragraphs; CI rejection fixtures exercise both boxes and layout. They use three interleaved rounds and independently
built twins as noise controls. New native results are observations on another
hosted runner, not a replacement for the original acceptance table.

### Cache scopes, model and evidence

The [memory script](memory-mechanism.py) sets I1 and D1 to 32 KiB, eight ways,
64-byte lines, and LL to 32 MiB, sixteen ways, 64-byte lines. This is an explicit,
fixed comparison model, **not** a claim about the hosted CPU's cache hierarchy.
Requested and observed geometry, machine details and Valgrind version are
retained; unexpected geometry is rejected. Callgrind cache and branch simulation
records Ir, data reads/writes, D1 and LL read/write misses, instruction-cache
misses and branch events by exclusive function cost. Every dump reconciles its
exclusive totals for every event. Inclusive call-edge costs are not added to
self costs. Paired phase/function outputs record candidate minus base deltas,
including combined D1 and LL data misses. Zero-work and synthetic rejection
controls detect nonzero control collection, missing events, bad totals and
missing self rows. Ordered nonzero phase boundaries remain required.

Full-layout boundaries retain box construction, font picks, and text preparation
plus layout separately. The corrected font-size boundaries are before/after
`wf_layout.styles_restyled`, after `wf_layout.text.extend_picks`, and after
`wf_layout.update`. The three disjoint parts contain marking, font picks with
intervening caller bookkeeping, and update with clock/caller bookkeeping; their
sum is the substantive original U interval. The first memory-run diagnosis below
explains why the earlier before-update option was replaced. This fixes the
previous update-only scope. Frozen native code inlines the timestamp wrappers,
so markers omit the small edge clock/argument bookkeeping. Preserve that
qualification: only native stdout is the exact U timestamp interval
(`renderer/oracle/layout/edit.wf:1246–1259,1445–1478`). Nonselected prefix dumps
are retained as state/warmth evidence, but excluded from selected-pair totals.

Two first-pair cache pilots establish startup cost/spread before the larger
prefix. Every cache or DHAT process has a hard **900-second** cap; this is a
per-process bound, not a promise of a 900-second total job. Startup dominates
the small pilot, so its duration is not multiplied by isolated U ratios to
predict the prefix. A capped process is unavailable, never a complete partial
profile or a zero result; its command, duration, exit/timeout and stderr survive.
This experiment prioritizes one costly pair rather than an unbounded complete
20-edit profile. The workflow job budget accommodates the bounded batch.

### Native counters and allocations

With `perf=true` (the push default), probe the installed perf wrapper and actual
`/usr/lib/linux-tools/*/perf` binaries. Attempt whole-process
`cycles,instructions,cache-misses,dTLB-load-misses,page-faults` for the same
frozen workloads, and independently attempt software page faults. An absent
executable, PMU denial, unsupported event, missing/non-numeric counter or failed
process is recorded as unavailable or partial, with raw counters and stderr;
this optional observation does not make CI fail. Numeric counts from a failed
process are not usable cohort comparisons. Whole-process stat includes parsing,
style, startup, the preceding edits and cleanup. It cannot assign selected-U
cycles or TLB misses by function. Box-only native runs help locate a construction
excess, but overlapping whole-process measurements cannot be summed as disjoint
phase costs. No hosted PMU availability is assumed.

Two small first-pair DHAT pilots record duration and spread before whole-prefix
base/candidate passes. The
[allocation reader](allocation-summary.py) records total successful allocation
events/requested bytes, maximum simultaneous live requested bytes and the block
count **at that byte-peak instant**, plus live exit allocations. It reconciles
all six totals with DHAT stderr and partitions original allocation stacks into
Whitefoot heap origins and other/unresolved origins. Individual allocation-site
maxima are not added: they occur at different times. Independent maximum live
block count is unavailable from these totals. Realloc contributes a new event
and its new requested extent, while retaining its original allocation stack;
zero-size requests use DHAT's one-byte normalization. This is intercepted heap
accounting, not RSS: it excludes mmap-only memory, stack, allocator slack and
profiler memory. It includes startup and every preceding edit and cannot assign
allocation bytes to U without phase instrumentation. Definitions follow the
[DHAT manual](https://valgrind.org/docs/manual/dh-manual.html).

Existing run 3 already verifies +189,504 construction heap takes (89,038 eager
empty-owner cells and 100,466 extra pages) and +100,828 release heap gives.
DHAT adds requested bytes and simultaneous liveness; it does not by itself
measure allocator latency. Cache self costs in allocator functions versus layout
consumers provide the independent separation available in this observation.

### Predictions to assess before assigning causes

Apply these criteria only to completed, matched-count cohort pairs. First check
whether selected native U reproduces an excess beyond its twin/interleaving
spread. If it does not, this runner/pair cannot settle the original +9.1%.
Report selected coverage before extrapolating to the 20-edit average. Thresholds
below are predeclared screening criteria for follow-up, not calibrated cycle
models or statistical proof.

1. **Locality/miss growth supports the time explanation** if candidate selected
   substantive U has at least 10% more D1 or LL data misses while instructions
   are flat or lower, and at least half of the gross positive self-miss delta
   occurs in layout consumers/publication/lookup callers rather than allocator
   functions. Full construction/layout is assessed separately. A compatible
   native rise in cache/TLB misses with cycles strengthens this explanation.
   This would identify H1/H2 or H3's retained geometry as memory-latency
   candidates despite instruction savings; it would not apportion their shares
   without a same-source metadata/geometry intervention. Inspect signed net
   deltas as well as gross positive deltas so migrations/inlining do not turn
   a net saving into a claimed regression.

2. **Allocation latency supports the full-layout explanation** if DHAT confirms
   increased events/bytes/liveness, native box construction carries the excess,
   and allocator functions account for at least half of gross positive
   construction data-miss delta while nonallocator preparation/layout shows
   less than 10% miss growth. Existing extra allocator instructions support this
   direction. Startup allocation latency alone cannot explain an isolated U
   excess; it can affect U only through retained working set, actual allocations
   inside U, or scope mismatch. The selected U call graph must show allocation
   activity before calling it an update allocation explanation. Counts alone
   are insufficient: sampled allocator cycles or a same-source allocation-policy
   comparison would still be needed to establish latency and a causal share.

3. **Neither observed mechanism accounts for the matched excess** if native U
   reproduces the slowdown, both D1 and LL data-miss growth are below 10%, and
   U has negligible extra allocator work, or full-layout excess is confined
   outside the observed construction/layout scopes. This rejects a large
   miss-growth explanation in this fixed model, not native memory behavior in
   general. Callgrind does not model dTLB, hardware prefetch, bandwidth, dependent-load
   latency for cache hits, or out-of-order overlap. Flat simulated misses with unavailable PMU therefore
   leave those causes **unverified**, rather than proving memory innocent.
   A failed/capped pass or unavailable native counters is inconclusive, never
   evidence for either mechanism. Further native phase sampling or same-source
   interventions are required if these observations do not discriminate.

No renderer data dependencies change in this experiment. Sequential replay is
forced by the original edit script's document-state dependencies; profiler
counters and serial CI orchestration are external measurement, not a shared
renderer table or a proposed serialization. The Whitefoot directory-separation
gap remains established independently of this new, as-yet-unverified memory
attribution. No workaround, pin change, request filing or approval-log edit is
part of this round.


## First hosted memory run: native result and boundary diagnosis

Evidence: [CI run 38147376573](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38147376573),
workflow revision `16970b3436c2db9aba1a8c7e8e78af480169805f`, uploaded
`paged-memory` artifact. All filenames below are relative to its extracted
`paged-memory/` directory; the artifact is not copied into this repository.
The hosted machine was Ubuntu 24.04.5 on an AMD EPYC 7763 VM with four vCPUs;
all drivers used `WF_WORKERS=1` (`machine.txt`, `metadata.json`). Frozen driver
and input checks passed. No new performance measurement ran locally.

### Why the pilot had six numbered parts

`processes.jsonl` records cache-pilot-0 exiting zero after 393.656 seconds,
without timeout. Its two original edits completed with matching counts.
These six numbered files exist, each with its trigger at line 14:

| Dump suffix | Trigger | Interval ending here |
| --- | --- | --- |
| `.1` | before `wf_layout.styles_restyled` | Initial state/style work |
| `.2` | after `wf_layout.styles_restyled` | Edit 1 marking |
| `.3` | after `wf_layout.update` | Edit 1 picks **and** update |
| `.4` | before `wf_layout.styles_restyled` | Between-edit/style work |
| `.5` | after `wf_layout.styles_restyled` | Edit 2 marking |
| `.6` | after `wf_layout.update` | Edit 2 picks **and** update |

The unsuffixed `cache-pilot-0.callgrind` is the termination residual, not a
seventh numbered boundary. Neither before-update trigger exists. This is not
an inlining failure: `.3:1396,2471` names `wf_layout.text.extend_picks` and
`wf_layout.update`; its whole interval includes both functions.
Geometry headers at lines 9–11 confirm the requested I1/D1/LL model, and line
17 declares all 13 cache/branch events. Cache-zero passed before this pilot.
These are real profiler compatibility observations, not paired miss evidence.

The cause is the Valgrind 3.22.0 function-option trie, verified in its release
source ([release-tag provenance](https://chromium.googlesource.com/external/sourceware.org/git/valgrind/+/refs/tags/upstream/VALGRIND_3_22_0)).
The before/after styles flags combine on the initial full-name node. Adding
before-update splits their common prefix. Registering after-update then
allocates and prepends a **new** update suffix instead of descending into its
existing node (`get_fnc2`,
[clo.c:239–268](https://github.com/tomhughes/valgrind/blob/bd4db67b1d386c352040b1d8fab82f5f3340fc59/callgrind/clo.c#L239)).
The matcher follows the first matching child
([clo.c:368–376](https://github.com/tomhughes/valgrind/blob/bd4db67b1d386c352040b1d8fab82f5f3340fc59/callgrind/clo.c#L368)),
so the new after-only node shadows the before flag. This also explains why
the earlier update-only instruction profile's paired flags worked: its update
node was the first function configuration. This is a profiler option defect,
not evidence of a Whitefoot gap.

The script replaces before-update with **after `wf_layout.text.extend_picks`**.
Styles' paired options remain first; each later function is registered once.
There are still four required triggers per edit, not acceptance of six out of
eight. The three intervals remain marking, picks with caller bookkeeping,
and `update_and_bookkeeping`; the last includes `stamp_picks` between picks
and update (`renderer/oracle/layout/edit.wf:1448–1465`). Their sum has the same
before-marking/after-update endpoints as the prior substantive U criterion.
Full-layout boundaries and their scope are unchanged.

`boundary_parts` requires the exact numbered filename set and exact ordered
singleton trigger in every file. CI controls exercise a valid two-edit
sequence and rejection of a deleted part, extra part and swapped triggers.
Required component symbols, nonzero Ir, cache geometry and exclusive event
conservation checks remain in place. Source inspection and read-only review
verify this wiring; the corrected flags and new controls still await CI.

### Completed native U meets the prior prerequisite

`selection.json` chose **7–8**, `C 414119 x5f` / `K 414119 x5f`, without override.
Its original baseline pair median was 238,116 microseconds, larger than pairs
11–12 (236,577) and 13–14 (212,047). It covers **34.4131%** of summed original
pair medians (691,934 microseconds); actual per-round coverage was
34.6913%, 34.3889%, 34.4604%. Every new selected-prefix run replayed ordinals
1–8. This is substantial coverage, not the complete 20-edit acceptance metric.

`native-samples.jsonl`, the twelve `native-round-*-edittime-selected.raw`
files and corresponding `.timed.json` files agree on original U timestamps:

| Round | Base pair U, µs | Base twin | Candidate | Candidate twin | Candidate/base |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 237,838 | 235,921 | 260,289 | 260,490 | 1.094396 |
| 2 | 242,014 | 237,564 | 263,789 | 260,985 | 1.089974 |
| 3 | 238,453 | 237,345 | 263,098 | 260,425 | 1.103354 |

The **median paired ratio is +9.4396%**. Maximum absolute twin/original
pair-U deviation is 1.8387%, so the 2% floor controls; every round's excess
(9.4396%, 8.9974%, 10.3354%) exceeds it. Independently built twins also show
candidate/base excesses in every round. The native matched-U prerequisite of
the prior criterion is therefore **verified for this pair**. Counts match
across all twelve runs: each selected ordinal reports 3 prepared, 5 contexts,
3 paragraphs. Initial hashes/byte counts also match. This removes the old
update-only scope mismatch for the native observation; it does not establish
which memory mechanism caused the excess or its share of all 20 edits.
Across all 24 selected-ordinal style records, marking is 9–16 microseconds
and font picks round to zero microseconds. These reported components cannot
account for the tens of milliseconds of pair excess; the residual update
interval (including clock/caller bookkeeping) carries it. This narrows the
scope concern for this costly pair without substituting for its cache profile.

The separate-process stage subtraction is weaker (`native-stage-differences.json`):

| Stage, T(1)−T(0) | Median paired candidate/base excess | Maximum twin deviation | Assessment |
| --- | ---: | ---: | --- |
| Box construction | +16.7034% | 28.6050% | Inconclusive |
| Full layout including boxes | +3.7891% | 3.8095% | Inconclusive |

Only one round of each stage exceeds its corresponding global noise band.
Zero-process subtraction includes startup noise; it does not establish a new
precise construction or full-layout regression on this runner. All zero-stage
counts are zero contexts/paragraphs, while full-stage counts match across
cohorts. Do not use these noisy stage values to confirm allocation latency.

### Memory attribution remains inconclusive

The artifact records exactly 66 completed processes: four native pilots, sixty
native production runs, cache-zero and cache-pilot-0. It contains **no perf or
DHAT measurement**: both occur later in `main`, after the second cache pilot
and production cache passes. `allocation-controls/fixture.dhat.json` is
synthetic reader-control input, not allocation evidence. No new allocation
totals, byte peaks, native counters or paired cache-function deltas can be
reported from this run; missing observations are unavailable, not zero.

Thus the prior criterion's native-U prerequisite passes, but its locality,
allocation-latency and neither-mechanism branches are all **inconclusive**.
The single base pilot describes only ordinals 1–2 and has no candidate twin
cache profile; it cannot test the selected-pair 10% miss-growth criterion.
Existing run 3 allocation-count evidence and the established Whitefoot
metadata gap stand unchanged. The next run must complete the corrected pilots,
selected-pair cache comparison and allocation/counter passes before assigning
memory causes. The 900-second per-process cap remains unchanged.


## Second memory run: footer reconciliation and file-only replay

Evidence: [CI run 38149516009](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38149516009),
revision `7bff6eb`, uploaded `paged-memory` artifact. The new marker sequence
worked: eight numbered pilot parts have the four expected triggers for each
of two edits. The next failure was in the file parser, before the second cache
pilot or any production cache, perf or DHAT measurement.

The parser treated `summary:` as the body conservation total and ignored
`totals:`. In `cache-pilot-0.callgrind.1`, exclusive rows match the footer
exactly; the header differs:

| Event | Exclusive sum = `totals:` | `summary:` | Summary minus totals |
| --- | ---: | ---: | ---: |
| Ir | 24,641,250,531 | 24,641,250,537 | +6 |
| Dr | 6,259,837,281 | 6,259,837,284 | +3 |
| Dw | 3,932,194,501 | 3,932,194,501 | 0 |
| I1mr | 52,118,324 | 52,118,324 | 0 |
| D1mr | 64,427,830 | 64,427,830 | 0 |
| D1mw | 31,410,857 | 31,410,857 | 0 |
| ILmr | 24,859 | 24,859 | 0 |
| DLmr | 21,331,406 | 21,331,406 | 0 |
| DLmw | 21,265,765 | 21,265,765 | 0 |
| Bc | 3,303,830,411 | 3,303,830,411 | 0 |
| Bcm | 130,320,804 | 130,320,804 | 0 |
| Bi | 93,566,119 | 93,566,119 | 0 |
| Bim | 17,099,689 | 17,099,689 | 0 |

The [Callgrind format specification](https://valgrind.org/docs/manual/cl-format.html#cl-format.reference.header)
assigns `totals:` to the consistency check; the reported summary need not be
the sum of represented self costs. This is distinct from row compression:
position columns are discarded according to `positions:`, repeated/relative
positions still contribute their cost vectors, omitted trailing counters are
zero, and a cost row following `calls=` belongs exclusively to the call edge.
These rules already produced exact body/footer sums in the failed dump.
The footer was the missing parsed field. Position-only rows now also represent
all-zero costs, as the format permits.

`cache_profile` now requires one footer and checks every exclusive event
**exactly** against it. It returns footer totals for function/phase arithmetic,
while `cache-header-audits.jsonl` retains each summary, footer and signed delta.
No tolerance, fabricated self cost, or dropped conservation event was added.
Missing/duplicate footer and incomplete call associations are rejected.
CI controls include distinct/lower summaries, omitted zero costs, and corrupted
footer/body cases. The exact Valgrind-internal origin of the small header
differences remains unverified; it is unnecessary for the documented reader
contract. In particular the termination summary's Dr is lower than its footer,
so no summary-greater-than-footer assertion is introduced.

The authorized local `python3 -I` replay parsed all ten real dumps: cache-zero,
the pilot residual, and parts `.1` through `.8`. For **all 130 event comparisons**,
exclusive body sums equal footer totals exactly. Summary-minus-footer differences
are `.1` Ir +6 and Dr +3, and the unnumbered residual Ir +1, Dr −3, I1mr +1,
ILmr +1; all other entries are zero. Each geometry header also matches the
fixed model. A scratch copy of `.1` with its first self-cost Ir incremented by
one (source line 24) was rejected by the exact footer conservation check.
Original artifact files were not modified.

File-only replay coverage of the later analysis is recorded below. Fixtures
for unobserved producer outputs are reader checks, never performance evidence;
no Valgrind, renderer, compiler or other child process is invoked by the replay.


| File-only check | Retained evidence or fixture | Result |
| --- | --- | --- |
| Native protocol, zero-stage and work-count parity | All 64 retained native stdout files | Pass |
| Ordered cache boundaries | Eight retained pilot parts | Pass |
| Cache geometry and exclusive footer conservation | All ten retained dumps, all 13 events | Pass |
| Phase components and substantive U sum | Replay the completed pilot and zero-control records; no process is executed | Pass |
| Nonselected-prefix filtering | Same real pilot, selecting ordinal 2 after validating every part | Pass |
| Missing/extra/misordered boundaries, bad totals, missing/duplicate footer, distinct/lower summary and native zero-work rejection | 27 built-in reader controls, allocation reader controls and altered scratch copies | Pass; invalid copies rejected |
| Position compression and inclusive call-edge exclusion | Synthetic two-position absolute/relative/repeated positions, omitted zeros and a child call | Pass; self 7+5=12, inclusive edge 5 excluded |
| Normalization and paired phase/function deltas | Synthetic completed layout and selected-pair rows, plus incomplete pairs | Pass; all 11 complete cells conserve; missing selected cells remain unavailable |
| Perf reader and availability bookkeeping | Synthetic numeric, unsupported, absent and duplicate counters; process-return fixtures | Pass; unavailable/partial and duplicate cases handled |
| Allocation reader, common-instant peak and paired deltas | Synthetic heap profiles with printed totals; missing/single/completed cohorts and process-return fixtures | Pass; all 18 completed delta rows produced |

The one-use isolated checker ran under `python3 -I` and exited zero with
34 recorded check groups, ten archived dumps, 64 native outputs and zero
unexpected child processes. Its audit hook rejected process spawning;
subprocess APIs and the default driver runner raised immediately. Scoped replay
stubs returned retained records or explicitly synthetic records, and `main`
was never called. All analysis output and altered copies lived in scratch space.
This exercises every later file-analysis function, including `cache_run`,
`cache_deltas`, `perf_run`, `dhat`, and `allocation_deltas`, without running their
external producers. Runtime markers and producer performance are CI evidence,
not results inferred from the fixtures.

The early frozen binary/font inventory and original full matrix selection were
not rerun locally: their files are outside this artifact, and CI had already
passed those checks. Production base/candidate layout, selected-pair cache,
perf and DHAT outputs still do not exist in this failed run. Accordingly this
validation fixes and checks the reader pipeline; it provides **no new causal
memory attribution** or allocation/counter measurements. The prior criterion
and the previous native selected-pair conclusion remain unchanged.
