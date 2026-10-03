# X12: the cost of recording reads and validating versions

## Question and criterion (written before the run, DESIGN.md Experiments row X12)

A no-change frame under 0.5 ms; recorded reads at context grain within 5 percent of the full build, or 3.3 (recorded reads / dynamic dependency tracing) is out. The decisive unknown was the per-edge recording cost: the budget's arithmetic assumed 100 ns to 1 us per recorded edge and about ten edges per unit.

## Method

One Whitefoot program, `wfroot/x12/x12.wf` (built seq and with `--par`; ~7 s per build, correctness below). It is a synthetic stand-in, not an instrumented copy of the layout or style stage: each unit performs 10 reads of other units' values at hashed positions, which is the "about ten edges per unit" shape of the budget. Units: the real counts of the three pages (contexts and paragraphs from the budget table; elements from `treestats.txt`):

| page | elements | contexts | paragraphs |
|---|---:|---:|---:|
| html5 | 117,179 | 13,843 | 60,868 |
| ecma262 | 179,471 | 10,217 | 57,514 |
| apollo11 | 11,845 | 1,113 | 2,569 |

Programs and tests (argument 1):
- 5 `plain`: per unit, 10 hashed reads, summed. This is "the same work without recording".
- 6 `append-id+ver` (`record_all`/`record_append`): the same 10 reads, and each read also loads the source's version and appends (source id u32, version u64) to the unit's own 16-slot log, skipping an id equal to the previous one, with a per-unit count. This is a realistic recorder (version at read time, dedupe, bounds-checked append), not a bare store.
- 7 `flat-ids`: older lower bound, ids only into a fixed window (kept from the earlier round).
- 8 `validate-dense-edges`: no-change frame over the recorded logs in unit order: for every recorded edge compare the source's current version with the recorded one.
- 9 `memo-lookup+edges`: no-change frame that walks memo keys: each unit's key is hashed and looked up in an open-addressing table (2x capacity, linear probing, 12 B/slot), then the entry's recorded edges are validated.
- 10 `memo-lookup-only`: the key lookup and one version compare per entry (a Salsa-style "verified at" check).
- 1 `scan`: dense version array, compare against a stored copy (earlier round; each frame also changes one entry, the cost of a true no-change frame is the same scan).
- 2-4 `tree`: subtree-max tick maintenance and find-from-root on the real parent arrays (earlier round).

Timing: per repetition = (T(REPS) - T(0)) / REPS, best of 3 process runs (`RUNS=3`, REPS calibrated for 0.5 s; `bench.py`), every run under one `run-check.pl` lock (`lockrun.sh`), workers via `WF_WORKERS`. Raw lines: `scan.raw`, `tree.raw`, `record.raw`, `validate.raw`, `ksweep.raw`, `big.raw`; derived numbers: `analysis.txt` (from `analyze.py`).

Correctness: the validation tests with `change=1` (each frame bumps one source version and restores it afterwards) return mismatch totals that equal an independent Python re-implementation of the hash, the dedupe and the dependents count (`ref.py`): n=1000, 300 frames: 3018 for tests 8 and 9 and Python alike; n=5000: 3009 alike. With `change=0` both return 0 (no false positives). Test 10 returns 300 (one per frame), as designed. Tree finds return the changed node every time (`wrong` = 0).

Denominators ("the full build") are from the earlier round's measured stage times, `efficiency.txt` (style+layout, from `research/investigations/layout/runs/time-parts.txt` and `style/runs/level-cascade-time-after.txt`): html5 3.414 s sequential and 1.308 s at four workers, ecma262 3.726 s and 1.513 s, apollo11 1.100 s and 0.326 s; layout alone at four workers 0.590 s, 0.587 s, 0.044 s. The budget's own figure for html5 is about 0.8 s.

Reused from the stopped round: `util.py`, `efficiency.py` were not rerun; reused `.parents` files, `treestats.txt`, `efficiency.txt` (denominators), the program's tests 1-4 and `bench.py`'s timing method. The earlier x12 binaries were rebuilt from the extended source.

## Results

### A. Per-edge recording cost (k = 10 edges per unit; `record.raw`)

Time of one pass over all units of the grain, sequential, in microseconds:

