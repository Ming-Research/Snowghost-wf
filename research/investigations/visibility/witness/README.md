# Visibility witness

A temporary witness that the pinned Whitefoot compiler gives one module no way
to call a private function of another module, however the two are related. It
supports Whitefoot request `sg-req-research-visibility` on the status board.

- `private/`: module `stage` (private `step_one`, public `run`) and module
  `probe`, which depends on `stage` and calls `pkg::stage::step_one`.
  Expected: `probe` is rejected for MOD-5 (a declaration of another module that
  is not public); `stage` alone is accepted.
- `control/`: identical except `step_one` is declared `public` in
  `stage/module.wfm`. Expected: the whole graph is accepted. This shows the
  rejection in `private/` is about visibility alone.

`.github/workflows/visibility-witness.yml` checks both with the compiler
`whitefoot.pin` names and fails unless the expectations hold.

Remove this directory and the workflow once Whitefoot closes the request.
