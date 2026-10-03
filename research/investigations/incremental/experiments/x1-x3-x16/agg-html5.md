
## html5: 183 edits, 0 invalid

elements 117179, boxes 117165, contexts 16066, paragraphs (dump-derived) 32684, H 1152166

### X1 locality

| kind | n | style nodes changed | paragraphs changed | % of paragraphs (med / p90 / max) | edits with <1 % | contexts changed (min) |
|---|---:|---|---|---|---:|---|
| word | 30 | med 0 / p90 0 / max 0 | med 1 / p90 1 / max 1 | 0.00 / 0.00 / 0.00 | 30/30 | med 1 / p90 1 / max 1 |
| sentence | 30 | med 0 / p90 0 / max 0 | med 1 / p90 1 / max 1 | 0.00 / 0.00 / 0.00 | 30/30 | med 1 / p90 1 / max 1 |
| class | 30 | med 1 / p90 6.4 / max 29 | med 0 / p90 1 / max 13 | 0.00 / 0.00 / 0.04 | 30/30 | med 1 / p90 2.1 / max 131 |
| color | 30 | med 1 / p90 2.1 / max 22 | med 0 / p90 0 / max 0 | 0.00 / 0.00 / 0.00 | 30/30 | med 0 / p90 0 / max 0 |
| block | 30 | med 0 / p90 0 / max 0 | med 0 / p90 0 / max 0 | 0.00 / 0.00 / 0.00 | 30/30 | med 2 / p90 2 / max 2 |
| fontsize | 30 | med 8.5 / p90 44 / max 602 | med 3 / p90 6.4 / max 102 | 0.01 / 0.02 / 0.31 | 30/30 | med 1 / p90 8 / max 294 |
| rootfont | 3 | med 117179 / p90 117179 / max 117179 | med 32666 / p90 32666 / max 32666 | 99.94 / 99.94 / 99.94 | 0/3 | med 16066 / p90 16066 / max 16066 |

Word edits: mean 0.003 % of paragraphs change lines, max 0.003 %; paragraphs changed per edit: med 1 / p90 1 / max 1; other than the edited one: med 0 / p90 0 / max 0

Recomputed over minimal (per edit with minimal > 0; "inf" = recomputed with empty minimal set):

| kind | unit | key | n with min>0 | ratio med / p90 / max | share of edits with ratio < 3 | recomputed with empty minimal |
|---|---|---|---:|---|---:|---:|
| word | paragraph | layout-relevant groups | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| word | paragraph | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| word | context | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| sentence | paragraph | layout-relevant groups | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| sentence | paragraph | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| sentence | context | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| class | paragraph | layout-relevant groups | 11 | 1.00 / 2.00 / 7.38 | 10/11 | 14 |
| class | paragraph | whole style | 11 | 1.00 / 2.00 / 7.38 | 10/11 | 17 |
| class | context | whole style | 26 | 1.00 / 1.00 / 1.00 | 26/26 | 3 |
| class | styled node | restyle subtree | 29 | 1.00 / 1.00 / 6.00 | 28/29 | 1 |
| color | paragraph | whole style | 0 | - | - | 30 |
| color | context | whole style | 0 | - | - | 30 |
| color | styled node | restyle subtree | 30 | 1.00 / 1.70 / 3.00 | 29/30 | 0 |
| block | paragraph | layout-relevant groups | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| block | paragraph | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| block | context | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| fontsize | paragraph | layout-relevant groups | 30 | 1.00 / 1.00 / 43.60 | 28/30 | 0 |
| fontsize | paragraph | whole style | 30 | 1.00 / 1.00 / 43.60 | 28/30 | 0 |
| fontsize | context | whole style | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| fontsize | styled node | restyle subtree | 30 | 1.00 / 1.00 / 1.00 | 30/30 | 0 |
| rootfont | paragraph | layout-relevant groups | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 0 |
| rootfont | paragraph | whole style | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 0 |
| rootfont | context | whole style | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 0 |
| rootfont | styled node | restyle subtree | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 0 |

### X3 rewrites

a absolute positions moved; b parent-relative; c context-relative; d sibling-anchored; e summary-tree node writes; f prefix-sum size writes. Edits with a height change or insertion (translation roots exist).

| subset | n | stat | a | b | c (context-rel) | d (sibling) | e (tree) | f (prefix sums) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| all qualifying | 97 | med | 116247 | 824 | 12445 | 1 | 23 | 5 |
| all qualifying | 97 | p90 | 213032 | 2956 | 24213 | 6.4 | 48 | 11 |
| all qualifying | 97 | p99 | 236926 | 34191 | 40162 | 28774 | 205441 | 44107 |
| all qualifying | 97 | max | 236926 | 34191 | 40162 | 28777 | 205727 | 44107 |
| word | 2 | med | 210780 | 2784 | 23978 | 0 | 16 | 3.5 |
| word | 2 | p90 | 224539 | 3222 | 26016 | 0 | 18 | 3.9 |
| word | 2 | p99 | 227635 | 3320 | 26474 | 0 | 19 | 4 |
| word | 2 | max | 227979 | 3331 | 26525 | 0 | 19 | 4 |
| sentence | 16 | med | 117510 | 844 | 12658 | 0 | 20 | 4 |
| sentence | 16 | p90 | 179940 | 1908 | 19670 | 0 | 30 | 6.5 |
| sentence | 16 | p99 | 194207 | 2331 | 21687 | 0 | 36 | 9.5 |
| sentence | 16 | max | 196320 | 2400 | 21998 | 0 | 36 | 10 |
| block | 30 | med | 132942 | 1174 | 14700 | 1 | 20 | 3.5 |
| block | 30 | p90 | 212865 | 2935 | 24182 | 1 | 28 | 7.2 |
| block | 30 | p99 | 221143 | 3155 | 25319 | 1 | 41 | 10 |
| block | 30 | max | 224029 | 3219 | 25705 | 1 | 41 | 10 |

