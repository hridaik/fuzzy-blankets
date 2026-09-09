# RESULTS_6_9

Stage 6.9 is a **pilot, and its feasibility gate FAILS.** The stage therefore
stops before any steering experiment, as `PLAN.md` and the task brief (§33)
require. This document reports the failure, the diagnosis, and one
explicitly-labelled off-specification exploration that explains it.

Every number comes from the frozen protocol in `PROTOCOL_6_9.md`; the gate's
five criteria were fixed in
`logs/translation_gate_criteria_predeclared.txt` before the gate ran, and were
not moved afterwards. Nothing in Stages 6–6.8 is modified by this stage.

---

## Headline

**At the specified interaction scale, the minimal moving-agent extension does
not sustain a coherent translating collective.** Across 40 uncontrolled
episodes at `R = 0.9, v = 0.28` — a mean realized live in-degree of **8.9**,
the Moore model's scale, as the brief requires — **0 of 40 episodes** satisfy
all five feasibility criteria.

| criterion | rate | reading |
|---|---|---|
| T1 persists ≥ 40 steps | 0.65 | often, not reliably (median duration 62) |
| T2 translates ≥ 3R | 0.80 | it does move |
| T3 material change `R_M` ≤ 0.70 | **0.90** | membership turns over freely |
| T4 co-moving similarity ≥ 0.70 | **0.38** | **organization does not persist** |
| T5 nontrivial and spatially coherent | **0.03** | **the binding failure** |

T5 breaks down cleanly: size is in the valid range on **100%** of steps — so
this is not shrink-to-win and not a degenerate remnant — but the group is
**≤ 2 spatial components on only 40% of steps, averaging 3.8 pieces**.

This is the failure mode the pre-declaration named in advance: `R_M` falls
(0.32) while `R_F` does *not* stay high (0.658), which means **the collective
is being destroyed and replaced rather than transported.** There is plenty of
constituent turnover, and nothing organized for it to be turnover *of*.

Deformation confirms it: `D_deform = 0.185` at spec against 0.023
off-specification — an eightfold difference in what is left after the best
bulk translation is removed.

**Per the brief, the stage stops here. No boundary-inference result, no
guidance experiment, and no identity claim is reported from this model.**

---

## 1. What went wrong first, and how it was caught

The first version of this stage ran at `R = 1.6, v = 0.5` and its gate
*passed* at 0.40. That parameterization violates the brief's requirement that
local degree stay "on roughly the same scale as the original Moore model"
(8 geometric, ~5 live after FOV). `PROTOCOL_6_9.md` originally recorded
`R = 1.6` as giving "4.6 at uniform density, ~10.7 realized" — **both figures
were wrong** as descriptions of the clustered configuration the flock actually
occupies. Measured directly there, the mean live in-degree is **21.2**, about
3× the Moore scale.

It surfaced through its consequences rather than through the bookkeeping. At
degree 21 the expected-free-energy gap between an interior bird's best and
second-best action is ≈ 93, so `policy_posterior` saturates: **77% of interior
birds have `max(u_t) == 1.0` to double precision.** A saturated decision cannot
be moved by one neighbour, so the one-step causal effect of intervening on
almost any exterior source is numerically zero:

| on seed 0, t = 60, \|I\| = 100, \|B_t^D\| = 47 | result |
|---|---|
| `B̂^causal` — finite probe, 60 rollouts × 3 repeats | **1 of 47** |
| `B^causal,exact` — the **exact** propagator | **1 of 47** |
| candidate sources with effect > 1e-9 | 1 of 63 |

