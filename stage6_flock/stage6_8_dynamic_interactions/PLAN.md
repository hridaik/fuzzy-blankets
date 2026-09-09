# PLAN.md — Stage 6.8: Dynamic interaction and online boundary inference

Planning document, written **before any Stage 6.8 number was produced**
(the only prior computation was a 6-seed β pilot confirming that the
predeclared β grid spans order and disorder at all; that pilot is recorded
in `logs/pilot_beta_range.txt` and used for nothing except deciding that
the grid did not need to be moved). Follows the Stage 6.5/6.6/6.7
convention: scope decisions are recorded up front so `RESULTS_6_8.md` can
be checked against stated intent rather than rationalized afterwards.

## What Stage 6.8 is

Stages 6–6.7 all ran on **one fixed, undirected, time-invariant Moore
graph**. Two conveniences followed from that, and both flattered the
pipeline:

1. The true causal interface `B^D(I)` was a *constant* set. "Tracking the
   interface" was not a task, because there was nothing to track.
2. Stage 6.7's causal estimator used the **exact** closed-form
   counterfactual propagator, which made structural recovery trivially
   perfect (300/300 candidates, precision = recall = 1.0). That measured
   identifiability, not estimation.

Stage 6.8 removes both. The interaction interface becomes genuinely
time-varying but stays mechanistically transparent, and the primary causal
estimator becomes **finite active probing** with sampling error.

## What Stage 6.8 is *not*

- Not asynchronous updates. Every bird still updates every step.
- Not an independent random-reorientation ("noise kick") process. The only
  stochasticity remains the two RNG draws already in
  `flock_sim.active_inference.step` (action choice, next-heading sample),
  plus — at L3 only — the edge gates.
- Not a moving-agent model. Positions are fixed lattice sites throughout
  Stage 6.8. Moving agents are Stage 6.9's problem.
- Not a re-run or a revision of anything in `python/`, `v1_mechanism_audit/`,
  `v2_interface_control/`, `v3_refinement/`, `stage6_5/`,
  `stage6_6_collective_landscape/`, or `stage6_7_blind_boundary/`. Every
  frozen Stage 6–6.7 result stands unmodified; this stage only adds files
  under `stage6_8_dynamic_interactions/`.

## The complexity ladder (task brief section 1)

| level | interaction interface | status |
|---|---|---|
| **L0** | fixed undirected Moore graph, β=1.0, ρ=15, ω=3 | frozen reference — Stage 6–6.7's model, re-run here only to reproduce reference statistics |
| **L1** | same fixed graph, β moved off the near-consensus regime | operating-point selection only |
| **L2** | L1 parameters + heading-dependent FOV → **time-varying directed** visibility graph | **the main Stage 6.8 result** |
| **L3** | L2 + persistent two-state Markov gates on visible directed edges | **secondary robustness condition only** |

No further modifications are combined. L3 is reported separately and is
never folded into the headline L2 numbers.

## Order of operations (each gate must pass before the next step runs)

1. **Phase scan first.** Map uncontrolled L1 phenomenology across the
   predeclared β grid. Write `PHASE_MAP.md`. *No boundary, causal-discovery
   or control metric may be computed before `PHASE_MAP.md` exists.* The
   operating point is chosen from uncontrolled phenomenology alone
   (polarization, coherent-component structure, lifetimes, turnover,
   heading entropy) — explicitly **not** from where downstream inference
   works best. If two regimes look equally reasonable, both are retained
   and carried through the rest of the stage.
2. **L2 oracle characterization.** Build the FOV simulator, record the full
   time-dependent oracle directed graph and `B_t^D` for validation, and
   measure interface size/turnover/lifetime. Still no inference.
3. **Firewall.** `tests/test_no_topology_leakage_68.py` must pass before any
   inference module is run on real data.
4. **Detection → prediction → causation.** Candidate detection (blind),
   heading-stratified predictive influence (blind), predictive boundary
   (blind), blind challenger certification (blind), finite active probing
   (black-box `do` API, blind to topology).
5. **Oracle reveal.** Only after every inference decision above is written
   to disk: exact black-box counterfactual, then the true FOV graph.
6. **L3.** Only after L2 is characterized.
7. **Adaptive control.** Only after 4–6 succeed.

## The firewall (task brief section 6)

