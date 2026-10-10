# CALIBRATION (natural dishes only)

Splits used for every threshold: **natural development dishes (200)**, divided by `body_id`: **calibration** = even body ids (100 dishes), **validation** = odd (100 dishes).
The manifest's 60 natural validation dishes (bodies 400-429) are `heldout_bodies`: they were not touched until after the freeze (a deviation from the brief's wording, which asks for validation on a disjoint subset: the disjoint subset is internal to development). No intervention run (operation, light, device, twin, sham) was ever used to set a threshold. All numbers below: `calibration/*.json` (reproduced by `scripts/calibrate_*.py`, `discover_states.py`).

## Geometry (`scripts/calibrate_geometry.py`)
| constant | value | rule |
|---|---|---|
| r_link | 1.6 | smallest grid value (0.1 steps) with <= 1 % of calibration dishes ever exceeding it in largest single-linkage (MST) edge; exceed rate calibration 0 %, validation 0 % (natural quantiles of per-frame max edge: median 1.02, 99 % 1.42, 99.9 % 1.55) |
| r_hold | 2.08 | 1.3 x r_link, hysteresis for existing co-members |
| r_coh | 1.42 | 99 % quantile of natural max MST edge (cohesion radius for the descriptor `ncomp_coh`) |
| m_min | 3 | smallest group for which a body frame is defined |
| margin | 0.15 | top-two piece difference below 0.15 of the organism size -> UNRESOLVED (declared, not tuned) |
| s_eff | 1.4 | blob sd maximising correlation between the c6 image and the O1-rendered Gaussian-sum model (corr 0.975); O1 used only as co-registered reference |
| mass_per_cell | 8.15 (sd 0.44) | foreground-region integrated c6 mass per cell on 40 calibration dishes |
| o3 foreground | far-field mean + 4 sd | single component in 100 % of calibration frames |
| o3_sign_S0 | 0.5 | natural |c6-centroid - c2-centroid| along the axis is 2.04 +- 0.04 |
Observation-model fact used: the c6/c2/c0/c4 fields are blurred versions of point sources (effective sd 1.4, quoted point-spread sd 0.5); pixel (row, col) = (y, x) with pixel centres at -fov + (i+0.5) 2 fov / 64.

## Validity envelope (`scripts/calibrate_envelope.py`, per level)
Per-axis bound = (1-alpha) quantile of the natural calibration axis value (frames >= 1), alpha tuned so that the fraction of calibration dishes passing all axes at all frames is 90 % (tightest alpha with pass >= 0.90).
| level | alpha | bounds (material, count, cohesion, shape, pattern) | cal pass | dev-validation pass [95 % dish bootstrap] | held-out natural pass (60) |
|---|---|---|---|---|---|
| O1 | 0.0056 | 0, 0, 1.47, 0.049, 1.53 | 0.90 | 0.97 [0.93, 1.00] | 0.90 [0.82, 0.97] |
| O2 | 0.0056 | 0, 0, 1.47, 0.049, 1.57 | 0.90 | 0.93 [0.88, 0.98] | 0.85 [0.75, 0.93] |
| O3a | 0.0041 | 0.53, 0.20, 8.1, 1.08, 2.24 | 0.90 | 0.90 [0.84, 0.95] | 0.93 [0.87, 0.98] |
| O3b | 0.0056 | 0.51, 0.20, 8.2, 1.03, 2.26 | 0.90 | 0.90 [0.84, 0.95] | 0.87 [0.77, 0.95] |
At O1/O2 material and count bounds are exactly 0 (natural dishes never lose or gain a cell, so any change is outside the envelope). At O3 the material axis is a field-overlap proxy and shape/cohesion bounds are very loose (pseudo-cell geometry is noisy), so O3 structural verdicts are effectively driven by count and pattern.
Time-scale matching: natural dishes have 7 comparisons at spacing 100; operation (dt 5), light/device (dt 2) runs would otherwise accumulate false exits. Axis inputs are therefore a causal median over the last 100 time units (identical to raw values at the natural spacing). Without this, controls failed the envelope in about half of the runs (found in development, fixed before freezing).

## States (`scripts/discover_states.py`, `select_state_models.py`) - see STATES.md.
OOD threshold: 0.5 % quantile of calibration log-likelihood. HMM stay probability 0.95 per 100 time units, change confidence 0.9, state assignment only for organisms with >= 12 cells (declared).

## Anticipation (`analysis_anticipation.py`): noise scale = robust sd of pre-onset frame differences (label-free); thresholds = 95 % quantile of per-run maxima in change-free twin/sham runs (this does use control and sham *development* runs; they are not intervention outcomes but they are not natural dishes - a deviation, noted in OPEN_QUESTIONS.md).
