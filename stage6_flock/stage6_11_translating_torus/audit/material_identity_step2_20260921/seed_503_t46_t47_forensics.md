# Seed 503, t=46→47 — dedicated forensic panel

Corrected observation (task §0): "seed 503 around t=46→47 appears visually
to jump to a substantially different flock, possibly one already heading
in or near the requested target direction." Investigated here at full
bird-ID resolution via `code/seed503_t46_t47_forensics.py`, a read-only
replay of the real, unmodified `lineage_611.LineageTracker611` +
`detect_69.propose` against the recorded ground-truth trajectory. Raw
output: `seed_traces/seed503_t46_t47_forensics.json`.

Control window for seed 503: t=35–57 (qualified at t=35, `target_heading=2`).
t=46→47 is squarely mid-control, 11–12 steps after qualification.

## Frame immediately before (t=46)

**Incumbent (displayed MAP, hid=11)**: 37 members, prob=0.262 (highest of 6
live hypotheses this step — this WAS the displayed interior). Heading
fraction at target: **0.135** (below the 0.25 uniform-random baseline for
4 discrete headings).

Full member list: `seed_traces/seed503_t46_t47_forensics.json`,
`incumbent_members_46` (37 bird IDs).

## Frame immediately after (t=47)

**New MAP (hid=29)**: 31 members, prob=0.241 (won the argmax; the
incumbent's own best child scored lower after branching-dilution — see
below). Heading fraction at target: **0.258**.

Full member list: `new_map_members_47` (31 bird IDs).

## All 14 detector candidates at t=47 (vs. the t=46 incumbent's 37 members)

| cand_idx | size | retained | R_old | R_new | jaccard | dice | centroid displacement | frac at target after |
|---|---|---|---|---|---|---|---|---|
| 11 | 18 | 18 | 0.486 | 1.000 | 0.486 | 0.655 | 1.66 | 0.111 |
| 12 | 16 | 16 | 0.432 | 1.000 | 0.432 | 0.604 | 1.56 | 0.125 |
| 2 | 39 | 3 | 0.081 | 0.077 | 0.041 | 0.079 | 2.96 | 0.333 |
| 0 | 45 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 9.89 | 0.067 |
| 1 | 41 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 11.46 | 0.390 |
| 3 | 36 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.53 | 0.083 |
| 4 | 32 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 11.60 | 0.281 |
| **5** | **31** | **0** | **0.0** | **0.0** | **0.0** | **0.0** | **8.79** | **0.258 (SELECTED as new MAP)** |
| 6 | 28 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 6.97 | 0.214 |
| 7 | 28 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 14.86 | 0.071 |
| 8 | 25 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.09 | 0.600 |
| 9 | 24 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 12.95 | **0.833** |
| 10 | 24 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.17 | 0.125 |
| 13 | 12 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 8.46 | 0.0 |

**Only two candidates (11, 12) share ANY material with the incumbent —
both are fragments (18 and 16 members) of the original 37.** Every other
candidate, including the one selected as the new MAP (candidate 5), shares
**zero** members with the incumbent.

## v1-selected candidate vs. v2-selected candidate

