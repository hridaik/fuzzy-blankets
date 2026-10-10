# Identity rule specification

## Tracker

`code/forward_material_trace_611.py`, class `ForwardMaterialTrace611`.
Deliberately simpler than v2: no probability mass, no branch tree, no
coalescing. At each step: gate every raw detector candidate against the
immediately-preceding ACCEPTED target by material overlap only; accept the
best passer; else go `unresolved` (bounded horizon) then `dead`. Never
looks at `target_heading`, actuator identity, or outcome — enforced by the
`Rule` type's signature (a pure function of an `overlap_metrics(a, b)` dict).

## Candidate metrics (computed for every candidate, every step)

`R_old = |prev∩C|/|prev|`, `R_new = |prev∩C|/|C|`, `jaccard = |prev∩C|/|prev∪C|`,
`dice = 2|prev∩C|/(|prev|+|C|)`, plus raw retained/lost/gained counts.
`overlap_metrics()` in `forward_material_trace_611.py`.

## Calibration data

`data/observational_corpus_611__val.npz` — **12 fully uncontrolled episodes,
seeds 236–247, 181 steps, 400 birds each.** Disjoint from seeds 500–504 and
from the train/test splits used to fit the (unrelated) predictive model
elsewhere in Stage 6.11. This is preference #1 of the task's calibration-
data ordering (existing uncontrolled runs, same regime). No additional
uncontrolled runs or synthetic-only data were needed.

Method (`code/calibrate_identity_rule.py`): the real `detect_69.propose`
detector run over every episode. Two distributions built, **never touching
any control seed or outcome**:
- **POSITIVE** ("natural gradual continuation"): every candidate at step t
  matched to its own best-Jaccard-overlap candidate at t+1, same episode —
  n=17,970 pairs.
- **NEGATIVE** ("unrelated flock" surrogate): candidates paired across
  DIFFERENT episodes at random (t, t'), same sample size — n=17,970 pairs.

## Threshold sensitivity (full grid: `data/identity_rule_calibration.json`)

| rule | threshold reaching FPR=0 | TPR at that threshold | notes |
|---|---|---|---|
| A (R_old alone) | ~0.65 | 0.974 | needs the highest threshold of the three — R_old alone is the weakest single-metric separator |
| B (Jaccard alone) | ~0.25–0.30 | 0.986–0.988 | widest stable FPR=0 plateau, threshold ∈ [0.25, 0.80] |
| D (Dice alone) | ~0.35 | 0.989 | comparable to B, needs a slightly higher threshold |
| C (two-sided R_old & R_new) | best: R_old≥0.4, R_new≥0.2 (J=0.9896) | 0.990 | no better separation than B despite 2 parameters |

## Frozen rule

**Rule B: `jaccard >= 0.30`.** Single parameter. Chosen because:
1. It reaches the FPR=0 plateau at the lowest threshold of the three
   single-parameter rules (ties with D, beats A by a wide margin), giving
   the widest safety margin before any unrelated-flock false-accept.
2. Rule C (two parameters) does not separate the calibration data any more
   cleanly than Rule B — the extra parameter buys nothing on this data, so
   per the task's explicit "prefer the simplest rule" instruction, the
   single-parameter rule wins.
3. Threshold = 0.30 is placed **inside** the flat FPR=0 plateau (0.25–0.80),
   not at its edge (0.20–0.25, the argmax-Youden-J point) — chosen for
   stability against small-sample calibration-curve noise, not to maximize
   J on this particular draw.
4. This value **was never chosen by looking at seeds 500–504.** It happens
   to numerically equal v1's own `RETENTION_MIN=0.30` constant
   (`lineage_611.py:39`) — noted here only as a post-hoc sanity check that
   the calibration landed on a physically sensible scale, not as any part
   of the selection process (the calibration script never reads that
   constant).

Full selection rationale, machine-readable: `data/identity_rule_calibration.json`,
key `frozen_rule.selection_rationale`.

## Auxiliary parameters (NOT independently calibrated — disclosed, per task §7)

- `missed_detection_horizon = 3` steps before declaring `dead`.
- `split_min_share = 0.30` (of the previous target's absolute size) —
  same scale as the primary threshold, for the same "genuinely substantial
  fragment" reasoning, but not swept/validated with the same rigor.
- `merge_max_r_new = 0.40`, `merge_min_size_ratio = 1.8` — diagnostic
  defaults for the merge flag.

These are explicitly marked `DIAGNOSTIC ONLY` in the frozen-rule JSON. The
task brief permits this ("exact split/merge thresholds may remain
diagnostic in this task if insufficiently validated").

## Known, disclosed limitation (found by the synthetic test suite, not hidden)

Test G (merge) **fails** under the frozen rule: a case where the previous
target is 100% retained (`R_old=1.0`) inside a candidate 5x larger
(`jaccard=40/200=0.20 < 0.30`) is rejected by the primary gate and goes
`unresolved` rather than being accepted-and-merge-flagged. This is an
honest property of a pure-Jaccard threshold (it penalizes size dilution
symmetrically with membership loss) and was **not patched** to force the
test to pass — patching it post-hoc, after seeing it fail a validation
test, would risk exactly the kind of outcome-directed rule engineering the
task prohibits, even though this test is theory-validation, not
control-outcome-validation. See `identity_validation.md` for the full
result and discussion.
