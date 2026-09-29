# Interior Actuation Method Note

**This is a methodology note only. No interior-actuation intervention is
designed, implemented, or run here.** Its purpose is narrow: establish, in
advance of that future experiment, a scoring correction that prevents a
trivial artifact from being mistaken for a real finding, per the task
brief's item 16.

## The trivial-inflation risk, stated precisely

Every outcome metric this programme uses (`J`, `J_assoc`, `J_conservative`,
and their `ΔJ` forms) is built from `A_release_late`, itself derived from
`V * (fraction of currently-traced target members satisfying some alignment
condition at the end of the release window)` -- see
`stage6_12_control_readiness/code/intervention_612.py` lines ~100-140. The
denominator of that fraction is the traced target's member count at the
relevant frame (`len(hist[i].accepted_members)`).

For every experiment run so far (Stage 6.9 through 6.12C), the forced
actuator `S` is drawn from the EXTERIOR pool (`pool20`, `nearest_M_pool`) --
by construction, `S` starts OUTSIDE the traced target `seed_members`. If the
actuator later enters the target (per `CONTACT_METRIC_AUDIT.md` and
`MEMBERSHIP_EMBEDDING_CLUES.md`, whether or how often this happens was not
even measured in the persisted data, but it is geometrically possible), it
becomes one of the `|target|` members counted in the denominator, and its
own forced-to-`h_star` heading trivially satisfies whatever alignment
condition defines the numerator (it IS at `h_star`, that is what forcing
means) -- so its own presence in the traced target inflates the metric by
approximately `1/|target|` PURELY MECHANICALLY, with zero contribution from
any actual reorganization of the rest of the collective.

**This risk does not apply to any Stage 6.9-6.12C result reported so far**
(the actuator is exterior throughout; whether it drifts in during release is
unmeasured but the forcing itself never targets an interior bird). It WILL
apply directly, and non-trivially, to any future experiment that forces an
actuator that is ALREADY an interior target member (or that the task brief's
"interior-vs-exterior" framing implies forcing a currently-interior bird
specifically to test whether interior status changes the actuator's
leverage) -- exactly the experiment this note is meant to guard.

## The required correction

For a future interior actuator `j` (a bird ID inside `seed_members`/the
traced target at t0, or that enters the traced target at some point during
the forcing/release window under evaluation):

1. Define **`A_minus_j`**: the fraction of alignment computed over
   `target_members(t) \ {j}` (the traced target's members at the relevant
   frame MINUS the forced bird itself), not over the full `target_members(t)`
   set the current metric uses. This requires per-frame membership sets to
   already be available (they are -- `hist[i].accepted_members`, already
   computed by `ForwardMaterialTrace611` for every rollout; only the
   OUTCOME-METRIC aggregation step needs to exclude `j`, not the tracer
   itself).

2. Define **`J_minus_j`** analogously to the existing `J` definitions
   (`V * A_minus_j_release_late`, and conservative/assoc variants), using
   `A_minus_j` in place of `A_release_late` throughout.

3. Report BOTH `ΔJ` (current definition, includes the forced bird's own
   trivial contribution when it is interior) and `ΔJ_minus_j` (excludes it)
   for every interior-actuator rollout, and treat any claim of "the
   collective reorganized around the interior actuator" as requiring
   `ΔJ_minus_j` to show the effect -- `ΔJ` alone, for an interior actuator,
   is not sufficient evidence, since it cannot distinguish "the rest of the
   target reorganized" from "the forced bird's own state was trivially
   counted."

4. **Identity-aware persistence, not just count.** `A_minus_j` should be
   computed using a genuine post-treatment identity-tracking definition
   (which unforced birds from the ORIGINAL `t0` target are STILL members,
   individually, at the evaluation frame, excluding `j` from both the
   original set and the current set) -- not merely
   `(|target(t)|-1)/|target(t)|`-style count arithmetic, which would still
   be vulnerable to `j`'s presence changing `|target(t)|` itself (e.g. if
   `j`'s forced entry causes a `split_flag`/`merge_flag` event that the
   tracer logs, `|target(t)|` is affected by `j`'s presence even in the
   denominator, not just the numerator). The existing
   `ForwardMaterialTrace611` machinery (Jaccard-based continuity, already
   used throughout Stage 6.11/6.12/6.12B/6.12C) is the natural basis for
   this -- it is not being proposed as new machinery, only as needing to be
   RE-AGGREGATED with `j` excluded, per point 1.

## What this note does NOT do

Specify which interior birds to test, what d/K to use, how many states, or
any other design parameter of the future interior-actuation experiment --
those are that experiment's own decisions, to be made when (and if) it is
designed, informed by `NEXT_EXPERIMENT_DECISION.md`'s recommendation on
whether that experiment is the right next step at all. Implement
`A_minus_j`/`J_minus_j` in code. Run any rollout.
