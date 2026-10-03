
## ecma262: 77 edits, 0 invalid

elements 179471, boxes 167714, contexts 11223, paragraphs (dump-derived) 35504, H 1275031

### X1 locality

| kind | n | style nodes changed | paragraphs changed | % of paragraphs (med / p90 / max) | edits with <1 % | contexts changed (min) |
|---|---:|---|---|---|---:|---|
| word | 10 | med 0 / p90 0 / max 0 | med 1 / p90 1.1 / max 2 | 0.00 / 0.00 / 0.01 | 10/10 | med 1 / p90 4.5 / max 18 |
| sentence | 10 | med 0 / p90 0 / max 0 | med 1 / p90 1 / max 1 | 0.00 / 0.00 / 0.00 | 10/10 | med 3 / p90 5.3 / max 8 |
| class | 10 | med 1.5 / p90 4.3 / max 7 | med 0 / p90 1 / max 1 | 0.00 / 0.00 / 0.00 | 10/10 | med 1 / p90 3 / max 3 |
| color | 10 | med 1 / p90 2.6 / max 8 | med 0 / p90 0 / max 0 | 0.00 / 0.00 / 0.00 | 10/10 | med 0 / p90 0 / max 0 |
| block | 10 | med 0 / p90 1 / max 1 | med 0 / p90 0 / max 0 | 0.00 / 0.00 / 0.00 | 10/10 | med 4 / p90 6 / max 6 |
| fontsize | 10 | med 14 / p90 53 / max 73 | med 3 / p90 12 / max 14 | 0.01 / 0.03 / 0.04 | 10/10 | med 3 / p90 22 / max 36 |
| custom | 14 | med 1.5 / p90 629 / max 4788 | med 0 / p90 0 / max 0 | 0.00 / 0.00 / 0.00 | 14/14 | med 0 / p90 0 / max 0 |
| rootfont | 3 | med 18 / p90 18 / max 18 | med 0 / p90 0 / max 0 | 0.00 / 0.00 / 0.00 | 3/3 | med 3 / p90 3 / max 3 |

Word edits: mean 0.003 % of paragraphs change lines, max 0.006 %; paragraphs changed per edit: med 1 / p90 1.1 / max 2; other than the edited one: med 0 / p90 0.1 / max 1

Recomputed over minimal (per edit with minimal > 0; "inf" = recomputed with empty minimal set):

| kind | unit | key | n with min>0 | ratio med / p90 / max | share of edits with ratio < 3 | recomputed with empty minimal |
|---|---|---|---:|---|---:|---:|
| word | paragraph | layout-relevant groups | 10 | 1.00 / 1.50 / 6.00 | 9/10 | 0 |
| word | paragraph | whole style | 10 | 1.00 / 1.50 / 6.00 | 9/10 | 0 |
| word | context | whole style | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| sentence | paragraph | layout-relevant groups | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| sentence | paragraph | whole style | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| sentence | context | whole style | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| class | paragraph | layout-relevant groups | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 4 |
| class | paragraph | whole style | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 5 |
| class | context | whole style | 7 | 1.00 / 1.00 / 1.00 | 7/7 | 1 |
| class | styled node | restyle subtree | 8 | 1.00 / 3.10 / 8.00 | 7/8 | 2 |
| color | paragraph | whole style | 0 | - | - | 10 |
| color | context | whole style | 0 | - | - | 10 |
| color | styled node | restyle subtree | 10 | 1.69 / 2.00 / 2.00 | 10/10 | 0 |
| block | paragraph | layout-relevant groups | 10 | 1.00 / 2.00 / 2.00 | 10/10 | 0 |
| block | paragraph | whole style | 10 | 1.00 / 2.00 / 2.00 | 10/10 | 0 |
| block | context | whole style | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| fontsize | paragraph | layout-relevant groups | 10 | 1.00 / 1.24 / 3.43 | 9/10 | 0 |
| fontsize | paragraph | whole style | 10 | 1.00 / 1.24 / 3.43 | 9/10 | 0 |
| fontsize | context | whole style | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| fontsize | styled node | restyle subtree | 10 | 1.00 / 1.00 / 1.00 | 10/10 | 0 |
| custom | paragraph | whole style | 0 | - | - | 3 |
| custom | context | whole style | 0 | - | - | 8 |
| custom | styled node | restyle subtree | 8 | 13805.46 / 116656.15 / 179471.00 | 0/8 | 6 |
| rootfont | context | whole style | 3 | 1.00 / 1.00 / 1.00 | 3/3 | 0 |
| rootfont | styled node | restyle subtree | 3 | 9970.61 / 9970.61 / 9970.61 | 0/3 | 0 |

### X3 rewrites

a absolute positions moved; b parent-relative; c context-relative; d sibling-anchored; e summary-tree node writes; f prefix-sum size writes. Edits with a height change or insertion (translation roots exist).

