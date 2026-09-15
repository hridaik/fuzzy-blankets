# Thingness/Clump Gate Audit — Stage 6.11B (item 3)

Additive, read-only against the existing Stage 6.11 record; no existing
threshold moved. Script: `audit/thingness_gate_audit_611.py`. Raw output:
`audit/thingness_gate_audit_611.json`. Reuses `audit/lineage_forensics_611__seed{n}__hypotheses.csv`
(Part D of the prior pass) for per-step C/D/Q/n_components/size_frac rather
than recomputing them, plus a freshly-computed `f_main` (not present in that
CSV) from `viz_bundle_611__seed{n}.json`.

## 1. Calibration (uncontrolled development data only)

`thingness_611.calibrate_thresholds` (imported, not reimplemented) on 1,350
candidate records drawn from 10 uncontrolled train-split episodes (largest 3
candidates every 4th step), 25th-percentile rule, matching the module's own
documented convention:

| threshold | value |
|---|---|
| C_min | 0.815 |
| D_min | 1.000 |
| Q_min | 1.000 |
| G_min | 0.0 (no dev record ever had G — see §3) |
| L_max | ∞ (no dev record ever had L — see §3) |
| size_frac_range | [0.03, 0.55] |
| dwell_min | 30 |

## 2. Applying the UNCHANGED gate, first, as instructed

Sanity check on the calibration set itself (by construction, ≈75% of
records should clear each 25th-percentile threshold on `C`, and this holds:
74.9%/97.5%/93.5% for C/D/Q respectively) — **except `one_dominant_component`
(`n_components == 1`), which only 0.15% of UNCONTROLLED DEVELOPMENT
candidates ever satisfy** (median n_components = 13, 90th percentile = 24,
even for ordinary, non-adversarial candidates the same detector produces
every day). This single hard check is, as calibrated and as coded, nearly
unsatisfiable — not a control-regime pathology, a base rate of the detector
itself.

Applying the full gate (all hard checks, `G`/`L` reported `None` and
therefore not counted against `passes` per the module's own `passes_gate`
semantics — see §3) to every step of all five online seeds' actual MAP
interior:

| seed | qualified at t= | fraction of ALL steps passing full gate | gate passes AT the qualification moment itself? |
|---|---|---|---|
| 500 | 61 | 0.0% | **No** |
| 501 | 30 | 1.3% | **No** |
| 502 | 30 | 0.0% | **No** |
| 503 | 35 | 0.0% | **No** |
| 504 | 47 | 4.3% | **No** |

**If the intended thingness gate had actually been connected to the online
qualification trigger (`run_online_control_611.py`, confirmed in
`METHODS_AUDIT_6_11.md`/`LINEAGE_FORENSICS_6_11.md` §5 to never invoke it),
none of the five reported control episodes would have qualified for control
at the moment they actually did — and, on this evidence, essentially never
would have qualified at any point in the uncontrolled phase either** (0.0–4.3%
of all steps pass, and it is `n_components==1` doing almost all of the
rejecting).

## 3. Root cause: a spatial-scale mismatch, not a genuine fragmentation finding

This is the headline finding of this section, and it revises how to read
`LINEAGE_FORENSICS_6_11.md`'s own n_components/D numbers (documented there as
"real, not an outlier" — see the caveat in §3.1 below).

`thingness_611.geometry_features` computes `n_components` and `D` (local
exterior contrast) using `periphery_radius = geometry_611.local_scale(r, L)`
— **2.5× the median NEAREST-NEIGHBOUR spacing across all 400 birds**. On the
primary regime's actual density this evaluates to **≈0.19–0.32 spatial
units**. The candidate DETECTOR that produces the very candidates being
graded (`detect_69.propose`) defines "close enough to be one community" via
a completely different, much larger scale: its affinity kernel cutoff is
**3.3 units — roughly 10–17× larger**.

Direct measurement, same candidate, same snapshot (train episode 0, t=50,
74-member candidate):

| connectivity radius | n_components | periphery set size (non-members within radius of any member) |
|---|---|---|
| `local_scale` (0.32, what the code actually uses) | (not 1 — fragmented) | **0** |
| detector's own kernel cutoff (3.3) | **1** | 66 |

