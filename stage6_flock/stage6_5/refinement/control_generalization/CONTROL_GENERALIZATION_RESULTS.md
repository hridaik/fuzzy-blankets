# CONTROL_GENERALIZATION_RESULTS.md — HARD GATE B

Frozen protocol: `../PROTOCOL_6_5R.md` (Part B section) /
`../configs/protocol_6_5r.yaml` (`part_b_control_generalization` block),
hash `../logs/protocol_6_5r_part_b.sha256`. All numbers below are read
directly from `data/discriminating_flocks.json` and `data/
four_controller_comparison.json`; none are hand-adjusted. Figures:
`figures/fig_r6_5_2_control_generalization.png` (R6.5-2), `figures/
fig_r6_5_3_inference_quality_vs_control.png` (R6.5-3).

## The discriminating-flock scan

Scanning **new** seeds 41-71 (stopped early once 12 discriminating flocks
qualified, well inside the predeclared 41-140 range), 17 seeds qualified as
flocks (`find_flock` succeeded) and **12 met the frozen discriminating
criterion** (`P_oracle >= 0.7`, `P_random(matched-to-oracle-budget) <= 0.3`,
20-replicate screen): seeds **42, 43, 49, 50, 51, 52, 53, 63, 68, 69, 70,
71**. This hits the upper end of the target range (8-12) inside the first
31 candidate seeds — a materially easier scan than the pessimistic 100-seed
budget suggested might be needed.

## The headline result

**On this evidence, inferred-boundary control does NOT outperform
matched-budget null intervention across the discriminating benchmark.**
50-replicate, fresh (independent-of-screening) evaluation of all four
controllers:

| seed | `\|B^D\|` | `\|\hat B\|` | recall | oracle `k`, `P` | inferred `k`, `P` | fiedler `k`, `P` | random `k`, `P` |
|---|---|---|---|---|---|---|---|
| 42 | 13 | 5 | 0.38 | 8, **0.92** | 3, 0.02 | 3, 0.00 | 3, 0.00 |
| 43 | 16 | 5 | 0.31 | 7, **0.82** | 4, 0.00 | 12, 0.00 | 4, 0.00 |
| 49 | 20 | 3 | 0.15 | 9, **1.00** | 3, 0.00 | 21, 0.00 | 3, 0.00 |
| 50 | 12 | 5 | 0.42 | 12, **1.00** | 2, 0.00 | 2, 0.00 | 2, 0.00 |
| 51 | 25 | 4 | 0.16 | 9, **0.96** | 4, 0.00 | 5, 0.00 | 4, 0.00 |
| 52 | 15 | 4 | 0.27 | 15, **1.00** | 4, 0.00 | 0, 0.00 | 4, 0.00 |
| 53 | 22 | 7 | 0.32 | 22, **1.00** | 7, 0.00 | 61, **0.70** | 7, 0.02 |
| 63 | 12 | 5 | 0.42 | 12, **0.96** | 4, 0.00 | 58, 0.06 | 4, 0.00 |
| 68 | 11 | 5 | 0.45 | 11, **0.90** | 2, 0.00 | 2, 0.00 | 2, 0.00 |
| 69 | 15 | 6 | 0.40 | 9, **0.72** | 3, 0.00 | 0, 0.00 | 3, 0.00 |
| 70 | 14 | 0 | 0.00 | 9, **1.00** | 0, 0.00 | 0, 0.00 | 1, 0.00 |
| 71 | 10 | 2 | 0.20 | 10, **0.88** | 2, 0.00 | 2, 0.00 | 2, **0.08** |

- **Precision stays 1.00 on every flock** (as in Stage 6.5's original
  evaluation) except seed 70, where `\hat B` came back **empty** — the
  inference pipeline found no exterior bird worth adding at all on this
  flock, a new failure mode not seen in the original 3-flock evaluation.
- **Recall (0.15-0.45, excluding the empty case) matches the original
  range (0.18-0.58) closely** — the inference pipeline behaves consistently
  on new flocks, not degenerately.
- **Inferred controller success is ~0 on 11 of 12 flocks** (exactly 0.00 on
  10, and a negligible 0.02 on seed 42) — nowhere close to the oracle's
  0.72-1.00. On **seed 71 the matched-budget random arm (0.08) beat the
  inferred arm (0.00)** — the one clear reversal in this benchmark.
