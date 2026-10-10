# Stage 6.12 — Collateral Analysis

## Method

For every Phase-A rollout, `intervention_612.mechanism_diagnostics` logs
coarse organizational/collateral readouts (S18; no new multi-object
identity system was built): `collateral_target_size_start/final`
(traced-target size at `t0` vs. the last traced frame) and
`collateral_frac_forced_heading_start/final` (fraction of birds that are
NEITHER the traced target NOR an actuator, at `h_star`, at `t0` vs. the
final traced frame).

## Results (n=1296 Phase-A rollouts)

- **Non-target, non-actuator birds at `h_star`**: mean 0.273 at `t0` →
  0.292 at the final traced frame. A small (+0.019) rise, consistent with
  the null baseline: with 4 cardinal headings roughly balanced in an
  uncontrolled flock, ~0.25 is close to chance-level occupancy of any one
  heading, and this stage's rollouts are dominated by short, mostly-
  ineffective forcing (§ READINESS_MAP.md). There is **no evidence of
  large collateral heading contamination** spreading from the forced
  actuators into the wider flock at this budget.
- **Target size**: mean 32.4 at `t0` → 40.5 at the final traced frame (a
  +25% mean rise). This is dominated by the high split-flag rate
  (`confirmed_split` on 34.4% of rollouts — `IDENTITY_AND_DISRUPTION.md`):
  `ForwardMaterialTrace611`'s split handling continues tracking the
  LARGER daughter by absolute retained count, and daughters plus newly
  adjacent recruits can grow the accepted set even while V remains 1 (the
  split is flagged, not blocking). **Target growth here is a tracker/
  organizational artifact, not evidence that forcing recruits new material
  into a stable target** — it is reported so it is visible, not smoothed
  into the alignment numbers.

## Interpretation

Collateral effects at the tested budgets are modest (heading contamination)
to organizationally noisy (target-size drift via frequent, mostly-flagged
splits) — neither rises to a level that would itself explain the
near-zero `G_sus` headline finding, but the split-driven size drift is a
relevant caveat for any future controller that uses target size as a
stopping/re-qualification signal.
