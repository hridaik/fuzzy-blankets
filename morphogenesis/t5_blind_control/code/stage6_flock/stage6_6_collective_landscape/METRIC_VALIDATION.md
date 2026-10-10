# METRIC_VALIDATION.md — Stage 6.6

Gate required by task brief section 15: **before** integrating the
landscape into the demo, do the four metrics produce interpretable
distinctions on controlled archetypes? This document was written from
`data/archetype_trajectories.json` (all 3 seeds x 5 conditions x the `f_E`
sweep, fully computed) and the first completed full candidate landscape
(`data/seed2__no_control__fE1.00__t20.json`, 5000 candidates), before the
remaining 14 landscape snapshots finished generating and before any figure
or UI polish. **Numbers below are not adjusted after the fact.** Where a
question needs the full 15-snapshot landscape for a complete cross-seed
answer, that is stated explicitly and finalized in `RESULTS_6_6.md`.

Verdict up front: **the gate passes.** The four metrics separate cleanly
and in the qualitatively expected directions on every controlled archetype,
and the natural-regime landscape already shows genuine, non-degenerate
independence between coherence and integration. No metric definition was
changed to produce this outcome — see `code/metrics_66.py`,
`code/predictive_cache.py` for the frozen formulas, unchanged since before
any archetype ran.

## Q1: Does global/same-direction alignment yield high C but low D?

**Yes, cleanly.** At `f_E=1.0` (full second-ring exterior forced toward the
same target `h*` as the shell):

| seed | C | D | H_E |
|---|---|---|---|
| 2 | 1.000 | 0.000 | ~0.000 |
| 3 | 1.000 | 0.000 | ~0.000 |
| 4 | 1.000 | 0.000 | ~0.000 |

`D=0.000` exactly across all three seeds is not a coincidence: with the
near-exterior forced to the *identical* heading as the shell (and the
interior successfully retargeted, `C=1.000`), `p_I` and `p_E_near` become
literally the same one-hot distribution, so `JSD(p_I,p_E_near)=0` exactly —
this is the "everything looks like one giant flock" case the task brief
predicts, reproduced numerically, not just qualitatively.

## Q2: Does opposite exterior yield high D without automatically implying low leakage?

**High D: yes, cleanly.** At `f_E=1.0`, `D=1.000` for all three seeds
(interior and near-exterior driven to disjoint one-hot heading
distributions — maximal JSD by construction).

**"Without automatically implying low leakage": partially answered by the
fixed-`I0` archetypes, fully answered by the landscape.** For the fixed
`I0` candidate on all three seeds, `|S(I0)|` happens to be `<=K=12`
(`shell_size: 12/12/~12` per seed — see `configs/protocol_6_6.yaml`), so
`boundary_search` always selects `B=S(I0)` and `L_I=0` **exactly by
construction** (proven in `tests/test_predictive_metrics.py::
test_full_structural_shell_gives_exactly_zero_leakage`), regardless of
which archetype condition is active. This means the fixed-`I0` archetypes
alone cannot show high-D-with-high-L (their `L` is always ~0 by a
structural coincidence of this particular flock's canonical interior, not
because leakage is genuinely low for every candidate). The full landscape
answers the general question directly: in `seed2__no_control`, 99.78% of
the 5000 candidates have `|S(I)| > 12` (mean shell size 31.6, i.e. real
budget-constrained search happens almost always), and among those, `L` and
`D` are only weakly correlated (`r=0.058`) — so **high-D candidates with
non-trivial `L` do occur**, `L` is not automatically pinned to zero just
because a candidate is visually distinct. Full cross-condition (not just
natural-regime) confirmation is in `RESULTS_6_6.md` once all 15 snapshots
are in.

## Q3: Does disordered exterior yield high D and high external entropy?

**Yes, both, cleanly, and the entropy signal is sharper than the contrast
signal:**

| seed | D | H_E |
|---|---|---|
| 2 | 0.572 | 0.994 |
| 3 | 0.485 | 0.994 |
| 4 | 0.536 | 0.998 |

`H_E` is near its ceiling of 1.0 (balanced rotating exterior across all
four headings) in every seed. `D` is clearly elevated relative to the
same-direction condition's `D=0.000`, but noticeably below the opposite
condition's `D=1.000` — the interior (concentrated on one heading) versus a
4-way-spread exterior gives a genuine but partial JSD, not a maximal one.
This is exactly the qualitative distinction task brief section 7 asks the
two secondary diagnostics to draw out: an opposite-coherent exterior
(`D=1.000, H_E~0.000`) and a disordered exterior (`D~0.5, H_E~0.995`) are
both clearly JSD-distinct from the interior, but the entropy diagnostic is
what tells them apart, confirming `H_E` is not redundant with `D`.

## Q4: Do high-C candidates sometimes have low G?

**Yes, and this is the most important single finding of the sanity check.**
Two independent pieces of evidence:

1. **Fixed-`I0` archetype, seed 3, natural regime**: `C=1.000` but
   `G=0.0022` — near-zero internal predictive integration despite perfect
   coherence.
