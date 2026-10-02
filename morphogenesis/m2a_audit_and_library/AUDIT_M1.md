# AUDIT_M1.md — Part 0: independent audit of Stage M1

Run 2026-10-01. Engine for every new run: m0c fallback engine (unmodified SPM12 `spm_ADEM`, Octave 10.3.0), plus the 0.2 hand-written script (`oracle/direct_morph.m`) and M2a's own driver (`oracle/m2a_run.m`, validated bit-exact against the fallback engine). Engine config hash (spm_ADEM + m0b oracle files): `1e351f1b3a7f0ef9`. Labels: ESTABLISHED / PROVISIONAL / NOT DONE.

## GATE: **FAIL — STOP after Part 0**

One injection control fails: M1's **AN ("anomalous cell") runs never applied a single-cell perturbation**. They are bit-for-bit copies of the DH runs. Everything else passes. Per the task's gate rule, Parts 1–4 were not started. Corrected re-run proposed at the end.

| Check | Verdict |
|---|---|
| 0.1a initial beliefs injected (10 individuals) | **PASS** |
| 0.1a designed control (6×permutation, 3 perms) | **PASS** (3/3 role maps = P) |
| 0.1b kicks took effect (25 runs, 5 per type) | **PASS** (measured = intended, 25/25) |
| 0.1c DH perturbation took effect (60 runs) | **PASS** (60/60) |
| 0.1c DT perturbation took effect (60 runs) | **PASS** (60/60) |
| 0.1c **AN** perturbation (60 runs) | **FAIL** — identical to DH; single-cell anomaly never tested |
| 0.1c sham took effect (60 runs) | **PASS** (60/60) |
| 0.2 engine cross-check (3 individuals) | **PASS** — bit-identical (max abs difference 0.0) |
| M1 headline 1: one end-state shape, d_target 0.2873 | **CONFIRMED** (with the reinterpretation in 0.3) |
| M1 headline 2: 100/100 kicks return | **CONFIRMED as a statement about M1's restart protocol** (caveats below) |
| M1 headline 3: 180/180 withdrawal reverted | **CONFIRMED at shape level for DH/DT/sham; NOT valid for AN; role assignment is NOT restored** |

## 0.1 Positive controls on injection

### 0.1a Initial beliefs — ESTABLISHED: injected
Ten individuals (primary 0–4, secondary 0–4; `data/part0/offline_1a.json`). Initial draws were regenerated (Octave seed draw for primary; numpy for secondary).
- Bin-0 position, secretion and belief equal the values computed from the draw to **0.0 max abs difference** in all 10. Bin 0 is the injected state; bin 1 has moved (position change up to 0.014–0.023 primary, 0.09–0.14 secondary).
- Bin-0 states differ across individuals as their draws differ: pairwise permutation-invariant bin-0 distance, min 0.027, median 0.90, max 1.54.
- Primary bin-0 position norm 0.16–0.22, secondary 2.6–5.0 (draw std 0.12–0.13 vs 6.8–7.7).
- **Designed control** (v0 = 6×permutation, 3 permutations: identity, reversal, a seeded random one; `data/part0/perms.json`): final Hungarian role map **equals the designed P in 3/3**, and the argmax-belief map equals P too. d_target = 0.28728 in all three, i.e. the same shape as the census. The role assignment is therefore a function of the initial beliefs, as the model predicts.

### 0.1b Kicks — ESTABLISHED: each kick took effect
Five seeded-random runs per kick type (`offline_1b.json`). Deviation of bin 0 of the kicked run from the pre-kick converged state equals the intended kick exactly:

| Kick | intended = measured |
|---|---|
| K1 σ0.5 (position) | Δx 1.91–2.62 (norm over 16 coords), Δs = Δv = 0 |
| K1 σ1.5 (position) | Δx 5.80–7.33, Δs = Δv = 0 |
| K2 (secretion → mean) | Δs 1.6686, Δx = Δv = 0 |
| K3 (beliefs reset) | Δv 8.37–8.83, Δx = Δs = 0 |
| K4 (one cell, 3 spacings) | Δx 3.2439, Δs = Δv = 0 |

