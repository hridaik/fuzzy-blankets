# VALIDATION_RESULTS.md

Results for the protocol frozen in `VALIDATION_PROTOCOL.md`. Numbers below
are read from `phase2_results/*.json`, produced by
`code/run_synthetic_validation.py`, `code/run_real_replay_comparison.py`,
and `code/run_phenomenology.py`. All four runs referenced below have
completed; this document reports what they found, not a pending state.

**Headline, up front, so it cannot be missed by skimming:** the proposed
joint model performs reasonably — a real, measured improvement over the
transparent baseline, replicated on an independent held-out seed set — on
small-scale synthetic scenarios (§1–2), but **fails to establish any
persistent track on the real 400-bird flock at all**, in all 5 tested
real episodes (§3), and produces implausible, highly seed-dependent label
churn on real uncontrolled data (§4). **§6 states the resulting gate
verdict: this does not pass the mandate's final scientific gate yet, and
Phase 4 (control integration) must not begin from this state.**

## 0. Implementation, disclosed scope, and what got fixed along the way

The proposed joint model (`code/joint_tracker.py`) implements
`IDENTITY_MODEL.md`'s §3–§9 at the following disclosed simplifications
relative to the full specification:

- `Sigma_ell` is axis-aligned (`sx, sy`), not a full oriented covariance.
- Phenotype `phi` is approximated by `(pi, Sigma)`, not the full
  `identity_69.field` density map.
- Exact global-hypothesis enumeration is used below
  `EXACT_ENUM_MAX_PAIRS=24` label×candidate pairs (covers every synthetic
  scenario in this battery); a documented greedy approximation with a
  cross-label merger/split pre- and post-check handles the real 400-bird
  replay, where `unaccounted_mass` is honestly reported as `None`
  (not computed exactly) rather than assumed zero.
- Candidate proposals come from two structurally different mechanisms
  (Louvain reuse + an independent density-grid connected-components
  detector), coalesced by Jaccard `>= 0.9` before entering the likelihood.

**Two real implementation bugs were found and fixed during dev-stage smoke
testing, before any held-out or real-replay run** (both disclosed here,
not quietly patched):

1. The synthetic generator originally re-randomized every background
   (unassigned) bird's position and heading completely fresh every frame.
   This produced transient phantom spatial clumps from pure IID noise,
   which the candidate detectors picked up as spurious births, which then
   spuriously "merged" with real labels. Fixed by giving background birds
   persistent random-walk motion (small per-step jitter, occasional
   heading resample) instead — a generator bug, not a tracker bug, but one
   that would have invalidated every synthetic result had it gone
   unnoticed.
2. The joint tracker's birth criterion originally used an absolute
   log-likelihood floor rather than a likelihood-RATIO test against the
   `f_0` uniform-background alternative, and had no track-confirmation
   step. Small background-noise clusters with a by-chance concentrated
   heading (Louvain's own affinity function rewards local heading
   agreement, which noise can exhibit briefly) passed as spurious births.
   Fixed with a likelihood-ratio test (own fit vs. uniform-heading
   background, `BIRTH_LR_FLOOR=16`, roughly `p<0.001` for a 3-df
   comparison) plus a minimum size (`MIN_BIRTH_SIZE=12`) plus a
   2-consecutive-step confirmation buffer before a candidate becomes a
   confirmed label — standard multi-target-tracking track-initiation
   discipline, added because the single-step version still let occasional
   noise through.

**A known, NOT fully resolved residual issue, disclosed rather than
tuned away:** even after both fixes, the simplest possible dev scenario
(`two_clumps` — two permanently separate, non-interacting objects that
should produce exactly 2 births and zero further events) still produces
occasional spurious `merger` events in smoke testing. Diagnosed as likely
related to torus-wraparound proximity between the two objects' paths
combined with the merger pre-check's reachable-radius test, not fully
root-caused given this pass's time budget. **This is reported as a
genuine, currently-unresolved sensitivity of the proposed model's merger
logic, not hidden or tuned away** — per the mandate's explicit instruction
not to make thresholds easier until examples pass. It is exactly the kind
of finding Phase 2 validation exists to surface.

