"""Phase 6 (partial): repeat the frozen protocol's canonical-snapshot + k=1
exhaustive search on additional independently emergent flocks (different
seeds), using the exact same thresholds/horizons from PROTOCOL_V1.md. This is
a reduced-scale replication (2 additional seeds, k=1 only) given this
session's time budget -- documented as partial in RESULTS_V1.md, not claimed
as the full task-brief-scale study."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import time
import numpy as np

from flock_sim.simulation import run_simulation
from flock_sim.lattice import Lattice
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence
from flock_sim.model import rotate_cw
from analysis.baseline_characterization import find_qualifying_t0

T_U = 20
T_R = 20
N_REPLICATES = 50
BASE_SEED_OFFSET = 200_000  # distinct range from the canonical-seed sweeps
SEEDS_TO_REPLICATE = [3, 4]


def main():
    lattice = Lattice(nn=100, nh=8)
    out = {}
    for seed in SEEDS_TO_REPLICATE:
        res = run_simulation(nn=100, nt=max(120, 60 + T_U + T_R + 20), seed=seed, lattice=lattice)
        q = find_qualifying_t0(res.z_hist[:61])
        if q is None:
            out[seed] = dict(found=False)
            continue
        t0, I0, h0 = q["t0"], np.array(q["I0"]), q["h0"]
        h_star = rotate_cw(h0)
        z_t0 = res.z_hist[t0]

        # k=1 exhaustive
        non_interior = np.setdiff1d(np.arange(100), I0)
        per_bird = {}
        t_start = time.time()
        for k in non_interior.tolist():
            Hstar_end = np.zeros(N_REPLICATES)
            for r in range(N_REPLICATES):
                seed_r = BASE_SEED_OFFSET + r
                interventions = make_pulse([k], h_star, t0=0, t_u=T_U)
                r_res = run_simulation(nn=100, nt=T_U + T_R, seed=seed_r, init_z=z_t0,
                                        interventions=interventions, lattice=lattice)
                Hstar_end[r] = target_heading_fraction(r_res.z_hist[T_U], I0, h_star)
            per_bird[int(k)] = dict(mean_Hstar_end=float(Hstar_end.mean()),
                                     p_success=float((Hstar_end >= 0.8).mean()))
        elapsed = time.time() - t_start
        best_k = max(per_bird, key=lambda k: per_bird[k]["p_success"])
        max_mean = max(v["mean_Hstar_end"] for v in per_bird.values())
        n_success = sum(1 for v in per_bird.values() if v["p_success"] >= 0.5)
        out[seed] = dict(found=True, t0=int(t0), h0=int(h0), h_star=int(h_star), size=len(I0),
                          eigengap=q["eigengap"], coherence=q["coherence"],
                          n_non_interior=len(non_interior), elapsed_s=elapsed,
                          best_k1_bird=int(best_k), best_k1_p_success=per_bird[best_k]["p_success"],
                          max_k1_mean_Hstar=max_mean, n_actuators_meeting_bar=n_success,
                          per_bird=per_bird)
        print(f"seed={seed}: t0={t0} h0={h0} size={len(I0)} -> max_k1_mean_Hstar={max_mean:.3f} "
              f"n_meeting_bar={n_success}/{len(non_interior)} elapsed={elapsed:.1f}s")

    out_dir = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    with open(out_dir / "phase6_replication_partial.json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
