"""Task brief section 16: a SMALL diagnostic (not a new controller
optimization stage) comparing four actuator sets on the existing
target-heading task and frozen control horizon, reusing
v2_interface_control/code/common_v2.py:evaluate_arm unmodified:

  - full inferred predictive interface  Bhat^pred(I0)
  - full inferred causal interface      Bhat^causal(I0)
  - matched-budget random (one random draw per reference size)
  - oracle B^D(I0)

For each seed's canonical I0 (condition="no_control", matching
run_sample_efficiency.py's own condition choice). Requires
data/predictive_boundary_panel.json and data/causal_discovery_panel.json to
already exist (run_predictive_boundary.py, run_causal_discovery.py).
"""
from __future__ import annotations

import json

import numpy as np

from common_67 import lattice_100, find_flock, evaluate_arm, dump_json, DATA_DIR, snapshot_key, PRIMARY_SEEDS_67
from oracle_validation import true_shell

CONDITION = "no_control"
N_REP = 30
SEED_OFFSET = 767_000_000


def load(name):
    return json.loads((DATA_DIR / name).read_text())


def main():
    lattice = lattice_100()
    pred_data = load("predictive_boundary_panel.json")["results"]
    causal_data = load("causal_discovery_panel.json")["results"]

    rows = []
    for seed in PRIMARY_SEEDS_67:
        key = snapshot_key(seed, CONDITION)
        pred_I0 = next(c for c in pred_data[key]["candidates"] if c["label"] == "established_I0")
        causal_I0 = next(c for c in causal_data[key]["candidates"] if c["label"] == "established_I0")

        fl = find_flock(seed, lattice=lattice)
        I0 = np.array(sorted(pred_I0["I"]), dtype=int)
        h_star = fl["h_star"]
        z_t0 = fl["z_t0"]
        B_D = true_shell(I0, lattice=lattice)

        arms = dict(
            oracle=np.array(sorted(int(b) for b in B_D.tolist())),
            predictive=np.array(sorted(int(b) for b in pred_I0["B_hat_pred"])),
            causal=np.array(sorted(int(b) for b in causal_I0["B_hat_causal"])),
        )
        rng = np.random.default_rng(SEED_OFFSET + seed)
        exterior = np.array([j for j in range(100) if j not in set(I0.tolist())])
        random_matched = {}
        for name, actuators in list(arms.items()):
            size = len(actuators)
            draw = rng.choice(exterior, size=min(size, len(exterior)), replace=False) if size > 0 else np.array([], dtype=int)
            random_matched[name] = np.array(sorted(int(x) for x in draw))

        row = dict(seed=seed, I0=I0.tolist(), h_star=int(h_star))
        for name, actuators in arms.items():
            perf = evaluate_arm(actuators, z_t0, I0, h_star, lattice, n_replicates=N_REP,
                                 seed_offset=SEED_OFFSET + seed * 10)
            row[name] = dict(actuators=actuators.tolist(), **perf)
            perf_rand = evaluate_arm(random_matched[name], z_t0, I0, h_star, lattice, n_replicates=N_REP,
                                      seed_offset=SEED_OFFSET + seed * 10 + 5)
            row[f"random_matched_{name}"] = dict(actuators=random_matched[name].tolist(), **perf_rand)
        rows.append(row)
        print(f"seed={seed}: oracle p_success={row['oracle']['p_success']:.2f} "
              f"predictive p_success={row['predictive']['p_success']:.2f} "
              f"causal p_success={row['causal']['p_success']:.2f}")

    dump_json(dict(rows=rows, condition=CONDITION, n_replicates=N_REP), DATA_DIR / "control_diagnostic.json")
    print("wrote data/control_diagnostic.json")


if __name__ == "__main__":
    main()
