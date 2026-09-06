# PORT_VALIDATION.md — Stage 6 (flock) Phase 1A

## 0. What could and could not be checked

No MATLAB or Octave installation is available in this environment (`which matlab
octave octave-cli` returns nothing). Per the task brief, this is not a blocking
condition: the port is validated via (a) direct hand-derivation from the MATLAB
source (already the basis of METHODS_AUDIT.md), (b) deterministic/algebraic
cross-checks that do not require running the original code, (c) internal
consistency and reproducibility tests within the Python port, and (d)
distributional/qualitative comparison against the paper's reported baseline
behavior (order-parameter/heading-alignment emergence). Bit-identical trajectory
matching against MATLAB was never attempted or claimed, consistent with the task
brief ("do not require identical random trajectories... instead validate
distributions and deterministic calculations").

## 1. Structural simplification discovered during the port (verified analytically)

While translating `active_inference_bird_control.m`'s expected-free-energy loop,
it became apparent that **G(u) does not depend on the bird's own current belief
about its heading**. Proof sketch: `B{1}(:,:,u)` (Eq. 5) has every column equal
(the transition to action `u` doesn't depend on the previous state — this is a
direct, verified reading of `spm_softmax(repmat(ucell,1,nu), precB)`, which
replicates the SAME one-hot column `nu` times before taking the softmax). Hence
for ANY prior distribution `x` (a probability vector), `B(:,:,u) @ x` equals that
one fixed column, independent of `x`. The upstream code's expected-free-energy
rollout (`active_inference_bird_control_t.m` lines ~148-156) starts from
`x = mdp.X{f}(:,t)` and immediately applies `x = B(:,:,u) @ x` before using `x`
for anything — so the specific value of `mdp.X{f}(:,t)` is provably irrelevant to
every subsequent quantity in the EFE computation (ambiguity, risk, `G`). A second
consequence: the upstream code's "predictive-observation" resample (RNG draw #3
in METHODS_AUDIT.md section 12) only ever feeds back into `mdp.X{f}(:,t+1)`
(belief bookkeeping) and `mdp.vFE` (a diagnostic scalar never fed back into
action selection or state transition), so it cannot affect the physically
sampled heading trajectory `mdp.s(1,:)` in this specific model.

**Validation of this claim**: `tests/test_active_inference.py::
test_G_independent_of_own_current_heading` constructs two states differing ONLY
in a bird's own current heading (holding its neighbors' headings fixed) and
confirms `compute_G` returns identical values for both. This passed. This
justifies implementing only 2 RNG draws/bird/timestep (action, next-heading)
instead of 3, and precomputing `G` as an 8(slot) x 4(action) x 4(neighbor
heading) lookup table rather than re-deriving beliefs every step — a genuine
performance and correctness simplification, not an approximation of an unknown
quantity. This is flagged prominently because it is exactly the kind of
"unexpected result" the task brief asks not to hide, even though in this case it
turned out to be a real property of the model rather than a bug.

## 2. Deterministic / algebraic checks performed (no MATLAB required)

