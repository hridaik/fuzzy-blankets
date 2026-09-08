# Visual Consistency Audit — Stage 6 Interactive Demo

Audit of `stage6_flock/interactive_demo/build/index.html` prior to the visual-consistency /
information-architecture pass. Methodology: Playwright (Chromium), screenshots and computed-style
measurements at 1440×900, 1280×800 and 1100×720, for the Control tab and all five Inference &
Identity sub-tabs (plus Info). No simulation data, metric definitions, or reported numbers were
touched to produce this document — it only reads DOM layout and CSS.

Screenshots: `audit_before/before_<viewport>_<view>.png` (not committed to the repo; regenerate
with the script referenced in `VISUAL_CONSISTENCY_PASS.md` if needed). All numbers below are
measured, not estimated.

## Reference: the Control tab (as-is, kept as the design source)

At 1440×900:
- `header` — 46px tall, `padding: 8px 18px`.
- `#topNav` — 41px tall.
- `#canvasArea` — `padding: 12px 14px`.
- `svg#svgMain` (10×10 lattice) — **1092×706px**, `border-radius: 10px`, `1px solid #e3e3e0`.
- `aside#sidebar` — **320px** wide, `padding: 12px`.
- `#summaryCard` — `border-radius: 8px`, `padding: 9px 11px`, `border: 1px solid #e3e3e0`, label
  `font-size: 11.5px`.
- `.metricRow` — label + numeric value + inline sparkline, row height ~40px.

This is the density/composition the task treats as canonical.

## Concrete inconsistencies found

### 1. Graph size varies 2× across tabs (the most visible issue)
Lattice/plot size at 1440×900, by view:

| View | Graph size (px) | vs. Control's 1092×706 |
|---|---|---|
| Control | 1092 × 706 | reference |
| Inference & Identity 1 (Predictive Boundary) | 1088 × 623 | ~12% shorter |
| Inference & Identity 2 (Causal Stress Test) | 1088 × 623 | ~12% shorter |
| Inference & Identity 3 (Prediction vs Control) | 1088 × 580 | ~18% shorter |
| Inference & Identity 4 (Collective Identity) | 1088 × 565 | ~20% shorter |
| Collective Landscape → **Explore** | **591 × 591** | **~55% of the area** |
| Collective Landscape → **Control** | 742 × 742 | ~68% of the area, and only ~52% of available width (a second, empty-by-default column reserves the rest) |

Root cause for Landscape/Explore: the control stack above the graph (snapshot selector + teaching
cases + 4 axis dropdowns + view toggle + Pareto checkbox + 4 range-filter rows, all rendered
unconditionally) is tall enough that at 900px viewport height the scatter plot is **partially
below the fold** on first load. This is the clearest instance of "one tab has a tiny graph
surrounded by controls."

### 2. Two independent "metric card" components
- Control: `#summaryCard` / `.metricRow` — 8px radius, `9px 11px` padding, label+value pairs with
  inline SVG sparklines, plus a distinct `.gammaBar` progress-bar treatment for coverage metrics.
- Inference & Identity: `.iiCard` / `.iiStat` — 10px radius, `11px 13px` padding, label+value rows
  separated by dashed borders, no sparklines.

Both represent the same idea (a labelled numeric readout) with different radius, padding, and
internal layout — defined independently rather than sharing tokens (task item G).

