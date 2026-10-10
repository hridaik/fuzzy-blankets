# EVENTS AND PAIRS (Part E): frozen pipeline applied to operation / light / device runs

Pairing: **P01-P09** (surgical or merging operations) have full triplets (treated / untreated_control twin / sham_treated): 24 development + 15 held-out groups. **Light runs (T3a, T3b, T4a, T4b)** have no twin: every light run is a different body (120 bodies); treated runs (96 = 56 dev + 40 held-out incl. held-out locations) are compared with the 24 sham runs of the same opaque label (unpaired, body-clustered). **Device runs (X*)** have a single treated run per dish, no twin, no sham: outcomes are described only; no intervention is designed or optimised.
"What happened, when": event flags with first times are in `outputs/<run>.json.gz` (`levels.O1.summary.events`, `frames[].events`); table below gives rates and median delays from the declared onset (negative onset = dish merge already running at the start of observation).
Verdict definitions per founder organism and layer: persist = no failure of that layer's axes at any frame (C1 material axis; C2 count/cohesion/shape/pattern; C3 no state change detected); change = some failure while the lineage is alive at the end (C3: state change detected); break = lineage gone at the end or, for C2/C3, final frame out of distribution (C3 also if organism < 12 cells).

## Event flags (O1; fraction of runs with >= 1 flag; median first-flag delay after onset in time units)
- Natural dishes (200 dev + 60 held-out): no flag of any type at O1 (0 / 260).
- P01 (cut): SPLIT in 6/6 treated runs (dev+held-out), delay 5 (the first frame after the onset frame); twins and shams: none. P02: SPLIT at delay 5 and MERGE at delay 25-85 (fragments re-fuse) in 6/6; P03 (tweezers): EXTRUSION at delay 5 and ARRIVAL at 10-25 (the displaced cell returns) in 6/6; P09 (replacement): LOSS and ARRIVAL together at delay 5 (3 cells replaced; ids change) in 6/6, SPLIT only in dev (delay ~300); P04-P08 (dish merges): SPLIT (usually with MERGE flicker) in 6 of 8 dev and 4 of 7 held-out treated runs (P07, a held-out condition: 2 of 3), EXTRUSION/ARRIVAL in 1 of 2 dev P04 and P06 runs, none of any type in twins/shams.
- Light (T*): **no geometric event flag in any of the 96 treated runs and none in shams** (SPLIT/MERGE/EXTRUSION/ARRIVAL/LOSS all 0). The light operates on structure and state, not material membership.
- Device runs: Xmpipette ARRIVAL (2/2, delay 6), Xsec SPLIT (2/2, delay 22); the other device conditions (Xmig, Xpipette, Xrg, Xbath, Xmbath_*): no flags.
Full table: `results_heldout/event_table.json` (all levels, dev and held-out).

## Reading the verdict tables
Untreated twins and shams are not perfectly stationary relative to the natural calibration: slow drift of left-right pattern features leaves the very tight natural state model in 25-50 % of development twins/shams (C2/C3 "break" = out-of-distribution at the last frame), 0-17 % in held-out. Hence **the paired difference to the twin is the primary quantity**; shams match twins (same V, no events, same number of state-change detections) in 54 % (13/24) of development triplets but 93 % (14/15) of held-out triplets, with sham-minus-twin differences whose CIs cover 0 for V, Jaccard, shape and pattern.


### Per opaque condition and arm - development (O1; founders; proportions, dish-cluster bootstrap CIs in the JSON)

