# G-indexed loop permission and emission at wf-6e800e9160f7

## Question and criterion

Does Whitefoot main 6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58,
specification v0.115, admit at least 16 of the same 32 complete G-indexed
loops, as written or after local helper effect/signature narrowing?
The mapping and method are those of [exp68](g-indexed-exp68.md),
[#290](g-indexed-290.md) and [#274](g-indexed-274.md).
Algorithms, passes and storage remain fixed; a direct-store rewrite is
not helper narrowing. Fewer than 16 permissions rejects the criterion;
a hard source refusal leaves unreported sites unmeasured. The release
owner's prediction is 17, compared with exp68's 17, #290's 11 and #274's 0.

The oracle is [PAR-2 at the adopted Whitefoot revision](https://github.com/Ming-Research/Whitefoot/blob/6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58/spec/kernel-spec.md#13-execution-overlap).
Permission is measured independently from emission: every permitted
call-form and copied-cell row must also be traced in `--emit-llvm` output
to its generated splitter's lane acquire, publish and join calls.
A permitted row that retains sequential lowering rejects that emission
claim without changing its source-permission verdict. No runtime overlap,
output-correctness or performance claim follows from these measurements.

## Hosted method and source compatibility

The inherited [par-count workflow](../../../../.github/workflows/par-count.yml)
builds `layout_oracle` with `--cache`, `--fragments function`, `--par` and
`--par-ledger`, preserving the revision, pin, release manifest, compiler
streams, exit code and full loop ledger. Its branch selector, release paths
and ledger artifact name now select this recount. A second compiler
invocation uses `--emit-llvm --par --par-ledger` on the same entry and cache,
without `--fragments`, which the CLI forbids with `--emit-llvm`. It preserves
the whole LLVM module, emission streams/exit and per-definition counts and
extracts for `set_coverage_bits`, `build_filters`, `mark_lookups`,
`collect_stage` and `sort_run`, including their generated helpers. Because
the layout entry uses normalization queries rather than full normalization,
`sort_run` is outside its emitted closure; a targeted invocation uses
`--function pkg::text::normalization::sort_run --emit-llvm --par --par-ledger`
on the same graph, source, pin and cache. Counts refer to call instructions,
never runtime declarations. The all-module permission ledger and this
targeted function's permission/actualization ledger remain separate evidence.

The independent existing `check` workflow runs unchanged `make check`.
Both workflows use GitHub-hosted Ubuntu 24.04. No local or self-hosted
build, test, check or timing is part of this measurement; CI status is
polled at most once every five minutes.

The [v0.110–v0.115 specification log](https://github.com/Ming-Research/Whitefoot/blob/6e800e9160f70b2f8a9aa10cab5b6d90d97bdf58/spec/log.md)
was read before the upgrade. v0.110 adds fieldless `IoError::Cancelled`
and cancellation parameters on host waits; v0.113 adds read-only shared
cancellation-state handles and makes cancellation firing a waiting call.
v0.111 adds map-reserve release, v0.112 extends range facts, v0.114 admits
the copied-cell and call-form indexed updates, and v0.115 changes canonical
scientific float spelling. Compiler overlap grouping also consumes proved
separations (#316); the ledger determines whether that changes these rows.

The renderer adaptations reuse [the matching cancellation classifier
fix](https://github.com/Ming-Research/Snowghost-wf/commit/551c21b0291656abf55014d62cb85d44f246aa54)
in `oracle/font_face/font_face.wf`:

```diff
     DeadlinePassed() => {
       return False();
     }
+    Cancelled() => {
+      return False();
+    }
```

`file_too_large` answers whether an `IoError` is `FileTooLarge`; cancellation
is a distinct host outcome, so `False()` is the specified classification.
Adding its explicit arm preserves exhaustive matching rather than hiding
an unhandled outcome. The file before this patch matches that fix's parent.
The other cancellation adaptations reuse [the upgrade's host-I/O patch](https://github.com/Ming-Research/Snowghost-wf/commit/d0cfd313ebacf1bac1010cfa248f68dfafbd87a9)
on matching files: `io_error_code` returns `0_u32` for fieldless `Cancelled`,
and its body/interface documentation now says that errors without a host
code return zero. Seven `write_once` sites and one `read_next` site in
oracle support and the six table-generator tool files pass a fresh
`cancel_never()` watch and close it after the host wait, before handling
the outcome. This satisfies the new argument/linear-handle obligations
and preserves the command-line tools' unbounded waits. It adds no polling,
deadline, cancellation source or renderer fallback.

These compatibility adaptations are separate from helper narrowing: none of
the 32 counted loop bodies or their permission inputs changes. The inherited
FN-1 unreachable-tail adaptation from #290 stays unchanged.

The initial runs on `7e1eaa3e8034894a9688a516e00266297f677ef9`, with only
the font-classifier arm applied, record the remaining compatibility refusals:

```text
./oracle/support/support.wf:327:3: error[ERR-2]: NonExhaustiveMatch
  source:   match error {
  marker:   ^^^^^^^^^^^^^
  missing_variants: [Cancelled]
```

The [initial par-count run 38001496505](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38001496505)
exited 1 before producing a loop ledger. The [initial gate run
38001496520](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38001496520)
stopped at the corresponding host-call signature change:

```text
./tools/static_atoms/static_atoms.wf:213:11: error[GRAM-11]: InvalidNamedArguments
  callee: read_next
  declared_parameters: [factory, input, destination, start, end, deadline, cancel]
```

These are the new exhaustive-match and required-argument obligations, not
a refusal of a sound natural form. The reused patches supply the correct
classification and the explicit noncancellable wait policy. The upgrade's
[hosted classifier controls, run 38000758589](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38000758589),
at `bb98d4371d0e148775e232e4d2938ddb9aec3be6` with `wf-f887e82c4611`,
exercise these identical classifier bodies: the correct mappings pass,
both missing-arm forms fail with ERR-2, and returning a nonzero code or
`True()` for cancellation is detected. This is reused classifier evidence
at v0.113, not a new runtime test of the v0.115 renderer.

## Narrowing boundary and observations for Whitefoot

No qualifying helper narrowing was found. The two font helpers already
receive their mutable primitive-array roots separately from the read-only
layout. For the remaining bodies, narrowing an effect or signature does
not remove the complete-loop blockers: sequence-selected item get/put in
the grid; shared `TableTrack` get/put after narrowing per-cell output
helpers; whole-`Col` get/put, floating maximum or old-field-dependent
contributions in columns; hidden-dominates-maximum in borders; and
key-dependent winner payloads in cascade. The direct first-pseudo,
scalar-mark, guarded exact-add and `NodeId` replacement forms have no
helper narrowing that removes their blockers. Replacing whole-record
get/put with field stores would be a direct-store rewrite, outside the
criterion. **Applied narrowing diffs: none.** The after-narrowing column
therefore uses the same measured bodies, not a hypothetical rewrite.

The copied-cell positive form in `sort_run` is this source fragment,
inside the counted loop with a bounded `class64` and independent contribution:

```whitefoot
let current = counts[class64];
let next = current +wrap 1_u64;
set counts[class64] = next;
```

A useful remaining rule boundary is `merge_edge`'s actual statement shape,
inside its bounds guard:

```whitefoot
let current = list^.inner[at];
if current < 0_i32 {
  return unit;
}
if value < 0_i32 {
  set list^.inner[at] = -1_i32;
  return unit;
}
let wider = imax(current, value);
set list^.inner[at] = wider;
```

This observes `current` in a branch as well as in `imax`, permits an
intervening write to the root, and mixes a constant mark with an operation
update. PAR-2 requires a single-use copied operand, disjoint intervening
footprints and one fixed family kind. Supporting hidden-dominates-maximum
requires a broader operator/selection rule, not helper narrowing. These
are illustrative source fragments, not separately compiled fixtures.
No renderer workaround or Whitefoot source change is made here.
