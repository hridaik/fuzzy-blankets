# PERTURBATIONS.md — Task 4: catalog and classification

**Status: catalog, classification, and exact equations are `ESTABLISHED`
(read directly from primary sources, several with corrected/clarified
detail vs. the task prompt's summary — see below). Implementation
(Python hooks with ramps, Octave golden traces for the equation/text-based
items, and the "continue to 512 bins under sustained perturbation" test) is
`NOT DONE`** — blocked on `PORT_DESIGN.md`'s unresolved port issue for the
Python side, and on remaining session time for the Octave side (the
CODE-BASED item already has Octave traces from Task 1; the others do not).

## Classification key

- **CODE-BASED**: reference code exists in a fetched repository; the plan is
  to run it in Octave and match it exactly.
- **EQUATION-BASED**: explicit equations are given in a paper; the plan is
  to implement them exactly, no free parameters invented.
- **TEXT-BASED**: only prose describes the manipulation; the plan is a
  small, declared parameter sweep, matched qualitatively only, never claimed
  exact.

## 1. Kuchling, Friston, Georgiev & Levin (2020) — EQUATION-BASED, highest priority

Source: `sources/papers/kuchling2020.pdf`, section 4.3 (pp. 18-19), read
directly (not from the task prompt's summary). All three sub-perturbations
share the normal sensory mapping `s_x = ẽ_x` (eq. 40) as their baseline.

### 1a. Double head / double tail (eq. 48, p.18)

```
(a) s_x = (ẽ_x)^2      -> double head
(b) s_x = -(ẽ_x)^2     -> double tail
```

Applied to **the vertical-axis component only** of the position sensory
mapping (the paper's simulations use a 2D position; "vertical" = the
anterior-posterior axis of the planarian-like target morphology in Fig. 2).
All other sensory channels (secretion `s_c`, extracellular `s_λ`) are
unchanged. The paper's own explanation (p.18): squaring "causes the signal
... to be updated only based on positive (or negative, with the minus sign)
values, causing each cell to explain all sensory inputs as an increased
signal from one direction," and "increases the sensitivity of sensory
inputs to extracellular concentrations (external states), thereby
increasing the effective precision." **Both effects are a direct
consequence of the squaring/negative-squaring, not a separate free
parameter — nothing to tune.** `ESTABLISHED`.

### 1b. Anomalous single cell (eq. 49, p.18)

```
s_x,j = (ẽ_x,j)^2   for j = j_f (the affected cell)
s_x,j = ẽ_x,j       for j != j_f
```

Same distortion as 1a(a), restricted to one designated cell `j_f`.
`ESTABLISHED`.

### 1c. Rescue via square-root distance kernel (eq. 50, p.19)

```
λ_{j_f} = τ · Σ_l e_cl · exp(-k · sqrt(d_{j_f,l}))
```

i.e., replace the affected cell's own field-sensing kernel's distance term
`d` with `sqrt(d)` (attenuating the exponential falloff so the anomalous
cell integrates signal from farther away) — applied **only to the
anomalous cell's own receiving kernel**, not to how other cells sense it,
and not to the squared position mapping itself (1b is left in place; 1c is
a rescue of its *consequences* via signalling range, not a reversal of the
position distortion). `ESTABLISHED`.

### Onset/offset ramping (Kuchling et al.'s own warning)

The paper does not give an explicit ramp equation for turning these
perturbations on, but does warn (via its own `τ` sensitivity factor, eq. 43)
that abrupt sensitivity changes are undesirable, and already ramps ordinary
signalling onset that way. **Design decision for the Python
implementation** (not yet built): reuse the same functional form — multiply
the perturbation's *deviation* from baseline by a `τ_pert(t) = 1-exp(-(t-t_on)/T_ramp)`
factor with a declared `T_ramp` (e.g. 4 bins), so the squared-mapping
distortion fades in smoothly rather than switching on at full strength at a
single bin boundary. `PROVISIONAL` design, not implemented or validated.

### Developmental sensitivity factor — three distinct forms (required fact, Task 2)

| Source | Form | Parameter |
|---|---|---|
| Friston et al. 2015 (p.6, eq. not numbered, prose: "τ∈[0,1]... models a linear increase") | **linear ramp** | none stated beyond `τ∈[0,1]` over the run |
| SPM12/SPM25 code (`DEM_morphogenesis.m` `Gg`/`Mg`) | `s = 1 - exp(-2t)`, `t=iY/nY` | rate constant 2 (hard-coded) |
| Kuchling et al. 2020 (p.16-17, eq. 43) | `τ = 1 - exp(-t/T)`, **T = 1/ln(2)** (a half-life parametrization: `τ=1-2^{-t}`) | half-life `T=1/ln2≈1.443` |

All three are **exponential-saturating or linear, never identical to each
other** — three genuinely different published forms for nominally "the same"
mechanism. `ESTABLISHED`, directly confirmed from both papers' primary text
in this session (not inferred).

## 2. Friston et al. 2015 sensitivity perturbations — EQUATION-BASED (Fig. 5, p.9)

Source: `sources/papers/friston2015.pdf`, Figure 5 and surrounding text
(pp. 8-9), read directly. **Figure 5's panel math labels give exact
multiplicative factors** applied to the relevant sensitivity/precision
parameter (`ψ` = the unperturbed value):

| Panel | Formula (from the panel label) | Body text description | Figure caption description |
|---|---|---|---|
| gradient (top-left) | `S_x = (1/2)·ψ_x` | "non-specific suppression of exogenous signals" | "changing the concentration of (or sensitivity to) exogenous gradients ... failure of migration and differentiation" |
| gradient (top-right) | `S_x1 = 2·ψ_x1` | "selectively increasing the vertical gradient produces compression along the corresponding direction" | "selectively increasing the vertical gradient produces compression" |
| intrinsic (bottom-left) | **`S_s = 2·ψ_s`** | **"Doubling the sensitivity to intracellular signals causes a failure of migration and differentiation and generalized atrophy"** | **"More exotic forms of dysmorphogenesis result... from decreasing the intracellular (intrinsic...) receptor sensitivities"** |
| extrinsic (bottom-middle) | `S_c2 = (1/4)·ψ_c2` | "reducing sensitivity to the second chemotactic signal—that is expressed by head cells—reduces the size of the head" | "decreasing... extracellular... receptor sensitivities" |
| extrinsic (bottom-right) | `S_c3 = (1/4)·ψ_c3` | "reducing sensitivity to the third signal induces a selective failure of body cells to differentiate" | (same as above, grouped) |

**The conflict the task asked us to find and report, confirmed verbatim**:
for the **intrinsic/intracellular** panel, the panel's own math label
(`S_s = 2·ψ_s`, an **increase**) and the body text ("**Doubling** the
sensitivity... causes... atrophy") **agree with each other** (both say
increase/doubling), but the **figure caption** says dysmorphogenesis results
"from **decreasing** the intracellular... receptor sensitivities" — the
opposite direction. **Plan: implement both directions** (`×2` per the panel
formula + body text, and `×0.5` per the caption, matching the 2015 paper's
own gradient-panel factor since no other explicit "decrease" factor is
given for intrinsic) **and report both outcomes**, per the task's
instruction. `ESTABLISHED` (the conflict itself; not yet run in Octave —
`NOT DONE`).

The `extrinsic` (signal-2, signal-3) and `gradient` (exogenous, vertical)
panels have no text/caption conflict — caption and body text agree in all
four other cases. `ESTABLISHED`.

**Implementation status**: these five (six, counting both intracellular
directions) perturbations require patching the generative **process**'s
signal-sensitivity terms, which are not exposed as named parameters
anywhere in `DEM_morphogenesis.m` (unlike Kuchling 2020's `Π^(1)`/`τ`, which
map cleanly onto the code's `M(1).V`/developmental-factor terms) — no code
implementing them was found anywhere in the fetched SPM12/morphopsy sources
(consistent with `m0_reconstruction/DISCREPANCIES.md` §6-7's earlier
finding). Implementing them requires deciding *which* generative-process
Jacobian term each `ψ` symbol maps to, which was not resolved in this pass.
`NOT DONE`, honestly, not invented.

## 3. Pio-Lopez et al. 2022 — CODE-BASED (high identity expectation)

Already covered in Task 1 / `ORACLE_REPORT.md`: `k=1..6` variants run in
Octave, golden traces saved and hashed
(`data/oracle_traces/pio_lopez_k{1..6}_N32_seed0.mat`). **This is the one
perturbation in the entire catalog with both a code reference AND an
existing Octave golden trace from this session.** Continuing these runs to
512 bins under sustained perturbation: `NOT DONE` (time budget; each
additional 512-bin run costs ~4 min per `ORACLE_REPORT.md`'s measured
scaling — cheap, just not yet done).

## 4. Pio-Lopez et al. 2022 — TEXT-BASED (high/low sensory precision, two-cell rescue)

No code found in `LPioL/active_inference_morphopsy` at the fetched commit
(confirmed again this session — only the 6 high-identity-expectation files
exist in that repository). Per the task's own instruction, these need a
**small declared parameter sweep**, matched qualitatively only:

- **High sensory precision**: sweep `M(1).V ∈ {exp(4), exp(5), exp(6)}`
  (baseline `exp(3)` — see `DISCREPANCIES.md` in m0 for the baseline value)
  applied to `k∈{1,2}` cells, by analogy with the code-based high-identity
  perturbation's cell-count parameterization.
- **Low sensory precision**: sweep `M(1).V ∈ {exp(0), exp(1), exp(2)}` for
  the same cell counts.
- **Two-cell rescue**: sweep not yet designed (would need the specific
  "rescue" mechanism's textual description re-read carefully from the 2022
  paper, which — per `m0_reconstruction/DISCREPANCIES.md` §6 — was
  summarized from the task prompt but not independently re-read from its
  own PDF in that stage; **also not independently re-read in this stage**
  — `NOT DONE`, flagged in `OPEN_QUESTIONS.md`).

`NOT DONE` in full; sweep values declared above are provisional design only,
not run.

## Summary table

| Perturbation | Class | Equations/params established | Octave trace | Python impl | 512-bin sustained run |
|---|---|---|---|---|---|
| Kuchling double head | EQUATION-BASED | yes | no | no | no |
| Kuchling double tail | EQUATION-BASED | yes | no | no | no |
| Kuchling anomalous cell | EQUATION-BASED | yes | no | no | no |
| Kuchling sqrt-rescue | EQUATION-BASED | yes | no | no | no |
| Friston exogenous gradient (x0.5) | EQUATION-BASED | yes | no | no | no |
| Friston vertical gradient (x2) | EQUATION-BASED | yes | no | no | no |
| Friston intracellular (x2, panel+text) | EQUATION-BASED | yes | no | no | no |
| Friston intracellular (x0.5, caption) | EQUATION-BASED | yes | no | no | no |
| Friston signal-2 (x0.25) | EQUATION-BASED | yes | no | no | no |
| Friston signal-3 (x0.25) | EQUATION-BASED | yes | no | no | no |
| Pio-Lopez high identity (k=1..6) | CODE-BASED | yes | **yes (6 traces)** | no | no |
| Pio-Lopez high precision | TEXT-BASED | sweep declared | no | no | no |
| Pio-Lopez low precision | TEXT-BASED | sweep declared | no | no | no |
| Pio-Lopez two-cell rescue | TEXT-BASED | not designed | no | no | no |

**Honest bottom line**: this session established a complete, source-grounded
catalog with exact equations (a genuine, checkable deliverable, including
finding and resolving the Figure 5 caption/text/panel conflict the task
specifically asked about), and one perturbation's Octave golden traces.
Execution of the rest — Octave traces for the equation/text-based items, any
Python implementation, ramped onset/offset, and the 512-bin sustained-run
test — is `NOT DONE`, consistent with `PORT_DESIGN.md`'s disclosed stopping
point.
