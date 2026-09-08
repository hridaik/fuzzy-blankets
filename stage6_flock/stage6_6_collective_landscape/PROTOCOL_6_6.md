# PROTOCOL_6_6.md — Stage 6.6: Collective Landscape

Frozen **after** the controlled-archetype sanity check (task brief section
11; `data/archetype_trajectories.json`, seeds 2/3/4, conditions A-E, the
`f_E` sweep) ran and was inspected qualitatively (see
`METRIC_VALIDATION.md`), and **before** the full 5000-candidate-per-snapshot
landscape used by the interactive demo was generated. This ordering matches
`PLAN.md`'s stated freeze point and the Stage 6.5 convention
(`../stage6_5/PROTOCOL_6_5.md`).

`configs/protocol_6_6.yaml` (SHA-256:
`7bfe7c2e8141fe442ad30bd0d8ad90ef470045de11cc790742c7b5e79d08b3d4`,
`configs/protocol_6_6.yaml.sha256`) is the
machine-readable version of everything below; nothing in that file changes
after this hash is recorded.

## 1. Reused, unmodified

See `PLAN.md` "Reused, unmodified" and the yaml's
`reused_unmodified_from_stage6` / `reused_unmodified_from_stage6_5` blocks
for the exact file:function citations. In particular: the control hook is
`flock_sim.interventions.make_pulse`, acting through the same
`applied_action` override inside `flock_sim.active_inference.step` that
V1-V3 used (never a direct `z_new` overwrite — verified in
`tests/test_control.py::test_control_hook_overrides_applied_action_not_z_new_directly`);
the predictive model is `stage6_5`'s `NodewiseModel` at its frozen
hyperparameters (`C=1.0, penalty=l2, solver=liblinear, max_iter=200`).

## 2. Primary objects

`k=|I|=20`, `K=12` (boundary budget), `W=10` (window), `R=100` (replicates),
seeds `{2,3,4}`. Every seed's reference `I0` is exactly size 20:

| seed | raw spectral size | resize |
|---|---|---|
| 2 | 20 | none (canonical snapshot) |
| 3 | 19 | +1 (grown via `resize_to_k`) |
| 4 | 20 | none |

## 3. Window dataset

Snapshot timepoint: `t = t0 + T_u` (control-end), per task brief section 25
("do not delay the core implementation waiting for all timepoints"). Window
= the trailing `W=10` states ending at `t` (9 transitions), pooled over
`R=100` common-random-number replicates that all branch from the same
`z_t0` and share the condition's intervention profile, differing only in
RNG seed (`seed_offset + r`) — mirrors
`v2_interface_control/code/common_v2.py:evaluate_arm`'s pairing scheme.
Trajectory(replicate)-level train/val split: 70/30, `split_seed=0`
(`code/windowed_data.py:TRAIN_FRACTION`). No timestep is ever split across
train and val within the same replicate, and no observation after `t` is
ever read.

## 4. Predictive mask cache

For bird `i` and neighbour-subset mask `m ⊆ neighbours(i)`,
`subset_loss[i,m]` is the held-out log-loss of a `NodewiseModel(I0=[i],
cond_extra=sorted(m))` fit on the window's train split and evaluated on its
val split — bird `i`'s own current state is always in the conditioning set
by construction (`I0=[i]`). Cache key `(i, frozenset(m))`; cost is bounded
by `sum_i 2^deg(i)` over touched birds, not by candidate count (confirmed
empirically: `code/run_landscape.py` pilot runs at 100/600/1500 candidates
on seed 2's natural regime needed 8183/15745/17210 unique fits respectively
— visibly saturating, not scaling linearly with the roughly 6x/15x
candidate-count increase). `G_i = ell_i(mask_B) - ell_i(mask_IB)`,
`L_i = ell_i(mask_IB) - ell_i(mask_full)`, raw (only machine-epsilon
negatives clamped, tol `1e-9`) — see
`tests/test_predictive_metrics.py::test_negative_finite_sample_estimates_are_not_zero_clamped`.

## 5. Candidate generation

Target 5000 unique connected `k=20` candidates per snapshot, mixed from five
methods (region-growing 35%, MCMC boundary-swap 25%, perturb-`I0` 15%,
high-coherence-weighted region-growing 15%, spectral-resized 10%), always
including the seed's reference `I0` explicitly
(`candidate_source=seed_reference_I0`). Spectral bases (`core1_nodes`/
`core2_nodes` from `flock_sim.spectral.analyze_window`) are reduced to their
largest connected component before resizing, since a Fiedler bipartition is
a graph cut and need not be spatially contiguous — discovered as a real bug
during test-writing (`tests/test_geometry.py::test_candidates_are_moore_connected`
failed against the first implementation; fixed in
`code/common_66.py:largest_connected_component` before any landscape data
was generated for this frozen protocol).

## 6. Boundary search

`B` chosen only from `I`'s structural shell `S(I)` (task brief section 10's
explicit "known shell as candidate pool" allowance for a
collective-*characterization*, not observational-boundary-discovery, stage).
Greedy forward selection minimizing held-out `L_I`, then up to 2 passes of
one-swap local refinement. `|B| = min(K, |S(I)|)`; when `|S(I)| <= K` the
full shell is used directly with no search (and `L_I` is then exactly `0`
by construction — every neighbour of every interior bird is either in `I`
or in `S(I)=B`, so `mask_IB(i) == mask_full(i)` identically; verified in
`tests/test_predictive_metrics.py::test_full_structural_shell_gives_exactly_zero_leakage`).

## 7. Archetype conditions and the `f_E` budget sweep

Conditions `{no_control, shell_only, same_direction, opposite, disordered}`
correspond to task brief archetypes A-E. Exterior control nodes are chosen
from `E_near(I)` (the second Moore-graph ring) via deterministic farthest-
point (max-min graph-distance) selection, never concentrated in one patch.
The disordered condition uses a deterministic balanced rotating schedule
`heading(rank, t) = (rank + t) mod 4`, not a random draw. The geometric
opposite heading is computed via `UV4` vector negation (verified equal to
`rotate_cw` applied twice, and verified to disagree with the naive
`(h+2)%4` for every `h` — see `tests/test_control.py`). `f_E ∈
{0.25,0.50,0.75,1.00}` swept for `same_direction`/`opposite`/`disordered`;
`no_control`/`shell_only` have no exterior actuation (`f_E` not applicable,
recorded as `1.00`/`0.00` placeholders where a field is required).

## 8. Pareto filter

Nondominated set across `(C, G, -L, D)` (all maximized), computed for every
snapshot and attached per-candidate as `is_pareto`, but used only as an
optional, default-OFF visualization filter — never to select candidates or
drive any conclusion in `RESULTS_6_6.md`.

## 9. Freeze statement

Everything above was fixed before `code/run_all_snapshots.py` (the full
5000-candidate-per-snapshot generation for the demo) was launched. The
computational-budget outcome (whether 5000 was reached for every snapshot,
and actual wall-clock costs) is reported in `RESULTS_6_6.md` and
`data/snapshot_manifest.json`, not adjusted here after the fact.
