# STATES (Part D): persistent collective states, discovered unsupervised on natural development dishes

Data: per-frame organism descriptors (channel patterns in the body frame: per channel mean, slope along the axis, left-right dipole, |q|-dipole, tail-head contrast), 100 calibration dishes x 8 frames; held-out likelihood and stability are evaluated on the 100 development validation dishes. No labels.
Procedure (`scripts/discover_states.py`): standardise + PCA (<= 8 whitened dims, 95 % variance), GMM with full covariance, k = 1..5, 8 k-means++ restarts; dish-clustered 5-fold CV log-likelihood; dish-bootstrap CI of the CV gain; half-split stability (15 random dish halves, ARI of validation labels); minimum state size 3 % of frames.
Declared rule: admissible k = {k>=2 : CV-gain CI vs k=1 above 0, ARI >= 0.8, smallest state >= 3 %}; k* = smallest admissible k whose successor has no significant gain, else the most stable admissible k, else 1. Descriptor family per level (all patterns / reflection-invariant only / reflection-sensitive only) = highest stability among families with k* >= 2, ARI >= 0.8 and positive median validation log-likelihood gain.

## Evidence 1 vs k (CV log-likelihood per frame, k = 1..5; ARI = half-split stability)
| level / family | CV ll k=1..5 | k* | ARI (k=2,3,4,5) |
|---|---|---|---|
| O1 pattern (all) | -11.54, -10.19, -9.04, -9.00, -9.00 | 3 | .53 .86 .94 .88 |
| O1 invariant only | -11.49, -10.05, -9.87, -9.87, -9.95 | 3 | .93 .96 .88 .75 |
| **O1 sensitive only (selected)** | -7.19, -5.30, -4.33, -4.29, -4.26 | **3** | .73 **1.00** .96 .87 |
| O2 pattern | -11.53, -10.41, -9.81, -9.79, -9.86 | 4 | .60 .66 .88 .88 |
| O2 invariant only | -11.47, -10.69, -10.61, -10.67, -10.73 | 1 | .33 .24 .15 .06 |
| **O2 sensitive only (selected)** | -5.78, -3.94, -2.88, -2.75, -2.72 | **4** | .80 1.00 **.97** .88 |
| O3a pattern | -11.55, -10.64, -10.15, -9.75, -9.48 | 1 (ARI < .8) | .36 .42 .45 .55 |
| O3a invariant only | -11.50, -10.81, -10.43, -10.29, -10.23 | 1 | .05 .32 .27 .26 |
| **O3a sensitive only (selected)** | -4.31, -3.98, -3.88, -3.86, -3.86 | **2** | **.97** .62 .50 .42 |
| O3b pattern | -11.49, -9.05, -8.60, -8.18, -8.03 | 2 | .98 .72 .61 .62 |
| O3b invariant only | -11.49, -9.73, -8.88, -8.76, -8.62 | 3 | .71 .87 .76 .59 |
| **O3b sensitive only (selected)** | -5.74, -3.60, -3.56, -3.51, -3.45 | **2** | **1.00** .60 .49 .43 |
(Complete table incl. BIC, validation likelihood, CV-gain CIs: `outputs/GLOBAL_SUMMARY.json`, `calibration/states_*.json`.)

## What the states are (descriptive; development natural dishes, O1 selected model)
| state | dishes (of 200) | c4 / c5 mean | c0 left-right dipole | c1 / c2 dipole | MST bridge | wide axis s2 | other |
|---|---|---|---|---|---|---|---|
| S0 | 96 (48 %) | 0.11 / 0.89 | **-0.146** | 0.184 / -0.183 | 1.02 | 0.89 | |
| S1 (rare) | 8 (4 %) | 0.50 / 0.50 (mixture of both dish modes) | +0.02 | 0.112 / -0.230 | 1.32 | 0.94 | ppq_sens -0.24: wider, looser |
| S2 | 96 (48 %) | 0.89 / 0.11 | **+0.145** | 0.183 / -0.183 | 1.02 | 0.89 | |
S0 and S2 are the same body with the **sign of the left-right asymmetry reversed** (and the c4/c5 pair exchanged): a mirror-image pair, each persistent through the 8 frames (with the selected family 100 % of development dishes carry a single label through the run at O1 and O2, 95 % at O3a, 99 % at O3b). The rare class is also split into two sign classes at O2 (4 + 4 dishes, c0 dipole +0.157 / -0.109), i.e. **four states in all: two common mirror-image organisations and a rare looser organisation with its own mirror pair**; O1 merges the rare pair (successor gain not significant with 8 dishes), O3 cannot see it.
Answer: **1 vs k:** k = 1 is rejected at every level (CV gain vs k=1: CI above 0 for k >= 2 in all selected families). **Number of states:** 2 common persistent states robustly at all four levels; 3 (O1) / 4 (O2) when the rare organisation is visible; k = 2 at O3 (rare organisation not resolved).

## Dependence on visible channels
| view | result |
|---|---|
| O1 all 7 channels, sensitive descriptors | k=3, ARI 1.00 |
| O1 without c4,c5 (family `noC45`) | k=4 (the mirror structure remains visible without the dish-level channels) |
| O2 (c4, c5 not assayed), sensitive | k=4, ARI .97; **invariant descriptors fail (k=1)** |
| O2, invariant only | the two common states are not distinguishable |
| O3a (c6,c2,c0 images), sensitive | k=2, ARI .97 (but median held-out gain only +0.5 nats/frame and per-frame labels noisy: single-label dishes 0.95) |
| O3b (+c4 image), all patterns | k=2, ARI .98; invariant patterns k=3 |
| O3a, all patterns | no stable states (k=1): image noise swamps the invariant features |
Summary: state discoverability needs a channel with a left-right (reflection-odd) pattern (c0, c1, c2, c3 dipoles) **or** the dish-level pair c4/c5; the type-channel dipoles alone suffice (O2, O3a); c4 helps invariant analysis.

## Online estimator (frozen, `OnlineState`)
Per frame: PCA-whitened descriptors (causal 100-time-unit median) -> GMM posterior -> HMM filter (stay 0.95 per 100 time units, hazard-scaled to dt) -> label = argmax if the frame is not out-of-distribution (log-likelihood < 0.5 % calibration quantile), posterior = filtered max; change = filtered posterior >= 0.9 for a new label (OOD counts as a change away). Development-validation performance (`calibration/states_report.json`):
| level | k | frames carrying the dish's modal label | mean posterior | OOD frames | false changes per dish | splice detection (dishes switched at frame 4) | latency (frames after switch) |
|---|---|---|---|---|---|---|---|
| O1 | 3 | 0.983 | 1.000 | 1.8 % | 0.10 | 100 % | median 0, q90 0 |
| O2 | 4 | 0.984 | 1.000 | 1.6 % | 0.09 | 100 % | 0, 0 |
| O3a | 2 | 0.975 | 0.997 | 1.8 % | 0.16 | 100 % | 0, 0 |
| O3b | 2 | 0.988 | 1.000 | 1.3 % | 0.10 | 100 % | 0, 0 |
**Declared latency**: one frame at the natural sampling (100 time units); for runs sampled every 2-5 time units the 100-unit causal median adds up to about 50 time units (half the window) plus the filter. This latency was measured only by splicing natural dishes at natural spacing; fast-run latency is by construction, not measured (NOT DONE).
Caveats: (i) the GMMs are very tight (within-dish sd of dipoles ~0.007), so slow drifts present in untreated twins push frames out of distribution late in long runs (25-50 % of twin/sham runs end OOD at O1); (ii) held-out natural dishes: 1-5 % of dishes with any state change (`natural_validity.json`).
