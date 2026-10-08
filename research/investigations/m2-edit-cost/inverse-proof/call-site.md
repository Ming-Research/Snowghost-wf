# Stored-field inverse at the renderer call site

Experiment release wf-exp-7bf6aadcb051 accepts the callee form of
`natural.wf` (branch research/inverse-proof-case, 552dcbf). On this branch
`shift_owner_suffix` in `renderer/layout/reference.wf` states the same
left-inverse requirement per variant and certifies its loop with `apart`.

Hosted layout-check [37823187962](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37823187962)
at 0d324c4 refuses the caller, not the callee:

```text
./layout/reference.wf:558:3: error[RANGE-3]: UndischargedRangeFact
  fact: open_slot
  site: a call
  missing: `blocks^[order^[k].Open.block].entry_slot == k` (line 486)
  mechanical_fix: establish the fact before this site: a range `requires`, a range invariant of the enclosing counted loop, or a guard that excludes the uncovered elements
```

Minimal form (not a complete program; the callee is `natural.wf`'s):

```text
fn caller(order: &[Flow], targets: &[Block]) -> result: unit reads(order), writes(targets) {
  translate_owner_suffix(order: order, targets: targets, first: 0_u64, delta: 1_i32);
  return unit;
}
```

The renderer intends this fact by construction: the writers found by source
inspection that store a payload at an owner slot also store that slot in the
target's `entry_slot` (construction, insertion, private relocation, and the
outer-output copy to a rebuilt child). No checker verifies that intent today.
The caller has no source form that carries this two-store invariant from
those writers to the call: a `requires` on the caller only moves the
obligation outward to `update` and the edit drivers, and a guard or checking
loop would be a run-time alias check, which the project does not use to
conceal a language gap. The missing feature is a maintained invariant over
stored data (for example on the owner sequence and its target stores) that
writers must preserve and readers may assume.
