# X8: edits the census missed, parser appends and font arrival

Run 2026-10-02/03 on Snowghost main fcb80cb plus commits 9ddcfd6 (font
census and text restricted to font groups) and 199f60a (mode `relaid`) on
worktree branch exp/x3; every build and timed run under the host lock.
Scripts ran with the run host's paths. A first round stopped midway; its
cut-point analysis and samples were reused and checked (an independent chunk
experiment agrees with them), and the gaps were filled.

**Criterion** (written before the run): an append re-lays out only what
follows, within 2 times the appended content's own cost; a font arrival
costs no more than the text preparation of the paragraphs using it.

## Method

**Append, whole remainder.** The page HTML is cut before a chosen element's
start tag and the prefix laid out, then compared with the full page's layout,
style and text: what the arrival of the rest changes in what was already laid
out. Cut points: 40 uniform per page, plus up to 12 per stratum by the layout
kind of the cut's ancestors (plain, float, table, flexgrid, inline-block,
abspos). 247 usable samples; 5 apollo11 samples skipped because the truncated
tree's structure differs.

**Append, chunks** (`chunk.py`). The page cut at c is compared with the page
cut K elements later, K about 20, 200 and 2,000: what a network-chunk-sized
append changes in the prefix. 16 uniform plus 6 per non-plain stratum per
page, 330 records. Classes: same, rigid translation (not counted as work),
and changed ("redo"); open ancestors (those containing the cut) counted
apart.

**Cost proxy.** (appended elements + redo + open ancestors) / appended
elements, each re-laid box costing one element. The cost of appended content,
T(full) − T(prefix), is linear in elements (`timing-cuts.py`, layout mode,
per-rep slope): html5 11.0 to 11.7 µs per element, ecma262 7.7 to 8.7,
apollo11 5.2 to 7.2.

**Font census.** Driver mode `fonts` counts scalars and paragraphs per font
group (`fonts.py`, `sets-*.json`).

**Font arrival timing** (driver mode `relaid`: the box tree, then only the
paragraphs of the given font groups, then lay_out):
- P_F = restricted_F − restricted_empty: text preparation of the paragraphs using font F;
- R_F = relaid_F − relaid_empty − P_F: their line breaking and placement;
- S = relaid_empty − restricted_empty: lay_out's structural cost with every paragraph emptied.

Per-rep slope of process wall time over reps, minimum over trials. A paragraph
with one run in the font is re-prepared whole.

## Results: append

**Whole remainder** (boxes in the prefix):

| page / stratum | redo, median / max | open ancestors, median / max | prefix paragraphs whose breaks changed | max rigidly translated | proxy ratio max |
|---|---|---|---|---|---|
| html5, non-table | 0 / 15 | 5 / 8 | 1 of 54 samples (1 paragraph) | 8 | 1.003 |
| html5, table (14) | median 1,447 (12 samples), max 5,117 | 6 / 7 | 5 of 14 (max 8) | 7,425 | 1.30 |
| ecma262, non-table | 1 / 2 | 10 / 15 | 0 | 1 | 1.002 |
| ecma262, table (12) | 9 / 81 | 12 / 14 | 3 of 12 (max 6) | 161 | 1.001 |
| apollo11, all (104) | 2 / 60 | 14 / 23 | 0 | 374 | 1.15 |

- 1 of 252 samples changed any prefix style (a `td` text-align, through a structural pseudo-class); 11 of 104 apollo11 samples changed one generated-content row.
- The table cases come from `table-layout: auto`: a new row changes the column widths, so every cell is re-laid.

**Chunks**, share within 2 times on the proxy:

| appended elements | other strata | table stratum |
|---|---|---|
| about 20 | 79 of 85 (max 2.55; the six are apollo11, an open chain of depth about 15 against 20 elements) | 10 of 16 (max 75.6) |
| about 200 | 82 of 82 (max 1.50) | 13 of 16 (max 8.46) |
| about 2,000 | 85 of 85 (max 1.06) | 16 of 16 (max 1.75) |

The worst case is an html5 table cut at element 103,232: 1,485 boxes re-laid
by any of the 20, 200 or 2,000 element appends, about 17 ms of re-layout for
a 0.23 ms append.

