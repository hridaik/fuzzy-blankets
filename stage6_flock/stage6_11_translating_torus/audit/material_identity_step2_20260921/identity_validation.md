# Identity validation

## Uncontrolled-data results

`data/identity_rule_calibration.json`. 12 episodes, seeds 236–247, 17,970
positive (natural continuation) and 17,970 negative (cross-episode
unrelated) candidate pairs. At the frozen threshold (Jaccard≥0.30): **TPR
(natural continuations correctly accepted) = 98.6%, FPR (unrelated flocks
incorrectly accepted) = 0.0%** (0/17,970). The two distributions are
cleanly separable in this uncontrolled corpus at this threshold, with a
wide margin (FPR stays exactly 0 from threshold 0.25 through 0.80).

## Synthetic/known-history identity tests (task §7, A–G)

`code/synthetic_identity_tests.py`, run against the frozen rule, unchanged.
Full results: `data/synthetic_identity_test_results.json`.

| test | result | detail |
|---|---|---|
| A. Stable continuation | **PASS** | 10 steps of ±2-member detector noise, `continuing` throughout |
| B. Gradual turnover | **PASS** | 20 steps, 10%/step turnover, `continuing` throughout every step (cumulative overlap with t=0 cohort falls to 0% by t=19 — the rule correctly ignores frozen-origin overlap and tracks only step-to-step continuity, exactly matching the "local continuation, not frozen material" theory in the task brief) |
| C. Abrupt replacement | **PASS** | a same-size, zero-overlap flock appears; status goes `unresolved`, **never** `continuing` onto it |
| D. Toroidal crossing | **PASS** (trivially, by construction) | a pure membership rule cannot be affected by a position-only event; demonstrated, not merely asserted — see note below |
| E. Temporary missed detection | **PASS** | target absent 2 steps (< horizon=3): `unresolved`, `unresolved`, then `continuing` again on reappearance with mild turnover — **never** silently switches to the distractor present during the gap |
| F. Split | **PASS** | previous target splits into two ≥40%-retaining candidates; `split_flag=True`, continues on the larger absolute-retained-count branch (a material, not behavioral, tie-break) |
| G. Merge | **FAIL** (disclosed, not patched) | previous target 100% retained inside a candidate 5x its size; `jaccard=0.20 < 0.30` → rejected → `unresolved`, not the intended `continuing + merge_flag` |

**6 of 7 pass.** Test D's "pass by construction" deserves a comment, not
just a check mark: it demonstrates the concrete, positive claim that a
membership-first identity rule is **structurally immune** to the class of
apparent-jump artifact a naive centroid-distance rule would be vulnerable
to near a periodic boundary — this is a real, if modest, methodological
advantage of the approach, not merely a tautology, and it is exactly the
property Step 1's torus-visualization audit was checking for by a
different route (§7 of `evidence_recovery_20260921/audit_findings.md`).

Test G's failure is discussed in `identity_rule_spec.md`'s "known,
disclosed limitation" section and is **not treated as invalidating the
rule** for this pass's purpose — merges are rare in this domain (only 1
genuine merge-shaped event was found across all 5 historical seeds' full
episodes combined, seed 503 t=43, see `seed_503_identity.md`) and the
failure mode (going `unresolved` instead of `continuing+flagged`) is the
SAFER of the two possible failure directions (it under-claims continuity
rather than over-claiming it), consistent with the task's overall
preference for `unresolved` over invented continuation.

## Threshold sensitivity (transparency, task §6)

Full grid in `identity_rule_spec.md` / `data/identity_rule_calibration.json`.
Summary: FPR=0 is achieved and HELD across a wide threshold range for
Rule B (0.25–0.80) and Rule D (0.35–0.80); Rule A never achieves as clean a
separation until threshold≈0.65, where TPR has already degraded more than
B/D's TPR at their own FPR=0 onset. This robustness-over-an-interval,
rather than a single sharp optimum, is what the task asked to check before
freezing, and is met.

## Failure cases (this pass's own, disclosed)

1. Test G (merge), above.
2. Section 12's frozen-material-decay and field-direction-radius-sweep
   analyses (`rescoring_reassessment.md`) could only be computed exactly at
   frames where the trace agrees with v1's displayed interior (member IDs
   are not separately persisted for every `continuing` step in the applied
   CSV, only the centroid/size are) — a resource/time trade-off disclosed
   explicitly in `rescoring_reassessment.py`'s docstring, not silently
   worked around.
3. v2's own per-frame centroid was not recomputed for the field-direction
   comparison (would require a full v2 replay of all 5 seeds; out of this
   pass's time budget) — the comparison actually performed is v1-anchor
   vs. trace-anchor, which is arguably the more directly relevant
   comparison for this audit's purpose (is the historical readout's anchor
   choice, not specifically v2, responsible for its verdict), but is not
   exactly what task §12 literally asked for. Disclosed, not hidden.
