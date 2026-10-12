# Source result contract transport

`SourceRouteOwners` (`renderer/layout/source_route_owners.wf`) bounds both of
its arrays by a type invariant, so the ownership union can add two counts and
index the sum with exact arithmetic. Its producers return it inside
`Result<SourceRouteOwners, LayoutError>` and reduce independent proposals by
balanced recursion. These witnesses concern only how that invariant reaches
each union call; they do not test the owner/entry inverse or parallel
publication.

Each witness is checked alone with the pinned compiler's front end:

```text
whitefootc --check research/investigations/m2-edit-cost/<witness>.wf
```

## Enum payloads (resolved by Whitefoot#398)

On `wf-78223721f77d` (spec v0.135) a struct invariant did not cross a function
boundary inside `Result`:

- `source-result-invariant.wf`: a valid source returned in `Ok`, propagated
  and passed to `&BoundedSource` was refused with FN-8 at that call.
- `source-error-forward.wf`: with a written
  `ensures when Ok(value: produced): ...` bound, the branch forwarding a
  generic always-`Err` helper was refused with FN-9.

Whitefoot#398, released as `wf-exp-fdbd95c73d50` (spec v0.136, TYPE-11),
makes each invariant of a struct carried in an enum variant a postcondition
routed by that variant: a producer proves it at every `Ok` exit, a generic
failure helper's instance holds it vacuously, and a caller receives it in the
`Ok` context that `propagate` or a `match` arm selects. The two witnesses are
the programs of Whitefoot's conformance cases
`type11-pos-enum-payload-propagated-result` and
`type11-pos-enum-payload-failure-helper`; Snowghost's CI has not yet checked
them on this pin. The renderer's hand-written `ensures when Ok` bounds, which
restated the invariant, were removed: the generated route states the same
relation.

## Recursive component (observed, open)

With the explicit bounds still present, the gate on the `wf-exp-fdbd95c73d50`
pin refused `pkg::layout` first at the union in `source_piece_owners`:

```text
./layout/source_route_owners.wf:125:22: error[FN-8]: UndischargedCallRequirement
source: return union_source_owners(first: &direct, second: &nested);
requires_clause: invariant supplier_limit(owner): owner.suppliers.inner.len <= 1073741824_u64;
instantiated_goal: nested.suppliers.inner.len <= 1073741824_u64
disposition: Unproved
```

`direct` comes from `source_style_owners` and `nested` from
`source_context_owners`; both are ordinary functions returning the struct in
`Result`, neither a container element nor a generic wrapper. The difference is
recursion: `source_piece_owners`, `source_context_owners`,
`source_context_range` and `source_paragraph_owners` form one call-graph
component, and FN-9 withholds every summary of a component from its own
members ("no member of that component may use a summary withheld by this
rule"). The generated TYPE-11 postcondition is such a summary, so a payload
returned by a member of the caller's own component carries no invariant.

`source-recursive-invariant.wf` is the smallest form: a self-recursive
producer passes its recursive call's `Ok` payload to `&BoundedSource`. The
expected refusal is FN-8 at `source_length(source: &inner)` with goal
`inner.values.inner.len <= 1073741824_u64`, or FN-9 at the return forwarding
`inner` if the checker reports that first.

The renderer sites, after the bounds' removal: FN-8 at the unions on lines
116, 141, 153, 217, 247, 248, 252 and 327 (`source_removed_range` is
self-recursive), and FN-9 at the returns forwarding a component member on
lines 184, 206 and 337 (`source_removed_at` is self-recursive).

The recursion is the producers' dependency structure: each balanced reduction
depends only on its two halves. Removing it would add an order the algorithm
does not need, and a ceiling preflight in the union would be a run-time check
standing in for the missing proof, so neither is used.

Acceptance: `source-recursive-invariant.wf` is accepted; the same producer
whose base case constructs a source of 1073741825 values is still refused at
that construction; and `pkg::layout` passes these sites unchanged.

## Value initializer (inferred, not yet observed)

GIVE-1 delivers facts through a `value_if` or `value_match` only for a fragment
integer and, by ENT-5, for a local `Result` or `Option`. A struct delivered by
`give` keeps none of its facts, its type invariant included, because TYPE-11
makes an invariant a fact only at a function boundary. The pinned compiler's
value-delivery join returns at once for a non-fragment result type.

`source-give-invariant.wf`: each branch of a `value_if` obtains a valid source
from a function returning the struct, and the delivered binding is passed to
`&BoundedSource`. The expected refusal is FN-8 at
`source_length(source: &chosen)` with goal
`chosen.values.inner.len <= 1073741824_u64`.

The renderer sites: the unions on `source_route_owners.wf` lines 201
(`style`, an optionally styled column) and 252 (`owned`, an optionally styled
context), and on `source_routes.wf` line 128 (`removed_owners`, present only on
removal). A `Result`-valued initializer followed by one `propagate` would carry
the `Ok` context under the current rules; it is not used, since it changes the
spelling only to avoid the refusal.

Acceptance: `source-give-invariant.wf` is accepted, and a delivery whose one
branch breaks the invariant before `give` is refused at the requiring call.

No code generation, renderer execution or test ran locally.
