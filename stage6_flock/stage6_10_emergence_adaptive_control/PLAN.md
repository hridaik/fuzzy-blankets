# PLAN.md — Stage 6.10: emergence → dynamic identity/interface → adaptive steering

Pre-registration, written **before any Stage 6.10 number was produced**. Follows
the Stage 6.5–6.9 convention: scope and thresholds are recorded up front so
`RESULTS_6_10.md` can be checked against stated intent rather than rationalized
afterwards. Additive throughout — nothing in Stages 6–6.9 is modified,
re-run, or reinterpreted.

## The question

> Can an emergent, visually/operationally thing-like collective be detected
> online, tracked while both its membership and its interface change, and
> adaptively redirected through its current causal interface while remaining
> the same valid lineage?

## Naming, fixed now and used everywhere

Stage 6.8 shipped an arm called `adaptive_oracle`. That name asserts more than
the arm earns: it selects actuators by a **task-agnostic** KL influence
criterion and is in no sense an optimum for the steering task. From here on:

| new name | what it is |
|---|---|
| **Full-info causal heuristic** | the old `adaptive_oracle` policy — exact influence, multicover selection |
| **Full-model control benchmark** | a NEW arm that explicitly optimizes the control objective with full state and exact dynamics |

The frozen Stage 6.8 arm keeps its recorded name `adaptive_oracle` **only**
when quoting frozen files verbatim. The word "oracle" is never used for a
controller that was not shown to be optimal.

## A. Audit the anomaly before running anything new

Stage 6.8 reported `adaptive_causal` (0.489) ≥ `adaptive_oracle` (0.411) on
8 episodes. Full information losing to inference is a red flag that must be
explained before it is built on.

The Stage 6.8 control episodes are replayed deterministically (the same replay
already verified to 1e-12 for the demo export) and instrumented to log, per
timestep per arm: detected interior, structural interface, exact effective
causal interface, sampled causal interface, actuators, actuator count,
per-actuator KL effect, per-actuator target-directed effect, predicted vs
realized one-step target gain, multi-step gain, and lineage metrics.

Six hypotheses, tested **separately**, each with a pre-stated discriminating
measurement:

| # | hypothesis | discriminating measurement |
|---|---|---|
| H1 | the full-information arm simply spends more actuators | mean \|A_t\| per arm; and a fixed-K re-run |
| H2 | it includes many weak causal channels | distribution of per-actuator KL within the selected set |
| H3 | KL influence is not aligned with target-directed influence | rank correlation between `C^do_{j→I}` and `A_j^{h*,τ}` |
| H4 | additive multicover misses synergy/antagonism | `S_jk = A_{jk} − A_j − A_k` over sampled pairs |
| H5 | one-step influence does not predict horizon-T effect | correlation of τ=1 authority with τ=4,8 authority |
| H6 | the episode-level ordering is mostly noise | paired per-episode differences under common random numbers |

Comparisons between actions use **common random numbers**. Frozen Stage 6.8
results are not altered; the audit writes only into this stage's `data/`.

## B. Independent truth/reference layer

Three modules, deliberately implemented independently:

