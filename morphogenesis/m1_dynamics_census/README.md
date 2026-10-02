# Morphogenesis Programme — Stage M1: dynamics census

## STATUS: `COMPLETE`. All Tier-1 parts (A-H) executed and analysed. Total compute: 8.71 hours wall-clock (well under the 24h threshold).

## ⚠️ TOP-LINE WARNINGS

1. **All compute used the m0c Octave fallback engine exclusively**
   (unmodified SPM12 `spm_ADEM` under Octave 10.3.0), never the unfinished
   Python port, per the ground rules. Every rollout's manifest records the
   engine and a config hash.
2. **Headline finding #1 (Part B, n=250, `ESTABLISHED`)**: essentially
   **every individual converges to the same single shape**, regardless of
   a ~59x range in initial-condition scale, and that shape is **not** the
   literal target morphology (`d_target=0.2873` for all 250, exactly;
   robust to threshold ×0.5/×2). This model, as coded, has one dominant
   attractor, and it is a reproducible near-miss of its own target.
3. **Headline finding #2 (Part C, n=100, `ESTABLISHED`)**: converged
   bodies return to the same attractor after **every** tested kick,
   100/100, including a full hidden-state (belief) reset.
4. **Headline finding #3 (Part D+E, n=240, `ESTABLISHED`)**: **no tested
   Kuchling-2020 perturbation (DH/DT/AN), at any timing (including holding
   it on a converged body for its own full stationarity time before
   release), left any durable trace** — 180/180 withdrawal runs AND 60/60
   sham runs reverted completely (exact `d_pair=0.0000` to the unperturbed
   twin). The task's headline re-verification check (ramp-width re-test)
   was never triggered because no PERSISTED/NOVEL outcome occurred.
5. **A real orchestration bug was caught and fixed this session**
   (`COMPUTE_PLAN.md` addendum) — disclosed, not hidden; did not
   invalidate any result.
6. **Part A (rescue fix)**: a genuine implementation gap in m0c's rescue
   mechanism was fixed. Of the two published readings, only the
   figure-caption mechanism (R-caption), and only at a mild 1.5× factor,
   produces an actual rescue in this implementation; the text mechanism
   (eq. 50) does not.

## Status table

| Part | Status |
|---|---|
| A — Rescue fix | **`DONE`**. `RESCUE_FIX.md` |
| B — Census (250 individuals) | **`DONE`**. Thresholds frozen. `CENSUS.md` |
| C — Robustness (100 kicks) | **`DONE`**. `ROBUSTNESS.md` |
| D — Withdrawal (240 runs) | **`DONE`**. `WITHDRAWAL.md` |
| E — Sham (60 runs) | **`DONE`**. `SHAM.md` |
| F — Timescales | **`DONE`**. `TIMESCALES.md` |
| G — Observation ladder | **`DONE`**. 705 rollouts rendered, 1.8GB total (well under 50GB cap). `OBSERVATION_LADDER.md` |
| H — Viewer | **`DONE`**. 75 exemplars + `index.html`. |

## Headline answers to the three questions

**How many stable forms?** **`ESTABLISHED`: effectively ONE**, for both
initial-condition families tested (200 primary + 50 secondary, ~59x scale
range). Every individual converges to the identical shape up to role
permutation (`d_pair<1e-12` pairwise), classified `DEFECT` (not
`TARGET-ASSEMBLED`) at `d_target=0.2873` for all 250 — robust to
`tau_pos×0.5` and `×2`. `CENSUS.md`.

**Do converged bodies return after kicks?** **`ESTABLISHED`: YES, 100/100**
across 5 kick conditions (position displacement, secretion reset, full
belief reset, single-cell large displacement). Only the largest position
kick shows any role relabeling (5/20), never a different morphology.
`ROBUSTNESS.md`.

**Does any withdrawn perturbation leave a durable effect beyond sham?**
**`ESTABLISHED`: NO.** 180/180 withdrawal runs (DH/DT/AN × 3 timings × 20
individuals) AND 60/60 RMS-matched sham runs reverted completely and
identically (`d_pair=0.0000` to the unperturbed twin in every case). Both
the floor (sham) and the real perturbations sit at exactly 0% durable-effect
rate — there is no signal above floor because neither produced one.
`WITHDRAWAL.md`, `SHAM.md`.

## Versions / provenance

- Engine: m0c fallback (Octave 10.3.0 subprocess), same SPM12 commit as
  m0b/m0c (`03ac9473c`). Every rollout's manifest/hash confirms this.
