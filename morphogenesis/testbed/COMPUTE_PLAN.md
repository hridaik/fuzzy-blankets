# COMPUTE_PLAN.md — batches, questions, decisions, timings (budget 24 h wall-clock for the task)

Machine: 8 CPU cores, no GPU, JAX 0.11.2 (float64), `par.py` = 8 single-thread worker processes. Times are measured wall-clock of the batch. The session's total wall-clock was not logged; engine compute below is the part that can be accounted for. **Projection check: no batch projected beyond budget; nothing was stopped for budget reasons.** Session-time effort went mostly into design iteration (below), not into compute.

| # | batch | question → decision informed | pilot / time | result |
|---|---|---|---|---|
| 1 | oracle stationarity null-space fit | is the engine's F the oracle's? → add D0 | seconds | D0 needed |
| 2 | time-calibration grid (49 points × 6 runs) | choose k_mu,k_a → T1.3 | ≈ 0.5 s/run; ≈ 10 min total | (1.4, 1.2) |
| 3 | census 100 runs from oracle initial beliefs | T1.4(b) | 70 s | 98/100 class agreement |
| 4 | DH/DT families + Jacobians + speed | T1.4(c–e) | ≈ 6 min | fixed points; speeds |
| 5 | dt convergence | T1.2 | ≈ 1 min | order 4 |
| 6 | **exploratory template/precision/start scans** (≈ 250 single runs, 24-cell, many serial; `code/explore/`) | find any relationally assemblable 24-cell design → T2a/T2b design | 5–60 s per 4 runs; ≈ 2–3 h total (serial, not recorded individually) | compact A + graded axial morphogen + prior e⁻¹⁰ |
| 7 | T2a 7 conditions × 50 draws (twice: log π_s = 3, then 2) | T2a | 218 s / 207 s | table in TESTBED_SPEC |
| 8 | T2b grid 90 runs; B grids 54 + 24 | choose operating point | 92 s; ≈ 3 min | log π_s 2, log π_prior −10 |
| 9 | memory-model scans (slow-manifold g(s) 8 params × 13–17 s-values; mixture runs; bias) | P2/P3 | 40–240 s per batch ×6 | no bistability |
| 10 | noise scan 15 runs; CRN; ensembles 54 runs; chiral forms 16; pulse scan 42 | T2d/T2e | ≈ 2 + 0.2 + 10 + 2 + 5 min | see docs |
| 11 | viewer exemplars | each check | ≈ 3 min | 18 HTML |
Preferred analysis over sampling where possible (autodiff Jacobians, slow-manifold scans). Replicates only where stochastic or where basins depend on the draw. Estimated engine compute ≈ 4 h of 8-core wall-clock including exploration — within 24 h.

---
# Update — Testbed v1 instruction (budget 18 h wall-clock, Part S at most 6 h)
Machine as before (8 cores; note the machine is shared: load average 10–20 during several batches, which lengthened wall times). Question → decision → pilot → budget, per batch. Times are measured batch wall-clock; the session wall-clock itself was not logged (estimated 8–10 h, of which Part S ≈ 3–4 h: inside both budgets; no projection exceeded a budget, nothing was stopped).
| # | batch | question → decision | pilot / time | result |
|---|---|---|---|---|
| S1a | seeded forms, log pi_prior −6/−7/−8 (96 runs) + Jacobian rates (4) | can crisp bodies be plastic? → choose operating point | 1–2 min | rates ≈ k_mu·pi_prior; −8 best |
| S1b | long noisy runs, 32 × 3000 tu (sigma_mu 0 … 0.3) | spontaneous switching / belief noise → sigma_mu | ≈ 6 min | belief noise dissolves bodies |
| S1c | natural-gradient variant forms + rates (≈ 190 runs) | restore plasticity? | ≈ 4 min | no |
| S1d | grid log pi_s 3–5 × log pi_prior −5…−8 (192 runs + 12 Jacobians) | does higher pi_s help? | ≈ 10 min | no |
| S3a | forward ladder 1728 runs | physical families find any switch? → S4 or not | 6.4 s/run pilot; ≈ 28 min | 0 R |
| S3b | gradient search 36 optimisations | same, gradient method | 24 s/2 iterations pilot; ≈ 12 min | none |
| S4 | fate-bias ladder 144 + refine 28 + long 12 | fallback | ≈ 6 + 3 + 4 min | none |
| I2 | a (24), b (4 + 2 long), c (24), d (2), e (6) | identity-event behaviour | 5–70 s per run; ≈ 25 min in total | tables |
| T3.3 | pilot ACF; dense-50 ensemble 120 bodies; final ensemble 560 bodies × 1600 tu | decorrelation, sample size → M2 | 65 s/body; ≈ 8 + 20 + 47 min | see DATASETS.md |
| T3.4 | stress: 60 jobs × 3 arms × 300 tu | identity-stress dataset | 463 s | 180 runs |
| T3.5 | LNA (2 forms), influence (2 forms × 4 frames) | hidden ground truth | ≈ 2 + 3 min | exports |
| T3.6 | blind package build ×2 + leak check | package | ≈ 3 min each | PASS |
| V | viewer exemplars (22 files), headless screenshots (3) | each check | ≈ 5 min | built; 3 rendered without errors |
Wasted compute to disclose: the first natural ensemble (spacing 200, 12 900 tu per body) was generated before it was known that bodies dissolve at ≈ 3 300 time units; it was superseded (`data/natural_v1_superseded`); the dense-50 ensemble (`natural_v1_dense50`) is kept for the decorrelation statistics.
