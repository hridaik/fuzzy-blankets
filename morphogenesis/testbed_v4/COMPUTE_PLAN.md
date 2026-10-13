# COMPUTE_PLAN.md — testbed v4 (budget 18 h wall-clock; 8 CPU cores; JAX float64; no GPU). Written before any measurement.

Measured speed (bench, v4 engine, 24 cells): ~3.7k RK4 steps/s/core = 46 tu/s/core (dt = 0.0125). 8 cores ≈ 370 tu/s. Declared constants: `code/dish.py` (θ = 30° (fallback 20° taken after V1: max D_k = 6.304 at places 14, 15, α(0.4) = 4.759e-3, α(0.8) = 9.518e-3), r = 0.05, σ_h = 0.4, g = 4rκ_g, g_min = 0.3, α(φ_max) = φ_max g_min/(β_E max_k D_k)). Frozen BEFORE scoring: switch scoring (target state + tail-angle sign flipped + within 20 % of the target-state reference angle + ORGANISM INTACT), release 20/g, discs r = 1.5, ramp = min(5, dur/4), the neighbour-Jaccard threshold is calibrated in C2 then frozen (`data/intact_threshold.json`).
Interpretation declared up front: "target template's angle" = the settled tail angle of the target state in that dish (nominal ±30° is also reported; they differ because ρ* < 1 gives a shape ∝ 2ρ−1 and ρ* depends on g).

| # | batch | question → decision | est. |
|---|---|---|---|
| C0 | V0: Jacobian block, clamp, v3 memory predictions, CRN twins, sham, v3 tests | engine as specified? | 30 min |
| C1 | V1: 16 seeded starts × 2 clamps; 5 × 5,000 tu durability ×2; 11-value sweep | shapes hold? θ fallback? | 1 h |
| C2 | calibrate ORGANISM INTACT neighbour threshold (natural + clean switch runs) | freeze | 40 min |
| C3 | V2: 3 variants: (a)(b) l*, (c) bath sweep, (d) 10 seeds × 10,000 tu × 2 states × 3 variants, (e) isolated cell | feedback dial as predicted? | 2 h |
| C4 | V3: bisect 5 patterns × 2 durations × 2 directions × 3 variants × 3 dishes (+noise) | switch with shape change | 3 h |
| C5 | V4: γ_0 bisection; safe-window map (4 durations × 2 centres) | damage calibration | 2 h |
| C6 | V5: 40 dishes × 4 centres × 4 durations, threshold + damage onset | adaptivity gap | 3 h (≤2 widenings) |
| C7 | V6 identity events | | 1 h |
| C8 | P1 package, P2 live env, P3 viewer, docs | | 3.5 h |

## Log
- C0 V0: tests/test_v4.py 7 pass (+ v3 14, v2 5). Isolated cell with α>0 relaxes at 2r (0.096–0.103) to a biased fixed point (l∞ = −0.30 / −0.62): a self-field term of the dial, not tiny (see FEEDBACK.md).
- C1 V1 at θ = 30: completion 14/16 at ρ = 1 and ρ = 0 (seeds 5 and 12 fail: 2 components / incomplete) → declared fallback θ = 20: 16/16 and 16/16, durable 5×5000 tu, 11-value sweep monotone. 330 s wall each. θ = 20 adopted globally; α recomputed (max D_k = 6.304 at places 14/15): α(0.4) = 4.759e-3, α(0.8) = 9.518e-3.
- C3 V2 (b) l* done (18 s); (c) bath + (d) durability launched.
- C3 V2 done: (b) 18 s; (c) bath 3 variants 6 min; (d) durability 60 runs × 10,000 tu: 0 switches, 48 min wall (8 workers).
- C4 V3: prelim bisection 180 conditions 13 min; τ_J calibration (first frame-wise version gave τ = 0.9826, i.e. ~1 % of natural frames fail — rejected as statistic; replaced by window-minimum statistic, 576 natural 330-tu windows, 13 min) → τ_J = 0.9332 frozen; final bisection 180 conditions 13 min; noise 1,080 trials 17 min.
- C5 V4: γ grid 8 values 6 min (χ = γ u_d = 3.68 ± 4 %); γ_0 = 1.239; verification 3 min (u_d = 3.02 vs target 2.97); window map 8 points 15 min.
- C6 V5 level 0: thresholds (640 bisections) → χ table (5 κ_g × 16 grid points, exact onset) → gap.
- C6 V5 (wall clock): level-0 thresholds 640 bisections 41 min; χ table 80 exact onset searches 2 h 15 min (shared CPU with V6); level 1 and 2 (middle disc only: 160 thresholds + 28/32 χ searches each) ≈ 1 h 20 min each; held-out validation 16 exact searches 12 min. **Gate V5 failed at level 0, 1 and 2 (best fixed policy 100 %): stop.**
- C7 V6 events (replacement, extrusion, serial, cut, fusion): ≈ 1 h 40 min wall at low priority behind V5.
- C8 P1: raw runs (damage 18 triplets 7.5 min; switch 180 runs 22 min; stress 36 triplets 26 min; natural 32 × 3,000 tu 20 min) ≈ 1 h 20 min, rendering 374 runs 35 min (9.5 GB), leak check, tests; P2 live tests 160 s; P3 viewer pages + headless screenshots ≈ 10 min.
- Total wall clock to completion ≈ 8 h of the 18 h budget (the 8 cores were shared between concurrent batches for most of the V5 and package work).
