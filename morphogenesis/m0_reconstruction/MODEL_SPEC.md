# MODEL_SPEC.md — Stage M0 source specification

Status of every claim below is labeled **ESTABLISHED** (verified directly in code/output in this repo), **PROVISIONAL** (inferred, not directly verified), or **NOT DONE**.

Primary reference file: `sources/spm12/toolbox/DEM/DEM_morphogenesis.m`, cloned from
`https://github.com/spm/spm12` (GitHub mirror of the FIL SPM12 distribution),
commit `03ac9473cad402407b6472228377c0167fdc54b8` (branch `main`, fetched 2026-09-25).
**ESTABLISHED**: this is byte-identical (module body, differs only in copyright-year
header comment) to `toolbox/DEM/DEM_morphogenesis.m` on SPM's SPM25 `25.01_release`
branch, commit `76167510b7190027995325d609a2365d9a7b6bc2` — see DISCREPANCIES.md §1.
The file carries an internal SPM revision tag `$Id: DEM_morphogenesis.m 7679
2019-10-24 15:54:07Z spm $`, i.e. authored/last-touched 2019-10-24, predating both
the 2022 Pio-Lopez paper and this fetch. **ESTABLISHED**.

No MATLAB or GNU Octave is installed in this environment and the user declined
installing Octave for this stage (see conversation record). **Nothing in this
document was executed** — every fact below is read directly from source text,
not from running output. Task B (golden traces) is therefore **NOT DONE** in
its entirety; see README.md top-of-file warning.

---
## 1. Target template decoding (file: `sources/spm12/toolbox/DEM/DEM_morphogenesis.m`)

- `L=2` (line 44) selects the 8-cell template `T`, an 11-column x 6-row integer
  matrix (lines 46–51). `L=4` (unused when `L=2` is set, lines 54–66) selects a
  22-column x 11-row alternative "larger template". **ESTABLISHED**: only `L=2`
  runs (no branch selects `L=4`; it is dead code under the hard-coded `L=2`).
- Cell existence mask: `p(:,:,1) = T > 0` (line 69). Cell positions
  `[y,x] = find(p(:,:,1))`; `P.x = spm_detrend([x(:) y(:)])'/2` (lines 74–75) —
  i.e. raw (row,col) grid coordinates of nonzero template entries, mean-centered
  by `spm_detrend` (removes the column mean) then divided by 2 (arbitrary units,
  presumably one grid cell = 0.5 units after centering). **ESTABLISHED**.
- Number of cells `n = size(P.x,2)`. For `L=2`: counted directly from `T`,
  **n = 8** (verified by counting nonzero entries of the `L=2` matrix in Python:
  8 nonzero cells at grid positions (1,3),(2,5),(3,1),(3,7),(3,9),(3,11),(4,5),(5,3)
  using 1-indexed (row,col)). **ESTABLISHED**.
- Signal codes: `p(:,:,2) = T==2 | T==1`, `p(:,:,3) = T==3 | T==1`,
  `p(:,:,4) = T==4` (lines 70–72). So `T` values encode a 3-bit-ish code over
  3 binary signals (`m=3` "type" signals) via integer codes {1,2,3,4}: code 1 →
  signals 2 AND 3 on; code 2 → signal 2 only; code 3 → signal 3 only; code 4 →
  neither 2 nor 3 (only signal 4, see below). **ESTABLISHED** from the boolean
  expressions; the *biological* naming of these signals is not given anywhere in
  the code or comments — no docstring names them. **NOT DONE** (no further named
  interpretation is available in this source tree; DEM_morphogenesis.m's header
  comment (lines 2–21) only says signal expression determines "cell type" without
  naming individual channels).
- `p(:,:,1)` (existence) is itself used as a 4th boolean channel in
  `P.s(1,:)` (always 1 for every real cell, since `j=find(p(:,:,1))` already
  restricts to existing cells) — so effectively `P.s` row 1 is constant 1 and
  carries no information; only rows 2–4 (`m=4` total from `size(p,3)`, line 80)
  vary. **ESTABLISHED** by inspection: `m = size(p,3) = 4` includes the trivial
  existence channel.
