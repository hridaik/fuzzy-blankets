# Visualization Notes — Interactive Demo v2

Scope: presentation layer only. No flock dynamics are reimplemented in
JavaScript; the browser only plays back and lets the viewer scrub/toggle
already-computed, already-frozen Stage 6 results. This document records
exactly which files each tab draws from, which seeds/events/formulas are
used, the one place a frozen formula is applied post hoc, what was
deliberately left out and why, the Stage 6.11 v1/audit caveat, and the
browser QA that was actually run against the committed `build/index.html`.

All paths below are relative to the repository's `stage6_flock/` directory.

---

## Tab 1 — Boundary

**Question:** Can trajectories reveal a compact screen around a collective?

- **Trajectory / lattice / roles:** `interactive_demo/data/seed2__no_control__cw.json`
  — seed 2, `no_control` condition, V3 protocol, L=10 (100 birds). `roles.core`
  (20 birds) = interior I0; `roles.dynamic_shell` (12 birds) = B^D;
  `roles.fiedler` (2 birds, ids 5 & 46) = B^F. `timeline.identify = 41` drives
  when the interior/boundary overlays are allowed to appear — **not**
  hardcoded, read from the stored scenario.
- **Predictive boundary B^pred:** `stage6_7_blind_boundary/data/predictive_boundary_panel.json`,
  `results["seed2_no_control"].candidates[0]` (`label: "established_I0"`).
  Verified in the export script (`assert established["I"] == seed2["roles"]["core"]`)
  that this candidate's interior matches the seed-2 bundle's I0 exactly —
  same flock, not a different run. `B_hat_pred = [6]` (bird 6, a subset of B^D).
- **Screening scatter** (excess loss vs. boundary size): the same panel's
  20 candidates for `seed2_no_control` (`C_internal/G_internal/L_blanket/D_local`
  and `excess_loss_test` per candidate, generation methods `high_coherence`,
  `mcmc_swap`, `perturb_I0`, `region_growing`, `spectral_resized`,
  `seed_reference_I0`), with a tolerance line at `delta_pred = 0.01`.
- **Generalization panel** (right sidebar): `stage6_5/boundary_inference/data/held_out_evaluation.json`
  — mean excess log-loss of B_hat / B_D / B_F / a size-matched random set,
  averaged over 3 **held-out** seeds (17, 18, 20) never used to tune the
  greedy shortlist selection rule (`shortlist_k=20`, `delta_tol_frac=0.05`).
  This is deliberately a *different* flock from the one drawn on the lattice
  — that's the actual generalization test, and pretending it's the same flock
  would be more misleading than showing it side by side with a note.
- **Headline log-loss numbers:** `v1_mechanism_audit/data/predictive_screening.json`
  (`n_traj=40`, `mean_logloss_full/BD/BF`), a structural sanity check that
  `excess_logloss_BD_minus_full ≈ 0` (B^D is provably predictively sufficient)
  while `excess_logloss_BF_minus_full > 0` (Fiedler is not).
- **No aggregation/rerun:** every number here is copied, not recomputed. The
  only arithmetic performed by the export script is a plain mean over 3
  already-computed per-seed `excess_loss` values (`mean_excess_loss`), purely
  for display — not a new statistical test.

## Tab 2 — Causal access

**Question:** Which exterior states can move the collective toward a chosen target?

- **State:** `stage6_10_emergence_adaptive_control/data/audit_trace.json`,
  `episodes[2]` — **seed 17**, dev split, h* = 2 (←), t0 = 60, L=20 regime
  (nn=400, beta=1.0, s=1.0). Candidate pool = the frozen `adaptive_oracle`
  arm's step-0 `B_do` (24 exterior sources that were actually do()-tested).
- **Seed selection (revised):** the tab originally used episode 0 (seed 15),
  the default/first audited state. Reviewer feedback correctly flagged it as
  a poor example: its heading vector was almost uniform and its authority
  values rounded to ~0 for nearly every candidate. `src/data_prep/explore_tab2_states.py`
  compares all 8 audited states (replays each one's t0 heading vector and
  verifies it against the stored per-candidate KL to machine precision, then
  reports authority spread, interior compactness (Q_clump), and heading
  diversity for each). Episode 2 (seed 17) has the best-separated authority
  spread of the 8 (max 0.0081 at τ=2, up to 0.032 at τ=8, **including real
  negative values down to −0.0044 at τ=8** — genuine examples of a source
  that actively hurts the target), a compact single-component interior
  (Q_clump=0.91), and a real mixed heading vector (281 vs. 119 birds across
  2 headings, not degenerate). See the module docstring in `prep_tab2_causal_access.py`
  for the full 8-state comparison table.
