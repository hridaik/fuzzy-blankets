"""Part A3: canonical-flock representativeness. The frozen baseline sweep
(data/baseline_v1/baseline_rows.json) recorded t0, |I0|, eigengap, coherence
for each of the 161 qualifying seeds, but NOT lambda2 itself or |B0^F|
(boundary size) -- both are recomputed here by re-running each qualifying
seed to its own t0 (deterministic given the seed; bit-identical to the
original baseline run) and calling analyze_window once. No control code is
invoked; this does not touch or overwrite any protocol_v1 data.
"""
from __future__ import annotations

import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, load_baseline_rows, dump_json, TW, percentile_rank
from flock_sim.simulation import run_simulation
from flock_sim.spectral import analyze_window
from flock_sim.lattice import Lattice


def main():
    rows = load_baseline_rows()
    found_rows = [r for r in rows if r["found"]]
    lattice = Lattice(nn=100, nh=8)

    recomputed = []
    for r in found_rows:
        seed, t0 = r["seed"], r["t0"]
        res = run_simulation(nn=100, nt=max(t0 + 1, 60), seed=seed, lattice=lattice)
        window = res.z_hist[t0 - TW + 1: t0 + 1]
        sr = analyze_window(window)
        recomputed.append(dict(seed=seed, t0=t0, size=r["size"], eigengap=r["eigengap"],
                                coherence=r["coherence"], lambda2=float(sr.lambda2),
                                lambda3=float(sr.lambda3), size_boundary=len(sr.boundary_nodes)))

    c = load_canonical()
    canon_t0 = c["t0"]
    canon_window = c["z_hist_full"][canon_t0 - TW + 1: canon_t0 + 1]
    sr_canon = analyze_window(canon_window, refclust=c["I0"])
    canon = dict(seed=2, t0=canon_t0, size=len(c["I0"]), eigengap=float(sr_canon.eigengap),
                 coherence=1.0, lambda2=float(sr_canon.lambda2), lambda3=float(sr_canon.lambda3),
                 size_boundary=len(sr_canon.boundary_nodes))

    pop_t0 = np.array([x["t0"] for x in recomputed])
    pop_size = np.array([x["size"] for x in recomputed])
    pop_boundary = np.array([x["size_boundary"] for x in recomputed])
    pop_coherence = np.array([x["coherence"] for x in recomputed])
    pop_lambda2 = np.array([x["lambda2"] for x in recomputed])
    pop_eigengap = np.array([x["eigengap"] for x in recomputed])

    out = dict(
        n_population=len(recomputed),
        canonical=canon,
        population_medians=dict(
            t0=float(np.median(pop_t0)), size=float(np.median(pop_size)),
            size_boundary=float(np.median(pop_boundary)), coherence=float(np.median(pop_coherence)),
            lambda2=float(np.median(pop_lambda2)), eigengap=float(np.median(pop_eigengap)),
        ),
        canonical_percentile_rank=dict(
            t0=percentile_rank(canon["t0"], pop_t0),
            size=percentile_rank(canon["size"], pop_size),
            size_boundary=percentile_rank(canon["size_boundary"], pop_boundary),
            coherence=percentile_rank(canon["coherence"], pop_coherence),
            lambda2=percentile_rank(canon["lambda2"], pop_lambda2),
            eigengap=percentile_rank(canon["eigengap"], pop_eigengap),
        ),
        population=recomputed,
    )
    dump_json(out, AUDIT_DIR / "data" / "canonical_representativeness.json")

    print(f"n_population={len(recomputed)}")
    print("canonical:", canon)
    print("population medians:", out["population_medians"])
    print("canonical percentile ranks (0=lowest,100=highest in population):")
    for k, v in out["canonical_percentile_rank"].items():
        print(f"  {k}: {v:.1f}th percentile")


if __name__ == "__main__":
    main()
