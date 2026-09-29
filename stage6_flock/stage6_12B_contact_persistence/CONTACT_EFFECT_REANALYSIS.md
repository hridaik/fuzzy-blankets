# Contact-Effect Reanalysis (Part I, existing Stage 6.12 data)

Full detail in `stage6_flock/stage6_12_control_readiness/STAGE612_
CORRECTION_MEMO.md` §5-6 and `data/correction_612_summary.json
["paired_effect_vs_mechanism"]`. This document isolates the corrected
mechanism analysis and states plainly what changed.

## What Stage 6.12's original `MECHANISM_ANALYSIS.md` did

Compared ABSOLUTE outcome groups: rollouts with `J > 0.3` (n=34) vs.
`J ≤ 0.3` (n=1262), on raw mechanism diagnostics. Found ~10× differences
(direct contacts at t0: 0.118 vs 0.006; cumulative contact edges: 110 vs
13; unique coverage: 13.7 vs 2.6).

**Problem**: this compares POST-treatment absolute outcomes, not a PAIRED
CAUSAL EFFECT. A rollout can reach `J>0.3` because (a) the state's
no-control baseline was already high, (b) the state's `ForwardMaterialTrace`
permissively continued through a split, or (c) the intervention genuinely
helped — the original comparison could not distinguish these.

## Corrected analysis: paired ΔJ vs. POST-TREATMENT mechanism correlates

(explicitly labelled post-treatment — never treated as a pre-treatment
predictor or as evidence of causal direction, per task brief S8/S31)

Spearman rank correlation, `Δ(J_assoc)` vs. mechanism diagnostic, n=1,296:

| diagnostic | ρ (all rollouts) | ρ (n=830, no split/merge flag) |
|---|---|---|
| direct contacts at t0 | **+0.199** | **+0.207** |
| cumulative contact edges | +0.022 | +0.053 |
| unique target coverage | +0.016 | +0.052 |
| mean actuator-target distance at t0 | +0.033 | +0.036 |
| actuators entered target | +0.123 | +0.139 |

Top-vs-bottom quartile of `Δ(J_assoc)` (n=324 each): cumulative contact
edges and unique coverage are actually HIGHER in the BOTTOM quartile
(29.1 vs 23.8 edges; 4.58 vs 4.30 coverage) — the opposite direction from
the original absolute-outcome comparison.

## Conclusion

**The original ~10× "sustained contact predicts success" finding does not
survive being recomputed as a paired causal effect.** What survives,
weakly and consistently (both in the full sample and restricted to clean
no-split trajectories) is: `direct_contacts_at_t0` (ρ≈0.20) and
`actuators_entered_target` (ρ≈0.12-0.14). Cumulative contact accumulated
DURING forcing does not show the strong positive association originally
reported — if anything it trends the opposite direction in the quartile
contrast. **This is a genuine downgrade of the contact-persistence lead's
strength**, motivating Stage 6.12B's design as a prospective test with
correctly paired, pre-registered predictors (§`CONTACT_PREDICTOR_
ANALYSIS.md`) rather than continued reliance on this backward-looking,
correlational, mostly-null-corrected signal.
