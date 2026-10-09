# CONTINUATION.md — protocol v2 continuation from a saved state (R0.1, R0.2)

## R0.1 Absolute developmental clock — ESTABLISHED
`s(b) = 1 - exp(-2 b / T_dev)`, `b` = ABSOLUTE bin since the start of development (b = t_off + iY, iY = 1..N within a segment), independent of the number of bins N in a run. Implemented in `oracle/m2a_ramp.m` (mode `'abs'`; `ramp_ref` = T_dev; `t_off` = bins already elapsed). Used by both the process (`m2a_Gg.m`, field gain) and the generative model (`m2a_Mg.m`), exactly as the published `Gg`/`Mg` use `s`. Canonical T_dev = 32 (published schedule: N=32, t=bin/N); secondary T_dev = 512 (M1's census clock). 1 - s < 1e-8 for b ≥ 10·T_dev (b ≥ 320 canonical).

**Diff relative to the published scripts.** Published: `t = iY/nY` (a global set by `spm_ADEM`), `s = 1-exp(-2t)`. v2: `s = 1-exp(-2 (t_off + round(t·N)) / T_dev)`. Nothing else in `Gg`/`Mg`/`morphogenesis` is changed (`oracle/m2a_{Gg,Mg,field,ramp}.m`; legacy v1 mode `'N'` reproduces the published behaviour bit-for-bit, tested).

**Control (R0.1):** T_dev = 512, 512 bins, primary-0 beliefs, state-exporting engine: positions equal M1's census `primary_0000_N512` to **0.0 max abs difference** (all 512 bins); d_target at bin 512 = 0.2872798670202126 = M1's value (difference 0.0; tolerance 1e-9). `data/r0/r0_results.json`.

## R0.2 Continuation — ESTABLISHED (state-exporting engine copy)
`spm_ADEM` cannot export or import its D-step state. Rather than restart (which loses the generalised coordinates), M2a uses **`oracle/spm_ADEM_m2a.m`, a copy of SPM12 `spm_ADEM.m` with five marked edits** (`oracle/spm_ADEM_m2a.diff`, 78 diff lines, no numerical change): (1) read optional `DEM.cont`; (2) restore `qu`, `pu`, action history from it; (3) build the action history `A = [Ahist, qU.a, qu.a]` and index the embeddings with the offsets; (4) optionally take full-horizon noise `Zfull/Wfull` indexed by absolute bin; (5) export `DEM.cont_out` after the last D-step update. This is a patch of the engine the earlier rules call "unmodified"; it is justified by R0.2 and validated below: with no `cont` it is bit-identical to unpatched `spm_ADEM` (N=64 fresh run: 0.0 difference in positions, secretion, beliefs).

### Everything the D-step reads (enumerated from `spm_ADEM.m`)
| Quantity | Role | Carried? |
|---|---|---|
| `qu.x{1..n}` | generalised coordinates (orders 0..2) of model hidden states | yes (no hidden states in this model; empty) |
| `qu.v{1..d}` | generalised coordinates (orders 0..1) of model causes = beliefs (64-vector) | yes |
| `qu.a{1}` | action (positions 16 + secretion 32) | yes |
| `pu.v{1..n}`, `pu.x{1..n}` | process outputs / hidden states, generalised | yes (recomputed each bin from `a` and the process, so not rate-limiting; see ablation) |
| `Ahist` | the previous bin's action column. `pu.a = embed(A, n, iY)` uses the window {iY-1, iY, iY} of the action history, so the action's generalised coordinates (its velocity) depend on the previous bin | yes (1 column) |
| `qu.y`, `qu.u`, `pu.z`, `pu.w` | recomputed each bin from `pu` and the noise / input embeddings | no (recomputed) |
| absolute bin offset `b0` | the clock (`s(b)`), event onsets, noise indexing | yes (`t_off`, `cont.b0`) |
| noise `Z`,`W` (when enabled) | one realisation over the whole horizon; segments index it at `iY+b0` (the embedding looks one bin ahead) | yes (`Zfull`) |
| `qu.c`, `pu.c`, `qE`, `qC`, free energy | outputs, not inputs | no |
| hyperparameters `qh`, parameters `qp` | `np = nh = 0` here: no E/M-steps (`nE = 1`) | n/a |
`t` (global) is reset each bin from `iY/nY` and used only through the ramp functions.

### Positive controls (tolerance declared: max abs deviation ≤ 1e-9 in positions, secretion, beliefs, prediction errors, free energy)
(a) **Split runs equal the single run.** Primary-0 beliefs, T_dev = 32, single run of 1100 bins vs two segments split at b0 = 64, 300, 320, 1000: max abs deviation **0.0** for positions, secretion, v_expect, pred_err_1, pred_err_2, free_energy_J at every split. Also T_dev = 512 split at b0 = 300 (speed there is 6.3e-4, ramp-driven): 0.0.
(b) **Null continuation stays at the fixed point.** From b = 320 (T_dev = 32), 780 further bins, no intervention: max drift 0.0 in positions, secretion and beliefs; speed is exactly 0.0 from b ≈ 300 (speed 3.0e-5 at b=100, 5.8e-8 at b=200).
Because the adult fixed point is exact, controls at 300/320/1000 cannot show which quantity matters. **Sensitivity ablations at a moving state** (split at b0 = 64, 40 bins, one carried quantity removed, `data/r0/abl64_*.mat`): without `Ahist` the trajectory deviates by up to 4.2e-5 (from bin 1); without the higher-order generalised coordinates of beliefs (`qu_hi`) 4.2e-6; replacing `qu.a` by the previous action 2.0e-4; a 1e-6 perturbation of the order-0 belief is detectable (9e-12, bin 1); zeroing `pu` has no effect (it is recomputed). So the test is sensitive to the action history and to the higher-order coordinates, and both are carried.
No quantity responsible for a failure: none failed.

## Limits (PROVISIONAL)
Split-run equality was checked for one individual (primary 0) and the noise-free engine. With noise (R0.3) the continuation shares one horizon-long noise realisation; a split-vs-single control with noise is part of the R4 tests (NOT YET DONE at the time of writing this section).

## Addendum (written after the D-stage) — later engine patches; ESTABLISHED
The five edits above were extended after this section was first written. `oracle/spm_ADEM_m2a.diff` is now **121 lines** (it was 78) and the engine identifier recorded in sidecars changed accordingly (the 'engine' field of early v2 sidecars carries the earlier hash; every later one the current hash; the numerical behaviour is the same, shown below). Added: (6) an optional **sensory-precision schedule** `DEM.prec` (global multiplier of the sensory block of the precision, with the per-order block indices of `V1`; matches a static `V1` override to 4e-12; used for the Pio-Lopez-style family and D3); (7) an optional **sub-step** `M(1).E.dt` that changes the embedding spacing and the D-step (used only by D2, which showed it is not a convergent refinement — SKELETON.md); (8) `m2a_mix.m` (state interpolation for D5) and `m2a_jac.m` (one-bin map Jacobian) as separate scripts that do not alter the engine.
**Verified (tests/test_engine_equivalence.py, run in this stage, passes): the patched engine with no continuation equals unmodified SPM12 `spm_ADEM` bit for bit (24 bins: positions and beliefs identical); a 12 + 12 bin split run equals the 24-bin single run bit for bit; an explicit `dt = 1` equals the default.** `m2a_mix(a, a', λ = 0)` followed by continuation equals continuing from `a` bit for bit (checked in D5).
