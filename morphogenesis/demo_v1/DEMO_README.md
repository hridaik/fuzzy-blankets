# demo_v1 — interactive presentation of the programme so far
**CONTAINS HIDDEN INFORMATION — never give this folder to a blind session** (see BANNER_HIDDEN_INFORMATION.md).

## Open it
Double-click `index.html` (Chrome / Firefox / Safari, no network, no server). Data are `.js` files in `data/` that assign globals and are loaded per chapter; the first page needs only `js/` (≈ 0.2 MB). Total size ≈ 20 MB.
Keys: ← / → chapter · space play/pause/continue at a callout · F presenter mode · N speaker notes · T hidden-truth view (2.3, 3.4, 4.2, 4.4). URL hash `#3.2`. "Export key frames" saves PNGs of a chapter's scripted pause points (static chapters: one frame; 1.3: one per button; 3.2: one per exemplar).

## Presentation paths
**10 minutes**: 1.1 (play, 4 callouts) → 1.4 (Overlay) → 1.5 (play to the end) → 3.1 (play across the cut; open "How is the outline drawn?") → 3.2 (Untouched, Cut, Light switch) → 4.4 (play; 8 callouts; press T at the end) → 4.5 → 5.1.
**25 minutes**: 1.1 → 1.2 (click two cells) → 1.3 (4 buttons) → 1.4 → 1.5 → 2.1 → 2.2 (six tools) → 2.3 (T, show outline) → 3.1 → 3.2 → 3.3 → 3.4 (T) → 4.1 (Reveal) → 4.2 (T) → 4.3 → 4.4 → 4.5 → 5.1 → 5.2 → Appendix A (drag r, g).
Appendix B (words) and C (about the data; provenance table in a closed drawer) are for questions.

## Asset provenance
Moved to **Appendix C** of the demo (and the Sources drawer of each chapter).
Rebuild: `python3 build/build_*.py` (white-box; needs the sealed live directory; set `PYTHONDONTWRITEBYTECODE=1`). Tests: `python3 build/test_demo.py` (headless Chromium; report `build/test_report.json`, screenshots in `screenshots/`). Other files: COPY_CHANGES.md, GAPS.md, COMPUTE_PLAN.md, `../testbed_v3/audit_t5/AUDIT_T5.md`.