| condition | arm | founders | V | V_cons | C1 persist/change/break | C2 persist/change/break | C3 persist/change/break |
|---|---|---|---|---|---|---|---|
| P01 | sham_treated | 4 | 0.50 | 0.50 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P01 | treated | 4 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P01 | untreated_control | 4 | 0.75 | 0.75 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P02 | sham_treated | 4 | 0.75 | 0.75 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P02 | treated | 4 | 0.00 | 0.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P02 | untreated_control | 4 | 0.50 | 0.50 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P03 | sham_treated | 4 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P03 | treated | 4 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/0.50/0.50 | 0.50/0.00/0.50 |
| P03 | untreated_control | 4 | 0.50 | 0.50 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P04 | sham_treated | 4 | 0.75 | 0.75 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P04 | treated | 2 | 0.00 | 0.00 | 0.00/0.50/0.50 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P04 | untreated_control | 4 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P05 | sham_treated | 4 | 0.75 | 0.75 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P05 | treated | 3 | 0.00 | 0.00 | 0.67/0.33/0.00 | 0.00/1.00/0.00 | 0.33/0.67/0.00 |
| P05 | untreated_control | 4 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P06 | sham_treated | 4 | 0.75 | 0.75 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P06 | treated | 2 | 0.00 | 0.00 | 0.00/0.50/0.50 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P06 | untreated_control | 4 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P08 | sham_treated | 4 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P08 | treated | 3 | 0.00 | 0.00 | 0.67/0.33/0.00 | 0.00/1.00/0.00 | 0.33/0.67/0.00 |
| P08 | untreated_control | 4 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.75/0.00/0.25 | 0.75/0.00/0.25 |
| P09 | sham_treated | 4 | 0.75 | 0.75 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| P09 | treated | 4 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/0.50/0.50 | 0.00/0.50/0.50 |
| P09 | untreated_control | 4 | 0.50 | 0.50 | 1.00/0.00/0.00 | 0.50/0.00/0.50 | 0.50/0.00/0.50 |
| T3a | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.67/0.00/0.33 | 0.67/0.00/0.33 |
| T3a | treated | 11 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/1.00/0.00 | 0.18/0.82/0.00 |
| T3b | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T3b | treated | 11 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.82/0.18 | 0.18/0.64/0.18 |
| T4a | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.67/0.00/0.33 | 0.67/0.00/0.33 |
| T4a | treated | 11 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.73/0.27 | 0.09/0.64/0.27 |
| T4b | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T4b | treated | 11 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.73/0.27 | 0.18/0.55/0.27 |
| Xmbath_high | treated | 2 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 |
| Xmig | treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| Xmpipette | treated | 2 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 | 1.00/0.00/0.00 |
| Xpipette | treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| Xrg | treated | 2 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 |
| Xsec | treated | 2 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 |

Dissociation of (C1/C2/C3) among treated/device founders (O1): persist/change/change: 35; change/break/break: 10; persist/change/persist: 9; persist/break/break: 8; break/break/break: 6; change/change/change: 6; change/change/persist: 4; persist/persist/persist: 4

### Paired differences treated - twin and sham - twin (development; 24 triplets, pooled; cluster = triplet group)

| level | quantity | treated - twin [95 % CI] | sham - twin [95 % CI] |
|---|---|---|---|
| O1 | V (founder fraction) | -0.71 [-0.88, -0.54] | 0.06 [-0.12, 0.27] |
| O1 | V_conservative | -0.71 [-0.88, -0.50] | 0.06 [-0.12, 0.27] |
| O1 | min Jaccard to initial members | -0.38 [-0.47, -0.29] | 0.00 [0.00, 0.00] |
| O1 | max shape deviation | 0.48 [0.36, 0.59] | 0.00 [-0.00, 0.00] |
| O1 | max pattern deviation | 13.04 [9.75, 16.75] | -0.02 [-0.06, 0.02] |
| O1 | state-change detections | 27.83 [10.00, 44.55] | 0.54 [-0.21, 1.67] |
| O2 | V (founder fraction) | -0.58 [-0.75, -0.40] | 0.00 [0.00, 0.00] |
| O2 | V_conservative | -0.58 [-0.77, -0.40] | 0.00 [0.00, 0.00] |
| O2 | min Jaccard to initial members | -0.42 [-0.53, -0.31] | 0.00 [0.00, 0.00] |
| O2 | max shape deviation | 0.44 [0.31, 0.58] | 0.00 [-0.00, 0.00] |
| O2 | max pattern deviation | 12.84 [8.84, 16.78] | -0.02 [-0.07, 0.03] |
| O2 | state-change detections | 19.25 [1.58, 37.42] | 0.88 [-0.25, 2.08] |
| O3b | V (founder fraction) | -0.35 [-0.54, -0.17] | -0.02 [-0.06, 0.00] |
| O3b | V_conservative | -0.35 [-0.54, -0.17] | -0.02 [-0.06, 0.00] |
| O3b | min Jaccard to initial members | -0.24 [-0.35, -0.14] | -0.00 [-0.01, 0.00] |
| O3b | max shape deviation | 0.21 [0.03, 0.42] | -0.07 [-0.18, 0.03] |
| O3b | max pattern deviation | 1.29 [0.26, 2.52] | 0.04 [-0.07, 0.16] |
| O3b | state-change detections | 6.21 [-2.67, 15.79] | 0.67 [-1.54, 3.04] |

