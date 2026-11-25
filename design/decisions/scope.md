# Scope

What part of the web platform Snowghost renders, the language it is written in, and the engine its output is judged against.

### decision subset-chosen-by-use-and-cost
Snowghost renders a subset of the web chosen feature by feature, and leaves out or approximates a feature whose cost in speed outweighs its use by mainstream sites and generated apps.
- rejected: an agent proposed a subset chosen by measured use alone; the owner rejected it, because the platform must also be fast, so a feature's cost in speed is weighed against its use, and speed wins over strict conformance where the two conflict.
- rejected: an agent proposed complete coverage of the web platform; the owner rejected it, because the goal is a light and fast platform for mainstream sites and generated apps, and complete coverage is the scale of Chromium.

### decision renderer-written-in-whitefoot
The renderer is written in Whitefoot: every module in `renderer/modules.wfg` is a Whitefoot module.
- rejected: an agent proposed an established systems language; the owner rejected it, because the project is there to show what Whitefoot's proofs give a renderer (memory safety, no data races, proved independent parallel work) and to drive Whitefoot with a large real program.

### decision follow-chromium-where-specs-differ
Where a specification and Chromium differ in what a page computes or how it is laid out, the renderer does as Chromium does and records the difference in the stage's research record.
- replaced: Following the specification and recording where Chromium differs was on main; the owner changed it, because readers compare a renderer with Chromium, so a page that differs from it reads as a defect whatever the specification says.
