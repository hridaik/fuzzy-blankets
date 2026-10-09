# Data manifest (testbed/data)
| file | produced by | content |
|---|---|---|
| oracle_targets.json, oracle_curves.npy | code/calib_targets.py | oracle merging / belief-timing targets (12 individuals) |
| calib_grid.json | code/calib_time.py (first grid only; later two grids printed in ENGINE_SPEC) | time-calibration grid |
| t12_convergence.json | code/t12_convergence.py | RK4 order, fixed-point convergence, stability limit |
| t14_census.json | code/t14_census.py | 100-draw census vs oracle classes |
| t14_cde.json | code/t14_cde.py | DH/DT families, Jacobian slowest modes, speed |
| t2a_results.json (+ _pis3 variants) | code/t2a.py | T2a 350 runs (current operating point; `_pis3` = earlier log pi_s = 3) |
| t2b_results.json, t2b_B_results.json, t2b_ka1.2_results.json | code/t2b.py, t2b_B.py, t2b_ka.py | crisp-role sweeps |
| p2_jacobian.json | code/p2_jacobian.py | Jacobian spectra at A, B, chiral end states |
| noise_fluct.json, crn.json | code/noise_crn.py fluct / crn | operating noise and CRN check |
| natural/ (manifest.json, *_obs.npz, *_hid.npz) | code/noise_crn.py ens 0.02 | natural ensembles, two-tier exports |
| chiral_forms.json, chiral_pulse_scan.json | code/chiral.py forms / pulse | T2d |
| explore_logs/ | transcribed from terminal output | memory-model exploration (see TRANSCRIBED_NOTE.txt) |
| *.log | batch stdout | |
Seeds: oracle initial beliefs (census), `default_rng(k)` for draws, `seeded_start(k)` uses `default_rng(777+k)`, noise `PRNGKey(1000+k)` / `5000+100+k` (validation), engine key 0 elsewhere.

## Testbed v1 additions
| file / dir | produced by | content |
|---|---|---|
| s1_forms*.json, s1_rates*.json, s1_switch_*.json, s1_grid_*.json, s1_*.log | code/s1.py | S1 scans (`_ng` = natural-gradient variant) |
| s2_geometry.json | code/s2.py | L vs R geometry |
| s3_ladder.json, s3_grad.json, s4_ladder.json, s4_refine.json, s4_long.json | s3_ladder.py, s3_grad.py, s4.py, s4_refine.py, s4_long.py | switch searches |
| i2a_replace.json, i2b_serial*.json, i2c_extrude.json, i2d_cut.json, i2e_fuse.json | code/i2.py | identity-event checks |
| natural_pilot.json, natural_pilot2.json | natural.py pilot, natural_pilot2.py | decorrelation / dissolution pilots |
| natural_v1/ (560 bodies + manifest), natural_v1_dense50/, natural_v1_superseded/ | natural.py ens | natural ensembles (final / dense-50 reference / superseded 200-spacing) |
| natural_stats*.json, natural_form_fraction.json | natural_stats.py | ensemble statistics |
| stress_raw/*.pkl, stress_check.json, stress_outcomes.json | stress.py, stress_check.py, stress_outcomes.py | identity-stress runs (raw, hidden), CRN check, outcomes |
| lna_L/R.npz, lna_summary.json, influence_L/R.npz, influence_summary.json | lyap.py, influence_forms.py | hidden ground truth |
| blind_v1_hidden/ | build_blind.py | opaque-label mapping and per-run hidden metadata (NOT in the package) |
