# DISCREPANCIES.md — deviations between sources, and between sources and papers

All items cross-referenced from MODEL_SPEC.md. Status labels as in that file.

## 1. SPM12 vs SPM25 — `DEM_morphogenesis.m` and `spm_ADEM.m`

- `toolbox/DEM/DEM_morphogenesis.m`: **identical** between SPM12 GitHub mirror
  (`spm/spm12`, commit `03ac9473c`) and SPM's `spm/spm` repo at tag
  `25.01_release` (commit `7616751`), except the copyright-year header comment
  (`2008` → `2008-2022`). No functional change. **ESTABLISHED**.
- `spm_ADEM.m`: functionally near-identical; SPM25 adds one second-order Hessian
  term (`dFdhh = dFdhh + diag(dFdh)`) in the M-step hyperparameter update block.
  This block only executes when `nh > 0` (hyperparameter components `M(i).Q`/
  `M(i).R` are set); `DEM_morphogenesis.m` sets neither, so `nh = 0` and this
  code path never runs for this model. **Conclusion: the two SPM releases are
  behaviourally identical for `DEM_morphogenesis.m`.** **ESTABLISHED.**
- **Decision**: SPM12 GitHub mirror (commit `03ac9473c`) is used as the
  reference throughout M0, because (a) it is behaviourally identical to SPM25
  for this model, (b) both published papers (2015, 2022) predate SPM25, and
  (c) the `LPioL/active_inference_morphopsy` repo's README explicitly states
  "The spm12 matlab package is required."

## 2. Developmental sensitivity factor: code vs. 2015 paper

- Code (`Gg`/`Mg` in `DEM_morphogenesis.m`): `s = 1 - exp(-2t)`, an exponential
  saturating ramp, `t = iY/nY ∈ (0,1]` reassigned every D-step sample inside
  `spm_ADEM.m`.
- 2015 paper (Friston, Levin, Sengupta & Pezzulo): described (per the ground
  rules summarizing it) as "a linear ramp over [0,1]".
- **These are different functional forms** (linear vs. exponential-saturating).
  This is a **genuine code/paper discrepancy**, not a version issue — both
  SPM12 and SPM25 use the exponential form; no linear-ramp variant was found
  anywhere in the fetched sources. **ESTABLISHED discrepancy, directly
  confirmed from the primary source**: the 2015 paper (p.6, §4, eq. 4.2) states
  the field function `λ_i(ψx,ψc) = τ · Σ_j ψcj · exp(-|ψxi - ψxj|)` where
  "τ ∈ [0,1] is developmental time and models a linear increase in sensitivity
  to extracellular signals (e.g. the progressive expression of cell surface
  receptors over time)." This `τ` plays the same role as the code's `s`, but
  the paper's `τ` is explicitly linear while the code's `s = 1-exp(-2t)` is
  explicitly exponential-saturating. The 2022 paper was not checked
  line-by-line against this specific claim in this pass (**NOT DONE**).

## 3. Model sensory precision — three-way comparison

| Source | Value | log-precision |
|---|---|---|
| 2015 paper (per ground rules) | — | **2** |
| 2022 paper (per ground rules) | — | "set to 1" |
| Canonical SPM12/SPM25 code (`M(1).V`, `DEM_morphogenesis.m` line 126) | `exp(3)` | **3** |
| All 6 Pio-Lopez `morphopsy` variants | `exp(3)` (unchanged from canonical) | **3** |
| "A Pio-Lopez variant" per ground rules | `exp(3)` | 3 |

**Conclusion**: the code (both canonical and every perturbation variant found)
uses log-precision **3**, matching the "Pio-Lopez variant" figure quoted in the
ground rules, but matching **neither** paper's stated value (2015: 2; 2022:
"set to 1"). No code path was found anywhere in the fetched sources using
log-precision 1 or 2 for `M(1).V`. **ESTABLISHED** (code value).

