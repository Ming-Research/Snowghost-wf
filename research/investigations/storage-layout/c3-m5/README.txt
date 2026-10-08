C3 for Whitefoot's built-in Paged<T> on the owner's M5 Air (2026-10-07)
=====================================================================

Measured while the 14900K runner was out of service; the owner approved
timing on the Air under Whitefoot's host lock (run-check.pl, labels
sg-c3-html5-seq, sg-c3-ecma262-seq, sg-c3-html5-par4). Air results; not
comparable with the 14900K's.

Machine: Apple M5 MacBook Air, 10 cores, 24 GB, macOS.
Drivers: layout_oracle, macOS arm64, built on GitHub-hosted macos-15
runners by research/timing-pages's darwin-drivers workflow, run
37710808694 (--cache --fragments function; seq and --par). Each
<name>.txt here gives the build's commit, pin and SHA-256 prefix:
  pages    8d5fab0f1586 (hand-written two-level pages, wf-0b7f5c5b9854);
           also timed as "twin", the noise control
  paged    ee58302d1f9e (built-in Paged port, context-wide pools,
           wf-exp-496186df5346)
  hf       3c47f784462b (the same source, header-first Paged,
           wf-exp-f1971c00269a)
  nodes    0ac400ed673b (like-for-like: one Paged per existing store,
           pools on Slots, wf-exp-496186df5346)
  nodeshf  3abffd812bb4 (the same source, wf-exp-f1971c00269a)
  main     02855399257b (main, reference)
Inputs: the fonts the Makefile's SYSTEM_FONTS names (47 files) and the
ecma262 and html5 pages at their pinned SHA-256s, packed by the same run's
data job.

Method (c3.py): every driver runs once unmeasured; then three rounds, each
running every build once in BUILDS order for every page, mode and lane.
Per-run time = (T(REPS) - T(0)) / REPS, with boxes at 30 and layout at 10
repetitions, seq or WF_WORKERS=4. Each JSON line is one measurement
(round, page, mode, lane, build, zero = T(0), full = T(REPS), per); the
SUMMARY lists the best round per cell. Wall times: html5 seq 178 s,
ecma262 seq 208 s, html5 par4 145 s, with 60 s between runs. Round 3 is
about 10% slower throughout, consistent with thermal throttling; the
summary takes the best round.
