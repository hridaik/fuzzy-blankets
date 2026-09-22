# Counterfactual material traces (Task E)

## What Task E asked for, and what was actually feasible

Spec Task E asks for `ForwardMaterialTrace611` applied to EVERY persisted/
reproducible Step-1 branch (`audit/branch_adjudication_611.py`'s 9 named
branches per seed: no_control, original_reproduced, old_set_one_shot,
old_set_held_actual_duration, matched_random_blind_exterior,
repaired_blind_authority, repaired_direct_causal_restricted,
exact_direct_interface_repaired, beam_search_benchmark), with full
per-frame persistence for every branch.

## Finding 1: Step 1's persisted branch outputs do not include raw trajectories

`audit/branch_adjudication_611__seed{500..504}.json` contain only
end-of-control/end-of-release SUMMARY readouts (`v1_end_control`,
`v2_end_release`, `original_material_end_control`,
`field_direction_end_release`, etc.) per branch — not the per-frame
`(r, z)` trajectories `track_trajectory` computed them from. Confirmed by
direct inspection (each branch's JSON entry is `{"meta": {...},
"readouts": {...}}`, ~11 scalar fields, no per-frame array).

**Consequence**: applying `ForwardMaterialTrace611` to these EXACT branch
runs requires RE-RUNNING `branch_adjudication_611.run_seed`, not merely
reading existing output.

## Finding 2: `branch_adjudication_611.py` is architecturally CRN-clean and (per a direct re-run check) deterministic

Read `branch_adjudication_611.simulate()` (lines 104–118): creates a
FRESH `rng = np.random.default_rng(rng_seed)` and calls ONLY
`mf.step(r, z, rng, forced_actions=forced)` in a loop — no other draw
touches this generator inside `simulate`. All 9 branches per seed call
`simulate(..., rng_seed=base_seed, ...)` with the **identical**
`base_seed = 5_000_000 + seed` — and every branch's `policy(step, r, z)`
that needs its own randomness (actuator selection: `old_select_actuators`,
`select_actuators_v2`, `beam_search`, the matched-random draw) uses its
own INDEPENDENTLY-seeded generator, never the shared `rng` passed into
`simulate`. Per `RNG_AND_CRN_AUDIT.md` Finding 1, this means
`branch_adjudication_611.py`'s own 9-branch comparison per seed **is
already valid CRN** — this pass did not need to fix or work around
anything here, only verify it (the task's Task F0 explicitly asks to
check rather than assume).

**Verification**: `run_seed(501, ...)` was re-run in full
(`code/verify_branch_adjudication_reproducibility.py`) and its 9×11
readouts compared against the persisted `branch_adjudication_611__seed501.json`
to floating-point tolerance 1e-9.

- **Result: REPRODUCED_EXACTLY. 0 mismatches across all 9 branches × 11
  readout fields (99 values total).** Elapsed: 1731 seconds (~28.9
  minutes) for seed 501 alone — confirming both the CRN-cleanliness
  argument above AND that `branch_adjudication_611.py`'s own actuator-
  selection procedures (including the rollout-based repaired-authority and
  beam-search branches) are themselves fully deterministic given their own
  internal seeds. This is a genuinely reassuring, independently-obtained
  fact about Step 1's original causal-adjudication infrastructure: it was
  not an artifact of one lucky run.

## Finding 3: full per-branch, per-frame material-trace instrumentation was not completed for all 9×5 branches, given its compute cost

Re-running `run_seed` for a single seed (with `repaired_blind_authority`,
`repaired_direct_causal_restricted`, `exact_direct_interface_repaired`,
and `beam_search_benchmark`'s expensive rollout-based actuator selection,
`N_ROLLOUTS_REPAIRED` Monte Carlo rollouts each) took over 25 CPU-minutes
for ONE seed in this environment. Extending this to full per-frame
persistence (member IDs, not just summary readouts) for all 9 branches ×
5 seeds was not completed within this pass's time budget — this is
disclosed as a genuine, cost-driven scope limitation (spec §5/workflow
rule: "state exactly why, preserve the partial result, proceed with all
other feasible sections"), not a silent narrowing.

## What WAS completed instead: a purpose-built, cheaper schedule-effect harness for the two priority seeds

`code/seed501_schedule_effect.py` and `code/seed503_schedule_effect.py`
(generalized as `code/seed_generic_schedule_effect.py` for 500/502/504)
implement a SIMPLER, materially-scored 3-branch comparison
(no_forcing / historical_schedule / matched_random) from the exact same
verified trigger states, with full per-replicate material-trace
persistence (`data/seed{n}_schedule_effect.json`), at a small fraction of
`branch_adjudication_611.py`'s per-branch cost (no expensive rollout-based
actuator re-optimization — the historical schedule is REPLAYED verbatim,
and the random comparator is drawn once per replicate from the same
oracle exterior pool `branch_adjudication_611.py` itself uses). This
directly answers the spec's core causal questions (intervention effect,
actuator selectivity, disruption) for the two seeds prioritized by the
task's own framing ("seed 501 is now the highest-priority historical
case"; seed 503's split/disruption question is the other headline case),
with proper CRN pairing and distributional (25-replicate) statistical
reporting — see `seed_501_causal.md`, `seed_503_causal.md`,
`seed_503_disruption_analysis.md`.

This is NOT the same as tracing Step 1's original 9 named branches
(which include repaired-authority and beam-search reference-upper-bound
branches not needed to answer the intervention-effect/selectivity
questions) — it is a materially-scored analogue of the 4 branches that
matter most for those questions (no_control ≈ no_forcing,
old_set_held_actual_duration ≈ historical_schedule,
matched_random_blind_exterior ≈ matched_random), independently
constructed and independently verified reproducible from the trigger
state, rather than a re-instrumentation of the original 9-branch script.

## Seeds 500, 502, 504

The same generic schedule-effect harness was run for these three seeds
(`data/seed500_schedule_effect.json`, `seed502_schedule_effect.json`,
`seed504_schedule_effect.json`) — see `seed_500_causal.md`,
`seed_502_causal.md`, `seed_504_causal.md` for results. Full 9-branch
Step-1 reproduction with material instrumentation was not attempted for
these three, for the same disclosed compute-cost reason as above.

## Disclosed gap: per-replicate schedule-effect data is summary-level, not full per-frame

For all 5 seeds' schedule-effect JSON files, each of the 20–25 replicates
× 3 branches persists per-replicate SUMMARY statistics (final status,
end-of-control/end-of-release alignment fraction, target size, split/
merge counts) rather than the full per-frame member-ID trace for every
one of the ~75 simulated rollouts per seed. This is a genuine,
disclosed scope reduction relative to spec Task E's "for every branch,
persist every frame: exact material member IDs...". Full per-frame
persistence for the ACTUAL recorded trajectories (not the simulated
schedule-effect replicates) IS complete — see `V2_REPLAY_AND_FIELD_READOUT.md`
and `data/v2_replay_seed{500..504}.json`, which have exact v1/v2/material
member IDs for every frame of the real recorded episodes. The gap is
specifically in the SIMULATED counterfactual replicates' per-frame detail,
not the real-trajectory record.
