# v1_mechanism_audit/

Additive, non-destructive mechanism audit of the frozen, negative
`protocol_v1` result (see `../RESULTS_V1.md`, `../PROTOCOL_V1.md`). **No file
under `../data/protocol_v1*`, `../data/baseline_v1*`, `../python/`, or any
other pre-existing `stage6_flock/` path is modified, deleted, or rerun with
different parameters by anything in this directory.**

## Purpose

V1 established a negative result under a frozen protocol: sparse control
confined to individually- or pair-ranked exterior birds did not retarget the
frozen core. This directory asks *why*, whether the task is externally
controllable at all, and which of several candidate "interfaces" — spectral
(`B^F`), dynamical/structural (`B^D`), statistical/predictive (`B^{MB}`), and
empirical-control (`B^C`) — actually mediates control of the flock. See
`MECHANISM_AUDIT_RESULTS.md` for the answer (short version: `B^F` and `B^D`
do not coincide; `B^D` is the one that works and the one that is statistically
sufficient; V1's sparse search failed because it never tested `B^D`).

## Contents

- `V1_RECORD_AUDIT.md` — Part A: documentation-inconsistency audit,
  heading-protocol provenance confirmation, canonical-flock representativeness
  (quantified percentiles), port-verification closure attempt (Octave install
  attempted and blocked; deterministic cross-language fixture produced instead).
- `MECHANISM_AUDIT_PLAN.md` — what was planned for Parts B-H, written before
  results.
- `MECHANISM_AUDIT_RESULTS.md` — the actual findings, Parts B-H, including the
  hard interpretation gate applied after Part D.
- `code/` — all new analysis code (not present in the original tree list's
  sketch, added because the scripts need somewhere to live; imports
  `../python/flock_sim` and `../python/analysis` unmodified):
  - `common.py` — shared loaders/utilities.
  - `dynamical_shell.py` — Part B (structural dependency graph, `B^D_0`).
  - `boundary_compare.py` — Part C (`B^F` vs `B^D` vs `B^C` overlap/distance).
  - `feasibility_ladder.py` — Part D (D0/D1/D2/D3+D4/D5 arms).
  - `pair_synergy.py` — Part E (exhaustive 3160-pair sweep).
  - `shell_sparsification.py` — bridges Part D to a sparse V2-ready actuator
    set, restricted to the correctly-identified `B^D_0` pool.
  - `core_resistance.py` — Part F (direct-core resistance curve, diagnostic).
  - `parameter_sensitivity.py` — Part G (`code_default` vs `manuscript_all_ones`).
  - `predictive_screening.py` — Part H (structural + empirical Markov-boundary
    validation).
  - `baseline_spectral_recompute.py` — Part A3 (canonical representativeness).
  - `cross_language_fixture.py` + `octave_fixture/` — Part A4.
  - `make_figures.py` — Part I (all `audit_fig*` figures).
- `configs/` — reserved for any audit-specific config (none needed beyond
  what's hardcoded/documented per-script; all frozen `PROTOCOL_V1a` values are
  imported from `../configs/protocol_v1.yaml`-equivalent constants in
  `code/common.py`, not redefined).
- `data/` — JSON outputs of every script above (`dynamical_shell.json`,
  `boundary_compare.json`, `feasibility_ladder.json`, `pair_synergy.json`,
  `shell_sparsification.json`, `core_resistance.json`,
  `parameter_sensitivity.json`, `predictive_screening.json`,
  `canonical_representativeness.json`, `cross_language_fixture.json`).
- `figures/` — `audit_figA_three_interfaces` through `audit_figH_predictive_screening`
  (PNG+PDF).
- `logs/` — `pair_synergy.log` (background-run log for the 3160-pair sweep).

## How to reproduce

```
cd code
python3 dynamical_shell.py          # Part B — must run first (others read its JSON)
python3 boundary_compare.py         # Part C
python3 feasibility_ladder.py       # Part D
python3 pair_synergy.py             # Part E (~8 minutes)
python3 shell_sparsification.py     # sparsification within B^D_0 (~6 minutes)
python3 core_resistance.py          # Part F
python3 parameter_sensitivity.py    # Part G (~2 minutes)
python3 predictive_screening.py     # Part H
python3 baseline_spectral_recompute.py  # Part A3
python3 cross_language_fixture.py       # Part A4
python3 make_figures.py             # Part I
```

Every script reads only from `../data/protocol_v1/`, `../data/baseline_v1/`,
and `../python/`, and writes only under this directory.

## Key numbers (see MECHANISM_AUDIT_RESULTS.md for full detail)

- `|I0|=20`, `|B^F_0|=2`, `|B^D_0|=12` on the canonical flock; `B^F_0 ⊂ B^D_0`.
- Feasibility ladder: `B^F_0` control fails (`p_success=0.00`); the correctly
  identified `B^D_0` (12 birds) succeeds at `p_success=0.96`, statistically
  matching forcing all 80 exterior birds.
- A sparsified 9-bird subset of `B^D_0` (found by greedy search restricted to
  the correct 12-bird pool) already reaches `p_success=0.90`.
- The full 3160-pair sweep confirms no pair (from anywhere in the 80 exterior
  birds) comes close to success — sparse control needs most of the correct
  shell, not a clever pair.
- `B^D_0` is an exact statistical Markov blanket for `I0`'s next state
  (0.0000 excess log-loss vs. ground truth, verified on 8,000 bird-samples);
  `B^F_0` is not (+0.032 nats excess log-loss).
- Under the manuscript's literally-stated "all precisions = 1," this model
  essentially never flocks (0/50 seeds qualify) — strong quantitative support
  that the paper's actual reported simulations used the code's defaults
  (`rho=15, omega=3`), not the text's stated value.