Shams matching their twins (same V, no event flags, same number of state-change detections) at O1: 0.54 of 24 triplets.

### Per opaque condition and arm - held-out (O1; founders; proportions, dish-cluster bootstrap CIs in the JSON)

| condition | arm | founders | V | V_cons | C1 persist/change/break | C2 persist/change/break | C3 persist/change/break |
|---|---|---|---|---|---|---|---|
| P01 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P01 | treated | 2 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P01 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P02 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P02 | treated | 2 | 0.00 | 0.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P02 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P03 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P03 | treated | 2 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 | 1.00/0.00/0.00 |
| P03 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P04 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P04 | treated | 2 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/1.00/0.00 | 1.00/0.00/0.00 |
| P04 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P05 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P05 | treated | 1 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 | 0.00/1.00/0.00 |
| P05 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P06 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P06 | treated | 2 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/1.00/0.00 | 1.00/0.00/0.00 |
| P06 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P07 | sham_treated | 6 | 1.00 | 1.00 | 1.00/0.00/0.00 | 0.83/0.00/0.17 | 0.83/0.00/0.17 |
| P07 | treated | 4 | 0.00 | 0.00 | 0.50/0.50/0.00 | 0.00/1.00/0.00 | 1.00/0.00/0.00 |
| P07 | untreated_control | 6 | 0.83 | 0.83 | 1.00/0.00/0.00 | 0.83/0.00/0.17 | 0.83/0.00/0.17 |
| P08 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P08 | treated | 1 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/0.00/1.00 | 0.00/0.00/1.00 |
| P08 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P09 | sham_treated | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| P09 | treated | 2 | 0.00 | 0.00 | 0.00/1.00/0.00 | 0.00/0.50/0.50 | 0.00/0.50/0.50 |
| P09 | untreated_control | 2 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T3a | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T3a | treated | 13 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.77/0.23 | 0.08/0.69/0.23 |
| T3b | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T3b | treated | 13 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.92/0.08 | 0.23/0.69/0.08 |
| T4a | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T4a | treated | 13 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.69/0.31 | 0.15/0.54/0.31 |
| T4b | sham_treated | 3 | 1.00 | 1.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 | 1.00/0.00/0.00 |
| T4b | treated | 13 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.92/0.08 | 0.15/0.77/0.08 |
| Xbath | treated | 2 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/1.00/0.00 | 1.00/0.00/0.00 |
| Xmbath_low | treated | 2 | 0.00 | 0.00 | 1.00/0.00/0.00 | 0.00/0.50/0.50 | 0.50/0.00/0.50 |

Dissociation of (C1/C2/C3) among treated/device founders (O1): persist/change/change: 35; persist/change/persist: 17; persist/break/break: 10; change/break/break: 4; change/change/persist: 4; break/break/break: 2; change/change/change: 2

### Paired differences treated - twin and sham - twin (held-out; 15 triplets, pooled; cluster = triplet group)

