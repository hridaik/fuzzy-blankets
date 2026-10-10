# REFINEMENT_PLAN.md — V3: interface-control law, integrity redefinition, predictive permeability

Written **before** any V3 sweep is run. This document fixes the design choices
that must be pre-registered (flock splits, sweep grids, replicate counts,
threshold-selection *procedure*) so that later results cannot be read as
"tuned until pretty." Numeric thresholds themselves (e.g. `gamma`, `T_rec`,
`c_recover`) are deliberately **not** fixed here — Part 2 requires examining
baseline transition statistics first, and Part 1D requires examining
dev-flock coverage curves first. What *is* fixed here is: which flocks count
as development vs. held-out, what is measured, and the rule for turning
measurements into a threshold. `PROTOCOL_V3.md` freezes the thresholds
themselves, with a hash, before final held-out evaluation.

Everything below is additive. `v1_mechanism_audit/` and `v2_interface_control/`
data, code and results are read-only inputs; nothing here overwrites them.

## Reused infrastructure (not reimplemented)

- Simulator: `python/flock_sim/*` (unchanged).
- Flock discovery: `analysis.baseline_characterization.find_qualifying_t0`
  (Phase-2A rule, unchanged) via `v2_interface_control/code/common_v2.find_flock`.
- `B^D_0(I0)` (dynamical shell): `common_v2.dynamical_shell` (unchanged).
- `B^F_0(I0)` (Fiedler boundary): `flock_sim.spectral.analyze_window` (unchanged).
- Control evaluation harness: `common_v2.evaluate_arm` (extended, not replaced —
  see `code/coverage_metrics.py` / `code/evaluate_v3.py` below, which add
  coverage/multiplicity/concentration outputs alongside the existing fields).
- Actuator rules A/B/C/D: `v2_interface_control/code/selection_rules.py`
  (imported, unchanged). V3 adds Rule R (explicit alias of D, for the naming
  in the task brief) and Rule COVER (new, `code/selection_rules_v3.py`).

## Flock pool: development vs. held-out (fixed before any Part 1 sweep)

V2's 10 replication flocks (seeds **2,3,4,8,9,10,11,13,14,16**, found by
scanning seeds 0-16 under the unchanged Phase-2A rule) are already frozen,
published evidence and were already used once (to derive the 0.75-fraction
budget on seed 2, and to compare rules across all 10). Reusing them as the
**development set** is honest bookkeeping, not double-dipping: no V3 metric
(coverage, concentration, multiplicity, gamma-threshold) has been computed
against them until this session.

- **Development flocks (10)**: seeds 2, 3, 4, 8, 9, 10, 11, 13, 14, 16.
- **Held-out flocks**: continue the *same* Phase-2A scan from seed 17 upward
  (numeric order, first-found, no re-drawing) until 6 more qualifying flocks
  are found, or seed 40 is reached, whichever comes first. This range was
  never inspected in V1 or V2. The resulting seed list is recorded in
  `data/held_out_flocks.json` the first time the scan is run, and is not
  re-run or cherry-picked afterward.
- Any threshold, fraction, or rule choice for the final V3 controller
  (`gamma`, `T_rec`, `c_recover`, the COVER-rule budget) is derived **only**
  from the development flocks. Held-out flocks are touched exactly once, for
  final reporting (Part 1E), after every threshold is frozen in `PROTOCOL_V3.md`.

## Part 1 — interface-control law

### 1A. Per-arm structural quantities (`code/coverage_metrics.py`)

For any flock (`I0`, `B^D_0`, `lattice`) and any actuator set `A subset B^D_0`:

- `f_A = |A| / |B^D_0|`.
- `Gamma(A)` = fraction of `I0` with at least one neighbor in `A` (`j ~ i`
  read as `j in lattice.neighbor_ids[i]`, i.e. the same adjacency that
  defines `B^D_0` itself — the one that provably enters `compute_G`).
- `m_i(A)` for every `i in I0`: count of `A`-members adjacent to `i`. Report
  mean, median, min, `P(m_i>=1)`, `P(m_i>=2)`, `P(m_i>=3)`.
- Concentration, computed on the induced lattice subgraph of `B^D_0`:
  - `n_components(A)`: connected components of `A` under that induced adjacency.
  - `max_component_fraction(A) = max component size / |A|`.
  - `sector_entropy(A)`: `B^D_0` is partitioned into angular sectors (8
    bins, atan2 around the `I0` centroid in lattice row/col coordinates);
    Shannon entropy of `A`'s occupancy across sectors actually populated by
    `B^D_0`, normalized by `log(n_sectors_occupied_by_B^D_0)` so it lies in
    `[0,1]` regardless of shell shape.
  - `mean_pairwise_graph_distance(A)`: mean BFS lattice-graph distance
    between all pairs in `A`, normalized by the same quantity computed over
    all of `B^D_0` (so 1.0 = as dispersed as the full shell, 0 = maximally
    clumped).
