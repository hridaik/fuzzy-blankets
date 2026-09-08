# PLAN.md — Stage 6.7: Blind Boundary & Causal Interface

Planning document, written before any Stage 6.7 result was inspected. Records
scope decisions up front so `RESULTS_6_7.md` can be checked against stated
intent rather than rationalized after the fact, matching the Stage 6.5/6.6
convention (`../stage6_5/PLAN.md`, `../stage6_6_collective_landscape/PLAN.md`).

## What Stage 6.7 is and is not

Stage 6.6 built a landscape of `(C,G,L,D)` for thousands of candidate flock
interiors, but its boundary `B` was always chosen from the simulator's
*known* structural shell `S(I)` — an explicit, stated simplification
("evaluation-only use... not observational boundary discovery,"
`stage6_6/PLAN.md`). Stage 6.7 asks: can a useful boundary — and then a
causal interface — be recovered **without ever supplying inference code the
flock's Moore-neighbour graph**? The central constraint, restated everywhere
in this stage's code and docs:

> **Inference code may see trajectories and interventions, but not topology.**

It is **not**:

- A refit of the Stage 6.5/6.6 predictive-model family. The nodewise
  multinomial logistic-regression estimator and its frozen hyperparameters
  (`C=1.0, penalty=l2, solver=liblinear, max_iter=200`) are reused verbatim
  (`stage6_5/boundary_inference/code/nodewise_model.py:NodewiseModel`); only
  the *conditioning sets* and the *directed-graph construction around it* are
  new.
