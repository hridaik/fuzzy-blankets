# PROTOCOL_6_9

Every threshold below was fixed before the experiment it governs was run.
`configs/protocol_6_9.yaml` is the machine-readable twin;
`logs/translation_gate_criteria_predeclared.txt` is the dated pre-declaration
of the feasibility gate. Nothing here was edited after any result was seen.

## 1. The firewall

Same rule as Stage 6.8, carried over unchanged:

> **Inference code may see bird IDs, positions, headings, past trajectories and
> its own interventions. It may not see the FOV rule, the effective interaction
> edges, `B_t^D`, the simulator's neighbour lists — or, new at this stage, the
> simulator's true centre trajectory.**

Inference-side: `code/identity_69.py`, `code/detect_69.py`. Evaluation-side:
`code/common_69.py`, `code/moving_flock.py`, and the runners. Enforced by
`tests/test_no_topology_leakage_69.py`.

The translating frame `Δ̂_t` is **estimated from observed positions and
headings only** — centroid displacement as initialization, then an
integer-pixel cross-correlation refinement of the fields. `MovingFlock` exposes
no centre trajectory and the tracker never asks for one.

## 2. The moving model (task brief §§25–26)

| kept unchanged | added |
|---|---|
| discrete four-state cardinal headings | positions `r_i ∈ [0, L)²` on a periodic torus |
| the active-inference heading update — the same `G_table`/`Risk_table`, the same `policy_posterior`, the same two categorical draws per bird per step | candidate partners within radius `R` (replacing the Moore neighbourhood) |
| the Stage 6.8 FOV rule `(r_j − r_i)·d_i ≥ 0` | `r_i(t+1) = r_i(t) + v·d_i(t+1) (mod L)` |

**No attraction, repulsion, centering or collision term is invented.** The
model's existing centering/collision-avoidance physics is
`flock_sim.model.SLOT_OVERRIDES` — the `compAexceps` switch-case setting
`R[o,s] = −ca` for particular (neighbour-direction, own-heading) pairs — and it
is reused faithfully by assigning each continuous neighbour to the Moore **slot
whose octant it falls in**:

`slot(i, j) = octant of (r_j − r_i)`, using `SLOT_VEC`'s own eight directions,
which are exactly the octant bisectors.

This is the only new modelling decision in Stage 6.9 and it introduces **no
free parameter**. Its consequence is that a bird approaching head-on from the
left still incurs the same `−ca` collision penalty it would have on the lattice.

| parameter | value | provenance |
|---|---|---|
| N | 400 | matches Stage 6.8's operating point |
| L | 24.0 | sets the density |
| R | **0.9** | mean realized live in-degree **8.9** in the clustered steady state — the Moore model's scale, which is what the brief requires. **Corrected**: the original R = 1.6 was recorded as "4.6 at uniform density, ~10.7 realized" and both figures were wrong; the true realized in-degree there is 21.2, about 3x the Moore scale. See `logs/translation_gate_criteria_predeclared.txt` ADDENDUM 4. Chosen by the declared rule "closest realized in-degree to 8", from uncontrolled phenomenology only |
| v | **0.28** | scaled with R to hold the neighbour-crossing time v/R = 0.31 fixed |
| R, v (superseded) | 1.6, 0.5 | the mis-specified pair; its data files carry `__SUPERSEDED` and its results are not claimed |
| β, ρ, ω | 1.0, 15, 3 | the **frozen Stage 6–6.8 values**, unchanged |

## 3. Detection (task brief §27)

The Stage 6.8 observer-facing logic with torus distance substituted for lattice
distance and **nothing else changed**: Gaussian spatial kernel × recent heading
agreement, then the same deterministic weighted Louvain
(`stage6_8_dynamic_interactions/code/louvain.py`, imported read-only).

| quantity | value |
|---|---|
| affinity window `W` | 6 steps |
| kernel σ, cutoff | 1.1, 3.3 |
| valid size | 3%–55% of the flock |
| lineage continuation score | `0.6·J(I_t, I_{t−1}) + 0.4·R_F` |
| continuation threshold | 0.30 |

