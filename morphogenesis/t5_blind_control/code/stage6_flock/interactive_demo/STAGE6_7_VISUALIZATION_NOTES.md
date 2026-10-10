# STAGE6_7_VISUALIZATION_NOTES

Scope: the "Boundary source: Oracle / Inferred" toggle added to the existing
Collective Landscape tab's Explore mode (task brief section 18), for the 300
candidates in Stage 6.7's own panel. Mirrors `STAGE6_6_VISUALIZATION_NOTES.md`'s
format at reduced scope, since this is a small, additive change to one
existing tab rather than a new tab.

## 1. Data flow

Own generator, own bundle, own placeholder — the established "each pipeline
owns one file" convention (`STAGE6_6_VISUALIZATION_NOTES.md` Part 1):
`stage6_7_blind_boundary/code/export_demo_data_67.py` reads
`data/{oracle_validation_panel,blind_landscape_panel,causal_discovery_panel,
sample_efficiency}.json` and writes `interactive_demo/data/stage6_7_bundle.json`
(261 KB, all 300 candidates embedded directly — no subsampling needed, unlike
Stage 6.6's 5000/snapshot landscape). Inlined via a 5th placeholder,
`/*__STAGE67_DATA__*/` → `window.STAGE67_DATA`, added to `app/build.py` and
`app/index.html` without touching the existing four.

## 2. UI

Inside `renderLsExplore()`'s single-candidate (non-compare) branch only —
the two-candidate compare view is unchanged, still oracle-only. When
`window.STAGE67_DATA` exists and the selected candidate's id is found in it
(`ls67Entry`), a "Boundary source: Oracle interaction shell / Inferred from
trajectories" button pair appears above the lattice. Selecting "Inferred"
switches the lattice's `roleFn` to `lsRoleFn67`, which colors by
`Bhat^pred`/`Bhat^causal`/both, and reveals a "Reveal oracle shell" checkbox
that, when checked, also outlines true-shell members missed by both
(`role: oracle_missed`). A new metric card (`lsInferredMetricCardHtml`)
shows Δℓ, structural Jaccard (predictive and causal), boundary sizes, and
the A/B/C/D outcome label. If "Inferred" is selected for a candidate NOT in
the 300-candidate panel, a note explains the fallback and the oracle
boundary is shown instead (verified live, see Part 3).

## 3. Testing

Headless Chromium via Playwright (`chromium-1243` + the extracted-`.deb`-
libs workaround, same as Stage 6.5/6.6's own QA passes — see their notes for
the setup detail), 1440x900/1400 viewport, `build/index.html` opened via
`file://`:

- Landscape tab loads (`#iiLsBody` visible).
- Both boundary-source buttons present for the default-selected candidate
  (established `I0`, always in-panel); clicking "Inferred" then "Reveal
  oracle shell" then back to "Oracle" all work with **zero console/page
  errors**.
- Screenshot confirms correct role coloring: interior (blue), inferred
  causal (red, the large majority — matches `RESULTS_6_7.md`'s finding that
  the causal interface is much larger than the predictive one), the single
  candidate with both, and no purple ("true shell, missed by both") circles
  for this candidate — consistent with the causal method's exact recovery
  (nothing is ever missed by both, aggregate count 0/8230+507+1).
- Selecting a scatter point outside the 300-candidate panel while
  "Inferred" is active correctly shows the fallback note.

Not (re-)tested: the pre-existing Stage 6.5/6.6 tabs' own behavior (owned by
their own QA artifacts), and the two-candidate compare view (intentionally
left oracle-only, out of scope for this toggle).

## 4. Known simplification

The toggle only affects the single-candidate Explore view. The compare view,
the sweep-grid view, and Control mode are unchanged — a deliberate scope
limit (task brief section 18 asks for the toggle "inside Collective
Landscape → Explore", not a rework of every view).
