# Next-step recommendations (implications only — no controller/authority work performed)

1. **Re-run Step 1's `branch_adjudication_611.py` counterfactual branches
   for seeds 501/502/503 through `ForwardMaterialTrace611`**, to resolve
   `STEP2_FINDINGS.md`'s first "provisional" item — this directly tests
   whether the counterfactual-branch analysis and the real-run analysis
   would agree if compared on the same identity standard. Mechanically
   simple (the branches already produce `(r_hist, z_hist)`; only needs
   `ForwardMaterialTrace611.start()`/`.step()` calls added to
   `track_trajectory()`), but changes Step 1 artifacts, so should be scoped
   as its own reviewed pass rather than folded in silently.

2. **Replay v2 (`LineageTrackerV2`) per-frame for all 5 seeds** and redo
   `rescoring_reassessment.py`'s field-direction anchor comparison using
   v2's actual centroid rather than v1's (used here as a documented proxy).
   This would give the literal comparison task §12 asked for.

3. **If a controllability re-study is ever run** (still not performed by
   either audit pass), evaluate the reported turn specifically against the
   `ForwardMaterialTrace611`-identified continuing target for seed 503,
   not against whatever v1 happens to display — this is now the single
   most load-bearing open question this two-part audit has surfaced: does
   ANY tested control condition move the ACTUAL continuing material, not
   just move a display pointer onto a fortuitously-aligned neighbor.

4. **A no-control / matched-random comparator specifically for the
   material-continuing targets** (seed 502's flat 0.19→0.10 population,
   seed 503's modestly-rising 0.05→0.35 population) would give the
   intervention-effect evidence this task explicitly scoped out.

5. **Consider seed 501 for reconsideration**, on real-run evidence only —
   not as a redesign instruction, but as a factual flag: this task's
   material trace shows the real, actual episode's continuing target does
   turn and persist, with only a brief, self-correcting 4-step identity
   detour. This is a materially different picture from Step 1's
   counterfactual-branch-based withdrawal and deserves a decision by
   whoever owns the historical-result-integrity question, not an automatic
   re-promotion.

6. **The merge-detection limitation (Test G) is low-priority** given only
   one real instance was found across all 5 seeds' full episodes (seed
   503, t=43) — worth a principled fix (e.g. an explicit OR-clause on
   near-total R_old) only if a future application domain produces merges
   more often than this one did.

7. **Do not treat `ForwardMaterialTrace611` as a drop-in replacement for
   v1/v2 in any future controller work** without first addressing what this
   task deliberately left out: re-planning-aware continuation (this tracker
   only ever looks one step back), and a validated, non-diagnostic
   split/merge policy. It was built and validated as an AUDIT comparator,
   exactly as scoped.

Nothing above is a controller, authority-estimator, or candidate-pool
change, per the task's explicit boundary.
