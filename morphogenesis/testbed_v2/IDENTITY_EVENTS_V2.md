# IDENTITY_EVENTS_V2.md — Gate G4 (v1 Part I protocols under the v2 model; deterministic, one body per condition)

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/g4.py`, `code/world2.py`; data `data/g4a_replace.json`, `g4b_serial.json`, `g4c_extrude.json`, `g4d_cut.json`, `g4e_fuse.json`. Same protocols as v1 (replacement 400 tu; serial: one replacement per 100 tu in random order then 400 tu; extrusion 8 units outward, 300 tu; cut: separation 7, 400 tu; fusion offsets 9, 8, (8,3), 400 tu), plus a 1,500 tu late read for cut and fusion. Naive cell: logits N(0,1/8), secretion 0, l = 0 (ρ = ½). Shape classes: L / R / other / DEFECT (fragmentation, extrusion, incomplete orbits) / fragment.

| event | v2 result | v1 |
|---|---|---|
| single replacement (24 cells) | **14/24 end as complete L** (6 DEFECT, 4 other); naive cell takes its place (belief > 0.5) in 11/24; by type: tail (type 4) 8/8 repaired, trunk 3/4, head 2/8, limb 1/4 | 9/24 |
| extrusion (24 cells) | cell rejoins in 24/24; body ends L in **15/24** (7 DEFECT, 2 other) | 13/24 |
| serial replacement, 4 seeds | **0/4 complete** (DEFECT in all; 2–9 slots filled; 3–7 components); all 24 ids new, 24 unique | 0/4 |
| cut (±y, x) | **±y cut: both fragments disintegrate and the cells disperse ballistically (speed ≈ 1 per tu; extents 240–355 at 400 tu; each fragment in ≥ 2 pieces)**. **x cut: head and tail fragments (12 + 12) stay compact (3.9 × 1.7 and 2.5 × 2.5) and drift apart slowly (centroid separation 11 → 19 over 400 tu)**: no regeneration of the missing half, no re-fusion | pieces re-contacted and interpenetrated, whole body DEFECT |
| fusion L+L, L+R (offsets 9, 8, (8,3)) | **bodies do not merge; in 4/6 runs (offsets 9 and 8) both bodies keep their own complete shape (L, or R for the second body of L+R; at offset 9 the second body fills 22 of 24 places)**; at offset (8,3) the second body is DEFECT (3 components in total) | all defective |

## Handedness outcomes (the identity questions about a collective memory)
* **Does each fragment keep its memory? Yes, passively.** Cut fragments keep exactly their ρ: y-cut L body ρ 0.81/0.76 before → 0.81/0.77 after → 0.80/0.76 at +1,500 tu; x-cut 0.74/0.82 → 0.74/0.82 → 0.74/0.82; R bodies mirrored (0.19–0.26). The fragments do not re-express the missing half, and the body-row types of each fragment stay as before.
* **L+R fusion: no handedness wins.** The L body keeps ρ 0.78 and the R body ρ 0.22 through 1,900 tu at every offset; they are separate intact bodies that do not interact at these offsets (the kernel range ≈ 1; separation ≥ 8 − 7.2 ≈ 1 at offset 8). L+L likewise.
* **Serial replacement:** body-row cells that are replaced re-adopt the surviving handedness: frac_L of body-row types = 1.0 in 3/4 seeds (0.8 in one); mean ρ 0.68–0.73. The handedness persists in the population while the body shape (place assignments) is lost — handedness is easier to keep than the place structure.
* Replacement: the naive cell starts at ρ = ½ and ends with ρ ≈ 0.5 (far-cell places), 0.93–1.0 (cells with morphological evidence); in all 24 runs the body-row types stay L (frac_L = 1).
Caveat: single deterministic body per condition; the fusion offsets were placed so the bodies touch only at ≈ 1 unit; closer or rotated fusions were not explored. v1's "interpenetration" is not reproduced in v2 — the v2 bodies do not penetrate at these offsets (PROVISIONAL: one placement set).
