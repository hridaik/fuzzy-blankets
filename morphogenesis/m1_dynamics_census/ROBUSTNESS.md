# ROBUSTNESS.md — Part C

## Status: `ESTABLISHED`. 100 kick runs complete (first 20 primary individuals × 5 kick conditions).

## Headline finding: converged bodies return after EVERY tested kick

**100/100 kicks returned to (within numerical precision of) the pre-kick
end-state.** Zero `NEW-FORM`, zero `NONCONVERGED`. `d_pair` to the
individual's own pre-kick state is `~0.0` for every kick, every condition.

| Kick | n | RETURNED-SAME-ROLES | RETURNED-RELABELLED | NEW-FORM | NONCONVERGED |
|---|---|---|---|---|---|
| `K1_sigma0.5` (position, σ=0.5×spacing) | 20 | 20 | 0 | 0 | 0 |
| `K1_sigma1.5` (position, σ=1.5×spacing) | 20 | 15 | **5** | 0 | 0 |
| `K2` (secretion → population mean) | 20 | 20 | 0 | 0 | 0 |
| `K3` (belief → fresh `randn/8`, opaque-ID harness intervention) | 20 | 20 | 0 | 0 | 0 |
| `K4` (one cell, +3 spacing units) | 20 | 20 | 0 | 0 | 0 |

**Only the largest position kick (`K1_sigma1.5`) produces any relabeling**
(5/20 — cells swap which physical position/role they end up occupying
during reconvergence), and even then the **overall morphology** returns to
the identical attractor, not a different one. `K3` (a full belief reset —
arguably the most aggressive kick, discarding all accumulated identity
information) still returns 20/20 to the same roles, underscoring how strong
this attractor's basin is: even from a hidden-state reset equivalent to
restarting a fresh individual from the SAME (already-converged) position
and secretion, the system recovers the same role assignment.

## Integrator diagnostics

**Zero NaN/Inf in free energy across all 100 runs.** No integrator
instability from any kick, including the largest (`K4`: 3-spacing-unit
single-cell displacement).

## Relaxation timescales — two timescales, with a methodological caveat

- **Dynamical relaxation** (log-linear fit of `|J(t)-J_∞|` decay after the
  kick): **mean τ ≈ 55 bins**, consistent across all 5 kick types
  (54.96-55.47) — this is the genuine "how fast does the system return"
  timescale, and it is **~4.5x faster** than a fresh individual's approach
  to stationarity (246 bins).
- **Stationarity-criterion crossing** (this stage's frozen threshold):
  **mean bin 246 — identical to a FRESH individual's own convergence time**,
  despite starting already near the attractor. **This is a methodological
  artifact, disclosed rather than mistaken for a real finding**: the
  frozen stationarity criterion (`THRESHOLDS.md`) is a FIXED per-bin
  threshold (`1e-3`), and the developmental sensitivity ramp
  `s(t)=1-exp(-2t)` (m0c `ORACLE_FACTS.md` A2) itself keeps changing the
  system's effective forcing until `t` is well past `~0.5` (bin `~256` at
  `N=512`) **regardless of the state's actual distance from the
  fixed point** — so per-bin changes stay above the fixed threshold until
  the ramp itself settles, even for a state that is already at the
  attractor. **The true relaxation timescale for THIS stage's purposes is
  the `~55`-bin dynamical fit, not the 246-bin criterion-crossing bin.**
  This is flagged prominently in `TIMESCALES.md` and is itself a useful,
  disclosed finding about this stage's own threshold design.
- **Belief-concentration relaxation, tracked separately from
  observable-tier quantities**: `NOT DONE` this pass — only free energy
  was fit; a genuinely separate hidden-tier belief-concentration curve is
  a declared gap (`OPEN_QUESTIONS.md` item 2).

## Threshold sensitivity (×0.5, ×2 on `tau_pair`)

Given `d_pair` is `~0.0` (far below even `tau_pair×0.5=0.125`) for all
100 kicks, **the RETURNED classification is completely insensitive to
`tau_pair` at both `×0.5` and `×2`** — every kick would still classify as
RETURNED at either threshold. (The `RETURNED-SAME-ROLES` vs.
`RETURNED-RELABELLED` split, based on a separate nearest-cell role-continuity
check rather than `tau_pair`, is unaffected by this sensitivity sweep.)
