"""Phase 5A greedy escalation beyond k=2 (exploratory, not pre-registered --
the brief explicitly allows greedy search for k>2 when exhaustive search is
infeasible/uninformative). Candidate pool restricted to the same top-10
shortlist used for the k=2 search, for tractability; documented as such."""
from __future__ import annotations

import sys
from pathlib import Path

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
MAX_K = 6


def evaluate(actuators, I0, h_star, z_t0, lattice):
    Hstar_end = np.zeros(N_REPLICATES)
    Hstar_rel = np.zeros(N_REPLICATES)
    min_coh = np.zeros(N_REPLICATES)
    lineage_end = np.zeros(N_REPLICATES)
    for r in range(N_REPLICATES):
        seed = BASE_SEED_OFFSET + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U)
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
    return dict(mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
                p_success_and_integrity=float((success & integrity).mean()),
                mean_Hstar_release=float(Hstar_rel.mean()), mean_min_coherence=float(min_coh.mean()),
                mean_lineage_end=float(lineage_end.mean()))


def main():
    d = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    rm = json.load(open(d / "phase4_5_response_map.json"))
    k2 = json.load(open(d / "phase5_k2_search.json"))
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    data = np.load(d / "canonical_snapshot.npz")
    I0 = np.array(rm["I0"])
    h_star = rm["h_star"]
    t0 = meta["t0"]
    z_t0 = data["z_hist_full"][t0]
    lattice = Lattice(nn=100, nh=8)

    shortlist = k2["shortlist"]
    current = [67, 57]  # best k=2 pair
    history = [dict(k=2, actuators=list(current), **evaluate(current, I0, h_star, z_t0, lattice))]
    print("k=2 seed:", history[-1])

    remaining = [b for b in shortlist if b not in current]
    t_start = time.time()
    while len(current) < MAX_K and remaining:
        best_add, best_metrics = None, None
        for cand in remaining:
            trial = current + [cand]
            m = evaluate(trial, I0, h_star, z_t0, lattice)
            if best_metrics is None or m["mean_Hstar_end"] > best_metrics["mean_Hstar_end"]:
                best_add, best_metrics = cand, m
        current = current + [best_add]
        remaining.remove(best_add)
        history.append(dict(k=len(current), actuators=list(current), **best_metrics))
        print(f"k={len(current)} actuators={current}: mean_Hstar_end={best_metrics['mean_Hstar_end']:.3f} "
              f"p_success={best_metrics['p_success']:.3f} elapsed={time.time()-t_start:.1f}s")
        if best_metrics["p_success"] >= 0.5:
            print("Success threshold reached; stopping greedy search.")
            break

    out_dir = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    with open(out_dir / "phase5_greedy_k.json", "w") as f:
        json.dump(dict(shortlist=shortlist, T_u=T_U, T_r=T_R, n_replicates=N_REPLICATES, history=history), f, indent=1)


if __name__ == "__main__":
    main()
