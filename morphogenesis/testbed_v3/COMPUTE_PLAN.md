# COMPUTE_PLAN.md — testbed v3 (budget 10 h wall-clock; 8 CPU cores; JAX float64; no GPU)

Measured speed (v2): ~25k RK4 steps/s per core for 24 cells (dt = 0.0125). Switch trials are SHORT in v3 (durations 1/g, 4/g, 16/g = 1.7, 6.7, 27 tu; release 20/g = 33 tu), so G3-style bisection is cheap. Declared before running; every batch states question → decision.

| # | batch | question → decision | est. |
|---|---|---|---|
| C0 | H0 tests (T4 decoupling 20 interventions x det/noisy; reporter formula; v2 + v1 tests) | is the implementation what the spec says? | 5 min |
| C1 | H1 structure: 16 seeded starts; 3 seeds x 20,000 tu | code path = v2 G1? | 15 min |
| C2 | H2(a)-(c): isolated cells, body a/b, bath sweep | T1-T3 within tolerance? choose sigma_h pilot | 30 min |
| C3 | H2(d) groups 2/4/8/12, quorum curve, 2 noise levels | T5 / lifetime vs N | 1 h |
| C4 | H2(e) durability 2 states x 10 seeds x 20,000 tu | gate H2 | 40 min |
| C5 | H3 deterministic bisection: 25 patterns x 3 durations x 2 directions | switch exists? dose table | 1 h |
| C6 | H3 noise: 6 centres x 10 seeds at 1.2x threshold; controls | robustness | 30 min |
| C7 | H4 events (replace 24, extrude 24, cut x3, fusion a+a, a+b at overlapping offsets) | memory outcomes | 1 h |
| C8 | H4b attenuated place sensing (bounded <= 1.5 h) | adopt? | 1.5 h |
| C9 | H5 (only if H0-H3 pass): natural ensembles >= 1000 decorrelated samples per state, stress, switch datasets, package | blind package | 2.5 h |
| C10 | viewer exemplars + headless screenshots | inspect | 20 min |

## Log (appended as batches finish)
- C0 H0 tests (6 pass: T4 det+noisy, reporter, isolated f=1/2, seed, mean-field l*): 35 s. C1 seeded 16/16. C2 (H2 a,b,c): 140 s wall (T1 rate 0.1003; T2 l*=2.292; T3 jump 0.6-0.7 vs 0.636).
- C4 H2(e) durability launched (20 x 20,000 tu, 7 workers); C5 H3 bisection launched concurrently.
- C5 H3 deterministic bisection: 150 jobs 667 s wall. Gate H3 (deterministic) passes; dur 1/g has no threshold (bounded drive).
- C5/C6 rerun after fixing reporter scoring rule (reporter lags rho ~2 tu; scored over last 10/g of release); old results kept in data/superseded.
- C5/C6 reruns done (525 s noise batch). Corrected thresholds: 4/g best 440 (c10) vs WB 450 (2/24 below WB), 16/g 14/24 below WB.
- C8 H4b: seeded start 0/16 complete (variant rejected). C7 H4 events done. H2(d) groups done (180 jobs).
- C9 H5 raw generation: natural 260 bodies (2333 s), stress 39 triplets (693 s), switch 144 runs (355 s), decoy 16 (51 s).
- BUG found by tests/test_package.py: twin arm of the stress dataset also received the operation (twin == event). Fixed in gen3.py; stress family regenerated and package rebuilt. Old raw in data/superseded.

# Follow-up: audit of T4 (Part A) and package v3 + live environment (Part B)
Budget: Part A ≈ 3 h (no new simulations), Part B ≈ 8 h; 8 cores. Declared before running.
| # | batch | question → decision | est. |
|---|---|---|---|
| A | audit scripts over stored truth (truth tables, a1–a8, viewer) | how right was T4? → AUDIT_T4.md | ≈ 1.5 h (done) |
| B1 | regenerate raw runs at fine resolution: natural 36 runs × 5,600 tu (1 tu frames; 50 × the slowest observable relaxation 112 tu), stress 117 runs × 600 tu, switch 120 runs, decoy 16 runs (0.5 tu frames in the dense window [onset−20, release+100]) | does the finer sampling expose lead/lag and fast dynamics? → package v3 | ≈ 40 min |
| B2 | render O1, O2, O3a, O3b, O3c (parallel, ≈ 5 GB); leak check; ESS report | package v3 ready? | ≈ 40 min |
| B3 | live environment (separate server process) + tests | can a blind client interact without engine access? | ≈ 2 h dev |
| B4 | viewer exemplars (OBSERVABLE builds) + screenshots | inspect | ≈ 30 min |
- B1 raw v4 generation (natural 36 × 5,600 tu, stress 39 triplets, switch 120, decoy 16): ≈ 50 min wall on 8 cores. B2 rendering 289 runs (O1,O2,O3a,O3b,O3c, hidden tier): 1,360 s render + effective-sample-size step (the first ESS version re-decompressed npz arrays per frame and was killed; fixed) ; 14 GB. B3 live environment tests: 28-63 s. Part A audit ≈ 1.5 h of scripts, no new simulations. Part B total ≈ 4 h.
