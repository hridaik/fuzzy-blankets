# DISCREPANCIES_UPDATE.md — corrections to `m0_reconstruction/DISCREPANCIES.md`

## Correction 1 (the one the task explicitly flagged): initial-expectation precision is REAL, distinct from the prior precision, and m0 was wrong to close it

**m0's `DISCREPANCIES.md` §4 concluded**: "no discrepancy" — reasoning that
the 2015 paper's stated "log precision -2" (for `M(2).V`, the *prior*
precision on the causal state `v`) matched the code's `exp(-2)` exactly, and
that the task prompt's separate mention of "log precision -4" for *initial
expectations* was "a probable transcription error in the task prompt," since
m0 could not find "-4" anywhere in the paper text it read.

**This was wrong. `m0_reconstruction` did not read carefully enough.** The
2015 paper contains **two separate, correctly-quoted statements about two
different quantities**, both re-confirmed by direct PDF read in this
session (`sources/papers/friston2015.pdf`):

1. **p.6, §4** (describing the generative model's prior term, `Π^(2)`):
   > "We assumed (zero-mean) Gaussian priors over the hidden states with a
   > small precision Π⁽²⁾ (with a log precision of **minus two**)."
   This is the *ongoing* prior precision used throughout the free-energy
   minimization (matches code `M(2).V = exp(-2)` exactly — `ESTABLISHED`,
   this part of m0's finding was correct).

2. **p.7, left column** (describing the *initial condition* used to start
   the simulation shown in Fig. 3), a **separate sentence about a separate
   quantity**:
   > "All the cells started at the same location and with undifferentiated
   > expectations about their fate (using small random expectations with a
   > **log precision of minus four**)."
   This describes the **initial draw** of `v` (the recognition density's
   starting point), not the prior term. **`ESTABLISHED`, directly quoted,
   re-confirmed by a second independent read in this session.**

**Corrected comparison to code**: the canonical script draws
`v = randn(n,n)/8` (`DEM_morphogenesis.m` line 91), i.e. σ=0.125,
**implied precision ≈ 1/0.125² = 64, log-precision ≈ ln(64) ≈ 4.16**. The
paper's stated **log-precision −4** for this same initial draw implies
**precision ≈ exp(−4) ≈ 0.018, σ ≈ 7.39** — a value **~59× larger** than the
code's actual σ. **This is a genuine, large, and previously-mis-closed
discrepancy between the 2015 paper and the code for the initial-condition
draw**, running in the *opposite direction* from what "small random
expectations" suggests informally (the paper's stated precision implies a
much *wider*, less confident initial spread than the code actually uses).
`ESTABLISHED discrepancy — REOPENED`.

Net correction: **m0_reconstruction was right that `M(2).V` (the ongoing
prior) matches the paper's −2, and wrong to conclude this meant the
separately-quoted −4 (for the initial draw) was a prompt error.** Both
figures are real, refer to different quantities, and only the −2 one
matches the code.

## Correction 2: Kuchling et al. (2020) confirms a THIRD developmental-sensitivity form, and gives its own precision values

Not a correction of an m0 error, but new information m0 did not have (it
only compared the 2015 paper and the code). Kuchling 2020 (p.16-17, eq. 43,
directly read this session) gives:

- Developmental sensitivity: `τ = 1 - exp(-t/T)`, `T = 1/ln(2)` — an
  **exponential approach parametrized by a half-life**, distinct from both
  the 2015 paper's linear ramp and the code's `1-exp(-2t)`. See
  `PERTURBATIONS.md` §1 for the three-way table. `ESTABLISHED`.
- Signal precision `Π^(1) = 1` (p.17) — a **fourth** value for this
  quantity, alongside the 2015 paper's 2, the code's `exp(3)`≈20.1, and the
  2022 paper's "set to 1" (per m0's summary, not independently re-verified
  against the 2022 PDF in either session). Kuchling 2020's figure (1)
  happens to match the 2022 paper's reported figure exactly — both papers
  from overlapping author groups (Levin, Friston co-author both) may share
  this convention. `ESTABLISHED` for Kuchling 2020's own stated value.
- Prior precision `Π^(2)`: "small precision... log precision of minus two"
  (p.17) — **matches the 2015 paper and the code exactly**, a third
  independent confirmation of this one figure. `ESTABLISHED`.

## Correction 3: none found to m0's field-law, softmax, or restriction-matrix findings

These were re-verified (not just re-read) in this session via live Octave
execution (`ORACLE_REPORT.md`) and stand as m0 reported them. No correction.

## Standing (unchanged) discrepancies from m0, re-confirmed

- Sensory precision: paper (2015) log-2 vs. code `exp(3)` (log-3) —
  `ESTABLISHED`, re-confirmed by direct PDF quote in m0 and again in this
  session.
- Developmental-sensitivity functional form: paper (2015) linear vs. code
  exponential-saturating — `ESTABLISHED`, re-confirmed, and now joined by a
  third form (Kuchling 2020, Correction 2 above).
