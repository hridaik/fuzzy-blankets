"""Same uncontrolled phase scan (identical metrics, identical frozen criteria)
applied to the L2 rung -- the heading-dependent FOV interaction graph.

Run because the L1 scan (data/phase_scan{,_cross,_refine}.json) found NO
mesoscopic cell anywhere on either predeclared grid or on the declared
resolution refinement: on the fixed undirected graph, coherent domains are
either non-persistent (beta<=0.25) or near-global (beta>=0.3), with nothing in
between. See PHASE_MAP.md. L2 is a genuinely different dynamical system --
under FOV a bird's own heading selects which sources are live, which is the
only self-coupling anywhere in this model family -- so its phase diagram has to
be mapped separately regardless.

Still uncontrolled phenomenology only. No boundary/causal/control quantity is
computed or importable here.
"""
from __future__ import annotations

import numpy as np

from common_68 import (ModelParams, lattice_100, polarization, dump_json, DATA_DIR,
                       BETA_GRID, RHO, OMEGA, S_GRID, PHASE_SEEDS, PHASE_NT, PHASE_BURN_IN)
from phase_metrics import summarize_run
from fov_dynamics import FovSimulator, GateParams


def scan_point(label, params, lattice, seeds, gate_params=None):
    sim = FovSimulator(params, lattice)
    per_seed = []
    for seed in seeds:
        res = sim.run(nt=PHASE_NT, seed=seed, gate_params=gate_params)
        per_seed.append(summarize_run(res.z_hist, lattice.neighbor_ids, PHASE_BURN_IN, polarization))
    agg = {}
    for k in per_seed[0]:
        v = np.array([d[k] for d in per_seed], dtype=float)
        v = v[~np.isnan(v)]
        agg[k + "__mean"] = float(v.mean()) if len(v) else float("nan")
        agg[k + "__sd"] = float(v.std()) if len(v) else float("nan")
    return dict(label=label, beta=params.beta, rho=params.precB, omega=params.precC,
                n_seeds=len(seeds), per_seed=per_seed, **agg)


def _line(tag, r):
    return (f"{tag} pol={r['mean_polarization__mean']:.3f} "
            f"largest={r['mean_largest_component__mean']:5.1f} "
            f"ncomp={r['mean_n_components__mean']:5.2f} "
            f"life={r['mean_component_lifetime__mean']:6.2f} "
            f"turn={r['mean_membership_turnover__mean']:.3f} "
            f"H={r['mean_heading_entropy__mean']:.3f} "
            f"glob={r['frac_time_largest_ge_90__mean']:.3f}")


def main_refine():
    """L2 resolution refinement inside the bracketed transition (logs/
    mesoscopic_criteria_predeclared.txt, ADDENDUM 2). Criteria unchanged."""
    lattice = lattice_100()
    grid = [(b, s) for b in [0.55, 0.60, 0.65, 0.70] for s in [0.50, 0.60]]
    grid += [(0.50, s) for s in [0.60, 0.65, 0.70]]
    out = dict(protocol="stage6_8 phase scan, L2 refinement inside bracketed transition",
               nt=PHASE_NT, burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS, refine=[])
    for beta, s in grid:
        r = scan_point(f"beta={beta}_s={s}",
                       ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA),
                       lattice, PHASE_SEEDS)
        r["s"] = s
        out["refine"].append(r)
        print(_line(f"[L2 refine] beta={beta:<5} s={s:<5}", r), flush=True)
    dump_json(out, DATA_DIR / "phase_scan_fov_refine.json")


def main():
    lattice = lattice_100()
    out = dict(protocol="stage6_8 phase scan, uncontrolled L2 (heading-dependent FOV)",
               nt=PHASE_NT, burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS, primary=[], cross=[])
    for beta in BETA_GRID:
        r = scan_point(f"beta={beta}", ModelParams(beta=beta, precB=RHO, precC=OMEGA),
                       lattice, PHASE_SEEDS)
        r["s"] = 1.0
        out["primary"].append(r)
        print(_line(f"[L2 primary] beta={beta:<5} s=1.0  ", r), flush=True)
    for beta in BETA_GRID:
        for s in S_GRID:
            if s == 1.0:
                continue
            r = scan_point(f"beta={beta}_s={s}",
                           ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA),
                           lattice, PHASE_SEEDS)
            r["s"] = s
            out["cross"].append(r)
            print(_line(f"[L2 cross]   beta={beta:<5} s={s:<5}", r), flush=True)
    dump_json(out, DATA_DIR / "phase_scan_fov.json")
    print("wrote", DATA_DIR / "phase_scan_fov.json")


if __name__ == "__main__":
    import sys
    main_refine() if "--refine" in sys.argv else main()
