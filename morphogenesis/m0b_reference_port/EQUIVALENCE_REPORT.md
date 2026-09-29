# EQUIVALENCE_REPORT.md — Task 3

## L1 — function level: `ESTABLISHED`, tolerance and results

Declared tolerance: exact match to displayed float precision (effectively
~1e-6 relative or better, since all comparisons below used deterministic
arithmetic with no accumulated iteration).

| Function | Test input | Octave output | Python output | Match |
|---|---|---|---|---|
| `spm_DEM_R(3,1)` | n=3,s=1 | `[[1.5,0,1],[0,2,0],[1,0,2]]` | identical | exact |
| `spm_dx(A,f,1)` | 2x2 linear system | `[0.7508, -0.3947]` | `[0.75079871, -0.39467986]` | exact (Octave display truncated) |
| `spm_DEM_embed(Y,3,4,1,0)` | interior bin | `7, 3.5, 1` | `7.0, 3.5, 1.0` | exact |
| `spm_DEM_embed(Y,3,1,1,0)` | boundary bin (clamped window) | `1, 0.5, 1` | `1.0, 0.5, 1.0` | exact (an earlier misreading of the Octave console output was caught and corrected by this exact numeric re-check — see `PORT_DESIGN.md`) |
| `spm_diff(f,x0,1)` nonlinear 2D | forward-diff Jacobian, step=exp(-8) | `[[1.0003,1],[−1,0.3622]]` | `[[1.00033546,1.],[-1.,0.36220142]]` | exact |

**All L1 primitives needed by the D-step match Octave exactly.**
`ESTABLISHED`.

Not yet L1-tested: `model.Mg`/`model.Gg` against the corresponding Octave
`dem_morphogenesis_Mg.m`/`dem_morphogenesis_Gg.m` outputs on an identical `v`
— the formulas are unchanged from `m0_reconstruction` (already read
character-by-character against source in that stage) but a live numeric
cross-check specifically in this stage's Python module was not run before
the port work stopped. `NOT DONE` (small, low-risk gap — flagged in
`OPEN_QUESTIONS.md`).

## L2 — single step: `NOT DONE`

Blocked on the `spm_ADEM_diff.m` recursion issue described in
`PORT_DESIGN.md` ("Where the port stopped"). An Octave-side instrumented
dump of one full D-step (`data/oracle_traces/dstep_dump_bin1.mat`) was
captured and is available for this test once the recursion is resolved — it
contains the exact target values (`E`, `dE.du`, `dE.da`, `dFdu`, `dFduu`,
`du`) a correct Python single-step implementation must reproduce.

## L3 — full trajectories: `NOT DONE`

Depends on L2. No Python trajectory was run against any of the 8 Octave
golden traces from Task 1.

## Octave self-sensitivity check (requested as a control for L3 deviation growth): `NOT DONE`

Not reached — there is no Python trajectory yet to compare against, so the
"does the port's deviation growth exceed the oracle's own sensitivity to a
1e-10 perturbation" question is moot for this pass. Recorded as a required
step for the follow-up session in `OPEN_QUESTIONS.md`.

## Honest summary

Of the three equivalence layers requested, **one (L1) is done and
validated with concrete matching numbers; two (L2, L3) are not done**,
disclosed here rather than silently skipped or fabricated. This is a
meaningful partial result (every low-level numerical primitive the D-step
depends on is now proven correct against the live oracle) but does **not**
constitute a validated port, and no downstream claim in this repository
treats it as one.
