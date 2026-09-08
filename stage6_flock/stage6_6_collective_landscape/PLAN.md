# PLAN.md — Stage 6.6: Collective Landscape

Planning document, written before any Stage 6.6 code ran. Records scope
decisions up front so `RESULTS_6_6.md` can be checked against stated intent
rather than rationalized after the fact, matching the Stage 6.5 convention
(`../stage6_5/PLAN.md`).

## What Stage 6.6 is and is not

It is exploratory, flock-specific work asking a question Stage 6/6.5 exposed
but never addressed: when does a `k`-sized subset of the flock look and
behave like an individuated collective, rather than an arbitrary patch of a
globally aligned system? It produces **four separate coordinates**
(coherence `C`, internal predictive integration `G`, budgeted blanket
leakage `L`, local inside/outside contrast `D`) for thousands of candidate
`k=20` interiors, plus a UI to explore them.

It is **not**:

- A universal definition of biological individuality or agency. Every
  document in this stage says so explicitly where the metrics are
  introduced.
- A search for a single scalar "thingness" score. `Phi(I) = (C,G,L,D)` is
  reported as a tuple; no `a*C+b*G-c*L+d*D` or product is ever computed as a
  primary quantity. Pareto nondominance across `(C,G,-L,D)` is provided only
  as an optional, off-by-default visualization filter (task brief section
  8/24) — it does not drive candidate generation or conclusions.
- A new controller-optimization stage. The exterior-forcing archetypes
  (Section 11/12 of the task brief) reuse the existing V1-V3 intervention
  hook unmodified, at existing frozen parameters, purely to produce
  interpretable test cases for the four metrics. No `max_u Q_thingness`
  optimization is implemented (task brief section 31).
- A refit of the Stage 6.5 predictive model family. The nodewise multinomial
  logistic-regression estimator, its hyperparameters
  (`C=1.0, penalty=l2, solver=liblinear, max_iter=200`), and its per-bird
  fit/held-out-logloss interface are reused verbatim
  (`stage6_5/boundary_inference/code/nodewise_model.py:NodewiseModel`); only
  the *conditioning sets fed to it* are new (per-bird neighbour-subset masks
  instead of a single shared `I0 union cond_extra` set).

## Reused, unmodified

- `python/flock_sim/{lattice,model,active_inference,simulation,metrics,
  interventions}.py` — simulator, transition dynamics, `rotate_cw`/
  `rotate_ccw`, `coherence()` (literally `C_I`), `make_pulse()` (the control
  hook). Imported, never edited.
- `v2_interface_control/code/common_v2.py:find_flock` — per-seed flock
  discovery (`t0, h0, h_star, I0, z_t0`), and its `T_U=20, T_R=20` constants.
- `v1_mechanism_audit/code/dynamical_shell.py:one_hop_neighbors,
  k_hop_shell, graph_distance_from_set` — structural one-hop shell `S(I)`
  and graph-distance shells, reused for the near/distant exterior split.
  `dynamical_shell.py`'s own worked example (`I0` canonical, `B^D_0`,
  `|B^D_0|=12`) is the origin of this stage's fixed boundary budget `K=12`
  (task brief section 4) — stated explicitly rather than re-derived.
- `python/analysis/canonical_snapshot.py` / `python/analysis/
  baseline_characterization.py:find_qualifying_t0` — canonical seed-2 `I0`
  (`t0=41, h0=2 (left), h_star=0 (up), |I0|=20`) and the flock-qualification
  rule used to discover seed 3 and seed 4's own interiors.
- `flock_sim.spectral.analyze_window` — `core1_nodes`/`core2_nodes` used as
  one of the five candidate-interior generation methods (task brief section
  9, "existing spectral/community proposals").
- `stage6_5/boundary_inference/code/nodewise_model.py:NodewiseModel,
  design_matrix` — the predictive model itself (see above).

Nothing in `stage6_5/` or earlier is modified. This stage is purely
additive, as required by the repository-wide norm stated in every prior
stage's README.