**Design caveats (ESTABLISHED by code reading and data):**
1. A "kick" is a **restart**: `dem_setup_from_state` starts a new `spm_ADEM` run in which the developmental ramp restarts at s≈0 (t = bin/N from 1/512). So post-kick relaxation includes re-development, not just recovery from the kick.
2. K1/K2/K4 leave the beliefs intact; only K3 touches them. Return of position/secretion kicks to a belief-determined position is close to guaranteed.
3. All 20 kicked individuals start from the same converged shape up to cell permutation, so across individuals the kick experiment has one distinct base state (the K2 deviation is 1.6686 for all individuals). The 100 kicks are 5 conditions × (1 state × 20 kick seeds or relabellings), not 20 independent bodies.

### 0.1c Perturbations — mixed: DH/DT took effect; AN did not do what it claims
M1 never stored an unperturbed twin at the withdrawal horizon (it compared end-states with the N=512 census). I ran **40 matched unperturbed twins** (20 individuals × FRESH and ADULT-restart, N=1024, same M1 pipeline with `kind='none'`; `data/twins/`). Declared before analysis: a perturbation "took effect" if the maximum, over the on-window (+8 bins), of the RMS over cells of the index-wise position deviation from the matched twin is ≥ 0.05 (0.2×tau_pos).

| Perturbation × timing | n | took effect | window max-deviation (min / median / max) | sustained twin vs unperturbed, mean d_pair | end d_pair to twin (max) | end role assignment differs from twin* |
|---|---|---|---|---|---|---|
| DH DEV-SHORT | 20 | 20 | 0.354 / 0.402 / 0.453 | 0.695 | 1.1e-12 | 12 |
| DH DEV-LONG | 20 | 20 | 0.615 / 0.768 / 0.991 | 0.695 | 1.3e-12 | 19 |
| DH ADULT | 20 | 20 | 0.703 / 0.703 / 0.703 | 0.695 | 1.4e-12 | 20 |
| DT DEV-SHORT | 20 | 20 | 0.320 / 0.375 / 0.574 | 0.433 | 1.1e-12 | 13 |
| DT DEV-LONG | 20 | 20 | 0.547 / 0.683 / 1.128 | 0.433 | 1.1e-12 | 20 |
| DT ADULT | 20 | 20 | 0.570 / 0.570 / 0.570 | 0.433 | 1.5e-12 | 20 |
| **AN** (all three timings) | 60 | 60* | identical to DH | 0.695 | identical to DH | identical to DH |
| Sham (3 timings) | 60 | 60 | 0.61–1.4 (medians 1.03 / 1.37 / 0.96) | — | 1.1e-12 | 58 |

All 60 sustained twins (DH/DT/AN, 20 individuals each) also differ from the unperturbed twin: d_pair 0.43–0.70 ≥ tau_pair, max deviation ≥ 0.58.
*"Took effect" for AN means the all-cell DH perturbation took effect.

**Findings (ESTABLISHED):**
- **AN defect.** `run_withdrawal.py` records the intended AN cell (`an_cell`) but passes `'cells', []` to Octave for every kind, so `kuchling_head` is applied to all cells. AN ≡ DH to 0.0 in positions for every individual and timing (checked all 80 AN/DH pairs; `tests/test_part0_findings.py`). M1's "single anomalous cell" result does not exist; the 60 AN runs are 60 more DH runs. This also means `WITHDRAWAL.md`'s "no difference between the population-wide distortions and the single-cell anomaly" is vacuous.
- **Shape reversion is real, and not a failure to perturb.** For DH, DT and sham, every perturbation produced a large transient deviation (≥ 0.32), and the end-state returned to the matched unperturbed twin's shape to d_pair ≤ 1.5e-12. 120/120 DH+DT and 60/60 sham.
- **The role assignment is not restored.** Compared index-wise with the matched twin, DH 51/60 (Wilson 95% [0.74, 0.92]), DT 53/60 ([0.78, 0.94]), all 180 runs counting AN as DH 155/180 ([0.80, 0.90]), and sham 58/60 ([0.89, 0.99]) end with a different cell-to-position assignment, even though the permutation-invariant d_pair is ~1e-12. M1's d_pair is blind to this by construction (`OPEN_QUESTIONS.md` M1 item 5 flagged it as low priority). Sham relabels as often as the real perturbations, so the relabelling is not specific to Kuchling's distortion. Baselines: an unperturbed N=1024 fresh run vs the N=512 census relabels in 9/20 individuals (so assignment is fragile to the ramp schedule alone), while an unperturbed ADULT restart vs the census relabels in 0/20. **Consequence:** "no durable effect" is true for shape and false for which cell ends up where. Any later claim about durable change must say which.
- **ADULT replicates are one experiment.** DH-ADULT window max is 0.703 for all 20 individuals (DT: 0.570), because all converged states are the same shape up to permutation.

