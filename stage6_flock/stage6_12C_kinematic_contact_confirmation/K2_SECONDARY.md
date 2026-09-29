# Stage 6.12C — K=2 Secondary Results

Analysis code: `code/analysis_612c.py` (`k2_analysis`). Reduced scope per
`README.md`: 6 confirmatory streams/pair (not 8), 26 pairs/state (top
predicted pair + 24 uniform-random pairs + 1 low-predicted pair), d=8.
Full data: `data/k2_pairs_612c.json` (260 rows).

Per the frozen sum-aggregation rule (`C_hat_S = sum_{j in S} C_hat_j`, no
interaction term), the top-predicted PAIR is provably the pair formed by
the top-2 individually-scored K=1 candidates (see `CONFIRMATORY_
PROTOCOL.md`) — this was not separately re-derived per pair.

## Per-state comparison (mean ΔJ_conservative, 6 confirmatory streams)

| state | top-predicted pair | random pairs (median of 24) | low-predicted pair | top − random median |
|---|---|---|---|---|
| s612c_00 | 0.00000 | -0.00134 | 0.00702 | +0.00134 |
| s612c_01 | -0.02704 | -0.00852 | -0.00962 | -0.01853 |
| s612c_02 | 0.12030 | 0.00289 | **0.27854** | +0.11741 |
| s612c_03 | 0.01160 | 0.00046 | 0.00573 | +0.01114 |
| s612c_04 | 0.00199 | 0.00396 | 0.01410 | -0.00197 |
| s612c_05 | 0.01057 | 0.01085 | 0.00871 | -0.00028 |
| s612c_06 | 0.00257 | 0.00149 | 0.00157 | +0.00108 |
| s612c_07 | -0.00516 | -0.00120 | -0.00278 | -0.00396 |
| s612c_08 | 0.00079 | -0.00052 | 0.00054 | +0.00130 |
| s612c_09 | 0.00446 | 0.00259 | 0.00328 | +0.00187 |

## Summary (state-clustered, n=10 states)

| quantity | value |
|---|---|
| top-predicted pair mean ΔJ_conservative | 0.01201 |
| random-pairs median mean ΔJ_conservative | 0.00107 |
| low-predicted pair mean ΔJ_conservative | **0.03071 — higher than the top-predicted pair** |
| top − random-median mean difference | +0.01094 |
| 90% CI (state-clustered bootstrap) | [-0.00347, +0.03383] — spans zero |
| fraction of states where top pair beats random median | 6/10 = 60% |

## Interpretation

**Weakly favorable point estimate, not state-clustered-reliable, and
internally inconsistent with the predictor's own claim.** The top-
predicted pair does beat the random-pair median in 6/10 states and its
mean absolute lift (+0.0109) is nominally positive, but the 90% CI spans
zero, so this does not clear a reliable-evidence bar on its own.

**More importantly, the LOW-predicted pair has the highest mean effect of
all three groups (0.0307), driven substantially by one state
(`s612c_02`, low-pair ΔJ_conservative=0.279 — an extreme outlier relative
to every other value in this entire stage's dataset).** Because the
top-predicted and low-predicted arms are each a SINGLE frozen pair per
state (unlike the random arm, which averages 24 pairs and is therefore
much less noisy), this single-pair volatility is expected and should not
be read as "low-predicted-contact pairs cause larger effects than
high-predicted ones" — it is more consistent with one or two
high-variance states dominating a small, unreplicated per-state
comparison. Removing `s612c_02` (the visibly extreme state) would bring
the low-pair mean much closer to the random-pair range; this ad hoc
exclusion is reported here for transparency, not substituted as the
primary result, per the claims-discipline rule against selecting
favorable states after viewing outcomes.

**Primary question answered**: does the prospective top-predicted pair
beat random pairs across fresh states? **Not reliably** — a positive but
CI-spanning-zero point estimate, further undermined by the low-predicted
pair's even larger (if noise-driven) mean. This is consistent with, not a
reversal of, the K=1 primary and predictor-validation findings: the
frozen kinematic aggregation rule does not show reliable state-clustered
value at K=2 either.
