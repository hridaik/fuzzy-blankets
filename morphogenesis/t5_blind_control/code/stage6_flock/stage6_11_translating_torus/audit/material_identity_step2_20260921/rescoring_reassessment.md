# Rescoring reassessment — Step 1's ID-independent readouts, re-examined

Audit only, per task §12. Step 1's readouts are not deleted or overwritten
anywhere. Script: `code/rescoring_reassessment.py`. Raw output:
`data/rescoring_reassessment.json`.

## 1. Frozen original material — how quickly does it lose relevance?

For every frame where the forward trace agrees with v1 (so its exact
membership is directly known), overlap with the exact t0 qualification
cohort is tracked. At the LAST such exactly-known frame per seed:

| seed | t0 cohort size | last exactly-known frame | frac of t0 cohort retained |
|---|---|---|---|
| 500 | 33 | t=107 (episode end) | 0.909 |
| 501 | 30 | t=76 (episode end) | 0.200 |
| 502 | 21 | t=31 (right before permanent divergence) | 0.571 |
| 503 | 21 | t=46 (right before the t=47 split) | 0.762 |
| 504 | 28 | t=93 (episode end) | 0.607 |

Seed 501 is the clearest illustration of the task's underlying concern: by
episode end, only **20%** of the exact t0 cohort remains in a population
this task's own independent forward-continuity rule certifies as the SAME
materially-continuing entity (identity-valid throughout, per
`seed_501_identity.md`). **`original_material`'s frozen-ID readout would
therefore read this seed as almost entirely turned-over material by
release, even though the forward trace finds no discontinuity anywhere in
its path.** This directly quantifies how much stricter `original_material`
is than a continuity-respecting standard: for a genuinely continuing
population under ~46 steps of ordinary gradual turnover, "still literally
the same IDs" and "still the same organizational entity" diverge sharply
long before any real identity break occurs. This does not mean Step 1's
`original_material` readout was WRONG for what it measures (a strict,
disclosed, intentionally conservative standard) — it means it measures a
different, stricter question than forward material continuity does, and
the two should not be read as interchangeable.

## 2. Field-direction: v1-anchor vs. trace-anchor, radius-sensitivity

For every seed, at the final episode frame, the SAME field-direction
formula (`branch_adjudication_611.py`'s own `field_direction_readout`,
reused unmodified) was computed twice: anchored at v1's own current
centroid (the historical choice, via v2 in Step 1 — this pass uses v1's
centroid as the closest available exact proxy, see `identity_validation.md`
for why v2's own centroid was not separately recomputed) and anchored at
`ForwardMaterialTrace611`'s own centroid.

| seed | v1-anchor field-direction (r=3.0) | trace-anchor field-direction (r=3.0) | gap |
|---|---|---|---|
| 500 | 0.000 | 0.000 | none |
| 501 | 0.933 | 0.933 | **none — anchors agree** |
| 502 | 0.412 | 0.070 | **large** |
| 503 | 0.879 | 0.308 | **large** |
| 504 | 0.000 | 0.000 | none |

**Radius sensitivity (seeds 502, 503), r ∈ {1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0}:**
the v1-anchor vs. trace-anchor gap is **large and stable across the entire
radius range tested** for both seeds — not an artifact of the specific
r=3.0 historical choice. (Seed 502: v1-anchor 0.19–0.80 vs. trace-anchor
0.06–0.13 across all seven radii; seed 503: v1-anchor 0.84–0.96 vs.
trace-anchor 0.20–0.40 across all seven radii. Full table:
`data/rescoring_reassessment.json`.)

**This is the empirical core of this task's headline finding, from a
completely different angle than the trace CSVs themselves**: for seeds 502
and 503, the historical "ID-independent" field-direction verdict is **not
robust to where the field is anchored** — it depends materially on
trusting v1's own (frequently-wrong-per-this-task's-other-evidence)
pointer for where to center the measurement. Anchoring the exact same,
unmodified formula at a defensibly-continuing material target instead
gives a starkly different answer for both seeds. Seed 501's agreement
between anchors is, by contrast, a positive robustness result — consistent
with `seed_501_identity.md`'s finding that v1 and the trace converge onto
the same population there.

**This was not tuned to produce this result.** The radius was swept in
full and reported in full; no radius was selected after seeing which one
"worked." The formula, threshold, and target set were fixed in advance
(the historical r=3.0 default plus a symmetric sensitivity band around it).

## 3. What this does and does not establish

**Established**: the "ID-independent" name for Step 1's field-direction
readout is accurate in the narrow sense that the readout itself does not
look up bird IDs once centered — but the readout's *answer* is sensitive
to a tracker-derived anchor choice, and that sensitivity is large enough,
for 2 of 5 seeds, to flip the qualitative picture (0.07 vs 0.41; 0.31 vs
0.88) depending on which tracker's pointer is trusted for centering.

**Not established**: which anchor is "correct" in some absolute sense —
this task's position is that the forward-material-trace anchor is more
defensible BECAUSE its own continuity claim is independently validated
(§ identity_validation.md) against data that never touched these five
seeds, not because it is newer. Step 1's own verdict (using v2's centroid,
not v1's) was not exactly reproduced here (disclosed gap,
`identity_validation.md`) — it is plausible v2's centroid tracks closer to
the trace's than v1's bare argmax pointer does, which would soften this
finding for Step 1's ACTUAL published numbers specifically; this is not
resolved here and is flagged as follow-up.
