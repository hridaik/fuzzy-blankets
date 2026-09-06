# CAUSAL_REDUNDANCY_RESULTS.md — HARD GATE A

Frozen protocol: `../PROTOCOL_6_5R.md` (Part A section) /
`../configs/protocol_6_5r.yaml` (`part_a_causal_redundancy` block), hash
`../logs/protocol_6_5r_part_a.sha256`. All numbers below are read directly
from `data/causal_redundancy.json`; none are hand-adjusted. Figure: `figures/
fig_r6_5_1_causal_redundancy.png` (R6.5-1).

## Method validation, before any headline number

`exact_intervention.py` computes `D_j^do` and the stress-tested
`Delta-ell`/`Delta_shift` in **closed form** (see its module docstring and
`../PLAN.md`), not by Monte Carlo. Two things were checked before trusting
this:

1. **The negative control is exact, not just small.** For every bird in the
   `E^D` sample (10 birds x 3 flocks x 3 headings x 30 states = 900 triples
   per flock), `D_j^do` is **exactly `0.0`** — not "close to zero," bit-for-bit
   equal to the undisturbed distribution (`tests/test_exact_zero_effect.py`).
   This follows from the computational graph (a non-neighbour bird cannot
   enter any interior bird's policy computation), and it means the negative
   control in Part A is a proof, not an estimate.
2. **The closed form matches literal simulator rollouts.** 2000-replicate
   Monte-Carlo rollouts of the real simulator (natural and do-intervened)
   agree with the closed-form distribution within 0.06 total-variation
   tolerance on every tested bird/heading (`tests/
   test_closed_form_matches_rollout.py`, both pass). A4/A5's "if the
   exact/MC distributions make KL stable" condition is satisfied by
   exactness, not approximation.

## Does independently perturbing an omitted true-shell bird change the interior's one-step distribution?

**Yes, on all three held-out flocks — but with a strongly right-skewed
distribution, not a uniform one.** Pooled `D_j^do` (KL of the true joint
interior next-state distribution, `n` = birds x states x alternative
headings):

| seed | class | n | mean | median | p90 | max |
|---|---|---|---|---|---|---|
| 17 | included shell (`\hat B`) | 450 | 0.386 | 0.221 | 1.161 | 3.776 |
| 17 | **omitted shell** (`B^D\setminus\hat B`) | 1170 | **0.066** | 0.00004 | 0.214 | **2.099** |
| 17 | non-shell (`E^D` sample) | 900 | **0.000** | 0.000 | 0.000 | 0.000 |
| 18 | included shell | 360 | 0.420 | 0.275 | 1.136 | 1.826 |
| 18 | **omitted shell** | 990 | **0.143** | 0.00009 | 0.486 | **3.784** |
| 18 | non-shell | 900 | **0.000** | 0.000 | 0.000 | 0.000 |
| 20 | included shell | 450 | 0.792 | 0.575 | 2.121 | 3.838 |
| 20 | **omitted shell** | 720 | **0.441** | 0.175 | 1.161 | **2.428** |
| 20 | non-shell | 900 | **0.000** | 0.000 | 0.000 | 0.000 |

Three things are worth separating:

- **The negative control is exactly zero on every one of 2700 non-shell
  triples**, on every flock. This is the expected result under the
  computational graph, confirmed to floating-point equality.
- **Omitted-shell birds have real, sometimes large, causal effects.** On
  seed 20, the omitted-shell mean (0.441 nats) is more than half the
  included-shell mean (0.792) — the same order of magnitude, not a
  rounding-error tail. On all three flocks the omitted-shell class's maximum
  single-triple effect (2.1-3.8 nats) is comparable to the included-shell
  class's maximum. **This directly answers Part A's central question: the
  omitted true-shell variables are not, in general, causally unimportant.**
- **But most individual (bird, state, heading) triples have a near-zero
  effect.** The omitted-shell median is 3-4 orders of magnitude below its
  mean on seeds 17/18 (0.00004-0.00009 vs. 0.066-0.143) — a small number of
  triples carry most of the mass (matching the `p90`/`max` columns). Seed
  20 is the exception: its omitted-shell median (0.175) is much closer to
  its mean, i.e. the effect is more uniformly spread across triples on this
  flock.

**Which omitted-shell birds matter most, and why (Outcome C's follow-up,
scoped lightly per A6's instruction not to launch a model-selection
project)**: the natural first guess — that a bird's raw multiplicity
(number of lattice edges into `I0`) predicts its causal importance — **does
not hold in this data**. Spearman correlation between per-bird mean
`D_j^do` and multiplicity into `I0`, pooled across all 32 omitted-shell
birds across the three flocks: `r = 0.013`, `p = 0.94` — indistinguishable
from no relationship. Concretely, on seed 17, birds 78/79/87/97 (multiplicity
2 into `I0`) have mean effect ~0.00004, while bird 92 (also multiplicity 2)
has mean effect 0.166 — multiplicity alone does not distinguish them. Which
*specific* `I0` bird(s) a shell member neighbours, not how many, appears to
matter more, but characterizing that fully would be the "large new
model-selection project" A6 explicitly says not to launch here; it is
flagged as a natural next question, not resolved.

## Does the observational boundary (`\hat B`) remain predictively sufficient under distribution shift?

**Mostly, with a small, reproducible, direction-consistent tax that is an
order of magnitude smaller than the causal effects above.** Recall from
Stage 6.5 Part 1 that `Delta-ell(\hat B) approx Delta-ell(B^D) approx 0` under
natural trajectories. Re-measuring both quantities exactly (closed-form
cross-entropy, this refinement's own operationalization — see
`../PROTOCOL_6_5R.md`) on the same 30-checkpoint set used for the
perturbation experiment:

| seed | natural `Delta-ell(\hat B)` | mean `Delta_shift(\hat B)` [included] | mean `Delta_shift(\hat B)` [**omitted**] | mean `Delta_shift(\hat B)` [non-shell] |
|---|---|---|---|---|
| 17 | -0.00583 | +0.00100 | **-0.00011** | -0.00048 |
| 18 | +0.00019 | -0.00077 | **+0.00150** | -0.00044 |
| 20 | -0.00408 | -0.00034 | **+0.00493** | -0.00027 |

- On seeds 18 and 20, the largest (most positive, i.e. most damaging)
  `Delta_shift(\hat B)` across the three classes is specifically the
  **omitted-shell** class — the theoretically expected direction (Part A5's
  question), and on seed 20 it is large enough (+0.00493) to flip
  `\hat B`'s natural slight *advantage* over the full-exterior model
  (-0.00408) into a modest net *disadvantage* (~+0.00085) once an omitted
  shell bird is deliberately decorrelated from its natural correlates.
- On seed 17, the pattern does not hold — the omitted-shell shift is
  slightly negative (no degradation), and the *included*-shell class shows
  the (still tiny) largest shift instead. This flock does not confirm the
  expected direction.
- In absolute terms, even the largest observed shift (seed 20, +0.0049 nats)
  is roughly **two orders of magnitude smaller** than the largest observed
  `D_j^do` causal effects (2-4 nats) on the same birds, and small relative to
  the flocks' own baseline loss scale (0.07-0.11 nats). The predictive
  boundary bends under this stress test; it does not break.

## Does the oracle shell (`B^D`) remain robust?

**Yes, clearly — its own excess-loss shift stays flat and small across every
class and every flock** (`B_D` column of `delta_shift_by_class` in `data/
causal_redundancy.json`): means range from -0.00123 to +0.00038 across all
nine (flock x class) combinations, with no directional pattern by class.
This is the expected contrast with `\hat B`: `B^D` already conditions on
every true shell member, so decorrelating one of them from its natural
correlates does not create a blind spot the way it does for `\hat B`'s
missing 42-82% of `B^D`.

## Are observational redundancy and causal redundancy distinguishable in this model?

**Yes — and the distinction is much sharper in the direct causal-effect
metric (`D_j^do`) than in its downstream predictive-loss consequence
(`Delta_shift`).** Omitted-shell birds were observationally redundant under
natural trajectories (Stage 6.5 Part 1: `\hat B`'s excess loss matched
`B^D`'s to within ~0.01 nats). Under independent perturbation, those same
birds have real, and on seed 20 substantial, causal effects on the true
interior one-step distribution — sometimes comparable in size to included-shell
members' effects. **This is Outcome A's headline distinction
(`observationally redundant != causally redundant`) at the level of the
direct interventional-effect metric.** At the level of the practical
predictive-sufficiency question (does `\hat B`'s own modeling gap versus the
full exterior widen under intervention), the answer is closer to **Outcome
B/C mixed**: a real but modest, and only partially flock-consistent, tax —
not the dramatic breakdown Outcome A's strongest form would predict, but not
"no clear distinction" (Outcome D) either. Per A6/G's stopping rule, this
mixed result is reported as found, not tuned toward either extreme.

## Summary

| Question | Answer |
|---|---|
| Do omitted true-shell states have measurable intervention effects? | Yes, on all 3 flocks — real, sometimes large (up to 2-4 nats per triple, comparable to included-shell effects), but concentrated in a minority of (bird, state, heading) triples on 2 of 3 flocks |
| Does the observational boundary remain sufficient under distribution shift? | Mostly — a small (<0.005 nat), reproducible tax appears specifically for omitted-shell perturbations on 2 of 3 flocks, large enough to flip `\hat B`'s natural slight advantage to a modest disadvantage on the clearest flock (seed 20), but roughly 100x smaller than the underlying causal effects |
| Does the oracle shell remain robust? | Yes — `Delta_shift(B^D)` stays flat and small (within ±0.0013 nats) across every class and flock |
| Are observational and causal redundancy distinguishable here? | Yes, clearly at the `D_j^do` level (Outcome A's distinction); more mutedly at the predictive-consequence level (`Delta_shift`, Outcome B/C mixed) |

**This is a genuinely mixed result, reported as found**: Stage 6.5's
inferred boundary is not "secretly" recovering the true causal interface —
omitted shell members do move the true dynamics, sometimes substantially —
but its practical predictive cost for doing so is small under the specific
stress test applied here. Proceeding to Part B (control generalization) is
warranted; Part D's synthesis should carry forward the `B^D != \hat B` and
`\hat B` (usually) `approx` `B^C` distinction this gate establishes, not
collapse it into either "the boundary was always causal" or "the boundary
is meaningless."
