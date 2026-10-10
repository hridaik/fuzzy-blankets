# Stage 6.12 — Theory and Estimands

## Unit of analysis

A Stage 6.12 experimental state: saved simulator state `x_t0 = (r_t0, z_t0)`;
material target lineage `L_t0` with exact membership `I_t0` (the
`ForwardMaterialTrace611` accepted set at `t0`); requested heading `h_star`;
eligible exterior pool `P_t0` (primary: `nearest_M_pool(I_t0, r_t0, L, 20)`);
intervention budget `b=(K,d)`. The action is a fixed actuator set
`S ⊂ P_t0`, `|S|=K`.

## Primary intervention semantics (frozen)

1. Select `S` once at `t0`.
2. Force birds in `S` toward `h_star` for exactly `d` consecutive real
   simulator steps (offsets `0..d-1` relative to `t0`). No replanning.
3. Release all forcing.
4. Observe for a fixed `R_RELEASE = 24` further steps.

## Outcome definitions

`A(t)` = fraction of the *currently valid* material-target members at
`h_star` (the historical fraction-at-target metric, unchanged).

**9.1 Immediate/control response**: `align_plus4` (alignment at `t0+min(d+4,
n-1)`), `align_end_forcing` (at `t0+d`), `mean_forcing_tail` (mean over the
final `min(4,d)` forcing steps), `peak_forcing` (max alignment during
forcing).

**9.2 Release/persistence response**: `A_release_late` = mean alignment over
the *final 8* release steps (the PRIMARY persistent measurement);
`end_of_release_alignment`; `peak_release`; full `release_trajectory`.

**9.3 Strict identity validity `V`**: `V=1` iff the trace status is
`continuing` (no `dead`/`unresolved` frame) through every step of the
release-evaluation window; else `V=0`. Event type is reported separately:
`none`, `lost_dead`, `unresolved`, `candidate_split_or_merge_interruption`,
and `+split_flag`/`+merge_flag` suffixes when a split/merge flag fired
anywhere in `[t0, t0+d+R_RELEASE]`. **`V=0` is a control-utility convention,
not a claim that physical alignment is literally zero** — raw alignment is
always reported alongside `V`.

**9.4 Primary valid-control utility**: `J = V · A_release_late` (0 when
`A_release_late` is undefined, e.g. the target is dead throughout the
window).

## Paired causal effect (CRN)

For physics replicate `r`, `J0_r` = no-forcing utility from the identical
saved state and the identical physics RNG stream. For actuator set `S`,
budget `b`: `Delta_r(S,b) = J_r(S,b) - J0_r`. Because the intervention and
no-control branches share `physics_seed`, this difference is attributable to
forcing alone up to the point the forced action itself diverges the
trajectory (verified by `rng_crn_diagnostic_612.py`).

**Compute optimization (does not change the estimand)**: because a
no-forcing rollout does not depend on `d`, one `D_MAX + R_RELEASE`-step
no-control rollout per stream is simulated once per state and sliced at
every `d ∈ {1,2,4,8,16,24}` to obtain `J0_r` for all six `d` values —
`run_no_control_full` in `intervention_612.py`.

## Generic susceptibility

`G_sus(x,b) = mean over sampled S, r of Delta_r(S,b)`, `S` drawn uniformly
from `P_t0`'s `K`-subsets via the DESIGN rng (never the physics rng). Also
reported per cell: median, p10/p90, fraction of actuator sets with positive
mean effect, identity-valid fraction, split/loss rates. `G_sus > 0` means a
typical random exterior intervention tends to help; it does **not** by
itself mean actuator identity matters.

## Actuator-set selectivity

**Between-set variance**: for the sampled sets `s` and shared physics
streams `r`, `J_sr = mu + alpha_s + beta_r + epsilon_sr`. We report
`between_set_var` = the sample variance (ddof=1) of each set's own
CRN-paired mean `J` across physics streams, and `within_set_var` = the mean
per-set variance across its own streams — a paired/ANOVA-style decomposition
that respects the CRN coupling (never treats `n_sets × n_streams` rollouts
as independent observations for variance-of-the-mean purposes; the between-
vs-within split is exactly the quantity that isolates reproducible
actuator-identity structure from shared physics-realization noise). A
between-set variance that is small relative to within-set noise is direct
evidence *against* selectivity at that state-budget.

**Best-found vs. random (the decisive test)**: `S_star` is selected using
DEVELOPMENT-only physics streams (Phase B), then frozen and evaluated on
FRESH holdout physics streams never touched during search (Phase C):

```
G_sel(x,b) = mean_holdout[J(S_star,b)] - median_random_holdout[J(S,b)]
```

A "best" set evaluated only on the streams used to find it is not accepted
as evidence (post-selection bias) — see `SELECTIVITY_ANALYSIS.md` for the
explicit dev-vs-holdout separation on every reported number.

## Readiness classification (continuous evidence first, label second)

- **No demonstrated response**: no clear `G_sus` and no clear between-set
  variance/held-out `G_sel` signal.
- **Generically susceptible**: `G_sus` clears a positive floor, but
  `best_found ≈ random` on held-out streams.
- **Selectively addressable**: a frozen best-found `S_star` reproducibly
  outperforms the random-set distribution on held-out streams — may occur
  whether or not the average random set also helps.
- **Organizationally unsafe / unstable overlay**: reported separately
  whenever identity-survival is poor or split/loss probability is high,
  regardless of the alignment label (see Example C in the original task
  brief — a high raw-alignment, identity-failed rollout is never credited as
  successful strict control; `J` already encodes this via `V`, but raw
  alignment is always reported alongside it so the distinction stays
  visible).

## Mechanistic diagnostics (audit-only, S16)

Logged per intervention rollout, using true-`R` oracle information, never
used to choose the primary nearest-20 actuator sets: direct actuator→target
contact count at `t0`, cumulative direct-contact edges during forcing,
unique target-member coverage, actuator-target distances, whether an
actuator entered the target lineage, first step (if any) an actuator loses
all direct contact. See `MECHANISM_ANALYSIS.md`.
