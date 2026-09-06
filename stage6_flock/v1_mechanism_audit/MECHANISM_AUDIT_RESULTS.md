# MECHANISM_AUDIT_RESULTS.md

All numbers below are freshly computed in this session, from the frozen
`PROTOCOL_V1a` canonical snapshot (seed 2, `t0=41`, `h0=left`, `h_star=up`,
`|I0|=20`, `T_u=T_r=20`), unless stated otherwise. Raw JSON for every number
is in `data/`; figures are in `figures/` (`audit_figA` through `audit_figH`).

## Part B — the model's actual interaction interface (structural, derived from source)

**Key structural fact** (`code/dynamical_shell.py`, cited directly from
`flock_sim.active_inference.compute_G` and `flock_sim.lattice.Lattice`):
a bird's next heading depends on exactly its (up to 8) Moore-neighbors on the
**fixed, time-invariant 10x10 lattice** — birds do not move in this port
(only the heading/Potts-spin state evolves; the physical interaction graph
`lattice.neighbor_ids` is built once from row/column position and never
changes). Consequently, for a frozen core `I0`:

$$B^D_t = \{j \notin I_0 : j \in \bigcup_{i \in I_0} \text{neighbors}(i)\} = B^D_0 \quad \text{for all } t.$$

**This means "adaptive" vs. "static" dynamical-shell control (the task's D3
vs. D4) are the SAME intervention set in this specific port** — not because
the distinction is meaningless in general, but because this model's physical
coupling graph cannot move. This is reported as a genuine, load-bearing
finding (it directly determines how Outcome 3 in the task's decision tree is
interpreted below), not a simplification chosen for convenience.

For the canonical flock at `t0=41`:

| Set | Size | Members |
|---|---|---|
| `I0` (frozen core) | 20 | `{7,8,9,16,17,18,19,26,27,28,29,36,37,38,39,47,48,49,58,59}` |
| `B^D_0` (dynamical shell) | **12** | `{5,6,15,25,35,45,46,56,57,67,68,69}` |
| `B^F_0` (Fiedler/spectral boundary) | **2** | `{5, 46}` |
| `E^D_0` (exterior beyond the shell) | 68 | (everything else) |

**`B^F_0 ⊂ B^D_0` exactly** (both spectral-boundary birds are also dynamical-shell
members) — the spectral boundary is not *wrong*, it is a small, incomplete
subset of the true interface, capturing 2 of the 12 birds that actually feed
into `I0`'s update.

## Part C — spectral vs. dynamical vs. control interfaces

`code/boundary_compare.py`, `data/boundary_compare.json`, Figures A-C.

- **Canonical flock**: `|B^F_0 ∩ B^D_0| = 2`, i.e. `B^F_0 ⊆ B^D_0` fully;
  `Jaccard(B^F_0, B^D_0) = 0.167`.
- **Small ensemble of 7 other qualifying baseline flocks** (seeds 2,3,4,8,9,10,11):
  mean Jaccard = **0.119**, median = 0.127. Two flocks (seeds 3, 9) had
  **zero** overlap between `B^F` and `B^D` at all. One flock (seed 11) had an
  anomalously large `B^F_0` (53 members — more than half the lattice), driven
  by an unusually large eigengap (12.8) that nonetheless produced a
  numerically very "flat" Fiedler vector; this is flagged, not silently
  averaged in without comment, as an instance of the eigengap not
  guaranteeing a well-behaved boundary size either. **The weak spectral/dynamical
  overlap is not a quirk of the canonical flock's small n=2 boundary — it holds,
  with substantial variability, across independently emergent flocks.**
- **Response vs. dynamical distance** (Figure C): Spearman correlation between
  single-actuator response (`mean_Hstar_end`, k=1 exhaustive, n=50/bird) and
  graph distance to `I0` on the static lattice = **-0.25** (closer birds
  respond somewhat more, as expected, but weakly — consistent with the fact
  that even the *full* 12-bird shell only reaches high response when forced
  *together*, not that any nearby bird is individually powerful).
