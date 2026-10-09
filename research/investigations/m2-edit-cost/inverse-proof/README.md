# Stored-field inverse with the released range rules

Question: does wf-01697d2de8a1 prove the original indirect owner writes,
carry their inverse through an owning structure without caller facts, and
express the same invariant over the renderer's actual order representation?
Reject completion if any of those obligations remains unproved, or if a
permitted loop emits no task offer. These are admission and emission probes,
not acceptance timing or semantic mutation detection.

`natural.wf` and `today.wf` are unchanged from the original
[stored-field case](https://github.com/Ming-Research/Snowghost-wf/tree/research/inverse-proof-case/research/investigations/m2-edit-cost/inverse-proof).
The first asks `apart(i, j)` to use
`targets^[order^[k].Open.block].entry_slot == k`; the second has the same
executable loop without that fact or certificate. `type-invariant.wf` moves
the relation to the owning Context and calls its writer through `forward`,
which states no fact. The small construction gives two blocks their matching
entry slots; the check after the writer observes only the resulting origins.

The renderer's EntrySequence instead keeps `payloads: SlotPages<Flow>`.
SlotPages is a recursively boxed `Vacant`/`Fork`/`Page` directory. Its accessor
`slot_read` walks a path whose depth depends on the slot and the directory's
span. A fixed `.Page.values.inner[k]` projection covers a leaf, not all Fork
paths. Neither the flat original example nor the released compiler's flat
nested-owner model establishes the required fact for this representation.

`recursive-fact.wf` reduces that remaining question to one owner and Open
payloads. `target_slot` follows the same directory path and reads the target's
stored inverse. Its range requirement asks that logical lookup to equal the
owner slot. This is a proposed proof expression, not source admitted by the
specification: RANGE-1 explicitly excludes calls from range terms. It does not
claim a compiler violation of v0.112. Enumerating finite paths, adding a
second inverse store, sorting targets, or checking the relation at run time
would not supply the requested natural proof and is not an integration.

The temporary [hosted workflow](../../../../.github/workflows/inverse-proof.yml)
collects diagnostics and exit statuses for the probe files and emits reachable
versions of the two original loops. Their generated main gives the loops two
matching target slots; the callee bodies are unchanged. Each compiler status
is read directly, outside a pipe. Probe-job success means the evidence was
collected, not that every case was admitted. Retire this workflow and move the
minimal remaining case to Whitefoot when the natural recursive fact is
specified and maintained there.

The oracle is [Whitefoot v0.112, TYPE-11 and RANGE-1 through RANGE-5](https://github.com/Ming-Research/Whitefoot/blob/01697d2de8a1349631d1a92a2659ae9f8c7ea7ad/spec/kernel-spec.md).
Results and the representation decision belong in
[SPLIT-CONTRACT.md](../SPLIT-CONTRACT.md#released-inverse-proof-and-recursive-order-storage).


Hosted [37995129991](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37995129991)
at 74ab9dd accepted the two original declarations: today reports `denied`
(condition 2), natural `permitted` (eligible; no accumulator). The reachable
natural construction was refused at the call with RANGE-3, missing `inv`.
The owning fixture first needed the actual unchanged target-length
postcondition to observe its result after `forward`; that contract is now
stated on both writer and forwarder, and the constructor then fails with TYPE-11, missing `inv`.
`filled-field.wf` isolates whether an aggregate fill exposes a field value to
a range requirement. No explicit-store rewrite is used to make this natural
constructor pass. Declaration emission is also captured independently of the
constructor diagnostic; neither is renderer parallelization evidence.

The recursive getter was refused at 56:42 with `error[RANGE-1]:
InvalidRangeClause`, reason `a range term calls a function`, and repair
`write range terms from literals, consts, integer values, measures and element
reads`. This agrees with the specified grammar; it is the remaining logical
order expression, not a reported compiler/specification contradiction.


Hosted [37996060054](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37996060054)
at 736c71d confirms the original natural declaration's permitted ledger and
`split independent map over 5 captured bindings`. Its emitted LLVM contains
`wf__par_acquire_lane(i64 96)`, publication of the split thunk and a join.
The serial control is denied condition 2 and has no task offer. These are
callee-declaration results; the generated reachable natural main still fails
RANGE-3 at its call, and the Context construction fails TYPE-11.

`filled-field.wf` is refused at 14:3 with RANGE-3 `UndischargedRangeFact`,
missing `targets^[k].entry_slot == 0_u32`. Its single element is naturally
initialized by `array_filled::<Block, 1>(value: Block(entry_slot: 0_u32))`.
OP-13 promises the runtime value, but PRE-1 makes the published contract the
proof boundary and RANGE-1 makes its generic whole-element equality inactive
for noninteger Block. The diagnostic therefore exposes a specified proof
limitation, not a demonstrated compiler violation. Explicitly storing the
field again would conceal this gap and is not used.


The aggregate-fill result is a limitation of this natural flat constructor.
It has not been established as an additional requirement of the renderer's
actual construction, whose target pools begin as empty Slots and append
records. The recursive logical-order relation is the established integration
blocker; this fixture does not widen that conclusion.
