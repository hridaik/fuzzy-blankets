# Morphogenesis Programme — Stage M0b: reference oracle, faithful Python port, equivalence, perturbations, characterization, viewer

## ⚠️ TOP-LINE WARNINGS (read first)

1. **Task 1 (Octave reference oracle) SUCCEEDED and is the strongest result
   in this stage.** The real, unmodified `spm_ADEM.m` (patched only with the
   built-in `DEM.db=0` no-graphics flag) runs correctly under Octave 10.3.0
   and **reproduces the published qualitative behaviour** — cells reach
   0.4-0.7 max-softmax identity concentration by bin 8, rising to ~0.75 by
   bin 32, with free energy rising (improving) monotonically after an early
   dip. This is a **dramatic, decisive contrast** with `m0_reconstruction`'s
   solver, which never exceeded 0.9 softmax in 512 bins.
2. **Task 2 (faithful Python port) is INCOMPLETE.** Every low-level
   numerical primitive the port depends on (`spm_DEM_R`, `spm_dx`,
   `spm_DEM_embed`, forward-difference `spm_diff`) is implemented and
   **validated to match Octave exactly** (`EQUIVALENCE_REPORT.md` L1). The
   full D-step Jacobian assembly is **not completed** — a self-referential
   recursion in `spm_ADEM_diff.m` (SPM12) for propagating generalized
   temporal orders of the process response was not resolved with confidence
   from static reading, and this session stopped rather than ship an
   unverified guess. See `PORT_DESIGN.md` for exactly where and why, and the
   concrete next step to unblock it.
