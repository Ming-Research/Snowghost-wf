# Apollo 11 structural-path diagnosis

## Question and rejection criterion

On the unchanged renderer at `cf12c609`, do Apollo 11's X5 block edits take
local splices, or do explicit refusals rebuild a large context? Inspect every
edit's structural path and boundary counters, sequentially and in parallel,
and compare every retained result with a full rebuild. Local paths throughout
would reject fallback as the explanation. Inventory each edited parent and
its containing owners against the splice contract before attributing a
reason code to a particular CSS dependency. Also inspect the other five X5
kinds to distinguish font-size propagation from structural reconstruction.

The temporary `apollo11-diag` hosted workflow uses the branch's pinned
compiler and ordinary X5 generator. It preserves and hashes the live HTML
and both external stylesheets: Apollo's oldid does not stabilize rendered
bytes. These bytes need not match the 14900K capture used by E2 run
[37674972449](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37674972449).
Hosted timing fields are incidental diagnostics, not a performance comparison
with that machine. E2's retained raw timing artifacts are the source for any
14900K time decomposition. No renderer behavior is changed by this diagnosis.

## Hosted capture, identity and edit sites

Hosted run [37727037303](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37727037303)
at `d180d718a0e20b4db7c0cf99e4a3b8a66631e94e` built the pinned sequential and
parallel drivers, prepared the ordinary X5 scripts, and checked all 60 edits
of each kind in each build. The first two-edit block sample passed before
the batch. The live input SHA-256 values are:

| Input | SHA-256 |
| --- | --- |
| apollo11.html | `1405f09a8888e2854ba8785a4da6b50dbd3951fb56ec9eca7f2e20aa3fe78dc4` |
| apollo11-modules.css | `cc2e64f8f1706af7f505ec69b6c9807cb05a743f7887ccbf8c7e104e1f41a9f8` |
| apollo11-site.css | `a292ccfd0f47accce300fd2febc776a88c2cd18b82f3f4cc8fad01fbdb9ca1d8` |

All block, word, colour, fontsize and rootfont edits report `inc same`,
sequentially and in parallel, and their seq/par comparable output agrees.
Sentence edits **31–32 report `inc DIFF` in both builds**; the other 58 match.
There are no `inc refused` edits. The workflow correctly fails rather than
weakening the expectation, and continues through the remaining kinds.
Thus this is a completed diagnosis with a discovered correctness defect,
**not a green all-kind identity result**. The original script inserts 85
bytes at byte offset 137 of Text NodeId 3126, then deletes them; its parent
is paragraph 3090 in the lead section 2154. The text describes Armstrong
walking on the Moon and Aldrin following nineteen minutes later.
The existing TODO's earlier sentence31–32 *performance* observation does not
establish the cause of this newly recorded identity failure.
A subsequent hosted dump capture in run
[37729474890](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37729474890)
shows 380 differing element/text rows for each edit. The first is element
index 1653, a following paragraph: full y=3097.84375, incremental y=3123.84375
for edit 31 and y=3071.84375 for edit 32 (±26 px). Both final heights remain
54677 px, so a height-only comparison would miss the defect. The dumps locate
the affected geometry; they do not establish the faulty dependency.


Both builds' block paths are exactly 54 `splice 0 reason 7` and six
`splice 0 reason 6`, with no other reasons and no local splice. The path
IDs and all six kinds' boundary-reason/fallback distributions agree with
E2's tables below despite the changed HTML and site CSS. Each block pair
inserts a fresh plain HTML `p` with one Text node before the listed old `p`,
then removes that newly created `p` (never the old sibling). These NodeIds
belong to this hosted capture, not to E2's distinct HTML. The three
blockquote pairs have reason 6; all remaining pairs have reason 7.

