# Stage 6.11 Evidence Recovery — 2026-09-21

## Purpose

This directory is a **forensic audit**, not a new experiment. It was
commissioned because a fresh visual inspection of seed 500 raised the
possibility that an apparent large identity jump around **t=46→47** (most
material not retained; tracker allegedly jumping to a flock already heading
toward the target) had been missed by earlier adjudication, and that some
of that earlier adjudication (the "ID-independent rescoring" that
overturned seeds 501/502 as successes) might itself need to be pinned down
precisely rather than taken on faith.

**No redesign was performed.** This audit did not: change
`lineage_611.LineageTracker611`, `lineage_v2_611.LineageTrackerV2`,
`run_online_control_611.py`'s control loop, `control_authority_611.py`,
`moving_flock_611.py`, or any success/qualification threshold. It did not
pick a material-retention threshold to rescue or reject any seed. Every
number in `seed_500.md`–`seed_504.md` and `seed_summary.csv` is either read
verbatim from an existing, dated repository artifact (with file/function
citation) or derived by new, additive, read-only scripts in `code/` that
recompute simple set arithmetic (Jaccard, retained/lost/gained) from
already-recorded membership lists — never by re-running the tracker,
controller, or simulator.

## What this audit found, in one paragraph

The "ID-independent rescoring" that withdrew seeds 501/502 as validated
successes is `branch_adjudication_611.py`'s `field_direction_readout`
(a fixed-radius, position-only, ALL-nearby-birds readout anchored at the
v2 comparator tracker's current centroid) plus the `original_material`
readout (fixed to the exact bird-ID set present at trigger); see
`rescoring_provenance.md`. Seed 500's suspected t=46→47 jump **does not
appear in any recorded production artifact**: the interior at t=46 and
t=47 is the identical 38-bird set in `viz_bundle_611__seed500.json`,
`interactive_demo/v2/data/tab6_translation.json`, and the independently
re-verified tracker replay (`lineage_forensics_611`); target_heading is
`None` at both t (qualification does not happen until t=61); centroid
displacement between the two frames is 0.28 spatial units, not a
torus-wrap-scale jump. Seed 500's own genuine, already-documented
discontinuities are at t≈1, 21, 27, 39 — all before qualification, none
during control. See `seed_500.md` and Section 4 of `audit_findings.md`.

## Reproducing this audit

```
conda activate fuzzy-blankets
cd stage6_flock/stage6_11_translating_torus/audit/evidence_recovery_20260921/code
python3 derive_material_retention.py   # writes ../data/material_retention_seed{500..504}.csv + manifest
python3 make_plots.py                  # writes ../plots/*.png
```

Both scripts are deterministic given the repository's existing, unmodified
`audit/lineage_forensics_611__seed*` outputs and `data/viz_bundle_611__seed*.json`
files, and write a JSON manifest recording the git commit and invocation
(`data/material_retention_manifest.json`).

The v2 interactive-demo instrumentation (material-retention panel) is
reproduced by:
```
cd stage6_flock/interactive_demo/v2/src
python3 data_prep/prep_tab6_translation.py   # regenerates ../data/tab6_translation.json with material_retention blocks
python3 build_v2.py                          # rebuilds ../build/index.html
```

## Repository commit used

`940a5f672bc9b8302c0436e5a531cea6ae1f6ce1` (main, 2026-09-15). No commits
were made changing tracker/controller/world code as part of this audit;
only new files under this directory and the additive instrumentation
described in `README.md`'s "Interactive demo" section were added.

## No-redesign statement

This audit's scripts (`code/derive_material_retention.py`,
`code/make_plots.py`) and the interactive-demo instrumentation
(`interactive_demo/v2/src/data_prep/prep_tab6_translation.py`,
`interactive_demo/v2/src/js/tab6.js`) perform **only**:
- reading already-recorded membership lists (`interior` fields) that the
  original production run already wrote to disk,
- computing set intersection/union arithmetic on those lists,
- rendering the result.

They do not call, patch, subclass, or monkeypatch any tracker, controller,
or simulator code, and they do not change what data
`run_online_control_611.py` or `lineage_611.py` produce. Existing audit
artifacts under `stage6_11_translating_torus/audit/` (not under this
subdirectory) were read and cited, never edited.

## Directory contents

| file | content |
|---|---|
| `README.md` | this file |
| `code_provenance.md` | historical claim/formula → source file/function/config map |
| `intervention_timing.md` | exact original 6.11 and 6.11B timing semantics |
| `rescoring_provenance.md` | exact reconstruction of "ID-independent rescoring" |
| `seed_500.md` … `seed_504.md` | per-seed chronological physical/identity/control audit |
| `seed_summary.csv` | one row per seed, separating original/rescored/physical/material/persistence/causal/actuator evidence |
| `data/material_retention_seed{500..504}.csv` | per-time-step R_old/R_new/Jaccard/retained/lost/gained, displayed and branch-internal |
| `data/material_retention_manifest.json` | provenance manifest (git commit, sources, crosscheck results) |
| `plots/seed{500..504}_material_retention_and_heading.png` | required visualization #1/#2 combined, per seed |
| `plots/R_old_distribution_ordinary_vs_flagged.png` | exploratory sensitivity view (not a threshold recommendation) |
| `audit_findings.md` | established facts, discrepancies, unresolved questions |
| `NEXT_STEP_RECOMMENDATIONS.md` | what the recovered evidence implies for Step 2, nothing more |

## What this audit did NOT produce (explicit gaps, per the stop-condition instructions)

- **No new wrapped-torus / target-centered animated replay** beyond the
  already-existing `interactive_demo/v2` tab 6 (world + co-moving panes,
  now with material-retention overlay) and the static per-seed plots. A
  frame-by-frame video export was judged out of scope for the time budget
  of this pass; the existing interactive replay plus the retention plots
  are sufficient to answer the primary questions asked.
- **No independent re-reproduction of the candidate-pool recall numbers**
  (`BLIND_POOL_AUDIT.md`'s nearest-20 100% recall claim) — cited from its
  existing artifact (`audit/blind_pool_611.json`), not re-run, because
  re-running it changes nothing about what is being audited here (Step 1
  is about recovering what happened, not re-certifying prior audit passes
  that already show their own work).
- **No new per-timestep table for the full candidate/hypothesis internals**
  of seeds 501–504 beyond what `lineage_forensics_611__seed{n}__hypotheses.csv`
  already provides (cited, and extended with Jaccard/retained/lost/gained
  in `data/material_retention_seed{n}.csv`). Re-deriving those from scratch
  would only reproduce a script that already exists, is already verified
  against production output with 0 mismatches, and is already cited by
  path/line throughout `code_provenance.md`.
