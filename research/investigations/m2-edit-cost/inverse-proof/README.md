# Stored-field inverse proof

Question: can the pinned checker use a target's stored `entry_slot` as a
left inverse of an enum payload's target index, to certify independent
suffix-origin writes? Acceptance of `natural.wf` would refute the suspected
formation gap; acceptance of `today.wf` isolates it from the executable body.

- `natural.wf` states `targets^[order^[k].Open.block].entry_slot == k`
  in `requires forall inv(...)` and asks for independence with `apart(i, j)`.
  Its projected places use the specification's GRAM-5 spelling. RANGE-1 at
  the pinned revision admits only integer elements and no selection below
  an element, so this program is expected to be refused.
- `today.wf` removes only that requirement and certificate. Its same counted
  loop is permitted without a proof of independence; the indirect writes
  remain serial. Neither file executes a fixture: `--check` checks the
  function declaration even though `main` does not call it.
- [The temporary workflow](../../../../.github/workflows/inverse-proof.yml)
  runs on pushes to `research/inverse-proof-case` on `ubuntu-24.04`. It uses
  `make compiler` to download and verify the release in `whitefoot.pin`,
  runs `whitefootc --check` on both files, prints every diagnostic and exit
  status, and uploads them as `inverse-proof-diagnostics`. The job requires
  acceptance of `today.wf` and a RANGE-1 refusal of `natural.wf`. Remove the
  workflow when the gap is closed and the case is maintained in Whitefoot.

This reduces `translate_reference_owner_suffix` / `translate_reference_payload`
in [reference.wf](../../../../renderer/layout/reference.wf) to one owner's
direct `Open(block: u32)` siblings and one `Block.normal_y: i32` write.
`entry_slot: u32`, the enum payload, index widening and saturating origin
addition retain the renderer's types and spelling. A flat order array
indexed by stable entry slot removes the paged sequence and AVL traversal;
neither establishes the target-index inverse. The suffix range here is a
minimal contiguous subset of those slots, not a claim that AVL order equals
slot order in the renderer.

For a fixed owner, equal target indices imply equal stored `entry_slot`,
hence equal `k`: distinct iterations cannot collide. The origin write must
preserve the fact about the separate `entry_slot` field. No extra inverse
array, sorting, runtime uniqueness check or renderer change is introduced.

The full `Flow` additionally has Text, Child, Float, Out and synthesized
Close. Text selects paragraphs; Child/Float/Out share the children store,
so their inverse facts must exclude collisions across those three variants,
not merely within each variant. Close performs no direct target write.
The proof language also needs variant-conditional payload projection and
must connect the copied `item` and match binder to the order-store payload.

`entry_slot` is owner-local. This one-owner case needs no parent conjunct
to distinguish its iterations. A proof across owners must identify the
owner too: block `parent`, paragraph `block`, or child context `block`, plus
the enclosing context identity where needed. Equal local slots in different
owners are valid. Full integration must also preserve read-only order and
inverse fields through projected helper effects; this check-only case does
not establish renderer parallelization or performance.

References: [the M2 gap](../SPLIT-CONTRACT.md#q139-independent-owner-motion-writes-and-the-stored-field-proof-gap),
the pinned [GRAM-5 / RANGE-1 / RANGE-5 specification](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/spec/kernel-spec.md),
and the supported [integer-array inverse case](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/range5-pos-scatter-through-left-inverse.wf).
