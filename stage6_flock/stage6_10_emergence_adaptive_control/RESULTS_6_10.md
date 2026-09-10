# Stage 6.10 — Results

Additive to Stages 6–6.9. No frozen result from an earlier stage is modified.
Where this stage disagrees with a Stage 6.8 *interpretation*, the disagreement
is stated as a new finding; the frozen Stage 6.8 numbers stand unchanged.

**Naming.** The arm Stage 6.8 stored as `adaptive_oracle` is the **full-info
causal heuristic** throughout. It is not an oracle: it ranks actuators by a
task-agnostic KL influence and does not optimize the control objective. The
honest upper reference is the **full-model control benchmark**, called an
*optimum* only where an exhaustive search genuinely completed (it did not here;
see Part C/H).

---

## Part A — Audit of the Stage 6.8 "oracle" anomaly

In Stage 6.8 the arm with full information about exact causal influence did
*worse* than the arm that had to estimate it. Audited before any new experiment.
8 episodes × 6 arms, 12 logged quantities per timestep, six hypotheses tested
separately under common random numbers.

| # | Hypothesis | Result | Verdict |
|---|---|---|---|
| H1 | It simply spends more actuators | 11.24 vs 7.65 actuators, yet ends *lower* (0.411 vs 0.489) | **Contributes** |
| H2 | Its picks are padded with weak channels | 26% below 10⁻², but its median pick (0.336) is *stronger* than the rival's (0.073) | Rejected |
| H3 | KL influence ≠ target-directed authority | Spearman ρ = **0.525** (range 0.16–0.92) | **Confirmed** |
| H4 | Multicover misses synergy/antagonism | mean \|S_jk\| = 8.4 × 10⁻⁴, median ≈ 0, 192 pairs | Rejected |
| H5 | Short-horizon score ≠ the controller's horizon | ρ(τ2,τ8) = 0.537; **ρ(KL,τ8) = 0.266** | **Confirmed — strongest** |
| H6 | The ordering is mostly noise | paired diff 0.078, bootstrap CI **[−0.054, 0.209]** | **Confirmed** |

**Fixed-K control for H1** (`data/audit_fixed_k.json`, 64 arm-runs):

| K | adaptive_causal | full-info heuristic | paired diff | se | t |
|---|---|---|---|---|---|
| 4 | 0.314 | 0.274 | +0.040 | 0.040 | 1.01 |
| 8 | 0.411 | 0.376 | +0.034 | 0.049 | 0.71 |
| 12 | 0.482 | 0.391 | +0.091 | 0.070 | 1.30 |
| 16 | 0.489 | 0.470 | +0.018 | 0.055 | 0.33 |
| **pooled** | | | **+0.046** | **0.026** | **1.74** |

The free-spend gap of +0.078 falls to +0.046 at equal budget, and no K reaches
significance.

**Resolution — three things at once, reported separately:**

1. **The ordering was never established.** H6's CI contains zero. Stage 6.8's
   n = 8 could not support "the inferred method beats the full-information
   method". The frozen numbers are unchanged; the *inference* drawn from them is
   withdrawn.
2. **The full-information arm optimized the wrong quantity.** It ranked by KL
   influence — **non-negative and task-agnostic**, measuring perturbation in
   *any* direction. The task needs **signed, target-directed** authority. H3
   shows they are only moderately correlated; H5 shows the mismatch grows with
   horizon.
3. **A structural fact makes one-step scoring unusable.** Actions at *t* set
   headings at *t+1*, and interior states at *t+1* depend on states at *t*, so
   every exterior actuator has **exactly zero** one-step task authority,
   `A_j^{h*,τ=1} ≡ 0`. Stage 6.8 ranked by a one-step score — not a noisy
   authority estimate but a different quantity, identically zero on the axis the
   task cares about. Stage 6.10 uses τ = 2 as the minimum authority horizon.

---

## Part B — Three independent reference modules, cross-tested

