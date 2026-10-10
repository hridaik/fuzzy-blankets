# RESULTS_6_8

Every number below comes from the frozen pipeline in `PROTOCOL_6_8.md` /
`configs/protocol_6_8.yaml`, and from data written to `data/` before
`code/run_oracle_reveal.py` was run. The dated audit trail of what was
declared when — including seven addenda recording every scan that failed and
every threshold that was *not* moved — is
`logs/mesoscopic_criteria_predeclared.txt`. Read `PHASE_MAP.md` first: the
operating point was chosen there, from uncontrolled phenomenology alone.

Nothing in Stages 6–6.7 is modified, re-run or restated by this stage.

---

## Headline

**The interaction interface is now genuinely time-varying, and it can be
tracked — but only by intervening.** Under the heading-dependent FOV rule the
true causal interface of a fixed reference interior takes **12.7 distinct
values in 61 steps** (L0: exactly 1), with 1.4 nodes entering or leaving per
step. A blind detector proposes collectives online and tracks **187 of them
for ≥10 steps** while roughly **half their members are replaced**. Against
that moving target:

| estimator | mean precision | mean recall | mean Jaccard vs `B_t^D` |
|---|---|---|---|
| exact black-box counterfactual (validation only) | **1.000** | **1.000** | **1.000** |
| finite active probing (primary, L2) | **1.000** | 0.602 | **0.602** |
| finite active probing (L3, hidden gates) | **1.000** | 0.411 | **0.411** |
| passive heading-stratified prediction (L2) | 0.837 | 0.239 | **0.233** |

Three findings organize the rest:

1. **Stage 6.7's "perfect causal recovery" was an artefact of the exact
   propagator.** Identifiability is still perfect here (1.000 on every run at
   both L2 and L3). Estimation is not: with a 90,000-rollout budget the finite
   probe finds **60%** of the interface at L2 and **41%** under hidden gates.
   The gap between those two rows *is* the estimation error, and it is
   reported separately from identifiability, never collapsed into it.
2. **The probe is precision-perfect and recall-limited.** Across all 23
   snapshot and gated runs it never once reported a bird that was not really
   in `B_t^D`. Its failure mode is silence, not error.
3. **`B^pred ≠ B^causal` survives, and widens.** The predictive interface has
   mean size 5.4 against a true interface of 20.6, and `J(B̂^pred, B^causal,exact)
   = 0.233` — yet **17/17 predictive boundaries are certified predictively
   sufficient relative to the challenger class** (mean 95% upper bound on the
   challenge loss 0.0051 nats, against δ = 0.01). Predictive sufficiency and
   causal structure are still different things, now measured with a challenger
   that Stage 6.7's "no single node helps" rule could not have caught.

The two negative results are equally clear: **L1 has no mesoscopic regime at
any parameter setting or lattice size tested** (`PHASE_MAP.md`), and **the
Stage-6 sparse-boundary control task is infeasible at this stage's scale even
with full oracle knowledge**.

---

## 1. The ladder, and what each rung cost

`compute_G_fov` with an all-ones mask is numerically identical to the frozen
`flock_sim.active_inference.compute_G`
(`tests/test_fov_model.py::test_all_ones_mask_reduces_to_frozen_model`), so L2
is a strict restriction of the Stage 6–6.7 model rather than a new one. The
FOV rule excludes exactly the three rear Moore neighbours per heading, is never
symmetrized, and leaves no bird blind at any step of any run tested.

The rule's real consequence is structural, and it is the reason L2 behaves
differently from L1 at identical parameters: **`compute_G` never reads `z[i]`**,
so in the frozen model a bird's next heading is independent of its own current
heading. Under FOV, `z[i]` selects which sources are live. That is the only
receiver-state dependence anywhere in this model family.

## 2. The interface really does move (task brief §4)

Fixed reference interior of 21 birds, 6 mesoscopic episodes, t ∈ [40, 100]:

| | L0 fixed graph | L2 FOV |
|---|---|---|
| mean \|B_t^D\| | 24.0 | 15.3 |
| distinct interfaces in 61 steps | **1** | **12.7** |
| \|B_t^D △ B_{t−1}^D\| per step | 0.0 | 1.43 |
| interface turnover per step | 0.000 | 0.046 |
| mean node interface lifetime | 61 (i.e. never leaves) | 17.5 steps |
| live directed edges | 100% | 63.9% |
| edge live/dead flips per step | 0.0% | 4.8% |

This is oracle validation data, recorded before any inference module was run on
real data, and it is what makes "tracking the interface" a task rather than a
tautology.

