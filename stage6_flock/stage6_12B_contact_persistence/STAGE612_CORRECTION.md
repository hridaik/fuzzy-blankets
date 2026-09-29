# Stage 6.12 Correction (Part I) — Summary

The full correction pass (no new simulation, existing Stage 6.12 Phase A
data only) lives in
`stage6_flock/stage6_12_control_readiness/STAGE612_CORRECTION_MEMO.md`,
with derivative machine-readable outputs in
`stage6_flock/stage6_12_control_readiness/data/phaseA_results_612_corrected.json`
and `.../data/correction_612_summary.json`, produced by
`stage6_flock/stage6_12_control_readiness/code/correction_612.py`. This
file is a pointer + the headline results that motivate Stage 6.12B's
design, not a duplicate of the full memo.

## Headline corrections

1. **Terminology**: `confirmed_split`/`confirmed_merge` in Stage 6.12's
   original `event` field were `ForwardMaterialTrace611` advisory flags,
   never checked against an independently validated physical-split
   criterion. Renamed `material_split_flag`/`material_merge_flag` in all
   NEW analysis (original files untouched, provenance preserved).
2. **Identity-valid fraction was optimistic**: 97% (original `V`) vs.
   **64.0%** (conservative `V_conservative`, requiring zero split/merge
   flags and zero unresolved steps).
3. **Pooled susceptibility remains statistically indistinguishable from
   zero once properly clustered by STATE** (not rollout) under both
   utilities — but the naive (unclustered) CI for `J_conservative` alone
   would have looked "significant" (a methodological trap, corrected here).
4. **Substantial state-level heterogeneity was hidden by the pooled
   average** — e.g. `s612_02`: +0.115 vs. `s612_04`: -0.145 under
   `J_assoc`; `s612_04` even REVERSES SIGN under `J_conservative` (+0.029)
   because its no-control baseline itself carried a high split-flag rate.
5. **The original "sustained contact predicts success" mechanism lead was
   substantially an artifact of comparing absolute post-hoc outcome groups
   (J>0.3 vs not), not a paired causal effect.** Recomputed as paired
   ΔJ-vs-mechanism Spearman correlation, most diagnostics are weak
   (|ρ|<0.07) and some REVERSE SIGN from the original comparison;
   `mech_direct_contacts_t0` is the one diagnostic that survives at a
   modest ρ≈0.20 (both in the full sample and restricted to
   split/merge-flag-free rollouts).

## What this means for Stage 6.12B

No major contradiction blocked proceeding — see the memo's final decision
section. But the "contact persistence" hypothesis entering Stage 6.12B is
now framed as **a lead worth testing rigorously with fresh, properly paired
data (which Stage 6.12B provides from the start, closing the Phase-B/C
data-availability gap the correction pass also surfaced), not an
established mechanism.** Stage 6.12B's own rollouts persist full
`V_conservative`/`J_conservative`/event fields at COMPUTE TIME
(`intervention_612b.add_conservative`), so this gap does not recur here.
