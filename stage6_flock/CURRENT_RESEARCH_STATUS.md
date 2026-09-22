# Stage 6.11 Flock Control: Current Research Status

**Date**: 2026-09-22
**Git commit**: `940a5f672bc9b8302c0436e5a531cea6ae1f6ce1`

## Purpose of this file

No authoritative top-level "Research Programme Handoff" document exists
in this repository (checked by search; this is stated, not invented).
This file is a repository-level status summary so a fresh agent or
researcher does not need hidden prior-conversation context to know what
is established, what is provisional, what is withdrawn, and what the next
task may assume. It is **not** a historical rewrite — every claim below
cites the audit directory that established it, and none of those
directories were modified to produce this file.

## Supporting audit directories, in order

1. `stage6_flock/stage6_11_translating_torus/audit/evidence_recovery_20260921/`
   — forensic recovery of what the original Stage 6.11 implementation
   actually did; withdrew the "3/5 successful blind adaptive controls"
   claim.
2. `stage6_flock/stage6_11_translating_torus/audit/material_identity_step2_20260921/`
   — built and calibrated `ForwardMaterialTrace611`, a simple
   material-overlap identity tracker, independently of the control seeds;
   re-adjudicated seeds 500–504 with it.
3. `stage6_flock/stage6_11_translating_torus/audit/identity_causal_reconciliation_20260921/`
   — hardened identity validation against same-world hard negatives;
   seed-503 split forensics; partial seed 501/503 adjudication.
4. `stage6_flock/stage6_11_translating_torus/audit/causal_reconciliation_step3_20260922/`
   — this pass: completed episode-level identity validation, an RNG/CRN
   audit, exact v2 replay, and identity-aware causal (schedule-effect)
   adjudication for all 5 seeds.

## Established findings

- **The original "3/5 successful blind adaptive controls" claim is
  WITHDRAWN.** (evidence_recovery_20260921; reaffirmed by every
  subsequent pass.) At least one reported "success" (seed 503) is now
  established to describe a population that is not materially descended
  from the flock selected and actuated at qualification.
- **v1 (`LineageTracker611`) can and does jump to unrelated, zero-
  material-overlap populations**, via a global-MAP-over-branching-
  histories mechanism with no margin/confidence gate. Confirmed at
  bird-ID resolution for seed 503 t=46→47 and (differently) for seed
  500's early uncontrolled phase. This is a real, structural tracker
  defect, not the primary subject of intervention analysis.
- **A frozen, simple material-association rule
  (`ForwardMaterialTrace611`, Jaccard≥0.30) exists**, calibrated on
  uncontrolled natural data independent of the control seeds, and
  hardened against same-world hard negatives (not just cross-episode
  ones). Across 72 full-episode sequential traces on natural data (36
  already-used-for-calibration + 36 genuinely untouched holdout), **zero
  erroneous transfers to unrelated populations were observed**
  (`causal_reconciliation_step3_20260922/IDENTITY_EPISODE_VALIDATION.md`).
  A small (~0.03–0.04%) non-subset same-frame false-accept risk exists at
  the pairwise level but did not manifest in any sequential trace tested.
  **This is a material ASSOCIATION layer, not a complete strict-identity
  decision** — split/merge/genealogy semantics sit above it.
- **Physical turn, identity continuity, intervention effect, and
  actuator selectivity are four separate questions**, and collapsing them
  produced the withdrawn claim. They are now tracked separately for every
  seed (`causal_reconciliation_step3_20260922/FINAL_STAGE611_ADJUDICATION.md`).
- **Seed 501**: the materially-continuous target undergoes a real,
  identity-valid physical turn (≈0.23→0.97) that persists through
  release. A repeated-replicate, CRN-paired schedule-effect comparison
  (25 replicates) shows sustained forcing DOES raise the material
  target's alignment relative to no forcing (demonstrated), but the
  specific historical actuator choice does NOT demonstrably outperform
  duration/cardinality/cadence/pool-matched random forcing (not
  demonstrated).
- **Seed 502**: v1 permanently diverges from the material target around
  t=32; the material target itself does not turn substantially
  (≈0.19→0.10); the reported later v1 rise belongs to a materially
  distinct population. v1 and v2 (exact replay) agree numerically with
  EACH OTHER at every field-direction radius while both diverge sharply
  from the material anchor — the strongest anchor-sensitivity case in the
  5-seed sweep. This pass's repeated-replicate comparison shows no
  demonstrated intervention effect on alignment, but a clearly elevated
  target-LOSS rate under forcing (44–52% of replicates lose the material
  target entirely, vs. 20% unforced) — a disruption signature distinct
  from seed 503's fragmentation but comparable in kind.
- **Seed 503**: the qualification-time target undergoes a **likely
  physical split** at t=47 (persistent daughter separation, no
  re-fusion, one daughter losing detectable coherence within 3 steps) —
  not formally "confirmed" (no independently validated physical-split
  threshold exists in this repository, and this pass declined to invent
  one to classify this specific seed). The large, historically-reported
  0.86 turn belongs to a THIRD, wholly unrelated, zero-overlap population
  — not either split daughter, and (new in this pass) v2's own EXACTLY
  computed anchor independently contradicts v1's high reading too (v2
  sides with the material trace's low readings, not v1's high one). A
  repeated-replicate causal comparison shows intervention raises the
  material-continuing daughter's own alignment (demonstrated) without a
  detectably elevated fragmentation rate relative to no forcing
  (organizational disruption not demonstrated as intervention-specific —
  split events are common, >50% of replicates, under all tested
  conditions including no forcing).
