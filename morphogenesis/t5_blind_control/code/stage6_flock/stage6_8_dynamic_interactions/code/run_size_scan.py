"""Finite-size check for the Stage 6.8 operating point (logs/
mesoscopic_criteria_predeclared.txt, ADDENDUM 4). Uncontrolled phenomenology
only; same six criteria, applied per episode."""
from __future__ import annotations

import numpy as np

from common_68 import (ModelParams, Lattice, polarization, dump_json, DATA_DIR,
                       RHO, OMEGA, PHASE_SEEDS, PHASE_NT, PHASE_BURN_IN)
from phase_metrics import summarize_run
from fov_dynamics import FovSimulator


def is_mesoscopic(p: dict, nn: int) -> bool:
    """The six frozen criteria, at episode level. M1/M3b scale with lattice
    size (they were stated for nn=100): a collective must be at least 10% of
    the flock and the largest component at most 70% of it. M2, M3a, M4a, M4b
    are size-free rates and are used verbatim."""
    t = p["mean_membership_turnover"]
    return bool(
        p["mean_largest_component"] >= 0.10 * nn
        and p["mean_component_lifetime"] >= 5
        and p["frac_time_largest_ge_90"] <= 0.20
        and p["mean_largest_component"] <= 0.70 * nn
        and (t == t and t >= 0.05)
        and p["mean_heading_entropy"] >= 0.40
    )


def main_op():
    """Operating-point scan at the best lattice size (ADDENDUM 5)."""
    nn = 400
    lattice = Lattice(nn=nn, nh=8)
    out = dict(protocol="stage6_8 L2 operating-point scan at nn=400", nt=PHASE_NT,
               burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS, cells=[])
    for beta in [0.75, 1.0, 1.25, 1.5]:
        for s in [1.0, 1.5, 2.0]:
            sim = FovSimulator(ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA), lattice)
            per_seed = []
            for seed in PHASE_SEEDS:
                res = sim.run(nt=PHASE_NT, seed=seed)
                st = summarize_run(res.z_hist, lattice.neighbor_ids, PHASE_BURN_IN, polarization)
                st["frac_time_largest_ge_90"] = _frac_global(res.z_hist, lattice, nn)
                per_seed.append(st)
            frac = float(np.mean([is_mesoscopic(p, nn) for p in per_seed]))
            cell = dict(nn=nn, beta=beta, s=s, mesoscopic_episode_fraction=frac, per_seed=per_seed)
            for k in per_seed[0]:
                v = np.array([d[k] for d in per_seed], float); v = v[~np.isnan(v)]
                cell[k + "__mean"] = float(v.mean()) if len(v) else float("nan")
            out["cells"].append(cell)
            print(f"nn=400 beta={beta:<5} s={s:<4} frac={frac:.2f} "
                  f"largest={cell['mean_largest_component__mean']:6.1f} "
                  f"ncomp={cell['mean_n_components__mean']:5.2f} "
                  f"life={cell['mean_component_lifetime__mean']:6.2f} "
                  f"turn={cell['mean_membership_turnover__mean']:.3f} "
                  f"H={cell['mean_heading_entropy__mean']:.3f} "
                  f"glob={cell['frac_time_largest_ge_90__mean']:.3f}", flush=True)
    dump_json(out, DATA_DIR / "phase_scan_op.json")


def main():
    out = dict(protocol="stage6_8 L2 finite-size scan", nt=PHASE_NT,
               burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS, cells=[])
    for nn in [100, 225, 400, 900]:
        lattice = Lattice(nn=nn, nh=8)
        for beta in [0.5, 0.75, 1.0, 1.5]:
            sim = FovSimulator(ModelParams(beta=beta, precB=RHO, precC=OMEGA), lattice)
            per_seed = []
            for seed in PHASE_SEEDS:
                res = sim.run(nt=PHASE_NT, seed=seed)
                # frac_time_largest_ge_90 is defined against 90% of the flock
                s = summarize_run(res.z_hist, lattice.neighbor_ids, PHASE_BURN_IN, polarization)
                s["frac_time_largest_ge_90"] = _frac_global(res.z_hist, lattice, nn)
                per_seed.append(s)
            frac = float(np.mean([is_mesoscopic(p, nn) for p in per_seed]))
            cell = dict(nn=nn, beta=beta, s=1.0, mesoscopic_episode_fraction=frac,
                        per_seed=per_seed)
            for k in per_seed[0]:
                v = np.array([d[k] for d in per_seed], float); v = v[~np.isnan(v)]
                cell[k + "__mean"] = float(v.mean()) if len(v) else float("nan")
            out["cells"].append(cell)
            print(f"nn={nn:<4} beta={beta:<5} mesoscopic_frac={frac:.2f} "
                  f"largest={cell['mean_largest_component__mean']:6.1f} "
                  f"({cell['mean_largest_component__mean']/nn:.2f}N) "
                  f"ncomp={cell['mean_n_components__mean']:5.2f} "
                  f"life={cell['mean_component_lifetime__mean']:6.2f} "
                  f"turn={cell['mean_membership_turnover__mean']:.3f} "
                  f"H={cell['mean_heading_entropy__mean']:.3f} "
                  f"glob={cell['frac_time_largest_ge_90__mean']:.3f}", flush=True)
    dump_json(out, DATA_DIR / "phase_scan_size.json")


def _frac_global(z_hist, lattice, nn):
    from phase_metrics import coherent_components
    hits = []
    for t in range(PHASE_BURN_IN, z_hist.shape[0]):
        comps = coherent_components(z_hist[t], lattice.neighbor_ids)
        hits.append((len(comps[0]) if comps else 0) >= 0.90 * nn)
    return float(np.mean(hits))


if __name__ == "__main__":
    import sys
    main_op() if "--op" in sys.argv else main()
