# Seed 503 — chronological audit

Sources: as `seed_500.md`, seed 503 files. `FIVE_SEED_CAUSAL_ADJUDICATION.md`
"Seed 503"; `AUTHORITY_AND_SET_EFFECT_AUDIT.md` §4; `data/material_retention_seed503.csv`.

## Timeline

| event | t |
|---|---|
| qualification / target set | 35 (`target_heading=2` left, current-dir=0; trigger interior size 21) |
| control window | 35–57 |
| release begin | 58 |
| episode end | 82 |

**Original v1 label: turn.** This is the ONE seed whose real, large,
persistent turn survives ID-independent rescoring — **but by a mechanism
the original method did not identify as the active ingredient**, per the
handoff's own summary ("a matched random exterior set produced almost the
same response").

## Pre-qualification identity churn

`LINEAGE_FORENSICS_6_11.md` §6: qualified at t=35, **6** MAP-hid switches
before qualification (t=3,7,8,9,10,11) — the messiest pre-qualification
lineage of the 5 seeds by switch count, despite ending up the one
unambiguous success.

## Zero-overlap discontinuities during control

This audit's frame-to-frame cross-check finds **two** zero-overlap events
inside the control window: **t=35→ actually flagged at t=35 (qualification
boundary itself) and t=47** (mid-control). Both are within 35–57. This
means even seed 503's "unambiguous" turn is displayed by an interior that
is not perfectly materially continuous with the t=35 qualified set —
consistent with the rest of this study's general finding that abrupt
displayed-membership breaks are common across all five seeds, not a
seed-500-specific defect.

## All four readouts agree: a real, large, substantially persistent turn

From `branch_adjudication_611__seed503.json`: `original_reproduced`
(v1/v2/material/field-direction, end-control→end-release) = 0.96→0.95 /
0.96→0.95 / 0.90→0.71 / 0.95→0.93. `old_set_held_actual_duration` (same
actuators as `original_reproduced` but held fixed rather than re-selected):
0.92→1.00 / 0.92→1.00 / 0.95→0.67 / 0.89→0.98. **v1 and v2 are identical
throughout for these two branches — no identity-artifact concern for THIS
particular finding.**

## The matched-random-exterior finding (the load-bearing caveat)

`matched_random_blind_exterior` — a RANDOM same-size set of exterior birds,
held the full 23-step duration — reproduces almost the same huge effect
(v1 0.95→0.92, `original_material` 1.00→0.81). This "strongly suggests the
mechanism at this trigger is 'hold a moderate number of exterior birds at
the target heading for ~23 steps,' largely independent of which birds, not
a genuine causal/authority-selection effect" (`FIVE_SEED_CAUSAL_ADJUDICATION.md`).
Meanwhile every evidence-gated repaired branch (`repaired_blind_authority`,
`repaired_direct_causal_restricted`, `exact_direct_interface_repaired`)
**abstains** — no candidate clears the bootstrap CI floor at this trigger —
and `beam_search_benchmark` finds only a single, weakly-positive actuator
(A=0.006) and achieves nothing.

## Separate conclusions

- **Physical turn**: **yes** — the strongest, most corroborated positive
  finding in the whole 5-seed study; all four readouts agree, on two
  independent branches (`original_reproduced`, `old_set_held_actual_duration`).
- **Material/organizational continuation**: partially — two zero-overlap
  discontinuities occur within the control window (at qualification and
  mid-control), so "the originally selected flock" is not a single
  unbroken thread even here; the turn is real for WHATEVER is displayed as
  the interior at each point, not proven to be one continuously-identified
  physical object start-to-finish.
- **Persistence after release**: yes, for the two branches above (0.71–0.98
  at release, well above the 0.048 starting fraction).
- **Intervention-effect (causal) evidence**: **not established** — the
  effect is duration-driven (holding ANY moderate exterior set for the
  full window), not selection-driven. `old_set_one_shot` (the SAME
  actuators, forced once then released) shows only a transient blip
  (0.35→0.04), directly confirming the intervention-duration mismatch
  (`METHODS_AUDIT_6_11.md` §1.5) is the operative defect here, not merely a
  theoretical one.
- **Actuator-selection-specificity evidence**: **negative** — a random set
  of the same size does nearly as well as the algorithm's own choice; the
  repaired, evidence-gated selectors find nothing to act on at all.

## v1 vs. later-rescore vs. physical-reconstruction

All agree a real turn occurred. They disagree on WHY:
`RESULTS_6_11.md`'s framing attributes it to the method's causal/authority
machinery; this pass's evidence (matched-random comparator +
`old_set_one_shot`'s collapse) attributes it to duration/holding, largely
independent of actuator identity. **The correct reading, per
`FIVE_SEED_CAUSAL_ADJUDICATION.md`: "this benchmark's search objective does
not find the intervention that a cruder, duration-matched approach finds
easily" — a benchmark-adequacy finding, not a controllability finding.**
No historical number is disputed here, only its causal interpretation.
