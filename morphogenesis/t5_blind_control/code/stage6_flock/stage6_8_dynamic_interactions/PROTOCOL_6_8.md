# PROTOCOL_6_8

Every threshold below was fixed before the experiment it governs was run, with
its provenance stated. `configs/protocol_6_8.yaml` is the machine-readable
twin; `configs/protocol_6_8.yaml.sha256` freezes its hash. The dated audit
trail for the operating-point search is
`logs/mesoscopic_criteria_predeclared.txt`; the phase-scan conclusion is
`PHASE_MAP.md`. Nothing in this file was edited after `code/run_oracle_reveal.py`
ran.

## 1. The firewall

> **Inference code may see bird IDs, positions, headings, past trajectories and
> its own performed interventions. It may not see the FOV rule, the effective
> interaction edges, the latent stochastic edge gates, `B_t^D`, or any
> source-code neighbour list.**

Inference-side modules: `code/{observer, louvain, candidate_detection,
spectral_proposal, tracker, heading_stratified, predictive_boundary_68,
challenger, probing}.py`. Enforced by
`tests/test_no_topology_leakage_68.py` — AST import scan, AST identifier scan,
AST parameter-name scan, plus a runtime seal that runs the whole blind pipeline
on synthetic data and asserts no `Lattice` / `FovSimulator` / `FovResult` /
`ExactPropagator` / `FiniteProbe` / `GateParams` object appears anywhere in its
outputs. 44/44 tests pass.

**Positions are newly permitted relative to Stage 6.7.** On a fixed lattice
this is a real weakening: geometric adjacency *is* recoverable from positions.
It is stated here rather than hidden. What remains hidden — and what Stage 6.8
actually asks about — is the *heading-dependent directed subset* of that
adjacency that is causally live at time *t*, which is not a function of
positions. All distance-based inference uses a smooth Gaussian kernel, never
the Moore or FOV predicate (asserted in
`tests/test_detector_and_tracker.py::test_affinity_uses_a_smooth_kernel_not_an_adjacency_indicator`).

Evaluation-side exceptions, isolated by name:
- `code/oracle_68.py` — the only module allowed to compute the true FOV graph
  and `B_t^D`; imported only by `run_oracle_characterization.py`,
  `run_oracle_reveal.py` and the figure script, all of which run **after** the
  inference results are on disk.
- `code/intervention_api_68.py` — imports the simulator because it must run
  interventions, but returns only numeric effects. `probing.py` receives it as
  a duck-typed callable.

## 2. Geometry (derivation, not convention)

`flock_sim.lattice` uses 0-based column-major indices, `row = idx % L`,
`col = idx // L`, and slot 0 ("top") `= idx-1 = row-1`.
`flock_sim.model.SLOT_OVERRIDES` sets the collision term `R[down, up] = -ca`
for slot 0 — "my TOP neighbour heading DOWN while I head UP is a collision" —
which pins `top` to the `+y` direction of `UV4`'s `up = (0,1)`. Hence
`x = col, y = (L-1) - row`, and the eight slot displacement vectors follow by
arithmetic. Asserted against actual positions in
`tests/test_fov_model.py::test_slot_vectors_match_actual_positions`.

## 3. The complexity ladder

| level | interface | role |
|---|---|---|
| L0 | fixed undirected Moore graph, β=1.0, ρ=15, ω=3 | frozen reference |
| L1 | same graph, β varied | operating-point search **only** |
| L2 | L1 + heading-dependent FOV → time-varying **directed** graph | **main result** |
| L3 | L2 + persistent two-state Markov edge gates | **secondary robustness only** |

`compute_G_fov` with an all-ones mask is numerically identical to the frozen
`flock_sim.active_inference.compute_G`
(`tests/test_fov_model.py::test_all_ones_mask_reduces_to_frozen_model`), so L2
is a strict restriction of the frozen model, not a re-parameterization.

**FOV rule.** Bird *i* sees geometric Moore neighbour *j* iff
`(r_j - r_i) · d_i(t) ≥ 0`, with `d_i(t)` the receiver's current cardinal
heading. Exactly 5 of 8 slots are visible per heading, the 3 rear neighbours
excluded; never symmetrized; boundary birds use only their available
neighbours; no bird is ever left with zero live in-edges (all asserted in
`tests/test_fov_model.py`).

## 4. Operating point

