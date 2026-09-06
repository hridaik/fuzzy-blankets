# Rate-induced-loss audit: Figure 3 / Section 9 — final summary

This audit is additive to Stage 5. `rate_induced.py`, `quasistatic.py`, Figure 3, and
all previously saved Stage-5 results are **unmodified**. All outputs are under
`stage5/data/rate_induced_audit/`. The model was not tuned; two genuine numerical bugs
in the *audit's own new code* were found and fixed mid-analysis (documented below) —
neither existed in, nor affected, the original Stage-5 `rate_induced.py`.

## Answers (Q1–Q10)

**Q1 — Was the old Figure-3 right-panel maximum calculated only during the ramp?**
Yes, exactly. `quasistatic.slow_ramp_run` integrates only over `[0, T_ramp]`
(`dyn.integrate(..., T_ramp, ...)`), and `rate_induced.run_ramp` takes `max()` over
that same array. Verified in Part 1 by re-running the *unmodified* original functions
and reproducing the saved Figure-3 curve to `0.000e+00` absolute difference at every
one of the 6 primary `T_ramp` values.

**Q2 — For fast ramps, does the largest leakage occur after the ramp ends?**
Yes. For `T_ramp <~ 0.2`, the full-event peak occurs strictly in the post-ramp
relaxation window — e.g. at `T_ramp=0.001` the peak is at `t≈0.104`, i.e. ~104× the
ramp duration, entirely outside the window the original analysis ever looked at.

**Q3 — Does the non-monotonic max_t Λ3 vs T_ramp survive full post-ramp accounting?**
**No.** Audit Fig B is definitive: the during-ramp-only curve (green) exactly
reproduces the old non-monotonic bump peaking at `T_ramp≈0.2`. But the full-event
curve (orange, `max` over the *entire* ramp+relaxation window) is a **flat plateau**
at `≈4.22×10⁻⁵` for `T_ramp` from `0.001` up to `≈0.15–0.2`, then **monotonically
decreasing** for all `T_ramp` beyond that, all the way to `16`. There is no interior
local maximum in the full-event curve. This holds for K=1,2,3,4 (Fig D) and for all
three tested ramp shapes — linear, smoothstep, smootherstep (Fig E).

**Q4 — If yes, mechanistic explanation:** N/A (answer to Q3 is No).

**Q5 — What caused the apparent old peak?**
A pure **truncation-window artifact**. For fast ramps, the true (large) peak occurs
after `t=T_ramp` and was never measured; the during-ramp window instead captured only
the *rising edge* of that same transient, and where that rising edge is cut off
happens to itself be non-monotonic in `T_ramp` (rising then falling as the window
endpoint sweeps past where the peak "would" be) — producing the appearance of an
intermediate-rate peak in a quantity that isn't the quantity of scientific interest.

**Q6 — What causes the two apparent leakage bumps?**
Two mechanistically DISTINCT phenomena (quantified in Part 10, `T_ramp=0.2`):
- **Primary bump** (`t≈0.208`, right at ramp completion): `K_delta=3` exactly at the
  peak (`Λ2=1.55e-2`, still far above `delta`), so a size-2 boundary is genuinely
  inadequate at this instant — this is a real boundary-CAPACITY event. Dominant
  `ΔK_{I,E}` entries are large and uniform (~0.0104) across all six `(I,E)` pairs.
- **Secondary bump** (`t≈0.544`, well after ramp completion): `K_delta=2` ALREADY
  (`Λ2=9.6e-5`, tiny), so the boundary-capacity transition is over. The residual
  `ΔK_{I,E}` entries are smaller (~0.0036) and of the OPPOSITE SIGN — a genuine
  multi-mode covariance-relaxation echo/overshoot, not a capacity event.

**Q7 — Are the bumps associated with the 2→3→2 boundary-capacity handoff?**
Only the **first** bump is (Hypothesis H1/H2: it coincides exactly with `K_delta=3`).
The **second**, smaller bump occurs while `K_delta=2` already, so it is explained by
**Hypothesis H3** (residual multi-eigenmode covariance lag), not the boundary
handoff. Answer: **a mixture (H4)** — first bump is capacity-driven, second is
lag-driven — quantified, not inferred visually, via the `ΔK` sign/magnitude table.

**Q8 — What happens for K=4?**
Same plateau-then-decay shape as K=3 (Fig D), consistently ~2.5–3× smaller in
magnitude throughout, never near-eliminating the effect (K=4 is not close to a
"trivial absorb-everything" regime here — even K=4's plateau is a genuine, non-zero
`≈1.6×10⁻⁵`).

**Q9 — Is the (corrected) finding robust to ramp shape?**
Yes. All three predeclared shapes (linear, smoothstep, smootherstep) show the same
qualitative plateau-then-monotone-decay full-event curve (Fig E); the plateau value
and the decay onset location shift only slightly (smootherstep plateaus/decays very
slightly later than linear), confirming the effect is a rate/timescale phenomenon,
not an artifact of the smoothstep's specific derivative-discontinuity structure.

**Q10 — Replacement for Paragraph 12** (see below).

## Recommended replacement for Section 9 / Figure 3 Paragraph 12