- Cell-type counts (from the `L=2` `T` matrix, code values in {1,2,3,4} at the 8
  nonzero positions): value 2 appears 3×, value 1 appears 2×, value 4 appears
  2×, value 3 appears 1×. **ESTABLISHED** (direct count).
- Body length / neighbour spacing: **NOT DONE** — not computed in this stage
  (would require running the Python port; deferred, no execution performed yet
  beyond source reading).
- Larger template (`L=4`, lines 54–66): 22×11 matrix; nonzero-entry count and
  decoding **NOT DONE** (not counted/decoded in this pass — flagged for a later
  pass of Task A; low priority since `L=4` is dead code in the published script).

## 2. Sensory channels and field law

- `P.c = morphogenesis(P.x, P.s)` (line 87): the local function `morphogenesis`
  (lines 350–376) computes, for each sample location `y` (default: cell
  locations `x`), `c(:,i) = Σ_j exp(-k*d_ij) * s(:,j)` with `d_ij = ‖y_i - x_j‖`
  (Euclidean) and **k = 1 fixed** (line 361, hard-coded, not a parameter).
  This is an isotropic exponential-decay diffusion-like field law, summed over
  all cells (source superposition), evaluated at every sample point independent
  of any grid/mesh. **ESTABLISHED**.
- Sensory channels per cell, set by `Mg` (model, lines 397–410) / `Gg` (process,
  lines 381–394):
  - `g.x` (2-vector): expected/actual 2D position.
  - `g.s` (4-vector, one per signal channel `m=4`): intrinsic (self-secreted)
    signal level.
  - `g.c` (4-vector): extrinsic (field-sensed) signal concentration at the
    cell's own location, **scaled by the developmental sensitivity factor `s`**
    (see §3).
  **ESTABLISHED**.

## 3. Developmental sensitivity factor and the global `t` — resolves ground-rule question (a)

- `Gg` and `Mg` both do:
  ```
  global t
  if isempty(t); s = 0; else; s = (1 - exp(-t*2)); end
  ```
  (`DEM_morphogenesis.m` lines 382–387 [`Gg`], 398–403 [`Mg`]).
  **ESTABLISHED**: this is the code form `1 - exp(-2t)`, matching the ground-rule
  description, NOT the 2015 paper's stated "linear ramp over [0,1]" — this is a
  **confirmed discrepancy**, logged in DISCREPANCIES.md §2.
- **`t` IS assigned** during `spm_ADEM` integration. In
  `sources/spm12/spm_ADEM.m` line 202, `global t` is declared once before the
  D-step loop; inside the per-sample D-step loop (`for iY = 1:nY`, line 439) the
  very first statement is:
  ```
  % time (GLOBAL variable for non-automomous systems)
  t = iY/nY;
  ```
  (line 444, comment on line 443 is original source text, including its typo
  "non-automomous"). Here `nY` is the number of generalized-coordinate samples
  per bin — **NOT DONE**: this pass did not trace `nY`'s exact relation to the
  outer bin index vs. within-bin embedding samples (spm_ADEM interleaves an outer
  E-step loop over `nE` iterations with this D-step loop; whether `t` resets or
  accumulates across outer E-step iterations was not traced). What is
  **ESTABLISHED** is: (i) `t` is a fraction in `(0, 1]` — never exactly the
  developmental-bin index, and never zero after the first sample; (ii) it is
  reassigned every D-step sample, monotonically increasing within a call to
  `spm_ADEM`; (iii) it is **not reset to 0** between the two halves of the
  optional bisection call (`DEM = spm_ADEM(DEM)` is called a second time at
  line 187/149 in the two source variants, and `global t` retains its value from
  the end of the first call unless MATLAB's `clear global` (line 31, run once at
  script start) is re-executed — it is not re-executed before the second call).
  So: **the extracellular (`g.c`) signal is NOT zero throughout** — sensitivity
  `s = 1 - exp(-2t)` ranges roughly from `1-exp(-2/nY)` (small, but nonzero) up to
  `1-exp(-2) ≈ 0.865` at `t=1`, and beyond into `>0.865` for any subsequent
  `spm_ADEM` call (bisection) where `t` is not reset to near 0. **This must be
  stated at the top of README.md per the ground rules — done.**

## 4. Generative model / process precisions — resolves ground-rule question (b)

