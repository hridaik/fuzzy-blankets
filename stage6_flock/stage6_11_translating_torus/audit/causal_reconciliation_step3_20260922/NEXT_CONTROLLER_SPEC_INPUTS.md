# Inputs for the next controller design task

This is NOT a controller design. It collects what this pass (and its
predecessors) established that the next design task should be able to
assume, and what it should NOT assume, per spec §16's explicit list.

## What the next task MAY assume

1. **A frozen, simple material-association layer is available and
   reasonably reliable**: `ForwardMaterialTrace611` at Jaccard≥0.30.
   Zero erroneous transfers to unrelated populations were observed across
   72 full-episode sequential traces on independent natural data
   (`IDENTITY_EPISODE_VALIDATION.md`). A small (~0.03–0.04%) non-subset
   same-frame false-accept risk exists and is disclosed
   (`identity_causal_reconciliation_20260921/IDENTITY_VALIDATION_HARDENING.md`)
   but did not manifest in any of the 72 sequential traces checked.
   **This is a material ASSOCIATION layer, not the complete strict-identity
   decision** — split/merge/genealogy semantics sit above it
   (`SPLIT_MERGE_SEMANTICS.md`).
2. **The known merge-dilution blind spot fails safe.** A target fully
   retained inside a much larger candidate is NOT auto-flagged as a merge
   under the frozen rule (goes `unresolved` instead) — confirmed stable
   across two different size ratios (tests G, K). The next design may rely
   on this failing toward under-claiming continuity, never over-claiming
   it.
3. **A validated, reusable audit-only CRN methodology exists**
   (`RNG_AND_CRN_AUDIT.md`): route physics through a DEDICATED rng stream
   never touched by decision-making code, for any future paired-branch
   comparison the next design task wants to run during development
   (e.g. comparing candidate controller variants). Do NOT assume
   same-top-level-seed alone gives valid CRN if the new controller's own
   decision logic shares an rng object with physics — verify per-variant,
   the way this pass did, rather than assume.
4. **Trigger-state reproduction from a raw episode seed is exact and
   cheap** (`RNG_AND_CRN_AUDIT.md` §4) — useful for any future paired
   counterfactual evaluation harness.
5. **Sustained forcing has a real, demonstrated effect on material-target
   alignment** in the tested seeds (501, 503; §F1/F2), relative to no
   forcing, under repeated stochastic replicates with proper CRN pairing.
   This supports pursuing intervention as a viable mechanism in the next
   design.
6. **No evidence that the SPECIFIC historical top-K-by-authority actuator
   selection outperforms duration/cardinality/cadence/pool-matched random
   selection**, in any tested seed. The next design should not assume the
   old selection method's specificity is worth preserving; a
   redesigned selection mechanism should be evaluated against a
   matched-random baseline as a matter of course, not treated as
   obviously superior by construction.
7. **No evidence that intervention increases organizational disruption**
   (split rate) beyond the flock's own baseline unforced fragmentation
   rate, in the one seed tested for this specifically (503) — though that
   baseline rate is itself substantial (>50% of replicates show a split
   event regardless of condition). The next design should expect
   fragmentation to be a common outcome in this regime generally, not
   specifically caused by control.

## What the next task must NOT assume

1. **Do not assume v1's displayed population is the control subject.**
   Confirmed, repeatedly, across seeds 500–504: v1 can and does jump to
   unrelated, zero-material-overlap populations (global-MAP-over-branching
   defect), and at least one historically-reported "success" (seed 503)
   is now established to be a report about a population disjoint from the
   flock actually selected and actuated.
2. **Do not assume "3/5 successful blind adaptive controls."** WITHDRAWN
   (Step 1, reaffirmed here). Seed-level outcomes require separating
   physical turn, identity continuity, intervention effect, and actuator
   selectivity — collapsing them into one "success" label is exactly what
   produced the withdrawn claim.
3. **Do not assume the candidate/actuator pool problem is fixed.** The
   true-interaction-radius firewall violation in `near_exterior`
   (`intervention_api_611.py`) is unchanged and was REUSED as-is by this
   pass's matched-random comparator (to keep the comparison apples-to-
   apples with the historical method, not because it is defensible for a
   production controller). The next design task inherits this as an open
   defect, not a closed one.
4. **Do not assume policy effect and schedule effect are the same
   question.** This pass only closed the schedule-effect estimand for
   500-504. Whether the ONLINE CONTROLLER's own re-inference (predictive
   boundary construction, causal probing, authority re-estimation) adds
   anything beyond a fixed schedule replay is UNRESOLVED — closing it
   requires the larger CRN-decoupling engineering effort described in
   `RNG_AND_CRN_AUDIT.md` §5, not yet done.
5. **Do not assume a validated physical-split/merge threshold exists.**
   `SPLIT_MERGE_SEMANTICS.md` explicitly declined to freeze one. If the
   next controller needs a binary split/merge decision (e.g. to decide
   whether to keep or abandon a target), that threshold must be
   independently calibrated first, the same way the primary Jaccard
   threshold was — not invented during controller design.
6. **Do not assume abstention-free top-K actuator selection is adequate.**
   Already a known, disclosed defect (Step 1); this pass adds that even
   where actuators WERE selected and held (not abstained), their
   specificity over random selection is not demonstrated — reinforcing,
   not just repeating, the case for an abstention-aware redesign.
7. **Do not assume `thingness_611.py`'s spatial-integrity gate is
   validated for production use.** Still never wired into qualification
   or identity in any pass to date (Step 1's finding, unchanged).

## Concrete recommendations for the next design task's evaluation protocol

- Score every candidate controller variant against the material-
  association + strict-identity layer established here, not v1/v2 raw
  output.
- Always include a duration/cardinality/cadence/pool-matched random
  comparator (not a single anecdotal draw — this pass used 20-25
  replicates; recommend similar or greater for any production evaluation).
- Report distributions (mean, median, std, percentiles, fraction
  favorable), not single-trajectory anecdotes, for any causal claim.
- Verify CRN validity explicitly for any new paired-branch comparison
  the next design introduces — do not assume it from a shared seed.
- Track physical-split/merge events as a first-class outcome alongside
  heading alignment, not as an afterthought only investigated when a
  result looks suspicious.
