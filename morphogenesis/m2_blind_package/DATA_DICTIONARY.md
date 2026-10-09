# DATA_DICTIONARY.md — what was measured and how

This package is a set of recordings from small groups of mobile cells that secrete diffusible chemicals into a shared arena. Each recording follows every cell in a group, bin by bin, and notes what an experimenter did to the group and when. Everything below is what a lab would know from the bench record; nothing is said or implied about how the cells decide what to do.

## Package layout
| Path | Content |
|---|---|
| `segments/R######.npz` | one recording segment (arrays below) — the unit of data |
| `manifest.jsonl` | one JSON record per segment: who, when, what was done, links between segments, split labels |
| `splits.json` | development / held-out lists (individuals, conditions, region centres) |
| `ladder/R######.npz`, `ladder_index.json` | image-style renderings of a declared subset of segments (section "Renderings") |
| `LEAK_CHECK.md` | result of the automated content check of this package |

## What is observed (every segment)
* `position` — array `(n_bins, n_cells, 2)`, float32. Cell centre coordinates (x, y) in **arena units** (one unit is of the order of the typical spacing between neighbouring cells; the arena has no walls in the recorded range). One sample per **bin** (the sampling interval of the experiment; time is counted in bins).
* `levels` — array `(n_bins, n_cells, 4)`, float32. The four chemical levels each cell is secreting at that bin, **raw, dimensionless, in the order 1–4**; they are not labelled by what they do. They are unbounded: untreated groups sit at values of order 1, strong treatments produce values far outside that range (positive or negative).
* Cells are numbered `0 … n_cells−1` within a segment; the numbering is fixed for the whole recording and carries **no meaning across individuals**. Groups have 8 cells unless `n_cells` says 16.
* Chemical field maps and images are not recorded directly; they are derived renderings (below).
* There is no noise added to the recordings except where `noise_label` ≠ `NL0` (below). Float32 storage is the only rounding.

## Segments, time and continuation (`manifest.jsonl`)
| Field | Meaning |
|---|---|
| `segment_id` | opaque id `R######` (order is random) |
| `individual_id` | `I###`: one independently prepared group. Different individuals start from different arrangements. |
| `protocol` | `"v2"` for every record in this package (one measurement protocol; the field is present so that records from any other protocol cannot be mixed in) |
| `n_cells`, `n_bins` | group size; number of bins in the segment |
| `bin_start` | absolute bin count since the preparation was started at the first bin of this segment (a segment with `bin_start` = 320 begins 320 bins after the start of the preparation) |
| `parent_segment` | `null` for a segment that starts a new preparation; otherwise the segment whose last bin is the exact state this one continues from (so segments chain into a longer recording; the first sample of a child follows the last sample of its parent) |
| `matched_control` | an untreated segment that continues from the same parent for the same number of bins (same preparation, no treatment) — present where one was recorded; `null` otherwise |
| `rearing_label` | `RC1` or `RC2`: two schedules for the preparation phase (RC2 is a slower one); identical thereafter |
| `noise_label` | `NL0` = no added fluctuation. `NL1`, `NL2`, `NL3` = three different non-zero levels of random fluctuation acting on the cells during the recording; **the labels are not ordered by magnitude** |
| `condition_id` | `C###`: one experimental condition (a kind of treatment with a given channel / family, amplitude and sign, applied to one cell / a region / all cells); untreated segments with the same noise label and group size share one condition |
| `treatments` | list of what was done within this segment (below); empty for untreated |
| `split`, `holdout_*` | development / held-out membership (below) |

## Treatments (`treatments` list)
Every treatment records **when** (`onset_bin`, absolute bins), **to what** (`applied_to`) and **how much**.
* `applied_to`: `{"cells": [i, …]}` — cell numbers at the time of treatment; `{"all": true}` — every cell; `{"region": {"centre": [x, y], "radius": r, "cells_at_actuation": [i, …]}}` — a disc of radius `r` arena units about `centre`, with the cells inside it at the time of treatment.
* `kind: "pulse"` — a brief stimulus on one of ten stimulus **channels** `CH1 … CH10`. Channel labels are arbitrary and consistent (the same label is the same physical knob in every segment); their numbering carries no meaning. Time course: raised cosine of width `width_bins` bins starting at `onset_bin`, peak `amplitude` (signed; units of the channel, not comparable across channels).
* `kind: "sustained"` or `"window"` — a treatment of kind `family` ∈ `TX1 … TX5` that is switched on over `ramp_bins` bins from `onset_bin` and either stays on until the end of the recording (`sustained`, `off_bin` null) or is switched off over `ramp_bins` bins from `off_bin` (`window`). `level` (dimensionless) or `amplitude` gives its strength. `TX1` and `TX2` are two opposite-signed versions of one manipulation; the families are otherwise unrelated and carry no further description.
* `kind: "displacement"` — at `onset_bin` every cell is moved instantaneously by the listed `(dx, dy)` (arena units, one pair per cell, in cell-number order), and the recording continues from the displaced state.
* `kind: "sudden"`, `family: "TX6"` — an instantaneous manipulation at `onset_bin` whose size is not recorded (listed with its timing only).
* A segment's `treatments` are applied inside that segment only; a child segment of a treated parent has its own (possibly empty) list.

## Splits (`splits.json`, `manifest.jsonl`)
* `holdout_individuals`: individuals withheld for evaluation (`holdout_individual` = true on every segment of those individuals).
* `holdout_conditions`: whole conditions withheld (`holdout_condition`); untreated conditions are never withheld.
* `holdout_region_centres`: region centres withheld (`holdout_region` = true on segments treated at those centres).
* `split`: `dev` if none of the above applies; otherwise `holdout_` followed by the reason(s) joined by `+`.
A segment is withheld if its own individual, condition or region is withheld; the untreated parent segments of a withheld condition remain in the development set.

## Renderings (`ladder/`, `ladder_index.json`)
A declared subset of 8-cell segments (listed in `ladder_index.json`) is also provided as images and maps, generated from the recordings by a fixed, versioned procedure (`renderer` in the index). Rendering choices are part of the observation procedure, not facts about the cells: field of view `[−4, 4]²` arena units; 96 × 96 pixels; each cell is a Gaussian blob of width 2.5 pixels; images are divided by their own maximum per frame (absolute amplitude is not recoverable); additive noise at 10 dB signal-to-noise plus a counting-style term, seeded from the segment id and frame. Frames: every bin for the first 8 bins after the treatment onset (for an untreated segment, the first 8 bins), every 8th bin afterwards; `frames` gives the bin index (within the segment) of each frame. Arrays, all with leading axis = frame:
* `cloud_position` `(F, 2, n_cells)` float16 and `cloud_levels` `(F, 4, n_cells)` float16 — the cells of each frame in an **independently random order for every frame** (no cell can be followed between frames by array index).
* `image_a` `(F, 96, 96, 4)` uint8 — one image channel per chemical level (levels 1–4). `image_b` `(F, 96, 96, 2)` uint8 — two of the levels (2 and 3), as two reporter channels.
* `map` `(F, 4, 32, 32)` float16 — the concentration of each of the four chemicals on a 32 × 32 grid over the same field of view, computed from the recorded cells with the experiment's diffusion law; no cell coordinates are stored in the maps.