- **Deterministic replay of the full heading vector, now used for real triangle
  headings:** the 400-bird heading vector at t0 was never persisted (the audit
  pipeline computed it in memory and discarded it). It is replayed exactly as
  `run_audit_hypotheses.py` did — `run_episode(sim, seed, nt=t0+2)`, `z_hist[t0]`
  — and verified by reproducing every stored per-candidate KL value to within
  1e-9 before use (`explore_tab2_states.py` shows max error ~1e-15 across all
  8 states). Birds now render with their real replayed heading instead of a
  placeholder.
- **Per-interior-bird causal-effect breakdown:** `reference_truth.do_influence`
  already computes a per-target-bird KL contribution (`per`) on its way to the
  summed total that was the only thing previously kept. No new quantity is
  computed — the same call that produces the stored "kl" total also produces
  this breakdown; we just stopped discarding half its return value. Top 10
  interior birds by |contribution| are kept per candidate. Shown as a bar list
  when "Direct causal effect" mode is active and a candidate is selected —
  it makes the effect's spatial locality legible (e.g. bird 150's total effect
  of 1.505 lands almost entirely on its two or three nearest interior
  neighbors, not spread evenly across the 108-bird interior).
- **Metrics:** `stage6_10_emergence_adaptive_control/data/audit_hypotheses.json`,
  `H3_kl_vs_authority.per_state[2]`, matched to the same (seed, step) and
  length-checked before use. Two real, cleanly-sourced quantities:
  - **Direct causal effect** = exact **one-step** (t → t+1) interventional KL
    divergence of the interior's next-heading marginals under `do(z_j = z')`,
    summed over the interior and averaged over alternate z'
    (`reference_truth.do_influence`, `agg="sum"`). This already *is* an
    interventional quantity — not a passive correlation — and it is a
    single-timestep quantity by construction, distinct from the multi-step
    (τ≥2) target authority below. The UI labels this explicitly ("1-step").
  - **Target authority** A_j^{h*,τ} = E[H*_{t+τ} | do(u_j=h*)] − E[H*_{t+τ} |
    baseline], common random numbers, n_roll=96, τ ∈ {2,4,8}
    (`reference_truth.task_authority`). τ=2 is the default and minimum
    informative horizon: τ=1 exterior authority is structurally exactly 0 in
    this model (a forced exterior action can't reach the interior in one
    step — asserted in `tests/test_reference_truth.py`), so it is never
    presented as meaningful, per the brief.
  - ρ(causal effect, authority) = 0.16 for this state, 0.53 pooled across the
    8 audited states — the actual finding this tab exists to show: influence
    magnitude is not a reliable proxy for signed, task-directed authority.
    (Seed 17's own ρ is even lower than the pooled figure — an even sharper
    illustration of the point than the originally-used seed 15, whose
    near-zero authority values made the correlation nearly undefined.)
- **Top-k highlight:** switching between "Direct causal effect" and "Target
  authority" highlights (★, filled marker on the lattice, shaded row in the
  bars) the top 5 candidates by whichever metric is active — the set an
  actuator policy that greedily chose by that one criterion would pick. The
  two top-5 sets barely overlap, a direct, concrete demonstration of the
  ρ=0.16–0.53 correlation number.
- **Lattice positions/neighbors:** `interactive_demo/data/stage6_10_bundle.json`
  (same L=20/nn=400 regime). Positions/neighbors are a deterministic function
  of lattice size only (`flock_sim.lattice.lattice_positions(nn)`,
  seed-independent), so reusing them for a different episode's seed is valid,
  not a mismatch. Clicking any bird draws its structural neighbors (dashed
  lines), consistent with the same interaction in Tabs 1, 3 and 5.
- **Scope decision — 2-way toggle, not 3-way:** the brief asked for a
  predictive-relevance / causal-effect / target-authority toggle. No stored,
  per-candidate, purely observational ("what does bird j's state predict
  about the interior's future, absent intervention") score exists for this
  exact (seed, step, candidate-set) triple. The nearest candidate quantity,
  `_predictive_boundary`'s single-source validation "gains" dict
  (`stage6_10_emergence_adaptive_control/code/run_closed_loop.py`), is
  computed in-memory during closed-loop runs and never persisted per-candidate
  to a result file. Producing it here would mean replaying a fitting routine
  with **no stored endpoint to verify the replay against** — the brief's
  replay rule ("verify it against stored states/endpoints before using it")
  doesn't have a clean anchor for that quantity at this exact state, so it
  was left out rather than manufactured. The two toggles that *are* cleanly
  sourced already carry the tab's stated pedagogical point (prediction ≠
  causation ≠ useful control) via the causation-vs-authority contrast, which
  is the sharpest and best-evidenced one in the data. Tab 1 already covers the
  "prediction" side of the triad (its screening scatter *is* a
  predictive-relevance analysis) so the concept isn't missing from the demo
  overall, just not re-plotted as a third bar series here for a candidate set
  that doesn't have it on file.
- **No timeline:** by design (see brief section 8, "a clean fixed-interior
  Stage-6.10/reference state") — this is one fixed state with many candidate
  interventions compared against the same baseline, exactly like the science
  that produced it, not a multi-step trajectory.

## Tab 3 — Control

**Question:** Does interface structure matter when steering a known collective?

- **Source:** `interactive_demo/data/seed16__{method}__cw.json` — the same
  frozen V1/V2/V3 demo bundles the *original* interactive demo uses, built by
  `interactive_demo/data/export_scenarios.py` and independently checked by
  `verify_bundles.py`. Seed 16, target = clockwise turn (the majority target
  in `manifest.json`'s primary scenario set — 3 of the 9 methods' 3 targets).
- **9 methods, one shared interior:** the export script asserts
  `roles.core` and `timeline.identify` are identical across all 9 method
  files before use — one fixed interior, identified once at **t=6** (read
  from `timeline.identify`, not hardcoded), only the actuator-selection
  policy differs. `timeline = {start:0, identify:6, control_start:6,
  control_end:26, release_end:46, nt_total:46}`.
  - Primary selector (6): No Control, Random Exterior, Fiedler Boundary,
    Connected Patch, Sparse Interface Multicover ("Our Method"/V3, default),
    Full Dynamical Shell.
  - Under "+ more comparisons" (3): Distributed Shell, V2 Conservative Shell,
    and Direct Core Forcing (flagged diagnostic — bypasses the interface
    entirely, kept for contrast but visually marked ⚠, never presented as a
    real control arm).
- **Inspect behavior:** clicking an interior bird draws its structural
  neighbors (from the bundle's `neighbors` map) as dashed lines, reproducing
  the original demo's "which interface birds feed this one" interaction.
- **Ensemble comparison:** each method's `ensemble.success_probability`
  (already-computed replicate studies — e.g. V3's `v3_refinement/data/minimal_interface.json`,
  20 replicates — not re-run here) shown as a compact bar list so the single
  illustrated trajectory is clearly marked as illustrative, not the full
  evidence.
- **Not used:** the seed-2 "canonical flock" bundles
  (`interactive_demo/data/seed2__{no_control,sparse_interface_multicover,v1_best_pair}__cw.json`)
  were left out of Tab 3's UI to keep one dominant visual per the brief —
  they're cited in `README.md`'s source table as available, not wired into
  a second flock selector, since seed 16 alone already carries the "does
  interface structure matter" comparison across all 9 methods.

## Tab 4 — Collective landscape

**Question:** Which candidate regions actually look like coherent, individuated collectives?

- **C / G / L / D:** `interactive_demo/data/collective_landscape_bundle.json`
  → `snapshots["seed2_no_control"]` and `snapshots["seed2_disordered"]`
  (chosen for regime diversity), `candidates` column arrays
  (`C_internal, G_internal, L_blanket, D_local`, computed by
  `stage6_6_collective_landscape/code/metrics_66.py`). Every 2nd candidate
  kept (`SAMPLE_STRIDE=2`) → 1200 of the 2400 available across the two
  conditions (5000 exist per condition in the full, un-embedded dataset).
- **Q (clumpness) — post-hoc application of an existing frozen formula, not
  new science:** Q was never computed for the 6.6 candidate set — it's a
  Stage 6.10 Part F axis (`stage6_10_emergence_adaptive_control/code/morphology.py`,
  `Q_clump = P_min(area) / P_4(I)`, Harary–Harborth minimal polyomino
  perimeter). The export script imports that module directly and calls
  `morphology.q_clump(node_ids, L)` on the node-id sets already stored per
  6.6 candidate. No candidate, boundary, or other metric is regenerated —
  only a structural, already-validated, closed-form formula evaluated on
  already-frozen node sets. This is the one derivation step anywhere in v2
  that isn't a pure re-export, and it's explicitly sanctioned by the brief
  ("If a display quantity was not persisted... verify it against stored
  states/endpoints").
- **Curated examples:** picked programmatically from the real computed rows
  (compact clump: high C, max Q; coherent-but-hollow: high C & G, min D;
  snake-like: C>0.4 & n≥10, min Q; weak/noisy: min C among n≥6) — not
  hand-picked node ids. `illustrative_trajectories` in the same bundle
  independently contains a hand-labeled "Scattered-but-connected (diagonal
  snake)" example from the original science, cited in the provenance drawer
  as a cross-check that "snake" is a real, previously-recognized pattern
  here, not a v2 invention.
- **No single "thingness" score:** C, G, L, D, Q are kept as five separate
  axes throughout (axis dropdowns + a 5-row metric strip), never combined.

## Tab 5 — Adaptive

**Question:** What changes when the collective and its interface must be inferred online?

- **Source:** direct re-export of `interactive_demo/data/stage6_10_bundle.json`
  — already built by `stage6_10_emergence_adaptive_control/code/export_demo_data_610.py`
  for exactly this purpose. One representative 20×20 (L=20, 400 birds)
  closed-loop episode: seed 7, arm `adaptive_causal`, t0=60, horizon=24,
  16 release steps, 100 frames total.
- **Selection rule, disclosed, not re-derived:** "median final H among
  `adaptive_causal` conjunctive successes" (Part L's declared rule, applied
  by `run_release_clarity.py`, copied verbatim into the bundle's own
  `provenance.selection_note` — surfaced in v2's provenance drawer unedited).
- **Replay, already verified before this demo ever touched it:** the
  bundle's own `provenance.replay_note` states per-timestep headings were
  regenerated by a deterministic replay of the frozen simulator at the same
  seed/regime/action-sequence, with *every* replayed quantity (qualifying
  I0, H*(I_t) at all 24 control steps, final state/lineage, structural
  interface size at every step, all 16 release records) asserted equal to
  the original frozen result file. v2 does not re-run or re-verify this — it
  only re-serves the file, trimmed of the multi-episode `arm_summary` detail
  the UI doesn't need.
- **Phases** (`t_start` values read from the bundle, not guessed):
  unstructured 0–7, emergence 8–59 (blind detector proposes a candidate `I_t`
  every step from t=8, its affinity window), detected t=60 (the frozen,
  morphology-only qualifying I0 — no target heading or control outcome
  enters that choice), steering 60–83 (interior *and* interface both
  re-inferred online, `B_do`/`B_struct`/actuators reported per step),
  release 84–99.
- **Reference/oracle overlay (normally off):** an optional "no-control
  counterfactual" dashed line, from the bundle's own `no_control.H` — the
  same start state played with zero actuation. Off by default, toggled on
  via a checkbox in the metrics card, drawn in the dedicated oracle token
  color, never the default view.
- **Caveat kept in the provenance drawer, not the canvas:** `provenance.caveat`
  ("Illustration only. Not used for any aggregate claim.") and `task.scope_line`
  are surfaced only in the Data & caveats drawer, per the brief's "keep
  statistical caveats in a compact drawer, not the main canvas" instruction.

## Tab 6 — Translation

**Question:** Can the same online idea operate when the collective itself moves through space?

- **Source, per seed in {500, 501, 502, 503, 504}:**
  `stage6_11_translating_torus/data/viz_bundle_611__seed{seed}.json`
  (per-frame continuous positions `r`, discrete headings `z`, phase, interior,
  actuators, target heading, torus centre) merged with
  `online_control_611__seed{seed}.json` (event log: qualification/target
  time, per-control-step `B_pred`/`B_causal`/`B_C`, and
  `frac_interior_at_target`). N=400, L=24.0 for every seed.
- **This is the ORIGINAL Stage 6.11 v1 identity/readout**, per explicit
  instruction — not the later 6.11B audit, and not the separate, unrelated
  `identity_foundation/` tracker (an in-progress effort whose own
  `FRESH_CHAT_HANDOFF.md` records that its Phase 2 validation gate **failed**
  on the real 400-bird flock in all 5 tested episodes; it has no Phase 3
  visualization and was never a candidate source for this tab).
- **Per-seed event times** (`qualified_and_target_set` / `release_begin` /
  `episode_end`, read from each seed's own log, not assumed uniform):

  | seed | v1 outcome | qualify t | release t | final t |
  |---|---|---|---|---|
  | 500 | no turn | 61 | 84 | 108 |
  | 501 | turn* | 30 | 53 | 77 |
  | 502 | turn* | 30 | 53 | 77 |
  | 503 | turn | 35 | 58 | 82 |
  | 504 | no turn | 47 | 70 | 94 |

- **Geometry:** minimum-image torus wrapping,
  `torus_delta(a,b,L) = ((a-b+L/2) % L) - L/2` (`geometry_611.py`), used for
  the co-moving frame's recentering; the world frame plots raw `r` (already
  wrapped into `[0,L)` by the stored data).
- **Display-only compaction:** positions rounded to 3 decimals (torus side
  length 24.0 — sub-visual-pixel precision, no state invented); per-frame
  records restricted to the fields actually rendered. No interpolation
  between recorded timesteps.
- **The required footnote**, shown directly under the seed selector:
  > Original v1 readout. Later audit found 501/502 were not corroborated by
  > ID-independent turn measures; 503 was corroborated.
- **The required Data & caveats drawer text** for this tab:
  > Uses original Stage 6.11 v1 identity/readout for presentation. Original
  > v1 outcomes: 500/504 no turn; 501/502/503 turn. Later 6.11B audit found
  > only seed 503's physical turn was independently corroborated; this view
  > is therefore historical/exploratory, not a confirmatory control result.

  The 6.11B audit location (`stage6_11_translating_torus/audit/RESULTS_6_11B.md`,
  `FIVE_SEED_CAUSAL_ADJUDICATION.md`) is cited in the drawer as a path, never
  opened or summarized further in the UI — no v2/audit lineage detail is
  shown, per instruction.

---

## Omitted / simplified relative to the brief, and why

- **Tab 2's third ("predictive relevance") toggle** — omitted for this exact
  candidate set; see Tab 2 notes above. Predictive relevance as a concept is
  still covered by Tab 1's screening scatter.
- **Tab 3's seed-2 canonical flock** (`v1_best_pair` vs. V3 vs. no-control) —
  cited as available in `README.md`, not wired into the UI, to keep one
  dominant visual (brief section 3.D) with 9 methods on one shared interior
  already doing the comparative work.
- **Every historical/diagnostic V1–V3 rule and metric** — only the 9 methods
  already exported for the interactive demo are shown (6 primary + 3 under
  "more comparisons"); `direct_core_diagnostic` is visually flagged ⚠ rather
  than presented as a real controller, per the manifest's own
  `diagnostic: true` flag.
- **Stage 6.11's identity_foundation/ effort and the 6.11B audit's per-seed
  adjudication detail** — cited by path only, never rendered, per instruction
  ("Do not show v2 or turn this panel into the audit").
- **A single combined "thingness" score in Tab 4** — deliberately never
  computed; C/G/L/D/Q stay five separate axes throughout.

## Playwright QA — what was actually run

`src/pw_test.py` (Chromium, headless) against the committed `build/index.html`,
at three required viewports (1440×900, 1280×800, 1100×720) plus one
additional narrow check (700×800, below the tab-6 world/co-moving breakpoint):

- Loads the page fresh at each viewport; collects `console` `error`-level
  messages and uncaught `pageerror` exceptions for the whole session — **zero
  at every viewport**, both before and after fixing the two bugs found during
  QA below.
- Clicks through all 6 top-level tabs at each viewport; checks
  `document.documentElement.scrollWidth` never exceeds `clientWidth` — **no
  horizontal overflow at any viewport/tab combination**.
- Tab 1: steps the timeline forward, plays/pauses, drags the scrubber past
  the identification event, confirms the interior/B^D/B^F/B^pred overlays
  are absent before `t=identify` and present after (screenshot-verified).
- Tab 3: switches methods (6 primary chips), expands "+ more comparisons"
  (3 more chips appear, 9 total), confirms actuator overlays only render
  inside the control window and disappear after release.
- Tab 4: changes both axis dropdowns, clicks all 4 curated examples, confirms
  the thumbnail + 5-metric strip update to the selected candidate.
- Tab 5: steps through unstructured → emergence → detected → steering →
  release; confirms the process-strip highlight moves and the H* sparkline
  reveals only up to the current t (no future value visible at `t=0`);
  toggles the no-control reference overlay on/off.
- Tab 6: switches all 5 seeds; confirms world + co-moving frames render side
  by side at ≥1100px and the world/co-moving toggle correctly shows exactly
  one frame at 700px with no overflow; steps the timeline across the
  qualify/release events; confirms actuator/B^C rings only appear once
  `phase != "uncontrolled"`.
- Opens and closes the "Data & caveats" drawer from multiple tabs and
  confirms its content changes per tab (screenshot-verified for Tab 6's
  audit-caveat text specifically).
- End-to-end "Next →" chain clicked from Tab 1 through Tab 6, confirming the
  active tab advances each time and no Next button is offered on Tab 6.

**Two real bugs were found and fixed this way, not just theorized:**

1. `main.js` called `renderNextButton()` (which looks up `#nextRowContainer`)
   *before* the tab's own `render()` had created that element on first
   activation — the Next button silently failed to appear on a tab's first
   visit. Fixed by rendering the tab's content before wiring the Next row.
