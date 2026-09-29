# Stage 6.12C — Oracle Decomposition

Analysis code: `code/analysis_612c.py` (`oracle_decomposition`). All
values are mean confirmatory-stream `ΔJ_conservative`, state-clustered
90% bootstrap CIs (n=10 states, 20,000 resamples).

## Definitions (frozen in `CONFIRMATORY_PROTOCOL.md` before this analysis)

1. **Random/median candidate**: `median_j mean_confirm ΔJ_conservative(j)`
   per state — the typical singleton actuator, no selection.
2. **Kinematic-predicted top (DEPLOYABLE)**: the candidate with the
   highest frozen `C_hat_kin`.
3. **Search-selected best (reproducibility check, NOT deployable
   authority inference)**: `j_best_search = argmax_j mean_search
   ΔJ_conservative(j)`, frozen using ONLY the 4 SEARCH streams, then
   evaluated on the 8 CONFIRMATORY streams.
4. **Forced-future contact oracle (NOT deployable)**:
   `j_contact_oracle(r) = argmax_j C_forced_actual(j,r)`, where
   `C_forced_actual(j,r)` is the realized direct actuator-target contact
   count under candidate j's OWN forced trajectory during the d=8 forcing
   window (`mech_cumulative_contact_edges`, reused unmodified from
   `intervention_612.mechanism_diagnostics` — this quantity was already
   being computed for every K=1 rollout as an audit-only mechanism
   diagnostic; Stage 6.12C's only new contribution here is USING it as an
   oracle-selection criterion, not reimplementing the contact-counting
   logic). This is the genuine upper bound the task brief asked for: it
   uses each candidate's OWN forced future, not the paired no-control
   future that Stage 6.12B's oracle used (a disclosed weakness of that
   prior construction — see `CONTACT_PREDICTOR_ANALYSIS.md`'s
   interpretation section).
5. **Outcome oracle (NOT deployable)**: `j_effect_oracle(r) = argmax_j
   ΔJ_conservative(j,r)` — the maximum achievable singleton causal effect
   in this action class, per stream, averaged into a per-state mean.

## Per-state comparison

| state | random (median) | kinematic-top | search-best | contact-oracle | **effect-oracle** |
|---|---|---|---|---|---|
| s612c_00 | 0.00000 | 0.00000 | -0.00357 | 0.00000 | 0.00527 |
| s612c_01 | -0.00043 | -0.00918 | -0.00580 | -0.00580 | 0.02498 |
| s612c_02 | 0.00231 | 0.00071 | 0.00750 | -0.00362 | **0.11421** |
| s612c_03 | 0.00473 | 0.01472 | 0.00505 | 0.01364 | 0.01472 |
| s612c_04 | 0.00422 | 0.01090 | 0.01090 | 0.00418 | 0.01100 |
| s612c_05 | 0.01486 | 0.00826 | 0.01721 | 0.00895 | 0.01733 |
| s612c_06 | 0.00000 | 0.00012 | 0.00162 | -0.00019 | 0.00263 |
| s612c_07 | 0.00522 | 0.00992 | -0.00823 | -0.00823 | 0.02544 |
| s612c_08 | 0.00070 | -0.00163 | -0.00058 | 0.00242 | 0.00242 |
| s612c_09 | 0.00069 | 0.00021 | 0.00093 | 0.00151 | 0.00438 |

## Summary (state-clustered means, 90% bootstrap CI)

| strategy | mean ΔJ_conservative | 90% CI | vs. random |
|---|---|---|---|
| random (median) | 0.00323 | [0.00122, 0.00570] | — |
| kinematic-predicted top (deployable) | 0.00340 | [-0.00014, 0.00697] | ≈ random (CIs heavily overlap; point estimate barely above) |
| search-selected best (reproducibility) | 0.00250 | [-0.00122, 0.00646] | ≈ random or slightly below |
| forced-future contact oracle (non-deployable) | 0.00128 | [-0.00189, 0.00461] | ≈ random or slightly BELOW |
| **outcome oracle (non-deployable)** | **0.02224** | **[0.00915, 0.04190]** | **~6.9× random, CI clearly separated from every other row** |

Agreement between selection strategies (fraction of 10 states where they
pick the SAME candidate): kinematic-top = contact-oracle in **0/10**
states; kinematic-top = effect-oracle in **1/10**; contact-oracle =
effect-oracle in **1/10**. The strategies are picking essentially
different candidates from each other in the overwhelming majority of
states.

## Interpretation — which of Cases A/B/C/D is supported

Recall the four named endpoints (`CONFIRMATORY_PROTOCOL.md`/task brief):
- **Case A**: kinematic ≈ contact-oracle ≈ outcome-oracle >> random →
  proceed to a contact-aware authority estimator.
- **Case B**: contact-oracle >> random but kinematic ≈ random → improve
  the deployable predictor first.
- **Case C**: outcome-oracle >> random but contact-oracle ≈ random →
  contact is not the operative mechanism.
- **Case D**: outcome-oracle ≈ random → no selective headroom exists;
  don't build an authority learner.

**This data supports Case C, cleanly.** Three separate facts, all from
the same table:

1. **Real, large, state-clustering-robust selective headroom EXISTS**:
   the outcome oracle's mean (0.0222) is ~6.9× the random/median
   candidate's mean (0.0032), and its 90% CI lower bound (0.0092) is
   above every other strategy's CI upper bound. Candidate IDENTITY
   clearly matters a great deal for SOME candidate in SOME state — this
   is not a "no controllability" (Case D) result.
2. **The forced-future contact oracle — a genuine, non-deployable upper
   bound on "found the actuator with the most realized future contact
   opportunity" — does NOT capture this headroom.** Its mean (0.00128) is
   not just "not clearly above random," it is numerically BELOW the
   random/median candidate's mean, with a CI comfortably straddling zero.
   This directly rules out Case A (which requires contact-oracle >>
   random) and Case B (which requires contact-oracle >> random specifically,
   just with kinematic lagging behind it).
3. **The deployable kinematic predictor tracks the (already-weak) contact
   oracle, not the outcome oracle** — both sit at essentially the random
   baseline. This is consistent with `PREDICTOR_VALIDATION.md`'s
   state-clustered-null ρ finding: the predictor is not failing to
   approximate a good contact oracle well; the contact oracle itself is
   not where the outcome headroom lives.

**Conclusion: singleton actuator choice has real, substantial causal
consequence in this system (outcome-oracle result), but that consequence
is NOT explained by, predicted by, or well-approximated via direct
physical contact between actuator and target — neither the deployable
kinematic proxy for future contact nor a genuine forced-future realized-
contact upper bound identifies the actuators that matter.** Whatever
mechanism DOES separate a high-ΔJ_conservative candidate from a low one in
this system remains open — plausibly something like an
indirect/social-field disruption pathway that does not require the
actuator to ever come within the true interaction radius R of the target,
but this stage's data can only rule OUT the contact-based explanation, not
identify the true one.

See `NEXT_STAGE_DECISION.md` for what this implies for the next task.