**Seed-count reduction (disclosed compute accommodation, not a rigor
cut):** `VALIDATION_PROTOCOL.md` specifies 20 dev + 20 held-out seeds per
scenario. Timing showed one seed across all 16(+4 out-of-model) scenarios
takes ~3.7 minutes; running the full 20+20 protocol would take roughly 5
hours of wall-clock compute, impractical for this session. **6 dev + 6
held-out seeds per scenario were run instead** — a session-compute
accommodation in the same disclosed-reduction pattern already used
elsewhere in this codebase (e.g. `RESULTS_6_11.md` §7's reduced online-
control budgets), not a change made after seeing results to improve them.

**v2 is not included in the synthetic battery** (only v1, baseline, and
the proposed model are) — v2's calibration lives with the real 5-seed
audit corpus; it IS included in the real-replay comparison below, in its
native context.

## 1. Synthetic validation — dev split

354 records (`phase2_results/dev_results.json`): 16 scenarios × 6 seeds ×
3 trackers (matched mode) + 4 scenarios × 6 seeds × 2 trackers (vicsek
mode). v2 not included here (see §0). Wall time: 1312s.

**A disclosed, important limitation of the v1 comparison, stated before
the numbers below so they are not misread:** v1
(`lineage_611.LineageTracker611`) is instantiated ONE INSTANCE PER TRUE
LABEL, each started directly on its own ground-truth birth members and
fed the same shared candidate list thereafter (§ `run_v1_multi` in
`run_synthetic_validation.py`). This tests v1's per-lineage MATCHING
QUALITY once it is already correctly attached to one object — it CANNOT
reproduce v1's actual, `CLAIMS_LEDGER.md`-documented production failure
mode (global-MAP switching to an entirely independent lineage), because
that requires one shared tracker session juggling multiple concurrently-
discovered lineages against a single argmax read-out, which is not how
`LineageTracker611`'s public API is built to be run standalone. **v1's
strong-looking numbers below should not be read as contradicting
`CLAIMS_LEDGER.md`'s findings** — they measure a different, narrower
question (association quality given a correct start) than the one that
document's real-seed forensics measured (global object selection across
an entire episode).

### Aggregate (matched mode, mean over 16 scenarios × 6 seeds)

| tracker | object-count bias | identity switches | false-track rate | missed-true rate | unresolved frac |
|---|---|---|---|---|---|
| baseline | +24.60 | 16.93 | 0.949 | 0.000 | 0.314 |
| **joint (proposed)** | **+0.81** | 19.80 | 0.435 | 0.103 | 0.156 |
| v1 (see caveat above) | +0.10 | 0.31 | 0.068 | 0.019 | 0.000 |

**Baseline's false-track rate (0.95) and object-count bias (+24.6) are as
expected, not a bug**: it has zero candidate deduplication (confirmed
directly, §5 below) and no birth confidence test at all, so it births a
new track for essentially every transient candidate the detectors ever
propose. This is the honest simple-alternative point of comparison the
protocol calls for — the proposed model's much lower bias (+0.81) and
false-track rate (0.44) are a real, measured improvement over doing
nothing principled about false births, achieved by the likelihood-ratio
birth test and coalescing described in §0.

**The proposed joint model still has a real, substantial false-track rate
(0.44) and a non-trivial miss rate (0.10) in aggregate** — this is not
hidden: roughly 4 in 10 of its reported labels don't correspond to a real
object, and about 1 in 10 real objects go undetected, at the parameter
settings fixed during dev-stage smoke testing (§0). This is reported as
the model's actual current performance, not rounded up.

### Per-scenario findings worth surfacing on their own (not just the aggregate)

