# W1 and W3 at the pinned language

These examples use only the language specified at
[`f949e676acfa811f96b21afd07f02c06dcd14b51`](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/spec/kernel-spec.md).
They were checked by reading that specification and its source examples, **not
compiled or executed**, as the brief requires. W1 is a complete implementation
record **in the existing `pkg::layout` module**, with its current declarations
and implementations as dependencies. W3 is a self-contained source bundle.
These contexts matter: private layout names cannot be imported from a new module.

## W1: today's real stable sequence implementation

This executes the same insert-before, removal and weighted selection operations
as the mock, against today's `EntrySequence`. Its dependencies are the existing
[sequence implementation](../renderer/layout/sequence.wf) and
[layout interface](../renderer/layout/module.wfm), not hypothetical APIs.
`removed` names an existing entry to remove; a removed/missing event query has
today's explicit `no_index` result. `storage_today_rank` also exposes direct-entry rank selection, using the same
cached counts and page-tree accessor; its bounded descent matches the existing
64-step AVL search convention. The input owner controls the lifetime of the
external payloads that Flow values name, as in the existing sequence API.

```wf
struct StorageTodaySelection {
  inserted: u32;
  selected: u32;
  offset: u64;
}

fn storage_today_sequence(sequence: &EntrySequence, before: u32, removed: u32, item: Flow, output: SequenceOutput, event: u64) -> result: Result<StorageTodaySelection, LayoutError> writes(sequence) {
  let visits = no_boundary_visits();
  let inserted = propagate insert_before(sequence: sequence, before: before, item: item, output: output, visits: &visits);
  remove(sequence: sequence, slot: removed, visits: &visits);
  let (selected, offset) = sequence_select(sequence: sequence, event: event);
  let observation = StorageTodaySelection(inserted: inserted, selected: selected, offset: offset);
  return Ok<StorageTodaySelection, LayoutError>(value: observation);
}

fn storage_today_rank(sequence: &EntrySequence, rank: u64) -> result: u32 reads(sequence.nodes), reads(sequence.root), reads(sequence.span) {
  let cursor = sequence^.root;
  let remaining = rank;
  for (level in 0_u64..64_u64) {
    let held = sequence_node(sequence: sequence, slot: cursor);
    if held.live {
    } else {
      return no_index;
    }
    let left = sequence_node(sequence: sequence, slot: held.left);
    if remaining < left.total_count {
      set cursor = held.left;
    } else if remaining == left.total_count {
      return cursor;
    } else {
      let after_left = remaining - left.total_count;
      set remaining = after_left - 1_u64;
      set cursor = held.right;
    }
  }
  return no_index;
}

fn storage_today_links(sequence: &EntrySequence, slot: u32) -> result: SequenceCursor reads(sequence.nodes), reads(sequence.span) {
  let links = slot_cursor(pages: &sequence^.nodes, slot: slot, span: sequence^.span);
  return links;
}
```

This baseline already avoids copying old payloads. Here is its actual access
path, stated with the source symbols so the hidden work is inspectable:

- `insert_before` checks `allocated < 2^30` and `before` liveness, obtains the
  rank, reserves paged storage, writes the fresh Flow and SequenceNode, then
  calls `sequence_insert_at` / `sequence_balance` and updates the root.
- `remove` obtains the rank and calls `sequence_remove_at`; a two-child removal
  calls `sequence_extract_first` and transplants links. Survivor payload slots
  do not change. Payload storage retains holes and slots are not reused.
- Each `sequence_node` / `slot_cursor` access recursively matches
  `SlotPages::Vacant`, `Page`, or `Fork`. A Fork compares with `span / 2`, then
  descends left or right through a Box. `slot_write` allocates a missing directory
  path plus a leaf; it never relocates an old payload page.
- `sequence_select` follows AVL links using cached `total_events` and
  `own_events`, but each link read pays that paged lookup. For a grown directory,
  one search has `O(log entries * directory_depth)` access work; initial single
  pages have no directory descent. C2 changes that inner factor, not AVL's
  child dependency.

The current field-narrow `slot_cursor` already avoids whole-SequenceNode copies;
C2 makes the selected field an ordinary indexed place and removes the bespoke
recursive accessor. FN-5's raw function-kind callback is another valid **today**
way to share recursive lookup, as
[`hash_map_edit`](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/lib/std/collections/hash_map/module.wfm)
shows. It does not give a paged tree O(1) indexing or an exact indirect scatter
footprint for free. No returned-reference feature is needed to write W1 today.

