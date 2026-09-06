# Stage 5 — moving-interface Markov-blanket steering: summary & audit log

Hypothesis under test: a persistent interior can be steered from one stable state to
another while the identities of its blanket variables change, provided a compact
low-leakage screening interface continues to exist throughout the transition.
Stages 1-4 were treated as read-only dependencies (`core.py` imported, never modified).

**Final patch (see `data/final_patch_log.txt` for full detail):** three focused
corrections were applied after this summary was first written: (1) Figure 6 was
replaced by `fig6_revised.py`, which visualizes membership among *minimum-cardinality*
delta-acceptable boundaries (via `integrity.K_delta`) instead of arbitrary |B|<=3
zero-leakage supersets; (2) Figure 8 was replaced by `fig8_revised.py`, comparing
task-only against genuinely organization-penalized control (lambda_org=1 and a newly
run lambda_org=100 case) rather than the original lambda_org=0 non-comparison; (3) a
new controller unit test (`stress_test.py`) swept the interface timescale tau_z over a
64x range and confirmed the pathwise-integrity constraint never activates at the
primary delta=0.01 (strengthening the baseline robustness finding), then found and
demonstrated genuine constraint-driven behavior change at a deliberately stringent
unit-test threshold (delta_unit=1e-6), producing `fig12_constraint_activation`. All
three changes are additive to the code (new optional `tau_z`/`rtol`/`atol` parameters
with baseline-preserving defaults) and did not alter any previously-computed baseline
number; pre-patch figures are preserved in `figures/pre_patch_backup/`.

## Code map

| File | Sections | Status |
|---|---|---|
| `core5.py` | 1-3: endpoint A/B, Omega(z), exhaustive separators | done, verified |
| `integrity.py` | 4: Lambda_K, K_delta | done, verified |
| `reference.py` | 5: p*_{y,z} | done, verified |
| `dynamics.py` | 6-7: moment ODEs, D_org | done, verified |
| `quasistatic.py` | 8: oracle boundary handoff | done, verified |
| `rate_induced.py` | 9: rate-induced loss (negative control) | done, verified |
| `control.py` / `control_sweep.py` | 10-14: 4 control formulations | baseline (32 runs) complete; rho_z/lambda_org/convergence running in background |
| `finite_data.py` | 15-19: finite-data discovery/certification | demo scale complete; full scale running in background |
| `fig1.py`-`fig11.py`, `make_contact_sheet.py` | figures | all 11 + contact sheet generated from saved data |

All numerical logs are under `stage5/data/*_log.txt` / `*.csv` / `*.npz` / `*.json`.

## What is proved analytically

- Omega(z) = I + L_{W(z)} is PD for all z in [-1,1]: W(z) is a nonnegative combination
  of two nonnegative-weight graphs, so L_{W(z)} is a graph Laplacian (PSD), hence
  Omega(z) = I + PSD has eigenvalues >= 1 (Section 3).
- For fixed deterministic y(t), z(t), the 8-node process is an exactly Gaussian
  (time-varying-coefficient Ornstein-Uhlenbeck) process, so (m_t, Sigma_t) obey the
  stated linear moment ODEs exactly, with no closure approximation (Section 6).
- mu*(y,z) = v(z) y is the exact solution of the constrained QP min 1/2 mu'Omega mu
  s.t. c'mu=y (KKT stationarity derived and numerically cross-checked to 1e-8; Section 5).
- The endpoint-A state (y=-1,z=-1, m=mu*(-1,-1), Sigma=Sigma*(-1)) is an exact fixed
  point of the uncontrolled moment ODEs (residuals <1e-9, machine precision; Section 6).
- D_org is the exact Gaussian KL divergence D_KL(p_t || p*_{y_t,z_t}); nonnegativity is
  the standard Gibbs/KL inequality (numerically spot-checked, not re-derived; Section 7).

## What is established numerically at population level

- Endpoint A reproduces `core.Omega0` bit-for-bit (max diff ~1e-16); B_A={4,5} is the
  UNIQUE minimum exact separator (Section 1).
