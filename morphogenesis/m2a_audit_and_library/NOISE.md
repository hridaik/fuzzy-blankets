# NOISE.md — noise extension (flagged; never mixed with canonical data)

Mechanism and levels: PROTOCOL_V2.md. Levels NOISE-L1/L2/L3 = `G(1).V` of exp(10.6) / exp(8.4) / exp(6.0), Gaussian smoothness 1 bin, one realisation over the horizon (segments share it; split-vs-single control 0.0; reduction control exp(16) = canonical bit-identical). Pilot-measured adult RMS positional fluctuation: 0.97–0.98%, 2.92–2.95%, 9.69–9.81% (and 8.6–8.7e-2 absolute in the 6000-bin runs) of the mean NN spacing 0.880; the long runs measured 0.0086, 0.026, 0.086 (0.98%, 2.9%, 9.8%).

## Long adult runs (4 individuals × 6000 bins × 3 levels) — ESTABLISHED
Spontaneous role switches: 0 at every level (0 / 24,000 bins per level; rate < 0.154 per 1000 bins, exact Poisson 95% upper bound). Shape-class transitions: 0. At L3 the instantaneous d_pair to the reference exceeds τ = 0.17 in 28 of 4800 samples (max 0.193) — shape fluctuation well below the class distance 0.411. Table in REANALYSIS.md (c).

## Reduced R2 (ADULT, 10 individuals × 3 levels, DH and SHAM_DH, matched noisy twin) — ESTABLISHED
See REANALYSIS.md (c): DH relabels 10/10, 10/10, 9/10 (L1–L3) vs 0/20 noise-free; SHAM_DH relabels 8/10, 7/10, 9/10 and reaches class 1 in 3/30 runs; DH shape REVERTED in 30/30. **The turnover baseline that intervention-induced relabelling must exceed is < 0.15 per 1000 bins (zero observed), so the observed relabelling is intervention-induced.** The noise-free DH-ADULT "no relabelling" does not survive 1% noise.
Limits: one noise realisation per (individual, level); fluctuation statistics are over 4 individuals that are one mature state up to relabelling.
