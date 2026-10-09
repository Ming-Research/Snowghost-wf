# Split fragment dependency contract (Q134 A; Q135 A)

Current outcome: the [released inverse-proof continuation](#released-inverse-proof-and-recursive-order-storage) merges percentage-height provenance from research/m2-layout and adopts wf-01697d2de8a1 (specification v0.112). The unchanged flat stored-field loop is admitted and emits parallel tasks. Renderer integration is blocked on a natural inverse over recursive SlotPages; owner-motion writes remain serial, with no workaround adopted. Separately, the flat reachable fixture exposes unavailable proof of fields initialized by aggregate fill. Acceptance timing is deferred under the owner's instruction while Whitefoot #275's owning-element sibling serialization remains open. The [previous ten-cohort result](#root-font-continuation-ten-cohort-result) is historical: four HTML5 root-font parallel cells failed and every block cell passed. [Draft PR 55](https://github.com/Ming-Research/Snowghost-wf/pull/55) carries delivery status and deferrals. No adoption merge is authorized.

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
the historical completion comparison below. A passing result is necessary but no longer sufficient for adoption: the owner requires the Whitefoot field-step range-proof fix first. Only research/m2-frag-a may be pushed in this continuation; no adoption merge is authorized.

## Q138 continuation and root-font bisect

The owner continues Q134 A through Q138 A (the previous report called it
Q136). Finish bounded topology replacement and the owner-motion/legacy-reader
contract. The acceptance now applies a twice-main limit to word, sentence,
colour, font-size and root-font, with block no worse than cf12c609, in both
modes and rounds on the same hosted runner. The correctness gates are unchanged.
The later Q139 ruling additionally blocks adoption until Whitefoot supports independent owner-motion writes.

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

Source inference, supported by the preparation counts below: a root-font invalidation does
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

### Historical prototype evidence before Q138

The following prototype evidence predates Q138's bounded topology and owner-motion
implementation. Its topology limitations are historical, not the current contract.
Independent contract
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
- Independent owner-motion writes (Q139 A): owner-selected wait for the Whitefoot field-step range-proof fix. Keep the serial prototype explicitly waiting; no adoption even if performance passes, and no sorting or inverse-array workaround.
- Effective flow inputs and dirty frontier (Q140 A): owner-selected contract first, then bounded marked-paragraph processing, including fixtures and falsifiers for every premise. Implement this before range displacement.
- Sequence-range displacement (Q141 A): owner-selected exact contract first, then implementation and falsifiers. The contract covers old/current readers, reductions, rotations, splice lifetimes and saturation order.

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

The owner selected A: wait for the Whitefoot field-step range-proof fix before adoption, retaining the explicitly pending serial writes. The bounded suffix traversal skips unchanged descendant interiors,
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

## Earlier Q134 completion correctness and review

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

A separate read-only reviewer examined cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 through 4b37693 plus
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

### Remaining suffix and block cost profile: question before sampling

The four-cohort continuation timing passes sentence and ECMA262 font-size but
still fails ECMA262 root-font, HTML5 font-size and six block cells. HTML5's
font-size pair 23 retains seven replay entries but the instrumented A path
visits 5,339 boundary entries, 20,609 block metadata records and 41,624 index
records. These counters include newly charged direct suffix traversal; comparing
them with earlier undercounted counters does not establish increased work.
Source inspection finds separate movement and publication passes over direct
following siblings, while intact block descendants are skipped. A flat suffix
of N direct blocks still requires N origin and transfer updates.

The HTML5 block case has equal base/A visit counts but slower A timings; those
counters do not attribute the difference. Profile identical first block
insert/remove pairs and font-size pair 23/24 on frozen base, its independently
built twin and A from acceptance run 37722644051. First time two single-pair
samples on both base and A, then bound the repeated workload to about 45 seconds
of edit work using the slowest pair. Block removals advance the append-only node
ID by two per insertion. This repeated-pair workload is diagnostic, not X5
acceptance; startup and session growth remain in the profile. Reject direct
suffix traversal as the font-size explanation if its update stacks are absent;
reject a claimed block cause unless the corresponding source difference and
samples distinguish it from the twin. No new layout design is implemented by
this diagnostic job, which is removed after its evidence is captured.

### Q140: unchanged effective flow inputs

The owner selected A: settle the complete input/invalidation/consumer contract, then implement bounded dirty-paragraph processing before range displacement. The hosted effective-input diagnostic below finds unchanged
completed frame and space in ECMA262's 112,817-event flow, but 41 paragraphs
are marked on both the first 12px edit and its undo. This rejects skipping an
entirely untouched interior: the dirty paragraphs must still be processed.
The current `flow_frame` comparison computes both frames with current styles,
so it cannot prove that a restyled context has the same old inputs. Stable
snapshot endpoints do not establish that every intermediate flex input stayed
unchanged. The proposal needs both a complete input certificate and bounded
processing of the marked frontier, not merely an equality test or a cache.

- A (recommended): retain the completed effective flow inputs and define the
  exact unchanged-input admission, invalidation and consumer contract before
  implementing it, including sparse dirty-paragraph processing and propagation
  of changed outputs. Unmarked interiors could retain geometry, naturals,
  fragments and summaries. This adds per-context state and proof obligations;
  the achievable improvement still needs measurement.
- B: retain full replay and investigate its metadata or compiler costs. This
  avoids a new cache but retains work proportional to the context.
- C: park the branch without merging.
- Confidence 3/5: unchanged completed inputs and the marked frontier are now
  measured for one correctly styled pair. Transient-input admission, sparse
  propagation and sufficient improvement across the complete workload remain
  to be established.

### Q141: retained suffix-range displacement

The owner selected A: settle the exact range-displacement contract, then implement it after dirty-frontier processing. After one edited paragraph followed by N direct block siblings,
current owner-relative geometry requires N sibling origins and cached transfer
updates even though each block's interior is unchanged. Native independent
scatter (Q139) would expose parallelism but would not remove these visits.
In the integrated 6bf0d0e comparison HTML5 font-size takes 1,991/1,859 us parallel
against main's 761/526 us. Cursor reuse removes 14.28% of index reads but none
of these payload updates, without establishing a general latency gain.

- A (recommended): develop retained exact displacement on sequence-index
  ranges, including old/current reads, cached reductions, split endpoints,
  rotations, splice lifetimes and saturation. This can replace sibling-wide
  updates with boundary-path work but is a broader representation contract.
- B: retain direct sibling publication and investigate constant costs only.
  This keeps the present representation and its linear suffix work; no timing
  evidence yet establishes that constant improvements meet the gate.
- C: park the branch without merging.
- Confidence 4/5 that removing the linear visits needs a changed representation;
  their complete timing contribution and achievable acceptance remain empirical.

The independent-write ruling remains binding: both implementation directions proceed, but neither permits adoption before the Whitefoot proof fix.

### Q138 four-cohort acceptance at 0dc2e5e

[Run 37722644051](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37722644051) passed its measurement workflow with 192 raw timing files and 7,680 edit records. This table measures 0dc2e5ee7abcc78c2c7b90b8e7975a8776b8608a, before the later lined-to-lineless correctness repair and oracle additions; it is failure evidence, not acceptance of a later revision. All cohorts use wf-0b7f5c5b9854, LLVM 22, WF_WORKERS=4 and identical scripts on one Ubuntu 24.04 AMD EPYC 7763 hosted runner exposing four vCPUs, Linux 6.17.0-1022-azure. Columns are upper median edit microseconds, round 1 / round 2; separate style time is excluded.

| Page | Kind | Mode | Main | cf12c609 | cf12 twin | A | Result |
|---|---|---|---:|---:|---:|---:|---|
| ecma262 | word | seq | 112/100 | 106/105 | 116/106 | 107/107 | passes |
| ecma262 | word | par | 161/169 | 173/180 | 197/178 | 194/186 | passes |
| ecma262 | sentence | seq | 240/236 | 846/717 | 724/775 | 169/150 | passes |
| ecma262 | sentence | par | 352/330 | 742/660 | 694/693 | 230/239 | passes |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| ecma262 | fontsize | seq | 1986/1314 | 9799/9437 | 9659/9312 | 609/588 | passes |
| ecma262 | fontsize | par | 2086/2102 | 9837/9473 | 8947/9468 | 1100/1148 | passes |
| ecma262 | rootfont | seq | 33198/31088 | 122099/116972 | 118760/116894 | 117447/114678 | fails r1,r2 |
| ecma262 | rootfont | par | 69565/68907 | 226799/222314 | 222385/220962 | 188655/188117 | fails r1,r2 |
| ecma262 | block | seq | 570280/554167 | 117/121 | 119/113 | 120/123 | fails r1,r2 |
| ecma262 | block | par | 400435/390379 | 201/187 | 208/182 | 189/196 | fails r2 |
| html5 | word | seq | 73/73 | 81/81 | 79/83 | 80/81 | passes |
| html5 | word | par | 122/121 | 132/132 | 126/131 | 127/125 | passes |
| html5 | sentence | seq | 240/224 | 361/320 | 323/343 | 374/362 | passes |
| html5 | sentence | par | 349/334 | 387/376 | 358/350 | 389/379 | passes |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| html5 | fontsize | seq | 898/673 | 2186/1820 | 1887/1851 | 1742/1421 | fails r2 |
| html5 | fontsize | par | 892/794 | 2303/2164 | 2370/2183 | 2100/1881 | fails r1,r2 |
| html5 | rootfont | seq | 635084/630093 | 783877/779067 | 783720/777928 | 782826/785511 | passes |
| html5 | rootfont | par | 368650/367799 | 572984/572601 | 568968/568400 | 543432/541945 | passes |
| html5 | block | seq | 655266/671965 | 583/575 | 571/579 | 634/622 | fails r1,r2 |
| html5 | block | par | 474319/456200 | 682/769 | 653/665 | 725/707 | fails r1 |

Acceptance fails 13 of 48 cells: four ECMA262 root-font cells, three HTML5 font-size cells and six block cells. The control twin records variability but does not waive any failed threshold. Main and base source revisions are frozen as in the root-font bisect above. The subsequent investigation and Q140/Q141 record the remaining work; no merge is authorized by this result.

The four-cohort pin-only children are main `7207d33e71bccdfcc51d2733cd70f0d2643ee53e`, base `bcec4b22e7a9d262836b646f1884ba9fa44c00ed`, twin `3702353f977b0c221f2bde88c8cda1f6a9f46f2b` and A `b8ecf9ba41f511fd9806e3684d86cc2c7f654b79`. Their exact patches and source identities are in that run’s `edit-cost-evidence` artifact; no pin-only child was pushed or adopted.

### Parallel reduction repair from completion review

The review found two added chains not covered by Q139's stored-field write
limitation: the old/new head union used serial cursors, and touched-owner motion
used a serial early-return scan. The union now partitions the source domain,
counts both nominee halves independently, then fills disjoint output slices
whose offsets depend only on those counts; empty subtrees prune immediately.
Owner motion now uses a balanced read-only Boolean reduction. No retained
representation or accepted rendering behavior changes. The additional count
work and compiler/runtime results require validation at this new revision;
earlier timings remain evidence of failure, not a performance claim for it.

### Suffix profile result and ordinary-origin hypothesis

[Hosted profile 37726861963](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37726861963) succeeded with the frozen four-cohort acceptance drivers. It used sequential mode, WF_WORKERS=4, wf-0b7f5c5b9854 and perf 499 Hz with 4096-byte DWARF stacks on Ubuntu 24.04, AMD EPYC 7763, four exposed vCPUs, Linux 6.17.0-1022-azure. Two single-pair samples per base/A took 2.73–2.82 seconds including startup. Their edit costs selected 30,000 block round trips (the cap) and 6,997 font-size round trips. These repeated-pair profiles include startup and session growth; they are neither the full X5 script nor acceptance timings, and symbol percentages are not exclusive edit-time shares.

For HTML5 font-size pair 23/24, base and twin spend 21.72/21.71% self samples in `translate_dense_reference_suffix`; A has removed that function. A instead shows `move_reference_payload` 6.06%, `publish_reference_owner_suffix` 5.59%, `reference_owner_cursor` 5.59% and `move_reference_owner_suffix` 2.41%, plus cached-output stores and unresolved libc descendants of those stores. This supports the source account of remaining direct-sibling movement and publication, without assigning unresolved libc symbols a specific implementation. Upper median edits were base 2,336 us, twin 2,393 us and A 1,788 us over 13,994 edits each; it does not establish the full-script 2x gate.

For the first HTML5 block pair, base/twin/A upper medians were 294/294/327 us over 60,000 edits each. Separating insertion and removal gives 315/315/349 us and 243/243/277 us. A's `retained_block_origin` accounts for 10.07% self samples, while both controls' largest costs remain splice positioning. The new phase-aware origin reader is therefore a candidate for the approximately 34 us paired overhead, not yet an isolated cause.

Before the repair experiment: ordinary owned geometry depends only on local x/y/dx/dy and parent links. Both production setters of `local_geometry = True()` first call `finish_reference_geometry`, clearing touched replay flags and selecting phase zero. Captured origins, freshness flags and raw replay scratch are outside that phase's input closure. Separate this ordinary traversal from the unchanged old/current replay traversal, and extend the independent frame oracle through publication and retirement. This removes unnecessary state reads; it is not an attempt to respell the same operations to hide a compiler limitation. Compare the same source immediately before/after this change, with an independently built before twin and unchanged compiler/inputs on one hosted runner. Reject the cost hypothesis if block timings do not separate from control spread; preserve all old/current frame and suffix omission checks. Root-font and indexed suffix-range proposals remain awaiting Q140/Q141.

### Block-only attribution after the six-cohort comparison

The db46e92 six-cohort comparison rejects the ordinary-origin block-cost
hypothesis: A's block medians overlap its immediate-before twin or are slower,
and seven block cells still exceed cf12c609. No isolated block improvement is
claimed. The earlier whole-process profile cannot separate startup from edit
samples, although source inspection confirms owner reads occur in both.

Before another repair: sample the frozen final base, base twin and db46e92
drivers on the same repeated first HTML5 block pair, delaying perf collection
by five seconds. Timestamp the base record and first edit on stdout and require
both before the delay, so the sampled interval excludes startup by observed
evidence. Keep the existing two single-pair samples and bounded repetition
calculation. This diagnostic is not the full X5 acceptance script. Reject a
remaining owner-walk attribution if those symbols are absent after startup.
`child_motion_travel` currently obtains its owner then `child_origin` repeats
that ancestry in the ordinary phase; reuse of the same immutable origin would
remove duplicate work without changing representation, viewport ownership or
saturation order, but its cost contribution is not yet established. No compiler
limitation or new block representation is inferred from function percentages.
The temporary profile job is removed after its evidence is captured.

### Q138 six-cohort acceptance at db46e92

[Run 37728270804](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37728270804) succeeded with 288 raw timing files and 11,520 edit records. The measured source is db46e9218eb3b53550148843a0c3f433e5c113e4; immediate-before and its independently built twin are 03a3d3ebc2f826c3c40aa6179237aa5819c4b39b. Main and cf12c609 retain the frozen source revisions above. All six cohorts use wf-0b7f5c5b9854, LLVM 22 and WF_WORKERS=4 on one Ubuntu 24.04 AMD EPYC 7763 hosted runner, four exposed vCPUs, Linux 6.17.0-1022-azure. Two rounds use forward/reverse cohort order. Values are upper median edit microseconds, round 1 / round 2, excluding separately measured style time.

| Page | Kind | Mode | Main | cf12 | twin | before | before twin | A | Result |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| ecma262 | word | seq | 104/102 | 108/106 | 106/112 | 108/107 | 109/108 | 117/112 | passes |
| ecma262 | word | par | 174/171 | 183/186 | 185/178 | 175/180 | 179/186 | 176/177 | passes |
| ecma262 | sentence | seq | 231/227 | 734/802 | 705/739 | 164/150 | 147/146 | 151/148 | passes |
| ecma262 | sentence | par | 334/300 | 741/673 | 762/730 | 232/234 | 246/239 | 241/232 | passes |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| ecma262 | fontsize | seq | 1419/1614 | 9408/9993 | 9155/9041 | 869/850 | 874/937 | 577/568 | passes |
| ecma262 | fontsize | par | 2355/1925 | 9431/9524 | 9455/10116 | 834/912 | 882/810 | 848/836 | passes |
| ecma262 | rootfont | seq | 30250/28979 | 116154/117899 | 111570/115859 | 111291/114405 | 111537/113402 | 113769/112539 | fails r1,r2 |
| ecma262 | rootfont | par | 68528/67792 | 222458/223198 | 220357/226586 | 185846/188312 | 187410/190318 | 191676/186910 | fails r1,r2 |
| ecma262 | block | seq | 530213/524230 | 113/113 | 119/116 | 117/119 | 119/128 | 119/125 | fails r1,r2 |
| ecma262 | block | par | 378708/377834 | 188/190 | 190/212 | 210/198 | 206/189 | 190/188 | fails r1 |
| html5 | word | seq | 75/73 | 79/82 | 80/81 | 85/79 | 81/82 | 81/79 | passes |
| html5 | word | par | 121/119 | 129/127 | 128/130 | 126/128 | 130/130 | 129/129 | passes |
| html5 | sentence | seq | 231/230 | 328/322 | 338/333 | 373/372 | 362/396 | 376/362 | passes |
| html5 | sentence | par | 313/312 | 376/366 | 370/378 | 406/406 | 385/402 | 385/405 | passes |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| html5 | fontsize | seq | 666/702 | 1860/1939 | 1735/2010 | 1578/1468 | 1468/1532 | 1437/1426 | fails r1,r2 |
| html5 | fontsize | par | 720/751 | 2202/2158 | 2100/2126 | 2184/1977 | 2172/2032 | 2065/2089 | fails r1,r2 |
| html5 | rootfont | seq | 616788/615236 | 770995/771687 | 768497/770434 | 774083/774906 | 779006/772078 | 772916/771384 | passes |
| html5 | rootfont | par | 357834/359159 | 567345/570063 | 567905/570159 | 538796/540888 | 538971/538381 | 543208/549456 | passes |
| html5 | block | seq | 603430/598779 | 564/576 | 569/569 | 603/597 | 613/594 | 619/596 | fails r1,r2 |
| html5 | block | par | 437996/431620 | 667/651 | 657/658 | 695/716 | 710/715 | 718/710 | fails r1,r2 |

Acceptance fails 15 of 48 cells: all four ECMA262 root-font cells, all four HTML5 font-size cells, and seven block cells. No merge follows this result. The base twin's spread does not waive literal failures. Before/before-twin/A block timings overlap or A is slower, rejecting an isolated block benefit from the ordinary-origin specialization. ECMA262 sequential font-size improves from before 869/850 and before twin 874/937 to A 577/568 us; this limited observation supports neither a general speed claim nor a root-font repair. The ordinary-phase input closure remains valid, but its proposed block-cost explanation is rejected.

Pin-only children are main `5e604f4902b7fc3edcf0b5df8d3b480ccc507655`, base `7af638017c4ce4735cae6df33d52e1ead825f49c`, twin `c7ad220d44f752f0cdc4b99bbd62d4f5528d8cff`, before `7fe57971ffc8d7333787d5454c01eb3e70f6babc`, before twin `1c54525b6d1439cf54b4fda018d2c5fbe08b802a` and A `30ebc091e3837d72fec63aff2214689c0d0c6d22`. Exact patches/source identities accompany that run's `edit-cost-evidence`; none is pushed or adopted.

The first-round root-font counters still prepare 41 paragraphs in ECMA262. Main reports three contexts, zero rebroken paragraphs and one entry; A reports four contexts, 41 rebroken paragraphs and 112,823 entries (112,817 held). Those counters include the previously described flex-accounting distinction and do not alone prove additional descendant reflow. HTML5 main and A both prepare 60,867–60,868 paragraphs, rebreak 60,868, visit 13,903 contexts and report 105,989 entries. Separate style upper medians are ECMA262 main/A 3,989/4,286 us sequential and 4,924/5,048 parallel; HTML5 290,437/293,647 sequential and 192,845/195,868 parallel. The mandatory floor is actual style dependencies, changed text preparation and dependent reflow; these measurements establish no universal numeric lower bound. Main's observed edit path is the practical comparison. Q140 remains an unimplemented unchanged-input proposal, not a claim that all root-font work can disappear.

### Child-motion owner reuse: question before matched measurement

The local-phase source computes the same immutable owner once for travel
charging and again inside `child_origin`. Reuse the first value for the child
anchor, with zero owner for viewport placement, while preserving both
`origin_accumulate` and every subsequent saturated add/subtract in their
existing order. Replay phases continue through `child_origin`. This removes
one ancestry traversal and adds no state, memoization key or shared ordering.
The unchanged positioned, atomic, transfer-travel and numeric-admission cases
exercise the affected behavior.

The delayed profile of frozen db46e92 proceeds independently of this candidate's
correctness and matched timing. Compare candidate versus db46e92 and its
independent twin, together with main/cf12/cf12-twin, on one hosted runner with
the full two-round six-kind script. Reject a block-cost attribution if its
medians do not separate from both before controls. All correctness gates remain
required; no profile percentage alone establishes an acceptance improvement.

### Q138 correctness and review at db46e92

The complete runtime revision db46e9218eb3b53550148843a0c3f433e5c113e4 passes
[layout-check 37728270697](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37728270697),
[check 37728270906](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37728270906),
[oracles 37728270744](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37728270744)
and [all 53 falsification jobs 37728270791](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37728270791).
This is the revision measured in the six-cohort table above; the subsequent
child-owner reuse candidate requires its own validation.

The oracle run passes all 14 jobs. Full ECMA262 and HTML5 dumps are byte-identical
to the oracle's frozen ddfd63d base and across sequential/parallel modes
(19,024,863 and 12,538,869 bytes); five layout cases and the saturation fixture
are also unchanged. All six X5 kinds yield 24 raw files, 960 incremental/full
matches, zero differences/refusals, and 12 byte-equal normalized seq/par pairs.
All page block paths are splice 1, reason 0: 20 ECMA262 and 60 HTML5 per mode.
The new topology matrix yields 384 matches across both modes; split-limit and
near-limit probes yield 32 and 40 matches respectively, with no differences or
refusals in these probes. Existing separately counted case refusals remain.

The exact original `reference-suffix` mutation is detected by the independent
cached-publication assertion. The missing-repair omission produces eight
transfer-fixture differences; missing following translation produces 54 transfer,
16 cascade and 16 reference-frame differences. The topology omission's baseline
has 192 matches, its negative control correctly rejects an undistinguished
result, and the compiled mutation produces 48 differences across all 12 variants.
Old-frame and natural-floor omissions are also detected. No mutation or expected
result was weakened. The lineless reset, source-retention lifetime and cached
publication regressions are fixed within their exercised scope.

A separate read-only reviewer inspected the full 30-file cf12c609..db46e92 diff, changed regions and
direct consumers, the pipeline/layout, pipeline, style and scope decisions,
and the actual hosted logs/artifacts. No suite was rerun. RV1–RV3 corrected
lineless-coordinate, style-floor and source-index lifetime documentation. RV4
corrected the constructed publication oracle's displacement before validation.
RV5 removed serial chains from the pure head union and owner-motion reduction.
The owned-origin specialization and subsequent local child-owner reuse received
separate narrow source review; runtime evidence for the latter is pending.

Groups A/D/C/T/R/M/V and G1–G3/DC1–DC4 were examined; pin-move checks and PR
operations are inapplicable because no dependency moved and the owner forbids
PR actions. Q139 remains an explicit R3/G2/DC2 finding against maximal
parallelism. Numeric/source-retention soundness beyond inspected paths and
probes, and independent Chromium conformance of the new generated topology
pages, remain unverified; existing external fixtures remain intact. DC4 and
full task acceptance remain incomplete because the timing gate fails. The
check log passes the DOM self-test, 21 checker tests and design lint. Lint's
CI base reports 7 nodes/depth 1/62 decisions/24 rejections against 53 decisions;
source counts against review base cf12 are 7→7 nodes, depth 1→1, 59→62 decisions
and 24→24 rejections. Only the layout node changes. Owner approval is not
supplied by review.

All compilation, execution and checks ran on GitHub-hosted CI. Local work only
inspected/edited source and Git state and analyzed downloaded evidence. The
Whitefoot pin and both submodule revisions are unchanged. Q139 records the
existing field/enum inverse-proof requirement in the TODO; no external issue
or compiler workaround was introduced.

### Delayed block profile: startup excluded, sample loss limits attribution

[Run 37733734625](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37733734625) succeeds with the frozen db46e92/base/twin drivers. First edits arrive 2.34–2.48 seconds after launch, before sampling starts at five seconds; total runs last 20.03–22.03 seconds. The two-edit samples took 2.25–2.30 seconds and selected the existing 30,000-round-trip cap. All three runs contain 60,000 edits; upper medians are base 245 us, twin 243 us and A 273 us. These instrumented repeated-pair medians are diagnostic, not acceptance.

Post-startup samples include A's block-origin and child-motion-travel reads, so those operations are not confined to startup. However, perf reports 39,542/35,244/41,288 lost samples for base/twin/A. No quantitative attribution is accepted from these percentages. Repeat the same frozen comparison at 99 Hz with a 1,024-page buffer instead of the 499 Hz default-buffer setup; retain the observed startup markers and admission controls. This repeat repairs measurement loss, not a failed performance threshold, and cannot replace the full-script acceptance comparison.

The [99 Hz repeat 37735300953](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37735300953) also completes, on an Intel Xeon Platinum 8573C hosted runner with four exposed vCPUs, Ubuntu 24.04/Linux 6.17.0-1022-azure. It uses the same wf-0b7f5c5b9854 drivers, WF_WORKERS=4, DWARF 4096-byte stacks and observed five-second delay. First edits arrive at 2.22–2.45 seconds, total runs last 20.03–22.03 seconds, and base/twin/A upper medians are 245/244/273 us over 60,000 edits each. The buffers reduce but do not eliminate loss: 3,354/2,498/5,991 samples are lost. Percentages still supply no reliable quantitative attribution. Both delayed runs establish that owner reads occur during the edit interval; neither establishes their exclusive cost. The source-level duplicate-walk removal is judged by its independent full-script before/twin comparison. No compiler defect is established, and no renderer spelling workaround follows from these profiles. The temporary profiling job is removed after capturing this evidence.

### Q138 six-cohort acceptance at 8ab7dc6

[Hosted run 37734202554](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37734202554) completes all 288 raw files and 11,520 edits at runtime revision 8ab7dc6151548a1268eff6be0af4db2bdc5f1d79. This is the current acceptance result. The runner is Intel Xeon Platinum 8573C with four exposed vCPUs, Ubuntu 24.04/Linux 6.17.0-1022-azure; LLVM 22, wf-0b7f5c5b9854 and WF_WORKERS=4 are shared across all cohorts. The workflow interleaves all six kinds in forward/reverse rounds. Values are upper-median edit microseconds, round 1/round 2; separate style time is excluded. Before and before twin are independently built db46e92. No result is compared numerically across hosted machines.

| Page | Kind | Mode | Main | cf12 | cf12 twin | Before | Before twin | A | Failed rounds |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| ecma262 | word | seq | 83/88 | 92/105 | 89/96 | 87/88 | 88/92 | 88/87 | pass |
| ecma262 | word | par | 114/134 | 123/153 | 125/124 | 122/120 | 119/121 | 124/124 | pass |
| ecma262 | sentence | seq | 267/270 | 755/760 | 840/751 | 125/129 | 128/128 | 130/129 | pass |
| ecma262 | sentence | par | 306/304 | 686/679 | 665/716 | 189/190 | 191/191 | 190/195 | pass |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| ecma262 | fontsize | seq | 1840/1778 | 8252/9271 | 7217/8863 | 1210/1278 | 1223/1069 | 1274/1023 | pass |
| ecma262 | fontsize | par | 1859/1806 | 9282/9970 | 8445/9556 | 1297/1514 | 1275/1361 | 1282/1025 | pass |
| ecma262 | rootfont | seq | 20501/18265 | 92296/90419 | 72139/85586 | 80919/79324 | 81403/66098 | 84149/73260 | 1,2 |
| ecma262 | rootfont | par | 58137/54725 | 226287/235503 | 213490/227136 | 178271/184706 | 180536/174279 | 182446/171797 | 1,2 |
| ecma262 | block | seq | 494459/479464 | 111/104 | 88/98 | 100/99 | 97/114 | 100/97 | pass |
| ecma262 | block | par | 381958/365497 | 163/167 | 157/174 | 149/146 | 149/162 | 160/170 | 2 |
| html5 | word | seq | 65/62 | 68/70 | 64/71 | 74/70 | 67/69 | 70/66 | pass |
| html5 | word | par | 92/99 | 94/101 | 93/97 | 90/92 | 91/92 | 92/100 | pass |
| html5 | sentence | seq | 215/194 | 284/306 | 317/280 | 320/307 | 315/315 | 310/302 | pass |
| html5 | sentence | par | 258/254 | 286/275 | 282/291 | 355/327 | 311/366 | 386/354 | pass |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| html5 | fontsize | seq | 779/765 | 1834/1985 | 1907/2003 | 1641/1689 | 1682/1650 | 1692/1620 | 1,2 |
| html5 | fontsize | par | 719/713 | 2134/2265 | 2213/2132 | 2165/2121 | 2104/2169 | 2152/2144 | 1,2 |
| html5 | rootfont | seq | 555087/552385 | 666760/670845 | 665728/670486 | 672712/685475 | 682833/679418 | 679275/681699 | pass |
| html5 | rootfont | par | 320095/321214 | 534921/541898 | 531449/536308 | 487662/494608 | 498398/496535 | 487359/487448 | pass |
| html5 | block | seq | 557116/602209 | 534/572 | 584/540 | 576/583 | 567/581 | 550/597 | 1,2 |
| html5 | block | par | 438537/450722 | 607/628 | 634/610 | 671/663 | 689/667 | 635/651 | 1,2 |

Acceptance fails 13 of 48 cells: four ECMA262 root-font cells, four HTML5 font-size cells and five block cells. No merge is authorized. Word, sentence, colour, ECMA262 font-size and HTML5 root-font satisfy the unchanged twice-main threshold in both modes and rounds. Base-twin variation does not waive any block failure.

The local child-owner reuse has a limited HTML5 parallel block improvement: A 635/651 us versus before 671/663 and before twin 689/667. It does not establish a general block improvement: ECMA262 parallel A 160/170 is above before 149/146 and before twin 149/162, and sequential results overlap controls or reverse between rounds. The general block-cost hypothesis is rejected; the change removes a source-level duplicate immutable ancestry walk while preserving viewport and saturation behavior. Full current correctness gates remain pending. Q140/Q141's unimplemented changes remain owner decisions; this result neither proves their sufficiency nor changes acceptance.

Exact source and isolated pin children (not pushed or adopted):

- `a source=8ab7dc6151548a1268eff6be0af4db2bdc5f1d79 pin-commit=1e14641538e83731dd4e0adea6d0a39bd53d32a1 release = wf-0b7f5c5b9854`
- `base source=cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 pin-commit=2fbd066f66c8898ccb9faff19db0b03519409120 release = wf-0b7f5c5b9854`
- `before source=db46e9218eb3b53550148843a0c3f433e5c113e4 pin-commit=19591a42a64ba01436ea9a560a66df8da05dd01f release = wf-0b7f5c5b9854`
- `beforetwin source=db46e9218eb3b53550148843a0c3f433e5c113e4 pin-commit=16dd9f02092fc83ae07e8f6ab9cab1709bff3a00 release = wf-0b7f5c5b9854`
- `main source=8fbc1601785cee70265da1eac4d99589fc6fb67c pin-commit=9a0482d3d0ff6b278aa686299909fd16e0a88780 release = wf-0b7f5c5b9854`
- `twin source=cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 pin-commit=cc6cb9a271bb5bbb4bbd2086e78fae10254a1763 release = wf-0b7f5c5b9854`

The current first-round counters confirm the same scope distinction: ECMA262 prepares 41 paragraphs on both main and A, while A reports 112,823 entries (112,817 held) versus main's one entry. The flex-accounting distinction still prevents interpreting this as a count of extra descendant reflows. HTML5 prepares 60,867–60,868 paragraphs on both and rebreaks 60,868 across 13,903 contexts and 105,989 reported entries. Separate style medians main/A are ECMA262 4,284/4,380 us sequential and 4,642/4,901 parallel; HTML5 260,910/255,110 sequential and 177,251/174,014 parallel. Full cost includes style plus edit work: the unavoidable work is actual style invalidation and changed preparation/dependent layout, not every retained metadata publication. Neither the counters nor these timings prove a universal numeric floor. Main's same-run path supplies the observed comparison; retained effective inputs under Q140 remain unproved and unimplemented.

### Positioned-certificate owner reuse: question before measurement

The positioned-child plan already captures the owning block's resolved origin. Child settlement writes only that child; preceding certificate publication propagates a zero geometric delta, so neither step changes the captured parent frame. Pass that existing origin into the exact travel computation instead of resolving its ancestry again. This adds no retained state or new invalidation rule. The helper preserves its guarded read, viewport placement, hybrid reader fallback and every saturating operation in order. Preparation, independent child writes and dependent certificate reductions retain their existing dependencies. This duplicate walk existed at cf12 as well: removing it is a general cost reduction, not an established cause of the block regression.

Compare the complete six-kind two-round workload at the candidate against 8ab7dc6 and an independently built 8ab7dc6 twin, alongside main/cf12/cf12 twin on one hosted runner. Reject a general block improvement if the result does not separate from both before controls across pages/modes/rounds. Preserve all positioned/atomic, arithmetic, old/current reader and omission gates; a passing measurement workflow alone is not task acceptance.

### Validation of the preceding child-owner reuse at 8ab7dc6

[Oracles 37734202620](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37734202620) completes all 14 jobs at 8ab7dc6. The main dump and fixture evidence is unchanged; all six X5 kinds yield 24 raw files, 960 incremental/full matches, no differences/refusals, and 12 byte-equal normalized sequential/parallel pairs. Every block path is splice 1 reason 0 (20 ECMA262 and 60 HTML5 per mode). Topology, split-limit and near-limit artifacts contain 384, 32 and 40 matches respectively. The separate reviewer independently verified these artifacts and the 288-file timing result. Layout-check 37734202492 and check 37734202410 pass at this revision. Falsify 37734202403 was cancelled with only a partial result when the next source revision superseded it; it is not a passing full gate. Revision 87baa10 runs all 53 unchanged falsification jobs and all other gates afresh.

### Q138 six-cohort acceptance at 87baa10

[Hosted run 37740867583](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37740867583) completes 288 raw files and 11,520 edits at 87baa109d4d3eb26c4a6726a43a26d3a5a061d28. All cohorts use one AMD EPYC 9V74 hosted runner exposing four CPUs, Ubuntu 24.04/Linux 6.17.0-1022-azure, LLVM 22, wf-0b7f5c5b9854 and WF_WORKERS=4. Before/before twin are independent builds of 8ab7dc6. Values below are upper-median edit microseconds, round 1/round 2, excluding separate style time.

| Page | Kind | Mode | Main | cf12 | cf12 twin | Before | Before twin | A | Failed rounds |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| ecma262 | word | seq | 81/81 | 86/85 | 86/86 | 88/88 | 87/87 | 87/88 | pass |
| ecma262 | word | par | 137/125 | 134/134 | 146/133 | 135/133 | 134/134 | 135/144 | pass |
| ecma262 | sentence | seq | 190/201 | 603/638 | 609/615 | 126/131 | 128/129 | 128/126 | pass |
| ecma262 | sentence | par | 240/249 | 493/550 | 534/485 | 186/192 | 201/190 | 191/200 | pass |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| ecma262 | fontsize | seq | 1346/1791 | 8027/9540 | 9579/8233 | 535/497 | 537/594 | 525/944 | pass |
| ecma262 | fontsize | par | 1492/1956 | 8752/9275 | 8520/8497 | 953/1165 | 854/694 | 729/856 | pass |
| ecma262 | rootfont | seq | 30358/31682 | 118645/118871 | 118474/118220 | 118605/117731 | 117499/119200 | 116646/118377 | 1,2 |
| ecma262 | rootfont | par | 59360/59535 | 200266/202178 | 200658/198647 | 168721/169760 | 168544/171063 | 172196/170613 | 1,2 |
| ecma262 | block | seq | 524782/530055 | 102/103 | 102/101 | 107/110 | 106/105 | 107/105 | 1,2 |
| ecma262 | block | par | 348380/353444 | 171/159 | 158/159 | 162/159 | 163/168 | 158/159 | pass |
| html5 | word | seq | 60/60 | 66/66 | 69/68 | 68/65 | 64/66 | 65/69 | pass |
| html5 | word | par | 98/95 | 99/100 | 105/103 | 100/100 | 100/100 | 99/100 | pass |
| html5 | sentence | seq | 176/177 | 291/285 | 282/291 | 294/292 | 304/303 | 274/276 | pass |
| html5 | sentence | par | 236/264 | 288/293 | 285/285 | 309/301 | 298/317 | 312/305 | pass |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | pass |
| html5 | fontsize | seq | 508/533 | 1857/2383 | 1673/1883 | 1411/1331 | 1359/1370 | 1369/1365 | 1,2 |
| html5 | fontsize | par | 512/521 | 1931/2058 | 1928/1858 | 1830/1732 | 1767/1840 | 1849/1805 | 1,2 |
| html5 | rootfont | seq | 541017/543334 | 679527/693070 | 682739/681402 | 691355/696390 | 690703/694283 | 684408/689985 | pass |
| html5 | rootfont | par | 291044/292823 | 483197/487761 | 480868/485056 | 459842/458468 | 459428/459935 | 457711/465139 | pass |
| html5 | block | seq | 612555/615238 | 496/511 | 506/512 | 524/537 | 516/537 | 503/531 | 1,2 |
| html5 | block | par | 417127/433287 | 576/584 | 565/575 | 592/587 | 592/607 | 565/577 | pass |

The strict per-round edit-only comparison fails 12 of 48 cells: ECMA262 root-font and HTML5 font-size in both modes/rounds, and both pages' sequential block cells. Parallel block cells pass. Twin spread is recorded but does not independently waive the literal block gate. The owner's best-round style-plus-update numbers are also reproduced: ECMA262 root-font A/main 120,848/34,668 us sequential and 175,407/63,953 parallel; HTML5 font-size 1,442/574 sequential and 1,933/633 parallel. These are paired per-edit style-plus-update medians, not sums of separately computed medians, and both failing kinds remain above twice main. The certificate-owner reuse establishes no general improvement over before and its twin.

All correctness gates pass at this runtime revision: [layout-check](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37740867579), [check](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37740867746), [oracles](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37740867504) and [falsify](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37740867651). The 14 oracle jobs retain byte-identical page and fixture dumps, 960 X5 matches without differences/refusals, 12 equal seq/par pairs and all page block paths splice 1 reason 0. Topology/split-limit/near-limit probes retain 384/32/40 matches. All 53 falsification jobs pass, including the required omissions. A separate read-only reviewer independently verified the complete measurement and identity artifacts. No merge into the layout line follows this failed acceptance.

### Integration of the Apollo11 repair

The layout line advanced to d13e18cdc7593bd392109955933ad8cb17981022. Integration keeps its private retained-sibling top-margin replacement and all three new regression scripts, including the unsupported new-context refusal. The reference conflict retains the hybrid old/current-frame reader contract. Its suffix guard already includes independently detected replayed-owner motion as well as net flow displacement; thus zero flow displacement does not skip the moved-owner rebasing that the Apollo sentence regression needs. It avoids adding unconditional publication when both frames and flow remain unchanged. The combined oracle must pass the sentence-convergence case, and the combined zero-suffix falsifier removes the owner-motion term, restoring the same semantic omission as the former delta-only guard. Every other mutation and fixture remains wired. The public interface retains the independent cached-publication oracle and adopts the sibling-frontier contract wording. Full correctness and timing must be rerun after integration before adoption.

### Hybrid suffix cursor reuse: question before measurement

Both hybrid traversals read the left child's cursor to locate a suffix and then reread it at recursive entry. Pass the already read cursor, as the raw reference traversal already does; read and charge root, right and nested cursors once at their callers. Coordinate changes and transfer publication preserve links, liveness and event counts. This removes a duplicated metadata read and its matching physical-visit increment, without changing payload counts, phase order, admission, saturation or the existing left/own/right association. A separate read-only reviewer checked those dependencies and every call site. Compare against the integrated 48cfbeb source and its independently built twin in the full same-host two-round cohort; reject a speed attribution unless before/twin controls separate from the candidate. All combined correctness gates, including both Apollo omissions, remain required.

Direct fusion of movement and publication is not a local repair: movement precedes used-height, positioned-child and fragment settlement, whereas publication consumes their final outputs and follows the old-root admission check and replayed-prefix publication. Moving either phase across those dependencies requires a new argument. With the current representation, a translated suffix of N direct Open siblings still needs N individual origins and N cached motion summaries updated; moving the root would incorrectly move the prefix. Removing that linear work requires the range-displacement contract proposed in Q141, although this lower bound proves no particular timing ratio.

### Root-font admission input audit

At the integrated source, a local style change sets `restyled`; bounded update refuses it, update_flow materializes the entire event sequence, the steady reference path excludes it, and nonpartial completion publishes all transfers and owned geometry. Existing Context space/width/output fields do not retain the completed FlowFrame's content origin, definite content height and column inputs. The apparent previous-frame calculation reads current styles with previous space/width, so it cannot establish old-frame equality after a local restyle. Static source-domain split indexes now survive this replay, but dynamic split joins/roles, boundary leaves/reductions/publication and origin encoding still cover the full context.

A source-level counterexample to general old-frame reconstruction is an empty fixed 200-by-100 border box with horizontal padding sum 20: old padding 0/20 versus 20/0 retains the same outer outputs and empty transfers but different old content-left inputs; either can become 10/10. Empty content itself can trivially skip, so this example does not prove that every useful restriction requires a cache. It shows why equal outer size and current styles alone cannot justify the general bypass. Q140 remains a new admission/state choice; a hosted before/after frame probe can determine whether the measured large context actually has unchanged effective inputs before selecting that change.

### Hosted effective-input diagnostic: criterion before capture

The temporary `root-frame-probe` workflow injects a read-only all-context API only
in its hosted checkout, before building a sequential oracle with the production
pin. For the correctly styled ECMA262 first 12px/undo pair, it records old styles
before restyle, current styles after marks at retained dimensions, and completed
frames after update. A large flow with unchanged completed frame/space and no
marked interior supports investigating own-constraint admission; changed effective
inputs or marked interiors reject that explanation for that context. Equal
endpoints do not exclude transient flex widths, so they alone cannot justify a
production bypass. The API changes no retained state or admission and adds no
module dependency. Instrumented elapsed time only bounds this two-edit sample;
it is not performance evidence. The ordinary independent full comparator remains
required, and a deliberately omitted snapshot must fail the diagnostic checker.
The workflow and its two scripts are removed after the captured source, inputs
and results are retained in the artifact and summarized here.

The first diagnostic run, [37753206438](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37753206438), failed before execution because the workflow paired production f949 with the timing cohort's LLVM 22; Clang rejected the `llvm.coro.end` return type. The repeat uses the existing production oracle's Ubuntu toolchain with the unchanged production pin. This is a workflow compatibility correction, not a renderer or language workaround; the failed run supplies no frame or timing evidence.


### Effective-input result and remaining root-font contract

[Hosted diagnostic 37754371973](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37754371973) passes at aa3d3240025499c4227233991a116cb29c9e87a7 using production wf-f949e676acfa, native Clang 18.1.3 and an AMD EPYC 7763 runner exposing four CPUs (Ubuntu 24.04.5, Linux 6.17.0-1022-azure). The artifact retains the injection patch, exact source, compiler/driver/input hashes and all raw records. Six snapshots cover 10,217 live contexts, with clean before marks and stable post-edit/before-next-edit fields. The process exits zero; dropping the first marked snapshot is rejected with exit one for the intended missing-snapshot reason. The bounded sample takes 10.27 seconds including startup and instrumentation; this is only batch-sizing evidence.

For both the first 12px root-font edit and undo, flow slot 91 (element 21173, under body flex slot 2) has 112,817 events, 41 marked paragraphs, no marked children or restyled blocks, and an own restyle mark. Its complete recorded frame and space are unchanged at marking and completion; outer size, baseline and content height also remain unchanged. All three dumps have hash `eb35ffcdb2ac7a51` and 19,024,863 bytes, with both edits matching independent full layout. The oracle reports 41 prepared/rebroken paragraphs, four contexts and 112,823 entries, including 112,817 held entries. The 41 marks reject the prior no-interior-marks criterion: no wholesale skip is justified. Q140 now explicitly requires bounded marked-frontier processing alongside a complete effective-input contract. The unchanged dump alone does not prove those marks unnecessary.

Flex preparation can assign a preliminary space; the row path does not lay out there, while final sizing and stretch may issue layout calls. The probe does not capture the actual row/target/cross values or every update-entry space, so a generic transient-input claim remains unverified. The root/html frame's inactive column-gap field also changes with font size: comparing every stored field without its use conditions would overreject. Any selected input contract must account for the actual consumers. The temporary workflow and scripts are removed after this result; no diagnostic state, API, renderer mutation or compiler pin is adopted.

### Integrated zero-displacement omission coverage

The full falsification run 37751546435 compiles the exact zero-suffix mutation but fails to detect it. The Apollo sentence fixture remains incrementally correct in the hybrid representation because movement already repairs rendered geometry; the missing publication can leave cached owner-relative offsets stale. The existing independent publication oracle has a nonzero displacement and does not distinguish this guard omission.

Retain the guard mutation and the original sentence fixture, and add a nested-owner publication case through the real movement and finish paths. A parent moves from absolute y=20 to 21 while its untouched nested block stays at absolute y=25 with zero net flow displacement. Its local and published offsets must change from 5 to 4, and its owner-relative natural floor from 10 to 9 while absolute natural y=30 stays fixed. These independent numeric expectations test the original zero-displacement/moved-owner obligation; the existing nonzero-displacement case remains intact. The unmutated combined oracle passes at 3edbfd9. In falsify run 37756682384, zero-suffix job 113242844511 compiles the unchanged guard mutation and fails the independent boundary-transfer assertion: the sentence fixture baseline has two matching edits, while the mutant exits before output with exactly `boundary transfer check failed`. This closes the missing cached-publication coverage without weakening the mutation or removing the original fixture.


### Integrated six-cohort acceptance at 6bf0d0e

[Hosted comparison 37751546759](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37751546759) completes all 288 raw files and 11,520 edits after integrating layout d13e18c. Every side runs on one AMD EPYC 9V74 hosted machine exposing four CPUs, Ubuntu 24.04/Linux 6.17.0-1022-azure, LLVM 22, wf-0b7f5c5b9854 and WF_WORKERS=4. Before and before twin are independent builds of integrated 48cfbeb. All six cohorts retain complete script ordinals: 20 ECMA262 and 60 HTML5 edits per file. Values are upper-median edit microseconds, round 1/round 2, excluding style.

| Page | Kind | Mode | Main | cf12 | cf12 twin | Before | Before twin | A | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| ecma262 | word | seq | 82/90 | 86/88 | 98/87 | 102/88 | 87/94 | 94/88 | passes |
| ecma262 | word | par | 125/122 | 143/141 | 134/137 | 134/135 | 138/144 | 134/137 | passes |
| ecma262 | sentence | seq | 183/184 | 643/622 | 762/691 | 125/132 | 125/124 | 127/130 | passes |
| ecma262 | sentence | par | 239/256 | 556/539 | 574/563 | 205/190 | 196/198 | 195/185 | passes |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| ecma262 | fontsize | seq | 1554/1659 | 10273/9461 | 10429/9617 | 608/643 | 551/607 | 589/600 | passes |
| ecma262 | fontsize | par | 1866/1924 | 10666/9876 | 10871/9755 | 829/836 | 1124/714 | 714/992 | passes |
| ecma262 | rootfont | seq | 31408/32225 | 120327/119462 | 122048/123690 | 120833/121690 | 120079/119532 | 122996/120811 | fails r1,r2 |
| ecma262 | rootfont | par | 59846/59858 | 202808/198503 | 203728/200474 | 170136/170182 | 170676/169595 | 171711/170533 | fails r1,r2 |
| ecma262 | block | seq | 538039/529701 | 105/102 | 103/101 | 109/114 | 107/113 | 108/108 | fails r1,r2 |
| ecma262 | block | par | 362510/360339 | 159/156 | 165/160 | 164/165 | 159/160 | 167/168 | fails r1,r2 |
| html5 | word | seq | 61/60 | 68/68 | 67/66 | 69/67 | 64/67 | 69/65 | passes |
| html5 | word | par | 95/98 | 102/100 | 98/101 | 101/101 | 100/101 | 101/99 | passes |
| html5 | sentence | seq | 177/179 | 283/278 | 275/278 | 277/289 | 275/277 | 283/276 | passes |
| html5 | sentence | par | 260/233 | 307/293 | 285/297 | 283/286 | 297/286 | 294/295 | passes |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | passes |
| html5 | fontsize | seq | 626/521 | 2447/2279 | 2446/1940 | 1468/1458 | 1501/1537 | 1412/1570 | fails r1,r2 |
| html5 | fontsize | par | 761/526 | 2248/2022 | 2395/2159 | 2088/1998 | 2131/2271 | 1991/1859 | fails r1,r2 |
| html5 | rootfont | seq | 546812/547987 | 700357/688240 | 697068/691013 | 701836/706486 | 706406/710203 | 702151/694936 | passes |
| html5 | rootfont | par | 295779/297857 | 491860/487458 | 487779/488532 | 463824/468031 | 463630/472365 | 461551/468776 | passes |
| html5 | block | seq | 628999/648082 | 527/497 | 509/519 | 504/540 | 504/553 | 511/524 | fails r2 |
| html5 | block | par | 453512/457355 | 613/576 | 570/568 | 578/577 | 583/593 | 645/591 | fails r1,r2 |

The strict gate fails 15 of 48 cells: all four ECMA262 root-font cells, all four HTML5 font-size cells and seven block cells. Word, sentence, colour, ECMA262 font-size and HTML5 root-font pass in both modes and rounds. Controls expose variation but do not waive literal block overruns; acceptance is not met and no adoption merge follows.

Cursor reuse changes only physical index-read counters against both immediate-before builds; every other per-edit work counter is identical. Each HTML5 font-size mode/round drops from 1,016,526 to 871,350 index reads (145,176, or 14.28%, removed), affecting 56 of 60 edits. Block and root-font counters do not change. Parallel HTML font-size medians fall, but the second-round gain is within the before-twin spread, while the sequential direction reverses. This establishes less metadata work, not a general isolated latency gain. Direct sibling payload updates and full restyled-context publication remain.

The paired style-plus-update medians below are computed per edit, not by adding separate medians. Both decisive failing kinds also fail this metric; eight block cells exceed cf12, for 16 failed cells total.

| Page | Kind | Mode | Main | cf12 | cf12 twin | Before | Before twin | A | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| ecma262 | word | seq | 82/90 | 86/88 | 98/87 | 102/88 | 87/94 | 94/88 | passes |
| ecma262 | word | par | 125/122 | 143/141 | 134/137 | 134/135 | 138/144 | 134/137 | passes |
| ecma262 | sentence | seq | 183/184 | 643/622 | 762/691 | 125/132 | 125/124 | 127/130 | passes |
| ecma262 | sentence | par | 239/256 | 556/539 | 574/563 | 205/190 | 196/198 | 195/185 | passes |
| ecma262 | colour | seq | 14/13 | 12/13 | 12/12 | 14/14 | 14/14 | 14/14 | passes |
| ecma262 | colour | par | 17/17 | 17/18 | 18/18 | 18/17 | 18/18 | 17/17 | passes |
| ecma262 | fontsize | seq | 1823/1788 | 10386/9518 | 10508/9681 | 1331/1454 | 1253/1241 | 1204/1361 | passes |
| ecma262 | fontsize | par | 2032/2134 | 10824/10001 | 11028/10169 | 1860/1901 | 1821/1731 | 1726/2036 | passes |
| ecma262 | rootfont | seq | 35702/36545 | 124570/123793 | 126364/128020 | 125138/126162 | 124326/123879 | 127242/125148 | fails r1,r2 |
| ecma262 | rootfont | par | 64677/64607 | 207520/203283 | 208548/205290 | 174947/175121 | 175570/174397 | 176615/175297 | fails r1,r2 |
| ecma262 | block | seq | 538112/529772 | 120/118 | 118/118 | 128/129 | 125/128 | 126/128 | fails r1,r2 |
| ecma262 | block | par | 362592/360371 | 182/180 | 193/184 | 189/211 | 190/188 | 192/192 | fails r1,r2 |
| html5 | word | seq | 61/60 | 68/68 | 67/66 | 69/67 | 64/67 | 69/65 | passes |
| html5 | word | par | 95/98 | 102/100 | 98/101 | 101/101 | 100/101 | 101/99 | passes |
| html5 | sentence | seq | 177/179 | 283/278 | 275/278 | 277/289 | 275/277 | 283/276 | passes |
| html5 | sentence | par | 260/233 | 307/293 | 285/297 | 283/286 | 297/286 | 294/295 | passes |
| html5 | colour | seq | 14/13 | 14/14 | 14/14 | 13/14 | 14/14 | 13/14 | passes |
| html5 | colour | par | 23/22 | 21/21 | 21/21 | 21/17 | 20/20 | 21/21 | passes |
| html5 | fontsize | seq | 684/599 | 2508/2342 | 2539/2033 | 1568/1528 | 1545/1591 | 1511/1653 | fails r1,r2 |
| html5 | fontsize | par | 871/655 | 2403/2129 | 2525/2274 | 2223/2100 | 2245/2421 | 2057/2007 | fails r1,r2 |
| html5 | rootfont | seq | 805575/805911 | 962780/948609 | 960032/950103 | 961138/967920 | 965797/973600 | 965069/955361 | passes |
| html5 | rootfont | par | 458471/462804 | 657571/652163 | 653741/654132 | 627982/633941 | 630483/638623 | 626007/633302 | passes |
| html5 | block | seq | 629159/648194 | 617/609 | 625/616 | 610/619 | 612/626 | 618/613 | fails r1,r2 |
| html5 | block | par | 453657/457478 | 698/685 | 679/704 | 694/714 | 705/708 | 741/693 | fails r1,r2 |

The full-cost floor includes actual style invalidation, processing of changed text/layout inputs and propagation of changed outputs. The diagnostic's 41 marked ECMA paragraphs cannot be discarded merely because final dumps match. It does not require rebuilding every unchanged source index or publishing every retained transfer. No universal numeric lower bound has been proved. Main's same-host observed full path is the practical comparison: ECMA262 root-font 35,702/36,545 us sequential and 64,677/64,607 parallel, versus A 127,242/125,148 and 176,615/175,297. HTML5's much broader changed-text work costs main 805,575/805,911 us sequential and 458,471/462,804 parallel, versus A 965,069/955,361 and 626,007/633,302. The earlier bisect and profile identify the additional M2 context-maintenance path; the current input diagnostic narrows a proposed repair to a complete input certificate plus marked-frontier processing.

Exact source and isolated pin-only children (not pushed or adopted):

- `a source=6bf0d0e93e78f9ce7612a93089ac92e211b8d842 pin-commit=aa06c50f9a8cc5296b1f391569ca0520581ef186 release = wf-0b7f5c5b9854`
- `base source=cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 pin-commit=8feb65b28c1e0dd740c8f2582bcc719d6c858b93 release = wf-0b7f5c5b9854`
- `before source=48cfbeb206214a93405f0d9ad300cbc150267ab4 pin-commit=542cbfd65edfa40241143683bc1c4a42fed6adc2 release = wf-0b7f5c5b9854`
- `beforetwin source=48cfbeb206214a93405f0d9ad300cbc150267ab4 pin-commit=6668ea02f19598ff8fe62bcdd588627894d4e3d5 release = wf-0b7f5c5b9854`
- `main source=8fbc1601785cee70265da1eac4d99589fc6fb67c pin-commit=2fc3d2acea1e398c115eef4a6598dc7f2210f228 release = wf-0b7f5c5b9854`
- `twin source=cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 pin-commit=5ec8c96b6ae4004a9385403eaad58962f285f1a4 release = wf-0b7f5c5b9854`

All renderer edit-path bodies remain those measured at 6bf0d0e. The later 3edbfd9 change adds only an independent startup publication check and removes temporary diagnostic files; it does not supply another performance measurement. Layout-check and check pass at 6bf0d0e (37751546586/37751546384) and at 3edbfd9 (37756682338/37756682325). The 6bf oracle main/structural jobs passed before the full oracle and falsification runs were cancelled after the known zero-suffix coverage failure; they are partial evidence, not full passing gates.

[Full oracles 37756682278](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37756682278) passes all 14 jobs at 3edbfd9. Its 24 X5 raw files contain 960 incremental/full matches, no differences or refusals, and 12 byte-equal normalized sequential/parallel pairs. All page block paths are splice 1 reason 0 (20 ECMA262 and 60 HTML5 per mode). Full dumps remain byte-identical to the frozen layout baseline ddfd63d0755e51f7c2972e0bb43b0c5d88fe30c7 and between sequential/parallel modes (19,024,863 and 12,538,869 bytes), and all five case pages plus the saturation fixture remain unchanged. The arithmetic artifacts contain 384 topology, 32 split-limit and 40 near-limit matches without differences or refusals. Each Apollo fixture has two matching edits per mode; sibling-margin splices with reason zero, while sibling-context takes the expected full fallback with reason six.

[Falsify 37756682384](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37756682384) passes all 55 jobs at the same revision. The affected-fragment omission produces eight transfer-case differences; following-fragment omission produces 54 transfer-case, 16 cascade and 16 reference-frame differences. Topology omission produces four differences in each of 12 cases, while its negative control rejects the unmutated renderer for the intended absence of differences. The Apollo sibling-frontier mutation produces two sibling-margin differences; the exact zero-suffix guard omission is detected by the independent publication assertion described above. No check or mutation is weakened.

### Integrated completion review

A separate read-only reviewer inspected the full 40-file cf12c609..13ac2b1 change, the final evidence-only update and directly affected consumers, followed the behavior and documentation repairs, and reviewed the Apollo conflict resolution. The later shared-board URL correction changes guidance only. All project checklist groups A/D/C/T/R/M/V and design checks G1–G3/DC1–DC4 were considered; no entire group was skipped. The reviewer read hosted gate logs and artifacts, independently recomputed the 288-file timing result and both 24-row metric tables, and ran no local build, test, check or performance workload. Design source counts against cf12 are 7→7 nodes, depth 1→1, 59→62 decisions and 24→24 rejections.

A1–A4, D1–D4, C3–C5, T1, T3, R1–R2, R4, V2, G1, G3, DC1 and DC3 pass within the recorded scope. C1, T2 and V1 pass with all 14 oracle jobs and all 55 falsification jobs complete, including the compiled zero-suffix omission. T4 is not applicable because adopted pins and submodules are unchanged; PR-specific V3/V4 are not applicable under the owner's no-PR instruction. C2 and DC4 remain unverified beyond the independent constants and existing external fixtures: generated topology compares incremental against full layout, not new external conformance, and finite numeric/source-retention probes do not prove their general arguments. Performance acceptance remains incomplete.

R3/G2/DC2 retain the stored-field inverse-proof finding. The pipeline decision requires all independent writes to be expressed as such, while the bounded reference traversal still orders direct sibling writes through shared context state. The open independent-write decision records the pinned language's missing proof form; it does not waive that design requirement. M1 therefore retains this finding and the unverified correspondence items despite passing hosted design-form lint.

Review findings led to repairs of lineless-origin behavior/documentation, an overstated universal root-style floor, fragment mapping lifetime/sentinel documentation, the first constant-publication fixture, and artificial chains in pure owner comparison and source-union helpers. The missing coverage of zero-displacement cached publication is fixed by the independent nested-owner case, with both unmutated success and compiled omission detection verified in hosted CI. No additional defect was found in the cursor reuse, root-input diagnostic or subsequent prose. The final local documentation repair (RV7, D3/V2) names the actual frozen dump comparator ddfd63d rather than conflating it with timing main 8fbc160; the passing dump evidence is unchanged. Empty touched-registry reconstruction is explicitly deferred in the TODO until native allocation evidence makes it material. Approval remains with the owner.

The incoming layout-line guidance commit 95ea4a1 was merged without source conflicts as a816ae0; its layout-check 37760214214 and check 37760214253 pass. The later review/guidance commit 13ac2b1 also passes layout-check 37763120951 and check 37763120875. The runtime integration remains the Apollo merge 48cfbeb, followed by cursor reuse 6bf0d0e and the independent publication oracle 3edbfd9. No adoption merge into research/m2-layout is made. The effective-input/marked-frontier and range-displacement proposals remain unimplemented owner decisions, as does the independent-write proof disposition. Production whitefoot.pin and both submodules are unchanged; the temporary diagnostic workflow and scripts have been removed. The design-log entry still waits for the approval of [PR #49, the layout-line design approval](https://github.com/Ming-Research/Snowghost-wf/pull/49).


### Retained effective inputs and dirty-paragraph transaction

The owner selected this contract-first implementation under Q140 A. This section defines the implementation contract, not a timing result. Its first admission is the ordinary, stationary dirty frontier; a changed placement or an input outside that admission runs the existing reference algorithm. The later range work does not change this contract.

**Completed inputs.** A flow context retains a valid bit, the actual `Space`, its used border-box width, and `FlowFrame` from its last completed publication. The frame is the content left/top, flow width, definite content height, and column state/shape. Compare actual inputs at every `update_flow` invocation, after the parent supplies its current space, including flex final-size and stretch calls. Never reconstruct old inputs from new styles. Preparation, a temporary fresh space, or an outer-output snapshot does not overwrite this certificate. Full flow layout and successful incremental publication replace it; reset, interior reconstruction and structural splice invalidate it. Copying outer outputs into rebuilt content does not copy the certificate. A refused attempt leaves the old certificate valid until reference publication completes.

**Admission and invalidation.** The initial frontier path requires completed owner-relative geometry, no pending boundary repair, equal actual space and used width, equal content left/top, flow width and definite height, and old/new non-column flow. Inactive column-count/width/gap values do not invalidate ordinary flow. It rejects intrinsic demand/held intrinsic inputs, shrink-to-fit space, marked child contexts, changed interior blocks, and positioned descendants. Own-style invalidation may pass only after these effective inputs are checked. Both exact-route and legacy dense style marking must classify changed blocks; zero block marks cannot be inferred from the legacy `restyled` flag. Structural reconstruction never qualifies on its copied outer dimensions. The paragraph admission additionally requires unchanged source identity, retained positive-height lines or the [bounded retained-lineless contract](#retained-lineless-frontier-bounded-contract-and-prior-falsifiers), no float dependency and no atomic children. The width and left edge supplied by the old completed prepass therefore remain effective. Line-presence transitions and unsupported empty-inline topology retain the reference repair path with distinct counted reasons.

**Frontier ownership.** Each context owns a sparse binary set over its stable paragraph slots in `[0, item_ceiling)`. An empty branch means no pending paragraph in that interval; a leaf denotes exactly one dirty paragraph; internal nodes partition their interval in halves. This is a semantic dirty-work index, used by preparation, independent breaking and retirement, not an inverse array introduced only for a write proof. Marking inserts once on the clean-to-dirty transition. Exact text/style routes insert their known slot; legacy dense marking and newly rebuilt content construct the equivalent set while already examining their paragraphs. Structural replacement retires the old set with its paragraph domain. A splice that preserves unrelated slots preserves their marks and invalidates the completed input certificate. No fixed dirty-count cap or whole-array rebuild is introduced when a new slot appears.

**Independent work and dependency order.** Frontier visitors prune empty intervals and pass disjoint paragraph slices to the two subtrees. Preparation and admitted line breaking read shared document/style/font/unchanged-child data and write only their own paragraphs. Their result reductions combine after both branches. This gives work proportional to marked slots and their directory paths, with no scan between sparse marks. Preparation retains marks until layout consumes them. Each leaf checks its own paragraph admission without waiting for other leaves, then captures the old line presence, extent and last baseline before a speculative break; the break always regenerates glyph fragments, even when placement is unchanged. The new paragraph transfer is produced independently. Only when every candidate preserves its line presence, advance and last baseline, with no unsupported empty-inline topology, may the transaction publish stationary transfers. Publication updates the retained leaf transfer and ancestor reductions, including first-baseline and intrinsic contributions; equal outer geometry alone never skips it. Existing owner writes remain serial pending Q139's Whitefoot proof fix; this is not a claim that distinct owner writes have a true algorithmic dependency.

**Failure and completion.** A context-input admission refusal changes no geometry. Once context inputs qualify, a refused leaf may coexist with independently completed speculative breaks. If any leaf refuses or independent breaks reveal changed placement, all marks remain and the caller enters full reference replay directly; it must not run another old-output probe against the newly broken lines. That full replay resets spaces, breaks dirty paragraphs and republishes the complete geometry, so speculative results cannot masquerade as old geometry. The failed attempt is counted. A successful stationary batch recomputes the context's used height from retained content height under current styles, derives baseline visibility under current overflow, refreshes its own rectangle, and lets its caller resolve margins. It does not copy the previous border-box result. It clears only the frontier it consumed and publishes the new completed-input certificate after all transfers and fragments are valid. The no-positioned-descendant admission is essential: equal interior frame does not imply an unchanged positioned containing box after border/padding redistribution.

**Consumers and floor.** Dirty preparation and retirement consume the frontier; the line breaker consumes effective paragraph width/left, new shaped text/strut and unchanged child inputs; transfer publication consumes the new line output and retained owner topology; outer settlement consumes current own sizing/overflow styles and retained content result. Parent flex/grid/flow algorithms still consume the resulting dimensions, margins and baseline, and may call again with different inputs. Root-font still performs its real style invalidation and every marked paragraph's preparation/break/publication. The avoided work is unchanged-context event materialization, child snapshots, prepass, stacking and transfer republishing. Main's measured style-plus-edit path remains the practical full-cost comparator; there is no asserted universal numeric floor.

**Required discriminators.** Hosted fixtures/falsifiers must cover: omission of a sparse dirty leaf; reuse with changed content width/offset or transient parent space; changed interior block styles through the legacy marking API; current minimum-height/overflow settlement despite equal interior inputs; dirty glyph/first-baseline publication despite stationary last-baseline/height; changed placement falling through to reference replay; lineless transitions; and source replacement retiring old input/frontier identities. Existing incremental/full, sequential/parallel, split/topology, saturation and structural oracles remain wired. Counter evidence must distinguish visited dirty paths from whole-context replay. The per-edit experiment interleaves the source before this change, its twin, the changed source, main and cf12c609 with a twin on the same hosted runner; failure to separate from the before twin is not reported as a speedup.

### Dirty-frontier fixture corrections

The runtime at c218633 passes hosted layout-check 37775073164 and check 37775073158. The initial focused falsification run 37775073205 is not passing evidence: its unmutated sparse fixture reported three prepared paragraphs, six breaks and 195 held entries, so the strict locality assertion correctly failed before mutation. The inherited 40px inline line-height changed ascent/descent distribution with font size and therefore changed the union with the paragraph strut. The renderer's speculative transaction correctly refused that changed extent. The corrected fixture top-aligns the unchanged 40px inline box within the fixed 40px strut, preserving height and baseline while still changing glyph geometry; the required three breaks, zero held entries and bounded entry count are unchanged. The known-blocked falsifier remainder was cancelled, and the corrected cases require another hosted run. No speedup or completed correctness gate is inferred from compilation alone.

The additional premise audit distinguishes material guard omissions from redundant/conservative restrictions. Positioned descendants, float exclusions, atomic placement, active column maps, marked child work and premature completed-input publication receive targeted falsifiers. A mixed lined/lineless dirty batch exercises refusal after independent speculative work. Structural splice already invalidates the completed certificate before marking boundary repair, so omitting only the frontier's redundant boundary-dirty guard need not produce a difference; source-splice identity still exercises the subsequent full bridge. The transient-flex fixture remains identity coverage rather than a claim that it isolates every intermediate flex call. The audit also withdrew the new, unvalidated failed-attempt-routing omission before claiming it as a falsifier: a one-paragraph frontier candidate already requires own restyle, while multiple-paragraph candidates are rejected by all existing single-entry probes and by `restack_entry`. Removing only the wrapper's restyled assignment therefore does not expose those stale-output probes under the current admission. The explicit assignment remains the transaction boundary and ensures early full event materialization; mixed lined/lineless and changed-placement fixtures retain identity coverage, and omitting failed-batch rejection itself still has its separate falsifier. No established mutation was removed. Source inspection and the initial fixture counts also expose duplicate initial breaking after a failed batch: S completed speculative leaves plus D dirty leaves in full replay cost S + D breaks, while preparation runs once; newly encountered float placement can require additional real breaks. Avoiding that duplicate work would require explicit same-transaction break provenance, since retained `broken_width`/`broken_left` survive text preparation and are not a freshness certificate. Its latency contribution remains unmeasured, so no speculative-line reuse is claimed or enabled.

Hosted runs at 24f351e (oracles 37778244027) and 3fec79f (falsify 37779838029) stopped on the unmutated `own-overflow` fixture with `inc refused`, before any later fixture ran. Overflow is a box-construction input: `retained_style` compares `overflow_x`/`overflow_y`, so `styles_changed` refuses the edit before `update` and the frontier never observes changed overflow. The `own-overflow` and `overflow-baseline` fixtures therefore cannot reach the transaction, and the `frontier-overflow-baseline` mutation (keeping the old `has_baseline`) is undetectable for that technical reason, not because the derivation is wrong: under every admitted edit the overflow inputs and the lined baseline entry are unchanged. The mutation and both fixtures are retired; the derivation remains in the transaction. Own settlement keeps `own-minimum` and adds `own-padding-bottom`, which changes the used border-box height without changing the content frame. The fixture generator now checks every case and reports all failing fixtures together.

### Dirty-frontier validation and timing result

At 3393042 (renderer identical to c218633 except fixtures), [oracles 37783479443](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37783479443) passes all 14 jobs, including every generated frontier fixture in sequential and parallel mode and the legacy-marking driver. [Falsify 37783479543](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37783479543) passes 15 of the 16 frontier jobs. The `frontier-inputs` mutation, which removes the space, width and all four frame comparisons together, is detected by each of the five frame fixtures, but the job failed its per-case requirement on `frontier-parent-space`: that case produced no difference when the space comparison was removed. The observed result is that this fixture does not reach the guarded comparison with a changed space; the mechanism that bypasses it was not instrumented. The space comparison therefore keeps identity coverage and no isolated discriminator; the requirement is removed and the combined omission remains required through the frame cases.

[Hosted timing 37776856362](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37776856362) measured the frontier runtime (d690845, renderer as above) against main 8fbc160, cf12c609 and the preceding runtime 593b2db (renderer of f119db2), each but the candidate with a twin, on one AMD EPYC hosted runner with wf-0b7f5c5b9854, LLVM 22 and WF_WORKERS=4. Values are upper-median update microseconds, round 1/round 2:

| Page | Kind | Mode | Main | Main twin | cf12 | cf12 twin | Before | Before twin | Frontier |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ecma262 | fontsize | seq | 2097/2152 | 2009/2014 | 12128/11623 | 11990/11647 | 1789/1676 | 1363/1538 | 605/604 |
| ecma262 | fontsize | par | 2553/2523 | 2197/2450 | 11925/11757 | 11529/11432 | 1698/1713 | 1527/1440 | 1090/1064 |
| ecma262 | rootfont | seq | 30560/31597 | 31369/30508 | 125600/122682 | 124005/122150 | 122394/121016 | 120763/121003 | 120318/119721 |
| ecma262 | rootfont | par | 66056/66903 | 66188/66802 | 238868/236524 | 242118/229664 | 201145/200971 | 192661/196152 | 195040/193535 |
| html5 | fontsize | seq | 1209/1310 | 1155/1386 | 3921/3280 | 3851/3695 | 3152/2432 | 2653/2489 | 1982/2295 |
| html5 | fontsize | par | 1094/1046 | 1032/1031 | 3606/3598 | 3851/3490 | 3665/3114 | 3154/3172 | 2850/2835 |
| html5 | rootfont | seq | 651734/650218 | 649396/647736 | 796413/791640 | 798012/790381 | 814099/802127 | 812622/804472 | 941448/945502 |
| html5 | rootfont | par | 407375/402335 | 407410/400041 | 620662/614958 | 625960/620838 | 599008/586886 | 596171/593158 | 976693/974479 |
| html5 | block | seq | 697823/673747 | 696016/685482 | 655/708 | 666/640 | 757/751 | 678/705 | 817/750 |

ECMA262 root-font does not separate from the before twins (120,318/119,721 against 122,394/121,016 and 120,763/121,003 sequential). Its counters show the transaction attempted and then replayed: every edit still holds all 112,817 entries, while 41 boundary entries are now charged against the 41 marked paragraphs. The counters do not record the refusal reason; a changed line extent of root-relative text, which the stationary admission must refuse, is the expected cause and is not separately verified. The stationary frontier therefore does not reduce this edit. ECMA262 font-size separates (605/604 against 1,789/1,676 and 1,363/1,538 sequential), and HTML5 font-size improves only in parallel. HTML5 root-font regresses well beyond twin spread (976,693 against 599,008/596,171 parallel); its style delta rose from 39,157 to 102,914 us. The cause is the frontier's root interval: every context's set was rooted at the 2^30 slot ceiling, so each of the 60,868 marked paragraphs in 13,903 contexts cost about thirty boxed directory levels. Commit f697443 roots each set at the smallest power of two over the context's own paragraphs and doubles it by wrapping when a larger slot is marked; the next comparison measures it as the patched frontier cohort.

### Sequence-range displacement contract

The owner selected Q141 A, with this contract preceding implementation. This section specifies the final representation; until its producers, consumers and falsifiers are all wired, the existing individual writes remain authoritative. The retained-flow experiment is measured before enabling range displacement so their costs remain attributable separately. Q139's independent-write proof gap remains a separate adoption blocker.

**Operations and exact action.** Keep hybrid reference translation distinct from ordinary boundary/splice translation. Hybrid translation first narrows the old absolute normal and visual positions separately, then adds the i32 vertical delta with saturation, then encodes against the settled owner. Ordinary boundary/splice translation changes the existing local y anchor by its admitted i64 delta and leaves horizontal and visual offsets unchanged. Sharing storage must not add horizontal normalization to the latter operation.

Write an `Origin` as `(x, y, dx, dy)`, with visual position `(x + dx, y + dy)`. For old absolute owner `O`, settled owner `C` and admitted hybrid absolute displacement `d`, the exact local action is `(O.x - C.x, O.y + d - C.y, O.dx - C.dx, O.dy - C.dy)`. It can be nonidentity when `d` is zero. Ordinary movement uses `(0, d, 0, 0)`. Viewport-owned positioned children retain their zero placement owner and are settled explicitly; they never inherit a formatting-block rebase. An intact nested Open moves once in its parent's sequence; its own sequence does not also receive that movement. Lineless paragraph scratch remains fixed.

**Range membership and storage.** Each owner AVL node retains separate own and pending-child geometry actions, separate own and pending-child semantic-bound displacements, and optional latest own and pending-child basis-height assignments. Geometry actions affect local origins. Semantic actions affect published transfer bounds and the duplicated block offset; they are not inferred from geometry because their publication times differ. Latest basis assignment wins, rather than adding, and preserves the existing assignment to translated Opens. Topology cursors retain only links and structural weights; action reads do not force every event/rank lookup to copy transfers.

Semantic traits describe applicable members: a placed generic anchor, an Open block, finite motion bounds, and the count of reachable positioned entries. Aggregate traits use OR for the first three and addition for the count. The positioned count includes an Open's nested sequence, so selection can skip ranges with no positioned work. Own-action applicability concerns the node's own payload; pending-child applicability concerns its children, excluding that payload. A range with no applicable coordinate or bound carries the identity action in that channel. No meaningless tag may accumulate without a member that witnesses its bound.

An immutable point geometry read adds ancestor pending-child actions to the target's own action, resolves the effective local anchor, then follows the placement owner. Each edge contributes exactly once. A partial range mutation distributes the pending child action before descending. Point replacement exposes its path, encodes the new base in the effective owner frame, and retires only that point's own action. Replacing an Open's placement does not retire actions inside its separate nested sequence.

Before rotation, insertion, removal or successor transplantation changes membership, distribute the affected nodes' pending actions. Actions belong to the old member set: a newly inserted private payload cannot inherit movement that happened before insertion, and a transplanted successor retains its own effective action rather than the removed slot's. Removed slots remain tombstones; replacement/source reconstruction retires actions with their existing stable identity domain. An action-aware point or splice operation must not normalize the whole owner to make its local access convenient.

**Atomic placement source.** An atomic child has a stable paragraph-slot placement source distinct from its formatting block and from `entry_slot`, which continues to classify direct non-atomic entries. Its retained anchor is relative to the paragraph's effective normal/visual origin. This avoids an atomic-child write for every translated Text entry without a second consumption clock. `finish_lines` clears the atomic list and appends retained atomic placements only inside its line loop, so committed atomic placements imply a lined paragraph; there is no committed lineless atomic group needing a synthetic placement source.

Initial placement still performs the reference's saturated operations first, and encoding records the exact difference of their resolved results. A later independent child encoding subtracts the current paragraph origin and writes only that child; it does not clear a Text action shared by its siblings. Full Text encoding can refresh the paragraph and its atomic children from their fresh raw results, using an immutable source-origin snapshot for independent writes. Paragraph source identities relocate with private paragraph slots, remain stable for retained slots, and retire with source replacement. Copying a child's outer placement preserves this source when its parent placement survives; a rebuilt parent assigns its new actual source. The full raw compatibility bridge also snapshots effective paragraph origins, before content adjustment and before any block, paragraph or child raw-coordinate write, alongside its existing block-origin snapshot. Atomic restoration uses that immutable paragraph source. Reading already-restored paragraph scratch would apply the content adjustment twice: paragraph y 20 plus adjustment 7, atomic local y 5, then another adjustment 7 would give 39 instead of 32. Tag retirement alone cannot prevent that mixed-version read. These snapshots belong only to the already-dense full bridge; a point reader creates no whole-context table. In the reverse full raw-to-owned pass, atomic encoding reads the paragraph's explicit raw normal/resolved fields, which paragraph-base encoding does not overwrite, rather than a generic reader that might combine the new base with an old tag. Raw geometry remains selected until all encoders finish. Geometry tags retire only after full raw materialization has consumed them, never as a side effect of semantic point publication.

**Old/current readers and transaction boundary.** Committed actions from preceding edits are visible to both old and current readers. During phase-one stacking, captured old block origins resolve untouched old geometry, while touched payloads may expose fresh raw scratch to current readers. An untouched atomic child resolves its retained paragraph base plus committed Text action against the old formatting owner, even when that paragraph already has fresh raw scratch. Ordinary current `paragraph_origin` is therefore not a valid substitute for this old-source read. Materialize old paragraph/atomic placement before breaking replaces line or atomic records. Retained bases and committed actions remain available until the old-read boundary; no additional old-paragraph snapshot is required under that order.

After convergence, collect the cut-owner chain's old/current frames and bounded range descriptors before installing any new geometry action. These descriptors name stable owners and ranges and contain exact local geometry/semantic actions, not a list of every suffix payload. The subsequent stages are: install range geometry; retain the saved old root for the existing admission; publish replayed entries; publish suffix semantic displacement and basis assignments; settle and republish position-dependent outputs and endpoint ancestors; retire replay captures and the transient descriptors. Installing a nonidentity geometry action immediately clears `reference_dense`, including ordinary boundary/splice producers; a full bridge before transaction finish must not mistake unchanged touched lists for complete raw validity. Geometry installation never repairs semantic totals as a side effect. No old-suffix geometry read occurs after installation unless it uses an explicitly captured input. Old semantic reductions remain readable until their publication stage, independently of new geometry. A single phase bit does not stand in for per-node validity while affected points are new and the suffix remains old.

**Reductions and duplicated readers.** Finite `natural_floor` and `float_reach` shift by the local y action, not necessarily the absolute displacement. Absent sentinels remain absent. Exact common translation commutes with their min/max reductions; all other transfer fields keep the original left-own-right association. A covered node's own and total outputs may incorporate semantic movement immediately, while a separate pending-child tag records what the children's stored outputs lack. An externally addressed stable-slot read collects inherited tags on its owner-AVL path. Recursive range reads receive inherited tags from their caller, rather than repeating a root lookup at every visited node. Point semantic replacement exposes its semantic path before writing, independently of geometry path exposure. Distribution uses the old applicability masks; a finite-to-absent or absent-to-finite transition cannot replace those masks first. Normalize any duplicated block offset before retiring its own semantic displacement, then replace the point's traits and repair ancestors. This order also holds when a different surviving finite bound leaves the aggregate finite flag unchanged. Repairs combine effective children and effective own values.

`Block.boundary` is a view of the effective Open transfer. `BlockOutput.offset` includes published semantic displacement; its raw field is not a second authority. `BlockOutput.basis_height` includes the latest applicable assignment, which the later splice-frontier certificate consumes. Readers in boundary propagation, splice previews/frontier certification/publication and independent publication assertions use these effective views. Translation-invariant width/style/through-state fields can keep narrow raw reads. Full publishers replace these views and retire actions only after their already-required geometry traversal has consumed effective origins. Private relocation starts with identity actions and may update its private raw fields directly.

Plain Text and in-flow Child sizes and baselines do not change under admitted translation. Float travel is relative to its natural cursor; atomic travel is charged from paragraph-local offsets, so common exact movement leaves those formulas invariant. Positioned travel depends on its resolved coordinate relative to its owner and must be regenerated after positioned settlement. Positioned selection is real semantic exception work, not permission to scan every child to discover it. Full output resolves tags during its existing traversal; independently addressed point consumers may pay an index path per placement edge. Fragment endpoints, placement tables, full raw restoration, old-frame materialization, splice payload offsets and positioned plans all consume the same effective placement authority. No raw anchor bypass remains outside an explicitly private or fresh-raw domain.

**Saturation and accumulator invariant.** Preserve the existing reference predicate exactly: `abs(content_top) +sat (old_travel +sat abs(delta)) < 2147483647`, including its order, the saved old root, the zero-displacement convergence test and the additional float/natural-floor/open-frame predicates. Ordinary boundary/splice admission remains `<= 2147483647` under its existing old/proposed travel certificate. Range storage broadens neither admission. Outside admission, reference operations run in their existing saturation order; no inverse of a saturated translation is attempted.

For admitted hybrid geometry, horizontal narrowing is an identity: full encoding starts from i32 normal and visual positions; ordinary movement changes y only; earlier admitted hybrid translation preserves absolute x; wide private splice relocation marks the boundary dirty and forces the raw compatibility bridge before hybrid replay. Nonzero context content adjustment likewise retains its bridge. The vertical travel predicate makes the admitted payload's old/new y operations exact. Thus the algebraic action equals the reference's separately narrowed normal/visual operation, including negative margins and relative displacement. This equivalence relies on the existing travel certificate's coverage; finite fixtures do not prove that certificate's general soundness.

Let `B = 4294967295`, the maximum difference of two i32 coordinates. Canonical local normal components have magnitude at most B and local visual-offset components at most 2B. A net own or pending action is a difference of such local endpoints, hence at most 2B or 4B respectively. This is a stored-tag invariant, not merely a claim that final cancellation fits: every nonidentity channel has an applicable member; no descendant base or membership changes before pending motion is distributed; partial updates expose ancestors first; point writes normalize their base; rewiring distributes old-member actions. An own tag therefore compares one member with its normalized base, and a child tag compares a fixed applicable member now with its state at the last distribution. No unbounded edit-count accumulation is possible.

The existing 64-level AVL path sum is then below 2^40. Resolve the local base plus its action before accumulating placement ancestry. Canonical endpoint differences provide a stronger induction than multiplying a per-edge bound by the block count: atomic-local plus paragraph-local is the difference between that child and its formatting block, and each subsequent owner step is the difference between the same child and the next owner. Every intermediate normal component is bounded by B and every visual-offset component by 2B. This includes the extra paragraph and atomic placement edges; a block-count-only bound would not cover them. Do not interleave unnormalized base/tag terms and rely only on final cancellation. Ordinary splice movement has zero horizontal action and retains its existing vertical placement certificate; the structural bridge reestablishes hybrid canonical coordinates. Saturating operators may remain in the implementation, but no new run-time overflow refusal substitutes for these invariants. A compiler inability to express the required proof is reported as a Whitefoot gap.

**Dependencies, evidence and completion.** Old/current cut-frame computations and positioned plans are independent once their immutable inputs are captured. Disjoint range branches are independent after receiving their inherited actions; each parent reduction depends on their returned totals. Old-before-new admission, structural rewiring and containing-block-before-positioned settlement are true orders. Retained paged writes remain explicitly serial pending the owner-selected Whitefoot proof fix; neither sorting/scattering nor an added run-time alias check conceals that gap.

The range experiment must distinguish geometry omission from semantic-publication omission; exercise both rotation directions, successor transplantation, insertion after prior motion, point replacement followed by opposite shifts, atomic point encoding without sibling movement, viewport versus block ownership, zero absolute displacement with owner rebasing, old-floor consumption on a later edit, latest basis assignment in splice reuse, and the full bridge after wide structural relocation. Existing independent publication constants keep their expected values while their reads migrate to the effective authority. Every new premise has an omission falsifier or a stated independent discriminator. Counters include action/index reads and selected exceptions; a hidden full normalization or child scan disqualifies bounded-suffix completion. Hosted before/after timing uses the preceding runtime plus its twin, main plus its twin and cf12c609 plus its twin, with no speedup claim inside control variation.

### Sequence-range displacement implementation

The implementation in `renderer/layout/range.wf` follows the contract above with these representation details. Each `SequenceNode` holds `RangeActions`: own and pending-child geometry (`Origin`), own and pending-child semantic displacement, and own and pending-child basis assignments. Applicability traits are carried in `SequenceOutput` (`placed`, `opens`, `positioned`) and compose by addition through the existing joins, so own applicability is the stored own transfer's trait and child applicability is the children's totals. An Open is a placed member with `opens` one and its nested positioned count; lined Text, in-flow Child and Float are placed members; lineless Text and every positioned entry are not.

Producers. Hybrid translation (`install_reference_geometry`) computes each cut-chain owner's action from its captured old frame and settled frame before installing anything, installs it on that owner's direct suffix and descends only into the Open containing the cut; semantic publication (`publish_reference_ranges`) later installs the action's local y on the same ranges while preserving each Open's immediate containing-block basis and retires the descriptors. Ordinary boundary propagation and the certified splice suffix install `(0, delta, 0, 0)` with the equal semantic displacement. Positioned entries of every installed range are found through the positioned trait and moved explicitly: block-owned anchors by the owner action (or their own planned splice movement) and viewport anchors by the ordinary vertical movement only. Atomic anchors are paragraph-relative (`placement_paragraph`) and follow their paragraph without a write.

Readers and lifetimes. Point readers (`block_local`, `paragraph_local`, `child_local`, `block_boundary`, `block_measured`, `effective_output`) collect ancestor actions on the owner index path only when that owner may retain actions (the later reader bound below); range reads (`inherited_range_output`) pass inherited displacement down. `boundary_set`, rotations, insertion, removal and successor extraction distribute pending actions first; point geometry encoding exposes its path and retires only its own geometry action; semantic point publication folds and retires only its own semantic and basis channels. Full bridges (`reference_geometry`, `own_geometry`, `full_reference_publication`) fold every action into bases, duplicated Open fields and stored transfers with one top-down traversal per owner before the existing dense loops; installation clears `reference_dense`.

Remaining linear work, not changed by this implementation: the splice plan still certifies each suffix sibling independently (`splice_move`, logarithmic reads per sibling), the dense raw path at reference phase 0 still translates and publishes each payload, and `publish_reference_positioned` and `splice_position` still scan every child of a context that has positioned children. Their cost and any replacement are open.

### Ten-cohort comparison at c5cae05

[Hosted timing 37804579353](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37804579353) interleaves ten independently built drivers on one hosted Intel Xeon Platinum 8573C runner (Linux 6.17.0-1022-azure, wf-0b7f5c5b9854, LLVM 22, WF_WORKERS=4): main 8fbc160, cf12c609, the preceding runtime 593b2db, the frontier runtime 3393042 with the bounded root interval applied as `.github/timing/frontier-span.patch`, and the range head c5cae05 (renderer identical to the final head apart from startup constant checks), each with a twin. Values are upper-median update microseconds, round 1/round 2:

| Page | Kind | Mode | Main | Main twin | cf12 | cf12 twin | Before | Before twin | Frontier | Frontier twin | Range | Range twin |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ecma262 | word | seq | 95/94 | 93/86 | 103/89 | 95/88 | 101/93 | 98/90 | 90/101 | 90/89 | 98/93 | 91/98 |
| ecma262 | word | par | 146/129 | 127/130 | 131/144 | 142/128 | 139/170 | 136/123 | 143/134 | 137/123 | 127/139 | 132/127 |
| ecma262 | sentence | seq | 259/283 | 259/272 | 763/769 | 774/760 | 122/133 | 129/130 | 132/122 | 126/120 | 116/117 | 124/129 |
| ecma262 | sentence | par | 333/308 | 290/300 | 710/695 | 688/651 | 193/201 | 196/191 | 192/193 | 192/215 | 219/207 | 206/199 |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | fontsize | seq | 1457/1520 | 1355/1461 | 7775/8562 | 8064/7465 | 1278/1224 | 1029/1153 | 500/446 | 466/441 | 441/466 | 442/438 |
| ecma262 | fontsize | par | 1736/1858 | 1589/1646 | 7886/8585 | 9070/7819 | 1474/1284 | 1479/914 | 747/742 | 800/775 | 896/844 | 869/841 |
| ecma262 | rootfont | seq | 18002/18744 | 16904/18183 | 74039/73770 | 77331/70185 | 78863/70181 | 69504/64840 | 83085/66211 | 73885/70132 | 73553/71432 | 68311/74841 |
| ecma262 | rootfont | par | 53963/57466 | 50616/56967 | 234170/232308 | 222831/222073 | 183213/170723 | 180959/171409 | 183202/164626 | 181096/168196 | 194329/209828 | 200961/204039 |
| ecma262 | block | seq | 427588/468962 | 431325/458027 | 102/97 | 103/92 | 102/105 | 96/99 | 104/114 | 100/113 | 104/107 | 102/99 |
| ecma262 | block | par | 349469/346436 | 332995/340476 | 161/166 | 173/164 | 167/174 | 167/179 | 181/168 | 170/152 | 184/180 | 163/182 |
| html5 | word | seq | 64/72 | 63/70 | 69/69 | 68/71 | 72/76 | 70/66 | 81/76 | 71/77 | 75/80 | 68/70 |
| html5 | word | par | 95/90 | 89/90 | 93/96 | 103/98 | 103/98 | 100/91 | 96/101 | 98/94 | 96/109 | 96/99 |
| html5 | sentence | seq | 183/187 | 181/197 | 299/289 | 286/295 | 294/293 | 298/301 | 334/305 | 330/304 | 567/573 | 554/577 |
| html5 | sentence | par | 289/261 | 259/254 | 309/288 | 323/308 | 310/320 | 331/284 | 317/343 | 340/282 | 762/693 | 702/710 |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | fontsize | seq | 775/804 | 776/804 | 1811/1954 | 1866/1807 | 1657/1791 | 1676/1667 | 1343/1398 | 1386/1301 | 1155/1207 | 1126/1138 |
| html5 | fontsize | par | 728/762 | 723/682 | 2114/2114 | 2246/2124 | 2209/1990 | 2149/2011 | 1872/1932 | 1803/1993 | 2018/1990 | 1992/2016 |
| html5 | rootfont | seq | 559178/568704 | 565998/560263 | 677048/680430 | 690422/679892 | 701790/694895 | 696085/685451 | 724672/710714 | 716895/719402 | 718016/714285 | 711365/718640 |
| html5 | rootfont | par | 324566/323833 | 324889/326038 | 541748/536977 | 535641/544031 | 507338/501864 | 500857/498908 | 516877/502163 | 514067/512955 | 541996/541983 | 545602/543639 |
| html5 | block | seq | 529113/559531 | 577963/567829 | 587/580 | 572/592 | 608/576 | 585/587 | 596/597 | 597/543 | 633/643 | 641/643 |
| html5 | block | par | 386501/415966 | 403109/433568 | 676/654 | 622/615 | 700/621 | 612/634 | 653/615 | 663/618 | 810/815 | 846/838 |

Against the gate (every non-block cell at most twice main in each round; block no worse than cf12), the range head fails 9 of 24 page/kind/mode cells in both rounds: ECMA262 root-font (both modes), HTML5 sentence (both modes), HTML5 font-size parallel, and block on both pages in both modes. Its twin fails the same cells except ECMA262 block sequential in round 1. The patched frontier fails 6 cells: ECMA262 root-font, ECMA262 block, HTML5 font-size parallel and HTML5 block sequential.

The bounded root interval removes the HTML5 root-font regression of the first frontier measurement: parallel 516,877/502,163 against 507,338/501,864 and 500,857/498,908 for the before twins. ECMA262 root-font still does not separate from the before twins in either mode.

Range displacement reduces the counted work of every affected kind: the HTML5 sentence median falls from 199 boundary entries, 112 blocks and 1,458 index reads to 5, 8 and 1,090; HTML5 block from 1,854, 965 and 9,107 to 9, 18 and 2,686; HTML5 font-size from 1,735, 5,608 and 9,518 to 543, 587 and 1,894. It removes the long tail (HTML5 sentence p90 1,118 to 717 us; every edit under 1 ms) and improves HTML5 font-size sequential beyond twin spread (1,155/1,207 and 1,126/1,138 against the frontier's 1,343/1,398 and 1,386/1,301). Yet the typical cost rises: HTML5 sentence 567/573 against the frontier's 334/305 sequential, and 762/693 against 317/343 parallel; HTML5 block 633/643 against 596/597 sequential and 810/815 against 653/615 parallel. The counters do not charge the inherited-action path reads of point readers (`range_inherited` through `slot_view`) or path exposure. Hypothesis, not yet tested: once a context holds any action, every effective origin, transfer and Open read walks its owner index path, and the stacking, encoding and settlement readers that run on every edit multiply that fixed cost. A matched profile of the HTML5 sentence edit on the frontier and range drivers would test it; reject it if the range driver's added samples are not in the inherited-path readers.


### Final gates at 15434d2 and 2638d46

The renderer is unchanged from 15434d2 to the final head. [Oracles 37811959019](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37811959019) passes all 14 jobs, including the frontier and range fixtures in both modes and every X5 kind on both pages. [Falsify 37811959115](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37811959115) passes 82 of 84 jobs, among them all 19 range falsifiers and all frontier falsifiers. The two failures were stale mutations: `reference-suffix` still targeted the dense phase-0 publisher that hybrid replay no longer reaches, and `no-positioned-anchor` deleted a write so that the mutant's effect row no longer matched and did not compile. Migrated to the range code, both pass in [falsify 37820751348](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37820751348) at 2638d46; check and layout-check pass there (37820751349, 37820751318).

Premises without a behavioral discriminator: the viewport-only action for viewport-owned positioned entries, the splice frontier's planned transfer after the range action, the ordinary path's semantic displacement and the latest basis assignment. Their mutations produced no difference on any generated or existing case and were withdrawn; the constant checks cover the semantic and basis channels of `install_range` and Open settlement independently of the producers.

### Matched inherited-reader profile: criterion before capture

The continuation profiles HTML5 sentence edits before changing the readers.
The controls are the table's patched frontier (3393042 plus the retained
frontier-span patch) and range head 58b16da, with the same wf-0b7f5c5b9854,
LLVM 22, fonts, page, edit script and hosted runner. Both sequential and
four-worker native drivers receive the identical script; instruction attribution
uses the sequential drivers. Two small native samples
and an update-only instruction sample precede the full-script profile.
Collection remains enabled; counters are zeroed before each layout-update entry
and dumped after each return. Only those function-return parts are selected;
the termination dump is discarded. Startup, style preparation and output are
excluded. Disabling instruction collection alone does not stop call counts,
and can leave uncollected call edges uncleared at zero-before. Parallel native
times are retained, but instruction attribution uses one thread throughout.
Native edit times remain separate from profiled times.

The added diagnostic counters use callgrind's call edges: calls entering
`range_inherited`, node reads from that function into `slot_view`, and the
recursive directory reads inside `slot_view`. They count compiled calls under
the update entry, without a shared counter write changing the dependency graph
of immutable geometry readers. Inlining can hide calls, so symbol visibility
and nonzero collection are checked before interpreting a missing edge as zero.
Direct-recursion and PLT suppression are disabled, and threads are dumped
separately. The sequential runtime enters the program on a pthread; only its
update-return parts enter the comparison. Each update's raw call graph and
per-function self/inclusive instructions are retained; recursion-inclusive
costs are not summed as disjoint costs. The hosted decoder checks an independent
hand-counted graph and its missing-edge variants, checks that self instructions
sum to the profile total, and requires one nonempty profile part per edit.
A tiny hosted native probe additionally requires the zero/dump boundary to
exclude 400 startup, inter-update and shutdown reader calls while retaining
exactly two and five reader calls inside its two updates on a pthread. Shared
allocation calls before and inside those updates test that skipped-function
costs cannot survive a reset. An initial capture failed the self-total equality
check on its first update and is excluded from attribution; this strengthened
probe and separate-thread capture address that measurement defect.
The [profiler's collection and dump controls](https://valgrind.org/docs/manual/cl-manual.html#cl-manual.limits)
define the measurement boundary.

The hypothesis predicts that inherited readers account for the majority of
the additional update instructions over the patched frontier. Reject it if
those readers do not account for that increase; inspect the actual dominant
path before selecting a repair. A reader change must then preserve the
existing range/freshness contract and pass the complete gates and twin-controlled
six-kind comparison. No performance or refusal cause is inferred from source
inspection alone.

### Matched inherited-reader verdict and owner-local bound

[Hosted profile 37838048934](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37838048934)
uses the two frozen drivers built in
[37833182001](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37833182001):
3393042 plus `frontier-span.patch`, and 58b16da, both with wf-0b7f5c5b9854
and LLVM 22. The capture ran on an AMD EPYC 7763 hosted runner, Linux
6.17.0-1022-azure, Valgrind 3.22.0, with the same frozen HTML5 page, fonts,
UA stylesheet and 60 sentence edits. Native parallel runs used four workers;
instruction attribution used sequential builds. Both cohorts produced exactly
60 update-return parts on thread 2, each with summed self instructions equal
to its summary. The threaded allocation probe retained exactly 2 and 5 reader
calls and excluded all 400 calls outside those updates.

| Across 60 updates | Patched frontier | Range head |
|---|---:|---:|
| Total instructions | 200,312,065 | 216,949,190 |
| Inherited-reader calls | 0 | 179,067 |
| Node-read calls from inherited readers | 0 | 822,700 |
| Native upper median, sequential, microseconds | 340 | 671 |
| Native upper median, four workers, microseconds | 367 | 626 |

The hypothesis survives: inherited readers execute 78,862,686 instructions,
36.35% of the range update cost and 4.74 times the net added 16,637,125
instructions. Removed suffix work offsets much of that addition. This
attribution is `range_inherited`'s 40,810,663 self instructions plus 38,052,023
instructions in its `slot_view` callees; it excludes 279,310 `slot_view`
instructions from other callers. `block_local` accounts for 68,152,224 of the
inherited-reader instructions (86.42%). The diagnostic observes no recursive
`slot_view` call edges; this does not establish zero directory work, because
compiled call edges do not count inlined or loop-lowered operations. Native
timings reproduce the regression but are exploratory, without twins or
interleaved rounds; they are not acceptance measurements.

**Reader repair contract.** Each owner sequence conservatively records whether
it may retain any geometry, semantic or basis action. Fresh construction starts
inactive. The outer `install_range` activates the owner before its recursive
mutation, even for an empty or identity range; recursive branches only read
that bit. Point retirement, exposure, rotations, insertion and removal never
clear it. A full normalization clears it only after folding every action of
that sequence. Reconstruction gets a fresh sequence and fresh bit. An inactive
owner's `range_inherited`, `range_expose` and `range_distribute` return the
identity/no operation before reading its index. Topology/applicability readers
such as `owner_view` remain unconditional. Active owners retain the existing
bounded AVL path and exact action rules; this change makes no shorter-path
claim for them.

**Dependencies and alternatives.** A read depends on its owner's published
bit and actions, with no new mutable cache shared by readers. Activation
precedes the action it advertises, and clearing follows complete consumption;
these are the true validity dependencies. A per-pass placement table would
require collecting its demanded domain before consumers run; a whole-context
table would also introduce unrelated work. The owner-local bit instead prunes
provably inactive domains while preserving independent immutable reads.
Existing serial owner-motion writes remain unchanged pending the recorded
Whitefoot gap. The bit represents retained state, not a proof-only ownership
array or an alias test.

**Falsification and acceptance.** Existing independent range constants and
range fixtures cover installation, inherited geometry/semantic reads, point
replacement, rewiring, opposite shifts and full normalization. The `range-activation` omission must fail their nonzero expected actions;
`range-retained-activation` clears the bit immediately after installation and
must fail retained-action reads. Existing rotation, exposure and point-output omissions
remove their newly unexhibited scalar read rows as well as the intended call,
so those mutations continue to reach the behavioral oracle rather than failing
compilation. No expected geometry or detection requirement changes. The after profile must reduce inherited node-read
calls; otherwise this bound has not addressed the observed cause. The timing
comparison retains main and cf12c609, replaces the old pre-frontier cohort
with 58b16da for a direct reader before/after, and keeps the patched frontier;
each has a twin, and every X5 kind is interleaved in both modes and two rounds.
HTML5 sentence/block must recover the patched-frontier cost while retaining
the font-size gain. Until these measurements pass, the reader repair is a
proposal, not a reported speedup.


The reader implementation passes [layout-check 37843507652](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37843507652)
at aa560f9. The subsequent oracle and range-falsification results are recorded
under [reader validation](#reader-validation-and-review); the completed latency comparison below shows a partial repair, with sentence
cost still above the patched frontier. The
one-use initial profile workflow is retired after its captured evidence above;
the same phase-checked profiler remains wired to the reader comparison.


### Root-font refusal: criterion before capture

The reader-only implementation is frozen for its ten-cohort comparison before
adding this diagnostic. The next hosted sample runs the correctly styled
ECMA262 first root-font edit and undo with the production compiler and native
Ubuntu toolchain, retaining the independent full-layout comparison. The new
leaf counters record actual failed guards, rather than inferring a cause from
final extents. Each independently processed leaf returns a refusal count and
reason bits; disjoint branches reduce the counts by addition and reasons by
bitwise union. No shared counter write orders leaf work. The failed attempt's
counts survive the following full replay through `UpdateCounts` aggregation.

The public `frontier_counts` contract owns the bit meanings: clean, lineless,
nonpositive-height, float, atomic, changed-width, changed-left, missing-slot,
new-through-output, changed-height and changed-last-baseline. Admission reports
its first failed guard; after a completed break, height and baseline changes
can both be recorded. Context-input refusals are outside these leaf counters.
The oracle appends both fields together after its boundary counts; historical
logs remain readable, while partial, contradictory and unknown-bit diagnostic
records are rejected. Independent constants cover clean/lineless reason codes
and multi-branch count/bit reduction; hosted protocol cases reject missing
fields and inconsistent records.

Changed-extent refusal is supported only if the observed bits include changed
height or last baseline after a speculative break. Admission-only refusal
rejects that explanation and must be addressed before treating non-stationary
restacking as the root-font remedy. Equal final dumps do not establish that
dirty work can be skipped. This diagnostic changes no admission or publication
rule and makes no new latency claim.


### Root-font refusal result and contract decision

[Hosted diagnostic 37845453577](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37845453577)
passed at ddb4e6b1ce5d397b9a3e8fe40d20fd0a2c027791 with production
wf-f949e676acfa, Clang 18.1.3, on Ubuntu 24.04 / Linux 6.17.0-1022-azure,
an AMD EPYC 9V45 host exposing four CPUs. This sequential correctness sample
uses the first ECMA262 12px edit and undo, the page's ecmarkup/print sheets,
and the ordinary full-layout comparator. It is not a latency comparison.
The artifact retains source/pin, input and binary hashes, raw records and the
exact two-edit script. The complete process took 7.05 seconds; no larger
root-font diagnostic batch was needed to identify this guard.

| Edit | Prepared | Frontier refused leaves | Reason bits | Boundary entries | Replay-held entries |
|---|---:|---:|---:|---:|---:|
| 12px | 41 | 41 | 2: no retained lines | 41 | 112,817 |
| Undo | 41 | 41 | 2: no retained lines | 41 | 112,817 |

All 41 refused leaves fail the lineless admission guard before speculative
breaking. The reported 41 breaks belong to subsequent full replay; they do
not show changed extents in the frontier. Neither changed-height bit 512 nor
changed-last-baseline bit 1024 appears. The observed reason therefore rejects
the earlier inference that changed extents caused this attempt's refusal; it
does not establish what fresh outputs would do if the guard were broadened.
Both incremental results match full layout and the base dump, with hash
`eb35ffcdb2ac7a51` and 19,024,863 bytes. Equal dumps still do not justify
skipping marked preparation, breaking or publication. The capture checker
also rejected missing refusal/reason fields and a duplicate diagnostic row.

The non-stationary implementation step is paused at the following choice;
the reader comparison and its validation continue independently. The existing
stationary contract explicitly excludes lineless paragraphs and line-presence
transitions, so extending it requires a contract and its own falsifiers.
No non-stationary admission or publication behavior has been changed.

---

**Should root-font work first handle retained lineless paragraphs?**

**Background.** The measured refusal is 41 lineless leaves on both edits,
not a post-break extent change. Full replay still holds 112,817 entries.
The original restack rationale does not identify this guard's replacement.

**Options.** A — First specify and implement bounded processing of retained
lineless paragraphs, preserving preparation, breaking and publication, with
explicit refusal for unsupported line/topology transitions. Recommended:
it addresses the measured guard while preserving independent paragraph work;
it requires new empty-source and line-transition falsifiers. B — Continue
with general non-stationary restacking and extend that contract to lineless
paragraphs too. This keeps the broader direction but adds convergence and
range-displacement machinery without evidence that this edit needs it.
Both options must state the true placement/publication dependencies and
retain the existing serial owner writes pending the Whitefoot proof gap.

**Confidence 4/5.** The observed counter settles the current guard. It does
not yet establish the fresh lineless outputs or their publication needs.
The owner's choice is pending; neither option is an approved replacement.

---


### Reader validation and review

The reader implementation frozen at fdc230806e791a793217a3fd9185d446a0f34023
passes [all 14 oracle jobs, 37844135717](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37844135717)
and [all 19 focused range mutations, 37844135744](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37844135744).
The page jobs compare every X5 kind in both modes: 20 edits per ECMA262 kind
and 60 per HTML5 kind, with zero differences/refusals and identical sequential
and parallel results. Both pages' block edits also pass zero-fallback checks.
The broad job includes the generated frontier fixtures and legacy style-marking
route. Each range mutation compiled and reached its intended behavioral
detector; disabling activation and prematurely clearing it both fail the
independent range constants. This is the focused range suite, not a rerun of
every unrelated M2 mutation.

The refusal-counter revision ddb4e6b passes the
[counter-protocol checks, 37845453324](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37845453324),
including missing fields, contradictory zero values and unknown reason bits;
the two-edit root sample supplies its actual sequential runtime evidence.
At ef54555cba11df90589525b1be5bf591e0b0e4de,
[make check 37848126355](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37848126355)
and [layout-check 37848126228](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37848126228)
pass. The gate includes the document self-test, 21 design-checker tests and
design lint. These later changes add diagnostic counters and repair prose;
the reader timing binary remains the earlier frozen revision for attribution.
No local build, test, check or performance measurement ran, and no adopted
Whitefoot pin or submodule moved.

A separate read-only review inspected the complete task diff from 58b16da,
changed regions and directly affected consumers under every applicable
A/D/C/T/R/M/V group, including G1–G3 and DC1–DC4, then reviewed the root
result and local repairs. It read `design/pipeline.md` and
`design/pipeline/layout.md`; the task adds one proposed decision without adding
a node or approval log. The repaired findings are: recursion suppression and
startup contamination in the profiler; overbroad parallel counter attribution;
mutation effect rows that previously prevented behavioral execution; a TODO
claim of speculative breaks unsupported by the old counts; and a reader
comment that omitted active-owner parent walks. A later metadata-only repair
selects the commit trailer explicitly for future synthetic timing commits,
with no change to their source, compiler or the running comparison.

There is no outstanding source finding within that review scope. The timing
and after-profile result below establish a partial reader improvement, and the
root-font contract and implementation await the decision above. Finite fixtures and source inspection
do not prove the general layout arguments. The existing Whitefoot owner-write
proof gap still blocks adoption, with serial owner writes unchanged; this work
found no additional Whitefoot gap. No pull request or adoption merge is made.


### Owner-local reader bound: ten-cohort result and remaining path

[Hosted comparison 37844135644](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37844135644)
measures the reader implementation at fdc230806e791a793217a3fd9185d446a0f34023
before the diagnostic counters. Ten independent builds use wf-0b7f5c5b9854
and LLVM 22 on one AMD EPYC 7763 runner exposing four CPUs, Ubuntu 24.04 /
Linux 6.17.0-1022-azure, with WF_WORKERS=4. The same two forward/reverse rounds
contain 480 raw timing files and 19,200 edit records: 20 edits per ECMA262
kind and 60 per HTML5 kind. Main is 8fbc1601785cee70265da1eac4d99589fc6fb67c,
cf12 is cf12c609e1c00f86bb431fab4e92f5dca2bf94f2, range-before is
58b16dae2770a774189370d4d2e5b74abc1a2fd0, and frontier is
3393042d79efe1ada22129b950a610ffae4508aa with `frontier-span.patch`.
Each has an independent twin. Values are upper-median update microseconds,
round 1/round 2; these are same-host measurements, not comparisons of absolute
numbers with earlier hosts.

| Page | Kind | Mode | Main | Main twin | cf12 | cf12 twin | Range before | Before twin | Frontier | Frontier twin | Reader | Reader twin |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ecma262 | word | seq | 101/99 | 119/99 | 106/106 | 116/119 | 106/107 | 106/108 | 111/123 | 108/120 | 107/107 | 107/106 |
| ecma262 | word | par | 172/160 | 164/164 | 182/183 | 172/185 | 194/183 | 181/181 | 178/175 | 179/179 | 183/193 | 176/188 |
| ecma262 | sentence | seq | 222/227 | 242/252 | 754/778 | 797/718 | 139/136 | 138/137 | 150/149 | 152/153 | 144/140 | 143/146 |
| ecma262 | sentence | par | 298/294 | 327/328 | 681/745 | 706/673 | 237/230 | 236/236 | 240/233 | 245/246 | 238/219 | 232/227 |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | fontsize | seq | 1272/1150 | 1114/1240 | 9242/9005 | 9141/8261 | 500/494 | 491/470 | 530/497 | 502/507 | 522/491 | 466/509 |
| ecma262 | fontsize | par | 1705/1796 | 1648/1477 | 9472/8922 | 9513/8786 | 825/837 | 1019/901 | 875/723 | 715/713 | 753/1006 | 742/731 |
| ecma262 | rootfont | seq | 29885/28381 | 29683/28901 | 114617/111466 | 112371/111038 | 113039/112768 | 113047/116440 | 109407/109273 | 108782/111529 | 114297/115150 | 115889/114122 |
| ecma262 | rootfont | par | 67086/66661 | 64904/63461 | 216157/215377 | 216183/214020 | 199556/197662 | 200385/200445 | 180679/178732 | 175295/180602 | 205130/205711 | 205475/206373 |
| ecma262 | block | seq | 528758/525776 | 531171/526326 | 116/111 | 112/110 | 117/117 | 116/116 | 120/118 | 119/120 | 113/117 | 115/116 |
| ecma262 | block | par | 376258/361573 | 375225/372235 | 186/183 | 189/184 | 211/198 | 204/186 | 195/197 | 209/187 | 190/194 | 189/192 |
| html5 | word | seq | 74/76 | 73/75 | 82/79 | 78/78 | 82/80 | 81/81 | 84/83 | 82/82 | 82/82 | 83/82 |
| html5 | word | par | 118/121 | 123/120 | 129/127 | 126/129 | 132/136 | 133/132 | 131/130 | 131/131 | 136/135 | 130/132 |
| html5 | sentence | seq | 240/218 | 222/222 | 332/318 | 328/318 | 662/655 | 649/661 | 353/346 | 333/331 | 495/490 | 506/492 |
| html5 | sentence | par | 344/321 | 314/332 | 373/390 | 353/353 | 604/614 | 619/603 | 367/353 | 353/349 | 512/542 | 541/538 |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | fontsize | seq | 755/729 | 663/720 | 1921/1916 | 1907/1684 | 1317/1326 | 1350/1315 | 1467/1771 | 1533/1576 | 960/997 | 1014/975 |
| html5 | fontsize | par | 832/759 | 706/785 | 2313/2142 | 2239/2174 | 2115/2270 | 2133/2230 | 2025/2116 | 1998/1924 | 1650/1622 | 1696/1680 |
| html5 | rootfont | seq | 615144/614068 | 617879/617138 | 766099/769813 | 759389/761600 | 802388/800519 | 804795/798973 | 796527/792803 | 787343/793048 | 808454/800712 | 805085/803271 |
| html5 | rootfont | par | 358008/356089 | 358841/358907 | 557892/556175 | 556490/555626 | 560226/560106 | 563921/564332 | 538409/537190 | 537262/531986 | 564464/563306 | 561301/559857 |
| html5 | block | seq | 599181/588656 | 604307/594482 | 558/569 | 563/589 | 729/741 | 729/745 | 589/606 | 585/569 | 597/594 | 581/576 |
| html5 | block | par | 433331/431983 | 447035/421804 | 666/674 | 659/676 | 713/730 | 709/728 | 668/680 | 692/673 | 645/644 | 646/645 |

The bound improves HTML5 sentence from 662/655 to 495/490 us sequential,
and from 604/614 to 512/542 parallel, beyond the corresponding twin spread.
It does not recover frontier's 353/346 and 367/353. HTML5 block parallel is
645/644 against frontier 668/680 and cf12 666/674; sequential 597/594 overlaps
frontier's 589/606 but remains above cf12 558/569. The HTML5 font-size gain is
retained and enlarged: 960/997 sequential and 1,650/1,622 parallel, compared
with frontier 1,467/1,771 and 2,025/2,116. Neither that observation nor lower
instruction counts makes the reader step complete.

The primary reader fails 12 literal round cells: ECMA262 root-font sequential
and parallel in both rounds (3.83/4.06 and 3.06/3.09 times main); HTML5 sentence
sequential in both rounds (2.06/2.25 times main); HTML5 font-size parallel in
round 2 (2.14 times main); ECMA262 block sequential in round 2 (117 > 111 us),
parallel in both rounds (190 > 186 and 194 > 183); and HTML5 block sequential
in both rounds (597 > 558 and 594 > 569). The table retains all twins so small
literal failures are not mistaken for an attributable regression.

The sequential after-profile uses the same 60 update-return parts and
phase-checking procedure, with Valgrind 3.22; every part's self sum equals its
summary and each cohort has one update thread. Compiled inherited-reader
calls remain 179,067. Node-read calls fall from 822,700 to 407,096 (50.5%).
Inherited self instructions plus their slot-reader callees fall from
78,862,686 to 44,182,629; total update instructions fall from 216,949,190 to
177,409,407, against frontier's 200,312,065. This supports the causal reader
improvement but leaves inherited reads at 24.9% of the new total. The profile
is sequential attribution; native parallel timings are separate observations.

Of the remaining inherited-chain instructions, 43,143,174 come through
`block_local`. Positioned plans separately resolve their owning block and
then the nearest positioned containing block: `splice_position_plan` calls
`block_origin` 15,930 times for 35,872,670 inclusive instructions, while
`chain_anchor` calls it 10,920 times for another 25,661,130. Their overlapping
ancestry is immutable during plan creation. The 30 `splice_finish` calls
spend 98,736,381 inclusive instructions in `splice_position`. These values
identify the next reader work; they do not establish its future speedup.

### Shared positioned ancestry: criterion before implementation

The next reader repair resolves an independent positioned plan's owner and
containing-block origins in one ancestry walk. It retains two accumulators:
the owner starts at the child's formatting block, and the containing-block
accumulator starts at the first non-static ancestor. Each effective local
origin is read once and prepended to each applicable accumulator. It never
subtracts a prefix from an accumulated total, so it preserves each original
saturating association, late visual narrowing, one content adjustment and
the subsequent border addition. The containing block's dimensions and style
are read at the same nearest ancestor as `chain_anchor`.

This combines the existing published-geometry readers only. Raw and hybrid
reference phases keep their defined old/current readers. The true chain is
block-parent discovery and the accumulation along that chain, followed by
containing-block settlement before child writes. Independent child plans
remain independent; no shared mutable cache, dense block scan or new order
between children is introduced. Separate duplicate walks repeat immutable
reads; a shared cache would instead require invalidation and publication not
needed for this repair. The existing serial certificate publication remains
unchanged pending the recorded Whitefoot proof gap.

The existing nested positioned, relative-inset, fixed-axis and moved-owner
fixtures compare with independent full layout in both modes. Nonzero context
content adjustment in the new published reader remains unverified by a
discriminating fixture: the table atomic case contains no positioned child,
and table ancestry refuses before the local splice. Its prior green result
covers the full/raw bridge. The shared reader preserves the content-adjustment
expression and order in source; that is not execution evidence for this path.
Omitting either accumulator must cause a behavioral difference; if these
fixtures do not distinguish it, add a specific independent fixture before
claiming coverage. The matched profile must show fewer `block_local` inherited
reads than the owner-local bound, and the native pilot must reduce sentence
cost beyond its paired controls. Otherwise the shared walk is insufficient.
The complete acceptance remains sentence/block no slower than the patched
frontier, preservation of font-size gains, and all X5 cells within the
unchanged main/cf12 gates; a promising pilot is not acceptance.


### Shared positioned ancestry: pilot result

[Hosted pilot 37859507860](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37859507860)
compares 6424e28ee94f7196518b9f3f8dfc910d3a727985 with the same-counter before
f402783aa7e6f14224e96b52ad3d9af2836e18b4 and the patched frontier, each with an
independent twin, on an AMD EPYC 9V45 runner exposing four CPUs. The Ubuntu
24.04 / Linux 6.17.0-1022-azure, wf-0b7f5c5b9854, LLVM 22 and WF_WORKERS=4
settings match within this run. The six-build pilot has 72 raw files and
4,320 edits, covering HTML5 sentence, font-size and block in two interleaved
forward/reverse rounds. Values are upper-median microseconds, round 1/round 2:

| Kind | Mode | Before | Before twin | Frontier | Frontier twin | Shared walk | Shared twin |
|---|---|---:|---:|---:|---:|---:|---:|
| sentence | seq | 274/283 | 277/290 | 195/179 | 188/197 | 219/227 | 258/252 |
| sentence | par | 328/358 | 324/317 | 195/189 | 191/193 | 304/309 | 334/319 |
| fontsize | seq | 594/585 | 582/598 | 1128/1032 | 956/1058 | 590/614 | 631/624 |
| fontsize | par | 1028/1029 | 1002/1071 | 1261/1284 | 1275/1224 | 941/1056 | 1029/1020 |
| block | seq | 354/363 | 358/360 | 361/357 | 352/370 | 318/302 | 316/322 |
| block | par | 422/425 | 433/431 | 428/387 | 426/391 | 395/430 | 414/401 |

Sequential sentence improves beyond the paired control spread, but its
219/227 us and twin 258/252 remain above frontier 195/179 and 188/197.
Parallel sentence still trails frontier substantially; overlapping before
and after twins do not establish a general parallel gain. Block sequential
improves, while its parallel difference lies within control variation. The
font-size gain over frontier survives. The pilot rejects completion of the
reader repair and supplies no new main/cf12 acceptance claim.

The 60-part sequential profile reports 177,967,660 before instructions and
154,817,770 after. Inherited calls fall from 179,067 to 114,357; node-read
calls from 407,096 to 243,326. Inherited self plus slot-reader instructions
fall from 44,182,629 to 26,617,149 (14,731,037 self and 11,886,112 callees).
Of the remaining chain, 25,577,694 instructions come through `block_local`.
The before total differs from the earlier fdc2308 profile because this before
includes diagnostic counters; the inherited counts are identical. These
instruction observations do not explain all native latency variation.

The shared-walk revision passes [make check 37859507784](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37859507784)
and [layout-check 37859507884](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37859507884).
Both [new mutation jobs 37859507855](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37859507855)
compile and each produces 18 incremental/full differences on the positioned
fixture, against a clean baseline and its six required splice paths. The
step-5 oracle job in [37859507852](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37859507852)
passes, including 20 ECMA262 and 60 HTML5 block edits using local splices;
the broader run subsequently passes all 14 jobs. Read-only review found and fixed
the mutation step's missing selector and an overbroad content-adjustment
coverage claim; nonzero adjustment on this new path remains unverified.
No arithmetic or dependency finding remains in the inspected shared walk.

### Geometry-only inherited reads: criterion before implementation

The remaining geometry readers request `RangeInherited`, which resolves and
returns every geometry, semantic and basis channel even though `block_local`,
`paragraph_local` and `child_local` consume only geometry. The next repair
gives that query its own field-narrow reader: one slot lookup returns its
parent, applicability and the requested own or pending-child geometry. The
geometry walk stops at the absent parent without another directory lookup,
skips non-placed anchors, and retains the owner-local presence bound. It
accumulates strict-ancestor geometry separately and adds the own geometry
last, preserving the existing association rather than relying on cancellation.
Semantic and duplicated Open readers keep the existing complete view.

Both candidates follow the same immutable parent chain; reading a single
channel adds no cross-child dependency, cache, shared counter or publication
stage. The distinction is the data each query asks for, not a change to range
membership or action lifetimes. The public placement consumers keep their
existing frame, applicability and saturation contracts. This introduces no
proof-only representation, alias check or substitute for unsupported writes.

The existing independent range constants must exercise both the complete and
geometry-only queries against the same explicit expected displacement, and
separate omissions of own and inherited geometry must each fail. Ordinary
range, rotation, insertion, removal, point-retirement and full-normalization
fixtures remain wired. Passive profile counters count both inherited-reader
functions and both slot-reader functions, with independent decoder examples
for the new edge names; renaming a path must not look like removing its work.
The prior criterion is lower inherited-query instructions than the shared
walk and native sentence cost outside its before/twin spread. Sentence and
block must still recover frontier cost, font-size gains must remain, and the
final ten-cohort comparison must report every X5 acceptance cell.


### Geometry-only reader: pilot result and remaining attribution

[Hosted pilot 37861961788](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37861961788)
compares 50a898e4d09feae50e19986773cb27dfd7e85040 with shared-walk before
6424e28ee94f7196518b9f3f8dfc910d3a727985 and the patched frontier, each with an
independent twin. This run uses an AMD EPYC 7763 runner exposing four CPUs,
Ubuntu 24.04 / Linux 6.17.0-1022-azure, wf-0b7f5c5b9854, LLVM 22 and
WF_WORKERS=4. Its 72 raw files contain 4,320 edits in the same two interleaved
rounds. Upper-median microseconds, round 1/round 2:

| Kind | Mode | Before | Before twin | Frontier | Frontier twin | Geometry query | Query twin |
|---|---|---:|---:|---:|---:|---:|---:|
| sentence | seq | 406/404 | 418/400 | 343/329 | 332/352 | 358/371 | 358/357 |
| sentence | par | 486/485 | 504/492 | 355/355 | 371/360 | 473/480 | 458/481 |
| fontsize | seq | 947/943 | 951/939 | 1491/1573 | 1590/1582 | 851/854 | 860/862 |
| fontsize | par | 1737/1694 | 1657/1652 | 1925/1972 | 2005/1944 | 1535/1584 | 1525/1554 |
| block | seq | 491/493 | 499/476 | 568/572 | 571/589 | 443/439 | 436/441 |
| block | par | 603/599 | 608/606 | 658/662 | 688/677 | 592/596 | 607/586 |

The query reduces sequential sentence, sequential block and font-size in both
modes beyond the respective before/twin spread. HTML5 block is now below the
frontier in both modes, and the font-size gain remains. Sentence still misses
the frontier target: sequential 358/371 against 343/329, and parallel 473/480
against 355/355. The reader task is not complete; this pilot has no main/cf12
cohorts and supplies no new all-X5 acceptance result.

The combined counters include both inherited functions and both slot-reader
functions. Over 60 update parts, calls remain 114,357 (98,118 now use the
geometry-only query), and node-read calls fall from 243,326 to 210,964. Their
combined self/callee instructions fall from 26,617,149 to 18,600,391
(10,540,911 self plus 8,059,480 slot readers); total update instructions fall
from 154,817,770 to 146,894,464. Each part's self sum matches its summary;
both decoder families and omitted-edge controls pass. This is sequential
instruction attribution, not an explanation of the remaining parallel gap.

At this revision [make check 37861961737](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37861961737),
[layout-check 37861961793](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37861961793),
the step-5 job of [oracles 37861961785](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37861961785)
and [both geometry omission jobs 37861961787](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37861961787)
pass. Each omission compiles and fails the independent range constants.
The broader oracle run is still pending. The preceding shared-walk revision
now passes all 14 jobs of [37859507852](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37859507852).
Read-only review found no geometry-query or counter-wiring defect, and verified
its association, applicability and absence of new shared state or a Whitefoot
workaround. General soundness and nonzero content adjustment on the new
published path remain outside the finite execution evidence.

### Remaining sentence cost: native profile criterion

Before changing placement representation again, distinguish retained reader
work from parallel runtime work on the actual HTML5 sentence pair already
used by the Callgrind pilot (edits 35/36). Frozen frontier and geometry-query
drivers, each with a twin, run the same restoring pair in sequential mode,
parallel mode with one worker and parallel mode with four workers. This is
an edit-loop diagnosis, not a replacement for full-script acceptance.
Two-edit native samples bound a repeated batch before it runs, with the
previously used 30,000-pair cap and a per-process timeout. Both setup and the
restoring pair remain identical across the controls.

Earlier hardware-event DWARF profiles lost samples even at 99 Hz and supplied
no quantitative attribution. The repeat uses the software `cpu-clock:u`
event, 99 Hz, a 4,096-page buffer and 4,096-byte DWARF stacks. Sampling starts
five seconds after process launch; observed base/first-edit timestamps must
precede that boundary, and summed sequential update durations must exceed
ten seconds. Overall process duration includes profiler finalization and
cannot establish that condition. Missing or late startup markers and a
short edit batch reject the profile. The
[perf record documentation](https://man7.org/linux/man-pages/man1/perf-record.1.html)
owns delay, frequency, buffer and stack options. Every raw perf record,
loss report, sample count and thread identity is retained. Quantitative
attribution requires at least 1,000 user CPU event samples in every cohort,
zero recorded loss, and usable stacks with report/script diagnostics inspected.
Any failure rules out quantitative attribution; lower frequency
alone is not assumed to repair loss. These software samples describe user CPU
work after startup, including edit-loop overhead, not blocked time or a
precise wall-time decomposition.

Reader attribution requires visible post-startup reader samples that separate
from the frontier controls. A runtime attribution requires an observed
runtime mechanism and a corresponding difference between the one- and
four-worker controls; slower parallel medians alone establish no compiler
gap. If neither distinguishes the residual, record it as unresolved rather
than selecting another representation from timing alone. The one-use native
profiling workflow and driver script are retired after capturing this result.

Review RV9 tightened the duration and sample admission criteria after the
first frozen capture began but before its results were inspected. That
capture records summed edit durations and raw samples, so it can be audited
against the stronger criteria; it did not run the repaired harness. The
repair additionally records last-edit receipt time and retains report/script
stderr. A receipt timestamp only corroborates execution duration.

The geometry reader's all-kind comparison uses ten independent builds of
main 8fbc1601785cee70265da1eac4d99589fc6fb67c, cf12c609e1c00f86bb431fab4e92f5dca2bf94f2,
the original range head 58b16dae2770a774189370d4d2e5b74abc1a2fd0, patched
frontier 3393042d79efe1ada22129b950a610ffae4508aa and the current reader,
each with its twin. Both forward/reverse rounds cover every X5 kind and both
pages in sequential and four-worker parallel mode. It supplies the complete
acceptance cells missing from the three-kind pilots; it does not presume that
the remaining sentence gap is resolved. Runtime code is unchanged from
50a898e4d09feae50e19986773cb27dfd7e85040.

The native capture's remaining join observations are followed by hosted
inspection of the same frozen binaries, without rebuilding or modifying the
renderer. The inspection retains binary hashes, symbol addresses, unwind
entries and disassembly of effective transfer reads and runtime joins. The
question is whether `effective_output`'s independent `boundary_output` and
`range_inherited` calls introduce a fork/join at each point read. Absence of
that generated call site rejects this explanation. Presence alone does not
attribute the complete latency gap or establish that a different source
spelling is warranted; any compiler granularity gap needs its own minimal
example and owner decision.

### Remaining sentence cost: native capture and attribution limit

[Hosted capture 37865310538](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37865310538)
uses the frozen 50a898e reader and patched-frontier binaries from the geometry
pilot, including both independent twins, on an AMD EPYC 9V74 host exposing
four CPUs (Ubuntu 24.04, Linux 6.17.0-1022-azure, perf 6.17.13,
wf-0b7f5c5b9854 and LLVM 22). Two-edit samples took 1.55–2.38 seconds
including startup; their largest pair cost, 1,392 us, selected the existing
30,000-pair cap. Every cohort completes 60,000 numbered edits, for 720,000
records total. These are profiled repeated-pair medians, including any
profiler perturbation; they do not replace X5 acceptance or an uninstrumented
performance comparison.

| Setting | Frontier | Frontier twin | Geometry reader | Reader twin |
|---|---:|---:|---:|---:|
| Sequential, one worker | 305 | 303 | 384 | 387 |
| Parallel, one worker | 298 | 297 | 384 | 384 |
| Parallel, four workers | 336 | 337 | 524 | 523 |

All observed first edits arrive before sampling begins, at 1.46–2.34 seconds;
summed edit execution is 17.896–31.539 seconds, independently exceeding the
repaired ten-second admission bound. Every cohort has 1,534–11,389 user CPU
event records, above the 1,000-sample minimum fixed before inspection. Perf
reports zero lost samples in all twelve cohorts; raw LOST records and record
stderr contain none. The original report/script stderr remains in the job
log and emits no diagnostic. This evidence meets the strengthened duration,
count and loss criteria even though the original capture ran the earlier
harness. Its late/missing marker controls ran; the added short-batch harness
control has not run.

Call-stack quality does not meet the quantitative caller-attribution criterion.
Many stacks contain unresolved or invalid intermediate frames; a one-frame
worker stack alone is not evidence of truncation. For example, reader parallel/four-worker has 10,076 one-frame records
out of 11,383; 1,011 records contain an unknown or all-ones frame. No caller
percentage or decomposition of the latency gap is accepted from these stacks.
Raw sampled instruction pointers still locate `range_geometry`, `slot_geometry`,
`block_local` and positioned-plan work after startup. Four-worker captures
also contain `wf__par_join` and `wf__par_worker_main`; their presence alone
neither proves a compiler defect nor distinguishes useful work from waiting.
The sampled windows also differ (about 17.8 seconds for frontier and 29.2
seconds for the reader in four-worker mode), so raw sample-count ratios are
not per-edit cost ratios. The binary call-site inspection below tests the
specific point-reader fork hypothesis. No dependency has been added to the renderer to suppress parallel
execution, and no new Whitefoot gap is yet established by this capture.

### Point-reader task grain: emitted call site and pending direction

[Hosted binary inspection 37866617553](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37866617553)
confirms the same call site in both reader twins. All eight inspected binary
hashes match the native capture. In the parallel reader, `effective_output`
publishes `wf__par_thunk_layout.effective_output.0`, runs `range_inherited`
on the calling lane, then calls `wf__par_join` before consuming the returned
transfer. The thunk contains the counted point lookup and copies one
184-byte stored transfer; it does not traverse a flow suffix. Publication and
lane bookkeeping are inlined into the caller, so their samples can appear
under `effective_output` rather than a named runtime helper. The frontier has
no `effective_output` symbol or corresponding thunk.

The relevant compiler source at the timing revision
[0b7f5c5b9854](https://github.com/Ming-Research/Whitefoot/blob/0b7f5c5b98547dd27deb9691aed36281e350576b/compiler/src/lowering/builder/call_grain.rs)
keeps an independent call offer whenever its callee reaches recursion,
regardless of its static work; otherwise the threshold is 150,000 units.
`boundary_output` reaches recursive `slot_output`, whose directory descent
can be short. The natural dependency is two independent reads followed by
combining their results. There is no algorithmic dependency between them.

Minimal semantic example (a fragment, not a standalone compiler trial):

```text
let stored = read_transfer(pages: pages, slot: slot);
let inherited = read_ancestor_actions(pages: pages, slot: slot);
return shift_transfer(output: stored, delta: inherited);
```

`read_transfer` descends an immutable paged tree and returns one stored
transfer; `read_ancestor_actions` sums the actions on its parent path. The
emitted reader reproducer offers the first lookup as a task even for a short
path; it need not execute on a different worker. This extends the existing Whitefoot point-query task-grain concern in
`docs/todo.md`; it identifies the mechanism, not its exclusive latency cost.
A standalone minimized trial and a compiler-only before/twin comparison have
not run. Sequential sentence cost also remains above frontier, so a grain
repair alone is not claimed to meet the reader target. Further reader
redesign pauses at this choice while the complete acceptance measurement and
validation finish. Existing independent calls and serial owner-motion writes
are preserved.

---

**Should Whitefoot's point-read task grain be investigated before another reader redesign?**

**Background.** The reader repair removes most inherited instructions, but
sentence still misses the pre-range target. The frozen binary now shows a
single transfer lookup published beside an ancestor read and joined before
use. The native sampled instruction pointers include that caller and joins;
invalid caller chains and different sample windows prevent a causal latency
percentage. The compiler's recursion exemption is sufficient to retain a
call reaching this lookup; no ledger comparison isolates it from the static-work criterion.

**Options.** A — Have the Whitefoot work minimize and evaluate this point-read
grain before another renderer representation change. Recommended: it keeps
the natural dependencies and addresses the observed generated mechanism;
it costs a compiler/runtime investigation and may leave sequential placement
work to repair afterward. B — Leave the current reader proposal unaccepted
and defer further reader redesign until the already recorded Whitefoot
task-grain concern is addressed. This avoids a second investigation now but
delays sentence acceptance and provides no date or guarantee for its resolution. Neither option serializes independent reads,
forces a worker count or changes the acceptance threshold.

**Confidence 4/5.** The emitted task and the static recursion exemption are
established. Their share of the remaining regression, the best compiler
remedy and its transfer to the complete X5 matrix are unverified.

---

### Geometry reader: completed correctness evidence

The runtime remains unchanged from 50a898e4d09feae50e19986773cb27dfd7e85040.
[All 14 oracle jobs, 37861961785](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37861961785),
pass the broad fixtures, step-5 checks and every X5 kind on both pages in
sequential and parallel modes. The page jobs cover 20 ECMA262 or 60 HTML5
edits per kind and mode, with identical full/incremental dumps and zero block
fallbacks. [All 21 range mutation jobs, 37865310392](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37865310392),
compile and reach their behavioral detectors against clean baselines,
including both new geometry-channel omissions and retained normalization.
The separate positioned-accumulator mutations remain covered by their
passing shared-walk run above. This is the affected range suite, not a claim
that every unrelated M2 mutation was rerun.

At 4e2c11f04c2f7c5698bba019a517c9fbb4e4f0a3,
[make check 37866617542](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37866617542)
and [layout-check 37866617548](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37866617548)
pass with the production pin. The native profiling and binary-inspection
workflow and script are retired after preserving their evidence. All builds,
tests, checks and timing ran on GitHub-hosted runners; local work was source
editing, repository inspection and analysis of downloaded evidence.
No pin, submodule or approval log changed. The completed all-kind timing
result is below, and neither owner direction card has been ruled on.

The separate read-only completion review covers the complete task-base
58b16da..4e2c11f diff, directly affected consumers, the current result/TODO
updates and diagnostic retirement: all 19 resulting changed paths, the
project checklist's applicable A/D/C/T/R/M/V groups and G1–G3/DC1–DC4,
including `design/pipeline.md` and `design/pipeline/layout.md`. No source
finding remains outstanding. RV1–RV3 corrected profile boundaries and
attribution scope; RV4 and RV7 repaired mutation effect rows and wiring;
RV5–RV6 corrected unsupported diagnostic and reader descriptions; RV8
removed an unproved fixture claim; RV9 corrected edit-duration admission;
RV10 corrected the section reference and distinguished a task offer from
execution on another worker. The form evidence remains seven nodes, depth
one, 66 to 67 decisions against the task base and 24 rejections.
General design arguments, nonzero content adjustment through the new
published positioned reader, the retired harness's unexecuted short-batch
control and a minimized compiler-only grain trial remain unverified.
The read-only evidence addendum independently parsed all 480 raw timing
files and 120 compressed profile parts, verified every table median,
acceptance failure and inherited-read total below, and checked the final
result/TODO prose over 992ffcd. It found no further issue. Final-head hosted
gates and remote verification are delivery checks; no owner approval or
completion of the paused implementation steps is implied.


### Geometry reader: ten-cohort result

[Hosted comparison 37866007483](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37866007483)
succeeds at f29dcde6f3a0cc9f70f7f082d222db1773445b83, whose runtime is
unchanged from 50a898e4d09feae50e19986773cb27dfd7e85040. The ten independent
builds are main 8fbc1601785cee70265da1eac4d99589fc6fb67c, cf12c609e1c00f86bb431fab4e92f5dca2bf94f2,
range-before 58b16dae2770a774189370d4d2e5b74abc1a2fd0, the patched frontier
3393042d79efe1ada22129b950a610ffae4508aa plus `frontier-span.patch`, and the
reader, each with its own twin. The main control has the same renderer and
pin as current main 9d720c49daf4de746d507f5b1400ea407e3dfc09; intervening
changes affect documentation and the vocabulary investigation's Makefile.
The measurement host is an AMD EPYC 7763 exposing four CPUs, Ubuntu 24.04.5,
Linux 6.17.0-1022-azure, Clang/LLVM 22.1.8, wf-0b7f5c5b9854 and
WF_WORKERS=4. The timing-only pin does not change the work branch's production
pin. All cohorts share the page, styles, fonts and edit scripts on this host.

The complete two forward/reverse rounds contain 480 raw timing files and
19,200 numbered edits: 20 per ECMA262 kind and 60 per HTML5 kind. These are
unprofiled upper-median microseconds, round 1/round 2. They are not compared
as absolute times with a different host's pilot.

| Page | Kind | Mode | Main | Main twin | cf12 | cf12 twin | Range before | Before twin | Frontier | Frontier twin | Reader | Reader twin |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ecma262 | word | seq | 101/100 | 104/119 | 119/119 | 110/107 | 120/107 | 118/116 | 113/116 | 120/124 | 112/107 | 109/116 |
| ecma262 | word | par | 162/164 | 160/165 | 178/180 | 178/188 | 185/191 | 177/198 | 183/188 | 192/180 | 180/187 | 181/177 |
| ecma262 | sentence | seq | 228/249 | 221/245 | 760/765 | 779/747 | 148/143 | 145/141 | 154/155 | 154/150 | 151/144 | 147/138 |
| ecma262 | sentence | par | 334/323 | 306/332 | 737/757 | 675/677 | 227/226 | 230/229 | 236/237 | 247/240 | 232/247 | 224/243 |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | fontsize | seq | 1275/1138 | 1611/1663 | 9380/9140 | 8210/9212 | 524/504 | 503/479 | 530/527 | 541/527 | 480/503 | 523/482 |
| ecma262 | fontsize | par | 1607/1695 | 1991/2027 | 9825/9402 | 9111/9160 | 865/852 | 873/775 | 750/850 | 743/718 | 745/784 | 737/919 |
| ecma262 | rootfont | seq | 28991/27826 | 31108/32443 | 113592/114077 | 112245/112759 | 121163/118514 | 119350/118302 | 115744/109431 | 118885/111866 | 116182/115852 | 120855/121796 |
| ecma262 | rootfont | par | 70559/63141 | 68100/69609 | 223822/220086 | 214862/217507 | 205687/203215 | 203949/203906 | 184945/182542 | 188363/183019 | 209840/210725 | 215146/214269 |
| ecma262 | block | seq | 532585/518370 | 555129/545896 | 119/116 | 121/114 | 119/121 | 119/119 | 118/122 | 134/120 | 116/119 | 122/119 |
| ecma262 | block | par | 374634/368477 | 395219/377648 | 185/207 | 186/188 | 190/201 | 196/196 | 196/189 | 216/188 | 196/192 | 191/209 |
| html5 | word | seq | 73/73 | 75/73 | 84/81 | 80/79 | 84/83 | 84/81 | 84/81 | 82/84 | 86/84 | 83/83 |
| html5 | word | par | 120/120 | 120/122 | 130/127 | 128/131 | 133/133 | 131/133 | 135/130 | 131/138 | 132/132 | 132/133 |
| html5 | sentence | seq | 236/218 | 220/219 | 323/326 | 321/339 | 648/671 | 688/680 | 355/339 | 335/337 | 361/366 | 359/354 |
| html5 | sentence | par | 340/314 | 342/331 | 345/373 | 358/346 | 620/614 | 610/615 | 355/377 | 360/399 | 461/484 | 453/456 |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | fontsize | seq | 764/803 | 793/708 | 2061/1983 | 1858/1796 | 1342/1371 | 1325/1336 | 1501/1488 | 1555/1503 | 870/860 | 854/825 |
| html5 | fontsize | par | 768/736 | 761/777 | 2342/2169 | 2105/2140 | 2199/2363 | 2284/2267 | 2079/1965 | 1941/1957 | 1521/1544 | 1558/1577 |
| html5 | rootfont | seq | 621884/621832 | 631431/623484 | 768593/770002 | 759687/769584 | 808825/818915 | 812900/824402 | 813977/810342 | 808991/805191 | 810300/814945 | 814386/810979 |
| html5 | rootfont | par | 361207/362765 | 366747/363055 | 563319/569207 | 559330/568705 | 566041/571591 | 576822/584619 | 551416/537318 | 547309/539117 | 575391/572831 | 571658/581770 |
| html5 | block | seq | 631204/636887 | 602985/612065 | 567/612 | 564/570 | 738/742 | 741/750 | 570/572 | 571/577 | 439/454 | 442/456 |
| html5 | block | par | 446901/474694 | 436301/443199 | 682/669 | 655/672 | 732/730 | 731/727 | 678/663 | 677/677 | 586/585 | 576/595 |

The complete reader repair lowers HTML5 sentence from 648/671 to 361/366 us
sequential and from 620/614 to 461/484 parallel, with both before and after
twins supporting the reduction. It still misses the patched frontier in all
four primary round cells: frontier is 355/339 sequential and 355/377 parallel.
The sequential first-round gap is small; the table retains twin variation
instead of interpreting every literal difference as an attributable cost.
HTML5 block now beats both controls in both modes and rounds: 439/454 us
sequential and 586/585 parallel, against frontier 570/572 and 678/663, and
cf12 567/612 and 682/669. Both reader twins also pass those block comparisons.
The font-size gain over frontier remains: 870/860 us sequential and
1,521/1,544 parallel, against 1,501/1,488 and 2,079/1,965, beyond their
respective twin spread.

**Acceptance still fails.** Against its primary controls, the reader fails
seven literal round cells: ECMA262 root-font sequential in both rounds
(4.01/4.16 times main) and parallel in both (2.97/3.34); ECMA262 block
sequential round 2 (119 > 116 us) and parallel round 1 (196 > 185); and
HTML5 font-size parallel round 2 (1,544 > 2 × 736 us, or 2.10 times main).
Every other primary all-X5/main and block/cf12 cell passes, but the additional
sentence/frontier target fails all four cells above.

The reader twin is compared with the corresponding main and cf12 twins,
not omitted from acceptance reporting. It fails ten cells: all four
ECMA262 root-font cells; all four ECMA262 block cells (sequential 122 > 121
and 119 > 114 us; parallel 191 > 186 and 209 > 188); and both HTML5
font-size parallel cells (1,558 > 2 × 761 and 1,577 > 2 × 777 us). These
are the same three failing workload families. The small block and font-size
threshold crossings are literal failures, not isolated causal regressions.
The twin also misses sentence/frontier in both modes and rounds.

Root-font work remains diagnostic only. All 80 primary-reader ECMA262
root-font records across both modes and rounds contain exactly 41 frontier
refusals with reason bit 2, 41 boundary entries, 112,817 replay-held entries,
three fallbacks and reason 7. This extends the production-pin two-edit
diagnostic to the complete timing workload at the timing compiler; none
records a post-break extent refusal. Root-font medians remain
116,182/115,852 us sequential and 209,840/210,725 parallel, versus main
28,991/27,826 and 70,559/63,141. No bounded lineless or non-stationary
contract or implementation has been added while the owner choice is pending.

The matched after-profile uses Valgrind 3.22 and the same 60 sentence edits
on the range-before and reader drivers. Each cohort has exactly 60
update-return parts on thread 2, with self sums equal to every summary.
The decoder's independent examples and the 400-outside-call exclusion probe
pass again. The page, script and UA hashes match the earlier geometry pilot.

| Across 60 sequential updates | Range before | Reader |
|---|---:|---:|
| Total instructions | 216,949,190 | 146,894,464 |
| Compiled inherited-query calls | 179,067 | 114,357 |
| Compiled node-read calls from inherited queries | 822,700 | 210,964 |
| Inherited-query self plus slot-reader instructions | 78,862,686 | 18,600,391 |

The reader executes 98,118 geometry-only query calls within the combined
inherited-query total. Inherited self instructions are 10,540,911 and slot
callees 8,059,480; the combined chain falls 76.4%, node-read calls 74.4% and
total update instructions 32.3%. These are compiled-call and instruction
observations, with the inlining and sequential-attribution limits already
stated; they are not mutable renderer counters or parallel wall-time shares.

The stop is now at the two owner direction cards, rather than unfinished CI:
choose the root-font lineless contract and whether to prioritize Whitefoot's
point-read grain investigation. The reader target is not met, and the
non-stationary implementation is not claimed. The passive inherited-read
profiler remains wired to the temporary timing workflow while this
acceptance investigation is open; the one-use native diagnostics are retired.


### Point-reader task grain: compiler-only comparison

Question: does the emitted point-read offer explain the reader's remaining
parallel cost? Comparison: the same sources built with the timing compiler
wf-0b7f5c5b9854 and with wf-b2209fd31035, a main-line release containing
Whitefoot #278 ("Call grain: exempt only recursion that offers its own
calls"), each with a twin. A parallel improvement of the reader beyond the
twins' spread, with the frontier unchanged, supports the account; no change
rejects it.

[Hosted run 37875294803](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37875294803)
built the reader head f184ee7 and the patched frontier 3393042 with each
compiler and timed 60 HTML5 edits per kind and mode in two reversed rounds
on one hosted Ubuntu 24.04 runner exposing four CPUs of an AMD EPYC 7763,
LLVM 22, `WF_WORKERS=4`. Every edit spliced without refusal or rebuild.
Median us, round 1/2, primary [twin]:

| kind, mode | frontier, old | frontier, #278 | reader, old | reader, #278 |
| --- | --- | --- | --- | --- |
| sentence, seq | 344/356 [334/340] | 355/356 [325/331] | 359/380 [373/376] | 373/354 [372/354] |
| sentence, par | 370/368 [387/384] | 358/366 [347/350] | 475/477 [459/478] | 341/327 [327/327] |
| fontsize, seq | 1477/1678 [1474/1860] | 1502/1805 [1742/1486] | 859/840 [843/851] | 854/855 [866/854] |
| fontsize, par | 1919/2159 [1928/2092] | 1917/2032 [1922/1924] | 1491/1600 [1533/1624] | 1245/1239 [1213/1223] |
| block, seq | 574/598 [593/603] | 568/585 [564/570] | 442/456 [442/448] | 462/452 [453/464] |
| block, par | 663/687 [690/695] | 639/684 [640/648] | 587/590 [590/583] | 410/403 [401/400] |

With #278 the reader's parallel sentence edit falls from about 476 to 334 us,
below the frontier under either compiler, and its parallel block and
font-size edits fall by 30 and 20 percent; the frontier, which has no such
offer, barely moves, and sequential cells are unchanged within their twins.
This supports the point-read offer as the cause of the reader's parallel
excess and #278 as its remedy, so the grain question needs no further
Whitefoot investigation for this reader. The sequential sentence edit stays
near the frontier, within or just above its spread. Acceptance is still
judged on the complete X5 matrix against main and cf12c609, which this pilot
did not run; it should run with a compiler containing #278 for every cohort,
as Snowghost adopts such a release. The suffix-traversal instance in
docs/todo.md was not re-measured.


### Retained lineless frontier: bounded contract and prior falsifiers

The owner selected option A of the root-font card for this task: process
retained lineless paragraphs first and use their actual post-break outputs
to decide whether general non-stationary restacking is needed. This extends
the stationary admission below; it does not implement general restacking.
The acceptance workflow now defaults every cohort and twin to
wf-b2209fd31035, containing Whitefoot #278. The old-compiler tables above
remain historical measurements; the optional compiler pilot names its old
compiler explicitly. The production pin and owner-motion writes stay as they
are.

**Bound.** The existing completed-input, stable-source and context admission
still applies. Each marked paragraph is prepared and broken, including an
empty or whitespace-only source. A retained lineless paragraph may publish
only when it remains lineless and has no Open mark: an Open can own an
empty-inline rectangle whose context placement/metrics need the topology
publisher. Node and Close marks alone create no empty-inline source. Stable
source identity ensures an old empty-inline source cannot lose its Open
without reconstruction invalidating the completed-input certificate.
Retained lined paragraphs keep the positive-height requirement. Both kinds
still require unchanged effective width/left and no float or atomic
placement dependence. A line-presence transition in either direction refuses
with bit 2048; a remaining lineless paragraph with an Open mark refuses with
bit 4096. These replace the blanket lineless exclusion, not the existing
source reconstruction or context-input guards. Historical reason bits 2 and
256 remain reserved for decoding earlier records.

After topology classification, unchanged height and last baseline remain
necessary. Changed height and baseline retain bits 512 and 1024 and may
co-occur. A stable lineless leaf contributes a live through transfer with
zero advance and no line baseline, rather than being dropped. Publication
still replaces its retained transfer and repairs ancestors, including
intrinsic contributions; preparation/breaking refresh paragraph-owned data.
It retains the unplaced geometry from the completed lineless output. Any
refusal keeps every mark and uses the existing full replay transaction.
The diagnostic must report actual refused leaf counts and reason bits; if
several reasons occur, their distribution must be captured before inferring
that a general restack is necessary.

**Dependencies and alternatives (R3).** For each paragraph, preparation
precedes its breaking, which precedes its output classification. Paragraphs
have no dependency on one another: both visitors retain disjoint slices,
shared immutable inputs and independent branch results. The existing
preparation call finishes before layout starts; publication requires the
all-leaf acceptance reduction because a refused transaction must keep all
marks. Ancestor reductions depend on their child outputs, and outer
settlement/mark retirement follow publication. Shared owner publication
remains serial under the existing stored-field proof gap; there is no new
algorithmic order between independent owner writes. Blanket refusal keeps
an unnecessary whole-flow stacking chain; general restacking adds placement
convergence machinery without current evidence that these 41 leaves need
it. This bounded extension keeps the shortest existing independent chain
and makes no shared cache or counter.

**Falsifiers recorded before code.** The hosted frontier fixture generator
will require whitespace-only retained paragraphs with empty prepared text to prepare,
break and publish without held context entries, with every edit equal to an
independent full layout. A whitespace-preservation toggle will exercise both
lined-to-lineless and lineless-to-lined transitions and require their exact
2048 refusal, rather than a coincidental full replay. A lineless inline Open
case will require the separate 4096 refusal and full-layout identity.
Independent constant cases will exercise both transition directions and the
Open-mark exclusion directly, including admitted empty/Node-only inputs. A
through-transfer publication case supplies independent intrinsic contributions
13 and 27 and requires its live entry, zero advance and absent line handles
to survive publication; a separate mutation skips only through publication.
Each new admission condition gets its own omission mutation against these
cases. Direct classification assertions are necessary for transitions:
changed height can otherwise mask the missing topology guard. Such a later
extent refusal is not mutation detection. Compilation failure, malformed
oracle output and unrelated refusal are invalid evidence. The established
boundary assertion mechanism checks these independent expected values;
normal/parallel fixtures additionally establish the production path. Existing
preparation/publication/retirement and source-domain mutations stay wired.

The final experiment is the complete ten-cohort X5 matrix, both pages and
all six kinds in sequential and four-worker parallel modes, with independent
twins and two reversed rounds on one hosted machine. Every candidate/main
cell must be at most 2x; every block/cf12 cell must be no worse. Literal
failures in either twin are reported without attributing differences inside
twin variation. No timing or correctness result is claimed by this contract.

### Retained lineless frontier: first hosted fixture evidence

At 3c3992e, [hosted check 37878177071](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37878177071)
and [layout-check 37878177082](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37878177082) pass.
The [focused falsifier run 37878177068](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37878177068) reaches compiled drivers, but its
unmutated fixture stage fails before mutation detection: deleting all text
from the node in the newly introduced `lineless-empty-source` case returns
`inc refused`. `patch_pieces` in `renderer/layout/update.wf` explicitly
refuses an empty replacement span because the box tree can change; full
reconstruction then removes that paragraph, leaving one marked leaf. It is
outside the retained-source contract and cannot test a two-leaf stationary
transaction. This new, never-passing deletion fixture is retired for that
technical reason, not counted as falsifier detection and not given a weaker
expected result. The required empty-or-whitespace boundary remains covered
by the whitespace source case (empty prepared text), plus independent
empty-paragraph admission and through-publication constants. No established
case or mutation is removed and no renderer source-transition rule changes.

The same unmutated hosted artifact reports four whitespace edits with exactly
two preparations and two breaks, zero held entries, fewer than 32 entries,
zero frontier refusals and full-layout identity. The whitespace-preservation
toggle reports two refused leaves with reason 2048 in both directions; the
empty-inline case reports two refused leaves with reason 4096 on all four
edits, each equal to full layout. These are fixture results, not yet evidence
for the 41 ECMA262 leaves or for the complete mutation/acceptance matrix.
The final run must repeat them in sequential and parallel modes.

The retained-lineless completion at 5b09e69 is recorded in
[Draft PR 55](https://github.com/Ming-Research/Snowghost-wf/pull/55), including
its 41-leaf distribution, correctness gates and historical ten-cohort run.
The root-font continuation below records its bisection, compiler gap and
repeated acceptance measurement; the PR carries current delivery and review
status. All evidence names its actual revision. Later investigation edits
change no renderer source, pin or submodule.


### HTML5 root-font parallel regression: bisection criterion before measurement

The continuation from 5b09e69 localizes the four-worker regression between
cf12c609 and 58b16da using only HTML5 root-font edits. Hosted run
[37892025668](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37892025668)
measured cf12c609 at 535511/535846 us sequential and 342864/345070 us
parallel, versus 58b16da at 564636/562091 and 604603/602147 us. All sources
used wf-b2209fd31035; the parallel jump is much larger than the sequential
change. This is the observed interval, not an attributed cause.

Bisect the branch's first-parent history, inspecting a merge's introduced
changes if it becomes the boundary. Each tested source has an independently
built twin with that same compiler, function fragments and LLVM 22. All
cohorts in a comparison execute the same HTML5 root-font script on one
GitHub-hosted machine with WF_WORKERS=4 in two reversed rounds, sequential
and parallel. Start with four edits, retaining the one-edit wall-time sample
and every raw edit; inspect edit, twin and round spread before enlarging.
The temporary dispatch inputs of `bisect-hosted.yml` select these cohorts
without changing the full acceptance default and are removed when this
bisection is complete. The existing timing parser rejects missing or
malformed records; a completed timing workflow is not acceptance success.

The discriminating observation is a persistent parallel increase beyond
both twins' and rounds' spread without a comparable sequential increase.
A midpoint separating from neither endpoint does not settle the interval;
repeat or enlarge that sample. Compare the before/after parallel ledgers at
the first source change and profile one four-worker edit only if needed.
The hypothesis of lost independent work is rejected if the relevant offers
and splits remain unchanged and the profile instead attributes the increase
to additional necessary work. True per-paragraph dependencies are preparation,
breaking, classification and dependent publication; independent paragraphs
must acquire no artificial order. Serial owner-motion writes remain unchanged
pending the existing stored-field proof gap. A naturally written independent
form refused by Whitefoot stops that repair, with a minimal example; it is
not replaced by an alternative spelling or proof-only storage.

The first four-edit pilot, [37899580622](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37899580622), places the jump after midpoint 03a3d3e: its
parallel upper medians and twin are 575707/586618 and 551766/564350 us,
versus 1012403/1038728 and 1024600/1020883 at 58b16da. Sequential medians
are 792701/801631 and 794158/803284, versus 846395/857006 and
846288/851224. The four-CPU EPYC 7763 pilot's one-edit wall samples are both
3.81 seconds. This large separation needs no larger sample for choosing the
next interval; it is not a final acceptance measurement. The next hosted
comparison includes the remaining midpoint 24f351e, its pre-frontier source
593b2db, the first syntax-corrected frontier d6383dd, and the bounded frontier
3393042 plus the established span patch, all with independent twins.

The 58b16da ledger permits both `frontier_prepare` recursive calls and emits
a runtime-derived recursion-budget family; child preparation and `break_all`
still split. A static permission-refusal account is therefore not supported.
Before attributing the loss, the temporary `rootfont-diagnose` workflow uses
unchanged pilot drivers for one root-font edit at four workers. Entry/return
uprobes delimit `layout.update` in CPU-clock samples, excluding initialization;
only instruction-pointer self attribution is attempted, not unreliable caller
stacks. Require one matched interval, samples inside it, zero recorded loss
and readable symbols before attribution. Capture native one/four-worker
samples and emitted preparation calls as separate evidence. A permitted and
emitted independent path with poor scheduling is a possible compiler/runtime
gap, not a reason to rewrite the source to suppress its offers. The workflow
is removed after the capture is recorded.

The second four-edit bisection, [37902138997](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37902138997), localizes the change to frontier introduction.
On one four-CPU EPYC 9V74, the pre-frontier source 593b2db has sequential
medians 864154/858288 us (twin 867614/865568) and parallel 580834/587982
(twin 572026/589441). The first syntax-corrected frontier d6383dd gives
1055912/1073714 sequential (twin 1056697/1058120) and 1251214/1251940
parallel (twin 1294570/1249397). The remaining midpoint 24f351e remains in
that slower class. The later 3393042 source with the established bounded-span
patch gives sequential 899252/902561 (twin 895686/896945), but parallel remains
1036509/1034254 (twin 1030264/1043152). Thus the bounded source still has the
parallel regression alongside a small sequential difference from the pre-frontier source. This comparison also
contains intervening frontier changes; it does not isolate the cost of
directory depth. These are same-host comparisons; their absolute values
are not compared with the first pilot's different processor.

The next diagnostic captures the adjacent pre-frontier, first frontier and
bounded-frontier drivers from that run. It also records compiler admission
of intervening b4ebd94 and a32573f with the same release, distinguishing the
introducing source change from the first buildable measured revision.

### Root-font source boundary and dependency audit

The introducing commit is [b4ebd94, retained effective inputs and stationary
frontiers](https://github.com/Ming-Research/Snowghost-wf/commit/b4ebd94d13e85e5db9a3d9d585752b7f3a3b2770).
Its immediate predecessor is 593b2dba6c10ed23babceea63e65029d7820ccc2.
The new multi-paragraph preparation call replaces the previously split
counted paragraph loop; the child-context loop and `break_all` map remain
split. The first buildable measured revision is
d6383ddf5be38fb2893a13a47536bea4baccf1c4, after two admission repairs.
Those intervening changes leave the recursive preparation pair unchanged;
they repair aliases, a borrowed publication value, a post-publication range
bound and oracle index types, and add oracle helpers.
Hosted [diagnostic 37904985865](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37904985865)
records exit 1 for b4ebd94 (first diagnostic: unresolved `Styles`) and
for a32573fd23d743f86ca279d574360b30ac7dc4dc (first diagnostic: a u32
counted-loop index where u64 is required; also a stationary-frontier range
proof refusal). No timing is claimed for either unbuildable source.

All pilot cells below are upper medians in microseconds, with the minimum
and maximum of the four edits in brackets. Stage 1 is run 37899580622 on
EPYC 7763; stage 2 is run 37902138997 on EPYC 9V74, each with four exposed
CPUs. Both use wf-b2209fd31035 and LLVM 22.1.8, the same generated HTML5
root-font script within the stage, independent builds for every twin, and
reversed cohort order in round 2. These hosted observations localize a large
regression; they are not precise cross-machine performance comparisons.

Stage 1 names: `good` = cf12c609, `mid` = 03a3d3e, `bad` = 58b16da.
Stage 2 names: `pre` = 593b2db, `first` = d6383dd, `mid2` = 24f351e,
`bounded` = 3393042 with the established `frontier-span.patch`.
Every `twin` repeats its named source independently. The artifacts retain
full source and pin-only child identities and patches.

| Stage | Build | Sequential round 1 | Sequential round 2 | Four workers round 1 | Four workers round 2 |
|---|---|---:|---:|---:|---:|
| 1 | good | 793935 [790472–807826] | 796397 [790503–800270] | 575520 [547635–578361] | 576964 [552322–627702] |
| 1 | goodtwin | 789943 [787264–798378] | 792898 [788025–810076] | 550411 [530302–577706] | 569578 [528855–637633] |
| 1 | mid | 792701 [784038–796393] | 801631 [791704–806520] | 575707 [561063–583861] | 586618 [574670–600488] |
| 1 | midtwin | 794158 [792668–801408] | 803284 [793887–804937] | 551766 [542620–579565] | 564350 [545072–599988] |
| 1 | bad | 846395 [836566–856159] | 857006 [833249–857147] | 1012403 [987205–1028534] | 1038728 [1004272–1095083] |
| 1 | badtwin | 846288 [837261–849048] | 851224 [834166–855300] | 1024600 [1013511–1056260] | 1020883 [1015246–1070982] |
| 2 | pre | 864154 [853470–866331] | 858288 [853326–875015] | 580834 [558730–628717] | 587982 [564829–595159] |
| 2 | pretwin | 867614 [855891–869971] | 865568 [858987–868111] | 572026 [564203–615726] | 589441 [567768–601554] |
| 2 | first | 1055912 [1044849–1067736] | 1073714 [1062189–1099446] | 1251214 [1189720–1330766] | 1251940 [1229188–1258117] |
| 2 | firsttwin | 1056697 [1053078–1098750] | 1058120 [1054229–1065660] | 1294570 [1206183–1325177] | 1249397 [1201017–1356081] |
| 2 | mid2 | 1087258 [1067280–1100480] | 1059602 [1056164–1062150] | 1245124 [1201020–1302573] | 1266235 [1228941–1308408] |
| 2 | mid2twin | 1066413 [1060255–1093067] | 1056779 [1047448–1088425] | 1231976 [1213169–1313877] | 1275540 [1227014–1311927] |
| 2 | bounded | 899252 [887617–904949] | 902561 [881819–919747] | 1036509 [1007010–1052743] | 1034254 [1005715–1041447] |
| 2 | boundedtwin | 895686 [884713–905109] | 896945 [887784–901156] | 1030264 [995670–1040171] | 1043152 [1016030–1072263] |

The first frontier raises sequential time as well as parallel time. In the
later bounded-frontier source, sequential is only about 3–5% above `pre`,
while four-worker medians remain about 76–80% higher, beyond
both twins' entire edit ranges. The first-to-bounded interval also changes
frontier admission and stationary processing, so this comparison does not
isolate how much sequential cost comes from directory depth. The lost
recursive offer is established separately by emission and profile evidence.
No midpoint result is compared numerically across hosts. Every stage-2 cohort and twin prepares 60867–60868 paragraphs,
breaks 60868, visits 13903 contexts and reports 105927 held entries and
105989 total entries. These counters rule out a larger paragraph set as the
explanation; they do not claim identical instruction counts.

R3 dependency audit: a fork must read its immutable directory node and
compute its half interval before either child starts. Each child reads only
shared document/style/font data and its own directory subtree, and writes
only its disjoint paragraph slice. A paragraph must retain its previous
text/shaping before reset and preparation; the parent must wait for both
Boolean completion results before `band`. Neither child needs the other's
result, storage or execution order. There is no shared accumulator or list
in this pair. Releasing a box owned by one paragraph cannot release an
adjacent paragraph or the immutable directory. The new source adds sparse
tree navigation, but no true sibling dependency. The existing serial
owner-motion publication is a separate stored-field proof gap and is
unchanged.

### Root-font profile and emitted preparation

Diagnostic 37904985865 reuses the stage-2 `pre`, `first` and `bounded`
drivers on one four-CPU EPYC 7763. One root-font edit has exactly one matched
`layout.update` entry/return interval in each capture. Fixed 2 ms user
CPU-clock instruction-pointer samples exclude initialization; every capture
has zero recorded lost events. The native parallel-driver one/four-worker
samples are respectively 765685/559579, 983807/1183397 and 813973/969448 us.
These single edits and instrumented captures are diagnosis, not acceptance.
The driver's edit time includes delta marking and font picks; the uprobe
window covers only `layout.update`, so its duration is not the whole edit.

| Driver | Update-window samples | Scheduler worker-loop self samples | Unknown-symbol samples |
|---|---:|---:|---:|
| pre | 843 | 121 | 77 |
| first | 1813 | 997 | 102 |
| bounded | 1779 | 1028 | 66 |

Preparation work spreads across worker threads before the frontier change;
after it, the main thread performs text preparation while most early worker
samples are in `wf__par_worker_main`. Later line-breaking work still reaches
workers. These are instruction-pointer self samples, not call-stack or
exact phase percentages; unknown symbols are retained rather than assigned.
Disassembly supplies the stronger mechanism evidence: the budget-carrying
`frontier_prepare` body directly calls the left child and continues into
the right, with no lane acquisition or publication in the recursive pair.

The ledger reports the pair **permitted, eligible**, and a runtime-derived
recursion-budget family. It does not report a refusal for that pair. Its
first neighboring condition-1 denial is between `let middle` and the first
call, because argument formation reads `middle`; the following denial is
between the second call and the result join, which reads `right_ok`. Those
are true dependencies and do not explain serial siblings. The old paragraph
loop's `split under band` disappears; child-context preparation and
`break_all` remain split. A budget-family ledger line alone is therefore
not evidence that sibling offers survived emission.

### Owning-range actualization gap and repair disposition

Hosted [emission probe 37907165434](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37907165434)
at a29e85d36a51355242e41eca7f0d098b1d4caaf0 compiles the following complete
library source with wf-b2209fd31035 using
`whitefootc --par --par-ledger --emit-llvm -o owning-pair.ll owning-pair.wf`.
The artifact contains the source, ledger, unoptimized LLVM and compiler hash.
The ordinary emission path reproduces the loss before LLVM optimization,
so function fragments, caching and runtime grain are not needed to trigger it.

```whitefoot
enum Frontier {
  doc "A sparse directory over stable element slots.";
  Vacant();
  Mark();
  Fork(left: Box<Frontier>, right: Box<Frontier>);
}

fn visit(frontier: &Frontier, values: &[Box<u64>], span: u64) -> ok: Bool reads(frontier), writes(values) {
  doc "Visits independent leaves and joins only their completion results.";
  let count = values^.len;
  match frontier^ {
    Vacant() => {
      return True();
    }
    Mark() => {
      if 0_u64 < count {
        let fresh = box_new::<u64>(value: 1_u64);
        set values^[0_u64] = move fresh;
        return True();
      }
      return False();
    }
    Fork(left: left_tree, right: right_tree) => {
      let half = span / 2_u64;
      let middle = imin(half, count);
      let left_ok = visit(frontier: &left_tree^.inner, values: &values^[0_u64..middle], span: half);
      let right_ok = visit(frontier: &right_tree^.inner, values: &values^[middle..count], span: half);
      let both_ok = band(left_ok, right_ok);
      return both_ok;
    }
  }
}
```

The ledger permits `pair(visit, visit)` at line 26 and records its two-member
chain. The emitted `wf_visit` instead calls itself twice in sequence and
contains no lane acquisition or publication. The first subsequent recursive
status is `excluded: visit has no sequential clone`; this is a consequence
of the lost offer, not a reported lifetime-conflict reason. The paired
control changes only the element to u64 and the leaf to a scalar increment;
it keeps the same directory and recursive slice pair, and emits a 48-byte
lane acquisition, publication, inline sibling and join. This is an emission
comparison, not a proposed renderer spelling or a throughput measurement.
The full renderer's unoptimized `frontier_prepare` also has no recursive
offer; its remaining descendant offers account for its sequential clone and
budget-family status even though the sibling pair disappeared.

Compiler source identifies the narrowing: [`CallStorageEffects::conflicts`](https://github.com/Ming-Research/Whitefoot/blob/b2209fd31035/compiler/src/semantic/permission.rs#L326)
compares released places with borrowed places using `UnprovedSeparations`.
Its [`ranges_disjoint` method always returns false](https://github.com/Ming-Research/Whitefoot/blob/b2209fd31035/compiler/src/semantic/places.rs#L1149),
so it cannot preserve the checker's proof that these two intervals are
disjoint. Written reference parameters whose elements can release owned
storage contribute released places. [`IrBuilder::overlaps`](https://github.com/Ming-Research/Whitefoot/blob/b2209fd31035/compiler/src/lowering/builder.rs#L1022)
then ends the group at that conflict. This narrowing supplies no ledger
line naming the conflict. It is a compiler proof-transport/diagnostic gap,
not a source dependency, a run-time alias uncertainty, or evidence that the
recursion budget refused real offers. The lifetime boundary exists for real
release/borrow hazards and must not simply be removed.

Repair disposition: **blocked on Whitefoot**. No renderer rewrite, proof-only
data, alias check, compiler-policy override or alternative spelling is
adopted. The serial owner-motion writes, production compiler pin and both
submodules remain unchanged. No new renderer design choice was made, so
this continuation adds no Decision or approval log. The diagnostic workflow
and bisection-only dispatch inputs are removed after their captures; the
existing full acceptance workflow is restored exactly. Its historical
commits and run artifacts retain how the observations were made.

**Decision pending: take the owning-range gap into Whitefoot?**

- **Background.** The permitted recursive slices above execute serially
  because actualization no longer has their proved separation. The same
  loss appears on the HTML5 preparation path and exceeds the acceptance
  bound. Restoring a counted loop would hide the naturally expressed gap.
- **A — Repair Whitefoot's proof transport and refusal reporting (recommended).**
  Preserve valid range-separation evidence at the lifetime boundary while
  keeping genuine release/borrow conflicts ordered, then qualify the same
  source against a released compiler and rerun the full comparison. Cost:
  a separate compiler change and its safety/code-generation review. Risk:
  an over-broad lifetime relaxation would be incorrect; the compiler task
  must retain the existing negative witnesses. Its architecture is not
  selected by this Snowghost investigation.
- **B — Defer the compiler repair and keep this PR blocked.** No new
  implementation cost or safety change; the HTML5 acceptance failure and
  adoption delay remain. This preserves the gap but does not meet the
  performance goal, so it is not recommended.
- **Confidence 5/5 on the gap, 4/5 on this next step.** The scalar/owning
  emission contrast, compiler source and unchanged-driver profile agree.
  A compiler repair has not been implemented or measured, so recovery of
  the complete acceptance matrix remains unverified.


### Root-font continuation ten-cohort result

[Hosted run 37906888534](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37906888534)
completed all ten builds and the full measurement. Its
[raw evidence](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37906888534/artifacts/11610267444)
contains 480 timing files and 19,200 numbered edits: 20 per ECMA262 file,
60 per HTML5 file. Every recomputed upper median agrees with its CI summary;
all 480 summaries occur in the intended forward/reversed order in the job
log. No timing edit is refused or rebuilt. Workflow success means the
measurement completed, not that acceptance passed.

The measurement host is a GitHub-hosted AMD EPYC 9V45 96-Core Processor
exposing four CPUs, Ubuntu 24.04.5, Linux 6.17.0-1022-azure. All ten builds
use wf-b2209fd31035, function fragments and Ubuntu Clang/LLVM 22.1.8
(++20260714014902+ca7933e47d3a-1~exp1~20260714135019.80). Sequential and
parallel drivers use WF_WORKERS=4; the separately recorded style time is
excluded. Both one-edit HTML5 root-font wall samples took 2.12 seconds before
the full batch. Native timing precedes the workflow's separate supplemental
reader profile. All cohorts share pages, fonts, styles and scripts; all 16
generated scripts match baseline 37892025668 byte for byte. Absolute times
from different hosted instances are not a before/after attribution.

| Cohort and independent twin | Source |
|---|---|
| Main | 8fbc1601785cee70265da1eac4d99589fc6fb67c |
| cf12 | cf12c609e1c00f86bb431fab4e92f5dca2bf94f2 |
| Pre-range | 58b16dae2770a774189370d4d2e5b74abc1a2fd0 |
| Frontier | 3393042d79efe1ada22129b950a610ffae4508aa with `.github/timing/frontier-span.patch` |
| Head | af2438c9337384a2640f0293b31d3523f9550cf7 |

Each cohort and twin is built independently, with its source and temporary
pin-only child recorded in the artifact. The measured head's renderer tree
is identical to 5b09e69 and to the continuation after diagnostic cleanup;
there is no renderer fix or compiler adoption in this measurement. Round 1
orders Main, Main twin, cf12, cf12 twin, Pre-range, Pre-range twin, Frontier,
Frontier twin, Head, Head twin; round 2 reverses it. Cells below are
unprofiled upper-median edit microseconds, round 1 / round 2.

| Page | Kind | Mode | Main | Main twin | cf12 | cf12 twin | Pre-range | Pre-range twin | Frontier | Frontier twin | Head | Head twin |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ecma262 | word | seq | 58/54 | 62/59 | 66/61 | 66/66 | 73/63 | 61/65 | 74/65 | 66/62 | 73/64 | 61/64 |
| ecma262 | word | par | 81/81 | 84/86 | 87/82 | 98/89 | 103/89 | 85/102 | 101/89 | 88/83 | 89/89 | 88/85 |
| ecma262 | sentence | seq | 163/135 | 164/124 | 473/464 | 446/527 | 87/88 | 82/87 | 99/99 | 98/92 | 84/86 | 84/83 |
| ecma262 | sentence | par | 224/209 | 223/226 | 417/375 | 418/486 | 131/131 | 120/128 | 145/156 | 139/142 | 121/124 | 118/125 |
| ecma262 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| ecma262 | fontsize | seq | 1480/932 | 1774/1780 | 9102/9192 | 9300/9403 | 419/409 | 384/392 | 426/382 | 387/439 | 380/374 | 462/371 |
| ecma262 | fontsize | par | 1664/1495 | 1745/1907 | 8496/8510 | 9051/9519 | 545/649 | 505/558 | 577/662 | 659/559 | 567/525 | 610/584 |
| ecma262 | rootfont | seq | 27370/23741 | 26636/27991 | 102895/99435 | 102627/104146 | 110285/108754 | 108694/107586 | 106567/102622 | 105206/102161 | 197/212 | 222/204 |
| ecma262 | rootfont | par | 49343/45285 | 48114/49279 | 118167/115232 | 118741/121722 | 128161/127110 | 128377/125518 | 125457/124954 | 123000/120596 | 280/303 | 285/300 |
| ecma262 | block | seq | 464323/447837 | 450182/432852 | 86/83 | 84/91 | 88/86 | 89/88 | 91/89 | 90/86 | 86/83 | 83/83 |
| ecma262 | block | par | 426141/415913 | 417140/426182 | 114/109 | 115/116 | 114/111 | 116/110 | 119/128 | 119/137 | 111/108 | 109/109 |
| html5 | word | seq | 42/43 | 42/41 | 52/47 | 46/48 | 50/51 | 49/48 | 52/45 | 47/47 | 52/48 | 49/50 |
| html5 | word | par | 69/63 | 63/62 | 68/70 | 66/65 | 73/87 | 71/67 | 67/69 | 67/69 | 69/68 | 68/65 |
| html5 | sentence | seq | 125/119 | 122/120 | 202/193 | 190/192 | 373/371 | 373/371 | 199/192 | 218/190 | 213/206 | 216/208 |
| html5 | sentence | par | 176/160 | 168/160 | 187/186 | 189/195 | 266/272 | 298/273 | 188/215 | 183/178 | 177/184 | 180/167 |
| html5 | colour | seq | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | colour | par | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| html5 | fontsize | seq | 513/393 | 394/480 | 1495/1416 | 1675/1889 | 864/843 | 846/880 | 918/898 | 894/906 | 568/561 | 609/665 |
| html5 | fontsize | par | 547/401 | 464/407 | 1379/1328 | 1702/1891 | 1060/1067 | 1128/1132 | 1134/1083 | 1194/1138 | 664/693 | 689/726 |
| html5 | rootfont | seq | 456305/444242 | 453698/446253 | 588136/579091 | 585211/579437 | 608328/619040 | 615551/620191 | 618997/604629 | 613477/603496 | 624984/605040 | 620651/615946 |
| html5 | rootfont | par | 270353/264201 | 270148/256831 | 381203/383936 | 396866/374302 | 662728/675158 | 673793/665521 | 662229/675223 | 666938/657692 | 661084/657582 | 668969/659094 |
| html5 | block | seq | 629684/578051 | 609471/573344 | 360/376 | 377/355 | 450/439 | 452/445 | 362/379 | 349/362 | 281/262 | 272/268 |
| html5 | block | par | 559404/520280 | 533354/509476 | 384/377 | 402/396 | 344/338 | 360/356 | 382/462 | 392/379 | 234/236 | 237/237 |

Acceptance compares each head build with its corresponding main build at
most twice main, and each block cell with its corresponding cf12 build at
most cf12. Of 112 comparisons (96 against main, including block, and 16
additional block comparisons), exactly four fail:

| Page / kind / mode | Candidate | Round | Candidate us | Main control us | Allowed maximum us | Ratio |
|---|---|---:|---:|---:|---:|---:|
| HTML5 rootfont par | Head | 1 | 661084 | 270353 | 540706 | 2.445x |
| HTML5 rootfont par | Head | 2 | 657582 | 264201 | 528402 | 2.489x |
| HTML5 rootfont par | Head twin | 1 | 668969 | 270148 | 540296 | 2.476x |
| HTML5 rootfont par | Head twin | 2 | 659094 | 256831 | 513662 | 2.566x |

Every other main comparison and all 16 block comparisons pass in this run.
The historical one-microsecond ECMA262 block miss is not reproduced; no
source change or isolated measurement establishes a block speedup. HTML5
root-font remains systematically over the limit in both builds and rounds,
consistent with the independently established missing preparation offers.
The compiler repair and its effect on acceptance remain unmeasured.

All 160 head/twin ECMA262 root-font timing edits prepare and break 41
paragraphs, visit six entries, hold zero entries and have zero frontier
refusals; the two existing context boundary fallbacks with reason 7 remain.
Head sequential medians are 197/212 us (twin 222/204), and parallel 280/303
(twin 285/300). All 480 corresponding HTML5 edits prepare 60867–60868
paragraphs, break 60868, visit 105989 entries and hold 105927, with zero
frontier refusals and 1979 context boundary fallbacks with reason 7.
The ECMA262 retained-lineless improvement remains present; it does not remove
HTML5's separate preparation cost.


### Released inverse proof and recursive order storage

The continuation starts at 50b40ca and merges layout base a1ed31e in 16fc1e3.
The incoming work is percentage-height provenance from merged PR 53; grid
splice PR 54 is still open at integration. Conflict resolution retains both
height inventories and fragment/range storage, combines initialization and
private relocation, and refreshes height provenance after settling the
fragment frontier's retained semantics. Both mutation families remain wired.
The merged height inventory replaces the old flow-definiteness bit's
consumers, so the unused bit is removed rather than left stale.

The pin moves from wf-f949e676acfa (specification v0.92) to
wf-01697d2de8a1 (v0.112); neither submodule moves. The initial source adaptation
carries the deletion-only FN-1 change from 3c7a80d: statements after ordinary
loops without a break edge are unreachable. Reachable returns, bodies,
contracts and checks are retained. The first hosted check ([37994844784](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37994844784))
refused the merged Open path: its new height-basis read followed
`set_natural`, whose broad `writes(context)` row discarded the preceding
block bound. The helper only updates existing scalar fields, so its contract
now states that the block count is unchanged. This is a checked function
boundary guarantee, with no extra guard, reordered read or runtime work.
Hosted layout-check 37996059947 accepts layout at 736c71d; the complete gate
is still pending.

The proposed proof owner is the Context that owns both the order stores and
the block, paragraph and child pools. A type invariant makes construction and
writers establish the inverse and gives it directly to readers; a writer fact
alone would have to be carried through every intermediate caller. For one
owner, the needed relation is the original `natural.wf` relation. Across
owners it also includes the target's owner, and Child, Float and Out share
one child store, so their facts must jointly exclude collisions.

The [focused probes](inverse-proof/README.md) ask separately whether the
released checker admits the unchanged original callee, the implicit caller
through a type invariant, and a fact over recursive SlotPages. The released
compiler's nested-owner test uses `Slots<Order>` whose payloads are another
Slots, while this branch's EntrySequence owns recursively boxed pages. The
finite range projection grammar does not name arbitrary directory paths;
RANGE-1 also excludes a logical accessor call. The proposed getter fact in
`recursive-fact.wf` makes this remaining expressibility question concrete,
without changing renderer storage or using runtime proof checks. Hosted probe 37996060054 rejects it with RANGE-1 InvalidRangeClause:
`a range term calls a function`. This is a remaining representation/proof
dependency, not a claim that v0.112 promises recursive predicates.

No renderer parallelization, invariant-maintenance falsifier or acceptance
recovery is claimed. Final-head correctness results and remaining gate
failures are recorded in Draft PR 55; the complete gates remain required. Four-worker acceptance timing waits for
the separately owned paged-overlap-regression repair; this continuation runs
only on GitHub-hosted CI and runs no acceptance timing.


The integration review found the range counterpart of a changed height rule:
`publish_reference_ranges` still replaced every retained Open's basis with
the context height, although the incoming `translated_reference_output`
correctly stopped doing that. Publication now keeps each Open's immediate
containing-block basis. The existing nested zero-rebase boundary case gives
its retained Open basis 40 while the context basis is unknown, and requires
40 after publication. The new `range-context-basis` mutation restores the
obsolete unknown-basis assignment and must trip this runtime assertion after
successful compilation; its result is pending. Range basis channels remain
covered by their existing explicit-action test, but reference suffix
translation no longer produces a basis assignment.


Hosted check [37995496943](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37995496943)
accepted layout after the count postcondition, then refused the host I/O
calls: v0.110 added the required cancellation-watch argument. Existing
command-line generators and oracle writers keep their no-cancellation
behavior by creating a never-firing watch for each read/write and closing it
immediately after the host call, before matching its result. No stream
operation, error case or check is removed. The font-face oracle's exhaustive
file-size classifier also treats Cancelled as an ordinary non-size error.

The same hosted probe permits the unchanged natural loop and emits a split
function with a 96-byte lane acquisition, task publication and join; the
serial control is denied condition 2 and emits no offer. This proves the
original callee's independence, not renderer integration. The reachable
natural caller fails RANGE-3 and the Context constructor fails TYPE-11.
A one-cell aggregate-fill reduction fails RANGE-3 for
`targets^[k].entry_slot == 0_u32`, despite filling Block(entry_slot: 0).
The specified generic fill postcondition is inactive for noninteger element
types (PRE-1 and RANGE-1), so its field value is unavailable to this proof.
No redundant explicit store is added. Its necessity for the renderer's
actual empty-Slots/append construction is unverified; the recursive relation
is the established renderer blocker. Both minimal gaps and their exact
diagnostics are recorded in [the probe record](inverse-proof/README.md).

The complete check at 736c71d additionally exposed the new IoError::Cancelled
variant. The exhaustive error-code reader returns zero for this fieldless
variant, as it already does for DeadlinePassed. This completes the cancellation API
adaptation without dropping any previous error handling.

The historical oracle worktrees need the same source-language adaptation
when built by the adopted compiler. The workflow applies only the immutable
FN-1 deletion and uncancelled I/O API diffs before compiling them, records
the original revisions and complete resulting diffs, and retains their old
behavior. In particular, 8e69668 still lacks the of-clause reach fix and must
fail the reach observation after compiling. The full-build base is still the
original structure-edits merge base. Compilation refusal is not detection.

Q139 intentionally corrected the context-wide height basis that produced
200/360/360 instead of Chromium's 200/100/50, as the imported
[independent full-layout probe](../structure-edits/layout-design.md#q139-implementation-independent-full-layout-probe)
records. The newly imported percentage-height fixture therefore cannot use
the pre-Q139 renderer's dump as its expected result. The historical oracle
step still compiles and runs that control, requires the established Chromium
comparison to reject its geometry with status 1, and requires the current
output to meet the same independent expectation. It keeps exact seq/par
comparison and every other historical fixture/page comparison. Both dumps
are retained; the permanent Q139 gate still checks that fresh Chromium agrees
with the committed reference. This is the approved behavior correction's
oracle adaptation, not a new renderer choice or a suppressed failed check.
