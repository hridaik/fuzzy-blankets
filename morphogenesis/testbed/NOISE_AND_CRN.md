# NOISE_AND_CRN.md — T2e operating noise, common random numbers, natural ensemble

Code `code/noise_crn.py`; data `data/noise_fluct.json`, `data/crn.json`, `data/natural/`. Testbed bodies = relational (positional OFF), compact 24-cell, operating point of TESTBED_SPEC.md; noise additive on `x` and `c` (`σ_x = σ_c = σ`), none on beliefs.

## Operating noise — ESTABLISHED
Criterion (declared before measuring): RMS positional fluctuation (over cells and coordinates, time-std in the body frame after per-frame rigid alignment, 300 time units after a 100-unit burn-in, 3 seeds) ≈ 3 % of the nearest-neighbour spacing (0.9), AND the body stays organisationally complete (type-constrained rigid distance to the template < 0.4 at every sampled time). 
| σ | RMS / NN spacing | max distance to template over time |
|---|---|---|
| 0.005 | 0.9 % | 0.019 |
| 0.01 | 1.8 % | 0.036 |
| **0.02** | **3.5 %** | 0.069 |
| 0.04 | 6.8 % | 0.126 |
| 0.08 | 14.2 % | 0.269 |
**Chosen σ = 0.02** (comparable to the vanilla NOISE-L2 level, 2.9 %). All levels stay complete (< 0.4). Body A only was scanned (3 seeds each): PROVISIONAL for B and the chiral body (B itself is not stable, see MEMORY_CALIBRATION.md).

## CRN verification — ESTABLISHED
Noise is a counter-based stream: increment of cell i at absolute step k = `normal(fold_in(fold_in(key,k),i))·sqrt(dt)`; twins share `key` and `dt`; an intervention consumes no random numbers. Test (σ = 0.02, disc pulse on 6 cells, t_on = 50, t_off = 60, horizon 100): state just before t_on: max |twin₁ − twin₂| = **4.4e-15** (floating-point, the compiled graph differs by the extra pulse branch); sham (amplitude 0) vs no-window run at t = 100: **6.2e-15**; pulse vs no pulse at t = 100: **19.3** (diverged through the intervention only). Also in `tests/test_engine.py`.

## Stochastic integrator
RK4 drift + additive noise increment (strong order 1 for additive noise). A *coupled-noise strong-convergence* test was NOT DONE (the per-step i.i.d. streams cannot be coarsened); only the stationary fluctuation level was seen to be stable across the dt used. NOT DONE: weak/strong order measurement.

## Natural ensemble — ESTABLISHED (as data), calibration use NOT DONE
`data/natural/manifest.json`: 54 unperturbed runs at σ = 0.02: kinds A, B, chiral; per kind 12 TRAIN (`*_train_NN`) + 6 VALIDATION (`*_val_NN`, disjoint seeds); each 300 time units after a 100-unit burn-in, frames every 5 time units (60 frames), exported in the two-tier layout of GROUND_TRUTH_EXPORTS.md (19 MB). **Caveat: kind B members are NOT natural bodies of a stable plan** — plan B is not an attractor (MEMORY_CALIBRATION.md): the B files record a body that is disintegrating or in a defective state. Do not use them as a "plan B" reference. A and chiral members are stationary organised bodies (seeded start, jitter 0.3).
Decorrelation time: slowest belief rates are ~1e-4–1e-5 (saturated softmax, prior e^-10), so belief-block quantities do not decorrelate within the 300-unit runs; positions decorrelate in ≈ 1/k_a·O(10) time units. For any future information-theoretic estimator (BRIDGE M1/M2) the sample size is therefore limited by the number of independent members (12 per kind), not by run length. NOT DONE: measuring the autocorrelation time.
