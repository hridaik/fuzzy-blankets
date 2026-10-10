"""Shared utilities for V2, self-contained (does not import from
v1_mechanism_audit, so this protocol stands on its own). Imports flock_sim
from the frozen ../../python tree, unmodified."""
from __future__ import annotations

import sys
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]          # stage6_flock/
V2_DIR = Path(__file__).resolve().parents[1]          # v2_interface_control/
sys.path.insert(0, str(ROOT / "python"))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from flock_sim.spectral import analyze_window  # noqa: E402
from flock_sim.model import rotate_cw  # noqa: E402
from analysis.baseline_characterization import find_qualifying_t0  # noqa: E402

T_U = 20
T_R = 20
TW = 5
BASE_SEED_OFFSET = 300_000   # distinct range from protocol_v1's 100_000 / phase6's 200_000
N_REP = 30


def dump_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)


def dynamical_shell(lattice: Lattice, I0: np.ndarray) -> np.ndarray:
    """B^D_0(I0): non-I0 birds that are a Moore-lattice-neighbor of some I0 member.
    Identical definition to v1_mechanism_audit/code/dynamical_shell.py."""
    nbrs = set()
    for i in I0.tolist():
        nbrs.update(lattice.neighbor_ids[i].tolist())
    nbrs -= set(I0.tolist())
    return np.array(sorted(nbrs), dtype=int)


def find_flock(seed: int, nn: int = 100, nt_search: int = 60, lattice: Lattice | None = None):
    lattice = lattice or Lattice(nn=nn, nh=8)
    res = run_simulation(nn=nn, nt=nt_search, seed=seed, lattice=lattice)
    q = find_qualifying_t0(res.z_hist)
    if q is None:
        return None
    t0, I0, h0 = q["t0"], np.array(q["I0"]), q["h0"]
    h_star = rotate_cw(h0)
    # re-run to have enough headroom for t0 + T_u + T_r
    nt_total = t0 + T_U + T_R + 5
    res_full = run_simulation(nn=nn, nt=nt_total, seed=seed, lattice=lattice)
    z_t0 = res_full.z_hist[t0]
    return dict(seed=seed, t0=int(t0), h0=int(h0), h_star=int(h_star), I0=I0,
                eigengap=q["eigengap"], coherence=q["coherence"], z_t0=z_t0, lattice=lattice)


def evaluate_arm(actuators, z_t0, I0, h_star, lattice, n_replicates=N_REP, seed_offset=BASE_SEED_OFFSET):
    Hstar_end = np.zeros(n_replicates)
    Hstar_release = np.zeros(n_replicates)
    coh_traj = np.zeros((n_replicates, T_U + 1))
    lineage_end = np.zeros(n_replicates)
    for r in range(n_replicates):
        seed = seed_offset + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
        res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        Hstar_release[r] = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
        for t in range(T_U + 1):
            coh_traj[r, t] = coherence(res.z_hist[t], I0)
        window = res.z_hist[T_U - TW + 1: T_U + 1]
        sr = analyze_window(window, refclust=I0)
        lineage_end[r] = len(np.intersect1d(I0, sr.core1_nodes)) / len(I0)

    min_coh_full = coh_traj.min(axis=1)
    min_coh_recovery = coh_traj[:, -4:].min(axis=1)  # trailing 4 steps incl. t0+T_u itself
    success = Hstar_end >= 0.8
    integrity_full = (min_coh_full >= 0.8) & (lineage_end >= 0.5)
    integrity_recovery = (min_coh_recovery >= 0.8) & (lineage_end >= 0.5)
    persistence = Hstar_release >= 0.5

    return dict(
        n_actuators=len(actuators), n_replicates=n_replicates,
        mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
        p_success_and_integrity_full=float((success & integrity_full).mean()),
        p_success_and_integrity_recovery=float((success & integrity_recovery).mean()),
        mean_Hstar_release=float(Hstar_release.mean()),
        p_persistence_given_success=float(persistence[success].mean()) if success.any() else None,
        mean_min_coherence=float(min_coh_full.mean()), mean_lineage_end=float(lineage_end.mean()),
    )
