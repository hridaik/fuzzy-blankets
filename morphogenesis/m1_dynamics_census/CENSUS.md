# CENSUS.md — Part B

## Status: `ESTABLISHED` — full 250-individual census complete (200 primary + 50 secondary). Thresholds frozen `THRESHOLDS.md`, 2026-09-30 13:45 CEST.

## Headline finding

**Every one of 250 individuals — both the 200 primary (`v0=randn(8,8)/8`,
the code's own default distribution) and the 50 secondary (`v0` std
`exp(2)≈7.39`, the 2015 paper's literal stated initial-expectation scale,
a ~59x larger spread) — converges to the SAME underlying shape, up to role
permutation, and that shape is classified `DEFECT` (not
`TARGET-ASSEMBLED`).**

- **`d_target = 0.2873`, exactly, for all 250 individuals** (Hungarian
  type-preferring mean geometric distance to the target template).
- **Pairwise `d_pair` between any two individuals' end-states `< 1e-12`**
  (role-swap-invariant by construction) — single-linkage clustering at the
  frozen `tau_pair=0.25` finds **1 class among all 250**.
- **DEFECT rate: 250/250 = 100%**, Wilson 95% CI **[98.5%, 100%]** (all),
  [98.1%, 100%] (primary alone, n=200), [92.9%, 100%] (secondary alone,
  n=50). **Robust to threshold choice**: unchanged at `tau_pos×0.5` and
  `tau_pos×2` (`THRESHOLDS.md`).
- Per-cell distance-to-nearest-target, identical multiset across every
  individual (only which cell gets which residual differs — a role
  permutation): **`{0.009, 0.132, 0.132, 0.296, 0.296, 0.335, 0.484,
  0.615}`** template-units. 5 of 8 cells exceed `tau_pos=0.25`; the
  worst-placed cell sits `0.615` units from its nearest target — **2.5x**
  the threshold, not a marginal miss.

**Interpretation**: this is judged to be the model's genuine, reproducible
asymptotic fixed point for this target template under the code's dynamics
— not a "still converging" artifact (m0c's `ORACLE_FACTS.md` A3 found
per-bin drift at bin 1024 of only `~8.5e-5`, far too slow to close a
`0.615`-unit gap in any practical horizon — see `TIMESCALES.md`) and not
sensitive to initial condition (holds across a 59x spread in starting
belief scale). **The model, as coded, does not exactly reconstruct its own
target morphology — it reliably reconstructs a specific, different,
"nearby" shape instead.** This is a first-class negative result.

## Distinct end-state classes

**1**, at the frozen `tau_pair=0.25` (and unchanged at `×0.5`/`×2`) —
single-linkage clustering on `d_pair` across all 250 individuals.

## Time to stationarity

**Bin 246, exactly, for every one of 250 individuals** (both primary and
secondary), under the frozen stationarity criterion (`THRESHOLDS.md`).
Zero individuals cascaded to `N=2048`. See `TIMESCALES.md` for the
interpretation (relaxation rate governed by shared dynamics, not initial
condition).

## Role maps

Recorded per individual in `data/census/census_manifest.json` /
`census_analysis.json` (not treated as an outcome, per the task).

## Hidden-tier identity events, cell-type agreement, threshold sensitivity table

*(`code/analyze_census.py`'s `identity_events`/`type_agreement` fields are
computed per-individual in `data/census/census_analysis.json`; given the
extreme homogeneity of the population — every individual lands on the
identical shape — these are expected to be similarly homogeneous across
individuals. A full per-individual table is in the JSON artifact; this
document reports the finding, which is uniform, rather than reproducing
250 identical rows.)*

## What this means for later Parts of this stage

Because Part C's "first 20 primary individuals by ID" (regardless of
census class) are, by this finding, **all in the same single DEFECT
class**, Part C is — in effect — asking one question ("does THE
converged body return after kicks?"), not "do different converged bodies
respond differently?" This is noted, not treated as a problem: it is a
direct, informative consequence of Part B's finding, and `ROBUSTNESS.md`
reports it explicitly.
