# COLLECTIVE_IDENTITY_RESULTS.md

Scope (see `../PLAN.md`): representation-comparison table (Part 4) on dev
flocks 2, 3, 4 (`data/identity_evaluation.json`, N_REP=8 controlled-episode
replicates per flock, frozen V3 multicover controller `q=2, gamma=0.5`
forcing the true `B^D_0`, unmodified); closed-loop adaptive-control
proof-of-concept (Part 5, `data/adaptive_control.json`) on flocks 2, 3;
pathwise boundary integrity (Part 6, `data/pathwise_boundary.json`) on the
canonical flock's three Part-5 episodes. All three identity definitions
(`code/definitions.py`) are fixed by construction (`TW=5`,
`MIN_CONTINUITY=0.3`, `MIN_SELF_COHERENCE=0.6`) — chosen for interpretability
before any of this data was generated, not tuned to these results (Part
3.4's "do not optimize them to coincide" applies equally to not tuning
either one to look better).

## Part 4 — does representation change the assessment of the SAME trajectories?

**Yes, sharply, and in the direction Part 4.1 warned about.** Aggregated
over N_REP=8 controlled episodes per flock:

| flock | rep | P(success) | P(persistence) | final `R_0` | final `Q_recruit` | total membership turnover | `H^\star`(retained) at end |
|---|---|---|---|---|---|---|---|
| 2 | M | 1.00 | 1.00 | 1.00 | 0.00 | 0.0 | 1.00 |
| 2 | L | 1.00 | 1.00 | 0.41 | 0.49 | 173.4 | 1.00 |
| 2 | F | 1.00 | 1.00 | **0.06** | 0.00 | 21.0 | 1.00 |
| 3 | M | 1.00 | 1.00 | 1.00 | 0.00 | 0.0 | 1.00 |
| 3 | L | 1.00 | 1.00 | 0.39 | 0.48 | 78.0 | 1.00 |
| 3 | F | 1.00 | 1.00 | 0.14 | 0.02 | 23.9 | 1.00 |
| 4 | M | 0.12 | 0.25 | 1.00 | 0.00 | 0.0 | 0.34 |
| 4 | L | 0.12 | 0.38 | 0.53 | 0.40 | 132.4 | 0.32 |
| 4 | F | **0.00** | 0.25 | 0.42 | 0.05 | 35.9 | 0.13 |

On flocks 2 and 3, all three representations agree on the headline verdict
(success=yes), but disagree enormously on what that verdict describes: `I^M`
by definition never changes; `I^L` retains under half its original members
by the end (`R_0\approx0.4`) while recruiting an almost-equal-sized cohort
from outside `I_0`; `I^F` on flock 2 retains **6%** of the original members
(`R_0=0.06`) — its "success" is a claim about a nearly-different set of
birds. On flock 4 (the harder flock, matching V3's own frozen record of
`p_success=0.05` for this exact `q=2,gamma=0.5` criterion,
`v3_refinement/data/minimal_interface.json`), `I^M` and `I^F` **disagree on
the headline verdict itself** (0.12 vs 0.00) — the same physical trajectory
is labeled a (rare) success under one description and never a success under
the other. Reporting these disagreements, not resolving them toward a
single "correct" verdict, is the point of Part 4.

## Part 4.1 — identity gaming

