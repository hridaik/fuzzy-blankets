# IDENTITY LAYERS (Part C) - material C1, structural C2, collective state C3, never folded into one score

## Layers (per organism lineage; reference = first frame of the lineage; every value causal)
- **C1 material**: Jaccard and Dice of member-id sets vs the initial set (`J_init`, `D_init`) and vs the previous frame (`J_prev`). O1: cell ids; O2: tracker ids; O3: foreground-pixel overlap (field-level proxy, NOT cell material - labelled).
- **C2 structural**: n cells (O3: mass estimate), cohesion (largest MST bridge and #components at r_coh=1.42), moment shape (s1,s2; shape deviation = hypot of log-ratios to the reference), channel-pattern descriptors in the body frame (mean, slope along the axis, left-right dipole [reflection-sensitive], |q| dipole [invariant], tail-head contrast per channel), Procrustes distance to the reference with rotation only and with reflection allowed (O1/O2).
- **C3 collective state**: label + posterior from the online estimator (STATES.md); -1 = out of distribution, -2 = organism < 12 cells.

## Reflection invariance (empirical)
- Within a dish, rotation-only and reflection-allowed Procrustes distances are **identical** in all 1820 natural frame comparisons (O1): no mirror flip ever happens inside a natural dish, and a reflection-invariant shape distance cannot see mirror-image bodies.
- Across dishes the two common organisations are mirror images that **only reflection-sensitive descriptors separate** (STATES.md): invariant descriptors give k = 1 at O2 and k = 1 at O3a, sensitive descriptors give 4 and 2 states with half-split ARI 0.97. Where c4/c5 (reflection-invariant channels) are visible (O1, O3b) the invariant descriptors also find the pair (k = 3, 3).
- In treated P runs (cut / replace / tweezers), 12 % of frames need the reflection to align with the initial shape (rot - refl > 0.05): fragments become ambiguous, not mirrored; we do not interpret this as chirality.
**Answer: they differ on natural data across dishes (not within a dish). The primary C2 shape axis is the rotation-invariant moment descriptor (reflection-neutral); the state descriptors include the sensitive family.**

## V / V_conservative
V = lineage alive at the end and all five axes pass at every frame since birth (per-axis verdicts stored per frame in `axis_pass`, first failure frame in `axis_first_fail_k`). V_conservative additionally requires no SPLIT, MERGE or UNRESOLVED on the lineage. Founders = lineages present at frame 0 (all scores below are for founders; children of splits are reported but excluded because they are new bodies). Conservative is primary; here V and V_conservative coincide in the vast majority of lineages because any SPLIT/MERGE also breaks a bound.

## Natural-dish validity (target 90 % pass; `results_heldout/natural_validity.json`)
| split | O1 | O2 | O3a | O3b |
|---|---|---|---|---|
| dev calibration (100) | 0.90 | 0.90 | 0.90 | 0.90 |
| dev validation (100) | 0.97 | 0.93 | 0.90 | 0.90 |
| held-out natural (60) | 0.90 [0.82,0.97] | 0.85 [0.75,0.93] | 0.93 [0.87,0.98] | 0.87 [0.77,0.95] |
Median fraction of natural dishes with any state change: 2-10 % (dev), 2-5 % (held-out). Axis-level failure rates on validation: shape 3-5 %, pattern 1-5 %, material/count 0 % at O1/O2.

## Per-layer outcomes in intervention runs (O1; founders; dev + held-out) - see EVENTS_AND_PAIRS.md for tables.
