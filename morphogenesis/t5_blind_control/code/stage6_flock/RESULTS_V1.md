# RESULTS_V1.md — Experiment 1 findings

Status: **primary finding is negative.** Under the protocol frozen in
`PROTOCOL_V1.md`, sparse external control confined to birds outside the frozen
core `I0` did **not** reproducibly retarget the core to the adjacent cardinal
heading within the pre-declared horizon and success threshold, for `k=1`,
`k=2`, or a greedy escalation up to `k=6` actuators (drawn from a
top-10-by-response shortlist). This is reported as the honest result of the
stated search procedure, not a global impossibility proof (the search was not
exhaustive beyond `k=2`, and only one canonical initial flock was tested at
full depth — see section 6).

## 1. What was verified from the original implementation (Gate A)

See `METHODS_AUDIT.md` (line-by-line source audit) and `PORT_VALIDATION.md`
(25 passing unit/validation tests; qualitative reproduction of emergent
alignment; a proven structural simplification — `G(u)` does not depend on a
bird's own current-heading belief). No MATLAB/Octave was available in this
environment; validation relied on deterministic/algebraic checks and
distributional comparison, per the task brief's explicit allowance for this.
**Confirmed discrepancies between the paper's text and the released code**
(full list in METHODS_AUDIT.md section 13): transition/preference precisions
(`rho=15`, `omega=3` in code vs. "all set to 1" in text); the Fiedler boundary
rule is a fixed absolute threshold (`|y2|<0.05`) in code vs. an adaptive
percentile rule described in the text; the 500/1000-simulation ensemble driver
and the PID/synergy/Potts-energy analysis pipeline behind the paper's Fig. 2-3
are not present in the 4 released files (only single-simulation building
blocks are); a `rng('default')` reset at the top of the released
`flocking_AIF_simulation.m` means the code as released does not vary across
naive repeated calls.

## 2. What was decided before any control was run

`PROTOCOL_V1.md` freezes: the Phase 2A flock-selection rule (eigengap, size,
coherence, lineage-stability thresholds) and its results on a 300-replicate
uncontrolled baseline (53.7% qualification rate; `t0` median 8; `|I0|` median
20; eigengap median 9.73); the canonical snapshot (seed 2, `t0=41`, `h0`=left,
20-bird core); the control horizon `T_u=20` and release horizon `T_r=20`,
chosen so that spontaneous target attainment is low (6.6%) but not
vanishing; the task-success (`H*>=0.8`), integrity (`C_I0>=0.8`,
`R_I>=0.5`), and persistence (`H*>=0.5` post-release) criteria; and the
actuator-search procedure (exhaustive `k=1`, then top-10-shortlist pairs,
then greedy).

**One correction was applied after freezing but before any actuator search**:
a heading-encoding bug (`(h0+1) mod 4` is not a 90-degree rotation in the
upstream state ordering `{up,down,left,right}`) was caught via an anomalous
Phase-3A control diagnostic and fixed geometrically
(`flock_sim.model.ROT_CW`/`ROT_CCW`) before Phase 4/5 began — see
`PROTOCOL_V1.md` section 1a for the full, transparent account, including the
preserved pre-fix data (`data/baseline_v1_buggy_naive_hstar_DO_NOT_USE/`).

## 3. What was observed

### 3.1 Gate D (intervention feasibility): PASSED

Phase 3A controls, branching from the canonical snapshot, 50 replicates each,
common random numbers:

| Arm | mean H*(t0+Tu) | P(success) | P(success & integrity) | mean H* at release |
|---|---|---|---|---|
| No control | 0.000 | 0.000 | 0.000 | 0.000 |
| Positive control (force entire `I0`, 20 birds) | 1.000 | 1.000 | 1.000 | 0.594 |
| Negative control (1 Chebyshev-farthest exterior bird) | 0.000 | 0.000 | 0.000 | 0.000 |

The intervention hook works as intended (full direct forcing succeeds; a
single, deliberately weak, far exterior bird has no effect; the uncontrolled
baseline never spontaneously reaches the target within `T_u=20` for this exact
initial condition). A secondary, unplanned-for finding: **even full-core
forcing loses ~40% of its target-heading fraction within `T_r=20` steps of
release** (`mean H*`: 1.000 -> 0.594) — the forced state is not fully
self-sustaining even under the strongest possible intervention, though it
clears the (weaker, pre-declared) persistence bar of 0.5.

### 3.2 Gate E / Phase 4 (empirical actuator-response map): informative negative result

Exhaustive single-actuator (`k=1`) sweep over all 80 non-interior birds, 50
replicates each (`data/protocol_v1/phase4_5_response_map.json`,
Figures 3-4): **no single bird reaches even a small fraction of the
target.** Maximum mean `H*(t0+Tu)` across all 80 candidates was **0.056**
(bird 67); 64/80 birds showed a mean effect indistinguishable from exactly
zero across 50 replicates; `P(success) = 0` for all 80. There was no
detectable relationship between spectral role (boundary vs. exterior) and
response magnitude in this dataset — the spectral boundary at `t0` had only 2
members (a small-sample caveat, see section 5), and both had zero response.

### 3.3 Phase 5A sparse search: k=1 and k=2 fail; greedy escalation results below

`k=1`: no actuator meets `P(success)>=0.5` (best: 0.000, see above).

`k=2`: exhaustive search over all 45 pairs within the top-10 single-actuator
shortlist (`data/protocol_v1/phase5_k2_search.json`). Best pair {67, 57}
reached mean `H*(t0+Tu) = 0.149`, still far below the 0.8 success threshold;
`P(success) = 0` for all 45 pairs.

`k=3..6` (greedy, same shortlist, `data/protocol_v1/phase5_greedy_k.json`),
each step adding the single remaining shortlist bird that most increases
`mean_Hstar_end`:

| k | actuators (bird indices) | mean H*(t0+Tu) | P(success) |
|---|---|---|---|
| 2 | [67, 57] | 0.149 | 0.000 |
| 3 | [67, 57, 46] | 0.195 | 0.000 |
| 4 | [67, 57, 46, 66] | 0.254 | 0.000 |
| 5 | [67, 57, 46, 66, 77] | 0.274 | 0.000 |
| 6 | [67, 57, 46, 66, 77, 68] | 0.282 | 0.000 |

The increment per additional actuator shrinks monotonically (+0.046, +0.059,
+0.020, +0.008 from k=2 to k=6) — clear diminishing returns, saturating well
below the 0.8 threshold, with `P(success)` remaining exactly 0.000 throughout.
The greedy search was stopped at `k=6` (30% of the 20-bird core) because the
trend was unambiguous and the shortlist was nearly exhausted; it was not
carried to convergence or to `k` values that would no longer count as
"sparse" relative to `|I0|=20`.

### 3.4 Interpretation

The response magnitude grows slowly and highly sub-linearly as more actuators
are added (roughly consistent with each additional bird contributing a small,
diminishing increment rather than triggering a cascade). **Within the search
performed, sparse control confined to a small number of exterior birds cannot
retarget this flock's frozen core to an adjacent heading inside the
pre-declared horizon.** This is reported as the result, not patched by
loosening the horizon, threshold, or actuator budget after the fact (all of
which were frozen in `PROTOCOL_V1.md` before this search began).

## 4. What is robust

- The port itself: 28 passing tests covering neighbor construction, the
  observation/transition/preference model, the spectral pipeline, and
  end-to-end reproducibility.
- The Phase 3A Gate D result: the intervention mechanism is not broken —
  direct, sufficiently large forcing works; the failure in section 3.2-3.3 is
  about *sparse* forcing specifically, not about the simulator or the
  intervention hook.
- The qualitative picture: this flocking model's alignment dynamics are
  strongly self-reinforcing (full polarization is essentially absorbing, see
  PORT_VALIDATION.md section 3), which independently explains both (a) why
  spontaneous rotation is rare (supporting task non-triviality) and (b) why a
  small number of dissenting exterior birds struggle to overcome an already
  20-bird-strong, mutually-reinforcing consensus within 20 steps.

## 5. What remains provisional

- The Fiedler classification at `t0` produced an unusually small spectral
  boundary (2 nodes) for this particular canonical snapshot; whether "spectral
  boundary role predicts control leverage" (the paper's/task's second
  question) has a fair test here is doubtful with n=2 — this needs a flock
  with a larger, more typical boundary before the boundary-vs-exterior
  comparison (Figure 4) can be considered informative rather than
  underpowered.
