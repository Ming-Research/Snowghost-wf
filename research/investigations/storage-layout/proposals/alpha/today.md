# W1 and W3 at today's pin

These are source readings at Whitefoot
`f949e676acfa811f96b21afd07f02c06dcd14b51`, not compiler runs. No hypothetical
Paged type, projection syntax, returned reference, or proof token occurs in
the source fences in this file. Canonical spelling was checked against the
pinned specification; compiler acceptance and runtime behavior remain untested
under the explicit no-compile constraint.

## W1: the actual layout-module fragment

The following six functions are reproduced byte-for-byte from
[`renderer/layout/sequence.wf`](../renderer/layout/sequence.wf) and
[`renderer/layout/splice_sequence.wf`](../renderer/layout/splice_sequence.wf) at Snowghost
`49c138aa666c3c8e474267fe4d24ae1ae92c2419`. They belong **inside the existing
layout module**, with its existing interface and helpers; they are not
advertised as a standalone program. `SlotPages<T>` is its `Vacant`,
`Fork(Box<SlotPages<T>>, Box<SlotPages<T>>)` or `Page(Box<Array<T>>)` owner.
The remaining names resolve to that module's existing definitions: in
particular its AVL insert/remove/rotation/summary code is the same library
boundary as W1's proposal. Copying those algorithms here a second time would
not add a storage comparison.

Insert appends a stable slot, navigates the AVL by rank and repairs only
index ancestors. Remove tombstones the node and transplants links; it does
not compact payloads. The two selection functions descend cached virtual-event weights or direct
entry counts, respectively; direct ranks therefore also work with nested
entries whose virtual-event weight exceeds one. Those stable
slots have no reuse, hence no generation checks today. The generic storage
read/write pair shows the extra runtime-depth directory descent concretely.

