# Stage 6.12 Correction Memo (Part I — no new simulation)

All numbers below come from `code/correction_612.py`, run against the
EXISTING `data/phaseA_results_612.json` (1,296 intervention rollouts, 9
states, full 24-cell K×d grid). Corrected derivative outputs:
`data/phaseA_results_612_corrected.json`,
`data/correction_612_summary.json`. The original files are untouched.

## 0. Terminology correction (source-verified)

`stage6_12_control_readiness/code/intervention_612.py:111-125` labels a
rollout `confirmed_split` iff `ForwardMaterialTrace611.split_flag` fired
anywhere in the traced rollout AND strict continuation (`V=1`) held
throughout. `split_flag` (`forward_material_trace_611.py:196`) is a pure
material-overlap heuristic ("≥2 accepting candidates each retain a
substantial absolute share of `prev`"), never checked against an
independently validated PHYSICAL split criterion — `CURRENT_RESEARCH_
STATUS.md` states outright that no such criterion has been validated in
this repository. **`confirmed_split`/`confirmed_merge` were therefore
mislabelled** — the ORIGINAL files retain the old label (never silently
rewritten), and the corrected derivative files add `event_corrected`,
renaming these to `material_split_flag` / `material_merge_flag`. Genuinely
ambiguous `V=0` cases already used hedged language
(`candidate_split_or_merge_interruption`) and are unchanged.

## 1. Did split/merge semantics make the original identity-valid fraction too optimistic?

**Yes, materially.** The original `V`/`identity_valid_fraction` (0.94–1.00
per cell) counts a `material_split_flag` rollout as fully valid. Under the
conservative definition (`V_conservative` = 1 only if `V=1` AND zero split
flags AND zero merge flags AND zero unresolved steps anywhere in the
traced rollout), the identity-valid fraction drops sharply: **only 830/1296
(64.0%) of rollouts are conservatively clean**, versus ~97% under the
original definition. This confirms the concern: the original headline
identity-valid numbers substantially overstated strict, unambiguous
continuation.

## 2. Do the null susceptibility/selectivity conclusions survive conservative identity scoring?

**Mostly yes at the pooled level, but not uniformly, and the per-state
picture changes materially (see Q4).** Pooled `G_sus`:

| utility | pooled mean | naive (unclustered) 90% CI | state-clustered 90% CI |
|---|---|---|---|
| `J_assoc` (original semantics) | +0.0011 | [-0.0054, +0.0078] | [-0.0317, +0.0321] |
| `J_conservative` | +0.0063 | **[+0.0023, +0.0107]** | [-0.0063, +0.0186] |

Under the conservative utility, the NAIVE (rollout-as-independent) 90% CI
excludes zero — a small but "significant"-looking positive effect. **This
does not survive state-clustering** (Q3) — the state-clustered CI for
`J_conservative` still spans zero. The corrected headline is: **neither
utility shows a robust, state-clustering-robust departure from zero at the
pooled level**, but conservative scoring shifts the point estimate up
(+0.0011→+0.0063) and the naive CI's sensitivity to the identity-scoring
convention is itself a finding — see Q1.

## 3. Is the pooled susceptibility CI still near zero when clustered by state?

**Yes, both CIs span zero once properly clustered by state** (9 independent
units, not 1,296 rollouts nested within them). The original Stage 6.12
`READINESS_MAP.md`/`analysis_612.py` CI was computed by bootstrap-resampling
INDIVIDUAL ROLLOUTS (see `bootstrap_ci` in `analysis_612.py`), which
**treats rollouts nested within the same 9 states, sharing physics streams
and actuator-set draws, as if independent — this is invalid** and is
superseded by the state-clustered bootstrap here. The state-clustered CIs
are visibly wider (±0.03 vs ±0.007 for `J_assoc`), exactly the symptom of
under-counted clustering the task flagged.

## 4. Are some states individually responsive despite the pooled null?

**Yes — substantial state heterogeneity, not uniform near-zero.**

| state | role | mean Δ (J_assoc) | mean Δ (J_conservative) | non-`none`-event rate |
|---|---|---|---|---|
| s612_00 | dev | +0.0058 | **-0.0270** | 31.2% |
| s612_01 | dev | -0.0012 | -0.0012 | 0.0% |
| s612_02 | dev | **+0.1146** | +0.0237 | 59.0% |
| s612_03 | dev | +0.0104 | +0.0327 | 68.1% |
| s612_04 | dev | **-0.1448** | **+0.0288** | 38.2% |
| s612_05 | dev | +0.0001 | +0.0303 | 27.8% |
| s612_06 | holdout | -0.0004 | -0.0004 | 0.0% |
| s612_07 | holdout | +0.0179 | -0.0273 | 44.4% |
| s612_08 | holdout | +0.0077 | -0.0024 | 66.7% |

**The pooled near-zero result is a genuine cancellation, not uniform
near-zero states**: `s612_02` (+0.115) and `s612_04` (-0.145) are both
large in magnitude and opposite in sign under `J_assoc`. Most strikingly,
**`s612_04` REVERSES SIGN entirely between utilities** (-0.145 under
`J_assoc` → +0.029 under `J_conservative`): its no-control baseline itself
carries a high split-flag rate (`J0_assoc`≈0.32 vs `J0_conservative`≈0.06),
so under the permissive utility the UNFORCED branch looks unusually good,
making forcing look harmful by comparison — an artifact of the
no-control baseline's own split-flag inflation, not evidence forcing hurts
this state. This is exactly the kind of state-level structure a pooled
average hides.

## 5. Does sustained actual contact remain associated with paired intervention effect?

**Much more weakly than Stage 6.12's original (uncorrected) mechanism
analysis suggested, and the direction is not consistent.** The original
`MECHANISM_ANALYSIS.md` compared ABSOLUTE outcome groups (`J>0.3` vs
`J≤0.3`) and found ~10× differences in contact/coverage. Recomputed as a
PAIRED causal effect (`delta_assoc` vs. mechanism diagnostics, Spearman
rank correlation over all 1,296 rollouts):

| mechanism diagnostic | Spearman vs Δ(J_assoc) | Spearman vs Δ(J_conservative) |
|---|---|---|
| direct contacts at t0 | **+0.199** | +0.033 |
| cumulative contact edges | +0.022 | -0.066 |
| unique target coverage | +0.016 | -0.065 |
| mean actuator-target distance at t0 | +0.033 | +0.060 |
| actuators entered target | +0.123 | -0.041 |

Top-vs-bottom quartile of `delta_assoc` (n=324 each): direct-contacts-at-t0
is higher in the top quartile (0.028 vs 0.009, ~3× not ~10×), but
**cumulative contact edges and unique coverage are HIGHER in the BOTTOM
quartile** (29.1 vs 23.8, and 4.58 vs 4.30 respectively) — the opposite
direction from the original absolute-outcome comparison. **The original
"sustained contact predicts success" finding was substantially an artifact
of comparing rare high-`J` rollouts (driven partly by permissive split
continuation and by state-level baseline differences) to the rest, not a
robust paired-causal-effect signal.** `direct_contacts_at_t0` is the one
diagnostic that holds up in the same direction under both analyses,
though weakly (Spearman ≈0.2).

## 6. Is the contact association present among clean no-split trajectories?

Restricting to the 830 rollouts with zero split/merge flags: correlations
are similar in magnitude to the full sample (`direct_contacts_t0`:
+0.207, `actuators_entered_target`: +0.139, others ≤0.05) — **the weak
`direct_contacts_t0` signal is not an artifact of split-flagged rollouts
specifically; it persists (weakly) among clean trajectories too.** This is
the one piece of the original mechanism lead that survives correction,
though at a much smaller effect size than originally reported.

## 7. Does existing evidence justify a large full-grid Monte Carlo rerun?

**No — not a blind rerun of the same design.** The corrected evidence
sharpens rather than reverses Stage 6.12's basic picture: pooled/
state-clustered effects remain indistinguishable from zero under proper
uncertainty accounting, AND the exploratory contact lead that might have
justified "just get more precision on the same random-fixed-set design" is
now known to be much weaker and less directionally consistent than
originally reported. A blanket higher-precision rerun of the SAME
random-fixed-set design would mostly sharpen a null. The evidence DOES
justify a **focused** follow-up that directly tests whether rare good
fixed sets exist (exhaustive small-K search) and whether temporal access
maintenance — not static set identity — is the operative variable, which
is exactly Stage 6.12B's design.

## Decision

**No major contradiction found that would block proceeding to Part II.**
The correction is real and substantively changes how the "contact
persistence" lead should be described (much weaker, direction-inconsistent
for most diagnostics, still present but small for `direct_contacts_at_t0`)
and surfaces genuine state-level heterogeneity that a pooled average was
hiding — but it does not overturn the basic conclusion that random fixed
forcing is weak/inconsistent at the tested precision, nor does it change
that the field is still genuinely open between "no useful controllability,"
"rare good fixed sets," and "sustained-access matters." **Proceeding
directly to Stage 6.12B**, with the contact-persistence hypothesis now
framed appropriately conservatively (a lead worth testing rigorously, not
an established mechanism).

## Known limitation carried into Part II

Phase B/C (`run_phaseBC_612.py`) rollouts were computed with
`with_mechanism=False` and only per-set `mean_J` was persisted — per-
rollout `V`/split/merge/unresolved fields were never saved for Phase B/C,
so `J_conservative` cannot be reconstructed for the Phase B/C search/
holdout results from existing data alone (disclosed in
`data/correction_612_summary.json["phase_bc_note"]`). This is a genuine
gap in what Part I's "no new simulation" constraint can recover; Stage
6.12B's fresh rollouts persist full per-rollout identity fields from the
start so this gap does not recur there.
