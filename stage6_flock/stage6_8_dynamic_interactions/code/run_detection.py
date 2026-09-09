"""Online candidate detection and lineage tracking (task brief sections 7-10).

Runs BOTH proposal methods -- the affinity/Louvain primary and the
spectral/coherence comparator -- side by side on the same single real
trajectory, one timestep at a time. Neither is privileged. Detection sees only
positions, headings and past trajectory; the control target does not exist yet
and the oracle graph is not importable from any module used here.
"""
from __future__ import annotations

import numpy as np

from common_68 import dump_json, load_json, DATA_DIR
from episode_data import make_simulator, run_episode, observation_record

import candidate_detection as cd
import spectral_proposal as sp
from tracker import LineageTracker

T_START, T_END = 20, 100


def run_one(sim, z_hist, t_start=T_START, t_end=T_END) -> dict:
    trackers = {"affinity_louvain": LineageTracker("affinity_louvain"),
                "spectral_coherence": LineageTracker("spectral_coherence")}
    per_t = []
    for t in range(t_start, t_end + 1):
        obs = observation_record(sim, z_hist, t)
        ok_a, all_a = cd.propose(obs)
        ok_s, all_s = sp.propose(obs)
        trackers["affinity_louvain"].update(ok_a)
        trackers["spectral_coherence"].update(ok_s)
        per_t.append(dict(
            t=t,
            affinity=dict(n_valid=len(ok_a), n_all=len(all_a),
                          sizes=[c.size for c in ok_a],
                          coherence=[c.coherence for c in ok_a],
                          compactness=[c.compactness for c in ok_a],
                          members=[c.members.tolist() for c in ok_a]),
            spectral=dict(n_valid=len(ok_s), n_all=len(all_s),
                          sizes=[c.size for c in ok_s],
                          coherence=[c.coherence for c in ok_s],
                          compactness=[c.compactness for c in ok_s],
                          members=[c.members.tolist() for c in ok_s]),
        ))
    return dict(per_t=per_t,
                lineages={k: v.summary() for k, v in trackers.items()})


def main():
    screen = load_json(DATA_DIR / "episode_screen.json")
    op = screen["ops"]["OP1"]
    sim = make_simulator(op["nn"], op["beta"], op["s"])
    seeds = op["dev_seeds"] + op["heldout_seeds"]
    out = dict(protocol="stage6_8 online candidate detection + tracking",
               operating_point={k: op[k] for k in ("nn", "beta", "s")},
               t_start=T_START, t_end=T_END,
               dev_seeds=op["dev_seeds"], heldout_seeds=op["heldout_seeds"], episodes={})
    for seed in seeds:
        res = run_episode(sim, seed, nt=T_END + 1, record_oracle=False)
        r = run_one(sim, res.z_hist)
        out["episodes"][str(seed)] = r
        for m in ("affinity_louvain", "spectral_coherence"):
            L = r["lineages"][m]
            durs = sorted([l["duration"] for l in L], reverse=True)
            long = [l for l in L if l["duration"] >= 10]
            print(f"seed {seed:<4} {m:<20} n_lineages={len(L):3d} "
                  f"max_dur={durs[0] if durs else 0:3d} "
                  f"n>=10 steps={len(long):2d} "
                  f"mean_size={np.mean([l['mean_size'] for l in L]):6.1f} "
                  f"mean_J={np.mean([l['mean_jaccard'] for l in L]):.3f} "
                  f"mean_turnover={np.mean([l['mean_turnover'] for l in L]):.3f}", flush=True)
    dump_json(out, DATA_DIR / "detection.json")
    print("wrote", DATA_DIR / "detection.json")


if __name__ == "__main__":
    main()
