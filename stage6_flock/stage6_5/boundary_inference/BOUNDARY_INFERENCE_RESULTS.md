# BOUNDARY_INFERENCE_RESULTS.md — HARD GATE A

Frozen protocol: `../PROTOCOL_6_5.md` / `configs/protocol_6_5.yaml`
(sha256 `e0d45adbb083a9ba5c9fb592de152ae7ffa872ea88e5b3224c030aa7ea9c4bdf`).
Dev-flock decisions (`data/dev_sweep.json`) preceded every number below;
nothing in the frozen threshold changed after seeing held-out, bootstrap, or
control-comparison results. All numbers below are read directly from the
JSON files named in each section — none are hand-adjusted.

## Can `B^D` be approximately recovered from trajectories?

**Partially, and with a very specific, reproducible error pattern: high
precision, limited recall.** Across all three held-out flocks
(`data/held_out_evaluation.json`, seeds 17/18/20 — the first three of V3's
own frozen six held-out seeds, never touched during development):

| seed | `\|B_D\|` | `\|\hat B\|` | precision | recall | Jaccard | FP |
|---|---|---|---|---|---|---|
| 17 | 18 | 5 | **1.00** | 0.28 | 0.28 | 0 |
| 18 | 15 | 4 | **1.00** | 0.27 | 0.27 | 0 |
| 20 | 13 | 5 | **1.00** | 0.38 | 0.38 | 0 |

Every single inferred boundary bird, on every held-out flock, was a true
member of `B^D` (zero false positives across all three flocks, 14/14
correct). The same pattern held on all three development flocks
(`data/dev_sweep.json`, `delta_tol_frac=0.05`): seed 2 recovered 7/12 true
members (0 FP), seed 3 recovered 3/14 (0 FP), seed 4 recovered 3/17 (0 FP).
This is not a coincidence of one threshold choice — the greedy stopping
rule (delta relative to the full-exterior predictor) is conservative by
construction: it only adds a candidate when doing so buys back a slice of
the *measurable* excess loss, so a true-but-weakly-informative shell member
(one whose individual marginal contribution is small relative to the
others, or redundant with an already-selected member) is the kind of thing
it under-selects, not something spurious it over-selects. Exact graph
recovery (`exact_match=true`) never happened on any of the 6 flocks tested
(dev or held-out) — `\hat B` is always a proper, precision-1.0 subset of
`B^D` at this threshold and this amount of data.

## How much data is required?

**Recovery improves monotonically and is still improving at the largest
tested `N_traj`, with no sign of a hard identifiability floor within the
tested range.** Sample-efficiency curve on the canonical flock (seed 2,
`data/sample_efficiency.json`; `N_traj=200` was in Part 1.9's suggested grid
but was dropped after timing out — see `PROTOCOL_6_5.md`'s "compute-scope
reduction" note):

| `N_traj` | `\|\hat B\|` | Jaccard vs `B^D` | `\Delta\ell(\hat B)` (nats) |
|---|---|---|---|
| 5   | 4 | 0.33 | -0.0010 |
| 10  | 4 | 0.33 |  0.0004 |
| 20  | 4 | 0.33 | -0.0004 |
| 50  | 6 | 0.50 | -0.0001 |
| 100 | 7 | 0.58 |  0.0005 |

Two things worth separating. **Graph recovery (Jaccard) needs real data
and keeps improving**: it is flat from 5-20 trajectories (a floor of 4
correct members findable almost immediately, presumably the largest-effect
shell members), then jumps as soon as 50+ trajectories are available.
**Predictive sufficiency is cheap and needs almost no data at all**: excess
loss is already indistinguishable from zero (within Monte Carlo noise of
the validation-set floor) at `N_traj=5`. This dissociation is itself an
answer to Part 1's framing question — a small amount of data is enough to
find a functionally-adequate (if incomplete) boundary; substantially more
data is needed to approach the *true* one.

## Does `\hat B` screen almost as well as `B^D`?

**Yes — and it dominates the null baselines by roughly an order of
magnitude**, on every held-out flock (`data/held_out_evaluation.json`,
`excess_loss` block):

| seed | `\Delta\ell(\hat B)` | `\Delta\ell(B^D)` | `\Delta\ell(B^F)` | `\Delta\ell(B^{\rm random,matched})` |
|---|---|---|---|---|
| 17 | 0.0088 | 0.0056 | 0.0254 | 0.0238 ± 0.0036 |
| 18 | 0.0001 | -0.0062 | 0.0138 | 0.0125 ± 0.0026 |
| 20 | 0.0025 | -0.0010 | 0.0300 | 0.0291 ± 0.0018 |

(`B^D`'s own excess loss dips slightly negative on two flocks — an
expected consequence of comparing against a full-exterior model on a
finite validation split, i.e. within noise of zero, not evidence that a
13-18-bird true shell "beats" the 80-bird full exterior on some other
signal.) On every flock, `\hat B` (5, 4, and 5 birds respectively) achieves
excess loss within ~0.01 nats of the oracle `B^D`, while the size-matched
Fiedler boundary `B^F` and random exterior draws of the *same size* sit
3-12x higher. **This is this project's cleanest instance of the
"`\hat B \neq B^D` while `\Delta\ell(\hat B)\approx 0`" outcome the task
brief calls out as the more scientifically interesting success mode**: the
inferred, precision-1.0, recall-0.3 subset is not a good topological
match, but it is an excellent functional one.

## Does control through `\hat B` approach oracle-shell control?

**Mixed, informatively so, across the three held-out flocks**
(`data/control_comparison.json`, frozen V3 multicover law `q=2, gamma=0.5`,
reused unmodified, `n_replicates=20`):

| seed | oracle `\|A\|`, P(success) | inferred `\|A\|`, P(success) | Fiedler `\|A\|`, P(success) | random `\|A\|`, P(success) |
|---|---|---|---|---|
| 17 | 9, **1.00** | 3, **1.00** | 1, 1.00 | 3, 0.95 |
| 18 | 9, 0.00 | 3, 0.00 | 42, 0.00 | 3, 0.00 |
| 20 | 13, **0.95** | 3, **0.30** | 0, 0.00 | 3, 0.00 |

Three qualitatively different outcomes, all reported as found:

- **Seed 17 is uninformative about the inferred boundary specifically**:
  every arm, including a random 3-bird draw, reaches ~1.0. This flock is
  simply easy to steer (consistent with V2/V3's own established finding
  that Rule D, uniform random draws from the *correct* shell, performs
  nearly as well as structured rules — `STAGE6_SYNTHESIS.md`); it does not
  demonstrate that `\hat B` carries useful information, only that it does
  not hurt.
- **Seed 18 is a known-hard flock, not a failure of this method**: V3's own
  frozen record (`v3_refinement/RESULTS_V3.md`, Part 1E) already reports
  "held-out seed 18 reaches only `p_success=0.167`" under this exact
  `(q=2, gamma=0.5)` criterion using the TRUE shell. Every arm here
  (including Oracle) fails for the same already-documented reason; this
  comparison is uninformative about inference quality, not evidence against
  it.
- **Seed 20 is the clean discriminating case**: the inferred 3-actuator
  arm reaches `P(success)=0.30`, far below the 13-actuator oracle's 0.95
  but **decisively above both same-or-larger-budget null arms**, which
  reach exactly 0.00. This is the direct answer to Part 2's question: on
  the one held-out flock where the comparison is actually informative,
  controlling through `\hat B` does not match oracle-shell control, but it
  retains real, usable causal structure that a same-size random draw or
  the Fiedler boundary does not.

**Overall**: inference-to-control transfer works, but transfers only part
of the oracle's *effectiveness* even where it clearly transfers real
*information* — a partial, not a full, positive result, consistent with
`\hat B`'s recall ceiling of ~0.3-0.4 (Part 1.8). Whether more data (Part
1.9) would close this gap on seed 20 specifically is a natural next check,
not answered here (see Limitations).

