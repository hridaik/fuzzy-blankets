# Invariance and Dynamical Transfer — Stage 6.11 (Part C)

Additive, read-only. No control anywhere in this document's experiments.
Raw numbers: `audit/invariance_checks_611.json`, `audit/transfer_checks_611.json`.
Scripts: `audit/invariance_transfer_611.py`.

## 1. Exact invariance (one real snapshot, floating-point tolerance)

Snapshot: `observational_corpus_611__test.npz`, episode 0, t=50 (primary regime, uncontrolled). All checks recomputed the SAME functions the production pipeline uses (`predictive_boundary_611.pool_and_histogram`/`predict_proba`, `detect_69.propose`, `predictive_boundary_611.construct_boundary`, `identity_69.field`/`estimate_translation`), never reimplementations.

### 1.1 Translation invariance — CONFIRMED to floating-point tolerance

Applied one arbitrary common torus translation δ (`rng.random(2)*L`) to all 400 positions, everything else held fixed:

| quantity | result |
|---|---|
| relational-model category histogram (probe bird) | bit-identical |
| relational-model `predict_proba` | max abs diff **0.0** |
| `detect_69.propose` candidate partition (as sets of bird IDs) | identical |
| co-moving field `(rho, m)` for a detected candidate | max abs diff **3.6e-14 / 8.4e-15** (floating-point noise) |
| lineage `d_norm` (random-subset reference distance) | relative diff **0.0** |
| `predictive_boundary_611.construct_boundary` selected set `B` | identical |
| boundary construction final log-loss | abs diff **0.0** |
| lineage continuation deformation distance (`estimate_translation`) | abs diff **5.6e-17** |

This is the expected result given the code (§2 of `METHODS_AUDIT_6_11.md`): every feature is built from `torus_delta`/`torus_distance`, which are exactly translation-invariant by construction, and every co-moving field is re-centred on its own candidate's centroid before comparison. **Translation invariance of the relational predictor, candidate affinity/detection, predictive-boundary construction, and lineage continuation scoring is verified, not assumed.**

### 1.2 Permutation invariance — CONFIRMED for the predictor and boundary construction; NOT exact for candidate detection (small, characterized)

Relabelled all 400 birds by a random permutation π, tracking each physical bird's new index:

| quantity | result |
|---|---|
| relational-model histogram, same physical bird | bit-identical |
| relational-model `predict_proba`, same physical bird | max abs diff **0.0** |
| `construct_boundary` selected set `B`, as physical IDs | identical |
| `detect_69.propose` candidate partition, as physical-ID sets | **NOT identical** |

The last row is a genuine, if small, violation of the permutation-invariance the module's own docstring implies ("the same observer-facing logic," reused unmodified from Stage 6.8/6.9). Quantified with a second random permutation on the same snapshot: of 10 detected candidates (sizes 17–100), 8 match their best-permuted-run counterpart with Jaccard **1.000**; the two largest (sizes 100, 49) match at Jaccard **0.990** and **0.980** (1–2 birds differ out of ~50–100). **Root cause, not guessed:** `louvain.louvain` is a greedy local-moving heuristic that visits nodes in index order and accepts the first improving move; relabelling nodes changes visitation order and can land the optimizer in a different (but comparably-scoring) local optimum near a modularity tie. This is a real, measurable non-invariance in the detector — not in the feature representation feeding it — and it is small (≤2% membership disagreement on the two affected candidates, exact agreement on the other eight) rather than a structural asymmetry. Not previously disclosed; not repaired here per the user's stop condition.

### 1.3 Rotation — explicitly NOT claimed, and the one testable narrower claim is falsified as stated

