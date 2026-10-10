# Stage 6 — flock: sparse steering of an emergent spectral macro-agent

Validation track built on the flocking active-inference model from Maisto, Nuzzi
& Pezzulo, "What the flock knows that the birds do not" (arXiv:2511.10835), and
its accompanying MATLAB code (`upstream/`, GPLv3,
https://github.com/dommai/flock_knows_what_birds_dont, commit
`06be55a45091e0883479f981e273410400bb7c3b`).

Question: can a sparse, external, boundary-only intervention reproducibly
reorient a spontaneously-formed flock's frozen interior identity to an adjacent
cardinal heading, while the interior remains identifiable as part of a
(dynamically reorganizing) spectral macro-agent?

Stages 1-5 elsewhere in this repository are read-only prior work (Gaussian toy
models of graded functional boundaries); nothing here imports or modifies them.

## Reading order

1. `METHODS_AUDIT.md` — line-by-line audit of the upstream MATLAB source
   (Phase 0), including every manuscript-vs-code discrepancy found.
2. `PORT_VALIDATION.md` — how the Python port was validated in the absence of a
   local MATLAB/Octave install, plus a structural simplification discovered
   (and proved) during porting.
3. `PROTOCOL_V1.md` — every threshold used in Experiment 1, frozen from
   baseline (uncontrolled) data before any control experiment ran, including
   one post-freeze correction (a heading-encoding bug) applied before the
   actuator search began.
4. `RESULTS_V1.md` — what was actually found.

## Layout

```
python/flock_sim/    the ported simulator + spectral analysis (library code)
python/analysis/     one script per experimental phase (baseline sweep,
                      canonical snapshot, controls, response map, ...)
python/figures/       one script per figure, reading only from data/
tests/                pytest unit/validation tests (run: pytest tests/ -q)
configs/              frozen protocol_v1.yaml + its sha256
data/                 raw + derived results, one subfolder per phase, never
                      overwritten (superseded runs are renamed, not deleted)
figures/              PNG + PDF outputs
upstream/             verbatim upstream MATLAB source + LICENSE (GPLv3)
```

## Scope note

The upstream model has a predator/stress-response variant (Appendix A.3 of the
paper). Experiment 1 as specified does not exercise predator dynamics, so the
Python port implements the heading-only generative model exactly and does not
(yet) port the stress/danger factor — this is a deliberate, documented scope
reduction (METHODS_AUDIT.md section 13), not an omission discovered later.

## Continuing work (additive, does not modify anything above)

`v3_refinement/` refines and closes the retargeting problem opened by
`RESULTS_V1.md`/V2 (interface-control law, transition-aware integrity,
predictive permeability vs. horizon); `interactive_demo/` is a
self-contained interactive walkthrough built on real simulator
trajectories. Start at `STAGE6_FINAL_REFINEMENT.md` for the short version,
or `v3_refinement/README.md` for the full one. Nothing in this section or
below has been changed.

`stage6_5/` is further additive work: it removes two conveniences the
sections above relied on (privileged access to the simulator's true
interaction graph; a permanently frozen interior) as methodological
preparation for a future moving-shepherding model. See
`STAGE6_5_SYNTHESIS.md` for the summary or `stage6_5/README.md` to start
reading. Nothing above this paragraph has been changed.

## Running

```
cd stage6_flock
python3 -m pytest tests/ -q
python3 python/analysis/baseline_characterization.py
python3 python/analysis/canonical_snapshot.py
python3 python/analysis/phase3_controls.py
python3 python/analysis/phase4_5_response_map.py
python3 python/figures/fig1_fig2_baseline.py
python3 python/figures/fig3_fig4_response_map.py
```
