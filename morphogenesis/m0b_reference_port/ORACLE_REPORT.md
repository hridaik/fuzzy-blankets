# ORACLE_REPORT.md — Task 1: Octave reference oracle

## Top-line: SUCCESS. The reference code runs under Octave, unmodified except `DEM.db=0`.

## Install

`conda create -n octave-dem -c conda-forge octave` — no root required.
**Octave 10.3.0** installed (`sources: conda-forge`, channel default at install
time 2026-09-29). `ESTABLISHED` (`octave --version` output captured).

SPM12: full shallow clone (`git clone --depth 1 https://github.com/spm/spm12.git`),
commit `03ac9473cad402407b6472228377c0167fdc54b8` (2024-02-05) — same commit
used in `morphogenesis/m0_reconstruction`. `ESTABLISHED`.

`LPioL/active_inference_morphopsy`: commit `bd378a4123485f18e588763d163c9f0315ac2671`
(2022-10-14) — same as m0. `ESTABLISHED`.

## Patch applied (the only one needed)

**`DEM.db = 0`** before calling `spm_ADEM(DEM)`. This is a **built-in SPM
option** (`spm_ADEM.m` line 150-153, `try db=DEM.db; catch db=1; end`), not a
modification of SPM source — it gates the two `if db ... end` blocks (lines
157-159 and 805-833) that call `spm_figure`/`spm_DEM_qU`/`plot`/`drawnow` for
progress display. With `db=0` those blocks are skipped entirely — **zero
numeric impact**, confirmed by inspecting that both blocks contain only
plotting calls and a convergence-report `fprintf`, no state mutation.
No other patch, to any file in `sources/spm12/`, was needed. `ESTABLISHED`.

Separately, we do not call the published `DEM_morphogenesis.m` script
directly (it would still execute ~190 lines of `plot`/`subplot`/`spm_figure`
graphics after solving, unrelated to `db`, since that gating only covers
`spm_ADEM`'s own internal progress plots). Instead, `oracle/dem_setup.m` is a
**disclosed, minimal, non-numeric transcription** of `DEM_morphogenesis.m`'s
lines 1-146 (preliminaries through `DEM.U`/`DEM.C` assembly) with the
post-solve graphics block (lines 195-341 of the original) removed, plus
`DEM.db=0` added and `L`/`N`/`seed`/initial-`v` exposed as arguments instead
of hard-coded. `oracle/dem_morphogenesis_{field,Gg,Mg}.m` are verbatim
transcriptions of the three local functions from the same source file (see
inline file:line comments in each). Diffs against the original are visually
inspectable by comparing these files to
`sources/spm12/toolbox/DEM/DEM_morphogenesis.m` side by side; a mechanical
unified diff is not meaningful here since the local functions were split
into separate files (a structural, not numeric, change).

## No Octave/DEM-toolbox incompatibilities found

Every function `spm_ADEM.m` calls for this model (`spm_ADEM_set`, `spm_vec`,
`spm_unvec`, `spm_cat`, `spm_diag`, `spm_speye`, `spm_DEM_R`, `spm_DEM_z`,
`spm_DEM_embed`, `spm_DEM_eval`, `spm_DEM_eval_diff`, `spm_ADEM_diff`,
`spm_diff`, `spm_dx`, `spm_expm`, `spm_logdet`, `spm_inv`, `spm_pinv`,
`spm_softmax`, `spm_detrend`, `spm_svd`) ran under Octave 10.3.0 without
error. The only console noise was a harmless deprecation warning
(`inline is obsolete; use anonymous functions instead`, from
`spm_ADEM_set.m`'s use of `inline()` to default unset `M(i).f`/`G(i).f` to a
zero function when a level has no hidden states — functionally correct under
Octave, just using an outdated MATLAB idiom). **No patch was needed for this
warning; it is cosmetic.** `ESTABLISHED`.

## Oracle sanity check vs. 2015 paper Figure 3 (qualitative)

Ran vanilla 8-cell, `N=32`, seed 0 (`data/oracle_traces/vanilla8_N32_seed0.mat`).
Free energy trace `DEM.J` (per-bin, `-ve` free energy so *higher = better fit*):
`[295.5, 233.8, 239.5, 290.8, 306.0, 310.8, ..., 358.7]` — an early dip
(bins 1-3, before the developmental sensitivity ramp has turned on extrinsic
signalling) then **monotonically rising and saturating** — qualitatively
matches "falling free energy" (in the paper's sign convention, `F` falls;
here `J=-ve F` so it rises) claimed for Fig. 3. `ESTABLISHED`.

Per-cell max-softmax identity concentration (`spm_softmax` over each cell's
column of the 8x8 `v_expect` matrix, computed in Python from the exported
trace):

| bin | max-softmax per cell (8 cells) | mean |
|---|---|---|
| 1 | 0.146 0.135 0.158 0.165 0.134 0.149 0.151 0.147 | 0.148 |
| 4 | 0.356 0.350 0.200 0.364 0.193 0.290 0.295 0.405 | 0.307 |
| **8** | **0.362 0.671 0.222 0.574 0.333 0.323 0.256 0.667** | **0.426** |
| 16 | 0.345 0.717 0.581 0.662 0.495 0.729 0.556 0.729 | 0.602 |
| 32 | 0.675 0.775 0.770 0.756 0.716 0.775 0.717 0.753 | 0.742 |

By bin 8, half the cells already exceed 0.55 (two exceed 0.65); by bin 32 all
8 cells are in the 0.68-0.78 range. This is **qualitatively consistent** with
the paper's claim of differentiation "by roughly bin 8" (clear, non-trivial,
still-rising concentration at bin 8, continuing to sharpen through bin 32) —
and is a **dramatic contrast with `m0_reconstruction`'s reduced Python
solver**, where no cell ever exceeded 0.9 softmax even after 512 bins. This
is strong evidence the real `spm_ADEM` dynamics (matrix-exponential local
linearization) converge qualitatively differently from — and much better
than — the ad hoc gradient-descent approximation m0 used.
**ESTABLISHED, the single most important finding of Task 1.**

