# FAITHFULNESS.md — T1.2 / T1.4: is the continuous-time engine faithful to the published (Octave `spm_ADEM`) model?

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Code: `code/t12_convergence.py`, `t14_census.py`, `t14_cde.py`, `calib_*.py`; data: `data/t12_convergence.json`, `t14_census.json`, `t14_cde.json`, `calib_grid.json`, `oracle_targets.json`. Oracle = the stored Octave traces of `m2a_audit_and_library/data/v2/census` (no Octave run was needed; Octave 10.3 is available in env `octave-dem`).

## GATE T1: PASSED (T1.2 converges; T1.4(a) d_pair = 8.7e-5 < 0.01)

## T1.2 integrator — ESTABLISHED
RK4 order 4.09 / 3.96 / 4.07 over successive halvings (dt 0.02 → 0.00125; error vs finest at T = 40: 2.6e-10 at 0.02, 1.5e-11 at 0.01); adult fixed point identical to 4e-14 for dt = 0.02, 0.01, 0.005. **Stability limit** dt < 2.78/ρ = 0.037 (ρ = 75 at the adult state): dt = 0.04 converges over the transient but diverges at the adult state (drift residual 2). The stochastic scheme's check is in NOISE_AND_CRN.md.

## T1.3 time calibration — ESTABLISHED (fit)
See ENGINE_SPEC.md §4: `k_mu = 1.4`, `k_a = 1.2`. Oracle targets on the same definitions: merging 7.85 (engine 7.68), t(mean max belief = 0.5) 10 (11), t(0.7) 21 (22).

## T1.4(a) fixed points — ESTABLISHED
Engine adult state from the oracle's own initial beliefs vs the oracle reference phenotype (permutation-invariant, type-constrained, positional channel ON): **d_pair = 8.7e-5** for all 50 primary draws that reach class 0 (declared threshold 0.01). Drift residual of the engine state 1e-13. Required deviation D0 (action-side weights, see ENGINE_SPEC.md); without it the oracle state is not stationary under the task's literal F (residual 0.53).

## T1.4(b) census from the oracle's own initial beliefs — ESTABLISHED (one realisation per draw)
| draws | engine class 0 / class 1 / other | oracle class 0 / 1 | per-draw agreement |
|---|---|---|---|
| 50 primary (randn/8) | 50 / 0 / 0 | 50 / 0 | 50/50 |
| 50 secondary (std e²) | 48 / 1 / 1 | 47 / 3 | 48/50 (secondary_0005: oracle class 1, engine another shape; secondary_0013: oracle class 1, engine class 0; secondary_0012 agrees: class 1) |
Class = distance to the oracle's own class-0 / class-1 end states < 0.17. The engine has a rare second attractor too (2/50 secondary draws land away from class 0, one on class 1 and one on a third shape not seen in the oracle), at a similar rate (oracle 3/50). The frequencies are consistent with each other (Wilson intervals overlap); per-draw agreement is not perfect because the basin boundaries depend on the time-scale ratio `k_a/k_mu` and on the scheme. Also: with `(k_mu,k_a) = (1,1)` or `(0.3,1)` the same initial beliefs end in a different stationary state 0.05 from class 0 — basin structure is not a fixed-point property.

## T1.4(c) sustained double-head (DH) distortion — ESTABLISHED as observation, PROVISIONAL as interpretation
Sensed long-axis position `s1 = (1-ε)x1 + ε x1²` (the m2a DH_ε family), applied as a *step* to the class-0 adult (not a quasi-static sweep), ε ∈ {0.1, 0.2, 0.3, 0.35, 0.4, 0.5, 0.7, 1.0}; DT (`-ε x²`) likewise. **Every case reaches a stable fixed point** (Jacobian max Re < 0; DT ε = 0.3 had drift 2e-8 and was still creeping with rate −0.017). The oracle shows period-2 cycles at DH ε = 0.35 and 1.0 and DT ε = 0.3 (amplitudes 0.25–0.62 in its up/down sweeps). The DH ε = 1 result is dt-converged (dt = 0.005, 0.002, 0.001 identical to 1e-13). **Evidence — not proof — that the oracle's period-2 cycle is an artefact of SPM's one-bin discretisation (eigenvalue −1.54 of its one-bin map; D2 in SKELETON.md).** Caveats: step onset vs sweep protocol; one body; the engine omits generalised coordinates and the action delay, either of which could be the cause.

## T1.4(d) linearisation at the adult fixed point — ESTABLISHED
| | engine (continuous rates) | oracle SKELETON D1 (one-bin map) |
|---|---|---|
| class 0 slowest rate | −0.125 per time (relaxation 8.0) | −0.127 per bin (7.9) |
| class 0 next rates | −0.180, −0.182, −0.190 | |μ| = 0.829, 0.827, 0.817 → rates −0.188, −0.190, −0.202 |
| class-0 slow-mode weight in belief block | 99–100 % | 96–100 % |
| class 1 slowest | −0.072 (13.9) | −0.066 (15.2) |
| class 1 belief weight (slowest) | 95 % | 88 % |
| unstable modes | 0 / 0 | 0 / 0 |
Expected differences from removing generalised coordinates: none large; the engine's class-1 slowest mode is 9 % faster. The sustained-DH unstable flip (μ = −1.54) has no counterpart: the engine's DH states are stable.

## T1.4(e) speed — ESTABLISHED (CPU, 8 cores, one 500-time-unit run = 25 000 RK4 steps at dt = 0.02)
| n | engine single | engine vmap-batched (32) | Octave (m2a, 320 bins ≈ 152 s per run, one core) |
|---|---|---|---|
| 8 | 0.60 s → 5 990 runs/h | 8 870 runs/h | ≈ 24 runs/h per core (≈ 190/h on 8 cores, assumed linear) |
| 24 | 2.4 s → 1 520 runs/h | 1 850 runs/h | not run |
| 48 | 14.5 s → 250 runs/h | 960 runs/h | not run |
Batching on CPU gains little for small n; process-level parallelism (`code/par.py`) is what scales. Testbed bodies need a smaller dt (stiffness grows with κ-overlap and precision): 24-cell bodies run at dt 0.005–0.02, i.e. 1–4× the cost above.
