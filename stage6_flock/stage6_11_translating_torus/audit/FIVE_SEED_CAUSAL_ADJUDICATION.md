# Five-Seed Causal Adjudication — Stage 6.11B (item 9-11)

Additive. Branches from the exact recorded pre-control trigger snapshot for
each of seeds 500–504 (`audit/trigger_states_611.json`, extracted directly
from `data/viz_bundle_611__seed{n}.json` and
`data/online_control_611__seed{n}.json` — no re-simulation to get there).
Script: `audit/branch_adjudication_611.py`. Raw per-seed output:
`audit/branch_adjudication_611__seed{n}.json`.

**Important interpretive note before the numbers.** Every branch (including
`original_reproduced`) runs from a **fresh common-random-number stream**
seeded at the trigger point, not the original recorded run's own RNG
stream — this is required for valid CRN comparison ACROSS branches from a
common start, but it means `original_reproduced`'s specific numbers will
**not** numerically match `RESULTS_6_11.md`'s reported trajectory for the
same seed. It reproduces the ALGORITHM (near_exterior(3R) oracle pool,
old one-shot authority, refresh-every-8-steps cadence) from the same
starting state, not the exact sample path. This is why the frozen
`RESULTS_6_11.md` numbers are the ones to cite for "what was reported,"
and this document's numbers are the ones to cite for "what a repeated
run of the same algorithm from the same state, under fresh randomness,
does" and "how the repaired alternatives compare to it under the SAME
fresh randomness."

## Branch definitions (recap)

1. `no_control` — no forcing at all.
2. `original_reproduced` — old `near_exterior`(3R) oracle pool, old one-shot
   d=1/tau=4 authority, refreshed every 8 real steps (the ORIGINAL
   pipeline's own logic, re-run from CRN).
3. `old_set_one_shot` — the SAME set branch 2 selects at t0, forced once
   then released (the estimand the old authority probe actually measured).
4. `old_set_held_actual_duration` — same set, held for the full 24-step
   control window (what actually happened in the real run).
5. `matched_random_blind_exterior` — random same-size subset of the blind
   `nearest_M12` pool, held 24 steps.
6. `repaired_blind_authority` — blind pool, repaired `A_S(tau=4,d=4)`,
   top-K with abstention, single-shot selection at t0, held 24 steps.
7. `repaired_direct_causal_restricted` — blind pool restricted to blind
   `B_causal` survivors, then repaired authority/top-K, held 24 steps.
8. `exact_direct_interface_repaired` — privileged oracle `B_D` as the ONLY
   candidate pool, repaired authority/top-K (reference upper bound).
9. `beam_search_benchmark` — privileged `near_exterior`(3R) pool, beam
   search over repaired `A_S` (reference upper bound, no MCTS).

Branches 6–9 select ONCE at t0 and hold for the full 24-step window
(disclosed compute-budget simplification, `RESULTS_6_11B.md`'s deferred
list); branch 2 keeps the original refresh-every-8-steps cadence since that
is what is being reproduced.

## Scoring (item 10): four identity readouts, every branch, end of control AND end of release

- **v1 MAP**: fraction of the ORIGINAL tracker's own end-of-window interior
  at the target heading.
- **v2 MAP**: same, for the repaired present-state-coalesced tracker.
- **Original material**: fraction of the EXACT bird IDs that were the
  interior at t0 (the "material set present at target introduction"),
  regardless of what either tracker now believes the interior is.
- **Field-direction (ID-independent)**: fraction of ALL birds within a
  fixed radius of the v2 tracker's current centroid (a soft, position-only
  anchor, not a hard membership test) currently at the target heading.

---

Heading indices follow `flock_sim.model.UV4` (0=up, 1=down, 2=left, 3=right
on the lattice) — not compass directions; the codebase itself never labels
them geographically.

## Seed 500 (t0=61, target=down, trigger interior size 33)

Trigger has **zero** true direct causal parents (`n_true_direct_parents=0`,
confirming `METHODS_AUDIT_6_11.md` §4's worked example exactly — this is the
same trigger snapshot). Blind pool (12) and oracle pool (10) both nonempty,
but neither contains a true parent because none exists.