| Edits B–X | Parent NodeId and element | Before old p | Created/removed p | Splice / reason, both edits |
| --- | --- | ---: | ---: | --- |
| 1–2 | 4719 `section#mwAqk` | 4736 | 23219 | 0 / 7 |
| 3–4 | 3891 `section#mwAXM` | 3988 | 23221 | 0 / 7 |
| 5–6 | 6357 `section#mwBS0` | 7073 | 23223 | 0 / 7 |
| 7–8 | 3347 `blockquote.templatequote` | 3348 | 23225 | 0 / 6 |
| 9–10 | 6357 `section#mwBS0` | 6976 | 23227 | 0 / 7 |
| 11–12 | 7411 `section#mwBsE` | 7418 | 23229 | 0 / 7 |
| 13–14 | 5150 `section#mwA0A` | 5235 | 23231 | 0 / 7 |
| 15–16 | 7411 `section#mwBsE` | 7488 | 23233 | 0 / 7 |
| 17–18 | 3210 `section#mwnw` | 3429 | 23235 | 0 / 7 |
| 19–20 | 6357 `section#mwBS0` | 6639 | 23237 | 0 / 7 |
| 21–22 | 8799 `section#mwCKU` | 8985 | 23239 | 0 / 7 |
| 23–24 | 4603 `section#mwAng` | 4637 | 23241 | 0 / 7 |
| 25–26 | 3210 `section#mwnw` | 3566 | 23243 | 0 / 7 |
| 27–28 | 9762 `section#mwCig` | 9805 | 23245 | 0 / 7 |
| 29–30 | 6307 `blockquote#mwBRk.templatequote` | 6308 | 23247 | 0 / 6 |
| 31–32 | 9762 `section#mwCig` | 9774 | 23249 | 0 / 7 |
| 33–34 | 5472 `section#mwA8Y` | 5695 | 23251 | 0 / 7 |
| 35–36 | 3350 `div#mw1g.templatequotecite` | 3351 | 23253 | 0 / 7 |
| 37–38 | 6013 `section#mwBJ4` | 6114 | 23255 | 0 / 7 |
| 39–40 | 5771 `section#mwBDc` | 5788 | 23257 | 0 / 7 |
| 41–42 | 4301 `section#mwAfU` | 4306 | 23259 | 0 / 7 |
| 43–44 | 7618 `blockquote#mwBxU.templatequote` | 7619 | 23261 | 0 / 6 |
| 45–46 | 3210 `section#mwnw` | 3366 | 23263 | 0 / 7 |
| 47–48 | 5771 `section#mwBDc` | 5853 | 23265 | 0 / 7 |
| 49–50 | 7645 `section#mwBx8` | 8243 | 23267 | 0 / 7 |
| 51–52 | 6357 `section#mwBS0` | 7037 | 23269 | 0 / 7 |
| 53–54 | 5472 `section#mwA8Y` | 5632 | 23271 | 0 / 7 |
| 55–56 | 6357 `section#mwBS0` | 6718 | 23273 | 0 / 7 |
| 57–58 | 7093 `section#mwBkI` | 7256 | 23275 | 0 / 7 |
| 59–60 | 7645 `section#mwBx8` | 8147 | 23277 | 0 / 7 |

The parents are 26 sections, three `blockquote.templatequote` elements and
one `div.templatequotecite`. No block insertion or removal is owned directly
by a table, infobox float, flex/grid container, positioned element, list item
or counter setter. The blockquotes establish their own flow contexts through
`overflow:hidden`, explaining their small Q86 reconstruction scope. The
citation's old paragraph 3351 has `display:inline`; the edited owner is
therefore a potential mixed-inline seam beyond the first complete-block
certificate, masked by the earlier reason-7 guard in this run.

All these owners lie under `div.mw-parser-output` 2153, `#mw-content-text`
2152, relative-positioned `#bodyContent` 2046, grid `main#content` 1288,
`.mw-content-container` 1286, grid `.mw-page-container-inner` 374,
relative-positioned `.mw-page-container` 372, body 69, and html 2.
Some section and blockquote ancestors intervene below `.mw-parser-output`;
the complete chains are in the artifact's `apollo11-owners.txt`. A full
html5lib/Snowghost tag-preorder agreement validated the attribute-label
mapping, and the style dump uses Snowghost's computed styles at the same
indices. The parser-output counter reset stays outside every inserted or
removed subtree; no reported structure reason 5 implicates counter state.

Font-size sites are a different sample: ten `li`, five `span`, three each
of `ul`, `td` and `tr`, and one each of `cite`, `audio`, `header`, `blockquote`,
`div` and `tbody`. They do reach list/table and other formatting paths; the
boundary maximum alone cannot identify an individual owner as their cause.

## E2 evidence already retained

The E2 artifact `time-14900k-37674972449` contains structural-path records,
although E2 ran `edittime`, not the full-rebuild identity check. Both builds
report **60 fallbacks: 54 reason 7 and six reason 6**, no successful splice.
Reason 6 is edits **7–8, 29–30 and 43–44**; all other block edits report
reason 7. There are no `structure fallback` rows: that separate diagnostic
means a full *style* reconstruction, not refusal of the layout splice.

