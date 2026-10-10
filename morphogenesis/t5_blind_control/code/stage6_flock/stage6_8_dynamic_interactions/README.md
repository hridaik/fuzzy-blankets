# Stage 6.8 — dynamic interaction and online boundary inference

Additive continuation of `stage6_flock/`. **Nothing in Stages 6–6.7 is
modified, re-run or restated by this stage**; every frozen scientific result
there continues to describe the fixed-graph, `nn=100` model and is untouched.

## What changes

Stages 6–6.7 ran on one fixed, undirected, time-invariant Moore graph. Two
conveniences followed, and both flattered the pipeline: the true causal
interface `B^D(I)` was a *constant set*, so "tracking the interface" was not a
task; and Stage 6.7's causal estimator used the exact closed-form
counterfactual propagator, which made structural recovery trivially perfect
(300/300 candidates, precision = recall = 1.0) — that measured
*identifiability*, not *estimation*.

Stage 6.8 removes both:

- the interaction interface becomes genuinely time-varying, via a
  **heading-dependent field of view** — bird *i* sees Moore neighbour *j* iff
  `(r_j − r_i) · d_i(t) ≥ 0` — which makes the graph **directed** and
  **state-dependent** while staying mechanistically transparent;
- the primary causal estimator becomes **finite active probing** with real
  sampling error; the exact propagator is demoted to validation.

Two further methodological changes: candidate collectives are **detected
online** rather than supplied, and boundary **construction** is separated from
boundary **certification** (a blind adversarial challenger, because "no single
node helps" is not a sufficiency proof).

## Reading order

1. `PLAN.md` — scope decisions, written before any number was produced.
2. `PHASE_MAP.md` — the uncontrolled phenomenology and the operating-point
   search, including the negative results at L1 and at `nn=100`.
3. `PROTOCOL_6_8.md` — every threshold, with provenance. Machine-readable twin
   in `configs/protocol_6_8.yaml` (+ `.sha256`).
4. `RESULTS_6_8.md` — what was found, and the Stage 6.9 gate verdict.
5. `logs/mesoscopic_criteria_predeclared.txt` — the dated audit trail of what
   was declared when, including every scan that failed and every threshold
   that was *not* moved.

## The firewall

> Inference code may see bird IDs, positions, headings, past trajectories and
> its own interventions. It may not see the FOV rule, the effective interaction
> edges, the latent edge gates, `B_t^D`, or any source-code neighbour list.

Inference-side: `code/{observer,louvain,candidate_detection,spectral_proposal,
tracker,heading_stratified,predictive_boundary_68,challenger,probing}.py`.
Enforced by `tests/test_no_topology_leakage_68.py` (AST import/identifier/
parameter scan + a runtime seal). Positions are newly permitted relative to
Stage 6.7 — a real, disclosed weakening; see `PROTOCOL_6_8.md` §1.

Evaluation-side exceptions, isolated by name: `code/oracle_68.py` (the only
module allowed to compute the FOV graph and `B_t^D`) and
`code/intervention_api_68.py` (a black-box `do`/`probe` interface).

## Layout

```
code/     simulator extension (fov_dynamics), blind inference modules,
          evaluation-side oracle + probe API, one runner per phase
configs/  protocol_6_8.yaml + sha256
data/     every result, one file per phase, never overwritten
figures/  Fig. 6.8-1 .. 6.8-6 (PNG + PDF)
logs/     run logs + the predeclaration audit trail
tests/    44 tests: firewall, FOV correctness, detector, tracker, comparator
```

## Running

```
cd stage6_flock/stage6_8_dynamic_interactions
python -m pytest tests/ -q                       # 44 tests, firewall included

cd code
python run_phase_scan.py            # L1 primary beta grid
python run_phase_scan.py --cross    # L1 (beta, s) cross
python run_phase_scan.py --refine   # L1 resolution refinement
python run_phase_scan_fov.py        # L2 phase map
python run_phase_scan_fov.py --refine
python run_size_scan.py             # finite-size scan
python run_size_scan.py --op        # operating-point scan at nn=400
python run_episode_screen.py        # mesoscopic-episode pool + dev/held-out split
python run_oracle_characterization.py        # L2 interface turnover (validation data)
python run_gate_selection.py                 # L3 gate grid
python run_gate_selection.py --fallback

python run_boundary_pipeline.py snapshot [shard n_shards]   # blind inference
python run_boundary_pipeline.py series
python run_boundary_pipeline.py gated
python run_boundary_pipeline.py merge snapshot 4

python run_oracle_reveal.py snapshot         # ORACLE REVEAL -- run last
python run_oracle_reveal.py series

python run_control.py calibrate              # theta, development seeds only
python run_control.py run
python make_figures_68.py
```

The order matters: `run_oracle_reveal.py` reads the frozen
`data/boundary_inference__*.json` and never modifies it, and no threshold in
`PROTOCOL_6_8.md` was changed after it ran.
