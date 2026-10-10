# TRACKING (Part B)

## Definitions declared before calibration (geometric)
Organism = single-linkage component of cell positions at r_link (with hysteresis), >= m_min=3 cells. Events at frame t compared to t-1 (member sets):
- SPLIT: an organism's members form >= 2 components each with >= m_min of its members; the larger piece keeps the id, other pieces get new ids (event SPLIT_CHILD). UNRESOLVED if the two largest pieces differ by < 0.15 |P|.
- MERGE: a component receives >= m_min members from >= 2 organisms; the organism with the largest contribution (claimed first by overlap) continues, the others end (END_MERGED). UNRESOLVED if the top two contributions differ by < 0.15 of the larger.
- EXTRUSION: a former member that is observed at t but no longer in the organism (and not part of a split piece); LOSS: a former member that is no longer observed; ARRIVAL: a member not in the organism at t-1 (flag `new` if the id was never seen inside an organism); BIRTH: a new group without a source.
At O3 cell-level EXTRUSION/ARRIVAL/LOSS cannot be defined; ARRIVAL/LOSS are replaced by mass-based flags (|change of integrated-mass count| >= 1.5 cells, `mass_based: true`); EXTRUSION: NOT DONE.
Online principle: claims by overlap size are made at each frame and never revised; no later frame is consulted. Causality verified by test (stage-1 members/events and stage-2 layer/state fields at frame k on a truncated recording equal those on the full recording).

## Calibration and false-flag rate on natural dishes
r_link chosen so that <= 1 % natural calibration dishes break; observed on 260 natural dishes (dev 200 + held-out 60): 0 SPLIT/MERGE/EXTRUSION/ARRIVAL/LOSS flags at O1; 0 SPLIT/MERGE at O2 and O3; one dev dish (0.5 %) with a spurious ARRIVAL+LOSS pair at O2 and one dev dish with a mass-based LOSS at O3b (body at the window edge); none in the 60 held-out dishes at any level.

## Internal consistency (O2 / O3 vs O1; `scripts/consistency.py`; dev | held-out)
| | O2 natural | O2 ops (P*) | O2 light/device | O3a natural | O3 ops (P*) | O3 light/device |
|---|---|---|---|---|---|---|
| runs | 200 \| 60 | 72 \| 45 | 68 \| 68 | 200 \| 60 | 72 \| 45 | 68 \| 68 |
| organism count agrees with O1 (frames) | 1.00 \| 1.00 | 0.999 \| 1.00 | 1.00 \| 1.00 | 1.00 \| 1.00 | 0.83 \| 0.82 | 0.98 \| 0.99 |
| correct cell links vs O1 | 1.000 \| 1.000 | 0.989 \| 0.994 | 0.996 \| 0.997 | n/a | n/a | n/a |
| centroid error (median, units) | 0.00 | 0.00 | 0.00 | 0.74 \| 0.72 | 0.73 \| 0.94 | 0.79 \| 0.72 |
| axis |cos| (median) | 1.00 | 1.00 | 1.00 | 0.955 \| 0.945 | 0.93 \| 0.93 | 0.97 \| 0.96 |
| orientation sign agrees with O1 | 1.00 | 1.00 | 1.00 | 0.991 \| 0.985 | 0.90 \| 0.91 | 0.99 \| 0.99 |
| cell-count error (mean) | 0 | -0.003 | 0 | -1.0 \| -0.9 | -1.2 \| +0.9 (abs 4.4) | -0.65 \| -0.80 |
| SPLIT matched (O1 count) | - | 52/58 \| 6/8 | 2/2 \| 0 | - | O3a 3/58, O3b 6/58 \| 2/8 | 0/2 \| - |
| MERGE matched | - | 32/32 \| 2/2 | - | - | 2-3/32 \| 2/2 | - |
O3 segmentation (pseudo-cells vs O1 cells, optimal assignment): mean distance 1.25 (natural, dev), 1.27 (held-out), 1.1-1.4 (operations, light); count error -1.07 +- 0.40 (natural). Position error is about one cell spacing: **cell-level segmentation at O3 is at the resolution limit; cell identity is not recoverable (negative result).** The count is good (mass-based); body-level quantities are good; the bias of the centroid (0.7 units) is the shift of the intensity centroid relative to the cell centroid.
O3 count error grows with distance of the body from the image centre (centroid |max coordinate| 0-2: -0.6 cells; 4-6: -2; 6-8: -5; > 8: -13) because the halo leaves the window and the far-field background estimate is contaminated.

## Where O2 fails
At the operation frame the cells jump (up to 8.7 units, signal changes up to 1.7 between consecutive frames): continuity is physically absent. The tracker then creates LOSS/ARRIVAL/BIRTH records at O2 (and the block-displacement vote re-links most of a moved fragment: 16 -> 8 wrong links in the P01 example). These frames are flagged, not hidden (O2 LOSS/ARRIVAL events in P01/P02 treated runs, none in twins/shams).
