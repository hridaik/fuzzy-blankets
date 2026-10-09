# MINIMAL_PERTURBATIONS.md — D4: minimal durable interventions by bisection (protocol v2)

Code `code/d4.py`, `d4_dirs.py`, `d4_full.py` (run), `d4_analyze.py`, `d4_md.py` (tables). Raw: `data/v2/d4/dir_*.json` (246 directions; per-evaluation labels), `data/v2/d4_summary.json`, tables `data/v2/d4_tables.md`. Replication of three thresholds on two relabelled individuals: SKELETON.md (D6). Viewer: D4 near-threshold pairs (below/above, synced) in `viz/`, OBSERVABLE and AUDIT.

## What was measured
- **Base state:** the class-0 adult (b = 320, canonical clock, zero process noise). One base state up to relabelling: every individual that reaches class 0 is the same body up to a permutation of cells (CENSUS_V2.md), so **the base-state sample size is 1**; directions are the sampling unit here, not individuals.
- **Intervention:** a transient (displacement: one-shot state edit; pulse: 4-bin secretion window), applied on the continued D-step state, then a 192-bin settle, then classification against the unperturbed twin (THRESHOLDS_v2.md; `tau_pair` = 0.170).
- **Labels:** SAME (shape and roles as the twin), **FATE-SWAP** (shape REVERTED, one or more cells end in a different role), **SHAPE-SWITCH** (shape differs from class 0 by more than `tau_pair`; in every case found it is class 1), NONCONV. All 2,309 evaluations produced SAME (1,611), FATE-SWAP (669) or SHAPE-SWITCH (29); **NONCONV never occurred**.
- **Threshold:** the lowest tested amplitude whose label is not SAME (FATE-SWAP) or is SHAPE-SWITCH, refined by bisection to 1 % in log-amplitude (bracket reported in the per-direction files). If the label is non-monotone in amplitude the lowest crossing is reported and the direction is flagged below.
- **Brackets (declared in COMPUTE_PLAN.md update 2):** displacement 0.05–10 position units (1 unit ≈ 1.14 × mean nearest-neighbour spacing); secretion pulses 0.05–50 (engine units, no calibration to a natural scale). "No threshold" means **none up to the top of the bracket**, not "never".
- **Direction sets (246):** single-cell displacement 128 (8 roles × 16 angles, 22.5° apart); whole-body position displacement 25 (5 slowest class-0 eigen-directions' position parts + 20 random); belief-space displacement 5 (belief parts of the same eigen-directions); single-cell secretion pulses 32 (8 roles × 4 ligand channels); regional pulses 52 (13 centres × 4 ligands, radius 0.88); global pulses 4. "Role" = slot of the perturbed cell in the base body.
- **Declared cuts that limit resolution:** single-cell displacement directions used a **4-point** amplitude grid (others 7-point): a window narrower than a factor ≈ 5.8 in amplitude can be missed, so the number of threshold-bearing displacement directions is a lower bound. Non-monotone windows were found in 29 of 246 directions even so (below).

## Results — minimum / median / maximum threshold per actuator class (ESTABLISHED for this base state and these direction sets)
Medians are over directions that have a threshold; the count of directions without one is the censoring and matters as much as the median.

**FATE-SWAP**
| class | directions | with threshold | min | median | max |
|---|---|---|---|---|---|
| single-cell displacement | 128 | 52 | 0.68 | 4.42 | 8.07 |
| whole-body position, eigen | 5 | 5 | 2.60 | 4.52 | 9.14 |
| whole-body position, random | 20 | 15 | 1.76 | 5.41 | 10.0 |
| whole-body belief-space, eigen | 5 | 1 | 5.80 | 5.80 | 5.80 |
| single-cell secretion pulse | 32 | 11 | 3.28 | 16.5 | 37.8 |
| regional pulse | 52 | 36 | 2.62 | 8.82 | 38.2 |
| global pulse | 4 | 4 | 4.53 | 7.63 | 9.64 |

**SHAPE-SWITCH**
| class | directions | with threshold | min | median | max |
|---|---|---|---|---|---|
| single-cell displacement | 128 | 4 | 1.86 | 5.53 | 9.21 |
| whole-body position, eigen | 5 | 1 | 9.53 | 9.53 | 9.53 |
| whole-body position, random | 20 | 0 | — | — | — |
| whole-body belief-space, eigen | 5 | 0 | — | — | — |
| single-cell secretion pulse | 32 | 0 | — | — | — |
| regional pulse | 52 | 0 | — | — | — |
| global pulse | 4 | 1 | 20.9 | 20.9 | 20.9 |

Ratios (native units, so only within-row comparisons are meaningful): SHAPE-SWITCH / FATE-SWAP is 1.09 (the most sensitive direction: role 7, 22.5° from the axis, 1.71 vs 1.86), 3.3 (global ligand-4: 6.37 vs 20.9), 2.1 (eigen-direction 2: 4.52 vs 9.53) and 7.7 (role 7, 45°: 1.19 vs 9.21). In all six directions that reach SHAPE-SWITCH the FATE-SWAP threshold is lower: **a durable shape change is always preceded, as amplitude grows, by a role swap with unchanged shape.** Within the displacement class the median FATE-SWAP is 4.4 against a minimum of 0.68 (6.5×); the single-cell pulse median / minimum is 5.0×.

## Identity outcome just above each threshold
- **FATE-SWAP:** at the first amplitude above threshold the label is FATE-SWAP in 100 % of directions that have one (52/52, 5/5, 1/1, 15/15, 11/11, 36/36, 4/4). The number of cells whose role changed there: **two (a transposition) in 44 of 52 single-cell displacements**, three in 4, four in 4; in the pulse classes 2–5, mostly 2 (regional: 2 in 22, 3 in 7, 4 in 5, 5 in 2). Shape is unchanged (REVERTED) by definition of the label.
- **SHAPE-SWITCH:** the pipeline's class assignment of the end shape is **class 1 in 6/6 directions** (the `to` field of the per-direction files; I did not re-measure `d_pair` to the class-1 exemplar for these six). Class 1 has a duplicated role, a vacant role and an undifferentiated cell (REANALYSIS.md e). So **no durable shape change without an organisational defect was found anywhere in 246 directions**: the only durable shape change is a switch into the defective second attractor.

## Is any role or region privileged? (ESTABLISHED for these directions; PROVISIONAL as a general statement — one base state, one region radius)
- **Single-cell displacement, FATE-SWAP.** Strongly role-dependent. Role 7 (tail end, on the axis) is the most easily swapped (median 1.45, min 1.19), roles 1 and 5 next (1.67), role 3 (2.55), role 0 (2.57, min 0.68 but only 3 of 16 angles respond). Roles 2, 4 and 6 are the hardest (medians 4.8, 5.9, 5.9; role 2 responds in 14/16 angles, 4 and 6 in 8/16). Max/min of per-role medians **4.05**; of per-role minima **6.35**. The count of angles that respond also differs by role (role 2: 14/16; roles 0, 1, 3, 5, 7: 3–5/16).
- **Single-cell displacement, SHAPE-SWITCH.** **Only role 7 has any** (4/16 angles; the other seven roles: none up to 10). Role 7 is privileged for both thresholds.
- **Single-cell pulses.** Role 3 is the most sensitive (min 3.28; 3 of 4 ligands), roles 1/5 at 8.5, role 2 at 16.5, role 7 at 25.5, roles 4/6 at 35.5–37.8 (2 of 4 ligands), **role 0: no FATE-SWAP up to 50**. Max/min of per-role medians **9.1** (lower bound; role 0 is censored); of minima 10.8. Ligand 4 is the most effective single-cell channel (5/8 directions respond, min 6.67), ligand 1 the least (2/8, 37.8).
- **Regional pulses by centre.** The centres on the axis (y ≈ 0) and the near-axis rows respond to all four ligands, and the minimum threshold rises monotonically with decreasing x: g13 (x = +1.74) 2.62, g10 (+0.86) 3.10, g7 (−0.02) 3.72, g3/g5 (−0.9) 6.37, g0/g2 (−1.78) 7.49 (medians 3.49, 3.41, 4.68, 7.81, 15.4). Off-axis centres respond to only 1–2 ligands, mostly at much larger amplitude (g6/g8 35.5–36.7, g9/g11 16.5). The tail end of the body is therefore the most easily re-assigned region, consistent with role 7 being privileged in displacement. Max/min of per-centre medians (centres with ≥ 1 response; g6/g8 over g10) **10.8**. Regions overlap and a single radius was used, so this is a description of the tested discs, not of a property of the body.
- **Global pulses.** All four ligand channels give FATE-SWAP (4.5, 6.4, 8.9, 9.6); only ligand 4 gives SHAPE-SWITCH (20.9).
- **Mirror check (PASS, 6/6 testable pairs).** Roles 1 and 5 have identical response sets and thresholds; roles 4 and 6 likewise; regional centres g0 = g2, g3 = g5, g6 = g8, g9 = g11 identical to the printed precision. No pair of mirror-image directions disagrees. Within role 7 (self-mirror) the mirror pairs 22.5°/337.5° (1.858) and 45°/315° (9.205) agree exactly. This is expected from the model's y-mirror symmetry and is also a check that the pipeline is symmetric.

## Non-monotone windows
29 of 246 directions have a label that is not monotone in amplitude (e.g. FATE-SWAP in a window, SAME above it): single-cell displacement 13 (roles 4, 6 and 7 among the twelve listed in `data/v2/d4_tables.md`), single-cell pulses 7, regional pulses 7, random whole-body 2. Reported thresholds are the lowest crossing. Windows are narrow relative to the bracket and can be an artefact of the settle-time classification (hypothesis, untested: a transient swap that relaxes after the settle window); **the mechanism is not investigated (NOT DONE)**. The 4-point grid in the displacement class makes this count a lower bound.

## What this does and does not show
- Durable role change (FATE-SWAP) needs a displacement of ≈ 0.7–8 position units from a single cell (≈ 0.8–9 mean neighbour spacings), or a secretion pulse of ≈ 3–38 units; it is reachable from every actuator class at the tested amplitudes, though from only 41 % of single-cell displacement directions and 34 % of single-cell pulse directions.
- Durable shape change is rare: 6 directions in 246, essentially one role (7) and the global ligand-4 channel, and always into class 1. Nothing produced a NOVEL (third) shape or a defect-free alternative.
- Not tested: other base states (class 1 as a base for D4 was not run), amplitudes above the brackets (a "no threshold" direction may switch beyond 10 or 50), combined multi-cell interventions, repeated pulses, noise. The thresholds are for the deterministic engine; the noisy case is not covered (NOISE.md covers withdrawal families only).
- Whether SHAPE-SWITCH thresholds are reached through the unstable direction found by D5 (SKELETON.md: one unstable mode at the edge state, 88 % belief-carried) is consistent with, but not tested by, the D4 directions: the D5 direction is the global ligand-4 pulse.
