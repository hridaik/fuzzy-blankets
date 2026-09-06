# UX_REFINEMENT_LOG.md

Log of this presentation/UX refinement pass over `interactive_demo/`. No
V1/V2/V3 scientific results, protocols, simulator behavior, or frozen
conclusions were modified — see "Data that had to be regenerated" below for
the one exception, which is a re-logging of an already-frozen protocol's
own diagnostic output, not a new experiment.

## New metrics added

Per bundle (`bundle.summary`), all computed from real trajectory arrays,
never inferred visually: `peak_actuators` (k_max), `bird_steps` (total
actuator exposure), `override_count` (actual decisions changed), two
exploratory `time_to_target` variants (dwell-3 and first-crossing, clearly
separate from the unchanged endpoint success definition), `recovery_time`
(V3's transition-aware integrity rule), `persistent` +
`final_post_release_Hstar`, `mean_multiplicity`, `gamma`, `gamma2`. Full
definitions and provenance: `METRIC_DEFINITIONS.md`.

## Is Sparse Interface Multicover actually faster, or merely cheaper?

**Answer, from the data now displayed in the demo: cheaper, not faster —
and the demo now says this explicitly rather than requiring the presenter
to infer it.** On the primary demo flock (seed 16, target = frozen protocol
direction), at the SAME actuator count (`k=9`):

| Method | k | This-run success | Time to target | Bird-steps | Ensemble P(success) |
|---|---|---|---|---|---|
| Random exterior | 9 | No | never | 180 | n/a |
| Connected patch | 9 | Yes | step 23 | 180 | **0.45** |
| Distributed shell | 9 | No (this run) | step 27 (after control ended) | 180 | **1.00** |
| **Sparse Interface Multicover** | **9** | **Yes** | **step 18** | **180** | **0.95** |
| V2 Conservative Shell | 12 | Yes | step 15 | 240 | 1.00 |
| Full Dynamical Shell | 16 | Yes | step 14 | 320 | 1.00 |
| Direct Core (inadmissible) | 20 | Yes | step 7 | 400 | n/a |

Reading down the "time to target" column at increasing budget (Direct Core
→ Full Shell → V2 Conservative → Our Method): **more actuators reach the
target faster.** Our Method is not an exception to this — it is
*slower* to converge than the two larger-budget admissible methods (Full
Shell, V2 Conservative), because it is deliberately using ~44–56% fewer
actuators. What it buys instead is a **smaller footprint at comparable
reliability**: 180 bird-steps and 9 peak actuators vs. 240–320 and 12–16,
at 0.95 ensemble success vs. 1.00 — a small, quantified reliability cost
for a real, quantified cost reduction. The demo's summary card and
"Compare all" table now show this trade-off directly rather than requiring
the presenter to eyeball it.

## Which methods share actuator count but differ in outcome?

The table above **is** the answer, and it is now the clearest single
illustration the demo can show: **four methods use exactly `k=9`
actuators on this flock/target — Random Exterior, Connected Patch,
Distributed Shell, and Sparse Interface Multicover — and their outcomes
range from complete failure to a 0.95 ensemble success probability.** This
is not actuator count driving the difference; it is *which 9 birds* and
*how redundantly they support the core* (Random Exterior isn't even in the
true interface; Connected Patch is, but concentrated; Distributed Shell is
random-from-the-correct-shell, and happened to fail on this one displayed
run despite a 1.00 ensemble rate — itself a useful, honest illustration of
why trajectory-level and ensemble-level numbers must never be conflated,
which is exactly why they're shown as two separate table sections in the
UI). This directly demonstrates the V3 finding the demo exists to
communicate: coverage *structure* (redundancy, distribution), not raw
count, determines outcome.

## Target/method combinations available

**Every (method × target) combination on the primary demo flock (seed 16)
is now precomputed and available** — 9 methods × 3 nontrivial targets (the
two 90° turns and the 180° opposite) = 27 real trajectories, replacing the
previous "only the default method supports target-switching" limitation.
The canonical seed-2 flock (used only for the dedicated V1-vs-V3 historical
comparison) intentionally keeps its single frozen-protocol target — it is
a fixed historical comparison, not a target-exploration surface — and its
target buttons are disabled with an explanatory note rather than silently
left active with no effect.

## Timeline bugs fixed

The previous version derived stage labels and slider range from
`bundle.markers` per-scenario, which was already dynamic in the code, but
every stage boundary, chart x-axis, and comparison-mode time range has been
rebuilt in this pass to read from a single `bundle.timeline` object
(`start/identify/control_start/control_end/release_end/nt_total`) with **no
literal numeric fallback anywhere in the JS** — verified by grep (no bare
`46`, `20`, or `41` timestep literals remain in the stage/timeline logic).
Compare mode now derives its shared slider range as
`max(nt_total_A, nt_total_B)` rather than assuming they match (they
currently always do, since compared methods share a flock and therefore a
`t0`/`T_u`/`T_r` — but the code no longer assumes this). Stage pills only
render for stages that exist in the selected bundle's own timeline.

## Data that had to be regenerated, and why

**One thing was regenerated**: every scenario bundle now also carries
`natural_action_hist` / `applied_action_hist` / `overridden_hist`, obtained
by rerunning `export_scenarios.py`'s simulations (same seed, same
interventions — nothing about the frozen protocol changed). These arrays
were always produced internally by `flock_sim.active_inference.step`; the
previous version of `export_scenarios.py` simply never captured them. This
is **not a new experiment** — `interactive_demo/data/verify_bundles.py`
independently recomputes every `summary` statistic (including
`override_count`) from the raw arrays now stored in each bundle and
confirms an exact match against the embedded values for all 30 bundles,
and the `headings`/`trajectory` arrays are bit-identical to what a run
without this capture would produce (same deterministic RNG stream). No
V1/V2/V3 frozen data file was touched; this only affects
`interactive_demo/data/*.json`.

A `V2_conservative_shell` method (V2's own frozen `f_A=0.75` policy,
DEG rule) was also added as a demo scenario so the V2-vs-V3 budget
trade-off requested for comparison could be shown directly — this reuses
V2's exact, unmodified policy definition, applied to the demo flock via the
same `evaluate_arm`-equivalent machinery already used throughout
`v3_refinement/`, not a new rule.

## Verification performed (Part 14)

- **Timeline**: all 27 primary + 3 canonical scenarios exercised via a
  jsdom-driven interaction sweep (every method button × every enabled
  target button, plus all 5 compare presets, plus manual flock/target
  switches in compare mode) — zero JS errors, zero "undefined"/"NaN" in
  rendered text.
- **Target**: every target button either loads a real precomputed
  trajectory or is disabled (current heading; canonical-flock alternate
  targets) — never both a live-looking button and a stale trajectory.
- **Metrics**: `verify_bundles.py` independently recomputes `success`,
  `persistent`, `peak_actuators`, `bird_steps`, `override_count`,
  `recovery_time_abs`, `time_to_target_dwell3_abs`, and `gamma2` from raw
  arrays for all 30 bundles — 30/30 match the embedded `summary`.
- **Comparisons**: all 5 default presets and free-form dropdown selection
  verified to only ever pair methods from the *same* flock (the UI's method
  dropdowns are repopulated from that flock's own method list on flock
  switch, so a mismatched pairing cannot be constructed through the UI).
- **HTML**: `build/index.html` re-verified after every change — no
  placeholder residue, valid embedded JSON, valid JS syntax (`node
  --check`), zero runtime errors under a full jsdom interaction sweep
  (browser rendering itself was not exercised — no headless browser could
  be installed in this sandbox without a system package install; a human
  should do a final visual pass).
