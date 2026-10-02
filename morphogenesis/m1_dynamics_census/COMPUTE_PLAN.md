# COMPUTE_PLAN.md

Written **before** launching any full-scale batch, per the ground rules.
All times below are pilot-measured (not guessed), on this machine (8 cores,
Octave 10.3.0, the m0c fallback engine, `n=8` cells unless noted).

## Pilot measurements

| Pilot | n | N (bins) | elapsed | Notes |
|---|---|---|---|---|
| 8 independent individuals (seeds 0-7), 8-way parallel | 8 | 512 | mean **234.1s**, max 234.7s | `code/pilot_stationarity.py` |
| Stationarity (thr=1e-3, window=32, restated in `THRESHOLDS.md`) | — | — | **bin 246 for all 8** | Smooth, monotonic decay confirmed (not an artifact — checked raw per-bin traces) |
| Part A quick test (3 configs, N=32) | 8 | 32 | ~15s each | AN / R-text / R-caption all run cleanly |
| m0c reference: n=16, N=512 | 16 | 512 | 728.4s | For any n=16 work (none planned this stage) |

**Key finding informing this whole plan**: stationarity (by the declared
criterion) arrives at essentially the **same bin (246) regardless of which
individual** — the convergence *rate* appears to be governed by the shared
developmental-sensitivity ramp and fixed precisions, not by which particular
identity configuration is being resolved. This means `N=512` (not 1024 or
2048) is expected to comfortably cover the overwhelming majority of Part B
individuals, with ~2x margin. **Design decision**: run every Part B/C/D/E
individual at a **fixed N=512** first; only individuals that are NOT
stationary by bin 512 are re-run once at `N=2048` (cascading fallback, not
always paying for 2048). This is the "early stopping to save compute" this
stage's ground rules ask for, implemented as a two-tier fixed-horizon
cascade rather than an in-loop break (which would require a further,
riskier patch to `spm_ADEM.m`'s D-step loop — judged not worth the
engineering risk given the pilot margin already observed).

## Per-part projections (8-way parallelism, 234s/run baseline at N=512)

| Part | Runs | Basis | Projected wall-clock |
|---|---|---|---|
| A (rescue fix + sweep) | ~58 (11 individuals × 5 conditions + factor sweep) | N=512 | **~0.5h** |
| B (census) | 250 (200 primary + 50 secondary) | N=512, cascade to 2048 for stragglers | **~2.0h** (+ small cascade tail) |
| C (robustness) | 20 individuals × 5 kick conditions = 100 | N=512 from converged state | **~0.8h** |
| D (withdrawal) | 20 individuals × 3 perturbations × 3 timings = 180, + 60 SUSTAINED twins = 240 | N≈512-700 (perturbed dynamics not expected to be dramatically slower, per m0c's non-chaotic finding) | **~2.0-2.7h** |
| E (sham) | 20 individuals × 3 timings = 60 (DH-magnitude-matched sham only, not all 3 perturbations — see below) | N≈512-700 | **~0.7h** |
| G (observation-ladder rendering) | post-hoc Python rendering of stored rollouts, CPU-bound, not Octave | — | **~1-2h estimated, storage-capped (see OBSERVATION_LADDER.md)** |
| H (viewer) | HTML generation, cheap | — | **<0.2h** |

**Total projected: ~8-10 hours wall-clock at full 8-way parallelism** —
**under the 24-hour threshold**, so no Tier-1 reduction is triggered by
the compute-time rule. (A separate, disclosed reduction — engineering-turn
budget, not compute time — is recorded per part as it is reached, matching
this program's practice in M0c.)

## Declared scope decision for Part E (sham)

The task specifies sham controls for "the same 20 individuals" matched
against DH's RMS distortion. Building 3 independently-matched sham fields
(one per perturbation: DH, DT, AN) would triple Part E's cost for a control
whose main purpose (per the task itself) is to bound the DH/DT headline
finding. **Declared reduction**: Part E sham runs are matched to the **DH**
condition only (RMS-matched to `SUSTAINED-DH`'s visited positions, as the
task's own magnitude-matching text specifies), and used as the floor for
**all** DH/DT/AN withdrawal outcomes, not re-matched per perturbation. This
is disclosed here, not silent, and reduces Part E from a potential 180 runs
to 60.

## Addendum: a real orchestration bug, disclosed

`code/orchestrate.py`'s `wait_for_census()` originally counted **all** `.mat`
files in `data/census/`, including leftover `*_vinit.mat` temp files that
m0c's `fallback_engine.run()` (imported, unmodified) writes for any call
using its `initial_state` override (used for every SECONDARY individual)
and never cleans up. This inflated the apparent count past 250 while ~18
secondary individuals were still actually running, so **Part A (rescue)
started ~17 minutes early, concurrently with the tail of Part B (census)**,
causing real CPU contention (individual run times measured at ~465-469s
instead of the expected ~232-238s, consistent with ~2x oversubscription on
8 cores). **This did not corrupt or invalidate any result** — both batches
continued running correctly, just slower — and total combined wall-clock
for "both batches complete" is not materially worse than running them
sequentially would have been (the same total CPU-seconds get done either
way, modulo scheduling overhead). **Fixed** in `orchestrate.py` for any
future run of this pipeline (now counts only `primary_`/`secondary_`-prefixed,
non-`vinit` files). Disclosed here rather than silently patched and
forgotten.

## Final actual wall-clock (all Tier-1 parts complete)

| Step | Wall-clock |
|---|---|
| Part B census (250 individuals) | 8250.6s (2.29h) |
| Part A rescue (55+4 runs) | 2456.6s (0.68h) |
| Part C kicks (100 runs) | 3056.2s (0.85h) |
| Part D SUSTAINED twins (60 runs) | 1900.7s (0.53h) |
| Part D withdrawal (180 runs) | 11326.5s (3.15h) |
| Part E sham (60 runs) | 4361.0s (1.21h) |
| **Total** | **31351.6s = 8.71 hours** |

**Under the projected ~8-10h estimate and well under the 24h threshold** —
no Tier-1 reduction was ever triggered by the compute-time rule. The one
real hiccup (the `_vinit.mat` counting bug causing ~17 minutes of
Part A/B contention, `COMPUTE_PLAN.md` addendum above) added negligible
total time.

## What would change this plan

If Part B's actual census (not just the 8-individual pilot) turns up a
non-trivial fraction of NONCONVERGED individuals at N=512, the cascade to
N=2048 will add real time (each cascade run ≈4x cost, i.e. ~936s). At the
pilot's observed 0/8 non-convergence rate, this is not expected to be
material; if it turns out otherwise, this document will be amended and the
change noted in `OPEN_QUESTIONS.md`.