2. Every tab's own template originally included its own
   `<div id="nextRowContainer">`. Once two tabs had been visited, the
   document had two elements sharing that id, and
   `document.getElementById("nextRowContainer")` always resolved to the
   first one in the DOM (the first-visited tab's, now hidden) — so the Next
   button on every *subsequently* visited tab was being inserted somewhere
   invisible. Fixed by hoisting a single `#nextRowContainer` out of the tab
   panels into the shared app shell in `template.html`.

Screenshots taken during QA (`pw_shots/`) were used for visual review — no
labels cut off, no overlapping controls, triangle headings legible at all
three required widths, role colors stay distinguishable — and were deleted
afterward; they are not part of the deliverable.

---

## Round 2 refinements (post-review)

A second review pass asked for a specific set of fixes and additions, all
implemented against the same "reuse, don't reinvent" rule as the first pass.

- **Triangle spacing:** `drawBird` in `shared.js` shrank the apex/back-corner
  multipliers (1.35→1.12, 0.75→0.60, perpendicular 0.85→0.72) so two
  triangles facing each other across one lattice spacing show a visible gap
  instead of touching.
- **Playback controls moved to the lattice:** the single shared `footer#timeline`
  DOM node is now physically relocated (via `Viz.TL.bind`) into a
  `.timelineSlot` div rendered directly under each time-based tab's stage,
  instead of staying pinned to the page bottom. Tabs with no timeline (2, 4)
  park the node in a hidden `#timelineGraveyard` instead of destroying it.
- **Scanning / observation-window visualization, using real data, not a
  generic spinner:**
  - **Tab 1** auto-cycles (every 1.5s, only while `t < identify`) through a
    curated subset of the *same 20 real screening candidates* already used
    for the scatter plot — each has its own real `I` (proposed interior) and
    `B_hat_pred` (its fitted predictive boundary) from the 6.7 panel. Shown
    as dashed rings layered on top of (not replacing) the raw trajectory, so
    it reads as "candidates under test," never as the committed answer.
  - **Tab 5** already had a real, per-step rolling candidate interior during
    emergence (`emergence[t].I`, t=8..59, from the blind detector) — it just
    wasn't visually distinguished from a confirmed interior. It is now drawn
    with a pale fill and dashed stroke (`drawBird`'s new `dashed` option)
    during the `emergence` stage only; the same region switches to solid,
    full-color fill the instant it becomes the frozen, detected I0 at t=60.
- **Click a boundary on Tab 1's scatter to see it on the lattice:** each of
  the 20 real screening candidates has its own `I` and `B_hat_pred` (see
  above) — clicking a scatter point now previews that specific candidate's
  interior and boundary as dashed rings over the real trajectory (not
  replacing the committed view — both are visible at once, so "different
  candidate boundaries over the same observed collective" is literal, not
  metaphorical). A banner names the candidate and offers a Clear button.
  Verified to show visibly different shapes (e.g. `diagonal_snake_pathology`
  reads as a scattered diagonal line, `highest_C` as a tighter blob).
- **Click-to-inspect neighbors, generalized:** previously only Tab 3's
  interior birds were clickable. `Viz.drawNeighborLines` is now a shared
  helper and every tab with a static lattice + neighbors map (1, 2, 3, 5)
  makes every bird clickable, not just interior ones. Tab 6 (continuous,
  moving positions) gets its own `continuousNeighbors()`: a torus-aware
  radius lookup (2.4 units, ~2 layers at this density) computed on demand
  from the already-provided per-frame positions — a geometric query, not new
  science — rendered in the co-moving frame only (world-frame wraparound
  would make straight connecting lines visually misleading).
- **Tab 2 per-interior-bird causal-effect breakdown, better example seed, and
  top-k highlighting:** see the Tab 2 section above for the full account
  (new seed 17, replayed real headings, `do_influence`'s previously-discarded
  per-target breakdown, ★ top-5 highlighting on toggle).
- **Tab 3 bird-steps comparison:** a new card bars `summary.bird_steps`
  (actuator-count × control-duration, already computed by the frozen
  scenario export — not recomputed) across all 9 methods, so cost is visible
  alongside the existing success-probability ensemble bars.
- **Tab 4 candidate thumbnails now show real headings and the boundary, and
  each archetype shows 3 examples, not 1:**
  - `prep_tab4_landscape.py` now also exports `representative_z` (a real,
    already-stored 100-bird heading snapshot per seed/condition — shared by
    every candidate drawn from that snapshot, since candidates differ only
    in which nodes are proposed, not in a separately simulated heading
    state) and each candidate's own `boundary_ids` (column `B`, already in
    the source bundle, previously not exported).
  - Thumbnails (both the main "Selected candidate" card and the new mini
    example strip) now draw triangles with real headings and ring the
    candidate's boundary nodes, consistent with every other tab's glyph
    language, instead of bare dots.
  - `pick_n()` replaces the old single-`pick()`: each archetype (compact
    clump / coherent-but-hollow / snake-like / weak-noisy) now surfaces its
    top 3 real matches, preferring (seed, condition) diversity among the
    matches, drawn from seeds 2, 3 and 4 (previously seed 2 only) across
    three conditions. Clicking a category renders all 3 as clickable mini
    thumbnails next to each other, so the "how do these vary visually"
    comparison the brief asked for is literal and side by side.
- **Tabs 5 and 6: "entered this step" / "left this step" restored.** Both
  tabs already carried the necessary data (a full interior-membership list
  every frame) but weren't diffing consecutive frames. `Viz.membershipDiff`
  is a plain set-difference between frame t-1's and frame t's interior list
  — no new inference — rendered as a teal halo (entered, matching the v1
  demo's own "recruited" color) or an amber ring (left; deliberately moved
  off violet after round-1 QA showed it collided visually with the B^C
  interface ring color) for exactly one frame, the one where the transition
  happened.
- **Tab 6 target-heading-fraction trace bug fixed:** `prep_tab6_translation.py`
  only collected `frac_interior_at_target` from `control_step` log events;
  `release_step` events carry the same field (confirmed in the raw
  `online_control_611__seed*.json` logs) and were being silently dropped, so
  the trace visually stopped at the control/release boundary. Both event
  types are now collected. Verified on seed 503 (the one corroborated "turn"
  seed): the trace now rises continuously through the whole control+release
  span instead of cutting off at the control boundary.
- **Target-heading indicator moved off the lattice, and time-gated:** Tabs 2,
  3, 5 and 6 previously drew a green circle+arrow directly on top of the
  lattice's top-right corner, overlapping birds there. It is now a dedicated
  `.targetBadge` card in the side column. For Tabs 3 and 5 (where the target
  is fixed as part of the scenario but shouldn't be visible before the
  observer would actually know it), the badge is hidden until
  `t >= control_start` / `t >= t0` respectively, matching the "no hindsight"
  rule already applied to interior/boundary overlays. Tab 6's badge was
  already correctly data-gated (`frame.target_heading` is `null` until the
  v1 detector's `qualified_and_target_set` event) and just moved to the side
  panel. Tab 2 has no time axis, so its target badge is static by design.
- **Direct causal effect is a 1-step quantity, target authority is multi-step
  (τ≥2) — now stated explicitly in the UI**, not just the provenance drawer:
  the Tab 2 mode toggle button reads "Direct causal effect (1-step)" and the
  tooltip/breakdown copy repeats it. `reference_truth.do_influence` computes
  `_next_dist`, the *exact one-step* next-heading marginal — there is no
  multi-step causal-effect quantity in this codebase; multi-step effects are
  only ever expressed through target authority A_j^{h*,τ}.
