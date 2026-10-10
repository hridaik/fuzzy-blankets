# PROTOCOL_6_5.md

Frozen boundary-inference protocol for Stage 6.5 Part 1. Mirrors V1/V2/V3's
own convention: every threshold below was chosen from **development-flock
data only** (seeds 2, 3, 4 -- the first three of V3's frozen ten
`DEV_SEEDS`), before any held-out, bootstrap, or control-comparison number
was computed. The machine-readable, hashed copy is
`boundary_inference/configs/protocol_6_5.yaml`
(sha256 `e0d45adbb083a9ba5c9fb592de152ae7ffa872ea88e5b3224c030aa7ea9c4bdf`,
`configs/protocol_6_5.yaml.sha256`). Nothing in either file changed after
`data/held_out_evaluation.json`, `data/sample_efficiency.json`,
`data/bootstrap_membership.json`, or `data/control_comparison.json` were
produced.

## What was reused unmodified from Stage 6

- The simulator (`python/flock_sim/*`), `find_flock`/`dynamical_shell`
  (`v2_interface_control/code/common_v2.py`), the frozen dev/held-out flock
  pools (`v3_refinement/code/common_v3.py`), and the frozen V3 multicover
  controller law (`q=2`, `gamma=0.5`,
  `v3_refinement/configs/protocol_v3.yaml`). None of these were re-derived
  or re-tuned.

## Flock-pool scope (see PLAN.md for the full rationale)

- Boundary-inference development: seeds **2, 3, 4**.
- Sample-efficiency curve (Part 1.9): seed **2** (canonical flock) only.
- Held-out evaluation (Part 1.8/1.10, Part 2, Gate A): the first **3** of
  V3's six frozen held-out seeds.

## Trajectory generation

Pure baseline continuation from each flock's frozen `z_t0`: independent
stochastic replicates, no actuation, `n_time=15` steps each. Splits are at
the **trajectory level** (never timestep) -- `N_train=100, N_val=30,
N_test=30` for every dev/held-out flock condition; the sample-efficiency
curve varies `N_train` over `{5,10,20,50,100,200}` on the canonical flock
with `N_val=N_test=30` held fixed.

## Estimator (Part 1.4)

Nodewise regularized logistic regression: one classifier per interior bird,
features = one-hot(`X_I0,t`) + one-hot(`X_B,t`). Initially fit with
`sklearn`'s `lbfgs` (true multinomial); a dev-flock timing check found
`lbfgs` took 20-30s per 20-bird fit at this problem's scale (400 one-hot
features, ~1500 training samples, several interior birds' per-class design
matrix close to separable because the flock is already highly
heading-aligned by construction) -- `liblinear` (regularized one-vs-rest)
gave numerically indistinguishable held-out log-loss (0.0932 vs 0.0936-0.0939
across repeated `lbfgs` runs on the same data) roughly **40x faster**. This
is a solver/scaling substitution, not a change of estimator family or a
retreat from Part 1.4's "prefer a transparent predictive model" instruction
-- `liblinear` logistic regression is exactly as transparent, and was chosen
purely for tractability, documented here rather than silently.

## Candidate screening + greedy forward selection (Part 1.5/1.6)

1. **Screening**: every exterior bird is scored once by its single-candidate
   marginal held-out log-loss gain over the interior-only baseline
   (`shortlist_k=20` kept for the greedy step -- a compute-feasibility
   measure, not a structural filter: nothing is excluded a priori by
   position or identity).
2. **Greedy forward selection** over the shortlist, stopping when either the
   current boundary's excess loss over the full-exterior model is
   `<= delta_tol`, or the best remaining candidate's gain is `<= min_gain`.