All in `DEM_morphogenesis.m`:
- `G(1).V = exp(16)` (line 106): generative-**process** sensory noise precision
  (i.e., the process is treated as near-noiseless/ground truth).
- `G(1).U = exp(2)` (line 107): action precision.
- `G(2).V = exp(16)` (line 116): precision on exogenous cause at level 2 of the
  process (unused; `G(2).v = 0` always, line 115).
- `M(1).V = exp(3)` (line 126): **generative-model sensory precision** — this is
  the quantity the ground rules ask about. **ESTABLISHED**: canonical SPM12/SPM25
  `DEM_morphogenesis.m` uses **`exp(3) ≈ 20.09`**, i.e. log-precision **3**, NOT
  the 2015 paper's stated log-precision 2, NOT the 2022 paper's stated "set to
  1", and NOT the `exp(3)` Pio-Lopez-variant value mentioned in the ground rules
  (which happens to match this canonical file exactly — see DISCREPANCIES.md §3
  for the three-way comparison). All 6 files in the `morphopsy` repo (the
  high-expectation-identity perturbations) leave this line unchanged at
  `M(1).V = exp(3)` (confirmed: `grep -n "M(1).V" sources/morphopsy/*.m` — all 6
  identical) — **ESTABLISHED**.
- `M(2).V = exp(-2)` (line 132): prior precision on the level-2 cause
  (identity-expectation vector `v`). **ESTABLISHED, and confirmed to match the
  2015 paper exactly**: the paper (p.6, §4) states "Gaussian priors over the
  hidden states with a small precision Π⁽²⁾ (with a log precision of minus
  two)" — log-precision **−2**, matching `exp(-2)` precisely. (The ground-rule
  prompt's summary said "-4"; that figure was not found in the paper and is
  treated as a prompt transcription error — see DISCREPANCIES.md §4.)

## 5. Initial expectations and initial positions — resolves ground-rule question (c)

- Canonical file (`sources/spm12/toolbox/DEM/DEM_morphogenesis.m` line 91):
  ```
  v = randn(n,n)/8;      % states (identity)
  ```
  preceded by `rng('default')` (line 32) at the top of the script (MATLAB's
  documented default RNG re-seed: Mersenne Twister with seed 0). So the
  canonical script uses **small random initial expectations** (Gaussian,
  σ=1/8), consistent with the 2015 paper's description of small, zero-mean
  Gaussian priors of log-precision −2 (confirmed by direct read of the paper;
  see DISCREPANCIES.md §4 — the ground-rule prompt's "-4" figure was not found
  in the paper and is treated as a transcription error, not a real
  discrepancy). **ESTABLISHED.**
- All 6 `morphopsy` perturbation files instead hard-code an explicit 8×8 numeric
  matrix for `v` (shown in full in §6 below) with two rows overwritten by
  `exp(6)` in `k` of the 8 columns (k = 1..6 across the 6 files) — this is the
  "high identity expectation in k cells" perturbation. **ESTABLISHED** by direct
  diff (see §6).
