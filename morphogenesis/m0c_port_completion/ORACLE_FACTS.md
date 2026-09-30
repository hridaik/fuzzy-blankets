# ORACLE_FACTS.md — Part A

## A1 — Free-energy sign convention: `ESTABLISHED`, match confirmed

- `DEM.J` (`spm_ADEM.m` line 873): commented **"[-ve] Free energy (over
  samples)"** — i.e. `J` is the **negative** of the conventional variational
  free energy `F` (so `J` is an ELBO/log-evidence-like quantity: **higher
  `J` = lower `F` = better fit**).
- The published script plots **`-DEM.J`** (`DEM_morphogenesis.m` line 229,
  `plot(-DEM.J)`, y-axis labeled `'Free energy'`) — i.e. it plots the
  conventional `F` (lower = better), matching Fig. 3's y-axis (`-340` down
  to `-420`, decreasing = improving).
- **2015 paper's described pattern** ("a brief initial increase in free
  energy... followed by a profound reduction," p.7): checked against our
  own `vanilla8_N32_seed0` trace, in the **plotted convention** (`-J`):
  `J` = `[295.5, 233.8, 239.5, 290.8, 306.0, ..., 358.7]` (rising overall)
  ⟹ `-J` = `[-295.5, -233.8, -239.5, -290.8, -306.0, ..., -358.7]` — **rises
  briefly** (bin 1→2: `-295.5→-233.8`, an increase) **then falls
  substantially** (`-233.8→-358.7`). **Match, `ESTABLISHED`**, confirmed
  quantitatively, not just qualitatively, this time.

## A2 — Time and developmental factor: `ESTABLISHED`, consolidated

- `t` (global): assigned `t = iY/nY` every D-step sample (`spm_ADEM.m` line
  444); units = **fraction of total run length**, `t∈(0,1]`. Since `nY=N`
  (bin count) exactly (m0b finding, re-confirmed: `nY = size(DEM.C,2)`), a
  given **absolute bin number corresponds to a different `t` depending on
  the run's total `N`** — e.g. bin 32 is `t=1.0` in a 32-bin run but only
  `t=0.031` in a 1024-bin run. This is a real, easily-missed subtlety for
  any cross-`N` comparison (flagged in A3 below).
- Developmental sensitivity factor, three published forms (m0b
  `PERTURBATIONS.md` §1, restated here for completeness):

| Source | Form |
|---|---|
| Friston et al. 2015 (p.6, prose) | linear ramp, `τ∈[0,1]` |
| SPM12/SPM25 code (`Gg`/`Mg`) | `s = 1 - exp(-2t)` |
| Kuchling et al. 2020 (p.16-17, eq. 43) | `τ = 1 - exp(-t/T)`, `T=1/ln(2)` (half-life form, `τ=1-2^{-t}`) |

  Per-bin values actually used by the code (`s=1-exp(-2t)`, `N=32`): bin 1
  `s=0.061`, bin 8 `s=0.375`, bin 16 `s=0.632`, bin 32 `s=0.865`.

## A3 — Long-horizon reference behaviour: `ESTABLISHED`

`vanilla8_N1024_seed0.mat` (fresh 1024-bin run, seed 0 — **not** a
continuation of the 512-bin run, since `t=iY/N` depends on the *chosen*
total `N` from the start; extending the horizon requires a fresh run at the
new `N`, not appending bins — see A2's subtlety):

| bin | max-softmax mean (min across cells) | free energy `J` | max per-bin Δposition (last 20 bins window) |
|---|---|---|---|
| 1 | 0.148 (0.134) | 315.66 | — |
| 32 | 0.225 (0.152) | 313.57 | — |
| 128 | 0.460 (0.266) | 329.32 | — |
| 256 | 0.656 (0.590) | 350.00 | — |
| 512 | 0.726 (0.692) | 359.17 | — |
| 768 | 0.744 (0.713) | 360.33 | — |
| **1024** | **0.751 (0.721)** | **360.26** | `8.5e-5` (last 20 bins) |

- **Convergence**: `J` changes by only `0.00088` max over the last 200 bins,
  and by `1.08` total from bin 512→1024 (against a baseline of ~360) —
  **effectively converged** by ~bin 700-800. Per-bin position/secretion
  change at bin 1024 (`~8.5e-5`) is an order of magnitude smaller than at
  bin 512 (`~1.6e-4`, m0b finding) — still slowly shrinking, not yet at a
  hard numerical floor, but clearly asymptoting. `ESTABLISHED`.
- **Does identity confusion resolve as the 2015 paper says?** The paper
  (p.7) describes head/body and body/tail confusion resolving "with
  continued differentiation." Here, **min-across-cells max-softmax** (the
  worst-differentiated cell) rises from 0.134 (bin1) through 0.590 (bin256)
  to 0.721 (bin1024) — **monotonically improving, consistent with
  resolving confusion**, though it does **not** reach the >0.9 threshold
  this programme has used elsewhere as "strongly concentrated" even by
  bin 1024. Whether the paper's own MATLAB run reaches >0.9 is unknown (no
  bitwise-comparable MATLAB run exists — Octave RNG differs, m0b
  `ORACLE_REPORT.md`). **`ESTABLISHED`** for this Octave run's own numbers;
  **`PROVISIONAL`** as a claim about what the *published* run specifically
  reached, since only this run's own trace was measured.

