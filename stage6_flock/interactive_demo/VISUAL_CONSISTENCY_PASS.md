# Visual Consistency Pass — Stage 6 Interactive Demo

Summary of the visual-consistency / information-architecture / copy-editing pass across
`stage6_flock/interactive_demo/`. This was a UI pass only — see "Scientific content" at the bottom
for an explicit confirmation of what did *not* change.

Full inconsistency inventory (with measured numbers): `VISUAL_CONSISTENCY_AUDIT.md`. This document
covers what was actually changed, why, and what was deliberately left alone.

## What was inconsistent before

See `VISUAL_CONSISTENCY_AUDIT.md` for the full, measured list. In short: the Control tab and the
five Inference & Identity tabs had independently-tuned card radius/padding, an unstable header
height (46px → 86px between 1440 and 1280px width), and — the biggest issue — the Collective
Landscape tab's graph was roughly half the visual area of the Control tab's lattice, with its
primary scatter plot partially below the fold on load, because of a CSS structural bug (below) and
a cluttered always-visible control row (9 controls + 4 sliders above the graph).

## Root cause found for the Landscape graph-size problem

`.iiLandscape` and `#iiLsBody` — the two wrapper `<div>`s the Collective Landscape tab's router
injects its content into — had no `display:flex` of their own. That broke the flexbox height chain
coming down from `.iiBody`, so `.iiLsExploreRow`'s `flex:1` had no bounded ancestor to size
against. The row instead grew to match its own content's height (a stacked lattice + legend +
metric card in one column, cross-axis-stretched onto the scatter plot in the other), which came out
taller than the viewport — forcing the whole tab's primary visual to require scrolling to see in
full, on every viewport tested. Tabs 1–4 never had this problem because their equivalent container
(`.iiMain`) is a *direct* child of `.iiBody`, so it was already flex-bounded correctly.

Fix: gave `.iiLandscape` and `#iiLsBody` their own `flex:1; display:flex; flex-direction:column;
min-height:0`, restoring the chain, and added `min-height:0`/`overflow-y:auto` at each intermediate
column so content that still doesn't fit scrolls locally instead of blowing out the page. Result: at
1440×900 the Explore scatter+lattice pair and the Control-mode lattice both now render fully within
the viewport with zero page-level scroll (previously `document.querySelector('.iiBody').scrollHeight`
exceeded `clientHeight` by 300–470px on this tab specifically).

## Shared design tokens / components introduced

