# Stage 6.12B — State Manifest

Same qualification rule as Stage 6.12 (`world_sampling_612b.py` reuses the
core logic of `stage6_12_control_readiness/code/world_sampling_612.py`
unmodified in structure): material lineage exists (`ForwardMaterialTrace611`,
Jaccard≥0.30), size in [20,80], `DWELL_WINDOW=20` steps of clean
continuation (no split/merge flag) immediately preceding qualification,
torus-aware displacement ≥ `3.0×R_PRIMARY=2.7`, `h_star =
ROT_CCW[bearing_to_cardinal(...)]`. Selection depends only on the trace's
own history up to `t0` — never on any Stage 6.12B intervention outcome
(which does not exist at sampling time).

Fresh seed range **62200–62399**, never overlapping Stage 6.12's
61200–61399, seeds 500–504, or prior audits. 5/5 seeds tried qualified
(62200–62204) — see `logs/world_sampling_612b.log`.

| state_id | role | seed | t0 | size | h_star | displacement |
|---|---|---|---|---|---|---|
| s612b_00_seed62200 | development | 62200 | 77 | 66 | 0 | 4.73 |
| s612b_01_seed62201 | development | 62201 | 135 | 58 | 1 | 3.53 |
| s612b_02_seed62202 | development | 62202 | 51 | 46 | 2 | 3.62 |
| s612b_03_seed62203 | holdout | 62203 | 77 | 22 | 1 | 3.14 |
| s612b_04_seed62204 | holdout | 62204 | 29 | 27 | 1 | 2.85 |

## Disclosed reduction

Task-brief practical target: ≥12 development / ≥6 holdout. This run uses
3 development / 2 holdout (5 total) — see `README.md`'s reduction table
and `EXPERIMENT_SPEC.md`'s compute plan for why.

## Sub-experiment coverage

- **6.12B-A (exhaustive fixed-set)**: runs on a further-restricted subset
  of 3 states — `s612b_00`, `s612b_01` (development), `s612b_03`
  (holdout) — because exhaustive search is the dominant compute cost
  (~39 min/state measured). Disclosed in `run_fixed_set_exhaustive_612b.py`
  and `FIXED_SET_EXHAUSTIVE_RESULTS.md`.
- **6.12B-B (refreshed access)**: runs on all 5 sampled states.

Full per-state metadata (exact bird IDs, positions, headings, pool
membership, detector context) is in `data/state_manifest_612b.json`.
