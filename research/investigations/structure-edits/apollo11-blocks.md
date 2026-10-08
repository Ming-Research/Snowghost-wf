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