> **Inference code may see bird IDs, positions, headings, past trajectories
> and its own performed interventions. It may not see the FOV rule, the
> effective interaction edges, the latent gates, `B^D`, or any source-code
> neighbour list.**

Positions are *newly permitted* relative to Stage 6.7 (an external observer
of a physical flock sees where the birds are). This is a real weakening of
the firewall on a fixed lattice, and it is stated plainly rather than
hidden: from positions alone one could reconstruct the *geometric* Moore
adjacency. What remains genuinely hidden — and what this stage actually
asks about — is the **heading-dependent directed subset of it that is
causally live at time t**, which is not a function of positions. All
distance-based inference code therefore receives an `(nn, 2)` float
position array through the observation record and must use a *smooth*
spatial kernel, never the exact Moore/FOV predicate.

Enforcement mirrors `stage6_7_blind_boundary/tests/test_no_topology_leakage.py`:
an AST-based import/identifier/signature scan of every inference-side
module, plus a runtime seal that runs the blind pipeline on synthetic data
and asserts no `Lattice`, `FovOracle`, or oracle-graph object appears
anywhere in its outputs.

Evaluation-side exceptions, isolated to named modules:
- `code/oracle_68.py` — the only module allowed to compute the true FOV
  graph and `B_t^D`; runs strictly after inference is frozen.
- `code/intervention_api_68.py` — must import the simulator to run
  interventional rollouts, but exposes only numeric effect estimates
  through a duck-typed `do`/`probe` interface, never `is_neighbor`,
  `visible`, or any topology-derived field.

## Detection before boundary inference (task brief section 7)

Stage 6.5–6.7 were always *handed* an interior `I0`. Stage 6.8's primary
analysis starts from **candidate collectives proposed online from
observations**. `I0` survives only as a comparator. Candidate detection may
not use the control target, oracle edges, oracle boundary, or any future
observation.

Two proposal methods are run side by side and neither is privileged a
priori:
- **Affinity/community proposal** (primary): rolling coherence-and-proximity
  affinity `W_ij(t) = K_σ(‖r_i − r_j‖) · (1/W)Σ_τ 1[z_i(τ)=z_j(τ)]`, then a
  deterministic weighted-Louvain community extraction. Returns *multiple*
  candidates, filtered only by predeclared validity constraints (size,
  persistence, spatial connectedness/compactness).
- **Spectral/coherence proposal** (comparator): the paper's Fiedler-style
  split, recomputed on the observed coherence adjacency. It is called a
  *spectral/coherence proposal*, **never** a Markov blanket.

Neither the affinity graph nor the Fiedler split is interpreted as a Markov
blanket anywhere in this stage.

## Construction vs. certification (task brief sections 14–15)

Stage 6.7 used `max_j Δ_j ≤ δ` as its stopping rule and treated it as
evidence of sufficiency. That is **not sufficient** — jointly informative
residual predictors can matter when no single one does. Stage 6.8 therefore
splits the two:

- **Construction**: greedy single-node gains, capped at `K_max`, reporting
  where the stopping rule terminates naturally.
- **Certification**: an independent *blind challenger* — best remaining
  single source, best pair from a residual shortlist, and a strongly
  regularized sparse multivariate challenger over *all* residual exterior
  sources. Selected on train/validation trajectories, evaluated **once** on
  untouched test trajectories, with a bootstrap upper confidence bound.

`B` is called **predictively sufficient relative to the challenger class**,
never "conditionally independent". The wording is fixed and is enforced in
the results text.

## Pre-declared thresholds

Every threshold is fixed in `PROTOCOL_6_8.md` / `configs/protocol_6_8.yaml`
before the experiment it governs is run, with its provenance stated. Where
a threshold is calibrated, it is calibrated on **development seeds** and
applied unchanged to held-out seeds.

## Stopping gate to Stage 6.9 (task brief section 23)

Stage 6.9 is created only if all four hold, and the gate verdict is written
into `RESULTS_6_8.md` before any 6.9 directory exists:

1. the L1 regime supports persistent **non-global** collectives;
2. L2 produces genuine interface turnover;
3. the candidate detector tracks at least some collectives for meaningful
   durations;
4. blind predictive and/or active causal inference produces interpretable
   dynamic estimates.

If they fail, the failure is reported and the stage stops. Adding model
complexity to rescue a failed gate is explicitly forbidden.
