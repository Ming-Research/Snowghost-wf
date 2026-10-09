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
