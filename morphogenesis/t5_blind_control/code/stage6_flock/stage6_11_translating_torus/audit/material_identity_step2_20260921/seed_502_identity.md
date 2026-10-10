# Seed 502 — material-identity adjudication

## A. Identity

Qualification-time target: t=30, 21 members. `ForwardMaterialTrace611`
diverges from v1 **at t=32 — exactly Step 1's flagged zero-overlap
transition — and never reconverges for the rest of the 47-step trace**
(45 of 47 steps disagree with v1's displayed interior; only t=30, 31
agree). Two `unresolved` episodes (t=32–33, t=39–40 — genuine, brief loss
of a qualifying candidate, correctly held rather than switched) and one
split flag (t=41).

**Do not allow a later apparently-successful flock to inherit the original
task if material continuity was lost** (task's explicit instruction for
this seed): by end of episode the trace's continuing target has **50
members**; v1's displayed interior has **28** — a size mismatch alone rules
out these being the same object, confirming continuity was genuinely and
permanently lost at t=32, not merely relabeled.

## B. Physical behavior

Material-continuing target's heading fraction: 0.190 at qualification →
**0.125 at end of control (t=52)** → 0.208 at start of release → **0.100
at end of release (t=76)**. **No turn.** The material-continuing target's
alignment is flat-to-declining across the entire episode.

v1's own displayed trajectory, by contrast: 0.190 → 0.263 (end control) →
0.30 (release start) → **0.750 (end release)** — the large apparent rise
that generated the original "turn" label is entirely on the OTHER,
materially-unrelated population v1 jumped to at t=32.

## C. Comparison to legacy readouts

- **v1**: turn (0.19→0.75).
- **Step 1 ID-independent rescoring**: withdrew this seed — `beam_search
  _benchmark`'s v1 rise (0.10→0.28) was NOT corroborated by v2/material/
  field-direction (0.02/0.00/0.02) on a counterfactual re-simulated branch.
- **This task's forward material trace (actual recorded trajectory)**:
  **independently confirms no turn**, by a completely different method
  (pure material continuity on the real recorded run, no counterfactual
  re-simulation, no probabilistic tracker, no target-heading dependence
  anywhere in the scoring). This is the strongest cross-method agreement in
  this five-seed set: two unrelated approaches (Step 1's counterfactual
  ID-independent rescoring, and this task's real-run forward material
  trace) reach the same negative conclusion via entirely different
  evidence.

**No disagreement to explain** — this is the cleanest confirmation case:
seed 502's original "turn" label is, on this task's evidence, attributable
to the tracker latching onto a different, already-diverging population at
t=32, not to any real behavior of the originally-qualified material.

## Fields (per task §14)

- Identity: **identity-invalid** from t=32 onward (permanent material
  discontinuity, never recovers).
- Physical turn: **not demonstrated** in the material-continuing target
  (flat/declining alignment throughout).
- Intervention effect: **not demonstrated**.
- Actuator selectivity: **not demonstrated**.
