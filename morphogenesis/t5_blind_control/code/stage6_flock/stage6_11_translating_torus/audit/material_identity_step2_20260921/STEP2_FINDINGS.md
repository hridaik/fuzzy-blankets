# Step 2 findings

## Established

1. **The corrected observation is real and reproduces exactly.** Seed 503,
   t=46→47: v1's displayed interior jumps from a 37-member population to a
   completely disjoint 31-member population (0 overlap), via a cross-branch
   MAP-argmax overtake — the same defect class Step 1 documented for seed
   500 t=20→21, now confirmed bird-ID-exact for the seed the correction
   identified. The incumbent had two legitimate, if diminished, material
   continuations available (18 and 16 members, R_old 0.49/0.43) that were
   not orphaned, merely outcompeted for the argmax by an independent,
   already-existing thread with one undiluted, perfectly-scoring match.
   (`seed_503_t46_t47_forensics.md`)

2. **No explicit target-direction dependence exists in the identity-scoring
   code.** Confirmed by full read of `lineage_611.py`'s branch score and
   softmax (no `target_heading`/`h_star` term). The newly-selected
   population at seed 503 t=47 had a modest pre-existing alignment
   advantage (0.194 vs. 0.135) but the tracker did NOT select the
   best-aligned available candidate (a 0.833-aligned candidate was ignored
   entirely) — ruling out literal target-seeking, while leaving intact the
   general concern that argmax instability can incidentally favor
   already-aligned populations for reasons unrelated to any explicit bias.

3. **A deliberately simple, material-overlap-only tracker
   (`ForwardMaterialTrace611`) was built, calibrated on 12 uncontrolled
   episodes (disjoint from seeds 500–504), and validated against a 7-test
   known-history suite (6/7 pass, 1 disclosed limitation) — all before
   ever being applied to the five historical seeds.**
   (`identity_rule_spec.md`, `identity_validation.md`)

4. **Applied unchanged, the frozen rule produces materially different
   pictures for seeds 501, 502, and 503 than v1's displayed trajectory:**
   - **Seed 500, 504**: perfect agreement with v1 throughout (0/47
     disagreements each) — clean sanity confirmation.
   - **Seed 501**: a transient 4-step v1/trace disagreement (t=32–35,
     matching Step 1's flagged event) that **self-corrects by t=36** —
     the material-continuing target and v1's displayed trajectory converge
     and agree for the rest of the episode, ending at the same turn
     (0.97). **The material-continuing flock in seed 501 does turn.**
   - **Seed 502**: a **permanent** divergence beginning at t=32 (also
     matching Step 1's flagged event) that never recovers. The
     material-continuing target's alignment stays flat-to-declining
     (0.19→0.10) while v1's displayed trajectory (a different, 50-vs-28-
     member-mismatched population by episode end) rises to 0.75. **The
     material-continuing flock in seed 502 does not turn.**
   - **Seed 503**: agreement for the first 12 control steps (t=35–46),
     then a **permanent split** at t=47 (the corrected observation's exact
     transition). The material-continuing branch shows a real but modest
     rise (0.05→0.35); v1's displayed trajectory, tracking the OTHER
     branch of the same split, reaches 0.86. **The dramatic, previously-
     reported seed-503 turn occurs in a population this task's evidence
     identifies as materially distinct from the flock selected and
     actuated at qualification.**

5. **Field-direction, recomputed at the trace's own centroid instead of
   v1's, is NOT robust to that anchor choice for seeds 502 and 503** (large
   gap, stable across a 7-point radius sweep, r∈[1.5,5.0]) — but IS robust
   for seed 501 (anchors agree). This independently corroborates finding 4
   via a completely different computational path (a spatial readout, not a
   membership-set comparison). (`rescoring_reassessment.md`)

6. **`original_material`'s frozen-t0-ID readout is measurably stricter
   than forward material continuity**: seed 501's material-continuing
   target (identity-valid throughout, by this task's own independent
   standard) retains only 20% of its exact t0 cohort by episode end —
   ordinary gradual turnover over ~46 steps, not a discontinuity.

## Provisional

- Whether Step 1's `original_material`/`field_direction` verdicts on the
  COUNTERFACTUAL branches (fresh-CRN re-simulations from each seed's
  trigger state) would show the same split/divergence pattern this task
  found in the ACTUAL recorded trajectories, if those branches were traced
  forward with `ForwardMaterialTrace611` too. Not tested in this pass —
  the two analyses used different trajectories (real vs. counterfactual)
  and are not a strict contradiction, but are not yet reconciled either.
- Whether v2's own centroid (rather than v1's, used here as a proxy) would
  narrow or preserve the field-direction anchor-sensitivity gap found in
  finding 5.
- Whether seed 503's material-continuing branch (0.05→0.35) reflects a
  real, if modest, intervention effect, or unforced fluctuation — this
  task did not run a no-control/matched-random comparator against the
  material-continuing target specifically.

## Contradicted historical interpretations

- **"Seed 503 is the one seed with an unambiguous, all-readout-corroborated
  real turn" (Step 1's `FIVE_SEED_CAUSAL_ADJUDICATION.md`)** is contradicted
  in one specific, narrow sense: the "all-readout-corroborated" claim was
  established on counterfactual branches where v1 and v2 happened to agree
  (because those branches' own re-simulated trajectories did not produce
  the same t=47 split as the real recorded run). Applied to the ACTUAL
  recorded episode, the "same population" assumption underlying that
  corroboration does not hold past t=47 — v1's own displayed pointer and a
  materially-continuous forward trace disagree about which population is
  being described from that point on. This does not mean no real turn
  occurred (finding 4 shows some real rise in SOME population); it means
  the turn's ownership by the originally-qualified flock is not established
  by the real run's own evidence.

- **Step 1's implicit treatment of seed 501/502 as symmetric "withdrawn"
  cases** is refined, not contradicted outright: this task's real-run-only
  evidence distinguishes them sharply. Seed 501's material identity
  survives its zero-overlap event (transient, self-correcting); seed 502's
  does not (permanent). Step 1's withdrawal of BOTH was based on
  counterfactual-branch readouts that did not make this distinction
  (both showed v1-only rises uncorroborated on their respective
  counterfactual branches) — this task's finding is consistent with, and
  adds resolution to, that withdrawal for seed 502, but suggests seed 501
  may deserve separate reconsideration on the real-run evidence
  specifically (see `seed_501_identity.md`'s explicit caveat that this is
  about the real run, not a re-litigation of the counterfactual analysis).

## Still open

- Full v2 per-frame replay of all 5 seeds (would sharpen the
  rescoring-reassessment anchor comparison).
- Applying `ForwardMaterialTrace611` to Step 1's counterfactual branches
  directly (would reconcile the provisional item above).
- A no-control / matched-random comparator run against the
  material-continuing targets specifically (would give intervention-effect
  evidence this task explicitly declined to produce, per its scope freeze).
- Whether the merge-flag rule's known limitation (Test G) matters in
  practice beyond the one observed instance (seed 503, t=43) — only one
  genuine merge-shaped event was found across all 5 seeds, so this has not
  been stress-tested further.
