# OBSERVATION_LADDER.md — Part G

**These rendering choices constitute an observer model.** Nothing here is
"the data" in any theory-neutral sense — every choice (field of view, blob
sigma, noise level, normalization, grid resolution) is a declared modeling
decision that a later blind stage must treat as part of its observation
process, not as ground truth. This stage generates these products and does
**not** analyse them (per the STOP conditions).

## Renderer

`code/observation_ladder.py`, deterministic and versioned
(`RENDERER_VERSION = "m1-obsladder-v1"`). Given the same rollout `.mat` file,
run ID string, and frame index, every random choice (O2's permutation, O3's
noise) is reproducible: seeded via
`sha256(version|run_id|frame_idx|salt)[:8 bytes] -> uint64 seed`. Callable
on demand for any stored rollout at any frame (`render_O2`/`render_O3a`/
`render_O3b`/`render_O4` are pure functions of a single frame's
`(a_x, a_s)`, not a whole-rollout state machine).

## O1 — tracked positions and secretion

Already produced by the m0c fallback engine (`positions`, `secretion` in
every rollout `.mat`) — no additional rendering needed. Declared: full,
labeled (cell-index-ordered), noiseless.

## O2 — unlabelled point clouds

Per frame, cell order is independently, randomly permuted (`render_O2`,
seeded as above) and the arrays are cast to `float16`. **No persistent cell
ID exists anywhere in these files** — a later stage attempting to track
identity across frames from O2 alone must do so from position/secretion
continuity, not from array index, by construction.

## O3a / O3b — images

**Declared parameters** (all in `observation_ladder.py`, restated here):
- Field of view: `[-4,4] × [-4,4]` in template units (the target template
  itself spans roughly `[-2.75,2.75] × [-1,1]`; checked against Part C's
  largest kicks — `K1_sigma1.5` and `K4`'s 3-spacing-unit displacement — to
  confirm this FOV comfortably encloses the visited range with margin, not
  merely the resting template).
- Image size: `96×96` px.
- Each cell rendered as an isotropic Gaussian blob, `sigma=2.5px`.
- O3a: **4 channels** = all 4 rows of the engine's own secretion array
  `a.s` (row 0 is the trivial "existence" channel, always ≈1 for a live
  cell — included because the task specifies "the 4 secreted levels"
  literally, not "the 3 informative ones"; see m0's `MODEL_SPEC.md` for why
  row 0 is trivial).
- O3b: **2 channels** = rows 1,2 of `a.s` (the paper's "signal 2" and
  "signal 3", excluding the trivial row 0 and row 3/"signal 4"), "mimicking
  two reporters" per the task.
- Per-frame normalization: image divided by its own max before noise
  (declared choice — this means absolute secretion magnitude is **not**
  directly recoverable from O3a/O3b alone, only relative/normalized
  intensity; a later stage should not assume otherwise).
- Noise: **declared SNR = 10 dB**, implemented as additive Gaussian noise
  at the corresponding power, **plus** a Poisson-like term (`rng.poisson`
  on a scaled image, rescaled back and weighted 0.3×) to emulate
  photon-counting-style noise alongside pure Gaussian read noise. Both
  terms use the SAME per-frame seed derivation, so are reproducible.
- Stored as `uint8` (0-255).

## O4 — ligand concentration maps

**No cell positions in the output files** — only the resulting field.
Computed via the engine's own field law (`model.field_concentration`,
m0b-validated, unmodified — not re-derived). Grid: `32×32`, same
`[-4,4]×[-4,4]` FOV as O3. All 4 signal channels. Stored as `float16`
(concentration values are unbounded in principle, unlike O3's normalized
0-255 images, so no uint8 quantization here).

## Storage

Estimated **before** writing (`≈2.2-4 GB`), per the ground rules. **Actual,
final**: all 705 rollouts rendered (250 census + 55 rescue + 100 kicks + 60
SUSTAINED twins + 180 withdrawal + 60 sham) — **1.8 GB total**,
comfortably under the 50 GB cap. No storage-triggered stop was needed at
any point.

## What is NOT done in this stage

Per the explicit STOP conditions: **these products are generated and
stored, never analysed, never fed to a representation-learning or
detection pipeline, and no interior/boundary/exterior partition is drawn
from them.** Any future blind stage consuming O2-O4 must treat every
parameter in this document as part of the observation process under test,
not as a neutral ground-truth channel.
