# INVENTORY (Part A) — from DATA_DICTIONARY.md, catalog.csv, split_manifest.json, treatments.json

## Observation levels (all four files exist for every one of the 513 runs)
| level | content | cell ids | signal channels | notes |
|---|---|---|---|---|
| O1 | tracked cells: xy (noise sd 0.02), level (7 cols, mult. noise 3 %) | yes (permanent, new cell = new id) | 7 (cols 0-6) | frame_ptr ragged arrays |
| O2 | unlabelled points, rows shuffled each frame | no | 5 (O1 cols 0,1,2,3,6) | cols 4,5 not assayed |
| O3a | images (frames,3,64,64) f16, window [-fov,fov]^2, PSF sd 0.5, peak SNR 20 | no | 3: O1 cols 6,2,0 (that order) | every `o3_every`-th frame |
| O3b | images with 4th channel | no | 4: cols 6,2,0,4 | as O3a |

Frame interval: natural dishes 100 (8 frames/dish); operation (P*) runs 5 (120 frames, onset 50 or -100 for dish merges);
light (T*) runs 2 (58 or 68 frames, onset 10); device (X*) runs 2 (80 frames, onset 10). Natural dishes 24 cells, fov 12.
Dish-merge (P04-P08) runs: 48 cells, fov 30. Total 513 runs.

## Run kinds and splits (count of runs)
| condition | arm | split | n | n_cells | n_frames | dt | fov |
|---|---|---|---|---|---|---|---|
| N0 | untreated | development | 200 | 24 | 8 | 100.0 | 12.0 |
| N0 | untreated | heldout_bodies | 60 | 24 | 8 | 100.0 | 12.0 |
| P01 | sham_treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P01 | sham_treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P01 | treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P01 | treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P01 | untreated_control | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P01 | untreated_control | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P02 | sham_treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P02 | sham_treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P02 | treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P02 | treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P02 | untreated_control | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P02 | untreated_control | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P03 | sham_treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P03 | sham_treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P03 | treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P03 | treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P03 | untreated_control | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P03 | untreated_control | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P04 | sham_treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P04 | sham_treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P04 | treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P04 | treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P04 | untreated_control | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P04 | untreated_control | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P05 | sham_treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P05 | sham_treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P05 | treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P05 | treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P05 | untreated_control | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P05 | untreated_control | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P06 | sham_treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P06 | sham_treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P06 | treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P06 | treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P06 | untreated_control | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P06 | untreated_control | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P07 | sham_treated | heldout_conditions | 3 | 48 | 120 | 5.0 | 30.0 |
| P07 | treated | heldout_conditions | 3 | 48 | 120 | 5.0 | 30.0 |
| P07 | untreated_control | heldout_conditions | 3 | 48 | 120 | 5.0 | 30.0 |
| P08 | sham_treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P08 | sham_treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P08 | treated | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P08 | treated | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P08 | untreated_control | development | 2 | 48 | 120 | 5.0 | 30.0 |
| P08 | untreated_control | heldout_bodies | 1 | 48 | 120 | 5.0 | 30.0 |
| P09 | sham_treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P09 | sham_treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P09 | treated | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P09 | treated | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| P09 | untreated_control | development | 4 | 24 | 120 | 5.0 | 12.0 |
| P09 | untreated_control | heldout_bodies | 2 | 24 | 120 | 5.0 | 12.0 |
| T3a | sham_treated | development | 3 | 24 | 58 | 2.0 | 12.0 |
| T3a | sham_treated | heldout_bodies | 1 | 24 | 58 | 2.0 | 12.0 |
| T3a | sham_treated | heldout_locations | 2 | 24 | 58 | 2.0 | 12.0 |
| T3a | treated | development | 11 | 24 | 58 | 2.0 | 12.0 |
| T3a | treated | heldout_bodies | 5 | 24 | 58 | 2.0 | 12.0 |
| T3a | treated | heldout_locations | 8 | 24 | 58 | 2.0 | 12.0 |
| T3b | sham_treated | development | 3 | 24 | 68 | 2.0 | 12.0 |
| T3b | sham_treated | heldout_bodies | 1 | 24 | 68 | 2.0 | 12.0 |
| T3b | sham_treated | heldout_locations | 2 | 24 | 68 | 2.0 | 12.0 |
| T3b | treated | development | 11 | 24 | 68 | 2.0 | 12.0 |
| T3b | treated | heldout_bodies | 5 | 24 | 68 | 2.0 | 12.0 |
| T3b | treated | heldout_locations | 8 | 24 | 68 | 2.0 | 12.0 |
| T4a | sham_treated | development | 3 | 24 | 58 | 2.0 | 12.0 |
| T4a | sham_treated | heldout_bodies | 1 | 24 | 58 | 2.0 | 12.0 |
| T4a | sham_treated | heldout_locations | 2 | 24 | 58 | 2.0 | 12.0 |
| T4a | treated | development | 11 | 24 | 58 | 2.0 | 12.0 |
| T4a | treated | heldout_bodies | 5 | 24 | 58 | 2.0 | 12.0 |
| T4a | treated | heldout_locations | 8 | 24 | 58 | 2.0 | 12.0 |
| T4b | sham_treated | development | 3 | 24 | 68 | 2.0 | 12.0 |
| T4b | sham_treated | heldout_bodies | 1 | 24 | 68 | 2.0 | 12.0 |
| T4b | sham_treated | heldout_locations | 2 | 24 | 68 | 2.0 | 12.0 |
| T4b | treated | development | 11 | 24 | 68 | 2.0 | 12.0 |
| T4b | treated | heldout_bodies | 5 | 24 | 68 | 2.0 | 12.0 |
| T4b | treated | heldout_locations | 8 | 24 | 68 | 2.0 | 12.0 |
| Xbath | treated | heldout_conditions | 2 | 24 | 80 | 2.0 | 12.0 |
| Xmbath_high | treated | development | 2 | 24 | 80 | 2.0 | 12.0 |
| Xmbath_low | treated | heldout_conditions | 2 | 24 | 80 | 2.0 | 12.0 |
| Xmig | treated | development | 2 | 24 | 80 | 2.0 | 12.0 |
| Xmpipette | treated | development | 2 | 24 | 80 | 2.0 | 12.0 |
| Xpipette | treated | development | 2 | 24 | 80 | 2.0 | 12.0 |
| Xrg | treated | development | 2 | 24 | 80 | 2.0 | 12.0 |
| Xsec | treated | development | 2 | 24 | 80 | 2.0 | 12.0 |

## Structure
- Natural (N0): 260 untreated dishes; 200 `development`, 60 `heldout_bodies` (validation bodies 400-429 per manifest).
- Event triplets: P01-P09 (surgery cut / replacement / tweezers / dish merge...): each group = treated + untreated_control (twin, same random circumstances) + sham_treated.
  Full triplets (treated + untreated_control + sham_treated, same group) exist only for P01-P09 (39 groups). Light runs (T*) have treated and sham runs in separate catalog groups (24 sham-only groups); pairing is by body_id (to be verified in EVENTS_AND_PAIRS.md). X* runs have no twin.
- Light runs T*: treated (many light codes/locations) and sham.
- Device runs X*: treated only, opaque labels (Xbath, Xmbath_*, Xmig, Xmpipette, Xpipette, Xrg, Xsec); no twin.
- Hidden-split categories: heldout_bodies, heldout_conditions (P07, Xbath, Xmbath_low), heldout_locations (some light runs).
- Observed in development data (my own look, not given): natural bodies are elongated clusters; a head-like end with a 3-type signature and a graded col-6 level along the major axis.
