# INTEGRITY_DEFINITION.md — what should "functional integrity" mean here?

Written before any numeric threshold in `PROTOCOL_V3.md` is chosen, and
before this session has looked at the Part 1B coherence-trajectory data in
aggregate (individual `coh_traj` values already exist in the frozen V2 JSON
and mechanism-audit data, but no new statistic has been computed over them
for the purpose of picking a V3 threshold). This is a conceptual document,
not a data-fitting exercise.

## Why the old criterion needs revisiting, not discarding

The frozen V1/V2 criterion is

    C_{I0}(t) >= 0.8 for all t in [t0, t0+T_u]

i.e. the core's plurality-heading fraction must never dip below 0.8 at any
single timestep of the control window. `STAGE6_SYNTHESIS.md` and
`RESULTS_V2.md` already established, by direct replication across 11 flocks
and every propagation-based control arm tested, that this criterion is
**structurally incompatible with propagation-based steering**: forcing an
exterior shell toward a new heading necessarily produces a transient window
where part of the core has already turned and part has not, so the
plurality fraction dips, even when the *final* state is exactly the desired
one. The criterion was designed for (and is trivially satisfied by) direct
full-core override, which sets every core bird's heading by fiat and so
never has a disagreement window at all.

This is not a reason to lower 0.8 to some smaller number and call it done.
A discrete heading transition is, definitionally, a period where the group's
opinion changes — some birds update before others as influence propagates
across the interface. Treating that transition itself as an integrity
*violation* conflates two different things:

- **changing state**: a group updating its consensus opinion in response to
  new information at its boundary — this is exactly what a functioning
  collective, given new input, is supposed to be able to do; a group that
  could not do this would not be "integrated," it would be inert.
- **losing identity**: the *same* group ceasing to exist as a coordinated
  unit — dissolving into subgroups too small or too weakly coupled to be
  called one macro-agent, wandering to an incoherent state and never
  reconverging, or continuing to look coherent only because the individual
  identities that make it up have silently been replaced by different birds.

A useful integrity criterion needs to tell these apart. The old criterion
cannot, by construction, because it is blind to *when* in the window the
dip occurs and to whether the group ever comes back together.

## What is fixed, and what is allowed to vary, in this model

The persistent identity anchor for this whole experiment is `I0` — the
frozen set of interior bird identities identified at `t0`. Nothing below
proposes changing that anchor. Given `I0` fixed by definition:

- **Allowed to vary, without penalty**: each individual `I0` bird's
  instantaneous heading. A bird changing its vote during a transition is
  not evidence of anything wrong.
- **Should remain true, for the group to still count as "the same
  functional collective"**:
  1. The group remains **dynamically coupled as a unit** — it continues to
     evolve as a single population responding to shared local coupling, not
     as birds acting independently by coincidence.
  2. It does **not disperse into unrelated persistent subgroups** — i.e. it
     should not end the episode split into two or more stable factions that
     never re-merge.
  3. It **reconverges to a coherent macrostate** — after the initial
     disagreement, plurality agreement should recover, not stay
     permanently fragmented.
  4. It **remains supported by an appropriate interface** — the shell
     relationship (`B^D`) that made this a controllable, well-defined
     interior in the first place should not have silently broken down
     (e.g., via some pathological config where the "interior" is no longer
     densely mutually coupled).
  5. It reaches a **self-maintaining post-release state** — once forcing
     stops, the new consensus should be held up by the group's own ordinary
     dynamics, not require indefinite continued external support.

One thing this model genuinely cannot speak to: **spatial cohesion**.
Birds occupy fixed lattice positions in this port (see
`STAGE6_SYNTHESIS.md`'s "Static-lattice scope" limitation) — only heading
evolves. A criterion that talked about the flock "staying together in
space" would be assessing a property this model does not have. Every
candidate component below is therefore defined purely over heading state
and the (fixed) interaction graph, never over position.

## Candidate components (measured separately, not prematurely collapsed)

These are the measurements Part 2B of the task brief calls for; all can be
computed from data already produced by `evaluate_arm`'s per-replicate
`coh_traj` (or a light extension of it) without any new simulation:

1. **Temporary coherence loss** `C_min = min_{t in [t0, t0+T_u]} C_{I0}(t)` —
   how far the group's internal agreement drops during the transition. This
   is expected to legitimately dip below 0.8 for a real, non-trivial
   heading change; the question is *how far* and *for how long*, not
   *whether*.
2. **Time below threshold** `T_low = sum_t 1[C_{I0}(t) < c_ref]` — duration
   of disagreement, for some reference level `c_ref` (chosen in
   `PROTOCOL_V3.md` after inspecting the empirical distribution of dip
   depths and durations across dev flocks — not before).
3. **Recovery time** — steps from when forcing begins until `C_{I0}(t)`
   first reaches some `c_recover` and *stays* at or above it for a short
   dwell period (a single instantaneous crossing should not count; a group
   that recovers and immediately re-fragments has not really recovered).
4. **Final coherence** `C_{I0}(T_u)` — agreement at the moment control ends.
5. **Post-release coherence** — agreement measured after forcing stops
   (already available as `mean_lineage_end`/coherence-at-`T_u+T_r` in the
   existing harness); this is where "self-maintaining" (component 5 above)
   is actually tested, since nothing is propping the answer up anymore.
6. **Target persistence** `H*` after release (already measured in V2 as
   `Hstar_release`/the `persistence_threshold_Hstar=0.5` criterion) — a
   *different* axis from coherence: persistence asks whether the group
   still holds the *new target heading*, coherence asks whether it still
   agrees with *itself*, whatever heading that is. Both matter; they are
   not substitutes for each other, and a good final criterion should not
   quietly conflate them.
7. **Predictive/interface integrity** — from Part 3's predictive-screening
   quantities: whether `B^D` continues to statistically screen the core's
   near-future state the way it did before the intervention (i.e., the
   *interface relationship*, not just the interior's opinion, has not
   broken down). This is the one component that is explicitly deferred
   until Part 3's machinery exists; it is listed here for completeness, not
   computed in this document.

## Shape of the eventual criterion (thresholds deferred to PROTOCOL_V3.md)

The criterion this points toward has the shape:

> Temporary disagreement is allowed, but the same frozen core `I0` must
> reconverge to a stable, coherent macrostate within a bounded recovery
> time, while remaining supported by an appropriate interaction interface —
> and that reconvergence must hold up on its own after control is released.

Concretely, a transition-aware success will be defined (with numbers filled
in only after examining dev-flock baseline statistics, in `PROTOCOL_V3.md`)
as the conjunction of: `I0` identity unchanged (true by definition), final
target attained (`H*(T_u) >= 0.8`, unchanged from V1/V2), coherence recovers
to `>= c_recover` and dwells there through a short window within `T_rec`
steps of control start, the post-release state persists (`H*` after release
`>= 0.5`, unchanged from V1/V2), and no catastrophic breakdown of the
predictive interface (Part 3, qualitative check, not a hard numeric gate at
this stage).

The **original frozen criterion is not being replaced quietly**. It remains
reported, unchanged, in every V3 results table, exactly as `C_{I0}(t)>=0.8
for all t`, labeled as the V1/V2 criterion. The transition-aware criterion
above is reported *alongside* it as a distinct, separately-justified
quantity — a reader should always be able to see both numbers and judge for
themselves which one they find more meaningful for this class of control
problem.
