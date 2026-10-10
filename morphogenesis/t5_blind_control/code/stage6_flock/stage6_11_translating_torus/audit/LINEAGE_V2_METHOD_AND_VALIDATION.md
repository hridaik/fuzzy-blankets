# lineage_v2 — Method and Validation (Stage 6.11B item 1-2)

`lineage_611.LineageTracker611` is unmodified. `lineage_v2_611.LineageTrackerV2`
is a fully independent comparator (`audit/lineage_v2_611.py`); calibration
in `audit/calibrate_lineage_v2_611.py`; synthetic validation in
`audit/test_lineage_v2_611.py`; real-trajectory replay in
`audit/lineage_v2_replay_611.py`.

## 1. What changed, precisely

| | v1 (`LineageTracker611`) | v2 (`LineageTrackerV2`) |
|---|---|---|
| identity unit | branch-history (`hid`); duplicate present-states get separate `hid`s | present member set; identical current states from different histories are summed into ONE entry before normalization |
| genealogy | conflated with identity (a new `hid` per branch) | kept as metadata (`genealogy: [(parent_lid, contributed_prob), ...]`), never a competing hypothesis |
| death | only when *zero* candidates clear the retention gate | every transition splits prior mass into `p_continue`-weighted live share + `(1-p_continue)` reported dead share, for EVERY transition, gate-clearing or not |
| zero-material-overlap continuation | impossible below `R_retain>=0.30` | possible if transport-consistent (see §2) |
| eligibility | `R_retain >= 0.30` only | `R_retain >= 0.10` OR (shape-similar AND displacement-consistent with the lineage's own recent velocity) |
| qualification age | `len(records)`, shared by every hypothesis in a branch tree regardless of which one is currently MAP | per-lineage `dwell`, reset to 1 whenever the REALIZED transition's own `p_continue < 0.5` — i.e. reset on a low-confidence switch even if that candidate ends up the sole survivor |
| "calibrated"? | scores are heuristic weights, never claimed calibrated | `p_continue = sigmoid(a*score+b)`, fit on labelled uncontrolled dev pairs, reliability-checked (§3) — reported as a "calibrated continuation confidence," explicitly NOT a Bayesian posterior |

## 2. The transport-consistency gap this fixes

Both v1 and v2 inherit `identity_69.field`/`estimate_translation`'s `R_F`,
which is a **centroid-relative SHAPE comparison** (both fields are already
re-centred on their own candidate's centroid before comparison) — it says
"does the pattern look similar," not "did this displacement make physical
sense." A first cut of `lineage_v2` that gated zero-overlap candidates on
`R_F` alone let an admittedly-synthetic "unrelated jump" test through: two
same-shaped Gaussian blobs at opposite corners of the box scored `R_F=0.79`
(comfortably above the 0.5 shape floor) purely because they had matching
shape, independent of location. **This is why item 1 asked for
transport-consistency as a DISTINCT quantity from `R_F`**, and the fix
(`d_transport` residual against the lineage's own rolling velocity history,
or — before any velocity history exists — a bound relative to
`geometry_611.local_scale`) is what actually separates "wave-like complete
replacement, consistent with known bulk motion" from "an unrelated spatial
teleport": see `test_complete_replacement_with_continuous_field` (passes:
zero material overlap, displacement consistent with bulk motion, tracked)
vs. `test_unrelated_spatial_jump_does_not_inherit_identity` (zero material
overlap, displacement inconsistent, correctly dies) in
`test_lineage_v2_611.py` — both pass, 10/10 synthetic scenarios pass overall
(translation, gradual recruitment, contraction, complete replacement with
continuous field, unrelated jump, split, merge, temporary missed detection,
unmatched-candidate new birth, duplicate-hypothesis coalescing).

## 3. Calibration and its actual reliability

`p_continue = sigmoid(11.87 * score - 7.55)`, fit on 1,768 "good" (natural
consecutive-step continuations, Jaccard≥0.5) and 1,736 "bad" (candidates
drawn from unrelated episodes/times) pairs from 10 uncontrolled train
episodes. Held-out Brier score **0.0123** — good, but this reflects an
**easy** classification problem by construction (good scores cluster
0.86–0.99, bad scores 0.01–0.47, a clean gap): the reliability curve's
extreme bins are well-populated and well-calibrated (bin 0: predicted 1.3%,
empirical 0.0%, n=479; bin 9: predicted 97.7%, empirical 98.5%, n=528), but
the MIDDLE of the range — exactly where a genuinely ambiguous real
transition like seed 500's t=21 event lands — has only 1–10 held-out points
per bin. **This calibration should be read as "well-behaved at the
extremes, largely untested in the ambiguous middle,"** not as a validated
posterior across its whole range. It is called a "calibrated continuation
confidence" throughout this pass, never a Bayesian posterior.

## 4. Real-trajectory validation: what v2 actually does differently

Replayed on all 5 seeds' recorded `(r,z)` ground truth
(`viz_bundle_611__seed{n}.json`, the same trajectories
`LINEAGE_FORENSICS_6_11.md` used) — v1 driven by the real
`LineageTracker611`, v2 by `LineageTrackerV2`, both fed the identical
candidate list each step.

| seed | v1 qualified at | v2 qualified (this-pass rule) | fraction of steps v1/v2 MAP share ZERO members | final v2 dwell |
|---|---|---|---|---|
| 500 | t=61 | never (within recorded window) | 80.4% | 101 |
| 501 | t=30 | never | 88.2% | 31 |
| 502 | t=30 | never | 19.7% | 27 |
| 503 | t=35 | never | 77.8% | 51 |
| 504 | t=47 | never | 4.3% | 75 |

### 4.1 Seed 500, t=18–24 — what v2 says about the flagship "jump"

|t|v1 MAP size|v1 MAP prob|v2 MAP size|v2 MAP prob|v2 dwell|overlap(v1,v2)|
|---|---|---|---|---|---|---|
|18|43|0.4721|22|0.4906|16|**0**|
|19|40|0.4721|22|0.4955|17|**0**|
|20|38|0.4721|20|0.3963|18|**0**|
|21|17|0.3574|**17**|0.4168|19|**17**|
|22|17|0.3574|17|0.4490|20|17|
|23|17|0.3574|17|0.5062|21|17|
|24|17|0.4028|17|0.5971|22|17|

**v2 was tracking the 17–22-member object continuously (dwell climbing
16→22, no reset) for at least the whole window shown — it did not experience
a jump at t=21.** v1's displayed MAP was a *different* object (size 38–43,
zero member overlap with v2's own answer) for t=18–20, and only coincides
with v2's answer starting at t=21, which is exactly the moment
`LINEAGE_FORENSICS_6_11.md` §1.1 identified as v1's cross-branch overtake.
**Under this evidence, the "jump" is not v2 discovering a new object at
t=21 — it is v1's argmax pointer catching up, three steps late, to an
object v2 had already been stably tracking.** The two trackers disagree
about which physical thing is "the interior" 80% of the time in this
episode, not just at the flagged transition.

### 4.2 v2 never reached qualification in any of the 5 recorded episodes

This is the direct, if uncomfortable, consequence of item 2's fix. Final v2
dwell values (27–101) show the per-lineage duration condition alone is
regularly satisfied — the recorded episodes are long enough for THAT.
Qualification also requires 80% of the last 30 records to hold size fraction
in [0.05, 0.50] AND net displacement ≥ 3R over the same window, evaluated
against the CONTINUOUS v2 lineage rather than the shared tree-wide age; in
this small sample, those conditions were never simultaneously satisfied for
30 consecutive records of one continuously-dwelling v2 lineage, within the
length the original v1-driven episodes happened to run. **This does not
establish v2 would never qualify** — the recorded trajectories stop wherever
v1's own run ended (once v1's control+release phase finished), so there was
no further uncontrolled data to observe whether a v2 lineage would
eventually satisfy all three conditions past that point. Determining that
requires longer uncontrolled runs, out of scope for this pass. **What IS
established: the per-lineage rule is strictly more conservative than the
global-MAP rule on this sample — it never fires early, and in 5/5 cases it
had not fired by the time the original pipeline had already committed to a
control target.** This is the intended fix (item 2), operating as intended,
and it means every one of the five reported trigger states was reached by a
qualification rule the repaired rule disagrees should have fired yet — feeds
directly into `FIVE_SEED_CAUSAL_ADJUDICATION.md`'s "valid lineage?" column.

## 5. What this section does NOT establish

- That v2's calibration generalizes beyond this codebase's own candidate
  detector/regime — it was fit and tested on the same primary regime only.
- That v2 would make different CONTROL decisions than v1 in general — this
  document is about identity/qualification, not actuation; Part 9 branches
  on the ORIGINAL v1 trigger snapshots regardless of what v2 says, because
  adjudicating the ORIGINAL five reported episodes requires starting from
  the states they actually occurred at.
- Full calibration robustness in the ambiguous middle of the score range
  (§3) — flagged as a real limitation, not swept under the rug.
