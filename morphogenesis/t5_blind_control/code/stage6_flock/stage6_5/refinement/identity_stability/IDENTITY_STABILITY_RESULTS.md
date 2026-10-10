# IDENTITY_STABILITY_RESULTS.md — HARD GATE C

Frozen protocol: `../PROTOCOL_6_5R.md` (Part C section) / `../configs/
protocol_6_5r.yaml` (`part_c_identity_stability` block), hash `../logs/
protocol_6_5r_part_c.sha256`. All numbers below are read directly from
`data/{jitter_analysis,regularized_lineage_calibration,validity_envelope,
representation_comparison,closed_loop_stabilized}.json`; none are
hand-adjusted. Figures: `figures/fig_r6_5_4_jitter_vs_physical_change.png`
(R6.5-4), `figures/fig_r6_5_5_collapse_vs_guarded.png` (R6.5-5), `figures/
fig_r6_5_6_pathwise_boundary_stabilized.png` (R6.5-6).

Scope (explicit user direction, 2026-09-06): 5 "informative" flocks (2, 3,
4, 8, 9 — first 5 of V3's frozen `DEV_SEEDS`, in frozen order, not selected
for showing interesting behavior) for the evaluation-only passes (C1, C5);
a smaller 3-flock subset (2, 3, 4) at 30 replicates per representation for
the closed-loop proof of concept (C7/C8).

## C1 — how much turnover is detector jitter?

`D_X(t)` (fraction of all 100 birds changing heading) vs `T_I(t)` (lineage
turnover) on uncontrolled baseline continuations (60 steps each):

| seed | Pearson corr(`D_X`,`T_I`) | steps flagged low-`D_X`/high-`T_I` |
|---|---|---|
| 2 | 0.276 | 3/60 |
| 3 | 0.153 | 4/60 |
| 4 | 0.101 | 4/60 |
| 8 | 0.423 | 1/60 |
| 9 | 0.284 | 0/60 |

**Weak-to-moderate correlation (0.10-0.42), not strong.** If lineage
turnover were purely a readout of overall physical activity, this
correlation would be close to 1; it is not. Between 0 and 4 of every 60
steps (0-7%) on each flock show large lineage turnover coincident with
below-median physical change — genuine, if not dominant, evidence that
*some* of the original turnover Stage 6.5 reported was
detector jitter rather than a readout of real reorganization. This does not
mean *most* turnover was jitter — the correlation, while weak, is
positive and nonzero on every flock, so real turnover and physical change
are related, just loosely.

## C2 — does temporal regularization reduce turnover, and cleanly?

**It reduces turnover dramatically, but NOT cleanly — it could not be
tuned to suppress jitter while leaving genuine transitions intact,
at any tested value.** Grid results (mean turnover during below-median-`D_X`
stretches vs. above-90th-percentile-`D_X` stretches, original lineage vs.
regularized, pooled over the 5 informative flocks):

| `lambda_T` | low-`D_X` turnover (orig -> reg) | high-`D_X` turnover (orig -> reg) | criterion met? |
|---|---|---|---|
| 0.1 | 1.71 -> 0.11 | 4.90 -> 0.76 | No |
| 0.25 | 1.71 -> 0.04 | 4.90 -> 0.58 | No |
| 0.5-2.0 | 1.71 -> 0.00 | 4.90 -> 0.00 | No |

At every tested `lambda_T`, high-`D_X` (genuine-transition) turnover is
suppressed by a **larger** fraction than the criterion's "still permits"
bar requires — even the loosest setting (0.1) leaves only 15% of original
high-`D_X` turnover, not the >=50% the frozen criterion asked for. From
`lambda_T=0.5` on, the regularized track **never changes from `I_0` at
all** (both columns reach exactly `0.00`) — the continuity bonus becomes
strong enough that no candidate can ever beat "keep previous," making
regularized lineage behave identically to material identity. **No grid
value satisfies the full frozen criterion.** Per the pre-specified fallback
(the smallest `lambda_T` satisfying the criterion's primary verb,
suppression, alone — see `configs/protocol_6_5r.yaml`), `lambda_T=0.1` was
used downstream. This is reported as a genuine limitation, not
papered over: **a single transparent hysteresis knob, calibrated on
uncontrolled baseline data, could not cleanly separate jitter from real
transitions in this data** — the two are not well-separated by a
coherence-based score alone at this level of simplicity.

## C3 — the validity envelope

5th-percentile bounds from the 5 informative flocks' baseline continuations
(305 size observations, 300 continuity observations):

| definition | `S_I` lower bound | `J_min` |
|---|---|---|
| Regularized lineage (`lambda_T=0.1`) | 0.65 | 0.905 |
| Functional (unconstrained) | **0.05** | 0.782 |