> Contrary to the originally reported finding, transient screening leakage is **not**
> maximized at an intermediate ramp duration. When the actual covariance is followed
> through the full post-ramp relaxation (not just the `[0,T_ramp]` window used
> originally), `max_t Λ3` is a flat plateau at its `T_ramp→0` (instantaneous-jump)
> value for all sufficiently fast ramps, then decreases monotonically as `T_ramp`
> increases toward the quasi-static regime — recovering `Λ3→0` as `T_ramp→∞`. The
> qualitative hypothesis that finite-rate structural change can transiently destroy
> exact screening still holds (leakage is strictly positive for any finite ramp rate),
> but its correct rate-dependence is **fastest-is-worst, monotone**, not
> intermediate-rate-is-worst. The apparent secondary bump visible within a single
> trajectory's leakage trace is real but mechanistically split: a capacity-driven
> peak exactly at ramp completion (where `K_delta` transiently rises to 3) followed by
> a smaller, purely relaxation-lag-driven echo after the boundary has already returned
> to `K_delta=2`. This finding is a property of this toy transition's timescale
## structure (verified robust to ramp shape, blanket capacity K=1..4, and tight
## numerical convergence) and should not be over-generalized without further study.

## Numerical integrity notes (found and fixed during this audit)

Two bugs were found in the audit's *own* new integration code (not in any existing
Stage-5 file) and fixed before any conclusion was drawn from affected data:

1. **RK45 step-aliasing over the forced transient.** Naively tightening
   `rtol`/`atol` with no `max_step` cap caused scipy's adaptive stepper to
   occasionally skip the entire narrow forced transient near `t=T_ramp` (signature:
   *fewer* function evaluations at *tighter* tolerance). Fixed by capping the solver's
   step during the ramp segment at `T_ramp/20` (verified stable to `T_ramp/100`,
   agreement to 7 significant figures) — added as a new, additive, default-`None`
   `max_step` parameter to `dynamics.integrate`, so no other Stage-5 code is affected.
2. **Segment-2 time-reference bug.** After splitting the ramp+relaxation into two
   `solve_ivp` calls (for efficiency — capping `max_step` over the whole long
   relaxation tail was needlessly slow), the second segment initially reused the
   ramp's own forcing closure, whose internal `t>=T_ramp` cutoff referenced GLOBAL
   time but received segment-2's LOCAL time (restarting at 0) — spuriously
   re-triggering ramp forcing and driving `z` far outside `[-1,1]` (caught via an
   anomalous `z=+3.56` in the Part 10 output, which also crashed Part 13's
   `Omega_of_z` call, since that function assumes `z∈[-1,1]`). Fixed with a dedicated,
   time-independent hold-forcing function for segment 2. Both bugs were caught,
   diagnosed, and fixed before generating any figure or table used in the final
   answers above; the primary sweep was re-run cleanly after each fix (see
   `run1_final.log`, `run2_final.log`).
   The peak-leakage *values* themselves (Fig B's headline plateau) were only
   mildly affected by bug 2 (secondary-peak location/anatomy in Part 10 was the
   part materially corrupted) and were not affected by bug 1 at the tolerances the
   primary 94-point sweep actually used (`rtol=1e-9,atol=1e-11`, unconstrained) —
   confirmed by the clean post-fix Part 15 convergence table (reldiff ~1e-7 to 1e-4
   between baseline/tighter-tolerance/denser-grid variants at all 5 test points).

## Outputs

- `full_event_peak_table.csv` — 94 T_ramp × 4 K values: during/post/full peaks,
  peak location, refined-peak cross-check.
- `full_event_sweep_smoothstep.npz` — full stored trajectories for 17 representative
  T_ramp values.
- `shape_robustness_table.csv` — 24 T_ramp × 3 shapes, K=3.
- `numerical_convergence_table.csv` — 5 T_ramp × {baseline, 10x tighter tol, 2x denser
  grid}.
- `precision_lag_peak_table.csv` — dominant ΔK_{I,E} entries at both T_ramp=0.2 peaks.
- `quasistatic_decomposition.npz` — actual vs quasi-static Λ2/Λ3, T_ramp=0.5.
- `T_relax_robustness_table.csv` — T_ramp×T_relax cross-check (see above).
- `instantaneous_jump.csv`/`.npz` — the true T_ramp→0 limit (Part 7).
- `audit_fig_A` through `audit_fig_F` (.png/.pdf/.svg).
- `audit_log.txt` — full run-by-run console log (Parts 1,2,4,10,11,12,13,15).
- `part7_log.txt` — Part 7 standalone log.

## T_relax robustness (now run directly)

`T_ramp ∈ {0.001, 0.02, 0.2, 1}` × `T_relax ∈ {4, 8, 12}` (12 runs, `T_relax_robustness_table.csv`):

| T_ramp | T_relax=4 | T_relax=8 | T_relax=12 |
|---|---|---|---|
| 0.001 | 4.2228e-05 | 4.2197e-05 | 4.2228e-05 |
| 0.02  | 4.2204e-05 | 4.2202e-05 | 4.2139e-05 |
| 0.2   | 3.8300e-05 | 3.8302e-05 | 3.8294e-05 |
| 1     | 1.3001e-05 | 1.3000e-05 | 1.3001e-05 |

Max spread across `T_relax` at any `T_ramp` is `<0.16%` (worst case `T_ramp=0.02`),
and peak timing (`t_peak`) agrees to `<2%` throughout. Confirms directly (not just by
the indirect early-peak/deep-decay argument) that `T_relax=8` is more than sufficient
and none of the reported peak values in Figs A/B/D/E would change under `T_relax=12`.

## Recommendation

**MODIFY.** Do not KEEP the original non-monotonicity claim as stated — Q3 shows it
does not survive full post-ramp accounting and was a truncation-window artifact. Do
not fully RETRACT the underlying qualitative hypothesis either — finite-rate leakage
is real, robustly positive, and mechanistically decomposed here into a genuine
capacity-driven component and a genuine lag-driven component. The correct replacement
statement is the one given above under Q10: fastest-ramp-is-worst with a plateau
below `tau_x`, monotonically improving as `T_ramp` grows past `~tau_x`.
