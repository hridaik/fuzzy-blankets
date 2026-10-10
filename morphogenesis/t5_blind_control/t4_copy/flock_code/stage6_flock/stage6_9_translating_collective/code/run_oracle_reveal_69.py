"""ORACLE REVEAL for Stage 6.9. Run only after `run_boundary_69.py` has written
its results to disk; reads that file and never modifies it.

Reports, separately and never collapsed:
  estimation error   Bhat^{causal,sampled}  vs  B^{causal,exact}
  identifiability    B^{causal,exact}       vs  B_t^D
  structural         Bhat^{causal,sampled}  vs  B_t^D
  predictive         Bhat^{pred}            vs  B_t^D

and, specific to this stage, interface turnover measured BOTH in world
coordinates and in the co-moving frame: an interface that is merely carried
along with the group is not the same thing as an interface that changes.
"""
from __future__ import annotations

import numpy as np

from common_69 import (ModelParams, dump_json, load_json, DATA_DIR, N_BIRDS, L_BOX,
                       R_RADIUS, V_SPEED, BETA, RHO, OMEGA)
from moving_flock import MovingFlock
from intervention_api_69 import ExactPropagatorMoving

TAU_EXACT = 1e-9


def compare(a, b):
    a, b = set(int(x) for x in a), set(int(x) for x in b)
    tp = len(a & b)
    return dict(precision=(tp / len(a) if a else (1.0 if not b else 0.0)),
                recall=(tp / len(b) if b else (1.0 if not a else 0.0)),
                jaccard=(len(a & b) / len(a | b) if (a or b) else 1.0),
                size_hat=len(a), size_true=len(b), size_error=len(a) - len(b))


def comoving_ids(mf, r_t, centre, ids):
    """Interface members expressed as offsets from the collective's own centre,
    rounded to a coarse grid. Two interfaces with the same co-moving signature
    are 'the same interface, carried along'."""
    d = (r_t[np.asarray(sorted(int(i) for i in ids))] - centre + mf.L / 2) % mf.L - mf.L / 2
    return {tuple(np.round(x / (mf.R / 2)).astype(int)) for x in d}


def main():
    frozen = load_json(DATA_DIR / "boundary_69.json")
    mf = MovingFlock(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED,
                     params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))
    out = dict(protocol="stage6_9 oracle reveal", source="boundary_69.json",
               model=frozen["model"], runs=[])
    by_seed = {}
    for r in frozen["runs"]:
        by_seed.setdefault(r["seed"], []).append(r)

    for seed, runs in by_seed.items():
        nt = max(r["t"] for r in runs) + 2
        res = mf.run(nt=nt, seed=seed)
        prev = None
        for r in sorted(runs, key=lambda x: x["t"]):
            t, I = r["t"], np.array(sorted(r["I"]))
            r_t, z_t = res.r_hist[t], res.z_hist[t]
            BD = mf.oracle_B_D(r_t, z_t, I).tolist()
            ep = ExactPropagatorMoving(mf, r_t)
            vals = {}
            for j in r["probe_candidates"]:
                others = [h for h in range(4) if h != int(z_t[int(j)])]
                vals[int(j)] = float(np.mean([ep.exact(I, int(j), zp, z_t)["D_do_joint"]
                                              for zp in others]))
            B_exact = sorted([j for j, v in vals.items() if v > TAU_EXACT])
            centre = np.asarray(r["centroid"])
            rec = dict(seed=seed, t=t, I_size=r["I_size"], B_D=BD,
                       B_causal_exact=B_exact, B_causal_sampled=r["B_causal"],
                       B_pred=r["B_pred"],
                       estimation_error=compare(r["B_causal"], B_exact),
                       identifiability=compare(B_exact, BD),
                       structural_agreement=compare(r["B_causal"], BD),
                       predictive_vs_BD=compare(r["B_pred"], BD),
                       predictive_vs_causal_exact=compare(r["B_pred"], B_exact),
                       n_probe_candidates=len(r["probe_candidates"]),
                       probe_budget=r["budget"])
            if prev is not None and prev["t"] == t - 1:
                a, b = set(prev["B_D"]), set(BD)
                rec["BD_world_turnover"] = len(b - a) / max(1, len(b))
                ca = comoving_ids(mf, res.r_hist[t - 1], np.asarray(prev["centroid"]), prev["B_D"])
                cb = comoving_ids(mf, r_t, centre, BD)
                rec["BD_comoving_turnover"] = len(cb - ca) / max(1, len(cb))
                sa, sb = set(prev["B_causal_sampled"]), set(r["B_causal"])
                rec["Bcausal_world_turnover"] = len(sb - sa) / max(1, len(sb))
            rec["centroid"] = centre.tolist()
            prev = rec
            out["runs"].append(rec)
            print(f"seed {seed:<3} t={t:<4} |B_D|={len(BD):<3} |exact|={len(B_exact):<3} "
                  f"|sampled|={len(r['B_causal']):<3} |pred|={len(r['B_pred']):<3} | "
                  f"est J={rec['estimation_error']['jaccard']:.2f} "
                  f"ident J={rec['identifiability']['jaccard']:.2f} "
                  f"struct J={rec['structural_agreement']['jaccard']:.2f} "
                  f"pred J={rec['predictive_vs_BD']['jaccard']:.2f}", flush=True)
    dump_json(out, DATA_DIR / "oracle_reveal_69.json")
    print("wrote", DATA_DIR / "oracle_reveal_69.json")


if __name__ == "__main__":
    main()
