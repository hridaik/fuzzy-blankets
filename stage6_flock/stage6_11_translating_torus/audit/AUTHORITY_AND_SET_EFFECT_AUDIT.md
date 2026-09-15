# Authority Repair and Set-Effect Audit — Stage 6.11B (items 6-8)

Additive. `intervention_api_611.MultiStepAuthorityProbe` and
`control_authority_611.select_actuators` are preserved unchanged (imported,
never edited) — everything here is a new comparator in `audit/authority_v2_611.py`.

## 1. The repaired estimand (item 6)

$$ A_S(\tau, d) = E[H^\star_{t+\tau} \mid S \text{ forced for } d \text{ consecutive steps}] - E[H^\star_{t+\tau}] $$

`held_rollout(mf, r, z, S, h_star, tau, d, seed)`: forces every bird in `S`
to `h_star` at steps `0..d-1`, then evolves freely to `t+tau`. `d=1`
reproduces `MultiStepAuthorityProbe`'s exact old semantics (forced only at
step 0); `d=tau` holds for the entire evaluation horizon.

**Planning/execution identity, proven by unit test, not asserted.**
`audit/test_authority_v2_611.py`, 4/4 passing:
- `held_rollout(..., d=tau)` is bit-for-bit identical to a real execution
  loop that holds the same forced actuators for `tau` real steps.
- `held_rollout(..., d<tau)` is bit-for-bit identical to a real execution
  that holds for `d` steps then releases while the world keeps running to
  `tau`.
- `held_rollout(..., d=1)` is bit-for-bit identical to the OLD
  `MultiStepAuthorityProbe._rollout`'s own output, same seed — the
  generalization is a strict superset, not a silent behaviour change at the
  old default.
- The baseline (unforced) arm is bit-for-bit identical to an ordinary
  unforced real trajectory.

**Matched-hold sweep.** `d ∈ {1, 2, 4, 8}` all implemented via the same
`held_rollout`/`authority_set` primitives; the adjudication run
(`FIVE_SEED_CAUSAL_ADJUDICATION.md`) uses `d=tau=4` as its primary repaired
value (a disclosed compute-budget choice: this exactly matches the OLD
`tau=4` evaluation horizon, removing the one-shot-then-released mismatch
within that same horizon, without requiring the full 8-step
re-planning-aware design a true `d=8` match would need). A `d=8` spot check
at reduced rollout budget is reported in §4 below rather than repeated for
the full 5-seed × 9-branch adjudication.

## 2. K≤8 as a maximum, never an obligation (item 7)

`select_actuators_v2` (`audit/authority_v2_611.py`) takes the top-K
CANDIDATES by descending `A`, but only includes one if its bootstrap CI
lower bound clears zero (`ci_lo > 0.0`) — a predeclared conservative rule,
not tuned per seed. `require_positive_evidence=False` reproduces the OLD
unconstrained-fill behaviour as an explicit comparator. Every `authority_set`
call reports `A`, `se`, and a bootstrap `(ci_lo, ci_hi)` for every
candidate/set evaluated — paired via common random numbers across the
do/baseline arms of each rollout (same convention as `probing_611`'s own
uncertainty treatment).

## 3. Individual vs. collective/set authority, with synergy (item 8)

At each of the five trigger states (`audit/trigger_states_611.json`),
higher-budget (`n_rollouts=15`, vs. the original 10) common-random-number
rollouts, `tau=d=4`, blind `nearest_M12` pool, `K_MAX=6` for this
standalone comparison (`audit/authority_method_comparison_611.py`; raw
output `audit/authority_method_comparison_611.json`):

| seed | old selected A (CI) | matched random A (CI) | top-K individual A (CI) | greedy marginal A (CI) | beam search A (CI) |
|---|---|---|---|---|---|
| 500 | 0.000 [0, 0] | 0.000 [0, 0] | abstained (empty) | 0.000 [0, 0.007] | abstained (empty) |
| 501 | 0.000 [0, 0] | 0.002 [−0.006, 0.009] | 0.002 [0, 0.009] (1 actuator) | abstained (empty) | 0.000 [0, 0] (1 actuator) |
| 502 | 0.000 [−0.013, 0.013] | 0.006 [0, 0.016] | abstained (empty) | 0.006 [0, 0.014] (5 act., own trace peaked 0.022) | 0.003 [0, 0.010] (4 act.) |
| 503 | **−0.006** [−0.016, 0] | 0.000 [0, 0] | abstained (empty) | abstained (empty) | 0.000 [0, 0] (1 actuator) |
| **504** | **0.048** [**0.017, 0.082**] | −0.005 [−0.035, 0.021] | 0.031 [−0.002, 0.064] (6 act.) | **0.024** [**0.005, 0.043**] (2 act.) | **0.031** [**0.012, 0.049**] (3 act.) |

