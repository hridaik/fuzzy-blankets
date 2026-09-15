# Methods Audit — Stage 6.11 (Part A/B)

Source-level audit only. No thresholds, code, or reported numbers changed.
Every claim below cites `file:line` in the Stage 6.11 / inherited 6.8–6.9
code as it exists on `main` at audit time. Where a claim required a live
number rather than a static reading, it was produced by
`audit/worked_example_611.py`, an **additive, read-only replay** of
`run_online_control_611.run_episode` (same functions, same RNG draw order,
same seed) that stops at the exact step already reported in
`data/online_control_611__seed500.json`'s first `control_step` log entry
and records everything the production loop computes but does not persist.
Its output (`audit/worked_example_seed500_t61.json`) was checked
field-for-field against the production log for that step (`B_C`, `B_causal`,
`B_pred`, `frac_interior_at_target`) and matches exactly — the replay is
faithful, not a reconstruction.

---

## 1. The two pipelines, stage by stage

### Pipeline 1: `Y_{0:t} → C_t → q_t(I)/Î_t → B̂pred_t`

#### 1.1 Candidate detection: `C_t`

- **Code:** `detect_69.propose` (`stage6_9_translating_collective/code/detect_69.py:52-61`), called every step from `run_online_control_611.run_episode` at `run_online_control_611.py:167`.
- **Input:** current positions `r` (N×2), a rolling window of up to `AFFINITY_WINDOW=6` past heading arrays `z_window` (`run_online_control_611.py:61,164-166`). Both observer-visible.
- **Equation:**
  `D_ij` = torus distance (`detect_69.py:35-38`);
  `K_ij = exp(-D_ij²/2σ²)·1[D_ij≤cutoff]`, σ=1.1, cutoff=3.3 (`detect_69.py:27-28,41-44`);
  `agree_ij = (1/|window|)·Σ_τ 1[z_i(τ)=z_j(τ)]` (`detect_69.py:46-48`);
  `W_ij = K_ij · agree_ij` (`detect_69.py:49`).
  Communities = deterministic weighted Louvain on `W` (`louvain.louvain`, Stage 6.8 module, reused read-only).
- **Output:** a list of member-index arrays, filtered to `0.03N ≤ |c| ≤ 0.55N` (`detect_69.py:29-30,57-58`), sorted largest-first. At the worked-example step (seed 500, t=61) this returns **13 candidates**, sizes `[39,38,36,36,33,32,30,28,27,25,19,19,12]`.
- **Thresholds:** σ=1.1, cutoff=3.3σ-equivalent (3.3 absolute units), size window [0.03,0.55]·N — all fixed constants in `detect_69.py`, not fit or tuned per episode.
- **Nature:** deterministic calculation given `(r, z_window)`; not fitted, not incrementally updated. Recomputed from scratch every single step (full Louvain re-run), not carried forward.
- **Observer-visible:** yes, entirely — positions and a bounded heading history only.

#### 1.2 Lineage tracking: `q_t(I) → Î_t`

