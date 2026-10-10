# Final adjudication — seeds 501 and 503 only (scope note in README.md)

This is **not** the full spec §13.12 table (5 seeds × 8 columns). Per the
user's explicit prioritization for this pass ("prioritize the scientific
headline first"), only seeds 501 and 503 are addressed, and only on the
dimensions this pass's own evidence (Task A hardening + Task B split
forensics, built on Step 1/Step 2's existing work) actually speaks to.
**Intervention effect, actuator selectivity, and persistence-after-release
are NOT evaluated here** — those require Task F's paired counterfactual
comparisons (no-forcing / matched-random / schedule-replay from saved
trigger states with verified stochastic provenance), which this pass did
not run. Marking them anything other than "not evaluated in this pass"
would misrepresent what was actually done.

| dimension | seed 501 | seed 503 |
|---|---|---|
| **physical_turn** | demonstrated (materially-continuing target: 0.23→0.97, persists to release) | demonstrated, but **not in the material-continuing target** — a large turn (→0.86) occurs in a population confirmed to share zero material with the qualification-time cohort past t=47 |
| **strict_identity_continuity** | valid throughout, after a self-correcting 4-step v1-vs-material disagreement (t=32–35) that does not affect the material trace's own continuity | **likely physical split at t=47** (this pass's Task B finding); downstream strict continuity from t=47 onward is unresolved, not preserved and not automatically terminated |
| **intervention_effect** | not evaluated in this pass (Task F not run) | not evaluated in this pass (Task F not run) |
| **actuator_selectivity** | not evaluated in this pass | not evaluated in this pass |
| **persistence_after_release** | material-continuing target's alignment is stable at 0.97 through release (t=76) — a real-run observational fact, not yet attributed to any tested intervention | material-continuing daughter's alignment (0.35 peak) never approaches a dominant value; whether this reflects release or ongoing dynamics is not analyzed here |
| **organizational_disruption** | none observed — no split/merge event coincides with the turn | **yes** — the t=47 fragmentation event (this pass's Task B finding) is temporally coincident with, and a plausible alternative explanation for, part of what the historical record described as "the seed 503 turn" |
| **evidence_status** | demonstrated (physical turn, identity-valid) / not evaluated (causal) | demonstrated (a physical turn occurs SOMEWHERE) / contradicted (that turn is NOT demonstrated to belong to the qualification-time flock) / unresolved (split confirmation) / not evaluated (causal) |

## Seed 501 — what changed and what did not

Nothing in this pass's Task A/B work re-examines seed 501's own
trajectory directly (Task B's daughter-forensics extension was seed-503-
specific, since 501 has no split event of comparable magnitude — Step 2
already reports 2 split flags for 501 but no permanent divergence). What
this pass adds is **confidence calibration**: Task A shows the frozen
identity rule that established seed 501's real-run material continuity
has a small (~0.03–0.04% non-subset), but non-zero, same-world false-
accept rate, stable across an already-seen and a genuinely untouched
natural holdout. This does not overturn seed 501's "physical turn,
identity-valid" verdict; it quantifies, for the first time, how much
residual risk that verdict carries from the identity rule itself (as
opposed to residual risk from the intervention-effect question, which
remains completely open, per Task F not being run).

## Seed 503 — what changed and what did not

Step 2 already established that v1's reported 0.86 turn belongs to a
population materially disjoint from the qualification-time flock past
t=47. This pass's addition is the **daughter-level forward forensics**
(`seed_503_split_forensics.md`) that upgrades the event from "the material
trace diverges from v1, following one fragment" to a specific, evidenced
characterization: **the ORIGINAL flock itself fragments into two material
daughters, one of which loses detectable coherence within 3 steps**, and
neither daughter is the population that shows the large reported turn.
This sharpens seed 503's interpretation from "unresolved target identity"
(the framing the original task brief flagged as acceptable, spec §4.3's
epigraph) toward the more specific "likely physical split with
organizational disruption," while explicitly declining to call it
"confirmed" absent a validated threshold.

## What would be needed to complete the standard §13.12 table

See `NEXT_STEP_RECOMMENDATIONS.md`.