| page | grain | units | edges | plain | append-id+ver | delta | all-in ns/edge |
|---|---|---:|---:|---:|---:|---:|---:|
| html5 | contexts | 13,843 | 138,430 | 478 | 489 | 11 | 3.5 |
| html5 | paragraphs | 60,868 | 608,680 | 2,142 | 2,344 | 203 | 3.9 |
| ecma262 | contexts | 10,217 | 102,170 | 359 | 364 | 5 | 3.6 |
| ecma262 | paragraphs | 57,514 | 575,140 | 2,025 | 2,207 | 182 | 3.8 |
| apollo11 | contexts | 1,113 | 11,130 | 39.2 | 39.1 | -0.1 | 3.5 |
| apollo11 | paragraphs | 2,569 | 25,690 | 90.1 | 88.9 | -1.2 | 3.5 |

The cost of recording is below measurement noise as a difference (0 to 0.33 ns per edge; a sweep over k, `ksweep.raw`, gave deltas of 477, 232, 258 and 78 us for k = 1, 4, 10, 16 on html5 paragraphs, not monotone, so run-to-run noise is on the order of 200 us at this size). The robust figure is the all-in cost of the whole recording pass, hash, read, version load and append together: **3.5 to 3.9 ns per edge**, an upper bound on what recording adds, since a real stage pays the reads anyway. That is 25 to 250 times below the recalled 100 ns to 1 us.

