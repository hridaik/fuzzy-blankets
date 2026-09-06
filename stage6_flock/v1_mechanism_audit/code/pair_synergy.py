"""Part E: exhaustive pair-synergy audit over all C(80,2)=3160 non-core-bird
pairs (not restricted to the V1 top-10 single-responder shortlist). Development
scale (n=10 replicates/pair, explicitly below the protocol's 50-replicate
development standard and far below the 200+ final-comparison target) --
documented as such, chosen purely for this session's compute/time budget given
3160 x 50 = 158,000 simulations would take much longer than 3160 x 10 = 31,600.
R_ij is defined as mean_Hstar_end (consistent with the response definition
already used throughout protocol_v1's phase4/phase5 scripts). Individual
per-bird R_i is taken directly from the existing, already-computed exhaustive
k=1 sweep (data/protocol_v1/phase4_5_response_map.json) using the SAME
common-random-number seed offset, so R_0 (baseline, no actuator) and R_i are
reused rather than re-simulated.
"""
from __future__ import annotations

import json
import time
from itertools import combinations

import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, load_phase4_response_map, dump_json, \
    T_U, T_R, BASE_SEED_OFFSET
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction

N_PAIR_REPLICATES = 10   # development scale; see module docstring


def main():
    c = load_canonical()
    lattice, I0, z_t0, h_star = c["lattice"], c["I0"], c["z_t0"], c["h_star"]
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0 = set(ds["B_D0"])
    B_F0 = set(ds["B_F0"])
    dist = np.array(ds["graph_distance_from_I0"])

    rm = load_phase4_response_map()
    R_i = {int(k): v["mean_Hstar_end"] for k, v in rm["results"].items()}
    non_core = sorted(R_i.keys())
    R_0 = 0.0  # baseline (no control) mean_Hstar_end at this canonical snapshot is exactly 0.0 (protocol_v1 phase3)

    pairs = list(combinations(non_core, 2))
    print(f"Running {len(pairs)} pairs x {N_PAIR_REPLICATES} replicates = "
          f"{len(pairs) * N_PAIR_REPLICATES} simulations")

    t_start = time.time()
    rows = []
    for idx, (a, b) in enumerate(pairs):
        Hstar_end = np.zeros(N_PAIR_REPLICATES)
        for r in range(N_PAIR_REPLICATES):
            seed = BASE_SEED_OFFSET + r
            interventions = make_pulse([a, b], h_star, t0=0, t_u=T_U)
            res = run_simulation(nn=100, nt=T_U, seed=seed, init_z=z_t0,
                                  interventions=interventions, lattice=lattice)
            Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        R_ij = float(Hstar_end.mean())
        S_ij = R_ij - (R_i[a] + R_i[b] - R_0)
        both_in_BD = (a in B_D0) and (b in B_D0)
        either_in_BF = (a in B_F0) or (b in B_F0)
        connected_patch = (b in lattice.neighbor_ids[a].tolist())  # spatially adjacent pair
        rows.append(dict(
            i=a, j=b, R_i=R_i[a], R_j=R_i[b], R_ij=R_ij, S_ij=S_ij,
            p_success_pair=float((Hstar_end >= 0.8).mean()),
            dist_i=int(dist[a]), dist_j=int(dist[b]),
            both_in_B_D0=both_in_BD, either_in_B_F0=either_in_BF,
            lattice_adjacent_pair=connected_patch,
        ))
        if (idx + 1) % 500 == 0:
            print(f"  {idx+1}/{len(pairs)} pairs done, elapsed={time.time()-t_start:.1f}s", flush=True)

    elapsed = time.time() - t_start
    rows_sorted = sorted(rows, key=lambda r: -r["R_ij"])
    top20 = rows_sorted[:20]
    top20_synergy = sorted(rows, key=lambda r: -r["S_ij"])[:20]

    out = dict(
        n_pairs=len(pairs), n_replicates=N_PAIR_REPLICATES, elapsed_s=elapsed,
        R_0=R_0, T_u=T_U,
        top20_by_R_ij=top20, top20_by_S_ij=top20_synergy,
        all_pairs=rows,
    )
    dump_json(out, AUDIT_DIR / "data" / "pair_synergy.json")

    R_ij_arr = np.array([r["R_ij"] for r in rows])
    S_ij_arr = np.array([r["S_ij"] for r in rows])
    print(f"\nDone in {elapsed:.1f}s. R_ij: mean={R_ij_arr.mean():.4f} max={R_ij_arr.max():.4f} "
          f"(V1's best-shortlist-pair R was 0.149 for {{67,57}})")
    print(f"S_ij (control-response synergy): mean={S_ij_arr.mean():.4f} max={S_ij_arr.max():.4f} "
          f"min={S_ij_arr.min():.4f}")
    print("Top 10 pairs by R_ij:")
    for r in top20[:10]:
        print(f"  ({r['i']},{r['j']}): R_ij={r['R_ij']:.3f} S_ij={r['S_ij']:.3f} "
              f"both_in_BD0={r['both_in_B_D0']} dist=({r['dist_i']},{r['dist_j']})")
    print("Top 10 pairs by synergy S_ij:")
    for r in top20_synergy[:10]:
        print(f"  ({r['i']},{r['j']}): R_ij={r['R_ij']:.3f} S_ij={r['S_ij']:.3f} "
              f"both_in_BD0={r['both_in_B_D0']} dist=({r['dist_i']},{r['dist_j']})")
    n_meeting_bar = sum(1 for r in rows if r["p_success_pair"] >= 0.5)
    print(f"Pairs meeting P(success)>=0.5 at n={N_PAIR_REPLICATES}: {n_meeting_bar} / {len(rows)}")


if __name__ == "__main__":
    main()