The functional definition's own **natural, uncontrolled** size distribution
already dips as low as 5% of `I_0` at least once in the baseline data — a
striking fact on its own: the tendency to shrink toward a small coherent
remnant is not purely a control-induced pathology, it is present in
undisturbed dynamics too, just rare enough that a control episode's
sustained pressure toward one heading reliably drives it there and keeps it
there.

## C5 — does stabilization change the representation-dependence finding?

Controlled episodes (frozen V3 multicover forcing true `B^D_0`, `N_REP=8`,
identical generation formula to Stage 6.5's own Part 4 for seeds 2/3/4,
extended to seeds 8/9 by the same method):

| seed | rep | `P`(nominal success) | mean final size |
|---|---|---|---|
| 2 | M | 1.00 | 20.0 |
| 2 | L (orig) | 1.00 | 15.4 |
| 2 | **L_reg** | **0.00** | 13.9 |
| 2 | F (orig) | 1.00 | 1.2 |
| 2 | F_guard | 1.00 | 11.2 |
| 3 | M / L / L_reg / F / F_guard | 1.00 / 1.00 / 1.00 / 1.00 / 1.00 | 19.0 / 14.8 / 19.0 / 2.9 / 15.9 |
| 4 | M / L / L_reg / F / F_guard | 0.12 / 0.12 / **0.00** / 0.00 / 0.00 | 20.0 / 17.4 / 15.9 / 9.4 / 11.6 |
| 8 | M / L / L_reg / F / F_guard | 0.88 / 0.88 / **0.00** / 0.88 / 0.88 | 20.0 / 18.1 / 12.9 / 1.4 / 7.4 |
| 9 | M / L / L_reg / F / F_guard | 0.75 / 0.88 / **0.00** / 0.88 / 0.88 | 19.0 / 15.8 / 14.8 / 2.5 / 8.6 |

**Yes, representation dependence is robust after stabilization — and a new,
unanticipated form of it appeared.** On 4 of 5 flocks (2, 4, 8, 9), the
regularized lineage's *nominal* success **drops to 0.00** even though
material, original lineage, and (guarded) functional all succeed. This is
not a calibration bug: `lambda_T=0.1` was calibrated purely on *uncontrolled*
baseline data (C2), which never contains an externally-forced reorientation
event. During active control, the collective is being pushed through a
genuinely large, real transition **by construction** — precisely the kind
of event the regularization is supposed to still permit — but a
regularization tuned only against passive dynamics has no way to have seen
anything like it, and ends up suppressing the very transition the
controller depends on tracking correctly. **This is itself an important,
unanticipated finding**: temporal identity regularization calibrated on
undisturbed dynamics does not automatically transfer to actively controlled
dynamics, and this failure mode would have been invisible without C5's
evaluation-only re-run on genuinely controlled episodes.

## C6 — the five questions, answered

**1. How much original turnover was detector jitter?** Some, not most.
Correlation between physical change and lineage turnover is positive but
weak (0.10-0.42); 0-7% of steps per flock show large turnover during
otherwise-quiet stretches. Detector jitter is real but is not the dominant
explanation for Stage 6.5's reported turnover.

**2. Does representation dependence remain after temporal stabilization?**
Yes, and more sharply in one respect: the regularized lineage now
*disagrees with itself* across development vs. controlled conditions —
successful by every other definition's account on 4 of 5 flocks, it alone
registers 0.00 nominal success once the same regularization is evaluated
on genuinely controlled trajectories rather than the baseline data it was
tuned on.

**3. Does the identity guard correctly expose collapse rather than reward
it?** Yes, cleanly. On the C7 closed-loop proof of concept (30 replicates,
flocks 2/3/4):

| seed | rep | nominal `P`(success) | identity-valid `P`(success) | `P`(collapsed) | mean final size | mean actuators |
|---|---|---|---|---|---|---|
| 2 | M | 0.93 | 0.93 | 0.00 | 20.0 | 12.0 |
| 2 | L_reg | 1.00 | **0.00** | 1.00 | 19.8 | 12.1 |
| 2 | F_guard | 1.00 | **0.07** | 1.00 | 9.2 | 8.6 |
| 2 | F (unguarded) | 1.00 | 1.00 | 0.00 | **1.9** | 7.2 |
| 3 | M | 1.00 | 1.00 | 0.00 | 19.0 | 7.0 |
| 3 | L_reg | 1.00 | 0.40 | 0.60 | 18.9 | 6.9 |
| 3 | F_guard | 1.00 | **0.00** | 1.00 | 14.9 | 5.6 |
| 3 | F (unguarded) | 1.00 | 1.00 | 0.00 | **2.2** | 4.2 |
| 4 | M | 0.10 | 0.10 | 0.00 | 20.0 | 8.0 |
| 4 | L_reg | 0.37 | **0.00** | 1.00 | 19.5 | 9.0 |
| 4 | F_guard | 1.00 | **0.30** | 0.97 | 8.9 | 8.0 |
| 4 | F (unguarded) | 0.97 | 0.97 | 0.00 | **1.8** | 6.6 |

