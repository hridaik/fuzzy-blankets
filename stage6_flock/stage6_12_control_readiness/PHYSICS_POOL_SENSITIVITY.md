# Stage 6.12 — Physics-Assisted Pool Sensitivity (S17)

## Method

On a predeclared subset (the first 3 development states, `s612_00`,
`s612_01`, `s612_02` — chosen by ascending state index, not by any Phase-A
outcome), `run_pool_sensitivity_612.py` compares:

- **PRIMARY**: `blind_pool_611.nearest_M_pool` (position-only nearest-20).
- **SECONDARY**: `intervention_api_611.near_exterior` (true-`R` oracle pool,
  `radius_factor=3.0`) — described here as "physics-assisted," never as
  "blind," matching the task brief's explicit instruction.

at the frozen primary search budget (`K=4, d=8`), with `K`, `d`, outcome
definition, and physics-stream count matched (`N_STREAMS=3`); only the
candidate pool differs. `N_SETS_POOL=6` random sets per pool per state (a
disclosed reduction from a full best-found search — sufficient to compare
achievable `G_sus`/spread between pools, not to duplicate the full
Phase B/C pipeline for a second pool).

## Question

Does modest knowledge of interaction physics (the true `R`) materially
change the amount of achievable selectivity/susceptibility, compared to a
pool built from positions alone?

## Results

| state | pool | pool size | mean Δ (paired vs. own no-control) | between-set var |
|---|---|---|---|---|
| s612_00 | primary (nearest-20) | 20 | +0.0318 | 0.00054 |
| s612_00 | secondary (oracle, true-R) | 9 | +0.0125 | 0.00028 |
| s612_01 | primary | 20 | +0.0022 | 0.00000 |
| s612_01 | secondary | 22 | -0.0011 | 0.00002 |
| s612_02 | primary | 20 | -0.0886 | 0.07629 |
| s612_02 | secondary | 17 | -0.0138 | 0.07252 |

Note the SECONDARY (physics-assisted, true-`R`) pool is not a superset or
fixed-size relative of the primary nearest-20 pool — its size varies with
local density (9, 22, and 17 birds across the three states tested, vs. a
constant 20 for the primary pool), since `near_exterior` is a radius rule
(`3×R` of any interior member), not a count rule.

## Interpretation

Effect sizes are small and NOISY in both pools (`N_SETS_POOL=6` sets ×
`N_STREAMS=3` streams — a small sample, disclosed above), and neither pool
shows a consistently larger `G_sus` than the other: primary is larger in
magnitude at `s612_00` and `s612_02`, essentially tied at `s612_01`. The
one large-magnitude cell (`s612_02`, both pools strongly negative, ~0.076
between-set variance in both) shows the SAME qualitative pattern in both
pools, suggesting whatever drives that state's outcome is not specific to
knowing the true interaction radius.

**On this small, predeclared 3-state check: modest knowledge of
interaction physics (the true `R`) does not materially change the
achievable susceptibility/selectivity landscape**, compared to the
position-only nearest-20 pool. This is consistent with — and reinforces —
`MECHANISM_ANALYSIS.md`'s finding that static `t0` proximity (which is
what BOTH pools are built from, just with different cutoffs) is a weak
discriminator of success; sustained contact persistence over the forcing
window, not which withheld-radius definition selects the initial
candidate set, appears to be the more relevant unknown.

**Caveat**: 3 states, 6 sets, 3 streams per pool is a small, disclosed
sample — this result should be read as "no large sensitivity detected at
this precision," not as a definitive equivalence claim.
