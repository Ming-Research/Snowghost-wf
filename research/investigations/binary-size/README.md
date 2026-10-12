# Snowghost binary size against the 10 MB limit

Status: draft. The numbers are placeholders until the measure workflow has
run; the open choices need the owner's answers (decision cards on the status
board, item sg-target-binary-size).

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
before the pull request is ready) runs on GitHub-hosted `ubuntu-24.04` and
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

Whitefoot compiler release: `<release>`; Snowghost revision: `<commit>`;
workflow run: `<link>`. Limit: 10 485 760 bytes (10 MiB) or 10 000 000 bytes
(10 MB), see the open choices.

| os | entry | flags | bytes |
|---|---|---|---|
| Linux-x86_64 | layout_oracle | seq | TBD |
| Linux-x86_64 | layout_oracle | par | TBD (the gate printed 4 475 392 on the gate run) |
| Linux-x86_64 | layout_oracle | par, no cache | TBD |
| Linux-x86_64 | layout_oracle | par, stripped | TBD |
| Linux-x86_64 | style_oracle | seq | TBD |
| Linux-x86_64 | style_oracle | par | TBD |
| Linux-x86_64 | proto_style | seq | TBD |
| Linux-x86_64 | proto_style | par | TBD |
| Linux-x86_64 | proto_layout | seq | TBD |
| Linux-x86_64 | proto_layout | par | TBD |
| Darwin-arm64 | layout_oracle | seq | TBD |
| Darwin-arm64 | layout_oracle | par | TBD |
| Darwin-arm64 | layout_oracle | par, no cache | TBD |
| Darwin-arm64 | layout_oracle | par, stripped | TBD |
| Darwin-arm64 | style_oracle | seq | TBD |
| Darwin-arm64 | style_oracle | par | TBD |
| Darwin-arm64 | proto_style | seq | TBD |
| Darwin-arm64 | proto_style | par | TBD |
| Darwin-arm64 | proto_layout | seq | TBD |
| Darwin-arm64 | proto_layout | par | TBD |

What the numbers show, to fill in once they exist: whether `--par` or
sequential is larger for each driver; whether `layout_oracle` is the largest
of the full-pipeline drivers on each platform; how much the cache flags and
stripping change `layout_oracle --par`; the margin to the limit on each
platform.

This measures only the renderer drivers. It is no measurement of the shell,
and the pipeline stages still to be written (paint, script, image decoding in
the pipeline) will add code, so the margin today is not the margin at the
first engine binary.

## Open choices for the owner

Each is a decision card; the check keeps its current form until they are
answered.

1. Renderer only, or renderer plus shell. The limit can cover the Whitefoot
   renderer binary alone or the whole engine as installed, which adds the
   Rust shell with its libraries (Skia among them, `design/processes.md`).
   The check measures the renderer alone; it cannot measure the shell until
   one exists.
2. MB or MiB. The Makefile's constant is 10 485 760 bytes (10 MiB). If the
   owner meant 10 000 000 bytes, the limit is 4.6 % tighter.
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
