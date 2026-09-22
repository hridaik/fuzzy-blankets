# Seed 501 causal adjudication

Highest-priority case per spec. Covers the SCHEDULE-EFFECT estimand
(Task F1 §10.1) in full; the POLICY-EFFECT estimand (§10.2) is a
documented partial/deferred item — see final section and
`NEXT_CONTROLLER_SPEC_INPUTS.md`.

## Identity and physical-turn baseline (from prior passes, cited not re-derived)

`identity_causal_reconciliation_20260921/seed_501_identity.md` /
`material_identity_step2_20260921/seed_501_identity.md`: the
materially-continuing target survives the whole episode
(`strict_identity_continuity = valid`, after a self-correcting v1
detour t=32–35), and rises 0.23→0.97 in the actual recorded trajectory,
persisting through release. `seed_501_controller_timeline.md` (this pass)
establishes: no authority refresh during the detour, actuators unchanged
throughout t=30–38, and actuators stayed physically close (min distance
0.57–1.24 units) to the material target throughout, never drifting toward
v1's temporarily-wrong displayed population.

**What was NOT yet established before this pass**: whether the observed
rise was caused by the intervention at all, versus reflecting the flock's
own unforced dynamics; and whether the SPECIFIC historical actuator
choice mattered versus any similarly-sized, similarly-timed forcing.

## Method: schedule-effect harness (Task F1 §10.1)

`code/seed501_schedule_effect.py`. Trigger state t0=30 (independently
verified bit-exact reproducible, `RNG_AND_CRN_AUDIT.md` §4). Three
branches per replicate, **CRN-paired** via a dedicated physics-only RNG
stream shared across all three branches within a replicate (validity
established in `RNG_AND_CRN_AUDIT.md` §3, NOT assumed):

- **no_forcing**: `forced_actions=None` every step, t=30 through t=77 (47
  steps, matching the historical episode's actual final_t).
- **historical_schedule**: the EXACT historical actuator IDs and
  `target_heading=2`, replayed with the exact refresh cadence and hold
  durations read from `data/online_control_611__seed501.json` (refreshes
  at t=30/39/48; see `seed_501_controller_timeline.md` for the full
  table) — schedule REPLAY only, not the online controller's own
  re-inference logic.
- **matched_random**: same actuator COUNT (8) at each of the same 3
  refresh times, same target heading, drawn from the SAME
  eligible-exterior-pool definition the real controller used
  (`near_exterior`, radius_factor=3.0, computed at the t0 interior — a
  disclosed simplification: the real controller recomputes its own
  exterior pool from its own evolving v1 interior at each refresh, which
  this schedule-only harness does not re-run; see "what this pass did not
  do" below). A fresh random draw per replicate (independent RNG stream,
  never touching the physics stream).

25 replicates requested; 22–24 completed with a valid (non-`None`)
end-of-release reading per branch (a `dead` final trace status yields no
alignment reading for that replicate/branch — reported as `n` per branch,
not silently imputed).

**Scoring**: `ForwardMaterialTrace611` (frozen rule) applied to each
branch's own simulated trajectory, seeded from the exact t0 interior (30
bird IDs), run forward through the branch's own detector output
(`detect_69.propose`, exactly the production call pattern, sliding window
seeded with the REAL recorded pre-t0 context then the branch's own
simulated frames from t0 onward).

## Results

| branch | n | mean end-of-release alignment | median | std | p10 | p90 | final status: continuing / dead |
|---|---|---|---|---|---|---|---|
| no_forcing | 24 | 0.263 | 0.075 | 0.322 | 0.024 | 0.774 | 24 / 1 |
| historical_schedule | 23 | **0.603** | 0.741 | 0.326 | 0.008 | 0.890 | 23 / 2 |
| matched_random | 24 | 0.488 | 0.618 | 0.378 | 0.041 | 0.921 | 24 / 1 |

### Paired differences (within-replicate, same physics noise — CRN)

