# OPEN_QUESTIONS.md

Consolidated from every "NOT DONE" flag in MODEL_SPEC.md, DISCREPANCIES.md,
REPRODUCTION_REPORT.md, EQUIVALENCE_REPORT.md, and CHARACTERIZATION.md.
Ordered roughly by how much they block a future M1 stage.

1. **No MATLAB/Octave reference run exists.** (REPRODUCTION_REPORT.md) This
   is the single biggest open item — it blocks Task B, makes Task C's
   equivalence testing vacuous, and makes every CHARACTERIZATION.md number an
   "unvalidated re-derivation." Octave 9/10 is installable via conda-forge
   without root; the user declined for this stage. Revisit before any M1
   work that depends on quantitative fidelity to the published model.

2. **`spm_ADEM.m`'s exact D-step integration (Jacobian + `spm_dx` local
   linearization) was not ported.** The Python solver reconstructs a reduced
   gradient-flow dynamics instead (DISCREPANCIES.md §9). Whether this
   materially changes qualitative behaviour (convergence speed, fixed points,
   the E4/E5 findings) is unknown without a reference to compare against.

3. **The restriction matrix `R`'s exact semantics** in `spm_ADEM.m`
   (`dE.da = dE.dv*((dgda + dgdx*Dfdx*dfda).*R)`) were not fully traced
   (MODEL_SPEC.md §10). The Python port does not implement `R` explicitly at
   all (action gradients are already per-cell by construction of the field
   law's chain rule) — worth checking whether `R` does something the current
   port is silently missing.

4. **`spm_DEM_z.m` (noise sampling) was not read.** The Python port injects
   simple i.i.d. Gaussian process noise instead of `spm_ADEM`'s temporally-
   correlated (roughness-kernel, `s=1`) generalized noise (DISCREPANCIES.md
   §9, MODEL_SPEC.md §10). Marginal variance was matched (`1/G(1).V`); the
   correlation structure was not.

5. **Three of four Pio-Lopez (2022) perturbations, and all four Friston
   (2015) perturbations, have no known source implementation** in the
   repositories fetched this session (DISCREPANCIES.md §6-7). Options for a
   future stage: (a) re-check `LPioL/active_inference_morphopsy` for branches
   or later commits beyond `bd378a4`; (b) contact the authors; (c) treat them
   as genuinely unpublished/never released and implement from the papers'
   prose description only, clearly labeled as an independent reconstruction
   rather than a port.

6. **The 2022 paper's specific precision claims were not independently
   verified** against its PDF (only the ground-rule prompt's summary was
   used) — unlike the 2015 paper, which was read directly (DISCREPANCIES.md
   §2-4). Low priority: the 2015-paper cross-checks already surfaced the
   important discrepancies (log-precision 2 vs. code's 3; linear vs.
   exponential sensitivity ramp).

7. **The larger (`L=4`) template's full decoded properties** (cell-type
   counts beyond raw n, body length, neighbour spacing) were not computed —
   only `n=16` was established (via E6). MODEL_SPEC.md §1.

8. **E4/E5's fixed learning-rate heuristics were not sensitivity-tested.**
   (CHARACTERIZATION.md, closing caveat.) The "never reaches stationarity"
   and "no cell exceeds 0.9 softmax by bin 512" findings could be solver
   artifacts (rates too small/large) rather than genuine model behaviour.
   Before drawing any conclusion from these numbers, re-run with at least an
   order-of-magnitude sweep on `LR_V`/`LR_A`.

9. **Whether the `active_inference_morphopsy` repo's hard-coded base `v`
   matrix (used by all 6 perturbation files) equals a `rng('default')`-seeded
   `randn(8,8)/8` draw was not checked** — would require MATLAB (item 1).
   (DISCREPANCIES.md §4.)

10. **DATA_SCHEMA.md's tiered blinding is enforced only at the Python-loader
    level, not the filesystem level.** Fine for this single-user stage;
    revisit if the programme moves to a multi-analyst setting where a
    blinded analyst might have raw disk access.
