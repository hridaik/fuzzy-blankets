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

---
## UPDATE 2 (redirect: D-stage; written after the D1/D2/D4 pilots, before the D3/D4 full runs)
The original Part 2 library is NOT built (replaced by the revised, symmetry-reduced library below). R4 and Part 1 continue as before.

**Pilot findings**
- **BLAS oversubscription:** Octave's threaded BLAS made 8 workers run at load ≈ 25 (pilots were ~3× slower than the 0.48 s/bin baseline). All later launches set `OMP/OPENBLAS/MKL_NUM_THREADS=1`.
- **D1:** 224-dimensional Jacobian, two central-difference steps (1e-4, 1e-6) agree to 4–6e-6 relative; ≈ 0.8 s per evaluation lightly loaded; 3 states ≈ 18–45 min wall under load. DONE (see SKELETON.md).
- **D2:** sub-stepping (`E.dt` = 1/m) is stable at the unperturbed fixed point but any perturbation (1e-3 position pulse, no DH) diverges for m = 2 and 4 (positions ~1e32). The engine is therefore not a usable finer integrator, and the full sub-stepped sustained-DH rerun is NOT run (cost saved ≈ 3 core-h). D2 conclusion rests on the Jacobian/Floquet analysis and the D3 onset scan.
- **D4 pilot (6 directions, 65 evaluations, 2559 s wall under load):** single-cell displacements up to 10 (≈ 11 × mean NN spacing) never leave SAME on the two tested directions; whole-body random displacement gives FATE-SWAP at 8.5; regional secretion pulse FATE-SWAP at 17; global ligand-1 pulse FATE-SWAP at 4.5; a non-monotone window exists (single-cell ligand pulse: FATE-SWAP at 15.8 only, SAME at 5 and 50). No SHAPE-SWITCH was seen in any pilot direction, so the SHAPE-SWITCH bisection will mostly report "no threshold up to max".
- Cost per evaluation ≈ 1–3 settle segments of 192 bins (≈ 1.5–5 min); no-effect direction = one grid scan.

**Declared D4 brackets:** displacement (position or belief-space) 0.05–10 (position units; 1 unit ≈ 1.14 × mean NN spacing); secretion pulses 0.05–50 (pulse window 4 bins). 7-point log grid + 1% log bisection; **single-cell displacement directions (128) use a 4-point grid** (declared cost cut; a non-monotone window narrower than a factor 5.8 in amplitude can be missed, flagged in the report). Mirror reduction not applied (kept all 8 roles × 16 directions) unless confirmed in D4 analysis.

**Revised projection (core-h at the threads-fixed rate 0.48 s/bin)**
| Item | Runs | Core-h |
|---|---|---|
| D1 (done) | 8 Jacobian jobs | ~2 |
| D3 (DH, DT: 41+40 steps up and down × 2 starts; PREC 25 steps × 2 starts; ≤ 4 × 192 bins per step) | ~6 chains | ~14 |
| D4 (246 directions: 128 disp1 × ≈ 4–6 evals; 25 body + 5 belief-space × ≈ 15; 88 pulses × ≈ 12) | ~2,800 evals | ~75 |
| D5 edge tracking (≤ 200 runs × ≤ 576 bins) | 200 | ≤ 15 |
| D6 (3 thresholds × 2 relabelled individuals × ~20 evals) | 120 | ~8 |
| Revised Part 2: 6 bases (class-0 adult, class-1 adult, class-0 dev states b = 16/32/64/128) × 8 roles × 4 channels × positive sign, 192-bin windows; linearity subset (sign reversal and ×2); one relabelled verification individual; transition dataset (D4 pairs) | ~1,700 | ~45 |
| Part 1 remainder (16-cell census in progress) | — | ~8 |
| **Remaining total** | | **≈ 165 core-h ≈ 21 h at 8-way** |

**24 h rule:** projected ≈ 21 h < 24 h, so no stop. Order of execution: D3 → D4 → D5/D6 → revised Part 2 → Parts 3–4. If the clock at launch of the revised Part 2 shows < 6 h of budget left, whole named conditions are dropped in the order: (1) dev-state bases at 128 bins, (2) dev-state bases at 64 bins, (3) the ×2-amplitude linearity subset; each drop will be declared in README.

### UPDATE 3 (D3 cut, declared before the D3 chains were completed)
Measured D3 cost ≈ 8 steps/hour/chain under load (settle segments of 192 bins, 2–4 per step near transitions), i.e. ≈ 10 h for an 81-step DH chain. Declared cuts (nothing else changed): (a) the DH/DT ε grid is 0.05 up to ε = 0.5 and 0.1 from 0.5 to 1 (31 steps up+down instead of 81); the first 11 steps are identical to the original grid and were kept; (b) **class-1 DH chain runs the up-sweep only to ε = 0.5** (CORRECTION, see update 4: the class-1 DT chain was later run in full, to ε = 1.0 up and down, because its trajectory does not collapse at ε = 0.05): the first step (ε = 0.05) already collapsed the class-1 body onto the class-0 trajectory (d_ref0 and d_ref1 equal the class-0 chain to 3 digits at every step to ε = 0.3), so the continuation of that chain is a relabelled copy of the class-0 chain; its down-sweep is reported as INFERRED from the class-0 chain, not run. PREC chains unchanged (25 steps each).
D4 measured ≈ 180 evaluations/hour at 4 workers under load; the D4 run continues and its direction list is re-examined when D3 frees cores.

## UPDATE 4 (closing record; written after all runs finished)
**Measured wall-clock (log timestamps, 2026-10-02):** D1/D4-pilot logs start 10:39; D3 chains 13:15–15:18; D4 forward launcher 13:16–23:59 (240 directions, 10.7 h); revised Part 2 library 14:17–23:31 (747 runs, 9.2 h, 3 niced workers sharing the machine with D4); D5 16:19–17:00; D6 16:32–16:43; D4 reverse-order launcher 17:13–23:59 (199 directions taken from the other end of the list; 246 direction files exist in total). **Total D-stage queue: ≈ 13.3 h from first launch to last completion**, inside the 24 h stop rule; the earlier projection was ≈ 21 h core-time-equivalent.  Part 1 and R4 are accounted for in GENERALIZATION.md / NOISE.md; their wall-clock was not re-tallied here.
**Cuts actually made (all declared above, none new):** D3 grid (update 3, DH class-1 truncation); D4 single-cell displacement 4-point grid (update 2); D2 sub-stepped rerun NOT RUN (engine diverges under sub-stepping); D5 stopped at 196 of the 200-run cap with the bracket lost at hops 15–20 (SKELETON.md). **No whole named condition was dropped for time**: the contingency order of update 2 (dev-state bases at 128, then 64, then the ×2 linearity subset) was not triggered; the revised Part 2 ran as designed (747/747).
**D4 totals:** 246 direction files, 2,309 evaluated amplitudes, 4,900 run files in `data/v2/d4/`; 0 NONCONV.
**Package:** 2,418 segments, 891,632 bins, 156 conditions, 150 individuals, 152 MB (including 34 ladder segments, 1,562 rendered frames), leak check PASS.
