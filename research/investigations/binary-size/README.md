# Snowghost binary size against the 10 MB limit

Status: measured 2026-10-12; the open choices are proposed as the design tree's
`design/scope/binary-size.md` and need the owner's approval (decision card on
the status board, item sg-target-binary-size).

## Question

The owner set a hard limit on 2026-10-12: the Snowghost engine binary stays
within 10 MB. No engine binary exists yet. The renderer is a set of Whitefoot
modules (`renderer/modules.wfg`) that `whitefootc` links into one executable
per entry, and the shell is a separate Rust program (`design/processes.md`).
This investigation asks:

1. What can the limit measure today, and which of those measurements is the
   best stand-in for the engine binary until one exists?
2. How close is Snowghost to 10 MB with that stand-in, and how much do the
   build flags (`--par`, the compiler cache with per-function fragments) and
   stripping change the number?
3. Do the numbers differ by platform enough to change which platform the
   limit is judged on?

The proposal under test is the one `make binary-size-check` implements: the
full-pipeline driver `layout_oracle`, built with `--par` and left unstripped,
measured on the Linux x86-64 gate. It is rejected as a stand-in if another
driver or build of the same pipeline is larger than it by more than the
margin below it leaves under the limit on the same platform, since then the
check could pass while a larger build of the same code would fail; or if the
Linux and macOS builds of it differ by more than the unused margin to the
limit.

## Method

The temporary workflow `.github/workflows/binary-size-measure.yml` (removed
after the run below; it is in the branch history at `52e7649`) ran on GitHub-hosted `ubuntu-24.04` and
`macos-15` (arm64), with the gate's own toolchain setup and the compiler
release `whitefoot.pin` names. Nothing ran on the owner's MacBook. For each
operating system it builds, from a cold runner:

- `layout_oracle`, `style_oracle`, `proto_style` and `proto_layout`, each
  sequential and with `--par`, with `--cache build/whitefoot-cache
  --fragments function` as the Makefile builds;
- `layout_oracle --par` again without the cache and fragments flags;
- a copy of `layout_oracle --par` after `strip` (`strip -x` on macOS).

`layout_oracle` and `style_oracle` are the oracle drivers over the shared page
pipeline (`pkg::oracle::page`); `proto_style` and `proto_layout` are the
earlier prototypes. The other entries in `renderer/modules.wfg` are unit
oracles and generators of single modules, not the pipeline, so they are not
measured.

The size is the file's byte count (`wc -c`). Each row is one binary, printed
as a table line and appended to the job summary.

## Results

Whitefoot compiler release: `wf-d837678c6905`; Snowghost revision: `52e7649`;
workflow run: [38240825791](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38240825791),
2026-10-12. Limit: 10 485 760 bytes (10 MiB) or 10 000 000 bytes (10 MB), see
the open choices.

| os | entry | flags | bytes |
|---|---|---|---|
| Linux-x86_64 | layout_oracle | seq | 2 975 160 |
| Linux-x86_64 | layout_oracle | par | 4 475 416 |
| Linux-x86_64 | layout_oracle | par, no cache | 3 124 592 |
| Linux-x86_64 | layout_oracle | par, stripped | 3 998 256 |
| Linux-x86_64 | style_oracle | seq | 2 181 688 |
| Linux-x86_64 | style_oracle | par | 3 169 576 |
| Linux-x86_64 | proto_style | seq | 797 352 |
| Linux-x86_64 | proto_style | par | 891 688 |
| Linux-x86_64 | proto_layout | seq | 840 904 |
| Linux-x86_64 | proto_layout | par | 923 576 |
| Darwin-arm64 | layout_oracle | seq | 1 731 328 |
| Darwin-arm64 | layout_oracle | par | 2 338 968 |
| Darwin-arm64 | layout_oracle | par, no cache | 2 820 712 |
| Darwin-arm64 | layout_oracle | par, stripped | 2 302 880 |
| Darwin-arm64 | style_oracle | seq | 1 138 592 |
| Darwin-arm64 | style_oracle | par | 1 399 760 |
| Darwin-arm64 | proto_style | seq | 578 064 |
| Darwin-arm64 | proto_style | par | 615 648 |
| Darwin-arm64 | proto_layout | seq | 628 768 |
| Darwin-arm64 | proto_layout | par | 683 552 |

The gate's own `make binary-size-check` on the same revision printed
4 475 456 bytes for `layout_oracle --par` on Linux, 40 bytes more than the
measure job's build. The cause was not examined; no conclusion below
depends on 40 bytes.

What the numbers show, for these drivers at this revision:

- `--par` is larger than sequential for every driver on both platforms; for
  `layout_oracle` by 50 % on Linux (4 475 416 against 2 975 160) and 35 % on
  macOS (2 338 968 against 1 731 328).
- `layout_oracle --par` is the largest binary measured on each platform, so
  the proposal is not rejected by the first criterion: no other driver or
  build of the pipeline is larger.
- The cache flags (`--cache --fragments function`) move the size in opposite
  directions: on Linux the build with them is 43 % larger than without
  (4 475 416 against 3 124 592), on macOS 17 % smaller (2 338 968 against
  2 820 712). Why is not known; the gate measures the build as the Makefile
  makes it, with the flags.
- Stripping removes 477 160 bytes (10.7 %) on Linux and 36 088 bytes (1.5 %)
  on macOS.
- The Linux build is 1.91 times the macOS build (4 475 416 against
  2 338 968). The difference, 2 136 448 bytes, is smaller than the margin
  the Linux build leaves under the limit (6 010 344 bytes under 10 MiB,
  5 524 584 under 10 MB), so the proposal is not rejected by the second
  criterion either, and gating Linux, the larger of the two, is the stricter
  choice.
- The largest binary, `layout_oracle --par` on Linux, uses 42.7 % of 10 MiB
  (44.8 % of 10 MB).

This measures only the renderer drivers. It is no measurement of the shell,
and the pipeline stages still to be written (paint, script, image decoding in
the pipeline) will add code, so the margin today is not the margin at the
first engine binary.

## Open choices for the owner

Each is a decision of `design/scope/binary-size.md`, proposed there and
approved on one decision card; the check follows the proposal and changes if
the owner rules otherwise.

1. Renderer only, or renderer plus shell. The limit can cover the Whitefoot
   renderer binary alone or the whole engine as installed, which adds the
   Rust shell with its libraries (Skia among them, `design/processes.md`).
   The check measures the renderer alone; it cannot measure the shell until
   one exists.
2. MB or MiB. The proposal and the Makefile's constant are 10 000 000 bytes
   (10 MB read decimally). If the owner meant 10 MiB (10 485 760 bytes), the
   limit is 4.6 % looser.
3. Which platform. CI gates the Linux x86-64 build only. macOS arm64 or
   another target could be larger; the measurement above shows by how much.
4. Stripped or not. The check measures the binary as linked. A shipped
   binary is normally stripped, which the stripped row shows the size of; the
   limit could be judged on either.
5. Which binary until a real engine binary exists. The candidates are the
   drivers above, in the sequential or `--par` build; the check uses
   `layout_oracle --par`. The measurement decides whether that is the largest
   candidate. Once an engine binary exists, the check measures it and this
   choice closes.