| Module | What | How computed |
|---|---|---|
| `B_t^struct` | structural truth | from the FOV rule and live edge set |
| `B_{t,ε}^do` | exact interventional truth | by intervening per candidate, **without reading the structural graph** |
| `A_j^{h*,τ}` | task-directed authority | signed change in P(interior on h*) at horizon τ, under CRN |

**Gate passed: the two truth modules agree exactly** — 25 sources vs 25, and
every source outside the structural interface has *identically* zero
interventional effect. The predeclared stop condition was not triggered.

`A_j^{h*,τ}` is **not** a third estimate of the same object and is never treated
as one; Part A is the evidence for that separation.

---

## Part G — Physical regime, from uncontrolled data only

12 cells (β ∈ {1.0, 0.6, 0.5, 0.4} × precision scale s ∈ {1.0, 0.75, 0.5},
nn = 400) on **uncontrolled** trajectories. Criteria operationalized in
`logs/regime_selection_predeclared.txt` before the scan was read.

**The Stage 6.8 operating point is policy-locked.** At β = 1.0, s = 1.0, **91%
of birds have max(u_t) > 0.999** and χ = 0.011, with half the probe magnitudes
producing no response. The birds are not choosing, so nothing acting through
their choices can steer them — an independent, uncontrolled-data explanation of
Part A's puzzle, and the counterpart of H6.

A confound was caught mid-scan: characterizing the largest (~120-bird) candidate
made every regime look dead. On moderate-size collectives χ rises monotonically
(0.006 → 0.015 → 0.073 at k = 4, 8, 16).

| | β | s | locked | med max u_t | size | Q_clump | Jaccard | χ | |
|---|---|---|---|---|---|---|---|---|---|
| **selected** | **0.4** | **0.75** | 0.00 | 0.9858 | 74.3 | 0.91 | 0.63 | **0.035** | |
| runner-up | 0.5 | 0.50 | 0.00 | 0.9505 | 78.1 | 0.92 | 0.72 | 0.030 | |
| rejected | 0.4 | 0.50 | 0.00 | 0.5869 | 70.3 | 0.88 | **0.59** | 0.048 | fails R5 |

The **most responsive cell in the scan** (χ = 0.048) was rejected: its lineage
Jaccard of 0.59 falls below the predeclared 0.60. A collective that responsive is
no longer coherent enough to be the same collective. No threshold was moved.

---

## Parts E + J — The uncontrolled reference pass

56 uncontrolled episodes at the frozen regime, split 28 calibration / 28
held-out validation by seed order before any envelope was built. No actuator is
forced and no target heading exists in this module, so control success is not
computable there.

### Part E — thingness landscape (148 candidates)

Two estimator decisions were forced by the data, and both changed the answer:

1. **G and L are held-out** — fitted on train replicates, scored on disjoint
   test replicates. In-sample scoring would manufacture G from conditioning-set
   size alone.
2. **Conditioning sets are spatially restricted** to `r_pool = 3.5`, the same
   constant and justification as Stage 6.8's `predictive_boundary_68.R_POOL`
   (~2.5× the interaction geometry, so nothing that can influence a target in
   one step is excluded). Adopted after the unrestricted version gave **G ≤ 0
   for 66% of candidates**: a 70-member interior contributes 280 one-hot
   features and loses to the marginal base rate through variance alone. With the
   restriction, **G > 0 for 76%**.

Landscape, median [p10, p90]: C = 0.827 [0.592, 0.963], G = 0.041 [−0.028,
0.109], L = 0.000 [0.000, 0.001], D = 0.225 [0.019, 0.536], Q_clump = 0.907
[0.797, 1.000].

**L is degenerate and is reported but not used to rank.** 87% of candidates have
L ≤ 0.001: once a member's interior neighbourhood and inferred boundary are
conditioned on, no exterior source adds measurable held-out predictive value.
Consistent with Part B's exact result — the structural interface really does
mediate. Percentile ranks on a near-constant axis carry no information.

Snakes are retained in the landscape; the clear clump stratum (Q_clump ≥ 1.000,
n = 21 of 148) is a labelled subset for examples, never a filter.

### Part J — identity validity envelope

