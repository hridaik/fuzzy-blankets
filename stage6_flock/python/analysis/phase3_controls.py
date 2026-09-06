"""Phase 3A: positive/negative controls, branching from the canonical snapshot.
Uses common random numbers (same seed for the paired baseline/controlled runs)
per PROTOCOL_V1.md / METHODS_AUDIT.md section 12.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import numpy as np

from flock_sim.lattice import Lattice, bird_to_rowcol
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence

T_U = 20
T_R = 20
N_REPLICATES = 50
BASE_SEED_OFFSET = 100_000  # keep well clear of canonical/other seed ranges


def load_canonical():
    d = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    data = np.load(d / "canonical_snapshot.npz")
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    z_t0 = data["z_hist_full"][meta["t0"]]
    return z_t0, meta


def farthest_non_interior_bird(I0: np.ndarray, nn: int, L: int) -> int:
    row0, col0 = bird_to_rowcol(I0, L)
    centroid = np.array([row0.mean(), col0.mean()])
    all_idx = np.arange(nn)
    non_interior = np.setdiff1d(all_idx, I0)
    row, col = bird_to_rowcol(non_interior, L)
    d = np.maximum(np.abs(row - centroid[0]), np.abs(col - centroid[1]))  # Chebyshev
    return int(non_interior[np.argmax(d)])


def run_arm(name: str, z_t0: np.ndarray, I0: np.ndarray, h_star: int, lattice: Lattice,
            actuators: list[int] | None, n_replicates: int) -> dict:
    results = []
    for r in range(n_replicates):
        seed = BASE_SEED_OFFSET + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if actuators else None
        res = run_simulation(nn=lattice.nn, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        h_star_end = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        h_star_release = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
        min_coh = min(coherence(res.z_hist[t], I0) for t in range(T_U + 1))
        results.append(dict(seed=seed, Hstar_end=h_star_end, Hstar_release=h_star_release, min_coherence=min_coh))
    Hstar_end = np.array([r["Hstar_end"] for r in results])
    Hstar_rel = np.array([r["Hstar_release"] for r in results])
    min_coh = np.array([r["min_coherence"] for r in results])
    success = Hstar_end >= 0.8
    integrity = min_coh >= 0.8
    summary = dict(
        name=name, actuators=actuators, n=n_replicates,
        mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
        p_success_and_integrity=float((success & integrity).mean()),
        mean_Hstar_release=float(Hstar_rel.mean()),
        mean_min_coherence=float(min_coh.mean()),
    )
    return summary, results


def main():
    z_t0, meta = load_canonical()
    I0 = np.array(meta["I0"])
    h_star = meta["h_star"]
    lattice = Lattice(nn=100, nh=8)

    arms = {}
    arms["baseline_no_control"], raw_baseline = run_arm(
        "baseline_no_control", z_t0, I0, h_star, lattice, actuators=None, n_replicates=N_REPLICATES)
    arms["positive_control_full_core"], raw_pos = run_arm(
        "positive_control_full_core", z_t0, I0, h_star, lattice, actuators=I0.tolist(), n_replicates=N_REPLICATES)
    far_bird = farthest_non_interior_bird(I0, 100, lattice.L)
    arms["negative_control_far_single_bird"], raw_neg = run_arm(
        "negative_control_far_single_bird", z_t0, I0, h_star, lattice, actuators=[far_bird], n_replicates=N_REPLICATES)

    out_dir = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    with open(out_dir / "phase3_controls_summary.json", "w") as f:
        json.dump(dict(far_bird=far_bird, T_u=T_U, T_r=T_R, n_replicates=N_REPLICATES, arms=arms), f, indent=2)

    for name, s in arms.items():
        print(f"{name}: mean_Hstar_end={s['mean_Hstar_end']:.3f} p_success={s['p_success']:.3f} "
              f"p_success_and_integrity={s['p_success_and_integrity']:.3f} "
              f"mean_Hstar_release={s['mean_Hstar_release']:.3f} mean_min_coherence={s['mean_min_coherence']:.3f}")
    print("far_bird (negative control actuator, Chebyshev-farthest non-interior bird):", far_bird)


if __name__ == "__main__":
    main()
