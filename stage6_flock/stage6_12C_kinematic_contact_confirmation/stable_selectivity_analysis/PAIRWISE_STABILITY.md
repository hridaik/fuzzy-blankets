# Pairwise Ranking Stability

Computed by `code/analysis.py:pairwise_stability()`. For every candidate
pair `(j,k)` within a state (190 pairs per state, `C(20,2)`), `P(ΔJ_j >
ΔJ_k)` across the 12 streams. A pair is called "stable" if
`max(P, 1-P) > 0.8` (i.e., one candidate beats the other in >80% of shared
streams).

## Per-state summary

| state | # pairs stable (>0.8) | frac stable | global-best-mean candidate beats pooled frac |
|---|---|---|---|
| s612c_00 | 103/190 | **0.542** (see caveat below) | 0.408 |
| s612c_01 | 36/190 | 0.189 | 0.425 |
| s612c_02 | 16/190 | 0.084 | 0.600 |
| s612c_03 | 16/190 | 0.084 | 0.492 |
| s612c_04 | 6/190 | 0.032 | 0.575 |
| s612c_05 | 105/190 | **0.553** (see caveat below) | 0.271 |
| s612c_06 | 72/190 | **0.379** (see caveat below) | 0.425 |
| s612c_07 | 8/190 | 0.042 | 0.542 |
| s612c_08 | 36/190 | 0.189 | 0.558 |
| s612c_09 | 22/190 | 0.116 | 0.588 |

**Aggregate:** mean fraction of stable pairs = 0.221; mean fraction of the
time the global best-mean candidate actually beats a randomly chosen
competitor pooled across streams = 0.488 -- statistically indistinguishable
from a coin flip (0.5).

## A caveat that materially changes the reading of the three highest "stable fraction" states

`s612c_00`, `s612c_05`, and `s612c_06` are exactly the three lowest-headroom
states in this sample (random/median ΔJ_conservative at or near 0.0 --
`STATE_TAXONOMY.md`). In `s612c_00` specifically, **77% of all 240
candidate x stream cells are exactly `ΔJ_conservative = 0.0`** (checked
directly against the raw data). When most values tie at exactly zero,
`P(ΔJ_j > ΔJ_k)` collapses toward 0 or 1 mechanically for any pair where one
side has any nonzero (even tiny) values and the other is all zero -- this
inflates the "stable ordering" count WITHOUT reflecting a real, consequential,
reproducible advantage (the pair is "stably ordered" in the sense that one
side is stably doing literally nothing while the other occasionally does
something arbitrarily small). **The pairwise-stability statistic should NOT
be read as "these three states show the strongest actuator selectivity"** --
if anything they are the states where the outcome surface is flattest and
least informative, and the apparent pairwise stability is a floor-effect
artifact, not evidence of leverage.

## Reading (the more informative half of the states)

In the 7 states without this degenerate floor effect (`s612c_01` through
`s612c_04`, `s612c_07` through `s612c_09`), the fraction of stably-ordered
pairs is consistently LOW (0.032-0.19, mean ~0.11), and the global best-mean
candidate beats a random other candidate on a pooled comparison only
42-60% of the time -- essentially chance. This is fully consistent with
`VARIANCE_DECOMPOSITION.md` and `RANK_RELIABILITY.md`: outside a few
degenerate near-zero-effect states, actuator pairs are not reliably
ordered relative to one another across physics streams.
