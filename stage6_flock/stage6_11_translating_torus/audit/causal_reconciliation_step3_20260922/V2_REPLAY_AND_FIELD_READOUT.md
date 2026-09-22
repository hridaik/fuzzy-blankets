# Exact v2 replay and field-direction readout reconciliation (Task D)

`code/v2_replay_and_field_readout.py`. Replays `LineageTrackerV2`
(`audit/lineage_v2_611.py`, imported unmodified) over the ACTUAL recorded
trajectory for all 5 control seeds (`data/viz_bundle_611__seed{n}.json`,
ground truth (r, z), never re-simulated), alongside v1
(`LineageTracker611`) and `ForwardMaterialTrace611`, all three consuming
the identical `detect_69.propose` candidate stream. Full per-frame
persistence: exact v1/v2/material member IDs, v2's own `prob`/`dwell`,
material trace status — `data/v2_replay_seed{500..504}.json`.

**Seeding convention (disclosed)**: v2 was never run online in the real
experiment. This pass starts it at the first step a candidate exists
(`cands[0]`), exactly mirroring `run_online_control_611.py`'s own v1
seeding convention — the same rule already used for v1, applied
consistently, not a new one invented for v2.

## Field-direction readout: exact historical formula, three anchors

`branch_adjudication_611.field_direction_readout(r, z, members, L,
radius, target_heading)` — imported and called **unmodified** (not
reimplemented), eliminating reimplementation-drift risk. Swept over the
full previously-used radius grid: 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0,
without selecting a favorable radius, at three anchors per frame: v1
members, v2 members (**the actual historical Step-1 anchor** — Step 2's
`rescoring_reassessment.md` had used v1 as a proxy for this, disclosed as
a gap; this pass closes it), and `ForwardMaterialTrace611` members.

## Results

### Seed 500 (sanity case)

v1==v2 exact member-set agreement at 22/108 frames (v1 and v2 diverge in
exact membership more often than they agree at the raw-set level — an
expected property of two structurally different trackers, not itself
evidence of a meaningful disagreement, since both report near-identical
readouts below). At the final frame (t=107), field-direction readout
across all three anchors and the full radius grid:

| radius | v1 anchor | v2 anchor | material anchor |
|---|---|---|---|
| 1.5 | 0.000 | 0.018 | 0.000 |
| 2.0 | 0.000 | 0.032 | 0.000 |
| 2.5 | 0.000 | 0.032 | 0.000 |
| 3.0 | 0.000 | 0.032 | 0.000 |
| 3.5 | 0.024 | 0.032 | 0.024 |
| 4.0 | 0.024 | 0.031 | 0.024 |
| 5.0 | 0.057 | 0.033 | 0.057 |