Break-even per-write cost ratio r* = p90(c) / p90(x): d 3783.34, e 508.68, f 2123.98
  word: d 26015.70, e 1406.25, f 6670.69
  sentence: d 19670.50, e 644.93, f 3026.23
  block: d 24181.60, e 851.46, f 3358.56

### X16 viewport share

unit costs from the full stages (sequential drivers): style 15.76 us/node, text prep 28.8 us/paragraph, layout passes 19.4 us/context (2.66 us/box)

Cost per edit (sequential estimate, work units S,P,C), ms: 
- word: med 0.048 p90 0.048 max 0.05; with moved boxes at average cost: med 0.048 p90 0.06 max 298.7; edits over one frame: 0/30 (A), 2/30 (B)
- sentence: med 0.048 p90 0.048 max 0.05; with moved boxes at average cost: med 52.448 p90 216.86 max 258.9; edits over one frame: 0/30 (A), 15/30 (B)
- class: med 0.067 p90 0.224 max 2.93; with moved boxes at average cost: med 57.606 p90 279.26 max 294.6; edits over one frame: 0/30 (A), 16/30 (B)
- color: med 0.016 p90 0.033 max 0.35; with moved boxes at average cost: med 0.016 p90 0.03 max 0.3; edits over one frame: 0/30 (A), 0/30 (B)
- block: med 0.068 p90 0.068 max 0.07; with moved boxes at average cost: med 180.005 p90 280.64 max 294.1; edits over one frame: 0/30 (A), 30/30 (B)
- fontsize: med 0.336 p90 1.675 max 12.44; with moved boxes at average cost: med 47.554 p90 234.36 max 269.5; edits over one frame: 0/30 (A), 29/30 (B)
- rootfont: med 3098.729 p90 3098.729 max 3098.73; with moved boxes at average cost: med 3410.476 p90 3410.48 max 3410.5; edits over one frame: 3/3 (A), 3/3 (B)

all edits: n=183

| window | pooled S,P,C,B med (p25-p75) | S,P,C only med | cost-weighted S,P,C med | S med | P med | C med | B med |
|---|---|---|---|---|---|---|---|
| in the viewport (+-360) | 0.009 (0.001-1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.001 |
| within 720 of the edit point | 0.017 (0.001-1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.002 |
| viewport +-720 (+-1080 of the edit point) | 0.025 (0.002-1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.002 |

per kind, median share within 720 (pooled / S,P,C only): block n=30 0.001 / 1.000; class n=30 0.004 / 1.000; color n=30 1.000 / 1.000; fontsize n=30 0.006 / 1.000; rootfont n=3 0.001 / 0.001; sentence n=30 0.044 / 1.000; word n=30 1.000 / 1.000

edits costing > 1 frame (S,P,C units at the full stages' per-unit times): n=3

| window | pooled S,P,C,B med (p25-p75) | S,P,C only med | cost-weighted S,P,C med | S med | P med | C med | B med |
|---|---|---|---|---|---|---|---|
| in the viewport (+-360) | 0.001 (0.000-0.001) | 0.001 | 0.000 | 0.001 | 0.000 | 0.000 | 0.001 |
| within 720 of the edit point | 0.001 (0.001-0.001) | 0.001 | 0.001 | 0.001 | 0.001 | 0.000 | 0.001 |
| viewport +-720 (+-1080 of the edit point) | 0.001 (0.001-0.002) | 0.001 | 0.001 | 0.002 | 0.001 | 0.000 | 0.001 |

per kind, median share within 720 (pooled / S,P,C only): rootfont n=3 0.001 / 0.001

edits costing > 1 frame on 4 ideal workers (cost / 4): n=3

| window | pooled S,P,C,B med (p25-p75) | S,P,C only med | cost-weighted S,P,C med | S med | P med | C med | B med |
|---|---|---|---|---|---|---|---|
| in the viewport (+-360) | 0.001 (0.000-0.001) | 0.001 | 0.000 | 0.001 | 0.000 | 0.000 | 0.001 |
| within 720 of the edit point | 0.001 (0.001-0.001) | 0.001 | 0.001 | 0.001 | 0.001 | 0.000 | 0.001 |
| viewport +-720 (+-1080 of the edit point) | 0.001 (0.001-0.002) | 0.001 | 0.001 | 0.002 | 0.001 | 0.000 | 0.001 |

per kind, median share within 720 (pooled / S,P,C only): rootfont n=3 0.001 / 0.001

Sensitivity to the cost threshold (window: within 720 of the edit point; median over edits):

| threshold | n edits | pooled S,P,C,B | S,P,C | cost-weighted S,P,C | p90 pooled |
|---|---:|---:|---:|---:|---:|
| all | 183 | 0.017 | 1.000 | 1.000 | 1.000 |
| 0.1 ms | 43 | 0.004 | 1.000 | 1.000 | 0.219 |
| 1 ms | 8 | 0.002 | 0.140 | 0.146 | 0.083 |
| 4.2 ms (240 Hz frame) | 5 | 0.002 | 0.002 | 0.002 | 0.162 |
| 16.7 ms (60 Hz frame) | 3 | 0.001 | 0.001 | 0.001 | 0.002 |
