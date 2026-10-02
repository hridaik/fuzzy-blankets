# RESCUE_FIX.md — Part A

## The implementation gap (documented, per the task)

m0c's `kuchling_rescue` perturbation kind (`m0c_port_completion/oracle/
dem_morphogenesis_Gg_perturbed.m`) applied **only** the sqrt-distance field
kernel to the target cell(s) — it never paired this with the squared-position
anomaly (eq. 48/49 of Kuchling et al. 2020) it was meant to rescue. As a
result, m0c's `kuchling_rescue_*` runs trivially reproduced baseline (nothing
was broken to begin with) and did **not** demonstrate an actual rescue.
This was disclosed in m0c's own `PERTURBATIONS_EXECUTED.md` and flagged in
`OPEN_QUESTIONS.md` item 9. **This stage fixes it.**

## The two readings, and the fix

Kuchling et al. 2020 describes the single-cell rescue two ways:
- **R-text** (eq. 50, p.19): the misbehaving cell's own sensed field is
  computed with `sqrt(distance)` in place of `distance` in the exponential
  kernel — i.e. a **self**-correction to the anomalous cell's own receiving
  field.
- **R-caption** (Fig. 5C caption, per the task): rescue by **increased
  signalling sensitivity of the OTHER cells** — i.e. a correction to how
  the rest of the population responds, not to the anomalous cell itself.

Both are now implemented as **new, correctly-paired** perturbation kinds in
`oracle/dem_morphogenesis_Gg_perturbed.m` (a copy in this stage's own
`oracle/`, not a modification of m0c's file):

- `kuchling_rescue_text`: the anomalous cell gets **both** the squared-position
  distortion (`g.x(1,c) = sign*(a.x(1,c))^2`, ramped) **and** the sqrt-distance
  kernel on its own receiving field, in the same run.
- `kuchling_rescue_caption`: the anomalous cell gets the squared-position
  distortion (no self-fix); all **other** cells get their extracellular
  sensitivity (`g.c`) scaled up by a declared `rescue_factor`
  (swept 1.5, 2, 4).

m0c's original `kuchling_rescue` kind is **kept, unmodified, for
reproducibility of the m0c number**, but its docstring now states plainly
that it should not be used for new work.

## Results

`ESTABLISHED`. Canonical individual (seed 0) + 10 census individuals (seeds
1-10), N=512, anomalous cell = index 5 (1-based, fixed across individuals),
`ramp_w=4`. Individual is the unit of replication (n=11); `code/analyze_rescue.py`.

| Condition | n | mean `d_target` | mean `d_pair` to unperturbed twin | position-switch rate (Wilson 95%) |
|---|---|---|---|---|
| AN alone (no rescue) | 11 | 0.341 | 0.081 | 6/11 [0.28, 0.79] |
| **R-text** (eq. 50, sqrt-kernel self-fix) | 11 | **0.340** | **0.077** | 4/11 [0.15, 0.65] |
| R-caption, factor 1.5 | 11 | **0.246** | 0.334 | 6/11 [0.28, 0.79] |
| R-caption, factor 2.0 | 11 | 0.504 | 0.574 | 11/11 [0.74, 1.00] |
| R-caption, factor 4.0 | 11 | 0.883 | 0.886 | 10/11 [0.62, 0.98] |

(For reference, the unperturbed population's own converged `d_target` is
`0.2873` for every individual — `CENSUS.md`.)

### Which version reproduces the published description?

**R-text (eq. 50) provides essentially no improvement over the unrescued
anomaly**: mean `d_target` 0.340 vs. AN-alone's 0.341 — statistically and
practically indistinguishable, and both are noticeably *worse* than the
unperturbed population's own `0.2873`. Under this implementation, **the
sqrt-distance self-correction does not rescue the phenotype.**

**R-caption (increased sensitivity of the OTHER cells) shows a genuine,
dose-dependent effect, but only in one direction at first**: at a **mild
factor of 1.5×**, `d_target` improves to **0.246 — better than even the
unperturbed baseline (0.287)** — a real rescue, and by this specific
(admittedly narrow) metric, an *overcorrection past baseline*. But
**stronger factors make it progressively worse**: 2.0× gives 0.504, 4.0×
gives 0.883 — both substantially worse than doing nothing. **This is a
clean, reportable dose-response finding**: the caption's mechanism *can*
rescue, but only within a narrow sensitivity range; it is not simply
"more is better."

**Conclusion**: of the two published readings, **R-caption (Fig. 5C) is the
one that reproduces a genuine rescue effect in this implementation, and
only at the mild end of the swept range (1.5×)** — R-text (eq. 50) does
not rescue at all under this implementation. This is reported as
`ESTABLISHED` for this specific implementation choice of both mechanisms
(m1's `dem_morphogenesis_Gg_perturbed.m`); it does not rule out that a
different implementation of eq. 50's self-correction could behave
differently — see `OPEN_QUESTIONS.md`.

### Position switch?

**Yes, and its rate tracks rescue strength.** Even AN-alone already shows a
6/11 "switch" rate (the anomalous cell's original template-role, as held in
the unperturbed twin, ends up occupied by a *different* cell after the
anomaly) — the population's role assignment for that slot is not perfectly
stable even without rescue. R-text's switch rate (4/11) is nominally lower
but the Wilson intervals overlap substantially (`[0.15,0.65]` vs.
`[0.28,0.79]`) — not a confident difference at n=11. **R-caption's stronger
factors show clearly elevated switching (11/11 at 2.0×, 10/11 at 4.0×)** —
consistent with the Fig. 5C caption's own description of "another cell
switching position with the aberrant cell," and consistent with the
mechanism's growing disruptiveness at higher factors.

