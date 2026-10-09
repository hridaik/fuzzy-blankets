# Data dictionary — culture-dish imaging experiments, package v1

Written as an experimenter would hand over a dataset. Nothing in this package describes how the cells work internally.

## What was measured
A dish contains a compact cluster of cells (24 cells in a single-body run, 48 when two clusters are in the dish). Each cell secretes four soluble signals; the dish was imaged and the cells were tracked. The cluster sits at an arbitrary position and orientation in the dish for each run (no axes are marked on the dish). Lengths are in arbitrary arena units (a cell is about 1 unit from its neighbours), time is in arbitrary time units. Small random motion of the cells is present in every run. Two cell lines were used, coded **S1** and **S2** (their relationship is not described here).

## Observation levels (one file per run and level, in `runs/`)
| file | level | contents |
|---|---|---|
| `<run>_O1.npz` | **O1 tracked cells** | `t` (frame times, one per frame), `frame_ptr` (frame f owns rows `frame_ptr[f]:frame_ptr[f+1]`), `cell_id` (permanent integer id given by the tracker; a new cell in the dish receives a never-used id), `xy` (arena coordinates, noise sd 0.02), `level` (4 columns: secreted level of the four signals, arbitrary column order that is the same in every run of this package; multiplicative noise 3 %) |
| `<run>_O2.npz` | **O2 unlabelled points** | as O1 without `cell_id`; the rows of each frame are in random order |
| `<run>_O3.npz` | **O3 images** | `t`, `image` (frames × 2 reporter channels × 96 × 96, float16): fluorescence-like field of two of the four signals (which two, and which is which, is not stated), arena window [−12, 12] × [−12, 12] (0.25 unit per pixel), Gaussian point-spread width 0.5 unit, additive Gaussian noise with peak signal-to-noise 20. Image frames are a subset of the O1/O2 frames: every 2nd frame (both kinds of run); use `t` to align. |
Dead or absent cells are simply not listed in a frame.

## `catalog.csv`
| column | meaning |
|---|---|
| `run` | run name (file prefix); names carry no meaning |
| `group` | `natural` for untreated dishes; otherwise `G###`, identifying a matched triplet of runs prepared identically (same cluster, same random-motion realisation) |
| `condition` | `N0` untreated; `P1`…`P6` coded treatment protocols (descriptions withheld) |
| `strain_code` | S1 or S2 |
| `arm` | `untreated` (natural run), `treated` (protocol applied), `untreated_control` (matched control of a treated run, nothing done), `sham_treated` (matched run on which the protocol's procedure was performed with zero strength) |
| `treatment` | protocol code for treated and sham runs |
| `onset` | time (run time, same units as `t`) at which the protocol starts; for the two-cluster protocols the clusters are in the dish from time 0 (onset 0) |
| `event_xy` | not provided (empty) |
| `n_frames`, `frame_interval` | number of O1/O2 frames and the time between them (5 for treatment runs; the natural runs have 10 frames, one every 150 time units: about the decorrelation time of the slow body deformation measured in pilots (≈ 150); fast cell-position fluctuations decorrelate in 14–20) |
| `split` | `development`, `heldout_bodies`, `heldout_conditions` (see `split_manifest.json`) |
| `body_seed` | integer identifying the particular dish (dishes with the same seed and strain are the same preparation) |
| `noise_level` | `n1`: the single noise level used |

## Matched triplets
For each `G###` there are three runs: `treated`, `untreated_control`, `sham_treated`. They were started from the same cluster with the same pose and the same random-motion sequence, so before the onset time the treated and control runs are identical up to rounding, and the sham run is identical to the control throughout. Differences after onset are due to the protocol.

## Splits (`split_manifest.json`)
`development`: all natural calibration dishes and treatment dishes whose `body_seed` is not divisible by 3; `heldout_bodies`: natural validation dishes (different seeds) and treatment dishes with `body_seed` divisible by 3; `heldout_conditions`: all runs of the protocols that are held out as whole conditions (P-codes whose runs are all marked so). There is no held-out actuator-location set in this package.

## Known limitations
24 or 48 cells; one noise level; natural runs have 10 frames spaced by 150 time units (1 500 time units after a 100-unit settling period); bodies in this dish are not durable on long times (about half of untreated bodies have fallen apart after 3 200 time units, so no run is longer than that); treatment runs last 300 time units after the start (treatment onset at 50 time units for single events, 0 for two-cluster runs). The images contain only two of the four signals.