- Only one canonical initial flock was tested at full depth (`k=1` exhaustive,
  `k=2` exhaustive-on-shortlist, greedy to `k={K_MAX}`). Phase 6 replication
  across independently emergent flocks (different seeds) was only partially
  run in this session (see section 6) — a full, task-brief-scale
  independent-replication study (multiple canonical flocks, each searched to
  the same depth) was not completed given this session's time budget.
- Replicate counts used (50 per actuator/pair/greedy-step) are the brief's
  "development" scale, not the "final canonical comparison" scale of 200+.
  Given `P(success)=0` was observed at n=50 for every single-actuator and
  pairwise candidate (not a borderline probability estimate), more replicates
  would tighten confidence intervals but are very unlikely to overturn the
  qualitative conclusion (mean effect sizes were near zero, not "just under
  0.8"). This is stated as a judgment call, not a claim that n=50 is
  equivalent to n=200+.
- The conditional-information (CMI/PID) analysis described in the task brief
  as follow-on work was not started in this session; full state trajectories
  needed for it were saved (`data/protocol_v1/canonical_snapshot.npz` contains
  the complete `z_hist`) so it can be run later without re-simulating.

## 6. Independent replication (partial)

Given this session's time budget, full replication (the task-brief scale of
searching several independent flocks each to the same `k=1`+`k=2`+greedy
depth) was not completed. A reduced check was run instead
(`python/analysis/phase6_replication.py`,
`data/protocol_v1/phase6_replication_partial.json`): the exact frozen
selection rule was applied to two more seeds (3 and 4, chosen as the next two
seeds after the canonical seed=2 in numeric order — not cherry-picked), and
the `k=1` exhaustive single-actuator sweep (50 replicates/bird, same
thresholds) was run on each resulting flock:

| seed | t0 | h0 | \|I0\| | eigengap | max single-actuator mean H*(t0+Tu) | actuators meeting P(success)>=0.5 |
|---|---|---|---|---|---|---|
| 2 (canonical) | 41 | left | 20 | 1.39 | 0.056 | 0 / 80 |
| 3 | 8 | up | 19 | (see json) | 0.134 | 0 / 81 |
| 4 | 5 | left | 20 | (see json) | 0.029 | 0 / 80 |

**The negative `k=1` finding generalizes across all three independently
emergent flocks tested**: in every case the best single external actuator
reaches at most ~13% of the target-heading fraction the task requires (0.8),
and zero single-bird actuators meet the acceptance bar in any of the three
flocks. This is still a small sample (n=3) and only at `k=1` depth — it
supports, but does not by itself prove, that the failure mode is a general
property of this model/parameter regime rather than a quirk of the one
canonical snapshot searched at full (`k<=6`) depth. Extending this replication
to `k=2`+ depth on more independent flocks, and to a formal statement about
*why* single/few dissenting exterior birds cannot overcome an already-formed
~20-bird consensus within 20 steps (a plausible candidate mechanism: the
alignment/collision-avoidance terms in Eq. 4 make a lone or small group of
dissenters locally self-correcting rather than contagious, given `vm=4`
dominates the `ca=2`/`fc=1` terms), is left as follow-on work.

## 7. Failed runs / anomalies (not hidden)

- The heading-encoding bug in section 2 above (full account in
  `PROTOCOL_V1.md` section 1a and `PORT_VALIDATION.md` section 3a).
- No MATLAB/Octave execution was possible in this environment; all upstream
  cross-checks are algebraic/deterministic rather than trajectory-level (see
  PORT_VALIDATION.md section 0).
- The predator/stress-response half of the upstream model (Appendix A.3) was
  not ported (deliberate scope reduction, stated up front in
  `METHODS_AUDIT.md` section 13 and `README.md`, not a late-discovered gap).

## 8. Deliverables index

- `METHODS_AUDIT.md`, `PORT_VALIDATION.md`, `PROTOCOL_V1.md`, this file.
- `python/flock_sim/`: simulator + spectral library (`lattice.py`, `model.py`,
  `active_inference.py`, `simulation.py`, `spectral.py`, `metrics.py`,
  `interventions.py`, `io.py`).
- `python/analysis/`: one script per phase (`baseline_characterization.py`,
  `canonical_snapshot.py`, `phase3_controls.py`, `phase4_5_response_map.py`,
  `phase5_k2_search.py`, `phase5_greedy_k.py`).
- `python/figures/`: figure scripts (`fig1_fig2_baseline.py`,
  `fig3_fig4_response_map.py`, `fig5_8_steering.py`).
- `python/analysis/phase6_replication.py`: partial independent-replication check.
- `tests/`: 28 passing tests, `pytest tests/ -q`.
- `configs/protocol_v1.yaml` + `logs/protocol_v1.sha256`.
- `data/`: raw JSON/NPZ results per phase, superseded runs renamed (not
  deleted) rather than overwritten.
- `figures/`: PNG + PDF outputs, figures 1-8.