## A4 — Octave self-sensitivity control (chaos baseline): `ESTABLISHED`

Vanilla-8, `N=32`, seed 0, vs. twins with initial `v` perturbed by a fixed
random unit direction scaled `1e-10` and `1e-6` (`oracle/run_sensitivity_pair.m`).

- **`eps=1e-10`**: position and `v`-expectation deviation from baseline is
  **exactly `0.0` at every sampled bin** (1,2,4,8,16,32) — below whatever
  numerical resolution the run's own floating-point operations preserve at
  this scale (the process noise floor alone, `~3.35e-4` marginal std per
  m0b, is ~3300x larger than this perturbation).
- **`eps=1e-6`**: deviation is small and **non-monotonic — rises from
  `2.5e-7` (bin 1) to a peak `~1.2e-5` (bin 10-11), then monotonically
  decays back to `1.5e-7` by bin 32**. **This is a transient-then-contracting
  pattern, not chaotic growth.** `ESTABLISHED`.
- **Conclusion (the chaos baseline itself)**: over a 32-bin horizon at
  these perturbation scales, **the reference is demonstrably NOT
  sensitive-dependent / chaotic** — small initial perturbations do not
  amplify; they peak early and decay. **Any future L3 port-vs-oracle
  deviation that grows monotonically and does not decay should be
  attributed to the port, not to inherent chaos in the reference model**,
  per this baseline.

## A5 — Live `Gg`/`Mg` check: `ESTABLISHED`

20 random identical `(v,a,t)` triples, evaluated in both live Octave
(`oracle/run_a5_function_check.m`) and Python (`m0b`'s `model.py`, imported
unmodified): **max relative deviation `1.176e-15` (`Mg`) / `2.907e-16`
(`Gg`)** — machine precision. **This closes m0b `OPEN_QUESTIONS.md` item 2.**

## A6 — Pio-Lopez et al. 2022 primary-source check: `ESTABLISHED`

Read directly from `sources/papers/piolopez2022.pdf` (fetched this session,
24 pages, DOI `10.3389/fncom.2022.988977`):

- **High sensory precision (§5.2, Fig. 4)**: *"we assigned an excessively
  high precision to the biochemical signals sensed by **ALL cells**"*
  (p.11) — confirms **all 8 cells**, not a subset, for the main
  demonstration figure.
- **The k-of-8 mosaic sweep (Fig. 5)**: caption (p.13): *"Results of the
  simulations for **one to eight cells** having a too high precision"*
  (Fig. 5A) and *"...too high prior on their identity"* (Fig. 5B) — **a
  separate experiment** from the "all cells" one, sweeping `k=1..8`.
  **Note**: the paper's own figure goes to **k=8**; the
  `LPioL/active_inference_morphopsy` code repository (m0b `ORACLE_REPORT.md`)
  only provides `k=1..6` — the paper's figure and the released code do not
  fully match in range. `ESTABLISHED`.
- **Low sensory precision (§5.4, Fig. 7)**: *"setting a very low sensory
  precision for **all cells** in the collective"* (p.15) — confirms all
  cells for this one too.
- **Two-cell rescue (§5.5, Fig. 8), the specific claim the task asked to
  verify**: *"This simulation shows the effect of the **reduction of
  concentration signaling and sensitivity to the other cells' signals** of
  the two cells having too high precision"* (p.15) and *"In our simulation,
  we **reduced the sensitivity to the other cell signals** for the two
  cells having a too high precision"* (p.16). **Confirmed exactly as the
  task described: the rescue reduces BOTH (1) the concentration of signals
  secreted by the two aberrant cells AND (2) their sensitivity to other
  cells' signals** — both explicitly stated, not inferred. `ESTABLISHED`,
  with page references.

**Amendment to m0b `PERTURBATIONS.md` §4** (recorded here, applied in
`PERTURBATIONS_EXECUTED.md`): the high/low-precision sweeps should default
to **all 8 cells**, not an arbitrary `k∈{1,2}` subset as m0b provisionally
declared — the paper's *own* main demonstration is all-cells; the k-sweep
is a separate, secondary figure.
