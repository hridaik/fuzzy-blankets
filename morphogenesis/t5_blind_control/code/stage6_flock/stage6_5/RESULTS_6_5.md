# RESULTS_6_5.md

Full results for both Stage 6.5 parts. This document indexes and cross-links
the two part-level results files; it does not restate every number, which
live (with their generating JSON) in `boundary_inference/
BOUNDARY_INFERENCE_RESULTS.md` and `collective_identity/
COLLECTIVE_IDENTITY_RESULTS.md`.

## Part 1-2: observational boundary inference (Hard Gate A)

See `boundary_inference/BOUNDARY_INFERENCE_RESULTS.md` for the full
writeup. Headline:

- The greedy, lattice-free inference pipeline recovers a **precision-1.0,
  recall-0.18-0.58** subset of the true `B^D` across all 6 flocks tested (3
  dev + 3 held-out) — zero false positives observed anywhere.
- This partial-recall boundary achieves **predictive excess loss within
  ~0.01 nats of the true `B^D`**, while size-matched Fiedler and random
  baselines sit 3-12x higher, on every held-out flock.
- Boundary recovery (Jaccard) improves steadily from `N_traj=5` to 100 with
  no sign of saturating; predictive sufficiency is reached almost
  immediately (`N_traj=5`).
- Controlling through the inferred boundary, using the frozen V3
  multicover law unmodified, **clearly beats null baselines on the one
  held-out flock where the comparison is discriminating** (seed 20:
  inferred 0.30 vs. Fiedler/random 0.00), ties nulls on an easy flock
  (seed 17, where even random succeeds), and is uninformative on a flock
  V3's own record already showed to be hard for every arm (seed 18).

## Part 3-6: collective identity

See `collective_identity/COLLECTIVE_IDENTITY_RESULTS.md` for the full
writeup. Headline:

- Material, lineage, and functional identity usually agree on the
  headline success verdict for the same physical trajectory, but describe
  wildly different underlying membership (final retention from 1.00 down
  to 0.06) — and on a harder flock (seed 4), they **disagree on the
  headline verdict itself**.
- The identity-gaming failure mode observed here is **collapse**, not
  substitution: the functional definition's "collective" shrank to a
  near-single-bird remnant under closed-loop control (mean final size
  1.1 on flock 2) while still registering nominal success — `n_retained`
  must be reported alongside `H^\star`(retained), not instead of it.
- Adaptive identity-based control uses measurably fewer actuators than
  fixed-material control at the same nominal success rate, but this
  reflects controlling a smaller/different group, not a more efficient
  interface for the original one (membership turnover in the hundreds
  over a 40-step episode under the lineage definition).
- A compact predictive interface (pathwise leakage ~0.01-0.014 nats)
  survives all three representations, even as the functional definition's
  boundary shrinks from 12 to 4 members and the lineage definition's
  fluctuates between 12 and 28 — instability of *membership* does not
  imply instability of *screening*.

## Cross-cutting observation

Both parts land on the same shape of result: **the naive "gold standard"
(exact `B^D` recovery; a permanently fixed `I_0`) is not what makes control
work.** A precision-1.0-but-incomplete boundary screens almost as well as
the true one; a collective whose membership is churning by the dozen per
step can still be surrounded by a small, stable-enough predictive interface
at each instant. What breaks is not the boundary concept but the *identity*
concept when left unconstrained — a flexible enough definition of "the
collective" can make almost anything look like success.

See `../STAGE6_5_SYNTHESIS.md` for the six-question summary and Stage 7
implications.
