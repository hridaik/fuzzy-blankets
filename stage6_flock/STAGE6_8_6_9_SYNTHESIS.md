# Cross-stage synthesis — what survives Stages 6.8 and 6.9

Written after `stage6_8_dynamic_interactions/RESULTS_6_8.md` and
`stage6_9_translating_collective/RESULTS_6_9.md`. It answers the ten questions
posed for the synthesis and nothing else; where a stage failed, the failure is
the answer.

Nothing in Stages 6–6.7 is modified by either stage. Their results continue to
describe the fixed undirected Moore graph at `nn = 100`.

---

## What the two stages actually removed

Stages 6–6.7 rested on four conveniences. Stage 6.8 removed three of them and
Stage 6.9 the fourth:

| convenience | removed by | replaced with |
|---|---|---|
| the interaction graph is fixed and undirected | 6.8 (L2) | a heading-dependent **directed** graph — 12.7 distinct interfaces in 61 steps where L0 has 1 |
| the causal estimator is the **exact** propagator | 6.8 | **finite active probing**, with real sampling error |
| the interior `I` is **supplied** | 6.8 | detected online from positions and headings |
| the collective is **stationary** | 6.9 | attempted — a translating collective on a torus. **The Stage 6.9 feasibility gate FAILS at the specified interaction scale**, so this convenience was *not* successfully removed. See Q7–Q9. |

---

## The ten questions

### 1. Which current conclusions survive moderate temperature changes?

Almost none of the *phenomenology* does, and that is the first surprise. On the
fixed graph, sweeping β across `{0.25 … 1.5}` and the precision scale across
`{0.5 … 2.0}` — 30 cells — produces only two behaviours: non-persistent churn
(β = 0.25, component lifetime 1.08 steps) or near-global consensus (β ≥ 0.5,
one ≥90-bird component 64–84% of the time). There is **no intermediate
regime at any temperature**, and the reason is mechanical rather than a search
failure: `flock_sim.active_inference.compute_G` never reads `z[i]`, so a bird's
next heading does not depend on its own current heading and a domain has no
inertia. Domain persistence and single-bird persistence are the same quantity,
so non-globality and persistence cannot be had together.

What *does* survive temperature change is the **methodological** conclusion,
because it was re-derived at a different operating point (nn = 400, L2) and
still held: predictive sufficiency arrives long before structural recovery, and
`B^pred ≠ B^causal`.

### 2. Which survive state-dependent directed interactions?

The core Stage 6.7 findings survive, with one important correction.

- **Survives:** identifiability. With an exact intervention the causal
  interface is recovered perfectly — precision = recall = 1.000 on every one of
  the 23 snapshot and gated candidates, exactly as at Stage 6.7.
- **Survives:** the predictive/causal separation. `J(B̂^pred, B^{causal,exact})
  = 0.233` at L2; the predictive interface is a quarter the size of the causal
  one; actuating it controls *worse than a random set of the same size*.
- **Survives, more strongly:** predictive sufficiency without structural
  recovery. 17/17 boundaries are predictively sufficient relative to the
  challenger class (95% upper bound 0.0051 nats vs δ = 0.01) while recovering
  24% of the true interface.
- **Corrected:** Stage 6.7's "perfect causal recovery" was an artefact of the
  exact propagator. Once the estimator is finite, recall falls to 0.602 at a
  90,000-rollout budget. Stage 6.7 measured identifiability and reported it as
  recovery.

One genuinely new requirement: predictors must be **heading-stratified**,
because FOV makes a source's relevance conditional on the receiver's
orientation. And stratification is data-starved exactly where it is needed —
inside a coherent collective only 1–2 of 4 strata ever clear the sample
minimum, because the receivers rarely change heading.

### 3. Can predictive boundaries track a genuinely changing interface?

**Weakly yes, with no lag but very little recall.** Over 12 consecutive steps
the predictive interface changes when the truth changes (turnover similarity
`T_B` 0.13–0.20; correlation between change magnitudes 0.54–0.57), and its best
temporal lag is **0** — Jaccard against `B^D_{t−lag}` falls monotonically with
lag. Its deficit is not staleness but thinness: mean size 5.4 against a true
interface of 20.6, recall 0.239.

### 4. Can finite active probing recover dynamic causal interfaces?

**Yes, and it is the only method here that does so usefully.** Precision
**1.000 in all 23 runs** — it never once named a bird that was not really in
`B_t^D` — at recall 0.602 (L2). `T_B` 0.29–0.38, best lag 0. It is a
*conservative* estimator: `size_error = −8.4`, i.e. it returns a genuine subset.
For a controller that is the right failure mode, and it shows: the adaptive
inferred-causal arm was the best-performing control arm.

