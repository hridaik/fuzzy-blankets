# Seed 501 — chronological audit

Sources: as `seed_500.md`, seed 501 files. `FIVE_SEED_CAUSAL_ADJUDICATION.md`
"Seed 501" section; `LINEAGE_FORENSICS_6_11.md` §§1,2,6; this audit's
`data/material_retention_seed501.csv`, `plots/seed501_material_retention_and_heading.png`.

## Timeline

| event | t |
|---|---|
| qualification / target set | 30 (`target_heading=2` left, current-dir observed=0; trigger interior size 30) |
| control window | 30–52 (23 steps) |
| release begin | 53 |
| episode end | 77 |

**Original v1 label: turn.** `RESULTS_6_11.md` reports this as one of the
"3/5 turned." **This is one of the two seeds withdrawn by ID-independent
rescoring** (`FIVE_SEED_CAUSAL_ADJUDICATION.md`).

## Pre-qualification identity churn

`LINEAGE_FORENSICS_6_11.md` §6: qualified at t=30, **5** MAP-hid switches
before qualification (t=2,3,11,12,17) — the target-setting interior arrived
via multiple cross-branch overtakes before control even began, same class
of mechanism as seed 500's t=21/t=39 events.

## Genuine zero-overlap discontinuity DURING the control window

This audit's frame-to-frame cross-check
(`data/material_retention_seed501.csv`, `overlap_zero_displayed`) finds a
**zero-overlap event at t=32 — inside the control window (30–52), two steps
after control began.** This is a NEW finding of this pass (not previously
tabulated as "inside vs. outside control" in `LINEAGE_FORENSICS_6_11.md`,
which counts unusual transitions per seed but does not phase-stamp them
individually in its summary table). Practical meaning: **whatever entity is
displayed as "the interior" from t=32 onward shares zero bird IDs with the
entity that was present at t=31 and at qualification (t=30)** — i.e. even
before considering the later ID-independent rescoring, the DISPLAYED v1
object being "controlled" is not materially continuous with the qualified
object for the bulk of the control window.

Two more zero-overlap events occur later, per `LINEAGE_FORENSICS_6_11.md`
§1's flag list (t=36 also flagged for this seed, by the broader
retain<0.40/deform>0.30 criteria — see that document for detail on whether
t=36 is a full zero-overlap or a partial-retention flag; this audit's
`data/material_retention_seed501.csv` `overlap_zero_displayed` column
shows only t=32 as a TRUE zero-overlap event among this seed's flagged
transitions inside 0–52).

## Rescoring outcome (from `branch_adjudication_611__seed501.json`)

Zero true direct causal parents at trigger (oracle pool 36, all negative).
`beam_search_benchmark`'s own v1 readout shows an apparently spectacular
turn (0.53→0.95 by release) — but its `v2`, `original_material`, and
`field_direction` readouts (0.094, 0.20, 0.061 at release) show **no real
turn at all**. v1's own interior shrank to 15 members at end-of-control
then grew to 62 by end-of-release, consistent with the MAP pointer drifting
onto a small, coincidentally-aligned fragment and then a different, larger
candidate inheriting that fragment's high score — the exact
cross-branch-overtake mechanism this audit independently confirms fires at
least once (t=32) squarely inside this seed's own control window.
`matched_random_blind_exterior` shows a second, smaller instance (v1 0.72
vs. v2 0.14 at release — v1 and v2 disagree with each other on the SAME
branch). `original_reproduced` (fresh-CRN reproduction of the real
algorithm) shows a modest, partially-persisting rise (0.39→0.17, above
no_control's 0.05) — smaller than `RESULTS_6_11.md`'s reported number for
this seed, consistent with a different random draw from the same starting
state, not the same sample path.

## Separate conclusions

- **Physical turn (originally selected material, with gradual turnover
  allowed)**: **unresolved by this pass in the strict sense of "does the
  continuing organized entity turn"** — this audit did not perform a full
  bird-ID lineage trace from t=30 through t=77 forward from the qualified
  set with an independently-defined material-continuity rule (that is
  exactly the kind of confirmatory analysis flagged as Step 2 work in
  `NEXT_STEP_RECOMMENDATIONS.md`). What IS established: the DISPLAYED v1
  object is not materially continuous across the control window (zero
  overlap at t=32), so any claim that "the originally selected flock
  turned" cannot currently be supported by the v1 record alone without
  first resolving which of the post-t=32 candidates, if any, is the
  legitimate physical descendant of the t=30 material.
- **Material/organizational continuation**: **no** — a genuine, zero-overlap
  discontinuity occurs inside the control window itself (t=32), on top of
  the 5 pre-qualification switches.
- **Persistence after release**: the only readout showing a persistent rise
  (`matched_random_blind_exterior`'s v1 number, 0.72) is not corroborated by
  v2, material, or field-direction on the SAME branch.
- **Intervention-effect evidence**: `beam_search_benchmark` (the strongest
  reference-branch v1 rise in the whole 5-seed study) is the clearest
  documented case in this study of a v1-only artifact — every ID-independent
  readout on that same branch shows no turn.
- **Actuator-selection-specificity evidence**: none survives — all 3
  evidence-gated repaired branches abstain (S=∅, no candidate clears the
  bootstrap CI floor).

## v1 vs. later-rescore vs. physical-reconstruction — explicit disagreement

- **v1 (original)**: turn.
- **Later ID-independent rescoring**: not demonstrated controllable — v1's
  rise does not survive contact with `original_material`/`field_direction`
  on the branches that show it.
- **This pass's direct reconstruction**: identifies a genuine, previously
  phase-unstamped zero-overlap discontinuity inside the control window
  itself, which independently supports the rescoring's skepticism from a
  different angle (material continuity, not just alternate readouts) —
  but does not, by itself, prove no real turn occurred in whichever
  material actually continues from t=30. **This is presented as an open
  question, not resolved here.**
