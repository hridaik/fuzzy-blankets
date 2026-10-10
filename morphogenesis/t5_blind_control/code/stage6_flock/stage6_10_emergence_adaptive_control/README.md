# Stage 6.10 — Emergence → dynamic identity/interface → adaptive steering

**Question.** Can an emergent, operationally thing-like collective be detected
online, tracked while both its membership and its causal interface change, and
adaptively redirected through that interface — while remaining the same valid
lineage?

Additive to Stages 6–6.9. Nothing frozen in an earlier stage is modified.

## Order of work (each gates the next)

| Part | What | Status |
|---|---|---|
| A | Audit the Stage 6.8 "oracle" anomaly before running anything new | done |
| B | Three independent reference modules, cross-unit-tested | done — they agree exactly |
| C | Full-model control benchmark (optimizes the objective) | done |
| D | Blind, task-neutral detection | done |
| E | Thingness profile (C, G, L, D), thresholds frozen on uncontrolled data | done |
| F | Clumpness `Q_clump` as a separate axis (cardinal perimeter only) | done |
| G | Regime selected from uncontrolled data only | done — β = 0.4, s = 0.75 |
| H | Establish controllability with the benchmark **before** testing inference | running |
| I | Seven-arm online closed loop, matched budgets + fixed-K | pending H |
| J | Identity-valid scoring against an uncontrolled validity envelope | envelope built |
| K | Release phase — does it hold the heading with control off? | pending I |
| L | One clarity trajectory, median rule, illustration only | pending I |

## Naming

The Stage 6.8 arm stored as `adaptive_oracle` is the **full-info causal
heuristic**. It is not an oracle: it ranks actuators by a task-agnostic KL
influence and does not optimize the control objective. The honest upper
reference is the **full-model control benchmark**, and it is called an *optimum*
only where an exhaustive search genuinely completed.

## Layout

```
code/     reference_truth.py     structural / interventional / task-authority modules
          full_model_benchmark.py exhaustive | beam | CEM, with convergence checks
          morphology.py          cardinal-perimeter clumpness
          thingness.py           (C, G, L, D), held-out, spatially restricted
          regime_probe.py        standardized weak directional probe, policy saturation
          identity_scoring.py    lineage statistics, validity envelope, conjunctive score
          closed_loop.py         the seven arms and the shared start-state rule
          run_*.py               drivers, one per part
data/     one JSON per run, written incrementally
logs/     predeclarations and run logs
figures/  fig_6_10_*
```

## Reading the results

`RESULTS_6_10.md`. Three things in it are negative results and are meant to be
read as such: the Stage 6.8 arm ordering was never statistically established;
the Stage 6.8 operating point is policy-locked; and material membership overlap
carries no identity information at this regime's 24-step horizon.