**Direct primary-source confirmation (2015 paper, p.6, §4, PDF
`sources/papers/friston2015.pdf`, page 6/12):** "The signal precision Π⁽¹⁾ had
a log precision of two, with the precisions over [generalized] motion modelled
using random fluctuations with a Gaussian autocorrelation function of one."
This directly confirms log-precision **2**, not 3 — **ESTABLISHED discrepancy
between the 2015 paper's stated Π⁽¹⁾ and the code's `M(1).V = exp(3)`**,
verified by reading the primary source (not just the ground-rule summary).
The 2022 paper's "set to 1" claim was not independently re-verified against
its PDF in this pass (**NOT DONE**).

## 4. Initial expectations — CORRECTED: no discrepancy found

**This item is corrected relative to the ground-rule prompt's summary, after
reading the primary source directly.** The 2015 paper (p.6, §4, PDF
`sources/papers/friston2015.pdf`, page 6/12) states: "We assumed (zero-mean)
Gaussian priors over the hidden states with a small precision Π⁽²⁾ (with a log
precision of **minus two**). This means that the cells have prior beliefs that
they have a high expectation of being a particular clone but they do not know
which clone they only belong to." **This is log-precision −2, not −4** as
summarized in the ground-rule prompt — and it matches the code's
`M(2).V = exp(-2)` (`DEM_morphogenesis.m` line 132) **exactly**.
**ESTABLISHED: no discrepancy** between the 2015 paper and the code for the
*prior precision on the identity cause* `M(2).V`. The ground-rule prompt's
"-4" figure could not be located anywhere in the paper text read in this pass;
flagged as a probable transcription error in the task prompt rather than a
real code/paper mismatch.

Separately: the canonical code's *specific initial draw* (`v = randn(n,n)/8`,
σ=0.125, under `rng('default')`) is a single Monte Carlo realization used for
the shipped demo, not itself "the prior" — the prior precision (`exp(-2)`,
confirmed above) governs the *inference dynamics' pull toward zero*, not the
literal RNG scale of this one initialization line, so there is no tension to
resolve here: **ESTABLISHED, ITEM 4 CLOSED, NOT a discrepancy.**
- Separately, all 6 `morphopsy` perturbation files **do not use `randn(n,n)/8`
  at all** — they hard-code a fixed numeric `v` matrix (presumably one
  realization saved from a canonical run, given its qualitative resemblance:
  10 of its 11 rows in the non-exp(6) columns look like the same numeric family
  as a `randn(8,8)/small-ish` draw, though not evaluated symbolically) with
  rows 4–5 overwritten by `exp(6)` in the first `k` columns. This means the
  Pio-Lopez perturbation runs are **not comparable to the canonical script's own
  random initial condition** unless one confirms that fixed base matrix equals
  a `rng('default')`-derived draw (unverified — no MATLAB available to check).
  **NOT DONE.**

## 5. Source-code variable-naming collision: `t`

`DEM_morphogenesis.m`'s bisection block (lines 153–190, dormant/`SPLIT=0`) uses
a *local* variable `t` (`t = 8;` line 159) to mean "the bin index at which to
split," which shadows the *global* `t` used by `Gg`/`Mg` to mean "fraction of
integration elapsed." This is present in the original SPM source as shipped
(verified identical in SPM12 and SPM25) — **not** an artifact introduced by
this reconstruction. Flagged because it is exactly the kind of ambiguity the
ground rules ask to resolve explicitly for item (a); the two `t`s are
unrelated variables that happen to share a name, and (since `SPLIT=0` in the
shipped script) the local `t=8` never executes in the published configuration.
**ESTABLISHED.**

## 6. Perturbations named in the task prompt but not found in any fetched source

Per ground-rule items (d) and (e), and MODEL_SPEC.md §6–7:

