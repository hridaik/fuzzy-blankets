# Lineage Forensics — Stage 6.11, all five online seeds (Part D)

Additive, read-only. No repair, no lineage_v2, no change to any code or
reported RESULTS_6_11.md number. Every number below is either read directly
from the existing production artifacts (`data/online_control_611__seed*.json`,
`data/viz_bundle_611__seed*.json`) or produced by two new additive scripts
that replay the **real** `lineage_611.LineageTracker611` / `detect_69.propose`
/ `intervention_api_611` code from the already-recorded ground-truth
trajectory — never a reimplementation of the tracker's own decision logic.

**Replay fidelity, verified, not assumed.** `audit/lineage_forensics_611.py`
drives the real tracker from `viz_bundle_611__seed{n}.json`'s recorded
`(r, z)` per step and compares its own MAP interior against that same file's
independently-recorded `interior` field every step, for all 5 seeds: **0
mismatches, all 5 seeds, all steps** (`consistency_mismatches: 0` in
`audit/lineage_forensics_611__summary.json`). The replay is exact.

Per-seed machine-readable detail: `audit/lineage_forensics_611__seed{500..504}__hypotheses.csv` (one row/step), `audit/lineage_forensics_611__seed{500..504}__candidates.csv` (one row per (hypothesis, raw candidate) pair per step, gate-failures included), `audit/lineage_forensics_611__seed{500..504}__transitions.json` (flagged events), `audit/lineage_forensics_611__summary.json` (roll-up), `audit/causal_authority_forensics_611__item8_direct_vs_reachable.json`, `audit/causal_authority_forensics_611__item9_zero_authority.json`.

---

## 1. Unusual transitions, all five seeds (not only seed 500 t=20→21)

Flag rule (disclosed diagnostic, not a code threshold): winning-branch `R_retain_step < 0.40` (near the 0.30 hard gate), OR zero member overlap between consecutive MAP interiors, OR `D_deform > 0.30` (post-alignment deformation exceeding 30% of the unrelated-groups reference distance). Counts: **seed 500: 4, seed 501: 7, seed 502: 7, seed 503: 9, seed 504: 2** (`lineage_forensics_611__summary.json`). Full per-event detail (all fields the tracker computed for the winning branch, plus MAP margin and live-hypothesis count) is in each seed's `__transitions.json`.

### 1.1 Seed 500, t=20→21 — the flagged event, fully decomposed