| # | Check | Result |
|---|---|---|
| 1 | Neighbor sets for hand-checked lattice positions (corner=3 neighbors, edge=5, interior=8; corner bird 1's neighbors are {2,11,12} by hand MATLAB arithmetic) | PASS — `tests/test_lattice.py` |
| 2 | Neighbor relation symmetry (i in neighbors(j) iff j in neighbors(i)) | PASS |
| 3 | Total edge count matches the free-boundary-grid combinatorial formula `2L(L-1) + 2(L-1)^2` for L=10 | PASS |
| 4 | Column-major row/col <-> linear-index roundtrip matches MATLAB's `ind2sub`/`sub2ind` convention | PASS |
| 5 | `R(i,j)` base matrix diagonal = `vm`, opposite-pair off-diagonal = `-fc`, orthogonal-pair = `0`, matching Eq. 4's dot-product structure | PASS |
| 6 | Per-slot override values (`-ca` at the 8 geometry-specific `(o,s)` entries), transcribed 1:1 from `compAexceps`'s switch-case, for the "top" slot spot-checked against the matrix by hand | PASS |
| 7 | `B(:,:,u)` — every column identical (Eq. 5's independence from previous state) | PASS |
| 8 | `B(:,:,u)` peaked at the commanded action `u` under `precB=15` (>0.9 mass) | PASS |
| 9 | Neighbor likelihood matrices are column-stochastic (valid `P(sigma^j|z^i)`) | PASS |
| 10 | Policy posterior (`ut`) sums to 1 for arbitrary `G` | PASS |
| 11 | Adjacency construction on a hand-built 4-bird, 2-block heading history reproduces the exact expected weighted-count matrix | PASS |
| 12 | Self-loops (diagonal = `TW`) are numerically inert for the Laplacian `L = D - A` (verified on a random 12-node, 5-step window: `L` identical with/without the diagonal) | PASS |
| 13 | A perfectly 2-block-separated (no cross-agreement) heading history yields a disconnected graph: >= 2 near-zero Laplacian eigenvalues | PASS |
| 14 | `classify()`'s fixed-threshold / percentile logic reproduces a hand-worked 10-node example (explicit top/bottom values -> correct `core1`/`core2`; explicit `|y2|<0.05` values -> correct `boundary`) | PASS |
| 15 | `align_to_reference` swap rule (raw overlap-count comparison, as literally coded upstream, not Jaccard) matches a hand-worked case | PASS |
| 16 | Reproducibility: identical seed -> bit-identical simulation trajectory across two independent calls; different seed -> different trajectory | PASS |
| 17 | Common-random-numbers structure: natural action is computed and recorded identically whether or not an override is later applied; only `applied_action`/`z_new` differ | PASS (`test_intervention_overrides_applied_action_but_not_natural`) |
| 18 | Forced-pulse sanity: forcing 3 birds toward a target heading for 10 steps leaves them at that heading with high probability at the end of the pulse | PASS |

All 25 tests pass (`pytest tests/ -q` -> `25 passed`). Test files:
`tests/test_lattice.py`, `tests/test_model.py`, `tests/test_spectral.py`,
`tests/test_active_inference.py`.

## 3. Population-level qualitative comparison against the paper / original code

The paper and the released `flocking_AIF_simulation.m` both describe emergent
alignment: birds gradually align their headings from a random initial
configuration (Fig. 1A: 8 steps, visibly converging by eye). The Python port
reproduces this qualitatively: starting from `pu` = uniform random headings
(polarization/order-parameter `Phi` near 0), a single `nn=100` run reaches
`Phi=1` (perfect global alignment) by `t≈20` and remains there
(`python/analysis/baseline_characterization.py` and the ad hoc check recorded
below). This matches the qualitative direction and rough timescale (order 10-20
steps for 100 birds on a 10x10 grid) of Fig. 1A's 8-step snapshot sequence,
though the paper does not report a precise convergence-time number to compare
against quantitatively — this is a qualitative, not quantitative, validation.

**A genuine and important finding surfaced by this check** (not an artifact of
the port, but a property of the model + Fiedler method interaction — see
`data/baseline_v1/` and PROTOCOL_V1.md for the full quantitative
characterization): once the flock reaches full polarization (`Phi=1`, i.e. every
bird shares one heading), the heading-agreement graph over any trailing window
becomes a **complete graph with uniform edge weight**, whose Laplacian has an
`(nn-1)`-fold degenerate top eigenvalue and, correspondingly, `lambda2 ≈ lambda3`
generically (eigengap ≈ 0). The Fiedler vector is then arbitrary within a large
degenerate eigenspace, and the resulting "macro-agent" partition is not
meaningful. This is exactly the "Fiedler instability when eigengap is near zero"
condition the task brief pre-warns about, and it is not a rare edge case here —
it is the **generic long-run state** of this particular flocking model, because
the dynamics are strongly self-reinforcing (once aligned, essentially locked).
**Consequence for the protocol**: candidate-flock identification (Phase 2A) must
target the *transient* alignment window (moderate, not-yet-complete polarization)
where the Fiedler decomposition is still informative, not the eventual
steady state. This is documented as a frozen, pre-control design constraint in
PROTOCOL_V1.md, derived entirely from baseline (uncontrolled) runs.

## 3a. A definitional bug caught by an anomalous control result (Phase 3A)

`tests/test_rotation.py` and `flock_sim.model.ROT_CW`/`ROT_CCW` document a real
bug caught during Phase 3A, not during unit testing: the upstream heading-state
order `{up,down,left,right}` is not a rotational cycle, so the task's "adjacent
cardinal heading" cannot be computed as `(h0+1) mod 4` (for 2 of the 4 possible
`h0` values this silently computes the *opposite* heading instead of a 90-degree
turn). It was caught because the canonical snapshot's positive/negative control
sweep produced a 32% spontaneous "success" rate against an aggregate-baseline
expectation of ~7% — investigated immediately rather than proceeding, per the
task brief's "unexpected results should first trigger deterministic unit
checks" guidance. See PROTOCOL_V1.md section 1a for the full account, including
that the fix was applied and both the baseline ensemble and canonical snapshot
were regenerated **before** any sparse-actuator search (Phase 4/5) began. The
pre-fix baseline data is preserved (not deleted) under
`data/baseline_v1_buggy_naive_hstar_DO_NOT_USE/` for the audit trail.

## 4. Gate A verdict

**No material, unexplained mismatch was found.** The one substantive discrepancy
uncovered (Fiedler degeneracy at full polarization) is a discovered *scientific*
property of the coupled model+method, not a port defect — it is independently
verifiable from the paper's own stated math (a complete graph's Laplacian is
`c(nI - J)`, whose spectrum is elementary), and does not depend on any
MATLAB-vs-Python discrepancy. Proceeding to Phase 2.
