# Final Stable-Selectivity Findings

**Scope reminder**: bounded, analysis-only follow-up to Stage 6.12C's
already-frozen K=1, d=8 exhaustive data (10 states, seeds 63200-63209, 20
candidates x 12 physics streams/state). No new simulation. Answers the
question `stage6_12C_kinematic_contact_confirmation/NEXT_STAGE_DECISION.md`
left open under its Case C finding: is the large outcome-oracle headroom a
reproducible actuator property, or stochastic-opportunity/winner's-curse
inflation?

## Answering the 8 questions posed by the task brief (section 21)

**1. How much of the per-stream oracle advantage is maximum-of-noise
inflation?** All of it, for the per-stream clairvoyant oracle specifically
-- this is a mathematical identity, not an estimate (`ORACLE_WINNERS_CURSE.md`
Result 1: permutation-null excess is exactly zero to numerical precision,
because the per-stream max is a property of each stream's own value set,
invariant to which candidate produced which value). For Stage 6.12C's
ACTUAL reported "outcome oracle" number (0.0222, which this follow-up
identifies as the state-stable-MEAN oracle, not a naive per-stream max --
see `DATA_DESIGN_AUDIT.md`), the permutation-null excess is **-0.0016**
(confirm-only) -- i.e., that headline number is not just partially
explained by no-stable-identity noise, its state-clustered mean sits
slightly BELOW what the null itself produces.

**2. Is there meaningful stable actuator-to-actuator variation?**
No. `Var_actuator / Var_total` (method-of-moments two-way decomposition)
is 0.0-4.2% in every one of the 10 states (mean 0.84%, median 0.0%,
`VARIANCE_DECOMPOSITION.md`). 7/10 states have a NEGATIVE raw (unclipped)
actuator-variance estimate -- actuator identity explains less cross-cell
variance than pure noise would.

**3. Can the best actuator be identified reproducibly before the future
physics realization is known?** Not reliably. Cross-validated selection
(train on a subset of streams, test on the rest) shows a mean lift of
+0.0013 over the median candidate (state-clustered 90% CI [-0.0012,
+0.0042], spans zero), with sign inconsistent across states (7/10 positive,
3/10 negative, `CROSS_VALIDATED_ORACLE.md`). This is roughly HALF the size
of the already-tiny random-candidate baseline effect (~0.003).

**4. How many physics samples are needed for candidate ranking to
stabilize?** As many as tested (up to 6 of the available streams) does not
stabilize it. Train/test rank correlation stays within a narrow band around
zero (mean Spearman rho: -0.005 at m=1 training stream, +0.001 at m=6) with
no monotonic improvement as training-set size grows (`RANK_RELIABILITY.md`).
This design cannot distinguish "needs more than 6 streams" from "there is no
stable ranking to find," but the complete absence of any trend toward
stability as m increases is more consistent with the latter.

**5. Do some flock states support stable selectivity while others only
support stochastic opportunity?** Not within this sample. Applying the task
brief's own named categories with explicit, stated thresholds, all 10/10
states classify as `stochastic-opportunity`, not `stable-selective`
(`STATE_TAXONOMY.md`). States differ substantially in the SCALE of their
per-stream opportunity (clairvoyant oracle ranges 0.008-0.242 across
states) but not in whether that opportunity is exploitable in advance
(`Var_actuator_frac` stays under 5% and `C` stays near/below random in
every state, regardless of scale).

**6. Did Stage 6.12C measure true directed causal interaction, or only
geometric contact?** Only geometric contact (`CONTACT_METRIC_AUDIT.md`).
`mech_cumulative_contact_edges` is `distance <= R`, undirected, FOV-free. The
simulator's actual causal-influence relation (`live_edges`) additionally
requires the RECEIVER's field of view and is directed/asymmetric. Stage
6.12C's Case-C conclusion ("headroom is not explained by contact") should
therefore be read specifically as "not explained by geometric proximity,"
not "not explained by any causal-interaction channel" -- a directed,
FOV-aware live-influence oracle was never computed by any stage to date.

**7. Is there any existing-data hint that actuators become privileged when
they enter/join the collective?** The required fields (entry event,
time-to-entry, post-entry membership duration) were never persisted by
Stage 6.12C and are not reconstructed here (out of scope; would require
re-simulation). The two available weak proxies (geometric contact-during-
forcing, final target size) show no consistent, state-clustered association
with effect size (`MEMBERSHIP_EMBEDDING_CLUES.md`). This is an absence of
data to test the hypothesis, not evidence against it.

**8. Should the next experiment test static organizational features, or
study stochastic/phase-conditioned control?** See `NEXT_EXPERIMENT_DECISION.md`
for the full argument -- **Decision 2**: study stochastic-opportunity /
phase-conditioned control, not static actuator-feature discovery, based on
findings 1-5 above.

## The single clearest number in this whole follow-up

Stage 6.12C's headline claim was: outcome oracle mean ΔJ_conservative ≈
0.0222, "~6.9x random, CI clearly separated from every other strategy."
This follow-up's single most decisive result: **a permutation null that
destroys stable candidate identity while preserving every stream's own
outcome distribution reproduces that exact quantity with essentially zero
excess (observed 0.0222 vs. null mean 0.0238, confirm-only precision,
`ORACLE_WINNERS_CURSE.md`).** The 6.9x number is real (it is a correct
description of the data), but it is not evidence of actuator selectivity --
a system engineered to have NO stable actuator effect at all would be
expected, by construction, to produce approximately the same number.

## What this follow-up does NOT establish

- That NO actuator feature could ever predict effect in this system -- only
  that none of the candidate-level features already logged (kinematic
  score, static distance, direct-contact-at-t0, geometric contact-during-
  forcing) does so reliably, and that raw candidate IDENTITY itself carries
  almost no reproducible information at this state/stream count.
- That a larger sample (more states, more streams per state) would not
  eventually reveal a small but real stable-actuator effect -- every
  "near-zero" finding here is a CI-spans-zero/small-magnitude finding, not
  a CI-excludes-any-possible-effect finding, exactly as Stage 6.12C's own
  findings documents are careful to state about their own null results.
- That the true directed causal-influence channel (FOV-gated `live_edges`,
  as opposed to geometric contact) has been tested and rejected -- it has
  never been computed for this purpose by any stage to date
  (`CONTACT_METRIC_AUDIT.md`).
- Any causal claim about WHY stochastic opportunity dominates -- this
  follow-up decomposes WHETHER the headroom is stable, not WHAT produces
  the per-realization variation.