## 0.2 Engine cross-check — PASS, ESTABLISHED
`oracle/direct_morph.m` re-types the setup of SPM12 `DEM_morphogenesis.m` and calls `spm_ADEM` directly (no m0b/m0c/m1 oracle code, no fallback engine). Primary 0, primary 1, secondary 0, N=512, same initial beliefs, noise seed reset before `spm_ADEM` as in M1. Max abs difference from M1's saved trajectories: positions 0.0, secretion 0.0, beliefs 0.0 for all three (declared tolerance 1e-9). Recovered initial beliefs equal the draws to 0.0.

**Related, ESTABLISHED:** the process noise is **identically zero**. `G(1).V = exp(16)` takes the `norm(P,1) >= exp(16)` branch of `spm_DEM_z`, which returns sparse zeros. Runs with a different noise seed (1001, 1002) and the same beliefs are bit-identical to the census run (max abs 0.0). So M1's "noise floor 3.35e-4" never operates; the engine is deterministic, and an individual is defined entirely by its initial beliefs (and by the interventions applied).

## 0.3 Why the exactness (d_target = 0.2873, stationarity at 246)

### 0.3a Merging — ESTABLISHED (`figures/part0_merge_and_stationarity.png`)
Ten individuals (6 primary, 4 secondary), all 45 pairs, permutation-invariant geometric distance at every bin. The maximum pairwise distance first stays below 0.25 at bin 20, 0.125 at 77, 0.01 at 108, 1e-3 at 126, 1e-6 at 185, 1e-9 at 245, and sits at a ~1.8e-12 numerical floor from about bin 300. Between bins 128–224 the decay is log-linear with rate 0.114/bin (time constant 8.8 bins). Starting from a spread of ~1.4 (secondary), 27 e-foldings take ~240 bins, so the exactness is **genuine strong contraction**, not an injection failure.

### 0.3b Stationarity is time-driven — ESTABLISHED
- The per-bin speed at the 1e-3 crossing (bin 246) is the same to 9 digits across all individuals, because they have already merged; the crossing is a property of the single shared trajectory.
- That trajectory is slaved to the developmental ramp: speed/(ds/dbin) falls only from 1.2 (bin 200) to 0.44 (bin 500); the speed stays comparable to the ramp's own rate for the whole run.
- **Declared alternative criterion** (state-based): bin after which the state stays within 1e-3 of the run's own final state. Result: bin 507 for all ten, i.e. it tracks ramp drift until the end of the run (also time-driven; it only tells us the ramp is still moving).
- **Decisive control (frozen ramp):** run with the ramp frozen (`s` const) so the system is autonomous. At s = 0.617 (the value at bin 246): M1's criterion fires at bin **35, 36** (primary 0, 1) and **79** (secondary 0), now individual-dependent and state-driven; the speed falls to exactly 0.0 by bin ~150; end states agree across individuals to 1.3e-8 and 3.9e-10. At s = 0.865 (primary 0): stationary at bin 30, d_target = 0.2872 = the census value.
- **Reading:** M1's census end-state is the fixed point of the dynamics at the *end-of-run* ramp value s(t=1) = 0.865, reached by quasi-static tracking. The fixed point itself moves with s: d_target = 0.3207 at s = 0.617, 0.2872 at s = 0.865. "Bin 246" means "the ramp-tracking speed has dropped under 1e-3"; it is not a convergence time.

### 0.3c Longer horizons — ESTABLISHED
Three individuals (primary 0, 1, secondary 0), two variants. d_target:

