# METHODS (flock origin: KEEP / ADAPT / NEW)
| # | method | origin | status |
|---|---|---|---|
| 1 | Single-linkage detection r_link 1.6 with hysteresis; MST cohesion; m_min 3 | T4 (flock candidate detection re-derived) | ADAPT (thresholds re-checked on v3 natural cal: 0 exceedances) |
| 2 | Forward identity by given O1 ids; Jaccard material | stage6 `jaccard`/forward tracker idea via T4 | KEEP |
| 3 | O2 cell tracker (Hungarian on registered position + fingerprint, block-vote) | T4 `celltrack.py` | KEEP (re-tested vs O1 on v3: 100 % links, 10 runs) |
| 4 | O3c blob detection (gaussian smooth + local maxima) | new | NEW (small test) |
| 5 | Body frame: principal axes, sign from c6 slope; e2 = rot90 e1 | T4 / flock heading frame | KEEP |
| 6 | Descriptor set (reflection-sensitive / invariant) | T4 `describe.py` | KEEP |
| 7 | Baseline-relative layered envelopes (material, geometry, pattern), 99 % quantile of 600-tu window maxima x 1.15, calibrated on natural cal only; validated on val | flock identity envelope (via T4 quantile envelope) | ADAPT (baseline-relative; separate axes; V_body = material+geometry) |
| 8 | V_body / V_body_conservative | flock V, V_conservative | ADAPT (state excluded; events -> conservative) |
| 9 | Two-state Gaussian posterior on (c4-c5, c0 dipole) with 10-tu median, TRANS label | T4 online state estimator | ADAPT (no HMM: natural dwell is unbounded; fast induced transitions) |
| 10 | Autocorrelation decorrelation times for window choice | flock ESS idea | ADAPT |
| 11 | Lagged ridge predictive influence with held-out dishes | flock held-out predictive contribution | ADAPT |
| 12 | CRN twin / matched sham paired design | flock paired design | KEEP (environment-supplied) |
| 13 | Safe-probe sysid, bisection on log amplitude | new | NEW |
| 14 | Online escalating-pulse commit/un-commit controller | new | NEW |
| 15 | Dish-clustered bootstrap, sign-flip permutation null, type-I variance decomposition | flock variance decomposition / paired design | KEEP/ADAPT |
| 16 | Viewer (own canvas page, playwright screenshots) | T4 viewer idea, own code | NEW |
Flock/T4 material read: README/METHODS/OPEN_QUESTIONS and library code of T4 (copied); `core.py`, `benchmark.py`, `stage6_flock` copied, **not studied beyond T4's usage**.
