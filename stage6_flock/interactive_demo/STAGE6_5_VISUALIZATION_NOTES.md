# STAGE6_5_VISUALIZATION_NOTES.md

Documents the redesigned `Inference & Identity` mode (graph-first, per the
2026-09-07 redesign request) and the regressions repaired in the Control
view before that redesign started. Does not modify any frozen scientific
result file — everything here is presentation tooling reading already-saved
`stage6_5/{boundary_inference,refinement/*}/data/*.json`, or deterministic
re-derivations of already-frozen quantities (see Part 4 below).

## Part 0 — regressions repaired in the Control view

Diagnosed by diffing the current `app/index.html` against the last
git-committed version (`git show HEAD:.../app/index.html`) and screenshotting
both with Playwright/Chromium at 1440x900, 1280x800, and 1024x768.

**Found and fixed**: `#refinementView { display: flex; ... }` (the Stage
6.5 mode container) has an explicit `display` property in its own ID rule,
which — per ordinary CSS specificity — **beats** the browser's built-in
`[hidden] { display: none }` rule (an ID selector always outranks a bare
attribute selector). The container was therefore rendering (and claiming
half the vertical flex space) even while marked `hidden`, visibly
squeezing the Control page's lattice and sidebar into a fraction of their
intended size. Fixed by adding an explicit `#refinementView[hidden] {
display: none; }` override — the same pattern already used correctly
elsewhere in the file (e.g. `#main[hidden]`).

No other regressions were found: header wrapping behavior, card widths,
legend, timeline, compare view, and the info modal were confirmed pixel-
equivalent (modulo the intentional new top nav row) to the pre-Stage-6.5
baseline at all three viewports.

