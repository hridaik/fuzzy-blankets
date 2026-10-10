# INFORMATION-THEORETIC STRUCTURE (Part G)

Data: natural dishes, O1 body-frame variables: 7 channels x 3 regions (terciles of the coordinate along the signed major axis: head / mid / tail) = **21 variables** per dish-frame (script `scripts/analysis_info.py`, `calibration/info_dev.json` = 200 development dishes; `results_heldout/info_heldout.json` = 60 held-out natural dishes, run once).

## Sampling, decorrelation, effective sample size
| | development | held-out |
|---|---|---|
| dishes x frames | 200 x 8 | 60 x 8 |
| lag-1 (100 time units) residual autocorrelation (dish mean removed) | -0.145 (bias-corrected for T = 8: -0.002) | -0.146 (-0.003) |
| intra-dish correlation (ICC, mean over variables) | 0.363 | 0.341 |
| design effect | 3.54 | 3.39 |
| n_eff using all frames | 452 (n_eff/dim 21.5) | 142 (6.8) |
| independent samples = one random frame per dish | 200 (n/dim 9.5) | **60 (n/dim 2.9)** |
| requirement n >= 5 dim | met (both) | one-frame version **fails**; all-frames n_eff version met |
Frames separated by 100 time units are decorrelated after removing the dish mean (the persistent component is the dish-level state, ICC about 0.35), so the lag-1 predictability is only dish-level.
Estimator: Gaussian plug-in L = I(X_I; X_E | X_B) with shrinkage 0.2 toward the scaled identity (formula of `core.py` / `benchmark.plug_in_L`; checked against the population value in `tests/test_t4.py`). Null: 1000 random partitions of equal sizes (300 for the all-frames variant). Held-out results are therefore indicative only.

## Partitions and leakage (one frame per dish; L, null median [percentile of observed L in the null]; development | held-out)
| partition (I,B,E) sizes | development | held-out | verdict |
|---|---|---|---|
| chan: I=c4c5, B=c6, E=c0-c3 (6,3,12) | 0.028, 0.443 [0.000] | 0.074, 0.557 [0.000] | **good blanket** |
| chan: I=c0-c3, B=c6, E=c4c5 (12,3,6) | 0.028, 0.429 [0.000] | 0.074, 0.552 [0.000] | **good blanket** |
| chan: I=c4c5, B=c0-c3, E=c6 (6,12,3) | 0.001, 0.057 [0.007] | 0.021, 0.096 [0.026] | good blanket |
| chan: I=c6, B=c0-c3, E=c4c5 (3,12,6) | 0.001, 0.056 [0.006] | 0.021, 0.092 [0.033] | good blanket |
| chan: I=c0-c3, B=c4c5, E=c6 (12,6,3) | 0.106, 0.165 [0.285] | 0.188, 0.239 [0.325] | not distinguishable from random |
| chan: I=c6, B=c4c5, E=c0-c3 (3,6,12) | 0.106, 0.164 [0.281] | 0.188, 0.237 [0.322] | not distinguishable |
| Louvain (communities {c0-c3,c6 in all regions} = 15 vs {c4,c5 in all regions} = 6; B empty) | 0.029, 1.051 [0.000] | 0.084, 1.177 [0.000] | **good (trivial) partition** |
| region: head/mid/tail, all 6 role assignments (7,7,7) | 0.175-0.403, null 0.23 [0.33-0.91] | 0.233-0.415, null 0.31 [0.19-0.82] | **not blankets** |
Louvain on the variable-level predictive-influence matrix found 2 communities in both samples (identical membership); no third community, so B is empty by construction.
Plain statement: the channel-type partitions that keep the dish-level pair {c4,c5} apart from the type channels {c0-c3} (graded channel c6 or the type channels as boundary) leak far less than random partitions; this reflects approximate independence between channels together with strong dependence between regions of the *same* channel (random partitions cut those dependencies, channel partitions never do). It is not evidence of a dynamical boundary. Body-frame region partitions are not blankets (they leak as much as or more than random).

## Directed predictive contribution (lag-1 ridge, dish-clustered 5-fold CV, relative held-out loss reduction, 95 % dish-bootstrap CI)
**No directed influence.** For every partition and every ordered group pair the CI of the relative held-out gain includes zero or is negative (largest development point estimate +0.0099 [-0.0033, 0.0244] for body-region pairs; held-out +0.0004 [-0.020, 0.020]); Louvain I->E in development is significantly *negative* (-0.0083 [-0.0167, -0.0002]: adding the source hurts held-out prediction). Asymmetries (I->B minus B->I etc.) are all within CI of 0 (`calibration/info_dev.json`, `results_heldout/info_heldout.json`, `outputs/GLOBAL_SUMMARY.json`).
**Known issue (reported, not fixed; frozen):** the flag `exceeds_null` in the JSON compares the gain with the 95 % quantile of a whole-dish source permutation null; replacing the source history by another dish's history adds noise regressors, so the null is centred *below* zero and the flag is True for 46 of 74 development and 17 of 74 held-out contrasts, including negative gains. It must not be read as evidence. The valid criterion is CI above zero, which is met by none of the 74 development and 74 held-out directed contrasts.
Not done: a time-resolved version at fast sampling (natural dishes have only 8 frames at 100 time units, which is why directed influence is estimated at lag 1 only).
