# Source result contract transport

After the bounded source union changed to its intended exact `+`, the pinned
front end reached two independent contract boundaries. These witnesses concern
only result contracts; they do not test the owner/entry inverse or parallel
publication. Whether either overlaps Whitefoot's helper-frame fix remains
unverified.

Compiler: `wf-78223721f77d`, Whitefoot revision
`78223721f77db615c950b6df1bcc690629f9fe4b`. Each witness was copied alone to
`layout/witness.wf` in a private scratch graph containing `pkg::layout: [];`.
Its `layout/module.wfm` contained only the canonical final newline. The only
compiler command was the authorized front-end check:

```text
whitefootc --graph modules.wfg --check-module pkg::layout
```

`source-result-invariant.wf` constructs a valid `BoundedSource`, returns it in
`Ok`, propagates it, then passes it to an ordinary reference parameter. The
check exited 1 in 0.01 seconds:

```text
./layout/witness.wf:20:16: error[FN-8]: UndischargedCallRequirement
source:   let length = source_length(source: &source);
instantiated_goal: source.values.inner.len <= 1073741824_u64
disposition: Unproved
```

TYPE-11 publishes a struct invariant as a postcondition when the result
ordinal's declared type is that struct. It does not state that publication for
a struct inside `Result`. A success-routed postcondition is the natural explicit
contract for that boundary, so the active producers now declare both array
length bounds. This first witness does not by itself prevent the implementation.

`source-error-forward.wf` adds that truthful success-routed postcondition.
Its failure branch calls the ordinary generic helper whose body returns only
`Err`. The check exited 1 in 0.00 seconds:

```text
./layout/witness.wf:16:5: error[FN-9]: UndischargedPostcondition
source:     return source_failure::<BoundedSource>();
relation: <success payload>.values.inner.len - 0 <= 1073741824
disposition: Unproved
```

FN-9 excludes a direct known failure return from a success-routed obligation,
but a forwarded outcome with no transported tag evidence retains an unknown
success payload. The generic failure helper cannot state its actual
always-`Err` result through the pinned contract interface: FN-9 admits only
success `Ok`/`Some` routes, excludes whole `Result` and Boolean result data, and
rejects an empty selected-return set for a success clause. A counterfeit
numeric constraint on an impossible success payload would not be a truthful
representation of the helper's interface.

The active renderer therefore retains its natural generic error helper calls
and the truthful explicit success bounds. No direct `Err` substitution,
runtime bound guard, serial producer or extra storage directory was introduced.
The full renderer first failed the analogous FN-8 in 8.46 seconds, then the
analogous FN-9 in 12.18 seconds. Later failures, including recursive producer
contract verification, remain unexamined behind this first refusal.

Acceptance for the remaining refusal: `source-error-forward.wf` checks, and
the renderer's success bounds cross ordinary generic error returns without
introducing a runtime check or changing the producer's dependency graph.
`source-result-invariant.wf` records the existing explicit-contract requirement;
accepting it unchanged is not required to unblock this increment. No code
generation, renderer execution or tests ran locally.
