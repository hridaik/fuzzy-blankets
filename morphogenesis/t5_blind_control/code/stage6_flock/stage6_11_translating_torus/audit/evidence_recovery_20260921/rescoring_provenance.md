# Rescoring provenance — what "ID-independent rescoring" actually was

**Source:** `stage6_11_translating_torus/audit/branch_adjudication_611.py`
(script), consuming `audit/trigger_states_611.json` (extracted, not
re-simulated, from `data/viz_bundle_611__seed{n}.json` and
`data/online_control_611__seed{n}.json`). Narrative: `FIVE_SEED_CAUSAL_ADJUDICATION.md`.
This is the **only** script in the repository that produces a labelled
"controllable / not demonstrated controllable" verdict per seed using a
readout that does not depend on bird-ID membership; it is what the current
handoff's "later audit work reported that seeds 501 and 502 did not survive
an ID-independent rescoring" refers to. No other script or notebook in the
repository computes an equivalent quantity for these five seeds.

**There is exactly one rescoring implementation**, not several — a single
script (`branch_adjudication_611.py`) computing four parallel readouts per
branch, of which one (`field_direction`) is explicitly the "ID-independent"
one and one (`original_material`) is ID-based-but-fixed-to-origin. The two
"v1 MAP" / "v2 MAP" readouts are ordinary bird-ID-membership readouts,
included for comparison, not themselves called ID-independent.

## What object was scored at each time point?

Four different objects, all computed at end-of-control (`t0+24`) and
end-of-release (`t0+48`) for every branch (`branch_adjudication_611.py:280-297`):

1. **`v1_end_control` / `v1_end_release`** — `frac_at_target(z, ids, h_star)`
   where `ids` = the ORIGINAL `LineageTracker611`'s own MAP interior at that
   instant, from a **freshly-instantiated tracker replayed on that branch's
   own trajectory**, seeded at the branch's t0 interior
   (`track_trajectory`, `branch_adjudication_611.py:128-161`). This is a
   bird-ID membership readout, using v1's own belief.
2. **`v2_end_control` / `v2_end_release`** — identical, but using
   `LineageTrackerV2` (`lineage_v2_611.py`) instead. Also a bird-ID
   membership readout, using v2's belief as a *comparator*, not as ground
   truth (the handoff's "v2 is not a trusted final identity model, only an
   audit comparator" is respected exactly here — v2's own membership output
   is one readout among four, never given deciding authority alone).
3. **`original_material_end_control` / `_end_release`** — `frac_at_target`
   using `interior0`, the **exact bird-ID set recorded as the interior at
   the moment the trigger snapshot was taken (t0)**, held fixed for the
   entire branch, regardless of anything either tracker later believes. This
   is "does the SPECIFIC set of birds present when the target was set end
   up facing the target heading" — a materially strict, ID-based readout
   that does NOT allow gradual turnover, by construction (see caveat below).
4. **`field_direction_end_control` / `_end_release`** — the actual
   ID-independent readout, `field_direction_readout`
   (`branch_adjudication_611.py:164-178`):
   ```
   c = centroid(r[members], L)              # members = that branch's own
                                              # v2 end-of-window membership
                                              # (falls back to interior0 if
                                              # v2's tracker had fully died)
   D = |torus_delta(r, c, L)|                # wrapped distance, geometry_611
   near = D <= radius   (radius = 3.0)
   readout = mean(z[near] == target_heading)
   ```
   This scores **every bird within a fixed radius of a centroid**, without
   regard to whether any individual nearby bird is a member of any tracked
   set. It is "ID-independent" specifically in the sense that once the
   centroid is fixed, membership plays no further role in who gets counted.

## How was the "target at evaluation time" chosen?

The **centroid location** (not a membership set) is the object doing the
"targeting." That centroid is derived from `tr["end_control"]["v2"]` /
`tr["end_release"]["v2"]` — i.e. **v2's own current dominant lineage
membership at that exact evaluation instant**, not the original t0 cohort,
and not a manually-drawn region. **Membership is therefore NOT fixed to the
original cohort for the field-direction readout** (it is fixed for
`original_material`, a different readout). A geometric/spatial region *is*
used (radius 3.0 around that centroid) but its center moves with v2's own
belief about where the collective currently is.

## Caveat this audit flags explicitly (not resolved by the original script)