**Namespacing**: every Stage-6.5-specific CSS rule now lives under a single
`.inference-identity` class (the redesign's container), except `#iiTooltip`
and `#main[hidden]`/`#refinementView[hidden]`, which are deliberately *not*
namespaced because they target elements appended to `document.body` or
existing outside `.inference-identity` — see the inline comment in
`index.html` at each of those rules for why.

## Part 0.5 — a tooltip bug the redesign introduced, then fixed

While testing the redesign, `#iiTooltip`'s CSS was originally written as
`.inference-identity .iiTooltip { position: absolute; ... }`. Because the
tooltip `<div>` is created and appended directly to `document.body` at
runtime (not inside `.inference-identity`), that rule never matched —
the tooltip rendered as a static block element and was pushed off-screen
by ordinary document flow. **Every hover tooltip on every one of the four
tabs was silently non-functional** until this was caught by checking
`getComputedStyle(...).position` in a Playwright script (the bug was
invisible to a plain screenshot diff, since the tooltip's *absence* looks
identical to "no tooltip shown yet"). Fixed by de-namespacing that one
rule to a bare `#iiTooltip { ... }` (the id is already unique, so no
scoping was needed). A second, unrelated genuine bug was caught the same
way: `.iiBtn:hover:not(:disabled)` had higher CSS specificity than
`.iiBtn.active` (the `:not()` pseudo-class inflates specificity), so an
active button that was also being hovered — exactly what
`Playwright.click()` leaves behind — rendered with identical text and
background color (invisible text). Fixed by adding `:not(.active)` to the
hover selector.

## Part 1 — navigation

Top-level nav is exactly `Control | Inference & Identity | Info`, no
additional top-level pages. `Inference & Identity` has four tabs:
**1. Predictive Boundary, 2. Causal Stress Test, 3. Prediction vs Control,
4. Collective Identity**. The Control page's own method dropdown/timeline
were not touched.

## Part 2 — shared rendering primitive

`drawIILattice(svg, opts)` (in `app/index.html`) is a new, dedicated
lattice-drawing function reusing the Control page's exact visual
conventions (node size formula, arrow-per-heading, halo rings, glow,
tooltip-on-hover) via the same `iiXY()` position formula as the Control
page's `birdXY()`, but parameterized by an arbitrary per-bird `roleFn(id)`
instead of the Control page's fixed Core/Shell/Fiedler/Exterior `classify()`
— because each Inference & Identity tab needs a richer, tab-specific role
vocabulary (inferred/omitted/recruited/actuator/etc.) that the original
function was never designed for. It was written as a sibling function
rather than a refactor of `renderLattice()` itself, to avoid any risk to
the proven, working Control-page renderer while building four new,
differently-parameterized views.

## Part 3 — data flow

- `interactive_demo/data/export_refinement_bundle.py` → `refinement_bundle.json`
  — aggregate tables (unchanged from the prior visualization pass), used
  only inside each tab's collapsible "Full statistics" `<details>` section.
- `interactive_demo/data/derive_refinement_viz_data.py` → `refinement_viz_data.json`
  (**new**) — the lattice-ready data each tab's graph is actually built
  from. `app/build.py` inlines both, plus the existing scenario bundles,
  into `build/index.html` under three placeholders
  (`__DEMO_DATA__`/`__REFINEMENT_DATA__`/`__REFINEMENT_VIZ__`).

Rebuild sequence (unchanged in spirit, one more step):
```
cd data && python3 export_scenarios.py && python3 verify_bundles.py
python3 export_refinement_bundle.py
python3 derive_refinement_viz_data.py
cd ../app && python3 build.py
```

## Part 4 — provenance of `derive_refinement_viz_data.py`'s fields

Every number in `refinement_viz_data.json` is either read verbatim from an
already-frozen `stage6_5/refinement/*/data/*.json` file, or **deterministically
reproduced** by calling already-frozen functions (`find_flock`,
`dynamical_shell`, `min_actuators_for_multicover`, the identity
`definitions.py` tracks, the closed-form `exact_intervention` propagator,
`validity_guard.retrospective_guard`) with the exact seeds/arguments the
frozen drivers already used. No inference procedure, controller, or
threshold was re-run with different settings; nothing was re-optimized to
look better. Field-by-field:

| Tab | Field | Source |
|---|---|---|
| shared | `lattice.positions`/`.neighbors` | `flock_sim.lattice.Lattice(nn=100, nh=8)` — identical for every flock in this port (the physical lattice never moves), computed once |
| 1 | `canonical.{I0,B_D}`, `membership` | `boundary_inference/data/bootstrap_membership.json` (canonical flock, seed 2), verbatim |
| 1 | `canonical.B_hat`, `.precision/.recall/.excess_loss` | `boundary_inference/data/dev_sweep.json`'s frozen row at `delta_tol_frac=0.05`, seed 2 (PROTOCOL_6_5.md's own table) — used instead of `bootstrap_membership.json`'s own point estimate (which can differ by ±1 member, a different but equally real run) so the graph and the metric card describe the *same* concrete set |
| 1 | `canonical.z_t0` | `find_flock(2)["z_t0"]` — the flock's own frozen identified state, re-derived deterministically (never persisted to disk by the frozen pipeline) |
| 1 | `held_out[]` | `boundary_inference/data/held_out_evaluation.json`, verbatim |
| 1 | `sample_efficiency.rows[]` (incl. per-N `B_hat`) | `boundary_inference/data/sample_efficiency.json`, verbatim (canonical flock only, per Stage 6.5's own scope) |
| 2 | `examples.{omitted_shell,included_shell,non_shell}` | Re-derived by calling `exact_intervention` on the SAME 30 checkpoint states `causal_redundancy`'s frozen driver generated (same seed offset), then taking the **single largest** `D_j^do` within each class — a pre-specified, non-cherry-picked selection rule, labelled "representative high-effect intervention" in the UI per the task's own instruction |
| 2 | `delta_shift_by_class` | `causal_redundancy/data/causal_redundancy.json`, verbatim (class-level means) |
| 3 | `rows[].{B_D,B_hat,arms}` | `control_generalization/data/four_controller_comparison.json`, verbatim |
| 3 | `rows[].I0`, `.z_t0` | `find_flock(seed)`, re-derived deterministically per discriminating flock (the frozen file only stored `n_I0`, a count, not the member list) |
| 3 | `summary` | `control_generalization/data/aggregate_summary.json`, verbatim |
| 3 | `m_i(A)` (redundant-support overlay) | Computed client-side in JS from `I0`/`neighbors`/the current arm's `actuators` — a pure counting function, not a new experiment |
| 4 | `z_hist`, `tracks.{M,L,F,F_guard}` | Regenerated by calling `identity_stability.run_identity_stability.run_controlled_episode` (frozen formula, seed = `CONTROLLED_SEED_OFFSET + 1000*2 + 0`) — **flock 2, replicate 0**, the first replicate of the already-frozen Part-C5 5-flock re-evaluation, not cherry-picked. The controller forces the TRUE `B^D_0` regardless of identity lens, so **the physical trajectory is identical across all four lenses** — exactly the "same world, different lens" property the redesign needed, and it is Stage 6.5's own Part-4/C5 experimental design, not a new one. `F_guard` uses the already-frozen `validity_envelope.json`'s `F` envelope. |
| 4 | `validity_envelope_F` | `identity_stability/data/validity_envelope.json`, verbatim |

**Why replicate 0 of flock 2 is the identity example, and not a search over
all replicates for the "best" collapse**: it is the first (index 0) of 8
frozen replicates, a rule fixed before looking at any of them. It happens
to show an unusually complete collapse (functional definition shrinks to
exactly 1 bird, `R_0=0.05`) — more dramatic than the 8-replicate mean
(`mean_final_size=1.2`), so the UI explicitly labels it "Representative
documented failure case" per the task's own labelling instruction, rather
than implying it is the typical outcome.

**Why the "Lineage" lens uses the *original* (unregularized) `lineage_track`,
not the C2 temporally-regularized version**: `identity_stability`'s own
results found no `lambda_T` that cleanly separated jitter from genuine
transitions, and the regularized track actively mis-tracked during
*active control* specifically because it was calibrated only on *passive*
baseline data. Presenting the regularized version as if it were a working
default would misrepresent that finding. The tab instead shows the original
lineage definition (matching Stage 6.5's own Part 3/4), with a short,
honest note that the regularization attempt did not produce a clean fix —
detailed in the collapsible Details panel and in `identity_stability/IDENTITY_STABILITY_RESULTS.md`.

**Why the validity guard toggle is only enabled for "Functional"**: the
guard (`validity_guard.py`) and its calibrated envelope were built and
evaluated specifically against the functional definition's observed
collapse pathology (Part C3/C4). No comparable envelope was calibrated for
plain Lineage, so offering the toggle there would either silently do
nothing or apply an envelope calibrated for a different track — the toggle
is disabled (not silently ignored) for Material/Lineage, with a tooltip
explaining why, per the task's explicit "unavailable controls disabled
rather than silently ignored" requirement.

## Part 5 — admission of Part B (control generalization)

The "Prediction vs Control" tab's across-flocks banner reports the negative
finding plainly (inferred boundary did **not** outperform matched-budget
random control on the frozen 12-flock benchmark) rather than omitting it or
softening it — consistent with `CONTROL_GENERALIZATION_RESULTS.md`'s own
verdict and the task's instruction not to claim random is better than it
demonstrably is, nor to hide an informative negative result.

## Browsers/viewports tested

Playwright + Chromium (locally extracted `.deb` shared libraries, no root
required — this sandbox has no system Chromium dependencies installed and
no passwordless sudo; Playwright/Chromium and the extracted libraries are
session-local development tooling only, **not** shipped with or required by
`build/index.html`, which remains a plain static file). Tested at 1440x900,
1280x800, and 1024x768 (desktop presentation sizes plus one narrower
laptop size). Console/page-error listeners were attached for every state
tested; zero errors were observed in the final build across all three
viewports and all twelve captured states (Control page, both Predictive
Boundary reveal states, IDs-label + N=5 sample view, expanded Details, both
Causal Stress Test perturbation states, both Prediction vs Control arms,
both Collective Identity lens/guard states, and the Info modal's new tab).