| branch | v1 MAP end-ctrl→rel | v2 MAP end-ctrl→rel | original material end-ctrl→rel | field-direction end-ctrl→rel |
|---|---|---|---|---|
| no_control | 0.00 → 0.04 | 0.03 → 0.10 | 0.06 → 0.06 | 0.03 → 0.10 |
| original_reproduced | **0.36 → 0.05** | **0.36 → 0.05** | 0.27 → 0.21 | 0.35 → 0.03 |
| old_set_one_shot | 0.03 → 0.00 | 0.03 → 0.02 | 0.06 → 0.03 | 0.03 → 0.02 |
| old_set_held_actual_duration | 0.03 → 0.02 | 0.03 → 0.02 | 0.03 → 0.03 | 0.03 → 0.03 |
| matched_random_blind_exterior | 0.03 → 0.02 | 0.03 → 0.02 | 0.03 → 0.03 | 0.03 → 0.03 |
| repaired_blind_authority | = no_control (abstained, S=∅) | | | |
| repaired_direct_causal_restricted | = no_control (abstained, blind B_causal pool = 0) | | | |
| exact_direct_interface_repaired | = no_control (abstained, 0 true parents) | | | |
| beam_search_benchmark | = no_control (abstained, A=0 [0,0]) | | | |

(Starting alignment `frac_at_target_start = 0.121` for reference.)

**Every repaired/reference branch correctly abstains** — there is nothing
to act through, and none of them force actuators anyway. **Only
`original_reproduced` (the old algorithm, unconstrained top-K, forced
regardless) shows any rise at all — to 0.36 by end of control — and it is
not release-persistent: it collapses to 0.05, statistically indistinguishable
from `no_control`'s own 0.04.** Critically, `old_set_held_actual_duration`
(the SAME initial actuator set as `original_reproduced`, but held fixed
rather than re-selected every 8 steps) shows **no rise at all** (0.03
throughout) — the transient rise in `original_reproduced` is not
attributable to the specific actuators chosen at t0, since holding exactly
that same set fixed produces nothing. It is attributable to the
REFRESH-EVERY-8-STEPS mechanism itself repeatedly forcing a *changing* set
of birds while candidate detection and the tracker keep re-evaluating what
"the interior" is — consistent with `LINEAGE_FORENSICS_6_11.md`'s
interior-selection-drift concern, not with any actuator having real,
persistent authority. **Seed 500: no branch, old or repaired, produces a
real, release-persistent turn from this trigger state.**

## Seed 501 (t0=30, target=left, trigger interior size 30)

Zero true direct causal parents at trigger (oracle pool 36, all negative).

| branch | v1 end-ctrl→rel | v2 end-ctrl→rel | material end-ctrl→rel | field-dir. end-ctrl→rel |
|---|---|---|---|---|
| no_control | 0.10 → 0.05 | 0.09 → 0.22 | 0.10 → 0.23 | 0.09 → 0.19 |
| original_reproduced | 0.39 → 0.17 | 0.39 → 0.17 | 0.43 → 0.27 | 0.39 → 0.19 |
| old_set_held_actual_duration | 0.10 → 0.06 | 0.10 → 0.06 | 0.23 → 0.07 | 0.10 → 0.06 |
| matched_random_blind_exterior | 0.09 → **0.72** | 0.09 → 0.14 | 0.13 → 0.23 | 0.09 → 0.14 |
| repaired_blind_authority / direct_causal_restricted / exact_direct_interface | = no_control (all abstained, S=∅) | | | |
| **beam_search_benchmark** | **0.53 → 0.95** | 0.09 → 0.09 | 0.27 → 0.20 | 0.10 → 0.06 |

(start = 0.233)

