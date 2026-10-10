# PHASE_MAP — Stage 6.8 uncontrolled phenomenology

Written **before any inference, boundary, causal-discovery or control code was
run on real data**, from `data/phase_scan*.json`, `data/phase_scan_size.json`,
`data/phase_scan_op.json` and `data/episode_screen.json` alone. The scripts
that produced those files (`code/run_phase_scan.py`,
`code/run_phase_scan_fov.py`, `code/run_size_scan.py`,
`code/run_episode_screen.py`) cannot import a boundary, causal or control
module — none existed when they were run.

The full audit trail of what was declared when, including every scan that
failed and every threshold that was *not* moved, is
`logs/mesoscopic_criteria_predeclared.txt` (five dated addenda).

---

## 1. The criteria, fixed before the search

The task brief's four desiderata, operationalized once and never relaxed:

| id | brief's wording | test |
|---|---|---|
| M1 | coherent groups form | mean largest coherent component ≥ 0.10·N |
| M2 | they persist | mean coherent-component lineage lifetime ≥ 5 steps |
| M3a | the entire lattice is not almost always one aligned component | fraction of time largest component ≥ 0.90·N is ≤ 0.20 |
| M3b | ″ | mean largest coherent component ≤ 0.70·N |
| M4a | substantial stochastic variation remains | mean membership turnover ≥ 0.05 |
| M4b | ″ | mean heading entropy ≥ 0.40 nats (of ln 4 = 1.386) |

A **coherent component** is a connected component of the *geometric* Moore
graph restricted to same-heading edges. This is deliberately the
model-independent definition — it is identical at L1 and L2, so the two rungs
are directly comparable, and it never uses the FOV graph.

Selection rule, also fixed in advance: **highest fraction of qualifying
episodes; ties broken by distance from the frozen L0 point (β=1.0, s=1.0);
if two cells remain equally reasonable, both are retained.** Downstream
inference/control quantities were not used, and were not computable.

---

## 2. L1 — fixed Moore graph: no mesoscopic regime, and why

Primary β scan (ρ=15, ω=3, nn=100, 20 seeds, nt=120, statistics on t ≥ 40):

| β | polarization | largest comp | n comps | lifetime | turnover | H | frac global |
|---|---|---|---|---|---|---|---|
| 0.25 | 0.240 | 31.1 | 8.17 | **1.08** | 0.270 | 1.290 | 0.000 |
| 0.50 | 0.835 | 85.8 | 1.45 | 63.3 | 0.031 | 0.258 | **0.636** |
| 0.75 | 0.923 | 93.9 | 1.22 | 62.3 | 0.017 | 0.113 | 0.841 |
| 1.00 | 0.944 | 93.9 | 1.23 | 68.8 | 0.017 | 0.120 | 0.817 |
| 1.25 | 0.919 | 92.4 | 1.34 | 66.6 | 0.024 | 0.160 | 0.788 |
| 1.50 | 0.941 | 93.3 | 1.26 | 69.5 | 0.020 | 0.137 | 0.782 |

**No β qualifies.** The transition is a step, not a ramp: at β=0.25 groups form
but do not persist (lifetime 1.08); at β≥0.5 the lattice is a single ≥90-bird
component 64–84% of the time.

The brief's prescribed remedy — a second scan in a common precision scale
(ρ,ω) = s·(15,3) — was run as the full 6×5 (β,s) cross (30 cells,
`data/phase_scan_cross.json`). **No cell qualifies.** A declared resolution
refinement inside the bracketed interval (β ∈ {0.30…0.45}, and β=0.25 at
s ∈ {1.1…1.4}, `data/phase_scan_refine.json`) also produced **no qualifying
cell**: the nearest, β=0.25 at s=1.2, has largest 56.5, frac-global 0.110,
turnover 0.217, H 0.97 — but lifetime 1.48.

### Why L1 cannot have one

The obstruction is mechanical, not a search failure. In the frozen model
`flock_sim.active_inference.compute_G` **never reads `z[i]`**: bird i's next
heading is a function of its *neighbours'* current headings and nothing else.
There is no self-coupling, so a domain has no inertia of its own. A direct
measurement confirms this is what binds:

| β, s | P(z_{t+1} = z_t) | J(largest_t, best match at t+1) |
|---|---|---|
| 0.25, 1.0 | 0.371 | 0.363 |
| 0.25, 1.2 | 0.556 | 0.563 |
| 0.25, 1.3 | 0.650 | 0.679 |
| 0.30, 1.0 | 0.896 | 0.896 |
| 1.00, 1.0 | 0.994 | 0.993 |

Domain persistence and single-bird persistence rise together, and by the time
persistence is usable (~0.9) the lattice is already ≳72% globally aligned.
**On the fixed undirected graph, persistence and non-globality are the same
quantity.** That is the L1 result, and it is negative.

---

## 3. L2 — heading-dependent FOV: a different phase diagram

The FOV rule makes `z[i]` select which sources are live. It is the *only*
receiver-state dependence anywhere in this model family, and it changes the
phenomenology qualitatively at identical parameters (nn=100):

| β | | largest | n comps | lifetime | turnover | H | frac global |
|---|---|---|---|---|---|---|---|
| 1.0 | L1 | 93.9 | 1.23 | 68.8 | 0.017 | 0.120 | 0.817 |
| 1.0 | **L2** | **74.3** | **3.54** | 23.4 | 0.062 | 0.361 | **0.478** |
| 1.5 | L1 | 93.3 | 1.26 | 69.5 | 0.020 | 0.137 | 0.782 |
| 1.5 | **L2** | **66.2** | **4.31** | 16.2 | 0.052 | 0.428 | **0.388** |

