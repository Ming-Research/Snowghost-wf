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
collects diagnostics and exit statuses for all four files and emits reachable
versions of the two original loops. Their generated main gives the loops two
matching target slots; the callee bodies are unchanged. Each compiler status
is read directly, outside a pipe. Probe-job success means the evidence was
collected, not that every case was admitted. Retire this workflow and move the
minimal remaining case to Whitefoot when the natural recursive fact is
specified and maintained there.

The oracle is [Whitefoot v0.112, TYPE-11 and RANGE-1 through RANGE-5](https://github.com/Ming-Research/Whitefoot/blob/01697d2de8a1349631d1a92a2659ae9f8c7ea7ad/spec/kernel-spec.md).
Results and the representation decision belong in
[SPLIT-CONTRACT.md](../SPLIT-CONTRACT.md#released-inverse-proof-and-recursive-order-storage).
