# Stage 6.6 — Collective Landscape

Additive track. Does not modify `python/flock_sim/`, `v1_mechanism_audit/`,
`v2_interface_control/`, `v3_refinement/`, `stage6_5/`, or any prior
`interactive_demo/` tab (adds one new subtab inside "Inference & Identity";
imports reusable library code from prior stages unmodified — see PLAN.md
"Reused, unmodified"). Stage 6 and 6.5 are frozen evidence; nothing here
changes their numbers, figures, or conclusions.

## Why this stage exists

Stage 6/6.5 characterized *one* interior (`I_0`, later inferred boundaries,
lineage-tracked identities) but never asked a more basic question: what
makes a `k`-sized subset of this flock look and behave like an individuated
collective at all, as opposed to an arbitrary patch of a globally aligned
system? Stage 6.6 answers this by computing four deliberately-uncollapsed
coordinates — visual/internal **coherence** (`C`), internal **predictive
integration** (`G`), budgeted **blanket leakage** (`L`), and local
**inside/outside contrast** (`D`) — for thousands of candidate `k=20`
interiors per snapshot, and lets you explore the resulting landscape
interactively.

This is flock-specific exploratory work, not a proposed universal
definition of biological individuality or agency. Every document below says
so explicitly wherever the metrics are introduced.

## Reading order

1. `PLAN.md` — scope decisions made before any code ran.
2. `PROTOCOL_6_6.md` + `configs/protocol_6_6.yaml` (hashed) — the frozen
   landscape-generation protocol, written after the controlled-archetype
   sanity check and before the full candidate landscape.
3. `METRIC_VALIDATION.md` — the gate: do the four metrics behave as
   qualitatively expected on controlled archetypes, before any UI polish?
4. `RESULTS_6_6.md` — the ten final scientific questions (task brief
   section 36), answered against the real landscape data.
5. `../interactive_demo/STAGE6_6_VISUALIZATION_NOTES.md` — the demo tab's
   design rationale and per-field data provenance.

## Layout

```
code/
    common_66.py           shared constants, lattice/shell helpers, resize_to_k
    metrics_66.py           C_I, JSD/D_local, external entropy, directional opposition
    predictive_cache.py     the mask cache; G_i/L_i/G_I/L_I
    windowed_data.py        W=10/R=100 past-only local regime dataset builder
    candidates.py           5-method candidate-interior generator
    boundary_search.py      greedy + one-swap B*_K(I) selection
    archetypes.py           control conditions A-E, opposite-heading geometry,
                             farthest-point exterior selection, balanced rotation
    landscape.py            per-candidate Phi(I) assembly + Pareto attach
    pareto.py               optional (C,G,-L,D) nondominance filter
    run_landscape.py        one snapshot's full candidate landscape (CLI)
    run_all_snapshots.py    batch driver, all 15 primary snapshots
    run_archetype_validation.py   fixed-I0 archetype + f_E-sweep trajectories
    run_illustrative_trajectories.py  curated (~10) full-heading-playback
                             trajectories spanning (C,G,L,D) and the five
                             control scenarios, for demo Control-mode animation
                             (not an exhaustive re-run -- see its own docstring)
    export_demo_data.py     shapes data/ into interactive_demo/data/collective_landscape_bundle.json
    make_figures.py         Figures 6.6-1..4
    analyze_results.py      cross-snapshot summary table backing RESULTS_6_6.md
configs/    protocol_6_6.yaml (+ .sha256)
data/       seed{2,3,4}__{condition}__fE1.00__t20.{json,csv} (15 snapshots),
            archetype_trajectories.json, illustrative_trajectories.json,
            snapshot_manifest.json, results_summary.json
figures/    fig_6_6_1..4 (.png + .pdf)
tests/      pytest -- metrics, geometry, predictive-metric machinery, control;
            qa_report.md -- demo QA transcript (interactive_demo/, not the
            science pipeline)
logs/       run_all_snapshots.log, run_archetype_validation.log,
            run_illustrative_trajectories.log
```

## Running

```bash
cd stage6_flock/stage6_6_collective_landscape/code

# one snapshot
python3 run_landscape.py --seed 2 --condition no_control --n 5000

# all 15 primary snapshots (seeds 2/3/4 x 5 regimes, control-end, f_E=1.0)
python3 run_all_snapshots.py

# fixed-I0 archetype sanity check + f_E budget sweep trajectories
python3 run_archetype_validation.py

# curated full-heading-playback trajectories for demo Control-mode animation
python3 run_illustrative_trajectories.py

# figures (reads data/ only, does not re-run the simulator)
python3 make_figures.py

# demo data bundle
python3 export_demo_data.py

# tests
cd ../../  # stage6_flock/
python3 -m pytest stage6_6_collective_landscape/tests/ -q
```

## Demo

Rebuild the interactive demo after `export_demo_data.py` (adds the new
"Collective Landscape" subtab under Inference & Identity):

```bash
cd ../interactive_demo
python3 app/build.py
```
