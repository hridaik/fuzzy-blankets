# EQUIVALENCE_REPORT.md — Task C status

## Top-line status: NOT DONE (no ground truth to compare against)

Task C asks for, per configuration, "max absolute and relative deviation per
variable per bin against the golden traces, with a tolerance declared in
advance." **No golden traces exist** (REPRODUCTION_REPORT.md) — Task B was
not performed because no MATLAB/Octave reference is available in this
environment. Equivalence testing against nothing is not meaningful, so this
report cannot contain quantitative deviation numbers, and none are fabricated
here.

## What was implemented instead

A modular Python implementation (`code/`) split exactly as Task C requests:

| Module | Task C component |
|---|---|
| `code/field.py` | (1) process physics — the field law |
| `code/generative.py` | (2) cell generative model (`Mg`) and process (`Gg`) |
| `code/solver.py` | (3) integrator (disclosed reduced reconstruction, DISCREPANCIES.md §9) |
| `code/interventions.py` | (4) intervention hooks — parameterised, logged, per-cell/channel/bin — **only the one perturbation with source-code grounding is implemented** (DISCREPANCIES.md §6) |
| `code/storage.py` | (5) observation layer with tiered blinding (DATA_SCHEMA.md) |

This satisfies the *structural* requirement of Task C (a modular
implementation with intervention hooks) but not its *validation* requirement
(quantitative agreement with a reference run), because step (3) is,
necessarily and by disclosure, a simplified reconstruction of `spm_ADEM`'s
generalized-filtering dynamics rather than a byte-level port — see
DISCREPANCIES.md §9 for exactly what was simplified and why (no hidden
states/hyperparameters in this specific model reduces the general 874-line
solver considerably, but the remaining gradient-flow dynamics were
reconstructed via explicit-Euler + finite-difference gradients, not
`spm_dx`'s local-linearization/matrix-exponential scheme).

## Declared tolerance (for future use, once golden traces exist)

Not set, because there is nothing to compare against yet. When Task B is
completed (REPRODUCTION_REPORT.md "path to closing this out"), the
recommended tolerance-setting procedure is: run the reference twice with
different RNG seeds (if any stochasticity exists) to establish the
reference's own run-to-run variability first, and only then declare a
port-vs-reference tolerance that is meaningfully tighter than reference
self-variability — per Task C's own instruction ("If deviations grow over
time, test whether the reference shows equal sensitivity to perturbations of
the same size before attributing it to the port").

## What partial validation was possible

- The template-decoding logic (`code/template.py`) was checked against a
  hand-computed reference ordering of MATLAB's column-major `find()` semantics
  (verified numerically in this session, not merely asserted) — see inline
  comments and MODEL_SPEC.md §1.
- The softmax, field law, and sensory/precision constants were transcribed
  and cross-checked line-by-line against the fetched SPM12 source (not
  executed, but read character-by-character) — MODEL_SPEC.md §2-4, §11.
- No numerical equivalence check was possible for the integration dynamics
  themselves (the one component that would actually require running the
  reference).
