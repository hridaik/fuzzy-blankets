# interactive_demo/ — Stage 6 interactive visualization

A presentation-quality, self-contained HTML page walking through the whole
Stage-6 story: emergence → identify collective → find the true interaction
interface → provide sufficient redundant support through it → retarget →
release. Every displayed trajectory is real output from the validated
Python simulator (`python/flock_sim/`) — nothing is reimplemented in
JavaScript. The browser only reads precomputed JSON, and every quantitative
comparison shown (cost, speed, reliability) is computed from real
trajectory/ensemble data, never inferred from how the animation looks.

See also: `METRIC_DEFINITIONS.md` (exact formula + provenance for every
metric shown) and `UX_REFINEMENT_LOG.md` (what changed in the most recent
presentation/UX refinement pass and why).

## Opening it

```
open build/index.html      # or just double-click it -- no server needed
```

The data is embedded inline in `build/index.html` at build time (see
"Rebuilding" below), so the file is fully self-contained and works from
`file://` with no CORS issues and no server. **If you edit `app/index.html`
directly, your changes will not appear until you rerun `app/build.py`** —
`app/index.html` is source; `build/index.html` is the runnable artifact.

## What you can do on the page

- **Step through or play** the flock's natural emergence, spontaneous
  collective identification, control, and release, with play/pause/step/
  restart/speed controls and keyboard shortcuts (Space, ←/→, R).
- **Pick a control method** from 9 options (No Control through Direct Core,
  including the frozen V3 "Sparse Interface Multicover" default) and any of
  3 target headings — every (method × target) combination on the primary
  demo flock is a real, precomputed trajectory; unavailable combinations
  (only relevant for the historical canonical-flock comparison) are
  disabled with an explanation, never silently mismatched.
- **Read a live summary card** for the current method: actuator cost, total
  control effort, actual override count, double-coverage, time to target,
  recovery time, persistence — trajectory-level numbers, clearly separated
  from ensemble (replicated) success probabilities where available.
- **Open the Compare view** (5 preset pairings, or free-form method/flock
  dropdowns) for a side-by-side split screen with shared-axis `H*(t)`/`C(t)`
  charts, per-method markers, and a side-by-side statistics table.
- **See a "compare all methods" table** for the current flock/target;
  clicking a row loads that method.
- **Click any bird** (inspect mode) to see its role, heading, and — for
  core birds — how many of its shell neighbors are Fiedler-boundary members
  or selected actuators.
- **Open "Methods & Metrics"** for a concise reference on every control
  method, boundary/interface definition, and metric — without leaving the
  page or reading a paper.

## Layout

```
interactive_demo/
    README.md                  this file
    METRIC_DEFINITIONS.md       exact formulas + data provenance for every metric
    UX_REFINEMENT_LOG.md        what changed in the latest UX pass, and why
    data/
        export_scenarios.py     generates every scenario bundle from the
                                 real simulator (the ONLY place trajectories
                                 are computed)
        verify_bundles.py        independently recomputes every bundle's
                                  summary statistics from its raw arrays and
                                  checks them against the embedded values
        *.json                   one bundle per (flock, method, target)
                                  scenario (see schema below)
        manifest.json            lists every flock/method/target combo and
                                  which scenario id it maps to
    app/
        index.html               authored source (HTML/CSS/JS), with a
                                  `/*__DEMO_DATA__*/` placeholder
        build.py                  inlines data/*.json into the placeholder,
                                   writes build/index.html
    assets/                  (reserved; the app is a single self-contained
                              file, so this is currently empty)
    build/
        index.html           the finished, self-contained artifact
```

## Data schema (per scenario JSON bundle)

Each bundle is ONE continuous, single-seed trajectory: natural emergence,
then the control window, then release, all under the flock's own discovery
seed (not a statistical average over replicates — see `single_run_disclaimer`
in every bundle, and the separate `ensemble` block for replicated
statistics where a matching one exists). Scenario ids follow
`{flock_id}__{method_id}__{target_id}`, e.g.
`seed16__sparse_interface_multicover__cw`.

