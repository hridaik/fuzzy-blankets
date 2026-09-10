# Stage 6.11 — Translating active-inference flock on a torus

**Pre-registration.** Written before any 6.11 run. Sections M–V are the task
brief; the operationalizations below are what this stage will actually execute.
Additive: Stages 6–6.10 are read-only.

**Gate.** This stage begins only after Stage 6.10 establishes the complete
fixed-lattice loop (detect → track → steer → release, identity-scored). That
gate is **met** — see `../stage6_10_emergence_adaptive_control/RESULTS_6_10.md`.

**Question.** Can the same framework detect, track and steer a spatially
translating collective whose *material membership changes*?

---

## M. Audit the moving model before changing it

Stage 6.9 already built a moving-agent extension (`moving_flock.py`). **Audit it
first; do not add forces that already exist.**

Verify whether effective versions of these are present, and name where:

| ingredient | present? | where |
|---|---|---|
| alignment / heading matching | to determine | |
| centering / cohesion | to determine | |
| collision avoidance / separation | to determine | |

Deliverable: `logs/moving_model_audit.txt`, one entry per ingredient, citing the
term in code. If an ingredient is genuinely absent, it is added **once**, and
recorded as an addition rather than folded in silently.

*The goal is not to engineer a trajectory. It is to ensure a moving flock has
the generic physical ingredients a moving flock requires.*

## N. Prevent degree from automatically causing policy saturation

Stage 6.9's failure mode was diagnostic: R = 1.6 gave realized in-degree 21.2
against a Moore scale of 8, producing 77% policy saturation and a 1-of-47 causal
interface. Raw-sum social evidence makes decision gain a function of degree.

Implement an explicitly labelled **degree-normalized** variant:

$$G_i^{\text{social}} \propto \frac{1}{|N_i|}\sum_{j \in N_i} g_{ij}$$

- Keep the raw-sum version as a comparator; both selectable, neither deleted.
- **This is a modelling assumption, not a bug fix**, and is presented as one.
- Purpose: separate *interaction range / spatial cohesion* from *overall
  decision gain / certainty*, which the raw sum conflates.
- **Verification:** at the original local degree, the normalized variant must
  approximately preserve the existing operating scale. Recorded as a numeric
  check, not asserted.

## O. Independently scan interaction radius and speed

**Do not preserve v/R automatically.** Two-dimensional scan over (R, v).

Report per cell: realized degree · policy saturation · collective persistence ·
clumpness · thingness profile (C,G,L,D) · translation distance · material
turnover · co-moving identity · fragmentation · weak-cue susceptibility.

**Regimes are selected using uncontrolled phenomenology only.** Criteria are
predeclared in `logs/regime_selection_predeclared_611.txt` before the scan is
read, following the Stage 6.10 pattern.

## P. Natural-emergence gate first

Start from **unstructured random positions and headings**. Search for episodes
where a translating clump emerges naturally. A qualifying episode is:

visually localized · C/G/L/D thing-like · clump-like · persistent · translating
several interaction radii · materially turning over · high co-moving functional
similarity · non-fragmented · non-saturated

If a reasonable frequency exists, **use this regime** and skip Q.

## Q. Only if spontaneous emergence is too rare — brief nucleation cue

**Do not directly select bird IDs.** Introduce a temporary *Eulerian* field:

$$F(x,t) = A\,\exp\!\left[-\frac{\|x-c(t)\|^{2}}{2\sigma^{2}}\right] d_{\text{seed}}$$

It modifies the local heading preference of *whichever birds occupy the region*.

- The identity/boundary inference system **must not receive** $F$, $c(t)$, or
  the affected set. Enforced by the firewall pattern used in Stage 6.8.
- Cue runs for a short nucleation interval, then $F = 0$.
- **The experiment begins after removal.** A successful induced regime requires
  the collective to persist on its own for a substantial interval afterwards.
- Label: **nucleated self-maintaining translating collective** — never
  "spontaneous emergence".

