# Seed 501 — material-identity adjudication

## A. Identity

Qualification-time target: t=30, 30 members. `ForwardMaterialTrace611`
reports `continuing` at all 47 traced steps — no `unresolved`, no `dead`.
**Two split flags** (candidate ambiguity events, flagged not silently
resolved) but no merge flags.

**The originally-qualified flock DOES have a continuous material path
through the v1 zero-overlap transition at t≈32.** At t=32, v1's displayed
interior jumps to an unrelated 23-member candidate (0 overlap with the
material trace's own continuing 33-member target) — this is Step 1's
flagged zero-overlap event, reconfirmed here bird-ID-exact. Crucially,
`ForwardMaterialTrace611` does **not** follow v1's jump: it stays on a
materially-overlapping candidate (t=32: 33 members, jaccard=0.388 vs. the
t=31 target — passes the 0.30 gate; a genuine split is flagged here, two
candidates both clear the gate, the larger-retained-count one is chosen).
This continues for 4 steps (t=32–35) while v1's own displayed interior is
tracking the unrelated population.

**At t=36, v1's own tracker independently arrives back at the SAME
population the material trace had been tracking the whole time** (both
report a 46-member set, zero disagreement from t=36 onward through release,
t=77). v1's t=32 jump was, in this specific seed, a **transient detour that
self-corrected**, not a permanent subject change.

## B. Physical behavior

Material-continuing target's heading fraction: 0.233 at qualification →
0.759 at end of control (t=52) → 0.759 at start of release → **0.971 at
end of release (t=76)**. This is **numerically identical to v1's own
reported trajectory** at every sampled endpoint (both trackers agree by
t=36 onward and stay agreed).

**The material-continuing target does turn, and the turn persists through
release.**

## C. Comparison to legacy readouts

- **v1**: turn (0.23→0.97).
- **v2 / original_material / field_direction (Step 1)**: withdrew this
  seed — the specific branches examined in `branch_adjudication_611
  __seed501.json` (`beam_search_benchmark`, `matched_random_blind_exterior`)
  showed v1-only rises NOT corroborated by material/field-direction. Those
  branches are **different simulated trajectories** (fresh-CRN re-runs from
  the t0=30 trigger under alternative actuator policies), not a replay of
  the actual recorded run — so their v1-vs-material disagreement is not
  directly comparable to this task's finding, which replays the **actual
  recorded trajectory**.
- **This task's forward material trace (actual recorded trajectory)**:
  agrees with v1 at every checked endpoint, and demonstrates the brief
  t=32–35 divergence self-corrects.

**Disagreement explained**: Step 1's rescoring withdrew seed 501 based on
COUNTERFACTUAL branches (re-simulated from the trigger state under
different, fresh-CRN policies) where v1 itself behaved erratically on those
specific alternate rollouts. This task's finding concerns the ACTUAL
recorded run only. **These are not contradictory findings about the same
object** — they are findings about different objects (the real run vs.
counterfactual re-simulations), and the apparent tension resolves once that
distinction is made explicit. This task does not overturn Step 1's
counterfactual-branch analysis; it adds a separate, real-run-only finding
that the real run's own material identity is more defensible than the
counterfactual branches' behavior might have suggested in isolation.

## Fields (per task §14)

- Identity: **identity-valid** throughout control and release (after a
  4-step transient v1-vs-trace disagreement that does not affect the
  trace's own continuity judgement).
- Physical turn: **demonstrated** (0.23→0.97, persists to release, in the
  materially-continuing target).
- Intervention effect: **not demonstrated** — this task did not re-run any
  actuator-ablation comparator against the material trace; Step 1's
  evidence-gated repaired branches all abstained at this trigger (S=∅).
  Separate question from identity, per task's explicit instruction not to
  conflate them.
- Actuator selectivity: **not demonstrated**, same reason.
