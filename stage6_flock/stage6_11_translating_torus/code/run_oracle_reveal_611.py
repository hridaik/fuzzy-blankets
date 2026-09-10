"""Stage 6.11 oracle reveal (task brief item 18). Run LAST: every inference
decision (detection, lineage, thingness thresholds, B^pred, B^causal, B^C,
actuator selection) is already frozen by the time this script runs, and
nothing here feeds back into any of them.

Uses the same val-episode snapshot as run_predictive_boundary_611.py and
run_causal_budget_sensitivity_611.py, so the oracle reveal is directly
comparable to the certified B^pred and the sampled B^causal already on disk.
"""
from __future__ import annotations

import json

import numpy as np

from common_611 import (
    DATA_DIR, L_BOX, dump_json, resolved_params, BETA_610, S_610,
    N_BIRDS, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY,
)
from moving_flock_611 import MovingFlock611
from detect_69 import propose
import oracle_611 as O


def main():
    d = np.load(DATA_DIR / "observational_corpus_611__val.npz")
    r_hist, z_hist = d["r_hist"][0], d["z_hist"][0]
    t0 = 90
    r_t, z_t = r_hist[t0], z_hist[t0]
    z_window = z_hist[max(0, t0 - 5):t0 + 1]
    cands = propose(r_t, z_window, L_BOX)
    members = cands[0]

    pm = resolved_params(BETA_610, S_610)
    mf = MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                         social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)

    pb = json.loads((DATA_DIR / "predictive_boundary_611.json").read_text())
    B_pred = pb["M_obs_20"]["boundary"]["B"]

    cb_path = DATA_DIR / "causal_budget_sensitivity_611.json"
    if cb_path.exists():
        cb = json.loads(cb_path.read_text())
        ref_key = "rollouts40_repeats3"
        B_causal = cb[ref_key]["B_causal"] if ref_key in cb else next(iter(cb.values()))["B_causal"]
    else:
        B_causal = []
    B_C = []  # control interface not evaluated at this static snapshot (needs a live episode)

    print(f"[oracle_reveal_611] candidate size={len(members)}, B_pred={B_pred}, B_causal={B_causal}")
    report = O.reveal_snapshot(mf, r_t, z_t, members, B_pred, B_causal, None, B_C)
    print(f"[oracle_reveal_611] |B_D_true|={len(report['B_D_true'])}")
    for name, cmp in report["vs_BD"].items():
        print(f"  {name} vs B_D: precision={cmp['precision']:.3f} recall={cmp['recall']:.3f} "
              f"jaccard={cmp['jaccard']:.3f} (hat={cmp['size_hat']}, true={cmp['size_true']})")
    ei = report["estimation_vs_identifiability"]
    print(f"  B_causal_sampled vs exact: jaccard={ei['B_causal_sampled_vs_exact']['jaccard']:.3f}")
    print(f"  B_causal_exact vs B_D:     jaccard={ei['B_causal_exact_vs_BD']['jaccard']:.3f}")

    dump_json(dict(t0=t0, candidate_size=len(members), members=members.tolist(),
                    B_pred=B_pred, B_causal_sampled=B_causal, **report),
              DATA_DIR / "oracle_reveal_611.json")
    print(f"[oracle_reveal_611] wrote {DATA_DIR / 'oracle_reveal_611.json'}")


if __name__ == "__main__":
    main()
