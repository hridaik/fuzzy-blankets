# Seed 502 — chronological audit

Sources: as `seed_500.md`, seed 502 files. `FIVE_SEED_CAUSAL_ADJUDICATION.md`
"Seed 502"; `LINEAGE_FORENSICS_6_11.md` §§1,2,6; `data/material_retention_seed502.csv`.

## Timeline

| event | t |
|---|---|
| qualification / target set | 30 (`target_heading=1` down, current-dir=2; trigger interior size 21) |
| control window | 30–52 |
| release begin | 53 |
| episode end | 77 |

**Original v1 label: turn.** One of the two seeds withdrawn by
ID-independent rescoring.

## Pre-qualification identity churn

`LINEAGE_FORENSICS_6_11.md` §6: qualified at t=30, **4** MAP-hid switches
before qualification (t=2,5,20,26).

## Genuine zero-overlap discontinuities during control/release

This audit's frame-to-frame cross-check finds **three** zero-overlap
events for this seed: **t=32 (control window), t=52 (last control step /
control-release boundary), t=68 (release window)** — i.e. this seed shows
zero-overlap breaks both entering and exiting the control window, and again
well into release. This is the most materially-discontinuous of the three
"turn"-labelled seeds by this specific count (501 has one such event inside
0–52; 503 has two).

## Rescoring outcome (`branch_adjudication_611__seed502.json`)

Zero true direct causal parents (oracle pool 18). `beam_search_benchmark`
v1 shows a modest rise (0.10→0.28) that v2/material/field-direction (0.02,
0.00, 0.02) do not corroborate at all. `original_reproduced` shows **no**
rise by any readout under fresh CRN — this sample path did not even
reproduce the original transient effect.

## Separate conclusions

- **Physical turn**: not established from the v1 record alone — three
  separate zero-overlap discontinuities (t=32, 52, 68) mean the "turning"
  object displayed at any late point in the episode cannot be assumed to be
  materially the qualified t=30 object without an explicit forward
  lineage trace (Step 2 work).
- **Material/organizational continuation**: no — the most discontinuous of
  the three original "successes" by this pass's frame-level count.
- **Persistence after release**: `original_reproduced`'s own v1 number is
  flat at 0.00 at release; no branch shows a persistent rise on any readout.
- **Intervention-effect evidence**: none — even the least-repaired
  reproduction shows nothing.
- **Actuator-selection-specificity evidence**: none — all repaired branches
  abstain.

## v1 vs. later-rescore vs. physical-reconstruction

- v1: turn. Later rescoring: not demonstrated controllable. This pass:
  consistent with the rescoring's skepticism — the DISPLAYED object is
  materially the most fractured of the three "success" seeds, and no
  readout (old or repaired) shows a persistent, corroborated rise. No
  contradiction found; this pass adds material-discontinuity evidence
  supporting the withdrawal, without independently re-deriving whether a
  correctly-traced continuing lineage would show a different picture
  (open, per `seed_501.md`'s same caveat).
