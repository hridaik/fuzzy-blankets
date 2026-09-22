# Seed 501 controller timeline, focused on the t=32–35 v1 detour

Source: `data/online_control_611__seed501.json` (the production run's own
event log — B_C actuator sets, refresh cadence, per-step interior size and
v1-displayed target-alignment fraction) cross-referenced with
`data/viz_bundle_611__seed501.json` (exact per-frame positions/headings/
interior membership) and `audit/material_identity_step2_20260921/data/
forward_material_trace_seed501.csv` (the material trace's own centroid per
step). Trigger state (t0=30) independently verified reproducible
bit-for-bit from the raw episode seed (`reproduce_trigger_states.py`,
`data/trigger_state_reproduction.json`).

## Trigger and target

Qualification: t=30, `target_heading=2` (verified from the log's
`qualified_and_target_set` event — matches the task's assumed t0=30
exactly). Interior at qualification: 30 exact bird IDs (recovered from
`viz_bundle` frame 30).

## Actuator schedule (exact, from the production log)

| refresh t | actuator set (B_C) | held through |
|---|---|---|
| 30 | `[2, 8, 9, 11, 24, 28, 34, 80]` | t=30–38 (9 steps) |
| 39 | `[65, 2, 28, 31, 34, 59, 80, 92]` | t=39–47 (9 steps) |
| 48 | `[2, 23, 28, 34, 55, 65, 72, 79]` | t=48–53 (6 steps, control ends t=53) |

`REINFER_AUTHORITY_EVERY=8` (`run_online_control_611.py:67`); refreshes
land at age_authority resetting to 0 at t=30, 39, 48 — consistent with the
constant (first refresh always fires since `B_C_cache is None` initially,
subsequent refreshes at +9/+9 rather than a flat +8 because `need_auth`
triggers on `age_authority >= REINFER_AUTHORITY_EVERY`, and age increments
once per step starting the step AFTER a refresh — an off-by-one-in-spirit
but not a bug, confirmed by direct count of the logged cadence).

## Answering the task's specific questions

**Was an authority refresh performed while v1 was on the wrong flock
(t=32–35)?** **No.** The refresh at t=30 (before the detour) set
`[2, 8, 9, 11, 24, 28, 34, 80]`; the next refresh is at t=39, four steps
AFTER v1 reconverges at t=36 (Step 2's finding). The detour window
(t=32–35) falls entirely inside the *first* actuator set's 9-step hold,
with no re-inference triggered during it.

**Were actuators changed during that interval?** **No** — same 8 actuator
IDs held from t=30 through t=38 inclusive, spanning the entire detour and
several steps on both sides of it.

**Were the active actuators still connected/near the actual material
target during the detour?** This pass computed torus-aware distance from
each actuator's position to the material trace's own centroid
(`forward_material_trace_seed501.csv`'s `centroid_x`/`centroid_y`, i.e.
the object the material trace — not v1 — was tracking) at every step
t=30–39:

| t | v1 interior size | actuators inside v1's (possibly wrong) interior | mean actuator→material-centroid distance | min distance | local density scale |
|---|---|---|---|---|---|
| 30 | 30 | 0/8 | 3.73 | 3.39 | 0.65 |
| 31 | 35 | 1/8 | 3.78 | 2.48 | 0.59 |
| 32 | 23 | 4/8 | 3.35 | 1.24 | 0.64 |
| 33 | 23 | 4/8 | 3.00 | 0.57 | 0.59 |
| 34 | 23 | 4/8 | 3.03 | 0.57 | 0.62 |
| 35 | 23 | 4/8 | 3.05 | 0.75 | 0.61 |
| 36 | 46 | 5/8 | 2.81 | 0.15 | 0.60 |
| 37 | 40 | 2/8 | 3.03 | 0.18 | 0.60 |
| 38 | 40 | 2/8 | 3.12 | 0.31 | 0.58 |
| 39 | 40 | 2/8 | 3.22 | 0.46 | 0.60 |

**Yes, actuators remained physically close to the material target
throughout the detour** — at every step, at least one actuator sits within
0.6–1.2 spatial units of the material centroid (well within a few local
density-scale units, and inside or at the edge of the true interaction
radius R=1.6 — noting the true R is used here only as a known repository
constant for interpretive scale, not as part of any scoring rule). Mean
distance stays in a tight 3.0–3.8 range throughout, never spiking the way
it would if the actuators had "gone with" an unrelated population. This is
consistent with (not proof of) actuators retaining genuine physical
influence on the material target even while v1's DISPLAY temporarily
pointed elsewhere — the actuators were never told to track v1's pointer;
`forced = {j: target_heading for j in B_C_cache["B_C"]}`
(`run_online_control_611.py:243`) simply forces a fixed heading on a fixed
bird-ID set for the duration of the hold, independent of which population
any tracker currently displays as "the interior."

**When did the material flock begin its turn relative to these events?**
Per Step 2 (`seed_501_identity.md`): 0.233 (t=30, qualification) → rising
through control → 0.759 (t=52, end of control) → 0.971 (t=76, end of
release). The rise is gradual across the whole control window, not
concentrated at or after the t=36 reconvergence — i.e. it does not look
like "the turn only starts once v1 catches up," consistent with the
actuators having been physically coupled to the material target the whole
time (table above), independent of what v1 displayed.

## What this does NOT establish

This timeline is descriptive (what did the historical run actually do,
and where were the actuators relative to what object). It does **not**
establish that the forcing CAUSED the observed alignment rise — that is
the separate, harder question `seed501_schedule_effect.py` /
`seed_501_causal.md` address via paired no-forcing and matched-random
comparisons from the same trigger state.