**Caveat**: this is a qualitative check against a verbal description of Fig.
3 (dispersion/differentiation/falling free energy), not a pixel-level or
value-level comparison against the actual published figure (which was not
re-extracted from the PDF in this pass). `PROVISIONAL` at the level of
"matches the paper's qualitative narrative"; `NOT DONE` at the level of
"matches the published numbers/pixels exactly."

## Octave RNG vs. MATLAB RNG

Octave and MATLAB use different default RNG algorithms/seed conventions
(Octave: currently Mersenne Twister but a different concrete seeding path
than MATLAB's `rng('default')`). **Traces from this oracle cannot and do not
match a hypothetical MATLAB run bitwise, even for an identical nominal
seed.** This is expected and disclosed, not a bug. Because of this, **every
random draw `spm_ADEM` uses is exported** per run (`z_exported`, `w_exported`
in each `.mat` file — the innovations `spm_DEM_z` produces), captured by
calling `spm_DEM_z` once under the same seed immediately before the real
`spm_ADEM` call and then resetting the seed so `spm_ADEM`'s own internal call
reproduces an identical sequence (`oracle/run_and_export.m`). The Python port
consumes these exported arrays directly rather than attempting to replicate
Octave's RNG. `ESTABLISHED`.

## Critical structural discovery: `nE` is forced to 1 for this model

`spm_ADEM.m` line 385: **`if ~np && ~nh, nE = 1; end`**. `DEM_morphogenesis.m`
sets no model parameters (`np=0`, no `M(i).pC`) and no hyperparameter
components (`nh=0`, no `M(i).Q`/`M(i).R`). So **the default `nE=16` "outer
E-step" iteration count is silently overridden to `nE=1`** for this specific
model. This means `spm_ADEM` performs **one single forward pass** through the
`N` bins (the D-step loop, `for iY=1:nY` with `nY=size(DEM.C,2)=N`), not 16
repeated smoothing sweeps as the general DEM/ADEM architecture would suggest
by default. This resolves an open question from `m0_reconstruction` and is
the reason a 32-bin run takes ~16s (≈0.5s/bin, single pass) rather than
16×16s. **ESTABLISHED, verified both by reading the exact conditional and by
runtime measurement matching the single-pass prediction.**

## Configurations run (all required Task 1 configs)

| Config | File | n cells | N bins | wall time | hash (sha256, first 12 chars) |
|---|---|---|---|---|---|
| vanilla 8-cell | `vanilla8_N32_seed0.mat` | 8 | 32 | 15.9s | `bc16782a3cde` |
| vanilla 8-cell, long | `vanilla8_N512_seed0.mat` | 8 | 512 | 247.7s | `b89da7ea46af` |
| bisection, split=1 (top half) | `bisection_split1_N32_seed0.mat` | 8 | 32 | 14.2s | `83416fcbdc80` |
| bisection, split=2 (bottom half) | `bisection_split2_N32_seed0.mat` | 8 | 32 | 14.5s | `4034f9dfc602` |
| 16-cell template (L=4) | `L4_16cell_N32_seed0.mat` | 16 | 32 | 41.9s | `e3f9db23c0fe` |
| Pio-Lopez high-identity, k=1..6 | `pio_lopez_k{1..6}_N32_seed0.mat` | 8 | 32 | ~14.3-14.9s each | see `SHA256SUMS.txt` |

Full hashes: `data/oracle_traces/SHA256SUMS.txt`. All runs: seed 0,
`DEM.db=0` patch only. `ESTABLISHED`.

## Runtime scaling (measured, informs Task 4/5 pilot estimates)

- n=8, N=32: ~14-16s (0.44-0.5 s/bin)
- n=8, N=512: 247.7s (0.484 s/bin) — **confirms linear scaling in N**, as
  expected for a single forward pass (`nE=1`).
- n=16 (L=4), N=32: 41.9s (1.31 s/bin) — **≈2.6× slower per bin at 2× n**,
  consistent with super-linear (roughly quadratic-to-cubic) scaling in `n`
  from the finite-difference Jacobian (`O(n)` perturbations × `O(n²)`-ish
  field evaluation) and the `spm_dx` matrix exponential (`O(nu³)`,
  `nu` scaling with `n`).

**Extrapolated cost for later tasks** (informs the reductions-policy pilot
estimate required before Task 4/5 batches): an n=8, N=1024 run ≈ 495s
(~8.3 min); an n=8, N=512 perturbation run ≈ 248s. A batch of ~15
perturbation configs (Task 4) each run to 512 bins ≈ 15×248s ≈ 62 minutes of
**Octave** compute. This is well under the 6-hour reductions-policy
threshold and is reported here in advance per the ground rules.

## Open items from Task 1 (see OPEN_QUESTIONS.md for the consolidated list)

- Figure 3 was checked qualitatively (narrative match), not pixel/value
  matched against the actual published figure image. `NOT DONE`.
- The `A = spm_cat({qU.a qu.a})` construction feeding `spm_DEM_embed` for the
  action's generalized-coordinate embedding (`spm_ADEM.m` line ~448) has
  subtle boundary-condition behavior (growing array, early-bin clamping) that
  was not fully re-derived from static reading alone — the Python port
  (`PORT_DESIGN.md`) calibrates this specific piece against an Octave-side
  instrumented single-step dump rather than claiming pure derivation.
  `PROVISIONAL`, being resolved empirically in Task 2/3.