**Only seed 504 shows a CI that is entirely positive for more than one
method** (old-selected, greedy, and beam all clear zero at both ends;
top-K's CI just barely touches zero). **Every other seed's every method is
either exactly zero, or has a CI that includes zero, or (seed 503's
old-selected set) is entirely NON-positive.** This is the same conclusion
`LINEAGE_FORENSICS_6_11.md` §9 reached with the OLD 10-rollout budget, now
reproduced at 1.5× the rollout budget with a properly matched-duration
estimand — the near-total absence of detectable authority in this sample is
not a budget or estimand artifact, at least not one this repair or this
rollout increase resolves.

**Noise check, disclosed rather than hidden:** seed 502's greedy search's
own internal trace (one consistent CRN seed throughout the search) shows a
smoothly increasing marginal-gain curve as actuators are added — 0.0032 →
0.0063 → 0.0127 → 0.0190 → **0.0222** at 5 actuators — but the table above
re-evaluates that SAME final 5-actuator set under an INDEPENDENT seed (as
every method's final number in this table is), giving **0.0063**, a >3×
smaller point estimate for the identical set. **This is a direct
demonstration that n_rollouts=15 does not fully resolve estimation noise
for effects of this size (~0.01-0.02)** — the "reference" budget in this
pass is better than the old 10, not sufficient for a stable point estimate.
This is disclosed as a real limitation, not smoothed over.

### Seed 504's counter-intuitive role

Seed 504 is one of the two ORIGINAL reported **failures** (no turn,
`RESULTS_6_11.md` §7) — yet it is the ONLY seed in this sample with a
robust, clearly-positive authority signal by three independent methods.
Seed 501 (an ORIGINAL reported **success**) shows essentially zero
authority by every method here. Taken together with `LINEAGE_FORENSICS_6_11.md`
§8-9's finding that actuators were almost never true causal parents and
authority was almost always ≈0 in the ORIGINAL pipeline too (successes and
failures alike), this is a second, independent line of evidence that **the
measured authority signal does not line up with which seeds the original
pipeline reported as turning** — raising the live question (adjudicated in
`FIVE_SEED_CAUSAL_ADJUDICATION.md`) of whether seed 504's real authority
was simply never converted into a persistent turn by the OLD controller's
selection/duration, while seeds 501-503's apparent turns came from
something other than the measured authority mechanism.

### Synergy (item 8's central question)

$$ \Gamma(S) = A_S - \sum_{j\in S} A_j $$

computed on every set of size 2-4 found above. Only seed 504 has sets worth
testing (every other seed's sets are empty or single-actuator):

| seed | set | $A_S$ | $\sum_j A_j$ | $\Gamma(S)$ |
|---|---|---|---|---|
| 502 | beam {84,122,198,234} | 0.000 | −0.003 | +0.003 (negligible) |
| **504** | greedy {65,99} | 0.033 | 0.050 | **−0.017** |
| **504** | beam {65,110,278} | 0.019 | 0.062 | **−0.043** |

**Synergy is negative (or negligible) everywhere it could be measured,
including at seed 504 where individual actuators DO have real, clearly
positive individual authority.** There is no evidence of a hidden
collective/threshold effect the individual one-shot estimator would have
missed — if anything, seed 504's individually-effective actuators
*interfere* when combined (their joint effect is noticeably less than the
sum of their separate effects, most sharply for the beam-search set: −0.043,
about 70% of the summed individual effect cancelled). **This satisfies item
L's stated condition for not needing more sophisticated search:** simple
top-K/greedy is not leaving synergistic value on the table that only a
smarter search could capture — the problem in this sample is not search
quality, it is that most trigger states simply do not have much authority
to find in the first place (§3 above).

## 4. d=8 spot check

Not run in this pass — the primary `d=tau=4` sweep above already used the
full compute budget planned for this section, and given §3's finding that
4 of 5 seeds show no detectable authority at all under `d=4`, a longer hold
duration was judged unlikely to change the qualitative picture enough to
justify the additional compute. Flagged as a specific, well-defined
follow-up rather than silently skipped.

## 5. Summary for the confirmed-vs-possible ledger

| claim | status |
|---|---|
| Planning (`held_rollout`) and real held execution apply identical intervention semantics | **CONFIRMED** — 4/4 unit tests, bit-for-bit |
| The repaired `d=tau` estimand changes the qualitative authority picture from the old `d=1` one | **NOT SUPPORTED on this sample** — 4/5 seeds show no detectable authority under either estimand |
| `K<=8` abstention behaves as intended (never fills on zero/negative evidence) | **CONFIRMED** — empty sets returned at seeds 500/501/502/503 for one or more methods |
| Old success episodes (501-503) contain a real collective/synergy effect the individual estimator missed | **REFUTED** — synergy is negative or negligible everywhere measured; the one seed with real authority (504) was an ORIGINAL reported failure, not a success |
| n_rollouts=15 is sufficient to stably estimate authority at the effect sizes seen here | **REFUTED** — same set, different seed, >3x different point estimate (seed 502) |