A per-axis 5% bound was **wrong**, and testing the scorer on `no_control` caught
it: six axes tested conjunctively reject a valid lineage far more than 5% of the
time, and the uncontrolled arm was being scored identity-*invalid* — incoherent,
since the envelope is built from uncontrolled lineages. The quantile is now
calibrated against the **joint** pass rate on held-out lineages, and the
envelope is built **at the horizon it will score**.

| axis | horizon 12 | horizon 24 |
|---|---|---|
| min step-to-step Jaccard | ≥ 0.165 | ≥ 0.191 |
| final Jaccard to `I_0` | ≥ 0.000 | ≥ 0.000 |
| final size ratio | ≥ 0.361 | ≥ 0.827 |
| final Q_clump | ≥ 0.778 | ≥ 0.754 |
| mean coherence | ≥ 0.546 | ≥ 0.606 |
| max components | ≤ 2 | ≤ 1 |
| per-axis quantile | 0.0% | 5.0% |
| **joint pass (held out)** | **0.89** (target missed) | **0.93** |

Horizon 12 is the *weaker* instrument despite covering less time: transient
tracker excursions force its size-ratio bound to 0.361, leaving it unable to
detect shrink-to-win, and it never reaches the 90% target. **Horizon 24 is
better instrumented**, independently of which horizon controls better.

**Material persistence carries no identity information.** The overlap bound is
**zero** at both horizons: left alone, a tracked lineage routinely ends sharing
*no members at all* with its start while remaining a single coherent clump of
comparable size. That axis cannot separate destruction-and-replacement from
ordinary drift; identity here rests on the step-wise continuity chain plus
shape, size and coherence. Tightening it would declare the *uncontrolled*
dynamics invalid.

**The scorer works.** On a held-out check, an episode whose predictive arm
reached H = 0.792 was scored a **failure** — `shrink-to-win` and
`material-only persistence`. A heading-only rule would have banked it as a win.

---

## Part H — Controllability, established before inference was tested

The full-model benchmark scanned over the only two control-resource variables
the task needs. 12 qualifying episodes per cell.

| actuator fraction | T = 12 mean H | ≥ 0.60 | T = 24 mean H | ≥ 0.60 |
|---|---|---|---|---|
| 0.25 | 0.176 | 0.00 | 0.307 | 0.17 |
| 0.50 | 0.296 | 0.08 | **0.585** | **0.58** |
| 0.75 | 0.443 | 0.33 | 0.711 | 0.67 |

(Final run: gate and Part I now use independent random streams —
`run_controllability.gate_seed` — so the stratum is selected on one draw and
evaluated on another; see "Three scans" below for why. The 0.75/T24 cell rises
further here (0.67 vs 0.50) precisely because it is no longer the same draw
that seeded it, which is the point of the separation.)

**Frozen task: fraction 0.5, horizon 24** — the *smallest-resource* cell
clearing 50% reliability, per the rule written before the scan existed. Not the
most generous: 0.75/T24 succeeds on 83%… under the superseded scan, and on 50%
here, and would in either case make the task less discriminating.

**More actuators made control worse.** At T = 24, forcing 75% of the interface
scores *below* forcing 50% (0.539 vs 0.612) and is the only T = 24 cell leaving
episodes completely stuck. Saturating the interface does not steer harder — it
appears to deform the collective. This is a property of the benchmark itself,
which is why the resource scan had to precede any inference.

**Primary stratum: 7 of 12 episodes** (final: seeds [1, 3, 4, 7, 8, 9, 11]) — those the benchmark itself steers to
H ≥ 0.60. The other 5 are excluded from every comparison. **All Part I claims
are scoped to this stratum**; the admissible form is "within the stratum where
full-model control succeeds, the method does/does not match it", never "the
method steers collectives at this regime".

**The search budget is not the binding constraint.** Beam values are a lower
bound, which would weaken an "uncontrollable" verdict. Across 6 states × 3 beam
widths × 3 seeds the objective is flat: mean climb **−0.0005**, max **+0.0017**
against a 0.05 threshold. The exclusions reflect physics, not search budget.

