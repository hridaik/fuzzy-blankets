# Final Stage 6.11 adjudication, all 5 seeds

Combines: prior-pass identity findings (Step 1/Step 2/Step 2.5, cited),
this pass's episode-level identity validation, exact v2 replay, and
identity-aware schedule-effect causal adjudication
(`seed_{500..504}_causal.md`, `seed_503_disruption_analysis.md`). Every
dimension is reported separately — never collapsed into one "success"
label, per the explicit task instruction that produced the withdrawn
"3/5 successful blind adaptive controls" claim in the first place.

| seed | physical_turn_of_material_target | strict_identity_continuity | intervention_effect | actuator_selectivity | persistence_after_release | organizational_disruption | evidence_status | notes |
|---|---|---|---|---|---|---|---|---|
| **500** | not demonstrated (stays low under all conditions incl. no forcing) | valid throughout | marginal / not clearly demonstrated (paired mean +0.009, 90% CI barely excludes zero) | not demonstrated | not applicable | not evaluated | not demonstrated under tested conditions | reference/sanity case; harness correctly does NOT manufacture a large effect here, unlike 501/503/504 |
| **501** | demonstrated (0.23→0.97 in the real recorded run, persists to release) | valid (self-corrects after a transient t=32–35 v1 detour; actuators stayed physically near the material target throughout) | **demonstrated** (paired mean +0.309, 90% CI [0.162, 0.455], 68% of replicates positive) | not demonstrated (paired mean +0.072, CI crosses zero) | consistent with persistence in the real run (0.97 at release); schedule-effect replicates show wide variance | none observed | demonstrated (turn + intervention effect) / not demonstrated (selectivity) | highest-priority seed; cleanest, best-powered result in the sweep |
| **502** | contradicted (real run: 0.19→0.10; replicates: paired diff ≈0, 50% positive) | v1 permanently diverges at t≈32 (prior passes); material target shows markedly reduced SURVIVAL under forcing this pass (44–52% death vs. 20% unforced) | not demonstrated (paired mean ≈0.03, CI crosses zero) | not demonstrated (point estimate favors random, n too small to confirm) | not applicable (target frequently lost before release) | **demonstrated, as elevated target loss** (not fragmentation like 503, but comparable in kind — control-associated loss of a trackable target) | contradicted (turn) / not demonstrated (effect, selectivity) / unresolved (disruption mechanism, since it manifests as death not split) | v1/v2 anchors agree with each other and both diverge sharply from material anchor — strongest anchor-choice-matters case in the sweep |
| **503** | demonstrated, but NOT in the material-continuing target (0.86 belongs to a 3rd, unrelated population; material daughter itself: 0.05→0.35 real run, paired mean +0.221 replicates) | **likely physical split at t=47** (persistent daughter separation, no re-fusion, not formally "confirmed" — no validated threshold exists) | **demonstrated** for the material-continuing target specifically (paired mean +0.221, CI [0.099, 0.344]) | not demonstrated (paired mean −0.037, CI crosses zero) | noisy (std≈0.35, comparable to mean) | **not demonstrated as intervention-specific** (split rate >50% under ALL conditions incl. no forcing) | demonstrated (turn exists, but not in the qualification-time target) / unresolved (split confirmation) / demonstrated (intervention effect on the correct target) | v2's EXACT anchor independently contradicts v1's high reading (this pass's sharpened finding — not just material trace vs. v1) |
| **504** | not demonstrated under no forcing; **demonstrated as possible, unreliably**, under sustained forcing (bimodal: median 0.07, mean 0.39, p90 0.92) | valid throughout | **demonstrated** (paired mean +0.367, 90% CI [0.235, 0.499], strongest paired signal of the 5 seeds) | not demonstrated (paired mean −0.061, CI crosses zero) | occurs in a minority of replicates (right-skewed distribution) — "short-horizon ≠ persistent" preserved as the TYPICAL case, not the only possible one | none observed (no elevated death rate; 25/25 continuing in all branches) | demonstrated (intervention effect) / not demonstrated (reliable persistence, selectivity) | v2's exact anchor is a striking outlier (high) despite near-total v1/v2 membership agreement — disclosed complication, doesn't overturn "no turn" under no forcing |

## Cross-seed pattern

**A consistent pattern holds across all 5 seeds**: wherever an
intervention effect is demonstrated (501, 503, 504; weakly 500), actuator
selectivity is NOT demonstrated in any of them. The historical top-K-by-
authority actuator selection never distinguishably outperforms
duration/cardinality/cadence/pool-matched random forcing in this sweep.
This is the single most consistent, best-replicated finding across the
whole reconciliation effort (Step 1's original seed-503 duration-vs-
selection finding, now independently reproduced for 3 additional seeds
under a different, materially-scored methodology).

**Disruption manifests differently by seed and is never clearly
intervention-caused**: seed 502 shows elevated target-loss (death), seed
503 shows persistent fragmentation (but at a rate indistinguishable from
the unforced baseline), seeds 500/501/504 show neither. There is no
evidence in this sweep that sustained forcing systematically induces
organizational disruption beyond what these regimes already show
unforced — but the sample sizes (20-25 replicates per seed) are modest,
and this is not proof of safety, only an absence of detected harm under
the tested conditions.

## What changes from the original Stage 6.11 report

The original "3/5 successful blind adaptive controls" (500=no, 501=turn,
502=turn, 503=turn, 504=no) is superseded by the above table on every
axis. Read strictly:
- 500: unchanged (no turn, no effect).
- 501: turn confirmed, identity-valid, intervention effect now positively
  demonstrated (new in this pass) — the strongest surviving case.
- 502: turn CONTRADICTED for the correct target; what v1 reported turning
  is a different population.
- 503: turn CONTRADICTED for the correct target (same structure as 502,
  via a different mechanism — split rather than permanent divergence);
  the correct target does show a smaller, real, intervention-associated
  rise.
- 504: previously "no", now more nuanced — "no" under no forcing, but a
  demonstrated (if unreliable) capacity to turn under sustained forcing,
  not evaluated for persistence-reliability in the original report.

No seed supports the original binary "success" framing once physical
turn, identity, intervention effect, and selectivity are scored
separately. The clearest surviving positive result across the whole
programme is: **sustained exterior forcing can, with reasonable evidence,
increase a materially-identified target's heading alignment (501, 503,
504) — but no tested method demonstrates that WHICH exterior birds are
forced matters, in any seed.**