- **Code:** `lineage_611.LineageTracker611` (`code/lineage_611.py:81-217`), driven from `run_online_control_611.py:169-176`.
- **Input:** the full candidate list `C_t` from 1.1, current `(r, z, t)`.
- **State:** a list of `Hypothesis` objects, each carrying a normalized `prob` (Σ over live hypotheses of one lineage tree = 1, `lineage_611.py:194-200`), a co-moving field `(rho, m)`, a `centre`, and an `origin` (the material set at the lineage's t=0 root).
- **Per-step update (`lineage_611.py:136-201`):**
  1. For each live hypothesis `h` and each candidate `cand` in `C_t`: compute `R_retain = |prev∩cand|/|prev|`, `R_purity = |prev∩cand|/|cand|` (`lineage_611.py:56-60`). `cand` is **viable** only if `R_retain ≥ RETENTION_MIN = 0.30` (`lineage_611.py:39,147`).
  2. If **no** candidate is viable: `h.status = "dissolved"`, hypothesis removed from the live set (`lineage_611.py:153-159`). This is the tracker's only death path — see §3 below for why it does not fire on every implausible match.
  3. For each viable candidate: estimate bulk translation `tr` via `identity_69.estimate_translation` (grid cross-correlation after centroid alignment, `identity_69.py:80-97`); `R_F = similarity(tr["distance"], h.d_norm)` (`identity_69.py:100-102`, `d_norm` = field-distance to an independent random same-size subset drawn once at `start()`, `lineage_611.py:107-110` — the "how far apart are two unrelated groups this size" normalizer).
  4. `score = 0.6·dice(prev,cand) + 0.4·R_F` (`lineage_611.py:151`).
  5. Softmax over viable candidates' scores, temperature 4.0: `branch_probs = softmax(4.0·(score - max score))` (`lineage_611.py:161-163,45`). **This is the entire "probability distribution over lineage continuation": a softmax over the current step's candidate scores, re-normalized among only the viable set.** It is not a recursive Bayesian filter in the sense of combining a transition-model prior with a likelihood — the previous hypothesis's `prob` enters only as a multiplicative prefactor (`new_prob = h.prob · branch_prob`, `lineage_611.py:167`), i.e. hypothesis-tree mass is propagated but **the per-step choice among viable candidates within one hypothesis's fan-out uses no memory of anything before the immediately preceding step** other than `prev.members`, `h.contrast_history` (last 5 steps) and `h.d_norm` (fixed at `start()`).
  6. Growth classification (`_grow_classification`, `lineage_611.py:121-134`): if `cand` is larger than `prev` **and** `R_retain ≥ GROWTH_RETENTION_MIN=0.70`, check whether local exterior contrast `D` has fallen below `0.5×` its 5-step trailing mean, or whether the candidate has split into >1 spatial component; if so, status becomes `"individuation_loss"` rather than crediting growth. Three consecutive individuation-loss steps → forced dissolution (`DISSOLVE_AFTER_INDIVIDUATION_STEPS=3`, `lineage_611.py:43,188-190`).
  7. Surviving hypotheses are re-normalized (`Σprob=1`) and pruned to the top `MAX_HYPOTHESES=6` by probability (`lineage_611.py:194-200`).
- **`Î_t`:** `run_online_control_611.dominant_interior` (`run_online_control_611.py:104-107`) simply takes `argmax_h h.prob` — the MAP hypothesis's member set. No entropy, margin, or confidence check gates whether this MAP pick is actually used; it is used even when the tracker holds 5 nearly-tied hypotheses (see worked example, §4).
- **New lineages:** if the tracker fully dissolves and `C_t` is non-empty, a brand-new `LineageTracker611` is started from `C_t[0]` (the single largest current candidate) — `run_online_control_611.py:174-176`. This is a genuine "no valid continuation → new birth" path, but it only fires after 100% of mass has already been assigned away from the old lineage tree (step 2/6 above); a candidate that clears `RETENTION_MIN` but is a poor match on every other axis is never routed here — see §3.
- **Merge/split:** not modeled as first-class events. A single detected community's Louvain relabeling naturally produces multiple simultaneously-viable candidates against one hypothesis (handled by the branch-softmax, step 5), and `detect_69.TranslatingTracker.update` (a *different*, unused-here Stage 6.9 tracker) records `branch_events` when two candidates each carry Jaccard ≥0.25 (`detect_69.py:143-146`) — but `LineageTracker611` itself has no analogous merge/split log; multiple viable candidates per hypothesis are simply treated as `MAX_HYPOTHESES`-capped branching.
- **Fitted/estimated/carried-forward:** nothing here is fitted from a training corpus. Everything is recomputed from the current + immediately preceding detector output every step. `h.d_norm` is estimated **once**, at hypothesis birth, and carried forward unchanged for that hypothesis's entire life.
- **Observer-visible:** yes. No simulator object enters (`geometry_611.py:1-11`'s own docstring, `lineage_611.py:1-29`'s docstring, and the firewall test below).

#### 1.3 Predictive boundary: `B̂pred_t`

- **Code:** `predictive_boundary_611.py`, driven from `run_online_control_611.py:203-224`.
- **Base model (fit offline, loaded via `load_pretrained_model`, `run_online_control_611.py:81-101`):** `RelationalHeadingModel`, one multinomial-logistic-regression model per current-heading stratum `h_cur ∈{0,1,2,3}` (`predictive_boundary_611.py:121-149`). Feature = a 96-dim histogram (`N_CATEGORIES = 4 headings × 3 dist bins × 8 bearing octants`, `predictive_boundary_611.py:34-37`) over the nearest `M_obs=12` other birds (`M_OBS_GRID=(12,20)`, `run_online_control_611.py:81` uses 12 online). Score `s_h(i,t) = b_h + hist·coef_h` (`predictive_boundary_611.py:157-167`); softmax over the 4 next-heading classes. **Never uses the true interaction radius** — distance-bin cut points are quantiles of the training split's own nearest-`M_obs` distance distribution (`estimate_distance_cuts`, `predictive_boundary_611.py:54-66`).
- **Base-model training data:** `observational_corpus_611.py`, primary regime, 36 train / 12 val / 12 test episodes of 180 steps each (RESULTS_6_11.md §3), 400 birds/episode; base fit uses a uniform per-episode subsample of ≤1500 (bird,t) rows/episode (`build_rows`, `predictive_boundary_611.py:97-110`).
- **Online refresh:** `model.refit_with_buffer(base_rows, online_buffer[-4000:])` — a **full batch refit** (warm-started `LogisticRegression`, `predictive_boundary_611.py:144-148`) on `base_rows` concatenated with the current episode's own online buffer, called only when `control_step % (REINFER_PRED_EVERY*3) == 0` i.e. every 36 real steps (`run_online_control_611.py:219-220`). This is **not** a Bayesian/sequential posterior update — it is a from-scratch re-solve of the logistic regression on the enlarged row set each time; "sequential MAP" in the module docstring (`predictive_boundary_611.py:151-154`) refers to the training set growing, not to the optimizer's internal state.
- **Online buffer contents:** every real step, `step_world` draws 20 of the 400 birds uniformly (`rng.choice(mf.N, size=min(20,mf.N), replace=False)`, `run_online_control_611.py:140`) and appends their **actual observed** `(hist_t, label=z_{t+1})` row, capped at `ONLINE_BUFFER_CAP=3000` rows (FIFO, `run_online_control_611.py:145-146`). See Part M for whether these rows include controlled transitions.
- **Boundary construction per candidate interior (`PB.construct_boundary`, `predictive_boundary_611.py:285-336`):** greedy conditional forward selection. Starts from the interior-only conditioning set (every exterior-sourced category count in each periphery row's histogram zeroed, `predictive_boundary_611.py:301-305`); at each step adds the single exterior source bird whose reinclusion most reduces mean log-loss on the row set (`predictive_boundary_611.py:314-331`); stops when no candidate improves loss by ≥`MIN_GAIN=0.002`, or `(current_loss - full_pool_loss) ≤ DELTA_TOL=0.01` nats, or `K_MAX=12` sources added (`predictive_boundary_611.py:40-44`). **Search complexity:** O(K_max · |candidate exterior sources|) vectorized log-loss evaluations, each O(rows); no backtracking, purely greedy — this is the "exact actuator-set search algorithm" for `B̂pred` specifically (§13 below covers `B̂C`'s separate, simpler top-K rule).
- **Row construction, online:** `interior_periphery_targets` restricts to interior members within `periphery_radius = local_scale(r,L)` (2.5× median observed nearest-neighbour spacing, `geometry_611.py:21,42-45`) of some non-member (`predictive_boundary_611.py:219-234`), using the rolling `SNAP_WINDOW=20`-step trajectory of real `(r,z)` snapshots plus the current step, i.e. genuine observed `(t→t+1)` labels, not synthetic ones (`run_online_control_611.py:212-216`).
- **Refresh cadence:** `REINFER_PRED_EVERY=12` real steps (`run_online_control_611.py:65,203`); stale `B_pred_cache` is reused and its age (`age_pred`) logged in between.
- **Certification (offline only, `PB.certify`, `predictive_boundary_611.py:339-397`):** single-challenger bootstrap over held-out test episodes; not re-run online.
- **Observer-visible:** yes throughout.

### Pipeline 2: `Î_t → B̂causal_t → Â_t → BC_t/St → u_t → Y_{t+1}`

#### 1.4 Causal probing: `B̂causal_t`

- **Simulator-side probe object:** `intervention_api_611.FiniteProbeMoving611` (`code/intervention_api_611.py:27-94`). One object per fixed position snapshot (`mf.position_cache(r_t)`). `.probe_rollout_indicators(I, j, z', z_t)` runs `n_rollouts` **paired common-random-number** one-step rollouts: for each rollout `k`, `seed_k=(self.seed, j, z', k)` seeds **both** the factual arm (`z_t` unmodified) and the counterfactual arm (`z_t[j]:=z'`), via two freshly-constructed `np.random.default_rng(seed_k)` generators so the two arms consume identical randomness (`intervention_api_611.py:80-89`). The intervention is on bird `j`'s **current state** `z_t[j]`, fed into that step's `G_i` computation for `j`'s neighbours, not on `j`'s drawn action (§1.4 note below explains why the earlier action-forcing version was a no-op and was fixed; RESULTS_6_11.md §5).
- **Inference-side decision rule:** `probing_611.probe_sources` (`code/probing_611.py:66-75`), consuming only the numeric `.probe_rollout_indicators` output (never `MovingFlock611` itself, `probing_611.py:1-18`). For source `j`: pool the per-rollout binary disagreement indicators across the `NU-1=3` alternative headings and all repeat probe objects (`probing_611.py:36-44`); `C^do_j = Σ_i mean(indicator_i)`; nonparametric bootstrap (vectorized, `n_boot=100` online / `N_BOOT_CI=500` default) over the pooled per-rollout indicators gives a 95% CI (`probing_611.py:53-60`); `j ∈ B̂causal` iff `ci_lo(C^do_j) > τ=0.0` (`probing_611.py:26,73`).
- **Rollout budget, online:** `PROBE_ROLLOUTS_ONLINE=20`, `PROBE_REPEATS_ONLINE=2` (`run_online_control_611.py:70-71,228-230`) — reduced from the Stage 6.10 reference `PROBE_ROLLOUTS=40, PROBE_REPEATS=3` (`intervention_api_611.py:22-23`), with the full-budget check run separately offline (`run_causal_budget_sensitivity_611.py`).
- **Intervention duration:** exactly **one** simulator step (`step_cached` called once per rollout, `intervention_api_611.py:64,66`) — genuinely one-step/task-neutral, matching the module's own framing.
- **Refresh cadence:** `REINFER_CAUSAL_EVERY=8` real steps (`run_online_control_611.py:66,204`).
- **Candidate pool — see §2, this is the firewall finding.**

#### 1.5 Authority: `Â_t`

- **Simulator-side probe:** `intervention_api_611.MultiStepAuthorityProbe` (`code/intervention_api_611.py:97-149`). `.authority(I, j, h_star)` runs `n_rollouts` paired CRN rollouts, **each of length `tau`**, via `_rollout(forced, seed)` (`intervention_api_611.py:121-127`):
  ```
  for step in range(tau):
      fa = forced if step == 0 else None
      r, z, _ = mf.step(r, z, rng, forced_actions=fa)
  ```
  **The forced action is applied only at `step==0` of the `tau`-length imagined rollout; steps 1..tau-1 evolve freely with no held intervention.** `H*(z)=fraction of I at h_star`; `A_j = E[H*_{t+τ}|do] - E[H*_{t+τ}|baseline]` (`intervention_api_611.py:129-146`).
- **Inference-side decision rule:** `control_authority_611.select_actuators` (`code/control_authority_611.py:23-36`): `rank_actuators` calls `probe.authority(...)` once per candidate `j` **independently** (no conditioning on other candidates' selection), sorts descending by `A`, and takes the top `k_act`. **This is plain top-K individual authority ranking — not greedy marginal-set search, not multicover, not beam search**; nothing in this module or its caller re-scores a candidate conditional on the actuators already chosen.
- **Rollout budget, online:** `AUTHORITY_ROLLOUTS_ONLINE=10` per candidate `j`, `tau=TAU_CONTROL=4` (`run_online_control_611.py:69,72,236-239`).
- **Refresh cadence:** `REINFER_AUTHORITY_EVERY=8` real steps (`run_online_control_611.py:67,205`).
- **Search complexity:** O(|exterior_pool| · n_rollouts · τ) simulator steps per refresh; the "search" itself (top-K sort) is O(|pool| log |pool|).
- ⚠️ **Intervention-duration mismatch (new finding, not previously documented in RESULTS_6_11.md).** The authority estimate that selects actuators assumes a **one-shot** forced action at the start of a `τ=4`-step imagined horizon, released thereafter. The real controller instead **holds** the same forced heading on the same actuator set for every real step of a refresh interval — every iteration of the `while` loop while `phase=="control"` recomputes `forced = {j: target_heading for j in B_C_cache["B_C"]}` (`run_online_control_611.py:243`) and applies it via `step_world(forced)` (`run_online_control_611.py:276`), and `B_C_cache` itself only changes every `REINFER_AUTHORITY_EVERY=8` steps — so in practice each selected actuator is forced to `target_heading` continuously for up to 8 consecutive real steps, not once. The one-shot-then-released `A_j` used to rank and select those actuators is therefore not actually estimating the effect of the intervention the controller performs. This is a genuine estimand/execution mismatch, distinct from the already-disclosed one-step-action-forcing bug (RESULTS_6_11.md §5); see `audit/CAUSAL_AUTHORITY_AUDIT_6_11.md` (Part G/H) for quantification.

#### 1.6 Actuation: `u_t`, `Y_{t+1}`

- `forced = {j: target_heading for j in B_C_cache["B_C"]}` (`run_online_control_611.py:243`); `mf.step(r, z, rng, forced_actions=forced)` (`moving_flock_611.py` inherited `step`, forces `applied[j]=target_heading` before drawing `z_new` — see `moving_flock_611.py:196-201`'s `step_cached` for the identical logic `step` shares). This is a genuine action-level force on the actuator's own next heading (not a state override) — appropriate here since the actuator itself is meant to *act* that way, in contrast to the causal-probe's state intervention on non-actuator sources (§1.4).
- `target_heading` is fixed once at qualification (`run_online_control_611.py:195`, `ROT_CCW[bearing_to_cardinal(bulk_delta)]`) and never re-derived during control — it is **not** the "adjacent 90° of the *current* bulk direction re-estimated every step," it is the 90°-CCW-of-the-direction-observed-at-qualification, held fixed for the whole 24-step control window.

---

## 2. Firewall audit by data flow (Part B)

**Finding: the primary online causal-probe and authority candidate pools are NOT blind — they are constructed using the true interaction radius R.**

- `run_online_control_611.py:226`: `exterior_pool = near_exterior(mf, r, interior, radius_factor=3.0)`.
- `near_exterior` (`intervention_api_611.py:152-168`) computes `near = (D ≤ radius_factor * mf.R).any(axis=0)` — **`mf.R` is the simulator's true interaction radius**, not an observed quantity. The function's own docstring (`intervention_api_611.py:156-159`) calls this an "ORACLE (uses the true R)" and asserts it "only bounds which exterior birds are worth spending probe budget on... never exposed to the predictive/lineage/thingness inference code." That second claim is true for `B̂pred` (§1.3, which uses only `M_obs`-nearest-neighbour pools with quantile distance bins, never `R`) but **is false in effect for `B̂causal` and `B̂C`**: `exterior_pool` is passed directly into `PR.probe_sources(probes, interior, exterior_pool, ...)` (`run_online_control_611.py:230`) and `CA.select_actuators(auth_probe, interior, exterior_pool, ...)` (`run_online_control_611.py:238`) — i.e. **the candidate set that can ever become `B̂causal` or an actuator is selected using privileged physics**, every control step, in the actual reported result.
- **Why this passes the existing 66 tests.** `tests/test_no_topology_leakage_611.py` AST-scans a fixed `INFERENCE_SIDE` module list (`geometry_611.py`, `lineage_611.py`, `thingness_611.py`, `predictive_boundary_611.py`, `probing_611.py`, `control_authority_611.py`, plus reused 6.8/6.9 modules — `test_no_topology_leakage_611.py:35-46`) for forbidden imports/identifiers/parameter names, and separately runs a synthetic-data "runtime seal" that checks no *simulator object type* leaks into blind-pipeline outputs (`test_no_topology_leakage_611.py:131-183`). `intervention_api_611.py` is **not** in `INFERENCE_SIDE` (it is evaluation-side by design, and correctly so — it legitimately touches `mf.R`) and `near_exterior`'s return value is a plain `list[int]`. No forbidden identifier, no forbidden import, no simulator object crosses into `probing_611.py` or `control_authority_611.py` — **those modules genuinely only ever see integers**. The tests check *object provenance and syntactic imports*, not *information content of a value computed elsewhere from privileged data and handed across the boundary as plain ints*. This is exactly the distinction the audit brief anticipated ("audit by data flow, not just AST names") and it is real: the tests are correct about what they check, and what they check is insufficient to catch this.
- **Is `near_exterior` "only an evaluation diagnostic"?** No — for the 28-bird-within-1.5R mention in RESULTS_6_11.md §5, yes: that number comes from `run_causal_budget_sensitivity_611.py:36` (`near_exterior(..., radius_factor=1.5)`), a **standalone offline diagnostic script**, never called from `run_online_control_611.py`. But the *function* `near_exterior` is also called, with a different `radius_factor=3.0`, from inside the **primary online loop itself** (`run_online_control_611.py:226`) to build the pool actually used for `B̂causal`/`B̂C` in every one of the 5 reported episodes. So: the specific "1.5R, 28 birds" number is diagnostic-only, but the underlying oracle-radius pool-construction mechanism is load-bearing in the primary reported result, not merely diagnostic.
- **Pool-size chain at the worked-example step (seed 500, t=61, verified in `audit/worked_example_seed500_t61.json`):**

  | stage | N |
  |---|---|
  | N exterior (all non-interior birds) | 367 |
  | N candidate exterior pool (`near_exterior`, 3R, oracle) | **10** |
  | N causal-probe pool (= same 10, `probing_611` receives the whole pool as sources) | 10 |
  | N authority pool (= same 10) | 10 |
  | K actuators selected | 8 |
  | **N true causal parents (`oracle_B_D`) in the 10-bird pool** | **0** |
  | **N true causal parents total, this interior, this step** | **0** |

  At this snapshot the true one-step live-neighbour boundary of the 33-bird interior is **empty** — no exterior bird has any live edge into the interior at all, so the maximum attainable recall of any causal-probe or authority estimator, however unbiased, is 0 at this step regardless of pool construction or budget. This is a controllability-relevant fact (Part J), not just a firewall fact, and is why every one of the 10 candidates' authority estimate `A_j` came back exactly `0.0` (`H_do_mean == H_base_mean` bit-for-bit for all 10 — see §4) — a clean, mechanistically-explained null, not noise.
- **Repair status:** not implemented in this pass, per the brief's instruction to report the violation first and preserve the existing result. A blind comparator pool (nearest-`M` exterior agents, or a distance threshold from the observer's own `local_scale`/nearest-neighbour statistics, exactly analogous to how `predictive_boundary_611.py` already builds its pool) is scoped as follow-up work in Part K's confirmatory study design, not built here.

---

## 3. The lineage "no death alternative" defect (feeds Part D/E)

`LineageTracker611.update` has **one** death path: *zero* candidates in `C_t` clear `R_retain ≥ 0.30` against a given hypothesis (`lineage_611.py:153-159`). If **at least one** candidate clears that floor, the hypothesis **must** branch into at least one child, regardless of how bad that candidate's spatial/functional match is on every other axis (`R_F`, displacement, exterior contrast): the branch-softmax (`lineage_611.py:161-167`) always sums to 1 over whatever passed the retention floor, however small the winning `score` is or however close it is to its competitors. There is:
- no "no valid continuation, hold as unresolved" state distinct from "dissolved" or "continued";
- no minimum-score floor on `score = 0.6·dice + 0.4·R_F` independent of the `RETENTION_MIN` material-overlap gate;
- no path for an unmatched-but-plausible candidate elsewhere in `C_t` to seed a competing new lineage while the old one still has a (bad) viable match — the tracker never asks "is there a *better* explanation than continuation" once continuation is merely *possible*.

This means: any candidate with ≥30% material overlap with the previous interior — even one displaced far beyond what bulk-translation would predict, with collapsed field similarity — is *eligible* to inherit 100% of a hypothesis's probability mass if it is the *only* eligible candidate that step, or a large share if it's merely the best-scoring one among several weak options. This is the exact class of defect the task brief's Part D/E describes as "forced identity teleportation." Whether it actually produced seed 500's apparent t=20→21 interior replacement is a factual question for the forensic audit (`LINEAGE_FORENSICS_6_11.md`, not yet performed) — this section only establishes, from source, that the code path which *would* produce that failure mode exists and is unguarded.

---

## 4. Worked numerical example — seed 500, t=61 (the episode's first control step)

Full record: `audit/worked_example_seed500_t61.json`. All numbers below reproduce the production run in `data/online_control_611__seed500.json` exactly (`B_pred=null`, `B_causal=[]`, `B_C=[68,107,125,131,147,173,253,285]`, `frac_interior_at_target=0.1212...` all match bit-for-bit).

1. **Candidate detection** (`detect_69.propose`): 13 communities from Louvain on the affinity graph; sizes 39→12. Largest three (39, 38, 36) are *not* selected as interior — dominance is by lineage-tree MAP probability, not raw size (next step).
2. **Lineage state:** the tracker (started ~60 steps earlier, `age=60`) holds **5 live hypotheses** simultaneously: `{hid 29: p=0.602, size 33}`, `{hid 41: p=0.147, size 12}`, `{hid 30: p=0.123, size 33}`, `{hid 43: p=0.103, size 12}`, `{hid 40: p=0.024, size 36}`. Note hid 29 and hid 30 are **both size-33, both `R_retain_step=1.0`, both `R_F=0.876`, both `n_components=11`** — i.e. two hypotheses with numerically-identical-looking step records but different accumulated probability (0.602 vs 0.123), a direct consequence of the `MAX_HYPOTHESES=6` branching tree carrying forward near-duplicate branches rather than merging them. `Î_t` = argmax → hid 29's 33 members, taken with no margin or entropy check even though the runner-up hypothesis is only 4.9× less probable and materially the same size/shape.
3. **`Î_t` geometry (from hid 29's last record):** `size=33`, `R_retain_from_origin=0.130` (87% of the original t=0 material has turned over across 60 steps — expected/intended per PLAN.md §S), `R_F=0.876` (high co-moving functional similarity despite the turnover — the target phenomenon), `D=1.0` (periphery maximally behaviourally distinct — no individuation blending), **`n_components=11`** (the "interior" is spatially fragmented into 11 disconnected spatial pieces, not one contiguous blob), `bulk_speed=0.196`.
4. **`B̂pred`:** `null` — `interior_periphery_targets` found no interior member within `local_scale(r,L)` of any non-member at this exact snapshot (or the rolling window had too few rows), so `construct_boundary` was skipped and the stale (nonexistent) cache carried forward as `None`.
5. **Exterior pool:** `near_exterior(mf, r, interior, radius_factor=3.0)` → **10** birds: `[68,107,125,131,147,173,253,285,292,328]`, out of 367 non-interior birds. The true causal boundary `oracle_B_D(r,z,interior)` (reference-only, never consumed downstream) is **empty** — `[]`. All 10 pool birds are true negatives by construction.
6. **`B̂causal`:** `probing_611.probe_sources` over the 10-bird pool, `20×2` rollouts each: every source's `C^do_j = 0.0` exactly (bootstrap CI `[0,0]`), so `B̂causal = []`. Mechanistically forced — with an empty true causal boundary, a one-step state intervention on any of these 10 birds cannot change any interior bird's next heading (their `G_i` sums have zero live edges to any of them), so the finite-sample estimate correctly recovers the true null with zero variance rather than merely failing to detect a small effect.
7. **`Â_t`/`B̂C`:** `MultiStepAuthorityProbe.authority`, τ=4, 10 rollouts/candidate: every candidate's `A_j = H_do_mean - H_base_mean = 0.0` exactly (e.g. `j=68: H_do_mean=H_base_mean=0.0667`). `select_actuators` top-8-sorts 10 exactly-tied zeros — the resulting `B_C=[68,107,125,131,147,173,253,285]` is therefore the first 8 pool entries in ascending-index order (the pool's own construction order, since `sorted()` is stable on ties), **not** a meaningfully-ranked top-8; the two excluded candidates (292, 328) are excluded only by list position, not by any authority difference.
8. **Actuation and outcome:** all 8 chosen actuators forced to `target_heading=1`. One real step later, `frac_interior_at_target` moved from `0.1212 → 0.0909` — i.e. *away* from target, consistent with the actuation having had no real causal purchase at this step (as §6/§7 predict) and the change instead reflecting the collective's own unforced fluctuation.

**Interpretation flagged for Part J/H, not concluded here:** this single step is consistent with "seed 500 was, at least momentarily, in a genuinely zero-authority configuration" rather than "the estimator was stale or under-budgeted" — the estimate is not stale (it was freshly computed this exact step, `age_causal=age_authority=0`) and not under-powered in a way more rollouts would fix (the true effect is exactly zero, not merely small). Whether this holds at other seed-500 control steps, or whether authority recovers later in the 24-step control window, is exactly what Part H's per-refresh staleness log is for and is not established by this one worked step alone.

---

## 5. Summary table (feeds `RESULTS_6_11_AUDIT.md`)

| instrument | intended meaning | exact implementation | validated by existing tests? | known limitation (this audit) |
|---|---|---|---|---|
| `C_t` (candidates) | all currently-plausible spatial/behavioural communities | weighted-Louvain on torus-distance × heading-agreement affinity, size-filtered | firewall AST+seal only | recomputed from scratch every step; no continuity smoothing of the detector itself |
| `Î_t` (interior) | the tracked collective's current membership | MAP (argmax prob) live lineage hypothesis | none directly | no margin/entropy gate on the MAP pick (§4.2); ties/near-ties resolved silently |
| lineage `prob` | belief the candidate continues this hypothesis | per-step softmax(0.6·Dice+0.4·R_F) over `R_retain≥0.30`-viable candidates, chained multiplicatively across steps | none directly | not a calibrated posterior (§1.2); no death alternative once ≥1 candidate is viable (§3) |
| `B̂pred` | passive predictive-sufficiency boundary | greedy conditional forward selection on relational-histogram log-loss, `K_max=12` | offline certification only (`predictive_boundary_611.py:339-397`), not re-run online | online refresh only every 36 steps; can return `None` for whole control steps (§4.4) |
| `B̂causal` | task-neutral one-step causal interface | bootstrap-CI-thresholded paired-CRN state-intervention discrepancy rate | 66/66 firewall tests (object/import provenance only) | **candidate pool built from true R** (§2) — content, not object-type, leakage |
| `Â_t`/`B̂C` | signed, target-directed, τ-reachable authority | independent top-K by one-shot-forced τ=4 paired-CRN rollout | 66/66 firewall tests (same caveat) | **same pool leakage**; **one-shot-vs-held intervention-duration mismatch** (§1.5) between estimation and execution |
| actuator selection | which K=8 birds to force | plain top-K individual authority, no conditioning on co-selected actuators | none (never previously named a search algorithm) | not greedy/multicover/beam — ties broken by pool order, not by any secondary criterion (§4.7) |

---

## 6. What remains for the rest of the audit program

This document covers Part A (methodology, from code, with a verified worked example) and the load-bearing half of Part B (data-flow firewall audit, pool-size chain, reference-only causal-parent recall). Not yet done, and each requiring either new instrumented replay runs (cheap) or new experiments (expensive — probe rollouts, beam search, 40–60-state confirmatory study):

- Reference-only recall of true causal parents in each pool, averaged over many steps/seeds (this document reports it for one step only).
- Parts C (invariance/transfer), D (full 5-seed lineage forensics with per-timestep CSVs), F (Bpred multivariate-challenger re-certification), G/H (causal/authority refresh-log audit, seed-504 staleness timeline), I (cadence comparison), J (controllability benchmark), K (confirmatory study), L (synergy check), M (buffer contamination check), N (visualization).