- Python: `fuzzy-blankets` conda env (as in m0b/m0c).
- New source this stage: Kuchling et al. 2020 (already fetched in m0c,
  re-read for Part A's eq. 50 / Fig. 5C caption).
- Total compute: 8.71h wall-clock (`COMPUTE_PLAN.md`), 8-way parallelism
  throughout.

## Repository layout

```
m1_dynamics_census/
  README.md                 (this file)
  COMPUTE_PLAN.md              pilot times, projections, actual wall-clock, declared reductions
  THRESHOLDS.md                 stationarity criterion, tau_pos/tau_pair/tau_bel, frozen 2026-09-30
  RESCUE_FIX.md                  Part A: gap + fix + results
  CENSUS.md                       Part B: single-attractor finding, frequencies, identity events
  ROBUSTNESS.md                    Part C: 100% kick-return, relaxation timescales
  WITHDRAWAL.md                     Part D: 100% reversion, no headline effect
  SHAM.md                            Part E: floor comparison (also 100% reversion)
  TIMESCALES.md                      Part F: consolidated timing recommendation for later stages
  OBSERVATION_LADDER.md                Part G: renderer, storage, observer-model disclosure
  OPEN_QUESTIONS.md                     consolidated gaps
  oracle/                                 M1-specific Octave scripts (rescue fix, withdrawal on/off, sham field)
  code/                                    runners (census/rescue/kicks/withdrawal/sham) + analysis + observation_ladder.py + orchestrate.py
  tests/                                   analysis.py regression tests (bug caught + fixed this session)
  data/                                    per-part .mat + manifests + obsladder/ (rendered, unanalysed)

../viz/                                 extended with an optional image panel (O3a/O3b); index.html (75 exemplars)
```

## Reproducing this session's key results

```bash
conda activate fuzzy-blankets
cd morphogenesis/m1_dynamics_census
python3 code/analyze_census.py        # Part B: single-attractor finding
python3 code/analyze_kicks.py         # Part C: 100% return-after-kick
python3 code/analyze_withdrawal.py    # Part D+E: 100% reversion, no durable effect
python3 tests/test_analysis.py        # regression tests (5/5)
```

Full pipeline (long-running, ~8.7h): `python3 code/orchestrate.py` (waits
for `data/census/` to reach 250 individuals — run `code/run_census.py`
first or concurrently).

## Proposed repository status entry (paste manually if desired — not applied by this stage)

> **2026-09-30 — Morphogenesis programme, Stage M1 (dynamics census),
> complete.** New directory `morphogenesis/m1_dynamics_census/`. Fixed a
> real implementation gap in m0c's Kuchling-2020 single-cell rescue (it
> never paired the sqrt-kernel fix with the anomaly it was meant to
> rescue); implemented both the paper's text (eq. 50, found NOT to rescue
> in this implementation) and figure-caption (found to rescue, but only at
> a mild 1.5× sensitivity factor — stronger factors overcorrect) readings.
> Ran a full 250-individual census (200 primary + 50 secondary
> initial-condition draws, ~59x scale range) using the m0c Octave fallback
> engine exclusively. **Headline finding**: the model converges to a
> single dominant attractor shape (role-permutation-invariant distance ~0
> between any two individuals' end-states) that is a reproducible
> near-miss of its own target, not the target itself — robust to
> threshold choice. This attractor proved extremely robust: 100/100
> instantaneous kicks (position, secretion, full belief reset, large
> single-cell displacement) returned to it, and 180/180 withdrawn
> Kuchling-2020 perturbations (double-head/tail/anomalous-cell, three
> developmental timings including holding the perturbation on a mature
> body) reverted completely and identically to 60/60 magnitude-matched
> sham controls — no durable effect of any tested perturbation was found.
> Built a deterministic, versioned observation-ladder renderer (unlabelled
> point clouds, multi-channel blob images with declared noise, ligand
> maps) for a future blind stage, generated but not analysed, for all 705
> rollouts (1.8GB, well under the 50GB cap). Extended the shared viewer
> with an optional image panel; built 75 exemplars per the declared
> selection rule. Total compute: 8.71 hours wall-clock at 8-way
> parallelism (one real orchestration bug caught and fixed mid-run,
> disclosed, no result invalidated). **Next step for this programme**: the
> single-attractor / universal-reversion findings are strong enough to
> warrant checking whether they are specific to this template/perturbation
> family or a general property of the model — and whether a blind analysis
> of the now-generated observation-ladder data (O2-O4) can detect the
> single attractor without hidden-tier access, as a sanity check on the
> observation process itself before any representation-learning work
> begins.