Cost: ~904 probe calls and ~90,450 paired rollouts per candidate over ~50
candidate sources. Common random numbers matter — with paired rollouts a bird
whose live in-edges are unchanged by the intervention contributes exactly zero,
so the estimator's variance comes only from the birds actually affected.

### 5. Does random persistent edge gating materially change those answers?

**It changes exactly one of them, and cleanly.** Identifiability is
**untouched** (J = 1.000 with the gate-aware exact propagator). Estimation
degrades: causal structural agreement 0.602 → 0.411, predictive 0.233 → 0.139.
A closed gate is indistinguishable from a null effect at a finite probe budget,
so hidden gating is a **pure estimation cost**, not an identifiability cost.

Separately, and reported as a negative result: **no gate regime in the
predeclared grid satisfied all three acceptance conditions.** Gating leaves
flocking intact but suppresses the mesoscopic regime itself (episode fraction
0.15 → 0.00–0.05), so L3 ran as a labelled robustness probe rather than as a
qualifying condition.

### 6. Can a collective be detected without supplying its identity?

**Yes, comfortably, and this is the clearest positive result of Stage 6.8.**
The affinity-plus-Louvain detector proposes 4.5 valid candidates per step from
positions and headings alone, yielding 464 lineages across 22 episodes with
mean duration 17.3 steps, 187 lasting ≥10 steps and 125 ≥20 steps.

The paper's Fiedler-style detector, run alongside as a comparator and called a
*spectral/coherence proposal* throughout, does **not**: it produces a valid
candidate on only 32% of steps and its lineages last 3.4 steps on average. Its
split usually returns one near-global core and a scattered remainder, which the
predeclared compactness and size filters reject.

### 7. Can the same detector track a translating group?

**Mechanically yes; usefully no, at the specified scale.** With torus distance
substituted for lattice distance and nothing else changed, the detector
proposed and followed a candidate in **40 of 40** moving episodes. But at the
specification (`R = 0.9`, mean realized live in-degree **8.9**, the Moore
scale) what it follows is not a coherent group: the tracked set is ≤2 spatial
components on only **40%** of steps, averaging **3.8 pieces**, with deformation
`D_deform = 0.185` and `R_F = 0.658`. Median tracked duration is 62 steps
against 160 off-specification.

So the detector transfers; the *phenomenon* does not.

### 8. Does material lineage fail before co-moving functional lineage?

**On the fixed lattice, yes. On the torus at specification, the question does
not arise, because functional lineage fails too.**

On the **fixed lattice** (6.8) this is solid: tracked collectives keep their
identity for 10+ steps while material retention falls to **0.498**. Material
identity is already failing before anything moves, and that result stands.

On the **torus at specification** (6.9), material retention falls readily
(T3 satisfied in 0.90 of episodes, mean final `R_M = 0.32`) but co-moving
functional similarity falls with it (`R_F = 0.658`, T4 satisfied in only 0.38),
and the world-frame and de-translated field distances are nearly equal — what
remains after removing the best bulk translation is **deformation, not
transport**. That is the pre-declared "destroyed and replaced rather than
transported" outcome, and it is reported as such.

The dissociation between the three identity notions — where two families of
episodes with identical path length, identical `R_F` and identical lineage
overlap are separated only by `R_M` — was obtained at **3× the specified
connectivity** and is **not claimed** as a result. It is retained only because
the contrast identifies connectivity as the controlling variable:

| mean live in-degree | components | `D_deform` | `R_F` | gate pass rate |
|---|---|---|---|---|
| **8.9** (specification) | 3.80 | 0.185 | 0.658 | **0.00** (40 episodes) |
| 14.8 | — | — | 0.89 | 0/6 |
| 16.5 | — | — | 0.94 | 2/6 |
| 21.2 (superseded) | 1.15 | 0.023 | 0.958 | 0.40 (40 episodes) |

**The same over-connection that makes a moving collective cohere is what makes
its causal interface vanish** — at degree 21 the policy posterior saturates to
exactly 1.0 for 77% of interior birds, and the *exact* propagator finds 1 live
channel of 47. In this model family you can have a trackable translating
collective or an inferable causal interface, but not both.

### 9. Can the group be guided while functional identity survives?

**Not answered — and deliberately not answered.** Stage 6.9's feasibility gate
is a hard stop, and it failed, so no steering experiment was run on the moving
model.

What *is* established comes from Stage 6.8: **sparse boundary control does not
scale.** Stage 6 steered a 20-bird interior with a 12-bird boundary on a
100-bird lattice; Stage 6.8's blind detector proposes collectives of 95–145
birds, and there the `adaptive_oracle` arm — handed the true interface and the
exact influence matrix — reaches only 0.21–0.33 of the target across the whole
predeclared budget/horizon grid. The task, not the interface estimate, is the
binding constraint.

