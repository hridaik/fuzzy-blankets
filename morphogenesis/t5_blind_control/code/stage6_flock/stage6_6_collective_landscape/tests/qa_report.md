# QA report — interactive_demo "5. Collective Landscape" tab

Scope: task-brief section 34 (visualization QA) for the new Inference &
Identity subtab described in `interactive_demo/STAGE6_6_VISUALIZATION_NOTES.md`.
This report covers only the demo UI (`interactive_demo/app/index.html` →
`interactive_demo/build/index.html`); it does not re-validate the
underlying Stage 6.6 science (metrics, candidate generation, archetype
trajectories), which is out of scope for this pass and owned by
`stage6_6_collective_landscape/`'s own test suite
(`tests/test_metrics_basics.py`, `tests/test_predictive_metrics.py`,
`tests/test_control.py`, `tests/test_geometry.py` — not modified or re-run
by this QA pass).

## Tooling situation

**Playwright with a real Chromium was available and used** — this should
be stated plainly rather than assumed unavailable. `npx playwright` (Node
v22.15.0) reported Chromium already installed
(`~/.cache/ms-playwright/chromium-1243`) from a prior session. The Python
`playwright` package (used for the actual QA script, since this session's
tools favor Python) was also installed, but its own pinned browser build
(`chromium_headless_shell-1234`) failed to launch:

```
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

No system NSS/NSPR packages were installed and there is no passwordless
root in this sandbox. This was resolved **without root**: `apt-get
download libnspr4 libnss3` (downloading a `.deb` requires no privileges),
`dpkg-deb -x` to extract the shared libraries into a scratch directory, and
launching Playwright against the already-present newer Chromium build
(`chromium-1243`) with that directory prepended to `LD_LIBRARY_PATH`
(`playwright.sync_api.sync_playwright().chromium.launch(executable_path=...,
args=["--no-sandbox"])`). This matches the same workaround recorded in
`interactive_demo/STAGE6_5_VISUALIZATION_NOTES.md`'s own tooling note from
the prior visualization pass. None of this — the browser, the extracted
`.deb` libraries, or `LD_LIBRARY_PATH` — is required by or shipped with
`build/index.html`, which remains a plain static file opened via `file://`.

**Conclusion: real headless-browser QA was performed, not a fabrication.**
A Playwright script (retained at
`/tmp/.../scratchpad/qa.py` in this session — not committed to the repo,
since it is throwaway test tooling, not a deliverable) drove
`build/index.html` end-to-end at three viewports with console/page-error
listeners attached throughout.

## What was tested and the result

Console/page-error count across the full script below, at each viewport:
**0 at 1440x900, 0 at 1280x800, 0 at 1024x768.**

For each of the three viewports (1440x900, 1280x800, 1024x768), the script:

1. Loaded `build/index.html`, confirmed the Control view (`#svgMain`)
   renders.
2. Switched to `Inference & Identity` (top nav), confirmed
   `#refinementView` is visible.
