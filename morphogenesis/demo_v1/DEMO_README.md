# demo_v1 — interactive presentation of the programme so far
**CONTAINS HIDDEN INFORMATION — never give this folder to a blind session** (see BANNER_HIDDEN_INFORMATION.md).

## Open it
Double-click `index.html` (Chrome / Firefox / Safari, no network, no server). Data are `.js` files in `data/` that assign globals and are loaded per chapter; the first page needs only `js/` (≈ 0.2 MB). Total size ≈ 4 MB.
Keys: ← / → chapter · space play/pause/continue at a callout · F presenter mode · N speaker notes · T hidden-truth overlay (2.2, 3.4, 4.2, 4.3). URL hash `#3.2`. "Export key frames" saves PNGs of a chapter's scripted pause points (static chapters: one frame; 1.3: one per button; 3.2: one per exemplar).

## Presentation paths
**10 minutes**: 1.1 (play, 3 callouts) → 1.4 → 1.5 (play to the end) → 3.2 (Undisturbed, Cut, Light switch) → 4.3 (play; 8 callouts; press T once at the end) → 4.4 → 5.1. Toggles: T in 4.3.
**25 minutes**: 1.1 → 1.2 (click two nodes) → 1.3 (4 buttons) → 1.4 (Overlay) → 1.5 → 2.1 → 2.2 (T) → 3.1 (steps 1–5, slide the radius, two-cluster dish) → 3.2 (3 exemplars) → 3.3 → 3.4 (T) → 4.1 (Reveal) → 4.2 (T) → 4.3 → 4.4 → 5.1 → 5.2 → Appendix A (drag r, g).

## Asset provenance
| chapter | assets | seeds / ids | files |
|---|---|---|---|
| 1.1 | Octave oracle (canonical clock), natural body 2100 | oracle seed 0; run_00011 | `m2a_audit_and_library/data/part0/direct_primary_0000.mat`; `testbed_v3/data/raw_v4/natural/a_cal_2100.pkl` |
| 1.2–1.4 | same body, states a (run_00011) and b (run_00133), t = 3000–3059 | body 2100 | `a_cal_2100.pkl`, `b_cal_2100.pkl` |
| 1.5 | re-simulated N = 1, 4, 24, σ_h = 0.7, 600 tu | seed 0 (rule in `build_mem15.py`) | `data/mem15.js` |
| 2.1, 2.2, 3.1 | package v3 observables + hidden tier | run_00011, 00263, 00640, 01105, 00702 | `testbed_blind_v3/runs`, `testbed_v3/data/blind_v3_hidden` |
| 3.2 | frozen T5 monitor (hash in `FROZEN_HASH.txt`) on run_00266 (undisturbed), run_00263 (cut), held-out seed 6007 controller (O1 regenerated, verdicts equal the live log in 164/164 frames) | 6007 | `data/c32.js` |
| 3.3 | serial replacement, noise-free, seed 0 | 0 | `data/c33.js` |
| 3.4 | T4 outputs + true state | 260 natural dishes | `t4_blind_identity/outputs`, `testbed_v3/data/blind_v2_hidden` |
| 4.1 | re-simulated lights L1–L5, amp 5, 10 tu, dev seed 5001 (a and b clone) | 5001 | `data/c41.js` |
| 4.2 | T5 blind map, audit A4 true maps, true duration curve; equal-dose clips re-simulated on dev seed 5004 | 4 dev dishes; 6000/6003/6007 | `data/c42map.js`, `data/c42clips.js` |
| 4.3 | sealed hidden logs + T5 episode logs | seed 6007: episodes 988 (ctrl), 991 (random), 994 (whole, dose-matched), 989 (twin) | `data/c43.js` |
| 4.4 | heldout_eval.json, audit A3 regret, worst episode seed 6026 (ep 1121) | 60 dishes | `data/c44stats.js`, `data/c44worst.js` |
| 5.1 | syntheses, audit, flock stage-6.9 clip (seed 37), oracle, 4.3 clip | | `data/c51flock.js` |
Rebuild: `python3 build/build_*.py` (white-box; needs the sealed live directory). Tests: `python3 build/test_demo.py` (headless Chromium; report `build/test_report.json`, screenshots in `screenshots/`).
Other files: GAPS.md, COMPUTE_PLAN.md, `../testbed_v3/audit_t5/AUDIT_T5.md`.
