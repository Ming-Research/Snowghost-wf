# Apollo 11 structural-path diagnosis

## Question and rejection criterion

On the unchanged renderer at `cf12c609`, do Apollo 11's X5 block edits take
local splices, or do explicit refusals rebuild a large context? Inspect every
edit's structural path and boundary counters, sequentially and in parallel,
and compare every retained result with a full rebuild. Local paths throughout
would reject fallback as the explanation. Inventory each edited parent and
its containing owners against the splice contract before attributing a
reason code to a particular CSS dependency. Also inspect the other five X5
kinds to distinguish font-size propagation from structural reconstruction.

The temporary `apollo11-diag` hosted workflow uses the branch's pinned
compiler and ordinary X5 generator. It preserves and hashes the live HTML
and both external stylesheets: Apollo's oldid does not stabilize rendered
bytes. These bytes need not match the 14900K capture used by E2 run
[37674972449](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37674972449).
Hosted timing fields are incidental diagnostics, not a performance comparison
with that machine. E2's retained raw timing artifacts are the source for any
14900K time decomposition. No renderer behavior is changed by this diagnosis.
