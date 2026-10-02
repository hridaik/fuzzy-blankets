# THRESHOLDS_v2.md — frozen 2026-10-01, after R1 (60 canonical individuals) and before analysing R2/R3
(Recalibrated from the R1 census; protocol v2. `sealed/thresholds_v2.json`.)
- **Reference phenotype:** the empirical adult fixed point of `primary_0000` at the canonical clock (T_dev = 32), bin 512. Classification is relative to it (the template is audit-only). Mean nearest-neighbour spacing 0.880, minimum 0.680.
- **τ_pair = τ_pos = 0.25 × minimum NN spacing of the reference phenotype = 0.170.** Basis: M1's rule (0.25 × spacing) applied to the empirical phenotype instead of the template. Sensitivity at ×0.5 (0.085) and ×2 (0.34): the 100-individual R1 census has 2 classes at ×1 and ×2 (97 + 3) and 3 at ×0.5 (97 + 2 + 1: the two chiral variants of class 1 separate). The class-1 distance to class 0 is 0.411 (> 2τ); the chiral separation is 0.144 (< τ).
- **Took-effect threshold:** max over the on-window (+8 bins) of the RMS-over-cells index-wise position deviation from the matched twin ≥ 0.05.
- **Stationarity (state-based, meaningful on the autonomous system):** per-bin speed = max(‖Δposition‖, ‖Δsecretion‖, ‖Δbeliefs‖) < 1e-6 for all later bins of the run, ≥ 32 bins at the end. **CYCLE2** branch (added after the W pilot, before R1/R2 analysis): lag-2 speed < 1e-6 while lag-1 speed ≥ 1e-6 (period-2 limit cycle of the D-step map). Time to stationarity = first bin of the final streak.
- **τ_bel = 0.9: RETIRED** (never met; max belief 0.46–0.82).
- v1 thresholds (M1 THRESHOLDS.md) are not used for v2 data.
