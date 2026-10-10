# VIZ_RECON.md — Phase 0 visualization reconnaissance

Read-only inspection of every heading-relevant visualization artifact
touching Stage 6.11 (and its cross-stage predecessor app), done directly
(code read + Playwright screenshots taken this pass, viewed by eye — not
inferred from filenames or docstrings). Nothing rendered here is new data;
no existing file was modified. This is the required Phase 0 input to the
later Phase 3 `VISUAL_QA.md` — it establishes the baseline and answers the
mandate's specific question ("identify why heading arrows disappeared or
became unreadable") before any new instrument is designed.

## Inventory and glyph type, confirmed by reading the actual drawing code

| artifact | generator | glyph per bird | heading drawn? | canvas/viewport |
|---|---|---|---|---|
| `figures/translating_collective_611.html` (the `RESULTS_6_11.md` §8 deliverable) | `code/export_viz_611.py` + `code/make_figures_611.py` | **oriented filled triangle** (`drawBird`, line 459) | **YES** — `ctx.rotate(Math.atan2(-v[1], v[0]) + Math.PI/2)` where `v = HEADING_VEC[heading]`; triangle height `r*1.6+r*1.1`, `r=2.2–3.4` normal / `r=2.4–3.8` for interior/actuator ("big" mode) | two 600×600 canvases (world + co-moving), side by side, `aspect-ratio:1/1`, scales with container |
| `stage6_flock/interactive_demo/app/index.html` (cross-stage app) | `app/build.py` | circle (fixed color-coded fill/stroke by role: core/shell/fiedler/actuator) **plus a separate short line segment** from center along `UV[h]` | **YES**, via the line segment, not glyph rotation | 400×400 SVG viewBox, lattice-positioned (fixed grid, not continuous torus coordinates) |
| `audit/viz_6_11b.html`, `audit/viz_6_11b_final.html` (the 6.11B audit-tooling comparator) | `audit/export_viz_v2_611.py` | **plain filled dot** (`ctx.arc(x,y,1.6–4.2,0,7)`) | **NO** — confirmed by reading the entire `draw()` function (lines 267–330+): `fr.z`/heading is never read; only `fr.r` (position) and set membership (v1/v2/actuator) determine color. No rotation, no line segment, nothing heading-derived anywhere in this file. | one 600(ish)×600 canvas, world + co-moving toggle (not side-by-side), scales with container |

**There is no `renderDyn611` (or equivalent) function anywhere in
`interactive_demo/app/index.html`** — the cross-stage app's per-stage
render functions go up to `renderDyn610` and stop; Stage 6.11 was never
integrated into it. The two visualization lineages (per-stage deliverable
vs. cross-stage app) diverged at 6.11, and only the per-stage deliverable
exists for this stage.

## The precise answer to "why did heading arrows disappear or become unreadable"

**They did not disappear from every renderer — they disappeared from one
specific, later-built one, for a reason unrelated to the mandate's implicit
assumption that this was a regression in "the" demo.** Two genuinely
different files exist for genuinely different purposes:

1. `figures/translating_collective_611.html` is the actual Stage 6.11
   result deliverable (built once, at the end of the stage, per
   `RESULTS_6_11.md` §8) and **has working, correctly-rotated heading
   triangles**, confirmed by direct code read and by three fresh
   screenshots taken this pass (`identity_foundation/visual_qa_screens/
   translating_611_{1440x900,1280x800,1100x720}.png`, zero console errors
   at all three viewports).