| subset | n | stat | a | b | c (context-rel) | d (sibling) | e (tree) | f (prefix sums) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| all qualifying | 32 | med | 193298 | 38 | 19118 | 2 | 24 | 9 |
| all qualifying | 32 | p90 | 348445 | 51 | 33006 | 3 | 40 | 21 |
| all qualifying | 32 | p99 | 355335 | 66 | 33682 | 17 | 60 | 33 |
| all qualifying | 32 | max | 355930 | 70 | 33763 | 19 | 61 | 36 |
| word | 1 | med | 354011 | 45 | 33503 | 1 | 22 | 9 |
| word | 1 | p90 | 354011 | 45 | 33503 | 1 | 22 | 9 |
| word | 1 | p99 | 354011 | 45 | 33503 | 1 | 22 | 9 |
| word | 1 | max | 354011 | 45 | 33503 | 1 | 22 | 9 |
| sentence | 8 | med | 187464 | 38 | 18536 | 1.5 | 24 | 9.5 |
| sentence | 8 | p90 | 344264 | 41 | 32757 | 2.3 | 31 | 13 |
| sentence | 8 | p99 | 354763 | 44 | 33662 | 2.9 | 34 | 14 |
| sentence | 8 | max | 355930 | 44 | 33763 | 3 | 34 | 14 |
| block | 10 | med | 136562 | 41 | 13676 | 2 | 24 | 8 |
| block | 10 | p90 | 341263 | 53 | 32490 | 3 | 27 | 10 |
| block | 10 | p99 | 348535 | 68 | 33013 | 3 | 28 | 11 |
| block | 10 | max | 349343 | 70 | 33071 | 3 | 28 | 11 |

Break-even per-write cost ratio r* = p90(c) / p90(x): d 11002.13, e 819.02, f 1602.25
  word: d 33503.00, e 1522.86, f 3722.56
  sentence: d 14242.22, e 1049.91, f 2599.77
  block: d 10829.87, e 1198.88, f 3216.79

### X16 viewport share

unit costs from the full stages (sequential drivers): style 13.19 us/node, text prep 22.8 us/paragraph, layout passes 31.9 us/context (2.13 us/box)

Cost per edit (sequential estimate, work units S,P,C), ms: 
- word: med 0.055 p90 0.169 max 0.62; with moved boxes at average cost: med 0.057 p90 35.95 max 353.6; edits over one frame: 0/10 (A), 1/10 (B)
- sentence: med 0.118 p90 0.192 max 0.28; with moved boxes at average cost: med 137.044 p90 340.26 max 355.6; edits over one frame: 0/10 (A), 8/10 (B)
- class: med 0.052 p90 0.175 max 0.21; with moved boxes at average cost: med 0.056 p90 234.39 max 304.9; edits over one frame: 0/10 (A), 3/10 (B)
- color: med 0.013 p90 0.034 max 0.11; with moved boxes at average cost: med 0.013 p90 0.03 max 0.1; edits over one frame: 0/10 (A), 0/10 (B)
- block: med 0.150 p90 0.227 max 0.23; with moved boxes at average cost: med 132.916 p90 340.56 max 348.6; edits over one frame: 0/10 (A), 9/10 (B)
- fontsize: med 0.435 p90 1.445 max 1.62; with moved boxes at average cost: med 216.540 p90 338.94 max 352.3; edits over one frame: 0/10 (A), 10/10 (B)
- custom: med 0.020 p90 8.292 max 63.14; with moved boxes at average cost: med 0.020 p90 8.29 max 63.1; edits over one frame: 1/14 (A), 1/14 (B)
- rootfont: med 0.333 p90 0.333 max 0.33; with moved boxes at average cost: med 0.333 p90 0.33 max 0.3; edits over one frame: 0/3 (A), 0/3 (B)

all edits: n=77

| window | pooled S,P,C,B med (p25-p75) | S,P,C only med | cost-weighted S,P,C med | S med | P med | C med | B med |
|---|---|---|---|---|---|---|---|
| in the viewport (+-360) | 0.003 (0.001-1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.001 |
| within 720 of the edit point | 0.006 (0.001-1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.001 |
| viewport +-720 (+-1080 of the edit point) | 0.007 (0.001-1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.002 |

per kind, median share within 720 (pooled / S,P,C only): block n=10 0.002 / 1.000; class n=10 1.000 / 1.000; color n=10 1.000 / 1.000; custom n=14 0.000 / 0.000; fontsize n=10 0.001 / 1.000; rootfont n=3 1.000 / 1.000; sentence n=10 0.001 / 1.000; word n=10 1.000 / 1.000

edits costing > 1 frame (S,P,C units at the full stages' per-unit times): n=1

| window | pooled S,P,C,B med (p25-p75) | S,P,C only med | cost-weighted S,P,C med | S med | P med | C med | B med |
|---|---|---|---|---|---|---|---|
| in the viewport (+-360) | 0.000 (0.000-0.000) | 0.000 | 0.000 | 0.000 | - | - | - |
| within 720 of the edit point | 0.000 (0.000-0.000) | 0.000 | 0.000 | 0.000 | - | - | - |
| viewport +-720 (+-1080 of the edit point) | 0.000 (0.000-0.000) | 0.000 | 0.000 | 0.000 | - | - | - |

per kind, median share within 720 (pooled / S,P,C only): custom n=1 0.000 / 0.000

edits costing > 1 frame on 4 ideal workers (cost / 4): n=0

Sensitivity to the cost threshold (window: within 720 of the edit point; median over edits):

| threshold | n edits | pooled S,P,C,B | S,P,C | cost-weighted S,P,C | p90 pooled |
|---|---:|---:|---:|---:|---:|
| all | 77 | 0.006 | 1.000 | 1.000 | 1.000 |
| 0.1 ms | 41 | 0.001 | 1.000 | 1.000 | 1.000 |
| 1 ms | 7 | 0.001 | 0.001 | 0.001 | 0.004 |
| 4.2 ms (240 Hz frame) | 3 | 0.000 | 0.000 | 0.000 | 0.001 |
| 16.7 ms (60 Hz frame) | 1 | 0.000 | 0.000 | 0.000 | 0.000 |
