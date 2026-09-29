# Morphogenesis Programme — Stage M0: simulator reconstruction, reproduction, and descriptive characterization

## 🛑 DEPRECATED — DO NOT IMPORT DOWNSTREAM

This stage's Python solver (`code/solver.py`) is a **reduced gradient-flow
approximation, not a port of SPM's `spm_ADEM`**. It is **numerically
non-equivalent** to the published simulator: under the real reference
(`spm_ADEM` under Octave, verified in `morphogenesis/m0b_reference_port/`),
cells clearly differentiate by ~bin 8 (max-softmax identity concentration
already 0.4-0.7 across cells) and free energy behaves as published; under
this stage's reduced solver, **no cell's identity belief ever exceeds 0.9
softmax even after 512 bins** — a qualitatively wrong result. Every
characterization number in this stage's `CHARACTERIZATION.md` describes
*this broken solver's own behaviour*, not the published model's.
**Superseded by `morphogenesis/m0b_reference_port/`. Nothing in this
directory should be imported or relied on by any later stage.**

## ⚠️ TOP-LINE WARNINGS (read first)

1. **No MATLAB or GNU Octave was run in this stage.** Neither is installed in
   this environment. Octave 9/10 is installable via conda-forge without root
   privileges (verified available); the user was asked explicitly and chose
   **not** to install it for this stage. **Consequently: Task B (reference
   execution / golden traces) is NOT DONE, Task C's equivalence testing is
   NOT DONE (no ground truth to compare against), and every quantitative
   result in `CHARACTERIZATION.md` is an "unvalidated re-derivation"** — a
   description of this session's own Python reconstruction, not a validated
   port of the published simulator. See `REPRODUCTION_REPORT.md` and
   `EQUIVALENCE_REPORT.md`.
2. **The global `t` question is resolved and is NOT the zero-signalling
   failure mode the task ground rules flagged as a risk.** `t` IS assigned
   during `spm_ADEM` integration (`spm_ADEM.m` line 444: `t = iY/nY`), so the
   extracellular/field-sensed signal (`g.c`) is **not** multiplied by zero
   throughout — sensitivity ramps from near-0 to `1-exp(-2)≈0.865` within a
   single `spm_ADEM` call. See `MODEL_SPEC.md` §3.
3. **Only one of the seven named perturbations (Pio-Lopez ×4, Friston-2015
   ×4, minus the one overlap) has source-code grounding** in the repositories
   fetched this session: Pio-Lopez's "high identity expectation in k cells."
   The other three Pio-Lopez variants and all four Friston-2015 perturbations
   were **not found in any fetched source** and are **not implemented** —
   see `DISCREPANCIES.md` §6-7. This is a large, disclosed reduction in scope
   relative to the original task prompt's expectations.
4. **Two apparent code/paper discrepancies were directly confirmed against
   the 2015 paper's PDF** (not just the task prompt's summary): the model's
   sensory precision is log-precision **2** in the paper vs. `exp(3)` (i.e.
   log-precision **3**) in all fetched code; the developmental-sensitivity
   ramp is **linear** in the paper vs. `1-exp(-2t)` (exponential-saturating)
   in all fetched code. See `DISCREPANCIES.md` §2-3.
   One apparent discrepancy in the task prompt's own summary was found to be
   an error and closed: the prompt said the 2015 paper's initial-expectation
   precision was "log precision -4"; the paper actually says **-2**, which
   matches the code's `M(2).V = exp(-2)` exactly. See `DISCREPANCIES.md` §4.

## Status table

| Task | Status |
|---|---|
| A — Source audit | **Done, with disclosed gaps** (see MODEL_SPEC.md, DISCREPANCIES.md; a few sub-items flagged NOT DONE, listed in OPEN_QUESTIONS.md) |
| B — Reference execution / golden traces | **NOT DONE** (no MATLAB/Octave available; REPRODUCTION_REPORT.md) |
| C — Independent Python implementation | **Done, structurally**; equivalence testing NOT DONE (no ground truth) — EQUIVALENCE_REPORT.md |
| D — Tiered data schema | **Done and tested** — DATA_SCHEMA.md |
| E — Descriptive characterization | **Done on the Python port only, with reduced sample counts**, labeled unvalidated re-derivation throughout — CHARACTERIZATION.md |

## Versions / provenance (exact, per ground rules)

