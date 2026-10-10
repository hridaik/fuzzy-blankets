# Stable-Selectivity Analysis (Stage 6.12C follow-up)

**Bounded, analysis-only follow-up to `stage6_12C_kinematic_contact_confirmation/`.**
No new simulation was run. Every number here is computed from the already-frozen
`../data/k1_candidates_612c.json` (200 rows = 10 states x 20 candidates) and
`../data/k1_rollouts_612c.json` (2,400 rows = 200 candidates x 12 physics
streams), which Stage 6.12C's exhaustive K=1, d=8 run already produced. This
directory does not modify, overwrite, or re-run anything under
`../code/`, `../data/`, or `../figures/`.

## The question

Stage 6.12C (`ORACLE_DECOMPOSITION.md`, `NEXT_STAGE_DECISION.md`) found a
large per-stream "outcome oracle" advantage (reported ~6.9x the
random/median candidate) that survives state-clustered bootstrapping, but
found that neither a deployable kinematic-contact predictor nor a genuine
forced-future contact oracle explains it (Case C). This leaves open exactly
the question this directory answers: **is that headroom a reproducible
property of specific actuators (something a next-stage feature-discovery
experiment could learn), or is it mostly winner's-curse inflation from
taking the max of 20 noisy candidates per stream, with no actuator identity
that predicts across futures?**

## Answer, in one paragraph

**Decision 2** (see `NEXT_EXPERIMENT_DECISION.md`). Cross-validated,
out-of-sample actuator selection collapses toward the random/median baseline
in essentially every state; stable-actuator variance is ~0-4% of total
candidate x stream variance in every one of the 10 states; ranking
reliability across independent stream splits is statistically indistinguishable
from zero (mean Spearman rho about 0.001 at 6 training streams, no
improvement from 1 to 6 training streams); and a permutation null that
destroys stable candidate identity while preserving every stream's own
outcome distribution reproduces the ENTIRE per-stream clairvoyant-oracle
advantage exactly (by construction, see `ORACLE_WINNERS_CURSE.md`) and
reproduces Stage 6.12C's own headline "outcome oracle" number (0.0222) with
**zero or even a slightly negative excess** over the null mean. The
selective headroom Stage 6.12C found is real (candidate identity clearly
matters for outcome IN a given realized future), but it is not knowable in
advance from past physics streams at this state count -- it behaves like
stochastic opportunity, not stable actuator leverage.

A significant, separate finding (`CONTACT_METRIC_AUDIT.md`): Stage 6.12C's
`mech_cumulative_contact_edges` metric is geometric distance-only (`D<=R`),
symmetric/undirected, ignoring both field-of-view and directionality. It is
NOT the simulator's own directed causal influence relation (`live_edges` in
`moving_flock.py`, which additionally requires the RECEIVER's field of view,
`(r_j-r_i).d_i >= 0`, and is asymmetric). Stage 6.12C's contact-based
conclusions should be read as "geometric proximity does not explain the
headroom," not "no causal-interaction channel explains the headroom" --
directed FOV-gated contact was never tested.

## Reading order

1. `DATA_DESIGN_AUDIT.md` -- confirms the crossed design and paired
   no-control structure this whole analysis depends on.
2. `VARIANCE_DECOMPOSITION.md`, `RANK_RELIABILITY.md`,
   `CROSS_VALIDATED_ORACLE.md`, `ORACLE_WINNERS_CURSE.md` -- the primary
   quantitative chain of evidence (sections 5-10 of the task brief).
3. `CANDIDATE_RECURRENCE.md`, `PAIRWISE_STABILITY.md` -- descriptive
   corroboration.
4. `STATE_TAXONOMY.md` -- state-by-state synthesis.
5. `CONTACT_METRIC_AUDIT.md` -- what "contact" in Stage 6.12C actually
   measured, from source code.
6. `MEMBERSHIP_EMBEDDING_CLUES.md`, `INTERIOR_ACTUATION_METHOD_NOTE.md` --
   exploratory, forward-looking, explicitly non-causal / methods-only.
7. `FINAL_STABLE_SELECTIVITY_FINDINGS.md`, `NEXT_EXPERIMENT_DECISION.md` --
   synthesis and the Decision 1/2/3 call.

## Directory structure

```
code/       analysis.py (all statistics), viz.py (all figures) -- both
            read-only against ../data/*.json, write only into this
            directory's own data/ and figures/
data/       stable_selectivity_results.json -- every number in every .md
            file below is machine-traceable to a field in this file
figures/    53 PNGs: 5 per-state figures x 10 states + 3 pooled figures
```

## What this directory does NOT do

Run any new simulator rollout. Modify `PREDICTOR_FREEZE.md`, any Stage
6.12C data file, or any Stage 6.12C document. Design or run the interior-
actuation experiment (only a method note is written, per the task brief).
Claim a causal mechanism for the headroom -- this is a decomposition of
whether the headroom is *stable*, not a search for *why*.