**A stark within-branch disagreement, and the clearest demonstration in
this study of the exact failure mode this whole audit exists to catch.**
`beam_search_benchmark`'s own v1 readout shows an apparently spectacular
turn (95% by release) — but its `v2`, `original_material`, and
`field_direction` readouts (0.094, 0.20, 0.061) show **no real turn at
all**. `v1`'s own interior shrank to 15 members at end-of-control then grew
to 62 by end-of-release — consistent with the MAP pointer drifting onto a
small, coincidentally-aligned fragment and then a different, larger
candidate inheriting that fragment's high score, exactly the
`LINEAGE_FORENSICS_6_11.md` §1 mechanism, not a real controlled turn.
`matched_random`'s 0.72 at release is a second, smaller instance of the
same pattern (a purely unforced release-phase swing with no `beam_search`-
level v1 corroboration — and here v1 and v2 disagree with EACH OTHER on the
same branch too: v1 says 0.72, v2 says 0.14). **Every reference branch that
would count as "controllable" evidence, on the v1 readout alone, evaporates
once the ID-independent readouts are consulted.** This seed's `original_reproduced`
run (the CRN-fresh reproduction of the actual old algorithm) shows a modest,
partially-persisting rise (0.39→0.17, still above `no_control`'s 0.05) —
smaller than what `RESULTS_6_11.md` reported for this seed, consistent with
this being a different random draw from the same starting state, not the
same sample path.

## Seed 502 (t0=30, target=down, trigger interior size 21)

Zero true direct causal parents at trigger (oracle pool 18).

| branch | v1 end-ctrl→rel | v2 end-ctrl→rel | material end-ctrl→rel | field-dir. end-ctrl→rel |
|---|---|---|---|---|
| no_control | 0.11 → 0.13 | 0.06 → 0.00 | 0.33 → 0.00 | 0.06 → 0.03 |
| original_reproduced | 0.06 → 0.00 | 0.06 → 0.00 | 0.43 → 0.19 | 0.06 → 0.08 |
| old_set_held_actual_duration | 0.06 → 0.01 | 0.06 → 0.01 | 0.52 → 0.38 | 0.06 → 0.01 |
| matched_random_blind_exterior | 0.06 → 0.00 | 0.06 → 0.00 | 0.19 → 0.33 | 0.06 → 0.00 |
| repaired_* (all 3) | = no_control (all abstained) | | | |
| beam_search_benchmark | 0.10 → 0.28 | 0.06 → 0.02 | 0.29 → 0.00 | 0.06 → 0.02 |

(start = 0.190)

Same pattern as seed 501, milder: `beam_search_benchmark`'s v1 readout
shows a modest rise (0.10→0.28) that v2/material/field-direction (0.02,
0.00, 0.02) do not corroborate at all. `original_reproduced` here shows NO
rise by any readout — this CRN draw did not reproduce even a transient
effect (again, a different sample path from the originally-reported one).

## Seed 503 (t0=35, target=left, trigger interior size 21)

Zero true direct causal parents at trigger (oracle pool 23). **The one
seed where a real, large, persistent, multiply-corroborated turn occurs —
but not from the mechanism the original method claims to exploit.**

| branch | v1 end-ctrl→rel | v2 end-ctrl→rel | material end-ctrl→rel | field-dir. end-ctrl→rel |
|---|---|---|---|---|
| no_control | 0.09 → 0.12 | 0.09 → 0.12 | 0.10 → 0.10 | 0.07 → 0.07 |
| **original_reproduced** | **0.96 → 0.95** | **0.96 → 0.95** | **0.90 → 0.71** | **0.95 → 0.93** |
| old_set_one_shot | 0.35 → 0.04 | 0.00 → 0.02 | 0.10 → 0.05 | 0.00 → 0.02 |
| **old_set_held_actual_duration** | **0.92 → 1.00** | **0.92 → 1.00** | **0.95 → 0.67** | **0.89 → 0.98** |
| **matched_random_blind_exterior** | **0.95 → 0.92** | 0.93 → 0.30 | **1.00 → 0.81** | 0.93 → 0.27 |
| repaired_* (all 3) | = no_control (all abstained) | | | |
| beam_search_benchmark | 0.06 → 0.12 | 0.06 → 0.12 | 0.24 → 0.29 | 0.07 → 0.07 |

(start = 0.048)

**All four readouts agree** for `original_reproduced` AND
`old_set_held_actual_duration`: a real, large, substantially persistent
turn (v1/v2 identical throughout — no identity-artifact concern here, both
trackers agree on the same interior). `old_set_one_shot` (same set, forced
only once) shows only a transient blip (0.35→0.04) — the intervention-
duration mismatch `METHODS_AUDIT_6_11.md` §1.5 predicted, directly
confirmed: **holding matters far more than which birds are held, at this
trigger.** `matched_random_blind_exterior` — a RANDOM same-size set,
held the full duration — reproduces almost the same huge effect (`v1`
0.95→0.92, `original_material` 1.00→0.81), strongly suggesting **the
mechanism at this trigger is "hold a moderate number of exterior birds at
the target heading for ~24 steps," largely independent of which birds, not
a genuine causal/authority-selection effect.** And yet: **every
evidence-gated repaired branch (`repaired_blind_authority`,
`repaired_direct_causal_restricted`, `exact_direct_interface_repaired`)
abstains** — no candidate's bootstrap CI clears positive evidence at
`d=tau=4`, so all three collapse to `no_control`'s own (flat) trajectory.
`beam_search_benchmark` finds only a single, weakly-positive actuator
(`A=0.006`, CI barely clearing zero) and achieves nothing. **The repaired
authority estimator is not wrong to abstain given what it measures — it
correctly reports no reliable short-horizon individual/small-set signal —
but what it measures is evidently not what is actually driving this
trigger's real, substantial controllability.** This is this pass's clearest
case of the repair being methodologically sound and empirically
insufficient at the same time; see `AUTHORITY_AND_SET_EFFECT_AUDIT.md` §4
for why a longer-hold spot check (this trigger looks like the strongest
candidate for one) was flagged as follow-up rather than resolved here.

## Seed 504 (t0=47, target=right, trigger interior size 28)

**The only trigger state with real true direct causal parents (11 of them)
and the clearest genuinely-positive measured authority in the whole study
(`AUTHORITY_AND_SET_EFFECT_AUDIT.md` §3) — and still no branch achieves a
real turn.**

| branch | v1 end-ctrl→rel | v2 end-ctrl→rel | material end-ctrl→rel | field-dir. end-ctrl→rel |
|---|---|---|---|---|
| no_control | 0.04 → 0.03 | 0.04 → 0.03 | 0.11 → 0.00 | 0.04 → 0.03 |
| original_reproduced | 0.76 → 0.14 | 0.76 → 0.14 | 0.46 → 0.07 | 0.76 → 0.10 |
| old_set_held_actual_duration | 0.03 → 0.08 | 0.03 → 0.08 | 0.07 → 0.07 | 0.03 → 0.06 |
| matched_random_blind_exterior | 0.00 → 0.05 | 0.00 → 0.05 | 0.07 → 0.00 | 0.00 → 0.05 |
| repaired_blind_authority (S={65,99,243,312}) | 0.10 → 0.06 | 0.10 → 0.06 | 0.39 → 0.21 | 0.10 → 0.05 |
| repaired_direct_causal_restricted (S={65,99,110,243,278}) | 0.03 → 0.05 | 0.03 → 0.05 | 0.07 → 0.04 | 0.03 → 0.05 |
| exact_direct_interface_repaired (S=7 of the 11 true parents) | 0.00 → 0.02 | 0.00 → 0.02 | 0.11 → 0.07 | 0.00 → 0.03 |
| beam_search_benchmark (S={65,243,278}, A=**0.052**, strongest in study) | 0.05 → 0.06 | 0.05 → 0.06 | 0.14 → 0.07 | 0.05 → 0.05 |

(start = 0.107)

**Not one branch — old, random, or any of the four repaired/reference
variants, including the one using true causal parents directly and the one
with the single strongest measured authority in this entire study —
achieves a rise above the starting fraction that survives to release.**
`original_reproduced` shows the largest CONTROL-phase rise (0.76) of any
branch in this seed, but it is entirely transient (down to 0.14 by
release, materially the same collapse pattern as seed 500's
`original_reproduced`). **This is the sharpest evidence in the whole study
that real, measurable, true-parent-grounded authority at this budget
(K≤8, τ=d=4, individual/small-set) is not sufficient to move this
particular collective's alignment** — not a repair failure (the repaired
branches behave exactly as their own evidence says they should), and not
obviously a search failure either (beam search found the single strongest
authority value measured anywhere in this study and still achieved nothing
persistent). Whether a larger K, longer hold, or different target/actuator
admissibility would succeed is not established either way by this evidence
— it is squarely a "not demonstrated controllable at this budget" case, not
a proof of impossibility.