Because the field-direction anchor's **location** depends on v2's own
membership output, and v2 (per `lineage_v2_611.py`'s docstring) allows a
candidate to remain viable via transport-consistency alone even at low
material overlap (`RETENTION_MIN_SOFT=0.10`), there is a theoretical channel
by which a v2 drift toward an already-aligned sub-population could bias
*where* the field-direction radius is centered, even though the readout
itself, once centered, is genuinely ID-independent (it does not care which
specific birds are inside the radius). `FIVE_SEED_CAUSAL_ADJUDICATION.md`
itself relies on `original_material` (a readout with NO such dependency,
since it is fixed to t0's exact IDs) agreeing with `field_direction` before
calling a rise "corroborated" (item 11's controllability rule requires
agreement with AT LEAST one of the two) — which partially, but not fully,
mitigates this channel, since a seed can in principle pass on
`field_direction` alone. In this study's actual results (seeds 501, 502),
BOTH `original_material` and `field_direction` failed to corroborate the v1
rise, so the caveat does not change either seed's verdict here, but it
should be understood as a residual, not fully independent-of-tracker,
property of the "ID-independent" name.

## Was a tracker other than v1 used?

Yes — v2 (`LineageTrackerV2`), for two purposes: (a) its own membership is
reported as a second, independent MAP readout, and (b) it supplies the
centroid anchor for `field_direction`. v1 is separately, independently
re-run on every branch's own trajectory (not reused from the original
production run — see the CRN caveat below).

## Was the target reconstructed manually?

No. Everything is computed by the script from recorded/replayed state;
there is no manually-specified target region or manually-labelled outcome
anywhere in `branch_adjudication_611.py`.

## Wrapped or unwrapped coordinates?

Wrapped throughout. `field_direction_readout` uses `geometry_611.torus_delta`
(minimum-image convention) for both the centroid computation
(`identity_69.centroid`, itself torus-aware) and the radius query. No
Euclidean (non-periodic) distance is used anywhere in this scoring path.

## Were persistent bird IDs available? Were gradual membership changes allowed?

Yes to both, but differently per readout:
- `v1`/`v2` readouts: yes, IDs persist and are tracked frame-to-frame by
  each tracker's own update rule (gradual turnover is exactly what each
  tracker's branching logic is meant to permit or refuse).
- `original_material`: IDs persist but are **frozen at t0** — this readout
  by construction does NOT allow any turnover; it asks "did literally the
  originally-present birds end up at target," which is a strict continuity
  test, not a soft one.
- `field_direction`: does not track IDs at all once the centroid is fixed
  for that instant; there is no "membership" to allow or disallow turnover
  in.

## Exact success criterion / time window (item 11, controllability verdict)

`FIVE_SEED_CAUSAL_ADJUDICATION.md`, "Controllability (item 11)": a seed is
called **controllable under tested budget** only if a REFERENCE branch
(`exact_direct_interface_repaired` or `beam_search_benchmark` — i.e. one of
the two *repaired*, evidence-gated, non-privileged-oracle-leaking branches,
never `original_reproduced` or any "old" branch) shows a
**release-persistent rise** (value at `t0+48` above `frac_at_target_start`,
the value at exactly t0) **corroborated by at least `original_material` OR
`field_direction`** at end-of-release. A v1-only rise is explicitly
insufficient. Evaluation window: `t0` (trigger) through `t0+24`
(end-of-control) through `t0+48` (end-of-release); `T_CONTROL=24,
T_RELEASE=24` (`branch_adjudication_611.py:74-75`).

## Was the requested target direction used in identity selection?

The requested `target_heading` (`h_star`) enters `field_direction_readout`
only as the label being measured (`z[near] == target_heading`), never as a
selection criterion for which birds are near the centroid or which
candidate becomes v2's dominant membership. `LineageTrackerV2`'s own
branch-scoring (`lineage_v2_611.py`, `DICE_WEIGHT, RF_WEIGHT` combination,
unchanged from v1's) contains no term referencing `target_heading` or
`h_star` at all — confirmed by reading `lineage_v2_611.py` in full for this
audit; grep for `h_star`/`target` inside that module's scoring functions
returns no hits outside `select_actuators_v2`/`authority_set` (a different
module, `authority_v2_611.py`, that consumes `h_star` for actuator
authority estimation, not for lineage/membership selection). **So: no, the
requested direction is not used in the identity-selection step that
produces v2's membership**, and by extension not in the centroid the
field-direction readout anchors on.

## Could a group already heading toward the target direction be preferentially selected?

Not through an explicit mechanism (see above — no `h_star` term in
`lineage_v2_611.py`'s scoring). However, this audit's separate,
frame-by-frame reconstruction (`LINEAGE_FORENSICS_6_11.md` §1.1,
independently reconfirmed by this pass's `data/material_retention_seed*.csv`
`displayed_vs_branch_internal_disagree` column — see `audit_findings.md`
§6) shows that v1's own cross-branch MAP-argmax mechanism CAN and DOES,
mechanistically, favor whichever independently-live branch happens to have
an undiluted, well-scoring continuation that step — and a branch whose
recent trajectory already correlates with the eventual target direction
would tend to have smoother, better-scoring continuations for reasons
unrelated to any explicit target-direction term. This is a plausible,
partially-evidenced (not proven) indirect channel for exactly the kind of
bias the new t=46→47 observation motivated checking — but the evidence
recovered in this pass places it in v1's own branch-argmax mechanism (fully
documented, seeds 500/501/502/503, pre-existing finding), not as a new
defect specific to `field_direction_readout` or seed 500's t=46→47
transition specifically, which (per `seed_500.md`) shows no discontinuity
of any kind at that point.

## What assumptions made the scoring "ID-independent"?

1. That a fixed-radius spatial neighborhood around a (tracker-derived)
   centroid is a reasonable stand-in for "the collective" when membership
   itself is in dispute — i.e. it trades a possibly-wrong membership set for
   a possibly-wrong-but-differently-wrong spatial region.
2. That the centroid itself, even though derived from a tracker (v2), is a
   sufficiently coarse/soft summary that errors in v2's precise membership
   don't propagate strongly into *where* the region is centered — this is
   an assumption, not something the script verifies quantitatively (no
   sensitivity check of `field_direction` to the specific centroid source is
   present in this pass's artifacts).
3. That radius=3.0 (in the same spatial units as the torus, `L=24`) is a
   reasonable neighborhood scale — this is a fixed constant in
   `branch_adjudication_611.py:164`, not calibrated or swept in this pass.