## 3. Candidate collectives can be detected without oracle structure (§§7–8, 10)

Both proposal methods ran side by side on the same single real trajectory,
one step at a time, over all 22 mesoscopic episodes (t = 20…100). Neither was
privileged; neither had access to the control target, the oracle edges, the
oracle boundary, or any future observation.

| | affinity + Louvain (primary) | spectral/coherence (comparator) |
|---|---|---|
| valid candidates per step | **4.51** | 0.32 |
| lineages found | 464 | 168 |
| mean lineage duration | **17.3 steps** | 3.4 steps |
| longest lineage | 81 (the whole window) | 45 |
| lineages lasting ≥10 steps | **187** | 15 |
| lineages lasting ≥20 steps | **125** | 3 |
| mean size | 66.8 | 72.9 |
| mean step-to-step Jaccard | 0.871 | 0.908 |
| mean membership turnover | 0.073 | 0.055 |
| material retention at the end of a ≥10-step lineage | **0.498** | 0.721 |

The affinity detector dominates on every stability measure that matters here:
it proposes a usable candidate at essentially every step, and it follows
collectives an order of magnitude longer. The spectral/coherence proposal
produces a *valid* candidate on only a third of steps — its Fiedler split
usually returns one near-global core and one scattered remainder, which the
predeclared compactness and size filters reject.

The last row is the finding Stage 6.9 depends on: **a tracked collective keeps
its identity for 10+ steps while about half of its original members leave.**
Material identity and lineage identity are already coming apart on a *fixed*
lattice, before anything moves.

Neither the affinity graph nor the Fiedler split is interpreted as a Markov
blanket anywhere in this stage; the comparator is called a spectral/coherence
proposal throughout, and `tests/test_detector_and_tracker.py` asserts the
module says so.

## 4. Passive prediction: heading-stratified, and heavily recall-limited (§§11–13)

Heading stratification was necessary and is visible in the fits: interior birds
in a coherent collective spend nearly all their time on one heading, so
typically only **1–2 of 4 strata** clear the 40-sample minimum. Within a
stratum the interior is close to deterministic — per-stratum held-out log-loss
of 0.000–0.015 nats for deep members — which is precisely why passive
prediction has so little to work with.

Selecting prediction targets on the candidate's *observed periphery* rather
than uniformly was the single change that made passive inference work at all:
a bird buried inside a 130-member candidate cannot be influenced from outside
in one step, so it contributes fitting cost and no boundary signal. With that
restriction the top predictive-influence scores are dominated by true
interface members.

Result over 16 affinity candidates (snapshot panel, t = 60):

- mean \|B̂^pred\| = **5.4** against mean \|B_t^D\| = **20.6**;
- precision **0.837**, recall **0.239**, Jaccard **0.233**;
- the greedy rule terminated **naturally** in every run — 12/17 on
  `delta_tol_reached` and 5/17 on `no_candidate_above_min_gain`. **The `K_max`
  cap was never reached**, so no boundary was truncated by the computational
  safety limit and none was padded to it.

## 5. Construction vs certification: the challenger changes the verdict's meaning (§§14–15)

All 17 snapshot boundaries are **predictively sufficient relative to the
challenger class**: the 95% bootstrap upper bound on

  `L̂_challenge(B) = ℓ_test(M_B) − min_c ℓ_test(M_{B+c})`

averages **0.0051 nats** against δ = 0.01, evaluated once on untouched test
trajectories after the challengers were selected on train/validation only. The
challenger class includes a strongly L1-regularized sparse multivariate model
over **every** residual exterior source, so a jointly-informative residual set
would have been caught where Stage 6.7's `max_j Δ_j ≤ δ` rule could not see it.

The point is what this does *not* say. A 5-bird boundary that misses 76% of the
true 20-bird interface is still predictively sufficient against this class.
That is a statement about the challenger class and about how little residual
predictability the interior has, **not** a statement of conditional
independence, and it is not written as one anywhere.

## 6. Active probing recovers the dynamic interface; passive prediction does not (§§16–17)

The oracle reveal reports three quantities separately, as required:

| | L2 (16 affinity candidates) | L3 (6 gated candidates) |
|---|---|---|
| **identifiability** — `B^{causal,exact}` vs `B^D` | precision 1.000, recall 1.000, **J = 1.000** | precision 1.000, recall 1.000, **J = 1.000** |
| **estimation error** — `B̂^{causal,sampled}` vs `B^{causal,exact}` | precision 1.000, recall 0.602, **J = 0.602** | precision 1.000, recall 0.411, **J = 0.411** |
| **structural agreement** — `B̂^{causal,sampled}` vs `B^D` | **J = 0.602** | **J = 0.411** |
| predictive interface vs `B^D` | **J = 0.233** | **J = 0.139** |