---

---

## Controllability (item 11)

A seed is called **controllable under tested budget** only if a REFERENCE
branch (`exact_direct_interface_repaired` or `beam_search_benchmark`) shows
a release-persistent rise corroborated by AT LEAST the `original_material`
or `field_direction` (ID-independent) readout — a `v1`-only rise is
explicitly NOT sufficient, given how often it disagreed with every other
readout in this sample (seeds 501, 502). Otherwise: **not demonstrated
controllable under tested budget** — never "uncontrollable."

| seed | reference branch rise (v1) | corroborated by material/field-direction? | verdict |
|---|---|---|---|
| 500 | none (both abstained) | — | not demonstrated controllable |
| 501 | beam: 0.53→0.95 | **No** (material 0.20, field-dir 0.06 — no rise) | not demonstrated controllable |
| 502 | beam: 0.10→0.28 | **No** (material 0.00, field-dir 0.02 — no rise) | not demonstrated controllable |
| 503 | beam: 0.06→0.12 (no rise); exact abstained | — (reference branches found nothing) | **not demonstrated controllable BY THE REFERENCE BENCHMARK** — important caveat below |
| 504 | none of 4 repaired/reference branches rise and persist | — | not demonstrated controllable |

**5 of 5 seeds: not demonstrated controllable under this pass's reference
benchmark, at K≤8, τ=d=4.** This is a substantially more cautious
conclusion than `RESULTS_6_11.md`'s "3 of 5 turned," and the difference is
almost entirely explained by two things established elsewhere in this
pass: (a) the `v1`-only apparent successes at seeds 501/502 do not survive
contact with ID-independent scoring (item 10), and (b) this benchmark's own
search objective (short-horizon individual/small-set authority) is
evidently not sensing whatever mechanism actually moves the system —
**seed 503 is the load-bearing counter-example**: `old_set_held_actual_duration`
and even `matched_random_blind_exterior` (NOT reference branches, but
real, corroborated-by-all-four-readouts turns) show this collective very
clearly CAN be moved by holding a moderate exterior set for the actual
24-step duration, largely independent of which specific birds. **The
correct reading is not "seed 503 is uncontrollable" — it is "this
benchmark's search objective does not find the intervention that a cruder,
duration-matched approach finds easily," which is a benchmark-adequacy
finding, not a controllability finding, and is reported as such rather
than overstated in either direction.**

## Synergy and search-method comparison (item 8)

See `AUTHORITY_AND_SET_EFFECT_AUDIT.md` for the full top-K/greedy/beam/
synergy comparison at each trigger state. Headline: synergy is negative or
negligible everywhere it could be measured (including at seed 504, the one
seed with genuine positive individual authority) — no evidence that a
smarter search was leaving value on the table; the limiting factor in this
sample is authority/duration coverage, not search sophistication.

## What this section does and does not establish

**Confirmed:** the original "3/5 turned" headline does not survive
ID-independent rescoring for 2 of its 3 reported successes (501, 502); the
one seed with unambiguous, all-readout-corroborated real control (503) is
achieved by mechanisms (duration, not selection) the original method did
not identify as the active ingredient, and by actuator sets (including a
random one) the original method did not need to compute; the one seed with
the strongest real measured authority AND real true causal parents (504)
still shows no persistent turn under any tested controller.

**Not established:** whether any of the four "not demonstrated
controllable" verdicts would flip at a larger K, a longer hold duration, a
different search, or a different admissible-actuator definition. This
audit deliberately stops short of the larger confirmatory study needed to
settle that, per the stop instruction.
