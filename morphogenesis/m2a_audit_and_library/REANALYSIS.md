# REANALYSIS.md — zero-compute reanalyses of existing v2 data

Code: `code/reanalysis_ae.py`, `reanalysis_be.py`, `reanalysis_c.py`, `r4_analyze_red.py`. Data: `data/v2/reanalysis_*.json`, `r4_red_results.json`. All hidden-tier (audit) except where stated.

## (a) Role-indexed AN — ESTABLISHED
Role = reference-phenotype slot of the targeted cell: at onset for ADULT (the adult state is the onset state); for DEV timings the slot the cell occupies in the unperturbed twin's end state (roles do not exist at b = 0). 20 individuals collapse into **8 role cases** (slots 0–7; individuals per slot: 5, 4, 1, 1, 5, 2, 1, 1). Reference mirror pairs (y → −y): slot 1 ↔ 5, 4 ↔ 6; slots 0, 2, 3, 7 are on the axis (self-mirror).

**ADULT (deterministic function of the targeted role: yes, 8/8 role cases are internally consistent, including slots with 4–5 individuals).** Shape: NO-SUSTAINED-EFFECT in all 20.
| slot | n | window max-dev | relabelled | targeted-cell fate | cycle |
|---|---|---|---|---|---|
| 0 (head end, on axis) | 5 | 0.346 | yes | changed | swap [2] |
| 1 | 4 | 0.232 | no | same | – |
| 2 | 1 | 0.023 | no | same | – |
| 3 | 1 | 0.623 | yes | changed | 3-cycle [3] |
| 4 | 5 | 0.057 | no | same | – |
| 5 | 2 | 0.232 | no | same | – |
| 6 | 1 | 0.057 | no | same | – |
| 7 (tail end, on axis) | 1 | 0.329 | no | same | – |
**Mirror check:** slot 1 and its mirror 5 give identical outcomes (no change; identical window deviation 0.232); slot 4 and its mirror 6 likewise (no change; 0.057). So mirror-symmetric roles give mirror-equivalent outcomes in all 2 testable pairs (the single-cell perturbation x → x² acts on the long axis only, which commutes with y-reflection). Only slots 0 and 3 (both on the axis, near the head/neck) produce a durable role change; role changes always include the targeted cell.
**DEV-SHORT / DEV-LONG:** NOT a function of the role alone: slot 0 → swap [2] or 3-cycle [3]; slot 1 → none, [2], or [2,2]; slots 4 and 5 → none or [3]/[2]. Developmental outcomes depend on the individual's history (initial beliefs), not only on which role the cell ends up in; they are also identical between DEV-SHORT and DEV-LONG for the same individual (the perturbation is no longer on when the roles are fixed).

## (b) The SHAM_DH NOVEL end-states — ESTABLISHED
There are **8** (not 7) runs: individual 4 (DEV-LONG, ADULT), 10 (DEV-SHORT, DEV-LONG), 13 (DEV-SHORT, DEV-LONG, ADULT), 19 (DEV-SHORT). **All 8 are class 1**: d_pair to the reference 0.411 in all; to the class-1 exemplar `secondary_0005`: 0.0 (3 runs: 4/DEV-LONG, 10/DEV-SHORT, 10/DEV-LONG) or 0.144 (5 runs); mutual distances 0.0 or 0.144 only, i.e. exactly the two class-1 chiral variants (e below), 3 of one and 5 of the other. A random smooth displacement field applied transiently to the whole body therefore reaches the second attractor in 8/60 sham runs (13%, Wilson [7%, 24%]; n_eff ≤ 20 per timing), including 2 mature-body (ADULT) runs. DH, DT and AN never do.

## (c) R4 spontaneous transitions — ESTABLISHED (extension; noise flagged)
Long adult runs, 4 individuals × 6000 bins per level (24,000 bins per level; role assignment sampled every 5 bins).
| Level | role switches | rate per 1000 bins (95% exact Poisson) | shape-class transitions | RMS fluctuation | max d_pair to reference |
|---|---|---|---|---|---|
| L1 (1%) | 0 | 0 [0, 0.154] | 0 | 0.0086 | 0.018 |
| L2 (3%) | 0 | 0 [0, 0.154] | 0 | 0.026 | 0.057 |
| L3 (10%) | 0 | 0 [0, 0.154] | 0 (28 of 4800 samples have d_pair just above τ: fluctuation, max 0.19 ≪ 0.41) | 0.086 | 0.193 |
Spontaneous role turnover and class transitions are **absent at every level** in 72,000 bins; the baseline any intervention-induced relabelling must exceed is < 0.15 per 1000 bins.
**Reduced R2 under noise (ADULT; 10 individuals × 3 levels; matched noisy twin with the same noise realisation; end state = mean of the last 100 bins):**
| Level | DH relabelled | SHAM_DH relabelled | NOVEL (shape) DH / SHAM_DH |
|---|---|---|---|
| L1 | 10/10 [0.72, 1.00] | 8/10 [0.49, 0.94] | 0 / 2 |
| L2 | 10/10 | 7/10 [0.40, 0.89] | 0 / 1 |
| L3 | 9/10 [0.60, 0.98] | 9/10 | 0 / 0 |
**The noise-free v2 conclusion "DH on a mature body returns to the same roles (0/20)" does not survive even 1% noise** (10/10 relabel), while spontaneous switching is 0: the intervention-induced relabelling is real, and the noise-free DH-ADULT return looks like a knife-edge of the deterministic system. Shape reversion survives noise (DH: 30/30 REVERTED). SHAM_DH reaches class 1 in 3/30 noisy runs (all NOVEL end-states d_pair 0.411).

## (d) n_eff columns — DONE
Added to `WITHDRAWAL_V2.md` and `ROBUSTNESS_V2.md` (n_eff = distinct base states × distinct intervention realisations). Headlines: DH-ADULT and DT-ADULT: 1 (20 runs, one experiment); AN-ADULT: 8 role cases; SHAM ADULT: 20 distinct fields; kicks: 1 base state × 100 realisations (K2: 1).

## (e) Class 1 (hidden tier, audit) — ESTABLISHED
Members `secondary_0005`, `_0012`, `_0013` (3/50 secondary; 0/50 primary).
- **Organisational defect:** argmax-belief template slots: slot 5 (the cell position at x ≈ +0.75 on the axis) is held by **two** cells; slot 0 (the head end) is **vacant**; the same pattern in all 3 members. One cell is **undifferentiated**: maximum belief 0.455 (others 0.71–0.82) and intermediate secretion codes (0.77/0.36/0.33/0.38). The 8 cells still occupy 8 distinct reference positions (role-assignment cost small), i.e. the body is a complete 8-cell shape with a duplicated role and a missing one.
- **Free energy:** J (log-evidence-type, larger = lower free energy) at the end: 353.13 (class 1) vs 359.39 (class 0): class 1 sits 6.26 nats of J above (higher free energy than) the class-0 fixed point, yet is stable (stationary by bin 218–260).
- **Symmetry:** class 0 is mirror-symmetric about y = 0 (residual 1e-4) and not about any vertical line (0.61). **Class 1 is not mirror-symmetric** (best y-mirror residual 0.142) and comes as an **enantiomorphic pair**: `secondary_0005` = `_0012` to 0.0 and each is the y-mirror image of `_0013` to 1e-4 (unmirrored distance 0.144). The single-linkage "class" at τ = 0.17 contains the two chiral variants; at τ ×0.5 they split (as noted in CENSUS_V2.md).