- **Empirical control-interface `B^C`** (top decile of single-actuator
  responders, 8 birds): `Jaccard(B^C, B^D_0) ` and `Jaccard(B^C, B^F_0)` are
  both low (see `data/boundary_compare.json`) — the single-bird response
  ranking used by V1's own shortlist procedure is itself an imperfect proxy
  for `B^D_0` membership (4 of V1's greedy top-6 shortlist birds — 67, 46, 68
  — are in `B^D_0`; 2 — 66, 77 — are not, they are 2 hops away).

**Headline of Part C**: `B^F` (spectral), `B^D` (dynamical), and `B^C`
(empirical single-bird response ranking) are three genuinely different sets
that partially, not fully, agree with one another.

## Part D — the feasibility ladder (the critical experiment)

`code/feasibility_ladder.py`, `data/feasibility_ladder.json`, Figure D.
n=50 replicates/arm, common random numbers, canonical snapshot, frozen
`T_u=20`/`T_r=20`/thresholds, **unchanged from PROTOCOL_V1a**.

| Arm | actuators | mean H*(t0+Tu) | P(success) | P(success & integrity) | mean H* at release | P(persistence \| success) |
|---|---|---|---|---|---|---|
| D0 baseline | 0 | 0.000 | 0.000 | 0.000 | 0.000 | — |
| D2 Fiedler boundary `B^F_0` | 2 | 0.003 | 0.000 | 0.000 | 0.000 | — |
| **D3/D4 dynamical shell `B^D_0`** | **12** | **0.968** | **0.960** | 0.000 | **0.993** | **1.00** |
| D5 all non-core | 80 | 0.968 | 0.960 | 0.000 | 1.000 | 1.00 |
| D1 full interior `I0` (diagnostic, inadmissible) | 20 | 1.000 | 1.000 | 0.500 | 0.594 | 0.64 |

### Interpretation gate (applied once, before any further sparsification)

This is **Outcome 2** in the task's decision tree, with a further nuance:

> **The Fiedler/spectral boundary is not the relevant control interface.
> The actual dynamical (lattice-interaction) shell is — and forcing it
> achieves target-heading success (P=0.96) statistically indistinguishable
> from forcing all 80 exterior birds (P=0.96), using only 12 of them.**

Two things sharpen this beyond a clean "Outcome 2":

