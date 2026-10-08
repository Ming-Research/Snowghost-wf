# Denied layout_oracle loops at wf-exp-0eee42d9be0f

## Scope and result

All **726 requested counted-loop denials** are classified exactly once in [classification.tsv](classification.tsv): **369 condition 2** and **357 condition 1**. There are **544 T**, **110 G**, and **72 S**. Estimated hot-path reachability is **583/726** (424 T, 94 G, 65 S); the other 143 are cold under the definition below. These are loop-site counts, including nested loops separately, not invocation counts or expected speedups.

Input: `loops-0eee42d9.txt`, 1,115 `PAR loop` lines. Its complete condition-1 label count is 372: 357 accumulator/shared-binding denials plus 15 ordinary-loop denials, excluded from this task. The other diagnostic groups and permitted loops are also excluded. The conditions in the TSV are the compiler’s first reported blockers; later conditions can still prevent overlap after that blocker is repaired.

Source: [Snowghost-wf dad6183afde7e58dd9600c0b34d87b98baae1f7c](https://github.com/Ming-Research/Snowghost-wf/tree/dad6183afde7e58dd9600c0b34d87b98baae1f7c). The earlier run’s clean clone was reused. Its renderer tree is `cfe0aa45890f38f570ca90e7453c71e0127e9d85`, also the renderer tree at ee58302. The source file/line locations below are relative to `renderer/`, at that exact revision.

Language oracle: [Whitefoot kernel specification at 0eee42d9be0f](https://github.com/Ming-Research/Whitefoot/blob/0eee42d9be0f/spec/kernel-spec.md), fetched again through `gh api`; its 554,384 bytes match `kernel-spec-0eee42d9.md`. At this revision there are **PAR-1 and PAR-2, not separately numbered PAR-3 through PAR-5**. The five loop-permission conditions are inside PAR-2. This report uses those conditions and RANGE-1 through RANGE-5, rather than inventing absent rules.

## Summary table

| Class | Kind | Count | Hot estimate |
|---|---|---:|---:|
| T | T1: Sequential recurrence, prefix state, or overlapping in-place move | 174 | 138 |
| T | T2: Ordered append, publication, or removal | 161 | 112 |
| T | T3: Data-dependent traversal, priority, or shared lookup state | 192 | 157 |
| T | T4: Order-sensitive floating or mixed-sign saturating reduction | 17 | 17 |
| G | G-indirect: Unproved injectivity of stored record/payload IDs and owned routes | 32 | 30 |
| G | G-indexed: Shared indexed commutative reductions and idempotent marks | 32 | 25 |
| G | G-partition: Disjoint variable intervals stored in records, hidden by range helpers | 9 | 7 |
| G | G-footprint: Conditional element footprints behind broad mutable helpers | 10 | 10 |
| G | G-product: Several independent accumulator components in one traversal | 15 | 12 |
| G | G-sat: Record-valued unsigned saturating sum | 2 | 2 |
| G | G-select: Lexicographic and stable payload-carrying extrema | 6 | 5 |
| G | G-fmax: Floating maximum on a proven finite ordered domain | 3 | 2 |
| G | G-fields: Neighbor reads of invariant bit slices | 1 | 1 |
| S | S-fold: Canonical scalar fold and safe bounded count | 18 | 16 |
| S | S-place: Expose same-index element paths and narrow source effects | 29 | 29 |
| S | S-map: Rebase a checked subrange or expose a fixed-stride row | 7 | 5 |
| S | S-pack: Pack independent flags or position/presence into one scalar | 5 | 2 |
| S | S-wide: Exact widened sum followed by one clamp | 13 | 13 |
| **Total** | | **726** | **583** |

## Classification boundary

T means a true dependency of the current algorithm, not a claim that no different parallel algorithm exists. Ordered append, scan/prefix state, collision/interning state and overlap-sensitive copies remain T even when a different materialization algorithm could avoid them. S means a concrete local rewrite using the existing rule families, preserving the traversal’s meaning and bounds/default behavior. This includes scalar packing, helper/borrow refactoring and bounded widened reductions. G means additional semantic independence proof or a missing reduction carrier for the retained work decomposition. Repeated multi-pass loop fission or a new map/scan/scatter algorithm is not counted as a mere spelling repair. A product reduction can therefore be G even when extra passes are a possible source-only redesign. This boundary is necessary: under arbitrary algorithm replacement nearly every append or search could be called S.

A G classification is an analysis of the intended valid data invariant, not a proof certificate that the existing compiler accepts. Required uniqueness, disjointness, no-growth, domain and tie-order obligations are listed explicitly. Each G estimate is a reasoned range of **whole source loops**, assuming its stated facts and local rewrites are supplied; a kind’s count is only an upper candidate bound. Estimates overlap in prerequisites and must not be added as an independent speedup forecast. No changed source was compiled, so all prospective permission results remain unverified.

## What the existing rules already admit

- PAR-1 derives interference from actual places and substituted declared effect rows. A whole-root helper effect remains whole-root; the compiler must not silently assume a narrow implementation.
- PAR-2 condition 1 allows only one whole-binding accumulator, with every use in one of the fixed total associative/commutative operations: +wrap, *wrap, iand, ior, ixor, imin, imax, band, bor, bxor. Integer min/max are already supported.
- Condition 2 admits iteration-owned storage, the accumulator, a constant-coefficient single-binder element map, a proved fixed-stride range, or certified elements. Every access overlapping a written root must meet its family’s rules. PR #268 already permits invariant descriptor/measure reads; those are not counted as new gaps.
- RANGE permits primitive integer element facts and explicit apart certificates. It does not permit projections below an element in range terms, preserve arbitrary aggregate-copy values, or certify range-helper footprints.
- Independent work must also reach the iteration continuation and have no waits: early return, outer break and propagated failure remain blockers. Merely eliminating the first condition-1/2 report does not establish permission.

## Hot-path estimate and call graph

“Hot” means statically reachable from the full build’s layout preparation/layout entry points or the retained text, font-size/class, and block-edit entry points used by layout_oracle. It does **not** mean observed high execution frequency. The closure is a named-function call graph derived from source definitions and per-module aliases; it includes branches/fallbacks and nested helpers without a workload-frequency model. Declaration parsing reached through restyle remains included; file loading, font decoding, HTML parsing, CLI/script parsing, serialization and dump-only sorting are excluded unless one of these selected roots reaches them. Input DOM mutation and script preparation are outside the timed layout/update boundary.

| Path | Roots / representative chain | Denied sites reachable |
|---|---|---:|
| Core lay_out | layout::lay_out → lay_out_context → flow/flex/grid/table and paragraph work | 230 |
| Full layout build | build_layout, prepare_text, lay_out, layout::text::pick_fonts | 337 |
| Retained text | text_changed, update → prepare_marked/update_flow → restack/paragraph shaping | 294 |
| Font-size/class edit | style::class_restyle, style::restyle, layout::styles_restyled, text::extend_picks/pick_fonts, update | 499 |
| Block edit | style::structure_restyle, layout::structure_splice/structure_changed, text::extend_picks, update | 571 |
| Union (not sum) | all except the separately displayed subset core lay_out | **583** |

Evidence in the oracle: `oracle/layout/layout.wf:678` calls pick_all/build_layout/lay_out; `oracle/layout/edit.wf:1108` applies text_changed then update; `:1127`, `:1243`, `:1363` and `:1468` cover class/font style, block splice/fallback, font picking and retained update. Compiler listing membership alone is not call reachability: for example, font metadata parsing and dump rectangle sorting are present but cold. The broad union deliberately includes style work on edit paths; using only lay_out would omit most incremental routing/style work. No timing or profile was collected.

## Most valuable rule directions

1. **Indexed reductions (32 candidates, 25 hot):** admit independently addressed monoid cells with no prefix observation. Approximately **16–22** complete loops are plausible with integer/Boolean carriers and narrow helpers; richer cascade/border winners require explicit total keys. This addresses intentional collisions rather than trying to prove them absent.
2. **Stored-ID projection/ownership proofs (32 candidates, 30 hot):** extend RANGE to integer record/guarded payload projections and preserve those values across copies, retaining certified pairwise disjointness. Approximately **8–15** complete loops with supplied producer facts and precise helpers; subtree moves and shared visit totals need more.
3. **Product accumulators (15 candidates, 12 hot):** allow distinct scalar/field accumulators whose contributions read none of the accumulating state. Approximately **5–8** complete loops with canonical updates; saturating components and exits are extra obligations. Variable interval certificates are another useful target (9 candidates), with roughly 4–6 whole-loop admissions after endpoint/helper proof work.

These are proposals for Whitefoot, not approved language decisions or filed compiler issues. Source-only opportunities below are observations, not implemented workarounds.

## Per-kind analysis

Examples are small self-contained function fragments in the specification’s canonical source style, showing the relevant shape, not complete module/program bundles. Some demonstrate the repaired S form and identify the rejected form in prose. G examples with semantic input assumptions state those assumptions outside the code because expressing or proving them is itself the missing facility. **No example was built, tested or compiled**, as requested; syntax/type/proof obligations and predicted permission still need eventual compiler confirmation.

### T1 — Sequential recurrence, prefix state, or overlapping in-place move

**Count:** 174; **hot estimate:** 138. Conditions: 1: 142, 2: 32.

The next iteration observes a value produced by the previous one: parser/decoder state, line width, stacking cursor, hashes, sorting passes, or a slot that an overlapping copy would destroy if reordered. T1 includes anti-dependencies of in-place moves, not just read-after-write dependencies. Replacing a prefix walk by a scan, or copying through a second buffer, changes the algorithm and is not a spelling repair.

```whitefoot
fn prefix() -> made: Box<Array<u64>> pure {
  let out = box_array_filled::<u64>(count: 4_u64, value: 0_u64);
  let cursor = 0_u64;
  for (i in 0_u64..4_u64) {
    set out.inner[i] = cursor;
    set cursor = cursor +wrap 1_u64;
  }
  return move out;
}
```

The store reads cursor outside an accumulator update. PAR-2 condition 1 correctly refuses despite +wrap being an admitted reduction operator.

**Complete file:line list:**

- `base/atom/atom.wf:32`, `base/atom/atom.wf:106`

- `css/selectors/anb.wf:583`

- `css/selectors/filter.wf:189`

- `css/selectors/keys.wf:19`

- `css/selectors/positions.wf:462`

- `css/selectors/specificity.wf:314`

- `css/values/boxes.wf:362`, `css/values/boxes.wf:452`, `css/values/boxes.wf:555`, `css/values/boxes.wf:664`

- `css/values/columns.wf:116`

- `css/values/declarations.wf:903`, `css/values/declarations.wf:972`, `css/values/declarations.wf:1054`, `css/values/declarations.wf:1102`, `css/values/declarations.wf:1170`, `css/values/declarations.wf:1287`, `css/values/declarations.wf:1380`, `css/values/declarations.wf:1457`

- `css/values/generated.wf:213`, `css/values/generated.wf:363`, `css/values/generated.wf:457`

- `css/values/grid.wf:232`, `css/values/grid.wf:281`, `css/values/grid.wf:342`, `css/values/grid.wf:620`, `css/values/grid.wf:636`, `css/values/grid.wf:801`, `css/values/grid.wf:848`, `css/values/grid.wf:905`, `css/values/grid.wf:1060`, `css/values/grid.wf:1102`, `css/values/grid.wf:1140`, `css/values/grid.wf:1196`, `css/values/grid.wf:1225`, `css/values/grid.wf:1390`

- `css/values/lengths.wf:572`, `css/values/lengths.wf:695`

- `css/values/longhands.wf:557`

- `css/values/shapes.wf:175`

- `css/values/tokens.wf:308`

- `font/cmap.wf:98`, `font/cmap.wf:207`

- `font/directory.wf:84`

- `font/layout.wf:299`

- `font/matching.wf:11`, `font/matching.wf:43`, `font/matching.wf:89`, `font/matching.wf:120`

- `font/metrics.wf:129`

- `font/positioning.wf:157`

- `font/shape_apply.wf:645`, `font/shape_apply.wf:710`, `font/shape_apply.wf:721`, `font/shape_apply.wf:809`, `font/shape_apply.wf:1084`

- `font/shape_buffer.wf:232`, `font/shape_buffer.wf:338`, `font/shape_buffer.wf:383`, `font/shape_buffer.wf:410`

- `font/shape_normalize.wf:115`, `font/shape_normalize.wf:425`

- `layout/boundary.wf:554`, `layout/boundary.wf:774`

- `layout/build.wf:767`, `layout/build.wf:793`, `layout/build.wf:795`, `layout/build.wf:827`, `layout/build.wf:1025`, `layout/build.wf:1271`, `layout/build.wf:2041`, `layout/build.wf:2733`, `layout/build.wf:2739`

- `layout/columns.wf:99`, `layout/columns.wf:192`, `layout/columns.wf:220`, `layout/columns.wf:247`

- `layout/flex.wf:782`, `layout/flex.wf:866`, `layout/flex.wf:1051`, `layout/flex.wf:1233`

- `layout/flow.wf:231`, `layout/flow.wf:465`, `layout/flow.wf:626`, `layout/flow.wf:644`, `layout/flow.wf:1089`, `layout/flow.wf:1117`, `layout/flow.wf:1799`, `layout/flow.wf:1916`, `layout/flow.wf:2305`, `layout/flow.wf:2573`, `layout/flow.wf:2967`, `layout/flow.wf:3034`

- `layout/geometry.wf:161`

- `layout/grid.wf:1278`, `layout/grid.wf:1430`, `layout/grid.wf:1454`, `layout/grid.wf:1505`, `layout/grid.wf:1640`, `layout/grid.wf:1694`, `layout/grid.wf:1879`, `layout/grid.wf:2379`

- `layout/inline.wf:318`, `layout/inline.wf:337`, `layout/inline.wf:443`, `layout/inline.wf:459`, `layout/inline.wf:688`, `layout/inline.wf:1132`, `layout/inline.wf:1145`, `layout/inline.wf:1201`, `layout/inline.wf:1205`

- `layout/prep.wf:387`, `layout/prep.wf:560`, `layout/prep.wf:577`, `layout/prep.wf:620`

- `layout/sequence.wf:952`

- `layout/table.wf:596`, `layout/table.wf:597`, `layout/table.wf:702`, `layout/table.wf:829`, `layout/table.wf:922`

- `layout/tablegrid.wf:234`, `layout/tablegrid.wf:566`, `layout/tablegrid.wf:567`, `layout/tablegrid.wf:684`

- `layout/text/shape.wf:257`, `layout/text/shape.wf:827`

- `layout/update.wf:505`, `layout/update.wf:2217`

- `oracle/fonts/fonts.wf:40`, `oracle/fonts/fonts.wf:94`, `oracle/fonts/fonts.wf:128`

- `oracle/layout/edit.wf:183`, `oracle/layout/edit.wf:239`, `oracle/layout/edit.wf:847`, `oracle/layout/edit.wf:1845`, `oracle/layout/edit.wf:1860`

- `oracle/layout/layout.wf:86`, `oracle/layout/layout.wf:135`, `oracle/layout/layout.wf:300`

- `oracle/support/support.wf:469`

- `style/cascade.wf:125`, `style/cascade.wf:234`

- `style/components.wf:736`

- `style/incremental.wf:1323`, `style/incremental.wf:1325`

- `style/inherited.wf:865`, `style/inherited.wf:879`, `style/inherited.wf:1761`

- `style/intern.wf:707`, `style/intern.wf:801`, `style/intern.wf:895`, `style/intern.wf:989`, `style/intern.wf:1083`, `style/intern.wf:1177`, `style/intern.wf:1271`, `style/intern.wf:1714`, `style/intern.wf:1719`, `style/intern.wf:1786`

- `style/levels.wf:144`

- `style/lists.wf:39`, `style/lists.wf:105`, `style/lists.wf:151`

- `style/media.wf:659`, `style/media.wf:838`

- `style/restyle.wf:104`, `style/restyle.wf:328`

- `style/serialize.wf:438`

- `style/store.wf:405`, `style/store.wf:685`

- `text/line_break/line_break.wf:31`

- `text/line_break/runs.wf:177`

- `text/normalization/decompose.wf:114`

### T2 — Ordered append, publication, or removal

**Count:** 161; **hot estimate:** 112. Conditions: 1: 9, 2: 152.

The body changes a shared collection boundary, emits records in required order, or assigns stable positions by that order. This includes apparently independent initialization through place_back and route writes that grow Paged storage. Pre-sizing and indexed materialization, two-pass compaction, or prefix allocation can replace some algorithms, but the existing append operation has a real descriptor/order dependency. A shared append is not made independent by making its payload independent.

```whitefoot
fn ordered() -> made: Box<Slots<u64>> pure {
  let out = box_slots_new::<u64>(capacity: 4_u64);
  for (
    i in 0_u64..4_u64,
    invariant filled: out.inner.len == i,
    invariant room: out.inner.cap == 4_u64
  ) {
    place_back(window: &out.inner, value: i);
  }
  return move out;
}
```

Each iteration writes the same descriptor and consumes its previous len. The invariant proves bounds, not independence.

**Complete file:line list:**

- `base/atom/atom.wf:22`, `base/atom/atom.wf:233`, `base/atom/atom.wf:277`

- `css/selectors/intern.wf:51`

- `css/selectors/positions.wf:98`, `css/selectors/positions.wf:214`

- `css/selectors/reach.wf:422`, `css/selectors/reach.wf:570`

- `css/selectors/types.wf:114`

- `css/values/declarations.wf:884`, `css/values/declarations.wf:1034`, `css/values/declarations.wf:1124`, `css/values/declarations.wf:1150`, `css/values/declarations.wf:1721`, `css/values/declarations.wf:1793`, `css/values/declarations.wf:1822`

- `css/values/grid.wf:430`, `css/values/grid.wf:718`, `css/values/grid.wf:775`

- `css/values/longhands.wf:566`, `css/values/longhands.wf:702`

- `css/values/shapes.wf:248`

- `dom/dom.wf:543`, `dom/dom.wf:591`

- `font/shape_buffer.wf:334`

- `font/shape_run.wf:18`, `font/shape_run.wf:44`

- `font/shape_substitute.wf:95`

- `html/tokenizer/tags.wf:240`

- `html/tokenizer/types.wf:14`

- `layout/boundary.wf:616`

- `layout/box.wf:519`

- `layout/build.wf:390`, `layout/build.wf:394`, `layout/build.wf:408`, `layout/build.wf:426`, `layout/build.wf:779`, `layout/build.wf:843`, `layout/build.wf:1057`, `layout/build.wf:2177`, `layout/build.wf:2955`

- `layout/columns.wf:134`, `layout/columns.wf:161`

- `layout/flex.wf:699`, `layout/flex.wf:742`, `layout/flex.wf:1482`

- `layout/flow.wf:1027`, `layout/flow.wf:1036`, `layout/flow.wf:1234`, `layout/flow.wf:1524`, `layout/flow.wf:1668`, `layout/flow.wf:1721`, `layout/flow.wf:2656`, `layout/flow.wf:3359`, `layout/flow.wf:3412`, `layout/flow.wf:3421`, `layout/flow.wf:3436`, `layout/flow.wf:3444`, `layout/flow.wf:3455`, `layout/flow.wf:3465`

- `layout/grid.wf:854`, `layout/grid.wf:860`, `layout/grid.wf:1234`

- `layout/inline.wf:415`, `layout/inline.wf:1117`, `layout/inline.wf:1125`, `layout/inline.wf:1506`, `layout/inline.wf:1578`, `layout/inline.wf:1594`, `layout/inline.wf:1628`, `layout/inline.wf:1645`

- `layout/pages.wf:32`, `layout/pages.wf:58`

- `layout/sequence.wf:996`

- `layout/splice_publish.wf:92`, `layout/splice_publish.wf:99`, `layout/splice_publish.wf:109`, `layout/splice_publish.wf:114`, `layout/splice_publish.wf:249`, `layout/splice_publish.wf:253`, `layout/splice_publish.wf:257`, `layout/splice_publish.wf:290`

- `layout/structure.wf:27`, `layout/structure.wf:39`, `layout/structure.wf:428`, `layout/structure.wf:572`, `layout/structure.wf:575`, `layout/structure.wf:748`

- `layout/table.wf:56`, `layout/table.wf:754`, `layout/table.wf:1015`, `layout/table.wf:1080`

- `layout/tablegrid.wf:75`, `layout/tablegrid.wf:85`, `layout/tablegrid.wf:96`, `layout/tablegrid.wf:123`

- `layout/text/fonts.wf:113`

- `layout/text/picks.wf:210`, `layout/text/picks.wf:245`, `layout/text/picks.wf:270`, `layout/text/picks.wf:277`, `layout/text/picks.wf:340`, `layout/text/picks.wf:347`

- `layout/update.wf:187`, `layout/update.wf:1553`

- `oracle/layout/edit.wf:271`

- `oracle/layout/layout.wf:310`, `oracle/layout/layout.wf:390`, `oracle/layout/layout.wf:520`, `oracle/layout/layout.wf:562`

- `oracle/support/support.wf:61`, `oracle/support/support.wf:516`

- `style/cascade.wf:98`, `style/cascade.wf:107`, `style/cascade.wf:141`, `style/cascade.wf:697`, `style/cascade.wf:700`

- `style/delta.wf:125`, `style/delta.wf:141`, `style/delta.wf:171`, `style/delta.wf:195`, `style/delta.wf:224`, `style/delta.wf:247`, `style/delta.wf:273`, `style/delta.wf:354`

- `style/hints.wf:194`, `style/hints.wf:510`

- `style/incremental.wf:1339`, `style/incremental.wf:1526`

- `style/inherited.wf:916`

- `style/levels.wf:67`

- `style/lists.wf:176`, `style/lists.wf:251`, `style/lists.wf:307`, `style/lists.wf:322`, `style/lists.wf:350`, `style/lists.wf:382`, `style/lists.wf:453`, `style/lists.wf:473`, `style/lists.wf:666`, `style/lists.wf:681`, `style/lists.wf:718`, `style/lists.wf:735`, `style/lists.wf:775`, `style/lists.wf:789`, `style/lists.wf:830`, `style/lists.wf:842`

- `style/restyle.wf:112`, `style/restyle.wf:549`, `style/restyle.wf:826`

- `style/serialize.wf:46`, `style/serialize.wf:119`

- `style/store.wf:460`, `style/store.wf:723`, `style/store.wf:820`

- `style/structure.wf:404`

- `style/traversal.wf:322`

- `text/normalization/decompose.wf:27`, `text/normalization/decompose.wf:49`, `text/normalization/decompose.wf:121`, `text/normalization/decompose.wf:127`

### T3 — Data-dependent traversal, priority, or shared lookup state

**Count:** 192; **hot estimate:** 157. Conditions: 1: 125, 2: 67.

Pointer/ancestor walks, binary searches, insertion sorts, first-match selection, collision probing and first-seen interning choose later work from previous results. The current algorithm's ordering is meaningful. Some read-only searches could be redesigned as argmin reductions, but that is not evidence that their existing cursor or first-success mutation is independent.

```whitefoot
fn walk(next: &[u64]) -> end: u64 reads(next) {
  let at = 0_u64;
  let count = next^.len;
  for (step in 0_u64..count) {
    if at < count {
      set at = next^[at];
    }
  }
  return at;
}
```

The next address depends on the preceding loaded value; a uniqueness assertion about step cannot separate the accesses.

**Complete file:line list:**

- `base/atom/atom.wf:177`, `base/atom/atom.wf:240`

- `css/selectors/dom_walk.wf:149`, `css/selectors/dom_walk.wf:177`, `css/selectors/dom_walk.wf:210`, `css/selectors/dom_walk.wf:233`

- `css/selectors/filter.wf:320`, `css/selectors/filter.wf:368`, `css/selectors/filter.wf:390`

- `css/selectors/keys.wf:143`

- `css/selectors/match.wf:344`

- `css/selectors/positions.wf:250`, `css/selectors/positions.wf:316`

- `css/selectors/reach.wf:527`

- `css/values/boxes.wf:571`

- `css/values/declarations.wf:1896`

- `css/values/grid.wf:673`

- `css/values/longhands.wf:538`

- `css/values/tokens.wf:230`, `css/values/tokens.wf:251`

- `dom/dom.wf:362`

- `font/gdef.wf:124`

- `font/shape_apply.wf:478`, `font/shape_apply.wf:534`, `font/shape_apply.wf:551`, `font/shape_apply.wf:603`, `font/shape_apply.wf:683`, `font/shape_apply.wf:751`, `font/shape_apply.wf:923`, `font/shape_apply.wf:994`

- `font/shape_buffer.wf:208`

- `font/shape_normalize.wf:315`, `font/shape_normalize.wf:404`

- `font/shape_position.wf:586`, `font/shape_position.wf:700`

- `font/shape_substitute.wf:138`

- `html/tokenizer/tags.wf:278`

- `layout/boundary.wf:589`, `layout/boundary.wf:691`

- `layout/build.wf:482`, `layout/build.wf:609`, `layout/build.wf:668`, `layout/build.wf:1588`, `layout/build.wf:1934`, `layout/build.wf:2108`, `layout/build.wf:2148`, `layout/build.wf:2217`, `layout/build.wf:2289`, `layout/build.wf:2399`, `layout/build.wf:2449`, `layout/build.wf:2531`, `layout/build.wf:2574`

- `layout/flex.wf:660`, `layout/flex.wf:667`

- `layout/flow.wf:959`, `layout/flow.wf:966`, `layout/flow.wf:1051`, `layout/flow.wf:1129`, `layout/flow.wf:1686`, `layout/flow.wf:1692`, `layout/flow.wf:1786`, `layout/flow.wf:1898`, `layout/flow.wf:2846`

- `layout/geometry.wf:67`

- `layout/grid.wf:645`, `layout/grid.wf:661`, `layout/grid.wf:912`, `layout/grid.wf:1087`, `layout/grid.wf:1107`, `layout/grid.wf:1147`, `layout/grid.wf:1165`, `layout/grid.wf:1180`, `layout/grid.wf:1555`

- `layout/inline.wf:630`, `layout/inline.wf:886`, `layout/inline.wf:943`, `layout/inline.wf:966`, `layout/inline.wf:1167`

- `layout/sequence.wf:685`, `layout/sequence.wf:708`, `layout/sequence.wf:794`

- `layout/splice.wf:52`

- `layout/splice_boundary.wf:134`

- `layout/splice_publish.wf:33`

- `layout/splice_sequence.wf:16`

- `layout/structure.wf:314`, `layout/structure.wf:414`, `layout/structure.wf:752`, `layout/structure.wf:808`

- `layout/style_update.wf:556`, `layout/style_update.wf:575`, `layout/style_update.wf:723`, `layout/style_update.wf:736`

- `layout/table.wf:640`, `layout/table.wf:1036`, `layout/table.wf:1097`, `layout/table.wf:1129`

- `layout/tablegrid.wf:609`

- `layout/text/shape.wf:92`, `layout/text/shape.wf:245`, `layout/text/shape.wf:378`

- `layout/update.wf:168`, `layout/update.wf:964`, `layout/update.wf:987`, `layout/update.wf:1852`

- `oracle/layout/edit.wf:1210`, `oracle/layout/edit.wf:1884`

- `oracle/layout/layout.wf:338`, `oracle/layout/layout.wf:340`, `oracle/layout/layout.wf:455`

- `style/cascade.wf:307`

- `style/delta.wf:529`, `style/delta.wf:539`, `style/delta.wf:549`, `style/delta.wf:556`, `style/delta.wf:563`, `style/delta.wf:575`, `style/delta.wf:585`, `style/delta.wf:595`, `style/delta.wf:605`, `style/delta.wf:615`, `style/delta.wf:625`, `style/delta.wf:635`, `style/delta.wf:645`, `style/delta.wf:655`, `style/delta.wf:665`

- `style/hints.wf:103`, `style/hints.wf:128`, `style/hints.wf:157`

- `style/incremental.wf:470`, `style/incremental.wf:1573`

- `style/inherited.wf:753`, `style/inherited.wf:768`, `style/inherited.wf:1812`, `style/inherited.wf:1818`

- `style/intern.wf:724`, `style/intern.wf:727`, `style/intern.wf:756`, `style/intern.wf:761`, `style/intern.wf:818`, `style/intern.wf:821`, `style/intern.wf:850`, `style/intern.wf:855`, `style/intern.wf:912`, `style/intern.wf:915`, `style/intern.wf:944`, `style/intern.wf:949`, `style/intern.wf:1006`, `style/intern.wf:1009`, `style/intern.wf:1038`, `style/intern.wf:1043`, `style/intern.wf:1100`, `style/intern.wf:1103`, `style/intern.wf:1132`, `style/intern.wf:1137`, `style/intern.wf:1194`, `style/intern.wf:1197`, `style/intern.wf:1226`, `style/intern.wf:1231`, `style/intern.wf:1288`, `style/intern.wf:1291`, `style/intern.wf:1320`, `style/intern.wf:1325`, `style/intern.wf:1801`, `style/intern.wf:1806`, `style/intern.wf:1824`, `style/intern.wf:1828`

- `style/lists.wf:121`, `style/lists.wf:125`, `style/lists.wf:158`, `style/lists.wf:528`, `style/lists.wf:588`, `style/lists.wf:627`, `style/lists.wf:904`

- `style/reset.wf:161`

- `style/restyle.wf:193`, `style/restyle.wf:267`, `style/restyle.wf:428`, `style/restyle.wf:435`, `style/restyle.wf:523`, `style/restyle.wf:658`, `style/restyle.wf:743`, `style/restyle.wf:863`, `style/restyle.wf:894`, `style/restyle.wf:961`, `style/restyle.wf:1001`

- `style/serialize.wf:271`

- `style/store.wf:927`

- `style/structure.wf:128`, `style/structure.wf:184`

- `style/traversal.wf:142`, `style/traversal.wf:198`

### T4 — Order-sensitive floating or mixed-sign saturating reduction

**Count:** 17; **hot estimate:** 17. Conditions: 1: 13, 2: 4.

Strict floating addition and mixed-sign signed saturating addition do not preserve their published result under reassociation. Positive or negative margins make several layout size sums mixed-sign. By contrast unsigned saturation, and saturation restricted to one sign, are associative; those are not T4 merely because the operator is spelled +sat.

```whitefoot
fn ordered_sum(values: &[i32]) -> result: i32 reads(values) {
  let total = 0_i32;
  let count = values^.len;
  for (i in 0_u64..count) {
    set total = total +sat values^[i];
  }
  return total;
}
```

For values [2147483647, 1, -1], source-order saturation yields 2147483646, whereas grouping the last two terms first yields 2147483647. Exact integer modeling of saturating operations still has this difference. Floating addition is associative over real arithmetic but not over the actual strict floating operation; T4 refers to exact preservation of that operation's result.

**Complete file:line list:**

- `font/shape_position.wf:677`, `font/shape_position.wf:683`

- `layout/flex.wf:296`, `layout/flex.wf:825`, `layout/flex.wf:834`, `layout/flex.wf:871`, `layout/flex.wf:920`, `layout/flex.wf:999`

- `layout/grid.wf:1538`, `layout/grid.wf:1699`, `layout/grid.wf:1808`

- `layout/inline.wf:208`, `layout/inline.wf:1672`

- `layout/table.wf:766`

- `layout/tablegrid.wf:422`, `layout/tablegrid.wf:704`

- `layout/text/shape.wf:340`

### G-indirect — Unproved injectivity of stored record/payload IDs and owned routes

**Count:** 32; **hot estimate:** 30. Conditions: 1: 5, 2: 27.

Independent destinations are named by lane.child, Item.child, NodeId.index, Flow/Mark payloads, packed IDs, or routes into distinct owned subtrees. PAR-2's affine family cannot express them. RANGE already handles primitive integer index arrays when appropriate forall facts and apart certificates are supplied: plain integer scatter by itself is not a new language gap. The missing parts here are projections below record/enum elements, value-preserving aggregate-copy images, and, in the harder cases, helper/subtree footprints. Scratch reused between parents is an additional issue at selectors/positions.wf:109, not proof that the parent outputs overlap.

```whitefoot
struct Destination {
  index: u64;
}

fn scatter() -> made: Box<Array<u64>> pure {
  let zero = Destination(index: 0_u64);
  let ids = box_array_filled::<Destination>(count: 2_u64, value: zero);
  set ids.inner[1_u64] = Destination(index: 1_u64);
  let out = box_array_filled::<u64>(count: 2_u64, value: 0_u64);
  for (i in 0_u64..2_u64) {
    let entry = ids.inner[i];
    let at = entry.index;
    if at < 2_u64 {
      set out.inner[at] = i;
    }
  }
  return move out;
}
```

Smallest rule change: extend RANGE-1 integer terms through a selected record field (and guarded enum payload), and RANGE-2 copying to preserve those projection values. Retain versioned support, bounds, and the existing two-iteration write/read and write/write apart proof. The producer must establish IDs' injectivity; never assume it from the name or from a traversal's intended use. Duplicate destinations remain unproved. Whole-context helpers must be narrowed or separately gain proved footprints; packed bit extraction and disjoint recursive routes require additional supported images. Estimate: approximately 8–15 whole loops with projection facts and narrow source helpers; the entire kind is a ceiling, not a promised admission count. BoundaryMove loops also update visits, and reuse/retirement loops require subtree ownership and count reductions.

**Complete file:line list:**

- `css/selectors/positions.wf:109`

- `layout/boundary.wf:679`

- `layout/flex.wf:753`

- `layout/flow.wf:290`, `layout/flow.wf:551`, `layout/flow.wf:944`, `layout/flow.wf:1353`, `layout/flow.wf:1496`, `layout/flow.wf:1829`, `layout/flow.wf:2923`

- `layout/splice_boundary.wf:275`

- `layout/splice_publish.wf:319`

- `layout/structure.wf:552`, `layout/structure.wf:602`, `layout/structure.wf:715`

- `layout/table.wf:138`, `layout/table.wf:725`, `layout/table.wf:844`, `layout/table.wf:907`

- `layout/update.wf:1036`, `layout/update.wf:1046`, `layout/update.wf:2129`, `layout/update.wf:2138`, `layout/update.wf:2346`, `layout/update.wf:2358`

- `oracle/layout/layout.wf:434`

- `style/delta.wf:775`

- `style/incremental.wf:1150`, `style/incremental.wf:1293`

- `style/structure.wf:324`, `style/structure.wf:336`, `style/structure.wf:360`

### G-indexed — Shared indexed commutative reductions and idempotent marks

**Count:** 32; **hot estimate:** 25. Conditions: 1: 1, 2: 31.

Several iterations intentionally address the same bucket: coverage-word OR, flags, row maxima, histograms, cascade winners and border winners. Injectivity is false and must not be asserted. Repeated identical True/1/zero/hole stores are idempotent updates; histogram +wrap and bounded counts are exact folds. Cascade/border payload selection needs a total key including original priority/tie order. Concurrent writes are not permitted merely because they usually store the same value.

```whitefoot
fn histogram(keys: &[u8]) -> made: Box<Array<u64>> reads(keys) {
  let counts = box_array_filled::<u64>(count: 256_u64, value: 0_u64);
  let count = keys^.len;
  for (i in 0_u64..count) {
    let bucket = cvt::<u8, u64>(keys^[i]);
    set counts.inner[bucket] = counts.inner[bucket] +wrap 1_u64;
  }
  return move counts;
}
```

Smallest rule change: extend PAR-2's closed scalar reduction operations to an indexed family of accumulator cells. Each cell may occur only as the target and one operand of the same fixed monoid operation; destination and contribution must not depend on any updated cell. No prefix reads or check-before-enqueue are allowed. Preserve the initial cell once, reduce privately, and combine with the specified identity. Normalize constant idempotent marks to proved OR/AND forms. More complex stable winners need an explicitly verified carrier rather than an arbitrary user helper. Estimate: roughly 16–22 whole loops with integer/Boolean bucket reductions and local helper narrowing; all loops in this kind are candidates only after record winners, product flags, indirect independent writes, and early exits are also handled.

**Complete file:line list:**

- `font/lookup_filters.wf:95`, `font/lookup_filters.wf:103`, `font/lookup_filters.wf:139`

- `font/shape_plan.wf:211`, `font/shape_plan.wf:267`

- `layout/flow.wf:1189`

- `layout/grid.wf:1070`, `layout/grid.wf:1239`, `layout/grid.wf:2273`

- `layout/inline.wf:1087`

- `layout/table.wf:532`

- `layout/tableborders.wf:127`, `layout/tableborders.wf:143`, `layout/tableborders.wf:185`

- `layout/tablegrid.wf:526`, `layout/tablegrid.wf:543`, `layout/tablegrid.wf:600`

- `oracle/layout/edit.wf:1196`

- `oracle/layout/layout.wf:286`

- `style/cascade.wf:184`, `style/cascade.wf:270`, `style/cascade.wf:419`

- `style/incremental.wf:77`, `style/incremental.wf:996`, `style/incremental.wf:1162`, `style/incremental.wf:1387`, `style/incremental.wf:1418`, `style/incremental.wf:1424`

- `style/levels.wf:30`

- `style/restyle.wf:97`

- `style/structure.wf:369`

- `text/normalization/decompose.wf:101`

### G-partition — Disjoint variable intervals stored in records, hidden by range helpers

**Count:** 9; **hot estimate:** 7. Conditions: 1: 0, 2: 9.

FlexLine, ClassRange, TextRun, shaped-segment, owner-sequence, row-group and sort-bucket boundaries define disjoint intervals. Their lengths vary; they do not have the existing single [s*i+b,s*i+b+s) form. RANGE-5 currently refuses whole-range call accesses rather than proving interval separation. Constant or runtime fixed-stride rows are already supported and are classified S-map. Row-group work also needs private deltas/weights scratch.

```whitefoot
struct Span {
  start: u64;
  end: u64;
}

fn clear(part: &[u64]) -> result: unit writes(part) {
  let count = part^.len;
  for (k in 0_u64..count) {
    set part^[k] = 0_u64;
  }
  return unit;
}

fn partitions(spans: &[Span], out: &[u64]) -> result: unit reads(spans), writes(out) {
  let count = spans^.len;
  for (i in 0_u64..count) {
    let span = spans^[i];
    if span.start <= span.end {
      if span.end <= out^.len {
        clear(part: &out^[span.start..span.end]);
      }
    }
  }
  return unit;
}
```

This fragment's intended independent input has pairwise disjoint spans; existing declarations cannot express the needed below-element projection fact. Smallest rule change: permit RANGE projected endpoint facts plus certified interval footprints, proving for any i != j that end_i <= start_j or end_j <= start_i for every overlapping written/read origin, with helper accesses contained in their actual ranges. Do not infer independence from sorted starts alone: nested or overlapping spans must fail. Estimate: about 4–6 whole loops with endpoint facts and helper range refactoring; the others also need privatized scratch, compound effects or counts.

**Complete file:line list:**

- `font/gdef.wf:75`

- `layout/flex.wf:1530`, `layout/flex.wf:1575`

- `layout/inline.wf:189`, `layout/inline.wf:1070`

- `layout/sequence.wf:970`

- `layout/table.wf:625`

- `oracle/layout/layout.wf:327`

- `text/line_break/line_break.wf:67`

### G-footprint — Conditional element footprints behind broad mutable helpers

**Count:** 10; **hot estimate:** 10. Conditions: 1: 1, 2: 9.

Glyph field transforms and child positioning pass a whole Buffer or Context to helpers. The semantic work on a valid live buffer is per element, but write_item's general interface can append, change descriptors and mark failure. Those effects cannot be erased from its row without proving the live-prefix/no-growth invariant at each call. This kind distinguishes that missing contextual footprint proof from the S-place helpers whose complete semantics are already simple guarded element accesses. The original transfer/extension loops with actual overlap or growth have been moved to T1/T2.

```whitefoot
struct Buffer {
  items: Box<Slots<u64>>;
  count: u64;
}

fn put(buffer: &Buffer, at: u64, value: u64) -> result: unit writes(buffer) {
  if at < buffer^.items.inner.len {
    set buffer^.items.inner[at] = value;
  } else if at == buffer^.items.inner.len {
    if buffer^.items.inner.len < buffer^.items.inner.cap {
      place_back(window: &buffer^.items.inner, value: value);
    }
  }
  return unit;
}

fn fill(buffer: &Buffer) -> result: unit writes(buffer) {
  let count = buffer^.count;
  for (i in 0_u64..count) {
    put(buffer: buffer, at: i, value: 1_u64);
  }
  return unit;
}
```

For valid live-buffer inputs, count <= items.inner.len before the loop: only existing-element stores execute. The fragment alone does not establish that invariant and general callers can append. Smallest rule change: admit a verified index-dependent conditional call footprint, consuming the caller's proved live-prefix bound and the callee's proved branch summary under PAR-2. A summary must exclude descriptor/failure writes and separate any input/output backing storage; never specialize away an append or failure branch without proof. Without the live-prefix premise this loop is T2. Alternatively, a source contract plus a specialized existing-element helper may move individual cases to S; the count here measures the current broad-interface/invariant gap. Estimate: 0 from naive effect narrowing alone; approximately 6–9 whole loops with proven live-buffer specialization and precise element rows. The context-positioning case also folds UpdateCounts.

**Complete file:line list:**

- `font/shape_buffer.wf:531`, `font/shape_buffer.wf:600`

- `font/shape_normalize.wf:644`, `font/shape_normalize.wf:648`, `font/shape_normalize.wf:672`

- `font/shape_position.wf:554`, `font/shape_position.wf:620`, `font/shape_position.wf:639`, `font/shape_position.wf:727`

- `layout/flow.wf:2880`

### G-product — Several independent accumulator components in one traversal

**Count:** 15; **hot estimate:** 12. Conditions: 1: 14, 2: 1.

FeatureFilter's four bit-vector words, geometry bounds, count/max pairs and UpdateCounts are products of independent folds. PAR-2 admits at most one whole binding, each occurrence in a fixed primitive operation; assigning one record through a pure combine helper does not meet that form. Small flag products that fit one ordinary bit mask are S-pack. Fission into several scans or an intermediate mapped array is possible for some remaining cases, but changes the traversal/work decomposition rather than locally spelling the accumulator.

```whitefoot
fn bounds(values: &[u64]) -> (lo: u64, hi: u64) reads(values) {
  let lower = 18446744073709551615_u64;
  let upper = 0_u64;
  let count = values^.len;
  for (i in 0_u64..count) {
    set lower = imin(lower, values^[i]);
    set upper = imax(upper, values^[i]);
  }
  return lower, upper;
}
```

Smallest rule change: admit a finite product of distinct accumulators or nonoverlapping record fields, each satisfying the existing no-other-occurrence condition with its own fixed operator and identity. Contributions may not read any of the product's accumulating state. Recombining each component independently is equivalent to the sequential product fold; a running cursor feeding another component still fails. Unsigned saturating components need G-sat too. Estimate: about 5–8 whole loops with product admission and canonical component updates; malformed-input exits, saturating counts, and indirect destinations keep the remainder dependent on further work.

**Complete file:line list:**

- `css/selectors/filter.wf:84`, `css/selectors/filter.wf:233`, `css/selectors/filter.wf:269`, `css/selectors/filter.wf:302`

- `css/selectors/reach.wf:305`

- `css/values/grid.wf:725`

- `layout/build.wf:2721`

- `layout/flex.wf:1190`

- `layout/grid.wf:341`, `layout/grid.wf:1024`, `layout/grid.wf:1480`

- `layout/structure.wf:614`

- `layout/tablegrid.wf:841`

- `layout/update.wf:758`, `layout/update.wf:2241`

### G-sat — Record-valued unsigned saturating sum

**Count:** 2; **hot estimate:** 2. Conditions: 1: 2, 2: 0.

Specificity adds three u32 components with unsigned saturation. Unsigned sat(a+b)=min(MAX,a+b) is associative and commutative with zero identity over the full unsigned type. The specification's blanket statement that +sat is not associative is correct for mixed-sign signed addition but too broad for unsigned addition. These record folds also need product-carrier support. Bounded scalar layout sums have source-only widening repairs and are S-wide.

```whitefoot
fn capped(values: &[u64]) -> result: u64 reads(values) {
  let total = 0_u64;
  let count = values^.len;
  for (i in 0_u64..count) {
    set total = total +sat values^[i];
  }
  return total;
}
```

Smallest rule change: add unsigned +sat to PAR-2's closed operation/type table with identity zero; do not add general signed +sat. For unsigned inputs both associations equal min(MAX,a+b+c), so the extension does not admit the T4 counterexample. Estimate: 0 complete corpus loops from the scalar change alone; 2 with componentwise product reduction. There is no justification to relax signed overflow or strict floating sums.

**Complete file:line list:**

- `css/selectors/specificity.wf:81`, `css/selectors/specificity.wf:91`

### G-select — Lexicographic and stable payload-carrying extrema

**Count:** 6; **hot estimate:** 5. Conditions: 1: 6, 2: 0.

The reductions select a Specificity, optional specificity, baseline, face or argument payload according to a total priority. The scalar imin/imax rows are already admitted; the missing carrier is a record or option and, for ties, the original ordinal. 'First wins' alone is not commutative: it becomes a stable selection monoid only when original index is part of the key.

```whitefoot
struct Pair {
  major: u64;
  minor: u64;
}

fn larger(a: Pair, b: Pair) -> result: Pair pure {
  if a.major > b.major {
    return a;
  }
  if a.major < b.major {
    return b;
  }
  if a.minor >= b.minor {
    return a;
  }
  return b;
}

fn maximum(values: &[Pair]) -> result: Pair reads(values) {
  let best = Pair(major: 0_u64, minor: 0_u64);
  let count = values^.len;
  for (i in 0_u64..count) {
    set best = larger(a: best, b: values^[i]);
  }
  return best;
}
```

Smallest rule change: add a compiler-checked lexicographic min/max carrier with a specified total key order and identity (None for optional candidates). Payload ties must be equal or resolved by a unique original ordinal; all contributions are independent of the current winner. This avoids admitting arbitrary user functions as associative. Estimate: 3–6 whole loops after canonical carrier conversion and removal/encoding of bounds exits; simple integer key maxima need no change.

**Complete file:line list:**

- `css/selectors/specificity.wf:55`, `css/selectors/specificity.wf:278`, `css/selectors/specificity.wf:354`

- `layout/grid.wf:2582`

- `layout/text/fonts.wf:388`

- `oracle/page/page.wf:145`

### G-fmax — Floating maximum on a proven finite ordered domain

**Count:** 3; **hot estimate:** 2. Conditions: 1: 3, 2: 0.

Grid minimum-fraction selection and rectangle-bottom selection use maxima, not floating addition. Finite ordered maxima have no rounding accumulation; PAR-2 nevertheless admits no floating operator. The sign of zero and NaN rules must be settled, not assumed from the word max. Grid leftover shares can be negative. Retain the original initial zero as a leaf, or normalize contributions by fmax with positive zero before a nonnegative-domain reduction. The rectangle dump case is cold.

```whitefoot
fn maximum(values: &[f32]) -> result: f32 reads(values) {
  let best = 0.0_f32;
  let count = values^.len;
  for (i in 0_u64..count) {
    set best = fmax(best, values^[i]);
  }
  return best;
}
```

The intended domain is finite nonnegative values with a fixed zero representation; the fragment alone does not establish that domain. Smallest rule change: a maximum reduction with a proved closed finite ordered domain and exact tie/zero behavior, or a total bit-pattern order that is proved equivalent to the original operator on its input domain. Zero is identity for the nonnegative domain; unrestricted signed values need the correct lower identity. Reject NaN/zero cases unless equivalence is proved. Estimate: 2–3 whole loops after domain evidence; do not extend this permission to fadd.strict.

**Complete file:line list:**

- `layout/grid.wf:1774`, `layout/grid.wf:1789`

- `oracle/layout/layout.wf:515`

### G-fields — Neighbor reads of invariant bit slices

**Count:** 1; **hot estimate:** 1. Conditions: 1: 0, 2: 1.

unhide_joiners reads neighboring combining-class/category bits but clears only unicode_hidden=64 in its own item. These are different bits of the same u16 unicode_props, not merely different record fields. PAR-2 sees neighbor element reads of the written root; whole-Item copies/helpers broaden that further. Ordinary field sensitivity alone is insufficient.

```whitefoot
fn clear_low(values: &[u16]) -> result: unit writes(values) {
  let count = values^.len;
  for (i in 1_u64..count) {
    let previous = i - 1_u64;
    let high = ishr.wrap(values^[previous], 8_u32);
    if high == 0_u16 {
      set values^[i] = iand(values^[i], 65534_u16);
    }
  }
  return unit;
}
```

Smallest rule change: prove value dependence on read masks and effective write masks, retaining untouched bits for RMW, and admit neighbor reads only when their masks are invariant under all writes. In this example the read uses bits 8–15 and writes only bit 0. If the predicate instead reads bit 0 of the predecessor, it must fail. The lowering must preserve bit/word race freedom, e.g. by reading a snapshot or safe scheduling; mask reasoning is not permission for racy machine loads. Estimate: 1 whole loop only with bit-dependence proof plus live-buffer element specialization; field-only refinement admits 0.

**Complete file:line list:**

- `font/shape_normalize.wf:475`

### S-fold — Canonical scalar fold and safe bounded count

**Count:** 18; **hot estimate:** 16. Conditions: 1: 18, 2: 0.

Spell a maximum/minimum as imax/imin on the whole accumulator; inline a pure lower helper; replace sticky True/False assignment with bor/band; replace a read-only early-exit Boolean scan by a guarded full fold; use +wrap for a zero-based count whose maximum cannot exceed u64. Preserve empty-input values and all bounds guards. Early exits may be removed only when later evaluations are total and have no observable writes beyond the fold.

```whitefoot
fn any_nonzero(values: &[u64]) -> result: Bool reads(values) {
  let any = False();
  let count = values^.len;
  for (i in 0_u64..count) {
    if values^[i] != 0_u64 {
      set any = True();
    }
  }
  return any;
}
```

Repair the update to `let yes = True();` followed by `set any = bor(any, yes);`. Every accumulator occurrence then has PAR-2's admitted shape. Bounds-safe +wrap counts are mathematical counts, not a request to accept wrapping overflow.

**Complete file:line list:**

- `css/selectors/positions.wf:76`

- `font/shape_buffer.wf:472`, `font/shape_buffer.wf:550`

- `font/shape_position.wf:713`

- `layout/build.wf:2714`

- `layout/grid.wf:1432`, `layout/grid.wf:1723`

- `layout/table.wf:456`

- `layout/tablegrid.wf:158`

- `layout/text/shape.wf:798`

- `layout/update.wf:2063`

- `oracle/layout/edit.wf:452`

- `oracle/layout/layout.wf:176`

- `style/cascade.wf:666`

- `style/components.wf:751`

- `style/incremental.wf:1019`

- `style/inherited.wf:937`, `style/inherited.wf:1841`

### S-place — Expose same-index element paths and narrow source effects

**Count:** 29; **hot estimate:** 29. Conditions: 1: 0, 2: 29.

Inline guarded get/put helpers or pass the actual element to a scalar helper; preserve their bounds/default behavior. Replace an opaque local reference spelling with the explicit same-index path where the listing fails to recognize the alias. Narrow a helper's declared read row when its complete implementation reads only disjoint fields. These require no extra independence rule.

```whitefoot
fn put_one(value: &u64) -> result: unit writes(value) {
  set value^ = 1_u64;
  return unit;
}

fn fill(out: &[u64]) -> result: unit writes(out) {
  let count = out^.len;
  for (i in 0_u64..count) {
    put_one(value: &out^[i]);
  }
  return unit;
}
```

This exposes a narrow element helper: the callee row projects onto out[i], not all of out. For layout/update.wf's split loop, block_at_entry reads blocks/events, so its source effect can stop claiming reads of splits. For relocate_splice, explicit paths are a source repair prediction; PAR-2 normatively resolves references, so those denials may also expose an implementation recognition defect.

**Complete file:line list:**

- `font/shape_apply.wf:743`, `font/shape_apply.wf:815`

- `layout/grid.wf:945`

- `layout/splice_publish.wf:130`, `layout/splice_publish.wf:151`, `layout/splice_publish.wf:203`

- `layout/structure.wf:892`

- `layout/table.wf:484`, `layout/table.wf:501`, `layout/table.wf:514`, `layout/table.wf:586`

- `layout/tablegrid.wf:182`, `layout/tablegrid.wf:254`, `layout/tablegrid.wf:294`, `layout/tablegrid.wf:351`, `layout/tablegrid.wf:388`, `layout/tablegrid.wf:445`, `layout/tablegrid.wf:479`, `layout/tablegrid.wf:507`, `layout/tablegrid.wf:559`, `layout/tablegrid.wf:584`, `layout/tablegrid.wf:654`, `layout/tablegrid.wf:669`, `layout/tablegrid.wf:797`, `layout/tablegrid.wf:809`, `layout/tablegrid.wf:822`, `layout/tablegrid.wf:875`, `layout/tablegrid.wf:906`

- `layout/update.wf:2149`

### S-map — Rebase a checked subrange or expose a fixed-stride row

**Count:** 7; **hot estimate:** 5. Conditions: 1: 0, 2: 7.

A runtime base in out[base+i] is outside the constant-offset affine-element family, but borrowing out[base..end] once makes part[i] the supported map. For a matrix, pass each checked full row [r*stride,r*stride+stride) as a range argument; PAR-2 already permits loop-invariant runtime stride. Keep checked arithmetic, original bounds/empty behavior, and separate a partial final row if one exists. No new RANGE injectivity rule is needed.

```whitefoot
fn fill_from(out: &[u64], base: u64) -> result: unit writes(out) {
  if base <= out^.len {
    let end = out^.len;
    let count = end - base;
    for (i in 0_u64..count) {
      let at = base + i;
      if at < end {
        set out^[at] = 1_u64;
      }
    }
  }
  return unit;
}
```

Repair by forming `let part = &out^[base..end];` before the loop, using part^.len as count and `set part^[i] = 1_u64;`. Fixed-row helpers analogously consume each row range; saturated multiplication cannot simply be relabelled checked multiplication without establishing its bounded domain.

**Complete file:line list:**

- `font/lookup_filters.wf:134`

- `layout/grid.wf:982`, `layout/grid.wf:983`

- `layout/tableborders.wf:33`, `layout/tableborders.wf:44`

- `layout/text/picks.wf:288`

- `text/normalization/decompose.wf:142`

### S-pack — Pack independent flags or position/presence into one scalar

**Count:** 5; **hot estimate:** 2. Conditions: 1: 5, 2: 0.

Five existence flags become five bits of one ior accumulator. Reach flags and a small mask fit disjoint bits of u16. A last matching position plus a seen flag becomes maximum of i+1 with zero as absent; decode after the loop and retain the original no-match default. For selector reach validation, reserve a separate invalid bit and return the original failure after scanning.

```whitefoot
fn last_nonzero(values: &[u64]) -> encoded: u64 reads(values) {
  let found = 0_u64;
  let count = values^.len;
  for (i in 0_u64..count) {
    if values^[i] != 0_u64 {
      let candidate = i +wrap 1_u64;
      set found = imax(found, candidate);
    }
  }
  return found;
}
```

The original shape assigns both a position and a Bool and fails condition 1. The repaired fragment has one admitted maximum. Since i<count<=u64_max, i+1 is representable; zero distinguishes absence without sacrificing position zero.

**Complete file:line list:**

- `css/selectors/reach.wf:263`

- `layout/tablegrid.wf:267`

- `oracle/layout/edit.wf:435`

- `oracle/page/page.wf:92`

- `style/restyle.wf:915`

### S-wide — Exact widened sum followed by one clamp

**Count:** 13; **hot estimate:** 13. Conditions: 1: 13, 2: 0.

These layout folds add bounded nonnegative i32 sizes/gaps/weights, or repetitions of one fixed-sign gap. Accumulate i32 terms as i64 with +wrap, then clamp once to the original i32 result domain; where the accumulator was already i64, replace +sat by +wrap after establishing the bound. This preserves saturation because all contributions have the same sign. Keep per-element writes and guards; inline their broad put helpers. For natural_cross, clip the loop endpoint to the lines length before removing its bounds break.

```whitefoot
fn sum_small(values: &[i32]) -> result: i32 reads(values) contract {
  requires values^.len <= 1073741824_u64;
} {
  let total = 0_i64;
  let count = values^.len;
  for (i in 0_u64..count) {
    let positive = imax(values^[i], 0_i32);
    let wide = cvt::<i32, i64>(positive);
    set total = total +wrap wide;
  }
  let capped = imin(total, 2147483647_i64);
  return cvt::<i64, i32>(capped);
}
```

The unrepaired fragment uses an i32 total and +sat on positive. With at most 2^30 terms, each <=2^31-1, the exact sum is <2^61; even two such terms per item are <2^62, within i64. These are Snowghost's actual item_ceiling=1073741824 and i32-domain contributions. tablegrid's i64 weights come from widened i32 sizes/percent units or 0/1; arbitrary external i64 weights would not justify the rewrite. Nonnegative layout invariants and helper bounds must be retained; this is not valid for mixed-sign T4 sums. No extra runtime fallback is proposed.

**Complete file:line list:**

- `layout/flex.wf:819`, `layout/flex.wf:1548`

- `layout/grid.wf:1347`, `layout/grid.wf:1373`, `layout/grid.wf:1764`

- `layout/table.wf:442`, `layout/table.wf:466`

- `layout/tablegrid.wf:227`, `layout/tablegrid.wf:372`, `layout/tablegrid.wf:397`, `layout/tablegrid.wf:472`, `layout/tablegrid.wf:485`, `layout/tablegrid.wf:763`

## Cross-cutting findings and disposition

- **Fixed in this analysis:** several saved G classifications concealed real descriptor growth or overlapping buffer transfers. shape_buffer/shape_run and sparse Paged route publication are now T1/T2 where applicable. `route_table(count)` and `sparse_routes(length)` do not establish the same physical storage invariant.
- **Fixed in this analysis:** same-index position helpers, block_at_entry’s read row, packed flag/sentinel folds, fixed-stride row ranges and bounded wide sums moved to S. Runtime stride and descriptor reads are not new gaps in this compiler revision.
- **Retained as proposals:** projected injectivity, indexed reductions, interval certificates, product carriers, finite-domain extrema and bit-slice dependence. No repository code, pin, submodule, design tree or TODO was changed; the user authorized read-only analysis and these two output files. No issue or pull request was posted.
- **Unverified:** full correctness of every producer invariant and proposed extension; exact compiler acceptance after rewrites; dynamic hotness and speedups. Broad helper summaries must not erase append/failure behavior. Saturating signed sums cannot be reassociated without their same-sign/domain argument.

## Validation and independent review

Source analysis only. The saved source bodies were compared with the checkout; the output has one unique row for each requested input coordinate/condition, and its grouped counts reconcile with the input and Markdown lists. Read-only review by a separate agent examined the complete annotation list, then focused on G/S source bodies and their directly affected helpers, rules and call graph. It found the hidden growth/overlap and source-rewrite corrections listed above. It did not independently rederive all 726 classifications. Final review covered checklist groups A, D, M, R and V (code/gate/pin/PR groups not applicable); model identity was not exposed. Counts, coordinate coverage, metadata and relevant pipeline/spec correspondence passed inspection. The reviewer’s table-format, conditional-helper example and floating-maximum domain findings were repaired and rereviewed; the final reference-measure spelling correction was checked locally. Formal extension soundness, producer invariants, example acceptance and admission forecasts remain unverified. No project gate, test suite, build, compiler invocation or performance experiment was run locally or in CI.

Input SHA-256: `87f47abbacc333f8964e33d8e7bb4c2a4e4aefab3bf876bc140875a8f2194154`.