- Endpoint B, built ONLY via the 4<->6 permutation, has unique minimum exact separator
  B_B={5,6}, interior unchanged (Section 2).
- The z-sweep exhaustive check reproduces the spec's numerical spot-checks essentially
  exactly: L_min,|B|=2(z=0) = 0.02983839764 (diff 2e-12), L_min,|B|=2(z=+-0.5) =
  0.00830386820 (diff 2e-13) (Section 3).
- Quasi-static boundary handoff reproduces the {4,5} -> {4,5,6} -> {5,6} transition
  exactly on the tested grid (Section 8, `fig2`).
- **Rate-induced loss (Section 9) is real but small, and NON-monotone in ramp
  duration** — see anomaly log below. This nuance was only caught by extending beyond
  the spec's requested duration set; reported per the audit requirement to retain
  unexpected results.
- Control formulations A-D (Section 10-14, baseline rho_z=1, 32 runs, all complete):
  SLSQP with a 12-knot piecewise-linear parameterization and 3 predetermined starts
  (zero / linear ramp / physics-informed front-loaded pulse) finds "best found" (never
  claimed globally optimal) protocols. Two robust, reportable findings:
  - **T=0.5 is empirically near-infeasible** under the tested optimizer budget: the
    task requires c^Tm(T)=1 exactly, but the interior mean's relaxation toward
    mu*(y,z) is rate-limited by Omega(1)'s slowest eigenvalue (=1, i.e. relaxation
    time constant 1), so a half-time-constant horizon cannot close the gap even with
    aggressive pushes (spot-checked up to amplitude 10; residual c^Tm(T) stayed <0.7).
    This is reported as a genuine finding, not silently patched.
  - **max_t Lambda_3(t) stayed far below delta=0.01 in every single baseline run**
    (typically 1e-6 to 1e-5), i.e. formulations B/C/D essentially never bind in this
    system at these horizons — task-only control is ALREADY pathwise-safe here. This
    is consistent with Section 9's finding that rate-induced leakage is small at these
    nondimensional rates (tau_x=tau_z=1). No artificial dissociation between D_org and
    Lambda_3 was found either (fig8) — reported as observed, not manufactured (matches
    the fig8 spec instruction not to force a dissociation that the model doesn't produce).
- **20-knot vs. 12-knot convergence check (formulations A and C, T in {1,2}, coordinated,
  all now complete)**:

  | config | 12-knot E | 20-knot E | 12-knot y(T)/cM(T) | 20-knot y(T)/cM(T) |
  |---|---|---|---|---|
  | A, T=1 | 29.68 | 21.45 | 1.50 / 0.44 | 1.22 / 0.40 |
  | A, T=2 | 8.59 | 8.86 | 1.00 / 1.00 | 0.90 / 0.96 |
  | C, T=1 | (T=1 not in baseline C grid at this rho/lambda) | 5.13 | — | 0.61 / -0.00 |
  | C, T=2 | 8.59 (via B/C near-identical to A at T=2) | 8.76 | ~1.00 / ~1.00 | 1.02 / 1.00 |

  T=2 is reasonably stable across knot counts (energy and task residuals agree to
  ~5-10%). **T=1 is NOT converged**: 20 knots finds a substantially different ("best
  found") solution than 12 knots, and neither satisfies the task constraints tightly
  (cM(T) is 0.40-0.44, far from the target 1.0). This corroborates the T=0.5
  near-infeasibility finding above — T=1 sits close enough to the same relaxation-rate
  limit that its "solution" is parameterization-sensitive, not a reliably converged
  optimum. T=1 results should be read as illustrative, not as certified best-found
  protocols.

## What is demonstrated only under finite Gaussian data

- Section 15: Euler-Maruyama trajectories vs. moment-ODE oracle — errors are MC-noise
  dominated at n_paths=500 (~0.03-0.05), not clearly resolving a dt-convergence trend;
  a larger n_paths would be needed to isolate discretization bias from sampling noise.
- Section 16, demo scale (R=15, n in {50,200}): exact recovery of the PLANTED
  I={1,2,3},B={4,5} via bias-corrected-CMI + simple accept/tie-break discovery was
  LOW (0% at n=50, 7% at n=200) — see anomaly log.
  **Full scale (R=100, n in {50,200,1000}), now complete**: exact-recovery rate
  0% (n=50), 10% (n=200), 24% (n=1000) — improves with n but remains low even at
  n=1000, confirming (with much better statistics) that the simple threshold/tie-break
  discovery rule under-recovers the planted partition; a per-candidate
  bootstrap-certified search (as in Stage 2 Part E) would likely do better but was not
  implemented here (see anomaly log item 2).
- Section 17, demo scale (n_ens=400/checkpoint, selection/validation split): boundary
  identity matched the oracle argmin at 4/5 z-checkpoints; Lambda_3 validation RMSE
  ~0.0076 (comparable to delta=0.01 itself — finite-n noise is not negligible relative
  to the certification tolerance).
  **Full-scale companion (Section 18's shared-path ensemble, n_ens=1000/checkpoint,
  now complete)**: Lambda_3 validation RMSE dropped to ~0.00093, an order of magnitude
  tighter, showing the RMSE is genuinely sample-size-limited rather than reflecting a
  bug.
- Section 18, demo scale: single-realization simultaneous 95% bootstrap band covered
  the oracle Lambda_3(t) trajectory; repeated-ensemble empirical coverage was 5/5=100%
  over only 5 realizations — too few to distinguish from the nominal 95%.
  **Full scale (n_paths=1000, n_boot=2000, n_outer=40), now complete**: single-
  realization band again covered the oracle trajectory at all 201 checkpoints
  (max band half-width ~0.041); repeated-ensemble empirical coverage was 40/40=100%
  over 40 independent realizations. With this many realizations, 100% coverage against
  a nominal 95% target is itself notable — it suggests the bootstrap band is
  conservative (over-covers) in this regime rather than under-covers, which is the
  safer direction for a certification tool but means the band is likely wider than
  necessary here; this was NOT tuned or investigated further.
- Fig 11 (finite-data pathwise classification, using a deliberately tighter
  delta_fig11=1e-5 chosen ONLY to create a nontrivial two-class problem, since no
  protocol tested violates the primary delta=0.01). **Full scale (40 realizations/cell,
  matching finite_data.py's n_outer; N_BOOT=500, N_CHECK=20), now complete**:
  true-violated protocols were classified correctly 100% of the time (40/40) at every
  n in {50,200,1000}; true-INTACT protocols were classified as "violated" 100% of the
  time (0/40 correct) at every n up to 1000 — identical to the earlier 6-realization
  demo, now confirmed with an order of magnitude more realizations, so this is a
  robust finding rather than small-sample noise: **at delta=1e-5, finite-sample
  certification could never confirm intactness at any tested sample size**, because
  bias-corrected CMI estimation noise at n<=1000 exceeds 1e-5. Reported as observed,
  a genuine limitation of certification at very tight tolerances, not tuned away.

## What remains untested

- Nonlinear/multi-agent generalization: nothing here tests more than one steered
  interior, competing interiors, or nonlinear (non-Gaussian) blanket structure.
- **True global optimality of any control solution** — only "best found" over 3 SLSQP
  starts is claimed anywhere. The 12-vs-20-knot cross-check (`--stage convergence`,
  now complete, see table above) shows T=2 is reasonably knot-count-stable but T=1 is
  NOT, so T=1 "best found" solutions should not be read as converged. A genuinely
  different optimization method (derivative-free/global-style cross-check, as the spec
  also recommends) was NOT run in this session — this remains untested.
- rho_z sensitivity {0.25,4} and the lambda_org grid for formulation D: **now
  complete** (68 total control_sweep results in `control_results.jsonl`); not yet
  folded into `fig7.py`/`fig9.py`, which still only plot the baseline rho_z=1,
  lambda_org=0 grid (see note at the bottom of this file).
- Full-scale finite-data replicate counts (R=100, n=1000, n_outer=40): **now
  complete**, results folded into the sections above.

## Anomaly / discrepancy log

1. **Section 9 non-monotonicity.** The spec's requested duration set {0.25,...,8} shows
   a clean monotone decrease of max_t Lambda_3 with ramp duration, matching the stated
   hypothesis. Extending to a finer grid (0.02 to 8) reveals the true relationship is
   NON-monotone: leakage peaks at T_ramp~0.2 and DECREASES again as T_ramp->0, because
   an instantaneous jump leaves the covariance too close to endpoint A, where {4,5,6}
   is already an exact size-3 separator. The spec's primary set happens to start just
   past this peak, so its own reported trend is correct but incomplete; `rate_induced.py`
   and `fig3` now report both the primary set and the finer diagnostic grid.
2. **Section 16 discovery accuracy is low** (0-7% exact recovery of the planted
   I/B at n=50-200, demo scale) under the simple threshold+tie-break discovery rule
   (`tau_discovery=0.02`, prefer min|B| then max|I|). This is a documented
   simplification of what a full per-candidate bootstrap-certified search (as in
   Stage 2 Part E) would do; the exhaustive-tripartition machinery itself is exact,
   but the accept/reject threshold was not calibrated per-candidate. Reported as a
   genuine finite-data limitation rather than tuned away.
3. **Control task infeasibility at T=0.5** (and marginal feasibility at T=1): see
   above. Not silently changed; T=0.5 remains in the sweep and is reported as
   near-infeasible under the tested optimizer/knot budget.
4. **Fig 11 delta choice.** delta=0.01 (primary) produces zero true-violation cases in
   this system across all tested protocols, so a separate delta_fig11=1e-5 was used
   purely to construct a two-class classification benchmark; this does not change any
   delta=0.01 result elsewhere and is documented at the top of `fig11.py`.
5. **Optimizer tolerances loosened for tractability**: `solve_ivp` in `control.py` uses
   rtol=1e-5/atol=1e-7 during optimization (vs 1e-8/1e-9 in `dynamics.py`/`quasistatic.py`)
   purely for SLSQP wall-clock budget; the DENSE post-hoc revalidation in
   `control.optimize_protocol` re-simulates each accepted solution at `N_CHECKPOINTS_DENSE=60`
   with the same tolerances — a genuinely tighter revalidation pass was not run
   separately in this session; flagged as a residual gap vs. the spec's "dense grid
   significantly denser than control-knot grid" requirement (60 vs 12 knots satisfies
   the density requirement; the tolerance itself was not separately tightened).

## Status of the background runs

All four queued runs are now **complete**:
`control_sweep.py --stage baseline` (32), `--stage rho_z` (16), `--stage lambda_org`
(20), and `--stage convergence` (4) — 72 total jobs in `stage5/data/control_results.jsonl`
— plus `finite_data.py --scale full`, whose results are folded into the sections above
and saved to `stage5/data/finite_data_results.json` / `finite_data_log_full.txt`.

Any of the `control_sweep.py` commands below can still be re-run safely at any time
(they skip already-completed jobs and are a no-op if nothing changed); `finite_data.py
--scale full` will fully re-run from scratch if invoked again (it only writes its
results at the end, not incrementally):

```
python3 stage5/control_sweep.py --stage all --workers 8   # verifies/completes all 4 control stages
python3 stage5/finite_data.py --scale full                # re-runs from scratch (no incremental checkpoint)
```

**Figures updated to use the full-scale data** (all now regenerated):
- `fig7.py` (cost of integrity) now has 3 rows: baseline grid, rho_z sensitivity
  (coordinated only, T in {1,2}), and lambda_org sensitivity (formulation D only,
  T in {1,2}).
- `fig9.py` (phenotype-only vs coordinated) now has a second row showing how the
  coordinated/phenotype-only energy and leakage gap changes with rho_z.
- `fig10.py` (finite-data recovery) replicate count raised from 20 to 100 per (n,z) to
  match `finite_data.py --scale full`'s R=100.
- `fig11.py` (finite-data classification) raised from 6 to 40 realizations/cell
  (matching `--scale full`'s n_outer=40), N_BOOT 100->500, N_CHECK 10->20.

Note: figures 1-6 and 8 were already population-level or baseline-grid figures and did
not need regeneration for "full scale" — see the per-figure notes above.