Probe budget: ~904 probe calls and ~90,450 paired rollouts per candidate,
over ~50 candidate sources — that is what 60% recall costs at L2.

Two corrections to Stage 6.7's picture follow. First, its causal recovery was
**exactly** the top row — an identifiability statement, obtained with the exact
propagator, and it survives intact here. Second, the moment the estimator has
to be finite, recovery becomes recall-limited: `size_error` is **−8.4** at L2
and **−10.0** at L3, i.e. the probe systematically returns a *subset*. Since
precision is 1.000 in all 23 runs, that subset is always genuine — the probe is
a conservative estimator of a real interface, which is the useful failure mode
for a controller.

Active probing beats passive prediction on structural agreement by **2.6×** at
L2 (0.602 vs 0.233) and **3.0×** at L3 (0.411 vs 0.139).

## 7. What hidden edge gates add (§5, §19)

**No gate regime in the predeclared grid satisfies all three acceptance
conditions, and the binding one is G1.** Gating largely leaves flocking intact
(G3 passes for **6 of the 7** regimes — largest coherent component 259–292
against an ungated 283; only the weakest-persistence regime, stationary-on 0.60
with a 5-step mean run, fails on heading entropy 0.863 against a 0.719
tolerance) and it produces genuine turnover (G2 passes for 2 of 7). But it
measurably suppresses the mesoscopic regime at **every** setting tested: the
mesoscopic-episode fraction falls from 0.15 to 0.00–0.05. L3 was therefore run as an explicitly labelled robustness
probe at the weakest regime satisfying G2 and G3 (stationary-on 0.85, mean
on-run 10 steps), and it is never folded into the L2 headline.

Its effect on inference is clean and one-sided: **identifiability is untouched
(J = 1.000), estimation degrades** (causal 0.602 → 0.411, predictive 0.233 →
0.139). A latent persistent gate does not make the interface harder to define
or, given an exact intervention, harder to resolve; it makes it harder to
*estimate* from a finite probe budget, because part of the channel is closed
during the probe and the experimenter cannot tell that from a null effect.

## 8. Tracking a changing interface step by step (§18)

Twelve consecutive timepoints (t = 55…66), one tracked collective per episode,
two episodes, everything re-inferred from scratch at every step:

| | seed 15 | seed 17 |
|---|---|---|
| \|B_t^D\| range over 12 steps | 10 → 19 | 17 → 24 |
| true interface change per step, \|B_t^D △ B_{t−1}^D\| | 11.1 | 16.3 |
| **turnover similarity `T_B(t)`, causal** | **0.384** | **0.292** |
| turnover similarity `T_B(t)`, predictive | 0.130 | 0.200 |
| corr(\|ΔB^D\|, \|ΔB̂^causal\|) | 0.583 | 0.796 |
| corr(\|ΔB^D\|, \|ΔB̂^pred\|) | 0.571 | 0.539 |
| best temporal lag, causal | **0** | **0** |
| best temporal lag, predictive | **0** | **0** |

Two results here.

**The inferred interface changes when the true interface changes, and the
causal one does it 1.5–3× better than the predictive one.** `T_B` compares the
*symmetric differences*, so it cannot be inflated by a static overlap — an
estimator that returned a fixed set would score `T_B = 0` however good its
average Jaccard.

**Neither interface lags.** Jaccard against `B_{t−lag}^D` falls monotonically
with lag for both estimators on both episodes, so the best lag is 0 in all four
cases. This is expected for the probe, which interrogates the real current
state; that it also holds for the passive predictor says its errors are
*recall* errors, not staleness — it is not tracking a stale interface, it is
tracking a thin one.

## 9. Adaptive control (§§20–21)

**First, the honest framing: the task is infeasible at this scale.** The
`adaptive_oracle` arm — handed the true interface and the exact influence
matrix — reaches only 0.21–0.33 mean final target fraction across the whole
predeclared (K_act, horizon) grid, against a 0.5 target
(`data/control_feasibility.json`). Stage 6 steered a 20-bird interior with a
12-bird boundary on a 100-bird lattice; this stage's blind detector proposes
collectives of 95–145 birds on a 400-bird lattice, where 20 actuators are a
fifth of the interface and the interior's own consensus is 5–10 hops deep.
**Sparse boundary steering does not scale from a 20-bird collective to a
120-bird one, and no absolute success is claimed below.**