```jsonc
{
  "scenario_id": "seed16__sparse_interface_multicover__cw",
  "flock_id": "seed16", "method_id": "sparse_interface_multicover",
  "method_label": "Sparse Interface Multicover", "method_subtitle": "Our refined controller (V3)",
  "method_short": "Our Method", "diagnostic_only": false,
  "target_id": "cw",                              // "cw" (frozen-protocol target) | "ccw" | "opposite"
  "initial_heading": 2, "target_heading": 0,       // 0..3 = up,down,left,right
  "lattice": { "L": 10, "nn": 100, "positions": [[row, col], ...] },
  "neighbors": { "0": [1, 10, 11], ... },          // Moore-lattice adjacency, all 100 birds
  "roles": { "core": [...], "dynamic_shell": [...], "fiedler": [...] },
  "actuators": [ ...bird ids forced during the control window... ],
  "timeline": { "start": 0, "identify": 6, "control_start": 6, "control_end": 26, "release_end": 46, "nt_total": 46 },
  "trajectory": [ [z_0..z_99], ... ],              // length nt_total+1, one row per timestep
  "control": { "natural_actions": [...], "applied_actions": [...], "overridden": [...] },  // length nt_total
  "metrics": { "Hstar": [...], "coherence": [...], "coverage": [...], "double_coverage": [...], "n_actuators_t": [...] },
  "summary": { "success": true, "persistent": true, "peak_actuators": 9, "bird_steps": 180,
               "override_count": 180, "time_to_target_dwell3_abs": 18, "recovery_time_abs": 6,
               "mean_multiplicity": 1.5, "gamma": 0.9, "gamma2": 0.5, ... },   // THIS RUN only
  "ensemble": { "available": true, "source": "v3_refinement/data/minimal_interface.json (q=2, gamma=0.5)",
                "success_probability": 0.95, "mean_actuators": 9, "n_replicates": 20 },  // population, if matched
  "why": "Succeeded: enough of the core received redundant target-consistent support...",
  "provenance": { "seed": 16, "protocol_version": "V3 (...sha256...)", ... },
  "single_run_disclaimer": "..."
}
```

Full definitions for every `summary`/`metrics` field: `METRIC_DEFINITIONS.md`.

## Scenarios included

**Primary flock (`seed16`, near-median success under the frozen V3
controller)**: 9 methods (`no_control`, `random_exterior`,
`fiedler_boundary`, `connected_patch`, `distributed_shell`,
`v2_conservative_shell`, `sparse_interface_multicover` — the default "Our
Method" — `full_dynamical_shell`, `direct_core_diagnostic`, marked
inadmissible) × 3 nontrivial targets (`cw` = frozen-protocol adjacent
target, `ccw`, `opposite`) = 27 real, precomputed trajectories.

**Canonical flock (`seed2` — the actual flock V1's original exhaustive
search ran on)**: `no_control`, `v1_best_pair` (birds 57+77, the best pair
from `v1_mechanism_audit/data/pair_synergy.json`, R_ij=0.16, p_success=0.0),
`sparse_interface_multicover` — same starting state, same target, same
horizon, for the dedicated "V1 vs V3" compare preset. This flock
intentionally keeps only its one frozen-protocol target (it is a fixed
historical comparison, not a target-exploration surface).

## Rebuilding after a data or science change

```
cd data && python3 export_scenarios.py     # regenerate trajectory bundles
python3 verify_bundles.py                   # independently check summary stats
cd ../app && python3 build.py               # re-inline into build/index.html
```

`export_scenarios.py` imports `flock_sim`, `v2_interface_control/code`, and
`v3_refinement/code` unmodified — it is presentation tooling, not a new
implementation of the model, and never overwrites V1/V2/V3 data. The one
exception, documented in full in `UX_REFINEMENT_LOG.md`: bundles now also
capture `natural_action_hist`/`applied_action_hist`/`overridden_hist` by
rerunning the identical frozen-protocol simulation (same seed, same
interventions) — a re-logging of an already-computed diagnostic, not a new
experiment, verified bit-identical by `verify_bundles.py`.