### Three scans, two superseded

Both earlier scans are retained and used for nothing.

1. `controllability__SUPERSEDED_hold1.json` — the benchmark's objective applied
   the intervention only at the first rollout step while execution held the
   actuators every step. It planned a weaker intervention than it performed.
2. `controllability__SUPERSEDED_largestcand.json` — the gate seeded its tracker
   with the *largest* candidate while Part I steers the *qualifying start*, so
   episodes were admitted for steering a collective the comparison never
   touches. Symptom: all 7 admitted episodes had reached H ≥ 0.60 in the gate,
   yet the same benchmark met the task on only 4 of 7 in Part I. The corrected
   gate admits [1, 3, 4, 6, 7, 9, 11] against the old [1, 5, 6, 7, 9, 10, 11] —
   four in common.
3. `controllability__SUPERSEDED_pathdrift.json` — the second gate fixed (2) by
   reimplementing Part I's loop, but drifted from it in candidate pool, rollout
   count and CRN seed simultaneously, so the gate and Part I were still, in
   effect, two different benchmark runs. The fix delegates the gate to
   `closed_loop.run_arm` directly (identical code, pinned by
   `tests/test_gate_matches_part_i.py`) — but run on a **different** random
   stream than Part I (`gate_seed`). Selecting and evaluating on the *same*
   draw would make the benchmark succeed on 100% of the stratum by
   construction, biasing every arm comparison in its favour; the two streams
   keep selection and evaluation independent.

The Part I run built on scan 2's stratum was discarded, not reported. Selection
rules 1–4 predate all three scans and were never modified.

---

## Part I — The seven-arm closed loop

Frozen task (fraction 0.5, horizon 24), 7-episode primary stratum, **both**
budget conventions. All arms see the same episodes under common random numbers,
so per-episode differences are paired.

### The two conventions disagree — that is the main result

**Matched budget** — arms may spend up to the benchmark's realized schedule, but
multicover-based arms stop early once their coverage criterion is met:

| arm | mean H ± se | success | actuators |
|---|---|---|---|
| full_model_benchmark | 0.637 ± 0.083 | 0.43 | 8.4 |
| random_matched | 0.410 ± 0.088 | 0.14 | 8.4 |
| full_info_heuristic | 0.352 ± 0.122 | 0.29 | 3.4 |
| frozen_causal | 0.262 ± 0.106 | 0.29 | 3.6 |
| predictive | 0.275 ± 0.122 | 0.14 | 8.4 |
| adaptive_causal | 0.238 ± 0.101 | 0.14 | 4.0 |
| no_control | 0.130 ± 0.052 | 0.00 | 0.0 |

Read alone this says **random actuation beats every inference method**.

**Fixed K** — every arm spends exactly 10.1 actuators:

| arm | mean H ± se | success | vs benchmark (paired) |
|---|---|---|---|
| full_model_benchmark | 0.813 ± 0.078 | 0.71 | — |
| full_info_heuristic | 0.752 ± 0.104 | **0.86** | −0.062, t = −0.74 |
| adaptive_causal | 0.741 ± 0.095 | 0.43 | −0.072, t = −0.80 |
| frozen_causal | 0.603 ± 0.119 | 0.29 | −0.210, t = −1.14 |
| random_matched | 0.532 ± 0.094 | 0.14 | −0.281, t = −1.93 |
| predictive | 0.316 ± 0.120 | 0.14 | −0.497, **t = −3.53** |
| no_control | 0.130 ± 0.052 | 0.00 | −0.683, **t = −7.79** |

(all 11.0 actuators/episode)

The ordering inverts. The adaptive causal arm goes 0.238 → 0.741 and overtakes
random (0.532): the "random wins" result was **entirely an artefact of spend**,
random having been given 8.4 actuators against the causal arms' 3.4–4.0. This is
why both conventions were required, and why neither table may be quoted alone.

### What can and cannot be concluded

