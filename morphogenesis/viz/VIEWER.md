# VIEWER.md — morphogenesis/viz/ (reusable by all later stages)

## Status: `ESTABLISHED` (functional, tested for structural correctness), `NOT DONE`: live-browser rendering verification

## What this is

`build_viewer.py` + `build_index.py`: a self-contained HTML viewer builder,
not tied to any one stage of the morphogenesis programme. Given rollout
arrays (positions, secretion, optionally target positions and a ligand
probe-grid), it produces a single `.html` file with:

- inline JS/CSS only, **no network or CDN dependency** (checked by
  construction — the template has zero `<script src=...>`/`<link>` tags to
  external URLs),
- data embedded as a plain JSON `<script type="application/json">` block
  (not gzip-compressed — a deliberate simplification over a hand-rolled
  in-browser decompressor, see "Design decisions" below),
- play/pause, single-step, frame scrubber, speed control,
- an arena panel (cells colored by RGB of signals 2-4, per the papers'
  convention — `cellColor()` maps `a.s` channels 1,2,3 (0-indexed, i.e.
  signals 2,3,4) directly to R,G,B), optional motion trails, optional
  per-ligand heatmap on a probe grid (rendered only if the rollout dict
  includes a `ligand` field — absent for OBSERVABLE-tier-only builds unless
  probe data was explicitly computed and included),
- a linked time-series panel (mean per-cell secretion, mean per-cell speed)
  with a cursor synced to the scrubber,
- **audit-only**: target positions (star markers) — gated by the
  `is_audit` flag, which also controls whether `target_x` is embedded in
  the data at all (an OBSERVABLE-tier build never receives `target_x` in
  its `rollout_to_json_dict()` call, so the file **physically** cannot leak
  it, not just UI-hidden).
- a header banner (`build_html`'s `banner_text`/`banner_class` args) with
  an unmissable red banner for unvalidated data (`banner-unvalidated` CSS
  class) vs. green for validated.
- side-by-side synced compare mode: pass **multiple** rollout dicts to
  `build_html()`'s `rollout_dicts` list — each gets its own arena+time-series
  panel, all driven by the same `curBin`/scrubber/play state (see the JS:
  `rollouts.forEach(...)` in both `drawArena`/`drawTimeSeries` and the
  shared `render()`).

## What is NOT in this build (disclosed)

- **Per-cell softmax identity-belief heatmap** and **prediction
  errors/free energy panels** (both listed as audit-only additions in the
  task) are **not implemented** in this pass — `hidden`-tier scalar/vector
  time series (`free_energy`, `pred_err_1/2`, `v_expect`) are saved by
  `code/storage.py` and available to a future viewer revision, but the
  current `build_viewer.py` template only renders arena + secretion/speed
  time-series. Flagged in `OPEN_QUESTIONS.md`.
- **No live-browser rendering test** was performed (headless session
  environment, no `node`/browser binary available — checked:
  `which node chromium chromium-browser google-chrome` all failed). Static
  checks only: template placeholder substitution completeness (`grep -c
  "__"` = 0 after build), brace/paren balance in the embedded script, and
  the `<20MB` size assertion (`build_html` raises if exceeded). **A human
  should open at least one built file in an actual browser before treating
  this as fully verified.**

## Design decisions

- **No gzip+in-browser-inflate.** An initial version attempted this (to
  reduce file size); a hand-rolled JS DEFLATE decoder is exactly the kind
  of untested, high-risk code this program's ground rules warn against
  shipping without empirical verification (c.f. the `spm_DEM_embed`
  misreading episode in `PORT_DESIGN_UPDATE.md`). Given this session had no
  browser available to test the decoder, it was **discarded** in favor of
  plain (uncompressed) embedded JSON, which needs no client-side decoding
  logic to get wrong. Trade-off: larger files (still well under the 20MB
  limit for every exemplar built this session — largest so far ~525KB).
- **Downsampling**: `downsample_trailing_time_axis()` caps embedded frames
  at 600 by default (stride-subsampling), declared in the rollout's
  `label` field (e.g. `"... [downsampled x2]"`) per the ground rules'
  requirement that downsampling be declared in the file header/label.

## Exemplar selection rule (declared, `build_index.py`)

Per batch of same-kind runs: **median, best, worst by type-constrained
Hungarian distance to template** (a hidden-tier metric — `.py`
`hungarian_distance_type_constrained()`), plus **2 uniformly random picks**
(seeded, seed recorded in the index). This rule is recorded in
`index.html` itself (the `rule` div at the top of the page), not only here.

## Built this session (see `output/` and `index.html`)

- `output/audit/a3_long_run_audit.html` + `output/observable/a3_long_run_observable.html`
  — the A3 1024-bin long run (Octave oracle, validated).
- `output/audit/a4_sensitivity_pair_audit.html` — the A4 synced compare
  (baseline vs. `eps=1e-6` perturbed initial condition).
- Part C perturbation viewers: built from `data/oracle_traces/perturbations/`
  once the batch (launched this session) completed — see `index.html` for
  the final list and `PERTURBATIONS_EXECUTED.md` for what each shows.
- **Octave-vs-Python synced pairs for B4 configs: NOT built** — Part B did
  not produce a working Python trajectory (L2 failed), so there is nothing
  to pair against the oracle. `OPEN_QUESTIONS.md` item 8.

## Usage

```python
import sys; sys.path.insert(0, "morphogenesis/viz")
from build_viewer import rollout_to_json_dict, build_html

rd = rollout_to_json_dict("my run", a_x, a_s, target_x=target_x)  # a_x,a_s: (N,dim,n)
build_html([rd], "My Viewer", "VALIDATED: ...", "banner-validated",
           "config=...\nengine=...\nseed=...", is_audit=True, out_path="out.html")
```
