"""Episode screen at the two retained operating points (logs/
mesoscopic_criteria_predeclared.txt, ADDENDUM 3/5).

The six frozen criteria are applied to each uncontrolled realization. Seeds
that qualify are "mesoscopic episodes" and are the population every later
Stage 6.8 experiment draws from. Screening is UNCONTROLLED phenomenology only:
no detector, boundary, causal or control quantity is computed or importable
here. The dev/held-out split is by seed parity of rank, fixed here, before any
threshold is calibrated.
"""
from __future__ import annotations

import numpy as np

from common_68 import (ModelParams, Lattice, polarization, dump_json, DATA_DIR,
                       RHO, OMEGA, PHASE_NT, PHASE_BURN_IN)
from phase_metrics import summarize_run
from fov_dynamics import FovSimulator
from run_size_scan import is_mesoscopic, _frac_global

OP = {
    "OP1": dict(nn=400, beta=1.0, s=1.0),     # primary: frozen beta/rho/omega, only nn differs
    "OP2": dict(nn=400, beta=1.5, s=1.0),     # retained second regime
}
# Enlarged from 120 to 600 purely for statistical power after the 120-seed run
# yielded only 6 qualifying episodes at OP1 (data/episode_screen__120seeds.json,
# kept as a record). No criterion, threshold or operating point changed.
SCREEN_SEEDS = list(range(600))


def main():
    out = dict(protocol="stage6_8 episode screen", nt=PHASE_NT, burn_in=PHASE_BURN_IN,
               seeds=SCREEN_SEEDS, ops={})
    for name, cfg in OP.items():
        lattice = Lattice(nn=cfg["nn"], nh=8)
        sim = FovSimulator(ModelParams(beta=cfg["beta"], precB=cfg["s"] * RHO,
                                       precC=cfg["s"] * OMEGA), lattice)
        rows = []
        for seed in SCREEN_SEEDS:
            res = sim.run(nt=PHASE_NT, seed=seed)
            st = summarize_run(res.z_hist, lattice.neighbor_ids, PHASE_BURN_IN, polarization)
            st["frac_time_largest_ge_90"] = _frac_global(res.z_hist, lattice, cfg["nn"])
            st["seed"] = seed
            st["mesoscopic"] = is_mesoscopic(st, cfg["nn"])
            rows.append(st)
        qual = [r["seed"] for r in rows if r["mesoscopic"]]
        dev = qual[0::2]
        held = qual[1::2]
        out["ops"][name] = dict(**cfg, n_screened=len(rows), qualifying=qual,
                                fraction=len(qual) / len(rows),
                                dev_seeds=dev, heldout_seeds=held, per_seed=rows)
        print(f"{name}: {len(qual)}/{len(rows)} qualify ({len(qual)/len(rows):.2f}); "
              f"dev={dev} held={held}", flush=True)
    dump_json(out, DATA_DIR / "episode_screen.json")


if __name__ == "__main__":
    main()