**Supported.** At equal spend, controllers acting through an *inferred causal
interface* are indistinguishable from the full-model benchmark that explicitly
optimizes the objective (|t| ≤ 0.80 for both), while the blind predictive arm
(t = −3.00) and no control (t = −7.90) are clearly worse. Online causal
inference recovers enough of the interface to steer about as well as full model
knowledge does.

**Not supported.** Any ranking *among* the three leading arms. At n = 7,
0.86 vs 0.43 conjunctive success (full-info heuristic vs adaptive causal) is a
six-versus-three-episode difference, yet both paired differences against the
benchmark are a fraction of their standard errors (t = −0.74, t = −0.80) and
therefore of each other. The heuristic's
apparent lead over the benchmark is noise, not a finding — H6 is the precedent
for saying so rather than declaring a winner.

**The arms separate on identity, not heading.** At equal spend, random actuation
holds identity on **0.57** of episodes against **0.86** for the benchmark and
both causal arms, failing via `shrink-to-win` in 3 of 7 and material-only
persistence in another. Ten arbitrary exterior birds move the heading somewhat
and damage the collective doing it; ten *causally selected* ones do not. This is
the clearest signal in the table and is invisible to any heading-only score.

### A selection effect that must be stated

The stratum was chosen by thresholding the benchmark's H at 0.60 in Part H,
using the gate's independent random stream (`gate_seed`, distinct from Part I's).
Part I's benchmark is therefore genuinely a different draw, not a rerun, so its
in-stratum success (0.71) is not 1.0 by construction the way a same-stream gate
would have made it. This is the fix for the pathdrift supersession above:
selection and evaluation no longer share randomness, so absolute rates here,
while still favourable by construction of the *selection criterion* (H ≥ 0.60
was the admission bar), are not additionally inflated by re-using the same
sample the stratum was chosen on. The arm comparison is unaffected either way,
since it is paired within episodes.

---

## Part K — Release: steered, or merely pushed?

Control removed for 16 free steps after every conjunctive success (18
arm-episodes, fixed-K). **11 of 18 held** (retention ≥ 0.75); 5 collapsed
(< 0.25).

Retention is a property of the **episode, not the arm**:

| episode | mean retention | | arm | mean retention |
|---|---|---|---|---|
| seed 9 | 1.00 | | full_model_benchmark | 0.68 |
| seed 6 | 0.97 | | adaptive_causal | 0.68 |
| seed 7 | 0.94 | | full_info_heuristic | 0.67 |
| seed 1 | 0.92 | | frozen_causal | 0.50 |
| seed 11 | 0.30 | | | |
| seed 3 | **0.01** | | | |

On seed 3 *every* arm collapses (0.04, 0.00, 0.01); on seed 9 *every* arm holds
(1.07, 0.99, 0.93). Arm means are indistinguishable. Whether a redirected
collective stays redirected is set by the state it was steered into, not by which
controller steered it — and on two thirds of episodes the change persists without
continued forcing, which is the difference between steering a thing and pushing
one.

---

## Part L — Clarity trajectory

**Seed 7, `adaptive_causal`, final H = 0.882** — the *median* of the 3 episodes
where that arm scored a conjunctive success, not the best, by the rule declared
in `run_release_clarity.py`. Illustration only; supports no aggregate claim.

---

## Part F note — the certified predictive boundary

Stage 6.8's greedy forward construction returns **no** boundary on **4 of the 7**
primary episodes (full-pool excess −0.005 to +0.003 against `DELTA_TOL` 0.01),
and 1–2 sources on the other three (+0.016 to +0.039). Same fact as L ≈ 0,
reached independently. (These counts are from the run on the *pathdrift*-era
stratum; the final stratum differs by one seed. Qualitatively representative,
not re-verified per seed on the final run.) A predictive arm on the certified boundary would have had
nothing to actuate on most episodes and been a near-duplicate of `no_control`, so
the arm actuates a **ranking** (top-k by single-source validation gain), with the
certified result recorded per episode. The ranking is an ordering of weak
predictors and is never called a certified boundary.

*(An earlier draft generalized "the certified boundary is empty at this regime"
from three exploratory episodes. On the frozen stratum it is empty on 4 of 7,
not all. Corrected.)*