| Variant | bin 246 | bin 512 | bin 1024 | bin 2048 |
|---|---|---|---|---|
| (A) N=2048 (ramp rescaled, as M1's cascade would run it) | 0.5401 | 0.3925 | 0.3179 | 0.2873 |
| (B) N=512 ramp schedule held in absolute bins, run to 2048 | 0.3209 | **0.2873** | 0.2783 | 0.2771 |

Individuals agree to 5 digits within each variant. (B) at bin 512 reproduces M1's end-state exactly; beyond it d_target keeps falling slowly as the ramp saturates (s → 1), to 0.277 at 2048. The near-miss therefore **persists** (0.277 vs tau_pos 0.25 per cell, and the per-cell worst case remains well above threshold), but 0.2873 is a function of the ramp endpoint, not an asymptote. In (A) stationarity is at bin 508 for all three, again determined by the ramp.

## 0.4 Role maps — ESTABLISHED
250 individuals give **248 distinct role maps** (type-preferring Hungarian map cell→template slot); two maps occur twice, the rest once. Under uniform random permutations of 8 (8! = 40320) the expected number of coinciding pairs is 0.77; observing 2 is unremarkable (P ≥ 2 ≈ 0.18). So the role map behaves like a random permutation determined by the draw (0.1a designed control confirms the mapping from initial beliefs to roles). d_target range over 250: 0.287279867020–0.287279867021.

## 0.5 Mechanism of the near-miss (hidden tier; audit only) — ESTABLISHED
At the end state, every cell's maximum belief is **0.72–0.78** (never > 0.78; the frozen threshold tau_bel = 0.9 is never met). For primary 0/1 and secondary 0/1 (`offline_5.json`):
- distance from final position to the **belief-weighted** predicted position (template positions weighted by the cell's softmax beliefs): 0.047–0.100;
- distance to the **argmax** target: 0.009–0.615 (multiset {0.009, 0.132, 0.132, 0.296, 0.296, 0.335, 0.484, 0.615}).
The belief-weighted prediction is 1.3–13× closer for 7 of 8 cells (the eighth cell, already on target, is closer to its argmax). **The near-miss is explained mainly by unconcentrated beliefs**: each cell sits near the belief-weighted average of template positions, not at its argmax target. The residual 0.05–0.10 is not explained by beliefs alone (sensory-field coupling not analysed here: PROVISIONAL). Belief concentration continues to grow slowly with the ramp (0.3c-B), but even at bin 2048 d_target is 0.277.

## 0.6 Terminology
From here on the census end-state is the **REFERENCE PHENOTYPE**: the model's realised normal form, an empirical attractor *at the end-of-run ramp value* (0.3b). The template is used only for audit.

## Implications and what changes for later stages
1. Shape monostability is solid; **cell-role assignment is a separate, perturbation-sensitive, durable hidden variable**, and M1's metric cannot see it. Part 1's outcome classes need a role-relabelling flag.
2. The system is **non-autonomous** (ramp). "Return to stationarity" and "S_FP" are ramp-dependent. Proposal for Part 2: define S_FP on an autonomous system by freezing the ramp at s = 0.865 (a true fixed point, speed exactly 0), and S_DEV by the absolute-bin ramp. Not applied; needs your decision.
3. The engine has **no stochasticity**; all between-individual variation is initial beliefs. A blind analyst gets deterministic, merged trajectories with relabelling as the only residual individuality.
4. Python-int pitfall found while building the toolkit: `scipy.io.savemat` writes ints as int64 and Octave integer arithmetic silently rounded the ramp. Fixed and regression-tested (`tests/test_toolkit.py`). It cannot have affected M1, which passed numbers as Octave literals.

## Proposed corrected re-run (needs your approval)
1. Re-run AN with `cells = an_cell+1`: 60 withdrawal runs (N=1024, ~550 s each) + 20 sustained twins (N=512, ~237 s), 20 individuals × 3 timings; ≈ 37,700 core-s ≈ **1.3 h wall at 8 cores**. The existing matched unperturbed twins are reused.
2. Add role-relabelling (index-wise, vs matched twin) as a reported outcome alongside REVERTED/PERSISTED/NOVEL, for all M1 runs (no new compute; data are in `offline_1c.json`).
3. Decide the ramp protocol for Parts 1–2 (frozen s = 0.865 vs absolute-bin ramp) and whether to keep zero process noise.
After that, Part 1 onward can start; COMPUTE_PLAN.md has a provisional (unpiloted) projection.