E2 used HTML SHA-256
`1c9d300c68a3bc082139d8c49b85f3fba5fc1fd85a5d772082780cc2da41de2b`,
modules CSS `cc2e64f8f1706af7f505ec69b6c9807cb05a743f7887ccbf8c7e104e1f41a9f8`,
and site CSS `3f439934c51c220c4b92072d4dec2219920cef1bbafb58eda32a7161df7b9d0c`.
Its M2 build is `54e4aab295013819254fe071faff4fb2f56af534`, whose renderer
source is identical to this task's `cf12c609e1c00f86bb431fab4e92f5dca2bf94f2`.
E2 uses compiler `wf-0b7f5c5b9854` and Ubuntu clang 22.1.8; this diagnostic
branch retains `wf-f949e676acfa`. E2's overall run failed in its Chromium
step after all Snowghost timings completed; the 340 us Chromium number is
not a new measurement from that failed step.

### Where the block time goes

The three E2 sequential round summaries report median style+layout costs
18,367, **18,846**, and 19,241 us. The quoted 18,846 us is the median round's
median, not an individual edit's time. That round separately reports
`delta_us` median 6,934, `style_us` median 134 and `picks_us` median 0;
medians of components need not add to the median total.

The workflow overwrites `results/raw/BUILD-MODE/*r1.txt` each round. Thus only
the third round's per-edit rows survive, despite all three summary files
surviving. The table below decomposes that retained round, **not** the
18,846 us round. This evidence-preservation limitation prevents an exact
per-edit decomposition of round 2 without a new timing run.

In [apply_structure_edit](../../../renderer/oracle/layout/edit.wf), `delta_us`
includes font-pick extension, the splice attempt, dense fallback flags and
`structure_changed` context reconstruction. The subsequent interval contains
font picks and `update`; `style_us` is outside `edit us`. Thus
`update remainder = edit us - delta_us - picks_us`; integer-microsecond
rounding can affect it by about a microsecond. `full_us` is zero in E2
because `edittime` runs no full comparator between edits.

For the retained third round, medians are 7,048 us delta, 12,009 us update
remainder and 127 us style; the median paired total is 19,241 us. Main's
retained third round has medians 3,265 / 11,008 / 135 us respectively and
14,435 us total. This locates most of the extra cost in structural delta /
reconstruction, with additional update work. It does not isolate the cost of
individual M2 data structures or certificate predicates; that would need
separate profiling or an interleaved controlled experiment.

All 54 reason-7 edits reconstruct **740 contexts**, **1,896 paragraphs for
insertion / 1,895 for removal**, reusing **1,762** paragraph preparations.
They then report 134 / 133 prepared paragraphs, 755 updated contexts,
1,907 / 1,906 updated paragraphs, and **133 boundary fallbacks** with maximum
`boundary_reason 9`. Each reports boundary entries / blocks / index visits
27 / 31 / 156. These boundary counters exclude much reference replay and
construction work; their small values do not certify small total work.

The six reason-6 edits rebuild only one context and two / one paragraphs,
with no reused preparations; their boundary fallback counts are four for
7–8 and 43–44, six for 29–30, maximum reason 9 throughout. Those are the
roughly 2 ms edits, not the 18–22 ms majority.

### Every retained E2 sequential block edit, microseconds

