# Stage 6.12 — Readiness Map (Phase A, full K×d grid)

**9 states** (6 development, 3 holdout), **24 K×d cells each** (216 cells
total), **3 random actuator sets × 2 CRN-paired physics streams per cell**
(6 paired `Delta_r(S,b)` observations per cell; 1,296 intervention rollouts
total, plus 18 full-length no-control rollouts, 2 per state). See
README.md's reduction table for why these counts are far below the task
brief's nominal Monte Carlo budget — this is a genuinely reduced-power
survey, and every number below should be read with that in mind (the 90%
CIs make the resulting uncertainty explicit rather than hiding it).

## Headline number

Across all 216 (state, K, d) cells: **`G_sus` (mean CRN-paired `Delta`) =
+0.0011, 90% bootstrap CI [-0.0083, +0.0107]** — indistinguishable from
zero. There is **no evidence, at this budget/state sample, that a typical
random exterior forcing set generically moves the material target's
persistent alignment**, in either direction.

## By budget (mean over all 9 states; full table in
`data/analysis_summary_612.json["summary"]["by_budget"]`)

| K | d=1 | d=2 | d=4 | d=8 | d=16 | d=24 |
|---|---|---|---|---|---|---|
| 1 | +0.005 | +0.004 | -0.000 | -0.013 | -0.012 | -0.008 |
| 2 | +0.022 | +0.031 | +0.031 | -0.007 | -0.003 | -0.006 |
| 4 | +0.005 | +0.002 | -0.010 | -0.025 | -0.022 | -0.018 |
| 8 | +0.041 | +0.018 | +0.010 | -0.021 | -0.001 | +0.005 |

(cell values = mean `G_sus` across the 9 states, each already a mean over 3
sets × 2 streams = 6 paired replicates)

**No clean inert → selective → generic/saturated progression is visible in
this table.** If anything, the pattern is the opposite of monotone: short
forcing durations (`d ≤ 4`) show small positive means at `K ∈ {2,8}`, while
`d ∈ {8,16}` are flat-to-negative across every `K`, and `d=24` partially
recovers. Given the effect sizes here are smaller than this run's own
per-cell noise (6 paired replicates per state, 54 total per row/column
cell), **this table should be read as "no reliable budget-progression
signal detected," not as "forcing hurts at long duration."** A negative
mean at n=54 paired replicates with this much between-replicate variance is
not distinguishable from zero without a much larger Monte Carlo budget than
this run affords — see `NEXT_STAGE_RECOMMENDATIONS.md`.

## Between-set variance (selectivity signal, before holdout confirmation)

Mean between-set variance ranges from ~0.00005 (`K4_d2`) to ~0.022 (`K8_d1`)
— see the full `by_budget` table for every cell. The largest between-set
variances cluster at **short forcing durations with larger `K`** (`K8_d1`:
0.0219; `K2_d4`: 0.0169), i.e. exactly where `G_sus` is also weakly
positive. This is DEVELOPMENT-level evidence only; whether it survives
held-out confirmation is answered in `SELECTIVITY_ANALYSIS.md`, not here
(23/216 cells were provisionally labelled `possible_selectivity_signal_dev_
only` by the classifier in `analysis_612.py` — see that file's docstring
for the exact, predeclared-but-heuristic threshold; this label is
descriptive of Phase-A-only evidence and is explicitly NOT the task brief's
`selective_addressable` category, which requires held-out confirmation).

## Identity-valid fraction

High throughout: 0.94–1.00 across essentially every cell (full table in
`data/analysis_summary_612.json`). Splits are common as ADVISORY flags
(`confirmed_split` fired on 446/1296 = 34.4% of rollouts) but rarely
downgrade `V` to 0 — see `IDENTITY_AND_DISRUPTION.md`.

## Figures

`figures/budget_map_aggregate.png` (3-panel: mean `G_sus`, mean
between-set variance, mean identity-valid fraction, averaged across all 9
states) and `figures/budget_map_<state_id>.png` (4-panel per-state: `G_sus`,
between-set variance, identity-valid fraction, split/loss probability) —
split/loss cells are never smoothed or hidden; hatched cells mark
`K > |pool|` unavailability (never triggered in this run, all pools were
size 20 ≥ K_max=8).
