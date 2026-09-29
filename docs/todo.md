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

- **No rounding conversion between float formats.** [OP-6]'s `cvt`
  from f64 to f32 is defined only for a value exactly representable in
  f32, and no operation rounds. `pkg::css::color` therefore narrows its
  channels by IEEE 754 round-to-nearest-even computed from the bits
  (`narrow_f32`, flushing results below f32's normal range to zero). A
  minimal example: `let x = fdiv.strict(136.0_f64, 255.0_f64);` has no
  total conversion to the nearest f32. Change: a total rounding conversion
  for float destinations. Reopen when Whitefoot adds one; then replace
  `narrow_f32`.

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
- **`bytes_push` (`html/tokenizer/buffers.wf`) leaves cell unchanged, rather
  than proving it, when a push would cross `ceiling`.** `text_ceiling` (3 *
  2^30) and `attribute_ceiling` (2^30) are sized from `next_token`'s own
  `source^.len <= 2^30` requirement and this module's worst-case per-source-byte
  expansion (a NUL becoming three-byte U+FFFD; no attribute without consuming
  a source byte), so no legitimate caller reaches ceiling and the guard is
  dead on every input the module accepts. Proving that mechanically needs a
  loop-position invariant (current output length vs. source position
  consumed) in every `scan_*` state that pushes text or attributes
  (`data_state.wf`, `text_states.wf`, `script_data.wf`, `comments.wf`,
  `doctype.wf`, `tags.wf`), tying each state's own advancement to the
  3x/1x bound above; `bytes_push` and its `push_byte`/`push_codepoint`/
  `push_attribute` callers already carry the exact `requires`/`ensures`
  pair such a proof would need (drafted and reverted; the reachable half,
  within `bytes_push` itself, checks). Add it if a stress input, fuzz run or
  future state addition raises real doubt that the sizing argument still
  holds, or when another finding forces the same loop-invariant work anyway.
- **Processing instructions are not parsed.** The HTML standard now parses
  `<?target data?>` into processing instruction nodes (WPT's
  `processing-instructions.dat`, 124 cases), while the tokenizer's oracle,
  html5lib-tests' frozen tokenizer suite, still reads `<?` as a bogus
  comment. The tree oracle excludes that file and four `<?` cases in other
  files. Support needs a token and a
  node variant in `pkg::html::tokenizer` and `pkg::dom`, the serializer's
  `<?target data?>` form, and the tokenizer cases that expect a comment
  marked as superseded. Reopen when a target site uses processing
  instructions or the tokenizer oracle moves to a suite that has them.
- **An option's contents are not cloned into `selectedcontent`.** The
  standard clones the selected option into a customizable select's
  `selectedcontent` element from the option element's insertion and
  selectedness steps, not from tree construction, so
  `pkg::html::tree_builder` does not do it; the tree oracle excludes the
  four `webkit02.dat` cases that observe it. Change: implement the element
  behaviour where DOM insertion steps live. Reopen when form controls are
  rendered.
- **pkg::css::color covers CSS Color Module Level 4 only.** System colors,
  `color-mix()`, `light-dark()`, relative color syntax, `calc()` in
  channels and the Level 5 spaces (`device-cmyk()`, `@color-profile`
  spaces) parse as Invalid, and `color_functions_5.json` is not in the
  oracle. Impact: pages using them lose the declaration. Change: extend
  `ParsedColor` and the parser, and add the suite. Reopen when the style
  system resolves colors, or a page in the corpus uses one.
- **pkg::text::normalization has NFC and NFD only.** NFKC and NFKD, and
  their NormalizationTest.txt invariants, are not implemented: IDNA needs
  NFC only. Change: add the compatibility decompositions to the generated
  tables and two NormalizationForm variants. Reopen when a consumer needs a
  compatibility form.
- **pkg::url computes no origin or search parameters and encodes queries
  as UTF-8 only.** The record has no origin (blob: URLs and opaque origins
  need modelling) and no application/x-www-form-urlencoded parsing, and a
  document's non-UTF-8 encoding does not reach the query's
  percent-encoding; WPT's origin and searchParams fields are not compared.
  Change: add an origin function and a search-parameter parser, and an
  encoding argument once text decoding exists. Reopen when fetch or
  same-origin checks need an origin, or a legacy-encoded page is loaded.
- **Punycode encoding is quadratic in the worst case.**
  `pkg::text::idna`'s encoder follows RFC 3492's reference structure: it
  scans the whole label once per distinct non-ASCII code point, so a label
  of n strictly ascending distinct code points costs O(n^2). With
  VerifyDnsLength false a label has no length limit, so a hostile URL can
  reach it. Change: sort the label's non-ASCII code points once and walk
  them in order. Reopen when URL parsing runs on untrusted input at scale,
  or a profile shows it.
