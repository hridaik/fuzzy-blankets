# Closure A — Organizational Role / Membership Privilege Results

## Question

Does organizational role have a reproducible CLASS-level effect even
though individual exterior actuator identity does not (established
negative, `stable_selectivity_analysis/`)? Four classes: core member,
boundary member, live exterior causal parent, near exterior non-parent.

## Design summary

8 states, K=1, d=8, release=24, up to 3 actuators/class/state, 4 physics
streams/actuator, 240 rollouts total. Interior actuators (core, boundary)
scored with the `A_minus_j`/`J_minus_j` correction
(`interior_correction.py`); exterior actuators (live parent, non-parent)
are unaffected by the correction by construction. Independent unit =
STATE throughout (`STATISTICAL_ANALYSIS.md`).

**Disclosed class-availability constraint** (see `STATE_MANIFEST.md`):
core member and near-exterior-non-parent actuators were available in all
8 states (96 rollouts each after 3-actuator-per-state sampling ×4
streams). Boundary member and live exterior parent actuators were
available in only 3/8 states (`sclosure_03`, `sclosure_05`,
`sclosure_06` — 28 and 20 rollouts respectively). Every class comparison
below is restricted to states where the relevant classes co-occur, and
`n_states` is reported explicitly for each comparison rather than implied.

## Class-level mean ΔJ_conservative (state-paired, A_minus_j-corrected, 90% bootstrap CI)

| class | n states with class | mean | 90% CI |
|---|---|---|---|
| core_member | 8 | −0.0038 | [−0.0158, +0.0085] |
| boundary_member | 3 | −0.0141 | [−0.0371, +0.0089] |
| live_exterior_parent | 3 | −0.0075 | [−0.0336, +0.0187] |
| near_exterior_non_parent | 8 | −0.0021 | [−0.0148, +0.0100] |

Every class's 90% CI spans zero. None of the four organizational classes
shows a reproducible positive class-level effect in this sample.

## Key paired comparisons (co-occurring states only)

| comparison | n states | mean diff | 90% CI |
|---|---|---|---|
| boundary − core | 3 | +0.0021 | [−0.0105, +0.0147] — spans zero |
| boundary − live parent | 3 | **−0.0068** | [**−0.0120, −0.0017**] — excludes zero |
| live parent − near non-parent | 3 | +0.0031 | [−0.0097, +0.0160] — spans zero |
| interior (core+boundary) − exterior (live parent+non-parent), pooled, minus-j | 8 | −0.0020 | [−0.0156, +0.0115] — spans zero |

The one comparison whose CI excludes zero (boundary − live parent,
−0.0068) rests on only 3 states with per-state diffs `[+0.0006, −0.0062,
−0.0149]` — 2/3 negative, 1/3 near-zero, i.e. the sign is not unanimous
even though the bootstrap CI (which resamples only 3 points) happens to
exclude zero. Given `n=3`, this is NOT treated as a robust "boundary is
worse than live-parent" finding — it is reported as a numerically
present but statistically fragile signal, disclosed rather than
suppressed or oversold.

Per-state `interior − exterior` diffs (8 states, wide spread, no
consistent sign): `+0.0060, +0.0032, −0.0240, −0.0004, +0.0049, +0.0380,
+0.0024, −0.0457` — 5/8 positive, 3/8 negative, magnitudes ranging over
more than an order of magnitude. This heterogeneity, not a consistent
sign, is itself the finding.

## Interpretation — which pattern was found

Checking each candidate pattern from the task spec against the data
above:

- **Membership privilege** (interior >> exterior after excluding forced
  interior bird): NOT supported — the pooled interior−exterior CI spans
  zero and per-state signs are mixed 5/8 vs 3/8.
- **Boundary privilege** (boundary >> core and exterior): NOT
  supported — boundary vs core spans zero; boundary vs live-parent is
  numerically NEGATIVE (opposite direction), not positive.
- **Live-parent privilege** (live exterior parent >> near exterior
  non-parent): NOT supported — CI spans zero, mixed sign (+0.026, −0.012,
  −0.005 across the 3 co-occurring states).
- **No stable class privilege** (all class effects small/inconsistent):
  **This is the pattern found.** Every class-level CI spans zero, every
  cross-class comparison CI either spans zero or is fragile at n=3, and
  per-state signs are inconsistent everywhere they can be checked with
  ≥5 states.

**Conclusion: no stable spatial/organizational actuator interface was
demonstrated among the four classes tested in this translating-flock
regime.** This extends (does not merely repeat) the individual-actuator
negative result from `stable_selectivity_analysis/`: even coarsening from
individual actuator identity to a 4-way structural-role classification
does not recover a reproducible class-level effect. Per the task's
decision language, this does NOT motivate a further exterior-selector or
class-refinement programme.

No further class-feature search was performed after this result, per the
task spec.