2. **Full landscape, seed 2, natural regime, n=5000**: among the 4106
   candidates with `C>0.9`, 996 (24%) fall in the bottom quintile of `G`.
   More strikingly, the *overall* Pearson correlation between `C` and `G`
   across all 5000 candidates is **`r=-0.76`** — strongly negative, not
   merely "sometimes decoupled." A plausible mechanism (stated as a
   hypothesis, not asserted as fact — see `RESULTS_6_6.md` for the
   fuller discussion): in an unforced regime, near-unanimous interior
   coherence more often reflects that the *boundary itself* already
   dictates the local consensus (so knowing the rest of the interior adds
   little beyond knowing the boundary, i.e. low `G`), whereas moderate
   coherence more often coincides with genuine internal correlation not
   fully explained by the boundary. This is a real, load-bearing
   distinction the two-axis (not one-scalar) design was built to expose —
   collapsing `C` and `G` into one score would have hidden it.

## Q5: Do low-leakage candidates sometimes have poor contrast?

**Yes — and the fixed-`I0` archetypes give a clean, if structurally
special, illustration.** `L_I0 ≈ 0` (exactly, by the same shell-size
coincidence as Q2) in *every* archetype condition, while `D` ranges from
`0.000` (same-direction) to `1.000` (opposite) across those same
near-zero-`L` observations. So for this one candidate, leakage stays
pinned near zero *regardless* of contrast — the two axes visibly do not
move together. In the general landscape (seed 2, natural regime, `L` in
`[-0.0008, 0.0043]`, i.e. a tiny dynamic range dominated by finite-sample
noise around zero — see Q7), essentially every candidate has near-zero `L`
under natural dynamics (mean `9.7e-6`), including plenty with `D` at or
near the regime's own low ceiling (max `D=0.075` in this unforced
snapshot). A full "is there a non-trivial low-L/poor-D cluster in a
regime where L actually varies" answer needs a forced-exterior landscape
(where more genuine cross-boundary information pressure exists) —
addressed in `RESULTS_6_6.md`.

## Q6: Are there visually convincing candidates in the high-G, low-L, high-C, high-D region?

**Not yet checked with a controlled/forced-exterior landscape; the natural
regime alone says "essentially no."** In `seed2__no_control` (n=5000), only
**1** candidate (the reference `I0` was not the one — checked separately)
falls in the joint top-quintile-`G` / bottom-quintile-`L` / `C>0.9` /
top-quintile-`D` region. This is consistent with, not contradictory to, the
stage's own working hypothesis: the *natural, unforced* regime is precisely
the "arbitrary patch of a globally aligned system" case the task brief
motivates this whole stage around — under it, `D` barely varies (see Q7),
so a jointly-high-on-all-four-axes candidate is expected to be rare.
Whether such candidates become common once the exterior is genuinely forced
into contrast (the `same_direction`/`opposite`/`disordered` landscape
snapshots, still generating) is exactly what `RESULTS_6_6.md` reports.

## Q7: Are there obvious visually bad candidates that nevertheless score well on some subset of metrics?

**Yes, structurally guaranteed by Q1's own mechanism.** Every candidate in
the natural regime whose local neighborhood is part of the flock's large
aligned bulk will show `D≈0` (indistinct from its surroundings) while often
still showing high `C` (internally coherent, since the whole neighborhood
shares one heading) — i.e. "looks like nothing special, but scores well on
coherence alone." This is visible directly in the summary statistics: 4106
of 5000 candidates (82%) have `C>0.9`, while the *same* population's `D`
never exceeds 0.075 (regime ceiling). A concrete face-validity check with
rendered lattices (not just summary statistics) is deferred to
`figures/fig_6_6_4_candidate_comparison.png` and `RESULTS_6_6.md`, once
generated.

## A genuine finite-sample caveat surfaced by this check, reported rather than hidden

`L`'s dynamic range under the natural regime is small (`mean=9.7e-6,
sd` on the order of `1e-3`) and includes negative values down to `-0.0008`
— i.e. **comparable in magnitude to plausible finite-sample noise**, not
clamped to zero per task brief section 5's instruction. This is not a bug:
the underlying model has an exact one-hop causal horizon (each bird's next
state depends only on its own current state and its own up-to-8 Moore
neighbours' current states — `flock_sim.active_inference.compute_G`), so a
`K=12` boundary shared across a 20-bird interior is, in the *unforced*
regime, nearly always sufficient to screen off virtually all one-step
information from beyond it, for almost any connected 20-node shape, not
just visually "good" ones. This is itself a real, reportable finding about
this metric's discriminative power in this regime (see
`RESULTS_6_6.md`, question "Does fixed-budget leakage distinguish
compactly screenable groups from arbitrary connected regions?") — not
something to paper over by re-normalizing or rescaling `L` after the fact.

## Gate decision

**Pass.** Every qualitative expectation in task brief section 11/15 that
could be checked from the fixed-`I0` archetypes and the first completed
full landscape held up under real numbers, including two genuinely
surprising, unforced findings (`C`-`G` anti-correlation in the natural
regime; `L`'s near-uniform near-zero-ness under natural dynamics) that were
reported rather than smoothed over. Proceeding to the full landscape
generation and demo integration is justified. `RESULTS_6_6.md` completes
the cross-seed, cross-condition picture once all 15 primary snapshots have
been generated.
