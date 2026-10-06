# Review checklist

Snowghost's own items, which the completion review checks together with the
owner-wide review checks and standards.

- [ ] **R3 — Parallelism first.** Each material choice of a stage,
  algorithm, data structure or interface states its candidates' data
  dependencies, prefers the shortest chain of true dependencies, and names
  the dependency behind every order it adds, such as a shared cache or
  table, a sequential pass or a global counter
  ([AGENTS.md](../AGENTS.md#goal-and-first-priorities)).
- [ ] **C4 — Interface fidelity.** Module bodies implement their `.wfm`
  interfaces and the renderer-shell format as written; an interface,
  contract or effect row changed only with the architecture's approval, and
  none was weakened to let a body pass.
- [ ] **A4 — Whitefoot untouched.** The only change to Whitefoot is a moved
  `whitefoot.pin`.
- [ ] **T4 — The pin.** Whitefoot-kit's
  [review items](../whitefoot-kit/downstream.md#review-items) hold.