Because the exact propagator agrees with the probe, this was **never an
estimation problem**. It was a mis-specified interaction radius producing a
locked dynamics. Reporting it as an identifiability-versus-estimation finding
would have been reporting an artefact of a parameter choice as a property of
the method. The full record, including the retraction of an earlier wrong
diagnosis (that the estimator's statistic was at fault), is
`logs/translation_gate_criteria_predeclared.txt`, ADDENDA 2–4.

## 2. The correction, and the rule used to make it

`R` was re-specified downward with `v` scaled to preserve the
neighbour-crossing time `v/R = 0.31`. The selection rule was declared before
the numbers were seen (ADDENDUM 4): **choose the pair whose mean realized live
in-degree, measured in the clustered steady state of uncontrolled runs, is
closest to the Moore model's 8** — uncontrolled phenomenology only, no identity
score, no interface recovery, no control outcome. That selects
`R = 0.9, v = 0.28` at degree 8.9.

The same addendum fixed in advance what to do if the gate then failed: **report
the failure; do not move `R` back up.** A gate that passes only at 3× the
specified connectivity is a gate passed by a different model.

## 3. The phenomenon tracks connectivity, not the specification

This is the one positive thing the stage establishes, and it is why the
off-specification runs are worth reporting rather than deleting:

| R | v | live in-degree | policy saturation | mean components | `D_deform` | `R_F` | gate pass rate |
|---|---|---|---|---|---|---|---|
| **0.90** | **0.28** | **8.9** ← spec | 0.41 | **3.80** | **0.185** | **0.658** | **0.00** (40 episodes) |
| 1.10 | 0.34 | 14.8 | 0.65 | — | — | 0.89 | 0/6 (pilot) |
| 1.30 | 0.40 | 16.5 | 0.70 | — | — | 0.94 | 2/6 (pilot) |
| 1.60 | 0.50 | 21.2 | 0.77 | 1.15 | 0.023 | 0.958 | 0.40 (40 episodes) |

Gate pass rate rises monotonically with interaction degree. **The
translating-collective phenomenon in this model is not a generic consequence of
adding motion to the Stage 6.8 flock; it requires an interaction neighbourhood
roughly three times the Moore scale**, at which point the dynamics are also
locked hard enough that the causal interface collapses to a single live channel.

Those two facts are in tension, and the tension is the result: **the same
over-connection that makes a moving collective cohere is what makes its causal
interface disappear.** In this model family you can have a trackable
translating collective or an inferable causal interface, but the parameter
ranges do not overlap.

## 4. What the off-specification runs showed (reported, not claimed)

At `R = 1.6` the gate passed at 0.40 (16/40) and the identity decomposition
behaved as hypothesized: gate-passing episodes ended at `R_M = 0.50` (one at
0.14) with `R_F = 0.952` and `D_deform = 0.027`, having travelled ~51.5
interaction radii of path; two families of episodes with identical path length,
identical `R_F` and identical step-to-step lineage overlap were separated only
by material retention (0.50 vs 0.95). `R_M` was non-monotone, with ~1.8 lineage
branch events per episode.

**None of that is claimed as a Stage 6.9 result.** It was produced by a model
that violates the stated specification, and it is retained only because the
contrast with the spec-compliant runs is what identifies connectivity as the
controlling variable. Its data files carry a `__SUPERSEDED` suffix and its
figures are labelled off-specification.

## 5. Answering the stage's own question

> Can a collective retain functional identity in a translating frame while its
> material membership changes?

**Not demonstrated in this model at its specified scale.** At degree 8.9,
membership changes readily (T3 = 0.90) but functional identity does not survive
(T4 = 0.38, `R_F` = 0.658) and the group is not spatially coherent (T5 = 0.03,
3.8 components). The two halves of the hypothesis do not co-occur.

At 3× connectivity they do co-occur, and there the decomposition does
distinguish "same constituents" from "same moving organization". But that is a
statement about a model built to different specification, and Stage 6.9 does
not convert it into a claim.

## 6. What was NOT run, and why

Per the brief's §33 and this stage's `PLAN.md`, the gate is a hard stop:

- **boundary inference in the translating frame (§34)** — not reported;
- **the guidance/control experiment (§§35–37)** — not run;
- **figures 6.9-5 and 6.9-6** — not produced.

An earlier off-specification guidance *feasibility* probe (oracle arm only, on
the superseded `R = 1.6` model) found the steering task infeasible there too:
mean path error 4.87, 4.94, 5.82, 5.82 interaction radii against a 3.0 R target
across the predeclared `(K_act, horizon)` grid, **worsening** with both more
actuators and a longer horizon. That echoes Stage 6.8's control finding — a
large collective's heading is set by its own internal consensus and boundary
actuation cannot outvote it — but it is recorded as a note, not a result.

## 7. Caveats

- **Pilot scale.** 40 episodes at spec, 40 off-specification, 6 per cell in the
  intermediate scan.
- **The failure is specific to this model family.** It says the *minimal*
  moving extension of this active-inference flock, with its existing
  collision terms and no invented attraction, does not cohere at Moore-scale
  connectivity. A flock model with an explicit cohesion term would very likely
  behave differently — but adding one is exactly what the brief forbids, and
  what `PLAN.md` committed not to do.
- **`R` and `v` were varied together** to hold `v/R` fixed, so the scan does not
  separate "fewer neighbours" from "slower relative motion".
- **The degree mis-specification was mine**, was found late, and cost the
  stage its headline. The audit trail records it in full rather than
  presenting the corrected run as if it had been the plan.