```wf
fn slot_read<T: copy>(pages: &SlotPages<T>, slot: u32, span: u32, missing: T) -> value: T reads(pages) {
  doc "Reads one stable slot through a bounded directory path; absent pages return the supplied vacant value.";
  if slot >= span {
    return missing;
  }
  match pages^ {
    Vacant() => {
      return missing;
    }
    Page(values: page) => {
      let at = cvt::<u32, u64>(slot);
      if at < page^.inner.len {
        return page^.inner[at];
      }
      return missing;
    }
    Fork(left: left_page, right: right_page) => {
      let half = span / 2_u32;
      if slot < half {
        let value = slot_read::<T>(pages: &left_page^.inner, slot: slot, span: half, missing: missing);
        return value;
      }
      let later = slot - half;
      let value = slot_read::<T>(pages: &right_page^.inner, slot: later, span: half, missing: missing);
      return value;
    }
  }
}

fn slot_write<T: copy>(pages: &SlotPages<T>, slot: u32, span: u32, value: T, missing: T) -> result: unit writes(pages) {
  doc "Allocates only a missing directory path and its four-slot page, then writes one slot. Existing payload pages never move.";
  if slot >= span {
    return unit;
  }
  match pages^ {
    Vacant() => {
      if span <= 4_u32 {
        let count = cvt::<u32, u64>(span);
        let values = box_array_filled::<T>(count: count, value: missing);
        let page = SlotPages<T>::Page(values: move values);
        set pages^ = move page;
      } else {
        let empty_left = SlotPages<T>::Vacant();
        let empty_right = SlotPages<T>::Vacant();
        let new_left = box_new::<SlotPages<T>>(value: move empty_left);
        let new_right = box_new::<SlotPages<T>>(value: move empty_right);
        let fork = SlotPages<T>::Fork(left: move new_left, right: move new_right);
        set pages^ = move fork;
      }
    }
    Fork(..) => {
    }
    Page(..) => {
    }
  }
  match pages^ {
    Vacant() => {
    }
    Page(values: stored_page) => {
      let at = cvt::<u32, u64>(slot);
      if at < stored_page^.inner.len {
        set stored_page^.inner[at] = value;
      }
    }
    Fork(left: stored_left, right: stored_right) => {
      let half = span / 2_u32;
      if slot < half {
        slot_write::<T>(pages: &stored_left^.inner, slot: slot, span: half, value: value, missing: missing);
      } else {
        let later = slot - half;
        slot_write::<T>(pages: &stored_right^.inner, slot: later, span: half, value: value, missing: missing);
      }
    }
  }
  return unit;
}

fn insert_before(sequence: &EntrySequence, before: u32, item: Flow, output: SequenceOutput, visits: &BoundaryVisits) -> result: Result<u32, LayoutError> writes(sequence), writes(visits) {
  doc "Inserts one new direct entry before a live stable slot, or at end for no_index. A range is a batch of these operations in source order. Earlier payload slots are neither read nor copied.";
  if sequence^.allocated >= 1073741824_u32 {
    let failure = too_large::<u32>();
    return failure;
  }
  if before != no_index {
    let target = boundary_node(sequence: sequence, slot: before, visits: visits);
    if target.live {
    } else {
      let inconsistent = LayoutError::Inconsistent();
      let failure = Err<u32, LayoutError>(error: inconsistent);
      return failure;
    }
  }
  let rank = boundary_rank(sequence: sequence, slot: before, visits: visits);
  sequence_reserve(sequence: sequence);
  let fresh = sequence^.allocated;
  let missing = Flow::Close(block: no_index);
  slot_write::<Flow>(pages: &sequence^.payloads, slot: fresh, span: sequence^.span, value: item, missing: missing);
  let yes = True();
  let links = SequenceCursor(left: no_index, right: no_index, parent: no_index, height: 1_u32, live: yes, own_events: output.events, total_events: output.events, total_count: output.count);
  let node = SequenceNode(links: links, own: output, total: output);
  let missing_node = vacant_node();
  slot_write::<SequenceNode>(pages: &sequence^.nodes, slot: fresh, span: sequence^.span, value: node, missing: missing_node);
  let old_root = sequence^.root;
  let inserted = sequence_insert_at(sequence: sequence, root: old_root, rank: rank, added: fresh, parent: no_index, visits: visits);
  set sequence^.root = inserted;
  set sequence^.allocated = fresh + 1_u32;
  let success = Ok<u32, LayoutError>(value: fresh);
  return success;
}

fn remove(sequence: &EntrySequence, slot: u32, visits: &BoundaryVisits) -> result: unit reads(sequence.span), writes(sequence.nodes), writes(sequence.root), writes(visits) {
  doc "Removes one stable slot, leaving its payload page as a hole. Removing a range repeats this operation over the removed handles; unrelated payloads are untouched.";
  let held = boundary_node(sequence: sequence, slot: slot, visits: visits);
  if held.live {
    let rank = boundary_rank(sequence: sequence, slot: slot, visits: visits);
    let old_root = sequence^.root;
    let remainder = sequence_remove_at(sequence: sequence, root: old_root, rank: rank, visits: visits);
    set sequence^.root = remainder;
  }
  return unit;
}

fn sequence_select(sequence: &EntrySequence, event: u64) -> (slot: u32, offset: u64) reads(sequence.nodes), reads(sequence.root), reads(sequence.span) {
  doc "Selects a direct entry by its virtual event weight in logarithmic index work, skipping cached subtree spans.";
  let cursor = sequence^.root;
  let remaining = event;
  for (level in 0_u64..64_u64) {
    let held = sequence_node(sequence: sequence, slot: cursor);
    if held.live {
    } else {
      return no_index, 0_u64;
    }
    let left_node = sequence_node(sequence: sequence, slot: held.left);
    if remaining < left_node.total_events {
      set cursor = held.left;
    } else {
      set remaining = remaining -sat left_node.total_events;
      if remaining < held.own_events {
        return cursor, remaining;
      }
      set remaining = remaining -sat held.own_events;
      set cursor = held.right;
    }
  }
  return no_index, 0_u64;
}

fn direct_slot(sequence: &EntrySequence, rank: u64, visits: &BoundaryVisits) -> slot: u32 reads(sequence.nodes), reads(sequence.root), reads(sequence.span), writes(visits) {
  doc "Selects one direct stable slot by a transient rank, opening only index metadata.";
  let cursor = sequence^.root;
  let remaining = rank;
  for (level in 0_u64..64_u64) {
    let held = boundary_node(sequence: sequence, slot: cursor, visits: visits);
    if held.live {
    } else {
      return no_index;
    }
    let left = boundary_node(sequence: sequence, slot: held.left, visits: visits);
    if remaining < left.total_count {
      set cursor = held.left;
    } else if remaining == left.total_count {
      return cursor;
    } else {
      let preceding = left.total_count +sat 1_u64;
      set remaining = remaining -sat preceding;
      set cursor = held.right;
    }
  }
  return no_index;
}
```