The W1 fence has 42 source lines; it calls the 1,106-line current
sequence module and its layout dependencies. Comparing this wrapper's line
count with the hypothetical library would be meaningless.

## W3: explicit integer-array inverse and explicit contracts

RANGE-1 admits integer-array elements; it cannot state the field-backed inverse
used by the proposed Selection. This source materializes a separate inverse
array once, validates an arbitrary sparse list (including duplicate and bounds
failure), and passes the same proof to two consumers. It deliberately demonstrates
what today's language **can** do: facts already travel through explicit range
postconditions/requirements. The missing feature is making them an encapsulated,
mutation-preserved property of the general field/enum representation, with
proof-only parameters erased.

The producer costs `O(slots + selected)` time/storage initialization because it
fills a whole inverse domain; it is not a proof-free cast of a list. Consumers
still guard indices because RANGE facts do not discharge ordinary OP-4 bounds
at this pin. `positions` is read only by contracts but is still an ordinary
runtime formal. Both scatter loops follow the pinned
[left-inverse conformance case](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/range5-pos-scatter-through-left-inverse.wf).

`desired` is the immutable result of the same ancestor-width computation needed
by W3, supplied as input here to isolate storage/proof costs; it is not a second
proof-derivation pass. Translation uses today's elementwise saturating operation,
as existing geometry helpers do. On the proposed mock's exact arithmetic domain
it has the same value as `+`; no reassociation of saturation is involved.