v1 selected candidate 5 (hid=29, prob=0.241, argmax). This audit did not
separately re-run v2 (`LineageTrackerV2`) at this exact transition (v2's
per-frame trajectory was not replayed in this pass — see
`identity_validation.md`'s disclosed gaps); Step 1's `branch_adjudication
_611__seed503.json` (a different, later time point — t0=35, the trigger,
not t=47) shows v1 and v2 in full agreement at that snapshot, but that
does not establish agreement at t=47 specifically, and this is flagged as
open rather than assumed.

## Forward-material-trace's choice

`ForwardMaterialTrace611` (frozen rule, Jaccard≥0.30) accepts **candidate
11** (18 members, jaccard=0.486) — the single best-overlapping fragment of
the incumbent — and **flags a SPLIT** (both candidate 11 and candidate 12
clear the 30%-of-37≈11-member split-share floor). It does **not** accept
candidate 5 (jaccard=0.0, far below threshold).

## Answering the five specific questions (task §3)

**1. Did the post-transition v1 target (candidate 5 / hid=29) exist as a
distinct candidate before the switch?** **Yes.** It was already a live,
independently-tracked hypothesis at t=46 (hid=29, prob=0.213, the
SECOND-highest of the 6 live hypotheses going into t=47, tracking a
31-member population that has evidently existed and been tracked in
parallel for some time before this step).

**2. How much material does it share with the incumbent?** **Zero.** 0 of
31 members overlap with the incumbent's 37 (`R_old=R_new=jaccard=dice=0.0`).

**3. Does the incumbent have another candidate continuation with materially
greater overlap?** **Yes — candidates 11 (R_old=0.486) and 12 (R_old=0.432),
both far above zero, exist and are the material-continuing options a
forward trace correctly picks up.** The incumbent was not orphaned; it had
two legitimate, if diminished, fragmentary continuations.

**4. Was the newly selected candidate already aligned more closely with
the eventual target direction?** **Modestly, yes.** hid=29's population was
at 0.194 target-heading fraction at t=46 (before selection) vs. the
incumbent's 0.135 — both below the 0.25 uniform baseline, but the newcomer
was already somewhat closer. After selection, it rises further to 0.258 at
t=47 alone. This is a real, if modest (0.06), pre-existing alignment
advantage — not dramatic, but directionally consistent with the task's
corrected observation. (For contrast: candidate 9, NOT selected, had an
even higher post-hoc heading fraction of 0.833 at t=47 — the tracker's
choice was not "pick whichever candidate faces the target most," since a
much-better-aligned option existed and was not chosen; this rules out a
literal "maximize target alignment" selection mechanism, consistent with
§5 below.)

**5. Exactly why did v1's global MAP select the branch it did?**
Reconstructed from the live hypothesis-probability arithmetic (six live
hypotheses at t=46, each independently branching against t=47's
candidates — full detail in
`../evidence_recovery_20260921/audit/LINEAGE_FORENSICS_6_11.md` §1.1's
general mechanism, confirmed here at the bird-ID level for THIS specific
transition): the incumbent (hid=11, prior mass 0.262) had **two** viable
continuations this step (candidates 11 and 12, scores 0.590 and 0.562 by
`lineage_611`'s own `0.6·dice+0.4·R_F` formula) — its prior mass was
**diluted by branching** across both. hid=29 (prior mass 0.213, lower than
the incumbent's) had **one** viable continuation (candidate 5, score
0.935 — the single highest-scoring match of ANY candidate this step,
`R_F=0.837`, essentially a perfect, undiluted match to its own prior
trajectory) and so kept its **full, undiluted** prior mass. Undiluted 0.213
exceeded the incumbent's diluted best child (≈0.14 of 0.262, after the
branching softmax split), so hid=29 won the argmax. **This is precisely
the cross-branch MAP-argmax-overtake mechanism already documented for seed
500 t=20→21 in Step 1** (`LINEAGE_FORENSICS_6_11.md` §1.1) — the same
defect class, now confirmed at bird-ID resolution for the seed the task
actually meant to flag.

## Distinguishing explicit target-dependence from incidental alignment (task's explicit instruction)

**No explicit target-direction dependence was found in the selection
arithmetic.** `lineage_611.py`'s branch score (`0.6·dice + 0.4·R_F`) and
the softmax that turns scores into branch probabilities contain no
`target_heading` or `h_star` term — confirmed by reading the module in
full (same conclusion Step 1 reached for `lineage_v2_611.py`, now
independently reconfirmed here for `lineage_611.py`, the actual production
tracker). The modest pre-existing alignment advantage (0.194 vs. 0.135,
question 4) is **incidental**, not selected-for: hid=29 won because its
own trajectory happened to produce one clean, undiluted match this step,
for reasons unrelated to target heading — and the tracker demonstrably did
NOT pick the best-aligned candidate available (candidate 9, 0.833, was
ignored entirely, never even live as a competing hypothesis). The honest
characterization is: **the tracker jumped to an unrelated, independently-
pre-existing, coincidentally-slightly-better-aligned population, via the
same argmax-dilution mechanism already known from seed 500 — not via any
target-seeking mechanism in the code.**

## Was v1's post-jump readout, at least, real material progress?

No — from t=47 onward, `ForwardMaterialTrace611` (staying on the
incumbent's actual material descendant, a shrinking fragment) shows a
**much lower and more slowly-rising** target-heading fraction than v1's
newly-adopted, materially-unrelated population — see
`plots/seed503_v1_vs_forward_trace.png` and `seed_503_identity.md` for the
full-episode comparison. The gap persists (v1 ≈0.85 vs. trace ≈0.1–0.4) all
the way to release, not just at this one transition.

## Interactive replay

`interactive_demo/v2` tab 6 (world + co-moving panes, seed 503, scrub to
t=46/47) now shows both the v1 interior and the `ForwardMaterialTrace611`
panel side by side, including the "WHY THIS CANDIDATE WAS CHOSEN" text and
the disagreement marker, for exactly this transition and every other frame
of every seed — see §9 of `STEP2_FINDINGS.md` for what is and is not
implemented in this pass's visualization.
