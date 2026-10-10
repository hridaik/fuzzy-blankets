# Seed 503 disruption analysis (Task F2)

Method identical to `seed_501_causal.md`'s schedule-effect harness (see
that document and `RNG_AND_CRN_AUDIT.md` for full CRN justification) —
`code/seed503_schedule_effect.py`. Trigger t0=35 (bit-exact reproducible,
`RNG_AND_CRN_AUDIT.md` §4), target_heading=2, 47 simulated steps (t=35
through t=82, matching the historical episode's final_t). 25 replicates
requested; 20–25 completed with a valid alignment reading per branch
(varies by branch — `dead` traces yield no reading, reported as `n`, never
imputed).

Historical actuator schedule (from `data/online_control_611__seed503.json`):

| refresh t | actuator set |
|---|---|
| 35 | `[8, 9, 39, 46, 54, 81, 93, 107]` |
| 44 | `[290, 66, 79, 222, 297, 330, 384, 287]` |
| 53 | `[46, 50, 152, 190, 225, 232, 267, 273]` |

Note: the t=44 refresh (a completely different actuator-ID set from the
first) happens 3 steps BEFORE the t=46→47 split event already
characterized in `SPLIT_MERGE_SEMANTICS.md`/`seed_503_split_forensics.md`
— it was selected using v1's own state shortly after the t=43 merge-shaped
event, before the t=47 split.

## Alignment outcome

| branch | n | mean end-of-release | median | std | split rate | mean first-split t | died |
|---|---|---|---|---|---|---|---|
| no_forcing | 23 | 0.089 | 0.051 | 0.087 | 56% (14/25) | 17.4 | 8% |
| historical_schedule | 21 | 0.341 | 0.135 | 0.347 | 52% (13/25) | 17.8 | 16% |
| matched_random | 24 | 0.384 | 0.171 | 0.377 | 68% (17/25) | 21.5 | 4% |

### Paired differences (within-replicate, CRN)

| comparison | n | mean diff | std | 90% CI | fraction positive |
|---|---|---|---|---|---|
| historical − no_forcing (alignment) | 20 | **+0.221** | 0.332 | [0.099, 0.344] | 70% |
| historical − matched_random (alignment) | 20 | −0.037 | 0.566 | [−0.245, 0.172] | 40% |
| historical − no_forcing (split occurred: −1/0/+1) | 25 | −0.04 | 0.599 | [−0.237, 0.157] | — |
| historical − matched_random (split occurred: −1/0/+1) | 25 | −0.16 | 0.612 | [−0.361, 0.041] | — |

## Answering the task's exact questions

**Does intervention (sustained forcing) increase the material-continuing
target's alignment relative to no forcing?** **Yes** — same pattern as
seed 501: paired mean +0.221, 90% CI entirely positive, 70% of replicates
favor the historical schedule.

**Does the historical actuator choice outperform matched random?** **Not
demonstrated** — paired mean −0.037, CI straddles zero, 40% positive (if
anything, slightly favoring random, but not distinguishably).

**Did the historical intervention change the probability or timing of a
split event, relative to no forcing?** **Not demonstrated** — split
occurrence is close across all three conditions (56% no-forcing, 52%
historical, 68% matched-random); the paired historical-vs-no-forcing
difference is centered near zero (mean −0.04, CI crosses zero both
directions). **This pass finds no evidence that the historical
intervention schedule specifically increased fragmentation risk relative
to leaving the flock unforced.** If anything, the matched-random
comparator shows a somewhat HIGHER split rate and a LATER mean first-split
time, but neither comparison reaches a distinguishable signal at n≈20–25
replicates.

**Did forcing retask the target, or did it make the target fragment?**
Based on this pass's repeated-stochastic-replicate evidence (distinct
from the single ACTUAL recorded trajectory, where a split did occur at
t=47 — see below): **forcing is associated with higher alignment
(retasking-consistent) without a detectably elevated fragmentation rate**
— i.e., this pass does not find evidence that intervention causes
disruption more often than the flock's own unforced dynamics already do
(56% baseline split rate is itself substantial — this is evidently a
regime where fragmentation is common regardless of forcing).

## Reconciling with the single recorded historical trajectory

This is a genuinely separate finding from `seed_503_split_forensics.md`'s
single-trajectory result (the actual recorded seed-503 episode: a split
DID occur at t=47, and the population reaching v1's reported 0.86 is not a
material descendant of the target past that point). That is one
realization; this document's schedule-effect harness runs the SAME
schedule/no-forcing/random comparisons across 20–25 independent physics
noise realizations from the identical trigger state, and finds split
events are common (>50%) under ALL THREE conditions including no forcing
— i.e. **the real run's t=47 split is consistent with this being a
generically fragile/fragmenting regime for this flock, not necessarily a
consequence of the specific historical forcing choice.** Both findings
are preserved, not collapsed into one: the real run genuinely split with
an unrelated population reaching the reported large alignment (established
fact); whether THAT specific split was caused by the intervention, versus
being a generic feature of this seed's dynamics, is **not established
either way** by the evidence in this pass — the schedule-effect
distribution is symmetric-ish across conditions, which argues against
(but does not rule out) intervention-specific causation of that one event.

## Fields (task §14/§18 style)

| dimension | evidence status |
|---|---|
| physical_turn_of_material_target | contradicted for the QUALIFICATION-TIME target specifically (the large 0.86 turn belongs to an unrelated population past t=47, prior passes); a real but modest rise (schedule-effect mean 0.34, single-trajectory 0.05→0.35) occurs in the actual material-continuing daughter |
| strict_identity_continuity | likely_physical_split at t=47 in the real recorded trajectory (prior pass); unresolved at "confirmed" strictness |
| intervention_effect | demonstrated for the material-continuing target's alignment (this pass, schedule-effect) |
| actuator_selectivity | not demonstrated under tested conditions (this pass) |
| persistence_after_release | schedule-effect end-of-release readings are noisy (std ≈ 0.35, comparable to the mean) — not strongly established either way |
| organizational_disruption | **not demonstrated as intervention-specific** — split rate is high (>50%) under no forcing too; this pass does not find intervention elevates it |