| level | quantity | treated - twin [95 % CI] | sham - twin [95 % CI] |
|---|---|---|---|
| O1 | V (founder fraction) | -0.97 [-1.00, -0.90] | 0.03 [0.00, 0.10] |
| O1 | V_conservative | -0.97 [-1.00, -0.90] | 0.03 [0.00, 0.10] |
| O1 | min Jaccard to initial members | -0.32 [-0.44, -0.19] | 0.00 [0.00, 0.00] |
| O1 | max shape deviation | 0.40 [0.25, 0.56] | 0.00 [-0.00, 0.00] |
| O1 | max pattern deviation | 12.79 [7.34, 18.30] | -0.01 [-0.08, 0.05] |
| O1 | state-change detections | 30.27 [6.07, 56.07] | -0.13 [-0.40, 0.00] |
| O2 | V (founder fraction) | -0.97 [-1.00, -0.90] | 0.03 [0.00, 0.10] |
| O2 | V_conservative | -0.97 [-1.00, -0.90] | 0.03 [0.00, 0.10] |
| O2 | min Jaccard to initial members | -0.26 [-0.39, -0.15] | 0.00 [0.00, 0.00] |
| O2 | max shape deviation | 0.34 [0.18, 0.51] | 0.00 [-0.00, 0.00] |
| O2 | max pattern deviation | 10.93 [5.05, 16.76] | -0.03 [-0.11, 0.05] |
| O2 | state-change detections | 21.00 [0.27, 43.00] | -0.47 [-1.40, 0.00] |
| O3b | V (founder fraction) | -0.20 [-0.47, 0.07] | 0.00 [0.00, 0.00] |
| O3b | V_conservative | -0.20 [-0.47, 0.07] | 0.00 [0.00, 0.00] |
| O3b | min Jaccard to initial members | -0.22 [-0.36, -0.09] | -0.01 [-0.03, 0.00] |
| O3b | max shape deviation | -0.00 [-0.22, 0.24] | -0.03 [-0.13, 0.08] |
| O3b | max pattern deviation | 0.96 [-0.51, 2.81] | 0.05 [-0.14, 0.22] |
| O3b | state-change detections | 13.00 [0.73, 26.33] | -1.93 [-7.60, 3.27] |

Shams matching their twins (same V, no event flags, same number of state-change detections) at O1: 0.93 of 15 triplets.

## Do layers dissociate? (answers)
- **How often does each layer persist, change, or break?** Treated founders, O1, dev + held-out (see the per-condition tables): C1 persists in all light-treated runs (96/96) and in 12 of 16 device founders, changes or breaks in all cut / replacement / tweezer / merge runs with a flag (turnover or fragmentation); C2 persists in only 4 of 156 treated founders (the four development Xmig/Xpipette founders), all others leave the envelope by shape or pattern; C3 persists in 8-23 % of light runs, changes (new state or OOD) in 54-82 %, breaks (organism too small, OOD at the end) in 0-31 %.
- **Dissociations**: the commonest pattern among treated/device founders is *material persists, structure changes, state changes* (persist/change/change: 35 dev, 35 held-out) and *material persists, structure changes, state persists* (9 dev, 17 held-out: held-out P03/P04/P06/P07, Xbath, development Xmpipette and a minority of light runs: a structural change without a state change). Material turnover with preserved *structure* never occurs (no change/persist/* combination): whenever C1 changes, C2 also fails. Material change with a preserved *state label* does occur (change/change/persist: 4 dev + 4 held-out founders). The converse dissociation, state or structure change without any material change, is the dominant light-run outcome.
- O2 reproduces O1's tables closely (differences in V of 0.0 for shams, treated-minus-twin V -0.58 dev / -0.97 held-out), O3b is weaker (V difference -0.35 dev, -0.20 held-out with CI covering 0) because its structural axes are loose (CALIBRATION.md).

## Known issues found after the freeze (reported, not fixed; frozen code kept)
- **B1 - repeated change records.** `states.change_times` appends a record at every frame while the filtered label stays OOD (-1) (the "current" label is not updated for OOD). Consequences: `state_changes` lists and the "state-change detections" rows in the paired table are inflated frame counts, not event counts. Unaffected: any-change flags (persist/change/break verdicts), first change time, `state_first/state_last`. Corrective reporting-only measure (`post_freeze/episodes.py`, number of consecutive-label transitions per founder, treated minus twin, pooled over triplets, 95 % cluster CI): **O1: +1.96 [0.67, 3.46] dev, +1.13 [0.60, 1.80] held-out; O2: +0.25 [-0.88, 1.38] dev, +0.87 [0.33, 1.60] held-out; sham minus twin about 0 (-0.08 [-0.25, 0], +0.13 [0, 0.40])** (`results_heldout/state_transition_pairs.json`).
- B2 - the sham-match criterion used in the tables (equal V, no flags, equal number of change records) is sensitive to B1; the V-only agreement is higher.