| Edit | Style | Delta / reconstruction | Picks | Update remainder | Style + layout |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 123 | 8645 | 0 | 12667 | 21435 |
| 2 | 110 | 7505 | 0 | 12434 | 20049 |
| 3 | 136 | 6948 | 0 | 12226 | 19310 |
| 4 | 143 | 6902 | 0 | 12193 | 19238 |
| 5 | 205 | 7647 | 0 | 12534 | 20386 |
| 6 | 183 | 6787 | 0 | 12271 | 19241 |
| 7 | 74 | 1745 | 0 | 236 | 2055 |
| 8 | 50 | 1743 | 0 | 188 | 1981 |
| 9 | 190 | 7717 | 0 | 12439 | 20346 |
| 10 | 233 | 7329 | 0 | 12980 | 20542 |
| 11 | 103 | 7991 | 0 | 12955 | 21049 |
| 12 | 92 | 7734 | 0 | 13175 | 21001 |
| 13 | 99 | 8011 | 0 | 13179 | 21289 |
| 14 | 88 | 8036 | 0 | 13116 | 21240 |
| 15 | 95 | 8826 | 0 | 12515 | 21436 |
| 16 | 89 | 6739 | 0 | 12561 | 19389 |
| 17 | 172 | 7660 | 0 | 13417 | 21249 |
| 18 | 196 | 8633 | 0 | 13067 | 21896 |
| 19 | 275 | 8478 | 0 | 12317 | 21070 |
| 20 | 218 | 6640 | 0 | 12750 | 19608 |
| 21 | 125 | 7162 | 0 | 12009 | 19296 |
| 22 | 115 | 7243 | 0 | 12781 | 20139 |
| 23 | 105 | 6512 | 0 | 13229 | 19846 |
| 24 | 97 | 7066 | 0 | 12118 | 19281 |
| 25 | 148 | 7109 | 0 | 11496 | 18753 |
| 26 | 136 | 6499 | 0 | 11381 | 18016 |
| 27 | 119 | 6780 | 0 | 11440 | 18339 |
| 28 | 99 | 8370 | 0 | 12469 | 20938 |
| 29 | 70 | 1896 | 0 | 187 | 2153 |
| 30 | 37 | 1920 | 0 | 142 | 2099 |
| 31 | 98 | 9897 | 0 | 12655 | 22650 |
| 32 | 127 | 7049 | 0 | 12519 | 19695 |
| 33 | 135 | 7301 | 0 | 12572 | 20008 |
| 34 | 151 | 8198 | 0 | 12800 | 21149 |
| 35 | 74 | 7091 | 0 | 11640 | 18805 |
| 36 | 55 | 6994 | 0 | 12608 | 19657 |
| 37 | 169 | 7194 | 0 | 12227 | 19590 |
| 38 | 155 | 6927 | 0 | 12012 | 19094 |
| 39 | 135 | 6975 | 0 | 11994 | 19104 |
| 40 | 127 | 6922 | 0 | 11428 | 18477 |
| 41 | 109 | 6610 | 0 | 11491 | 18210 |
| 42 | 146 | 7011 | 0 | 11708 | 18865 |
| 43 | 64 | 1892 | 0 | 194 | 2150 |
| 44 | 48 | 1922 | 0 | 173 | 2143 |
| 45 | 120 | 7676 | 0 | 11475 | 19271 |
| 46 | 118 | 6714 | 0 | 11424 | 18256 |
| 47 | 136 | 6831 | 0 | 11485 | 18452 |
| 48 | 127 | 6787 | 0 | 11417 | 18331 |
| 49 | 144 | 6791 | 0 | 11567 | 18502 |
| 50 | 135 | 6717 | 0 | 11480 | 18332 |
| 51 | 196 | 6865 | 0 | 11493 | 18554 |
| 52 | 167 | 6710 | 0 | 11504 | 18381 |
| 53 | 126 | 6788 | 0 | 11420 | 18334 |
| 54 | 119 | 7226 | 0 | 11657 | 19002 |
| 55 | 196 | 7083 | 0 | 11590 | 18869 |
| 56 | 199 | 7048 | 0 | 11656 | 18903 |
| 57 | 137 | 7160 | 0 | 11564 | 18861 |
| 58 | 124 | 6992 | 0 | 11527 | 18643 |
| 59 | 138 | 7416 | 0 | 11861 | 19415 |
| 60 | 131 | 6868 | 0 | 11484 | 18483 |

### Other E2 kinds and the font-size comparison

These are distributions of the **maximum reported boundary reason per edit**,
not counts of each internal refusal site. Sequential and four-worker parallel
counts agree. `boundary_reason` is a separate namespace from `structure path`.

| Kind | Structural paths | Boundary maximum reason: number of edits | Boundary fallbacks per edit |
| --- | --- | --- | --- |
| word | Not structural | 7: 26; 8: 30; 9: 4 | 1–3 |
| sentence | Not structural | 7: 6; 8: 8; 9: 46 | 1–4 |
| colour | Not structural | 0: 60 | 0 |
| fontsize | Not structural | 7: 2; 8: 8; 9: 50 | 3–9 |
| rootfont | Not structural | 7: 60 | 32 |
| block | 6: 6; 7: 54, all nonlocal | 9: 60 | 4, 6 or 133 |

[boundary_update](../../../renderer/layout/boundary.wf) uses boundary reason 7
for restyle/intrinsic/space changes, 8 for columns or spanning fragments,
and 9 for a failed ancestor/output/arithmetic certificate. The maximum
cannot reveal all contributors, and reason 9 does not establish overflow.

