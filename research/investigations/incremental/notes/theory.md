# Dependency-determined incremental computation: theory and language mechanisms, mapped onto Whitefoot

Branch of the shared exploration (`context.md`). Scope: the families of
incremental computation, what each would mean for the renderer, and what
Whitefoot as specified today (kernel spec v0.84, `whitefoot/spec/kernel-spec.md`)
gives, withholds, or would need. Not covered here: the paint/display-list
and shell side beyond where reconciliation touches cutoff, and the concrete
layout algorithms.

Evidence labels used below:

- **measured**: a figure from a Snowghost or Whitefoot research record, with
  the record named;
- **spec**: a rule of the kernel specification, with its ID;
- **established**: practice in a named system, with a URL where one was
  fetched today (2026-10-02); **from memory** where no page was fetched;
- **speculation**: my own reasoning, not yet observed.

Status legend: established / promising / uncertain / hard / likely dead end.

---

## 0. The budget, in numbers (frames the whole tree)

**measured** (`research/investigations/layout/DESIGN.md`, Speed, commit
a5fc2de; `research/investigations/concurrency/DESIGN.md`, Shape D run 28):

| html5 | sequential | 4 workers |
|---|---:|---:|
| style stage (shape C, prototype) | 0.597 s | 0.183 s |
| layout stage, whole | 1.390 s | 0.590 s |
| of which text preparation | 0.937 s | 0.357 s |
| of which layout passes | 0.353 s | 0.143 s |
| of which box tree walk | 0.100 s | 0.090 s |

So a full style+layout of html5 is about 0.8 s at four workers, as the
context says. The page has 44,111 block-level boxes, 73,008 inline-level
boxes and 119,707 text nodes (same record, Layout results); ecma262 has
179,471 elements (`research/investigations/style/DESIGN.md`).

A 60 Hz frame is 16.7 ms, about 50 times less than the full recompute. Two
arithmetic facts follow and constrain every family below:

1. **Validation must not scale with the page.** If a frame in which nothing
   changed had to verify every memoized unit, 120,000 units at even 100 ns
   each (one cache-missing load and a compare) is 12 ms, most of the frame.
   At ~10 ns per unit (a sequential scan over a dense version array) it is
   about 1 ms, tolerable. Any scheme whose steady-state cost is "visit every
   node and ask whether it changed" is therefore limited to one scan of a
   dense array, or must be push-based (the write marks what it dirties) so
   that a no-change frame costs nothing. (speculation on the constants;
   arithmetic otherwise)
2. **Dynamic dependency edges are affordable per formatting context or
   paragraph, not per box or text node.** Recording a dependency edge in a
   trace (Adapton, Salsa) costs an allocation or a hash insert, on the order
   of 100 ns to 1 µs each (from memory, order of magnitude). At 10 edges per
   unit and 120,000 units that is 0.1 to 1 s per full build, i.e. the
   bookkeeping would cost as much as the work it saves. At a few thousand
   units it is a few milliseconds and acceptable. The number of formatting
   contexts on the three pages is **not measured**; it is the first number
   experiment E1 should record.

The target the owner states, "a local change stays local", means:
time ∝ |dirty set| × (depth factor), with a constant per-frame floor well
under a millisecond.

---

## 1. Families of incremental computation

Each node: what it is, granularity, how dependencies are found, cutoff,
bookkeeping and memory, parallel fit, what it would mean for the renderer,
and its status for Whitefoot.

### 1.1 Memoization with explicit keys, build-system style (Salsa, Shake, Bazel, Pluto) — promising, in a Whitefoot-specific form

