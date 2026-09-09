# PROTOCOL_6_10

Every threshold below was fixed before the experiment it governs was run, with
its provenance stated. `configs/protocol_6_10.yaml` is the machine-readable
twin. Additive: nothing in Stages 6–6.9 is modified, re-run or reinterpreted;
every frozen path is opened read-only.

## 0. Naming (Part A)

| name used here | what it is |
|---|---|
| **Full-info causal heuristic** | exact influence + weighted multicover — the policy Stage 6.8 recorded as `adaptive_oracle` |
| **Full-model control benchmark** | a controller that explicitly optimizes the control objective (Part C) |

`adaptive_oracle` appears **only** when quoting a frozen Stage 6.8 file
verbatim. The word "oracle" is not applied to a controller that was never shown
to be optimal, and "optimum" is used only where an exhaustive search completed.

## 1. Part A — audit of the frozen control cases

`code/run_audit_trace.py` calls Stage 6.8's own `adaptive_control.run_arm`, so
the trajectory is the frozen one by construction, and asserts each replayed
`final_target_fraction` against `stage6_8/data/control.json` to 1e-12. Per
timestep per arm it records: detected interior, structural interface, exact
effective causal interface, sampled causal interface, actuators, actuator
count, per-actuator KL effect, predicted vs realized one-step target gain,
multi-step gain, and lineage metrics (size, Jaccard, turnover, `Q_clump`,
cardinal components).

| quantity | value |
|---|---|
| authority horizon `τ` | 2 (the first horizon at which an exterior actuator can act — see §2) |
| authority rollouts | 96 (trace), 128 (hypotheses) |
| sampled steps for the expensive tests | 0, 6, 12, 18, 24 |
| synergy pairs per state | ≤ 24, drawn from the top-8 by τ-authority |
| horizons compared for H5 | τ ∈ {2, 4, 8} |
| fixed-K grid (H1) | K ∈ {4, 8, 12, 16} |
| H6 bootstrap | 20 000 resamples of the paired per-episode difference |

All action comparisons use **common random numbers**: uniforms are drawn once
per state from a fixed seed and reused for the baseline and every candidate
actuator set (`reference_truth.rollout_alignment`).

## 2. Part B — the independent truth layer, and one structural fact

Three modules in `code/reference_truth.py`:

1. `structural_interface` — `B_t^struct(I)` read from the simulator's transition
   dependencies;
2. `exact_do_interface` — `B_{t,ε}^do` computed **without** the structural graph,
   by perturbing every exterior source through all admissible headings and
   comparing exact next-state distributions (`ε = 1e-9`);
3. `task_authority` — `A_j^{h*,τ}`, plus `pair_synergy` `S_jk = A_{jk} − A_j − A_k`.

**Gate**: (1) and (2) are cross-validated in
`tests/test_reference_truth.py::test_structural_and_interventional_truth_agree`
at three states. They agree exactly, and every source outside `B^struct` is
verified to have identically zero interventional effect. Had they disagreed
materially the stage would have stopped.

**A structural fact that shapes the whole audit.** The controller sets a bird's
*action* at time t, which fixes its *heading* at t+1; an interior bird's t+1
heading is computed from the state at t. Therefore

> `A_j^{h*, τ=1} ≡ 0` exactly, for every exterior actuator j.

The first horizon at which an exterior actuator can move the interior is τ = 2.
This is asserted in
`tests/test_reference_truth.py::test_exterior_actuator_has_exactly_zero_one_step_authority`,
and it is why a **one-step influence score cannot be a task-authority score**.
Stage 6.8 ranked actuators by exactly such a score.

KL influence is non-negative by construction; task authority is signed. They are
kept as separate objects and are never equated.

## 3. Part C — the full-model control benchmark

`code/full_model_benchmark.py` maximizes

    A_S = E[H*(I_t, t+τ) | do(u_j = h* for j in S)] − E[H*(I_t, t+τ) | no action]

