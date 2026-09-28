# Snowghost

Snowghost is a cross-platform renderer for user interfaces built with web
technology. It implements a chosen subset of the web platform: the part that
mainstream sites and the applications AI coding tools generate actually use.
It is written in [Whitefoot](https://github.com/mbbill/Whitefoot), a systems
language whose compiler proves memory safety, the absence of data races and
silent overflow, and the independence it uses to run code in parallel.

The aim is a light platform for web-built applications, with a rendering
pipeline that is parallel and incremental from end to end: a change to one
element reruns only the stages and the parts of the page it affects, and the
independent parts of every stage run on all cores. Snowghost measures itself
against Chromium and Servo on rendering performance.

The name comes from the snow ghosts of Big White, the rime-covered trees of
the mountain where Whitefoot also takes its name.

## Status

Design. Nothing renders yet; the architecture is being worked out, and its
decisions are recorded in the design tree under `design/`.

## Layout

- `design/`: the decisions Snowghost is built on, each with its reason and
  its refused alternatives, and the procedure that maintains them.
- `docs/`: the agent procedures, the completion review checklist and the list
  of known defects and follow-up work.
- `whitefoot/`: the Whitefoot language and compiler, pinned as a git
  submodule at the revision Snowghost builds with.

## Build and check

You need git, Rust stable (at least the `rust-version` in
`whitefoot/compiler/Cargo.toml`) and Python 3.

    git clone --recurse-submodules https://github.com/mbbill/Snowghost
    cd Snowghost
    make check

`make check` builds the pinned Whitefoot compiler and runs every Snowghost
check.

## License

MIT; see [LICENSE](LICENSE).
