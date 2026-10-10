import sys, os, json; sys.path.insert(0, '.')
import build_blind4 as B4, build_blind3 as B3
ess = json.load(open(os.path.join(B4.TB, 'data', 'ess_observable.json'))); c = lambda l: ', '.join(str(x) for x in l)
def e(sp, k): return int(round(ess[sp][k]['ess_total']))
txt = f"""# Data dictionary — culture-dish imaging and perturbation experiments, package v3 (fine time resolution, cell-resolving images)

Written as an experimenter would hand over a dataset. Nothing in this package describes how the cells work internally, and no treatment is described by its effect. Package v2 is unchanged and is a different dataset: dishes, seeds and file names here are new, the opaque labels (signal columns, light codes, reagent codes, condition codes) are the same as in v2.

## What was measured
A dish contains a compact cluster of cells (24 cells in a single-cluster run, 48 when two clusters share the dish). Each cell secretes soluble signals; the dish was imaged and the cells were tracked. The cluster sits at an arbitrary position and orientation in the dish for each run (no axes are marked on the dish). Lengths are in arbitrary arena units (a cell is about 1 unit from its neighbours), time is in arbitrary time units (tu). Small random motion of the cells and measurement noise are present in every run. Cells are identical in manufacture; the body id in the catalog names the dish.

## Observation levels (files in `runs/`, five per run)
| file | level | contents |
|---|---|---|
| `<run>_O1.npz` | **O1 tracked cells** | `t` (frame times), `frame_ptr` (frame f owns rows `frame_ptr[f]:frame_ptr[f+1]`), `cell_id` (permanent id from the tracker; a newly introduced cell receives a never-used id), `xy` (arena coordinates, noise sd 0.02), `level` (**7 columns**, fixed order for the whole package: the secreted level of seven signals as read by the imaging assay; multiplicative noise 3 %) |
| `<run>_O2.npz` | **O2 unlabelled points** | as O1 without `cell_id`; rows of each frame in random order; `level` has **5 columns**, which are O1 columns {c(B3.O2_COLS)} (in that order) |
| `<run>_O3a.npz` | **O3 field images, variant a** | `t`, `image`: array (frames, 3, {B3.IMG_PX}, {B3.IMG_PX}) float16, the fluorescence field of three signals — O1 columns {c(B3.O3A)} in this channel order — window [-fov, fov]² (`fov` in the catalog), point-spread sd {B3.PSF_SIGMA}, peak SNR {B3.SNR:.0f}. The fields are smooth (effective blob width about 1.4 units, wider than the cell spacing): individual cells are not resolved. |
| `<run>_O3b.npz` | **O3 field images, variant b** | as O3a with a fourth channel: O1 column {B3.O3B[-1]} (the signal of that column is imaged only in this variant) |
| `<run>_O3c.npz` | **O3c cell-resolving images** | `t`, `image`: array (frames, 4, px_c, px_c) uint8 and `scale` (4 values; intensity = uint8 / scale), window [-fov_c, fov_c]² (`fov_c`, `px_c` in the catalog; 10 and 128 pixels for single clusters, 24 and 256 for dish-merge runs). **Channel 0 is a cell-marker image**: every cell appears as a sharp blob (Gaussian, sd {B4.MARK_SD}, that is 0.28 of the nearest-neighbour spacing; unit peak; additive noise sd {B4.MARK_NOISE}). Channels 1–3 are the fluorescence fields of O3a on the same pixel grid (smooth, as above). |
The two O1 columns that are not in O2 ({c([j for j in range(7) if j not in B3.O2_COLS])}) were not assayed in point-cloud mode.

## Time resolution
Frames are recorded every **1 tu**. In every perturbation run (surgical or merging operations, light runs and other device runs) the interval is **0.5 tu in a fine window** that starts 20 tu before the onset and ends 100 tu after the end of the treatment (`fine_window` in the catalog, in tu from the start of observation). Images (O3a, O3b, O3c) are stored at every recorded frame in light and device runs; in operation runs at integer times inside the fine window and every 2 tu elsewhere; in natural dishes every 2 tu; O3c in dish-merge runs every 4 tu. The exact image times are the `t` arrays of the image files.
**Natural dishes are long**: 5,600 tu each after the settling period (50 times the slowest relaxation visible in the cluster shape, about 112 tu), 12 calibration and 6 disjoint validation dishes per kind of dish (24 + 12 dishes in all). Effective sample sizes (initial-positive-sequence autocorrelation estimate, observable variables from O1 only, summed over dishes; calibration | validation): shape of the cluster (log ratio of the principal axes) {e('development','shape_logratio')} | {e('heldout_bodies','shape_logratio')}; mean of O1 column 0 {e('development','level_mean_c0')} | {e('heldout_bodies','level_mean_c0')}; column 4 {e('development','level_mean_c4')} | {e('heldout_bodies','level_mean_c4')}; column 6 {e('development','level_mean_c6')} | {e('heldout_bodies','level_mean_c6')} (full table: `ess_observable.json` in this package).

## Catalog (`catalog.csv`)
`run` file stem; `group` runs sharing a dish setup (an operation run, its untreated twin and its sham share a group); `condition` opaque treatment code (`N0` untreated natural dishes; `P01…` surgical or merging operations; `T…` light experiments (number = light code, letter = pulse length class); `X…` other devices); `arm`: `untreated`, `treated`, `untreated_control` (twin dish with identical random circumstances but no operation), `sham_treated` (the same procedure without the delivered operation); `n_cells`; `n_frames`; `frame_interval` (1 tu); `fine_window` and `fine_interval` (0.5 tu); `fov` (O3a/O3b window), `fov_c`, `px_c` (O3c); `onset` (time of the operation or light onset after the start of observation); `split`; `body_id`; `noise_level`.
## Treatments (`treatments.json`)
Devices: **light channels L1–L5** (a disc of given centre `disc_xy` (arena coordinates at light onset) and radius; `amplitude` nominal intensity, `t_on`, `t_off`, `ramp`; what each channel does is not described); **pipette** (point source of a reagent R1–R6 at `xy`), **bath** (uniform addition of a reagent); surgery (cell replacement; cut along a line), tweezers (displacement of one cell), dish merge (two clusters brought together at a given offset; in the twin and sham arms the two clusters are in the dish far apart). Reagents are not identified with signals.
## Splits (`split_manifest.json`)
`development`; `heldout_bodies` (body_id % 3 == 0 for operation and light runs; the validation natural dishes 2400–2405); `heldout_conditions` (all runs of the listed condition codes); `heldout_locations` (light runs whose disc is centred on one of two places of the cluster).
## Not provided
How the cells work, the identity of the signals and of the light channels, and which cluster is which.
"""
open(os.path.join(B4.PKG, 'DATA_DICTIONARY.md'), 'w').write(txt); print('dictionary written', len(txt))
