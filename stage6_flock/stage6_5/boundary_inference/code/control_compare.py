"""EVALUATION-SIDE (Part 2). Builds a controller from the INFERRED incidence
graph (Ghat, from graph_inference.py -- itself inference-side and lattice-
free) using the frozen V3 q-fold multicover objective (q=2, gamma=0.5,
v3_refinement/configs/protocol_v3.yaml), and compares Oracle-B^D / Inferred-
B_hat / Fiedler-B^F / random-matched-budget controllers by actually running
the simulator (which requires the lattice -- hence evaluation-side). The
control RULE itself is not retuned here (Part 2.2's requirement); q and
gamma are imported as frozen constants, not searched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))

from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from common_v2 import T_U, T_R  # noqa: E402

FROZEN_Q = 2
FROZEN_GAMMA = 0.5  # v3_refinement/configs/protocol_v3.yaml: interface_control_law.frozen_gamma


def multicover_select(B_pool: list[int], I0: list[int], G_hat: dict, q: int = FROZEN_Q,
                       gamma: float = FROZEN_GAMMA) -> list[int]:
    """Greedy q-fold multicover on an arbitrary incidence graph G_hat[i] =
    set of pool members predictively supported as inputs to i (works
    identically whether G_hat came from the true lattice or from
    graph_inference.infer_incidence_graph -- this function itself never
    reads the lattice). Mirrors v3_refinement/code/selection_rules_v3.py's
    greedy_multicover_order / min_actuators_for_multicover, generalized from
    a lattice-neighbor incidence to an arbitrary one. q, gamma default to
    the FROZEN V3 values and are not re-tuned here."""
    I0 = list(int(i) for i in I0)
    incoming = {i: (set(G_hat.get(i, set())) & set(B_pool)) for i in I0}
    count = {i: 0 for i in I0}
    remaining = set(int(b) for b in B_pool)
    order: list[int] = []

    while remaining:
        def gain(b):
            return sum(1 for i in I0 if b in incoming[i] and count[i] < q)
        best = max(remaining, key=lambda b: (gain(b), -b))
        order.append(best)
        for i in I0:
            if best in incoming[i]:
                count[i] += 1
        remaining.discard(best)

    def frac_covered(k: int) -> float:
        c = {i: 0 for i in I0}
        chosen = set(order[:k])
        for i in I0:
            c[i] = len(incoming[i] & chosen)
        return float(np.mean([1 if c[i] >= q else 0 for i in I0])) if I0 else float("nan")

    for k in range(1, len(order) + 1):
        if frac_covered(k) >= gamma:
            return order[:k]
    return order


def evaluate_controller(actuators: list[int], z_t0: np.ndarray, I0: np.ndarray, h_star: int,
                         nn: int, lattice, n_replicates: int, seed_offset: int) -> dict:
    """Identical protocol to v2_interface_control/code/common_v2.py's
    evaluate_arm (T_u/T_r pulse, same success/persistence bars) so numbers
    are directly comparable to Stage-6 controller results; reimplemented
    here (rather than imported) only because it must accept an arbitrary
    actuator list without assuming that list is a subset of any particular
    lattice-derived shell."""
    Hstar_end = np.zeros(n_replicates)
    Hstar_release = np.zeros(n_replicates)
    coh_traj = np.zeros((n_replicates, T_U + 1))
    for r in range(n_replicates):
        seed = seed_offset + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
        res = run_simulation(nn=nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        Hstar_release[r] = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
        for t in range(T_U + 1):
            coh_traj[r, t] = coherence(res.z_hist[t], I0)

    success = Hstar_end >= 0.8
    persistence = Hstar_release >= 0.5
    return dict(
        n_actuators=len(actuators), n_replicates=n_replicates,
        mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
        mean_Hstar_release=float(Hstar_release.mean()),
        p_persistence_given_success=float(persistence[success].mean()) if success.any() else None,
        mean_min_coherence=float(coh_traj.min(axis=1).mean()),
        actuators=sorted(int(a) for a in actuators),
    )
