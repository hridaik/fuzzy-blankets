# GAPS — revision of demo_v1
**CONTAINS HIDDEN INFORMATION.**
- **O3b** (second glow variant) is not shown: "microscope image (glow)" uses O3a only.
- **3.1 microscope image (cell markers)**: T4 has no cell-marker grouping, so the outline is T5's spot detection + the T4 linking rule (position-only cell tracker). It finds 19 of 24 cells after the cut (spots merge), 24 before.
- **3.1 outline of the glow image** is the organism's foreground pixel set (the pipeline's own grouping), not an alpha hull.
- **2.2 Merge clip**: the run starts already merged; the two outlines are drawn from the cell-id sets (ids 0–23 vs 24–47).
- **4.3 interface panel**: arrow widths computed from a settled frame mapped to the template by a rigid fit; coupling = sum over lit cells of exp(−distance) for each unlit cell. Middle and tail-end discs share one width scale.
- **Flock persistence** (5.1): not tested → shown as "not tested".
- **Appendix C**: full provenance (run ids, seeds, files) is inside a closed "Sources" drawer on that page.
- Cosmetic leftovers from the first version (4.2 chart label overlap, 3.2 light-switch bubble placement) were not specifically re-checked; see `screenshots/`.
- Not re-run here: the live server stays stopped/untouched; no new simulation beyond deterministic regeneration of exemplar assets.
