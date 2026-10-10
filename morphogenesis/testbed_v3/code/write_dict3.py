import sys; sys.path.insert(0, '.')
import build_blind3 as B, os
c = lambda l: ', '.join(str(x) for x in l)
txt = f"""# Data dictionary — culture-dish imaging and perturbation experiments, package v2

Written as an experimenter would hand over a dataset. Nothing in this package describes how the cells work internally, and no treatment is described by its effect.

## What was measured
A dish contains a compact cluster of cells (24 cells in a single-cluster run, 48 when two clusters share the dish). Each cell secretes soluble signals; the dish was imaged and the cells were tracked. The cluster sits at an arbitrary position and orientation in the dish for each run (no axes are marked on the dish). Lengths are in arbitrary arena units (a cell is about 1 unit from its neighbours), time is in arbitrary time units. Small random motion of the cells and measurement noise are present in every run. Cells are identical in manufacture; clusters differ only through the random circumstances of each dish (the body id in the catalog names the dish).

## Observation levels (files in `runs/`, four per run)
| file | level | contents |
|---|---|---|
| `<run>_O1.npz` | **O1 tracked cells** | `t` (frame times), `frame_ptr` (frame f owns rows `frame_ptr[f]:frame_ptr[f+1]`), `cell_id` (permanent id from the tracker; a newly introduced cell gets a never-used id), `xy` (arena coordinates, noise sd 0.02), `level` (**7 columns**, fixed order for the whole package: the secreted level of seven signals as read by the imaging assay; multiplicative noise 3 %) |
| `<run>_O2.npz` | **O2 unlabelled points** | as O1 without `cell_id`; rows of each frame in random order; `level` has **5 columns**, which are O1 columns {c(B.O2_COLS)} (in that order) — the two other O1 signals were not assayed in this mode |
| `<run>_O3a.npz` | **O3 images, variant a** | `t`, `image`: array (frames, 3, {B.IMG_PX}, {B.IMG_PX}) float16, the fluorescence field of three signals — O1 columns {c(B.O3A)} in that channel order — window [-fov, fov]² in arena coordinates (`fov` in the catalog), Gaussian point-spread sd {B.PSF_SIGMA}, peak SNR {B.SNR:.0f}; every `o3_every`-th frame only (see catalog interval) |
| `<run>_O3b.npz` | **O3 images, variant b** | as O3a with a fourth channel: O1 column {B.O3B[-1]} |
The two O1 columns that are not in O2 ({c([j for j in range(7) if j not in B.O2_COLS])}) were not assayed in point-cloud mode; the signal of O1 column {B.O3B[-1]} is imaged only in variant b of the image mode.

## Catalog (`catalog.csv`)
`run` file stem; `group` runs sharing a dish setup (an event run, its untreated twin and its sham share a group); `condition` opaque treatment code (`N0` untreated natural dishes; `P01…` surgical or merging operations; `T…` light experiments (the number is the light code, the letter the pulse length class); `X…` other devices); `arm`: `untreated`, `treated`, `untreated_control` (twin dish with identical random circumstances but no operation), `sham_treated` (the same procedure run without delivering the operation); `n_cells`; `n_frames`; `frame_interval` (time between frames: 100 for natural dishes, 5 for operation runs, 2 for light and device runs); `fov`; `onset` (time of the operation or light onset after the start of observation; empty for untreated); `split`; `body_id`; `noise_level`.
## Treatments (`treatments.json`, one entry per run)
Devices: **light channels L1–L5** (a light of one channel is projected on a disc of given centre `disc_xy` (arena coordinates at light onset) and radius; `amplitude` is the nominal intensity, `t_on`, `t_off`, `ramp` times); what each channel does is not described; **pipette** (point source at `xy` of reagent R1–R6; `amplitude`, times); **bath** (uniform addition of reagent R1–R6); surgery (cell replacement; cut with a line), tweezers (displacement of one cell), dish merge (two clusters brought together at a given offset). Reagents R1–R6 are not identified with signals.
## Natural dishes
Untreated dishes observed at intervals of 100 time units (8 frames per dish) after a settling period; `split` marks calibration and validation dishes.
## Splits (`split_manifest.json`)
`development`; `heldout_bodies` (body_id % 3 == 0 for operation and light runs; the validation natural dishes 400–429); `heldout_conditions` (all runs of the listed condition codes); `heldout_locations` (light runs whose disc is centred on one of two places of the cluster). No run appears in more than one split.
## Not provided
How the cells work, the identity of the signals and of the light channels, and which cluster is which.
"""
open(os.path.join(B.PKG, 'DATA_DICTIONARY.md'), 'w').write(txt); print(txt[:300])
