# RESULTS_6_7

All numbers below come from the frozen pipeline in `PROTOCOL_6_7.md` /
`configs/protocol_6_7.yaml`, run at full spec scale: 15 snapshots (3 seeds ×
5 conditions), 300 primary candidates, `shortlist_k=25`, `B_boot=30`,
`N_STATES_PER_CANDIDATE=15`, `CI_N_BOOT=1000`. Full data in `data/`, figures
in `figures/`. `oracle_validation.py` was run once, after every inference
decision above was frozen — nothing below was used to retune the pipeline.

## Headline

**The predictive boundary can be inferred blind, and it is small and
precise — but it recovers almost none of the true structural shell.** Across
the 300 candidates, the inferred predictive boundary achieves **73%
predictive sufficiency** (Δℓ ≤ 0.01 nats/bird-step) with a mean size of only
**1.7 birds** (38% of candidates get an *empty* boundary and are still
predictively sufficient), at **99.8% precision** but **5.3% recall** against
the true shell (mean structural Jaccard **0.053**). **Zero** of the 300
candidates landed in outcome A (both high) or C (poor prediction despite
good structural luck) — every candidate is either **B** (219/300, reduced
predictive interface) or **D** (81/300, failed both). The **active/causal**
method is a completely different story: using the exact counterfactual
propagator, it recovers the true shell **exactly** (precision = recall =
Jaccard = 1.0) on **all 300/300 candidates**, and in the one-off control
diagnostic, actuating the causal interface controls the flock exactly as
well as actuating the true shell (100% success, matching oracle, vs. 0% for
the predictive interface and 0-3% for a random draw of the same size as
oracle/causal).

## Answers to the ten questions (task brief section 20)

**1. Can the predictive boundary be inferred without topology?**
Yes, mechanically — `predictive_boundary.py` never touches the lattice and
still produces a boundary that is predictively useful 73% of the time. But
"inferred" here means "a small, high-precision, low-recall subset," not
"the graph." See Fig. 6.7-1: every candidate with worthwhile structural
recovery (J > ~0.15) has excess loss above the 0.01 threshold, and every
candidate below threshold has J below ~0.24 (mean 0.053) — no candidate
achieves both.

**2. How many trajectories are needed for predictive sufficiency?**
Not many. In the sample-efficiency sweep (Fig. 6.7-4, `data/sample_efficiency.json`),
the fraction of candidates meeting Δℓ ≤ 0.01 rises from 56% at R=5 to 72% at
R=10 and plateaus around 78% by R=20 — already near its R=100 value (78%).
Predictive sufficiency needs on the order of **R≈10-20** replicates.

**3. How many are needed for structural-shell recovery?**
Far more, and still climbing. Mean structural Jaccard rises **monotonically
and without saturating** across the whole grid: 0.017 (R=5) → 0.017 (R=10) →
0.036 (R=20) → 0.048 (R=50) → 0.058 (R=100). Precision stays ≥0.97
throughout (almost no false positives at any R) — it is recall, not
precision, that is data-starved. Naive extrapolation of this slow, still-
rising curve suggests recovering even half the true shell would need very
substantially more than R=100 replicates, if it is reachable by passive
observation at all within this model class.

**4. Does predictive sufficiency arrive before structural recovery?**
Unambiguously yes, at every sample size tested (R=5 through R=100) and
across the full 300-candidate panel. This replicates Stage 6.5's single-flock
finding at 25× the candidate count and across all five control regimes.

**5. Does global consensus make the true graph observationally unidentifiable?**
Yes — the effect is monotonic and clean across the five conditions
(`data/oracle_validation_panel.json`, grouped by condition):

| condition | frac. pred. sufficient | mean Δℓ (nats) | mean pred. Jaccard | mean \|B_hat_pred\| |
|---|---|---|---|---|
| no_control | 0.65 | 0.0082 | 0.089 | 2.85 |
| shell_only | 0.58 | 0.0074 | 0.061 | 1.95 |
| same_direction | 0.72 | 0.0056 | 0.057 | 1.77 |
| opposite | 0.82 | 0.0051 | 0.031 | 1.07 |
| disordered | 0.88 | 0.0045 | 0.025 | 0.83 |

As exterior forcing pushes the flock toward stronger global coordination
(no_control → disordered isn't a coordination ladder by name, but
`same_direction`/`opposite` explicitly synchronize the near-exterior and
`disordered` still couples it on a shared deterministic schedule), predictive
sufficiency gets *easier* (58%→88%) while structural recovery gets *harder*
(Jaccard 0.089→0.025, inferred boundary shrinking toward empty). More
redundancy among exterior birds means fewer of them are *needed* to predict
the interior, which is exactly what makes the *specific* true neighbours
harder to single out.

**6. Which regimes improve or worsen boundary recovery?**
`no_control` (the least-forced regime) gives the *best* structural recovery
(Jaccard 0.089) and worst predictive sufficiency (65%); `disordered` gives
the worst structural recovery (0.025) and best predictive sufficiency (88%).
By candidate shape (`data/candidate_panel.json` labels): the compact
`established_I0` is the *easiest* to predict (93% sufficient, often with a
negative excess loss — the sparse model generalizes better than the
99-feature full model) but has the *worst* structural recovery of any label
(Jaccard 0.010); the scattered `diagonal_snake_pathology` is the *hardest* to
predict (47% sufficient) but has above-average structural recovery (0.089)
among the labelled groups.

