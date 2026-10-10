# Stage 6.12B — Identity and Disruption

## Coverage note

Per-rollout `V`/`event_corrected` fields are persisted in full for **6.12B-B
(refreshed access, 750 rollouts)** but NOT for 6.12B-A's exhaustive search
(`run_fixed_set_exhaustive_612b.py` stores only mean deltas per set, to
keep the exhaustive-coverage compute budget tractable — a disclosed
limitation, the same kind of gap Part I's correction pass found and
criticized in Stage 6.12's own Phase B/C). This document therefore reports
identity statistics from 6.12B-B only.

## 6.12B-B identity-valid fraction (750 rollouts: 5 states × 10 (K,q) × ~5
strategies × 3 streams)

| utility | mean identity-valid fraction |
|---|---|
| `V` (original semantics) | **0.820** |
| `V_conservative` | **0.724** |

Both are meaningfully LOWER than Stage 6.12's original (0.94-1.00 per
cell) or even Stage 6.12's conservative figure (64.0% pooled, computed in
Part I). Event breakdown (`event_corrected`, n=750):

| event | count | % |
|---|---|---|
| `none` (clean) | 544 | 72.5% |
| `lost_dead` | 116 | 15.5% |
| `material_split_flag` | 61 | 8.1% |
| `lost_dead+merge_flag` | 10 | 1.3% |
| `material_merge_flag` | 5 | 0.7% |
| other combinations | 14 | 1.9% |

**`lost_dead` (target loss, not merely a split/merge flag) is far more
common here (15.5%) than in Stage 6.12 (0.8% pooled)** — a genuine
difference, not a labelling artifact. Plausible contributors, disclosed
without further validated attribution: (a) Stage 6.12B's fresh states have
larger typical target sizes (up to 66 birds vs Stage 6.12's 22-55) and
longer/more complex dwell histories (`STATE_MANIFEST.md`); (b) the
24-step matched-effort control window is longer than most of Stage 6.12's
tested durations (mean `d`≈9 there vs. fixed `T_control=24` here); (c) the
refresh loop's online detection/tracing (interleaved with simulation) is
functionally identical to Stage 6.12's post-hoc tracing, so this is not a
tracer-implementation difference. **This elevated loss rate is itself a
relevant finding for `NEXT_STAGE_DECISION.md`**: longer, matched-effort
interventions carry materially higher target-loss risk in this system than
the short/medium fixed-schedule interventions Stage 6.12 characterized.

## Contact/turnover mechanism summary (6.12B-B)

- Mean `fraction_actuator_steps_in_contact` = **0.132** — even under
  active refreshing, forced birds are in direct contact with the traced
  target only about 13% of forced steps on average.
- Mean `n_turnovers` (actuator-set changes across the 24-step control
  period) = 6.7 — substantial identity churn even at moderate q, as
  expected by construction (higher at low q).

## Interpretation

The elevated target-loss rate is a genuine, disclosed complication for
interpreting Stage 6.12B-B's small/inconsistent `ΔJ` effects
(`REFRESHED_ACCESS_RESULTS.md`): some of the "near-zero" effect could
reflect target loss diluting `J` (via `V=0`→`J=0`) rather than a genuinely
flat behavioral response. Raw `A_release_late` (independent of `V`) should
be consulted alongside `J`/`ΔJ` for any follow-up work that wants to
separate these two explanations — both are retained in
`data/refreshed_access_612b.json`'s per-rollout rows.
