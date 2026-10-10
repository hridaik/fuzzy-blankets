# MONITOR v2 (Part A) — frozen as `MONITOR_CONFIG.json` + `code/t5mon/*.py` (hash in `MONITOR_HASH.txt`, `FROZEN_HASH.txt`)

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Natural data: calibration = dev natural bodies 2100-2105 (12 runs), validation = dev natural bodies 2106-2111 (12 runs, disjoint bodies). The 12 package "heldout_bodies" natural runs (2400-2405) were featurised once but **not analysed** before the freeze (ACCESS_LOG).

## What the natural dishes look like (ESTABLISHED, dev)
* Every natural dish (24/24, 5600 tu each) sits in exactly one of two persistent mirror-image organisations for the whole run, **0 changes in 134,400 tu** (95 % upper bound on change rate ~ 2.2e-5 /tu). 12 dishes each. Which one is read, with d' > 80, from the sign of the c0 left/right dipole (`c0_dq_sens` = +0.146 / -0.144, within-dish sd 0.008) and, at O1/O3b only, from the dish-level channels (`c4_mean` 0.89 vs 0.11, `c5_mean` the reverse; within sd 0.01). The reflection-invariant descriptors do NOT separate the states, except c4/c5 means (invariant, but only visible at O1 and O3b). Everything else (type channels c1-c3, graded c6, shape, cohesion) is identical between states (d' < 1).
* Number of states: 2 (the rare third morphology of T4 does not occur in the 24 dev natural dishes; not tested further).
* State carried by two numbers `u = (c4_mean - c5_mean, c0_dq_sens)`; state label S+ (c4-high, dipole +) / S- ; TRANS if the 5-frame median is beyond the 99.9 % natural Mahalanobis radius of both.

## Time scales (A3; measured on calibration natural dishes, 2-tu sampling)
| quantity | e-fold decorrelation | acf<0.05 |
|---|---|---|
| state variables (c0 dipole, c4 mean), per-frame noise | 4-6 tu | 16-18 tu |
| channel pattern features | 2-8 tu | 2-26 tu (c0_dabsq 144) |
| cohesion MST bridge | 2 tu | 26 tu |
| shape (s1, s2) | 56-70 tu | ~206 tu |
Declared windows: **10 tu causal running median** for state and pattern (fast variables); shape is slow (e-fold ~60 tu, body relaxation ~112 tu) so it is not smoothed but compared with the dish's own baseline with a bound calibrated for slow drift over 600-tu windows. Not the fixed 100 tu of T4.

## Layers (A2), all causal, all O1 (cell ids given)
* MATERIAL: id set vs the first frame (J, LOSS/ARRIVAL events). Exact: any loss/arrival violates.
* GEOMETRY: n = 24, one linked component (r_link 1.6), cohesion MST bridge <= 1.40, shape change |s/s_base - 1| <= 4.9 % (s1) / 6.6 % (s2).
* PATTERN: max_k |median10tu(x_k) - baseline_k| / sd_within_k <= 4.83 over 14 state-independent pattern features.
* BODY IDENTITY = MATERIAL + GEOMETRY. **V_body** = cumulative (since start) all-ok; **V_body_conservative** = V_body and no SPLIT/EXTRUSION/LOSS/ARRIVAL flag ever. Pattern and the STATE are reported separately and never enter V_body. A mirror flip of the body (state change) does not change V_body (unit test).
* Bounds are the 99 % quantile of 600-tu-window maxima on calibration natural dishes x 1.15 margin; a 95 % level is kept as an informational `geometry_warn` (the controller does not abort on it).
* Baseline-relative design (a dish compared with itself, first 20 tu): between-dish differences otherwise gave 33 % false violations on validation dishes (absolute bounds), 2.7 % with the baseline-relative bounds.

## Natural false-violation rate (ESTABLISHED for these dishes; PROVISIONAL as population statement)
Per 600-tu window: calibration 0/300 for all axes; validation: pattern 2.3 %, shape-1 0.3 %, everything else 0; any axis 2.7 % (4 of 12 validation dishes had a violated window at least once). Observed in the live work: seed 5014 exceeds the cohesion bound in its untreated twin (t=152) - a natural false alarm that V_body_conservative inherits.

## State change detection (A3)
Posterior (Gaussian classes, pooled within-dish covariance) on the 10-tu median. **False changes on natural data: 0** (0 / 24 dishes x 5600 tu). Latency: on the 27 treated dev light runs that changed state, the monitor labels the new state **0-1 tu (median 1) after the raw (unsmoothed) trace enters the new state's region**. The physical transition is much slower than the detection: from release of a pulse to the new pure state takes median 27.5, q90 63, max 82 tu (live B1/B2, n=74).
## Events on package perturbation runs (dev, light/T3-T4)
Events appear only in run_01301 (SPLIT flagged, a cell displaced 22 units); runs 01709 and 01749 exceed the 95 % cohesion level without events (`geometry_warn`). Surgical/merge runs and O2/O3c event tests: NOT DONE here (T4 did O2 events).

## Observation levels (A1)
* O1: monitor frozen and used for control.
* O2 tracker (T4 `CellTracker`, copied): 100 % correct links on 4 natural dishes (800 frames each) and 6 treated light runs (340 frames each), against O1 ids (PROVISIONAL: 10 runs, no surgical runs).
* O3c: peak detection on channel 0 recovers 24/24 cells in 2/3 tested dishes (23.85 mean in one), median distance O1-cell to nearest detection 0.06-0.07 units (worst 0.73 in one frame). Cell-resolved tracking and an O2/O3c version of V_body/the state estimate: **NOT DONE** (the frozen monitor is O1-only). At O2 the c4/c5 channels are missing, so only the c0 dipole sign would carry the state (not built).
## A4 re-checks
* States: above. **Anticipation**: natural dishes contain no change to anticipate (NOT APPLICABLE); in perturbation runs the only lead is the response itself (SYSID.md; the critical-slowing cue was tested and adds nothing). **Directed predictive influence** (`code/a_influence.py`, lag 2/10/50 tu, ridge, fit on calibration bodies, test on validation bodies, no CIs): relative held-out loss reduction <= 0.017, only graded-c6 <-> shape (0.005-0.017); all other pairs <= 0.003 (PROVISIONAL, tiny, no bootstrap).
