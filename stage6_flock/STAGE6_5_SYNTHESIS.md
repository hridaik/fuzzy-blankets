# STAGE6_5_SYNTHESIS.md

Concise summary of `stage6_5/`, the methodological-preparation track that
removes two Stage-6 conveniences (privileged knowledge of the interaction
graph; a permanently frozen interior) before Stage 7's moving-shepherding
model. Full evidence: `stage6_5/RESULTS_6_5.md`,
`stage6_5/boundary_inference/BOUNDARY_INFERENCE_RESULTS.md`,
`stage6_5/collective_identity/COLLECTIVE_IDENTITY_RESULTS.md`. Stage 6
itself (`STAGE6_SYNTHESIS.md` and everything it covers) is unchanged.

## Boundary inference

**Can we recover a useful boundary without privileged source knowledge?
Yes — a precision-1.0, recall-0.2-to-0.6 subset, which is functionally
almost as good as the true shell despite not matching it topologically.**
Across all 6 flocks tested (3 development, 3 held-out), the lattice-free
greedy inference pipeline never selected a bird outside the true `B^D`
(zero false positives), while recovering 18-58% of `B^D`'s true members.
That partial boundary's predictive excess loss sits within ~0.01 nats of
the oracle shell's, and 3-12x below same-size Fiedler or random exterior
draws, on every held-out flock. Recovery keeps improving with more data
(5 to 100 trajectories) with no sign of plateauing; a functionally useful
boundary is identifiable from remarkably little data (`N_traj=5` already
gives ~zero excess loss), while topological completeness needs
substantially more.

## Inference-to-control transfer

**Partially, and informatively so.** Applying the frozen (unmodified) V3
multicover controller to the inferred boundary beats null baselines
decisively on the one held-out flock where the comparison actually
discriminates (inferred 0.30 vs. Fiedler/random 0.00 success), ties nulls
on a flock easy enough that even random actuators succeed, and is
uninformative on a flock V3's own frozen record already showed to fail for
every arm including the oracle. Inferred-boundary control does not match
oracle-shell control's ceiling, but it is not equivalent to ignorance
either — it retains real, exploitable causal structure.

## Representation dependence

**Fixed-member, lineage, and functional descriptions usually agree on
whether an episode "succeeded," but almost never agree on what succeeded.**
Final retention of the original 20-bird interior ranged from 1.00 (fixed,
by definition) down to 0.06 (functional) on the same controlled episodes.
On a harder flock, the descriptions even disagreed on the headline verdict
itself. The physical interaction lattice never moves in this port, but the
representation-*relative* boundary moves constantly under the two adaptive
definitions — a limited, honest analogue of the moving-interface problem
Stage 7 must solve for real.

## Identity versus task

**Yes, adaptive definitions make apparent success easier, but by changing
who counts as "the collective," not by controlling the original one more
efficiently.** The clearest instance here is collapse, not substitution:
under closed-loop functional-identity control, the tracked "collective"
shrank to close to a single bird on average (mean final size 1.1 of the
original 20) while still registering nominal success. Adaptive controllers
used measurably fewer actuators at the same nominal success rate than the
fixed-material controller — a smaller job, not a better solution to the
original one. Reporting `H^\star`(retained) without `n_retained` alongside
it would have hidden this.

## Pathwise boundary

**Yes — a compact predictive interface survived all three representations
along the same control episode**, with one-step leakage staying in a
narrow ~0.01-0.014 nat band regardless of whether the tracked boundary was
flat (fixed identity, size 12 throughout), shrinking monotonically
(functional identity, 12 down to 4), or fluctuating sharply (lineage
identity, 12 up to 28 and back). Instability of membership did not imply
instability of screening in this data.

## Stage-7 implications

Stage 7's moving-shepherding model must supply what this port structurally
cannot: an interaction graph that changes because birds actually move in
space, not because a representation-choice re-labels a static graph's
relevant subset. Three concrete carry-overs from this stage:

1. **Keep the inference pipeline's architecture, not its numbers.** The
   screen -> shortlist -> greedy -> bootstrap pipeline and its
   lattice-free/evaluation-side split (enforced by an AST-level test here)
   generalize directly to a model where `B^D_t` is genuinely time-varying;
   the specific frozen thresholds (`delta_tol_frac=0.05`, `shortlist_k=20`)
   were fit to this port's sample sizes and effect sizes and should be
   re-frozen, not carried over as constants.
2. **Expect the recall ceiling to matter more, not less, once the graph
   truly moves.** Here, missing ~70% of `B^D`'s members still left enough
   signal to sometimes beat null control; with a graph that moves within a
   single episode, a stale or incomplete boundary estimate may go stale
   faster than a static one's recall gap costs.
3. **Any adaptive-identity mechanism in Stage 7 needs an explicit
   anti-collapse or anti-substitution safeguard.** This stage's clearest
   failure mode — a technically-successful controller that quietly steers
   almost no one — will be strictly easier to trigger, not harder, once
   membership can change for genuinely physical (not just representational)
   reasons.

## Success criteria, self-assessed

The task brief's stated bar for a successful Stage 6.5 does not require
exact shell recovery or perfectly separated identity definitions. Both
parts land closer to its "more interesting" outcome than its "strongest
possible" one: `\hat B \neq B^D` while `\Delta\ell(\hat B)\approx 0`, and
"same collective" is demonstrably representation-dependent in a way that
concretely changes both the measured boundary and the realized control
policy. Neither result required, or received, any tuning of the frozen V3
controller.
