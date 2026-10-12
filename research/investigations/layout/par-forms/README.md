# Witnesses for six independent layout loop forms

Board item `sg-par2-forms-wait` lists six loop forms in `renderer/layout/`
whose iterations are independent but whose natural spelling the counted-loop
parallel permission ([PAR-2]) of the pinned Whitefoot refuses. Whitefoot
collects them under `sg-par2-layout-forms`. This directory gives Whitefoot one
minimal, compilable witness per form, each with a variant that must stay
refused and a `main` that checks the result in index order.

Question: for each form, does the pinned compiler (`whitefoot.pin`,
wf-d837678c6905, specification v0.129) refuse the natural spelling, and with
which reason; and once Whitefoot closes the gap, is the natural spelling
admitted while the overlapping or dependent variant stays refused?

A form is a real gap only if the natural witness is refused today. If CI
permits a natural witness on the pinned compiler, the form needs no Whitefoot
change and Snowghost should rewrite its loops instead; that result rejects the
form as a Whitefoot requirement. Form 3 is handled that way already (below).

The oracle is the specification at the pinned commit:
[PAR-2, RANGE-1 to RANGE-5, REF-4, OP-10, WIN-2](https://github.com/Ming-Research/Whitefoot/blob/d837678c69057a7ca79be8fa0bd1598af51647b6/spec/kernel-spec.md).

## How the witnesses are built

- Each witness function, the one whose loop is under test, holds exactly one
  counted loop, so Whitefoot's `loop_permission.rs` helpers (`permitted`,
  `denied`, which take the only loop of a named function) apply unchanged.
  Helpers and `main` may hold other loops; they are not under test.
- Forms 1 and 2 state the disjointness the writer knows as a range
  requirement and ask for it with an empty `apart(i, j)` certificate
  ([RANGE-5]), as Whitefoot's own certified-scatter cases do. Today a refused
  certificate is a hard error, so such a witness does not compile at all. The
  workflow therefore also builds a *serial control* of each: the same source
  with the `apart` clause removed, whose `main` runs today and pins the
  semantics, and whose ledger shows the loop's verdict without a certificate.
- Form 1 guards its range formation with `if first <= end` and
  `if end <= items^.len`. A range fact cannot discharge a range-reference
  formation: the range judgment selects only subscript-bound, integer-domain
  and conversion-domain goals, not [REF-4]'s formation goal
  (`compiler/src/semantic/range_judgment/selection.rs` at the pin). Form 2
  guards its subscripts the same way, matching the renderer's style.
- [FORM-4] admits no comments, so each witness cites its real instance in its
  `doc` entries.

The temporary workflow
[`par-forms.yml`](../../../../.github/workflows/par-forms.yml) runs on every
push to `research/layout-par-witnesses`. For every witness and every serial
control it records `whitefootc --check --par-ledger` output and exit status,
builds the program sequentially and with `--par --par-ledger`, runs each
`main` that built, and uploads everything as the `par-forms` artifact with a
`summary.txt` table. Exit statuses are read outside any pipe. The job fails
only when a `main` that built exits nonzero; a refused witness is evidence,
not a failure.

## The forms

Verdicts marked TBD are filled in from the first CI run.

### Form 1: intervals whose endpoints are data

- Real instance: `renderer/layout/flex.wf`, `lay_out_flex`. Its line loops
  hand each line's run `lines.inner[l].first..lines.inner[l].end` of the
  ordered items to `flex_resolve`, `flex_align_main` and `flex_align_cross`.
  `flex_build_lines` makes the lines from consecutive items, so they do not
  overlap.
- Natural spelling: [form1-natural.wf](form1-natural.wf), `align_lines`.
  Each iteration passes the line's run `&items^[first..end]` to a helper that
  writes it. `requires ordered`: for lines a < b, `lines^[a].end <=
  lines^[b].first`. The loop carries `apart(i, j)`.
