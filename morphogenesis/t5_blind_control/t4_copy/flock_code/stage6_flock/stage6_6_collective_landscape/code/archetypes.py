"""Sections 11-14 of the task brief: the transparent control archetypes used
to sanity-check the four metrics (and later, Explore-mode snapshot regimes /
Control-mode conditions in the demo). Reuses the exact existing Stage-6
intervention hook (`flock_sim.interventions.make_pulse`) unmodified -- control
acts at the same update-rule point as V2/V3 (the "applied action" override
inside `active_inference.step`, see PLAN.md), never a direct z_new overwrite.
"""
from __future__ import annotations

import numpy as np

from common_66 import (
    Lattice, make_pulse, rotate_cw, structural_shell, near_exterior,
    graph_distance_from_set, T_U, T_R,
)

UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])

CONDITIONS = ["no_control", "shell_only", "same_direction", "opposite", "disordered"]


def opposite_heading(h: int) -> int:
    """Geometric 180-degree opposite, via the existing UV4 heading map (task
    brief section 11.D: "Do not compute this by naive heading-index
    arithmetic"). (h+2)%4 would be WRONG here because {0,1,2,3}={up,down,
    left,right} is not a rotational cycle (see flock_sim.model's ROT_CW/
    ROT_CCW docstring); e.g. naive (0+2)%4=2=left, but the true geometric
    opposite of up is down=1."""
    target_vec = -UV4[h]
    matches = np.where(np.all(np.isclose(UV4, target_vec), axis=1))[0]
    assert len(matches) == 1
    result = int(matches[0])
    from common_66 import rotate_cw as _cw
    assert result == _cw(_cw(h)), "opposite_heading disagrees with rotate_cw . rotate_cw"
    return result


def farthest_point_subset(lattice: Lattice, nodes: np.ndarray, fraction: float) -> np.ndarray:
    """Deterministic max-min (farthest-point) selection of a spatially
    distributed subset of `nodes`, at the given fraction. Never concentrates
    controlled nodes in one patch (task brief section 13)."""
    nodes = np.asarray(sorted(int(n) for n in nodes))
    n_select = max(1, int(round(fraction * len(nodes)))) if fraction > 0 else 0
    if n_select == 0 or len(nodes) == 0:
        return np.array([], dtype=int)
    if n_select >= len(nodes):
        return nodes

    # pairwise graph distance among `nodes` only, via one BFS per node
    idx = {n: k for k, n in enumerate(nodes)}
    D = np.zeros((len(nodes), len(nodes)), dtype=int)
    for k, n in enumerate(nodes):
        dist = graph_distance_from_set(lattice, np.array([n]), nn=lattice.nn)
        D[k] = dist[nodes]

    selected = [0]  # deterministic seed: lowest-id node
    while len(selected) < n_select:
        min_dist_to_selected = D[:, selected].min(axis=1)
        min_dist_to_selected[selected] = -1
        nxt = int(np.argmax(min_dist_to_selected))
        selected.append(nxt)
    return nodes[np.array(sorted(selected))]


def balanced_rotating_targets(nodes: np.ndarray, t0: int, t_u: int) -> dict:
    """Deterministic balanced rotating schedule: bird at rank r within the
    (sorted) controlled set is forced toward heading (r + t) % 4 at timestep
    t. At any fixed t this partitions the controlled set into (nearly) equal
    quarters across the four headings, and every bird cycles through all
    four headings over 4 consecutive steps -- "disordered" without ever
    passing through a transient accidental consensus (task brief section 11.E:
    "Do not use an uncontrolled random draw that can accidentally generate
    temporary consensus.")."""
    nodes = np.asarray(sorted(int(n) for n in nodes))
    out = {}
    for t in range(t0, t0 + t_u):
        out[t] = {int(n): int((r + t) % 4) for r, n in enumerate(nodes)}
    return out


def _merge_interventions(*dicts) -> dict:
    out: dict = {}
    for d in dicts:
        for t, m in d.items():
            out.setdefault(t, {}).update(m)
    return out


def build_condition(lattice: Lattice, I: np.ndarray, h_star: int, condition: str,
                     f_E: float = 1.0, t0: int = 0, t_u: int = T_U) -> dict:
    """Returns dict(interventions, shell, near_exterior, controlled_exterior,
    h_star, h_opp, condition, f_E). `interventions` is None for 'no_control'."""
    assert condition in CONDITIONS, condition
    S = structural_shell(lattice, I)
    E_near = near_exterior(lattice, I, nn=lattice.nn)
    h_opp = opposite_heading(h_star)

    if condition == "no_control":
        return dict(interventions=None, shell=S, near_exterior=E_near,
                     controlled_exterior=np.array([], dtype=int),
                     h_star=h_star, h_opp=h_opp, condition=condition, f_E=0.0)

    shell_pulse = make_pulse(S, h_star, t0=t0, t_u=t_u)
    if condition == "shell_only":
        return dict(interventions=shell_pulse, shell=S, near_exterior=E_near,
                     controlled_exterior=np.array([], dtype=int),
                     h_star=h_star, h_opp=h_opp, condition=condition, f_E=0.0)

    controlled = farthest_point_subset(lattice, E_near, f_E)
    if condition == "same_direction":
        ext_pulse = make_pulse(controlled, h_star, t0=t0, t_u=t_u)
    elif condition == "opposite":
        ext_pulse = make_pulse(controlled, h_opp, t0=t0, t_u=t_u)
    elif condition == "disordered":
        ext_pulse = balanced_rotating_targets(controlled, t0=t0, t_u=t_u)
    else:
        raise ValueError(condition)

    interventions = _merge_interventions(shell_pulse, ext_pulse)
    return dict(interventions=interventions, shell=S, near_exterior=E_near,
                controlled_exterior=controlled, h_star=h_star, h_opp=h_opp,
                condition=condition, f_E=f_E)