| quantity | value | provenance |
|---|---|---|
| nn | **400** (20×20) | the only deviation from the frozen Stage 6–6.7 nn=100; forced by the finite-size finding in `PHASE_MAP.md` §5 |
| β, ρ, ω | **1.0, 15, 3** | the frozen Stage 6–6.7 values; selected by the mesoscopic-episode rule, not assumed |
| OP-2 (retained) | β = 1.5, same ρ, ω, nn | second regime retained per task brief §2 |
| episodes | 22 of 600 screened seeds (3.7%) | `data/episode_screen.json`; 11 development, 11 held-out, split by rank parity before any threshold was calibrated |
| nt, burn-in | 120, 40 | fixed for every scan |

## 5. Candidate detection (task brief §§7–8, 10)

| quantity | value |
|---|---|
| affinity window `W` | 8 steps |
| spatial kernel | Gaussian, `σ = 1.75` lattice units, hard cutoff at 4.0 |
| community method | deterministic weighted Louvain (`code/louvain.py`), resolution 1.0 |
| validity: size | ≥ 2% and ≤ 55% of the flock |
| validity: spatial | exactly one connected component at link radius 1.75 |
| validity: compactness | size / bounding-box area ≥ 0.25 |
| comparator | spectral/coherence Fiedler split, `core_pctl = (80, 20)` |

The affinity graph is **not** a Markov blanket and the Fiedler split is called
a **spectral/coherence proposal**, never a Markov blanket. `G`, `L`, `D`,
causal recovery and control performance are not used to filter candidates and
are not importable by the detector.

Louvain determinization (two departures from Blondel et al., both to make a
proposal reproducible bit-for-bit): ascending node order instead of a shuffle;
ties broken to the lowest community index, with movement only on a strictly
positive gain.

## 6. Lineage tracking (task brief §9)

`score = 0.7·J(I_t, I_{t-1}) + 0.3·functional_similarity`, continuation
threshold **0.35**, mutual-best-match, one pass per frame. Material identity is
**not** imposed as exact equality (asserted in
`tests/test_detector_and_tracker.py::test_tracker_survives_membership_change_without_exact_equality`).
Recorded per step: size, Jaccard retention, membership turnover, coherence,
centroid, compactness, aspect ratio.

## 7. Heading-stratified prediction (task brief §§11–12)

| quantity | value | provenance |
|---|---|---|
| estimator | multinomial logistic, `solver=liblinear, penalty=l2, C=1.0, max_iter=200` | **identical** to Stage 6.5–6.7's frozen hyperparameters |
| stratification | one model per (target `i`, current heading `h`) | task brief §11 |
| minimum stratum size | 40 samples | fixed before any fit |
| source pool radius `R_POOL` | 3.5 lattice units | disclosed compute restriction, ~2.5× the interaction geometry |
| coefficient shortlist | 12 per stratum | as Stage 6.7's `shortlist_k`, scaled to the pool |
| bootstrap stability | 12 resamples (6 in the pipeline runs), `τ_freq = 0.5` | `τ_freq` is Stage 6.7's frozen value, reused unchanged |
| observation protocol | `W = 20`, `R = 200` replicates, 60/20/20 **replicate-level** split, `split_seed = 0` | extends Stage 6.6/6.7's repeated-observation protocol |

Non-shortlisted sources get `Δ = 0` exactly — a disclosed approximation, as in
Stage 6.7, not a silent omission.

## 8. Boundary construction vs certification (task brief §§13–15)

**Construction** (greedy, single-node gains allowed): pool = exterior sources
with `selection_frequency ≥ 0.5`, greedy search capped at the top 20 by
influence score; stop when excess over the full-pool loss ≤ `δ_tol = 0.01`
nats/bird-step, or best remaining gain ≤ `min_gain = 0.002`, or `K_max = 12`.
`δ_tol` and `min_gain` are Stage 6.5–6.7's frozen constants, reused unchanged.
`K_max` is a computational cap only; the stop reason is recorded for every run
and the boundary is never padded.

**Certification** (independent, joint, adversarial): three challenger classes —
C1 best remaining single source, C2 best pair from an 8-source residual
shortlist, C3 an L1-regularized (`C = 0.05`) sparse multivariate multinomial
over **all** residual exterior sources. Selected on train/validation only; the
test split is touched exactly once. `L̂_challenge(B) = ℓ_test(M_B) −
min_c ℓ_test(M_{B+c})`, bootstrapped over 500 resamples of test
**trajectories** (not rows). `B` is **predictively sufficient relative to the
challenger class** iff `U_{0.95}(L̂_challenge) ≤ δ = 0.01`.

**This is not a test of exact conditional independence and is never described
as one.** The wording is fixed and is used verbatim in `RESULTS_6_8.md` and in
every figure caption.

