# Stage 6.10 — Orientation summary

Companion to `RESULTS_6_10.md`, for reading without having followed the run.
The results file carries the numbers and their caveats; this one says what the
stage was for, what it actually established, and what it did not.

---

## 1. The question

> Can an emergent, operationally thing-like collective be detected online,
> tracked while both its membership and its causal interface change, and
> adaptively redirected through that interface — while remaining the same
> valid lineage?

Four things have to hold at once, and the stage is built so each can fail
separately: **detect** (blind, task-neutral), **track** (through membership and
interface turnover), **steer** (through the inferred interface), **stay itself**
(the thing you redirected is still the thing you detected).

---

## 2. The one-paragraph answer

**Yes, within a stratum, and the honest version has three qualifications.** At
equal actuator spend, controllers acting through an *online-inferred* causal
interface steer the collective about as well as a benchmark with the full model
that explicitly optimizes the objective — the difference is a third of a
standard error. Blind predictive actuation and no control are clearly worse. The
redirected collective usually stays redirected after control is removed. But the
comparison holds only on the 7 of 12 episodes where full-model control works at
all, n = 7 cannot rank the leading arms against each other, and the most
interesting separation between methods is not in the heading at all — it is in
whether the collective survives being steered.

---

## 3. What was established, in dependency order

| Part | Question it settles | Outcome |
|---|---|---|
| **A** | Why did Stage 6.8's full-information arm lose? | Three separate causes; the ordering itself was never significant |
| **B** | Do the structural and interventional interfaces agree? | Exactly — 25 vs 25 sources, gate passed |
| **G** | Which physical regime is even alive? | β = 0.4, s = 0.75. The Stage 6.8 point is **policy-locked** |
| **E/J** | What do untouched collectives do? | Reference landscape + calibrated identity envelope |
| **H** | Is the task controllable *before* testing inference? | Yes at fraction 0.5, T = 24, on 7 of 12 episodes |
| **I** | Do inference-based controllers match full model knowledge? | At equal spend, yes — indistinguishable |
| **K** | Steered, or merely pushed? | 12 of 18 hold after release; depends on episode, not arm |
| **L** | One illustration | Seed 7, median success, never used for claims |

### Three results worth knowing on their own

**The Stage 6.8 operating point could not have worked.** 91% of birds sit at
`max(u_t) > 0.999` — saturated policies. They are not choosing, so nothing
acting through their choices can steer them. This came out of *uncontrolled*
data and independently explains why Stage 6.8's control comparison was noise.

**More actuators made control worse.** Forcing 75% of the interface scores below
forcing 50%. Saturating the interface deforms the collective rather than
steering it harder — a property of the benchmark, found before any inference.

**Methods separate on identity, not heading.** At identical spend, random
actuation holds identity on 0.57 of episodes versus 0.86 for causally-selected
actuation, failing mostly by `shrink-to-win`. Both move the heading; only one
leaves the collective intact. A heading-only score sees none of this.

---

## 4. What is deliberately *not* claimed

- **No ranking among the top three arms.** The full-info heuristic's apparent
  lead over the benchmark is noise at n = 7.
- **No regime-wide control claim.** Everything is scoped to the stratum where
  full-model control itself succeeds; 5 of 12 episodes are excluded and the
  count travels with every claim.
- **Absolute success rates are optimistic.** The stratum was selected by
  thresholding a noisy estimate, so it regresses on replication (the benchmark
  meets the task on 4 of 7 in Part I, not 7 of 7). Paired comparisons are
  unaffected.
- **The full-info heuristic is never called an oracle**, and the benchmark is
  never called an optimum — beam search, not exhaustive.
- **"Ground truth" is never claimed for the detected interior.**

---

## 5. Why so much of this file is about instruments

Five defects were found by testing instruments before trusting them. Each was
caught by an internal inconsistency, and each would have changed a headline.