over actuator subsets `S ⊆` the current causal interface with `|S| ≤ K`.

| quantity | value |
|---|---|
| objective horizon `τ` | 4 |
| rollouts per evaluation | 96 |
| exhaustive when | `Σ_r C(n,r) ≤ 20 000` — only then is the result called an optimum |
| beam width | 10 (closed loop) / 12 (convergence check) |
| convergence check | beam width × rollouts ∈ {(6,48), (12,96), (20,192)} × seeds {0,1,2} |

`info.is_optimum` is True only for a completed exhaustive search, and the
results text uses "optimum" only where that flag is set.

## 4. Part E — thingness profile (C, G, L, D)

`code/thingness.py`. `C` heading coherence; `G` internal predictive integration
(`ℓ(marginal) − ℓ(interior-only)`); `L` residual predictive leakage after
conditioning on interior ∪ inferred boundary, against the strongest residual
exterior challenger (**low is thing-like**); `D` total-variation contrast
between the collective's heading histogram and its local exterior ring.

Percentile ranks are taken against **comparable** candidates — connected, of
similar size, same uncontrolled regime — because raw `G`/`L` scale with size and
a raw threshold would silently select for size. Estimator hyperparameters are
Stage 6.5–6.8's frozen ones (`liblinear`, `l2`, `C=1.0`, `max_iter=200`).

Stratum thresholds are frozen on **development/uncontrolled data only**. Control
success is neither computed in nor importable from this module.

## 5. Part F — clumpness

`code/morphology.py`:

    A = |I|
    P_4(I) = #{(i,j) : i∈I, j∉I, j shares a CARDINAL grid edge with i}
    Q_clump = P_min(A) / P_4(I),    P_min(A) = 2·⌈2√A⌉

The physical lattice edge counts as exterior space. **Moore adjacency is never
used for perimeter** — asserted in
`tests/test_morphology.py::test_perimeter_uses_cardinal_not_moore_adjacency`,
which pins a diagonal chain at `P_4 = 4|I|`. Validated ordering (also asserted):
compact square `Q > 0.85` > elongated strip > diagonal snake `Q < 0.3`, with a
fragmented region below the strip.

Snake-like candidates are **retained** in the landscape. The *clear clump
stratum* (thing-like ∧ high `Q_clump`) is a selection for visual and control
examples, never a filter on the analysis.

## 6. Part G — operating regime, from uncontrolled data only

`code/run_regime_scan.py` — no controller is run and none is importable. Grid:
`β ∈ {1.0, 0.6, 0.5, 0.4} × s ∈ {1.0, 0.75, 0.5}` at `nn = 400`, 8 seeds,
`nt = 90`, candidates characterized at `t ∈ {60,65,70,75,80}`.

Reported per cell: policy saturation (`frac_locked` = fraction of birds with
`max u_t > 0.999`), candidate size distribution and the moderate-size fraction
(band **[12, 90]**, declared), non-globality, `Q_clump`, cardinal components,
membership turnover, interface turnover, and the susceptibility curve `χ_τ(k)`.

**The tracked lineage is seeded on the moderate-size, most clump-like candidate**,
not the largest. Declared before the scan was read, and using only size and
morphology: the desiderata ask for a moderate-size clump-like collective, and
characterizing the ~120-bird blob instead makes every response look dead purely
because the interface is a tiny fraction of it.

Standardized weak probe (`code/regime_probe.py`, regime characterization only,
never scored): draw `k ∈ {2,4,8,16}` birds uniformly from the exact causal
interface, force them to `h*` for one step, measure the alignment gain at
`τ = 4` against a common-random-number baseline, 6 draws. A cell is *dead* if
`χ_max < 0.01` and *saturating* if the last increment adds `< 15%` of `χ_max`.

The regime is **not** selected by later controller performance. The target is a
robust-responsive window; the chosen regime and seeds are frozen before any
controller comparison.

