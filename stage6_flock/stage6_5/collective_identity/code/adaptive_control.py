"""Part 5: closed-loop identity-adaptive control, proof-of-concept only (per
Part 5's own instruction: "This is a smaller proof-of-concept, not another
major optimization study" / "Do not develop a new optimization algorithm").

Scope decision, stated up front: actuator selection here uses the TRUE
relative shell B_t^{D,r} = dynamical_shell(lattice, I_t^r) and the FROZEN V3
multicover rule (q=2, gamma=0.5, v3_refinement/configs/protocol_v3.yaml),
not a re-inferred Ĝ from boundary_inference/Part 1. Reason: Part 1's
inference procedure needs many independent trajectories to fit a predictive
model; a live closed-loop episode is ONE realized trajectory, so there is no
statistically meaningful way to re-run Part 1's greedy selection online at
every step without either (a) reusing a Ĝ inferred offline from unrelated
baseline trajectories, which would silently import inference error into a
question this proof-of-concept is not trying to ask, or (b) fabricating
"replicate" data by branching the live episode itself, which the Part 5
brief's own stopping rule ("do not spend large amounts of time engineering
around limitations of a model we already plan to replace") argues against
building out. Using the true shell isolates the actual target question of
Part 5 -- does a CHANGING DEFINITION of the collective change the
intervention interface and control policy? -- from a second, separate
inference-error question already covered by Part 1/2. This is recorded
here, not discovered after the fact.
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
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from common_v2 import dynamical_shell, T_U, T_R  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
from definitions import lineage_track, functional_track, material_track  # noqa: E402

FROZEN_Q = 2
FROZEN_GAMMA = 0.5
CLOSED_LOOP_SEED_OFFSET = 780_000


def _current_I_t(representation: str, z_hist_so_far: np.ndarray, I0: np.ndarray, lattice) -> np.ndarray:
    t_end = z_hist_so_far.shape[0] - 1
    if representation == "M":
        return np.array(sorted(int(i) for i in I0.tolist()))
    elif representation == "L":
        return lineage_track(z_hist_so_far, I0, t_start=0, t_end=t_end)[-1]
    elif representation == "F":
        return functional_track(z_hist_so_far, I0, t_start=0, t_end=t_end, lattice=lattice)[-1]
    raise ValueError(representation)


def run_closed_loop_episode(fl: dict, representation: str, seed: int, T_u: int = T_U, T_r: int = T_R,
                             q: int = FROZEN_Q, gamma: float = FROZEN_GAMMA) -> dict:
    """One closed-loop replicate. At each control step t in [0, T_u): recompute
    I_t^r causally from the realized episode so far, its true relative shell
    B_t = dynamical_shell(lattice, I_t^r), and a multicover actuator set A_t
    subset of B_t (frozen q, gamma); force A_t toward h_star for exactly that
    one step; advance. During release [T_u, T_u+T_r), no actuation, but I_t^r
    (and hence B_t) keep being tracked so post-release persistence/coherence
    can be evaluated per-representation. Returns z_hist, I_track, B_track,
    A_track (empty list during release) for the whole episode.
    """
    lattice, I0, h_star = fl["lattice"], fl["I0"], fl["h_star"]
    nn = lattice.nn
    z_current = fl["z_t0"].copy()
    z_hist = [z_current.copy()]
    I_track = [np.array(sorted(int(i) for i in I0.tolist()))]
    B_track = [dynamical_shell(lattice, I_track[0])]
    A_track: list[list[int]] = []

    for t in range(T_u):
        z_so_far = np.array(z_hist)
        I_t = _current_I_t(representation, z_so_far, I0, lattice)
        B_t = dynamical_shell(lattice, I_t)
        A_t = min_actuators_for_multicover(B_t, I_t, lattice, q=q, gamma=gamma) if len(B_t) and len(I_t) else []
        interventions = {0: {int(a): int(h_star) for a in A_t}} if A_t else None
        res = run_simulation(nn=nn, nt=1, seed=CLOSED_LOOP_SEED_OFFSET + 1000 * seed + t,
                              init_z=z_current, interventions=interventions, lattice=lattice)
        z_current = res.z_hist[1]
        z_hist.append(z_current.copy())
        I_track.append(I_t)
        B_track.append(B_t)
        A_track.append(A_t)

    for t in range(T_u, T_u + T_r):
        z_so_far = np.array(z_hist)
        I_t = _current_I_t(representation, z_so_far, I0, lattice)
        B_t = dynamical_shell(lattice, I_t)
        res = run_simulation(nn=nn, nt=1, seed=CLOSED_LOOP_SEED_OFFSET + 1000 * seed + t,
                              init_z=z_current, interventions=None, lattice=lattice)
        z_current = res.z_hist[1]
        z_hist.append(z_current.copy())
        I_track.append(I_t)
        B_track.append(B_t)

    return dict(z_hist=np.array(z_hist), I_track=I_track, B_track=B_track, A_track=A_track,
                I0=I0, h_star=h_star, T_u=T_u, T_r=T_r)


def summarize_episode(ep: dict) -> dict:
    z_hist, I_track, I0, h_star, T_u, T_r = ep["z_hist"], ep["I_track"], ep["I0"], ep["h_star"], ep["T_u"], ep["T_r"]
    n = len(I_track)
    Hstar_full = np.array([target_heading_fraction(z_hist[t], I_track[t], h_star) for t in range(n)])
    I0_arr = np.array(sorted(int(i) for i in I0.tolist()))
    Hstar_retained = np.array([
        target_heading_fraction(z_hist[t], np.intersect1d(I0_arr, I_track[t]), h_star) for t in range(n)
    ])
    coh = np.array([coherence(z_hist[t], I_track[t]) if len(I_track[t]) else float("nan") for t in range(n)])
    end_idx, rel_idx = min(T_u, n - 1), min(T_u + T_r, n - 1)
    n_actuators = [len(a) for a in ep["A_track"]]
    return dict(
        success=bool(Hstar_full[end_idx] >= 0.8),
        success_retained_only=bool(Hstar_retained[end_idx] >= 0.8),
        persistence=bool(Hstar_full[rel_idx] >= 0.5),
        Hstar_end=float(Hstar_full[end_idx]), Hstar_end_retained=float(Hstar_retained[end_idx]),
        Hstar_release=float(Hstar_full[rel_idx]),
        mean_min_coherence=float(np.nanmin(coh)),
        mean_n_actuators=float(np.mean(n_actuators)) if n_actuators else 0.0,
        max_n_actuators=int(np.max(n_actuators)) if n_actuators else 0,
        final_retention=float(len(np.intersect1d(I0_arr, I_track[end_idx])) / len(I0_arr)),
        final_size=len(I_track[end_idx]),
        membership_turnover_total=int(sum(
            len(set(I_track[t - 1].tolist()) ^ set(I_track[t].tolist())) for t in range(1, n)
        )),
        actuator_turnover_total=int(sum(
            len(set(ep["A_track"][t - 1]) ^ set(ep["A_track"][t])) for t in range(1, len(ep["A_track"]))
        )) if len(ep["A_track"]) > 1 else 0,
    )
