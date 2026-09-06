# MECHANISM_AUDIT_PLAN.md

Plan executed for Parts B-H of the mechanism audit (Part A is
`V1_RECORD_AUDIT.md`; Parts I/J/K/L are in this directory's figures and in
`../v2_interface_control/`). Written before results are summarized in
`MECHANISM_AUDIT_RESULTS.md`, to keep the plan/results distinction visible.

All code lives in `code/`, imports the frozen `../python/flock_sim` package
unmodified, and writes only into `data/`, `figures/`, `logs/` under this
directory. `PROTOCOL_V1a` (see `V1_RECORD_AUDIT.md` section A2) thresholds,
horizons, and the canonical snapshot are used throughout, unchanged.

1. **B — structural dependency audit** (`code/dynamical_shell.py`). Derive,
   from `flock_sim.active_inference.compute_G` and `flock_sim.lattice.Lattice`
   directly (not assumed), which birds are actual inputs to the frozen core
   `I0`'s update at time `t`. Compute `B^D_0`, `E^D_0`, and (for later parts)
   k-hop shells and graph distances, all on the STATIC lattice interaction
   graph (birds do not move in this port — see the structural finding stated
   in that file's docstring).

2. **C — boundary comparison** (`code/boundary_compare.py`). Overlap
   (`|B^F_0 cap B^D_0|`, Jaccard) on the canonical flock and on a small
   ensemble of other qualifying baseline flocks; join the existing k=1
   response map with dynamical distance; define an empirical control-interface
   candidate `B^C`.

3. **D — feasibility ladder** (`code/feasibility_ladder.py`). Arms
   D0 (baseline) / D1 (full I0, diagnostic) / D2 (`B^F_0`) / D3+D4 (`B^D_0`,
   argued identical here — see structural finding in Part B) / D5 (all
   non-core), n=50 replicates/arm, common random numbers, canonical snapshot,
   frozen `T_u=20/T_r=20` and success/integrity/persistence thresholds.

4. **Interpretation gate**: applied inline in `MECHANISM_AUDIT_RESULTS.md`
   before any further sparsification, per the task brief's hard requirement.

5. **E — exhaustive pair synergy** (`code/pair_synergy.py`). All
   `C(80,2)=3160` non-core pairs, n=10 replicates/pair (development scale,
   documented), `R_ij`/`S_ij` diagnostics, joined with `B^D_0`/`B^F_0`
   membership and dynamical distance.

5b. **Shell sparsification** (`code/shell_sparsification.py`, not separately
   named in the task brief's letter but directly required by its Part K2
   spirit): exhaustive k=1-3 and greedy k=4-12 *restricted to the 12-member
   `B^D_0` pool identified in Part B* — the natural next question once Part D
   shows the full shell works and Part E shows no pair (from any of the 80
   exterior birds) does.

6. **F — direct-core resistance curve** (`code/core_resistance.py`).
   Mechanistic diagnostic only; `k in {1,2,4,8,12,16,20}` interior birds
   forced, ranked by internal degree, plus random-subset controls.

7. **G — parameter-regime sensitivity** (`code/parameter_sensitivity.py`).
   `code_default` (beta=1,rho=15,omega=3) vs `manuscript_all_ones`
   (beta=1,rho=1,omega=1), both predeclared and run once each: from-scratch
   baseline qualification rate (n=50 seeds) and a ceteris-paribus check on the
   canonical initial condition (uncontrolled, `B^D_0` control, all-non-core
   control, resistance-by-degree).

8. **H — statistical/Markov-boundary validation**
   (`code/predictive_screening.py`). H1: a structural one-step screening claim
   derived directly from the computational graph (not assumed). H2: empirical
   validation via per-bird one-step-ahead predictive log-loss, comparing
   `M_full` (ground truth), `M_{B^D_0}` (should be exact, verified by
   assertion + corruption test), and `M_{B^F_0}` (Monte-Carlo mean-field
   marginalization over unknown neighbors — explicitly flagged as an
   approximation, not exact CMI, per the task brief's tractability guidance).

9. **A4 continuation** (`code/cross_language_fixture.py`): a deterministic
   fixture for a future MATLAB/Octave run, since Octave remains uninstallable
   in this sandbox (checked fresh this session; see `V1_RECORD_AUDIT.md`).

10. **I — figures** (`code/make_figures.py`): audit_figA through audit_figH,
    PNG+PDF, written to `figures/`.

No parameter, threshold, or protocol value was retuned after seeing any of
the above results. The interpretation-gate decision in
`MECHANISM_AUDIT_RESULTS.md` was made once, from the Part D numbers, before
Parts E-H were run for any purpose other than the pre-planned characterization
above.
