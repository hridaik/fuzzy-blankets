# Stage 6.12B — Contact Predictor Analysis (S18/S19)

Three PRE-INTERVENTION predictors, aggregated per exhaustive set (sum over
`j in S` of each candidate's individual score), validated by Spearman
correlation against the realized paired `Δ(J_assoc)`/`Δ(J_conservative)`
from `data/fixed_set_exhaustive_612b.json` (1,260 set-cell rows, 3
states): **static t0 distance** (deployable), **kinematic predicted
contact** (deployable; physics-assisted true-R and radius-free variants),
**oracle no-control future contact** (audit-only, from the paired
no-control trajectory at the same physics_seed — never the forced
trajectory itself).

## Overall (pooled across all 3 states, 4 cells)

| predictor | ρ vs Δ(J_assoc) | ρ vs Δ(J_conservative) |
|---|---|---|
| static t0 distance | **-0.301** | -0.203 |
| kinematic (physics-assisted, true R) | **+0.227** | **+0.289** |
| kinematic (radius-free variant) | -0.084 | -0.100 |
| oracle no-control future contact | +0.018 | +0.158 |

## By state (ρ vs Δ(J_assoc))

| state | static | kinematic | kinematic (radius-free) | oracle |
|---|---|---|---|---|
| s612b_00 | +0.005 | +0.138 | -0.139 | +0.138 |
| s612b_01 | +0.124 | +0.299 | +0.404 | +0.180 |
| s612b_03 | -0.075 | +0.186 | -0.001 | -0.232 |

## By cell (ρ vs Δ(J_assoc), pooled across states)

| cell | static | kinematic | kinematic (radius-free) | oracle |
|---|---|---|---|---|
| K1_d4 | +0.536 | **+0.779** | +0.434 | **+0.777** |
| K1_d8 | -0.373 | -0.057 | +0.131 | -0.127 |
| K2_d4 | -0.153 | +0.050 | -0.150 | -0.164 |
| K2_d8 | -0.553 | **+0.434** | -0.193 | -0.009 |

## Interpretation

**The physics-assisted kinematic predictor is the most consistently
positive of the three** — positive overall (ρ≈0.23-0.29), positive in
every one of the 3 states individually (+0.14 to +0.30), and positive (or
near-zero) in 3 of 4 cells. This is the strongest, most reproducible
signal in this analysis: a simple, deployable, no-future-truth predictor
built from current position/heading/known speed and the TRUE interaction
radius shows a real, if modest, relationship with realized paired
intervention effect.

**Static t0 distance is NEGATIVELY correlated overall** (-0.30) —
counter to the naive expectation that closer-at-t0 actuators help more,
and a striking reversal from Stage 6.12's original (uncorrected, absolute-
outcome) finding that distance barely mattered. This should not be
over-read given the small state count, but it is at minimum further
evidence (alongside `CONTACT_EFFECT_REANALYSIS.md`) that **static t0
proximity is not a reliable, sign-stable predictor of intervention
effect** in this system.

**The radius-free kinematic variant performs much worse than its
physics-assisted counterpart** (-0.08 vs +0.23 overall) — removing
knowledge of the true interaction radius substantially degrades this
predictor, at least in the specific "mean predicted distance" form used
here. A different radius-free formulation might do better; this result
does not rule that out, only this specific construction.

**The oracle predictor does NOT dominate** the deployable kinematic
predictor (+0.018 vs +0.227 overall) — surprising for a nominal "upper
bound." The most likely explanation, disclosed as a genuine limitation of
this stage's oracle CONSTRUCTION (not a claim that no better oracle could
exist): `oracle_future_contact_scores` predicts contact using the PAIRED
NO-CONTROL trajectory's future, which is exactly correct only insofar as
the forced trajectory does not itself diverge from the unforced one during
the prediction window — but forcing K birds changes the flock's own
dynamics, so the "no-control future" is systematically a worse guide to
"what will actually happen under forcing" than the kinematic predictor's
purely LOCAL, short-horizon extrapolation. **This oracle should be read as
an upper bound on 'contact if nothing about the intervention perturbed the
system,' not as a true global upper bound on achievable contact under
forcing** — a caveat that matters for `NEXT_STAGE_DECISION.md`.

## Caveat

n=3 states, and the by-cell/by-state breakdowns show real sign
instability (e.g., K1_d8's overall -0.06 masks nothing consistent; oracle
is positive for 2 states and clearly negative for the third). This
analysis identifies the physics-assisted kinematic predictor as the most
promising lead worth testing at a larger, properly powered scale — it does
NOT establish it as validated.
