"""Stage 6.11 causal-probe budget-sensitivity check (task brief item 11:
"perform a small budget-sensitivity check" against the Stage 6.10 reference
budget of 40 rollouts x 3 repeats).

EVALUATION-SIDE driver. Fixes one real snapshot (from the observational
corpus, primary regime) and one detected candidate, then re-estimates
B_causal at each (rollouts, repeats) cell in
`intervention_api_611.BUDGET_SENSITIVITY_GRID`, reporting how the estimated
interface (size, CI width, membership) changes with budget.
"""
from __future__ import annotations

import numpy as np

from common_611 import DATA_DIR, L_BOX, dump_json
from moving_flock_611 import MovingFlock611
from common_611 import resolved_params, BETA_610, S_610, N_BIRDS, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY
from detect_69 import propose
from intervention_api_611 import FiniteProbeMoving611, near_exterior, BUDGET_SENSITIVITY_GRID
import probing_611 as PR


def main():
    d = np.load(DATA_DIR / "observational_corpus_611__val.npz")
    r_hist, z_hist = d["r_hist"][0], d["z_hist"][0]
    t0 = 90
    r_t, z_t = r_hist[t0], z_hist[t0]
    z_window = z_hist[max(0, t0 - 5):t0 + 1]
    cands = propose(r_t, z_window, L_BOX)
    members = cands[0]
    print(f"[budget_sensitivity] candidate size={len(members)}", flush=True)

    pm = resolved_params(BETA_610, S_610)
    mf = MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                         social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)
    exterior_pool = near_exterior(mf, r_t, members, radius_factor=1.5)
    print(f"[budget_sensitivity] exterior pool size={len(exterior_pool)}", flush=True)
    rng = np.random.default_rng(0)

    results = {}
    for rollouts, repeats in BUDGET_SENSITIVITY_GRID:
        probes = [FiniteProbeMoving611(mf, r_t, n_rollouts=rollouts, seed=10_000 + rep)
                  for rep in range(repeats)]
        out = PR.probe_sources(probes, members, exterior_pool, z_t, rng, n_boot=100)
        widths = [res["ci_hi"] - res["ci_lo"] for res in out["C"].values()]
        key = f"rollouts{rollouts}_repeats{repeats}"
        results[key] = dict(rollouts=rollouts, repeats=repeats, total_rollouts_per_source=rollouts * repeats * 3,
                             B_causal=out["B_causal"], n_B_causal=len(out["B_causal"]),
                             mean_ci_width=float(np.mean(widths)), max_ci_width=float(np.max(widths)))
        print(f"  {key}: |B_causal|={len(out['B_causal'])} mean_ci_width={np.mean(widths):.4f} "
              f"B_causal={out['B_causal']}", flush=True)

    dump_json(results, DATA_DIR / "causal_budget_sensitivity_611.json")
    print(f"[budget_sensitivity] wrote {DATA_DIR / 'causal_budget_sensitivity_611.json'}")


if __name__ == "__main__":
    main()