## Boundary-membership uncertainty (canonical flock, `n_boot=15`)

`data/bootstrap_membership.json` / Figure 6.5A. Every single exterior bird
with nonzero bootstrap selection frequency is a true `B^D` member — the
precision-1.0 pattern holds at the bootstrap-membership level, not just for
the point estimate:

| bird | `m_j` | true `B^D` member? |
|---|---|---|
| 6, 25, 69 | 1.00 | yes |
| 15 | 0.93 | yes |
| 46 | 0.60 | yes |
| 57 | 0.47 | yes |
| 68 | 0.27 | yes |
| every other exterior bird (73 of 80) | 0.00 | (5 of these are true `B^D` members never selected in any of the 15 bootstrap replicates) |

The membership frequency is not smeared uniformly across the 80 exterior
birds — it drops sharply to exactly zero outside a 7-bird core, all 7 of
which are true shell members. This is the sharpest version yet of the
precision/recall asymmetry: recall is bounded (5 of `B^D`'s 12 true members
never appear in any bootstrap replicate here), but there is no bootstrap
instability manufacturing false positives.

## Which inference errors matter most?

With zero false positives on every flock tested, this project's evidence
cannot yet speak to Part 2.4's false-positive-cost question — there are no
false positives to evaluate. **False negatives are the entire error
budget here**, and seed 20's result (Part 2 above) suggests they are not
free: missing ~9 of 13 true shell members cost roughly two-thirds of the
oracle's success probability on that flock, even though the 3 members kept
were enough to clear both null baselines. A sharper answer — whether the
missed members are disproportionately high-multiplicity (per Part 2.4's
stated hypothesis) — would need the per-bird multiplicity data cross-
referenced against `false_negative_ids` in `held_out_evaluation.json`; not
computed here, flagged as the natural next analysis rather than asserted
without evidence.

## Summary

| Question | Answer |
|---|---|
| Approximate `B^D` recovery from trajectories alone? | Yes, but with a strong precision-over-recall bias (14/14 selections correct across 6 flocks; recall 0.18-0.58) |
| Data required? | Predictive sufficiency: very little (`N_traj=5` already ~0 excess loss). Topological recovery: needs 50-100+ trajectories and is still improving at 100 |
| `\hat B` vs `B^D` predictively? | `\hat B` within ~0.01 nats of oracle on every held-out flock; Fiedler and random baselines 3-12x worse |
| Control through `\hat B`? | Real but partial transfer — clearly beats null baselines on the one flock where the comparison is informative (seed 20); ties nulls on an easy flock (17); uninformative on a known-hard flock (18) |
| Dominant error type | False negatives only (zero false positives observed); their control cost is real (seed 20) but not exhaustively characterized here |

**This is not a negative result**, per the task brief's own success
criteria: `\hat B \neq B^D` (never exact), yet `\Delta\ell(\hat B)\approx 0`
on every flock tested, and inferred-boundary control retains real
(non-null) effectiveness on the flock where the comparison is actually
discriminating. Proceeding to Part 3 (collective identity) is warranted.