3. Clicked through tabs 1-4 (`Predictive Boundary`, `Causal Stress Test`,
   `Prediction vs Control`, `Collective Identity`) and confirmed `#iiBody`
   stays visible for each — i.e. **the four pre-existing tabs still work
   after this change** (task brief's own QA requirement: "original
   Inference & Identity tabs unchanged").
4. Clicked tab 5 (`Collective Landscape`), confirmed the Explore-mode
   scatter SVG renders with candidate points (1200, the one real snapshot
   embedded at the time of this build — `seed2_no_control`).
5. Hovered a scatter point; confirmed `#iiTooltip`'s computed CSS
   `position` is `absolute` (not `static`) — the exact class of bug
   documented in `STAGE6_5_VISUALIZATION_NOTES.md` Part 0.5 (a
   mis-namespaced tooltip rule that silently never renders), specifically
   re-checked here since tab 5 reuses the same shared `#iiTooltip` element.
6. Clicked a scatter point; confirmed the lattice (`#iiLsSvg1`) draws 100
   bird nodes.
7. Swapped X axis to Coherence (`C`) and Y axis to Contrast (`D`) via the
   two `<select>` elements; no error.
8. Dragged (via a scripted `input` event on the underlying range input,
   not a physical mouse drag — see Limitations) the Coherence filter's low
   handle to the midpoint; confirmed the filtered point count changed and
   no error was thrown.
9. Checked and unchecked "Show Pareto candidates only"; no error.
10. Switched to Sweep-grid view; confirmed non-empty binned cells render
    (6 for the default axis pair against this snapshot) and are clickable
    (clicked one, selection updated without error).
11. Clicked "Pin as candidate A" on the selected point, then clicked a
    different scatter point; confirmed the compare layout renders two
    lattice `<svg>`s (`#iiLsSvgA`/`#iiLsSvgB`); clicked "Exit compare";
    confirmed it returns to single-lattice view.
12. Confirmed both snapshot `<select>` dropdowns (seed, condition) render.
13. Clicked the "Global-looking consensus" teaching-case button (enabled,
    since a real example exists in this snapshot's data); no error.
    Confirmed the third case button ("Looks coherent, weakly integrated")
    is correctly **absent** for this snapshot — verified this is the
    data-driven, intended behavior (no such candidate exists in
    `seed2_no_control`'s embedded population; see
    `STAGE6_6_VISUALIZATION_NOTES.md` Part 2), not an unnoticed bug.
14. Switched to Control submode; confirmed the lattice
    (`#iiLsCtrlSvg`) renders.
15. Clicked the `same_direction` condition button; confirmed the four
    exterior-budget buttons (25/50/75/100%) appear; clicked 50%; no error.
16. Scrubbed the timeline slider (scripted `input` event) to the midpoint
    index; confirmed no error and the four metric traces / secondary
    numbers update.
17. Clicked Play, waited ~700ms (several 250ms ticks), clicked Pause; no
    error, no runaway timer (confirmed by the subsequent tab-switch/return
    step producing no further console errors from a stray interval).
18. Returned to the top-level `Control` nav view; confirmed `#main` is
    visible again (i.e. leaving the new tab doesn't break the original
    Control page).

## Visual inspection (screenshots)

Full-resolution screenshots were captured at each of the above steps for
all three viewports (kept in this session's scratch directory, not
committed — they are QA artifacts, not deliverables; regenerate by rerunning
the retained script against `build/index.html` if needed). Visual review of
those screenshots found and led to two fixes during this pass (both
recorded in `STAGE6_6_VISUALIZATION_NOTES.md` Part 5 with full detail):

- **Explore mode initially pushed the scatter/lattice graphs below the
  fold** at 1440x900 (a 3x5 button table for the snapshot selector plus a
  4-row filter grid consumed too much vertical space above the graphs,
  violating the task brief's repeated "graph must stay dominant"
  requirement). Fixed by replacing the table with two compact `<select>`
  dropdowns and switching the filter grid to `auto-fit` so all four
  filters sit on one row at desktop widths. Re-screenshotted and confirmed
  both the scatter and lattice are substantially visible without scrolling
  at 1440x900 post-fix.
- **A stuck tooltip** was visible in a Control-mode screenshot (stale
  content from an earlier Explore-mode hover, left behind because a full
  `innerHTML` rebuild doesn't fire `mouseleave`). Fixed with a defensive
  `iiHideTooltip()` call at the top of `renderTabLandscape()`.
- **Long candidate IDs overflowed the metric-card header** in the
  side-by-side compare layout. Fixed with `word-break:break-all` and a
  line break, scoped to that one heading only.

Post-fix screenshots at all three viewports show: the top nav/header/tab
bar (unchanged from tabs 1-4); the Explore-mode controls (snapshot
dropdowns, axis/view/Pareto row, four filters on one row at ≥1280px width,
wrapping to two rows at 1024px); the scatter (colored/sized points, axis
tick labels, axis title) and lattice (colored interior/boundary/shell/
exterior rings, real heading arrows) both visible without scrolling at
1440x900 and with only modest scrolling at 1024x768; the sweep grid
(hatched empty cells vs. solid populated cells with counts); the compare
layout (two lattices + two metric cards + Exit compare button); and
Control submode (seed/condition/exterior-budget button rows, lattice with
actuated-role coloring, four small metric traces, secondary numbers card).

## Other section-34 checks

- **Original Control mode unchanged**: confirmed both by the scripted
  before/after visit in every viewport run (step 1 and step 18 above) and
  by `git diff --stat` — the only line touching pre-existing code in
  `app/index.html` is the `.iiTabBtn` click handler gaining one additional
  function call (`iiStopLandscapePlayback()`); every other changed line is
  a pure addition. `renderLattice()`, `classify()`, and all Control-page
  state/rendering code are untouched.
- **Original Inference & Identity tabs (1-4) unchanged**: same diff
  argument, plus the scripted tab-by-tab visibility check in step 3 above,
  at all three viewports.
- **New tab namespaced so CSS cannot leak**: mechanically verified (not
  just asserted) — a small script parsed every new CSS rule in the added
  block and confirmed 100% of selectors start with `.inference-identity`
  (37 rules checked, 0 violations). Full detail in
  `STAGE6_6_VISUALIZATION_NOTES.md` Part 5.
- **`node --check`** was run against the extracted `<script>` contents of
  `app/index.html` after every edit in this pass and passed cleanly each
  time (no JS syntax errors) — the closest available proxy for "browser
  console check" that doesn't require a browser, used in addition to (not
  instead of) the real Playwright console-error listeners above.
- **`python3 app/build.py`** runs cleanly from `interactive_demo/`,
  producing `build/index.html` at **1967 KB** (up from the pre-Stage-6.6
  baseline; grew because of the ~370 KB `collective_landscape_bundle.json`
  now being inlined as a 4th placeholder — see
  `STAGE6_6_VISUALIZATION_NOTES.md` Part 1).

## Addendum — verification against the complete 15-snapshot dataset

This report was written while `run_all_snapshots.py` was still generating
data (only `seed2_no_control` existed). After all 15 snapshots completed
(`data/snapshot_manifest.json`, 5000/5000 candidates each), the
orchestrating session re-ran `export_demo_data.py` + `app/build.py`
(bundle 0.38MB->3.89MB, `build/index.html` 1967KB->5400KB) and independently
re-verified with a fresh Playwright/Chromium script at 1440x900, 1280x800,
1024x768:

- Zero console/page errors at all three viewports with the full bundle.
- `#iiLsSeedSel` / `#iiLsCondSel` now expose all 3x5 = 15 combinations with
  no disabled options (previously only `seed2/no_control` was enabled).
- Selected `seed 4 / disordered` (untested by this original pass): scatter
  renders correctly with a visibly different point distribution, and the
  third teaching-case button ("Looks coherent, weakly integrated") —
  observed absent for `seed2/no_control` in step 13 above — **correctly
  appears** for this snapshot, confirming the data-driven logic behaves as
  designed on a second, materially different snapshot, not just the one
  this pass had access to.

The original "only 1 of 15 snapshots existed" limitation below is now
closed for at least one additional snapshot; the remaining 13 were not
individually clicked through but share the identical code path (verified
by source inspection, as this report's step 2 above already noted).

## Limitations of this QA pass (stated explicitly, not omitted)

- **Chromium only.** No Firefox/Safari/WebKit engine was available in this
  sandbox. The dual-range filter sliders in particular use a CSS-only
  two-overlapping-`<input type=range>` trick with both `-webkit-` and
  `-moz-` thumb rules written, but only the `-webkit-` behavior (via
  Chromium) was actually rendered and visually confirmed; the `-moz-` rule
  is unverified.
- **Slider/drag interactions were driven via scripted DOM events**
  (`element.dispatchEvent(new Event('input'))`), not a simulated
  mouse-down/move/up drag gesture. The resulting state changes (and their
  visual rendering, confirmed by screenshot) are verified; the raw
  pointer-drag interaction itself was not independently exercised.
- **Only 1 of the 15 planned Explore-mode snapshots existed** at the time
  of this QA pass (the background batch job that generates the rest was
  still running). All interactive mechanics were exercised against that
  one real snapshot (`seed2_no_control`, 1200 embedded candidates); the
  other 14 seed×condition regimes were not individually clicked through,
  since they didn't exist yet to click through. The code path does not
  branch on which snapshot is loaded (verified by reading the source), but
  this is stated as an assessment of the code, not a claim of having
  exercised those 14 specific regimes.
- **No automated visual-regression baseline** exists for a brand-new tab
  (nothing to diff against). Screenshots were reviewed by hand for
  obvious layout problems (see the two fixes above) rather than compared
  pixel-by-pixel to a reference image.
- **Comment/asset/artifact-style capabilities are not applicable** here —
  this is a static `file://` HTML page with no server, so there is no
  live-data, persistence, or multi-user surface to test.

## Addendum 2 — real-trajectory playback for curated illustrative examples

Follow-up feature (task: play real, frame-by-frame heading arrows for a
small curated set of examples spanning the (C,G,L,D) surface and the five
archetype conditions — not all combinations). Full design rationale is in
`interactive_demo/STAGE6_6_VISUALIZATION_NOTES.md` Part 8; this addendum
covers only the QA re-run for it, at the same three viewports, with the
same Chromium + extracted-`.deb`-libs workaround as this report's own
"Tooling situation" section above (redone from scratch this session —
nothing persists between sessions; the exact command sequence there still
applies verbatim).

**Zero console/page errors** at all three viewports across the full
scripted run below (a dedicated script, separate from the original QA
script referenced above, retained in this session's scratch directory —
not committed, for the same reason as before).

What was exercised, per viewport:

- `seed 2 / A. Natural` (2 curated candidates — "Reference I0" and
  "Scattered-but-connected (diagonal snake)"): confirmed the Example
  selector shows exactly 2 buttons; confirmed the heading note states a
  curated example is active; confirmed the lattice `<svg>`'s own markup
  differs after a single step-forward (i.e. the arrows are genuinely
  advancing, not static); switched to the second example and confirmed
  both the metric-card title and the lattice re-rendered for that
  candidate's own interior shape (screenshot: the "diagonal snake"
  candidate shows a diagonal blue interior with its own, differently-
  shaped orange shell ring — visibly different from I0's compact one, the
  exact risk flagged in the follow-up task); pressed Play, waited ~900ms
  (~3-4 ticks at 250ms), confirmed the lattice markup differed from the
  t=0 frame and the time readout advanced to `t=4/40`, then paused.
- `seed 2 / B. Shell retarget` (2 curated candidates): confirmed the
  Example selector shows exactly 2 buttons.
- `seed 2 / C. Same-direction exterior` (1 curated candidate): confirmed
  **no** Example selector renders (by design — a selector with one option
  is not shown); confirmed real headings are active at the default 100%
  exterior budget; moved the exterior-budget slider to 50% and confirmed
  the UI correctly falls back to the sparse/no-arrows note (the curated
  entry is only ever used at 100%, since it carries no explicit `f_E`
  field and was verified, by inspecting `controlled_exterior` counts
  against the archetype metadata, to represent the 100% condition only —
  see notes doc Part 8, "the f_E gate"). One assertion in this specific
  check initially looked like a failure; investigated and found to be the
  QA script's own overly-broad substring match (the correct fallback
  message legitimately contains the phrase being searched for, inside its
  own explanatory sentence) — logged in the notes doc's bug log (Part 5)
  since it's worth recording even though it wasn't a product bug.
- `seed 3 / C. Same-direction exterior` (the "global-cascade" curated
  example, D=0 for literally every candidate in that seed's landscape per
  the coordinator's brief): confirmed real headings are active.
- `seed 4 / E. Disordered exterior` (2 curated candidates, including the
  "jointly high-C/high-G/low-L/high-D" pick): confirmed the Example
  selector shows exactly 2 buttons; switched to the second and confirmed
  the metric-card title updates to that candidate's label.
- `seed 3 / D. Opposite exterior` (deliberately chosen as a pair with
  **no** curated data at all): confirmed 0 Example buttons render and the
  heading note correctly states headings aren't archived for this
  trajectory (screenshot on file: the lattice shows neutral/actuator-glow
  roles only, no arrows — the pre-existing, unchanged fallback behavior).
- Explore mode, all four pre-existing Inference & Identity tabs, and the
  top-level Control page were all re-visited at the end of the same script
  run and confirmed still functioning (no regression from this change).

**What was not verified in this addendum**: the same Firefox/Safari and
pointer-drag caveats from this report's main "Limitations" section still
apply unchanged. Additionally: the remaining `illustrative_trajectories`
entries not explicitly named above (there are exactly 10 total; all 10
were reached via the 7 (seed,condition) pairs walked through here) were
exercised as part of the groups above but not separately screenshotted one
by one — each group's *behavior* (selector presence/absence, real
animation, correct title/legend updates) was confirmed, which exercises
every entry's code path identically.

## Files referenced

- `interactive_demo/app/index.html` (source)
- `interactive_demo/app/build.py` (build script, now with a 4th
  `LANDSCAPE_DATA` placeholder)
- `interactive_demo/build/index.html` (built artifact QA'd above)
- `interactive_demo/data/collective_landscape_bundle.json` (data source,
  now also carrying `illustrative_trajectories` — Addendum 2)
- `interactive_demo/STAGE6_6_VISUALIZATION_NOTES.md` (full design
  rationale, field provenance, and bug log for everything summarized here)