- Today: TBD. Expected a [RANGE-5] hard error at the certificate, because a
  call through a reference argument naming a run leaves a certificate
  unproved; PAR-2's proved range references accept only endpoints `s*i+b`.
  The serial control's ledger verdict: TBD.
- After the fix: `align_lines` permitted. The fix places a run argument whose
  endpoints the certificate proves disjoint across iterations, or extends
  proved range references to such endpoints.
- Must stay refused: [form1-overlap.wf](form1-overlap.wf). Its requirement
  `sorted` orders only the runs' starts, so a run may reach into the next and
  two iterations may write one item; its `main` runs `0..3` and `2..5`, which
  share item 2. The certificate must fail with [RANGE-5].

### Form 2: a variable number of outputs per iteration, in iteration order

- Real instances: `renderer/layout/inline.wf`, `finish_lines`, appends each
  line's pending fragments to the paragraph's fragments, line by line;
  `renderer/layout/table.wf`, `measure_cells`, appends one item for each cell
  that has a child.
- Natural spelling: [form2-natural.wf](form2-natural.wf), `place_lines`.
  Each line's output slots `first..end` are known (a prefix sum of the
  counts), and an inner loop writes `out^[slot]` for each of them.
  `requires placed`: for lines a < b, `spans^[a].end <= spans^[b].first`. The
  loop carries `apart(i, j)`. This is the offset form both projects use in
  their sketches; the append-per-iteration spelling the renderer has today is
  sequential by construction.
- Today: TBD. Whitefoot expects this may already hold with the existing
  certificate. If CI permits it, form 2 needs no Whitefoot change, and
  Snowghost's rewrite is to compute each line's count and offset first.
- After the fix: `place_lines` permitted.
- Must stay refused: [form2-overlap.wf](form2-overlap.wf). Its requirement
  `sorted` orders only the lines' first slots, so one line's output may run
  into the next; its `main` has both lines write `out` slot 2. The
  certificate must fail with [RANGE-5].

### Form 3: indirect writes through an index table without repeats

No witness: the pinned language already admits the natural spelling, so this
is not a PAR-2 gap. Whitefoot's own runnable conformance cases at the pin,
`range5-pos-children-fresh-values` and
`range5-pos-scatter-through-left-inverse`, certify exactly this form: a
requirement `forall nodup(a, b) when a != b, kids^[a] < results^.len: kids^[a] != kids^[b]` and an
empty `apart(i, j)` admit `set results^[kids^[k]] = value`.

How Snowghost rewrites a real instance, `renderer/layout/table.wf`,
`lay_out_table`, whose item loops write each item's child
`context^.children.inner[item.child]` and the per-child lists `forced`,
`finals_width`, `finals_height`, `finals_dx` and `finals_dy`:

1. Write each target element with a `set` instead of `put_i32`, which takes
   the whole list and so cannot be placed by a certificate.
2. State that no two items name one child, as a range postcondition of the
   function that builds the items (`measure_cells`), carried to the loop.
3. Add an empty `apart(i, j)` to the loop.

The open part is step 2: the items' children come from `context^.cells`,
which the box tree builder fills, so the no-repeat fact must be established
where cells are made and carried to `measure_cells`. That is a fact-transport
question of the kind `sg-inverse-proof-gap` tracks, not a permission rule.
`prepare_table`'s `kinds` loop may need even less: it writes the constant 1
at each cell's child, which reads as PAR-2's constant-mark indexed family, a
family admitted without any distinctness, once written as `set` instead of
`put_i32`. This is a reading of PAR-2, not yet checked by the compiler.

### Form 4: several accumulators, or the fields of one record

- Real instance: `renderer/layout/update.wf`, `sum_counts`: four `+sat`
  counters over the children's `UpdateCounts`.
- Natural spellings: [form4-natural.wf](form4-natural.wf). `sum_scalars`
  keeps three scalar `+sat` accumulators; `sum_fields` accumulates the three
  fields of one record. Each accumulator's contribution reads no
  accumulator.
