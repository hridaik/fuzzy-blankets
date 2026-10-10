# COMPUTE_PLAN (written before analysis code)
Budget 16 h wall-clock, 8 cores, numpy/scipy/matplotlib only (no sklearn/pandas); own GMM, ridge, Louvain (flock code).
Data: 513 runs x 4 files (691 MB); runs are tiny (<=120 frames x 48 cells) except O3 images.
| step | est. time |
|---|---|
| Part A inventory | 5 min |
| Part B detector/tracker (O1,O2) on dev natural + operation dev, calibrate radii | 1 h incl. iteration |
| O3 segmentation (CLEAN-style Gaussian deconvolution) + consistency vs O1 | 1.5 h |
| Part C layers, envelope calibration on natural calibration split, validate on validation split | 1 h |
| Part D state discovery (GMM k=1..5, held-out stability), online estimator | 1.5 h |
| Parts E/F/G on dev | 2 h |
| Freeze (FROZEN_CONFIG.json + hash), single held-out run | 30 min |
| Viewer + 5 playwright screenshots, docs | 2 h |
Total plan ~10 h; fallback: drop O3b-specific extras and reduce bootstrap reps (1000 -> 500) if behind.
Order of discipline: develop on `development` runs only -> freeze -> run held-out once.
NOTE on natural splits: the manifest marks the 60 natural validation dishes (bodies 400-429) as held-out. They are therefore NOT used
for any tuning. Calibration/validation for thresholds is made INSIDE the 200 development natural dishes, split by body_id (see CALIBRATION.md).
Held-out natural dishes are only used once, after freeze.

## Actual compute (wall-clock, 8 cores)
Stage 1 (all 513 runs x 4 levels): ~2 min; stage 2: ~15 s; state discovery per descriptor family: ~3 min x 5; calibration scripts: < 5 min each; held-out analyses incl. info theory with permutation nulls: ~6 min; viewer build ~3 min; playwright screenshots < 1 min. Total compute < 1 h of the 16 h budget; the rest was development iteration. No step was dropped.
