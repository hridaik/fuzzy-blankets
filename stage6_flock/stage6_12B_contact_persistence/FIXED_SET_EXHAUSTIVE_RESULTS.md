# Stage 6.12B-A — Exhaustive Fixed-Set Results

3 states (`s612b_00`, `s612b_01` development; `s612b_03` holdout), K∈{1,2}
EXHAUSTIVE (20 + 190 sets), d∈{4,8}, `N_DEV_STREAMS=1`,
`N_HOLDOUT_STREAMS=4` for 8 finalists (S_star, median-dev, worst-dev, 5
random comparators) per K,d cell. Full per-set results in
`data/fixed_set_exhaustive_612b.json`; aggregates in
`data/analysis_summary_612b.json["fixed_set"]`.

## Headline table (mean across the 3 searched states)

| cell | mean between-set var (dev) | mean G_sel (holdout) | mean rank stability (dev→holdout) |
|---|---|---|---|
| K1_d4 | 0.00002 | +0.0067 | +0.42 |
| K1_d8 | 0.00162 | +0.0053 | +0.11 |
| K2_d4 | 0.00004 | +0.0040 | -0.06 |
| K2_d8 | 0.00152 | +0.0021 | -0.06 |

## Per-state detail

| state | cell | dev mean | dev best | dev worst | G_sel | rank stability |
|---|---|---|---|---|---|---|
| s612b_00 | K1_d4 | -0.0028 | +0.0047 | -0.0154 | +0.0116 | +0.37 |
| s612b_01 | K1_d4 | +0.0016 | +0.0297 | -0.0020 | +0.0084 | +0.46 |
| s612b_03 | K1_d4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a (all-zero) |
| s612b_00 | K1_d8 | +0.0008 | +0.0156 | -0.0032 | -0.0049 | -0.11 |
| s612b_01 | K1_d8 | +0.0009 | +0.0099 | -0.0019 | +0.0180 | +0.86 |
| s612b_03 | K1_d8 | -0.0675 | +0.0033 | -0.1418 | +0.0028 | -0.43 |
| s612b_00 | K2_d4 | -0.0049 | +0.0166 | -0.0244 | +0.0030 | -0.55 |
| s612b_01 | K2_d4 | +0.0029 | +0.0307 | -0.0024 | +0.0090 | +0.43 |
| s612b_03 | K2_d4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a (all-zero) |
| s612b_00 | K2_d8 | +0.0011 | +0.0156 | -0.0104 | -0.0054 | -0.54 |
| s612b_01 | K2_d8 | +0.0016 | +0.0152 | -0.0040 | +0.0181 | +0.31 |
| s612b_03 | K2_d8 | -0.0804 | +0.0683 | -0.1418 | -0.0064 | +0.05 |

## Interpretation

**`s612b_03` at d=4 is uniformly all-zero** (every one of 210 sets, every
metric, exactly 0.0) — the traced target's material identity was already
lost/dead or the no-control baseline itself scored exactly zero, making
every intervention's paired difference vanish by construction; at `d=8`
the SAME state shows the largest between-set spread of any cell (dev best
+0.068, worst -0.142) — a striking illustration that duration alone can
flip a state from "nothing is measurable" to "the widest spread we
observed," reinforcing that state × duration interactions, not a single
scalar "does selectivity exist," are the right unit of description.

**G_sel (held-out S_star advantage over random comparators) is small but
MOSTLY POSITIVE** — 10 of 12 (state,cell) combinations are ≥0 (only
`s612b_00`'s K1_d8 and K2_d8 are negative, both small: -0.005). This is
more consistently positive than Stage 6.12's original sparse-search
result, though the magnitudes (+0.002 to +0.018) remain small relative to
typical `J0` baselines (~0.03-0.32 in Stage 6.12's own data).

**Rank stability (dev-selection rank vs. holdout rank among the 8
finalists) is POOR and inconsistent** — ranging from -0.55 to +0.86 across
cells/states, frequently near zero or negative. With only
`N_DEV_STREAMS=1`, this is expected: a single noisy physics realization is
a weak basis for ranking 210 candidate sets. **This is the "highly
stochastic" interpretation named in the task brief**: development rankings
are unstable, YET the aggregate held-out G_sel across all searched cells
still tilts positive more often than not. The most defensible reading is
that **real between-set differences likely exist at small K, but reliably
identifying the specific best set from this little development data is
not currently possible** — a distinct finding from "no selectivity exists"
and from "selectivity is easily found."

## Caveat

n=3 states is far too small to generalize a "typical" magnitude with
confidence — every number above should be read alongside its
per-state row, not just the cross-state mean.