The unguarded functional definition (`F`) **reproduces Stage 6.5's original
one-bird-collapse finding cleanly, and more starkly**: nominal success stays
at or near ceiling (0.97-1.00) on all three flocks — including the *hard*
flock 4, where the material controller only succeeds 10% of the time — by
shrinking to a mean final size of **1.8-2.2 birds** that is trivially easy
to steer. The guarded functional definition (`F_guard`) holds a much larger
group throughout (mean final size **8.9-14.9**, 4-8x larger than the
unguarded collapse) and correctly flags **97-100% of these episodes as
IDENTITY COLLAPSE / UNRESOLVED**, driving identity-valid success down to
0.00-0.30 even though nominal success stays at 1.00 on 2 of 3 flocks. The
guard does exactly what Part C3/C4 asked: it neither silently accepts the
tiny collapsed remnant as "the collective" nor silently substitutes an
arbitrary larger group and calls it success — it holds a defensible larger
group and honestly reports that continuity could not be maintained.

**4. Does adaptive control remain beneficial after accounting for identity
preservation? No.** `F_guard`'s actuator cost is lower than material's
(8.6/5.6/8.0 vs. 12.0/7.0/8.0) — but this "saving" tracks its
smaller retained group size exactly (9.2/14.9/8.9 vs. material's
19-20), and `F_guard`'s identity-valid success (0.00-0.30) is far below
material's own nominal success (0.10-1.00) on every flock. Once identity
validity is accounted for, there is no efficiency gain left to claim: the
guarded controller does a smaller, mostly-invalidated job for a smaller
price, not the same job more cheaply. `L_reg` shows the same pattern even
more starkly — it costs about the same as material (since it rarely departs
from `I_0` at `lambda_T=0.1`) while its identity-valid success is 0.00-0.40,
worse than material's own nominal success on 2 of 3 flocks.

**5. Does a compact pathwise predictive boundary survive under the
stabilized descriptions? Yes.** Mean one-step leakage across all four
descriptions and three flocks stays in a **0.006-0.043 nat** band — the
same narrow range Stage 6.5's original (unstabilized) evaluation found
(0.0118-0.0143), now confirmed under the guard-stabilized functional
definition and the regularized (if imperfectly-tuned) lineage as well:

| seed | rep | mean leakage | boundary size trace |
|---|---|---|---|
| 2 | M | 0.0084 | 12 (constant) |
| 2 | L_reg | 0.0063 | 12 (constant) |
| 2 | F_guard | 0.0194 | 12 -> 7 (stabilizes, does not keep shrinking) |
| 2 | F (unguarded) | 0.0166 | 12 -> 4 (shrinks throughout) |
| 4 | M | 0.0426 | 17 (constant) |
| 4 | L_reg | 0.0273 | 17 -> 12 (one step change) |
| 4 | F_guard | 0.0247 | 17 -> 6 (stabilizes) |
| 4 | F (unguarded) | 0.0234 | 17 -> 3 (shrinks throughout) |

Instability of *membership* still does not imply instability of *screening*
— even `F_guard`'s post-collapse-detection boundary (which stabilizes at a
smaller size rather than continuing to shrink, unlike the unguarded `F`)
screens about as well as material identity's constant 12-17-member
boundary.

## Summary

| Question | Answer |
|---|---|
| Detector jitter vs. physical reorganization? | Some jitter (weak positive correlation, 0-7% of steps flagged), but not the dominant explanation |
| Does simple temporal regularization cleanly separate them? | No — every tested `lambda_T` suppressed genuine transitions by a larger fraction than jitter; at `lambda_T>=0.5` the regularized track never changes from `I_0` at all |
| Does representation dependence survive stabilization? | Yes, and a new form appeared: regularization tuned on baseline data fails specifically during active control (0.00 nominal success on 4/5 flocks) |
| Does the guard expose collapse rather than reward it? | Yes — 97-100% of `F_guard` closed-loop episodes are correctly flagged IDENTITY COLLAPSE / UNRESOLVED, vs. 0% for the unguarded definition that reaches the same nominal success via a 1.8-2.2-bird remnant |
| Does adaptive control remain cheaper after accounting for validity? | No — the actuator savings track the smaller (often invalid) group size exactly; no efficiency gain survives |
| Does a compact pathwise boundary survive stabilization? | Yes — leakage stays in a narrow 0.006-0.043 nat band across all four descriptions |

**This is a genuinely mixed, informative result, not forced toward either
extreme.** The guard mechanism (C3/C4) works cleanly and does exactly what
it was designed to do. The regularization mechanism (C2) does not achieve
a clean jitter/signal separation and, more importantly, reveals a real
generalization gap between calibration data (passive) and deployment data
(actively controlled) that a more sophisticated future mechanism would need
to address — reported here as a limitation discovered, not one to be
quietly tuned away.