- Python: 3.12.14, conda env `fuzzy-blankets`
- numpy 2.5.3, scipy 1.18.0
- No MATLAB. No Octave (not installed this stage).
- SPM12 (GitHub mirror `spm/spm12`, branch `main`): commit
  `03ac9473cad402407b6472228377c0167fdc54b8` (2024-02-05), used as the
  primary reference (justification in DISCREPANCIES.md §1).
- SPM25 (`spm/spm`, branch `25.01_release`): commit
  `76167510b7190027995325d609a2365d9a7b6bc2` (2025-01-23), fetched and diffed
  against SPM12 for `DEM_morphogenesis.m`/`spm_ADEM.m` only (DISCREPANCIES.md §1).
- `LPioL/active_inference_morphopsy`: commit
  `bd378a4123485f18e588763d163c9f0315ac2671` (2022-10-14).
- Friston, Levin, Sengupta & Pezzulo (2015), *J. R. Soc. Interface* 12:20141383
  — PDF fetched to `sources/papers/friston2015.pdf`, read directly (not just
  summarized) for the precision/sensitivity claims in DISCREPANCIES.md §2-4.
- Pio-Lopez, Kuchling, Tung, Pezzulo & Levin (2022) — **not independently
  re-fetched/re-read as a PDF in this pass**; only the task prompt's summary
  of it was used (OPEN_QUESTIONS.md item 6).
- Random seeds: all seeded explicitly via `numpy.random.default_rng(<seed>)`
  in `code/`; specific seeds are recorded per-run in each run's
  `hidden/config.json` (DATA_SCHEMA.md).

## Repository layout

```
morphogenesis/m0_reconstruction/
  README.md                 (this file)
  MODEL_SPEC.md              Task A: source-grounded specification
  DISCREPANCIES.md            Task A: deviations, code/paper mismatches
  REPRODUCTION_REPORT.md       Task B status (NOT DONE, with rationale)
  EQUIVALENCE_REPORT.md         Task C status (NOT DONE, with rationale)
  DATA_SCHEMA.md                  Task D: tiered schema, tested
  CHARACTERIZATION.md              Task E: E1-E6 results (Python-only)
  OPEN_QUESTIONS.md                 consolidated NOT DONE / follow-up list
  sources/                           fetched SPM12/SPM25/morphopsy/papers
  code/                                Python implementation (see below)
  tests/test_basic.py                   sanity tests (8/8 passing)
  data/golden_traces/                    Python-port run output (tiered)
  data/characterization_results.json      raw E1-E6 numbers
```

`code/`: `template.py` (target decoding), `field.py` (field law),
`generative.py` (Mg/Gg, softmax, sensitivity ramp), `solver.py` (reduced
D-step integrator — see DISCREPANCIES.md §9 for exactly how it differs from
`spm_ADEM.m`), `interventions.py` (the one implemented perturbation),
`synthetic_template.py` (E6 scaling templates), `storage.py` (tiered
save/load with audit-gated hidden tier), `run.py` (CLI driver),
`characterization.py` (E1-E6 script).

## Reproducing this session's results

```bash
conda activate fuzzy-blankets
cd morphogenesis/m0_reconstruction
python tests/test_basic.py                 # 8/8 sanity tests
cd code
python run.py vanilla8 --seed 0             # writes data/golden_traces/vanilla8_seed0_n32/
python characterization.py                   # writes data/characterization_results.json, ~30s
```

## Proposed repository status entry (for a top-level status file — NOT applied by this stage; paste manually if desired)

> **2026-09-25 — Morphogenesis programme, Stage M0 (simulator reconstruction)
> opened and closed for this pass.** New directory `morphogenesis/
> m0_reconstruction/`. Source-audited the SPM12/SPM25 `DEM_morphogenesis`
> active-inference morphogenesis model and the Pio-Lopez et al. 2022 code
> release; built an independent, disclosed-simplification Python
> reconstruction; ran descriptive-only characterization (E1-E6) on the
> Python port. **No MATLAB/Octave reference run was performed** (none
> installed; declined for this stage) — all Task B/C validation against the
> published simulator remains open. No hypothesis testing, controller
> design, or identity/boundary metric work was done, per this stage's scope.
> Next step for this programme: install Octave (conda-forge, no root
> needed) and attempt reference execution before any M1 work that depends on
> quantitative fidelity.
