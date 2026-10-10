# PLAN.md — Stage 6.5 Refinement

Written before any refinement code ran. Mirrors `../PLAN.md`'s convention:
records scope decisions up front so later results can be checked against
intent, not rationalized afterward.

## What this refinement is and is not

It resolves three specific open questions Stage 6.5 raised but did not
settle (see `../STAGE6_5_SYNTHESIS.md`):

1. **Part A / Hard Gate A** — Stage 6.5's inferred boundary `B_hat` was shown
   *predictively* sufficient under natural trajectories. It was never
   stress-tested under intervention, so "observationally redundant" and
   "causally redundant" have not actually been distinguished for the birds
   `B_hat` omits.
2. **Part B / Hard Gate B** — inferred-boundary control beat null baselines
   on exactly one of three held-out flocks; the other two were uninformative
   by construction (too easy / already-known-hard for every arm). One
   discriminating flock is not a generalization claim.
3. **Part C / Hard Gate C** — adaptive identity definitions showed turnover
   in the hundreds and one near-single-bird collapse while still registering
   nominal success, with no way yet to tell genuine reorganization from
   detector jitter, and no anti-collapse guard.

It is **not** a re-optimization of the frozen V3 controller or the frozen
Part-1 inference pipeline. No new `q`/`gamma` search, no re-tuning of
`delta_tol_frac`/`shortlist_k`/the estimator family. Those stay exactly as
`../PROTOCOL_6_5.md` and `v3_refinement/configs/protocol_v3.yaml` froze them.

## Reused, unmodified

See `README.md`'s "What is reused, unmodified" section — the simulator,
`common_v2`/`common_v3`/`selection_rules_v3`, and every Part-1/Part-2/identity
module from `stage6_5/{boundary_inference,collective_identity}/code/`.

## Key finding that shapes Part A's design

`flock_sim.active_inference.step` factors as `action_i ~ Categorical(ut_i)`
then `z_new_i ~ Categorical(Bu[:, action_i])`. `Bu` does not depend on the
current state at all (a documented port simplification —
`active_inference.py`'s module docstring). `ut_i` is a deterministic softmax
function of `G[i, :]`, which depends on the current state **only through the
headings of bird `i`'s lattice neighbours** (`compute_G`: `nbr_heading =
z[nbr_ids]`). Consequently the one-step marginal `p(z_{i,t+1} | z_t) = Bu @
ut_i(z_t)` is an exact closed-form categorical, and a `do(z_j := z'_j)`
intervention changes it **iff `j` is a lattice-neighbour of `i`** — a
closed-form proof, not just an empirical one, that a true non-shell exterior
bird cannot affect any interior bird's one-step distribution. Part A's
`causal_redundancy/code/exact_intervention.py` computes `D_j^do` this way:
exact, not Monte Carlo, satisfying A4's "if the exact/MC distributions make
KL stable" condition by being exact. A small literal-rollout cross-check
(200 replicates) is still run and reported, since the task brief frames
exactness as conditional.

## Flock-pool / compute scope (fixed before any refinement code ran)

- **Part A**: the same 3 held-out flocks already frozen in
  `boundary_inference/data/held_out_evaluation.json` (seeds 17, 18, 20),
  reusing their recorded `B_hat`/`B^D` rather than re-running inference (A1's
  "do not refit"). Held-out natural states: 30 freshly generated test-split
  trajectories per flock, disjoint seed offset from Part 1's, one state per
  trajectory at a fixed checkpoint. Perturbation targets: all of `B_hat`, all
  of `B^D \ B_hat`, and a fixed 10-bird random sample of `E^D` (the
  identifiability claim for `E^D` is exact by construction — see above — so
  10 birds is a numerical sanity sample, not the evidence for that claim).
  All 3 alternative headings per (state, bird) — cheap under the closed-form
  approach.
- **Part B**: new seeds only, scan starts at 41 (first seed after V3's
  held-out pool of 17-40), predeclared max scan range 41-140. Discriminating
  criterion (`P_oracle >= 0.7`, `P_random <= 0.3`) frozen in
  `PROTOCOL_6_5R.md` before any inferred-controller run, scanned in seed
  order, stopping at 8-12 qualifying flocks or range exhaustion — reported
  either way, never loosened after seeing inferred results.
- **Part C**: re-evaluates the *same* physical trajectories Stage 6.5 already
  generated for dev flocks 2, 3, 4 (Part 4) and the canonical flock's Part
  5/6 episodes, regenerated deterministically from their recorded seeds
  (Stage 6.5 did not persist raw `z_hist` to disk, only summary JSON — see
  each script's docstring for the exact regeneration seed). The closed-loop
  re-run (C7) reuses Part 5's own scope: flocks 2 and 3, `N_REP=8`.

## Freeze points

Each part gets its own frozen section of `PROTOCOL_6_5R.md`
(+ `configs/protocol_6_5r.yaml`, hashed into `logs/`), frozen strictly before
that part's held-out/closed-loop numbers are computed:

- Part A's perturbation/metric design is frozen before any `D_j^do`/`Delta_shift`
  number is computed (there is no "development" sub-phase to tune here, since
  the metric is exact by construction, not fit to data).
- Part B's discriminating criterion and scan range are frozen before the
  seed scan runs, and the seed scan's output (`data/discriminating_flocks.json`)
  is frozen before any inferred/Fiedler controller is evaluated on it.
- Part C's `lambda_J`/`lambda_T` grid and the validity-envelope percentile
  rule are frozen (calibrated on uncontrolled dev-flock data only) before the
  closed-loop re-run (C7).

No threshold in `PROTOCOL_6_5R.md` changes after its corresponding freeze
point. If a later step needs a different number, that is reported as a
limitation, not silently patched in.