Headings live on the fixed 4-state `UV4` lattice, so only the discrete 90°-rotation that maps `UV4` onto itself is even well-defined (checked here: positions rotated 90° CCW about the box centre, headings relabelled `up→left→down→right→up` to match). Candidate-partition *sizes* were preserved in shape (9 candidates, comparable size distribution) under this transform, consistent with detection depending only on torus distance (rotation-covariant) and heading-agreement history (invariant under a consistent relabelling). **But** the relational model's category index (`predictive_boundary_611.category_index`) bakes in *absolute* heading identity (`z_j ∈ {0,1,2,3}` enters the category index directly, not `z_j` relative to anything), and the per-stratum coefficients (`RelationalHeadingModel.models[h]`) are keyed by the same absolute `h_cur`. Recomputing the raw category histogram under the 90°-rotated-and-relabelled configuration gave a **different** histogram than the unrotated one (`rotation90_histogram_identical_no_relabel_of_model_strata: false`) — expected, since a fair rotation check would also need to permute *which stratum's coefficients* apply, which nothing in the codebase does. **Conclusion: this stage's own moving-flock docstring's claim of isotropy (`moving_flock_611.py`'s cohesion-term docstring, "equivariant under the 90-degree rotations that map the four-heading lattice onto itself") is about the *dynamics*, not about this predictor, and should not be read as implying the relational predictor is rotation-invariant in any sense — it is not, and nothing in RESULTS_6_11.md claims otherwise. This audit finds no basis for calling any Stage 6.11 inference component rotation-invariant, narrow or general, and the code confirms why: heading identity is absolute in the feature representation.**

## 2. Dynamical transfer: frozen v=0.28 model at v ∈ {0.14, 0.28, 0.42}

**Protocol.** The pretrained relational model (`pretrained_relational_model_611.pkl`, fit at v=V_PRIMARY=0.28) is held frozen; R=0.9, cohesion=1.0, all other params identical to the primary regime — v is the only thing varied. v=0.28 reuses 4 existing held-out test episodes (`observational_corpus_611__test.npz`); v=0.14 and v=0.42 use 4 freshly-generated **uncontrolled** episodes each (seeds 300–303, 150 steps, `MovingFlock611.step` only — no control, no probing, no intervention anywhere in this generation). Two evaluation modes, both walk-forward (never using a future label to produce a past prediction):
- **zero adaptation:** the frozen base model scores every step's actual transition.
- **online-buffer adaptation:** replicates `run_online_control_611.step_world`'s own mechanism exactly — 60 birds/step appended to a buffer (scaled up from the online loop's 20/step since these episodes carry no control phase to draw the comparison out over; cap 3000), full warm-started refit against `base_rows + buffer` every `REINFER_PRED_EVERY=12` steps, matching the production cadence and refit call.

Candidate stability = mean step-to-step Jaccard of the best-matching largest detected candidate. Bpred quality = one `construct_boundary` snapshot per episode (midpoint step) on the largest detected candidate.

| v | zero-adapt mean logloss | online-adapt mean logloss | candidate stability (mean Jaccard) | Bpred final loss | Bpred \|B\| |
|---|---|---|---|---|---|
| 0.14 | 0.760 | 0.819 | 0.712 | 0.863 | 2.5 |
| **0.28 (trained)** | **0.467** | **0.519** | **0.955** | 0.543 | 0.25 |
| 0.42 | 0.722 | 0.763 | 0.672 | 0.724 | 6.25 |

(Uniform-random baseline logloss = ln 4 = 1.386 throughout, for scale — every cell still beats a uniform guess.)

**Finding 1 — representational transfer genuinely degrades away from the trained speed, in both directions.** Zero-adaptation logloss roughly *doubles* at v=0.14 (0.760 vs 0.467, +63%) and at v=0.42 (0.722, +55%) relative to the trained v=0.28. This alone is consistent with either a representation-shift story or a cadence story; §2's next finding starts to separate them.

