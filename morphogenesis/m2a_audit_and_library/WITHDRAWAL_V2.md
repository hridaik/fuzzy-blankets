# WITHDRAWAL_V2.md — R2: withdrawal battery under protocol v2 (canonical clock T_dev = 32)

Status: `ESTABLISHED` for the 300 perturbed runs (20 individuals = primary 0–19; DH, DT, AN, SHAM_DH, SHAM_AN × DEV-SHORT / DEV-LONG / ADULT), with matched unperturbed twins (fresh 800 bins; null adult continuation 560 bins) and sustained twins (DH, DT, AN). Data `data/v2/r2/`, results `data/v2/r2_results.json`, code `code/r2_withdrawal.py`, `code/r2_analyze.py`. Thresholds frozen in THRESHOLDS_v2 before analysis (τ = 0.170 = 0.25 × min NN spacing of the empirical reference phenotype; took-effect ≥ 0.05).
Timings: DEV-SHORT on bins 0→64; DEV-LONG on 0→W = 240; ADULT = continuation from b = 320, on for W = 240 bins, then off; ramp width 4. AN cell = individual index mod 8 (0-based), passed to Octave (unit test: only that cell's long-axis sensation changes; `tests/test_toolkit.py`). Sham: random-Fourier-feature displacement field of the sensed position; SHAM_DH RMS-matched to the sustained DH twin (1.447), SHAM_AN to the sustained AN twin's single cell (per individual, 0.021–1.76, because the anomalous cell sits in a different role in each individual).

## Twins (ESTABLISHED)
- Unperturbed twins: all 40 FIXED. Null continuation from the adult state: 0/20 relabelled and max position change 0.0 (as R0).
- Sustained twins: DH → **period-2 cycle** in 20/20 (shape differs from unperturbed by d_pair 0.73–0.74); DT → fixed point in 19/20 (d_pair 0.43–0.57), one NONCONVERGED; AN → fixed point 20/20 with d_pair to unperturbed 0.017–0.147, i.e. **below τ: the single anomalous cell is compensated in shape under sustained application**. AN runs are therefore classified NO-SUSTAINED-EFFECT on the shape axis (REVERTED/PERSISTED cannot be told apart); roles and targeted-cell fate are the informative axes.
- After switch-off every one of the 300 perturbed runs ends at a fixed point (including DH, whose sustained twin cycles).

## Took-effect check
All DH, DT, SHAM_DH, AN runs show window deviations ≥ 0.05 except AN-ADULT 19/20. **SHAM_AN took effect in only 17/20 (DEV) and 8/20 (ADULT)**: the RMS-matched single-cell sham is often too weak to count; read SHAM_AN ADULT rows with that in mind.

## Outcome table (v2 taxonomy; n = 20 each; Wilson 95% for relabelling)
| Perturbation / timing | SHAPE | RELABELLED | median cells changed; cycle structure | targeted-cell fate changed |
|---|---|---|---|---|
| DH DEV-SHORT | 20 REVERTED | 20/20 [0.84, 1.00] | 6; [6] 9, [4] 2, [6,2] 2 … | – | ≤20 (a) |
| DH DEV-LONG | 20 REVERTED | 19/20 [0.76, 0.99] | 6; [6] 8, [3] 3 … | – | ≤20 (a) |
| DH ADULT | 20 REVERTED | **0/20 [0, 0.16]** | – | – | **1** (b) |
| DT DEV-SHORT | 20 REVERTED | 12/20 [0.39, 0.78] | 2.5; [2] 6 … | – | ≤20 (a) |
| DT DEV-LONG | 20 REVERTED | 12/20 [0.39, 0.78] | 2 | – | ≤20 (a) |
| DT ADULT | 20 REVERTED | **20/20 [0.84, 1.00]** | 2; [2] 20 | – | **1** (b) |
| AN DEV-SHORT | 20 NO-SUSTAINED-EFFECT | 11/20 [0.34, 0.74] | 2; [2] 7, [3] 3, [2,2] 1 | 11/20 (all relabelled runs) | ≤20 (a) |
| AN DEV-LONG | 20 NO-SUSTAINED-EFFECT | 11/20 [0.34, 0.74] | 2 | 11/20 | ≤20 (a) |
| AN ADULT | 20 NO-SUSTAINED-EFFECT | 6/20 [0.15, 0.52] | 2; [2] 5, [3] 1 | 6/20 | **8** role cases (c) |
| SHAM_DH DEV-SHORT / DEV-LONG / ADULT | REVERTED 17 / 17 / 18; NOVEL 3 / 3 / 2 | 19/20, 19/20, 16/20 [0.58, 0.92] | 6 / 5 / 2.5 | – | ≤20 (a) |
| SHAM_AN DEV-SHORT / DEV-LONG / ADULT | 20 REVERTED each | 5/20, 5/20, 0/20 | 2 | 5/20, 5/20, 0/20 | ≤20 (a) |
| NULL continuation (ADULT) | – | 0/20 [0, 0.16] | – | – | 1 |
n_eff = number of distinct base states × distinct intervention realisations. (a) 20 individuals are distinct base states at onset (different initial beliefs) but merge to one trajectory by bin ~54 while the perturbation is still on, so n_eff is *at most* 20 and probably much less for the deterministic whole-body distortions. (b) one mature state up to relabelling × one deterministic whole-body distortion: 20 runs, 1 independent experiment. (c) one mature state × the 8 distinct targeted-cell roles (REANALYSIS.md a: the ADULT outcome is a deterministic function of the targeted role). SHAM_DH ADULT: 1 base × 20 distinct fields = 20; SHAM_AN ADULT: 20 distinct (role, field) cases.

No shape ever persisted: no PERSISTED outcome and no NONCONVERGED outcome among 300 runs. The only NOVEL outcomes are SHAM_DH (2–3 of 20 per timing; the sham has no sustained twin, so any end shape ≥ τ from the unperturbed twin is labelled NOVEL; they should be inspected, not read as a perturbation effect).

## Key comparison — ADULT relabelling: real vs SHAM vs NULL vs spontaneous
| | relabelled |
|---|---|
| NULL continuation | 0/20 | 1 |
| DH (real) | 0/20 |
| DT (real) | 20/20 |
| AN (real) | 6/20 (targeted cell involved in every one) |
| SHAM_DH | 16/20 |
| SHAM_AN | 0/20 (but only 8/20 took effect) |
| spontaneous switching (noise-free) | 0 (exact fixed point); noisy baseline: NOISE.md |
Fisher exact: DH vs SHAM_DH p < 1e-4; DT vs SHAM_DH p = 0.11 (not different); AN vs SHAM_DH p = 0.004; AN vs SHAM_AN p = 0.02 (weak sham, caveat above). So relabelling of a mature body is **not** a generic outcome of any transient distortion (null 0/20; DH 0/20) and **not specific to the Kuchling perturbations** (the displacement-field sham relabels as often as DT). The ADULT DH and DT rows are one experiment replicated 20 times: converged bodies are identical up to permutation, so their outcome is the same for every individual (n_eff = 1; 0/20 and 20/20 carry no independent information beyond that). AN and the shams differ between individuals (they act on a role-dependent cell or a per-individual field), so those rows have genuine spread.

## What v1 got wrong, from this battery (see AUDIT_M1_ADDENDUM.md)
- DH-ADULT under protocol v2 (continuation, no ramp reset) returns to the same roles in 20/20; v1's ADULT restart relabelled 20/20. The v1 ADULT relabelling was largely produced by the restart (ramp reset + re-development), not by the perturbation. DT-ADULT does relabel under v2 (a 2-cycle swap in all 20).
- Developmental perturbations (DEV-SHORT/LONG) relabel in 60–100% of runs for DH/DT and ~55% for AN.
