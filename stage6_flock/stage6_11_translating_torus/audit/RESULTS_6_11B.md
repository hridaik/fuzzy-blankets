# Stage 6.11B — Instrument Repair and Causal Adjudication: Results

Additive to Stages 6–6.11 (all frozen, read-only) and to the prior audit
pass (`audit/METHODS_AUDIT_6_11.md`, `audit/INVARIANCE_AND_TRANSFER_6_11.md`,
`audit/LINEAGE_FORENSICS_6_11.md`, all frozen, read-only). Every number in
this document is either newly computed by a script under `audit/` (named
per section) or copied verbatim from one of those frozen documents with
attribution. No existing Stage 6.11 result, threshold, or number was
changed to produce this document.

**Scope actually delivered in this pass**, against the 15-item brief:
items 1–4 (lineage_v2, thingness gate, blind pool) and item 12 (Bpred
recertification) are complete with full validation. Items 6–11 (authority
repair, set-effect adjudication, five-seed causal adjudication,
controllability) are [PLACEHOLDER — filled once the two background
compute jobs (`branch_adjudication_611.py`, all 5 seeds;
`authority_method_comparison_611.py`) complete]. Items 5 and 13
(architecture clarification, deferred-repairs list) are documentation-only
and complete below. Item 14 (visualization) is [PLACEHOLDER].

---

## Architecture, stated once, precisely (items 5 and 13)

```
                    I_t  (candidate collective, blind or v2)
                     │
        ┌────────────┼────────────────────┐
        ▼            ▼                    ▼
   B_t^pred      B_t^{D,1}            B_t^{C,tau}
 (observational  (task-neutral,       (task-specific,
  screenability;  instantaneous       horizon-tau signed
  predictive_     direct causal       authority; item 6's
  boundary_611)   interface;          repaired A_S(tau,d);
                  probing_611)        control_authority_611
                                       / authority_v2_611)
```

**These three are siblings, not a pipeline.** `B^pred` is never used to
restrict the control pool (item 12) — it screens what is passively
predictable, a different question from what is causally or
control-relevant. `B^{D,1}` does not have to filter `B^{C,tau}` in the
PRIMARY repaired controller: a moving, multi-hop system can have a useful
horizon-`tau` actuator that is not a current one-step direct parent (this
is exactly what `audit/branch_adjudication_611.py`'s
`repaired_blind_authority` branch is — unrestricted by `B^{D,1}`) — and,
symmetrically, `B_causal` does not filter `B_C` in the ORIGINAL Stage 6.11
controller either (confirmed from source in `METHODS_AUDIT_6_11.md`
§Firewall / `LINEAGE_FORENSICS_6_11.md` §7: both were independently computed
from the same privileged pool, with `B_causal` logged but never consumed
downstream). A `B_causal`-restricted comparator (`repaired_direct_causal_restricted`,
branch 7) and an exact-direct-interface comparator (`exact_direct_interface_repaired`,
branch 8) are both run so this pass can measure whether direct-interface
restriction helps, harms, or is neutral — not asserted a priori either way.

## Deferred to a future pass (item 13)

- **Rotation/receiver-frame-equivariant relational features.**
  `INVARIANCE_AND_TRANSFER_6_11.md` established translation/permutation
  invariance is real (to floating-point tolerance) and that no component of
  this stage's inference is rotation-invariant (heading identity is
  absolute in the relational predictor's category index). Repairing that is
  a representational change to `predictive_boundary_611`'s feature
  construction, out of scope here.
- **Speed transfer / online-buffer refit.** Confirmed net-harmful at every
  tested speed including the trained one (`INVARIANCE_AND_TRANSFER_6_11.md`
  §2, Finding 4). This pass freezes the pretrained model (item 12) rather
  than re-opening that question; a real fix (e.g. a properly regularized
  or larger online sample, or abandoning online refit in favour of a purely
  frozen model) is future work.
- **Re-planning cadence for the repaired controller.** Branches 6–9 in
  `branch_adjudication_611.py` select actuators ONCE at the trigger and hold
  for the full 24-step control window (a disclosed compute-budget
  simplification for this pass), rather than re-selecting every 8 steps
  like the original controller. Whether/how often a repaired controller
  should re-plan is Part I's question from the original audit brief and is
  not reopened here.