What the comparison can still answer is the ordering. All arms run at the
grid's best oracle setting (K_act = 20, horizon = 30), scored on `I0` — the
collective detected at the control start — with `random_matched` and
`predictive` held to `adaptive_causal`'s own realized per-step actuator count:

| arm | development | held-out | all 8 episodes | mean actuators |
|---|---|---|---|---|
| **adaptive inferred causal** | 0.445 ± 0.156 | **0.533 ± 0.304** | **0.489 ± 0.245** | 7.7 |
| adaptive **oracle** causal | 0.327 ± 0.185 | 0.494 ± 0.277 | 0.411 ± 0.250 | 11.2 |
| **frozen** initial causal | 0.330 ± 0.189 | 0.466 ± 0.321 | 0.398 ± 0.272 | 6.2 |
| matched-budget random | 0.242 ± 0.126 | 0.407 ± 0.320 | 0.324 ± 0.257 | 7.7 |
| predictive interface | 0.274 ± 0.213 | 0.127 ± 0.148 | 0.200 ± 0.197 | 3.9 |
| no control | 0.053 ± 0.052 | 0.076 ± 0.131 | 0.064 ± 0.100 | 0.0 |

The ordering is identical on development and held-out seeds except that
`predictive` collapses on held-out, and it is stable across the whole
trajectory (Fig. 6.8-5, right panel). What survives the noise at n = 8:

- **every actuated arm beats no control** (0.064) by a wide margin;
- **the three causal arms beat matched-budget random** (0.324), which beats
  **the predictive interface** (0.200) — actuating a predictively-sufficient
  boundary is *worse than actuating a random set of the same size*, replicating
  Stage 6.7's control diagnostic on a moving interface;
- **adaptive (0.489) ≥ frozen (0.398)**, but with SD ≈ 0.25 across 8 episodes
  this gap is **not statistically resolved** and is not claimed as one.

`adaptive_causal` scoring above `adaptive_oracle` is likewise within noise. The
one thing that should not be over-read: the oracle arm spends more actuators
(11.2 vs 7.7) because it sees influence the probe misses, and still does not do
better — at this scale the binding constraint is the task, not the interface
estimate.

## 10. Answers to the Stage-6.8 questions (§19)

1. **Can the candidate collective be detected without oracle structure?**
   Yes. 4.5 valid candidates per step from positions and headings alone, 464
   lineages across 22 episodes.
2. **Does candidate detection remain stable in the mesoscopic regime?**
   Yes — mean lineage 17.3 steps, 187 lineages ≥10 steps, 125 ≥20 steps, mean
   step-to-step Jaccard 0.871. The spectral/coherence comparator does not (3.4
   steps, valid on only 32% of steps).
3. **Can passive prediction track heading-dependent interface changes?**
   Weakly. It changes when the truth changes (`T_B` 0.13–0.20, correlation
   0.54–0.57) but recovers only 23% of the interface, and heading
   stratification is data-starved because coherent interiors rarely change
   heading — typically only 1–2 of 4 strata are fittable.
4. **How much lag does the predictive interface have?**
   None. Best lag 0 on both episodes; its deficit is recall, not staleness.
5. **Does active probing recover dynamic causal channels better than passive
   prediction?** Yes, decisively: J 0.602 vs 0.233 at L2 (2.6×), 0.411 vs
   0.139 at L3 (3.0×), and `T_B` 1.5–3× better.
6. **How many interventions are required?**
   ~904 probe calls / ~90,450 paired rollouts per candidate over ~50 candidate
   sources buys precision 1.000 at recall 0.602. The control loop runs at a
   much smaller online budget (25 rollouts × 2 repeats, every 6 steps).
7. **Does FOV make the causal graph easier to infer than arbitrary stochastic
   edge churn?** Yes. FOV churn is *state-determined*: the interface follows
   the receivers' headings, which the observer can see. Gate churn is latent.
   At comparable edge-flip rates, structural agreement is 0.602 under FOV alone
   and 0.411 with gates added.
8. **What extra difficulty do persistent hidden edge gates introduce?**
   Purely estimation difficulty. Identifiability is unchanged (1.000), the
   probe's recall falls 0.602 → 0.411 and the predictive interface 0.233 →
   0.139. A closed gate is indistinguishable from a null effect at a finite
   probe budget. Gating also suppresses the mesoscopic regime itself
   (episode fraction 0.15 → 0.00–0.05), which is why no gate regime passed the
   predeclared acceptance conditions.