The arm ordering at matched budget, scored on the collective detected at the
control start, is: adaptive inferred causal (0.489) ≥ adaptive oracle (0.411) ≈
frozen causal (0.398) > matched-budget random (0.324) > predictive interface
(0.200) > no control (0.064). Causal interfaces beat random; the predictive
interface is **worse than random**; adaptive ≥ frozen is not resolved at n = 8
(SD ≈ 0.25) and is not claimed.

An off-specification guidance feasibility probe on the superseded `R = 1.6`
model found the same wall: oracle-arm path error 4.87, 4.94, 5.82, 5.82
interaction radii against a 3.0 R target, **worsening** with both more
actuators and a longer horizon. Recorded as a note, not a result.

### 10. Which parts of the framework look system-specific, and which generalize?

**Looks system-specific:**

- *the phase structure*. No mesoscopic regime exists on the fixed graph at any
  temperature or lattice size, and the reason — no self-coupling in `compute_G`
  — is a property of this particular generative model. Another flock family with
  heading inertia would behave differently.
- *the FOV rule doing the pinning*. Coexisting domains appear at L2 and not at
  L1 at identical parameters. The mechanism generalizes (receiver-state-dependent
  interaction), the specific 5-of-8 half-plane rule does not.
- *the control result*. 0.4–0.5 target fraction with 20 actuators on a 120-bird
  collective is a statement about this task at this scale.
- *the translating collective itself*. It exists only at ~3x the specified
  interaction degree. Whether a flock model with an explicit cohesion term
  would show it at Moore-scale connectivity is untested — adding one is what
  the brief forbids.
- *the absolute recall of finite probing* (0.602), which is a budget/density
  number: the moving flock's denser neighbourhoods make the same budget buy
  less.

**Appears to generalize:**

- **construction ≠ certification.** "No single node helps" is not a sufficiency
  proof, and a challenger class including a sparse multivariate model over all
  residual sources is a cheap, model-agnostic fix. Nothing about it is
  flock-specific.
- **identifiability ≠ estimation.** Reporting them separately changed the
  headline: Stage 6.7's perfect recovery survives as identifiability and
  collapses to 0.60 recall as estimation. Any interventional-discovery result
  reported with an exact propagator is vulnerable to the same conflation.
- **prediction ≠ causation for interfaces.** A predictively sufficient boundary
  can be a quarter the size of the causal one and worse than random to actuate.
  This held on a fixed graph (6.7), a state-dependent directed graph (6.8), and
  under hidden gating (L3).
- **detect before you infer.** Handing an algorithm the interior it is supposed
  to find hides whether the pipeline works at all; a task-neutral
  affinity-plus-community proposal recovered usable collectives on both a
  lattice and a torus without modification.
- **the three-way identity split, as an instrument.** Keeping material,
  lineage and functional-modulo-transformation separate is what let the Stage
  6.9 failure be *diagnosed* rather than merely observed: `R_M` falling while
  `R_F` fell with it identified "destroyed and replaced" as distinct from
  "transported". A single fused identity score would have shown a number
  getting worse and said nothing about why. (The stronger claim — that the
  split cleanly separates same-constituents from same-moving-organization — was
  seen only off-specification and is not claimed.)
- **conservative interventional estimators are the useful kind.** Precision
  1.000 with partial recall made the inferred interface a usable controller
  input; the high-recall/low-precision alternative would not have been.

---

## What neither stage established

- No claim of a universal definition of identity. The experiment establishes
  only that *this* decomposition separates same-constituents from
  same-moving-organization in *this* model.
- No claim that flock interaction graphs are observationally identifiable.
  Passive prediction recovered 24% of the interface at L2 and 14% under gating.
- No claim of absolute control success at Stage 6.8's scale — the task is
  infeasible there even with oracle knowledge, and only the arm ordering is
  interpreted.
- No claim that a collective preserves functional identity under translation
  in this model. At specification it does not; the supporting evidence came
  from a model that violated the specification.
- Small n throughout: 22 mesoscopic episodes from 600 screened seeds, 17
  snapshot candidates, 6 gated candidates, 2 interface time series, 8 control
  episodes, 40 moving episodes at specification (0 passing) and 40
  off-specification (16 passing).
- **One specification error, found late.** Stage 6.9's interaction radius was
  ~3x too large for eleven addenda' worth of work before it was caught, and it
  cost the stage its headline result. It was found by following an anomaly
  (a near-empty causal interface that the *exact* propagator reproduced) back
  to its cause, not by review of the parameter file.
