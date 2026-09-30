# Morphogenesis Programme — Stage M0c: oracle-driven port completion, oracle-only deliverables, interactive viewer, fallback engine

## ⚠️ TOP-LINE WARNINGS (read first)

1. **The `u.v{i}` recursion that blocked m0b's port is now FULLY RESOLVED.**
   Empirically confirmed (dump evidence, `PORT_DESIGN_UPDATE.md`): `pu.v{i}`
   persists across bins (predict via `spm_ADEM_diff`, correct via the later
   `spm_dx` joint update), and — decisively — `dg.dv ≡ 0` identically for
   this model, so the recursion has zero effective self-dependence. This is
   real, dump-verified progress.
2. **Despite that, the Python port still does NOT achieve L2 (single-step)
   equivalence.** A from-scratch D-step (`code/dstep.py`) built on the now-
   resolved semantics uses a **block-decoupled** approximation to the joint
   `dFduu` local-linearization solve, which understates the actual update by
   2-7x and gets at least one sign wrong (tested directly against Octave's
   dumped bin-1 update). Per the task's own B5 timebox, Part B **stops
   here**, with the mismatch precisely localized (statement, bin, variable,
   magnitude — `EQUIVALENCE_REPORT.md`), and **Parts C and E proceed on the
   Octave oracle via the Part D fallback engine, not this incomplete port.**
3. **For any later stage: use the Octave oracle (via `code/fallback_engine.py`)
   as the engine, not the Python port.** The Python port
   (`code/dstep.py`) is a documented, partially-validated *research
   artifact* (L1 exact; L2 does not match) — do not treat its trajectories
   as ground truth.
4. **L1 (function-level) is fully validated**, extending m0b: `Mg`/`Gg`
   match live Octave to `~1e-15/1e-16` relative deviation (A5, 20 random
   inputs); the sensory/prior error vector `E` matches Octave's dumped bin-1
   value to `3.3e-16` (machine precision).
5. **A4's chaos-baseline finding**: the Octave reference is **not**
   sensitive-dependent/chaotic over a 32-bin horizon at `1e-6`-scale initial
   perturbations — deviations peak early (~bin 10-11) and then **decay**,
   not grow. Any future L3 port-vs-oracle deviation that grows and does not
   decay should be attributed to the port.
6. **Part C highlights**: population-wide Kuchling distortions (double
   head/tail) persist and worsen under sustained application (512 bins),
   while a single anomalous cell's distortion washes out almost completely
   by bin 512 — the collective "routes around" one bad actor but cannot
   route around a distortion shared by everyone. Ramp width measurably
   affects outcomes (up to +8% distance over instant-vs-8-bin-ramp onset) —
   not a free implementation choice. The `kuchling_rescue` runs have a
   disclosed implementation gap (they don't pair with an anomaly to
   rescue) — do not read them as a validated rescue result.

## Status table