## 7. Part I/J/K — the closed loop, scoring, and release

`code/closed_loop.py`. Per step `X_t → Î_t → B̂_t → u_t → X_{t+1}`, with both
the interior and the interface recomputed every step. Seven arms, listed in
`closed_loop.ARMS`. Sampled-causal probing runs at 40 rollouts × 3 repeats.

Scoring (Part J): the primary metric is `H*(I_t, t)` on the **current tracked
lineage**, with the frozen-`I_0` value retained as a diagnostic. Full success is
`S_target ∧ S_lineage ∧ S_nondegenerate`, the lineage envelope being learned
from comparable *uncontrolled* lineages. Material membership is not required to
stay fixed; shrink-to-win is excluded by the size floor.

Release (Part K): control is removed and the lineage is measured for heading
retention, thingness, clumpness and lineage validity.

Budget matching (Part I): where an arm chooses fewer actuators by policy, both
outcome and effort are reported, **and** a fixed-K comparison is run so budget
cannot explain the ordering.

## Frozen operating regime (Part G, selected 2026-09-09)

| Quantity | Value | Provenance |
|---|---|---|
| Lattice | nn = 400 (20x20) | Stage 6.8 finite-size addendum; only size with a mesoscopic regime |
| Temperature | beta = 0.4 | Part G scan, `data/regime_scan__main.json` |
| Precision scale | s = 0.75 | Part G scan |
| Susceptibility | chi_max_mean = 0.035 | standardized weak directional probe, uncontrolled |
| Policy-locked fraction | 0.00 | `frac_locked`, threshold R1 |
| Median max u_t | 0.9858 | threshold R1 (< 0.99) |
| Mean candidate size | 74.3 (80% moderate, 0% global) | R4 |
| Mean Q_clump | 0.91 | R7 |
| Mean lineage Jaccard | 0.63 | R5 |
| Membership turnover | 0.230 | R6 |
| Interface turnover | 0.73 | R6 |
| Runner-up regime | beta = 0.5, s = 0.50 | sensitivity check |

Selected by the criteria operationalized in `logs/regime_selection_predeclared.txt`
**before** the scan was read, from uncontrolled data only. The most responsive
cell in the scan (beta=0.4, s=0.5, chi=0.048) was rejected by the lineage
criterion R5 and was not admitted by relaxing it.

## Frozen on uncontrolled data (Parts E + J, 2026-09-09)

Source: `data/uncontrolled_reference__main.json`, 24 uncontrolled episodes at
the frozen regime. No actuator is forced and no target heading exists in the
module that produces this file, so control success is not computable there.

### Thingness estimator (Part E)

| Item | Value | Why |
|---|---|---|
| G, L estimation | held-out (train replicates → disjoint test replicates) | in-sample scoring manufactures G from conditioning-set size |
| Replicates per state | 120, 6 steps | sample size for the held-out fits |
| Conditioning radius `r_pool` | 3.5 | identical to Stage 6.8 `predictive_boundary_68.R_POOL`; ~2.5× interaction geometry |
| Max targets per candidate | 10 | disclosed subsample |
| Max challengers | 24 nearest exterior sources | disclosed compute restriction |
| Clear clump stratum | Q_clump ≥ 0.950 (90th pct), n = 13 of 71 | a labelled subset for examples, **not** a filter on the landscape |

`L` is reported but **not** used for ranking: it is ~0 across the landscape
(median 0.000, p90 0.001), so its percentile ranks carry no information.

### Identity validity envelope (Part J)

Quantile 5%, one-sided, from 24 uncontrolled lineages over 24 steps:

| axis | bound |
|---|---|
| `min_step_jaccard` | ≥ 0.202 |
| `final_jaccard_to_I0` | ≥ 0.000 |
| `final_size_ratio` | ≥ 0.843 |
| `final_q_clump` | ≥ 0.746 |
| `mean_coherence` | ≥ 0.598 |
| `max_n_components` | ≤ 1 |

