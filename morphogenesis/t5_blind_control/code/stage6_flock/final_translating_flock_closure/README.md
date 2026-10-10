# Final Translating-Flock Closure

This directory is the FINAL bounded experimental pass on the
translating-flock research programme (Stage 6.x) before the project moves
to morphogenesis. It completes three compact closures and produces the
programme-level synthesis and morphogenesis handoff.

- **Closure A — organizational role / membership privilege.** Does being
  inside the collective, on its organizational boundary, or an actual live
  exterior causal parent create a different, reproducible intervention
  channel — even though no single exterior bird's identity does (Stage
  6.12C / `stable_selectivity_analysis`)?
- **Closure B — true FOV-gated directed causal interface.** Does the
  simulator's actual directed `live_edges` relation explain intervention
  effect better than the geometric proximity metric used throughout Stage
  6.12/6.12B/6.12C (`mech_cumulative_contact_edges`, shown by
  `CONTACT_METRIC_AUDIT.md` to be undirected and FOV-free)?
- **Closure C — minimal timing-susceptibility check.** Is outcome variation
  across intervention ONSET time materially larger than variation across
  actuator identity at a fixed onset?

See `EXPERIMENT_PROTOCOL.md` for the full method, `STATE_MANIFEST.md` for
the 8 fresh states, and `FINAL_CLOSURE_FINDINGS.md` for the answers.

## Directory layout

```
final_translating_flock_closure/
  README.md                        (this file)
  EXPERIMENT_PROTOCOL.md            method, RNG protocol, runtime benchmark
  STATE_MANIFEST.md                 8 fresh states (seeds 64200-64207)
  ORGANIZATIONAL_ROLE_RESULTS.md    Closure A results
  LIVE_EDGE_CAUSAL_INTERFACE.md     Closure B results
  TIMING_SUSCEPTIBILITY.md          Closure C results
  IDENTITY_AND_DISRUPTION.md        identity validity / persistence across all closures
  STATISTICAL_ANALYSIS.md           state-paired/state-clustered method notes
  FINAL_CLOSURE_FINDINGS.md         concise answers to the 6 final scientific questions
  MORPHOGENESIS_HANDOFF.md          what the next programme should/shouldn't carry forward
  code/                             all closure code (see EXPERIMENT_PROTOCOL.md)
  data/                             machine-readable rollout data + analysis summary
  figures/                          (referenced from the *.md files)
  logs/                             run timing logs
```

## Reproducing

```
cd code
python3 world_sampling_closure.py      # writes data/state_manifest_closure.json
python3 run_closureAB.py               # writes data/closureAB_*.json  (~19 min, 1 core)
python3 run_closureC_timing.py         # writes data/closureC_timing_*.json (~17 min, 1 core)
python3 analysis_closure.py            # writes data/closure_analysis_summary.json
```

Requires the `fuzzy-blankets` conda environment (`numpy`, `scikit-learn`
are used transitively by imported Stage 6.11 modules).

## Hard stop

Per the task spec, this is the last translating-flock experimental pass.
No further flock experiments were initiated after these three closures,
regardless of what they found — see `FINAL_CLOSURE_FINDINGS.md` question 6
and `stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md`.
