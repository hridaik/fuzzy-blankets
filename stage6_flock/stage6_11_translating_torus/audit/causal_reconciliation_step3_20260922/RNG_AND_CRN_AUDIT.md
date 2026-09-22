# RNG and common-random-number (CRN) audit (Task F0)

Performed **before** any paired-branch causal claim, per the task's
explicit ordering requirement. Code: `code/rng_crn_diagnostic.py`,
`code/reproduce_trigger_states.py`. Raw results:
`data/rng_crn_diagnostic.json`, `data/trigger_state_reproduction.json`.

## 1. How the simulator consumes randomness (source-read, cited)

`flock_sim/active_inference.py:sample_categorical_rows` (lines 102–110)
draws exactly `probs.shape[0]` (= N = 400) uniforms via a single
`rng.random(N)` call, **unconditionally** — the draw count never depends
on the probability values. `MovingFlock611.step_cached`
(`moving_flock_611.py:189–203`, and the inherited, equivalent `step`) calls
this **exactly twice per step**, in a fixed order: (1) the action draw,
(2) the heading-transition draw. `forced_actions` only **overwrites**
`applied` entries **after** the first draw already happened
(`moving_flock_611.py:198–200`) — it never adds, removes, or reorders an
RNG call.

**Finding 1 (confirmed, `rng_crn_diagnostic.py:demo_1`)**: at the
PHYSICS-STEP level, forcing some birds' actions does not, by itself,
change how many random draws are consumed or in what order. Two branches
sharing one `rng` object, one forcing 40 birds every step and one forcing
none, leave that shared generator at the **identical stream position**
after 10 steps (verified via a canary draw immediately afterward:
bit-identical to machine precision).

## 2. Where naive same-seed CRN breaks: the online control loop

`run_online_control_611.py:run_episode` shares **one** `rng` object
(`np.random.default_rng(seed)`, line 120) between:
- physics (`mf.step`, 2 draws/step, always — finding 1 above);
- the online passive-model buffer sample (`rng.choice(mf.N, size=20,
  replace=False)`, line 140) — **unconditional**, fires every step
  regardless of phase;
- **and**, only while `phase == "control"` and only on re-inference steps
  (`need_pred`/`need_causal`, age-gated, always true on the first control
  step since the caches start `None`): `PB.rows_for_targets(..., rng, ...)`
  (line 216) and `PR.probe_sources(..., rng, ...)` (line 230), both of
  which consume additional draws from the **same shared** `rng`.
  (`CA.select_actuators`/`MultiStepAuthorityProbe`/`FiniteProbeMoving611`
  already use their **own** independently-seeded generators —
  `seed=1000+t+rep`, `seed=2000+t` — not the shared `rng`; those are
  already correctly isolated in the existing production code.)

**Finding 2 (confirmed, `rng_crn_diagnostic.py:demo_2`)**: a "no-control"
branch never executes the control-phase-only calls; a "with-control"
branch does, starting at its first control step. Minimal reproduction: two
branches sharing one `np.random.default_rng(42)`, **forced_actions=None in
BOTH** (so no bird's action is ever overridden in either branch) — one
additionally consumes a stand-in for the control-phase auxiliary draws,
the other does not. Result: **73.75% of birds have a different heading by
t=10**, purely from the shared stream being at different positions — with
zero difference in what was actually forced.

**Conclusion: same top-level seed is NOT sufficient for valid CRN between
a no-control and a with-control branch of the actual
`run_online_control_611.py` production loop**, because the control
decision machinery and the physics step share one RNG object. This is
exactly the risk the task instructed to check rather than assume.

## 3. Audit-only fix used throughout this directory's Task F1–F3 scripts

**Finding 3 (confirmed, `rng_crn_diagnostic.py:demo_3`)**: routing physics
through a **dedicated** generator that no decision-making code ever
touches keeps branches' physics draws aligned regardless of how much (or
how differently) their decision-side code consumes, as long as that
decision-side code uses a **separate** generator instance. Two branches
with different decision-side consumption patterns (one draws nothing
extra, one draws 37 extra values from its OWN separate stream) produce
**bit-identical** physics `z` trajectories after 10 steps.

