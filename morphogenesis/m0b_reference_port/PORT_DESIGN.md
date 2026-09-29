# PORT_DESIGN.md — Task 2: function-by-function mapping

Status labels as elsewhere. This document is honest about a genuine
stopping point reached during the port: **L1 (function-level) primitives are
fully validated against Octave to numerical precision. The full D-step
Jacobian assembly and trajectory integration (L2/L3) was NOT completed** —
see "Where the port stopped" below.

## What "faithful" means here, concretely

Per the ground rules ("no invented learning rates, no explicit-Euler
substitutes"), every primitive below is a direct transliteration of the
named SPM12 source function, not a re-derivation or simplification, and each
is validated by calling the ACTUAL Octave function on identical inputs and
diffing outputs (not merely by reading the source).

## Function-by-function mapping (all in `code/spm_port.py` unless noted)

| Python function | SPM12 source | Validated? |
|---|---|---|
| `spm_softmax_cols` | `spm_softmax.m` | `ESTABLISHED` — identical formula to m0, re-verified against source text |
| `spm_diff_jacobian` | `spm_diff.m` (forward-diff path, `dx=exp(-8)`, source line 37) | `ESTABLISHED` — matches Octave's `spm_diff` to float precision on a nonlinear 2D test case (`[1.00033546 1.; -1. 0.36220142]` both sides, exact digit match) |
| `spm_DEM_R` | `spm_DEM_R.m` ('Gaussian' branch) | `ESTABLISHED` — exact match on `spm_DEM_R(3,1)` (3x3, all entries identical) |
| `spm_DEM_embed` | `spm_DEM_embed.m` | `ESTABLISHED` — exact match at an interior bin (t=4, order-0/1/2 = 7, 3.5, 1.0) and at a boundary bin (t=1, clamped window: 1, 0.5, 1.0), both against live Octave calls |
| `spm_dx` | `spm_dx.m` (dense `n<=512` path via augmented-matrix `expm`) | `ESTABLISHED` — exact match on a 2x2 test system (`[0.75079871, -0.39467986]` both sides) |
| `model.decode_template` | `DEM_morphogenesis.m` lines 44-86 | `ESTABLISHED` (carried over from `m0_reconstruction`, re-verified: n=8 for L=2, n=16 for L=4, both confirmed against live Octave `dem_setup` runs — `ORACLE_REPORT.md`) |
| `model.field_concentration` | local fn `morphogenesis` | `ESTABLISHED`, same formula as m0, k=1 fixed |
| `model.Mg` | local fn `Mg` | `ESTABLISHED` at the level of "produces the same shape/values as the m0 reduced port's Mg" (same formula); **not yet cross-checked against Octave's `dem_morphogenesis_Mg.m` output on identical `v` — flagged below** |
| `model.Gg` | local fn `Gg` | same status as `Mg` |

## Octave-side instrumentation built for L2 testing

`oracle/spm_ADEM_debug.m`: a disclosed, minimal patch on top of the pristine
`spm_ADEM.m` (diff: renamed function + `dumpbin`/`dumpfile` args + two
`save()` calls bracketing the local-linearization update at `iY==dumpbin`,
no other line touched — see inline comments in the file and
`ORACLE_REPORT.md`). Produces `dstep_dump_bin1.mat` containing, at bin 1 of
the vanilla-8 config: `qu.v{1}` (the recognition cause value, 64-dim),
`qu.v{2}` (its 1st generalized derivative, 64-dim, confirmed **zero** at
bin 1 — a clean initial condition), `qu.a{1}` (order-1 action, 48-dim), the
full error vector `E` (432-dim = 3 generalized orders x 144 = ny(80)+nv(64)),
`dE.du` (432x128), `dE.da` (432x48), `dE.dv` (432x243), `dFdu` (790-dim),
`dFduu` (790x790), `du` (790-dim, the actual local-linearization update spm_dx
produced), and the restriction matrix `R` (243x48). `ESTABLISHED` (real
numbers captured, reproducible via `oracle/run bin1 dump`).

Empirically confirmed (from this dump, not assumed): `E[0:80]` (sensory
prediction error, order 1) is **exactly zero** at bin 1, because the
canonical script initializes `a.x=g.x, a.s=g.s` from the model's own
prediction at the initial `v`, so process and model agree exactly before any
noise/field mismatch accumulates. `E[80:144]` (the order-1 prior error on the
cause) equals `qu.v{1}` exactly (i.e. the prior pulls toward zero, error =
value − 0), confirming the hierarchical error-stack structure described in
`spm_DEM_eval.m`. **ESTABLISHED.**

## Where the port stopped, and why (disclosed failure, not silently reduced)

The recursion in `spm_ADEM_diff.m` (SPM12) that propagates the process's
response to **higher generalized orders** —

```
u.v{1} = spm_vec(vi);
for i = 2:(n-1)
    u.v{i}     = dg.dv*u.v{i} + dg.dx*u.x{i} + dg.da*u.a{i} + u.z{i};
    ...
end
u.v{n}  = dg.dv*u.v{n} + dg.dx*u.x{n} + dg.da*u.a{n} + u.z{n};
```

— reads `u.v{i}` on **both** sides of the assignment for `i>=2`. This means
`pu.v{2}`, `pu.v{3}` must already hold a meaningful value *before*
`spm_ADEM_diff` is called (most likely the level-2/exogenous-cause portion of
the embedded prior-cause sequence, given `G(2).v` is a scalar always 0, but
this was not confirmed), and this session could not resolve, from static
reading alone and with confidence, exactly what that pre-existing value is
and how the "combined 81-dim" `u.v{i}` (process response levels 1+2
concatenated) is partitioned across this update. Given the earlier
misreading incident in this same session (`spm_DEM_embed`'s boundary case,
caught only by direct numeric comparison against Octave — see
`ORACLE_REPORT.md`), continuing to hand-derive this recursive step without
an analogous numeric check was judged too likely to produce a plausible but
silently wrong port. **Rather than ship that risk, this is reported as a
stopping point: L1 primitives are done and validated; the full D-step
Jacobian assembly (`dFdu`, `dFduu`) and hence L2 single-step and L3
trajectory equivalence testing are `NOT DONE`.**

## What would unblock this (concrete, for a follow-up session)

Add one more `save()` inside `spm_ADEM_debug.m`, this time **inside**
`spm_ADEM_diff.m` itself (a second disclosed patched copy), dumping `u.v`
(all 3 orders) both on entry and exit of that function at bin 1. That
isolates the exact recursion in question to a single, small, directly
checkable numeric example — the same technique that already resolved the
`spm_DEM_embed` boundary-case error in this session. This is a small,
well-scoped next step, not a re-opening of the whole problem.

## Consequence for Tasks 3-6

- **Task 3 (equivalence)**: L1 done with concrete numbers above. L2/L3
  `NOT DONE`. See `EQUIVALENCE_REPORT.md`.
- **Task 5 (characterization)**: requires a *validated* port per the task's
  own instruction ("validated port only") — `NOT DONE` in this pass.
- **Task 6 (viewer)**: Octave-vs-Python synced comparisons need a working
  Python trajectory — `NOT DONE` for the Python side; the viewer's
  Octave-only visualizations (oracle traces alone) were not built either,
  for lack of remaining session time, and are reported `NOT DONE` rather
  than built partially and left undocumented.
- **Task 4 (perturbations)**: the catalog, classification, and
  Octave-side CODE-BASED golden traces (Pio-Lopez high-identity, already
  obtained in Task 1) are reported in `PERTURBATIONS.md`; Python
  implementation and the "continue to 512 bins" requirement are `NOT DONE`
  for the same reason.
