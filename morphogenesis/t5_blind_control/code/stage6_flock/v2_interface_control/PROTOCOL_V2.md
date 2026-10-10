# PROTOCOL_V2.md — frozen experimental protocol for V2 (interface-based control)

**SHA-256 of `configs/protocol_v2.yaml` at freeze**:
`23fd16f9da67a499ba6335de552939ab3c8ded2bf8d1e6c9faeed3036ae57272`
(see `logs/protocol_v2.sha256`).

This file is frozen **after** the mechanism audit (`../v1_mechanism_audit/`)
and **before** any V2 actuator-rule comparison or multi-flock replication was
run. Task success/integrity/persistence thresholds, the model, and the
spectral pipeline are copied **unchanged** from `PROTOCOL_V1a` (see
`../v1_mechanism_audit/V1_RECORD_AUDIT.md` section A2 for why the frozen
protocol V1 actually executed deserves that name). Nothing here was retuned
in response to a V2 result — the config file above was hashed before
`code/` was run.

## What the mechanism audit established, carried into this freeze

1. A bird's next heading depends only on its Moore-lattice neighbors — a
   structural fact derived from `flock_sim.active_inference.compute_G`
   (`v1_mechanism_audit/MECHANISM_AUDIT_RESULTS.md` Part B), verified
   empirically to be an EXACT statistical Markov blanket for the frozen core
   (0.0000 excess predictive log-loss vs. ground truth, Part H).
2. The paper's/V1's spectral (Fiedler) boundary `B^F` is a small, often
   incomplete, subset of this true interface (`B^F_0 ⊂ B^D_0` on the
   canonical flock; mean Jaccard 0.12 over a small ensemble) and is not a
   statistically adequate substitute for it (+0.032 nats excess log-loss,
   Part H) — Fiedler-boundary-only control fails completely
   (`p_success=0.00`, Part D).
3. Forcing the FULL, correctly-identified dynamical shell `B^D_0` succeeds
   almost perfectly (`p_success=0.96`, matching all-80-exterior-bird forcing)
   using only 12 of 100 birds, and a sparsified 9-bird subset of that same
   correct pool (found by greedy search restricted to it) already reaches
   `p_success=0.90` — dramatically better than V1's best result at comparable
   actuator count (`p_success=0.00` at k=6, using the wrong candidate pool).
4. `B^D_t = B^D_0` for every `t` within a single control episode in this
   specific port, because birds occupy fixed lattice sites and only their
   heading (Potts-spin) state evolves — the "dynamical shell" cannot move
   *within an episode*. What DOES vary, and is exercised by the Part L
   replication below, is that **different flocks have different `I0`, hence
   different `B^D_0`** — so "compute the interface from structure, not from a
   fixed bird-ID list" remains a live, testable idea across flocks, even
   though it is not literally "moving" within one flock's control window.
   This is a genuine scope limitation relative to the task brief's
   moving-interface framing, stated plainly rather than glossed over (see
   `RESULTS_V2.md` for how this plays out).
5. `P(success & integrity)` was 0.000 for every exterior-only arm in the
   mechanism audit, despite near-perfect target-heading success, because the
   frozen `C_{I0}(t)>=0.8`-at-every-timestep integrity bar appears to
   structurally conflict with ANY propagation-based (as opposed to
   direct-override) steering mechanism. **This protocol does not loosen that
   criterion.** It is carried forward unchanged and reported honestly
   alongside success, exactly as the mechanism audit reported it. An
   additional, clearly-labeled RECOVERY diagnostic (integrity checked only in
   a trailing window ending at `t0+T_u`, not the whole control window) is
   also reported, side by side, never as a replacement.

## The V2 control policy (frozen)

At the flock's own `t0` (found by the unchanged Phase-2A selection rule),
compute `B^D_0(I0)` directly from `lattice.neighbor_ids`, exactly as in the
mechanism audit. Choose `k = ceil(0.75 * |B^D_0|)` actuators (the fraction
that first crossed `p_success>=0.8` on the canonical flock — tested, not
re-derived, on each replication flock) via one of four predeclared,
transparent rules (`configs/protocol_v2.yaml`'s `actuator_selection_rules`):

- **Rule A (degree)**: highest number of edges into `I0`.
- **Rule B (leverage)**: highest individual k=1 empirical response, from a
  predeclared n=20-replicate per-flock sweep restricted to `B^D_0`.
- **Rule C (patch)**: a single spatially/graph-connected patch within
  `B^D_0`'s own induced subgraph.
- **Rule D (random)**: uniform random subset of `B^D_0` (explicit control).
- Reference arms: full shell (`k=|B^D_0|`) and baseline (`k=0`).

Force the chosen set toward `h_star` for `t in [t0, t0+T_u)`, exactly as
`make_pulse` already implements (unchanged from `protocol_v1`). Release and
observe for `T_r=20` more steps, exactly as before.

## Replication (frozen before running)

The first 10 seeds (starting from 0, numeric order) that satisfy the
unchanged Phase-2A selection rule within `nt_search=60` — not cherry-picked,
not re-drawn if a flock turns out to be "hard." 30 replicates per
(flock x rule) condition (development scale, logged as such). No flock is
discarded from the reported results regardless of outcome.

## What would constitute a V2 failure, stated in advance

- If the fixed fraction `0.75` derived from the single canonical flock
  systematically fails to reach `p_success>=0.5` on a majority of the other 9
  replication flocks, that is reported as a genuine generalization failure of
  the fraction rule — NOT an occasion to re-tune the fraction inside this
  session.
- If Rule D (random) performs statistically indistinguishably from Rules A-C,
  that would indicate the specific *within-shell* selection rule matters less
  than simply drawing from the correct shell at all — reported as such, not
  hidden.
- If `P(success & integrity)` remains ~0 even under the RECOVERY diagnostic,
  that is reported as a persisting, unresolved tension between the frozen
  integrity criterion and any propagation-based control mechanism — grounds
  for a future `protocol_v3` to reconsider the criterion itself, not for this
  protocol to quietly redefine it.
