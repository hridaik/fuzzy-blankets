# DATA_SCHEMA.md — tiered data schema (Task D)

Implemented in `code/storage.py`. **ESTABLISHED** (implemented and exercised
by `code/run.py`; see `data/golden_traces/*/` for real output on disk).

## Directory layout

```
data/golden_traces/<run_id>/
  manifest.json                # content hashes (sha256 of each array's bytes)
  observable/
    positions.npy               # (n_bins, 2, n_cells) -- a.x per bin
    secretion.npy                # (n_bins, 4, n_cells) -- a.s per bin
    ligand_at_probes.npy          # (n_bins, 4, n_probes) -- field sampled at fixed probe points
    probe_points.npy               # (2, n_probes)
    intervention_log.json           # list of {id: OPAQUE, cells, bins, dose} -- no mechanism
  hidden/
    v_expectations.npy           # (n_bins, n_cells, n_cells) -- recognition cause v
    softmax_p.npy                 # (n_bins, n_cells, n_cells) -- spm_softmax_cols(v)
    eps_x.npy, eps_s.npy, eps_c.npy   # prediction errors per channel
    free_energy.npy                # (n_bins,) scalar per bin
    config.json                     # full run config (seed, n_bins, n_cells, ...)
    intervention_mapping.json        # OPAQUE id -> {name, params} -- the sealed mapping
```

## Tier contents (exact fields)

**OBSERVABLE** (per Task D spec): per-cell positions and secreted signal
levels per bin; ligand concentrations at a configurable set of probe points;
intervention log with **opaque IDs only** (`cells`, `bins`, `dose` are
retained per the task prompt's own wording — note this means cell indices and
bin indices ARE observable even though the *mechanism* is opaque; this
matches the prompt's literal spec: "cells, bins, dose — no mechanism").

**HIDDEN**: internal expectations (`v`, `softmax_p`), prediction errors,
free energy, the target template (`P.x`/`P.s`/`P.c`, reconstructable from
`code/template.py` + `config.json`'s recorded template choice), generative-
model parameters (precisions, hard-coded in `code/solver.py` — recorded
verbatim in `config.json` for provenance), the field law
(`code/field.py`), and the sealed opaque-ID → implementation mapping
(`intervention_mapping.json`).

## Loader / blinding enforcement

`storage.load_observable(root, run_id)` — always allowed, no flag needed.

`storage.load_hidden(root, run_id, audit=False)` — raises `PermissionError`
unless `audit=True` is passed explicitly. **ESTABLISHED**, tested:

```python
>>> storage.load_hidden(root, run_id)
PermissionError: Hidden-tier access requires audit=True. ...
>>> storage.load_hidden(root, run_id, audit=True)
{...}  # succeeds
```

## Known gap (disclosed)

Physical separation is directory-level, not filesystem-permission-level (no
OS-level ACLs are set on `hidden/`). A blinded analyst using the Python
loader API is enforced; a blinded analyst with raw filesystem access is not
prevented from reading `hidden/*.npy` directly. This was judged sufficient
for a single-user local research repository at this stage; flagged in
OPEN_QUESTIONS.md if this programme moves to a multi-analyst setting.