Cache sensitivity (`big.raw`, same code at unit counts beyond this program's page sizes; this host has 2 MiB L2 per core and a 260 MiB shared L3, so DRAM misses are not exercised):

| units | plain us (ns/edge) | append us (ns/edge) |
|---:|---:|---:|
| 200,000 | 7,227 (3.6) | 10,512 (5.3) |
| 1,000,000 | 39,779 (4.0) | 104,117 (10.4) |
| 3,000,000 | 162,121 (5.4) | 424,126 (14.1) |

At 3 million units (logs of 576 MB) all-in recording is 14 ns per edge; the delta over plain grows to 9 ns per edge as the logs and the version array fall out of L2. The real pages need at most 60,868 units (about 12 MB of logs).

Share of the full build (all-in sequential recording pass, recorded serially; the compiler did not split `record_all` at `--par`: the per-unit log windows are slices the independence check cannot separate (`PAR denied ... overlaps`), so the pass costs the same at 4 workers, `record.raw` par-4 rows):

| page | context grain: us, % of 4-worker style+layout | paragraph grain: us, % of 4-worker style+layout | both grains |
|---|---|---|---:|
| html5 | 497, 0.038% | 2,327, 0.178% | 0.22% |
| ecma262 | 365, 0.024% | 2,179, 0.144% | 0.17% |
| apollo11 | 39, 0.012% | 90, 0.028% | 0.04% |

Against the sequential full build the shares are 4 times smaller; against layout alone at four workers (html5 0.590 s) they are 0.084% (contexts) and 0.394% (paragraphs).

Break-even: 5 percent of the 4-worker style+layout is reached at 1,336 edges per context on html5 (2,076 ecma262, 4,159 apollo11) and at 279 edges per paragraph on html5 (343, 1,831), at the all-in constants above. For comparison, the recalled constants at 10 edges per unit give, against the 4-worker style+layout of html5, 1.1 percent (100 ns) to 11 percent (1 us) at context grain and 4.7 to 47 percent at paragraph grain; the measured constant removes the dependence on which end is true.

### B. The no-change frame (microseconds, sequential / four workers)

Dense version array scan (test 1, `scan.raw`): html5 elements 44.4 / 22.3, paragraphs 19.5 / 11.5, contexts 4.4 / 4.6; ecma262 elements 82.5 / 29.2, paragraphs 18.8 / 11.6, contexts 3.4 / 3.3; apollo11 elements 3.7, paragraphs 0.8, contexts 0.3. All three grains of html5 together: 68 us sequential. The budget's "about 1 ms" is 15 to 25 times pessimistic here (0.4 ns per entry).

Push-based alternative, a subtree-max tick over the owned tree (tests 2-4, `tree.raw`): a change rewrites its ancestors' ticks in 27 ns (html5, mean depth 5.3), 42 ns (ecma262, 9.8), 39 ns (apollo11, 15.4). Finding the changed node from the root by scanning children for the first newer tick costs 2.0 us on html5 for a random node (body has 3,545 children; 4.2 us at the worst node found by `treestats.py`), 0.28 us on ecma262, 0.15 us on apollo11. A no-change frame is then one load of the root's tick; that single load was not timed separately.

Validating recorded reads (`validate.raw`; k = 10, one source changed per frame and restored; a `change=0` run on html5 paragraphs gave the same time, 745 vs 713 us and 2,576 vs 2,575 us, so nothing was hoisted):

| page, grain | dense edges in unit order (seq / 4 workers) | memo-key walk with edges (seq / 4) | memo-key lookup only (seq / 4) |
|---|---:|---:|---:|
| html5 contexts | 139 / 59 | 361 / 435 | 133 / 118 |
| html5 paragraphs | 713 / 258 | 2,575 / 2,917 | 753 / 729 |
| ecma262 contexts | 98 / 49 | 236 / 295 | 62 / 61 |
| ecma262 paragraphs | 687 / 247 | 2,322 / 2,639 | 698 / 675 |
| apollo11 contexts | 9.9 / 10.4 | 18.8 / 25.9 | 4.1 / 3.1 |
| apollo11 paragraphs | 23.1 / 13.0 | 46.1 / 63.4 | 9.6 / 7.9 |

Per recorded edge, validation costs 1.2 ns in unit order and 4.2 ns through the memo walk; a memo lookup alone costs 9.6 to 12.4 ns per unit. The memo walks did not speed up at 4 workers (the compiler split only the inner edge loop), and validation cost grows with the number of units, not the number of changes.

## Verdict

- **Criterion 1, no-change frame under 0.5 ms: holds for the dense designs, fails for the memo-key walk at paragraph grain.** A dense version-array scan is 0.0003 to 0.082 ms for every grain on every page (html5 all grains 0.068 ms), and a tick at the root is a single load. Validating recorded edges densely is 0.14 ms at context grain and 0.71 ms at paragraph grain sequentially (0.26 ms at four workers). Walking memo keys with edge validation costs 0.36 ms at context grain and 2.3 to 2.6 ms at paragraph grain, and the key lookup alone costs 0.70 to 0.75 ms at paragraph grain: over the criterion. A no-change frame therefore has to be a dense version or tick check (push-based), not a per-unit memo lookup, at paragraph grain.
- **Criterion 2, recorded reads at context grain within 5 percent of the full build: holds by two orders of magnitude on this model.** Context grain costs 0.012 to 0.038 percent of the 4-worker style+layout build (0.5 ms of 1.3 s on html5); paragraph grain 0.03 to 0.18 percent. The per-edge cost is 3.5 to 3.9 ns all-in, not 100 ns to 1 us; the 5 percent line is reached only at 279 or more edges per paragraph or 1,336 or more per context. On this evidence 3.3 is not out on cost grounds, and the "uncertain, decided by X12" status can move to "affordable at context grain; what remains is the edge count per unit".

## Limits

- The program is synthetic: recording sits in a loop of hashed reads, not in the real layout or style stage. Edges per unit (10) is the budget's assumption, not measured on the stages; the break-even edge counts above are the way to read the result if the real count differs. A cheap next step is to count the actual far reads of layout (floats across blocks, counters, absolute containing blocks) per context.
- Per-edge deltas of recording over plain are inside the noise (±200 us on 2 ms); the reported cost is the all-in pass, an upper bound on the added work. The recorder does not include a reverse index (source to dependents) or a log reclaim sweep; the validation tests scan all logs, which is the cost when no reverse index exists, and a push-based dirty set would avoid even that.
- The working sets of the real pages (at most 12 MB of logs) are L2- to L3-resident here. The host has a 260 MiB L3; DRAM latency is not exercised. At 3 million units the all-in cost rose to 14 ns per edge, still below the recalled range.
- Recording is serial in this program (the compiler cannot split windowed log writes at `--par`), so the percentages above are against the four-worker build as if recording stayed serial; recording per context inside a parallel stage would divide this.
- Sequential numbers are best of 3 on a shared four-core host under the host lock; apollo11 cases with very small times (under 40 us) are noise-level.
- The memo table is a hand-rolled open-addressing table with linear probing and a keyed hash; a different table or key layout changes the 9.6 to 12.4 ns per lookup.
- The tick tree numbers come from the earlier round; its find-from-root assumes children scanned in order, which is the 2 us worst case on html5's flat body.

## What it means for the tree

- 3.3 (recorded reads at context grain) is affordable on cost: replace the 100 ns to 1 us constant in the budget with 3.5 to 3.9 ns all-in measured (14 ns when logs exceed the cache), which turns the 2 to 17 percent estimate into about 0.04 percent at context grain.
- The no-change-frame constants of the budget are confirmed pessimistic for dense scans (68 us, not 1 ms for html5) and optimistic for memo-key walks (2.3 to 2.6 ms at paragraph grain with edges). 3.1's near-free no-change frame holds only with dense versions or push-based ticks; it fails if validation walks memo keys per paragraph.
- The open quantity is the number of recorded edges per unit on the real stages (break-even 279 per paragraph, 1,336 per context on html5), not the per-edge constant.
