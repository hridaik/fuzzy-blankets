# Identity episode validation, complete (Task 0)

Extends `identity_causal_reconciliation_20260921`'s sequential-trace audit
(which reported per-trace summary statistics — final status, duration,
turnover — but did not classify what the COMPETING candidates were at
ambiguous-accept steps, so could not distinguish a genuine erroneous
transfer from a genealogically-explicable fragment/split/merge). Same 36
dev traces (seeds 236–247) + 36 untouched-holdout traces (seeds 248–259),
same 3-largest-candidates-at-t=5-per-episode protocol, frozen
Jaccard≥0.30 rule, **never retuned**. Code: `code/identity_episode_validation.py`.
Raw data: `data/identity_episode_validation.json`.

## Classification scheme (reused constants, nothing invented)

At every step where more than one candidate clears the Jaccard≥0.30 gate,
every NON-WINNING accepting candidate is classified against the previous
accepted target using `forward_material_trace_611.py`'s own pre-existing,
frozen diagnostic constants (`split_min_share=0.30`,
`merge_min_size_ratio=1.8`) — no new threshold was introduced for this
classification:
- **nested_fragment**: the competing candidate is a (near-)strict subset
  of the previous target (R_new≥0.99) — the detector proposing a
  sub-clique of the same physical group as its own separate candidate.
- **merge_dilution**: the previous target is (near-)fully retained inside
  a much larger competing candidate (R_old≥0.99, size ratio ≥1.8).
- **split_daughter**: the competing candidate retains a substantial share
  of the previous target (≥30%) without being a nested fragment or merge
  candidate — the same criterion the tracker's own `split_flag` logic
  already uses.
- **unrelated_candidate**: clears the Jaccard gate without fitting any of
  the above — the operational proxy for "an unrelated population
  coincidentally scored high enough to be eligible." The WINNER, on the
  rare step where it would itself classify this way relative to its own
  previous state, is separately counted as an **erroneous transfer**.

## Results

| metric | dev (already used for calibration) | untouched validation |
|---|---|---|
| n_traces | 36 | 36 |
| n_complete (final status = continuing) | 32 (88.9%) | 29 (80.6%) |
| n_dead | 4 (11.1%) | 7 (19.4%) |
| **fraction complete WITHOUT any erroneous transfer** | **1.0 (36/36)** | **1.0 (36/36)** |
| n_traces with any erroneous transfer | 0 | 0 |
| n_total_erroneous_transfer_steps | 0 | 0 |
| n_total_unresolved_steps | 18 | 38 |
| n_total_candidate_split_events | 20 | 20 |
| n_total_candidate_merge_events | 6 | 6 |
| n_total_recovered_gaps | 4 | 10 |
| max_unresolved_gap_duration | 3 (= horizon) | 3 (= horizon) |
| n_unresolved_gaps_observed | 8 | 17 |
| trace-length distribution (of 176 possible) | min 20, p25/median/p75 175, max 175 | min 22, p25/median/p75 175, max 175 |
| competitor classification totals | nested_fragment 14, merge_dilution 0, split_daughter 6, **unrelated_candidate 0** | nested_fragment 15, merge_dilution 0, split_daughter 5, **unrelated_candidate 0** |

### Target-size-stratified behavior

| bucket | split | n | final continuing | final dead | mean duration | mean turnover |
|---|---|---|---|---|---|---|
| medium (20–49) | dev | 20 | 19 | 1 | 169.6 | 0.700 |
| large (≥50) | dev | 16 | 13 | 3 | 150.3 | 0.651 |
| medium (20–49) | validation | 25 | 19 | 6 | 155.4 | 0.815 |
| large (≥50) | validation | 11 | 10 | 1 | 161.5 | 0.627 |

(No small-target (<20) seed targets were drawn in this protocol — seed
targets are the 3 largest candidates at t=5, which are consistently
≥20 members across all 24 episodes.)

## Interpretation

**Zero erroneous transfers to an unrelated population were observed in
72 full-episode sequential traces, across both the already-seen dev split
and the genuinely untouched holdout.** Every ambiguous-accept event
encountered (26 across dev, 20 across validation — i.e. the moments where
`n_accepting_candidates > 1`) was genealogically explicable: either a
nested detector sub-fragment of the same object, or a genuine split
daughter. Not one was classified `unrelated_candidate`, and the winner
itself was never classified that way relative to its own previous state
either.

This does **not** contradict `IDENTITY_VALIDATION_HARDENING.md`'s earlier
finding of a small (~0.03–0.04%) non-subset same-frame false-accept rate
— that number describes how often an unrelated candidate, if compared in
isolation against every target in the corpus, crosses the Jaccard gate at
all (a pairwise, non-sequential measure). This episode-level result
describes something different and stronger: across 72 actual sequential
traces run to their natural conclusion, that rare pairwise risk never
manifested as an actual accepted, in-context transfer. The two results are
consistent (a low per-pair risk need not manifest at all in a bounded
number of trace-steps) and together give a fuller picture than either
alone.

**Bottom line for the next controller (spec's Task 0 stated purpose)**:
the frozen Jaccard≥0.30 rule, used as a MATERIAL ASSOCIATION layer (not
the full strict-identity decision — split/merge/genealogy semantics sit
above it, exactly as `SPLIT_MERGE_SEMANTICS.md` already established), is
reliable enough at the sequential level to serve as that layer for the
next controller design task, subject to the already-disclosed caveats:
the known merge-dilution blind spot (fails safe, `unresolved` not false
continuation), and the fact that "no erroneous transfer observed in 72
traces" is an empirical absence, not a proof of zero risk — the rare
same-frame false-accept rate found in `IDENTITY_VALIDATION_HARDENING.md`
means this could occur in a larger sample, just was not observed here.