- `.iiCard`/`.iiStat` (Inference & Identity's metric-card component) now use the exact same
  `border-radius` (8px), `padding` (9px 11px), and font-size (11.5px) as Control's `#summaryCard`/
  `.metricRow`, instead of independently-tuned values (10px/`11px 13px`/12px before).
- `.iiSideCol` max-width bumped from 300px to 320px to match Control's `aside#sidebar` exactly.
- `header` no longer wraps to a second line at 1280/1100px width (which doubled its height); the
  inline legend now scrolls horizontally within a fixed-height header instead, matching the
  already-stable height of `#topNav`/`.iiTabs`.
- A new, generic **popover** component (`.iiPopoverWrap` / `.iiPopoverBtn` / `.iiPopover`): click to
  open, closes on outside click or Escape (one document-level listener, not per-popover), anchored
  to its trigger, clamped to a `max-height`/`overflow-y:auto`, no external dependency, works from
  `file://`. Used everywhere a "View settings"/"Filters" affordance was needed.
- The Collective Landscape Control-mode metrics column is now capped at 320px (`.iiLsMetricsCol`,
  reusing Control's side-panel width) instead of splitting the row 50/50 with the lattice.

## Controls moved into menus

Per the task's rule ("if it changes the scientific question, keep it visible; if it only changes
how the same result is displayed, it can move"):

| Tab | Moved to "View settings" | Kept visible |
|---|---|---|
| 1. Predictive Boundary | Labels: IDs / Roles | Reveal true interaction shell; Observed-trajectories sample size (changes which B̂ is computed) |
| 3. Prediction vs Control | Show redundant support (mᵢ) overlay | Flock selector; Oracle/Inferred/Fiedler/Random controller buttons |
| 5. Collective Landscape → Explore | Color by, Size by, Show Pareto candidates only (→ "View settings"); the 4 range filters (→ separate "Filters" popover, with a "Filters · N active" indicator and a Reset button) | Snapshot/regime selector; X axis; Y axis; Scatter/Sweep-grid view; Oracle/Inferred boundary source; teaching-case shortcuts |

Tabs 2 (Causal Stress Test) and 4 (Collective Identity) had no purely-visual toggles to move — every
control there already changes the scientific question being viewed (perturbation class/state,
identity lens, the validity guard) — so they were left structurally unchanged, only picking up the
shared card/token styling. **The identity validity guard in Tab 4 was deliberately kept directly
visible, per the task brief**, and was never a candidate for the menu.

## UI copy shortened

Copy was already fairly tight going into this pass (an earlier UX refinement pass had already run —
see `UX_REFINEMENT_LOG.md`). A search for the specific banned filler phrasing ("key takeaway is
that…", "interestingly…", "this result demonstrates…", etc.) found zero matches anywhere in
`app/index.html`. One real trim was made, preserving every number and caveat:

- Tab 2 (Causal Stress Test) takeaway: "Note the direct effect (X) and the predictive penalty (Y)
  are **different metrics at very different scales** — not directly comparable magnitudes." →
  "Direct effect (X) and predictive penalty (Y) are **different metrics at different scales** — not
  comparable."

No wording that carries a caveat, an uncertainty qualifier, or a specific number was removed or
altered anywhere else.

## Confirmation: no scientific data or conclusions changed

- No `data/*.json` file was regenerated, edited, or touched.
- No metric definition, threshold, classification rule, or reported number in `app/index.html` was
  changed. `git diff` on `app/index.html` touches only `<style>` rules, popover markup/JS, and the
  one copy trim quoted above — every numeric template literal (`.toFixed(...)`, stat values, table
  cells) is untouched.
- Stage 6.7's specific frozen distinctions (blind predictive boundary ≠ causal interface; the
  causal-interface diagnostic was not a 300-candidate benchmark; causal recovery used the exact
  counterfactual propagator; blind G tracked oracle G strongly; blind L was not comparable to oracle
  L) are rendered by the same, unmodified data-reading code path (`ls67Entry`, `lsRoleFn67`,
  `lsInferredMetricCardHtml`) — only their CSS container changed.
- No new methodology (e.g., a residual-leakage challenger) was added to any view.

## Tested browsers / viewports

Chromium (Playwright, headless), at 1440×900, 1280×800, and 1100×720, for: Control tab; all five
Inference & Identity tabs (Predictive Boundary, Causal Stress Test, Prediction vs Control,
Collective Identity, Collective Landscape → both Explore and Control submodes); Info modal; plus
secondary states (true-shell reveal, causal perturbation, identity guard + step-to-collapse,
Landscape scatter, Landscape sweep grid, Landscape oracle/inferred boundary source, View settings
popover open, Filters popover open + active-filter count + outside-click/Escape close).

Regression results at all three viewports, before vs. after:
- Console errors: 0 → 0.
- Horizontal page overflow (`scrollWidth > clientWidth`): none before, none after.
- Vertical overflow on the Collective Landscape tab specifically: present before (graph partially
  below the fold at 900px viewport height), resolved after (page fits with zero scroll at 1440×900
  and 1280×800; the ~1100×720 case scrolls only as much as tabs 1–4 already did, which is expected
  per the task's own responsive guidance to stack rather than shrink the primary graph).
- Control tab: pixel-identical layout at all three viewports (only `.iiCard`/`.iiSideCol`/header CSS
  under `.inference-identity`/global `header` selectors changed; Control's own markup and its
  dedicated rules were not touched beyond the header-wrap fix, which affects Control too since the
  header is shared chrome — see below).

## Intentionally retained inconsistencies, and why

- **Header wrap fix applies to the shared header, so it also touches the Control tab.** This was a
  deliberate exception to "avoid large changes to Control unless fixing an obvious bug" — the
  header's 46px→86px height jump between 1440 and 1280px width is exactly that kind of bug (a
  responsive regression, not a design choice), and the header is shared chrome above both modes, not
  Control-tab-specific markup.
- **Tabs 1–4's lattice is ~565–623px tall vs. Control's 706px at 1440×900 (not identical).** Left
  as-is: these tabs each pair the lattice with a single side card, same composition family as
  Control, and the task explicitly says not to force mathematically identical dimensions when
  sizing is legitimately driven by different content. The gap is a rhythm difference, not a "tiny
  graph vs. giant graph" problem — the actual instance of that in the audit (Collective Landscape)
  was fixed.
- **Collective Landscape's Explore-mode lattice (591px wide) is smaller than the scatter next to it
  and smaller than Control's lattice.** Left as-is: Explore mode has two co-primary visuals (the
  scatter *is* the main exploration surface; the lattice is the drill-down for whatever point is
  selected), unlike every other tab's single-lattice composition, so a 1.35:1 scatter:lattice split
  is appropriate rather than mechanical sameness.
- **`.iiStat` keeps its dashed-row-divider style rather than adopting Control's sparkline-based
  `.metricRow`.** The two components represent different information shapes (Control's rows always
  pair a scalar with a time-series sparkline; Inference & Identity's cards are point-in-time reads
  with no time axis in most tabs), so forcing sparklines into `.iiStat` would fabricate a chart
  where none of the underlying data has a "wiggle." Font size, padding, and radius were unified
  instead (see tokens above), which is what made the two components look like the same design
  system without pretending they show the same kind of number.
- **Legends, role colors, and lattice node/arrow/halo/ring sizing were already fully shared** across
  every tab (confirmed by inspection — `drawIILattice`'s node-radius formula is textually identical
  to Control's `renderLattice`, and no color is redefined for a different meaning anywhere). No
  changes were needed or made here.
- **Large tables were already secondary** (wrapped in a collapsible `iiDetails()` `<details>` in
  every tab that has one) before this pass. No changes were needed or made here.
