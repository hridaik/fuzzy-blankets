# EQUIVALENCE_REPORT.md — Part B, invoking the B5 timebox

## Top-line: L1 done (machine precision). L2 mismatch found and localized precisely. Per B5, Part B stops here; Part D (fallback engine) is the path forward for Parts C/E.

## L1 — function level: `ESTABLISHED`

| Check | Result |
|---|---|
| `Mg`/`Gg` vs. live Octave, 20 random inputs (A5) | max relative deviation `1.176e-15` / `2.907e-16` — exact to machine precision |
| Sensory error `E[:80] = Gg(a0) - Mg(v0)` vs. Octave's dumped `E[:80]` at bin 1 | max abs deviation `3.33e-16` — exact |
| Prior error `E[80:144] = qu.v[0]` vs. Octave's dumped value | exact, `0.0` deviation |
| Order-2/3 error blocks (both zero at bin 1) | exact match, both zero |
| `spm_DEM_R`, `spm_dx`, `spm_DEM_embed`, forward-diff Jacobian | all exact (carried over from m0b, re-confirmed) |

**Every static, non-iterative quantity the D-step depends on is reproduced
exactly.** This is real, verified progress beyond m0b.

## The `u.v{i}` recursion: fully resolved (see `PORT_DESIGN_UPDATE.md`)

Confirmed via instrumented dump (`oracle/spm_ADEM_b1.m`,
`data/oracle_traces/b1_dump.mat`) that `pu.v{i}` persists across bins
(predict via `spm_ADEM_diff`, correct via the later `spm_dx` joint update),
and that `dg.dv ≡ 0` identically for this model (`Gg` ignores its `v`
argument) — which means the recursion has **zero effective dependence on
its own previous value** for this specific model. `ESTABLISHED`, dump-backed.

## B3 — action gradients use the process Jacobian: `ESTABLISHED`

`dE.da` is built from `dg.da`, the output of `spm_ADEM_diff(G,pu)` (process
side), confirmed both from source (`dE.da = dE.dv*((dgda + ...).*R)`, with
`dgda` derived from `dg.da`) and from the dumped `dg.da` matrix's structure
(identity block for `d(g.x)/d(a.x)`).

## L2 — single step: mismatch found, precisely localized

Constructed a from-scratch Python D-step (`code/dstep.py`) using the
established L1 pieces, but taking one **undisclosed-until-now
simplification**: rather than solving `spm_ADEM`'s full joint
`dFduu` system (790-dim for this config, coupling `{pu.v, pu.z, qu.v, qu.a}`
in one matrix-exponential local-linearization step), it solves **separate,
block-decoupled Gauss-Newton steps** for `qu.v[0]`, `qu.v[1]`, and `qu.a`
independently (each via its own small `spm_dx` call), justified by the fact
that `pu.v`'s own gradient contribution is zero (dg.dv=0) so it needn't be
in the joint solve — but this reasoning **does not extend to decoupling
`qu.v` from `qu.a`**, which the real `dFduu` couples through the
`dVduv`/`dVdua`/`dVdav`/`dVdau` cross-blocks (built from `dE.du`, `dE.da`
together against the *same* `iS`-weighted quadratic form).

**Result, tested directly against Octave's bin-1 dump**
(`../m0b_reference_port/data/oracle_traces/dstep_dump_bin1.mat`,
`dump_pre`/`dump_post`):

| Quantity | Octave (ground truth) | This port | Match? |
|---|---|---|---|
| `Δqu.v[order1]` norm | 1.8437 | 0.2709 | **No — ~6.8x too small** |
| `Δqu.v[order2]` norm | 0.0 (exact) | not separately isolated in this test | — |
| `Δqu.a` norm | 1.0962 | 0.5516 | **No — ~2x too small, and per-component signs differ** (e.g. first component: Octave `+0.446`, port `-0.166`) |

**This is a real, disclosed failure, not a rounding difference.** The sign
flip on `Δqu.a`'s first component in particular indicates the block-decoupled
approximation is missing a genuine coupling term, not merely using a
different step size.

## Where exactly the mismatch first appears (per B5's requirement)

**Statement**: the joint local-linearization update,
`du = spm_dx(dFduu, dFdu, dt)` (`spm_ADEM.m`, ~line 594) — specifically, the
cross-coupling sub-blocks `dVduv`, `dVdua`, `dVdav`, `dVdau` of `dFduu`,
which this port's `code/dstep.py` never constructs (it constructs only the
block-diagonal `H_v0`, `H_v1`, `H_a` pieces).
**Bin**: 1 (the very first D-step; the mismatch is present from the start,
not an accumulating drift).
**Variable**: `qu.v` (order 1) and `qu.a`.
**Magnitude**: update norms low by a factor of ~2-7x, with at least one
sign disagreement in `qu.a`.

## Decision: invoke B5's timebox

Per the task's explicit instruction: *"If B1-B4 are not complete after a
genuine instrumented attempt, stop Part B, document exactly where the
mismatch first appears..., and proceed to Part D's fallback engine."*
That condition is met. A genuine, well-instrumented attempt was made,
real (and reusable) progress was achieved (L1 exact; the `u.v{i}` recursion
fully resolved; B3 confirmed), and the specific remaining gap (constructing
the true 790-dim joint `dFduu`, including the `dVduv`/`dVdua`/`dVdav`/`dVdau`
cross-blocks and the `Dp`/`Dq` shift-operator bookkeeping for the full
`{p,q}` state stack) is precisely identified for a future session, rather
than being shipped as an uncertain guess. **Parts C and E proceed using
the Octave oracle directly via Part D's fallback engine, not this
incomplete Python D-step.**

## L3 — full trajectories

`NOT DONE` — depends on L2, which did not pass.

## A4 chaos-baseline interpretation (for when L2/L3 are revisited)

See `ORACLE_FACTS.md` A4 for the Octave self-sensitivity numbers. Once L2
passes, L3 deviation growth should be compared against those figures before
attributing any growth to the port, per the task's instruction — not
applicable yet since L2 has not passed.