1. **D3 and D4 are the same arm here** (Part B's structural finding), so this
   audit cannot separately confirm "Outcome 3" (adaptive beats static) as a
   distinct phenomenon *in this port* — the two conditions are not
   distinguishable because the model's physical graph never moves. This is
   stated plainly rather than silently claiming Outcome 3 support that the
   port cannot actually provide.
2. **`P(success & integrity) = 0.000` for every exterior-only arm**,
   including the near-perfect D3/D4/D5 arms, while `mean_min_coherence` for
   those arms (~0.515) is well below the frozen `0.8` integrity bar. This is
   a genuine, mechanistically interesting secondary finding, not a
   contradiction: unlike direct full-core forcing (which trivially keeps
   `C_{I0}(t)=1.0` throughout, since every core member is simply told what to
   do), steering the core *by propagation from its boundary* necessarily
   passes through a transient period where different parts of the core
   respond at slightly different rates, so the core's internal heading
   agreement dips before it reconverges on the new target. **The frozen
   integrity criterion (`C_{I0}(t)>=0.8` at every single timestep of the
   control window) is well-suited to detecting fragmentation under direct
   forcing, but appears structurally difficult for ANY indirect/propagation-based
   exterior control strategy to satisfy simultaneously with target-heading
   success** — this is flagged as a demonstrated tension for `PROTOCOL_V2.md`
   to address explicitly (see that file), not silently patched here. Both
   metrics are reported throughout this document precisely so this tension
   stays visible rather than being averaged away.
3. A genuinely good secondary finding: **post-release persistence is
   essentially perfect for exterior-shell control (`P(persistence|success)=1.00`,
   `mean_Hstar_release=0.993`) — markedly BETTER than direct full-core forcing's
   own persistence (`0.64`, `mean_Hstar_release=0.594`)**. Steering via the
   boundary, once it succeeds, appears to leave a more self-sustaining
   configuration than overriding the core directly (plausibly because the
   boundary birds continue reinforcing the target heading by ordinary local
   coupling after release, whereas direct-forced core birds have no such
   external support once released). This is exactly the kind of "the flock
   knows something no single intervention modality reveals alone" result the
   audit was designed to surface.

**Decision**: proceed to sparsification using `B^D_0` as the primary control
interface (task's "Outcome 2" branch), carrying the integrity-criterion
tension forward transparently into `PROTOCOL_V2.md` rather than loosening it
silently.

## Part E — exhaustive pair-synergy audit (all 3160 pairs)

`code/pair_synergy.py`, `data/pair_synergy.json`, Figure E. n=10
replicates/pair (development scale — 3160 x 50 was judged too expensive for
this session's budget; documented, not hidden). Runtime: 470s for all 3,160
pairs (31,600 simulations).

- **Best pair over the full 3160**: `{57, 77}`, `R_ij=0.160`; **zero of 3160
  pairs meet `P(success)>=0.5`** at n=10. This is close to, and consistent
  with, V1's shortlist-restricted result (`{67,57}`, `R=0.149`) — **the full
  sweep confirms the k=2 negative finding generalizes beyond the top-10
  shortlist searched in `protocol_v1`**, closing the gap `RESULTS_V1.md`
  itself flagged as untested.
- **Control-response synergy `S_ij`**: mean -0.001, max 0.104 (pair `{57,77}`),
  min -0.051. Synergy is small and not concentrated in `B^D_0`-only pairs —
  several of the highest-`S_ij` pairs (`{57,77}`, `{57,87}`, `{66,68}`) have
  only ONE member in `B^D_0`, suggesting near-shell-adjacent pairs (distance
  1-3) can show modest cooperative effects even without being exactly on the
  shell, but never anywhere near the magnitude needed for two-actuator success.
- **No pair, from any of the 3160, comes remotely close to the 0.8 success
  threshold.** This is the clean confirmation that "two birds, however chosen,
  cannot do this" — you need most of the shell, not a clever pair.

## Shell sparsification (bridges Part D's finding to a V2-ready actuator budget)

`code/shell_sparsification.py`, `data/shell_sparsification.json`. Once Part D
showed the FULL `B^D_0` (12 birds) succeeds, the natural next question is how
much of it is actually necessary — searched exhaustively for k=1-3 within the
correct 12-bird pool (298 combinations), then greedy for k=4-12. n=30
replicates/candidate (development scale).

| k | best set (greedy path) | mean H*(t0+Tu) | P(success) |
|---|---|---|---|
| 1 | {67} | 0.047 | 0.000 |
| 2 | {57,67} | 0.135 | 0.000 |
| 3 | {46,56,68} | 0.230 | 0.000 |
| 6 | +{69,35,25} | 0.467 | 0.000 |
| 7 | +{6} | 0.652 | 0.267 |
| **8** | +{15} | 0.870 | **0.700** (crosses `p_min=0.5`) |
| **9** | +{67} | 0.945 | **0.900** (crosses `p_min=0.5` AND `success_threshold=0.8` in mean) |
| 12 (=full shell) | all of `B^D_0` | 0.973 | 0.967 |

**A real, sparse, externally-admissible actuator set of 9 birds (45% of the
shell, 9% of the whole flock) achieves `mean_Hstar_end=0.945` and
`p_success=0.900`** — dramatically different from V1's best-found result at
comparable actuator count (`k=6`, `mean_Hstar_end=0.282`, `p_success=0.000`,
using the wrong candidate pool). **This is the mechanistic resolution of the
V1 negative result: sparse control was never impossible — it required
searching the physically-correct candidate pool (`B^D_0`), not an
empirically-ranked shortlist drawn from all 80 exterior birds.** As with Part
D, `p_success_and_integrity` remains 0.000 throughout this table — the same
integrity-vs-propagation tension noted above.

## Part F — direct-core resistance curve (mechanistic diagnostic only)

`code/core_resistance.py`, `data/core_resistance.json`, Figure F. Forcing
`k∈{1,2,4,8,12,16,20}` INTERIOR birds directly (inadmissible for the real
task; diagnostic only).

| k (of 20 interior) | by internal-degree mean H* | random-subset mean H* (n=5 draws) |
|---|---|---|
| 1 | 0.079 | 0.061 ± 0.004 |
| 2 | 0.305 | 0.129 ± 0.029 |
| 4 | 0.551 | 0.639 ± 0.083 |
| 8 | 0.731 | 0.862 ± 0.063 |
| 12 | 0.906 | 0.962 ± 0.026 |
| 16 | 0.922 | 1.000 ± 0.000 |
| 20 | 1.000 | 1.000 ± 0.000 |

**No sharp cascade/bistable threshold** — the response climbs smoothly and
roughly monotonically with `k`, consistent with a gradually-reinforcing
consensus rather than a hard tipping point. A secondary, mildly
counter-intuitive observation: **spatially-distributed random subsets of
`I0` often outperform the highest-internal-degree subset** at matched `k`
(e.g. k=8: random 0.862 vs. degree-ranked 0.731) — plausibly because the
highest-internal-degree birds cluster in one region of the core, exciting
only part of the block, while random subsets spread influence more evenly
across it. This is a real observation from this specific canonical flock,
reported as such — not investigated further here per the task brief's
instruction not to over-analyze this diagnostic.

## Part G — parameter-regime ambiguity audit

`code/parameter_sensitivity.py`, `data/parameter_sensitivity.json`, Figure G.
Two named, predeclared regimes, each run once:

| | `code_default` (β=1,ρ=15,ω=3) | `manuscript_all_ones` (β=1,ρ=1,ω=1) |
|---|---|---|
| From-scratch flock-selection qualification rate (n=50 seeds) | **54%** | **0%** |
| Mean polarization `Phi` at t=30 (n=50 seeds) | 0.744 | 0.107 |
| `B^D_0` control, canonical IC, ceteris paribus (n=20) | `p_success=0.95` | `p_success=0.00` |
| Uncontrolled `H*` at `t0+Tu`, canonical IC (n=20) | 0.000 | 0.255 (noise floor, not genuine attainment) |

**This is a materially important, not cosmetic, discrepancy.** Under the
manuscript's literally-stated "all precisions set to 1," this specific
flocking model **essentially never reaches a qualifying, Fiedler-identifiable
flock within 60 steps** (0/50 seeds) and barely polarizes at all
(`Phi≈0.11`, close to the ~0 disordered baseline). The paper's Fig. 1A shows
clear visible alignment within 8 steps; that is categorically inconsistent
with the `manuscript_all_ones` regime and consistent with `code_default`.
**This strongly corroborates `METHODS_AUDIT.md`'s discrepancy #1**: the
paper's reported simulations almost certainly used the code's actual
defaults (`ρ=15,ω=3`), not the text's stated `1,1,1` — now with direct
quantitative evidence rather than only a code-reading argument. Both regimes
are reported here, as required; **no threshold or protocol value was changed
based on which regime "worked better."** `code_default` is retained as V1's
(and V2's) operating regime because it is what the code — and, by this
evidence, almost certainly the paper's actual reported results — actually
runs, not because it is the regime under which control happens to succeed.

**Open question for Giovanni** (as requested by the task brief): *which
precision values (`rho`, `omega`) actually generated the simulations behind
the manuscript's Figures 1-3 — the code's defaults (15, 3) or the text's
stated value (1)?* This audit's evidence points strongly toward the code's
defaults having been used, but only the original authors can confirm this.

## Part H — statistical / Markov-boundary validation

`code/predictive_screening.py`, `data/predictive_screening.json`, Figure H.

**H1 (structural, exact)**: because `compute_G` for a bird `i` sums
independent contributions over exactly `lattice.neighbor_ids[i]`, and because
per-bird action/next-heading RNG draws are conditionally independent given
the full current state, the model's computational graph implies EXACTLY:

$$X_{I_0,t+1} \perp X_{E^D_0,t} \mid X_{I_0,t}, X_{B^D_0,t}$$

This is a genuine structural one-step Markov/screening property with
`B=B^D_0` — not an empirical estimate, but a direct consequence of the
update code (`B^D_0` is defined, in Part B, as exactly the set that makes
this true by construction: it contains every neighbor of every `I0` bird).

**H2 (empirical validation + Fiedler comparison)**: verified two ways.

1. **Structural check, verified by deliberate corruption**: setting every
   bird outside `I0 ∪ B^D_0` to an arbitrary different heading and
   recomputing the exact predictive distribution for every `I0` bird produced
   **identical results to the uncorrupted computation in 100.00% of 8,000
   bird-samples** (`frac_BD_predictions_exactly_matching_full = 1.0`) —
   direct empirical confirmation of the structural claim, not just a
   plausibility argument.
2. **Predictive log-loss, `M_full` vs. `M_{B^D_0}` vs. `M_{B^F_0}`** (n=40
   trajectories x 10 sampled timesteps x 20 core birds = 8,000 bird-samples;
   `M_{B^F_0}` uses 24 Monte-Carlo mean-field draws to marginalize unknown
   neighbors — an explicit approximation, not exact CMI):

   | Model | mean one-step log-loss (nats) |
   |---|---|
   | `M_full` (ground truth) | 0.0779 |
   | `M_{B^D_0}` (12 birds) | 0.0779 (**exactly equal**, as predicted) |
   | `M_{B^F_0}` (2 birds) | 0.1097 |

   **Excess log-loss from using the spectral boundary instead of the
   dynamical shell: +0.032 nats/bird-step** — a real, positive, non-trivial
   information loss. **The Fiedler boundary does not screen the interior's
   future state as well as the true interaction shell; the dynamical shell
   screens it perfectly (by construction and confirmed empirically).**

This directly answers the central question posed in Part H: *no*, the
spectral boundary is not an adequate statistical Markov blanket substitute
for the true one-step interaction shell in this model.

## Cross-cutting summary: do `B^F`, `B^D`, `B^{MB}`, `B^C` coincide?

| Pair | Relationship found |
|---|---|
| `B^F` vs. `B^D` | `B^F ⊂ B^D` (strict subset on canonical flock); weak-to-moderate overlap generally (mean Jaccard 0.12 over ensemble); **do NOT coincide** |
| `B^F` vs. `B^{MB}` (statistical/predictive) | `B^D_0` (not `B^F_0`) is the set that achieves exact statistical screening (Part H); **`B^F` is not an adequate `B^{MB}`; `B^D_0` IS `B^{MB}` exactly, by construction and by verification** |
| `B^D` vs. `B^C` (empirical control interface) | Overlap is partial — `B^D_0`'s members are enriched among high single-actuator responders but the single-bird response ranking alone (`B^C`) is an incomplete proxy for `B^D_0` membership (Part C); **the FULL `B^D_0`, forced together, is what actually works (Part D) — no individual response ranking predicted this from k=1 data alone** |
| `B^C` (pairs) vs. success | No pair, from the full `C(80,2)=3160`, approaches success (Part E) — control requires most of the shell acting jointly, not a well-chosen small set found by ranking individuals or pairs |

**The single most important result of this mechanism audit**: V1's negative
finding was correct *as a statement about the specific search performed*, but
the model IS externally, sparsely controllable — the earlier search simply
never tested the physically-motivated candidate set. Once the actual
one-step dynamical interaction shell is identified directly from source code
(not assumed, not searched for empirically) and forced as a whole, control
succeeds almost perfectly (96%) with only 12% of the flock, and a
sparsified 9-bird subset of that same, correctly-identified shell already
reaches 90% success — none of which required searching outside the
structurally-derived candidate pool.
