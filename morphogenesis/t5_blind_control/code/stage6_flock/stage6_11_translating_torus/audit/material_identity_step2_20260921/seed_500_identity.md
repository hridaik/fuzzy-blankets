# Seed 500 — material-identity adjudication (sanity/reference case)

## A. Identity

The qualification-time target (t=61, 33 members) has a valid forward
material continuation for the **entire** control (61–83) and release
(84–108) window: `ForwardMaterialTrace611` reports `continuing` at all 47
traced steps, **zero** disagreements with v1's own displayed interior over
that span (`data/forward_material_trace_seed500.csv`). No split, no merge,
no unresolved step.

The previously-misreported t=46→47 concern (Step 1's initial, later-corrected
observation) does not exist in this seed's data at all: t=46/47 fall in the
UNCONTROLLED, pre-qualification phase (qualification is at t=61), and Step
1 already established byte-identical membership at that transition. This
task's own reproduction check (`step2_reproduction_check.md`) reconfirms it.

**Real pre-control v1 branch switches** (documented in Step 1,
independently reconfirmed by this task's own replay tooling): t≈4, 21, 27,
39 — all before qualification. `ForwardMaterialTrace611` is only seeded at
qualification (t=61, per the task's "starting from the flock selected at
qualification" instruction) and so has no opinion about pre-qualification
switches by design — it cannot "avoid" them because it does not exist yet
during that span. What it DOES establish is that none of that
pre-qualification churn recurs during control/release: the entity handed
the target at t=61 is materially stable throughout everything that follows.

## B. Physical behavior

Material-continuing target's heading trajectory: flat and low throughout —
0.12 at qualification, 0.07 at end of control, 0.06 at start of release,
0.00 at end of release. **No turn, no persistence.** Identical to v1's own
reported trajectory (since identity never diverges).

## C. Comparison to legacy readouts

v1, v2 (Step 1), frozen original material, field-direction, and this
task's forward trace **all agree**: no turn, no controllability
demonstrated. No disagreement to explain for this seed.

## Fields (per task §14)

- Identity: **identity-valid** throughout control and release.
- Physical turn: **not demonstrated**.
- Intervention effect: **not demonstrated** (trigger has zero true direct
  causal parents, Step 1).
- Actuator selectivity: **not demonstrated** (same reason).