**At the radius the gate actually uses, the candidate's periphery is
EMPTY — not sparse, empty.** `geometry_611.local_exterior_contrast` returns
its documented trivial fallback (`D = 1.0`) whenever no exterior bird is
found within `periphery_radius` of any member (`geometry_611.py`, "if
len(periphery) == 0: return 1.0"). **This means `D` has almost certainly
never functioned as a genuine periphery-blending measurement anywhere in
Stage 6.11 — not in the online pipeline (which never called `thingness_611`
at all, per the Methods Audit) and not in `LineageTracker611`'s own
`_grow_classification` individuation-loss check (`lineage_611.py:121-134`),
which calls this exact function with this exact radius.** Aggregated over
the 10-episode calibration set, `D` cleared its threshold 97.5% of the time
— consistent with "D is almost always exactly 1.0 because the periphery
search almost always comes back empty," not with "the periphery is
genuinely, almost always, behaviourally distinct."

Recomputing connectivity at the detector's OWN 3.3-unit scale instead of
`local_scale` (diagnostic only, not adopted — see §4): the SAME candidates
that showed 13–24 fragmented "components" under the gate's own radius are
**100% single-connected-component** under the radius the detector itself
used to decide they belonged together. The torus-aware minimum-image
distance and union-find code (`geometry_611.connected_components`) is
correct and was verified torus-aware directly (candidates spanning the
periodic boundary are still merged correctly under either radius) — the
defect is entirely in which radius value is handed to it, not in the
distance/connectivity algorithm itself.

### 3.1 Correction to `LINEAGE_FORENSICS_6_11.md`

That document (prior pass) reported n_components=11–24 for the tracked
interior at essentially every step, and separately reported `D` at or near
1.0 almost everywhere, reading the second fact as evidence the fragmentation
was "a genuine spatial-shape property... not a symptom of losing definition
against the background." **That reading should now be treated as
unsupported, not confirmed or refuted**: `D`'s near-ubiquitous 1.0 value is,
on this pass's evidence, very likely the trivial "no periphery found" default
rather than a real measurement of behavioural blending, because the search
radius that produces both the fragmentation count AND the `D` value is the
same undersized `local_scale`. This does not overturn the fragmentation
finding itself (it is real, under the gate's own coded radius, and the gate
was never invoked online regardless) — it removes `D` as independent
corroborating evidence that the fragmentation was benign. `LINEAGE_FORENSICS_6_11.md`
is left unedited per the freeze instruction; this is the correction going
forward.

## 4. Spatial integrity, `f_main`, and a proposed (not adopted) future threshold

`f_main` (largest-connected-component fraction of the tracked interior,
new in this pass, `lineage_v2_611.component_sizes`) computed at the SAME
`local_scale` radius the existing gate uses, for comparability:

| seed | qualification-moment f_main | mean f_main (whole episode) |
|---|---|---|
| 500 | 0.576 | 0.589 |
| 501 | 0.400 | 0.578 |
| 502 | 0.524 | 0.489 |
| 503 | 0.619 | 0.506 |
| 504 | 0.857 | 0.699 |

So the largest single fragment is typically 40–86% of the tracked interior
at `local_scale` radius, not a vanishing sliver — the interior is fragmented
(consistent with §1's near-zero `one_dominant_component` pass rate: 13–24
pieces is not compatible with `f_main` this high unless most of the OTHER
pieces are small) but not atomized. This should still be read with §3's
caveat: at the detector's own connectivity scale the same object is 100%
single-component, so `f_main` at `local_scale` understates spatial coherence
by construction, not because the tracked collective is loosely organized.

**Per the task brief's explicit instruction, no new threshold is adopted
here.** What is reported instead, as a distinct, clearly-labelled proposal
for a *future* pass:

> **Proposed (not adopted): recalibrate the spatial-integrity check's
> connectivity radius to the SAME scale the candidate detector itself uses to
> decide two birds are "close enough" to co-occur in a community (currently
> `detect_69.KERNEL_CUTOFF = 3.3`), rather than `geometry_611.local_scale`
> (designed for a different purpose — the individuation-contrast periphery
> band around a candidate's own boundary, at a much finer grain). This would
> make `n_components == 1` and a non-trivial `D` measurement both achievable
> for ordinary candidates, without weakening what "one dominant component"
> is actually checking for.**

This is a proposal, not a threshold change: it has not been calibrated,
tested against control outcome, or applied to any decision in this pass.

## 5. G and L

Confirmed again (independently of `METHODS_AUDIT_6_11.md`'s source-level
finding): across all 1,350 development records and all five online seeds'
per-step records, `G` and `L` are never available — `thingness_611`'s own
`passes_gate` correctly treats a missing `G`/`L` as "not yet evaluated,"
not as a failure, so this does not by itself explain the near-total
qualification failures above (those come almost entirely from
`one_dominant_component`, per §2). Computing `G`/`L` at scale (via
`predictive_boundary_611.construct_boundary`/`certify`) for every step of
every seed was out of budget for this pass (each call is a boundary
construction/bootstrap, not a cheap geometry lookup) and is deferred.

## 6. Summary for the confirmed-vs-possible ledger

| claim | status |
|---|---|
| The thingness gate, applied unchanged, would have qualified any of the 5 online seeds' actual control episode | **REFUTED** — 0/5, both at the qualification moment and over the whole episode (0.0–4.3% of all steps) |
| `n_components == 1` is a reasonable bar given how the detector actually behaves | **REFUTED as currently scaled** — 0.15% of ordinary uncontrolled candidates ever clear it |
| The fragmentation found in `LINEAGE_FORENSICS_6_11.md` reflects genuinely incoherent spatial organization | **UNRESOLVED, likely overstated** — real under the gate's own coded radius, but that radius is ~10-17x smaller than the scale the detector itself uses to define "together," and switching to the detector's own scale makes the same candidates uniformly single-component |
| `D` (local exterior contrast) independently corroborated that fragmentation was benign | **RETRACTED** — `D`'s ubiquitous 1.0 is very likely the "no periphery found" trivial default at this radius, not a measurement |
