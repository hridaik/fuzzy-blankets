# Stage 6.12 — Selectivity Analysis (Phase B search + Phase C held-out confirmation)

## Frozen primary search budget

`K=4, d=8` — chosen before any Stage 6.12 intervention result existed (see
`run_phaseBC_612.py`'s module docstring), applied identically to all 9
states (development and holdout).

- **Phase B (search)**: 15 sampled `K=4` subsets of the 20-bird pool,
  evaluated on `N_SEARCH_STREAMS=2` development-only physics streams;
  argmax mean `J` becomes `S_star`, frozen.
- **Phase C (confirmation)**: `S_star` and `N_HOLDOUT_COMPARATORS=6` fresh
  random `K=4` sets, evaluated on `N_HOLDOUT_STREAMS=5` physics streams
  from a seed range never touched during search (`RNG_PROTOCOL.md`).

## Between-set variance (Phase A, all budgets — DEVELOPMENT-observable evidence)

Per `READINESS_MAP.md`, between-set variance at `K4_d8` specifically is one
of the *smallest* in the whole grid (mean 0.00035, vs. up to 0.022 at
`K8_d1`) — i.e. the frozen primary search budget was NOT selected because
Phase A flagged it as promising (it wasn't chosen from Phase A at all — see
above), and it happens to sit in a low-between-set-variance region of the
grid. This is disclosed, not hidden: a budget chosen for its position in
the grid (a defensible mid-range choice) rather than for its apparent
Phase-A selectivity signal is a conservative test of whether selectivity
exists, not one stacked in favor of finding it.

## Held-out result: `G_sel = mean_holdout[J(S_star)] - median_random_holdout[J(S)]`

| state | role | G_sel | S*_holdout mean J | random holdout median-of-means | no-control holdout mean J | S* identity-valid frac |
|---|---|---|---|---|---|---|
| s612_00 | dev | **+0.0256** | 0.141 | 0.115 | 0.131 | 1.00 |
| s612_01 | dev | +0.0070 | 0.074 | 0.067 | 0.077 | 1.00 |
| s612_02 | dev | +0.0931 | 0.581 | 0.488 | 0.551 | 1.00 |
| s612_03 | dev | +0.0004 | 0.307 | 0.306 | 0.200 | 1.00 |
| s612_04 | dev | +0.0070 | 0.086 | 0.079 | 0.062 | 1.00 |
| s612_05 | dev | **-0.1064** | 0.104 | 0.210 | 0.242 | 1.00 |
| s612_06 | holdout | +0.0015 | 0.047 | 0.046 | 0.048 | 1.00 |
| s612_07 | holdout | -0.0169 | 0.056 | 0.073 | 0.072 | 1.00 |
| s612_08 | holdout | +0.0185 | 0.053 | 0.034 | 0.049 | 1.00 |

**Development**: n=6, mean `G_sel`=+0.0045, median=+0.0070, 5/6 (83%)
positive. **Holdout**: n=3, mean=+0.0010, median=+0.0015, 2/3 (67%)
positive.

## Interpretation

At the frozen `K=4, d=8` budget, `G_sel` is **small in magnitude
everywhere it is positive** (typically +0.001 to +0.03, i.e. a few
percentage points of alignment) and is **occasionally clearly negative**
(`s612_05`: -0.106, `s612_07`: -0.017) — including one development state
where the development-selected `S_star` performed markedly WORSE than the
random-set median on fresh holdout streams for that SAME state (`s612_05`:
Phase B picked a set that scored well on its 2 search streams but
underperforms by 0.106 on 5 fresh streams; a textbook post-selection
regression-to-the-mean case, exactly the failure mode the task brief's own
"a best set evaluated on the same rollouts used to find it is NOT
acceptable evidence" warning names). Genuinely held-out states (`s612_06`,
`s612_07`, `s612_08`) show the same pattern at smaller scale: one small
positive, one negative, one small positive — **no reproducible,
directionally-consistent selectivity signal survives held-out
confirmation** at this budget, sample size, and Monte Carlo precision.

Every `S_star` remained strictly identity-valid on every holdout stream
(identity-valid fraction 1.00 throughout) — so failures/successes above are
about behavioral alignment, not identity loss (see
`IDENTITY_AND_DISRUPTION.md`).

## Honest limitation

`N_SEARCH_STREAMS=2` and `N_HOLDOUT_STREAMS=5` are far below the task
brief's nominal ≥24 holdout confirmation streams; with this few replicates,
a true small selectivity effect (say `G_sel≈0.03`, comparable to the
largest positive holdout value observed) would not reliably separate from
noise. **This analysis cannot rule out a real but small selectivity effect
at K=4,d=8** — it can only report that, at the precision actually achieved,
no such effect reproducibly survived the development→holdout split, and
one state showed the opposite (a "successful-looking" development result
that reversed on holdout), which is itself informative: it demonstrates
concretely why development-only "best-found" numbers are not acceptable
evidence on their own, reproducing (at smaller scale, with genuinely fresh
states) the same qualitative finding Stage 6.11 reported for the historical
actuator choice.

See `FINAL_STAGE612_FINDINGS.md` Q2–Q4 and Q8 for how this feeds the
overall endpoint call.
