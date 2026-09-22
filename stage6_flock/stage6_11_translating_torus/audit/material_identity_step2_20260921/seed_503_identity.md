# Seed 503 — material-identity adjudication (the critical case)

Full transition detail: `seed_503_t46_t47_forensics.md`. This file covers
the whole episode.

## A. Identity

Qualification-time target: t=35, 21 members. `ForwardMaterialTrace611`
agrees with v1's displayed interior for t=35–46 (12 steps — the trace and
v1 track the same material through the early part of control). **At t=47
(the corrected observation's exact transition) the trace and v1 diverge,
and — unlike seed 501 — they never reconverge for the remaining 35 steps
of the episode, through end-of-control (t=57) and all of release (t=58–82).**
35 of 47 traced steps disagree with v1.

One genuine merge flag (t=43: the previous target is 100% retained inside a
larger, ~42-member candidate — the only merge event found across all 5
seeds). Three split flags (t=47, 59, 62 — repeated candidate ambiguity,
consistent with a spatially fragmenting, hard-to-individuate population
even along the trace's own continuing path).

**Determination (task's explicit three-way question for this seed):**
the material target genuinely **splits at t=47** — the incumbent's own
best continuations (candidates retaining 49% and 43% of its material) are
both real, substantial fragments, not a "no valid continuation" situation
— and `ForwardMaterialTrace611` follows the larger fragment (18 members)
forward while v1's own argmax jumps to an unrelated, zero-overlap,
independently-pre-existing population (hid=29, 31 members). **This is not
identity-unresolved (a valid continuation existed and was taken) and not
simple continuation (v1's path and the material path are now different
objects) — it is a genuine split where v1 and the material trace follow
different branches from that point on.**

## B. Physical behavior — separated explicitly, per task instruction

**The materially-continuing target** (the trace's own path, following the
larger fragment forward from t=47): heading fraction 0.048 (qualification)
→ 0.091 (end of control, t=57) → 0.089 (release start) → **0.346 (end of
release, t=81)**. A real, non-trivial rise (roughly 7x the starting
fraction) but far short of a dominant alignment, and reached slowly.

**v1's displayed trajectory** (tracking the unrelated population from t=47
onward): 0.048 → 0.710 (end of control) → 0.719 (release start) → **0.857
(end of release)** — the large, dramatic turn `RESULTS_6_11.md` and Step 1
both reported.

**These are trajectories of two different, materially-disjoint
populations from t=47 onward.** The "large physical turn" is real, in the
sense that SOME population in the simulation reaches 0.86 alignment — but
it is not demonstrated to be the same organizational entity that was
selected as the control target at qualification and actuated throughout
the control window.

## C. Comparison to legacy readouts

- **v1**: turn (0.05→0.86), large and persistent.
- **Step 1 ID-independent rescoring**: did NOT withdraw this seed —
  `original_reproduced` and `old_set_held_actual_duration` showed
  agreement across v1/v2/original_material/field_direction (all four
  readouts corroborated a real turn), on COUNTERFACTUAL fresh-CRN branches
  from the t0=35 trigger. Step 1 additionally found the effect was
  duration-driven (a matched random exterior set does nearly as well),
  not selection-driven — a separate finding from this task's identity
  finding.
- **Frozen original material**: fixed to the exact t0=35 cohort; Step 1
  reported this readout also corroborating a real turn on the
  counterfactual branches (0.90→0.71 for `original_reproduced`).
- **This task's forward material trace (the ACTUAL recorded trajectory,
  not a counterfactual re-simulation)**: shows a much smaller rise
  (0.05→0.35) in the target's real forward material descendant, with the
  bulk of the reported 0.86 belonging to a population that is NOT
  materially descended from the t0=35 cohort past t=47.

**Explaining the disagreement**: Step 1's `original_material` readout and
this task's forward trace are conceptually similar (both anchor to real
bird-ID continuity) but were computed on **different trajectories** —
Step 1's on fresh-CRN counterfactual re-simulations from the trigger state,
this task's on the actual recorded episode. It is not established here
that Step 1's `original_material` finding on the counterfactual branch
would also show a large split if that branch were traced forward the same
way this task traced the real one — that would require applying
`ForwardMaterialTrace611` to Step 1's counterfactual branches too, which
this task did not do (a disclosed scope limitation, not a contradiction).
**What IS established, directly, is that the ACTUAL historical run's
target undergoes a genuine material split at t=47, and the population that
produces the dramatic 0.86 alignment is the OTHER branch of that split.**

## The reinterpretation the task flagged as acceptable

> "This may change the interpretation of seed 503 from 'identity-valid
> physical turn' to 'real system-level response but unresolved target
> identity.'"

The finding here is slightly more specific than "unresolved": it is a
**resolved split** — the trace does not lose the thread (status stays
`continuing`, never `unresolved` or `dead`), but the thread it follows is
demonstrably not the one that turns. The honest summary: **a real,
large, system-level alignment event occurs in this episode, but it occurs
in a population that a defensible forward material-continuity rule
identifies as distinct from the flock selected and actuated at
qualification.**

## Fields (per task §14)

- Identity: **identity-valid but split at t=47** — the trace continues
  materially, but diverges from v1's displayed pointer permanently from
  that point.
- Physical turn: **demonstrated, but not in the material-continuing
  target** — a large turn (0.86) occurs in the simulation, in a population
  the material trace identifies as a different branch from t=47 onward;
  the material-continuing target itself shows only a modest rise (0.05→0.35).
- Intervention effect: **not established for the material-continuing
  target** — Step 1's duration-vs-selection finding (matched-random
  exterior reproduces most of the effect) was computed on v1's own
  (unrelated-population) counterfactual branches, not on the material
  trace's target; whether the actuators had any effect on the actual
  continuing material is not evaluated in this pass.
- Actuator selectivity: **not established**, same reason.