| Perturbation | Found? | Where checked |
|---|---|---|
| Pio-Lopez: high identity expectation in k cells | **Yes** | `sources/morphopsy/*.m` (6 files) |
| Pio-Lopez: high sensory precision | **No** | full-text search of `sources/morphopsy` and the two fetched `DEM_morphogenesis.m` copies |
| Pio-Lopez: low sensory precision | **No** | same |
| Pio-Lopez: rescue (reduced signalling + sensitivity) | **No** | same |
| Friston 2015: suppressed exogenous gradient | **No** | same, plus no exogenous gradient term exists at all in the fetched code (§8 below) |
| Friston 2015: doubled vertical-gradient sensitivity | **No** | same |
| Friston 2015: doubled intracellular sensitivity | **No** | same |
| Friston 2015: quartered sensitivity to signals 2 and 3 | **No** | same |

Per the ground rules ("If absent from code, say so; do not invent an
implementation"), **no Python implementation of these seven perturbations is
provided in this stage.** Only the one Pio-Lopez "high identity expectation"
perturbation (parameterized by `k`, the number of cells) is implemented in the
Python port (Task C), because it is the only one with source-code grounding.
This is a **major, explicitly disclosed reduction in scope** relative to the
original task prompt's Task B configuration list ("every Pio-Lopez variant in
the repository; any Friston 2015 perturbation found in A(e)") — the repository
in question (`LPioL/active_inference_morphopsy`) contains fewer variants than
the prompt anticipated.

## 7. No exogenous gradient exists in the fetched code — bears on Friston-2015 items

`DEM.U` and `DEM.C` (`DEM_morphogenesis.m` lines 122–123) are `zeros(n*n, N)`
and `zeros(1, N)` respectively — an all-zero exogenous cause for all 32 bins.
There is no spatial gradient field, external morphogen source, or boundary
condition anywhere in the generative process `G` or model `M`. This means the
model as published is **entirely self-organizing from the initial condition**
(no environmental scaffold at all), which makes "suppressed exogenous
gradient" (a 2015-paper perturbation) structurally inapplicable to *this*
version of the code — there is no gradient present to suppress. This is
consistent with, and reinforces, §6's finding that the four 2015-paper
perturbations are absent from the fetched sources. **ESTABLISHED.**

## 8. Reference execution: not performed (Task B blanket status)

No MATLAB or GNU Octave is available in this environment. The user was asked
and explicitly chose **not** to install Octave via conda-forge for this stage.
Per the ground rules' own contingency ("If neither can run the reference,
state this at the top of README.md and label all later Python results
'unvalidated re-derivation'"): **Task B (golden traces) is NOT DONE in its
entirety.** No published figure was reproduced pixel-for-pixel or
value-for-value against a run of the reference code, because the reference
code was never executed. All Python outputs in this repository are
**unvalidated re-derivations**, not validated ports. See README.md for the
top-of-file warning and CHARACTERIZATION.md for how this propagates to every
descriptive claim in Task E.

## 9. Python port is a reconstructed solver, not a byte-level port of `spm_ADEM.m`

`spm_ADEM.m` (874 lines) implements full generalized-filtering dynamics via
local linearization of the joint state (causes, hidden states, action,
generalized motion, hyperparameters) and matrix-exponential integration
(`spm_dx`). For `DEM_morphogenesis.m` specifically, several of those general
mechanisms are inert: there are no hidden states `x` (`M(1)`/`G(1)`/`G(2)`
define no `.f` field), no parameter estimation (`M(i).pC` unset), and no
hyperparameter estimation (`nh=0`, `M(i).Q`/`M(i).R` unset). The Python
implementation in `code/` reconstructs the **reduced dynamics that remain**
(gradient flow on generalized causes `v` under precision-weighted prediction
error, and gradient flow on action `a` under the same, restricted by `R`)
using an explicit-Euler / gradient-ascent scheme rather than `spm_ADEM`'s
Jacobian-based `spm_dx` integrator. **This is a deliberate, disclosed
simplification, not a hypothesis about the reference's behaviour** — since no
MATLAB/Octave reference run exists to validate against (§8), exactness cannot
be checked either way, so Task C's "equivalence report" is correspondingly
**NOT DONE** (no ground truth exists to compare to) — see EQUIVALENCE_REPORT.md.