This is **not** a case of a single bad candidate inheriting identity for lack of an alternative (the mechanism in §3 below). It is a **cross-branch MAP overtake**: the tracker held 5 simultaneously-live, genealogically-independent hypothesis threads going into t=21 (state after t=20's update):

| hid | prob (going into t=21) | size | thread identity |
|---|---|---|---|
| 3 | 0.472 | 38 | "big" thread (displayed as MAP at t=20) |
| 2 | 0.350 | 20 | "small" thread (runner-up at t=20) |
| 7 | 0.064 | 30 | third thread |
| 5 | 0.058 | 38 | **exact duplicate of hid 3** (same current members) |
| 6 | 0.056 | 22 | fourth thread |

At t=21, candidate detection found (among others) two size-17 candidates. Evaluating every live hypothesis against every t=21 candidate (full table in `seed500__candidates.csv`, filtered `t=21`):

- **hid 3** (the incumbent MAP thread) had **two** viable continuations this step: one scoring 0.692 (R_retain=0.58, R_F=0.63) and one scoring 0.552 (R_retain=0.42, R_F=0.51). Branching splits its 0.472 prior mass via the temperature-4 softmax of `[0.692, 0.552]` → weights `[0.637, 0.363]` → children get **0.301** and **0.171** (pre-renormalization).
- **hid 2** (the runner-up thread) had **one** viable continuation, scoring **0.876** (R_retain=0.85, R_purity=1.00, R_F=0.81 — the single best-matching continuation of *any* hypothesis this step). No branching competition → keeps its full prior mass: child gets **0.350**.
- hid 7 → one viable continuation (score 0.877) → child 0.064. hid 5 (duplicate of hid 3) → same two branches, children 0.037/0.021. hid 6 → one viable continuation (score 0.879) → child 0.056.

Pre-renormalization total ≈ 0.301+0.171+0.350+0.064+0.037+0.021+0.056 = 1.000 (no hypothesis fully dissolved this step); after `MAX_HYPOTHESES=6` pruning and renormalization, **hid 2's child (prob ≈0.357) exceeds hid 3's best child (prob ≈0.301/1.000≈0.30)** and becomes the new MAP — reported `map_prob=0.357, margin=0.050` (near-tied against the runner-up).

**Mechanism, stated precisely:** the previously-displayed interior (hid 3's thread) had a perfectly reasonable continuation available (R_retain=0.58 is well above the 0.30 gate, R_F=0.63 is a moderate-to-good match) — it was not orphaned. It lost the MAP race because **(a)** its own prior mass was structurally *diluted* by having two competing viable candidates this step (branching softmax splits probability that a non-branching hypothesis keeps whole), and **(b)** a fully independent, non-overlapping thread (hid 2, tracking a materially different ~20-22-member group since at least t≈19) happened to have a single, well-matched, undiluted continuation this same step. The two threads share **zero members** at the moment of the switch (`overlap_prev_map_new_map=0` in the transitions log), so the *displayed* "interior" jumps discontinuously even though the underlying belief state evolved by ordinary, locally-defensible arithmetic on each branch. **This is an argmax-instability defect in how `dominant_interior()` reads out a single pointer from a multi-branch belief state, not (in this instance) the "no death alternative forces a bad match" defect anticipated in `METHODS_AUDIT_6_11.md` §3** — that defect is real (§3 below shows it firing elsewhere) but is a different mechanism from what actually produced this specific, visually dramatic event.

## 2. Duplicate / near-duplicate lineage hypotheses

Exact-duplicate hypotheses (two or more live `hid`s sharing the *identical current member set*, as seen above with hid 3/hid 5) occur constantly:

| seed | steps with ≥1 exact-duplicate group | of n steps | near-duplicate pairs (different members, same size, field-distance < 0.05) |
|---|---|---|---|
| 500 | 92 | 108 (85%) | 0 |
| 501 | 74 | 77 (96%) | 0 |
| 502 | 51 | 77 (66%) | 0 |
| 503 | 75 | 82 (91%) | 0 |
| 504 | 0 | 94 (0%) | 0 |

(Near-duplicate-by-field-distance never triggered at the diagnostic 0.05 threshold — the duplication problem here is entirely the *exact* kind, i.e. the same physical candidate reached by more than one branch-history, not merely similar-looking distinct candidates.)

**Coalescing exact duplicates (merging probability mass of hypotheses with the same current member set, before taking argmax) materially changes both the reported uncertainty and, on a substantial minority of steps, the MAP choice itself:**

| seed | mean entropy (raw) | mean entropy (coalesced) | mean margin (raw) | mean margin (coalesced) | steps where coalesced MAP ≠ raw MAP |
|---|---|---|---|---|---|
| 500 | 0.921 | 0.591 | 0.455 | 0.580 | 1 / 108 |
| 501 | 1.633 | 0.949 | 0.064 | 0.332 | **15 / 77 (19%)** |
| 502 | 1.366 | 1.041 | 0.125 | 0.270 | **13 / 77 (17%)** |
| 503 | 1.619 | 1.270 | 0.100 | 0.196 | **16 / 82 (20%)** |
| 504 | 0.022 | 0.022 | 0.982 | 0.982 | 0 / 94 |

Entropy shrinks by 30–42% once duplicate branches are merged (the raw entropy overstates uncertainty — much of the apparent "spread" of belief across live hypotheses is the *same* candidate counted 2–3 times under different `hid`s, not genuinely distinct competing explanations), and — the more consequential finding — **on 17–20% of all steps for seeds 501–503, the member set that a naive coalesced-probability argmax would select is different from the member set `dominant_interior()` actually selects.** Note the asymmetry with §1: seed 500 (the clean flagship "jump," a genuine cross-branch overtake between two *distinct* threads) shows almost no MAP sensitivity to duplicate-coalescing (1/108), while seeds 501–503 (the three seeds RESULTS_6_11.md reports as control *successes*) show it constantly. This is a second, independent MAP-instability channel, present in the majority of steps of the "successful" episodes, not only in the dramatic failure case that prompted this audit.

## 3. The no-death-state defect: does it actually fire?

`METHODS_AUDIT_6_11.md` §3 established the code path exists (once ≥1 candidate clears `RETENTION_MIN=0.30`, a hypothesis must transfer some probability mass to it, however poor its match on every other axis). Scanning every step of every seed for a hypothesis with **exactly one** viable candidate whose match is nonetheless poor (`score < 0.40` or `R_F < 0.30`, i.e. worse alignment than a random same-size unrelated group would typically produce) — a forced, undiluted, low-quality inheritance:

| seed | n forced-poor-continuation events |
|---|---|
| 500 | 1 |
| 501 | 2 |
| 502 | 2 |
| 503 | 5 |
| 504 | 1 |
| **total** | **11** |

This defect is real and observed, not merely theoretical. The clearest instance: **seed 504, t=33**, where the tracker's hypothesis held **`prob=1.0`** (total, uncontested certainty — the only live hypothesis) and the sole candidate clearing the retention gate had `R_retain=1.00`, `R_purity=0.545` (only 55% of the new 33-member group is old material), `R_F=0.296` (a functional-similarity score *below* what an average random unrelated group typically scores against this thread's own normalizer) — and the tracker's output is unconditional confidence that this is "the same collective," with no signal anywhere in its state that the match was in fact poor on the one axis (`R_F`) designed to catch exactly this. Contrast with the diagnostic "none" alternative the tracker does not have: a version that could assign, say, `P(no valid continuation) = 1 − f(score)` for some monotonic `f`, leaving output uncertainty rather than false confidence, would flag this transition; the current code cannot.

## 4. Spatial integrity every step (not only during growth)

Computed via `thingness_611.geometry_features` on the MAP interior at **every** step (not only when growing), reusing the module the online loop itself never calls (§5):

| seed | max n_components (MAP) | fraction of steps with n_components > 1 |
|---|---|---|
| 500 | 24 | **100%** |
| 501 | 22 | 98.7% |
| 502 | 19 | **100%** |
| 503 | 21 | **100%** |
| 504 | 15 | 95.7% |

**The MAP-selected "interior" is spatially fragmented into more than one disconnected spatial piece at essentially every single step, in every one of the 5 episodes, including all 3 reported successes.** (The worked example in `METHODS_AUDIT_6_11.md` §4, n_components=11 at seed 500 t=61, is the typical case, not an outlier — seed 500's own maximum was 24 components.) `Q` (compactness) and `D` (exterior contrast) are computed alongside and available per-step in the hypotheses CSVs; `D` is at or near its 1.0 ceiling almost everywhere (the periphery is behaviourally distinct — not an individuation-blending failure), so fragmentation is a genuine spatial-shape property of the tracked object, not a symptom of losing definition against the background.

**Why does the tracker neither reject nor downweight this?** Because nothing in the decision path checks it (established from source, §5) — `n_components` is computed and logged by this audit's instrumentation, and by `thingness_611.geometry_features` when that module is invoked, but the online qualification/control loop never invokes `thingness_611` at all, and `LineageTracker611`'s own branch-scoring (`0.6·dice + 0.4·R_F`) contains no spatial-connectivity term either — the only place `n_components` enters the *real* tracker's logic is the narrow growth-classification check (`_grow_classification`, `lineage_611.py:121-134`), which looks at it **only when a candidate is both growing and already passed the 70% growth-retention floor**, to decide "individuation loss" vs. "bounded recruitment" — it is never consulted as a general plausibility check on any candidate, growing or not. A permanently-fragmented, 11-to-24-piece "collective" is therefore fully eligible to be the interior, to qualify for control, and to receive forced actuation, with nothing in the current pipeline ever noticing.

## 5. The online qualification trigger, exactly as coded (not inferred from the protocol)

From `run_online_control_611.py:184-199`, the **complete** condition for `phase = "control"`:

```
h = argmax_hyp tracker.hypotheses.prob
recs = h.records
if len(recs) >= 30:                                   # QUALIFY_MIN_DURATION
    recent = recs[-30:]
    size_ok = mean(0.05 <= size/N <= 0.50 for recent) >= 0.8    # QUALIFY_SIZE_RANGE
    disp = |sum(bulk_delta for recent)|
    if size_ok and disp >= 3.0 * R_PRIMARY:            # QUALIFY_MIN_DISPLACEMENT_R
        → qualify, set target
```

**Three conditions only: this hypothesis chain's own record length (persistence), its size staying in [5%,50%] of the population for ≥80% of the last 30 records, and cumulative net displacement over those 30 records ≥ 2.7 spatial units.** Confirmed by grep across the entire codebase (`code/*.py`): **`thingness_611` is imported and called nowhere outside its own unit tests** (`tests/test_lineage_and_thingness_611.py`, `tests/test_no_topology_leakage_611.py`). `passes_gate`, `ThingnessThresholds`, `geometry_features` never execute in any driver script (`run_online_control_611.py`, `run_predictive_boundary_611.py`, `export_viz_611.py`, `analyze_online_control_611.py`). **None of C, G, L, D, Q, single-component/clumpness, or lineage MAP probability/margin/entropy gate qualification.** The module exists, is unit-tested, is correctly implemented, and is presented in its own docstring as "the scientific object" gate — but it is dead code with respect to every reported Stage 6.11 online result. This is consistent with, and explains, §4's finding: nothing would have stopped a 24-component fragment from qualifying, because nothing checks component count (or coherence, or predictive/causal integration `G`/`L`, which additionally were never computed online at all — `B_pred` is cached as a member-ID set only, never converted into the `G`/`L` scalars `thingness_611.passes_gate` expects).

## 6. Same lineage vs. jumped-before-qualification, per control seed

For each seed: did the MAP-`hid` identity change (a cross-branch overtake, of the kind decomposed in §1.1) at any point between lineage birth and the moment the target was set?

| seed | qualified at t= | n MAP-hid switches before qualification | unusual-transition t's before qualification |
|---|---|---|---|
| 500 | 61 | **4** | 4, 21, 27, 39 |
| 501 | 30 | **5** | 2, 3, 11, 12, 17 |
| 502 | 30 | **4** | 2, 5, 20, 26 |
| 503 | 35 | **6** | 3, 7, 8, 9, 10, 11, 35 |
| 504 | 47 | **0** | (none caused a switch — only 1 live hypothesis existed throughout) |

**4 of 5 seeds (500, 501, 502, 503 — including all 3 reported control successes) had their target-setting "interior" arrive via multiple cross-branch MAP overtakes, not via one continuously-tracked organizational thread.** By the mechanism in §1.1, each individual overtake is locally explicable (branch dilution + an undiluted competing thread), but the practical consequence is the same regardless of mechanism: **the physical collective that is handed a translation target and then actuated is not necessarily the same physical collective whose spontaneous emergence originally satisfied the "qualifying episode" phenomenology described in PLAN.md §P** — it may be the 4th–6th distinct thread to hold the MAP slot by the time qualification fires. **Seed 504 is the sole exception**: a single, uncontested (`prob=1.0` throughout) hypothesis the entire episode — notably also the seed with zero exact-duplicate-hypothesis steps (§2) and the cleanest lineage bookkeeping of the five, despite also being one of the two seeds that failed to turn. Lineage cleanliness and control success are therefore not the same axis in this 5-episode sample: seed 504 has the cleanest lineage and fails; seeds 501–503 have messy, duplicate-laden, multiply-overtaken lineages and succeed; seed 500 has messy lineage tracking and fails. This sample is too small (n=5) to support a causal claim either way, and this audit does not make one.

## 7. Causal/control architecture, stated explicitly (not repaired)

Restating precisely, since the task brief asked this be in the final methods diagram: **`B̂causal` (probing_611, task-neutral one-step effect) is never consumed by `B̂C`/actuator selection.** `control_authority_611.select_actuators` (`code/control_authority_611.py:23-36`) takes `candidates` directly — in `run_online_control_611.py:238` that argument is `exterior_pool`, the *same* `near_exterior`-derived, oracle-radius-bounded pool passed to `probing_611.probe_sources` at line 230, **not** `B_causal_cache["B_causal"]`. The two interfaces are computed **independently, from the same privileged candidate pool**, and never cross-reference each other's output. `B_causal` is logged and reported (RESULTS_6_11.md §5, §6) but plays no functional role in which actuators get forced. This means: even if `B_causal` estimation were made fully blind (the §2 firewall repair), it would change nothing about which actuators are chosen unless `B̂C`'s own candidate pool were separately repaired and unless `select_actuators` were changed to filter or weight by `B_causal` membership — two structurally independent fixes, not one. Not implemented here.

```
                 exterior_pool = near_exterior(true R, radius_factor=3.0)   [ORACLE-DERIVED, shared]
                       │                                    │
                       ▼                                    ▼
        probing_611.probe_sources               control_authority_611.select_actuators
              → B̂causal (logged,                      → B̂C / actuators
                reported, NOT consumed                  (top-K individual τ=4
                downstream)                              authority, independent
                                                           of B̂causal)
```

## 8. Direct causal parenthood vs. τ-reachability of the actually-selected actuators

For every control/release-phase frame in all 5 seeds (235 frame-checks total), computed the true one-step causal boundary `B_t^{D,1} = oracle_B_D(interior_t)` (reference-only; never consumed by any decision) and checked whether each currently-forced actuator was a member:

| seed | actuator-slot-steps | direct causal parent at that instant | frames with ≥1 actuator that is a direct parent |
|---|---|---|---|
| 500 | 159 | **0 (0.0%)** | 0/47 |
| 501 | 184 | 5 (2.7%) | 3/47 |
| 502 | 148 | 1 (0.7%) | 1/47 |
| 503 | 184 | **0 (0.0%)** | 0/47 |
| 504 | 184 | 11 (6.0%) | 2/47 |

**Across all 5 seeds, 0.7–6.0% of actuator-slot-steps (17/859 total) correspond to a currently-forced bird that is a true one-step live-neighbour of the interior at that instant.** For the large majority of non-parent instances, forward-looking within the same episode to see whether that bird *later* becomes a direct parent while it is still being forced: seed 500 (5 of 154 later become parents), seed 501 (67 of 112 — the one seed where this happens often), seed 502 (1 of 146), seed 503 (**0 of 184 — never, in the entire episode**), seed 504 (1 of 172). **This holds for seeds 501–503 (the reported "successes") as much as for 500/504 (the reported "failures")** — actuated birds are, for almost the entire episode, in neither a current nor (mostly, except seed 501) a soon-to-be-realized one-step causal relationship with the interior they are meant to be steering. This is diagnostic only, per the task brief; it has not been fed back into any decision.

## 9. Zero/non-positive authority, across seeds, not only seed 500 t=61

Recomputed authority (same probe class, τ=4, 10 rollouts/candidate, same per-`(t,j)` seed convention as production) at each of the 3 real authority-refresh points per seed (`REINFER_AUTHORITY_EVERY=8` real steps into the 24-step control window: control_step 1/9/17 → real t = qualify_t, qualify_t+8, qualify_t+16):

| seed | refresh t | pool size | frac. candidates with A ≤ 0 | max A | all exactly 0.0 |
|---|---|---|---|---|---|
| 500 | 61 | 10 | **100%** | 0.0000 | yes |
| 500 | 69 | 10 | **100%** | 0.0000 | yes |
| 500 | 77 | 4 | **100%** | 0.0000 | yes |
| 501 | 30 | 36 | **100%** | 0.0000 | yes |
| 501 | 38 | 29 | 100% | 0.0000 | no (mean slightly negative — sampling noise) |
| 501 | 46 | 27 | **100%** | 0.0000 | yes |
| 502 | 30 | 18 | 88.9% | 0.0048 | no |
| 502 | 38 | 5 | **100%** | 0.0000 | yes |
| 502 | 46 | 28 | **100%** | 0.0000 | yes |
| 503 | 35 | 23 | **100%** | 0.0000 | yes |
| 503 | 43 | 47 | 83.0% | 0.0071 | no |
| 503 | 51 | 6 | **100%** | 0.0000 | yes |
| 504 | 47 | 22 | 59.1% | 0.0357 | no |
| 504 | 55 | 18 | **100%** | 0.0000 | yes |
| 504 | 63 | 15 | **100%** | 0.0000 | yes |

**At every one of the 15 refresh points, across all 5 seeds, 59–100% of candidates score non-positive authority, and 11 of 15 refreshes score EXACTLY zero for every single candidate in the pool** (bit-identical `H_do_mean == H_base_mean` for every candidate — a deterministic null, matching the mechanism identified in `METHODS_AUDIT_6_11.md` §4: an empty or near-empty true one-step causal boundary makes the τ-horizon effect genuinely, not just statistically, undetectable at the sampled budget). The handful of refreshes with nonzero signal (502@t=30, 503@t=43, 504@t=47, 501@t=38 negative-noise) show `max_A` values of 0.005–0.036 — a tiny fraction of the [0,1] range `H*` lives in, i.e. even the "positive" cases show barely-distinguishable-from-noise signal at this rollout budget. **The controller filled all K=8 actuator slots at every one of these 15 refreshes regardless** (`control_authority_611.select_actuators` has no abstain/minimum-authority threshold — confirmed from source, `code/control_authority_611.py:27-36`, plain top-K sort with no floor). This reproduces and generalizes the seed-500-t=61 worked example in `METHODS_AUDIT_6_11.md` §4 to all 5 seeds and all 15 refreshes: **it is not a seed-500-specific or staleness-specific phenomenon — it is the typical state of the authority signal actually driving actuator selection throughout this stage's reported result, including its 3 reported successes.**

**Open question this audit does not resolve, and flags for the controllability benchmark (Part J) rather than answering here:** if selected actuators are almost never true causal parents (§8) and their measured authority is almost always ≈0 (§9), what mechanism produced the reported turning in seeds 501–503? Candidates not adjudicated here: (a) real multi-hop/indirect effects over the held 8-step actuation windows that neither the one-step `B_D` nor the one-shot-then-released τ=4 authority estimator (intervention-duration mismatch, `METHODS_AUDIT_6_11.md` §1.5) are designed to detect; (b) the MAP-instability/duplicate-hypothesis effects documented in §§1–2 and 6 causing the *displayed, scored* interior to drift toward whichever sub-population happens to already be turning, independent of any forcing; (c) some combination. This audit only establishes that the causal/authority machinery, as measured with its own stated methodology, does not explain the outcome — it does not establish that the outcome is spurious, nor that it is real-but-unmeasured. That adjudication requires the (not yet run) controllability benchmark and confirmatory study.

## 10. Seed 500 t=61 in context

The worked example in `METHODS_AUDIT_6_11.md` §4 (empty `B_D`, all-zero authority, top-8 filled anyway) is confirmed by §9 above to be the **typical**, not exceptional, state of every refresh in every seed — restated here for completeness rather than re-derived.

---

## Recommendation: confirmed vs. possible

**Confirmed by this pass (C and D), with reproducible artifacts:**
1. Translation and permutation invariance of the relational predictor and Bpred construction — exact, floating-point tolerance.
2. Candidate detection is *not* exactly permutation-invariant (small, Louvain-traversal-order artifact, not a representational defect).
3. No component of the inference stack is rotation-invariant, narrowly or generally; the relational predictor's features are heading-identity-absolute by construction.
4. Frozen-model predictive quality degrades substantially (~55–63% logloss increase) at v=0.14 and v=0.42 relative to the trained v=0.28, with candidate-detection stability degrading asymmetrically (more at higher v), consistent with a real fixed-cadence contribution on top of representation shift.
5. **The existing online-buffer adaptation mechanism is net-harmful, not helpful, at every speed tested including the trained one** — not previously known, and directly relevant to any future repair of the online loop.
6. The seed-500 t=20→21 "identity jump" is real and is a genuine tracker defect, but its mechanism is **cross-branch MAP argmax instability** (dilution-by-branching + an undiluted competing thread), not the anticipated "no-death-state forces a bad match" mechanism — though that second, distinct defect is also confirmed to fire (11 times across the 5 seeds, most clearly at seed 504 t=33 with prior probability 1.0 inherited into an `R_F=0.30` match).
7. Duplicate live hypotheses (same current members, different `hid`) are pervasive (66–96% of steps in 4 of 5 seeds) and materially inflate reported lineage entropy and destabilize MAP choice (13–16 steps per seed, 17–20% of steps, where coalescing duplicates would flip the MAP pick) in exactly the three seeds RESULTS_6_11.md reports as successes.
8. The tracked interior is spatially fragmented (>1 disconnected component) at 96–100% of steps in every seed, and nothing in the online pipeline checks or downweights this — the thingness gate (`thingness_611.py`) is never invoked by any driver script; qualification uses only persistence + size-fraction + net displacement.
9. In 4 of 5 seeds, the interior handed a control target had already passed through 4–6 cross-branch MAP overtakes before qualification; only seed 504 tracked one continuous thread throughout.
10. `B̂causal` is computed, logged, and reported, but structurally never consumes into `B̂C`/actuator selection — the two are independent computations sharing only their (oracle-derived) candidate pool.
11. Selected/forced actuators are true one-step causal parents of the interior in only 0.7–6.0% of actuator-slot-steps across all 5 seeds, and authority estimates at the actual refresh points are non-positive for 59–100% of candidates (exactly zero at 11 of 15 refreshes) — in the reported successes as much as the reported failures.

**Possible, not established, and explicitly left open for Parts J/K:**
- Whether the mechanism behind seeds 501–503's reported turning is a real but unmeasured multi-step/indirect control effect, an artifact of interior-selection drift toward already-turning sub-populations, or some mixture — this audit shows the measured causal/authority justification does not explain the outcome, but does not show the outcome is spurious.
- Whether repairing the oracle-pool firewall violation (`METHODS_AUDIT_6_11.md` §2) or the intervention-duration mismatch (§1.5) would recover a genuine, detectable authority signal, or whether the true signal is simply weak/absent in this regime.
- Whether a lineage tracker with an explicit death/uncertain state and duplicate-hypothesis coalescing would have changed which seeds qualified for control, or only when.

No thresholds, code paths, or existing RESULTS_6_11.md numbers were changed in the production of this document.
