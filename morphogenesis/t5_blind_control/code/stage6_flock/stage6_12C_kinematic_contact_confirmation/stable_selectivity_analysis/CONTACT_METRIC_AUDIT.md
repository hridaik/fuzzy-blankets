# Contact Metric Audit

Source-code audit (no computation beyond reading the two relevant
functions). This determines exactly what Stage 6.12C's contact-based
conclusions (`ORACLE_DECOMPOSITION.md`, `NEXT_STAGE_DECISION.md`) did and
did not rule out.

## Question: what does `mech_cumulative_contact_edges` actually count?

Source: `stage6_flock/stage6_12_control_readiness/code/intervention_612.py`,
function `mechanism_diagnostics` (lines ~146-204):

```python
delta = C.torus_delta(r_hist[i][S_arr][:, None, :], r_hist[i][mem_arr][None, :, :], mf.L)
D = np.sqrt((delta ** 2).sum(-1))
contact = D <= mf.R
cum_edges += int(contact.sum())
```

This computes, for every step `i` of the `d`-step forcing window, the
pairwise torus distance between every actuator in `S` and every currently-
traced target member, thresholds it at `D <= mf.R` (the SAME numeric radius
`R` the simulator's own interaction model uses), and sums the count of
`True` cells across all actuator-member pairs and all `d` steps.

**Answer: (A) distance < R only.** No field-of-view term, no directionality,
no weighting. It is a plain symmetric geometric-proximity count: `contact[a,m]
= 1` iff `|r_a - r_m| <= R` on the torus, for actuator `a` and target member
`m`, regardless of which way either bird is facing. `mech_direct_contacts_t0`
(the t0-only version) is the identical rule evaluated at a single step.

## Question: is this the same relation the simulator's own update step actually uses?

Source: `stage6_flock/stage6_9_translating_collective/code/moving_flock.py`,
`MovingFlock.live_edges` (lines 92-101), inherited unmodified by
`MovingFlock611` (Stage 6.11) and used by every `mf.step(...)` call in Stage
6.12/6.12B/6.12C:

```python
def live_edges(self, r, z):
    """Directed live interaction edges (src -> recv): within R AND in the
    receiver's field of view. ORACLE; inference code never calls this."""
    d = self.displacements(r)
    D = np.sqrt((d ** 2).sum(-1))
    near = D <= self.R
    vis = (d * UV4[z][:, None, :]).sum(-1) >= 0.0
    recv, src = np.nonzero(near & vis)
    ...
```

This is the function `compute_G` calls every simulator step to determine
which bird pairs actually exchange influence. It requires BOTH `D <= R`
AND a field-of-view condition: the source must lie in the RECEIVER's
forward half-plane, `(r_src - r_recv) . heading_unit(recv) >= 0` (the
module's own docstring: "the Stage 6.8 FOV rule"). It is also explicitly
DIRECTED (`recv, src` are separate, asymmetric arrays) -- bird A can be a
live source for bird B's update without B being a live source for A's,
depending on which way each is facing.

## Answer to the audit question, stated plainly

**`mech_cumulative_contact_edges` measures (A), NOT (C).** It is undirected,
FOV-free geometric proximity, sharing only the numeric radius `R` with the
simulator's own causal edge relation. The simulator's actual directed
causal-influence relation (`live_edges`) requires distance-within-R **AND**
the receiver's field of view, and is asymmetric. A candidate actuator can
register `mech_cumulative_contact_edges > 0` (geometrically near a target
member at some point in the forcing window) while NEVER being a live,
FOV-visible source of influence to that member if it stays outside the
member's forward half-plane the whole time -- and, symmetrically, it is
possible in principle for geometric proximity to slightly undercount live
influence in edge cases near the FOV boundary, though the dominant direction
of the gap is over-counting (geometric proximity is necessary but not
sufficient for the simulator's own causal edge).

Directionality is not weighted either way in `mech_cumulative_contact_edges`
-- it does not distinguish "actuator is near and facing the target" from
"actuator is near but facing away" from "actuator is near and the target is
facing away from the actuator." All three collapse to the same count.

## What this means for Stage 6.12C's Case-C conclusion

`NEXT_STAGE_DECISION.md` states: "singleton actuator choice has real,
substantial causal consequence... but that consequence is NOT explained by,
predicted by, or well-approximated via direct physical contact between
actuator and target." Given the above, **this claim is accurate only as a
claim about GEOMETRIC proximity, not about the simulator's own directed
causal-influence channel.** The forced-future contact oracle Stage 6.12C
built (`C_forced_actual(j,r) = mech_cumulative_contact_edges`) tested
whether "gets geometrically near the target" identifies high-effect
actuators, and found it does not (contact-oracle mean at or below random,
`ORACLE_DECOMPOSITION.md`). It did NOT test whether "becomes a live,
FOV-gated causal source of influence into the target" identifies high-
effect actuators -- that is a narrower, stricter, and different condition,
never computed by this stage or any prior one for this specific purpose.

**Revised interpretation, superseding the geometric-contact framing where
Stage 6.12C's own prose over-claimed:** Stage 6.12C's data supports
"geometric contact does not explain the headroom." It does NOT support (and
was never positioned by its own code to test) "true directed causal
interaction does not explain the headroom." This distinction matters for
any future work: a directed, FOV-aware "live-influence" oracle -- counting
`live_edges` occurrences where the actuator is `src` and a target member is
`recv`, during the forcing window -- is a straightforward, already-available
(`live_edges` exists, unmodified, in the simulator) next diagnostic that
has NOT yet been tried, and is a strictly more faithful test of "does
becoming a causal influence source on the target explain the effect" than
the geometric proximity metric Stage 6.12C actually used. This document does
not run that diagnostic (out of scope for a bounded, analysis-only
follow-up using only already-computed data) -- it is flagged here as
unfinished business for whoever designs the next experiment
(`INTERIOR_ACTUATION_METHOD_NOTE.md` / `NEXT_EXPERIMENT_DECISION.md`).

## What this document does NOT alter

Nothing in `../ORACLE_DECOMPOSITION.md`, `../NEXT_STAGE_DECISION.md`, or any
other Stage 6.12C document was edited. This is a new, interpretive
correction note only, per the task brief's explicit instruction.
