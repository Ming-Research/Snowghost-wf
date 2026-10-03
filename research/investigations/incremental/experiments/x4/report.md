# X4: do a paragraph's line breaks hold over a range of widths?

Run 2026-10-03 on Snowghost main fcb80cb plus commit 30e62a4 (worktree branch
exp/x2: in dump mode the layout driver takes the viewport width), every build
and run under the host lock. Scripts ran with the run host's paths.

**Criterion** (written before the run): width-keyed memoization pays if more
than half of the paragraphs keep their breaks across a 10 px resize;
otherwise container-width edits get parallelism only.

**Verdict: met on all three pages.**

## Method

- **Driver.** `layout_oracle` built from 30e62a4 (404 s, exit 0).
- **Sweep.** `sweep.sh` dumps each page at 18 viewport widths: 1100, 1150, 1200, 1230, 1250, 1260, 1270, 1275, 1279, 1280, 1281, 1285, 1290, 1300, 1310, 1330, 1360, 1400, around a base of 1280. Pages: html5 (117,179 elements), ecma262 (179,471), apollo11 (11,845), with their sheets.
- **Width checks.** The 1280 dump of each page is byte-identical to the older driver's default dump; the `html` box reads 1270 and 1100 wide in the 1270 and 1100 dumps; results differ across widths.
- **Analysis** (`analyze.py`, output `analysis-PAGE.txt`). A paragraph is the nearest block-level ancestor of its text nodes. Its signature is the fragment rectangles of its text nodes (keyed by node ordinal) and of its inline elements. It holds at a width when the keys match and, per key, the fragment count matches and the fragment widths agree within 0.02 px; a change of breaks changes a count or a width. The matching tolerates whitespace nodes that collapse at a line end.
- **Counts.** All paragraphs; multi-line paragraphs; paragraphs whose own block width changed; and fragment-weighted, a proxy for text work.

## Results

Percent of paragraphs that hold at viewport −10 / +10 px:

| page (paragraphs, multi-line) | all | multi-line | container changed | fragment-weighted |
|---|---|---|---|---|
| html5 (32,684, 6,124) | 95.0 / 95.1 | 76.7 / 76.5 | 92.9 / 93.0 | 86.3 / 87.3 |
| ecma262 (30,307, 3,473) | 96.9 / 96.8 | 77.1 / 75.3 | 96.6 / 96.5 | 93.0 / 92.5 |
| apollo11 (1,185, 658) | 86.7 / 85.5 | 76.1 / 73.9 | 76.6 / 74.6 | 58.5 / 59.9 |

For apollo11, fragment-weighted over container-changed paragraphs only, the
figure is 53.7 / 55.3 %, the lowest under any reading.

- On html5 and apollo11 the paragraph's block changes by the full 10 px (20,945 and 650 paragraphs; 92.5 and 75.8 % hold). On ecma262 the content column is two thirds of the viewport, so 27,162 paragraphs change by 6.7 px; 96.8 % hold.
- Fall-off with the shrink (all paragraphs / multi-line):

| delta | html5 | ecma262 | apollo11 |
|---|---|---|---|
| −1 | 99.4 / 97.0 | 99.6 / 96.9 | 98.6 / 97.4 |
| −5 | 97.3 / 87.2 | 98.3 / 87.6 | 91.4 / 84.5 |
| −10 | 95.0 / 76.7 | 96.9 / 77.1 | 86.7 / 76.1 |
| −20 | 91.0 / 58.2 | 94.1 / 58.2 | 79.3 / 63.4 |
| −50 | 84.0 / 31.6 | 89.1 / 28.2 | 69.1 / 45.3 |
| −180 | 78.4 / 22.2 | 80.9 / 7.1 | 64.4 / 37.7 |

- The grow side is within 2 points of the shrink side. About 0.5 % of paragraphs change their breaks per pixel.

**What a memo could save.** Per-rep stage times from X8's timing runs:

| page | boxes | text preparation | lay_out | lay_out share of the three |
|---|---|---|---|---|
| html5 | 81.5 ms | 903.6 ms | 356.5 ms | 26.6 % |
| ecma262 | 52.2 ms | 845.0 ms | 316.8 ms | 26.1 % |
| apollo11 | 5.0 ms | 53.1 ms | 23.3 ms | 28.6 % |

A resize repeats neither box construction nor text preparation, so the
saving is a fraction of a quarter to a third of the three stages. Line
breaking was not separated from the rest of lay_out.

## Limits

- Paragraphs, not time. Multi-line paragraphs carry the saving; they are 19 % (html5), 11 % (ecma262) and 56 % (apollo11) of the paragraphs.
- One base against one other width. A memo needs the hold interval, which the breaker would have to produce (slack against the next word, room to shrink); its cost was not measured.
- Only the viewport varies; an edit inside the page changes the available width by any amount.
- Snowghost's layout matches Chromium at 1280; it was not compared at the other widths.
- Justified text would fail the same-width test; none of these pages justifies body text.
