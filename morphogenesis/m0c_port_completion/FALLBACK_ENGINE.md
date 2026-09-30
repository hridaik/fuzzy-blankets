# FALLBACK_ENGINE.md — Part D

## Status: `ESTABLISHED`, built and pilot-timed, used as the engine for Part C.

## Design

`code/fallback_engine.py` exposes `run(config, initial_state, noise_seed,
interventions, n_bins) -> (mat_dict, elapsed_seconds)`, implemented as a
**subprocess call into the `octave-dem` conda environment** (not oct2py —
zero extra dependency, and this programme already shells out to Octave via
`bash -c` throughout m0b/m0c, so this is the path of least surprise).

- `config`: `{'L': 2|4}` (template selection).
- `initial_state`: optional `v` override array (Pio-Lopez high-identity
  variants, or any custom initial condition).
- `interventions`: `None` (plain oracle, calls m0b's `run_and_export.m`
  unmodified) or `{'kind': str, 'params': dict}` (calls this stage's
  `oracle/run_perturbed.m`, Part C).
- Every rollout is saved via `code/storage.py`'s tiered schema
  (`save_rollout`), which **records the engine** (`'fallback_octave_subprocess'`,
  or `'octave_oracle'` for the raw Part A/B runs) and a `validation_status`
  field on every manifest — satisfying "every rollout records which engine
  produced it."

## Correctness check: the "none" perturbation path is bit-identical to the plain oracle

Before trusting `run_perturbed.m` for Part C, verified that
`kind='none'` reproduces `run_and_export.m`'s output **exactly**:
`max abs diff positions: 0.0`, `max abs diff v_expect: 0.0` (8-bin vanilla
run, seed 0). This confirms the perturbation machinery (`dem_setup_perturbed.m`,
`dem_morphogenesis_Gg_perturbed.m`) is a true superset of the unperturbed
path, not an independent (and possibly subtly different) reimplementation.

## Pilot timing (Part D's explicit requirement)

| Config | n cells | N bins | elapsed |
|---|---|---|---|
| vanilla-8 (L=2) | 8 | 512 | **254.5 s** (seed 0) / 256.8 s (seed 1) |
| 16-cell (L=4) | 16 | 512 | **728.4 s** (measured, seed 1) |

Runtime scaling from m0b/m0c measurements: linear in `N` (single-pass D-step,
`nE=1`), super-linear in `n` (measured: n=16 is `728.4/255.6 ≈ 2.85x` slower
than n=8 at the same `N=512`, for a 2x increase in `n` — consistent with the
`n^2.5-3` scaling predicted from the finite-difference Jacobian's `O(n)`
perturbations × field evaluation cost, and matching the n=16,N=32 pilot's
own `44.6/15.25 ≈ 2.9x` ratio vs n=8,N=32).

**Runs/hour at full parallelism** (8 cores, one Octave process per core;
confirmed no problematic internal multi-threading contention in practice —
the Part C batch ran 5 concurrent Octave processes cleanly, wall time
836.4s for 31 jobs vs. a naive serial-sum estimate of ~4700s, a ~5.6x
speedup consistent with 5-way parallelism):
- n=8, N=512: `3600/255 ≈ 14.1` runs/hour per core → **~113 runs/hour at
  8-way parallelism**.
- n=16, N=512: `3600/728.4 ≈ 4.9` runs/hour per core → **~39.5 runs/hour at
  8-way parallelism**.

## Blinded data schema

`code/storage.py` re-implements (not imports) the OBSERVABLE/HIDDEN tiered
design first specified in `m0_reconstruction/DATA_SCHEMA.md` (schema reused;
that stage's deprecated solver is not imported, per this stage's ground
rules):

```
data/golden_traces/<run_id>/
  manifest.json          (engine, validation_status, content hashes)
  observable/
    positions.npy, secretion.npy, ligand_at_probes.npy (if provided),
    intervention_log.json (opaque IDs, cells, bins, dose -- no mechanism)
    engine_and_validation.json
  hidden/
    v_expect.npy, free_energy.npy, pred_err_1.npy, pred_err_2.npy,
    target_x/s/c.npy, config.json, intervention_mapping.json (sealed)
```

`storage.load_hidden(root, run_id, audit=False)` raises `PermissionError`
unless `audit=True` — same enforcement pattern as m0's schema, re-tested
here (not just copied) — see `tests/test_storage.py`.

## Known limitations of this fallback (disclosed)

- Every call pays Octave's interpreter startup cost (~1-2s) on top of the
  actual computation — negligible for N=512 runs, non-negligible if this
  engine were used for very short (N<8) runs at scale.
- No batching within a single Octave process (each `run()` call spawns a
  fresh `octave-cli`), which is simple and robust but not optimal for
  throughput; acceptable given the runs/hour figures above are already
  adequate for this stage's needs.
