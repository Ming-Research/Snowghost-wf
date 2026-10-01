# Known defects and follow-up work

Items the work has found and not yet done, each with its impact, the change
that would address it and when to reopen it ([AGENTS.md](../AGENTS.md#how-work-proceeds),
"Fix or record what you notice"). Remove an item in the change that resolves
it.

## Whitefoot requirements

Gaps Snowghost needs Whitefoot to close, each stated as its minimal semantic
example apart from the renderer code that exposed it
([AGENTS.md](../AGENTS.md#the-whitefoot-boundary)).

- **A write through indices the program knows are distinct cannot be
  proved disjoint.** Minimal example: a tree in an arena, each node's
  children's indices kept in its own list, built in one pass in index
  order, so every index appears in exactly one list; a counted loop over
  one level's nodes writes `results[child]` for each of their children.
  The writes never collide, but Whitefoot sees integers read from storage
  and cannot prove them distinct, so the loop cannot run in parallel. It
  keeps the style stage's cascade a sequential pass in document order
  (`design/pipeline/style.md`), and the layout builder's map from node to
  style index is the same scatter. The owner prefers a mechanism that
  works for any container (array, hash map, arena), needs no restricted
  container operations and costs nothing at run time; the candidate is an
  affine key that only its container mints, so that two places hold two
  different keys, studied in Whitefoot as its own investigation against
  monotone containers and a built-in partition. The real style stage's
  pass in document order takes 0.164 s, 26 percent of the four-worker stage,
  on ecma262 and 8 and 3 percent on html5 and apollo11
  (`research/investigations/style/DESIGN.md`, criterion 2). Reopen the
  cascade when Whitefoot settles it.

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

- **A local `slots_new::<T, N>()` clears all N slots when created.** The
  code compiled at the pin clears the whole window before any value is
  placed, though no slot past `len` is readable ([WIN-1], [OP-13]); in
  `pkg::css::selectors`'s `match_complex`, a 64-frame window per call, it
  was 21 percent of the style stage's instructions on ecma262 before the
  rule index (`research/investigations/concurrency/DESIGN.md`, "Style's
  work per element"). Whitefoot records it in its `docs/todo.md`
  (mbbill/Whitefoot#196). Change: a window created without clearing.
  Reopen when that lands, to move the pin and measure again.

## Snowghost

- **The selector oracle does not exercise the rule index, sibling
  positions or specificity.** `tests/css/selectors_oracle.py` drives
  `selector_matches`, which scans; `subject_key`, `name_hash`,
  `sibling_positions`, `selector_matches_positioned` and
  `matching_specificity` are checked only end to end, by the style stage's
  comparison with Chromium on three real pages
  (`research/investigations/style/run.sh check`), where a wrong match or
  specificity shows only as a wrong computed value. Drive
  `matching_specificity` with `sibling_positions` in the oracle, with the
  specificities Selectors Level 4's examples give, and add cases that pin
  `subject_key` against `selector_matches` (ids and classes in quirks mode,
  SVG and MathML names, duplicate attributes). Reopen now that
  `pkg::style` uses them; it is the next selector change's first step.
- **Passing sibling positions costs the scanning matcher about 13
  percent.** With the positions slice threaded through `list_matches`,
  `match_complex`, `compound_matches` and `instr_matches`, the style
  prototype's shape A, which calls `selector_matches` for every rule and
  element, takes 6.57 s against 5.77 s for two repetitions on ecma262 (wall
  time with setup included, best of three, sequential build; the run is in
  the concurrency investigation's `runs/21-shape-a-95b9073.txt`); the cause
  is not attributed. Measure where
  the time goes, and if it is the extra parameter, give the positions to
  the nth helpers another way; reopen when `selector_matches` is on a hot
  path outside the prototype.
- **Interning is timed only as a difference of whole runs.** Three runs on
  the real style stage put the interning tasks at 10 to 22 percent of the
  four-worker stage on ecma262 and html5 and under 8 percent on apollo11,
  on both sides of the 15 percent bound of `design/vocabulary.md`, and
  interning hardly speeds up with workers
  (`research/investigations/style/DESIGN.md`, criterion 2). Change: time
  interning alone with its own mode, and if it passes the bound, split each
  table by hash into partitions interned in parallel, as criterion 2
  prescribes. Reopen before the style stage is measured against another
  engine.
- **Matching costs more than the prototype's.** Matching takes 0.300,
  0.366 and 0.179 s at four workers on ecma262, html5 and apollo11, against
  0.224, 0.180 and 0.202 s for the prototype's whole shape C, with the same
  index and shape; specificity accounts for at most 13 percent of it. The
  user-agent sheet now holds 147 rules, against the prototype's display
  rules, and the cost per rule offered is not measured. Change: count the
  rules the index offers per element and the time per test, then decide.
  Reopen with the interning item.
- **Sibling positions are counted by one sequential walk of the whole
  document.** The table matching reads (`renderer/css/selectors/positions.wf`)
  shares its type counters across parents, an order the counts do not need:
  one parent's children depend only on that parent's child list. Counting
  each parent's children in a counted loop would run in parallel and, after
  a change, recount only the parents whose children changed. The walk's own
  time is not measured. Reopen when it is, or when style runs incrementally
  (`design/pipeline/style.md`).
- **Building the box tree as a walk then a decoding loop is measured on two
  pages only.** On ecma262 and html5 it made the builder and layout together
  1.08 and 1.24 times faster at four workers, short of the 1.5 sought, and
  the sequential build 34 and 21 percent slower; the owner kept it because
  what remains is under 1 percent of the four-worker pipeline
  (`design/pipeline/layout.md`), and asked that it be measured again on
  more real cases. Measure the real builder against decoding during the
  walk, sequentially and at four workers, on every real page the first
  milestone renders. Reopen when the real box tree builder exists.
- **The tokenizer copies text one code point at a time.** `bytes_push` and
  `push_codepoint` take 13 and 10 percent of html5's parse, and UTF-8
  decoding 7 (the concurrency investigation's HTML parsing section): a text
  token's bytes are decoded and pushed back singly where a run of plain
  bytes could be copied whole, which shortens parsing's chain without
  parallelism. The owner placed it after style. Reopen when parsing is the
  next sequential cost studied.

- **The user-agent sheet's rules match every namespace, and only HTML
  style elements are read.** `pkg::style::add_sheet` skips `@namespace`, so
  `ua.css`'s `@namespace` for HTML does not restrict its rules: an SVG
  `title` takes `title { display: none }` (one element of ecma262), and
  `sheet_sources` lists only `style` elements in the HTML namespace, not
  SVG's. Change: give a sheet's default namespace to the selector parser
  and read SVG style elements. Reopen when an SVG-heavy page joins the
  corpus.

- **Component walking helpers are written twice.** `pkg::css::values`
  (`tokens.wf`, `components.wf`) and `pkg::style` (`components.wf`) each
  classify components, skip whitespace, find a sibling and compare an
  identifier with a word list, because neither module can reach the
  other's private functions. Change: make one set public in
  `pkg::css::syntax`, next to the component list they read, and use it from
  both. Reopen at the next change to either module's component handling.
- **`pkg::proto::style` duplicates the rule index and traversal that
  `pkg::style` now holds.** The prototype stays because the concurrency
  investigation's measurements are reproduced with it and
  `pkg::proto::layout` builds on it; `pkg::style`'s `cascade.wf` and
  `traversal.wf` started as copies of its `index.wf` and `traversal.wf`.
  Change: retire both prototypes, or point them at `pkg::style`, when the
  layout stage is built on `pkg::style` and the concurrency investigation's
  runs no longer need reproducing.

- **No mechanical check for documents and artifacts.** `make check` does not
  refuse non-English text, personal filesystem paths or broken Markdown links
  and anchors; reviewers check them by hand (checklist A4 and D2).
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
  oracle. Impact: pages using them lose the declaration; the style stage now
  resolves colors, and the HTML Standard's user-agent sheet uses `Canvas`,
  `CanvasText` and `ThreeDFace`, whose declarations are dropped, which no
  element of the three real pages shows in its computed values. Change:
  extend `ParsedColor` and the parser, and add the suite. Reopen when a
  page in the corpus shows a system color or a Level 5 form in a mismatch.
- **`narrow_f32` predates `cvt.nearest`.** `pkg::css::color` narrows its
  channels from f64 to f32 by computing round-to-nearest-even from the
  bits, because the pin it was written against had no rounding conversion;
  the pin now has `cvt.nearest` ([OP-6]), which `pkg::css::values` uses.
  Change: replace `narrow_f32` with `cvt.nearest::<f64, f32>` and rerun
  `make oracle-css-color`. Reopen at the next change to `pkg::css::color`.
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
- **pkg::oracle::support has no signed decimal writer.** The font drivers
  print negative metrics, advances and offsets, so `pkg::oracle::font_face`
  (`put_signed_field`) and `pkg::oracle::font_shape` (`put_signed_item`)
  each carry the same sign-and-magnitude step beside support's unsigned
  `put_decimal`. Change: add a signed writer to support's interface and use
  it in both drivers. Reopen when a third driver prints signed numbers or
  support's interface next changes.
- **pkg::font reads only raw sfnt fonts for simple scripts.** WOFF and
  WOFF2 (which needs a Brotli decoder), font collections, variable fonts
  and CFF2 are refused as Unsupported; shaping covers horizontal
  left-to-right Latin, Greek and Cyrillic with HarfBuzz's default
  features, not the complex-script shapers (Arabic, Indic, Khmer,
  Myanmar, Hangul, Thai), vertical text, cmap format 14 variation
  selectors or the GSUB and GPOS lookup types outside the listed ones;
  and load_face validates only the tables shaping reads, not the outline
  tables (glyf, loca, CFF) the shell's rasterizer will read. Impact: web
  fonts, which are mostly WOFF2, and pages in other scripts cannot use
  their fonts yet. Change: a WOFF2 and Brotli leaf, outline validation
  before any font reaches the shell, and one shaper leaf per script
  family. Reopen when the first page needs a web font, a non-Latin script
  beyond Greek and Cyrillic, or the shell rasterizes.
- **load_face ignores a whole malformed GDEF, GSUB or GPOS table.** Chrome
  passes these tables to HarfBuzz unsanitized, and HarfBuzz's sanitizer
  neuters each offset it cannot follow, so the lookups that parse still
  apply. pkg::font drops the whole table instead. The two agree when the
  table is unreadable as a whole or when the neutered offset is the only
  structure a feature uses; otherwise a font with one broken lookup loses
  its other lookups here. Change: validate per lookup and ignore only the
  failing lookup, matching HarfBuzz's neutering. Reopen when a real web
  font with a partly broken layout table renders differently from Chrome.