9. **Does boundary screenability remain compact as node identities change?**
   Yes, and it stays *too* compact: mean \|B̂^pred\| = 5.4 against \|B^D\| =
   20.6, with 17/17 certified predictively sufficient relative to the
   challenger class.
10. **Does `B^pred ≠ B^causal` remain?** Yes, and it widens under a moving
    interface: `J(B̂^pred, B^{causal,exact}) = 0.233` at L2 and 0.139 at L3,
    with the predictive interface roughly a quarter the size of the causal one,
    and actuating it performs worse than random.

## 11. Figures

| figure | content |
|---|---|
| `fig_6_8_1_phase_map` | uncontrolled phase map, L1 vs L2, across β and precision scale |
| `fig_6_8_1b_size_scan` | the finite-size scan that set the operating point |
| `fig_6_8_2_interface_changes` | the true FOV interface changing as birds reorient (L0 ≡ constant) |
| `fig_6_8_3_interfaces` | detected interior + predictive + sampled causal + oracle causal |
| `fig_6_8_4_precision_recall_lag` | precision/recall/size/turnover-similarity over 12 steps |
| `fig_6_8_5_adaptive_vs_frozen` | the six control arms |
| `fig_6_8_6_fov_vs_gated` | L2 vs L3, and why no gate regime passed |

## 12. Caveats, stated plainly

- **Lattice size changed.** `nn = 100 → 400` is the one deviation from the
  frozen Stage 6–6.7 convention. It was forced by the phase scan, not chosen
  for convenience, and nothing in Stages 6–6.7 was re-run at the new size.
- **Positions are visible to inference code.** On a fixed lattice this makes
  geometric adjacency recoverable. What stays hidden is the heading-dependent
  live subset. This is a genuine weakening of Stage 6.7's firewall.
- **Two disclosed compute restrictions** shape the predictive results: the
  source pool radius (3.5 lattice units, ~2.5× the interaction geometry) and
  the observed-periphery target selection. The second is not cosmetic — before
  it, uniform target subsampling found essentially no predictive influence at
  all, because deep interior members carry no boundary signal.
- **Small n.** 22 mesoscopic episodes from 600 screened seeds; 17 snapshot
  candidates; 6 gated candidates; 2 time-series episodes; 8 control episodes.
  Every SD is reported. The control gap between adaptive and frozen is not
  resolved at this n.
- **The certification is relative to its challenger class**, not a test of
  conditional independence, and is written that way everywhere.
- **L3 fails its own acceptance condition G1** and is reported as a labelled
  robustness probe, never folded into the L2 headline.

## 13. Stage 6.9 gate verdict (§23)

| criterion | verdict |
|---|---|
| 1. the **L1** regime supports persistent non-global collectives | **FAIL as literally stated.** No parameter setting and no lattice size tested produces a mesoscopic episode on the fixed undirected graph; persistence and non-globality are the same quantity there (`PHASE_MAP.md` §2). **PASS at the actual operating point**: L1's parameters *plus the L2 FOV rule*, at nn = 400, produce persistent non-global collectives in 22 of 600 screened episodes (3.7%). |
| 2. **L2 produces genuine interface turnover** | **PASS.** 12.7 distinct interfaces in 61 steps against L0's 1; 1.4 nodes in/out per step; node interface lifetime 17.5 steps; 4.8% of directed edges flip live/dead per step. |
| 3. the candidate detector tracks **some collectives for meaningful durations** | **PASS.** 187 lineages ≥10 steps and 125 ≥20 steps across 22 episodes, at mean size 67 — while material retention falls to 0.498. |
| 4. blind predictive and/or active causal inference produces **interpretable dynamic estimates** | **PASS.** Finite probing: precision 1.000, recall 0.602, `T_B` 0.29–0.38, lag 0. Passive prediction: interpretable but thin (recall 0.239). |

**Verdict: proceed to Stage 6.9, with criterion 1 recorded as a partial
failure.** The substantive requirement — a persistent, non-global, trackable
collective with genuine constituent turnover and an inferable moving interface
— is met, but *only because of the FOV rule*, and the L1 negative result is
carried forward rather than buried: on a fixed undirected interaction graph
this model family has no mesoscopic regime at all.

Two things Stage 6.9 must inherit rather than repeat:

- **the control task does not scale.** Steering must be posed at a scale where
  the oracle arm can actually succeed, or its failure will be a scale artefact
  again.
- **material identity already fails before lineage identity**, on a *fixed*
  lattice, at 50% retention over 10 steps. Stage 6.9's question — whether
  functional identity survives in a co-moving frame while membership turns over
  — is therefore a sharpening of something already visible here, not a new
  phenomenon conjured by adding motion.