Coexisting domains appear (1.2 → 3.5–4.3 components), the largest shrinks by
~28 birds, and heading entropy triples. Still, **no L2 cell of the primary
grid, the 6×5 cross, or the declared L2 refinement qualifies** — M3a is
binding everywhere, exactly mirroring L1.

---

## 4. The seed-average was the wrong summary

Behind those means the distribution is strongly **bimodal**. At β=1.0 (L2,
nn=100) the per-seed frac-global values are
{1.0, .32, .12, .31, 0, 0, .44, 0, .68, 0, .36, .22, 0, .83, .19, .59, 1.0, 0, 0, .74};
the across-seed SD of frac-global (0.34–0.40) equals its mean. **No single
realization resembles the seed-average.** The criteria were therefore applied
at the level they always described — one uncontrolled realization — and a
cell is scored by its *fraction of qualifying episodes*. Thresholds unchanged.

At episode level, L2 at nn=100 scores **0/20 in every cell**. The failures are
diagnostic rather than marginal:

- β=0.25: disordered churn, lifetime ≈ 1 (fails M2);
- many β≥0.5 seeds **freeze**: heading entropy exactly ln 2 = 0.693,
  polarization 0.006–0.04, turnover 0.004–0.009, lifetime 26–80. These are
  static two-heading absorbing states, not flocks, and M4a correctly rejects
  them;
- the rest lock globally.

At L1 the best cell (β=1.25, s=0.5) scores 6/20 — but those episodes are
*frozen two-domain* configurations (lifetime 62 with almost no turnover), i.e.
the same absorbing-state artefact one criterion short of being caught.

---

## 5. Finite size was a real confound

nn = 100 with a Moore neighbourhood means every bird interacts with 8% of the
entire flock and a domain wall costs ~10 of 100 sites. Coexistence may simply
not fit. Scanning L2 across lattice size (`data/phase_scan_size.json`,
identical criteria, identical seeds):

| nn | β=0.5 | β=0.75 | β=1.0 | β=1.5 | largest/N | n comps | lifetime | frac global |
|---|---|---|---|---|---|---|---|---|
| 100 | 0.00 | 0.00 | 0.00 | 0.00 | 0.74 | 3.5 | 23.4 | 0.478 |
| 225 | 0.00 | **0.10** | 0.00 | 0.00 | 0.71 | 5.2 | 7.5 | 0.306 |
| 400 | 0.00 | 0.05 | **0.15** | 0.10 | 0.71 | 4.7 | 3.2 | 0.203 |
| 900 | 0.00 | 0.00 | 0.00 | 0.05 | 0.58 | 6.9 | 2.3 | 0.069 |

(cell entries = mesoscopic-episode fraction; the right-hand columns are the
β=1.0 row.) Coexisting domains do appear once the lattice can hold them —
largest/N falls 0.74 → 0.58, components rise 3.5 → 6.9, frac-global falls
0.478 → 0.069 — but lifetime falls with N, so M2 takes over from M3a as the
binding criterion. The optimum is interior, at **nn = 400**.

---

## 6. The two retained operating points

Final scan at nn = 400 (`data/phase_scan_op.json`, 12 cells):

| β | s | mesoscopic-episode fraction |
|---|---|---|
| **1.00** | **1.00** | **0.15** |
| 0.75 | 2.0 | 0.10 |
| 1.25 | 2.0 | 0.10 |
| 1.50 | 1.0 | 0.10 |
| (all others) | | ≤ 0.05 |

Applying the selection rule as written:

> **OP-1 (primary): nn = 400 (20×20), β = 1.0, ρ = 15, ω = 3, L2 (FOV).**
> **OP-2 (retained second regime): nn = 400, β = 1.5, ρ = 15, ω = 3, L2.**

OP-1 is the unique maximum, and it lands on **exactly the frozen Stage 6–6.7
values of β, ρ and ω**. Among the three cells tied at 0.10, the distance
tie-break (|Δ ln β| + |Δ ln s| from β=1.0, s=1.0) selects β=1.5, s=1.0
(0.405) over β=1.25, s=2.0 (0.916) and β=0.75, s=2.0 (0.981).

### The one scope change, stated plainly

**Lattice size is the only parameter Stage 6.8 moves away from the frozen
Stage 6–6.7 convention (nn = 100 → nn = 400).** It was forced by an
uncontrolled-phenomenology finding, not by anything downstream: at nn = 100 no
parameter setting anywhere in this model family produces a mesoscopic episode.
Nothing in Stages 6–6.7 is re-run, re-fit or restated at the new size; every
frozen result there continues to describe nn = 100 and is untouched.

---

## 7. What this means for the Stage 6.9 gate

Gate criterion 1 is *"the L1 regime supports persistent non-global
collectives."* **At L1 it does not, at any parameter setting or lattice size
tested — this is a negative result and it is reported as one.** What supports
them is L1's parameters *plus the L2 FOV rule*, at nn = 400, and only in
about 15% of realizations, which are identified by the same uncontrolled,
task-neutral screen (`data/episode_screen.json`) and split into development
and held-out sets before any threshold was calibrated.

Whether that is enough to pass the gate is decided in `RESULTS_6_8.md`
against gate criteria 2–4, not here.
