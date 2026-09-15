# FRESH_CHAT_HANDOFF.md

Concise state of this research effort, for picking up in a new
conversation with no prior context. Read `VALIDATION_RESULTS.md` §6 first
— it is the one-paragraph version of everything below.

## Where this stands

**Phase 0 (provenance/inventory) and Phase 1 (analytical model) are
complete**, including a real adversarial review that found and fixed
three non-cosmetic bugs (`THEORY_REVIEW.md`). **Phase 2 (validation) is
complete and found that the implemented tracker does NOT yet meet the
mandate's final scientific gate on real data** (`VALIDATION_RESULTS.md`
§6) — it works reasonably on small synthetic scenarios but fails to
establish any persistent track on the real 400-bird flock in all 5 tested
episodes. **Phase 3 (visualization instrument) and Phase 4 (control
integration) have NOT been started** — Phase 4 explicitly must not start
until the Phase 2 failure below is fixed, per the mandate's own rule.

## Read in this order

1. `CLAIMS_LEDGER.md` — verdicts on the prior (pre-this-effort) audit
   corpus's claims. Settled background; nothing here needs re-litigating.
2. `IDENTITY_MODEL.md` + `MATHEMATICAL_CHECKS.md` — the analytical
   specification, post-fix (see `THEORY_REVIEW.md` for what was wrong and
   fixed: an inverted decision threshold, a missing first-class Birth
   event, a broken cross-reference, a near-duplicate coalescing
   cliff-edge, an incoherent state-noise model, an overclaimed
   irreducible-ambiguity case).
3. `MEASUREMENT_CONTRACT.md`, `VALIDATION_PROTOCOL.md` — the frozen
   measurement/scoring contracts these results were scored against.
4. `VALIDATION_RESULTS.md` — what actually happened when the model in (2)
   was implemented (`code/joint_tracker.py`) and run against the protocol
   in (3). **This is the most important document for deciding what to do
   next.**
5. `VIZ_RECON.md` — Phase 0's visualization reconnaissance (separate
   track, not blocked on the Phase 2 finding above — could proceed in
   parallel if the next session wants to work on Phase 3 instead of
   fixing the tracker).

## The single most important next step

**Root-cause and fix the real-scale tracking failure documented in
`VALIDATION_RESULTS.md` §3.** Concretely: `code/joint_tracker.py`'s
`JointTracker` never confirms a label matching the real flock's actual
coherent region in any of 5 real seeds within at least 30 steps, while
v1, v2, and even the naive baseline all track it fine on the same data.
The leading hypothesis (not confirmed): real data almost always exceeds
`EXACT_ENUM_MAX_PAIRS=24`, forcing the GREEDY assignment path plus the
merger pre-check — a combination only ever validated at small synthetic
scale — at essentially every real step, and this combination appears too
unstable/conservative to let anything survive the 2-step birth-
confirmation window. Suggested diagnostic approach for the next session:

1. Instrument `JointTracker.step()` to log, per real-replay step, WHY the
   reference-matching candidate was or wasn't confirmed (which branch —
   merger pre-check consuming it, greedy assignment losing it to a
   competing label, or the confirmation-matching Jaccard threshold
   (`0.6`) never being cleared between consecutive steps).
2. Re-run the smallest reproducing case: `run_real_replay_comparison.py`
   for seed 500 only, with that instrumentation on, for just the first 10
   steps.
3. Once root-caused, fix it as a versioned, disclosed change (not a
   silent threshold loosening) and re-run BOTH the synthetic battery
   (confirm no regression on the scenarios that currently work) and the
   real-replay comparison (confirm the fix actually produces a persistent
   track) before declaring this resolved.

## Other concrete open items, roughly in priority order

1. Implement `IDENTITY_MODEL.md` §7 rows 3 ("detector over-segmentation")
   and 4 ("detector merger") in `joint_tracker.py` — currently unbuilt,
   and directly responsible for `symmetric_split` and
   `superposition_two_distinct` being the two worst-performing scenarios
   in both the dev and held-out synthetic batteries (`VALIDATION_RESULTS.md`
   §1–2).
2. Root-cause the residual spurious-merger sensitivity found even in the
   simplest dev scenario (`two_clumps`, `VALIDATION_RESULTS.md` §0) —
   likely related to the same real-scale issue above, since torus-
   wraparound proximity plus the merger pre-check's reachable-radius test
   are the suspected mechanism in both cases.
3. Run the scale-sensitivity checks (`MEASUREMENT_CONTRACT.md` §1,
   `VALIDATION_RESULTS.md` §5) that were skipped this pass — ±20%
   perturbation of `PROCESS_NOISE_STD`, `K_SIGMA_REACHABLE`,
   `BIRTH_LR_FLOOR`, `MIN_BIRTH_SIZE`, and the candidate-coalescing
   Jaccard threshold.
4. Re-run the synthetic battery at the protocol's originally-specified 20
   dev + 20 held-out seeds (this pass used 6+6 as a disclosed compute
   accommodation, `VALIDATION_RESULTS.md` §0) once the real-scale issue
   above is fixed and worth the additional compute.
5. Add v1 to the vicsek (out-of-model) synthetic sub-battery — omitted
   this pass, not a deliberate scope decision.
6. Build the fuller `identity_69.field`-based phenotype representation
   `phi` in place of the current `(pi, Sigma)` approximation, if the
   real-scale fix above doesn't already require touching this code.

## Things this session verified directly, worth trusting without re-checking

- Production `run_online_control_611.py` imports `lineage_611` (v1) and
  never `thingness_611` or any `lineage_v2` module — confirmed by direct
  grep, twice, by two different passes.
- The oracle-radius control-pool leak
  (`intervention_api_611.near_exterior`, `radius_factor=3.0`, using the
  simulator's true `R`) is real and located at
  `code/run_online_control_611.py:226`.
- `pytest tests/` passes 66/66 in the `fuzzy-blankets` conda environment
  (NOT on the base `python3` — `pytest` is only installed in that env).
- Playwright (Python) works directly against local `file://` HTML with no
  server, confirmed by actually rendering
  `figures/translating_collective_611.html` at three viewports with zero
  console errors (screenshots in `visual_qa_screens/`).
- Raw per-step position/heading data for all 5 real seeds (500–504) exists
  at `data/viz_bundle_611__seed{500..504}.json` (`r`, `z`, `phase`,
  `interior`, `actuators`, `target_heading` per frame) — this is what
  Phase 2's real-replay comparison and any future Phase 3/4 work should
  read for raw real observations; it is NOT the same as
  `audit/lineage_v2_replay_611__seed*.json`, which only has derived
  per-tracker summaries, not raw frames.

## Environment notes

- Use `conda run -n fuzzy-blankets python3 ...` for anything needing
  `pytest`, `playwright`, or the numerical stack — the base `python3` at
  `/home/hkhurana/miniconda3/bin/python3` is missing these.
- All Phase 2 code lives under `identity_foundation/code/`; results under
  `identity_foundation/phase2_results/*.json`. Nothing outside
  `identity_foundation/` was modified by this effort — `code/`, `audit/`,
  `data/`, `figures/` in the parent `stage6_11_translating_torus/`
  directory are all as they were found.
- One synthetic-battery seed across all 16(+4 vicsek) scenarios takes
  ~3.7 minutes uncontended; a real-replay seed takes ~5.5 minutes
  uncontended. Budget accordingly before launching a bigger re-run.