- **Aggregate**: mean `P_success` — oracle 0.93, inferred **0.0017**,
  Fiedler 0.063, random 0.0083. Only **1 of 12 flocks** (seed 42, `Delta_s =
  +0.02`) shows the inferred controller beating random at all, and by a
  negligible margin. The flock-level bootstrap CI (10,000 resamples over
  flocks, not replicates) for the mean `Delta_s = P_{\hat B} - P_{\rm
  random}` is **[-0.0217, +0.0033]** — spans zero, i.e. **statistically
  indistinguishable from no effect** across this benchmark.

## Why — a mechanistic note (light-touch, per B7's exploratory framing)

The oracle's own actuator budget on this new benchmark (7-22, mean 11.1) is
similar to or larger than on the original 3 held-out flocks (9, 9, 13),
while `\hat B`'s size stays in its usual 2-7 range (dictated by Part 1's
precision-first stopping rule, unrelated to any coverage objective). A quick
check of whether `\hat B` at least captures the highest-multiplicity
(most-I0-connected) shell members — the ones a `q`-fold multicover objective
leans on most — shows it usually does (`\hat B`'s mean I0-degree exceeds
`B^D`'s own mean on 8 of 12 flocks, and `\hat B` includes the single
highest-multiplicity "hub" bird on 6 of 12). **The failure is not primarily
about which birds `\hat B` selects — it is about `q=2`/`gamma=0.5`
multicover coverage being a strongly nonlinear, threshold-like function of
budget size**: reaching `gamma=0.5` at `q=2` typically requires most of the
oracle's full greedy order, so a budget capped at 27-45% of the oracle's own
size (the recall ceiling's direct consequence) usually lands well short of
the coverage threshold, regardless of which specific birds fill that
smaller budget. Stage 6.5's own seed 20 (inferred 3/13 = 23% of oracle's
budget, `P=0.30`) looks, in light of this 12-flock benchmark, like a
favorable draw rather than a representative one.

## B6 — flock-level, not replicate-level, evidence

Per B6's explicit instruction, the headline claim above is a flock-level
statistic (12 flocks, bootstrap-resampled), not an appeal to the underlying
600 replicate simulations (50 x 12) as independent evidence. The
distribution of `Delta_s^{(f)}` across the 12 flocks is heavily concentrated
at or near zero (11 of 12 flocks within `[-0.02, +0.02]`), with the sole
outlier being seed 71's `-0.08` (random beating inferred) — see Figure
R6.5-2's paired flock-level panel.

## B7 — inference quality vs. control (exploratory)

None of the four candidate predictors correlate meaningfully with
`P_{\hat B}(\text{success})` across these 12 flocks (Spearman, `n=12`):
recall `r=0.13, p=0.68`; excess loss `r=-0.39, p=0.21` (weak, in the
expected direction, but not significant at this sample size); boundary size
`r=0.14, p=0.67`; actuator budget `r=-0.05, p=0.89`. With `P_success` itself
sitting at ~0 on 11 of 12 flocks, there is very little outcome variance
for any predictor to explain — this null result is a direct consequence of
the headline finding, not an independent puzzle.

## HARD GATE B verdict

**Does observationally inferred interface control outperform null
intervention across a nontrivial set of flocks where the task is neither
trivially easy nor impossible? On this evidence, no.** The discriminating
criterion worked exactly as intended — it produced 12 flocks where the
oracle clearly succeeds and a matched-budget random draw clearly fails, a
nontrivial and non-degenerate benchmark — but the inferred controller,
using the frozen Part 1 inference pipeline and the frozen V3 multicover
law unmodified, fails almost uniformly on it. The single earlier
discriminating success (held-out seed 20) does not generalize: on this
12-flock benchmark, inferred-boundary control is statistically
indistinguishable from a matched-budget random draw. This is a materially
different, and more sobering, conclusion than Stage 6.5's original
"partial, informative" framing based on one discriminating flock — Part D's
synthesis should carry this forward plainly, and Part E's visualization
should not present an aggregate "inferred beats random" claim (E9's
admission criterion: integrate only if the comparison is genuinely
informative — it is informative here, but the informative finding is
negative).