- **MCTS-based actuator search.** Not implemented, per explicit instruction;
  `AUTHORITY_AND_SET_EFFECT_AUDIT.md` reports whether the simpler comparators
  (top-K, greedy, beam) already show negligible synergy, which is the stated
  condition for not needing it.

---

## 1. Lineage repair (items 1-2) — full detail in `LINEAGE_V2_METHOD_AND_VALIDATION.md`

`lineage_v2_611.LineageTrackerV2` coalesces duplicate present-states before
normalization, carries an explicit death/no-continuation bucket every step,
allows zero-material-overlap continuations when transport-consistent (and
rejects them when not — both proven by synthetic test, 10/10 passing), and
resets qualification dwell on any low-confidence transition. Replayed on
all 5 real seeds: **v1 and v2 disagree about which physical object is "the
interior" on 4–88% of steps depending on seed**, and at seed 500's flagship
t=20→21 event, v2 shows the "jump" is v1's argmax catching up three steps
late to an object v2 had tracked continuously since at least t=18 — not a
discontinuity in the underlying belief state. **Under the repaired
per-lineage qualification rule, none of the 5 seeds' lineages reached
qualification within the recorded episode length** — the original
qualification trigger fired on all 5 episodes before a rule that doesn't
conflate "some branch of this tree persisted" with "this specific present
object has persisted" would have agreed to.

## 2. Thingness gate (item 3) — full detail in `THINGNESS_GATE_AUDIT.md`

Applying the EXISTING, unchanged thingness gate to all 5 online seeds:
**0/5 pass at their qualification moment**, and 0.0–4.3% of all steps pass
across the whole episode. Root cause identified and quantified: the gate's
spatial-integrity check uses `geometry_611.local_scale` (≈0.2–0.3 units) as
its connectivity radius, ~10–17× smaller than the detector's OWN affinity
cutoff (3.3 units) that produced the candidates being graded — at the
gate's radius, even ordinary UNCONTROLLED development candidates pass
`one_dominant_component` only 0.15% of the time (median 13 components), while
the SAME candidates are 100% single-component at the detector's own scale.
This also retracts `LINEAGE_FORENSICS_6_11.md`'s D-based corroboration that
fragmentation was benign — `D`'s near-ubiquitous 1.0 is very likely the
"no periphery found" trivial default at this radius, not a measurement.

## 3. Blind exterior pool (item 4) — full detail in `BLIND_POOL_AUDIT.md`