**What it is.** A computation is a set of named functions over a store of
inputs. Each function's result is cached under a key; a result is reused
when its key's inputs have not changed. Build Systems à la Carte
(Mokhov, Mitchell, Peyton Jones; fetched
https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems.pdf)
classifies the design space: static dependencies known before running
(Make) versus dynamic ones discovered while running (Shake, Excel, Pluto);
*early cutoff* ("a build system can avoid recomputing a task if its
dependencies have not changed"); and traces: verifying (record hashes of
what was read), constructive (also keep the results), deep constructive.
Salsa (rust-analyzer's engine; fetched
https://salsa-rs.github.io/salsa/overview.html and
https://salsa-rs.github.io/salsa/reference/algorithm.html) is the dynamic,
constructive-trace design with a revision counter: "each time you set an
input, the revision is incremented"; each input records "the revision in
which it was last changed"; a tracked function re-executes when any input
it read changed in a newer revision; **backdating** is the cutoff: when a
re-executed function "produces identical output, Salsa can backdate the
result, meaning that we say that, even though the inputs changed, the
output didn't"; *durability* classes let a query that read only
rarely-changing inputs validate in one comparison.

**Granularity.** Chosen by the writer: one tracked function call = one
memo entry. Dependencies are discovered **dynamically** in Salsa/Shake/
Pluto (what the function actually read this run), **statically** in Make.

**Cutoff.** Equality of the recomputed result with the old one (backdating).
Requires an equality on results.

**Bookkeeping.** Per memo entry: key, result, list of dependencies with
their revisions, `verified_at`, `changed_at`. Validation is a *pull*: the
demanded root query walks its dependencies ("deep verify") until it finds
one that changed, so a no-change frame still walks the dependency graph
unless durability short-circuits it. Memory: results plus dependency lists
for every entry.

**Parallel fit.** Salsa runs queries on several threads with per-entry
locks and cycle detection, and Shake schedules independent rules in
parallel (both from memory; neither fetched page covers it).
Independence is discovered at run time from the trace, not proved.

**For the renderer.** Queries like `style(element)`,
`layout(context, available_size)`, `lines(paragraph, width, intrusions)`,
`display_list(context)`. This is what `design/pipeline.md`'s third decision
describes in spirit: "each stage ... is a pure Whitefoot function of
explicit inputs whose result is memoized by those inputs".

**Mapping onto Whitefoot.** The decisive difference from Salsa: Whitefoot
already knows the read set statically and completely (§2.1), so dynamic
tracing is unnecessary *for places*; what it does not know is whether the
values at those places changed (§2.2). The Whitefoot-native form of this
family is therefore "static key shape from the row, versions as data"
(§1.8 and §2.3), not a Salsa-like tracing runtime. Status: **promising**,
as the family the other feasible nodes reduce to.

### 1.2 Self-adjusting computation and Adapton — hard as a mechanism; one idea worth keeping

**What it is.** Self-adjusting computation (Acar et al., from memory)
records the whole execution as a trace of reads and writes of modifiable
references; a change to an input re-executes exactly the trace segments
that read it (change propagation), splicing new segments in. Adapton
(Hammer et al., PLDI 2014, from memory for the paper; the Rust crate's
documentation was fetched, https://docs.rs/adapton/latest/adapton/) makes
it demand-driven: a *demanded computation graph* of named cells and thunks;
"the Editor role creates and mutates input, and demands the output of
incremental computations in the Archivist role"; propagation re-evaluates a
thunk only when demanded and when an observation it made no longer matches
("it finds that these earlier observations match the current values.
Consequently, it reuses the output"). Its key idea beyond SAC is **nominal
memoization**: a thunk or cell is allocated under a first-class name chosen
by the program, so that re-running a structural recursion with slightly
different input reuses the old nodes by name instead of by position ("when
pointer name n is independent of pointer content v, we say this name
affords the program nominal independence").

**Granularity.** Every thunk and every cell read: fine, automatic.
Dependencies: fully dynamic. Cutoff: per thunk, by equality of the
re-evaluated result with the cached one (and in Adapton by the "observation
matches" check at each edge).

**Bookkeeping and memory.** The trace or DCG is kept in full between
updates: typically several times the size of the data, with a constant
factor slowdown on from-scratch runs that the literature reports in the
range of about 2 to 10× (from memory; not re-checked today). This is the
family §0's second fact rules out at box granularity.

**Parallel fit.** Parallel SAC exists in research (from memory) but the
trace is a sequential object; it is the opposite of Whitefoot's proved
independence.

**Mapping onto Whitefoot.** Unrepresentable as designed: a DCG is a graph of
thunks pointing at cells, and Whitefoot storage holds no references
([TYPE-8], [STOR-5], spec) and a `Box` has exactly one owner ([TYPE-9]). The
graph would have to be an arena of integer indices with an interpreter over
it, which is the explicit-key family again with a dynamic trace on top.
Status: **hard / likely dead end as a mechanism**.

**The idea to keep: nominal identity.** A formatting context, paragraph or
line that survives an edit must keep its identity (its arena slot) so that
cached results keyed on it survive structural edits around it. In Whitefoot
this is a free-list arena with stable indices and a generation number as
data (§1.8). Without it, inserting one paragraph shifts every later index
and invalidates everything after the insertion point, which is the
positional-reuse failure Adapton's names fix.

### 1.3 Differential and timely dataflow — promising for selector matching as an idea; hard elsewhere

**What it is.** Differential dataflow (McSherry et al.; crate docs fetched,
https://docs.rs/differential-dataflow/latest/differential_dataflow/)
computes over collections (multisets of records) with `map`, `filter`,
`join`, `reduce` and `iterate`; inputs arrive as "update records (triples of
data, time, and change in count)" and "the system will automatically update
the computation's outputs with the appropriate corresponding additions and
removals". Cutoff is inherent: only non-zero differences flow. Operators
keep *arrangements* (indexed traces of their inputs) so a join can respond
to one changed record by probing the other side.

**Granularity.** Per record. Dependencies: static in the dataflow graph,
dynamic in which records a change touches. Memory: arrangements hold the
full indexed inputs of every stateful operator, typically 2 to 3× the data
(from memory). Per-record overhead on the order of hundreds of nanoseconds
(from memory).

**Parallel fit.** Excellent by construction: data-parallel operators,
timely progress tracking; this is its reason to exist.

**For the renderer.** Selector matching *is* a join: elements (with their
id, classes, local name, position among siblings, ancestors) joined with
rule compounds, then an ancestor/sibling combinator check, then a reduce
per element and longhand to pick the winning declaration. Snowghost's
rule index ("matching tests an element only against the rules that its own
id, class words and local name select", `design/pipeline/style.md`) is the
static half of that join's index. A class toggle on one element is then a
one-record update that re-probes only that element's candidate rules, and
a rule insertion re-probes only the elements the rule's rightmost compound
selects. This is how Blink's invalidation sets behave in effect (§3.2).

Layout is not a join: block flow is a fold with a true chain (each box's
position depends on the previous one's size), and `iterate` over a fold
degenerates to re-running the suffix. So the family fits match, cascade
(a per-element reduce) and the inherited pass (a tree-recursive
`iterate`), not layout.

**Mapping onto Whitefoot.** The library is Rust and out of reach; the idea
is a pattern: keep the index (arrangement) of rules by rightmost compound
as owned storage, and treat the dirty element set and the dirty rule set as
the two update streams. Each is a counted loop over a list of indices, i.e.
the dirty-frontier shape of §2.4. Status: **promising as the shape of
incremental matching; hard/dead end as a general renderer substrate**.

### 1.4 Incremental λ-calculus: derivatives of functions — uncertain in general; its special case is the "delta API" the owner asks for

**What it is.** Cai, Giarrusso, Rendel, Ostermann (fetched
https://arxiv.org/abs/1312.0658): "a derivative maps changes in the
program's input directly to changes in the program's output, without
reexecuting the original program"; a *change structure* per type says what
a change is and how to apply it; *static differentiation* transforms a
program into its derivative mechanically, with correctness proved in Agda
for simply typed λ-calculi and a Scala plugin reporting "orders of
magnitude" on one program.

**Granularity.** Per value, by type. Dependencies: static (the derivative
is a program). Cutoff: when a derivative yields the nil change. Memory: no
trace; only the old input/output where the derivative needs them.

**Honest assessment.** Derivatives are only cheap when a primitive has a
cheap derivative; a fold with a sequential chain (block flow, a prefix
sum, counter numbering in document order) has a derivative that is "re-run
from the change point", so for the layout core the derivative is the naive
incremental algorithm. The transformation also needs change structures for
every type in the stage, which the writer supplies. Status: **uncertain /
likely dead end as a transformation; promising as a discipline.**

**The special case that matters: hand-written derivatives with resync
cutoff.** `old result + change → new result` is ordinary code with a
specific shape for each algorithm:

- *Line breaking after a text edit*: re-break from the line containing the
  edit; stop at the first break opportunity that coincides with an old
  line's start with the same width state; the lines after it are reused
  unchanged. Text editors have done this for decades (from memory); Blink's
  LayoutNG reuses the unaffected line boxes of a paragraph after a change
  (from memory; its "line reuse"/fragment-items mechanism, not re-checked
  today).
- *Block flow after a child's size change*: re-place children from the
  changed one; cutoff when the running block offset equals the old one at
  some later child (which happens only when sizes net to zero, so rarely;
  the realistic cutoff is "the context's own size did not change", which
  stops the parent).
- *Column balancing, table column widths, flex distribution*: no cheap
  derivative; these are the "a local change is not local" cases (§3.4).

**Mapping onto Whitefoot.** Nothing in the language is needed beyond
ownership: the result must be a mutable owned structure the derivative
edits in place, e.g. `Box<Slots<Line>>` with `insert_at`/`remove_at`
([OP-10]). Those two shift the suffix by one memmove each, O(n) per edit;
a list with many lines and frequent single-line edits wants a chunked
sequence (`Segments` is fixed at construction, so chunking is a `Slots` of
`Box<Slots<Line>>`). Note from [OP-10]: `insert_at`/`remove_at` invalidate
nothing by reference (there are none in storage) but *stale indices name
the current occupant* ("a logic error and not a memory error", spec
[OP-13] note at line 1212), which is exactly why a generation number must
be data (§1.8).

### 1.5 FRP and signals — likely dead end at renderer scale; fine mental model for the stage graph

**What it is.** A graph of signals; a write to a source marks dependents
dirty (push) and reads recompute on demand (pull); modern "fine-grained
reactivity" (SolidJS and the like; from memory) is a dynamic DCG with
automatic dependency capture on read and a topological re-evaluation.
Granularity: per signal. Dependencies: dynamic. Cutoff: equality at each
signal. Bookkeeping: per signal, subscriber lists, hundreds of bytes.

**Fit.** The same cost profile as §1.2; subscriber lists are references,
unrepresentable without an arena. At renderer scale (10^5 nodes) it is out
by §0. It describes the *stage* graph well (document → rule store →
matched → cascaded → inherited → computed → box tree → prepared text →
laid out → painted: a dozen signals), where a push of dirtiness between
stages costs nothing. Status: **likely dead end** for data, **established
vocabulary** for the stage DAG.

### 1.6 React-style reconciliation — established; belongs at the output boundary

**What it is.** Recompute a *description* of the output cheaply, then diff
it against the previous description with stable keys to produce the minimal
set of mutations to an expensive mutable sink (the browser DOM in React;
the shell's display lists, layer tree and damage here). Dependencies: none
tracked; it is output-side cutoff. Cost: O(n) in the description's size
with keyed children, which is why React also needs memoization
(`memo`/`shouldComponentUpdate`) above it to avoid re-describing unchanged
subtrees.

**For the renderer.** Per formatting context, a display list is the
"description"; `design/processes.md` already sends display lists through
shared memory. If each context's display list is memoized (§1.1) and keyed
by the context's stable identity (§1.8), reconciliation reduces to: for each
dirty context, send its new list; for the rest, send nothing. The shell's
damage then follows the dirty contexts' positions, with no tiles. That is
the other branch's core; here it is only the point that **reconciliation
needs stable identity and per-unit equality, the same two things the memo
family needs**, so one mechanism serves both. Status: **established**.

### 1.7 Persistent data structures and structural sharing (hash-consing, HAMT, ropes, finger trees) — likely dead end in pointer form; reduces to 1.8

**What it is.** Immutable trees where an update copies the O(log n) spine
and shares the rest by pointer; old and new versions coexist; equality of
shared subtrees is pointer equality (hash-consing makes it so for all equal
subtrees). Cutoff is free: a memo keyed on a subtree pointer is valid while
the pointer is. Memory: shared; versions cost only their spines.

**Why not in Whitefoot.** A shared subtree has two owners. [TYPE-8] "a
reference kind is not a value type ... No struct field, enum variant
payload, Array, Slots, Ring, or Segments element, Box content ... may be
one", [STOR-5] "Storage is reference-free", [TYPE-9] a `Box` has "exactly
one heap object the Box value owns". There is no `Rc`, no arena pointer
type, no `Shared<T>` inside data (a `Shared<T>` handle exists, [SHARE-1],
but it is a synchronization object reached only through `atomic`
statements, [SHARE-2], and each such statement is a waiting call that
forbids overlap; it is not a cheap shared pointer). Pointer persistence is
therefore unrepresentable. Status: **likely dead end** as such.

**What survives.** The same sharing by *index* into an arena, with explicit
versions; see §1.8. Hash-consing survives as *interning*: Snowghost already
interns computed-style groups, so "same group id" is a free equality for
cutoff (`design/pipeline/style.md`, the intern post-pass; measured at
0.5 to 4.6 percent of the four-worker style stage across the three real
pages, `concurrency/DESIGN.md`, Style measurement). Ropes survive as
chunked `Slots` of `Box<Slots<T>>`.

### 1.8 Versioned arenas, generations and change ticks — promising; the family that fits Whitefoot

**What it is.** Entities live in a `Slots<Option<T>>` (or a `Slots<T>`
with a free list) addressed by index; each slot carries a generation that
is incremented on free, so a stale index is detected as data; each slot
(or each field group) carries a *change tick*, the global frame counter at
its last write; each consumer records the tick at its last run and
compares. **Established**: entity-component systems; Bevy's change
detection keeps per-component "change ticks" compared against the
system's last-run tick (from memory, not fetched today); Chromium's
layout objects keep dirty bits propagated to ancestors (from memory). The
spec itself names the pattern: "a program that must detect it keeps a
generation number as data" ([OP-13] note, line 1212).

**Granularity.** One tick per slot, or per field group of a slot (e.g. one
for the element's own style, one for its subtree's maximum). Dependencies:
static (the consumer knows, from its row, which arena roots it reads;
§2.1); the dynamic part is which *slots* changed, which the ticks record.
Cutoff: compare the result's tick: if the recompute wrote an equal value,
do not bump the tick (that is backdating, and needs equality: §2.2).

**Bookkeeping.** One or two integers per slot; writes cost one store; a
no-change frame costs one comparison per *root* if each root keeps a
subtree-maximum tick, otherwise one dense scan (§0, fact 1). Memory: O(n)
integers.

**Parallel fit.** Good, and this is where Whitefoot's rules help:
- a per-slot tick written in a counted loop at `ticks[i]` is a proved
  single-binder affine element ([PAR-2]), permitted like any other
  per-element write;
- a per-root "maximum tick" is exactly a [PAR-2] accumulator: `imax` is
  one of the ten admitted recombinable operations, so
  `set latest = imax(latest, ticks[i])` keeps the loop parallel. (spec; not
  compiled today.)
- the subtree-maximum tick up an owned tree is computed by the same
  recursion over disjoint children that layout already uses.

**For the renderer.** The context tree, the paragraphs and the element
styles each get ticks; the "dirty frontier" is the set of slots whose tick
equals the current frame (or a list built as the writes happen). Status:
**promising**; the concrete data layout is decided by E1.

---

## 2. Whitefoot specifically: what the language gives and withholds

### 2.1 The effect row as a memoization key: place-complete, not value-complete — established in part, gap in part

`design/pipeline.md`, third decision: "the compiler then proves the
memoization key complete and a result that read anything outside its key
does not compile". Separate two claims.

**Claim A, place-completeness: holds.** (spec)
- [EFF-2]: "Rows are checked both ways against this complete exhibited set
  — every declared entry is exhibited ... and every exhibited access lies
  under some declared entry — so undeclared-but-exhibited and
  declared-but-unexhibited are both EFF-2 errors."
- Roots: "Every effect_path is rooted at one reference parameter of the
  same callable"; "A by-value parameter has no effect entry at all: the
  call site records the consumption of a move argument or the read of a
  copy argument"; "A root resolving to a local, a result binder, a
  by-value parameter, or a non-parameter declaration is an EFF-1
  rejection"; "A const root ... contribute[s] no read effect".
- There are no globals, no function values ([FN-5]), no hidden state; host
  outcomes enter only through waiting calls ([WAIT-2]), which a function
  that does not wait cannot make ([WAIT-1]).

So the set of *places* a function can observe is exactly: the storage under
each `reads`/`writes` path of its row, substituted with the actual
arguments at the call ([EFF-5]), plus its by-value arguments, plus consts
(immutable). A memoization key made of those places is complete, and
nothing can be read outside it. This part of the decision is true and is
the real asset: it is what Salsa buys with dynamic tracing and Chrome with
code review.

**Claim B, value-completeness: not given by the language.** A key must say
whether the *values* at those places changed since the cached run. The row
names `reads(styles)`; it does not say "unchanged since frame 41". Nothing
in the spec records versions or compares old and new inputs; that is
program data, and a program that forgets to bump a version has exactly the
"missed dependency renders stale output" failure the decision wants to
exclude, moved from the read side to the write side. Minimal example:

```wf
fn border_edges(styles: &Styles, style: StyleRef) -> edges: Edges reads(styles)
```

(real signature, `renderer/layout/box.wf:28`). The compiler proves this
reads nothing but `styles`; a caller that cached `edges` must still decide
on its own whether `styles` changed, and the row does not tell it that the
function depends on one group of `styles`, not all of it.

**Claim C, the compiler's own licensed memoization barely applies.**
[EFF-3]: "A call whose row is pure and which allocates nothing licenses
deduplication and reordering with equal arguments." Every stage result that
is a tree (`Box<Slots<Context>>`) allocates, so the license covers only
leaf arithmetic. Any memoization of stage results is program-level.

**Granularity caveat and the pattern that recovers it.** [EFF-2]: "a
dynamic element or range maps to its nearest statically nameable enclosing
path"; a signature "never contains an index expression; an index enters an
effect only through an IDENT that resolves to a value parameter of the same
callable". So:

```wf
// coarse: the row names the whole store; the key is "all of styles"
fn edges_a(styles: &Styles, style: StyleRef) -> e: Edges reads(styles)

// fine: the caller passes the element; the substituted row at the call
// is reads(styles.groups[k]) (EFF-5 substitutes the actual's path)
fn edges_b(group: &BoxGroup) -> e: Edges reads(group)
...
let e = edges_b(&styles^.groups[k]);
```

"Pass the inputs, not the world": a memoized unit receives exactly its
inputs as reference or value arguments; its row is then its key shape, at
element granularity, with no wildcard. The cost is that callers must form
those references, which [REF-2]/[OWN-7] police; the benefit is that the key
shape is now a static list of element paths, which §2.3 can turn into
versions. Status: **established** for A, **gap** for B, **pattern** for the
caveat.

### 2.2 Equality for cutoff — gap with a workable route

The spec's operation table has equality on primitives (`ieq`, `feq`) and
tag-only enums (`eeq`), and nothing on aggregates: "Payload-carrying enums
... remain outside the operation table" ([OP-8], spec line 1131). Cutoff
(backdating) on a context's result needs `Fragment == Fragment` and
`Lines == Lines`. Routes:

- hand-written `eq` per result type, supplied where generic code needs it
  through an `interface` with function-kind members ([FN-3]: "fn
  find<interface Key<K, E>>" declares type binders and one function-kind
  parameter per member, with "no reflexivity, transitivity, ordering
  consistency, hash/equality compatibility, or other algebraic law" assumed,
  [FN-4]). Expressible today; verbose; no derivation.
- interning: equality of interned ids is `ieq`. Snowghost's style groups are
  interned already; a layout result's *size* is a few integers, and "same
  border-box size" is the cutoff that stops the parent (§4.2). So the cheap
  cutoffs need no aggregate equality; only "same lines" would.
- a derived structural equality would be a language decision (`design/`
  tree): a compiler-generated `eq` for a struct of comparable fields. Not
  in the spec; mark as the smallest language change this branch would ask
  for, after E1 shows aggregate cutoff matters.

Minimal semantic example of the gap:

```wf
let new_lines = break_lines(&para, width);
// wanted: if eq(&new_lines, &old_lines) { keep old tick } — no such eq
```

Status: **gap**, **workable** by interface and interning.

### 2.3 Version stamps derived from the row — the language mechanism this branch would propose; promising, needs a decision

The row gives the key *shape*; what is missing is the key *values*. Every
write is visible to the compiler statically: it is either a [SET-1] commit
in the body that owns the storage, or a callee's row-declared write
substituted at the call ([EFF-5]); there is no third way to change state.
(Not "every write appears in a row": [EFF-2] says "an access rooted only in
local storage contributes no enclosing formal-rooted effect", so the
function that owns a tracked root writes it with no row entry; the
argument rests on the two statically visible write forms, not on rows
alone.) So the compiler could bump a version at each write site and
nowhere else. Sketch of a mechanism (speculation; no spec rule today):

- a `tracked` storage root: a `Box<Slots<T>>` (or any owned aggregate)
  declared to carry a version per element and a version for the whole;
- every write through a row entry `writes(root[i])` bumps the element's
  version to the current epoch (a per-element affine write, [PAR-2]-safe)
  and the root's version as an `imax` accumulator;
- a `memo fn` whose row reads tracked paths: the compiler stores, beside the
  result, the versions of the read paths at the last run, and re-runs the
  body exactly when one differs; on a re-run whose result is equal under a
  supplied `eq`, the result's own version is not bumped (backdating).

What this buys over the library route: the write side cannot be forgotten
(the bump is derived from the statically visible write sites), so Claim B
of §2.1 becomes true by construction.

**Granularity bound on the write side.** A derived version is only as fine
as the static path of the write, by the same [EFF-2] rule as §2.1's caveat:
`set root^[k] = v` with `k` a local computed in a non-loop body resolves to
the nearest statically nameable prefix, `root`, so the compiler could bump
only the root's version there, not element k's. Per-element versions are
derivable exactly where the index is a value parameter (the row names
`root[k]`) or a counted loop's binder (the [PAR-2] affine element). A
writer that wants element-grain versions must write through those forms,
which is the "pass the inputs" discipline again, now on the write side.
This bounds what the mechanism can promise: complete at root grain
always, at element grain only for parameter- and binder-indexed writes. What it costs: a decision in Whitefoot's
design tree (it is a material choice: a new declaration form, a runtime
counter per element, erased nothing), and a semantics for versions in
parallel loops (an `imax` accumulator is already admitted, so the root
version has a defined value whatever the schedule).

The library route first: the same bookkeeping as explicit code
(`ticks: Box<Slots<u64>>` beside the arena, every writer bumps) is
expressible today and is what E2 measures; the language mechanism is
justified only if E2 finds either a stale-output bug the compiler would
have caught or an overhead the compiler could remove. Status: **promising;
decide after E2**.

### 2.4 Parallel scheduling of a dirty frontier — feasible today in two shapes, with proof cost

The dirty set is dynamic: a list of indices. The parallel loop over it is

```wf
for (k in 0_u64..dirty^.len, apart(i, j) { }) {
  relayout(&contexts^[dirty^[k]], ...);   // writes(contexts[dirty[k]])
}
```

[PAR-2] permits a write only to iteration-own storage, the accumulator, a
proved single-binder affine element (`a*i + b`, which `dirty[k]` is not), a
proved range reference, or a *certified element*: "the element one
set_stmt, or one call through a reference argument naming one element,
writes in B when L carries an apart_clause whose certificate holds
[RANGE-5]". [RANGE-5] needs the two index tuples "proved different ... under
both executions' path conditions and i != j, with the entry state's facts
... active". So the loop needs an entry-state fact that `dirty` has no
repeated entry. **Precedent, measured**: Shape D's level cascade
(`renderer/proto/style/shapes.wf:272-298`) does exactly this with the
requirement `forall listed(k in 0..slots.len) when slots[k] < out.len:
positions[slots[k]] == k` (a left inverse, which implies distinctness) and
an empty `apart(i, j) { }`; `--par-ledger` permits the loop
(`research/investigations/concurrency/DESIGN.md`, Shape D, run 27), and
the producer `level_index` proves the fact as a range postcondition.

Three consequences for a frontier:

1. **The fact is derived per frame.** The POINTWISE record's Limits say:
   "The live DOM. Nothing is stated about the linked arena itself: not
   acyclicity, not facts that survive a mutation. Incremental restyling that
   keeps a numbering across edits would need order keys with gaps, or the
   model route." So the dirty list's distinctness is re-proved by whatever
   builds the list each frame (a walk over the dirty list with a
   `positions` inverse), O(|dirty|), which is the right cost class.
2. **Proof cost is per loop at compile time**, seconds for nested facts
   (POINTWISE, Limits: "a fact with a nested read such as owned costs
   seconds per loop"); acceptable for a handful of frontier loops.
3. **Nesting breaks it.** Contexts are an owned tree (`Box<Slots<Context>>`
   inside each context, `design/pipeline/layout.md`); two dirty contexts
   where one contains the other are not independent, and "not an ancestor
   of" is a tree fact outside RANGE-5's two-bound-variable vocabulary.

The second shape avoids the certificate entirely: **pull from the root
over dirty bits**. Recurse from the root context; at each context, visit
only children whose subtree-maximum tick is current; sibling children are
disjoint owned values, so the recursion over them is the ordinary proved
sibling parallelism the stage already has (Q56's shape). Cost
O(|dirty| × depth) with no distinctness fact; the frontier is an antichain
by construction. This is also Chrome's shape (dirty bits up, recalc down;
from memory). Status: **feasible now** (shape 2), **feasible with a
derived fact** (shape 1); E4 measures both.

### 2.5 Concurrency across stage boundaries — hard under today's rules; needs a measured experiment

The owner's picture: "modify a DOM node, compute style locally, lay out
what that affects, repaint those places, submit to screen", all
concurrently. What the spec allows:

- Within one context of execution, [PAR-1] overlaps two adjacent statements
  when their write paths are disjoint from the other's reads and writes,
  judged statically on paths. `restyle(&doc, &styles, dirty_a);
  relayout(&styles, &tree, dirty_b);` overlap only if `styles` written by
  the first is disjoint from `styles` read by the second: it is not, as
  whole-root paths, and dynamic index lists give "nearest statically
  nameable prefix", i.e. the whole root. So cross-stage overlap of two
  *dynamic* dirty sets is denied statically, whatever the sets are.
- Across contexts, a spawn [WAIT-3] takes value parameters only ("every
  parameter of its callee is a value parameter"), so a spawned layout
  context cannot hold a reference into the document while style writes it;
  data crosses by `move`. A pipeline is therefore "owned messages between
  stages": style produces an owned batch of (element, new group) for the
  layout context, through a `Shared<Ring<...>>` queue with atomic
  statements ([SHARE-2/3]), each atomic statement a waiting call.

So the attainable form is a pipeline of stage contexts passing owned
deltas, with parallelism *within* each stage by [PAR-1/2]. That is real
cross-stage concurrency, but by data boundaries, the same principle as
`design/processes.md`'s renderer/shell boundary. The alternative the owner
describes, one change flowing through all stages as a single chain, is
sequential per change but short, and runs several changes' chains in
parallel only when their paths are proved disjoint, which for dynamic sets
needs the certificate of §2.4 applied to a loop whose body is the whole
chain. Status: **hard**; E5 decides whether the pipeline-of-contexts form
beats the sequential-chain form on latency for a local edit.

### 2.6 Stable identity across edits — feasible now

A `Slots<T>` with `insert_at`/`remove_at` shifts indices ([OP-10]); a
free-list arena (`Slots<Option<T>>` plus a `Slots<u32>` of generations and
a free list) keeps an index stable for the life of its occupant and detects
a stale index as data ([OP-13] note). Every cached result keyed by context
identity then survives edits elsewhere. The context tree's owned nesting
(`Box<Slots<Context>>` in each context) gives stable *paths* but not stable
*indices* across sibling insertions: the layout stage would move to a flat
arena of contexts with parent/child indices if a dirty-frontier loop
(§2.4, shape 1) is chosen, and can keep the owned tree if the pull-from-root
shape is chosen. Status: **feasible now**; the choice falls out of E4.

### 2.7 Determinism as the oracle — established in Snowghost, extend it

[PAR-1/2] make the overlapped result equal to the sequential one; the
layout criterion 3 already checks byte-identical dumps between the
sequential and `--par` builds (measured, `runs/check.txt`). An incremental
build adds a second identity: **incremental(history) == full(final
state)**, byte for byte, for every prefix of an edit script. This is the
cheapest strong test of any scheme in this tree and should be the standing
check of E1 before any timing is believed.

---

## 3. Static versus dynamic dependency tracking

### 3.1 Where static knowledge replaces tracing — established

- **The key shape** of every memoized unit: its row (§2.1). No run-time
  dependency list at all; Salsa's per-call dependency vector is replaced by
  a static list of paths and a per-path version read.
- **Which stage reads which stage**: the stage DAG is a dozen functions
  with rows; dirtiness between stages is a push along static edges.
- **Inheritance structure of CSS**: which properties inherit is static per
  property. `design/pipeline/style.md`'s split ("only the font size, the
  custom properties and the inherited values depend on the parent") is
  already the static dependency statement: a change to a non-inherited
  declaration on element e affects e's computed style alone; a change to an
  inherited one affects e's subtree, bounded by the first descendant that
  declares the property itself (a cutoff visible by interned group
  equality at each child).
- **Layout-affecting versus paint-only**: whether a computed-style change
  can affect layout is decidable from *which group changed*: the interned
  box group (margins, widths, display, floats) versus a color/paint group.
  Interning gives this as one integer compare per element, which is what
  Blink's "style difference" computes by comparing old and new
  ComputedStyle field by field (from memory).
- **Selector structure**: which classes, ids, attributes and pseudo-classes
  a sheet's selectors mention, and in which position (subject, ancestor,
  sibling), is static over the sheet. Blink's invalidation sets (fetched,
  https://chromium.googlesource.com/chromium/src/+/HEAD/third_party/blink/renderer/core/css/style-invalidation.md)
  are built from that: for `.c1 div.c2`, a change of `c1` on an element
  schedules a descendant invalidation that "matches against c2 and
  descends into all light-descendants"; the sets "err on the side of
  correctness, so we invalidate elements that do not need recalculation but
  this [is] significantly better than recalculating everything". Snowghost's
  rule index by rightmost compound is the subject half of this; the
  ancestor/sibling halves are the same precomputation over the sheet.

### 3.2 Where dynamic tracing is unavoidable — established

- **Which elements a selector change affects** needs matching, i.e.
  evaluation: a rule inserted into the sheet affects the elements its
  rightmost compound selects (found through the index, a dynamic set) and
  then the ancestor/sibling test per candidate. Blink does not try to avoid
  this; it bounds it with the invalidation sets.
- **Which elements a DOM mutation affects through selectors** likewise:
  class toggle → invalidation set → descendant walk with matching.
- **Sibling position**: `:nth-child` and `:nth-of-type` read a position
  table built by one walk (`design/pipeline/style.md`); inserting a sibling
  shifts every later sibling's position, O(siblings), and the affected
  elements are found only by looking.
- **Geometry**: which paragraphs a float narrows, which contexts a width
   change reaches through shrink-to-fit (Q56, intrinsic sizes on demand,
   flow *upward*: a text edit inside a table cell changes a column's
   min-content, so the table, so every cell); where a line re-break resyncs.
   These are value-dependent and found by computing.
- **Counters and quotes** are a true chain in document order
  (`design/pipeline/layout.md`): a counter change at one element renumbers
  every later reader in its scope; the affected set is found by walking.

The honest summary: Whitefoot removes the *dependency-discovery* half of
dynamic tracing (no trace, no missed dependency) and leaves the
*affected-set* half, which is the computation itself. That is the right
split: discovery is where Chrome's hand-maintained rules fail, and the
affected-set work is proportional to the change.

---

## 4. Cutoff and granularity for a renderer

Per unit, the key, the cutoff signal, and the overhead, against §0's
budget. Costs per unit are speculation unless marked.

### 4.1 Per element (style) — right grain for style, with ticks not traces

- Key: matched rule set (from the index, by the element's own id, classes,
  local name and sibling position), parent's inherited group id, own
  declarations and custom properties. The rows of the three style loops
  already name these.
- Cutoff: interned group ids equal after recompute → nothing downstream.
  Measured asset: the intern pass costs 2.9 to 4.6 percent of the stage.
- Overhead: one tick per element (8 bytes), one compare; dynamic trace
  entries per element are out by §0. At 180k elements a dense tick scan is
  about 1 ms; a subtree-max tick in the tree makes a no-change frame O(1).
- The inherited pass re-runs over the dirty element's subtree only, in the
  same document-order chain; with Shape D's certificate it could run per
  level in parallel within the subtree (measured: the level cascade is 1.2
  to 2.8× faster than the sequential pass at four workers on the prototype,
  `concurrency/DESIGN.md` Shape D).

### 4.2 Per formatting context (layout) — the natural memo unit

- Key: available size (Q55: "a context's inside then depends on its
  available size alone"), the box-group ids of its own boxes, its
  paragraphs' prepared text (ticks), its child contexts' result sizes and
  intrinsic sizes when read (Q56). Result: boxes, lines and fragments
  relative to its own border box, so **moving a context touches none of
  its contents** (Q55); the parent re-places it by one offset.
- Cutoff: the context's border-box size unchanged → the parent's block
  flow after it unchanged → stop. A few integer compares; no aggregate
  equality needed. Established: Blink LayoutNG's layout cache keyed on the
  constraint space, with a hit when the space is equal or differs only in
  a dimension the box does not depend on (from memory).
- Overhead: ticks plus the key (a few words) per context; with contexts in
  the thousands (not measured; E1 records it), even dynamic bookkeeping is
  affordable here, so this is the one grain where a Salsa-like dependency
  list *could* be kept if a dynamic dependency (which child intrinsic sizes
  were read) turns out to matter.
- Failure of locality: Q56's upward flow (tables, flex, grid, shrink-to-fit,
  floats) means a leaf edit can dirty an ancestor context's key, and the
  ancestor re-runs; the cutoff then fires again at *its* parent if its size
  held. That is inherent, not a scheme defect, and html5's 20.7 percent of
  block boxes in multi-column containers (Q59) are a case where balancing
  re-runs the whole container.

### 4.3 Per paragraph (text preparation and line breaking) — right grain for text, with a derivative

- Text preparation is 60 to 67 percent of the sequential layout stage
  (measured). Key: the paragraph's pieces (byte spans of text nodes plus
  inserted scalars), the font and style groups of its items, the available
  width and float intrusions. Q53 already isolates it: "a paragraph's
  preparation depends on its own text and styles alone".
- Cutoff: lines after the resync point unchanged (§1.4); the paragraph's
  block size unchanged stops the context.
- Overhead: a tick per paragraph (120k text nodes, far fewer paragraphs;
  not measured); the derivative needs the old lines kept, which they are.
- A width change re-breaks every paragraph of the context (no derivative
  helps), in the existing counted loop, in parallel.

### 4.4 Per display chunk (paint) — the context again

A display list per context, keyed on the context's result tick; the shell
receives lists for dirty contexts only, with their new offsets; damage is
the union of old and new rectangles of dirty contexts. Per-box display
items are too fine to key individually and need not be: a context's list
is rebuilt when its tick moved. The other branch owns the details.

### 4.5 What overhead per node is acceptable — arithmetic

With 0.8 s full and 16.7 ms frame: a no-change frame may spend at most a
few hundred microseconds on validation, so validation is O(1) per *root*
(subtree-max ticks) or one dense scan at most; a frame with d dirty units
may spend O(d × depth) on finding them and O(d) on bookkeeping at tens of
nanoseconds each; the per-unit static bookkeeping (ticks, keys of a few
words) adds under 5 percent to a full build if it is a store per write and
no allocation (criterion for E2). Dynamic per-edge records are acceptable
only at context grain.

---

## 5. Experiments that discriminate

Each with its criterion stated before running, as `research/README.md`
asks. None edits the repository; each is a research prototype under
`research/investigations/` if adopted.

**E1. Incremental layout prototype on real pages (decisive for the unit).**
Build the context tree with per-context ticks and keys (§4.2) and a
per-paragraph derivative (§4.3); apply an edit script to html5 and
apollo11: (a) replace one word in one paragraph; (b) toggle a class that
changes a margin on one leaf; (c) change the viewport width; (d) insert a
float; (e) change a table cell's text. Record |dirty contexts|, |dirty
paragraphs|, the count of contexts on each page, and time per edit, at one
and four workers; check incremental == full, byte for byte, after every
edit (§2.7). Criteria: for (a), (b), (e) time ∝ dirty set and under 5 ms on
html5; a no-op edit under 0.5 ms; full build with bookkeeping within 5
percent of today's. Outcome decides context versus paragraph versus
stage-record as the unit, the open question `concurrency/DESIGN.md` names.

**E2. Library versions versus a language mechanism (§2.3).** In E1's
prototype, keep ticks as explicit data first; count the write sites that
must bump a tick and, with a deliberately omitted bump, whether the
byte-identity check of §2.7 catches it (it should, which is the argument
that a test can replace a language rule for a while). Measure the
bookkeeping's share of the full build. Criterion for proposing `tracked`/
`memo` to Whitefoot: either an omitted bump that survived the test script,
or bookkeeping above 5 percent that the compiler could place better.

**E3. Static invalidation sets over the three sheets (§3.1).** For each
class, id and attribute the sheets mention, compute the descendant/sibling
invalidation set Blink-style and, on each page, the number of elements a
toggle of that feature would re-match through it, against the number whose
computed style actually changes. Criterion: median re-matched elements per
toggle below 1 percent of the page, and the over-approximation factor
(re-matched / changed) recorded; if the factor is large, incremental
matching needs the join form of §1.3 rather than invalidation sets.

**E4. Dirty-frontier loop shapes (§2.4).** Write the frontier loop twice:
(1) a flat context arena with `apart` and a `listed`-style distinctness
postcondition from the frontier builder; (2) pull-from-root over subtree
ticks on the owned tree. Record whether `--par-ledger` permits each, the
compile-time proof cost of (1), and the four-worker time on E1's edits.
Criterion: (1) is adopted only if it beats (2) by 1.5× on the frontier
phase; otherwise the owned tree stays and no distinctness fact is needed.

**E5. Pipeline of stage contexts versus sequential chain (§2.5).** Two
drivers for E1's edit (a): one context running style then layout then
paint for the dirty set; and three contexts connected by `Shared<Ring>`
queues of owned deltas. Measure edit-to-display-list latency and the
proportion of the chain that overlaps. Criterion: the pipeline is kept only
if latency falls by 1.3× or more for the local edit; otherwise cross-stage
concurrency is deferred to the parallelism inside each stage.

---

## 6. Top three recommendations

1. **E1 first: an incremental layout prototype with per-context keys and
   ticks, and the byte-identity oracle.** It is the measurement the
   concurrency record already names as the one that decides the unit of
   storage, invalidation and caching; Q55 and Q56 already give the context
   the dependency shape a memo unit needs; and its two numbers nobody has
   yet, the count of contexts per page and the dirty-set sizes for real
   edits, decide whether anything finer than the context is ever needed.
   Everything else in this tree is cheaper to judge once those exist.

2. **Treat the effect row as the key *shape* and versions as data, with
   the "pass the inputs, not the world" pattern, before asking Whitefoot
   for anything (E2).** Claim A of the pipeline decision is already true
   and is the asset; Claim B is a write-side discipline the byte-identity
   test can enforce for now. The one language mechanism this branch would
   propose, a `tracked` storage root whose versions the compiler bumps at
   the writes its rows already know, is justified only by what E2 finds,
   and it is the kind of material choice that needs a decision card with
   measured grounds, not a plan.

3. **Choose the pull-from-root frontier over the owned tree unless E4
   proves otherwise, and do not pursue trace-based schemes.** The arithmetic
   of §0 excludes per-box dynamic tracing (Adapton, signals, Salsa-style
   dependency vectors) and the reference-free storage rules exclude
   pointer-persistent structures; what remains, arenas with ticks, static
   key shapes and output-side reconciliation, is one coherent mechanism
   that also serves the paint boundary. The pull-from-root recursion needs
   no certificate at all, and Shape D shows the certified flat-loop form is
   available if it is ever faster.

Open questions this branch leaves to measurement: the number of contexts
and paragraphs on real pages; the proportion of real edits whose dirty set
escapes upward through intrinsic sizes, floats or counters; the cost of a
derived structural equality against the integer cutoffs that need none; and
whether any stage benefits from dynamic dependency lists at context grain.
