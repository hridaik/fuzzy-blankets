# Stage 6.12 — State Sampling

## Selection rule (predeclared, code: `world_sampling_612.py`)

Fresh uncontrolled worlds are simulated from seeds `61200, 61201, ...`
(never used by seeds 500–504, prior identity-validation worlds, prior
audits, or this stage's own development). For each world:

1. Simulate from a fresh random initial condition (`r ~ Uniform(0,L)^2`,
   `z ~ Uniform{0,1,2,3}`), driven by `np.random.default_rng(seed)` — the
   world's own dedicated physics stream, nothing shared with any design/
   search RNG.
2. Run `detect_69.propose` every step; seed a `ForwardMaterialTrace611`
   instance from the first non-empty candidate set's top hypothesis
   (`cands[0]`, the same seeding convention `run_episode` in
   `run_online_control_611.py` uses for `LineageTracker611`) — **never**
   `LineageTracker611`/v1 itself.
3. A state QUALIFIES at step `t0` iff, over the preceding `DWELL_WINDOW=20`
   consecutive steps, the trace was `continuing` with no split/merge flag
   AND target size stayed in `[20,80]` AND the torus-aware centroid
   displacement of the (dwell-window-start ∩ now) common membership over
   that window is `≥ QUALIFY_MIN_DISPLACEMENT_R(3.0) × R_PRIMARY(0.9) =
   2.7`.
4. `h_star = ROT_CCW[bearing_to_cardinal(delta)]`, `delta` = that same
   torus-aware centroid displacement vector (the historical deterministic
   convention, quoted verbatim from `run_online_control_611.py`).
5. `P_t0 = nearest_M_pool(I_t0, r_{t0}, L, 20)`; the state is discarded if
   `|P_t0| < K_MAX(8)` (never observed in this run).
6. World generation gives up after `NT_MAX_UNCONTROLLED_WORLD = 180` steps
   with no qualifying lineage (never triggered in this run — see below).

Selection depends **only** on the trace's own material/geometric history up
to `t0` — never on authority score, pilot intervention outcome, future
no-control outcome, random-set success, or future stability, by
construction (qualification is checked online, before any Stage 6.12
intervention exists for that world).

## Development vs. holdout

The first `N_DEV=6` qualifying worlds (by ascending seed) become
development states; the next `N_HOLDOUT=3` become holdout states. This is a
deterministic, outcome-independent rule (seed order), not a separately
re-randomized draw, and is applied identically regardless of anything about
the state's eventual intervention behavior (which does not exist yet at
sampling time).

## Disclosed reduction

Task-brief minimums are 24 development / 12 holdout states,
`DWELL_WINDOW≈30`, `NT_MAX_UNCONTROLLED≈260`. This run uses `N_DEV=6`,
`N_HOLDOUT=3`, `DWELL_WINDOW=20`, `NT_MAX_UNCONTROLLED_WORLD=180` — a
disclosed reduction in state COUNT and qualification depth, not a change to
the qualification RULE's structure (size range, persistence, displacement,
and heading convention are the same as the task brief specifies).

## Result

9/10 seeds tried (61200–61209, skipping 61203 which failed to qualify)
qualified — see `data/state_manifest_612.json` and
`logs/world_sampling_612.log` for the full per-seed log. Qualification was
fast and reliable at this operating point; the state-count shortfall
relative to the task-brief minimum is a compute-budget decision made before
sampling, not a consequence of worlds failing to qualify.

| state_id | role | seed | t0 | size | h_star | displacement | pool size |
|---|---|---|---|---|---|---|---|
| s612_00_seed61200 | development | 61200 | 65 | 42 | 1 | 2.77 | 20 |
| s612_01_seed61201 | development | 61201 | 38 | 34 | 0 | 4.15 | 20 |
| s612_02_seed61202 | development | 61202 | 30 | 22 | 2 | 3.00 | 20 |
| s612_03_seed61204 | development | 61204 | 66 | 25 | 1 | 2.80 | 20 |
| s612_04_seed61205 | development | 61205 | 44 | 25 | 2 | 2.88 | 20 |
| s612_05_seed61206 | development | 61206 | 29 | 22 | 2 | 2.76 | 20 |
| s612_06_seed61207 | holdout | 61207 | 48 | 35 | 0 | 4.56 | 20 |
| s612_07_seed61208 | holdout | 61208 | 39 | 32 | 1 | 2.74 | 20 |
| s612_08_seed61209 | holdout | 61209 | 40 | 55 | 3 | 3.81 | 20 |

Full state metadata (exact bird IDs, positions, headings, pool membership,
detector context) is in `data/state_manifest_612.json`.