| comparison | n pairs | mean diff | std | fraction positive | 90% CI on mean |
|---|---|---|---|---|---|
| historical − no_forcing | 22 | **+0.309** | 0.418 | 68.2% | [0.162, 0.455] |
| historical − matched_random | 22 | +0.072 | 0.426 | 54.5% | [−0.078, 0.221] |

(90% CI = mean ± 1.645×SE, SE = std/√n — a simple normal-approximation
interval, not a new success threshold; reported for uncertainty
quantification only, per spec §13's instruction not to invent a binary
criterion after seeing results.)

## Answering the task's exact questions

**Does the materially continuous target turn more under the historical
intervention than under no forcing?** **Yes, with reasonably strong
paired evidence**: mean paired difference +0.309 in end-of-release
alignment, 90% CI entirely positive ([0.162, 0.455]), 68% of paired
replicates favor the historical schedule. Distributions are wide (both
branches show high variance — this flock's own unforced dynamics
sometimes reach high alignment by chance, visible in `no_forcing`'s
right-skewed distribution: median 0.075 but p90 0.774) — this is reported
plainly rather than hidden, but the PAIRED comparison (same physics noise
per replicate) is the more informative statistic than the unpaired
means, and it points the same direction.

**Does the historical/learned actuator choice outperform matched random
choices?** **Not demonstrated.** Paired mean difference +0.072, 90% CI
[−0.078, 0.221] — crosses zero. 54.5% of replicates favor the historical
choice, indistinguishable from a coin flip at this sample size.

## Conclusion for seed 501 (exactly the form spec §10.3 anticipates)

**Intervention effective (sustained forcing raises the material target's
alignment relative to no forcing); actuator selection not demonstrated
(the specific historical actuator IDs do not clearly outperform
duration/cardinality/cadence/pool-matched random alternatives).** This is
reported as the honest conclusion, not softened toward either a stronger
or a null result.

| dimension | evidence status |
|---|---|
| physical_turn_of_material_target | demonstrated (real recorded trajectory, prior passes) |
| strict_identity_continuity | valid (prior passes; reconfirmed by this pass's controller-timeline actuator-proximity evidence) |
| intervention_effect (schedule vs. no forcing) | **demonstrated** (this pass) |
| actuator_selectivity (historical vs. matched random) | **not demonstrated under tested conditions** (this pass) |
| persistence_after_release | consistent with persistence in the real recorded trajectory (0.97 at t=76); the schedule-effect harness's own end-of-release readings (median 0.741 for historical_schedule) are broadly consistent with sustained post-control alignment, though with wide variance across replicates |
| organizational_disruption | none observed in this pass's traces (all historical_schedule replicates that survive to the end show `continuing` status; 2/23 die, consistent with ordinary trace attrition, not disruption events) |

## What this pass did NOT do (disclosed, not silently skipped)

- **Policy-effect estimand (§10.2)**: re-running the actual ONLINE
  controller (including its own predictive-boundary/causal-probing/
  authority-re-estimation decision logic) from the trigger state, rather
  than replaying a fixed historical schedule. Per `RNG_AND_CRN_AUDIT.md`
  §5, this requires the control loop's auxiliary decision machinery to be
  re-routed to its own dedicated RNG stream (decoupled from physics) for
  valid CRN pairing against a no-control comparator — a substantially
  larger audit-only fork of `run_online_control_611.py`'s loop body than
  the schedule-effect harness required. Not attempted in this pass; see
  `NEXT_CONTROLLER_SPEC_INPUTS.md`.
- **Geometry-matched random forcing (§10.1.C)**: the matched-random
  comparator matches count/timing/pool/heading but not the SPECIFIC
  spatial arrangement of the historical actuators within that pool. Not
  attempted separately in this pass (time budget); the pool-level match
  is the comparator actually reported.
- **Exterior-pool recomputation per refresh** from each branch's own
  evolving interior (the real controller does this; this harness computes
  the pool once, from the t0 interior, for all three refresh draws) — a
  disclosed simplification, not silently assumed equivalent.
