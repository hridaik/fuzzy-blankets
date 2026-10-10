# Stage 6.12 — Identity and Disruption (methodology; results filled in after Phase A/B/C complete)

## What is measured

For every rollout (Phase A random-set, Phase B search, Phase C holdout),
`intervention_612.outcome_metrics` reports:

- `V` (0/1): strict identity validity through the release-evaluation window
  `[t0+d, t0+d+24]` — every frame in that window must be `continuing` with
  no gap.
- `event`: `none | lost_dead | unresolved | candidate_split_or_merge_
  interruption`, with `+split_flag`/`+merge_flag` suffixes when
  `ForwardMaterialTrace611`'s own split/merge advisory flags fired anywhere
  from `t0` through the end of the window (never silently absorbed into
  `continuing`).
- `n_split_flags`, `n_merge_flags`, `n_unresolved_steps` — full counts over
  the whole traced rollout, not just the release window.
- `target_size_end` — target size at the last traced frame.

`J = V · A_release_late` is the strict-control-utility convention: **a high
raw `A_release_late` with `V=0` is reported as "high behavioral response
accompanied by identity failure," never as successful identity-preserving
control** (task brief Example C). Raw `A_release_late` and `V` are always
reported as separate columns in `data/phaseA_results_612.json` /
`data/phaseBC_results_612.json` so this distinction is auditable rollout by
rollout, not just in aggregate.

## Aggregate identity-valid fraction and split/loss rates

Per (state, K, d) cell: `identity_valid_fraction` = mean `V` across all
sampled sets × streams; loss/split/unresolved counts are broken out by
`event` label. See `READINESS_MAP.md` for the full grid and
`figures/budget_map_*.png` for the per-state and aggregate heatmaps (a
dedicated split/loss-probability panel, `1 - identity_valid_fraction`, is
included precisely so a state cannot be reported as "behaviorally
addressable" while silently hiding a high disruption rate).

## Results

**Phase A (1,296 intervention rollouts, all 24 K×d cells, 9 states)**:
identity-valid fraction (`V=1` through the whole release-evaluation window)
ranged 0.94–1.00 across every cell (full table in
`data/analysis_summary_612.json`), with a pooled event breakdown:

| event | count | % |
|---|---|---|
| `none` (clean continuation) | 813 | 62.7% |
| `confirmed_split` (flagged, but `V` still 1) | 446 | 34.4% |
| `lost_dead` | 11 | 0.8% |
| `confirmed_merge` | 8 | 0.6% |
| `candidate_split_or_merge_interruption` (`V=0`) | 6 | 0.5% |
| other split/merge-flag combinations | 12 | 0.9% |

**Split events are common (34%) but strict identity validity is NOT the
bottleneck at this budget/duration regime** — `ForwardMaterialTrace611`'s
split handling continues on the larger daughter by absolute retained
count and keeps `V=1` in the overwhelming majority of split cases; only
~1.3% of rollouts (17/1296) actually drove `V` to 0 (`lost_dead` +
`candidate_split_or_merge_interruption` + its flag combinations). Merges
are rare (0.6%).

**Phase C (holdout confirmation, K=4,d=8)**: every evaluated `S_star`
remained identity-valid (`V=1`, i.e. `identity_valid_fraction=1.00`) on
every one of 5 holdout streams, for every one of the 9 states — the
selectivity results in `SELECTIVITY_ANALYSIS.md` are therefore about
BEHAVIORAL alignment differences, not identity survival differences,
at this budget.

## Conclusion for this stage

The near-zero `G_sus`/`G_sel` headline findings (`READINESS_MAP.md`,
`SELECTIVITY_ANALYSIS.md`) are **not** explained by identity failure — the
material target survives forcing at this budget/duration regime the large
majority of the time. Whatever limits behavioral control here, it is not
primarily organizational disruption of the tracked lineage.
