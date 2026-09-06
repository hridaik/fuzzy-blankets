"""Phase 5A continuation: k=1 found no actuator meeting P(success)>=0.5 (see
data/protocol_v1/phase4_5_response_map.json). Per PROTOCOL_V1.md section 7,
exhaustively test all pairs within the top-10 shortlist by empirical response
magnitude (mean_Hstar_end)."""
from __future__ import annotations

import sys
from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import time
import numpy as np

from flock_sim.lattice import Lattice
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence
from flock_sim.spectral import analyze_window

T_U = 20
T_R = 20
N_REPLICATES = 50
BASE_SEED_OFFSET = 100_000
TW = 5
SHORTLIST_SIZE = 10


def main():
    d = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    rm = json.load(open(d / "phase4_5_response_map.json"))
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    data = np.load(d / "canonical_snapshot.npz")
    I0 = np.array(rm["I0"])
    h_star = rm["h_star"]
    t0 = meta["t0"]
    z_t0 = data["z_hist_full"][t0]
    lattice = Lattice(nn=100, nh=8)

    results = {int(k): v for k, v in rm["results"].items()}
    shortlist = [k for k, v in sorted(results.items(), key=lambda kv: -kv[1]["mean_Hstar_end"])[:SHORTLIST_SIZE]]
    print("Shortlist (top-10 by k=1 mean_Hstar_end):", shortlist)

    pair_results = {}
    t_start = time.time()
    for a, b in combinations(shortlist, 2):
        Hstar_end = np.zeros(N_REPLICATES)
        Hstar_rel = np.zeros(N_REPLICATES)
        min_coh = np.zeros(N_REPLICATES)
        lineage_end = np.zeros(N_REPLICATES)
        for r in range(N_REPLICATES):
            seed = BASE_SEED_OFFSET + r
            interventions = make_pulse([a, b], h_star, t0=0, t_u=T_U)
            res = run_simulation(nn=100, nt=T_U + T_R, seed=seed, init_z=z_t0,
                                  interventions=interventions, lattice=lattice)
            Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
            Hstar_rel[r] = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
            min_coh[r] = min(coherence(res.z_hist[t], I0) for t in range(T_U + 1))
            window = res.z_hist[T_U - TW + 1: T_U + 1]
            sr = analyze_window(window, refclust=I0)
            lineage_end[r] = len(np.intersect1d(I0, sr.core1_nodes)) / len(I0)
        success = Hstar_end >= 0.8
        integrity = (min_coh >= 0.8) & (lineage_end >= 0.5)
        pair_results[f"{a}_{b}"] = dict(
            pair=[a, b], mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
            p_success_and_integrity=float((success & integrity).mean()),
            mean_Hstar_release=float(Hstar_rel.mean()), mean_min_coherence=float(min_coh.mean()),
            mean_lineage_end=float(lineage_end.mean()),
        )
    print(f"Tested {len(pair_results)} pairs in {time.time()-t_start:.1f}s")

    out_dir = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    with open(out_dir / "phase5_k2_search.json", "w") as f:
        json.dump(dict(shortlist=shortlist, T_u=T_U, T_r=T_R, n_replicates=N_REPLICATES, results=pair_results), f, indent=1)

    best = max(pair_results.items(), key=lambda kv: kv[1]["p_success"])
    print(f"\nBest pair: {best[1]['pair']}, p_success={best[1]['p_success']:.3f}, "
          f"p_success_and_integrity={best[1]['p_success_and_integrity']:.3f}, mean_Hstar_end={best[1]['mean_Hstar_end']:.3f}")
    n_meeting = sum(1 for v in pair_results.values() if v["p_success"] >= 0.5)
    print(f"Pairs meeting P(success)>=0.5: {n_meeting} / {len(pair_results)}")
    top5 = sorted(pair_results.items(), key=lambda kv: -kv[1]["p_success"])[:5]
    for name, v in top5:
        print(f"  {v['pair']}: p_success={v['p_success']:.3f} mean_Hstar_end={v['mean_Hstar_end']:.3f}")


if __name__ == "__main__":
    main()