- These are pure graph computations (no simulation), reported for every arm
  alongside its simulated outcome.

### 1B. Coverage sweep (`code/coverage_sweep.py`)

Grid: `f_A in {0.1, 0.2, ..., 1.0}` (10 fractions) x 5 rules x 10 dev flocks.
`k(f_A) = max(1, round(f_A * |B^D_0|))`, clipped to `|B^D_0|`.

- **Rule R (random)**: `rule_D_random` (identical procedure; V3 name matches
  the task brief's "R").
- **Rule DEG**: `rule_A_degree` (identical procedure; V3 name matches the
  task brief's "DEG").
- **Rule LEV**: `rule_B_leverage`, reusing its predeclared per-bird sweep
  (`n_replicates=20`), computed once per flock at `k=|B^D_0|` (full ranking)
  and then truncated to each `k(f_A)` — not re-ranked per fraction, to avoid
  8-fold-repeating an expensive per-bird sweep.
- **Rule COVER** (new, `code/selection_rules_v3.py`): greedy maximum-coverage
  — repeatedly add the `B^D_0` member covering the most currently-uncovered
  `I0` birds (ties broken by highest raw `I0`-degree, then bird index) until
  `k` actuators are chosen. This directly targets `Gamma(A)`, not simulated
  outcome.
- **Rule PATCH**: `rule_C_patch` (unchanged; the known-poor comparator).
- Replicates: **20 per (flock, rule, fraction)** condition (development
  scale, same `T_u=20, T_r=20` and common-random-number convention as V2,
  logged as such). Total: 10 x 5 x 10 x 20 = 10,000 runs, ~30-60s of compute
  given the ~27ms/60-step-sim measured baseline.
- Record, per condition: `f_A, |A|, Gamma(A), mean/median/min m_i,
  P(m_i>=1), P(m_i>=2), n_components, max_component_fraction, sector_entropy,
  mean_pairwise_graph_distance, p_success, mean_Hstar_end, mean_Hstar_release,
  mean_min_coherence, p_success_and_integrity_full/recovery` (old criterion,
  reported not reused as final), `p_persistence_given_success`.

### 1C. What predicts success (`code/fit_success_models.py`)

Fit, on **development-flock data only**, three nested logistic regressions
of binary per-replicate success on: (i) `f_A` alone, (ii) `Gamma(A)` alone,
(iii) `Gamma(A) + mean(m_i)`. Report McFadden pseudo-R^2 and held-out
(cross-flock, leave-one-dev-flock-out) log-loss for each — not in-sample R^2
alone, which would favor the richer model trivially. State plainly which
quantity collapses the data more cleanly; do not force a preferred ranking.

### 1D. Minimal sufficient interface (`code/minimal_interface.py`)

Once 1B/1C are in hand: solve, per dev flock, `min |A| s.t. Gamma(A) >= gamma`
via the same greedy COVER procedure (which is optimal for plain set-cover up
to the standard log-factor bound) for a grid of candidate `gamma in
{0.5,0.6,...,1.0}`. For each candidate `gamma`, compute mean dev-flock
`p_success` at the resulting (per-flock-varying) `|A|`. Choose the **smallest
gamma whose dev-mean `p_success >= 0.8`** (mirroring V2's own 0.75-fraction
selection rule, generalized to a coverage-based criterion) — this choice
is made and frozen in `PROTOCOL_V3.md` *before* touching held-out flocks.

### 1E. Held-out generalization

Apply the frozen `gamma` (and, for comparison, the frozen `f_A=0.75` from
V2) to the 6 held-out flocks, computing the same outcome fields as 1B. This
is the only time held-out flocks are used for anything threshold-related.
Report success probability, `|A|`, `f_A`, `Gamma(A)`, and persistence,
compared against the dev-flock numbers, explicitly checking whether the
*general* claim ("enough Gamma-coverage predicts success, near-independent
of which IDs") holds up better than the narrower "75% of the shell" framing.

## Part 2 — functional integrity (see `INTEGRITY_DEFINITION.md`, `PROTOCOL_V3.md`)

`INTEGRITY_DEFINITION.md` is written as a conceptual note with **no**
numbers chosen yet. Numeric thresholds (`c_recover`, `T_rec`, dwell period)
are chosen only after examining baseline transition statistics from the
Part 1B full-shell sweep (`coh_traj` is already recorded per replicate for
every arm, reusing `evaluate_arm`'s existing per-timestep coherence array) —
specifically the distribution of `C_min`, `T_low`, and empirical recovery
time across all dev-flock, all-rule, `f_A=1.0` and `f_A~gamma` conditions.
Thresholds are then written into `PROTOCOL_V3.md`, hashed, and used
unchanged for the Part 2D staged-actuation comparison and all final
reporting.

## Part 2D — staged actuation (`code/staged_actuation.py`)

Compared at matched total control budget (`k = k(gamma)` from Part 1D, one
representative dev flock's shell size, and pooled across 3-4 dev flocks for
robustness — not just the canonical flock):

- **Pulse**: existing `make_pulse` (all k actuators, full strength, for the
  whole `T_u` window) — the V1/V2 baseline.
- **Ramp-up**: partition the k actuators (by COVER-rule addition order, so
  the earliest-added actuators are the ones covering the most new core
  birds) into 4 tranches of `k/4`; bring one tranche online every `T_u/4`
  steps, cumulatively, so all k are active by the final quarter.
- **Sequential distributed recruitment**: partition the k actuators by
  angular sector (same 8-sector partition as 1A) rather than by COVER
  order; activate one sector-group at a time, round-robin, so coverage
  breadth (not depth) increases first.
- **Ramp-down/release taper**: full k active for the first `3*T_u/4` steps,
  then linearly reduce the active actuator count to 0 over the last `T_u/4`
  steps (reverse of ramp-up), rather than releasing all at once.

All four use the *same* total actuator-budget-times-steps ("control
effort") for a fair comparison, made explicit in `RESULTS_V3.md`. Compare
`C_min`, `T_low`, recovery time, final `H*`, and persistence. Report
honestly if none of the schedules reduce the coherence dip — Part 6 of the
task brief explicitly permits "the dip is intrinsic" as a valid conclusion.

## Part 3 — predictive permeability vs. horizon (`code/predictive_permeability.py`)

Extends `v1_mechanism_audit/code/predictive_screening.py`'s one-step
methodology (M_full / M_B / Monte-Carlo mean-field marginalization of
everything outside `I0 union B`) to a horizon sweep `tau = 1..6`, and to
both `B = B^D_0` and `B = B^F_0`, run on a subset of **4 development
flocks** (seeds 2, 3, 8, 13 — chosen for shell-size/eigengap diversity
already characterized in V1/V2, not by any Part-3 outcome) to keep compute
bounded while still supporting a qualitative B^F-vs-B^D comparison. For each
`(flock, B, tau)`: excess log-loss of `M_B` (condition on `X_{I,t}, X_{B,t}`
only, marginalizing the rest of the state by Monte-Carlo resampling from the
pooled empirical per-timestep marginal, exactly as the existing script's
`M_BF` branch) vs `M_full` (condition on the entire true state at `t`,
averaged only over the forward stochastic dynamics), evaluated against the
realized `X_{I,t+tau}` from real trajectories. Report `P_tau` (excess
log-loss, a log-loss analogue of the CMI in the task brief) vs `tau`, for
both boundaries, on one shared figure per flock plus a pooled summary.

## Part 3C — control/permeability correlation

Exploratory only: scatter `Gamma(A)` (Part 1) against `P_tau` at the
horizon matching `T_u` (Part 3) and against `p_success`, across dev flocks.
Report the correlation honestly; do not claim causality.

## Part 4 — interactive demo

Built incrementally, starting now (data schema + a minimal working page),
not bolted on at the end — see `interactive_demo/README.md`. The Python
side exports full per-timestep trajectory bundles (`z_hist`, actuator
schedule, `B^D_0`, `B^F_0`, `I0`, live metrics, markers, provenance) via a
new `interactive_demo/data/export_scenarios.py`; no dynamics are
reimplemented in JavaScript.

## Part 5 — figures

`code/make_v3_figures.py`, following the existing `Agg`-backend,
data-driven, PNG+PDF convention from `v1_mechanism_audit/code/make_figures.py`
and `v2_interface_control/code/make_v2_figures.py`.

## Stopping rules

As stated in the task brief Part 6, verbatim as the operating rule for this
session: do not force the expected story at any of the above steps; report
whichever outcome the data actually show, including "coverage doesn't
collapse it," "COVER isn't better than DEG/LEV," "staged actuation doesn't
help," or "Fiedler does fine at short horizons." `STAGE6_FINAL_REFINEMENT.md`
will report on all such branches as they actually resolve.