No target-path information and no oracle interaction graph enters the detector.
Continuation deliberately mixes set overlap **and** co-moving field similarity,
so a group that keeps its members but loses its organization is not silently
credited (task brief §37, "material-only persistence").

## 4. The three identity notions (task brief §28)

| notion | quantity |
|---|---|
| material | `R_M(t) = |I_t ∩ I_{t0}| / |I_{t0}|` |
| lineage | `J(I_t, I_{t−1})` |
| functional, modulo translation | `R_F(t) = 1 − d(T_Δ̂ φ_t, φ_{t+1}) / d_norm` |

Fields, on a grid in the collective's own frame: half-width 8.0, pixel 0.5,
kernel σ 0.9. `φ_t = (ρ_t, m_t)`; the distance is half normalized density
mismatch plus half density-weighted orientation mismatch. `d_norm` is the field
distance between the collective and an independently drawn same-size random
subset at the tracking start — "how far apart are two unrelated groups of this
size" — and is observer-computable.

`R_F` is kept as a **full continuous similarity**, never reduced to a threshold.

Three distances are recorded separately, and the separation is the point:

| quantity | meaning |
|---|---|
| `D_world_frame` | the fields compared with **no translation removed** |
| `D_centroid_aligned_only` | after removing centroid displacement |
| `D_deform` | after removing the best bulk translation — what is left is deformation |

`D_world_frame ≫ D_deform` is how "bulk motion is not destruction" is
demonstrated rather than assumed (§31).

Shape/topology recorded alongside at every step (§32): size, spatial
components, area, density, aspect ratio, radius of gyration, centroid, bulk
speed, turnover, material retention.

## 5. The feasibility gate (task brief §33) — frozen before it was run

| id | brief's wording | test |
|---|---|---|
| T1 | persists for many steps | tracked duration ≥ 40 |
| T2 | translates by multiple interaction radii | net centroid displacement ≥ 3R |
| T3 | membership genuinely changes | final `R_M` ≤ 0.70 |
| T4 | co-moving similarity remains high | mean `R_F` ≥ 0.70 |
| T5 | nontrivial and spatially coherent | size in [0.03N, 0.55N] and ≤2 spatial components on ≥90% of steps |

**OUTCOME: the gate FAILS at the specified model.** Pass rate 0.00 over 40
episodes at R = 0.9; per-criterion rates T1 0.65, T2 0.80, T3 0.90, T4 0.38,
T5 0.03. T5 is the binding failure and it is a coherence failure, not a size
failure: size is in range on 100% of steps while the group is ≤2 spatial
components on only 40%. Stage 6.9 therefore stops before any steering
experiment. See `RESULTS_6_9.md`.

An episode passes iff all five hold; the **gate** passes iff the pass rate is
≥ 0.20 across screened seeds, i.e. the phenomenon is repeatable rather than one
lucky realization. Each episode's *longest tracked* collective is evaluated,
chosen by duration alone — never by displacement, turnover or any identity
score.

Outcomes that are explicitly **not** a pass, and how each is reported:
groups that translate with `R_M ≈ 1` are reported as **moving material
identity** and the constituent-replacement result is not claimed; if no
persistent translating collective emerges, the stage **stops**; if T4 fails
while T1–T3 hold, the collective is being destroyed and replaced rather than
transported, and is reported as such.

## 6. Reused unmodified

`python/flock_sim/*`; Stage 6.8's `louvain.py` (imported read-only), its
firewall convention, its affinity/community detector design, and its frozen
β/ρ/ω. Nothing in `python/`, `v1_mechanism_audit/`, `v2_interface_control/`,
`v3_refinement/`, `stage6_5/`, `stage6_6_collective_landscape/`,
`stage6_7_blind_boundary/` or `stage6_8_dynamic_interactions/` is modified,
re-run or restated by this stage.
