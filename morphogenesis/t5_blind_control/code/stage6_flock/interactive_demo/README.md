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
metric shown), `UX_REFINEMENT_LOG.md` (what changed in the most recent
Control-view presentation/UX refinement pass and why),
`STAGE6_5_VISUALIZATION_NOTES.md` (the `Inference & Identity` mode's first
four tabs: what each tab's graph is built from, which examples were chosen
and why, and the regressions/bugs found and fixed while building it),
`STAGE6_6_VISUALIZATION_NOTES.md` (the 5th tab, "Collective Landscape":
same, for the Stage 6.6 candidate-interior landscape),
`STAGE6_8_9_VISUALIZATION_NOTES.md` (the 6th tab, "Dynamic Interfaces":
Stage 6.8's time-varying interface and Stage 6.9's translation pilot —
the representative-episode selection rule, data provenance, the
deterministic replay and its integrity assertions, and what is
deliberately not shown), `STAGE6_10_VISUALIZATION_NOTES.md` (the 3rd
internal view of that same tab, "6.10 Steering & release": the Part L
clarity-trajectory selection rule, what is inferred vs what is a
reference/oracle overlay, the replay assertions, and the scope caveat),
and `VISUAL_CONSISTENCY_AUDIT.md` / `VISUAL_CONSISTENCY_PASS.md` (a later
visual-consistency / information-architecture pass across the whole demo —
shared design tokens, "View settings"/"Filters" popovers, copy tightening;
no simulation data, metric definitions, or scientific conclusions changed).

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
    STAGE6_5_VISUALIZATION_NOTES.md  Inference & Identity tabs 1-4: design, provenance, bug log
    STAGE6_6_VISUALIZATION_NOTES.md  Inference & Identity tab 5 (Collective Landscape): design, provenance, bug log
    STAGE6_8_9_VISUALIZATION_NOTES.md  Inference & Identity tab 6 (Dynamic Interfaces): selection rule, replay provenance, what is not shown
    STAGE6_10_VISUALIZATION_NOTES.md   Inference & Identity tab 6, 3rd view (6.10 Steering & release): Part L clarity trajectory, inferred vs reference, scope caveat
    data/
        export_scenarios.py     generates every scenario bundle from the
                                 real simulator (the ONLY place trajectories
                                 are computed)
        verify_bundles.py        independently recomputes every bundle's
                                  summary statistics from its raw arrays and
                                  checks them against the embedded values
        export_refinement_bundle.py  exports a compact summary of Stage
                                  6.5 + Stage 6.5-refinement results (reads
                                  only already-saved data/*.json under
                                  stage6_5/, computes nothing) for the
                                  "Full statistics" Details sections
        derive_refinement_viz_data.py  derives lattice/graph-ready data
                                  (shared node positions/edges, per-flock
                                  role sets, one representative
                                  intervention example, one fixed identity
                                  trajectory) for Inference & Identity tabs
                                  1-4's main graphs -- see
                                  ../STAGE6_5_VISUALIZATION_NOTES.md for
                                  field-by-field provenance
        *.json                   one bundle per (flock, method, target)
                                  scenario (see schema below)
        refinement_bundle.json   Details-section table data (tabs 1-4)
        refinement_viz_data.json  tabs 1-4's graph-ready data
        stage6_8_bundle.json     tab 6 / "6.8 Dynamic flock": L0/L2/L3 frames
                                  and the control episode. Generated by
                                  ../../stage6_8_dynamic_interactions/code/
                                  export_demo_data_68.py
        stage6_9_bundle.json     tab 6 / "6.9 Translation pilot": the
                                  specified model (gate failed) and the
                                  labelled off-spec diagnostic. Generated by
                                  ../../stage6_9_translating_collective/code/
                                  export_demo_data_69.py
        stage6_10_bundle.json    tab 6 / "6.10 Steering & release": one
                                  continuous timeline (emergence -> control ->
                                  release) for Stage 6.10's Part L clarity
                                  trajectory. Generated by
                                  ../../stage6_10_emergence_adaptive_control/
                                  code/export_demo_data_610.py
        collective_landscape_bundle.json  tab 5's data: candidate-interior
                                  landscape (per snapshot) + archetype
                                  control trajectories + curated
                                  illustrative real-trajectory examples,
                                  written by
                                  stage6_6_collective_landscape/code/export_demo_data.py
                                  (not part of this directory's own data/
                                  pipeline -- see ../STAGE6_6_VISUALIZATION_NOTES.md)
        manifest.json            lists every flock/method/target combo and
                                  which scenario id it maps to
    app/
        index.html               authored source (HTML/CSS/JS), with
                                  `/*__DEMO_DATA__*/`, `/*__REFINEMENT_DATA__*/`,
                                  `/*__REFINEMENT_VIZ__*/`, and
                                  `/*__LANDSCAPE_DATA__*/` placeholders
        build.py                  inlines data/*.json into the placeholders,
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

## Inference & Identity mode

A second top-level mode (alongside the Control view described above),
reached via the `Inference & Identity` button in the top nav — redesigned
(2026-09-07) to explain each Stage 6.5 result primarily through the same
10x10 node-graph visual language as the Control view (bird positions,
heading arrows, halos/rings, hover tooltips), with tables/plots demoted to
collapsible "Full statistics" sections rather than the primary explanation.
See `STAGE6_5_VISUALIZATION_NOTES.md` for full provenance of every derived
quantity, which examples were chosen and why, and the regressions/bugs
found and fixed during the redesign. Six tabs (the 6th, "Dynamic
Interfaces", was added later — see `STAGE6_8_9_VISUALIZATION_NOTES.md`).
Tabs 1-4 are each built
from `data/refinement_viz_data.json` (lattice-ready derived data; supporting
tables come from `data/refinement_bundle.json`) — both read only
already-saved `stage6_5/{boundary_inference,refinement/*}/data/*.json`, or
deterministic re-derivations of already-frozen quantities (documented
field-by-field in the notes doc); no simulation is re-run to make the
visualization prettier, no fabricated dynamics:

- **1. Predictive Boundary** — the canonical flock's core/inferred-boundary
  graph, a "Reveal true interaction shell" toggle, and a 5/10/20/50/100-
  trajectory sample-size slider that swaps the highlighted node set on the
  same graph (kept directly visible — it changes which boundary is actually
  shown). The IDs/Roles label toggle is purely a display choice and lives
  in a small "View settings" popover next to Reveal.
- **2. Causal Stress Test** — a representative flock (seed 20) with
  Included-shell/Omitted-shell/Non-shell selectors; perturbing the selected
  bird highlights its true lattice edges to the core birds it actually
  affects and shows before/after next-heading probabilities, with the
  direct causal effect and the predictive-loss penalty reported as two
  separate, explicitly non-comparable metrics. The non-shell negative
  control shows an exact-zero effect with no highlighted edges.
- **3. Prediction vs Control** — a 12-flock selector and a four-controller
  button group (Oracle/Inferred/Fiedler/Random) that swap actuator
  highlighting on the same graph, with the frozen benchmark's negative
  finding stated plainly below. The optional "redundant support" overlay
  (color-codes each core bird's actuated-neighbor count `m_i`) is a display
  encoding, not a different controller, so it lives in a "View settings"
  popover next to the controller buttons.
- **4. Collective Identity** — one fixed physical trajectory (flock 2,
  replicate 0) with a local timeline scrubber; switching the
  Material/Lineage/Functional lens changes only which birds are
  highlighted as "the collective," never the underlying headings. The
  Functional lens visibly collapses toward a documented ~1-bird remnant;
  an "Apply identity validity guard" toggle (enabled only for Functional,
  where it was actually built and calibrated) shows the guard holding a
  larger group while correctly flagging IDENTITY COLLAPSE / UNRESOLVED —
  nominal and identity-valid success are always shown as two separate
  values, never one checkmark.
- **5. Collective Landscape** (Stage 6.6) — built from
  `data/collective_landscape_bundle.json` instead of
  `refinement_viz_data.json`; see `STAGE6_6_VISUALIZATION_NOTES.md` for
  full design rationale, field provenance, and bug log. Two internal
  submodes:
  - **Explore** — a snapshot/regime selector (seed 2/3/4 x 5 control
    conditions, at control-end), the X/Y axis choice (the actual exploration
    question), and a Scatter/Sweep-grid toggle stay directly visible. Color
    encoding, size encoding, and the Pareto-only filter (default off, never
    a default visual emphasis) are purely visual and live in a "View
    settings" popover; the four independent per-metric range filters (never
    combined into one score) live in a "Filters" popover, with a
    "Filters · N active" count on its trigger and a one-click reset — this
    keeps the scatter/lattice pair the dominant visual instead of a wall of
    controls pushing them below the fold. The same lattice renderer used by
    tabs 1-4 shows the selected candidate's interior/selected-boundary/
    structural-shell/near-exterior/distant-exterior roles and real
    headings; a lightweight pin-and-compare (two candidates side by side);
    and data-driven "teaching case" shortcuts (only rendered when the
    current snapshot's actual candidate population contains a clear
    example).
  - **Control** — a fixed candidate (the seed's own established I₀ by
    default) with a local timeline scrubber over one of the five archetype
    control conditions (and, for the three exterior-control conditions, an
    exterior-budget of 25/50/75/100%); the lattice shows interior/actuated
    structural shell/actuated near-exterior roles exactly at every
    timestep. For 7 hand-picked (seed, condition) combinations (10 curated
    candidates total, chosen to span the C/G/L/D surface and all five
    control archetypes), real per-timestep heading arrows animate
    frame-by-frame through Play/step/scrub, exactly like the main Control
    tab — an "Example" selector appears when more than one curated
    candidate shares a regime, letting you compare e.g. the reference I₀
    against a visually-scattered-but-metrically-favorable alternative on
    the same physical trajectory. Everywhere else, real per-bird headings
    are shown only at the single instant the underlying data actually
    contains them, and omitted (not interpolated or fabricated) elsewhere
    — stated explicitly in the UI either way. Four compact live metric
    traces (C_I(t), G_I(t), L_I(t), D_local(t)) plus target fraction,
    external entropy, and control effort as secondary numbers — these
    reflect whichever candidate is currently displayed, not always I₀.

- **6. Dynamic Interfaces** (Stages 6.8 / 6.9) — built from
  `data/stage6_8_bundle.json` and `data/stage6_9_bundle.json`. Two internal
  views. **6.8 Dynamic flock**: one 20x20 lattice with real heading arrows and
  a condition selector (L0 fixed graph / L2 heading-dependent FOV / L3 FOV +
  hidden gates / Control), an interior selector (fixed reference I vs tracked
  collective I(t), the latter enabled only where a per-timestep track was
  actually stored), and four optional overlays — inferred predictive boundary,
  sampled causal interface, oracle causal interface, and the live directed
  interactions of a selected bird — all off by default. The Control view puts
  actuated nodes on the lattice and compares all six arms from the same start.
  **6.9 Translation pilot**: synchronized world-frame and co-moving-frame
  panels; the default is the *specified* model, whose feasibility gate failed,
  and the over-connected diagnostic is selectable behind a persistent
  "not a Stage 6.9 result" label. Representative episodes are chosen by an
  objective median rule, and the per-timestep headings the science runs did not
  persist are regenerated by a deterministic replay that is asserted equal to
  the frozen files. See `STAGE6_8_9_VISUALIZATION_NOTES.md`.
  **6.10 Steering & release** (Stage 6.10) — built from
  `data/stage6_10_bundle.json`. One episode on one continuous timeline
  (t = 0–99): natural emergence with the frozen blind detector's own output,
  then 24 control steps, then 16 free steps with control off. The episode is
  *not* chosen here — it is Stage 6.10's own Part L `clarity_trajectory`
  (median final H among the method arm's conjunctive successes; seed 7), whose
  declared rule and "illustration only" caveat are carried into the bundle and
  displayed. The lattice shows real heading arrows, the tracked collective with
  entered/left marking, and the actuated nodes at each step (an *inferred*
  object). The structural interface B_t and the exact-do interface are
  *reference* overlays, off by default, tinted like the 6.8 oracle toggles, and
  their sizes are not reported until switched on. A compact H*(I_t, t) trace
  puts control and release on one axis with the release half shaded and
  separated, so "steered" versus "merely pushed" is legible. A header caption
  carries the scope limit: the stratum where full-model control itself steers
  the collective, 7 of 12 episodes, one illustrative episode, no aggregate
  claim. No arm ranking is shown — Stage 6.10 establishes none. See
  `STAGE6_10_VISUALIZATION_NOTES.md`.

## Rebuilding after a data or science change

```
cd data && python3 export_scenarios.py     # regenerate trajectory bundles
python3 verify_bundles.py                   # independently check summary stats
python3 export_refinement_bundle.py         # refresh Details-table data
python3 derive_refinement_viz_data.py       # refresh tabs 1-4's graph-ready lattice data
cd ../../stage6_6_collective_landscape/code && python3 export_demo_data.py  # refresh tab 5's bundle
cd ../../stage6_10_emergence_adaptive_control/code && python3 export_demo_data_610.py  # refresh tab 6's 6.10 bundle
cd ../../interactive_demo/app && python3 build.py    # re-inline into build/index.html
```

`export_refinement_bundle.py` and `derive_refinement_viz_data.py` only need
rerunning after a `stage6_5/` science change (new `data/*.json` in
`boundary_inference/`, `refinement/causal_redundancy/`,
`refinement/control_generalization/`, or `refinement/identity_stability/`);
neither touches the V1-V3 scenario bundles above.
`derive_refinement_viz_data.py` additionally calls a handful of already-
frozen functions (`find_flock`, the identity `definitions.py` tracks, the
closed-form intervention propagator) to deterministically reproduce a few
full trajectories/probability vectors the frozen driver scripts summarized
before discarding — see `STAGE6_5_VISUALIZATION_NOTES.md` for exactly which
fields these are and why.

`export_scenarios.py` imports `flock_sim`, `v2_interface_control/code`, and
`v3_refinement/code` unmodified — it is presentation tooling, not a new
implementation of the model, and never overwrites V1/V2/V3 data. The one
exception, documented in full in `UX_REFINEMENT_LOG.md`: bundles now also
capture `natural_action_hist`/`applied_action_hist`/`overridden_hist` by
rerunning the identical frozen-protocol simulation (same seed, same
interventions) — a re-logging of an already-computed diagnostic, not a new
experiment, verified bit-identical by `verify_bundles.py`.