Font-size therefore shares the cost of reference boundary propagation, but
**does not take the structural reconstruction path**. Its E2 sequential
round medians including style are 341, 329 and 351 us. The retained round
has median two microseconds of marking (`delta_us`), zero picks, 39 us style,
314 us layout, one prepared paragraph, ten contexts, four updated paragraphs
and 1,002 reported entries. That differs from the block majority's rebuilding
740 contexts. The broad boundary/fallback counters do not allocate those
microseconds among constraints, floats, fragments, intrinsic computation or
bookkeeping, so they cannot prove a common detailed cause for the reported
2.5× regression. A renderer/profile experiment would be required for that
stronger attribution; this diagnosis changes neither renderer nor pins.


## Hosted refusal-isolation question, before the controls

The captured computed styles show `height:100%` on html and body, grid on
`main#content` and `.mw-page-container-inner`, and a first-child top-margin
rule inside the three edited blockquotes. The narrowed comparison keeps the
capture and the original X5 sites: override html height alone, body height
alone, restore body height, replace the two grids with blocks, combine that
with body height, and make blockquote paragraph top margins independent of
first-child membership. The first B/X pair precedes the complete script.
A change from reason 7 to 2 would identify a height refusal masking a grid
refusal, not a local splice. No changed path would reject that causal account.
Removing reason 6 with the margin control would distinguish sibling-style
invalidation from counter/quote state. Every control retains full-rebuild
identity as its correctness expectation; these changed inputs are diagnostic
controls, never proposed page workarounds or acceptance of the original page.

The controls reuse `page-identity-inputs` from hosted oracles run
[37668144468](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37668144468)
at `050a1ccd87a672842ec72e798207485eaa9a1b60`; CI checks that its renderer and
compiler pin equal this branch's. The original hosted capture and generated
scripts come from run
[37727037303](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37727037303).
The initial baseline must still pass the ordinary `inctime.py --check`.
The helper also captures requested full and incremental dumps for original
sentence edits 31–32, which the first run found different in both builds.

### Follow-up question before simultaneous-height controls

Run 37729474890 rejected the sufficiency of either individual html/body height
override, even with the two grids changed to blocks: every sampled path stayed
at reason 7. The blockquote margin control removed all six reason-6 outcomes;
all 60 then reported reason 7 and retained full-rebuild identity.

The next comparison overrides both html and body heights together, restores
each separately, and combines the joint override with the grid control. The
initial anonymous flow can contain both height dependencies; removing only
one cannot certify it. A broad height/min/max override supplies a bounded
control for other retained height dependencies. Reason 2 after the joint
override would support the simultaneous-height account; no change would
reject it. The full 60-edit script checks whether the first pair generalizes.

### Control results and causal limit

Hosted run [37730165607](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37730165607)
at `e8140cd89ace6ec82676d4c76ea819ed842cb979` completed these sequential
input controls, all with `inc same`. The baseline two-edit sample took
1.338 seconds before expansion; the joint-height full script took 20.151
seconds. These elapsed values selected experiment scale, not performance.

| Input control | Edits | Structure outcomes |
| --- | --- | --- |
| Original baseline | 1–2 | 2 × reason 7 |
| html and body both `height:auto` | 1–2 | 2 × reason 2 |
| Joint override, restore html `height:100%` | 1–2 | 2 × reason 7 |
| Joint override, restore body `height:100%` | 1–2 | 2 × reason 7 |
| Joint override, both grid ancestors become blocks | 1–2 | 2 × reason 9 |
| All elements auto height / zero min-height / no max-height | 1–2 | 2 × reason 2 |
| All-height override plus both grids become blocks | 1–2 | 2 × reason 9 |
| Joint html/body override | All 60 | 54 × reason 2; original six × reason 6 |

Every outcome is `splice 0`. Together with the prior one-at-a-time controls,
the restoration tests isolate two simultaneous percentage-height blockers:
removing both, and only both, exposes the grid-container refusal. The full
script establishes the same transition for every original reason-7 edit.
This agrees with the anonymous root and html/body flow ancestry constructed
by `build_boxes`, the in-flow percentage-height fact in `prepare_spaces`,
and the top-down `splice_inputs` preflight. It is not evidence that arbitrary
percentage heights can safely be ignored. The generic numeric/travel and
other reason-7 predicates remain necessary even though they are not the
first refusal for these original edits.

