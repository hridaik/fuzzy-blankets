# PORT_DESIGN_UPDATE.md — Part B: the `u.v{i}` recursion, resolved

## Status: **RESOLVED, `ESTABLISHED`, with dump evidence.**

## The question (from m0b `PORT_DESIGN.md`)

`spm_ADEM_diff.m` contains, for generalized orders `i=2..n`:
```
u.v{i} = dg.dv*u.v{i} + dg.dx*u.x{i} + dg.da*u.a{i} + u.z{i};
```
with `u.v{i}` appearing on both sides. m0b could not determine, from static
reading alone, what value `u.v{i}` holds on the right-hand side at the
moment this line executes.

## Resolution (two independent parts)

### Part 1 — `pu.v` is never reset inside the D-step loop; it persists across bins

Direct read of `spm_ADEM.m`:
- **Before** the `for iY=1:nY` loop (lines ~335-345,
  `sources/spm12/spm_ADEM.m`): `pu.v = cell(n,1); [pu.v{:}] = deal(sparse(gr,1));`
  then **only** `pu.v{1} = spm_vec({G.v})` is overwritten — i.e. **all
  higher generalized orders of `pu.v` start at exactly zero**, `ESTABLISHED`.
- **Inside** the loop (line ~447-453): each bin freshly overwrites
  `pu.z`, `pu.w`, `pu.a` (via `spm_DEM_embed`) but **does not touch `pu.v`
  at all** before calling `[pu,dg,df] = spm_ADEM_diff(G,pu);` — so
  `spm_ADEM_diff` receives, as input, exactly whatever `pu.v` held at the
  **end of the previous bin's D-step**. `ESTABLISHED` by direct read.

### Part 2 — empirically confirmed, and a further, decisive simplification found

Instrumented `oracle/spm_ADEM_b1.m` (a disclosed patched copy of
`spm_ADEM.m`, diff: dump statements only, no logic changed — see the file's
own header comment) dumps `pu.v` immediately before and after
`spm_ADEM_diff`, and again after the later `spm_dx` local-linearization
update, for bins 1-3 of the vanilla-8 config. Result
(`data/oracle_traces/b1_dump.mat`):

| | bin 1 in | bin 1 out (spm_ADEM_diff) | bin 1 after spm_dx | bin 2 in |
|---|---|---|---|---|
| order 2 (norm) | 0 | 0 | 0 | 0 |
| order 3 (norm) | 0 | 0 | 0 | 0 |

| | bin 2 out (spm_ADEM_diff) | bin 2 after spm_dx | bin 3 in |
|---|---|---|---|
| order 2 | 0.6709 | 0.2732 | **0.2732 — exact match** |
| order 3 | 1.3418 | 1.4079 | **1.4079 — exact match** |

**`bin (k+1)`'s input to `spm_ADEM_diff` equals `bin k`'s value *after the
later `spm_dx` update*, not `spm_ADEM_diff`'s own output** — bitwise
identical across all tested values. This means `pu.v{i}` (`i>=2`) is
updated **twice** per bin: (1) `spm_ADEM_diff` computes a "prediction" from
the current Jacobians + embedded noise/action derivatives (using the
*previous bin's post-correction* value as its right-hand-side input — plain
MATLAB/Octave value-copy semantics, exactly as the task hypothesized), and
(2) the later joint local-linearization `spm_dx` step applies a **second,
pure-shift correction** to the same variable (via the `Dp*spm_vec(p)` block
of `dFdu`, which is a bookkeeping/consistency term, not a free-energy
gradient — `p={pu.v,pu.x,pu.z,pu.w}` gets no `dVd*` gradient term at all,
only `q={qu.x,qu.v,qu.u,qu.a}` does). **`ESTABLISHED` from dump evidence,
not merely re-derived.**

### The decisive simplification: `dg.dv ≡ 0` for this model

The same dump captured the actual Jacobian `dg.dv` (81x81) computed inside
`spm_ADEM_diff` at bin 1: **identically zero**, every entry. This is because
`dem_morphogenesis_Gg.m`'s process mapping **does not use its `v` argument
at all** (`Gg(x,v,a,P)` ignores `v` — confirmed by reading the function body,
MODEL_SPEC.md from m0). Consequently **the recursion's self-referential
term `dg.dv*u.v{i}` is always exactly zero, regardless of what `u.v{i}`
held** — so, for *this specific model*, the recursion is not actually
self-referential in effect: `u.v{i} = dg.da*u.a{i} + u.z{i}` for `i>=2`,
full stop. `ESTABLISHED` (dumped matrix, all entries `0.0`).

**This resolves the recursion completely and removes the risk the task
flagged (i) NumPy aliasing and (ii) value-vs-reference semantics**: since
the term that would require careful "old value" bookkeeping has zero
coefficient, the Python port for `i>=2` needs no explicit `u.v{i}`
carry-over logic at all — it can compute each generalized order directly
from `dg.da @ pu.a[i] + pu.z[i]` each bin, with **no dependency on any
previous value**. (The general-case fix, for a future model where
`dg.dv != 0`, is still documented: read `u.v{i}` as it stood at loop entry
— Octave/MATLAB copy-on-assign semantics — before this statement executes,
i.e. cache the pre-update value explicitly in Python rather than relying on
in-place mutation order, since NumPy in-place ops can alias.)

## B3 — action gradients use the PROCESS Jacobian, confirmed

`spm_ADEM.m`: `dE.da = dE.dv*((dgda + dgdx*Dfdx*dfda).*R);` where
`dgda = kron(spm_speye(n,1,0), dg.da)` and **`dg.da` is the output of
`spm_ADEM_diff(G,pu)`** — i.e. the **generative-process's** (`G`) Jacobian,
not the model's (`M`). `ESTABLISHED` both from this source line and from
the dumped `dg.da` (81x48) matrix's structure (rows 1-2 show an identity
block matching `d(g.x)/d(a.x) = I`, exactly the process's own known
`Gg` mapping — MODEL_SPEC.md m0). Confirmed, not merely asserted.

## Indexing/ordering conventions used throughout the Python port (per B2's checklist)

- **Column-major flattening**: every `spm_vec`-equivalent in the Python port
  uses `.ravel(order="F")` (already established and tested in m0b's
  `model.py`/`spm_port.py`).
- **1-based vs 0-based**: all bin indices `iY` (1-based in Octave) are
  converted to Python's 0-based loop index `b` via `iY = b + 1`
  consistently; `t = iY/nY = (b+1)/N`, matching m0/m0b.
- **No in-place aliasing**: the Python D-step (`code/dstep.py`) never
  mutates a NumPy array that a *previous* bin's state still references —
  every per-bin update creates a **new** array (`.copy()`/fresh
  `np.concatenate`) rather than assigning into a slice of a shared buffer,
  precisely to avoid the aliasing risk the task flagged, even though `B2`'s
  finding above shows it is moot for `pu.v{i>=2}` specifically (it still
  matters for `pu.v{1}`, `qu.v`, `qu.a`, which persist bin-to-bin with
  nonzero coupling).
