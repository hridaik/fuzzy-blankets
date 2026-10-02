# CENSUS_V2.md — R1: reference census under protocol v2 (canonical clock T_dev = 32)

Status `ESTABLISHED`. 50 primary individuals (randn(8,8)/8, seeds 0–49) + 50 secondary (std exp(2); 10 planned + **40 added after the first 10 showed one individual in a second class — a declared post-hoc extension**), each run 320 bins (adult state) + 192 bins continuation (512 total); plus 10 primary at T_dev = 512 for comparison (2048 bins). Code `code/r1_census.py`, `r1_ext.py`, `r1_analyze.py`; results `data/v2/r1_results.json`. Thresholds: THRESHOLDS_v2.md.

## Does the published clock change the stable-shape census? **Yes.**
| Class | n | primary | secondary | d_target (audit) | stationary at bin | max belief | role maps |
|---|---|---|---|---|---|---|---|
| 0 (reference phenotype) | 97 | 50/50 [93%, 100%] | 47/50 [84%, 98%] | 0.27710 (all) | 178–192 | 0.729–0.781 | 95 distinct |
| 1 (second shape) | 3 | 0/50 [0%, 7.1%] | 3/50 [2.1%, 16.2%] | 0.5455 | 218, 232, 260 | 0.455–0.822 | 3 distinct |
All 100 runs reach a fixed point (no cycles). Under M1's slow clock (T_dev = 512) the same 50 secondary draws never produced a second class. Class 0 per-cell residuals to nearest template slot (audit): {0.003, 0.129, 0.129, 0.286, 0.286, 0.323, 0.468, 0.592}; class 1 has one cell 2.75 from any template slot (below). Class 1 is an organisational defect: duplicated and vacant roles and an undifferentiated cell, mirror-asymmetric and enantiomorphic (REANALYSIS.md e). It is also reached by transient perturbations of the mature body (large position kicks: 6/200, ROBUSTNESS_V2.md; sham fields: 8/60, REANALYSIS.md b), so it is a genuine alternative attractor, not an initial-condition curiosity. **Parts 2 and 4 cover both classes** (class 1 base state: `secondary_0005`).

## Merging (class 0, 12 individuals incl. secondary) 
Pairwise permutation-invariant distance (max over 66 pairs) first stays below τ = 0.17 at bin 54, 1e-3 at 78, 1e-6 at 132, 1e-9 at 186; log-linear decay between bins 40–120 with **time constant 6.5 bins** (M1-clock estimate 8.8); numerical floor ~1e-12. Role maps: 98 distinct among 100 individuals (random permutations; 2 collisions).
## Time to stationarity
Class 0: 178–192; class 1: 218–260 (state-based criterion, THRESHOLDS_v2). M1's "246 for everyone" was the ramp (AUDIT_M1 0.3b).
## Slow clock comparison (10 primary, T_dev = 512, 2048 bins)
d_target 0.28728 (bin 512, M1's value), 0.27827 (1024), 0.27712 (2048): the slow-clock "attractor" is the fast-clock class-0 fixed point seen early; end-state d_pair to the canonical reference 2.2e-5; not stationary by the 1e-6 criterion at 2048 bins (lag-1 speed 1.2e-6; ramp still moving).
