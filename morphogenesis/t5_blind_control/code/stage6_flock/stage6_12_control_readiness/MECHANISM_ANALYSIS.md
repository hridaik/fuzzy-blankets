# Stage 6.12 — Mechanism Analysis (audit-only; exploratory)

## Method

`intervention_612.mechanism_diagnostics` logs, for every Phase-A rollout
(1,296 total; never Phase B/C, which run `with_mechanism=False` to keep
search/holdout compute bounded — these diagnostics are audit-only and were
never used to choose or filter actuator sets anywhere in the primary
pipeline), using the TRUE interaction radius `R` (oracle information
withheld from the primary nearest-20 pool definition itself):
`mech_direct_contacts_t0`, `mech_cumulative_contact_edges`,
`mech_unique_target_coverage`, `mech_mean_actuator_target_dist`,
`mech_min_actuator_target_dist`, `mech_actuators_entered_target`,
`mech_actuators_lost_all_contact_step`.

## Result (exploratory; success defined post hoc as `J > 0.3`)

Of 1,296 Phase-A rollouts, **34 (2.6%) reached `J > 0.3`** (persistent,
identity-valid alignment above 0.3 in the final 8 release steps).
Comparing those 34 to the remaining 1,262:

| diagnostic | J>0.3 (n=34) mean | J≤0.3 (n=1262) mean |
|---|---|---|
| direct actuator-target contacts at t0 | 0.118 | 0.006 |
| cumulative contact edges during forcing | 109.9 | 13.4 |
| unique target members ever contacted | 13.7 | 2.6 |
| mean actuator-target distance at t0 | 2.42 | 2.33 |
| actuators that entered the target by end of forcing | 0.71 | 0.17 |

**Successful rollouts have roughly an order of magnitude more direct
contact and coverage during forcing than unsuccessful ones** — this is the
single clearest signal in the whole Stage 6.12 dataset. Mean actuator-target
distance at `t0` is barely different between the two groups (2.42 vs 2.33),
so **initial proximity alone is a weak discriminator**; it is *sustained
contact accumulated over the forcing window* (cumulative edges, unique
coverage) that tracks success, not the nearest-20 pool's own distance
ranking. Given the primary pool is defined purely by nearest-neighbour
distance at `t0`, this is a real gap between what the primary (blind) pool
selects for and what mechanistically drives the rare successes it does
produce.

**Caveat**: this is a post hoc, exploratory, correlational comparison on a
strongly imbalanced sample (34 vs 1262) drawn from a Monte Carlo budget
this stage has already disclosed as small; it is reported to motivate
`NEXT_STAGE_RECOMMENDATIONS.md`, not as a validated predictive rule, and it
was never used to select or filter which actuator sets Phase A itself
tested (Phase A's sets were drawn uniformly from the nearest-20 pool before
any outcome was known).

## Implication

If a future authority estimator is built, this result argues for
conditioning it on projected/dynamic contact persistence (which nearest-20
by itself does not capture, since a bird "nearest at `t0`" can still lose
all contact within a step or two as the flock moves) rather than on static
`t0` distance alone.
