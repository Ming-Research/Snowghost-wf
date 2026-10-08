C3 for Whitefoot's built-in Paged<T> on the owner's i9-14900K (2026-10-08)
=========================================================================

Confirms on the 14900K the Air measurement in ../c3-m5/. Run 37725144848
of the time-14900k workflow on research/timing-pages (head 0f907b6),
self-hosted runner 14900k, Linux 6.8.0 x86_64, 32 processors.

Builds (commit, Whitefoot pin); each file's header repeats the commit, the
compiler hash and the seq/par driver SHA-256 prefixes:
  pages    8d5fab0f1586 (hand-written two-level pages, wf-0b7f5c5b9854)
  twin     the same drivers as pages, timed under a second name as the
           noise control
  paged    ee58302d1f9e (built-in Paged port, context-wide pools,
           wf-exp-496186df5346)
  hf       3c47f784462b (the same source, header-first Paged,
           wf-exp-f1971c00269a)
  nodes    0ac400ed673b (like-for-like: one Paged per existing store,
           pools on Slots, wf-exp-496186df5346)
  nodeshf  3abffd812bb4 (the same source, wf-exp-f1971c00269a)
  main     02855399257b (main, reference)

Files:
  full-layout-<build>-<round>.txt
      layout/run.sh's full-build table for one build in one round: per page
      (ecma262, html5), mode (boxes, text, layout) and lane (seq, par-4),
      T(0), T(REPS) and per-run = (T(REPS) - T(0)) / REPS. Rounds 1-3 are
      interleaved: each round runs every build once in the order above
      before the next round starts. Compare builds within a round or by
      their best round.
  perf-stat-<build>.txt
      perf stat of one boxes run (html5, seq, 20 repetitions): task-clock,
      page faults, elapsed, user and sys time. The runner's kernel exposes
      no hardware counters, so instructions, cycles and cache misses read
      "not supported".
  perf-boxes-<build>.txt, perf-boxes-children-<build>.txt
      perf record of the same boxes run, reported by self time and with
      children (inclusive time) respectively.

The perf files are single runs taken after the interleaved rounds, outside
them; they explain where time goes and carry no timing comparison of their
own. No perf data was taken for twin or main.
