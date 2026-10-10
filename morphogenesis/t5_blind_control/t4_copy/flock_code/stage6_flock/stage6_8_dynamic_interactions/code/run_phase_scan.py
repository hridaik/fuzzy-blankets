"""Stage 6.8 phase scan (task brief section 2).

Maps the UNCONTROLLED phenomenology of the L1 ladder rung (fixed Moore graph,
varying beta) across the predeclared grid, plus the secondary (rho, omega) =
s*(15, 3) precision-scale grid. Writes data/phase_scan.json.

No boundary, causal-discovery or control metric is computed here, and none is
importable from this script. `PHASE_MAP.md` is written from this output alone.
"""
from __future__ import annotations

import time

import numpy as np

from common_68 import (ModelParams, lattice_100, polarization, dump_json, DATA_DIR,
                       BETA_GRID, RHO, OMEGA, S_GRID, PHASE_SEEDS, PHASE_NT, PHASE_BURN_IN)
from phase_metrics import summarize_run

from flock_sim.simulation import run_simulation


def scan_point(label: str, params: ModelParams, lattice, seeds) -> dict:
    per_seed = []
    for seed in seeds:
        res = run_simulation(nn=100, nt=PHASE_NT, seed=seed, params=params, lattice=lattice)
        per_seed.append(summarize_run(res.z_hist, lattice.neighbor_ids, PHASE_BURN_IN, polarization))
    keys = per_seed[0].keys()
    agg = {}
    for k in keys:
        vals = np.array([d[k] for d in per_seed], dtype=float)
        vals = vals[~np.isnan(vals)]
        agg[k + "__mean"] = float(vals.mean()) if len(vals) else float("nan")
        agg[k + "__sd"] = float(vals.std()) if len(vals) else float("nan")
    return dict(label=label, beta=params.beta, rho=params.precB, omega=params.precC,
                n_seeds=len(seeds), per_seed=per_seed, **agg)


def main_cross():
    """Secondary scan: the full predeclared (beta, s) cross (task brief section 2).
    Run only after the primary beta grid was found to contain no intermediate
    regime, against criteria frozen in logs/mesoscopic_criteria_predeclared.txt."""
    lattice = lattice_100()
    out = dict(protocol="stage6_8 phase scan, secondary (beta, s) cross",
               nt=PHASE_NT, burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS, cross=[])
    for beta in BETA_GRID:
        for s in S_GRID:
            p = ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA)
            r = scan_point(f"beta={beta}_s={s}", p, lattice, PHASE_SEEDS)
            r["s"] = s
            out["cross"].append(r)
            print(f"beta={beta:<5} s={s:<5} pol={r[chr(39)+chr(39)]}" if False else
                  f"beta={beta:<5} s={s:<5} "
                  f"pol={r['mean_polarization__mean']:.3f} "
                  f"largest={r['mean_largest_component__mean']:5.1f} "
                  f"ncomp={r['mean_n_components__mean']:5.2f} "
                  f"life={r['mean_component_lifetime__mean']:6.2f} "
                  f"turn={r['mean_membership_turnover__mean']:.3f} "
                  f"H={r['mean_heading_entropy__mean']:.3f} "
                  f"glob={r['frac_time_largest_ge_90__mean']:.3f}", flush=True)
    dump_json(out, DATA_DIR / "phase_scan_cross.json")


def main_refine():
    """Resolution refinement inside the bracketed transition (logs/
    mesoscopic_criteria_predeclared.txt, ADDENDUM 1). Criteria unchanged."""
    lattice = lattice_100()
    grid = [(b, s) for b in [0.30, 0.35, 0.40, 0.45] for s in [1.0, 1.25]]
    grid += [(0.25, s) for s in [1.10, 1.20, 1.30, 1.40]]
    out = dict(protocol="stage6_8 phase scan, refinement inside bracketed transition",
               nt=PHASE_NT, burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS, refine=[])
    for beta, s in grid:
        p = ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA)
        r = scan_point(f"beta={beta}_s={s}", p, lattice, PHASE_SEEDS)
        r["s"] = s
        out["refine"].append(r)
        print(f"beta={beta:<5} s={s:<5} "
              f"pol={r['mean_polarization__mean']:.3f} "
              f"largest={r['mean_largest_component__mean']:5.1f} "
              f"ncomp={r['mean_n_components__mean']:5.2f} "
              f"life={r['mean_component_lifetime__mean']:6.2f} "
              f"turn={r['mean_membership_turnover__mean']:.3f} "
              f"H={r['mean_heading_entropy__mean']:.3f} "
              f"glob={r['frac_time_largest_ge_90__mean']:.3f}", flush=True)
    dump_json(out, DATA_DIR / "phase_scan_refine.json")


def main():
    lattice = lattice_100()
    t0 = time.time()
    out = dict(
        protocol="stage6_8 phase scan, uncontrolled L1 (fixed Moore graph)",
        nt=PHASE_NT, burn_in=PHASE_BURN_IN, seeds=PHASE_SEEDS,
        primary=[], secondary=[],
    )
    for beta in BETA_GRID:
        p = ModelParams(beta=beta, precB=RHO, precC=OMEGA)
        r = scan_point(f"beta={beta}", p, lattice, PHASE_SEEDS)
        out["primary"].append(r)
        print(f"[primary] beta={beta:<5} pol={r['mean_polarization__mean']:.3f} "
              f"largest={r['mean_largest_component__mean']:.1f} "
              f"ncomp={r['mean_n_components__mean']:.2f} "
              f"life={r['mean_component_lifetime__mean']:.2f} "
              f"turn={r['mean_membership_turnover__mean']:.3f} "
              f"H={r['mean_heading_entropy__mean']:.3f} "
              f"t>.9={r['frac_time_pol_above_0_9__mean']:.3f} "
              f"global={r['frac_time_largest_ge_90__mean']:.3f}", flush=True)
    for s in S_GRID:
        p = ModelParams(beta=1.0, precB=s * RHO, precC=s * OMEGA)
        r = scan_point(f"s={s}", p, lattice, PHASE_SEEDS)
        out["secondary"].append(r)
        print(f"[secondary] s={s:<5} (rho={s*RHO},omega={s*OMEGA}) "
              f"pol={r['mean_polarization__mean']:.3f} "
              f"largest={r['mean_largest_component__mean']:.1f} "
              f"ncomp={r['mean_n_components__mean']:.2f} "
              f"life={r['mean_component_lifetime__mean']:.2f} "
              f"turn={r['mean_membership_turnover__mean']:.3f} "
              f"global={r['frac_time_largest_ge_90__mean']:.3f}", flush=True)
    out["elapsed_s"] = time.time() - t0
    dump_json(out, DATA_DIR / "phase_scan.json")
    print(f"wrote {DATA_DIR/'phase_scan.json'} in {out['elapsed_s']:.1f}s")


if __name__ == "__main__":
    import sys
    if "--cross" in sys.argv:
        main_cross()
    elif "--refine" in sys.argv:
        main_refine()
    else:
        main()