**v1 and material anchors agree EXACTLY at every radius** (both trace the
same population throughout this seed, consistent with prior passes'
finding that seed 500 shows no material/v1 divergence). v2's anchor
differs slightly but stays in the same low range (0.02–0.03) at every
radius — no anchor produces a qualitatively different conclusion ("no
turn") for this seed. **No anchor-sensitivity issue for seed 500.**

### Seed 501

v1==v2 exact member-set agreement at only 10/77 frames (v2's coalescing/
probabilistic-branch machinery produces a structurally different
membership trajectory from v1 even when both ultimately reach similar
conclusions — exact-set agreement is a strict, not a necessary,
condition). At the final frame (t=76):

| radius | v1 anchor | v2 anchor | material anchor |
|---|---|---|---|
| 1.5 | 0.971 | 0.868 | 0.971 |
| 2.0 | 0.971 | 0.878 | 0.971 |
| 2.5 | 0.929 | 0.896 | 0.929 |
| 3.0 | 0.933 | 0.903 | 0.933 |
| 3.5 | 0.918 | 0.893 | 0.918 |
| 4.0 | 0.860 | 0.872 | 0.860 |
| 5.0 | 0.810 | 0.855 | 0.810 |

**v1 and material anchors agree exactly at every radius** (same
population, as established). **v2's anchor, computed EXACTLY for the
first time (not proxied by v1), gives a somewhat lower but still
uniformly HIGH reading at every radius** (0.855–0.903 vs. v1/material's
0.810–0.971) — both trackers agree the target substantially turned, at
every tested radius. **This reconfirms, with the exact v2 anchor (not a
v1 proxy), Step 2's original finding that seed 501's field-direction
readout is robust to anchor choice** — the conclusion ("real turn") does
not change based on which of the three anchors or which radius is used.

### Seed 502

v1==v2 exact member-set agreement at 62/77 frames (much closer agreement
than seed 501's 10/77 — the two trackers converge on the same wrong
population here). At the final frame (t=76):

| radius | v1 anchor | v2 anchor | material anchor |
|---|---|---|---|
| 1.5 | 0.800 | 0.800 | 0.062 |
| 2.0 | 0.769 | 0.769 | 0.073 |
| 2.5 | 0.667 | 0.667 | 0.071 |
| 3.0 | 0.412 | 0.412 | 0.070 |
| 3.5 | 0.303 | 0.303 | 0.068 |
| 4.0 | 0.258 | 0.258 | 0.100 |
| 5.0 | 0.191 | 0.191 | 0.127 |

**v1 and v2 anchors are numerically IDENTICAL at every single radius** —
not merely similar, exactly equal — because the two trackers have
converged on the same (materially wrong) population by this frame. **The
material anchor is dramatically and consistently lower at every radius**
(0.06–0.13 vs. 0.19–0.80). **This is the strongest possible reconfirmation
of Step 2's original finding, now with the EXACT v2 anchor rather than
a v1 proxy**: the field-direction readout's large anchor-choice gap for
seed 502 does NOT disappear, weaken, or depend on which of v1/v2 is used
as the (wrong) comparator — both agree with each other and both disagree
sharply with the material trace, at every tested radius. **Anchor
sensitivity for seed 502: fully survives exact v2 anchoring.**

### Seed 503

v1==v2 exact member-set agreement at only 19/82 frames. At the final
frame (t=81):

| radius | v1 anchor | v2 anchor | material anchor |
|---|---|---|---|
| 1.5 | 0.958 | 0.024 | 0.000 |
| 2.0 | 0.931 | 0.022 | 0.500 |
| 2.5 | 0.931 | 0.042 | 0.417 |
| 3.0 | 0.879 | 0.058 | 0.278 |
| 3.5 | 0.879 | 0.055 | 0.273 |
| 4.0 | 0.857 | 0.067 | 0.222 |
| 5.0 | 0.839 | 0.129 | 0.188 |

**This is a materially NEW and sharper finding than Step 2's original
v1-as-proxy comparison.** v1's anchor gives the familiar HIGH reading
(0.84–0.96, matching the historically-reported dramatic turn) — but
**v2's own, EXACTLY computed anchor gives a dramatically LOW reading at
every radius (0.02–0.13), much closer to the material trace's own low-end
readings than to v1's.** The material anchor itself is radius-UNSTABLE
here (0.0 at r=1.5 jumping to 0.5 at r=2.0, then declining to 0.19 by
r=5.0 — small-member-count sensitivity at the smallest radius, since the
followed daughter has shrunk considerably by t=81), but never approaches
v1's 0.84–0.96 range at any tested radius.

**v1 and v2 sharply DISAGREE with each other for seed 503** (unlike seed
502, where they agreed exactly) — v2 does NOT corroborate v1's high
reading at all; if anything it sides with the low end the material trace
also reports. **This strengthens, rather than merely reconfirms, the
prior finding**: it is not just that the material trace disagrees with
v1 — an independent, differently-constructed probabilistic tracker (v2)
ALSO disagrees with v1's high reading, landing near the material trace's
low end instead. Three of three non-v1 signals (v2, material, and — per
Step 1 — the original `field_direction` computed at a v1-proxied anchor
already) converge on "the large reported turn is not corroborated once
you stop anchoring on v1," now confirmed with v2's own exact centroid
rather than a v1 substitute.

### Seed 504

v1==v2 exact member-set agreement at 90/94 frames (the cleanest agreement
of all 5 seeds). At the final frame (t=93):

| radius | v1 anchor | v2 anchor | material anchor |
|---|---|---|---|
| 1.5 | 0.000 | 0.875 | 0.000 |
| 2.0 | 0.000 | 0.845 | 0.000 |
| 2.5 | 0.000 | 0.755 | 0.000 |
| 3.0 | 0.000 | 0.747 | 0.000 |
| 3.5 | 0.033 | 0.747 | 0.033 |
| 4.0 | 0.045 | 0.740 | 0.045 |
| 5.0 | 0.053 | 0.721 | 0.053 |

**v1 and material anchors again agree exactly** (same population, "no
turn" — consistent with prior passes). **v2's anchor is a striking,
consistent outlier here: HIGH (0.72–0.88) at every radius**, despite
90/94 frames of exact v1==v2 MEMBERSHIP agreement — meaning v2's high
reading is not about a different tracked population, but about v2's
CENTROID landing in a different, more-aligned neighborhood than v1's
centroid at this specific final frame, even when the two trackers'
membership sets mostly coincide across the episode. This is a new
finding this pass surfaces (Step 2 did not examine seed 504's
field-direction anchor sensitivity in detail; it was treated as the
"clean reference" case). **It does not overturn seed 504's "no turn"
characterization** — v1/material's own membership-based readout, and
seed 504's own recorded alignment fraction in `online_control_611__seed504.json`
(0.11→0.03 across the real control window), both firmly support "no
turn"; but it does mean seed 504 is NOT anchor-insensitive either, once
v2 is computed exactly rather than assumed clean by default. Flagged as a
genuine, disclosed complication, not resolved further in this pass — see
`NEXT_CONTROLLER_SPEC_INPUTS.md`.

## Cross-seed anchor-sensitivity summary

| seed | v1 vs. material | v2 vs. (v1/material) | conclusion changes by anchor? |
|---|---|---|---|
| 500 | identical at every radius | v2 close to v1/material (low, all anchors) | No — all three agree "no turn" |
| 501 | identical at every radius | v2 somewhat lower but still uniformly HIGH at every radius | No — all three agree "real turn" |
| 502 | v1/v2 identical to each other; material sharply lower at every radius | v2 = v1 exactly | No — reconfirms the original divergence with the exact anchor |
| 503 | v1 high, material radius-unstable but always far below v1 | **v2 sharply LOW, siding with material against v1** | **Sharpened**: v2 independently contradicts v1's high reading |
| 504 | identical at every radius (low) | **v2 sharply HIGH despite membership agreement** | New complication surfaced; "no turn" conclusion itself unchanged but anchor-insensitivity assumption for this seed is not supported |

**Overall**: Step 2's original anchor-sensitivity conclusion (robust for
501, not for 502/503) **survives exact v2 replay for seeds 501 and 502**,
and for 503 the picture **sharpens** (v2 now independently, not just
via material trace, contradicts v1). It **newly emerges** for 504, a seed
previously treated as anchor-clean. No seed's headline physical-turn
conclusion (500/504 "no turn", 501 "real turn", 502/503 "not the
qualification-time target that turns") is reversed by this pass's exact
v2 replay — but the ROBUSTNESS of those conclusions to anchor choice is
now established (not merely assumed) on a seed-by-seed basis, including
one new disclosed complication (504) that was not previously examined.

## Interpretation (finalized once all 5 seeds are in)

Step 2's original finding (`rescoring_reassessment.md`) was that
field-direction, recomputed at the material trace's own centroid instead
of v1's, is NOT robust to anchor choice for seeds 502/503 (large,
radius-stable gap) but IS robust for seed 501 (anchors agree) — using
v1's centroid as a proxy for v2's own centroid throughout, a disclosed
simplification. This section states, once the full sweep is complete,
whether that conclusion survives exact v2 anchoring, weakens, disappears,
or differs by seed — per spec's explicit requirement not to claim
ID-independence without noting the spatial anchor is itself
tracker-derived.
