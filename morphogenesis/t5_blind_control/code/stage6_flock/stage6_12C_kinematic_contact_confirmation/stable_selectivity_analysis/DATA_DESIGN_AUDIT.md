# Data Design Audit

Computed by `code/analysis.py:data_design_audit()`, stored at
`data/stable_selectivity_results.json["data_design_audit"]`.

## Data shape (confirmed programmatically, not assumed from prose)

| quantity | value |
|---|---|
| number of states | 10 (`s612c_00`..`s612c_09`, seeds 63200-63209) |
| candidates per state | 20 (uniform across all 10 states) |
| search (diagnostic) streams per candidate | 4 (uniform across all 10 states) |
| confirmatory streams per candidate | 8 (uniform across all 10 states) |
| total streams per candidate (search+confirm, pooled for this analysis) | 12 |
| candidate-level rows | 200 (10 x 20) |
| rollout-level rows | 2,400 (200 x 12) |

## Crossed design

**Confirmed complete in all 10/10 states.** For every state, all 20
candidates have exactly the same number of search-stream entries (4) and
confirmatory-stream entries (8) in `search_delta_conservative_all` /
`confirm_delta_conservative_all` -- there is no missing cell, no candidate
with a truncated stream list. This means the candidate x stream matrix used
throughout this analysis (20 x 12 per state) is a genuinely complete,
non-ragged design, which is what makes the variance decomposition,
train/test splitting, and permutation-null analyses in the following
documents valid without imputation.

## Paired no-control baselines

**Confirmed shared across all 20 candidates, within every (state, stream)
cell, in all 10/10 states.** Verified directly from `k1_rollouts_612c.json`
(not assumed from `CONFIRMATORY_PROTOCOL.md`'s prose): for every
`(state_id, stream_role, stream_idx)` triple, every one of the 20
candidate-rows sharing that triple carries the identical `physics_seed`.
This is exactly the CRN (common random numbers) design Stage 6.12C's
protocol describes, and it is what licenses treating `ΔJ_conservative(j,r)`
for different candidates `j` at the same stream `r` as paired observations
of "the same physics future, different actuator" -- the premise this whole
follow-up's train/test and permutation analyses rest on.

## Both outcome metrics available candidate x stream

`ΔJ_conservative` and `ΔJ_assoc` are both present for every candidate x
stream cell (`confirm_delta_conservative_all` / `confirm_delta_assoc_all`,
and the analogous `search_*` arrays). `ΔJ_conservative` is used as PRIMARY
throughout this analysis, matching Stage 6.12C's own convention;
`ΔJ_assoc` sensitivity numbers are reported in
`VARIANCE_DECOMPOSITION.md` (variance-fraction sensitivity) and are directionally
consistent with the conservative-metric result (near-zero stable-actuator
variance fraction under either metric).

## What this analysis adds beyond the raw JSON

Stage 6.12C's own `k1_candidates_612c.json` already carries per-state,
per-candidate summary fields (`mean_confirm_delta_conservative`,
`mean_search_delta_conservative`, etc.) and the full per-stream arrays
needed to reconstruct the 20x12 matrix exactly. No new rollout data was
needed or generated; this analysis only recombines, resamples (bootstrap /
permutation / train-test splits), and decomposes numbers Stage 6.12C already
computed and stored.

## One data-provenance correction, stated plainly (see `ORACLE_WINNERS_CURSE.md` for the full analysis)

Stage 6.12C's `ORACLE_DECOMPOSITION.md` describes its "outcome oracle" in
prose as "`j_effect_oracle(r) = argmax_j ΔJ_conservative(j,r)` ... per
stream, averaged into a per-state mean" -- i.e., a true per-stream
clairvoyant oracle (mean of per-stream maxima). Re-deriving the reported
number (0.0222, `confirm_delta_conservative_all` only) directly from the raw
per-stream arrays shows this description does not match what the code
(`analysis_612c.py:oracle_decomposition`) actually computed:
`effect_oracle_top = max(srows, key=lambda r: r["mean_confirm_delta_conservative"])`
selects the single candidate with the highest MEAN confirmatory-stream
delta, i.e. the **state-stable mean oracle** (`argmax_j mean_r ΔJ(j,r)`,
Definition B in `CROSS_VALIDATED_ORACLE.md`), not the true per-stream max
averaged over streams (Definition A). Recomputing Definition A directly from
the same data gives a LARGER number (confirm-only mean across states:
0.0544, vs. Definition B's 0.0222 reproduced exactly here from
`confirm_delta_conservative_all`). This is not a criticism of Stage 6.12C's
arithmetic (its number, 0.0222, is exactly reproduced here as Definition B)
-- it is a correction of what that number actually measures: it was already
a partially-stability-filtered quantity (it requires one candidate to be
good ON AVERAGE across all 8 confirmatory streams, using those same 8
streams to both select and evaluate), not a naive per-stream maximum. See
`ORACLE_WINNERS_CURSE.md` for why this matters: even this
already-partially-stable quantity shows ~zero excess over a
no-stable-identity permutation null.