- **Seed 500**: reference/sanity case; v1 and material identity agree
  throughout at every field-direction radius; this pass's schedule-effect
  harness correctly does NOT manufacture a large intervention effect here
  (paired mean +0.009, 90% CI barely excludes zero) — a useful negative
  control on the harness itself.
- **Seed 504**: v1 and material identity agree throughout, but v2's exact
  anchor is a striking outlier (high, 0.72–0.88) despite 90/94 frames of
  v1==v2 membership agreement — a disclosed complication, not resolved
  further. This pass's repeated-replicate comparison REFINES the prior
  "positive short-horizon authority without persistent reorganization"
  finding rather than simply preserving it: under sustained forcing, a
  persistent (end-of-release) rise is demonstrated on average (paired
  mean +0.367, 90% CI [0.235, 0.499], the strongest paired signal of the
  5 seeds) but is highly unreliable (median 0.07 vs. mean 0.39 — a
  right-skewed/bimodal outcome). "Short-horizon response ≠ reliable
  persistent transition" is preserved as the TYPICAL case; this pass
  shows persistent transition is possible, just uncommon, under the
  tested budget.
- **Across all 5 seeds, actuator selectivity is never demonstrated.**
  Wherever an intervention effect exists (501, 503, 504), the specific
  historical top-K-by-authority actuator choice never distinguishably
  outperforms duration/cardinality/cadence/pool-matched random forcing.
  This is the most consistently replicated finding of the whole
  programme.
- **Trigger-state reproduction is exact for all 5 seeds** — independently
  verified bit-for-bit from each raw episode seed
  (`causal_reconciliation_step3_20260922/RNG_AND_CRN_AUDIT.md`).
- **`branch_adjudication_611.py` (Step 1's original 9-branch
  counterfactual adjudication script) is exactly reproducible** (verified
  for seed 501: 0 mismatches across 99 readout values) and architecturally
  CRN-clean (all branches per seed share one physics RNG stream; every
  branch's own decision-side randomness uses an independent generator).

## Provisional findings (evidence exists, not fully closed)

- Whether the ONLINE CONTROLLER's own re-inference (as opposed to a fixed
  schedule replay of its final actuator choices) adds anything beyond
  what schedule replay already shows — the "policy effect" estimand —
  is not yet closed for any seed; it requires decoupling the control
  loop's auxiliary decision-code RNG consumption from the physics stream,
  a larger audit-only engineering effort not completed in this pass.
  (`causal_reconciliation_step3_20260922/RNG_AND_CRN_AUDIT.md` §5,
  `NEXT_CONTROLLER_SPEC_INPUTS.md`.)
- Whether the field-direction readout's anchor-sensitivity finding
  (robust for 501, not for 502/503) survives EXACT v2 anchoring (as
  opposed to v1-as-proxy) — being closed in this pass; see
  `V2_REPLAY_AND_FIELD_READOUT.md` for seed-by-seed results.
- Full per-frame material tracing of Step 1's original 9 named
  counterfactual branches (as opposed to this pass's own, cheaper,
  materially-scored 3-branch schedule-effect harness) — not completed for
  all 5 seeds due to compute cost (~29 CPU-minutes per seed for the full
  9-branch reproduction); disclosed in
  `causal_reconciliation_step3_20260922/COUNTERFACTUAL_MATERIAL_TRACES.md`.

## Explicitly withdrawn claims

- "3/5 successful blind adaptive controls" (original Stage 6.11 report).
- "Seed 503 is the one seed with an unambiguous, all-readout-corroborated
  real turn" (Step 1's own `FIVE_SEED_CAUSAL_ADJUDICATION.md`) — narrowly
  contradicted: that corroboration was established on counterfactual
  branches whose own re-simulated trajectories did not reproduce the
  actual recorded run's t=47 split; applied to the real run, the
  "same-population" assumption does not hold past that point.

## Conceptual boundaries that remain load-bearing

- **Traveling-wave identity is explicitly OUT OF SCOPE for the flock
  experiment.** Identity here means flock/material-organizational
  identity with gradual local turnover permitted — never "does the same
  traveling pattern persist."
- **Material association (Jaccard overlap) is not the same thing as
  strict identity.** A confirmed physical split or merge should terminate
  strict same-object continuity even though material descendants can be
  tracked genealogically for analysis. No physical-split/merge threshold
  has been validated in this repository yet — any future use of one
  requires independent calibration first, the same way the primary
  association threshold was calibrated.
- **v1 and v2 are trackers, not ground truth.** Neither has ever been
  treated as ground truth in any pass to date, and this file does not
  start now.

## What the next task (controller redesign) may and may not assume

See `stage6_flock/stage6_11_translating_torus/audit/causal_reconciliation_step3_20260922/NEXT_CONTROLLER_SPEC_INPUTS.md`
for the full, itemized list. Controller redesign was explicitly out of
scope for every pass to date, including this one.