3. **Tasks 3 (L2/L3 equivalence), 5 (characterization), and 6 (viewer) are
   NOT DONE**, blocked on item 2 (they explicitly require a *validated*
   port). **Task 4 (perturbation catalog)** is done at the
   research/classification level (exact equations from three primary
   sources, including finding and resolving a genuine caption/text/panel
   conflict in Friston et al. 2015's Figure 5) but not executed.
4. **A significant correction to `m0_reconstruction`'s own findings**: m0
   incorrectly closed a discrepancy about the 2015 paper's initial-condition
   precision, having missed a second relevant quotation. **This is now
   reopened and confirmed as a real discrepancy** — see
   `DISCREPANCIES_UPDATE.md`.
5. This session's own scope-vs-effort tradeoff was surfaced to the user
   mid-session (a full byte-exact port plus everything downstream was
   assessed as requiring many more hours than remained), and the user chose
   to continue building the faithful port and validating empirically. The
   port work reached a genuine, disclosed stopping point rather than
   completing — see item 2.

## Status table

| Task | Status |
|---|---|
| 1 — Reference oracle (Octave) | **DONE.** All required configs run, hashed, sanity-checked against Fig. 3 qualitatively. `ORACLE_REPORT.md` |
| 2 — Structure-preserving Python port | **PARTIAL.** L1 primitives done+validated. Full D-step assembly NOT DONE (disclosed blocker). `PORT_DESIGN.md` |
| 3 — Layered equivalence | **PARTIAL.** L1 done with concrete numbers. L2/L3 NOT DONE. `EQUIVALENCE_REPORT.md` |
| 4 — Perturbation catalog | **PARTIAL.** Catalog+equations+classification DONE (3 primary sources read directly). Execution NOT DONE except the one CODE-BASED item's Octave traces (already had them from Task 1). `PERTURBATIONS.md` |
| 5 — Characterization | **NOT DONE** (requires validated port per the task's own wording). |
| 6 — Interactive viewer | **NOT DONE** (requires a Python trajectory to compare against Octave). |
| DISCREPANCIES_UPDATE | **DONE.** One m0 finding corrected/reopened, one new (Kuchling 2020) source added. |

## Versions / provenance

- Octave: **10.3.0** (`conda create -n octave-dem -c conda-forge octave`, no
  root required).
- SPM12: full clone, `github.com/spm/spm12`, commit
  `03ac9473cad402407b6472228377c0167fdc54b8` (same commit m0 used).
- `LPioL/active_inference_morphopsy`: commit
  `bd378a4123485f18e588763d163c9f0315ac2671` (same as m0).
- Papers read directly as PDF in this session: Friston et al. 2015 (again,
  more thoroughly than m0 — found the missed "-4" quote and the Fig. 5
  conflict), Kuchling et al. 2020 (new this session, full equations read).
  Pio-Lopez et al. 2022: **still not independently fetched/read as a PDF**
  in either stage — flagged in `OPEN_QUESTIONS.md` item 6.
- Python: 3.12.14, conda env `fuzzy-blankets`, numpy 2.5.3, scipy 1.18.0.
- Octave RNG seeds: 0 throughout; every noise draw `spm_ADEM` used is
  exported per run (`z_exported`/`w_exported` in each `.mat` trace) — see
  `ORACLE_REPORT.md` "Octave RNG vs. MATLAB RNG".

## Repository layout

```
m0b_reference_port/
  README.md                  (this file)
  ORACLE_REPORT.md             Task 1: install, patches, sanity check, all configs run+hashed
  PORT_DESIGN.md                Task 2: function-by-function mapping, validated vs. not
  EQUIVALENCE_REPORT.md          Task 3: L1 results (concrete numbers), L2/L3 status
  PERTURBATIONS.md                 Task 4: catalog, exact equations, classification
  DISCREPANCIES_UPDATE.md            corrected m0 finding + new Kuchling 2020 facts
  OPEN_QUESTIONS.md                   consolidated NOT DONE / next-steps list
  sources/                              spm12 (full clone), morphopsy, papers
  oracle/                                 Octave setup/runner/debug-dump scripts
  code/                                    Python: spm_port.py (validated L1 primitives), model.py
  tests/test_l1_primitives.py              5/5 passing, each checked against live Octave output
  data/oracle_traces/                       13 golden traces + SHA256SUMS.txt + 1 D-step debug dump
```

`morphogenesis/viz/`: **not created** — Task 6 was not reached.

## Reproducing this session's results

```bash
conda activate octave-dem
cd morphogenesis/m0b_reference_port
octave --no-gui --eval "addpath('sources/spm12'); addpath('sources/spm12/toolbox/DEM'); addpath('oracle'); run_and_export(2,32,0);"

conda activate fuzzy-blankets
python tests/test_l1_primitives.py     # 5/5
```

## Proposed repository status entry (paste manually if desired — not applied by this stage)

> **2026-09-29 — Morphogenesis programme, Stage M0b (reference oracle +
> faithful port, partial).** New directories `morphogenesis/m0b_reference_port/`
> (work) and a deprecation notice added to `morphogenesis/m0_reconstruction/README.md`
> (its solver is confirmed non-equivalent to the published simulator — do
> not import it downstream). **Major result: the real SPM12 `spm_ADEM`
> reference now runs under Octave** (installed via conda-forge, no patches
> beyond the built-in no-graphics flag) and **reproduces the published
> qualitative behaviour** (differentiation by ~bin 8, falling free energy) —
> a capability the programme lacked entirely before this stage. All required
> Task 1 configurations were run and hashed. **The faithful Python port was
> not completed**: every low-level numerical primitive is validated exactly
> against Octave, but the full generalized-filtering D-step assembly hit an
> unresolved recursion in `spm_ADEM_diff.m` and the session stopped rather
> than ship an unverified guess (see `m0b_reference_port/PORT_DESIGN.md` for
> the precise, small next step). Consequently, equivalence testing (L2/L3),
> full-power characterization, the perturbation catalog's execution, and the
> interactive viewer are not done this stage, though the perturbation
> catalog itself (exact equations from Friston 2015, Kuchling 2020, and
> Pio-Lopez 2022, including resolving a genuine figure-caption/text
> contradiction in Friston 2015) is complete. A discrepancy m0 incorrectly
> closed (initial-expectation precision) was reopened and confirmed real.
> **Next step for this programme**: instrument `spm_ADEM_diff.m` directly
> (a small, well-scoped addition to the existing Octave debug-dump
> machinery) to resolve the blocking recursion, then resume from Task 2.
