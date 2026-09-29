# Existing-Data Clues About Collective-Membership Privilege

**Exploratory and non-causal throughout, per the task brief's explicit
instruction.** No interior-actuation experiment is run or designed here.
This document only asks whether Stage 6.12C's ALREADY-COMPUTED rollout-level
fields hint at an association between an exterior actuator's realized
effect and its subsequent relationship to the traced target -- as a
motivation check for whether the (separate, future) interior-actuation
experiment is worth running, not as evidence of a mechanism.

## What Stage 6.12C actually persisted, per rollout

From `k1_rollouts_612c.json` (2,400 rows): `delta_conservative`, `V`,
`V_conservative`, `event`/`event_corrected`, `target_size_end`,
`mech_cumulative_contact_edges`, `mech_direct_contacts_t0`,
`align_end_forcing`, `end_of_release_alignment`. Stage 6.12C's own
`mechanism_diagnostics` function (`intervention_612.py`) additionally
computes `mech_actuators_entered_target` (whether the actuator's OWN bird ID
is among the traced target's `accepted_members` by the end of the forcing
window) -- **but this field is NOT written into `k1_rollouts_612c.json`'s
per-rollout dict** (checked directly against `run_confirmatory_612c.py`'s
`rollout_rows.append(...)` call, which lists the exact set of keys written;
`mech_actuators_entered_target` is not among them, and neither
`time_to_entry`, `duration_of_target_membership_after_entry`, nor any
lineage-tracking field is computed or persisted anywhere in Stage 6.12C's
code or data).

**Per the task brief's own instruction ("If required fields were not
persisted, say so rather than reconstructing them approximately"): the
specific quantities item 15 asks for -- actuator later entering the target,
time-to-entry, duration of membership after entry, candidate/material
lineage -- are NOT available in this dataset and are not reconstructed
here.** Reconstructing them would require re-deriving actuator/target
overlap trajectory from `r_hist`/`z_hist`/`hist[i].accepted_members`, which
are not saved to disk either (only their aggregate consequences, like
`target_size_end`, survive in the JSON) -- doing so would require re-running
the traced simulation, which is explicitly out of scope for this bounded,
analysis-only follow-up.

## What IS available, examined as weak, pooled, non-causal, non-state-clustered exploratory associations

Two proxies are available in the persisted data and were checked:

1. **`mech_cumulative_contact_edges`** (geometric proximity during forcing,
   see `CONTACT_METRIC_AUDIT.md`) vs. `delta_conservative`: pooled Spearman
   rho across all 2,400 rollouts = **-0.040** (p=0.049, barely below the
   conventional 0.05 threshold on a POOLED, non-independent sample -- 20
   candidates x 12 streams within a state are not independent draws, so this
   p-value should not be trusted at face value). Per-state Spearman rho
   (state-clustered, the discipline this whole programme otherwise insists
   on): `[0.037, -0.169, 0.084, -0.021, -0.103, -0.111, 0.105, -0.075,
   0.046, 0.074]`, mean **-0.013**. **No consistent association, sign
   flips across states, centered near zero.** If anything, weakly
   consistent with `ORACLE_DECOMPOSITION.md`'s existing finding that more
   geometric contact does not predict higher effect.

2. **`target_size_end`** (does the traced target end up LARGER when this
   actuator was forced, a coarse proxy for "did the collective grow,"
   which COULD partly reflect the actuator or other birds joining) vs.
   `delta_conservative`: pooled Spearman rho = -0.012 (p=0.55, not
   significant even ignoring the independence caveat). Per-state rho:
   `[-0.046, 0.139, -0.002, 0.032, 0.045, -0.043, -0.093, -0.082, 0.124,
   0.032]`, mean **+0.011**. Again centered near zero, no consistent sign.

3. **Identity-validity stratification** (`V_conservative`): mean
   `delta_conservative` is **+0.0055** when the trace stays conservative-valid
   (`V_conservative=1`, n=2,190/2,400 rollouts) vs. **-0.0178** when it does
   not (`V_conservative=0`, split/merge-flagged rollouts, n=210/2,400).
   This is the clearest pooled association in the data, but it is close to
   definitional: `V_conservative=0` rollouts are exactly the ones where
   `J_conservative` is heavily penalized by construction (any split/merge
   flag anywhere zeroes out the conservative identity term), so a negative
   mean `delta_conservative` among them is close to circular, not an
   independent signal about membership privilege.

## Purpose-relevant conclusion (motivation check only)

**These are all POST-TREATMENT, weak, sign-inconsistent, pooled associations
-- none of them constitute evidence of "membership privilege" and none
should be read as motivating or de-motivating the interior-actuation
experiment on their own.** The honest statement is narrower: this dataset
does not contain the fields (entry timing, membership duration) that would
be needed to check the membership-privilege hypothesis even
exploratorily, and the two proxies that ARE available (contact-during-
forcing, final target size) show no consistent relationship with effect
size. This absence of a signal in a WEAK, indirect proxy is not evidence
against the hypothesis (a proper test requires the interior-actuation
experiment's own directly-forced-interior-member design, which by
construction starts an actuator already inside the target rather than
asking whether an exterior actuator drifts in) -- it simply means Stage
6.12C's existing data cannot adjudicate this question, which is consistent
with `NEXT_STAGE_DECISION.md`'s own framing of "membership privilege" as an
untested hypothesis for the next task, not a finding of any prior one.
