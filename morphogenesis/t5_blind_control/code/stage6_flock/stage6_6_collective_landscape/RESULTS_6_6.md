# RESULTS_6_6.md — Stage 6.6: Collective Landscape

Protocol: `PROTOCOL_6_6.md`, `configs/protocol_6_6.yaml`
(SHA-256 `7bfe7c2e8141fe442ad30bd0d8ad90ef470045de11cc790742c7b5e79d08b3d4`).
Gate: `METRIC_VALIDATION.md` (passed). Data: all 15 primary snapshots,
`data/seed{2,3,4}__{no_control,shell_only,same_direction,opposite,
disordered}__fE1.00__t20.{json,csv}` (up to 5000 candidate `k=20` interiors
each — 5000 reached in every snapshot, see `data/snapshot_manifest.json`),
`data/archetype_trajectories.json`, `data/results_summary.json`. Figures:
`figures/fig_6_6_1[_seed{3,4}]`, `fig_6_6_2..4`.

## Computational-budget outcome

The target of >=5000 unique connected `k=20` candidates per snapshot (task
brief section 9) was reached for **every one of the 15 primary snapshots**
(3 seeds x 5 regimes, control-end, `f_E=1.0`) —
`data/snapshot_manifest.json` records `n_candidates_unique=5000` for all
15. Total wall-clock: **6791.9s (~113 minutes)** on one CPU core, ~400-810s
per snapshot, dominated by the mask-cache's unique `(bird, neighbour-mask)`
fits, which saturate near **17,400** regardless of candidate count
(confirmed empirically at 100/600/1500/5000 candidates on a seed-2
natural-regime pilot: 8183/15745/17210/17414 fits — visibly plateauing, not
scaling with the ~50x candidate-count increase; the full-scale runs all
land in the same 17,376-17,428 band). This confirms `PLAN.md`'s stated
design bet (task brief section 5's "cheap once the cache saturates" claim)
held in practice; the full 5000-candidate target did not require the
documented fallback of a reduced count.

## Q1: Can two candidate k=20 groups have similar coherence but very different external distinctiveness?

**Yes, routinely, in every seed.** Within any single snapshot, `C` and `D`
vary largely independently at the top end of `C`. Sharpest single-flock
illustration: `seed2__no_control` (n=5000), `C` ranges `[0.90, 1.00]` (mean
0.978) while `D` simultaneously ranges only `[0.000, 0.075]` — among the
many `C>0.95` candidates, `D` still varies across its own full available
range. Across regimes, the effect is starker still: `seed4__same_direction`
has `C` mean 0.893 (comparable to plenty of other conditions) but `D` mean
0.089 versus `seed4__no_control`'s `C` mean 0.725 and `D` mean 0.333 — two
groups of candidates with *lower* average coherence can carry *higher*
average contrast than a higher-coherence group, which is itself direct
evidence that coherence does not determine contrast in either direction.

## Q2: Can two groups have similar visual coherence but very different internal predictive integration?

**Yes — the sharpest and most cross-seed-robust finding of the whole
stage.** The Pearson correlation between `C` and `G`, across all 5000
candidates per snapshot:

| seed | no_control | shell_only | same_direction | opposite | disordered |
|---|---|---|---|---|---|
| 2 | **-0.76** | +0.25 | +0.31 | **+0.45** | +0.32 |
| 3 | **-0.26** | -0.50 | n/a (D, C both constant) | **+0.35** | -0.38 |
| 4 | **-0.20** | +0.12 | -0.14 | **+0.59** | +0.39 |

**Two patterns are stable across all three seeds:** `r(C,G)` is
**negative under natural, unforced dynamics in every seed** (`-0.76,
-0.26, -0.20`), and **positive under the `opposite` archetype in every
seed** (`+0.45, +0.35, +0.59`) — the only two conditions where the sign is
unanimous. The other three conditions (`shell_only`, `same_direction`,
`disordered`) flip sign across seeds and are **not** reliable in
direction — an honest limit on generalization, reported rather than
smoothed into "forcing always makes C and G move together." The mechanism
proposed in `METRIC_VALIDATION.md` Q4 (near-unanimous *unforced* coherence
tends to reflect boundary-driven consensus, which caps `G`'s marginal
value) is consistent with the one pattern that *does* hold everywhere
(`no_control`'s negative sign); the `opposite` condition's unanimous
positive sign is a new, equally robust finding this full-landscape pass
adds beyond `METRIC_VALIDATION.md`'s fixed-`I0` check.

## Q3: Can a group look visually distinct yet leak substantial predictive information from outside?

**Yes.** `L`'s scale is small everywhere in this model (see Q4), but its
single largest value in the entire 15-snapshot dataset is
`seed3__no_control`'s mean `L=0.00686` (max individual value higher still)
— i.e. the *un*forced regime, not a forced one, produced the most leakage
on average for that seed, alongside `D` mean `0.271` (well above that
seed's `D=0` floor seen elsewhere). `corr(L,D)` is weak-to-moderate and
**always non-positive** across every one of the 15 snapshots (range
`-0.44` to `-0.00`, `data/results_summary.json`) — meaning where a
relationship exists at all, it mildly favors low-L-high-D, but it is far
from a strong constraint: `seed4__disordered` (`corr(L,D)=-0.44`, the
strongest of the 15) still has plenty of individual candidates with
above-median `L` *and* above-median `D` simultaneously (visually confirmed
via `code/analyze_results.py`-style per-candidate inspection, not just the
aggregate correlation). So: yes, visually distinct candidates leaking
substantial information do occur; low leakage is correlated with, but not
required for, high contrast.

## Q4: Does fixed-budget leakage distinguish compactly screenable groups from arbitrary connected regions?

**Weakly overall, and the natural regime is the extreme case — an honest
limitation of `L` in this model/flock, not a bug.** `L`'s mean across all
15 snapshots never exceeds `0.00686` and is usually one to two orders of
magnitude smaller (`data/results_summary.json`); a `K=12` boundary budget
essentially always suffices to screen a 20-bird interior in this
one-hop-causal-horizon model (see `METRIC_VALIDATION.md`'s finite-sample
caveat for the mechanism: each bird's next state depends only on its own
up-to-8 Moore neighbours, so a 12-node shared budget rarely runs short).
The natural regime is not uniformly the *smallest*-`L` condition across
seeds (seed 3's natural regime has the dataset's largest mean `L`), so the
"budget is trivially sufficient" story is strongest for seed 2 specifically
and should not be over-generalized. In no snapshot does `L` cleanly
separate "compact, shape-typical" candidates from unusual ones — the
`region_growing`/`mcmc_swap`/`spectral_resized`/etc. source populations
show no visible `L` separation in any of the 15 snapshots. **`L` remains
the least discriminative of the four axes in this particular flock/model,
across every regime tested, not just the natural one.**

## Q5: Does the four-dimensional landscape contain visibly convincing and visibly unconvincing candidate collectives in the expected regions?

**Yes, on both counts, and the face-validity check itself surfaced a
genuine "visually bad, metric-favorable" case worth reporting explicitly.**
`figures/fig_6_6_4_candidate_comparison.png` (`seed2__no_control`) shows
compact, blob-like `high C + high D` and `high G, low L` examples that look
like real, spatially contiguous groups, alongside a `spectral_resized`
candidate that is a **Moore-connected but visually scattered diagonal
"snake"** — every step in its structural connection uses only a diagonal
Moore edge, which is fully valid under this model's actual interaction
graph but reads as scattered, not blob-like, to the eye. This is exactly
the "obvious visually bad candidate that nevertheless scores well on some
subset of metrics" case task brief section 33/36 asks whether the
landscape contains — it does, and it is disclosed and shown deliberately
rather than filtered out of the figure. `seed2__no_control` also contains
a large population of `C>0.95, D<0.03` candidates: coherent but visually
indistinguishable from their surroundings, the "arbitrary patch of a
globally aligned system" case motivating this whole stage.

## Q6: Does making the exterior same/opposite/disordered move the candidate through the metric landscape in an interpretable way?

**Yes, directionally, but the magnitude and even the sign of secondary
effects (like the size of the "jointly ideal" population) are seed
dependent — reported honestly rather than papered over.** The primary
`D`/`H_E` movements replicate `METRIC_VALIDATION.md`'s fixed-`I0` findings
at full landscape scale in every seed: `same_direction` pulls `D` toward
its regime floor (exactly `0.000` for *all 5000* seed-3 candidates — the
most extreme case, discussed in Q9), `opposite` reliably produces the
dataset's highest `D` ceiling (`D_max=1.000` in 13 of 15 snapshots), and
`disordered` reliably keeps `D` moderate with external entropy near its
ceiling. What does **not** replicate cleanly across seeds is the "jointly
ideal" (`n_ideal_region`, top-quintile `G`, bottom-quintile `L`, `C>0.9`,
top-quintile `D`) population size:

| seed | no_control | shell_only | same_direction | opposite | disordered |
|---|---|---|---|---|---|
| 2 | 1 | 350 | 11 | 25 | 369 |
| 3 | 16 | 11 | 0 | 31 | 24 |
| 4 | 13 | 16 | 25 | **0** | 292 |

For seed 2, every forced condition has *more* jointly-ideal candidates than
natural — the clean story `METRIC_VALIDATION.md` previewed. For seeds 3 and
4, several forced conditions have **fewer** than natural (seed 3's
`same_direction`, seed 4's `opposite`), because natural dynamics for those
seeds at this snapshot are already less globally homogeneous (see Q9) —
forcing does move the landscape in the hypothesized direction on average,
but "more forcing conditions -> more individuated-looking candidates" is
not a law that holds snapshot-by-snapshot.

## Q7: Which of C, G, L, D appears redundant in this particular model, if any?

**None are redundant; `L` is the weakest independent axis, consistently,
across every snapshot tested (not just natural dynamics).** No pair of the
four correlates strongly and consistently in one direction across all 15
snapshots: `corr(C,G)` ranges `[-0.76, +0.59]` and flips sign by
seed/condition (Q2); `corr(L,D)` stays weak-to-moderate and one-signed but
never approaches +-0.9 (Q3); `corr(C,D)` and `corr(G,D)` likewise never
reach a magnitude that would make one axis a stand-in for another
(`data/results_summary.json`, all 15 rows). `L`'s weakness is specifically
in its *own* dynamic range (Q4), not in being correlationally identical to
another axis — it stays informative in direction (always weakly negatively
associated with `D`) even where its magnitude is small.

## Q8: Which metrics appear genuinely necessary to distinguish "globally aligned patch" from "individuated coherent collective"?

**`D` (with its secondary companions `H_E`, directional opposition) still
does most of the distinguishing work, and `G` remains the necessary second
axis for the "high-C-but-hollow" failure mode — both conclusions hold up
across all three seeds, not just seed 2.** `C` alone cannot separate a
globally-aligned patch from an individuated one: across the 15 snapshots,
the condition with the *highest* mean `C` is not consistently the same
across seeds, and `C`'s own cross-condition range within a single seed
(e.g. seed 4: `0.715`-`0.893`) is much narrower than `D`'s range in the
same seed (`0.089`-`0.333`), i.e. `D` is simply the more sensitive
instrument for this distinction in every seed checked. `G`'s necessity is
demonstrated by Q2's finding holding in all three seeds: a candidate can be
`C`-coherent and `G`-hollow simultaneously, robustly, not as a one-off.
`L` contributes least (Q4/Q7) in every seed, not just seed 2.

## Q9: Are the results stable across seeds 2, 3 and 4?

**Partially, and the honest answer is itself informative: the *mechanism*
questions (is C-G decoupling real? does D separate visually-distinct
candidates? is L structurally the weakest axis?) replicate robustly, while
*quantitative regime comparisons* (which condition has the most
individuated-looking candidates, whether forcing always raises D relative
to natural) do not, because the three seeds' natural regimes at this
snapshot are not equally close to a single, large, globally-aligned patch
to begin with.**

Concretely, `C` under the natural/uncontrolled regime alone:

| seed | C mean (no_control) | D mean (no_control) |
|---|---|---|
| 2 | 0.978 | 0.020 |
| 3 | 0.760 | 0.271 |
| 4 | 0.725 | 0.333 |

Seed 2's natural regime at this snapshot really is close to one big aligned
patch (task brief's motivating case); seeds 3 and 4's are not — their
natural-regime `D` is already substantial. This single fact explains most
of the downstream cross-seed differences reported above: seed 2 shows the
cleanest "forcing raises D above the natural floor" story (Q6) simply
because its natural floor is unusually low; seeds 3/4 don't have as much
room to rise, and in a few conditions (seed 3 `same_direction`, seed 4
`opposite`) forcing actually *collapses* the landscape toward *less*
variation than natural, not more (seed 3's `same_direction` reaching
`D=0.000` for **all 5000** candidates — apparently the forcing cascades to
essentially the whole 100-bird lattice for that seed/snapshot, not just the
targeted region, an extreme and genuinely new finding this full-landscape
pass surfaced that the fixed-`I0` archetype check could not have shown).

**What is stable:** the `C`-`G` sign pattern for `no_control` (always
negative) and `opposite` (always positive) (Q2); `corr(L,D)` always
non-positive (Q3); `L` always the smallest-dynamic-range, least
discriminative axis (Q4/Q7); `D_max` reaching 1.000 in the `opposite`
condition in every seed where it's meaningfully forced. **What is not
stable:** the sign of `corr(C,G)` for `shell_only`/`same_direction`/
`disordered`; whether any given forced condition has more or fewer
jointly-ideal candidates than natural (Q6); the absolute scale of `D` and
`C` under natural dynamics, which depends on how globally homogeneous that
particular seed's flock happens to be at the control-end snapshot.

## Q10: What caveats prevent these flock-specific metrics from being treated as a general definition of individuality?

1. **Model-specific causal horizon.** `G`/`L` are only as meaningful as the
   underlying nodewise predictive model's ability to capture this
   particular simulator's exactly-one-Moore-hop dependency structure;
   nothing here transfers to a system with a different (or unknown) causal
   structure without re-deriving the mask-cache machinery from scratch.
2. **Fixed `k`, fixed lattice.** Every candidate here has exactly 20 of 100
   fixed, non-moving lattice sites. Nothing in this stage's numbers
   addresses variable-size collectives, moving agents (Stage 7's actual
   target), or continuous state spaces.
3. **`E_near` is one specific choice of "the exterior."** The second
   Moore-ring definition of "nearby outside" is a modeling decision (task
   brief section 7's own explicit design choice), not derived from first
   principles; a different exterior definition could shift `D`/`H_E`
   numerically, though the qualitative archetype behavior
   (`METRIC_VALIDATION.md`) is unlikely to depend on the exact ring radius.
4. **`L`'s small dynamic range in this flock/model (Q4/Q7), confirmed
   across all three seeds** means at least one of the four axes is doing
   comparatively little discriminative work almost everywhere here — a
   warning against assuming all four axes are equally load-bearing in
   every context without checking, exactly the kind of check this stage
   was built to make possible.
5. **Regime-comparison conclusions are snapshot-specific, not flock-
   specific.** Q9 shows that "how much does forcing help" depends heavily
   on how globally homogeneous the *particular* natural-regime snapshot
   already was for that seed — a fact only visible because three seeds
   were checked instead of one. A single-flock study (or a study that only
   looked at seed 2) would have reported a cleaner, but less honest,
   version of this stage's conclusions.
6. **No claim of sufficiency.** The stage's own working hypothesis
   (`C` up, `G` up, `L` down, `D` up jointly characterizing "collective-like"
   candidates) is a pattern found by *inspection* of this flock's data
   across three seeds, not a theorem, and nothing here establishes it would
   hold for a different flock, a different simulator, or a biological
   system. Task brief section 2/30's caution — "not a universal definition
   of biological individuality or agency" — is taken at face value
   throughout.

## Final conceptual target, revisited

The working hypothesis stated in the task brief —
`collective-like candidates tend to occupy high-C, high-G, low-L, high-D
regions` — is **partially supported and partially complicated**, and the
complications are themselves the more interesting result:

- `D` behaves closest to the hypothesis and does most of the distinguishing
  work, in every seed.
- `C` is necessary but insufficient, and its own natural-regime baseline
  varies enough across seeds that "high C" alone means something different
  from one flock to the next.
- `G` reveals a real, seed-robust tension with `C` specifically under
  natural dynamics (negative correlation, all three seeds) and a
  seed-robust *alignment* with `C` specifically under the `opposite`
  archetype (positive correlation, all three seeds) — a genuinely
  regime-dependent relationship, not a fixed law in either direction.
- `L` contributes the least in this particular flock/model, consistently
  across every regime and seed checked.

The four quantities are not interchangeable and are not well summarized by
a single scalar — exactly the outcome the stage's four-separate-axes
design was built to be able to detect, rather than assume. Where the
three-seed check disagreed with the one-seed (seed 2) preview from
`METRIC_VALIDATION.md`, that disagreement is reported here as the more
important finding, not smoothed away.
