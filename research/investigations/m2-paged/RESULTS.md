# Paged storage comparison — 2026-10-11 UTC

Performance verdict: **reject** under the [pre-written criterion](README.md#comparison-fixed-before-measurement). Correctness gates and the deferred inverse proof are separate conditions. The complete initial comparison is retained below; focused extensions retain their own observations and machines. All six initial page/mode jobs and all six focused extension jobs completed. The longer observations resolve some ambiguous cells; eight cells remain unverified, as listed below. Further measurement is not needed to establish the rejection.

## Revisions and method

- Base and independently built base twin: `030e4dd4081c9c15699363bdfa0e57c53a7f761d`.
- Candidate and independently built candidate twin: `2c2c171911933aef499e0fb96a288643803eacd5`.
- Compiler: `wf-78223721f77d`, binary SHA-256 `5d3522d32388f5cc9596eedeea51fed8786df6b916b30103a550b0a1d5f9c99a`; Clang and LLD 22.1.8.
- Independent builds and pilot: [38096036798](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38096036798). Default compiler flags for sequential drivers; `--par` for four-worker drivers. Runtime `WF_WORKERS` is 1 or 4 respectively.
- Initial workflow revision: `ac3a2ae0d218e45eee1bde4482dab6f03a4a2eea`; extension workflow revision: `d7e0a8c3accd65d0ec9fc9e18fb015a4696127f4`. Reuse requires identical renderer, compiler pin and kit to the measured ancestor.
- All runners: GitHub-hosted Ubuntu 24.04, four exposed CPUs, Linux 6.17.0-1022-azure, glibc 2.39. Each page/mode comparison runs all four cohorts on one runner; absolute durations from different rows or phases are not cross-machine speedup evidence.
- Three interleaved rounds, cohort order reversed in round two. Initial full stages use 20 repetitions; selected extensions use 100. Initial edit cells execute each complete script once per cohort/round; extensions use five complete executions. All ordinals and non-timing counts remain checked.
- Full-stage time is `(T(repetitions) - T(0)) / repetitions`, including box construction for layout. Edit cells average all timed ordinals in a round, with `style_us` separate. Table durations are medians; ratios are medians of paired round ratios, which need not equal the ratio of the two displayed medians.
- Noise is the largest absolute twin/original deviation over both pairs and every round, with a 2% floor. Full layout above 3% outside noise rejects; full-style/edit regression outside noise rejects. Inconsistent round classifications remain unverified. Peak RSS is the maximum process high-water mark across measured rounds/repetitions, without subtracting T(0).
- Every linked run retains `machine.json`, process records and command lines, raw edit ordinals, paired round values in `summary.json`, driver/input/script/font hashes and the rendered tables. Colour-layout observations near zero are limited by the integer-microsecond clock; a criterion pass with a large noise band does not establish a precise percentage cost.

## Machines and evidence

| Phase | Page | Mode | CPU | Run |
| --- | --- | --- | --- | --- |
| matrix | ecma262 | seq | AMD EPYC 7763 64-Core Processor | [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274) |
| matrix | ecma262 | par4 | AMD EPYC 7763 64-Core Processor | [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274) |
| matrix | html5 | seq | AMD EPYC 7763 64-Core Processor | [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274) |
| matrix | html5 | par4 | INTEL(R) XEON(R) PLATINUM 8573C | [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274) |
| matrix | apollo11 | seq | AMD EPYC 7763 64-Core Processor | [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274) |
| matrix | apollo11 | par4 | AMD EPYC 7763 64-Core Processor | [38101523274](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38101523274) |
| extension | ecma262 | seq | AMD EPYC 7763 64-Core Processor | [38102566750](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38102566750) |
| extension | ecma262 | par4 | INTEL(R) XEON(R) PLATINUM 8573C | [38102204378](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38102204378) |
| extension | html5 | seq | AMD EPYC 7763 64-Core Processor | [38103117610](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38103117610) |
| extension | html5 | par4 | AMD EPYC 7763 64-Core Processor | [38102566750](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38102566750) |
| extension | apollo11 | seq | AMD EPYC 7763 64-Core Processor | [38102204378](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38102204378) |
| extension | apollo11 | par4 | AMD EPYC 9V74 80-Core Processor | [38102204378](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38102204378) |

## Complete initial comparison

### Full stages

| Page | Mode | Stage | Base ms | Candidate ms | Ratio | Noise | Verdict |
|---|---|---|---|---|---|---|---|
| ecma262 | seq | style | 1270.789 | 1273.814 | 1.0024 | 2.0% | pass |
| ecma262 | seq | layout | 1154.039 | 1195.374 | 1.0331 | 2.0% | reject |
| ecma262 | par4 | style | 683.554 | 687.813 | 1.0057 | 2.0% | pass |
| ecma262 | par4 | layout | 810.793 | 841.231 | 1.0456 | 2.0% | unverified |
| html5 | seq | style | 629.569 | 633.664 | 1.0053 | 3.2% | unverified |
| html5 | seq | layout | 1208.633 | 1233.022 | 1.0193 | 2.0% | pass |
| html5 | par4 | style | 286.391 | 289.419 | 1.0046 | 2.0% | pass |
| html5 | par4 | layout | 718.549 | 742.133 | 1.0341 | 2.0% | reject |
| apollo11 | seq | style | 138.660 | 138.393 | 0.9934 | 2.0% | pass |
| apollo11 | seq | layout | 72.348 | 71.222 | 0.9835 | 3.2% | pass |
| apollo11 | par4 | style | 73.543 | 74.665 | 1.0031 | 2.5% | pass |
| apollo11 | par4 | layout | 58.258 | 59.935 | 1.0136 | 6.0% | unverified |

### All selected edit kinds

| Page | Mode | Kind | Component | Base us | Candidate us | Ratio | Noise | Verdict |
|---|---|---|---|---|---|---|---|---|
| ecma262 | seq | word | layout | 105.80 | 107.60 | 1.0175 | 2.0% | unverified |
| ecma262 | seq | sentence | layout | 133.45 | 131.90 | 0.9854 | 2.0% | pass |
| ecma262 | seq | colour | layout | 0.05 | 0.05 | 1.0000 | 2.0% | pass |
| ecma262 | seq | colour | style | 15.00 | 14.80 | 0.9867 | 8.0% | pass |
| ecma262 | seq | fontsize | layout | 34567.95 | 37793.75 | 1.0908 | 3.2% | reject |
| ecma262 | seq | fontsize | style | 267.80 | 261.85 | 0.9778 | 2.5% | pass |
| ecma262 | seq | rootfont | layout | 215.75 | 220.85 | 0.9889 | 10.0% | pass |
| ecma262 | seq | rootfont | style | 3558.00 | 3525.50 | 0.9899 | 6.5% | pass |
| ecma262 | seq | block | layout | 88.60 | 88.00 | 0.9977 | 4.3% | pass |
| ecma262 | seq | block | style | 35.40 | 35.60 | 1.0100 | 5.1% | pass |
| ecma262 | par4 | word | layout | 186.35 | 191.50 | 1.0117 | 5.6% | pass |
| ecma262 | par4 | sentence | layout | 230.60 | 222.35 | 0.9765 | 2.0% | pass |
| ecma262 | par4 | colour | layout | 0.05 | 0.05 | 1.0000 | 100.0% | pass |
| ecma262 | par4 | colour | style | 24.50 | 23.95 | 0.9776 | 8.1% | pass |
| ecma262 | par4 | fontsize | layout | 37222.15 | 40639.30 | 1.0918 | 4.8% | unverified |
| ecma262 | par4 | fontsize | style | 366.65 | 371.95 | 1.0145 | 2.8% | unverified |
| ecma262 | par4 | rootfont | layout | 447.50 | 480.25 | 1.0277 | 24.9% | unverified |
| ecma262 | par4 | rootfont | style | 4567.90 | 5096.50 | 1.0348 | 28.2% | pass |
| ecma262 | par4 | block | layout | 143.65 | 137.05 | 0.9541 | 7.1% | pass |
| ecma262 | par4 | block | style | 53.55 | 51.30 | 0.9580 | 9.2% | pass |
| html5 | seq | word | layout | 121.28 | 122.10 | 1.0067 | 2.0% | pass |
| html5 | seq | sentence | layout | 251.25 | 251.58 | 1.0009 | 2.0% | pass |
| html5 | seq | colour | layout | 0.02 | 0.02 | 1.0000 | 50.0% | unverified |
| html5 | seq | colour | style | 34.77 | 35.15 | 1.0164 | 2.5% | pass |
| html5 | seq | fontsize | layout | 12891.90 | 13640.83 | 1.0483 | 4.9% | unverified |
| html5 | seq | fontsize | style | 94.72 | 95.28 | 1.0178 | 5.4% | pass |
| html5 | seq | rootfont | layout | 815845.82 | 814466.62 | 1.0084 | 2.0% | pass |
| html5 | seq | rootfont | style | 261966.08 | 260719.45 | 0.9951 | 2.0% | pass |
| html5 | seq | block | layout | 929.68 | 883.63 | 0.9408 | 2.0% | pass |
| html5 | seq | block | style | 379.17 | 387.40 | 1.0109 | 2.5% | pass |
| html5 | par4 | word | layout | 140.38 | 142.25 | 1.0310 | 5.6% | pass |
| html5 | par4 | sentence | layout | 230.45 | 236.00 | 1.0301 | 4.5% | pass |
| html5 | par4 | colour | layout | 0.02 | 0.03 | 1.0000 | 100.0% | pass |
| html5 | par4 | colour | style | 40.80 | 40.85 | 1.0062 | 5.0% | pass |
| html5 | par4 | fontsize | layout | 9209.92 | 9808.63 | 1.0470 | 4.0% | unverified |
| html5 | par4 | fontsize | style | 115.40 | 115.07 | 1.0065 | 2.2% | unverified |
| html5 | par4 | rootfont | layout | 452637.80 | 456868.33 | 1.0146 | 2.0% | pass |
| html5 | par4 | rootfont | style | 153056.23 | 153983.10 | 1.0036 | 2.0% | pass |
| html5 | par4 | block | layout | 563.92 | 549.37 | 0.9771 | 2.0% | pass |
| html5 | par4 | block | style | 401.63 | 394.33 | 0.9822 | 2.0% | pass |
| apollo11 | seq | word | layout | 226.38 | 228.63 | 1.0155 | 2.0% | pass |
| apollo11 | seq | sentence | layout | 314.27 | 310.05 | 0.9916 | 2.0% | pass |
| apollo11 | seq | colour | layout | 0.02 | 0.02 | nan | nan% | unverified |
| apollo11 | seq | colour | style | 28.30 | 27.87 | 0.9782 | 6.2% | unverified |
| apollo11 | seq | fontsize | layout | 491.13 | 486.58 | 0.9907 | 2.1% | pass |
| apollo11 | seq | fontsize | style | 80.77 | 80.87 | 1.0157 | 4.9% | unverified |
| apollo11 | seq | rootfont | layout | 48567.55 | 48691.42 | 1.0051 | 2.0% | pass |
| apollo11 | seq | rootfont | style | 37750.02 | 37630.57 | 0.9972 | 2.0% | pass |
| apollo11 | seq | block | layout | 14186.30 | 14554.23 | 1.0270 | 3.0% | unverified |
| apollo11 | seq | block | style | 189.87 | 192.48 | 1.0138 | 5.7% | pass |
| apollo11 | par4 | word | layout | 398.85 | 406.08 | 1.0164 | 7.7% | unverified |
| apollo11 | par4 | sentence | layout | 574.95 | 565.18 | 0.9818 | 2.0% | pass |
| apollo11 | par4 | colour | layout | 0.02 | 0.02 | nan | nan% | unverified |
| apollo11 | par4 | colour | style | 43.02 | 42.82 | 0.9833 | 17.1% | pass |
| apollo11 | par4 | fontsize | layout | 781.05 | 768.40 | 0.9814 | 4.0% | pass |
| apollo11 | par4 | fontsize | style | 118.28 | 120.43 | 1.0198 | 4.7% | pass |
| apollo11 | par4 | rootfont | layout | 38081.32 | 38204.67 | 1.0121 | 2.3% | unverified |
| apollo11 | par4 | rootfont | style | 26394.03 | 26093.20 | 0.9995 | 4.4% | pass |
| apollo11 | par4 | block | layout | 15020.85 | 15408.15 | 1.0181 | 2.0% | unverified |
| apollo11 | par4 | block | style | 268.78 | 271.43 | 0.9967 | 2.0% | unverified |

### Peak RSS

| Page | Mode | Stage/script | Base peak MiB | Base twin | Candidate peak MiB | Candidate twin |
|---|---|---|---|---|---|---|
| ecma262 | seq | style | 425.75 | 424.62 | 427.63 | 425.65 |
| ecma262 | seq | layout | 536.69 | 536.59 | 581.82 | 581.45 |
| ecma262 | seq | word | 784.32 | 782.66 | 823.51 | 828.27 |
| ecma262 | seq | sentence | 784.39 | 782.61 | 825.77 | 826.09 |
| ecma262 | seq | colour | 782.50 | 783.53 | 825.76 | 825.18 |
| ecma262 | seq | fontsize | 814.66 | 814.48 | 877.59 | 877.60 |
| ecma262 | seq | rootfont | 783.90 | 784.54 | 824.52 | 823.44 |
| ecma262 | seq | block | 784.70 | 782.72 | 824.92 | 825.27 |
| ecma262 | par4 | style | 422.93 | 422.77 | 422.70 | 420.77 |
| ecma262 | par4 | layout | 560.43 | 569.78 | 624.94 | 616.26 |
| ecma262 | par4 | word | 790.80 | 790.39 | 831.03 | 829.78 |
| ecma262 | par4 | sentence | 786.73 | 788.04 | 831.25 | 827.23 |
| ecma262 | par4 | colour | 791.32 | 786.75 | 829.05 | 826.93 |
| ecma262 | par4 | fontsize | 824.96 | 817.41 | 845.89 | 850.94 |
| ecma262 | par4 | rootfont | 790.34 | 789.48 | 832.94 | 833.02 |
| ecma262 | par4 | block | 791.79 | 789.79 | 829.07 | 833.31 |
| html5 | seq | style | 273.05 | 273.45 | 275.14 | 271.55 |
| html5 | seq | layout | 498.09 | 497.56 | 540.66 | 537.93 |
| html5 | seq | word | 652.89 | 652.73 | 694.78 | 694.50 |
| html5 | seq | sentence | 652.48 | 652.09 | 694.39 | 694.53 |
| html5 | seq | colour | 654.05 | 654.43 | 696.90 | 694.86 |
| html5 | seq | fontsize | 682.86 | 681.98 | 731.89 | 731.63 |
| html5 | seq | rootfont | 830.25 | 831.55 | 837.38 | 837.18 |
| html5 | seq | block | 652.04 | 654.24 | 695.94 | 694.20 |
| html5 | par4 | style | 270.38 | 272.36 | 271.88 | 273.85 |
| html5 | par4 | layout | 545.41 | 538.68 | 593.71 | 589.49 |
| html5 | par4 | word | 656.66 | 657.20 | 701.43 | 699.21 |
| html5 | par4 | sentence | 656.27 | 656.59 | 700.50 | 701.52 |
| html5 | par4 | colour | 656.57 | 658.07 | 698.91 | 698.53 |
| html5 | par4 | fontsize | 692.86 | 693.73 | 736.26 | 732.04 |
| html5 | par4 | rootfont | 853.00 | 852.68 | 897.88 | 916.95 |
| html5 | par4 | block | 657.16 | 658.27 | 698.64 | 699.19 |
| apollo11 | seq | style | 57.27 | 57.14 | 57.20 | 57.39 |
| apollo11 | seq | layout | 64.74 | 64.54 | 66.45 | 64.61 |
| apollo11 | seq | word | 85.73 | 83.64 | 85.96 | 87.93 |
| apollo11 | seq | sentence | 83.56 | 83.61 | 85.89 | 85.80 |
| apollo11 | seq | colour | 85.71 | 85.91 | 85.97 | 85.89 |
| apollo11 | seq | fontsize | 85.73 | 83.79 | 86.04 | 86.01 |
| apollo11 | seq | rootfont | 104.09 | 105.53 | 106.70 | 108.42 |
| apollo11 | seq | block | 95.95 | 97.98 | 101.35 | 101.55 |
| apollo11 | par4 | style | 55.57 | 55.62 | 55.54 | 55.58 |
| apollo11 | par4 | layout | 74.84 | 73.00 | 74.36 | 76.81 |
| apollo11 | par4 | word | 85.97 | 87.82 | 89.87 | 88.10 |
| apollo11 | par4 | sentence | 87.69 | 85.98 | 88.06 | 90.00 |
| apollo11 | par4 | colour | 88.00 | 85.84 | 87.98 | 87.90 |
| apollo11 | par4 | fontsize | 86.08 | 88.04 | 90.12 | 89.87 |
| apollo11 | par4 | rootfont | 109.06 | 109.28 | 112.69 | 113.32 |
| apollo11 | par4 | block | 102.24 | 100.82 | 105.64 | 104.64 |


## Focused extensions

### Full stages

| Page | Mode | Stage | Base ms | Candidate ms | Ratio | Noise | Verdict |
|---|---|---|---|---|---|---|---|
| ecma262 | par4 | layout | 779.389 | 809.134 | 1.0382 | 2.0% | reject |
| html5 | seq | style | 623.632 | 628.419 | 1.0076 | 2.0% | pass |
| apollo11 | par4 | layout | 46.679 | 48.036 | 1.0284 | 4.8% | unverified |

### All selected edit kinds

| Page | Mode | Kind | Component | Base us | Candidate us | Ratio | Noise | Verdict |
|---|---|---|---|---|---|---|---|---|
| ecma262 | seq | word | layout | 107.10 | 108.22 | 1.0144 | 2.0% | unverified |
| ecma262 | par4 | fontsize | layout | 34327.42 | 36044.98 | 1.0433 | 2.5% | unverified |
| ecma262 | par4 | fontsize | style | 351.96 | 349.96 | 0.9943 | 2.0% | pass |
| ecma262 | par4 | rootfont | layout | 389.75 | 387.05 | 0.9939 | 10.0% | pass |
| ecma262 | par4 | rootfont | style | 2839.29 | 2820.39 | 0.9836 | 4.9% | pass |
| html5 | seq | colour | layout | 0.02 | 0.02 | 1.0000 | 2.0% | pass |
| html5 | seq | colour | style | 35.21 | 35.60 | 1.0089 | 2.0% | pass |
| html5 | seq | fontsize | layout | 12491.02 | 13096.09 | 1.0583 | 2.0% | reject |
| html5 | seq | fontsize | style | 94.15 | 94.49 | 1.0041 | 2.0% | unverified |
| html5 | par4 | fontsize | layout | 11138.08 | 11583.77 | 1.0408 | 2.0% | reject |
| html5 | par4 | fontsize | style | 122.85 | 124.73 | 1.0120 | 2.0% | pass |
| apollo11 | seq | colour | layout | 0.02 | 0.02 | 1.0000 | 50.0% | pass |
| apollo11 | seq | colour | style | 31.51 | 32.03 | 1.0142 | 4.1% | unverified |
| apollo11 | seq | fontsize | layout | 526.83 | 517.48 | 0.9809 | 2.0% | pass |
| apollo11 | seq | fontsize | style | 91.28 | 90.34 | 0.9796 | 2.0% | pass |
| apollo11 | seq | block | layout | 15215.47 | 16025.83 | 1.0406 | 3.6% | reject |
| apollo11 | seq | block | style | 231.44 | 238.30 | 1.0182 | 9.4% | unverified |
| apollo11 | par4 | word | layout | 300.14 | 299.07 | 0.9984 | 2.0% | pass |
| apollo11 | par4 | colour | layout | 0.02 | 0.02 | 1.0000 | 2.0% | pass |
| apollo11 | par4 | colour | style | 37.04 | 36.52 | 0.9868 | 6.9% | pass |
| apollo11 | par4 | rootfont | layout | 31680.38 | 32178.75 | 1.0092 | 2.0% | unverified |
| apollo11 | par4 | rootfont | style | 20587.54 | 20673.97 | 1.0042 | 2.0% | pass |
| apollo11 | par4 | block | layout | 12394.31 | 12847.47 | 1.0286 | 2.4% | unverified |
| apollo11 | par4 | block | style | 253.72 | 251.35 | 0.9897 | 3.9% | pass |

### Peak RSS

| Page | Mode | Stage/script | Base peak MiB | Base twin | Candidate peak MiB | Candidate twin |
|---|---|---|---|---|---|---|
| ecma262 | seq | word | 784.57 | 784.69 | 826.70 | 827.04 |
| ecma262 | par4 | layout | 597.78 | 590.24 | 640.44 | 633.75 |
| ecma262 | par4 | fontsize | 840.39 | 848.55 | 867.50 | 860.34 |
| ecma262 | par4 | rootfont | 789.65 | 789.27 | 832.51 | 834.07 |
| html5 | seq | style | 274.42 | 273.57 | 274.29 | 276.08 |
| html5 | seq | colour | 654.62 | 654.62 | 696.76 | 696.39 |
| html5 | seq | fontsize | 682.17 | 683.22 | 733.13 | 731.58 |
| html5 | par4 | fontsize | 691.81 | 689.11 | 732.31 | 731.51 |
| apollo11 | seq | colour | 83.82 | 85.79 | 87.96 | 87.95 |
| apollo11 | seq | fontsize | 85.82 | 85.80 | 87.93 | 87.84 |
| apollo11 | seq | block | 97.89 | 97.98 | 101.60 | 99.68 |
| apollo11 | par4 | layout | 75.11 | 74.87 | 75.23 | 77.20 |
| apollo11 | par4 | word | 87.83 | 87.93 | 89.98 | 90.11 |
| apollo11 | par4 | colour | 88.09 | 86.59 | 90.25 | 90.16 |
| apollo11 | par4 | rootfont | 111.50 | 110.43 | 112.84 | 112.55 |
| apollo11 | par4 | block | 101.47 | 102.47 | 107.77 | 107.94 |


## Remaining unverified observations

After the selected longer observations, round classifications still disagree
for the following cells. They remain unverified; the confirmed rejecting cells
elsewhere determine the overall verdict.

- ecma262: sequential word layout update; four-worker fontsize layout update.
- html5: sequential fontsize style work.
- Apollo11: sequential colour and block style work; four-worker full layout,
  rootfont layout update and block layout update.

Colour-layout means are near the integer-microsecond clock's resolution even
where the numerical rule passes them. Their precise percentage cost is not
established. The allocation/access/initialization mechanism behind the storage
regressions has not been isolated. No inverse proof or parallel owner-motion
claim follows from these storage-only measurements.
