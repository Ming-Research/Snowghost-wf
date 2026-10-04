# The renderer-to-shell contract

## Question

What exactly does the renderer give the shell, and how does each frame's
change cross? The owner ruled the boundary (Q65, `design/processes.md`):
the renderer sends facts about the page and the shell owns every policy
that turns them into pixels. The incremental research tree lists the facts
the shell needs (`research/investigations/incremental/DESIGN.md` 6.3). This
investigation turns them into records, a delta protocol and a transport.

`notes/survey.md` holds the survey this draft rests on: what Chromium (paint
chunks, property trees, viz's frames and the newer `LayerContext`),
Gecko with WebRender, Flutter, Fuchsia's Flatland and Android's hwui send,
with every claim marked as read from a primary source, recalled or
inferred; derived message sizes; three candidate contracts; and the open
questions with their criteria.

## What the precedents agree on

Every system separates content in local coordinates, properties in a tree
and resources by key (survey §2). They differ in what crosses and whether
the receiver is told what changed: Chromium's renderer sends viz a complete
frame of quads per frame, while its flag-gated `LayerContext` sends only
added or modified layers and property nodes; Gecko sends WebRender a whole
display list per change, which WebRender diffs; Flatland applies a stream
of operations on client-chosen ids atomically at each present.

## Findings that bear on recorded decisions

1. **Chunk grain.** The incremental tree's 2.1 makes a paint chunk "per
   context and paint phase", but one block formatting context holds 85 to
   95 percent of a page's text, so a one-word edit on html5 would resend
   about 19 MB of glyph data; at one chunk per paragraph, X1's layout unit,
   it is about 0.7 KB (survey §3.1, §4, derived).
2. **Transport.** `design/processes.md` says the data crosses "through
   shared memory", but Whitefoot's host modules are a closed list of six
   ([PRE-2] in Whitefoot's specification) with no shared memory; a byte
   stream (`std::io`) exists. A shared-memory transport is a Whitefoot
   specification change, and since Whitefoot orders two host writes only
   through state both reach ([HOST-1]), publishing a payload before its
   epoch needs one region owner (survey §1, §5).
3. **Two facts the 6.3 table lacks** (survey §3.6): hit-test and
   scroll-routing facts (pointer-events, touch-action, regions whose input
   handlers can block scrolling), without which the shell cannot scroll on
   its own; and a generation on each scroll offset, which has two writers,
   the shell and script. Conversely, facts the shell can derive (glyph
   counts, blur cost, whether a chunk changed in content or geometry) need
   not be sent (§3.11).

## Candidate contracts

All three use renderer-allocated ids with generations, immutable chunks
without positions, placement and order in tables of their own, interned
effect descriptors and long-lived resource blobs (survey §5).

- **A. A retained arena plus an epoch journal.** The shell reads records in
  place, freed after an acknowledgement. No copy, but the shell validates
  data that stays writable, the renderer manages and compacts the arena,
  and it needs shared memory.
- **B. Transactions copied into a scene the shell owns.** Flatland's and
  `LayerContext`'s shape. Its meaning does not depend on the transport, so
  it runs over a pipe on today's Whitefoot and over a shared ring later; the
  shell copies before it validates; the buffer is reclaimed by a read index.
  A shell restart needs a full republish, which the renderer's memoized
  paint can produce.
- **C. Versioned snapshots sharing unchanged subtrees.** Every epoch is a
  whole value, but reclaiming shared structure across processes is hard,
  and it needs shared memory.

The survey recommends B.

## Checking that policy never changes the picture

Three layers (survey §6): the scene rebuilt from any history of deltas
equals the scene of one full publish; every shell policy's frame at rest
equals a reference full redraw (X14; Q66's exception); and the reference
rasterizer checks each declared fact (bounds, opaque area, backdrop reads)
against the chunk's own pixels. This works because every field is either
drawn by the reference redraw or a claim about what it draws.

## Decisions for the owner

Open; the cards are in the PR's handoff.

- **Q74, chunk grain.** One chunk per paragraph (and per block box's
  decoration), recommended, against the tree's per-context chunk.
- **Q75, transport staging.** Begin over a byte stream with contract B's
  records, and move to a shared-memory ring when Whitefoot has a host
  module for it, recommended; against waiting for that module, and against
  changing the records with the transport. This departs from the wording of
  `design/processes.md` until shared memory arrives.
- **Q76, the contract's shape.** B, recommended, against A and C.

## Open questions and their experiments

Each criterion is fixed before its run (survey §7):

| Id | Question | Criterion |
|---|---|---|
| C1 | Paragraph chunks, or line chunks for large paragraphs? | lines are added where the p99 one-word-edit transaction exceeds 4 KB at paragraph grain |
| C2 | Glyph encoding: 10, 6 or 4 bytes per glyph | the smallest form whose shell decode costs under 1 ms per MB and whose positions round-trip exactly |
| C3 | Context-relative placement or a summary tree in the contract | the summary form if a sentence edit's p90 placement bytes exceed 16 KB under context-relative placement |
| C4 | Is copying into the shell (B) a measurable cost? | keep B unless the copy exceeds 10 percent of apply and upload for the first frame or 0.1 ms per edit transaction |
| C5 | Whole page or progressive first frame (the tree's X9) | X9's criterion as written |
| C6 | Glyph outlines, with or without slight hinting applied by the renderer, against font bytes | outlines if their text pixels differ from the reference browser's in no more glyphs than font bytes do |
| C7 | Splices or whole-list replacement for order lists | splices if whole-list replacement exceeds 64 KB at p90 on block insertions and removals |
| C8 | Interning repeated chunk content | intern only if duplicates exceed 10 percent of the first frame's bytes |
| C9 | The two-writer scroll protocol | after a script sets `scrollTop` during a shell-driven fling, the offset equals the generation-ordered result and no frame shows an older script offset |
| C10 | Does the soundness check catch wrong facts? | each injected wrong fact (shrunken bounds, too-large opaque area, missing backdrop read) fails the check once |

C1 to C3, C7, C8 and C10 need Snowghost's paint stage; C4, C5 and C9 the
shell; C6 a rasterizer and the reference's pixels.

## Not decided here

Video's producer and frame protocol, image decode size, the accessibility
tree's place on the same transport, and whether colour animations move to
the shell.

## Owner rulings

2026-10-04: after a comparison of each card's performance and feasibility,
the owner wrote in Chinese that they agree to all, as recommended: Q74 (a
chunk per paragraph), Q75 (a byte stream first with unchanged records,
shared memory when Whitefoot has a host module for it) and Q76 (transactions
copied into a scene the shell owns; revisit if C4 finds the copy above its
criterion). The design-tree changes they need (the chunk grain in the
incremental tree's paint boundary, the transport wording of
`design/processes.md`) are made with their log entry in the work that
builds the paint stage or the shell.