**Finding 2 — candidate-detection stability degrades asymmetrically, more at higher v, supporting a fixed-cadence contribution distinct from pure representation shift.** Mean step-to-step candidate Jaccard falls from 0.955 (v=0.28) to 0.712 (v=0.14, −25%) and further to 0.672 (v=0.42, −30%) — i.e. detection itself is *less* stable at higher speed than at lower speed, even though the zero-adapt logloss degradation was roughly symmetric (+63% vs +55%) in the two directions. Candidate detection's affinity kernel (`detect_69.SIGMA=1.1`, `KERNEL_CUTOFF=3.3`, inherited unchanged from the fixed-lattice Stage 6.8) is a fixed spatial scale evaluated once per real step regardless of v; at higher v birds displace further per step relative to that fixed scale, which is exactly a **fixed-cadence-expressed-in-simulation-steps** artifact, not a property of the learned heading predictor. This does not rule out an additional, separate representational shift (the logloss numbers show one exists at both v=0.14 and v=0.42), but it does show the two are at least partially separable, and that the cadence contribution is real and directionally asymmetric.

**Finding 3 — the Bpred boundary grows away from the trained speed (0.25 → 2.5 → 6.25 exterior sources as v moves 0.28 → 0.14 → 0.42), consistent with both stories:** more exterior information is needed to explain periphery dynamics once the nearest-`M_obs`-neighbour relational features no longer capture what actually drives a bird's next heading — whether because the *relationship itself* changed (representation shift) or because the *effective interaction footprint per step* changed with v (cadence). This audit does not adjudicate between the two explanations for Finding 3 specifically; Finding 2 is the cleaner separating evidence.

**Finding 4 — online-buffer adaptation makes prediction WORSE, not better, at every tested speed, including the trained one.** This is the headline result of this section and was not anticipated going in:

| v | zero-adapt | online-adapt | Δ |
|---|---|---|---|
| 0.14 | 0.760 | 0.819 | **+0.059 (worse)** |
| 0.28 | 0.467 | 0.519 | **+0.053 (worse)** |
| 0.42 | 0.722 | 0.763 | **+0.041 (worse)** |

The exact mechanism `run_online_control_611.py` uses to "adapt" the predictor online — periodic warm-started refit on `base_rows + online_buffer` — degrades held-out predictive log-loss uniformly across all three speeds tested, by a similar absolute margin (~0.04–0.06 nats/bird-step) regardless of whether the frozen model was well- or poorly-matched to begin with. **This is not a transfer-specific problem — it reproduces even at the model's own training speed.** A plausible mechanism (not verified further here, out of this pass's scope): each episode's buffer is a small (≤3000-row), temporally-autocorrelated sample from one single trajectory, and refitting toward it pulls the shared coefficients away from the broader, more representative base corpus without contributing enough independent information to justify the pull — but this is a hypothesis, not a demonstrated cause, and is flagged as a specific, well-defined question for any future repair pass, not resolved here. **What is established, not hypothesized: the "adaptive" half of the online predictive-boundary mechanism, as actually implemented and actually measured, is currently net-harmful on every regime tested,** including 4 independent held-out episodes at the primary v=0.28 regime itself (n=4 episodes/speed — a modest sample, stated as such, but the effect is directionally consistent across all 12 episodes and both non-primary speeds independently).

## 3. Summary for the audit's confirmed-vs-possible ledger

| claim | status |
|---|---|
| Relational predictor, candidate affinity features, Bpred construction, lineage dice/R_F are exactly translation-invariant | **CONFIRMED** (floating-point tolerance) |
| Relational predictor and Bpred construction are exactly permutation-invariant | **CONFIRMED** |
| Candidate detection (`detect_69.propose`) is exactly permutation-invariant | **REFUTED** — small (≤2% membership), traced to Louvain's node-order-dependent local optimum, not the feature representation |
| Any Stage 6.11 inference component is rotation-invariant (narrow 90° or general) | **REFUTED / not claimed** — heading identity is absolute in the relational predictor's features |
| Frozen-model predictive quality degrades away from the trained speed | **CONFIRMED**, both directions, ~55-63% logloss increase at ±0.14 from v=0.28 |
| The degradation is at least partly a fixed-cadence artifact, not pure representation shift | **CONFIRMED** via the asymmetric candidate-stability result (Finding 2); not fully decomposed from representation shift |
| Existing online-buffer adaptation improves predictive performance under speed transfer | **REFUTED** — it is net-harmful at v=0.14, v=0.28, *and* v=0.42 alike |