## Primary objects, fixed before any candidate was generated

- `k = |I| = 20` for the primary experiment (task brief section 1). The
  implementation (`code/candidates.py`) takes `k` as a parameter so other
  values can be explored later, but no run in this stage uses `k != 20`.
- `K = 12` boundary budget (task brief section 4), matching
  `|B^D_0(I0_canonical)| = 12` exactly (Section "Reused, unmodified" above).
- `W = 10` step window, `R = 100` paired replicates (task brief section 6).
- Primary flocks: **seeds 2, 3, 4** — the first three of V3's frozen dev
  pool, chosen the same way Stage 6.5 chose them (already "deeply
  characterized," not selected after seeing Stage 6.6 results — task brief
  section 12). Seed 2's `I0` is exactly size 20 already (canonical
  snapshot). Seed 3's spectral `I0` is size 19 and seed 4's is size 20
  (`data/baseline_v1/baseline_rows.json`); a seed's reference `I0` is
  resized to exactly `k=20` by the same connectivity-preserving
  grow/trim rule used for the "spectral proposals resized to k=20"
  candidate-generation method (`code/candidates.py:resize_to_k`), applied
  identically regardless of whether the seed needs 0, +1, or a larger
  adjustment. This is recorded per-seed in `data/*_reference_I0.json`.

## Scope-narrowing decisions (stated up front, not discovered later)

1. **Candidate count.** The task brief asks for >=5000 unique connected
   `k=20` candidates per visualized snapshot. Candidate *generation* is
   cheap; candidate *evaluation* is made cheap by the mask-cache design in
   section 5 of the brief (`code/predictive_cache.py`), whose cost is
   bounded by `sum_i 2^deg(i)` over the *touched* birds regardless of how
   many candidates are drawn from those birds — i.e. cost saturates, it does
   not grow linearly with candidate count once most of the lattice is
   touched. A timing pilot (logged in `logs/timing_pilot.json`) is run
   before committing to a final per-snapshot candidate count; the number
   actually used for each snapshot is recorded in `PROTOCOL_6_6.md` and may
   be below 5000 for archetype-condition snapshots (B-E) if the pilot shows
   the Natural-regime run alone saturates the compute budget for this
   session. This is a deliberate, disclosed compute-budget decision, not a
   silent reduction.
2. **Snapshot timepoints.** Per task brief section 25, only the fixed
   control-end timepoint `t = t0 + T_u` is computed for the primary
   landscape in this first implementation. `t0`, mid-control, and
   release-end are left as a documented future extension (brief explicitly
   permits this: "do not delay the core implementation waiting for all
   timepoints").
3. **External-control budget sweep (`f_E`).** Computed for the fixed
   candidate `I0` only (task brief section 13/27), not for the full
   candidate landscape — the brief itself scopes it this way ("The full
   landscape visualization only needs the `f_E=1` archetypes precomputed as
   snapshots. The full `f_E` sweep should be used to show metric
   trajectories/trade-offs.").
4. **Visualization QA.** A full cross-viewport Playwright suite is written
   and run against the built demo (`tests/qa_playwright.py` /
   `tests/qa_report.md`), but is scoped to the checks enumerated in task
   brief section 34 rather than a general regression suite of the whole
   demo — pre-existing Control-mode and Inference & Identity behavior is
   spot-checked for non-regression, not re-verified exhaustively (that
   coverage belongs to Stage 6.5's own QA artifacts, not this stage's).

## Freeze point

`PROTOCOL_6_6.md` + `configs/protocol_6_6.yaml` are written and hashed
**after** the timing pilot and the controlled-archetype sanity checks
(task brief section 11, "before building the full visualization") have run,
and **before** the full 5-seed x snapshot candidate landscape is generated
for the demo. `METRIC_VALIDATION.md` is the gate: if the four metrics do not
behave in the qualitatively-expected way on the controlled archetypes, this
plan requires stopping and reporting the failure (task brief section 15)
rather than adjusting metric definitions to manufacture the desired
ordering.
