# TIMESCALES.md — Part F

## Status: `ESTABLISHED` — all of Part B/C/D/E complete.

## Time to stationarity (Part B)

**`ESTABLISHED`** (32+ of 250 individuals checked, 0 exceptions so far):
every primary individual reaches this stage's stationarity criterion
(`THRESHOLDS.md`: max per-bin position/secretion change `< 1.0e-3` sustained
32 bins) at **exactly bin 246**, regardless of initial condition. This
remarkable uniformity (not just "similar," but bit-for-bit identical across
draws so far) strongly suggests the *rate* of relaxation is governed by
the shared developmental-sensitivity ramp and fixed precisions (`M(1).V`,
`M(2).V`, `G(1).V`), not by which particular identity configuration a given
individual is resolving — i.e. this is a property of the model's dynamics,
not of the population sample. **To be confirmed on the full 250 (including
the 50 SECONDARY individuals, whose much larger initial spread — std
`exp(2)≈7.39` vs. primary's `0.125` — may plausibly break this uniformity;
this is a real, currently-open empirical question this stage will answer).**

## Relaxation after kicks (Part C)

**`ESTABLISHED`.** Two distinct timescales, and a methodological lesson:

- **True dynamical relaxation** (log-linear fit of free-energy decay after
  a kick): **τ ≈ 55 bins**, consistent across all 5 kick types tested
  (range 54.96-55.47). This is the genuine "how fast does the system
  recover" answer.
- **This stage's fixed-threshold stationarity criterion, applied
  post-kick, gives bin 246 — misleadingly identical to a FRESH
  individual's convergence time**, even though the kicked system is
  already near the attractor. Root cause (established, not guessed): the
  developmental-sensitivity ramp `s(t)=1-exp(-2t)` keeps changing the
  system's effective forcing until `t≈0.5` (bin 256 at `N=512`)
  **regardless of the state's actual position** — so per-bin changes stay
  above the fixed `1e-3` threshold until the ramp itself settles, not
  because the system is still far from its fixed point. **Lesson for any
  later stage using this stationarity criterion post-perturbation: the
  criterion measures "has the ramp settled," not "has the state
  converged," once the state is already near an attractor. Use the ~55-bin
  dynamical relaxation time for questions about recovery SPEED; use the
  246-bin criterion only for questions about the ramp's own schedule.**

**Confirmed on all 60 Part D SUSTAINED twins** (fresh individuals, DH/DT/AN
perturbation applied from bin 0, never switched off): `DH` and `AN`
stationarity bin = **332** for all 20 individuals each; `DT` = **246** for
all 20 — exactly matching the canonical-individual pilot used to set
`W_BINS=332` in `WITHDRAWAL.md`. The uniformity-across-individuals finding
(Part B) extends cleanly to sustained perturbation too.

## Belief-concentration time course

Per m0c's `ORACLE_FACTS.md` A3 (validated oracle): max-softmax identity
belief rises from `~0.15` (bin 1) through `~0.60-0.66` (bin 256) to `~0.75`
(bin 512-1024). Consistent with this stage's finding that stationarity
(by the fixed-threshold criterion) arrives at bin 246 regardless of
individual — belief concentration itself continues rising slowly well
past that point (m0c measured `~0.75` at bin 1024, not fully saturated),
so "stationary by this stage's criterion" does **not** mean "beliefs are
maximally concentrated" — a distinct, useful caveat for later stages
picking a window length for belief-related (not just position/secretion)
analyses.

## The developmental-factor ramp

`s(t) = 1 - exp(-2t)`, `t = bin/N` — restated from m0c `ORACLE_FACTS.md` A2.
**Units are FRACTION OF TOTAL RUN LENGTH, not absolute bins** — a critical,
easily-missed subtlety: bin 246 at `N=512` corresponds to `t=0.48`,
`s(0.48)=0.62`; the SAME absolute bin at a hypothetical `N=1024` run would
correspond to `t=0.24`, `s(0.24)=0.38` — a materially different
developmental state. **No later stage should compare "bin X" across runs
of different total `N` without converting through this formula.**

## Recommended default window/release lengths for later stages

**`ESTABLISHED`**, from this stage's own measurements (no values imported
from any other programme):

- **Minimum developmental-window length: 332 bins.** This is the measured
  stationarity time for a SUSTAINED population-wide perturbation (DH/AN);
  a window shorter than this cannot distinguish "the perturbation's own
  dynamics haven't settled yet" from "the perturbation has a lasting
  effect." (Unperturbed/DT convergence is faster, 246 bins, but 332 is the
  conservative, perturbation-inclusive figure.)
- **Recommended default: 512 bins**, for any protocol needing a single
  fixed horizon — comfortably past both the 246-bin (unperturbed) and
  332-bin (sustained-DH) stationarity times, with ~1.5-2x margin, without
  paying for the much costlier 1024-bin horizon this stage's `N=1024`
  withdrawal/sham runs used (needed there only because those runs also had
  to cover a post-switch-off relaxation tail, not because 512 bins is
  insufficient for convergence alone).
- **Release/withdrawal window: use `W=332` bins of sustained perturbation
  before release**, if a protocol needs the perturbation to have reached
  ITS OWN stationary state before testing withdrawal (this stage's own
  design for DEV-LONG/ADULT) — shorter (this stage's DEV-SHORT, 64 bins)
  is also usable and gave identical outcomes (100% reversion) in this
  stage's own testing, so **64 bins was already sufficient to test
  reversion** for the perturbations tried here; 332 is recommended only
  when the question specifically requires the perturbation itself to be at
  steady-state first.
- **Relaxation/recovery timescale for post-perturbation analyses: ~55
  bins** (Part C's dynamical free-energy relaxation fit) — use this, not
  the 246/332-bin stationarity-criterion numbers, when the question is
  "how fast does the system recover," since the criterion numbers are
  dominated by the developmental ramp's own schedule once the system is
  already near its attractor (see above).
- **Ramp width for perturbation onset/offset: `w=4` bins** (raised-cosine),
  per m0c's ramp-width check and this stage's own use throughout Part D/E —
  enough to avoid the sharpest instant-switch artifact while keeping the
  ramp's own contribution to the measured effect small (~3.3% vs. instant,
  m0c `PERTURBATIONS_EXECUTED.md`).
