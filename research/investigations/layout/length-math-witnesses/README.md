# Length-expression arena invariant witnesses

These temporary programs isolate the proof needed by an immutable, locally
indexed length-expression arena. A node's operands precede it, and its root
is valid. Recursive evaluation reads independent operands and needs no
runtime index checks or sequential evaluation pass.

`generic.wf` states those invariants on `LengthMath<L>`, as the proposed
representation naturally requires. `concrete.wf` changes only the wrapper
to a concrete `ComputedMath` holding `MathNode<f32>`. It is a diagnostic
control, not a selected production alternative.

## Evidence and expected result

The pinned Whitefoot release is defined by the repository's `whitefoot.pin`.
At its source revision, `spec/kernel-spec.md` section TYPE-11 states that a
type invariant is admitted only when its struct declares no generics.
The range-invariant paragraph keeps those conditions except for the relation's
form. Consequently, the generic witness is expected to be rejected with
TYPE-11 at its invariant declarations. This is a specification prediction,
not an observed compiler refusal.

RANGE-1 permits the enum-payload projections used here; their definedness
conditions each fact on the active variant. RANGE-2 and RANGE-3 describe
using those facts to discharge ordinary subscript bounds and recursive-call
requirements. The pinned conformance cases
`range1-pos-enum-payload-by-variant.wf` and
`share1-neg-frozen-range-type-invariant.wf` provide the syntax used here.
The concrete control is expected to compile and return success, but has
not been compiled or run. A failure there would need its own diagnosis.

## CI commands

Run only in CI, after downloading the compiler selected by `whitefoot.pin`
and installing the toolchain required by the ordinary project gate. From
the repository root, with `WHITEFOOTC` set to that compiler's absolute path:

```sh
mkdir -p build/research/layout/length-math-witnesses
"$WHITEFOOTC" research/investigations/layout/length-math-witnesses/generic.wf -o build/research/layout/length-math-witnesses/generic
```

Record that command's own exit status and diagnostics. It should fail for
the TYPE-11 generic-invariant restriction, not an unrelated syntax error.
Then independently run the control:

```sh
"$WHITEFOOTC" research/investigations/layout/length-math-witnesses/concrete.wf -o build/research/layout/length-math-witnesses/concrete
build/research/layout/length-math-witnesses/concrete
```

The standalone source and `-o` CLI form is documented by the pinned
Whitefoot README's compiler examples. No builds, checks or tests were run
locally when preparing these programs.

Remove this directory once the gap's disposition is settled and a production
length-math case exercises the resulting proof. Until then it records the
unverified proof question that blocks the arena implementation.
