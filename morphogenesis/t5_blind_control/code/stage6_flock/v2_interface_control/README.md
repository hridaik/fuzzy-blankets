# v2_interface_control/

V2: a controller frozen only after `../v1_mechanism_audit/` established which
interface actually mediates control of the flock (the dynamical shell `B^D_0`,
not the spectral/Fiedler boundary `B^F_0`). See `PROTOCOL_V2.md` for the full,
frozen protocol (hashed in `logs/protocol_v2.sha256` before any code in
`code/` was run).

## Contents

- `PROTOCOL_V2.md` — the frozen protocol, referencing the mechanism-audit
  findings that justify each design choice.
- `RESULTS_V2.md` — actuator-rule comparison and 10-flock replication results.
- `configs/protocol_v2.yaml` — machine-readable frozen config; hash in `logs/`.
- `code/`:
  - `common_v2.py` — self-contained utilities (imports `../../python/flock_sim`
    unmodified; does NOT depend on `v1_mechanism_audit/code`, so this
    protocol stands on its own).
  - `selection_rules.py` — Rules A (degree) / B (leverage) / C (patch) /
    D (random), operating on `B^D_0`.
  - `replicate.py` — Part L: applies the frozen policy, unmodified, to the
    first 10 qualifying flocks (seeds 0..N in order) and compares all four
    rules plus the full-shell and baseline reference arms.
- `data/replication_results.json` — raw per-flock, per-rule results.
- `figures/` — V2 comparison figures.
- `logs/protocol_v2.sha256` — freeze hash.

## How to reproduce

```
cd code
python3 replicate.py       # scans seeds until 10 qualifying flocks are found,
                            # then runs all 4 rules + 2 reference arms on each
python3 make_v2_figures.py # figures
```

## One scope limitation, stated plainly

Because birds occupy fixed lattice sites in this port (only heading evolves —
see the mechanism audit's Part B structural finding), `B^D_t = B^D_0` for
every `t` *within a single control episode*. "Adaptive interface control"
in this V2 therefore means "the interface is computed fresh from structure
for each new flock," not "the interface visibly moves during one steering
episode" — the latter is not a distinction this specific port's physics can
exhibit. See `PROTOCOL_V2.md` and `RESULTS_V2.md` for the honest accounting
of what this does and does not demonstrate relative to the Stage-5
moving-boundary idea.
