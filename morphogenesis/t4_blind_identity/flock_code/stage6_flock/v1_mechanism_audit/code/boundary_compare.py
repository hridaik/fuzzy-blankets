"""Part C: compare B^F (spectral), B^D (dynamical), and B^C (empirical control
response) on the canonical flock, using the already-computed Phase 4 k=1
response map (data/protocol_v1/phase4_5_response_map.json) -- no new
simulation needed for this part.
"""
from __future__ import annotations

import json
import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, load_phase4_response_map, dump_json
from dynamical_shell import one_hop_neighbors, graph_distance_from_set


def jaccard(a, b):
    sa, sb = set(a.tolist()) if hasattr(a, "tolist") else set(a), set(b.tolist()) if hasattr(b, "tolist") else set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def main():
    c = load_canonical()
    lattice, I0 = c["lattice"], c["I0"]
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0 = np.array(ds["B_D0"])
    B_F0 = np.array(ds["B_F0"])
    dist = np.array(ds["graph_distance_from_I0"])

    overlap = np.intersect1d(B_F0, B_D0)
    out = dict(
        size_B_F0=len(B_F0), size_B_D0=len(B_D0), size_overlap=len(overlap),
        overlap_members=overlap.tolist(),
        frac_of_BF_in_BD=float(len(overlap) / len(B_F0)) if len(B_F0) else None,
        frac_of_BD_in_BF=float(len(overlap) / len(B_D0)) if len(B_D0) else None,
        jaccard_BF_BD=jaccard(B_F0, B_D0),
    )

    # Response-map (k=1 exhaustive) join with distance / B^F / B^D membership.
    rm = load_phase4_response_map()
    results = {int(k): v for k, v in rm["results"].items()}
    rows = []
    for bird, v in results.items():
        rows.append(dict(
            bird=bird,
            mean_Hstar_end=v["mean_Hstar_end"],
            p_success=v["p_success"],
            dynamical_distance=int(dist[bird]),
            in_B_F0=bool(bird in B_F0.tolist()),
            in_B_D0=bool(bird in B_D0.tolist()),
        ))
    rows.sort(key=lambda r: -r["mean_Hstar_end"])
    out["response_by_distance"] = rows

    # Empirical control-interface candidate B^C: birds meeting some fraction of
    # the max observed single-actuator response (not "the top responder" alone,
    # since with continuous-valued small responses a single cutoff is somewhat
    # arbitrary -- report both the max-responder and a top-decile set).
    resp = np.array([r["mean_Hstar_end"] for r in rows])
    birds_sorted = np.array([r["bird"] for r in rows])
    n_top_decile = max(1, len(birds_sorted) // 10)
    B_C_top_decile = birds_sorted[:n_top_decile]
    out["B_C_top_decile"] = B_C_top_decile.tolist()
    out["B_C_top_decile_vs_B_D0_jaccard"] = jaccard(B_C_top_decile, B_D0)
    out["B_C_top_decile_vs_B_F0_jaccard"] = jaccard(B_C_top_decile, B_F0)

    # Correlation between response magnitude and dynamical distance (Spearman,
    # computed by hand to avoid a scipy dependency).
    d_all = np.array([r["dynamical_distance"] for r in rows], dtype=float)
    r_all = np.array([r["mean_Hstar_end"] for r in rows], dtype=float)
    def spearman(x, y):
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        rx -= rx.mean(); ry -= ry.mean()
        denom = np.sqrt((rx**2).sum() * (ry**2).sum())
        return float((rx * ry).sum() / denom) if denom > 0 else float("nan")
    out["spearman_response_vs_distance"] = spearman(d_all, r_all)

    # Baseline-ensemble check: for a handful of OTHER qualifying baseline
    # flocks (not just canonical), recompute B^F and B^D at their own t0 and
    # report overlap -- tests whether the canonical flock's weak B^F/B^D
    # overlap is typical or a quirk of n=2 boundary size.
    from analysis.baseline_characterization import find_qualifying_t0
    from flock_sim.simulation import run_simulation
    from flock_sim.spectral import analyze_window
    ensemble_rows = []
    TW = 5
    for seed in range(0, 12):
        res = run_simulation(nn=100, nt=60, seed=seed, lattice=lattice)
        q = find_qualifying_t0(res.z_hist)
        if q is None:
            continue
        t0s, I0s = q["t0"], np.array(q["I0"])
        window = res.z_hist[t0s - TW + 1: t0s + 1]
        sr = analyze_window(window, refclust=I0s)
        B_F0s = sr.boundary_nodes
        B_D0s = one_hop_neighbors(lattice, I0s)
        ov = np.intersect1d(B_F0s, B_D0s)
        ensemble_rows.append(dict(
            seed=seed, t0=int(t0s), size_I0=len(I0s), eigengap=float(sr.eigengap),
            size_B_F0=len(B_F0s), size_B_D0=len(B_D0s), size_overlap=len(ov),
            jaccard=jaccard(B_F0s, B_D0s),
        ))
    out["baseline_ensemble_overlap"] = ensemble_rows
    if ensemble_rows:
        jaccards = np.array([r["jaccard"] for r in ensemble_rows])
        out["baseline_ensemble_jaccard_mean"] = float(jaccards.mean())
        out["baseline_ensemble_jaccard_median"] = float(np.median(jaccards))

    dump_json(out, AUDIT_DIR / "data" / "boundary_compare.json")
    print(f"|B^F_0 ∩ B^D_0| = {len(overlap)} / |B^F_0|={len(B_F0)}, |B^D_0|={len(B_D0)}, "
          f"Jaccard={out['jaccard_BF_BD']:.3f}")
    print(f"Spearman(response, dynamical_distance) = {out['spearman_response_vs_distance']:.3f}")
    print(f"Baseline ensemble (n={len(ensemble_rows)}): mean Jaccard(B^F,B^D) = "
          f"{out.get('baseline_ensemble_jaccard_mean', float('nan')):.3f}")
    for r in ensemble_rows:
        print(" ", r)


if __name__ == "__main__":
    main()
