# Atlas trial 1: can an agent describe the layout engine from the atlas?

Written before any run.

## Question

Does the static atlas (generated from declarations, docs, effect rows and the
call graph, plus the hand annotation layer) let an agent describe an
architectural subject as accurately as reading the source does? Where it does
not, is the cause information the atlas lacks (a language or tool gap), or
information it holds that the agent failed to find (an interaction gap)?

## Prompt (identical in every condition, apart from the access sentence)

> Describe the design of Snowghost's layout engine (the renderer's layout
> stage): its inputs and outputs, its main data structures and how they relate
> (including what the integer indices in them point to), the steps it runs and
> in what order, how it handles incremental updates after an edit, and where
> its work is independent and could run in parallel. Write 600 to 1000 words.
> Make concrete, checkable statements and name the functions and types you rely
> on. Say "unknown" rather than guess.

## Conditions

| | Access | Isolation |
|---|---|---|
| A | atlas only, at http://127.0.0.1:8765, through Playwright MCP | codex shell tool and unified exec disabled, other browser and app tools disabled, cwd an empty /tmp/sg-trial/A, Playwright allowed origin 127.0.0.1:8765 only |
| B | renderer source only, a copy of renderer/*.wf, *.wfm, modules.wfg | read-only sandbox, cwd /tmp/sg-trial/B holding only that copy; no design/ or research/ prose |
| C | both | as A, plus the B copy in cwd and the shell enabled read-only |

Agent: codex-cli 0.160.0, model gpt-6.1-sol, reasoning effort low. Each run
records wall time, tokens and its full event log (--json).

Isolation is verified, not assumed: before A runs, a probe asks the A setup to
list its directory and read a file outside it, and must fail; after each run
its event log is checked for tool calls outside its access.

## Grading

A separate Claude agent that did not answer, with read access to the source,
splits each answer into atomic claims and labels each correct, incorrect or
unverifiable, citing file:line. I check a sample of at least ten labels per
answer against the source myself.

Every incorrect claim and every omitted subject in A is classified:
(a) the atlas does not hold the information; (b) the atlas holds it and the
agent did not find it; (c) the agent asserted something neither the atlas nor
the source supports.

## Criterion

- The atlas answers this question adequately if A's incorrect fraction is no
  more than B's plus 10 points and A covers at least four of the five asked
  subjects with a correct claim.
- Every (a) item becomes a candidate requirement for the language or the
  exporter; every (b) item an interaction defect.
- One run per condition first. If A and B differ by less than 10 points,
  repeat each twice more before concluding anything about the difference.
