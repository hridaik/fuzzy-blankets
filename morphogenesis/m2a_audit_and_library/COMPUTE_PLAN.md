# COMPUTE_PLAN.md — protocol v2 (pilot-timed; supersedes the provisional v1-era plan)

Machine: 8 cores, Octave 10.3.0, one Octave process per core. **Measured per-bin cost (n=8 cells): 0.44–0.50 s/bin** (R0: single 1100-bin run 528 s; 512-bin run 230 s; 400-bin noise runs 184 s; 8-way parallel). Per-run overhead ~3 s. Continuations cost the same per bin as fresh runs. n=16: 1.42 s/bin (m0c, not re-measured; pilot before Part 1.1). Pilots done: R0 (clock, continuation, noise levels), W pilot (sustained DH/DT, 1000 bins each).

Pilot findings that set the plan: adult state exact by b≈300 (T_dev=32); contraction time constant ≈ 9 bins; sustained DT reaches a fixed point at b=181; **sustained DH reaches a period-2 cycle at b=232** (so W = 240 declared, and the stationarity criterion includes a CYCLE2 branch); response windows of 192 bins (≈ 21 time constants) suffice for pulse responses.

## Run lengths (bins) and projection (core-hours = bins × 0.48 s / 3600)
| Item | Runs | Bins/run | Core-h |
|---|---|---|---|
| R0 (done) | ~60 | various | ~4 |
| R1 canonical (60 ind) + T_dev 512 (10 ind) | 70 | 512; 2048 | 3.9 + 2.7 = 6.6 |
| R2 sustained twins (DH, DT, AN × 20) | 60 | 768 | 6.1 |
| R2 unperturbed twins (fresh + null adult) | 40 | ~800; 560 | 4.9 |
| R2 perturbed (5 perts × 3 timings × 20) | 300 | 640 / 624 / 560 | 23.0 |
| M1-comparable AN re-run (v1 settings) | 80 | 1024 (60); 512 (20) | 9.2 |
| R3 kicks (5 ind × (4 types × 20 + 1)) | 405 | 400 | 21.6 |
| R4 noise: long adult runs (4 ind × 3 levels) | 12 | 6000 | 9.6 |
| R4 noise: reduced R2 (10 ind × 3 levels × {DH, SHAM, twin}, ADULT) | 90 | 560 | 6.7 |
| Part 1.1 16-cell census (30) | 30 | 512 canonical (+ continuation if not stationary) | 30×512×1.42/3600 = 6.1 (to ~12) |
| Part 1.2 other families (10 ind × 2 families × {sustained, DEV-LONG, ADULT}; pilot 3 values) | ~70 | ~700 | 6.5 |
| Part 1.3 high initial expectation k=2,4 (10 ind each) | 20 | 512 | 1.4 |
| Part 2 Tier 1 (S_FP; 4 ind × ~230 pulses + linearity subset ~48 + twins) | ~1100 | 195 | 28 |
| Observation-ladder rendering O1–O4, package, leak check | — | CPU, post hoc | ~3 |
| **Tier 1 total** | | | **≈ 136–142 core-h = 17–18 h at 8-way full parallelism** |
| Part 2 Tier 2 (S_DEV at 16, 32, 64, 128 bins: 4 × 4 ind × ~230 pulses) | ~3700 | 195 | ~96 (≈ 12 h) |

**24 h rule:** Tier 1 projects to ≈ 17–18 h < 24 h, so no stop and no cuts are proposed. Tier 1 + Tier 2 ≈ 29–30 h would exceed 24 h; Tier 2 is therefore run LAST and, if time is short, cut only by dropping whole named conditions (declared at that point, not chosen silently): candidate whole conditions in order: S_DEV at 128, then A-REGION at S_DEV. Declared parameters used in this projection (A-REGION grid, linearity-subset size, pulse window) are placeholders until the Part 2 pilots fix them.
Early stopping: not available inside a single `spm_ADEM` call; compute is bounded instead by using continuations from the adult state (no re-development) and horizons set from the measured time constants. Individuals are redundant after merging (R0.3); compute is spent on conditions (targets, regions, times, noise realisations), not on extra individuals.
