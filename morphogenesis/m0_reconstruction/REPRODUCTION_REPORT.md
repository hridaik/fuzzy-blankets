# REPRODUCTION_REPORT.md — Task B status

## Top-line status: NOT DONE

No MATLAB or GNU Octave is installed in this environment. Octave 9/10 is
available (verified, `sources: conda-forge`) and could be installed without
root privileges into a dedicated conda environment; the user was asked
explicitly and chose **not** to install it for this stage (session record,
2026-09-25). Per the task's own ground rules: *"If neither can run the
reference, state this at the top of README.md and label all later Python
results 'unvalidated re-derivation'."* Both actions have been taken.

## What this means concretely

- **No golden traces exist.** `data/golden_traces/` contains only Python-port
  output (see DATA_SCHEMA.md), never a MATLAB/Octave run.
- **No published figure was reproduced.** Friston et al. 2015 fig. 2/3 and
  the Pio-Lopez et al. 2022 figures were not regenerated from a running
  reference and not compared pixel-for-pixel or value-for-value to anything.
- **Panel-by-panel published-vs-reproduced comparison: NOT DONE**, for every
  configuration in the original task list (vanilla 8-cell; bisection; larger
  template; every Pio-Lopez variant; any Friston 2015 perturbation).

## What was done instead

- Full source-level specification of the reference model (MODEL_SPEC.md),
  read directly from the SPM12/SPM25 source and the `active_inference_morphopsy`
  repo, with file:line provenance for every claim.
- A from-scratch Python reconstruction of the model's dynamics (`code/`),
  run and characterized on its own terms (CHARACTERIZATION.md), explicitly
  and repeatedly labeled "unvalidated re-derivation."
- Direct confirmation of two of the ground rules' cross-check items (a, b, c)
  against the primary 2015 paper PDF (`sources/papers/friston2015.pdf`) —
  see DISCREPANCIES.md §2-4.

## Path to closing this out (for a future stage, not this one)

1. Install Octave via conda-forge (`conda create -n octave-dem -c conda-forge
   octave`) — no sudo required, verified available in this environment.
2. Test DEM-toolbox/Octave compatibility (unverified, per the original task's
   own caveat) by attempting to run `toolbox/DEM/DEM_morphogenesis.m` under
   Octave with SPM12 on the path; document any required patches with diffs.
3. If Octave fails, escalate to installing MATLAB (licensing/availability
   outside this session's scope) or running on a machine that already has it.
4. Only after a reference run succeeds: re-attempt Task B's golden-trace
   capture and Task C's equivalence testing (EQUIVALENCE_REPORT.md).