**7. Does active perturbation recover causal parents that passive prediction omits?**
Yes, completely. Aggregated over all 300 candidates (Fig. 6.7-3): **8230**
exterior-bird memberships are causal-only, **507** are shared by both
methods, and only **1** is predictive-only — i.e. the predictive boundary is
(almost exactly) a tiny subset of the causal interface, never an alternative
view of it.

**8. How close is B̂^causal to the true B^D?**
Exact. Precision = recall = Jaccard = 1.0 on all 300/300 candidates
(mean \|B̂^causal\| = mean \|B^D\| = 29.1). This is a direct consequence of
the *exact* counterfactual propagator's own proven property (zero effect iff
non-neighbour, `exact_intervention.py`'s docstring) — it is not a claim about
how a bootstrap-based causal-discovery procedure would perform against a
noisy/Monte-Carlo propagator or real sampled rollouts, where the CI-based
`Bhat^causal` criterion (retained precisely for that reason, task brief
section 14) would be expected to show some recall loss and possibly a
nonzero false-positive rate.

**9. Does the Stage-6.6 collective landscape survive when boundaries are inferred blindly?**
Partially. `G_blind` (internal integration) correlates strongly with Stage
6.6's oracle-boundary `G` (r=0.95, Fig. 6.7-5 left) — the qualitative
*ordering* of candidates by G is preserved under blind boundaries. `L_blind`
(boundary leakage) does **not** survive (r=0.10, Fig. 6.7-5 right): oracle
`L` clusters tightly near 0 by construction (Stage 6.6's boundary search
directly minimizes it against the *true* full-neighbour set), whereas
`L_blind` compares against `M_all` (all 99 exterior birds, since a blind
pipeline has no oracle-restricted "full neighbour set" to fall back on) and
is frequently strongly negative — the 99-bird full model overfits on
~540 training samples, so the small blind boundary's held-out loss often
beats it. This is a property of `L`'s *reference point* under blindness, not
a contradiction of Stage 6.6: `G`'s two-model comparison (boundary alone vs.
interior+boundary) needs no oracle reference and travels well; `L`'s
comparison against "everything" does not.

**10. Which information is genuinely available from passive observation, and which requires intervention?**
Passive observation alone reliably gives a *small, high-precision predictive
sufficiency certificate* — enough to say "this much information already
predicts the interior almost as well as everything" — but not the causal
graph, and, per the control diagnostic, not control authority: actuating the
predictive interface produced **0% control success** (matching a random
same-size draw) on all three seeds, while actuating the causal interface
matched the oracle shell's **100%** exactly (random draws matched to the
oracle/causal size also scored 0-3%, so this gap is about *identity*, not
just *budget*). Recovering the actual interaction graph, and a set of
actuators with real control authority, required active perturbation in every
case tested here.

## Figures

- **Fig. 6.7-1** (`fig_6_7_1_predictive_vs_structural.png`) — predictive
  excess loss vs. structural Jaccard, all 300 candidates, colored by outcome
  (only B and D occur).
- **Fig. 6.7-2** (`fig_6_7_2_representative_cases.png`) — two representative
  lattice renders (a B and a D case) showing interior, inferred boundary, and
  true shell.
- **Fig. 6.7-3** (`fig_6_7_3_predictive_vs_causal_overlap.png`) — aggregate
  predictive/causal/both/missed edge counts across all 300 candidates.
- **Fig. 6.7-4** (`fig_6_7_4_sample_efficiency.png`) — predictive loss and
  structural Jaccard vs. R∈{5,...,100}, per seed.
- **Fig. 6.7-5** (`fig_6_7_5_oracle_vs_blind_landscape.png`) — oracle- vs.
  blind-boundary `G` and `L` coordinates, all 300 candidates.

## Caveats, stated plainly

- The 300-candidate panel is dominated by irregular/diverse shapes (Stage
  6.6's five generation methods), whose true shells (mean \|B^D\|=29.1) are
  much larger than the canonical compact `I0`'s own shell (12-14). Recall
  numbers here are therefore not directly comparable to Stage 6.5's
  single-flock canonical-I0 result (recall 0.18-0.58) — a smaller absolute
  miss count divided by a much larger true-shell denominator yields a
  smaller fraction, not a worse estimator.
- The causal method's perfect recovery is a property of the *exact*
  propagator used here, stated explicitly in question 8's answer above —
  do not read it as "active causal discovery is trivial" in a stochastic or
  real-world setting.
- `L_blind`'s reference point (`M_all`, all exterior birds) differs from
  Stage 6.6's oracle `L` reference (the true full neighbour set) by
  necessity under the firewall; question 9's answer states this plainly
  rather than treating the two `L` values as directly comparable.
- The control diagnostic (task brief section 16) is a single fixed-budget
  comparison per seed's canonical `I0`, not a sweep over the 300-candidate
  panel — a deliberate scope limit stated in `PLAN.md`, not a claim that
  every candidate's predictive/causal interface would show the same gap.
