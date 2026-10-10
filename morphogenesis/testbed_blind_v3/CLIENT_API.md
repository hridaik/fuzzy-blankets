# Live dish experiments — client API (experimenter's guide)

You operate a virtual imaging rig. A dish holds one compact cluster of 24 cells. You can image it, project light on it, and let time pass. Everything you can learn comes from the images and tracked cells you request; nothing about how the cells work is described here or available through the interface. Lengths are arbitrary arena units (a cell is about 1 unit from its neighbours); time is in arbitrary time units (tu).

## Start
Start the rig server once (separate process; it writes a small `ready.json` with a port and a one-time token) and connect:
```python
from live_client import Dish
dish = Dish('ready.json')
```
The client library uses only the standard library and numpy.

## Calls
| call | arguments | returns |
|---|---|---|
| `reset(seed_pool='development', seed=None, sham_of=None)` | `seed_pool`: `'development'` or `'heldout'`; `seed`: dish seed from the pool (None = next unused); `sham_of`: episode id to repeat as a matched sham | `episode` (id), `seed_pool`, `seed`, `sham`, `time` (0), `budget` |
| `observe(episode, level)` | `level` in `O1`, `O2`, `O3a`, `O3b`, `O3c` (below) | the current frame (see below) |
| `act(episode, channel_label, arena_mask, amplitude, duration, ramp)` | channel `L1`…`L5`; mask in arena coordinates; the light starts now, lasts `duration` tu, with raised-cosine ramps of `ramp` tu at both ends (`2·ramp ≤ duration`) | `accepted`, `dose`, `cells_in_mask`, `time`, `budget` |
| `step(episode, dt)` | `dt` a positive multiple of 0.5 tu | `time`, `budget` |
| `end_episode(episode)` | | `ended`, `budget` |
| `freeze(hash)` | a string of at least 8 characters identifying your frozen analysis (e.g. a digest of your code and settings) | `frozen`, `heldout_unlocked` |
| `status()` | | budgets, levels, channel labels |
`arena_mask`: `{'type': 'disc', 'xy': [x, y], 'radius': r}`, `{'type': 'halfplane', 'n': [nx, ny], 'd': d}` (points with n·x > d) or `{'type': 'all'}`. Edges are soft (width about 0.3). The dish is placed at a random position and orientation in the arena for every episode; no axes are marked.

## Observation levels
* **O1 tracked cells**: `id` (permanent integer per cell; a newly introduced cell receives a never-used id), `xy` (position noise sd 0.02), `level_values` (7 columns, fixed order, 3 % multiplicative noise).
* **O2 unlabelled points**: `xy`, `level_values` (5 columns: the O1 columns 0, 1, 2, 3 and 6 in this order; rows in random order, no ids).
* **O3a / O3b images** (window ±12, 64 × 64 pixels, point-spread sd 0.5, peak SNR 20): three (O3a) or four (O3b) fluorescence channels; channels show the O1 columns 6, 2, 0 (O3a) and 6, 2, 0, 4 (O3b).
* **O3c cell-resolving images** (window ±10, 128 × 128 pixels, uint8; `scale` converts to intensities, value = uint8 / scale): channel 0 marks every cell with a sharp blob (sd 0.25, noise sd 0.05); channels 1–3 are the fluorescence fields of O3a at the same pixel grid.
Repeating `observe` at the same time with the same level returns the identical frame.

## Episodes, seeds and sham
* Every episode has a seed; episodes that use the same seed start from the same dish and share their random events, so an untreated run and a treated run of the same seed can be compared directly. `reset(sham_of=episode)` starts a matched sham: the same seed, but every `act` call is accepted and recorded with its dose set to zero (the procedure without any delivered light).
* **Seed pools.** The development pool is open. The held-out pool is locked until you call `freeze(hash)`; one freeze per server session; the hash is recorded.

## Budgets
Per episode: simulated time, total dose, number of actions. Over the session: number of episodes, simulated time, total dose. Dose of an action = amplitude × duration × number of cells inside the mask at the time of the call. Every response carries the current budget; exhausted budgets raise an error. A sham action costs no dose. Limits are set by the server operator (`status()` shows them).

## Errors
Calls raise `DishError` with a short message (unknown episode, unknown channel, invalid mask, `dt` not a multiple of 0.5, locked pool, budget exhausted).
