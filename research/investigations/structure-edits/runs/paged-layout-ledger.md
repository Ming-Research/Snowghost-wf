# Built-in Paged layout permission evidence

Source: [`64e6dbfc4b935a15fc647404b8df7939068695b4`](https://github.com/Ming-Research/Snowghost-wf/commit/64e6dbfc4b935a15fc647404b8df7939068695b4), compared with [`38fd6be2ba5ad1ca972f689e734e7f40737d8876`](https://github.com/Ming-Research/Snowghost-wf/commit/38fd6be2ba5ad1ca972f689e734e7f40737d8876). [CI run 37579711874](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37579711874), successful `paged-evidence` job, artifact `paged-evidence`. This is a permission listing, not a timing measurement.

## Complete loop listing

[paged-layout-ledger.tsv](paged-layout-ledger.tsv) records every current loop below `renderer/layout/`, including the `pkg::layout::text` submodule, and every removed baseline loop. It has 559 rows: 551 current sites, eight baseline-only sites, and 539 one-to-one correspondences. Every site has its exact function, ordinal within that function, source header, compiler verdict and complete refusal or permission reason. Every current and baseline source loop has an artifact ledger entry; no missing entry is treated as permission. File/line coordinates are relative to the immutable source revisions above, not this document's later commit.

The `paged_scope` column deliberately uses a **function-scope superset**, rather than claiming that every nested loop directly indexes a page. A row is labeled `Paged function scope` when its containing function's signature includes a concrete Paged owner (`Context, EntryStorage, Layout, RoutePatch, RouteTable` or `Paged`), accepts a `&Run`, or constructs such an owner. `scope_evidence` states the source evidence. This labels 316 current loops (85 permitted, 231 denied). Nested loops over a paragraph's ordinary text arrays can therefore be included. All other loops remain in the complete table, labeled `other loop; included for completeness`; that label is not a proof of no indirect Paged access. This complete superset ensures that no loop over Paged is omitted, including loops accessing storage through helpers.

The table's transition applies only to the same logical loop. Stable function and normalized header identify unchanged loops, with occurrence order used for repeated identical headers. Four changed forms were inspected explicitly: the old `store_reduction` inner cell loop becomes the flat pool loop; `finish_tree_sequences`' block-owner loop becomes `seal_context_entries`' owner-sealing loop; `seal_payload_page` becomes `finish_sequence`'s payload run loop; `relocate_payload_page` becomes `relocate_storage`'s payload loop. Each row states its mapping rationale.

Changed loops with no one-to-one match retain `unmatched` in the table: this means a new, removed, or decomposed operation, not a fabricated verdict transition. In particular, old `relocate_node_page` writes both transfer fields in one loop; its replacements are the separate `relocate_storage` own and total loops. Old `seal_node_page` disappears because `bulk_nodes` now writes the final run directly. `relocate_storage`'s links loop is new because slots became context-wide. The old directory allocation/traversal loops disappear into built-in storage operations.

| Ledger scope | Permitted | Denied | Total |
| --- | ---: | ---: | ---: |
| Baseline, experiment compiler | 128 | 419 | 547 |
| Current, experiment compiler | 130 | 421 | 551 |
| Corresponding loops: still permitted | 124 | | 124 |
| Corresponding loops: still denied | | 413 | 413 |
| Corresponding loops: newly permitted | 0 | | 0 |
| Corresponding loops: newly denied | | 2 | 2 |
| Unmatched current operations | 6 | 6 | 12 |
| Removed baseline operations | 2 | 6 | 8 |

The two newly denied loops are child-context sealing in `finish_tree_sequences` (the new checked capacity path propagates failure) and block-owner sealing in `seal_context_entries` (its call writes shared `context.storage`). These are source/effect changes. The baseline was also compiled with its original Whitefoot pin: all 547 verdicts **and reasons** match the experiment compiler byte-for-byte in the loop listing. No compiler-only permission change was observed on that baseline.

The new permitted loops are paragraph and child entry-slot rebasing, entry-field publication through `publish_entry_run`, and links/own/total relocation. These are newly introduced operations, not newly permitted corresponding baseline loops. `prepare_context`'s flat paragraph loop remains permitted, as do the three `boundary_ranks` loops. Flat `store_reduction` remains denied. `publish_payload_run` is denied at its element `swap` call, while `publish_entry_run`'s element assignment is permitted.

## Line counts

[paged-line-counts.tsv](paged-line-counts.tsv) counts all 31 `.wf`/`.wfm` files recursively under `renderer/layout`, including blank and documentation lines, directly from the two Git trees. Total: 28,480 → 28,401 (-79). The renderer diff has 626 inserted and 705 deleted lines; these are edit counts, not total file lengths.

[paged-probe-line-counts.tsv](paged-probe-line-counts.tsv) is separate: native C1 is 103 lines, built-in Paged C1 is 92 (-11). The native file at the current evidence revision has the identical Git blob as `research/storage-mocks` revision `44f616b7babaaeb86eb526e39f2e76cb403675f2`. Neither probe is included in the renderer total.

## Artifact identity

The CI run's recorded head is `64e6dbfc4b935a15fc647404b8df7939068695b4`. The workflow checks out baseline `38fd6be2ba5ad1ca972f689e734e7f40737d8876` explicitly. Each TSV verdict was matched against its raw artifact line and each source location against the named Git tree. These SHA-256 values identify the downloaded loop listings:

| Artifact file | SHA-256 |
| --- | --- |
| `layout-current-loops.txt` | `75ee310f315c1bbb243ce360c11b33203993deca0ea87d4ebcff84d77e6d7226` |
| `layout-baseline-loops.txt` | `73cfb9eb32138a9ab2f6726f51fd3cb2a592725b078c6d1ef362a7be1a073395` |
| `layout-baseline-original-loops.txt` | `73cfb9eb32138a9ab2f6726f51fd3cb2a592725b078c6d1ef362a7be1a073395` |