## Results: font arrival

**Census.**

| page | what uses which family |
|---|---|
| html5 (60,868 paragraphs, 59 groups) | generic sans-serif first in 62 % of paragraphs; monospace in 24.3 %; named faces small (Times 0.06 %, Essays1743 0.05 %) |
| ecma262 (57,514) | IBM Plex Serif first in groups holding 96.1 % of scalars; IBM Plex Mono 12.1 % of paragraphs, Comic Code 2.2 %, IBM Plex Sans 2.8 % |
| apollo11 (2,569) | sans-serif 84 %; the serif set (Linux Libertine and fallbacks) 0.43 % |

**Costs, large sets** (reference per-rep times: boxes / preparation /
lay_out in ms):

| page | reference | set | paragraphs | P_F | R_F | (P_F+R_F)/P_F | with S |
|---|---|---|---|---|---|---|---|
| apollo11 | 5.0 / 53.1 / 23.3 | sans-serif first | 97.0 % | 51.0 | 17.3 | 1.34 | 1.42 |
| html5 | 81.5 / 903.6 / 356.5 | sans-serif first | 96.9 % | 848.6 | 212.7 | 1.25 | 1.32 |
| html5 | | monospace first | 22.5 % | 555.1 | 169.1 | 1.30 | 1.40 |
| ecma262 | 52.2 / 845.0 / 316.8 | IBM Plex Serif anywhere | 90.3 % | 731.1 | 319.5 | 1.44 | 1.50 |

**Smaller sets** (15 to 21 reps):

| page | set | paragraphs | P_F | R_F | (P_F+R_F)/P_F | with S |
|---|---|---|---|---|---|---|
| ecma262 | IBM Plex Mono first | 12.0 % | 108.6 | 19.2 | 1.18 | 2.04 |
| ecma262 | IBM Plex Mono anywhere | 14.2 % | 172.4 | 54.4 | 1.32 | 1.86 |
| ecma262 | Comic Code first | 2.2 % | 72.9 | 22.8 | 1.31 | 2.60 |
| ecma262 | IBM Plex Sans first | 2.8 % | 83.5 | 5.7 | 1.07 | 2.19 |
| html5 | serif, Times, Essays1743 | 26 to 113 paragraphs | −2.1 to 1.7 | −8.8 to 3.6 | under noise | |

- The rare html5 sets are below the noise of about ±3 ms (expected 1.7 ms for 113 paragraphs).
- S is 4.2 ms (apollo11), 55 to 77 ms (html5) and 45 to 94 ms (ecma262); an incremental flow would not pay it whole.
- Earlier 3-rep runs showed larger R_F for the small ecma262 sets (up to 5.7 times); the 15-rep rerun does not reproduce them.

## Verdicts

1. **Append.** Met for appends of about 200 elements or more anywhere outside auto-layout tables, and when the whole remainder arrives (ratio max 1.30; the prefix changes only in its open chain plus up to 31 boxes outside tables, 116 at 2,000 elements). Not met for appends of about 20 elements (6 of 85 non-table cases over 2 times, all apollo11, and 6 of 16 table cases), nor for appends inside auto-layout tables, where the cost follows the table, not the appended content (up to 1,485 boxes for one row, about 75 times).
2. **Font arrival.** Not met as written, by a modest margin: arrival costs 1.07 to 1.44 times P_F, the excess being the re-breaking and placement of the same paragraphs; with S, 1.3 to 2.6 times. Rare web fonts cost under the noise (below about 3 ms on html5).

## Limits

- The ratio is an element-count proxy; it charges extending an open ancestor like laying a box, which probably overstates tiny appends. "Redo" is what changed; detecting cheaply that the rest did not was not measured.
- Appends are cut at element starts, not mid-text, and the parser closes the cut tree.
- Table strata have 12 to 14 samples per page; the 20-element chunks are the high-variance cases.
- The appended content's cost is a from-scratch layout, not an incremental implementation.
- Font arrival keeps whole paragraphs; run-granular re-preparation would be cheaper for mixed paragraphs (html5 monospace: 22.5 % of paragraphs, 61 % of preparation). Font loading time is not included.