**Stopping-threshold operationalization.** Part 1.5 asks for "delta relative
to the full predictor". A first attempt used a fixed absolute-nats
`delta_tol in {0.005, 0.01, 0.02}` (`data/dev_sweep.json`'s superseded round
1, not separately retained as a file -- reported here for the record): on
one dev flock (seed 3), the exterior's *total* available gain over
interior-only prediction was itself only ~0.005 nats, so every tested
absolute threshold was either trivially already satisfied at `B=empty` or
made little practical difference. This was reported honestly rather than
patched by picking a smaller absolute number by hand -- instead, the
threshold was **redefined as a fraction of each flock's own total gap**
(`interior_only_loss - full_loss`), so it adapts to how much signal a given
flock's exterior actually carries. `min_gain_frac = delta_tol_frac / 10`
throughout.

**Frozen values**: `delta_tol_frac = 0.05`, `min_gain_frac = 0.005`. Freeze
rule (pre-registered before this sweep ran): take the **tightest** value in
the tested grid `{0.6, 0.4, 0.2, 0.1, 0.05}`. Recovery (Jaccard against the
true `B^D`, revealed on dev flocks only for this diagnostic) improved
monotonically as the threshold tightened, with excess loss staying tiny
throughout (`<=0.0008` nats on two of three dev flocks, `-0.0002`
-- i.e. statistically indistinguishable from the full-exterior floor -- on
the third, at the frozen value). Untested, tighter values were not assumed
better and were not tried.

| `delta_tol_frac` | seed 2 (`|B_hat|`, Jaccard, excess) | seed 3 | seed 4 |
|---|---|---|---|
| 0.6  | 2, 0.17, 0.0098 | 1, 0.07, 0.0016 | 2, 0.12, 0.0107 |
| 0.4  | 3, 0.25, 0.0085 | 1, 0.07, 0.0000 | 2, 0.12, 0.0104 |
| 0.2  | 4, 0.33, 0.0034 | 1, 0.07, 0.0003 | 3, 0.18, 0.0017 |
| 0.1  | 5, 0.42, 0.0003 | 3, 0.21, 0.0005 | 3, 0.18, 0.0028 |
| **0.05 (frozen)** | **7, 0.58, 0.0006** | **3, 0.21, -0.0002** | **3, 0.18, 0.0008** |

(Full trace: `boundary_inference/data/dev_sweep.json`.)

## Bootstrap (Part 1.7)

`n_boot = 15` trajectory-level bootstrap replicates, resampling
`z_train` with replacement (never timesteps), rerunning the full
screen -> shortlist -> greedy pipeline on each replicate with the SAME
`delta_tol_frac`/`min_gain_frac` recomputed against the replicate's own
total gap. Run on the **canonical flock (seed 2) only** -- a documented
compute-scope reduction (see PLAN.md), not every dev/held-out flock.

## Null baselines (Part 1.10)

Fiedler `B^F` (`flock_sim.spectral.analyze_window`, `refclust=I0`, on a
`TW=5` window drawn from a held-out test trajectory -- itself never touching
the lattice, since it is Stage 6's own spectral method computed purely from
observed headings), a size-matched random exterior draw (20 draws,
mean/std reported), the full 80-bird exterior (the `Delta-ell=0` reference
by construction), and the oracle `B^D` (revealed only after `\hat B` is
frozen).

## Control comparison (Part 2)

Reuses the **frozen, unmodified** V3 multicover law (`q=2`, `gamma=0.5`,
`v3_refinement/configs/protocol_v3.yaml`), applied to an **inferred**
incidence graph (`boundary_inference/code/graph_inference.py`, itself
inference-side and lattice-free) built only from the already-frozen
`B_hat`. `q`/`gamma` are not re-tuned here, per Part 2.2's explicit
instruction. `n_replicates=20` per controller arm, matching V3's own
`N_REP`.

## What is NOT in this protocol

No V3 controller re-optimization of any kind (no new `q` search, no
Fiedler-threshold tuning, no schedule search) -- Part 8's explicit
prohibition. Those numbers are imported from `protocol_v3.yaml` as
constants.
