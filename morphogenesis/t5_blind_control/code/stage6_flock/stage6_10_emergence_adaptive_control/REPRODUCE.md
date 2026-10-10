# Stage 6.10 — how to re-run and how to check it

Everything below is evaluation-side. Stages 6–6.9 are read-only inputs; no
script here writes outside `stage6_10_emergence_adaptive_control/`.

## Environment

```bash
PY=/home/hkhurana/miniconda3/envs/fuzzy-blankets/bin/python
cd stage6_flock/stage6_10_emergence_adaptive_control
OMP_NUM_THREADS=1            # every script is single-threaded; parallelism is by sharding
```

`code/common_610.py` puts `stage6_flock/python` and
`stage6_8_dynamic_interactions/code` on `sys.path`. **Import `common_610` before
`episode_data`** — it is what makes the Stage 6.8 modules importable.

## Pipeline, in dependency order

Each step consumes the previous step's frozen output. Wall times are for an
8-core machine; the sharded steps run one process per shard.

| # | Command | Writes | ~time |
|---|---|---|---|
| 1 | `$PY run_audit_trace.py` | `data/audit_trace.json` | 25 min |
| 2 | `$PY run_audit_hypotheses.py` | `data/audit_hypotheses.json` | 5 min |
| 3 | `$PY run_audit_fixedk.py` | `data/audit_fixed_k.json` | 20 min |
| 4 | `$PY run_regime_scan.py` | `data/regime_scan__main.json` | 30 min |
| 5 | `$PY run_uncontrolled_reference.py main` | `data/uncontrolled_reference__main.json` | 6 min |
| 6 | `$PY add_thingness_ranks.py main` | (adds `rank_*` in place) | instant |
| 7 | `$PY run_benchmark_convergence.py 0.25` | `data/benchmark_convergence__main.json` | 15 min |
| 8 | `$PY run_controllability.py <cell>` ×6, then `merge main` | `data/controllability__main.json` | 25 min sharded |
| 9 | `$PY run_select_task.py main` | adds `frozen_task` to the above | instant |
| 10 | `$PY run_closed_loop.py <seed> main` ×7, then `merge main` | `data/closed_loop__main.json` | 35 min sharded |
| 11 | `$PY run_closed_loop.py <seed> fixedk fixedk` ×7, then `merge fixedk` | `data/closed_loop__fixedk.json` | 35 min sharded |
| 12 | `$PY run_release_clarity.py fixedk` (and `main`) | `data/release__*.json` | 5 min |
| 13 | `$PY make_figures_610.py` | `figures/fig_6_10_*.{png,pdf}` | 1 min |

Shard values: cells are `f0.25_T12 f0.25_T24 f0.5_T12 f0.5_T24 f0.75_T12
f0.75_T24`; seeds for steps 10–11 come from
`data/controllability__main.json → frozen_task.primary_episodes`.

Launch a sharded step detached so it survives the shell:

```bash
for c in f0.25_T12 f0.25_T24 f0.5_T12 f0.5_T24 f0.75_T12 f0.75_T24; do
  OMP_NUM_THREADS=1 PYTHONUNBUFFERED=1 setsid nohup $PY run_controllability.py $c \
      > ../logs/run_ctrl_$c.log 2>&1 < /dev/null &
done
```

## How to check it

### 1. The unit gates (fast, run these first)

```bash
$PY -m pytest tests/ -q          # 29 tests, ~2.5 min
```

Four of them are the load-bearing ones:

| test | what it protects |
|---|---|
| `test_reference_truth.py::test_structural_and_interventional_truth_agree` | Part B gate — the two truth modules are independent implementations and must agree. **If this fails, stop the stage.** |
| `test_reference_truth.py::test_hold_semantics_*` | authority stays one-shot; the benchmark plans the intervention it executes |
| `test_gate_matches_part_i.py` | the Part H gate is the same code as the Part I benchmark arm — the defect that superseded two scans |
| `test_identity_scoring.py` (7 cases) | the conjunctive score rejects shrink-to-win, splitting, destruction+replacement and material-only persistence even when the heading target is met |

### 2. The pre-registrations were written before the data

- `logs/regime_selection_predeclared.txt` — criteria R1–R7 and the tie-break,
  written before `regime_scan__main.json` was read.
- `logs/task_selection_predeclared.txt` — rules 1–4 plus four addenda recording
  every supersession. **These rules were never modified**; the addenda only
  record what was re-run and why.

Check that the selected regime and task actually follow the rules: rerun
`run_select_task.py` and confirm it reproduces `frozen_task` unchanged.

### 3. Thresholds are frozen on uncontrolled data only

`run_uncontrolled_reference.py` forces no actuator and has no target heading —
control success is not computable inside it. Anything it freezes (thingness
landscape, clump stratum, identity envelope) is therefore independent of any
controller's performance. Verify by grepping: the module imports no arm.

### 4. Provenance of superseded runs

| file | why superseded |
|---|---|
| `data/controllability__SUPERSEDED_hold1.json` | benchmark planned a one-shot intervention while executing a held one |
| `data/controllability__SUPERSEDED_largestcand.json` | gate tracked the largest candidate; Part I steers the qualifying start |
| `data/controllability__SUPERSEDED_pathdrift.json` | gate reimplemented Part I's loop and drifted in pool, rollout count and CRN seed |
| `data/superseded_partI/` | a Part I run built on the second gate's stratum |
| `logs/RESULTS_6_10.CORRUPTED.bak` | results file damaged by a concurrent second session; rebuilt from `data/` |

None of these feed any claim. They are kept so the history is auditable.

### 5. The two numbers that are *not* measurements

- **Benchmark task-success inside the primary stratum.** The stratum is defined
  by the benchmark, so this is partly a selection artefact. It is mitigated —
  the gate runs on a different random stream (`run_controllability.gate_seed`)
  than Part I, so selection and evaluation are independent draws — but absolute
  rates in the stratum remain optimistic. Paired arm-vs-arm comparisons are
  unaffected.
- **`rank_L`.** L is near-degenerate (87% of candidates ≤ 0.001), so its
  percentile ranks are stored for completeness and carry no information.

### 6. Claim scope

Every Part I conclusion is scoped to the stratum where full-model control
itself steers the collective (7 of 12 episodes). The admissible form is
"*within the stratum where full-model control succeeds*, the method does/does
not match it". `frozen_task.claim_scope` in the data file carries this text so
it travels with the numbers.

## Determinism

Seeds are explicit everywhere: episode seeds are passed on the command line,
rollouts use common random numbers keyed by `rng_seed`, and the
calibration/validation split is by seed order. Re-running any step reproduces
its output byte-for-byte on the same machine and numpy version. Steps 10–11 are
order-independent across shards; `merge` re-orders episodes by the frozen
primary list, not by completion order.

## One-writer rule

`data/` is the source of truth and there is no locking. Do **not** run two
Claude Code sessions (or two shells) against this directory at once: they will
interleave writes with no merge and no conflict marker. Use `git worktree add`
for a parallel session, and commit before handing off.