- Initial positions derive from initial expectations, not independently: line
  92, `g = Mg([], v, P)`, then `a.x = g.x` (line 93). `Mg` computes
  `g.x = P.x * p` where `p = spm_softmax(v)` (softmax over rows, i.e. per-column
  distribution over the `n` template identities — verified from
  `sources/spm12/spm_softmax.m` docstring: "softmax function over columns" /
  `y = exp(k*x)/sum(exp(k*x))` summed down each column). So **every cell's
  initial position is a softmax-weighted mixture of all `n` prototype
  positions**, not the prototype position itself, and with `v` initially
  near-zero-mean-random, the softmax is initially near-uniform (1/n per row) so
  **all cells start near the centroid of the template** (consistent with the
  paper's description of self-assembly "from a common starting point").
  **ESTABLISHED**.

## 6. Pio-Lopez (2022) perturbation: "high identity expectation in k cells"

Source: `sources/morphopsy/DEM_morphogenesis_highexpectation_identity_{1..6}cell.m`,
cloned from `https://github.com/LPioL/active_inference_morphopsy`,
commit `bd378a4123485f18e588763d163c9f0315ac2671` (2022-10-14). **ESTABLISHED**.

- **Only this one perturbation family exists in this repository.** The ground
  rules ask about four Pio-Lopez perturbations (high identity expectation;
  high sensory precision; low sensory precision; rescue by reduced
  signalling/sensitivity). **Only "high identity expectation" is present as
  code** in `LPioL/active_inference_morphopsy` at this commit. The repo's
  `README.md` (fetched, reproduced verbatim below) names only the 2022 paper
  and says nothing about additional files:
  > "You will find the code associated to the following paper: Pio-Lopez, L.,
  > Kuchling, F., Tung, A., Pezzulo, G., & Levin, M. (2022, July 9). Active
  > inference, morphogenesis, and computational psychiatry... The spm12 matlab
  > package is required."
  The other three perturbations (high/low sensory precision, rescue) described
  in the 2022 paper are therefore **NOT DONE / absent from available source** —
  logged as a discrepancy, not invented. **ESTABLISHED** (absence verified by
  `find . -type f` over the full repo checkout — only 6 `.m` files + README).
- Mechanism of the one perturbation that does exist: identical script to
  canonical `DEM_morphogenesis.m` except (i) `v` is replaced by a fixed 8×8
  numeric matrix (not `randn(n,n)/8`) whose rows 4–5, columns 1..k, are set to
  `exp(6)` instead of small values (~0.1–0.35) — diff-verified:
  `1cell.m` has `exp(6)` only in column 1 of rows 4–5; `2cell.m` also in column
  2; ...; `6cell.m` has `exp(6)` in columns 1–6 of rows 4–5 (all remaining
  columns unchanged). **This alters the initial expectation `v`, not a model
  prior precision `M(2).V` (unchanged at `exp(-2)` in all 6 files) and not the
  generative-process ground truth `P`.** So "high prior" here means: a strongly
  peaked **initial value** of the recognition density's mode for those cells'
  identity beliefs (rows 4–5 = 2 of the `n=8` candidate identities, given
  large, roughly-equal logits in a softmax-over-rows scheme this makes those 2
  candidate identities dominate the mixture for the first `k` cells) — NOT a
  change to the precision/confidence of that prior in the sense of `M(2).V`.
  **ESTABLISHED** by diff + read of `Mg`.
- No perturbation touches `M(1).V` (sensory precision) in any of the 6 files —
  confirmed via `grep -c "M(1).V" sources/morphopsy/*.m` = 1 per file, and the
  value is unchanged (`exp(3)`) in all. So **"high/low sensory precision"
  perturbations are not implemented here** — consistent with §6's absence note.

## 7. Friston (2015) perturbations — resolves ground-rule question (e)

**NOT DONE / NOT FOUND.** Neither `sources/spm12` (the files fetched: `toolbox/
DEM/DEM_morphogenesis.m`, `spm_ADEM.m`, and core `spm_*.m` utilities) nor
`sources/spm25` (same file list) nor `sources/morphopsy` contain any code
implementing: suppressed exogenous gradient, doubled vertical-gradient
sensitivity, doubled intracellular sensitivity, or quartered sensitivity to
signals 2/3. Only one generative-process/model pair (`Gg`/`Mg` in
`DEM_morphogenesis.m`) exists in the fetched SPM tree, with no perturbation
switches inside it (no `if` branches on a "condition" flag). Per the ground
rules ("If absent from code, say so; do not invent an implementation"): **these
four 2015-paper perturbations are absent from all code obtained in this stage.**
This does not rule out their existing in an SPM12 toolbox subdirectory not
fetched by this pass's sparse-checkout (only `toolbox/DEM/DEM_morphogenesis.m`
and a short list of shared utilities were pulled, not the full `toolbox/DEM/`
tree of ~230 files) — **NOT DONE**: a full-text grep of the complete `toolbox/
DEM/` directory for a second morphogenesis-related script was not performed in
this pass (would require fetching the full 230-file directory, deferred for
time). Flagged in OPEN_QUESTIONS.md.

## 8. Mechanical interaction — resolves ground-rule question (h)

