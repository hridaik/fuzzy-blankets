# v3_refinement/

Refines and closes the single-core retargeting problem opened by
`../v1_mechanism_audit/` and `../v2_interface_control/`, per
`STAGE6_SYNTHESIS.md`'s "Next scientific experiments" #1. Additive only —
nothing here modifies V1/V2 code, data, configs, or results.

## Reading order

1. `REFINEMENT_PLAN.md` — pre-registered design: what is measured, which
   flocks are development vs. held-out, and the rule for turning
   measurements into thresholds (fixed *before* any V3 sweep ran).
2. `INTEGRITY_DEFINITION.md` — conceptual note on what "functional
   integrity" should mean for a state transition, written before any
   numeric threshold was chosen.
3. `PROTOCOL_V3.md` — the frozen protocol (config hash in `logs/`), written
   after Part 1's development-flock sweep and before any held-out, staged-
   actuation, or predictive-permeability result.
4. `RESULTS_V3.md` — what was actually found, including where the data did
   *not* confirm the boxed hypothesis.

## Layout

```
code/                  one script per part (see below), importing
                        python/flock_sim and v2_interface_control/code
                        unmodified
configs/protocol_v3.yaml + logs/protocol_v3.sha256   frozen config + hash
data/                  raw results, one JSON per script
figures/               R1-R6, PNG + PDF
tests/                 (reserved; core logic is exercised via the existing
                        28 flock_sim tests plus the smoke-tested scripts
                        themselves)
```

## Code, in the order it should be run

```
python3 code/coverage_sweep.py           # Part 1B: dev-flock coverage sweep
python3 code/fit_success_models.py       # Part 1C: what predicts success
python3 code/minimal_interface.py        # Part 1D: minimal sufficient interface
python3 code/analyze_baseline_transition.py   # Part 2 prep: transition stats
#  ---- PROTOCOL_V3.md frozen here ----
python3 code/held_out_eval.py            # Part 1E: held-out generalization
python3 code/staged_actuation.py         # Part 2D: scheduling comparison
python3 code/predictive_permeability.py  # Part 3: horizon sweep
python3 code/make_v3_figures.py          # Part 5: figures
```

`common_v3.py`, `coverage_metrics.py`, `selection_rules_v3.py`, and
`evaluate_v3.py` are shared library code imported by the scripts above, not
run directly.

## The one-sentence finding

Plain interface coverage (`Gamma(A)`, "does this core bird have *some*
actuated neighbor") turned out to be the **weakest** predictor of control
success tested — worse than raw actuator count. Mean actuator-neighbor
*multiplicity* (redundant support per core bird) is the strongest. The
refined, still-sparse controller this motivates needs only ~54% of the
shell (vs. V2's 75%) for comparable development-flock success, generalizes
imperfectly-but-honestly to held-out flocks, and resolves the
integrity-criterion tension from V1/V2 by checking for bounded
*reconvergence* rather than a physically-impossible zero-tolerance bar
during a state transition.
