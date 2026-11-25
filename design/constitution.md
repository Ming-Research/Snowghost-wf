# The Snowghost constitution

This constitution holds what Snowghost is for and its lasting values, and every
decision in the project comes from them. The owner sets it and changes it.

## What Snowghost is for

Snowghost is a renderer for user interfaces built with web technology, written
in Whitefoot. It exists first for Whitefoot: it is the large real program that
shows what Whitefoot gives a renderer, safety from the source together with a
rendering pipeline parallel and incremental from end to end, and it exposes what
Whitefoot still lacks. Second, it may become a product in its own right: a
small, fast engine that can take the place of the system WebView on every
platform.

## Article 1 (faithful). It renders the web it claims as today's engines do

Within the part of the web platform Snowghost claims, a page renders on it as
today's engines render it, so that the pages and applications in scope move to
it unchanged.

Violations: a page in scope that renders differently on Snowghost, unrecorded.

## Article 2 (safe). Safety from Whitefoot's proofs

Snowghost's renderer gets its safety from Whitefoot's proofs: it keeps every
check Whitefoot requires, and nothing turns one off. A page, whatever it holds,
cannot break the safety of Snowghost or of its host.

Violations: an unchecked operation or an escape from Whitefoot's checks, for any
reason; a page that breaks the safety of Snowghost or its host.

## Article 3 (fast). Faster than the engines in use today

On the same pages and the same edits, Snowghost renders faster than the engines
in use today. Speed counts only on top of Articles 1 and 2.

Violations: a speed-up that breaks Article 1 or 2.

## Article 4 (for Whitefoot). A gap goes back to Whitefoot

What Snowghost cannot write well or make fast in Whitefoot is a gap of
Whitefoot, closed in Whitefoot; a fault of Snowghost's own is fixed in
Snowghost.

Violations: a gap of Whitefoot that Whitefoot never heard of.
