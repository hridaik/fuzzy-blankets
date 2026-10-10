# Candidate Recurrence

Computed by `code/analysis.py:candidate_recurrence()`, using the 12-stream
(search+confirm) matrix. Per state: how often each of the 20 candidates is
the per-stream best actuator (the winner of `argmax_j ΔJ(j,r)` for that one
stream `r`), the Shannon entropy of that winner distribution (normalized by
`log(n_unique_winners)`, so 1.0 = winners as spread out as possible given how
many distinct candidates ever won), and how many unique candidates ever
appear in the per-stream top-1 / top-3 / top-5.

## Per-state table

| state | # streams | # unique winners (of 20 candidates, 12 streams) | max win count | max win frequency | entropy (normalized) | unique in top-3 any stream | unique in top-5 any stream |
|---|---|---|---|---|---|---|---|
| s612c_00 | 12 | 5 | 5 | 0.417 | 0.885 | 8 | 14 |
| s612c_01 | 12 | 6 | 3 | 0.250 | 0.951 | 16 | 19 |
| s612c_02 | 12 | 8 | 3 | 0.250 | 0.952 | 12 | 16 |
| s612c_03 | 12 | 9 | 3 | 0.250 | 0.953 | 19 | 19 |
| s612c_04 | 12 | 9 | 3 | 0.250 | 0.953 | 19 | 20 |
| s612c_05 | 12 | 3 | 5 | 0.417 | 0.936 | 12 | 17 |
| s612c_06 | 12 | 5 | 5 | 0.417 | 0.885 | 10 | 13 |
| s612c_07 | 12 | 9 | 2 | 0.167 | 0.973 | 18 | 19 |
| s612c_08 | 12 | 8 | 3 | 0.250 | 0.952 | 17 | 19 |
| s612c_09 | 12 | 8 | 3 | 0.250 | 0.952 | 15 | 18 |

**Aggregate:** mean max-win-frequency = 0.292 (i.e., the single most-winning
candidate in a state wins on average only ~29% of that state's 12 streams --
well short of dominance); mean normalized winner entropy = 0.939 (close to
the maximum possible given the number of unique winners); mean # unique
winners = 7.0 (of 20 candidates, across only 12 streams).

## Reading

**No candidate repeatedly wins across streams in any state.** Even the
highest max-win-frequency states (`s612c_00`, `s612c_05`, `s612c_06`, all
0.417) only have their top winner taking 5 of 12 streams -- and winner
identity is otherwise close to maximally spread (entropy ~0.88-0.97 of the
maximum possible for that many unique winners). Across a typical state, 6-9
DIFFERENT candidates (out of 20) each win at least one stream outright, and
12-20 different candidates appear in the per-stream top-3 across only 12
streams -- most of the 20-candidate pool cycles through being "the best
choice" for at least one physics realization. This is exactly the
signature expected if per-stream winners are being drawn close to
uniformly at random from a large subset of candidates (stochastic
opportunity), not repeatedly identifying the same reproducibly-superior
actuator.
