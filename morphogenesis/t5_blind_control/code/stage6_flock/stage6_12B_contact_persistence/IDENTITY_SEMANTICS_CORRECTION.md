# Identity Semantics Correction (source-verified)

## Where the mislabelling happened

`stage6_12_control_readiness/code/intervention_612.py`, `outcome_metrics`
(lines ~106-125, quoted from the code as it existed at the start of this
task):

```python
event = "none"
any_split = any(h.split_flag for h in hist[: release_end + 1])
any_merge = any(h.merge_flag for h in hist[: release_end + 1])
if V == 0:
    ...
if any_split:
    event = "confirmed_split" if event == "none" else event + "+split_flag"
if any_merge:
    event = "confirmed_merge" if event == "none" else event + "+merge_flag"
```

`h.split_flag`/`h.merge_flag` come from
`material_identity_step2_20260921/code/forward_material_trace_611.py`'s
`ForwardMaterialTrace611.step`: `split_flag` fires when ">=2 accepting
candidates each retain a substantial absolute share (`split_min_share`=
0.30) of the previous target"; `merge_flag` fires on a size-ratio/overlap
heuristic. Both are pure MATERIAL-OVERLAP heuristics, computed from
`overlap_metrics` (Jaccard/Dice/retained-fraction) — **neither checks the
true simulator state for anything resembling a physically validated
split/merge event** (no velocity divergence, no independently calibrated
separation threshold, nothing beyond set-overlap arithmetic).

`CURRENT_RESEARCH_STATUS.md`'s own "Conceptual boundaries" section states
this explicitly: *"A confirmed physical split or merge should terminate
strict same-object continuity... No physical-split/merge threshold has
been validated in this repository yet."* Labelling the tracker's own flag
`confirmed_split` therefore contradicted the repository's own established
epistemic boundary — this was a genuine terminology bug in Stage 6.12's
implementation, not a documentation-only error (verified by reading the
source, not the docstrings, per this task's instruction to prefer source
over prose wherever they could differ).

## Correction applied

- **Stage 6.12 (existing data)**: `stage6_12_control_readiness/code/
  correction_612.py` adds an `event_corrected` field to every rollout in a
  NEW derivative file (`data/phaseA_results_612_corrected.json`), renaming
  `confirmed_split`→`material_split_flag`, `confirmed_merge`→
  `material_merge_flag`. The original files and their `event` field are
  untouched — anyone reading `phaseA_results_612.json` directly still sees
  the original (now known to be overreaching) label, with this document
  and `STAGE612_CORRECTION_MEMO.md` as the record of what it actually
  means.
- **Stage 6.12B (this stage's fresh code)**: `intervention_612b.
  add_conservative` computes `event_corrected` and `V_conservative`/
  `J_conservative` AT COMPUTE TIME, for every rollout, from the start —
  Stage 6.12B never produces a `confirmed_split`/`confirmed_merge` label
  in its own primary output fields (`event_corrected` is what all Stage
  6.12B analysis documents cite).

## What is still true and still unvalidated

- `ForwardMaterialTrace611`'s split/merge flags remain a useful, disclosed
  ADVISORY signal — genuinely informative about material-overlap ambiguity
  — but they are not, and this correction does not newly claim they are, a
  validated physical-split detector.
- No independently calibrated physical-split/merge criterion exists in
  this repository after this correction either. `V_conservative` is
  explicitly a LOWER-BOUND sensitivity convention (deliberately more
  restrictive than necessary), not a claim of having solved this gap.
- Genuinely hedged labels from the original code
  (`candidate_split_or_merge_interruption`, used when `V=0`) were already
  appropriately cautious and are unchanged by this correction.
