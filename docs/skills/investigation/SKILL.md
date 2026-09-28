---
name: investigation
description: Plan, run and report a Snowghost investigation or experiment - an architecture study, a measurement, a comparison with other engines or an agent writer trial - so its result can select or reject a design. Use when starting or extending research/investigations/<name>/, or when a claim needs a new measurement. Not for routine test runs, reading existing research or reporting a CI result.
---

# Investigation

An investigation exists to decide something. Its design, measurements and
rejected alternatives live in `research/investigations/<name>/`, and the
decision that survives goes to the design tree through the `design-tree`
skill. AGENTS.md's rules for choices and verification apply throughout; these
add what this project's experiments need.

1. **Criterion first.** Write the question, the comparison that could answer
   it either way and the result that would reject the proposal before running
   the measurement.
2. **Engine comparisons.** Measure Snowghost, Chromium and Servo on the same
   machine, content, viewport, device pixel ratio, fonts and output path, and
   record each engine's version and settings. Compare pipeline stages only
   where each engine exposes them, and name what each number includes.
3. **Performance attribution.** Attribute a gain or loss with a same-source
   causal comparison, before and after the change, and a falsifier.
4. **Agent writer trials.** Keep four observations apart: whether the program
   and its proofs can be expressed in Whitefoot; whether the tested agent
   writes them with the supplied interfaces, context, tools and repair help;
   whether separately written modules meet independent expectations when
   composed; and whether the result meets its runtime cost goal, and why.
   Record the model, prompt, supplied context, turns and time for each run.
   Model identity and assistance are experimental conditions, not ceilings on
   the language.