| # | Defect | Would have caused | Caught by |
|---|---|---|---|
| 1 | Benchmark planned a one-shot intervention but executed a held one | Excluding steerable episodes from the gate | Reading the rollout against `sim.step` |
| 2 | Identity envelope calibrated per-axis (5% × 6) instead of jointly | `no_control` scored identity-**invalid** | Testing the scorer on the uncontrolled arm |
| 3 | Certified predictive boundary mostly empty | Predictive arm a silent clone of `no_control` | Arm produced zero actuators |
| 4 | Gate tracked the **largest** candidate; Part I steers the **qualifying** one | Comparing on episodes selected for a different object | Benchmark met task on 4/7 of episodes admitted for ≥ 0.60 |
| 5 | `_rank_by_influence` written against a matrix, given a dict | Crashed all 14 workers on arm 2, ~5h lost | The crash — no smoke test after patching |
| 6 | Reimplemented gate drifted from Part I in pool/rollouts/seed simultaneously | Same class of defect as #4, recurring | Second concurrent session's own equivalence test |
| 7 | Gate delegation initially shared Part I's random stream | Stratum success = 1.0 by construction, biasing every arm comparison in the benchmark's favour | Reading the delegating gate's own docstring |

Defect 4 is the instructive one. The gate and the comparison each looked
internally fine; only their *disagreement about the benchmark* revealed that
they were measuring different collectives. Defect 5 is the cautionary one: it was
mine, introduced by patching code while a run was in flight and relaunching
without re-testing.

Two controllability scans were superseded (defects 1 and 4) and one full Part I
run discarded. All superseded artifacts are retained under `SUPERSEDED_*` names
and `data/superseded_partI/`, used for nothing. **The selection rules predate all
three scans and were never modified** — the pre-registration in
`logs/task_selection_predeclared.txt` and
`logs/regime_selection_predeclared.txt` is what makes the re-runs safe rather
than convenient.

### The pre-registration doing real work

- The **most responsive regime cell** in the scan (χ = 0.048, the one that would
  have made control look best) was **rejected** for lineage incoherence
  (Jaccard 0.59 < 0.60). No threshold was moved to admit it.
- The frozen task is the **smallest-resource** cell clearing reliability, not the
  most generous — a more generous cell would have flattered every arm.
- Thingness and identity thresholds were frozen on **uncontrolled data only**;
  control success is not computable in the module that sets them.

---

## 6. An incident that cost real time

An orphaned shell from an earlier session stayed alive ~9.5 hours, unblocked
from a stale wait loop, and replayed old archive-and-relaunch commands: it moved
Part I's data aside, started six rogue jobs, and appended the Part I section to
`RESULTS_6_10.md` about nineteen times, stripping its headers. All processes
were killed, every data file restored and verified against the frozen stratum,
and the results file was **rebuilt from the data rather than repaired**. The
corrupted copy is kept at `logs/RESULTS_6_10.CORRUPTED.bak`. No measurement was
lost; `data/` was the source of truth throughout, which is the reason recovery
was possible.

---

## 7. State of the work

**Complete:** Parts A–L, six figures, 27 tests passing, all pre-registrations and
addenda logged.

**Known gaps, none blocking the conclusions:**

1. **Part E percentile ranks are not materialized.** The (C, G, L, D) landscape
   and `thingness.percentile_ranks` both exist, but per-candidate ranks are not
   written into `uncontrolled_reference__main.json`. Note that **L is degenerate**
   (87% of candidates at ≤ 0.001), so ranks on that axis would carry no
   information regardless.
2. **No Stage 6.10 demo bundle.** The Part L clarity trajectory is selected and
   recorded but not exported to `interactive_demo/`.
3. **Stage 6.11 (translating torus, sections M–V) is not started.** It was gated
   on Stage 6.10 establishing the complete fixed-lattice loop, which has now
   happened.

**Reading order for someone new:** this file → `RESULTS_6_10.md` Parts A, G, I →
`figures/fig_6_10_5_arms.png` (the two budget conventions side by side) →
`PROTOCOL_6_10.md` for frozen thresholds and their provenance.
