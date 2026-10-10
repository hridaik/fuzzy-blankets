# Final Translating-Flock Closure — State Manifest

Same qualification rule as Stage 6.12/6.12B/6.12C, reused unmodified
(`code/world_sampling_closure.py`, logic reproduced from
`stage6_12C_kinematic_contact_confirmation/code/world_sampling_612c.py`):
material lineage exists (`ForwardMaterialTrace611`, Jaccard≥0.30 frozen
rule), target size in `[20,80]`, `DWELL_WINDOW=20` steps of clean
continuation (no split/merge flag) immediately preceding qualification,
torus-aware displacement ≥ `3.0×R_PRIMARY=2.7`, `h_star =
ROT_CCW[bearing_to_cardinal(...)]`. Selection depends only on the trace's
own history up to `t0` — never on any closure-experiment outcome (which
does not exist at sampling time).

Fresh seed range **64200–64799**, disjoint from all prior Stage 6.x work:
seeds 500–504 (Stage 6.11), 61200–61399 (Stage 6.12), 62200–62399 (Stage
6.12B), 63000–63499 (Stage 6.12C pilot 63000-63099 + confirmatory
63200-63499). 8/8 seeds tried qualified on the first attempt
(64200–64207) — see `logs/world_sampling_closure.log`; total sampling
wall time 70.1s.

| state_id | seed | t0 | size | h_star | displacement |
|---|---|---|---|---|---|
| sclosure_00_seed64200 | 64200 | 66 | 28 | 3 | 3.29 |
| sclosure_01_seed64201 | 64201 | 80 | 34 | 1 | 3.63 |
| sclosure_02_seed64202 | 64202 | 79 | 28 | 0 | 4.69 |
| sclosure_03_seed64203 | 64203 | 38 | 36 | 1 | 2.72 |
| sclosure_04_seed64204 | 64204 | 49 | 41 | 0 | 2.80 |
| sclosure_05_seed64205 | 64205 | 40 | 25 | 0 | 2.96 |
| sclosure_06_seed64206 | 64206 | 33 | 25 | 2 | 3.59 |
| sclosure_07_seed64207 | 64207 | 146 | 56 | 2 | 4.01 |

## Organizational-class availability at t0 (Closure A/B)

Computed directly from the simulator's `live_edges(r0, z0)` (directed,
FOV-gated), not approximated. Classes: A=core_member, B=boundary_member,
C=live_exterior_parent (∩ nearest-20 pool), D=near_exterior_non_parent.

| state_id | core (A) | boundary (B) | live parent (C) | non-parent (D) |
|---|---|---|---|---|
| sclosure_00_seed64200 | 28 | 0 | 0 | 20 |
| sclosure_01_seed64201 | 34 | 0 | 0 | 20 |
| sclosure_02_seed64202 | 28 | 0 | 0 | 20 |
| sclosure_03_seed64203 | 35 | 1 | 1 | 19 |
| sclosure_04_seed64204 | 41 | 0 | 0 | 20 |
| sclosure_05_seed64205 | 22 | 3 | 1 | 19 |
| sclosure_06_seed64206 | 21 | 4 | 6 | 14 |
| sclosure_07_seed64207 | 56 | 0 | 0 | 20 |

**Disclosed finding, not a bug**: at the single instant t0, 5/8 states have
ZERO boundary members and ZERO live exterior causal parents. At `R_PRIMARY
= 0.9`, `mf.expected_degree() ≈ 0.77` — the mean-field expected live degree
is well under 1, so most instants have no live edge crossing any given
boundary even though the flock is visibly cohesive (verified:
`n_live_edges` in the full 400-bird graph is 1100–4200 per state, i.e.
edges are common in aggregate, just not always incident on this particular
target's boundary at this particular instant). Per the task spec ("do not
reject a qualifying state because one actuator class is inconvenient — if
a class is absent in a state, mark that class/state unavailable and
proceed"), Closure A/B sampling proceeds with whatever classes are
non-empty per state; class B/C comparisons are necessarily thinner (8
boundary-class and 8 live-parent-class actuators total across all 8
states) than class A/D comparisons (24 core, 20 near-non-parent actuators
before per-state 3-cap sampling). This sparsity is itself part of the
Closure A/B finding, not a design flaw — see
`ORGANIZATIONAL_ROLE_RESULTS.md`.