```wf
struct CheckedOrder {
  order: Box<Array<u64>>;
  positions: Box<Array<u64>>;
}

const vacant_position: u64 = 18446744073709551615_u64;

fn checked_order(source: &[u64], slots: u64) -> result: Option<CheckedOrder> reads(source) contract {
  requires slots <= 1073741824_u64;
  requires source^.len <= slots;
  ensures when Some(value: checked): checked.order.inner.len == source^.len;
  ensures when Some(value: checked): checked.positions.inner.len == slots;
  ensures when Some(value: checked): forall result_bounded(k in 0_u64..checked.order.inner.len): checked.order.inner[k] < slots;
  ensures when Some(value: checked): forall result_paired(k in 0_u64..checked.order.inner.len): checked.positions.inner[checked.order.inner[k]] == k;
} {
  let count = source^.len;
  let order = box_array_filled::<u64>(count: count, value: vacant_position);
  let positions = box_array_filled::<u64>(count: slots, value: vacant_position);
  for (
    at in 0_u64..count,
    invariant forall prefix_bounded(k in 0_u64..at): order.inner[k] < slots,
    invariant forall prefix_paired(k in 0_u64..at): positions.inner[order.inner[k]] == k
  ) {
    let slot = source^[at];
    if slot < slots {
      if positions.inner[slot] != vacant_position {
        return None<CheckedOrder>();
      }
      set order.inner[at] = slot;
      set positions.inner[slot] = at;
    } else {
      return None<CheckedOrder>();
    }
  }
  let checked = CheckedOrder(order: move order, positions: move positions);
  return Some<CheckedOrder>(value: move checked);
}

fn translate_order(order: &[u64], positions: &[u64], origins: &[i64], delta: i64) -> result: unit reads(order), writes(origins) contract {
  requires positions^.len == origins^.len;
  requires forall paired(k in 0_u64..order^.len) when order^[k] < origins^.len: positions^[order^[k]] == k;
} {
  let count = order^.len;
  for (
    at in 0_u64..count,
    apart(i, j) {
    }
  ) {
    let slot = order^[at];
    if slot < origins^.len {
      let old = origins^[slot];
      set origins^[slot] = old +sat delta;
    }
  }
  return unit;
}

fn prepare_order(order: &[u64], positions: &[u64], desired: &[i32], widths: &[i32]) -> result: unit reads(order), reads(desired), writes(widths) contract {
  requires positions^.len == widths^.len;
  requires desired^.len == widths^.len;
  requires forall paired(k in 0_u64..order^.len) when order^[k] < widths^.len: positions^[order^[k]] == k;
} {
  let count = order^.len;
  for (
    at in 0_u64..count,
    apart(i, j) {
    }
  ) {
    let slot = order^[at];
    if slot < widths^.len {
      let wanted = desired^[slot];
      set widths^[slot] = wanted;
    }
  }
  return unit;
}

fn two_scatter_passes(source: &[u64], origins: &[i64], widths: &[i32], desired: &[i32], delta: i64) -> result: Bool reads(source), reads(desired), writes(origins), writes(widths) contract {
  requires origins^.len <= 1073741824_u64;
  requires source^.len <= origins^.len;
  requires widths^.len == origins^.len;
  requires desired^.len == origins^.len;
} {
  let made = checked_order(source: source, slots: origins^.len);
  match move made {
    None() => {
      return False();
    }
    Some(value: checked) => {
      let count = checked.order.inner.len;
      let slots = checked.positions.inner.len;
      translate_order(order: &checked.order.inner[0_u64..count], positions: &checked.positions.inner[0_u64..slots], origins: origins, delta: delta);
      prepare_order(order: &checked.order.inner[0_u64..count], positions: &checked.positions.inner[0_u64..slots], desired: desired, widths: widths);
      return True();
    }
  }
}

fn main() -> status: std::process::ExitStatus pure {
  let source = array_filled::<u64, 3>(value: 0_u64);
  set source[0_u64] = 5_u64;
  set source[1_u64] = 1_u64;
  set source[2_u64] = 4_u64;
  let origins = array_filled::<i64, 7>(value: 10_i64);
  let widths = array_filled::<i32, 7>(value: 0_i32);
  let desired = array_filled::<i32, 7>(value: 12_i32);
  let ok = two_scatter_passes(source: &source[0_u64..3_u64], origins: &origins[0_u64..7_u64], widths: &widths[0_u64..7_u64], desired: &desired[0_u64..7_u64], delta: 3_i64);
  if ok {
  } else {
    return std::process::exit_status(code: 1_u8);
  }
  if origins[5_u64] != 13_i64 {
    return std::process::exit_status(code: 2_u8);
  }
  if origins[0_u64] != 10_i64 {
    return std::process::exit_status(code: 3_u8);
  }
  if widths[4_u64] != 12_i32 {
    return std::process::exit_status(code: 4_u8);
  }
  if widths[2_u64] != 0_i32 {
    return std::process::exit_status(code: 5_u8);
  }
  set source[2_u64] = 5_u64;
  let duplicate = two_scatter_passes(source: &source[0_u64..3_u64], origins: &origins[0_u64..7_u64], widths: &widths[0_u64..7_u64], desired: &desired[0_u64..7_u64], delta: 3_i64);
  if duplicate {
    return std::process::exit_status(code: 6_u8);
  }
  set source[2_u64] = 9_u64;
  let outside = two_scatter_passes(source: &source[0_u64..3_u64], origins: &origins[0_u64..7_u64], widths: &widths[0_u64..7_u64], desired: &desired[0_u64..7_u64], delta: 3_i64);
  if outside {
    return std::process::exit_status(code: 7_u8);
  }
  return std::process::exit_status(code: 0_u8);
}
```

The W3 fence has 135 source lines. The first loop is intentionally
ordered: validating an arbitrary list updates the inverse that the next lookup
must observe; on a duplicate it rejects before either scatter modifies output.
A sort/parallel-check producer is another algorithm with different costs. The
consumer loops need only the retained `paired` relation. By RANGE-3, preserving
it at insertion splits into same-slot/different-slot cases; a repeated slot would
have an earlier non-vacant inverse and cannot take the successful branch.
The two calls do not modify `order` or `positions`, so the second requirement
uses the same producer fact. Readonly `desired` is disjoint from writable widths
by EFF-5 at the enclosing call.

Specification inspection covers FORM-2/GRAM-2–5 formatting and named calls,
OWN-1/OWN-13 moves, OP-2/OP-4 numeric/index domains, REF-3 nonescape,
FN-8/FN-9 routed contracts, EFF-5 separation, RANGE-1–5 and PAR-2. A corresponding
producer pattern was read in
[`range3-pos-postcondition-producer.wf`](https://github.com/Ming-Research/Whitefoot/blob/f949e676acfa811f96b21afd07f02c06dcd14b51/tests/conformance/cases/range3-pos-postcondition-producer.wf).
This is a specification-based validity assessment, not a green compiler ledger.