This is valid existing source in its module context at the pinned language,
not proof that the pin was re-run here. A callback lookup using FN-5 and REF-1
could remove repeated source descents today, as hash_map_edit demonstrates;
it would not remove the directory's dependent loads or give a writing callback
a more precise whole-tree effect. Current field-narrow helpers already reduce
whole-value copies. The proposed storage is not credited with inventing them.

## W3: complete source bundle with two passes

Unlike W1, this fence is a complete source-bundle program. It uses a separate
integer inverse array, the representation the pin already supports. There is
one validation call, followed by two later parallel-eligible scatter passes;
their RANGE requirements reuse the result. Thus **fact transfer itself is not
new in the proposal**. S2 replaces the duplicate integer-array representation
with a projection of a public stored integer field and permits physical field
groups. It does not erase the inverse parameter or create a private invariant.

The sparse order is 5, 1, 6; the expected output changes only those slots.
The final duplicate list 5, 5 must be rejected. Expected widths are derived
from the literal available widths minus the literal inset, not the program's
previous output. The guards on the stored indices are still necessary because
RANGE facts do not discharge ordinary indexing obligations.

```wf
fn validate_order(order: &[u64], position: &[u64]) -> result: Result<u64, unit> reads(order), reads(position) contract {
  ensures when Ok(value: checked): forall bounded(k in 0_u64..order^.len): order^[k] < position^.len;
  ensures when Ok(value: checked): forall inverse(k in 0_u64..order^.len): position^[order^[k]] == k;
} {
  let count = order^.len;
  let limit = position^.len;
  for (
    k in 0_u64..count,
    invariant forall bounded_prefix(q in 0_u64..k): order^[q] < limit,
    invariant forall inverse_prefix(q in 0_u64..k): position^[order^[q]] == q
  ) {
    let at = order^[k];
    if at >= limit {
      return Err<u64, unit>(error: unit);
    }
    if position^[at] != k {
      return Err<u64, unit>(error: unit);
    }
  }
  return Ok<u64, unit>(value: count);
}

fn translate(order: &[u64], position: &[u64], y: &[i64], delta: i64) -> result: unit reads(order), writes(y) contract {
  requires position^.len == y^.len;
  requires forall inverse(k in 0_u64..order^.len) when order^[k] < y^.len: position^[order^[k]] == k;
} {
  let count = order^.len;
  for (
    k in 0_u64..count,
    apart(i, j) {
    }
  ) {
    let at = order^[k];
    if at < y^.len {
      set y^[at] = y^[at] +sat delta;
    }
  }
  return unit;
}

fn set_widths(order: &[u64], position: &[u64], parents: &[u64], available: &[i64], widths: &[i64], inset: i64) -> result: unit reads(order), reads(parents), reads(available), writes(widths) contract {
  requires position^.len == widths^.len;
  requires forall inverse(k in 0_u64..order^.len) when order^[k] < widths^.len: position^[order^[k]] == k;
} {
  let count = order^.len;
  for (
    k in 0_u64..count,
    apart(i, j) {
    }
  ) {
    let at = order^[k];
    if at < widths^.len {
      if at < parents^.len {
        let parent = parents^[at];
        if parent < available^.len {
          let room = available^[parent] -sat inset;
          set widths^[at] = imax(room, 0_i64);
        }
      }
    }
  }
  return unit;
}

fn two_passes(order: &[u64], position: &[u64], parents: &[u64], available: &[i64], y: &[i64], widths: &[i64], delta: i64, inset: i64) -> result: Result<unit, unit> reads(order), reads(position), reads(parents), reads(available), writes(y), writes(widths) {
  if position^.len != y^.len {
    return Err<unit, unit>(error: unit);
  }
  if position^.len != widths^.len {
    return Err<unit, unit>(error: unit);
  }
  let checked = validate_order(order: order, position: position);
  match checked {
    Ok(value: done) => {
      translate(order: order, position: position, y: y, delta: delta);
      set_widths(order: order, position: position, parents: parents, available: available, widths: widths, inset: inset);
      return Ok<unit, unit>(value: unit);
    }
    Err(error: failure) => {
      return Err<unit, unit>(error: unit);
    }
  }
}

fn main() -> status: std::process::ExitStatus pure {
  let order = array_filled::<u64, 3>(value: 0_u64);
  set order[0_u64] = 5_u64;
  set order[1_u64] = 1_u64;
  set order[2_u64] = 6_u64;
  let position = array_filled::<u64, 8>(value: 18446744073709551615_u64);
  set position[5_u64] = 0_u64;
  set position[1_u64] = 1_u64;
  set position[6_u64] = 2_u64;
  let parents = array_filled::<u64, 8>(value: 0_u64);
  set parents[1_u64] = 2_u64;
  let available = array_filled::<i64, 3>(value: 30_i64);
  set available[2_u64] = 50_i64;
  let y = array_filled::<i64, 8>(value: 0_i64);
  let widths = array_filled::<i64, 8>(value: 0_i64);
  let applied = two_passes(order: &order[0_u64..3_u64], position: &position[0_u64..8_u64], parents: &parents[0_u64..8_u64], available: &available[0_u64..3_u64], y: &y[0_u64..8_u64], widths: &widths[0_u64..8_u64], delta: 3_i64, inset: 4_i64);
  match applied {
    Ok(value: checked) => {
    }
    Err(error: failed) => {
      return std::process::exit_status(code: 1_u8);
    }
  }
  if y[5_u64] != 3_i64 {
    return std::process::exit_status(code: 2_u8);
  }
  if y[1_u64] != 3_i64 {
    return std::process::exit_status(code: 3_u8);
  }
  if y[6_u64] != 3_i64 {
    return std::process::exit_status(code: 4_u8);
  }
  if y[0_u64] != 0_i64 {
    return std::process::exit_status(code: 5_u8);
  }
  if widths[5_u64] != 26_i64 {
    return std::process::exit_status(code: 6_u8);
  }
  if widths[1_u64] != 46_i64 {
    return std::process::exit_status(code: 7_u8);
  }
  if widths[6_u64] != 26_i64 {
    return std::process::exit_status(code: 8_u8);
  }
  let duplicate = array_filled::<u64, 2>(value: 5_u64);
  let rejected = validate_order(order: &duplicate[0_u64..2_u64], position: &position[0_u64..8_u64]);
  match rejected {
    Ok(value: wrong) => {
      return std::process::exit_status(code: 9_u8);
    }
    Err(error: expected) => {
      return std::process::exit_status(code: 0_u8);
    }
  }
}
```

The proof shape follows the pin's
[maintained left-inverse case](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/range5-pos-scatter-through-left-inverse.wf),
RANGE-1–5 and PAR-2. It intentionally exposes the extra input array and runtime
ABI parameters. General aliasing is still EFF-5 checked: `available` must not
be a writing target, and `position` must remain unchanged for both passes.

## License for adapted Snowghost source

The W1 excerpts and adaptations retain this repository's notice beside them:

```text
MIT License

Copyright (c) 2026 Bai Ming

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