`nearest_M20` (positions only, never true R/FOV/live-edges) achieves
**100% mean maximum-attainable direct-causal-parent recall**, matching the
privileged oracle `near_exterior`(3R) pool exactly, across 36 dev + online
snapshots. The oracle-radius firewall violation
(`METHODS_AUDIT_6_11.md` §2) does not appear to buy any real recall
advantage. The alternative radius-based blind rule is rejected as primary
because `local_scale` (§2's same root cause) makes it numerically unstable
(median pool size 0→6→60.5→267.5 as its multiplier goes 5→10→20→40).

## 4. Authority repair and set-effect adjudication (items 6-8) — full detail in `AUTHORITY_AND_SET_EFFECT_AUDIT.md`

$$ A_S(\tau,d) = E[H^\star_{t+\tau} \mid S \text{ forced } d \text{ steps}] - E[H^\star_{t+\tau}] $$

proven identical to real held execution by 4/4 unit tests (not merely
described as such). `d\in\{1,2,4,8\}` implemented; `d=\tau=4` primary for
this pass's compute budget. `select_actuators_v2` makes `K\le 8` a ceiling,
never a fill obligation — abstains when no candidate's bootstrap CI clears
positive evidence. Individual/top-K/greedy/beam/synergy comparison at all
5 trigger states: [SUMMARY BELOW, §6].

## 5. Bpred recertification (item 12) — full detail in `BPRED_RECERTIFICATION.md`

Pair/block and regularized cross-fitted multivariate-interaction challengers
added alongside the reproduced single-source certification. At the tested
candidate, all three challenger classes agree the (here, empty) boundary is
already sufficient — no evidence of missed multi-source or interaction
structure. One candidate, not a general claim; `delta` never moved.

## 6. Five-seed causal adjudication (items 9-11) — full detail in `FIVE_SEED_CAUSAL_ADJUDICATION.md`

Branched from each seed's exact recorded pre-control trigger snapshot with
common random numbers into 9 comparators. Headline: **under a stricter
scoring rule that requires a `v1`-only apparent turn to be corroborated by
at least one ID-independent readout, 5 of 5 seeds are "not demonstrated
controllable" by this pass's reference benchmark** — a materially more
cautious result than `RESULTS_6_11.md`'s frozen "3/5 turned," for two
distinct, evidenced reasons, not one:

1. **Two of the three original "successes" (501, 502) do not survive
   ID-independent rescoring.** Their apparent turns exist only in the `v1`
   MAP readout; `v2`, the exact original material, and a position-only
   field-direction measure all show no real change. This is
   `LINEAGE_FORENSICS_6_11.md`'s MAP-instability mechanism, caught directly
   in the act: the identity pointer used to score "did it turn" drifted
   onto a small, coincidentally-aligned fragment.
2. **The one original success that IS real and multiply-corroborated
   (503) is not explained by the mechanism the original method computes.**
   Holding ANY moderate-size exterior set (including a random one) for the
   real 24-step duration reproduces almost the same large, persistent turn
   — the repaired, evidence-gated authority estimator correctly finds no
   reliable short-horizon signal here and abstains, but the system is
   empirically movable anyway. This is a benchmark-adequacy finding, not a
   controllability finding, and `FIVE_SEED_CAUSAL_ADJUDICATION.md` reports
   it as exactly that rather than overstating in either direction.
3. **Seed 504 — the one trigger with real true causal parents (11) and the
   single strongest measured authority anywhere in this study — still
   shows no branch achieving a persistent turn**, including the branch
   using true causal parents directly and the beam-search benchmark. Real,
   statistically genuine short-horizon authority, at K≤8/τ=d=4, was
   demonstrated insufficient here, not merely undetected.

Synergy (item 8) is negative or negligible everywhere measurable —
including at seed 504 — so this is not a search-quality problem either;
simple top-K/greedy already captures what synergy there is to capture.

---

## Closing table

| seed | old apparent turn | valid lineage? | valid thing? | controllable? | old set has real held authority? | random also works? | repaired controller works? | release persists? |
|---|---|---|---|---|---|---|---|---|
| 500 | no | No (v2 never qualified) | No (0% gate pass) | Not demonstrated | No (0 true parents; A=0 exactly) | No | No (all abstained) | n/a (no turn) |
| 501 | **yes** (v1-only) | No (v2 never qualified) | No (0% gate pass) | Not demonstrated | No (A=0, CI [0,0]) | No (0.72 v1-only spike, not corroborated) | No (beam v1-only 0.95, not corroborated) | No (not a real turn) |
| 502 | **yes** (v1-only) | No (v2 never qualified) | No (0% gate pass) | Not demonstrated | No (A=0, CI crosses 0) | No | No (beam v1-only 0.28, not corroborated) | No (not a real turn) |
| 503 | **yes** (real, all readouts agree) | No (v2 never qualified) | No (0% gate pass) | Not demonstrated **by reference benchmark** (but empirically movable — see caveat) | No (old-selected A=−0.006, CI≤0) | **Yes** (matched-random held 24 steps: 0.95 v1, 0.81 material) | No (all repaired/reference branches abstain or find nothing) | **Yes**, for the non-authority-gated branches (old-set-held, matched-random, original-reproduced all persist substantially) |
| 504 | no | No (v2 never qualified) | No (0% gate pass) | Not demonstrated | **Yes** (A=0.048, CI [0.017, 0.082] — the one seed with real authority) | No | No (none persist despite real, true-parent-grounded authority) | n/a (no turn achieved by any controller) |

No existing Stage 6.11 result, threshold, or number was changed to produce
this table. The 40–60-episode confirmatory study this pass was explicitly
scoped to precede is not run here.