2. `audit/viz_6_11b.html`/`viz_6_11b_final.html` is a **separate,
   later-built comparator tool**, purpose-built during the 6.11B
   audit/repair pass specifically to compare v1-vs-v2 tracker MAP output
   over a recorded trajectory (its own caption: "Original tracker (v1) vs.
   present-state-coalesced comparator (v2), replayed on the recorded
   ground-truth trajectory. No control decision reads this page."). Its
   author (`export_viz_v2_611.py`) built a new, simpler drawing routine
   from scratch rather than reusing `drawBird`, and that new routine never
   reads heading at all — every bird is a plain dot, colored only by
   which tracker (if any) currently claims it. **This is the file the six
   pre-existing `audit/screenshot*.png` baseline screenshots were taken
   from**, and it is almost certainly what the user means by "v2's
   animation still looks jumpy": with no heading channel and no trail,
   the only visible signal from one frame to the next is a cluster of
   dots abruptly changing color as membership reassigns — which reads as
   jumpier than the same event would with headings and trails present,
   independent of whether the underlying identity switch is itself real.

So: the mandate's framing ("heading arrows disappeared") is *approximately*
right about the artifact the user has most recently been looking at
(`viz_6_11b_final.html`), but the mechanism is not "arrows were removed
from a maintained renderer" — it is "a second, narrower-purpose renderer
was built without them, for a task (tracker MAP comparison) its author
did not consider heading-critical for." Both files independently exist and
both are preserved unchanged; Phase 3 builds a third, new instrument that
does not repeat the second file's omission.

## What the working renderer (`translating_collective_611.html`) gets right, worth reusing conventions from

Confirmed directly from the three screenshots taken this pass:

- A proper narrative structure matching PLAN.md Section U almost exactly:
  a 7-step story (**1** Unstructured start → **2** Scanning → **3**
  Detected & locked → **4** Interfaces & actuators → **5** Control running
  → **6** Release → **7** Outcome), with per-step caption text.
- World frame and co-moving frame shown **side by side**, both large,
  neither squeezed to make room for a dashboard.
- A dark theme with a legible, restrained color palette; a compact header
  strip (episode seed, arm, N birds, box L, outcome) above the panels.
- A seed selector (5 seeds) as a row of pills, not a dropdown — quick to
  scan and switch.
- Distinguishes interior/actuator/exterior/"just-left" roles by **color**,
  reserving a **ring** for "just left the interior" — i.e., already
  follows the mandate's "don't overload one color with several meanings"
  principle to a first approximation.

## What is genuinely missing or too small, confirmed by looking at the actual pixels, not just the code

- **Triangle glyphs are present but too small to be individually legible
  at world-view scale.** At 1100×720 (the smallest required QA viewport),
  the world/co-moving panels render at roughly 510px square each, holding
  all ~400 birds; a `r=2.2–3.4`px triangle (roughly 4–11px tall) is, at
  that density, visually indistinguishable from a dot in a static
  screenshot — confirmed by direct visual inspection of
  `translating_611_1100x720.png`, not assumed from the radius numbers
  alone. This is *exactly* the mandate's "heading channel is essential
  data, not decoration" concern, materializing not as an outright removal
  but as a legibility failure under crowding — the same failure mode the
  mandate anticipates with "use a zoom/follow view when 400 arrows cannot
  be read in the world panel."
- **No zoom or follow view exists.** Confirmed by grep across the entire
  file for `zoom`/`follow`/`scale(` — none found outside the unrelated
  "big" boolean that only enlarges interior/actuator triangles slightly
  (§ table above). There is no mechanism to crop/magnify onto the tracked
  interior once it is small (e.g. 20–40 members out of 400) — exactly the
  situation where individual heading orientation matters most for judging
  whether a turn is really happening, and exactly where this renderer's
  design has no answer.
- **No trail/short-history rendering** — each frame is drawn independently
  with no fading trail of recent positions, which (independent of the
  heading-glyph issue) also contributes to abrupt-looking frame-to-frame
  changes.
- **The two lineages have diverged and will need explicit reconciliation
  in Phase 3**, not a silent pick of one: the per-stage deliverable has
  headings and a good narrative shell but no zoom/follow/trails and no
  lineage/genealogy readout (it was built before the v1/v2 tracker
  question existed); the 6.11B comparator has the tracker-comparison
  panel layout and MAP-belief readouts the identity work now needs, but
  no headings, no narrative, and no trails. Per the mandate, **both must
  be preserved unchanged**; Phase 3's new page is additive, reusing
  layout/typography conventions from the former and panel-content
  conventions (Identity/Spatial-integrity/Control sections) from the
  latter, building the new identity model's own readouts on top.

## Environment confirmed for Phase 3

Playwright (Python) is installed and works directly against local
`file://` URLs with no server needed (`sync_playwright().chromium.launch()`
succeeded against `figures/translating_collective_611.html` at all three
required viewports, zero console errors). This is the same tool to use for
Phase 3's own screenshot/interaction QA.

## Screenshots taken this pass

`identity_foundation/visual_qa_screens/translating_611_1440x900.png`,
`_1280x800.png`, `_1100x720.png` — fresh renders of the one working
heading-aware demo, for direct comparison against whatever Phase 3
produces. The six pre-existing `audit/screenshot_*.png` /
`audit/screenshot2_*.png` files (already on disk from the prior session)
remain the baseline for the no-heading comparator tool and are unchanged.
