# Seed 500 — chronological audit

Sources: `data/viz_bundle_611__seed500.json`, `data/online_control_611__seed500.json`,
`audit/lineage_forensics_611__seed500__{hypotheses,candidates,transitions}.{csv,json}`,
`audit/branch_adjudication_611__seed500.json`, `audit/FIVE_SEED_CAUSAL_ADJUDICATION.md`,
this audit's `data/material_retention_seed500.csv` and
`plots/seed500_material_retention_and_heading.png`.

## Timeline

| event | t | note |
|---|---|---|
| episode start | 0 | uncontrolled |
| genuine identity discontinuities (pre-qualification) | ~1, 21, 27, 39 | see below |
| qualification / target set | 61 | `target_heading=1` (down), current-dir observed = 2 (left); trigger interior size 33 |
| control window | 61–83 (23 steps) | |
| release begin | 84 | |
| episode end | 108 | |

**Original v1 label: no turn.** `original_material_end_release=0.06` (from
`branch_adjudication_611__seed500.json`'s reproduction with fresh CRN),
consistent with `RESULTS_6_11.md`'s original call.

## Genuine identity discontinuities (this seed's own data, no audit judgement call)

From `lineage_forensics_611__seed500__transitions.json` (already-existing,
verified 0-mismatch replay) and this audit's independent frame-to-frame
cross-check (`data/material_retention_seed500.csv`, `overlap_zero_displayed`
column, computed directly from `viz_bundle_611__seed500.json`'s recorded
`interior` lists — no tracker internals used for this cross-check):

| t | prev size | new size | overlap | mechanism |
|---|---|---|---|---|
| ~1 | small | — | 0 | tracker restart very early in the episode (still forming) |
| **21** | 38 | 17 | **0** | **cross-branch MAP overtake**, fully decomposed in `LINEAGE_FORENSICS_6_11.md` §1.1: the previously-displayed thread (hid 3) had a perfectly viable continuation (R_retain=0.58) but its prior mass was diluted by branching into two candidates; an independent thread (hid 2) had one undiluted, well-matched continuation (score 0.876) and won the argmax, `map_prob=0.357`, margin only 0.050 (near-tied) |
| 27 | 17 | 29 | 14 (partial, R_retain=0.82 but flagged for `D_deform=0.317`) | partial regrowth after t=21's jump |
| **39** | 36 | 20 | **0** | a second cross-branch overtake, same class of mechanism as t=21 (not separately decomposed candidate-by-candidate in this pass, but confirmed zero-overlap by both the tracker-internal record and this audit's independent frame cross-check) |

**None of these four events occurs during the control window (61–83) or
release window (84–108).** All four are pre-qualification. `LINEAGE_FORENSICS
_6_11.md` §6 independently confirms: "seed 500: qualified at t=61, 4 MAP-hid
switches before qualification (t=4,21,27,39), 0 after."

## The new observation: seed 500 t=46→47 — NOT SUBSTANTIATED BY ANY RECORDED ARTIFACT

This audit was commissioned partly because a fresh visual inspection
reported "a large identity jump around t=46→47: most of the material
appears not to be retained, and the tracker seems to select another flock
already heading in the target direction." Checked directly against every
recorded artifact:

- **`viz_bundle_611__seed500.json`** (production ground truth): `interior`
  at frame t=46 and frame t=47 are **the identical 38-member set**, same
  order, zero difference (`overlap=38, union=38`, `Jaccard=1.0`).
- **`interactive_demo/v2/data/tab6_translation.json`** (the demo dataset):
  same result, identical 38-member set at t=46 and t=47.
- **`lineage_forensics_611__seed500__hypotheses.csv`** (independently
  replayed, 0-mismatch-verified tracker state): `map_hid=29` unchanged
  across t=43–48; `map_size` 37→38 (t=45→46, R_retain=1.0) and 38→38
  (t=46→47, R_retain=1.0, R_purity=1.0); `n_live_hypotheses=5` unchanged;
  not among the 4 flagged unusual-transition steps (t=4,21,27,39).
- **Positions**: mean member displacement from t=46 to t=47 is **0.28
  spatial units** (torus side `L=24`) — no periodic-wrap-scale jump, no
  torus artifact either (see `audit_findings.md` §7 for the general torus
  audit).
- **Target direction**: `target_heading` is `None` at both t=46 and t=47 —
  **qualification does not occur until t=61**, so there is no "target
  direction" for the tracker to be biased toward at this point in the
  episode at all. No actuators exist yet (`actuators=[]` both frames,
  `phase="uncontrolled"` both frames).

**Conclusion for this transition: no membership discontinuity, no torus
artifact, and no target-direction bias mechanically possible (because no
target has been set yet) is present in any recorded production or replay
artifact at seed 500, t=46→47.** See `plots/seed500_material_retention_and_heading.png`
for the full-episode retention trace: the line is flat at 1.0 across this
exact window, in visible contrast to the two real zero-overlap dips at
t=21 and t=39.

**This is a genuine "evidence not present" finding, not a rescue of the
original result** (`per Non-negotiable working principle #1`): the audit
cannot confirm the visually-reported t=46→47 jump against any artifact
that was checked. Two explanations remain open, NOT adjudicated between by
this pass (per the stop-condition instructions):

1. The visual inspection that motivated this audit used a different
   rendering (a figure, an older/different build of `interactive_demo`, a
   different frame-indexing convention, or a scrubbed replay where playback
   speed made an unrelated event — e.g. the t=39 jump six steps earlier, or
   the t=61 qualification/target-set event fifteen steps later — appear to
   be at t≈46–47).
2. A rendering path not audited in this pass (e.g. a static figure under
   `figures/`, not part of `interactive_demo/v2`) contains a genuine bug
   this pass did not check, because it was not identified as the source by
   any artifact this pass located.

This audit did **not** locate any artifact reproducing the reported
observation, and states that as the result rather than guessing which
explanation applies.

## Control-phase mechanism (why v1 shows a transient rise and no persistent turn)

Trigger state at t=61 has **zero true direct causal parents**
(`n_true_direct_parents=0`, `branch_adjudication_611__seed500.json`) —
confirmed independently by `METHODS_AUDIT_6_11.md` §4's worked example for
this exact snapshot. Every evidence-gated repaired branch
(`repaired_blind_authority`, `repaired_direct_causal_restricted`,
`exact_direct_interface_repaired`, `beam_search_benchmark`) **correctly
abstains** — nothing to act through. Only `original_reproduced` (old
algorithm, unconstrained top-K) shows a rise, to 0.36 by end-of-control,
which collapses to 0.05 by end-of-release — not release-persistent, and
`old_set_held_actual_duration` (same actuators, held fixed rather than
re-selected every 8 steps) shows **no rise at all** (0.03 throughout),
showing the transient rise is an artifact of the refresh-every-8-steps
mechanism itself, not of the specific actuators chosen. Full branch table:
`FIVE_SEED_CAUSAL_ADJUDICATION.md`, "Seed 500" section.

## Separate conclusions (per task instruction, not collapsed into one verdict)

- **Physical turn**: no — `original_material` and `field_direction` both
  fail to rise and persist in every branch, old or repaired.
- **Material/organizational continuation**: the tracked interior at
  qualification (t=61) is NOT the original lineage's first thread — it
  arrived via 4 cross-branch MAP overtakes before qualification (all
  pre-control). Once in control, membership is materially stable (no
  zero-overlap event during 61–108, confirmed above).
- **Persistence after release**: n/a — no turn to persist.
- **Causal/intervention-effect evidence**: none survives (`old_set_held
  _actual_duration` with the SAME actuators as `original_reproduced` shows
  no rise at all — the transient effect in `original_reproduced` tracks the
  refresh mechanism, not the actuators).
- **Actuator-selection-specificity evidence**: none — the trigger has zero
  true causal parents, so no actuator set (old or repaired) could have had
  real one-step authority at this snapshot.

## v1 vs. later-rescore vs. physical-reconstruction

All three agree for seed 500: **no turn, not controllable under tested
budget.** No disagreement to report for this seed.