**`H^\star`(retained) never drops below `H^\star`(full) in this data** — i.e.
the specific gaming pattern the brief names ("drop resistant birds, recruit
already-aligned ones, so the *retained* core is worse off than the reported
aggregate suggests") does **not** show up as a retained/recruited *heading*
gap here. What DOES show up, and is arguably a more severe version of the
same underlying concern, is **gaming through collapse**: `I^F` on flock 2
did not fail to preserve the original collective by recruiting substitutes
so much as by **shrinking towards a tiny remnant** (see Part 5 below,
`mean_final_size=1.1` under closed-loop control) whose heading is then
trivially easy to call "at target". A retained-member fraction of 0.06 or a
final size near 1 makes "the original collective succeeded" a
close-to-vacuous claim regardless of what `H^\star`(retained) numerically
reads — **`n_retained`, not just `H^\star`(retained), must always be
reported alongside it**, which is why every table above and in
`data/identity_evaluation.json` carries `n_retained` next to the heading
fractions.

## Part 4.2 — boundary under adaptive identity

`B_t^{D,L}` and `B_t^{D,F}` (the TRUE lattice-neighbor shell of the
representation's own `I_t`, ground-truth use only) visibly change size and
membership across `t` even though the physical lattice itself never moves
— see Figure 6.5E. This is the "limited but useful test of moving
functional membership before Stage 7" the brief anticipates: **the physical
interaction graph is static throughout; only the representation-relative
boundary moves**, and it moves a lot (Part 5/6 below quantify how much).

## Part 5 — closed-loop identity-adaptive control (proof of concept)

Scope decision (see `code/adaptive_control.py`'s module docstring): actuator
selection uses the TRUE relative shell `B_t^{D,r}` and the frozen V3
multicover rule, not a re-inferred `\hat G` — isolating the identity
question from the inference-error question already covered in Part 1-2.
N_REP=8 replicates, flocks 2 and 3:

| flock | rep | P(success) | P(success, retained-only) | mean `\|A_t\|` | mean final retention | mean membership turnover | mean actuator turnover |
|---|---|---|---|---|---|---|---|
| 2 | M | 1.00 | 1.00 | 12.0 | 1.00 | 0.0 | 0.0 |
| 2 | L | 1.00 | 0.875 | 10.5 | 0.44 | 163.0 | 129.4 |
| 2 | F | 1.00 | 1.00 | 7.0 | **0.056** | 18.9 | 43.8 |
| 3 | M | 1.00 | 1.00 | 7.0 | 1.00 | 0.0 | 0.0 |
| 3 | L | 1.00 | 1.00 | 6.5 | 0.43 | 82.5 | 55.0 |
| 3 | F | 1.00 | 1.00 | 4.3 | 0.13 | 23.3 | 32.6 |

**Yes, a changing collective definition changes both the intervention
interface and the control policy**, sharply: `I^L`/`I^F` use FEWER mean
actuators than the fixed-material controller (7.0-10.5 vs. 12.0 on flock 2;
4.3-6.5 vs. 7.0 on flock 3) while reaching the SAME nominal success rate —
but this is not "the adaptive controller found a more efficient interface
for the same job." Mean final collective size under `I^F` on flock 2 was
**1.125 birds** (`data/adaptive_control.json`, `mean_final_size`) — i.e. on
average the "functional collective" being declared successfully steered
had shrunk to close to a single bird by the end of the control window. The
smaller actuator budget is a direct consequence of needing to move a
much smaller (self-selected, already-more-alignable) group, not evidence of
a more efficient control law. `I^L` shows the complementary failure mode:
retention 0.44/0.43 with membership turnover in the hundreds over a
40-step episode (up to ~4 members changing per step on average) — most of
the "successfully steered collective" by the end is not the group Stage 6
set out to steer.

**Part 5.4's question, answered plainly**: on this evidence, adaptive
identity does make the task LOOK easier (fewer actuators, same or higher
nominal success), but almost entirely by changing what counts as "the
collective" rather than by controlling the original one more efficiently.
`P(success, retained-only)` stayed at or near `P(success, full)` in 5 of 6
adaptive rows here (the flock-2 `I^L` row is the one exception, 0.875 vs
1.00) — so in this limited proof-of-concept, the retained-original-members
bar was usually still cleared, but the actuator-count and retention numbers
above show the adaptive controllers were doing a measurably different job,
not a strictly easier version of the same one.

## Part 6 — pathwise boundary integrity

Canonical flock (seed 2), the same three Part-5 episodes, one-step leakage
diagnostic (`code/pathwise_boundary.py`, Stage 6's own H1/H2 Monte-Carlo
corruption method reused across time, 25 honest + 25 corrupted one-step
branches per checkpoint, 11 checkpoints every 4 steps across the 40-step
episode):

| rep | mean leakage (nats) | max leakage | steps above 0.02-nat tolerance | boundary size range |
|---|---|---|---|---|
| M | 0.0138 | 0.0738 | 2/11 | 12 (constant) |
| L | 0.0143 | 0.0337 | 4/11 | 12 -> 28, fluctuating |
| F | 0.0118 | 0.0752 | 2/11 | 12 -> 4, monotonically shrinking |

**The collective stays approximately screened by its own (representation-
relative) boundary throughout, regardless of which definition is used and
regardless of how much that boundary's size or membership is changing.**
Mean leakage is close (0.012-0.014 nats) across all three representations
despite wildly different boundary dynamics — `I^F`'s boundary shrinks from
12 to 4 members and its mean leakage is if anything the *lowest* of the
three, not the highest. This is a genuinely informative negative-ish
result: a shrinking, unstable definition of "the collective" does not, on
this evidence, make it harder to find *some* compact interface that
screens it well at each instant — it is the size and membership of that
interface, not its existence, that becomes unstable. `I^L`'s boundary is
the most erratic (12 to 28 members and back, `boundary_turnover` up to 23
in a single 4-step gap) and also has the most checkpoints above tolerance
(4/11), consistent with the interior-turnover picture above.

## Summary

| Question | Answer |
|---|---|
| Do fixed, lineage, and functional identity give the same verdict on the same trajectory? | Usually the same headline verdict on easy flocks, but built on very different underlying membership (`R_0` from 1.00 down to 0.06); they DISAGREE on the headline verdict itself on a harder flock |
| Identity gaming? | Not via a retained/recruited heading gap in this data; instead via **collapse** — the functional definition shrinking the "collective" toward a near-trivial remnant while still registering nominal success |
| Does changing the definition change the controller? | Yes — smaller actuator budgets under adaptive identity, but driven by controlling a smaller/different group, not a more efficient interface for the original one |
| Does a compact predictive interface survive representation change? | Yes — pathwise leakage stays low (~0.01-0.014 nats) under all three definitions even as boundary size and membership change dramatically |
