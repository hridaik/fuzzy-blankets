# PROTOCOL_6_5R.md

Frozen refinement protocol, written incrementally: each part's section is
frozen (and hashed) strictly before that part's held-out/closed-loop numbers
are computed, mirroring `../PROTOCOL_6_5.md`'s own convention. The
machine-readable copy is `configs/protocol_6_5r.yaml`. Nothing in a part's
section changes after that part's data files (named in its `frozen_before`
list) exist.

## Part A — causal redundancy (Hard Gate A)

See `configs/protocol_6_5r.yaml`'s `part_a_causal_redundancy` block for the
exact machine-readable values. Summary:

- Reuses the 3 held-out flocks already frozen in
  `stage6_5/boundary_inference/data/held_out_evaluation.json` (seeds 17, 18,
  20) and their recorded `B_hat`/`B^D` verbatim — the inference pipeline is
  **not** re-run (A1).
- The core metric (`D_j^do`, and the stress-tested `Delta-ell`) is computed
  **exactly**, in closed form, not by Monte Carlo — see
  `causal_redundancy/code/exact_intervention.py`'s module docstring for the
  derivation (the ported generative model's action-to-heading map does not
  depend on the current state; the policy posterior driving action choice
  depends on the current state only through each bird's lattice-neighbour
  headings). This is cross-checked against literal simulator rollouts in
  `causal_redundancy/tests/test_closed_form_matches_rollout.py` (2000
  replicates, tolerance 0.06 on per-bird next-heading frequency) — both
  pass.
- 30 fresh held-out checkpoint states per flock (disjoint seed offset from
  every Part-1 trajectory), all 3 alternative headings per (state, bird),
  perturbed independently across the three A3 classes (all of `B_hat`, all
  of `B^D \ B_hat`, a fixed 10-bird sample of `E^D`).
- `Delta-ell`/`Delta_shift` are computed with the SAME exact-cross-entropy
  method under both natural and intervened states, on the SAME 30-checkpoint
  set, so the two are directly comparable — this is a new, exact
  operationalization for this refinement, not identical to (but consistent
  with) Part 1's own empirical validation-split `Delta-ell`.

**Frozen at**: after `causal_redundancy/tests/` passed (validating the
closed-form derivation), **before** `causal_redundancy/data/causal_redundancy.json`
existed. Hash recorded in `logs/protocol_6_5r_part_a.sha256`.

## Part B — control generalization (Hard Gate B)

See `configs/protocol_6_5r.yaml`'s `part_b_control_generalization` block.
Summary:

- Scans **new** seeds only, starting at 41 (first seed after V3's held-out
  pool of 17-40), predeclared max scan range 41-140 (100 candidates),
  stopping once 12 discriminating flocks qualify or the range is exhausted.
- Discriminating criterion frozen before any inferred-controller run:
  `P_oracle(success) >= 0.7` and `P_random(success) <= 0.3`, both via the
  frozen `evaluate_arm` harness. The screening-phase random null is matched
  to the **oracle's** own actuator budget; a cheap **20-replicate** screen is
  used for this scan (explicit user direction, 2026-09-06 — cheaper than the
  V2/V3 convention's `N_REP=30` since this is a pass/fail filter applied to
  ~50+ candidates, not a headline number).
- For every qualifying (discriminating) flock: fresh observational
  trajectories, the frozen (unmodified) inference pipeline re-run on them to
  get `B_hat`/`Ghat`, then a **50-replicate** (explicit user direction,
  2026-09-06) evaluation of all four controllers (Oracle / Inferred /
  Fiedler / Random, the last matched to the **inferred** controller's own
  budget) — a fresh, statistically independent replicate range from the
  screening phase.
- Aggregation resamples **flocks**, not replicates, for the headline
  bootstrap CI (B6's explicit instruction).

**Frozen at**: before the seed scan ran. Hash recorded in
`logs/protocol_6_5r_part_b.sha256`.

## Part C — identity stability (Hard Gate C)

See `configs/protocol_6_5r.yaml`'s `part_c_identity_stability` block.
Summary:

- Deliberately smaller than Part A/B (explicit user direction, 2026-09-06):
  **5 "informative" flocks** — the first 5 of V3's frozen `DEV_SEEDS` in
  frozen seed order (2, 3, 4, 8, 9), chosen by seed-list position, not by
  which flocks show interesting identity behavior (that would be exactly the
  kind of post-hoc selection Part G prohibits) — for the evaluation-only
  passes (C1 jitter analysis, C5 representation re-evaluation).
- An even smaller **3-flock** subset (2, 3, 4 — Stage 6.5's own original
  Part 4/5 flocks) for the closed-loop proof of concept (C7/C8), at
  **30 replicates** per flock per representation (explicit user direction,
  2026-09-06 — up from Stage 6.5's own `N_REP=8`).
- `lambda_T` (temporal-turnover regularization weight) is chosen from a
  predeclared grid, calibrated **only** on uncontrolled/baseline
  continuations of the 5 informative flocks (never on controlled-episode
  outcomes), by the transparent criterion in the yaml block above.
- The identity-validity envelope (`S_I` lower bound, `J_min`) is likewise a
  fixed percentile of the same baseline-continuation distributions, not
  fit to controlled-episode outcomes.

**Frozen at**: before any baseline-continuation calibration number was
computed. Hash recorded in `logs/protocol_6_5r_part_c.sha256`.
