"""Bridge from Part D/E to Part K2: now that the feasibility ladder has shown
the FULL dynamical shell B^D_0 (12 birds) achieves p_success=0.96 while every
individual bird and every pair (Part E, 3160/3160 pairs) fails, ask the more
useful question directly: how many of the 12 B^D_0 birds are actually needed,
if the search is restricted to the CORRECT candidate pool (unlike V1's
top-10-by-single-response shortlist, which was drawn from all 80 exterior
birds and only partially overlapped B^D_0)? Exhaustive k=1..3 within B^D_0
(12+66+220=298 combinations), then greedy k=4..12.
"""
from __future__ import annotations

import json
import time
from itertools import combinations

import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, dump_json, T_U, T_R, BASE_SEED_OFFSET, N_DEV, TW
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence
from flock_sim.spectral import analyze_window

N_REP = 30  # development scale, between V1's 50 (single conditions) and this larger combinatorial sweep


def evaluate(actuators, z_t0, I0, h_star, lattice, n_replicates=N_REP):
    Hstar_end = np.zeros(n_replicates)
    min_coh = np.zeros(n_replicates)
    lineage_end = np.zeros(n_replicates)
    for r in range(n_replicates):
        seed = BASE_SEED_OFFSET + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
        res = run_simulation(nn=100, nt=T_U, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        min_coh[r] = min(coherence(res.z_hist[t], I0) for t in range(T_U + 1))
        window = res.z_hist[T_U - TW + 1: T_U + 1]
        sr = analyze_window(window, refclust=I0)
        lineage_end[r] = len(np.intersect1d(I0, sr.core1_nodes)) / len(I0)
    success = Hstar_end >= 0.8
    integrity = (min_coh >= 0.8) & (lineage_end >= 0.5)
    return dict(mean_Hstar_end=float(Hstar_end.mean()), p_success=float(success.mean()),
                p_success_and_integrity=float((success & integrity).mean()),
                mean_min_coherence=float(min_coh.mean()), mean_lineage_end=float(lineage_end.mean()))


def main():
    c = load_canonical()
    lattice, I0, z_t0, h_star = c["lattice"], c["I0"], c["z_t0"], c["h_star"]
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0 = ds["B_D0"]

    t_start = time.time()
    exhaustive = {}
    for k in (1, 2, 3):
        best = None
        for combo in combinations(B_D0, k):
            m = evaluate(list(combo), z_t0, I0, h_star, lattice)
            if best is None or m["mean_Hstar_end"] > best[1]["mean_Hstar_end"]:
                best = (combo, m)
        exhaustive[k] = dict(best_actuators=list(best[0]), **best[1])
        print(f"k={k} exhaustive within B^D_0: best={best[0]} mean_Hstar_end={best[1]['mean_Hstar_end']:.3f} "
              f"p_success={best[1]['p_success']:.3f}  ({time.time()-t_start:.1f}s elapsed)")

    # greedy continuation k=4..12
    current = list(exhaustive[3]["best_actuators"])
    remaining = [b for b in B_D0 if b not in current]
    history = [dict(k=3, actuators=list(current), **{kk: exhaustive[3][kk] for kk in
               ("mean_Hstar_end", "p_success", "p_success_and_integrity", "mean_min_coherence", "mean_lineage_end")})]
    while len(current) < len(B_D0) and remaining:
        best_add, best_m = None, None
        for cand in remaining:
            trial = current + [cand]
            m = evaluate(trial, z_t0, I0, h_star, lattice)
            if best_m is None or m["mean_Hstar_end"] > best_m["mean_Hstar_end"]:
                best_add, best_m = cand, m
        current = current + [best_add]
        remaining.remove(best_add)
        history.append(dict(k=len(current), actuators=list(current), **best_m))
        print(f"k={len(current)} greedy: actuators={current} mean_Hstar_end={best_m['mean_Hstar_end']:.3f} "
              f"p_success={best_m['p_success']:.3f} p_success_and_integrity={best_m['p_success_and_integrity']:.3f} "
              f"({time.time()-t_start:.1f}s elapsed)")

    out = dict(B_D0=B_D0, n_replicates=N_REP, exhaustive_k1_3=exhaustive, greedy_history=history)
    dump_json(out, AUDIT_DIR / "data" / "shell_sparsification.json")

    # smallest k meeting p_success>=0.5 and >=0.8, restricted to this search path
    k_meet_05 = next((h["k"] for h in history if h["p_success"] >= 0.5), None)
    k_meet_08 = next((h["k"] for h in history if h["p_success"] >= 0.8), None)
    print(f"\nSmallest k (this greedy path within B^D_0) meeting p_success>=0.5: {k_meet_05}")
    print(f"Smallest k (this greedy path within B^D_0) meeting p_success>=0.8: {k_meet_08}")


if __name__ == "__main__":
    main()
