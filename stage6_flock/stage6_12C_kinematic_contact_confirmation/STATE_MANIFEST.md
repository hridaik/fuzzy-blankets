# Stage 6.12C — State Manifest

Same qualification rule as Stage 6.12/6.12B, reused unmodified in
`code/world_sampling_612c.py`: material lineage exists
(`ForwardMaterialTrace611`, Jaccard≥0.30), size in [20,80],
`DWELL_WINDOW=20` steps of clean continuation (no split/merge flag)
immediately preceding qualification, torus-aware displacement ≥
`3.0×R_PRIMARY=2.7`, `h_star = ROT_CCW[bearing_to_cardinal(...)]`.
Qualification depends only on the trace's own history up to `t0` —
never on any Stage 6.12C intervention outcome, none of which exist at
world-sampling time.

## Seed ranges (disjoint from all prior stages)

- **Pilot** (excluded from inference, used only for runtime
  benchmarking): 63000-63099. One seed tried (seed 63000), qualified
  immediately (5.5s).
- **Confirmatory**: 63200-63499. Disjoint from seeds 500-504, Stage
  6.12's 61200-61399, Stage 6.12B's 62200-62399, and the pilot range.

## Confirmatory sample: 10/10 seeds tried qualified

| state_id | seed | t0 | size | h_star | displacement |
|---|---|---|---|---|---|
| s612c_00_seed63200 | 63200 | 55 | 40 | 0 | 2.75 |
| s612c_01_seed63201 | 63201 | 30 | 33 | 0 | 2.86 |
| s612c_02_seed63202 | 63202 | 38 | 27 | 0 | 2.77 |
| s612c_03_seed63203 | 63203 | 46 | 32 | 1 | 2.84 |
| s612c_04_seed63204 | 63204 | 90 | 41 | 1 | 2.93 |
| s612c_05_seed63205 | 63205 | 72 | 34 | 0 | 2.95 |
| s612c_06_seed63206 | 63206 | 119 | 66 | 3 | 5.05 |
| s612c_07_seed63207 | 63207 | 75 | 47 | 3 | 4.49 |
| s612c_08_seed63208 | 63208 | 88 | 61 | 2 | 4.25 |
| s612c_09_seed63209 | 63209 | 123 | 73 | 2 | 3.61 |

Every seed tried in the confirmatory range qualified on first attempt
(10/10) — no state was excluded, skipped, or resampled because a
preliminary intervention looked difficult, per the task brief's own
prohibition. All 10 states are used for the K=1 exhaustive primary and
K=2 secondary arms. **The duration-safety sub-study (d=8 vs d=24) uses a
PREDECLARED subset: the first 5 states by seed order**
(`s612c_00`..`s612c_04`), fixed before any intervention was simulated
(see `run_confirmatory_612c.py`'s `DURATION_SUBSTUDY_N_STATES=5`).

## Disclosed scope reduction

The task brief's full design calls for N_STATES=20. This run uses
**N_STATES=10** (2× Stage 6.12B's n=5, but a real, disclosed reduction
from the brief's ask) — approved in advance because per-step simulation
cost (~0.13-0.14s/step, confirmed again by this stage's own pilot
timing: 4.32s/rollout at d=8, 6.38s/rollout at d=24, matching the
~4.2s/8.4s brief estimates closely) made the full N_STATES=20 design's
estimated compute infeasible in one session once the K=1 exhaustive
(20 candidates × 12 streams), K=2 secondary (26 pairs × 6 streams), and
duration sub-study arms were all included at full brief-specified
per-candidate coverage. See `README.md` for the full reduction table and
measured total runtime.

Full per-state metadata (exact bird IDs, positions, headings, pool
membership, detector context) is in `data/state_manifest_612c.json`.
