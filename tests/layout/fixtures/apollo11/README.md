# Apollo11 original-page block fixture

`inputs.tar.gz` contains the unmodified Apollo 11 HTML and its two loaded
stylesheets from [the original diagnostic capture, run 37727037303](https://github.com/Ming-Research/Snowghost-wf/actions/runs/37727037303).
The accompanying `inputs.sha256` is that artifact's original manifest, with
paths relative to the repository after extraction. The permanent Q140 gate
extracts these inputs into `build/research/concurrency/` and verifies every
hash before generating the original block edits. Keep these bytes while that
regression gate exists; retire them only with its explicit replacement.
Actions artifact retention cannot serve as permanent fixture storage.

The article is [Wikipedia's Apollo 11, revision 1371120273](https://en.wikipedia.org/w/index.php?title=Apollo_11&oldid=1371120273),
by its [Wikipedia contributors](https://en.wikipedia.org/w/index.php?title=Apollo_11&action=history).
The HTML retains its attribution, copyright notices and
[Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
license link. The archive preserves the original page and ResourceLoader
stylesheets without modification, including embedded notices and original
source URLs. Wikipedia's page and stylesheet responses are not byte-stable,
so the live revision URL is provenance, not a substitute for these inputs.

The ECMA262 and HTML5 fixtures continue to use the revision-pinned URLs and
hashes in `research/investigations/concurrency/run.sh`.