Conjunctive success threshold on the task axis: `H*(I_t, t) ≥ 0.60`, matching
the Part H success band. Success requires the task **and** identity validity;
the two are also reported separately, and a failed run is labelled with which
failure mode(s) it exhibits.

The `final_jaccard_to_I0` bound of 0.000 is a real measurement, not a disabled
check: uncontrolled lineages at this regime routinely retain no original members
after 24 steps. That axis therefore cannot discriminate here, and the envelope
is not tightened to make it appear to.

### Shared start-state rule

`closed_loop.qualifying_start` — the most clump-like single-component detected
candidate with 12 ≤ size ≤ 90. Used identically by Part H, the Part J envelope,
and the Part I arms, so all three are calibrated on the same population.
Morphology only: no target heading, no arm, no control outcome.

## Corrections applied before Part I (2026-09-09)

Three defects were found by validating instruments before using them, and all
three are recorded here because each would have silently changed a headline.

### 1. Benchmark objective did not model its own actuation

`reference_truth.rollout_alignment` applied the intervention only at the first
rollout step, evaluating "force now, release, look τ steps later", while
execution holds the actuators on every step between re-plans. The benchmark was
planning a weaker intervention than it carried out — and Part H uses it to
decide which episodes are unsteerable, so it would have excluded steerable
episodes.

Fix: a `hold` parameter, with two deliberately different defaults.

| caller | `hold` | why |
|---|---|---|
| `task_authority`, `set_authority`, `pair_synergy` | 1 | authority *is* the one-shot quantity; Part B numbers unchanged |
| `full_model_benchmark.optimize` | τ | matches execution |

Asserted in `test_hold_semantics_are_distinct_and_authority_stays_one_shot`.
That test had to move to the Stage 6.10 regime: at the Stage 6.8 operating point
both semantics return **identically 0.0**, so the test could not tell them apart
there — policy lock again, this time as a test that cannot discriminate.

Empirically the correction changed nothing measurable (mean H 0.450 → 0.410 at
frac 0.25 / T 12, se ≈ 0.116, and in the opposite direction from the one
predicted). It is justified because planning must model execution, **not**
because it improved a number.

### 2. Envelope calibrated per-axis instead of jointly

Six one-sided 5% bounds tested conjunctively rejected valid uncontrolled
lineages, scoring `no_control` identity-invalid. The per-axis quantile is now
chosen so the **joint** pass rate on held-out uncontrolled lineages reaches
`TARGET_JOINT_PASS = 0.90` (`identity_scoring.calibrate_envelope`), and the
envelope is built separately at each candidate horizon. Achieved: 0.93 at
horizon 24, 0.89 at horizon 12 (target not met at any setting; recorded as
such, not relaxed further).

### 3. Predictive arm had no actuators

The certified predictive boundary is empty at this regime (full-pool excess
~0.003–0.009 nats vs `DELTA_TOL` 0.01). The arm now actuates the top-k
single-source validation-gain **ranking**, with the certified-empty result
recorded per episode. The ranking is never described as a certified boundary.

### Benchmark search budget (measured, not assumed)

`data/benchmark_convergence__main.json`, 6 states × 3 beam widths × 3 seeds:

| | bw 4 / 32 roll | bw 8 / 64 | bw 16 / 128 |
|---|---|---|---|
| objective | +0.022 … +0.073 | +0.023 … +0.073 | +0.023 … +0.073 |

mean climb **−0.0005**, max **+0.0017**, against a 0.05 threshold — flat across
a 4× range. The search budget is therefore **not** the binding constraint, which
discharges the asymmetry noted in `run_benchmark_convergence.py`: an
"unsteerable" verdict reflects the physics rather than an under-resourced
search. Part I may use beam width 4 with measured justification.
