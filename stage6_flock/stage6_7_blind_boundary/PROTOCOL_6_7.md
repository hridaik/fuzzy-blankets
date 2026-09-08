# PROTOCOL_6_7

Frozen after `tests/test_no_topology_leakage.py` passed (16/16), the timing
pilot (`logs/timing_pilot.json`, `code/run_timing_pilot.py`) ran, and the
edge-stability thresholds were chosen from seed 2's blind bootstrap
statistics alone. Written before `code/oracle_validation.py` was run on the
full 300-candidate panel. `configs/protocol_6_7.yaml` is the machine-readable
twin of this document; `configs/protocol_6_7.yaml.sha256` freezes its hash.

## 1. The firewall

> **Inference code may see trajectories and interventions, but not topology.**

Enforced by `tests/test_no_topology_leakage.py` against
`code/{blind_cache,directed_graph_inference,graph_bootstrap,
predictive_boundary,causal_discovery}.py`: no import of `flock_sim.lattice`,
`flock_sim.spectral`, `common_v2`, `common_66`, `common_67`,
`dynamical_shell`, `windowed_data`, `archetypes`, `intervention_api`,
`oracle_validation`, or `candidate_panel`; no reference to identifiers like
`Lattice`, `neighbor_ids`, `one_hop_neighbors`, `structural_shell`,
`graph_distance_from_set`, `InterventionOracle`; no function parameter named
like a lattice/neighbour/graph-distance object. A runtime seal additionally
runs the full blind pipeline on synthetic data and asserts no `Lattice`
instance appears anywhere in the results. `code/oracle_validation.py` is the
only module in this stage permitted to import the lattice for scientific
conclusions, and it is only ever invoked after every `Bhat^pred`/`Bhat^causal`
decision is written to disk.

## 2. Reused, unmodified

See `configs/protocol_6_7.yaml`'s `reused_unmodified_from_stage6{,_5,_6}`
blocks. Highlights: the simulator (`python/flock_sim/*`), the nodewise
multinomial logistic-regression estimator and its frozen hyperparameters
(`solver=liblinear, penalty=l2, C=1.0, max_iter=200`,
`stage6_5/boundary_inference/code/nodewise_model.py`), greedy forward
selection (`stage6_5/boundary_inference/code/greedy_selection.py`), the exact
counterfactual propagator
(`stage6_5/refinement/causal_redundancy/code/exact_intervention.py`), Stage
6.6's archetype-condition replicate generator
(`stage6_6_collective_landscape/code/{archetypes,windowed_data}.py`), and
Stage 6.6's own frozen 5000-candidate-per-snapshot data (read-only, used only
to build the 20-candidate panel).

## 3. Primary objects

| quantity | value |
|---|---|
| `W` (window) | 10 |
| `R` (replicates) | 100 |
| primary seeds | 2, 3, 4 |
| conditions | no_control, shell_only, same_direction, opposite, disordered |
| snapshots | 15 (3 seeds x 5 conditions) |
| candidates/snapshot | 20 |
| total primary candidates | 300 |
| train/val/test split | 60/20/20, replicate-level, split_seed=0 |

## 4. Directed graph inference (task brief section 4)

For every target bird `i` (0..99): fit the full L2-regularized multinomial
logistic model conditioning on all 99 other birds' one-hot current headings
(own heading included via `I0=[i]`); rank sources by summed `|coefficient|`
mass on their 4-column one-hot block across all fitted class rows; take the
top `shortlist_k=25`; for each shortlisted source, refit with it removed and
compute `Delta_{i<-j} = ell_i^{(-j)} - ell_i^{(full)}`. Non-shortlisted pairs
get `Delta=0` exactly (disclosed approximation, not silently omitted).

## 5. Bootstrap edge stability (task brief section 5)

`B_boot=30` trajectory(=replicate)-level bootstrap resamples of the entire
graph-inference procedure per snapshot. Per edge: `mean_gain`, `median_gain`,
`selection_frequency` (fraction of boots with `Delta>0`), `sign_stability`
(`max(#positive,#negative)/B_boot`).

