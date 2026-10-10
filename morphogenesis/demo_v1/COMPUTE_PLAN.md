# COMPUTE_PLAN (Part B) — declared before the assets were built
CONTAINS HIDDEN INFORMATION — never give to a blind session.
Budget: Part B ≈ 12 h wall-clock (Part A ≈ 3 h; Part A's A3 regret job was run in the background in parallel and dominated the CPU).
New simulations are allowed only to regenerate exemplar assets deterministically (same seeds, same actions; live == offline engine, verified bit-identical: max |ΔL| = |ΔX| = 0.0 on held-out episode 945).
| asset | how obtained | cost |
|---|---|---|
| 1.1 oracle clip, 1.2–1.4 body | read: Octave oracle `m2a/.../direct_primary_0000.mat`, natural run pickles `a_/b_cal_2100.pkl` | seconds |
| 1.5 N = 1, 4, 24 at σ_h = 0.7 | **re-simulated** (h2d protocol, 600 tu, seed rule declared in `build_mem15.py`) | ~1 min |
| 2.1, 2.2, 3.1 | read: package v3 observables + hidden tier | seconds |
| 3.2 | frozen T5 monitor run on package O1 (undisturbed, cut) and on O1 frames regenerated from the sealed hidden log of held-out episode 988 (reproduces the logged verdicts, 164/164 frames) | seconds |
| 3.3 | **re-simulated**: serial replacement seed 0, noise-free, 2,800 tu | ~1 min |
| 3.4 | read: T4 outputs + hidden state | seconds |
| 4.1 | **re-simulated**: 5 lights × 2 states, dev seed 5001 | ~1 min |
| 4.2 | read: audit A4 + **re-simulated** equal-dose clips (dev seed 5004) and noise-free duration curve (3 held-out dishes, A4) | ~10 min |
| 4.3, 4.4 worst | read: sealed hidden logs of episodes 988–994 and 1121 | seconds |
| 4.4 regret | audit A3 (60 dishes × 5 protocols, noise-free bisection + 10-key noisy thresholds) | ~2 h on 6 cores |
| 5.x, A, B | read / analytic | — |
Tests: headless Chromium (playwright), every chapter at every pause point; ~5 min per run.
