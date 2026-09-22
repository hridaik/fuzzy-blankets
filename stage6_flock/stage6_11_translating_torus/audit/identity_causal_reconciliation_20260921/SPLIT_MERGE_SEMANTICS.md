# Split/merge semantics (Task B)

## Policy (spec §4.3, §4.4, §6)

Four-way classification for any split-like event:
1. **detector/candidate split only** — a transient fragmentation that
   re-fuses within a few steps, or whose daughters never separate by more
   than the population's own local density scale. Does not, by itself,
   terminate `strict_identity_valid` for the parent.
2. **likely physical split** — daughters diverge in position and/or
   material composition, persist as separate (or one dies while the other
   persists) trajectories, and do not re-fuse, but no independently
   validated numeric threshold exists in this repository to elevate the
   call to "confirmed."
3. **confirmed physical split** — would require an explicitly stated,
   independently validated criterion (e.g. a distance/duration threshold
   calibrated the same rigorous way the primary Jaccard threshold was).
   **No such criterion exists yet in this codebase**, and this pass does
   not invent one to force a classification, per spec §6's explicit
   instruction.
4. **unresolved** — evidence insufficient either way.

**Strict-identity consequence**: a confirmed physical split terminates
`strict_identity_valid` for the parent control target going forward,
genealogy/descendant tracking may continue for descriptive analysis, and a
CANDIDATE split alone does not automatically terminate identity. An
UNRESOLVED split status makes downstream strict-outcome scoring
unresolved, not success and not failure.

## Applying the policy to seed 503, t=46→47

Evidence (full detail: `seed_503_split_forensics.md`):
- Two material daughters at the split (18 and 16 members, both clearing
  the split-substantiality floor).
- Daughters remain 3.1–4.4 spatial units apart (6.6–9.3× local density
  scale) throughout the window both are tracked — **not** adjacent
  sub-clusters of one coherent group.
- No re-fusion: at most 1-member incidental overlap (Jaccard ≤0.03)
  between the daughters after the split — far below anything that would
  suggest they are still one physically integrated flock.
- One daughter (B, unfollowed) loses detectable coherence within 3 steps
  and is never re-acquired; the other (A, followed) persists to episode
  end with ordinary gradual turnover.
- Both daughters' heading-alignment stays well below v1's reported 0.86,
  which belongs to a *third*, wholly unrelated, zero-overlap population
  v1's own argmax jumped to at the same step — not a daughter of this
  split at all.

**Classification: likely physical split.** This is not classified as mere
"detector/candidate split only" — that category (exemplified by this
pass's synthetic test N, spec §5.4) is characterized by fragments that
re-fuse within a few steps and stay spatially close throughout; seed 503's
t=47 fragments do neither. It is also not classified as "confirmed" —
this pass located no independently validated distance/duration threshold
in the repository to elevate "persistent, non-re-fusing, spatially
separated daughters, one of which loses coherence" to a formally confirmed
physical event, and inventing one now, after seeing this specific seed's
numbers, would be exactly the outcome-directed threshold engineering the
task brief prohibits (spec §14). A rigorously calibrated physical-split
criterion (analogous to how the primary Jaccard threshold was calibrated
on independent, uncontrolled data before ever being applied to a control
seed) is listed in `NEXT_STEP_RECOMMENDATIONS.md`.

**Strict-identity consequence for seed 503**: because this is classified
as *likely* rather than confirmed, downstream strict-outcome scoring for
seed 503's control-target continuity from t=47 onward is **unresolved**,
not automatically terminated and not automatically preserved. What IS
established without needing the split classification resolved further:
the population that reaches v1's reported 0.86 alignment is demonstrably
**not** descended from either split daughter — it is a separate,
pre-existing, zero-overlap population (Step 2's finding, reconfirmed
here). That fact does not depend on whether t=47 is called "likely" or
"confirmed" — under either label, the large reported turn does not belong
to the flock selected and actuated at qualification.

## The one genuine merge event found (seed 503, t=43)

Reported in `material_identity_step2_20260921/seed_503_identity.md`: the
previous target is 100% retained inside a larger (~42-member) candidate.
This is a genuine size-dilution event of the same shape as synthetic tests
G and K (§5.4 of `IDENTITY_VALIDATION_HARDENING.md`) — the frozen rule's
disclosed limitation means this event was NOT flagged with
`merge_flag=True` and instead went `unresolved` at that step (safer
failure direction, per identity_rule_spec.md's own discussion). This is
"ordinary turnover" in the sense that the previous material fully
persists; it is reported here for completeness, not re-litigated, since
Step 2 already found only 1 such event across all 5 seeds' full episodes.
