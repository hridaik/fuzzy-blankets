# Stage 6.12C — Identity and Disruption

Computed from `data/k1_rollouts_612c.json` (2,400 rows; 1,600 confirmatory
+ 800 search). K=2 pair rollouts (`data/k2_pairs_612c.json`) preserve only
mean paired ΔJ per pair, not per-rollout identity fields — this is a
disclosed scope reduction (see below), matching in spirit (though not
matching the specific gap) Stage 6.12's own Phase B/C identity-field gap
documented in `STAGE612_CORRECTION_MEMO.md`'s "Known limitation."

## K=1 identity outcomes (2,400 rollouts, all use `event_corrected` —
`material_split_flag`/`material_merge_flag`, never "confirmed")

| quantity | confirmatory streams (n=1,600) |
|---|---|
| `V=1` (permissive strict continuation through release window) | **100.0%** |
| `V_conservative=1` (strict: zero split/merge flags, zero unresolved steps) | **91.1%** |
| `event_corrected == "none"` | 91.1% (1,458/1,600) |
| `event_corrected` contains `material_split_flag` | 8.9% (142/1,600) |
| `event_corrected` contains `material_merge_flag` | 0.0% |
| `event_corrected` contains `lost_dead` | 0.0% |
| `event_corrected` contains `unresolved` | 0.0% |
| mean target size at end of window | 57.8 birds (mean start-of-window size across states ≈ 46 — an upward drift consistent with Stage 6.12's own "split-continuation artifact, not recruitment" finding, `COLLATERAL_ANALYSIS.md`) |
| mean `A_release_late` (late-release alignment) | 0.135 |

**Identity failure does not explain this stage's weak effect-size
findings.** As in Stage 6.12/6.12B, `V` (permissive) never fails at K=1 —
every confirmatory rollout retained SOME material continuation. The
CONSERVATIVE identity-valid fraction (91.1%) is notably higher than Stage
6.12's pooled 64.0% and closer to Stage 6.12B's per-state range — K=1,
d=8 is a much smaller, shorter perturbation than Stage 6.12's full grid
(up to K=8, d=24) or Stage 6.12B's matched-effort 24-step interventions,
so a lower disruption rate here is expected, not a methodological
artifact.

## Per-state `V_conservative` rate (confirmatory streams, n=160/state)

| state | V_conservative rate |
|---|---|
| s612c_00 | 99.4% |
| s612c_01 | 97.5% |
| s612c_02 | 97.5% |
| **s612c_03** | **55.6%** — the one clearly disruption-prone state in this sample |
| s612c_04 | 95.6% |
| s612c_05 | 80.6% |
| s612c_06 | 100.0% |
| s612c_07 | 85.0% |
| s612c_08 | 100.0% |
| s612c_09 | 100.0% |

**Substantial state heterogeneity, one outlier state.** `s612c_03` shows
a conservative identity-valid rate of only 55.6%, far below every other
state (next-lowest is 80.6%) — consistent with the state-heterogeneity
pattern already established in Stage 6.12
(`STAGE612_CORRECTION_MEMO.md` Q4) and Stage 6.12B. This state is NOT
excluded from any analysis (per the task brief's prohibition on excluding
states after seeing intervention behavior) but is flagged here as the
one state where split-flag-driven identity ambiguity is common enough to
materially affect the `J_conservative` vs `J_assoc` gap.

## Disclosed scope reduction: K=2 per-rollout identity fields

`run_k2_for_state` (`code/run_confirmatory_612c.py`) records only
`mean_delta_assoc`/`mean_delta_conservative` per pair, not the full
per-rollout `V`/`event_corrected`/split-flag record that K=1 preserves.
This was a deliberate compute/storage economy given the K=2 arm's already-
reduced scope (26 pairs × 6 streams × 10 states = 1,560 rollouts) — full
per-rollout identity logging for K=2 would not have changed any ΔJ number
already reported in `K2_SECONDARY.md` (which only ever uses the mean), but
it does mean this document cannot report a K=2-specific identity-validity
breakdown. If a future stage needs per-rollout K=2 identity records, this
is the concrete extension point (`run_k2_for_state` would need to persist
`out["V_conservative"]`/`out["event_corrected"]` per rollout, not just the
aggregated deltas — a small code change, not re-simulation, if the
underlying `run_one_b` calls are re-run with logging enabled).

## Disruption in the duration sub-study

See `DURATION_SAFETY.md` — 0% lost/dead at both d=8 and d=24 for K=1
forcing in the 5-state subset, materially lower than Stage 6.12B's 15.5%
K∈{2,4},d=24 finding (different forcing cardinality, not a contradiction).
