# Interactive Demo v2

A polished, self-contained, six-tab walkthrough of Stage 6's collective-identity
research: **Boundary → Causal access → Control → Collective landscape →
Adaptive → Translation** (OBSERVE → INFER → PROBE → CONTROL → ADAPT → MOVE).

This is a **presentation layer over existing results**. No flock dynamics are
implemented in JavaScript, no science is rerun, and no new statistics are
computed anywhere in the browser. Every number, trajectory, and boundary set
shown was already produced by the Stage 6 pipeline; the one exception is a
2-line post-hoc application of an existing frozen formula (Q clumpness,
`morphology.q_clump`) to already-frozen candidate node sets, documented in
`VISUALIZATION_NOTES.md`.

It does **not** replace or modify the original demo at
`interactive_demo/build/index.html` — that file is untouched.

## Open it

```
open build/index.html
```

or just double-click it. No server, no build step needed to *view* it — the
committed `build/index.html` is already a single, fully self-contained file
(~4.4 MB, data inlined) that works from `file://`.

## Rebuild it

Only needed if you change `src/` or regenerate `data/`.

```bash
# 1. Regenerate the six compact v2 data bundles from the frozen Stage 6 result
#    files (safe to skip if data/*.json is already up to date):
cd src/data_prep
python3 prep_tab1_boundary.py
python3 prep_tab2_causal_access.py
python3 prep_tab3_control.py
/usr/bin/python3 prep_tab4_landscape.py   # needs numpy; see note below
python3 prep_tab5_adaptive.py
python3 prep_tab6_translation.py

# 2. Inline data + css + js into build/index.html:
cd ..
python3 build_v2.py
```

`prep_tab4_landscape.py` imports `morphology.py` from
`stage6_10_emergence_adaptive_control/code/` and needs `numpy`, which is not
on the default `python3` in this environment — run it with `/usr/bin/python3`
(has numpy 1.26) or any interpreter that has numpy available. The other five
`prep_*` scripts are pure stdlib `json` re-exports and run under any Python 3.

### Validate a rebuild

```bash
python3 src/pw_test.py
```

Opens `build/index.html` in headless Chromium via Playwright at 1440×900,
1280×800 and 1100×720, clicks through all six tabs, exercises the timeline,
method/seed/axis selectors, and the provenance drawer, and reports console
errors and horizontal overflow. See `VISUALIZATION_NOTES.md` for the full
checklist that was actually run against this build.

## Layout

```
v2/
  src/
    template.html        shell: header, progress rail, tab nav, legend,
                          6 empty tab panels, shared timeline footer,
                          provenance drawer -- placeholders for css/data/js
    css/main.css          design tokens (extends the v1 demo's palette) + layout
    js/shared.js           bird glyph renderer, timeline controller, tooltip,
                          provenance drawer, lattice projector, number formatter
    js/tab1.js .. tab6.js  one module per tab; each registers window.Tabs.tabN
    js/main.js              tab switching, progress rail, legend, Next button
    data_prep/prep_tabN_*.py  one export script per tab, reused verbatim from
                          frozen Stage 6 result files -> data/tabN_*.json
    build_v2.py            inlines css/data/js into template.html -> build/index.html
    pw_test.py              Playwright validation script (see above)
  data/
    tab1_boundary.json .. tab6_translation.json   compact, pre-built bundles
    (regenerate with data_prep/*.py; committed here so build_v2.py runs standalone)
  build/
    index.html            the deliverable -- open this
```

## Source-stage mapping (six tabs)

| Tab | Question | Primary Stage 6 source |
|---|---|---|
| 1. Boundary | Can trajectories reveal a compact screen around a collective? | `interactive_demo/data/seed2__no_control__cw.json` (lattice/roles), `stage6_7_blind_boundary/data/predictive_boundary_panel.json` (B^pred, screening scatter), `stage6_5/boundary_inference/data/held_out_evaluation.json` (3-seed generalization), `v1_mechanism_audit/data/predictive_screening.json` (headline log-loss) |
| 2. Causal access | Which exterior states can move the collective toward a chosen target? | `stage6_10_emergence_adaptive_control/data/audit_trace.json` + `audit_hypotheses.json` (H3: KL causal effect vs. signed target authority A_j^{h*,τ}), `interactive_demo/data/stage6_10_bundle.json` (lattice) |
| 3. Control | Does interface structure matter when steering a known collective? | `interactive_demo/data/seed16__{method}__cw.json` — the 9 frozen V1/V2/V3 control-policy bundles (Fiedler, random, connected patch, distributed shell, V2 conservative, sparse-interface-multicover/V3, full shell, direct-core diagnostic) |
| 4. Collective landscape | Which candidate regions look like coherent, individuated collectives? | `stage6_6_collective_landscape` candidates (C, G, L, D) via `interactive_demo/data/collective_landscape_bundle.json`, + post-hoc Q (clumpness) from `stage6_10_emergence_adaptive_control/code/morphology.py` |
| 5. Adaptive | What changes when the collective and its interface must be inferred online? | `interactive_demo/data/stage6_10_bundle.json` — one Stage 6.10 closed-loop 20×20 episode (observe → detect → adaptively steer → release), already exported for exactly this purpose |
| 6. Translation | Can the same online idea operate when the collective moves through space? | `stage6_11_translating_torus/data/viz_bundle_611__seed{500..504}.json` + `online_control_611__seed{...}.json` — the original Stage 6.11 **v1** identity/readout, all 5 seeds |

Full per-tab provenance (exact files, seeds, event times, formulas, and every
scope/omission decision) is in `VISUALIZATION_NOTES.md` and is also reachable
live inside the demo via the **Data & caveats** button.