- **`symmetric_split` is the joint model's worst scenario by far**: bias
  `-1.09` (UNDER-counting), missed-true rate **0.80** (it fails to find 4
  out of 5 true objects on average), unresolved frac 0.51. Root cause,
  traced directly: **this implementation pass built the "actual split"
  event (§7 row 5) and its post-check, but never implemented dedicated
  code for row 4 ("detector merger") or row 3 ("detector over-
  segmentation")** — `IDENTITY_MODEL.md` specifies both, but only rows
  1/2/5/6/7/8 have working code in `joint_tracker.py`. When a single
  parent label's true split produces two candidates that the exact-
  enumeration assignment (or the merger pre-check) can misroute, there is
  no row-3/4 machinery to catch the resulting mis-segmentation, and the
  split post-check's retention/disjointness thresholds (`retain >= 0.6`,
  pairwise Jaccard `< 0.2`) are stricter than this dev scenario's actual
  post-split geometry in a meaningful fraction of seeds. **This is a real
  implementation gap in this pass, not a specification problem** —
  `IDENTITY_MODEL.md` §7 already specifies rows 3/4 precisely; they were
  simply not built in the code yet. Flagged as the top priority for the
  next implementation pass, not smoothed over here.
- **`superposition_two_distinct`** (the "one detected blob, two still-
  distinct groups" scenario — exactly row 4's target case) also shows a
  real weakness: missed-true rate 0.30, though its false-track rate (0.09)
  is the BEST of any scenario — consistent with the same root cause: with
  no dedicated detector-merger logic, the tracker sometimes only confirms
  one of the two overlapping groups as a label rather than reporting both
  with association uncertainty as §7 row 4 specifies.
- **Vicsek (out-of-model) results show real, expected degradation**:
  joint model's object-count bias worsens from +0.81 (matched) to +3.94
  (vicsek), switches worsen from 19.8 to 33.5, and unresolved frac jumps
  from 0.16 to 0.57 — more than half of reported label-steps are
  unresolved under real, correlated Vicsek dynamics. This is the expected,
  honest signature of the §4 elliptical-mixture likelihood's conditional-
  independence assumption being genuinely violated by correlated
  real-agent dynamics, exactly what the out-of-model test battery exists
  to surface, not a failure of the test.
- **v1 was NOT run on the vicsek sub-mode** in this pass (an omission in
  `run_synthetic_validation.py`'s battery loop, not a deliberate scope
  decision stated in `VALIDATION_PROTOCOL.md` — noted here as a gap for a
  future pass, since it means the vicsek comparison in this document is
  baseline-vs-joint only).
- Scenarios where the joint model performs comparably well across the
  board (bias within ±1.5, false-track rate 0.3–0.6, unresolved <0.15):
  `two_clumps`, `crossing`, `growth`, `contraction`, `density_change`,
  `torus_seam`, `missed_then_continue`, `rapid_motion`, `shape_compact`,
  `shape_disconnected`, `lookalike_death`, `ambiguous_symmetric`,
  `actual_merger`. `actual_merger` in particular (bias +0.25, false-track
  0.27) shows the merger pre-check (§ row 5, implemented) working
  reasonably, in contrast to the un-implemented row-4 detector-merger case
  above — a useful internal contrast confirming the gap is specifically
  the un-built rows, not the merger mechanism in general.

## 2. Synthetic validation — held-out split

354 records (`phase2_results/heldout_results.json`), disjoint seeds
(100–105) from dev (0–5), same 16 scenarios, same trackers, same
parameters — **no threshold was changed between the dev run (§1) and this
run.**

| tracker | object-count bias | identity switches | false-track rate | missed-true rate | unresolved frac |
|---|---|---|---|---|---|
| baseline | +24.40 | 16.68 | 0.948 | 0.000 | 0.312 |
| **joint (proposed)** | **+0.82** | 19.90 | 0.434 | 0.094 | 0.145 |
| v1 (see §1's caveat) | +0.08 | 0.20 | 0.039 | 0.003 | 0.000 |

**These numbers replicate the dev split almost exactly** (joint: bias 0.82
vs. dev's 0.81; false-track 0.434 vs. 0.435; missed 0.094 vs. 0.103;
vicsek bias 4.20 vs. 3.94, vicsek unresolved 0.571 vs. 0.568) — this is a
genuine confirmatory result: the dev-split findings are not small-sample
noise, they generalize to an independent seed set.

**The two scenario-level weaknesses identified in §1 both replicate on
held-out, confirming they are real properties of the current
implementation, not dev-set flukes:**

| scenario | joint bias (dev → heldout) | joint missed-rate (dev → heldout) |
|---|---|---|
| `symmetric_split` | −1.09 → −0.61 | 0.80 → 0.61 |
| `superposition_two_distinct` | −0.46 → −0.14 | 0.30 → 0.27 |

Both scenarios improve somewhat on held-out relative to dev (fewer misses)
but remain the two worst-performing scenarios by a wide margin in both
splits — consistent with the §1 root-cause diagnosis (rows 3/4 of
`IDENTITY_MODEL.md` §7 not yet implemented in `joint_tracker.py`), not
with random scenario-to-scenario variance.

## 3. Real-replay comparison (seeds 500–504)

**Headline finding, stated plainly and without hedging: the proposed
joint tracker never confirms a single label matching the reference
subject, in any of the 5 real seeds, within at least the first 30 steps
of each episode** (`phase2_results/real_replay_results.json`). v1, v2,
and even the deliberately-simple baseline all maintain a continuous,
sensibly-sized track on the SAME reference region of the SAME raw data
over the same steps (member counts fluctuating in a plausible 15–57
range for seed 500, all starting near `ref_size=23`). The joint model's
`joint_n` is 0 at every single step checked. This was checked twice
(§ methodology note below) to rule out a comparison-harness bug before
being reported as a real finding.

**Methodology note (ruling out a harness bug before trusting this
result):** the first version of `run_real_replay_comparison.py` only
checked for a reference-label match once, exactly at `t_start`, which is
guaranteed empty by the joint tracker's own 2-step birth-confirmation
delay — that WAS a harness bug, caught and fixed (retry window extended
to `t_start..t_start+6`). After the fix, the result did not change: not
just at `t=0`, but at every one of the first 30 steps checked directly
for seed 500, `joint_n` stays exactly 0, while `baseline_n` (same harness,
same candidate stream) fluctuates sensibly throughout. This rules out the
specific harness bug found; it does not rule out a different one, but no
further bug was found in the time available for this pass.

**Diagnosis (hypothesis, not fully confirmed):** the real 400-bird flock
routinely presents far more simultaneous candidates than any synthetic
dev/held-out scenario (this codebase's own prior audit,
`METHODS_AUDIT_6_11.md`, documents up to ~13 simultaneous Louvain
candidates at one real snapshot). With even 2–3 live labels, `n_pairs`
(labels × candidates) exceeds `EXACT_ENUM_MAX_PAIRS=24` almost
immediately, forcing the tracker onto the GREEDY assignment path (§0) at
essentially every real step — a path never exercised in the smaller
synthetic scenarios validated in §1–2 (all of which stayed within the
exact-enumeration regime). The merger pre-check (§0) also runs before
the greedy path and was already flagged as a source of spurious churn at
small scale (§0's disclosed residual issue in `two_clumps`); at real
candidate density this appears to prevent the reference region from ever
surviving 2 consecutive confirmation-matching steps, hence zero
confirmed births matching it. **This is a hypothesis pointing at the most
likely mechanism, not a confirmed root cause** — root-causing it further
is the single most important next step, listed first in
`FRESH_CHAT_HANDOFF.md`.

**Cross-tracker agreement (v1/v2/baseline, excluding the joint model
since it has nothing to compare):**

| seed | mean Jaccard(v1, v2) |
|---|---|
| 500 | 0.33 |
| 501 | 0.35 |
| 502 | 0.72 |
| 503 | 0.02 |
| 504 | 0.86 |

Wide variation (0.02 to 0.86) across seeds, consistent with
`CLAIMS_LEDGER.md`'s own finding that v1 and v2 frequently disagree
substantially — this real-replay comparison independently reproduces that
disagreement pattern rather than contradicting it. **Per the mandate's
explicit instruction, neither v1 nor v2 is treated as ground truth here**
— the disagreement is reported as a fact about the two estimators, not
resolved in either direction.

**v1/v2 final-episode outcomes** (whether either tracker's own hypothesis
set survives to the end of the recorded episode): v1's single lineage
dissolved entirely (`v1_n=0` at the final step) in 4 of 5 seeds (500, 501,
503, 504); only seed 502 kept a live v1 hypothesis to the end. v2 kept a
live dominant hypothesis to the end in all 5 seeds. This is consistent
with — not a new contradiction of — `CLAIMS_LEDGER.md`'s own characterization
of v1's fragility and v2's design goal of avoiding forced termination.

**What this section does NOT show:** because the joint tracker never
locks onto anything comparable, this real-replay pass cannot yet answer
which tracker's account of the real flock is more defensible in the
sense `VALIDATION_PROTOCOL.md` §6 intended (showing every disagreement
with raw observations, given all four trackers something to disagree
about). That comparison is blocked on fixing the real-scale confirmation
failure above.

## 4. Fresh uncontrolled-episode phenomenology

Reuses the `uncontrolled`-phase segment already present at the start of
each of the 5 recorded real episodes (physical model untouched, no
actuation, no target heading read) — see `run_phenomenology.py`,
`phase2_results/phenomenology_results.json`.

| seed | uncontrolled frames | total labels seen | alive at end | terminated |
|---|---|---|---|---|
| 500 | 61 | **28** | 28 | 18 |
| 501 | 30 | 0 | 0 | 0 |
| 502 | 30 | 2 | 2 | 0 |
| 503 | 35 | 5 | 5 | 2 |
| 504 | 47 | 12 | 12 | 6 |

**This is a striking, and not encouraging, result, reported plainly rather
than explained away.** Seed 500 alone produces 28 distinct confirmed
labels (18 of which already terminated) over just 61 uncontrolled frames —
roughly one new label every 2 steps — which is not a plausible rate of
genuine spontaneous multi-object emergence at this population size; it is
the same merger/birth churn pattern flagged as a residual, unresolved
sensitivity in §0 and directly confirmed at real scale in §3 below. Seed
501, at the opposite extreme, confirms ZERO labels across its entire
30-frame uncontrolled window — meaning the tracker's birth criteria (§0)
were never cleared even once for that episode, which is also not obviously
correct (RESULTS_6_11.md's own world-selection work established that this
regime produces qualifying mesoscopic domains at 95–100% frequency by a
DIFFERENT, privileged diagnostic). Seeds 502–504 fall in between (2, 5, 12
labels respectively over similar-length windows) with no obvious
population-size or duration explanation for the huge spread.

**Reading, stated plainly:** this phenomenology run does not answer "how
often does a stable, visually recognizable lineage emerge spontaneously" —
it mainly demonstrates that the current joint tracker's real-scale
behavior is too unstable (seed 500) or too conservative (seed 501) across
different episodes to answer that question yet. This is exactly the kind
of finding that should stop a claim of "phenomenology established," not be
smoothed into one — see §6's overall verdict.

## 5. Duplicate-invariance and scale-sensitivity checks

**Duplicate invariance (MATHEMATICAL_CHECKS.md Case 2), executed as code,
not just reasoned about:**

- **Weak version (fresh tracker, single step)**: both trackers reported 0
  labels under both `k=1` and `k=3` duplication because the joint
  tracker's 2-step birth-confirmation buffer (§0) cannot confirm anything
  on a single isolated step — a trivial pass (0==0), not informative,
  caught and corrected in the next check.
- **Meaningful version (established tracks, duplicate only the final
  step's candidates)**: ran the joint tracker identically for 10 steps
  (`two_clumps`, seed 1, 5 labels alive by t=10 — including some of the
  scenario's own residual spurious labels, §0), then compared the t=10
  outcome with that step's candidate list duplicated 1x vs. 3x. **Result:
  identical member-set lists (`True`)** — the coalescing mechanism (§5's
  Jaccard `>=0.9` merge) holds under real duplicate input with live
  tracks in play, not only in the empty-tracker toy case.
- **Baseline, by contrast and by design**: duplicating a 17-candidate list
  3x produced 51 tracks (exactly 3x, `invariant=False`) — baseline has NO
  candidate deduplication of any kind (its own docstring, corrected during
  this validation pass, now states this plainly rather than the earlier,
  inaccurate claim of "exact-set dedup"). This is the intended, disclosed
  contrast: the proposed model's §5/§9(5) coalescing step is a real,
  verified improvement over the simple baseline's total absence of one.

**Scale-sensitivity (±20% on the reachable-radius / birth-size
constants):** **not run in this pass** — flagged as an explicit gap
against `MEASUREMENT_CONTRACT.md` §1's stability-check requirement, not
performed here due to session time constraints. The constants currently
in force (`PROCESS_NOISE_STD`, `K_SIGMA_REACHABLE`, `BIRTH_LR_FLOOR`,
`MIN_BIRTH_SIZE`) were fixed once during dev-stage smoke testing (§0) and
never varied afterward, but their SENSITIVITY to reasonable perturbation
— required before they could be treated as calibrated rather than merely
"a value that happened to run" — remains unverified. Listed explicitly in
`FRESH_CHAT_HANDOFF.md` as the next concrete step.

## 6. Overall verdict against the mandate's final scientific gate

The mandate's own final gate: *"Can an independent reader identify which
physical organization a track refers to, understand its uncertainty and
event history, and reproduce why it was called the same object? ... If
that gate fails, do not run control and do not call the phase complete."*

**This gate does not pass, for the proposed joint model, on real data,
in this pass.** An independent reader cannot currently be shown why any
specific real-flock track is "the same object" over time, because in
every one of the 5 tested real episodes the tracker never confirms a
track corresponding to the flock's actual coherent structure in the first
place (§3). It CAN answer that question on the synthetic scenarios (§1–2),
where ground truth exists and the tracker's confirmed labels can be
traced directly to specific, inspectable events (births, mergers, the one
implemented split path) — but the real data is the data this whole
research program is ultimately about, and the gate is stated in terms of
a real track, not a synthetic one.

**What DID validate successfully, stated so the genuine progress is not
lost in the headline failure:**

- The theoretical model (`IDENTITY_MODEL.md`, `MATHEMATICAL_CHECKS.md`)
  survived an adversarial review with real, fixed defects (`THEORY_REVIEW.md`)
  and is internally consistent.
- The implementation's core mechanisms — duplicate/near-duplicate
  coalescing (§5), the corrected decision threshold, the merger/split
  event logic, the likelihood-ratio birth test — all work AS DESIGNED at
  the scale they were built and tested at (small synthetic scenes,
  confirmed exactly via `MATHEMATICAL_CHECKS.md`-style checks executed as
  code, not just reasoned about on paper).
- On that scale, the proposed model is a measured, held-out-confirmed
  improvement over both the naive baseline (far fewer false tracks) and
  over what an unconstrained tracker would do with duplicate candidates
  (§5's invariance check).
- Two real implementation bugs (generator background-noise re-
  randomization; birth criterion using an absolute floor instead of a
  likelihood ratio) were found and fixed BEFORE they could invalidate the
  synthetic results — itself a legitimate output of this validation pass,
  not a footnote.

**What did NOT validate, stated with equal weight:**

- The tracker does not scale to the real flock's candidate density/count
  in its current form (§3, diagnosed but not fixed).
- Two specific event rows (§7 rows 3–4, detector over-segmentation and
  detector merger) were specified in `IDENTITY_MODEL.md` but never
  implemented in `joint_tracker.py`, and this measurably hurts two
  scenarios in both dev and held-out splits (§1–2).
- A residual, unresolved spurious-merger sensitivity exists even at small
  synthetic scale (§0), not fully root-caused.
- Scale-sensitivity checks (§5) were not run.
- Real-scale phenomenology (§4) is currently uninterpretable given the
  tracking failure it sits on top of.

**Consequence for Phase 4 (control integration), stated per the
mandate's own rule:** Phase 4 must NOT begin from this state. Attaching a
control task to a label this tracker cannot yet reliably produce on real
data would not be a meaningful test of the identity-to-control contract
`IDENTITY_MODEL.md` describes — it would be testing a contract layered on
top of an instrument known, by this pass's own validation, not to work
yet at the scale that matters. The next concrete engineering step (fixing
the real-scale confirmation failure) is listed first in
`FRESH_CHAT_HANDOFF.md`, ahead of any control-layer work.
