# STAGE6_6_VISUALIZATION_NOTES.md

Documents the 5th Inference & Identity subtab, **"5. Collective Landscape"**
(Stage 6.6), added 2026-09-07. Follows the structure and rigor of
`STAGE6_5_VISUALIZATION_NOTES.md`: what each piece of UI is built from,
which design choices were made and why, and a running log of bugs found
and fixed while building it. Nothing here modifies a frozen scientific
result file — everything reads `interactive_demo/data/collective_landscape_bundle.json`
(written by `stage6_6_collective_landscape/code/export_demo_data.py`, not
touched by this pass) or derives client-side from it via pure, checkable
functions (graph-distance BFS; see Part 4).

## Part 0 — scope and namespacing

One new subtab, `data-reftab="landscape"` / **"5. Collective Landscape"**,
added to the existing `Inference & Identity` mode's tab bar. No new
top-level nav mode — `Control | Inference & Identity | Info` is unchanged.
Inside the tab: two internal submodes, **Explore** and **Control** (task
brief section 17), toggled by two buttons; each is a from-scratch
`innerHTML` rebuild on every state change, matching the existing
`renderTabX()` convention in this file (no diffing anywhere in this
codebase, by design — see Stage 6.5 notes Part 2).

Every new CSS rule lives under `.inference-identity .iiLandscape ...`
(verified mechanically — see Part 5, "CSS namespacing check"). The only
edit to pre-existing code is one line: the `.iiTabBtn` click handler now
also calls the new `iiStopLandscapePlayback()` alongside the existing
`iiStopIdentityPlayback()`, so a running Control-mode timer doesn't keep
firing after the user leaves the tab (mirrors the existing tab-4 pattern
exactly — see Part 5 for a caveat this doesn't fully close). Everything
else in the diff is pure addition. `git diff --stat` on this pass:
1 file changed for `build.py` (+16/-2), and for `index.html` all but one
line are additions (`675 insertions(+), 2 deletions(-)`).

## Part 1 — data flow / build.py integration decision

Stage 6.6's data (`interactive_demo/data/collective_landscape_bundle.json`)
comes from a separate, independent generator
(`stage6_6_collective_landscape/code/export_demo_data.py`) from Stage 6.5's
`derive_refinement_viz_data.py`. Rather than folding its JSON into the
existing `REFINEMENT_VIZ` tree (which would require `build.py` to parse and
merge two independently-generated JSON documents by hand, and would make
`REFINEMENT_VIZ` non-null-safe if only one of the two source files exists),
**a fourth placeholder was added**, following the exact existing pattern:

```python
window.LANDSCAPE_DATA = /*__LANDSCAPE_DATA__*/ null /*__END_LANDSCAPE_DATA__*/;
```

`app/build.py` inlines `data/collective_landscape_bundle.json` into it the
same way it already inlines `refinement_bundle.json` and
`refinement_viz_data.json` — read raw text if the file exists, else the
literal string `"null"` (so a build missing this file still produces a
working page; the tab just reports "data not available", exactly like the
existing `if (!RVIZ)` guard in `renderRefinementView()`). Each of the two
Stage-6.x science pipelines keeps writing and owning exactly one file; nothing
new needs to know about the other's internal schema.

Rebuild sequence (one more step appended to Stage 6.5's):
```
cd stage6_6_collective_landscape/code && python3 export_demo_data.py   # re-run any time to pick up new snapshots
cd ../../interactive_demo/app && python3 build.py
```

`export_demo_data.py` is idempotent and was **not modified** by this pass
(explicitly out of scope per the task brief) — it was only re-read to
understand its output schema and re-run once to confirm the pipeline
end-to-end. At the time of this build, `data/collective_landscape_bundle.json`
contained **1 of the planned 15 `snapshots` entries** (`seed2_no_control`)
because the background batch job (`run_all_snapshots.py`) was still running;
`archetype_trajectories` (used by Control mode) already contained all 3
seeds x 5 conditions x their fraction-of-exterior-controlled variants. The
JS was written generically against `Object.keys(LANDSCAPE_DATA.snapshots)`
and `Object.keys(LANDSCAPE_DATA.archetype_trajectories)` — **no seed or
condition list is hardcoded anywhere in the JS**; re-running
`export_demo_data.py` once more snapshots exist and rebuilding is all that
is required to light up the remaining regime buttons in the Explore-mode
snapshot selector (they render as a disabled `"(pending)"` option today,
computed from which `seed{n}_{condition}` keys are actually present).

## Part 2 — Explore mode

Left: a custom SVG scatter (`drawLsScatter`, hand-rolled — the file has no
charting library and the existing `iiBarChart`/`drawSpark` precedent is to
write small dedicated SVG renderers). Right: the **exact same**
`drawIILattice()` primitive every other tab uses, with a role function
built from a client-side 2-hop BFS (see Part 4). This satisfies task brief
section 21 ("reuse the original graph/lattice renderer") literally — no
second lattice implementation was written.

**Axis/color/size dropdowns** (section 18): all four quantities (C, G, L,
D) are available on every one of X/Y/color; size additionally offers
"constant". Default `x=L, y=G, color=D, size=C` exactly matches the task
brief's specified default. Nothing hardcodes the G-vs-L pairing — swapping
any dropdown re-renders both the scatter and (implicitly, since selection
state doesn't change) the lattice.

**Four independent range filters** (section 19): implemented as four
separate two-thumb sliders (`.iiLsDual`, two overlapping native
`<input type=range>` elements with `pointer-events` split between track and
thumb via CSS — a standard trick for a dual-handle range control without a
library). Each filter's bounds are stored as **fractions in [0,1]** of that
metric's actual min/max **within the current snapshot**, not raw values —
so switching snapshots (different seed/condition, different natural scale
per metric) doesn't require re-deriving five absolute thresholds by hand.
Filters are applied as an explicit AND of four independent interval tests
(`lsFilteredIndices`) — never combined into a single score, per the task
brief's explicit instruction.

**Sweep-grid mode** (section 20): `drawLsSweepGrid` bins the *currently
filtered* candidate set into a 5x5 grid over the current X/Y axis pair,
using each axis's full-snapshot range (not the filtered subset's own
range, so cell boundaries don't shift as filters change). Each populated
cell shows a count; the representative is the candidate with minimum
normalized Euclidean distance (normalized by cell width/height, so the two
axes contribute comparably regardless of their absolute scales) to the
cell's centre. Clicking a cell sets `selectedIdx` to that representative,
exactly as clicking a scatter point does — both paths converge on the same
"draw the lattice for `selectedIdx`" code, so there is exactly one lattice
rendering path in Explore mode, not two.

**Compare-two-candidates** (section 23): "Pin as candidate A" appears only
once a candidate is selected; the compare layout (two lattices, two metric
cards, side by side) activates automatically whenever a pinned candidate
and the currently-selected candidate differ — no separate `compareOn`
toggle was introduced, since that state is fully derivable from
`(pinnedIdx, selectedIdx)`, per the brief's "lightweight" instruction. The
scatter/sweep panel stays live and clickable while comparing, so candidate
B can be changed by clicking a new point without leaving compare view.

**Pareto filter** (section 24): a single checkbox, default OFF, that adds
`Pa[i] === true` to the same AND-filter used by the four range sliders.
Pareto status is *also* shown as plain text in every candidate's Secondary
Details panel regardless of the checkbox — this is informational text, not
a visual privilege (no distinct marker/highlight is drawn on Pareto points
in the scatter unless the filter is checked, per the brief's explicit
"do not visually privilege" instruction).

**Snapshot/regime selector** (section 25): two `<select>` dropdowns (seed,
condition) rather than a 3x5 button table — see Part 5, "graph must stay
dominant" bug entry, for why this was changed mid-build. Options for
seed/condition combinations not yet present in `LANDSCAPE_DATA.snapshots`
render disabled with a `"(pending)"` suffix; selecting a seed with no
snapshots at all is prevented by disabling that `<option>` outright.

**Teaching cases** (section 28): computed **fresh, per snapshot, at every
render** by `lsTeachingCases()` — never hardcoded to a specific candidate
id. "Global-looking consensus" = argmax(C − D) over all candidates.
"Distinct coherent group" = argmax(C + D) restricted to the top quartile of
C (falls back to the full set if the top-quartile subset is empty, which
cannot currently happen since quartiles are always non-empty for N≥4).
"Looks coherent, weakly integrated" only renders its button when a
candidate exists in the top-C quartile whose D is *also* in that subset's
top quartile *and* whose G is in that subset's bottom quartile — i.e. a
candidate that looks like a distinct, agreeing group but is measurably not
well-integrated. **Checked against the one snapshot available at build
time (`seed2_no_control`): no such candidate exists** (there is no overlap
between the top-quartile-D and bottom-quartile-G subsets of the top-C
group in that snapshot — confirmed by direct query, see Part 6) — so the
third button correctly does not appear there. It is expected to appear
automatically for other seeds/conditions once generated and rebuilt,
without further code changes, if the pattern is real in that regime.

## Part 3 — Control mode

Fixed candidate `I` = the snapshot's own `archetype_trajectories[seed].I0`
(the "established I0", per the task brief). A local timeline scrubber
follows the exact pattern of tab 4's `renderTabIdentity()` (own play/pause/
step/restart buttons, own `setInterval(...,250)`, own
`iiStopLandscapePlayback()` twin of `iiStopIdentityPlayback()`), scrubbing
over `series.t` (index-based, since exterior-budget conditions below 100%
are stored at stride 2 — see Part 4, "index vs absolute time").

Condition buttons (No control / Shell only / Same exterior / Opposite
exterior / Disordered exterior) map 1:1 onto the bundle's
`no_control|shell_only|same_direction|opposite|disordered` condition keys
(archetype labels A–E per the task brief). The three exterior conditions
additionally show 25/50/75/100% exterior-budget buttons
(`conditions[cond]["0.25"|"0.50"|"0.75"|"1.00"]`); `no_control`/`shell_only`
have only a `"1.00"` entry (present in the data even though `f_E` is not a
meaningful concept for those two conditions — see Part 4).

**Live metrics** (section 27): four compact line traces
(`drawLsTrace`, ~220x44px each — deliberately small, "keep compact" per the
brief) for `C_I(t)`, `G_I(t)`, `L_I(t)`, `D_local(t)`, read straight from
`series.C/G/L/D`. Secondary numbers (target fraction `H*(t)` from
`series.H_star`, external entropy from `series.H_E`, control effort) are
shown below in a plain `.iiCard`, not charted — matches the brief's "keep
compact... secondary numbers" framing exactly.

**Control effort** is defined, explicitly and in the UI copy itself, as
`meta.n_shell_actuators + meta.n_exterior_actuators` while `t ≤ T_u`, and
`0` after (`t > T_u`) — stated as a derivation, not asserted as a
pre-existing frozen metric, per the task brief's data section: *"'control
effort' ... can be reported as n_shell_actuators + n_exterior_actuators
(constant during the active window, 0 after release) — state this
derivation explicitly ... rather than inventing a different definition."*

## Part 4 — the graph-distance BFS, and other client-side derivations

`E_near(I)` (near/second-ring exterior) and `S(I)` (structural shell) are
**not** precomputed per candidate in the bundle (would multiply its size —
see `export_demo_data.py`'s own docstring). `lsBFSRoles(lattice, I)`
computes them client-side: a standard multi-source BFS from every node in
`I` over `lattice.neighbors`, taking nodes first reached at hop-distance 1
as `S(I)` and at hop-distance 2 as `E_near(I)`; "distant exterior" (used
only in the tooltip role label) is simply "reached at neither hop, or not
reached at all within 2 hops." This mirrors the graph-distance definitions
given verbatim in the task brief (verified against
`stage6_6_collective_landscape/code/common_66.py`'s
`structural_shell`/`near_exterior` *definitions*, read-only, per the task
brief's explicit allowance — the file itself was not imported or executed
by the JS, which reimplements the same two-line BFS logic natively since
there is no Python runtime in a static HTML page).

**Index vs. absolute time in Control mode**: `series.t` is not always
`[1,2,...,40]` — conditions with `f_E < 1.0` are stored at `stride=2`
(`t = 1,3,5,...,39`, 20 points instead of 40; confirmed by direct
inspection of the bundle). The timeline slider therefore scrubs an
**index** into `series.t` (`0..series.t.length-1`), and the displayed
`t = series.t[tIdx]` is read back from the array rather than assumed.

**Headings in Control mode are not fabricated.** `archetype_trajectories`
stores only the four scalar metric series per timestep — no per-timestep
heading array (confirmed: `series` keys are exactly
`t,C,G,L,D,H_E,directional_contrast,cosine_similarity,H_star,effective_window`).
The only real per-bird heading state available anywhere in the Stage 6.6
bundle is each snapshot's single `representative_z` (captured at
`t_snapshot = t0+T_u`, i.e. control-end, for the `f_E=1.0` condition of
that seed+condition pair). Control mode therefore shows real arrows
**only** when the scrubber is at exactly `t = T_u`, the exterior budget is
at 100%, and a matching snapshot (`seed{n}_{condition}`) has been
generated — otherwise arrows are omitted entirely, with an explicit
in-UI caption explaining why, rather than holding the last-known heading,
interpolating, or reusing `h0` as a fake static pose. **Role highlighting
(interior / actuated shell / actuated near-exterior / neutral) is exact at
every `t`** regardless of heading availability, since actuator-set
membership is fully described by `meta.shell`/`meta.controlled_exterior`
and is constant during `t ≤ T_u` and empty after — this is the one part of
section 26's "current headings" requirement that could not be shown
literally; see Part 6 for the explicit gap statement.

## Part 4.5 — provenance of every displayed field

| Submode | Displayed field | Source |
|---|---|---|
| shared | `lattice.positions`/`.neighbors` | `LANDSCAPE_DATA.lattice`, verbatim from `export_demo_data.py`'s `build_lattice_block()` — a 10x10 grid, structurally identical to `DEMO_DATA`'s and `REFINEMENT_VIZ`'s own lattice blocks (checked field-for-field: same `L=10`, `nn=100`, same `positions`, same `neighbors["0"]`). Read directly from `LANDSCAPE_DATA` rather than cross-referencing `RVIZ`/`DEMO_DATA`, so tab 5 has no runtime dependency on tabs 1-4's or the Control page's data being present (a build with only `LANDSCAPE_DATA` populated still renders tab 5 correctly) |
| Explore | scatter X/Y/color/size values (`C`,`G`,`L`,`D`) | `snapshots[key].candidates.{C,G,L,D}[i]`, verbatim (already rounded at export time by `export_demo_data.py`'s `_columnar()`) |
| Explore | filter bounds shown next to each slider | computed client-side: `lsRange()` = min/max of that metric over the *current snapshot's* full embedded candidate array; the slider's fraction is denormalized against that range |
| Explore | "N / M candidates shown" | N = `lsFilteredIndices().length` (client-side filter count); M = `candidates.id.length` (embedded count, verbatim `n_candidates_embedded`) |
| Explore | "of {n_candidates_full} total" | `snapshots[key].n_candidates_full`, verbatim |
| Explore | metric card `C`,`G`,`L`,`D`,`|B|` | `candidates.{C,G,L,D,Bs}[idx]`, verbatim; `K` = `LANDSCAPE_DATA.K_boundary_budget`, verbatim |
| Explore | metric card secondary: shell size, `H_E`, `D_c`, source, Pareto | `candidates.{Sh,He,Dc,src,Pa}[idx]`, verbatim |
| Explore | lattice roles (interior/selected boundary/shell-not-selected/near/distant) | `candidates.I[idx]`/`candidates.B[idx]` (verbatim id lists) for interior/selected-boundary; shell/near computed client-side by `lsBFSRoles()`, a 2-hop BFS over `lattice.neighbors` from `I` (see Part 4) — spot-checked against the bundle's own `Sh` field and `archetype_trajectories`' `meta.near_exterior` (Part 5) |
| Explore | lattice headings | `snapshots[key].representative_z`, verbatim — one shared realization per snapshot (same for every candidate in that snapshot; only the highlighted role set changes per candidate) |
| Explore | teaching-case candidates | computed client-side by `lsTeachingCases()` from the current snapshot's own `C`/`G`/`D` arrays (argmax/quantile queries — see Part 2); never a stored field |
| Control | fixed interior `I` | `archetype_trajectories[seed].I0` **unless** a curated `illustrative_trajectories` example is active, in which case that entry's own `I` (verbatim) — see Part 8 |
| Control | seed/condition/exterior-budget button availability | presence of `archetype_trajectories[seed].conditions[cond][fE]` keys, checked live against the loaded bundle (not a hardcoded list) |
| Control | Example-selector button availability/labels | `illustrative_trajectories` filtered client-side by `(seed, condition)` (`lsIllustrativeGroup()`); the selector itself only renders when that filter yields >1 entry — see Part 8 |
| Control | `t` display | `activeSeries.t[tIdx]`, verbatim (index-based scrubbing — see Part 4, "index vs absolute time," since stride varies by condition); `activeSeries` is `entry.series` (archetype) unless a curated example is active, in which case it's that example's own `series`, field-renamed once (`Hstar`→`H_star`, `He`→`H_E`) to the archetype naming convention the rest of the function expects — see Part 8 |
| Control | four metric traces `C(t)/G(t)/L(t)/D(t)` | `activeSeries.{C,G,L,D}`, verbatim (I&#8320;'s own when no curated example is active; the specific displayed candidate's own otherwise — these differ, see Part 8) |
| Control | target fraction `H*(t)` | `activeSeries.H_star`, verbatim |
| Control | external entropy `H_E(t)` | `activeSeries.H_E`, verbatim |
| Control | control effort | derived: `meta.n_shell_actuators + meta.n_exterior_actuators` while `t≤T_u`, else `0` — an explicit derivation, not a stored field (see Part 3, quoting the task brief's own instruction to state this derivation); always I&#8320;'s own physically-forced counts, regardless of which candidate is being viewed (see Part 8) |
| Control | shell / exterior actuator counts | `meta.{n_shell_actuators,n_exterior_actuators}`, verbatim |
| Control | "actuated now" glow role | `meta.{shell,controlled_exterior}` (verbatim id lists, always I&#8320;'s own — this reflects what the simulator physically forced, not a property of whichever candidate is being viewed) combined with `t≤T_u` and `condition≠"no_control"` client-side |
| Control | "structural shell (not actuated)" / "near exterior" ring roles | client-side 2-hop BFS (`lsBFSRoles()`, the same function Explore mode uses) over the **displayed candidate's own** `I` — numerically identical to `meta.{shell,near_exterior}` when no curated example is active (verified, Part 5), genuinely different for the 3 curated non-I&#8320; candidates (Part 8) |
| Control | lattice headings | curated example active → `illEntry.z_hist[t]`, verbatim, every `t` (Part 8); otherwise `snapshots["seed{n}_{condition}"].representative_z`, shown only when `fE==="1.00" && t===T_u` and that snapshot key exists (see Part 4) — omitted (not fabricated) in every other case |

## Part 5 — bugs found and fixed while building this tab

**CSS namespacing check.** Every new selector was mechanically verified to
start with `.inference-identity` (a small Python script parsed the new CSS
block line-by-line and flagged any rule whose selector didn't have that
prefix; zero were found). No `#id`-only rules were added for this tab (the
one pre-existing bare-id exception, `#iiTooltip`, was reused as-is, not
duplicated), so there was nothing here to accidentally leave unscoped —
unlike the Stage 6.5 build, no analogous tooltip-in-`document.body` bug was
introduced, because `iiShowTooltip`/`iiHideTooltip` were reused unchanged
rather than reimplemented.

**Stuck tooltip across submode switches (found and fixed).** During QA,
switching from Explore to Control mode (or between tabs) after a scripted
hover left `#iiTooltip` visibly stuck on screen with stale content — the
element's `hidden` flag was never reset because the `mouseleave` that
normally calls `iiHideTooltip()` doesn't fire when the hovered element is
removed from the DOM out from under the pointer (which is exactly what a
full `innerHTML` rebuild does). Confirmed this is a **pre-existing latent
risk shared by every tab** (tabs 1–4 never call `iiHideTooltip()` on
tab-switch either — `wireControls()`'s top-nav handler doesn't call it, and
neither does the `.iiTabBtn` handler for tabs 1–4). Rather than touch that
shared code path (out of scope — tabs 1–4 must stay unchanged), a
defensive `iiHideTooltip()` call was added at the top of
`renderTabLandscape()` itself, closing the bug for every entry into/within
tab 5 (Explore↔Control switch, and every re-render) without changing
tabs 1–4's behavior at all.

**Explore-mode controls initially pushed the graph below the fold (found
and fixed).** The first working version's Explore mode stacked: mode
toggle → question/caveat text → a full 3-seed x 5-condition **table**
snapshot selector → axis/view/Pareto row → a 2x2 grid of filter rows (4
separate lines) → a candidate-count line — all *above* the scatter/lattice
row. At 1440x900 this pushed the actual graphs (the visual element the
task brief repeatedly insists must stay dominant — sections 17, 21, 34)
below the fold of the tab's own internal scroll container
(`.iiBody{overflow-y:auto}`), confirmed by an actual Playwright screenshot
showing the lattice as an unstyled grid of grey circles with the colored
interior/boundary rows scrolled out of view. Fixed by: (1) replacing the
15-button table with two `<select>` dropdowns (task brief section 25 only
asks for "let the user change the physical regime" — a table was a
self-imposed design overreach); (2) changing `.iiLsFilters` from a fixed
`1fr 1fr` grid to `repeat(auto-fit, minmax(220px,1fr))`, letting all four
filters sit on one row at desktop widths instead of two; (3) merging the
candidate-count line into the same row as the View/Pareto controls. Net
effect, verified by a second screenshot: the scatter and lattice are both
substantially visible without scrolling at 1440x900, and only a modest
scroll is needed at 1024x768 (consistent with how much *more* interactive
surface this tab exposes than tabs 1–4, each of which has a single
question and one control cluster).

**Long candidate IDs overflowed the metric-card header (found and
fixed).** Candidate ids are long
(`seed2__no_control__fE1.00__t20__c00673`, ~40 characters). In the
side-by-side compare layout (two ~300px-wide cards) the id visibly ran past
the card's right edge. Fixed with `word-break:break-all` plus a line break
after "Candidate" on that one `<h4>`, scoped inline (not a global `.iiCard
h4` rule change, to avoid any visual effect on tabs 1–4's own `.iiCard`
usage, which never has long content in an `<h4>`).

**Off-by-one risk in the BFS ring definitions — checked, not found.**
Because "structural shell" (hop 1) and "near exterior" (hop 2) look
superficially similar to "one more Moore-neighborhood ring," the BFS was
written to explicitly track first-visited hop distance per node (a
`Map<id,distance>`, sourced from **all** of `I` simultaneously, not
iterated ring-by-ring from a single node) and unit-checked by hand against
`I0`'s known values before use: for the `seed2_no_control` snapshot,
`I0` has 20 members, its structural shell size is 12 (`Sh` field for the
`seed_reference_I0` candidate matches `Bs`'s companion `Sh=12` exactly —
the boundary budget `K_boundary_budget=12` in this regime happens to equal
the full structural shell size, i.e. every structural-shell node is inside
the selected boundary for that particular reference candidate), and
`near_exterior` for that same seed (from `archetype_trajectories`'
`meta.near_exterior`) has 13 members — both numbers reproduced exactly by
`lsBFSRoles()` on the actual lattice, confirmed via a one-off console check
during development. No off-by-one was found, but this check is recorded
here per the task's "log bugs found (or ruled out after specifically
checking)" spirit.

**False alarm in the QA script itself while building the illustrative-
trajectory feature (Part 8) — investigated, ruled out as a product bug.**
A Playwright assertion checking that the 100%-exterior-budget curated
example correctly disappears when the budget slider is moved to 50%
initially reported failure. Investigation (bisecting the exact click
sequence, then dumping the live DOM's note text) found the actual rendered
text at 50% was the correct sparse-fallback message — the assertion itself
was checking for the substring `"curated illustrative example"`, which
also appears, legitimately, inside that very fallback message's own
explanatory sentence ("...a real heading snapshot is only available...
and only where a curated illustrative example exists for this regime").
Fixed by tightening the test's own string check
(`"Real per-timestep headings" not in note`), not by changing any product
code — re-verified green after the fix, and the underlying feature was
independently confirmed correct by direct screenshot inspection (arrows
absent, roles neutral/actuator-only) before the test was even fixed. Logged
here because the failure signal looked, at first, exactly like a genuine
regression.

## Part 6a — post-completion verification (added after all 15 snapshots landed)

The gaps in Part 6 below were written while the background landscape-
generation batch job was still running, against a bundle containing only 1
of 15 planned snapshots. After all 15 completed
(`data/snapshot_manifest.json`: 5000/5000 candidates for every one, total
6791.9s), the orchestrating session re-ran `export_demo_data.py` (bundle
grew from 0.38MB/1 snapshot to 3.89MB/15 snapshots) and `app/build.py`
(`build/index.html`: 1967KB -> 5400KB), then independently re-verified with
a fresh Playwright script (same `chromium-1243` + extracted-`.deb`-libs
workaround as Part 7, reproduced from scratch rather than reusing this
pass's throwaway script) at 1440x900, 1280x800, and 1024x768:

- **Zero console/page errors** at all three viewports with the full
  15-snapshot bundle loaded.
- Both snapshot `<select>` elements (`#iiLsSeedSel`, `#iiLsCondSel`) now
  expose all 3 seeds x 5 conditions with **no options disabled** (previously
  every condition but `seed2/no_control` rendered as a disabled
  `"(pending)"` option, exactly as Part 1/6 predicted).
  `iiLsCondSel`'s `option.disabled` was confirmed `False` for all 5 values
  via `eval_on_selector_all`.
- Switching to `seed 4 / E. Disordered exterior` (a snapshot this pass never
  saw — `n_ideal_region=292` in the underlying data, the richest of the 15)
  renders a visibly different, denser scatter and a **third teaching-case
  button, "Looks coherent, weakly integrated," correctly appears** for this
  snapshot (screenshot on file with the orchestrating session) — confirming
  gap 3 below is genuinely data-driven, not a code path that only happens to
  fire (or fail to fire) for the one snapshot originally tested.
- Gap 2 below (only 1/15 snapshots individually exercised) is accordingly
  now closed for at least one additional, materially different snapshot;
  the remaining 13 were not clicked through individually but exercise the
  identical, snapshot-agnostic code path.

## Part 6 — known simplifications and explicitly stated gaps

1. **Control-mode headings are real but sparse, EXCEPT for 10 curated
   examples** (see Part 4 and, for the follow-up feature that added the
   curated set, Part 8) — for most seed×condition×budget combinations,
   arrows are shown only at `t=T_u`, `f_E=100%`, if a snapshot happens to
   be generated, because `archetype_trajectories` genuinely does not
   contain per-timestep headings (confirmed by inspecting every key in
   `series`). For 7 specific (seed, condition) combinations (10 candidates
   total, since 3 of those 7 have 2 curated candidates apiece — see Part 8),
   a **separate, hand-picked dataset** (`illustrative_trajectories`) does
   contain a full `z_hist` array and is used instead, giving true
   frame-by-frame animation through Play/step/scrub for exactly those
   examples. This was not a shortcut taken to save effort in either
   direction: the sparse case reflects what the bulk data genuinely
   contains, and the curated case is a deliberately small, explicitly
   labeled set (never silently presented as if it covered everything) per
   the follow-up task's own instruction not to generate all 3×5×thousands
   of combinations.
2. **Only 1 of 15 planned Explore-mode snapshots existed at the time this
   was built and QA'd** (`seed2_no_control`; the background batch job was
   still running). All interactive mechanics (scatter, filters, sweep
   grid, compare, teaching cases, tooltips) were exercised against that
   one real snapshot's 1200 embedded candidates via Playwright. The other
   14 seed×condition combinations were **not** individually exercised
   (they didn't exist yet) — the code path is identical for all of them
   (nothing branches on which snapshot is loaded beyond reading
   `LS.snapshots[key]`), but this is stated plainly rather than implied to
   have been tested. Re-running `export_demo_data.py` + `build.py` once
   more snapshots land, then a quick re-click through the seed/condition
   dropdown, would be the natural follow-up check.
3. **The third teaching case ("Looks coherent, weakly integrated") does
   not currently appear** for the one available snapshot, per its own
   data-driven design (Part 2) — this is working as intended, not a bug,
   but is listed here since a reviewer clicking through the demo today
   will only ever see two of the three possible case buttons.
4. **Embedded candidate subsample.** Each snapshot embeds up to 1200 of
   (typically) 5000 generated candidates (`export_demo_data.py`'s own
   `EMBED_CAP`, unchanged) — every Pareto-nondominated candidate and the
   seed-reference `I0` are always kept; the rest is a fixed-seed random
   subsample. The UI states the embedded/full counts next to the
   candidate-count readout and in the "Metric questions..." Details panel;
   it does not claim to show the full landscape.
5. **Dual-range sliders use a CSS-only two-`<input type=range>` overlay
   trick** rather than a purpose-built custom slider component. This was
   verified to work correctly under Chromium (the only engine available
   for QA — see Part 7) via both scripted `dispatchEvent('input')` calls
   and visual screenshot inspection of the thumb positions/fill bar; it was
   **not** tested under Firefox or Safari, which is a real gap for a
   Firefox/Safari user (the `-moz-range-thumb` rule was written from
   memory of the standard pattern and reduces the risk somewhat, but is
   unverified).
6. **No composite score, no controller optimization.** Per the task
   brief's explicit "Do NOT implement" list, there is no single "thingness"
   score anywhere in this tab, and Control mode only *displays* the
   archetype trajectories' already-computed metrics — it does not run or
   expose any `max_u Q`-style optimization.

## Part 7 — tooling and testing

**Playwright + Chromium** was used for real headless-browser QA (not just
code review), with one environment wrinkle worth recording: the Python
`playwright` package's own pinned Chromium build
(`chromium_headless_shell-1234`) failed to launch —
`error while loading shared libraries: libnspr4.so: cannot open shared
object file` — because this sandbox has no system NSS/NSPR packages and no
passwordless root to `apt install` them. Root was not needed: `apt-get
download libnspr4 libnss3` (downloading a `.deb` to the working directory
requires no privileges) followed by `dpkg-deb -x` to extract the two
packages' shared libraries into a local directory, then launching
Playwright's *already-present* newer Chromium build
(`~/.cache/ms-playwright/chromium-1243`, left over from a prior session's
`npx playwright install`) with that directory prepended to
`LD_LIBRARY_PATH`, worked cleanly. This mirrors the "locally extracted
`.deb` shared libraries, no root required" approach recorded in
`STAGE6_5_VISUALIZATION_NOTES.md`'s own tooling note; none of this is
shipped with or required by `build/index.html`, which remains a plain
static file opened via `file://`.

**What was actually verified**, at 1440x900, 1280x800, and 1024x768, with
`page.on("console"/"pageerror")` listeners attached throughout (zero errors
recorded at any viewport across the full script below):

- Control view renders and is reachable both before and after visiting the
  Landscape tab (confirms no regression / no stray timers breaking it).
- Tabs 1–4 all still switch to and render their `#iiBody` content.
- Landscape Explore mode: scatter renders (1200 points for the one real
  snapshot); tooltip is genuinely `position:absolute` (this exact class of
  bug — see Stage 6.5 notes Part 0.5 — was specifically re-checked here
  since it's the same tooltip element); clicking a point selects a
  candidate and renders it on the lattice (100 bird nodes drawn); axis
  swap (X↔C, Y↔D); a filter slider driven via scripted `input` event;
  Pareto-only checkbox toggled on and off; Sweep-grid view toggle (6
  non-empty cells found for the default axis pair, clicked one); Pin +
  select-a-second-point → compare view (two lattice `<svg>`s confirmed
  present) → Exit compare; the two snapshot `<select>`s render; the
  "Global-looking consensus" teaching-case button clicked successfully;
  confirmed the third teaching-case button is correctly absent for this
  snapshot's actual data (not just "didn't check").
- Landscape Control mode: lattice renders; selecting `same_direction`
  reveals the four exterior-budget buttons; 50% budget selected; timeline
  slider scrubbed via scripted `input` event; play button clicked, left
  running ~700ms, then paused.
- Returning to the top-level Control nav view afterward still works.

**What was not machine-verified**: pixel-level visual regression against a
prior baseline (there is no prior baseline for a brand-new tab); Firefox/
Safari rendering (Chromium-only tooling, as above); the 14 not-yet-generated
snapshots (Part 6, item 2); pointer-drag gestures on the dual-range sliders
(exercised via `dispatchEvent`, not a simulated mouse drag — the visual
result was additionally confirmed correct by screenshot, so the rendering
side is verified even though the interaction was not driven identically to
a real user's mouse-down-drag-mouse-up).

See `stage6_flock/stage6_6_collective_landscape/tests/qa_report.md` for the
full QA run transcript and viewport screenshots list.

## Part 8 — real-trajectory playback for curated illustrative examples (follow-up)

Follow-up request, addressed 2026-09-07 after the base tab (Parts 0–7) was
built and independently re-verified against the complete 15-snapshot
dataset (Part 6a): the user wanted Control mode to animate **real** heading
arrows frame-by-frame (like `#svgMain`/`renderLattice` on the main Control
tab), for a small, curated, illustrative set spanning the (C,G,L,D) surface
and the five archetype conditions — explicitly **not** all
3 seeds × 5 conditions × thousands of candidates.

**Data.** A new top-level bundle key, `LANDSCAPE_DATA.illustrative_trajectories`
(10 entries, produced by a script the orchestrating session owns,
`run_illustrative_trajectories.py`, and already flowing through
`export_demo_data.py` into the existing `LANDSCAPE_DATA` placeholder — no
`build.py` change was needed for this follow-up). Each entry carries a
`label`, the displayed candidate's own `I` (20 ids), a full `z_hist`
(41 frames, `t=0..T_u+T_r`), and its own `series` (the same four metrics +
secondaries as `archetype_trajectories`, but computed for *this specific
candidate* rather than for I&#8320;, at full `t=1..40` resolution — no
stride-2 subsampling, unlike some `archetype_trajectories` exterior-budget
entries). 7 (seed, condition) pairs have a curated entry; 3 of those 7 have
**two** entries (an I&#8320; reference plus one alternative candidate
picked to illustrate something specific — a visually-scattered-but-
metrically-favorable interior, a high-integration/low-leakage pick, and a
jointly-high-C/high-G/low-L/high-D pick). No entry carries an explicit
`f_E` field; every entry's `controlled_exterior` count was checked against
that seed's own `f_E=1.00` archetype metadata and matches exactly (13 for
seed 2, 13 for seed 4's disordered condition) — so this pass treats every
curated entry as an `f_E=100%` recording and never surfaces one at a
lower exterior budget (see "the `f_E` gate," below).

**Where the data lives in the UI.** `renderLsControl()` (unchanged in
overall structure from Part 3) now:

1. Looks up `lsIllustrativeGroup(seed, condition)` — a plain `.filter()`
   over `illustrative_trajectories`, only consulted when the current
   exterior budget is `"1.00"` (or the condition doesn't have a budget
   concept at all, e.g. `no_control`/`shell_only`). Any other budget value
   (25/50/75%) always falls back to the pre-existing sparse-heading path,
   **even for the 3 conditions that do have a curated entry at 100%** —
   this is a deliberate, stated gate (see "the `f_E` gate" below), not an
   oversight.
2. When the group is non-empty, an **"Example" selector** (small button
   row, same visual pattern as the Seed/Condition/Exterior-budget rows)
   appears — but **only when the group has more than one entry** (3 of the
   7 pairs). For the other 4 pairs (a single curated entry each), no
   selector is shown; that one entry is used automatically, since there is
   nothing to choose between.
3. `activeSeries` normalizes the two different series field-naming
   conventions in this bundle (archetype: `H_star`/`H_E`; illustrative,
   matching Explore mode's own candidate columns: `Hstar`/`He`) to one
   shape once, so every downstream read (`activeSeries.H_star[tIdx]`, the
   four trace charts, etc.) is unaware of which source it came from.
4. `headings = illEntry ? illEntry.z_hist[t] : (existing sparse-fallback logic)`
   — when a curated example is active, this now uses `z_hist[t]` at
   **every** `t`, not only `t=T_u`, giving genuine frame-by-frame
   animation through the full Play/pause/step/scrub controls already
   built in Part 3 (no changes were needed to the playback controls
   themselves — they already just increment `st.control.tIdx` and
   re-render, and re-rendering now happens to pull a different, real
   heading frame each time).

**The `S(I)`/`E_near(I)` subtlety (the coordinator's flagged risk,
verified and handled).** For the 3 non-I&#8320; curated candidates, the
displayed candidate's own 2-hop structural neighborhood is genuinely
different from I&#8320;'s — because the simulator always physically forces
I&#8320;'s own shell/near-exterior (`meta.shell`/`meta.controlled_exterior`
in `archetype_trajectories`, regardless of which candidate is being
*viewed* for metric-comparison purposes), reusing `meta.shell` to decide
"is this a structural-shell node" would silently mislabel the alternative
candidate's own boundary. Fixed by computing `candSets =
lsBFSRoles(lattice, activeI)` (the exact same function Explore mode already
uses) on **whichever** `I` is currently displayed, and using `candSets` —
not `meta`— for the "structural shell (not actuated)" / "near exterior"
ring roles, while still using `meta.shell`/`meta.controlled_exterior` (only)
to decide the "actuated now" glow, since that is a fact about the physical
simulation, not about the candidate being looked at. This is a strict
generalization rather than a special case: for I&#8320; itself, `candSets`
is numerically identical to `meta.{shell,near_exterior}` (already verified
in Part 5's BFS check — 12/13 either way for seed 2), so the pre-existing
I&#8320;-only behavior is reproduced exactly, not approximated, when no
curated non-I&#8320; candidate is active. Visually confirmed via screenshot
(`ctrl_seed2_nocontrol_ex1_*.png` in this session's QA output): the
"Scattered-but-connected (diagonal snake)" candidate renders a diagonal
blue interior with its *own*, differently-shaped orange shell ring around
it — not I&#8320;'s compact one.

**The `f_E` gate.** Because no curated entry carries an explicit `f_E`
field, "is a curated example available" is gated on `fE === "1.00"` in the
JS rather than on any per-entry field. This means: switching the exterior
budget away from 100% for `same_direction`/`opposite`/`disordered`
**always** drops back to the pre-existing sparse/no-arrows path, even
though a curated 100% example exists for that same (seed, condition) pair
— confirmed correct behavior (not a bug) by explicit QA (see below) and
stated in-UI via the same heading-note mechanism already used for the
"no curated data at all" case, so a user moving the slider sees an
explanation, not an unexplained disappearance of the arrows.

**Metric card / legend updates.** The live-metrics card title now appends
the active example's label when one is active (e.g. "Live metrics at
t=12 — Jointly high-C/high-G/low-L/high-D pick"), and the lattice legend's
"interior" line reads "interior I (this candidate)" instead of "interior
I&#8320;" whenever a non-default candidate is being shown, so the two
representations (metrics and lattice) are never visually implied to both
be about I&#8320; when they aren't.

**QA for this follow-up.** A dedicated Playwright script exercised, at
1440x900/1280x800/1024x768 (same Chromium + extracted-`.deb`-libs
workaround as Part 7 — redone from scratch this session, nothing persists
between sessions): `seed2/no_control` (2 examples: switched between them,
confirmed the metric-card title and lattice both changed, confirmed the
lattice SVG's own markup genuinely differs after one step-forward and
after ~900ms/~3-4 ticks of Play, confirmed the time display advanced to
`t=4/40`); `seed2/shell_only` (2 examples, selector present);
`seed2/same_direction` (1 example, no selector shown, confirmed **and**
confirmed the fallback correctly re-engages at `f_E=50%`, including one
false-alarm investigated and ruled out as a test-script issue, not a
product bug — see Part 5); `seed3/same_direction` ("global-cascade" case,
confirmed active); `seed4/disordered` (2 examples, confirmed the
"Jointly high-C/..." title renders); `seed3/opposite` (a pair with **no**
curated data at all — confirmed 0 Example buttons and the correct
sparse-fallback note); Explore mode, tabs 1–4, and the main Control page
all re-confirmed unaffected in the same script run. **Zero console/page
errors** at all three viewports across the entire script. Full transcript
in `stage6_6_collective_landscape/tests/qa_report.md`'s own follow-up
addendum.

**What was simplified / not covered, stated plainly.** Only the 10 curated
candidates animate with real headings; every other candidate (in Explore
mode, or as I&#8320; under any non-curated seed/condition/budget
combination in Control mode) still shows sparse or role-only headings,
exactly as before — this is the explicit scope the user asked for
("does not need to cover all combinations exhaustively if they are chosen
well"), not a shortfall. The Example-selector's button labels are the
curator's own free-text `label` strings, displayed verbatim — no attempt
was made to normalize or re-word them.