**Frozen rule**: `stable(i<-j) <=> selection_frequency >= 0.5 AND
sign_stability >= 0.7`. Developed by examining ONLY the blind
(selection_frequency, sign_stability) joint histogram over every edge ever
shortlisted at least once, on seed 2's `no_control` snapshot (1407/9900
edges ever shortlisted; a visible cluster at `selection_frequency>=0.9`
[176 edges] separated from a long low-frequency tail) — the true graph was
never consulted for this choice. Applied unchanged to every snapshot,
including seed 4 and every condition, and never re-tuned after
`oracle_validation.py` ran.

## 6. Predictive boundary construction (task brief section 6)

`Shat^pred(I) = {j not in I : exists i in I, stable(i<-j) with Delta_{i<-j}>0}`
(pure lookup, no geometry). Greedy conditional selection from this pool via
`stage6_5/boundary_inference/code/greedy_selection.py:greedy_forward_select`,
stopping when the validation excess-over-full loss reaches `delta_tol=0.01`
nats or the best remaining marginal gain falls below `min_gain=0.002`, or
`|B|=K_max=12` (never padded to that size).

## 7. Primary predictive criterion (task brief section 7)

`Delta-ell(Bhat) = ell(M_{I,Bhat}) - ell(M_all)`, computed on the untouched
test split. `delta_pred=0.01` nats/bird-step (same value as the greedy
stopping tolerance, task brief's own boxed constant) is the predictive-
sufficiency threshold; continuous loss is reported regardless of pass/fail.

## 8. Causal interface identification (task brief sections 12-14)

The exact counterfactual propagator
(`stage6_5/refinement/causal_redundancy/code/exact_intervention.py`) is
wrapped by `code/intervention_api.py:InterventionOracle`, exposing only
`D_do_joint` and the per-target-bird `C_{j->i}^do` breakdown (never
`is_neighbor` or any topology-derived field). For each panel candidate,
`N_STATES_PER_CANDIDATE=15` observed states (sampled from that snapshot's own
pooled window data) x every exterior bird x every alternative heading are
tested; `D_j^do` is the sample mean; a bootstrap (`CI_N_BOOT=1000`,
`alpha=0.05`, resampling the already-collected per-state KL values, no new
oracle calls) gives a CI. `Bhat^causal(I) = {j : CI lower bound > 0}`.

## 9. Oracle validation (task brief section 9) — the only topology-aware step

`code/oracle_validation.py` computes `B^D(I) = one_hop_neighbors(I)` and
precision/recall/Jaccard for both `Bhat^pred` and `Bhat^causal`, strictly
after every inference decision above is frozen. Never used to retroactively
adjust `shortlist_k`, `tau_freq`/`tau_sign`, `delta_tol`/`min_gain`, or
`N_STATES_PER_CANDIDATE`.

## 10. Sample-efficiency sweep (task brief section 11) — scope reduction

`R in {5,10,20,50,100}`, `W=10` fixed, for established `I0` + 5 more
panel candidates per seed (`no_control` condition). Uses the single
(non-bootstrapped) directed graph with raw `Delta>0` as the candidate-pool
criterion — bootstrapping at `R<=20` is not statistically meaningful (a 60%
split of 5 replicates is 3 training replicates). This reduction applies only
to the sweep, never to the primary panel's `B_boot=30` numbers.

## 11. Control diagnostic (task brief section 16)

One fixed-budget comparison per seed's canonical `I0` (`no_control`
condition): full `Bhat^pred`, full `Bhat^causal`, a matched-budget random
draw per arm, and oracle `B^D`, evaluated via
`v2_interface_control/code/common_v2.py:evaluate_arm` unmodified
(`n_replicates=30`, the existing target-heading task and frozen `T_u=20`
control horizon). Diagnostic only — no controller optimization.
