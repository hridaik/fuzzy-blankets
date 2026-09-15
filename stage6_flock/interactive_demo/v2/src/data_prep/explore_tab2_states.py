"""Investigate all 8 audited states to pick a better Tab 2 example, and
verify a deterministic replay of do_influence against the stored kl values.

Run with an interpreter that has numpy (e.g. /usr/bin/python3).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "stage6_10_emergence_adaptive_control/code"))
sys.path.insert(0, str(ROOT / "stage6_8_dynamic_interactions/code"))

from episode_data import make_simulator, run_episode  # noqa: E402
import reference_truth as rt  # noqa: E402
import numpy as np  # noqa: E402

trace = json.load(open(ROOT / "stage6_10_emergence_adaptive_control/data/audit_trace.json"))
hyp = json.load(open(ROOT / "stage6_10_emergence_adaptive_control/data/audit_hypotheses.json"))

sim = make_simulator(trace["operating_point"]["nn"], trace["operating_point"]["beta"], trace["operating_point"]["s"])
t0 = trace["t0"]
per_state = hyp["H3_kl_vs_authority"]["per_state"]

for i, ep in enumerate(trace["episodes"]):
    seed, h_star, I0 = ep["seed"], ep["h_star"], ep["I0"]
    step0 = ep["arms"]["adaptive_oracle"]["steps"][0]
    cands = [int(j) for j in step0["B_do"]]
    st = per_state[i]
    assert st["seed"] == seed

    res = run_episode(sim, seed, nt=t0 + 2, record_oracle=False)
    zt = np.array(res.z_hist[t0])

    kl_replay = []
    for j in cands:
        total, per = rt.do_influence(sim, zt, np.array(I0), j, agg="sum")
        kl_replay.append(total)
    kl_replay = np.array(kl_replay)
    kl_stored = np.array(st["kl"])
    max_err = float(np.max(np.abs(kl_replay - kl_stored)))

    auth2 = np.array(st["authority"]["2"])
    print(f"episode {i}: seed={seed} h_star={h_star} n_I0={len(I0)} n_cands={len(cands)} "
          f"max_replay_err={max_err:.2e} auth2_max={auth2.max():.4f} auth2_absmean={np.abs(auth2).mean():.5f} "
          f"kl_max={kl_stored.max():.4f} kl_nonzero_frac={(kl_stored>1e-4).mean():.2f} "
          f"heading_unique={len(set(zt.tolist()))}")