**NOT DONE checked and answered: none exists.** `morphogenesis()` (the field
law, §2) and `Gg`/`Mg` contain no term referencing inter-cell distance for any
purpose other than the exponential-decay signal field. There is no volume
term, no repulsion, no adhesion, no minimum-distance clamp, anywhere in
`DEM_morphogenesis.m`. Cell "collisions" (identical or near-identical
positions) are possible and unconstrained. **ESTABLISHED** by full read of the
231-line functional part of the file (excludes the ~180-line graphics-only
tail, lines 195–341, which was skimmed, not lifted for physics).

## 9. Bisection / regeneration procedure — resolves ground-rule question (i)

Lines 153–190 (guarded by `if SPLIT`, and `SPLIT = 0` hard-coded at line 33 in
the canonical file — **so bisection never runs in the published, as-shipped
script**; it is present but dormant dead code unless a user manually edits
`SPLIT`). **ESTABLISHED**.

- Timing: fixed at bin `t = 8` (line 159; this local variable `t` **shadows**
  the `global t` used by `Gg`/`Mg` inside this block — a naming collision in the
  original source, not a bug we introduced. **ESTABLISHED**, flagged as a
  source-code oddity in DISCREPANCIES.md §5).
- Cell selection: sort cells by their bin-8 expected x-position (`v.x(1,:)`,
  first spatial coordinate) ascending (`SPLIT>1`) or descending (`SPLIT==1`),
  then take `j = [j(1:n/2) j(1:n/2)]` — i.e. **the top (or bottom) half of
  cells by position, duplicated to refill all `n` slots** (each of the `n/2`
  selected cells appears twice in the new `n`-cell population). **ESTABLISHED**.
- Duplication + noise: hidden causes `v`, model expectations `g`, and action
  `a` are all re-indexed by `j` (duplicating the selected half); then
  `a.x = a.x(:,j) + randn(size(a.x))/512` and `a.s = a.s(:,j) + randn(...)/512`
  — small Gaussian jitter (σ=1/512) added to the duplicated actions only, not
  to `v` or `g`. **ESTABLISHED**.
- Whether halves are integrated independently: **no** — both halves (upper,
  lower) are represented as `SPLIT=1` vs `SPLIT=2` on separate, sequential runs
  of the *entire* `DEM.M(1).v`/`DEM.M(2).v`/`DEM.G(2).a` state (each run
  restarts from the bin-8 state of a *single* prior full run and integrates all
  `n` cells together as one coupled system) — i.e. this is "split the
  population and re-run the whole thing from that half's duplicated state," not
  two physically separate simultaneous sub-simulations. **ESTABLISHED**.

## 10. Process noise, integration scheme

- `M(1).E.d = 1` (approximation order), `M(1).E.n = 2` (embedding order),
  `M(1).E.s = 1` (smoothness, in bins) — `DEM_morphogenesis.m` lines 38–40.
  **ESTABLISHED**.
- In `spm_ADEM.m` (lines 169–171): internally, `d = M(1).E.d + 1 = 2` (order of
  `q(v)`: value + 1 derivative) and `n_embed = M(1).E.n + 1 = 3` (order of
  `q(x)`; moot here, no hidden states `x` are defined by either `M(1)` or
  `G(1)`/`G(2)` in `DEM_morphogenesis.m` — no `.f` field is set on any level).
  **ESTABLISHED**.
- `nE = 16` (outer/E-step iterations, default, `spm_ADEM.m` line 194),
  `nM = 8` (M-step iterations, default, line 195 — moot here: no `M(i).Q`/`M(i).R`
  hyperparameter components are set in `DEM_morphogenesis.m`, so `nh = 0` and the
  M-step is a no-op), `dt = 1` (default, line 196). **ESTABLISHED**.
- `N = 32` bins (`DEM_morphogenesis.m` line 34): this is the outer developmental
  time axis length (`DEM.U`/`DEM.C` are `n²×N` / `1×N` zero arrays, lines
  122–123, i.e. 32 columns = 32 bins of exogenous cause, all identically zero —
  there is no exogenous/environmental driving signal at all in this model; all
  dynamics are self-generated through the `v`/`a` feedback loop). **ESTABLISHED**.
