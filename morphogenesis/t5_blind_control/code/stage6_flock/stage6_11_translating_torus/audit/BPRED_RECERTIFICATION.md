# Bpred Recertification — Stage 6.11B (item 12)

Additive. `delta=0.01` (`predictive_boundary_611.DELTA_SUFFICIENT`) never
moved. The pretrained relational predictor is frozen (no online-buffer
refit — `INVARIANCE_AND_TRANSFER_6_11.md` established that refit is net
harmful at every speed tested, including the trained one; not re-litigated
here). Bpred is not used to restrict any control pool in this pass — it
remains, as the architecture note (`RESULTS_6_11B.md` §Architecture)
states, a parallel, task-neutral observational-screening object. Script:
`audit/bpred_recertification_611.py`. Raw output:
`audit/bpred_recertification_611.json`.

## Candidate used

A fresh example (val episode 0, t=90, 75-member candidate, M_obs=12) — a
different snapshot from the one `RESULTS_6_11.md` §4 originally certified
(that snapshot's own K=12-boundary numbers are frozen/unrepeated, per the
freeze instruction; this is an independent additional data point at the
compute budget available for this pass's construction row set, ~800 rows
from a 10-step recent window, smaller than the original's construction
volume).

## Results

| challenger | base test log-loss | challenge gap (point) | challenge gap (95% upper) | ≤ δ=0.01? |
|---|---|---|---|---|
| single-source (reproduction) | 0.419 | 0.0042 | 0.0054 | **Yes** |
| pair/2-source block (new) | 0.448 | 0.0058 | 0.0070 | **Yes** |
| regularized cross-fitted multivariate (new) | 0.384 (base features) vs 0.385 (augmented) | −0.0002 (augmented is NOT better) | — | **Yes (no residual signal found)** |

At this candidate, the greedy construction (`K_max_audit=24`, double the
original cap) added **zero exterior sources** (`B = []`, `interior_only_loss
== final_loss == 0.1315`) — the interior-only conditioning already explains
this candidate's periphery as well as any exterior source or exterior-pair
addition does. This is consistent across all three challenger classes: the
single-source and pair/block challengers both certify the (empty) boundary
as sufficient well within `δ`, and the multivariate residual challenger
(presence-indicator features for the top 15 individual-gain exterior
sources, plus pairwise-interaction terms among the top 5, L2-regularized,
5-fold cross-fitted on 4,800 rows) finds **no held-out improvement at all**
over the base features — if anything, a negligible degradation (regularized
augmentation adding noise, not signal).

## Interpretation

**An economical predictive screen does appear to exist at this candidate,
and stronger multi-source/interaction challengers do not overturn it** —
neither a second exterior source acting jointly, nor a small, regularized
model with genuine interaction terms, recovers meaningfully more predictive
information than the (here, empty) single-source-certified boundary. This
is a positive result for the ORIGINAL certification methodology's own
discipline (single-source ablation is not obviously leaving real
synergistic structure on the table, at least at this candidate) — but it is
one candidate, at a reduced construction-row budget, and should not be
read as a general statement that Bpred certification is robust everywhere;
the original `RESULTS_6_11.md` example (K=12, hitting the construction cap)
shows boundaries are not always this compact. No `δ` was moved to produce
either result.
