# Morphogenesis programme — Stage M2a: audit of M1, generalization, library, blind package

## STATUS: `STOPPED AT GATE` after Part 0. Gate result: **FAIL** (one injection control). Parts 1–4 `NOT DONE`.

Why: M1's AN ("anomalous cell") runs never applied a single-cell perturbation. They are bit-identical to the DH runs (`cells=[]` was passed to Octave). Per the task, I stopped and am proposing a corrected re-run rather than building on M1 as-is. Everything else in M1 passed its injection controls. Details: `AUDIT_M1.md`.

## Status table
| Part | Status |
|---|---|
| 0.1 injection controls | **DONE** — beliefs, designed permutation control, kicks, DH, DT, sham PASS; **AN FAIL** |
| 0.2 direct-Octave cross-check | **DONE** — PASS, bit-identical |
| 0.3 explain the exactness | **DONE** — strong contraction; stationarity at bin 246 is ramp-driven |
| 0.4 role maps | **DONE** — 248 distinct of 250 |
| 0.5 near-miss mechanism | **DONE** — unconcentrated beliefs |
| 1 generalization (16-cell, other families, k=2/4) | **NOT DONE** (gate) |
| 2 perturbation-response library, linearity | **NOT DONE** (gate) |
| 3 blind package, leak check, data dictionary | **NOT DONE** (gate); nothing in `m2_blind_package/` |
| 4 viewer | **NOT DONE** (gate); one static figure only |
| COMPUTE_PLAN.md | provisional, unpiloted |

## Headline answers
- **Is M1 confirmed?** Mostly. Census exactness is real (injection works, an independent Octave script reproduces M1 bit-for-bit, individuals merge with time constant ~9 bins). Reinterpreted: the "reference phenotype" is the fixed point at the end-of-run ramp value s=0.865, and "stationary at bin 246" is the ramp's own pace (frozen ramp: bin 35). Kicks and DH/DT/sham reversion are confirmed at shape level. **Not confirmed:** AN (never single-cell), and "no durable effect": the cell-to-role assignment is changed in 155/180 withdrawal runs and 58/60 sham runs (permutation-invariant d_pair cannot see it). `ESTABLISHED`.
- **Is the 16-cell template monostable?** `NOT DONE`.
- **Do the other perturbation families revert?** `NOT DONE`.
- **Is the library linear?** `NOT DONE`.
- Also found: process noise is identically zero (engine is deterministic); the near-miss comes from unconcentrated beliefs (max belief 0.72–0.78).

## What I need from you
See `AUDIT_M1.md` (end) and `OPEN_QUESTIONS.md`: approve the AN re-run (~1.3 h), pick the ramp protocol for Parts 1–2, and say whether to keep zero noise.

## Layout
```
AUDIT_M1.md  COMPUTE_PLAN.md  OPEN_QUESTIONS.md  GENERALIZATION.md/LIBRARY.md/LINEARITY.md (NOT DONE stubs)
oracle/   direct_morph.m (0.2), m2a_run.m + m2a_{Gg,Mg,ramp,pulse,field,templates}.m (toolkit; ramp modes, pulse events)
code/     part0_*.py (launch, offline analyses, 0.1c audit, figures), m2a_sim.py, m2a_common.py, run_unperturbed_twins.py
tests/    test_toolkit.py, test_part0_findings.py   (python3 -W ignore tests/test_*.py)
data/     part0/, twins/, MANIFEST.md        figures/part0_merge_and_stationarity.png
```
Toolkit status: `m2a_run.m` reproduces the fallback engine bit-exactly in default mode (N=64 and N=512 checked). Pulse/event machinery (`pos`/`sec`/`gain`) is written but **untested in simulation**.

## Proposed repository status entry (do not apply automatically)
> **2026-10-01 — Morphogenesis programme, Stage M2a (audit), stopped at gate.** New directory `morphogenesis/m2a_audit_and_library/`. Independent audit of M1: initial-belief and kick injection verified, a hand-written Octave script reproduces M1 trajectories bit-for-bit, and M1's exact convergence is genuine strong contraction (merge time constant ~9 bins) onto the fixed point at the end-of-run developmental ramp value; M1's stationarity time (bin 246) is set by that ramp (frozen ramp: bin ~35). The engine has zero process noise. Near-miss of the target is explained by unconcentrated beliefs (max 0.72–0.78). **Gate failed:** M1's single-anomalous-cell (AN) runs were bit-identical to DH runs (cells not passed). DH/DT/sham reverted in shape, but cell-role assignment changed in 155/180 withdrawal and 58/60 sham runs. Parts 1–4 (generalization, response library, blind package, viewer) not run; corrected AN re-run (~1.3 h) and protocol decisions proposed.