- Restriction matrix `R` (line 99–100):
  ```
  R = spm_cat({kron(eye(n),ones(2,2)) []; [] kron(eye(n),ones(4,4));
               kron(eye(n),ones(4,2)) kron(eye(n),ones(4,4))});
  ```
  an `(2n+4n) × (2n+4n)` block-diagonal-ish 0/1 mask (with an off-diagonal
  `kron(eye(n),ones(4,2))` block) restricting which action dimensions (`a.x`:
  2 per cell, `a.s`: 4 per cell) each sensory prediction error can drive,
  **structured strictly per-cell** (each cell's action is only driven by that
  same cell's own prediction errors — no direct cross-cell action coupling; all
  cross-cell influence is mediated through the sensed field `g.c`).
  **ESTABLISHED** from the matrix construction (block-per-cell `kron` structure);
  **NOT DONE**: the precise semantics of the asymmetric off-diagonal block
  (`kron(eye(n),ones(4,2))` in the lower-left) were not fully traced through
  `spm_ADEM`'s use of `.R` (line ~530, `dE.da = dE.dv*((dgda + dgdx*Dfdx*dfda).*R)`)
  — flagged in OPEN_QUESTIONS.md.
- Noise: `G(1).V = exp(16)` (process sensory precision, ≈8.9M — effectively a
  deterministic/near-noiseless process for our purposes) and `G(2).V = exp(16)`
  (process cause-2 precision, unused since `G(2).v=0` always). No `G(1).W`
  (state noise precision) is set — moot, since no hidden states `x` exist.
  Noise sampling itself happens inside `spm_ADEM.m` via `spm_DEM_z`/embedding
  with roughness kernel `spm_DEM_R(n_embed, s)` (`s=1`) — **NOT DONE**: the
  exact sampling distribution (`spm_DEM_z.m`) was not read in this pass (file
  was requested in the sparse-checkout list but the path pattern used,
  `spm_DEM_z.m` at repo root, does not match its actual location —
  **ESTABLISHED as a fetch gap**, not yet corrected; flagged in
  OPEN_QUESTIONS.md).

## 11. `spm_softmax` — exact definition used throughout

`sources/spm12/spm_softmax.m`: softmax **over columns** of the input matrix
(each column normalized to sum to 1 independently); optional second argument
`k` multiplies `x` by `k` before exponentiating (inverse-temperature); default
`k=1`; numerically stabilized by subtracting the per-column max before
exponentiating. **ESTABLISHED**, full text read.

## 12. Summary table

| Item | Value | Status |
|---|---|---|
| n cells (L=2 template) | 8 | ESTABLISHED |
| m signal channels | 4 (1 trivial "existence" + 3 informative) | ESTABLISHED |
| N bins | 32 | ESTABLISHED |
| Embedding order (causes) | 2 (value + 1 derivative) | ESTABLISHED |
| Smoothness s | 1 bin | ESTABLISHED |
| dt | 1 | ESTABLISHED |
| nE / nM (E/M-step iters) | 16 / 8 (M-step is a no-op: nh=0) | ESTABLISHED |
| Field law | isotropic exp(-d), k=1, linear superposition | ESTABLISHED |
| Developmental sensitivity | s(t) = 1-exp(-2t), t=iY/nY assigned every D-step sample | ESTABLISHED |
| M(1).V (model sensory precision) | exp(3) | ESTABLISHED |
| M(2).V (prior precision on v) | exp(-2) | ESTABLISHED |
| G(1).V (process sensory precision) | exp(16) | ESTABLISHED |
| G(1).U (action precision) | exp(2) | ESTABLISHED |
| Initial v (canonical) | randn(n,n)/8, rng('default') | ESTABLISHED |
| Initial v (Pio-Lopez high-identity, k cells) | fixed matrix, exp(6) in rows 4-5 cols 1..k | ESTABLISHED |
| Mechanical interaction | none | ESTABLISHED |
| Bisection (SPLIT) | dormant (SPLIT=0); at bin 8; top/bottom half by x-position, duplicated + N(0,1/512²) jitter on action only | ESTABLISHED |
| Friston 2015 4 perturbations | not found in fetched code | NOT DONE (absence established for fetched subset only) |
| Pio-Lopez high/low precision + rescue perturbations | not found in fetched code | ESTABLISHED absent from `active_inference_morphopsy` repo |
| Larger (L=4) template decoding | not decoded | NOT DONE |
