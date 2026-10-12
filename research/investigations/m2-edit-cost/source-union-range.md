# Saturating source union range witness

`source-union-range.wf` preserves the narrow observation for Whitefoot: the pinned
`wf-78223721f77d` front end refuses the offset store with OP-4,
`at < made.inner.len`, after a ceiling preflight excludes saturation. ENT-3
does not provide the needed affine sum relation for `+sat`. This is a
specified proof limitation, not a demonstrated compiler/specification conflict.

The renderer uses exact `+` for these logical counts and indices. Its private
source-record type invariants bound each operand by `1073741824`, so saturation
cannot occur and exact addition is defined. The owner verified the bounded
exact-addition form on the pinned front end; exact addition states the intended
operation and resolves this arithmetic obstacle. The owner will file only the
narrower `+sat` observation as a low-priority request. It does not gate increment 1.