Interior-model conditioning is restricted to `(I ∪ B)` members within `R_POOL`
of the target — the same disclosed spatial restriction as §7, applied so that a
peripheral bird is not conditioned on 80 members ten lattice units away.

## 9. Finite active probing — the PRIMARY causal estimator (task brief §16)

| quantity | value |
|---|---|
| probe candidate set | exterior birds within 2.5 lattice units of the candidate (disclosed; the true FOV shell lies within √2) |
| rollouts per arm | 50, **paired under common random numbers** |
| repeats per (source, alternative heading) | 6 independent CRN draws |
| alternative headings | all 3 ≠ the source's current heading |
| smoothing | Laplace `α = 0.5`, applied identically to both arms |
| bootstrap | 500 resamples of the collected KL samples |
| decision rule | `B̂_t^causal = { j : CI lower bound > 0 }`, `α = 0.05` |

Probing uses the **real observed current state** `z_t`, so `B̂_t^causal`
estimates `B_t^D` at the same instant.

## 10. Oracle reveal (task brief §17) — the only topology-aware step

`code/run_oracle_reveal.py` reads the frozen
`data/boundary_inference__*.json`, never modifies it, and reports three
quantities **separately, never collapsed into one number**:

- **estimation error due to finite probing** — `B̂^{causal,sampled}` vs `B^{causal,exact}`
- **identifiability** — `B^{causal,exact}` vs `B^D`
- **structural agreement** — `B̂^{causal,sampled}` vs `B^D`

plus, for both interfaces, precision, recall, size error, temporal lag, and the
turnover similarity `T_B(t) = J(B_t △ B_{t-1}, B_t^D △ B_{t-1}^D)`.
`τ_exact = 1e-9`. None of this was used to retune any estimator, threshold,
shortlist size or stopping rule.

## 11. L3 gates (task brief §5)

Gate `G_{j→i}(t)` is an independent two-state Markov process on each
**directed** Moore edge, evolving whether or not the edge is currently visible;
`A_{j→i}(t) = V_{j→i}(t) · G_{j→i}(t)`.

Selection conditions, declared before the grid ran, from uncontrolled
phenomenology only (`code/run_gate_selection.py` imports no boundary, causal or
control module):

- **G1** local collective formation intact: mesoscopic-episode fraction within
  0.5×–2× the ungated L2 value;
- **G2** nontrivial edge turnover: gate flip rate ≥ ½ the FOV visibility flip
  rate, and live-edge fraction in [0.45, 0.85];
- **G3** flocking not destroyed: mean largest coherent component ≥ 0.5× ungated,
  heading entropy ≤ 1.2× ungated.

**Outcome: no regime in the predeclared grid satisfies all three; G1 is
binding.** The fallback used for the L3 robustness probe is the weakest regime
(by gate flip rate) satisfying G2 and G3 — stationary-on 0.85, mean on-run 10
steps, `p01 = 0.5667`, `p10 = 0.1` — and it is labelled as failing G1 wherever
it appears. L3 results are reported separately and never folded into the
headline L2 numbers.

## 12. Adaptive control (task brief §§20–21)

| quantity | value |
|---|---|
| control horizon | 16 steps, starting at t = 60 |
| actuator budget `K_act` | 10, matched across every arm |
| re-inference cadence | every 4 steps (adaptive arms) |
| support rule | `s_i(A_t,t) = Σ_{j∈A_t} Ĉ^do_{j→i}(t) ≥ θ` for ≥ 50% of the current interior |
| `θ` | calibrated on **development seeds only** as the 25th percentile of each interior bird's strongest single-source inferred influence |
| arms | frozen initial causal · adaptive inferred causal · adaptive oracle causal · predictive · matched-budget random |

`θ` is calibrated from the empirical scale of the influence estimates, not from
control success — `run_control.py --calibrate` does not compute a control
outcome. Held-out seeds are never used to set it.

## 13. Reused unmodified

`python/flock_sim/*` (the simulator, the model tables, the policy posterior,
the sampling rule); Stage 6.5's estimator family and its frozen hyperparameters;
Stage 6.5–6.7's `δ_tol`, `min_gain`, `τ_freq` and 60/20/20 replicate-level
split convention; Stage 6.5's exact-counterfactual derivation, generalized to
the masked edge set. Nothing in `python/`, `v1_mechanism_audit/`,
`v2_interface_control/`, `v3_refinement/`, `stage6_5/`,
`stage6_6_collective_landscape/` or `stage6_7_blind_boundary/` is modified,
re-run or restated by this stage.
