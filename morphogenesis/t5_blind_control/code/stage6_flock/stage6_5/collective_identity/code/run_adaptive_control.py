"""Part 5: closed-loop identity-adaptive control, proof-of-concept.
Compares fixed-material (I_t=I0), lineage-adaptive (I_t=I_t^L), and
functional-adaptive (I_t=I_t^F) control on the same flocks, same frozen
multicover law. See adaptive_control.py's module docstring for the scope
decision (true shell + frozen q/gamma, not a re-inferred graph).

Scope (PLAN.md / Part 5.1's own "smaller proof-of-concept" instruction):
flocks 2, 3 (2 of the 3 boundary-inference dev flocks); N_REP=8 replicates
per (flock, representation).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
from common_v2 import find_flock  # noqa: E402

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))
from adaptive_control import run_closed_loop_episode, summarize_episode  # noqa: E402

FLOCKS = [2, 3]
REPRESENTATIONS = ["M", "L", "F"]
N_REP = 8
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main():
    all_results = []
    for flock_seed in FLOCKS:
        fl = find_flock(flock_seed)
        flock_row = dict(flock_seed=flock_seed, per_representation={})
        for rep in REPRESENTATIONS:
            summaries = []
            for r in range(N_REP):
                ep = run_closed_loop_episode(fl, rep, seed=r)
                summaries.append(summarize_episode(ep))
            agg = dict(
                p_success=float(np.mean([s["success"] for s in summaries])),
                p_success_retained_only=float(np.mean([s["success_retained_only"] for s in summaries])),
                p_persistence=float(np.mean([s["persistence"] for s in summaries])),
                mean_Hstar_end=float(np.mean([s["Hstar_end"] for s in summaries])),
                mean_Hstar_end_retained=float(np.mean([s["Hstar_end_retained"] for s in summaries])),
                mean_n_actuators=float(np.mean([s["mean_n_actuators"] for s in summaries])),
                max_n_actuators=int(np.max([s["max_n_actuators"] for s in summaries])),
                mean_final_retention=float(np.mean([s["final_retention"] for s in summaries])),
                mean_final_size=float(np.mean([s["final_size"] for s in summaries])),
                mean_membership_turnover=float(np.mean([s["membership_turnover_total"] for s in summaries])),
                mean_actuator_turnover=float(np.mean([s["actuator_turnover_total"] for s in summaries])),
                mean_min_coherence=float(np.mean([s["mean_min_coherence"] for s in summaries])),
                per_replicate=summaries,
            )
            flock_row["per_representation"][rep] = agg
            print(f"flock={flock_seed} rep={rep}: p_success={agg['p_success']:.2f} "
                  f"p_success_retained_only={agg['p_success_retained_only']:.2f} "
                  f"mean_n_actuators={agg['mean_n_actuators']:.1f} "
                  f"mean_final_retention={agg['mean_final_retention']:.2f} "
                  f"mean_membership_turnover={agg['mean_membership_turnover']:.1f}")
        all_results.append(flock_row)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "adaptive_control.json", "w") as f:
        json.dump(dict(flocks=FLOCKS, representations=REPRESENTATIONS, n_rep=N_REP, results=all_results),
                  f, indent=1)
    print("\nWrote data/adaptive_control.json")


if __name__ == "__main__":
    main()
