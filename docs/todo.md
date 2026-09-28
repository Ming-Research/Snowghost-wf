# Known defects and follow-up work

Items the work has found and not yet done, each with its impact, the change
that would address it and when to reopen it ([AGENTS.md](../AGENTS.md#how-work-proceeds),
"Fix or record what you notice"). Remove an item in the change that resolves
it.

## Whitefoot requirements

Gaps Snowghost needs Whitefoot to close, each stated as its minimal semantic
example apart from the renderer code that exposed it
([AGENTS.md](../AGENTS.md#the-whitefoot-boundary)).

- **A file named by bytes cannot be opened through a symbolic link.**
  `std::fs::open_directory` and `std::fs::open_file` open one component with
  `O_NOFOLLOW`, and `std::fs::open_read`, which follows links, takes a
  `RelativePath` that only `relative_path` of an argument's `HostString`
  forms. A program given a directory `d` that must open `d/n.png` for names
  `n` read from a file therefore fails when a component of `d` is a link:
  `open_directory(root: cwd, name: "build")` fails with host error 20
  (`ENOTDIR`) and no std call reaches the file. Impact: `png_oracle check`
  refuses its `DIR` in a worktree whose `build` is a link to another
  checkout's build directory, so `make oracle-png` fails there; a `DIR`
  spelling that reaches the same directory without a link works. Change: a
  std function that forms a `RelativePath` from a byte range, or a component
  open that follows links. Reopen when oracle runs from such worktrees are
  needed.

## Snowghost

- **No mechanical check for documents and artifacts.** `make check` does not
  refuse non-English text, personal filesystem paths or broken Markdown links
  and anchors; completion reviewers check them by hand (checklist A4 and D2).
  Whitefoot's `make static` stages `repository-invariants` and `guidance` are
  the models. Add the equivalent when the documents grow enough that a missed
  link or leaked path costs review time, or when one first reaches a pull
  request.
- **CI rebuilds the Whitefoot compiler on every push.** A `make check` run
  takes about two and a half minutes, most of it the compiler build. Cache
  the built compiler keyed by the `whitefoot/` pin when the gate's run time
  starts to slow down work, or when the pin moves often enough that the
  build dominates.
- **pkg::css::color covers CSS Color Module Level 4 only.** System colors,
  `color-mix()`, `light-dark()`, relative color syntax, `calc()` in
  channels and the Level 5 spaces (`device-cmyk()`, `@color-profile`
  spaces) parse as Invalid, and `color_functions_5.json` is not in the
  oracle. Impact: pages using them lose the declaration. Change: extend
  `ParsedColor` and the parser, and add the suite. Reopen when the style
  system resolves colors, or a page in the corpus uses one.
