"""Membership/turnover/boundary/task metrics (Part 3.5, 4, 4.1, 4.2)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from common_v2 import dynamical_shell  # noqa: E402

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
from definitions import jaccard  # noqa: E402


def retention_fraction(I0, I_t) -> float:
    I0s, Its = set(I0.tolist()), set(I_t.tolist())
    return len(I0s & Its) / len(I0s) if I0s else float("nan")


def recruit_fraction(I0, I_t) -> float:
    I0s, Its = set(I0.tolist()), set(I_t.tolist())
    return len(Its - I0s) / len(Its) if Its else float("nan")


def turnover(I_prev, I_cur) -> int:
    return len(set(I_prev.tolist()) ^ set(I_cur.tolist()))


def track_membership_metrics(I0, I_track: list[np.ndarray]) -> dict:
    """Part 3.5: size, R0(t), Qrecruit(t), turnover T_I(t), lineage Jaccard."""
    sizes, R0, Qrec, T_I, J = [], [], [], [], []
    for t, I_t in enumerate(I_track):
        sizes.append(len(I_t))
        R0.append(retention_fraction(I0, I_t))
        Qrec.append(recruit_fraction(I0, I_t))
        if t == 0:
            T_I.append(0)
            J.append(1.0)
        else:
            T_I.append(turnover(I_track[t - 1], I_t))
            J.append(jaccard(I_track[t - 1], I_t))
    return dict(size=sizes, R0=R0, Qrecruit=Qrec, turnover=T_I, jaccard_lineage=J)


def track_boundary_metrics(I_track: list[np.ndarray], lattice) -> dict:
    """Part 4.2: B_t^{D,r} for the representation's own I_t track (true
    lattice, ground-truth/ evaluation use only), plus its turnover."""
    sizes, turn, B_track = [], [], []
    B_prev = None
    for I_t in I_track:
        B_t = dynamical_shell(lattice, I_t)
        B_track.append(B_t)
        sizes.append(len(B_t))
        turn.append(0 if B_prev is None else len(set(B_prev.tolist()) ^ set(B_t.tolist())))
        B_prev = B_t
    return dict(size=sizes, turnover=turn, B_track=B_track)


def target_heading_decomposition(z: np.ndarray, I0, I_t, h_star: int) -> dict:
    """Part 4.1: H*(I_t), H*(I_t ∩ I0) [retained], H*(I_t \\ I0) [recruited] --
    the identity-gaming decomposition."""
    I0s, Its = set(I0.tolist()), set(I_t.tolist())
    retained = np.array(sorted(I0s & Its))
    recruited = np.array(sorted(Its - I0s))
    return dict(
        H_full=target_heading_fraction(z, I_t, h_star) if len(I_t) else float("nan"),
        H_retained=target_heading_fraction(z, retained, h_star) if len(retained) else float("nan"),
        H_recruited=target_heading_fraction(z, recruited, h_star) if len(recruited) else float("nan"),
        n_retained=len(retained), n_recruited=len(recruited),
    )


def per_definition_trajectory_report(z_hist, I0, I_track, h_star, T_u, T_r) -> dict:
    """Part 4: success/recovery/persistence/coherence for one representation's
    I_t track, matching Stage-6's own success (H*>=0.8 at t0+T_u) and
    persistence (H*>=0.5 at t0+T_u+T_r) bars for direct comparability."""
    n = len(I_track)
    Hstar = np.zeros(n)
    coh = np.zeros(n)
    decomp = []
    for t in range(n):
        I_t = I_track[t]
        Hstar[t] = target_heading_fraction(z_hist[t], I_t, h_star) if len(I_t) else float("nan")
        coh[t] = coherence(z_hist[t], I_t) if len(I_t) else float("nan")
        decomp.append(target_heading_decomposition(z_hist[t], I0, I_t, h_star))

    end_idx = min(T_u, n - 1)
    release_idx = min(T_u + T_r, n - 1)
    success = bool(Hstar[end_idx] >= 0.8)
    persistence = bool(Hstar[release_idx] >= 0.5)
    recovery_time = next((t for t in range(n) if Hstar[t] >= 0.8), None)
    return dict(
        Hstar_trajectory=Hstar.tolist(), coherence_trajectory=coh.tolist(),
        decomposition_trajectory=decomp, success=success, persistence=persistence,
        Hstar_end=float(Hstar[end_idx]), Hstar_release=float(Hstar[release_idx]),
        recovery_time=recovery_time,
        min_coherence=float(np.nanmin(coh)) if n else float("nan"),
    )