1. **Structural truth** `B_t^struct(I)` — read from the simulator's transition
   dependencies (which sources enter which bird's update).
2. **Exact interventional truth** `B_{t,ε}^do` — computed *without* the
   structural graph, by perturbing every exterior source through all admissible
   headings and comparing exact next-state distributions.
3. **Task-directed authority** `A_j^{h*,τ}` — the expected change in target
   alignment at horizon τ under `do(u_j = h*)`, plus pair terms `S_jk` to
   quantify non-additivity.

(1) and (2) must agree; `tests/` cross-validates them and **the stage stops if
they disagree materially**. Large KL influence is never equated with positive
task authority — that equation is precisely what Part A suspects.

## C. Full-model control benchmark

A new primary reference controller with full current state, exact dynamics, the
current detected `I_t`, full structural/causal information, the same task,
the same actuator budget and the same identity constraints, which **explicitly
optimizes the expected control objective**. Exhaustive over actuator subsets
where the space allows; otherwise beam search / CEM with convergence checks
across search budgets and random seeds. It is called an *optimum* only where
exhaustive search actually established one.

## D. Detection stays blind and task-neutral

The Stage 6.8 affinity detector, unchanged in kind. At every step
`X_{0:t} → C_t` before control. The detector never sees the target heading,
future states, the true causal graph, the true interface, or which arm is
running. Lineages are tracked independently of the controller, membership may
change, and **the controller may not optimize membership**.

## E. Thingness profile (C, G, L, D)

For every sufficiently persistent candidate lineage: heading coherence `C`,
internal predictive integration `G`, challenger-certified residual leakage `L`,
local exterior heading-distribution contrast `D`. Percentile ranks are taken
against comparable connected candidates of similar size in the same
uncontrolled regime. A **thing-like stratum** is defined by jointly favourable
`C,G,L,D` with thresholds frozen on development/uncontrolled data only —
never on control success. All other candidates are retained for secondary
analysis.

## F. Clumpness as a separate morphology axis

`A = |I|`; cardinal-edge perimeter `P_4(I)` counting only shared grid edges,
with the physical lattice edge treated as exterior space; and

    Q_clump = P_min(A) / P_4(I).

Validated in `tests/` against compact blob (high), elongated strip
(intermediate), diagonal Moore snake (low), fragmented region (low). **Moore
adjacency is not used for perimeter.** Snake-like candidates are **not** deleted
from the landscape — they are scientifically interesting and are retained; a
separate **clear clump stratum** (thing-like ∧ high `Q_clump`) supplies the
primary visual and control examples.

## G. Operating-regime search, from uncontrolled data only

Looking for episodes with lineages that are persistent, non-global,
moderate-size, thing-like, clump-like, with real membership *and* boundary
turnover, and not policy-saturated. A standardized **weak directional probe**
gives a susceptibility curve `χ_τ`, used for regime characterization only.

The regime is **not** selected by maximizing later controller performance. The
target is a *robust-responsive window*: collective persists, a weak cue has a
measurable but non-saturating effect, lineage stays coherent, the interface
changes, and the policy posterior is not numerically locked. Regime and seeds
are frozen before any controller comparison.

## H. Controllability before inference

For every prospective primary episode the **full-model benchmark** must first
establish that the task is achievable. The task is a visually obvious adjacent
cardinal heading change `h_0 → h*` (90°). Only the control-resource variables
needed to pose a reasonable task are scanned: actuator fraction of the current
causal interface, and control horizon. The frozen operating task is one where
the benchmark succeeds **reliably but not trivially** — clearly positive, not
~0%, not ~100% under tiny forcing. Controller comparison does not run on
episodes where full-information control cannot steer the collective.

## I. The online closed loop

Per step `X_t → Î_t → B̂_t → u_t → X_{t+1}`, with **both** `I_t` and `B_t`
updated online. Seven arms: no control · predictive boundary · matched random ·
frozen initial sampled-causal · adaptive sampled-causal · full-info causal
heuristic · full-model control benchmark. Budgets are matched carefully; where
an arm chooses fewer actuators by policy, both outcome and effort are reported,
**and a fixed-K comparison is run so budget cannot explain the ordering**.

## J. Identity-valid outcome

Primary metric is target alignment of the **current tracked lineage**
`H*(I_t, t)`, with a frozen-`I_0` diagnostic retained for comparison. Full
success is

    S_target ∧ S_lineage ∧ S_nondegenerate

with the lineage inside a validity envelope learned from comparable
*uncontrolled* lineages (size range, stepwise continuity, turnover range,
clumpness, fragmentation). Material membership is **not** required to stay
fixed; shrink-to-win is not allowed.

## K. Release

After successful steering, control is removed and the tracked lineage is
measured for whether it maintains the new heading, stays thing-like, stays
clump-like, and continues to satisfy lineage validity. Emergence → identify →
steer → release.

## L. Primary visual trajectory

Aggregate statistics use **every qualifying held-out episode**. Separately, one
*clarity trajectory* is chosen for the demo from held-out episodes that already
pass the thing-like gate, high clumpness, obvious emergence, clear membership
and boundary turnover, benchmark success, adaptive sampled-causal success, an
obvious 90° turn, and an interpretable release. Choosing for visual clarity
*within that prequalified set* is allowed and is documented exactly. The
clarity trajectory is **never** used for aggregate claims.

## Hard interpretation rules (carried into every result statement)

- No method success is claimed where the full-model benchmark says the task is
  uncontrollable.
- The full-info causal heuristic is never called an optimal controller.
- The candidate interior is never called ground truth — spontaneous collective
  identity has no unique simulator label.
- Visual clumpness never erases statistically interesting snake-like candidates.
- The physical regime is never selected using blind-estimator performance.
- Thingness thresholds are never tuned on control success.
- Identity/clumpness thresholds are never relaxed after a failed intervention.
