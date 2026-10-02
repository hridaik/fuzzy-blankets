# ROBUSTNESS_V2.md — R3: kicks on the mature body under protocol v2

Status `ESTABLISHED`. Kicks K1 (position, σ = 0.5 and 1.5 × 1.0806), K2 (secretion → population mean), K3 (belief reset to fresh randn/8), K4 (one cell displaced 3 × 1.0806) with M1's magnitudes, applied as **continuations at b = 320 on the same absolute clock** (full D-step state kept; the kick edits the stored state: action and its history column, or the belief vector with its higher orders zeroed). No ramp reset, no re-development. 5 individuals (primary 0–4) × 20 kick seeds per type/magnitude (K2 is deterministic: 1 per individual) = 405 runs, 400 bins each. Reference for the twin: the null continuation (exact fixed point). Kick sizes measured at bin 1 equal the intended kicks (K1σ0.5: 1.3–3.1; K1σ1.5: 3.8–9.3; K2: 1.70; K4: 3.24; K3: beliefs only). Code `code/r3_kicks.py`, `code/r3_analyze.py`; data `data/v2/r3_results.json`.

| Kick | n | SHAPE | RELABELLED (Wilson 95%) | cycle structure | stationary after kick (median / max bins) | n_eff |
|---|---|---|---|---|---|---|
| K1 σ0.5 | 100 | 100 RETURNED | 5/100 [0.02, 0.11] | [2] 3, [3] 2 | 84 / 127 | 1 base × 100 distinct kicks = 100 |
| K1 σ1.5 | 100 | 96 RETURNED, **4 NEW-FORM** | 36/100 [0.27, 0.46] | [2] 18, [3] 10, [2,2] 2, [4] 2 | 95 / 188 | 100 |
| K2 | 5 | 5 RETURNED | 0/5 | – | 59 | **1** (deterministic) |
| **K3 (belief reset, s ≈ 1)** | 100 | **100 RETURNED** | **0/100 [0, 0.04]** | – | 106 / 110 | 100 distinct belief draws |
| K4 (one cell, 3 spacings) | 100 | 98 RETURNED, **2 NEW-FORM** | 13/100 [0.08, 0.21] | [3] 5, [2] 4, [4] 3, [5] 1 | 76 / 188 | 100 (cell, direction) draws |

n_eff = distinct base states × distinct intervention realisations. The five individuals have the same mature state up to relabelling: 1 base state; the kick realisations are independent draws.

## Findings
- **K3, the condition most likely to expose another attractor, does not**: with no protective ramp, a full belief reset returns to the same shape and the same roles in 100/100 (positions and secretion were untouched, so the cells re-infer their old roles). 
- **The alternative shape is reachable from the mature body by large position kicks**: 6 of 200 position kicks at the large magnitudes (K1σ1.5: 4/100; K4: 2/100; individuals 3 and 0/4) end in a NEW-FORM at d_pair = 0.411 from the reference, the distance of the second R1 class (CENSUS_V2.md). Small kicks (σ0.5) never do. Wilson for NEW-FORM among large position kicks: 6/200 = 3% [1.4%, 6.4%]. Checked: both examined NEW-FORM end states equal the R1 class-1 exemplar (`secondary_0005`) to d_pair 1.5e-9 and 3.7e-8, so the kick lands in the *same* second attractor that large initial beliefs reach.
- **Role relabelling after a kick scales with kick size** (5% → 36% for the position kicks) and is absent for the belief and secretion kicks.
- Recovery is fast (median 59–106 bins), matching the ~6.5-bin contraction constant plus tail.
- Protocol v1 comparison: M1 reported 100/100 RETURNED and only K1σ1.5 relabelling (5/20); the v2 continuation shows NEW-FORM outcomes that the v1 restart (which re-developed with ramp at 0) could not produce.
- The five individuals share one mature state up to permutation, so the 100 kicks per row are 100 kick realisations on essentially one base state.
