# PLAN.md — Stage 6.9: translating-collective pilot

Planning document, written **after the Stage 6.8 gate was recorded in
`../stage6_8_dynamic_interactions/RESULTS_6_8.md` §13** and before any Stage
6.9 number was produced. The only prior computation is a moving-agent
feasibility prototype run in a scratch directory to check that the minimal
extension does not simply disperse; its outcome is restated in §"What the
prototype already showed" below and is used for nothing else.

## The question

**Can a collective retain functional identity in a translating frame while its
material membership changes?**

That is a *hypothesis to be tested*, not an assumption. The interesting regime
is the conjunction

    R_M decreases substantially   AND   R_F remains high

— the physical bird identities are replaced while the spatially organized
collective persists in its own moving frame. If groups translate but keep
essentially the same members (`R_M ≈ 1` throughout), that tests **moving
material identity**, not constituent-independent functional identity, and it
will be reported as such and **not** claimed as the result.

## What Stage 6.9 is not

- **Not a manufactured traveling wave.** No ad-hoc wave-propagation rule is
  added on the fixed lattice. A heading wave over stationary birds would be a
  useful *pattern* benchmark, but it would then have to be called a traveling
  state pattern, not a translating flock, and Stage 6.9 does not take that
  route at all.
- **Not a redesigned flock.** No attraction, repulsion, centering or collision
  term is invented. The model's existing centering/collision-avoidance physics
  lives in `flock_sim.model.SLOT_OVERRIDES` (the `compAexceps` switch-case that
  sets `R[o,s] = -ca` for particular neighbour-direction/own-heading pairs) and
  is reused faithfully by assigning each continuous neighbour to the Moore slot
  whose octant it falls in. **If the minimal moving extension disperses and the
  existing terms cannot support localized groups, that is the pilot outcome and
  the stage stops there** rather than being rescued by new terms.
- **Not a new detector.** Candidate detection is the Stage 6.8 observer-facing
  logic with torus distance substituted for lattice distance, and the same
  deterministic weighted Louvain. No target-path information and no oracle
  interaction graph may enter it.
- **Not a claim about identity in general.** See "Interpretation rules" below.

## Minimal moving-agent extension (task brief §25)

Kept unchanged: discrete four-state cardinal headings; the existing
active-inference heading update (the same precomputed `G_table` / `Risk_table`,
the same `policy_posterior`, the same two categorical draws per bird per step);
the Stage 6.8 FOV rule.

Added, and only this:

- positions `r_i(t) ∈ [0, L)²` on a periodic torus;
- candidate partners are birds within a local radius `R`;
- `r_i(t+1) = r_i(t) + v · d_i(t+1)  (mod L)`, small fixed `v`.

Visibility still requires `(r_j − r_i) · d_i ≥ 0`, so geometry *and* heading
determine the directed graph, exactly as at Stage 6.8 L2. `R` is chosen so the
expected local degree is on the scale of the Moore model's 8.

## Three identity notions, tracked separately (task brief §28)

| notion | quantity |
|---|---|
| **material continuity** | `R_M(t) = |I_t ∩ I_{t0}| / |I_{t0}|` |
| **lineage continuity** | `J(I_t, I_{t−1})` |
| **functional continuity modulo translation** | `R_F(t) = 1 − d(T_Δ̂ φ_t, φ_{t+1}) / d_norm` |

with `φ_t = (ρ_t, m_t)` a density and local-orientation field centred on the
collective's current frame. `R_F` is kept as a full continuous similarity, not
a threshold. The translating frame `Δ̂_t` is estimated **online** — centroid
displacement as initialization, then local cross-correlation refinement — and
**the simulator's true centre trajectory is never used** (§29).

Deformation is measured *after* removing the best bulk translation
(`D_deform(t) = d(T_Δ̂ φ_t, φ_{t+1})`), so bulk motion can never be mistaken
for destruction (§31), and shape/topology is recorded alongside — size, spatial
components, area, density, aspect ratio, radius of gyration, centroid, bulk
velocity, order parameter — so a thin chain or a fragmented remnant cannot be
labelled the same collective merely because its centroid moves smoothly (§32).

## Order of operations, with a hard gate

1. **Uncontrolled dynamics first.** Characterize the moving model with no
   steering at all.
2. **Translation feasibility gate (§33).** Proceed to any control experiment
   *only if* there are repeatable episodes where a detected collective persists
   many steps, translates by multiple interaction radii, **genuinely changes
   membership**, keeps co-moving functional similarity high, and stays
   nontrivial and spatially coherent. If groups translate with `R_M ≈ 1`, that
   is reported clearly and the constituent-replacement result is not claimed.
   If no persistent translating collective emerges, **stop** — a prechosen
   moving cluster will not be forced into existence and called emergence.
3. **Boundary inference in the translating frame (§34)**, only if the gate
   passes: the same hierarchy `I_t → B̂_t^pred → B̂_t^causal`, with turnover
   measured both in world coordinates and in the co-moving frame.
4. **Guidance experiment (§35)**, only after natural detection and tracking
   work, and only at a scale where the task is achievable — Stage 6.8's control
   experiment was infeasible at its own scale even for the oracle arm, and that
   lesson is inherited rather than repeated.

## Success must be conjunctive (§36)

    S_full = S_path ∧ S_functional_identity ∧ S_nondegenerate ∧ S_boundary

Material retention is **reported but not required to stay high**. Low material
retention with high functional continuity is the phenomenon of interest, not a
failure.

## Failure cases that must be detected explicitly (§37)

- **destruction + replacement** — the original pattern disappears and a
  different coherent group appears near the target (task maybe yes, identity
  no);
- **splitting** — one collective becomes two; a lineage branch event is marked
  and the child nearest the target is *not* silently chosen;
- **shrink-to-win** — the tracker must not collapse onto a few convenient
  birds; a natural-regime validity envelope is enforced;
- **material-only persistence** — the same birds stay together but the
  functional/spatial organization is lost; reported separately.

## Interpretation rules (§40)

No claim of a universal definition of identity is made. The experiment
establishes only whether *this* decomposition can distinguish **same
constituents** from **same moving organization**. Material continuity, lineage
continuity, and functional continuity modulo translation are kept separate
throughout and are never summed into a single "identity score".

## What the prototype already showed

A scratch feasibility prototype (before this document, used only to decide
whether the stage was worth opening) established that the minimal moving
extension **does not disperse**: with `N = 400`, `L = 24`, `R ∈ {1.6, 2.0}`,
`v ∈ {0.2, 0.3, 0.5}` the flock forms clusters and polarizes (0.61–1.00), with
mean degree 9–21. It also flagged the central risk, which this stage must
confront rather than hide: at high polarization every bird translates
identically, the configuration is frozen in the co-moving frame, and `R_M`
stays at ~1.0 — the exact degenerate case the brief warns against. Whether a
regime exists with real translation *and* real constituent turnover is the
question the feasibility gate decides.

## Additive

Nothing in `python/`, `v1_mechanism_audit/`, `v2_interface_control/`,
`v3_refinement/`, `stage6_5/`, `stage6_6_collective_landscape/`,
`stage6_7_blind_boundary/` or `stage6_8_dynamic_interactions/` is modified by
this stage. Stage 6.8's inference modules are imported read-only.
