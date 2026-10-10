# COMPUTE_PLAN.md — testbed v2 (budget 12 h wall-clock, 8 CPU cores, JAX float64, no GPU)

Single-run speed measured: ~25k RK4 steps/s per core for the 24-cell model (dt = 0.0125 → 20,000 time units ≈ 2 min). Every batch below states its question and the decision it informs. No broad searches; knobs only within the declared ranges.

| # | batch | question → decision | est. |
|---|---|---|---|
| B0 | G0 deterministic checks | is the implementation what the spec says? → proceed | <1 min |
| B1 | G1 (a),(b): 16 seeded starts × a handful of declared knob settings (beta_E, k_mu, pi_c/pi_lam), Jacobians | is the categorical body crisp and plastic? → choose beta_E, k_mu, ratio | ~10 min |
| B2 | G1 (c): 10 seeds × 20,000 tu, noise | durable? → freeze G1 operating point | ~25 min (8 cores) |
| B3 | G1 (d): 24 single replacements + 4 serial | repair report | ~15 min |
| B4 | G2 (a)-(f): mean-field numbers, isolated cell, bodies L/R, hysteresis continuation, 2×10 seeds × 20,000 tu | does the body remember while the cell forgets? → choose pi_d, pi_psi, r, k_h, sigma_h | ~1.5 h |
| B5 | G3 bisection: 24 centres × 3 durations × 2 directions ≈ 144 bisections × ~7 runs × (dur+2000 tu) | is there an identity-preserving, location-dependent switch? | ~2 h |
| B6 | G4 identity events (24 + 24 + 4 serial + cuts + fusions) | handedness outcomes of cuts and fusions | ~1 h |
| B7 | G5 datasets (natural ensembles, stress, switch, observation levels, blind package) | package v2 | ~2 h |
| B8 | viewer exemplars + headless screenshots | inspect | ~20 min |

Timings and outcomes are appended below as batches finish.

## Log
- B1 (G1 a,b; 6 declared settings × 16 seeds; ~18 min serial): beta_E=4, pi_c=e, pi_lam=e^3 selected (16/16, min orbit belief 0.98). Decision: G1 operating point.
- B2 (G1 c; 10 seeds × 20,000 tu, 8 workers): 885 s wall. 0/10 dissolved.
- B4a (G2 a-d deterministic; hysteresis 13 steps x 1500 tu), B4b G2e durability 2 forms x 10 seeds x 20,000 tu, 7 workers: 1630 s wall. 0/20 spontaneous switches.
- B5 (G3 scan: 93 jobs, geometric amp scan 0.5..128, 24 centres + whole body, 3 durations, L->R and 6 centres R->L): ~100 min wall incl. contention. 0 switches. G5 not run (gate).
- B6 (G4: replace 24, serial 4, extrude 24, cut 4, fuse 6; deterministic): ~6 min wall total.
- B8 viewer (5 pages) + 12 screenshots, diag.py (dt, Kramers, G3 mechanism): ~10 min. Total compute ≈ 6 h of 12 h; G5 not run (gated).