| Part | Status |
|---|---|
| A — Oracle facts | **DONE.** A1-A6 all `ESTABLISHED`. `ORACLE_FACTS.md` |
| B — Port completion | **PARTIAL, B5 timebox invoked.** Recursion resolved; L2 joint solve not completed. `PORT_DESIGN_UPDATE.md`, `EQUIVALENCE_REPORT.md` |
| C — Perturbations on oracle | **DONE for Kuchling+Friston (35 runs, both horizons, ramp-width check); Pio-Lopez precision/rescue sweeps designed but not run (time budget).** One implementation gap disclosed (`kuchling_rescue` doesn't pair with an anomaly). `PERTURBATIONS_EXECUTED.md` |
| D — Fallback engine | **DONE.** Built, correctness-checked (bit-identical to plain oracle on the no-op path), pilot-timed (n=8: 254.5s; n=16: 728.4s, both N=512, measured not estimated). `FALLBACK_ENGINE.md` |
| E — Interactive viewer | **DONE for Octave-only content** (A3, A4, all 33 Part-C perturbation traces, index.html with declared exemplar rule). Octave-vs-Python pairs not built (no Python trajectory to pair, per Part B); live-browser rendering not verified (no browser in this environment). `viz/VIEWER.md` |

## Versions / provenance

- Octave: **10.3.0** (same `octave-dem` conda env as m0b — not recreated).
- SPM12 / `LPioL/active_inference_morphopsy`: same commits as m0b
  (`03ac9473c` / `bd378a4`) — **sources reused via `../m0b_reference_port/sources/`,
  not re-cloned**, per the ground rules ("you may import m0b's validated
  primitives").
- New paper fetched this session: Pio-Lopez et al. 2022, PDF from
  `frontiersin.org` (24 pages), for Part A6.
- Python: 3.12.14, conda env `fuzzy-blankets`, numpy/scipy as in m0b.

## Repository layout

```
m0c_port_completion/
  README.md                 (this file)
  ORACLE_FACTS.md              Part A: A1-A6, all established
  PORT_DESIGN_UPDATE.md          Part B: the u.v{i} recursion, resolved
  EQUIVALENCE_REPORT.md            Part B: L1 exact, L2 mismatch localized, B5 invoked
  PERTURBATIONS_EXECUTED.md          Part C: catalog, reductions, results
  FALLBACK_ENGINE.md                  Part D: design, correctness check, pilot timing
  OPEN_QUESTIONS.md                    consolidated NOT DONE list
  sources/papers/piolopez2022.pdf        fetched this session
  oracle/                                  instrumented Octave scripts (disclosed patches)
  code/                                     dstep.py (partial port), fallback_engine.py,
                                              storage.py, a5_check.py, run_perturbation_batch.py
  tests/                                     test_l1... / test_storage.py
  data/oracle_traces/                        golden traces, dumps, perturbation batch outputs

../viz/                                   builder (build_viewer.py, build_index.py), VIEWER.md,
                                            output/{observable,audit}/, index.html
```

## Reproducing this session's key results

```bash
conda activate octave-dem
cd morphogenesis/m0c_port_completion
octave --no-gui --eval "addpath('../m0b_reference_port/sources/spm12'); addpath('../m0b_reference_port/sources/spm12/toolbox/DEM'); addpath('../m0b_reference_port/oracle'); addpath('oracle'); DEM=dem_setup(2,32,0); DEM=spm_ADEM_b1(DEM,'data/oracle_traces/b1_dump.mat');"

conda activate fuzzy-blankets
python3 code/a5_check.py          # A5: Mg/Gg exact match
python3 tests/test_storage.py     # Part D schema tests
```

## Proposed repository status entry (paste manually if desired — not applied by this stage)

> **2026-09-29 — Morphogenesis programme, Stage M0c (oracle-driven port
> completion, partial).** New directory `morphogenesis/m0c_port_completion/`
> plus shared `morphogenesis/viz/`. **Resolved m0b's blocking mystery**: the
> `spm_ADEM_diff.m` `u.v{i}` recursion is now fully understood via
> instrumented dumps (predict/correct two-update-per-bin pattern, plus a
> decisive model-specific simplification: the process's `Gg` ignores its
> `v` argument, so `dg.dv≡0` and the recursion has no effective
> self-dependence). **Despite this, the Python port still does not reach
> single-step (L2) equivalence** — a block-decoupled approximation to the
> true joint `dFduu` solve understates the actual state update by 2-7x.
> Per this stage's own timebox rule, Part B stopped there with the mismatch
> precisely localized, and **a Python-driven Octave fallback engine was
> built instead** (subprocess-based, correctness-checked, pilot-timed,
> blinded OBSERVABLE/HIDDEN data schema) to carry Parts C (perturbations —
> Kuchling 2020's double-head/tail/anomalous/rescue and a declared
> interpretation of Friston 2015's Figure 5, run on the real oracle at
> published and sustained-to-512-bin horizons) and E (a self-contained,
> zero-CDN-dependency interactive HTML viewer, reusable by all later
> stages). Primary-source verification of Pio-Lopez et al. 2022 (fetched
> fresh this session) confirmed the paper's precision manipulations target
> all 8 cells (not a subset) and that the two-cell rescue reduces both
> secretion and cross-cell sensitivity, exactly as the task asked to
> verify. **35 perturbation runs completed on the oracle** at both
> published and 512-bin sustained horizons plus a ramp-width sensitivity
> check, finding that population-wide distortions persist/worsen under
> sustained application while single-cell anomalies wash out, and that
> onset ramp width measurably affects outcomes. A self-contained,
> zero-dependency interactive HTML viewer was built and populated with all
> Part A/C exemplars, with a declared exemplar-selection rule. **Next step
> for this programme**: complete the joint `dFduu` solve (the missing
> `dVduv`/`dVdua`/`dVdav`/`dVdau` cross-blocks) against the dump evidence
> already captured in this stage, to finally retire the Octave fallback in
> favor of a validated, fast Python port; and fix the `kuchling_rescue`
> implementation gap (it doesn't pair with an anomaly to rescue).
