# INTERFACE.md — T3.1 observation renderer and T3.2 experimenter-level actuator API

Code: `code/interface.py` (Experiment, Mask, render_O1/O2/O3), `code/world.py`, `code/engine.py` (control inputs). Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Nothing here reveals the body frame, slots, beliefs or the template to the observer.

## Arena and hidden pose
All outputs are in ARENA coordinates. At construction the adult body is given a hidden random rigid motion (rotation ~ U(0, 2π), translation ~ U(−3, 3)² units; proper rotations only, so the form is preserved); the pose is recorded in the hidden tier only. The observer must locate and orient the body itself. Time unit and length unit are the engine's (arbitrary to the observer).

## T3.1 renderer — observation levels (declared constants in `interface.py`)
| level | content | constants |
|---|---|---|
| **O1 tracked cells** | per frame: permanent cell id, arena position, the four secreted levels (order shuffled by a package-wide opaque permutation) | localisation noise σ = 0.02 units; multiplicative level noise 3 % |
| **O2 point clouds** | as O1 without ids; rows randomly permuted in every frame | same noise |
| **O3 images** | 2 reporter channels (a declared subset of 2 of the 4 signals, opaque), concentration field Σ_j c_j,k exp(−\|r − x_j\|) on a 96 × 96 pixel grid, field of view [−12, 12]² (0.25 unit/pixel), Gaussian PSF σ = 0.5 unit, additive Gaussian noise at peak SNR 20, clipped at 0, float16 | frame interval = the run's frame interval (5 time units for stress runs, subsampled ×2; natural runs: one frame per decorrelation spacing, subsampled ×4) |
Frame rate: observation frames every `OBS_EVERY = 5` time units; actuation re-evaluated every `CHUNK = 1` time unit.

## T3.2 actuator API (`Experiment.run(T, actions, sham)`)
* **Light patterns**: masks in arena coordinates (`Mask`: union of discs and half-planes with a smooth edge of width 0.3), with **opaque channel labels** `L1…L4`; the private mapping from a label to its internal effect (fate-bias toward a type, receptor gain, secretion, migration gain) is held in `Experiment.private` and appears only in the hidden tier. The mask is evaluated at the CELL POSITIONS every chunk, so the lit cells follow the arena geometry, not the cells' identities.
* **Pipette**: point source of ligand k at an arena position (engine control `src_pos`, `src_amp`: extra field emitter with the signal's kernel). **Bath**: global level of ligand k (`bath`). Both are implemented in the engine (`ctl` elements 6–8) and unit-tested only by construction (no experiment in this package uses them).
* **Tweezers**: instantaneous displacement of the cell nearest to an arena point (logged `extrude`). **Surgery**: remove / insert / replace at the cell nearest an arena point; cut along an arena line (cells on one side displaced by a vector); fusion of two bodies (World-level).
* **Smooth ramps**: raised-cosine on/off ramps for all continuous actuators; **separate forcing and release windows** (an action has `t_on`, `t_off`, `ramp`; the experiment continues after `t_off`); **dose accounting**: ∫|amplitude|·(number of lit cells)·dt per action in `Experiment.dose` (hidden tier).
* **SHAM**: `run(..., sham=True)` goes through the identical code path with all amplitudes zeroed and instantaneous events replaced by a logged no-op. The noise is a counter-based per-cell stream indexed by (key, absolute step, cell): an intervention consumes no random numbers, so matched twins and shams are bit-identical until the intervention acts (verified: 4e-15 before onset, sham = no-treatment to 6e-15; NOISE_AND_CRN.md, tests).

## Status
The renderer and actuators are ESTABLISHED as code and exercised by the identity-stress dataset (surgery, tweezers, fusion) and the viewer exemplars. The light-channel/actuator pipeline for a SWITCH experiment was exercised only through the S4 fate-bias runs (white-box, body-frame masks); the arena-mask light path was NOT used in any dataset because Gate S failed. The pipette and bath actuators are NOT DONE as experiments (implemented, not run).
