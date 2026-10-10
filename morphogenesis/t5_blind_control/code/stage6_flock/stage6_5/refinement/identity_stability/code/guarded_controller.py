"""C4: closed-loop identity guard. Extends (does not edit)
collective_identity/code/adaptive_control.py's closed-loop pattern: at each
control step, recompute the representation's RAW candidate identity exactly
as before, then apply the C3 validity envelope. If the raw candidate fails
the envelope, hold the last VALID identity for a short predeclared grace
period; if validity is not recovered within that window, mark the episode
IDENTITY COLLAPSE / UNRESOLVED (sticky for the remainder of the episode)
rather than silently substituting a different group or forcing an ad hoc
larger cluster.

Four representations, matching Part C7's controller set:
  "M"       material (fixed I0, trivially always valid, no guard needed)
  "L_reg"   temporally regularized lineage (C2), GUARDED
  "F_guard" original functional definition (definitions.functional_track), GUARDED
  "F"       original functional definition, UNGUARDED -- kept only as the
            Part-C7 pathology comparator (reproduces Stage 6.5's own
            one-bird-collapse finding under this refinement's harness).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))
COLLECTIVE_IDENTITY_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from common_v2 import dynamical_shell, T_U, T_R  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402
from definitions import functional_track, material_track  # noqa: E402
from regularized_lineage import regularized_lineage_track  # noqa: E402
from validity_guard import is_valid  # noqa: E402

FROZEN_Q, FROZEN_GAMMA = 2, 0.5
CLOSED_LOOP_SEED_OFFSET = 8_700_000
GUARDED_REPRESENTATIONS = {"L_reg", "F_guard"}


def _raw_candidate(representation: str, z_so_far: np.ndarray, I0: np.ndarray, lattice,
                    lambda_T: float) -> np.ndarray:
    t_end = z_so_far.shape[0] - 1
    if representation == "M":
        return np.array(sorted(int(i) for i in I0.tolist()))
    elif representation == "L_reg":
        return regularized_lineage_track(z_so_far, I0, t_start=0, t_end=t_end, lambda_T=lambda_T)[-1]
    elif representation in ("F_guard", "F"):
        return functional_track(z_so_far, I0, t_start=0, t_end=t_end, lattice=lattice)[-1]
    raise ValueError(representation)


def run_guarded_closed_loop_episode(fl: dict, representation: str, seed: int, envelope: dict | None,
                                     lambda_T: float | None = None, grace_period: int = 3,
                                     T_u: int = T_U, T_r: int = T_R, q: int = FROZEN_Q,
                                     gamma: float = FROZEN_GAMMA) -> dict:
    lattice, I0, h_star = fl["lattice"], fl["I0"], fl["h_star"]
    nn = lattice.nn
    n_I0 = len(I0)
    guarded = representation in GUARDED_REPRESENTATIONS

    z_current = fl["z_t0"].copy()
    z_hist = [z_current.copy()]
    I0_sorted = np.array(sorted(int(i) for i in I0.tolist()))
    I_track = [I0_sorted]
    valid_track = [True]
    collapsed_track = [False]
    B_track = [dynamical_shell(lattice, I_track[0])]
    A_track: list[list[int]] = []

    last_valid = I0_sorted
    grace_counter = 0
    collapsed = False

    def _step_identity(t_idx: int) -> np.ndarray:
        nonlocal last_valid, grace_counter, collapsed
        z_so_far = np.array(z_hist)
        raw = _raw_candidate(representation, z_so_far, I0, lattice, lambda_T)
        if not guarded:
            valid_track.append(True)
            collapsed_track.append(False)
            return raw
        check = is_valid(raw, last_valid, n_I0, envelope)
        if check["valid"]:
            last_valid = raw
            grace_counter = 0
            valid_track.append(True)
            collapsed_track.append(collapsed)
            return raw
        grace_counter += 1
        valid_track.append(False)
        if grace_counter > grace_period:
            collapsed = True
        collapsed_track.append(collapsed)
        return last_valid

    for t in range(T_u):
        I_t = _step_identity(t)
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
        I_t = _step_identity(t)
        B_t = dynamical_shell(lattice, I_t)
        res = run_simulation(nn=nn, nt=1, seed=CLOSED_LOOP_SEED_OFFSET + 1000 * seed + t,
                              init_z=z_current, interventions=None, lattice=lattice)
        z_current = res.z_hist[1]
        z_hist.append(z_current.copy())
        I_track.append(I_t)
        B_track.append(B_t)

    return dict(z_hist=np.array(z_hist), I_track=I_track, B_track=B_track, A_track=A_track,
                valid_track=valid_track, collapsed_track=collapsed_track,
                identity_collapse_unresolved=collapsed,
                I0=I0, h_star=h_star, T_u=T_u, T_r=T_r, representation=representation)


def summarize_guarded_episode(ep: dict) -> dict:
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
    nominal_success = bool(Hstar_full[end_idx] >= 0.8)
    identity_valid_at_end = not ep["collapsed_track"][end_idx]
    return dict(
        representation=ep["representation"],
        nominal_success=nominal_success,
        identity_collapse_unresolved=ep["identity_collapse_unresolved"],
        identity_valid_success=bool(nominal_success and identity_valid_at_end),
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
        n_invalid_steps=int(sum(1 for v in ep["valid_track"] if not v)),
    )