This is implemented as: every Task F1–F3 rollout in this directory calls
`mf.step(r, z, rng_physics, forced_actions=...)` with `rng_physics` a
generator that is **never** passed to any predictive/causal/authority
estimation code. Where a script needs decision-side randomness at all
(e.g. drawing a matched-random actuator set), it uses an **independent**
generator (`rng_for_draw` in `seed501_schedule_effect.py`), never
`rng_physics`. This changes **only** which generator object feeds which
subsystem — no update equation, controller information, or model
semantics is altered (per the task's explicit constraint), and it is
audit-only: no production file (`run_online_control_611.py`,
`moving_flock_611.py`, `intervention_api_611.py`, etc.) was edited.

**Important correction, disclosed rather than hidden (`demo_4`)**: an
earlier draft assumed the "physics-irrelevant" buffer-sampling draw
(`rng.choice(20)`, line 140) could simply be omitted from an audit replay
without consequence, since it never feeds back into `r`/`z` directly.
**This is wrong for EXACT historical reproduction**: because it still
consumes from the shared production stream, omitting it shifts every
subsequent physics draw's stream position, changing the actual sampled
`z`-trajectory. `demo_4` confirms: a naive harness that skips this call
does **not** bit-for-bit reproduce a real production trajectory, while one
that replays the exact call sequence (physics call, then the buffer draw,
every step, in order) does. **Consequence**: `reproduce_trigger_states.py`
replays `run_online_control_611.py`'s exact uncontrolled-phase call
pattern verbatim (not a hand-simplified equivalent) to recover each seed's
trigger state.

## 4. Trigger-state reproduction: verified for all 5 control seeds

`code/reproduce_trigger_states.py` replays each seed's raw episode seed
forward (exact production call sequence, forced_actions=None throughout,
since this is entirely before the control phase starts) to the seed's own
recorded qualification time `t0`, and compares against the recorded
`(r, z)` in `data/viz_bundle_611__seed{n}.json` at that frame.

| seed | t0 (from production log) | r match | z match | status |
|---|---|---|---|---|
| 500 | 61 | yes | yes | REPRODUCED_EXACTLY |
| 501 | 30 | yes | yes | REPRODUCED_EXACTLY |
| 502 | 30 | yes | yes | REPRODUCED_EXACTLY |
| 503 | 35 | yes | yes | REPRODUCED_EXACTLY |
| 504 | 47 | yes | yes | REPRODUCED_EXACTLY |

**All five trigger states reproduce bit-for-bit** (`r` matched to
`atol=1e-9`, `z` matched exactly as integers). No stop condition applies
here for any seed — this closes one of spec §19's listed potential
blockers ("old trigger state cannot be reproduced") for all five seeds.

## 5. What this licenses, and what it does not

**Licensed**: schedule-effect comparisons (Task F1 §10.1 etc.) that
replay a FIXED, pre-determined `forced_actions` schedule (whether the
exact historical one, empty, or a pre-drawn random one) via a dedicated
physics-only RNG stream, paired across branches by using the identical
physics seed. This is used by `seed501_schedule_effect.py`.

**NOT licensed without further work**: a naive "just re-run
`run_online_control_611.run_episode` twice with the same top-level seed,
once with control enabled and once without" comparison — per Finding 2,
this does NOT give valid CRN, because the control loop's own re-inference
machinery desyncs the shared stream the moment control begins. A POLICY-
effect comparison (Task F1 §10.2, re-running the actual online controller
including its own decision logic) that wants CRN-paired physics against a
no-control branch would need the control loop's auxiliary
predictive/causal-probing calls re-routed to their own dedicated
generator, decoupled from physics — an audit-only fork of
`run_online_control_611.py`'s loop body (not an edit to the production
file), which is a substantially larger undertaking than the schedule-
effect harness. See `NEXT_CONTROLLER_SPEC_INPUTS.md` /
`FINAL_STAGE611_ADJUDICATION.md` for how far this pass got on policy
effect given that cost.

## 6. Stop conditions checked against (spec §19)

- "old trigger state cannot be reproduced" — **does not apply**, verified
  reproducible for all 5 seeds (§4).
- "CRN validity cannot be established" — **does not apply** for the
  schedule-effect estimand (§3, verified); **partially applies** for a
  naive full-policy-loop CRN pairing (§5), which this pass avoids rather
  than assumes valid.
- "audit-only RNG coupling changes simulator semantics" — checked and
  rejected: the dedicated-stream harness calls the exact same
  `mf.step`/`step_cached` functions with the exact same arguments except
  which generator object is passed; no update equation changed (§3).
