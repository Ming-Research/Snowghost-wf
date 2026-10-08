# Split fragment dependency contract (Q134 A; Q135 A)

Current outcome: [completion acceptance](#completion-acceptance) fails; option A
is not merged into research/m2-layout.

## Question and prior rejection criterion

The owner selected Q134 A on 2026-10-07: retain stable split-run and endpoint
identities with owner-relative anchors, repair affected fragments, and let
following fragments resolve through translated endpoints. Q135 A requires the
dependency and validity contract first. Q132 A retains counted post-publication
flex recovery. Option B is no longer an adoption candidate and its branch stays
unchanged. This document owns A's contract and its acceptance evidence beside
[the cost investigation](DESIGN.md).

Acceptance is byte-identical full dumps, incremental/full identity for all six
X5 kinds in sequential and parallel modes, unchanged case/fixture pages, every
page block edit splice 1 reason 0, and all existing falsifiers plus omissions
of affected-fragment repair and following-fragment translation. Two hosted
rounds compare A with main, cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 and an
independently built same-source base twin, using identical scripts, compiler,
host and settings. The owner's Q138 continuation requires word, sentence, colour, font-size and
root-font medians at most twice main in each page/mode/round, and block no
worse than cf12c609. This supersedes the earlier word threshold recorded in
the historical completion comparison below. Only a
passing result authorizes a merge commit into research/m2-layout followed by
layout-check and check. Failure is reported to the owner without merging.

## Q138 continuation and root-font bisect

The owner continues Q134 A through Q138 A (the previous report called it
Q136). Finish bounded topology replacement and the owner-motion/legacy-reader
contract. The acceptance now applies a twice-main limit to word, sentence,
colour, font-size and root-font, with block no worse than cf12c609, in both
modes and rounds on the same hosted runner. The correctness gates are unchanged.
Only acceptance permits the requested merge commit into research/m2-layout.

Before measurement: compare main 8fbc160, step 2 0e2a093, step 3a db5d98c,
2d706ba, cf12c609, its independent twin and the working A revision. Each CI
build makes and records a pin-only child commit selecting wf-0b7f5c5b9854;
no timing pin is adopted by the work branch. The hosted workflow retains the
patch and both source and child identities. All cohorts use LLVM 22, the same
page/script inputs and one measurement runner in forward/reverse order.
The first step whose root-font cost separates from its predecessor and control
spread identifies the regression interval, not yet its cause. Inspect its
per-edit counters and profile the responsible path before attributing cost.
Reject the hypothesis that retained metadata alone explains the regression if
its work does not rise at that interval or a same-source removal does not
improve the measured root-font edit. Root font still invalidates its actual style consumers;
paragraph preparation, changed inherited metrics and actual reflow are not
assumed removable. Compare that floor with main's path explicitly.

### Exact-route membership experiment

Source inspection finds route-by-route paragraph membership scans introduced
with M2 style routing. Every recorded paragraph route comes from its strut or
pieces. A change that includes strut inputs can therefore trust route membership;
a boxes-only change still filters strut-only uses. A paragraph already dirty
needs neither the membership scan nor another count. The candidate removes
only these repeated proofs; it retains explicit routing and all mark propagation.
Compare A and this repair on the same source/compiler/runner, retaining delta,
layout and total edit times. Profiles include startup and styling and establish
sampled attribution only, not an exclusive edit-time percentage. Reject the
cost explanation if those functions and marking time do not separate, or the
same-source repair does not reduce root-font cost. Existing style, boxes-only
and post-splice style oracles remain required.

The first bisect attempt (37718099858) cannot measure: main already has the
requested release pin, so its pin-only commit exits with no change. Recovery
allows that no-op commit and reuses only the other successfully built exact
cohort artifacts; their revision and pin patches remain in the evidence. This
setup failure supplies no performance evidence.

### Root-font cost floor: source hypothesis before counters

The X5 root-font script changes the html element among 12px, 20px and 24px,
then removes each class. The captured ECMA262
[ecmarkup.css at 24620d3341aaf1a59440fde65343cda3e3f0ad4c](https://github.com/tc39/ecma262/blob/24620d3341aaf1a59440fde65343cda3e3f0ad4c/assets/css/ecmarkup.css)
sets `body { font-size:18px }` and
`#spec-container { max-width:80rem }`. The inspected bytes have SHA-256
`8bef2688107197ac28abe81b62a61100904cec548e223d03a10ac7ea7b6b2fc7`, matching
`research/investigations/concurrency/run.sh`'s pinned input.

Source inference, pending per-edit counters: a root-font invalidation does
not imply that every paragraph's computed font or used line width changes.
The fixed body size can retain text preparation, while a rem-valued container
constraint changes; a changed constraint that does not change its used width
need not rebreak that container's unchanged lines. This is a dependency claim,
not a page-specific admission rule or a measurement of how many consumers the
current scripts change.

The existing [style decision](../../../design/pipeline/style.md) queues actual
root-font readers and inherited changes, then may rebuild without matching when
readers or visited elements exceed a sixty-fourth of the document. A root-font
edit therefore does not unconditionally recompute every style. These timing
records do not count visited style elements, so they establish separate style
cost, not which threshold path each edit took or a global restyle floor. The measured edit time
includes marking actual changed consumers, font picks, preparing or rescaling
text whose inputs changed, rebreaking changed line inputs, dependent placement,
and publication of changed geometry and summaries. Compare main and every M2
cohort's `prepared`, `paragraphs`, `contexts`, `held_entries` and `entries` with
`delta_us`, `picks_us` and the remaining layout time before attributing the
regression. Main has no M2 owner-index summary publication or geometry bridge.
M2 must retain valid summaries, but unchanged flow topology, route membership
and split endpoint identities require no reconstruction. A narrower replay or
publication path must follow actual changed dependencies on any document;
ECMA262's identity or a root-font edit label must never select it.

### Correctly styled ECMA262 profile: membership hypothesis rejected

[Hosted profile 37722145044](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37722145044)
uses the frozen bisect drivers, wf-0b7f5c5b9854, and the same captured page,
UA stylesheet and named external stylesheet mappings as the timing command.
The original bisect workflow's ECMA262 profile commands omitted the external
stylesheets; those profiles cannot attribute the timing workload. This separate
job corrects that input mismatch without cancelling or replacing the timing run.

The corrected profile ran sequential drivers with WF_WORKERS=4 on one
Ubuntu 24.04 AMD EPYC 7763 hosted runner exposing four vCPUs, Linux
6.17.0-1022-azure. Two A sample round trips took 3.70 and 3.64 seconds including
startup, selecting 16 round trips (32 edits), all the first 12px/undo pair.
These upper medians in microseconds are from profiled runs, include profiler
overhead and are diagnostic evidence, not the two-round acceptance workload:

| Source cohort | Edit | Marking | Layout after marking/picks |
|---|---:|---:|---:|
| main 8fbc160 | 28,629 | 1,100 | 27,532 |
| step 2 0e2a093 | 35,882 | 11 | 35,871 |
| step 3a db5d98c | 3,556,842 | 17 | 3,556,824 |
| 2d706ba | 92,276 | 70 | 92,204 |
| cf12c609 | 114,619 | 74 | 114,545 |
| A 0857633 | 110,735 | 72 | 110,665 |
| exact-route repair b31a1b1 | 110,151 | 70 | 110,081 |

Picks have zero upper median in these runs. Style medians range from 3,877 to
4,044 microseconds and are excluded from edit time. The layout column subtracts
each edit's marking and picks before taking its median; subtracting the column
medians need not give the same result. The exact-route membership hypothesis is
rejected for this ECMA262 pair: marking is already only tens of microseconds,
and its removal leaves the roughly 110 ms edit unchanged within this profile's
uncontrolled spread. The repair's correctness gate passed, but no root-font
performance improvement is claimed from it.

The first large profile regression is step 2 to step 3a. Step 3a replaces direct
flat-event reads with virtual owner-index selection in compatibility walkers.
Its `slot_read` specialization accounts for 76.64% inclusive samples,
`sequence_select` for 8.03% self samples, and `sequence_repair` for 2.03% self.
Most of `slot_read`'s descendants are unresolved libc addresses; record copying
is a source hypothesis, not a resolved symbol attribution. By 2d706ba, shared
materialized events and revised publication remove most of that intermediate
regression, but `reduce_sequence` (6.44% self), `prepare_boundary_entry` (3.74%),
`fill_flow` (3.13%) and `store_reduction` (2.76%) expose remaining full-context
representation maintenance. A and the repair show the same dominant layout
functions. Profiles include initial construction and style work, so these
percentages are not isolated edit-time shares; call-stack gaps also limit
inclusive attribution.

Every cohort prepares 41 paragraphs in this pair. The earlier cohorts report
three updated contexts and zero rebroken paragraphs; cf12c609/A/repair report
four contexts, 41 rebroken paragraphs and 112,823 entries. These counts are not
comparable across that interval: the flex update changed from adding only one
context to including the child's `flex_counts`. They do not establish that
those descendants were newly visited. Correctly timed full-cohort evidence and
a dependency-based removal of unnecessary context work remain required.

### Ordinary hosted root-font bisect: complete timing, cancelled profile

[Run 37718501510](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37718501510) completed all 64 ordinary root-font timing files before its 60-minute measurement-job limit cancelled the subsequent profiler. The always-run artifact upload preserved all 2,560 numbered edit records: 20 ECMA262 and 60 HTML5 edits for each of eight cohorts, two modes and two forward/reverse rounds. This is complete timing evidence, not a successful workflow or correctness gate. The partial original ECMA262 profiles have the stylesheet mismatch described above; no HTML5 profile completed. The separate corrected ECMA262 profile supplies the available sampled attribution.

Timing used one Ubuntu 24.04 Intel Xeon Platinum 8370C hosted runner exposing four vCPUs, Linux 6.17.0-1022-azure, WF_WORKERS=4, function fragments, wf-0b7f5c5b9854 and Ubuntu Clang 22.1.8. Frozen source and pin-only child revisions are preserved in the artifact:

| Cohort | Source revision | Pin-only child |
|---|---|---|
| main | `8fbc1601785cee70265da1eac4d99589fc6fb67c` | `ef9a1e47d64059c5609abc692827ebc9876fff02` |
| s2 | `0e2a0931f630f156bf99bcc9596d37acea787ca8` | `faff8fe85c09978e60cfe064158a48824160642b` |
| s3a | `db5d98c8675ab7ead43d829a802abb9bc32f9562` | `5860a0ab17b05b659c7310e6e40b9802fb9862f5` |
| m2 | `2d706ba252c80336ba1926c3d77054714046586d` | `a12772f3ad66b3be11379cba5cdf6f8749948429` |
| base | `cf12c609e1c00f86bb431fab4e92f5dca2bf94f2` | `318b327c85458c86b40ea6d999d3ed60b523bd56` |
| twin | `cf12c609e1c00f86bb431fab4e92f5dca2bf94f2` | `8a2172b9d3cee9b1800928ad687fcd526b063f5c` |
| a | `08576333ed5ecfd84d790cd810324b403bdcf95a` | `3fbe84071d6e71ed25256e3a2aeaf30ca4ed4e65` |
| fixed | `b31a1b1233fe86b3da66fc1c2027d621ada6b0d4` | `08434d3e31c62abea59f5c208021a4e1fa323e02` |

Upper medians in microseconds, round 1 / round 2. Layout subtracts each edit's marking and picks before taking its median. Style remains separately reported and excluded from edit time; picks medians are 0–1 microseconds.

| Page / mode / cohort | Edit | Marking | Style | Layout |
|---|---:|---:|---:|---:|
| ecma262 / seq / main | 27,971/26,865 | 1,731/1,656 | 4,481/4,130 | 26,181/25,188 |
| ecma262 / seq / s2 | 32,593/31,390 | 11/10 | 4,470/4,127 | 32,581/31,380 |
| ecma262 / seq / s3a | 2,805,168/2,807,622 | 15/15 | 4,155/4,312 | 2,805,148/2,807,599 |
| ecma262 / seq / m2 | 81,849/81,234 | 60/60 | 4,246/4,139 | 81,790/81,174 |
| ecma262 / seq / base | 113,424/113,568 | 64/63 | 4,369/4,262 | 113,360/113,505 |
| ecma262 / seq / twin | 113,270/117,174 | 64/66 | 4,349/4,436 | 113,210/117,100 |
| ecma262 / seq / a | 107,989/107,931 | 60/61 | 4,158/4,204 | 107,926/107,873 |
| ecma262 / seq / fixed | 108,095/111,047 | 61/63 | 4,139/4,387 | 108,023/110,986 |
| ecma262 / par / main | 65,039/64,658 | 1,938/1,968 | 4,879/4,959 | 63,120/62,677 |
| ecma262 / par / s2 | 71,334/69,987 | 18/16 | 5,112/4,801 | 71,316/69,970 |
| ecma262 / par / s3a | 3,911,243/3,887,471 | 19/19 | 4,860/4,945 | 3,911,223/3,887,452 |
| ecma262 / par / m2 | 160,372/157,919 | 77/77 | 4,800/4,887 | 160,294/157,842 |
| ecma262 / par / base | 232,214/234,144 | 79/76 | 5,000/4,940 | 232,135/234,070 |
| ecma262 / par / twin | 220,551/230,247 | 76/76 | 5,085/5,030 | 220,475/230,173 |
| ecma262 / par / a | 232,118/222,682 | 74/77 | 4,861/4,951 | 232,033/222,605 |
| ecma262 / par / fixed | 211,026/220,233 | 77/77 | 4,887/4,857 | 210,948/220,155 |
| html5 / seq / main | 636,041/632,503 | 4,718/4,768 | 292,928/292,233 | 631,326/627,936 |
| html5 / seq / s2 | 659,375/657,612 | 16,922/16,878 | 291,176/289,774 | 642,430/640,587 |
| html5 / seq / s3a | 5,124,109/5,126,274 | 18,794/18,782 | 291,734/291,948 | 5,105,197/5,107,211 |
| html5 / seq / m2 | 734,410/732,907 | 38,395/38,210 | 295,230/292,234 | 695,888/694,783 |
| html5 / seq / base | 768,128/771,479 | 39,997/40,145 | 292,697/293,573 | 727,771/731,183 |
| html5 / seq / twin | 770,413/763,210 | 40,126/39,833 | 293,186/290,377 | 730,606/723,465 |
| html5 / seq / a | 770,016/772,543 | 39,868/39,955 | 293,425/293,231 | 729,919/732,765 |
| html5 / seq / fixed | 760,823/761,223 | 36,484/36,618 | 290,465/290,114 | 724,478/724,705 |
| html5 / par / main | 390,073/390,646 | 4,204/4,263 | 204,166/203,502 | 385,593/386,377 |
| html5 / par / s2 | 410,442/413,817 | 17,166/17,355 | 203,685/204,472 | 393,470/396,527 |
| html5 / par / s3a | 5,935,147/5,914,202 | 18,739/18,555 | 204,058/203,472 | 5,916,629/5,895,635 |
| html5 / par / m2 | 524,367/525,260 | 40,433/40,377 | 202,403/201,401 | 483,895/484,993 |
| html5 / par / base | 600,447/590,885 | 41,412/41,556 | 203,886/204,545 | 558,841/549,347 |
| html5 / par / twin | 585,124/599,593 | 41,660/41,575 | 204,995/204,934 | 543,139/558,286 |
| html5 / par / a | 598,453/600,015 | 41,946/41,457 | 204,520/204,651 | 556,612/558,662 |
| html5 / par / fixed | 582,187/580,373 | 38,573/38,468 | 204,259/204,031 | 543,682/541,913 |

The ordinary runs confirm the first major interval at step 2 to step 3a: ECMA262 grows from 31–33 ms to 2.81 s sequential and 70–71 ms to 3.89–3.91 s parallel; HTML5 grows from 658–659 ms to 5.12–5.13 s sequential and 410–414 ms to 5.91–5.94 s parallel. Shared event materialization and revised publication recover most of this by 2d706ba, but ECMA262 remains above twice main there and at cf12c609/A/repair. The exact-route repair leaves ECMA262 unchanged in scale. HTML5 marking falls from A's 39.9–41.9 ms to 36.5–38.6 ms; that local reduction does not remove the broader whole-context costs or establish acceptance for the current implementation. The independent cf12 twin quantifies control spread without authorizing a relaxed threshold.

The unavoidable work is dependency work, not a measured time lower bound. ECMA262 reports style time of about 4.1–5.1 ms in these runs (outside edit time) and prepares 41 paragraphs; preparation and any changed layout inputs require handling, but their isolated minimum cost was not measured. Main's 26.9–28.0 ms sequential and 64.7–65.0 ms parallel edit times are comparison-path costs, not proof that every operation on that path is necessary. Its unused-constraint handling may itself do avoidable work.

HTML5 prepares 60,867 or 60,868 paragraphs, rebreaks 60,868, updates 13,903 contexts and walks 105,989 entries in every cohort and mode. Its root-font change therefore has extensive actual text/layout consequences: style costs about 289.8–295.2 ms sequential or 201.4–205.0 ms parallel, while main edit costs 632.5–636.0 ms sequential or 390.1–390.6 ms parallel. These observed operations and times are the full-cost comparison; they do not prove a universal timing floor. Cached preparation may reuse shaping, and unchanged dependency outputs can still stop propagation. The ECMA262 flex-counter caveat above remains: earlier counters omitted descendant work that later versions report, so their zero rebreak count is not evidence that no descendant lines were broken.

The generic possible next design is to retain the actual completed effective flow inputs and admit an own-constraint-only edit when those inputs and used outputs are equal and no interior consumer is marked. That could retain unchanged origins, natural-position offsets, fragment roles and boundary summaries without replay or publication. It is a proposal only: recomputing a previous frame with current styles does not establish equality with the old inputs, and equal outer dimensions alone do not establish equal interiors. No such cache or admission was implemented as part of this bisect. The current continuation's full six-kind acceptance must decide whether another owner decision is needed.

### Bounded topology dependency audit

The retained geometry interval is not a topology certificate. In particular,
two split heads of one owner separated by a lineless paragraph form one run;
adding visible text makes two. The new run needs roles that did not previously
exist. A lined paragraph immediately before/after a run also controls whether
that run emits an empty role, and a backward sibling query controls its leading
position. Those negative dependencies can lie outside first-open..last-close.
The preceding compact aligned arrays could not insert a role without shifting
later slots, so `stacked.fragments_same=False` cleared the entire domain.

The continuation's implementation reserves three independently active
roles in one record at every stable split slot, with a run using its first
split's cells. A single record per split preserves the source-count limit;
a flat array of three times the split count could reject previously admitted
source domains solely because some inactive roles acquired capacity.
Same-owner adjacency and indexed join edges identify only the runs intersecting
a changed dependency. Empty-inline sources retain paragraph/mark ownership,
separately from split cells. Publication emits only active records in the
existing phases and source order; physical capacity must never stand in for a
live-fragment count. A local run replacement retires only its changed records;
source-domain reconstruction still retires every handle and dependency index.
The replacement is wired into replay; its correctness and cost remain unverified
until the hosted gates below run on this revision.

A separate source-domain certificate retains sorted split keys, same-owner links
and negative dependency intervals across a full geometry replay. Such a replay
still recomputes every required join from current line presence, every role,
empty-source activity and geometric range certificate; it does not repeat source
sorting or structural gap discovery. Source construction invalidates the
certificate, and a new context starts without it. Certified splices preserve it
only under the same retained-source/barrier contract used by bounded repair.
Equal source counts alone never authorize reuse. The retained-splice argument
uses existing admission: inserted content has no split sources, retired subtrees
have no fragment sources, Float/Out retirement is refused, and the seam rejects
insertion into a potentially joinable same-owner gap. A non-Text Open/Child
between splits of the same still-open inline owner is itself a split source, so
removing that barrier would fail source retirement. This deduction relies on
`splice.wf` and `splice_boundary.wf`; independent review must check it against
their complete admission paths. This removes source work that root-font
restyling cannot change; its measured contribution remains unverified.

### Owner motion and legacy-reader transaction

The selected continuation retains owner-relative geometry as durable state.
Reference scratch has a transaction-local freshness obligation rather than a
promise that every suffix descendant has been materialized. A context has three
phases: ordinary retained state, replay with old-frame reads for untouched
payloads, and settled replay with current-frame reads. These states distinguish
temporal inputs; a single `local_geometry=False` bit cannot distinguish them.

Before a replay writes a block, it captures that block's old absolute origin
and materializes its raw fields. Untouched payloads during replay resolve their
retained local fields through old ancestry, stopping at a captured old origin;
they must not inherit a still-open block's temporary stacking coordinates.
Fresh targets continue to expose the raw values the reference walker expects.
After stacking finishes, current-frame resolution uses settled fresh ancestors.
Moved intact suffix Opens also capture old origins before local mutation, so
later old-frame queries cannot accidentally observe updated locals. A bounded
list of touched payloads clears freshness and captures after publication; no
wrapping generation or whole-context reset is required. A child's parent-owned
placement freshness is distinct from its own context's replay phase.

For a uniform exact suffix move, change each direct suffix entry by the requested
absolute displacement minus its owner's displacement; an intact Open retains
its descendants' local origins and nested reductions. The replayed range and
ancestor chains publish fresh results. Unchanged suffix scratch is never encoded
as if fresh. Lined Text moves its paragraph; untouched lineless scratch retains the
reference exception. A freshly stacked paragraph that has no lines resets its
unplaced normal/resolved origins and beside flag to the fresh-build defaults.
This includes a paragraph losing its last line: newly active empty sources must
not inherit its preceding lined coordinates. Placed atomic children move independently, including those
of a lineless paragraph. Positioned children resolve static axes from settled
anchors, then the existing containing-block algorithm resolves explicit axes.
Each coordinate is translated exactly once.

Natural positions also retain a presence bit and an exact i64 offset from the
payload's normal origin. Open, Text, Child and Float resolve through the same
old/current frame as their geometry; Close and Out remain absent. The natural
sentinel is never converted to an offset or identity. Replayed natural values
stay raw until their payload settles. This removes the separate dense
`shift_naturals` obligation rather than moving the suffix scan into another
reader. Full replay may materialize the complete current state because it
actually visits it; local replay must not set `boundary_dirty` merely because
unvisited raw scratch is stale and thereby force the next edit to rebuild it.

The existing origin/travel admission still precedes suffix motion and partial
convergence. Unsafe arithmetic executes the reference operations in their
original order. Materialization and encoding preserve exact i64 differences and
all i32 narrowing/saturating boundaries. Anchoring does not authorize reversing
saturation or treating a previous raw rectangle as current reference output.
The stack gives a finite Text natural only to a paragraph with lines. Lineless
untouched paragraph scratch therefore remains fixed with an absent natural; atomic child
anchors still move independently. For a raw fallback, a natural that saturates
to MAX becomes absent and cannot be resurrected by a later negative shift.
The boundary oracle exercises MAX-1, +1, -1 directly and requires both persistent
absence and the independent round-trip of scratch coordinates. Its omission
falsifier must successfully compile and trip that assertion.

These are implementation obligations under Q138 A; hosted semantic and omission
evidence is required before claiming the new transaction is complete.

### Continuation validation probes

The generated topology probe changes whitespace-only paragraphs between lineless
and lined states with a preserved newline under `white-space:pre-line`. The first
probe inserted visible text into whitespace-only nodes and was correctly refused
by the existing text-patch admission before layout; replacing that operation
preserves the intended split/join test without changing admission. It covers
leading, intervening, trailing and empty-inline sources, nested owners sharing
an opening, negative margins, coincident rectangles, growth and undo. Established
fixture HTML stays unchanged.

The owner-motion omission removes direct block displacement. Its first mutant
left a blank line and failed canonical-form checking; that result is not semantic
detection. The corrected omission removes the complete statement line. The
old-frame omission supplies current scratch instead of the captured old origin
at the shared ancestry resolver. A narrower paragraph-materialization mutation
was not detected by the existing fixtures and did not omit old-frame resolution
for children or descendant Opens; it therefore did not test the stated global
contract. A relative-owner/padded-context fixture extends the existing cascade
schedule. Neither an unrelated compiler failure nor a refused edit counts as a
falsifier result.

## Contract before implementation

The reference is the existing full fragment generator, checked against the
project's external rendering oracles; cached output is never a correctness
oracle. The relevant owners are `design/pipeline.md`,
`design/pipeline/layout.md`, and the stable-split section of
`../structure-edits/layout-design.md`. The merged anchors already identify
endpoints. Q134 therefore concerns retaining run correspondence and complete
invalidation, rather than inventing an endpoint identity absent from the base.

A split is one open inline owner interrupted by an Open(block) or
Child(context) payload. A run is a maximal sequence of that owner's splits
whose intervening flow events are all lineless paragraphs. Multiple runs of
one owner remain distinct even when their rectangles coincide. Fragment
identity is run identity plus role (leading, spanning, trailing), never owner
plus rectangle. Paragraph text/inline fragments retain paragraph ownership.
Empty-inline identity is source paragraph plus inline mark, separate from
run-plus-role identity. Context-owned empty-inline fragments retain their source paragraph's reference
scratch semantics: a lineless paragraph does not acquire a translated origin.

| Output | Inputs, including negative dependencies |
|---|---|
| Run membership/order | Split source order and owner; first/last live payload identities; every intervening event's kind and paragraph line-presence bit. An absent separating line is an input. |
| Leading fragment existence | The event immediately preceding the first opening; whether it is lined; its closing inline-owner marks. |
| Leading y selector | `sibling_above` backwards through lineless paragraphs, floats and positioned events to the first discriminating event; whether a closed block is itself a split head; Split.line sentinel. |
| Leading y | First visual top, or pending line position from the first normal origin and exact offset; preserve the selector and saturation order. |
| Spanning rectangle | First split's containing left/width; context content left; first visual top; last visual top and height. Height is `(last_top +sat last_height) -sat first_top`. |
| Trailing existence | Event immediately after the last close; its line presence and opening inline-owner marks. |
| Trailing y | Last visual top, height, and resolved bottom margin: a block resolves its style with the first split width as percentage basis; an independent Child supplies its already resolved margin_bottom. |
| Empty-inline rectangle | Source paragraph's line-presence bit, marks and styles, absence of that owner from the split-owner set, paragraph left and its retained lineless resolved position. |

Text can change shaping, line count, height, intrinsic contributions and
line-presence, hence run joining and adjacent-fragment existence. Unchanged
line presence is insufficient when owner marks change. Font-size can also
change inherited lengths, widths, margins, pending lines, and the containing
block's geometry. Class changes use actual style deltas: paint-only changes
leave these inputs unchanged; layout or generated-content changes follow all
style uses, including visibility of an inline's own fragment. Block insertion
or removal changes order, source ownership, adjacency and lifetimes. A kept
split head's interior edit changes its extent without necessarily changing
its external run. The existing structural certificate proves which complete
block seams preserve run topology and selectors; it must not be weakened.

Recompute topology when any membership, adjacency, source or selector input
changes. Recompute geometry only for changed geometric inputs. A uniform
translation with unchanged local geometry and exact arithmetic changes no
run topology or dimensions; A changes the owning origin, whereas B writes
each affected flat rectangle. A spanning run whose endpoints move differently
recomputes its extent. A changed pending margin repairs Split.line's offset;
translation alone preserves it only under the same exact-arithmetic and
sentinel conditions as the existing motion certificate. A changed width or
margin always refreshes the corresponding run fields, even if height agrees.

Validity has separate topology, geometry and scratch obligations. An anchor
certificate is carried only across edits whose dependency closure preserves
it; changed expressions must be checked against freshly computed reference
rectangles. Raw scratch is authoritative after reference replay until repaired
anchors are certified. A stale raw rectangle cannot be compared as if it were
fresh, nor can a fresh anchor override a legitimate reference result. The full
bridge remains necessary when a legacy reader requires all resolved scratch.
Missing metadata, retired endpoints or failed numeric conditions retain the
existing reference behavior; no new source limitation is introduced.

### Edit closure and publication

| Edit | Invalidated inputs | Required repair | Retained work |
|---|---|---|---|
| Word or sentence text | Shaping, breaks, line-presence, paragraph size and outgoing flow state | Prepare/break the changed paragraph; settle affected flow; repair intersecting run intervals. A line-presence transition rebuilds topology, including negative adjacency inputs. | Unchanged pieces retain owner marks; runs outside replay keep selectors, offsets and geometry certificates. Following endpoints consume the exact admitted motion. |
| Local font-size or root font | All actual inherited font/length uses, intrinsic size, available width, line-presence and resolved margins | Follow recorded style uses, recompute affected widths, breaks, margins and flow; repair the run's first width and last margin even when height is unchanged. | A uniform exact vertical move preserves local offsets and role slots. Root font has no promised small frontier. |
| Class / colour | The actual style delta, including fragment visibility and generated content | Paint-only colour changes no layout input; layout deltas follow their recorded uses. Changed box/inline ownership or generated pieces replaces topology. | Style identity alone is neither an invalidator nor a proof of unchanged layout. |
| Block insertion/removal | Source order, endpoint lifetime, adjacency, owner marks and boundary state | The existing complete-block splice certificate permits retention only when no split or empty source is retired and the seam preserves topology/selectors. Otherwise rebuild the affected context through its recorded checkpoint. | Certified kept payload slots and relative anchors survive rank shifts; reference entry rebuild restores raw ranks before binary split lookup. |

There are three authority states. Full construction/reconstruction publishes raw
reference rectangles, dirty pending lines and uncached topology. Encoding then
publishes exact line offsets, checks every raw/anchor field, and constructs the
interval index. A stable-topology replay starts with these certificates, dirties
only stacked split lines, publishes their offsets after endpoints settle, and
repairs/certifies intersecting leaf slots before the balanced validity join.
Only then is `fragments_anchored` published. Raw suffix y fields are deliberately
stale in this last state: every output reader must use `placed_context_fragment`.
A compatibility bridge materializes anchored values before making raw scratch
authoritative again. Clearing fragments drops the index, aligned anchors and
repair/authority flags together. A failed certificate forbids local reuse;
it is not evidence that stale suffix scratch is reference output.

The index stores split-slot extrema, not coordinates: an enclosing run intersects
a replay of its interior even when neither endpoint is replayed. Payload slots,
not shifted event ranks, identify the endpoint. Flow order determines interval
selection and output order; it must never be inferred from y because relative
positioning and negative margins can reverse it. Empty-inline rectangles keep
their source paragraph's last lineless scratch semantics and are not suffix
rectangles. They can be retained only under the explicit empty-source stability
condition.

### Targeted certificate invariant

`repair_anchored_fragments` returns whether the targeted path executed, while
`fragments_valid` records the comparison result. Its admitted unmutated path
must produce true: `geometry_update_reference` first materializes nonzero
context adjustments and clears them; topology validity supplies live first/last
payloads and split slots; dirty line offsets are published before leaf repair.
For each mode, repair and evaluation then read the same immutable endpoints
and apply the same ordered i32 operations. The mode-2 i64 difference reconstructs
the freshly stacked i32 line exactly; mode 1 uses first top, mode 3 uses last
bottom minus first top, and mode 4 uses last bottom plus the repaired margin.
Untouched roles retain their prior certificates under the topology and exact
motion conditions above. Thus a failed targeted field comparison is an internal
invariant failure, exposed by the full/incremental oracle, rather than a supported
route to valid raw suffix rectangles. The omission falsifiers intentionally
break this invariant; there is no recovery that hides their missing work.
The normal full publisher differs: all its raw rectangles are freshly generated,
so a non-representable anchor may legitimately leave raw output authoritative.

## Candidate data, invariants and true order

A retains a run slot within a retained topology, its first/last split endpoints, explicit
fragment roles, horizontal inputs, trailing margin, leading selector and
owner-relative line offset. A reverse dependency index maps changed sources
and adjacency intervals to runs. Distinct runs never alias through coordinates.
Split slots remain stable while the source domain survives; local joins and
splits replace only their old and new run heads' role records. Rebuilding the
source domain retires its slots together with every index that can name them.
Internal references do not escape that domain, so reused storage cannot be
observed through an old reference. Identity is context plus source-domain
lifetime plus local split and role; the lifetime needs no stored or wrapping global generation counter.
Logical publication order is separate from storage identity: the context own
rectangle comes first, runs follow first-split source order, each emits leading,
spanning and trailing roles in that order when present, then empty-inline
sources follow event and mark order. Replacement updates this logical order
without appending an early replacement behind a kept suffix. Source adjacency
is the true ordering dependency; independent rectangle evaluation is unordered.
Context replacement retires its entire identity domain. The prototypes add no
identity allocator: split indices use the existing guarded `flow_index`
conversion and role slots use existing array storage. No generation counter is
incremented or saturated; `no_index` remains missing metadata, never a fresh
identity. Any later handle that escapes topology ownership would require an
explicit non-wrapping generation and exhaustion policy before publication.

B retains the same semantic dependencies and lifetime distinction, but its
published outputs are flat rectangles. An index maps source identities and
flow intervals to disjoint rectangle slots. Source or topology replacement
updates that mapping before reuse. Geometry repair writes the actual affected
rectangles, including every translated suffix rectangle. Coincident rectangles
are separate destinations. Lookup cannot use rectangle intersection, because
negative margins and coincident geometry are valid.

Both candidates start with independent text/style preparation and speculative
paragraph breaking. Flow placement follows only margin/float/available-space
dependencies. Changed line-presence and marks select topology repair; stable
run membership permits independent endpoint, width and margin evaluation.
Each run's outputs depend on its endpoints and selectors, not on another run's
rectangle. Dependency lookup is read-only; disjoint repair destinations run
independently. Publication follows preparation of complete replacement records;
ancestor summary reduction follows the existing tree. Read-only snapshots or
function-kind parameters may expose these independent writes without shared
append cursors. A shared mutable work queue, serial run scan or global
allocation counter would add an unjustified order.

A's order ends at changed local inputs and ancestor origins; absolute
resolution belongs to dump/paint. B adds the necessary flat-output writes after
a movement is known, but those writes are mutually independent. Topology
joining has an order dependency on source adjacency, not on geometric repair
of preceding runs. Balanced summaries can discover independent runs without
serial reconstruction of the whole context. Full rebuilding of unchanged runs
is an experiment limitation, not fulfillment of bounded repair.

The i32 reference operation order is normative for both candidates. Widened
owner differences are exact i64 differences; narrowing happens at the same
observable boundary as the reference. In particular, translating a previously
clamped height is not equivalent to re-evaluating two endpoints. `no_line` and
`no_index` remain sentinels and cannot be reused as finite coordinates or live
identities. Existing saturation and structural falsifiers remain enabled.

## Status

The contract preceded the prototype. Q134 A and Q135 A are owner-approved;
implementation completeness and acceptance are separate from that selection.
The owner instructed that the design log entry wait until
[pull request #49](https://github.com/Ming-Research/Snowghost-wf/pull/49) is approved;
this work opens no pull request.
The following dated prototype evidence predates the completion validation. Independent contract
review found and fixed the empty-source line-presence/identity dependency,
publication order separate from storage identity, and the Child margin case.

Both prototypes use topology-local run-role slots aligned with the reference
fragment sequence and a balanced postorder interval index. Internal references
do not escape the topology; clearing it drops the entire index before slots
can be reused. This implements a lifetime domain rather than a wrapping global
generation counter. Kept topology retains stable split endpoints and role
slots. Topology-changing replays still reconstruct the context's split runs;
bounded topology replacement remains an explicit prototype limitation.
Text/style preparation rebuilds Open/Close marks from the unchanged Begin/End
pieces; changed text offsets do not change the owner predicates read by the
fragment builder. Box-tree reconstruction replaces the topology instead.

The first hosted layout-check sample at 7e38d03541fdf44ae6d3b383b0d8b634ac02524f
spent 10 seconds in its compiler/check step (run 37675824700), before expanding
to full correctness jobs. The first B compilation exposed a missing Styles
alias, fixed at 1c68bb5; it was a source error, not a Whitefoot gap. Obsolete
mutation run 37677062916 was cancelled after the source changed; it is no pass.

B repairs the changed range plus its translated suffix, then runs the existing
complete field comparison only over those dependency intervals. A repairs the
replayed range, retaining suffix expressions and their certificates because
their local inputs are unchanged. A's split lines are also owner-relative:
stacked openings mark raw line scratch dirty; binary source-range lookup
publishes those offsets. The existing arithmetic travel certificate is required before suffix reuse,
including convergence at a computed zero delta because saturated old positions
cannot recover the true old cursor. Exact motion preserves suffix offsets;
unsafe arithmetic replays the suffix through the original operations. Both options
keep the original full construction and certification for replaced topology.

A's no-split-line-refresh mutant disables the published mode-2 anchor
resolution and reads stale raw line scratch. The reference-only
`split_reference_line` helper is not the reader of retained suffix fragments;
its superseded queued mutation is not validation evidence. The previous dirty-publication omission was
not detected (37679193027): ordinary suffix translation no longer needs that
publication. Dropping an eliminated suffix-coordinate write is also ineffective.
The original path requirement and unmutated identity remain unchanged. The additional option-specific mutant drops the
targeted fragment-cell repair and must fail a semantic identity check. No
fixture HTML, expected dump, or block success requirement is changed.

`split-limit.py` generates low/high-origin Open and Child heads with an empty
leading fragment and plain/atomic paragraphs, followed by growth and exact
undo. Ordinary oracles require identity in seq/par. The numeric falsifier
requires unmutated identity and a detector negative control before omitting
each `reference_motion_fits` admission call separately; low-origin controls must stay identical
and a high-origin semantic difference must be observed. No expected result or
page block-splice requirement is relaxed.

The source review also found an unnecessary global repair-to-certificate
barrier. Both prototypes now evaluate the unchanged full field comparison
immediately after each leaf repair, using a shared value evaluator with narrow
immutable reads. Independent subtrees return booleans to a balanced conjunction;
only validity publication waits for the whole reduction. The separate second
index traversal is removed. Full publication uses the same evaluator and exact
comparison, including raw/missing-anchor behavior and saturating operation order.
Final timing and affected validation must use this fused revision.

The initial plain boundary probes passed, but did not exercise the exceptional
line repair: paragraph pre-breaking followed by numeric refusal forced full
stacking. Adding an unchanged atomic inline reached reference reuse and exposed
an undo mismatch in both prototypes (A run 37691741191, B run 37696134276).
The B debug dump shows the head at 33554412 px instead of the full build's
33554420 px after undo; the full hash returns to the initial hash. Saturating
`old_y + 20px`, then subtracting 20px, loses the original coordinate. The old
publication-time numeric check was too late to repair that information.

Both prototypes now require the origin/travel certificate before in-place
suffix translation and before accepting partial-stack convergence. Failed
admission continues reference replay through the suffix. The old root travel
is read once before partial stacking. A's exceptional fragment-only line repair
is retired: it cannot repair saturated endpoint geometry, and both former
call sites now require its exact-motion certificate before translation.
The numeric admission omission replaces that unreachable repair omission;
all existing fragment and targeted-cell falsifiers remain wired. [The historical-base probe](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37696128952)
also fails both growth and undo at cf12c609; its undo dump has the same lost
head coordinate. Corrected runtime validation is pending.

The numeric argument uses the existing conservative travel metadata: margins,
frames, baseline components, constrained heights, relative displacement and
atomic/float/positioned excursions are charged by absolute magnitude and
summed without wrapping. Unchanged suffix placement therefore needs the old
travel plus the proposed displacement and content-origin magnitude to remain
strictly below the i32 sentinel. Changed prefix operations retain their
reference order. The travel argument was audited in source; it is not a
machine-checked arithmetic proof. Independent omissions are configured to exercise both new
admission sites separately.

## Remaining-cost diagnostic question, before profiling

The fused hosted comparison 37684940686 still fails HTML5 font-size acceptance
for both representations. Selected pairs 23/24 and 43/44 were near A's earlier
sequential median, with reason-5 and reason-6 boundary fallbacks and thousands
of boundary visits despite few held entries. Profile those unchanged C/K pairs
on main, cf12c609, A and B using the measured drivers and verified page digest.
Two small samples select a bounded repetition count before the profiler runs.
If split-fragment work still dominates, reject the claim that the targeted
representation removes the observed cost. If boundary publication/lookup
instead dominates, the remaining bottleneck is broader reference maintenance.
This repeated-pair profile is exploratory diagnosis, includes process startup
and style preparation, and does not replace the two-round acceptance workload.

## Remaining-cost profile result

[Hosted profile 37696133904](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37696133904)
used the measured fused drivers A 3b239df449c136a2f690f5f8d16636c527a5e73f,
B 6d0286f6257a19d1375e5a4501ec3169193949c2 (renderer 1d7db04),
main 1fdb4050806ba08ca1ecd09c1e23b7cb77729ce9 and cf12c609,
with wf-0b7f5c5b9854/clang 22.1.8 on one hosted Intel Xeon Platinum 8370C
(4 vCPU, Linux 6.17.0-1022-azure). This precedes the numeric correction.
Four ten-pair samples took 2.55–2.63 seconds including startup; the bounded
rule selected 228 repetitions, or 456 measured edits, per profile.

For A, pairs 23/24 and 43/44 retained only 7 and 10 entries but accounted for
84,675 and 54,285 entries, respectively. Their boundary visits were
2,940/18,042/28,623 and 1,654/8,624/13,634 (entries/blocks/indexes), with one
reason-5 or reason-6 fallback per edit. `translate_dense_reference_suffix`
was the largest layout self-time symbol at 12.47% and 7.28%; B showed 12.62%
and 6.26%, and cf12c609 10.23% and 5.87%. No fragment repair/reconstruction
symbol reached the report's 0.5% self threshold in A's two profiles.
The profile includes startup and style work, so these percentages are not
isolated per-edit shares and do not establish a complete cost decomposition.

Source inspection agrees: the legacy reference path still translates dense
suffix scratch, then encodes/publishes boundary outputs through retained
owner indexes. Both representations optimize split fragments, not that wider
compatibility suffix. This is the remaining measured mechanism for these two
HTML font edit pairs; it does not prove every HTML font edit has the same cost.
The ordinary two-round workload remains the acceptance test. A bounded
reference-suffix representation/consumer contract is deferred in the TODO;
neither prototype claims to have solved it.

## Completion validation setup

The first completion timing attempt, [37710841463](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37710841463),
failed all four driver builds before measurement: the pinned f949 compiler's
`llvm.coro.end` return type was rejected by Clang 22. The workflow had retained
the newer compiler's toolchain while selecting the branch pin for all drivers.
The corrected workflow uses Ubuntu 24.04's native clang/lld, as this branch's
correctness workflows do, with the same f949 compiler for main, base, twin and A.
No renderer source or expected output is changed for this toolchain correction.

## Completion acceptance

[Hosted comparison 37711499602](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37711499602)
completed both rounds at workflow/renderer revision
4b37693262c7f109e23d7afd6e829ba1a318449b. Its successful job status means
measurement completed, not that adoption passed. The four independently built
cohorts are main 8fbc1601785cee70265da1eac4d99589fc6fb67c, base and twin
cf12c609e1c00f86bb431fab4e92f5dca2bf94f2, and A at the workflow revision.
Current main's renderer tree is identical to the earlier comparator 1fdb4050.
All use wf-f949e676acfa, Ubuntu Clang 18.1.3, function fragments, and the same
pages, fonts and scripts on one Ubuntu 24.04 AMD EPYC 7763 runner with four
vCPUs, Linux 6.17.0-1022-azure and WF_WORKERS=4. Round 1 runs main/base/twin/A;
round 2 reverses that order. The two one-edit HTML root-font samples both took
3.33 seconds including startup before the full batch was admitted.

The artifact holds 192 raw per-edit files, with 20 ECMA262 or 60 HTML5 edits
each, the generated scripts, revision records and machine settings. These are
upper medians of the unchanged X5 `edit us` field in microseconds, round 1 /
round 2; separately reported style timing is not added to that established
metric. A zero is the driver's reported median, not a claim of free styling.

| Page / edit / mode | main | cf12c609 | base twin | A |
|---|---:|---:|---:|---:|
| ecma262 / word / seq | 123/114 | 116/109 | 106/122 | 108/107 |
| ecma262 / word / par | 181/178 | 181/192 | 185/178 | 172/173 |
| ecma262 / sentence / seq | 257/247 | 823/803 | 946/812 | 453/484 |
| ecma262 / sentence / par | 337/324 | 724/718 | 741/746 | 517/505 |
| ecma262 / colour / seq | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 / colour / par | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 / fontsize / seq | 1701/1668 | 10290/9952 | 10857/10743 | 1519/1561 |
| ecma262 / fontsize / par | 2043/2071 | 11058/9960 | 10755/10168 | 1372/1434 |
| ecma262 / rootfont / seq | 33821/32827 | 117078/112876 | 117759/113303 | 115478/115150 |
| ecma262 / rootfont / par | 73770/72261 | 228104/223820 | 229364/226936 | 224028/222388 |
| ecma262 / block / seq | 574169/555342 | 125/115 | 116/117 | 122/129 |
| ecma262 / block / par | 415012/396201 | 198/195 | 185/184 | 194/202 |
| html5 / word / seq | 76/77 | 80/81 | 82/79 | 83/81 |
| html5 / word / par | 128/128 | 134/134 | 132/136 | 134/124 |
| html5 / sentence / seq | 237/233 | 344/337 | 378/352 | 335/350 |
| html5 / sentence / par | 343/370 | 400/374 | 391/367 | 359/394 |
| html5 / colour / seq | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 / colour / par | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 / fontsize / seq | 774/755 | 2406/2343 | 2259/2166 | 2314/2344 |
| html5 / fontsize / par | 823/824 | 2502/2501 | 2783/2576 | 2668/2632 |
| html5 / rootfont / seq | 663040/649378 | 811450/796922 | 807878/804012 | 807047/804858 |
| html5 / rootfont / par | 386491/378454 | 593840/582971 | 593779/589958 | 584867/584278 |
| html5 / block / seq | 664928/614113 | 611/573 | 588/578 | 583/589 |
| html5 / block / par | 491170/444027 | 700/687 | 706/706 | 699/698 |

Sentence edits meet the twice-main limit on both pages in both modes and rounds.
ECMA262 font-size also meets it and improves substantially over the merged base.
HTML5 font-size fails every combination: A/main is 2.99/3.10 sequential and
3.24/3.19 parallel. Its 2,314–2,668 us medians remain near the base/twin costs,
well above main's 755–824 us. The literal word/block condition is not uniformly
met either: HTML word seq round 1 is 83 vs 80 us; round-2 block medians are
129 vs 115 (ECMA seq), 202 vs 195 (ECMA par), 589 vs 573 (HTML seq), and
698 vs 687 (HTML par). The independent twin shows small-control variability;
these small overruns do not establish an isolated regression mechanism, but no
noise allowance was authorized and they cannot be declared passes.

Acceptance therefore fails and there is no merge into research/m2-layout.
Retained-run A substantially reduces ECMA font edit cost in this comparison,
but does not finish M2's broader edit-cost task.
The existing two-pair profile and unchanged source identify dense reference
suffix translation/publication as remaining work; they do not isolate all
current HTML font edits' costs. In this run, A's sequential round-1 edits
23/24 still report 7 held entries versus 84,675 logical entries and
2,940/18,042/28,623 entry/block/index visits (reason 5); edits 43/44 report
10 versus 54,285 and 1,654/8,624/13,634 visits (reason 6). These are the same
frontiers as the earlier profile, not an isolated time attribution.
Topology-changing replays also still reconstruct
the context's runs. These limits remain in docs/todo.md rather than being
presented as bounded repair for all edit kinds.

### Owner ledger after measurement

- Q132 A: approved; counted post-publication flex recovery is retained.
- Q134 A: approved representation; adoption is blocked by acceptance, not by
  an unresolved A/B choice.
- Q135 A: approved; the dependency/validity contract is recorded above.
- Q138 A (previous report label Q136): approved continuation. Complete the
  compatibility-suffix and bounded topology work, and investigate/remove the
  earlier M2 root-font regression; acceptance remains required before merging.
- Q139: open; independent owner-motion publication reopens the stored-field
  proof requirement. No sorting or inverse-array workaround is adopted.

---

**Q138 — Extend option A to finish the remaining bounded repair before adoption? (A approved)**

- **Background.** A passes the sentence and ECMA font-size timing limits, but
  HTML font-size remains 2.99–3.24 times concurrent main, and several literal
  word/block comparisons overrun the base slightly. The prior profile's two
  HTML font pairs and current source still reach
  `translate_dense_reference_suffix`; topology-changing edits also rebuild all
  runs. The approved run representation alone therefore does not meet the
  stated adoption gate.
- **Options.** A (recommended): establish the retained owner-motion/legacy-reader
  contract and bounded adjacency/topology replacement, implement the remaining
  work in A, then repeat the unchanged acceptance gates. This needs further
  investigation and implementation; other HTML costs may remain. B: park A
  without merging and retain cf12c609 on the layout line. This avoids extending
  the investigation now, but leaves the measured latency and bounded-topology
  obligations unresolved.
- **Confidence 4/5.** The same-run two-round acceptance failure is decisive.
  The precise decomposition of remaining HTML font cost is not yet isolated;
  further profiling could change which retained consumer should be addressed
  first, but not turn these measurements into acceptance.

---

### Q139: independent owner-motion writes and the stored-field proof gap

Q139 is open. The bounded suffix traversal skips unchanged descendant interiors,
but its left/node/right writes share the context and touched-slot lists. Direct
sibling moves have no CSS dependency on one another. A read-only preparation
phase, independent target writes, then reduction is the natural dependency order;
the present traversal does not establish maximal parallelism.

At the pinned Whitefoot f949e676acfa811f96b21afd07f02c06dcd14b51,
[RANGE-1](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/spec/kernel-spec.md)
allows integer element reads but says a range place selects nothing below an
element. The needed stored inverse has this form (a specification fragment,
not an admitted complete program):

```text
payloads[order[k]].entry_slot == k
```

The maintained `range5-pos-scatter-through-left-inverse.wf` conformance case
uses a separate integer inverse array. Adding proof-only inverse storage or
sorting targets solely to obtain disjoint slices would hide the same existing
Whitefoot requirement recorded in `docs/todo.md`; neither is adopted here.
This finding comes from source/specification inspection, not a new compiler
trial. Correctness and cost investigation can continue with the bounded
prototype, but its serial sibling publication is not reported as intrinsic.

- A (recommended): finish the independent evidence, hold the merge, and close
  the Whitefoot field/enum inverse-proof gap before certifying these writes.
  This preserves the project rule and delays adoption until a compiler fix
  and its pin adoption are separately authorized.
- B: explicitly accept temporary serial sibling publication while keeping the
  language requirement open. This permits assessing adoption under the latency
  gate but is a deliberate exception to maximal parallelism, not a language fix.
- Confidence 4/5: the pinned range grammar excludes the natural proof; a native
  admitted proof that needs no proof-only representation could overturn this.

## Completion correctness and review

The runtime bodies are unchanged between correctness revision
75c20f5df74775e21fee5ad7ddc8389aa80d43b0 and measured revision
4b37693262c7f109e23d7afd6e829ba1a318449b; the latter changes only a function's
doc string within renderer/. The completion changes settle the contract,
record the owner rulings, add the following-translation omission, and select
and repair the hosted timing cohort/setup. They do not claim that the inherited
prototype has gained bounded topology replacement.

- [layout-check 37711499569](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37711499569)
  and [check 37711499574](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37711499574)
  pass at 4b37693, including the DOM self-test and 21 design-checker tests.
  Design lint uses CI base 6f2235c25e01293299afd72a5fdaf5b51592b5ef and reports
  nodes 7/base 7, depth 1/base 1, decisions 60/base 53, rejected 24/base 24.
- [Oracles 37710841337](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37710841337)
  passes all 14 jobs at 75c20f5. Page dumps match reference revision
  ddfd63d0755e51f7c2972e0bb43b0c5d88fe30c7 and sequential/parallel outputs byte
  for byte: ECMA262 19,024,863 bytes and HTML5 12,538,869 bytes. Five layout
  fixture pages and the saturation fixture are also identical. All six X5
  kinds on both pages match incremental/full and seq/par: 24 page/mode files,
  960 edits, no difference or refusal. Every block edit is splice 1 reason 0:
  20 ECMA262 and 60 HTML5 per mode. Existing case refusals remain exactly the
  separately documented block/style cases; no case or fixture HTML changed.
- [Falsify 37710841485](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37710841485)
  passes all 48 jobs at 75c20f5: 46 matrix mutations, the job independently
  omitting both numeric-admission sites, and check-machinery. All inherited
  mutations stay wired. The two required added omissions are semantic
  detections after successful compilation: missing affected-fragment repair
  produces eight transfer-fixture differences; stale following spanning y
  produces 54 transfer and 16 cascade differences. Both numeric omissions
  fail growth and undo in high-origin atomic Open/Child cases while low-origin
  controls remain identical, and the detector rejects the unmutated control.

All compilation, checks and runtime measurements ran on GitHub-hosted CI.
Local work was limited to editing, source/Git inspection and reading/analyzing
CI evidence. Neither whitefoot.pin nor either submodule moved; no Whitefoot
language gap was established or filed. The first timing attempt's toolchain
mismatch is recorded above and supplies no performance evidence.

A separate read-only reviewer using the inherited default model (identifier not
exposed) examined cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 through 4b37693 plus
this completion documentation: all 18 changed files, changed regions and direct
geometry/reference/splice consumers, pipeline/layout nodes and ancestors, the
style sibling, structural contracts, and actual CI logs/artifacts. It reran no
suite. Checklist groups A/D/C/T/R/M/V and G1–G3/DC1–DC4 were covered; pin-move
T4 and PR-action V3/V4 were inapplicable. Reported outcomes and evidence pass;
M1/DC4 retain the explicitly incomplete bounded topology and adoption gate.

Review findings and dispositions: D1/M1's process-only log-approval sentence was
moved from the layout decision into this record's status section (fixed).
The targeted-repair return/certificate distinction is now explicit; inspection
found no reachable unmutated counterexample demanding a recovery path (clarified).
Bounded topology replacement and failed timing acceptance remain open under
Q138 A (now reopened by the owner's continuation). The broader reference-suffix
cost is recorded in docs/todo.md with its validation and reopening condition.
No additional correctness defect was found within scope. The general travel
argument is source-audited and probed, not universally proved; its completeness
and the full decomposition of HTML font cost remain unverified by this review.
The owner's Q134/Q135/Q132 rulings stand; a failed acceptance result does not
reopen the selected A/B representation. Approval remains with the owner.

### Lined-to-lineless revival regression

The admitted pre-line topology probe at 48b1cd0 failed its unmutated control
([job 113136419249](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37723544963/job/113136419249)) on open-plain edits 8 and 13, both removing the last newline from an independent empty inline source. The preceding insertion placed the paragraph; removing its last line left those old coordinates behind, whereas a fresh full build never places a lineless paragraph. The repair clears the freshly stacked lineless paragraph to the construction defaults before source-fragment revival, without changing untouched prefix or suffix scratch. The same unchanged probe must pass after repair.

### Cached suffix publication falsifier

The unchanged `reference-suffix` omission compiled but was not detected by the
48b1cd0 rendered-output cases ([job 113136419287](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37723544963/job/113136419287)). Previously that call published both local geometry and cached transfers. Owner motion now updates authoritative geometry first, so omitting cached publication can leave rendered dumps equal while natural-floor summaries and the block's published offset remain stale. The mutation is retained exactly; the oracle now calls `reference_publication_check` before edits. A constructed two-block suffix moves its root-owned offset from 5 to 12 with displacement 7 and a retained natural offset of 5. Independent expectations require suffix own and block-boundary natural floors of 17, root minimum 17 against the unaffected prefix's 100, published offset 12 and four virtual events. The ordinary branch must pass and the original omission must fail this assertion. The initial draft's zero displacement was corrected before CI because it contradicted the root-owned movement. This adds a cached-state discriminator without narrowing the existing rendered-output checks.
