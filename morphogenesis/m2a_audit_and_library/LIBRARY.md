# LIBRARY.md — revised, symmetry-reduced perturbation-response library (protocol v2)

**Status: DONE and ESTABLISHED for what it contains. The original Part 2 library (full cell × channel × sign × amplitude grid on many individuals) was NOT built, by instruction.** Code `code/p2_revised.py` (run), `p2r_analyze.py` (analysis); raw runs `data/v2/p2r/`, bases `data/v2/p2rbase/`, results `data/v2/p2r_results.json`. 747 of 747 runs complete (9.2 h wall, 3 niced workers alongside D4). Linearity: LINEARITY.md.

## Design (as run)
- **Every run is a continuation** from a saved D-step state on the absolute clock, with its own unperturbed twin (192 bins, same base).
- **Bases (6):** C0 = class-0 adult (`primary_0000`, b = 320); C1 = class-1 adult (`secondary_0005`, b = 320); D16, D32, D64, D128 = developmental states of `primary_0000` at b = 16, 32, 64, 128 (0.5, 1, 2, 4 × T_dev).
- **Symmetry reduction:** pulses are indexed by **role × actuator channel**, positive sign, not by cell. Role r = the cell that holds slot r of the adult role map (for the developmental bases, the cell that will hold it; for C1, the Hungarian slot label). Role maps differ between individuals only by a permutation of cells (CENSUS_V2.md), so one individual per base carries the information; the equivariance check below tests that.
- **Channels (10 per cell):** position x, position y, secretion ligands 1–4, field gain 1–4. Amplitude 0.03, width 4 bins, onset at base + 2, response window 192 bins. The amplitude is the smallest tested value in the amplitude pilot (`data/v2/p2_pilot.json`); positions and secretions met the 5 % linearity criterion there, one gain channel did not (LINEARITY.md).
- **Counts:** 6 bases × 8 roles × 10 channels = 480 positive pulses; linearity subset 180 (below); verification individual 80; twins 7 (one per base plus the verification individual) → **747**.
- **Linearity subset (declared):** roles {0, 3, 5} × 10 channels × {sign reversed, amplitude ×2} on C0, C1 and D32.
- **Verification individual:** `primary_0001` (a relabelled class-0 individual), C0 base, all 80 role × channel pulses.
- **Not done (dropped by the redirect, not by the clock):** negative-sign and ×2 pulses outside the subset, other individuals, other amplitudes, multi-cell pulses, noisy bases. No condition was dropped for time: the 24 h rule was not triggered (COMPUTE_PLAN.md update 4).

## Results (ESTABLISHED within the design)
1. **All 747 responses are transient and linear-sized: they return to the unperturbed twin.** The final-bin response norm (positions and secretion levels, difference to the twin) is at most 2.3e-7 over all 480 positive pulses (C1; ≤ 5.5e-8 on C0, ≤ 1.5e-9 on the developmental bases), against peak elementwise responses of 0.0025–0.040 (≥ 4 orders smaller); no pulse of amplitude 0.03 leaves a durable effect on any base. This is consistent with D1 (no unstable mode at the class-0 or class-1 adult state, SKELETON.md).
2. **Response size** (Frobenius norm of the difference to the twin over positions and secretion levels across the 192-bin window; mean over roles, per channel; channel order pos x, pos y, sec 1–4, gain 1–4):

| base | pos x | pos y | sec 1 | sec 2 | sec 3 | sec 4 | gain 1 | gain 2 | gain 3 | gain 4 |
|---|---|---|---|---|---|---|---|---|---|---|
| C0 | .028 | .040 | .026 | .023 | .024 | .026 | .059 | .034 | .021 | .017 |
| C1 | .034 | .041 | .024 | .024 | .026 | .027 | .063 | .035 | .031 | .026 |
| D16 | .027 | .041 | .022 | .019 | .019 | .020 | .051 | .028 | .019 | .014 |
| D32 | .028 | .040 | .024 | .021 | .022 | .024 | .056 | .032 | .020 | .016 |
| D64 | .028 | .040 | .026 | .023 | .024 | .026 | .059 | .033 | .021 | .017 |
| D128 | .028 | .040 | .026 | .023 | .024 | .026 | .059 | .034 | .021 | .017 |

   Gain 1 and position y are the largest-response channels on every base.
3. **The developmental bases converge on the adult response:** D64 and D128 equal C0 to the printed precision in every channel; D32 is within 10 % (secretion and gain channels up to 9 % smaller); D16 is 4 % smaller on position and 14–18 % smaller on secretion and gain channels. The linear response operator is therefore already adult-like by b ≈ 64 (2 × T_dev), well before the shape itself is stationary (b ≈ 178–192).
4. **Role dependence** (max/min of the role-mean response): C0 1.25, D16–D128 1.24–1.26, **C1 1.90**. On C0 the roles differ little (role means 0.027–0.033). On C1 the role labelled 7 is 0.049 against 0.026–0.037 for the others: the response of the class-1 body is not role-symmetric in the way the class-0 body is, as expected for a body with a duplicated role and an undifferentiated cell. The Hungarian slot labels of C1 are a labelling convention, not a role identity (the body has a vacant and a duplicated slot), so "role 7" on C1 is only a label.
5. **Equivariance under relabelling (verification individual):** for all 80 role × channel pairs, the response of `primary_0001` equals the response of `primary_0000` for the same role to a relative difference with median 2.5e-9 and maximum 2.0e-8. **The role-indexed reduction is exact within numerical error for the class-0 adult** (n = 80 comparisons, one relabelled individual; the individual is the unit, so this is a replication count of 1 beyond the base).
6. **Not found:** no pulse at amplitude 0.03 left a lasting trace (point 1); I did not run the role/shape classifier on these runs, so FATE-SWAP and SHAPE-SWITCH are excluded only through the vanishing final-bin response. The thresholds for those are in MINIMAL_PERTURBATIONS.md, at amplitudes ≈ 100× larger.

## Where the library goes
The library runs are in the blind package as ordinary segments (opaque channel labels CH1–CH10, role maps excluded), together with the D4 TRANSITION DATASET (below). The sealed mapping from package ids to these runs is in `sealed/blind_mapping.json`, not in the package.

### TRANSITION DATASET (D4 run pairs)
For every D4 direction with a threshold: the run at the first amplitude above threshold and the run at the largest tested amplitude below it, for both FATE-SWAP and SHAPE-SWITCH; for directions with no threshold, the run at the maximum amplitude. 390 segments of 2,345 D4 run files (the rest are intermediate bisection runs, not packaged). Outcome labels are not in the package.

### Noisy runs
The R4 noisy runs (long adult runs ×3 noise levels; reduced R2 ADULT under noise) are included, with noise levels as unordered opaque labels NL1–NL3 (34 segments each) and NL0 = canonical zero-noise. They are flagged noise-extended and never mixed with canonical data.
