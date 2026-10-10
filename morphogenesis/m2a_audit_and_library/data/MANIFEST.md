# Data manifest (Part 0)
Engine: m0c fallback engine (rollouts `perm_*`, `noiseseed_*`, `long_*`) / hand-written `oracle/direct_morph.m` (`direct_*`) / `oracle/m2a_run.m` toolkit (`frozen_*`, `longabs_*`). spm_ADEM config hash `1e351f1b3a7f0ef9`; M2A oracle dir hash `d1d8505b07c52fb4`. Noise: identically zero (AUDIT_M1.md 0.2).
- data/part0/*.mat: Part 0 rollouts (positions 2n x N, secretion 4n x N, v_expect n^2 x N)
- data/part0/offline_*.json, part0_results.json: analysis outputs
- data/twins/: 40 matched unperturbed twins of M1 withdrawal runs (N=1024; FRESH and ADULT-restart), plus restart states
- data/*.log: launcher logs
No OBSERVABLE-only package was built (Part 3 not done).

# Data manifest — protocol v2 (M2a continuation and redirect)
Engine: `oracle/spm_ADEM_m2a.m` (state-exporting copy of SPM12 `spm_ADEM`, bit-identical to SPM when no state is imported: `tests/test_engine_equivalence.py`); canonical clock T_dev = 32 (secondary 512), zero process noise unless flagged. Protocol-v1 data (M1) are never mixed with these.
- `data/r0/` (R0), `data/v2/census/`, `census512/`, `r2/`, `r3/`, `r4/`: R1–R4 (CENSUS_V2, WITHDRAWAL_V2, ROBUSTNESS_V2, NOISE); `r1_results.json`…`r4_red_results.json`, `reanalysis_*.json`
- `data/v2/p1_16/`, `p1_fam/`, `p1_hi/`, `p1_pilot/`; `p1_results.json`: Part 1 (GENERALIZATION.md)
- `data/v2/d1/`, `d2/`: Jacobians and Floquet/sub-step attempts (SKELETON.md); `d3/`, `d3_*.json`, `d3_summary.json`, `d3_tables.md`: hysteresis (HYSTERESIS.md); `d4/` (4,900 run files + 246 `dir_*.json` direction records), `d4_summary.json`, `d4_tables.md`: MINIMAL_PERTURBATIONS.md; `d5/`, `d6/`, `d6_results.json`: edge tracking and replication
- `data/v2/p2rbase/`, `p2r/`, `p2_pilot.json`, `p2r_results.json`: revised library (LIBRARY.md, LINEARITY.md)
- `data/*.log`: launcher logs (`d4_full.log`, `d4_rev.log`, `p2r.log`, `pkg_final.log`, …)
- Blind package: `../m2_blind_package/` (built by `code/pkg_build.py`, `pkg_ladder.py`; checked by `code/leak_check.py`). **Sealed** mapping and reference arrays: `sealed/` (never in the package).
- Viewer: `../viz/output/m2a/{observable,audit}/` (55 entries each), index section in `../viz/index.html`.