## R. If persistence still requires continuous drive

A continuously moving hidden field may be used as a final **driven identity
benchmark**, labelled **driven translating collective**, and used for
detection/identity tests only.

- **No autonomous-control claims from it.**
- **Driven and self-maintaining regimes are never blurred** — separate tables,
  separate labels, no pooled statistics.

## S. Translating identity

Track, separately and never collapsed:

- $R_M(t)$ material retention
- $R_F(t)$ translation-aligned functional identity
- clumpness · component count · density/area
- **deformation after removing bulk translation**
- bulk velocity

Target phenomenon: $R_M \downarrow$ while $R_F$ and $Q_{\text{clump}}$ remain
high — the collective persists as a thing while its matter turns over.

## T. Translating control

**Only run control if** (a) natural emergence or brief nucleation produces a
self-maintaining translating collective, **and** (b) the full-model control
benchmark establishes controllability — the Stage 6.10 Part H discipline.

Task: **turn the collective by 90°** (e.g. bulk motion east → north).

- Controller acts only through **current exterior causal channels**.
- Each step updates $I_t$, $B_t$, $\hat v_I(t)$ — the translating frame is
  *estimated*, never read from the simulator.
- Primary score: angular / bulk-velocity alignment with the target.
- Identity and clumpness must remain valid (Stage 6.10 conjunctive scoring,
  envelope recalibrated for the moving regime).
- Then **release control and check persistence**.

## U. Final interactive-demo story

One concise primary walkthrough: Unstructured → Emergence → Detected thing →
Dynamic interface → Target introduced → Adaptive steering → Release.

- Stage 6.10: the 90° **heading** turn.
- Stage 6.11 *if it succeeds*: the 90° **spatial-trajectory** turn, world and
  co-moving frames.
- Always distinguish blind inferred quantities from oracle/reference overlays;
  **oracle overlays off by default**.

## V. Hard interpretation rules

1. No method-success claim where the full-model benchmark says the task is uncontrollable.
2. Never call the full-info causal heuristic an optimal controller.
3. Never call the candidate interior "ground truth" — spontaneous collective identity has no unique simulator label.
4. Do not let visual clumpness erase statistically interesting snake-like candidates.
5. Do not select the physical regime using blind-estimator performance.
6. Do not tune thingness thresholds on control success.
7. Do not relax identity/clumpness thresholds after observing a failed intervention.

---

## Order of work, with stop conditions

| step | gate to pass | outcome |
|---|---|---|
| M audit | ingredients present or added once | done (`logs/moving_model_audit.txt`) |
| N normalization | preserves operating scale at original degree | done; kept as labelled comparator only (Section N did not achieve gain/degree separation) |
| O (R,v,cohesion) scan | a non-saturated, cohesive cell exists | **passed** — global-collapse probability 0.00 in all 36 dev cells; 26 candidates; see `RESULTS_6_11.md` §1 |
| P emergence | qualifying episodes at reasonable frequency | **passed in the same screen** — 95-100% episode frequency at the confirmed regimes; no gap to Q |
| Q nucleation | only if P too rare | **not needed** |
| R driven benchmark | only if Q insufficient | **not needed** |
| T control | benchmark establishes controllability | **partial positive**: 3/5 online seeds turned and the turn persisted through release at the primary regime (reduced compute budget, no full-model benchmark run); see `RESULTS_6_11.md` §7 |

Full task-brief items 1-20 (firewall, relational predictor, causal probing,
lineage, thingness, control interfaces, online loop, oracle reveal, figures)
are reported in `RESULTS_6_11.md`, not re-narrated here.

**Stage 6.9 is the precedent for stopping.** Its translation gate failed 0/40
and the radius was *not* moved back up to make it pass. Here the same radius
DID pass once the Section M/N positional-cohesion term (already planned,
not invented after the fact) was switched on — the discipline that mattered
was resisting the temptation to raise R, not resisting cohesion.