Changing both grids to blocks then reaches float-suffix reason 9 for the
first pair. That control changes formatting-context boundaries and geometry;
it does **not** establish a float refusal on the original grid page, or
identify an infobox as its owner. It shows why removing just one reported
guard would not establish local-splice coverage. The individual float/reach
predicate and any later mixed-inline refusal remain unisolated. A new grid
propagation implementation must measure the unchanged page again rather
than treating this altered-topology control as its expected outcome.

## Contract, stages and disposition

The owner-facing choice is whether to extend locality to the dependencies
found here; the existing fallback is the specified behavior, not a rendering
subset reduction. The relevant live node is
[the layout decision](../../../design/pipeline/layout.md), with the
[splice transaction](layout-design.md#the-splice-transaction) and
[Q128/Q129 extension](layout-design.md#q128-semantic-extension-constituent-inventory-and-proof-boundary)
as its detailed grounds. No decision or renderer code changes in this task.

| Cause or dependency | Contract and implementation relation | Disposition |
| --- | --- | --- |
| Retained sibling margin changes, reason 6 | Inserting before a blockquote's first `p` changes that retained sibling's `margin-top` from 0 to 8 px; removal restores it. `structure_splice` refuses any changed retained style outside the inserted subtree before the ancestor preflight. The margin override eliminates all six reason-6 paths. The transaction expressly puts changed sibling uses in the dirty frontier. | Covered by the existing sibling-frontier contract; completing its implementation needs no new semantic scope decision. It would still expose the later ancestor refusals, not by itself make these edits local. |
| In-flow percentage-height dependence, a reason-7 predicate | `prepare_spaces` records `flow_definite_free` across ordinary blocks, child contexts and floats; `splice_context_ready` refuses when false. html and body both specify `height:100%`. Q128's positioned stage deliberately excludes only `Out` entries from this fact because `position_one` settles those again. It does not authorize ignoring retained in-flow height dependencies. | A new scope decision and dependency proof are needed to admit this case, potentially by distinguishing an unchanged resolved basis from a true growing-height dependency. Do not simply remove the guard. |
| Enclosing grid contexts | `splice_context_ready` admits ordinary flow and the certified flex path; grid remains reason 2 when reached. The common ancestor chain contains two grids. Q128 B adds flex-container recomputation, not grid track/item propagation. | New scope decision for grid propagation. Existing grid fallback is intentional; the original reason-7 rows alone do not prove that this later guard was reached. |
| Citation pair 35–36's inline old `p` | The first contract requires complete block entries without an inline run crossing the seam; the existing citation child is `display:inline`. Mixed-inline repair remains a separately deferred certificate. | New scope decision if a local path needs mixed-inline repair. This is a masked prospective seam dependency, not the observed reason-7 cause. |
| Retained positioned boxes, floats and clearance | Relative ancestors and off-path infobox/table/float content are present, but the edited parents are ordinary sections, blockquotes or the citation div. Q128 handles positioned/atomic anchors; Q129 A handles stationary earlier float reach and common translation of later floats, including clearance checks. | Covered within those certificates; an implementation gap inside them can be fixed without new scope. A failed stationary-reach or changed-export condition would need a wider argument. No original reason 9 identifies such a structural refusal here, so no float-specific cause is established. |
| Lists and counters | The inserted/removed paragraphs introduce no list/counter operations; the retained parser-output counter reset lies outside them. The contract requires neutrality, not absence of all counters elsewhere. | No additional counter scope is indicated by these block edits; reason 5 never occurs. Non-neutral reader propagation would still be a separate owner choice if another workload requires it. |
| Sentence full/retained mismatch | Full-dump identity is mandatory even when a certificate refuses; equality of final page height is insufficient. | Correctness repair is covered by the existing contract. Deferred to a renderer task because this task explicitly forbids renderer changes; cause not yet isolated. |
| Font-size boundary replay | Different edit sites reach list/table and fragmented owners; all identity checks pass, with boundary fallbacks but no structure reconstruction. | Profiling and fixes within the existing propagation decisions require no new scope. A broader certificate needs a decision only if profiling identifies an explicitly excluded dependency; current counters cannot decide that. |

The two incidental defects have entries in `docs/todo.md`: sentence identity
is deferred to a correctness task; preserving every timing round's raw rows
is deferred to the next timing-harness change. Neither expected result was
weakened. No Whitefoot gap was encountered, and no compiler pin or submodule
was moved. The temporary workflow and its one caller-owned helper remain on
this diagnostic branch for reproducibility and must be removed before any
integration; no pull request was opened.
