# Stage 6.12C — Statistical Analysis

## Independent generalization unit: the STATE

Every summary in this stage's documents is a STATE-LEVEL summary with
STATE-CLUSTERED uncertainty (bootstrap resampling of the 10 states, with
replacement, 20,000 resamples per quantity — `code/analysis_612c.py`'s
`state_clustered_bootstrap`), never a pooled-candidate-rollout or
pooled-stream computation treated as independent. This stage has:

- **n_states = 10** (K=1 primary and K=2 secondary arms; n=5 predeclared
  subset for the duration-safety sub-study).
- **n_candidates = 20/state** (K=1 exhaustive pool).
- **n_physics_streams = 12/candidate** (4 search + 8 confirmatory) for
  K=1; 6 confirmatory streams/pair for K=2; 6 paired confirmatory streams
  per candidate per duration for the duration sub-study.
- **n_rollouts**: 2,400 (K=1) + 1,560 (K=2) + 120 (duration, d=24 arm
  only, since d=8 values are reused from K=1) = **4,080 total simulated
  intervention rollouts**, plus 10×(12+6) ≈ 180 no-control baseline
  rollouts (some shared/reused across arms).

**Despite 4,080+ rollouts, this remains fundamentally an n≈10 state
study.** No result in this stage is reported as "significant" on the
strength of rollout count; every headline number is qualified by its
state-clustered CI, which is visibly wider than a naive rollout-pooled CI
would be (e.g., the L_pred ratio 90% CI spans [0.30, 8.33] at the state
level, vastly wider than any candidate-pooled CI computed from the same
4,080 rollouts would show).

## Runtime

- **Pilot**: 1 state (seed 63000, disjoint range 63000-63099, excluded
  from inference), used to benchmark per-rollout cost before committing
  to N_STATES. Measured: 4.32s/rollout at d=8, 6.38s/rollout at d=24,
  6.37s for a full no-control (8,24) trajectory — matching the ~4.2s/6.3s
  estimates from prior-stage timing logs closely.
- **Full confirmatory run**: `code/run_confirmatory_612c.py`, single
  process, 10 states, seeds 63200-63209 (10/10 qualified on first
  attempt). **Total wall time: 17,465.7s = 4.85 hours.** Per-state
  breakdown (`logs/run_confirmatory_612c.log`): K=1 exhaustive arm
  ≈1,000-1,080s/state; K=2 secondary arm ≈630-680s/state; duration
  sub-study (5 states only) ≈107-113s/state additional.
- This matches the pre-run estimate (~5.0-5.2h) closely, and comfortably
  cleared the ~6-7h soft ceiling — **N_STATES was NOT reduced below 10**
  after the pilot benchmark, per the process brief's own instruction.

## What is and is not claimed at this precision

**Established at this precision** (state-clustered CI excludes zero, or a
clean qualitative separation with non-overlapping CIs):
- The outcome oracle (non-deployable, per-stream best singleton) achieves
  mean ΔJ_conservative ≈6.9× the random/median candidate, with a 90% CI
  clearly separated from every other strategy tested
  (`ORACLE_DECOMPOSITION.md`). Real selective headroom exists in this
  action class.
- The forced-future contact oracle does NOT capture this headroom (mean
  below random, CI spanning zero and well below the outcome oracle's CI).
- K=1, d=8, single-actuator forcing does not show any elevated target-loss
  rate relative to d=24 in the 5-state duration sub-study (0% at both
  durations) — genuinely different from Stage 6.12B's K∈{2,4} finding.

**NOT established at this precision** (state-clustered CI spans zero):
- Whether the top-kinematic-predicted candidate reliably beats the median
  candidate in absolute ΔJ_conservative terms (L_pred's ratio summary
  looks favorable; the ratio-free absolute-difference summary does not —
  `K1_EXHAUSTIVE_RESULTS.md`).
- Whether the state-level Spearman ρ between C_hat_kin and held-out
  ΔJ_conservative is reliably positive (median +0.145, but CI
  [-0.035, +0.180]) — `PREDICTOR_VALIDATION.md`.
- Whether the top-predicted K=2 pair reliably beats random pairs
  (`K2_SECONDARY.md`).
- Whether direct-contact-at-t0, static distance, or the kinematic score
  add reliable incremental predictive value in a simple rank regression
  (`INCREMENTAL_VALUE_ANALYSIS.md`).

## Contextualizing magnitudes against the 0-1 utility scale

`J_conservative ∈ [0,1]`. The random-candidate baseline mean
ΔJ_conservative is ≈0.003 — three-tenths of one percentage point of the
full utility scale. Even the outcome oracle's much larger 0.022 mean is
still only ~2.2 percentage points of the 0-1 scale. For comparison: Stage
6.11's largest demonstrated paired schedule effect (seed 504, sustained
forcing) was +0.367 on the same scale; Stage 6.12's pooled `G_sus` was
≈+0.001-0.006; Stage 6.12B's exhaustive-search best-vs-random advantage
was +0.002 to +0.018. **This stage's random-candidate and top-predicted-
candidate effects sit at the very low end of this historical range, and
even the non-deployable outcome oracle does not reach Stage 6.11's
largest historical single-seed effect.** No effect reported in this stage
should be read as "useful control" without this context.

## Claims-discipline checklist (explicit, per task brief)

- The predictor was frozen (`PREDICTOR_FREEZE.md`) before any confirmatory
  rollout was analyzed and was never retuned after.
- No state was excluded after being seen (10/10 seeds tried qualified;
  see `STATE_MANIFEST.md`).
- `material_split_flag`/`material_merge_flag` are never called "confirmed"
  anywhere in this stage's documents.
- The forced-future contact oracle and the outcome oracle are both
  explicitly labelled non-deployable throughout, never presented as
  candidate methods.
- Tiny positive point estimates (e.g., L_pred's ratio-form median of
  1.23, or the K=2 top-pair's +0.011 mean lift) are always paired with
  their ratio-free/CI counterpart and the 0-1 scale context above, not
  reported as "useful" in isolation.
- 4,080+ rollouts are never used to substitute for the n≈10 state sample
  in any headline claim.