### 3. Header height is not stable across viewports
`header` height: **46px** at 1440×900, **86px** at 1280×800, **76px** at 1100×720. The title,
inline legend, and two right-aligned buttons all live in one unconstrained flex row with
`flex-wrap: wrap`, so the legend wraps to a second line as soon as width tightens — even though
1280px is still a "desktop" width. `#topNav` and `.iiTabs`, by contrast, hold a stable height
(41px / 51px) at all three widths. This is a responsive regression risk under item P ("reduce
secondary spacing before primary visual size, not the other way around").

### 4. Collective Landscape → Explore is the most cluttered view in the app
Simultaneously visible, unconditionally, above the graph: snapshot seed/condition selectors,
3 "teaching case" buttons, X-axis select, Y-axis select, **Color by** select, **Size by** select,
Scatter/Sweep-grid toggle, "Pareto only" checkbox, and 4 dual-handle range filters (Coherence,
Integration, Leakage, Contrast) — 9 distinct controls plus 4 sliders before the graph. Per task
item E, "Color by," "Size by," "Pareto filter," and the 4 range filters should move into
compact `View settings` / `Filters` affordances; axis choices, seed/condition, and boundary source
are the actual scientific question and should stay visible.

### 5. Secondary display toggles are visible at the same level as scientific choices, elsewhere too
- Predictive Boundary: label mode (IDs/Roles) and sample-size buttons sit in their own
  `.iiControls` row, visually equal in weight to "Reveal true interaction shell" (item F).
- Prediction vs Control: "Show redundant support (mᵢ)" is a plain always-visible checkbox next to
  the arm-selection buttons (item F asks for this to move to View settings).
- Collective Identity: lens buttons and the validity-guard checkbox are correctly kept visible
  (this matches the brief — the guard must stay visible) — no change needed here beyond visual
  token alignment.

### 6. Copy density / repeated explanation
Every Inference & Identity tab currently explains its finding up to three times: `iiSubtake`
banner, one or more `iiTakeaway` paragraphs (some 2+ sentences with embedded parentheticals), and
again inside the collapsible Details section. Example (Tab 3, Prediction vs Control) carries two
separate `iiTakeaway` blocks back to back that both restate "predictive sufficiency ≠ actuator
coverage." Per item H/I, the finding should be stated once, briefly, in the primary view; deeper
caveats belong only in Details.

### 7. Tables are already mostly secondary (no action needed)
`iiDetails()` (an existing `<details>` collapsible) already wraps every large table in the
Inference & Identity tabs — Full statistics, held-out flocks, across-flocks comparison, etc. This
already matches item N and is left as-is.

### 8. Legends and role colors are already consistent (no action needed)
Every tab's role palette (core = `--core`, shell/boundary = `--shell`, exterior = `--exterior`,
actuator = `--actuator`) is reused from the same CSS custom properties Control defines. No
redefinition of an established color for a different meaning was found. Legend markup
(`.dot`/`.ring` swatches) is already a single shared pattern (`iiLegendItem`/`iiDot`/`iiRing`
mirror Control's `.swatch`/`.dot`/`.ring`). This is good and is preserved.

### 9. No overflow, no console errors (no action needed)
`document.documentElement.scrollWidth` never exceeded `clientWidth` at any of the 9
view/viewport combinations captured, and zero console errors were logged. The wrapping described
in #3 is a height problem, not a horizontal-overflow problem.

### 10. Button/select component sizes are already close
`.iiBtn` (`padding: 6px 11px`, `font-size: 12px`, `border-radius: 7px`) and Control's
`button.opt`/`button.chip` (`padding: 5-6px`, `font-size: 11.5-12px`, `border-radius: 6-7px`) are
close enough that unifying them to shared tokens is a small, low-risk change rather than a
redesign.

## Summary of what needs to change

1. Extract shared tokens from Control (content padding, card padding/radius/border, graph sizing
   rule, side-panel width, button height, font sizes) and apply them under `.inference-identity`
   so cards/buttons match exactly instead of coincidentally.
2. Fix the Landscape Explore/Control graph-size deficit by moving secondary encoding controls
   (Color by, Size by, Pareto filter, the 4 range filters) into a compact `View settings` /
   `Filters` popover, and rebalance the Control-mode two-column layout so the graph is not
   artificially narrow.
3. Fix the header's viewport-dependent height jump (46 → 86px) so it stays stable, matching
   `#topNav`/`.iiTabs`.
4. Move purely-visual toggles (label mode, sample-size in Tab 1; redundant-support in Tab 3) into
   a small `View settings` popover per tab, keeping every scientifically-defining control visible.
5. Tighten `iiTakeaway`/banner copy to remove repetition, without dropping any caveat or number.
6. Unify `.iiCard`/`.iiStat` styling with `#summaryCard`/`.metricRow` token values.

No scientific content, metric definitions, thresholds, or Stage 6/6.5/6.6/6.7 result files are
touched by any of the above.
