# Stage 6.7 — Blind Boundary & Causal Interface

Can a useful boundary — and then a causal interface — be recovered for an
arbitrary flock interior **without ever supplying inference code the
simulator's Moore-neighbour graph**? Builds directly on Stage 6.6's
candidate-interior landscape, replacing its oracle-`S(I)`-constrained
boundary with one inferred purely from observed heading trajectories and
active interventions.

See `PLAN.md` for scope and the reused/new code inventory, `PROTOCOL_6_7.md`
+ `configs/protocol_6_7.yaml` for the frozen parameters, and `RESULTS_6_7.md`
for the findings.

## Layout

```
code/       inference-side + evaluation-side modules and run_*.py drivers
configs/    protocol_6_7.yaml (+ .sha256)
data/       per-snapshot graphs, panel, oracle-validation, sweep results
figures/    fig_6_7_1 .. fig_6_7_5 (PNG + PDF)
tests/      firewall AST/runtime test + unit tests
logs/       timing pilot, pipeline run logs
```

## The firewall

> **Inference code may see trajectories and interventions, but not topology.**

`code/{blind_cache,directed_graph_inference,graph_bootstrap,
predictive_boundary,causal_discovery}.py` never import `flock_sim.lattice`
or anything topology-derived — enforced by
`tests/test_no_topology_leakage.py`. Only `code/oracle_validation.py` reveals
the true Moore-neighbour graph, and only after every inference decision is
frozen.

## Reproducing

```
cd code
python3 candidate_panel.py                 # builds the 20-candidate/snapshot panel from Stage 6.6 data
python3 run_graph_pipeline.py --n_jobs 8    # directed graph inference + bootstrap stability, 15 snapshots
python3 run_predictive_boundary.py          # Shat^pred(I) + greedy boundary + test excess loss, 300 candidates
python3 run_causal_discovery.py --n_jobs 8  # Bhat^causal(I) via the exact counterfactual propagator
python3 run_oracle_validation.py            # reveals the true graph; precision/recall/Jaccard; A/B/C/D outcomes
python3 run_blind_landscape.py              # G_blind/L_blind for the oracle-vs-blind landscape comparison
python3 run_sample_efficiency.py            # R in {5,10,20,50,100} sweep
python3 run_control_diagnostic.py           # small fixed-budget actuator-set comparison
python3 make_figures_67.py                  # fig_6_7_1 .. fig_6_7_5
python3 export_demo_data_67.py              # interactive_demo/data/stage6_7_bundle.json
```

Then from `interactive_demo/app/`: `python3 build.py` to rebuild
`interactive_demo/build/index.html` with the new "Boundary source" toggle
inside Collective Landscape → Explore.

Run tests with `pytest stage6_flock/stage6_7_blind_boundary/tests/ -q`.