- Today: TBD. Expected `sum_scalars` denied by condition 1, `the body carries
  3 accumulators`; `sum_fields` denied by condition 1 or 2 (a field write of a
  record declared outside the loop is no whole-place accumulator write).
- After the fix: both permitted, each accumulator or field recombined under
  its own operation.
- Must stay refused: [form4-dependent.wf](form4-dependent.wf). `entries` (or
  `total.entries`) adds the running `contexts` total, so its contribution
  reads another accumulator's partial value; `main` checks the index-order
  value 10, which another order or grouping would not give.
- Out of scope: `sum_counts` also folds a nested record through a pure call,
  `add_boundary_visits`. A fold through a callee is refused by condition 1
  for a different reason (the operation is not one of [OP-1]'s associative
  operations) and is not part of this form.

### Form 5: one unconditional append per iteration into reserved capacity

- Real instance: `renderer/layout/inline.wf`, `finish_lines`: its pending
  loop appends every finished fragment of a line to the paragraph's
  fragments.
- Natural spelling: [form5-natural.wf](form5-natural.wf), `emit_fragments`.
  The caller reserves room (`requires out^.inner.len + pending^.len <=
  out^.inner.cap`); each iteration `place_back`s one fragment; the header
  invariant `filled: out^.inner.len == base + k` is the proof `place_back`'s
  requirement needs anyway.
- Today: TBD. Expected denied by condition 2: `place_back` writes the
  window's length and append slot, as Whitefoot's
  `par2-neg-affine-element-append` records.
- After the fix: permitted. The invariant states that iteration k fills slot
  `base + k`, an affine element map, and the length after the loop is
  `base + count`.
- Must stay refused: [form5-dependent.wf](form5-dependent.wf). Each iteration
  still appends exactly one fragment, but reads the fragment the previous
  iteration appended to place its own after it, so iteration k needs
  iteration k - 1's write.

### Form 6: no truncate operation on a window

This is a standard-library gap, not a permission rule.

- Real instances: the clears at the start of `break_lines` and
  `finish_lines` (`renderer/layout/inline.wf`), `lay_out_context`
  (`renderer/layout/box.wf`) and `clear_column_map`
  (`renderer/layout/flow.wf`). Each empties a `Box<Slots<T>>` window with a
  counted loop of `take_back` guarded by a `break`.
- Natural spelling: [form6-natural.wf](form6-natural.wf),
  `truncate(window: &lines^.inner, length: kept)`. It does not compile on
  the pinned compiler, which has no such operation; its check status records
  that.
- Today's spelling: [form6-today.wf](form6-today.wf), the pop loop, which
  compiles and whose `main` checks the same result.
- Missing operation: a prelude window operation beside `take_back` [OP-10].
  The two existing alternatives are no substitute: `split_off` moves the
  tail into a second window the caller must allocate with room for it and
  then release, and `std::collections::vector`'s `grow_vector_truncate`
  works on `GrowVector`, not on the `Box<Slots<T>>` windows layout keeps, and
  is itself a `take_back` loop.
- Proposed contract, admitting the shapes `take_back` admits:

  ```
  fn truncate<W>(window: &W, length: u64) -> result: unit writes(window.last), writes(window.len) contract {
    requires length <= window^.len;
    ensures window^.len == length;
    ensures window^.cap == entry(window)^.cap;
  };
  ```

  It releases every element at index `length` and above, in descending index
  order as successive `take_back` calls would, and leaves every element below
  `length` unchanged; the range judgment places it as it places `take_back`
  [RANGE-2]. Its row is `take_back`'s, which [WIN-2] already defines to cover
  every slot successive `take_back` calls reach. An element type whose
  release is not compiler-derived (a linear type) is refused, as such a
  window cannot be truncated without consuming each element.

## Results

TBD: the first CI run's `summary.txt`, each ledger line for the witness
functions, and the dispositions above.
