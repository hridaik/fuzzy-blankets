# Intervention timing — original 6.11 vs. repaired 6.11B semantics

Recovered from `METHODS_AUDIT_6_11.md` §1 (source-cited, worked-example
verified against production output field-for-field) and
`branch_adjudication_611.py`'s branch definitions/comments. Not re-derived
from scratch; this document restates it as a compact timing table because
the handoff's own version of this material was flagged as corrupted.

## Original Stage 6.11 (production, `run_online_control_611.py`)

Per real simulator step `t`, while `phase == "control"`:

1. **State at `t`**: `(r_t, z_t)` from the previous step's `mf.step`.
2. **Candidate detection**: `detect_69.propose(r_t, z_window, L)` — every
   step (`run_online_control_611.py:167`).
3. **Lineage update**: `LineageTracker611.update(cands, r_t, z_t, t)` —
   every step; `Î_t = dominant_interior()` — every step.
4. **Refresh gates** (independent cadences, all counted in real steps since
   the last refresh):
   - `B̂pred`: every `REINFER_PRED_EVERY*3 = 36` steps.
   - `B̂causal`: every `REINFER_CAUSAL_EVERY = 8` steps.
   - `Â_t`/`B̂C` (actuator set): every `REINFER_AUTHORITY_EVERY = 8` steps.
   When a refresh is due: recompute `exterior_pool = near_exterior(mf, r_t,
   Î_t, radius_factor=3.0)` (oracle pool, firewall violation), then
   `B̂causal = probe_sources(...)` (computed, logged, **not consumed
   downstream**) and `B_C_cache = select_actuators(...)` (plain top-K,
   `k_act=8`, no abstention) — both independently, from the same pool.
5. **Actuation, EVERY step regardless of refresh**: `forced = {j:
   target_heading for j in B_C_cache["B_C"]}`; `mf.step(r_t, z_t, rng,
   forced_actions=forced)` (`run_online_control_611.py:243,276`). The
   **estimator that selected `B_C_cache` assumed a one-shot forced action
   at step 0 of a τ=4 rollout, released thereafter** (`intervention_api_611
   .py:121-127`) — but the controller instead holds the SAME forced heading
   on the SAME actuator set for every real step until the next 8-step
   refresh. **This is the intervention-duration mismatch**
   (`METHODS_AUDIT_6_11.md` §1.5): the quantity used to choose actuators is
   not the quantity the controller actually executes.
6. **`target_heading` itself**: fixed once, at qualification
   (`t=t_qualify`), as `ROT_CCW[bearing_to_cardinal(bulk_delta)]` — never
   re-derived from the current bulk direction during control
   (`run_online_control_611.py:195`, `METHODS_AUDIT_6_11.md` §1.6).
7. **Control window**: `T_CONTROL` real steps from qualification (24 steps
   in the reported 5-seed result — confirmed per-seed in
   `interactive_demo/v2/data/tab6_translation.json`'s `events` list, e.g.
   seed 500: `qualified_and_target_set` at t=61, `release_begin` at t=84 —
   `84-61=23` real control steps recorded, i.e. `T_CONTROL=23` inclusive
   framing; see individual seed files for the exact per-seed count).
8. **Release**: control stops, `forced_actions=None` thereafter, tracker
   and candidate detection continue running unforced through `episode_end`.
9. **Outcome evaluation**: `frac_interior_at_target` logged every control
   and release step (`online_control_611__seed{n}.json`'s `log`), used for
   the original "3/5 turned" call — exact numeric threshold for that call
   is **not** present as a named constant anywhere in `run_online_control
   _611.py` or `analyze_online_control_611.py`; `RESULTS_6_11.md` is the
   authoritative source for how that qualitative label was assigned, and is
   cited, not re-derived, here (flagged as a `code_provenance.md` /
   `audit_findings.md` open item — see below).

## Repaired 6.11B semantics (`branch_adjudication_611.py`, audit-only)

Branches 6–9 (`repaired_blind_authority`, `repaired_direct_causal_restricted`,
`exact_direct_interface_repaired`, `beam_search_benchmark`) select their
actuator set **ONCE at t0** and hold it fixed for the **entire** 24-step
control window — no re-planning mid-window (a disclosed compute-budget
simplification, `branch_adjudication_611.py:31-37`, not silently chosen).
Their authority estimand is `A_S(τ=4, d=4)` — forced for the full 4-step
evaluation horizon, matching the OLD τ=4 window's own length exactly, which
"at minimum removes the one-shot-then-released mismatch inside the same
horizon the original method already used" (script comment,
`branch_adjudication_611.py:39-46`); a `d=8` spot-check exists separately,
at reduced rollout budget, in `AUTHORITY_AND_SET_EFFECT_AUDIT.md` (not
repeated for all 9 branches — disclosed, not silent). Branch 2
(`original_reproduced`) deliberately KEEPS the original refresh-every-8-steps
cadence, because it exists specifically to reproduce the original algorithm's
own logic, not to repair it.

## Compact timing diagram

```
ORIGINAL (production):
  t=qualify .. qualify+23        : control. Every step: force B_C_cache
                                    (same set for up to 8 steps at a time).
                                    Every 8 steps: re-select B_C via a
                                    one-shot-then-released τ=4 estimate.
  t=qualify+24 .. qualify+47     : release. No forcing. Tracker keeps running.

REPAIRED, single-shot (6.11B, branches 6-9):
  t0                             : select S ONCE, via A_S(τ=4, d=4),
                                    top-K<=8 with abstention (ci_lo>0).
  t0 .. t0+23                    : hold S forced at h_star, no re-selection.
  t0+24 .. t0+47                 : release. No forcing.

REPAIRED, cadence-matched reproduction (6.11B, branch 2, "original_reproduced"):
  t0 .. t0+23                    : same refresh-every-8-steps cadence as
                                    production, but under fresh CRN (see
                                    FIVE_SEED_CAUSAL_ADJUDICATION.md's
                                    interpretive note: numbers will not
                                    numerically match RESULTS_6_11.md's own
                                    sample path for the same seed).
```

## Why the original planning/execution mismatch occurred (confirmed by code inspection)

The authority estimator (`MultiStepAuthorityProbe`, designed for a
one-step-causal-probe-adjacent use case) was reused for actuator *selection*
without updating its own rollout semantics to match how the controller
actually holds actuation. Both pieces of code are individually correct for
what they each implement; the mismatch is an integration defect between
`intervention_api_611.MultiStepAuthorityProbe._rollout` (one-shot-at-step-0)
and `run_online_control_611.py`'s control loop (continuous hold until next
refresh) — confirmed by reading both, not inferred from behavior.
`METHODS_AUDIT_6_11.md` §1.5 is the first documented identification of this;
this audit did not find an earlier one.

## Confirming the repaired 6.11B semantics by test

`audit/test_authority_v2_611.py` and `audit/test_lineage_v2_611.py` exist
and were collected by pytest as of the last `.pytest_cache` run in this
directory (`stage6_11_translating_torus/.pytest_cache/v/cache/nodeids`
lists both). This audit did not re-run the full test suite (out of scope
for a read-only evidence-recovery pass); their existence and collection is
cited as evidence the repaired semantics have at least unit-level coverage,
not as a re-certification of that coverage's adequacy.
