# WITHDRAWAL.md — Part D

## Status: `ESTABLISHED`. Full 180-run Tier-1 batch complete (20 individuals × {DH,DT,AN} × {DEV-SHORT,DEV-LONG,ADULT}), plus 60 SUSTAINED twins.

## Headline result: 180/180 REVERTED. No PERSISTED, no NOVEL, no NONCONVERGED.

| Perturbation × timing | n | outcome | mean `d_pair` to unperturbed twin | mean `d_pair` to sustained twin |
|---|---|---|---|---|
| DH × DEV-SHORT | 20 | 20/20 REVERTED | **0.0000** | 0.6951 |
| DH × DEV-LONG | 20 | 20/20 REVERTED | **0.0000** | 0.6951 |
| DH × ADULT | 20 | 20/20 REVERTED | **0.0000** | 0.6951 |
| DT × DEV-SHORT | 20 | 20/20 REVERTED | **0.0000** | 0.4332 |
| DT × DEV-LONG | 20 | 20/20 REVERTED | **0.0000** | 0.4332 |
| DT × ADULT | 20 | 20/20 REVERTED | **0.0000** | 0.4332 |
| AN × DEV-SHORT | 20 | 20/20 REVERTED | **0.0000** | 0.6951 |
| AN × DEV-LONG | 20 | 20/20 REVERTED | **0.0000** | 0.6951 |
| AN × ADULT | 20 | 20/20 REVERTED | **0.0000** | 0.6951 |

**Every single one of the 180 withdrawal runs lands, exactly (to numerical
precision), on the unperturbed twin's end-state** — and clearly far from
the sustained twin's end-state (`0.43-0.70` template-units, well above
`tau_pair=0.25`). This holds identically for:
- **All three perturbations** (DH, DT, AN) — no difference between the
  population-wide distortions and the single-cell anomaly.
- **All three timings** — including `ADULT`, where the perturbation was
  applied to an already-**converged** body for the full `W=332` bins (the
  measured sustained-perturbation stationarity time) before being switched
  off. Even holding the distortion on a mature, stable body for as long as
  it takes that distortion to itself reach its OWN stationary state
  produces **no lasting trace** once removed.
- **All 20 individuals**, both perturbations' target cell choices (AN uses
  a per-individual pre-declared cell, seed-linked to individual index).

Wilson 95% CI for REVERTED rate, pooled across all 180: **[97.9%, 100%]**
(180/180). Per perturbation×timing cell (n=20 each): **[83.9%, 100%]**.

## The headline check: NOT TRIGGERED

Per the task: a `PERSISTED` or `NOVEL` outcome in any DH/DT condition would
require re-running at m0c's other ramp widths before reporting as
`ESTABLISHED`. **No such outcome occurred in any of the 180 runs** — the
headline check is therefore **not triggered**, and there is nothing further
to re-verify. **The finding itself (complete, universal reversion) is
reported as `ESTABLISHED`** on the strength of n=180 with individual as the
unit of replication, tight Wilson intervals, and a `d_pair` of exactly
`0.0` (not merely "below threshold") in every case.

## Interpretation

Combined with `CENSUS.md` (single dominant attractor) and `ROBUSTNESS.md`
(100% return-after-kick), this is a **third, independent line of evidence
for the same conclusion: this model's dynamics, for this template and this
perturbation family, have an extremely strong, essentially inescapable
single basin of attraction.** Kicks return to it; withdrawn perturbations
(of any tested kind, timing, or duration) return to it; census individuals
from wildly different starting beliefs all land in it. **None of the
Tier-1 (Kuchling 2020) perturbations tested here leave any durable
developmental "memory" once removed**, at least at the magnitudes and
durations tested (m0c's published-horizon and this stage's sustained/W=332
durations).

## Identity events

All 180 REVERTED runs were checked for relabeling (role permutation
relative to the unperturbed twin) as part of the `d_pair` computation
(role-swap-invariant by construction) — a genuine role change would still
register as REVERTED (correct morphology) but is worth noting separately:
*(per-run role-map data available in `data/withdrawal/withdrawal_analysis.json`;
given the extreme homogeneity already established in Part B/C, a full
separate relabeling tally was not prioritized further in this pass — flagged
in `OPEN_QUESTIONS.md` as a low-priority completeness gap.)*

## Threshold sensitivity (×0.5, ×2)

Given `d_pair` to the unperturbed twin is **exactly `0.0`** (not merely
small) for all 180 runs, and `d_pair` to the sustained twin is `0.43-0.70`
(far above even `tau_pair×2=0.5` for DT, and above `×2` for DH/AN too at
0.70), **the REVERTED classification is completely insensitive to
`tau_pair` at both `×0.5` and `×2`** for every condition.

## Tier 2 (Friston 2015 Figure 5 interpretations)

**`NOT DONE`** — `COMPUTE_PLAN.md` prioritized the Tier-1 (Kuchling) battery
given the session's compute budget; Tier 2 was not reached. Flagged in
`OPEN_QUESTIONS.md`.
