# State-Level Reanalysis (Part I, existing Stage 6.12 data)

Full detail in `stage6_flock/stage6_12_control_readiness/STAGE612_
CORRECTION_MEMO.md` §4 and `data/correction_612_summary.json`. This
document isolates the state-level table and its implication for Stage
6.12B's design.

## Per-state mean paired effect (Stage 6.12, 9 states, 144 rollouts/state)

| state | role | mean Δ (J_assoc) | mean Δ (J_conservative) | non-`none`-event rate |
|---|---|---|---|---|
| s612_00 | dev | +0.0058 | -0.0270 | 31.2% |
| s612_01 | dev | -0.0012 | -0.0012 | 0.0% |
| s612_02 | dev | **+0.1146** | +0.0237 | 59.0% |
| s612_03 | dev | +0.0104 | +0.0327 | 68.1% |
| s612_04 | dev | **-0.1448** | +0.0288 | 38.2% |
| s612_05 | dev | +0.0001 | +0.0303 | 27.8% |
| s612_06 | holdout | -0.0004 | -0.0004 | 0.0% |
| s612_07 | holdout | +0.0179 | -0.0273 | 44.4% |
| s612_08 | holdout | +0.0077 | -0.0024 | 66.7% |

## Answer to the driving question

**The pooled near-zero result is a genuine heterogeneous cancellation, not
uniform near-zero states.** Two states (`s612_02`, `s612_04`) show large
effects of opposite sign under `J_assoc` (+0.115 / -0.145); `s612_04`
reverses sign entirely under conservative scoring. Two states
(`s612_01`, `s612_06`) show essentially zero non-`none`-event rates —
genuinely clean, uneventful trajectories with near-zero effect — while
others (`s612_02`, `s612_03`, `s612_08`) have >55% non-clean event rates.

**Implication for Stage 6.12B**: state identity matters a great deal to
the outcome landscape here. This is part of why Stage 6.12B samples FRESH
states rather than reusing Stage 6.12's 9 states (avoiding overfitting any
conclusion to this particular heterogeneous mix), and why every Stage
6.12B result is reported per-state as well as pooled/state-clustered (see
`STATISTICAL_ANALYSIS.md`).