- A universal claim that flock interaction graphs are always observationally
  identifiable. Section 20's outcome taxonomy (A/B/C/D, `oracle_validation.py:
  classify_outcome`) is reported per candidate, and predictive sufficiency
  without structural recovery is treated as a real, interesting outcome
  ("B: reduced predictive interface"), not a failure.
- A new controller-optimization stage. `run_control_diagnostic.py` is one
  small, fixed-budget comparison on the existing target-heading task
  (`v2_interface_control/code/common_v2.py:evaluate_arm`, unmodified) — no
  `max_u Q` optimization is implemented (task brief section 16).
- A re-run of Stage 6.6's 5000-candidate-per-snapshot landscape. Stage 6.7
  works from a fixed 20-candidate/snapshot panel (300 total) drawn from
  Stage 6.6's already-frozen candidate data (task brief section 8); broader
  scaling is left as a documented future extension.

## Reused, unmodified

See `configs/protocol_6_7.yaml`'s `reused_unmodified_from_stage6{,_5,_6}`
blocks for the exact file:function citations. Nothing in `python/`,
`v1_mechanism_audit/`, `v2_interface_control/`, `v3_refinement/`,
`stage6_5/`, or `stage6_6_collective_landscape/` is modified by this stage.

## The firewall

Every inference-side module (`code/blind_cache.py`,
`code/directed_graph_inference.py`, `code/graph_bootstrap.py`,
`code/predictive_boundary.py`, `code/causal_discovery.py`) is scanned by
`tests/test_no_topology_leakage.py` — an AST-based import/identifier/
signature scanner directly modeled on
`stage6_5/boundary_inference/tests/test_no_lattice_leakage.py`, plus a
runtime seal that runs the whole blind pipeline on synthetic data and
asserts no `Lattice` instance ever appears in its results (catching a
smuggled reference via `**kwargs`). `code/oracle_validation.py` is the
**only** module in this stage permitted to import `flock_sim.lattice` /
`one_hop_neighbors` for scientific conclusions, and it runs strictly after
every `Bhat^pred`/`Bhat^causal` decision has been frozen and written to disk
— never used to retroactively re-tune the estimator, the shortlist size, or
the edge-stability thresholds.

`code/intervention_api.py` is a second, narrower exception: it must import
the lattice because it has to call the simulator's exact counterfactual
propagator, but it is wrapped as a black-box `InterventionOracle.do(...)`
that returns only the numeric intervention effect (never `is_neighbor` or
any topology-derived field) — `code/causal_discovery.py` receives an
instance of it purely as a duck-typed callable and never imports `flock_sim`
or the lattice itself.

## Primary objects, fixed before any candidate was scored

- `W=10` step window, `R=100` paired replicates (task brief section 2,
  identical to Stage 6.6's own `W_WINDOW`/`R_REPLICATES` constants).
- 60/20/20 trajectory(=replicate)-level split, extending Stage 6.5's
  `trajectory_gen.make_splits` 2-way convention to three ways
  (`code/common_67.py:build_window_dataset3`).
- Primary seeds **2, 3, 4**, all 5 archetype conditions — 15 snapshots.
- A fixed 20-candidate/snapshot panel (300 total), drawn from Stage 6.6's
  own frozen 5000-candidate-per-snapshot data (`code/candidate_panel.py`):
  established `I0`, argmax/argmin over each of `C,G,L,D`, one high-`C`/low-`D`
  patch, the documented diagonal-snake pathology
  (`stage6_6/RESULTS_6_6.md`'s own worked example, selected here by minimum
  `avg_internal_degree` — a metric Stage 6.6's own `common_66.py` docstring
  reserves for exactly this "figure/example selection" use), and 13
  deterministic RNG-drawn candidates.
- `shortlist_k=25` (matches `stage6_5/boundary_inference/code/api.py`'s own
  default), `B_boot=30` bootstrap resamples per snapshot for edge stability.
- Edge-stability thresholds `tau_freq=0.5, tau_sign=0.7`, frozen from **only
  the blind bootstrap statistics** on seed 2's `no_control` snapshot (never
  the true graph) — see `configs/protocol_6_7.yaml`'s `edge_stability` block
  for the exact freeze process. Applied unchanged to every snapshot,
  including seed 4 and every condition.
- `K_max=12` boundary-size cap (matches Stage 6.6's own `K_BOUNDARY_BUDGET`,
  "retained only for comparability," task brief section 6) and
  `delta_pred=0.01` nats/bird-step (task brief section 7), reused as the
  greedy-selection stopping tolerance too.

## Scope-narrowing decisions (stated up front, not discovered later)

1. **Compute budget.** A timing pilot (`logs/timing_pilot.json`,
   `code/run_timing_pilot.py`) measured ~8ms/logistic-regression fit with
   `liblinear` at this stage's sample sizes — far faster than a worst-case
   estimate assumed at design time. The full spec (`shortlist_k=25,
   B_boot=30`, all 15 snapshots) is therefore run at its stated values, no
   reduction needed, parallelized across bootstrap resamples with a
   `multiprocessing.Pool` (`n_jobs=8` of 12 available cores).
2. **Sample-efficiency sweep compute.** Bootstrapping the graph-inference
   procedure itself at `R<=20` replicates is barely meaningful (a 60% split
   of 5 replicates is 3 training replicates); the sweep
   (`code/run_sample_efficiency.py`) therefore uses the single
   (non-bootstrapped) directed graph with raw `Delta>0` as the candidate-pool
   criterion — a disclosed, sweep-only reduction that never touches the
   primary panel's frozen bootstrap numbers.
3. **Causal discovery sampling.** The exact counterfactual propagator is
   closed-form per query but still one query per (state, source, alt-heading)
   triple; `N_STATES_PER_CANDIDATE=15` observed states (drawn from that
   snapshot's own pooled window data, never simulator-privileged) are sampled
   per candidate rather than exhaustively enumerating every replicate x
   timestep.
4. **Control diagnostic scope.** One fixed-budget diagnostic per seed's
   canonical `I0` (task brief section 16's own scoping: "For now, do only a
   small diagnostic... Do not optimize a new controller in this stage"), not
   a sweep over all 300 panel candidates.

## Freeze point

`PROTOCOL_6_7.md` + `configs/protocol_6_7.yaml` are written and hashed
**after** the firewall test passes and the timing pilot + edge-stability
freeze (seeds 2/3 only) have run, and **before** `oracle_validation.py` is
run on the full 300-candidate panel. `RESULTS_6_7.md` answers task brief
section 20's ten questions from the frozen, completed run — if a metric
does not behave as expected, this plan requires reporting that plainly
(matching Stage 6.6's own `METRIC_VALIDATION.md` gate) rather than adjusting
thresholds to manufacture an outcome.
